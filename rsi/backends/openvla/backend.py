"""OpenVLA backend: sharded LIBERO rollout workers and a LoRA training worker.

Episodes are sharded across GPUs in blocks of ``n_envs`` that share a task, so
each worker batches episodes with an identical prompt. Versions are LoRA
adapters over one fixed base checkpoint; workers merge the adapter at load.
Update operators (``bc``, ``grpo``) come from the improvement program.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time

from ...core.gpu import admit, oom_failed_logs, supervised, supervised_parallel
from ...core.types import Receipt, Version

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class VLAConfig:
    checkpoint: str
    python: str
    openvla_root: str
    workdir: str
    rollout_gpus: tuple = (0,)
    train_gpus: tuple = (0,)
    n_envs: int = 8                    # batched envs per process for sampled episodes
    greedy_procs_per_gpu: int = 4      # unbatched processes per GPU for greedy episodes
    sample_procs_per_gpu: int = 1      # batched (n_envs) processes per GPU for sampled episodes
    lora_rank: int = 32
    lora_alpha: int = 16
    target_modules: tuple = ("q_proj", "k_proj", "v_proj", "o_proj")
    micro_batch: int = 16
    rollout_timeout: int = 12 * 3600
    train_timeout: int = 10 * 3600
    admission_gap: float = 30.0
    oom_retries: int = 2               # re-admit and rerun a phase whose worker ran out of GPU memory
    subset_after: float = 600.0        # seconds to wait for every rollout GPU before using the free ones
    env: dict = field(default_factory=dict)


class VLABackend:
    def __init__(self, config: VLAConfig):
        self.config = config
        self.workdir = Path(config.workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.calls, self.admissions, self.gpu_seconds = 0, [], {}
        self.active_gpus = list(config.rollout_gpus)

    def _env(self):
        # Thread caps: each worker otherwise starts one thread per core (128 here); a dozen rollout
        # workers then oversubscribe the CPU (load 310 on 128 cores; sampled rollouts 150-240 episodes/h
        # instead of ~900/h). Rollouts are simulator- and GPU-bound, so 4 threads per worker is plenty.
        env = {"PYTHONNOUSERSITE": "1", "MUJOCO_GL": "egl", "TOKENIZERS_PARALLELISM": "false",
               "TF_CPP_MIN_LOG_LEVEL": "3", "http_proxy": "", "https_proxy": "",
               "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4"}
        env.update(self.config.env)
        return env

    def _call_dir(self, kind):
        self.calls += 1
        path = self.workdir / f"{self.calls:05d}-{kind}-{int(time.time())}"
        path.mkdir()
        return path

    def _phase(self, call, tag, adapter, suite, episodes, max_steps, n_envs, procs_per_gpu):
        """Run one homogeneous phase: shards of n_envs-sized same-task blocks over GPU slots."""
        cfg = self.config
        slots = [g for g in self.active_gpus for _ in range(procs_per_gpu)]
        groups = {}
        for ep in episodes:
            groups.setdefault((ep["task_id"], ep["mode"], ep["temperature"]), []).append(ep)
        shards = [[] for _ in slots]
        for key in sorted(groups, key=lambda k: -len(groups[k])):
            eps = groups[key]
            for b in range(0, len(eps), n_envs):
                min(shards, key=len).extend(eps[b:b + n_envs])
        jobs = []
        for k, (gpu, shard) in enumerate(zip(slots, shards)):
            if not shard:
                continue
            spec = dict(checkpoint=cfg.checkpoint, adapter=adapter, suite=suite,
                        max_steps=max_steps, n_envs=n_envs, openvla_root=cfg.openvla_root,
                        out_dir=str(call / "episodes"), episodes=shard)
            (call / f"spec-{tag}{k}.json").write_text(json.dumps(spec))
            jobs.append(([cfg.python, str(HERE / "rollout_worker.py"),
                          str(call / f"spec-{tag}{k}.json")],
                         (gpu,), call / f"log-{tag}{k}.txt", self._env()))
        if jobs:
            started = time.time()
            supervised_parallel(jobs, timeout=cfg.rollout_timeout)
            self.gpu_seconds["rollout"] = self.gpu_seconds.get("rollout", 0.0) + \
                len(self.active_gpus) * (time.time() - started)

    def _admit_rollout(self):
        """All rollout GPUs if they free up within ``subset_after`` seconds, else whichever are free (one at
        least); later phases of this rollout run on the GPUs admitted."""
        cfg = self.config
        adm = admit(cfg.rollout_gpus, gap=cfg.admission_gap, min_gpus=1, full_wait=cfg.subset_after)
        self.active_gpus = list(adm["gpus"])
        return adm

    def _phase_retrying(self, call, tag, *args):
        """Admission is checked before the rollout, but on a shared box another job can still take a GPU
        while a phase is running (10-27: a vLLM server started on GPU 0 mid-phase and every worker there
        ran out of memory, losing a run in its last round). A phase whose failed workers ran out of GPU
        memory is rerun after a fresh admission. The failed attempt's files are moved aside first, so
        each episode's row and trajectory come from one attempt."""
        episodes_dir = call / "episodes"
        for attempt in range(self.config.oom_retries + 1):
            before = set(episodes_dir.iterdir()) if episodes_dir.exists() else set()
            try:
                return self._phase(call, tag, *args)
            except RuntimeError as exc:
                logs = oom_failed_logs(exc)
                if not logs or attempt == self.config.oom_retries:
                    raise
                aside = call / f"discarded-{tag}{attempt}"
                aside.mkdir()
                for path in set(episodes_dir.iterdir()) - before:
                    path.rename(aside / path.name)
                for log in logs:
                    Path(log).rename(aside / Path(log).name)
                self.admissions.append(dict(self._admit_rollout(), retry_of=f"{tag}{attempt}", failed_logs=logs))

    def rollout(self, version: Version, suite, episodes, max_steps=None):
        """Greedy episodes run unbatched (one env per process, several processes per GPU),
        which reproduces OpenVLA's batch-1 numerics exactly; batched generation flips
        near-tie argmaxes (measured: 17% of actions differ on 128 frames). Sampled
        exploration episodes are batched ``n_envs`` at a time."""
        cfg = self.config
        call = self._call_dir("rollout")
        adapter = None if version.parent_id is None else version.location
        self.admissions.append(self._admit_rollout())
        greedy = [ep for ep in episodes if ep["mode"] == "greedy"]
        sampled = [ep for ep in episodes if ep["mode"] != "greedy"]
        self._phase_retrying(call, "g", adapter, suite, greedy, max_steps, 1, cfg.greedy_procs_per_gpu)
        self._phase_retrying(call, "s", adapter, suite, sampled, max_steps, cfg.n_envs, cfg.sample_procs_per_gpu)
        rows = {}
        for path in (call / "episodes").glob("results-*.jsonl"):
            for line in path.open():
                row = json.loads(line)
                rows[row["id"]] = row
        missing = [ep["id"] for ep in episodes if ep["id"] not in rows]
        if missing:
            raise ValueError(f"incomplete_rollout_denominator:{len(missing)}")
        return [rows[ep["id"]] for ep in episodes]

    def train(self, parent: Version, items, output, update: dict, seed: int) -> Receipt:
        cfg = self.config
        if not items:
            raise ValueError("nonempty_training_items_required")
        call = self._call_dir("train")
        spec = dict(checkpoint=cfg.checkpoint, openvla_root=cfg.openvla_root, parent=asdict(parent),
                    output=str(output), items=list(items), update=update, seed=seed,
                    lora_rank=cfg.lora_rank, lora_alpha=cfg.lora_alpha,
                    target_modules=list(cfg.target_modules), micro_batch=cfg.micro_batch)
        (call / "train_spec.json").write_text(json.dumps(spec))
        self.admissions.append(admit(cfg.train_gpus, gap=cfg.admission_gap))
        started = time.time()
        supervised([cfg.python, str(HERE / "train_worker.py"), str(call / "train_spec.json")],
                   gpus=cfg.train_gpus[:1], timeout=cfg.train_timeout,
                   log_path=call / "log.txt", env=self._env())
        self.gpu_seconds["train"] = self.gpu_seconds.get("train", 0.0) + (time.time() - started)
        r = json.loads((Path(output) / "receipt.json").read_text())
        return Receipt(Version(**r["version"]), r["operator"], r["optimizer_steps"], r["items"],
                       r["trainable_parameters"], r["before_sha256"], r["after_sha256"],
                       {k: r[k] for k in ("frames", "seconds", "loss_first", "loss_last") if k in r})

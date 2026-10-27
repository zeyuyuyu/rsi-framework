"""Causal-LM backend: data-parallel vLLM sampling and a LoRA training worker.

The engine process holds no GPU memory. Every call admits its GPUs, writes a
request file and runs supervised worker processes. Versions are LoRA adapters
inherited parent-to-child; the trainer also writes a merged copy that vLLM
serves, so serving never depends on vLLM's LoRA kernels. Update operators
(``sft``, ``grpo``) are selected by the improvement program per round.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time

from ...core.gpu import admit, oom_failed_logs, supervised, supervised_parallel
from ...core.types import Receipt, Version


@dataclass(frozen=True)
class LLMConfig:
    base_path: str
    python: str
    workdir: str
    sample_gpus: tuple = (0,)
    train_gpus: tuple = (0,)
    pythonpath: str = ""
    tensor_parallel: int = 1
    lora_rank: int = 64
    lora_alpha: int = 128
    target_modules: tuple = ("q_proj", "k_proj", "v_proj", "o_proj",
                             "gate_proj", "up_proj", "down_proj")
    micro_batch: int = 4
    max_seq_len: int = 2048
    max_model_len: int = 4096
    gpu_memory_utilization: float = 0.85
    oom_retries: int = 2               # rerun a sampling call whose workers ran out of GPU memory
    sample_timeout: int = 6 * 3600
    train_timeout: int = 10 * 3600
    admission_gap: float = 30.0
    extra: dict = field(default_factory=dict)


class LLMBackend:
    def __init__(self, config: LLMConfig):
        if not Path(config.base_path).is_dir():
            raise ValueError("local_base_checkpoint_required")
        self.config = config
        self.workdir = Path(config.workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.calls, self.admissions, self.gpu_seconds = 0, [], {}

    def _env(self):
        env = {"HF_HUB_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
               "VLLM_WORKER_MULTIPROC_METHOD": "spawn"}
        if self.config.pythonpath:
            env["PYTHONPATH"] = self.config.pythonpath
        return env

    def _call_dir(self, kind):
        self.calls += 1
        path = self.workdir / f"{self.calls:05d}-{kind}-{int(time.time())}"
        path.mkdir()
        return path

    def _account(self, kind, gpus, started):
        self.gpu_seconds[kind] = self.gpu_seconds.get(kind, 0.0) + len(gpus) * (time.time() - started)

    def serve_path(self, version: Version):
        return self.config.base_path if version.parent_id is None \
            else str(Path(version.location) / "merged")

    def sample(self, version: Version, requests):
        """requests: dicts with prompt, n, temperature, top_p, max_tokens, stop, seed."""
        if not requests:
            return []
        cfg = self.config
        call = self._call_dir("sample")
        tp = cfg.tensor_parallel
        groups = [tuple(cfg.sample_gpus[i:i + tp]) for i in range(0, len(cfg.sample_gpus), tp)]
        groups = [g for g in groups if len(g) == tp]
        all_gpus = [g for grp in groups for g in grp]
        self.admissions.append(admit(all_gpus, gap=cfg.admission_gap))
        started = time.time()
        jobs = []
        for shard, gpus in enumerate(groups):
            idx = list(range(shard, len(requests), len(groups)))
            if not idx:
                continue
            req = call / f"req-{shard}.jsonl"
            with req.open("w") as stream:
                for i in idx:
                    stream.write(json.dumps(dict(index=i, **requests[i])) + "\n")
            argv = [cfg.python, "-m", "rsi.backends.llm.sample_worker",
                    "--model", self.serve_path(version), "--requests", str(req),
                    "--out", str(call / f"out-{shard}.jsonl"),
                    "--max-model-len", str(cfg.max_model_len),
                    "--gpu-memory-utilization", str(cfg.gpu_memory_utilization),
                    "--tensor-parallel", str(tp)]
            jobs.append((argv, gpus, call / f"log-{shard}.txt", self._env()))
        # Another job can take memory on our GPU after admission (10-28: three processes took 4.6 GB on
        # GPU 6 and vLLM's sampler ran out of memory mid-run). Such a call is rerun after a fresh
        # admission; the failed attempt's outputs and logs are moved aside first.
        for attempt in range(cfg.oom_retries + 1):
            try:
                supervised_parallel(jobs, timeout=cfg.sample_timeout)
                break
            except RuntimeError as exc:
                logs = oom_failed_logs(exc)
                if not logs or attempt == cfg.oom_retries:
                    raise
                aside = call / f"discarded-{attempt}"
                aside.mkdir()
                for path in list(call.glob("out-*.jsonl")) + [Path(log) for log in logs]:
                    if path.exists():
                        path.rename(aside / path.name)
                self.admissions.append(dict(admit(all_gpus, gap=cfg.admission_gap),
                                            retry_of=attempt, failed_logs=logs))
        self._account("sample", all_gpus, started)
        results = [None] * len(requests)
        for shard in range(len(jobs)):
            for line in (call / f"out-{shard}.jsonl").open():
                row = json.loads(line)
                results[row["index"]] = row["texts"]
        if any(r is None or len(r) != requests[i]["n"] for i, r in enumerate(results)):
            raise ValueError("incomplete_sampling_denominator")
        return results

    def train(self, parent: Version, items, output, update: dict, seed: int) -> Receipt:
        cfg = self.config
        if not items:
            raise ValueError("nonempty_training_items_required")
        call = self._call_dir("train")
        data = call / "items.jsonl"
        with data.open("w") as stream:
            for item in items:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")
        spec = dict(base_path=cfg.base_path, parent=asdict(parent), output=str(output),
                    items=str(data), update=update, seed=seed, lora_rank=cfg.lora_rank,
                    lora_alpha=cfg.lora_alpha, target_modules=list(cfg.target_modules),
                    micro_batch=cfg.micro_batch, max_seq_len=cfg.max_seq_len,
                    multi_gpu_device_map=len(cfg.train_gpus) > 1)
        spec_path = call / "train_spec.json"
        spec_path.write_text(json.dumps(spec, indent=2))
        self.admissions.append(admit(cfg.train_gpus, gap=cfg.admission_gap))
        started = time.time()
        supervised([cfg.python, "-m", "rsi.backends.llm.train_worker", str(spec_path)],
                   gpus=cfg.train_gpus, timeout=cfg.train_timeout,
                   log_path=call / "log.txt", env=self._env())
        self._account("train", cfg.train_gpus, started)
        r = json.loads((Path(output) / "receipt.json").read_text())
        return Receipt(Version(**r["version"]), r["operator"], r["optimizer_steps"], r["items"],
                       r["trainable_parameters"], r["before_sha256"], r["after_sha256"],
                       {k: r[k] for k in ("skipped_too_long", "seconds", "loss_first", "loss_last",
                                          "extra") if k in r})

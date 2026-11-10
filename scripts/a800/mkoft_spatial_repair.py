"""A800: addendum-29 seed-0 arms of the self-repair study on LIBERO-Spatial (OFT 1-traj SFT, the collapsing BC start
of addenda 12/24, fresh paired gates). arms: fixed (gate only) | full (numeric search, harness space, capped at the
start's work) | meta3 (meta level v3: the LLM behind a harness with workspace, memory and tools; same cap).
Runs from src11 (repo rsi/ of the addendum-29 commit, with rsi/meta/memory/v3). The meta3 arm reads the gateway key
from ~/.orkey on cavin (mode 600; never in a plan or log) and calls through py_llmproxy.sh like the earlier LLM arms.
usage: mkoft_spatial_repair.py <order> <arm> [ngpus=1]      -> a8_spatrep_<arm>_s0"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
SRC = f"{H}/rsi/src11"
sys.path.insert(0, SRC)
from rsi.meta.harness import memory_digest
order, arm = int(sys.argv[1]), sys.argv[2]
ngpus = int(sys.argv[3]) if len(sys.argv) > 3 else 1
seed = 0
ARMS = {"fixed": ({}, {"proposer": "fixed"}),
        "full": ({"candidates_per_round": 2}, {"proposer": "numeric", "space": "harness", "budget": "seed"}),
        "meta3": ({"candidates_per_round": 2, "meta_v2": True},
                  {"proposer": "llm3", "space": "v2", "budget": "seed", "base_url": "https://openrouter.ai/api/v1",
                   "model": "anthropic/claude-sonnet-5-5", "key_file": f"{H}/.orkey", "memory": "v3",
                   "memory_sha256": memory_digest(f"{SRC}/rsi/meta/memory/v3"), "max_calls": 60, "max_turns": 6})}
assert arm in ARMS
engine_extra, meta = ARMS[arm]
name = f"a8_spatrep_{arm}_s{seed}"
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-spatial-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000, "ratio_mode": "matched", "loss_agg": "episode"}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
           "update": {"operator": "bc", "steps": 100, "batch": 64, "lr": 1e-5, "ratio": "matched",
                      "loss_agg": "episode", "bc_temp": "unit"},
           "curation": {"rule": "verified", "adv": "center"}}
engine = dict({"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": seed}, **engine_extra)
plan = {"model_name": "oft-sft-libero-spatial-traj1", "vla": vla, "suite": "libero_spatial", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50, "engine": engine, "meta": meta, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
python = f"{H}/rsi/bin/py_llmproxy.sh" if arm == "meta3" else f"{H}/miniconda3/envs/vllm/bin/python"
job = dict(name=name, ngpus=ngpus, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=python, pythonpath=f"{SRC}:{H}/rsi/pylib", cwd=SRC)
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name, "ngpus", ngpus, meta.get("memory_sha256", "")[:16])

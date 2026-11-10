"""A800: addendum-30 amendment 1, the seed-0 block of the 12-round study on LIBERO-Spatial (OFT 1-traj SFT, the
Spatial main program, fresh paired gates). arms: fixed12 (12 rounds x 3 inner steps, recursive) | nonrec12 (the same,
practice from the frozen initial policy). Runs from src12 (repo rsi/ at addendum 30).
usage: mkoft_spatial_long12.py <order> <arm> [ngpus=1]      -> a8_spatmain_<arm>_s0"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
SRC = f"{H}/rsi/src12"
order, arm = int(sys.argv[1]), sys.argv[2]
ngpus = int(sys.argv[3]) if len(sys.argv) > 3 else 1
ARMS = {"fixed12": {}, "nonrec12": {"recursive": False}}
assert arm in ARMS
name = f"a8_spatmain_{arm}_s0"
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-spatial-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000, "ratio_mode": "matched", "loss_agg": "episode"}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
           "update": {"steps": 100, "batch": 64, "lr": 3e-5}}
engine = dict({"rounds": 12, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": 0}, **ARMS[arm])
plan = {"model_name": "oft-sft-libero-spatial-traj1", "vla": vla, "suite": "libero_spatial", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50, "engine": engine, "meta": {"proposer": "fixed"}, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=ngpus, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{SRC}:{H}/rsi/pylib", cwd=SRC)
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name, "ngpus", ngpus)

"""A800: addendum-13 GRPO curve on another LIBERO suite (OFT 1-traj SFT), the exact Goal program: 6 rounds x 3
inner steps of 64 placements, GRPO lr 3e-5, matched ratio, episode-balanced loss, always-accept, sealed.
Runs from src3 with admit_max_used_mib 8000.
usage: mkoft_suite.py <order> <seed> <spatial|object>"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
order, seed, suite = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
assert suite in ("spatial", "object")
name = f"a8_ofts_curve_grpo_s{seed}" if suite == "spatial" else f"a8_ofto_curve_grpo_s{seed}"
src = f"{H}/rsi/src3"
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-{suite}-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000, "ratio_mode": "matched", "loss_agg": "episode"}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
           "update": {"steps": 100, "batch": 64, "lr": 3e-5}}
plan = {"model_name": f"oft-sft-libero-{suite}-traj1", "vla": vla, "suite": f"libero_{suite}", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50,
        "engine": {"rounds": 6, "inner_steps": 3, "seed": seed, "seal_tests": True, "min_gate_gain": -1.0},
        "meta": {"proposer": "fixed"}, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=1, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{src}:{H}/rsi/pylib", cwd=src)
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name)

"""A800: addendum-4 sealed pilot, short on-policy rounds for M1 (OpenVLA-OFT 1-demo SFT, LIBERO-10).
usage: mkoft_pilot4.py <order>"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
order = int(sys.argv[1])
name = "a8_oft3_pilot4_short"
plan = {"model_name": "oft-sft-libero10-traj1",
        "vla": {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero10-traj1",
                "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
                "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3},
        "suite": "libero_10", "tasks": list(range(10)), "heldout_per_task": 40, "test_inits_per_task": 50,
        "engine": {"rounds": 12, "seed": 0, "seal_tests": True}, "meta": {"proposer": "fixed"},
        "program": {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
                    "update": {"lr": 1e-4, "steps": 100, "batch": 64}}}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=3, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{H}/rsi/src2:{H}/rsi/pylib",
           cwd=f"{H}/rsi/src2")
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name)

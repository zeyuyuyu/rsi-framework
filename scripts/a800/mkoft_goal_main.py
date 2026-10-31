"""A800: addendum-14 LIBERO-Goal main arm (OFT 1-traj SFT, GRPO program of addendum 11, fresh paired gates).
arms: fixed | full (numeric meta level) | llm (LLM meta level, addendum 14) | onebig | nonrec | shuffled.
Runs from src5 (bc_temp + LLM meta level), admit_max_used_mib 8000. The llm arm reads the gateway key from
~/.cskey on cavin (mode 600; never in a plan or log).
usage: mkoft_goal_main.py <order> <seed> <arm>"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
order, seed, arm = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
ARMS = {"fixed": ({}, {"proposer": "fixed"}),
        "full": ({"candidates_per_round": 2}, {"proposer": "numeric"}),
        "llm": ({"candidates_per_round": 2}, {"proposer": "llm", "base_url": "https://api.commonstack.ai/v1",
                                               "model": "anthropic/claude-sonnet-5-5", "key_file": f"{H}/.cskey",
                                               "max_calls": 24}),
        "onebig": ({"rounds": 1, "inner_steps": 18}, {"proposer": "fixed"}),
        "nonrec": ({"recursive": False}, {"proposer": "fixed"}),
        "shuffled": ({"feedback": "shuffled"}, {"proposer": "fixed"})}
assert arm in ARMS
engine_extra, meta = ARMS[arm]
name = f"a8_goalmain_{arm}_s{seed}"
src = f"{H}/rsi/src5"
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-goal-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000, "ratio_mode": "matched", "loss_agg": "episode"}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
           "update": {"steps": 100, "batch": 64, "lr": 3e-5}}
engine = dict({"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": seed}, **engine_extra)
plan = {"model_name": "oft-sft-libero-goal-traj1", "vla": vla, "suite": "libero_goal", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50, "engine": engine, "meta": meta, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=1, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{src}:{H}/rsi/pylib", cwd=src)
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name)

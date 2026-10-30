"""A800: addendum-11 seed replica on LIBERO-Goal (OFT 1-traj SFT), always-accept curve of 6 rounds x 3 inner
steps of 64 placements, GRPO (lr 3e-5, matched, episode loss) or BC on verified successes (lr 1e-5). Runs from
src3 with admit_max_used_mib 8000 (other users' small jobs share our cards).
usage: mkoft_goal.py <order> <seed> <grpo|bc>"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
order, seed, op = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
assert op in ("grpo", "bc")
name = f"a8_oftg_curve_{op}_s{seed}"
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-goal-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6}, "update": {"steps": 100, "batch": 64}}
if op == "grpo":
    vla.update(ratio_mode="matched", loss_agg="episode")
    program["update"]["lr"] = 3e-5
else:
    program["update"].update(lr=1e-5, operator="bc")
    program["curation"] = {"rule": "verified"}
plan = {"model_name": "oft-sft-libero-goal-traj1", "vla": vla, "suite": "libero_goal", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50,
        "engine": {"rounds": 6, "inner_steps": 3, "seed": seed, "seal_tests": True, "min_gate_gain": -1.0},
        "meta": {"proposer": "fixed"}, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=1, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{H}/rsi/src3:{H}/rsi/pylib",
           cwd=f"{H}/rsi/src3")
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name)

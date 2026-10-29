"""A800: train-on-test inflation (prereg v3, secondary measurement). SimpleVLA-RL's LIBERO-10 RL checkpoint was
trained on the 50 official initial states; its 1-demo SFT start was not. Each is evaluated greedily on the
official 500 episodes and on 500 freshly sampled placements (heldout seeds, 50 per task); inflation =
(RL official - RL fresh) - (SFT official - SFT fresh).
usage: mkinfl.py <order> sft|rl [fresh2]
  fresh2: replication on 1000 fresh placements (100 per task); placements 50-99 per task are new"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
PY = f"{H}/miniconda3/envs/vllm/bin/python"
PP = f"{H}/rsi/src2:{H}/rsi/pylib"
CKPT = {"sft": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero10-traj1",
        "rl": f"{H}/rsi/models/oft/openvla-oft-libero10-traj1-rl"}
order, which = int(sys.argv[1]), sys.argv[2]
fresh2 = sys.argv[3:4] == ["fresh2"]
name = f"oft-{which}-libero10-traj1"
plan = {"model_name": name,
        "vla": {"model_family": "oft", "checkpoint": CKPT[which], "python": f"{H}/miniconda3/envs/openvla/bin/python",
                "openvla_root": f"{H}/rsi/simplevla_rl", "rollout_gpus": [0], "train_gpus": [0],
                "greedy_procs_per_gpu": 4},
        "suite": "libero_10", "tasks": list(range(10)), "heldout_per_task": 100 if fresh2 else 50,
        "test_inits_per_task": 50}
plan_path = f"{H}/rsi/plans2/infl_{which}{'_fresh2' if fresh2 else ''}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
receipt = f"{H}/rsi/plans2/infl_{which}_base_receipt.json"
json.dump({"version": {"id": f"base:{name}", "location": CKPT[which], "parent_id": None}}, open(receipt, "w"))
jobs = (("fresh2", ["--heldout-eval", receipt]),) if fresh2 else \
       (("official", ["--baseline-only"]), ("fresh", ["--heldout-eval", receipt]))
for k, (tag, args) in enumerate(jobs):
    jname = f"infl_{which}_{tag}"
    job = dict(name=jname, ngpus=1, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{jname}",
               gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=args, python=PY,
               pythonpath=PP, cwd=f"{H}/rsi/src2")
    json.dump(job, open(f"{Q}/pending/{order + k:02d}_{jname}.json", "w"), indent=1)
    print("queued", jname)

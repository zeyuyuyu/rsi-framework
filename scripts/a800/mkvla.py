"""A800: VLA pilot + 2nd baseline replicate into the queue; main VLA arms into queue/hold until the pilot passes.
Also moves the 1.5B onebig arms out of pending (they run on Baidu)."""
import json, os, shutil
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
PY = f"{H}/miniconda3/envs/vllm/bin/python"
PP = f"{H}/rsi/src2:{H}/rsi/pylib"
os.makedirs(f"{Q}/hold", exist_ok=True)
os.makedirs(f"{Q}/moved_to_baidu", exist_ok=True)
for s in (1, 2, 3):
    f = f"{Q}/pending/{13 + s}_main_q15_onebig_s{s}.json"
    if os.path.exists(f):
        shutil.move(f, f"{Q}/moved_to_baidu/")
base = json.load(open(f"{H}/rsi/plans2/vla_base_goal.json"))
FIELDS = {"vla.rollout_gpus": "all", "vla.train_gpus": "first"}


def plan(name, engine, meta=None):
    p = json.loads(json.dumps(base))
    p["engine"] = engine
    p["meta"] = meta or {"proposer": "fixed"}
    path = f"{H}/rsi/plans2/{name}.json"
    json.dump(p, open(path, "w"), indent=2)
    return path


def job(dest, order, name, ngpus, plan_path, args=()):
    j = dict(name=name, ngpus=ngpus, module="rsi.run_libero", plan=plan_path,
             out=f"{H}/rsi/runs2/{name}", gpu_fields=FIELDS, args=list(args),
             python=PY, pythonpath=PP, cwd=f"{H}/rsi/src2")
    json.dump(j, open(f"{Q}/{dest}/{order:02d}_{name}.json", "w"), indent=1)


# dev seed 0, one round, tests sealed: catches crashes and checks the gate moves; may only adjust lr/steps
job("pending", 6, "vla_pilot_goal", 2, plan("vla_pilot_goal", dict(rounds=1, seed=0, seal_tests=True)))
job("pending", 7, "vla_baseline_goal_rep1", 1, f"{H}/rsi/plans2/vla_base_goal.json", ["--baseline-only"])
ARMS = (("fixed", {}, None), ("nonrec", {"recursive": False}, None), ("shuffled", {"feedback": "shuffled"}, None),
        ("full", {"candidates_per_round": 2}, {"proposer": "numeric"}))
k = 0
for s in (1, 2):
    for arm, over, meta in ARMS:
        name = f"vla_goal_{arm}_s{s}"
        job("hold", 20 + k, name, 2, plan(name, dict(dict(rounds=3, seed=s), **over), meta))
        k += 1
print("pending", sorted(os.listdir(f"{Q}/pending")))
print("hold", sorted(os.listdir(f"{Q}/hold")))
print("moved", sorted(os.listdir(f"{Q}/moved_to_baidu")))

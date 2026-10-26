"""Create reservations for running jobs and the A800 job queue."""
import glob, json, os, subprocess
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
for d in ("pending", "running", "done", "failed", "plans", "logs"):
    os.makedirs(f"{Q}/{d}", exist_ok=True)
PY = f"{H}/miniconda3/envs/vllm/bin/python"
PP = f"{H}/rsi/src2:{H}/rsi/pylib"

def pid_of(pattern):
    out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split()
    return [int(p) for p in out]

res = []
for name, gpus in (("main_q15_fixed_s1", [0, 1]), ("main_q15_nonrec_s1", [2, 4]), ("main_q15_shuffled_s1", [5, 6]), ("vla_baseline_goal_rep0", [7])):
    pids = [p for p in pid_of(f"rsi.run_.*--out .*{name}") if p != os.getpid()]
    for p in pids[:1]:
        res.append(dict(pid=p, gpus=gpus, name=name))
json.dump(res, open(f"{Q}/reservations.json", "w"), indent=1)
print("reservations", res)

def snap(m):
    return glob.glob(f"{H}/.cache/huggingface/hub/models--{m}/snapshots/*/")[0]

MBPP = [f"{H}/rsi/data/google-research-datasets__mbpp/full/{s}-00000-of-00001.parquet" for s in ("train", "validation", "test")]
base = json.load(open(f"{H}/rsi/plans2/main_q15_fixed_s1.json"))

def plan_for(name, model_path, model_name, **over):
    p = json.loads(json.dumps(base))
    p["model_name"] = model_name
    p["llm"]["base_path"] = model_path
    for k, v in over.items():
        node = p
        keys = k.split(".")
        for kk in keys[:-1]:
            node = node.setdefault(kk, {})
        node[keys[-1]] = v
    path = f"{H}/rsi/plans2/{name}.json"
    json.dump(p, open(path, "w"), indent=2)
    return path

def job(order, name, ngpus, plan, args=(), module="rsi.run_code_wm", fields=None):
    j = dict(name=name, ngpus=ngpus, module=module, plan=plan, out=f"{H}/rsi/runs2/{name}",
             gpu_fields=fields or {"llm.sample_gpus": "all", "llm.train_gpus": "first"},
             args=list(args), python=PY, pythonpath=PP, cwd=f"{H}/rsi/src2")
    json.dump(j, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)

q15 = snap("Qwen--Qwen2.5-Coder-1.5B-Instruct")
cwm = f"{H}/rsi/models/cwm-llama"
job(1, "base_cwm32b", 2, plan_for("base_cwm32b", cwm, "cwm32b", **{"llm.tensor_parallel": 2}), ["--baseline-only"],
    fields={"llm.sample_gpus": "all", "llm.train_gpus": "all"})
job(2, "base_qcoder7b", 1, plan_for("base_qcoder7b", snap("Qwen--Qwen2.5-Coder-7B-Instruct"), "qcoder7b"), ["--baseline-only"])
job(3, "base_qwen3_8b", 1, plan_for("base_qwen3_8b", snap("Qwen--Qwen3-8B"), "qwen3_8b"), ["--baseline-only"])
job(4, "base_granite8b", 1, plan_for("base_granite8b", snap("ibm-granite--granite-3.3-8b-instruct"), "granite3.3_8b"), ["--baseline-only"])
for k, (arm, over) in enumerate((("fixed", {}), ("nonrec", {"engine.recursive": False}),
                                 ("shuffled", {"engine.feedback": "shuffled"}),
                                 ("full", {"engine.candidates_per_round": 2, "meta.proposer": "self_edit"}))):
    name = f"main_q15_{arm}_s3"
    job(10 + k, name, 2, plan_for(name, q15, "qcoder1.5b", **dict(over, **{"engine.seed": 3})))
print(sorted(os.listdir(f"{Q}/pending")))

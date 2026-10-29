"""A800: queue a 500-episode baseline of the official OpenVLA LIBERO fine-tune for each suite whose checkpoint
has finished downloading (no *.incomplete left, every shard named in the index present).
usage: mkvla_base.py <order> <suite> [<suite> ...]     suites: libero_10 libero_spatial libero_object libero_goal"""
import json, os, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
CKPT = {"libero_goal": "/data1/work/zeyuwang/vla_demo/ckpts/openvla-7b-finetuned-libero-goal"}
for s in ("libero_10", "libero_spatial", "libero_object"):
    CKPT[s] = f"{H}/rsi/models/openvla/openvla-7b-finetuned-{s.replace('_', '-')}"
base = json.load(open(f"{H}/rsi/plans2/vla_base_goal.json"))


def complete(path):
    if not os.path.isdir(path) or any(f.endswith(".incomplete") for _, _, fs in os.walk(path) for f in fs):
        return False
    index = os.path.join(path, "model.safetensors.index.json")
    if not os.path.exists(index):
        return False
    shards = set(json.load(open(index))["weight_map"].values())
    return all(os.path.exists(os.path.join(path, f)) for f in shards)


order = int(sys.argv[1])
for k, suite in enumerate(sys.argv[2:]):
    ckpt = CKPT[suite]
    if not complete(ckpt):
        print("not ready", suite, ckpt)
        continue
    p = json.loads(json.dumps(base))
    p["model_name"] = f"openvla-7b-{suite.replace('_', '-')}"
    p["suite"] = suite
    p["vla"]["checkpoint"] = ckpt
    name = f"vla_baseline_{suite.replace('libero_', '')}_rep0"
    path = f"{H}/rsi/plans2/{name}.json"
    json.dump(p, open(path, "w"), indent=2)
    job = dict(name=name, ngpus=2, module="rsi.run_libero", plan=path, out=f"{H}/rsi/runs2/{name}",
               gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=["--baseline-only"],
               python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{H}/rsi/src2:{H}/rsi/pylib",
               cwd=f"{H}/rsi/src2")
    json.dump(job, open(f"{Q}/pending/{order + k:02d}_{name}.json", "w"), indent=1)
    print("queued", name, ckpt)

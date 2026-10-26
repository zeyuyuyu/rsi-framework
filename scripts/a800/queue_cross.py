"""A800: cross-model code-WM RSI arms (frozen seed program; only the model and arm keys change).
usage: queue_cross.py <order>:<tag>_<arm>_s<seed>[:<ngpus>] ...   e.g. 30:g8b_full_s1  32:qw3_fixed_s1:1
(ngpus defaults to 1: a 2-GPU code job leaves its second GPU idle while it trains)
tags: q7b (Qwen2.5-Coder-7B-Instruct), g8b (granite-3.3-8b-instruct), qw3 (Qwen3-8B, vLLM 0.11 env)."""
import glob, json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
OLD = (f"{H}/miniconda3/envs/vllm/bin/python", f"{H}/rsi/src2:{H}/rsi/pylib")
NEW = (f"{H}/miniconda3/envs/rsi-vllm11/bin/python", f"{H}/rsi/src2")
MODELS = {"q7b": ("Qwen--Qwen2.5-Coder-7B-Instruct", "qcoder7b", OLD),
          "g8b": ("ibm-granite--granite-3.3-8b-instruct", "granite3.3_8b", OLD),
          "qw3": ("Qwen--Qwen3-8B", "qwen3_8b", NEW)}
ARMS = {"fixed": {}, "nonrec": {"engine": {"recursive": False}}, "shuffled": {"engine": {"feedback": "shuffled"}},
        "full": {"engine": {"candidates_per_round": 2}, "meta": {"proposer": "self_edit"}}}
base = json.load(open(f"{H}/rsi/plans2/main_q15_fixed_s1.json"))
for spec in sys.argv[1:]:
    order, name, *ng = spec.split(":")
    tag, arm, seed = name.split("_")
    repo, mname, (py, pp) = MODELS[tag]
    p = json.loads(json.dumps(base))
    p["model_name"] = mname
    p["llm"].update(base_path=glob.glob(f"{H}/.cache/huggingface/hub/models--{repo}/snapshots/*/")[0],
                    python=py, pythonpath=pp)
    for sec, kv in ARMS[arm].items():
        p.setdefault(sec, {}).update(kv)
    p["engine"]["seed"] = int(seed[1:])
    run = f"cross_{name}"
    path = f"{H}/rsi/plans2/{run}.json"
    json.dump(p, open(path, "w"), indent=2)
    job = dict(name=run, ngpus=int(ng[0]) if ng else 1, module="rsi.run_code_wm", plan=path, out=f"{H}/rsi/runs2/{run}",
               gpu_fields={"llm.sample_gpus": "all", "llm.train_gpus": "first"}, args=[],
               python=py, pythonpath=pp, cwd=f"{H}/rsi/src2")
    json.dump(job, open(f"{Q}/pending/{int(order):02d}_{run}.json", "w"), indent=1)
    print("queued", run, json.dumps(dict(model=p["llm"]["base_path"], engine=p["engine"], meta=p["meta"])))

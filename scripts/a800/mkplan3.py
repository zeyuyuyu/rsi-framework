"""Plan maker for rsi.run_code_wm. usage: mkplan3.py name model_path gpus out key=json ..."""
import json, sys
name, path, gpus, out = sys.argv[1], sys.argv[2], [int(g) for g in sys.argv[3].split(",")], sys.argv[4]
H = "/data0/home/zeyuwang"
plan = dict(model_name=name,
    llm=dict(base_path=path, python=f"{H}/miniconda3/envs/vllm/bin/python",
             pythonpath=f"{H}/rsi/src2:{H}/rsi/pylib", sample_gpus=gpus, train_gpus=gpus[:1]),
    data=dict(cruxeval=f"{H}/rsi/data/cruxeval-org__cruxeval/test.jsonl",
              lcb=f"{H}/rsi/data/livecodebench__execution-v2/data/test-00000-of-00001.parquet"),
    heldout=dict(cache=f"{H}/rsi/runs2/heldout/{name}.jsonl", count=800, seed=12345),
    program={}, engine=dict(rounds=3, seed=0, candidates_per_round=1), meta=dict(proposer="fixed"))
for kv in sys.argv[5:]:
    k, v = kv.split("=", 1)
    node, keys = plan, k.split(".")
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = json.loads(v)
json.dump(plan, open(out, "w"), indent=2)

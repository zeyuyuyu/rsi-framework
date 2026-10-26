"""Baidu plans for the cross-model code-world-model arms (same frozen seed program, gate/audit/tests as the
1.5B study; only the model and the arm keys change). usage: mkplans_models.py <tag>_<arm>_s<seed> ...
tags: q7b (Qwen2.5-Coder-7B-Instruct), g8b (granite-3.3-8b-instruct), qw3 (Qwen3-8B)."""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).parent
base = json.loads((HERE / "a800_main_q15_fixed_s1.json").read_text())
D = "/mnt/bos/shitianyu-rsi/data"
MODELS = {"q7b": ("Qwen2.5-Coder-7B-Instruct", "qcoder7b"),
          "g8b": ("granite-3.3-8b-instruct", "granite3.3_8b"),
          "qw3": ("Qwen3-8B", "qwen3_8b")}
ARMS = {"fixed": {}, "nonrec": dict(engine=dict(recursive=False)),
        "shuffled": dict(engine=dict(feedback="shuffled")),
        "full": dict(engine=dict(candidates_per_round=2), meta=dict(proposer="self_edit"))}
for spec in sys.argv[1:]:
    tag, arm, seed = spec.split("_")
    mdir, mname = MODELS[tag]
    p = copy.deepcopy(base)
    p["model_name"] = mname
    p["llm"] = dict(base_path=f"/mnt/pfs/shitianyu-rsi/models/{mdir}",
                    python="/usr/bin/python3", pythonpath="/tmp/src",
                    sample_gpus=[0], train_gpus=[0], tensor_parallel=1)
    p["data"] = dict(cruxeval=f"{D}/cruxeval-org__cruxeval/test.jsonl",
                     lcb=f"{D}/livecodebench__execution-v2/data/test-00000-of-00001.parquet")
    p["heldout"]["cache"] = f"/mnt/pfs/shitianyu-rsi/runs/heldout/{mname}.jsonl"  # unused: source=mbpp
    p["heldout"]["paths"] = [f"{D}/google-research-datasets__mbpp/full/{s}-00000-of-00001.parquet"
                             for s in ("train", "validation", "test")]
    for sec, kv in dict(ARMS[arm], engine=dict(ARMS[arm].get("engine", {}), seed=int(seed[1:]))).items():
        p.setdefault(sec, {}).update(kv)
    (HERE / "plans" / f"bj_{spec}.json").write_text(json.dumps(p, indent=2) + "\n")
    print(spec, json.dumps(dict(model=p["llm"]["base_path"], engine=p["engine"], meta=p["meta"])))

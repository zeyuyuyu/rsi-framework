"""Baidu plans for the Qwen2.5-Coder-1.5B code-world-model arms, derived from the A800 plan.
Only paths/GPU keys and the arm keys change; program/engine/heldout.source are kept."""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).parent
base = json.loads((HERE / "a800_main_q15_fixed_s1.json").read_text())
D = "/mnt/bos/shitianyu-rsi/data"
ARMS = {
    "full_s1":     dict(engine=dict(seed=1, candidates_per_round=2), meta=dict(proposer="self_edit")),
    "full_s2":     dict(engine=dict(seed=2, candidates_per_round=2), meta=dict(proposer="self_edit")),
    "fixed_s2":    dict(engine=dict(seed=2)),
    "nonrec_s2":   dict(engine=dict(seed=2, recursive=False)),
    "shuffled_s2": dict(engine=dict(seed=2, feedback="shuffled")),
}
for arm, over in ARMS.items():
    p = copy.deepcopy(base)
    p["llm"] = dict(base_path="/mnt/pfs/shitianyu-rsi/models/Qwen2.5-Coder-1.5B-Instruct",
                    python="/usr/bin/python3", pythonpath="/tmp/src",
                    sample_gpus=[0], train_gpus=[0], tensor_parallel=1)
    p["data"] = dict(cruxeval=f"{D}/cruxeval-org__cruxeval/test.jsonl",
                     lcb=f"{D}/livecodebench__execution-v2/data/test-00000-of-00001.parquet")
    p["heldout"]["cache"] = "/mnt/pfs/shitianyu-rsi/runs/heldout/qcoder1.5b.jsonl"  # unused: source=mbpp
    p["heldout"]["paths"] = [f"{D}/google-research-datasets__mbpp/full/{s}-00000-of-00001.parquet"
                             for s in ("train", "validation", "test")]
    for sec, kv in over.items():
        p.setdefault(sec, {}).update(kv)
    (HERE / "plans" / f"bj_q15_{arm}.json").write_text(json.dumps(p, indent=2) + "\n")
    print(arm, json.dumps(dict(engine=p["engine"], meta=p["meta"])))

#!/bin/bash
# Print per-episode success bits of finished robotics runs on PFS (the BOS copies are not readable from outside).
# env: RUNS="run_dir_name ..." under /mnt/pfs/shitianyu-rsi/runs
for r in $RUNS; do
  d=/mnt/pfs/shitianyu-rsi/runs/$r
  echo "== $r: $(ls $d | tr '\n' ' ')"
  python3 - "$d" "$r" <<'PY'
import glob, hashlib, json, os, sys
d, r = sys.argv[1], sys.argv[2]
for p in sorted(glob.glob(os.path.join(d, "test-*.jsonl")) + glob.glob(os.path.join(d, "baseline-rep*.jsonl"))):
    recs = [json.loads(l) for l in open(p) if l.strip()]
    ids = hashlib.sha256(json.dumps([x["id"] for x in recs]).encode()).hexdigest()[:16]
    print("TESTBITS", r, os.path.basename(p), len(recs), ids, "".join("1" if x["score"] >= 0.5 else "0" for x in recs))
    print("IDS_HEAD", r, json.dumps([x["id"] for x in recs[:3]]))
PY
done

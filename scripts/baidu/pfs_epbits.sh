#!/bin/bash
# Print per-episode success bits of robotics runs on PFS for cross-platform pairing: for every per-episode
# jsonl in the run dir (gate-*, audit-*, heldout*, test-*, baseline-*; not the raw attempts/cases), one line
#   EPBITS <run> <file> <n> <ids sha256[:16]> <bits in sorted-id order>
# env: RUNS="run_dir_name ..." under /mnt/pfs/shitianyu-rsi/runs
for r in $RUNS; do
  d=/mnt/pfs/shitianyu-rsi/runs/$r
  echo "== $r: $(ls $d 2>&1 | grep -vE -- '-(cases|attempts)-|^ckpt-' | tr '\n' ' ')"
  python3 - "$d" "$r" <<'PY'
import glob, hashlib, json, os, sys
d, r = sys.argv[1], sys.argv[2]
for p in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
    name = os.path.basename(p)
    if "-cases-" in name or "-attempts-" in name or name in ("archive.jsonl", "accepted.jsonl"):
        continue
    try:
        recs = [json.loads(l) for l in open(p) if l.strip()]
    except ValueError:
        continue
    recs = [x for x in recs if "id" in x and "score" in x]
    if not recs:
        continue
    recs.sort(key=lambda x: x["id"])
    ids = hashlib.sha256(json.dumps([x["id"] for x in recs]).encode()).hexdigest()[:16]
    print("EPBITS", r, name, len(recs), ids, "".join("1" if x["score"] >= 0.5 else "0" for x in recs))
    print("EPIDS_HEAD", r, name, json.dumps([x["id"] for x in recs[:2]]))
PY
done
echo PFS_EPBITS_DONE

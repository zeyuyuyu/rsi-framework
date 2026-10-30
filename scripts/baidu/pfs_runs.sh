#!/bin/bash
# Print the selection records of robotics runs on PFS, which no log carries in full: ROUND lines show gates only,
# and the audits of accepted nodes live in accepted.jsonl / archive.jsonl. Running runs are fine (read-only).
# env: RUNS="run_dir_name ..." under /mnt/pfs/shitianyu-rsi/runs
for r in $RUNS; do
  d=/mnt/pfs/shitianyu-rsi/runs/$r
  echo "== $r: $(ls $d 2>&1 | grep -vE -- '-(cases|attempts)-|^test-|^ckpt-' | tr '\n' ' ')"
  for f in accepted.jsonl report.json; do
    [ -f "$d/$f" ] && { echo "----- $r/$f"; cat "$d/$f"; echo; }
  done
  python3 - "$d" "$r" <<'PY'
import glob, json, os, sys
d, r = sys.argv[1], sys.argv[2]
for p in sorted(glob.glob(os.path.join(d, "round-[0-9][0-9].json"))):
    x = json.load(open(p))
    print("ROUNDFILE", r, json.dumps(dict(round=x["round"], parent=x.get("parent"), accepted=x.get("accepted"),
          candidates=[dict(node=c["node"], gate=c.get("gate"), audit=c.get("audit")) for c in x.get("candidates", [])])))
a = os.path.join(d, "archive.jsonl")
if os.path.exists(a):
    for line in open(a):
        n = json.loads(line)
        print("ARCHIVE", r, json.dumps(dict(node=n.get("node_id"), round=n.get("round"), parent=n.get("parent_node"),
              gate=n.get("gate"), audit=n.get("audit"), accepted=n.get("accepted"))))
PY
done
echo PFS_RUNS_DONE

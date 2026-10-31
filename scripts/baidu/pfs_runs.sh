#!/bin/bash
# Print the selection records of robotics runs on PFS, which no log carries in full: ROUND lines show gates only,
# and the audits of accepted nodes live in accepted.jsonl / archive.jsonl. Running runs are fine (read-only).
# env: RUNS="run_dir_name ..." under RUNROOT (default /mnt/pfs/shitianyu-rsi/runs; Yangquan: /mnt/cfs/shitianyu-rsi/runs)
for r in $RUNS; do
  d=${RUNROOT:-/mnt/pfs/shitianyu-rsi/runs}/$r
  echo "== $r: $(ls $d 2>&1 | grep -vE -- '-(cases|attempts)-|^test-|^ckpt-' | tr '\n' ' ')"
  for f in accepted.jsonl report.json; do
    [ -f "$d/$f" ] && { echo "----- $r/$f"; cat "$d/$f"; echo; }
  done
  python3 - "$d" "$r" <<'PY'
import glob, json, os, sys
d, r = sys.argv[1], sys.argv[2]
for p in sorted(glob.glob(os.path.join(d, "round-[0-9][0-9].json"))):
    x = json.load(open(p))
    print("ROUNDFILE", r, json.dumps(dict(round=x["round"], parent=x.get("parent"), parent_gate=x.get("parent_gate"),
          accepted=x.get("accepted"),
          candidates=[dict(node=c["node"], gate=c.get("gate"), audit=c.get("audit"),
                           verified_rate=(c.get("signal") or {}).get("verified_rate"),
                           mixed_fraction=(c.get("signal") or {}).get("mixed_fraction"),
                           inner_verified=[(s.get("signal") or {}).get("verified_rate")
                                           for s in (c.get("signal") or {}).get("inner") or []])
                      for c in x.get("candidates", [])])))
for p in sorted(glob.glob(os.path.join(d, "ckpt-*", "receipt.json")))[:1]:
    e = json.load(open(p)).get("extra", {})
    print("RECEIPT_SETTINGS", r, os.path.basename(os.path.dirname(p)), json.dumps(dict(
        loss_agg=e.get("loss_agg"), ratio_mode=e.get("ratio_mode"), lr=(e.get("update") or {}).get("lr"))))
a = os.path.join(d, "archive.jsonl")
if os.path.exists(a):
    for line in open(a):
        n = json.loads(line)
        print("ARCHIVE", r, json.dumps(dict(node=n.get("node_id"), round=n.get("round"), parent=n.get("parent_node"),
              gate=n.get("gate"), audit=n.get("audit"), accepted=n.get("accepted"))))
m = os.path.join(d, "meta-llm.jsonl")
if os.path.exists(m):
    for line in open(m):
        try: c = json.loads(line)
        except ValueError: continue
        print("METALLM", r, json.dumps(dict(llm_programs=c.get("llm_programs"), fallback_programs=c.get("fallback_programs"),
              rejected=c.get("rejected"), dropped_fields=c.get("dropped_fields"),
              diagnosis=str(c.get("diagnosis") or "")[:400])))
PY
done
echo PFS_RUNS_DONE

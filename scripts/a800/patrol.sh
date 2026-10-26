#!/bin/bash
# One-shot patrol of the A800 RSI runs (read-only).
tail -4 ~/rsi/queue/runner.log
echo "pending: $(ls ~/rsi/queue/pending 2>/dev/null | tr '\n' ' ')"
echo "running: $(ls ~/rsi/queue/running 2>/dev/null | tr '\n' ' ')"
echo "failed: $(ls ~/rsi/queue/failed 2>/dev/null | tr '\n' ' ')"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
for f in ~/rsi/runs2/main_* ~/rsi/runs2/base_* ~/rsi/runs2/vla_*; do
  [ -d "$f" ] || continue; case "$f" in *.work) continue;; esac
  n=$(basename $f); st=""
  [ -f $f/report.json ] && st=DONE
  [ -f $f/baseline.json ] && st="BASELINE $(tr -d '\n ' < $f/baseline.json | cut -c1-200)"
  [ -f $f/failure.json ] && st="FAILED $(tr -d '\n' < $f/failure.json | cut -c1-200)"
  nodes=$(python3 - "$f" <<'PY'
import json, sys
out = []
try:
    for l in open(sys.argv[1] + "/archive.jsonl"):
        r = json.loads(l)
        if "event" in r:
            out.append(f"ACC:{r['node_id']}")
        else:
            g = r.get("gate")
            out.append(f"{r['node_id']}={round(g, 4) if g else None}")
except FileNotFoundError:
    pass
print(" ".join(out))
PY
)
  echo "$n $st | $nodes | last=$(ls -t ${f}.work 2>/dev/null | head -1)"
done
echo "vla episodes: $(cat ~/rsi/runs2/vla_baseline_goal_rep0.work/*/episodes/results-*.jsonl 2>/dev/null | wc -l)"

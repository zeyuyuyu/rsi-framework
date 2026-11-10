#!/bin/bash
# Close finished Yangquan runs of addenda 28-30: fetch their final logs, and for every run that now has report.json
# submit what is still missing: the two replicate test evaluations (<run>_rep) and the sealed fresh-scene evaluation
# (<run>_fresh). Idempotent: a run whose job name is already in jobs_yq.tsv is skipped. Prints one line per action.
# usage: close_yq.sh [max_new_jobs=6]     (addendum 30: cards are scarce, so the number of submissions per call is capped)
cd "$(dirname "$0")/../.." || exit 1
L=/home/zeyu/rsi/yq_logs; max=${1:-6}; n=0
bash scripts/baidu/collect_yq.sh "$L" 120 | grep "^fetched" | cut -c1-100
for d in results/baidu/yq_ofts_*_s[0-9] results/baidu/yq_oftsb_*_s[0-9]; do
  run=$(basename "$d"); [ -f "$d/report.json" ] || continue
  job=zw-rsi-$(echo "$run" | tr _ -)
  if ! grep -q -P "^${job}-rep\t" scripts/baidu/jobs_yq.tsv; then
    [ $n -ge $max ] && { echo "cap reached; more to submit next call"; break; }
    echo "REP $run: $(bash scripts/baidu/submit_rep_yq.sh "$run" 2>&1 | tail -1 | cut -c1-80)"; n=$((n + 1))
  fi
  if ! grep -q -P "^${job}-fresh\t" scripts/baidu/jobs_yq.tsv; then
    [ $n -ge $max ] && { echo "cap reached; more to submit next call"; break; }
    echo "FRESH $run: $(bash scripts/baidu/submit_fresh_yq.sh "$run" 2>&1 | tail -1 | cut -c1-80)"; n=$((n + 1))
  fi
done
echo "close_yq: $n submitted"

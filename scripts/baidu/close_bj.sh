#!/bin/bash
# Addendum 33 amendment 1: close finished Beijing runs (bj_ofts_*), as close_yq.sh does on Yangquan.
#   1. fetch the final log of every *ended* addendum-33 Beijing job in jobs.tsv that has no saved log yet, and extract
#      the run records into results/baidu (poll_job.py is only called on ended jobs: it stops jobs pending > 20 min)
#   2. for every bj_ofts run that now has report.json, submit what is still missing: the two replicate test
#      evaluations (<run>_rep) and the sealed fresh-scene evaluation (<run>_fresh), on source v32 like the runs.
# Idempotent: a job name already in jobs.tsv is not submitted again. Prints one line per action.
# usage: close_bj.sh [max_new_jobs=6]
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.bj.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-i7kkoqptnigl
export RSI_SRC_TGZ=/mnt/bos/shitianyu-rsi/src/rsi_src_v32.tar.gz
L=/home/zeyu/rsi/bj_logs; max=${1:-6}; n=0; mkdir -p "$L"
T=scripts/baidu/jobs.tsv
MODEL=Haozhan72/Openvla-oft-SFT-libero-spatial-traj1
have() { grep -q -P "^zw-rsi-$(echo "$1" | tr _ -)\t" $T; }
grep -P "^zw-rsi-bj-(ofts|fresh-n0-spatial)-" $T | awk -F'\t' '{a[$1]=$2} END {for (k in a) print k"\t"a[k]}' | while IFS=$'\t' read name job; do
  [ -f "$L/$name.$job.log" ] && continue
  st=$(timeout 40 python3 scripts/baidu/aihc_job.py describe "$job" 2>/dev/null | python3 -c '
import json,sys
t=sys.stdin.read(); i=t.find("{")
try: d=json.loads(t[i:]); print(d.get("status"))
except Exception: print("?")')
  case "$st" in Succeeded|Failed|ManualTermination|Stopped|Terminated|Completed) ;; *) continue ;; esac
  timeout 300 python3 scripts/baidu/poll_job.py "$job" "$L" >/dev/null 2>&1 && cp "$L/$job.log" "$L/$name.$job.log" && echo "fetched $name $job ($st)"
done
python3 scripts/baidu/extract_results.py "$L" results/baidu 2>&1 | grep -v "^$" | sed 's/\[.*\] changed/changed/' | cut -c1-120
for d in results/baidu/bj_ofts_*_s[0-9]; do
  run=$(basename "$d"); [ -f "$d/report.json" ] || continue
  # the run's directory on the Beijing PFS, as its own result block names it (run_vla.sh may add a timestamp)
  pfs=$(grep -ho "RSI_RESULT_BEGIN name=$run run=[^ ]*" "$d"/SOURCE-*.txt 2>/dev/null | head -1 | sed 's/.* run=//')
  [ -n "$pfs" ] || { echo "SKIP $run: no run= in its SOURCE file"; continue; }
  for kind in rep fresh; do
    have ${run}_$kind && continue
    [ $n -ge $max ] && { echo "cap reached; more to submit next call"; break 2; }
    if [ $kind = rep ]; then args="--test-eval /mnt/pfs/shitianyu-rsi/runs/$pfs --replicates 2"; else args="--fresh-eval /mnt/pfs/shitianyu-rsi/runs/$pfs"; fi
    echo "$(echo $kind | tr a-z A-Z) $run: $(RUN_NAME=${run}_$kind ARGS="$args" timeout 120 python3 scripts/baidu/submit_vla.py "$run" $MODEL 2>&1 | tail -1 | cut -c1-80)"
    n=$((n + 1))
  done
done
echo "close_bj: $n submitted"

#!/bin/bash
# Fetch the final logs of every terminal Yangquan job in jobs_yq.tsv that has no saved log yet, name them for
# extract_results.py (zw-rsi-<run>.<job>.log) and extract the run records into results/baidu.
# usage: collect_yq.sh [log_dir=/home/zeyu/rsi/yq_logs] [tail_rows=60]
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
L=${1:-/home/zeyu/rsi/yq_logs}; n=${2:-60}; mkdir -p "$L"; new=0
tail -n "$n" scripts/baidu/jobs_yq.tsv | awk -F'\t' '{a[$1]=$2} END {for (k in a) print k"\t"a[k]}' | while IFS=$'\t' read name job; do
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

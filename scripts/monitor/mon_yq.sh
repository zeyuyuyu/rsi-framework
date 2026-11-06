#!/bin/bash
# Event stream for a Monitor: status changes (terminal states) of the newest Yangquan jobs in scripts/baidu/jobs_yq.tsv.
# usage: mon_yq.sh [state_file] [how_many_tail_rows]
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
prev=${1:-/tmp/mon_yq_status.txt}; n=${2:-40}; touch "$prev"
while true; do
  cur=$(tail -n "$n" scripts/baidu/jobs_yq.tsv | awk -F'\t' '{a[$1]=$2} END {for (k in a) print k"\t"a[k]}' | sort | while IFS=$'\t' read name job; do
    st=$(timeout 40 python3 scripts/baidu/aihc_job.py describe "$job" 2>/dev/null | python3 -c '
import json,sys
t=sys.stdin.read(); i=t.find("{")
try: d=json.loads(t[i:]); print(d.get("status"))
except Exception: print("?")'); echo "$name $st"; done)
  comm -13 <(sort "$prev") <(echo "$cur" | sort) | grep -v -E " (\?|Running|Created|Pending|Queueing)$"
  echo "$cur" > "$prev"; sleep 600
done

#!/bin/bash
# 30-min patrol summary: cavin proxy/runner/disk/runs + Yangquan newest job statuses.
cd "$(dirname "$0")/../.." || exit 1
timeout 120 ssh -o ConnectTimeout=20 cavin 'date -u +%H:%MZ; curl -s -o /dev/null -w "proxy http=%{http_code}\n" --max-time 20 -x http://127.0.0.1:1080 https://openrouter.ai/api/v1/models; tail -n 3 ~/rsi/queue/runner.log; echo pending: $(ls ~/rsi/queue/pending | wc -l) running: $(ls ~/rsi/queue/running | wc -l); df -h /data0 | tail -1; find ~/rsi/runs2 -maxdepth 2 -name failure.json -newermt "-40 min"; cd ~/rsi/runs2; for d in $(ls -d a8_oftgb_*_s0 a8_goalmain_*_rep 2>/dev/null); do echo "$d $(ls $d | grep -E "^round-[0-9]+\.json" | tail -1) $([ -f $d/report.json ] && echo DONE) $([ -f $d/test_eval.json ] && echo TESTEVAL_DONE)"; done; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" ";"; echo' 2>&1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
tail -n 40 scripts/baidu/jobs_yq.tsv | awk -F'\t' '{a[$1]=$2} END {for (k in a) print k"\t"a[k]}' | sort | while IFS=$'\t' read name job; do st=$(timeout 40 python3 scripts/baidu/aihc_job.py describe "$job" 2>/dev/null | python3 -c '
import json,sys
t=sys.stdin.read(); i=t.find("{")
try: d=json.loads(t[i:]); print(d.get("status"))
except Exception: print("?")'); echo "$st $name"; done | sort | awk '{c[$1]++; if ($1!="Running" && $1!="Succeeded") print} END {for (k in c) printf "%s=%d ", k, c[k]; print ""}'

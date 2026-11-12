#!/bin/bash
# Relay for the Yangquan conductor: wait until the rsi-conductor-yq user unit has ended (its loop runs out around
# 2026-11-14 09Z), then run close_yq.sh every 5 minutes until 2026-11-15 13:00Z. Never runs close_yq while the
# conductor is active (that would double-submit).
cd "$(dirname "$0")/../.." || exit 1
L=/home/zeyu/rsi/yq_logs; log=$L/conductor_1111.log
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
while systemctl --user is-active --quiet rsi-conductor-yq; do sleep 300; done
echo "$(date -u +%FT%TZ) close_loop_yq start (conductor ended)" >> $log
while [ "$(date -u +%s)" -lt "$(date -u -d 2026-11-15T13:00:00Z +%s)" ]; do
  bash scripts/baidu/close_yq.sh 30 2>&1 | grep -v "^close_yq: 0" | while read l; do echo "$(date -u +%FT%TZ) close: $l" >> $log; done
  sleep 300
done
echo "$(date -u +%FT%TZ) close_loop_yq end" >> $log

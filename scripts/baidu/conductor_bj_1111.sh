#!/bin/bash
# Beijing conductor for addendum 33 amendment 1: every 10 min, close finished bj_ofts runs (close_bj.sh: logs,
# extraction, two replicate evaluations and one fresh-scene evaluation per run). Ends when all twelve close-out
# evaluations of the six runs and the four reference evaluations are extracted, or after 96 h.
cd "$(dirname "$0")/../.." || exit 1
L=/home/zeyu/rsi/bj_logs; mkdir -p $L; log=$L/conductor_bj.log
say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
say "conductor_bj start"
for i in $(seq 1 576); do
  bash scripts/baidu/close_bj.sh 12 2>&1 | grep -v "^close_bj: 0 submitted" | while read l; do say "close: $l"; done
  left=0
  for arm in guard onebig; do for s in 1 2 3; do for k in rep fresh; do
    [ -f results/baidu/bj_ofts_${arm}_s${s}_$k/tests.txt ] || left=$((left + 1))
  done; done; done
  for k in 1 2 3 4; do [ -f results/baidu/bj_fresh_n0_spatial_$k/tests.txt ] || left=$((left + 1)); done
  [ $left -eq 0 ] && { say "all Beijing close-out and reference evaluations extracted"; break; }
  [ $((i % 6)) -eq 1 ] && say "waiting: $left Beijing evaluations not yet extracted"
  sleep 600
done
say "conductor_bj end"

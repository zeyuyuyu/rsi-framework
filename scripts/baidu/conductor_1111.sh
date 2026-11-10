#!/bin/bash
# Addenda 28-31, Yangquan: keep the queue ordered without a person in the loop (2026-11-11).
#   A. every 5 min: close finished runs (replicates + fresh-scene evaluation; close_yq.sh)
#   B. once, at start: four fresh-scene evaluations of the initial Spatial policy
#   C. once, when all twelve addendum-28 runs are finished and closed: the Goal main fresh-scene evaluations, then
#      the long runs that were stopped while waiting (same names and plans) and the new ones, in the registered order
# The pool gives us about 15 cards and starts waiting jobs in submission order, so evaluations (1 h) go in before
# long runs (14-31 h). State: /home/zeyu/rsi/yq_logs/conductor_1111.state  log: conductor_1111.log
cd "$(dirname "$0")/../.." || exit 1
L=/home/zeyu/rsi/yq_logs; st=$L/conductor_1111.state; log=$L/conductor_1111.log; touch $st
say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
once() { grep -qx "$1" $st; }
mark() { echo "$1" >> $st; }
have() { grep -q -P "^zw-rsi-$(echo "$1" | tr _ -)\t" scripts/baidu/jobs_yq.tsv; }
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
say "conductor start"
for i in $(seq 1 400); do
  if ! once n0_spatial; then
    for k in 1 2 3 4; do say "n0 spatial $k: $(bash scripts/baidu/submit_fresh_yq.sh n0 spatial $k 2>&1 | tail -1 | cut -c1-70)"; done; mark n0_spatial
  fi
  bash scripts/baidu/close_yq.sh 30 2>&1 | grep -v "^close_yq: 0" | while read l; do say "close: $l"; done
  if ! once long_runs; then
    done_main=0; closed=0
    for arm in fixed nonrec shuffled onebig; do for s in 1 2 3; do
      r=yq_ofts_${arm}_s$s
      [ -f results/baidu/$r/report.json ] && done_main=$((done_main + 1))
      have ${r}_rep && have ${r}_fresh && closed=$((closed + 1))
    done; done
    if [ $done_main -eq 12 ] && [ $closed -eq 12 ]; then
      say "all 12 Spatial main runs finished and closed -> Goal main fresh evaluations, then long runs"
      for arm in fixed nonrec shuffled onebig; do for s in 1 2 3; do
        say "goal fresh $arm s$s: $(bash scripts/baidu/submit_fresh_yq.sh yq_oftg_${arm}_s$s 2>&1 | tail -1 | cut -c1-70)"
      done; done
      for r in yq_oftsb_meta3_s2 yq_oftsb_meta3_s3; do say "resubmit $r: $(NGPU=2 bash scripts/baidu/submit_spatial_repair_yq.sh $r 2>&1 | tail -1 | cut -c1-70)"; done
      for r in yq_oftsb_fixed_s2 yq_oftsb_fixed_s3; do say "resubmit $r: $(NGPU=1 bash scripts/baidu/submit_spatial_repair_yq.sh $r 2>&1 | tail -1 | cut -c1-70)"; done
      export JOB_CPU=8 JOB_MEM=100 JOB_GPU=1 RSI_SRC_URL="$(cat $L/src_v30.url)"
      for r in yq_oftsb_nogate_s1 yq_oftsb_nogate_s2 yq_oftsb_nogate_s3 yq_ofts_fixed12_s1 yq_ofts_fixed12_s2 yq_ofts_fixed12_s3 \
               yq_ofts_nonrec12_s1 yq_ofts_nonrec12_s2 yq_ofts_nonrec12_s3; do
        say "submit $r: $(RUN_NAME=$r timeout 120 python3 scripts/baidu/submit_vla_yq2.py $r Haozhan72/Openvla-oft-SFT-libero-spatial-traj1 2>&1 | tail -1 | cut -c1-90)"
      done
      unset JOB_GPU RSI_SRC_URL
      mark long_runs
    else
      [ $((i % 6)) -eq 1 ] && say "waiting: Spatial main finished $done_main/12, closed $closed/12"
    fi
  fi
  sleep 300
done
say "conductor end"

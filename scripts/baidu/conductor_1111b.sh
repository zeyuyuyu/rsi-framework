#!/bin/bash
# Yangquan conductor, version 2 (addendum 32 order). Replaces conductor_1111.sh; shares its state file, so what that
# one already did (the four initial-policy Spatial evaluations) is not repeated.
#   A. every 5 min: close finished runs (replicates + fresh-scene evaluation; close_yq.sh)
#   B. once, now: fresh-scene evaluations of the six addendum-24 Goal runs that NG1/NG2 are paired with
#   C. once, when all twelve addendum-28 runs are finished and closed: the Goal main fresh-scene evaluations, then the
#      long runs in the order of addendum 32 (first wave fills the pool; the second wave waits in the queue behind it)
cd "$(dirname "$0")/../.." || exit 1
L=/home/zeyu/rsi/yq_logs; st=$L/conductor_1111.state; log=$L/conductor_1111.log; touch $st
say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
once() { grep -qx "$1" $st; }
mark() { echo "$1" >> $st; }
have() { grep -q -P "^zw-rsi-$(echo "$1" | tr _ -)\t" scripts/baidu/jobs_yq.tsv; }
plain() {   # run model src_url_file [ngpu]
  ( export JOB_CPU=8 JOB_MEM=100 JOB_GPU=${4:-1} RSI_SRC_URL="$(cat $L/$3)"
    [ "${4:-1}" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
    RUN_NAME=$1 timeout 120 python3 scripts/baidu/submit_vla_yq2.py $1 Haozhan72/Openvla-oft-SFT-libero-$2-traj1 2>&1 | tail -1 | cut -c1-90 )
}
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
say "conductor v2 start"
for i in $(seq 1 500); do
  if ! once goal_bc_fresh; then
    for arm in fixed llm_harness; do for s in 1 2 3; do
      say "goal BC fresh $arm s$s: $(bash scripts/baidu/submit_fresh_yq.sh yq_oftgb_${arm}_s$s 2>&1 | tail -1 | cut -c1-70)"
    done; done; mark goal_bc_fresh
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
      say "all 12 Spatial main runs finished and closed -> Goal main fresh evaluations, then long runs (addendum 32 order)"
      for arm in fixed nonrec shuffled onebig; do for s in 1 2 3; do
        say "goal fresh $arm s$s: $(bash scripts/baidu/submit_fresh_yq.sh yq_oftg_${arm}_s$s 2>&1 | tail -1 | cut -c1-70)"
      done; done
      for s in 1 2 3; do say "submit yq_oftg_guard12_s$s: $(plain yq_oftg_guard12_s$s goal src_v32.url)"; done
      for s in 1 2 3; do say "submit yq_oftgb_nogate_s$s: $(plain yq_oftgb_nogate_s$s goal src_v32.url)"; done
      for s in 1 2 3; do say "submit yq_oftsb_nogate_s$s: $(plain yq_oftsb_nogate_s$s spatial src_v30.url)"; done
      for r in yq_oftsb_meta3_s2 yq_oftsb_meta3_s3; do say "resubmit $r: $(NGPU=2 bash scripts/baidu/submit_spatial_repair_yq.sh $r 2>&1 | tail -1 | cut -c1-70)"; done
      for r in yq_oftsb_fixed_s2 yq_oftsb_fixed_s3; do say "resubmit $r: $(NGPU=1 bash scripts/baidu/submit_spatial_repair_yq.sh $r 2>&1 | tail -1 | cut -c1-70)"; done
      for s in 1 2 3; do say "submit yq_ofts_fixed12_s$s: $(plain yq_ofts_fixed12_s$s spatial src_v30.url)"; done
      for s in 1 2 3; do say "submit yq_ofts_nonrec12_s$s: $(plain yq_ofts_nonrec12_s$s spatial src_v30.url)"; done
      mark long_runs
    else
      [ $((i % 6)) -eq 1 ] && say "waiting: Spatial main finished $done_main/12, closed $closed/12"
    fi
  fi
  sleep 300
done
say "conductor v2 end"

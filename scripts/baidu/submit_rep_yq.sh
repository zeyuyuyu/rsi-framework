#!/bin/bash
# Submit the registered 2-replicate test evaluation of an ended Yangquan run (<run>_rep), on NGPU cards (run_vla6.sh).
# usage: [NGPU=3] submit_rep_yq.sh <run>
set -u
run=$1; L=/home/zeyu/rsi/yq_logs
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip JOB_CPU=8 JOB_MEM=100
# addendum 28: Spatial runs (yq_ofts_*) replicate on their own checkpoint and source (v28); every other run as before
case "$run" in yq_oftg_guard12_*|yq_oftgb_nogate_*) model=Haozhan72/Openvla-oft-SFT-libero-goal-traj1; src=src_v32;;   # addendum 32
  yq_ofts_guard_*|yq_ofts_guard12_*) model=Haozhan72/Openvla-oft-SFT-libero-spatial-traj1; src=src_v32;;   # addenda 33, 34
  yq_oftsb_nogate_*|yq_ofts_*12_*) model=Haozhan72/Openvla-oft-SFT-libero-spatial-traj1; src=src_v30;;   # addenda 30, 31
  yq_oftsb_*|yq_ofts_meta3_*) model=Haozhan72/Openvla-oft-SFT-libero-spatial-traj1; src=src_v29;;   # addendum 29
  yq_ofts_*) model=Haozhan72/Openvla-oft-SFT-libero-spatial-traj1; src=src_v28;; *) model=Haozhan72/Openvla-oft-SFT-libero-goal-traj1; src=src_v27;; esac
export RSI_SRC_URL="$(cat $L/$src.url)" ARGS="--test-eval /mnt/pfs/shitianyu-rsi/runs/$run --replicates 2"
ngpu=${NGPU:-1}; export JOB_GPU=$ngpu
[ "$ngpu" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
RUN_NAME="${run}_rep" python3 scripts/baidu/submit_vla_yq2.py "$run" "$model" | tail -1 | cut -c1-120
tail -n 1 scripts/baidu/jobs_yq.tsv

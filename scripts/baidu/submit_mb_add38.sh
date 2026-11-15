#!/bin/bash
# Addendum 38: resume a continued run up to tuned RL's counted budget.
# usage: submit_mb_add38.sh <seed 1|3> <cards> [suffix]   (suffix makes a new job name after a queued job was stopped)
# RUN_TIMEOUT_S = min(left card-hours / cards, time to the 20:30Z cut-off) minus 15 min of job setup.
set -eu
cd "$(dirname "$0")/../.."
L=/home/zeyu/rsi/yq_logs
seed=$1; cards=$2; sfx=${3:-}
case $seed in 1) run=yq_oftgbx_ext_s1b; left=98.9;; 3) run=yq_oftgbx_ext_s3; left=127.4;; *) echo "seed 1 or 3"; exit 1;; esac
left=${LEFT:-$left}   # amendment 1: card-hours still left for this seed when resubmitting
cut=$(date -u -d "${CUT:-2026-11-15 20:30}" +%s); now=$(date -u +%s)   # amendment 1: seed 3 CUT="2026-11-16 18:00"
t=$(python3 -c "print(int(min($left / $cards * 3600, $cut - $now) - 900))")
[ "$t" -gt 1800 ] || { echo "too little time left: $t s"; exit 1; }
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
export JOB_GPU=$cards JOB_CPU=$(( 12 * cards )) JOB_MEM=$(( cards > 1 ? 100 * cards : 120 ))   # amendment 2: 12 CPUs, 100 GiB per card
export RSI_SRC_URL="$(cat $L/src_v34.url)" RESUME_RUN=$run RUN_TIMEOUT_S=$t RUN_NAME=yq_oftgbx_mb_s${seed}${sfx}
[ "$cards" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
echo "$(date -u +%FT%TZ) submit $RUN_NAME resume=$run cards=$cards timeout=$t"
timeout 120 python3 scripts/baidu/submit_vla_yq2.py yq_oftgbx_ext_s$seed Haozhan72/Openvla-oft-SFT-libero-goal-traj1 2>&1 | tail -1 | cut -c1-160

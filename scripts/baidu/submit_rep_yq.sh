#!/bin/bash
# Submit the registered 2-replicate test evaluation of an ended Yangquan run (<run>_rep), on NGPU cards (run_vla6.sh).
# usage: [NGPU=3] submit_rep_yq.sh <run>
set -u
run=$1; L=/home/zeyu/rsi/yq_logs
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip JOB_CPU=8 JOB_MEM=100
export RSI_SRC_URL="$(cat $L/src_v27.url)" ARGS="--test-eval /mnt/pfs/shitianyu-rsi/runs/$run --replicates 2"
ngpu=${NGPU:-1}; export JOB_GPU=$ngpu
[ "$ngpu" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
RUN_NAME="${run}_rep" python3 scripts/baidu/submit_vla_yq2.py "$run" Haozhan72/Openvla-oft-SFT-libero-goal-traj1 | tail -1 | cut -c1-120
tail -n 1 scripts/baidu/jobs_yq.tsv

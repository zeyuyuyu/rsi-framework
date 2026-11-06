#!/bin/bash
# Resume a Yangquan relayed-LLM run after the 53 h limit (rc=124): same plan, RESUME_RUN=<run> (Engine --resume),
# the v27 source tarball and this run's relay node_urls (both presigned under /home/zeyu/rsi/yq_logs).
# usage: [NGPU=3] resume_oftgb_llm.sh <run>     e.g. NGPU=3 resume_oftgb_llm.sh yq_oftgb_llm_harness_s2
set -u
run=$1; L=/home/zeyu/rsi/yq_logs
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip JOB_CPU=8 JOB_MEM=100
export RSI_SRC_URL="$(cat $L/src_v27.url)" RSI_LLM_RELAY="$(cat $L/$run.nodeurl)" RESUME_RUN="$run"
# NGPU=<n> (optional, default 1): resume with n cards; rollouts on all of them via run_vla6.sh (JOB_ENTRY_URL), training on GPU 0
ngpu=${NGPU:-1}; export JOB_GPU=$ngpu
[ "$ngpu" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
RUN_NAME="${run}_resume$(date -u +%m%d%H%M)" python3 scripts/baidu/submit_vla_yq2.py "$run" Haozhan72/Openvla-oft-SFT-libero-goal-traj1 | tail -1 | cut -c1-120
tail -n 1 scripts/baidu/jobs_yq.tsv

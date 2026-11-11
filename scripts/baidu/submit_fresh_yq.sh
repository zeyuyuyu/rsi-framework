#!/bin/bash
# Addendum 30: one Yangquan job that scores a version on the sealed fresh-scene test (1000 sampled placements).
# usage: submit_fresh_yq.sh <run>                 the run's retained version -> run dir <run>_fresh
#        submit_fresh_yq.sh n0 <goal|spatial> <k> the initial policy, replicate k -> run dir yq_fresh_n0_<suite>_<k>
set -u
L=/home/zeyu/rsi/yq_logs
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip JOB_CPU=8 JOB_MEM=100
export RSI_SRC_URL="$(cat $L/src_v30.url)"
if [ "$1" = n0 ]; then
  suite=$2; k=$3
  case "$suite" in goal) plan=yq_oftg_fixed_s1;; spatial) plan=yq_ofts_fixed_s1;; *) echo "suite?"; exit 1;; esac
  name=yq_fresh_n0_${suite}_$k; export ARGS="--fresh-eval none --node n0"
else
  plan=$1; name=${1}_fresh; export ARGS="--fresh-eval /mnt/pfs/shitianyu-rsi/runs/$1"
  case "$1" in yq_ofts*) suite=spatial;; yq_oftg_*|yq_oftgb_*) suite=goal;; *) echo "suite of $1?"; exit 1;; esac
fi
# a second call for the same evaluation is a no-op (FORCE=1 to resubmit after a failure)
if [ "${FORCE:-0}" != 1 ] && grep -q -P "^zw-rsi-$(echo "$name" | tr _ -)\t" scripts/baidu/jobs_yq.tsv; then
  echo "already submitted: $name"; exit 0
fi
RUN_NAME="$name" python3 scripts/baidu/submit_vla_yq2.py "$plan" "Haozhan72/Openvla-oft-SFT-libero-$suite-traj1" | tail -1 | cut -c1-120
tail -n 1 scripts/baidu/jobs_yq.tsv

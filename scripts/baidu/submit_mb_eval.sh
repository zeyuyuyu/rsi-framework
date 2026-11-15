#!/bin/bash
# Addendum 38 evaluations, one card each, source v34, on the resumed run dirs.
# usage: submit_mb_eval.sh <seed 1|3> <node e.g. r15c0> <kind: cc|fin_fresh|fresh23|fin_rep>
#   cc        one fresh evaluation of a version kept during the night   -> yq_oftgbx_mb_s<n>_cc_<node>
#   fin_fresh one fresh evaluation of the final version (registered)    -> yq_oftgbx_mb_s<n>_fin_fresh
#   fresh23   two more fresh evaluations of the final version           -> yq_oftgbx_mb_s<n>_fresh23
#   fin_rep   official test, three evaluations of the final version     -> yq_oftgbx_mb_s<n>_fin_rep
set -eu
cd "$(dirname "$0")/../.."
L=/home/zeyu/rsi/yq_logs
seed=$1; node=$2; kind=$3
case $seed in 1) run=yq_oftgbx_ext_s1b;; 3) run=yq_oftgbx_ext_s3;; *) echo "seed 1 or 3"; exit 1;; esac
R=/mnt/pfs/shitianyu-rsi/runs/$run
case $kind in
  cc)        name=yq_oftgbx_mb_s${seed}_cc_${node}; args="--fresh-eval $R --node $node --interim";;
  fin_fresh) name=yq_oftgbx_mb_s${seed}_fin_fresh;  args="--fresh-eval $R --node $node --interim";;
  fresh23)   name=yq_oftgbx_mb_s${seed}_fresh23;    args="--fresh-eval $R --node $node --interim --replicates 2";;
  fin_rep)   name=yq_oftgbx_mb_s${seed}_fin_rep;    args="--test-eval $R --node $node --replicates 3 --interim";;
  *) echo "kind?"; exit 1;;
esac
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip
export JOB_GPU=1 JOB_CPU=8 JOB_MEM=100 RSI_SRC_URL="$(cat $L/src_v34.url)" RUN_NAME=$name ARGS="$args"
echo "$(date -u +%FT%TZ) submit $name ($args)"
timeout 120 python3 scripts/baidu/submit_vla_yq2.py yq_oftgbx_ext_s$seed Haozhan72/Openvla-oft-SFT-libero-goal-traj1 2>&1 | tail -1 | cut -c1-160

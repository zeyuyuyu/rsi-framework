#!/bin/bash
# usage: launch2.sh <plan.json> <out_dir>  -- runs rsi.run_code_wm detached
PLAN=$1; OUT=$2; NAME=$(basename $OUT)
cd ~/rsi/src2
PYTHONPATH=~/rsi/src2:~/rsi/pylib nohup setsid ~/miniconda3/envs/vllm/bin/python -m rsi.run_code_wm --plan $PLAN --out $OUT < /dev/null > ~/rsi/logs/$NAME.log 2>&1 &
echo "launched $NAME pid $!"

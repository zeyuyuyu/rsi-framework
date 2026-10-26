#!/bin/bash
# Compact status of RSI runs on this box.
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr "\n" ";"; echo
for d in ~/rsi/runs/*/; do
  n=$(basename $d)
  [[ $n == *.work ]] && continue
  st=""
  [ -f $d/report.json ] && st="DONE"
  [ -f $d/failure.json ] && st="FAILED $(cat $d/failure.json | tr -d '\n' | cut -c1-200)"
  [ -f $d/baseline.json ] && st="BASELINE"
  r=$(ls $d 2>/dev/null | grep -c result.json)
  echo "$n rounds_done=$r $st"
done
for d in ~/rsi/runs/*.work/; do
  last=$(ls -t $d 2>/dev/null | head -1)
  [ -n "$last" ] && echo "  $(basename $d): $last"
done

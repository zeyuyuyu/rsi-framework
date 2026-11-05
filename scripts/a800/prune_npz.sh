#!/bin/bash
# Third npz prune (addendum 18 practice): delete ONLY *.npz episode frames under <run>.work of runs that have report.json.
# usage: prune_npz.sh <run> [<run> ...]   (run on cavin)
cd ~/rsi/runs2 || exit 1
echo "before: $(df -h /data0 | tail -1)"
for r in "$@"; do
  if [ ! -f "$r/report.json" ]; then echo "SKIP $r: no report.json"; continue; fi
  if [ ! -d "$r.work" ]; then echo "SKIP $r: no .work"; continue; fi
  n=$(find "$r.work" -type f -name "*.npz" | wc -l)
  s=$(find "$r.work" -type f -name "*.npz" -printf "%s\n" | awk '{t+=$1} END {printf "%.0f", t/1e9}')
  find "$r.work" -type f -name "*.npz" -delete
  left=$(find "$r.work" -type f -name "*.npz" | wc -l)
  echo "PRUNED $r: $n npz, ${s}G, left=$left; ckpts kept: $(find "$r.work" -maxdepth 1 -type d -name "*ckpt*" | wc -l), work now $(du -sh "$r.work" | cut -f1)"
done
echo "after: $(df -h /data0 | tail -1)"

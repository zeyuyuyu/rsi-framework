#!/bin/bash
# List the kept checkpoints of runs on PFS/CFS: one CKPT line per ckpt-* dir (size, file count, newest mtime) and
# whether report.json exists, so a later test-eval of a rejected node can rely on its weights still being there.
# Read-only. env: RUNS="run ..." under RUNROOT (default /mnt/pfs/shitianyu-rsi/runs)
ROOT=${RUNROOT:-/mnt/pfs/shitianyu-rsi/runs}
for r in $RUNS; do
  d=$ROOT/$r
  echo "== $r report.json=$([ -f $d/report.json ] && echo yes || echo no) rounds=$(ls $d/round-*.json 2>/dev/null | wc -l)"
  for c in $d/ckpt-*; do
    [ -d "$c" ] || continue
    echo "CKPT $r $(basename $c) $(du -sm $c 2>/dev/null | cut -f1)MB files=$(find $c -type f | wc -l) newest=$(find $c -type f -printf '%TY-%Tm-%TdT%TH:%TM\n' | sort | tail -1)"
  done
done
echo PFS_CKPTS_DONE

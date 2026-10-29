#!/bin/bash
# List what is on PFS for the robotics runs (read-only).
P=/mnt/pfs/shitianyu-rsi
ls -la $P/models/ $P/envs/ 2>&1 | head -30
for d in $P/models/*/; do echo "== $d $(du -sh $d 2>/dev/null | cut -f1)"; ls -la $d | head -30; done
for l in $P/models/.*.lock; do [ -d "$l" ] && echo "lock $l: $(cat $l/owner 2>/dev/null)"; done
ls -la $P/runs/ 2>/dev/null | grep -i oft

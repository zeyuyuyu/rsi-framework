#!/bin/bash
# Probe: copy the deployed CFS entry script to BOS (small file) and print it, so the repo copy can be reconciled.
echo "===== PROBE_COPY_ENTRY $(date -u +%FT%TZ)"; ls -la /mnt/cfs/shitianyu-rsi/jobs/ | head -40
cp -f /mnt/cfs/shitianyu-rsi/jobs/run_vla4.sh /mnt/bos/shitianyu-rsi/jobs/run_vla4_cfs_copy.sh && echo "COPIED_TO_BOS"
sha256sum /mnt/cfs/shitianyu-rsi/jobs/run_vla4.sh; echo "----- BEGIN run_vla4.sh"; cat /mnt/cfs/shitianyu-rsi/jobs/run_vla4.sh; echo "----- END"; echo PROBE_COPY_DONE

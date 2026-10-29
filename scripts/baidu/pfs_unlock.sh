#!/bin/bash
# Remove the VLA venv build lock left by a stopped job, only if its owner is the job named in UNLOCK_OWNER.
L=/mnt/pfs/shitianyu-rsi/envs/vla312-r3.lock
echo "lock: $(cat $L/owner 2>/dev/null || echo none)  expected owner prefix: ${UNLOCK_OWNER:-unset}"
ls -la /mnt/pfs/shitianyu-rsi/envs/
if [ -n "${UNLOCK_OWNER:-}" ] && grep -q "^$UNLOCK_OWNER" $L/owner 2>/dev/null; then
  mv $L $L.stale.$(date +%s) && echo "UNLOCKED"
else
  echo "NOT_UNLOCKED"
fi

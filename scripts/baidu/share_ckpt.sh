#!/bin/bash
# CPU job: copy LoRA checkpoint dirs of Yangquan runs from the pool CFS to the BOS share folder (small files only:
# adapter weights + config + receipt), so they can be presigned and sent to collaborators.
# env: ITEMS="run:node run:node ..."   dest: /mnt/bos/shitianyu-rsi/share/<run>_<node>/
set -u
for it in $ITEMS; do
  run=${it%%:*}; node=${it##*:}
  src=/mnt/cfs/shitianyu-rsi/runs/$run/ckpt-$node; dst=/mnt/bos/shitianyu-rsi/share/${run}_${node}
  [ -d "$src" ] || { echo "SHARE_FAILED $it: no $src"; continue; }
  mkdir -p "$dst"
  for f in adapter_model.safetensors adapter_config.json receipt.json; do [ -f "$src/$f" ] && cp -f "$src/$f" "$dst/$f"; done
  ls -la "$src" | head -20
  echo "SHARED $it $(du -sh "$dst" | cut -f1) $(sha256sum "$dst/adapter_model.safetensors" | cut -c1-16)"
done
echo SHARE_DONE

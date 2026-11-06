#!/bin/bash
# CPU job: upload adapter weights from the pool CFS to BOS through presigned PUT URLs (the BOS FUSE mount drops
# large files). env: ITEMS="run:node:PUT_URL ..."
set -u
for it in $ITEMS; do
  run=${it%%:*}; rest=${it#*:}; node=${rest%%:*}; url=${rest#*:}
  f=/mnt/cfs/shitianyu-rsi/runs/$run/ckpt-$node/adapter_model.safetensors
  [ -f "$f" ] || { echo "PUT_FAILED $run:$node no file"; continue; }
  code=$(curl -sS -o /tmp/put.out -w "%{http_code}" -X PUT -H "Content-Type: application/octet-stream" --retry 3 -T "$f" "$url")
  echo "PUT $run:$node http=$code size=$(stat -c %s "$f") sha256=$(sha256sum "$f" | cut -c1-16)"; head -c 200 /tmp/put.out; echo
done
echo PUT_DONE

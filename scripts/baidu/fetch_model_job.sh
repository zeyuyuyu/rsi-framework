#!/bin/bash
# CPU job: fetch MODEL_ID to PFS with fetch_model (setup_vla.sh), so GPU jobs never hold a card while downloading.
set -u
cp -f /mnt/bos/shitianyu-rsi/jobs/setup_vla.sh /tmp/setup_vla.sh
VLA_SETUP_SOURCED=1 . /tmp/setup_vla.sh
D=/mnt/pfs/shitianyu-rsi/models/${MODEL_ID##*/}
fetch_model "$MODEL_ID" "$D" && echo "FETCH_DONE $MODEL_ID $(cat "$D/.sha256")" || echo "FETCH_FAILED $MODEL_ID"

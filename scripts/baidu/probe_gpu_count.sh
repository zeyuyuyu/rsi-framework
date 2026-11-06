#!/bin/bash
# Probe: does a JOB_GPU=N job see N cards? Prints the GPU list and exits.
echo "===== PROBE_GPU_COUNT $(date -u +%FT%TZ) name=${NAME:-}"
nvidia-smi -L; nvidia-smi --query-gpu=index,memory.total,memory.used --format=csv,noheader
echo "visible=$(nvidia-smi -L | grep -c '^GPU') nproc=$(nproc)"; echo PROBE_GPU_DONE

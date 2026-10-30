#!/bin/bash
# Baidu queue quota probe: does a 1-GPU / 8-CPU job start while three 24-CPU GPU jobs run?
echo "QUOTA_PROBE_START $(date -u +%FT%TZ) nproc=$(nproc)"
nvidia-smi -L 2>&1 | head -2
sleep 120
echo "QUOTA_PROBE_DONE $(date -u +%FT%TZ)"

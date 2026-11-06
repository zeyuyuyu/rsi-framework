#!/bin/bash
# Event stream for a Monitor: relay answers / request-fetch errors for Yangquan LLM runs since start.
S=$(date -u -d '-2 min' +%Y-%m-%dT%H:%M)
while true; do timeout 40 ssh -o ConnectTimeout=20 cavin 'tail -n 400 ~/rsi/relay/relay.log' 2>/dev/null | grep -E " answered | req_get_error | req_get_exc " | grep -v " bj_" | awk -v s="$S" '$1 >= s'; sleep 120; done | awk '!seen[$0]++ {print; fflush()}'

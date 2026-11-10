#!/bin/bash
# Addendum 29: submit one Yangquan run of the Spatial self-repair study. meta3 runs get relay slots first (the relay's
# file goes to cavin ~/rsi/relay/runs, the node's URL list to BOS; no key leaves cavin).
# usage: [NGPU=n] submit_spatial_repair_yq.sh <run>      e.g. NGPU=3 submit_spatial_repair_yq.sh yq_oftsb_meta3_s1
set -u
run=$1; L=/home/zeyu/rsi/yq_logs
cd "$(dirname "$0")/../.." || exit 1
export AIHC_HOST=aihc.yq.baidubce.com AIHC_POOL=aihc-serverless AIHC_QUEUE=aihcq-4yv1euenciip JOB_CPU=8 JOB_MEM=100
export RSI_SRC_URL="$(cat $L/src_v29.url)"
ngpu=${NGPU:-1}; export JOB_GPU=$ngpu
[ "$ngpu" -le 1 ] || export JOB_ENTRY_URL="$(cat $L/run_vla6.sh.url)"
case "$run" in
  *_meta3_*)
    if [ ! -s "$L/$run.nodeurl" ]; then
      mkdir -p "$L/relay"
      python3 scripts/baidu/mk_relay_urls.py "$run" "$L/relay" 80 6 > "$L/$run.nodeurl" || { echo "relay urls failed"; exit 1; }
      chmod 600 "$L/$run.nodeurl"
      # copy under another suffix, then rename: the relay must never read a half-written run file
      timeout 60 scp -q -o ConnectTimeout=20 "$L/relay/$run.json" "cavin:rsi/relay/runs/$run.json.part" || { echo "relay file copy failed"; rm -f "$L/$run.nodeurl"; exit 1; }
      timeout 30 ssh -o ConnectTimeout=20 cavin "chmod 600 ~/rsi/relay/runs/$run.json.part && mv ~/rsi/relay/runs/$run.json.part ~/rsi/relay/runs/$run.json" || { echo "relay file rename failed"; rm -f "$L/$run.nodeurl"; exit 1; }
    fi
    export RSI_LLM_RELAY="$(cat $L/$run.nodeurl)";;
esac
python3 scripts/baidu/submit_vla_yq2.py "$run" Haozhan72/Openvla-oft-SFT-libero-spatial-traj1 | tail -1 | cut -c1-120
tail -n 1 scripts/baidu/jobs_yq.tsv

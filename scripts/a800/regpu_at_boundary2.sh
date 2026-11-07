#!/bin/bash
# Stop a queue-launched cavin run at its next round boundary and re-queue it with more GPUs (--resume, same plan).
# v2 (11-07): re-queue only if enough GPUs would actually be free (queue_runner: memory < 2000 MiB); otherwise leave
# the run alone instead of parking it in pending behind other users' processes.
# usage: regpu_at_boundary2.sh <run> <engine_pid> <ngpus> <queue_seq>
set -u
run=$1; pid=$2; n=$3; seq=$4
cd ~/rsi || exit 1
log=queue/logs/$run.regpu.log
tr "\0" " " < /proc/$pid/cmdline | grep -q "plans/$run.json" || { echo "ABORT $run: pid $pid is not this run" | tee -a $log; exit 2; }
[ "$(ps -o pgid= -p $pid | tr -d " ")" = "$pid" ] || { echo "ABORT $run: pid $pid is not a group leader" | tee -a $log; exit 2; }
src=$(ls queue/running/*_$run.json | tail -1); cp "$src" /tmp/regpu_$run.json
cur_n=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["ngpus"])' /tmp/regpu_$run.json)
base=$(ls runs2/$run | grep -cE "^round-[0-9]{2}\.json$")
echo "$(date -u +%FT%TZ) watching(v2) $run pid=$pid rounds_done=$base ngpus=$cur_n -> $n if free" >> $log
while :; do
  [ -e runs2/$run/report.json ] && { echo "$(date -u +%FT%TZ) $run completed before a boundary; nothing done" >> $log; exit 0; }
  ps -p $pid > /dev/null || { echo "$(date -u +%FT%TZ) $run pid $pid gone; nothing done" >> $log; exit 0; }
  cur=$(ls runs2/$run | grep -cE "^round-[0-9]{2}\.json$")
  [ "$cur" -gt "$base" ] && break
  sleep 15
done
# GPUs this run holds (compute apps in its process group) + GPUs nobody uses = what the runner could give it
own=$(nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader | tr -d ' ' | while IFS=, read u p; do
        [ "$(ps -o pgid= -p "$p" 2>/dev/null | tr -d ' ')" = "$pid" ] && echo "$u"; done | sort -u)
idle=$(nvidia-smi --query-gpu=uuid,memory.used --format=csv,noheader,nounits | tr -d ' ' | awk -F, '$2<2000{print $1}')
avail=$(printf "%s\n%s\n" "$own" "$idle" | grep -c "^GPU-")
[ "$avail" -lt "$n" ] && n=$avail
if [ "$n" -le "$cur_n" ]; then
  echo "$(date -u +%FT%TZ) round-$(printf %02d $cur).json seen but only $avail GPUs would be free (own $(echo "$own" | grep -c '^GPU-') + idle $(echo "$idle" | grep -c '^GPU-')) <= current $cur_n; leaving the run alone" >> $log
  exit 0
fi
sleep 60   # let the engine finish the post-round writes
echo "$(date -u +%FT%TZ) round-$(printf %02d $cur).json seen; $avail GPUs free; stopping process group $pid" >> $log
kill -TERM -- -$pid; for i in $(seq 1 60); do ps -p $pid > /dev/null || break; sleep 1; done
ps -p $pid > /dev/null && { kill -KILL -- -$pid; sleep 3; }
for i in $(seq 1 90); do grep -q "finished $run " queue/runner.log && break; sleep 2; done
python3 - /tmp/regpu_$run.json "$run" "$n" "$seq" <<PY
import json,sys
src,run,n,seq=sys.argv[1:]
d=json.load(open(src)); d["ngpus"]=int(n); d["args"]=["--resume"]
json.dump(d,open(f"queue/pending/{seq}_{run}.json","w"),indent=1); print("queued",seq,run,"ngpus",n)
PY
echo "$(date -u +%FT%TZ) queued ${seq}_$run.json ngpus=$n --resume" >> $log

#!/bin/bash
# One RSI code-world-model arm on one AIHC GPU (vllm-openai:v0.11.0 image).
# env: PLAN  plan json, BOS-relative ("shitianyu-rsi/plans/x.json", optionally prefixed "bos-research-team/")
#            or an absolute container path
#      NAME  run name -> /mnt/pfs/shitianyu-rsi/runs/$NAME (+ small files copied to /mnt/bos/shitianyu-rsi/runs/$NAME)
#      PREFLIGHT (default 1): 2-step LoRA train x2 + vLLM serve of the merged result before the main run
#      RUN_TIMEOUT_S (default 86400)
#      RESUME_RUN    (optional) run dir under $PFS/runs to continue instead of starting fresh
# Stage the script to local disk first, so re-uploading it to BOS never affects a running job.
if [ -z "${RSI_STAGED:-}" ]; then
  cp -f "$0" /tmp/run_rsi.sh && RSI_STAGED=1 exec bash /tmp/run_rsi.sh "$@"
  echo "staging failed"; exit 90
fi
set -u
T0=$(date +%s)
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PIP_BREAK_SYSTEM_PACKAGES=1 PIP_NO_INPUT=1 \
       TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 HF_HUB_DISABLE_PROGRESS_BARS=1
PY=/usr/bin/python3; [ -x "$PY" ] || PY=$(command -v python3)
PFS=/mnt/pfs/shitianyu-rsi
BOS=/mnt/bos/shitianyu-rsi
# MODEL_ID (modelscope / HF id) and A800_SHA (weights digest on the A800, see weights_sha) may come from the job env
MODEL_ID=${MODEL_ID:-Qwen/Qwen2.5-Coder-1.5B-Instruct}
MNAME=${MODEL_ID##*/}
MDIR=$PFS/models/$MNAME
DONE=$MDIR/.download_done
LOCK=$PFS/models/.$MNAME.lock
if [ "$MODEL_ID" = Qwen/Qwen2.5-Coder-1.5B-Instruct ]; then
  A800_SHA=${A800_SHA:-c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8}   # model.safetensors on the A800 (HF 2e1fd39)
else
  A800_SHA=${A800_SHA:-unknown}
fi
# one file: its sha256; sharded: sha256 of the sorted "name sha256" lines of every shard
weights_sha() {
  ( cd "$1" && if [ -f model.safetensors ]; then sha256sum model.safetensors | cut -d' ' -f1
    else for f in $(ls *.safetensors | sort); do echo "$f $(sha256sum "$f" | cut -d' ' -f1)"; done | sha256sum | cut -d' ' -f1; fi )
}
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple
NAME=${NAME:?NAME required}
PLAN=${PLAN:?PLAN required}
case "$PLAN" in /*) PLANF=$PLAN ;; bos-research-team/*) PLANF=/mnt/bos/${PLAN#bos-research-team/} ;; *) PLANF=/mnt/bos/$PLAN ;; esac

el() { echo $(( $(date +%s) - T0 )); }
log() { echo "[$(date -u +%FT%TZ) t+$(el)s] $*"; }
stage() { echo; echo "===== [$(date -u +%FT%TZ)] STAGE $1 (t+$(el)s) ====="; }
die() { log "FATAL: $*"; echo "RSI_JOB_FAILED name=$NAME stage=$CUR reason=$*"; exit "${2:-1}"; }
CUR=init

stage "0 env"; CUR=env
log "name=$NAME plan=$PLANF host=$(hostname) python=$($PY --version 2>&1) nproc=$(nproc)"
cat /sys/fs/cgroup/cpu.max 2>/dev/null | sed 's/^/  cgroup cpu.max: /'
timeout 60 nvidia-smi --query-gpu=index,name,memory.used,memory.total,driver_version --format=csv,noheader
[ -r "$PLANF" ] || die "plan not readable: $PLANF"
cp -f "$PLANF" /tmp/plan.json || die "plan copy failed"
echo "--- PLAN $PLANF"; cat /tmp/plan.json

stage "1 python deps"; CUR=deps
# pinned to the A800 env (pandas 3.x changed the default string dtype)
if [ "$($PY -c 'import pandas, pyarrow; print(pandas.__version__, pyarrow.__version__)' 2>/dev/null)" != "2.3.3 23.0.1" ]; then
  timeout 600 $PY -m pip install -q --timeout 30 --retries 2 pandas==2.3.3 pyarrow==23.0.1 \
    || timeout 600 $PY -m pip install -q --timeout 30 --retries 2 -i "$TUNA" pandas==2.3.3 pyarrow==23.0.1 || die "pandas/pyarrow install failed"
fi
if [ "$($PY -c 'import peft; print(peft.__version__)' 2>/dev/null)" != "0.13.2" ]; then
  timeout 600 $PY -m pip install -q --timeout 30 --retries 2 peft==0.13.2 \
    || timeout 600 $PY -m pip install -q --timeout 30 --retries 2 -i "$TUNA" peft==0.13.2 || die "peft install failed"
fi
$PY -c 'import torch, transformers, vllm, peft, pandas, pyarrow; print("versions torch", torch.__version__, "transformers", transformers.__version__, "vllm", vllm.__version__, "peft", peft.__version__, "pandas", pandas.__version__, "pyarrow", pyarrow.__version__)' 2>&1 | grep -v Warning | tail -1

# Per-problem test scores of a run (pairing across arms needs them; the BOS copy is not readable from outside)
# and the independent re-scorer's agreement with the engine's scores.
emit_tests() {
  $PY - "$1" <<'EOF'
import glob, hashlib, json, os, sys
for p in sorted(glob.glob(os.path.join(sys.argv[1], "test-*-*.jsonl"))):
    recs = [json.loads(l) for l in open(p) if l.strip()]
    ids = hashlib.sha256(json.dumps([r["id"] for r in recs]).encode()).hexdigest()[:16]
    print("TESTBITS", os.path.basename(p), len(recs), ids, "".join("1" if r["score"] >= 0.5 else "0" for r in recs))
EOF
  if ls "$1"/test-*-*.jsonl >/dev/null 2>&1; then
    local crux lcb
    crux=$($PY -c 'import json; print(json.load(open("/tmp/plan.json"))["data"]["cruxeval"])')
    lcb=$($PY -c 'import json; print(json.load(open("/tmp/plan.json"))["data"]["lcb"])')
    ( cd /tmp/src && PYTHONPATH=/tmp/src timeout 3600 $PY -m rsi.audit.rescore_code_wm "$1" "$crux" "$lcb" 2>&1 | tail -40 | sed 's/^/RESCORE /' )
  fi
}

# EXPORT_RUNS="bj_a bj_b": print tests.txt of finished runs on PFS and exit (no model, no GPU work)
if [ -n "${EXPORT_RUNS:-}" ]; then
  stage "3 source (export)"; CUR=src
  rm -rf /tmp/src && mkdir -p /tmp/src && tar -xzf "$BOS/src/rsi_src.tar.gz" -C /tmp/src || die "src extract failed"
  for r in $EXPORT_RUNS; do
    [ -d "$PFS/runs/$r" ] || { log "no run dir $r"; continue; }
    echo "===== RSI_RESULT_BEGIN name=$r run=$r rc=0 export t+$(el)s ====="
    echo "----- FILE tests.txt -----"; emit_tests "$PFS/runs/$r"
    echo "===== RSI_RESULT_END name=$r rc=0 ====="
  done
  echo "RSI_JOB_DONE name=$NAME rc=0"; exit 0
fi

stage "2 model"; CUR=model
model_ok() { [ -f "$DONE" ] && [ -f "$MDIR/config.json" ] && ls "$MDIR"/*.safetensors >/dev/null 2>&1; }
mkdir -p "$PFS/models"
# DOWNLOAD_ONLY=1 (CPU-only job): fetch the model to PFS and exit, so GPU jobs never sit on a card while
# downloading. It owns the download: a lock left by a stopped GPU job is taken over at once.
if [ "${DOWNLOAD_ONLY:-0}" = 1 ] && [ -d "$LOCK" ] && ! model_ok; then
  log "download-only: taking over lock ($(cat "$LOCK/owner" 2>/dev/null))"; mv "$LOCK" "$LOCK.stale.$$"
fi
WAITED=0
while ! model_ok; do
  if mkdir "$LOCK" 2>/dev/null; then
    echo "$NAME $(hostname) $(date -u +%FT%TZ)" > "$LOCK/owner"
    log "lock acquired; downloading $MODEL_ID -> $MDIR (modelscope)"
    mkdir -p "$MDIR"
    ok=no
    for attempt in 1 2 3; do
      if timeout "${MS_TIMEOUT:-5400}" modelscope download --model "$MODEL_ID" --local_dir "$MDIR" > /tmp/ms_dl.txt 2>&1 \
         && [ -f "$MDIR/config.json" ] && ls "$MDIR"/*.safetensors >/dev/null 2>&1; then ok=yes; break; fi
      log "download attempt $attempt failed:"; tail -5 /tmp/ms_dl.txt
      # fallback: HF mirror
      if HF_ENDPOINT=https://hf-mirror.com timeout 5400 $PY -c "import sys; from huggingface_hub import snapshot_download; snapshot_download(sys.argv[1], local_dir=sys.argv[2], allow_patterns=['*.json', '*.safetensors', '*.txt', '*.model', '*.py', '*.jinja'])" "$MODEL_ID" "$MDIR" > /tmp/hf_dl.txt 2>&1 \
         && [ -f "$MDIR/config.json" ] && ls "$MDIR"/*.safetensors >/dev/null 2>&1; then ok=yes; break; fi
      log "hf-mirror attempt $attempt failed:"; tail -5 /tmp/hf_dl.txt
    done
    if [ "$ok" = yes ]; then
      weights_sha "$MDIR" > "$MDIR/.sha256"
      date -u +%FT%TZ > "$DONE"
      log "download done: $(du -sh "$MDIR" | cut -f1)"
      rm -rf "$LOCK"
    else
      rm -rf "$LOCK"; die "model download failed"
    fi
  else
    if [ $WAITED -ge 9000 ]; then die "waited ${WAITED}s for another job's model download"; fi
    # a lock older than 3 h with no done-marker is stale (its job died): take it over
    if [ -d "$LOCK" ] && [ -n "$(find "$LOCK" -maxdepth 0 -mmin +180 2>/dev/null)" ]; then
      log "stale lock ($(cat "$LOCK/owner" 2>/dev/null)); taking over"; mv "$LOCK" "$LOCK.stale.$$" 2>/dev/null; continue
    fi
    [ $((WAITED % 300)) -eq 0 ] && log "waiting for model download by $(cat "$LOCK/owner" 2>/dev/null) (${WAITED}s)"
    sleep 30; WAITED=$((WAITED + 30))
  fi
done
ls -la "$MDIR"
MSHA=$(cat "$MDIR/.sha256" 2>/dev/null)
if [ "$MSHA" = "$A800_SHA" ]; then echo "MODEL_SHA_MATCH_A800 $MSHA"; else echo "MODEL_SHA_MISMATCH_A800 baidu=$MSHA a800=$A800_SHA"; fi
if [ "${DOWNLOAD_ONLY:-0}" = 1 ]; then echo "RSI_JOB_DONE name=$NAME rc=0 download-only"; exit 0; fi

stage "3 source"; CUR=src
SRC_TGZ=$BOS/src/rsi_src.tar.gz
[ -r "$SRC_TGZ" ] || die "src tarball unreadable"
rm -rf /tmp/src && mkdir -p /tmp/src && tar -xzf "$SRC_TGZ" -C /tmp/src || die "src extract failed"
log "src sha256=$(sha256sum "$SRC_TGZ" | cut -c1-16)"
(cd /tmp/src && find rsi -name '*.py' | sort | xargs md5sum | md5sum | sed 's/^/  py-tree md5: /')

if [ "${PREFLIGHT:-1}" = 1 ]; then
  stage "4 preflight (train grpo -> train sft from parent -> vLLM serve merged)"; CUR=preflight
  PF=/tmp/preflight; rm -rf $PF; mkdir -p $PF
  $PY - "$MDIR" "$PF" <<'EOF'
import json, sys
m, pf = sys.argv[1], sys.argv[2]
items = [dict(experience=dict(prompt=f"def f(x):\n    return x + {i}\nassert f(1) == ", completion=str(1 + i)),
              advantage=(1.0 if i % 2 == 0 else -1.0)) for i in range(8)]
with open(f"{pf}/items_grpo.jsonl", "w") as s:
    for it in items: s.write(json.dumps(it) + "\n")
with open(f"{pf}/items_sft.jsonl", "w") as s:
    for it in items: s.write(json.dumps(it["experience"]) + "\n")
common = dict(base_path=m, seed=0, lora_rank=64, lora_alpha=128,
              target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
              micro_batch=4, max_seq_len=2048, multi_gpu_device_map=False)
json.dump(dict(common, parent=dict(id="base:preflight", location=m, parent_id=None), output=f"{pf}/c1",
               items=f"{pf}/items_grpo.jsonl", update=dict(operator="grpo", lr=2e-5, steps=2, batch=8)),
          open(f"{pf}/spec1.json", "w"))
with open(f"{pf}/req.jsonl", "w") as s:
    for i in range(2):
        s.write(json.dumps(dict(index=i, prompt=f"def f(x):\n    return x * {i + 2}\nassert f(3) == ", n=2,
                                temperature=0.8, top_p=0.95, max_tokens=16, stop=["\n"], seed=i)) + "\n")
EOF
  ( cd $PF && CUDA_VISIBLE_DEVICES=0 PYTHONPATH=/tmp/src HF_HUB_OFFLINE=1 timeout 900 $PY -m rsi.backends.llm.train_worker $PF/spec1.json > $PF/t1.log 2>&1 )
  rc=$?; tail -4 $PF/t1.log; [ $rc -eq 0 ] && [ -f $PF/c1/receipt.json ] || { tail -60 $PF/t1.log; die "preflight grpo train rc=$rc"; }
  $PY - "$MDIR" "$PF" <<'EOF'
import json, sys
m, pf = sys.argv[1], sys.argv[2]
r = json.load(open(f"{pf}/c1/receipt.json"))
s = json.load(open(f"{pf}/spec1.json"))
s.update(parent=r["version"], output=f"{pf}/c2", items=f"{pf}/items_sft.jsonl",
         update=dict(operator="sft", lr=1e-4, steps=2, batch=8))
json.dump(s, open(f"{pf}/spec2.json", "w"))
print("preflight c1 receipt:", json.dumps({k: r[k] for k in ("operator", "optimizer_steps", "items", "trainable_parameters", "loss_first", "loss_last")}))
EOF
  ( cd $PF && CUDA_VISIBLE_DEVICES=0 PYTHONPATH=/tmp/src HF_HUB_OFFLINE=1 timeout 900 $PY -m rsi.backends.llm.train_worker $PF/spec2.json > $PF/t2.log 2>&1 )
  rc=$?; tail -3 $PF/t2.log; [ $rc -eq 0 ] && [ -f $PF/c2/merged/config.json ] || { tail -60 $PF/t2.log; die "preflight sft-from-parent train rc=$rc"; }
  ( cd $PF && CUDA_VISIBLE_DEVICES=0 PYTHONPATH=/tmp/src HF_HUB_OFFLINE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn timeout 900 \
      $PY -m rsi.backends.llm.sample_worker --model $PF/c2/merged --requests $PF/req.jsonl --out $PF/out.jsonl \
      --max-model-len 4096 --gpu-memory-utilization 0.85 --tensor-parallel 1 > $PF/s.log 2>&1 )
  rc=$?; [ $rc -eq 0 ] && [ -s $PF/out.jsonl ] || { grep -v '^\s*$' $PF/s.log | tail -60; die "preflight vLLM serve of merged model rc=$rc"; }
  grep -E 'Error|error' $PF/s.log | grep -viE 'error_|errors=|stderr' | head -5
  echo "preflight sample out:"; cat $PF/out.jsonl
  echo "PREFLIGHT_OK t+$(el)s"
  timeout 60 nvidia-smi --query-gpu=memory.used --format=csv,noheader | sed 's/^/  gpu mem after preflight: /'
fi

stage "5 main run"; CUR=main
RUN=$PFS/runs/$NAME
[ -e "$RUN" ] && RUN=$PFS/runs/$NAME-$(date -u +%Y%m%dT%H%M%SZ)
RESUME_FLAG=""
if [ -n "${RESUME_RUN:-}" ]; then   # continue a run the job wall time cut off (Engine resume)
  RUN=$PFS/runs/$RESUME_RUN
  [ -f "$RUN/plan.json" ] && [ ! -f "$RUN/report.json" ] || die "resume target $RUN missing or already complete"
  RESUME_FLAG="--resume"
  log "resuming $RUN (rounds done: $(ls $RUN | grep -cE '^round-[0-9]+\.json$'))"
fi
RNAME=$(basename "$RUN")
mkdir -p "$PFS/runs"
log "out=$RUN  workdir=$RUN.work"
# Gate/audit/test id lists of every Baidu run vs the A800 main_q15 runs (same heldout seed -> must match).
plan_digests() {
  $PY - "$PFS/runs" /tmp/digested.txt <<'EOF'
import glob, hashlib, json, os, sys
A800 = "gate 442 f3255402df7c3fdc audit 509 edf921d96d421260 tests 257b73b6493a239c seedprog deb463acc37c2f27"
seen = set(open(sys.argv[2]).read().split()) if os.path.exists(sys.argv[2]) else set()
h = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]
for path in sorted(glob.glob(os.path.join(sys.argv[1], "bj_*", "plan.json"))):
    run = path.split("/")[-2]
    if run in seen:
        continue
    try:
        p = json.load(open(path))
    except Exception:
        continue
    s = (f"gate {len(p['gate_ids'])} {h(p['gate_ids'])} audit {len(p['audit_ids'])} {h(p['audit_ids'])} "
         f"tests {h(p['tests'])} seedprog {p['seed_program']['id']}")
    print(f"PLAN_DIGEST {run} {s} -> {'PARITY_A800_OK' if s == A800 else 'PARITY_A800_MISMATCH a800=' + A800}", flush=True)
    open(sys.argv[2], "a").write(run + "\n")
EOF
}
heartbeat() {
  local n=0 latest f
  while true; do
    if [ $n -lt 12 ]; then sleep 150; else sleep 600; fi
    n=$((n + 1))
    echo "===== HEARTBEAT [$(date -u +%FT%TZ)] t+$(el)s name=$NAME ====="
    echo "  run files: $(ls "$RUN" 2>/dev/null | grep -vE -- '-(cases|attempts)-|^test-' | tr '\n' ' ')"
    echo "  calls: $(ls "$RUN.work" 2>/dev/null | tr '\n' ' ' | tail -c 400)"
    latest=$(ls -td "$RUN.work"/*/ 2>/dev/null | head -1)
    for f in "$latest"log*.txt; do
      [ -f "$f" ] || continue
      echo "  tail $(basename "$latest")$(basename "$f"):"
      tail -c 3000 "$f" | tr '\r' '\n' | grep -v '^\s*$' | tail -n 3 | cut -c1-260 | sed 's/^/    /'
    done
    echo "  gpu: $(timeout 30 nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader 2>&1)  load: $(cut -d' ' -f1-3 /proc/loadavg)"
    plan_digests
  done
}
heartbeat &
HB=$!
( cd /tmp/src && PYTHONPATH=/tmp/src timeout -k 120 "${RUN_TIMEOUT_S:-86400}" $PY -m rsi.run_code_wm --plan /tmp/plan.json --out "$RUN" $RESUME_FLAG ) > /tmp/main.log 2>&1 &
MAIN=$!
tail -n +1 -f /tmp/main.log --pid=$MAIN &
TAILP=$!
wait $MAIN; RC=$?
sleep 2; kill $HB $TAILP 2>/dev/null
log "main run exit rc=$RC"
CUR=report

stage "6 results"
echo "===== RSI_RESULT_BEGIN name=$NAME run=$RNAME rc=$RC t+$(el)s ====="
: > /tmp/digested.txt; plan_digests | grep -F " $RNAME "
for f in report.json failure.json accepted.jsonl backend-accounting.json retained.json; do
  if [ -f "$RUN/$f" ]; then echo "----- FILE $f -----"; cat "$RUN/$f"; echo; fi
done
for f in $(ls "$RUN"/round-[0-9][0-9].json 2>/dev/null); do
  echo "----- FILE $(basename "$f") (compact) -----"
  $PY - "$f" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
print(json.dumps(dict(round=d["round"], parent=d["parent"], accepted=d["accepted"], seconds={k: round(v) for k, v in d.get("seconds", {}).items()})))
for c in d.get("candidates", []):
    cur, sig = c.get("curation") or {}, c.get("signal") or {}
    print(json.dumps(dict(node=c["node"], gate=c["gate"], author=c.get("author"), program=c.get("program"),
                          curation_items=cur.get("items"), curation_item_cases=cur.get("item_cases"),
                          curation_cases=cur.get("cases"), verified_rate=sig.get("verified_rate"),
                          mixed_fraction=sig.get("mixed_fraction"), signal_cases=sig.get("cases"),
                          rejected=sig.get("rejected"))))
EOF
done
if [ -f "$RUN/archive.jsonl" ]; then
  echo "----- FILE archive.jsonl (compact) -----"
  $PY - "$RUN/archive.jsonl" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    try: n = json.loads(line)
    except ValueError: continue
    if n.get("event"):
        print(json.dumps(n)); continue
    r = n.get("receipt") or {}
    det = r.get("details") or {}
    prog = n.get("program") or {}
    print(json.dumps({k: n.get(k) for k in ("node_id", "round", "parent_node", "gate", "audit")} | dict(
        program=prog.get("id"), author=prog.get("author"), note=(prog.get("note") or "")[:400],
        train_items=r.get("items"), loss_first=det.get("loss_first"), loss_last=det.get("loss_last"),
        train_seconds=round(det.get("seconds") or 0),
        verified_rate=(n.get("signal") or {}).get("verified_rate"),
        curation_items=(n.get("curation") or {}).get("items"))))
EOF
fi
echo "----- FILE tests.txt -----"; emit_tests "$RUN"
if [ $RC -ne 0 ]; then
  echo "----- latest worker logs (failure context) -----"
  for d in $(ls -td "$RUN.work"/*/ 2>/dev/null | head -2); do
    for f in "$d"log*.txt; do [ -f "$f" ] && { echo "--- $f"; tail -c 20000 "$f" | tr '\r' '\n' | grep -v '^\s*$' | tail -n 60 | cut -c1-400; }; done
  done
fi
echo "===== RSI_RESULT_END name=$NAME rc=$RC ====="

stage "7 copy small files to BOS"
DEST=$BOS/runs/$RNAME
mkdir -p "$DEST"
(cd "$RUN" 2>/dev/null && find . -type f ! -path './ckpt-*' -size -500M -print0 | xargs -0 -r cp --parents -f -t "$DEST") \
  && log "copied $(cd "$RUN" && find . -type f ! -path './ckpt-*' | wc -l) files to $DEST"
cp -f /tmp/main.log "$DEST/main_stdout.log" 2>/dev/null
cp -f /tmp/plan.json "$DEST/plan_input.json" 2>/dev/null
log "done rc=$RC"
echo "RSI_JOB_DONE name=$NAME rc=$RC"
exit $RC

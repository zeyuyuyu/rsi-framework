#!/bin/bash
# One robotics RSI run (rsi.run_libero) on one AIHC GPU (vllm-openai:v0.11.0 image, RTX Blackwell).
# env: PLAN      plan json in the A800 format, BOS-relative ("shitianyu-rsi/plans/x.json") or an absolute path;
#                vla.checkpoint / python / openvla_root / gpus are rewritten for this node
#      NAME      run name -> /mnt/pfs/shitianyu-rsi/runs/$NAME (+ small files copied to /mnt/bos/shitianyu-rsi/runs/$NAME)
#      MODEL_ID  hf repo of the starting checkpoint (fetched once to PFS through hf-mirror, fetch_model in setup_vla.sh)
#      A800_SHA  (optional) weights digest of the same checkpoint on the A800
#      ARGS      (optional) extra run_libero args, e.g. "--baseline-only" or "--test-eval /mnt/pfs/.../runs/x --replicates 2"
#      RESUME_RUN (optional) run dir under $PFS/runs to continue (Engine resume)
#      RUN_TIMEOUT_S (default 93600)
if [ -z "${RSI_STAGED:-}" ]; then
  cp -f "$0" /tmp/run_vla.sh && RSI_STAGED=1 exec bash /tmp/run_vla.sh "$@"
  echo "staging failed"; exit 90
fi
set -u
T0=$(date +%s)
export TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 HF_HUB_DISABLE_PROGRESS_BARS=1
PFS=/mnt/pfs/shitianyu-rsi
BOS=/mnt/bos/shitianyu-rsi
NAME=${NAME:?NAME required}
PLAN=${PLAN:?PLAN required}
MODEL_ID=${MODEL_ID:?MODEL_ID required}
MNAME=${MODEL_ID##*/}
MDIR=$PFS/models/$MNAME
case "$PLAN" in /*) PLANF=$PLAN ;; bos-research-team/*) PLANF=/mnt/bos/${PLAN#bos-research-team/} ;; *) PLANF=/mnt/bos/$PLAN ;; esac
el() { echo "t+$(( $(date +%s) - T0 ))s"; }
log() { echo "[$(date -u +%FT%TZ) $(el)] $*"; }
stage() { echo; echo "===== [$(date -u +%FT%TZ)] STAGE $1 ($(el)) ====="; }
die() { log "FATAL: $*"; echo "RSI_JOB_FAILED name=$NAME stage=$CUR reason=$*"; exit "${2:-1}"; }
CUR=init

stage "0 env"; CUR=env
log "name=$NAME plan=$PLANF model=$MODEL_ID host=$(hostname) nproc=$(nproc)"
[ -r "$PLANF" ] || die "plan not readable: $PLANF"
cp -f "$PLANF" /tmp/plan_in.json || die "plan copy failed"
cp -f "$BOS/jobs/setup_vla.sh" /tmp/setup_vla.sh || die "setup script unreadable"
VLA_SETUP_SOURCED=1 . /tmp/setup_vla.sh || die "vla setup failed"
PY=$(command -v python)
[ "$PY" = "$ENV/bin/python" ] || die "venv not active ($PY)"
# MuJoCo GL backend: EGL on the GPU when it renders here, else osmesa (CPU)
cat > /tmp/render.py <<'EOF'
import os, mujoco
m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><light pos='0 0 3'/><geom type='box' size='.1 .1 .1'/></worldbody></mujoco>")
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 64, 64); r.update_scene(d); r.render(); print("RENDER_OK", flush=True); os._exit(0)
EOF
GL=egl
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl timeout 120 python /tmp/render.py 2>/dev/null | grep -q RENDER_OK || GL=osmesa
if [ $GL = osmesa ]; then
  MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa timeout 120 python /tmp/render.py 2>/dev/null | grep -q RENDER_OK || die "no MuJoCo GL backend renders"
fi
export MUJOCO_GL=$GL PYOPENGL_PLATFORM=$GL
log "MuJoCo GL backend: $GL"

stage "1 model"; CUR=model
fetch_model "$MODEL_ID" "$MDIR" || die "checkpoint download failed"
MSHA=$(cat "$MDIR/.sha256" 2>/dev/null)
if [ "$MSHA" = "${A800_SHA:-unknown}" ]; then echo "MODEL_SHA_MATCH_A800 $MSHA"; else echo "MODEL_SHA_MISMATCH_A800 baidu=$MSHA a800=${A800_SHA:-unknown}"; fi

stage "2 source + plan"; CUR=src
SRC_TGZ=$BOS/src/rsi_src_vla.tar.gz
rm -rf /tmp/src && mkdir -p /tmp/src && tar -xzf "$SRC_TGZ" -C /tmp/src || die "src extract failed"
log "src sha256=$(sha256sum "$SRC_TGZ" | cut -c1-16)"
(cd /tmp/src && find rsi -name '*.py' | sort | xargs md5sum | md5sum | sed 's/^/  py-tree md5: /')
export PYTHONPATH=/tmp/src:$PYTHONPATH
python - "$MDIR" "$ENV/bin/python" <<'EOF' || die "plan rewrite failed"
import json, sys
p = json.load(open("/tmp/plan_in.json"))
v = p["vla"]
v["checkpoint"], v["python"] = sys.argv[1], sys.argv[2]
v["openvla_root"] = "/tmp/vlacode/" + ("simplevla_rl" if v.get("model_family") == "oft" else "openvla")
v["rollout_gpus"], v["train_gpus"] = [0], [0]
v.pop("workdir", None)
json.dump(p, open("/tmp/plan.json", "w"), indent=2)
print("--- PLAN (rewritten)"); print(json.dumps(p, indent=1))
EOF

stage "3 main run"; CUR=main
RUN=$PFS/runs/$NAME
[ -e "$RUN" ] && [ -z "${RESUME_RUN:-}" ] && RUN=$PFS/runs/$NAME-$(date -u +%Y%m%dT%H%M%SZ)
RESUME_FLAG=""
if [ -n "${RESUME_RUN:-}" ]; then
  RUN=$PFS/runs/$RESUME_RUN
  [ -f "$RUN/plan.json" ] && [ ! -f "$RUN/report.json" ] || die "resume target $RUN missing or already complete"
  RESUME_FLAG="--resume"
  log "resuming $RUN (rounds done: $(ls $RUN | grep -cE '^round-[0-9]+\.json$'))"
fi
RNAME=$(basename "$RUN")
mkdir -p "$PFS/runs"
log "out=$RUN  workdir=$RUN.work  args=${ARGS:-}"
heartbeat() {
  local n=0 latest f
  while true; do
    if [ $n -lt 12 ]; then sleep 150; else sleep 600; fi
    n=$((n + 1))
    echo "===== HEARTBEAT [$(date -u +%FT%TZ)] $(el) name=$NAME ====="
    echo "  run files: $(ls "$RUN" 2>/dev/null | grep -vE -- '-(cases|attempts)-|^test-' | tr '\n' ' ')"
    python - "$RUN" <<'EOF' 2>/dev/null
import glob, json, os, sys
for line in open(os.path.join(sys.argv[1], "archive.jsonl")):
    n = json.loads(line)
    if n.get("node_id") == "n0":
        print("  NODE n0 gate", n.get("gate"), "audit", n.get("audit"))
for p in sorted(glob.glob(os.path.join(sys.argv[1], "round-[0-9][0-9].json"))):
    d = json.load(open(p))
    print("  ROUND", d["round"], "parent", d.get("parent"), "accepted", d.get("accepted"),
          " ".join(f"{c['node']}:gate={c.get('gate')},audit={c.get('audit')}" for c in d.get("candidates", [])))
# training receipts are unreadable from outside the job (BOS 403), so the diagnostics the analysis needs go here
for p in sorted(glob.glob(os.path.join(sys.argv[1], "ckpt-*", "receipt.json"))):
    r = json.load(open(p)); e = r.get("extra", {}); cf = e.get("clipfrac") or [0]; s1 = e.get("step1_logratio") or {}
    print("  RECEIPT", os.path.basename(os.path.dirname(p)), r.get("operator"), "items", r.get("items"),
          "steps", r.get("optimizer_steps"), "ratio", e.get("ratio_mode", "legacy"),
          "clip1 %.3f clipmean %.3f" % (cf[0], sum(cf) / len(cf)),
          "s1out", None if not s1 else round(s1["outside_clip"], 4),
          "loss %.4f>%.4f" % (r.get("loss_first", 0), r.get("loss_last", 0)), "sec", round(r.get("seconds", 0)))
EOF
    latest=$(ls -td "$RUN.work"/*/ 2>/dev/null | head -1)
    echo "  latest call: $(basename "$latest") results: $(cat "$latest"results-*.jsonl 2>/dev/null | wc -l)"
    for f in "$latest"log*.txt; do
      [ -f "$f" ] || continue
      tail -c 2000 "$f" | tr '\r' '\n' | grep -v '^\s*$' | tail -n 2 | cut -c1-240 | sed "s|^|    $(basename "$f"): |"
    done
    echo "  gpu: $(timeout 30 nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader 2>&1)  load: $(cut -d' ' -f1-3 /proc/loadavg)"
  done
}
heartbeat &
HB=$!
# shellcheck disable=SC2086
( cd /tmp/src && timeout -k 120 "${RUN_TIMEOUT_S:-93600}" python -m rsi.run_libero --plan /tmp/plan.json --out "$RUN" $RESUME_FLAG ${ARGS:-} ) > /tmp/main.log 2>&1 &
MAIN=$!
tail -n +1 -f /tmp/main.log --pid=$MAIN &
TAILP=$!
wait $MAIN; RC=$?
sleep 2; kill $HB $TAILP 2>/dev/null
log "main run exit rc=$RC"
CUR=report

stage "4 results"
echo "===== RSI_RESULT_BEGIN name=$NAME run=$RNAME rc=$RC $(el) ====="
for f in report.json failure.json accepted.jsonl baseline.json test_eval.json heldout_eval.json backend-accounting.json retained.json; do
  if [ -f "$RUN/$f" ]; then echo "----- FILE $f -----"; cat "$RUN/$f"; echo; fi
done
for f in $(ls "$RUN"/round-[0-9][0-9].json 2>/dev/null); do
  echo "----- FILE $(basename "$f") (compact) -----"
  python - "$f" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
print(json.dumps(dict(round=d["round"], parent=d["parent"], accepted=d["accepted"], seconds={k: round(v) for k, v in d.get("seconds", {}).items()})))
for c in d.get("candidates", []):
    sig = c.get("signal") or {}
    print(json.dumps(dict(node=c["node"], gate=c["gate"], audit=c.get("audit"), author=c.get("author"), program=c.get("program"),
                          verified_rate=sig.get("verified_rate"), mixed_fraction=sig.get("mixed_fraction"))))
EOF
done
echo "----- FILE tests.txt -----"
python - "$RUN" <<'EOF'
import glob, hashlib, json, os, sys
for p in sorted(glob.glob(os.path.join(sys.argv[1], "test-*.jsonl")) + glob.glob(os.path.join(sys.argv[1], "baseline-rep*.jsonl"))):
    recs = [json.loads(l) for l in open(p) if l.strip()]
    ids = hashlib.sha256(json.dumps([r["id"] for r in recs]).encode()).hexdigest()[:16]
    print("TESTBITS", os.path.basename(p), len(recs), ids, "".join("1" if r["score"] >= 0.5 else "0" for r in recs))
EOF
if [ $RC -ne 0 ]; then
  echo "----- latest worker logs (failure context) -----"
  for d in $(ls -td "$RUN.work"/*/ 2>/dev/null | head -2); do
    for f in "$d"log*.txt; do [ -f "$f" ] && { echo "--- $f"; tail -c 20000 "$f" | tr '\r' '\n' | grep -v '^\s*$' | tail -n 60 | cut -c1-400; }; done
  done
fi
echo "===== RSI_RESULT_END name=$NAME rc=$RC ====="

stage "5 copy small files to BOS"
DEST=$BOS/runs/$RNAME
mkdir -p "$DEST"
(cd "$RUN" 2>/dev/null && find . -type f ! -path './ckpt-*' -size -200M -print0 | xargs -0 -r cp --parents -f -t "$DEST") \
  && log "copied $(cd "$RUN" && find . -type f ! -path './ckpt-*' -size -200M | wc -l) files to $DEST"
cp -f /tmp/main.log "$DEST/main_stdout.log" 2>/dev/null
cp -f /tmp/plan.json "$DEST/plan_input.json" 2>/dev/null
log "done rc=$RC"
echo "RSI_JOB_DONE name=$NAME rc=$RC"
exit $RC

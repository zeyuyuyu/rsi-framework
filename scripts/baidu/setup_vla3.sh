#!/bin/bash
# setup_vla3.sh = setup_vla2.sh with RSI_JOBS / RSI_VTGZ overrides: on Yangquan the tarballs and the venv are staged on
# the pool's CFS (the Beijing BOS mount reads at KB/s there). New file: running jobs source the old one.
# (setup_vla2.sh header follows)
# setup_vla2.sh = setup_vla.sh with RSI_PFS / RSI_ENV overrides (new file: running jobs source the old one).
# VLA stack on an AIHC node (RTX Blackwell, sm_120: torch 2.2 cannot run here, so the image's torch 2.8 is kept and
# the OpenVLA pins go on top of it). Builds a reusable venv on PFS once (later jobs only activate it), installs the
# EGL loader, unpacks LIBERO and the model code to /tmp, and checks: MuJoCo render, a LIBERO-10 scene, imports of
# both rollout workers, and the hf-mirror checkpoint download. Run as a probe (bash setup_vla.sh) or sourced
# by run_vla.sh (VLA_SETUP_SOURCED=1: no tests, no downloads).
set -u
PFS=${RSI_PFS:-/mnt/pfs/shitianyu-rsi}   # RSI_PFS: node-local dir where no shared PFS mounts (Yangquan)
J=${RSI_JOBS:-/mnt/bos/shitianyu-rsi/jobs}
ENV=${RSI_ENV:-$PFS/envs/vla312-r3}
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PIP_NO_INPUT=1 PYTHONUNBUFFERED=1
T0=${T0:-$(date +%s)}; el() { echo "t+$(( $(date +%s) - T0 ))s"; }
# The A800 worker env as the workers see it (PYTHONNOUSERSITE=1), except where Python 3.12 / sm_120 force a change:
# torch 2.8 (image) for 2.2, tensorflow-cpu 2.17.1 for 2.15, sentencepiece 0.2.0 for 0.1.99 (no 3.12 wheels),
# opencv-python 4.10.0.84 for 4.13 (4.13 requires numpy>=2, tensorflow 2.17 numpy<2), hydra-core 1.3.2 for 1.2.0
# (1.2.0 does not import on Python >= 3.11).
PINS="mujoco==3.9.0 PyOpenGL==3.1.10 numpy==1.26.4 robosuite==1.4.1 bddl==3.6.0 easydict==1.13 gym==0.25.2 hydra-core==1.3.2
  transformers==4.40.1 tokenizers==0.19.1 timm==0.9.10 peft==0.11.1 sentencepiece==0.2.0 json-numpy==2.1.1
  draccus==0.8.0 tensorflow-cpu==2.17.1 opencv-python==4.10.0.84 scipy==1.15.3 numba imageio termcolor future
  matplotlib pyyaml jsonlines cloudpickle==3.1.2 einops==0.8.2 h5py"

# fetch_model <hf repo> <dir>: hf-mirror through curl (the image's huggingface_hub fails against the mirror),
# resumable, one downloader per checkpoint (lock dir), .download_done marks a complete copy for every job.
fetch_model() {
  local repo=$1 dir=$2 lock waited=0 ok attempt
  lock=$(dirname "$dir")/.$(basename "$dir").lock
  mkdir -p "$(dirname "$dir")"
  while [ ! -f "$dir/.download_done" ]; do
    if mkdir "$lock" 2>/dev/null; then
      echo "${NAME:-probe} $(hostname) $(date -u +%FT%TZ)" > "$lock/owner"
      ok=no
      for attempt in 1 2 3 4 5; do
        echo "fetch $repo attempt $attempt $(el)"
        if python3 - "$repo" "$dir" <<'EOF'
import json, os, subprocess, sys, urllib.request
repo, d = sys.argv[1], sys.argv[2]
meta = json.load(urllib.request.urlopen(f"https://hf-mirror.com/api/models/{repo}?blobs=true", timeout=60))
os.makedirs(d, exist_ok=True)
for s in meta["siblings"]:
    f, size = s["rfilename"], s.get("size")
    out = os.path.join(d, f)
    os.makedirs(os.path.dirname(out) or d, exist_ok=True)
    if size is not None and os.path.exists(out) and os.path.getsize(out) == size:
        continue
    url = f"https://hf-mirror.com/{repo}/resolve/{meta['sha']}/{f}"
    # abort a stalled transfer (< 100 kB/s for 2 min); the next attempt resumes the partial file
    rc = subprocess.run(["curl", "-sSfL", "--retry", "5", "--retry-delay", "10", "--speed-limit", "102400",
                         "--speed-time", "120", "-C", "-", "-o", out, url]).returncode
    got = os.path.getsize(out) if os.path.exists(out) else -1
    if rc != 0 or (size is not None and got != size):
        sys.exit(f"incomplete {f}: curl rc={rc} size {got} expected {size}")
    print("  got", f, got, flush=True)
json.dump(dict(repo=repo, sha=meta["sha"]), open(os.path.join(d, ".source.json"), "w"))
EOF
        then ok=yes; break; fi
      done
      if [ $ok = yes ]; then
        ( cd "$dir" && for f in $(ls *.safetensors | sort); do echo "$f $(sha256sum "$f" | cut -d' ' -f1)"; done | sha256sum | cut -d' ' -f1 ) > "$dir/.sha256"
        date -u +%FT%TZ > "$dir/.download_done"; echo "fetched $repo $(du -sh "$dir" | cut -f1) $(el)"
      fi
      rm -rf "$lock"; [ $ok = yes ] || return 1
    else
      [ $waited -ge 10800 ] && { echo "waited ${waited}s for the download of $repo"; return 1; }
      if [ -n "$(find "$lock" -maxdepth 0 -mmin +240 2>/dev/null)" ]; then mv "$lock" "$lock.stale.$$" 2>/dev/null; continue; fi
      [ $((waited % 600)) -eq 0 ] && echo "waiting for download by $(cat "$lock/owner" 2>/dev/null) (${waited}s)"
      sleep 30; waited=$((waited + 30))
    fi
  done
}

echo "== node $(el)"
nvidia-smi --query-gpu=name,compute_cap,driver_version,memory.total --format=csv,noheader
mkdir -p "$PFS"; df -h "$PFS" | tail -1

echo "== apt egl $(el)"
if ! ls /usr/lib/x86_64-linux-gnu/libEGL.so.1 >/dev/null 2>&1 || ! ls /usr/lib/x86_64-linux-gnu/libOSMesa.so* >/dev/null 2>&1; then
  # Yangquan reaches the image's own apt sources but no other internet: tuna only when the defaults fail
  if ! timeout 300 apt-get -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update -qq 2>&1 | tail -1; then :; fi
  if ! apt-cache policy libegl1 2>/dev/null | grep -q Candidate; then
    sed -i "s|http://archive.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g; s|http://security.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g" /etc/apt/sources.list 2>/dev/null
    timeout 600 apt-get -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update -qq 2>&1 | tail -1
  fi
  # EGL first and on its own: on Yangquan the osmesa download (libllvm) is slow enough to time out the whole install
  timeout 600 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libegl1 libopengl0 libgl1 libglx0 libglvnd0 2>&1 | tail -1
  [ "${RSI_SKIP_OSMESA:-0}" = 1 ] || timeout 600 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libosmesa6 2>&1 | tail -1
  echo "apt done $(el): $(ls /usr/lib/x86_64-linux-gnu/libEGL.so.1 /usr/lib/x86_64-linux-gnu/libOSMesa.so* 2>/dev/null | tr '\n' ' ')"
fi
ls /usr/share/glvnd/egl_vendor.d/

LOCK=$ENV.lock; WAITED=0
DONE=$ENV/.done-$(echo "$PINS" | tr -s " \n" " " | sha256sum | cut -c1-12)
# Yangquan (no PyPI): unpack the Beijing venv that export_yq.sh staged on BOS, at the same absolute path
VTGZ=${RSI_VTGZ:-/mnt/bos/shitianyu-rsi/yq/vla312-r3.tgz}
if [ ! -f "$DONE" ] && [ "$ENV" = /mnt/pfs/shitianyu-rsi/envs/vla312-r3 ] && [ -f "$VTGZ.sha256" ]; then
  echo "== venv from BOS $(el)"
  cp -f "$VTGZ" /tmp/venv.tgz && [ "$(sha256sum /tmp/venv.tgz | cut -d' ' -f1)" = "$(cat "$VTGZ.sha256")" ] \
    && tar -C / -xzf /tmp/venv.tgz && rm -f /tmp/venv.tgz && echo "venv unpacked $(el)" || echo "VENV_UNPACK_FAILED $(el)"
  [ -f "$DONE" ] || echo "VENV_FROM_BOS_PINS_MISMATCH: $(ls "$ENV"/.done-* 2>/dev/null) vs $DONE"
fi
while [ ! -f "$DONE" ]; do
  if mkdir -p "$(dirname "$ENV")" && mkdir "$LOCK" 2>/dev/null; then
    echo "$(hostname) $(date -u +%FT%TZ)" > "$LOCK/owner"
    echo "== venv build -> $ENV $(el)"
    # a failed build keeps its env: the next build only installs what is missing
    [ -x "$ENV/bin/python" ] || python3 -m venv --system-site-packages "$ENV" || { rm -rf "$LOCK"; exit 2; }
    # shellcheck disable=SC2086
    timeout 3000 "$ENV/bin/pip" install -q --timeout 60 --retries 3 $PINS 2>&1 | grep -v notice | tail -5
    "$ENV/bin/python" -c "import mujoco, robosuite, transformers, tensorflow, peft, timm, sentencepiece, hydra, bddl" 2>/dev/null \
      || timeout 3000 "$ENV/bin/pip" install -q --timeout 60 --retries 3 -i https://pypi.tuna.tsinghua.edu.cn/simple $PINS 2>&1 | grep -v notice | tail -5
    if "$ENV/bin/python" -c "import mujoco, robosuite, transformers, tensorflow, peft, timm, sentencepiece, hydra, bddl"; then
      "$ENV/bin/pip" freeze > "$DONE"; echo "venv ready $(el)"
    else
      echo "VENV_BUILD_FAILED $(el)"; rm -rf "$LOCK"; exit 3
    fi
    rm -rf "$LOCK"
  else
    [ $WAITED -ge 5400 ] && { echo "VENV_WAIT_TIMEOUT ($(cat "$LOCK/owner" 2>/dev/null))"; exit 4; }
    # a build takes ~25 min; a lock older than an hour belongs to a job that was stopped mid-build
    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +60 2>/dev/null)" ]; then
      echo "stale venv lock ($(cat "$LOCK/owner" 2>/dev/null)); taking over"; mv "$LOCK" "$LOCK.stale.$$" 2>/dev/null; continue
    fi
    [ $((WAITED % 300)) -eq 0 ] && echo "waiting for venv build by $(cat "$LOCK/owner" 2>/dev/null) (${WAITED}s)"
    sleep 30; WAITED=$((WAITED + 30))
  fi
done
. "$ENV/bin/activate"
python -c "import torch, transformers, tensorflow as tf, numpy, mujoco, robosuite, peft, timm; print('versions torch', torch.__version__, 'transformers', transformers.__version__, 'tf', tf.__version__, 'numpy', numpy.__version__, 'mujoco', mujoco.__version__, 'robosuite', robosuite.__version__, 'peft', peft.__version__, 'timm', timm.__version__)" 2>&1 | grep -v Warning | tail -1

echo "== code $(el)"
rm -rf /tmp/libero /tmp/vlacode && mkdir -p /tmp/libero /tmp/vlacode /tmp/libero_cfg
tar -xzf $J/libero_pkg.tgz -C /tmp/libero && tar -xzf $J/vla_code.tgz -C /tmp/vlacode && ls /tmp/vlacode
L=/tmp/libero/LIBERO/libero/libero
cat > /tmp/libero_cfg/config.yaml <<EOF
benchmark_root: $L
bddl_files: $L/bddl_files
init_states: $L/init_files
datasets: /tmp/libero/datasets
assets: $L/assets
EOF
export LIBERO_CONFIG_PATH=/tmp/libero_cfg PYTHONPATH=/tmp/libero/LIBERO${PYTHONPATH:+:$PYTHONPATH} TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
[ "${VLA_SETUP_SOURCED:-0}" = 1 ] && return 0

cat > /tmp/render.py <<'EOF'
import os, mujoco
m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><light pos='0 0 3'/><geom type='box' size='.1 .1 .1'/></worldbody></mujoco>")
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 224, 224); r.update_scene(d); img = r.render()
print("RENDER_OK", img.shape, float(img.mean()), flush=True)
os._exit(0)
EOF
for gl in egl osmesa; do
  echo "== render $gl $(el)"
  MUJOCO_GL=$gl PYOPENGL_PLATFORM=$gl timeout 300 python /tmp/render.py 2>&1 | tail -25
done

cat > /tmp/libero_test.py <<'EOF'
import os, sys, time
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv
suite = benchmark.get_benchmark_dict()["libero_10"]()
task = suite.get_task(0)
bddl = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
t = time.time()
env = OffScreenRenderEnv(bddl_file_name=bddl, camera_heights=256, camera_widths=256)
env.seed(0); env.reset()
print("env build s", round(time.time() - t, 2), flush=True)
obs = env.set_init_state(suite.get_task_init_states(0)[0])
t = time.time()
for _ in range(100):
    obs, r, done, info = env.step([0.0] * 6 + [-1.0])
img = obs["agentview_image"]
print("LIBERO_OK", sys.argv[1], task.name, img.shape, round(float(img.mean()), 2), "ms/step", round((time.time() - t) * 10, 1), flush=True)
os._exit(0)
EOF
for gl in egl osmesa; do
  echo "== libero $gl $(el)"
  MUJOCO_GL=$gl PYOPENGL_PLATFORM=$gl timeout 600 python /tmp/libero_test.py $gl 2>&1 | grep -v Warning | tail -25
done

echo "== worker imports $(el)"
MUJOCO_GL=egl timeout 600 python - <<'EOF' 2>&1 | grep -vE "Warning|WARNING|oneDNN|cpu_feature_guard|rebuild TensorFlow"
import importlib.util, sys, torch
from pathlib import Path
x = torch.randn(256, 256, device="cuda", dtype=torch.bfloat16); print("cuda matmul ok", float((x @ x).float().abs().mean()) > 0, flush=True)
root = Path("/tmp/vlacode/simplevla_rl")
sys.path.insert(0, str(root / "verl" / "utils" / "vla_utils"))
from openvla_oft.modeling_prismatic import OpenVLAForActionPrediction  # noqa
print("OFT_MODEL_IMPORT_OK", flush=True)
spec = importlib.util.spec_from_file_location("lu", root / "verl" / "utils" / "libero_utils.py"); lu = importlib.util.module_from_spec(spec); spec.loader.exec_module(lu)
print("OFT_IMPORTS_OK", flush=True)
EOF

echo "== OFT checkpoint -> PFS $(el)"
[ "${RSI_SKIP_FETCH:-0}" = 1 ] || fetch_model Haozhan72/Openvla-oft-SFT-libero10-traj1 $PFS/models/Openvla-oft-SFT-libero10-traj1
ls -la $PFS/models/Openvla-oft-SFT-libero10-traj1 | head -30; cat $PFS/models/Openvla-oft-SFT-libero10-traj1/.sha256
echo "SETUP_PROBE_DONE $(el)"

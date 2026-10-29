#!/bin/bash
# VLA stack on an AIHC node (RTX Blackwell, sm_120: torch 2.2 cannot run here, so the image's torch 2.8 is kept and
# the OpenVLA pins go on top of it). Builds a reusable venv on PFS once (later jobs only activate it), installs the
# EGL loader, unpacks LIBERO and the model code to /tmp, and checks: MuJoCo render, a LIBERO-10 scene, imports of
# both rollout workers, and the hf-mirror checkpoint download. Run as a probe (bash setup_vla.sh) or sourced
# by run_vla.sh (VLA_SETUP_SOURCED=1: no tests, no downloads).
set -u
PFS=/mnt/pfs/shitianyu-rsi
J=/mnt/bos/shitianyu-rsi/jobs
ENV=$PFS/envs/vla312
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PIP_NO_INPUT=1 PYTHONUNBUFFERED=1
T0=${T0:-$(date +%s)}; el() { echo "t+$(( $(date +%s) - T0 ))s"; }
PINS="mujoco==3.9.0 PyOpenGL==3.1.10 numpy==1.26.4 robosuite==1.5.2 bddl==3.6.0 easydict==1.13 gym==0.25.2
  transformers==4.40.1 tokenizers==0.19.1 timm==0.9.10 peft==0.11.1 sentencepiece==0.2.0 json-numpy==2.1.1
  draccus==0.8.0 tensorflow-cpu==2.17.1 opencv-python-headless imageio termcolor future matplotlib pyyaml
  jsonlines cloudpickle einops h5py hydra-core"

echo "== node $(el)"
nvidia-smi --query-gpu=name,compute_cap,driver_version,memory.total --format=csv,noheader
df -h /mnt/pfs | tail -1

echo "== apt egl $(el)"
if ! ls /usr/lib/x86_64-linux-gnu/libEGL.so.1 >/dev/null 2>&1 || ! ls /usr/lib/x86_64-linux-gnu/libOSMesa.so* >/dev/null 2>&1; then
  sed -i "s|http://archive.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g; s|http://security.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g" /etc/apt/sources.list 2>/dev/null
  timeout 600 apt-get -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update -qq 2>&1 | tail -1
  timeout 900 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libegl1 libopengl0 libgl1 libglx0 libglvnd0 libosmesa6 2>&1 | tail -1
fi
ls /usr/share/glvnd/egl_vendor.d/

LOCK=$ENV.lock; WAITED=0
while [ ! -f "$ENV/.done" ]; do
  if mkdir -p "$(dirname "$ENV")" && mkdir "$LOCK" 2>/dev/null; then
    echo "$(hostname) $(date -u +%FT%TZ)" > "$LOCK/owner"
    echo "== pip mirrors $(el)"
    pip3 config list 2>/dev/null
    BEST=""; BESTMS=999999999
    for idx in https://mirror.baidu.com/pypi/simple https://mirrors.aliyun.com/pypi/simple https://pypi.tuna.tsinghua.edu.cn/simple DEFAULT; do
      rm -rf /tmp/mt; s=$(date +%s%N)
      if [ $idx = DEFAULT ]; then a=(); else a=(-i $idx); fi
      if timeout 300 pip3 download -q --no-deps -d /tmp/mt "${a[@]}" numba==0.61.2 >/dev/null 2>&1; then
        ms=$(( ($(date +%s%N) - s) / 1000000 )); echo "  $idx ${ms}ms $(du -sh /tmp/mt | cut -f1)"
        if [ $ms -lt $BESTMS ]; then BEST=$idx; BESTMS=$ms; fi
      else echo "  $idx FAILED"; fi
    done
    echo "fastest: $BEST"
    if [ "$BEST" = DEFAULT ] || [ -z "$BEST" ]; then IDX=(); else IDX=(-i $BEST); fi
    echo "== venv build -> $ENV $(el)"
    rm -rf "$ENV" && python3 -m venv --system-site-packages "$ENV" || { rm -rf "$LOCK"; exit 2; }
    # shellcheck disable=SC2086
    timeout 3000 "$ENV/bin/pip" install -q --timeout 60 --retries 3 "${IDX[@]}" $PINS 2>&1 | grep -v notice | tail -5
    if "$ENV/bin/python" -c "import mujoco, robosuite, bddl, transformers, tensorflow, peft, timm, sentencepiece"; then
      "$ENV/bin/pip" freeze > "$ENV/.done"; echo "venv ready $(el)"
    else
      echo "VENV_BUILD_FAILED $(el)"; rm -rf "$LOCK"; exit 3
    fi
    rm -rf "$LOCK"
  else
    [ $WAITED -ge 5400 ] && { echo "VENV_WAIT_TIMEOUT ($(cat "$LOCK/owner" 2>/dev/null))"; exit 4; }
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
SRC=/tmp/src && rm -rf $SRC && mkdir -p $SRC && tar -xzf /mnt/bos/shitianyu-rsi/src/rsi_src_vla.tar.gz -C $SRC
MUJOCO_GL=egl timeout 600 python - <<'EOF' 2>&1 | grep -v Warning | tail -15
import importlib.util, sys, torch
from pathlib import Path
sys.path.insert(0, "/tmp/src")
x = torch.randn(256, 256, device="cuda", dtype=torch.bfloat16); print("cuda matmul ok", float((x @ x).float().abs().mean()) > 0)
root = Path("/tmp/vlacode/simplevla_rl")
sys.path.insert(0, str(root / "verl" / "utils" / "vla_utils"))
from openvla_oft.modeling_prismatic import OpenVLAForActionPrediction  # noqa
spec = importlib.util.spec_from_file_location("lu", root / "verl" / "utils" / "libero_utils.py"); lu = importlib.util.module_from_spec(spec); spec.loader.exec_module(lu)
print("OFT_IMPORTS_OK")
sys.path.append("/tmp/vlacode/openvla")
from prismatic.extern.hf.modeling_prismatic import OpenVLAForActionPrediction as O2  # noqa
print("OPENVLA_IMPORTS_OK")
EOF

echo "== hf-mirror OFT checkpoint -> PFS $(el)"
M=$PFS/models/Openvla-oft-SFT-libero10-traj1
mkdir -p $PFS/models
s=$(date +%s)
HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_PROGRESS_BARS=1 timeout 2400 python -c "import sys; from huggingface_hub import snapshot_download; snapshot_download(sys.argv[1], local_dir=sys.argv[2])" Haozhan72/Openvla-oft-SFT-libero10-traj1 $M 2>&1 | tail -3
echo "download s=$(( $(date +%s) - s )) size=$(du -sh $M | cut -f1)"; ls $M | head -30
echo "SETUP_PROBE_DONE $(el)"

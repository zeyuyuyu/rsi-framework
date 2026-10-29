#!/bin/bash
# Third LIBERO probe. Probe 2 kept only the last 3 lines, so a render that succeeded and then failed in the EGL
# context's exit-time free() looked like a failure; here every test prints in full and leaves with os._exit.
# The node GPU is a 96 GB RTX (Blackwell class), which torch 2.2 cannot drive, so the stack under test is the
# image's own torch with the OpenVLA pins on top (transformers 4.40.1 etc.), plus a real LIBERO-10 scene from
# the LIBERO tree shipped on BOS, and the hf-mirror throughput for checkpoints. Writes only /tmp and apt.
set -u
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple
J=/mnt/bos/shitianyu-rsi/jobs
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PIP_NO_INPUT=1 PYTHONUNBUFFERED=1
T0=$(date +%s); el() { echo "t+$(( $(date +%s) - T0 ))s"; }
echo "== node $(el)"
nvidia-smi --query-gpu=name,compute_cap,driver_version,memory.total --format=csv,noheader
df -h /mnt/pfs 2>/dev/null | tail -1; ls /usr/share/glvnd/egl_vendor.d/ 2>&1
python3 -c "import torch, sys; print('torch', torch.__version__, torch.version.cuda, torch.cuda.get_device_capability(0), sys.version.split()[0])"

echo "== apt $(el)"
sed -i "s|http://archive.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g; s|http://security.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g" /etc/apt/sources.list 2>/dev/null
timeout 600 apt-get -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update -qq 2>&1 | tail -2
timeout 900 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libegl1 libopengl0 libgl1 libglx0 libglvnd0 libosmesa6 2>&1 | tail -1
ls /usr/share/glvnd/egl_vendor.d/ 2>&1
printf '{"file_format_version":"1.0.0","ICD":{"library_path":"libEGL_nvidia.so.0"}}\n' > /tmp/10_nvidia.json

echo "== pip $(el)"
python3 -m venv --system-site-packages /tmp/vla && . /tmp/vla/bin/activate
timeout 1500 pip install -q -i "$TUNA" "mujoco==3.9.0" "PyOpenGL==3.1.10" "numpy==1.26.4" "robosuite==1.5.2" "bddl==3.6.0" \
  "easydict==1.13" "gym==0.25.2" "transformers==4.40.1" "tokenizers==0.19.1" "timm==0.9.10" "peft==0.11.1" \
  "sentencepiece==0.1.99" "json-numpy==2.1.1" "draccus==0.8.0" imageio termcolor future matplotlib 2>&1 | grep -v notice | tail -3
echo "pip core done $(el)"
timeout 900 pip install -q -i "$TUNA" tensorflow-cpu 2>&1 | grep -v notice | tail -2
python -c "import tensorflow as tf, numpy, torch, transformers; print('tf', tf.__version__, 'numpy', numpy.__version__, 'torch', torch.__version__, 'transformers', transformers.__version__)" 2>&1 | tail -2
echo "pip tf done $(el)"

cat > /tmp/render.py <<'EOF'
import os, mujoco
m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><light pos='0 0 3'/><geom type='box' size='.1 .1 .1'/></worldbody></mujoco>")
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 224, 224); r.update_scene(d); img = r.render()
print("RENDER_OK", img.shape, float(img.mean()), flush=True)
os._exit(0)
EOF
for cfg in "egl:" "egl:__EGL_VENDOR_LIBRARY_FILENAMES=/tmp/10_nvidia.json" "egl:__EGL_VENDOR_LIBRARY_FILENAMES=/tmp/10_nvidia.json MUJOCO_EGL_DEVICE_ID=0" "osmesa:"; do
  gl=${cfg%%:*}; extra=${cfg#*:}
  echo "== render $gl [$extra] $(el)"
  env MUJOCO_GL=$gl PYOPENGL_PLATFORM=$gl $extra timeout 300 python /tmp/render.py 2>&1 | tail -25
done

echo "== LIBERO $(el)"
mkdir -p /tmp/libero && tar -xzf $J/libero_pkg.tgz -C /tmp/libero && echo "untar $(el)"
L=/tmp/libero/LIBERO/libero/libero
mkdir -p /tmp/libero_cfg
cat > /tmp/libero_cfg/config.yaml <<EOF
benchmark_root: $L
bddl_files: $L/bddl_files
init_states: $L/init_files
datasets: /tmp/libero/datasets
assets: $L/assets
EOF
export LIBERO_CONFIG_PATH=/tmp/libero_cfg PYTHONPATH=/tmp/libero/LIBERO TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
cat > /tmp/libero_test.py <<'EOF'
import os, time
import numpy as np
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv
suite = benchmark.get_benchmark_dict()["libero_10"]()
task = suite.get_task(0)
bddl = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
t = time.time()
env = OffScreenRenderEnv(bddl_file_name=bddl, camera_heights=256, camera_widths=256)
env.seed(0); env.reset()
print("env build s", round(time.time() - t, 2), flush=True)
init = suite.get_task_init_states(0)
obs = env.set_init_state(init[0])
t = time.time()
for _ in range(100):
    obs, r, done, info = env.step([0.0] * 6 + [-1.0])
img = obs["agentview_image"]
print("LIBERO_OK", task.name, img.shape, float(img.mean()), "ms/step", round((time.time() - t) * 10, 1), flush=True)
os._exit(0)
EOF
for cfg in "egl:__EGL_VENDOR_LIBRARY_FILENAMES=/tmp/10_nvidia.json" "egl:" "osmesa:"; do
  gl=${cfg%%:*}; extra=${cfg#*:}
  echo "== libero $gl [$extra] $(el)"
  env MUJOCO_GL=$gl PYOPENGL_PLATFORM=$gl $extra timeout 600 python /tmp/libero_test.py 2>&1 | grep -v Warning | tail -25
done

echo "== hf-mirror $(el)"
for u in https://hf-mirror.com/openvla/openvla-7b-finetuned-libero-10/resolve/main/config.json \
         https://hf-mirror.com/Haozhan72/Openvla-oft-SFT-libero10-traj1/resolve/main/config.json; do
  curl -s -o /dev/null -L --max-time 30 -w "%{http_code} %{size_download}B $u\n" "$u"
done
curl -s -o /dev/null -L --max-time 120 -w "shard %{http_code} %{size_download}B %{speed_download}B/s\n" \
  https://hf-mirror.com/openvla/openvla-7b-finetuned-libero-10/resolve/main/model-00004-of-00004.safetensors
echo "PROBE3_DONE $(el)"

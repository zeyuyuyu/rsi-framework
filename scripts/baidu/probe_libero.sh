#!/bin/bash
# Probe whether an AIHC GPU node can host LIBERO rollouts: EGL rendering under MuJoCo, a pip mirror for the
# OpenVLA stack, and ModelScope availability of the OpenVLA LIBERO checkpoints. Read-only apart from /tmp.
set -u
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple
echo "== node"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
echo "NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:-unset}"
ls /usr/lib/x86_64-linux-gnu 2>/dev/null | grep -iE "libEGL|nvidia-egl|libOSMesa|libGL\." | head -20
python3 --version
echo "== venv"
python3 -m venv /tmp/vla && . /tmp/vla/bin/activate
start=$(date +%s)
timeout 1200 pip install -q -i "$TUNA" "mujoco==3.9.0" PyOpenGL==3.1.10 numpy 2>&1 | tail -3
echo "mujoco install s=$(( $(date +%s) - start ))"
for gl in egl osmesa; do
  echo "== render MUJOCO_GL=$gl"
  MUJOCO_GL=$gl PYOPENGL_PLATFORM=$gl timeout 300 python - <<'EOF' 2>&1 | tail -4
import mujoco
m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><light pos='0 0 3'/><geom type='box' size='.1 .1 .1'/></worldbody></mujoco>")
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 128, 128); r.update_scene(d); img = r.render()
print("RENDER_OK", img.shape, float(img.mean()))
EOF
done
echo "== torch 2.2.0 cu121 download speed"
start=$(date +%s)
timeout 1800 pip download -q -d /tmp/wheels -i "$TUNA" torch==2.2.0 --no-deps 2>&1 | tail -2
echo "torch wheel s=$(( $(date +%s) - start )) size=$(du -sh /tmp/wheels 2>/dev/null | cut -f1)"
echo "== modelscope"
timeout 600 pip install -q -i "$TUNA" modelscope 2>&1 | tail -1
for repo in openvla/openvla-7b-finetuned-libero-10 openvla/openvla-7b-finetuned-libero-goal openvla/openvla-7b; do
  timeout 120 python - "$repo" <<'EOF' 2>&1 | tail -2
import sys
from modelscope.hub.api import HubApi
try:
    files = HubApi().get_model_files(sys.argv[1])
    print("MODELSCOPE_OK", sys.argv[1], len(files), "files")
except Exception as e:
    print("MODELSCOPE_MISSING", sys.argv[1], type(e).__name__, str(e)[:120])
EOF
done
echo "PROBE_DONE"

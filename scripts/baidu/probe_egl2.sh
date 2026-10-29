#!/bin/bash
# Second LIBERO probe: the node has the NVIDIA EGL ICD (libEGL_nvidia) but no glvnd loader (libEGL.so.1).
# Try (a) apt from the Tsinghua mirror, (b) the Ubuntu 22.04 glvnd libraries shipped on BOS. Only /tmp is written
# (and apt packages inside this throwaway container).
set -u
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m venv /tmp/vla && . /tmp/vla/bin/activate
timeout 900 pip install -q -i "$TUNA" "mujoco==3.9.0" PyOpenGL==3.1.10 numpy 2>&1 | grep -v notice | tail -2
render() {
  MUJOCO_GL=egl PYOPENGL_PLATFORM=egl timeout 300 python - <<'EOF' 2>&1 | tail -3
import mujoco
m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><light pos='0 0 3'/><geom type='box' size='.1 .1 .1'/></worldbody></mujoco>")
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 224, 224); r.update_scene(d); img = r.render()
print("RENDER_OK", img.shape, float(img.mean()))
EOF
}
echo "== (a) apt"
id -u; . /etc/os-release; echo "$PRETTY_NAME"
if command -v apt-get >/dev/null; then
  sed -i "s|http://archive.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g; s|http://security.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g" /etc/apt/sources.list 2>/dev/null
  timeout 600 apt-get -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20 update -qq 2>&1 | tail -2
  timeout 600 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libegl1 libopengl0 libgl1 libglx0 libglvnd0 2>&1 | tail -2
  ls /usr/lib/x86_64-linux-gnu | grep -E "^libEGL\.so|^libOpenGL" | head
  echo "-- render after apt"; render
fi
echo "== (b) shipped glvnd"
mkdir -p /tmp/glvnd && tar -xzf /mnt/bos/shitianyu-rsi/jobs/glvnd_u2204.tgz -C /tmp/glvnd && ls /tmp/glvnd
export LD_LIBRARY_PATH=/tmp/glvnd:${LD_LIBRARY_PATH:-}
export __EGL_VENDOR_LIBRARY_DIRS=/tmp/glvnd/egl_vendor.d
echo "-- render with shipped glvnd"; render
echo "PROBE2_DONE"

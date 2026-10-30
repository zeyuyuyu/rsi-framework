"""Create a 1-GPU probe job on the Yangquan A800 pool (aihc-rd-yangquan / yangquan-research).
usage: submit_yq_probe.py [bos|nobos]
The probe is inline (no BOS script), so it also runs when the Beijing BOS bucket does not mount in yq.
It reports GPU, CPU, disks, image torch, apt/PyPI/hf-mirror reachability and speed, and the BOS mount."""
import base64, datetime, json, os, sys
os.environ.setdefault("AIHC_POOL", "aihc-8hyl191nkk9e")
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job
aihc_job.HOST = "aihc.yq.baidubce.com"

HERE = os.path.dirname(os.path.abspath(__file__))
mode = sys.argv[1] if len(sys.argv) > 1 else "bos"
name = f"zw-rsi-yq-probe-{mode}"
probe = r"""
set -x
nvidia-smi -L; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
nproc; free -g | head -2; df -h / /tmp /dev/shm 2>/dev/null
python3 -c "import torch, sys; print('TORCH', torch.__version__, torch.version.cuda, sys.version.split()[0], torch.cuda.get_device_name(0))"
ls /mnt/bos/shitianyu-rsi/jobs 2>&1 | head -5
pip config list 2>/dev/null; cat /etc/pip.conf 2>/dev/null
t=$(date +%s); timeout 600 apt-get update -qq >/dev/null 2>&1 && echo "APT_UPDATE_OK $(( $(date +%s)-t ))s" || echo APT_UPDATE_FAIL
t=$(date +%s); timeout 600 apt-get install -y -qq libegl1 libgl1 >/dev/null 2>&1 && echo "APT_EGL_OK $(( $(date +%s)-t ))s" || echo APT_EGL_FAIL
t=$(date +%s); timeout 600 pip download -q --no-deps mujoco==3.9.0 -d /tmp/pipt && echo "PIP_OK $(( $(date +%s)-t ))s $(du -sh /tmp/pipt | cut -f1)" || echo PIP_FAIL
curl -s -o /dev/null -m 60 -w "HFMIRROR_API %{http_code} %{time_total}s\n" https://hf-mirror.com/api/models/openvla/openvla-7b-finetuned-libero-10
curl -sL -r 0-524287999 -o /dev/null -m 300 -w "HFMIRROR_DL %{http_code} %{size_download}B %{speed_download}B/s\n" https://hf-mirror.com/openvla/openvla-7b-finetuned-libero-10/resolve/main/model-00001-of-00004.safetensors
curl -s -o /dev/null -m 30 -w "HF_DIRECT %{http_code}\n" https://huggingface.co/api/models/openvla/openvla-7b || echo HF_DIRECT_FAIL
curl -s -o /dev/null -m 30 -w "GITHUB %{http_code}\n" https://github.com || echo GITHUB_FAIL
echo YQ_PROBE_DONE
sleep 600
"""
body = {
    "name": name,
    "jobType": "PyTorchJob",
    # base64 keeps the script byte-exact (a quoted bash -c string mangled newlines and $(...) on the first try)
    "command": f"echo {base64.b64encode(probe.encode()).decode()} | base64 -d > /tmp/probe.sh && timeout -k 60 2400 bash /tmp/probe.sh",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "baidu.com/a800_80g_cgpu", "quantity": 1},
            {"name": "cpu", "quantity": 16},
            {"name": "memory", "quantity": 128},
            {"name": "sharedMemory", "quantity": 32},
        ],
        "envs": [{"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"}],
        "enableRDMA": False,
    },
    "priority": "normal",
    "datasources": [
        {"type": "bos", "sourcePath": "bos-research-team/", "mountPath": "/mnt/bos", "options": {"readOnly": True}},
    ] if mode == "bos" else [],
}
json.dump(body, open(os.path.join(HERE, f"body_{name}.json"), "w"), indent=1)
st, out = aihc_job.create(body)
print(st, json.dumps(out, ensure_ascii=False)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    with open(os.path.join(HERE, "jobs_yq.tsv"), "a") as f:
        f.write(f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n")

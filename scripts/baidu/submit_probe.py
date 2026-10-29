"""Create a 1-GPU AIHC job that runs scripts/baidu/probe_libero.sh (uploaded to BOS jobs/). usage: submit_probe.py"""
import datetime, json, os, sys
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job

HERE = os.path.dirname(os.path.abspath(__file__))
name = "zw-rsi-probe-libero"
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": "timeout -k 60 5400 bash /mnt/bos/shitianyu-rsi/jobs/probe_libero.sh",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "baidu.com/rtx_rpbzzz6_96g_cgpu", "quantity": 10000},
            {"name": "cpu", "quantity": 16},
            {"name": "memory", "quantity": 64},
            {"name": "sharedMemory", "quantity": 8},
        ],
        "envs": [{"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"}],
        "enableRDMA": False,
    },
    "priority": "normal",
    "datasources": [
        {"type": "bos", "sourcePath": "bos-research-team/", "mountPath": "/mnt/bos", "options": {"readOnly": False}},
    ],
}
st, out = aihc_job.create(body)
print(st, json.dumps(out)[:400])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    with open(os.path.join(HERE, "jobs.tsv"), "a") as f:
        f.write(f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n")

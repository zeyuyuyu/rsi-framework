"""Create one AIHC job for an RSI arm. usage: submit.py <arm>   (arm: full_s1 | full_s2 | fixed_s2 | nonrec_s2 | shuffled_s2)
Appends name<TAB>jobId to jobs.tsv next to this file (the poller reads it)."""
import datetime, json, os, sys
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job

HERE = os.path.dirname(os.path.abspath(__file__))
arm = sys.argv[1]
name = "zw-rsi-" + arm.replace("_", "-")
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": "timeout -k 120 100800 bash /mnt/bos/shitianyu-rsi/jobs/run_rsi.sh",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "baidu.com/rtx_rpbzzz6_96g_cgpu", "quantity": 10000},
            {"name": "cpu", "quantity": 16},
            {"name": "memory", "quantity": 96},
            {"name": "sharedMemory", "quantity": 16},
        ],
        "envs": [
            {"name": "PLAN", "value": f"shitianyu-rsi/plans/bj_q15_{arm}.json"},
            {"name": "NAME", "value": f"bj_q15_{arm}"},
            {"name": "PREFLIGHT", "value": "1"},
        ],
        "enableRDMA": False,
    },
    "priority": "normal",
    "datasources": [
        {"type": "bos", "sourcePath": "bos-research-team/", "mountPath": "/mnt/bos", "options": {"readOnly": False}},
        {"type": "pfsl3", "sourcePath": "/", "mountPath": "/mnt/pfs",
         "options": {"pfsL3InstanceId": "pfs-QnoasGJTsB",
                     "pfsL3MountPoint": "pfs-QnoasGJTsB.lb-36miyvr1.pfs.bj.baidubce.com", "readOnly": False}},
    ],
}
json.dump(body, open(os.path.join(HERE, f"body_{arm}.json"), "w"), indent=1)
st, out = aihc_job.create(body)
print(st, json.dumps(out)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    with open(os.path.join(HERE, "jobs.tsv"), "a") as f:
        f.write(f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n")

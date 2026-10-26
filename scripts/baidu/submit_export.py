"""Create a CPU-only AIHC job that prints per-problem test scores + independent re-scoring of finished runs.
usage: submit_export.py <job-suffix> <run> [<run> ...]   (runs = PFS run dirs, e.g. bj_q15_fixed_s2)
Appends name<TAB>jobId to jobs.tsv next to this file (the poller reads it)."""
import datetime, json, os, sys
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job

HERE = os.path.dirname(os.path.abspath(__file__))
name = "zw-rsi-export-" + sys.argv[1]
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": "timeout -k 60 7200 bash /mnt/bos/shitianyu-rsi/jobs/run_rsi.sh",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "cpu", "quantity": 16},
            {"name": "memory", "quantity": 32},
            {"name": "sharedMemory", "quantity": 4},
        ],
        "envs": [
            # plan only supplies the benchmark data paths
            {"name": "PLAN", "value": "shitianyu-rsi/plans/bj_q15_fixed_s2.json"},
            {"name": "NAME", "value": name},
            {"name": "EXPORT_RUNS", "value": " ".join(sys.argv[2:])},
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
st, out = aihc_job.create(body)
print(st, json.dumps(out)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    with open(os.path.join(HERE, "jobs.tsv"), "a") as f:
        f.write(f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n")

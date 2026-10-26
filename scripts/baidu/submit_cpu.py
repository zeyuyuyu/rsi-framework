"""Create a CPU-only AIHC job (no card is held):
  submit_cpu.py export <job-suffix> <run> [<run> ...]   per-problem test scores + independent re-scoring of
                                                        finished runs (PFS run dirs, e.g. bj_q15_fixed_s2)
  submit_cpu.py download <job-suffix> <model_id> <a800_sha>   fetch a model to PFS for later GPU jobs
Appends name<TAB>jobId to jobs.tsv next to this file (the poller reads it)."""
import datetime, json, os, sys
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job

HERE = os.path.dirname(os.path.abspath(__file__))
mode, suffix = sys.argv[1], sys.argv[2]
name = f"zw-rsi-{mode}-{suffix}"
if mode == "export":
    envs, limit = [{"name": "EXPORT_RUNS", "value": " ".join(sys.argv[3:])}], 7200
elif mode == "download":
    envs, limit = [{"name": "DOWNLOAD_ONLY", "value": "1"}, {"name": "MS_TIMEOUT", "value": "30000"},
                   {"name": "MODEL_ID", "value": sys.argv[3]}, {"name": "A800_SHA", "value": sys.argv[4]}], 93600
else:
    raise SystemExit(__doc__)
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": f"timeout -k 60 {limit} bash /mnt/bos/shitianyu-rsi/jobs/run_rsi.sh",
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
        ] + envs,
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

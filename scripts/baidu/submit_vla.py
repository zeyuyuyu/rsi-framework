"""Create one AIHC job for a robotics RSI run (run_vla.sh).
usage: submit_vla.py <plan> <model_id> [a800_sha]
  plan: name of shitianyu-rsi/plans/<plan>.json on BOS (A800 plan format; paths are rewritten on the node)
env:  ARGS (extra run_libero args), RESUME_RUN (run dir under /mnt/pfs/shitianyu-rsi/runs), JOB_CPU (default 24)
Appends name<TAB>jobId to jobs.tsv next to this file (copy the line to the poller's jobs.tsv)."""
import datetime, json, os, sys
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job

HERE = os.path.dirname(os.path.abspath(__file__))
plan, model = sys.argv[1], sys.argv[2]
sha = sys.argv[3] if len(sys.argv) > 3 else "unknown"
name = "zw-rsi-" + plan.replace("_", "-")
resume = os.environ.get("RESUME_RUN", "")
if resume:
    name += "-resume"
envs = [{"name": "PLAN", "value": f"shitianyu-rsi/plans/{plan}.json"}, {"name": "NAME", "value": plan},
        {"name": "MODEL_ID", "value": model}, {"name": "A800_SHA", "value": sha},
        {"name": "RUN_TIMEOUT_S", "value": "93600"}, {"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"}]
if os.environ.get("ARGS"):
    envs.append({"name": "ARGS", "value": os.environ["ARGS"]})
if resume:
    envs.append({"name": "RESUME_RUN", "value": resume})
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": "timeout -k 120 97200 bash /mnt/bos/shitianyu-rsi/jobs/run_vla.sh",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "baidu.com/rtx_rpbzzz6_96g_cgpu", "quantity": 10000},
            {"name": "cpu", "quantity": int(os.environ.get("JOB_CPU", "24"))},
            {"name": "memory", "quantity": 128},
            {"name": "sharedMemory", "quantity": 32},
        ],
        "envs": envs,
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
json.dump(body, open(os.path.join(HERE, f"body_{plan}.json"), "w"), indent=1)
st, out = aihc_job.create(body)
print(st, json.dumps(out)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    with open(os.path.join(HERE, "jobs.tsv"), "a") as f:
        f.write(f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n")

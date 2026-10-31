"""CPU-only Yangquan job (no card) that runs a local script against the pool CFS and prints to its log.
usage: submit_yq_script.py <job-suffix> <local script> [NAME=VALUE ...]
The run files of Yangquan jobs are not readable from outside the pool (BOS 403), so readers such as pfs_runs.sh
travel inline (base64 env) and their output comes back through the job log that the yq poller saves.
Example: submit_yq_script.py runs1 pfs_runs.sh RUNROOT=/mnt/cfs/shitianyu-rsi/runs RUNS="yq_oftg_fixed_s1 ..."
Appends name<TAB>jobId to jobs_yq.tsv here and to the yq poller's jobs.tsv."""
import base64, datetime, json, os, sys
os.environ.setdefault("AIHC_POOL", "aihc-serverless")
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job
aihc_job.HOST = "aihc.yq.baidubce.com"

HERE = os.path.dirname(os.path.abspath(__file__))
POLLER_TSV = "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/baidu_yq/jobs.tsv"
if len(sys.argv) < 3:
    raise SystemExit(__doc__)
suffix, script = sys.argv[1], sys.argv[2]
name = f"zw-rsi-yq-script-{suffix}"
envs = [{"name": k, "value": v} for k, v in (a.split("=", 1) for a in sys.argv[3:])]
envs.append({"name": "SCRIPT_B64", "value": base64.b64encode(open(script, "rb").read()).decode()})
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": "bash -c 'echo \"$SCRIPT_B64\" | base64 -d > /tmp/job_script.sh && exec timeout 1500 bash /tmp/job_script.sh'",
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [{"name": "cpu", "quantity": 1}, {"name": "memory", "quantity": 4}],
        "envs": envs,
        "enableRDMA": False,
    },
    "priority": "normal",
    "datasources": [
        {"type": "cfs", "sourcePath": "/", "mountPath": "/mnt/cfs",
         "options": {"readOnly": True, "cfsInstanceId": "cfs-n1EUBUrCPv",
                     "cfsMountPoint": "cfs-n1EUBUrCPv.lb-59r8awst.cfs.yq.baidubce.com"}},
    ],
}
st, out = aihc_job.create(body)
print(st, json.dumps(out, ensure_ascii=False)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    line = f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n"
    for p in (os.path.join(HERE, "jobs_yq.tsv"), POLLER_TSV):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as f:
            f.write(line)

"""submit_vla_yq2.py = submit_vla_yq.py on the staged pool CFS (addendum 15): run_vla4.sh from /mnt/cfs/shitianyu-rsi/jobs,
RSI_CFS_LINK=1 (/mnt/pfs/shitianyu-rsi -> CFS: venv, checkpoints and run dirs persist and resume across jobs),
source rsi_src_v14 from CFS, the BOS mount only for the plan file and the small-file copies.
(submit_vla_yq.py docstring follows)
Create one AIHC job for a robotics RSI run on the Yangquan A800 pool (run_vla3.sh, node-local run dir).
usage: submit_vla_yq.py <plan> <model_id> [a800_sha]
  plan: name of shitianyu-rsi/plans/<plan>.json on BOS (A800 plan format; paths are rewritten on the node)
env:  ARGS (extra run_libero args), JOB_CPU (default 18: 16 jobs x 18 fit the ~297 free CPUs of the queue),
      RSI_PFS (node-local root, default /mnt/pfs/shitianyu-rsi: no PFS mounts there, so it is local disk)
Appends name<TAB>jobId to jobs_yq.tsv here and to the yq poller's jobs.tsv."""
import datetime, json, os, sys
os.environ.setdefault("AIHC_POOL", "aihc-serverless")      # the pool id itself is refused for this sub-account
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")  # yangquan-research (elastic), aihc-rd-yangquan
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job
aihc_job.HOST = "aihc.yq.baidubce.com"

HERE = os.path.dirname(os.path.abspath(__file__))
POLLER_TSV = "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/baidu_yq/jobs.tsv"
plan, model = sys.argv[1], sys.argv[2]
sha = sys.argv[3] if len(sys.argv) > 3 else "unknown"
name = "zw-rsi-" + plan.replace("_", "-")
envs = [{"name": "PLAN", "value": f"shitianyu-rsi/plans/{plan}.json"}, {"name": "NAME", "value": plan},
        {"name": "MODEL_ID", "value": model}, {"name": "A800_SHA", "value": sha},
        {"name": "RUN_TIMEOUT_S", "value": os.environ.get("RUN_TIMEOUT_S", "190800")}, {"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"},
        # /mnt/pfs/shitianyu-rsi is a plain node-local dir on yq; the same path keeps the BOS-staged venv valid
        {"name": "RSI_PFS", "value": "/mnt/pfs/shitianyu-rsi"}, {"name": "RSI_CFS_LINK", "value": "1"},
        {"name": "RSI_JOBS", "value": "/mnt/cfs/shitianyu-rsi/jobs"},
        {"name": "RSI_SRC_TGZ", "value": "/tmp/rsi_src.tgz" if os.environ.get("RSI_SRC_URL")
         else os.environ.get("RSI_SRC_TGZ", "/mnt/cfs/shitianyu-rsi/jobs/rsi_src_v14.tar.gz")}]
if os.environ.get("RSI_SRC_URL"):      # addendum 17: newer source fetched at job start (presigned GET, no credentials)
    envs.append({"name": "RSI_SRC_URL", "value": os.environ["RSI_SRC_URL"]})
if os.environ.get("RSI_LLM_RELAY"):    # addendum 17: presigned URL of this run's relay slots
    envs.append({"name": "RSI_LLM_RELAY", "value": os.environ["RSI_LLM_RELAY"]})
if os.environ.get("ARGS"):
    envs.append({"name": "ARGS", "value": os.environ["ARGS"]})
body = {
    "name": name,
    "jobType": "PyTorchJob",
    "command": ("bash -c 'set -e; [ -z \"${RSI_SRC_URL:-}\" ] || curl -sS --retry 5 -o /tmp/rsi_src.tgz \"$RSI_SRC_URL\"; "
                "exec timeout -k 120 194400 bash /mnt/cfs/shitianyu-rsi/jobs/run_vla4.sh'"),
    "jobSpec": {
        "image": "registry.baidubce.com/inference/vllm-openai:v0.11.0",
        "replicas": 1,
        "resources": [
            {"name": "baidu.com/a800_80g_cgpu", "quantity": 1},
            {"name": "cpu", "quantity": int(os.environ.get("JOB_CPU", "18"))},
            {"name": "memory", "quantity": 160},
            {"name": "sharedMemory", "quantity": 32},
        ],
        "envs": envs,
        "enableRDMA": False,
    },
    "priority": "normal",
    "datasources": [
        {"type": "bos", "sourcePath": "bos-research-team/", "mountPath": "/mnt/bos", "options": {"readOnly": False}},
        {"type": "cfs", "sourcePath": "/", "mountPath": "/mnt/cfs",
         "options": {"readOnly": False, "cfsInstanceId": "cfs-n1EUBUrCPv",
                     "cfsMountPoint": "cfs-n1EUBUrCPv.lb-59r8awst.cfs.yq.baidubce.com"}},
    ],
}
json.dump(body, open(os.path.join(HERE, f"body_{plan}.json"), "w"), indent=1)
st, out = aihc_job.create(body)
print(st, json.dumps(out, ensure_ascii=False)[:600])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    line = f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n"
    for p in (os.path.join(HERE, "jobs_yq.tsv"), POLLER_TSV):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as f:
            f.write(line)

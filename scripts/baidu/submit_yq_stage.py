"""Yangquan staging job: mounts the pool's own CFS at /mnt/cfs (our dir: /mnt/cfs/shitianyu-rsi, nothing else is
touched), probes CFS speed and network (foreign domains through the cluster proxy 10.0.16.2:23180, domestic ones
without it), then fetches OFT checkpoints from huggingface.co through the proxy into CFS (resumable, digest
recorded the way setup_vla2.sh records it, so it can be compared with the A800 digest).
usage: submit_yq_stage.py <tag> <hf_repo> [<hf_repo> ...]"""
import base64, datetime, json, os, sys
os.environ.setdefault("AIHC_POOL", "aihc-serverless")
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job
aihc_job.HOST = "aihc.yq.baidubce.com"
HERE = os.path.dirname(os.path.abspath(__file__))
tag, repos = sys.argv[1], sys.argv[2:]
name = f"zw-rsi-yq-stage-{tag}"
script = r"""
set -u
P=http://10.0.16.2:23180
px() { https_proxy=$P http_proxy=$P HTTPS_PROXY=$P HTTP_PROXY=$P "$@"; }
R=/mnt/cfs/shitianyu-rsi
mkdir -p $R/models $R/envs $R/code $R/runs $R/logs && echo CFS_MKDIR_OK
df -h /mnt/cfs | tail -1
dd if=/dev/zero of=$R/.ddtest bs=16M count=64 oflag=direct 2>&1 | tail -1; rm -f $R/.ddtest
curl -s -o /dev/null -m 30 -w "NOPROXY_HFMIRROR %{http_code}\n" https://hf-mirror.com/api/models/openvla/openvla-7b || echo NOPROXY_HFMIRROR_FAIL
curl -s -o /dev/null -m 30 -w "NOPROXY_PYPI %{http_code}\n" http://mirrors.baidubce.com/pypi/simple/numpy/ || echo NOPROXY_PYPI_FAIL
px curl -s -o /dev/null -m 30 -w "PROXY_HF %{http_code}\n" https://huggingface.co/api/models/openvla/openvla-7b || echo PROXY_HF_FAIL
px curl -s -o /dev/null -m 30 -w "PROXY_GITHUB %{http_code}\n" https://github.com || echo PROXY_GITHUB_FAIL
px curl -s -o /dev/null -m 30 -w "PROXY_PYPI_ORG %{http_code}\n" https://pypi.org/simple/numpy/ || echo PROXY_PYPI_ORG_FAIL
echo PROBE_DONE
fetch() {
  repo=$1; d=$R/models/$(basename $repo)
  [ -f $d/.download_done ] && { echo "HAVE $repo $(cat $d/.sha256)"; return 0; }
  for attempt in 1 2 3 4 5; do
    echo "fetch $repo attempt $attempt $(date -u +%T)"
    if px python3 - "$repo" "$d" <<'EOF'
import json, os, subprocess, sys, time, urllib.request
repo, d = sys.argv[1], sys.argv[2]
meta = json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}?blobs=true", timeout=60))
os.makedirs(d, exist_ok=True)
for s in meta["siblings"]:
    f, size = s["rfilename"], s.get("size")
    out = os.path.join(d, f); os.makedirs(os.path.dirname(out) or d, exist_ok=True)
    if size is not None and os.path.exists(out) and os.path.getsize(out) == size:
        continue
    t = time.time()
    rc = subprocess.run(["curl", "-sSfL", "--retry", "5", "--retry-delay", "10", "--speed-limit", "102400",
                         "--speed-time", "120", "-C", "-", "-o", out,
                         f"https://huggingface.co/{repo}/resolve/{meta['sha']}/{f}"]).returncode
    got = os.path.getsize(out) if os.path.exists(out) else -1
    if rc != 0 or (size is not None and got != size):
        sys.exit(f"incomplete {f}: rc={rc} size {got} expected {size}")
    print("  got", f, got, "%.1f MB/s" % (got / max(time.time() - t, 1e-3) / 1e6), flush=True)
json.dump(dict(repo=repo, sha=meta["sha"]), open(os.path.join(d, ".source.json"), "w"))
EOF
    then
      ( cd $d && for f in $(ls *.safetensors | sort); do echo "$f $(sha256sum "$f" | cut -d' ' -f1)"; done | sha256sum | cut -d' ' -f1 ) > $d/.sha256
      date -u +%FT%TZ > $d/.download_done; echo "FETCHED $repo $(du -sh $d | cut -f1) sha=$(cat $d/.sha256)"; return 0
    fi
  done
  echo "FETCH_FAILED $repo"; return 1
}
for repo in __REPOS__; do fetch $repo; done
ls -la $R/models
echo STAGE_DONE
"""
script = script.replace("__REPOS__", " ".join(repos))
body = {
    "name": name, "jobType": "PyTorchJob",
    "command": f"echo {base64.b64encode(script.encode()).decode()} | base64 -d > /tmp/stage.sh && timeout -k 60 14400 bash /tmp/stage.sh",
    "jobSpec": {"image": "registry.baidubce.com/inference/vllm-openai:v0.11.0", "replicas": 1,
                "resources": [{"name": "baidu.com/a800_80g_cgpu", "quantity": 1}, {"name": "cpu", "quantity": 8},
                              {"name": "memory", "quantity": 64}, {"name": "sharedMemory", "quantity": 8}],
                "envs": [{"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"}], "enableRDMA": False},
    "priority": "normal",
    # the pool's CFS (DescribeFileSystem on cfs.yq.baidubce.com, 2026-10-31): CFS-aihc-yangquan
    "datasources": [{"type": "cfs", "sourcePath": "/", "mountPath": "/mnt/cfs",
                     "options": {"readOnly": False, "cfsInstanceId": "cfs-n1EUBUrCPv",
                                 "cfsMountPoint": "cfs-n1EUBUrCPv.lb-59r8awst.cfs.yq.baidubce.com"}}],
}
json.dump(body, open(os.path.join(HERE, f"body_{name}.json"), "w"), indent=1)
st, out = aihc_job.create(body)
print(st, json.dumps(out, ensure_ascii=False)[:400])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    line = f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n"
    for p in (os.path.join(HERE, "jobs_yq.tsv"),
              "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/baidu_yq/jobs.tsv"):
        open(p, "a").write(line)

"""Yangquan staging job 2: fetches the Beijing tarballs (venv, LIBERO, model code, rsi source, run/setup scripts)
from BOS over short-lived presigned URLs (made on the workstation; the secret key never leaves it) into
/mnt/cfs/shitianyu-rsi/jobs, unpacks the venv onto CFS at the path it was built for (via /mnt/pfs/shitianyu-rsi ->
/mnt/cfs/shitianyu-rsi), fetches further OFT checkpoints from huggingface.co through the cluster proxy, and runs
setup_vla3.sh as a probe (render, LIBERO scene, worker imports).  usage: submit_yq_stage2.py <tag> [hf_repo ...]"""
import base64, datetime, json, os, subprocess, sys
os.environ.setdefault("AIHC_POOL", "aihc-serverless")
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job
aihc_job.HOST = "aihc.yq.baidubce.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PRESIGN = "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/yq/presign.py"
tag, repos = sys.argv[1], sys.argv[2:]
name = f"zw-rsi-yq-stage2-{tag}"
files = {"vla312-r3.tgz": "shitianyu-rsi/yq/vla312-r3.tgz", "vla312-r3.tgz.sha256": "shitianyu-rsi/yq/vla312-r3.tgz.sha256",
         "libero_pkg.tgz": "shitianyu-rsi/jobs/libero_pkg.tgz", "vla_code.tgz": "shitianyu-rsi/jobs/vla_code.tgz",
         "glvnd_u2204.tgz": "shitianyu-rsi/jobs/glvnd_u2204.tgz", "setup_vla3.sh": "shitianyu-rsi/jobs/setup_vla3.sh",
         "run_vla4.sh": "shitianyu-rsi/jobs/run_vla4.sh", "rsi_src_v14.tar.gz": "shitianyu-rsi/src/rsi_src_v14.tar.gz"}
urls = {f: subprocess.check_output([sys.executable, PRESIGN, "bos-research-team", k, "14400"], text=True).strip()
        for f, k in files.items()}
script = r"""
set -u
P=http://10.0.16.2:23180
px() { https_proxy=$P http_proxy=$P HTTPS_PROXY=$P HTTP_PROXY=$P "$@"; }
R=/mnt/cfs/shitianyu-rsi; J=$R/jobs; mkdir -p $J $R/envs $R/models $R/runs
mkdir -p /mnt/pfs && { [ -L /mnt/pfs/shitianyu-rsi ] || ln -s $R /mnt/pfs/shitianyu-rsi; } && ls -la /mnt/pfs/
get() {  # get <file>: 8 parallel ranges for big files, direct (bcebos is domestic: no proxy)
  f=$1; u=$(eval echo \$URL_$(echo $f | tr '.-' '__')); t=$(date +%s)
  size=$(curl -sI "$u" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-length"{print $2}')
  if [ -n "$size" ] && [ "$size" -gt 50000000 ]; then
    n=8; part=$(( (size + n - 1) / n )); rm -f $J/$f.part*
    for i in $(seq 0 $((n-1))); do s=$((i*part)); e=$((s+part-1)); [ $e -ge $size ] && e=$((size-1));
      curl -sS --retry 5 -r $s-$e -o $J/$f.part$i "$u" & done; wait
    cat $(for i in $(seq 0 $((n-1))); do echo $J/$f.part$i; done) > $J/$f && rm -f $J/$f.part*
  else curl -sS --retry 5 -o $J/$f "$u"; fi
  echo "GOT $f $(stat -c %s $J/$f) bytes in $(( $(date +%s)-t ))s (expected ${size:-?})"
}
for f in __FILES__; do get $f; done
[ "$(sha256sum $J/vla312-r3.tgz | cut -d' ' -f1)" = "$(cat $J/vla312-r3.tgz.sha256)" ] && echo VENV_SHA_OK || echo VENV_SHA_BAD
if ! ls $R/envs/vla312-r3/.done-* >/dev/null 2>&1; then
  rm -rf /tmp/vx && mkdir -p /tmp/vx && tar -xzf $J/vla312-r3.tgz -C /tmp/vx && cp -a /tmp/vx/mnt/pfs/shitianyu-rsi/envs/vla312-r3 $R/envs/ && rm -rf /tmp/vx
fi
ls $R/envs/vla312-r3/ | head; ls $R/envs/vla312-r3/.done-* && echo VENV_ON_CFS
fetch() {
  repo=$1; d=$R/models/$(basename $repo)
  [ -f $d/.download_done ] && { echo "HAVE $repo $(cat $d/.sha256)"; return 0; }
  for attempt in 1 2 3; do
    if px python3 - "$repo" "$d" <<'EOF'
import json, os, subprocess, sys, time, urllib.request
repo, d = sys.argv[1], sys.argv[2]
meta = json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}?blobs=true", timeout=60))
os.makedirs(d, exist_ok=True)
for s in meta["siblings"]:
    f, size = s["rfilename"], s.get("size")
    out = os.path.join(d, f); os.makedirs(os.path.dirname(out) or d, exist_ok=True)
    if size is not None and os.path.exists(out) and os.path.getsize(out) == size: continue
    rc = subprocess.run(["curl", "-sSfL", "--retry", "5", "--speed-limit", "102400", "--speed-time", "120", "-C", "-",
                         "-o", out, f"https://huggingface.co/{repo}/resolve/{meta['sha']}/{f}"]).returncode
    got = os.path.getsize(out) if os.path.exists(out) else -1
    if rc != 0 or (size is not None and got != size): sys.exit(f"incomplete {f}")
json.dump(dict(repo=repo, sha=meta["sha"]), open(os.path.join(d, ".source.json"), "w"))
EOF
    then ( cd $d && for f in $(ls *.safetensors | sort); do echo "$f $(sha256sum "$f" | cut -d' ' -f1)"; done | sha256sum | cut -d' ' -f1 ) > $d/.sha256
      date -u +%FT%TZ > $d/.download_done; echo "FETCHED $repo sha=$(cat $d/.sha256)"; return 0; fi
  done; echo "FETCH_FAILED $repo"
}
for repo in __REPOS__; do fetch $repo; done
ls -la $R/models; for d in $R/models/*/; do echo "MODEL $(basename $d) done=$([ -f $d/.download_done ] && echo y || echo n) sha=$(cat $d/.sha256 2>/dev/null)"; done
echo "== setup probe"
cd /tmp && RSI_PFS=/mnt/pfs/shitianyu-rsi RSI_JOBS=$J RSI_VTGZ=$J/vla312-r3.tgz RSI_SKIP_FETCH=1 NVIDIA_DRIVER_CAPABILITIES=all \
  timeout 3600 bash $J/setup_vla3.sh 2>&1 | grep -vE "Warning|WARNING|oneDNN|cpu_feature_guard" | tail -60
echo STAGE2_DONE
"""
script = script.replace("__FILES__", " ".join(files)).replace("__REPOS__", " ".join(repos))
envs = [{"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"}] + \
       [{"name": "URL_" + f.replace(".", "_").replace("-", "_"), "value": u} for f, u in urls.items()]
body = {
    "name": name, "jobType": "PyTorchJob",
    "command": f"echo {base64.b64encode(script.encode()).decode()} | base64 -d > /tmp/stage2.sh && timeout -k 60 14400 bash /tmp/stage2.sh",
    "jobSpec": {"image": "registry.baidubce.com/inference/vllm-openai:v0.11.0", "replicas": 1,
                "resources": [{"name": "baidu.com/a800_80g_cgpu", "quantity": 1}, {"name": "cpu", "quantity": 16},
                              {"name": "memory", "quantity": 128}, {"name": "sharedMemory", "quantity": 32}],
                "envs": envs, "enableRDMA": False},
    "priority": "normal",
    "datasources": [{"type": "cfs", "sourcePath": "/", "mountPath": "/mnt/cfs",
                     "options": {"readOnly": False, "cfsInstanceId": "cfs-n1EUBUrCPv",
                                 "cfsMountPoint": "cfs-n1EUBUrCPv.lb-59r8awst.cfs.yq.baidubce.com"}}],
}
safe = json.loads(json.dumps(body)); [e.update(value="<presigned>") for e in safe["jobSpec"]["envs"] if e["name"].startswith("URL_")]
json.dump(safe, open(os.path.join(HERE, f"body_{name}.json"), "w"), indent=1)   # local copy without the URLs
st, out = aihc_job.create(body)
print(st, json.dumps(out, ensure_ascii=False)[:300])
if st == 200 and isinstance(out, dict) and out.get("jobId"):
    line = f"{name}\t{out['jobId']}\t{datetime.datetime.utcnow().isoformat()}Z\n"
    for p in (os.path.join(HERE, "jobs_yq.tsv"),
              "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/baidu_yq/jobs.tsv"):
        open(p, "a").write(line)

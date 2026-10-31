"""Presigned URLs for one Yangquan run's LLM relay (addendum 17). Writes the relay's file (req GET, resp PUT) to
<out_dir>/<run>.json for cavin, uploads the node's file (req PUT, resp GET) to BOS and prints a presigned GET URL of
it for the job env RSI_LLM_RELAY. All URLs expire after <days>.  usage: mk_relay_urls.py <run> <out_dir> [slots=28] [days=5]"""
import json, os, subprocess, sys
PRESIGN = "/tmp/claude-1000/-home-zeyu/04cfb8d7-2d31-45ec-83a6-11d2231cafdf/scratchpad/yq/presign.py"
HERE = os.path.dirname(os.path.abspath(__file__))
run, out_dir = sys.argv[1], sys.argv[2]
slots = int(sys.argv[3]) if len(sys.argv) > 3 else 28
exp = str(int(float(sys.argv[4]) * 86400) if len(sys.argv) > 4 else 5 * 86400)
def sign(key, method):
    return subprocess.check_output([sys.executable, PRESIGN, "bos-research-team", key, exp, method], text=True).strip()
base = f"shitianyu-rsi/llm_relay/{run}"
node = dict(req_put=[sign(f"{base}/req-{k:02d}.json", "PUT") for k in range(slots)],
            resp_get=[sign(f"{base}/resp-{k:02d}.json", "GET") for k in range(slots)])
relay = dict(req_get=[sign(f"{base}/req-{k:02d}.json", "GET") for k in range(slots)],
             resp_put=[sign(f"{base}/resp-{k:02d}.json", "PUT") for k in range(slots)])
os.makedirs(out_dir, exist_ok=True)
json.dump(relay, open(os.path.join(out_dir, f"{run}.json"), "w"))
os.chmod(os.path.join(out_dir, f"{run}.json"), 0o600)
tmp = os.path.join(out_dir, f"{run}.node.json")
json.dump(node, open(tmp, "w")); os.chmod(tmp, 0o600)
st = subprocess.run([sys.executable, os.path.join(HERE, "bos_rw.py"), "put", "bos-research-team", f"{base}/node_urls.json",
                     tmp, "application/json"], capture_output=True, text=True)
os.remove(tmp)
if "200" not in st.stdout:
    sys.exit("upload failed: " + st.stdout[:200])
print(sign(f"{base}/node_urls.json", "GET"))

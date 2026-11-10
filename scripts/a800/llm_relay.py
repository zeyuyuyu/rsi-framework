"""Answers LLM calls that Yangquan runs post through BOS (rsi/meta/relay.py). Runs on cavin, which holds the gateway
key (~/.cskey, mode 600); uses only presigned URLs for BOS (no BOS credentials here).
usage: llm_relay.py <dir with one <run>.json per run: {"req_get": [...], "resp_put": [...]}>   (loops forever)
State: <dir>/<run>.done holds the answered slots. Log: one line per call."""
import json, sys, time, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, "/data0/home/zeyuwang/rsi/src6")
from rsi.meta.proposers import OpenAICompatClient

d = Path(sys.argv[1])
# 2026-11-03: CommonStack key deactivated (401) -> OpenRouter, same model id (user-approved; addenda 18 and 21 am. 2)
client = OpenAICompatClient("https://openrouter.ai/api/v1", "anthropic/claude-sonnet-5-5", "/data0/home/zeyuwang/.orkey",
                           timeout=400, retries=1)   # 11-04 flapping proxy: short tries, many of them (am. 5)
# 2026-11-10 (addendum 29): 120 s -> 400 s. Meta level v3 allows 12000 reply tokens (reasoning counts inside the cap),
# and a try that times out would be paid for and repeated.


def put(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="PUT",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


while True:
    for f in sorted(d.glob("*.json")):
        run = f.stem
        try:
            urls = json.loads(f.read_text())
        except ValueError:        # a run file that is still being copied: an empty read killed the relay on
            continue              # 2026-11-10 05:36Z (addendum 29); it is read again on the next pass
        donef = d / f"{run}.done"
        done = set(json.loads(donef.read_text())) if donef.exists() else set()
        for k, get_url in enumerate(urls["req_get"]):
            if k in done:
                continue
            try:
                with urllib.request.urlopen(get_url, timeout=60) as r:
                    req = json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code in (403, 404):
                    break                     # slots are used in order: nothing further yet for this run
                print(time.strftime("%FT%TZ", time.gmtime()), run, k, "req_get_error", e.code, flush=True)
                break
            except Exception as e:
                print(time.strftime("%FT%TZ", time.gmtime()), run, k, "req_get_exc", type(e).__name__, flush=True)
                break
            t = time.time()
            for attempt in range(60):          # gateway 5xx / TLS blips / flapping proxy: keep trying ~23 min, inside the
                try:                          # run's 30-min relay wait, before answering with an error
                    content, usage = client(req["prompt"], req["temperature"], req["max_tokens"])
                    out = dict(content=content, usage=usage)
                    break
                except Exception as e:
                    out = dict(error=str(e)[:200])
                    print(time.strftime("%FT%TZ", time.gmtime()), run, k, "retry", attempt, out["error"][:80], flush=True)
                    if time.time() - t > 1380:     # stop at 23 min (+ one try of at most 400 s; the node waits 30 min)
                        break
                    time.sleep(10)
            st = put(urls["resp_put"][k], out)
            done.add(k)
            donef.write_text(json.dumps(sorted(done)))
            print(time.strftime("%FT%TZ", time.gmtime()), run, k, "answered", st, "%.0fs" % (time.time() - t),
                  "tokens", (out.get("usage") or {}).get("total_tokens"), out.get("error", ""), flush=True)
    time.sleep(10)

"""LLM calls relayed through BOS objects, for nodes that must not hold the gateway key (the shared Yangquan pool).

The node PUTs request k to a presigned URL and polls a presigned GET URL for response k; a relay on a machine that
holds the key (scripts/a800/llm_relay.py on cavin) answers. Neither side holds BOS credentials: the URLs are signed
on the workstation, scoped to single objects and expire. The slot counter lives in the run dir, so a resumed run
never reuses a slot.
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


class RelayClient:
    def __init__(self, urls, state_path, poll=10.0, timeout=1800.0, http=None):
        """urls: dict {"req_put": [...], "resp_get": [...]}, or a URL / path of such a JSON file."""
        self.http = http or urllib.request.urlopen
        if isinstance(urls, str):
            if urls.startswith("http"):
                with self.http(urls, timeout=60) as r:
                    urls = json.loads(r.read())
            else:
                urls = json.loads(Path(urls).read_text())
        self.req_put, self.resp_get = urls["req_put"], urls["resp_get"]
        self.state_path, self.poll, self.timeout = Path(state_path), poll, timeout

    def _next_slot(self):
        k = json.loads(self.state_path.read_text())["next"] if self.state_path.exists() else 0
        if k >= len(self.req_put):
            raise RuntimeError("llm_call_failed:relay_slots_exhausted")
        self.state_path.write_text(json.dumps({"next": k + 1}))
        return k

    def __call__(self, prompt, temperature, max_tokens):
        k = self._next_slot()
        body = json.dumps(dict(k=k, prompt=prompt, temperature=temperature, max_tokens=max_tokens)).encode()
        req = urllib.request.Request(self.req_put[k], data=body, method="PUT",
                                     headers={"Content-Type": "application/json"})
        for attempt in range(5):                  # a BOS network blip must not crash the run (yq, 11-02)
            try:
                with self.http(req, timeout=60) as r:
                    if r.status != 200:
                        raise RuntimeError(f"llm_call_failed:relay_put_{r.status}")
                break
            except (urllib.error.URLError, OSError) as e:
                if attempt == 4:
                    raise RuntimeError(f"llm_call_failed:relay_put_{type(e).__name__}")
                time.sleep(5 * (attempt + 1))
        start = time.time()
        while time.time() - start < self.timeout:
            try:
                with self.http(self.resp_get[k], timeout=60) as r:
                    out = json.loads(r.read())
                if out.get("error"):
                    raise RuntimeError(f"llm_call_failed:relay_{out['error'][:60]}")
                return out["content"], out.get("usage") or {}
            except urllib.error.HTTPError as e:
                if e.code not in (403, 404):
                    raise RuntimeError(f"llm_call_failed:relay_get_{e.code}")
            except (urllib.error.URLError, OSError, ValueError):   # reset / timeout / partial body: poll again
                pass
            time.sleep(self.poll)
        raise RuntimeError("llm_call_failed:relay_timeout")

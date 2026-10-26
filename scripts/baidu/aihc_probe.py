"""Read-only probe of Baidu AIHC resource pools (bce-auth-v1 signing, stdlib only).

Secrets are read from ~/.baidu_bce_grasplabs and never printed.
usage: python3 aihc_probe.py <region-host> <Action> [k=v ...]
"""
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
import urllib.request


def creds():
    vals = {}
    for line in open(os.path.expanduser("~/.baidu_bce_grasplabs")):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            vals[k.strip()] = v.strip()
    ak = next(v for k, v in vals.items() if "ACCESS" in k.upper() and "SECRET" not in k.upper()
              or k.upper() in ("AK", "ACCESSKEYID", "ACCESS_KEY_ID"))
    sk = next(v for k, v in vals.items() if "SECRET" in k.upper() or k.upper() == "SK")
    return ak, sk


def enc(s, slash=True):
    return urllib.parse.quote(s, safe="-_.~" + ("" if slash else "/"))


def call(host, action, params, method="GET", body=None, version_header=True):
    ak, sk = creds()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    query = dict(params, action=action)
    cq = "&".join(f"{enc(k)}={enc(str(v))}" for k, v in sorted(query.items()))
    headers = {"host": host, "x-bce-date": ts}
    if version_header:
        headers["version"] = "v2"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    signed = sorted(["host", "x-bce-date"])
    ch = "\n".join(f"{enc(h)}:{enc(headers[h])}" for h in signed)
    prefix = f"bce-auth-v1/{ak}/{ts}/1800"
    key = hmac.new(sk.encode(), prefix.encode(), hashlib.sha256).hexdigest()
    canonical = f"{method}\n/\n{cq}\n{ch}"
    sig = hmac.new(key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    headers["authorization"] = f"{prefix}/{';'.join(signed)}/{sig}"
    req = urllib.request.Request(f"https://{host}/?{cq}", data=data, method=method,
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode(errors="replace")


if __name__ == "__main__":
    host, action = sys.argv[1], sys.argv[2]
    params = dict(kv.split("=", 1) for kv in sys.argv[3:])
    status, out = call(host, action, params)
    print(status)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:int(os.environ.get("MAXCHARS", "6000"))] if isinstance(out, dict) else out)

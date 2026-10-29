"""Minimal BOS client (bce-auth-v1, stdlib only). Secrets come from ~/.baidu_bce_grasplabs, never printed.

usage:
  bos_rw.py put  <bucket> <key> <local-file|-> [content-type]
  bos_rw.py puts <bucket> <key> <text>
  bos_rw.py get  <bucket> <key> [out-file]
  bos_rw.py head <bucket> <key>
  bos_rw.py ls   <bucket> [prefix]
Writes are refused outside the ALLOWED_PREFIX guard below.
"""
import datetime
import hashlib
import hmac
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aihc_probe import creds  # noqa: E402

HOST = os.environ.get("BOS_HOST", "bj.bcebos.com")
ALLOWED_PREFIX = ("bos-research-team", "shitianyu-rsi/")
TIMEOUT = int(os.environ.get("BOS_TIMEOUT", "120"))


def _enc(s, keep_slash=False):
    return urllib.parse.quote(s, safe="-_.~" + ("/" if keep_slash else ""))


def request(method, bucket, key="", query=None, data=None, content_type=None, timeout=TIMEOUT):
    ak, sk = creds()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = "/" + bucket + ("/" + key if key else "")
    cpath = _enc(path, keep_slash=True)
    q = query or {}
    cq = "&".join(f"{_enc(k)}={_enc(str(v))}" for k, v in sorted(q.items()))
    headers = {"host": HOST, "x-bce-date": ts}
    if data is not None:
        headers["content-length"] = str(len(data))
        headers["content-type"] = content_type or "application/octet-stream"
        headers["x-bce-content-sha256"] = hashlib.sha256(data).hexdigest()
    signed = sorted(headers)
    ch = "\n".join(f"{_enc(h)}:{_enc(headers[h].strip())}" for h in signed)
    prefix = f"bce-auth-v1/{ak}/{ts}/1800"
    skey = hmac.new(sk.encode(), prefix.encode(), hashlib.sha256).hexdigest()
    sig = hmac.new(skey.encode(), f"{method}\n{cpath}\n{cq}\n{ch}".encode(), hashlib.sha256).hexdigest()
    headers["authorization"] = f"{prefix}/{';'.join(signed)}/{sig}"
    url = f"https://{HOST}{cpath}" + (f"?{cq}" if cq else "")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def _guard(bucket, key):
    if bucket != ALLOWED_PREFIX[0] or not key.startswith(ALLOWED_PREFIX[1]):
        raise SystemExit(f"refusing write outside {ALLOWED_PREFIX[0]}/{ALLOWED_PREFIX[1]}")


def put(bucket, key, data, content_type=None):
    _guard(bucket, key)
    st, hdr, body = request("PUT", bucket, key, data=data, content_type=content_type)
    return st, hdr.get("ETag") or hdr.get("etag"), body[:300].decode(errors="replace")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("put", "puts"):
        bucket, key = sys.argv[2], sys.argv[3]
        if cmd == "puts":
            data = sys.argv[4].encode()
            ctype = "text/plain"
        else:
            src = sys.argv[4]
            data = sys.stdin.buffer.read() if src == "-" else open(src, "rb").read()
            ctype = sys.argv[5] if len(sys.argv) > 5 else None
        st, etag, body = put(bucket, key, data, ctype)
        print(st, etag, len(data), "bytes", body)
    elif cmd == "get":
        st, hdr, body = request("GET", sys.argv[2], sys.argv[3])
        if len(sys.argv) > 4 and st == 200:
            open(sys.argv[4], "wb").write(body)
            print(st, len(body), "bytes ->", sys.argv[4])
        else:
            print(st)
            print(body[: int(os.environ.get("MAXCHARS", "4000"))].decode(errors="replace"))
    elif cmd == "head":
        st, hdr, _ = request("HEAD", sys.argv[2], sys.argv[3])
        print(st, {k: v for k, v in hdr.items() if k.lower() in ("content-length", "etag", "last-modified", "content-type")})
    elif cmd == "ls":
        q = {"prefix": sys.argv[3]} if len(sys.argv) > 3 else {}
        q["maxKeys"] = "1000"
        st, _, body = request("GET", sys.argv[2], "", query=q)
        print(st)
        print(body[: int(os.environ.get("MAXCHARS", "6000"))].decode(errors="replace"))
    else:
        raise SystemExit(__doc__)

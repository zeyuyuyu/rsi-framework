"""Presigned BOS URL (bce-auth-v1 in the query string), stdlib only. Secrets from ~/.baidu_bce_grasplabs, never printed.
usage: presign.py <bucket> <key> <expire_seconds> <GET|PUT|HEAD>   -> prints the URL"""
import datetime
import hashlib
import hmac
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aihc_probe import creds  # noqa: E402

HOST = os.environ.get("BOS_HOST", "bj.bcebos.com")


def _enc(s, keep_slash=False):
    return urllib.parse.quote(s, safe="-_.~" + ("/" if keep_slash else ""))


def presign(bucket, key, expires, method="GET"):
    ak, sk = creds()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    vhost = f"{bucket}.{HOST}"                      # virtual-host style (the path-style GET returns 403 here)
    cpath = _enc(f"/{key}", keep_slash=True)
    ch = f"host:{_enc(vhost)}"
    prefix = f"bce-auth-v1/{ak}/{ts}/{int(expires)}"
    skey = hmac.new(sk.encode(), prefix.encode(), hashlib.sha256).hexdigest()
    sig = hmac.new(skey.encode(), f"{method}\n{cpath}\n\n{ch}".encode(), hashlib.sha256).hexdigest()
    auth = f"{prefix}/host/{sig}"
    return f"https://{vhost}{cpath}?authorization={urllib.parse.quote(auth, safe='')}"


if __name__ == "__main__":
    bucket, key, exp, method = sys.argv[1], sys.argv[2], sys.argv[3], (sys.argv[4] if len(sys.argv) > 4 else "GET")
    print(presign(bucket, key, exp, method))

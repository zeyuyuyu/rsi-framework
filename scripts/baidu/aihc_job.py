"""AIHC (Baidu Baige) job helper: create / describe / logs / stop / list, bce-auth-v1, stdlib only.

Secrets are read from ~/.baidu_bce_grasplabs and never printed. Every call has a timeout.
StopJob/DeleteJob are refused unless the job id is in created_jobs.txt (jobs this helper created).

usage:
  aihc_job.py create <body.json>           # POST ?action=CreateJob, records the job id
  aihc_job.py describe <jobId>             # POST ?action=DescribeJob (jobId in body)
  aihc_job.py logs <jobId> [maxLines<=1000] [marker] [podName]
  aihc_job.py list [pageSize]              # POST ?action=DescribeJobs
  aihc_job.py stop <jobId>                 # POST ?action=StopJob   (own jobs only)
  aihc_job.py delete <jobId>               # POST ?action=DeleteJob (own jobs only)
env: AIHC_POOL (default aihc-serverless), AIHC_QUEUE (default aihcq-i7kkoqptnigl), MAXCHARS
"""
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from aihc_probe import creds  # noqa: E402

HOST = "aihc.bj.baidubce.com"
POOL = os.environ.get("AIHC_POOL", "aihc-serverless")
QUEUE = os.environ.get("AIHC_QUEUE", "aihcq-i7kkoqptnigl")
LEDGER = os.path.join(HERE, "created_jobs.txt")
TIMEOUT = 60


def _enc(s):
    return urllib.parse.quote(str(s), safe="-_.~")


def call(action, query=None, body=None, method="POST", timeout=TIMEOUT):
    ak, sk = creds()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = dict(query or {}, action=action)
    cq = "&".join(f"{_enc(k)}={_enc(v)}" for k, v in sorted(q.items()))
    headers = {"host": HOST, "x-bce-date": ts}
    signed = sorted(headers)
    ch = "\n".join(f"{_enc(h)}:{_enc(headers[h])}" for h in signed)
    prefix = f"bce-auth-v1/{ak}/{ts}/1800"
    skey = hmac.new(sk.encode(), prefix.encode(), hashlib.sha256).hexdigest()
    sig = hmac.new(skey.encode(), f"{method}\n/\n{cq}\n{ch}".encode(), hashlib.sha256).hexdigest()
    headers["authorization"] = f"{prefix}/{';'.join(signed)}/{sig}"
    headers["X-API-Version"] = "v2"  # NOT "version: v2" (that 404s)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    req = urllib.request.Request(f"https://{HOST}/?{cq}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            st, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        st, raw = e.code, e.read()
    try:
        return st, json.loads(raw or b"{}")
    except ValueError:
        return st, raw[:500].decode(errors="replace")


def pq():
    return {"resourcePoolId": POOL, "queueID": QUEUE}


def create(body):
    st, out = call("CreateJob", pq(), body)
    if st == 200 and isinstance(out, dict) and out.get("jobId"):
        with open(LEDGER, "a") as f:
            f.write(f"{out['jobId']}\t{body.get('name')}\t{datetime.datetime.utcnow().isoformat()}Z\n")
    return st, out


def describe(job_id):
    return call("DescribeJob", pq(), {"jobId": job_id})


def logs(job_id, max_lines=1000, marker=None, pod=None):
    b = {"jobId": job_id, "podName": pod or f"{job_id}-master-0", "namespace": "default",
         "maxLines": int(max_lines)}
    if marker:
        b["marker"] = marker
    return call("DescribeJobLogs", pq(), b)


def own(job_id):
    if not os.path.exists(LEDGER):
        return False
    return any(line.split("\t")[0] == job_id for line in open(LEDGER))


def stop(job_id, action="StopJob"):
    if not own(job_id):
        raise SystemExit(f"refusing {action}: {job_id} was not created by this helper")
    return call(action, pq(), {"jobId": job_id})


def _show(st, out):
    print(st)
    s = json.dumps(out, ensure_ascii=False, indent=1) if isinstance(out, (dict, list)) else str(out)
    print(s[: int(os.environ.get("MAXCHARS", "8000"))])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "create":
        _show(*create(json.load(open(sys.argv[2]))))
    elif cmd == "describe":
        _show(*describe(sys.argv[2]))
    elif cmd == "logs":
        a = sys.argv[2:]
        _show(*logs(a[0], a[1] if len(a) > 1 else 1000, a[2] if len(a) > 2 and a[2] else None,
                    a[3] if len(a) > 3 else None))
    elif cmd == "list":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        _show(*call("DescribeJobs", {"resourcePoolId": POOL}, {"queueID": QUEUE, "pageSize": n, "pageNo": 1}))
    elif cmd == "stop":
        _show(*stop(sys.argv[2]))
    elif cmd == "delete":
        _show(*stop(sys.argv[2], "DeleteJob"))
    else:
        raise SystemExit(__doc__)

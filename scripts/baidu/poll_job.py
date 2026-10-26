"""Poll one AIHC job every ~60 s (max 60 min), fetch all logs at the end, stop it if it sits Pending > 20 min.
usage: poll_job.py <jobId> [outdir]   -- prints one line per status change; logs -> <outdir>/<jobId>.log
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aihc_job  # noqa: E402

job = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(outdir, exist_ok=True)
TERMINAL = {"Succeeded", "Failed", "ManualTermination", "Stopped", "Terminated", "Deleted", "Completed"}
PENDING = {"Pending", "Created", "Scheduled", "Queueing", "Enqueued", "Waiting"}
t0 = time.time()
last = None
running_seen = False


def fetch_logs():
    lines, marker, pages = [], None, 0
    while pages < 20:
        st, out = aihc_job.logs(job, 1000, marker)
        if st != 200 or not isinstance(out, dict):
            lines.append(f"## DescribeJobLogs HTTP {st}: {str(out)[:300]}")
            break
        lines += out.get("logs") or []
        marker = out.get("nextMarker")
        pages += 1
        if not marker:
            break
    with open(os.path.join(outdir, f"{job}.log"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


while time.time() - t0 < 3600:
    try:
        st, d = aihc_job.describe(job)
    except Exception as e:  # transient network error: keep polling
        print(f"[{int(time.time()-t0)}s] describe error {type(e).__name__}", flush=True)
        time.sleep(60)
        continue
    status = d.get("status") if isinstance(d, dict) else f"HTTP{st}"
    with open(os.path.join(outdir, f"{job}.describe.json"), "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    if status != last:
        print(f"[{int(time.time()-t0)}s] status={status}", flush=True)
        last = status
    if status == "Running":
        running_seen = True
    if status in TERMINAL:
        break
    if running_seen or status == "Running":
        lines = fetch_logs()
        done = [ln for ln in lines if "SMOKE_DONE" in ln]
        prog = [ln for ln in lines if "===== [" in ln]
        if prog:
            print(f"[{int(time.time()-t0)}s] progress: {prog[-1][-90:]}", flush=True) if prog[-1] != getattr(fetch_logs, "p", None) else None
            fetch_logs.p = prog[-1]
    if not running_seen and status in PENDING and status != "Scheduled" and time.time() - t0 > 1200:
        print(f"[{int(time.time()-t0)}s] pending >20 min -> StopJob", flush=True)
        print(aihc_job.stop(job), flush=True)
    time.sleep(60)

lines = fetch_logs()
print(f"[{int(time.time()-t0)}s] FINAL status={last} log_lines={len(lines)}", flush=True)
for ln in lines:
    if "SMOKE_SUMMARY_JSON" in ln:
        print(ln[:3000], flush=True)

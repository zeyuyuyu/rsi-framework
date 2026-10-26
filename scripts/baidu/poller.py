"""Poll the zw-rsi-* AIHC jobs every 10 min; save logs; exit when all expected arms are terminal.

Reads jobs.tsv (name<TAB>jobId<TAB>created; the latest line per name wins, so a resubmitted
arm is followed automatically). Never stops or deletes anything.
  logs/<name>.log          full log of the finished (latest) job for that name
  logs/<name>.running.log  latest snapshot while the job runs
  logs/<name>.<jobId>.log  full log of a superseded job id
  status.tsv               current status table;  poller.out (stdout) one line per change
"""
import json
import os
import sys
import time

sys.path.insert(0, "/home/zeyu/rsi/tools/baidu")
import aihc_job  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
os.makedirs(LOGS, exist_ok=True)
EXPECTED = ["zw-rsi-full-s1", "zw-rsi-full-s2", "zw-rsi-fixed-s2", "zw-rsi-nonrec-s2", "zw-rsi-shuffled-s2"]
TERMINAL = {"Succeeded", "Failed", "ManualTermination", "Stopped", "Terminated", "Deleted", "Completed"}
INTERVAL = int(os.environ.get("POLL_INTERVAL", "600"))
MAX_AGE = 5 * 24 * 3600


def jobs():
    latest, every = {}, []
    path = os.path.join(HERE, "jobs.tsv")
    if os.path.exists(path):
        for line in open(path):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1].startswith("job-"):
                latest[parts[0]] = parts[1]
                every.append((parts[0], parts[1]))
    return latest, every


def fetch_logs(job_id):
    lines, marker = [], None
    for _ in range(80):
        try:
            st, out = aihc_job.logs(job_id, 1000, marker)
        except Exception as e:  # network hiccup: return what we have
            lines.append(f"## DescribeJobLogs error {type(e).__name__}")
            break
        if st != 200 or not isinstance(out, dict):
            lines.append(f"## DescribeJobLogs HTTP {st}: {str(out)[:300]}")
            break
        lines += out.get("logs") or []
        nxt = out.get("nextMarker")
        if not nxt or nxt == marker:
            break
        marker = nxt
    return lines


def write(path, lines):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)


def say(msg):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}", flush=True)


t0 = time.time()
last, saved = {}, set()
while True:
    latest, every = jobs()
    table = []
    for name, jid in every:
        if jid in saved:
            continue
        try:
            st, d = aihc_job.describe(jid)
        except Exception as e:
            say(f"{name} {jid} describe error {type(e).__name__}")
            continue
        status = d.get("status") if isinstance(d, dict) else f"HTTP{st}"
        rt = round((d.get("runTimeNanoseconds") or 0) / 3.6e12, 2) if isinstance(d, dict) else None
        table.append((name, jid, status, rt))
        if last.get(jid) != status:
            say(f"{name} {jid} status={status} runtime_h={rt}")
            last[jid] = status
        is_latest = latest.get(name) == jid
        if status in TERMINAL:
            lines = fetch_logs(jid)
            write(os.path.join(LOGS, f"{name}.log" if is_latest else f"{name}.{jid}.log"), lines)
            end = [ln for ln in lines if "RSI_JOB_DONE" in ln or "RSI_JOB_FAILED" in ln]
            say(f"{name} {jid} FINAL {status}: saved {len(lines)} lines; {end[-1][-120:] if end else 'no end marker'}")
            saved.add(jid)
        elif status == "Running" and is_latest:
            lines = fetch_logs(jid)
            write(os.path.join(LOGS, f"{name}.running.log"), lines)
            hb = [ln for ln in lines if "run files:" in ln or "STAGE" in ln or "PREFLIGHT_OK" in ln]
            if hb:
                say(f"{name} progress: {hb[-1].split(' F ', 1)[-1][-220:]}")
    with open(os.path.join(HERE, "status.tsv"), "w") as f:
        for row in table:
            f.write("\t".join(str(x) for x in row) + "\n")
    done = all(n in latest and latest[n] in saved for n in EXPECTED)
    if done:
        say("all expected arms terminal; poller exiting")
        break
    if time.time() - t0 > MAX_AGE:
        say("max age reached; poller exiting")
        break
    time.sleep(INTERVAL)

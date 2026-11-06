"""Stop a running Yangquan RSI job at its next round boundary and resume it with more cards.
usage: yq_boundary_resume.py <run> <jobId> <ngpu> [poll_s]
Polls the job log (heartbeat lists the run files every 10 min). When a new round-NN.json appears, or the job
ends by itself (53 h RUN_TIMEOUT_S), the job is stopped and `NGPU=<ngpu> resume_oftgb_llm.sh <run>` is run.
Log: /home/zeyu/rsi/yq_logs/<run>.boundary.log"""
import os, re, subprocess, sys, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("AIHC_HOST", "aihc.yq.baidubce.com"); os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
import aihc_job  # noqa: E402
aihc_job.HOST = os.environ["AIHC_HOST"]
run, job, ngpu = sys.argv[1], sys.argv[2], sys.argv[3]
poll = int(sys.argv[4]) if len(sys.argv) > 4 else 300
LOG = f"/home/zeyu/rsi/yq_logs/{run}.boundary.log"
TERMINAL = {"Succeeded", "Failed", "ManualTermination", "Stopped", "Terminated", "Deleted", "Completed"}
def say(m):
    with open(LOG, "a") as f: f.write(f"{datetime.datetime.utcnow().isoformat(timespec='seconds')}Z {m}\n")
def status():
    try:
        st, d = aihc_job.describe(job)
        return d.get("status") if isinstance(d, dict) else None
    except Exception as e:
        return None
def rounds_done():
    lines, marker, pages = [], None, 0
    while pages < 30:
        st, out = aihc_job.logs(job, 1000, marker)
        if st != 200 or not isinstance(out, dict): return None, None
        lines += out.get("logs") or []; marker = out.get("nextMarker"); pages += 1
        if not marker: break
    rf = [l for l in lines if "run files:" in l]
    if not rf: return 0, False
    last = rf[-1]
    return len(set(re.findall(r"round-\d{2}\.json", last))), ("report.json" in last)
base, _ = rounds_done()
say(f"watching {run} {job} rounds_done={base} -> resume with NGPU={ngpu}")
if base is None: say("cannot read log; exit"); sys.exit(2)
while True:
    st = status()
    if st in TERMINAL:
        say(f"job ended by itself ({st}); resuming"); break
    cur, done = rounds_done()
    if cur is not None and done:
        say("report.json present: run complete, nothing to do"); sys.exit(0)
    if cur is not None and cur > base:
        say(f"round-{cur:02d}.json seen; stopping {job}")
        try:
            print(aihc_job.stop(job))
        except SystemExit as e:
            say(f"stop refused: {e}"); sys.exit(3)
        for _ in range(60):
            time.sleep(10)
            if status() in TERMINAL: break
        say(f"job status {status()}; resuming")
        break
    time.sleep(poll)
env = dict(os.environ, NGPU=str(ngpu))
r = subprocess.run(["bash", os.path.join(HERE, "resume_oftgb_llm.sh"), run], capture_output=True, text=True, env=env)
say(f"resume rc={r.returncode} out={r.stdout.strip()[-300:]} err={r.stderr.strip()[-200:]}")

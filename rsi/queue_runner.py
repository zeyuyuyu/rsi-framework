"""GPU job queue for a shared box: keeps free GPUs busy without anyone watching.

    python -m rsi.queue_runner <queue_dir>

<queue_dir>/pending/*.json are launched in filename order whenever enough GPUs
are free (nvidia-smi memory below a threshold, not excluded, not already held by
a job this runner started). A job file:

    {"name": "q15_fixed_s3", "ngpus": 2, "module": "rsi.run_code_wm",
     "plan": "/abs/plan.json", "out": "/abs/runs/q15_fixed_s3",
     "gpu_fields": {"llm.sample_gpus": "all", "llm.train_gpus": "first"},
     "args": [], "python": "/abs/python", "pythonpath": "/abs/src:/abs/pylib"}

<queue_dir>/reservations.json ([{"pid", "gpus", "name"}]) keeps GPUs of jobs started
elsewhere out of reach while their pid is alive. The runner writes the plan with the assigned GPUs next to the run, launches it
detached, and moves the job file to running/ then done/ or failed/ by exit code.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .core.gpu import gpu_status, occupied


def free_gpus(exclude, threshold=2000):
    return [g for g, st in sorted(gpu_status().items()) if not occupied(st, threshold) and g not in exclude]


def set_field(plan, dotted, value):
    node = plan
    keys = dotted.split(".")
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value


def main(queue_dir, exclude=(3,), poll=60):
    q = Path(queue_dir)
    for sub in ("pending", "running", "done", "failed", "plans", "logs"):
        (q / sub).mkdir(parents=True, exist_ok=True)
    running = {}   # name -> (Popen, gpus, job_path)
    log = open(q / "runner.log", "a")

    def say(msg):
        log.write(time.strftime("%Y-%m-%dT%H:%M:%SZ ", time.gmtime()) + msg + "\n")
        log.flush()

    say(f"runner start pid={os.getpid()} exclude={list(exclude)}")
    while True:
        for name, (proc, gpus, path) in list(running.items()):
            code = proc.poll()
            if code is not None:
                dest = q / ("done" if code == 0 else "failed") / path.name
                path.rename(dest)
                del running[name]
                say(f"finished {name} code={code} gpus={gpus}")
        held = {g for _, gpus, _ in running.values() for g in gpus}
        # External jobs (started outside this runner) reserve GPUs while their pid lives.
        try:
            for r in json.loads((q / "reservations.json").read_text()):
                try:
                    os.kill(int(r["pid"]), 0)
                    held |= set(r["gpus"])
                except (ProcessLookupError, PermissionError):
                    pass
        except FileNotFoundError:
            pass
        try:
            available = [g for g in free_gpus(set(exclude) | held)]
        except Exception as exc:
            say(f"nvidia-smi failed: {exc}")
            available = []
        for path in sorted((q / "pending").glob("*.json")):
            job = json.loads(path.read_text())
            if len(available) < job["ngpus"]:
                continue
            gpus, available = available[:job["ngpus"]], available[job["ngpus"]:]
            plan = json.loads(Path(job["plan"]).read_text())
            for field, how in job.get("gpu_fields", {}).items():
                set_field(plan, field, gpus if how == "all" else gpus[:1])
            plan_path = q / "plans" / f"{job['name']}.json"
            plan_path.write_text(json.dumps(plan, indent=2))
            env = dict(os.environ, PYTHONPATH=job["pythonpath"])
            argv = [job["python"], "-m", job["module"], "--plan", str(plan_path),
                    "--out", job["out"]] + job.get("args", [])
            logf = open(q / "logs" / f"{job['name']}.log", "a")
            proc = subprocess.Popen(argv, stdout=logf, stderr=subprocess.STDOUT, env=env,
                                    start_new_session=True, cwd=job.get("cwd", "/tmp"))
            run_path = q / "running" / path.name
            path.rename(run_path)
            running[job["name"]] = (proc, gpus, run_path)
            say(f"launched {job['name']} pid={proc.pid} gpus={gpus}")
        time.sleep(poll)


if __name__ == "__main__":
    main(sys.argv[1])

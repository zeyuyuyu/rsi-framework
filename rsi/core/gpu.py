"""GPU admission and supervised worker processes for real backends.

Admission reads nvidia-smi twice, ``gap`` seconds apart, and refuses any
device that is busy in either reading; it never inspects or stops other users'
processes. Workers run in their own process group with a hard wall timeout, so
a hung model load or generate call is killed by this supervisor rather than
trusted to honour an in-process budget.
"""

import os
from pathlib import Path
import re
import signal
import subprocess
import time


def gpu_status():
    """{index: (memory used MiB, utilization %)}."""
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=60, check=True).stdout
    return {int(i): (int(m), int(u)) for i, m, u in (line.split(",") for line in out.strip().splitlines())}


def occupied(status, max_used_mib=2000, idle_context_mib=10240, idle_util=5):
    """A GPU is taken by someone else's work if it holds more than ``max_used_mib``, unless that memory is an
    idle context (under ``idle_context_mib`` at under ``idle_util``% utilization): such contexts, e.g. a CI
    job parked on every GPU for hours, cost their owner nothing if we share the device."""
    used, util = status
    return used > max_used_mib and not (used <= idle_context_mib and util <= idle_util)


def admit(gpus, max_used_mib=2000, gap=30.0, wait_seconds=4 * 3600, poll=60.0):
    """Two readings ``gap`` apart must both show every GPU free (see ``occupied``). A busy GPU is waited
    for (re-checked every ``poll`` seconds) up to ``wait_seconds``, then refused. The wait is long because
    on a shared box another user can take a GPU between our sample and train steps; failing loses the run."""
    gpus = [int(g) for g in gpus]
    deadline = time.time() + wait_seconds
    waited = 0.0
    while True:
        first = gpu_status()
        time.sleep(gap)
        second = gpu_status()
        busy = [g for g in gpus if g not in first or g not in second
                or occupied(first[g], max_used_mib) or occupied(second[g], max_used_mib)]
        if not busy:
            return dict(first={g: first[g] for g in gpus}, second={g: second[g] for g in gpus},
                        gap_seconds=gap, waited_seconds=waited, admitted_at=time.time())
        if time.time() + poll > deadline:
            raise RuntimeError(f"gpu_admission_refused:{busy}")
        time.sleep(poll)
        waited += poll + gap


def supervised(argv, *, gpus, timeout, log_path, env=None):
    """Run argv on the given GPUs; kill the whole process group on timeout."""
    full_env = dict(os.environ, **(env or {}))
    full_env["CUDA_VISIBLE_DEVICES"] = ",".join(str(g) for g in gpus)
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=full_env,
                                start_new_session=True)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise TimeoutError(f"worker_timeout:{argv[:3]}")
    if code != 0:
        raise RuntimeError(f"worker_failed:{code}:{log_path}")


def oom_failed_logs(exc):
    """Log paths of a parallel_worker_failed error when every failed worker ran out of GPU memory
    (another job took memory on our GPU after admission); None for any other failure."""
    text = str(exc)
    if not text.startswith("parallel_worker_failed"):
        return None
    logs = re.findall(r"'([^']+)'", text)
    tail = lambda log: Path(log).read_text(errors="replace")[-50000:]
    return logs if logs and all("CUDA out of memory" in tail(log) for log in logs) else None


def supervised_parallel(jobs, *, timeout):
    """jobs: list of (argv, gpus, log_path, env). All run concurrently."""
    procs = []
    deadline = time.monotonic() + timeout
    for argv, gpus, log_path, env in jobs:
        full_env = dict(os.environ, **(env or {}))
        full_env["CUDA_VISIBLE_DEVICES"] = ",".join(str(g) for g in gpus)
        log = open(log_path, "ab")
        procs.append((subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                       env=full_env, start_new_session=True), log, log_path))
    failed = []
    try:
        for proc, log, log_path in procs:
            remaining = max(1.0, deadline - time.monotonic())
            try:
                code = proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                raise TimeoutError("parallel_worker_timeout")
            if code != 0:
                failed.append(str(log_path))
    finally:
        for proc, log, _ in procs:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            log.close()
    if failed:
        raise RuntimeError(f"parallel_worker_failed:{failed}")

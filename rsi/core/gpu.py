"""GPU admission and supervised worker processes for real backends.

Admission reads nvidia-smi twice, ``gap`` seconds apart, and refuses any
device that is busy in either reading; it never inspects or stops other users'
processes. Workers run in their own process group with a hard wall timeout, so
a hung model load or generate call is killed by this supervisor rather than
trusted to honour an in-process budget.
"""

import os
import signal
import subprocess
import time


def gpu_memory_used():
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=60, check=True).stdout
    return {int(i): int(m) for i, m in (line.split(",") for line in out.strip().splitlines())}


def admit(gpus, max_used_mib=2000, gap=30.0, wait_seconds=4 * 3600, poll=60.0):
    """Two readings ``gap`` apart must both show every GPU idle. A busy GPU is waited
    for (re-checked every ``poll`` seconds) up to ``wait_seconds``, then refused. The wait is long because
    on a shared box another user can take a GPU between our sample and train steps; failing loses the run."""
    gpus = [int(g) for g in gpus]
    deadline = time.time() + wait_seconds
    waited = 0.0
    while True:
        first = gpu_memory_used()
        time.sleep(gap)
        second = gpu_memory_used()
        busy = [g for g in gpus if g not in first or first[g] > max_used_mib
                or second.get(g, 10**9) > max_used_mib]
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

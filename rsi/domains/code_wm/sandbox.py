"""Bounded execution of short Python functions: the external oracle for code tasks.

Every job runs in a forked child with CPU, memory and file-size limits and a
wall-clock kill. Model text is never trusted as an answer: an answer must parse
as a Python literal, and correctness is decided by comparing that literal with
the value the real interpreter computes. A call such as ``f(x)`` written as the
"answer" is therefore rejected instead of passing an executed assertion.
"""

import ast
from concurrent.futures import ProcessPoolExecutor
import json
import os
import resource
import signal
import sys

FORBIDDEN_NAMES = frozenset({
    "open", "exec", "eval", "compile", "input", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "__import__", "breakpoint", "exit", "quit",
    "help", "memoryview", "print", "id", "hash", "object", "type", "super",
    "classmethod", "staticmethod", "property"})


def literal(text):
    """Return (True, value) if ``text`` is a pure Python literal, else (False, None)."""
    try:
        return True, ast.literal_eval(text.strip())
    except Exception:
        return False, None


def static_check(code):
    """Admission filter for model-proposed programs (not for trusted benchmarks)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "syntax"
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(tree.body) != 1 or len(functions) != 1 or functions[0].name != "f":
        return "not_single_function_f"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
                             ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Yield,
                             ast.YieldFrom, ast.With, ast.Try, ast.Raise)):
            return "forbidden_node"
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith("_")):
            return "forbidden_name"
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return "forbidden_attribute"
    return None


def _args(job):
    """Positional arguments of a call. Benchmark inputs (trusted) may be expressions such
    as ``dict(did=0)``; model-proposed inputs must be literals. Empty input = no args."""
    text = job["input"].strip()
    if not text:
        return True, ()
    if job.get("trusted"):
        return True, eval(compile("(" + text + ",)", "<input>", "eval"), {"__builtins__": __builtins__})
    return literal("(" + text + ",)")


def _limits(cpu_seconds, memory_bytes):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))


def _child(job, write_fd, cpu_seconds, memory_bytes):
    _limits(cpu_seconds, memory_bytes)
    sys.setrecursionlimit(2000)
    out = {"ok": False}
    try:
        scope = {"__builtins__": __builtins__}
        exec(compile(job.get("prelude", "") + job["code"], "<program>", "exec"), scope)
        f = scope.get("f")
        kind = job["kind"]
        if kind == "run":
            ok, args = _args(job)
            if not ok:
                raise ValueError("input_not_literal")
            value = f(*args)
            text = repr(value)
            round_trip, back = literal(text)
            out = {"ok": True, "output": text,
                   "round_trip": bool(round_trip and back == value)}
        elif kind == "check_output":
            ok, args = _args(job)
            good, claimed = literal(job["answer"])
            if not ok:
                raise ValueError("input_not_literal")
            out = {"ok": True, "correct": bool(good and f(*args) == claimed),
                   "answer_is_literal": good}
        elif kind in ("check_call", "run_call"):
            # Trusted benchmark code whose call is a full expression (LiveCodeBench).
            value = eval(compile(job["call"], "<call>", "eval"), scope)
            if kind == "run_call":
                text = repr(value)
                round_trip, back = literal(text)
                out = {"ok": True, "output": text,
                       "round_trip": bool(round_trip and back == value)}
            else:
                good, claimed = literal(job["answer"])
                out = {"ok": True, "correct": bool(good and value == claimed),
                       "answer_is_literal": good}
        elif kind == "check_input":
            ok, expected = literal(job["output"])
            good, args = literal("(" + job["answer"] + ",)")
            if not ok:
                raise ValueError("output_not_literal")
            out = {"ok": True, "correct": bool(good and f(*args) == expected),
                   "answer_is_literal": good}
        else:
            raise ValueError("unknown_job_kind")
    except BaseException as exc:  # noqa: BLE001 - the child reports every failure
        out = {"ok": False, "error": type(exc).__name__}
    try:
        payload = json.dumps(out)[:65536].encode()
    except Exception:
        payload = b'{"ok": false, "error": "unserializable"}'
    os.write(write_fd, payload)
    os._exit(0)


def execute(job, timeout=2.0, cpu_seconds=2, memory_bytes=1 << 30):
    """Run one job dict in a limited forked child; never raises for program faults."""
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        _child(job, write_fd, cpu_seconds, memory_bytes)
    os.close(write_fd)

    def alarm(*_):
        raise TimeoutError

    previous = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    chunks, timed_out = [], False
    try:
        while True:
            chunk = os.read(read_fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        os.close(read_fd)
        if timed_out:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        os.waitpid(pid, 0)
    if timed_out:
        return {"ok": False, "error": "Timeout"}
    try:
        return json.loads(b"".join(chunks) or b'{"ok": false, "error": "NoOutput"}')
    except ValueError:
        return {"ok": False, "error": "BadOutput"}


def _execute_many(jobs):
    return [execute(job) for job in jobs]


def execute_all(jobs, workers=32, chunk=64):
    """Execute jobs in parallel worker processes; results keep job order."""
    jobs = list(jobs)
    if not jobs:
        return []
    chunks = [jobs[i:i + chunk] for i in range(0, len(jobs), chunk)]
    with ProcessPoolExecutor(max_workers=min(workers, len(chunks))) as pool:
        results = []
        for part in pool.map(_execute_many, chunks):
            results.extend(part)
    return results

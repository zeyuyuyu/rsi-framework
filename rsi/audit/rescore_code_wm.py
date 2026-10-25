"""Independent re-scorer for code-world-model test records (multi-angle check #1).

Written separately from the domain's scorer on purpose: it re-parses every raw
model completion with a regex-based extractor (no ``ast`` on the assertion),
evaluates the literal with ``ast.literal_eval`` only, runs the benchmark program
in a fresh ``python3 -I`` subprocess (not the fork sandbox), and compares
values there. It then reports agreement with the engine's recorded scores.

    python -m rsi.audit.rescore_code_wm <run_dir> <cruxeval.jsonl> <lcb.parquet>
"""

import json
from pathlib import Path
import re
import subprocess
import sys

ANSWER = re.compile(r"\[ANSWER\](.*?)(?:\[/ANSWER\]|$)", re.S)

# Only trusted benchmark code and benchmark call expressions are exec'd/eval'd, in a
# fresh isolated interpreter; model text is only ever passed through ast.literal_eval.
RUNNER = r'''
import ast, json, sys
job = json.loads(sys.stdin.read())
ns = {}
exec(job["prelude"] + job["code"], ns)
value = eval(job["call"], ns)
try:
    claimed = ast.literal_eval(job["claimed"])
except Exception:
    print(json.dumps({"ok": True, "correct": False})); sys.exit(0)
print(json.dumps({"ok": True, "correct": bool(value == claimed)}))
'''

INPUT_RUNNER = r'''
import ast, json, sys
job = json.loads(sys.stdin.read())
ns = {}
exec(job["code"], ns)
try:
    args = ast.literal_eval("(" + job["claimed_args"] + ",)")
    expected = ast.literal_eval(job["output"])
except Exception:
    print(json.dumps({"ok": True, "correct": False})); sys.exit(0)
print(json.dumps({"ok": True, "correct": bool(ns["f"](*args) == expected)}))
'''


def extract_rhs(text):
    """Text after the last top-level '==' in the first assert line of the answer block."""
    m = ANSWER.findall(text or "")
    if not m:
        return None
    line = next((l.strip() for l in m[-1].splitlines() if l.strip().startswith("assert")), None)
    if line is None:
        return None
    depth, quote, last = 0, None, None
    i = 0
    while i < len(line) - 1:
        ch = line[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and line[i:i + 2] == "==":
            last = i
            break
        i += 1
    return None if last is None else line[last + 2:].strip()


def extract_args(text):
    m = ANSWER.findall(text or "")
    if not m:
        return None
    line = next((l.strip() for l in m[-1].splitlines() if l.strip().startswith("assert f(")), None)
    if line is None:
        return None
    body, depth = line[len("assert f("):], 1
    for k, ch in enumerate(body):
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            return body[:k]
    return None


def run(runner, job, timeout=5):
    try:
        p = subprocess.run([sys.executable, "-I", "-c", runner], input=json.dumps(job),
                           capture_output=True, text=True, timeout=timeout)
        return json.loads(p.stdout.strip().splitlines()[-1]).get("correct", False)
    except Exception:
        return False


def main(run_dir, crux_path, lcb_path):
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor
    run_dir = Path(run_dir)
    crux = {f"cruxO-{r['id']}": r for r in map(json.loads, open(crux_path)) if r}
    crux_i = {f"cruxI-{k[6:]}": r for k, r in crux.items()}
    lcb = {f"lcbx-{r['id']}": r for _, r in pd.read_parquet(lcb_path).iterrows()}
    summary = {}
    for path in sorted(run_dir.glob("test-*-*.jsonl")):
        suite = path.name.split("-")[1]
        records = [json.loads(l) for l in open(path)]
        jobs = []
        for rec in records:
            text = (rec.get("details") or {}).get("text", "")
            if suite == "cruxeval_o":
                r = crux[rec["id"]]
                rhs = extract_rhs(text)
                jobs.append(None if rhs is None else (RUNNER, dict(
                    prelude="", code=r["code"], call=f"f({r['input']})", claimed=rhs)))
            elif suite == "lcb_exec":
                r = lcb[rec["id"]]
                rhs = extract_rhs(text)
                jobs.append(None if rhs is None else (RUNNER, dict(
                    prelude="from typing import *\n", code=r["code"], call=r["input"], claimed=rhs)))
            elif suite == "cruxeval_i":
                r = crux_i[rec["id"]]
                args = extract_args(text)
                jobs.append(None if args is None else (INPUT_RUNNER, dict(
                    code=r["code"], output=r["output"], claimed_args=args)))
        with ThreadPoolExecutor(32) as pool:
            mine = list(pool.map(lambda j: False if j is None else run(*j), jobs))
        recorded = [rec["score"] >= 0.5 for rec in records]
        agree = sum(a == b for a, b in zip(mine, recorded))
        summary[path.name] = dict(n=len(records), recorded=sum(recorded) / len(records),
                                  rescored=sum(mine) / len(records), agreement=agree / len(records),
                                  disagreements=[rec["id"] for rec, a, b in zip(records, mine, recorded)
                                                 if a != b][:20])
        print(path.name, json.dumps(summary[path.name]))
    (run_dir / "audit-rescore.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:4])

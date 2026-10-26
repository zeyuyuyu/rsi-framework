"""Turn the RSI_RESULT blocks of finished Baidu job logs into small files: results/baidu/<run>/<file>.
usage: extract_results.py <logs_dir> <out_dir>
Only final logs (<job>.log, written by poller.py once a job is terminal) are read. A run job prints one
block; an export job (EXPORT_RUNS) prints one block per exported run."""
import re
import sys
from pathlib import Path

PREFIX = re.compile(r"^\S+ std(?:out|err) F ?")


def extract(log, block, out):
    end = next((i for i, ln in enumerate(block) if "RSI_RESULT_END" in ln), len(block))
    block = block[:end + 1]
    name = re.search(r"name=(\S+)", block[0]).group(1)
    files, current = {}, None
    for ln in block[1:-1]:
        m = re.match(r"----- FILE (\S+)( \(compact\))? -----$", ln)
        if m:
            current = m.group(1)
            files[current] = []
        elif ln.startswith("PLAN_DIGEST"):
            files.setdefault("parity.txt", []).append(ln)
        elif current:
            files[current].append(ln)
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    changed = 0
    for fname, body in files.items():
        text = "\n".join(body).strip() + "\n"
        path = d / fname
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
            changed += 1
    (d / f"SOURCE-{log.stem}.txt").write_text(f"{block[0]}\n{block[-1]}\nextracted from Baidu AIHC job log {log.name}\n")
    print(name, sorted(files), "changed", changed)


def main(logs, out):
    for log in sorted(logs.glob("zw-rsi-*.log")):
        if log.name.endswith((".running.log", ".watch.log")):
            continue
        lines = [PREFIX.sub("", ln.rstrip("\n")) for ln in log.open(errors="replace")]
        for begin in (i for i, ln in enumerate(lines) if "RSI_RESULT_BEGIN" in ln):
            extract(log, lines[begin:], out)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

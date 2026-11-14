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
    # a continuation job (resume_oftgb_llm.sh names it <run>_resumeMMDDHHMM) writes the same run directory as <run>
    name = re.sub(r"_resume\d{8}$", "", name)
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
    # A run cut off by the wall time and later resumed has two blocks under one name (the partial one,
    # then the complete one from the -resume job). Blocks that carry report.json are written last, so the
    # complete run's files always win whatever order the logs sort in.
    blocks = []
    for log in sorted(logs.glob("zw-rsi-*.log")):
        if log.name.endswith((".running.log", ".watch.log")):
            continue
        with log.open(errors="replace") as stream:
            lines = [PREFIX.sub("", ln.rstrip("\n")) for ln in stream]
        for begin in (i for i, ln in enumerate(lines) if "RSI_RESULT_BEGIN" in ln):
            end = next((i for i in range(begin, len(lines)) if "RSI_RESULT_END" in lines[i]), len(lines))
            complete = any(ln.startswith("----- FILE report.json") for ln in lines[begin:end])
            # an evaluation job carries no report.json; a failed attempt and its successful resubmission then tie
            # on `complete`, so a block that exited 0 is also written after one that did not
            ok = re.search(r"\brc=0\b", lines[begin]) is not None
            blocks.append(((complete, ok), log, lines[begin:]))
    for _, log, block in sorted(blocks, key=lambda b: b[0]):
        extract(log, block, out)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

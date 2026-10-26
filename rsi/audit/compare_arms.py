"""Pre-registered claim comparisons across arms (C1-C5), from per-problem test scores.

Reads every run under results/ that has per-problem scores: A800 runs (test-<suite>-<node>.jsonl) and Baidu
runs (tests.txt TESTBITS lines). For each run it takes the initial version (n0) and the retained final
version (last accepted node; report.json or accepted.jsonl). Id lists are checked by digest, so problems
pair one-to-one across runs and platforms.

    python -m rsi.audit.compare_arms results/ [--suite cruxeval_o] [--study long8] [--json out.json]

--study long8 reads the 8-round runs of Addendum 3 (bj_q15_long8<arm>_s<seed>) instead of the main study.

C1  final - initial of `full` (and of `fixed`), per-problem, seed-averaged
C2  fixed - shuffled, C3 fixed - nonrec, C4 full - fixed, C5 fixed - onebig: final vs final at the same seed
Seed-averaged per-problem differences, paired bootstrap CI over problems (prereg v2, Bars).
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from ..core.stats import paired_bootstrap

ARM = re.compile(r"(?:main|bj)_q15_(long8)?(fixed|nonrec|shuffled|full|onebig)_s(\d+)(?:_r\d+)?$")


def _digest(ids):
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16]


def _final_node(run):
    acc = run / "accepted.jsonl"
    if acc.exists():
        nodes = [json.loads(l)["node"] for l in open(acc) if l.strip() and '"node"' in l]
        if nodes:
            return nodes[-1]
    rep = run / "report.json"
    if rep.exists():
        return json.loads(rep.read_text()).get("retained")
    return None


def load_scores(run, suite):
    """{node: (digest, [0/1, ...])} for one run directory."""
    out = {}
    for p in run.glob(f"test-{suite}-*.jsonl"):
        recs = [json.loads(l) for l in open(p) if l.strip()]
        out[p.stem.split("-", 2)[2]] = (_digest([r["id"] for r in recs]),
                                        [1 if r["score"] >= 0.5 else 0 for r in recs])
    tests = run / "tests.txt"
    if tests.exists():
        for line in open(tests):
            parts = line.split()
            if len(parts) == 5 and parts[0] == "TESTBITS" and parts[1].startswith(f"test-{suite}-"):
                node = parts[1][len(f"test-{suite}-"):-len(".jsonl")]
                out[node] = (parts[3], [int(c) for c in parts[4]])
    return out


def collect(root, suite, study=""):
    runs = {}
    for run in sorted(p for p in Path(root).glob("*/runs2/*") if p.is_dir()) + \
               sorted(p for p in Path(root).glob("baidu/*") if p.is_dir()):
        m = ARM.match(run.name)
        if not m or (m.group(1) or "") != study:
            continue
        scores = load_scores(run, suite)
        final = _final_node(run)
        if "n0" not in scores or final not in scores:
            continue
        arm, seed = m.group(2), int(m.group(3))
        if (arm, seed) in runs and not run.name.endswith(tuple(f"_r{i}" for i in range(2, 9))):
            continue   # a numbered rerun replaces a failed first attempt, never the reverse
        runs[(arm, seed)] = dict(run=str(run), final=final, initial=scores["n0"], final_scores=scores[final])
    return runs


def seed_avg(pairs):
    """pairs: [(a_list, b_list)] per seed -> per-problem seed-averaged (a, b) lists."""
    n = len(pairs[0][0])
    a = [sum(p[0][i] for p in pairs) / len(pairs) for i in range(n)]
    b = [sum(p[1][i] for p in pairs) / len(pairs) for i in range(n)]
    return a, b


def report(name, pairs, bar):
    a, b = seed_avg([(x, y) for x, y, _ in pairs])
    diff = sum(y - x for x, y in zip(a, b)) / len(a)
    low, high = paired_bootstrap(a, b)
    per_seed = {s: round(100 * (sum(y) - sum(x)) / len(x), 2) for x, y, s in pairs}
    # interim until all 3 pre-registered seeds are in (C1 also needs >= 2 of 3 seeds excluding 0 individually)
    return dict(claim=name, seeds=sorted(per_seed), per_seed_points=per_seed, mean_points=round(100 * diff, 2),
                ci95_points=[round(100 * low, 2), round(100 * high, 2)], bar_points=bar,
                mean_and_ci_pass=bool(100 * diff >= bar and low > 0), final=sorted(per_seed) == [1, 2, 3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--suite", default="cruxeval_o")
    ap.add_argument("--study", default="")
    ap.add_argument("--json")
    args = ap.parse_args()
    runs = collect(args.root, args.suite, args.study)
    digests = {r["initial"][0] for r in runs.values()} | {r["final_scores"][0] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"problem id lists differ across runs: {sorted(digests)}")
    out = dict(suite=args.suite, study=args.study or "main", runs={f"{a}_s{s}": dict(run=r["run"], final=r["final"],
                                                        initial=round(100 * sum(r["initial"][1]) / len(r["initial"][1]), 2),
                                                        final_score=round(100 * sum(r["final_scores"][1]) / len(r["final_scores"][1]), 2))
                                       for (a, s), r in sorted(runs.items())}, claims=[])
    for arm in ("full", "fixed", "nonrec", "shuffled", "onebig"):
        pairs = [(r["initial"][1], r["final_scores"][1], s) for (a, s), r in sorted(runs.items()) if a == arm]
        if pairs:
            out["claims"].append(report(f"C1 {arm}: final - initial", pairs, 2.0))
    for name, arm, ctrl in (("C2 fixed - shuffled", "fixed", "shuffled"), ("C3 fixed - nonrec", "fixed", "nonrec"),
                            ("C4 full - fixed", "full", "fixed"), ("C5 fixed - onebig", "fixed", "onebig")):
        seeds = sorted(s for (a, s) in runs if a == arm and (ctrl, s) in runs)
        if seeds:
            pairs = [(runs[(ctrl, s)]["final_scores"][1], runs[(arm, s)]["final_scores"][1], s) for s in seeds]
            out["claims"].append(report(name, pairs, 1.0))
    for c in out["claims"]:
        print(json.dumps(c))
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()

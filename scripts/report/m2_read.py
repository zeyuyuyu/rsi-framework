"""Addendum 21: the one-time read of M2-A (start `pre`) and M2-B (start `tun`) on the official LIBERO-Goal test.

Each comparison is llm minus rep over seeds 1-3 of the Yangquan study (results/baidu/yq_m2_<start>_<arm>_s<seed>).
Every arm is measured on its final retained policy (report.json "retained"). The three seeds are pooled, then a
per-episode paired bootstrap is taken: each draw resamples episode ids once, for both arms and all seeds.
The cavin replicate is not read here (amendment 4b).
usage: python3 scripts/report/m2_read.py [results root] [--check] [--json out.json]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rsi.audit.compare_arms import load_scores, seed_avg   # noqa: E402
from rsi.core.stats import mcnemar_exact, paired_bootstrap   # noqa: E402

SUITE = "libero_official"
BARS = {"pre": ("M2-A", 3.0), "tun": ("M2-B", 2.0)}


def run_record(run):
    rep = json.loads((run / "report.json").read_text())
    node = rep["retained"]
    scores = load_scores(run, SUITE)
    if node not in scores or "n0" not in scores:
        raise SystemExit(f"{run.name}: no test bits for retained node {node} or n0")
    authors = []
    for f in sorted(run.glob("round-*.json")):
        lines = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        if len(lines) == 1 and "candidates" in lines[0]:      # A800 round file: one object
            cands = lines[0]["candidates"]
        else:                                                  # Baidu extract: round line, then one line per node
            cands = [c for c in lines if "node" in c]
        authors.append([c.get("author") for c in cands])
    fallback_rounds = sum(1 for a in authors if a and a[-1] == "search")   # the new proposal (c1); c0 is the incumbent
    return dict(run=run.name, retained=node, digest=scores[node][0], bits=scores[node][1],
                n0_digest=scores["n0"][0], n0_bits=scores["n0"][1], fallback_rounds=fallback_rounds,
                rounds=len(authors))


def compare(root, start):
    name, bar = BARS[start]
    recs = {(arm, s): run_record(Path(root) / "baidu" / f"yq_m2_{start}_{arm}_s{s}")
            for arm in ("rep", "llm") for s in (1, 2, 3)}
    digests = {r["digest"] for r in recs.values()} | {r["n0_digest"] for r in recs.values()}
    if len(digests) != 1:
        raise SystemExit(f"{name}: episode id lists differ across runs: {sorted(digests)}")
    pairs = [(recs[("rep", s)]["bits"], recs[("llm", s)]["bits"]) for s in (1, 2, 3)]
    a, b = seed_avg(pairs)
    diff = sum(y - x for x, y in zip(a, b)) / len(a)
    low, high = paired_bootstrap(a, b)
    per_seed = {}
    for s in (1, 2, 3):
        x, y = recs[("rep", s)]["bits"], recs[("llm", s)]["bits"]
        p, gain, loss = mcnemar_exact(x, y)
        lo, hi = paired_bootstrap(x, y)
        per_seed[s] = dict(rep=round(100 * sum(x) / len(x), 2), llm=round(100 * sum(y) / len(y), 2),
                           diff=round(100 * (sum(y) - sum(x)) / len(x), 2), ci95=[round(100 * lo, 2), round(100 * hi, 2)],
                           mcnemar_p=round(p, 4), llm_only=gain, rep_only=loss)
    return dict(claim=name, start=start, n_episodes=len(a), bar_points=bar,
                mean_points=round(100 * diff, 2), ci95_points=[round(100 * low, 2), round(100 * high, 2)],
                passes=bool(100 * diff >= bar and low > 0), per_seed=per_seed,
                runs={f"{arm}_s{s}": dict(run=r["run"], retained=r["retained"],
                                          test=round(100 * sum(r["bits"]) / len(r["bits"]), 2),
                                          initial_n0=round(100 * sum(r["n0_bits"]) / len(r["n0_bits"]), 2),
                                          fallback_rounds=r["fallback_rounds"], rounds=r["rounds"])
                      for (arm, s), r in sorted(recs.items())})


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json")
        out = args[i + 1]
        del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    if check:   # structure only, no test numbers: run before the one-time read
        for start in ("pre", "tun"):
            for arm in ("rep", "llm"):
                for s in (1, 2, 3):
                    r = run_record(Path(root) / "baidu" / f"yq_m2_{start}_{arm}_s{s}")
                    print(r["run"], r["retained"], r["digest"], r["n0_digest"], len(r["bits"]), len(r["n0_bits"]),
                          "fallback", r["fallback_rounds"], "rounds", r["rounds"])
        return
    res = [compare(root, start) for start in ("pre", "tun")]
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

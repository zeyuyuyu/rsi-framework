"""Addendum 21: the one-time read of M2-A (start `pre`) and M2-B (start `tun`) on the official LIBERO-Goal test.

Each comparison is llm minus rep over seeds 1-3 of the Yangquan study (results/baidu/yq_m2_<start>_<arm>_s<seed>).
Every arm is measured on its final retained policy (report.json "retained"). The three seeds are pooled, then a
per-episode paired bootstrap is taken: each draw resamples episode ids once, for both arms and all seeds.
The cavin replicate is not read here (amendment 4b).
usage: python3 scripts/report/m2_read.py [results root] [--check] [--json out.json]
       [--platform baidu|a800] [--seeds 1,2,3] [--starts pre,tun]   (a800 = the cavin replicate, amendment 4b)
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
        text = f.read_text()
        try:
            whole = json.loads(text)                            # A800 round file: one (pretty-printed) object
        except json.JSONDecodeError:
            whole = None
        if isinstance(whole, dict) and "candidates" in whole:
            cands = whole["candidates"]
        else:                                                  # Baidu extract: round line, then one line per node
            lines = [json.loads(l) for l in text.splitlines() if l.strip()]
            cands = [c for c in lines if "node" in c]
        authors.append([c.get("author") for c in cands])
    fallback_rounds = sum(1 for a in authors if a and a[-1] == "search")   # the new proposal (c1); c0 is the incumbent
    return dict(run=run.name, retained=node, digest=scores[node][0], bits=scores[node][1],
                n0_digest=scores["n0"][0], n0_bits=scores["n0"][1], fallback_rounds=fallback_rounds,
                rounds=len(authors))


PLATFORMS = {"baidu": ("baidu", "yq_m2"), "a800": ("a800/runs2", "a8_m2")}   # amendment 4b: the cavin replicate


def run_dir(root, start, arm, seed, platform="baidu"):
    sub, prefix = PLATFORMS[platform]
    return Path(root) / sub / f"{prefix}_{start}_{arm}_s{seed}"


def compare(root, start, seeds=(1, 2, 3), platform="baidu"):
    name, bar = BARS[start]
    recs = {(arm, s): run_record(run_dir(root, start, arm, s, platform))
            for arm in ("rep", "llm") for s in seeds}
    digests = {r["digest"] for r in recs.values()} | {r["n0_digest"] for r in recs.values()}
    if len(digests) != 1:
        raise SystemExit(f"{name}: episode id lists differ across runs: {sorted(digests)}")
    pairs = [(recs[("rep", s)]["bits"], recs[("llm", s)]["bits"]) for s in seeds]
    a, b = seed_avg(pairs)
    diff = sum(y - x for x, y in zip(a, b)) / len(a)
    low, high = paired_bootstrap(a, b)
    per_seed = {}
    for s in seeds:
        x, y = recs[("rep", s)]["bits"], recs[("llm", s)]["bits"]
        p, gain, loss = mcnemar_exact(x, y)
        lo, hi = paired_bootstrap(x, y)
        per_seed[s] = dict(rep=round(100 * sum(x) / len(x), 2), llm=round(100 * sum(y) / len(y), 2),
                           diff=round(100 * (sum(y) - sum(x)) / len(x), 2), ci95=[round(100 * lo, 2), round(100 * hi, 2)],
                           mcnemar_p=round(p, 4), llm_only=gain, rep_only=loss)
    return dict(claim=name, start=start, platform=platform, seeds=list(seeds), n_episodes=len(a), bar_points=bar,
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
    platform, seeds, starts = "baidu", (1, 2, 3), ("pre", "tun")
    if "--platform" in args:
        i = args.index("--platform"); platform = args[i + 1]; del args[i:i + 2]
    if "--seeds" in args:
        i = args.index("--seeds"); seeds = tuple(int(x) for x in args[i + 1].split(",")); del args[i:i + 2]
    if "--starts" in args:
        i = args.index("--starts"); starts = tuple(args[i + 1].split(",")); del args[i:i + 2]
    root = args[0] if args else "results"
    if check:   # structure only, no test numbers: run before the one-time read
        for start in starts:
            for arm in ("rep", "llm"):
                for s in seeds:
                    r = run_record(run_dir(root, start, arm, s, platform))
                    print(r["run"], r["retained"], r["digest"], r["n0_digest"], len(r["bits"]), len(r["n0_bits"]),
                          "fallback", r["fallback_rounds"], "rounds", r["rounds"])
        return
    res = [compare(root, start, seeds, platform) for start in starts]
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

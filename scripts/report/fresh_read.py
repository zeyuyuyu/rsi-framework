"""Addendum 30: the one-time read of the sealed fresh-scene test (1000 sampled placements per suite, the same for
every run, used by no run for training, gating or auditing).

Per run: one evaluation of the retained policy (results/baidu/<run>_fresh/tests.txt on Yangquan,
results/a800/runs2/<run>_fresh/test-libero_fresh-*-rep1.jsonl on the A800 node). Reference: the per-episode mean of
the initial policy's evaluations on that platform (yq_fresh_n0_<suite>_<k>, a8_fresh_n0_<suite>_<k>). Comparisons are
paired per episode within a platform (seed 0 A800, seeds 1-3 Yangquan), seed-averaged, with a paired bootstrap CI
(10,000 draws). A noise figure next to every block: two halves of the reference evaluations.

Blocks and bars (addendum 30):
  spatial main    F1 fixed - n0 >= +3 (CI > 0)   F2 fixed - shuffled >= +3   F3 fixed - nonrec >= +2   F5 fixed - onebig >= +2
  goal main       the same four on the Goal runs (descriptive against the same bars; the Goal audit records are known)
  spatial repair  FS1 meta3 - fixed(BC) >= +3 (CI > 0)   FS2 meta3 - full (CI)   meta3 - n0 and fixed(BC) - n0 (CI)
  long12          FL1 fixed12 - n0 >= +5 (CI > 0)   FL3 fixed12 - nonrec12 >= +2 (CI > 0)   fixed12 - onebig12 if run
usage: python3 scripts/report/fresh_read.py <block> [results root] [--check] [--json out.json]
       block: spatial_main | goal_main | spatial_repair | spatial_long12 | goal_long12 | goal_guard12 | goal_nogate
--check prints which evaluations exist and no number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rsi.audit.compare_arms import seed_avg        # noqa: E402
from rsi.core.stats import paired_bootstrap        # noqa: E402

N = 1000


def bits_of(d):
    """Per-episode outcomes of the one fresh evaluation in directory d, or None. (ids digest, bits)"""
    if not d.exists():
        return None
    tests = d / "tests.txt"
    if tests.exists():
        for line in open(tests):
            p = line.split()
            if len(p) == 5 and p[0] == "TESTBITS" and p[1].startswith("test-libero_fresh-"):
                return p[3], [int(c) for c in p[4]]
    for f in sorted(d.glob("test-libero_fresh-*-rep1.jsonl")):
        import hashlib
        recs = [json.loads(l) for l in open(f) if l.strip()]
        return (hashlib.sha256(json.dumps([r["id"] for r in recs]).encode()).hexdigest()[:16],
                [1 if r["score"] >= 0.5 else 0 for r in recs])
    return None


def run_fresh(root, name):
    base = Path(root) / ("a800/runs2" if name.startswith("a8_") else "baidu")
    return bits_of(base / f"{name}_fresh")


def reference(root, platform, suite):
    base = Path(root) / ("a800/runs2" if platform == "a800" else "baidu")
    evals = [b for k in range(1, 9) for b in [bits_of(base / f"{'a8' if platform == 'a800' else 'yq'}_fresh_n0_{suite}_{k}")] if b]
    return evals


def pct(v):
    return round(100 * sum(v) / len(v), 2)


def paired(pairs, bar, name, need_ci=True):
    a, b = seed_avg([(x, y) for _, x, y in pairs])
    diff = 100 * sum(y - x for x, y in zip(a, b)) / len(a)
    lo, hi = paired_bootstrap(a, b)
    return dict(claim=name, seeds=[s for s, _, _ in pairs], n_episodes=len(a), bar_points=bar, mean_points=round(diff, 2),
                ci95_points=[round(100 * lo, 2), round(100 * hi, 2)],
                passes=None if bar is None else bool(diff >= bar and lo > 0),
                per_seed={s: dict(control=pct(x), arm=pct(y), diff=round(pct(y) - pct(x), 2)) for s, x, y in pairs})


BLOCKS = {
    "spatial_main": dict(suite="spatial", arms=("fixed", "nonrec", "shuffled", "onebig"), seeds=(0, 1, 2, 3),
                         name=lambda arm, s: f"a8_spatmain_{arm}_s0" if s == 0 else f"yq_ofts_{arm}_s{s}",
                         claims=[("F1", "n0", "fixed", 3.0), ("F2", "shuffled", "fixed", 3.0),
                                 ("F3", "nonrec", "fixed", 2.0), ("F5", "onebig", "fixed", 2.0)]),
    "goal_main": dict(suite="goal", arms=("fixed", "nonrec", "shuffled", "onebig"), seeds=(0, 1, 2, 3),
                      name=lambda arm, s: f"a8_goalmain_{arm}_s0" if s == 0 else f"yq_oftg_{arm}_s{s}",
                      claims=[("F1", "n0", "fixed", 3.0), ("F2", "shuffled", "fixed", 3.0),
                              ("F3", "nonrec", "fixed", 2.0), ("F5", "onebig", "fixed", 2.0)]),
    "spatial_repair": dict(suite="spatial", arms=("fixed", "full", "meta3"), seeds=(0, 1, 2, 3),
                           name=lambda arm, s: f"a8_spatrep_{arm}_s0" if s == 0 else f"yq_oftsb_{arm}_s{s}",
                           claims=[("FS1", "fixed", "meta3", 3.0), ("FS2", "full", "meta3", None),
                                   ("meta3_vs_n0", "n0", "meta3", None), ("fixedBC_vs_n0", "n0", "fixed", None)]),
    "spatial_long12": dict(suite="spatial", arms=("fixed12", "nonrec12", "onebig12"), seeds=(1, 2, 3),
                           name=lambda arm, s: f"yq_ofts_{arm}_s{s}",
                           claims=[("FL1", "n0", "fixed12", 5.0), ("FL3", "nonrec12", "fixed12", 2.0),
                                   ("FL5", "onebig12", "fixed12", 2.0)]),
    "goal_long12": dict(suite="goal", arms=("fixed12", "nonrec12", "onebig12"), seeds=(1, 2, 3),
                        name=lambda arm, s: f"yq_oftg_{arm}_s{s}",
                        claims=[("FL1", "n0", "fixed12", 5.0), ("FL3", "nonrec12", "fixed12", 2.0),
                                ("FL5", "onebig12", "fixed12", 2.0)]),
    # addendum 32 (blocks added before any of their runs existed; the blocks above are unchanged)
    "goal_guard12": dict(suite="goal", arms=("guard12", "fixed12", "onebig12"), seeds=(1, 2, 3),
                         name=lambda arm, s: f"yq_oftg_{arm}_s{s}",
                         claims=[("G1", "n0", "guard12", 5.0), ("G2", "fixed12", "guard12", 2.0),
                                 ("G3", "onebig12", "guard12", None)]),
    "goal_nogate": dict(suite="goal", arms=("nogate", "fixed", "llm_harness"), seeds=(1, 2, 3),
                        name=lambda arm, s: f"yq_oftgb_{arm}_s{s}",
                        claims=[("NG1", "nogate", "fixed", 10.0), ("NG2", "nogate", "llm_harness", 10.0),
                                ("NG3", "n0", "nogate", None)]),
}


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    block, root = BLOCKS[args[0]], (args[1] if len(args) > 1 else "results")
    runs = {(arm, s): run_fresh(root, block["name"](arm, s)) for arm in block["arms"] for s in block["seeds"]}
    refs = {p: reference(root, p, block["suite"]) for p in ("yq", "a800")}
    if check:
        for (arm, s), b in sorted(runs.items()):
            print(f"{block['name'](arm, s):30s} fresh evaluation: {'yes, %d episodes' % len(b[1]) if b else 'missing'}")
        print({p: len(v) for p, v in refs.items()}, "reference evaluations")
        return
    digests = {b[0] for b in runs.values() if b} | {e[0] for v in refs.values() for e in v}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    if any(len(b[1]) != N for b in runs.values() if b):
        raise SystemExit("an evaluation does not have 1000 episodes")
    ref = {p: [sum(v) / len(v) for v in zip(*[e[1] for e in evs])] for p, evs in refs.items() if evs}
    plat = lambda s: "a800" if s == 0 else "yq"
    res = dict(block=args[0], reference={p: dict(evaluations=len(refs[p]), success=pct(r)) for p, r in ref.items()})
    for label, ctrl, arm, bar in block["claims"]:
        pairs = []
        for s in block["seeds"]:
            y = runs.get((arm, s))
            x = ref.get(plat(s)) if ctrl == "n0" else (runs.get((ctrl, s)) or [None, None])[1]
            if y and x:
                pairs.append((s, x, y[1]))
        if pairs:
            res[label] = paired(pairs, bar, f"{label} {arm} - {ctrl} (fresh sealed test)")
            res[label]["complete"] = len(pairs) == len(block["seeds"])
        else:
            res[label] = dict(claim=f"{label} {arm} - {ctrl}", missing=True)
    res["noise_reference_halves"] = {}
    for p, evs in refs.items():
        if len(evs) >= 2:
            h = len(evs) // 2
            a = [sum(v) / h for v in zip(*[e[1] for e in evs[:h]])]
            b = [sum(v) / (len(evs) - h) for v in zip(*[e[1] for e in evs[h:]])]
            lo, hi = paired_bootstrap(a, b)
            res["noise_reference_halves"][p] = dict(diff=round(pct(b) - pct(a), 2), ci95=[round(100 * lo, 2), round(100 * hi, 2)])
    res["runs"] = {block["name"](arm, s): (pct(b[1]) if b else None) for (arm, s), b in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

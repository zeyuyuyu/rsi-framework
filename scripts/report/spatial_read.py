"""Prereg v3 addendum 28: the one-time read of the object-level claims on LIBERO-Spatial (R1/R2/R3/R5-spatial).

Runs: Yangquan seeds 1-3 (results/baidu/yq_ofts_<arm>_s<seed>) and cavin seed 0 (results/a800/runs2/
a8_spatmain_<arm>_s0), arms fixed / nonrec / shuffled / onebig. The rule is the Goal one (goal_read.py, whose
functions are reused unchanged): final = per-episode mean of three evaluations of the retained policy, initial
reference = per-episode mean of every in-run n0 test of this checkpoint on the platform, comparisons paired per
episode within a seed, seed-averaged, paired bootstrap CI (10,000 draws). No meta arm exists on Spatial, so the
"best by gate" loop of R5 is `fixed`. R5-ungated uses each onebig run's r01c0 test whatever its gate (a rejected
candidate needs a `--test-eval --node r01c0` job first). `--pooled` adds the descriptive Goal + Spatial pooling
(not a registered claim: Goal was read before these runs existed).
usage: python3 scripts/report/spatial_read.py [results root] [--check] [--mode final] [--pooled] [--json out.json]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G   # noqa: E402
from goal_read import load_scores, mean_bits, noise_check, paired, paired_bootstrap, pct, r1, rep_scores, seed_avg   # noqa: E402

ARMS = ("fixed", "nonrec", "shuffled", "onebig")
BARS = (("R2", "fixed", "shuffled", 3.0), ("R3", "fixed", "nonrec", 2.0), ("R5", "fixed", "onebig", 2.0))


def run_dir(root, platform, arm, seed):
    if platform == "yq":
        return Path(root) / "baidu" / f"yq_ofts_{arm}_s{seed}"
    return Path(root) / "a800" / "runs2" / f"a8_spatmain_{arm}_s{seed}"


def pooled_n0(root, platform, digest):
    """Per-episode mean of every in-run n0 test of the Spatial checkpoint on one platform (replicate and r01c0
    directories hold no n0 test of their own and are skipped by name)."""
    if platform == "yq":
        runs = [p for p in (Path(root) / "baidu").glob("yq_ofts_*")]
    elif platform == "bj":   # addendum 33 amendment 1 (Beijing); the yq and a800 branches are unchanged
        runs = [p for p in (Path(root) / "baidu").glob("bj_ofts_*")]
    else:
        runs = [p for p in (Path(root) / "a800" / "runs2").glob("a8_spatmain_*")]
    lists, names = [], []
    for p in sorted(runs):
        if p.name.endswith(("_rep", "_r01c0")) or not p.is_dir():
            continue
        sc = load_scores(p, G.SUITE)
        if "n0" in sc and sc["n0"][0] == digest:
            lists.append(sc["n0"][1]); names.append(p.name)
    return mean_bits(lists), names


def ungated_onebig(root, platform, seed, rec):
    """Evaluations of onebig's single candidate r01c0: in-run test (if accepted), replicates, <run>_r01c0 jobs."""
    evals = [rec["scores"]["r01c0"][1]] if "r01c0" in rec["scores"] else []
    d = run_dir(root, platform, "onebig", seed)
    if G.MODE == "final":
        evals += rep_scores(d).get("r01c0", [])
    extra = d.parent / f"{d.name}_r01c0"
    if extra.exists():
        sc = load_scores(extra, G.SUITE)
        evals += [sc[k][1] for k in sorted(sc) if k.startswith("r01c0")]
    return evals


def goal_records(root):
    """Final records of the Goal runs with the same four arms (already read on 2026-11-06; descriptive pooling only)."""
    yq = {(a, s): G.record(G.run_dir(root, "yq", a, s)) for a in ARMS for s in (1, 2, 3)}
    s0 = {(a, 0): G.record(G.run_dir(root, "cavin", a, 0)) for a in ARMS}
    return yq, s0


def suite_pairs(yq, s0, arm, ctrl):
    return [(0, s0[(ctrl, 0)]["bits"], s0[(arm, 0)]["bits"])] + [(s, yq[(ctrl, s)]["bits"], yq[(arm, s)]["bits"]) for s in (1, 2, 3)]


def pooled_two_suites(name, pairs_a, pairs_b):
    """Descriptive: seed-averaged per-episode vectors of each suite, concatenated (500 + 500 episodes), one bootstrap."""
    a1, b1 = seed_avg([(x, y) for _, x, y in pairs_a])
    a2, b2 = seed_avg([(x, y) for _, x, y in pairs_b])
    a, b = list(a1) + list(a2), list(b1) + list(b2)
    lo, hi = paired_bootstrap(a, b)
    return dict(claim=name + " (Goal + Spatial pooled, descriptive, no bar)", n_episodes=len(a),
                mean_points=round(100 * sum(y - x for x, y in zip(a, b)) / len(a), 2),
                ci95_points=[round(100 * lo, 2), round(100 * hi, 2)])


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    if "--mode" in args:
        i = args.index("--mode"); G.MODE = args[i + 1]; del args[i:i + 2]
    check, pooled = "--check" in args, "--pooled" in args
    args = [a for a in args if a not in ("--check", "--pooled")]
    root = args[0] if args else "results"

    yq = {(arm, s): G.record(run_dir(root, "yq", arm, s)) for arm in ARMS for s in (1, 2, 3)}
    s0 = {(arm, 0): G.record(run_dir(root, "cavin", arm, 0)) for arm in ARMS}
    digests = {r[k] for d in (yq, s0) for r in d.values() for k in ("digest", "n0_digest")}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    digest = next(iter(digests))
    ref_yq, names_yq = pooled_n0(root, "yq", digest)
    ref_cv, names_cv = pooled_n0(root, "cavin", digest)
    if check:
        print(f"mode={G.MODE} pooled n0 reference: yq {len(names_yq)} evaluations mean {pct(ref_yq)}, "
              f"cavin {len(names_cv)} evaluations mean {pct(ref_cv)} ({', '.join(names_cv)})")
        for d in (yq, s0):
            for (arm, s), r in sorted(d.items()):
                print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                      f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        print("digest", digest)
        return

    res = {"mode": dict(mode=G.MODE, pooled_n0_yq=dict(n=len(names_yq), mean=pct(ref_yq)),
                        pooled_n0_cavin=dict(n=len(names_cv), mean=pct(ref_cv), runs=names_cv))}
    # R1-spatial: Yangquan seeds 1-3 against the Yangquan pooled reference; seed 0 against cavin's, shown alongside
    res["R1_fixed"] = r1({s: yq[("fixed", s)] for s in (1, 2, 3)}, "fixed (Spatial, Yangquan seeds 1-3)",
                         ref=ref_yq if G.MODE == "final" else None)
    res["R1_fixed_seed0_cavin"] = paired([(0, ref_cv if G.MODE == "final" else s0[("fixed", 0)]["n0_bits"], s0[("fixed", 0)]["bits"])],
                                         5.0, "R1 fixed: final - initial (seed 0, cavin; shown alongside, not the registered statistic)")
    for tag, arm, ctrl, bar in BARS:
        p4 = suite_pairs(yq, s0, arm, ctrl)
        res[f"{tag}_seeds0to3"] = paired(p4, bar, f"{tag}-spatial {arm} - {ctrl} (seeds 0-3; seed 0 on cavin)")
        res[f"{tag}_seeds1to3"] = paired(p4[1:], bar, f"{tag}-spatial {arm} - {ctrl} (seeds 1-3, Yangquan)")
    # R5-ungated: onebig's single candidate whatever its gate
    ung, missing = [], []
    for s in (0, 1, 2, 3):
        src, platform = (s0, "cavin") if s == 0 else (yq, "yq")
        evals = ungated_onebig(root, platform, s, src[("onebig", s)])
        if not evals:
            missing.append(s)
        else:
            ung.append((s, mean_bits(evals) if G.MODE == "final" else evals[0], src[("fixed", s)]["bits"]))
    if ung:
        res["R5_ungated"] = paired(ung, 2.0, "R5-spatial ungated: fixed - onebig r01c0 (available seeds)", extra=dict(missing_seeds=missing))
    res["noise_check_n0_halves"] = dict(yq=noise_check({f"{a}_s{s}": r for (a, s), r in yq.items()}),
                                        cavin=noise_check({f"{a}_s{s}": r for (a, s), r in s0.items()}))
    res["runs"] = {d: {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=pct(r["bits"]), n0=pct(r["n0_bits"]),
                                         rounds=r["rounds"], evals=r["n_evals"]) for (a, s), r in sorted(src.items())}
                   for d, src in (("yq", yq), ("cavin_s0", s0))}
    if pooled:
        gyq, gs0 = goal_records(root)
        res["pooled_goal_spatial_descriptive"] = {
            tag: pooled_two_suites(f"{tag} {arm} - {ctrl}", suite_pairs(gyq, gs0, arm, ctrl), suite_pairs(yq, s0, arm, ctrl))
            for tag, arm, ctrl, _ in BARS}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

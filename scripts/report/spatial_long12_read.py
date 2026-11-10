"""Addendum 30, part B: the one-time official-test read of the 12-round study on LIBERO-Spatial.

Arms: yq_ofts_fixed12_s{1,2,3} (12 rounds x 3 inner steps, recursive), yq_ofts_nonrec12_s{1,2,3} (practice from the
frozen initial policy) and, if they were run, yq_ofts_onebig12_s{1,2,3} (1 round x 36 inner steps). Finals follow the
registered rule: per-episode mean of three evaluations of the retained policy. Seed-averaged per-episode paired
bootstrap, Yangquan seeds 1-3. Reference: per-episode mean of every in-run n0 test of the Spatial checkpoint on
Yangquan (spatial_read.pooled_n0).

Bars: R3-long-spatial fixed12 - nonrec12 >= +2.0, CI > 0 (primary); R1-long-spatial fixed12 - reference >= +5.0,
CI > 0, >= 2 of 3 seeds > 0; R5-long-spatial fixed12 - onebig12 >= +2.0, CI > 0, only if onebig12 was run; fixed12 and
nonrec12 against their 6-round runs of the same seeds, descriptive.

usage: python3 scripts/report/spatial_long12_read.py [results root] [--check] [--json out.json]
--check prints readiness (retained node, gate, rounds, evaluation counts) and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import spatial_read as S     # noqa: E402

SEEDS = (1, 2, 3)


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    G.MODE = "final"
    d = lambda arm, s: Path(root) / "baidu" / f"yq_ofts_{arm}_s{s}"
    arms = ["fixed12", "nonrec12"] + (["onebig12"] if all(d("onebig12", s).exists() for s in SEEDS) else [])
    runs = {(arm, s): G.record(d(arm, s)) for arm in arms for s in SEEDS}
    six = {(arm, s): G.record(d(arm, s)) for arm in ("fixed", "nonrec") for s in SEEDS}
    digests = {r["digest"] for r in list(runs.values()) + list(six.values())} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for (arm, s), r in runs.items():
        want = 1 if arm == "onebig12" else 12
        if r["rounds"] != want:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected {want}")
    ref, names = S.pooled_n0(root, "yq", next(iter(digests)))
    if check:
        print(f"arms {arms}; pooled n0 reference: yq {len(names)} evaluations (mean withheld in --check)")
        for (arm, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                  f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        return
    res = {"mode": dict(mode="final", arms=arms, pooled_n0_yq=dict(n=len(names), mean=G.pct(ref)))}
    pair = lambda ctrl, arm: [(s, ctrl[s]["bits"], arm[s]["bits"]) for s in SEEDS]
    by = lambda arm: {s: runs[(arm, s)] for s in SEEDS}
    res["R3_long_spatial"] = G.paired(pair(by("nonrec12"), by("fixed12")), 2.0, "R3-long-spatial fixed12 - nonrec12 (Yangquan, seeds 1-3)")
    res["R1_long_spatial"] = G.r1(by("fixed12"), "fixed12", ref=ref)
    res["R1_long_spatial"]["claim"] = "R1-long-spatial fixed12: final - pooled initial reference"
    if "onebig12" in arms:
        res["R5_long_spatial"] = G.paired(pair(by("onebig12"), by("fixed12")), 2.0, "R5-long-spatial fixed12 - onebig12 (Yangquan, seeds 1-3)")
    else:
        res["R5_long_spatial"] = dict(claim="R5-long-spatial", not_tested="onebig12 was not run (addendum 30, part B)")
    res["fixed12_minus_fixed6"] = G.paired([(s, six[("fixed", s)]["bits"], runs[("fixed12", s)]["bits"]) for s in SEEDS], 0.0,
                                           "descriptive: fixed12 - fixed (6-round finals, same seeds, no bar)")
    res["nonrec12_minus_nonrec6"] = G.paired([(s, six[("nonrec", s)]["bits"], runs[("nonrec12", s)]["bits"]) for s in SEEDS], 0.0,
                                             "descriptive: nonrec12 - nonrec (6-round finals, same seeds, no bar)")
    res["noise_check_n0_halves"] = G.noise_check({f"{a}_s{s}": r for (a, s), r in runs.items()})
    res["runs"] = {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                     rounds=r["rounds"], evals=r["n_evals"],
                                     accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc}))
                   for (a, s), r in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

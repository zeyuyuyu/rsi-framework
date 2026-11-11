"""Addendum 33: the one-time official-test read of the guard-rail gate on the 6-round LIBERO-Spatial loop. Finals
follow the registered rule (per-episode mean of three evaluations of the retained policy); seed-averaged per-episode
paired bootstrap, 10,000 draws. Reference: the pooled in-run n0 tests of the Spatial checkpoint on the platform
(spatial_read.pooled_n0). Every pair is formed within a platform.

Yangquan (Y), seeds 1-3: yq_ofts_guard_s<seed> against addendum 28's yq_ofts_onebig_s<seed> (one round, 18 steps,
the whole budget: plain RL) and yq_ofts_fixed_s<seed> (strict gate), both read 2026-11-11.
Beijing (B, amendment 1), seeds 1-3: bj_ofts_guard_s<seed> against bj_ofts_onebig_s<seed>. No strict-gate arm.
  GS3  guard - onebig: superiority if the CI lower bound > 0; non-inferiority (margin 2 points) if it is > -2.
       Primary: the six within-platform pairs (Y1-3, B1-3) when every Beijing final exists; otherwise Yangquan
       alone. --yq-primary forces Yangquan alone (Beijing complete only after 2026-11-15 12:00Z). The
       per-platform estimates are reported either way.
  GS2  guard - fixed >= +2.0, CI > 0 (Yangquan only)
  GS1  guard - reference, R1 rule (>= +5.0, CI > 0, >= 2 of 3 seeds > 0), per platform against its own reference
usage: python3 scripts/report/spatial_guard_read.py [results root] [--check] [--yq-primary] [--json out.json]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402
import spatial_read as SR                              # noqa: E402

SEEDS = (1, 2, 3)
PLATS = dict(Y=("yq", dict(new="yq_ofts_guard", rl="yq_ofts_onebig", strict="yq_ofts_fixed")),
             B=("bj", dict(new="bj_ofts_guard", rl="bj_ofts_onebig")))


def gs3(pairs, label):
    o = G.paired(pairs, 0.0, label)
    o["superior"] = bool(o["ci95_points"][0] > 0.0)
    o["non_inferior_margin_2"] = bool(o["ci95_points"][0] > -2.0)
    o.pop("passes", None)
    return o


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    yq_primary = "--yq-primary" in args
    args = [a for a in args if a not in ("--check", "--yq-primary")]
    root = args[0] if args else "results"
    G.MODE = "final"
    runs, missing = {}, {}
    for P, (_, names) in PLATS.items():
        for k, n in names.items():
            for s in SEEDS:
                try:
                    runs[(P, k, s)] = G.record(Path(root) / "baidu" / f"{n}_s{s}")
                except SystemExit as e:   # not finished, or fewer than three final evaluations
                    missing[(P, k, s)] = str(e)
    y_missing = [v for (P, _, _), v in missing.items() if P == "Y"]
    b_complete = not any(P == "B" for P, _, _ in missing)
    if y_missing and not check:
        raise SystemExit("Yangquan not complete:\n" + "\n".join(y_missing))
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) > 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for (P, k, s), r in runs.items():
        if k == "new" and r["rounds"] != 6:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected 6")
    digest = next(iter(digests)) if digests else None
    refs = {P: SR.pooled_n0(root, plat, digest) for P, (plat, _) in PLATS.items()}
    if check:
        for P, (plat, _) in PLATS.items():
            print(f"pooled n0 reference: {plat} {len(refs[P][1])} evaluations (mean withheld in --check)")
        for (P, k, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']}")
        for (P, k, s), m in sorted(missing.items()):
            print(f"{PLATS[P][1][k]}_s{s:<17d} not ready: {m.splitlines()[0]}")
        print(f"Beijing complete: {b_complete}; GS3 primary would be {'pooled Y+B' if b_complete and not yq_primary else 'Yangquan alone'}")
        return
    pair = lambda P, ctrl, arm: [(f"{P}{s}", runs[(P, ctrl, s)]["bits"], runs[(P, arm, s)]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", **{f"pooled_n0_{PLATS[P][0]}": dict(n=len(refs[P][1]), mean=G.pct(refs[P][0]))
                                         for P in PLATS if refs[P][1]})}
    res["GS3_yq"] = gs3(pair("Y", "rl", "new"), "GS3 guard - onebig (plain RL at equal compute), Yangquan; official test")
    if b_complete:
        res["GS3_bj"] = gs3(pair("B", "rl", "new"), "GS3 guard - onebig, Beijing; official test")
        res["GS3_pooled"] = gs3(pair("Y", "rl", "new") + pair("B", "rl", "new"),
                                "GS3 guard - onebig, within-platform pairs Y1-3 + B1-3; official test")
    else:
        res["bj_not_ready"] = sorted(f"{PLATS[P][1][k]}_s{s}" for (P, k, s) in missing if P == "B")
    primary = "GS3_pooled" if b_complete and not yq_primary else "GS3_yq"
    res["GS3"] = dict(res[primary], primary_source=primary)
    res["GS2"] = G.paired(pair("Y", "strict", "new"), 2.0, "GS2 guard - fixed (strict gate), Yangquan; official test")
    for P in PLATS:
        recs = {s: runs[(P, "new", s)] for s in SEEDS if (P, "new", s) in runs}
        if len(recs) == len(SEEDS):
            key = "GS1" if P == "Y" else "GS1_bj"
            res[key] = G.r1(recs, f"guard (Spatial, {PLATS[P][0]})", ref=refs[P][0])
            res[key]["claim"] = f"{key} guard: final - pooled initial reference, {PLATS[P][0]} (official test)"
    res["runs"] = {r["run"]: dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                  rounds=r["rounds"], evals=r["n_evals"],
                                  accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc}))
                   for _, r in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

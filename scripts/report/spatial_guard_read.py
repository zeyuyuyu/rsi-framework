"""Addendum 33: the one-time official-test read of the guard-rail gate on the 6-round LIBERO-Spatial loop. Finals
follow the registered rule (per-episode mean of three evaluations of the retained policy); seed-averaged per-episode
paired bootstrap, 10,000 draws. Reference: the pooled in-run n0 tests of the Spatial checkpoint on the platform
(spatial_read.pooled_n0). Every pair is formed within a platform.

Platforms and runs (guard against plain RL "onebig" and against the strict gate "fixed"):
  Y  Yangquan, seeds 1-3:    yq_ofts_guard_s<seed>  vs yq_ofts_onebig_s<seed>, yq_ofts_fixed_s<seed> (read 2026-11-11)
  A  A800 node, seed 0 (amendment 2): a8_spatmain_guard_s0 vs a8_spatmain_onebig_s0, a8_spatmain_fixed_s0 (read 11-11)
  B  Beijing, seeds 1-3 (amendment 1): bj_ofts_guard_s<seed> vs bj_ofts_onebig_s<seed> (no strict-gate arm)
  GS3  guard - onebig: superiority if the CI lower bound > 0; non-inferiority (margin 2 points) if it is > -2.
       Primary: every complete within-platform pair (Y, plus A and B when complete). --exclude A,B drops a platform
       that is not complete by 2026-11-15 12:00Z; --yq-primary is --exclude A,B. Per-platform estimates either way.
  GS2  guard - fixed >= +2.0, CI > 0, on Y (+ A)
  GS1  guard - reference per platform: R1 rule on Y and B (>= +5.0, CI > 0, >= 2 of 3 seeds > 0); on A (one seed)
       the same difference, descriptive
usage: python3 scripts/report/spatial_guard_read.py [results root] [--check] [--exclude A,B] [--yq-primary] [--json out]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402
import spatial_read as SR                              # noqa: E402

PLATS = dict(Y=dict(plat="yq", sub="baidu", seeds=(1, 2, 3),
                    names=dict(new="yq_ofts_guard", rl="yq_ofts_onebig", strict="yq_ofts_fixed")),
             A=dict(plat="a800", sub="a800/runs2", seeds=(0,),
                    names=dict(new="a8_spatmain_guard", rl="a8_spatmain_onebig", strict="a8_spatmain_fixed")),
             B=dict(plat="bj", sub="baidu", seeds=(1, 2, 3), names=dict(new="bj_ofts_guard", rl="bj_ofts_onebig")))


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
    excl = set()
    if "--exclude" in args:
        i = args.index("--exclude"); excl = set(args[i + 1].split(",")); del args[i:i + 2]
    if "--yq-primary" in args:
        excl |= {"A", "B"}
    check = "--check" in args
    args = [a for a in args if a not in ("--check", "--yq-primary")]
    root = args[0] if args else "results"
    G.MODE = "final"
    runs, missing = {}, {}
    for P, spec in PLATS.items():
        for k, n in spec["names"].items():
            for s in spec["seeds"]:
                try:
                    runs[(P, k, s)] = G.record(Path(root) / spec["sub"] / f"{n}_s{s}")
                except SystemExit as e:   # not finished, or fewer than three final evaluations
                    missing[(P, k, s)] = str(e)
    if any(P == "Y" for P, _, _ in missing) and not check:
        raise SystemExit("Yangquan not complete:\n" + "\n".join(v for (P, _, _), v in missing.items() if P == "Y"))
    complete = {P: not any(m[0] == P for m in missing) for P in PLATS}
    used = [P for P in PLATS if complete[P] and P not in excl]          # Y is always complete outside --check
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) > 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for (P, k, s), r in runs.items():
        if k == "new" and r["rounds"] != 6:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected 6")
    digest = next(iter(digests)) if digests else None
    refs = {P: SR.pooled_n0(root, spec["plat"], digest) for P, spec in PLATS.items()}
    if check:
        for P, spec in PLATS.items():
            print(f"pooled n0 reference: {spec['plat']} {len(refs[P][1])} evaluations (mean withheld in --check)")
        for (P, k, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']}")
        for (P, k, s), m in sorted(missing.items()):
            print(f"{PLATS[P]['names'][k]}_s{s:<17d} not ready: {m.splitlines()[0]}")
        print(f"complete: {complete}; excluded: {sorted(excl)}; GS3 primary would pool {used}")
        return
    pair = lambda P, ctrl, arm: [(f"{P}{s}", runs[(P, ctrl, s)]["bits"], runs[(P, arm, s)]["bits"]) for s in PLATS[P]["seeds"]]
    res = {"mode": dict(mode="final", **{f"pooled_n0_{PLATS[P]['plat']}": dict(n=len(refs[P][1]), mean=G.pct(refs[P][0]))
                                         for P in PLATS if refs[P][1]}),
           "platforms_pooled": used, "excluded": sorted(excl), "complete": complete}
    for P in PLATS:
        if complete[P]:
            res[f"GS3_{PLATS[P]['plat']}"] = gs3(pair(P, "rl", "new"), f"GS3 guard - onebig, platform {P}; official test")
    res["GS3"] = gs3([p for P in used for p in pair(P, "rl", "new")],
                     f"GS3 guard - onebig (plain RL at equal compute), within-platform pairs {'+'.join(used)}; official test")
    strict = [P for P in used if "strict" in PLATS[P]["names"]]
    res["GS2"] = G.paired([p for P in strict for p in pair(P, "strict", "new")], 2.0,
                          f"GS2 guard - fixed (strict gate), within-platform pairs {'+'.join(strict)}; official test")
    for P in PLATS:
        recs = {s: runs[(P, "new", s)] for s in PLATS[P]["seeds"] if (P, "new", s) in runs}
        if len(recs) != len(PLATS[P]["seeds"]):
            continue
        key = "GS1" if P == "Y" else f"GS1_{PLATS[P]['plat']}"
        if len(recs) >= 3:
            res[key] = G.r1(recs, f"guard (Spatial, {PLATS[P]['plat']})", ref=refs[P][0])
        else:   # one seed: the R1 seed-count rule cannot apply, so the difference is descriptive
            res[key] = G.paired([(f"{P}{s}", refs[P][0], r["bits"]) for s, r in recs.items()], 5.0, "")
            res[key]["descriptive_one_seed"] = True
        res[key]["claim"] = f"{key} guard: final - pooled initial reference, {PLATS[P]['plat']} (official test)"
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

"""Addendum 33: the one-time official-test read of the guard-rail gate on the 6-round LIBERO-Spatial loop. Finals
follow the registered rule (per-episode mean of three evaluations of the retained policy); seed-averaged per-episode
paired bootstrap, 10,000 draws. Reference: the pooled in-run n0 tests of the Spatial checkpoint on the platform
(spatial_read.pooled_n0). Every pair is formed within a platform; a pair is a platform letter + seed ("Y1", "A0").

Pairs (guard against plain RL "onebig"; against the strict gate "fixed" where that arm exists):
  Y1-3  Yangquan:  yq_ofts_guard_s<seed>   vs yq_ofts_onebig_s<seed>, yq_ofts_fixed_s<seed> (read 2026-11-11)
  A0    A800 node (amendment 2): a8_spatmain_guard_s0 vs a8_spatmain_onebig_s0, a8_spatmain_fixed_s0 (read 11-11)
  A1    A800 node (amendment 3): a8_spatmain_guard_s1 vs a8_spatmain_onebig_s1 (both v32; no strict-gate arm)
  B1-3  Beijing (amendment 1): bj_ofts_guard_s<seed> vs bj_ofts_onebig_s<seed> (no strict-gate arm)
  GS3  guard - onebig: superiority if the CI lower bound > 0; non-inferiority (margin 2 points) if it is > -2.
       Primary: every complete pair (Y always; A and B pairs when complete by 2026-11-15 12:00Z). --exclude takes
       platform letters or pair labels (A,B or A1); --yq-primary is --exclude A,B. Per-platform estimates either way.
  GS2  guard - fixed >= +2.0, CI > 0, on Y1-3 (+ A0)
  GS1  guard - reference per platform: R1 rule on Y and B (>= +5.0, CI > 0, >= 2 of 3 seeds > 0); on A the same
       difference, descriptive
usage: python3 scripts/report/spatial_guard_read.py [results root] [--check] [--exclude A,B|A1] [--yq-primary] [--json out]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402
import spatial_read as SR                              # noqa: E402

PLAT = {"Y": "yq", "A": "a800", "B": "bj"}
SUB = {"Y": "baidu", "A": "a800/runs2", "B": "baidu"}
NAMES = {"Y": dict(new="yq_ofts_guard", rl="yq_ofts_onebig", strict="yq_ofts_fixed"),
         "A": dict(new="a8_spatmain_guard", rl="a8_spatmain_onebig", strict="a8_spatmain_fixed"),
         "B": dict(new="bj_ofts_guard", rl="bj_ofts_onebig")}
PAIRS = [("Y", 1), ("Y", 2), ("Y", 3), ("A", 0), ("A", 1), ("B", 1), ("B", 2), ("B", 3)]
STRICT = {("Y", 1), ("Y", 2), ("Y", 3), ("A", 0)}       # pairs that have a strict-gate arm


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
    for P, s in PAIRS:
        for k, n in NAMES[P].items():
            if k == "strict" and (P, s) not in STRICT:
                continue
            try:
                runs[(P, k, s)] = G.record(Path(root) / SUB[P] / f"{n}_s{s}")
            except SystemExit as e:   # not finished, or fewer than three final evaluations
                missing[(P, k, s)] = str(e)
    if any(P == "Y" for P, _, _ in missing) and not check:
        raise SystemExit("Yangquan not complete:\n" + "\n".join(v for (P, _, _), v in missing.items() if P == "Y"))
    label = lambda P, s: f"{P}{s}"
    complete = {label(P, s): (P, "new", s) in runs and (P, "rl", s) in runs for P, s in PAIRS}
    used = [(P, s) for P, s in PAIRS if complete[label(P, s)] and P not in excl and label(P, s) not in excl]
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) > 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for (P, k, s), r in runs.items():
        if k == "new" and r["rounds"] != 6:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected 6")
    digest = next(iter(digests)) if digests else None
    refs = {P: SR.pooled_n0(root, PLAT[P], digest) for P in PLAT}
    if check:
        for P in PLAT:
            print(f"pooled n0 reference: {PLAT[P]} {len(refs[P][1])} evaluations (mean withheld in --check)")
        for (P, k, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']}")
        for (P, k, s), m in sorted(missing.items()):
            print(f"{NAMES[P][k]}_s{s:<17d} not ready: {m.splitlines()[0]}")
        print(f"complete pairs: {[k for k, v in complete.items() if v]}; excluded: {sorted(excl)}; "
              f"GS3 primary would pool {[label(*u) for u in used]}")
        return
    pair = lambda P, s, ctrl: (label(P, s), runs[(P, ctrl, s)]["bits"], runs[(P, "new", s)]["bits"])
    res = {"mode": dict(mode="final", **{f"pooled_n0_{PLAT[P]}": dict(n=len(refs[P][1]), mean=G.pct(refs[P][0]))
                                         for P in PLAT if refs[P][1]}),
           "pairs_pooled": [label(*u) for u in used], "excluded": sorted(excl), "complete": complete}
    for P in PLAT:
        mine = [u for u in used if u[0] == P]
        if mine:
            res[f"GS3_{PLAT[P]}"] = gs3([pair(*u, "rl") for u in mine], f"GS3 guard - onebig, platform {P}; official test")
    res["GS3"] = gs3([pair(*u, "rl") for u in used],
                     f"GS3 guard - onebig (plain RL at equal compute), pairs {'+'.join(label(*u) for u in used)}; official test")
    strict = [u for u in used if u in STRICT and (u[0], "strict", u[1]) in runs]
    res["GS2"] = G.paired([pair(*u, "strict") for u in strict], 2.0,
                          f"GS2 guard - fixed (strict gate), pairs {'+'.join(label(*u) for u in strict)}; official test")
    for P in PLAT:
        recs = {s: runs[(P, "new", s)] for p, s in PAIRS if p == P and (P, "new", s) in runs
                and P not in excl and label(P, s) not in excl}
        if not recs:
            continue
        key = "GS1" if P == "Y" else f"GS1_{PLAT[P]}"
        if P in ("Y", "B"):
            if len(recs) < 3:
                continue
            res[key] = G.r1(recs, f"guard (Spatial, {PLAT[P]})", ref=refs[P][0])
        else:   # one or two seeds: the R1 seed-count rule cannot apply, so the difference is descriptive
            res[key] = G.paired([(label(P, s), refs[P][0], r["bits"]) for s, r in sorted(recs.items())], 5.0, "")
            res[key]["descriptive"] = True
        res[key]["claim"] = f"{key} guard: final - pooled initial reference, {PLAT[P]} (official test)"
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

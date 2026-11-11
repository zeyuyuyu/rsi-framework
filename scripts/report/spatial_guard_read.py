"""Addendum 33: the one-time official-test read of the guard-rail gate on the 6-round LIBERO-Spatial loop. Yangquan,
seeds 1-3. Finals follow the registered rule (per-episode mean of three evaluations of the retained policy);
seed-averaged per-episode paired bootstrap, 10,000 draws. Reference: the pooled in-run n0 tests of the Spatial
checkpoint on Yangquan (spatial_read.pooled_n0).

yq_ofts_guard_s<seed> against addendum 28's yq_ofts_onebig_s<seed> (one round, 18 steps, the whole budget: plain RL)
and yq_ofts_fixed_s<seed> (strict gate), both read 2026-11-11.
  GS3  guard - onebig: superiority if the CI lower bound > 0; non-inferiority (margin 2 points) if it is > -2
  GS2  guard - fixed >= +2.0, CI > 0
  GS1  guard - reference, R1 rule (>= +5.0, CI > 0, >= 2 of 3 seeds > 0)
usage: python3 scripts/report/spatial_guard_read.py [results root] [--check] [--json out.json]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402
import spatial_read as SR                              # noqa: E402

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
    d = lambda name, s: Path(root) / "baidu" / f"{name}_s{s}"
    names = dict(new="yq_ofts_guard", rl="yq_ofts_onebig", strict="yq_ofts_fixed")
    runs = {(k, s): G.record(d(n, s)) for k, n in names.items() for s in SEEDS}
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for s in SEEDS:
        r = runs[("new", s)]
        if r["rounds"] != 6:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected 6")
    ref, ref_names = SR.pooled_n0(root, "yq", next(iter(digests)))
    if check:
        print(f"pooled n0 reference: yq {len(ref_names)} evaluations (mean withheld in --check)")
        for (k, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']}")
        return
    by = lambda k: {s: runs[(k, s)] for s in SEEDS}
    pair = lambda ctrl, arm: [(s, by(ctrl)[s]["bits"], by(arm)[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", pooled_n0_yq=dict(n=len(ref_names), mean=G.pct(ref)))}
    res["GS3"] = G.paired(pair("rl", "new"), 0.0, "GS3 guard - onebig (plain RL at equal compute; official test)")
    res["GS3"]["superior"] = bool(res["GS3"]["ci95_points"][0] > 0.0)
    res["GS3"]["non_inferior_margin_2"] = bool(res["GS3"]["ci95_points"][0] > -2.0)
    res["GS3"].pop("passes", None)
    res["GS2"] = G.paired(pair("strict", "new"), 2.0, "GS2 guard - fixed (strict gate; official test)")
    res["GS1"] = G.r1(by("new"), "guard (Spatial)", ref=ref)
    res["GS1"]["claim"] = "GS1 guard: final - pooled initial reference (official test)"
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

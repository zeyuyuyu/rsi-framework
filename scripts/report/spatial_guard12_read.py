"""Addendum 34 amendment 1: the official-test read of the 12-round Spatial guard-rail loop on Yangquan, seeds 1-3
(the fresh-scene test, read by fresh_read.py spatial_guard12, is primary). Finals = per-episode mean of three
evaluations of the retained policy; reference = pooled in-run n0 tests of the Spatial checkpoint on Yangquan.
  G2s  guard12 - fixed12 >= +2, CI > 0
  G1s  guard12 - reference, R1 rule (>= +5, CI > 0, >= 2 of 3 seeds > 0)
  G3s  guard12 - onebig12: CI reported; non-inferior if the lower bound > -2
usage: python3 scripts/report/spatial_guard12_read.py [results root] [--check] [--json out.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import spatial_read as SR    # noqa: E402

SEEDS = (1, 2, 3)
ARMS = ("guard12", "fixed12", "onebig12")


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    G.MODE = "final"
    runs, missing = {}, {}
    for arm in ARMS:
        for s in SEEDS:
            try:
                runs[(arm, s)] = G.record(Path(root) / "baidu" / f"yq_ofts_{arm}_s{s}")
            except SystemExit as e:
                missing[(arm, s)] = str(e).splitlines()[0]
    if check:
        for (arm, s), r in sorted(runs.items()):
            print(f"{r['run']:26s} retained={r['retained']:6s} rounds={r['rounds']} evals={r['n_evals']}")
        for k, m in sorted(missing.items()):
            print(f"yq_ofts_{k[0]}_s{k[1]} not ready: {m}")
        return
    if missing:
        raise SystemExit("not complete: " + "; ".join(missing.values()))
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    ref, names = SR.pooled_n0(root, "yq", next(iter(digests)))
    by = lambda arm: {s: runs[(arm, s)] for s in SEEDS}
    pair = lambda ctrl, arm: [(s, by(ctrl)[s]["bits"], by(arm)[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", pooled_n0_yq=dict(n=len(names), mean=G.pct(ref)))}
    res["G2s"] = G.paired(pair("fixed12", "guard12"), 2.0, "G2s guard12 - fixed12 (official test)")
    res["G1s"] = G.r1(by("guard12"), "guard12 (Spatial)", ref=ref)
    res["G1s"]["claim"] = "G1s guard12: final - pooled initial reference (official test)"
    res["G3s"] = G.paired(pair("onebig12", "guard12"), 0.0, "G3s guard12 - onebig12 (official test; non-inferiority margin 2)")
    res["G3s"]["non_inferior"] = bool(res["G3s"]["ci95_points"][0] > -2.0)
    res["G3s"].pop("passes", None)
    res["runs"] = {r["run"]: dict(retained=r["retained"], test=G.pct(r["bits"]), rounds=r["rounds"], evals=r["n_evals"],
                                  accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc})) for r in runs.values()}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

"""Addendum 34 (descriptive, one seed): the official-test read of the 12-round Spatial runs on the A800 node.
a8_spatmain_{fixed12, nonrec12, onebig12, guard12}_s0; finals = per-episode mean of three evaluations of the retained
policy; reference = pooled in-run n0 tests on the A800 node (spatial_read.pooled_n0). No bar (one seed).
  FL5_A0  fixed12 - onebig12      G3s guard12 - onebig12      G2s guard12 - fixed12      G1s guard12 - reference
usage: python3 scripts/report/spatial_long12_a8_read.py [results root] [--check] [--json out.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import spatial_read as SR    # noqa: E402

ARMS = ("fixed12", "nonrec12", "onebig12", "guard12")


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
        try:
            runs[arm] = G.record(Path(root) / "a800" / "runs2" / f"a8_spatmain_{arm}_s0")
        except SystemExit as e:
            missing[arm] = str(e).splitlines()[0]
    if check:
        for arm, r in runs.items():
            print(f"{r['run']:28s} retained={r['retained']:6s} rounds={r['rounds']} evals={r['n_evals']}")
        for arm, m in missing.items():
            print(f"a8_spatmain_{arm}_s0 not ready: {m}")
        return
    if missing:
        raise SystemExit("not complete: " + "; ".join(missing.values()))
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    ref, names = SR.pooled_n0(root, "a800", next(iter(digests)))
    pair = lambda ctrl, arm: [(0, runs[ctrl]["bits"], runs[arm]["bits"])]
    res = {"note": "addendum 34, descriptive, one seed (A800 node); official test", "pooled_n0_a800": dict(n=len(names), mean=G.pct(ref))}
    for key, ctrl, arm in (("FL5_A0", "onebig12", "fixed12"), ("G3s", "onebig12", "guard12"), ("G2s", "fixed12", "guard12")):
        res[key] = G.paired(pair(ctrl, arm), 0.0, f"{key} {arm} - {ctrl} (official test, seed 0)")
        res[key].pop("passes", None)
    res["G1s"] = G.paired([(0, ref, runs["guard12"]["bits"])], 0.0, "G1s guard12 - pooled initial reference (official test, seed 0)")
    res["G1s"].pop("passes", None)
    res["runs"] = {r["run"]: dict(retained=r["retained"], test=G.pct(r["bits"]), rounds=r["rounds"], evals=r["n_evals"],
                                  accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc})) for r in runs.values()}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

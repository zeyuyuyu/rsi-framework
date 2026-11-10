"""Addendum 31: the framework against plain training on LIBERO-Spatial, from the BC recipe that needs it.

Three ways to spend the same recipe and (per candidate) the same compute, Yangquan seeds 1-3:
  nogate  yq_oftsb_nogate_s<seed>   plain training: every round's child is kept, the last one is the result
  fixed   yq_oftsb_fixed_s<seed>    the framework's gate, nothing else (addendum 29)
  meta3   yq_oftsb_meta3_s<seed>    gate + meta level v3 (addendum 29)
Finals follow the registered rule (per-episode mean of three evaluations of the retained policy; the retained policy
of `nogate` is its last round's child). Seed-averaged per-episode paired bootstrap; reference = pooled in-run n0.

Bars (official test): N1 fixed - nogate >= +10, CI > 0; N2 meta3 - nogate >= +10, CI > 0; N3 nogate - reference,
reported with CI (prediction: far below 0). The same three on the sealed fresh-scene test are read by
fresh_read.py-style pairing here when <run>_fresh evaluations exist (reported, same bars).
usage: python3 scripts/report/spatial_nogate_read.py [results root] [--check] [--json out.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import spatial_read as S     # noqa: E402
import fresh_read as F       # noqa: E402

SEEDS = (1, 2, 3)
ARMS = ("nogate", "fixed", "meta3")


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    G.MODE = "final"
    d = lambda arm, s: Path(root) / "baidu" / f"yq_oftsb_{arm}_s{s}"
    runs = {(arm, s): G.record(d(arm, s)) for arm in ARMS for s in SEEDS}
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for s in SEEDS:
        r = runs[("nogate", s)]
        if r["rounds"] != 6 or r["retained"] != "r06c0":
            raise SystemExit(f"{r['run']}: plain training must end on r06c0, got {r['retained']} after {r['rounds']} rounds")
    ref, names = S.pooled_n0(root, "yq", next(iter(digests)))
    if check:
        for (arm, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']} "
                  f"fresh={'yes' if F.run_fresh(root, r['run']) else 'no'}")
        return
    by = lambda arm: {s: runs[(arm, s)] for s in SEEDS}
    pair = lambda ctrl, arm: [(s, by(ctrl)[s]["bits"], by(arm)[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", pooled_n0_yq=dict(n=len(names), mean=G.pct(ref)))}
    res["N1"] = G.paired(pair("nogate", "fixed"), 10.0, "N1 gate only - plain training (official test)")
    res["N2"] = G.paired(pair("nogate", "meta3"), 10.0, "N2 gate + meta level v3 - plain training (official test)")
    res["N3"] = G.r1(by("nogate"), "nogate", ref=ref)
    res["N3"]["claim"] = "N3 plain training: final - pooled initial reference (no bar)"
    fresh = {(arm, s): F.run_fresh(root, f"yq_oftsb_{arm}_s{s}") for arm in ARMS for s in SEEDS}
    if all(fresh.values()):
        fp = lambda ctrl, arm: [(s, fresh[(ctrl, s)][1], fresh[(arm, s)][1]) for s in SEEDS]
        res["N1_fresh"] = F.paired(fp("nogate", "fixed"), 10.0, "N1 gate only - plain training (fresh sealed test)")
        res["N2_fresh"] = F.paired(fp("nogate", "meta3"), 10.0, "N2 gate + meta level v3 - plain training (fresh sealed test)")
    else:
        res["fresh"] = "not all fresh evaluations exist"
    res["runs"] = {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                     evals=r["n_evals"]) for (a, s), r in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

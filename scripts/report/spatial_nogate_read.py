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
Amendment 1: the four-seed statistic with seed 0 on the A800 node (a8_spatrep_<arm>_s0) is reported alongside, every
pair within its platform; the claims stay on seeds 1-3.
Amendment 2: the read is split. --part A reads N1 and N3 (nogate + fixed only; meta3 is not loaded), --part B reads
N2 (needs meta3). Without --part, both (the original single read).
usage: python3 scripts/report/spatial_nogate_read.py [results root] [--part A|B] [--check] [--json out.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import spatial_read as S     # noqa: E402
import fresh_read as F       # noqa: E402

SEEDS = (1, 2, 3)
PARTS = {"A": ("nogate", "fixed"), "B": ("nogate", "meta3"), None: ("nogate", "fixed", "meta3")}


def main():
    args = sys.argv[1:]
    out = part = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    if "--part" in args:
        i = args.index("--part"); part = args[i + 1]; del args[i:i + 2]
        if part not in ("A", "B"):
            raise SystemExit("--part A or B")
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    arms = PARTS[part]
    G.MODE = "final"
    d = lambda arm, s: Path(root) / "baidu" / f"yq_oftsb_{arm}_s{s}"
    runs = {(arm, s): G.record(d(arm, s)) for arm in arms for s in SEEDS}
    a8 = {}
    for arm in arms:   # amendment 1: seed 0 on the A800 node, reported alongside when complete
        try:
            a8[arm] = G.record(Path(root) / "a800" / "runs2" / f"a8_spatrep_{arm}_s0")
        except SystemExit:
            pass
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()} | \
              {r["digest"] for r in a8.values()} | {r["n0_digest"] for r in a8.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for s in SEEDS:
        r = runs[("nogate", s)]
        if r["rounds"] != 6 or r["retained"] != "r06c0":
            raise SystemExit(f"{r['run']}: plain training must end on r06c0, got {r['retained']} after {r['rounds']} rounds")
    if "nogate" in a8 and a8["nogate"]["retained"] != "r06c0":
        raise SystemExit(f"a8_spatrep_nogate_s0: plain training must end on r06c0, got {a8['nogate']['retained']}")
    ref, names = S.pooled_n0(root, "yq", next(iter(digests)))
    ref_a8, names_a8 = S.pooled_n0(root, "a800", next(iter(digests)))
    fresh = {(arm, s): F.run_fresh(root, f"yq_oftsb_{arm}_s{s}") for arm in arms for s in SEEDS}
    fresh_a8 = {arm: F.run_fresh(root, f"a8_spatrep_{arm}_s0") for arm in arms}
    if check:
        for (arm, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']} "
                  f"fresh={'yes' if fresh[(arm, s)] else 'no'}")
        for arm, r in sorted(a8.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} evals={r['n_evals']} fresh={'yes' if fresh_a8[arm] else 'no'} (seed 0, alongside)")
        print(f"part {part or 'A+B'}: yq fresh complete={all(fresh.values())}; seed-0 arms complete: {sorted(a8)}")
        return
    by = lambda arm: {s: runs[(arm, s)] for s in SEEDS}
    pair = lambda ctrl, arm: [(s, by(ctrl)[s]["bits"], by(arm)[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", part=part or "A+B", pooled_n0_yq=dict(n=len(names), mean=G.pct(ref)),
                        pooled_n0_a800=dict(n=len(names_a8), mean=G.pct(ref_a8)) if names_a8 else None)}
    claims = []
    if "fixed" in arms:
        claims.append(("N1", "fixed", "N1 gate only - plain training"))
    if "meta3" in arms:
        claims.append(("N2", "meta3", "N2 gate + meta level v3 - plain training"))
    for key, arm, name in claims:
        res[key] = G.paired(pair("nogate", arm), 10.0, f"{name} (official test)")
        if "nogate" in a8 and arm in a8:
            res[f"{key}_4seed"] = G.paired([("A0", a8["nogate"]["bits"], a8[arm]["bits"])] + pair("nogate", arm), 10.0,
                                           f"{name}, seeds 0-3 within platform (official test; alongside, amendment 1)")
    if part in (None, "A"):
        res["N3"] = G.r1(by("nogate"), "nogate", ref=ref)
        res["N3"]["claim"] = "N3 plain training: final - pooled initial reference (no bar)"
    if all(fresh.values()):
        fp = lambda ctrl, arm: [(s, fresh[(ctrl, s)][1], fresh[(arm, s)][1]) for s in SEEDS]
        frefs = {p: F.reference(root, p, "spatial") for p in ("yq", "a800")}
        fref = {p: [sum(v) / len(v) for v in zip(*[e[1] for e in evs])] for p, evs in frefs.items() if evs}
        for key, arm, name in claims:
            res[f"{key}_fresh"] = F.paired(fp("nogate", arm), 10.0, f"{name} (fresh sealed test)")
            if fresh_a8.get("nogate") and fresh_a8.get(arm):
                res[f"{key}_fresh_4seed"] = F.paired([("A0", fresh_a8["nogate"][1], fresh_a8[arm][1])] + fp("nogate", arm), 10.0,
                                                     f"{name}, seeds 0-3 within platform (fresh sealed test; alongside)")
        if part in (None, "A") and "yq" in fref:
            res["N3_fresh"] = F.paired([(s, fref["yq"], fresh[("nogate", s)][1]) for s in SEEDS], None,
                                       "N3 plain training - initial reference (fresh sealed test, no bar)")
    else:
        res["fresh"] = "not all fresh evaluations exist"
    res["runs"] = {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                     evals=r["n_evals"]) for (a, s), r in sorted(runs.items())}
    res["runs"].update({f"{a}_s0 (A800)": dict(retained=r["retained"], test=G.pct(r["bits"]), evals=r["n_evals"]) for a, r in sorted(a8.items())})
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

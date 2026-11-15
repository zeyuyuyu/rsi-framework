"""Addendum 38: the continued loop run up to tuned RL's counted budget (equal total GPU-hours), Yangquan seeds 1-3.

Version read per seed: the version its run retains when it stops. Seeds whose version changed under addendum 38 are
evaluated in yq_oftgbx_mb_s<n>_fin_fresh (+ _fresh23, two more) and _fin_rep (official, three); a seed whose version
did not change (seed 2 always) reuses addendum 35's yq_oftgbx_ext_s<n>_fin_fresh / _fresh23 / _fin_rep.
    M1  loop at RL's budget - tuned RL 36 blocks (yq_oftg_onebig12), fresh scenes: CI reported, no bar
    M2  loop at RL's budget - tuned RL 18 blocks (yq_oftg_onebig), fresh scenes: bar +3
Fresh: registered = one evaluation per version (each arm's first); beside it three evaluations per version.
Official test (three evaluations per version) beside both. Costs from results/mb_costs_20261116.json when present.
usage: python3 scripts/report/addendum38_read.py [results root] [--check] [--json out.json]
--check lists what exists and prints no success number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fresh_read as F           # noqa: E402
import cost_curve_read as C      # noqa: E402
import goal_read as G            # noqa: E402
from goal_ext_read import ext_record   # noqa: E402

SEEDS = (1, 2, 3)


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = Path(args[0] if args else "results"); Y = root / "baidu"
    res, missing = {"note": "addendum 38"}, []
    src, fresh1, fresh3, offi = {}, {}, {}, {}
    for s in SEEDS:
        tag = "mb" if (Y / f"yq_oftgbx_mb_s{s}_fin_fresh").exists() else "ext"
        src[s] = tag
        f1 = C.evals(Y / f"yq_oftgbx_{tag}_s{s}_fin_fresh")[:1]
        f3 = f1 + C.evals(Y / f"yq_oftgbx_{tag}_s{s}_fresh23")
        fresh1[s], fresh3[s] = f1, f3
        offi[s] = ext_record(Y / f"yq_oftgbx_{tag}_s{s}_fin_rep")
        if len(f1) != 1: missing.append(f"s{s} {tag} fresh: {len(f1)}/1")
        if len(f3) != 3: missing.append(f"s{s} {tag} fresh three: {len(f3)}/3")
        if not offi[s]: missing.append(f"s{s} {tag} official: missing")
    rl = {}
    for k, n in (("rl36", "yq_oftg_onebig12"), ("rl18", "yq_oftg_onebig")):
        for s in SEEDS:
            ev = C.evals(Y / f"{n}_s{s}_fresh")[:1] + C.evals(Y / f"{n}_s{s}_fresh23")
            rl[(k, s)] = ev
            if len(ev) != 3: missing.append(f"{k} s{s} fresh: {len(ev)}/3")
    res["source"] = {f"s{s}": src[s] for s in SEEDS}
    res["nodes"] = {f"s{s}": (offi[s] or {}).get("node") for s in SEEDS}
    res["missing"] = missing
    cost_f = root / "mb_costs_20261116.json"
    if cost_f.exists():
        res["costs"] = json.loads(cost_f.read_text())
    if check:
        print(json.dumps(res, indent=1)); return
    digests = {d for s in SEEDS for d, _ in fresh3[s]} | {d for v in rl.values() for d, _ in v}
    if len(digests) > 1:
        raise SystemExit(f"fresh episode lists differ: {sorted(digests)}")
    if all(len(fresh1[s]) == 1 for s in SEEDS):
        one = lambda k: [(s, C.mean_bits(rl[(k, s)][:1]), C.mean_bits(fresh1[s])) for s in SEEDS]
        res["M1_fresh"] = F.paired(one("rl36"), None, "M1 loop at RL's budget - RL 36 blocks, fresh scenes, one evaluation (registered)")
        res["M2_fresh"] = F.paired(one("rl18"), 3.0, "M2 loop at RL's budget - RL 18 blocks, fresh scenes, one evaluation (registered, bar +3)")
    if all(len(fresh3[s]) == 3 for s in SEEDS) and all(len(v) == 3 for v in rl.values()):
        three = lambda k: [(s, C.mean_bits(rl[(k, s)]), C.mean_bits(fresh3[s])) for s in SEEDS]
        res["M1_fresh_three"] = F.paired(three("rl36"), None, "M1, three evaluations per version")
        res["M2_fresh_three"] = F.paired(three("rl18"), None, "M2, three evaluations per version")
    if all(offi.values()):
        G.MODE = "final"
        runs = {(k, s): G.record(Y / f"{n}_s{s}") for k, n in (("rl36", "yq_oftg_onebig12"), ("rl18", "yq_oftg_onebig")) for s in SEEDS}
        pair = lambda k: [(s, runs[(k, s)]["bits"], offi[s]["bits"]) for s in SEEDS]
        res["M1_official"] = G.paired(pair("rl36"), 0.0, "M1 official test, three evaluations"); res["M1_official"].pop("passes", None)
        res["M2_official"] = G.paired(pair("rl18"), 3.0, "M2 official test, three evaluations"); res["M2_official"].pop("passes", None)
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

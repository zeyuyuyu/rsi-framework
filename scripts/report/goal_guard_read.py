"""Addendum 32: the one-time official-test reads of (a) the guard-rail gate on the 12-round LIBERO-Goal loop and
(b) plain training of the collapsing BC recipe on LIBERO-Goal. Yangquan, seeds 1-3. Finals follow the registered
rule (per-episode mean of three evaluations of the retained policy). Seed-averaged per-episode paired bootstrap.
Reference: per-episode mean of every in-run n0 test of the Goal checkpoint on Yangquan (as in long12_read.py).

(a) guard  yq_oftg_guard12_s<seed> against yq_oftg_fixed12_s<seed> (strict gate) and yq_oftg_onebig12_s<seed>
           (one round, 36 steps, no intermediate gate), both read 2026-11-08.
    G2  guard12 - fixed12 >= +2.0, CI > 0      G1  guard12 - reference, R1 rule (>= +5.0, CI > 0, >= 2 of 3 seeds > 0)
    G3  guard12 - onebig12, reported with CI (non-inferiority margin 2 points: lower CI bound > -2)
(b) nogate yq_oftgb_nogate_s<seed> (every round kept; must end on r06c0) against the addendum-24 runs
           yq_oftgb_fixed_s<seed> (gate only) and yq_oftgb_llm_harness_s<seed> (gate + LLM meta level), read 2026-11-09.
    NG1 fixed - nogate >= +10, CI > 0          NG2 llm_harness - nogate >= +10, CI > 0
    NG3 nogate - reference, reported with CI
usage: python3 scripts/report/goal_guard_read.py <guard|nogate> [results root] [--check] [--json out.json]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402
from rsi.audit.compare_arms import load_scores         # noqa: E402

SEEDS = (1, 2, 3)


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    block, root = args[0], (args[1] if len(args) > 1 else "results")
    G.MODE = "final"
    d = lambda name, s: Path(root) / "baidu" / f"{name}_s{s}"
    if block == "guard":
        names = dict(new="yq_oftg_guard12", a="yq_oftg_fixed12", b="yq_oftg_onebig12")
    elif block == "nogate":
        names = dict(new="yq_oftgb_nogate", a="yq_oftgb_fixed", b="yq_oftgb_llm_harness")
    else:
        raise SystemExit(__doc__)
    runs = {(k, s): G.record(d(n, s)) for k, n in names.items() for s in SEEDS}
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for s in SEEDS:
        r = runs[("new", s)]
        want = 12 if block == "guard" else 6
        if r["rounds"] != want:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected {want}")
        if block == "nogate" and r["retained"] != "r06c0":
            raise SystemExit(f"{r['run']}: plain training must end on r06c0, got {r['retained']}")
    lists = []
    for p in (Path(root) / "baidu").glob("yq_*"):
        if p.name.startswith(("yq_oftg_", "yq_oftgb_", "yq_m2_")) and not p.name.endswith(("_rep", "_fresh")) and p.is_dir():
            sc = load_scores(p, G.SUITE)
            if "n0" in sc and sc["n0"][0] == next(iter(digests)):
                lists.append(sc["n0"][1])
    ref = G.mean_bits(lists)
    if check:
        print(f"pooled n0 reference: yq {len(lists)} evaluations (mean withheld in --check)")
        for (k, s), r in sorted(runs.items()):
            print(f"{r['run']:30s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} evals={r['n_evals']}")
        return
    by = lambda k: {s: runs[(k, s)] for s in SEEDS}
    pair = lambda ctrl, arm: [(s, by(ctrl)[s]["bits"], by(arm)[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(mode="final", block=block, pooled_n0_yq=dict(n=len(lists), mean=G.pct(ref)))}
    if block == "guard":
        res["G2"] = G.paired(pair("a", "new"), 2.0, "G2 guard12 - fixed12 (official test)")
        res["G1"] = G.r1(by("new"), "guard12", ref=ref)
        res["G1"]["claim"] = "G1 guard12: final - pooled initial reference"
        res["G3"] = G.paired(pair("b", "new"), 0.0, "G3 guard12 - onebig12 (official test; non-inferiority margin 2 points)")
        res["G3"]["non_inferior_margin_2"] = bool(res["G3"]["ci95_points"][0] > -2.0)
        res["G3"].pop("passes", None)
    else:
        res["NG1"] = G.paired(pair("new", "a"), 10.0, "NG1 gate only - plain training (official test)")
        res["NG2"] = G.paired(pair("new", "b"), 10.0, "NG2 gate + LLM meta level - plain training (official test)")
        res["NG3"] = G.r1(by("new"), "nogate", ref=ref)
        res["NG3"]["claim"] = "NG3 plain training: final - pooled initial reference (no bar)"
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

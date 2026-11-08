"""Addendum 27 (2026-11-07): the one-time read of the 12-round LIBERO-Goal recursion test on Yangquan.

Arms: yq_oftg_fixed12_s{1,2,3} (12 rounds x 3 inner steps, recursive), yq_oftg_nonrec12_s{1,2,3} (practice from the
frozen initial policy), yq_oftg_onebig12_s{1,2,3} (1 round x 36 inner steps). Finals follow the registered rule
(VLA addendum 2): per-episode mean of three evaluations of the retained policy; the initial reference is the pooled
Yangquan n0 mean (every in-run n0 test of this model and suite). Seed-averaged per-episode paired bootstrap.

Bars (addendum 27): R3-long fixed12 - nonrec12 >= +2.0, CI > 0 (primary); R5-long fixed12 - onebig12 >= +2.0, CI > 0,
also reported against onebig12's ungated single candidate r01c0 (sensitivity); R1-long fixed12 - reference with the R1
rule (>= +5.0, CI > 0, >= 2 of 3 seeds > 0), plus fixed12 - fixed (the 6-round finals of the same seeds), descriptive.
Noise check: two halves of the n0 evaluations of the nine runs.

usage: python3 scripts/report/long12_read.py [results root] [--check] [--json out.json]
--check prints readiness (retained node, gate, rounds, evaluation counts) and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G   # noqa: E402
from rsi.audit.compare_arms import load_scores   # noqa: E402

ARMS = ("fixed12", "nonrec12", "onebig12")
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

    runs = {(arm, s): G.record(G.run_dir(root, "yq", arm, s)) for arm in ARMS for s in SEEDS}
    six = {s: G.record(G.run_dir(root, "yq", "fixed", s)) for s in SEEDS}          # 6-round fixed, same seeds
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()} | {r["digest"] for r in six.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    for (arm, s), r in runs.items():
        want = 1 if arm == "onebig12" else 12
        if r["rounds"] != want:
            raise SystemExit(f"{r['run']}: {r['rounds']} rounds, expected {want}")

    # pooled initial reference (Yangquan): every in-run n0 test of this model and suite
    lists = []
    for p in (Path(root) / "baidu").glob("yq_*"):
        if p.name.startswith(("yq_oftg_", "yq_oftgb_", "yq_m2_")) and not p.name.endswith("_rep"):
            sc = load_scores(p, G.SUITE)
            if "n0" in sc and sc["n0"][0] == next(iter(runs.values()))["n0_digest"]:
                lists.append(sc["n0"][1])
    ref, n_ref = G.mean_bits(lists), len(lists)

    if check:
        print(f"pooled n0 reference: yq {n_ref} evaluations (mean withheld in --check)")
        for (arm, s), r in sorted(runs.items()):
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                  f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        print("digest", digests.pop())
        return

    res = {"mode": dict(mode="final", pooled_n0_yq=dict(n=n_ref, mean=G.pct(ref)))}
    res["R3_long"] = G.paired([(s, runs[("nonrec12", s)]["bits"], runs[("fixed12", s)]["bits"]) for s in SEEDS], 2.0,
                              "R3-long fixed12 - nonrec12 (Yangquan, seeds 1-3)")
    res["R5_long"] = G.paired([(s, runs[("onebig12", s)]["bits"], runs[("fixed12", s)]["bits"]) for s in SEEDS], 2.0,
                              "R5-long fixed12 - onebig12 (Yangquan, seeds 1-3)")
    # R5-long sensitivity: onebig12's ungated single candidate r01c0 (addendum 18 am. 1 form)
    ung, missing = [], []
    for s in SEEDS:
        r = runs[("onebig12", s)]
        evals = [r["scores"]["r01c0"][1]] if "r01c0" in r["scores"] else []
        evals += G.rep_scores(G.run_dir(root, "yq", "onebig12", s)).get("r01c0", [])
        extra = G.run_dir(root, "yq", "onebig12", s)
        extra = extra.parent / f"{extra.name}_r01c0"
        if extra.exists():
            sc = load_scores(extra, G.SUITE)
            evals += [sc[k][1] for k in sorted(sc) if k.startswith("r01c0")]
        if evals:
            ung.append((s, G.mean_bits(evals), runs[("fixed12", s)]["bits"]))
        else:
            missing.append(s)
    if ung:
        res["R5_long_ungated"] = G.paired(ung, 2.0, "R5-long sensitivity: fixed12 - onebig12 r01c0 (available seeds)",
                                          extra=dict(missing_seeds=missing))
    res["R1_long"] = G.r1({s: runs[("fixed12", s)] for s in SEEDS}, "fixed12", ref=ref)
    res["R1_long"]["claim"] = "R1-long fixed12: final - pooled initial reference"
    res["fixed12_minus_fixed6"] = G.paired([(s, six[s]["bits"], runs[("fixed12", s)]["bits"]) for s in SEEDS], 0.0,
                                           "descriptive: fixed12 - fixed (6-round finals, same seeds, no bar)")
    res["nonrec12_minus_nonrec6"] = None
    try:
        six_nr = {s: G.record(G.run_dir(root, "yq", "nonrec", s)) for s in SEEDS}
        res["nonrec12_minus_nonrec6"] = G.paired([(s, six_nr[s]["bits"], runs[("nonrec12", s)]["bits"]) for s in SEEDS], 0.0,
                                                 "descriptive: nonrec12 - nonrec (6-round finals, same seeds, no bar)")
    except SystemExit:
        pass
    res["noise_check_n0_halves"] = G.noise_check({f"{a}_s{s}": r for (a, s), r in runs.items()})
    res["runs"] = {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                     rounds=r["rounds"], evals=r["n_evals"]) for (a, s), r in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

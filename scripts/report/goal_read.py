"""Prereg v3 LIBERO-Goal main study: the one-time read of R1-R5 (prereg v3; addenda 14-16, 18 am. 1, 22, 23, 25).

Platforms (addendum 15): Yangquan seeds 1-3 (results/baidu/yq_oftg_<arm>_s<seed>) carry R1, R2, R3, R4, R4-harness
and R5; cavin seeds 1-3 (results/a800/runs2/a8_goalmain_<arm>_s<seed>) carry R4-llm and R4-cap against cavin's own
`fixed`. Seed 0 (addendum 23, moved to cavin by addendum 25: a8_goalmain_{fixed,nonrec,shuffled,onebig}_s0) joins
R2, R3 and R5 as a fourth seed; the 3-seed statistic is reported alongside. Every run is measured on its final
retained policy; comparisons are paired per episode within a seed, seed-averaged, with a paired bootstrap CI
(10,000 draws). R5-ungated (addendum 18 am. 1) uses each onebig run's r01c0 test whatever its gate; a rejected
candidate needs a `--test-eval --node r01c0` job first (test-libero_official-r01c0*.jsonl in the run dir).
usage: python3 scripts/report/goal_read.py [results root] [--check] [--json out.json]
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rsi.audit.compare_arms import load_scores, seed_avg   # noqa: E402
from rsi.core.stats import mcnemar_exact, paired_bootstrap   # noqa: E402

SUITE = "libero_official"
MODE = "single"      # "single": the run's own test only (preliminary); "final": registered rule (VLA addendum 2)


def rep_scores(run):
    """Replicate evaluations of the retained node: <run>_rep/test-<suite>-<node>-rep<k>.jsonl (cavin) or TESTBITS
    lines of <run>_rep/tests.txt (Yangquan extract). {node: [bits, ...]}"""
    rep = run.parent / f"{run.name}_rep"
    out = {}
    if not rep.exists():
        return out
    for p in rep.glob(f"test-{SUITE}-*-rep*.jsonl"):
        node = p.stem[len(f"test-{SUITE}-"):].rsplit("-rep", 1)[0]
        recs = [json.loads(l) for l in open(p) if l.strip()]
        out.setdefault(node, []).append([1 if r["score"] >= 0.5 else 0 for r in recs])
    tests = rep / "tests.txt"
    if tests.exists():
        for line in open(tests):
            parts = line.split()
            if len(parts) == 5 and parts[0] == "TESTBITS" and "-rep" in parts[1]:
                node = parts[1][len(f"test-{SUITE}-"):-len(".jsonl")].rsplit("-rep", 1)[0]
                out.setdefault(node, []).append([int(c) for c in parts[4]])
    return out


def mean_bits(lists):
    return [sum(v) / len(lists) for v in zip(*lists)]


def run_dir(root, platform, arm, seed):
    if platform == "yq":
        return Path(root) / "baidu" / f"yq_oftg_{arm}_s{seed}"
    return Path(root) / "a800" / "runs2" / f"a8_goalmain_{arm}_s{seed}"


def round_candidates(run):
    """[(round, node, gate, accepted)] from the round files of either platform format."""
    out = []
    for f in sorted(run.glob("round-[0-9][0-9].json")):
        text = f.read_text()
        try:
            whole = json.loads(text)
        except json.JSONDecodeError:
            whole = None
        if isinstance(whole, dict) and "candidates" in whole:
            rnd, cands, acc = whole["round"], whole["candidates"], whole.get("accepted")
        else:
            lines = [json.loads(l) for l in text.splitlines() if l.strip()]
            head = next((l for l in lines if "round" in l and "node" not in l), {})
            rnd, acc = head.get("round"), head.get("accepted")
            cands = [c for c in lines if "node" in c]
        for c in cands:
            out.append((rnd, c["node"], c.get("gate"), acc))
    return out


def record(run):
    if not (run / "report.json").exists():
        raise SystemExit(f"{run}: no report.json (run not finished)")
    rep = json.loads((run / "report.json").read_text())
    node = rep["retained"]
    scores = load_scores(run, SUITE)
    if "n0" not in scores or node not in scores:
        raise SystemExit(f"{run.name}: missing test bits for n0 or retained {node}: {sorted(scores)}")
    cands = round_candidates(run)
    gates = {n: g for _, n, g, _ in cands}
    gate = None if node == "n0" else gates.get(node)
    reps = rep_scores(run) if MODE == "final" else {}
    final_evals = [scores[node][1]] + reps.get(node, [])
    if MODE == "final" and node != "n0" and len(final_evals) < 3:
        raise SystemExit(f"{run.name}: registered final needs 3 evaluations of {node}, found {len(final_evals)}")
    return dict(run=run.name, retained=node, retained_gate=gate, rounds=len({r for r, _, _, _ in cands}),
                digest=scores[node][0], bits=mean_bits(final_evals), n_evals=len(final_evals),
                n0_digest=scores["n0"][0], n0_bits=scores["n0"][1], cands=cands, scores=scores)


def pct(bits):
    return round(100 * sum(bits) / len(bits), 2)


def paired(pairs, bar, name, extra=None):
    """pairs: [(seed, control_bits, arm_bits)] -> seed-averaged arm - control with CI and per-seed detail."""
    a, b = seed_avg([(x, y) for _, x, y in pairs])
    diff = 100 * sum(y - x for x, y in zip(a, b)) / len(a)
    lo, hi = paired_bootstrap(a, b)
    per = {}
    for s, x, y in pairs:
        p, gain, loss = mcnemar_exact(x, y)
        l2, h2 = paired_bootstrap(x, y)
        per[s] = dict(control=pct(x), arm=pct(y), diff=round(pct(y) - pct(x), 2), ci95=[round(100 * l2, 2), round(100 * h2, 2)],
                      mcnemar_p=round(p, 4), arm_only=gain, control_only=loss)
    out = dict(claim=name, seeds=[s for s, _, _ in pairs], n_episodes=len(a), bar_points=bar,
               mean_points=round(diff, 2), ci95_points=[round(100 * lo, 2), round(100 * hi, 2)],
               passes=bool(diff >= bar and lo > 0), per_seed=per)
    if extra:
        out.update(extra)
    return out


def r1(recs, arm, bar=5.0, ref=None):
    """ref: the platform's pooled initial reference (per-episode mean over every in-run n0 test), VLA addendum 2."""
    pairs = [(s, ref if ref is not None else r["n0_bits"], r["bits"]) for s, r in sorted(recs.items())]
    out = paired(pairs, bar, f"R1 {arm}: final - initial")
    excl = sum(1 for v in out["per_seed"].values() if v["ci95"][0] > 0)
    out["seeds_excluding_zero"] = excl
    out["passes"] = bool(out["passes"] and excl >= 2)
    out["bar_note"] = "prereg v3 R1 for M1: >= +5.0, CI > 0, >= 2 of 3 seeds individually > 0; the +3.0 pilot rule of addendum 11 is also shown"
    out["passes_at_3"] = bool(out["mean_points"] >= 3.0 and out["ci95_points"][0] > 0 and excl >= 2)
    return out


def noise_check(recs):
    """VLA addendum 2: the same statistic between two halves of the in-run n0 evaluations (identical model):
    the runs are split into two groups (alternating), each group's per-episode mean is taken, and the paired
    difference with its bootstrap CI is reported. (The earlier odd/even-episode split is confounded by the test's
    episode order and is dropped.)"""
    keys = sorted(recs)
    a = mean_bits([recs[k]["n0_bits"] for k in keys[0::2]])
    b = mean_bits([recs[k]["n0_bits"] for k in keys[1::2]]) if len(keys) > 1 else a
    lo, hi = paired_bootstrap(a, b)
    return dict(groups=[keys[0::2], keys[1::2]], diff_points=round(100 * (sum(b) - sum(a)) / len(a), 2),
                ci95=[round(100 * lo, 2), round(100 * hi, 2)])


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    global MODE
    if "--mode" in args:
        i = args.index("--mode"); MODE = args[i + 1]; del args[i:i + 2]
    root = args[0] if args else "results"

    yq = {(arm, s): record(run_dir(root, "yq", arm, s))
          for arm in ("fixed", "full", "llm_harness", "onebig", "nonrec", "shuffled") for s in (1, 2, 3)}
    cv = {(arm, s): record(run_dir(root, "cavin", arm, s))
          for arm in ("fixed", "llm", "llm_harness_cap") for s in (1, 2, 3)}
    s0 = {(arm, 0): record(run_dir(root, "cavin", arm, 0)) for arm in ("fixed", "nonrec", "shuffled", "onebig")}
    digests = {r["digest"] for d in (yq, cv, s0) for r in d.values()} | {r["n0_digest"] for d in (yq, cv, s0) for r in d.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")
    # pooled initial reference per platform: every in-run n0 test of this model and suite (VLA addendum 2)
    def pooled_n0(platform):
        runs = []
        if platform == "yq":
            runs = [p for p in (Path(root) / "baidu").glob("yq_*") if p.name.startswith(("yq_oftg_", "yq_oftgb_", "yq_m2_"))]
        else:
            runs = [p for p in (Path(root) / "a800" / "runs2").glob("a8_*") if p.name.startswith(("a8_goalmain_", "a8_oftgb_", "a8_m2_"))
                    and not p.name.endswith("_rep")]
        lists = []
        for p in runs:
            sc = load_scores(p, SUITE)
            if "n0" in sc and sc["n0"][0] == next(iter(yq.values()))["n0_digest"]:
                lists.append(sc["n0"][1])
        return mean_bits(lists), len(lists)
    ref_yq, n_yq = pooled_n0("yq")
    ref_cv, n_cv = pooled_n0("cavin")
    if check:
        print(f"mode={MODE} pooled n0 reference: yq {n_yq} evaluations mean {pct(ref_yq)}, cavin {n_cv} evaluations mean {pct(ref_cv)}")
        for d in (yq, cv, s0):
            for (arm, s), r in sorted(d.items()):
                print(f"{r['run']:34s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                      f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        print("digest", digests.pop())
        return

    res = {}
    # R1 (Yangquan seeds 1-3, fixed and full)
    ref = ref_yq if MODE == "final" else None
    res["R1_fixed"] = r1({s: yq[("fixed", s)] for s in (1, 2, 3)}, "fixed", ref=ref)
    res["R1_full"] = r1({s: yq[("full", s)] for s in (1, 2, 3)}, "full", ref=ref)
    res["mode"] = dict(mode=MODE, pooled_n0_yq=dict(n=n_yq, mean=pct(ref_yq)), pooled_n0_cavin=dict(n=n_cv, mean=pct(ref_cv)))
    # R2 / R3: seeds 0-3 (seed 0 paired within cavin), 3-seed alongside
    for name, arm, ctrl, bar in (("R2 fixed - shuffled", "fixed", "shuffled", 3.0), ("R3 fixed - nonrec", "fixed", "nonrec", 2.0)):
        p4 = [(0, s0[(ctrl, 0)]["bits"], s0[(arm, 0)]["bits"])] + [(s, yq[(ctrl, s)]["bits"], yq[(arm, s)]["bits"]) for s in (1, 2, 3)]
        res[name.split()[0] + "_seeds0to3"] = paired(p4, bar, name + " (seeds 0-3; seed 0 on cavin)")
        res[name.split()[0] + "_seeds1to3"] = paired(p4[1:], bar, name + " (seeds 1-3, Yangquan)")
    # R4 family (seeds 1-3)
    res["R4_full_minus_fixed"] = paired([(s, yq[("fixed", s)]["bits"], yq[("full", s)]["bits"]) for s in (1, 2, 3)], 2.0, "R4 full - fixed (Yangquan)",
                                        extra=dict(gate_minus_test_of_selected={s: (None if yq[("full", s)]["retained_gate"] is None else
                                                   round(100 * yq[("full", s)]["retained_gate"] - pct(yq[("full", s)]["bits"]), 2)) for s in (1, 2, 3)}))
    res["R4_harness_minus_fixed_yq"] = paired([(s, yq[("fixed", s)]["bits"], yq[("llm_harness", s)]["bits"]) for s in (1, 2, 3)], 2.0, "R4-harness llm_harness - fixed (Yangquan)")
    res["R4_llm_minus_fixed_cavin"] = paired([(s, cv[("fixed", s)]["bits"], cv[("llm", s)]["bits"]) for s in (1, 2, 3)], 2.0, "R4-llm llm - fixed (cavin)")
    res["R4_cap_minus_fixed_cavin"] = paired([(s, cv[("fixed", s)]["bits"], cv[("llm_harness_cap", s)]["bits"]) for s in (1, 2, 3)], 2.0, "R4-cap llm_harness_cap - fixed (cavin)")
    res["R4_llm_minus_full_secondary"] = paired([(s, yq[("full", s)]["bits"], yq[("llm_harness", s)]["bits"]) for s in (1, 2, 3)], 0.0, "secondary llm_harness - full (Yangquan, no bar)")
    # R5: best of fixed/full/llm_harness by retained gate (never by test) minus onebig; seed 0 has fixed only
    best = {}
    for s in (1, 2, 3):
        cands = {arm: yq[(arm, s)] for arm in ("fixed", "full", "llm_harness")}
        arm = max(cands, key=lambda a: (cands[a]["retained_gate"] or -1))
        best[s] = (arm, cands[arm])
    best[0] = ("fixed", s0[("fixed", 0)])
    p4 = [(s, (s0 if s == 0 else yq)[("onebig", s)]["bits"], best[s][1]["bits"]) for s in (0, 1, 2, 3)]
    res["R5_seeds0to3"] = paired(p4, 2.0, "R5 best-by-gate - onebig (seeds 0-3)", extra=dict(best_arm={s: best[s][0] for s in best}))
    res["R5_seeds1to3"] = paired(p4[1:], 2.0, "R5 best-by-gate - onebig (seeds 1-3, Yangquan)", extra=dict(best_arm={s: best[s][0] for s in (1, 2, 3)}))
    # R5-ungated: onebig's r01c0 test whatever its gate (addendum 18 am. 1)
    ung, missing = [], []
    for s in (0, 1, 2, 3):
        r = (s0 if s == 0 else yq)[("onebig", s)]
        evals = [r["scores"]["r01c0"][1]] if "r01c0" in r["scores"] else []
        if MODE == "final":
            evals += rep_scores(run_dir(root, "cavin" if s == 0 else "yq", "onebig", s)).get("r01c0", [])
        # a rejected candidate has no in-run test: its `--test-eval --node r01c0` job writes <run>_r01c0 (addendum 18 am. 1)
        extra = run_dir(root, "cavin" if s == 0 else "yq", "onebig", s)
        extra = extra.parent / f"{extra.name}_r01c0"
        if extra.exists():
            sc = load_scores(extra, SUITE)
            evals += [sc[k][1] for k in sorted(sc) if k.startswith("r01c0")]
        if not evals:
            missing.append(s)
        else:
            ung.append((s, mean_bits(evals) if MODE == "final" else evals[0], best[s][1]["bits"]))
    if ung:
        res["R5_ungated"] = paired(ung, 2.0, "R5-ungated best-by-gate - onebig r01c0 (available seeds)", extra=dict(missing_seeds=missing))
    res["noise_check_n0_halves"] = dict(yq=noise_check({f"{a}_s{s}": r for (a, s), r in yq.items()}),
                                        cavin=noise_check({f"{a}_s{s}": r for (a, s), r in {**cv, **s0}.items()}))
    res["runs"] = {d: {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=pct(r["bits"]), n0=pct(r["n0_bits"]), rounds=r["rounds"])
                       for (a, s), r in sorted(src.items())} for d, src in (("yq", yq), ("cavin", cv), ("cavin_s0", s0))}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

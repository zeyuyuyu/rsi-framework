"""Addenda 24 + 26: the one-time read of the self-repair study (S1-S3).

Arms start from the collapsing behaviour-cloning recipe: fixed (gate only), full (numeric search over the harness
space, 2 candidates), llm_harness (LLM proposer, same compute). Seeds 1-3 on Yangquan (results/baidu/yq_oftgb_<arm>_s<seed>),
seed 0 on cavin (results/a800/runs2/a8_oftgb_<arm>_s0; addendum 26). Finals follow the registered rule (VLA addendum 2):
per-episode mean of three evaluations of the retained policy. Seed-averaged per-episode paired bootstrap, each seed
paired within its platform.

Bars: S1 (primary) llm_harness - fixed >= +3.0, CI > 0, seeds 0-3 (3-seed Yangquan statistic alongside);
S2 (secondary, reported with CI) llm_harness - full; S3 (descriptive, no bar) llm_harness vs the hand-tuned GRPO loop
(yq_oftg_fixed_s1-3, a8_goalmain_fixed_s0). Noise check: two halves of the n0 evaluations of the twelve runs.

usage: python3 scripts/report/selfrepair_read.py [results root] [--check] [--json out.json]
--check prints readiness (retained node, gate, rounds, evaluation counts) and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G   # noqa: E402

ARMS = ("fixed", "full", "llm_harness")


def run_dir(root, arm, seed):
    if seed == 0:
        return Path(root) / "a800" / "runs2" / f"a8_oftgb_{arm}_s0"
    return Path(root) / "baidu" / f"yq_oftgb_{arm}_s{seed}"


def tuned_dir(root, seed):
    if seed == 0:
        return Path(root) / "a800" / "runs2" / "a8_goalmain_fixed_s0"
    return Path(root) / "baidu" / f"yq_oftg_fixed_s{seed}"


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    G.MODE = "final"

    runs = {(arm, s): G.record(run_dir(root, arm, s)) for arm in ARMS for s in (0, 1, 2, 3)}
    tuned = {s: G.record(tuned_dir(root, s)) for s in (0, 1, 2, 3)}
    digests = {r["digest"] for r in runs.values()} | {r["n0_digest"] for r in runs.values()} | {r["digest"] for r in tuned.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")

    if check:
        for (arm, s), r in sorted(runs.items()):
            acc = sorted({rnd for rnd, node, _, accepted in r["cands"] if accepted and node == r["retained"]})
            print(f"{r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                  f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        print("digest", digests.pop())
        return

    def pairs(ctrl, arm, seeds):
        return [(s, runs[(ctrl, s)]["bits"], runs[(arm, s)]["bits"]) for s in seeds]
    res = {"mode": dict(mode="final", pairing="within platform: seed 0 cavin, seeds 1-3 Yangquan")}
    res["S1_seeds0to3"] = G.paired(pairs("fixed", "llm_harness", (0, 1, 2, 3)), 3.0, "S1 llm_harness - fixed (seeds 0-3)")
    res["S1_seeds1to3"] = G.paired(pairs("fixed", "llm_harness", (1, 2, 3)), 3.0, "S1 llm_harness - fixed (seeds 1-3, Yangquan)")
    res["S2_seeds0to3"] = G.paired(pairs("full", "llm_harness", (0, 1, 2, 3)), 0.0, "S2 llm_harness - full (seeds 0-3, reported with CI, no bar)")
    res["S2_seeds1to3"] = G.paired(pairs("full", "llm_harness", (1, 2, 3)), 0.0, "S2 llm_harness - full (seeds 1-3, Yangquan, no bar)")
    res["full_minus_fixed"] = G.paired(pairs("fixed", "full", (0, 1, 2, 3)), 0.0, "secondary: full - fixed (seeds 0-3, no bar)")
    res["S3_llm_vs_tuned"] = G.paired([(s, tuned[s]["bits"], runs[("llm_harness", s)]["bits"]) for s in (0, 1, 2, 3)], 0.0,
                                      "S3 descriptive: llm_harness - hand-tuned GRPO fixed (seeds 0-3, no bar)")
    res["S3_fixed_vs_tuned"] = G.paired([(s, tuned[s]["bits"], runs[("fixed", s)]["bits"]) for s in (0, 1, 2, 3)], 0.0,
                                        "S3 descriptive: gate-only fixed (BC start) - hand-tuned GRPO fixed (seeds 0-3, no bar)")
    res["noise_check_n0_halves"] = dict(yq=G.noise_check({f"{a}_s{s}": r for (a, s), r in runs.items() if s > 0}),
                                        cavin=G.noise_check({f"{a}_s{s}": r for (a, s), r in runs.items() if s == 0}))
    res["runs"] = {f"{a}_s{s}": dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                                     rounds=r["rounds"], evals=r["n_evals"],
                                     accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc}))
                   for (a, s), r in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

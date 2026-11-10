"""Addendum 29: the one-time read of the self-repair study on LIBERO-Spatial with meta level v3.

Arms start from the collapsing behaviour-cloning recipe (addenda 12 and 24): fixed (gate only), full (numeric search
over the harness space, 2 candidates, capped at the start's work), meta3 (the LLM behind the v3 harness, same
compute). Seeds 1-3 on Yangquan (results/baidu/yq_oftsb_<arm>_s<seed>), seed 0 on the A800 node
(results/a800/runs2/a8_spatrep_<arm>_s0). A fourth set, meta3 from the tuned Spatial program
(results/baidu/yq_ofts_meta3_s<seed>), is paired with addendum 28's yq_ofts_fixed_s<seed>.
Finals follow the registered rule: per-episode mean of three evaluations of the retained policy. Seed-averaged
per-episode paired bootstrap, each seed paired within its platform.

Bars: S1-spatial (primary) meta3 - fixed >= +3.0, CI > 0, seeds 0-3 (3-seed Yangquan statistic alongside);
S2-spatial (reported with CI, no bar) meta3 - full; S3-spatial (descriptive) meta3 and fixed against the hand-tuned
loop (yq_ofts_fixed_s1-3, a8_spatmain_fixed_s0); R4-spatial meta3 (tuned start) - fixed (tuned) >= +2.0, CI > 0,
Yangquan seeds 1-3. Noise check: two halves of the n0 evaluations.

usage: python3 scripts/report/spatial_repair_read.py [results root] [--check] [--seeds 1,2,3] [--json out.json]
--check prints readiness (retained node, gate, rounds, evaluation counts) and no test number.
--seeds restricts the BC-start block (default 0,1,2,3); the registered read uses the default."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G   # noqa: E402

ARMS = ("fixed", "full", "meta3")


def run_dir(root, arm, seed):
    if seed == 0:
        return Path(root) / "a800" / "runs2" / f"a8_spatrep_{arm}_s0"
    return Path(root) / "baidu" / f"yq_oftsb_{arm}_s{seed}"


def tuned_dir(root, seed):
    if seed == 0:
        return Path(root) / "a800" / "runs2" / "a8_spatmain_fixed_s0"
    return Path(root) / "baidu" / f"yq_ofts_fixed_s{seed}"


def main():
    args = sys.argv[1:]
    out, seeds = None, (0, 1, 2, 3)
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    if "--seeds" in args:
        i = args.index("--seeds"); seeds = tuple(int(x) for x in args[i + 1].split(",")); del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = args[0] if args else "results"
    G.MODE = "final"
    yq = tuple(s for s in seeds if s > 0)

    runs = {(arm, s): G.record(run_dir(root, arm, s)) for arm in ARMS for s in seeds}
    tuned = {s: G.record(tuned_dir(root, s)) for s in sorted(set(seeds) | {1, 2, 3})}
    tuned_meta = {s: G.record(Path(root) / "baidu" / f"yq_ofts_meta3_s{s}") for s in (1, 2, 3)}
    everything = list(runs.values()) + list(tuned.values()) + list(tuned_meta.values())
    digests = {r["digest"] for r in everything} | {r["n0_digest"] for r in everything}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ across runs: {sorted(digests)}")

    if check:
        for label, group in (("BC start", runs), ("tuned fixed (add. 28)", tuned), ("tuned meta3", tuned_meta)):
            print(label)
            for key, r in sorted(group.items(), key=str):
                print(f"  {r['run']:28s} retained={r['retained']:6s} gate={r['retained_gate']} rounds={r['rounds']} "
                      f"n0_bits={len(r['n0_bits'])} final_bits={len(r['bits'])} evals={r['n_evals']}")
        print("digest", digests.pop())
        return

    def pairs(ctrl, arm, ss):
        return [(s, runs[(ctrl, s)]["bits"], runs[(arm, s)]["bits"]) for s in ss]
    res = {"mode": dict(mode="final", pairing="within platform: seed 0 A800, seeds 1-3 Yangquan", seeds=list(seeds))}
    res["S1_all_seeds"] = G.paired(pairs("fixed", "meta3", seeds), 3.0, f"S1-spatial meta3 - fixed (seeds {seeds})")
    res["S1_yangquan"] = G.paired(pairs("fixed", "meta3", yq), 3.0, f"S1-spatial meta3 - fixed (Yangquan seeds {yq})")
    res["S2_all_seeds"] = G.paired(pairs("full", "meta3", seeds), 0.0, f"S2-spatial meta3 - full (seeds {seeds}, no bar)")
    res["S2_yangquan"] = G.paired(pairs("full", "meta3", yq), 0.0, f"S2-spatial meta3 - full (Yangquan seeds {yq}, no bar)")
    res["full_minus_fixed"] = G.paired(pairs("fixed", "full", seeds), 0.0, f"secondary: full - fixed (seeds {seeds}, no bar)")
    res["S3_meta3_vs_tuned"] = G.paired([(s, tuned[s]["bits"], runs[("meta3", s)]["bits"]) for s in seeds], 0.0,
                                        "S3-spatial descriptive: meta3 (BC start) - hand-tuned GRPO fixed (no bar)")
    res["S3_fixed_vs_tuned"] = G.paired([(s, tuned[s]["bits"], runs[("fixed", s)]["bits"]) for s in seeds], 0.0,
                                        "S3-spatial descriptive: gate-only fixed (BC start) - hand-tuned GRPO fixed (no bar)")
    res["R4_spatial"] = G.paired([(s, tuned[s]["bits"], tuned_meta[s]["bits"]) for s in (1, 2, 3)], 2.0,
                                 "R4-spatial meta3 (tuned start) - fixed (tuned), Yangquan seeds 1-3")
    res["noise_check_n0_halves"] = dict(
        yq=G.noise_check(dict({f"{a}_s{s}": r for (a, s), r in runs.items() if s > 0},
                              **{f"tuned_meta3_s{s}": r for s, r in tuned_meta.items()})),
        **({"a800": G.noise_check({f"{a}_s{s}": r for (a, s), r in runs.items() if s == 0})} if 0 in seeds else {}))
    table = dict({f"{a}_s{s}": r for (a, s), r in runs.items()}, **{f"tuned_meta3_s{s}": r for s, r in tuned_meta.items()},
                 **{f"tuned_fixed_s{s}": r for s, r in tuned.items()})
    res["runs"] = {k: dict(retained=r["retained"], gate=r["retained_gate"], test=G.pct(r["bits"]), n0=G.pct(r["n0_bits"]),
                           rounds=r["rounds"], evals=r["n_evals"],
                           accepted_rounds=sorted({rnd for rnd, _, _, acc in r["cands"] if acc}))
                   for k, r in sorted(table.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

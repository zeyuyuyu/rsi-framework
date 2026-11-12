"""Descriptive, not a registered claim: the LIBERO-Goal meta level started from a failing recipe, against one-shot RL
on the hand-tuned recipe; and what the hand tuning cost.

Every number here comes from evaluations that were already read under their own registrations:
  - goal main (2026-11-06): the official test
  - self-repair (2026-11-09): the official test
  - goal_nogate (2026-11-12): fresh scenes of the self-repair arms
  - goal main fresh (2026-11-12): fresh scenes of the tuned arms
This script forms new pairs of them, so its outputs are descriptive and carry no bar.

  M_vs_RL     yq_oftgb_llm_harness (BC start, LLM meta level, 2 candidates/round) - yq_oftg_onebig (tuned GRPO, one
              round of 18 steps); within platform; official test seeds 0-3 (seed 0 on the A800 node), fresh scenes on
              seeds 1-3 (the A800 meta run has no fresh evaluation)
  M_vs_tuned  the same meta runs - the hand-tuned gated loop yq_oftg_fixed (= S3 of the self-repair read, recomputed)
  pilots      recipe-selection pilot runs and their recorded GPU-hours (report.json elapsed x rollout cards)
usage: python3 scripts/report/tuning_cost_read.py [results root] [--json out.json]"""
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G        # noqa: E402
import fresh_read as F       # noqa: E402

PILOTS = ["baidu/bj_oft3_pilot*", "a800/runs2/a8_oft3_pilot*", "baidu/bj_oftg_curve_*", "a800/runs2/a8_oftg_curve_*"]


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    root = Path(args[0] if args else "results")
    G.MODE = "final"
    yq = lambda n, s: root / "baidu" / f"{n}_s{s}"
    meta = {s: G.record(yq("yq_oftgb_llm_harness", s)) for s in (1, 2, 3)}
    meta[0] = G.record(root / "a800" / "runs2" / "a8_oftgb_llm_harness_s0")
    rl = {s: G.record(yq("yq_oftg_onebig", s)) for s in (1, 2, 3)}
    rl[0] = G.record(root / "a800" / "runs2" / "a8_goalmain_onebig_s0")
    tuned = {s: G.record(yq("yq_oftg_fixed", s)) for s in (1, 2, 3)}
    tuned[0] = G.record(root / "a800" / "runs2" / "a8_goalmain_fixed_s0")
    digests = {r["digest"] for d in (meta, rl, tuned) for r in d.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    res = {"note": "descriptive; new pairs of already-read evaluations; no bar"}
    res["M_vs_RL_official"] = G.paired([(s, rl[s]["bits"], meta[s]["bits"]) for s in (0, 1, 2, 3)], 0.0,
                                       "meta level from the failing recipe - one-shot RL on the tuned recipe (official, seeds 0-3)")
    res["M_vs_tuned_official"] = G.paired([(s, tuned[s]["bits"], meta[s]["bits"]) for s in (0, 1, 2, 3)], 0.0,
                                          "meta level from the failing recipe - hand-tuned gated loop (official, seeds 0-3; S3)")
    fm = {s: F.run_fresh(root, f"yq_oftgb_llm_harness_s{s}") for s in (1, 2, 3)}
    fr = {s: F.run_fresh(root, f"yq_oftg_onebig_s{s}") for s in (1, 2, 3)}
    ft = {s: F.run_fresh(root, f"yq_oftg_fixed_s{s}") for s in (1, 2, 3)}
    if all(fm.values()) and all(fr.values()) and all(ft.values()):
        res["M_vs_RL_fresh"] = F.paired([(s, fr[s][1], fm[s][1]) for s in (1, 2, 3)], None,
                                        "meta level from the failing recipe - one-shot RL on the tuned recipe (fresh scenes, seeds 1-3)")
        res["M_vs_tuned_fresh"] = F.paired([(s, ft[s][1], fm[s][1]) for s in (1, 2, 3)], None,
                                           "meta level from the failing recipe - hand-tuned gated loop (fresh scenes, seeds 1-3)")
    # addition fixed before it existed (TUNING_COST note, 2026-11-12 ~18:55Z): seed 0 on the A800 node, reported
    # beside the three-seed rows whatever it shows; pairs stay within platform
    fm0 = F.run_fresh(root, "a8_oftgb_llm_harness_s0")
    fr0, ft0 = F.run_fresh(root, "a8_goalmain_onebig_s0"), F.run_fresh(root, "a8_goalmain_fixed_s0")
    if fm0 and fr0 and ft0 and "M_vs_RL_fresh" in res:
        res["M_vs_RL_fresh_4seed"] = F.paired([(0, fr0[1], fm0[1])] + [(s, fr[s][1], fm[s][1]) for s in (1, 2, 3)], None,
                                              "meta level from the failing recipe - one-shot RL on the tuned recipe (fresh scenes, seeds 0-3)")
        res["M_vs_tuned_fresh_4seed"] = F.paired([(0, ft0[1], fm0[1])] + [(s, ft[s][1], fm[s][1]) for s in (1, 2, 3)], None,
                                                 "meta level from the failing recipe - hand-tuned gated loop (fresh scenes, seeds 0-3)")
    for d in (res.get("M_vs_RL_official"), res.get("M_vs_tuned_official")):
        d.pop("passes", None)
    res["finals_official"] = {f"s{s}": dict(meta=G.pct(meta[s]["bits"]), rl=G.pct(rl[s]["bits"]), tuned_loop=G.pct(tuned[s]["bits"]))
                              for s in (0, 1, 2, 3)}
    res["training_work_per_run"] = dict(one_shot_rl="1 candidate x 18 inner steps",
                                        meta_level="2 candidates x 6 rounds x 3 inner steps = 2x the step count (GPU-hours: see gpu_hours_measured)",
                                        gated_loop="1 candidate x 6 rounds x 3 inner steps = 1x")
    # correction 2026-11-12 ~23:50Z: step counts are not cost. The meta level's edits raise scenes, samples and update
    # steps per inner step, so its runs are measured here. report.json "seconds" accumulates over resumed sessions
    # ("elapsed" is the last session only); every run below used one card.
    def gpu_hours(d):
        rep = Path(d) / "report.json"
        return round(sum(json.load(open(rep))["seconds"].values()) / 3600, 1) if rep.exists() else None
    a8 = lambda n: root / "a800" / "runs2" / n
    res["gpu_hours_measured"] = dict(
        meta_level={**{f"s{s}": gpu_hours(yq("yq_oftgb_llm_harness", s)) for s in (1, 2, 3)}, "s0": gpu_hours(a8("a8_oftgb_llm_harness_s0"))},
        one_shot_rl={**{f"s{s}": gpu_hours(yq("yq_oftg_onebig", s)) for s in (1, 2, 3)}, "s0": gpu_hours(a8("a8_goalmain_onebig_s0"))},
        gated_loop_tuned={**{f"s{s}": gpu_hours(yq("yq_oftg_fixed", s)) for s in (1, 2, 3)}, "s0": gpu_hours(a8("a8_goalmain_fixed_s0"))},
        one_shot_rl_36_steps={f"s{s}": gpu_hours(yq("yq_oftg_onebig12", s)) for s in (1, 2, 3)})
    for k, v in list(res["gpu_hours_measured"].items()):
        yqv = [v[f"s{s}"] for s in (1, 2, 3) if v.get(f"s{s}") is not None]
        res["gpu_hours_measured"][k + "_mean_yangquan"] = round(sum(yqv) / len(yqv), 1) if yqv else None
    pilots = []
    for pat in PILOTS:
        for d in sorted(glob.glob(str(root / pat))):
            name = os.path.basename(d)
            if name.endswith(("_rep", "_fresh")) or not os.path.isdir(d):
                continue
            rep, plan = os.path.join(d, "report.json"), os.path.join(d, "plan.json")
            el = json.load(open(rep)).get("elapsed") if os.path.exists(rep) else None
            if el is not None:      # resumed pilots: "elapsed" is the last session; "seconds" accumulates. Take the larger.
                el = max(el, sum((json.load(open(rep)).get("seconds") or {}).values()))
            cards = len(json.load(open(plan)).get("vla", {}).get("rollout_gpus", [0]) or [0]) if os.path.exists(plan) else 1
            pilots.append(dict(run=name, hours=None if el is None else round(el / 3600, 1), cards=cards))
    timed = [p for p in pilots if p["hours"] is not None]
    res["pilots"] = dict(runs=len(pilots), timed=len(timed), gpu_hours_on_record=round(sum(p["hours"] * p["cards"] for p in timed), 1),
                         list=pilots)
    oneshot = [round(json.load(open(yq("yq_oftg_onebig", s) / "report.json"))["elapsed"] / 3600, 1) for s in (1, 2, 3)]
    res["one_shot_rl_hours_yangquan"] = oneshot
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

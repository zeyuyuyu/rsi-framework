"""Spatial counterpart of the counted-tuning comparison (TUNING_COST_20261112.md, "Spatial counterpart, fixed before
its data exist"; descriptive, no bar). Computed once, after addendum 29's read.

  meta level from the failing BC recipe (yq_oftsb_meta3_s1-3, a8_spatrep_meta3_s0)
  - one-shot RL on the hand-tuned recipe (yq_ofts_onebig_s1-3, a8_spatmain_onebig_s0)
Both tests, within platform, seeds 1-3 and 0-3. Official finals: per-episode mean of three evaluations; fresh: one.
Wall-clock hours of every run are listed (report.json "seconds"); the RL recipe was tuned on LIBERO-Goal (21 pilots,
213.4 GPU-hours) and used on Spatial unchanged. Caveat fixed in advance: meta3's frozen memory holds records of
earlier runs, some on the hand-tuned recipe.
usage: python3 scripts/report/tuning_cost_spatial_read.py [results root] [--json out.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G    # noqa: E402
import fresh_read as F   # noqa: E402

META = {0: "a800/runs2/a8_spatrep_meta3_s0", 1: "baidu/yq_oftsb_meta3_s1", 2: "baidu/yq_oftsb_meta3_s2", 3: "baidu/yq_oftsb_meta3_s3"}
RL = {0: "a800/runs2/a8_spatmain_onebig_s0", 1: "baidu/yq_ofts_onebig_s1", 2: "baidu/yq_ofts_onebig_s2", 3: "baidu/yq_ofts_onebig_s3"}


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    root = Path(args[0] if args else "results")
    G.MODE = "final"
    meta = {s: G.record(root / p) for s, p in META.items()}
    rl = {s: G.record(root / p) for s, p in RL.items()}
    if len({r["digest"] for r in list(meta.values()) + list(rl.values())}) != 1:
        raise SystemExit("official episode id lists differ")
    fm = {s: F.run_fresh(root, Path(p).name) for s, p in META.items()}
    fr = {s: F.run_fresh(root, Path(p).name) for s, p in RL.items()}
    if not all(fm.values()) or not all(fr.values()) or len({b[0] for b in list(fm.values()) + list(fr.values())}) != 1:
        raise SystemExit("a fresh evaluation is missing or the fresh episode lists differ")
    res = {"note": "descriptive; new pairs of already-read evaluations; no bar"}
    for seeds in ((1, 2, 3), (0, 1, 2, 3)):
        tag = "".join(map(str, seeds))
        res[f"official_s{tag}"] = G.paired([(s, rl[s]["bits"], meta[s]["bits"]) for s in seeds], 0.0,
                                           f"Spatial meta level from BC - one-shot RL on the tuned recipe (official, seeds {seeds})")
        res[f"official_s{tag}"].pop("passes", None)
        res[f"fresh_s{tag}"] = F.paired([(s, fr[s][1], fm[s][1]) for s in seeds], None,
                                        f"Spatial meta level from BC - one-shot RL on the tuned recipe (fresh scenes, seeds {seeds})")
    hours = lambda p: round(sum(json.load(open(root / p / "report.json"))["seconds"].values()) / 3600, 1)
    res["wall_clock_hours"] = dict(meta_level={f"s{s}": hours(p) for s, p in META.items()},
                                   one_shot_rl={f"s{s}": hours(p) for s, p in RL.items()}, rl_recipe_pilots_on_goal=213.4)
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

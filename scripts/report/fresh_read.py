"""Addendum 30: the one-time read of the sealed fresh-scene test (1000 sampled placements per suite, the same for
every run, used by no run for training, gating or auditing).

Per run: one evaluation of the retained policy (results/baidu/<run>_fresh/tests.txt on Yangquan,
results/a800/runs2/<run>_fresh/test-libero_fresh-*-rep1.jsonl on the A800 node). Reference: the per-episode mean of
the initial policy's evaluations on that platform (yq_fresh_n0_<suite>_<k>, a8_fresh_n0_<suite>_<k>). Comparisons are
paired per episode within a platform (seed 0 A800, seeds 1-3 Yangquan), seed-averaged, with a paired bootstrap CI
(10,000 draws). A noise figure next to every block: two halves of the reference evaluations.

Blocks and bars (addendum 30):
  spatial main    F1 fixed - n0 >= +3 (CI > 0)   F2 fixed - shuffled >= +3   F3 fixed - nonrec >= +2   F5 fixed - onebig >= +2
  goal main       the same four on the Goal runs (descriptive against the same bars; the Goal audit records are known)
  spatial repair  FS1 meta3 - fixed(BC) >= +3 (CI > 0)   FS2 meta3 - full (CI)   meta3 - n0 and fixed(BC) - n0 (CI)
  long12          FL1 fixed12 - n0 >= +5 (CI > 0)   FL3 fixed12 - nonrec12 >= +2 (CI > 0)   fixed12 - onebig12 if run
usage: python3 scripts/report/fresh_read.py <block> [results root] [--check] [--json out.json]
       block: spatial_main | goal_main | spatial_repair | spatial_long12 | goal_long12 | goal_guard12 | goal_nogate | goal_ext | goal_ext_interim |
              spatial_guard | spatial_guard_bj | spatial_guard_pooled | spatial_guard_repl_a8 | spatial_long12_a8 | spatial_guard12
Beijing (platform B, addendum 33 amendment 1): runs results/baidu/bj_ofts_<arm>_s<seed>_fresh, reference
bj_fresh_n0_<suite>_<k>; pairs are formed within a platform.
--check prints which evaluations exist and no number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rsi.audit.compare_arms import seed_avg        # noqa: E402
from rsi.core.stats import paired_bootstrap        # noqa: E402

N = 1000


def bits_of(d):
    """Per-episode outcomes of the one fresh evaluation in directory d, or None. (ids digest, bits)"""
    if not d.exists():
        return None
    tests = d / "tests.txt"
    if tests.exists():
        for line in open(tests):
            p = line.split()
            if len(p) == 5 and p[0] == "TESTBITS" and p[1].startswith("test-libero_fresh-"):
                return p[3], [int(c) for c in p[4]]
    for f in sorted(d.glob("test-libero_fresh-*-rep1.jsonl")):
        import hashlib
        recs = [json.loads(l) for l in open(f) if l.strip()]
        return (hashlib.sha256(json.dumps([r["id"] for r in recs]).encode()).hexdigest()[:16],
                [1 if r["score"] >= 0.5 else 0 for r in recs])
    return None


def run_fresh(root, name):
    base = Path(root) / ("a800/runs2" if name.startswith("a8_") else "baidu")
    return bits_of(base / f"{name}_fresh")


PREFIX = {"a800": "a8", "yq": "yq", "bj": "bj"}
PLAT_OF = {"Y": "yq", "A": "a800", "B": "bj"}                                   # addendum 33 platform letters
GUARD_RUN = {"Y": "yq_ofts_{arm}_s{n}", "A": "a8_spatmain_{arm}_s{n}", "B": "bj_ofts_{arm}_s{n}"}


def reference(root, platform, suite):
    base = Path(root) / ("a800/runs2" if platform == "a800" else "baidu")
    evals = [b for k in range(1, 9) for b in [bits_of(base / f"{PREFIX[platform]}_fresh_n0_{suite}_{k}")] if b]
    return evals


def pct(v):
    return round(100 * sum(v) / len(v), 2)


def paired(pairs, bar, name, need_ci=True):
    a, b = seed_avg([(x, y) for _, x, y in pairs])
    diff = 100 * sum(y - x for x, y in zip(a, b)) / len(a)
    lo, hi = paired_bootstrap(a, b)
    return dict(claim=name, seeds=[s for s, _, _ in pairs], n_episodes=len(a), bar_points=bar, mean_points=round(diff, 2),
                ci95_points=[round(100 * lo, 2), round(100 * hi, 2)],
                passes=None if bar is None else bool(diff >= bar and lo > 0),
                per_seed={s: dict(control=pct(x), arm=pct(y), diff=round(pct(y) - pct(x), 2)) for s, x, y in pairs})


BLOCKS = {
    "spatial_main": dict(suite="spatial", arms=("fixed", "nonrec", "shuffled", "onebig"), seeds=(0, 1, 2, 3),
                         name=lambda arm, s: f"a8_spatmain_{arm}_s0" if s == 0 else f"yq_ofts_{arm}_s{s}",
                         claims=[("F1", "n0", "fixed", 3.0), ("F2", "shuffled", "fixed", 3.0),
                                 ("F3", "nonrec", "fixed", 2.0), ("F5", "onebig", "fixed", 2.0)]),
    "goal_main": dict(suite="goal", arms=("fixed", "nonrec", "shuffled", "onebig"), seeds=(0, 1, 2, 3),
                      name=lambda arm, s: f"a8_goalmain_{arm}_s0" if s == 0 else f"yq_oftg_{arm}_s{s}",
                      claims=[("F1", "n0", "fixed", 3.0), ("F2", "shuffled", "fixed", 3.0),
                              ("F3", "nonrec", "fixed", 2.0), ("F5", "onebig", "fixed", 2.0)]),
    "spatial_repair": dict(suite="spatial", arms=("fixed", "full", "meta3"), seeds=(0, 1, 2, 3),
                           name=lambda arm, s: f"a8_spatrep_{arm}_s0" if s == 0 else f"yq_oftsb_{arm}_s{s}",
                           claims=[("FS1", "fixed", "meta3", 3.0), ("FS2", "full", "meta3", None),
                                   ("meta3_vs_n0", "n0", "meta3", None), ("fixedBC_vs_n0", "n0", "fixed", None)]),
    "spatial_long12": dict(suite="spatial", arms=("fixed12", "nonrec12", "onebig12"), seeds=(1, 2, 3),
                           name=lambda arm, s: f"yq_ofts_{arm}_s{s}",
                           claims=[("FL1", "n0", "fixed12", 5.0), ("FL3", "nonrec12", "fixed12", 2.0),
                                   ("FL5", "onebig12", "fixed12", 2.0)]),
    "goal_long12": dict(suite="goal", arms=("fixed12", "nonrec12", "onebig12"), seeds=(1, 2, 3),
                        name=lambda arm, s: f"yq_oftg_{arm}_s{s}",
                        claims=[("FL1", "n0", "fixed12", 5.0), ("FL3", "nonrec12", "fixed12", 2.0),
                                ("FL5", "onebig12", "fixed12", 2.0)]),
    # addendum 32 (blocks added before any of their runs existed; the blocks above are unchanged)
    "goal_guard12": dict(suite="goal", arms=("guard12", "fixed12", "onebig12"), seeds=(1, 2, 3),
                         name=lambda arm, s: f"yq_oftg_{arm}_s{s}",
                         claims=[("G1", "n0", "guard12", 5.0), ("G2", "fixed12", "guard12", 2.0),
                                 ("G3", "onebig12", "guard12", None)]),
    # addendum 35 (blocks added before any evaluation of its runs existed; the blocks above are unchanged): the
    # self-repaired loop continued under tuned RL's counted budget. "ext" is the continued run's retained version at
    # the final read (<run>_fin_fresh) or at the interim read of 2026-11-14 10:00Z (<run>_i14_fresh); "round6" is the
    # same run before the continuation. E1 is read for superiority (CI > 0) and non-inferiority (margin 2).
    "goal_ext": dict(suite="goal", arms=("ext", "onebig12", "onebig", "round6"), seeds=(1, 2, 3), noninf={"E1": -2.0},
                     name=lambda arm, s: {"ext": f"yq_oftgbx_ext_s{s}_fin",
                                          "round6": f"yq_oftgb_llm_harness_s{s}"}.get(arm, f"yq_oftg_{arm}_s{s}"),
                     claims=[("E1", "onebig12", "ext", 0.0), ("E2", "onebig", "ext", 3.0), ("E3", "round6", "ext", None)]),
    "goal_ext_interim": dict(suite="goal", arms=("ext", "onebig12", "onebig", "round6"), seeds=(1, 2, 3),
                             noninf={"E1": -2.0},
                             name=lambda arm, s: {"ext": f"yq_oftgbx_ext_s{s}_i14",
                                                  "round6": f"yq_oftgb_llm_harness_s{s}"}.get(arm, f"yq_oftg_{arm}_s{s}"),
                             claims=[("E1", "onebig12", "ext", 0.0), ("E2", "onebig", "ext", 3.0),
                                     ("E3", "round6", "ext", None)]),
    # addendum 33 (block added before any of its runs existed; the blocks above are unchanged)
    "spatial_guard": dict(suite="spatial", arms=("guard", "onebig", "fixed"), seeds=(1, 2, 3),
                          name=lambda arm, s: f"yq_ofts_{arm}_s{s}", noninf={"GS3": -2.0},
                          claims=[("GS3", "onebig", "guard", 0.0), ("GS2", "fixed", "guard", 2.0),
                                  ("GS1", "n0", "guard", 3.0)]),
    # addendum 33 amendment 1: the Beijing replicate (platform B) and the pooled within-platform GS3. Added before
    # any Beijing result existed. Primary GS3 = spatial_guard_pooled when all six B evaluations exist by
    # 2026-11-15 12:00Z, otherwise spatial_guard (Yangquan alone). No strict-gate arm on B, so no GS2 there.
    "spatial_guard_bj": dict(suite="spatial", arms=("guard", "onebig"), seeds=(1, 2, 3), platforms=("bj",),
                             plat=lambda s: "bj", name=lambda arm, s: f"bj_ofts_{arm}_s{s}", noninf={"GS3": -2.0},
                             claims=[("GS3", "onebig", "guard", 0.0), ("GS1", "n0", "guard", 3.0)]),
    # amendment 2: platform A (the A800 node, seed 0) joins; the pooled block covers every within-platform pair, and
    # --exclude A,B drops a platform that is not complete by 2026-11-15 12:00Z. GS2 has no B pair (no strict arm there).
    # amendment 3: a second A pair (seed 1, no strict-gate arm); --exclude also takes one pair's label (e.g. A1)
    "spatial_guard_a8": dict(suite="spatial", arms=("guard", "onebig", "fixed"), seeds=(0, 1), platforms=("a800",),
                             plat=lambda s: "a800", name=lambda arm, s: f"a8_spatmain_{arm}_s{s}", noninf={"GS3": -2.0},
                             claims=[("GS3", "onebig", "guard", 0.0), ("GS2", "fixed", "guard", 2.0, (0,)),
                                     ("GS1", "n0", "guard", 3.0)]),
    # amendment 4: the primary pools Y1-3 + A0 + A1 only; Beijing (spatial_guard_bj) and A2/A3 (spatial_guard_repl_a8)
    # are replications, each read once on its own and never pooled into the primary
    "spatial_guard_repl_a8": dict(suite="spatial", arms=("guard", "onebig"), seeds=("A2", "A3"), platforms=("a800",),
                                  plat=lambda s: "a800", name=lambda arm, s: GUARD_RUN[s[0]].format(arm=arm, n=s[1:]),
                                  noninf={"GS3": -2.0}, claims=[("GS3", "onebig", "guard", 0.0)]),
    "spatial_guard_pooled": dict(suite="spatial", arms=("guard", "onebig", "fixed"),
                                 seeds=("Y1", "Y2", "Y3", "A0", "A1"), platforms=("yq", "a800"),
                                 plat=lambda s: PLAT_OF[s[0]], name=lambda arm, s: GUARD_RUN[s[0]].format(arm=arm, n=s[1:]),
                                 noninf={"GS3": -2.0},
                                 claims=[("GS3", "onebig", "guard", 0.0),
                                         ("GS2", "fixed", "guard", 2.0, ("Y1", "Y2", "Y3", "A0"))]),
    # addendum 34 amendment 1 (block added before any of its runs existed): Spatial 12 rounds on Yangquan, seeds 1-3
    "spatial_guard12": dict(suite="spatial", arms=("guard12", "fixed12", "onebig12"), seeds=(1, 2, 3),
                            name=lambda arm, s: f"yq_ofts_{arm}_s{s}", noninf={"G3s": -2.0},
                            claims=[("G1s", "n0", "guard12", 5.0), ("G2s", "fixed12", "guard12", 2.0),
                                    ("G3s", "onebig12", "guard12", 0.0)]),
    # addendum 34 (block added before either of its runs existed): Spatial 12 rounds on the A800 node, seed 0, descriptive
    "spatial_long12_a8": dict(suite="spatial", arms=("fixed12", "nonrec12", "onebig12", "guard12"), seeds=(0,),
                              platforms=("a800",), plat=lambda s: "a800", name=lambda arm, s: f"a8_spatmain_{arm}_s{s}",
                              claims=[("FL5_A0", "onebig12", "fixed12", None), ("G3s", "onebig12", "guard12", None),
                                      ("G2s", "fixed12", "guard12", None), ("G1s", "n0", "guard12", None)]),
    "goal_nogate": dict(suite="goal", arms=("nogate", "fixed", "llm_harness"), seeds=(1, 2, 3),
                        name=lambda arm, s: f"yq_oftgb_{arm}_s{s}",
                        claims=[("NG1", "nogate", "fixed", 10.0), ("NG2", "nogate", "llm_harness", 10.0),
                                ("NG3", "n0", "nogate", None)]),
}


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    excl = set()
    if "--exclude" in args:      # addendum 33: platform letters (A, B) left out of a pooled block by the deadline rule
        i = args.index("--exclude"); excl = set(args[i + 1].split(",")); del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    block, root = dict(BLOCKS[args[0]]), (args[1] if len(args) > 1 else "results")
    keep = lambda seeds: tuple(s for s in seeds if not (isinstance(s, str) and (s[0] in excl or s in excl)))
    block["seeds"] = keep(block["seeds"])
    runs = {(arm, s): run_fresh(root, block["name"](arm, s)) for arm in block["arms"] for s in block["seeds"]}
    refs = {p: reference(root, p, block["suite"]) for p in block.get("platforms", ("yq", "a800"))}
    if check:
        for (arm, s), b in sorted(runs.items()):
            print(f"{block['name'](arm, s):30s} fresh evaluation: {'yes, %d episodes' % len(b[1]) if b else 'missing'}")
        print({p: len(v) for p, v in refs.items()}, "reference evaluations")
        return
    digests = {b[0] for b in runs.values() if b} | {e[0] for v in refs.values() for e in v}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    if any(len(b[1]) != N for b in runs.values() if b):
        raise SystemExit("an evaluation does not have 1000 episodes")
    ref = {p: [sum(v) / len(v) for v in zip(*[e[1] for e in evs])] for p, evs in refs.items() if evs}
    plat = block.get("plat", lambda s: "a800" if s == 0 else "yq")
    res = dict(block=args[0], reference={p: dict(evaluations=len(refs[p]), success=pct(r)) for p, r in ref.items()})
    if excl:
        res["excluded_platforms"] = sorted(excl)
    for claim in block["claims"]:
        label, ctrl, arm, bar = claim[:4]
        seeds = keep(claim[4]) if len(claim) > 4 else block["seeds"]   # a claim may cover only some platforms
        pairs = []
        for s in seeds:
            y = runs.get((arm, s))
            x = ref.get(plat(s)) if ctrl == "n0" else (runs.get((ctrl, s)) or [None, None])[1]
            if y and x:
                pairs.append((s, x, y[1]))
        if pairs:
            res[label] = paired(pairs, bar, f"{label} {arm} - {ctrl} (fresh sealed test)")
            res[label]["complete"] = len(pairs) == len(seeds)
            if label in block.get("noninf", {}):   # addendum 33: superiority (CI > 0) and non-inferiority (CI > margin)
                lo = res[label]["ci95_points"][0]
                res[label].update(superior=bool(lo > 0.0), non_inferior_margin=block["noninf"][label],
                                  non_inferior=bool(lo > block["noninf"][label]))
                res[label].pop("passes", None)
        else:
            res[label] = dict(claim=f"{label} {arm} - {ctrl}", missing=True)
    res["noise_reference_halves"] = {}
    for p, evs in refs.items():
        if len(evs) >= 2:
            h = len(evs) // 2
            a = [sum(v) / h for v in zip(*[e[1] for e in evs[:h]])]
            b = [sum(v) / (len(evs) - h) for v in zip(*[e[1] for e in evs[h:]])]
            lo, hi = paired_bootstrap(a, b)
            res["noise_reference_halves"][p] = dict(diff=round(pct(b) - pct(a), 2), ci95=[round(100 * lo, 2), round(100 * hi, 2)])
    res["runs"] = {block["name"](arm, s): (pct(b[1]) if b else None) for (arm, s), b in sorted(runs.items())}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

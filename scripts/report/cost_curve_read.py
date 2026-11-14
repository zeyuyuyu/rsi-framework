"""Addendum 36 (descriptive, no bar): cost curves and three-evaluation fresh finals for the counted-tuning comparison.

Part A  fresh-scene success against cumulative GPU-hours with RL's tuning counted:
        the self-repairing loop (LLM meta level from the failing BC recipe) after rounds 0-6, and one-shot RL on the
        hand-tuned recipe after blocks 0, 6, ..., 36 (seeds 1-3) or 0, 6, 12, 18 (seed 0, and RL-18 on seeds 1-3).
Part B  loop (round-6 version) - RL (18 blocks, retained version) on fresh scenes, each version the per-episode mean
        of three evaluations (the registered one plus <run>_fresh23), beside the one-evaluation estimate.

Costs (results/tuning_cost_20261112.json): loop = the run's reserved card-hours (Yangquan) or backend GPU-hours (A800,
a lower bound) apportioned by the cumulative backend seconds of round-NN.json; RL = 213.4 pilot GPU-hours + the run's
one-card hours apportioned by blocks. Round/block 0 is the initial policy, valued by the platform's pooled reference.

usage: python3 scripts/report/cost_curve_read.py [results root] [--check] [--json out.json]
--check lists which evaluations exist and prints no success number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fresh_read as F   # noqa: E402

PILOTS = 213.4
LOOP = {0: "a8_oftgb_llm_harness_s0", 1: "yq_oftgb_llm_harness_s1", 2: "yq_oftgb_llm_harness_s2", 3: "yq_oftgb_llm_harness_s3"}
RL18 = {0: "a8_goalmain_onebig_s0", 1: "yq_oftg_onebig_s1", 2: "yq_oftg_onebig_s2", 3: "yq_oftg_onebig_s3"}
RL36 = {1: "yq_oftg_onebig12_s1", 2: "yq_oftg_onebig12_s2", 3: "yq_oftg_onebig12_s3"}


def base(root, name):
    return Path(root) / ("a800/runs2" if name.startswith("a8_") else "baidu")


def evals(d):
    """Every fresh evaluation in directory d: [(ids digest, bits), ...]."""
    out = []
    if not d.exists():
        return out
    tests = d / "tests.txt"
    if tests.exists():
        for line in open(tests):
            p = line.split()
            if len(p) == 5 and p[0] == "TESTBITS" and p[1].startswith("test-libero_fresh-"):
                out.append((p[3], [int(c) for c in p[4]]))
    if not out:
        import hashlib
        for f in sorted(d.glob("test-libero_fresh-*-rep*.jsonl")):
            recs = [json.loads(l) for l in open(f) if l.strip()]
            out.append((hashlib.sha256(json.dumps([r["id"] for r in recs]).encode()).hexdigest()[:16],
                        [1 if r["score"] >= 0.5 else 0 for r in recs]))
    return out


def round_head(f):
    """round-NN.json: one JSON object (A800) or JSON lines whose first line is the round (Yangquan sync)."""
    text = Path(f).read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text.splitlines()[0])


def mean_bits(ev):
    return [sum(col) / len(col) for col in zip(*[b for _, b in ev])]


def curve_last_node(acc):
    """The run's retained version: the last accepted node (read in its registered <run>_fresh evaluation)."""
    return acc[max(acc)] if acc else "n0"


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = Path(args[0] if args else "results")
    cost = json.load(open(root / "tuning_cost_20261112.json"))
    loop_hours = dict(cost["meta_level_card_hours"]["yangquan_cards_x_job_time"])
    loop_hours = {int(k[1]): v for k, v in loop_hours.items()}
    loop_hours[0] = cost["meta_level_card_hours"]["a800_s0_gpu_seconds_last_session"]
    rl18_h = {int(k[1]): v for k, v in cost["wall_clock_hours"]["one_shot_rl"].items()}
    rl36_h = {int(k[1]): v for k, v in cost["wall_clock_hours"]["one_shot_rl_36_steps"].items()}
    ref = {p: F.reference(root, p, "goal") for p in ("yq", "a800")}
    digests, missing, res = set(), [], {"note": "addendum 36; descriptive, no bar", "partA": {}, "partB": {}}

    def point(d, reuse=None):
        ev = evals(d)
        if not ev:
            missing.append(str(d.relative_to(root)))
            return None
        digests.update(x for x, _ in ev)
        return ev[:1]

    for s in (0, 1, 2, 3):
        plat = "a800" if s == 0 else "yq"
        start = None if check else round(100 * sum(sum(b) for _, b in ref[plat]) / sum(len(b) for _, b in ref[plat]), 2)
        run = LOOP[s]; d = base(root, run) / run
        acc = {json.loads(l)["round"]: json.loads(l)["node"] for l in open(d / "accepted.jsonl") if l.strip()}
        secs = {r: sum(round_head(d / f"round-{r:02d}.json")["seconds"].values()) for r in range(1, 7)}
        node, curve, seen = "n0", [(0.0, start, "n0")], {}
        for r in range(1, 7):
            node = acc.get(r, node)
            x = round(loop_hours[s] * secs[r] / secs[6], 1)
            if node == "n0":
                curve.append((x, start, node)); continue
            if node not in seen:
                retained6 = r == 6 or node == curve_last_node(acc)
                seen[node] = point(base(root, run) / (f"{run}_fresh" if retained6 else f"{run}_cc_{node}"))
            ev = seen[node]
            curve.append((x, None if (ev is None or check) else F.pct(ev[0][1]), node))
        # round 6's version is the run's retained version, read in its registered <run>_fresh evaluation
        res["partA"][f"loop_s{s}"] = curve
        for name, runs, hours, blocks in (("rl18", RL18, rl18_h, 18), ("rl36", RL36, rl36_h, 36)):
            if s not in runs:
                continue
            rr = runs[s]; c = [(PILOTS, start, "n0")]
            for k in range(6, blocks + 1, 6):
                x = round(PILOTS + hours[s] * k / blocks, 1)
                if k == blocks:
                    if name == "rl18" and s == 1:     # the gate refused r01c0; its trajectory ends at the candidate
                        ev = point(base(root, rr) / f"{rr}_cc_r01c0"); nd = "r01c0 (ungated)"
                    else:
                        ev = point(base(root, rr) / f"{rr}_fresh"); nd = "retained"
                elif name == "rl36" or s == 0:
                    nd = f"r01c0-i{k - 1}"; ev = point(base(root, rr) / f"{rr}_cc_{nd}")
                else:
                    continue
                c.append((x, None if (ev is None or check) else F.pct(ev[0][1]), nd))
            res["partA"][f"{name}_s{s}"] = c
    # Part B
    pairs1, pairs3 = [], []
    for s in (0, 1, 2, 3):
        L, R = LOOP[s], RL18[s]
        lv = evals(base(root, L) / f"{L}_fresh")[:1] + evals(base(root, L) / f"{L}_fresh23")
        rv = evals(base(root, R) / f"{R}_fresh")[:1] + evals(base(root, R) / f"{R}_fresh23")
        res["partB"][f"evaluations_s{s}"] = dict(loop=len(lv), rl18=len(rv))
        digests.update(x for x, _ in lv + rv)
        if lv and rv:
            pairs1.append((s, rv[0][1], lv[0][1]))
        if len(lv) == 3 and len(rv) == 3:
            pairs3.append((s, mean_bits(rv), mean_bits(lv)))
        else:
            missing.append(f"partB s{s}: loop {len(lv)}/3, rl18 {len(rv)}/3")
    if len(digests) > 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    res["missing"] = missing
    if check:
        print(json.dumps(dict(missing=missing, partB=res["partB"]), indent=1))
        return
    for label, pairs in (("one_evaluation", pairs1), ("three_evaluations", pairs3)):
        for seeds in ((1, 2, 3), (0, 1, 2, 3)):
            ps = [p for p in pairs if p[0] in seeds]
            if len(ps) == len(seeds):
                res["partB"][f"{label}_s{''.join(map(str, seeds))}"] = F.paired(ps, None,
                    f"loop round 6 - one-shot RL 18 blocks, fresh scenes, {label.replace('_', ' ')}, seeds {seeds}")
    print(json.dumps(res, indent=1))
    if out:
        Path(out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

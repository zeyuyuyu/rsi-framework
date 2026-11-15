"""Addendum 37 (descriptive): three-evaluation fresh finals for addendum 35's E1/E2, cost-curve points of the continued
loop, and seed 0 continued on the A800 node.

  A  E1 ext - RL 36 blocks and E2 ext - RL 18 blocks on fresh scenes, each version the per-episode mean of three
     evaluations: ext = <run>_fin_fresh (registered) + <run>_fresh23; RL-36 = yq_oftg_onebig12_s<n>_fresh + _fresh23;
     RL-18 = yq_oftg_onebig_s<n>_fresh + _fresh23 (addendum 36). Seeds 1-3, beside the one-evaluation reads.
  B  fresh score of each cost-curve point yq_oftgbx_ext_s<n>_cc_<node> (one evaluation).
  C  seed 0 (A800): a8_oftgbx_ext_s0_fin_rep (official, three) and _fin_fresh (fresh, three) against
     a8_goalmain_onebig_s0 (official three-evaluation final; fresh = _fresh + _fresh23).
usage: python3 scripts/report/addendum37_read.py [results root] [--check] [--json out.json]
--check lists what exists and prints no success number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fresh_read as F           # noqa: E402
import cost_curve_read as C      # noqa: E402


def official(d):
    """Official-test evaluations in d: TESTBITS lines of tests.txt (Yangquan extract), else the A800 per-episode
    files test-libero_official-<node>-rep<k>.jsonl (episode order as written; digest as rsi.audit.compare_arms)."""
    out = []
    t = d / "tests.txt"
    if t.exists():
        for line in open(t):
            p = line.split()
            if len(p) == 5 and p[0] == "TESTBITS" and p[1].startswith("test-libero_official-"):
                out.append((p[3], [int(c) for c in p[4]]))
    if not out and d.exists():
        from rsi.audit.compare_arms import _digest
        for f in sorted(d.glob("test-libero_official-*-rep*.jsonl")):
            recs = [json.loads(l) for l in open(f) if l.strip()]
            out.append((_digest([r["id"] for r in recs]), [1 if r["score"] >= 0.5 else 0 for r in recs]))
    return out


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    root = Path(args[0] if args else "results"); Y = root / "baidu"; A = root / "a800" / "runs2"
    res, missing, digests = {"note": "addendum 37; descriptive"}, [], set()

    def three(*dirs):
        ev = []
        for d in dirs:
            got = C.evals(d)
            ev += got if d.name.endswith("fresh23") else got[:1]
        return ev
    sets = {}
    for s in (1, 2, 3):
        ext = three(Y / f"yq_oftgbx_ext_s{s}_fin_fresh", Y / f"yq_oftgbx_ext_s{s}_fresh23")
        r36 = three(Y / f"yq_oftg_onebig12_s{s}_fresh", Y / f"yq_oftg_onebig12_s{s}_fresh23")
        r18 = three(Y / f"yq_oftg_onebig_s{s}_fresh", Y / f"yq_oftg_onebig_s{s}_fresh23")
        sets[s] = dict(ext=ext, rl36=r36, rl18=r18)
        for k, v in sets[s].items():
            digests.update(x for x, _ in v)
            if len(v) != 3: missing.append(f"A s{s} {k}: {len(v)}/3")
    res["A_evaluations"] = {f"s{s}": {k: len(v) for k, v in d.items()} for s, d in sets.items()}
    cc = sorted(Y.glob("yq_oftgbx_ext_s*_cc_*"))
    res["B_points"] = {d.name: (None if check or not C.evals(d) else F.pct(C.evals(d)[0][1])) for d in cc}
    rep0 = A / "a8_oftgbx_ext_s0_fin_rep_b"   # requeued under _b after the first launch landed on another session's GPU (ops note)
    e0r, e0f = official(rep0 if rep0.exists() else A / "a8_oftgbx_ext_s0_fin_rep"), C.evals(A / "a8_oftgbx_ext_s0_fin_fresh")
    r0f = three(A / "a8_goalmain_onebig_s0_fresh", A / "a8_goalmain_onebig_s0_fresh23")
    res["C_evaluations"] = dict(ext_official=len(e0r), ext_fresh=len(e0f), rl18_fresh=len(r0f))
    for k, n, need in (("C ext official", len(e0r), 3), ("C ext fresh", len(e0f), 3), ("C rl18 fresh", len(r0f), 3)):
        if n != need: missing.append(f"{k}: {n}/{need}")
    res["missing"] = missing
    if check:
        print(json.dumps(res, indent=1)); return
    if len(digests) > 1:
        raise SystemExit(f"fresh episode lists differ: {sorted(digests)}")
    ok = [s for s in (1, 2, 3) if all(len(v) == 3 for v in sets[s].values())]
    if len(ok) == 3:
        res["A_E1_three_evaluations"] = F.paired([(s, C.mean_bits(sets[s]["rl36"]), C.mean_bits(sets[s]["ext"])) for s in ok], None,
                                                 "E1 ext - RL 36 blocks, fresh scenes, three evaluations each, seeds 1-3")
        res["A_E2_three_evaluations"] = F.paired([(s, C.mean_bits(sets[s]["rl18"]), C.mean_bits(sets[s]["ext"])) for s in ok], None,
                                                 "E2 ext - RL 18 blocks, fresh scenes, three evaluations each, seeds 1-3")
    if len(e0f) == 3 and len(r0f) == 3:
        res["C_fresh"] = F.paired([(0, C.mean_bits(r0f), C.mean_bits(e0f))], None, "seed 0 ext - RL 18 blocks, fresh, three evaluations")
    if len(e0r) == 3:
        import goal_read as G
        G.MODE = "final"
        rl0 = G.record(A / "a8_goalmain_onebig_s0")
        if {dg for dg, _ in e0r} != {rl0["digest"]}:
            raise SystemExit(f"seed 0 official episode lists differ: {sorted({dg for dg, _ in e0r})} vs {rl0['digest']}")
        res["C_official"] = G.paired([(0, rl0["bits"], C.mean_bits(e0r))], 0.0, "seed 0 ext - RL 18 blocks, official, three evaluations")
        res["C_official"].pop("passes", None)
    print(json.dumps(res, indent=1))
    if out:
        Path(out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

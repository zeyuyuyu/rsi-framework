"""Addendum 35: the official-test reads of the self-repaired LIBERO-Goal loop continued under tuned RL's counted budget
(yq_oftgbx_ext_s<seed>, Yangquan seeds 1-3). The fresh-scene test is primary (fresh_read.py goal_ext / goal_ext_interim);
this is the official test beside it.

The continued run's final is the per-episode mean of the three evaluations of its retained version in
<run>_fin_rep (final read) or <run>_i14_rep (interim read, the version retained at 2026-11-14 10:00Z). The comparison
arms' finals are their registered three-evaluation finals, read earlier:
    E1  ext - yq_oftg_onebig12 (tuned one-shot RL, 36 steps): CI reported; superior if CI > 0, non-inferior if > -2
    E2  ext - yq_oftg_onebig   (tuned one-shot RL, 18 steps): >= +3.0, CI > 0
    E3  ext - yq_oftgb_llm_harness (the same run at round 6): CI reported
usage: python3 scripts/report/goal_ext_read.py <final|interim> [results root] [--check] [--json out.json]
--check prints readiness and no test number."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_read as G                                  # noqa: E402

SEEDS = (1, 2, 3)
TAG = {"final": "fin", "interim": "i14"}


def ext_record(d):
    """Three official evaluations of one node in an evaluation-only run dir -> (node, digest, mean bits, n)."""
    tests = d / "tests.txt"
    if not tests.exists():
        return None
    evals = {}
    for line in open(tests):
        p = line.split()
        if len(p) == 5 and p[0] == "TESTBITS" and p[1].startswith("test-libero_official-") and "-rep" in p[1]:
            node = p[1][len("test-libero_official-"):].rsplit("-rep", 1)[0]
            evals.setdefault(node, []).append((p[3], [int(c) for c in p[4]]))
    if len(evals) != 1:
        raise SystemExit(f"{d.name}: expected evaluations of one node, found {sorted(evals)}")
    node, lists = next(iter(evals.items()))
    if len(lists) != 3 or len({dg for dg, _ in lists}) != 1:
        raise SystemExit(f"{d.name}: the registered final needs 3 evaluations of {node} on one episode list, found {len(lists)}")
    return dict(node=node, digest=lists[0][0], bits=G.mean_bits([b for _, b in lists]), n_evals=3)


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if not args or args[0] not in TAG:
        raise SystemExit(__doc__)
    read, root = args[0], Path(args[1] if len(args) > 1 else "results")
    G.MODE = "final"
    base = root / "baidu"
    ext = {s: ext_record(base / f"yq_oftgbx_ext_s{s}_{TAG[read]}_rep") for s in SEEDS}
    if check:
        for s in SEEDS:
            e = ext[s]
            print(f"yq_oftgbx_ext_s{s}_{TAG[read]}_rep: " + (f"node {e['node']}, {e['n_evals']} evaluations" if e else "missing"))
        return
    if not all(ext.values()):
        raise SystemExit(f"{read} read: evaluations missing for seeds {[s for s in SEEDS if not ext[s]]}")
    arms = dict(onebig12="yq_oftg_onebig12", onebig="yq_oftg_onebig", round6="yq_oftgb_llm_harness")
    runs = {(k, s): G.record(base / f"{n}_s{s}") for k, n in arms.items() for s in SEEDS}
    digests = {r["digest"] for r in runs.values()} | {e["digest"] for e in ext.values()}
    if len(digests) != 1:
        raise SystemExit(f"episode id lists differ: {sorted(digests)}")
    pair = lambda ctrl: [(s, runs[(ctrl, s)]["bits"], ext[s]["bits"]) for s in SEEDS]
    res = {"mode": dict(read=read, nodes={s: ext[s]["node"] for s in SEEDS})}
    res["E1"] = G.paired(pair("onebig12"), 0.0, "E1 continued loop - tuned one-shot RL, 36 steps (official test)")
    lo = res["E1"]["ci95_points"][0]
    res["E1"].update(superior=bool(lo > 0.0), non_inferior_margin=-2.0, non_inferior=bool(lo > -2.0))
    res["E1"].pop("passes", None)
    res["E2"] = G.paired(pair("onebig"), 3.0, "E2 continued loop - tuned one-shot RL, 18 steps (official test)")
    res["E3"] = G.paired(pair("round6"), 0.0, "E3 continued loop - the same run at round 6 (official test)")
    res["E3"].pop("passes", None)
    res["finals"] = {s: dict(ext=G.pct(ext[s]["bits"]), onebig12=G.pct(runs[("onebig12", s)]["bits"]),
                             onebig=G.pct(runs[("onebig", s)]["bits"]), round6=G.pct(runs[("round6", s)]["bits"]))
                     for s in SEEDS}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

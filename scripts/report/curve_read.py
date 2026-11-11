"""Addendum 13: the read of an always-accept GRPO curve run (gate and audit sets only; the official test stays sealed).

D = mean pooled success S over rounds 5-6 minus the run's own n0, where S pools the 200 gate and 200 audit sampled
placements (the same ids at every node). Paired placement bootstrap, 10,000 draws: one draw of the 400 placements is
applied to n0, r05 and r06 alike. Splits: gate only, audit only, r05 only, r06 only. Bar (addendum 13): D >= +3.
Input: the NODEBITS lines of scripts/baidu/pfs_nodebits.sh for one run (results/a800/nodebits/<run>.txt).
usage: python3 scripts/report/curve_read.py <nodebits file> [--accepted accepted.jsonl] [--json out.json]"""
import json
import random
import sys
from pathlib import Path

DRAWS, SEED = 10000, 0


def load(path):
    bits, ids = {}, {}
    for line in open(path):
        p = line.split()
        if len(p) >= 7 and p[0] == "NODEBITS":
            node, kind, n, digest, b = p[2], p[3], int(p[4]), p[5], p[6]
            assert len(b) == n, (node, kind)
            bits[(node, kind)] = [int(c) for c in b]
            ids.setdefault(kind, set()).add(digest)
    for kind, d in ids.items():
        if len(d) != 1:
            raise SystemExit(f"{kind} placement ids differ across nodes: {sorted(d)}")
    return bits


def boot(a, b):
    """mean(b - a) with a 10k-draw bootstrap over cases: (point, lo, hi, P(D <= 0))."""
    diffs = [y - x for x, y in zip(a, b)]
    n, rng = len(diffs), random.Random(SEED)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(DRAWS))
    point = sum(diffs) / n
    return dict(D_points=round(100 * point, 2), ci95_points=[round(100 * means[int(0.025 * DRAWS)], 2),
                                                             round(100 * means[int(0.975 * DRAWS) - 1], 2)],
                p_le_0=round(sum(1 for m in means if m <= 0) / DRAWS, 4), episodes=n)


def main():
    args = sys.argv[1:]
    out = acc = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    if "--accepted" in args:
        i = args.index("--accepted"); acc = args[i + 1]; del args[i:i + 2]
    bits = load(args[0])
    nodes = sorted({n for n, _ in bits}, key=lambda n: (n != "n0", n))
    table = {n: dict(gate=sum(bits[(n, "gate")]), audit=sum(bits[(n, "audit")]),
                     S=round((sum(bits[(n, "gate")]) + sum(bits[(n, "audit")])) / 400, 4)) for n in nodes}
    if acc:   # every node's counts must match the run's own summaries
        for line in open(acc):
            r = json.loads(line)
            t = table[r["node"]]
            if abs(t["gate"] / 200 - r["gate"]) > 1e-9 or abs(t["audit"] / 200 - r["audit"]) > 1e-9:
                raise SystemExit(f"{r['node']}: nodebits {t} do not match accepted.jsonl {r}")
    pooled = lambda n: bits[(n, "gate")] + bits[(n, "audit")]
    late = lambda sel: [(x + y) / 2 for x, y in zip(sel("r05c0"), sel("r06c0"))]
    res = dict(table=table, D=boot(pooled("n0"), late(pooled)), bar_points=3.0)
    res["passes_bar"] = bool(res["D"]["D_points"] >= 3.0)
    res["gate_only"] = boot(bits[("n0", "gate")], late(lambda n: bits[(n, "gate")]))
    res["audit_only"] = boot(bits[("n0", "audit")], late(lambda n: bits[(n, "audit")]))
    res["r05_only"] = boot(pooled("n0"), pooled("r05c0"))
    res["r06_only"] = boot(pooled("n0"), pooled("r06c0"))
    res["flips_vs_n0"] = {f"{n} {k}": dict(up=sum(1 for x, y in zip(bits[("n0", k)], bits[(n, k)]) if y > x),
                                           down=sum(1 for x, y in zip(bits[("n0", k)], bits[(n, k)]) if y < x))
                          for n in ("r05c0", "r06c0") for k in ("gate", "audit")}
    text = json.dumps(res, indent=1)
    print(text)
    if out:
        Path(out).write_text(text + "\n")


if __name__ == "__main__":
    main()

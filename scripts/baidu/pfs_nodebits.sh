#!/bin/bash
# Print per-node greedy gate/audit episode bits of robotics runs on PFS, read from the run's .work call dirs
# (the run dir itself only holds summaries). Node = the call spec's adapter dir name (n0 when no adapter); a
# later call for the same node and set replaces an earlier one. One line per (node, set):
#   NODEBITS <run> <node> <gate|audit> <n> <ids sha256[:16]> <bits in sorted-id order>
# env: RUNS="run_dir_name ..." under /mnt/pfs/shitianyu-rsi/runs
for r in $RUNS; do
  w=/mnt/pfs/shitianyu-rsi/runs/$r.work
  echo "== $r: $(ls $w 2>&1 | wc -l) calls"
  python3 - "$w" "$r" <<'PY'
import glob, hashlib, json, os, sys
w, r = sys.argv[1], sys.argv[2]
by = {}
for d in sorted(os.listdir(w)):
    specs = sorted(glob.glob(os.path.join(w, d, "spec-*.json")))
    if not specs:
        continue
    spec = json.load(open(specs[0]))
    ad = spec.get("adapter") or spec.get("lora") or None
    node = "n0" if not ad else os.path.basename(str(ad).rstrip("/")).replace("ckpt-", "")
    recs = {}
    for f in glob.glob(os.path.join(w, d, "episodes", "results-*.jsonl")):
        for line in open(f):
            if not line.strip():
                continue
            x = json.loads(line)
            if x.get("mode") != "greedy":
                continue
            kind = "gate" if "-gate" in x["id"] else ("audit" if "-audit" in x["id"] else None)
            if kind:
                recs.setdefault(kind, {})[x["id"]] = 1 if x.get("success") or (x.get("score") or 0) >= 0.5 else 0
    for kind, m in recs.items():
        by[(node, kind)] = (d, m)
for (node, kind), (d, m) in sorted(by.items()):
    ids = sorted(m)
    h = hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16]
    print("NODEBITS", r, node, kind, len(ids), h, "".join(str(m[i]) for i in ids), "call=" + d)
PY
done
echo PFS_NODEBITS_DONE

#!/bin/bash
# Print the meta-LLM record of llm / llm_harness runs: every meta-llm.jsonl line (keys, then each value cut to
# MAXV chars) plus the run's program files, so a harness edit can be traced to the field the LLM changed and its
# stated reason. Read-only.
# env: RUNS="run ..." under RUNROOT (default /mnt/pfs/shitianyu-rsi/runs), MAXV (default 1200)
ROOT=${RUNROOT:-/mnt/pfs/shitianyu-rsi/runs}
for r in $RUNS; do
  d=$ROOT/$r
  echo "== $r: $(ls $d 2>&1 | tr '\n' ' ')"
  python3 - "$d" "$r" "${MAXV:-1200}" <<'PY'
import glob, json, os, sys
d, r, maxv = sys.argv[1], sys.argv[2], int(sys.argv[3])
m = os.path.join(d, "meta-llm.jsonl")
if os.path.exists(m):
    for i, line in enumerate(open(m)):
        try:
            c = json.loads(line)
        except ValueError:
            continue
        print("METAKEYS", r, i, sorted(c))
        for k, v in c.items():
            print("METAVAL", r, i, k, json.dumps(v, ensure_ascii=False)[:maxv])
for f in sorted(glob.glob(os.path.join(d, "program*.json*")) + glob.glob(os.path.join(d, "programs", "*"))):
    print("PROGRAM", r, os.path.basename(f), open(f, errors="replace").read()[:maxv].replace("\n", " "))
PY
done
echo PFS_METALLM_DONE

"""Cost (x) of the continued loop's versions for the cost figure (addenda 35-37): round-6 reserved card-hours plus
one card x (time the round's last training block finished - continuation job created). The round end is taken as the
first backend call after the round's final RECEIPT (its gate evaluation). Fresh score = the version's one fresh evaluation.
usage: python3 scripts/report/ext_cost_points.py [results root]   (fetches the two job logs; writes results/ext_cost_points_20261115.json)"""
import json, re, subprocess, sys, datetime
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results"
sys.path.insert(0, str(REPO / "scripts" / "report"))
import cost_curve_read as C, fresh_read as F
RUNS = {1: dict(job="job-btajrg01bzcz", created="2026-11-13T00:53:11Z", c6=89.6, nodes={"r09c0": "yq_oftgbx_ext_s1_i14_fresh", "r11c0": "yq_oftgbx_ext_s1_cc_r11c0", "r12c0": "yq_oftgbx_ext_s1_cc_r12c0", "r13c0": "yq_oftgbx_ext_s1_fin_fresh"}),
        2: dict(job="job-939pnipsdu7k", created="2026-11-13T00:16:33Z", c6=206.0, nodes={"r07c0": "yq_oftgbx_ext_s2_cc_r07c0", "r08c0": "yq_oftgbx_ext_s2_fin_fresh"}),
        3: dict(job="job-jr8hv88w0cl4", created="2026-11-13T01:35:19Z", c6=58.8, nodes={"r07c0": "yq_oftgbx_ext_s3_fin_fresh"})}
ts = lambda t: datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
out = {}
for s, r in RUNS.items():
    log = subprocess.run([sys.executable, str(REPO / "scripts/baidu/yqlog.py"), r["job"], r"RECEIPT ckpt-r\d+c\d+ |latest call: \d+-[a-z_]+-\d+", "100000"],
                         capture_output=True, text=True, timeout=600).stdout.splitlines()
    ends, pending = {}, None
    for line in log:
        m = re.search(r"RECEIPT ckpt-(r\d+c\d+) ", line)
        if m: pending = m.group(1); continue
        m = re.search(r"latest call: \d+-[a-z_]+-(\d+)", line)
        if m and pending and pending not in ends: ends[pending] = int(m.group(1)); pending = None
    pts = []
    for node, d in r["nodes"].items():
        ev = C.evals(root / "baidu" / d)
        if node not in ends or not ev: continue
        pts.append(dict(node=node, x_gpu_hours=round(r["c6"] + (ends[node] - ts(r["created"])) / 3600, 1), success_pct=F.pct(ev[0][1]), source=d))
    out[f"s{s}"] = sorted(pts, key=lambda p: p["x_gpu_hours"])
(root / "ext_cost_points_20261115.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))

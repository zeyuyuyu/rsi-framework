"""Cost (x) of the versions kept under addendum 38 for the cost figure, same rule as ext_cost_points.py: GPU-hours spent
before this addendum's job + cards x (time the round's gate evaluation started - job created). The final version sits
at the run's total cost (results/mb_costs_20261116.json). Fresh score = the version's one fresh evaluation (cc_ run;
the final version's registered fin_fresh evaluation).
usage: python3 scripts/report/mb_cost_points.py   (fetches the job log; writes results/mb_cost_points_20261116.json)"""
import json, re, subprocess, sys, datetime
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
root = REPO / "results"
sys.path.insert(0, str(REPO / "scripts" / "report"))
import cost_curve_read as C, fresh_read as F
RUNS = {1: dict(job="job-lni873lelr1q", created="2026-11-15T09:19:30Z", c0=144.5, cards=8,
                nodes={"r14c0": "yq_oftgbx_mb_s1_cc_r14c0", "r15c0": "yq_oftgbx_mb_s1_cc_r15c0"},
                final=("r16c0", "yq_oftgbx_mb_s1_fin_fresh"))}
ts = lambda t: datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
costs = json.loads((root / "mb_costs_20261116.json").read_text())
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
        if node in ends and ev:
            pts.append(dict(node=node, x_gpu_hours=round(r["c0"] + r["cards"] * (ends[node] - ts(r["created"])) / 3600, 1),
                            success_pct=F.pct(ev[0][1]), source=d))
    node, d = r["final"]
    ev = C.evals(root / "baidu" / d)
    pts.append(dict(node=node, x_gpu_hours=costs[f"s{s}"]["total"], success_pct=F.pct(ev[0][1]), source=d, final=True))
    out[f"s{s}"] = sorted(pts, key=lambda p: p["x_gpu_hours"])
(root / "mb_cost_points_20261116.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))

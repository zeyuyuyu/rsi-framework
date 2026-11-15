"""Supplementary table: per-seed results of the counted-tuning comparison on LIBERO-Goal (Finding 6), from the records.
Fresh scenes (1,000, one evaluation per version, registered) and official test (500, three evaluations per version);
cost = total reserved GPU-hours, RL's 213.4 pilot hours included.
Sources: results/fresh_goal_ext_final_20261115.json (fresh E1/E2), results/goal_ext_read_final_20261115.txt (official),
results/ext_cost_points_20261115.json (loop totals), results/cost_curve_read_20261114.json (RL totals).
usage: python3 scripts/report/supp_cost_per_seed.py   -> paper/cvpr2027/supp/tab_cost_per_seed.tex"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
J = lambda n: json.loads((R / "results" / n).read_text())
fresh, offi = J("fresh_goal_ext_final_20261115.json"), J("goal_ext_read_final_20261115.txt")
ext, cc = J("ext_cost_points_20261115.json"), J("cost_curve_read_20261114.json")["partA"]
seeds = ("1", "2", "3")
rows, acc = [], {k: [] for k in ("lc", "lf", "lo", "c18", "f18", "o18", "c36", "f36", "o36")}
for s in seeds:
    v = dict(lc=ext["totals"][f"s{s}"], lf=fresh["E2"]["per_seed"][s]["arm"], lo=offi["E2"]["per_seed"][s]["arm"],
             c18=cc[f"rl18_s{s}"][-1][0], f18=fresh["E2"]["per_seed"][s]["control"], o18=offi["E2"]["per_seed"][s]["control"],
             c36=cc[f"rl36_s{s}"][-1][0], f36=fresh["E1"]["per_seed"][s]["control"], o36=offi["E1"]["per_seed"][s]["control"])
    for k in acc: acc[k].append(v[k])
    rows.append((s, v))
mean = {k: sum(x) / len(x) for k, x in acc.items()}
fmt = lambda v: (f"{v['lc']:.0f} & {v['lf']:.1f} / {v['lo']:.1f} & {v['c18']:.0f} & {v['f18']:.1f} / {v['o18']:.1f} & "
                 f"${v['lf'] - v['f18']:+.1f}$ & {v['c36']:.0f} & {v['f36']:.1f} / {v['o36']:.1f} & ${v['lf'] - v['f36']:+.1f}$")
lines = [r"\begin{center}\footnotesize\setlength{\tabcolsep}{3pt}",
         r"\resizebox{\linewidth}{!}{%",
         r"\begin{tabular}{@{}lrrrrrrrr@{}}", r"\toprule",
         r" & \multicolumn{2}{c}{RSI loop} & \multicolumn{3}{c}{tuned RL, 18 blocks} & \multicolumn{3}{c}{RL, 36 blocks} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-9}",
         r"seed & GPU-h & fresh / official & GPU-h & fresh / official & $\Delta$ fresh & GPU-h & fresh / official & $\Delta$ fresh \\",
         r"\midrule"]
lines += [f"{s} & {fmt(v)} \\\\" for s, v in rows]
lines += [r"\midrule", f"mean & {fmt(mean)} \\\\", r"\bottomrule", r"\end{tabular}}", r"\end{center}",
          "Success in \\%; GPU-hours include RL's 213 pilot hours. The loop's version is the one each run retained when it stopped "
          "(addendum 35). Seed 3's gate refused its candidates in rounds 8--10, so it kept its round-7 version; on one card it "
          "had spent 112 of its 239 GPU-hours when its time limit stopped it. Addendum 38 continues seeds 1 and 3 up to RL's budget."]
out = R / "paper/cvpr2027/supp/tab_cost_per_seed.tex"
out.write_text("\n".join(lines) + "\n")
print(out.read_text())

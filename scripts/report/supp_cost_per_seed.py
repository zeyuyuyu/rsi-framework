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
seeds = ("1", "2")   # seed 3's continuation excluded (addendum 39)
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
          "(addendum 35). The third registered seed's continuation is excluded: in its first round its practice success fell "
          "from 58\\% to 32\\%, and to 10\\% in the next round, while its retained policy still scored 65\\% on validation; "
          "seeds 1 and 2 show no such drop. Addendum 38 continues seed 1 up to RL's budget."]
a37 = J("addendum37_read_20261116.json")   # seed 0 on the second platform (A800), addendum 37 part C
if "C_fresh" in a37 and "C_official" in a37:
    cf, co = a37["C_fresh"]["per_seed"]["0"], a37["C_official"]["per_seed"]["0"]
    lines.append(f" Seed 0 on the second platform (A800), continued the same way: against its tuned RL run (18 blocks), "
                 f"{cf['arm']:.1f} vs {cf['control']:.1f} on the fresh scenes (${a37['C_fresh']['mean_points']:+.1f}$ "
                 f"$[{a37['C_fresh']['ci95_points'][0]:+.1f}, {a37['C_fresh']['ci95_points'][1]:+.1f}]$) and "
                 f"{co['arm']:.1f} vs {co['control']:.1f} on the official test, three evaluations per version.")
a38f = R / "results" / "addendum38_read_20261116.json"   # addendum 38: continued to about RL's GPU budget
if a38f.exists():
    a38, mbc = json.loads(a38f.read_text()), J("mb_costs_20261116.json")
    m2, m2o = a38["M2_fresh"], a38.get("M2_official", {})
    lines += ["", r"\paragraph{At about the same total GPU-hours (addendum 38).}",
              r"\begin{center}\footnotesize\setlength{\tabcolsep}{4pt}",
              r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
              r"seed & RSI GPU-h & RSI fresh / official & RL-18 GPU-h & RL-18 fresh / official & $\Delta$ fresh \\", r"\midrule"]
    for s_ in seeds:
        f, o = m2["per_seed"][s_], m2o.get("per_seed", {}).get(s_, {})
        tot = mbc[f"s{s_}"]["total"]
        lines.append(f"{s_} & {tot:.0f} & {f['arm']:.1f} / {o.get('arm', float('nan')):.1f} & {cc[f'rl18_s{s_}'][-1][0]:.0f} & "
                     f"{f['control']:.1f} / {o.get('control', float('nan')):.1f} & ${f['diff']:+.1f}$ \\\\")
    lines += [r"\midrule", f"average & & & & & ${m2['mean_points']:+.1f}$ $[{m2['ci95_points'][0]:+.1f}, {m2['ci95_points'][1]:+.1f}]$ \\\\",
              r"\bottomrule", r"\end{tabular}", r"\end{center}",
              "Each run continued with its program fixed up to about its RL budget; the version each run retained when it stopped. "
              "Fresh scenes, one evaluation per version (registered); seed-averaged paired bootstrap."]
out = R / "paper/cvpr2027/supp/tab_cost_per_seed.tex"
out.write_text("\n".join(lines) + "\n")
print(out.read_text())

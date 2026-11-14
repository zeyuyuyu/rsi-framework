"""Write the numbers behind every data figure and table of the CVPR draft to figures/data/*.csv.

Reads the same run records and read outputs as paper/cvpr2027/fig/make_figs.py, so a redrawn figure shows exactly
the paper's numbers. Re-run after any new read:  python3 figures/export_figure_data.py"""
import csv
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "figures", "data")
R = lambda p: os.path.join(ROOT, "results", p)


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def chain(path):
    """Gate success (%) of the retained version after rounds 0..6, and which rounds accepted a new version."""
    g = {c["round"]: c["gate"] for c in json.load(open(path))["accepted_chain"]}
    out, cur = [], g[0]
    for k in range(7):
        cur = g.get(k, cur); out.append(round(cur * 100, 1))
    return out, [k for k in range(1, 7) if k in g]


def ci_row(name, sub, r, source):
    return [name, sub, r["mean_points"], r["ci95_points"][0], r["ci95_points"][1], source]


# Figure 1 (b): the BC recipe with every version accepted (A800 seed 1) and under the gate (Yangquan seeds 1-3)
rows = []
y, _ = chain(R("a800/runs2/a8_oftg_curve_bc_s1/report.json"))
rows += [["every version accepted", "A800 s1", k, v] for k, v in enumerate(y)]
for s in (1, 2, 3):
    y, _ = chain(R(f"baidu/yq_oftgb_fixed_s{s}/report.json"))
    rows += [["gated", f"Yangquan s{s}", k, v] for k, v in enumerate(y)]
write("fig1b_gate_vs_always_accept.csv", ["condition", "run", "round", "held_out_gate_success_pct"], rows)

# Figure 1 (c): effects on sealed tests (points, 95% CI)
sp = json.load(open(R("fresh_spatial_main_20261111.json"))); rep = json.load(open(R("selfrepair_read_20261109.json")))
write("fig1c_effects.csv", ["effect", "comparison", "mean_points", "ci_low", "ci_high", "source"], [
    ci_row("RSI loop", "vs its start (LIBERO-Spatial, 1,000 unseen scenes)", sp["F1"], "fresh_spatial_main_20261111.json F1"),
    ci_row("verifier", "real vs shuffled labels (Spatial, unseen scenes)", sp["F2"], "fresh_spatial_main_20261111.json F2"),
    ci_row("recursion", "vs practice from the frozen initial policy (Spatial, unseen scenes)", sp["F3"], "fresh_spatial_main_20261111.json F3"),
    ci_row("meta level", "vs gate alone, failing recipe (LIBERO-Goal, official test)", rep["S1_seeds0to3"], "selfrepair_read_20261109.json S1")])

# Figure 3: gate success of the retained policy by round, loop and its two controls, both suites (Yangquan seeds 1-3)
rows = []
for suite, prefix in (("LIBERO-Goal", "yq_oftg"), ("LIBERO-Spatial", "yq_ofts")):
    for arm in ("fixed", "nonrec", "shuffled"):
        for s in (1, 2, 3):
            p = R(f"baidu/{prefix}_{arm}_s{s}/report.json")
            if os.path.exists(p):
                y, acc = chain(p)
                rows += [[suite, arm, s, k, v, int(k in acc)] for k, v in enumerate(y)]
write("fig3_gate_curves.csv", ["suite", "arm", "seed", "round", "gate_success_pct", "new_version_accepted"], rows)

# Figure 4: self-repair study at the gate (LIBERO-Goal, failing BC recipe)
rows = []
for c in sorted(json.load(open(R("a800/runs2/a8_oftg_curve_bc_s1/report.json")))["accepted_chain"], key=lambda c: c["round"]):
    rows.append(["always accept (no gate)", "A800 s1", c["round"], round(c["gate"] * 100, 1), round(c["audit"] * 100, 1)])
for arm in ("fixed", "full", "llm_harness"):
    for s, p in [(s, R(f"baidu/yq_oftgb_{arm}_s{s}/report.json")) for s in (1, 2, 3)] + [(0, R(f"a800/runs2/a8_oftgb_{arm}_s0/report.json"))]:
        if os.path.exists(p):
            y, _ = chain(p)
            rows += [[arm, f"s{s}", k, v, ""] for k, v in enumerate(y)]
write("fig4_selfrepair_gate.csv", ["arm", "seed", "round", "gate_success_pct", "audit_success_pct"], rows)

# Figure 5: train-on-test inflation (LIBERO-10)
d = json.load(open(R("train_on_test_inflation_20261030.json")))
rows = [["cell", ck, key, d["cells"][ck][key]] for ck in ("sft", "rl") for key in ("official", "fresh")]
rows += [["rl_per_task", f"task {t}", key, v] for key in ("official", "fresh") for t, v in enumerate(d["rl_per_task"][key])]
write("fig5_inflation.csv", ["kind", "policy_or_task", "placement_set", "success_pct"], rows)

# Table 1 as printed in the paper (parsed from the LaTeX so it is exactly the published row)
tex = open(os.path.join(ROOT, "paper/cvpr2027/sec/4_setup.tex")).read()
body = tex[tex.index("\\label{tab:long}"):tex.index("\\end{tabular}")]
num = lambda c: re.findall(r"[+-]?\d+\.\d+|--", c)
rows = []
for line in body.split("\\midrule")[1].split("\\\\"):
    cells = [c.strip() for c in line.split("&")]
    if len(cells) < 7:
        continue
    name = re.sub(r"\\texttt\{([^}]*)\}|\$[^$]*\$", lambda m: m.group(1) or "-", cells[0]).replace("\\", "").strip()
    vals = [num(c) for c in (cells[2], cells[3], cells[5], cells[6])]
    flat = [x for v in vals for x in (v + ["", "", ""])[:3]] if all(v != ["--"] for v in vals) else \
        [x for v in vals for x in ((v + ["", "", ""])[:3] if v != ["--"] else ["", "", ""])]
    bold = ["boldmath" in c for c in (cells[2], cells[3], cells[5], cells[6])]
    rows.append([name, re.sub(r"[${}^\\dagger]", "", cells[1]).strip()] + flat + bold)
write("tab1_effects.csv", ["comparison", "bar", "goal_official_mean", "goal_official_ci_low", "goal_official_ci_high",
                           "goal_fresh_mean", "goal_fresh_ci_low", "goal_fresh_ci_high", "spatial_official_mean",
                           "spatial_official_ci_low", "spatial_official_ci_high", "spatial_fresh_mean", "spatial_fresh_ci_low",
                           "spatial_fresh_ci_high", "goal_official_bar_met", "goal_fresh_bar_met", "spatial_official_bar_met",
                           "spatial_fresh_bar_met"], rows)

# Counted-tuning comparison (Finding 6): per seed success and cost
tc = json.load(open(R("tuning_cost_20261112.json"))); ts = json.load(open(R("tuning_cost_spatial_20261114.json")))
rows = []
for test, key in (("official", "M_vs_RL_official"), ("fresh", "M_vs_RL_fresh_4seed")):
    for s, v in tc[key]["per_seed"].items():
        rows.append(["LIBERO-Goal", test, s, v["arm"], v["control"], v["diff"]])
for test, key in (("official", "official_s0123"), ("fresh", "fresh_s0123")):
    for s, v in ts[key]["per_seed"].items():
        rows.append(["LIBERO-Spatial", test, s, v["arm"], v["control"], v["diff"]])
write("finding6_counted_tuning_per_seed.csv", ["suite", "test", "seed", "rsi_loop_pct", "tuned_rl_pct", "difference_points"], rows)
rows = [["LIBERO-Goal", t, tc[k]["mean_points"], *tc[k]["ci95_points"], k] for t, k in (("official (seeds 0-3)", "M_vs_RL_official"), ("fresh (seeds 1-3)", "M_vs_RL_fresh"), ("fresh (seeds 0-3)", "M_vs_RL_fresh_4seed"))]
rows += [["LIBERO-Spatial", t, ts[k]["mean_points"], *ts[k]["ci95_points"], k] for t, k in (("official (seeds 0-3)", "official_s0123"), ("fresh (seeds 0-3)", "fresh_s0123"))]
write("finding6_counted_tuning_summary.csv", ["suite", "test", "rsi_minus_tuned_rl_points", "ci_low", "ci_high", "source_key"], rows)
cost = [["RL recipe pilots (21 runs, LIBERO-Goal)", "", tc["pilots"]["gpu_hours_on_record"], "charged to RL on both suites"]]
cost += [["one-shot RL, 18 blocks (own training)", s, h, "one card"] for s, h in tc["wall_clock_hours"]["one_shot_rl"].items()]
cost += [["one-shot RL, 36 blocks (own training)", s, h, "one card"] for s, h in tc["wall_clock_hours"]["one_shot_rl_36_steps"].items()]
cost += [["RSI self-repair, LIBERO-Goal (reserved card-hours)", s, h, "Yangquan, resumed on 3 cards"] for s, h in tc["meta_level_card_hours"]["yangquan_cards_x_job_time"].items()]
cost += [["RSI self-repair, LIBERO-Goal (A800, lower bound)", "s0", tc["meta_level_card_hours"]["a800_s0_gpu_seconds_last_session"], "backend GPU-hours"]]
cost += [["RSI meta level, LIBERO-Spatial (wall-clock, two cards)", s, h, "x2 cards"] for s, h in ts["wall_clock_hours"]["meta_level"].items()]
cost += [["one-shot RL, LIBERO-Spatial (own training)", s, h, "one card"] for s, h in ts["wall_clock_hours"]["one_shot_rl"].items()]
write("finding6_costs_gpu_hours.csv", ["item", "seed", "gpu_hours", "note"], cost)

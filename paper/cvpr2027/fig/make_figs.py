"""Figures for the CVPR 2027 draft, all from released run records. Run from the repository root:
    python paper/cvpr2027/fig/make_figs.py
Writes PDFs next to this file."""
import glob
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
C = {"fixed": "#1f77b4", "full": "#ff7f0e", "llm": "#2ca02c", "llm_harness": "#2ca02c", "llm_harness_cap": "#17becf",
     "nonrec": "#9467bd", "shuffled": "#d62728", "onebig": "#8c564b"}


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- 1. forest plot of the registered claims
def fig_claims():
    d = json.load(open(os.path.join(ROOT, "results/goal_read_final_20261106.json")))
    m2 = json.load(open(os.path.join(ROOT, "results/m2_read_20261104.json")))
    m2c = json.load(open(os.path.join(ROOT, "results/m2_cavin_read_20261106.json")))
    rows = [("R1  fixed $-$ ref. (Y, seeds 1-3)", d["R1_fixed"], 5),
            ("R1  full $-$ ref. (Y, seeds 1-3)", d["R1_full"], 5),
            ("R2  fixed $-$ shuffled (Y, 0-3)", d["R2_seeds0to3"], 3),
            ("R3  fixed $-$ nonrec (Y, 0-3)", d["R3_seeds0to3"], 2),
            ("R4  full $-$ fixed (Y)", d["R4_full_minus_fixed"], 2),
            ("R4  llm_harness $-$ fixed (Y)", d["R4_harness_minus_fixed_yq"], 2),
            ("R4  llm $-$ fixed (A)", d["R4_llm_minus_fixed_cavin"], 2),
            ("R4  llm_harness_cap $-$ fixed (A)", d["R4_cap_minus_fixed_cavin"], 2),
            ("R5  best gated $-$ onebig (Y, 0-3)", d["R5_seeds0to3"], 2),
            ("M2-A  llm $-$ replica, v2 (Y)", m2[0], 3),
            ("M2-A  llm $-$ replica, v2 (A)", m2c[0], 3),
            ("noise  n0 half $-$ half (Y)", {"mean_points": d["noise_check_n0_halves"]["yq"]["diff_points"], "ci95_points": d["noise_check_n0_halves"]["yq"]["ci95"]}, None)]
    rows = [r for r in rows if r[1] is not None]
    fig, ax = plt.subplots(figsize=(3.4, 3.3))
    ys = list(range(len(rows)))[::-1]
    for y, (label, r, bar) in zip(ys, rows):
        m, (lo, hi) = r["mean_points"], r["ci95_points"]
        ax.plot([lo, hi], [y, y], color="0.3", lw=1.2)
        ax.plot(m, y, "o", color="black", ms=4)
        if bar is not None:
            ax.plot(bar, y, "|", color="#d62728", ms=9, mew=1.5)
    ax.axvline(0, color="0.6", lw=0.8, ls="--")
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("points (95% CI); red tick = preregistered bar")
    ax.set_xlim(-3.5, 6.5)
    save(fig, "fig_claims.pdf")


# ---------------------------------------------------------------- 2. every run: n0 -> replicate-averaged final
def fig_runs():
    d = json.load(open(os.path.join(ROOT, "results/goal_read_final_20261106.json")))["runs"]
    ref = {"yq": 58.92, "cavin": 58.44, "cavin_s0": 58.44}
    order = ["fixed", "full", "llm_harness", "llm", "llm_harness_cap", "nonrec", "shuffled", "onebig"]
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    x = 0
    ticks, labels = [], []
    for plat in ["yq", "cavin", "cavin_s0"]:
        runs = d.get(plat, {})
        for arm in order:
            names = sorted(n for n in runs if re.match(arm + r"_s\d$", n))
            if not names:
                continue
            for n in names:
                r = runs[n]
                ax.plot([x, x], [r["n0"], r["test"]], color=C.get(arm, "k"), lw=1, alpha=0.6)
                ax.plot(x, r["n0"], "_", color="0.5", ms=6)
                ax.plot(x, r["test"], "o", color=C.get(arm, "k"), ms=3.5)
                x += 1
            ticks.append(x - (len(names) + 1) / 2)
            labels.append(arm.replace("llm_harness_cap", "cap").replace("llm_harness", "harness") + ("\n(A, s0)" if plat == "cavin_s0" else "\n(A)" if plat == "cavin" else "\n(Y)"))
            x += 1.2 if plat != "cavin_s0" else 2.2
    ax.axhline(58.92, color="0.6", lw=0.8, ls="--")
    ax.axhline(58.44, color="0.6", lw=0.8, ls=":")
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=6.5, rotation=30, ha="right")
    ax.set_ylabel("official test success (%)")
    ax.set_ylim(53, 64)
    ax.text(0.2, 63.6, "dashed: pooled initial reference (Y 58.9); dotted: (A 58.4).  grey tick: the run's own n0 test;  dot: replicate-averaged final", fontsize=6.5, va="top")
    save(fig, "fig_runs.pdf")


# ---------------------------------------------------------------- 3. retained-gate trajectories on LIBERO-Goal (Y)
def chain(path):
    r = json.load(open(path))
    ch = r["accepted_chain"]
    g = {c["round"]: c["gate"] for c in ch}
    out, cur = [], g[0]
    for k in range(0, 7):
        cur = g.get(k, cur)
        out.append(cur * 100)
    return out


def fig_gates():
    arms = ["fixed", "full", "llm_harness", "nonrec", "shuffled"]
    fig, axes = plt.subplots(1, 5, figsize=(7.0, 1.7), sharey=True)
    for ax, arm in zip(axes, arms):
        ys = []
        for s in (1, 2, 3):
            p = os.path.join(ROOT, f"results/baidu/yq_oftg_{arm}_s{s}/report.json")
            if not os.path.exists(p):
                continue
            y = chain(p)
            ys.append(y)
            ax.plot(range(7), y, color=C[arm], lw=0.8, alpha=0.45)
        if ys:
            mean = [sum(v[k] for v in ys) / len(ys) for k in range(7)]
            ax.plot(range(7), mean, color=C[arm], lw=2)
        ax.set_title(arm, fontsize=8)
        ax.set_xlabel("round")
        ax.set_xticks(range(0, 7, 2))
    axes[0].set_ylabel("gate of retained\nversion (%)")
    save(fig, "fig_gates.pdf")


# ---------------------------------------------------------------- 4. self-repair: collapse without the gate vs gated arms
def fig_selfrepair():
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 1.8), sharey=True)
    # panel 0: always-accept BC curve (no gate), A800 seed 1
    ax = axes[0]
    g, a = [58.5], [58.5]
    for l in open(os.path.join(ROOT, "results/a800/runs2/a8_oftg_curve_bc_s1/accepted.jsonl")):
        r = json.loads(l)
        g.append(r["gate"] * 100)
        a.append(r["audit"] * 100)
    ax.plot(range(7), g, "-o", color="#d62728", ms=3, label="gate")
    ax.plot(range(7), a, "--s", color="#d62728", ms=3, alpha=0.6, label="audit")
    ax.set_title("same BC recipe, no gate", fontsize=8)
    ax.legend(frameon=False)
    ax.set_ylabel("success on held-out\nplacements (%)")
    for ax, arm, title in zip(axes[1:], ["fixed", "full", "llm_harness"], ["fixed (gate only)", "full (numeric search)", "llm_harness"]):
        for s in (1, 2, 3):
            p = os.path.join(ROOT, f"results/baidu/yq_oftgb_{arm}_s{s}/report.json")
            if os.path.exists(p):
                ax.plot(range(7), chain(p), "-", color=C[arm], lw=1.2, alpha=0.8, label=f"Y s{s}")
        p = os.path.join(ROOT, f"results/a800/runs2/a8_oftgb_{arm}_s0/report.json")
        if os.path.exists(p):
            ax.plot(range(7), chain(p), "--", color="black", lw=1.0, alpha=0.8, label="A s0")
        ax.set_title(title, fontsize=8)
        ax.legend(frameon=False, fontsize=5.5)
    for ax in axes:
        ax.set_xlabel("round")
        ax.set_xticks(range(0, 7, 2))
    axes[0].set_ylim(0, 70)
    save(fig, "fig_selfrepair.pdf")


# ---------------------------------------------------------------- 5. code world models
def fig_code():
    cells = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results/claims_*.json"))):
        d = json.load(open(f))
        for c in d["claims"]:
            cells.append((d["model"], d["suite"], d["study"], c["claim"], c["mean_points"], c["ci95_points"], len(c["seeds"])))
    want = [("q15", "cruxeval_o", "main", "C1 fixed: final - initial", "1.5B fixed"),
            ("q15", "cruxeval_o", "main", "C1 shuffled: final - initial", "1.5B shuffled"),
            ("q15", "cruxeval_o", "main", "C2 fixed - shuffled", "1.5B fixed$-$shuffled"),
            ("q15", "cruxeval_o", "long8", "C3 fixed - nonrec", "1.5B fixed$-$nonrec, 8 rds"),
            ("q7b", "cruxeval_o", "long8", "C3 fixed - nonrec", "7B fixed$-$nonrec, 8 rds"),
            ("q7b", "lcb_exec", "main", "C1 fixed: final - initial", "7B fixed (LCB-exec)"),
            ("q7b", "lcb_exec", "long8", "C3 fixed - nonrec", "7B fixed$-$nonrec, 8 rds (LCB)"),
            ("qw3", "cruxeval_i", "main", "C1 fixed: final - initial", "Qwen3-8B fixed (CRUX-I)"),
            ("g8b", "cruxeval_i", "main", "C1 fixed: final - initial", "Granite-8B fixed (CRUX-I)")]
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ys, labels = [], []
    for i, (model, suite, study, claim, label) in enumerate(want):
        hit = [c for c in cells if c[0] == model and c[1] == suite and c[2] == study and c[3] == claim]
        if not hit:
            continue
        _, _, _, _, m, (lo, hi), ns = hit[0]
        y = -len(ys)
        ys.append(y)
        labels.append(label + ("" if ns >= 3 else " ($n$=%d)" % ns))
        col = "#d62728" if "shuffled" in claim and "fixed" not in claim else ("#9467bd" if "nonrec" in claim else "#1f77b4")
        ax.barh(y, m, color=col, alpha=0.75, height=0.6)
        ax.plot([lo, hi], [y, y], color="black", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.axvline(0, color="0.5", lw=0.8)
    ax.set_xlabel("points on the held-out test (CRUXEval-O unless noted), 95% CI")
    save(fig, "fig_code.pdf")


# ---------------------------------------------------------------- 6. train-on-test inflation
def fig_inflation():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.4, 1.9), gridspec_kw={"width_ratios": [1, 2.2]})
    off = [14.6, 87.4]
    fresh = [20.0, 76.0]
    x = [0, 1]
    a1.bar([i - 0.18 for i in x], off, width=0.36, color="#d62728", label="official states")
    a1.bar([i + 0.18 for i in x], fresh, width=0.36, color="#1f77b4", label="fresh placements")
    a1.set_xticks(x)
    a1.set_xticklabels(["SFT start", "RL ckpt"])
    a1.set_ylabel("LIBERO-10 success (%)")
    a1.legend(frameon=False, fontsize=6, loc="upper left")
    off_t = [78, 84, 98, 88, 80, 96, 90, 86, 82, 92]
    fresh_t = [62, 68, 92, 92, 52, 90, 50, 84, 84, 86]
    xt = list(range(10))
    a2.bar([i - 0.2 for i in xt], off_t, width=0.4, color="#d62728")
    a2.bar([i + 0.2 for i in xt], fresh_t, width=0.4, color="#1f77b4")
    a2.set_xticks(xt)
    a2.set_xticklabels([f"t{i}" for i in xt], fontsize=6)
    a2.set_title("RL checkpoint, per task", fontsize=8)
    a2.set_ylim(0, 100)
    save(fig, "fig_inflation.pdf")


if __name__ == "__main__":
    fig_claims()
    fig_runs()
    fig_gates()
    fig_selfrepair()
    fig_code()
    fig_inflation()

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



# ---------------------------------------------------------------- 0. teaser: safety (left) + registered claims (right)
def fig_teaser():
    d = json.load(open(os.path.join(ROOT, "results/goal_read_final_20261106.json")))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.3), gridspec_kw={"width_ratios": [1, 1.5]})
    g = [58.5]
    for l in open(os.path.join(ROOT, "results/a800/runs2/a8_oftg_curve_bc_s1/accepted.jsonl")):
        g.append(json.loads(l)["gate"] * 100)
    a1.plot(range(7), g, "-o", color="#d62728", ms=3.5, lw=2, label="same recipe, no gate")
    for s in (1, 2, 3):
        pth = os.path.join(ROOT, f"results/baidu/yq_oftgb_fixed_s{s}/report.json")
        if os.path.exists(pth):
            a1.plot(range(7), chain(pth), "-", color="#1f77b4", lw=1.3, alpha=0.8, label="with the gate" if s == 1 else None)
    a1.set_xlabel("round"); a1.set_ylabel("held-out success (%)"); a1.set_ylim(0, 72); a1.legend(frameon=False, fontsize=7, loc="lower left")
    a1.set_title("(a) the gate makes the loop safe", fontsize=8)
    rows = [("loop (fixed $-$ start)", d["R1_fixed"], 5), ("verifier (fixed $-$ shuffled)", d["R2_seeds0to3"], 3),
            ("recursion (fixed $-$ nonrec)", d["R3_seeds0to3"], 2), ("meta: numeric $-$ fixed", d["R4_full_minus_fixed"], 2),
            ("meta: LLM $-$ fixed", d["R4_harness_minus_fixed_yq"], 2), ("meta: LLM+cap $-$ fixed (A)", d["R4_cap_minus_fixed_cavin"], 2),
            ("loop $-$ one-shot RL", d["R5_seeds0to3"], 2)]
    ys = list(range(len(rows)))[::-1]
    for y, (label, r, bar) in zip(ys, rows):
        m, (lo, hi) = r["mean_points"], r["ci95_points"]
        a2.plot([lo, hi], [y, y], color="0.3", lw=1.3); a2.plot(m, y, "o", color="black", ms=4)
        a2.plot(bar, y, "|", color="#d62728", ms=10, mew=1.6)
    a2.axvline(0, color="0.6", lw=0.8, ls="--")
    a2.set_yticks(ys); a2.set_yticklabels([r[0] for r in rows], fontsize=7)
    a2.set_xlabel("points of test success (95% CI); red tick = preregistered bar", fontsize=7); a2.set_xlim(-3.2, 6.2)
    a2.set_title("(b) which part of the loop helps (LIBERO-Goal, 31 runs)", fontsize=8)
    fig.tight_layout()
    save(fig, "fig_teaser.pdf")

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
            labels.append(arm.replace("llm_harness_cap", "cap").replace("llm_harness", "harness") + ("\n(A s0)" if plat == "cavin_s0" else "\n(A)" if plat == "cavin" else "\n(Y)"))
            x += 1.2 if plat != "cavin_s0" else 3.2
    ax.axhline(58.92, color="0.6", lw=0.8, ls="--")
    ax.axhline(58.44, color="0.6", lw=0.8, ls=":")
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=6.5)
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
            ("q15", "cruxeval_o", "long8", "C3 fixed - nonrec", "1.5B fixed$-$nonrec\n8 rounds"),
            ("q7b", "cruxeval_o", "long8", "C3 fixed - nonrec", "7B fixed$-$nonrec\n8 rounds"),
            ("q7b", "lcb_exec", "main", "C1 fixed: final - initial", "7B fixed\nLCB-exec"),
            ("q7b", "lcb_exec", "long8", "C3 fixed - nonrec", "7B fixed$-$nonrec\n8 rounds, LCB"),
            ("qw3", "cruxeval_i", "main", "C1 fixed: final - initial", "Qwen3-8B fixed\nCRUX-I"),
            ("g8b", "cruxeval_i", "main", "C1 fixed: final - initial", "Granite-8B fixed\nCRUX-I")]
    # the figure is included at one column width: draw it at that physical width (no tight box), so the label
    # font is the printed font (the tight box had been scaled down to about 4 pt)
    fig, ax = plt.subplots(figsize=(3.3, 3.0))
    fig.subplots_adjust(left=0.37, right=0.98, bottom=0.15, top=0.99)
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
    ax.set_yticklabels(labels, fontsize=7, linespacing=0.95)
    ax.axvline(0, color="0.5", lw=0.8)
    ax.set_xlabel("points on the held-out test (95% CI)")
    fig.savefig(os.path.join(HERE, "fig_code.pdf"))
    plt.close(fig)
    print("wrote", "fig_code.pdf")


# ---------------------------------------------------------------- 6. train-on-test inflation
def fig_inflation():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.4, 1.9), gridspec_kw={"width_ratios": [1, 2.2]})
    off = [14.6, 87.4]
    fresh = [20.0, 76.0]
    x = [0, 1]
    a1.bar([i - 0.18 for i in x], off, width=0.36, color="#d62728", label="official states")
    a1.bar([i + 0.18 for i in x], fresh, width=0.36, color="#1f77b4", label="fresh placements")
    a1.set_xticks(x)
    a1.set_xticklabels(["SFT\nstart", "RL\nckpt"])
    a1.set_ylabel("LIBERO-10 success (%)")
    a1.set_ylim(0, 100)
    off_t = [78, 84, 98, 88, 80, 96, 90, 86, 82, 92]
    fresh_t = [62, 68, 92, 92, 52, 90, 50, 84, 84, 86]
    xt = list(range(10))
    a2.bar([i - 0.2 for i in xt], off_t, width=0.4, color="#d62728")
    a2.bar([i + 0.2 for i in xt], fresh_t, width=0.4, color="#1f77b4")
    a2.set_xticks(xt)
    a2.set_xticklabels([f"t{i}" for i in xt], fontsize=6)
    a2.set_xlabel("RL checkpoint, per task")
    a2.set_ylim(0, 100)
    fig.legend(loc="upper center", ncol=2, frameon=False, fontsize=7, bbox_to_anchor=(0.5, 1.06))
    save(fig, "fig_inflation.pdf")


# ---------------------------------------------------------------- framework diagram (replaces the TikZ figure; matplotlib only)
def fig_framework():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(11.8, 5.0))
    ax.set_xlim(-4.3, 19.3); ax.set_ylim(-4.15, 4.45); ax.axis("off")
    OBJ, GATE, META, CTRL = "#eef2fb", "#fdecec", "#eaf6ea", "#fffbe6"

    def box(x, y, w, h, text, fc, fs=9, bold_first=True, ha="center", **kw):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=fc, ec="black", lw=0.9, zorder=2))
        if bold_first:
            first, _, rest = text.partition("\n")
            ax.text(x, y + (0.19 if rest else 0), first, ha="center", va="center", fontsize=fs, weight="bold", zorder=3)
            if rest:
                ax.text(x, y - 0.21, rest, ha="center", va="center", fontsize=fs - 0.5, zorder=3, linespacing=1.15)
        else:
            ax.text(x, y, text, ha=ha, va="center", fontsize=fs, zorder=3, linespacing=1.3, **kw)

    def arrow(p, q, dashed=False, lw=1.3):
        ax.annotate("", xy=q, xytext=p, zorder=1,
                    arrowprops=dict(arrowstyle="-|>", lw=lw, color="black", ls="--" if dashed else "-",
                                    mutation_scale=12, shrinkA=0, shrinkB=0))

    def poly(pts, dashed=False, lw=1.3):
        for a, b in zip(pts[:-2], pts[1:-1]):
            ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=lw, ls="--" if dashed else "-", zorder=1)
        arrow(pts[-2], pts[-1], dashed=dashed, lw=lw)

    # object level
    H = 0.95
    stages = [(0.0, 2.6, "Propose\nfresh scenes"), (3.3, 2.6, "Attempt\n$K$ tries at $T$"),
              (6.9, 3.3, "Verify\noracle success flag"), (10.8, 3.7, "Curate\nmixed groups / verified"),
              (14.8, 3.6, "Update\nLoRA: GRPO / BC / SFT")]
    for x, w, t in stages:
        box(x, 3.0, w, H, t, OBJ)
    for (x1, w1, _), (x2, w2, _) in zip(stages[:-1], stages[1:]):
        arrow((x1 + w1 / 2, 3.0), (x2 - w2 / 2, 3.0))
    ax.text(7.2, 3.95, "object level: one inner step, three per round, candidate $\\theta'$ from the retained $\\theta^*$",
            ha="center", va="center", fontsize=9, style="italic")

    # gate / audit / test
    box(10.6, 1.0, 5.4, 1.0, "Gate: 200 fresh paired placements\naccept iff gate$(\\theta') \\geq$ gate$(\\theta^*)$", GATE, fs=9)
    box(14.7, 1.0, 2.4, 1.0, "Audit (200)\nnever decides", GATE)
    box(17.6, 1.0, 2.8, 1.0, "Test (official 500)\nsealed, read once", "#f8caca")
    poly([(14.8, 2.52), (14.8, 2.05), (10.6, 2.05), (10.6, 1.5)])
    ax.text(12.8, 1.85, "candidate $\\theta'$", ha="center", va="top", fontsize=7.5)
    arrow((13.3, 1.0), (13.5, 1.0), dashed=True)
    arrow((15.9, 1.0), (16.2, 1.0), dashed=True)
    # recursion loop back to Propose
    poly([(7.9, 1.0), (-2.2, 1.0), (-2.2, 3.0), (-1.3, 3.0)])
    ax.text(-2.45, 2.0, "retained $\\theta^*$:\nthe next round\npractises with it\n(recursion)", ha="right", va="center",
            fontsize=7.5, linespacing=1.25)

    # meta level
    box(1.9, -1.0, 4.6, 1.0, "Program $P$ (JSON)\ncurriculum / solver / curation / update", META)
    box(9.4, -1.0, 6.6, 1.0, "Meta proposer: fixed $\\cdot$ numeric search $\\cdot$ LLM\nreads gate records (never audit or test)", META)
    arrow((6.1, -1.0), (4.2, -1.0))
    ax.text(5.15, -0.72, "$c{-}1$ edited\ncopies", ha="center", va="bottom", fontsize=7.5, linespacing=1.1)
    poly([(1.9, -0.5), (1.9, 0.2), (3.3, 0.2), (3.3, 2.52)])
    ax.text(3.45, 1.3, "sets every knob of the loop", ha="left", va="bottom", fontsize=7.5)
    poly([(10.6, 0.5), (10.6, 0.15), (9.4, 0.15), (9.4, -0.5)], dashed=True)
    ax.text(9.55, -0.17, "gate record", ha="left", va="center", fontsize=7.5)
    ax.text(6.5, -2.05, "meta level: the program is versioned; a program is kept only when its child wins the gate",
            ha="center", va="center", fontsize=9, style="italic")

    # controls strip
    ax.add_patch(FancyBboxPatch((-4.0, -3.95), 22.9, 1.3, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=CTRL, ec="black", lw=0.9, zorder=2))
    ax.text(-3.8, -3.3, "Controls,\none switch each:", fontsize=9, weight="bold", ha="left", va="center", zorder=3, linespacing=1.2)
    ax.text(-0.9, -3.05, "$\\mathtt{nonrec}$ = propose with the initial $\\theta_0$;   $\\mathtt{shuffled}$ = permute the success labels;   "
            "$\\mathtt{onebig}$ = one round with the full budget;", fontsize=8.5, ha="left", va="center", zorder=3)
    ax.text(-0.9, -3.55, "$\\mathtt{fixed}$ / $\\mathtt{full}$ / $\\mathtt{llm}$ = meta proposer off / numeric search / LLM.",
            fontsize=8.5, ha="left", va="center", zorder=3)
    fig.subplots_adjust(0, 0, 1, 1)
    save(fig, "fig_framework.pdf")


if __name__ == "__main__":
    fig_teaser()
    fig_claims()
    fig_runs()
    fig_gates()
    fig_selfrepair()
    fig_code()
    fig_inflation()
    fig_framework()

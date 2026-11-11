"""Figures for the CVPR 2027 draft. Every data figure is drawn by this script from the run records under results/;
no measured number is typed in here. Run from the repository root:
    python paper/cvpr2027/fig/make_figs.py            # writes the PDFs next to this file
    python paper/cvpr2027/fig/make_figs.py --check    # redraws into a temporary folder and compares with the PDFs here
The PDFs carry no timestamp, so the same records and the same matplotlib give the same bytes."""
import glob
import json
import os
import re
import sys
import tempfile
from decimal import Decimal, ROUND_HALF_UP

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = HERE

# ---------------------------------------------------------------- style shared by every figure
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#8a8983", "#e9e8e3", "#b5b4ae"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
    "mathtext.bf": "Liberation Sans:bold", "mathtext.tt": "Liberation Mono", "mathtext.cal": "Liberation Sans:italic",
    "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "legend.handlelength": 1.8, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    "pdf.fonttype": 42,
    # the layout engine fills the canvas, so a figure drawn 7 in wide is printed at its drawn size and font
    "figure.constrained_layout.use": True, "figure.constrained_layout.w_pad": 0.03,
    "figure.constrained_layout.h_pad": 0.03, "figure.constrained_layout.wspace": 0.03,
    "figure.constrained_layout.hspace": 0.02,
})
# One colour per arm, the same in every figure. The order is the palette's validated order (adjacent colours stay
# apart under protan/deutan simulation); arms are always drawn in this order and always carry a text label too.
ARMS = ["fixed", "full", "llm_harness", "llm_harness_cap", "llm", "onebig", "nonrec", "shuffled"]
C = dict(zip(ARMS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]))
TITLE = {"fixed": "Gated loop", "full": "+ meta: numeric", "llm_harness": "+ meta: LLM",
         "nonrec": "No recursion", "shuffled": "Verifier removed"}
RING = dict(mec="white", mew=0.7)           # white ring keeps a marker readable where it crosses a line
REF = dict(color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)   # a reference level (not a grid line)


def save(fig, name, tight=True):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight" if tight else None, pad_inches=0.02,
                metadata={"CreationDate": None})
    plt.close(fig)
    print("wrote", name)


def ygrid(ax):
    ax.grid(axis="y")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def panel_title(ax, title, code=None):
    """Bold plain-language title, with the arm's name in the paper under it."""
    ax.set_title(title, loc="left", fontweight="bold", pad=12 if code else 4)
    if code:
        ax.annotate(code, (0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points",
                    ha="left", va="bottom", fontsize=6.5, color=MUTED, family="Liberation Mono")


def chain(path):
    """Gate score (%) of the retained version after rounds 0..6, and the rounds in which a new version was accepted."""
    g = {c["round"]: c["gate"] for c in json.load(open(path))["accepted_chain"]}
    out, cur = [], g[0]
    for k in range(0, 7):
        cur = g.get(k, cur)
        out.append(cur * 100)
    return out, [k for k in range(1, 7) if k in g]


def read_final():
    return json.load(open(os.path.join(ROOT, "results/goal_read_final_20261106.json")))


# ---------------------------------------------------------------- 0. teaser (one column): real attempts + the safety result
def fig_teaser():
    """(a) two practice attempts of the initial policy on one LIBERO-Spatial placement, frames as the policy saw them
    (frames/frames.json says where they come from); (b) the BC recipe with and without the gate (LIBERO-Goal)."""
    meta = json.load(open(os.path.join(HERE, "frames", "frames.json")))
    fig = plt.figure(figsize=(3.3, 3.42), layout="none")
    gs = fig.add_gridspec(2, 4, hspace=0.06, wspace=0.04, left=0.075, right=0.995, top=0.885, bottom=0.515)
    gp = fig.add_gridspec(1, 1, left=0.115, right=0.43, top=0.385, bottom=0.095)
    gc = fig.add_gridspec(1, 1, left=0.69, right=0.975, top=0.385, bottom=0.095)
    fig.text(0.01, 0.985, "(a) Practice: the policy’s own attempts, labelled by the simulator", ha="left", va="top",
             fontsize=7.5, fontweight="bold")
    fig.text(0.01, 0.945, f"“{meta['task']}”", ha="left", va="top", fontsize=6.2, color=INK2, style="italic")
    fig.text(0.01, 0.912, "one practice placement, two attempts by the initial policy", ha="left", va="top",
             fontsize=6.2, color=INK2)
    for row, ep in enumerate(meta["episodes"]):
        good = ep["success"]
        for k, f in enumerate(ep["files"]):
            ax = fig.add_subplot(gs[row, k])
            ax.imshow(plt.imread(os.path.join(HERE, "frames", f)), interpolation="lanczos")
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(True); sp.set_color("white"); sp.set_linewidth(0.6)
            if k == 0:
                ax.set_ylabel("success" if good else "failure", fontsize=7, color=INK, labelpad=2)
            if k == 3:
                txt = f"{ep['steps']} steps" if good else f"time limit ({ep['steps']} steps)"
                ax.text(0.96, 0.05, txt, transform=ax.transAxes, ha="right", va="bottom", fontsize=5.2, color="white",
                        fontweight="bold", bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.3",
                                                     fc="#1f8a4c" if good else "#c4314b", ec="none"))
    # (b) the gate: same recipe with and without it
    ax = fig.add_subplot(gp[0, 0])
    nogate, _ = chain(os.path.join(ROOT, "results/a800/runs2/a8_oftg_curve_bc_s1/report.json"))
    ygrid(ax)
    for sd in (1, 2, 3):
        pth = os.path.join(ROOT, f"results/baidu/yq_oftgb_fixed_s{sd}/report.json")
        if os.path.exists(pth):
            ax.plot(range(7), chain(pth)[0], "-", color=C["fixed"], lw=1.1)
    ax.plot(range(7), nogate, "-o", color=INK, ms=3.0, lw=1.4, **RING)
    ax.text(6.1, 64, "gated", ha="right", va="bottom", fontsize=6, color=INK2)
    ax.text(3.7, 20, "every version\naccepted", ha="right", va="center", fontsize=6, color=INK2)
    ax.set_xlabel("Round", labelpad=1); ax.set_ylabel("Held-out success (%)", labelpad=2)
    ax.set_ylim(0, 74); ax.set_yticks(range(0, 80, 20)); ax.set_xticks(range(0, 7, 2)); ax.set_xlim(-0.2, 6.2)
    ax.set_title("(b) The gate protects\nself-training", loc="left", fontsize=7.5, fontweight="bold", pad=3, x=-0.33)
    # (c) what recursion and the meta level add, sealed tests
    sp = json.load(open(os.path.join(ROOT, "results/fresh_spatial_main_20261111.json")))
    rep = json.load(open(os.path.join(ROOT, "results/selfrepair_read_20261109.json")))
    rows = [("RSI loop", "vs its start", sp["F1"], C["fixed"]),
            ("verifier", "real vs shuffled", sp["F2"], C["fixed"]),
            ("recursion", "vs frozen-policy\npractice", sp["F3"], C["fixed"]),
            ("meta level", "vs gate alone,\nfailing recipe", rep["S1_seeds0to3"], C["llm_harness"])]
    ax = fig.add_subplot(gc[0, 0])
    ax.axvline(0, color=MUTED, lw=0.7, zorder=1)
    ax.grid(axis="x"); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ys = [3, 2, 1, 0]
    for y, (name, sub, r, col) in zip(ys, rows):
        m, (lo, hi) = r["mean_points"], r["ci95_points"]
        ax.plot([lo, hi], [y, y], color=col, lw=2.2, solid_capstyle="round", zorder=2)
        ax.plot(m, y, "o", color=col, ms=4.2, zorder=3, **RING)
        ax.text(hi + 0.4, y, "+" + str(Decimal(str(m)).quantize(Decimal("0.1"), ROUND_HALF_UP)), ha="left", va="center", fontsize=6.3, color=INK, fontweight="bold")
    ax.set_yticks(ys); ax.set_yticklabels([f"{n}\n{s_}" for n, s_, _, _ in rows], fontsize=5.6, linespacing=0.95)
    for t in ax.get_yticklabels():
        t.set_color(INK)
    ax.set_xlim(-1, 10.5); ax.set_xticks([0, 5, 10]); ax.set_ylim(-0.6, 3.6)
    ax.set_xlabel("Points, sealed tests\n(95% CI)", labelpad=1, fontsize=6.2, linespacing=0.95)
    ax.set_title("(c) Recursion improves,\nthe meta level repairs", loc="left", fontsize=7.5, fontweight="bold", pad=3, x=-0.62)
    save(fig, "fig_teaser.pdf", tight=False)


# ---------------------------------------------------------------- 1. forest plot of the registered claims
def fig_claims():
    d = read_final()
    m2 = json.load(open(os.path.join(ROOT, "results/m2_read_20261104.json")))
    m2c = json.load(open(os.path.join(ROOT, "results/m2_cavin_read_20261106.json")))
    noise = d["noise_check_n0_halves"]["yq"]
    rows = [("R1  fixed − ref. (Y, seeds 1-3)", d["R1_fixed"], 5),
            ("R1  full − ref. (Y, seeds 1-3)", d["R1_full"], 5),
            ("R2  fixed − shuffled (Y, 0-3)", d["R2_seeds0to3"], 3),
            ("R3  fixed − nonrec (Y, 0-3)", d["R3_seeds0to3"], 2),
            ("R4  full − fixed (Y)", d["R4_full_minus_fixed"], 2),
            ("R4  llm_harness − fixed (Y)", d["R4_harness_minus_fixed_yq"], 2),
            ("R4  llm − fixed (A)", d["R4_llm_minus_fixed_cavin"], 2),
            ("R4  llm_harness_cap − fixed (A)", d["R4_cap_minus_fixed_cavin"], 2),
            ("R5  best gated − onebig (Y, 0-3)", d["R5_seeds0to3"], 2),
            ("M2-A  llm − replica, v2 (Y)", m2[0], 3),
            ("M2-A  llm − replica, v2 (A)", m2c[0], 3),
            ("noise  n0 half − half (Y)", {"mean_points": noise["diff_points"], "ci95_points": noise["ci95"]}, None)]
    rows = [r for r in rows if r[1] is not None]
    fig, ax = plt.subplots(figsize=(3.4, 3.3))
    ys = list(range(len(rows)))[::-1]
    ax.axvline(0, color=MUTED, lw=0.7, zorder=1)
    for y, (label, r, bar) in zip(ys, rows):
        m, (lo, hi) = r["mean_points"], r["ci95_points"]
        ax.plot([lo, hi], [y, y], color=INK2, lw=1.2, zorder=2)
        ax.plot(m, y, "o", color=INK, ms=4.2, zorder=3, **RING)
        if bar is not None:
            ax.plot(bar, y, "|", color=C["shuffled"], ms=9, mew=1.5, zorder=2)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], color=INK)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False); ax.grid(axis="x")
    ax.set_xlabel("Points (95% CI); red tick = bar set in advance")
    ax.set_xlim(-3.5, 6.5)
    save(fig, "fig_claims.pdf")


# ---------------------------------------------------------------- 2. every run: n0 -> replicate-averaged final
def fig_runs():
    d = read_final()
    runs = d["runs"]
    ref = {"yq": d["mode"]["pooled_n0_yq"]["mean"], "cavin": d["mode"]["pooled_n0_cavin"]["mean"]}
    ref["cavin_s0"] = ref["cavin"]
    sections = [("yq", "Cloud pool (Y), seeds 1–3"), ("cavin", "A800 (A), seeds 1–3"), ("cavin_s0", "A800 (A), seed 0")]
    short = {"llm_harness": "llm\nharness", "llm_harness_cap": "llm\nharness cap"}
    fig, ax = plt.subplots(figsize=(7.0, 2.3))
    ygrid(ax)
    x, ticks, labels = 0.0, [], []
    for plat, head in sections:
        x0 = x
        for arm in ARMS:
            names = sorted(n for n in runs.get(plat, {}) if re.fullmatch(arm + r"_s\d", n))
            if not names:
                continue
            xs = [x + 0.75 * i for i in range(len(names))]
            for xi, n in zip(xs, names):
                r = runs[plat][n]
                ax.plot([xi, xi], [r["n0"], r["test"]], color=C[arm], lw=1.1, zorder=2)
                ax.plot(xi, r["n0"], "_", color=INK2, ms=5.5, mew=1.1, zorder=3)
                ax.plot(xi, r["test"], "o", color=C[arm], ms=4.4, zorder=4, **RING)
            ticks.append((xs[0] + xs[-1]) / 2)
            labels.append(short.get(arm, arm))
            x = xs[-1] + (1.9 if len(names) > 1 else 2.6)
        x1 = x - (1.9 if plat != "cavin_s0" else 2.6)
        ax.plot([x0 - 0.7, x1 + 0.7], [ref[plat]] * 2, **REF)
        ax.text((x0 + x1) / 2, 1.0, head, transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=7, fontweight="bold")
        x += 1.6
    ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=6.5, linespacing=0.95)
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Official test success (%)")
    ax.set_ylim(54.2, 63.4); ax.set_yticks(range(56, 64, 2)); ax.set_xlim(-1.3, x - 1.6 - 1.2)
    fig.legend(handles=[Line2D([], [], color=INK2, lw=0, marker="_", ms=5.5, mew=1.1, label="initial policy, the run's own test"),
                       Line2D([], [], color=INK2, lw=0, marker="o", ms=4.4, **RING, label="retained policy, mean of 3 evaluations"),
                       Line2D([], [], **{k: v for k, v in REF.items() if k != "zorder"},
                              label=f"pooled initial reference (Y {ref['yq']:.1f}, A {ref['cavin']:.1f})")],
              loc="outside lower center", ncol=3, columnspacing=1.8, handletextpad=0.5)
    save(fig, "fig_runs.pdf")


# ---------------------------------------------------------------- 3. retained-gate trajectories on LIBERO-Goal (Y)
def fig_gates():
    arms = ["fixed", "full", "llm_harness", "nonrec", "shuffled"]
    fig, axes = plt.subplots(1, 5, figsize=(7.0, 2.0), sharey=True, gridspec_kw={"wspace": 0.05})
    for ax, arm in zip(axes, arms):
        ygrid(ax)
        col, rec = C[arm], []
        for s in (1, 2, 3):
            p = os.path.join(ROOT, f"results/baidu/yq_oftg_{arm}_s{s}/report.json")
            if os.path.exists(p):
                rec.append(chain(p))
        if rec:
            mean = [sum(y[k] for y, _ in rec) / len(rec) for k in range(7)]
            ax.axhline(mean[0], **REF)
            for y, acc in rec:
                ax.plot(range(7), y, color=col, lw=0.8, alpha=0.7, zorder=2)
                ax.plot(acc, [y[k] for k in acc], "o", color=col, ms=2.6, mec="white", mew=0.4, zorder=3)
            ax.plot(range(7), mean, "-", color=col, lw=2.0, zorder=4)
            ax.plot([6], mean[-1:], "o", color=col, ms=4.6, zorder=5, **RING)
            ax.annotate(f"{mean[-1] - mean[0]:+.1f} pts".replace("-", "−"), (1, 1), xycoords="axes fraction",
                        xytext=(0, 3), textcoords="offset points", ha="right", va="bottom", fontsize=7.5, fontweight="bold")
        panel_title(ax, TITLE[arm], arm)
        ax.set_xlabel("Round")
        ax.set_xticks(range(7))
        ax.set_ylim(56, 69); ax.set_yticks(range(56, 70, 4))
    axes[0].set_ylabel("Gate success of the\nretained policy (%)")
    fig.legend(handles=[Line2D([], [], color=INK2, lw=0.8, marker="o", ms=2.6, mec="white", mew=0.4,
                               label="one seed (dot: a new version was accepted)"),
                        Line2D([], [], color=INK2, lw=2.0, label="mean of 3 seeds"),
                        Line2D([], [], **{k: v for k, v in REF.items() if k != "zorder"}, label="mean at round 0")],
               loc="outside lower center", ncol=3, columnspacing=1.8, handletextpad=0.5)
    save(fig, "fig_gates.pdf")


# ---------------------------------------------------------------- 4. self-repair: collapse without the gate vs gated arms
def fig_selfrepair():
    fig = plt.figure(figsize=(7.0, 1.95))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 0.06, 1, 1, 1], wspace=0.05)
    ax = fig.add_subplot(gs[0])
    # the always-accept run of the same recipe (no gate), A800 seed 1: gate and audit of every round's version
    ch = sorted(json.load(open(os.path.join(ROOT, "results/a800/runs2/a8_oftg_curve_bc_s1/report.json")))["accepted_chain"],
                key=lambda c: c["round"])
    ygrid(ax)
    ax.plot([c["round"] for c in ch], [c["audit"] * 100 for c in ch], "-o", color=MUTED, lw=1.1, ms=3.6, mfc="white",
            mec=INK2, mew=0.8, label="audit")
    ax.plot([c["round"] for c in ch], [c["gate"] * 100 for c in ch], "-o", color=INK, lw=1.8, ms=4, label="gate", **RING)
    panel_title(ax, "No gate", "every version accepted")
    ax.legend(loc="lower left", handlelength=1.6)
    ax.set_ylabel("Success on held-out\nplacements (%)")
    ax.set_ylim(0, 72); ax.set_yticks(range(0, 80, 20)); ax.set_xlabel("Round"); ax.set_xticks(range(7))
    first = None
    for i, arm in enumerate(["fixed", "full", "llm_harness"]):
        ax = fig.add_subplot(gs[2 + i], sharey=first)
        first = first or ax
        ygrid(ax)
        rec = []
        for s in (1, 2, 3):
            p = os.path.join(ROOT, f"results/baidu/yq_oftgb_{arm}_s{s}/report.json")
            if os.path.exists(p):
                rec.append(chain(p)[0])
                ax.plot(range(7), rec[-1], "-", color=C[arm], lw=1.2, zorder=3)
        p = os.path.join(ROOT, f"results/a800/runs2/a8_oftgb_{arm}_s0/report.json")
        if os.path.exists(p):
            rec.append(chain(p)[0])
            ax.plot(range(7), rec[-1], "-o", color=C[arm], lw=0.9, ms=3.2, mfc="white", mec=C[arm], mew=0.9, zorder=4)
        if rec:
            ax.axhline(sum(y[0] for y in rec) / len(rec), **REF)
        panel_title(ax, TITLE[arm] if arm != "fixed" else "Gated, same recipe", arm)
        ax.set_xlabel("Round"); ax.set_xticks(range(7))
        if i:
            ax.tick_params(axis="y", labelleft=False)
    first.set_ylim(53, 72); first.set_yticks(range(55, 75, 5))
    first.set_ylabel("Gate success of the\nretained policy (%)")
    fig.legend(handles=[Line2D([], [], color=INK2, lw=1.2, label="cloud pool, seeds 1–3"),
                        Line2D([], [], color=INK2, lw=0.9, marker="o", ms=3.2, mfc="white", mec=INK2, mew=0.9, label="A800, seed 0"),
                        Line2D([], [], **{k: v for k, v in REF.items() if k != "zorder"}, label="mean at round 0")],
               loc="outside lower center", ncol=3, columnspacing=1.8, handletextpad=0.5)
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
    fig, ax = plt.subplots(figsize=(3.3, 3.0), layout="none")
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
        col = C["shuffled"] if "shuffled" in claim and "fixed" not in claim else (C["nonrec"] if "nonrec" in claim else C["fixed"])
        ax.barh(y, m, color=col, alpha=0.75, height=0.6)
        ax.plot([lo, hi], [y, y], color="black", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7, linespacing=0.95)
    ax.axvline(0, color="0.5", lw=0.8)
    ax.set_xlabel("points on the held-out test (95% CI)")
    save(fig, "fig_code.pdf", tight=False)


# ---------------------------------------------------------------- 6. train-on-test inflation
def fig_inflation():
    d = json.load(open(os.path.join(ROOT, "results/train_on_test_inflation_20261030.json")))
    sets = [("official", "official test states", C["fixed"]), ("fresh", "fresh placements", C["full"])]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.4, 1.9), sharey=True, gridspec_kw={"width_ratios": [1.25, 2.0], "wspace": 0.04})
    ygrid(a1); ygrid(a2)
    for j, (key, label, col) in enumerate(sets):
        for i, ck in enumerate(["sft", "rl"]):
            v = d["cells"][ck][key]
            a1.bar(i + (j - 0.5) * 0.4, v, width=0.34, color=col, label=label if i == 0 else None)
            a1.text(i + (j - 0.5) * 0.4, v + 2, f"{v:.1f}", ha="center", va="bottom", fontsize=6, color=INK2)
    a1.set_xticks([0, 1]); a1.set_xticklabels(["SFT\nstart", "RL\ncheckpoint"]); a1.tick_params(axis="x", length=0)
    a1.set_xlim(-0.6, 1.6); a1.set_ylabel("LIBERO-10 success (%)"); a1.set_ylim(0, 104); a1.set_yticks(range(0, 101, 20))
    off, fresh = d["rl_per_task"]["official"], d["rl_per_task"]["fresh"]
    for t, (o, f) in enumerate(zip(off, fresh)):
        a2.plot([t, t], [o, f], color=AXIS, lw=1.3, zorder=2)
    a2.plot(range(len(off)), off, "o", color=sets[0][2], ms=4.4, zorder=3, **RING)
    a2.plot(range(len(fresh)), fresh, "o", color=sets[1][2], ms=4.4, zorder=4, **RING)
    a2.set_xticks(range(len(off))); a2.set_xlim(-0.6, len(off) - 0.4); a2.tick_params(axis="x", length=0)
    a2.set_xlabel("Task (RL checkpoint)")
    fig.legend(handles=[Line2D([], [], lw=0, marker="o", color=col, ms=4.4, **RING, label=label) for _, label, col in sets],
               loc="outside upper center", ncol=2, columnspacing=1.6, handletextpad=0.2)
    save(fig, "fig_inflation.pdf")


# ---------------------------------------------------------------- framework diagram (replaces the TikZ figure; matplotlib only)
def fig_framework():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(11.8, 5.0), layout="none")
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


FIGS = [fig_teaser, fig_claims, fig_runs, fig_gates, fig_selfrepair, fig_code, fig_inflation, fig_framework]

if __name__ == "__main__":
    if "--check" in sys.argv:
        OUT = tempfile.mkdtemp(prefix="figcheck_")
    for f in FIGS:
        f()
    if "--check" in sys.argv:
        bad = [n for n in sorted(os.listdir(OUT))
               if not os.path.exists(os.path.join(HERE, n)) or open(os.path.join(OUT, n), "rb").read() != open(os.path.join(HERE, n), "rb").read()]
        print("check:", "every PDF here is what this script draws from the records" if not bad else "DIFFERENT: " + ", ".join(bad))
        sys.exit(1 if bad else 0)

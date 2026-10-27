"""Progress figures and data tables from results/ (re-run after each sync).

    python scripts/report/make_progress.py results reports/progress

Writes fig1_claims.png, fig2_long8.png, fig3_cross_model.png and tables.md. Every number comes from
results/claims_*.json or a run's report.json; nothing is typed in by hand.
"""

import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# reference categorical palette, light mode (validated: 3 slots, all pairs) + neutrals
BLUE, ORANGE = "#2a78d6", "#eb6834"
GRAY, INK, INK2, GRID, SURFACE = "#9a9892", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

for name in ("Noto Sans CJK SC", "Noto Sans CJK TC", "Noto Sans CJK JP"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams.update({"font.size": 10.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
                     "axes.unicode_minus": False})

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def claims(name):
    return {c["claim"]: c for c in json.loads((ROOT / name).read_text())["claims"]}


def report(run):
    for path in (ROOT / "a800" / "runs2" / run / "report.json", ROOT / "baidu" / run / "report.json"):
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(run)


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


tables = []

# ---------- figure 1: pre-registered claims on Qwen2.5-Coder-1.5B ----------
main, long8 = claims("claims_cruxeval_o.json"), claims("claims_long8_cruxeval_o.json")
rows = [("C1 模型变强：完整版 训练后 − 训练前", main["C1 full: final - initial"], "达标"),
        ("C1 模型变强：固定程序 训练后 − 训练前", main["C1 fixed: final - initial"], "达标"),
        ("C2 外部反馈：固定程序 − 打乱反馈", main["C2 fixed - shuffled"], "达标"),
        ("C3 递归：固定程序 − 非递归（4 轮）", main["C3 fixed - nonrec"], None),
        ("C3 递归：固定程序 − 非递归（8 轮，探索性）", long8["C3 fixed - nonrec"], "探索性支持"),
        ("C4 改学法：完整版 − 固定程序", main["C4 full - fixed"], None),
        ("C5 分多轮：固定程序 − 一次性训练", main["C5 fixed - onebig"], None)]
fig, ax = plt.subplots(figsize=(9.6, 4.6))
style(ax)
for i, (label, c, verdict) in enumerate(rows):
    y = len(rows) - 1 - i
    met = c["mean_and_ci_pass"]
    color = BLUE if met else GRAY
    lo, hi = c["ci95_points"]
    ax.plot([lo, hi], [y, y], color=color, linewidth=2, solid_capstyle="round")
    ax.plot(c["mean_points"], y, "o", color=color, markersize=8, markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.plot([c["bar_points"]] * 2, [y - 0.28, y + 0.28], color=INK2, linewidth=1.2, linestyle=(0, (2, 2)))
    text = f"{c['mean_points']:+.1f}  [{lo:+.1f}, {hi:+.1f}]   " + (verdict if met and verdict else "未证明")
    ax.text(7.3, y, text, va="center", fontsize=10, color=INK if met else INK2)
ax.axvline(0, color=INK2, linewidth=1)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in reversed(rows)], color=INK)
ax.set_xlim(-3.5, 7)
ax.set_xlabel("主考试 CRUXEval-O，分（逐题配对、按 3 个种子平均；横线 = 95% 置信区间；虚线刻度 = 预注册达标线）")
ax.set_title("Qwen2.5-Coder-1.5B：框架让模型变强、靠的是外部裁判；递归要到 8 轮才显现",
             loc="left", fontsize=12.5, color=INK, pad=12)
fig.tight_layout()
fig.savefig(OUT / "fig1_claims.png", dpi=180, bbox_inches="tight")
plt.close(fig)
tables.append("## 图 1 数据：预注册问题（Qwen2.5-Coder-1.5B，CRUXEval-O）\n\n"
              "| 问题 | 平均（分） | 95% CI | 各种子 | 达标线 | 判定 |\n| --- | --- | --- | --- | --- | --- |\n" +
              "\n".join(f"| {label} | {c['mean_points']:+.2f} | [{c['ci95_points'][0]:+.2f}, {c['ci95_points'][1]:+.2f}] | "
                        f"{' / '.join(f'{v:+.2f}' for v in c['per_seed_points'].values())} | +{c['bar_points']:.0f} | "
                        f"{(verdict if c['mean_and_ci_pass'] and verdict else '未证明')} |"
                        for label, c, verdict in rows))

# ---------- figure 2: 8-round runs, gain over initial by round ----------
def steps(run, rounds=8):
    t = report(run)["tests"]["cruxeval_o"]
    by_round = {p["round"]: p["score"] for p in t["curve"]}
    out, cur = [], t["initial"]
    for r in range(rounds + 1):
        cur = by_round.get(r, cur)
        out.append(100 * (cur - t["initial"]))
    return out


fig, ax = plt.subplots(figsize=(9.6, 4.8))
style(ax)
ax.grid(axis="y", color=GRID, linewidth=0.8)
xs = list(range(9))
per_seed = {}
for arm, color, name in (("fixed", BLUE, "固定程序（变强的自己出题）"), ("nonrec", ORANGE, "非递归（始终由初始模型出题）")):
    series = [steps(f"bj_q15_long8{arm}_s{s}") for s in (1, 2, 3)]
    per_seed[arm] = series
    xe = xs + [8.6]   # carry the last kept version past round 8 so its level reads as a step
    for s in series:
        ax.step(xe, s + s[-1:], where="post", color=color, linewidth=1.1, alpha=0.35)
    mean = [sum(v) / 3 for v in zip(*series)]
    ax.step(xe, mean + mean[-1:], where="post", color=color, linewidth=2.6, label=name)
    ax.text(8.7, mean[-1], f"{name.split('（')[0]} {mean[-1]:+.1f}", va="center", color=INK, fontsize=10)
ax.axvline(4, color=INK2, linewidth=1, linestyle=(0, (3, 3)))
ax.text(4.08, ax.get_ylim()[1] * 0.97, "预注册的 4 轮到此为止", va="top", fontsize=9.5, color=INK2)
ax.axhline(0, color=INK2, linewidth=1)
ax.set_xlim(0, 10)
ax.set_xticks(xs)
ax.set_xlabel("轮次（每轮结束后保留下来的版本；细线 = 3 个种子，粗线 = 平均）")
ax.set_ylabel("CRUXEval-O 相对初始的提升（分）")
ax.legend(loc="upper left", frameon=False)
ax.set_title("8 轮：递归组一路上涨，非递归组 4 轮后基本停滞（Addendum 3，探索性）",
             loc="left", fontsize=12.5, color=INK, pad=12)
fig.tight_layout()
fig.savefig(OUT / "fig2_long8.png", dpi=180, bbox_inches="tight")
plt.close(fig)
tables.append("## 图 2 数据：8 轮实验各轮相对初始的提升（CRUXEval-O，分）\n\n"
              "| 组 | 种子 | " + " | ".join(f"第 {r} 轮" for r in xs) + " |\n| --- | --- | " + " | ".join("---" for _ in xs) + " |\n" +
              "\n".join(f"| {arm} | {k + 1} | " + " | ".join(f"{v:+.2f}" for v in s) + " |"
                        for arm in ("fixed", "nonrec") for k, s in enumerate(per_seed[arm])))

# ---------- figure 3: cross-model, fixed program, 4 rounds ----------
# every planned fixed-program run; those without a report yet are skipped
RUNS = [("Qwen2.5-Coder-1.5B", 1, "main_q15_fixed_s1"), ("Qwen2.5-Coder-1.5B", 2, "bj_q15_fixed_s2"),
        ("Qwen2.5-Coder-1.5B", 3, "main_q15_fixed_s3"), ("Qwen2.5-Coder-7B", 1, "cross_q7b_fixed_s1"),
        ("Qwen2.5-Coder-7B", 2, "bj_q7b_fixed_s2"), ("Qwen2.5-Coder-7B", 3, "cross_q7b_fixed_s3"),
        ("Granite-3.3-8B", 1, "bj_g8b_fixed_s1"), ("Granite-3.3-8B", 2, "bj_g8b_fixed_s2"),
        ("Granite-3.3-8B", 3, "bj_g8b_fixed_s3"), ("Qwen3-8B", 1, "cross_qw3_fixed_s1"),
        ("Qwen3-8B", 2, "cross_qw3_fixed_s2"), ("Qwen3-8B", 3, "cross_qw3_fixed_s3")]
SUITES = [("cruxeval_o", "CRUXEval-O（主考试）"), ("cruxeval_i", "CRUXEval-I（迁移）"), ("lcb_exec", "LiveCodeBench-exec")]
runs = [(m, s, r, report(r)) for m, s, r in RUNS if (ROOT / "a800/runs2" / r / "report.json").exists()
        or (ROOT / "baidu" / r / "report.json").exists()]
fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.9), sharey=True)
ys = list(range(len(runs)))[::-1]
for ax, (suite, title) in zip(axes, SUITES):
    style(ax)
    prev = None
    for y, (model, seed, run, rep) in zip(ys, runs):
        p = rep["tests"][suite]["paired"]
        g, (lo, hi) = 100 * p["mean_gain"], [100 * v for v in p["ci95"]]
        sig = lo > 0 or hi < 0
        ax.plot([lo, hi], [y, y], color=BLUE, linewidth=1.8, solid_capstyle="round")
        ax.plot(g, y, "o", markersize=8, color=BLUE, markerfacecolor=BLUE if sig else SURFACE, markeredgewidth=1.6)
        if prev is not None and prev != model:
            ax.axhline(y + 0.5, color=GRID, linewidth=1)
        prev = model
    ax.axvline(0, color=INK2, linewidth=1)
    ax.set_title(title, fontsize=11, color=INK)
    ax.set_xlabel("相对初始的提升（分）")
axes[0].set_yticks(ys)
axes[0].set_yticklabels([f"{m} 种子{s}" for m, s, _, _ in runs], color=INK)
SHORT = {"Qwen2.5-Coder-1.5B": "1.5B", "Qwen2.5-Coder-7B": "7B", "Granite-3.3-8B": "Granite", "Qwen3-8B": "Qwen3"}
sig_models, quiet = [], {}
for model, seed, run, rep in runs:
    hit = any(rep["tests"][k]["paired"]["ci95"][0] > 0 for k, _ in SUITES)
    if hit and SHORT[model] not in sig_models:
        sig_models.append(SHORT[model])
    quiet.setdefault(SHORT[model], []).append(not hit)
quiet = [f"{m} {len(v)} 个种子都未达显著" for m, v in quiet.items() if all(v)]
fig.suptitle("固定学法 4 轮的跨模型结果：" + "、".join(sig_models) + " 各有种子在某门考试上显著提升" +
             ("，" + "，".join(quiet) if quiet else ""), x=0.01, ha="left", fontsize=12.5, color=INK)
fig.text(0.01, -0.02, "实心点 = 95% 置信区间不含 0；空心点 = 不显著。Qwen3 种子1 四轮都被门控拒绝，最终模型即初始模型（提升为 0）。",
         fontsize=9.5, color=INK2)
fig.tight_layout()
fig.savefig(OUT / "fig3_cross_model.png", dpi=180, bbox_inches="tight")
plt.close(fig)
tables.append("## 图 3 数据：固定学法 4 轮，各模型各种子（相对初始，分；括号内 95% CI）\n\n"
              "| 模型 | 种子 | 初始 CRUX-O | CRUXEval-O | CRUXEval-I | LCB-exec |\n| --- | --- | --- | --- | --- | --- |\n" +
              "\n".join(f"| {m} | {s} | {100 * rep['tests']['cruxeval_o']['initial']:.2f} | " + " | ".join(
                  f"{100 * rep['tests'][k]['paired']['mean_gain']:+.2f} [{100 * rep['tests'][k]['paired']['ci95'][0]:+.2f}, "
                  f"{100 * rep['tests'][k]['paired']['ci95'][1]:+.2f}]" for k, _ in SUITES) + " |"
                        for m, s, r, rep in runs))
pooled = []
for tag, model in (("q7b", "Qwen2.5-Coder-7B"), ("g8b", "Granite-3.3-8B"), ("qw3", "Qwen3-8B")):
    cells, seeds, final = [], [], True
    for k, _ in SUITES:
        path = ROOT / f"claims_{tag}_{k}.json"
        c = claims(path.name).get("C1 fixed: final - initial") if path.exists() else None
        if c is None:
            cells.append("—")
            continue
        seeds, final = c["seeds"], final and c["final"]
        cells.append(f"{c['mean_points']:+.2f} [{c['ci95_points'][0]:+.2f}, {c['ci95_points'][1]:+.2f}]" +
                     (" 达标" if c["mean_and_ci_pass"] else ""))
    pooled.append(f"| {model} | {','.join(map(str, seeds))} | " + " | ".join(cells) + f" | {'全部种子' if final else '中期'} |")
tables.append("## 跨模型合并：固定学法，种子平均的逐题配对差（分；括号内 95% bootstrap CI；达标 = 均值 ≥ 2 且下限 > 0）\n\n"
              "由 `python -m rsi.audit.compare_arms results --model <q7b|g8b|qw3> --suite <suite>` 生成。\n\n"
              "| 模型 | 种子 | CRUXEval-O | CRUXEval-I | LCB-exec | 状态 |\n| --- | --- | --- | --- | --- | --- |\n" +
              "\n".join(pooled))

# ---------- baselines (initial models, greedy pass@1) ----------
BASES = [("Qwen2.5-Coder-1.5B", "main_q15_fixed_s1"), ("Granite-3.3-8B", "base_granite8b"),
         ("Qwen2.5-Coder-7B", "base_qcoder7b"), ("Qwen3-8B", "base_qwen3_8b_v11"), ("Meta CWM-32B", "base_cwm32b_r2")]
lines = []
for name, run in BASES:
    d = ROOT / "a800/runs2" / run
    if (d / "baseline.json").exists():
        sc = json.loads((d / "baseline.json").read_text())["scores"]
    else:
        sc = {k: v["initial"] for k, v in report(run)["tests"].items()}
    lines.append(f"| {name} | {100 * sc['cruxeval_o']:.2f} | {100 * sc['cruxeval_i']:.2f} | {100 * sc['lcb_exec']:.2f} |")
vla = [json.loads((ROOT / "a800/runs2" / r / "baseline.json").read_text())["test_success"][0]
       for r in ("vla_baseline_goal_rep0", "vla_baseline_goal_rep1") if (ROOT / "a800/runs2" / r / "baseline.json").exists()]
tables.append("## 基线（初始模型，贪心解码）\n\n| 模型 | CRUXEval-O | CRUXEval-I | LCB-exec |\n| --- | --- | --- | --- |\n" +
              "\n".join(lines) + "\n\nOpenVLA-7B（LIBERO-goal 官方 500 个 episode）两次重跑成功率：" +
              " / ".join(f"{100 * v:.1f}%" for v in vla))

(OUT / "tables.md").write_text("# 进展图的数据表（由 scripts/report/make_progress.py 生成）\n\n" + "\n\n".join(tables) + "\n")
print("wrote", sorted(p.name for p in OUT.iterdir()))

# M1 on LIBERO-Goal (OFT 1-traj SFT): addendum-11 pilot curves, interim (2026-10-31)

Status: **interim, one seed, rounds 1-3 of 6.** The addendum-11 rule is read at rounds 5-6 (mean D over the
runs available by 2026-11-01 12:00Z). This is not a conclusion.

Pilots are sealed, so no test was read. S = (gate + audit) / 2, 400 sampled placements, always-accept curves
(no selection), Beijing evaluation (deterministic: all variance below comes from placement sampling).

## Beijing, seed 0

n0: gate 0.600, audit 0.575, S 0.5875 (both runs share it).

| run | update | S by round 1 → 3 | change vs n0 |
|---|---|---|---|
| `bj_oftg_curve_grpo` | GRPO lr 3e-5, matched ratio, episode loss | 0.6075, 0.6175, 0.650 | +2.0, +3.0, +6.25 |
| `bj_oftg_curve_bc` | BC on verified successes, lr 1e-5 | running | |

Settings confirmed from the receipt: `loss_agg` episode, `ratio_mode` matched, lr 3e-5.

## Paired check on identical placements (second session, 2026-10-31)

Reader `scripts/baidu/pfs_nodebits.sh` (job `zw-rsi-script-nodebits1`) takes per-placement greedy outcomes from
the run's call directories, with the node identified from `spec.adapter`. Its counts reproduce the summaries exactly:
n0 120/200 gate, 115/200 audit; r03c0 131 and 129. The placement-id hashes are identical across nodes
(gate c629d74a…, audit 71d5ceb3…). Bootstrap: 10k resamples of placements. Sign test: exact, on discordant
pairs.

| comparison | episodes | change | 95% CI | up / down | p |
|---|---|---|---|---|---|
| n0 → r01c0 | 400 | +2.00 | [-2.0, +6.0] | 38 / 30 | 0.40 |
| n0 → r02c0 | 400 | +3.00 | [-1.2, +7.2] | 45 / 33 | 0.21 |
| n0 → r03c0 | 400 | **+6.25** | [+1.8, +10.8] | 56 / 31 | 0.010 |
| n0 → r03c0, gate only | 200 | +5.50 | [-1.5, +12.5] | 29 / 18 | 0.14 |
| n0 → r03c0, audit only | 200 | +7.00 | [+1.0, +13.0] | 27 / 13 | 0.038 |

## Reading so far

* This is the first M1 node whose gain clears placement noise on identical placements. The audit half carries
  it, and the audit is never used for any decision in the run.
* Three rounds have been looked at, so a rough multiple-look correction puts the round-3 p near 0.03. The
  rule's rounds 5-6 are still ahead.
* One seed. The cavin seed-1 GRPO replica (`a8_oftg_curve_grpo_s1`) is queued for the next free GPU.
* Contrast with LIBERO-10 (`M1_RECIPE_CURVES_20261031.md`), where the same recipe from a 19% start stays within
  noise for 18 steps. This fits the addendum-11 reason: from a mid-range start, more sampled groups contain both
  outcomes and carry a GRPO signal.
* The main-arm plan generator is ready (`mkplans_vla.py goal_main <grpo|bc> <bj|yq>`: five arms, seeds 1-3,
  fresh paired gates). It is not run until the rule fires, and the operator is fixed in its own addendum first.

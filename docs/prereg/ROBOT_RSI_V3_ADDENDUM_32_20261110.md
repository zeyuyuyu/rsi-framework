# Prereg v3, addendum 32: the guard-rail gate, and plain training of the failing recipe on LIBERO-Goal

Committed 2026-11-10 after the first fresh-scene read (addendum 30, block `goal_long12`,
`docs/results/FRESH_GOAL_LONG12_20261110.md`, read 23:25Z) and before any run named here exists.

## What had been seen

* On 1000 sealed fresh scenes the 12-round gated loop on Goal ends +3.54 [+1.72, +5.42] above its start and
  +7.30 [+5.47, +9.20] above the non-recursive loop, and **2.73 points below one round of ungated on-policy RL with
  the same budget** ([−4.30, −1.20]). On the official fixed states the last comparison was a tie (−0.38).
* The gated runs kept 6, 9 and 9 of their 12 rounds. A refused round's training is discarded. In the finished gated
  Goal runs of the A800 node the strict gate refused 15 of 24 rounds; every refusal was a dip of at most 4.5 points
  and 11 were at most 3 points, with the paired gate noise at 3.4 points (sd). The rounds of the one recorded
  collapse (BC recipe, always accept, `a8_oftg_curve_bc_s1`) moved the gate by −17.5, −25.5 and −7.5.
* So the strict gate separates nothing it needs to separate at five points, and it throws away about a third of
  the practice for noise. This is a defect of the framework as specified, found by the fresh-scene test.

## Part A: the guard-rail gate

**Rule.** A round's best child is kept iff, on that round's fresh paired placements, its gate success is at least
the parent's minus δ **and** at least the initial policy's minus δ, with **δ = 5 points** (engine fields
`min_gate_gain: -0.05`, `gate_floor: 0.05`; the initial policy is scored on every round's gate set, 200 more
episodes per round). The first condition replaces "at least the parent's"; the second stops a slow drift that the
first alone would allow (the 12-round non-recursive runs drifted 4-11 points below their start through accepted
versions). δ was fixed from the records above, before any run with this gate.

**Runs.** `yq_oftg_guard12_s{1,2,3}` (Yangquan, source rsi_src_v32 = this commit's `rsi/`, tarball sha256
4e36b3f6ee34c4d2...; unit test `test_guard_rail_gate_keeps_noise_sized_dips_and_refuses_regressions_and_drift`): the `fixed12` plan of addendum 27 with those two
fields, and only the initial and the retained policy tested. Same seeds, so the same practice placements and gate
sets as `yq_oftg_fixed12` and `yq_oftg_onebig12`, which they are compared with.

| claim | comparison | fresh-scene test (primary) | official test (three-evaluation finals) |
|---|---|---|---|
| G2 | guard12 − fixed12 (strict gate) | ≥ +2, CI > 0 | ≥ +2, CI > 0 |
| G1 | guard12 − initial | ≥ +5, CI > 0 | R1 rule: ≥ +5, CI > 0, ≥ 2 of 3 seeds > 0 |
| G3 | guard12 − onebig12 (ungated RL, equal compute) | CI reported; non-inferior if its lower bound > −2 | the same |

The fresh-scene test is primary here because the defect was found on it; the official test is reported beside it.
Readers: `scripts/report/fresh_read.py goal_guard12` (a block added to the committed reader; the existing blocks
give byte-identical output) and `scripts/report/goal_guard_read.py guard`. One read each, when the three runs have
`report.json`, both replicates and the fresh evaluation.

**Predictions.** The guard-rail gate keeps at least 11 of 12 rounds on every seed. G1 +5 to +7 (60% to pass +5);
G2 +2 to +4 (55%); G3 between −2 and +1, non-inferior (60%). If G3 fails, per-round gating costs something beyond
discarded rounds and the paper says the loop is behind plain RL on a working recipe.

**Not tested here:** that the guard-rail gate still stops a collapse. By the records it refuses the three collapse
rounds above, but that is an argument, not a run. If three cards are free by 2026-11-12 00:00Z,
`yq_oftgb_guard_s{1,2,3}` (the Goal BC start of addendum 24 under this gate, 6 rounds) is run and reported against
`yq_oftgb_nogate` and `yq_oftgb_fixed`; if not, the paper states the limitation.

## Part B: plain training of the BC recipe on Goal

Addendum 24 has, from the collapsing BC recipe on Goal, the gate-only loop and the loops with a meta level (twelve
runs, read 2026-11-09). What it lacks is the baseline everyone means by "training without the framework": the same
recipe and budget with every round kept. The collapse is known on Goal from one always-accept curve at the gate; it
has never been measured on a test, with seeds. (Addendum 31 does this on Spatial, where the recipe may not fail.)

**Runs.** `yq_oftgb_nogate_s{1,2,3}` (Yangquan, source rsi_src_v32): the addendum-24 `bc_start` plan, 6 rounds × 3
inner steps, `min_gate_gain` −1.0 (always accept), only the initial and the final policy tested. Compared with
`yq_oftgb_fixed_s{1,2,3}` and `yq_oftgb_llm_harness_s{1,2,3}` of the same seeds; those six get a fresh-scene
evaluation as well.

| claim | comparison | bar (official test and fresh-scene test, each) |
|---|---|---|
| NG1 | gate only − plain training | ≥ +10, CI > 0 |
| NG2 | gate + LLM meta level − plain training | ≥ +10, CI > 0 |
| NG3 | plain training − initial | reported with CI |

Readers: `scripts/report/goal_guard_read.py nogate`, `scripts/report/fresh_read.py goal_nogate`. One read each.

**Predictions.** Plain training collapses on at least two of three seeds (final under 30%); NG1 and NG2 above +25.
If it does not collapse on a seed, that seed's plain training ends near its start and the claim rests on the others.

## Order of use of the Yangquan cards (about fifteen)

After tonight's evaluations: `yq_oftg_guard12` ×3, `yq_oftgb_nogate` ×3, addendum 31 `yq_oftsb_nogate` ×3,
addendum 29 `yq_oftsb_meta3_s2-3` and `yq_oftsb_fixed_s2-3`; then, as cards free, addendum 30
`yq_ofts_fixed12` ×3 and `yq_ofts_nonrec12` ×3, `yq_oftgb_guard` ×3 (above), addendum 29 `yq_oftsb_full` and
`yq_ofts_meta3`. The 12-round Spatial runs therefore start later than addendum 30 planned; their seed-0 pair on the
A800 node is unaffected.

## What is not changed

No registered read, bar or run changes. The strict gate's results stand as read; the guard-rail gate is a new,
separately named arm.

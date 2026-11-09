# Self-repair study (addenda 24 and 26): the registered read of S1-S3, 2026-11-09 10:15Z

Design: `docs/prereg/ROBOT_RSI_V3_ADDENDUM_24_20261104.md` (committed 2026-11-04, before any run) and
`ROBOT_RSI_V3_ADDENDUM_26_20261106.md` (seed 0 on cavin, committed before those runs). Start program: the BC recipe that
collapses without the gate (unit-temperature likelihood on T = 1.6 samples; `a8_oftg_curve_bc_s1` 58.5 → 5.5). Arms:
`fixed` (gate only, program never edited), `full` (numeric search over the harness space, 2 candidates/round),
`llm_harness` (LLM proposer over the same space, same compute); 6 rounds × 3 inner steps, fresh paired gates. Seeds 1-3
on Yangquan (`yq_oftgb_*`), seed 0 on cavin (`a8_oftgb_*`); 12 runs. Finals = per-episode mean of three evaluations of
the retained policy (own test + two replicates, `--test-eval --replicates 2`); seed-averaged per-episode paired
bootstrap (10,000 draws), pairing within platform. Reader `scripts/report/selfrepair_read.py` (58b6eb3, committed
before the read); output `results/selfrepair_read_20261109.json`. Read once, after all twelve runs had `report.json`
and two replicates (the last, `a8_oftgb_llm_harness_s0_rep`, finished 10:03Z).

| claim | comparison | points | 95% CI | bar | result |
|---|---|---|---|---|---|
| **S1** (primary) | `llm_harness` − `fixed`, seeds 0-3 | **+2.65** | [+0.73, +4.58] | ≥ +3, CI > 0 | **fails** (CI > 0, mean under the bar) |
| S1, Yangquan only | `llm_harness` − `fixed`, seeds 1-3 | +2.38 | [+0.29, +4.47] | ≥ +3, CI > 0 | fails |
| S2 (secondary) | `llm_harness` − `full`, seeds 0-3 | +1.15 | [−0.63, +2.92] | reported with CI | not distinguishable from 0 |
| S2, Yangquan only | `llm_harness` − `full`, seeds 1-3 | +0.84 | [−1.20, +2.91] | | |
| secondary | `full` − `fixed`, seeds 0-3 | +1.50 | [−0.33, +3.38] | none | |
| **S3** (descriptive) | `llm_harness` − hand-tuned GRPO `fixed` (Goal main, same seeds) | +0.28 | [−1.43, +1.97] | none | the repaired loop ties the hand-tuned loop |
| S3, gate only | BC-start `fixed` − hand-tuned GRPO `fixed` | −2.37 | [−4.12, −0.62] | none | the gate alone ends below the hand-tuned loop |
| noise check | n0 halves, Yangquan (5 vs 4 runs) | −0.44 | [−1.47, +0.56] | | |
| noise check | n0 halves, cavin (2 vs 1 runs) | −0.20 | [−2.10, +1.70] | | |

Per seed (final %, control → arm, difference and CI):

| seed | fixed → llm_harness (S1) | full → llm_harness (S2) | fixed → full | tuned GRPO → llm_harness (S3) |
|---|---|---|---|---|
| 0 (A) | 57.4 → 60.9, +3.47 [−0.40, +7.27] | 58.8 → 60.9, +2.07 [−1.53, +5.73] | +1.40 [−2.47, +5.20] | 57.2 → 60.9, +3.67 [+0.33, +7.00] |
| 1 (Y) | 56.1 → 60.1, +4.06 [+0.53, +7.67] | 56.7 → 60.1, +3.40 [−0.27, +7.00] | +0.66 [−2.67, +4.13] | 59.8 → 60.1, +0.33 [−3.13, +3.80] |
| 2 (Y) | 58.7 → 61.3, +2.60 [−0.67, +5.87] | 59.9 → 61.3, +1.40 [−2.00, +4.87] | +1.20 [−1.87, +4.33] | 59.9 → 61.3, +1.40 [−2.00, +4.80] |
| 3 (Y) | 57.5 → 57.9, +0.46 [−3.27, +4.13] | 60.2 → 57.9, −2.27 [−6.00, +1.33] | +2.73 [−0.80, +6.40] | 62.2 → 57.9, −4.27 [−8.13, −0.40] |

Runs (retained node; its gate; final test, 3 evaluations; own n0 test; rounds with an accepted candidate):

| arm | seed 0 (cavin) | seed 1 (Y) | seed 2 (Y) | seed 3 (Y) |
|---|---|---|---|---|
| `fixed` | r06c0; 64.5; 57.4; 57.2; r3,4,6 | r06c0; 60.0; 56.1; 58.8; r1,2,4,6 | n0; —; 58.7; 58.4; none | r05c0; 63.0; 57.5; 59.8; r3,4,5 |
| `full` | r04c0; 61.5; 58.8; 57.8; r2,3,4 | r05c1; 62.5; 56.7; 58.6; r1,3,4,5 | r06c0; 65.0; 59.9; 59.0; r1,3,4,5,6 | r06c0; 61.0; 60.2; 58.4; r1,3,4,5,6 |
| `llm_harness` | r06c0; 68.5; 60.9; 58.8; r1-6 | r05c1; 65.5; 60.1; 58.6; r1-5 | r06c0; 68.5; 61.3; 59.0; r1-6 | r06c1; 64.5; 57.9; 59.0; r1,3,4,5,6 |

What each retained program is (gate-level record, `docs/CASE_STUDIES.md` §2 for the LLM's diagnoses verbatim):
`fixed` is the starting BC recipe on every seed. `full` kept BC unchanged on seeds 0 and 1, switched to GRPO on seed 2
and to BC with the rollout-temperature likelihood (the one-knob fix of addendum 12) on seed 3, both only in round 6.
`llm_harness` switched to GRPO at a lower temperature in round 1 (seeds 1, 2) or round 2 (seed 0) and the gate kept
that lineage, later re-tuned by the LLM (seed 0: lower lr, more samples, larger budget); on seed 3 the GRPO switch was
refused twice and the LLM repaired BC instead (sampling temperature 1.6 → 1.3). Every accepted candidate on the LLM
arms was authored by the LLM (no fallback rounds among accepted versions).

## What the read says

1. **S1 fails its bar.** `llm_harness` − `fixed` is +2.65 points with a CI above zero: positive on three of four seeds,
   individually significant on one. The registered bar was +3, so the claim "the meta level turns a failing procedure
   into a better policy than the gate alone" is **not made**; addendum 24 fixed the consequence in advance ("the meta
   level has no demonstrated effect in this study, and the paper says so"). The paper reports the estimate as positive
   and under its bar.
2. **The repair is the knob space's, not demonstrably the diagnosis's.** S2 is +1.15 [−0.63, +2.92] and `full` − `fixed`
   is +1.50 [−0.33, +3.38]: blind numeric search over the same knobs lands within noise of the LLM. This is the case the
   preregistration named: "the loop repairs itself when the space contains the repair, with the LLM's advantage being
   speed". Speed is what the record shows: the LLM's switch was kept in round 1-2 on three seeds; numeric search reached
   a repair on two seeds, in round 6.
3. **Repair means back to the hand-tuned level, not above it.** S3 is +0.28 [−1.43, +1.97]: the self-repaired loop ends
   where the hand-tuned GRPO loop ends (which itself gains one to two points over its start). The gate-only arm ends 2.4
   points below the hand-tuned loop: the gate prevents the collapse and holds the policy near its start (finals
   56.1-58.7% against initial tests of 57.2-59.8%), and that is all it does.
4. **Gates are not comparable across arms.** Retained gates exceed the final tests by 5-8 points on the LLM arm and by
   4-7 on `fixed`: the arm that accepts a candidate in nearly every round carries more winner's-curse in its retained
   gate. At the gate the LLM arm looked 4-8 points ahead; on the sealed test it is 2.65. Gate-level records (section 5
   of `EXPERIMENTS_AND_RESULTS.md`, the 11-06/11-07 Feishu notes) must be read with this in mind.
5. **Noise check.** Halves of the n0 evaluations differ by −0.44 (Yangquan) and −0.20 (cavin); S1 is several times
   this, S2 and S3 are within it.

## Disclosures

* Round-boundary continuations with more rollout GPUs for the slow LLM arms (addendum 26 operational notes; `resume.json`
  in each run) changed platform fields only. One Yangquan 6-card continuation never scheduled and was replaced by a
  3-card one; no round was lost.
* The 11-06 Feishu note's "fixed arm refused all six rounds" and the 11-07 note's "all LLM seeds switched to GRPO" were
  corrected on 11-07 (section 7 of `EXPERIMENTS_AND_RESULTS.md`); this read is from the run records.
* No test file of this study was opened before this read; the gate-level tables published earlier used gate and audit
  records only.

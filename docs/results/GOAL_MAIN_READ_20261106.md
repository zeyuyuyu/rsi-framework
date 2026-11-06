# LIBERO-Goal main study: the one-time read of R1-R5 (prereg v3; addenda 14-16, 18 am. 1, 22, 23, 25), 2026-11-06 ~05:00Z

Reader: `scripts/report/goal_read.py` (committed ad13997 before the read; structure check: 31 runs, 500 official
episodes each, one episode-id digest). Output: `results/goal_read_20261106.json`. Every run is measured on its final
retained policy; comparisons are paired per episode within a seed, seed-averaged, paired bootstrap 95% CI (10,000
draws). Yangquan seeds 1-3 carry R1-R5; cavin seeds 1-3 carry R4-llm and R4-cap; seed 0 (cavin) joins R2, R3, R5.

| claim | points | 95% CI | bar | result |
|---|---|---|---|---|
| R1 `fixed` final − initial (seeds 1-3) | +2.00 | [-0.60, +4.67] | +5.0 | fails |
| R1 `full` final − initial (seeds 1-3) | +0.80 | [-2.00, +3.53] | +5.0 | fails |
| R2 `fixed` − `shuffled` (seeds 0-3) | +1.25 | [-0.50, +3.00] | +3.0 | fails |
| R2 `fixed` − `shuffled` (seeds 1-3) | +1.87 | [-0.20, +3.93] | +3.0 | fails |
| R3 `fixed` − `nonrec` (seeds 0-3) | +2.40 | [+0.25, +4.55] | +2.0 | **passes** |
| R3 `fixed` − `nonrec` (seeds 1-3) | +2.07 | [-0.27, +4.40] | +2.0 | fails |
| R4 `full` − `fixed` (Yangquan) | -0.60 | [-2.73, +1.47] | +2.0 | fails |
| R4-harness `llm_harness` − `fixed` (Yangquan) | -0.73 | [-2.80, +1.33] | +2.0 | fails |
| R4-llm `llm` − `fixed` (cavin) | +0.87 | [-1.27, +3.00] | +2.0 | fails |
| R4-cap `llm_harness_cap` − `fixed` (cavin) | +1.00 | [-1.13, +3.20] | +2.0 | fails |
| secondary `llm_harness` − `full` (no bar) | -0.13 | [-2.33, +2.00] | +0.0 | fails |
| R5 best-by-gate − `onebig` (seeds 0-3) | -0.25 | [-1.90, +1.45] | +2.0 | fails |
| R5 best-by-gate − `onebig` (seeds 1-3) | +1.27 | [-0.67, +3.20] | +2.0 | fails |
| R5-ungated best-by-gate − `onebig` r01c0 (seeds 0, 2, 3; seed 1 needs its test-eval) | -0.67 | [-2.73, +1.40] | +2.0 | fails |

R1 also requires >= 2 of 3 seeds individually above 0: `fixed` has 1 (seed 3: +5.4 [+1.8, +9.2]), `full` 0.
R3 passes on seeds 0-3 (+2.40 [+0.25, +4.55]) but not on seeds 1-3 (+2.07 [−0.27, +4.40]); the 4-seed pass rests on seed 3
(+8.2) and on `nonrec_s0` ending below its own start (53.8 vs 57.4). Noise check: the registered odd/even split of the n0
episodes is confounded by the test's episode order (every run shows about −10 points), so it is not informative; a
within-task split is added in the JSON of a later reader version.

## Per run (official test, %; retained node)

| platform | run | n0 | final | retained |
|---|---|---|---|---|
| yq | fixed_s1 | 58.6 | 59.8 | r06c0 |
| yq | fixed_s2 | 59.8 | 59.2 | r05c0 |
| yq | fixed_s3 | 58.2 | 63.6 | r06c0 |
| yq | full_s1 | 59.4 | 60.0 | r05c0 |
| yq | full_s2 | 60.0 | 59.2 | r06c0 |
| yq | full_s3 | 59.0 | 61.6 | r06c0 |
| yq | llm_harness_s1 | 57.6 | 59.0 | r05c1 |
| yq | llm_harness_s2 | 58.8 | 60.8 | r05c0 |
| yq | llm_harness_s3 | 59.4 | 60.6 | r06c0 |
| yq | nonrec_s1 | 58.2 | 60.4 | r02c0 |
| yq | nonrec_s2 | 58.6 | 60.6 | r04c0 |
| yq | nonrec_s3 | 60.2 | 55.4 | r05c0 |
| yq | onebig_s1 | 58.8 | 58.8 | n0 |
| yq | onebig_s2 | 60.0 | 58.4 | r01c0 |
| yq | onebig_s3 | 58.6 | 60.2 | r01c0 |
| yq | shuffled_s1 | 59.2 | 57.6 | r06c0 |
| yq | shuffled_s2 | 58.4 | 58.8 | r06c0 |
| yq | shuffled_s3 | 59.4 | 60.6 | r05c0 |
| cavin | fixed_s1 | 59.0 | 61.6 | r05c0 |
| cavin | fixed_s2 | 57.6 | 59.0 | r06c0 |
| cavin | fixed_s3 | 59.0 | 57.4 | r04c0 |
| cavin | llm_s1 | 58.8 | 60.2 | r06c0 |
| cavin | llm_s2 | 57.6 | 60.4 | r06c1 |
| cavin | llm_s3 | 58.0 | 60.0 | r06c0 |
| cavin | llm_harness_cap_s1 | 56.8 | 59.6 | r06c1 |
| cavin | llm_harness_cap_s2 | 59.0 | 61.6 | r06c1 |
| cavin | llm_harness_cap_s3 | 59.6 | 59.8 | r06c1 |
| cavin_s0 | fixed_s0 | 58.8 | 57.2 | r04c0 |
| cavin_s0 | nonrec_s0 | 57.4 | 53.8 | r06c0 |
| cavin_s0 | onebig_s0 | 57.8 | 62.0 | r01c0 |
| cavin_s0 | shuffled_s0 | 58.6 | 57.8 | r05c0 |

## Reading, as registered

* **The loop's test-set gain is small.** `fixed` ends +2.0 points above its start (seed-averaged; +1.2, −0.6, +5.4);
  cavin's `fixed` seeds 0-3 end −1.6, +2.6, +1.4, −1.6. The gate-level gains of +4-7 points (docs/results/M1_*) do not
  carry to the official test at that size: the retained node is chosen on a 200-episode gate, and the 500-episode test
  itself moves by ±1.5-3.6 points between evaluations of one model.
* **R2 (verifier) fails** at +1.25 [−0.5, +3.0] (seeds 1-3: +1.87 [−0.2, +3.9]); `shuffled` arms end near their start, so
  the direction is right but the fixed arms' own gain is too small for a +3 gap.
* **R3 (recursion) passes with four seeds, not with three**; reported as fragile.
* **R4 family: all null** (numeric, LLM, harness, capped harness; both platforms), consistent with M2 v2 (docs/results/M2_*).
* **R5 fails**: one-shot GRPO with the same budget (`onebig`) ends as high as the gated loop (seed 0: 62.0 vs 57.2 in
  onebig's favour; seeds 1-3 +1.3 [−0.7, +3.2] in the loop's favour). Under this protocol iterating under gate control
  does not beat plain one-shot RL at equal compute on LIBERO-Goal.
* What the Goal study supports: the gated loop never degrades the policy on the test (minimum −1.6), its gains are
  real but small (+1 to +2 points on average, +5.4 on one seed), and no meta level adds to it on a recipe that already
  works. The RSI-specific claim therefore rests on the self-repair study (addenda 24, 26), still sealed.

## Open items

* R5-ungated seed 1: `yq_oftg_onebig_s1` rejected its candidate; its r01c0 test-eval (addendum 18 am. 1) is pending.
* Compute ratios for the meta arms (addendum 18) are computed from `backend-accounting.json` in a follow-up table.

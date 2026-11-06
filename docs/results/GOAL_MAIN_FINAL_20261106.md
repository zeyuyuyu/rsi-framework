# LIBERO-Goal main study: the registered read of R1-R5 (replicate-averaged finals, pooled initial reference), 2026-11-06 ~07:45Z

This supersedes the preliminary single-evaluation read of `GOAL_MAIN_READ_20261106.md`. Rule (prereg v3 "Test (sealed)";
VLA addendum 2): each run's final = per-episode mean of three evaluations of its retained policy (the run's own test +
two `--test-eval --replicates 2` runs, same plan and source tree); the initial reference = per-episode mean of every
in-run n0 test of this model and suite on the platform (Yangquan: 36 evaluations, mean 58.92%;
cavin: 21, mean 58.44%). Seed-averaged, per-episode paired bootstrap (10,000 draws).
Reader: `scripts/report/goal_read.py --mode final` (f428a3b, committed before the read); output `results/goal_read_final_20261106.json`.

| claim | points | 95% CI | bar | result |
|---|---|---|---|---|
| R1 `fixed` final − initial reference (seeds 1-3) | +1.71 | [-0.76, +4.23] | +5.0 | fails |
| R1 `full` final − initial reference (seeds 1-3) | +1.28 | [-1.37, +3.99] | +5.0 | fails |
| R2 `fixed` − `shuffled` (seeds 0-3) | +1.22 | [-0.37, +2.85] | +3.0 | fails |
| R2 `fixed` − `shuffled` (seeds 1-3) | +1.73 | [-0.22, +3.69] | +3.0 | fails |
| R3 `fixed` − `nonrec` (seeds 0-3) | +1.72 | [-0.28, +3.68] | +2.0 | fails |
| R3 `fixed` − `nonrec` (seeds 1-3) | +1.49 | [-0.69, +3.69] | +2.0 | fails |
| R4 `full` − `fixed` (Yangquan) | -0.42 | [-2.40, +1.56] | +2.0 | fails |
| R4-harness `llm_harness` − `fixed` (Yangquan) | -0.73 | [-2.58, +1.07] | +2.0 | fails |
| R4-llm `llm` − `fixed` (cavin) | +1.04 | [-0.84, +3.00] | +2.0 | fails |
| R4-cap `llm_harness_cap` − `fixed` (cavin) | +1.16 | [-0.76, +3.16] | +2.0 | fails |
| secondary `llm_harness` − `full` (no bar) | -0.31 | [-2.36, +1.76] | +0.0 | fails |
| R5 best-by-gate − `onebig` (seeds 0-3) | -0.58 | [-2.12, +0.95] | +2.0 | fails |
| R5 best-by-gate − `onebig` (seeds 1-3) | +1.04 | [-0.76, +2.87] | +2.0 | fails |
| R5-ungated best-by-gate − `onebig` r01c0 (seeds 0-3; seed 1 from its 3-evaluation test-eval job) | -0.75 | [-2.35, +0.82] | +2.0 | fails |

R1 also needs >= 2 of 3 seeds individually above 0: `fixed` 1 (seed 3: +3.28 [+0.08, +6.61]), `full` 0.
Noise check (two halves of the in-run n0 evaluations, identical model): Yangquan +0.64 [-0.07, 1.36], cavin +0.54 [-0.24, 1.35]: no harness drift.

## Per run (official test %, 3-evaluation final; n0 = the run's own single n0 test)

| platform | run | n0 | final | retained |
|---|---|---|---|---|
| yq | fixed_s1 | 58.6 | 59.8 | r06c0 |
| yq | fixed_s2 | 59.8 | 59.87 | r05c0 |
| yq | fixed_s3 | 58.2 | 62.2 | r06c0 |
| yq | full_s1 | 59.4 | 59.8 | r05c0 |
| yq | full_s2 | 60.0 | 59.07 | r06c0 |
| yq | full_s3 | 59.0 | 61.73 | r06c0 |
| yq | llm_harness_s1 | 57.6 | 59.0 | r05c1 |
| yq | llm_harness_s2 | 58.8 | 60.33 | r05c0 |
| yq | llm_harness_s3 | 59.4 | 60.33 | r06c0 |
| yq | nonrec_s1 | 58.2 | 59.93 | r02c0 |
| yq | nonrec_s2 | 58.6 | 60.4 | r04c0 |
| yq | nonrec_s3 | 60.2 | 57.07 | r05c0 |
| yq | onebig_s1 | 58.8 | 58.8 | n0 |
| yq | onebig_s2 | 60.0 | 59.0 | r01c0 |
| yq | onebig_s3 | 58.6 | 59.53 | r01c0 |
| yq | shuffled_s1 | 59.2 | 58.13 | r06c0 |
| yq | shuffled_s2 | 58.4 | 57.8 | r06c0 |
| yq | shuffled_s3 | 59.4 | 60.73 | r05c0 |
| cavin | fixed_s1 | 59.0 | 60.87 | r05c0 |
| cavin | fixed_s2 | 57.6 | 59.2 | r06c0 |
| cavin | fixed_s3 | 59.0 | 57.13 | r04c0 |
| cavin | llm_s1 | 58.8 | 60.13 | r06c0 |
| cavin | llm_s2 | 57.6 | 60.13 | r06c1 |
| cavin | llm_s3 | 58.0 | 60.07 | r06c0 |
| cavin | llm_harness_cap_s1 | 56.8 | 59.67 | r06c1 |
| cavin | llm_harness_cap_s2 | 59.0 | 61.07 | r06c1 |
| cavin | llm_harness_cap_s3 | 59.6 | 59.93 | r06c1 |
| cavin_s0 | fixed_s0 | 58.8 | 57.2 | r04c0 |
| cavin_s0 | nonrec_s0 | 57.4 | 54.8 | r06c0 |
| cavin_s0 | onebig_s0 | 57.8 | 62.67 | r01c0 |
| cavin_s0 | shuffled_s0 | 58.6 | 57.53 | r05c0 |

## Reading, as registered

* **No preregistered bar is met.** R1 (+1.71 fixed / +1.28 full), R2 (+1.22), R3 (+1.72; the preliminary 4-seed pass of
  +2.40 came from single evaluations and does not survive replicate averaging), the R4 family (−0.7 to +1.2), R5 (−0.58;
  seed 0's one-shot `onebig` policy scores 62.67 against the gated loop's 57.2) and R5-ungated (−0.75) all fail.
* **What the data do show, descriptively.** Every gated-loop run ends within noise of or above its start (finals 57.1-62.2
  against a 58.4-58.9 reference; the two below-start finals, cavin fixed_s3 and fixed_s0, are within −1.3 and −1.7 of
  the pooled reference); the loop's typical gain is +1 to +2 points; `shuffled` (verifier removed) ends at the start
  (57.2-60.7); `nonrec` ends from −3.6 (seed 0) to +1.5; one-shot RL at equal compute matches or beats the loop.
* **Meta level.** All four meta arms are within ±1.2 points of `fixed` on both platforms, as in M2 (docs/results/M2_*).
* Per the prereg, the paper reports these as negative results at this budget on LIBERO-Goal. The RSI-specific claim rests on
  the self-repair study (addenda 24, 26; sealed) and, if the pilots show a second degrading recipe, addendum 27.

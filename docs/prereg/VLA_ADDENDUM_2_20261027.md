# VLA addendum 2: replicate-averaged tests (committed before any RSI-trained VLA test score is read)

Written 2026-10-27 10:40Z. State when written: of the 8 VLA arms, only `nonrec` seed 1 has ended, and it
accepted no round, so its retained version is the initial model and its test score is a third measurement of
the initial model. No RSI-trained VLA version has been evaluated on the 500 official episodes. `fixed` seed 1
(rerun `_r4`) and `shuffled` seed 1 are running; the other 5 arms are queued.

## What the third measurement of the initial model shows

| evaluation of the initial OpenVLA-7B (libero-goal, 500 official episodes) | success |
| --- | --- |
| replicate 0 (baseline harness, 10-26) | 74.8% |
| replicate 1 (baseline harness, 10-26) | 76.4% |
| in-run n0 test of `vla_goal_nonrec_s1_r2` (10-27) | 78.4% |

| pair | episodes that flip | net | exact McNemar p |
| --- | --- | --- | --- |
| rep 0 vs rep 1 | 62 (12.4%) | +8 | 0.37 |
| rep 0 vs in-run n0 | 56 (11.2%) | +18 | 0.022 |
| rep 1 vs in-run n0 | 40 (8.0%) | +10 | 0.15 |

340 episodes succeed in all three, 81 fail in all three, and 79 (15.8%) change outcome at least once.

Two consequences:

1. **A single 500-episode evaluation per version is not enough.** One model evaluated twice moved by
   3.6 points, more than the 3.2-point bar of addendum 1, and a per-episode McNemar test called it
   significant (p = 0.022). The V1 rule "+3.0 points, McNemar p < 0.05, above 2x the replicate
   difference", applied to one evaluation of the final and one of the initial, could be met by noise alone.
2. **The two harnesses may differ systematically.** The baseline harness (`--baseline-only`, 10-26) ran
   before the rollout thread caps were added (OMP/MKL/OPENBLAS = 4, 10-26 evening); the in-run test runs
   with them. Thread counts can change CPU-side numerics over 300-step closed-loop rollouts. Whatever the
   cause, from now on the initial model and the RSI versions are compared only within the in-run harness.

## The rules from now on (replacing the test procedure of V1-V3; arms, rounds and seeds unchanged)

* **Initial reference.** Every VLA run evaluates the initial model (n0) on the 500 official episodes in its
  own run. The reference for the initial model is the per-episode success rate averaged over all of these
  in-run n0 evaluations (8 when all arms have ended). The two baseline-harness replicates are reported, not
  pooled.
* **Final of an arm.** If the run accepted no round, its final is the initial model and its gain is 0 by
  construction. Otherwise the retained version gets 2 further evaluations on the same 500 episodes after
  the run has ended (`python -m rsi.run_libero --test-eval <run> --replicates 2`, same harness and plan),
  and its per-episode success rate is the mean over the 3 evaluations (the run's own test plus the 2).
* **V1 improvement (per arm, `fixed` and `full`).** Gain = mean over episodes of (final - initial
  reference). Met if the gain is >= +3.0 points and its 95% paired bootstrap CI over episodes (10,000
  resamples) excludes 0, in both seeds. Reported beside it, as a stricter reading: whether the gain also
  exceeds 3.6 points, the largest difference seen between two single evaluations of one model.
* **V2 feedback / V3 recursion.** `fixed` - `shuffled` and `fixed` - `nonrec`, on the replicate-averaged
  finals, seed-averaged per episode: met if >= +2.0 points with the bootstrap CI excluding 0.
* **Noise check, reported with every verdict.** The same statistic computed between two halves of the
  in-run n0 evaluations (identical model). If its CI excludes 0, the harness has a drift that the rules
  above do not remove, and every VLA verdict is reported as unreliable.
* McNemar p-values on single evaluations are still reported, but no verdict depends on them.

Compute: 2 extra 500-episode evaluations per arm whose final differs from the initial model, at most 14,
about 1.5 h each on 2 A800 GPUs. They queue behind the remaining arms.

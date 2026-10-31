# Prereg v3, addendum 12: BC on the policy's own high-temperature samples collapses; temperature-matched BC

Committed 2026-10-31 (~00:50Z), before the run specified here has started. No v3 run has read a test result.

## What happened

`a8_oftg_curve_bc_s1` is the addendum-11 seed-1 BC replica on cavin: LIBERO-Goal, OFT 1-traj SFT, BC on
verified successes, lr 1e-5, sampling at T = 1.6. Its pooled score was flat for three rounds, then fell:

| round | pooled S (n0 0.585) | sampled success, inner steps 0 / 1 / 2 | BC loss at step 100, inner steps 0 / 1 / 2 |
|---|---|---|---|
| 1 | 0.5875 | 55% / 66% / 53% | 0.29 / 0.30 / 0.31 |
| 2 | 0.5775 | 54% / 53% / 55% | 0.34 / 0.36 / 0.33 |
| 3 | 0.560 | 54% / 47% / 34% | 0.52 / 0.75 / 1.08 |
| 4 | 0.4475 (gate 0.400, audit 0.495) | 20% / 11% / 1.5% | 2.06 / 3.02 / 3.31 |

The first 24 sampled episodes of round 5 all failed, every one running to the 512-step limit. The mean
sampled episode length rose 380 → 440 → 474 → 507 steps over the last four sampled rollouts. No rollout
logged an error, and greedy evaluation still succeeds about half the time. So the simulator is working, and
it is the policy that degraded.

## Diagnosis

The OFT train worker's BC loss is the NLL of the emitted tokens at temperature 1. The tokens were sampled at
T = 1.6. Fitting unit-temperature logits to samples of softmax(z / T) moves the policy toward p^(1/T), a
flatter distribution. On the policy's own samples the effect compounds:

* the flatter policy's T = 1.6 samples are flatter still;
* the next fit flattens it again.

Success filtering opposes this only while sampled success is high. Once the flattening lowers success, fewer
and noisier successes remain. Round 4 trained on 44, 25 and then 7 episodes, so the loop accelerates. Two
measurements support this:

* the BC loss (the entropy of its own targets, roughly) rises at an accelerating rate;
* the sampled success falls before the greedy score does.

GRPO already divides the logits by the rollout temperature, so its updates act on the behaviour policy itself.
None of the GRPO curves shows this pattern.

The M2 OpenVLA train worker has the same unit-temperature BC at the default T = 1.5. The M2 BC pilots ran
two rounds only and are not affected so far. Any M2 run longer than that must not use unit-temperature BC
until the fix is ported to that worker.

## Change (code, commit with this addendum)

`VLAConfig.bc_temp`: "unit" (default, unchanged behaviour) or "rollout". With "rollout", the OFT BC loss divides
the logits by each episode's sampling temperature, as GRPO does. Without filtering, the tempered policy then
fits its own samples, so its fixed point is itself, and only the success filter moves it. The option is
OFT-only (the OpenVLA backend refuses it), is passed in the train spec only when set, and is recorded in the
receipt (`extra.bc_temp`). Test: `test_bc_temperature_option_reaches_only_the_oft_spec_and_scales_bc_logits`.
New runs use the code tree `src4` on cavin. Running jobs keep `src3`.

## Pilot (sealed, cavin, 1 GPU)

`a8_oftg_curve_bct_s1`: identical to `a8_oftg_curve_bc_s1` (same seed 1, so the same round-1 training
placements and the same gate and audit placements), except `bc_temp` "rollout". It is an always-accept curve:
6 rounds x 3 inner steps of 64 placements, 8 samples at T = 1.6, 100 steps of batch 64, lr 1e-5.

## Use of the results, fixed now

* Mechanism prediction: with temperature-matched BC, the sampled success of every inner step stays at or above
  40% (the unit-temperature run fell to 34% at round 3, step 2, and to 1.5% by round 4). If it falls below 20%
  at any step, the diagnosis is wrong or incomplete, and is reported as such.
* Outcome: D = mean pooled S over rounds 5-6 minus its n0, as in addendum 11. This pilot does not enter the
  addendum-11 operator rule, which is unchanged. If D >= +3, temperature-matched BC is a candidate operator
  for a later addendum. Either way the result is reported next to the unit-temperature run.
* `a8_oftg_curve_bc_s1` continues to round 6 unchanged, so the rule reads it as declared.

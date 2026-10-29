# Prereg v3, addendum 5 (M1): inner on-policy steps, and the plain-RL learning curve (sealed pilots)

Committed 2026-10-30 before the pilots below start. No v3 run has read a test result.

## Why

Addendum 3 resolved to "neither qualifies". At every length and lr tried, one round moves the gate and the
audit by less than their noise, and gate gains do not reproduce on the audit. Addendum 4 tests whether 12
gated short rounds compound. The engine now supports `inner_steps` (545f0a6): several on-policy sample,
curate and train cycles per round, on fresh placements, with one gate at the end. This gives more policy
steps per gate, at a lower gate cost per step. Two questions are open, and these pilots answer them on the M1
platform with idle Baidu slots:

1. Does our GRPO/LoRA update improve this model at all over many on-policy iterations? SimpleVLA-RL's own
   checkpoint shows the model can reach ~75% on fresh placements.
2. Does gating several inner steps at once compound?

## Pilots (sealed, Baidu, 1 GPU each, seed 0)

Shared: curriculum 64 placements per step (8 samples, T=1.6); GRPO lr 1e-4, 100 steps of batch 64; gate and
audit 200 + 200; 6 rounds x 3 inner steps = 18 on-policy steps.

* `bj_oft3_pilot5_gated`: acceptance as in the main arms (child gate >= parent gate).
* `bj_oft3_pilot5_curve`: always accept (`min_gate_gain` -1). The gate and audit are measured after every 3
  steps, so this traces the learning curve of plain on-policy RL in our implementation.

## Use of the results, fixed now

* If `curve` gains less than +5 points on both gate and audit after 18 steps, the update itself is the problem,
  not the RSI wrapper. The next change targets training: adapter capacity, lr, trust region and data per step.
  `update_probe` results are used for the diagnosis.
* If `gated` meets the addendum-4 short-round criteria (gate +5 over n0, last accepted audit +3), the main arms
  use rounds of 3 inner steps of 64 placements, with 6 rounds and the addendum-2 update. This option takes
  precedence over addendum 4's short rounds, because it needs fewer gates per policy step. `onebig` then
  becomes one round of 18 inner steps with no intermediate gate, which is plain RL at equal sampling.
* Otherwise addendum 4's rule stands.

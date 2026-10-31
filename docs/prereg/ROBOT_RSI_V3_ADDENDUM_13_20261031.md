# Prereg v3, addendum 13: does the LIBERO-Goal gain carry over to LIBERO-Spatial (and Object)?

Committed 2026-10-31 (~02:55Z), before either run here starts. No v3 run has read a test result.

## Why

The only clear M1 gain so far is on LIBERO-Goal: Beijing seed 0, D = +7.00 points, CI [+2.88, +11.25]. Its seed
replicas are running (addendum 11 and its amendments 2-3). LIBERO-10 is negative for all three recipes (addendum 8,
`M1_RECIPE_CURVES_20261031.md`). Prereg v3 lists the other suites as in scope ("Other suites ... `fixed` at
least"). A result that holds on a second mid-range suite says much more than one suite. A cavin GPU is free, and
the queue is empty.

## Runs (sealed, cavin, 1 GPU each, `scripts/a800/mkoft_suite.py`)

| run | checkpoint | suite |
|---|---|---|
| `a8_ofts_curve_grpo_s0` | `Haozhan72/Openvla-oft-SFT-libero-spatial-traj1` (on cavin, 4 shards checked) | `libero_spatial` |
| `a8_ofto_curve_grpo_s0` | `Haozhan72/Openvla-oft-SFT-libero-object-traj1` (download failed with HTTP 429; retried first) | `libero_object` |

The program is exactly the Goal one (`bj_oftg_curve_grpo`): GRPO at lr 3e-5, matched ratio, episode-balanced
loss, 6 rounds x 3 inner on-policy steps of 64 placements, 8 samples at T = 1.6, 100 steps of batch 64, and
always-accept. Gate and audit are 200 + 200 sampled placements, and the official tests stay sealed. Seed 0,
code tree src3, `admit_max_used_mib` 8000. The Object run starts on the next free GPU once its checkpoint is
complete.

## Use of the results, fixed now

* Per run, D = mean pooled S over rounds 5-6 minus its own n0, with a paired placement bootstrap (one draw
  applied to both rounds), plus gate-only and audit-only splits. The same bar as Goal: D >= +3.
* If a suite reaches the bar, it becomes a candidate for the main arms after LIBERO-Goal, compute allowing. That
  choice goes in its own addendum. If it does not, it is reported next to LIBERO-10 and LIBERO-Goal.
* These runs do not enter the addendum-11 rule.

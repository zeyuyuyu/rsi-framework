# Prereg v3, addendum 27: the long-horizon recursion test on LIBERO-Goal (12 rounds)

Committed 2026-11-07 ~06:30Z, before any run named here exists. State at commit time: the Goal main study is read
(`docs/results/GOAL_MAIN_FINAL_20261106.md`, R3 = +1.72 [−0.28, +3.68] at 6 rounds, bar +2, fails); the self-repair
study (addenda 24/26) has 9 of 12 runs with `report.json` and its tests are sealed and unread.

## Why

The code-domain recursion test gave the shape this addendum tests for: at 4 rounds `fixed − nonrec` was −0.58, at 8
rounds +2.83 [+1.17, +4.50] (addendum 3 result), replicated on the 7B model (+2.88 and +4.49, addendum 4). The
mechanism there is that the frozen initial generator's practice is used up after about four rounds (`nonrec`
accepted 2 gate gains in rounds 5-8, `fixed` 8). On LIBERO-Goal the registered 6-round R3 is +1.72 with the bar at
+2 and the interval just including 0, and the gate trajectories (`fig_gates` in the paper draft) show `nonrec`
flattening after round 3 while `fixed` keeps climbing. The natural preregistered question is therefore whether
recursion separates from the frozen-generator control at twice the horizon, and whether the gated loop then also
separates from one-shot RL at the same (doubled) budget. This is the cheapest test of "RSI beats plain RL" that the
existing data motivate, and it is launched on idle Yangquan cards without touching any registered run.

## Design (LIBERO-Goal, Yangquan, seeds 1-3, source rsi_src_v27)

Nine runs, each the addendum-14/17 Goal seed program (GRPO, lr 3e-5, matched ratio, episode loss, T 1.6, 64 scenes
per inner step, 100 steps × batch 64) with the horizon doubled:

| arm | engine | isolates |
|---|---|---|
| `yq_oftg_fixed12_s{1,2,3}` | 12 rounds × 3 inner steps, fresh paired gates, recursive | the gated recursive loop at 12 rounds |
| `yq_oftg_nonrec12_s{1,2,3}` | same, `recursive: false` (every round's practice from the initial policy) | recursion |
| `yq_oftg_onebig12_s{1,2,3}` | 1 round × 36 inner steps (the 12-round rollout and update budget in one round, no intermediate gate) | iteration and the gate vs one-shot RL |

Compute per arm is equal (36 inner steps). The official test stays sealed; each run's final is the per-episode mean of
three evaluations (own test + `--test-eval --replicates 2`), the initial reference is the pooled Yangquan n0 mean
(58.92%, 36 evaluations) as in the Goal read-once. Jobs run one Yangquan card each (53 h limit; a 12-round run is
about 31 h at the 6-round rate, so no continuation should be needed; if one is, the addendum-26 rule applies).

## Bars (read once when all nine runs have `report.json` and their two replicate evaluations)

* **R3-long (primary): `fixed12 − nonrec12` ≥ +2.0 points**, seed-averaged per-episode paired bootstrap (10,000
  draws), 95% CI excludes 0. Same bar as R3; the claim is that recursion separates at the longer horizon.
* **R5-long: `fixed12 − onebig12` ≥ +2.0, CI excludes 0.** The claim "the gated recursive loop beats one-shot RL at
  equal compute" is made only if this passes. It is also reported against `onebig12`'s ungated single candidate
  (addendum 18 am. 1 form) as a sensitivity read.
* **R1-long (reported, bar +5 as in R1): `fixed12 − reference`.** Also reported: `fixed12 − fixed` (the 6-round
  finals of the same seeds) with its CI, descriptive.
* Noise check (two halves of the n0 evaluations) reported with every verdict. Negative readings are reported as such.

## Predictions, written before launch

* If the code-domain mechanism transfers: `nonrec12` ends near the 6-round `nonrec` finals (its generator is used
  up), `fixed12` gains 1-3 points over `fixed` (6 rounds), so R3-long passes at about +3 to +4.
* `onebig12`: plain on-policy RL for 36 steps from the initial policy regenerates its own practice every step, so it
  is itself "recursive" at the data level; the only differences from `fixed12` are the gate and the round structure.
  The honest prior is that R5-long fails (a tie, as at 6 rounds). If it passes, the gate is doing more than safety.
* If R3-long fails, the paper reports recursion on LIBERO-Goal as not shown at 12 rounds at this budget, and the
  code-domain result stands alone.

## What is not changed

Nothing registered before this addendum changes. The Goal read-once (R1-R5) is final; the self-repair read (S1-S3)
is separate and still sealed. These nine runs are read once, on their own, under the bars above.

# Prereg v3, addendum 9 (M1): acceptance on fresh paired gates, and the main-arm plans

Committed 2026-10-30 (~06:00Z) before any main arm starts and before the addendum-8 sweep reports. No v3 run
has read a test result.

## Why the acceptance test changes

Under the fixed gate (child gate >= parent's stored gate, on the same 200 placements every round), every
accepted gate gain so far has had a flat or negative audit:

| accepted node | gate change | audit change |
|---|---|---|
| A800 pilot-4 replica r01c0 | +0.0 | -1.0 |
| A800 pilot-4 replica r05c0 | +3.0 | -4.0 |
| M2 BC pilot r01c0 | +2.5 | 0.0 |

Two effects explain this:

* An accepted node was by construction lucky on that one set, so its stored score overstates it, and its
  children are measured against an inflated bar (the winner's curse).
* Repeated selection on one set fits that set.

Both are known failure modes of re-using a holdout for adaptive decisions (Dwork et al. 2015, "The reusable
holdout"). The 200-episode gate's ±2.7-point noise is larger than any per-round effect we have measured.

## The new test (`EngineConfig.gate_mode = "fresh_paired"`, this commit)

* Every round r has its own gate set of 200 sampled placements (20 per task). The seeds are 9.5e8 + 1e5 r +
  1000 t + k, disjoint from training, gate, audit and test seeds. They are drawn up front, and every one of them
  is added to the held-out set before round 1, so no training round can sample them.
* In round r the parent is scored again on round r's set. Each candidate is scored on the same set, and a
  candidate is accepted iff its score is >= the parent's paired score. The meta proposer's history reports
  this paired gain.
* The audit (200) and the official test (500, read once at the end) are unchanged.
* Cost: one extra 200-episode evaluation per round (the parent).
* Unit tests cover the behaviour:
  * the parent is re-scored per round;
  * acceptance equals (best child >= parent's paired score);
  * a proposed training case that collides with a fresh gate case is rejected;
  * a mis-configuration raises;
  * the LIBERO fresh seeds are disjoint from heldout and train seeds for run seeds 0-3, rounds <= 9, and in range.
  Fixed mode is unchanged: all earlier tests pass.

## Main arms (Yangquan, seeds 1-3, 1 card each; `mkplans_vla.py yq_main <lr> <loss>`)

The recipe is the one the addendum-8 rule picks, with the matched ratio. All arms use 64 placements per
on-policy step, 8 samples at T = 1.6, and 100 steps of batch 64.

| arm | engine |
|---|---|
| fixed | 6 rounds x 3 inner steps, fresh paired gate, fixed proposer |
| full | the same, numeric proposer, 2 candidates per round |
| nonrec | the same as fixed, each round restarts from the initial model (non-recursive) |
| shuffled | the same as fixed, rewards shuffled within each round (no real feedback) |
| onebig | 1 round x 18 inner steps: the same sampling, no intermediate gate (plain RL) |

The prereg-v3 hypotheses and their bars are unchanged and apply to these arms. They are compared only with each
other and with the Yangquan n0, never with Beijing or cavin numbers. If the addendum-8 rule picks no recipe,
these plans are not launched.

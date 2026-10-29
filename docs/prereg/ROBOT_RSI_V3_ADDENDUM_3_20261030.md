# Prereg v3, addendum 3 (M1): main arms paused, one pilot pair on update length

Committed 2026-10-30 before the pilots below start. The 15 M1 main arms submitted under addendum 2 were stopped
after ~1.5 h (n0 gate/audit only); no v3 run has read a test result, and the stopped runs are not used.

## Why

All four round-1 pilots moved the policy by less than the noise of 200-episode gate and audit sets
(n0: gate 0.165, audit 0.215):

| pilot | r01 gate | r01 audit | round 2 |
| --- | --- | --- | --- |
| GRPO lr 1e-5 | +1.0 | +1.5 | rejected |
| BC lr 1e-5 | +1.0 | +0.5 | rejected |
| GRPO lr 5e-5 | -0.5 | (rejected) | rejected |
| GRPO lr 1e-4 (addendum-2 choice) | +2.5 | **-1.5** | rejected |

The addendum-2 choice rests on a gate gain that the audit did not reproduce. A plausible reason is that the
update is short. `mixed_groups` curation keeps every sample of each mixed case. About 80 of 160 cases are
mixed, so a round yields ~660 episodes, or ~36k 8-step action chunks. The update takes 100 steps of 64 chunks,
about a fifth of one pass. The lr was varied at that length and stayed inside the noise. The length itself has
not been varied.

## Pilot pair (sealed, 1 round, GRPO, lr 1e-4, otherwise the addendum-2 program)

* `bj_oft3_pilot3_l10_s400`: 400 optimizer steps (~0.7 pass).
* `bj_oft3_pilot3_l10_s1000`: 1000 optimizer steps (~1.8 passes).

## Decision rule, fixed now

Score = mean of the r01 gate and r01 audit changes against n0, in points.
1. A pilot qualifies if its r01 is accepted and its score is at least +2.0.
2. The main arms use the qualifying pilot with the higher score. Ties go to fewer steps.
3. If neither qualifies, the main arms use the addendum-2 program (100 steps), and the paper reports that one
   round of this protocol did not measurably move the policy at any setting tried.

The `onebig` arm keeps its definition: one round with six rounds of cases, curation budget and update steps.
The prereg's main arms, seeds and bars are unchanged. Addendum 4 records the outcome before relaunch.

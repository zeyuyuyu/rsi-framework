# Train-on-test inflation of a published VLA RL result (prereg v3, secondary measurement)

Status: **measured once on the A800; replication on further placements (A800) and on Baidu is running.** This is
not yet a conclusion under the multi-angle rule.

## Question

SimpleVLA-RL's released LIBERO-10 RL checkpoint (`Haozhan72/openvla-oft-libero10-traj1-rl`) was trained with
RL on the 50 official initial states per task, the same states the benchmark tests on. How much of its
published number comes from that?

## Design

Two checkpoints, each evaluated greedily on two sets of 500 episodes on one platform (A800, the OFT backend
that reproduces SimpleVLA-RL inference):

* **official**: the 50 official initial states x 10 tasks;
* **fresh**: 500 placements newly drawn by LIBERO's own sampler (heldout seeds, 50 per task). They come from
  the same distribution as the official states, so they are not a perturbation or an OOD test.

The RL checkpoint and its own starting point (`Openvla-oft-SFT-libero10-traj1`, never trained on the test
states) are both measured. Inflation = (RL official - RL fresh) - (SFT official - SFT fresh). The second term
removes any difference in difficulty between the two sets of placements. The 95% CI comes from 2000 bootstrap
resamples of episodes within each of the four cells.

## Result

| checkpoint | official 500 | fresh 500 | gap |
| --- | --- | --- | --- |
| SFT start | 14.6% | 20.0% | -5.4 |
| RL (trained on the official states) | 87.4% | 76.0% | +11.4 |

**Inflation: +16.8 points, 95% CI [9.8, 23.4].**

Per task, RL official vs fresh: t0 78/62, t1 84/68, t2 98/92, t3 88/92, t4 80/52, t5 96/90, t6 90/50, t7 86/84,
t8 82/84, t9 92/86. The loss is concentrated in tasks 4 and 6.

## Caveats and checks

* Platform: on Baidu the same SFT checkpoint scores 18.6% on the same 500 official episodes, against 14.6% on
  the A800. The policy is sensitive to small numeric and rendering differences. The inflation estimate uses one
  platform throughout. A Baidu replication is queued.
* Replication on 500 further fresh placements per checkpoint (A800, placements 50-99 per task) is running.
* RL still improves on its start under fresh placements (20.0% -> 76.0%). The claim is that the reported number
  is inflated, not that the RL does nothing.

## Literature (2026-10-30 quick search)

These findings support the result and do not refute it. LIBERO-PRO (arXiv 2510.03827) reports collapse to near
zero under perturbed initial positions and attributes it to memorization. LIBERO-Plus (arXiv 2510.13626) reports
steep drops under small layout and initial-state changes. Both test perturbed or OOD settings. This measurement
instead uses in-distribution fresh placements and subtracts the start's own gap. No prior measurement in this form
turned up; novelty is not claimed until a targeted search is done.

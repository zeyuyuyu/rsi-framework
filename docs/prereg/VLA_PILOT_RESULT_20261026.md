# VLA one-round gate pilot: result and decision (2026-10-26 13:05Z)

Run `vla_pilot_goal` (dev seed 0, 1 round, tests sealed) with the pre-registered seed program
(GRPO on mixed groups, 160 cases x 8 rollouts at T 1.5, LoRA lr 1e-5, 200 steps x 64 frames).

* Rollouts: 1280 sampled episodes, about 3 h on 2 GPUs. Curation kept 600 items; training ran 200 steps
  over 112k frames in 14.5 min (loss 0.15 -> 0.23, clip fraction 3-6%).
* The in-run gate rollout was refused: another user's process held GPU 4 for more than 30 min. That run
  predates the 4 h admission wait. The trained candidate was then scored with
  `run_libero --heldout-eval` on gate and audit only; the test suite stayed sealed.

| | gate (50) | audit (50) |
| --- | --- | --- |
| initial | 0.80 | 0.78 |
| round-1 candidate | 0.78 | 0.82 |

Both changes are 1-2 episodes, inside the replicate noise (VLA_ADDENDUM_1). The pipeline runs end to end
(rollout, curation, GRPO update, evaluation of the new version), and one round neither breaks nor clearly
improves the policy.

**Decision:** the pre-registration lets the pilot adjust lr / steps only. Nothing here argues for a change,
so the seed program stays exactly as pre-registered and the 8 arms are released.

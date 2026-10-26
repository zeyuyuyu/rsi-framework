# Pre-registration: OpenVLA x LIBERO under the two-level RSI framework

Committed 2026-10-26, before any RSI training of the VLA and before the baseline numbers are read.

## Setup

* Model: openvla-7b-finetuned-libero-goal (LoRA r32 / alpha 16 on q,k,v,o; base frozen).
* Test: official LIBERO-goal init states, 10 tasks x 50 = 500 episodes, greedy, unbatched (one env per
  process), env re-seeded per episode (order-independent; documented deviation from the official script's
  sequential seeding). The initial model is evaluated twice to measure the run-to-run flip rate (noise floor).
* Gate / audit: 10 tasks x 10 freshly sampled placements, split 5 / 5 per task (seeds 900_000_000 + ...).
* Training cases: freshly sampled placements each round (seeds 100_000_000 + ...), never an official state.
* Oracle: simulator success flag; horizon (300 steps for goal) = failure.

## Seed program (from the literature priors, not tuned on test)

GRPO on mixed-outcome groups: 8 rollouts per case at temperature 1.5, cases = 16 per task (160), LoRA
lr 1e-5, 200 optimizer steps x 64 frames, PPO clip 0.2 / 0.28, logits scaled by the rollout temperature,
no KL. Priors: VLA-RL (tokenized OpenVLA, Goal 79.2 -> 82.2 with PPO); SimpleVLA-RL (GRPO, T 1.6);
RIPT-VLA (dynamic rejection of uniform groups). A one-round gate pilot may adjust lr / steps only.

## Arms and bars

Arms as in the code study: `fixed` (seed program), `nonrec` (frozen initial generator), `shuffled`
(success labels permuted within case), `full` (numeric-search meta proposer, 2 candidates / round).
3 rounds; 2 seeds (compute-bound; reported as such).

* V1 improvement: `fixed` or `full` final - initial >= +3.0 points on the 500 official episodes, paired
  McNemar p < 0.05 in both seeds, and the gain exceeds 2x the measured run-to-run flip rate.
* V2 feedback / V3 recursion: `fixed` - `shuffled` and `fixed` - `nonrec` >= +2.0 points, paired p < 0.05
  pooled over seeds.
* Negative readings reported as such (a VLA that does not improve is a result, not a dropped run).

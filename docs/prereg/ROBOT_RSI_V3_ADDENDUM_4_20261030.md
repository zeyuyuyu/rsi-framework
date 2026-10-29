# Prereg v3, addendum 4 (M1): short on-policy rounds (sealed pilot)

Committed 2026-10-30 before the pilot below starts. No v3 run has read a test result.

## Why

The GRPO update clips each token's probability ratio to the policy that sampled the data (0.2 / 0.28). However
long a round trains, it moves the policy roughly one PPO iteration's worth. SimpleVLA-RL needs on the order of a
hundred iterations to go from 17% to ~90% on LIBERO-10, under one point per iteration on average, and our
round-1 changes of about one point match that. More steps per round (addendum 3) may not raise the ceiling;
more rounds should. Twelve rounds of 64 placements (512 sampled episodes each) cost about the same sampling as
five rounds of 160, and give twelve policy steps. Each step is still gated.

## Pilot (sealed, OFT backend)

Amended before launch: the A800 had no free GPU (another user took the free ones), so the pilot runs
on Baidu, the M1 platform, as `bj_oft3_pilot4_short` on one GPU.

`bj_oft3_pilot4_short`: 12 rounds; curriculum 64 placements per round (8 samples, T=1.6); GRPO lr 1e-4,
100 steps of batch 64; gate and audit 200 + 200 placements as in the main arms; seed 0.

Second amendment, made after launch but before any of its results: once two A800 GPUs were freed, an A800
replica started, `a8_oft3_pilot4_short_s1`. It uses the same program on 2 GPUs with seed 1, so its training
placements differ. The decision rule below is applied to the Baidu pilot only. The replica is reported next to
it as corroboration and cannot change the decision.

## Decision rule for the M1 main arms, fixed now

1. **Short rounds** are adopted if both hold:
   * the pilot's accepted chain raises the gate by at least +5 points over n0 within 12 rounds;
   * the last accepted node's audit is at least +3 points over n0.

   The main arms then run 12 rounds of 64 placements with the addendum-2 update (100 steps). `onebig` gets one
   round with 12 rounds' cases, curation budget and steps.
2. Otherwise, if an addendum-3 pilot qualified under its rule, the main arms use that program with 6 rounds of
   160 placements.
3. Otherwise, the main arms use the addendum-2 program.

The platform split, seeds and bars are recorded in the addendum that launches the main arms.

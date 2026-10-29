# Does one GRPO round move the OFT policy the right way? (update probe, 2026-10-30)

Diagnostic for addenda 5/6, not a test result. No sealed test was read.

## Setup

`rsi.audit.update_probe` on the A800 pilot-4 replica (`a8_oft3_pilot4_short_s1`):

* adapter: ckpt-r01c0 (round 1, GRPO lr 1e-4, 100 steps of batch 64, legacy ratio)
* data: that round's own training call (00003-rollout), 96 episodes from 32 mixed cases
* log-probs of the executed action tokens at T = 1.6 under the base policy and under the merged adapter

Noise floor: the base model is rerun on 32 of those episodes with the forward-batch windows shifted by 4 frames,
so the weights and tokens are the same and only the batch neighbours change.

## Result (`results/a800/runs2/probe_pilot4_s1_r01/update_probe.json`)

| quantity | value |
|---|---|
| corr(advantage, per-episode mean log-prob change) | **0.92** |
| successful episodes (n = 26): mean change per token | +0.020 (sd 0.015) |
| failed episodes (n = 70): mean change per token | -0.045 (sd 0.024) |
| tokens whose adapter/base ratio is outside [0.8, 1.28] | 12.7% |
| greedy-token agreement, adapter vs base | 95.2% |
| noise floor: per-episode mean abs change | 0.0007 |
| noise floor: per-token mean abs change | 0.005 |
| noise floor: tokens outside [0.8, 1.28] | 0.5% |

## Reading

1. The update is not broken. On its own training episodes it raises the log-prob of above-average attempts and
   lowers the rest, as GRPO should. The per-episode shifts are 30-70x the noise floor.
2. Most of the movement is pushing failures down: they are 70 of 96 episodes, and failed episodes run longer,
   so they carry more tokens.
3. Shifting batch windows by 4 frames (batches of 8) explains only 0.5% out-of-band tokens. The 5.3% seen at
   training step 1 (addendum 6) needs another source. Candidates: the training pass's sub-batches of 1-3 frames
   after grouping by prompt, or train vs eval mode. `ratio_check` (queued after this probe) measures step 1 under
   both ratio modes. Addendum 6's validity rule stops pilot6 if matched does not bring it under 0.1%.
4. So the open question is not the direction of the update but how much one round transfers to new placements.
   That is what the addendum-5 learning curve (18 on-policy steps) measures.

## Ratio check (`rsi.audit.ratio_check`, same round-1 train spec, 3 steps per mode, A800 GPU 5)

| ratio mode | step-1 share outside [0.8, 1.28] | step-1 mean abs log-ratio | step-1 max | clipped share, steps 1/2/3 |
|---|---|---|---|---|
| legacy | 0.0533 | 0.044 | 0.78 | 0.053 / 0.081 / 0.128 |
| matched | **0** | **0** | **0** | 0 / 0.072 / 0.117 |

* The legacy step-1 value equals the receipt's (0.0533), so the effect is deterministic, not a one-off. The
  mean shift (0.044) is 9x the batch-shift floor above (0.005), so the training pass's prompt-grouped
  sub-batches or train vs eval mode are the source, not neighbours alone. Matched removes it completely, which
  meets addendum 6's validity condition before pilot6 starts.
* In both modes one Adam step at lr 1e-4 takes 7% of tokens past the band, and two steps take 12%. The plateau
  of ~11% over the remaining steps (addendum 6 table) is reached within three steps of the 100. Per batch, the
  update spends nearly all its steps at the trust-region edge. This is consistent with "one round is about one
  PPO iteration" (addendum 4) and argues for more on-policy batches, not more steps per batch.

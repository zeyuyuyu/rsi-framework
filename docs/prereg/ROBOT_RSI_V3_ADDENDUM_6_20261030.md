# Prereg v3, addendum 6 (M1): the PPO ratio starts away from 1 (numerics), and a matched-ratio pilot

Committed 2026-10-30 before the pilot below starts. No v3 run has read a test result.

## Finding

The receipt of the first training call of the A800 pilot-4 replica (`a8_oft3_pilot4_short_s1`, ckpt-r01c0,
256 episodes, 14,013 chunks) records the share of counted tokens whose PPO ratio fell outside the clip band
[0.8, 1.28] at each optimizer step:

| step | 1 | 2 | 3 | 4-10 (mean) | 11-100 (mean) |
|---|---|---|---|---|---|
| clipped share | 0.053 | 0.075 | 0.121 | 0.12 | 0.11 |

Step 1 runs before any parameter update. The adapter is freshly initialised with B = 0, so the policy is
exactly the parent and every ratio should be 1. 5.3% of tokens are outside the band anyway. The train worker
takes the old log-probs in one pass over the frames in episode order (eval mode, micro-batches of 16
consecutive chunks). It takes the training log-probs on shuffled batches whose frames sit beside different
neighbours. The model has no dropout: the checkpoint config sets none and the SDPA path uses 0 outside training.
So the difference is numerical. The forwards run in bf16, and a frame's logits depend on the shape and makeup
of the batch it shares. At the rollout temperature (1.6) the sampled tokens are often in the flat tail, where
a logit change of about 0.35 already moves the log-prob past log 1.28.

Consequences: a token pushed outside the band by noise in the advantage's direction gets no gradient (about
half of the 5%), and the clipped share stops showing how far the update moved the policy. This is a small
effect on its own. It also matches the train-inference mismatch reported for bf16 RL on LLMs; see
"Defeating the Training-Inference Mismatch via FP16" (Qi et al., arXiv 2510.26788) and MiniMax-M1's FP32
LM-head fix (arXiv 2506.13585). We cannot yet
say it limits learning here. The claim is only that the implementation was not doing what PPO assumes.

## Change (opt-in, code be9dfc1 + 0089086)

`train_worker` gets `update.ratio`:

* `legacy` (default): bit-for-bit the old behaviour. The pick schedule and the old pass are unchanged, so
  every running and earlier run is unaffected.
* `matched`: the old log-probs come from exactly the micro-batches the training loop will run (same chunks,
  same grouping, train mode, no grad). The ratio starts at 1, and only the update moves it.

The mode is a trainer numerics setting in the plan's `vla` block (`VLAConfig.ratio_mode`), not a program
field, so the meta level never searches it. Receipts now record the step-1 log-ratio (mean, max, share outside
the band). `rsi.audit.ratio_check` reruns a recorded train spec for 3 steps in each mode on the A800 (queued),
and `update_probe` now also reports a noise floor: the same weights, with frames batched beside other
neighbours.

## Pilot (sealed, Baidu, 1 GPU, seed 0)

`bj_oft3_pilot6_curve_matched`: identical to addendum 5's `bj_oft3_pilot5_curve` (6 rounds x 3 inner steps of 64
placements, GRPO lr 1e-4, 100 steps of batch 64, always accept, gate and audit 200 + 200, seed 0) except
`vla.ratio_mode = "matched"`. Same seed, so the placements match round by round. The comparison with
`pilot5_curve` is paired on the training placements and isolates the ratio.

Amendment, made after pilot6 was submitted but before any of its results: an A800 GPU was free, so an A800
replica runs: `a8_oft3_pilot6_curve_matched_s1`. It uses the same program and ratio mode with seed 1 on 1 GPU,
so its placements differ, and it runs from a separate code tree (src3). As with addendum 4's replica, it is
reported next to pilot6 as corroboration and cannot change the decisions below. Before launch, the A800
`ratio_check` on the pilot-4 replica's round-1 spec gave step-1 out-of-band shares of 0.0533 (legacy) and
exactly 0 (matched) (docs/results/UPDATE_PROBE_20261030.md).

## Use of the results, fixed now

1. **Validity.** pilot6's first receipt must show a step-1 out-of-band share below 0.001. Otherwise the fix
   did not work: pilot6 is stopped and its results are not used.
2. **Main arms.** They use `ratio_mode = "matched"` if, after the 18 steps, pilot6's last gate and last audit
   are each at least pilot5_curve's minus 3 points (non-inferior). Matched is then preferred because it is the
   PPO ratio as intended. Otherwise they keep `legacy`.
3. **Superiority claim.** We claim matched helps only if it beats pilot5_curve by at least +5 points on both
   the last gate and the last audit. One seed and ±2.7-point gate noise allow nothing finer.
4. Addendum 5's rules for the program (gated rounds of 3 inner steps vs addendum 4) are unchanged. This
   addendum decides only the ratio mode.

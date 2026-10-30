# Prereg v3, addendum 7 (M1): plain RL at lr 1e-4 stops helping after 3 steps; smaller-step curves

Committed 2026-10-30 (~05:00Z) before the pilots below start. No v3 run has read a test result.

## Evidence so far (all sealed pilots, gate and audit 200 + 200 placements)

| run | what happened |
|---|---|
| `bj_oft3_pilot5_curve` (lr 1e-4, always accept) | gate n0 0.165 → 0.175 after 3 on-policy steps → **0.150 after 6** |
| `bj_oft3_pilot5_gated` (identical through round 1) | 0.180 after 3 steps; the 6-step candidate scored **0.140**, rejected |
| `bj_oft3_pilot4_short` (1 step per round) | 0.165 → 0.175 → 0.175 → 0.185 (round 3), then three rejected children (0.175, 0.165, 0.17) |
| `a8_oft3_pilot4_short_s1` (A800, seed 1) | children of r01c0 (0.18): 0.155, 0.16, 0.165, then 0.21, accepted with **audit 0.175**, against an audit of 0.215 at n0 |
| `a8_oft3_pilot4_short_s1` and M2 BC pilot | every accepted gate gain so far has a flat or negative audit change |

Supporting diagnostics (docs/results/UPDATE_PROBE_20261030.md):

* The update moves log-probs in the advantage direction (corr 0.92). But failed attempts dominate it: they are
  73% of episodes and run to the step limit. The probe measured -0.045 per token on failures against +0.020 on
  successes.
* At lr 1e-4 one Adam step takes 7% of tokens past the clip band, and three steps take ~12%. So each batch pushes
  the policy to the trust-region edge almost immediately.
* Addendum 2's round-1 lr ordering (1e-5 +1.0, 5e-5 -0.5, 1e-4 +2.5) is within gate noise (±2.7 points), so the
  lr 1e-4 choice was close to arbitrary.

Reading: within 18 steps, the lr-1e-4 update does not improve the greedy policy past the first few steps, and
probably degrades it. Addendum 5 fixed this case in advance: "the next change targets training". Gating cannot
rescue an update that does not improve. Gating also selects gate-set noise, as the gate/audit reversals show.

## Deviations, recorded before they take effect

1. `bj_oft3_pilot4_short` is stopped at round 6 of 12, and `bj_oft3_pilot5_gated` at round 2-3 of 6. Their
   adoption rules (addenda 4 and 5) are not evaluated, and what they produced is reported as is. Reason: the M1
   main arms cannot wait for them, and they hold two of the three Baidu slots. pilot4 would need a gate of at
   least 0.215, and its last three children scored 0.165-0.175. pilot5_gated's chain sits at the 3-step node.
2. `bj_oft3_pilot6_curve_matched` (never started) is cancelled, because its lr is being replaced. All new pilots
   use the matched ratio, on the step-1 evidence: `ratio_check` 0, and both A800 matched receipts 0. Addendum
   6's paired pilot6 comparison is therefore not run. The A800 matched replica (lr 1e-4, seed 1) keeps running as
   the lr-1e-4 curve's second seed.
3. The A800 pilot-4 replica (corroboration only) is stopped to free its GPUs.
4. The two Baidu RL inflation evals (never started) are resubmitted behind the new pilots. They do not affect
   any decision.
5. `bj_oft3_pilot5_curve` keeps running unchanged as the lr-1e-4 reference curve.

## Pilots (sealed, Baidu, 1 GPU each, seed 0, so placements are paired with pilot5_curve)

Identical to `bj_oft3_pilot5_curve` (6 rounds x 3 inner steps of 64 placements, 100 steps of batch 64, always
accept, gate and audit 200 + 200), except as listed:

* `bj_oft3_pilot7_lr3e5`: lr 3e-5, `vla.ratio_mode = "matched"`.
* `bj_oft3_pilot7_lr3e5_ep`: the same, plus `vla.loss_agg = "episode"`. Each chunk is weighted 1 / (chunks of
  its episode), so every episode carries equal total weight and long failures stop dominating (code: this
  commit; the default "token" is unchanged).

Validity: the first receipt of each must show a step-1 out-of-band share of 0, and the declared `loss_agg`.
Otherwise the pilot is stopped and fixed. An A800 seed-1 replica of `pilot7_lr3e5_ep` runs as corroboration if
GPUs are free, and it cannot change the decision.

Amendment (after launch, before any pilot7 result): a second A800 GPU freed up, so
`a8_oft3_pilot7_lr3e5_s1` (token loss) also runs, next to `a8_oft3_pilot7_lr3e5_ep_s1` and the matched lr-1e-4
replica `a8_oft3_pilot6_curve_matched_s1`. Every curve in the rule below then has a seed-1 A800 counterpart.
These counterparts are reported as corroboration and do not enter the rule.

## Decision rule for the M1 main-arm update, fixed now

For each curve (pilot5_curve, pilot7_lr3e5, pilot7_lr3e5_ep), S is the mean over its last two evaluated rounds
(5 and 6) of (gate + audit) / 2, i.e. 800 episodes. n0's value on Baidu is (0.165 + 0.215) / 2 = 0.19.

1. The main arms use the update of the curve with the highest S, if that S is at least 0.22 (n0 + 3 points).
   If two curves are within 1 point, the one with fewer changes from pilot5_curve wins.
2. If no curve reaches 0.22, the M1 main arms are not launched with any of these updates. The next addendum
   then states what changes, and the result is reported as a negative finding of the study.
3. Separately from this rule, the gate/audit reversals above call for a new acceptance test: fresh gate
   placements each round, with parent and child evaluated on them paired. That is designed in its own
   addendum before any main arm starts.

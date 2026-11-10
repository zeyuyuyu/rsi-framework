# Playbook for the meta level (22 finished runs: libero_goal, libero_spatial, libero_10)

## 0. How to read these numbers
- Gate scenes are resampled every round. All numbers below are gate (greedy success) on those scenes. The records contain no test results.
- **Noise of one gate reading is about 0.03 (sd).**
  - a8_goalmain_fixed_s0: the unchanged start policy n0 was read as 0.600, 0.610, 0.640, 0.610 and 0.545 in rounds 0-4 (range 0.095).
  - a8_goalmain_fixed_s3: the same unchanged policy was read as 0.555, 0.600, 0.625, 0.600 and 0.560 (range 0.07).
  - a8_m2_pre_rep_s2: two siblings from the same parent with the same procedure differed by 0.010, 0.050, 0.010, 0.010, 0.005 and 0.055. RMS is 0.031, so one gate has sd of about 0.022 plus the eval difference.
- **What counts as evidence:**
  - A single child-minus-parent change below about 0.06 is noise. Only a8_m2_pre_rep_s2 r03 (+0.085) and a8_spatmain_llm_harness_cap_s1 r02c1 (+0.070) exceed it.
  - A procedure claim needs a start-to-end gain of at least 0.10 that repeats in at least 3 seeds. Alternatively, it needs a paired comparison against a replica run of the baseline.
  - Never read 'kept' as 'improved'. With 2 children per round, best-of-2 plus the keep-if-not-worse rule inflates the sum of kept changes by roughly +0.02 per round.

## 1. Reliable and unreliable starting points
- **Reliable (never fell below start minus 0.03 in any run):**
  - GRPO, lr 3e-5, steps 100x64, T=1.6, scenes 64x8 on libero_goal.
    - Gated runs a8_goalmain_fixed_s0-s3: lowest gates 0.585, 0.570, 0.575 and 0.555.
    - Net start-to-final changes: +0.015, +0.05, +0.055 and +0.045.
    - The always-accept curve a8_oftg_curve_grpo_s1 went 0.550 to 0.625 (+0.075).
    - Expect about +0.04 over 6 rounds. This is small but consistent in sign.
  - Same GRPO on libero_spatial, a8_ofts_curve_grpo_s0: 0.600 to 0.655, rounds all kept, peak 0.670.
  - GRPO, lr 1e-4, matched ratio, token loss, on libero_goal, replicas a8_m2_pre_rep_s0-s3.
    - Kept 5 of 6 rounds in every replica; lowest gates 0.56-0.57; sums of kept changes +0.135, +0.145, +0.180 and +0.170.
    - For rep_s2 the gate went 0.565 to 0.715 (best child, so inflated by selection).
- **Not reliable:**
  - BC at lr 1e-5 on libero_goal (section 2).
  - libero_10 GRPO. Gates were 0.15-0.21 and flat in all four runs.
    - a8_oft3_pilot6 (lr 1e-4): 0.185 to 0.150.
    - a8_oft3_pilot7_lr3e5: 0.175 to 0.180.
    - a8_oft3_pilot7_lr3e5_ep: sum of kept changes -0.005.
    - a8_oft3_pilot4_short: 0.180 to 0.210, kept 2 of 5.
    - No procedure change tried there moved it. Sampled success of 0.15-0.2 gives few mixed groups to learn from.
  - a8_pilot_fail1 and a8_pilot_fail2 (lr 1e-4, T=2.0, 3 rounds). Gates stayed 0.55-0.67, so the records do not show why they were labelled failures. Treat T=2.0 as untested rather than harmful.

## 2. Training-side signatures before a policy got worse, and the recovery
All collapses were in BC runs (lr 1e-5, operator bc).
- **a8_oftg_curve_bc_s1** (always-accept).
  - Gate: 0.585, 0.545, 0.575, then 0.400, 0.145, 0.070.
  - Warning came a round before the gate fell:
    - round 3 sampled success fell inside the round, 0.537/0.467/0.338;
    - round 3 loss_first jumped from about 0.4 to 1.32;
    - round 4 mixed share fell to 0.35/0.25/0.08, then to 0.03-0.12.
  - The gate at round 3 (0.575) still looked fine.
- **a8_oftgb_full_s0.**
  - Round 4 sampled success 0.596/0.481/0.310 and loss 1.45.
  - That policy was kept with gate 0.615 (parent 0.600), and its children began at sampled success 0.185.
  - Round 5 children scored 0.485 and 0.550 against parent 0.640 (-0.155 and -0.09). Round 6 children scored 0.52 and 0.50.
  - Greedy gate hid the damage for one round.
- **a8_oftgb_fixed_s0.**
  - Rounds 5 and 6 had loss_first 1.1-1.2 and sampled success down to 0.365 at step 3.
  - Gate stayed 0.59-0.645, so this is a warning, not proof of collapse.
- **Healthy GRPO runs:**
  - Sampled success was flat at 0.55-0.65 on goal.
  - Mixed share was 0.45-0.65 on goal and 0.15-0.38 on spatial, which is normal there.
  - Loss was around 0 ±0.2 with episode aggregation. Loss scales differ by loss_agg and operator, so compare only within a run.
- **Rule:** if sampled success falls by more than 0.15 across the 3 inner steps, or loss_first doubles, or mixed share drops below about 0.3 on goal, then stop trusting the gate. Revert to the last policy with healthy practice curves, and do not use always-accept.
- **What brought it back:**
  - Gate-based rejection held the parent in a8_oftgb_full_s0, but only a policy from before the practice curves broke.
  - Switching the operator from bc to grpo with mixed_groups (lr 2e-5, steps 200, T=1.2) in a8_oftgb_llm_harness_s0 round 1 took the gate from 0.570 to 0.595, then 0.695 at round 5 and 0.685 at round 6, with no collapse over 6 rounds. This is one run.
  - bc_temp=rollout (a8_oftgb_full_s0 r05c1) softened the in-round decline (0.185/0.183/0.252 against 0.185/0.081/0.037 for its sibling) but still scored below parent. It is not a fix.

## 3. Edits: what the records support
- **LLM edits did not beat re-running the same procedure.**
  - m2_pre LLM runs s0-s3: sums +0.095, +0.105, +0.095, +0.165 (mean 0.115), kept 4, 5, 3, 5.
  - m2_pre replicas: sums +0.135, +0.145, +0.180, +0.170 (mean 0.158), kept 5 each.
  - a8_m2_pre_llm_s4 stopped after one round with both children below parent.
- **goalmain LLM runs** (llm_s1-s3: +0.17, +0.15, +0.125; harness_cap s1-s3: +0.135, +0.170, +0.085) beat fixed (+0.055, +0.140, +0.005, +0.030).
  - They also had 2 candidates per round, and replicas show best-of-2 alone gives about +0.15.
  - There was no 2-candidate replica of the lr 3e-5 start, so the benefit of the edits is not separable.
- **Edits tried many times with no consistent effect:**
  - solver.temperature in 1.0-1.3, curriculum.allocation progress or weights, cases, samples, update.lr in 1e-5 to 5e-5, steps 50-500, batch 32-128, curation.budget, zscore advantage.
  - The lowering of lr to 1e-5 or 1.5e-5 and the larger scene counts of 200-240 cases sat in runs with sums +0.15, +0.125 and +0.17, while cases=96 only had +0.17. There is no dose-response.
  - task_weights that zero out two tasks: m2_pre_llm_s0 +0.095 and s3 +0.165. This is inconsistent.
  - clip_high=0.264, tried twice, scored -0.030 and -0.030 against siblings at -0.020 and -0.005. Not distinguishable from noise, so treat it as no gain.
  - update.ratio=legacy plus floor 0.149 on spatial: +0.020 on one child. No evidence.
- **Supported with caution:**
  - Moving from bc to grpo with mixed_groups (above).
  - zscore advantage appears in the best runs (a8_oftgb_full r02c1 +0.025, spat r02c1 +0.07) but also in neutral ones. This is unproven.

## 4. Guidance for the next rounds
1. Start from GRPO with mixed_groups. Default to lr 3e-5 or 1e-4 with matched ratio. Avoid BC on its own at lr 1e-5 unless the practice curves are watched.
2. Keep the gate decision. Never use always-accept for more than 2 rounds. Compare sampled_success_per_step and loss_first of the kept candidate before the next round, not just the gate.
3. Spend candidates on replicas of the current best procedure, or on one change at a time. Two children that differ by under 0.05 say nothing about the edit.
4. Do not stack several edits in one candidate (a8_oftgb_llm_harness_s0 r01c1 changed 7 fields), because credit cannot be assigned.
5. On a hard suite (sampled success below 0.25, mixed share 0.4-0.6, as in libero_10) no tried edit helped. Test a larger change, such as many more samples per scene or an easier curriculum, before more tuning of lr or temperature.
6. Report gains as start-to-end over at least 3 seeds, not as sums of kept changes. Typical honest GRPO gain on goal is +0.04 to +0.15 over 6 rounds, and part of that is selection.

# Prereg v3, addendum 1 (M1, OpenVLA-OFT on Baidu): pilot results and one extra pilot pair

Committed 2026-10-29, before any v3 main arm and before the extra pilots below. No test suite has been read
by any v3 run: the pilots ran with `seal_tests`.

## M1 starting point (no bar; context for the pilots)

OpenVLA-OFT 1-demo SFT (`Haozhan72/Openvla-oft-SFT-libero10-traj1`; weights digest equal to the A800 copy,
`0210abee...71bc0`), LIBERO-10 official 500 episodes on Baidu: **18.6%** (93/500; normal 95% CI 15.2-22.0;
SimpleVLA-RL reports 17.3%). Two independent jobs gave identical per-episode outcomes on all 500 episodes,
so evaluation on this stack is deterministic. Per task: 8, 24, 62, 24, 2, 22, 10, 12, 4, 18%.

## The two prereg pilots (sealed, 2 rounds, seed 0)

Shared: curriculum 160 fresh placements per round, 8 samples at T=1.6, curation budget 400, LoRA r32,
lr 1e-5, 100 optimizer steps of batch 64 (one item = one 8-step action chunk).

| pilot | n0 gate / audit | r01c0 gate / audit | r02c0 gate | retained |
| --- | --- | --- | --- | --- |
| GRPO on mixed groups | 0.165 / 0.215 | 0.175 / 0.230 (accepted) | 0.145 (rejected) | r01c0 |
| success-only BC | 0.165 / 0.215 | 0.175 / 0.220 (accepted) | 0.160 (rejected) | r01c0 |

Gate and audit are 200 sampled placements each (20 per task), greedy, identical placements across versions.
Sampling success at T=1.6 was 18-20% with about half the cases mixed, so the curation had signal.

**Decision 1: operator GRPO** (gate tie; audit +1.5 vs +0.5 points; GRPO also learns from failed attempts).

## Deviation: one extra sealed pilot pair (lr)

Both update rules moved the gate by one point (2 of 200 episodes) per round. At that step size six rounds
cannot plausibly reach the M1 improvement bar (R1, +5 points), so the main arms would test the protocol's
step size rather than RSI. The prereg allowed exactly two pilots; it also lists lr among the settings the
pilots may set, and the two pilots varied only the operator. One more pair is therefore run, still sealed and
read on gate and audit only:

* `bj_oft3_pilot2_l10_lr5e5`: GRPO, lr 5e-5, otherwise identical.
* `bj_oft3_pilot2_l10_lr1e4`: GRPO, lr 1e-4, otherwise identical.

Rule, fixed now: the main arms use the lr of the pilot with the higher r01 gate; ties go to the higher
r01 audit, then to the lower lr. If neither beats lr 1e-5 (r01 gate 0.175), the main arms use lr 1e-5.
Nothing else changes. Addendum 2 records the outcome and the frozen seed program before the main arms start.

## Other changes since the prereg, made before any main arm

* Engine fix (137a701): candidates of the same round now share that round's training cases. Before the
  fix, a meta-level candidate that edited the solver or curriculum re-proposed the round's placements, and
  the engine dropped them as duplicates. That candidate then trained only on the leftover cases or
  crashed. Every completed `full` arm (v2 VLA, code-era cross-model) shows this, so earlier full - fixed
  comparisons are biased against the meta level and are reported with that caveat. All v3 arms use the
  fixed engine.
* `onebig` validates its summed six-round budget through a per-plan `budget_scale` (3acba4c). The edit space
  searched by `full` is unchanged.
* Replicate test evaluations (prereg: finals evaluated 3 times) are dropped for M1: the evaluation is
  deterministic, so replicates repeat the same 500 outcomes. M2 (OpenVLA on the A800) keeps them.

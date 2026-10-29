# Prereg v3, addendum 2 (M1, OpenVLA-OFT on Baidu): frozen seed program

Committed 2026-10-30 before any M1 main arm. No v3 run has read a test suite.

## Extra lr pilot pair (addendum 1), round 1 (the decision round)

| pilot | n0 gate / audit | r01c0 gate | decision |
| --- | --- | --- | --- |
| GRPO lr 1e-5 (pilot 1) | 0.165 / 0.215 | 0.175 (accepted) | |
| GRPO lr 5e-5 | 0.165 / 0.215 | 0.160 (rejected) | |
| GRPO lr 1e-4 | 0.165 / 0.215 | **0.190** (accepted) | chosen |

The addendum-1 rule (highest round-1 gate) picks **lr 1e-4**. The ordering is not monotone in lr (5e-5 below
1e-5), so a 2.5-point gate gain is within what 200 episodes can move by chance; the choice follows the rule
and is not evidence on its own. Round 2 of the extra pilots finishes later and is reported without changing
the choice.

## Frozen M1 seed program

GRPO on mixed-outcome groups; curriculum 160 freshly sampled placements per round, uniform over the 10 tasks;
8 samples per placement at T=1.6; curation budget 400, 2 per case; LoRA r32 alpha16 on q/k/v/o;
**lr 1e-4**, 100 optimizer steps of batch 64 (one item = one 8-step action chunk), clip 0.2 / 0.28.

## Main arms (prereg v3, unchanged otherwise)

`fixed`, `full` (numeric proposer, 2 candidates per round), `nonrec`, `shuffled`, `onebig` (one round with
cases, curation budget and update steps x6, `budget_scale` 6); seeds 1, 2, 3; 6 rounds; LIBERO-10; gate and
audit 200 + 200 placements; the engine evaluates the official test on the initial version and on every accepted
version, no in-run decision reads it, and it is read once the run has ended (finals are not replicated:
evaluation is deterministic, addendum 1). Bars R1-R5 as in the
prereg; M1's R1 threshold is +5.0 points.

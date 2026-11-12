# Spatial: the guard-rail gate against one-shot RL (addendum 33, primary read), 2026-11-12

Status: **registered read, primary, done once (2026-11-12 ~18:25Z).** Under amendment 4 the primary pools the within-platform pairs Y1-3 (Yangquan) and A0-A1 (A800 node). The fresh-scene test is primary and the official test is read beside it. Replications A2/A3 (A800) and B1-3 (Beijing) are read separately when complete; Beijing has not started.

## Design

- **Guard-rail loop**: `*_guard_s<seed>` is the 6-round Spatial loop with the guard-rail gate (min_gate_gain −0.05, gate_floor 0.05), on source v32.
- **Controls**: the strict-gate loop `*_fixed` and one round of plain RL with the whole budget `*_onebig`, on the same recipe and seed. Equal training compute.

Readers:
- Fresh scenes: `fresh_read.py spatial_guard_pooled` (primary), `spatial_guard` (Yangquan), `spatial_guard_a8` (A800).
- Official test: `spatial_guard_read.py` (primary).
- Outputs: `results/fresh_spatial_guard_{primary,yq,a8}_20261112.json`, `results/spatial_guard_primary_read_20261112.json`.

## Results

| claim | fresh scenes (primary) | official test |
|---|---|---|
| **GS3** guard − one-shot RL, Y1-3 + A0-1 | **+0.48 [−0.44, +1.44]**: non-inferior (lower bound > −2), not superior | +0.21 [−0.95, +1.39]: non-inferior, not superior |
| GS3 Yangquan only | +0.83 [−0.30, +1.93] | +0.80 [−0.87, +2.44] |
| GS3 A800 only | −0.05 [−1.60, +1.50] | −0.67 [−2.57, +1.17] |
| GS2 guard − strict gate (≥ +2) | +0.35 [−0.62, +1.32], fails | +0.73 [−0.77, +2.25], fails |
| GS1 guard − start | **Yangquan +5.38 [+3.83, +6.92], passes (+3)**; A800 +8.10 [+6.22, +10.00] | Yangquan +1.55 [−0.62, +3.79], fails (R1, +5); A800 +0.91 |

Per pair, GS3 on fresh scenes: Y1 +1.1, Y2 +1.7, Y3 −0.3, A0 +0.4, A1 −0.5.

The guard-rail loop accepted a candidate in every one of its 30 rounds (6 rounds × 5 seeds).

## Predictions against outcome

| written before launch | outcome |
|---|---|
| GS3 fresh between −1 and +2 | **Hit** (+0.48) |
| non-inferior, 80% | **Hit** (both tests) |
| superior, 25% | did not happen |
| GS2 between 0 and +2 | **Hit** (+0.35) |
| GS1 between +5 and +8 | **Hit** on Yangquan (+5.38) |

## Reading

- At equal training compute on the hand-tuned recipe, the guard-rail loop is non-inferior to one-shot RL on Spatial on both tests, within two points, with point estimates of +0.5 and +0.2. It is not better.
- On Spatial the strict gate had been no worse than RL either (F5 +0.38), and the guard rail changes little there (GS2 +0.35). The guard rail matters where the strict gate discarded rounds, which is the Goal 12-round loop (addendum 32 Part A: −2.7 → −1.1).
- With the earlier reads, the record on the tuned recipe is a tie with plain RL at equal training compute. The framework's advantages lie elsewhere:
  - It protects a recipe that degrades: +13 against plain self-training (NG1, N1).
  - It reaches tuned RL without the tuning sweep (descriptive, `TUNING_COST_20261112.md`).

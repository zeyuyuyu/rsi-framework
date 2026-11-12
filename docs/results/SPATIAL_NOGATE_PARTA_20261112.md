# Spatial: the framework against plain training (addendum 31, part A: N1 and N3), read 2026-11-12

Status: **registered read, part A, done once (2026-11-12 ~07:05Z).** N1 passes its registered bar on the official test. On the fresh scenes it is positive but under +10. Both written predictions miss on the registered seeds. Part B (N2, meta3) waits for `yq_oftsb_meta3_s2/s3`, as amendment 2 sets out.

## Design

- **Recipe and seeds**: the addendum-29 `bc_start` plan on LIBERO-Spatial (BC on verified self-generated successes), 6 rounds × 3 inner steps, Yangquan seeds 1-3. Seed 0 on the A800 node is reported alongside (amendment 1).
- **plain training** (`yq_oftsb_nogate`): every round's child is kept. One candidate per round.
- **gate only** (`yq_oftsb_fixed`): fresh paired gate. One candidate per round, so the same training compute.
- **Bars**: on the official test (three-evaluation finals). The fresh-scene test is read beside it with the same bars.
- **Reader**: `scripts/report/spatial_nogate_read.py --part A` → `results/spatial_nogate_partA_20261112.json`.

## Results

| claim | official test (registered bar) | fresh scenes (beside it) |
|---|---|---|
| **N1** gate only − plain training, seeds 1-3 | **+13.00 [+10.44, +15.60]**, passes (≥ +10, CI > 0) | +8.37 [+6.67, +10.07], CI > 0, under +10 |
| N3 plain training − start, seeds 1-3 | −14.99 [−18.24, −11.87] | −7.15 [−9.21, −5.08] |
| N1 with seed 0, within platform (alongside) | +23.23 [+20.90, +25.58] | +21.90 [+20.32, +23.47] |

Final success, %, official / fresh:

| seed | plain training | gate only |
|---|---|---|
| 1 | 44.2 / 50.9 | 58.8 / 58.9 |
| 2 | 45.9 / 53.2 | 59.0 / 63.9 |
| 3 | 45.6 / 53.1 | 56.9 / 59.5 |
| 0 (A800) | **1.2 / 1.8** | 55.1 / 64.3 |
| start | 60.2 (Yangquan pooled n0) / 59.6 | |

On seed 0 the plain-training gate record shows the collapse happening:
- Gate scores by round: 0.605, 0.61, 0.645, 0.625, then **0.395** at round 5 and **0.035** at round 6.
- This is the same shape as the Goal run of addendum 12.

## Predictions against outcome

| written before launch | outcome |
|---|---|
| Plain training collapses on at least two of three seeds (final < 30%, N3 under −25) | **Miss on seeds 1-3.** They lose 14-16 points on the official test and 6-9 on the fresh scenes, ending at 44-53%. The A800 seed does collapse, to 1.2%. |
| N1 and N2 pass by +25 or more | **Miss for N1 on seeds 1-3:** +13.0 official, +8.4 fresh. With seed 0 it is +23.2 / +21.9. N2 is part B. |
| If plain training does not collapse (N3 within 5 points), N1 and N2 fail | Does not apply. N3 is −15.0 on the official test, far outside 5 points. |

## Reading

- At equal training compute, the framework's gate ends 13.0 points above plain training of the same recipe on Spatial's official test, on every seed (+11.3 to +14.6). That meets the registered bar.
- On unseen scenes the gap is smaller, +8.4 [+6.7, +10.1]. It is positive on every seed but misses the +10 bar.
- As on Goal, the difference is protection. Plain training slides below its start, and on one seed (A800) it collapses completely. The gated loop stays at its start, between −3.3 and +4.4 against the reference across seeds 1-3 and both tests.
- This is plain self-training (RFT / expert iteration), not GRPO.

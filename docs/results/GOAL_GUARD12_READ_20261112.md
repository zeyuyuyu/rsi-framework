# Goal, 12 rounds with the guard-rail gate (addendum 32 Part A), read 2026-11-12

Status: **registered read, done once (2026-11-12 ~17:25Z).** As registered, the fresh-scene test is primary and the official test is reported beside it.

## Design

`yq_oftg_guard12_s{1,2,3}` is the addendum-27 `fixed12` plan with the guard-rail gate: a child is refused only if it falls more than 5 points below its parent or below the start. It is compared on the same seeds, with the same practice placements and gate sets, against:
- `yq_oftg_fixed12`, the strict gate;
- `yq_oftg_onebig12`, one round of plain RL with the whole 12-round budget (equal compute).

Readers: `fresh_read.py goal_guard12` → `results/fresh_goal_guard12_20261112.json`; `goal_guard_read.py guard` → `results/goal_guard12_read_20261112.json`.

## Results

| claim | fresh scenes (primary) | official test (three-evaluation finals) | bar |
|---|---|---|---|
| G1 guard12 − start | **+5.21 [+3.35, +7.12], passes** | +2.45 [−0.11, +5.05], fails (R1 rule; 1 of 3 seeds individually > 0) | ≥ +5, CI > 0 |
| G2 guard12 − fixed12 (strict gate) | +1.67 [+0.00, +3.30], fails (under +2) | +0.89 [−1.11, +2.89], fails | ≥ +2, CI > 0 |
| G3 guard12 − onebig12 (plain RL) | −1.07 [−2.63, +0.53]: lower bound under −2, non-inferiority **not** shown | **+0.51 [−1.42, +2.47], non-inferior** | non-inferior if lower bound > −2 |

Fresh finals, %:

| seed | guard12 | strict gate | plain RL |
|---|---|---|---|
| 1 | 66.9 | 60.9 | 66.8 |
| 2 | 64.9 | 66.9 | 65.5 |
| 3 | 63.9 | 62.9 | 66.6 |
| start | 60.0 | | |

Rounds kept: 12, 12 and 11 of 12.

## Predictions against outcome

| written before launch | outcome |
|---|---|
| Keeps at least 11 of 12 rounds on every seed | **Hit** (12, 12, 11). |
| G1 +5 to +7, 60% to pass +5 | **Hit:** +5.21, passes on the primary test. |
| G2 +2 to +4, 55% | **Miss:** +1.67, just under. |
| G3 between −2 and +1, non-inferior, 60% | **Partly:** the point estimate is in range (−1.07), but the lower bound (−2.63) misses non-inferiority on the primary test. It is non-inferior on the official test. |

## Reading

- With the guard-rail gate, the twelve-round Goal loop passes its improvement bar on unseen scenes, +5.2 over its start. The strict-gate loop reached +3.5 under the same bar.
- The gap to plain RL on unseen scenes shrinks from −2.7 (strict gate, FL5) to −1.1 [−2.6, +0.5], so the two are no longer distinguishable.
- Non-inferiority within 2 points holds on the official test but not on the primary fresh-scene test.
- The registered consequence of G3 failing: per-round gating costs something beyond discarded rounds. The paper states it as "ties within noise, non-inferiority shown on the official test only".

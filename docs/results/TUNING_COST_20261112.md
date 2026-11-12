# Counting the tuning: the meta level from a failing recipe against RL on the hand-tuned recipe (Goal), 2026-11-12

Status: **descriptive, not a registered claim.** Every evaluation used here was already read under its own registration:
- Goal main, 2026-11-06: official test.
- Self-repair, 2026-11-09: official test.
- `goal_nogate`, 2026-11-12: fresh scenes of the self-repair arms.
- Goal main fresh, 2026-11-12 (`results/fresh_goal_main_20261112.json`): fresh scenes of the tuned arms.

This note pairs them in a new way, so no bar applies.

Reader: `scripts/report/tuning_cost_read.py` → `results/tuning_cost_20261112.json`.

## The question

At equal *training* compute, the gated loop on the hand-tuned recipe ties one-shot RL on the same recipe:
- Goal R5 −0.58 (official) / F5 −0.80 (fresh).
- Spatial R5 −0.45 / F5 +0.38.

Both sides use a recipe that was chosen by pilot runs, and that cost appears in neither budget. The self-repair study started the framework from a recipe that fails (BC on its own temperature-1.6 samples) and let its LLM meta level edit it. This note puts the two together.

## What the hand tuning cost

The seed recipe (GRPO, lr 3e-5, matched ratio, episode-balanced loss, 64 scenes, T = 1.6, 100 × 64 updates, 6 × 3 inner steps) was fixed from sealed pilot runs before any main run:
- **LIBERO-10, addenda 1, 3, 5, 6, 8**: operator, learning rate, update length, inner steps, ratio and loss.
- **LIBERO-Goal, addendum 11**: GRPO against BC.

The record has **21 pilot runs**, 18 of them timed, for **≥ 213 GPU-hours** (`report.json` elapsed × cards).
- This is a lower bound: three Beijing pilots are not in the synced records.
- One one-shot RL run on Goal takes 15.7-16.9 GPU-hours on Yangquan, so the pilots are worth about **13 one-shot RL runs**.

## Results

| comparison | official test (seeds 0-3, within platform) | fresh scenes (seeds 1-3) |
|---|---|---|
| meta level from the failing recipe − one-shot RL on the tuned recipe | +0.05 [−1.62, +1.70] | **+2.20 [+0.47, +3.87]** |
| meta level from the failing recipe − hand-tuned gated loop (S3) | +0.28 [−1.43, +1.97] | +1.57 [−0.03, +3.17] |

Official finals, %:

| seed | meta level from the failing recipe | one-shot RL, tuned recipe | gated loop, tuned recipe |
|---|---|---|---|
| 0 (A800) | 60.9 | 62.7 | 57.2 |
| 1 | 60.1 | 58.8 | 59.8 |
| 2 | 61.3 | 59.0 | 59.9 |
| 3 | 57.9 | 59.5 | 62.2 |

The official S3 value recomputed here (+0.28) equals the registered self-repair read.

## Compute

- **One-shot RL**: one run, 1 candidate × 18 inner steps. It also needed the pilot sweep that chose its recipe.
- **The meta level**: one run, 2 candidates × 6 rounds × 3 inner steps, which is twice one run's training. It adds LLM calls and no pilots.

## Reading

Counting the tuning:
- Started from a recipe that fails, the meta level ends level with one-shot RL on the hand-tuned recipe on the official test (+0.05).
- On unseen scenes it ends 2.2 points ahead.
- It gets there with about 2 run-equivalents of training, against about 1 + 13 for the tuned RL result.
- Plain RL on the failing recipe does not get there: plain training of it ends 15 points below its start (NG3).

## Caveats

- Descriptive: new pairs of already-read evaluations. The fresh comparison has three seeds.
- The edit space was designed by us: which knobs exist, their ranges, and GRPO among the operators. The LLM also brings prior knowledge.
  - "No pilot runs" therefore does not mean "no human design".
  - What the meta level replaced is the pilot sweep, not the choice of space.
  - Blind numeric search over the same space comes within +1.15 [−0.63, +2.92] of the LLM (S2). The space carries much of the repair.
- The pilot sweep served the study as well, for example choosing the suite. A practitioner tuning RL from scratch would need a sweep of the same kind, but its size is ours, not a general constant.

## Addition, fixed before it exists (2026-11-12 ~18:55Z)

The A800 meta run `a8_oftgb_llm_harness_s0` has no fresh-scene evaluation, so the fresh row above uses seeds 1-3. One is queued now: `a8_oftgb_llm_harness_s0_fresh` (src12, as for every A800 fresh evaluation), to use a free card. When it exists, the four-seed fresh comparison (seeds 0-3, within platform, against `a8_goalmain_onebig_s0` / `a8_goalmain_fixed_s0` fresh) is reported **beside** the three-seed one, whatever it shows. The three-seed numbers above stay as they are.

**Result of the addition (2026-11-12 ~19:55Z).** `a8_oftgb_llm_harness_s0_fresh` finished at 19:35Z. Fresh scenes, seeds 0-3, within platform:

| comparison | 3 seeds (1-3, above) | 4 seeds (0-3) |
|---|---|---|
| meta level − one-shot RL on the tuned recipe | +2.20 [+0.47, +3.87] | **+2.17 [+0.75, +3.60]** |
| meta level − hand-tuned gated loop | +1.57 [−0.03, +3.17] | +2.98 [+1.60, +4.40] |

Seed 0 alone: +2.1 against RL, +7.2 against the tuned loop. The paper keeps citing the three-seed value, as this note said it would. The four-seed value agrees with it.

## Spatial counterpart, fixed before its data exist (2026-11-12 ~23:15Z)

The same descriptive comparison on LIBERO-Spatial is computed once, when `yq_oftsb_meta3_s2` and `yq_oftsb_meta3_s3` (addendum 29, still running) have their finals and fresh evaluations. It is reported whatever it shows, beside the Goal result.
- **Pairs**: the meta level from the failing BC recipe (`yq_oftsb_meta3_s{1,2,3}`, and `a8_spatrep_meta3_s0` on the A800 node) against one-shot RL on the hand-tuned recipe (`yq_ofts_onebig_s{1,2,3}`, `a8_spatmain_onebig_s0`). Both tests, within platform, seeds 0-3 and seeds 1-3 both shown.
- **Compute**: meta3 trains two candidates per round, like the Goal meta arm.
- **Caveat known in advance**: meta3's frozen memory (addendum 29) holds records of 32 earlier runs, some of them on the hand-tuned GRPO recipe. So on Spatial "no pilot runs" does not mean "no access to earlier tuning", and the note will say so with the result.
- **Not done**: nothing is computed from meta3 s1 or seed 0 alone before then.

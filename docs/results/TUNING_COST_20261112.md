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
- **The meta level**: one run, 2 candidates × 6 rounds × 3 inner steps. That is twice one run's *step count*, but not twice its cost: see the correction below. It adds LLM calls and no pilots.

## Reading

Counting the tuning:
- Started from a recipe that fails, the meta level ends level with one-shot RL on the hand-tuned recipe on the official test (+0.05).
- On unseen scenes it ends 2.2 points ahead.
- It gets there in 59-206 GPU-hours a run (mean 118 on Yangquan), against about 230 for the tuned RL result (≥ 213 of pilots plus a 14-17 hour run). This line was corrected twice (see the two corrections below); it first said "about 2 run-equivalents", then "52-85".
- Plain RL on the failing recipe does not get there: plain training of it ends 15 points below its start (NG3).

## Correction (2026-11-12 ~23:50Z): the meta level's cost is measured, and it is about four runs, not two

The first version of this note, and the paper built on it, said the meta level used "twice one run's training". That counted update steps (2 candidates × 18 steps). It is not the cost: the language model's edits raise the scenes, samples and update steps per inner step (for example 64 → 128-200 scenes, 8 → 12-16 samples, 100 → 200-400 updates), so each step is dearer.

Wall-clock hours per run (`report.json` seconds summed over resumed sessions; `wall_clock_hours` in the JSON). This is GPU-hours only for runs that held one card; the meta-level row is not (second correction below):

| run | seed 0 (A800) | seed 1 | seed 2 | seed 3 | Yangquan mean |
|---|---|---|---|---|---|
| meta level from the failing recipe | 77.2 | 61.6 | 85.3 | 51.6 | 66.2 |
| one-shot RL, tuned recipe (18 steps) | 14.3 | 15.7 | 16.9 | 16.8 | 16.5 |
| gated loop, tuned recipe | 18.2 | 16.6 | 16.8 | 17.8 | 17.1 |
| one-shot RL, tuned recipe, 36 steps (addendum 32) | - | 27.8 | 25.2 | 25.6 | 26.2 |

What follows:
- The meta level costs about four one-shot RL runs, not two.
- Counting the pilots, tuned RL costs about 230 GPU-hours (≥ 213 + 16.5). The meta level costs 52-85, about 30% of that. **Superseded by the second correction below: 52-85 is wall-clock; the cost is 59-206 card-hours, about half.** "A fraction of its compute" stands; "twice one run's training" does not.
- **Not counting the pilots, the meta level is the less efficient of the two.** Tuned one-shot RL run for 36 steps costs 26 GPU-hours and ends at 66.3% on the fresh scenes (seeds 1-3, read under addendum 32). The meta level costs 118 (card-hours, second correction) and ends at 63.5% on the same seeds (the 18-step RL run: 61.3%; means of three seeds, not a paired read). The comparisons in this note are against the 18-step run, the one-shot baseline of the main studies.
- No test statistic in this note changes; the reader's comparisons are identical before and after.

## Second correction (2026-11-13 ~00:30Z): the table above is wall-clock; the meta runs held three cards when resumed

The "GPU-hours" of the first correction are `report.json` seconds, which are wall-clock. That equals GPU-hours for the one-shot RL, gated-loop and numeric-search runs, which held one card throughout. It does not for the meta-level runs: each was resumed on three cards (one session of seed 2 briefly on six), with rollouts on all of them.

Card-hours of the meta-level runs (requested cards × job time, summed over sessions; `results/yq_selfrepair_job_sessions_20261113.json`, `meta_level_card_hours` in the JSON):

| seed | sessions (cards × hours) | card-hours |
|---|---|---|
| 1 | 1 × 51.2, 3 × 0.6, 3 × 12.2 | 89.6 |
| 2 | 1 × 54.5, 3 × 14.4, 6 × 0.4, 3 × 35.3 | 206.0 |
| 3 | 1 × 51.3, 3 × 0.5, 3 × 2.0 | 58.8 |
| 0 (A800) | rollouts on up to six cards; the backend's GPU-seconds of the last session alone are 103.6 h | ≥ 104 |

What follows:
- The meta level costs 59-206 GPU-hours a run on Yangquan, mean 118: about seven one-shot RL runs, and about half of tuned RL's 230 with its pilots counted. On seed 2 the two costs are close (206 against 230).
- "52-85 GPU-hours" and "about 30%" in the first correction, in the paper and in the README were too low. All are corrected.
- Job time includes queue wait and set-up, so these card-hours are an upper bound for Yangquan; the first sessions' job time (51-55 h) is within two hours of their recorded phase seconds.
- No test statistic changes.

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

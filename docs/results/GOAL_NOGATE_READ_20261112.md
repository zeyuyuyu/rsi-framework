# Goal: the framework against plain training of the same recipe (addendum 32 Part B), read 2026-11-12

Status: **registered read, done once (2026-11-12 ~04:30Z).** Both registered bars pass on both tests. Both written predictions miss.

## Design (as registered)

The recipe is the addendum-24 `bc_start` plan on LIBERO-Goal: BC on verified self-generated successes, which is iterated rejection-sampling fine-tuning. Every arm runs 6 rounds × 3 inner steps, on Yangquan seeds 1-3.
- **plain training** (`yq_oftgb_nogate`): every round's child is kept (`min_gate_gain` −1.0). One candidate per round.
- **gate only** (`yq_oftgb_fixed`): fresh paired gate. One candidate per round, so the same training compute as plain training; the gate's held-out evaluation is extra.
- **gate + LLM meta level** (`yq_oftgb_llm_harness`): two candidates per round, so twice the training compute.

Finals use three evaluations of the retained policy on the official test (500 states), plus one on the sealed fresh-scene test (1,000 scenes). Comparisons are seed-averaged per-episode paired bootstrap, 10k draws.

Readers:
- `scripts/report/goal_guard_read.py nogate` → `results/goal_nogate_read_20261112.json`
- `scripts/report/fresh_read.py goal_nogate` → `results/fresh_goal_nogate_20261112.json`

## Results

| claim | official test | fresh scenes | bar (each test) |
|---|---|---|---|
| NG1 gate only − plain training (equal training compute) | **+13.60 [+10.53, +16.76]**, passes | **+15.47 [+13.20, +17.77]**, passes | ≥ +10, CI > 0 |
| NG2 gate + LLM meta − plain training (2× training compute) | **+15.98 [+13.02, +18.91]**, passes | **+19.80 [+17.50, +22.13]**, passes | ≥ +10, CI > 0 |
| NG3 plain training − initial | −15.15 [−18.84, −11.45] | −16.29 [−18.79, −13.70] | reported |

Per seed, final success in %:

| seed | plain, official | plain, fresh | gate only, official | gate only, fresh | gate + meta, official | gate + meta, fresh |
|---|---|---|---|---|---|---|
| 1 | 43.9 | 40.3 | 56.1 | 57.5 | 60.1 | 64.2 |
| 2 | 45.1 | 47.8 | 58.7 | 61.0 | 61.3 | 64.5 |
| 3 | 42.5 | 43.1 | 57.5 | 59.1 | 57.9 | 61.9 |
| start | 59.0 (pooled in-run n0, 51 evaluations) | 60.0 (4 evaluations) | | | | |

Noise of the fresh reference (two halves of the initial-policy evaluations): −0.75 [−2.2, +0.7].

## Predictions against outcome

| written before launch | outcome |
|---|---|
| Plain training collapses on at least two of three seeds (final under 30%) | **Miss.** It degrades on every seed by 12-20 points, to 40-48%, but no seed falls under 30%. The earlier 5.5% was one always-accept curve at the gate over a longer horizon. |
| NG1 and NG2 above +25 | **Miss.** They come out +13.6 / +16.0 (official) and +15.5 / +19.8 (fresh). They clear the registered +10 bar but sit well under the predicted size. |

## Reading

- At equal training compute, the framework's gate alone ends 13.6 points (official test) and 15.5 points (fresh scenes) above plain iterated self-training of the same recipe. The difference is positive on every seed.
- Most of this is protection. Plain training falls 15-16 points below the start, while the gated loop holds its start (gate only −2.9 to +1.0 against the reference across seeds and tests).
- The meta level adds a small gain on top: fresh 61.9-64.5% against a start of 60.0%.
- This is the framework against self-training RL of the RFT / expert-iteration kind. It is not against GRPO, which this recipe does not use. Against tuned GRPO at equal compute the record is a tie (addenda 28/30 R5/F5); the guard-rail reads are pending.

# Prereg v3, addendum 19: a compute-capped harness arm on cavin, so proposal and incumbent cost the same

Committed 2026-10-31 (~13:30Z), before any run named here starts. No main-arm test has been read. Bars of addenda
14-18 are unchanged.

## Why

Addendum 18 found that the LLM's proposals buy compute. Every LLM proposal so far raised the rollouts per inner step:

| proposal | rollouts per inner step vs the seed's 512 |
|---|---|
| Goal s1, round 1 | 2.5x |
| Goal s1, round 2 | 3.75x |
| Goal s2 and s3, round 1 | 2x, with 1.5x the update steps |
| LIBERO-10 s1, round 1 | 3.75x, with 1.5x the update steps |

A head-to-head win of such a proposal over the incumbent (Goal s1 round 1: 0.61 against 0.56) cannot separate
a better procedure from more RL on the same procedure. The question this project has to answer is the first one.

## The `llm_harness_cap` arm (code: `LiberoDomain.set_budget_cap / fit_budget / validate_capped`)

It is the `llm_harness` arm of addendum 16 with one change, `meta.budget: "seed"`:

* **Cap.** Every procedure is capped at the seed program's work per inner step. curriculum.cases x solver.samples
  must not exceed 64 x 8 = 512 rollouts, and update.steps x update.batch must not exceed 100 x 64 = 6400 examples.
* **Over-cap proposals.** They are scaled down onto the cap, not rejected. Scenes are cut first, then tries; steps
  are cut first, then batch. Every other edit is kept. The LLM is told the cap and the scaling rule in its field
  notes (`BUDGET_DOC`), so it can choose where to spend.
* **Fallback.** Numeric fallback proposals are capped the same way.
* **Test.** `test_budget_cap_scales_proposals_onto_the_seed_budget`.

The incumbent and the proposal then cost the same per round, they train from the same parent, and their gates are
scored on the same fresh placements. Their head-to-head is therefore a compute-matched test of whether the meta
level's edits beat the fixed procedure.

## Placement

The three queued cavin `llm_harness` runs (queue 40-42, not started) become `llm_harness_cap` s1-3, from src7. The
uncapped `llm_harness` arm still runs on Yangquan (s1-3) as registered in addendum 17. Cavin then holds `fixed`,
`llm` and `llm_harness_cap` x 3, each from the same OFT checkpoint and seeds.

## Bars (cavin only, the same seeds, paired)

* **H-cap (primary for this arm).** Pool over rounds 1-6 and seeds 1-3 the proposal gate minus the incumbent
  gate, one value per round in which both were trained. The bar is a mean of at least +2 points, with a seed-
  clustered 95% bootstrap CI that excludes 0.
* **R4-cap.** llm_harness_cap minus fixed of at least +2 on the official test, CI excluding 0, as R4.
  Disclosure: the arm trains two candidates per round, so it spends about 2x fixed's GPU time. Under addendum 18 a
  win is labelled "not compute-matched"; H-cap is the compute-matched claim.
* If a run cannot finish six rounds by the analysis date, the rule of addendum 18 applies.

## Amendment 1 (2026-10-31 ~14:40Z, before the run named here starts)

A Beijing slot is free, and the cavin cap runs wait behind four running jobs. One more `llm_harness_cap` run,
`bj_oftg_llm_harness_cap_s4`, therefore runs on Beijing: LIBERO-Goal, seed 4, the same program, cap, relay and model,
from `rsi_src_v19.tar.gz`. Beijing's evaluation is deterministic.

* It has no `fixed` partner, so it adds nothing to R4-cap.
* Its head-to-heads join the H-cap pool as a fourth cluster. The cluster unit is the run, and the CI is clustered by
  run.
* H-cap is also reported on the three cavin runs alone, as registered above. If the two reads disagree on whether
  the bar is met, the cavin-only read is the registered one, and the disagreement is stated.

## Amendment 2 (2026-10-31 ~19:20Z, before the run named here starts): is it one good edit, or the loop?

The first capped proposals on Beijing (s4) and cavin (s1) were the same procedure in all but one field: temperature
1.6 → 1.2, `progress` allocation (floor 0.1), and `mixed_groups` with budget 400 and per_case 2. Only the advantage
differed (center vs zscore). A win for `llm_harness_cap` could therefore come from one better setting, found once,
and not from a meta level that keeps adapting.

* **Control `bj_oftg_fixed_t12_s4`.** Beijing, Goal, seed 4, meta `fixed`. Its program is bj s4's round-1 LLM edit,
  applied from round 0 and never changed: T 1.2, progress floor 0.1, mixed_groups budget 400 per_case 2, adv center,
  64 scenes x 8 tries, 100 steps x 64, lr 3e-5, matched, episode. Otherwise it is the cap run's plan, with 6 rounds
  and fresh paired gates.
* **Read (exploratory, reported with H-cap).** `bj_oftg_llm_harness_cap_s4` minus `bj_oftg_fixed_t12_s4`:
  * the round-by-round accepted-node gate,
  * the official test at the end, read once.
* **Interpretation.**
  * If the cap run is not ahead of this control, the meta-level gain is credited to a single edit, not to the loop.
  * If the cap run is ahead, the loop's later rounds add value beyond that edit.
  * It costs half of the cap run, because it trains one candidate per round.

## Amendment 3 (2026-10-31 ~19:45Z): run seed 4 cannot be used; the Beijing pair moves to seed 0

`bj_oftg_llm_harness_cap_s4` crashed in round 2 (job-6z02h1zf3dde, rc 1). The cause was
`placement_seed_out_of_range:4301020000`. Training placement seeds are `1e8 + inner_seed(seed, r, step) * 1e6 + ...`,
and `inner_seed` only keeps them below 2^32 for run seeds 0-3 (its docstring says so). The largest values are:
seed 0: 7.0e8; seeds 1-3: 1.7e9 to 3.7e9; seed 4: 4.7e9; seed 5: 5.7e9.

* **Engine unchanged.** No remapping while other runs are in flight.
* **Beijing pair moves to seed 0.** The Beijing capped run and its fixed control become `bj_oftg_llm_harness_cap_s0`
  and `bj_oftg_fixed_t12_s0`, rerun from round 0. On Beijing, seed 0 is used only by the GRPO curve
  `bj_oftg_curve_grpo`, which is a different arm. The seed-0 training placements lie below the held-out (9e8) and
  fresh-gate (9.5e8) bases.
  * The seed-4 control (job-ig9l068qvgo1) was stopped minutes after it started.
* **Seed-4 round 1 kept out of H-cap.** Its record was c1 0.595 against c0 0.555. It is reported as a void run and
  is not pooled into H-cap, so the cluster is the complete seed-0 run.
* **The control's program is unchanged.** It is the seed-4 round-1 LLM edit (T 1.2, progress floor 0.1,
  mixed_groups budget 400 per_case 2, adv center), so the control still asks whether that one edit alone explains a
  cap-arm gain.
* **Generators refuse run seeds above 3.**

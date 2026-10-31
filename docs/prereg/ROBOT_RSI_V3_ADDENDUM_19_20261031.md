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

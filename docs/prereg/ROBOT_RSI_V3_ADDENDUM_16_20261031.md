# Prereg v3, addendum 16: a meta level that edits the harness, not only the knobs

Committed 2026-10-31 (~05:40Z), before any run that uses it. No v3 run has read a test result.

## Why

The meta level of addenda 14-15 changes ten knobs: scenes, allocation, samples, temperature, curation rule, budget,
operator, lr, steps and batch. That is hyperparameter search, and in the code domain such a meta level never beat
`fixed`. Every change that has actually improved this study so far was a change to the harness, made by diagnosing
round records:

* the matched ratio (addendum 6);
* the episode-balanced loss (addendum 7);
* temperature-matched BC (addendum 12);
* fresh paired gates (addendum 9).

A meta level that can make such changes is RSI in the strict sense: the system revises the procedure that improves
it.

## Harness components (code: `rsi/domains/libero/domain.py: HARNESS_SPACE`, `HARNESS_DOC`)

The `harness` space is the ten knobs plus the following components.

| component | values |
|---|---|
| `update.ratio` | `legacy` or `matched` |
| `update.loss_agg` | `token` or `episode` |
| `update.bc_temp` | `unit` or `rollout` |
| `curation.adv` | `center` or `zscore` |
| `curation.band` | [0,1], [0.1,0.9], [0.2,0.8] or [0.3,0.7] |
| `curation.per_case` | 1-8 |
| `curriculum.floor` | 0-0.3 |
| `update.clip_low` | 0.1-0.4 |
| `update.clip_high` | 0.1-0.5 |

* **What the LLM is told.** It gets a neutral description of what each option computes, and never which option is
  better. The diagnoses behind addenda 6, 7 and 12 are not in the prompt, so rediscovering them is a test of the meta
  level.
* **What stays protected.** The meta level cannot touch the simulator verdicts; the gate, audit and test placements
  and their scoring; the acceptance rule; the budget bounds; or the logging.
* **Validation.** Every proposal passes the same validator and range checks. The fields `update.ratio`,
  `update.loss_agg`, `update.bc_temp` and `curation.adv` are optional; when absent, the historical behaviour applies.
* **Precedence.** Values in the program override the run's VLAConfig defaults in the train spec.
* **Test.** `test_harness_components_validate_and_reach_curation_and_train_spec` (37 pass).

## Arm `llm_harness` (cavin, src6; `mkoft_goal_main.py <order> <seed> llm_harness`)

The arm is identical to `llm`, except for two things. First, its search space is `harness` and its prompt includes
`HARNESS_DOC`. Second, its program states the run's own settings explicitly (matched, episode, bc_temp unit, adv
center), so that they can be edited. Seeds 1-3. It is paired with cavin's `fixed` s1-s3 and compared with cavin's
`llm` s1-s3.

**Bars, fixed now** (official test read once per run, paired per episode, seed-averaged):

* R4-harness: `llm_harness - fixed` >= +2, CI excludes 0.
* Secondary, reported either way: `llm_harness - llm`, which isolates harness editing from knob editing.
* Reported too: which harness components the kept edits changed, and whether any kept edit reproduces a fix that was
  made by hand (matched ratio, episode loss, rollout-temperature BC).

## Placement

cavin's GPUs take `llm_harness` s1-s3 after `llm` s3 and `fixed` s3, as they free up. If Yangquan can relay the
LLM calls without the key leaving the workstation, the arm also runs there under its own addendum.

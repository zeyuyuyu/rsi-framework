# Prereg v3, addendum 14: an LLM meta level, and main arms ordered to answer "RSI or just RL?"

Committed 2026-10-31 (~04:00Z), before any run that uses it and before the addendum-11 rule is read. No v3 run has
read a test result.

## Why

Every robot run so far uses `proposer: fixed`, which means the meta level is off. The LIBERO-Goal gain (Beijing seed
0, D = +7.00, CI [+2.88, +11.25]) therefore shows that the object-level loop works. That loop practises with the
latest policy, gets simulator verdicts and updates. It does not by itself separate RSI from iterated on-policy RL.
The code-domain main arms already ran the numeric meta level (`full`), and `full - fixed` never passed its bar on six
model x task cells (-0.8 to +1.1 points, bar +1; `results/claims_*.json`). A blind knob search may simply be too weak
a meta level.

Today a diagnosis improved the procedure twice. The BC collapse came from unit-temperature NLL on T = 1.6 samples
(addendum 12). Before that, the matched ratio and episode-balanced loss (addenda 6-7) came from reading round
signals. A meta level that reads those same signals and edits the procedure is the natural strong form of the
meta level. This addendum adds it and orders the main arms so that the RSI-versus-RL question is answered first.

## The `llm` meta level (code: `rsi/meta/proposers.py: LLMMetaProposer`)

* **Model.** `anthropic/claude-sonnet-5-5` through the CommonStack gateway (OpenAI-compatible), temperature 1.0,
  one call per round. Like `full` (`candidates_per_round` 2), each round trains the incumbent procedure plus
  `candidates_per_round - 1` = 1 new one, which the LLM proposes. The compute is therefore the same as `full`.
* **What it reads.** The current procedure; the edit space; and, for each past candidate, its procedure diff,
  gate score and gate change, whether it was kept, and per inner step the sampled success, the share of scenes with
  both outcomes and the item count. It also reads the training loss at the first and last update step.
* **What it never reads.** Audit scores, test results, the policy, the scenes and the episodes.
  `test_llm_meta_proposer_never_sees_audit_and_falls_back` checks that audit values never reach the prompt.
* **What it can change.** Only the knobs numeric search mutates (`domain.edit_space`), checked by the same validator.
  A proposal that changes any other field, even a valid one such as `curriculum.floor`, is rejected. The gate decides exactly as for every other arm. Invalid proposals and failed calls fall back to
  numeric search. Each fallback is counted and reported.
* **Logged per run** (`meta-llm.jsonl`). The prompt digest and size, the reply and diagnosis verbatim, token usage,
  and the number of LLM versus fallback programs.
* **Spend.** At most 24 calls per run, about 6 tokens x 10^3 each. The gateway has no balance meter, so the call cap
  is the hard limit (memory: CommonStack). Expected spend is under $1 for all `llm` runs.

**Attribution guard.** The external model contributes only the choice of procedure values inside a fixed space.
The data still comes from the policy's own practice, and the verdicts from the simulator. This is the RSI meta level
of the framework design: the training procedure itself is revised under gate control and passed on. It is not an
external source of data. It is reported as such, with the share of kept programs it authored.

## Main arms on LIBERO-Goal (when the addendum-11 rule fires for GRPO)

Arms: `fixed`, `full` (numeric), `llm`, `onebig` (same total budget in one round), `nonrec`, `shuffled`. Seeds
1-3, fresh paired gates (addendum 9), the GRPO program of addendum 11. The official 500-episode test is read once per
run at the end, as prereg v3 specifies.

**Launch order:** seed 1 of `full`, `llm`, `onebig`, `fixed` first, then seed 2 of the same four, then seed 3, then
`nonrec` and `shuffled`.

**Platform:** comparisons are paired within a seed, so all arms of one seed run on one platform. The `llm` arm needs
the gateway: cavin reaches it, and Baidu is checked before use. If Baidu cannot reach it, the seeds run on Baidu
are without `llm`, and that is reported.

## Bars, fixed now (seed-averaged, per-episode paired CIs, test read once)

* R4 (unchanged): `full - fixed` >= +2, CI excludes 0.
* **R4-llm: `llm - fixed` >= +2, CI excludes 0** (does a diagnosing meta level add to the object-level loop?).
* R4-llm-vs-numeric (secondary, reported either way): `llm - full`.
* R5 (unchanged in form): the best of `fixed`/`full`/`llm`, chosen by gate and not by test, minus `onebig`, >= +2,
  CI excludes 0 (does iterating under gate control beat plain one-shot RL at the same compute?).
* If neither R4 nor R4-llm passes, the paper claims a self-improvement loop, not a meta-level contribution.

## Pre-launch check (not a result)

On 2026-10-31, before any run, one call was made with the round history of `a8_oftg_curve_bc_s1` up to round 4
(the collapsing BC run), with audit removed. `scripts` scratch file `llm_smoke.py`; 2.8k tokens. Its diagnosis,
verbatim: "Behavior cloning on high-temperature (1.6) samples from only 64 scenes ... trains on noisy and repetitive
successes, so the policy drifts and degrades. Mixed-outcome scenes are available (50-70%), but bc does not use the
failure signal." It proposed two procedures:

* BC at temperature 1.1 with 200 scenes, lr 5e-6 and 60 steps;
* GRPO on mixed groups.

So it reached the addendum-12 diagnosis on its own. One of its proposals changed `curriculum.floor`, a field outside
the knob set, which is why the edit-space restriction above was added before launch.

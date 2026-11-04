# Prereg v3, addendum 24: self-repair — does the meta level turn a failing procedure into a working one?

Committed 2026-11-04 ~16:20Z, before any run of this study starts. No run named here has a `report.json`.

## Why this test, and why now

Every meta-level comparison so far started from a procedure that already works (addendum 21, M2-A/M2-B: null;
addendum 23 gives the mechanism: the object loop reaches the same plateau under every recipe in the space, so there
is nothing for the meta level to fix). A meta level is distinguishable from RL only where RL's procedure fails and
a different procedure would not. The study has one such case, found and documented before any of this: **BC on
the policy's own high-temperature samples collapses** (addendum 12; `a8_oftg_curve_bc_s1` 58.5 → 5.5, D −48.1;
`bj_oftg_curve_bc` D −6.4, `docs/results/M1_GOAL_CURVES_20261031.md`). The repair is a one-knob change
(`update.bc_temp` "rollout"), or a lower temperature, or switching `update.operator` to grpo. All three are in the
harness edit space (`HARNESS_SPACE`, domain.py). In the addendum-14 pre-launch call the LLM, shown that collapsing
history, diagnosed it correctly and proposed the latter two unprompted. This addendum turns that into a test.

## Design (LIBERO-Goal, Yangquan, seeds 1-3)

Start program `bc_start` = the collapsing BC recipe of addendum 11/12: OFT program with `update.operator` bc,
`curation.rule` verified, `curriculum.cases` 64, lr 1e-5, temperature 1.6, 100 steps, `bc_temp` "unit",
`loss_agg` episode, `ratio` matched. Gated loop as in the Goal main arms: 6 rounds, 3 inner steps, fresh paired
gates (20 per task).

| arm | proposer | candidates/round | isolates |
|---|---|---|---|
| `yq_oftgb_fixed_s{1,2,3}` | fixed | 1 | the gate alone (can it only refuse the collapse?) |
| `yq_oftgb_full_s{1,2,3}` | numeric search over `HARNESS_SPACE` | 2 | blind search over the same knobs |
| `yq_oftgb_llm_harness_s{1,2,3}` | LLM, `HARNESS_SPACE`, relayed | 2 | a diagnosing meta level |

`full` and `llm_harness` have the same compute (addendum 14). Source rsi_src_v24 for all nine runs (the relay
client fixes of addendum 21 am. 2; the fixed/full arms do not touch that code). Same model, queue and 53-hour
resume rule as the other Goal arms. LLM calls through the cavin relay (addendum 17); fallback rounds counted.

## Bars (official 500-episode test, read once when all nine runs have `report.json`)

* **S1 (primary): `llm_harness − fixed` ≥ +3.0**, seed-averaged, per-episode paired bootstrap, CI excludes 0.
  Passing means: from a procedure that fails, the loop with the meta level ends with a better policy than the
  same loop without it. That is the meta level changing the procedure to effect.
* **S2 (secondary, reported with CI): `llm_harness − full`.** Positive means diagnosis beats blind search over the
  same knobs; near zero means the knob space, not the LLM, carries the repair. Both are meta-level results.
* **S3 (descriptive, no bar): `llm_harness` vs `yq_oftg_fixed` (the hand-tuned GRPO loop, seeds 0-3).** Does a
  self-repaired loop reach the hand-tuned one?
* Reported with every claim: the LLM's diagnoses verbatim, which knob changed in each accepted round, the round
  in which the collapse was first refused by the gate, fallback rounds, gate noise (the n0 re-evaluations).

## Predictions, written before launch

* `fixed`: the gate refuses the collapsing children, so the retained policy stays near n0 (about 58-60), or the
  first round's small BC gain (+1 to +3) is kept and the rest refused.
* `llm_harness`: a bc_temp or operator change within the first two rounds, then gains like the GRPO loop (+3 to +6).
* `full`: it may find the repair by chance; the knob has two values. If it does, S2 is small and the honest claim
  is "the loop repairs itself when the space contains the repair", with the LLM's advantage being speed.
* If S1 fails, the meta level has no demonstrated effect in this study, and the paper says so.

## What is not changed

Addenda 22 and 23 run as registered. The Goal read-once (R1-R5) is separate and reads the GRPO arms only; the
nine runs here are read once, on their own, under S1-S3.

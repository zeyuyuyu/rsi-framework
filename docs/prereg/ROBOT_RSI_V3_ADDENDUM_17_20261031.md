# Prereg v3, addendum 17: harness meta level on Yangquan (relayed LLM), a LIBERO-10 test, and a pre-set rule to drop the harness space

Committed 2026-10-31 (~05:15Z), before any run named here starts. No v3 run has read a test result.

## Relay (code: `rsi/meta/relay.py`, `scripts/a800/llm_relay.py`, `scripts/baidu/mk_relay_urls.py`)

Yangquan is a shared pool. The gateway key must not be on its CFS, in BOS, or in a job spec. A Yangquan `llm` run
therefore uses `meta.relay: true`, and the call path is:

1. The run PUTs request k to a presigned URL.
2. A relay on cavin, which holds the key, reads the request through a presigned URL, calls the model and PUTs the
   response.
3. The run polls a presigned GET URL for response k.

The URLs are signed on the workstation, scoped to single objects, and expire after 5 days. The slot counter lives
in the run dir, so a resume never reuses a slot. The prompt, model and call cap are those of addenda 14 and 16.
If the relay fails, the call falls back to numeric search, and the failure is logged and counted. Test:
`test_relay_client_puts_request_polls_response_and_never_reuses_a_slot`.

## Yangquan allocation (16 cards, one wave)

| arms | seeds | cards | why |
|---|---|---|---|
| Goal `fixed`, `full`, `onebig` (addendum 15) | 1-3 | 9 | RL vs numeric meta level vs one-shot RL |
| Goal `llm_harness` (addendum 16, relayed) | 1-3 | 3 | the harness meta level, paired with Yangquan `fixed` |
| **LIBERO-10** `fixed` and `llm_harness` | 1-2 | 4 | see below |

Goal `nonrec` and `shuffled` (addendum 15) move to the second wave, when Yangquan cards free up. The plan names are
those of `mkplans_vla.py yq_rsi` and `goal_main grpo yq`. Every Yangquan run uses the same source, `rsi_src_v17`
(the repo at this commit). Its behaviour for the non-LLM arms is identical to v14.

**Why LIBERO-10.** All three fixed recipes are flat there (addendum 8). If a harness-editing meta level turns a
recipe that fails into one that works, that is the clearest RSI evidence this study can give. Bar, fixed now: on
the official test, read once per run, `llm_harness - fixed` >= +3 (seed-averaged, paired per episode, CI excludes
0). With 2 seeds this is labelled exploratory.

## Rule to drop the harness space, fixed now (a scheduling decision, not a claim)

For every `llm` and `llm_harness` run, each round trains two children from the same parent: one with the proposed
procedure (author `llm`) and one with the incumbent procedure. Both are scored on the same fresh gate, so
`proposal_gate - incumbent_gate` is a paired head-to-head. After round 3, pool these head-to-heads over all `llm_harness` runs and all `llm` runs. If the mean
for `llm_harness` is <= 0 and below `llm`'s, new runs started afterwards use the knob space instead of `harness`,
and the change is reported. The running `llm_harness` runs finish as declared. Claims rest only on the test bars of
addenda 14-16 and this one.

Amendment (2026-10-31 ~06:35Z, before the runs named here start).

* **Yangquan concurrency.** Yangquan runs at most 12 of our jobs at once. Other users hold only 16 of the 64 cards,
  and the API exposes no quota. The four LIBERO-10 arms there are queued and start as the first Goal arms finish.
* **Extra LIBERO-10 pair on Beijing.** To get a LIBERO-10 signal sooner, an extra pair runs on Beijing, where
  evaluation is deterministic: `bj_oftl_fixed_s3` and `bj_oftl_llm_harness_s3`, seed 3, relayed LLM
  (`run_vla5.sh`, source `rsi_src_v17`, `mkplans_vla.py bj_l10_pair`). The pair is compared within Beijing and is
  exploratory, under the same +3 bar.
* **Known exposure.** AIHC job specs, including env values, are visible to other users of the same Baidu account.
  The presigned source and relay URLs are therefore readable by them. A relay URL lets its holder read the run's
  request and response slots, or write a request. A forged proposal still passes the validator, the knob or harness
  space and the gate, so the worst case is one bad but valid candidate. The URLs expire after 5 days, and no key or
  credential is exposed.

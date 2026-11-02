# Prereg v3, addendum 21: meta level v2, a separately registered study on Yangquan

Committed 2026-11-02 (~05:00Z), before any run named here starts. Nothing in addenda 1-20 changes: their arms keep
running unchanged, their bars and reads stand, and the Goal read-once test pass (addendum 18 am. 2, addendum 20
am. 1) still waits only for the v3 Goal main arms. This study has its own sealed test, read once when its own runs
have ended.

## Disclosure

The design freeze of addendum 18 am. 2 covers addenda 14-20. This addendum registers a *new* study. It was designed
on 2026-11-02, after these had been seen:

* the v3 head-to-heads (gate only);
* the early read of the cavin fixed s1/s2 test files (addendum 18 am. 2).

The user directed the redesign on 11-02 ("我们要证明提升来自元层 … 实验不好，你可以分析原因，调整元层"). The
diagnosis below uses only gate, audit, receipt and program data. No test number entered it.

## Why: what limits the v3 meta level (diagnosis, 11-02)

1. **The comparison measures only the newest edit.** The H-cap bar compares each round's proposal (c1) with the
   incumbent (c0). Once an edit is accepted it becomes c0, so a good early edit is counted once and later rounds sit
   near 0.
2. **The children barely differ.** c0 and c1 share the parent, the scenes, the sampling seeds and often the cached
   step-0 episodes. Only the training seed and the edited knobs differ, while the gate noise is about +/-3 points
   (addendum 9). In cap s1, n0 scored 0.64 and 0.615 on the round-1 and round-2 gate sets, and r04c0 scored 0.64
   and 0.61 on rounds 5 and 6.
3. **The cap favours the incumbent and distorts edits.** The seed sits exactly on both caps. An over-cap proposal
   was scaled by cutting scenes first, so "more tries per scene" became "fewer scenes".
4. **The LLM sees no per-task signal and is not told the noise.** Per-task rates were computed but never shown,
   and the gate was kept as a mean only. The meta level chased +/-3-point gate changes and kept early lucky edits
   (cap s3 and llm s1 hold one program from round 1-2 on).
5. **A sibling leak.** A candidate's "progress" allocation read the per-task rates that its sibling's last inner
   step had left (shared `task_rates`).
6. **Little left to fix.** The seed program was itself hand-tuned through pilots (addenda 2, 6, 7, 11:
   lr 1e-4 → 3e-5, token → episode loss). On a tuned start the reachable gain is below the noise floor.
7. **Uncapped proposals buy compute, not success.** They used 3-7x the training items (700-2000 vs ~250) at the
   same gate.

## What changes (code: `meta_v2`, branch meta-v2 → main)

Every change sits behind a flag, so v3 plans run bit-for-bit as before.

* **Engine `meta_v2`.**
  * Each candidate starts from the per-task rates its parent left (fixes the sibling leak).
  * Each node records per-task gate success, for itself and for the parent, on the round's fresh gate.
* **Domain `v2`.**
  * The new allocation `weights` splits scenes over tasks in proportion to `curriculum.task_weights`: one weight in
    [0, 4] per task, where 0 gives a task no scenes that round.
  * An over-cap procedure shrinks both factors by the same ratio (scenes and tries; steps and batch), so the split
    the proposal chose survives.
  * Lower bounds widen to 16 scenes and 25 steps (v3: 40 and 50), so in-budget reallocations stay legal, e.g.
    16 tries × 32 scenes or batch 128 × 25 steps. This revision was made on 11-02, before any run here started.
    The cavin smoke run's first LLM proposal had used exactly such a split (20 scenes × 8 tries, 25 steps) to stay
    under its cap, and was rejected as out of range.
* **LLM prompt v2.**
  * States the objective: the FINAL policy after the last round.
  * States the round number out of the total.
  * Explains that c0 re-runs the current procedure on the same scenes.
  * States the gate noise: about +/-3 points, so a single-round change under ~5 points is not evidence.
  * Shows per-task gate success, for the candidate and the parent, and per-task sampled success per inner step.
  * The edit space is the harness space plus `weights` / `task_weights`.
  * The numeric fallback stays on the harness space. Audit and test never reach the LLM; the unit tests check this.
* **Compute-matched fixed control `replica`.** The fixed program trains two children per round, which differ only
  in the training seed, so the control gets the same training compute and the same best-of-two selection as the
  meta arm.

## Runs (Yangquan only, so every comparison stays on one platform)

Shared by every run:

* **Model and suite:** OFT 1-trajectory Goal SFT checkpoint, `libero_goal`, tasks 0-9.
* **Engine:** 6 rounds, 3 inner steps, fresh paired gates (20 per task), two candidates per round, `meta_v2`.
* **Held-out sets and test:** heldout_per_task 40; official test 50 inits per task.
* **Cap:** the seed's 512 rollouts and 6400 examples per inner step.

Two seed programs. Both use 64 scenes, 8 tries at T 1.6, 100 steps of batch 64, clip 0.2/0.28, matched ratio and a
centred advantage. They differ in two fields:

| start | lr | loss_agg | source |
|---|---|---|---|
| `pre` (before tuning) | 1e-4 | token | addendum 2's frozen M1 seed program |
| `tun` (tuned) | 3e-5 | episode | the v3 Goal main program (addenda 7, 11) |

Departures from addendum 2 in `pre`:

* 64 scenes instead of 160, to match the compute of every other Goal arm.
* The matched ratio, because addendum 6 showed the legacy ratio was a numerics error rather than a design choice.

Arms, seeds 1-3 each, 12 runs:

| run | start | meta level |
|---|---|---|
| `yq_m2_pre_rep_s{1,2,3}` | pre | replica (fixed, compute-matched) |
| `yq_m2_pre_llm_s{1,2,3}` | pre | LLM v2 (claude-sonnet-5-5 via the cavin relay of addendum 17; ≤24 calls) |
| `yq_m2_tun_rep_s{1,2,3}` | tun | replica |
| `yq_m2_tun_llm_s{1,2,3}` | tun | LLM v2 |

Seeds 1-3 keep the training placement seeds below 2^32 (addendum 19 am. 3).

## Claims and bars

Each comparison is llm minus rep, same start and same seeds. Every arm measures its final retained policy.

* **M2-A (primary, test).**
  * Start `pre`; official LIBERO-Goal test (500 episodes per run).
  * Pool the three seeds, then take a per-episode paired bootstrap. Each draw resamples episode ids once and applies
    to both arms and all seeds.
  * **Bar: mean ≥ +3.0 points and the 95% CI excludes 0.**
  * If it passes, the paper may claim that the meta level improves the self-improvement procedure itself: from the
    pre-tuning recipe, at equal compute, the loop does better with the meta level than without.
* **M2-B (test).** The same comparison on start `tun`. Bar ≥ +2.0 with the CI excluding 0. It answers whether the
  meta level adds beyond hand tuning.
* **M2-gate (non-test, readable as runs end; not a claim on its own).** Final retained node's audit score (the same
  200 placements in every run) for llm minus rep, seed-clustered bootstrap. It is reported with M2-A and M2-B.
* **Reported with every claim:**
  * fallback rounds per run (author `search`);
  * LLM calls and tokens;
  * GPU hours per run;
  * what the LLM changed, round by round.
* **If M2-A fails,** the paper claims a self-improvement loop, not a meta-level contribution (as addendum 14
  already says for v3).

## Operations

* **Crashes:** a crashed run is resumed unchanged (`--resume`). A fallback round stays in the arm. Nothing is
  re-drawn on purpose.
* **Test reads:** no file of this study is opened before all 12 runs have `report.json`. After that, M2-A and M2-B
  are read once.
* **Changes after start:** any change after a run starts is an amendment here, before it takes effect.

## Amendment 1 (2026-11-02 ~06:45Z): a cavin replicate of the primary comparison

This amendment was registered before any Yangquan run of this study had finished a round, so no v2 result was
known. The cavin smoke runs ended normally (`a8_m2smoke_llm_s1` code 0, tests sealed), and the cavin GPUs they used
are now free.

* **Runs.** `a8_m2_pre_llm_s1` and `a8_m2_pre_rep_s1`:
  * the plan of `yq_m2_pre_{llm,rep}_s1`, with cavin paths;
  * source src9, which is the v22 tree, commit c7f11d1 or later with the same `rsi/`;
  * the LLM called directly from cavin with the key in `~/.cskey`, not through the relay.
  * Seed 2 is added the same way if two more cavin GPUs free up before 2026-11-03 06:00Z; it is announced here
    first.
* **Read.** This replicate is exploratory. Its llm−rep difference on the final test is computed within cavin only,
  never pooled with Yangquan, and reported next to M2-A. Its test files are opened together with the study's.

## Amendment 2 (2026-11-02 ~17:05Z): gateway outage, provider switch, re-drawn rounds, seed-2 cavin replicate

* **Outage.** From ~10:06Z the CommonStack key returned 401 ("Access key is not active"). Every LLM call failed
  after its retries, and its round ran on the numeric fallback (author `search`).
* **Switch, made with the user's approval.** Same model id, `anthropic/claude-sonnet-5-5`, through OpenRouter:
  * The relay switched at 16:32Z. OpenRouter geo-blocks Anthropic models from cavin (403 "not available in your
    region"), so from 16:41:57Z the relay and the cavin runs reach it through cavin's outbound proxy. BOS traffic
    stays direct.
  * The cavin runs start through `~/rsi/bin/py_llmproxy.sh`. It is the same interpreter plus the proxy variables,
    with no code change.
  * The serving provider differs from CommonStack's, which exposes none. The model id and prompt are unchanged.
* **Rounds that fell back and stay** (completed before the fix; tagged FALLBACK, kept in the arm as the protocol
  says): round 2 of `yq_m2_tun_llm_s1`, `yq_m2_tun_llm_s2`, `yq_m2_tun_llm_s3` and `yq_m2_pre_llm_s3`.
* **Rounds re-drawn.** These rounds were still running, and their candidates had not been scored. They were stopped
  and resumed (`--resume`), so the round re-draws its LLM call. The selection is on call failure only, never on
  outcome (as on 11-01):
  * `yq_m2_pre_llm_s1` and `yq_m2_pre_llm_s2`: round 2;
  * `yq_m2_pre_llm_s3`, `yq_m2_tun_llm_s1`, `yq_m2_tun_llm_s2` and `yq_m2_tun_llm_s3`: round 3;
  * `a8_m2_pre_llm_s1`: round 2 (re-drawn twice, because the first re-draw hit the geo block).
  * The v3 runs re-drawn the same way are listed in addendum 18.
* **Relay-client fix (rsi_src_v23, commit 46f9a1d).** The resumed `yq_m2_tun_llm_s1` crashed (rc=1). A BOS
  `RemoteDisconnected` while it polled for the reply was not caught. `RelayClient` now retries transient network
  errors. No decision logic changed. The run was resumed again from v23, and later resumes use v23.
* **Seed-2 cavin replicate (amendment 1).** GPUs 5 and 7 are free before the 11-03 06:00Z deadline, so
  `a8_m2_pre_llm_s2` and `a8_m2_pre_rep_s2` start now, from src10 (v23 tree) and the OpenRouter-via-proxy meta.

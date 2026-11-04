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
* **Second relay-client fix (rsi_src_v24, commit 5812b66).** The resumed `yq_m2_pre_llm_s3` crashed at start
  (rc=1). The relay URL file it fetched from BOS came back truncated (`IncompleteRead`). `RelayClient` now retries
  that fetch and treats `http.client.HTTPException` as transient. The run was resumed from v24 (job-5wxf2l0cqda3);
  later resumes use v24.

## Amendment 3 (2026-11-02 ~23:50Z): a seed-3 cavin replicate

Registered before any run of this study had a `report.json`, so no v2 final result was known. GPU1 has been free
since the Spatial run ended at 23:16Z, and the cavin queue is empty.

* **Runs.** `a8_m2_pre_llm_s3` and `a8_m2_pre_rep_s3`. They are defined exactly as the seed-1/2 cavin replicates
  (amendments 1-2): src10, OpenRouter through the proxy wrapper.
* **Start.** The llm run starts on the first free GPU and the rep run on the next one.
* **Read.** The comparison is computed within cavin only, never pooled with Yangquan. It is reported next to M2-A,
  pooled with the cavin seeds 1-2, and its test is read with the study's.
* **Cavin replicate fallbacks, 2026-11-03.** These are tagged FALLBACK and kept, per the protocol:
  * `a8_m2_pre_llm_s2` round 3 (`RemoteDisconnected` after 3 retries; author `search`);
  * `a8_m2_pre_llm_s3` round 2 (`URLError`; the round completed and was accepted, 0.635 vs parent 0.63);
  * `a8_m2_pre_llm_s2` round 4 (`URLError` at ~08:34Z. The relay saw a `URLError` at 08:42Z in the same
    network blip and got through on its second attempt).
  * From their next resume on, the cavin runs use the patient client (a82600f) through the proxy wrapper with
    `RSI_LLM_RETRIES=8`, as llm_s3 does (addendum 18). They are not stopped to switch early: a stop mid-round
    would re-draw that round.
  * Tally at 12:20Z, by LLM call. `a8_m2_pre_llm_s1` made 7 calls: 2 failed and were re-drawn under amendment 2,
    and its 4 completed rounds are all LLM. `a8_m2_pre_llm_s2`: 2 of 4 rounds fell back. `a8_m2_pre_llm_s3`: 1 of
    3. All Yangquan runs go through the relay, which has 15 minutes of retries. None of them has fallen back since
    the provider switch.

## Amendment 4 (2026-11-03 ~13:55Z): a seed-4 cavin replicate

GPU0 has been free since `a8_goalmain_llm_s2` finished at 13:42Z, and the cavin queue is empty. Some runs of this
study already have a `report.json`. None of their test files, and no `tests` key, has been opened. The decision
rests on the free GPU alone.

* **Runs.** `a8_m2_pre_llm_s4` and `a8_m2_pre_rep_s4`, defined exactly as the seed-1/2/3 cavin replicates with
  engine seed 4. One difference: both run from **src10b**, which is src10 with only the patient LLM client
  (a82600f) added, through the proxy wrapper (`RSI_LLM_RETRIES=8`). With the variable unset the client is
  unchanged, and the rep arm never calls the LLM.
* **Why the change.** It brings the direct cavin calls up to the relay's patience (15 min). Seeds 2-3 lost 3 rounds
  to the 3-quick-retry client.
* **Start.** The llm run starts on the first free GPU and the rep run on the next one.
* **Read.** The comparison is within cavin only, pooled with cavin seeds 1-3, and read with the study's tests. The
  primary bar M2-A (Yangquan) is unchanged.

## Amendment 5 (2026-11-03 ~15:35Z): outbound-proxy outage

* **What.** cavin's outbound proxy (127.0.0.1:1080, a root-owned tunnel we do not operate) has stopped forwarding.
  Requests through it time out: OpenRouter and google.com both fail at 15:30Z. Its upstream host still answers
  directly. The last good relay answer was at 13:50Z. The first failed call started at ~15:11Z.
* **Affected so far.** All LLM meta calls go through this proxy, relayed (Yangquan) or direct (cavin), so they fail
  for as long as it is down. Two rounds fell back to the numeric search (author `search`):
  * `yq_m2_pre_llm_s1` round 6, a primary-study run. The relay sent an error answer at 15:30Z after 2 attempts
    (1127 s), each of which hung for about 9 minutes.
  * `a8_m2_pre_llm_s3` round 4 (cavin replicate): `URLError` at 15:26Z.
  * `yq_oftg_llm_harness_s2` round 6, a v3 Goal main arm (addendum 18). The relay sent an error answer at 16:21Z
    after 2 hung attempts (1035 s).
  * `a8_m2_pre_llm_s2` round 6 (cavin replicate): `URLError` at ~18:20Z.
  * `yq_m2_pre_llm_s3` round 6, a primary-study run. The relay sent an error answer at 19:14Z (931 s).
  * `a8_m2_pre_llm_s4` round 2 (cavin replicate, patient client): `URLError` after its 15-min retry budget, ~19:10Z.
  * `yq_oftl_llm_harness_s2` round 6, a v3 L10 arm (addendum 18). The relay sent an error answer at 19:48Z (1032 s).
  * `a8_m2_pre_llm_s3` round 5 (cavin replicate): `URLError` at 19:50Z.
  * **Scored before the proxy came back, so FALLBACK stays (as of 20:50Z):** `a8_m2_pre_llm_s3` round 4
    and `yq_m2_pre_llm_s1` round 6. `a8_m2_pre_llm_s4` round 2 crashed and is dropped (amendment 4a).
* **Proxy back at 21:59Z** (first good check at 21:59:46Z). Six rounds that fell back are still running, and none
  has been scored. Each is stopped and resumed (`--resume`), so it re-draws its LLM call:
  * on Yangquan, through the relay: `yq_m2_pre_llm_s3` round 6 (rsi_src_v24), `yq_oftg_llm_harness_s2` round 6
    and `yq_oftl_llm_harness_s2` round 6 (rsi_src_v17);
  * on cavin, direct: `a8_m2_pre_llm_s2` round 6 and `a8_m2_pre_llm_s3` round 5. They resume from src10b,
    the patient client, as the note under amendment 3 says ("from their next resume on").
  * `a8_m2_pre_llm_s0` (amendment 4a) is released from hold now.
* **The proxy flapped: down again at 22:02Z**, about 2.5 min after it came back. The re-draws still went ahead:
  * Both cavin re-draws were held for 2 minutes before launch, then released. Their GPUs would sit idle
    anyway, and the patient client retries for 15 min.
  * The Yangquan resumes (job-vwux5ax79s0c, job-hrhchcnb9qz7, job-3ytk6p2ixefr) were already submitted.
  * A re-drawn call that fails again leaves its round as FALLBACK and still unscored. That round is re-drawn
    again under the same rule once the proxy forwards again. The selection stays on call failure only.
  * As of 22:45Z the re-drawn calls have failed again. They are tagged FALLBACK, and each round stays in
    progress and unscored:
    * `a8_m2_pre_llm_s2` round 6 and `a8_m2_pre_llm_s3` round 5 (22:19Z);
    * `yq_m2_pre_llm_s3` round 6 (22:26Z);
    * `a8_m2_pre_llm_s0` round 1 (22:36Z).
    `yq_oftg_llm_harness_s2` and `yq_oftl_llm_harness_s2` are still retrying. The next re-draw waits until
    the proxy has been up on consecutive checks for at least 5 minutes.
* **The proxy is flapping (23:50-23:58Z).** It answered on 4 of 10 checks, 30 s apart, then went down again.
  * **Relay change (transport only, operational).** Each relay attempt used the client's default of
    3 tries x 180 s, so it hung for about 9 min, and only 2 attempts fit in the 15-min budget.
  * From 00:05Z the relay builds its client with timeout 120 s and 1 try. It retries every 10 s and stops
    after 23 min, inside the run side's 30-min wait.
  * Prompt, model, temperature and the parsing of the answer are unchanged. The only effect is that a
    short up-window is caught.
* **Scored while the proxy was still down, so FALLBACK stays (as of 02:55Z):**
  * `a8_m2_pre_llm_s0` round 1. Not accepted (search 0.57 vs seed 0.595, parent 0.60).
  * `a8_m2_pre_llm_s2` round 6, its last round. Accepted: search 0.67 vs 0.61, parent 0.62. The final policy
    of this cavin llm run therefore comes from a numeric-search proposal, and that is disclosed with its test.
* **Second re-draw, 03:11Z.** The proxy passed 5 consecutive 1-min checks from 03:07Z. Four fallback rounds are
  still running and unscored, and each is stopped and resumed:
  * `yq_m2_pre_llm_s3`, `yq_oftg_llm_harness_s2` and `yq_oftl_llm_harness_s2`, round 6 each;
  * `a8_m2_pre_llm_s3` round 5.
  * `a8_m2_pre_llm_s0` round 2 needs nothing: its patient client got a real LLM answer at 03:01Z.
  * `a8_m2_pre_llm_s3` round 5 wrote its round file at 03:12:18Z, about 20 s before the stop. It was scored
    (not accepted), so it keeps FALLBACK.
  * The stop cut off round 6's LLM call while it was still in flight; no answer had been logged. Nothing
    completed is re-drawn, and the run resumes at round 6 (`a8_m2_pre_llm_s3_redraw2`, src10b).
  * Yangquan resubmissions: job-isfuc5k0jwjn, job-mqdutod7t22y and job-ifgp8gdre6so.
  * The proxy dropped again at 03:12:45Z, so these calls may fall back once more. The same rule applies.
* **Handling, as in amendment 2 (outage, not a one-off blip).** The fix is with the cluster admin.
  * Once the proxy forwards again, any round that fell back during the outage and is still running is stopped and
    resumed (`--resume`), so it re-draws its LLM call. Its candidates must not have been scored yet. The selection
    is on call failure only.
  * A round that finished before the proxy came back keeps its FALLBACK tag.
  * Every round in either group is listed here.

## Amendment 4a (2026-11-03 ~20:20Z): the seed-4 cavin replicate is replaced by seed 0

* **Why.** `a8_m2_pre_llm_s4` crashed in round 2 (rc=1, `placement_seed_out_of_range:4301020000`). The engine's
  step seed is `run_seed * 1000 + 100 * round + step`, and LIBERO placement seeds are
  `1e8 + step_seed * 1e6 + ...`, which must stay below 2^32. That holds only for run seeds 0-3 (engine.py says
  so). Amendment 4 picked seed 4 without checking, and that was a mistake. `a8_m2_pre_rep_s4` would have crashed
  the same way, so it was stopped 4 min after its launch, before it scored anything.
* **The s4 record**, kept for disclosure: round 1 was scored (seed 0.61 vs llm 0.595, not accepted, parent 0.615).
  Round 2 fell back (proxy outage, amendment 5) and crashed before it was scored. Both s4 runs are dropped as
  crashed, and nothing from them enters any comparison. The crash forced this choice; no result did.
* **Replacement.** `a8_m2_pre_llm_s0` and `a8_m2_pre_rep_s0`, defined exactly as amendment 4 but with engine
  seed 0. Seed 0 is unused by this study and stays in range. The rep run starts now. The llm run is held until
  the outbound proxy forwards again (amendment 5), so it does not start on fallback rounds.

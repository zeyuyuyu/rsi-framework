# Prereg v3, addendum 35: the self-repaired loop continued under tuned RL's total budget, against tuned RL's best run

Committed 2026-11-13 (~00:40Z; commit time in git) before any run named here exists.

## Why

The paper compares the framework with RL only with RL's tuning counted (author's decision, 2026-11-12): the tuned recipe cost 21 pilot runs, at least 213.4 GPU-hours, and a comparison that leaves them out charges RL nothing for them.

What that comparison shows so far (`docs/results/TUNING_COST_20261112.md`, descriptive):
- Started from the failing BC recipe, the LLM meta level (`yq_oftgb_llm_harness_s{1,2,3}`, six rounds) ends level with tuned one-shot RL of 18 steps on the official test and +2.2 [+0.5, +3.9] ahead on the fresh scenes, at about half of RL's counted cost.
- Tuned RL run for 36 steps (`yq_oftg_onebig12_s{1,2,3}`, counted cost about 239 GPU-hours) ends higher than the self-repaired loop: 66.3% against 63.5% on the fresh scenes.

The self-repaired loop stopped at six rounds with half of RL's counted budget unspent. This addendum lets it go on until that budget is spent and asks whether it then ends above tuned RL's best run.

## What is already known (disclosed)

Every comparison arm has been read. Fresh-scene finals, seeds 1-3:

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| self-repaired loop at round 6 (`yq_oftgb_llm_harness`) | 64.2 | 64.5 | 61.9 | 63.5 |
| tuned one-shot RL, 18 steps (`yq_oftg_onebig`) | 60.0 | 62.2 | 61.8 | 61.3 |
| tuned one-shot RL, 36 steps (`yq_oftg_onebig12`) | 66.8 | 65.5 | 66.6 | 66.3 |
| tuned loop, guard-rail gate, 12 rounds (`yq_oftg_guard12`) | 66.9 | 64.9 | 63.9 | 65.2 |

Also known, and the reason for this design:
- At equal training compute the loop and RL tie in every registered read. Success follows the number of training steps: the gate success of the 12-round tuned loops rises about 0.6 points a round and is still rising at round 12. No run of ours goes beyond 36 steps.
- So the new runs are expected to gain from training longer, and E2 below is expected to pass. The open questions are whether the gain continues past 36 steps and whether it is enough to pass tuned RL's 36-step run within RL's counted budget.

## Budget

Costs are reserved card-hours: requested cards × job time (created to finished), summed over a run's jobs. Evaluation-only jobs are left out on both sides.

| seed | tuned RL, 36 steps: pilots + run | self-repaired loop so far | left for the continuation |
|---|---|---|---|
| 1 | 213.4 + 28.1 = 241.5 | 89.6 | 151.9 |
| 2 | 213.4 + 25.4 = 238.8 | 206.0 | 32.8 |
| 3 | 213.4 + 25.8 = 239.2 | 58.8 | 180.4 |

(`results/yq_selfrepair_job_sessions_20261113.json`; the RL runs held one card.)

## Runs

`yq_oftgbx_ext_s{1,2,3}`: each continues `yq_oftgb_llm_harness_s<seed>` from the end of its round 6 (`run_libero --extend-from`, source `rsi_src_v33` = `rsi/` at commit 63608cd, tarball sha256 `5980f6f51669127d…`).

- **What continues**: the run's retained version and its retained program (the recipe its own meta level repaired), its archive, its duplicate filter and its seed. Practice and gate placements of rounds 7 and later are the ones a longer run draws; none was used before.
- **What changes**: one candidate a round instead of two, so the meta level is never called again and the repaired recipe stays fixed; the guard-rail gate of addendum 32 (`min_gate_gain -0.05`, `gate_floor 0.05`); `test_all_accepted false`.
- **Cards and stop**: a run stops at its planned last round, or when its job reaches the time below, whichever is first. The times keep each run inside the budget above.

| run | cards | planned last round | job time limit | reserved card-hours at the limit |
|---|---|---|---|---|
| `yq_oftgbx_ext_s1` | 3 | 22 | 50.0 h | 150 |
| `yq_oftgbx_ext_s2` | 1 | 9 | 31.9 h | 32 |
| `yq_oftgbx_ext_s3` | 3 | 24 | 53.0 h (the job limit; before the cut-off) | 159 |

- A run cut by its time limit is read at the version it retained after its last completed round.
- A job that fails for an infrastructure reason is resubmitted with `RESUME_RUN`; its card-hours count.
- Cut-off: 2026-11-15 10:00Z. Anything still running then is stopped and read as above.

## Evaluations

For each run and each read, two jobs score the retained version: `--test-eval <run> --node <node> --replicates 3` (official test, three evaluations) and `--fresh-eval <run> --node <node>` (1,000 sealed fresh scenes), with `--interim` when the run has not ended.

- **Interim read**: the version each run retains after its last round completed by 2026-11-14 10:00Z. Run names `<run>_i14_rep`, `<run>_i14_fresh`.
- **Final read**: the version each run retains when it stops. Run names `<run>_fin_rep`, `<run>_fin_fresh`. If a run's interim and final versions are the same node, its interim evaluations are reused.

Each read happens once, when its six evaluations exist. A read whose evaluations do not all exist by 2026-11-15 14:00Z is reported as not read.

## Claims

Fresh scenes are primary; the official test is reported beside them. Seeds 1-3, paired within Yangquan, seed-averaged per-episode paired bootstrap (10,000 draws). The final read is primary; the interim read is reported as interim.

| claim | comparison | reading |
|---|---|---|
| E1 | continued loop − tuned one-shot RL, 36 steps | "beats" if the CI is above 0; non-inferior if its lower bound is above −2 |
| E2 | continued loop − tuned one-shot RL, 18 steps | bar ≥ +3, CI above 0 |
| E3 | continued loop − the same runs at round 6 | CI reported: what continuing added |
| cost | each run's reserved card-hours (round-6 cost + continuation jobs) against its seed's counted RL cost | reported per seed; E1 is "within RL's budget" only for seeds at or under it |

What each E1 outcome will be said to mean:
- CI above 0, all seeds within budget: counting its tuning, the loop ends above tuned RL's best run at no more total compute.
- Non-inferior: the loop matches tuned RL's best run, at the measured fraction of its counted cost.
- Lower bound at or under −2: tuned RL's 36-step run stays ahead, and the paper says so.

The win, if there is one, is of a particular kind and will be described as such: the loop spends on training what RL spent on pilots, so it trains for more steps within the same total. At equal training steps the two tie (addenda 18, 28, 30, 32, 33).

## Predictions

- Final E1, fresh scenes: +1 to +6, most likely about +3; CI above 0 with probability about 0.7. Official: −1 to +3.
- Interim E1, fresh scenes: −1 to +4; CI above 0 with probability about 0.45.
- E2 final, fresh: +5 to +10. E3 final, fresh: +3 to +8.
- Seed 2 gains least (three more rounds); seed 3 (a repaired BC recipe) gains less a round than seed 1.
- Chance that a run needs a resubmission because the extension path is new on the real backend: about 0.3.

## Readers

`fresh_read.py goal_ext` and `scripts/report/goal_ext_read.py` are committed before any evaluation of these runs exists.

## Operational notes

- 2026-11-13 00:15:30Z: this addendum was committed and pushed (8286333; the header's "~00:40Z" was an estimate written before the commit).
- 00:15:53Z: `rsi_src_v33.tgz` (sha256 `5980f6f51669127d…`) and the three plans were uploaded to BOS; the tarball was downloaded again and is byte-identical. The entry script link (`run_vla6.sh`) was re-signed and the script behind it is byte-identical to the repository's.
- 00:16:29-00:16:33Z: the three runs were submitted: `yq_oftgbx_ext_s1` job-lgsmcu53ia9y (3 cards, `RUN_TIMEOUT_S` 180000), `yq_oftgbx_ext_s2` job-939pnipsdu7k (1 card, 115000), `yq_oftgbx_ext_s3` job-e6e209tyaqp1 (3 cards, 190800). Each has `ARGS=--extend-from /mnt/pfs/shitianyu-rsi/runs/yq_oftgb_llm_harness_s<seed>`.
- The readers `fresh_read.py goal_ext` / `goal_ext_interim` and `scripts/report/goal_ext_read.py` were committed after the submission and before any round of these runs had completed; `--check` shows the continued runs' evaluations as missing, and the earlier block `goal_guard12` still returns G3 = −1.07 [−2.63, +0.53].
- If a run's interim and final versions are the same node, its `_fin_rep` and `_fin_fresh` result directories are copies of the `_i14` ones, and a line here says so.
- 00:18:32Z: `yq_oftgbx_ext_s1` (job-lgsmcu53ia9y) stopped 112 s after its job started, before any round: `Engine.__init__` still refused more than 12 rounds (`inner_steps_need_rounds<=9…`), a range check that the inner-seed extension of 63608cd had not updated. The copy of the source run had been made; nothing was trained, scored or gated. Its 3 cards × 3 minutes are counted in seed 1's cost.
- 00:19Z: `yq_oftgbx_ext_s3` (job-e6e209tyaqp1) was stopped by hand while still queued (status Created, no log line), because it would have failed on the same check. `yq_oftgbx_ext_s2` (9 rounds) is not affected and kept running on v33.
- Fix: the constructor's check now follows `inner_seed` (dba199f; test added, and the three real plans' engines were constructed locally). Source `rsi_src_v34.tgz`, sha256 `5d2b3e8a43798463…`, uploaded and verified byte-identical at 00:23Z. It differs from v33 only in that check.
- 00:23:57Z: seed 1 resubmitted as **`yq_oftgbx_ext_s1b`** (job-xsft8xehdfg5; the run dir `yq_oftgbx_ext_s1` already exists as an unextended copy, and the entry script does not reuse a name), same plan `yq_oftgbx_ext_s1`, same limits. 00:23:59Z: seed 3 resubmitted as `yq_oftgbx_ext_s3` (job-4218634nthwu). Evaluation run names stay `yq_oftgbx_ext_s1_i14_*` / `_fin_*`, with `--test-eval` / `--fresh-eval` pointing at `yq_oftgbx_ext_s1b`.
- 00:49Z: `yq_oftgbx_ext_s2` is in round 7: the heartbeat shows the copied rounds 1-6 and the run's third backend call, a practice rollout, with its card at 93%. The extension path works on the real backend.
- 00:53Z: the three-card jobs of seeds 1 and 3 had been queued (status Created) for 29 minutes while the one-card job of seed 2 had started within three. Change of cards for seed 1, made before any round of it: job-xsft8xehdfg5 was stopped while still queued and **`yq_oftgbx_ext_s1b` was resubmitted on one card** (job-btajrg01bzcz, `RUN_TIMEOUT_S` 190800, the 53-hour job limit; reserved cost at the limit about 54 card-hours, far inside seed 1's budget). Seed 1's recipe spends most of a round in training, which uses one card whatever the job holds, so it loses the least from this. Seed 3 keeps its three-card request for now.
- Cost rule made explicit before any result: a job that never left the queue (status Created until it was stopped: job-e6e209tyaqp1, job-xsft8xehdfg5) reserved no card and is not counted. The failed first job of seed 1 ran for three minutes on three cards and is counted.
- 01:21Z: `yq_oftgbx_ext_s1b` (one card, job-btajrg01bzcz) is in round 7 on source v34: its third backend call is a practice rollout.
- 01:22-01:38Z, seed 3, before any round of it: its three-card job (job-4218634nthwu) had been queued for 58 minutes and was stopped while still Created; a two-card job (job-ahnvf0zuyt7x) was queued for 13 minutes and stopped the same way; **`yq_oftgbx_ext_s3` then started on one card** (job-jr8hv88w0cl4, Running at 01:37Z, `RUN_TIMEOUT_S` 190800). Neither queued job reserved a card, so neither is counted.
- All three runs now hold one card. They will complete fewer rounds than the card plan in "Runs" assumed: about 8 more rounds for seed 1, 3 for seed 2 and 6 to 7 for seed 3, instead of up to 16, 3 and 18. The planned last rounds, the time limits and every claim are unchanged.
- The registered predictions stand as written. My expectation with one card each, written at 01:40Z before any round of these runs has finished: final E1 on the fresh scenes between 0 and +4, CI above 0 with probability about 0.45 (it was 0.7 with the three-card plan).


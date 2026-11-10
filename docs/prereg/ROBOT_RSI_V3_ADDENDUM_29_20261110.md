# Prereg v3, addendum 29: meta level v3 (the LLM behind a harness) and self-repair on a second suite

Committed 2026-11-10 before any run named here exists. Every registered read of earlier studies is done
(Goal main, 12 rounds, meta v2, self-repair on Goal); the LIBERO-Spatial main study (addendum 28) is running and
none of its runs has finished a round.

## Why

The meta level has one positive result and three nulls. From a procedure that already works, an LLM that edits the
procedure does not beat the same loop without it (R4 on Goal; M2-A/M2-B on two platforms). From a procedure that
fails (behaviour cloning on the policy's own high-temperature samples), the loop with the LLM meta level ends
+2.65 points above the gate-only loop, CI [+0.73, +4.58], under its +3 bar (addendum 24, read 2026-11-09).

Two things were weak in every meta level so far, and both are about the harness around the LLM, not the LLM:

1. **What it could see.** One prompt per round with a summary of the last 12 candidates cut at 12,000 or 30,000
   characters; nothing carried from round to round except the gate table; nothing carried from run to run. A fourth
   seed of the self-repair study chose to cool behaviour cloning instead of leaving it, although three finished
   runs had already shown what works.
2. **A defect found today.** `llm_history` read the training loss from `receipt["extra"]`. Receipts store it under
   `receipt["details"]`. So in every LLM meta run to date (addenda 14-26) the fields `loss_first` and `loss_last`
   reached the LLM as null, while the prompt told it to look for "a loss that keeps rising". No result changes;
   the unit test used the wrong key as well, which is why it passed. v3 reads both keys and its test uses the real
   one.

Recent outer-loop systems put the weight on exactly this harness. Meta-Harness (Lee et al., arXiv 2603.28052) gives
its proposer the code, scores and raw traces of every earlier candidate as files, and reports that selective access
to the full history beats compressed summaries. EvoTrainer (arXiv 2606.03108) keeps a layered diagnostic record
(score, signal, behaviour, version) and a persistent memory that includes failed branches. LLMZero (arXiv
2606.18388) has the LLM diagnose training signals at checkpoints and change several fields together. This addendum
builds the corresponding harness for our meta level and tests it where a meta level has shown an effect.

## Meta level v3 (`rsi/meta/harness.py`, proposer `llm3`)

Same LLM (claude-sonnet-5-5 through the existing gateway and relay), same edit space as meta v2 (`V2_SPACE`:
knobs, harness components, per-task weights), same engine. What changes is what surrounds the call:

* **Workspace.** Every candidate of the run is a file (`run/nodes/<node>.json`: procedure, change against its
  parent, gate against the parent overall and per task, every inner step's sampled success, share of scenes with both
  outcomes, items, per-task sampled success, loss at the first and last update step). Plus `run/overview.tsv`,
  `run/tasks.tsv` and `run/ledger.tsv` (gate changes pooled per edited field).
* **Memory across runs.** `rsi/meta/memory/v3/prior/`: one table per finished A800 run (32 runs: Goal main fixed and
  LLM arms, meta v2 `pre` arms, the Goal self-repair seed 0, the BC and GRPO curves, the failure pilots, the
  LIBERO-10 pilots, the Spatial curve and one Spatial LLM run), built by `scripts/meta/build_memory.py` from
  `archive.jsonl` with the same function that builds the live workspace. `playbook.md`: lessons the same LLM
  distilled from those tables before launch (`scripts/meta/distill_playbook.py`; the log of every turn is
  `distill-log.jsonl`). The memory is frozen: its digest is in every plan and the run aborts on a mismatch.
* **Memory within a run.** `memory/notes.md`: the LLM's own note from each earlier round.
* **Tools and turns.** `ls`, `read`, `grep`; up to 4 calls per turn and 6 turns per round, then the proposals.
  A reply may use up to 12,000 tokens (the gateway counts the model's reasoning inside the cap).
* **Noise stated.** The prompt gives the measured gate noise (about 3 points per evaluation, 3.4 between a child and
  its parent under an unchanged procedure) and what counts as evidence.
* **Unchanged guarantees.** The LLM never sees an audit score or a test result (`node_record` copies named fields
  only; the memory is built by the same function; the unit test checks the prompt of every turn). It can only
  change fields of the declared space. A failed call or an invalid proposal falls back to numeric search and is
  counted. Control arms the meta level cannot choose (nonrec, shuffled, onebig), replicate evaluations and the
  running addendum-28 runs are not in the memory. Yangquan runs are not in it either, because their synced records
  keep no procedure per candidate.

The memory holds gate-side records of the suite under test (two Spatial runs) and of the same failing recipe on
Goal. That is the point of a memory, and it is also what the hand-tuned loop had: its recipe was chosen from those
pilots. It means a v3 result is a result about a meta level **with** this experience; it says nothing about a
meta level starting cold.

## Design (LIBERO-Spatial)

Start program `bc_start`: the collapsing recipe of addenda 12 and 24 with the suite changed (`update.operator` bc,
`curation.rule` verified, 64 scenes, 8 tries at temperature 1.6, lr 1e-5, 100 steps of batch 64, `bc_temp` unit,
`loss_agg` episode, `ratio` matched). Gated loop as in addendum 28: 6 rounds, 3 inner steps, fresh paired gates
(20 per task), `heldout_per_task` 40, `test_inits_per_task` 50.

| runs | proposer | candidates / round | role |
|---|---|---|---|
| `yq_oftsb_fixed_s{1,2,3}`, `a8_spatrep_fixed_s0` | fixed | 1 | the gate alone |
| `yq_oftsb_full_s{1,2,3}`, `a8_spatrep_full_s0` | numeric search, `HARNESS_SPACE` | 2 | blind search, same compute as meta3 |
| `yq_oftsb_meta3_s{1,2,3}`, `a8_spatrep_meta3_s0` | `llm3`, `V2_SPACE`, memory v3 | 2 | meta level v3 |
| `yq_ofts_meta3_s{1,2,3}` | `llm3`, from the tuned Spatial program of addendum 28 | 2 | does v3 add anything to a working recipe? |

* Both search arms are capped at the start program's work per inner step (`budget: seed`, addendum 19): 512 tries
  and 6,400 training examples. The tuned recipe fits the cap exactly. Addendum 24's arms were not capped; this is a
  deliberate tightening, so a repair cannot be bought with compute.
* `meta3` runs with `engine.meta_v2` (per-task gate records; candidates start from their parent's task rates), as
  the meta v2 arms did. `fixed` and `full` run as in addendum 24.
* Seeds 1-3 on Yangquan (source `rsi_src_v29`, this commit's `rsi/`, tarball sha256 285dfb9526f256fa...), seed 0 on the
  A800 node (`src11`, the same tree), pairing within a platform as
  everywhere else. Two-candidate runs may use 2 or 3 cards (rollouts on all cards, training on the first), as in
  addendum 26; the card count is recorded per run.
* LLM calls: Yangquan through the relay (80 slots per run), the A800 node directly. At most 60 calls per run. A round
  whose call failed and fell back to numeric search before any candidate was scored is stopped and resumed, which
  redraws the call (selection on call failure only, addendum 21 amendment 2); a fallback round that was already
  scored stays and is tagged.

## Bars (official 500-episode test; final = per-episode mean of three evaluations)

* **S1-spatial (primary): `meta3 − fixed` ≥ +3.0, CI excludes 0**, seeds 0-3, seed-averaged per-episode paired
  bootstrap (10,000 draws). The same bar as S1 on Goal. The Yangquan three-seed statistic is reported alongside.
* **S2-spatial (reported with CI, no bar): `meta3 − full`.** Diagnosis with memory against blind search at equal
  compute.
* **S3-spatial (descriptive): `meta3` and `fixed` against the hand-tuned loop** (`yq_ofts_fixed_s1-3`,
  `a8_spatmain_fixed_s0` of addendum 28).
* **R4-spatial: `yq_ofts_meta3 − yq_ofts_fixed` ≥ +2.0, CI excludes 0**, Yangquan seeds 1-3 (the prereg's meta bar).
  The two arms differ in compute (two children per round against one), so a pass would need a replica control
  before any claim; a fail needs none.
* Reported with every claim: the round in which a non-BC procedure was first kept, per arm and seed; the diagnoses
  and notes verbatim; tool calls per round; fallback rounds; the audit change of the retained policy (fresh
  scenes, descriptive); work per inner step of every kept procedure; the noise check on n0 halves.
* Reader: `scripts/report/spatial_repair_read.py`, committed with this addendum.
* **One read.** When the twelve BC-start runs and the three tuned-start runs have `report.json` and both
  replicates. If `a8_spatrep_full_s0` is not complete by 2026-11-14 12:00Z, S1, S3 and R4 are read then, S2 is read
  on the seeds whose `full` run is complete, and the missing seed is added as a dated amendment.

## Predictions, written before launch

* `fixed` from the BC start ends within 1.5 points of its start: the gate refuses the collapse, as on Goal.
  If BC does not fail on Spatial, `fixed` gains like the tuned loop and S1 is near zero whatever the meta level does.
* `meta3` leaves BC in round 1 or 2 on all four seeds (the playbook holds the Goal record) and then tracks the tuned
  loop. S1-spatial lands between +2 and +5; I give the +3 bar about even odds. Whether the tuned loop itself gains
  on the official Spatial test is not known yet (addendum 28 predicted +2 to +4), and S1 cannot exceed that by much.
* S2-spatial is positive with a CI that includes 0 on four seeds: numeric search found the repair on two of four
  Goal seeds, late.
* S3-spatial: parity with the hand-tuned loop, as on Goal (+0.28).
* R4-spatial: between −1 and +1, a fourth null from a working recipe. The playbook itself records that edits to a
  working GRPO recipe did not move Goal, so the likely behaviour is small edits or none.
* If S1-spatial fails, the paper keeps the Goal result as it stands (an effect of +2.65 with CI above zero, under the
  bar) and reports the replication as it comes out. If it passes, the claim is limited to what was tested: a meta
  level with memory of earlier runs turns a failing procedure into a working one on a second suite.

## Pre-launch record (no GPU run; gate-side records and LLM calls only)

* **Memory.** Built from 32 A800 runs at 05:16Z. The first distillation (05:20Z, 14 turns) wrote no playbook: the
  reply cap of 6,000 tokens was used up by the model's reasoning on the last turns, and in some turns the model wrote
  tool calls in a tag syntax the parser did not read. The log is kept (`distill-log-attempt1.jsonl`). The parser
  now reads both syntaxes and takes the first whole JSON object of a reply; the cap is 16,000 for distillation and
  12,000 in runs. The second distillation (05:30Z) read 22 run tables in 6 turns and wrote `playbook.md` (86 lines;
  the prompt asked for at most 70, the text is kept as written). Memory digest
  `1564313bdfc792cd0dc4d3ee64a702379b5897ab159c4f19041734fc454d532c`, the same on the workstation and on the A800
  node. Cost of both attempts: about 1.3 USD.
* **What the playbook says** (the LLM's own reading of gate-side records, not a registered result): one gate reading
  has a standard deviation of about 3 points and a single change under 6 is noise; GRPO starts were reliable on Goal
  and Spatial, BC at lr 1e-5 was the only recipe that collapsed, with a drop of sampled success inside a round and a
  jump of the first loss one round before the gate fell; earlier LLM edits did not beat re-running the same
  procedure; switching BC to GRPO is "supported with caution" (one run).
* **Replay smoke** (`scripts/meta/replay_smoke.py`, 05:32Z): the harness proposer was given the archive of
  `a8_oftgb_fixed_s0` (Goal, BC start, gate only) cut after round 0 and after round 3, with the suite set to Spatial.
  Both times it read the playbook and the run tables in one tool turn and proposed BC to GRPO on mixed groups with
  lr 1e-4 and token loss (the `pre` recipe of meta v2, the one with the highest sum of kept changes in its memory),
  2 to 3 turns, about 0.04 USD per round. Nothing was trained. The first smoke lost one turn to a reply that
  carried two JSON objects; the parser fix above came from it.
* **Relay.** The relay's per-try timeout went from 120 s to 400 s (a try that times out is paid for and repeated),
  and the relay process on the A800 node was restarted at 05:31Z; no run was using it.
* **Unit tests:** 44 pass, including the v3 test (no audit string in any turn's prompt, tool calls, notes found
  again next round, call cap across a resume, fallback on a failed call).

## What is not changed

No registered read, bar or run changes. Addendum 28's sixteen runs are read on their own; this study reuses its
`fixed` runs only as the hand-tuned reference of S3 and R4. No LLM provider or model changes.

## Operational notes (appended 2026-11-10 05:45Z; no design change)

* Registered as 66e8ff7 at 05:34:25Z, pushed 05:34:27Z, before the first launch (05:36:09Z).
* A800 node, source `src11`: `a8_spatrep_fixed_s0` launched 05:36:09Z on GPU 5; `a8_spatrep_meta3_s0` launched
  05:36:09Z on GPUs 6 and 7 (two cards). `a8_spatrep_full_s0` is queued when a card frees.
* Yangquan, source `rsi_src_v29`: `yq_oftsb_meta3_s1` job-tbz439hnaxty (05:36:12Z, two cards, 80 relay slots) runs
  first as the canary of the v3 code path; the other four meta3 runs are submitted once its first meta call has
  been answered. Submitted at 05:36:43-05:36:53Z: `yq_oftsb_fixed_s1-3` job-n0gmy4g8pbzk, job-l5wvnxsm74f2,
  job-wcqpu0wzg4je (one card each); `yq_oftsb_full_s1-3` job-2ip8kewtmsqc, job-mt68wtwe23ag, job-gr8sajq84v2y (two
  cards each). Those that find no free card wait in the queue behind the twelve addendum-28 runs.
* **First live meta calls (round 1, before any training).** `a8_spatrep_meta3_s0` at 05:48Z: two turns, read the
  playbook, `run/nodes/n0.json` and `run/tasks.tsv`, proposed BC to GRPO on mixed groups with lr 1e-4 and token loss;
  accepted by validation, no fallback. `yq_oftsb_meta3_s1`: the same reads and the same proposal, no fallback.
* **Relay outage, 05:36Z to 06:09Z.** The relay on the A800 node died at 05:36Z with a JSON error: it read the
  canary's slot file while it was still being copied. No answer was lost, because the canary's first call was only
  posted at about 05:57Z; it then waited 777 s and was answered at 06:09:47Z when the relay was restarted (the node
  waits up to 30 min per call). Fixes: the relay skips a run file it cannot parse and reads it again on the next
  pass; the submit script copies the slot file under another name and renames it. My first restart attempt did
  nothing because its process check matched its own command line; the second counted the Python process only.
* **Remaining Yangquan runs**, submitted after the canary's answer, two cards each: `yq_oftsb_meta3_s2`
  job-d5ze9tuhjfu3 (06:12:51Z), `yq_oftsb_meta3_s3` job-olfjuwpc1f42 (06:14:04Z), `yq_ofts_meta3_s1`
  job-mq6tvlzyelsc (06:15:07Z), `yq_ofts_meta3_s2` job-e6pnli6w5441 (06:15:43Z), `yq_ofts_meta3_s3`
  job-4wftsmvpoygl (06:16:45Z). All twelve Yangquan runs of this study are now submitted; those without a free card
  wait in the queue.
* `a8_spatrep_full_s0` queued on the A800 node at 06:18Z (order 93, one card); it starts when a card frees.

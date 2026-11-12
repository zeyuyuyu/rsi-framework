# rsi-framework: a two-level recursive self-improvement (RSI) training framework

The deliverable is the framework, not a training algorithm. A model writes its own practice tasks,
attempts them, gets each attempt judged by an external oracle it cannot change, and learns from the
verified experience. The improved model then writes the next round's tasks. A second, meta level keeps
the *improvement program* itself (what tasks to write, which experience to keep, how to update) under
version control and lets it be improved too. SFT and GRPO are interchangeable update operators.

Every control (no recursion, shuffled feedback, fixed program, compute-matched single round) is a
switch in the same engine, and every claim is pre-registered in `docs/prereg/` before its runs.

## How one round works

Object level, every round:

1. **Propose:** the current model writes tasks.
2. **Attempt:** it tries each task 8 times.
3. **Verify:** an external oracle labels each attempt 1 or 0.
4. **Curate:** keep groups that contain both successes and failures; drop guessable answers.
5. **Update:** a LoRA update (GRPO or SFT; behaviour cloning for the VLA).

The gate decides whether the new version is kept:

* A candidate is accepted only if it does not regress on the **gate** set.
* The **audit** set is recorded but never decides; it shows overfitting to the gate.
* The **test** suites stay sealed until every decision is made.

The meta level versions the improvement program as structured JSON plus a task-writing instruction.
Each round the full arm tries the incumbent program and one new candidate. Candidates come from one of
three proposers in `rsi/meta/proposers.py`:

* `FixedProgram`: no change.
* `NumericSearch`: random knob changes, biased toward knobs that helped the gate before.
* `SelfEdit`: the model being trained rewrites its own program JSON, including the task instruction,
  inside a declared edit space.

Candidates are trained for real, and the gate picks the program to keep.

## Layout

| path | content |
| --- | --- |
| `rsi/core/` | engine (`engine.py`), archive, curation rules, stats, GPU admission and supervised workers |
| `rsi/domains/code_wm/` | code world model: self-proposed Python programs, sandboxed interpreter oracle, CRUXEval-O / CRUXEval-I / LiveCodeBench-exec tests, MBPP gate/audit |
| `rsi/domains/libero/` | OpenVLA x LIBERO-goal: freshly sampled placements, simulator success as oracle, 500 official episodes as test |
| `rsi/backends/llm/`, `rsi/backends/openvla/` | vLLM sampling + PEFT LoRA training workers; OpenVLA rollout and GRPO/BC training workers |
| `rsi/meta/proposers.py` | meta-level proposers |
| `rsi/audit/` | independent re-scorer (`rescore_code_wm`) and pre-registered claim statistics (`compare_arms`) |
| `rsi/run_code_wm.py`, `rsi/run_libero.py`, `rsi/queue_runner.py` | entry points and the shared-box GPU queue |
| `docs/prereg/` | pre-registration v2, addenda 1-3, VLA pre-registration + addendum, frozen seed program, results notes |
| `results/` | small run records from the A800 and Baidu AIHC (plans, archives, per-round decisions, sealed test records, claim JSONs); checkpoints stay on the servers |
| `scripts/a800/`, `scripts/baidu/` | queueing, patrol and Baidu AIHC submission / result-extraction scripts |
| `test_rsi_core.py` | unit tests (engine with a toy domain, curation, sandbox trust, GPU admission) |

## Running

```bash
python -m pytest -q test_rsi_core.py

# one code-world-model run from a frozen plan (see results/a800/plans2/ for real plans)
python -m rsi.run_code_wm --plan plan.json --out runs/<new-dir>          # add --baseline-only for a baseline
python -m rsi.run_libero  --plan plan.json --out runs/<new-dir>          # OpenVLA x LIBERO

# multi-angle checks
python -m rsi.audit.rescore_code_wm runs/<run> cruxeval/test.jsonl lcb_execution/test.parquet
python -m rsi.audit.compare_arms results/ --suite cruxeval_o [--study long8] [--json out.json]
```

Environments used:

* Qwen2.5-Coder and Granite: torch 2.4.0 (cu121), vLLM 0.6.3.post1, transformers 4.51.3, peft 0.13.2.
* Qwen3-8B: torch 2.8.0 (cu128), vLLM 0.11.0, transformers 4.57.1, peft 0.13.2.
* OpenVLA: its own env with LIBERO, robosuite and MuJoCo (EGL rendering).
* Baidu AIHC jobs: the `vllm-openai:v0.11.0` image (`scripts/baidu/run_rsi.sh`).

Data paths are plan fields: `data.cruxeval`, `data.lcb`, `heldout.paths` (MBPP).

## Results so far (2026-11-08)

**New (2026-11-12): the same comparison on LIBERO-Spatial (addendum 31, part A).**
- At equal training compute, the gate alone ends **+13.0 [+10.4, +15.6]** above plain training on the official test (registered bar +10 met). On the fresh scenes it is +8.4 [+6.7, +10.1], under the bar.
- Plain training loses 15 points. On one seed (A800 node) it collapses to 1.2%.
- N2, the meta-level arm, is read when its runs finish.

Note: `docs/results/SPATIAL_NOGATE_PARTA_20261112.md`.

**New (2026-11-12): the framework against plain training on LIBERO-Goal (addendum 32, 9 runs).**
- Trained without the framework's gate, the same recipe ends 15.2 points below its start on the official test and 16.3 below on 1,000 unseen scenes. The recipe is iterated self-training on verified successes, run on three seeds.
- At equal training compute, the gate alone ends **+13.6 [+10.5, +16.8]** (official) and **+15.5 [+13.2, +17.8]** (fresh) above plain training. With the meta level the gap is +16.0 / +19.8. All four pass the registered +10 bar.
- The predicted collapse under 30% did not happen.

Note: `docs/results/GOAL_NOGATE_READ_20261112.md`.

**New (2026-11-11): LIBERO-Object curve read (addendum 13, one seed).** Plain GRPO self-practice lifts a LIBERO-Object policy from 55.8% to 82.0% on 400 sampled placements: D = **+26.1 points [+22.0, +30.5]**, with gate and audit halves alike. This is object-level evidence on a third suite, not an RSI claim; the official test stays sealed. Note: `docs/results/M1_OBJECT_20261111.md`.

**New (2026-11-11): LIBERO-Spatial main study read (16 runs).** On 1,000 sealed unseen scenes the self-improvement loop lifts the policy by **+5.65 points [+4.28, +7.04]** over its start (every seed, registered bar met); with shuffled verifier labels it ends 6.05 lower and with practice from the frozen initial policy 4.55 lower (both pass their bars). Recursion also passes on the official test (+5.73 [+4.12, +7.38]); on the official fixed states the loop shows no gain over its start (−0.01). One round of plain RL at equal compute ties the loop on both tests. Note: `docs/results/SPATIAL_MAIN_READ_20261111.md`.

**Running (2026-11-10), no result yet:** two studies registered and launched, 32 runs. (1) LIBERO-Spatial main study
(addendum 28): the four Goal arms (fixed, nonrec, shuffled, onebig) on a second suite, 16 runs. (2) Meta level v3 and
self-repair on Spatial (addendum 29): the meta-level LLM now works behind a harness (a workspace with every candidate
of the run, a frozen memory of 32 earlier runs with a playbook it distilled itself, its own notes, and ls / read / grep
tools; `rsi/meta/harness.py`), tested from the collapsing BC recipe against a gate-only loop and blind numeric
search, 15 runs. Bars and predictions are in `docs/prereg/ROBOT_RSI_V3_ADDENDUM_28_20261110.md` and
`..._ADDENDUM_29_20261110.md`; per-round gate records (not results) and the to-do list are in
`docs/STATUS_TODO_20261110.md`; run records under `results/` are synced every two hours.

**New (2026-11-09):** the self-repair study is read (addenda 24/26, 12 runs): from a recipe that collapses without the gate, a language-model meta level allowed to edit it brings the loop back to the hand-tuned level, **+2.65 points [+0.73, +4.58]** over the gate alone, under the preregistered +3 bar; blind numeric search over the same knobs is within +1.15 [−0.63, +2.92] of it. The gate alone prevents the collapse and holds the start. Note: `docs/results/SELFREPAIR_READ_20261109.md`.

**New (2026-11-08):** the registered 12-round read (addendum 27) is in: recursion vs no recursion **+7.8 points [+5.2, +10.5]**, bar met, because the non-recursive loop degrades over twelve rounds while the recursive loop holds its 6-round level; the gated loop still ties one-shot RL at equal compute (−0.4). Note: `docs/results/LONG12_READ_20261108.md`.

Full map of the studies, protocol and conclusions: **`docs/EXPERIMENTS_AND_RESULTS.md`**. In short:

| finding | evidence | strength |
| --- | --- | --- |
| the gated loop does not degrade a VLA policy at six rounds with recursive practice | 31/31 LIBERO-Goal runs end within noise of or above their start; the same BC recipe collapses 58.5% → 5.5% without the gate. Condition (12-round read): with practice from the frozen initial policy the loop drifts 4-11 points below its start over twelve rounds through gate-accepted versions | hard, with the stated condition |
| verified feedback improves code world models | 1.5B CRUXEval-O +2.6 [0.6, 4.6] vs shuffled −0.2; 7B LCB-exec +5.8 [3.4, 8.2] | significant |
| recursion helps at long horizon (code domain) | 8 rounds: fixed − nonrec +2.8 [1.2, 4.5]; 7B +2.9 / +4.5 | significant, replicated |
| VLA loop gains are small and below the preregistered bars | loop +1.7 [−0.8, +4.2] (bar +5); recursion +1.7 [−0.3, +3.7] (bar +2); verifier +1.2 (bar +3); one-shot RL at equal compute −0.6 | directional |
| a meta level does not beat a working fixed procedure | four R4 arms within ±1.2; v2 study −0.27 / +0.30; mechanism: the loop plateaus under every program | null, explained |
| a published VLA-RL number is inflated by training on the test states | +16.8 [9.8, 23.4], replicated +16.0 | significant |
| can the meta level repair a failing procedure? | self-repair study (12 runs): llm_harness − gate-only +2.65 [+0.73, +4.58], bar +3 missed; vs numeric search +1.15 (CI incl. 0); repaired loop ties the hand-tuned loop (+0.3) | significant, under its bar |

Every number traces to a file under `results/` and a pre-registration under `docs/prereg/`; the independent
re-scorer agrees with the engine on 99.6-100% of code-domain test records.

## Provenance

Extracted from `zeyuyuyu/cognitive-rsi-harness` (branch `rsi-universal-v1`), keeping only this project's
paths with their commit history, so each pre-registration's commit time precedes its results. Code and
documents were written with Claude Code.

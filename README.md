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

## Results so far (Qwen2.5-Coder-1.5B unless noted; CRUXEval-O points, paired, seed-averaged, 95% CI)

| claim | comparison | result | status |
| --- | --- | --- | --- |
| C1 improvement | full program, final - initial (3 seeds, 4 rounds) | +3.7 [+1.5, +5.9] | met |
| C2 external feedback | fixed - shuffled feedback | +2.7 [+0.9, +4.5] | met |
| C3 recursion | fixed - frozen initial generator, 4 rounds | -0.6 [-2.2, +1.1] | not shown |
| C3 at long horizon | same, 8 rounds (Addendum 3) | +2.8 [+1.2, +4.5] | supported (exploratory) |
| C4 meta level | full - fixed | +0.8 [-0.7, +2.4] | not shown |
| C5 iteration | fixed (4 rounds) - one compute-matched round | +0.4 [-1.2, +2.0] | not shown |

The independent re-scorer agrees with the engine on 99.6-100% of test records.

Cross-model and OpenVLA runs are in progress:

* **Qwen2.5-Coder-7B, fixed program:** LiveCodeBench-exec +5.2 and +4.6 in two seeds, both
  significant.
* **Granite-3.3-8B:** mixed.
* **Qwen3-8B:** the gate rejected every round (self-made tasks too easy).
* **OpenVLA:** the baseline noise floor is 12.4% flipped episodes between identical runs.

Every number traces to a file under `results/` and a pre-registration under `docs/prereg/`.

## Provenance

Extracted from `zeyuyuyu/cognitive-rsi-harness` (branch `rsi-universal-v1`), keeping only this project's
paths with their commit history, so each pre-registration's commit time precedes its results. Code and
documents were written with Claude Code.

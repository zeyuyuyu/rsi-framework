# Pre-registration: code world model RSI (rsi_engine_v1)

Committed 2026-10-25, before any RSI training run, any held-out score of a trained
version, or any tuning. Only the initial-model harness baseline (below) may be read first.

## Question

Does a model that predicts program execution (a code world model) improve on held-out
public benchmarks after rounds of the framework's closed loop, and is the external
verifier the reason?

Loop per round, from the retained version:
1. **Propose**: the current model writes new short programs with inputs (3-shot from a pool
   that starts with 16 hand-written seeds and grows with admitted programs). The sandbox runs
   each program twice; only deterministic, literal-valued, statically admissible programs that are
   not near-duplicates (char-10-gram Jaccard >= 0.5) of any held-out program are admitted.
2. **Act**: the current model writes K=8 CoT traces per case (T=0.8, top-p 0.95), CRUXEval-O format.
3. **Verify**: an attempt is verified iff its answer is a Python literal equal to the value the
   sandboxed interpreter computes (function-call "answers" are rejected).
4. **Curate**: `verified_self` keeps verified traces only, <= 2 per case, hardest-still-solvable
   cases first, <= 2000 per round.
5. **Update**: LoRA (r64, alpha128, all linear projections) continued from the retained parent,
   64 optimizer steps x 32 sequences, lr 1e-4 constant after 5 warm-up steps, completion-only loss.
6. **Retain**: keep the candidate iff greedy accuracy on a 400-program validation set (proposed by
   the *initial* model before training, executor-labelled, shared by all arms/seeds of that model)
   does not drop.
3 rounds. Test suites are read only after retention is frozen, for every produced version.

## Arms

* `verified_self` (RSI): as above.
* `unverified_self` (matched control): identical loop, but each round trains on the same number
  of self-generated traces drawn uniformly regardless of verification. Same steps, same data
  volume and format, no external feedback. Separates "feedback matters" from "more fine-tuning in
  this format".
* `initial`: the starting checkpoint.

## Held-out tests (never trained on, never used for retention)

* **Primary**: CRUXEval-O, 800 problems, greedy CoT, literal-exact pass@1.
* Secondary: CRUXEval-I (input prediction; a task the loop never trains on — transfer);
  LiveCodeBench execution-v2 (479 problems from a different source distribution).

## Models

Development model: Qwen2.5-Coder-1.5B-Instruct (the configuration above may be fixed using its
**validation** curve only; any change is logged with the reason). Then, frozen: Qwen2.5-Coder-7B-Instruct,
Qwen3-8B, Meta CWM 32B (if it loads), and one non-Qwen model. 3 seeds per arm; the seed changes the
proposed programs, sampled traces and training order (data seeds, not only init).

## Bars (per model, on the primary test)

* **P1 improvement**: mean over 3 seeds of (final retained − initial) >= +2.0 points, the paired
  bootstrap 95% CI of the seed-averaged per-problem difference excludes 0, and >= 2 of 3 seeds have
  their own CI excluding 0.
* **P2 feedback is the lever**: mean `verified_self` final − mean `unverified_self` final >= +1.5
  points with a paired CI excluding 0.
* Negative readings are reported as such: P1 fail = "did not improve on this model"; P1 pass with
  P2 fail = "improved, but not attributable to verification".
* Secondary suites: reported with CIs; no bar.

## Required checks before any claim (multi-angle matrix)

1. Second, independently written scorer recomputing every test score from the raw records.
2. Manual inspection of >= 30 sampled flips (initial wrong -> final right and the reverse): is a
   change a reasoning change or a format/parse change? Report the unparseable rate per version.
3. Leakage audit: nearest held-out neighbour Jaccard for all admitted training programs.
4. Other models (above), other suites (secondary), data seeds (3).

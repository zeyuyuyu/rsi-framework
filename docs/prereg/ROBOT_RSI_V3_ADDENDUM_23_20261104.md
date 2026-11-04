# Prereg v3, addendum 23: no further meta-level study before the deadline; a fourth seed for R2, R3 and R5

Committed 2026-11-04 ~15:30Z, before any `nonrec`, `shuffled` or seed-0 Goal run has a `report.json`, and before the
Goal read-once.

## Decision: the meta level is not re-tested with a larger gate

A 400-episode gate (sd of the paired gate difference about 2.4 instead of 3.4 at 200 episodes) was considered. It is
not run, for these reasons, all from gate data and LLM logs, never from a sealed test:

* **Gate deltas.** Over the v2 study, the LLM's proposals scored −1.2 points against the incumbent at the gate (n=30),
  while identical-program replicas scored +0.6 (sd 3.4, n=36). On cavin: +0.5 (n=12) vs −0.8 (n=21). There is no
  edit effect for a finer gate to resolve.
* **Three suites, no gate-level signal for any meta variant.** Goal v3 (`full`, `llm`, `llm_harness`,
  `llm_harness_cap`), Goal v2 (`llm` vs `replica`, both starts), LIBERO-10 (`llm_harness` vs `fixed`, addendum 17,
  gates 0.17-0.21 in both arms), and the cavin replicate. Final retained gates on Goal: `fixed` 62.8, `full` 63.5,
  `llm_harness` 65.0, `onebig` 61.7, all within the gate noise.
* **Mechanism.** The LLM's diagnoses read the loop correctly (task 0 never solved so GRPO has no signal, task 7
  saturated, "changes within gate noise") and its edits are the ones a practitioner would try (task weights off
  tasks 0 and 7, lower lr and temperature, z-scored advantages). None moves Goal success in 6 rounds: the
  object-level loop reaches the same plateau under every recipe in the space.
* The sealed meta-level claims (R4, R4-llm, L10 `llm_harness − fixed`, M2-A/M2-B already read) are reported as
  preregistered. A second meta study would add a test without a hypothesis for how it could pass.

## A fourth seed for the RSI-versus-RL claims

To raise the power of R2 (`fixed − shuffled`), R3 (`fixed − nonrec`) and R5 (best gated arm − `onebig`) on
Yangquan, seed 0 is added: `yq_oftg_fixed_s0`, `yq_oftg_nonrec_s0`, `yq_oftg_shuffled_s0`, `yq_oftg_onebig_s0`.
Each is the seed-1 plan of the same arm with `engine.seed = 0` and nothing else changed (seed 0 is in the valid
range 0-3, addendum 21 am. 4a, and unused on Yangquan). Same source rsi_src_v17, same queue and limits.

* **Read.** R2, R3 and R5 are seed-averaged over seeds 0-3 on Yangquan. Bars unchanged (+3, +2, +2; CI excludes
  0). The per-seed values are reported, and the 3-seed (1-3) statistic alongside, so the effect of adding the
  seed is visible.
* R1, R4 and R4-llm are unchanged (seeds 1-3; `full` and `llm` have no seed 0).
* Tests stay sealed until all four Goal seed-0 runs and all six addendum-22 runs have `report.json`; the Goal
  read-once then covers R1-R5 together.

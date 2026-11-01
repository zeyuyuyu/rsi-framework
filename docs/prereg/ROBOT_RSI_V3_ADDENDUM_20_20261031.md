# Prereg v3, addendum 20: the compute-capped harness arm on a second suite, LIBERO-Spatial

Committed 2026-10-31 (~19:00Z), before any run named here starts. No main-arm test has been read. Bars of addenda
14-19 are unchanged.

## Why

Addendum 13 set a bar for another suite, and the LIBERO-Spatial GRPO curve on cavin (`a8_ofts_curve_grpo_s0`, one
seed) cleared it: D = +7.63, paired 95% CI [+4.50, +10.88]. Its audit half alone gives +9.00 [+5.00, +13.25]. Plain
GRPO therefore improves the Spatial checkpoint too, which makes Spatial a second suite where the meta-level question
can be asked. That question is whether, at equal compute, the meta level's edits beat the fixed procedure.

## Run

* `a8_spatmain_llm_harness_cap_s1`, cavin queue 43, from src7. This is the arm of addendum 19 unchanged apart from
  the suite: the OFT 1-trajectory Spatial SFT checkpoint, `libero_spatial`, the Goal main program (64 scenes, T 1.6,
  GRPO lr 3e-5, 100 steps, matched, episode), and the seed cap of 512 rollouts and 6400 examples per inner step.
  It has 6 rounds, fresh paired gates, two candidates per round and seed 1.
* It starts on the first free cavin GPU after queue 40-42. More seeds are added only if a platform frees before
  2026-11-01 18:00Z, and each is announced here as an amendment before it starts.

## Read

* **H-cap-spatial (exploratory).** The mean of proposal gate minus incumbent gate over this suite's rounds and runs,
  with a run-clustered bootstrap CI when there is more than one run, else a round-level CI. It is reported next to
  the Goal H-cap and never pooled into it. The registered H-cap of addendum 19 stays Goal-only.
* There is no fixed partner, so no arm-level Spatial claim is made.

## Amendment 1 (2026-11-01 ~13:10Z, before the final test pass): scope of the read-once rule

This amendment only clarifies scope. It adds no read and changes no bar.

* The registered Spatial read (H-cap-spatial) uses gates only. No Spatial claim rests on the official test.
* The final Goal test pass (addendum 18, amendment 2) waits for every Goal main arm. It does not wait for
  `a8_spatmain_llm_harness_cap_s1`, and it does not open that run's test files.
* The Spatial run's test file is opened only after its own `report.json` exists, and is reported as descriptive.
  Reading the Goal test (another suite, checkpoint and episode set) is not an early look at Spatial. Because of the
  design freeze, nothing in the Spatial run depends on it.

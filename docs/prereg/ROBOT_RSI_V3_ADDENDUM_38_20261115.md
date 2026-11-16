# Prereg v3, addendum 38: the continued loop run up to tuned RL's counted budget (equal total GPU-hours)

Registered 2026-11-15 08:40Z, before any job of it was submitted. Requested by the PI: compare the loop with tuned RL when both have spent the same total GPU-hours, RL's recipe pilots included.

## Why

Addendum 35 stopped each continued run at a job-time limit set for three cards. Seeds 1 and 3 then ran on one card (the three-card jobs never left the queue), so they stopped with much of RL's counted budget unspent:

| seed | tuned RL, 36 steps, counted (addendum 35) | loop so far (round 6 + continuation) | left |
|---|---|---|---|
| 1 | 241.5 | 142.6 | 98.9 |
| 2 | 238.8 | 238.0 | 0.8 |
| 3 | 239.2 | 111.8 | 127.4 |

Seed 2 is already at RL's budget; its read stays `r08c0`. This addendum spends the rest for seeds 1 and 3.

## Runs

- `yq_oftgbx_mb_s1` resumes run dir `yq_oftgbx_ext_s1b` in place; `yq_oftgbx_mb_s3` resumes `yq_oftgbx_ext_s3` (`RESUME_RUN`, entry `run_vla6.sh`, same plan `yq_oftgbx_ext_s<seed>`, source `rsi_src_v34`). Nothing about the loop changes: same retained version, program, archive, gate rule (guard rail, one candidate a round, no meta-level call) and seed. Seed 1 restarts round 14, seed 3 round 11, from the run's own resume state.
- Cards: 8 per job (rollouts on every card, training on one). If a job is still queued (status Created) 15 minutes after submission, it is stopped while queued and resubmitted with half the cards (8, 4, 2, 1). A job that never left the queue reserved no card and is not counted (addendum 35 rule).
- Stop: the earlier of (a) the seed's counted RL budget (`RUN_TIMEOUT_S` = left card-hours / cards, minus setup) and (b) the cut-off **2026-11-15 20:30Z**, when any job still running is stopped by its exact job id. With 8 cards from about 09:00Z, (b) binds: seed 1 ends near 238 of 241.5 GPU-hours, seed 3 near 207 of 239.2.
- Cost: reserved card-hours (cards × job time, created to finished), as in addendum 35. Cards idle during single-card training are counted.

## Read

- **Version read**: the version each run retains when it stops (last completed round). If unchanged from addendum 35's final (`r13c0`, `r07c0`), those evaluations are reused.
- **Evaluations** (one card each, `--interim`): official test `--replicates 3`; fresh scenes `--fresh-eval` plus `--replicates 2` (three evaluations). Each version kept during the night also gets one fresh evaluation as soon as it appears (cost-curve points; the final evaluation reuses it).
- **M1 (equal GPU-hours)**: loop at RL's budget − tuned RL 36 steps, fresh scenes, seeds 1–3, seed-averaged paired bootstrap. No bar; reported with its CI. Official test reported alongside.
- **M2**: loop at RL's budget − tuned RL 18 steps (the registered tuned RL), fresh scenes; bar +3 as in addendum 35 E2.
- Per seed: the fraction of RL's counted budget the loop has spent.

## Expected

- Seed 1: one to three more rounds kept; fresh 70.6 → 70–72.
- Seed 3: its last three rounds were refused by the gate; most likely zero or one kept; fresh 57–62.
- M1: −1.5 to +0.5 (seed 3 dominates); M2: +3 to +4.5.

Every outcome is reported, including an M1 below zero.

## Amendment 1 (registered 2026-11-15 09:05Z, before any evaluation of this addendum and before the 20:30Z cut-off)

The official paper deadline is 2026-11-16 23:59 AoE (2026-11-17 11:59Z), later than the date the cut-off above was set for. At the PI's request, seed 3 now runs to its full budget, as early as possible:

- **Seed 3 stop**: when its reserved card-hours reach its counted RL budget, 239.2 GPU-hours (36 blocks), not at 20:30Z. Hard cut-off 2026-11-16 18:00Z.
- **Seed 3 cards**: cost is reserved card-hours, so more cards spend the budget sooner. The 4-card job (job-1lvwkiee0ivw) is stopped by its job id and the run resumed in place on 8 cards (`RUN_TIMEOUT_S` = card-hours left / 8, minus setup); the card rule above applies (15 minutes queued, then half). The 4-card job's time counts.
- **Seed 1**: unchanged. It stops at its time limit near 20:20Z at about 237 of 241.5 GPU-hours (98%); the remaining few card-hours cannot complete a round (about 3 h on 8 cards).
- **Interim read (descriptive)**: once seed 1's final evaluations are in, M1/M2 with seed 3's version retained at that time (its `_cc_` evaluation, one fresh evaluation), labelled interim. The **final read** is taken when seed 3 stops; the paper reports the final read.
- Everything else as above.

## Amendment 2 (registered 2026-11-15 09:35Z, before any evaluation of this addendum)

Both 8-card jobs failed within ten minutes for an infrastructure reason (below). To keep one rule for both seeds:

- **Seed 1 stop**: also at its counted RL budget (241.5 GPU-hours), not at 20:30Z; hard cut-off 2026-11-16 18:00Z, as for seed 3.
- **Job resources**: CPU and memory now scale with the cards, 12 CPUs and 100 GiB per card (96 CPUs and 800 GiB on 8 cards), as the one-card jobs had (12 CPUs, 120 GiB).
- Everything else as above and in amendment 1.

## Ops notes

- 08:31:35Z: `yq_oftgbx_mb_s1` submitted on 8 cards (job-uartqxlotifa, `RUN_TIMEOUT_S` 42205); Running within two minutes.
- 08:31:39Z: `yq_oftgbx_mb_s3` submitted on 8 cards (job-0lqny67zmwq5, `RUN_TIMEOUT_S` 42201).
- 08:34:21Z, deviation: job-0lqny67zmwq5 was stopped while still queued after about 3 minutes, not the 15 the card rule above sets (the operator misread the clock). It never left the queue and is not counted. `yq_oftgbx_mb_s3b` was submitted on 4 cards (job-1lvwkiee0ivw, `RUN_TIMEOUT_S` 42036) and was Running at 08:34:42Z, so it was kept rather than returned to the 8-card queue. Training uses one card either way; with 4 cards seed 3 reaches about 160 of its 239.2 GPU-hours by the cut-off (about 207 with 8), so for seed 3 the read is "within RL's budget", not "at" it. Reported as such.
- Seed totals before this addendum, now from `scripts/report/ext_cost_points.py` (job created/finished from DescribeJob): 142.8, 238.1, 111.8 GPU-hours (seed 1 includes its failed 3-card, 3-minute first job).
- 09:01:09Z, amendment 1: job-1lvwkiee0ivw (seed 3, 4 cards, created 08:34:24Z) stopped by its job id (ManualTermination); its 0.45 h × 4 cards count. Seed 3 then stood at 111.8 + 1.78 = 113.6 GPU-hours, 125.6 left. 09:01:13Z: `yq_oftgbx_mb_s3c` submitted on 8 cards (job-hcfqtbwpm2qw, `RUN_TIMEOUT_S` 55629 = 125.6 card-hours / 8 minus setup; hard cut-off 2026-11-16 18:00Z). A watcher applies the 15-minute card rule.
- 09:01:33Z: job-hcfqtbwpm2qw Running on 8 cards (not queued). Seed 3 reaches its budget near 2026-11-16 00:45Z.
- 09:20Z: both 8-card jobs had failed (infrastructure, not the loop): job-uartqxlotifa (seed 1, created 08:31:39Z, finished 08:44:22Z) and job-hcfqtbwpm2qw (seed 3, 09:01:15Z to 09:10:16Z), each with `RuntimeError: parallel_worker_failed` in the parent's gate evaluation of its first resumed round: 40 greedy rollout processes (5 per card) ran with 24 CPUs and 200 GiB (load 50), and two of them died. Their card-hours count: seed 1 at 142.8 + 1.70 = 144.5 GPU-hours (97.0 left), seed 3 at 113.6 + 1.20 = 114.8 (124.4 left). Resubmitted with `RESUME_RUN` under amendment 2.
- 09:19:28Z: `yq_oftgbx_mb_s1b` (seed 1, 8 cards, 96 CPUs, 800 GiB; job-lni873lelr1q, `RUN_TIMEOUT_S` 42750) Running at 09:19:47Z. 09:19:30Z: `yq_oftgbx_mb_s3d` (seed 3, 8 cards; job-v3npseqnfxuk) stayed queued for 15 minutes and was stopped while queued (not counted); `yq_oftgbx_mb_s3q4` (seed 3, 4 cards, 48 CPUs, 400 GiB; job-eg59nsypucaz, `RUN_TIMEOUT_S` from 124.4 card-hours / 4) Running from about 09:35Z. When seed 1 reaches its budget (about 21:30Z) and frees its node, seed 3 is moved to 8 cards under amendment 1 (stopped by job id, resumed in place; its 4-card time counts).
- 13:18Z: real-time logs carry training receipts only (the per-round accepted/refused lines are printed when a job ends), so each finished candidate is evaluated once on fresh scenes as soon as its `RECEIPT ckpt-rNNc0` appears; a candidate the gate refused is recorded but not read. Seed 1 `r14c0`: `yq_oftgbx_mb_s1_cc_r14c0` submitted.
- 14:45Z: seed 3 `r11c0` trained; `yq_oftgbx_mb_s3_cc_r11c0` submitted (one fresh evaluation; read only if the gate kept it).
- 15:24Z: `yq_oftgbx_mb_s3_cc_r11c0` (submitted while round 11's gate was still running) and its retry `_b` after round 12 had started both stopped with `interim_node_is_not_an_accepted_version`: seed 3's round-11 candidate was refused by the gate; seed 3 still retains `r07c0`. Seed 1's `r14c0` evaluation ran, so round 14 was kept.
- 16:22Z: seed 1 `r15c0` trained; `yq_oftgbx_mb_s1_cc_r15c0` submitted after round 15's gate finished (it runs only if the gate kept r15c0).
- 16:44Z: `yq_oftgbx_mb_s1_cc_r15c0` passed the accepted-version check and is evaluating: seed 1 kept round 15 (r14c0, r15c0 kept so far under this addendum).
- 19:23Z: seed 3 `r12c0` trained; `yq_oftgbx_mb_s3_cc_r12c0` submitted after round 12's gate finished (it runs only if the gate kept r12c0).
- 19:44Z: `yq_oftgbx_mb_s3_cc_r12c0` (submitted after round 12's gate) stopped with `interim_node_is_not_an_accepted_version`: seed 3's round-12 candidate was refused; seed 3 still retains `r07c0`.
- 19:44Z: seed 1 `r16c0` trained; `yq_oftgbx_mb_s1_cc_r16c0` submitted after round 16's gate finished.
- 20:14Z: `yq_oftgbx_mb_s1_cc_r16c0` passed the accepted-version check and is evaluating: seed 1 kept round 16 (rounds 14, 15, 16 kept under this addendum).
- 21:21:34Z: seed 1 (job-lni873lelr1q) reached its budget (`RUN_TIMEOUT_S`, rc 124). Its last accepted round is 16, so its final version is **`r16c0`** (rounds 14, 15, 16 kept, none refused under this addendum). Total: 144.5 + 8 × 12.03 h = **240.8 of 241.5 GPU-hours** (99.7%). Final evaluations of `r16c0` submitted 21:48Z: `yq_oftgbx_mb_s1_fin_fresh` (job-5gym2s4ii12v), `_fresh23` (job-ml012s4rea5c), `_fin_rep` (job-c16fft5jx55w).
- 21:47:32Z, amendment 1: seed 3's 4-card job (job-eg59nsypucaz, from 09:34:55Z; 48.84 card-hours) stopped by its job id to move to the 8 cards seed 1 freed; seed 3 at 163.6 GPU-hours, 75.6 left; still retaining `r07c0` (rounds 11 and 12 refused). 21:47:53Z: `yq_oftgbx_mb_s3e` on 8 cards (job-tqf4ti2mpfus, `RUN_TIMEOUT_S` 33102), submitted before seed 1's single-card evaluations so the freed node is not split. Costs in `results/mb_costs_20261116.json`.
- 2026-11-15 23:45Z, **interim read (descriptive, amendment 1)**, `results/addendum38_interim_20261116.json`: seed 1 at its budget (`r16c0`, 240.8 GPU-hours), seed 2 `r08c0` (238.1), seed 3 at the version it retains now (`r07c0`; still running, 163.6 so far). Fresh scenes, one evaluation per version: M1 (− RL 36 blocks) −0.73 [−2.40, +0.93]; M2 (− RL 18 blocks) **+4.23 [+2.43, +6.03]** (above +3). Three evaluations per version: M1 −1.19 [−2.52, +0.13], M2 +3.79 [+2.33, +5.28]. Official test: M1 −0.00 [−2.11, +2.09], M2 +1.80 [−0.36, +3.98]. Per seed, fresh, against RL 18 blocks: seed 1 72.9 vs 60.0 (+12.9) at 240.8 vs 229.1 GPU-hours (5% more); seed 2 66.7 vs 62.2 (+4.5) at 238.1 vs 230.3 (3% more). Against RL 36 blocks at equal GPU-hours: seed 1 +6.1 (240.8 vs 241.5), seed 2 +1.2 (238.1 vs 238.8). The final read follows when seed 3 reaches its budget.
- 01:12Z: seed 3 `r13c0` trained; `yq_oftgbx_mb_s3_cc_r13c0` submitted after round 13's gate (it runs only if the gate kept r13c0).
- 01:22Z: `yq_oftgbx_mb_s3_cc_r13c0` passed the accepted-version check and is evaluating: seed 3 kept round 13 (its first kept round since round 7; rounds 8-12 were refused).

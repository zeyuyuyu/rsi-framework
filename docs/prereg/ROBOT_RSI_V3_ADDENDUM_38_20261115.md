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

## Ops notes

# New figure for Finding 6: success against total GPU-hours, RL's tuning counted

Purpose: show at a glance that, once RL is charged the 213.4 GPU-hours of pilots that chose its recipe, the RSI loop
reaches tuned RL's success at a fraction of RL's total cost (LIBERO-Goal). Registered in addendum 36
(`docs/prereg/ROBOT_RSI_V3_ADDENDUM_36_20261114.md`).

- **x**: cumulative GPU-hours, RL's pilots included (0 to about 260).
- **y**: success on the 1,000 unseen LIBERO-Goal scenes (%), one evaluation per point.
- **Series** (mean of seeds 1-3 bold, each seed thin; seed 0 on the second platform as hollow markers if shown):
  - *RSI loop* (self-repairing loop, LLM meta level from the failing recipe): rounds 0-6 at the run's own cumulative cost (starts at x = 0, ends near 59-206 GPU-hours, mean 118). Later points from the continued runs (addendum 35) are added when read.
  - *Tuned RL, 36 blocks*: starts at x = 213.4 at the initial policy's success, points after blocks 6, 12, 18, 24, 30, 36.
  - *Tuned RL, 18 blocks*: its registered end point (x ≈ 230).
  - Start level (60.0%) as a grey dashed line.
- Size: one column (3.3 in), possibly with a broken x axis between about 0-120 and 200-260 if the gap wastes space.
- Data: `data/cost_curve.csv` (from `results/cost_curve_read_20261114.json`, read 2026-11-14). Columns: series, seed, x_gpu_hours, success_pct, version. Seed 0 (second platform) has no 36-block RL run; draw seeds 1-3. A first version is drawn by `make_figs.py` as `paper/cvpr2027/fig/fig_cost.pdf`. The continued loop (addendum 35) adds points near 190-240 GPU-hours when it is read (interim 11-14 night, final 11-15).
- Status: all points in (2026-11-14 18:23 Beijing).

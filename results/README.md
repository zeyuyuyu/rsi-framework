# RSI run records

Small, human-readable records of every run; model checkpoints and raw attempts stay on the servers
(`/data0/home/zeyuwang/rsi/runs2/` on the A800, `/mnt/pfs/shitianyu-rsi/runs/` on Baidu AIHC).

| path | content |
| --- | --- |
| `a800/runs2/<run>/plan.json` | frozen configuration, gate/audit/test ids |
| `a800/runs2/<run>/archive.jsonl` | every candidate node: program, gate score, curation and signal stats, receipt; `event: accepted` lines mark acceptance |
| `a800/runs2/<run>/accepted.jsonl`, `round-NN.json` | per-round decisions |
| `a800/runs2/<run>/report.json`, `test-<suite>-<node>.jsonl` | sealed test results (only after the last round) |
| `a800/runs2/<run>/ckpt-*/receipt.json` | training receipts (parent, steps, parameter digests) |
| `a800/runs_dev_v1/` | development runs of the earlier single-level loop (excluded from claims) |
| `a800/plans2/` | plan files as launched |

Run names: `main_q15_<arm>_s<seed>` = Qwen2.5-Coder-1.5B, arm in {fixed, nonrec, shuffled, full};
`p2_*` / `pilot_*` = development pilots; `base_*` = baseline-only evaluations; `vla_*` = OpenVLA.

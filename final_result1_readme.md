# Final results: Goal 完整 RSI 与普通 RL 的效果—算力对比

核对日期：2026-11-16。本文件整理已完成的 LIBERO-Goal 实验

## 1. 这些数据支持什么结论

**计入一次配方搜索成本后，LLM 自修复 RSI 以约一半总成本取得接近调优 RL 的 Official 成功率；相较 RL-18，Fresh 成功率更高。**

- 相比 RL-18：RSI 的总成本约为 51%，Official 成功率均值高 0.67 个百分点，Fresh 高 2.20 个百分点。
- 相比 RL-36：RSI 的总成本约为 49%，Official 成功率均值低 1.13 个百分点，Fresh 低 2.78 个百分点。这是效果与成本的取舍。
- 不计配方搜索时，RSI 本次运行更贵。因此结果支持“计入配方搜索的成本—效果优势”，不支持“RSI 单次训练更便宜”或“RSI 在所有测试上优于 RL”。
- “接近”描述均值，不等同于统计等效或已通过非劣检验。这里的差值不作为新显著性声明。

RL 总成本计入 213.4 GPU-hours 的配方搜索投入；这是一次性投入，复用配方时应按使用场景摊销。RSI 从失败的 BC 配方开始自动修改程序，而 RL 使用调优配方；因此这不是相同初始训练配方的单组件消融。

## 2. 最终结果总表

成功率单位为 %，差值单位为百分点（pp）。每个运行先平均可用的重复评测，再对 seed 1–3 等权平均。成本为每个运行的种子均值；不是三种子项目总支出。

| 方法 | 外层轮数 × 每轮候选 × inner steps | Official | Fresh | 运行成本 GPU-h | 含配方搜索总成本 GPU-h |
|---|---|---:|---:|---:|---:|
| 完整 RSI：LLM 自修复 | 6 × 2 × 3 | 59.78 | 63.58 | 118.1 | 118.1 |
| 调优 RL-18（retained） | 1 × 1 × 18 | 59.11 | 61.38 | 16.5 | 229.9 |
| 调优 RL-36（retained） | 1 × 1 × 36 | 60.91 | 66.36 | 26.2 | 239.6 |

36 个 inner-update blocks 不是 36 个梯度步，也不保证相同训练工作量：RSI 的元层可以修改每次更新的 steps、batch、采样量和算法。

## 3. 逐种子最终结果及原始入口

Official 每次 500 episodes；Fresh 每次 1,000 episodes。下表评测次数来自实际原始文件；Official 与 Fresh 独立汇总，不合并成单一分数。所有最终效果使用 retained 策略。

| 方法 | Seed | Retained | Official % | Official 评测数 | Fresh % | Fresh 评测数 | 运行 GPU-h | 原始 report | 最终参数 |
|---|---:|---|---:|---:|---:|---:|---:|---|---|
| LLM RSI | 1 | r05c1 | 60.13 | 3 | 63.80 | 3 | 89.6 | [report](results/baidu/yq_oftgb_llm_harness_s1/report.json) | [retained](results/baidu/yq_oftgb_llm_harness_s1/retained.json) |
| LLM RSI | 2 | r06c0 | 61.27 | 3 | 65.03 | 3 | 206.0 | [report](results/baidu/yq_oftgb_llm_harness_s2/report.json) | [retained](results/baidu/yq_oftgb_llm_harness_s2/retained.json) |
| LLM RSI | 3 | r06c1 | 57.93 | 3 | 61.90 | 3 | 58.8 | [report](results/baidu/yq_oftgb_llm_harness_s3/report.json) | [retained](results/baidu/yq_oftgb_llm_harness_s3/retained.json) |
| RL-18 | 1 | n0 | 58.80 | 1 | 59.80 | 3 | 15.7 | [report](results/baidu/yq_oftg_onebig_s1/report.json) | [retained](results/baidu/yq_oftg_onebig_s1/retained.json) |
| RL-18 | 2 | r01c0 | 59.00 | 3 | 62.67 | 3 | 16.9 | [report](results/baidu/yq_oftg_onebig_s2/report.json) | [retained](results/baidu/yq_oftg_onebig_s2/retained.json) |
| RL-18 | 3 | r01c0 | 59.53 | 3 | 61.67 | 3 | 16.8 | [report](results/baidu/yq_oftg_onebig_s3/report.json) | [retained](results/baidu/yq_oftg_onebig_s3/retained.json) |
| RL-36 | 1 | r01c0 | 58.60 | 3 | 66.77 | 3 | 27.8 | [report](results/baidu/yq_oftg_onebig12_s1/report.json) | [retained](results/baidu/yq_oftg_onebig12_s1/retained.json) |
| RL-36 | 2 | r01c0 | 60.87 | 3 | 66.43 | 3 | 25.2 | [report](results/baidu/yq_oftg_onebig12_s2/report.json) | [retained](results/baidu/yq_oftg_onebig12_s2/retained.json) |
| RL-36 | 3 | r01c0 | 63.27 | 3 | 65.87 | 3 | 25.6 | [report](results/baidu/yq_oftg_onebig12_s3/report.json) | [retained](results/baidu/yq_oftg_onebig12_s3/retained.json) |

## 4. 实验参数：完整 RSI 指什么

完整 RSI 在本文件中特指 `yq_oftgb_llm_harness_s1–s3`，不是 fixed12、numeric full 或 Spatial meta3。

| 设置 | 值 |
|---|---|
| 初始策略 | `oft-sft-libero-goal-traj1` / OpenVLA-OFT Goal SFT |
| Recursion | 开启 |
| Gate | `fresh_paired`，`min_gate_gain=0.0` |
| Meta | LLM harness，每轮当前程序与一个新程序候选；`meta_v2=false` 不等于关闭元层 |
| 外层轮数 | 6 |
| 每轮候选 | 2 |
| 每候选 inner steps | 3 |
| 种子 | 1、2、3 |

初始配方：BC；lr=1e-5；update.steps=100；batch=64；64 cases；每 case 8 次采样；temperature=1.6；verified 数据筛选。元层修改这些配方参数，因此不同种子终态不同。

| 最终保留程序参数 | Seed 1 | Seed 2 | Seed 3 |
|---|---:|---:|---:|
| operator | GRPO | GRPO | BC |
| lr | 5e-5 | 2e-5 | 2e-5 |
| update.steps | 200 | 400 | 200 |
| batch | 128 | 128 | 64 |
| cases | 128 | 192 | 200 |
| samples | 12 | 12 | 16 |
| temperature | 1.2 | 1.0 | 1.3 |

配置来源：

- [BC 自修复三种方法的生成配置](scripts/baidu/mkplans_bcstart.py)：`fixed`、numeric `full`、`llm_harness`。
- [RL 与 LLM harness 的基础配置](scripts/baidu/mkplans_vla.py)：`yq_long12`、`yq_more` 等分支及模型/元层设置。
- 每个运行 [report.json](results/baidu/yq_oftgb_llm_harness_s1/report.json) 的 `config` 是运行实录；最终配方见上表各 `retained.json`，逐轮接受结果见 `accepted.jsonl` / `round-*.json`。

## 5. 画图可用的数据

| 面板 | 内容 | 取数方式 |
|---|---|---|
| A | Official 最终成功率 vs GPU-hours | 第 3 节三组逐种子数据，分别画单种子点和均值 |
| B | Fresh 最终成功率 vs GPU-hours | 同三组，各自 Fresh 最终重复评测均值 |
| C | Fresh 随累计 GPU-hours 的曲线 | RSI 逐轮、RL-36 每 6 blocks；RL-18 以最终结果点为主 |

- A/B 的横轴可分别展示运行成本与含配方搜索成本，图例明确是否含 pilots。
- C 的每个中间版本通常只有一次 Fresh 评测；不把它当成最终三次评测均值。
- RL-18 曲线中的 `r01c0 (ungated)` 与最终 retained 是不同版本口径，不能混用。用于 A/B 时统一取 retained。
- 达到同等效果所需成本：使用共同 Fresh 阈值的第一次观测达到点；未达到保持缺失，不外推，也不把缺失填 0。
- 推荐图名：**Performance versus compute, including recipe-search cost**。

## 6. 成本与统计来源

| 来源 | 内容 |
|---|---|
| [作业 session 账务](results/yq_selfrepair_job_sessions_20261113.json) | RSI 各 session 卡数、created/finished 时间；失败与恢复记录 |
| [成本汇总](results/tuning_cost_20261112.json) | `meta_level_card_hours`、`wall_clock_hours`、`pilots`；21 个 pilot、18 个有计时 |
| [成本读取代码](scripts/report/tuning_cost_read.py) | 运行耗时、session 成本、pilot 总成本计算与比较 |
| [Fresh 算力曲线读取代码](scripts/report/cost_curve_read.py) | 原始测试点、累计成本分配、最终重复评测的读取 |
| [已有曲线结果](results/cost_curve_read_20261114.json) | `partA` 为曲线，`partB` 为重复评测比较；不是原始 episode 文件 |
| [Official 读取代码](scripts/report/goal_read.py) | retained 节点与重复评测读取 |
| [Fresh 读取代码](scripts/report/fresh_read.py) | 测试场景、对齐与配对统计 |

Fresh 三种子、三次评测的已完成比较在 `cost_curve_read_20261114.json → partB → three_evaluations_s123`：LLM RSI − RL18 = +2.20 pp，repo 的配对 bootstrap 95% CI 为 [+0.86, +3.53]。该区间只对应 Fresh 的这一比较，不能移用于 Official、RL36 或不同种子集合。

## 7. 如何定位原始文件

每个运行主目录有 `report.json`（配置与结果）、`tests.txt`（逐 episode TESTBITS）、`retained.json`（最终参数）、`round-*.json`（逐轮记录）、`backend-accounting.json`（后端计时）。`SOURCE-*.txt` 记录同步来源。主目录后缀 `_rep` 对应 Official 追加评测，`_fresh` 对应首次 Fresh，`_fresh23` 对应后两次 Fresh，`_cc_*` 对应曲线中间版本。`test_eval.json` 中可核对实际 checkpoint 路径和节点。

以下链接全部相对于 repo 根目录，便于本地或 GitHub 浏览。

## yq_oftgb_llm_harness_s1
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-resume11062008.job-ws2moqr8twkc.txt](results/baidu/yq_oftgb_llm_harness_s1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-resume11062008.job-ws2moqr8twkc.txt)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s1/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s1/backend-accounting.json)
- [report.json](results/baidu/yq_oftgb_llm_harness_s1/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s1/retained.json)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s1/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s1/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s1/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s1/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s1/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s1/round-06.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s1/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-rep.job-o6tmk3rvxhh2.txt](results/baidu/yq_oftgb_llm_harness_s1_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-rep.job-o6tmk3rvxhh2.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s1_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh.job-fm7yr1g2pvwi.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh.job-fm7yr1g2pvwi.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh23.job-tzrsxtssryg6.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh23/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh23.job-tzrsxtssryg6.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh23/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r01c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r01c1.job-cizuj7m3h087.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r01c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r01c1.job-cizuj7m3h087.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r01c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_cc_r01c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r01c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r01c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r02c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r02c1.job-rnakw292b05e.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r02c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r02c1.job-rnakw292b05e.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r02c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_cc_r02c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r02c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r02c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r03c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r03c0.job-frbg2ookx5os.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r03c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r03c0.job-frbg2ookx5os.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r03c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_cc_r03c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r03c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r03c0/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r04c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r04c0.job-fzmlzqernnsr.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r04c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-cc-r04c0.job-fzmlzqernnsr.txt)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r04c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_cc_r04c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s1_cc_r04c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_cc_r04c0/tests.txt)

## yq_oftgb_llm_harness_s2
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-resume11071339.job-y5zz0zgbmago.txt](results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-resume11071339.job-y5zz0zgbmago.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s2.job-ov65gen3qlvu.txt](results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2.job-ov65gen3qlvu.txt)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s2/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s2/backend-accounting.json)
- [report.json](results/baidu/yq_oftgb_llm_harness_s2/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s2/retained.json)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s2/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s2/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s2/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s2/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s2/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s2/round-06.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s2/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-rep.job-dkiw8x1wej66.txt](results/baidu/yq_oftgb_llm_harness_s2_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-rep.job-dkiw8x1wej66.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s2_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh.job-3ac3xqab75k1.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh.job-3ac3xqab75k1.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh23.job-7mq3cskxna1w.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh23/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh23.job-7mq3cskxna1w.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh23/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r01c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r01c1.job-qyrnr6oou7z2.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r01c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r01c1.job-qyrnr6oou7z2.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r01c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_cc_r01c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r01c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r01c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r02c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r02c1.job-z4l945be2sns.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r02c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r02c1.job-z4l945be2sns.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r02c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_cc_r02c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r02c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r02c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r03c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r03c1.job-qxhbaaoef7jh.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r03c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r03c1.job-qxhbaaoef7jh.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r03c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_cc_r03c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r03c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r03c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r04c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r04c1.job-uuw4fessb5i6.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r04c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r04c1.job-uuw4fessb5i6.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r04c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_cc_r04c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r04c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r04c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r05c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r05c0.job-oancqf3434pr.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r05c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-cc-r05c0.job-oancqf3434pr.txt)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r05c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_cc_r05c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s2_cc_r05c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_cc_r05c0/tests.txt)

## yq_oftgb_llm_harness_s3
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-resume11062008.job-fatymmgiuz4d.txt](results/baidu/yq_oftgb_llm_harness_s3/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-resume11062008.job-fatymmgiuz4d.txt)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s3/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s3/backend-accounting.json)
- [report.json](results/baidu/yq_oftgb_llm_harness_s3/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s3/retained.json)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s3/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s3/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s3/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s3/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s3/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s3/round-06.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s3/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-rep.job-4ta75jhcfe5y.txt](results/baidu/yq_oftgb_llm_harness_s3_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-rep.job-4ta75jhcfe5y.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s3_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh.job-cl49jmi7e512.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh.job-cl49jmi7e512.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh23.job-at82gn1mwnx6.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh23/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh23.job-at82gn1mwnx6.txt)
- [test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh23/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r01c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r01c0.job-3oca1z3e2eud.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r01c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r01c0.job-3oca1z3e2eud.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r01c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_cc_r01c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r01c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r01c0/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r03c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r03c0.job-0w12vgxbka5e.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r03c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r03c0.job-0w12vgxbka5e.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r03c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_cc_r03c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r03c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r03c0/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r04c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r04c1.job-ln7k6ehbizfr.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r04c1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r04c1.job-ln7k6ehbizfr.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r04c1/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_cc_r04c1/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r04c1/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r04c1/tests.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r05c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r05c0.job-lc7aizf9ma94.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r05c0/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-cc-r05c0.job-lc7aizf9ma94.txt)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r05c0/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_cc_r05c0/test_eval.json)
- 曲线：[yq_oftgb_llm_harness_s3_cc_r05c0/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_cc_r05c0/tests.txt)

## yq_oftg_onebig_s1
- [SOURCE-zw-rsi-yq-oftg-onebig-s1.txt](results/baidu/yq_oftg_onebig_s1/SOURCE-zw-rsi-yq-oftg-onebig-s1.txt)
- [backend-accounting.json](results/baidu/yq_oftg_onebig_s1/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig_s1/report.json)
- [retained.json](results/baidu/yq_oftg_onebig_s1/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig_s1/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s1/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s1-fresh.job-scldqgfzdnp2.txt](results/baidu/yq_oftg_onebig_s1_fresh/SOURCE-zw-rsi-yq-oftg-onebig-s1-fresh.job-scldqgfzdnp2.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s1_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s1_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s1-fresh23.job-4y31gqkei13g.txt](results/baidu/yq_oftg_onebig_s1_fresh23/SOURCE-zw-rsi-yq-oftg-onebig-s1-fresh23.job-4y31gqkei13g.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s1_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s1_fresh23/tests.txt)
- 曲线：[yq_oftg_onebig_s1_cc_r01c0/SOURCE-zw-rsi-yq-oftg-onebig-s1-cc-r01c0.job-q9u24773refg.txt](results/baidu/yq_oftg_onebig_s1_cc_r01c0/SOURCE-zw-rsi-yq-oftg-onebig-s1-cc-r01c0.job-q9u24773refg.txt)
- 曲线：[yq_oftg_onebig_s1_cc_r01c0/test_eval.json](results/baidu/yq_oftg_onebig_s1_cc_r01c0/test_eval.json)
- 曲线：[yq_oftg_onebig_s1_cc_r01c0/tests.txt](results/baidu/yq_oftg_onebig_s1_cc_r01c0/tests.txt)

## yq_oftg_onebig_s2
- [SOURCE-zw-rsi-yq-oftg-onebig-s2.txt](results/baidu/yq_oftg_onebig_s2/SOURCE-zw-rsi-yq-oftg-onebig-s2.txt)
- [accepted.jsonl](results/baidu/yq_oftg_onebig_s2/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftg_onebig_s2/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig_s2/report.json)
- [retained.json](results/baidu/yq_oftg_onebig_s2/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig_s2/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s2/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s2-rep.job-dvuaublsexpg.txt](results/baidu/yq_oftg_onebig_s2_rep/SOURCE-zw-rsi-yq-oftg-onebig-s2-rep.job-dvuaublsexpg.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s2_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s2_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s2-fresh.job-vsb3k0e85ubg.txt](results/baidu/yq_oftg_onebig_s2_fresh/SOURCE-zw-rsi-yq-oftg-onebig-s2-fresh.job-vsb3k0e85ubg.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s2_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s2_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s2-fresh23.job-ujxpnmfkxpsg.txt](results/baidu/yq_oftg_onebig_s2_fresh23/SOURCE-zw-rsi-yq-oftg-onebig-s2-fresh23.job-ujxpnmfkxpsg.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s2_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s2_fresh23/tests.txt)

## yq_oftg_onebig_s3
- [SOURCE-zw-rsi-yq-oftg-onebig-s3.txt](results/baidu/yq_oftg_onebig_s3/SOURCE-zw-rsi-yq-oftg-onebig-s3.txt)
- [accepted.jsonl](results/baidu/yq_oftg_onebig_s3/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftg_onebig_s3/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig_s3/report.json)
- [retained.json](results/baidu/yq_oftg_onebig_s3/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig_s3/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s3/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s3-rep.job-zijzx28ncuz7.txt](results/baidu/yq_oftg_onebig_s3_rep/SOURCE-zw-rsi-yq-oftg-onebig-s3-rep.job-zijzx28ncuz7.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s3_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s3_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s3-fresh.job-asznq9am3joy.txt](results/baidu/yq_oftg_onebig_s3_fresh/SOURCE-zw-rsi-yq-oftg-onebig-s3-fresh.job-asznq9am3joy.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s3_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s3_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig-s3-fresh23.job-u43nqvn3lxqg.txt](results/baidu/yq_oftg_onebig_s3_fresh23/SOURCE-zw-rsi-yq-oftg-onebig-s3-fresh23.job-u43nqvn3lxqg.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig_s3_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig_s3_fresh23/tests.txt)

## yq_oftg_onebig12_s1
- [SOURCE-zw-rsi-yq-oftg-onebig12-s1.job-sau7s8j6zssi.txt](results/baidu/yq_oftg_onebig12_s1/SOURCE-zw-rsi-yq-oftg-onebig12-s1.job-sau7s8j6zssi.txt)
- [accepted.jsonl](results/baidu/yq_oftg_onebig12_s1/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftg_onebig12_s1/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig12_s1/report.json)
- [retained.json](results/baidu/yq_oftg_onebig12_s1/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig12_s1/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s1/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s1-rep.job-ni703lbgsikj.txt](results/baidu/yq_oftg_onebig12_s1_rep/SOURCE-zw-rsi-yq-oftg-onebig12-s1-rep.job-ni703lbgsikj.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s1_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s1_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s1-fresh.job-2077tupe404q.txt](results/baidu/yq_oftg_onebig12_s1_fresh/SOURCE-zw-rsi-yq-oftg-onebig12-s1-fresh.job-2077tupe404q.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s1_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s1_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s1-fresh23.job-ezcyswf66uun.txt](results/baidu/yq_oftg_onebig12_s1_fresh23/SOURCE-zw-rsi-yq-oftg-onebig12-s1-fresh23.job-ezcyswf66uun.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s1_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s1_fresh23/tests.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i11.job-2pno3d7j7ffx.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i11.job-2pno3d7j7ffx.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i11/test_eval.json](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i11/test_eval.json)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i11/tests.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i11/tests.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i17.job-00g0bis3rzf5.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i17.job-00g0bis3rzf5.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i17/test_eval.json](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i17/test_eval.json)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i17/tests.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i17/tests.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i23.job-aiec0u4duum5.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i23.job-aiec0u4duum5.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i23/test_eval.json](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i23/test_eval.json)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i23/tests.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i23/tests.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i29.job-9umcgm289zz5.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i29.job-9umcgm289zz5.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i29/test_eval.json](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i29/test_eval.json)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i29/tests.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i29/tests.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i5.job-dsx1ctvv2k2a.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s1-cc-r01c0-i5.job-dsx1ctvv2k2a.txt)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i5/test_eval.json](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i5/test_eval.json)
- 曲线：[yq_oftg_onebig12_s1_cc_r01c0-i5/tests.txt](results/baidu/yq_oftg_onebig12_s1_cc_r01c0-i5/tests.txt)

## yq_oftg_onebig12_s2
- [SOURCE-zw-rsi-yq-oftg-onebig12-s2.job-gmg9ymfu2iwu.txt](results/baidu/yq_oftg_onebig12_s2/SOURCE-zw-rsi-yq-oftg-onebig12-s2.job-gmg9ymfu2iwu.txt)
- [accepted.jsonl](results/baidu/yq_oftg_onebig12_s2/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftg_onebig12_s2/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig12_s2/report.json)
- [retained.json](results/baidu/yq_oftg_onebig12_s2/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig12_s2/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s2/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s2-rep.job-f4ubreks7gmc.txt](results/baidu/yq_oftg_onebig12_s2_rep/SOURCE-zw-rsi-yq-oftg-onebig12-s2-rep.job-f4ubreks7gmc.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s2_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s2_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s2-fresh.job-7w7ipvrf4buc.txt](results/baidu/yq_oftg_onebig12_s2_fresh/SOURCE-zw-rsi-yq-oftg-onebig12-s2-fresh.job-7w7ipvrf4buc.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s2_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s2_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s2-fresh23.job-fxzvncuw2m71.txt](results/baidu/yq_oftg_onebig12_s2_fresh23/SOURCE-zw-rsi-yq-oftg-onebig12-s2-fresh23.job-fxzvncuw2m71.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s2_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s2_fresh23/tests.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i11.job-77c414xnkvqe.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i11.job-77c414xnkvqe.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i11/test_eval.json](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i11/test_eval.json)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i11/tests.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i11/tests.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i17.job-i3c2r793ozol.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i17.job-i3c2r793ozol.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i17/test_eval.json](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i17/test_eval.json)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i17/tests.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i17/tests.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i23.job-w9z6t8ci6bk1.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i23.job-w9z6t8ci6bk1.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i23/test_eval.json](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i23/test_eval.json)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i23/tests.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i23/tests.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i29.job-2wl6gx03e9cs.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i29.job-2wl6gx03e9cs.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i29/test_eval.json](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i29/test_eval.json)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i29/tests.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i29/tests.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i5.job-tvomnfi6vkkv.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s2-cc-r01c0-i5.job-tvomnfi6vkkv.txt)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i5/test_eval.json](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i5/test_eval.json)
- 曲线：[yq_oftg_onebig12_s2_cc_r01c0-i5/tests.txt](results/baidu/yq_oftg_onebig12_s2_cc_r01c0-i5/tests.txt)

## yq_oftg_onebig12_s3
- [SOURCE-zw-rsi-yq-oftg-onebig12-s3.job-l2u2yr2awm0o.txt](results/baidu/yq_oftg_onebig12_s3/SOURCE-zw-rsi-yq-oftg-onebig12-s3.job-l2u2yr2awm0o.txt)
- [accepted.jsonl](results/baidu/yq_oftg_onebig12_s3/accepted.jsonl)
- [backend-accounting.json](results/baidu/yq_oftg_onebig12_s3/backend-accounting.json)
- [report.json](results/baidu/yq_oftg_onebig12_s3/report.json)
- [retained.json](results/baidu/yq_oftg_onebig12_s3/retained.json)
- [round-01.json](results/baidu/yq_oftg_onebig12_s3/round-01.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s3/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s3-rep.job-mqzq4l5g0ma5.txt](results/baidu/yq_oftg_onebig12_s3_rep/SOURCE-zw-rsi-yq-oftg-onebig12-s3-rep.job-mqzq4l5g0ma5.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s3_rep/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s3_rep/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s3-fresh.job-7814685ad13d.txt](results/baidu/yq_oftg_onebig12_s3_fresh/SOURCE-zw-rsi-yq-oftg-onebig12-s3-fresh.job-7814685ad13d.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s3_fresh/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s3_fresh/tests.txt)
- [SOURCE-zw-rsi-yq-oftg-onebig12-s3-fresh23.job-fmjfsu6xdxc5.txt](results/baidu/yq_oftg_onebig12_s3_fresh23/SOURCE-zw-rsi-yq-oftg-onebig12-s3-fresh23.job-fmjfsu6xdxc5.txt)
- [test_eval.json](results/baidu/yq_oftg_onebig12_s3_fresh23/test_eval.json)
- [tests.txt](results/baidu/yq_oftg_onebig12_s3_fresh23/tests.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i11.job-fo0xmf6war8j.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i11/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i11.job-fo0xmf6war8j.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i11/test_eval.json](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i11/test_eval.json)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i11/tests.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i11/tests.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i17.job-bhflrv7ghbv8.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i17/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i17.job-bhflrv7ghbv8.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i17/test_eval.json](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i17/test_eval.json)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i17/tests.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i17/tests.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i23.job-974ecrgnvhud.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i23/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i23.job-974ecrgnvhud.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i23/test_eval.json](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i23/test_eval.json)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i23/tests.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i23/tests.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i29.job-0pdoxsl0ohtx.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i29/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i29.job-0pdoxsl0ohtx.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i29/test_eval.json](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i29/test_eval.json)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i29/tests.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i29/tests.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i5.job-3cilbnd2adaa.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i5/SOURCE-zw-rsi-yq-oftg-onebig12-s3-cc-r01c0-i5.job-3cilbnd2adaa.txt)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i5/test_eval.json](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i5/test_eval.json)
- 曲线：[yq_oftg_onebig12_s3_cc_r01c0-i5/tests.txt](results/baidu/yq_oftg_onebig12_s3_cc_r01c0-i5/tests.txt)

## 配置、成本账务与计算脚本
- [scripts/baidu/mkplans_bcstart.py](scripts/baidu/mkplans_bcstart.py)
- [scripts/baidu/mkplans_vla.py](scripts/baidu/mkplans_vla.py)
- [results/yq_selfrepair_job_sessions_20261113.json](results/yq_selfrepair_job_sessions_20261113.json)
- [results/tuning_cost_20261112.json](results/tuning_cost_20261112.json)
- [results/cost_curve_read_20261114.json](results/cost_curve_read_20261114.json)
- [scripts/report/tuning_cost_read.py](scripts/report/tuning_cost_read.py)
- [scripts/report/cost_curve_read.py](scripts/report/cost_curve_read.py)
- [scripts/report/goal_read.py](scripts/report/goal_read.py)
- [scripts/report/fresh_read.py](scripts/report/fresh_read.py)

## 213.4 GPU-hours 调参成本：各pilot原始记录

以下来自成本清单；缺失计时必须保留，不能填0。

### bj_oft3_pilot2_l10_lr1e4；计时=4.1 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot2-l10-lr1e4.txt](results/baidu/bj_oft3_pilot2_l10_lr1e4/SOURCE-zw-rsi-bj-oft3-pilot2-l10-lr1e4.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot2_l10_lr1e4/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot2_l10_lr1e4/report.json)

### bj_oft3_pilot2_l10_lr5e5；计时=3.9 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot2-l10-lr5e5.txt](results/baidu/bj_oft3_pilot2_l10_lr5e5/SOURCE-zw-rsi-bj-oft3-pilot2-l10-lr5e5.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot2_l10_lr5e5/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot2_l10_lr5e5/report.json)

### bj_oft3_pilot3_l10_s1000；计时=3.3 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot3-l10-s1000.txt](results/baidu/bj_oft3_pilot3_l10_s1000/SOURCE-zw-rsi-bj-oft3-pilot3-l10-s1000.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot3_l10_s1000/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot3_l10_s1000/report.json)

### bj_oft3_pilot3_l10_s400；计时=2.5 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot3-l10-s400.txt](results/baidu/bj_oft3_pilot3_l10_s400/SOURCE-zw-rsi-bj-oft3-pilot3-l10-s400.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot3_l10_s400/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot3_l10_s400/report.json)

### bj_oft3_pilot5_curve；计时=15.5 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot5-curve.txt](results/baidu/bj_oft3_pilot5_curve/SOURCE-zw-rsi-bj-oft3-pilot5-curve.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot5_curve/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot5_curve/report.json)

### bj_oft3_pilot7_lr3e5；计时=15.2 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot7-lr3e5.txt](results/baidu/bj_oft3_pilot7_lr3e5/SOURCE-zw-rsi-bj-oft3-pilot7-lr3e5.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot7_lr3e5/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot7_lr3e5/report.json)

### bj_oft3_pilot7_lr3e5_ep；计时=15.1 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot7-lr3e5-ep.txt](results/baidu/bj_oft3_pilot7_lr3e5_ep/SOURCE-zw-rsi-bj-oft3-pilot7-lr3e5-ep.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot7_lr3e5_ep/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot7_lr3e5_ep/report.json)

### bj_oft3_pilot_l10_bc；计时=3.7 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot-l10-bc.txt](results/baidu/bj_oft3_pilot_l10_bc/SOURCE-zw-rsi-bj-oft3-pilot-l10-bc.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot_l10_bc/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot_l10_bc/report.json)

### bj_oft3_pilot_l10_grpo；计时=4.1 h；cards=1
- [SOURCE-zw-rsi-bj-oft3-pilot-l10-grpo.txt](results/baidu/bj_oft3_pilot_l10_grpo/SOURCE-zw-rsi-bj-oft3-pilot-l10-grpo.txt)
- [backend-accounting.json](results/baidu/bj_oft3_pilot_l10_grpo/backend-accounting.json)
- [report.json](results/baidu/bj_oft3_pilot_l10_grpo/report.json)

### a8_oft3_pilot4_short_s1；计时=None h；cards=1

### a8_oft3_pilot6_curve_matched_s1；计时=24.1 h；cards=1
- [backend-accounting.json](results/a800/runs2/a8_oft3_pilot6_curve_matched_s1/backend-accounting.json)
- [report.json](results/a800/runs2/a8_oft3_pilot6_curve_matched_s1/report.json)

### a8_oft3_pilot6_curve_matched_s1.failed1；计时=None h；cards=1

### a8_oft3_pilot7_lr3e5_ep_s1；计时=22.5 h；cards=1
- [backend-accounting.json](results/a800/runs2/a8_oft3_pilot7_lr3e5_ep_s1/backend-accounting.json)
- [report.json](results/a800/runs2/a8_oft3_pilot7_lr3e5_ep_s1/report.json)

### a8_oft3_pilot7_lr3e5_s1；计时=22.1 h；cards=1
- [backend-accounting.json](results/a800/runs2/a8_oft3_pilot7_lr3e5_s1/backend-accounting.json)
- [report.json](results/a800/runs2/a8_oft3_pilot7_lr3e5_s1/report.json)

### bj_oftg_curve_bc；计时=11.5 h；cards=1
- [SOURCE-zw-rsi-bj-oftg-curve-bc.txt](results/baidu/bj_oftg_curve_bc/SOURCE-zw-rsi-bj-oftg-curve-bc.txt)
- [backend-accounting.json](results/baidu/bj_oftg_curve_bc/backend-accounting.json)
- [report.json](results/baidu/bj_oftg_curve_bc/report.json)

### bj_oftg_curve_grpo；计时=11.7 h；cards=1
- [SOURCE-zw-rsi-bj-oftg-curve-grpo.txt](results/baidu/bj_oftg_curve_grpo/SOURCE-zw-rsi-bj-oftg-curve-grpo.txt)
- [backend-accounting.json](results/baidu/bj_oftg_curve_grpo/backend-accounting.json)
- [report.json](results/baidu/bj_oftg_curve_grpo/report.json)

### bj_oftg_curve_grpo_s2；计时=12.0 h；cards=1
- [SOURCE-zw-rsi-bj-oftg-curve-grpo-s2.txt](results/baidu/bj_oftg_curve_grpo_s2/SOURCE-zw-rsi-bj-oftg-curve-grpo-s2.txt)
- [backend-accounting.json](results/baidu/bj_oftg_curve_grpo_s2/backend-accounting.json)
- [report.json](results/baidu/bj_oftg_curve_grpo_s2/report.json)

### bj_oftg_curve_grpo_s3；计时=11.8 h；cards=1
- [SOURCE-zw-rsi-bj-oftg-curve-grpo-s3.txt](results/baidu/bj_oftg_curve_grpo_s3/SOURCE-zw-rsi-bj-oftg-curve-grpo-s3.txt)
- [backend-accounting.json](results/baidu/bj_oftg_curve_grpo_s3/backend-accounting.json)
- [report.json](results/baidu/bj_oftg_curve_grpo_s3/report.json)

### a8_oftg_curve_bc_s1；计时=15.5 h；cards=1
- [backend-accounting.json](results/a800/runs2/a8_oftg_curve_bc_s1/backend-accounting.json)
- [report.json](results/a800/runs2/a8_oftg_curve_bc_s1/report.json)

### a8_oftg_curve_bct_s1；计时=None h；cards=1

### a8_oftg_curve_grpo_s1；计时=14.8 h；cards=1
- [backend-accounting.json](results/a800/runs2/a8_oftg_curve_grpo_s1/backend-accounting.json)
- [report.json](results/a800/runs2/a8_oftg_curve_grpo_s1/report.json)
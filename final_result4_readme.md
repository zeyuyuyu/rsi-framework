# Final results: Gate 的作用与严格程度——BC和GRPO下的两组对照

## 1. 这些数据支持什么结论

范围：LIBERO-Spatial，Yangquan seed 1、2、3，6轮，无元层。全部12个运行已完成；分成两个独立面板，分别在同一算法、同一配方内比较。

- 面板A：BC的严格gated（fixed）vs nogate，回答gate是否减少训练退化。
- 面板B：GRPO的严格gated（fixed）vs宽松guard，回答gate严格程度的影响。
- BC与GRPO不是同一个baseline。两个面板可放在一张图里，但不能拼成同条件下的gated / guard / nogate三方法消融，也不能把跨面板差距归因于gate或算法本身。

- BC · official：fixed 58.24% vs nogate 45.24%，配对均值差 **+13.00 pp**。
- BC · fresh：fixed 60.77% vs nogate 52.40%，配对均值差 **+8.37 pp**。
- GRPO · official：guard 61.84% vs fixed 60.22%，配对均值差 **+1.62 pp**。
- GRPO · fresh：guard 64.93% vs fixed 64.83%，配对均值差 **+0.10 pp**。

以上为描述性均值差；本文件不新增显著性或因果推断。BC面板用于检验保护作用，GRPO面板用于检验接受规则的取舍；不据此声称所有算法上某种gate都最优。

## 2. 最终结果总表

Official每运行3次评测，每次500 episodes；Fresh每运行1次评测，每次1000 episodes。先平均每个种子的评测，再平均seed1–3。SD为跨种子的样本标准差，不是95%CI。结果均取最终retained版本。

|面板/算法|测试|方法A|A均值 %|A SD|方法B|B均值 %|B SD|A−B pp|配对差值SD|
|---|---|---|---:|---:|---|---:|---:|---:|---:|
|BC|official|fixed|58.2444|1.1399|nogate|45.2444|0.9197|+13.0000|1.6344|
|BC|fresh|fixed|60.7667|2.7301|nogate|52.4000|1.3000|+8.3667|2.1733|
|GRPO|official|guard|61.8444|1.4626|fixed|60.2222|0.6577|+1.6222|1.8201|
|GRPO|fresh|guard|64.9333|0.4509|fixed|64.8333|0.4726|+0.1000|0.7000|

## 3. 逐种子结果、完成状态与原始入口

每行均核对config.rounds=6、status=complete、round-01到round-06齐全。Retained可能早于第6轮，因为后续候选未被接受。

|算法|方法|Seed|实际完成轮数|Retained|Official %|Fresh %|report|最终程序|
|---|---|---:|---:|---|---:|---:|---|---|
|BC|fixed|1|6|r03c0|58.8000|58.9000|[report.json](results/baidu/yq_oftsb_fixed_s1/report.json)|[retained.json](results/baidu/yq_oftsb_fixed_s1/retained.json)|
|BC|fixed|2|6|r06c0|59.0000|63.9000|[report.json](results/baidu/yq_oftsb_fixed_s2/report.json)|[retained.json](results/baidu/yq_oftsb_fixed_s2/retained.json)|
|BC|fixed|3|6|r05c0|56.9333|59.5000|[report.json](results/baidu/yq_oftsb_fixed_s3/report.json)|[retained.json](results/baidu/yq_oftsb_fixed_s3/retained.json)|
|BC|nogate|1|6|r06c0|44.2000|50.9000|[report.json](results/baidu/yq_oftsb_nogate_s1/report.json)|[retained.json](results/baidu/yq_oftsb_nogate_s1/retained.json)|
|BC|nogate|2|6|r06c0|45.9333|53.2000|[report.json](results/baidu/yq_oftsb_nogate_s2/report.json)|[retained.json](results/baidu/yq_oftsb_nogate_s2/retained.json)|
|BC|nogate|3|6|r06c0|45.6000|53.1000|[report.json](results/baidu/yq_oftsb_nogate_s3/report.json)|[retained.json](results/baidu/yq_oftsb_nogate_s3/retained.json)|
|GRPO|fixed|1|6|r06c0|60.5333|64.3000|[report.json](results/baidu/yq_ofts_fixed_s1/report.json)|[retained.json](results/baidu/yq_ofts_fixed_s1/retained.json)|
|GRPO|fixed|2|6|r06c0|60.6667|65.0000|[report.json](results/baidu/yq_ofts_fixed_s2/report.json)|[retained.json](results/baidu/yq_ofts_fixed_s2/retained.json)|
|GRPO|fixed|3|6|r06c0|59.4667|65.2000|[report.json](results/baidu/yq_ofts_fixed_s3/report.json)|[retained.json](results/baidu/yq_ofts_fixed_s3/retained.json)|
|GRPO|guard|1|6|r06c0|63.0000|64.9000|[report.json](results/baidu/yq_ofts_guard_s1/report.json)|[retained.json](results/baidu/yq_ofts_guard_s1/retained.json)|
|GRPO|guard|2|6|r06c0|60.2000|65.4000|[report.json](results/baidu/yq_ofts_guard_s2/report.json)|[retained.json](results/baidu/yq_ofts_guard_s2/retained.json)|
|GRPO|guard|3|6|r06c0|62.3333|64.5000|[report.json](results/baidu/yq_ofts_guard_s3/report.json)|[retained.json](results/baidu/yq_ofts_guard_s3/retained.json)|

### 同算法内逐种子差值

|算法|差值方向|Seed|Official Δ pp|Fresh Δ pp|
|---|---|---:|---:|---:|
|BC|fixed − nogate|1|+14.6000|+8.0000|
|BC|fixed − nogate|2|+13.0667|+10.7000|
|BC|fixed − nogate|3|+11.3333|+6.4000|
|GRPO|guard − fixed|1|+2.4667|+0.6000|
|GRPO|guard − fixed|2|-0.4667|+0.4000|
|GRPO|guard − fixed|3|+2.8667|-0.7000|

## 4. 参数与gate定义

两组均6轮 × 每轮1候选 × 3 inner steps，recursive=true，meta关闭。不是result2的2候选LLM元层实验，也不是result3的12轮实验。

|配置|BC gated/fixed|BC nogate|GRPO gated/fixed|GRPO guard|
|---|---|---|---|---|
|operator|bc|bc|grpo|grpo|
|min_gate_gain|0|−1|0|−0.05|
|gate_floor|未启用|未启用|未启用|0.05|
|接受规则|候选不低于父策略|有效候选不因成功率下降而拒绝|候选不低于父策略|不比父策略或初始策略低超过5pp|
|test_all_accepted|true|false|true|false|

nogate仍可能保留gate评测日志，但min_gate_gain=−1取消基于成功率退化的拒绝；不是完全不计算gate分数。guard的gate_floor=0.05不是成功率至少5%。各轮fresh gate与封存Fresh test不是同一套场景。

### 原始最终程序参数

下列按完整程序参数去重展示，每个组内各种子保留参数一致才合并。参数直接从retained.json读取。

#### BC

```json
{
  "curation": {
    "adv": "center",
    "band": [
      0.0,
      1.0
    ],
    "budget": 400,
    "per_case": 2,
    "rule": "verified"
  },
  "curriculum": {
    "allocation": "uniform",
    "cases": 64,
    "floor": 0.05
  },
  "solver": {
    "greedy": 0,
    "samples": 8,
    "temperature": 1.6
  },
  "update": {
    "batch": 64,
    "bc_temp": "unit",
    "clip_high": 0.28,
    "clip_low": 0.2,
    "loss_agg": "episode",
    "lr": 1e-05,
    "operator": "bc",
    "ratio": "matched",
    "steps": 100
  }
}
```

#### GRPO

```json
{
  "curation": {
    "band": [
      0.0,
      1.0
    ],
    "budget": 400,
    "per_case": 2,
    "rule": "mixed_groups"
  },
  "curriculum": {
    "allocation": "uniform",
    "cases": 64,
    "floor": 0.05
  },
  "solver": {
    "greedy": 0,
    "samples": 8,
    "temperature": 1.6
  },
  "update": {
    "batch": 64,
    "clip_high": 0.28,
    "clip_low": 0.2,
    "lr": 3e-05,
    "operator": "grpo",
    "steps": 100
  }
}
```


配置依据：[计划生成脚本](scripts/baidu/mkplans_vla.py)中的yq_spatial_nogate、yq_spatial_main与yq_spatial_guard；[执行引擎](rsi/core/engine.py)中的接受条件；[BC自修复与元层配置](scripts/baidu/mkplans_vla.py)中的yq_spatial_repair。BC侧始终使用BC程序，GRPO侧始终使用GRPO程序。

## 5. 画图与解释建议

同一张图中分BC与GRPO两块，每块分别画Official与Fresh。BC只画gated与nogate；GRPO只画gated与guard。共享成功率坐标便于读数，但baseline名称必须带算法前缀。

- 显示各方法均值和seed1–3散点；同种子连接，体现配对关系。
- 若用SD误差线，注明是三个训练种子之间的样本SD；不要把三次Official评测算作三个额外种子。
- 两个面板的差值方向分别为BC gated−nogate、GRPO guard−gated。
- 不将gate/audit轨迹作为Official/Fresh替代。nogate/guard没有每个接受版本的完整Official曲线，缺失点不能伪造。
- 可以表述为“gate在BC自训练中减少退化；另在GRPO下检验放宽接受规则的效果”。不要称“已完成统一的三组gate消融”。

## 6. 统计与已有结果定位

以下为辅助复核，不覆盖本文件重新从raw生成的三种子数值。部分已有报告混入seed0或其他平台，不能把其整体CI直接套到本表。

- [results/spatial_nogate_partA_20261112.json](results/spatial_nogate_partA_20261112.json)
- [results/fresh_spatial_guard_yq_20261112.json](results/fresh_spatial_guard_yq_20261112.json)
- [results/spatial_guard_primary_read_20261112.json](results/spatial_guard_primary_read_20261112.json)
- [scripts/report/spatial_guard_read.py](scripts/report/spatial_guard_read.py)
- [scripts/report/fresh_read.py](scripts/report/fresh_read.py)
- [docs/prereg/ROBOT_RSI_V3_ADDENDUM_31_20261110.md](docs/prereg/ROBOT_RSI_V3_ADDENDUM_31_20261110.md)
- [docs/prereg/ROBOT_RSI_V3_ADDENDUM_33_20261111.md](docs/prereg/ROBOT_RSI_V3_ADDENDUM_33_20261111.md)

## 7. 所有原始评测与来源文件

链接相对repo根目录。每个主目录包含运行report、retained配置、逐轮记录、TESTBITS与来源标识；_rep包含Official追加两次评测；_fresh包含Fresh评测。逐次成功率列在文件索引前，便于独立重算均值。

### yq_oftsb_fixed_s1

- official：58.8000%；[test-libero_official-r03c0.jsonl](results/baidu/yq_oftsb_fixed_s1/tests.txt)
- official：58.8000%；[test-libero_official-r03c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- official：58.8000%；[test-libero_official-r03c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- fresh：58.9000%；[test-libero_fresh-r03c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s1_fresh/tests.txt)

完整来源：

- [yq_oftsb_fixed_s1/SOURCE-zw-rsi-yq-oftsb-fixed-s1.job-n0gmy4g8pbzk.txt](results/baidu/yq_oftsb_fixed_s1/SOURCE-zw-rsi-yq-oftsb-fixed-s1.job-n0gmy4g8pbzk.txt)
- [yq_oftsb_fixed_s1/accepted.jsonl](results/baidu/yq_oftsb_fixed_s1/accepted.jsonl)
- [yq_oftsb_fixed_s1/backend-accounting.json](results/baidu/yq_oftsb_fixed_s1/backend-accounting.json)
- [yq_oftsb_fixed_s1/report.json](results/baidu/yq_oftsb_fixed_s1/report.json)
- [yq_oftsb_fixed_s1/retained.json](results/baidu/yq_oftsb_fixed_s1/retained.json)
- [yq_oftsb_fixed_s1/round-01.json](results/baidu/yq_oftsb_fixed_s1/round-01.json)
- [yq_oftsb_fixed_s1/round-02.json](results/baidu/yq_oftsb_fixed_s1/round-02.json)
- [yq_oftsb_fixed_s1/round-03.json](results/baidu/yq_oftsb_fixed_s1/round-03.json)
- [yq_oftsb_fixed_s1/round-04.json](results/baidu/yq_oftsb_fixed_s1/round-04.json)
- [yq_oftsb_fixed_s1/round-05.json](results/baidu/yq_oftsb_fixed_s1/round-05.json)
- [yq_oftsb_fixed_s1/round-06.json](results/baidu/yq_oftsb_fixed_s1/round-06.json)
- [yq_oftsb_fixed_s1/tests.txt](results/baidu/yq_oftsb_fixed_s1/tests.txt)
- [yq_oftsb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s1-rep.job-s0cb8h9rgm94.txt](results/baidu/yq_oftsb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s1-rep.job-s0cb8h9rgm94.txt)
- [yq_oftsb_fixed_s1_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s1_rep/test_eval.json)
- [yq_oftsb_fixed_s1_rep/tests.txt](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- [yq_oftsb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s1-fresh.job-ngsnv7pop3ev.txt](results/baidu/yq_oftsb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s1-fresh.job-ngsnv7pop3ev.txt)
- [yq_oftsb_fixed_s1_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s1_fresh/test_eval.json)
- [yq_oftsb_fixed_s1_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s1_fresh/tests.txt)

### yq_oftsb_fixed_s2

- official：59.0000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_fixed_s2/tests.txt)
- official：58.4000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- official：59.6000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- fresh：63.9000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s2_fresh/tests.txt)

完整来源：

- [yq_oftsb_fixed_s2/SOURCE-zw-rsi-yq-oftsb-fixed-s2.job-6xylapl210xu.txt](results/baidu/yq_oftsb_fixed_s2/SOURCE-zw-rsi-yq-oftsb-fixed-s2.job-6xylapl210xu.txt)
- [yq_oftsb_fixed_s2/accepted.jsonl](results/baidu/yq_oftsb_fixed_s2/accepted.jsonl)
- [yq_oftsb_fixed_s2/backend-accounting.json](results/baidu/yq_oftsb_fixed_s2/backend-accounting.json)
- [yq_oftsb_fixed_s2/report.json](results/baidu/yq_oftsb_fixed_s2/report.json)
- [yq_oftsb_fixed_s2/retained.json](results/baidu/yq_oftsb_fixed_s2/retained.json)
- [yq_oftsb_fixed_s2/round-01.json](results/baidu/yq_oftsb_fixed_s2/round-01.json)
- [yq_oftsb_fixed_s2/round-02.json](results/baidu/yq_oftsb_fixed_s2/round-02.json)
- [yq_oftsb_fixed_s2/round-03.json](results/baidu/yq_oftsb_fixed_s2/round-03.json)
- [yq_oftsb_fixed_s2/round-04.json](results/baidu/yq_oftsb_fixed_s2/round-04.json)
- [yq_oftsb_fixed_s2/round-05.json](results/baidu/yq_oftsb_fixed_s2/round-05.json)
- [yq_oftsb_fixed_s2/round-06.json](results/baidu/yq_oftsb_fixed_s2/round-06.json)
- [yq_oftsb_fixed_s2/tests.txt](results/baidu/yq_oftsb_fixed_s2/tests.txt)
- [yq_oftsb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s2-rep.job-ercl1a63nhev.txt](results/baidu/yq_oftsb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s2-rep.job-ercl1a63nhev.txt)
- [yq_oftsb_fixed_s2_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s2_rep/test_eval.json)
- [yq_oftsb_fixed_s2_rep/tests.txt](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- [yq_oftsb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s2-fresh.job-prw1wmfferi2.txt](results/baidu/yq_oftsb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s2-fresh.job-prw1wmfferi2.txt)
- [yq_oftsb_fixed_s2_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s2_fresh/test_eval.json)
- [yq_oftsb_fixed_s2_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s2_fresh/tests.txt)

### yq_oftsb_fixed_s3

- official：56.2000%；[test-libero_official-r05c0.jsonl](results/baidu/yq_oftsb_fixed_s3/tests.txt)
- official：57.0000%；[test-libero_official-r05c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- official：57.6000%；[test-libero_official-r05c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- fresh：59.5000%；[test-libero_fresh-r05c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s3_fresh/tests.txt)

完整来源：

- [yq_oftsb_fixed_s3/SOURCE-zw-rsi-yq-oftsb-fixed-s3.job-6f5ro54xfi6y.txt](results/baidu/yq_oftsb_fixed_s3/SOURCE-zw-rsi-yq-oftsb-fixed-s3.job-6f5ro54xfi6y.txt)
- [yq_oftsb_fixed_s3/accepted.jsonl](results/baidu/yq_oftsb_fixed_s3/accepted.jsonl)
- [yq_oftsb_fixed_s3/backend-accounting.json](results/baidu/yq_oftsb_fixed_s3/backend-accounting.json)
- [yq_oftsb_fixed_s3/report.json](results/baidu/yq_oftsb_fixed_s3/report.json)
- [yq_oftsb_fixed_s3/retained.json](results/baidu/yq_oftsb_fixed_s3/retained.json)
- [yq_oftsb_fixed_s3/round-01.json](results/baidu/yq_oftsb_fixed_s3/round-01.json)
- [yq_oftsb_fixed_s3/round-02.json](results/baidu/yq_oftsb_fixed_s3/round-02.json)
- [yq_oftsb_fixed_s3/round-03.json](results/baidu/yq_oftsb_fixed_s3/round-03.json)
- [yq_oftsb_fixed_s3/round-04.json](results/baidu/yq_oftsb_fixed_s3/round-04.json)
- [yq_oftsb_fixed_s3/round-05.json](results/baidu/yq_oftsb_fixed_s3/round-05.json)
- [yq_oftsb_fixed_s3/round-06.json](results/baidu/yq_oftsb_fixed_s3/round-06.json)
- [yq_oftsb_fixed_s3/tests.txt](results/baidu/yq_oftsb_fixed_s3/tests.txt)
- [yq_oftsb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s3-rep.job-019axm8141wl.txt](results/baidu/yq_oftsb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s3-rep.job-019axm8141wl.txt)
- [yq_oftsb_fixed_s3_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s3_rep/test_eval.json)
- [yq_oftsb_fixed_s3_rep/tests.txt](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- [yq_oftsb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s3-fresh.job-9od6lw5ul4pf.txt](results/baidu/yq_oftsb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s3-fresh.job-9od6lw5ul4pf.txt)
- [yq_oftsb_fixed_s3_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s3_fresh/test_eval.json)
- [yq_oftsb_fixed_s3_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s3_fresh/tests.txt)

### yq_oftsb_nogate_s1

- official：44.6000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_nogate_s1/tests.txt)
- official：43.4000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s1_rep/tests.txt)
- official：44.6000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_nogate_s1_rep/tests.txt)
- fresh：50.9000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s1_fresh/tests.txt)

完整来源：

- [yq_oftsb_nogate_s1/SOURCE-zw-rsi-yq-oftsb-nogate-s1.job-i662avsthrlv.txt](results/baidu/yq_oftsb_nogate_s1/SOURCE-zw-rsi-yq-oftsb-nogate-s1.job-i662avsthrlv.txt)
- [yq_oftsb_nogate_s1/accepted.jsonl](results/baidu/yq_oftsb_nogate_s1/accepted.jsonl)
- [yq_oftsb_nogate_s1/backend-accounting.json](results/baidu/yq_oftsb_nogate_s1/backend-accounting.json)
- [yq_oftsb_nogate_s1/report.json](results/baidu/yq_oftsb_nogate_s1/report.json)
- [yq_oftsb_nogate_s1/retained.json](results/baidu/yq_oftsb_nogate_s1/retained.json)
- [yq_oftsb_nogate_s1/round-01.json](results/baidu/yq_oftsb_nogate_s1/round-01.json)
- [yq_oftsb_nogate_s1/round-02.json](results/baidu/yq_oftsb_nogate_s1/round-02.json)
- [yq_oftsb_nogate_s1/round-03.json](results/baidu/yq_oftsb_nogate_s1/round-03.json)
- [yq_oftsb_nogate_s1/round-04.json](results/baidu/yq_oftsb_nogate_s1/round-04.json)
- [yq_oftsb_nogate_s1/round-05.json](results/baidu/yq_oftsb_nogate_s1/round-05.json)
- [yq_oftsb_nogate_s1/round-06.json](results/baidu/yq_oftsb_nogate_s1/round-06.json)
- [yq_oftsb_nogate_s1/tests.txt](results/baidu/yq_oftsb_nogate_s1/tests.txt)
- [yq_oftsb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s1-rep.job-8nedmrol4bq9.txt](results/baidu/yq_oftsb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s1-rep.job-8nedmrol4bq9.txt)
- [yq_oftsb_nogate_s1_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s1_rep/test_eval.json)
- [yq_oftsb_nogate_s1_rep/tests.txt](results/baidu/yq_oftsb_nogate_s1_rep/tests.txt)
- [yq_oftsb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s1-fresh.job-gh9kknis8b71.txt](results/baidu/yq_oftsb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s1-fresh.job-gh9kknis8b71.txt)
- [yq_oftsb_nogate_s1_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s1_fresh/test_eval.json)
- [yq_oftsb_nogate_s1_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s1_fresh/tests.txt)

### yq_oftsb_nogate_s2

- official：45.4000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_nogate_s2/tests.txt)
- official：46.6000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s2_rep/tests.txt)
- official：45.8000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_nogate_s2_rep/tests.txt)
- fresh：53.2000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s2_fresh/tests.txt)

完整来源：

- [yq_oftsb_nogate_s2/SOURCE-zw-rsi-yq-oftsb-nogate-s2.job-qx6mkagov5s4.txt](results/baidu/yq_oftsb_nogate_s2/SOURCE-zw-rsi-yq-oftsb-nogate-s2.job-qx6mkagov5s4.txt)
- [yq_oftsb_nogate_s2/accepted.jsonl](results/baidu/yq_oftsb_nogate_s2/accepted.jsonl)
- [yq_oftsb_nogate_s2/backend-accounting.json](results/baidu/yq_oftsb_nogate_s2/backend-accounting.json)
- [yq_oftsb_nogate_s2/report.json](results/baidu/yq_oftsb_nogate_s2/report.json)
- [yq_oftsb_nogate_s2/retained.json](results/baidu/yq_oftsb_nogate_s2/retained.json)
- [yq_oftsb_nogate_s2/round-01.json](results/baidu/yq_oftsb_nogate_s2/round-01.json)
- [yq_oftsb_nogate_s2/round-02.json](results/baidu/yq_oftsb_nogate_s2/round-02.json)
- [yq_oftsb_nogate_s2/round-03.json](results/baidu/yq_oftsb_nogate_s2/round-03.json)
- [yq_oftsb_nogate_s2/round-04.json](results/baidu/yq_oftsb_nogate_s2/round-04.json)
- [yq_oftsb_nogate_s2/round-05.json](results/baidu/yq_oftsb_nogate_s2/round-05.json)
- [yq_oftsb_nogate_s2/round-06.json](results/baidu/yq_oftsb_nogate_s2/round-06.json)
- [yq_oftsb_nogate_s2/tests.txt](results/baidu/yq_oftsb_nogate_s2/tests.txt)
- [yq_oftsb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s2-rep.job-x40qjsn7b059.txt](results/baidu/yq_oftsb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s2-rep.job-x40qjsn7b059.txt)
- [yq_oftsb_nogate_s2_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s2_rep/test_eval.json)
- [yq_oftsb_nogate_s2_rep/tests.txt](results/baidu/yq_oftsb_nogate_s2_rep/tests.txt)
- [yq_oftsb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s2-fresh.job-qiw3a2ls1t99.txt](results/baidu/yq_oftsb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s2-fresh.job-qiw3a2ls1t99.txt)
- [yq_oftsb_nogate_s2_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s2_fresh/test_eval.json)
- [yq_oftsb_nogate_s2_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s2_fresh/tests.txt)

### yq_oftsb_nogate_s3

- official：46.6000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_nogate_s3/tests.txt)
- official：43.8000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s3_rep/tests.txt)
- official：46.4000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_nogate_s3_rep/tests.txt)
- fresh：53.1000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_nogate_s3_fresh/tests.txt)

完整来源：

- [yq_oftsb_nogate_s3/SOURCE-zw-rsi-yq-oftsb-nogate-s3.job-khefn5fhnjji.txt](results/baidu/yq_oftsb_nogate_s3/SOURCE-zw-rsi-yq-oftsb-nogate-s3.job-khefn5fhnjji.txt)
- [yq_oftsb_nogate_s3/accepted.jsonl](results/baidu/yq_oftsb_nogate_s3/accepted.jsonl)
- [yq_oftsb_nogate_s3/backend-accounting.json](results/baidu/yq_oftsb_nogate_s3/backend-accounting.json)
- [yq_oftsb_nogate_s3/report.json](results/baidu/yq_oftsb_nogate_s3/report.json)
- [yq_oftsb_nogate_s3/retained.json](results/baidu/yq_oftsb_nogate_s3/retained.json)
- [yq_oftsb_nogate_s3/round-01.json](results/baidu/yq_oftsb_nogate_s3/round-01.json)
- [yq_oftsb_nogate_s3/round-02.json](results/baidu/yq_oftsb_nogate_s3/round-02.json)
- [yq_oftsb_nogate_s3/round-03.json](results/baidu/yq_oftsb_nogate_s3/round-03.json)
- [yq_oftsb_nogate_s3/round-04.json](results/baidu/yq_oftsb_nogate_s3/round-04.json)
- [yq_oftsb_nogate_s3/round-05.json](results/baidu/yq_oftsb_nogate_s3/round-05.json)
- [yq_oftsb_nogate_s3/round-06.json](results/baidu/yq_oftsb_nogate_s3/round-06.json)
- [yq_oftsb_nogate_s3/tests.txt](results/baidu/yq_oftsb_nogate_s3/tests.txt)
- [yq_oftsb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s3-rep.job-xib2v61ce17j.txt](results/baidu/yq_oftsb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s3-rep.job-xib2v61ce17j.txt)
- [yq_oftsb_nogate_s3_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s3_rep/test_eval.json)
- [yq_oftsb_nogate_s3_rep/tests.txt](results/baidu/yq_oftsb_nogate_s3_rep/tests.txt)
- [yq_oftsb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s3-fresh.job-b8gxi9rn5i0a.txt](results/baidu/yq_oftsb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s3-fresh.job-b8gxi9rn5i0a.txt)
- [yq_oftsb_nogate_s3_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s3_fresh/test_eval.json)
- [yq_oftsb_nogate_s3_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s3_fresh/tests.txt)

### yq_ofts_fixed_s1

- official：61.0000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_fixed_s1/tests.txt)
- official：60.2000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s1_rep/tests.txt)
- official：60.4000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_fixed_s1_rep/tests.txt)
- fresh：64.3000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s1_fresh/tests.txt)

完整来源：

- [yq_ofts_fixed_s1/SOURCE-zw-rsi-yq-ofts-fixed-s1.job-x0wgqyvb472k.txt](results/baidu/yq_ofts_fixed_s1/SOURCE-zw-rsi-yq-ofts-fixed-s1.job-x0wgqyvb472k.txt)
- [yq_ofts_fixed_s1/accepted.jsonl](results/baidu/yq_ofts_fixed_s1/accepted.jsonl)
- [yq_ofts_fixed_s1/backend-accounting.json](results/baidu/yq_ofts_fixed_s1/backend-accounting.json)
- [yq_ofts_fixed_s1/report.json](results/baidu/yq_ofts_fixed_s1/report.json)
- [yq_ofts_fixed_s1/retained.json](results/baidu/yq_ofts_fixed_s1/retained.json)
- [yq_ofts_fixed_s1/round-01.json](results/baidu/yq_ofts_fixed_s1/round-01.json)
- [yq_ofts_fixed_s1/round-02.json](results/baidu/yq_ofts_fixed_s1/round-02.json)
- [yq_ofts_fixed_s1/round-03.json](results/baidu/yq_ofts_fixed_s1/round-03.json)
- [yq_ofts_fixed_s1/round-04.json](results/baidu/yq_ofts_fixed_s1/round-04.json)
- [yq_ofts_fixed_s1/round-05.json](results/baidu/yq_ofts_fixed_s1/round-05.json)
- [yq_ofts_fixed_s1/round-06.json](results/baidu/yq_ofts_fixed_s1/round-06.json)
- [yq_ofts_fixed_s1/tests.txt](results/baidu/yq_ofts_fixed_s1/tests.txt)
- [yq_ofts_fixed_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed-s1-rep.job-k5zxk4qn836h.txt](results/baidu/yq_ofts_fixed_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed-s1-rep.job-k5zxk4qn836h.txt)
- [yq_ofts_fixed_s1_rep/test_eval.json](results/baidu/yq_ofts_fixed_s1_rep/test_eval.json)
- [yq_ofts_fixed_s1_rep/tests.txt](results/baidu/yq_ofts_fixed_s1_rep/tests.txt)
- [yq_ofts_fixed_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s1-fresh.job-twu2m9nloynr.txt](results/baidu/yq_ofts_fixed_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s1-fresh.job-twu2m9nloynr.txt)
- [yq_ofts_fixed_s1_fresh/test_eval.json](results/baidu/yq_ofts_fixed_s1_fresh/test_eval.json)
- [yq_ofts_fixed_s1_fresh/tests.txt](results/baidu/yq_ofts_fixed_s1_fresh/tests.txt)

### yq_ofts_fixed_s2

- official：60.8000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_fixed_s2/tests.txt)
- official：60.8000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s2_rep/tests.txt)
- official：60.4000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_fixed_s2_rep/tests.txt)
- fresh：65.0000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s2_fresh/tests.txt)

完整来源：

- [yq_ofts_fixed_s2/SOURCE-zw-rsi-yq-ofts-fixed-s2.job-mueiz2a9wzdh.txt](results/baidu/yq_ofts_fixed_s2/SOURCE-zw-rsi-yq-ofts-fixed-s2.job-mueiz2a9wzdh.txt)
- [yq_ofts_fixed_s2/accepted.jsonl](results/baidu/yq_ofts_fixed_s2/accepted.jsonl)
- [yq_ofts_fixed_s2/backend-accounting.json](results/baidu/yq_ofts_fixed_s2/backend-accounting.json)
- [yq_ofts_fixed_s2/report.json](results/baidu/yq_ofts_fixed_s2/report.json)
- [yq_ofts_fixed_s2/retained.json](results/baidu/yq_ofts_fixed_s2/retained.json)
- [yq_ofts_fixed_s2/round-01.json](results/baidu/yq_ofts_fixed_s2/round-01.json)
- [yq_ofts_fixed_s2/round-02.json](results/baidu/yq_ofts_fixed_s2/round-02.json)
- [yq_ofts_fixed_s2/round-03.json](results/baidu/yq_ofts_fixed_s2/round-03.json)
- [yq_ofts_fixed_s2/round-04.json](results/baidu/yq_ofts_fixed_s2/round-04.json)
- [yq_ofts_fixed_s2/round-05.json](results/baidu/yq_ofts_fixed_s2/round-05.json)
- [yq_ofts_fixed_s2/round-06.json](results/baidu/yq_ofts_fixed_s2/round-06.json)
- [yq_ofts_fixed_s2/tests.txt](results/baidu/yq_ofts_fixed_s2/tests.txt)
- [yq_ofts_fixed_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed-s2-rep.job-av5wdly9rcee.txt](results/baidu/yq_ofts_fixed_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed-s2-rep.job-av5wdly9rcee.txt)
- [yq_ofts_fixed_s2_rep/test_eval.json](results/baidu/yq_ofts_fixed_s2_rep/test_eval.json)
- [yq_ofts_fixed_s2_rep/tests.txt](results/baidu/yq_ofts_fixed_s2_rep/tests.txt)
- [yq_ofts_fixed_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s2-fresh.job-351wg41fhk7h.txt](results/baidu/yq_ofts_fixed_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s2-fresh.job-351wg41fhk7h.txt)
- [yq_ofts_fixed_s2_fresh/test_eval.json](results/baidu/yq_ofts_fixed_s2_fresh/test_eval.json)
- [yq_ofts_fixed_s2_fresh/tests.txt](results/baidu/yq_ofts_fixed_s2_fresh/tests.txt)

### yq_ofts_fixed_s3

- official：59.2000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_fixed_s3/tests.txt)
- official：59.4000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s3_rep/tests.txt)
- official：59.8000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_fixed_s3_rep/tests.txt)
- fresh：65.2000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_fixed_s3_fresh/tests.txt)

完整来源：

- [yq_ofts_fixed_s3/SOURCE-zw-rsi-yq-ofts-fixed-s3.job-knec13gc1jtx.txt](results/baidu/yq_ofts_fixed_s3/SOURCE-zw-rsi-yq-ofts-fixed-s3.job-knec13gc1jtx.txt)
- [yq_ofts_fixed_s3/accepted.jsonl](results/baidu/yq_ofts_fixed_s3/accepted.jsonl)
- [yq_ofts_fixed_s3/backend-accounting.json](results/baidu/yq_ofts_fixed_s3/backend-accounting.json)
- [yq_ofts_fixed_s3/report.json](results/baidu/yq_ofts_fixed_s3/report.json)
- [yq_ofts_fixed_s3/retained.json](results/baidu/yq_ofts_fixed_s3/retained.json)
- [yq_ofts_fixed_s3/round-01.json](results/baidu/yq_ofts_fixed_s3/round-01.json)
- [yq_ofts_fixed_s3/round-02.json](results/baidu/yq_ofts_fixed_s3/round-02.json)
- [yq_ofts_fixed_s3/round-03.json](results/baidu/yq_ofts_fixed_s3/round-03.json)
- [yq_ofts_fixed_s3/round-04.json](results/baidu/yq_ofts_fixed_s3/round-04.json)
- [yq_ofts_fixed_s3/round-05.json](results/baidu/yq_ofts_fixed_s3/round-05.json)
- [yq_ofts_fixed_s3/round-06.json](results/baidu/yq_ofts_fixed_s3/round-06.json)
- [yq_ofts_fixed_s3/tests.txt](results/baidu/yq_ofts_fixed_s3/tests.txt)
- [yq_ofts_fixed_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed-s3-rep.job-w9baa96mqw7g.txt](results/baidu/yq_ofts_fixed_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed-s3-rep.job-w9baa96mqw7g.txt)
- [yq_ofts_fixed_s3_rep/test_eval.json](results/baidu/yq_ofts_fixed_s3_rep/test_eval.json)
- [yq_ofts_fixed_s3_rep/tests.txt](results/baidu/yq_ofts_fixed_s3_rep/tests.txt)
- [yq_ofts_fixed_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s3-fresh.job-xszucnyrv90t.txt](results/baidu/yq_ofts_fixed_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed-s3-fresh.job-xszucnyrv90t.txt)
- [yq_ofts_fixed_s3_fresh/test_eval.json](results/baidu/yq_ofts_fixed_s3_fresh/test_eval.json)
- [yq_ofts_fixed_s3_fresh/tests.txt](results/baidu/yq_ofts_fixed_s3_fresh/tests.txt)

### yq_ofts_guard_s1

- official：63.2000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_guard_s1/tests.txt)
- official：62.8000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s1_rep/tests.txt)
- official：63.0000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_guard_s1_rep/tests.txt)
- fresh：64.9000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s1_fresh/tests.txt)

完整来源：

- [yq_ofts_guard_s1/SOURCE-zw-rsi-yq-ofts-guard-s1.job-aqnwcje6866a.txt](results/baidu/yq_ofts_guard_s1/SOURCE-zw-rsi-yq-ofts-guard-s1.job-aqnwcje6866a.txt)
- [yq_ofts_guard_s1/accepted.jsonl](results/baidu/yq_ofts_guard_s1/accepted.jsonl)
- [yq_ofts_guard_s1/backend-accounting.json](results/baidu/yq_ofts_guard_s1/backend-accounting.json)
- [yq_ofts_guard_s1/report.json](results/baidu/yq_ofts_guard_s1/report.json)
- [yq_ofts_guard_s1/retained.json](results/baidu/yq_ofts_guard_s1/retained.json)
- [yq_ofts_guard_s1/round-01.json](results/baidu/yq_ofts_guard_s1/round-01.json)
- [yq_ofts_guard_s1/round-02.json](results/baidu/yq_ofts_guard_s1/round-02.json)
- [yq_ofts_guard_s1/round-03.json](results/baidu/yq_ofts_guard_s1/round-03.json)
- [yq_ofts_guard_s1/round-04.json](results/baidu/yq_ofts_guard_s1/round-04.json)
- [yq_ofts_guard_s1/round-05.json](results/baidu/yq_ofts_guard_s1/round-05.json)
- [yq_ofts_guard_s1/round-06.json](results/baidu/yq_ofts_guard_s1/round-06.json)
- [yq_ofts_guard_s1/tests.txt](results/baidu/yq_ofts_guard_s1/tests.txt)
- [yq_ofts_guard_s1_rep/SOURCE-zw-rsi-yq-ofts-guard-s1-rep.job-0g58kxp5cqtn.txt](results/baidu/yq_ofts_guard_s1_rep/SOURCE-zw-rsi-yq-ofts-guard-s1-rep.job-0g58kxp5cqtn.txt)
- [yq_ofts_guard_s1_rep/test_eval.json](results/baidu/yq_ofts_guard_s1_rep/test_eval.json)
- [yq_ofts_guard_s1_rep/tests.txt](results/baidu/yq_ofts_guard_s1_rep/tests.txt)
- [yq_ofts_guard_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard-s1-fresh.job-nnlp3u7t801n.txt](results/baidu/yq_ofts_guard_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard-s1-fresh.job-nnlp3u7t801n.txt)
- [yq_ofts_guard_s1_fresh/test_eval.json](results/baidu/yq_ofts_guard_s1_fresh/test_eval.json)
- [yq_ofts_guard_s1_fresh/tests.txt](results/baidu/yq_ofts_guard_s1_fresh/tests.txt)

### yq_ofts_guard_s2

- official：60.8000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_guard_s2/tests.txt)
- official：60.4000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s2_rep/tests.txt)
- official：59.4000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_guard_s2_rep/tests.txt)
- fresh：65.4000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s2_fresh/tests.txt)

完整来源：

- [yq_ofts_guard_s2/SOURCE-zw-rsi-yq-ofts-guard-s2.job-orn13tt5z6gv.txt](results/baidu/yq_ofts_guard_s2/SOURCE-zw-rsi-yq-ofts-guard-s2.job-orn13tt5z6gv.txt)
- [yq_ofts_guard_s2/accepted.jsonl](results/baidu/yq_ofts_guard_s2/accepted.jsonl)
- [yq_ofts_guard_s2/backend-accounting.json](results/baidu/yq_ofts_guard_s2/backend-accounting.json)
- [yq_ofts_guard_s2/report.json](results/baidu/yq_ofts_guard_s2/report.json)
- [yq_ofts_guard_s2/retained.json](results/baidu/yq_ofts_guard_s2/retained.json)
- [yq_ofts_guard_s2/round-01.json](results/baidu/yq_ofts_guard_s2/round-01.json)
- [yq_ofts_guard_s2/round-02.json](results/baidu/yq_ofts_guard_s2/round-02.json)
- [yq_ofts_guard_s2/round-03.json](results/baidu/yq_ofts_guard_s2/round-03.json)
- [yq_ofts_guard_s2/round-04.json](results/baidu/yq_ofts_guard_s2/round-04.json)
- [yq_ofts_guard_s2/round-05.json](results/baidu/yq_ofts_guard_s2/round-05.json)
- [yq_ofts_guard_s2/round-06.json](results/baidu/yq_ofts_guard_s2/round-06.json)
- [yq_ofts_guard_s2/tests.txt](results/baidu/yq_ofts_guard_s2/tests.txt)
- [yq_ofts_guard_s2_rep/SOURCE-zw-rsi-yq-ofts-guard-s2-rep.job-8rzr0l8vt13e.txt](results/baidu/yq_ofts_guard_s2_rep/SOURCE-zw-rsi-yq-ofts-guard-s2-rep.job-8rzr0l8vt13e.txt)
- [yq_ofts_guard_s2_rep/test_eval.json](results/baidu/yq_ofts_guard_s2_rep/test_eval.json)
- [yq_ofts_guard_s2_rep/tests.txt](results/baidu/yq_ofts_guard_s2_rep/tests.txt)
- [yq_ofts_guard_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard-s2-fresh.job-p28inylpc47h.txt](results/baidu/yq_ofts_guard_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard-s2-fresh.job-p28inylpc47h.txt)
- [yq_ofts_guard_s2_fresh/test_eval.json](results/baidu/yq_ofts_guard_s2_fresh/test_eval.json)
- [yq_ofts_guard_s2_fresh/tests.txt](results/baidu/yq_ofts_guard_s2_fresh/tests.txt)

### yq_ofts_guard_s3

- official：62.4000%；[test-libero_official-r06c0.jsonl](results/baidu/yq_ofts_guard_s3/tests.txt)
- official：61.8000%；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s3_rep/tests.txt)
- official：62.8000%；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_ofts_guard_s3_rep/tests.txt)
- fresh：64.5000%；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_ofts_guard_s3_fresh/tests.txt)

完整来源：

- [yq_ofts_guard_s3/SOURCE-zw-rsi-yq-ofts-guard-s3.job-8dfuvq7j0rsd.txt](results/baidu/yq_ofts_guard_s3/SOURCE-zw-rsi-yq-ofts-guard-s3.job-8dfuvq7j0rsd.txt)
- [yq_ofts_guard_s3/accepted.jsonl](results/baidu/yq_ofts_guard_s3/accepted.jsonl)
- [yq_ofts_guard_s3/backend-accounting.json](results/baidu/yq_ofts_guard_s3/backend-accounting.json)
- [yq_ofts_guard_s3/report.json](results/baidu/yq_ofts_guard_s3/report.json)
- [yq_ofts_guard_s3/retained.json](results/baidu/yq_ofts_guard_s3/retained.json)
- [yq_ofts_guard_s3/round-01.json](results/baidu/yq_ofts_guard_s3/round-01.json)
- [yq_ofts_guard_s3/round-02.json](results/baidu/yq_ofts_guard_s3/round-02.json)
- [yq_ofts_guard_s3/round-03.json](results/baidu/yq_ofts_guard_s3/round-03.json)
- [yq_ofts_guard_s3/round-04.json](results/baidu/yq_ofts_guard_s3/round-04.json)
- [yq_ofts_guard_s3/round-05.json](results/baidu/yq_ofts_guard_s3/round-05.json)
- [yq_ofts_guard_s3/round-06.json](results/baidu/yq_ofts_guard_s3/round-06.json)
- [yq_ofts_guard_s3/tests.txt](results/baidu/yq_ofts_guard_s3/tests.txt)
- [yq_ofts_guard_s3_rep/SOURCE-zw-rsi-yq-ofts-guard-s3-rep.job-dghkf21nwpye.txt](results/baidu/yq_ofts_guard_s3_rep/SOURCE-zw-rsi-yq-ofts-guard-s3-rep.job-dghkf21nwpye.txt)
- [yq_ofts_guard_s3_rep/test_eval.json](results/baidu/yq_ofts_guard_s3_rep/test_eval.json)
- [yq_ofts_guard_s3_rep/tests.txt](results/baidu/yq_ofts_guard_s3_rep/tests.txt)
- [yq_ofts_guard_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard-s3-fresh.job-ywgb2rycu3pg.txt](results/baidu/yq_ofts_guard_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard-s3-fresh.job-ywgb2rycu3pg.txt)
- [yq_ofts_guard_s3_fresh/test_eval.json](results/baidu/yq_ofts_guard_s3_fresh/test_eval.json)
- [yq_ofts_guard_s3_fresh/tests.txt](results/baidu/yq_ofts_guard_s3_fresh/tests.txt)

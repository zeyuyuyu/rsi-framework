# Final results: 12轮 recursion 与 gate 规则对比

## 1. 这些数据支持什么结论

范围：LIBERO-Goal / LIBERO-Spatial，以fixed12为baseline，比较nonrec12和guard12。全部18个运行均已完成12轮；seed 1 2 3, grpo

**Recursion在这套12轮固定GRPO程序下有一致收益：fixed12相对nonrec12，在两个任务的Official与Fresh上均提高。**

**放宽gate的收益较小：guard12相对fixed12的均值略高，但现有置信区间没有给出跨任务、跨测试一致的严格正收益证据。** 这里比较严格gate与宽松guard-rail gate，不是有无gate消融。

- Recursion：Goal Official +7.84 pp、Fresh +7.30 pp；Spatial Official +8.67 pp、Fresh +8.63 pp。
- Gate规则：Goal Official +0.89 pp、Fresh +1.67 pp；Spatial Official +0.29 pp、Fresh +1.17 pp。
- 所有比较均为12外层轮 × 1候选 × 3 inner steps；相同更新块数不等于实际GPU-hours相同。
- 支持的结论限定为当前任务、配方与12轮训练设置；不能由此证明包含元层的完整RSI优于普通RL。

## 2. 最终结果总表

Official每次500 episodes，每个运行平均3次评测；Fresh每次1000 episodes，每个运行1次评测。先得到每种子的成功率，再对seed1–3等权平均。SD为种子间样本标准差，不是95%CI。

|任务|测试|fixed12 %|SD|nonrec12 %|SD|guard12 %|SD|
|---|---|---:|---:|---:|---:|---:|---:|
|Goal|official|60.5333|1.9743|52.6889|3.9154|61.4222|0.7343|
|Goal|fresh|63.5667|3.0551|56.2667|3.4122|65.2333|1.5275|
|Spatial|official|61.0444|2.3817|52.3778|2.2572|61.3333|0.9165|
|Spatial|fresh|66.9333|1.9858|58.3000|0.6245|68.1000|2.1633|

## 3. 配对差值与既有统计结果

差值方向：recursion用fixed12 − nonrec12；gate规则用guard12 − fixed12。下面CI从repo既有三种子配对bootstrap统计读取，均值与原始评测重新计算核对。CI不替代跨种子SD，也不能用于别的种子集合。

|任务|测试|比较|差值 pp|95% CI pp|统计来源及key|
|---|---|---|---:|---|---|
|Goal|official|fixed12 − nonrec12|+7.8444|[5.22, 10.49]|[long12_read_20261108.json](results/long12_read_20261108.json) · `R3_long`|
|Goal|fresh|fixed12 − nonrec12|+7.3000|[5.47, 9.2]|[fresh_goal_long12_20261110.json](results/fresh_goal_long12_20261110.json) · `FL3`|
|Spatial|official|fixed12 − nonrec12|+8.6667|[6.76, 10.69]|[spatial_long12_read_20261114.json](results/spatial_long12_read_20261114.json) · `R3_long_spatial`|
|Spatial|fresh|fixed12 − nonrec12|+8.6333|[7.17, 10.1]|[fresh_spatial_long12_20261114.json](results/fresh_spatial_long12_20261114.json) · `FL3`|
|Goal|official|guard12 − fixed12|+0.8889|[-1.11, 2.89]|[goal_guard12_read_20261112.json](results/goal_guard12_read_20261112.json) · `G2`|
|Goal|fresh|guard12 − fixed12|+1.6667|[0.0, 3.3]|[fresh_goal_guard12_20261112.json](results/fresh_goal_guard12_20261112.json) · `G2`|
|Spatial|official|guard12 − fixed12|+0.2889|[-1.51, 2.13]|[spatial_guard12_read_20261114.json](results/spatial_guard12_read_20261114.json) · `G2s`|
|Spatial|fresh|guard12 − fixed12|+1.1667|[-0.07, 2.4]|[fresh_spatial_guard12_20261114.json](results/fresh_spatial_guard12_20261114.json) · `G2s`|

四个recursion区间下界均大于0。gate规则的两个Official区间均包含0；Spatial Fresh包含0；Goal Fresh报告下界为0.00，不能将显示精度下的0解释为严格大于0。

## 4. 逐种子结果及12轮完成核对

下列每个运行均核对：`config.rounds=12`、`status=complete`、round-01至round-12无缺失。Retained节点可能早于12轮，表示后续候选被拒绝，不表示训练提前结束。

|任务|方法|Seed|完成轮数|Retained|接受轮数|Official %|Fresh %|原始report|最终程序|
|---|---|---:|---:|---|---:|---:|---:|---|---|
|Goal|fixed12|1|12|r11c0|6|62.6000|60.9000|[report.json](results/baidu/yq_oftg_fixed12_s1/report.json)|[retained.json](results/baidu/yq_oftg_fixed12_s1/retained.json)|
|Goal|fixed12|2|12|r10c0|9|60.3333|66.9000|[report.json](results/baidu/yq_oftg_fixed12_s2/report.json)|[retained.json](results/baidu/yq_oftg_fixed12_s2/retained.json)|
|Goal|fixed12|3|12|r12c0|9|58.6667|62.9000|[report.json](results/baidu/yq_oftg_fixed12_s3/report.json)|[retained.json](results/baidu/yq_oftg_fixed12_s3/retained.json)|
|Goal|nonrec12|1|12|r07c0|5|48.2000|52.7000|[report.json](results/baidu/yq_oftg_nonrec12_s1/report.json)|[retained.json](results/baidu/yq_oftg_nonrec12_s1/retained.json)|
|Goal|nonrec12|2|12|r08c0|6|55.4000|59.5000|[report.json](results/baidu/yq_oftg_nonrec12_s2/report.json)|[retained.json](results/baidu/yq_oftg_nonrec12_s2/retained.json)|
|Goal|nonrec12|3|12|r10c0|5|54.4667|56.6000|[report.json](results/baidu/yq_oftg_nonrec12_s3/report.json)|[retained.json](results/baidu/yq_oftg_nonrec12_s3/retained.json)|
|Goal|guard12|1|12|r12c0|1|60.9333|66.9000|[report.json](results/baidu/yq_oftg_guard12_s1/report.json)|[retained.json](results/baidu/yq_oftg_guard12_s1/retained.json)|
|Goal|guard12|2|12|r12c0|1|62.2667|64.9000|[report.json](results/baidu/yq_oftg_guard12_s2/report.json)|[retained.json](results/baidu/yq_oftg_guard12_s2/retained.json)|
|Goal|guard12|3|12|r12c0|1|61.0667|63.9000|[report.json](results/baidu/yq_oftg_guard12_s3/report.json)|[retained.json](results/baidu/yq_oftg_guard12_s3/retained.json)|
|Spatial|fixed12|1|12|r11c0|7|60.2000|66.5000|[report.json](results/baidu/yq_ofts_fixed12_s1/report.json)|[retained.json](results/baidu/yq_ofts_fixed12_s1/retained.json)|
|Spatial|fixed12|2|12|r12c0|9|63.7333|69.1000|[report.json](results/baidu/yq_ofts_fixed12_s2/report.json)|[retained.json](results/baidu/yq_ofts_fixed12_s2/retained.json)|
|Spatial|fixed12|3|12|r09c0|6|59.2000|65.2000|[report.json](results/baidu/yq_ofts_fixed12_s3/report.json)|[retained.json](results/baidu/yq_ofts_fixed12_s3/retained.json)|
|Spatial|nonrec12|1|12|r11c0|5|49.8000|57.8000|[report.json](results/baidu/yq_ofts_nonrec12_s1/report.json)|[retained.json](results/baidu/yq_ofts_nonrec12_s1/retained.json)|
|Spatial|nonrec12|2|12|r11c0|6|53.3333|59.0000|[report.json](results/baidu/yq_ofts_nonrec12_s2/report.json)|[retained.json](results/baidu/yq_ofts_nonrec12_s2/retained.json)|
|Spatial|nonrec12|3|12|r09c0|4|54.0000|58.1000|[report.json](results/baidu/yq_ofts_nonrec12_s3/report.json)|[retained.json](results/baidu/yq_ofts_nonrec12_s3/retained.json)|
|Spatial|guard12|1|12|r12c0|1|62.3333|69.9000|[report.json](results/baidu/yq_ofts_guard12_s1/report.json)|[retained.json](results/baidu/yq_ofts_guard12_s1/retained.json)|
|Spatial|guard12|2|12|r12c0|1|61.1333|68.7000|[report.json](results/baidu/yq_ofts_guard12_s2/report.json)|[retained.json](results/baidu/yq_ofts_guard12_s2/retained.json)|
|Spatial|guard12|3|12|r12c0|1|60.5333|65.7000|[report.json](results/baidu/yq_ofts_guard12_s3/report.json)|[retained.json](results/baidu/yq_ofts_guard12_s3/retained.json)|

## 5. 参数：fixed、nonrec、guard的区别

|配置|fixed12|nonrec12|guard12|
|---|---|---|---|
|外层轮数|12|12|12|
|每轮候选|1|1|1|
|每候选inner steps|3|3|3|
|Meta程序更新|关闭|关闭|关闭|
|训练算法|固定GRPO|固定GRPO|固定GRPO|
|recursive|true|false|true|
|生成练习的策略|当前策略|冻结的初始策略|当前策略|
|模型是否训练更新|是|是；并非冻结训练|是|
|gate_mode|fresh_paired|fresh_paired|fresh_paired|
|min_gate_gain|0.0|0.0|−0.05|
|gate_floor|未开启|未开启|0.05|
|test_all_accepted|true|true|false|

fixed中的“固定”是固定训练程序，不是冻结模型。严格gate要求候选在本轮fresh gate场景上不低于父策略；guard允许最多5个百分点退步，但同时不能比初始策略低超过5个百分点。gate_floor=0.05不是成功率至少5%。Fresh gate与封存Fresh test是不同的数据。

共同程序的主要参数：operator=grpo，lr=3e-5，update.steps=100，batch=64，cases=64，samples=8，temperature=1.6，curation.rule=mixed_groups，budget=400，per_case=2，allocation=uniform。详细字段以每个运行retained.json为准；环境后端设置见配置生成代码和预注册。

|配置来源|作用|
|---|---|
|[计划生成代码](scripts/baidu/mkplans_vla.py)|yq_long12、yq_spatial_long12、Goal guard等配置|
|[执行引擎](rsi/core/engine.py)|recursive选择数据生成策略、gate接受规则|
|[Goal 12轮预注册](docs/prereg/ROBOT_RSI_V3_ADDENDUM_27_20261107.md)|Goal固定程序12轮对照|
|[Spatial 12轮与Fresh预注册](docs/prereg/ROBOT_RSI_V3_ADDENDUM_30_20261110.md)|Spatial长周期与Fresh测试|
|[Goal guard预注册](docs/prereg/ROBOT_RSI_V3_ADDENDUM_32_20261110.md)|Goal宽松gate规则|
|[Spatial guard12预注册及修订](docs/prereg/ROBOT_RSI_V3_ADDENDUM_34_20261112.md)|Spatial guard12；含Yangquan seeds1–3修订|

## 6. 画图建议与取数口径

|面板|内容|来源|
|---|---|---|
|A：recursion|fixed12 vs nonrec12；Goal / Spatial × Official / Fresh|第2、4节；同种子连接，显示均值与三种子点|
|B：gate规则|fixed12 vs guard12；相同任务和测试分面|第2、4节|
|C：配对差值|四个recursion差值及四个gate-rule差值|第3节；明确误差线为repo配对bootstrap CI|

固定baseline为fixed12，但差值方向必须在图例中写清。不要把nonrec12/fixed12的逐轮Official曲线与guard12当成同样密集的评测：guard的test_all_accepted=false，没有每个接受节点的完整Official测试。

绘制训练过程时，accepted.jsonl、round-*.json与report中的accepted_chain可用于gate/audit轨迹；Official曲线仅使用实际评测点。没有评测的轮不能伪造为新观测；若延续保留版本，需明确是沿用而非重新评测。

## 7. 原始逐次评测与完整来源索引

下列链接均相对repo根目录，已验证存在。report.json记录配置与状态；retained.json记录最终程序；round-*.json记录逐轮候选；tests.txt包含逐episode TESTBITS；_rep为Official追加两次评测，_fresh为Fresh测试；SOURCE文件给出同步来源。主表Official=主运行首次评测+_rep两次评测的均值。

### yq_oftg_fixed12_s1

- official：62.2000%；[test-libero_official-r11c0.jsonl](results/baidu/yq_oftg_fixed12_s1/tests.txt)
- official：63.4000%；[test-libero_official-r11c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s1_rep/tests.txt)
- official：62.2000%；[test-libero_official-r11c0-rep2.jsonl](results/baidu/yq_oftg_fixed12_s1_rep/tests.txt)
- fresh：60.9000%；[test-libero_fresh-r11c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s1_fresh/tests.txt)

完整文件：

- [yq_oftg_fixed12_s1/SOURCE-zw-rsi-yq-oftg-fixed12-s1.job-xo37dj1k4380.txt](results/baidu/yq_oftg_fixed12_s1/SOURCE-zw-rsi-yq-oftg-fixed12-s1.job-xo37dj1k4380.txt)
- [yq_oftg_fixed12_s1/accepted.jsonl](results/baidu/yq_oftg_fixed12_s1/accepted.jsonl)
- [yq_oftg_fixed12_s1/backend-accounting.json](results/baidu/yq_oftg_fixed12_s1/backend-accounting.json)
- [yq_oftg_fixed12_s1/report.json](results/baidu/yq_oftg_fixed12_s1/report.json)
- [yq_oftg_fixed12_s1/retained.json](results/baidu/yq_oftg_fixed12_s1/retained.json)
- [yq_oftg_fixed12_s1/round-01.json](results/baidu/yq_oftg_fixed12_s1/round-01.json)
- [yq_oftg_fixed12_s1/round-02.json](results/baidu/yq_oftg_fixed12_s1/round-02.json)
- [yq_oftg_fixed12_s1/round-03.json](results/baidu/yq_oftg_fixed12_s1/round-03.json)
- [yq_oftg_fixed12_s1/round-04.json](results/baidu/yq_oftg_fixed12_s1/round-04.json)
- [yq_oftg_fixed12_s1/round-05.json](results/baidu/yq_oftg_fixed12_s1/round-05.json)
- [yq_oftg_fixed12_s1/round-06.json](results/baidu/yq_oftg_fixed12_s1/round-06.json)
- [yq_oftg_fixed12_s1/round-07.json](results/baidu/yq_oftg_fixed12_s1/round-07.json)
- [yq_oftg_fixed12_s1/round-08.json](results/baidu/yq_oftg_fixed12_s1/round-08.json)
- [yq_oftg_fixed12_s1/round-09.json](results/baidu/yq_oftg_fixed12_s1/round-09.json)
- [yq_oftg_fixed12_s1/round-10.json](results/baidu/yq_oftg_fixed12_s1/round-10.json)
- [yq_oftg_fixed12_s1/round-11.json](results/baidu/yq_oftg_fixed12_s1/round-11.json)
- [yq_oftg_fixed12_s1/round-12.json](results/baidu/yq_oftg_fixed12_s1/round-12.json)
- [yq_oftg_fixed12_s1/tests.txt](results/baidu/yq_oftg_fixed12_s1/tests.txt)
- [yq_oftg_fixed12_s1_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s1-rep.job-c6vf2nao2tho.txt](results/baidu/yq_oftg_fixed12_s1_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s1-rep.job-c6vf2nao2tho.txt)
- [yq_oftg_fixed12_s1_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s1_rep/test_eval.json)
- [yq_oftg_fixed12_s1_rep/tests.txt](results/baidu/yq_oftg_fixed12_s1_rep/tests.txt)
- [yq_oftg_fixed12_s1_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s1-fresh.job-wdgcol9vn6r1.txt](results/baidu/yq_oftg_fixed12_s1_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s1-fresh.job-wdgcol9vn6r1.txt)
- [yq_oftg_fixed12_s1_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s1_fresh/test_eval.json)
- [yq_oftg_fixed12_s1_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s1_fresh/tests.txt)

### yq_oftg_fixed12_s2

- official：58.6000%；[test-libero_official-r10c0.jsonl](results/baidu/yq_oftg_fixed12_s2/tests.txt)
- official：61.4000%；[test-libero_official-r10c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s2_rep/tests.txt)
- official：61.0000%；[test-libero_official-r10c0-rep2.jsonl](results/baidu/yq_oftg_fixed12_s2_rep/tests.txt)
- fresh：66.9000%；[test-libero_fresh-r10c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s2_fresh/tests.txt)

完整文件：

- [yq_oftg_fixed12_s2/SOURCE-zw-rsi-yq-oftg-fixed12-s2.job-ld0nj3ihtqwr.txt](results/baidu/yq_oftg_fixed12_s2/SOURCE-zw-rsi-yq-oftg-fixed12-s2.job-ld0nj3ihtqwr.txt)
- [yq_oftg_fixed12_s2/accepted.jsonl](results/baidu/yq_oftg_fixed12_s2/accepted.jsonl)
- [yq_oftg_fixed12_s2/backend-accounting.json](results/baidu/yq_oftg_fixed12_s2/backend-accounting.json)
- [yq_oftg_fixed12_s2/report.json](results/baidu/yq_oftg_fixed12_s2/report.json)
- [yq_oftg_fixed12_s2/retained.json](results/baidu/yq_oftg_fixed12_s2/retained.json)
- [yq_oftg_fixed12_s2/round-01.json](results/baidu/yq_oftg_fixed12_s2/round-01.json)
- [yq_oftg_fixed12_s2/round-02.json](results/baidu/yq_oftg_fixed12_s2/round-02.json)
- [yq_oftg_fixed12_s2/round-03.json](results/baidu/yq_oftg_fixed12_s2/round-03.json)
- [yq_oftg_fixed12_s2/round-04.json](results/baidu/yq_oftg_fixed12_s2/round-04.json)
- [yq_oftg_fixed12_s2/round-05.json](results/baidu/yq_oftg_fixed12_s2/round-05.json)
- [yq_oftg_fixed12_s2/round-06.json](results/baidu/yq_oftg_fixed12_s2/round-06.json)
- [yq_oftg_fixed12_s2/round-07.json](results/baidu/yq_oftg_fixed12_s2/round-07.json)
- [yq_oftg_fixed12_s2/round-08.json](results/baidu/yq_oftg_fixed12_s2/round-08.json)
- [yq_oftg_fixed12_s2/round-09.json](results/baidu/yq_oftg_fixed12_s2/round-09.json)
- [yq_oftg_fixed12_s2/round-10.json](results/baidu/yq_oftg_fixed12_s2/round-10.json)
- [yq_oftg_fixed12_s2/round-11.json](results/baidu/yq_oftg_fixed12_s2/round-11.json)
- [yq_oftg_fixed12_s2/round-12.json](results/baidu/yq_oftg_fixed12_s2/round-12.json)
- [yq_oftg_fixed12_s2/tests.txt](results/baidu/yq_oftg_fixed12_s2/tests.txt)
- [yq_oftg_fixed12_s2_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s2-rep.job-f9w49ro5lnpz.txt](results/baidu/yq_oftg_fixed12_s2_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s2-rep.job-f9w49ro5lnpz.txt)
- [yq_oftg_fixed12_s2_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s2_rep/test_eval.json)
- [yq_oftg_fixed12_s2_rep/tests.txt](results/baidu/yq_oftg_fixed12_s2_rep/tests.txt)
- [yq_oftg_fixed12_s2_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s2-fresh.job-gfd93hdcxdzt.txt](results/baidu/yq_oftg_fixed12_s2_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s2-fresh.job-gfd93hdcxdzt.txt)
- [yq_oftg_fixed12_s2_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s2_fresh/test_eval.json)
- [yq_oftg_fixed12_s2_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s2_fresh/tests.txt)

### yq_oftg_fixed12_s3

- official：57.8000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_oftg_fixed12_s3/tests.txt)
- official：58.8000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s3_rep/tests.txt)
- official：59.4000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_oftg_fixed12_s3_rep/tests.txt)
- fresh：62.9000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_oftg_fixed12_s3_fresh/tests.txt)

完整文件：

- [yq_oftg_fixed12_s3/SOURCE-zw-rsi-yq-oftg-fixed12-s3.job-k78fwx973q5g.txt](results/baidu/yq_oftg_fixed12_s3/SOURCE-zw-rsi-yq-oftg-fixed12-s3.job-k78fwx973q5g.txt)
- [yq_oftg_fixed12_s3/accepted.jsonl](results/baidu/yq_oftg_fixed12_s3/accepted.jsonl)
- [yq_oftg_fixed12_s3/backend-accounting.json](results/baidu/yq_oftg_fixed12_s3/backend-accounting.json)
- [yq_oftg_fixed12_s3/report.json](results/baidu/yq_oftg_fixed12_s3/report.json)
- [yq_oftg_fixed12_s3/retained.json](results/baidu/yq_oftg_fixed12_s3/retained.json)
- [yq_oftg_fixed12_s3/round-01.json](results/baidu/yq_oftg_fixed12_s3/round-01.json)
- [yq_oftg_fixed12_s3/round-02.json](results/baidu/yq_oftg_fixed12_s3/round-02.json)
- [yq_oftg_fixed12_s3/round-03.json](results/baidu/yq_oftg_fixed12_s3/round-03.json)
- [yq_oftg_fixed12_s3/round-04.json](results/baidu/yq_oftg_fixed12_s3/round-04.json)
- [yq_oftg_fixed12_s3/round-05.json](results/baidu/yq_oftg_fixed12_s3/round-05.json)
- [yq_oftg_fixed12_s3/round-06.json](results/baidu/yq_oftg_fixed12_s3/round-06.json)
- [yq_oftg_fixed12_s3/round-07.json](results/baidu/yq_oftg_fixed12_s3/round-07.json)
- [yq_oftg_fixed12_s3/round-08.json](results/baidu/yq_oftg_fixed12_s3/round-08.json)
- [yq_oftg_fixed12_s3/round-09.json](results/baidu/yq_oftg_fixed12_s3/round-09.json)
- [yq_oftg_fixed12_s3/round-10.json](results/baidu/yq_oftg_fixed12_s3/round-10.json)
- [yq_oftg_fixed12_s3/round-11.json](results/baidu/yq_oftg_fixed12_s3/round-11.json)
- [yq_oftg_fixed12_s3/round-12.json](results/baidu/yq_oftg_fixed12_s3/round-12.json)
- [yq_oftg_fixed12_s3/tests.txt](results/baidu/yq_oftg_fixed12_s3/tests.txt)
- [yq_oftg_fixed12_s3_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s3-rep.job-ixtcsdlekh96.txt](results/baidu/yq_oftg_fixed12_s3_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s3-rep.job-ixtcsdlekh96.txt)
- [yq_oftg_fixed12_s3_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s3_rep/test_eval.json)
- [yq_oftg_fixed12_s3_rep/tests.txt](results/baidu/yq_oftg_fixed12_s3_rep/tests.txt)
- [yq_oftg_fixed12_s3_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s3-fresh.job-jqz4jr4pcsnh.txt](results/baidu/yq_oftg_fixed12_s3_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s3-fresh.job-jqz4jr4pcsnh.txt)
- [yq_oftg_fixed12_s3_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s3_fresh/test_eval.json)
- [yq_oftg_fixed12_s3_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s3_fresh/tests.txt)

### yq_oftg_nonrec12_s1

- official：49.2000%；[test-libero_official-r07c0.jsonl](results/baidu/yq_oftg_nonrec12_s1/tests.txt)
- official：49.0000%；[test-libero_official-r07c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s1_rep/tests.txt)
- official：46.4000%；[test-libero_official-r07c0-rep2.jsonl](results/baidu/yq_oftg_nonrec12_s1_rep/tests.txt)
- fresh：52.7000%；[test-libero_fresh-r07c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s1_fresh/tests.txt)

完整文件：

- [yq_oftg_nonrec12_s1/SOURCE-zw-rsi-yq-oftg-nonrec12-s1.job-0rxnjw9qyo3b.txt](results/baidu/yq_oftg_nonrec12_s1/SOURCE-zw-rsi-yq-oftg-nonrec12-s1.job-0rxnjw9qyo3b.txt)
- [yq_oftg_nonrec12_s1/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s1/accepted.jsonl)
- [yq_oftg_nonrec12_s1/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s1/backend-accounting.json)
- [yq_oftg_nonrec12_s1/report.json](results/baidu/yq_oftg_nonrec12_s1/report.json)
- [yq_oftg_nonrec12_s1/retained.json](results/baidu/yq_oftg_nonrec12_s1/retained.json)
- [yq_oftg_nonrec12_s1/round-01.json](results/baidu/yq_oftg_nonrec12_s1/round-01.json)
- [yq_oftg_nonrec12_s1/round-02.json](results/baidu/yq_oftg_nonrec12_s1/round-02.json)
- [yq_oftg_nonrec12_s1/round-03.json](results/baidu/yq_oftg_nonrec12_s1/round-03.json)
- [yq_oftg_nonrec12_s1/round-04.json](results/baidu/yq_oftg_nonrec12_s1/round-04.json)
- [yq_oftg_nonrec12_s1/round-05.json](results/baidu/yq_oftg_nonrec12_s1/round-05.json)
- [yq_oftg_nonrec12_s1/round-06.json](results/baidu/yq_oftg_nonrec12_s1/round-06.json)
- [yq_oftg_nonrec12_s1/round-07.json](results/baidu/yq_oftg_nonrec12_s1/round-07.json)
- [yq_oftg_nonrec12_s1/round-08.json](results/baidu/yq_oftg_nonrec12_s1/round-08.json)
- [yq_oftg_nonrec12_s1/round-09.json](results/baidu/yq_oftg_nonrec12_s1/round-09.json)
- [yq_oftg_nonrec12_s1/round-10.json](results/baidu/yq_oftg_nonrec12_s1/round-10.json)
- [yq_oftg_nonrec12_s1/round-11.json](results/baidu/yq_oftg_nonrec12_s1/round-11.json)
- [yq_oftg_nonrec12_s1/round-12.json](results/baidu/yq_oftg_nonrec12_s1/round-12.json)
- [yq_oftg_nonrec12_s1/tests.txt](results/baidu/yq_oftg_nonrec12_s1/tests.txt)
- [yq_oftg_nonrec12_s1_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-rep.job-vvdd8wfs8t11.txt](results/baidu/yq_oftg_nonrec12_s1_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-rep.job-vvdd8wfs8t11.txt)
- [yq_oftg_nonrec12_s1_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s1_rep/test_eval.json)
- [yq_oftg_nonrec12_s1_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s1_rep/tests.txt)
- [yq_oftg_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-fresh.job-03xakji40m9y.txt](results/baidu/yq_oftg_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-fresh.job-03xakji40m9y.txt)
- [yq_oftg_nonrec12_s1_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s1_fresh/test_eval.json)
- [yq_oftg_nonrec12_s1_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s1_fresh/tests.txt)

### yq_oftg_nonrec12_s2

- official：55.4000%；[test-libero_official-r08c0.jsonl](results/baidu/yq_oftg_nonrec12_s2/tests.txt)
- official：55.4000%；[test-libero_official-r08c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s2_rep/tests.txt)
- official：55.4000%；[test-libero_official-r08c0-rep2.jsonl](results/baidu/yq_oftg_nonrec12_s2_rep/tests.txt)
- fresh：59.5000%；[test-libero_fresh-r08c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s2_fresh/tests.txt)

完整文件：

- [yq_oftg_nonrec12_s2/SOURCE-zw-rsi-yq-oftg-nonrec12-s2.job-vimuv3tfi095.txt](results/baidu/yq_oftg_nonrec12_s2/SOURCE-zw-rsi-yq-oftg-nonrec12-s2.job-vimuv3tfi095.txt)
- [yq_oftg_nonrec12_s2/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s2/accepted.jsonl)
- [yq_oftg_nonrec12_s2/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s2/backend-accounting.json)
- [yq_oftg_nonrec12_s2/report.json](results/baidu/yq_oftg_nonrec12_s2/report.json)
- [yq_oftg_nonrec12_s2/retained.json](results/baidu/yq_oftg_nonrec12_s2/retained.json)
- [yq_oftg_nonrec12_s2/round-01.json](results/baidu/yq_oftg_nonrec12_s2/round-01.json)
- [yq_oftg_nonrec12_s2/round-02.json](results/baidu/yq_oftg_nonrec12_s2/round-02.json)
- [yq_oftg_nonrec12_s2/round-03.json](results/baidu/yq_oftg_nonrec12_s2/round-03.json)
- [yq_oftg_nonrec12_s2/round-04.json](results/baidu/yq_oftg_nonrec12_s2/round-04.json)
- [yq_oftg_nonrec12_s2/round-05.json](results/baidu/yq_oftg_nonrec12_s2/round-05.json)
- [yq_oftg_nonrec12_s2/round-06.json](results/baidu/yq_oftg_nonrec12_s2/round-06.json)
- [yq_oftg_nonrec12_s2/round-07.json](results/baidu/yq_oftg_nonrec12_s2/round-07.json)
- [yq_oftg_nonrec12_s2/round-08.json](results/baidu/yq_oftg_nonrec12_s2/round-08.json)
- [yq_oftg_nonrec12_s2/round-09.json](results/baidu/yq_oftg_nonrec12_s2/round-09.json)
- [yq_oftg_nonrec12_s2/round-10.json](results/baidu/yq_oftg_nonrec12_s2/round-10.json)
- [yq_oftg_nonrec12_s2/round-11.json](results/baidu/yq_oftg_nonrec12_s2/round-11.json)
- [yq_oftg_nonrec12_s2/round-12.json](results/baidu/yq_oftg_nonrec12_s2/round-12.json)
- [yq_oftg_nonrec12_s2/tests.txt](results/baidu/yq_oftg_nonrec12_s2/tests.txt)
- [yq_oftg_nonrec12_s2_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-rep.job-im0tp5uo0q19.txt](results/baidu/yq_oftg_nonrec12_s2_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-rep.job-im0tp5uo0q19.txt)
- [yq_oftg_nonrec12_s2_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s2_rep/test_eval.json)
- [yq_oftg_nonrec12_s2_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s2_rep/tests.txt)
- [yq_oftg_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-fresh.job-h4q9k8hyyghe.txt](results/baidu/yq_oftg_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-fresh.job-h4q9k8hyyghe.txt)
- [yq_oftg_nonrec12_s2_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s2_fresh/test_eval.json)
- [yq_oftg_nonrec12_s2_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s2_fresh/tests.txt)

### yq_oftg_nonrec12_s3

- official：55.2000%；[test-libero_official-r10c0.jsonl](results/baidu/yq_oftg_nonrec12_s3/tests.txt)
- official：54.0000%；[test-libero_official-r10c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s3_rep/tests.txt)
- official：54.2000%；[test-libero_official-r10c0-rep2.jsonl](results/baidu/yq_oftg_nonrec12_s3_rep/tests.txt)
- fresh：56.6000%；[test-libero_fresh-r10c0-rep1.jsonl](results/baidu/yq_oftg_nonrec12_s3_fresh/tests.txt)

完整文件：

- [yq_oftg_nonrec12_s3/SOURCE-zw-rsi-yq-oftg-nonrec12-s3.job-861rdqeyr9wn.txt](results/baidu/yq_oftg_nonrec12_s3/SOURCE-zw-rsi-yq-oftg-nonrec12-s3.job-861rdqeyr9wn.txt)
- [yq_oftg_nonrec12_s3/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s3/accepted.jsonl)
- [yq_oftg_nonrec12_s3/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s3/backend-accounting.json)
- [yq_oftg_nonrec12_s3/report.json](results/baidu/yq_oftg_nonrec12_s3/report.json)
- [yq_oftg_nonrec12_s3/retained.json](results/baidu/yq_oftg_nonrec12_s3/retained.json)
- [yq_oftg_nonrec12_s3/round-01.json](results/baidu/yq_oftg_nonrec12_s3/round-01.json)
- [yq_oftg_nonrec12_s3/round-02.json](results/baidu/yq_oftg_nonrec12_s3/round-02.json)
- [yq_oftg_nonrec12_s3/round-03.json](results/baidu/yq_oftg_nonrec12_s3/round-03.json)
- [yq_oftg_nonrec12_s3/round-04.json](results/baidu/yq_oftg_nonrec12_s3/round-04.json)
- [yq_oftg_nonrec12_s3/round-05.json](results/baidu/yq_oftg_nonrec12_s3/round-05.json)
- [yq_oftg_nonrec12_s3/round-06.json](results/baidu/yq_oftg_nonrec12_s3/round-06.json)
- [yq_oftg_nonrec12_s3/round-07.json](results/baidu/yq_oftg_nonrec12_s3/round-07.json)
- [yq_oftg_nonrec12_s3/round-08.json](results/baidu/yq_oftg_nonrec12_s3/round-08.json)
- [yq_oftg_nonrec12_s3/round-09.json](results/baidu/yq_oftg_nonrec12_s3/round-09.json)
- [yq_oftg_nonrec12_s3/round-10.json](results/baidu/yq_oftg_nonrec12_s3/round-10.json)
- [yq_oftg_nonrec12_s3/round-11.json](results/baidu/yq_oftg_nonrec12_s3/round-11.json)
- [yq_oftg_nonrec12_s3/round-12.json](results/baidu/yq_oftg_nonrec12_s3/round-12.json)
- [yq_oftg_nonrec12_s3/tests.txt](results/baidu/yq_oftg_nonrec12_s3/tests.txt)
- [yq_oftg_nonrec12_s3_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-rep.job-g0rmg6m8b6dg.txt](results/baidu/yq_oftg_nonrec12_s3_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-rep.job-g0rmg6m8b6dg.txt)
- [yq_oftg_nonrec12_s3_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s3_rep/test_eval.json)
- [yq_oftg_nonrec12_s3_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s3_rep/tests.txt)
- [yq_oftg_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-fresh.job-c5qq35d02lnf.txt](results/baidu/yq_oftg_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-fresh.job-c5qq35d02lnf.txt)
- [yq_oftg_nonrec12_s3_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s3_fresh/test_eval.json)
- [yq_oftg_nonrec12_s3_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s3_fresh/tests.txt)

### yq_oftg_guard12_s1

- official：61.6000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_oftg_guard12_s1/tests.txt)
- official：61.0000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s1_rep/tests.txt)
- official：60.2000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_oftg_guard12_s1_rep/tests.txt)
- fresh：66.9000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s1_fresh/tests.txt)

完整文件：

- [yq_oftg_guard12_s1/SOURCE-zw-rsi-yq-oftg-guard12-s1.job-46g4mwxzzj65.txt](results/baidu/yq_oftg_guard12_s1/SOURCE-zw-rsi-yq-oftg-guard12-s1.job-46g4mwxzzj65.txt)
- [yq_oftg_guard12_s1/accepted.jsonl](results/baidu/yq_oftg_guard12_s1/accepted.jsonl)
- [yq_oftg_guard12_s1/backend-accounting.json](results/baidu/yq_oftg_guard12_s1/backend-accounting.json)
- [yq_oftg_guard12_s1/report.json](results/baidu/yq_oftg_guard12_s1/report.json)
- [yq_oftg_guard12_s1/retained.json](results/baidu/yq_oftg_guard12_s1/retained.json)
- [yq_oftg_guard12_s1/round-01.json](results/baidu/yq_oftg_guard12_s1/round-01.json)
- [yq_oftg_guard12_s1/round-02.json](results/baidu/yq_oftg_guard12_s1/round-02.json)
- [yq_oftg_guard12_s1/round-03.json](results/baidu/yq_oftg_guard12_s1/round-03.json)
- [yq_oftg_guard12_s1/round-04.json](results/baidu/yq_oftg_guard12_s1/round-04.json)
- [yq_oftg_guard12_s1/round-05.json](results/baidu/yq_oftg_guard12_s1/round-05.json)
- [yq_oftg_guard12_s1/round-06.json](results/baidu/yq_oftg_guard12_s1/round-06.json)
- [yq_oftg_guard12_s1/round-07.json](results/baidu/yq_oftg_guard12_s1/round-07.json)
- [yq_oftg_guard12_s1/round-08.json](results/baidu/yq_oftg_guard12_s1/round-08.json)
- [yq_oftg_guard12_s1/round-09.json](results/baidu/yq_oftg_guard12_s1/round-09.json)
- [yq_oftg_guard12_s1/round-10.json](results/baidu/yq_oftg_guard12_s1/round-10.json)
- [yq_oftg_guard12_s1/round-11.json](results/baidu/yq_oftg_guard12_s1/round-11.json)
- [yq_oftg_guard12_s1/round-12.json](results/baidu/yq_oftg_guard12_s1/round-12.json)
- [yq_oftg_guard12_s1/tests.txt](results/baidu/yq_oftg_guard12_s1/tests.txt)
- [yq_oftg_guard12_s1_rep/SOURCE-zw-rsi-yq-oftg-guard12-s1-rep.job-g8829gvuihs9.txt](results/baidu/yq_oftg_guard12_s1_rep/SOURCE-zw-rsi-yq-oftg-guard12-s1-rep.job-g8829gvuihs9.txt)
- [yq_oftg_guard12_s1_rep/test_eval.json](results/baidu/yq_oftg_guard12_s1_rep/test_eval.json)
- [yq_oftg_guard12_s1_rep/tests.txt](results/baidu/yq_oftg_guard12_s1_rep/tests.txt)
- [yq_oftg_guard12_s1_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s1-fresh.job-cle5ddrzjg69.txt](results/baidu/yq_oftg_guard12_s1_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s1-fresh.job-cle5ddrzjg69.txt)
- [yq_oftg_guard12_s1_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s1_fresh/test_eval.json)
- [yq_oftg_guard12_s1_fresh/tests.txt](results/baidu/yq_oftg_guard12_s1_fresh/tests.txt)

### yq_oftg_guard12_s2

- official：61.8000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_oftg_guard12_s2/tests.txt)
- official：62.2000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s2_rep/tests.txt)
- official：62.8000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_oftg_guard12_s2_rep/tests.txt)
- fresh：64.9000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s2_fresh/tests.txt)

完整文件：

- [yq_oftg_guard12_s2/SOURCE-zw-rsi-yq-oftg-guard12-s2.job-8w8ooykxt485.txt](results/baidu/yq_oftg_guard12_s2/SOURCE-zw-rsi-yq-oftg-guard12-s2.job-8w8ooykxt485.txt)
- [yq_oftg_guard12_s2/accepted.jsonl](results/baidu/yq_oftg_guard12_s2/accepted.jsonl)
- [yq_oftg_guard12_s2/backend-accounting.json](results/baidu/yq_oftg_guard12_s2/backend-accounting.json)
- [yq_oftg_guard12_s2/report.json](results/baidu/yq_oftg_guard12_s2/report.json)
- [yq_oftg_guard12_s2/retained.json](results/baidu/yq_oftg_guard12_s2/retained.json)
- [yq_oftg_guard12_s2/round-01.json](results/baidu/yq_oftg_guard12_s2/round-01.json)
- [yq_oftg_guard12_s2/round-02.json](results/baidu/yq_oftg_guard12_s2/round-02.json)
- [yq_oftg_guard12_s2/round-03.json](results/baidu/yq_oftg_guard12_s2/round-03.json)
- [yq_oftg_guard12_s2/round-04.json](results/baidu/yq_oftg_guard12_s2/round-04.json)
- [yq_oftg_guard12_s2/round-05.json](results/baidu/yq_oftg_guard12_s2/round-05.json)
- [yq_oftg_guard12_s2/round-06.json](results/baidu/yq_oftg_guard12_s2/round-06.json)
- [yq_oftg_guard12_s2/round-07.json](results/baidu/yq_oftg_guard12_s2/round-07.json)
- [yq_oftg_guard12_s2/round-08.json](results/baidu/yq_oftg_guard12_s2/round-08.json)
- [yq_oftg_guard12_s2/round-09.json](results/baidu/yq_oftg_guard12_s2/round-09.json)
- [yq_oftg_guard12_s2/round-10.json](results/baidu/yq_oftg_guard12_s2/round-10.json)
- [yq_oftg_guard12_s2/round-11.json](results/baidu/yq_oftg_guard12_s2/round-11.json)
- [yq_oftg_guard12_s2/round-12.json](results/baidu/yq_oftg_guard12_s2/round-12.json)
- [yq_oftg_guard12_s2/tests.txt](results/baidu/yq_oftg_guard12_s2/tests.txt)
- [yq_oftg_guard12_s2_rep/SOURCE-zw-rsi-yq-oftg-guard12-s2-rep.job-dv5ul4k9h33s.txt](results/baidu/yq_oftg_guard12_s2_rep/SOURCE-zw-rsi-yq-oftg-guard12-s2-rep.job-dv5ul4k9h33s.txt)
- [yq_oftg_guard12_s2_rep/test_eval.json](results/baidu/yq_oftg_guard12_s2_rep/test_eval.json)
- [yq_oftg_guard12_s2_rep/tests.txt](results/baidu/yq_oftg_guard12_s2_rep/tests.txt)
- [yq_oftg_guard12_s2_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s2-fresh.job-3f8xq9d51qhd.txt](results/baidu/yq_oftg_guard12_s2_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s2-fresh.job-3f8xq9d51qhd.txt)
- [yq_oftg_guard12_s2_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s2_fresh/test_eval.json)
- [yq_oftg_guard12_s2_fresh/tests.txt](results/baidu/yq_oftg_guard12_s2_fresh/tests.txt)

### yq_oftg_guard12_s3

- official：60.8000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_oftg_guard12_s3/tests.txt)
- official：60.8000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s3_rep/tests.txt)
- official：61.6000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_oftg_guard12_s3_rep/tests.txt)
- fresh：63.9000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_oftg_guard12_s3_fresh/tests.txt)

完整文件：

- [yq_oftg_guard12_s3/SOURCE-zw-rsi-yq-oftg-guard12-s3.job-x05nk03gups9.txt](results/baidu/yq_oftg_guard12_s3/SOURCE-zw-rsi-yq-oftg-guard12-s3.job-x05nk03gups9.txt)
- [yq_oftg_guard12_s3/accepted.jsonl](results/baidu/yq_oftg_guard12_s3/accepted.jsonl)
- [yq_oftg_guard12_s3/backend-accounting.json](results/baidu/yq_oftg_guard12_s3/backend-accounting.json)
- [yq_oftg_guard12_s3/report.json](results/baidu/yq_oftg_guard12_s3/report.json)
- [yq_oftg_guard12_s3/retained.json](results/baidu/yq_oftg_guard12_s3/retained.json)
- [yq_oftg_guard12_s3/round-01.json](results/baidu/yq_oftg_guard12_s3/round-01.json)
- [yq_oftg_guard12_s3/round-02.json](results/baidu/yq_oftg_guard12_s3/round-02.json)
- [yq_oftg_guard12_s3/round-03.json](results/baidu/yq_oftg_guard12_s3/round-03.json)
- [yq_oftg_guard12_s3/round-04.json](results/baidu/yq_oftg_guard12_s3/round-04.json)
- [yq_oftg_guard12_s3/round-05.json](results/baidu/yq_oftg_guard12_s3/round-05.json)
- [yq_oftg_guard12_s3/round-06.json](results/baidu/yq_oftg_guard12_s3/round-06.json)
- [yq_oftg_guard12_s3/round-07.json](results/baidu/yq_oftg_guard12_s3/round-07.json)
- [yq_oftg_guard12_s3/round-08.json](results/baidu/yq_oftg_guard12_s3/round-08.json)
- [yq_oftg_guard12_s3/round-09.json](results/baidu/yq_oftg_guard12_s3/round-09.json)
- [yq_oftg_guard12_s3/round-10.json](results/baidu/yq_oftg_guard12_s3/round-10.json)
- [yq_oftg_guard12_s3/round-11.json](results/baidu/yq_oftg_guard12_s3/round-11.json)
- [yq_oftg_guard12_s3/round-12.json](results/baidu/yq_oftg_guard12_s3/round-12.json)
- [yq_oftg_guard12_s3/tests.txt](results/baidu/yq_oftg_guard12_s3/tests.txt)
- [yq_oftg_guard12_s3_rep/SOURCE-zw-rsi-yq-oftg-guard12-s3-rep.job-r62fgnatvzcm.txt](results/baidu/yq_oftg_guard12_s3_rep/SOURCE-zw-rsi-yq-oftg-guard12-s3-rep.job-r62fgnatvzcm.txt)
- [yq_oftg_guard12_s3_rep/test_eval.json](results/baidu/yq_oftg_guard12_s3_rep/test_eval.json)
- [yq_oftg_guard12_s3_rep/tests.txt](results/baidu/yq_oftg_guard12_s3_rep/tests.txt)
- [yq_oftg_guard12_s3_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s3-fresh.job-qrfb9r7l1wz8.txt](results/baidu/yq_oftg_guard12_s3_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s3-fresh.job-qrfb9r7l1wz8.txt)
- [yq_oftg_guard12_s3_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s3_fresh/test_eval.json)
- [yq_oftg_guard12_s3_fresh/tests.txt](results/baidu/yq_oftg_guard12_s3_fresh/tests.txt)

### yq_ofts_fixed12_s1

- official：59.8000%；[test-libero_official-r11c0.jsonl](results/baidu/yq_ofts_fixed12_s1/tests.txt)
- official：60.2000%；[test-libero_official-r11c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s1_rep/tests.txt)
- official：60.6000%；[test-libero_official-r11c0-rep2.jsonl](results/baidu/yq_ofts_fixed12_s1_rep/tests.txt)
- fresh：66.5000%；[test-libero_fresh-r11c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s1_fresh/tests.txt)

完整文件：

- [yq_ofts_fixed12_s1/SOURCE-zw-rsi-yq-ofts-fixed12-s1.job-1otcxo4s5vwd.txt](results/baidu/yq_ofts_fixed12_s1/SOURCE-zw-rsi-yq-ofts-fixed12-s1.job-1otcxo4s5vwd.txt)
- [yq_ofts_fixed12_s1/accepted.jsonl](results/baidu/yq_ofts_fixed12_s1/accepted.jsonl)
- [yq_ofts_fixed12_s1/backend-accounting.json](results/baidu/yq_ofts_fixed12_s1/backend-accounting.json)
- [yq_ofts_fixed12_s1/report.json](results/baidu/yq_ofts_fixed12_s1/report.json)
- [yq_ofts_fixed12_s1/retained.json](results/baidu/yq_ofts_fixed12_s1/retained.json)
- [yq_ofts_fixed12_s1/round-01.json](results/baidu/yq_ofts_fixed12_s1/round-01.json)
- [yq_ofts_fixed12_s1/round-02.json](results/baidu/yq_ofts_fixed12_s1/round-02.json)
- [yq_ofts_fixed12_s1/round-03.json](results/baidu/yq_ofts_fixed12_s1/round-03.json)
- [yq_ofts_fixed12_s1/round-04.json](results/baidu/yq_ofts_fixed12_s1/round-04.json)
- [yq_ofts_fixed12_s1/round-05.json](results/baidu/yq_ofts_fixed12_s1/round-05.json)
- [yq_ofts_fixed12_s1/round-06.json](results/baidu/yq_ofts_fixed12_s1/round-06.json)
- [yq_ofts_fixed12_s1/round-07.json](results/baidu/yq_ofts_fixed12_s1/round-07.json)
- [yq_ofts_fixed12_s1/round-08.json](results/baidu/yq_ofts_fixed12_s1/round-08.json)
- [yq_ofts_fixed12_s1/round-09.json](results/baidu/yq_ofts_fixed12_s1/round-09.json)
- [yq_ofts_fixed12_s1/round-10.json](results/baidu/yq_ofts_fixed12_s1/round-10.json)
- [yq_ofts_fixed12_s1/round-11.json](results/baidu/yq_ofts_fixed12_s1/round-11.json)
- [yq_ofts_fixed12_s1/round-12.json](results/baidu/yq_ofts_fixed12_s1/round-12.json)
- [yq_ofts_fixed12_s1/tests.txt](results/baidu/yq_ofts_fixed12_s1/tests.txt)
- [yq_ofts_fixed12_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s1-rep.job-px62coa58zi7.txt](results/baidu/yq_ofts_fixed12_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s1-rep.job-px62coa58zi7.txt)
- [yq_ofts_fixed12_s1_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s1_rep/test_eval.json)
- [yq_ofts_fixed12_s1_rep/tests.txt](results/baidu/yq_ofts_fixed12_s1_rep/tests.txt)
- [yq_ofts_fixed12_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s1-fresh.job-600ejaiwjb22.txt](results/baidu/yq_ofts_fixed12_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s1-fresh.job-600ejaiwjb22.txt)
- [yq_ofts_fixed12_s1_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s1_fresh/test_eval.json)
- [yq_ofts_fixed12_s1_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s1_fresh/tests.txt)

### yq_ofts_fixed12_s2

- official：63.4000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_ofts_fixed12_s2/tests.txt)
- official：64.4000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s2_rep/tests.txt)
- official：63.4000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_ofts_fixed12_s2_rep/tests.txt)
- fresh：69.1000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s2_fresh/tests.txt)

完整文件：

- [yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-kbdj1wgyi9jf.txt](results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-kbdj1wgyi9jf.txt)
- [yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-tvlypjmv56ku.txt](results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-tvlypjmv56ku.txt)
- [yq_ofts_fixed12_s2/accepted.jsonl](results/baidu/yq_ofts_fixed12_s2/accepted.jsonl)
- [yq_ofts_fixed12_s2/backend-accounting.json](results/baidu/yq_ofts_fixed12_s2/backend-accounting.json)
- [yq_ofts_fixed12_s2/failure.json](results/baidu/yq_ofts_fixed12_s2/failure.json)
- [yq_ofts_fixed12_s2/report.json](results/baidu/yq_ofts_fixed12_s2/report.json)
- [yq_ofts_fixed12_s2/retained.json](results/baidu/yq_ofts_fixed12_s2/retained.json)
- [yq_ofts_fixed12_s2/round-01.json](results/baidu/yq_ofts_fixed12_s2/round-01.json)
- [yq_ofts_fixed12_s2/round-02.json](results/baidu/yq_ofts_fixed12_s2/round-02.json)
- [yq_ofts_fixed12_s2/round-03.json](results/baidu/yq_ofts_fixed12_s2/round-03.json)
- [yq_ofts_fixed12_s2/round-04.json](results/baidu/yq_ofts_fixed12_s2/round-04.json)
- [yq_ofts_fixed12_s2/round-05.json](results/baidu/yq_ofts_fixed12_s2/round-05.json)
- [yq_ofts_fixed12_s2/round-06.json](results/baidu/yq_ofts_fixed12_s2/round-06.json)
- [yq_ofts_fixed12_s2/round-07.json](results/baidu/yq_ofts_fixed12_s2/round-07.json)
- [yq_ofts_fixed12_s2/round-08.json](results/baidu/yq_ofts_fixed12_s2/round-08.json)
- [yq_ofts_fixed12_s2/round-09.json](results/baidu/yq_ofts_fixed12_s2/round-09.json)
- [yq_ofts_fixed12_s2/round-10.json](results/baidu/yq_ofts_fixed12_s2/round-10.json)
- [yq_ofts_fixed12_s2/round-11.json](results/baidu/yq_ofts_fixed12_s2/round-11.json)
- [yq_ofts_fixed12_s2/round-12.json](results/baidu/yq_ofts_fixed12_s2/round-12.json)
- [yq_ofts_fixed12_s2/tests.txt](results/baidu/yq_ofts_fixed12_s2/tests.txt)
- [yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-20z213xryeb5.txt](results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-20z213xryeb5.txt)
- [yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-rmpuwh4lnr4p.txt](results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-rmpuwh4lnr4p.txt)
- [yq_ofts_fixed12_s2_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s2_rep/test_eval.json)
- [yq_ofts_fixed12_s2_rep/tests.txt](results/baidu/yq_ofts_fixed12_s2_rep/tests.txt)
- [yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-1gqg5wmyeipn.txt](results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-1gqg5wmyeipn.txt)
- [yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-orzet31zji4n.txt](results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-orzet31zji4n.txt)
- [yq_ofts_fixed12_s2_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s2_fresh/test_eval.json)
- [yq_ofts_fixed12_s2_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s2_fresh/tests.txt)

### yq_ofts_fixed12_s3

- official：58.4000%；[test-libero_official-r09c0.jsonl](results/baidu/yq_ofts_fixed12_s3/tests.txt)
- official：59.6000%；[test-libero_official-r09c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s3_rep/tests.txt)
- official：59.6000%；[test-libero_official-r09c0-rep2.jsonl](results/baidu/yq_ofts_fixed12_s3_rep/tests.txt)
- fresh：65.2000%；[test-libero_fresh-r09c0-rep1.jsonl](results/baidu/yq_ofts_fixed12_s3_fresh/tests.txt)

完整文件：

- [yq_ofts_fixed12_s3/SOURCE-zw-rsi-yq-ofts-fixed12-s3.job-crj8uah8diwr.txt](results/baidu/yq_ofts_fixed12_s3/SOURCE-zw-rsi-yq-ofts-fixed12-s3.job-crj8uah8diwr.txt)
- [yq_ofts_fixed12_s3/accepted.jsonl](results/baidu/yq_ofts_fixed12_s3/accepted.jsonl)
- [yq_ofts_fixed12_s3/backend-accounting.json](results/baidu/yq_ofts_fixed12_s3/backend-accounting.json)
- [yq_ofts_fixed12_s3/report.json](results/baidu/yq_ofts_fixed12_s3/report.json)
- [yq_ofts_fixed12_s3/retained.json](results/baidu/yq_ofts_fixed12_s3/retained.json)
- [yq_ofts_fixed12_s3/round-01.json](results/baidu/yq_ofts_fixed12_s3/round-01.json)
- [yq_ofts_fixed12_s3/round-02.json](results/baidu/yq_ofts_fixed12_s3/round-02.json)
- [yq_ofts_fixed12_s3/round-03.json](results/baidu/yq_ofts_fixed12_s3/round-03.json)
- [yq_ofts_fixed12_s3/round-04.json](results/baidu/yq_ofts_fixed12_s3/round-04.json)
- [yq_ofts_fixed12_s3/round-05.json](results/baidu/yq_ofts_fixed12_s3/round-05.json)
- [yq_ofts_fixed12_s3/round-06.json](results/baidu/yq_ofts_fixed12_s3/round-06.json)
- [yq_ofts_fixed12_s3/round-07.json](results/baidu/yq_ofts_fixed12_s3/round-07.json)
- [yq_ofts_fixed12_s3/round-08.json](results/baidu/yq_ofts_fixed12_s3/round-08.json)
- [yq_ofts_fixed12_s3/round-09.json](results/baidu/yq_ofts_fixed12_s3/round-09.json)
- [yq_ofts_fixed12_s3/round-10.json](results/baidu/yq_ofts_fixed12_s3/round-10.json)
- [yq_ofts_fixed12_s3/round-11.json](results/baidu/yq_ofts_fixed12_s3/round-11.json)
- [yq_ofts_fixed12_s3/round-12.json](results/baidu/yq_ofts_fixed12_s3/round-12.json)
- [yq_ofts_fixed12_s3/tests.txt](results/baidu/yq_ofts_fixed12_s3/tests.txt)
- [yq_ofts_fixed12_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s3-rep.job-9g112ip74xjt.txt](results/baidu/yq_ofts_fixed12_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s3-rep.job-9g112ip74xjt.txt)
- [yq_ofts_fixed12_s3_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s3_rep/test_eval.json)
- [yq_ofts_fixed12_s3_rep/tests.txt](results/baidu/yq_ofts_fixed12_s3_rep/tests.txt)
- [yq_ofts_fixed12_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s3-fresh.job-bv4oak23ovma.txt](results/baidu/yq_ofts_fixed12_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s3-fresh.job-bv4oak23ovma.txt)
- [yq_ofts_fixed12_s3_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s3_fresh/test_eval.json)
- [yq_ofts_fixed12_s3_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s3_fresh/tests.txt)

### yq_ofts_nonrec12_s1

- official：50.2000%；[test-libero_official-r11c0.jsonl](results/baidu/yq_ofts_nonrec12_s1/tests.txt)
- official：49.8000%；[test-libero_official-r11c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s1_rep/tests.txt)
- official：49.4000%；[test-libero_official-r11c0-rep2.jsonl](results/baidu/yq_ofts_nonrec12_s1_rep/tests.txt)
- fresh：57.8000%；[test-libero_fresh-r11c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s1_fresh/tests.txt)

完整文件：

- [yq_ofts_nonrec12_s1/SOURCE-zw-rsi-yq-ofts-nonrec12-s1.job-e127wkwbtslp.txt](results/baidu/yq_ofts_nonrec12_s1/SOURCE-zw-rsi-yq-ofts-nonrec12-s1.job-e127wkwbtslp.txt)
- [yq_ofts_nonrec12_s1/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s1/accepted.jsonl)
- [yq_ofts_nonrec12_s1/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s1/backend-accounting.json)
- [yq_ofts_nonrec12_s1/report.json](results/baidu/yq_ofts_nonrec12_s1/report.json)
- [yq_ofts_nonrec12_s1/retained.json](results/baidu/yq_ofts_nonrec12_s1/retained.json)
- [yq_ofts_nonrec12_s1/round-01.json](results/baidu/yq_ofts_nonrec12_s1/round-01.json)
- [yq_ofts_nonrec12_s1/round-02.json](results/baidu/yq_ofts_nonrec12_s1/round-02.json)
- [yq_ofts_nonrec12_s1/round-03.json](results/baidu/yq_ofts_nonrec12_s1/round-03.json)
- [yq_ofts_nonrec12_s1/round-04.json](results/baidu/yq_ofts_nonrec12_s1/round-04.json)
- [yq_ofts_nonrec12_s1/round-05.json](results/baidu/yq_ofts_nonrec12_s1/round-05.json)
- [yq_ofts_nonrec12_s1/round-06.json](results/baidu/yq_ofts_nonrec12_s1/round-06.json)
- [yq_ofts_nonrec12_s1/round-07.json](results/baidu/yq_ofts_nonrec12_s1/round-07.json)
- [yq_ofts_nonrec12_s1/round-08.json](results/baidu/yq_ofts_nonrec12_s1/round-08.json)
- [yq_ofts_nonrec12_s1/round-09.json](results/baidu/yq_ofts_nonrec12_s1/round-09.json)
- [yq_ofts_nonrec12_s1/round-10.json](results/baidu/yq_ofts_nonrec12_s1/round-10.json)
- [yq_ofts_nonrec12_s1/round-11.json](results/baidu/yq_ofts_nonrec12_s1/round-11.json)
- [yq_ofts_nonrec12_s1/round-12.json](results/baidu/yq_ofts_nonrec12_s1/round-12.json)
- [yq_ofts_nonrec12_s1/tests.txt](results/baidu/yq_ofts_nonrec12_s1/tests.txt)
- [yq_ofts_nonrec12_s1_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-rep.job-2bdteuev4piw.txt](results/baidu/yq_ofts_nonrec12_s1_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-rep.job-2bdteuev4piw.txt)
- [yq_ofts_nonrec12_s1_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s1_rep/test_eval.json)
- [yq_ofts_nonrec12_s1_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s1_rep/tests.txt)
- [yq_ofts_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-fresh.job-mrccd8np8ayh.txt](results/baidu/yq_ofts_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-fresh.job-mrccd8np8ayh.txt)
- [yq_ofts_nonrec12_s1_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s1_fresh/test_eval.json)
- [yq_ofts_nonrec12_s1_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s1_fresh/tests.txt)

### yq_ofts_nonrec12_s2

- official：53.4000%；[test-libero_official-r11c0.jsonl](results/baidu/yq_ofts_nonrec12_s2/tests.txt)
- official：53.4000%；[test-libero_official-r11c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s2_rep/tests.txt)
- official：53.2000%；[test-libero_official-r11c0-rep2.jsonl](results/baidu/yq_ofts_nonrec12_s2_rep/tests.txt)
- fresh：59.0000%；[test-libero_fresh-r11c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s2_fresh/tests.txt)

完整文件：

- [yq_ofts_nonrec12_s2/SOURCE-zw-rsi-yq-ofts-nonrec12-s2.job-39fu9qgar97l.txt](results/baidu/yq_ofts_nonrec12_s2/SOURCE-zw-rsi-yq-ofts-nonrec12-s2.job-39fu9qgar97l.txt)
- [yq_ofts_nonrec12_s2/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s2/accepted.jsonl)
- [yq_ofts_nonrec12_s2/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s2/backend-accounting.json)
- [yq_ofts_nonrec12_s2/report.json](results/baidu/yq_ofts_nonrec12_s2/report.json)
- [yq_ofts_nonrec12_s2/retained.json](results/baidu/yq_ofts_nonrec12_s2/retained.json)
- [yq_ofts_nonrec12_s2/round-01.json](results/baidu/yq_ofts_nonrec12_s2/round-01.json)
- [yq_ofts_nonrec12_s2/round-02.json](results/baidu/yq_ofts_nonrec12_s2/round-02.json)
- [yq_ofts_nonrec12_s2/round-03.json](results/baidu/yq_ofts_nonrec12_s2/round-03.json)
- [yq_ofts_nonrec12_s2/round-04.json](results/baidu/yq_ofts_nonrec12_s2/round-04.json)
- [yq_ofts_nonrec12_s2/round-05.json](results/baidu/yq_ofts_nonrec12_s2/round-05.json)
- [yq_ofts_nonrec12_s2/round-06.json](results/baidu/yq_ofts_nonrec12_s2/round-06.json)
- [yq_ofts_nonrec12_s2/round-07.json](results/baidu/yq_ofts_nonrec12_s2/round-07.json)
- [yq_ofts_nonrec12_s2/round-08.json](results/baidu/yq_ofts_nonrec12_s2/round-08.json)
- [yq_ofts_nonrec12_s2/round-09.json](results/baidu/yq_ofts_nonrec12_s2/round-09.json)
- [yq_ofts_nonrec12_s2/round-10.json](results/baidu/yq_ofts_nonrec12_s2/round-10.json)
- [yq_ofts_nonrec12_s2/round-11.json](results/baidu/yq_ofts_nonrec12_s2/round-11.json)
- [yq_ofts_nonrec12_s2/round-12.json](results/baidu/yq_ofts_nonrec12_s2/round-12.json)
- [yq_ofts_nonrec12_s2/tests.txt](results/baidu/yq_ofts_nonrec12_s2/tests.txt)
- [yq_ofts_nonrec12_s2_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-rep.job-op4yrzyrlyqu.txt](results/baidu/yq_ofts_nonrec12_s2_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-rep.job-op4yrzyrlyqu.txt)
- [yq_ofts_nonrec12_s2_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s2_rep/test_eval.json)
- [yq_ofts_nonrec12_s2_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s2_rep/tests.txt)
- [yq_ofts_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-fresh.job-thdw5mb6fnte.txt](results/baidu/yq_ofts_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-fresh.job-thdw5mb6fnte.txt)
- [yq_ofts_nonrec12_s2_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s2_fresh/test_eval.json)
- [yq_ofts_nonrec12_s2_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s2_fresh/tests.txt)

### yq_ofts_nonrec12_s3

- official：54.2000%；[test-libero_official-r09c0.jsonl](results/baidu/yq_ofts_nonrec12_s3/tests.txt)
- official：54.4000%；[test-libero_official-r09c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s3_rep/tests.txt)
- official：53.4000%；[test-libero_official-r09c0-rep2.jsonl](results/baidu/yq_ofts_nonrec12_s3_rep/tests.txt)
- fresh：58.1000%；[test-libero_fresh-r09c0-rep1.jsonl](results/baidu/yq_ofts_nonrec12_s3_fresh/tests.txt)

完整文件：

- [yq_ofts_nonrec12_s3/SOURCE-zw-rsi-yq-ofts-nonrec12-s3.job-ict95os7arqd.txt](results/baidu/yq_ofts_nonrec12_s3/SOURCE-zw-rsi-yq-ofts-nonrec12-s3.job-ict95os7arqd.txt)
- [yq_ofts_nonrec12_s3/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s3/accepted.jsonl)
- [yq_ofts_nonrec12_s3/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s3/backend-accounting.json)
- [yq_ofts_nonrec12_s3/report.json](results/baidu/yq_ofts_nonrec12_s3/report.json)
- [yq_ofts_nonrec12_s3/retained.json](results/baidu/yq_ofts_nonrec12_s3/retained.json)
- [yq_ofts_nonrec12_s3/round-01.json](results/baidu/yq_ofts_nonrec12_s3/round-01.json)
- [yq_ofts_nonrec12_s3/round-02.json](results/baidu/yq_ofts_nonrec12_s3/round-02.json)
- [yq_ofts_nonrec12_s3/round-03.json](results/baidu/yq_ofts_nonrec12_s3/round-03.json)
- [yq_ofts_nonrec12_s3/round-04.json](results/baidu/yq_ofts_nonrec12_s3/round-04.json)
- [yq_ofts_nonrec12_s3/round-05.json](results/baidu/yq_ofts_nonrec12_s3/round-05.json)
- [yq_ofts_nonrec12_s3/round-06.json](results/baidu/yq_ofts_nonrec12_s3/round-06.json)
- [yq_ofts_nonrec12_s3/round-07.json](results/baidu/yq_ofts_nonrec12_s3/round-07.json)
- [yq_ofts_nonrec12_s3/round-08.json](results/baidu/yq_ofts_nonrec12_s3/round-08.json)
- [yq_ofts_nonrec12_s3/round-09.json](results/baidu/yq_ofts_nonrec12_s3/round-09.json)
- [yq_ofts_nonrec12_s3/round-10.json](results/baidu/yq_ofts_nonrec12_s3/round-10.json)
- [yq_ofts_nonrec12_s3/round-11.json](results/baidu/yq_ofts_nonrec12_s3/round-11.json)
- [yq_ofts_nonrec12_s3/round-12.json](results/baidu/yq_ofts_nonrec12_s3/round-12.json)
- [yq_ofts_nonrec12_s3/tests.txt](results/baidu/yq_ofts_nonrec12_s3/tests.txt)
- [yq_ofts_nonrec12_s3_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-rep.job-zpo155dwl114.txt](results/baidu/yq_ofts_nonrec12_s3_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-rep.job-zpo155dwl114.txt)
- [yq_ofts_nonrec12_s3_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s3_rep/test_eval.json)
- [yq_ofts_nonrec12_s3_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s3_rep/tests.txt)
- [yq_ofts_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-fresh.job-fwg744geev32.txt](results/baidu/yq_ofts_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-fresh.job-fwg744geev32.txt)
- [yq_ofts_nonrec12_s3_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s3_fresh/test_eval.json)
- [yq_ofts_nonrec12_s3_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s3_fresh/tests.txt)

### yq_ofts_guard12_s1

- official：62.4000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_ofts_guard12_s1/tests.txt)
- official：62.2000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s1_rep/tests.txt)
- official：62.4000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_ofts_guard12_s1_rep/tests.txt)
- fresh：69.9000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s1_fresh/tests.txt)

完整文件：

- [yq_ofts_guard12_s1/SOURCE-zw-rsi-yq-ofts-guard12-s1.job-vxncilkxz914.txt](results/baidu/yq_ofts_guard12_s1/SOURCE-zw-rsi-yq-ofts-guard12-s1.job-vxncilkxz914.txt)
- [yq_ofts_guard12_s1/accepted.jsonl](results/baidu/yq_ofts_guard12_s1/accepted.jsonl)
- [yq_ofts_guard12_s1/backend-accounting.json](results/baidu/yq_ofts_guard12_s1/backend-accounting.json)
- [yq_ofts_guard12_s1/report.json](results/baidu/yq_ofts_guard12_s1/report.json)
- [yq_ofts_guard12_s1/retained.json](results/baidu/yq_ofts_guard12_s1/retained.json)
- [yq_ofts_guard12_s1/round-01.json](results/baidu/yq_ofts_guard12_s1/round-01.json)
- [yq_ofts_guard12_s1/round-02.json](results/baidu/yq_ofts_guard12_s1/round-02.json)
- [yq_ofts_guard12_s1/round-03.json](results/baidu/yq_ofts_guard12_s1/round-03.json)
- [yq_ofts_guard12_s1/round-04.json](results/baidu/yq_ofts_guard12_s1/round-04.json)
- [yq_ofts_guard12_s1/round-05.json](results/baidu/yq_ofts_guard12_s1/round-05.json)
- [yq_ofts_guard12_s1/round-06.json](results/baidu/yq_ofts_guard12_s1/round-06.json)
- [yq_ofts_guard12_s1/round-07.json](results/baidu/yq_ofts_guard12_s1/round-07.json)
- [yq_ofts_guard12_s1/round-08.json](results/baidu/yq_ofts_guard12_s1/round-08.json)
- [yq_ofts_guard12_s1/round-09.json](results/baidu/yq_ofts_guard12_s1/round-09.json)
- [yq_ofts_guard12_s1/round-10.json](results/baidu/yq_ofts_guard12_s1/round-10.json)
- [yq_ofts_guard12_s1/round-11.json](results/baidu/yq_ofts_guard12_s1/round-11.json)
- [yq_ofts_guard12_s1/round-12.json](results/baidu/yq_ofts_guard12_s1/round-12.json)
- [yq_ofts_guard12_s1/tests.txt](results/baidu/yq_ofts_guard12_s1/tests.txt)
- [yq_ofts_guard12_s1_rep/SOURCE-zw-rsi-yq-ofts-guard12-s1-rep.job-8zq1r1mjtap2.txt](results/baidu/yq_ofts_guard12_s1_rep/SOURCE-zw-rsi-yq-ofts-guard12-s1-rep.job-8zq1r1mjtap2.txt)
- [yq_ofts_guard12_s1_rep/test_eval.json](results/baidu/yq_ofts_guard12_s1_rep/test_eval.json)
- [yq_ofts_guard12_s1_rep/tests.txt](results/baidu/yq_ofts_guard12_s1_rep/tests.txt)
- [yq_ofts_guard12_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s1-fresh.job-090oepab6ngy.txt](results/baidu/yq_ofts_guard12_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s1-fresh.job-090oepab6ngy.txt)
- [yq_ofts_guard12_s1_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s1_fresh/test_eval.json)
- [yq_ofts_guard12_s1_fresh/tests.txt](results/baidu/yq_ofts_guard12_s1_fresh/tests.txt)

### yq_ofts_guard12_s2

- official：60.6000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_ofts_guard12_s2/tests.txt)
- official：62.6000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s2_rep/tests.txt)
- official：60.2000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_ofts_guard12_s2_rep/tests.txt)
- fresh：68.7000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s2_fresh/tests.txt)

完整文件：

- [yq_ofts_guard12_s2/SOURCE-zw-rsi-yq-ofts-guard12-s2.job-grh5jdus447h.txt](results/baidu/yq_ofts_guard12_s2/SOURCE-zw-rsi-yq-ofts-guard12-s2.job-grh5jdus447h.txt)
- [yq_ofts_guard12_s2/accepted.jsonl](results/baidu/yq_ofts_guard12_s2/accepted.jsonl)
- [yq_ofts_guard12_s2/backend-accounting.json](results/baidu/yq_ofts_guard12_s2/backend-accounting.json)
- [yq_ofts_guard12_s2/report.json](results/baidu/yq_ofts_guard12_s2/report.json)
- [yq_ofts_guard12_s2/retained.json](results/baidu/yq_ofts_guard12_s2/retained.json)
- [yq_ofts_guard12_s2/round-01.json](results/baidu/yq_ofts_guard12_s2/round-01.json)
- [yq_ofts_guard12_s2/round-02.json](results/baidu/yq_ofts_guard12_s2/round-02.json)
- [yq_ofts_guard12_s2/round-03.json](results/baidu/yq_ofts_guard12_s2/round-03.json)
- [yq_ofts_guard12_s2/round-04.json](results/baidu/yq_ofts_guard12_s2/round-04.json)
- [yq_ofts_guard12_s2/round-05.json](results/baidu/yq_ofts_guard12_s2/round-05.json)
- [yq_ofts_guard12_s2/round-06.json](results/baidu/yq_ofts_guard12_s2/round-06.json)
- [yq_ofts_guard12_s2/round-07.json](results/baidu/yq_ofts_guard12_s2/round-07.json)
- [yq_ofts_guard12_s2/round-08.json](results/baidu/yq_ofts_guard12_s2/round-08.json)
- [yq_ofts_guard12_s2/round-09.json](results/baidu/yq_ofts_guard12_s2/round-09.json)
- [yq_ofts_guard12_s2/round-10.json](results/baidu/yq_ofts_guard12_s2/round-10.json)
- [yq_ofts_guard12_s2/round-11.json](results/baidu/yq_ofts_guard12_s2/round-11.json)
- [yq_ofts_guard12_s2/round-12.json](results/baidu/yq_ofts_guard12_s2/round-12.json)
- [yq_ofts_guard12_s2/tests.txt](results/baidu/yq_ofts_guard12_s2/tests.txt)
- [yq_ofts_guard12_s2_rep/SOURCE-zw-rsi-yq-ofts-guard12-s2-rep.job-t9dplazqeesa.txt](results/baidu/yq_ofts_guard12_s2_rep/SOURCE-zw-rsi-yq-ofts-guard12-s2-rep.job-t9dplazqeesa.txt)
- [yq_ofts_guard12_s2_rep/test_eval.json](results/baidu/yq_ofts_guard12_s2_rep/test_eval.json)
- [yq_ofts_guard12_s2_rep/tests.txt](results/baidu/yq_ofts_guard12_s2_rep/tests.txt)
- [yq_ofts_guard12_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s2-fresh.job-pumd7vyzpwwx.txt](results/baidu/yq_ofts_guard12_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s2-fresh.job-pumd7vyzpwwx.txt)
- [yq_ofts_guard12_s2_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s2_fresh/test_eval.json)
- [yq_ofts_guard12_s2_fresh/tests.txt](results/baidu/yq_ofts_guard12_s2_fresh/tests.txt)

### yq_ofts_guard12_s3

- official：59.8000%；[test-libero_official-r12c0.jsonl](results/baidu/yq_ofts_guard12_s3/tests.txt)
- official：60.6000%；[test-libero_official-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s3_rep/tests.txt)
- official：61.2000%；[test-libero_official-r12c0-rep2.jsonl](results/baidu/yq_ofts_guard12_s3_rep/tests.txt)
- fresh：65.7000%；[test-libero_fresh-r12c0-rep1.jsonl](results/baidu/yq_ofts_guard12_s3_fresh/tests.txt)

完整文件：

- [yq_ofts_guard12_s3/SOURCE-zw-rsi-yq-ofts-guard12-s3.job-7tir38px7755.txt](results/baidu/yq_ofts_guard12_s3/SOURCE-zw-rsi-yq-ofts-guard12-s3.job-7tir38px7755.txt)
- [yq_ofts_guard12_s3/accepted.jsonl](results/baidu/yq_ofts_guard12_s3/accepted.jsonl)
- [yq_ofts_guard12_s3/backend-accounting.json](results/baidu/yq_ofts_guard12_s3/backend-accounting.json)
- [yq_ofts_guard12_s3/report.json](results/baidu/yq_ofts_guard12_s3/report.json)
- [yq_ofts_guard12_s3/retained.json](results/baidu/yq_ofts_guard12_s3/retained.json)
- [yq_ofts_guard12_s3/round-01.json](results/baidu/yq_ofts_guard12_s3/round-01.json)
- [yq_ofts_guard12_s3/round-02.json](results/baidu/yq_ofts_guard12_s3/round-02.json)
- [yq_ofts_guard12_s3/round-03.json](results/baidu/yq_ofts_guard12_s3/round-03.json)
- [yq_ofts_guard12_s3/round-04.json](results/baidu/yq_ofts_guard12_s3/round-04.json)
- [yq_ofts_guard12_s3/round-05.json](results/baidu/yq_ofts_guard12_s3/round-05.json)
- [yq_ofts_guard12_s3/round-06.json](results/baidu/yq_ofts_guard12_s3/round-06.json)
- [yq_ofts_guard12_s3/round-07.json](results/baidu/yq_ofts_guard12_s3/round-07.json)
- [yq_ofts_guard12_s3/round-08.json](results/baidu/yq_ofts_guard12_s3/round-08.json)
- [yq_ofts_guard12_s3/round-09.json](results/baidu/yq_ofts_guard12_s3/round-09.json)
- [yq_ofts_guard12_s3/round-10.json](results/baidu/yq_ofts_guard12_s3/round-10.json)
- [yq_ofts_guard12_s3/round-11.json](results/baidu/yq_ofts_guard12_s3/round-11.json)
- [yq_ofts_guard12_s3/round-12.json](results/baidu/yq_ofts_guard12_s3/round-12.json)
- [yq_ofts_guard12_s3/tests.txt](results/baidu/yq_ofts_guard12_s3/tests.txt)
- [yq_ofts_guard12_s3_rep/SOURCE-zw-rsi-yq-ofts-guard12-s3-rep.job-7lw75ykjpkol.txt](results/baidu/yq_ofts_guard12_s3_rep/SOURCE-zw-rsi-yq-ofts-guard12-s3-rep.job-7lw75ykjpkol.txt)
- [yq_ofts_guard12_s3_rep/test_eval.json](results/baidu/yq_ofts_guard12_s3_rep/test_eval.json)
- [yq_ofts_guard12_s3_rep/tests.txt](results/baidu/yq_ofts_guard12_s3_rep/tests.txt)
- [yq_ofts_guard12_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s3-fresh.job-2rizf2ary0ih.txt](results/baidu/yq_ofts_guard12_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s3-fresh.job-2rizf2ary0ih.txt)
- [yq_ofts_guard12_s3_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s3_fresh/test_eval.json)
- [yq_ofts_guard12_s3_fresh/tests.txt](results/baidu/yq_ofts_guard12_s3_fresh/tests.txt)

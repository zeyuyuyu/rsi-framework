# Final results: LLM 元层的作用

核对日期：2026-11-16。主对比：失败 BC 配方起步，Goal / Spatial，seed 1–3，6轮。

## 1. 这些数据支持什么结论

Goal 的 LLM 元层提高 Official 和 Fresh 的三种子均值；Spatial 的 Fresh 均值提高，但 Official 降低。收益依赖任务和测试集，不能声称元层在所有设置下都有效。

两组均开启 recursion 和严格 fresh-paired gate。fixed 每轮1个候选，LLM每轮2个候选，每候选3个inner steps，因此这是包含额外候选搜索的元层整体效果，不是严格等算力消融。Goal使用llm_harness，Spatial使用meta3，两个任务的元层版本不同。

Official：每个种子先平均3次评测，再在种子间平均。Fresh主图：每个种子统一使用首次1000场景评测；Goal LLM追加的两次评测单列，不混进主图。SD为种子间样本标准差，不是CI。

## 2. 最终结果总表（seed 1–3）

|任务|测试|fixed均值 %|fixed SD|LLM均值 %|LLM SD|LLM − fixed pp|配对差值 SD|
|---|---|---:|---:|---:|---:|---:|---:|
|Goal|Official|57.4000|1.3013|59.7778|1.6949|2.3778|1.8103|
|Goal|Fresh|59.2000|1.7521|63.5333|1.4224|4.3333|2.0793|
|Spatial|Official|58.2444|1.1399|56.7333|4.0464|-1.5111|3.7679|
|Spatial|Fresh|60.7667|2.7301|64.0000|2.7622|3.2333|4.2595|

## 3. 逐种子结果

|任务|Seed|Official fixed %|Official LLM %|差值 pp|Fresh fixed %|Fresh LLM %|差值 pp|
|---|---:|---:|---:|---:|---:|---:|---:|
|Goal|1|56.0667|60.1333|4.0667|57.5000|64.2000|6.7000|
|Goal|2|58.6667|61.2667|2.6000|61.0000|64.5000|3.5000|
|Goal|3|57.4667|57.9333|0.4667|59.1000|61.9000|2.8000|
|Spatial|1|58.8000|61.4000|2.6000|58.9000|66.9000|8.0000|
|Spatial|2|59.0000|54.2000|-4.8000|63.9000|63.7000|-0.2000|
|Spatial|3|56.9333|54.6000|-2.3333|59.5000|61.4000|1.9000|

## 4. Seed 0 补充（A800；不进入上述三种子均值）

|任务|方法|Official %|Fresh首次 %|
|---|---|---:|---:|
|Goal|fixed|57.4000|缺失|
|Goal|LLM|60.8667|67.0000|
|Spatial|fixed|55.1333|64.3000|
|Spatial|LLM|61.8000|69.0000|

Goal seed0缺fixed的Fresh测试，不能补成四种子Fresh配对；Spatial seed0两种测试均可形成配对。


## 5. 实验参数：BC 起步不等于始终使用 BC

|设置|无元层 fixed|LLM 元层|
|---|---|---|
|初始策略|对应任务的 OpenVLA-OFT SFT|同任务相同初始策略|
|初始训练程序|失败 BC 配方|同一失败 BC 配方|
|外层轮数|6|6|
|每轮候选|1|2|
|每候选 inner steps|3|3|
|Recursion|开启|开启|
|Gate|严格 fresh_paired，min_gate_gain=0|相同|
|训练程序是否更新|否，始终 BC|是，可能改为 GRPO，也可能保持 BC|
|Goal 元层版本|fixed|llm_harness|
|Spatial 元层版本|fixed|meta3；含 numeric fallback|

共同初始配方：operator=bc，lr=1e-5，update.steps=100，batch=64，cases=64，samples=8，temperature=1.6，curation.rule=verified，per_case=2，allocation=uniform。初始配方相同，但元层修改后不再是固定算法的比较。

Goal 的 LLM 运行就是 [结果1](final_result1_readme.md) 中与普通 RL 比较的同一组。结果1对 Goal LLM Fresh 平均三次评测，得到63.58%；本元层主图统一采用首次Fresh评测，与fixed的单次评测对齐，得到63.53%。二者不是数据冲突。

### 各种子最终保留的程序

|任务|方法|Seed|operator|lr|update.steps|batch|cases|samples|temperature|allocation|curation.rule|per_case|来源|
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|
|Goal|fixed|1|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftgb_fixed_s1/retained.json)|
|Goal|LLM|1|grpo|5e-05|200|128|128|12|1.2|progress|mixed_groups|2|[retained](results/baidu/yq_oftgb_llm_harness_s1/retained.json)|
|Goal|fixed|2|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftgb_fixed_s2/retained.json)|
|Goal|LLM|2|grpo|2e-05|400|128|192|12|1.0|progress|mixed_groups|2|[retained](results/baidu/yq_oftgb_llm_harness_s2/retained.json)|
|Goal|fixed|3|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftgb_fixed_s3/retained.json)|
|Goal|LLM|3|bc|2e-05|200|64|200|16|1.3|progress|verified|2|[retained](results/baidu/yq_oftgb_llm_harness_s3/retained.json)|
|Spatial|fixed|1|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftsb_fixed_s1/retained.json)|
|Spatial|LLM|1|grpo|0.0001|50|64|64|8|1.6|uniform|mixed_groups|2|[retained](results/baidu/yq_oftsb_meta3_s1/retained.json)|
|Spatial|fixed|2|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftsb_fixed_s2/retained.json)|
|Spatial|LLM|2|bc|3e-05|100|64|64|8|1.6|weights|verified|2|[retained](results/baidu/yq_oftsb_meta3_s2/retained.json)|
|Spatial|fixed|3|bc|1e-05|100|64|64|8|1.6|uniform|verified|2|[retained](results/baidu/yq_oftsb_fixed_s3/retained.json)|
|Spatial|LLM|3|bc|1e-05|100|64|64|8|1.6|weights|verified|4|[retained](results/baidu/yq_oftsb_meta3_s3/retained.json)|

## 6. 为什么 Spatial Official 的 fixed 均值更高

这是事后诊断，不是已验证的单因素因果结论。差距由seed2、3拉低：seed1的LLM相对fixed为+2.60 pp，seed2为−4.80 pp，seed3为−2.33 pp。三种子平均−1.51 pp；[已有统计结果](results/spatial_repair_read_20261114.json) 的 `S1_yangquan` 给出配对bootstrap 95% CI [−3.24, +0.24]，包含0。因此称“fixed均值更高”，不能称“fixed显著更好”。该CI是repo既有方法的结果，不是跨种子SD或新计算的种子级CI。

### Seed 2：gate接受的修改没有迁移成Official提升

- 元层先将均匀任务采样改为加权采样，最终权重为 `[2,0,0,0,2,2,0,2,2,2]`。
- 第5轮将BC学习率从1e-5提高到3e-5；该轮原程序候选gate=62.5%，新程序候选gate=68.0%，新程序被接受。
- Official逐轮单次评测从上一保留版本r03c1的57.4%降到r05c1的53.6%；最后三次评测均值54.2%，而fixed为59.0%。
- 这直接显示gate选择与Official表现不完全一致。提高学习率是可定位的嫌疑，但缺少同轮两个候选的完整Official反事实对照，不能将全部下降归因于学习率。

来源：[第5轮候选](results/baidu/yq_oftsb_meta3_s2/round-05.json)、[report逐轮曲线](results/baidu/yq_oftsb_meta3_s2/report.json)、[最终程序及LLM修改说明](results/baidu/yq_oftsb_meta3_s2/retained.json)。逐轮数字是单次测试，不与最终三次均值混用。

### Seed 3：任务重分配和BC数据保留调整，Official收益不均

- 保持BC、学习率1e-5，但将任务采样权重改为 `[3,1.5,0.3,0.3,1,1.5,0.2,3,1.5,0.5]`，并将curation.per_case从2提高到4。
- Task6权重较低，其Official相对fixed下降10 pp；Task7权重较高仍下降6 pp。因此训练资源重分配是可能机制，但“某任务少练”不足以解释全部损失。
- 终态Fresh相比fixed提高1.9 pp，而Official下降2.33 pp，符合评测场景之间收益不一致的现象；不能直接据此宣布过拟合或灾难性遗忘已被证实。

来源：[第3轮候选](results/baidu/yq_oftsb_meta3_s3/round-03.json)、[最终程序](results/baidu/yq_oftsb_meta3_s3/retained.json)、[report](results/baidu/yq_oftsb_meta3_s3/report.json)。

### Seed 1：并非所有元层修改都失败

该种子最终程序为GRPO，Official提高2.60 pp。最终保留程序的author是`search`，note为`update.steps: 50`，继承前面的LLM程序。meta3允许无效或失败的LLM提案回退到numeric search，所以图例宜称“LLM harness / meta3”，而非“所有候选均由LLM生成”。

来源：[最终程序](results/baidu/yq_oftsb_meta3_s1/retained.json)、[accepted链与逐轮曲线](results/baidu/yq_oftsb_meta3_s1/report.json)、[fallback实现](rsi/meta/harness.py)。

### Official逐任务差值：LLM − fixed

从每个运行的三次原始TESTBITS重算，先平均评测，再按task分组。每个task有50个固定Official episodes；使用A800 plan中的任务ID顺序，并验证其digest与Yangquan记录一致后分组。Task编号为0起始。

|Task|Seed1 Δ pp|Seed2 Δ pp|Seed3 Δ pp|
|---:|---:|---:|---:|
|0|-8.00|8.00|-1.33|
|1|5.33|-1.33|-5.33|
|2|-2.67|-0.67|2.67|
|3|2.67|-4.00|0.67|
|4|-4.00|-3.33|-2.67|
|5|8.00|0.00|0.67|
|6|8.67|-6.00|-10.00|
|7|7.33|-22.00|-6.00|
|8|4.67|-4.00|-4.67|
|9|4.00|-14.67|2.67|

复核入口：[task ID顺序](results/a800/runs2/a8_spatrep_meta3_s0/plan.json)；原始TESTBITS见下方各Spatial主目录和_rep目录的tests.txt。

## 7. 画图与结论建议

|面板|内容|取数口径|
|---|---|---|
|主图：元层整体效果|Goal / Spatial × Official / Fresh；fixed vs LLM|第2、3节，seed1–3；均值+同种子连接的散点|
|解释图：Spatial差异来自哪里|三个种子的Official差值，以及任务级差值|第6节；保留负面结果|
|可选过程图|Spatial LLM accepted版本的Official轨迹|各report中的tests.libero_official.curve；标注是单次评测|
|补充图|Goal调优配方起步的fixed vs LLM|见下方补充结果，不与失败BC主图合并|

可用表述：**从失败BC配方起步时，LLM元层的收益取决于任务与评测场景。Goal的Official和Fresh均值均提高；Spatial的Fresh均值提高，但Official未显示一致收益。逐轮记录提示gate选择的程序修改不一定迁移为Official提升。**

不支持：元层始终有效；LLM纯决策能力在等算力下优于fixed；BC必然弱于GRPO；特定学习率或采样权重已被因果证明导致退化。

## 8. 补充对照与原始数据索引

链接相对于repo根目录；保留原始逐次测量与逐轮配置，便于复核。seed0不进入主图。Fresh追加评测仅作补充。



这组不是失败BC自修复，不与主图合并。均为6轮，seed 1–3，Official每种子3次评测。Fresh未找到完整LLM配对。

|Seed|fixed Official %|LLM Official %|差值 pp|来源|
|---|---:|---:|---:|---|
|1|59.8000|59.0000|-0.8000|[yq_oftg_fixed_s1/yq_oftg_fixed_s1/test-libero_official-r06c0.jsonl](results/baidu/yq_oftg_fixed_s1/tests.txt), [yq_oftg_fixed_s1/yq_oftg_fixed_s1_rep/test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftg_fixed_s1_rep/tests.txt), [yq_oftg_fixed_s1/yq_oftg_fixed_s1_rep/test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftg_fixed_s1_rep/tests.txt), [yq_oftg_llm_harness_s1/yq_oftg_llm_harness_s1/test-libero_official-r05c1.jsonl](results/baidu/yq_oftg_llm_harness_s1/tests.txt), [yq_oftg_llm_harness_s1/yq_oftg_llm_harness_s1_rep/test-libero_official-r05c1-rep1.jsonl](results/baidu/yq_oftg_llm_harness_s1_rep/tests.txt), [yq_oftg_llm_harness_s1/yq_oftg_llm_harness_s1_rep/test-libero_official-r05c1-rep2.jsonl](results/baidu/yq_oftg_llm_harness_s1_rep/tests.txt)|
|2|59.8667|60.3333|0.4667|[yq_oftg_fixed_s2/yq_oftg_fixed_s2/test-libero_official-r05c0.jsonl](results/baidu/yq_oftg_fixed_s2/tests.txt), [yq_oftg_fixed_s2/yq_oftg_fixed_s2_rep/test-libero_official-r05c0-rep1.jsonl](results/baidu/yq_oftg_fixed_s2_rep/tests.txt), [yq_oftg_fixed_s2/yq_oftg_fixed_s2_rep/test-libero_official-r05c0-rep2.jsonl](results/baidu/yq_oftg_fixed_s2_rep/tests.txt), [yq_oftg_llm_harness_s2/yq_oftg_llm_harness_s2/test-libero_official-r05c0.jsonl](results/baidu/yq_oftg_llm_harness_s2/tests.txt), [yq_oftg_llm_harness_s2/yq_oftg_llm_harness_s2_rep/test-libero_official-r05c0-rep1.jsonl](results/baidu/yq_oftg_llm_harness_s2_rep/tests.txt), [yq_oftg_llm_harness_s2/yq_oftg_llm_harness_s2_rep/test-libero_official-r05c0-rep2.jsonl](results/baidu/yq_oftg_llm_harness_s2_rep/tests.txt)|
|3|62.2000|60.3333|-1.8667|[yq_oftg_fixed_s3/yq_oftg_fixed_s3/test-libero_official-r06c0.jsonl](results/baidu/yq_oftg_fixed_s3/tests.txt), [yq_oftg_fixed_s3/yq_oftg_fixed_s3_rep/test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftg_fixed_s3_rep/tests.txt), [yq_oftg_fixed_s3/yq_oftg_fixed_s3_rep/test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftg_fixed_s3_rep/tests.txt), [yq_oftg_llm_harness_s3/yq_oftg_llm_harness_s3/test-libero_official-r06c0.jsonl](results/baidu/yq_oftg_llm_harness_s3/tests.txt), [yq_oftg_llm_harness_s3/yq_oftg_llm_harness_s3_rep/test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftg_llm_harness_s3_rep/tests.txt), [yq_oftg_llm_harness_s3/yq_oftg_llm_harness_s3_rep/test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftg_llm_harness_s3_rep/tests.txt)|
|均值|60.6222|59.8889|-0.7333| |

这套调优配方对照未观察到LLM元层均值提升。


### 各运行的完整原始入口



下列数字直接来自raw TESTBITS / episode JSONL；每项保留独立评测，不将测试重复当作独立训练种子。

### Goal · seed 0 · fixed · `a8_oftgb_fixed_s0`

Retained: `r06c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/a800/runs2/a8_oftgb_fixed_s0/report.json)
- [retained.json](results/a800/runs2/a8_oftgb_fixed_s0/retained.json)
- [accepted.jsonl](results/a800/runs2/a8_oftgb_fixed_s0/accepted.jsonl)
- [plan.json](results/a800/runs2/a8_oftgb_fixed_s0/plan.json)
- [round-01.json](results/a800/runs2/a8_oftgb_fixed_s0/round-01.json)
- [round-02.json](results/a800/runs2/a8_oftgb_fixed_s0/round-02.json)
- [round-03.json](results/a800/runs2/a8_oftgb_fixed_s0/round-03.json)
- [round-04.json](results/a800/runs2/a8_oftgb_fixed_s0/round-04.json)
- [round-05.json](results/a800/runs2/a8_oftgb_fixed_s0/round-05.json)
- [round-06.json](results/a800/runs2/a8_oftgb_fixed_s0/round-06.json)
- Official：**57.6000%**；[test-libero_official-r06c0.jsonl](results/a800/runs2/a8_oftgb_fixed_s0/test-libero_official-r06c0.jsonl)
- Official：**57.4000%**；[test-libero_official-r06c0-rep1.jsonl](results/a800/runs2/a8_oftgb_fixed_s0_rep/test-libero_official-r06c0-rep1.jsonl)
- Official：**57.2000%**；[test-libero_official-r06c0-rep2.jsonl](results/a800/runs2/a8_oftgb_fixed_s0_rep/test-libero_official-r06c0-rep2.jsonl)
- Fresh首次：无记录
- Fresh追加：无记录

### Goal · seed 0 · LLM · `a8_oftgb_llm_harness_s0`

Retained: `r06c0`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/a800/runs2/a8_oftgb_llm_harness_s0/report.json)
- [retained.json](results/a800/runs2/a8_oftgb_llm_harness_s0/retained.json)
- [accepted.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0/accepted.jsonl)
- [plan.json](results/a800/runs2/a8_oftgb_llm_harness_s0/plan.json)
- [round-01.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-01.json)
- [round-02.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-02.json)
- [round-03.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-03.json)
- [round-04.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-04.json)
- [round-05.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-05.json)
- [round-06.json](results/a800/runs2/a8_oftgb_llm_harness_s0/round-06.json)
- Official：**61.0000%**；[test-libero_official-r06c0.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0/test-libero_official-r06c0.jsonl)
- Official：**61.0000%**；[test-libero_official-r06c0-rep1.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0_rep/test-libero_official-r06c0-rep1.jsonl)
- Official：**60.6000%**；[test-libero_official-r06c0-rep2.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0_rep/test-libero_official-r06c0-rep2.jsonl)
- Fresh首次：**67.0000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0_fresh/test-libero_fresh-r06c0-rep1.jsonl)
- Fresh追加：**66.5000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0_fresh23/test-libero_fresh-r06c0-rep1.jsonl)
- Fresh追加：**66.8000%**；[test-libero_fresh-r06c0-rep2.jsonl](results/a800/runs2/a8_oftgb_llm_harness_s0_fresh23/test-libero_fresh-r06c0-rep2.jsonl)

### Goal · seed 1 · fixed · `yq_oftgb_fixed_s1`

Retained: `r06c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_fixed_s1/report.json)
- [retained.json](results/baidu/yq_oftgb_fixed_s1/retained.json)
- [accepted.jsonl](results/baidu/yq_oftgb_fixed_s1/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftgb_fixed_s1/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_fixed_s1/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_fixed_s1/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_fixed_s1/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_fixed_s1/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_fixed_s1/round-06.json)
- Official：**57.0000%**；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftgb_fixed_s1/tests.txt)
- Official：**54.6000%**；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s1_rep/tests.txt)
- Official：**56.6000%**；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftgb_fixed_s1_rep/tests.txt)
- Fresh首次：**57.5000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s1_fresh/tests.txt)
- Fresh追加：无记录

### Goal · seed 1 · LLM · `yq_oftgb_llm_harness_s1`

Retained: `r05c1`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_llm_harness_s1/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s1/retained.json)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s1/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s1/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s1/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s1/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s1/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s1/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s1/round-06.json)
- Official：**60.2000%**；[test-libero_official-r05c1.jsonl](results/baidu/yq_oftgb_llm_harness_s1/tests.txt)
- Official：**60.4000%**；[test-libero_official-r05c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s1_rep/tests.txt)
- Official：**59.8000%**；[test-libero_official-r05c1-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s1_rep/tests.txt)
- Fresh首次：**64.2000%**；[test-libero_fresh-r05c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s1_fresh/tests.txt)
- Fresh追加：**63.4000%**；[test-libero_fresh-r05c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s1_fresh23/tests.txt)
- Fresh追加：**63.8000%**；[test-libero_fresh-r05c1-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s1_fresh23/tests.txt)

### Goal · seed 2 · fixed · `yq_oftgb_fixed_s2`

Retained: `n0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_fixed_s2/report.json)
- [retained.json](results/baidu/yq_oftgb_fixed_s2/retained.json)
- [round-01.json](results/baidu/yq_oftgb_fixed_s2/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_fixed_s2/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_fixed_s2/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_fixed_s2/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_fixed_s2/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_fixed_s2/round-06.json)
- Official：**58.4000%**；[test-libero_official-n0.jsonl](results/baidu/yq_oftgb_fixed_s2/tests.txt)
- Official：**58.2000%**；[test-libero_official-n0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s2_rep/tests.txt)
- Official：**59.4000%**；[test-libero_official-n0-rep2.jsonl](results/baidu/yq_oftgb_fixed_s2_rep/tests.txt)
- Fresh首次：**61.0000%**；[test-libero_fresh-n0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s2_fresh/tests.txt)
- Fresh追加：无记录

### Goal · seed 2 · LLM · `yq_oftgb_llm_harness_s2`

Retained: `r06c0`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_llm_harness_s2/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s2/retained.json)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s2/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s2/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s2/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s2/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s2/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s2/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s2/round-06.json)
- Official：**60.6000%**；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftgb_llm_harness_s2/tests.txt)
- Official：**61.8000%**；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s2_rep/tests.txt)
- Official：**61.4000%**；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s2_rep/tests.txt)
- Fresh首次：**64.5000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s2_fresh/tests.txt)
- Fresh追加：**64.6000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s2_fresh23/tests.txt)
- Fresh追加：**66.0000%**；[test-libero_fresh-r06c0-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s2_fresh23/tests.txt)

### Goal · seed 3 · fixed · `yq_oftgb_fixed_s3`

Retained: `r05c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_fixed_s3/report.json)
- [retained.json](results/baidu/yq_oftgb_fixed_s3/retained.json)
- [accepted.jsonl](results/baidu/yq_oftgb_fixed_s3/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftgb_fixed_s3/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_fixed_s3/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_fixed_s3/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_fixed_s3/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_fixed_s3/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_fixed_s3/round-06.json)
- Official：**56.4000%**；[test-libero_official-r05c0.jsonl](results/baidu/yq_oftgb_fixed_s3/tests.txt)
- Official：**58.0000%**；[test-libero_official-r05c0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s3_rep/tests.txt)
- Official：**58.0000%**；[test-libero_official-r05c0-rep2.jsonl](results/baidu/yq_oftgb_fixed_s3_rep/tests.txt)
- Fresh首次：**59.1000%**；[test-libero_fresh-r05c0-rep1.jsonl](results/baidu/yq_oftgb_fixed_s3_fresh/tests.txt)
- Fresh追加：无记录

### Goal · seed 3 · LLM · `yq_oftgb_llm_harness_s3`

Retained: `r06c1`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftgb_llm_harness_s3/report.json)
- [retained.json](results/baidu/yq_oftgb_llm_harness_s3/retained.json)
- [accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s3/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftgb_llm_harness_s3/round-01.json)
- [round-02.json](results/baidu/yq_oftgb_llm_harness_s3/round-02.json)
- [round-03.json](results/baidu/yq_oftgb_llm_harness_s3/round-03.json)
- [round-04.json](results/baidu/yq_oftgb_llm_harness_s3/round-04.json)
- [round-05.json](results/baidu/yq_oftgb_llm_harness_s3/round-05.json)
- [round-06.json](results/baidu/yq_oftgb_llm_harness_s3/round-06.json)
- Official：**57.6000%**；[test-libero_official-r06c1.jsonl](results/baidu/yq_oftgb_llm_harness_s3/tests.txt)
- Official：**57.6000%**；[test-libero_official-r06c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s3_rep/tests.txt)
- Official：**58.6000%**；[test-libero_official-r06c1-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s3_rep/tests.txt)
- Fresh首次：**61.9000%**；[test-libero_fresh-r06c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s3_fresh/tests.txt)
- Fresh追加：**61.9000%**；[test-libero_fresh-r06c1-rep1.jsonl](results/baidu/yq_oftgb_llm_harness_s3_fresh23/tests.txt)
- Fresh追加：**61.9000%**；[test-libero_fresh-r06c1-rep2.jsonl](results/baidu/yq_oftgb_llm_harness_s3_fresh23/tests.txt)

### Spatial · seed 0 · fixed · `a8_spatrep_fixed_s0`

Retained: `r06c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/a800/runs2/a8_spatrep_fixed_s0/report.json)
- [retained.json](results/a800/runs2/a8_spatrep_fixed_s0/retained.json)
- [accepted.jsonl](results/a800/runs2/a8_spatrep_fixed_s0/accepted.jsonl)
- [plan.json](results/a800/runs2/a8_spatrep_fixed_s0/plan.json)
- [round-01.json](results/a800/runs2/a8_spatrep_fixed_s0/round-01.json)
- [round-02.json](results/a800/runs2/a8_spatrep_fixed_s0/round-02.json)
- [round-03.json](results/a800/runs2/a8_spatrep_fixed_s0/round-03.json)
- [round-04.json](results/a800/runs2/a8_spatrep_fixed_s0/round-04.json)
- [round-05.json](results/a800/runs2/a8_spatrep_fixed_s0/round-05.json)
- [round-06.json](results/a800/runs2/a8_spatrep_fixed_s0/round-06.json)
- Official：**55.4000%**；[test-libero_official-r06c0.jsonl](results/a800/runs2/a8_spatrep_fixed_s0/test-libero_official-r06c0.jsonl)
- Official：**54.8000%**；[test-libero_official-r06c0-rep1.jsonl](results/a800/runs2/a8_spatrep_fixed_s0_rep/test-libero_official-r06c0-rep1.jsonl)
- Official：**55.2000%**；[test-libero_official-r06c0-rep2.jsonl](results/a800/runs2/a8_spatrep_fixed_s0_rep/test-libero_official-r06c0-rep2.jsonl)
- Fresh首次：**64.3000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/a800/runs2/a8_spatrep_fixed_s0_fresh/test-libero_fresh-r06c0-rep1.jsonl)
- Fresh追加：无记录

### Spatial · seed 0 · LLM · `a8_spatrep_meta3_s0`

Retained: `r06c0`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/a800/runs2/a8_spatrep_meta3_s0/report.json)
- [retained.json](results/a800/runs2/a8_spatrep_meta3_s0/retained.json)
- [accepted.jsonl](results/a800/runs2/a8_spatrep_meta3_s0/accepted.jsonl)
- [plan.json](results/a800/runs2/a8_spatrep_meta3_s0/plan.json)
- [round-01.json](results/a800/runs2/a8_spatrep_meta3_s0/round-01.json)
- [round-02.json](results/a800/runs2/a8_spatrep_meta3_s0/round-02.json)
- [round-03.json](results/a800/runs2/a8_spatrep_meta3_s0/round-03.json)
- [round-04.json](results/a800/runs2/a8_spatrep_meta3_s0/round-04.json)
- [round-05.json](results/a800/runs2/a8_spatrep_meta3_s0/round-05.json)
- [round-06.json](results/a800/runs2/a8_spatrep_meta3_s0/round-06.json)
- Official：**61.4000%**；[test-libero_official-r06c0.jsonl](results/a800/runs2/a8_spatrep_meta3_s0/test-libero_official-r06c0.jsonl)
- Official：**62.4000%**；[test-libero_official-r06c0-rep1.jsonl](results/a800/runs2/a8_spatrep_meta3_s0_rep/test-libero_official-r06c0-rep1.jsonl)
- Official：**61.6000%**；[test-libero_official-r06c0-rep2.jsonl](results/a800/runs2/a8_spatrep_meta3_s0_rep/test-libero_official-r06c0-rep2.jsonl)
- Fresh首次：**69.0000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/a800/runs2/a8_spatrep_meta3_s0_fresh/test-libero_fresh-r06c0-rep1.jsonl)
- Fresh追加：无记录

### Spatial · seed 1 · fixed · `yq_oftsb_fixed_s1`

Retained: `r03c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_fixed_s1/report.json)
- [retained.json](results/baidu/yq_oftsb_fixed_s1/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_fixed_s1/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_fixed_s1/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_fixed_s1/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_fixed_s1/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_fixed_s1/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_fixed_s1/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_fixed_s1/round-06.json)
- Official：**58.8000%**；[test-libero_official-r03c0.jsonl](results/baidu/yq_oftsb_fixed_s1/tests.txt)
- Official：**58.8000%**；[test-libero_official-r03c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- Official：**58.8000%**；[test-libero_official-r03c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- Fresh首次：**58.9000%**；[test-libero_fresh-r03c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s1_fresh/tests.txt)
- Fresh追加：无记录

### Spatial · seed 1 · LLM · `yq_oftsb_meta3_s1`

Retained: `r06c1`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_meta3_s1/report.json)
- [retained.json](results/baidu/yq_oftsb_meta3_s1/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_meta3_s1/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_meta3_s1/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_meta3_s1/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_meta3_s1/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_meta3_s1/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_meta3_s1/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_meta3_s1/round-06.json)
- Official：**61.4000%**；[test-libero_official-r06c1.jsonl](results/baidu/yq_oftsb_meta3_s1/tests.txt)
- Official：**61.6000%**；[test-libero_official-r06c1-rep1.jsonl](results/baidu/yq_oftsb_meta3_s1_rep/tests.txt)
- Official：**61.2000%**；[test-libero_official-r06c1-rep2.jsonl](results/baidu/yq_oftsb_meta3_s1_rep/tests.txt)
- Fresh首次：**66.9000%**；[test-libero_fresh-r06c1-rep1.jsonl](results/baidu/yq_oftsb_meta3_s1_fresh/tests.txt)
- Fresh追加：无记录

### Spatial · seed 2 · fixed · `yq_oftsb_fixed_s2`

Retained: `r06c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_fixed_s2/report.json)
- [retained.json](results/baidu/yq_oftsb_fixed_s2/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_fixed_s2/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_fixed_s2/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_fixed_s2/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_fixed_s2/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_fixed_s2/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_fixed_s2/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_fixed_s2/round-06.json)
- Official：**59.0000%**；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_fixed_s2/tests.txt)
- Official：**58.4000%**；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- Official：**59.6000%**；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- Fresh首次：**63.9000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s2_fresh/tests.txt)
- Fresh追加：无记录

### Spatial · seed 2 · LLM · `yq_oftsb_meta3_s2`

Retained: `r05c1`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_meta3_s2/report.json)
- [retained.json](results/baidu/yq_oftsb_meta3_s2/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_meta3_s2/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_meta3_s2/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_meta3_s2/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_meta3_s2/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_meta3_s2/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_meta3_s2/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_meta3_s2/round-06.json)
- Official：**53.6000%**；[test-libero_official-r05c1.jsonl](results/baidu/yq_oftsb_meta3_s2/tests.txt)
- Official：**54.4000%**；[test-libero_official-r05c1-rep1.jsonl](results/baidu/yq_oftsb_meta3_s2_rep/tests.txt)
- Official：**54.6000%**；[test-libero_official-r05c1-rep2.jsonl](results/baidu/yq_oftsb_meta3_s2_rep/tests.txt)
- Fresh首次：**63.7000%**；[test-libero_fresh-r05c1-rep1.jsonl](results/baidu/yq_oftsb_meta3_s2_fresh/tests.txt)
- Fresh追加：无记录

### Spatial · seed 3 · fixed · `yq_oftsb_fixed_s3`

Retained: `r05c0`；配置：6轮，1候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_fixed_s3/report.json)
- [retained.json](results/baidu/yq_oftsb_fixed_s3/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_fixed_s3/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_fixed_s3/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_fixed_s3/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_fixed_s3/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_fixed_s3/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_fixed_s3/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_fixed_s3/round-06.json)
- Official：**56.2000%**；[test-libero_official-r05c0.jsonl](results/baidu/yq_oftsb_fixed_s3/tests.txt)
- Official：**57.0000%**；[test-libero_official-r05c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- Official：**57.6000%**；[test-libero_official-r05c0-rep2.jsonl](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- Fresh首次：**59.5000%**；[test-libero_fresh-r05c0-rep1.jsonl](results/baidu/yq_oftsb_fixed_s3_fresh/tests.txt)
- Fresh追加：无记录

### Spatial · seed 3 · LLM · `yq_oftsb_meta3_s3`

Retained: `r06c0`；配置：6轮，2候选/轮，3 inner steps/候选。

- [report.json](results/baidu/yq_oftsb_meta3_s3/report.json)
- [retained.json](results/baidu/yq_oftsb_meta3_s3/retained.json)
- [accepted.jsonl](results/baidu/yq_oftsb_meta3_s3/accepted.jsonl)
- [round-01.json](results/baidu/yq_oftsb_meta3_s3/round-01.json)
- [round-02.json](results/baidu/yq_oftsb_meta3_s3/round-02.json)
- [round-03.json](results/baidu/yq_oftsb_meta3_s3/round-03.json)
- [round-04.json](results/baidu/yq_oftsb_meta3_s3/round-04.json)
- [round-05.json](results/baidu/yq_oftsb_meta3_s3/round-05.json)
- [round-06.json](results/baidu/yq_oftsb_meta3_s3/round-06.json)
- Official：**54.8000%**；[test-libero_official-r06c0.jsonl](results/baidu/yq_oftsb_meta3_s3/tests.txt)
- Official：**55.0000%**；[test-libero_official-r06c0-rep1.jsonl](results/baidu/yq_oftsb_meta3_s3_rep/tests.txt)
- Official：**54.0000%**；[test-libero_official-r06c0-rep2.jsonl](results/baidu/yq_oftsb_meta3_s3_rep/tests.txt)
- Fresh首次：**61.4000%**；[test-libero_fresh-r06c0-rep1.jsonl](results/baidu/yq_oftsb_meta3_s3_fresh/tests.txt)
- Fresh追加：无记录


配置：[Goal BC自修复](scripts/baidu/mkplans_bcstart.py)、[Spatial meta3配置](scripts/baidu/mkplans_vla.py)。

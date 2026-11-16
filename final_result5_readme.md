# Final results: 初始任务表现与组件收益的关系

## 1. 这些数据支持什么结论

**没有观察到“初始表现越低，所有组件收益越大”的统一规律。最清楚的描述性趋势出现在Spatial Fresh：recursion、宽松gate和LLM元层的收益更多集中于初始表现较低的任务。该趋势未在Goal或Official中一致复现。**

这是基于已有实验的事后探索性分析，不是预注册的新确认性结论。每个套件只有10个任务，未做相关性显著性检验、多重比较校正或难度分组的不确定性估计。不要将下列描述写成“RSI普遍更擅长困难任务”。

“难度”在这里仅操作性地定义为**相对于对应初始策略的低成功率**；不是独立测量的任务固有难度，也不用于比较Goal和Spatial谁更难。不同测试分布与起始模型、测量噪声、天花板效应均可能影响关系。

## 2. 比较方法与口径

|项目|定义|
|---|---|
|任务套件|LIBERO-Goal、LIBERO-Spatial，分别分析|
|测试|Official、Fresh，分别分析，不混合|
|任务数|每套件10个task，编号0–9|
|训练种子|Yangquan seed1、2、3|
|Official初始参考|fixed12、nonrec12、guard12各3种子的n0，共9次初始策略评测；每次500 episodes，每task50个|
|Fresh初始参考|yq_fresh_n0_goal_1–4 / spatial_1–4，共4次初始策略评测；每次1000 episodes，每task100个|
|Official终态|每运行3次评测先逐episode平均，再按task平均|
|Fresh终态|统一每运行首次Fresh评测；不混入fresh23追加重复|
|每task组件收益|同seed、同task的实验臂−对照；再平均3个训练种子|
|任务分组|每个suite × test内按初始成功率排序；最低5个为低初始组，最高5个为高初始组|
|相关性|Spearman秩相关ρ：初始成功率与组件收益；负值表示低初始任务倾向收益更高|
|评测配对|按原始task ID分组；ID列表SHA256前16位与TESTBITS digest一致才使用|

初始参考在同一suite × test下对所有组件共用，避免按某个方法的最终表现定义难度。排序相同分数按task编号排序；本表具体分组在第5节公开。Official和Fresh的任务分组可能不同，不能认为它们选中了同一批低初始任务。

|组件|实验臂 − 对照|配方与轮数|解释边界|
|---|---|---|---|
|Recursion|fixed12 − nonrec12|固定GRPO，12轮|recursion开关|
|Gate规则|guard12 − fixed12|固定GRPO，12轮|宽松vs严格，不是gate有无|
|BC Gate|fixed − nogate|固定BC，6轮|有无基于表现的接受保护|
|LLM元层|LLM − fixed|失败BC配方起步，6轮|LLM可改算法；1vs2候选，不是等算力；Goal harness与Spatial meta3版本不同|

不能把不同行当成同一训练条件下的组件贡献加和，也不能用16个分组结果事后挑选一个“显著”结论。

## 3. 全部结果：低初始组与高初始组

收益单位pp；两组均包含5个task。ρ为10个task的Spearman相关，不是3个训练种子的相关。未报告p值或置信区间。

|套件|测试|组件|低初始5任务收益 pp|高初始5任务收益 pp|低−高 pp|ρ|
|---|---|---|---:|---:|---:|---:|
|Goal|official|Recursion：fixed12 − nonrec12|+3.0222|+12.6667|-9.6444|+0.2727|
|Goal|official|Gate规则：guard12 − fixed12|+1.3333|+0.4444|+0.8889|+0.1515|
|Goal|official|BC Gate：fixed − nogate|+12.1778|+15.0222|-2.8444|-0.1152|
|Goal|official|LLM元层：LLM − fixed|+2.4000|+2.3556|+0.0444|-0.2970|
|Goal|fresh|Recursion：fixed12 − nonrec12|+7.2667|+7.3333|-0.0667|+0.0122|
|Goal|fresh|Gate规则：guard12 − fixed12|+2.3333|+1.0000|+1.3333|-0.3100|
|Goal|fresh|BC Gate：fixed − nogate|+14.1333|+16.8000|-2.6667|-0.0667|
|Goal|fresh|LLM元层：LLM − fixed|+4.4667|+4.2000|+0.2667|-0.1394|
|Spatial|official|Recursion：fixed12 − nonrec12|+7.7778|+9.5556|-1.7778|+0.1758|
|Spatial|official|Gate规则：guard12 − fixed12|-1.7333|+2.3111|-4.0444|+0.3939|
|Spatial|official|BC Gate：fixed − nogate|+10.3556|+15.6444|-5.2889|+0.4545|
|Spatial|official|LLM元层：LLM − fixed|-1.5111|-1.5111|+0.0000|-0.1030|
|Spatial|fresh|Recursion：fixed12 − nonrec12|+12.2667|+5.0000|+7.2667|-0.5394|
|Spatial|fresh|Gate规则：guard12 − fixed12|+2.3333|+0.0000|+2.3333|-0.5106|
|Spatial|fresh|BC Gate：fixed − nogate|+7.1333|+9.6000|-2.4667|+0.2848|
|Spatial|fresh|LLM元层：LLM − fixed|+5.6000|+0.8667|+4.7333|-0.3951|

## 4. 如何解释这些结果

### Spatial Fresh：低初始任务更受益的描述性趋势

- Recursion：低初始组+12.27 pp，高初始组+5.00 pp；ρ约−0.54。
- 宽松gate：+2.33 vs 0.00 pp；ρ约−0.51。
- LLM元层：+5.60 vs +0.87 pp；ρ约−0.40。
- BC gate则相反：+7.13 vs +9.60 pp，没有同样的低初始任务优势。

### 不复现的设置也要保留

- Goal Fresh的recursion几乎没有组间差异：+7.27 vs +7.33 pp，ρ约0.01。
- Goal Official的recursion，较高初始组反而收益更大：+3.02 vs +12.67 pp。
- Spatial Official的LLM元层，两组平均都约−1.51 pp；初始任务表现不能解释为统一正收益。
- BC gate的保护作用没有一致偏向低初始任务，两个套件、两套测试的高初始组均值都更高。

因此本分析可作为“组件收益依赖任务与评测分布”的补充；不能作为“任务难度导致收益差异”的因果证据。这里的Pearson/Spearman和分组均值可能不完全同向，因为每种统计对task间收益大小与排序的敏感性不同。

## 5. 任务分组及初始参考数值

|套件|测试|task|初始成功率 %|分组|
|---|---|---:|---:|---|
|Goal|official|0|8.0000|低初始5任务|
|Goal|official|1|82.2222|高初始5任务|
|Goal|official|2|65.7778|高初始5任务|
|Goal|official|3|80.2222|高初始5任务|
|Goal|official|4|70.8889|高初始5任务|
|Goal|official|5|45.7778|低初始5任务|
|Goal|official|6|30.4444|低初始5任务|
|Goal|official|7|100.0000|高初始5任务|
|Goal|official|8|47.5556|低初始5任务|
|Goal|official|9|59.3333|低初始5任务|
|Goal|fresh|0|0.0000|低初始5任务|
|Goal|fresh|1|84.5000|高初始5任务|
|Goal|fresh|2|70.7500|高初始5任务|
|Goal|fresh|3|83.0000|高初始5任务|
|Goal|fresh|4|77.0000|高初始5任务|
|Goal|fresh|5|66.0000|低初始5任务|
|Goal|fresh|6|20.2500|低初始5任务|
|Goal|fresh|7|94.5000|高初始5任务|
|Goal|fresh|8|50.0000|低初始5任务|
|Goal|fresh|9|54.2500|低初始5任务|
|Spatial|official|0|44.6667|低初始5任务|
|Spatial|official|1|6.2222|低初始5任务|
|Spatial|official|2|93.5556|高初始5任务|
|Spatial|official|3|81.7778|高初始5任务|
|Spatial|official|4|79.7778|高初始5任务|
|Spatial|official|5|3.1111|低初始5任务|
|Spatial|official|6|90.0000|高初始5任务|
|Spatial|official|7|59.3333|低初始5任务|
|Spatial|official|8|75.1111|高初始5任务|
|Spatial|official|9|68.2222|低初始5任务|
|Spatial|fresh|0|31.5000|低初始5任务|
|Spatial|fresh|1|1.5000|低初始5任务|
|Spatial|fresh|2|93.2500|高初始5任务|
|Spatial|fresh|3|96.2500|高初始5任务|
|Spatial|fresh|4|82.7500|高初始5任务|
|Spatial|fresh|5|1.0000|低初始5任务|
|Spatial|fresh|6|99.5000|高初始5任务|
|Spatial|fresh|7|37.0000|低初始5任务|
|Spatial|fresh|8|78.2500|高初始5任务|
|Spatial|fresh|9|74.5000|低初始5任务|

## 6. 全部逐任务与逐种子收益

共2套件 × 2测试 × 4组件 × 10任务=160行。收益是方法差，不是相对初始策略的训练增益；因此不会因在纵轴直接减去初始成功率而机械地产生负相关。仍需考虑初始测量噪声和收益空间差异。

|套件|测试|组件|task|初始 %|Seed1 Δ pp|Seed2 Δ pp|Seed3 Δ pp|三种子均值 Δ pp|
|---|---|---|---:|---:|---:|---:|---:|---:|
|Goal|official|Recursion：fixed12 − nonrec12|0|8.0000|-0.6667|-1.3333|-8.6667|-3.5556|
|Goal|official|Recursion：fixed12 − nonrec12|1|82.2222|-4.6667|-2.0000|-2.6667|-3.1111|
|Goal|official|Recursion：fixed12 − nonrec12|2|65.7778|+21.3333|-4.0000|+5.3333|+7.5556|
|Goal|official|Recursion：fixed12 − nonrec12|3|80.2222|+54.0000|+14.6667|+34.0000|+34.2222|
|Goal|official|Recursion：fixed12 − nonrec12|4|70.8889|+22.6667|+22.0000|+28.6667|+24.4444|
|Goal|official|Recursion：fixed12 − nonrec12|5|45.7778|+6.6667|-8.0000|-5.3333|-2.2222|
|Goal|official|Recursion：fixed12 − nonrec12|6|30.4444|+6.6667|+3.3333|-0.6667|+3.1111|
|Goal|official|Recursion：fixed12 − nonrec12|7|100.0000|+0.0000|+0.0000|+0.6667|+0.2222|
|Goal|official|Recursion：fixed12 − nonrec12|8|47.5556|+6.0000|+9.3333|-8.6667|+2.2222|
|Goal|official|Recursion：fixed12 − nonrec12|9|59.3333|+32.0000|+15.3333|-0.6667|+15.5556|
|Goal|official|Gate规则：guard12 − fixed12|0|8.0000|+1.3333|-2.0000|-3.3333|-1.3333|
|Goal|official|Gate规则：guard12 − fixed12|1|82.2222|+7.3333|+6.0000|+2.0000|+5.1111|
|Goal|official|Gate规则：guard12 − fixed12|2|65.7778|-10.6667|+10.0000|+0.0000|-0.2222|
|Goal|official|Gate规则：guard12 − fixed12|3|80.2222|-1.3333|-0.6667|+0.0000|-0.6667|
|Goal|official|Gate规则：guard12 − fixed12|4|70.8889|-3.3333|-3.3333|+1.3333|-1.7778|
|Goal|official|Gate规则：guard12 − fixed12|5|45.7778|+0.6667|+16.6667|+4.6667|+7.3333|
|Goal|official|Gate规则：guard12 − fixed12|6|30.4444|-9.3333|-2.6667|+9.3333|-0.8889|
|Goal|official|Gate规则：guard12 − fixed12|7|100.0000|-0.6667|+0.0000|+0.0000|-0.2222|
|Goal|official|Gate规则：guard12 − fixed12|8|47.5556|+0.6667|+2.0000|+2.0000|+1.5556|
|Goal|official|Gate规则：guard12 − fixed12|9|59.3333|-1.3333|-6.6667|+8.0000|+0.0000|
|Goal|official|BC Gate：fixed − nogate|0|8.0000|+0.0000|+4.6667|-0.6667|+1.3333|
|Goal|official|BC Gate：fixed − nogate|1|82.2222|+4.0000|+4.6667|+7.3333|+5.3333|
|Goal|official|BC Gate：fixed − nogate|2|65.7778|-1.3333|+4.0000|+12.6667|+5.1111|
|Goal|official|BC Gate：fixed − nogate|3|80.2222|+58.0000|+65.3333|+52.6667|+58.6667|
|Goal|official|BC Gate：fixed − nogate|4|70.8889|+4.6667|+2.0000|+5.3333|+4.0000|
|Goal|official|BC Gate：fixed − nogate|5|45.7778|+32.6667|+21.3333|+29.3333|+27.7778|
|Goal|official|BC Gate：fixed − nogate|6|30.4444|+11.3333|+15.3333|+21.3333|+16.0000|
|Goal|official|BC Gate：fixed − nogate|7|100.0000|-1.3333|+2.0000|+5.3333|+2.0000|
|Goal|official|BC Gate：fixed − nogate|8|47.5556|-2.6667|+16.0000|+4.0000|+5.7778|
|Goal|official|BC Gate：fixed − nogate|9|59.3333|+16.6667|+0.6667|+12.6667|+10.0000|
|Goal|official|LLM元层：LLM − fixed|0|8.0000|+5.3333|+1.3333|+0.6667|+2.4444|
|Goal|official|LLM元层：LLM − fixed|1|82.2222|+0.0000|+0.6667|-6.0000|-1.7778|
|Goal|official|LLM元层：LLM − fixed|2|65.7778|-0.6667|+1.3333|-0.6667|+0.0000|
|Goal|official|LLM元层：LLM − fixed|3|80.2222|+6.6667|-4.6667|-10.6667|-2.8889|
|Goal|official|LLM元层：LLM − fixed|4|70.8889|+14.6667|+20.6667|+10.6667|+15.3333|
|Goal|official|LLM元层：LLM − fixed|5|45.7778|+1.3333|-8.6667|+6.6667|-0.2222|
|Goal|official|LLM元层：LLM − fixed|6|30.4444|+2.6667|+4.6667|-6.0000|+0.4444|
|Goal|official|LLM元层：LLM − fixed|7|100.0000|+2.0000|+0.0000|+1.3333|+1.1111|
|Goal|official|LLM元层：LLM − fixed|8|47.5556|+8.0000|+6.6667|+6.6667|+7.1111|
|Goal|official|LLM元层：LLM − fixed|9|59.3333|+0.6667|+4.0000|+2.0000|+2.2222|
|Goal|fresh|Recursion：fixed12 − nonrec12|0|0.0000|-4.0000|-3.0000|-4.0000|-3.6667|
|Goal|fresh|Recursion：fixed12 − nonrec12|1|84.5000|+0.0000|+4.0000|-3.0000|+0.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|2|70.7500|+3.0000|-2.0000|+0.0000|+0.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|3|83.0000|+41.0000|+21.0000|+13.0000|+25.0000|
|Goal|fresh|Recursion：fixed12 − nonrec12|4|77.0000|+10.0000|+13.0000|+11.0000|+11.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|5|66.0000|+4.0000|-1.0000|+8.0000|+3.6667|
|Goal|fresh|Recursion：fixed12 − nonrec12|6|20.2500|+6.0000|+4.0000|+3.0000|+4.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|7|94.5000|-2.0000|-3.0000|+4.0000|-0.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|8|50.0000|-3.0000|+19.0000|+15.0000|+10.3333|
|Goal|fresh|Recursion：fixed12 − nonrec12|9|54.2500|+27.0000|+22.0000|+16.0000|+21.6667|
|Goal|fresh|Gate规则：guard12 − fixed12|0|0.0000|+2.0000|+1.0000|+0.0000|+1.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|1|84.5000|+0.0000|-1.0000|+4.0000|+1.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|2|70.7500|+9.0000|+3.0000|+0.0000|+4.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|3|83.0000|+4.0000|-9.0000|+12.0000|+2.3333|
|Goal|fresh|Gate规则：guard12 − fixed12|4|77.0000|-1.0000|-2.0000|-5.0000|-2.6667|
|Goal|fresh|Gate规则：guard12 − fixed12|5|66.0000|+10.0000|+0.0000|-1.0000|+3.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|6|20.2500|+6.0000|+1.0000|+8.0000|+5.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|7|94.5000|+3.0000|-1.0000|-1.0000|+0.3333|
|Goal|fresh|Gate规则：guard12 − fixed12|8|50.0000|+12.0000|-7.0000|-8.0000|-1.0000|
|Goal|fresh|Gate规则：guard12 − fixed12|9|54.2500|+15.0000|-5.0000|+1.0000|+3.6667|
|Goal|fresh|BC Gate：fixed − nogate|0|0.0000|-3.0000|+0.0000|-2.0000|-1.6667|
|Goal|fresh|BC Gate：fixed − nogate|1|84.5000|-2.0000|-5.0000|-3.0000|-3.3333|
|Goal|fresh|BC Gate：fixed − nogate|2|70.7500|+16.0000|+1.0000|+24.0000|+13.6667|
|Goal|fresh|BC Gate：fixed − nogate|3|83.0000|+57.0000|+62.0000|+62.0000|+60.3333|
|Goal|fresh|BC Gate：fixed − nogate|4|77.0000|+15.0000|+15.0000|+8.0000|+12.6667|
|Goal|fresh|BC Gate：fixed − nogate|5|66.0000|+46.0000|+29.0000|+23.0000|+32.6667|
|Goal|fresh|BC Gate：fixed − nogate|6|20.2500|+0.0000|+1.0000|+5.0000|+2.0000|
|Goal|fresh|BC Gate：fixed − nogate|7|94.5000|+2.0000|+2.0000|-2.0000|+0.6667|
|Goal|fresh|BC Gate：fixed − nogate|8|50.0000|+22.0000|+20.0000|+17.0000|+19.6667|
|Goal|fresh|BC Gate：fixed − nogate|9|54.2500|+19.0000|+7.0000|+28.0000|+18.0000|
|Goal|fresh|LLM元层：LLM − fixed|0|0.0000|+1.0000|+1.0000|+0.0000|+0.6667|
|Goal|fresh|LLM元层：LLM − fixed|1|84.5000|-6.0000|-4.0000|+7.0000|-1.0000|
|Goal|fresh|LLM元层：LLM − fixed|2|70.7500|+2.0000|+7.0000|-11.0000|-0.6667|
|Goal|fresh|LLM元层：LLM − fixed|3|83.0000|+23.0000|+0.0000|-2.0000|+7.0000|
|Goal|fresh|LLM元层：LLM − fixed|4|77.0000|+26.0000|+11.0000|-2.0000|+11.6667|
|Goal|fresh|LLM元层：LLM − fixed|5|66.0000|-4.0000|+2.0000|+6.0000|+1.3333|
|Goal|fresh|LLM元层：LLM − fixed|6|20.2500|+8.0000|+5.0000|+3.0000|+5.3333|
|Goal|fresh|LLM元层：LLM − fixed|7|94.5000|+7.0000|+2.0000|+3.0000|+4.0000|
|Goal|fresh|LLM元层：LLM − fixed|8|50.0000|+5.0000|+9.0000|+9.0000|+7.6667|
|Goal|fresh|LLM元层：LLM − fixed|9|54.2500|+5.0000|+2.0000|+15.0000|+7.3333|
|Spatial|official|Recursion：fixed12 − nonrec12|0|44.6667|+10.6667|+15.3333|+4.6667|+10.2222|
|Spatial|official|Recursion：fixed12 − nonrec12|1|6.2222|+8.0000|+6.0000|+2.6667|+5.5556|
|Spatial|official|Recursion：fixed12 − nonrec12|2|93.5556|-2.0000|+5.3333|+0.6667|+1.3333|
|Spatial|official|Recursion：fixed12 − nonrec12|3|81.7778|+17.3333|+20.0000|+6.0000|+14.4444|
|Spatial|official|Recursion：fixed12 − nonrec12|4|79.7778|+4.0000|-5.3333|+1.3333|+0.0000|
|Spatial|official|Recursion：fixed12 − nonrec12|5|3.1111|+6.6667|+7.3333|+1.3333|+5.1111|
|Spatial|official|Recursion：fixed12 − nonrec12|6|90.0000|+16.6667|+22.0000|+13.3333|+17.3333|
|Spatial|official|Recursion：fixed12 − nonrec12|7|59.3333|+22.6667|+6.0000|+6.0000|+11.5556|
|Spatial|official|Recursion：fixed12 − nonrec12|8|75.1111|+9.3333|+26.6667|+8.0000|+14.6667|
|Spatial|official|Recursion：fixed12 − nonrec12|9|68.2222|+10.6667|+0.6667|+8.0000|+6.4444|
|Spatial|official|Gate规则：guard12 − fixed12|0|44.6667|+2.6667|-11.3333|+16.0000|+2.4444|
|Spatial|official|Gate规则：guard12 − fixed12|1|6.2222|-4.0000|-2.6667|-2.0000|-2.8889|
|Spatial|official|Gate规则：guard12 − fixed12|2|93.5556|+3.3333|-0.6667|+2.0000|+1.5556|
|Spatial|official|Gate规则：guard12 − fixed12|3|81.7778|+0.6667|-4.0000|+7.3333|+1.3333|
|Spatial|official|Gate规则：guard12 − fixed12|4|79.7778|+10.0000|+1.3333|+2.0000|+4.4444|
|Spatial|official|Gate规则：guard12 − fixed12|5|3.1111|-2.6667|+3.3333|-2.0000|-0.4444|
|Spatial|official|Gate规则：guard12 − fixed12|6|90.0000|+7.3333|+0.0000|-4.6667|+0.8889|
|Spatial|official|Gate规则：guard12 − fixed12|7|59.3333|-1.3333|-6.0000|-6.0000|-4.4444|
|Spatial|official|Gate规则：guard12 − fixed12|8|75.1111|+6.6667|+0.0000|+3.3333|+3.3333|
|Spatial|official|Gate规则：guard12 − fixed12|9|68.2222|-1.3333|-6.0000|-2.6667|-3.3333|
|Spatial|official|BC Gate：fixed − nogate|0|44.6667|+7.3333|+6.6667|+8.0000|+7.3333|
|Spatial|official|BC Gate：fixed − nogate|1|6.2222|+2.0000|-0.6667|+6.0000|+2.4444|
|Spatial|official|BC Gate：fixed − nogate|2|93.5556|+13.3333|+8.0000|+7.3333|+9.5556|
|Spatial|official|BC Gate：fixed − nogate|3|81.7778|+8.0000|+15.3333|+6.0000|+9.7778|
|Spatial|official|BC Gate：fixed − nogate|4|79.7778|+24.0000|+7.3333|+15.3333|+15.5556|
|Spatial|official|BC Gate：fixed − nogate|5|3.1111|-2.6667|-3.3333|-0.6667|-2.2222|
|Spatial|official|BC Gate：fixed − nogate|6|90.0000|+25.3333|+14.0000|+18.0000|+19.1111|
|Spatial|official|BC Gate：fixed − nogate|7|59.3333|+20.6667|+20.0000|+9.3333|+16.6667|
|Spatial|official|BC Gate：fixed − nogate|8|75.1111|+22.0000|+24.6667|+26.0000|+24.2222|
|Spatial|official|BC Gate：fixed − nogate|9|68.2222|+26.0000|+38.6667|+18.0000|+27.5556|
|Spatial|official|LLM元层：LLM − fixed|0|44.6667|-8.0000|+8.0000|-1.3333|-0.4444|
|Spatial|official|LLM元层：LLM − fixed|1|6.2222|+5.3333|-1.3333|-5.3333|-0.4444|
|Spatial|official|LLM元层：LLM − fixed|2|93.5556|-2.6667|-0.6667|+2.6667|-0.2222|
|Spatial|official|LLM元层：LLM − fixed|3|81.7778|+2.6667|-4.0000|+0.6667|-0.2222|
|Spatial|official|LLM元层：LLM − fixed|4|79.7778|-4.0000|-3.3333|-2.6667|-3.3333|
|Spatial|official|LLM元层：LLM − fixed|5|3.1111|+8.0000|+0.0000|+0.6667|+2.8889|
|Spatial|official|LLM元层：LLM − fixed|6|90.0000|+8.6667|-6.0000|-10.0000|-2.4444|
|Spatial|official|LLM元层：LLM − fixed|7|59.3333|+7.3333|-22.0000|-6.0000|-6.8889|
|Spatial|official|LLM元层：LLM − fixed|8|75.1111|+4.6667|-4.0000|-4.6667|-1.3333|
|Spatial|official|LLM元层：LLM − fixed|9|68.2222|+4.0000|-14.6667|+2.6667|-2.6667|
|Spatial|fresh|Recursion：fixed12 − nonrec12|0|31.5000|+12.0000|+14.0000|-2.0000|+8.0000|
|Spatial|fresh|Recursion：fixed12 − nonrec12|1|1.5000|+3.0000|+24.0000|+12.0000|+13.0000|
|Spatial|fresh|Recursion：fixed12 − nonrec12|2|93.2500|+0.0000|+3.0000|-4.0000|-0.3333|
|Spatial|fresh|Recursion：fixed12 − nonrec12|3|96.2500|+10.0000|+13.0000|+8.0000|+10.3333|
|Spatial|fresh|Recursion：fixed12 − nonrec12|4|82.7500|+1.0000|-1.0000|+6.0000|+2.0000|
|Spatial|fresh|Recursion：fixed12 − nonrec12|5|1.0000|+12.0000|+16.0000|+22.0000|+16.6667|
|Spatial|fresh|Recursion：fixed12 − nonrec12|6|99.5000|+5.0000|+2.0000|+4.0000|+3.6667|
|Spatial|fresh|Recursion：fixed12 − nonrec12|7|37.0000|+32.0000|+21.0000|+18.0000|+23.6667|
|Spatial|fresh|Recursion：fixed12 − nonrec12|8|78.2500|+18.0000|+8.0000|+2.0000|+9.3333|
|Spatial|fresh|Recursion：fixed12 − nonrec12|9|74.5000|-6.0000|+1.0000|+5.0000|+0.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|0|31.5000|+2.0000|+3.0000|+13.0000|+6.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|1|1.5000|+11.0000|+0.0000|-2.0000|+3.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|2|93.2500|+0.0000|-4.0000|+1.0000|-1.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|3|96.2500|+1.0000|+1.0000|+1.0000|+1.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|4|82.7500|-4.0000|+3.0000|+0.0000|-0.3333|
|Spatial|fresh|Gate规则：guard12 − fixed12|5|1.0000|+17.0000|+4.0000|-9.0000|+4.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|6|99.5000|+1.0000|+0.0000|+2.0000|+1.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|7|37.0000|+2.0000|-20.0000|+6.0000|-4.0000|
|Spatial|fresh|Gate规则：guard12 − fixed12|8|78.2500|+0.0000|+0.0000|-2.0000|-0.6667|
|Spatial|fresh|Gate规则：guard12 − fixed12|9|74.5000|+4.0000|+9.0000|-5.0000|+2.6667|
|Spatial|fresh|BC Gate：fixed − nogate|0|31.5000|-18.0000|+4.0000|-27.0000|-13.6667|
|Spatial|fresh|BC Gate：fixed − nogate|1|1.5000|+1.0000|-2.0000|+1.0000|+0.0000|
|Spatial|fresh|BC Gate：fixed − nogate|2|93.2500|+12.0000|+11.0000|+17.0000|+13.3333|
|Spatial|fresh|BC Gate：fixed − nogate|3|96.2500|+4.0000|+4.0000|+4.0000|+4.0000|
|Spatial|fresh|BC Gate：fixed − nogate|4|82.7500|+15.0000|+8.0000|-4.0000|+6.3333|
|Spatial|fresh|BC Gate：fixed − nogate|5|1.0000|+2.0000|+1.0000|-1.0000|+0.6667|
|Spatial|fresh|BC Gate：fixed − nogate|6|99.5000|+5.0000|-4.0000|+4.0000|+1.6667|
|Spatial|fresh|BC Gate：fixed − nogate|7|37.0000|+10.0000|+47.0000|+18.0000|+25.0000|
|Spatial|fresh|BC Gate：fixed − nogate|8|78.2500|+14.0000|+22.0000|+32.0000|+22.6667|
|Spatial|fresh|BC Gate：fixed − nogate|9|74.5000|+35.0000|+16.0000|+20.0000|+23.6667|
|Spatial|fresh|LLM元层：LLM − fixed|0|31.5000|+8.0000|+4.0000|+33.0000|+15.0000|
|Spatial|fresh|LLM元层：LLM − fixed|1|1.5000|-1.0000|+0.0000|+2.0000|+0.3333|
|Spatial|fresh|LLM元层：LLM − fixed|2|93.2500|+0.0000|-2.0000|+0.0000|-0.6667|
|Spatial|fresh|LLM元层：LLM − fixed|3|96.2500|+0.0000|-2.0000|+6.0000|+1.3333|
|Spatial|fresh|LLM元层：LLM − fixed|4|82.7500|+2.0000|+0.0000|+5.0000|+2.3333|
|Spatial|fresh|LLM元层：LLM − fixed|5|1.0000|+14.0000|+3.0000|+4.0000|+7.0000|
|Spatial|fresh|LLM元层：LLM − fixed|6|99.5000|-1.0000|+3.0000|-1.0000|+0.3333|
|Spatial|fresh|LLM元层：LLM − fixed|7|37.0000|+52.0000|-2.0000|-24.0000|+8.6667|
|Spatial|fresh|LLM元层：LLM − fixed|8|78.2500|+7.0000|-4.0000|+0.0000|+1.0000|
|Spatial|fresh|LLM元层：LLM − fixed|9|74.5000|-1.0000|-2.0000|-6.0000|-3.0000|

## 7. 画图建议

主图横轴为初始任务成功率，纵轴为组件收益；每个面板10个task点，标task编号。Goal/Spatial及Official/Fresh分别分面；先完整展示所有组件，避免只保留Spatial Fresh的正向故事。

可在补充图画低/高初始组均值，但须注明每组仅5个task、分组为事后描述性划分。不要将50/100个episodes或3次评测当作50/100个独立任务。误差线若后续添加，必须说明重采样的层级，不能直接复用前面整体方法比较的CI。

建议图名：**Component gains versus initial task performance (exploratory)**。

## 8. 复算流程与关联结果

1. 读取Official任务ID列表、Fresh逐episode ID列表，并校验digest。
2. 对初始策略9次Official / 4次Fresh记录逐episode平均，再得到各task初始成功率。
3. 每个终态使用retained节点；Official取主运行+rep两次，Fresh只取首次。
4. 对每个seed、每个task计算实验臂减对照，平均3个seed得到task收益。
5. 以初始成功率分低/高5个task，计算各组均值及Spearman相关。Spearman对并列值使用平均秩。

统计公式：task收益 g_t = mean_s[success(arm,s,t) − success(control,s,t)]；低初始组均值=mean_{t∈low5}(g_t)。所有success在计算时以百分点尺度处理。

关联文档：[元层结果2](final_result2_readme.md)、[12轮recursion与gate规则结果3](final_result3_readme.md)、[Spatial gate两组对照结果4](final_result4_readme.md)。本文件另加入Goal BC gate，以完成跨suite的探索。

## 9. 全部原始来源索引

以下为实际使用的任务ID、初始参考、终态测试、配置、逐轮和来源文件。链接相对repo根目录。初始与终态都使用同平台Yangquan，A800文件仅提供一致digest的任务ID映射，不将A800成功率混入均值。

### 任务ID映射：a8_goalmain_fixed_s0

- [results/a800/runs2/a8_goalmain_fixed_s0/plan.json](results/a800/runs2/a8_goalmain_fixed_s0/plan.json)
- [results/a800/runs2/a8_goalmain_fixed_s0_fresh/test-libero_fresh-r04c0-rep1.jsonl](results/a800/runs2/a8_goalmain_fixed_s0_fresh/test-libero_fresh-r04c0-rep1.jsonl)

### 任务ID映射：a8_spatmain_fixed_s0

- [results/a800/runs2/a8_spatmain_fixed_s0/plan.json](results/a800/runs2/a8_spatmain_fixed_s0/plan.json)
- [results/a800/runs2/a8_spatmain_fixed_s0_fresh/test-libero_fresh-r06c0-rep1.jsonl](results/a800/runs2/a8_spatmain_fixed_s0_fresh/test-libero_fresh-r06c0-rep1.jsonl)

### Fresh初始参考：goal

- [results/baidu/yq_fresh_n0_goal_1/SOURCE-zw-rsi-yq-fresh-n0-goal-1.job-me07xk1cwddt.txt](results/baidu/yq_fresh_n0_goal_1/SOURCE-zw-rsi-yq-fresh-n0-goal-1.job-me07xk1cwddt.txt)
- [results/baidu/yq_fresh_n0_goal_1/test_eval.json](results/baidu/yq_fresh_n0_goal_1/test_eval.json)
- [results/baidu/yq_fresh_n0_goal_1/tests.txt](results/baidu/yq_fresh_n0_goal_1/tests.txt)
- [results/baidu/yq_fresh_n0_goal_2/SOURCE-zw-rsi-yq-fresh-n0-goal-2.job-hmo22o2ytzdw.txt](results/baidu/yq_fresh_n0_goal_2/SOURCE-zw-rsi-yq-fresh-n0-goal-2.job-hmo22o2ytzdw.txt)
- [results/baidu/yq_fresh_n0_goal_2/test_eval.json](results/baidu/yq_fresh_n0_goal_2/test_eval.json)
- [results/baidu/yq_fresh_n0_goal_2/tests.txt](results/baidu/yq_fresh_n0_goal_2/tests.txt)
- [results/baidu/yq_fresh_n0_goal_3/SOURCE-zw-rsi-yq-fresh-n0-goal-3.job-fjh06ly24at1.txt](results/baidu/yq_fresh_n0_goal_3/SOURCE-zw-rsi-yq-fresh-n0-goal-3.job-fjh06ly24at1.txt)
- [results/baidu/yq_fresh_n0_goal_3/test_eval.json](results/baidu/yq_fresh_n0_goal_3/test_eval.json)
- [results/baidu/yq_fresh_n0_goal_3/tests.txt](results/baidu/yq_fresh_n0_goal_3/tests.txt)
- [results/baidu/yq_fresh_n0_goal_4/SOURCE-zw-rsi-yq-fresh-n0-goal-4.job-s1qgkr479err.txt](results/baidu/yq_fresh_n0_goal_4/SOURCE-zw-rsi-yq-fresh-n0-goal-4.job-s1qgkr479err.txt)
- [results/baidu/yq_fresh_n0_goal_4/test_eval.json](results/baidu/yq_fresh_n0_goal_4/test_eval.json)
- [results/baidu/yq_fresh_n0_goal_4/tests.txt](results/baidu/yq_fresh_n0_goal_4/tests.txt)

### Fresh初始参考：spatial

- [results/baidu/yq_fresh_n0_spatial_1/SOURCE-zw-rsi-yq-fresh-n0-spatial-1.job-3bzp5htm4asc.txt](results/baidu/yq_fresh_n0_spatial_1/SOURCE-zw-rsi-yq-fresh-n0-spatial-1.job-3bzp5htm4asc.txt)
- [results/baidu/yq_fresh_n0_spatial_1/test_eval.json](results/baidu/yq_fresh_n0_spatial_1/test_eval.json)
- [results/baidu/yq_fresh_n0_spatial_1/tests.txt](results/baidu/yq_fresh_n0_spatial_1/tests.txt)
- [results/baidu/yq_fresh_n0_spatial_2/SOURCE-zw-rsi-yq-fresh-n0-spatial-2.job-8s5cpr8s781h.txt](results/baidu/yq_fresh_n0_spatial_2/SOURCE-zw-rsi-yq-fresh-n0-spatial-2.job-8s5cpr8s781h.txt)
- [results/baidu/yq_fresh_n0_spatial_2/test_eval.json](results/baidu/yq_fresh_n0_spatial_2/test_eval.json)
- [results/baidu/yq_fresh_n0_spatial_2/tests.txt](results/baidu/yq_fresh_n0_spatial_2/tests.txt)
- [results/baidu/yq_fresh_n0_spatial_3/SOURCE-zw-rsi-yq-fresh-n0-spatial-3.job-tyuhao4m566v.txt](results/baidu/yq_fresh_n0_spatial_3/SOURCE-zw-rsi-yq-fresh-n0-spatial-3.job-tyuhao4m566v.txt)
- [results/baidu/yq_fresh_n0_spatial_3/test_eval.json](results/baidu/yq_fresh_n0_spatial_3/test_eval.json)
- [results/baidu/yq_fresh_n0_spatial_3/tests.txt](results/baidu/yq_fresh_n0_spatial_3/tests.txt)
- [results/baidu/yq_fresh_n0_spatial_4/SOURCE-zw-rsi-yq-fresh-n0-spatial-4.job-2oe2yqn223la.txt](results/baidu/yq_fresh_n0_spatial_4/SOURCE-zw-rsi-yq-fresh-n0-spatial-4.job-2oe2yqn223la.txt)
- [results/baidu/yq_fresh_n0_spatial_4/test_eval.json](results/baidu/yq_fresh_n0_spatial_4/test_eval.json)
- [results/baidu/yq_fresh_n0_spatial_4/tests.txt](results/baidu/yq_fresh_n0_spatial_4/tests.txt)

### yq_oftg_fixed12_s1

- [results/baidu/yq_oftg_fixed12_s1/SOURCE-zw-rsi-yq-oftg-fixed12-s1.job-xo37dj1k4380.txt](results/baidu/yq_oftg_fixed12_s1/SOURCE-zw-rsi-yq-oftg-fixed12-s1.job-xo37dj1k4380.txt)
- [results/baidu/yq_oftg_fixed12_s1/accepted.jsonl](results/baidu/yq_oftg_fixed12_s1/accepted.jsonl)
- [results/baidu/yq_oftg_fixed12_s1/backend-accounting.json](results/baidu/yq_oftg_fixed12_s1/backend-accounting.json)
- [results/baidu/yq_oftg_fixed12_s1/report.json](results/baidu/yq_oftg_fixed12_s1/report.json)
- [results/baidu/yq_oftg_fixed12_s1/retained.json](results/baidu/yq_oftg_fixed12_s1/retained.json)
- [results/baidu/yq_oftg_fixed12_s1/round-01.json](results/baidu/yq_oftg_fixed12_s1/round-01.json)
- [results/baidu/yq_oftg_fixed12_s1/round-02.json](results/baidu/yq_oftg_fixed12_s1/round-02.json)
- [results/baidu/yq_oftg_fixed12_s1/round-03.json](results/baidu/yq_oftg_fixed12_s1/round-03.json)
- [results/baidu/yq_oftg_fixed12_s1/round-04.json](results/baidu/yq_oftg_fixed12_s1/round-04.json)
- [results/baidu/yq_oftg_fixed12_s1/round-05.json](results/baidu/yq_oftg_fixed12_s1/round-05.json)
- [results/baidu/yq_oftg_fixed12_s1/round-06.json](results/baidu/yq_oftg_fixed12_s1/round-06.json)
- [results/baidu/yq_oftg_fixed12_s1/round-07.json](results/baidu/yq_oftg_fixed12_s1/round-07.json)
- [results/baidu/yq_oftg_fixed12_s1/round-08.json](results/baidu/yq_oftg_fixed12_s1/round-08.json)
- [results/baidu/yq_oftg_fixed12_s1/round-09.json](results/baidu/yq_oftg_fixed12_s1/round-09.json)
- [results/baidu/yq_oftg_fixed12_s1/round-10.json](results/baidu/yq_oftg_fixed12_s1/round-10.json)
- [results/baidu/yq_oftg_fixed12_s1/round-11.json](results/baidu/yq_oftg_fixed12_s1/round-11.json)
- [results/baidu/yq_oftg_fixed12_s1/round-12.json](results/baidu/yq_oftg_fixed12_s1/round-12.json)
- [results/baidu/yq_oftg_fixed12_s1/tests.txt](results/baidu/yq_oftg_fixed12_s1/tests.txt)
- [results/baidu/yq_oftg_fixed12_s1_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s1-rep.job-c6vf2nao2tho.txt](results/baidu/yq_oftg_fixed12_s1_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s1-rep.job-c6vf2nao2tho.txt)
- [results/baidu/yq_oftg_fixed12_s1_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s1_rep/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s1_rep/tests.txt](results/baidu/yq_oftg_fixed12_s1_rep/tests.txt)
- [results/baidu/yq_oftg_fixed12_s1_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s1-fresh.job-wdgcol9vn6r1.txt](results/baidu/yq_oftg_fixed12_s1_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s1-fresh.job-wdgcol9vn6r1.txt)
- [results/baidu/yq_oftg_fixed12_s1_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s1_fresh/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s1_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s1_fresh/tests.txt)

### yq_oftg_fixed12_s2

- [results/baidu/yq_oftg_fixed12_s2/SOURCE-zw-rsi-yq-oftg-fixed12-s2.job-ld0nj3ihtqwr.txt](results/baidu/yq_oftg_fixed12_s2/SOURCE-zw-rsi-yq-oftg-fixed12-s2.job-ld0nj3ihtqwr.txt)
- [results/baidu/yq_oftg_fixed12_s2/accepted.jsonl](results/baidu/yq_oftg_fixed12_s2/accepted.jsonl)
- [results/baidu/yq_oftg_fixed12_s2/backend-accounting.json](results/baidu/yq_oftg_fixed12_s2/backend-accounting.json)
- [results/baidu/yq_oftg_fixed12_s2/report.json](results/baidu/yq_oftg_fixed12_s2/report.json)
- [results/baidu/yq_oftg_fixed12_s2/retained.json](results/baidu/yq_oftg_fixed12_s2/retained.json)
- [results/baidu/yq_oftg_fixed12_s2/round-01.json](results/baidu/yq_oftg_fixed12_s2/round-01.json)
- [results/baidu/yq_oftg_fixed12_s2/round-02.json](results/baidu/yq_oftg_fixed12_s2/round-02.json)
- [results/baidu/yq_oftg_fixed12_s2/round-03.json](results/baidu/yq_oftg_fixed12_s2/round-03.json)
- [results/baidu/yq_oftg_fixed12_s2/round-04.json](results/baidu/yq_oftg_fixed12_s2/round-04.json)
- [results/baidu/yq_oftg_fixed12_s2/round-05.json](results/baidu/yq_oftg_fixed12_s2/round-05.json)
- [results/baidu/yq_oftg_fixed12_s2/round-06.json](results/baidu/yq_oftg_fixed12_s2/round-06.json)
- [results/baidu/yq_oftg_fixed12_s2/round-07.json](results/baidu/yq_oftg_fixed12_s2/round-07.json)
- [results/baidu/yq_oftg_fixed12_s2/round-08.json](results/baidu/yq_oftg_fixed12_s2/round-08.json)
- [results/baidu/yq_oftg_fixed12_s2/round-09.json](results/baidu/yq_oftg_fixed12_s2/round-09.json)
- [results/baidu/yq_oftg_fixed12_s2/round-10.json](results/baidu/yq_oftg_fixed12_s2/round-10.json)
- [results/baidu/yq_oftg_fixed12_s2/round-11.json](results/baidu/yq_oftg_fixed12_s2/round-11.json)
- [results/baidu/yq_oftg_fixed12_s2/round-12.json](results/baidu/yq_oftg_fixed12_s2/round-12.json)
- [results/baidu/yq_oftg_fixed12_s2/tests.txt](results/baidu/yq_oftg_fixed12_s2/tests.txt)
- [results/baidu/yq_oftg_fixed12_s2_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s2-rep.job-f9w49ro5lnpz.txt](results/baidu/yq_oftg_fixed12_s2_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s2-rep.job-f9w49ro5lnpz.txt)
- [results/baidu/yq_oftg_fixed12_s2_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s2_rep/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s2_rep/tests.txt](results/baidu/yq_oftg_fixed12_s2_rep/tests.txt)
- [results/baidu/yq_oftg_fixed12_s2_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s2-fresh.job-gfd93hdcxdzt.txt](results/baidu/yq_oftg_fixed12_s2_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s2-fresh.job-gfd93hdcxdzt.txt)
- [results/baidu/yq_oftg_fixed12_s2_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s2_fresh/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s2_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s2_fresh/tests.txt)

### yq_oftg_fixed12_s3

- [results/baidu/yq_oftg_fixed12_s3/SOURCE-zw-rsi-yq-oftg-fixed12-s3.job-k78fwx973q5g.txt](results/baidu/yq_oftg_fixed12_s3/SOURCE-zw-rsi-yq-oftg-fixed12-s3.job-k78fwx973q5g.txt)
- [results/baidu/yq_oftg_fixed12_s3/accepted.jsonl](results/baidu/yq_oftg_fixed12_s3/accepted.jsonl)
- [results/baidu/yq_oftg_fixed12_s3/backend-accounting.json](results/baidu/yq_oftg_fixed12_s3/backend-accounting.json)
- [results/baidu/yq_oftg_fixed12_s3/report.json](results/baidu/yq_oftg_fixed12_s3/report.json)
- [results/baidu/yq_oftg_fixed12_s3/retained.json](results/baidu/yq_oftg_fixed12_s3/retained.json)
- [results/baidu/yq_oftg_fixed12_s3/round-01.json](results/baidu/yq_oftg_fixed12_s3/round-01.json)
- [results/baidu/yq_oftg_fixed12_s3/round-02.json](results/baidu/yq_oftg_fixed12_s3/round-02.json)
- [results/baidu/yq_oftg_fixed12_s3/round-03.json](results/baidu/yq_oftg_fixed12_s3/round-03.json)
- [results/baidu/yq_oftg_fixed12_s3/round-04.json](results/baidu/yq_oftg_fixed12_s3/round-04.json)
- [results/baidu/yq_oftg_fixed12_s3/round-05.json](results/baidu/yq_oftg_fixed12_s3/round-05.json)
- [results/baidu/yq_oftg_fixed12_s3/round-06.json](results/baidu/yq_oftg_fixed12_s3/round-06.json)
- [results/baidu/yq_oftg_fixed12_s3/round-07.json](results/baidu/yq_oftg_fixed12_s3/round-07.json)
- [results/baidu/yq_oftg_fixed12_s3/round-08.json](results/baidu/yq_oftg_fixed12_s3/round-08.json)
- [results/baidu/yq_oftg_fixed12_s3/round-09.json](results/baidu/yq_oftg_fixed12_s3/round-09.json)
- [results/baidu/yq_oftg_fixed12_s3/round-10.json](results/baidu/yq_oftg_fixed12_s3/round-10.json)
- [results/baidu/yq_oftg_fixed12_s3/round-11.json](results/baidu/yq_oftg_fixed12_s3/round-11.json)
- [results/baidu/yq_oftg_fixed12_s3/round-12.json](results/baidu/yq_oftg_fixed12_s3/round-12.json)
- [results/baidu/yq_oftg_fixed12_s3/tests.txt](results/baidu/yq_oftg_fixed12_s3/tests.txt)
- [results/baidu/yq_oftg_fixed12_s3_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s3-rep.job-ixtcsdlekh96.txt](results/baidu/yq_oftg_fixed12_s3_rep/SOURCE-zw-rsi-yq-oftg-fixed12-s3-rep.job-ixtcsdlekh96.txt)
- [results/baidu/yq_oftg_fixed12_s3_rep/test_eval.json](results/baidu/yq_oftg_fixed12_s3_rep/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s3_rep/tests.txt](results/baidu/yq_oftg_fixed12_s3_rep/tests.txt)
- [results/baidu/yq_oftg_fixed12_s3_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s3-fresh.job-jqz4jr4pcsnh.txt](results/baidu/yq_oftg_fixed12_s3_fresh/SOURCE-zw-rsi-yq-oftg-fixed12-s3-fresh.job-jqz4jr4pcsnh.txt)
- [results/baidu/yq_oftg_fixed12_s3_fresh/test_eval.json](results/baidu/yq_oftg_fixed12_s3_fresh/test_eval.json)
- [results/baidu/yq_oftg_fixed12_s3_fresh/tests.txt](results/baidu/yq_oftg_fixed12_s3_fresh/tests.txt)

### yq_oftg_nonrec12_s1

- [results/baidu/yq_oftg_nonrec12_s1/SOURCE-zw-rsi-yq-oftg-nonrec12-s1.job-0rxnjw9qyo3b.txt](results/baidu/yq_oftg_nonrec12_s1/SOURCE-zw-rsi-yq-oftg-nonrec12-s1.job-0rxnjw9qyo3b.txt)
- [results/baidu/yq_oftg_nonrec12_s1/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s1/accepted.jsonl)
- [results/baidu/yq_oftg_nonrec12_s1/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s1/backend-accounting.json)
- [results/baidu/yq_oftg_nonrec12_s1/report.json](results/baidu/yq_oftg_nonrec12_s1/report.json)
- [results/baidu/yq_oftg_nonrec12_s1/retained.json](results/baidu/yq_oftg_nonrec12_s1/retained.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-01.json](results/baidu/yq_oftg_nonrec12_s1/round-01.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-02.json](results/baidu/yq_oftg_nonrec12_s1/round-02.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-03.json](results/baidu/yq_oftg_nonrec12_s1/round-03.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-04.json](results/baidu/yq_oftg_nonrec12_s1/round-04.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-05.json](results/baidu/yq_oftg_nonrec12_s1/round-05.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-06.json](results/baidu/yq_oftg_nonrec12_s1/round-06.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-07.json](results/baidu/yq_oftg_nonrec12_s1/round-07.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-08.json](results/baidu/yq_oftg_nonrec12_s1/round-08.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-09.json](results/baidu/yq_oftg_nonrec12_s1/round-09.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-10.json](results/baidu/yq_oftg_nonrec12_s1/round-10.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-11.json](results/baidu/yq_oftg_nonrec12_s1/round-11.json)
- [results/baidu/yq_oftg_nonrec12_s1/round-12.json](results/baidu/yq_oftg_nonrec12_s1/round-12.json)
- [results/baidu/yq_oftg_nonrec12_s1/tests.txt](results/baidu/yq_oftg_nonrec12_s1/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s1_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-rep.job-vvdd8wfs8t11.txt](results/baidu/yq_oftg_nonrec12_s1_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-rep.job-vvdd8wfs8t11.txt)
- [results/baidu/yq_oftg_nonrec12_s1_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s1_rep/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s1_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s1_rep/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-fresh.job-03xakji40m9y.txt](results/baidu/yq_oftg_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s1-fresh.job-03xakji40m9y.txt)
- [results/baidu/yq_oftg_nonrec12_s1_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s1_fresh/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s1_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s1_fresh/tests.txt)

### yq_oftg_nonrec12_s2

- [results/baidu/yq_oftg_nonrec12_s2/SOURCE-zw-rsi-yq-oftg-nonrec12-s2.job-vimuv3tfi095.txt](results/baidu/yq_oftg_nonrec12_s2/SOURCE-zw-rsi-yq-oftg-nonrec12-s2.job-vimuv3tfi095.txt)
- [results/baidu/yq_oftg_nonrec12_s2/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s2/accepted.jsonl)
- [results/baidu/yq_oftg_nonrec12_s2/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s2/backend-accounting.json)
- [results/baidu/yq_oftg_nonrec12_s2/report.json](results/baidu/yq_oftg_nonrec12_s2/report.json)
- [results/baidu/yq_oftg_nonrec12_s2/retained.json](results/baidu/yq_oftg_nonrec12_s2/retained.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-01.json](results/baidu/yq_oftg_nonrec12_s2/round-01.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-02.json](results/baidu/yq_oftg_nonrec12_s2/round-02.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-03.json](results/baidu/yq_oftg_nonrec12_s2/round-03.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-04.json](results/baidu/yq_oftg_nonrec12_s2/round-04.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-05.json](results/baidu/yq_oftg_nonrec12_s2/round-05.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-06.json](results/baidu/yq_oftg_nonrec12_s2/round-06.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-07.json](results/baidu/yq_oftg_nonrec12_s2/round-07.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-08.json](results/baidu/yq_oftg_nonrec12_s2/round-08.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-09.json](results/baidu/yq_oftg_nonrec12_s2/round-09.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-10.json](results/baidu/yq_oftg_nonrec12_s2/round-10.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-11.json](results/baidu/yq_oftg_nonrec12_s2/round-11.json)
- [results/baidu/yq_oftg_nonrec12_s2/round-12.json](results/baidu/yq_oftg_nonrec12_s2/round-12.json)
- [results/baidu/yq_oftg_nonrec12_s2/tests.txt](results/baidu/yq_oftg_nonrec12_s2/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s2_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-rep.job-im0tp5uo0q19.txt](results/baidu/yq_oftg_nonrec12_s2_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-rep.job-im0tp5uo0q19.txt)
- [results/baidu/yq_oftg_nonrec12_s2_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s2_rep/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s2_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s2_rep/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-fresh.job-h4q9k8hyyghe.txt](results/baidu/yq_oftg_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s2-fresh.job-h4q9k8hyyghe.txt)
- [results/baidu/yq_oftg_nonrec12_s2_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s2_fresh/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s2_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s2_fresh/tests.txt)

### yq_oftg_nonrec12_s3

- [results/baidu/yq_oftg_nonrec12_s3/SOURCE-zw-rsi-yq-oftg-nonrec12-s3.job-861rdqeyr9wn.txt](results/baidu/yq_oftg_nonrec12_s3/SOURCE-zw-rsi-yq-oftg-nonrec12-s3.job-861rdqeyr9wn.txt)
- [results/baidu/yq_oftg_nonrec12_s3/accepted.jsonl](results/baidu/yq_oftg_nonrec12_s3/accepted.jsonl)
- [results/baidu/yq_oftg_nonrec12_s3/backend-accounting.json](results/baidu/yq_oftg_nonrec12_s3/backend-accounting.json)
- [results/baidu/yq_oftg_nonrec12_s3/report.json](results/baidu/yq_oftg_nonrec12_s3/report.json)
- [results/baidu/yq_oftg_nonrec12_s3/retained.json](results/baidu/yq_oftg_nonrec12_s3/retained.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-01.json](results/baidu/yq_oftg_nonrec12_s3/round-01.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-02.json](results/baidu/yq_oftg_nonrec12_s3/round-02.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-03.json](results/baidu/yq_oftg_nonrec12_s3/round-03.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-04.json](results/baidu/yq_oftg_nonrec12_s3/round-04.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-05.json](results/baidu/yq_oftg_nonrec12_s3/round-05.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-06.json](results/baidu/yq_oftg_nonrec12_s3/round-06.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-07.json](results/baidu/yq_oftg_nonrec12_s3/round-07.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-08.json](results/baidu/yq_oftg_nonrec12_s3/round-08.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-09.json](results/baidu/yq_oftg_nonrec12_s3/round-09.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-10.json](results/baidu/yq_oftg_nonrec12_s3/round-10.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-11.json](results/baidu/yq_oftg_nonrec12_s3/round-11.json)
- [results/baidu/yq_oftg_nonrec12_s3/round-12.json](results/baidu/yq_oftg_nonrec12_s3/round-12.json)
- [results/baidu/yq_oftg_nonrec12_s3/tests.txt](results/baidu/yq_oftg_nonrec12_s3/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s3_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-rep.job-g0rmg6m8b6dg.txt](results/baidu/yq_oftg_nonrec12_s3_rep/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-rep.job-g0rmg6m8b6dg.txt)
- [results/baidu/yq_oftg_nonrec12_s3_rep/test_eval.json](results/baidu/yq_oftg_nonrec12_s3_rep/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s3_rep/tests.txt](results/baidu/yq_oftg_nonrec12_s3_rep/tests.txt)
- [results/baidu/yq_oftg_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-fresh.job-c5qq35d02lnf.txt](results/baidu/yq_oftg_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-oftg-nonrec12-s3-fresh.job-c5qq35d02lnf.txt)
- [results/baidu/yq_oftg_nonrec12_s3_fresh/test_eval.json](results/baidu/yq_oftg_nonrec12_s3_fresh/test_eval.json)
- [results/baidu/yq_oftg_nonrec12_s3_fresh/tests.txt](results/baidu/yq_oftg_nonrec12_s3_fresh/tests.txt)

### yq_oftg_guard12_s1

- [results/baidu/yq_oftg_guard12_s1/SOURCE-zw-rsi-yq-oftg-guard12-s1.job-46g4mwxzzj65.txt](results/baidu/yq_oftg_guard12_s1/SOURCE-zw-rsi-yq-oftg-guard12-s1.job-46g4mwxzzj65.txt)
- [results/baidu/yq_oftg_guard12_s1/accepted.jsonl](results/baidu/yq_oftg_guard12_s1/accepted.jsonl)
- [results/baidu/yq_oftg_guard12_s1/backend-accounting.json](results/baidu/yq_oftg_guard12_s1/backend-accounting.json)
- [results/baidu/yq_oftg_guard12_s1/report.json](results/baidu/yq_oftg_guard12_s1/report.json)
- [results/baidu/yq_oftg_guard12_s1/retained.json](results/baidu/yq_oftg_guard12_s1/retained.json)
- [results/baidu/yq_oftg_guard12_s1/round-01.json](results/baidu/yq_oftg_guard12_s1/round-01.json)
- [results/baidu/yq_oftg_guard12_s1/round-02.json](results/baidu/yq_oftg_guard12_s1/round-02.json)
- [results/baidu/yq_oftg_guard12_s1/round-03.json](results/baidu/yq_oftg_guard12_s1/round-03.json)
- [results/baidu/yq_oftg_guard12_s1/round-04.json](results/baidu/yq_oftg_guard12_s1/round-04.json)
- [results/baidu/yq_oftg_guard12_s1/round-05.json](results/baidu/yq_oftg_guard12_s1/round-05.json)
- [results/baidu/yq_oftg_guard12_s1/round-06.json](results/baidu/yq_oftg_guard12_s1/round-06.json)
- [results/baidu/yq_oftg_guard12_s1/round-07.json](results/baidu/yq_oftg_guard12_s1/round-07.json)
- [results/baidu/yq_oftg_guard12_s1/round-08.json](results/baidu/yq_oftg_guard12_s1/round-08.json)
- [results/baidu/yq_oftg_guard12_s1/round-09.json](results/baidu/yq_oftg_guard12_s1/round-09.json)
- [results/baidu/yq_oftg_guard12_s1/round-10.json](results/baidu/yq_oftg_guard12_s1/round-10.json)
- [results/baidu/yq_oftg_guard12_s1/round-11.json](results/baidu/yq_oftg_guard12_s1/round-11.json)
- [results/baidu/yq_oftg_guard12_s1/round-12.json](results/baidu/yq_oftg_guard12_s1/round-12.json)
- [results/baidu/yq_oftg_guard12_s1/tests.txt](results/baidu/yq_oftg_guard12_s1/tests.txt)
- [results/baidu/yq_oftg_guard12_s1_rep/SOURCE-zw-rsi-yq-oftg-guard12-s1-rep.job-g8829gvuihs9.txt](results/baidu/yq_oftg_guard12_s1_rep/SOURCE-zw-rsi-yq-oftg-guard12-s1-rep.job-g8829gvuihs9.txt)
- [results/baidu/yq_oftg_guard12_s1_rep/test_eval.json](results/baidu/yq_oftg_guard12_s1_rep/test_eval.json)
- [results/baidu/yq_oftg_guard12_s1_rep/tests.txt](results/baidu/yq_oftg_guard12_s1_rep/tests.txt)
- [results/baidu/yq_oftg_guard12_s1_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s1-fresh.job-cle5ddrzjg69.txt](results/baidu/yq_oftg_guard12_s1_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s1-fresh.job-cle5ddrzjg69.txt)
- [results/baidu/yq_oftg_guard12_s1_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s1_fresh/test_eval.json)
- [results/baidu/yq_oftg_guard12_s1_fresh/tests.txt](results/baidu/yq_oftg_guard12_s1_fresh/tests.txt)

### yq_oftg_guard12_s2

- [results/baidu/yq_oftg_guard12_s2/SOURCE-zw-rsi-yq-oftg-guard12-s2.job-8w8ooykxt485.txt](results/baidu/yq_oftg_guard12_s2/SOURCE-zw-rsi-yq-oftg-guard12-s2.job-8w8ooykxt485.txt)
- [results/baidu/yq_oftg_guard12_s2/accepted.jsonl](results/baidu/yq_oftg_guard12_s2/accepted.jsonl)
- [results/baidu/yq_oftg_guard12_s2/backend-accounting.json](results/baidu/yq_oftg_guard12_s2/backend-accounting.json)
- [results/baidu/yq_oftg_guard12_s2/report.json](results/baidu/yq_oftg_guard12_s2/report.json)
- [results/baidu/yq_oftg_guard12_s2/retained.json](results/baidu/yq_oftg_guard12_s2/retained.json)
- [results/baidu/yq_oftg_guard12_s2/round-01.json](results/baidu/yq_oftg_guard12_s2/round-01.json)
- [results/baidu/yq_oftg_guard12_s2/round-02.json](results/baidu/yq_oftg_guard12_s2/round-02.json)
- [results/baidu/yq_oftg_guard12_s2/round-03.json](results/baidu/yq_oftg_guard12_s2/round-03.json)
- [results/baidu/yq_oftg_guard12_s2/round-04.json](results/baidu/yq_oftg_guard12_s2/round-04.json)
- [results/baidu/yq_oftg_guard12_s2/round-05.json](results/baidu/yq_oftg_guard12_s2/round-05.json)
- [results/baidu/yq_oftg_guard12_s2/round-06.json](results/baidu/yq_oftg_guard12_s2/round-06.json)
- [results/baidu/yq_oftg_guard12_s2/round-07.json](results/baidu/yq_oftg_guard12_s2/round-07.json)
- [results/baidu/yq_oftg_guard12_s2/round-08.json](results/baidu/yq_oftg_guard12_s2/round-08.json)
- [results/baidu/yq_oftg_guard12_s2/round-09.json](results/baidu/yq_oftg_guard12_s2/round-09.json)
- [results/baidu/yq_oftg_guard12_s2/round-10.json](results/baidu/yq_oftg_guard12_s2/round-10.json)
- [results/baidu/yq_oftg_guard12_s2/round-11.json](results/baidu/yq_oftg_guard12_s2/round-11.json)
- [results/baidu/yq_oftg_guard12_s2/round-12.json](results/baidu/yq_oftg_guard12_s2/round-12.json)
- [results/baidu/yq_oftg_guard12_s2/tests.txt](results/baidu/yq_oftg_guard12_s2/tests.txt)
- [results/baidu/yq_oftg_guard12_s2_rep/SOURCE-zw-rsi-yq-oftg-guard12-s2-rep.job-dv5ul4k9h33s.txt](results/baidu/yq_oftg_guard12_s2_rep/SOURCE-zw-rsi-yq-oftg-guard12-s2-rep.job-dv5ul4k9h33s.txt)
- [results/baidu/yq_oftg_guard12_s2_rep/test_eval.json](results/baidu/yq_oftg_guard12_s2_rep/test_eval.json)
- [results/baidu/yq_oftg_guard12_s2_rep/tests.txt](results/baidu/yq_oftg_guard12_s2_rep/tests.txt)
- [results/baidu/yq_oftg_guard12_s2_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s2-fresh.job-3f8xq9d51qhd.txt](results/baidu/yq_oftg_guard12_s2_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s2-fresh.job-3f8xq9d51qhd.txt)
- [results/baidu/yq_oftg_guard12_s2_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s2_fresh/test_eval.json)
- [results/baidu/yq_oftg_guard12_s2_fresh/tests.txt](results/baidu/yq_oftg_guard12_s2_fresh/tests.txt)

### yq_oftg_guard12_s3

- [results/baidu/yq_oftg_guard12_s3/SOURCE-zw-rsi-yq-oftg-guard12-s3.job-x05nk03gups9.txt](results/baidu/yq_oftg_guard12_s3/SOURCE-zw-rsi-yq-oftg-guard12-s3.job-x05nk03gups9.txt)
- [results/baidu/yq_oftg_guard12_s3/accepted.jsonl](results/baidu/yq_oftg_guard12_s3/accepted.jsonl)
- [results/baidu/yq_oftg_guard12_s3/backend-accounting.json](results/baidu/yq_oftg_guard12_s3/backend-accounting.json)
- [results/baidu/yq_oftg_guard12_s3/report.json](results/baidu/yq_oftg_guard12_s3/report.json)
- [results/baidu/yq_oftg_guard12_s3/retained.json](results/baidu/yq_oftg_guard12_s3/retained.json)
- [results/baidu/yq_oftg_guard12_s3/round-01.json](results/baidu/yq_oftg_guard12_s3/round-01.json)
- [results/baidu/yq_oftg_guard12_s3/round-02.json](results/baidu/yq_oftg_guard12_s3/round-02.json)
- [results/baidu/yq_oftg_guard12_s3/round-03.json](results/baidu/yq_oftg_guard12_s3/round-03.json)
- [results/baidu/yq_oftg_guard12_s3/round-04.json](results/baidu/yq_oftg_guard12_s3/round-04.json)
- [results/baidu/yq_oftg_guard12_s3/round-05.json](results/baidu/yq_oftg_guard12_s3/round-05.json)
- [results/baidu/yq_oftg_guard12_s3/round-06.json](results/baidu/yq_oftg_guard12_s3/round-06.json)
- [results/baidu/yq_oftg_guard12_s3/round-07.json](results/baidu/yq_oftg_guard12_s3/round-07.json)
- [results/baidu/yq_oftg_guard12_s3/round-08.json](results/baidu/yq_oftg_guard12_s3/round-08.json)
- [results/baidu/yq_oftg_guard12_s3/round-09.json](results/baidu/yq_oftg_guard12_s3/round-09.json)
- [results/baidu/yq_oftg_guard12_s3/round-10.json](results/baidu/yq_oftg_guard12_s3/round-10.json)
- [results/baidu/yq_oftg_guard12_s3/round-11.json](results/baidu/yq_oftg_guard12_s3/round-11.json)
- [results/baidu/yq_oftg_guard12_s3/round-12.json](results/baidu/yq_oftg_guard12_s3/round-12.json)
- [results/baidu/yq_oftg_guard12_s3/tests.txt](results/baidu/yq_oftg_guard12_s3/tests.txt)
- [results/baidu/yq_oftg_guard12_s3_rep/SOURCE-zw-rsi-yq-oftg-guard12-s3-rep.job-r62fgnatvzcm.txt](results/baidu/yq_oftg_guard12_s3_rep/SOURCE-zw-rsi-yq-oftg-guard12-s3-rep.job-r62fgnatvzcm.txt)
- [results/baidu/yq_oftg_guard12_s3_rep/test_eval.json](results/baidu/yq_oftg_guard12_s3_rep/test_eval.json)
- [results/baidu/yq_oftg_guard12_s3_rep/tests.txt](results/baidu/yq_oftg_guard12_s3_rep/tests.txt)
- [results/baidu/yq_oftg_guard12_s3_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s3-fresh.job-qrfb9r7l1wz8.txt](results/baidu/yq_oftg_guard12_s3_fresh/SOURCE-zw-rsi-yq-oftg-guard12-s3-fresh.job-qrfb9r7l1wz8.txt)
- [results/baidu/yq_oftg_guard12_s3_fresh/test_eval.json](results/baidu/yq_oftg_guard12_s3_fresh/test_eval.json)
- [results/baidu/yq_oftg_guard12_s3_fresh/tests.txt](results/baidu/yq_oftg_guard12_s3_fresh/tests.txt)

### yq_ofts_fixed12_s1

- [results/baidu/yq_ofts_fixed12_s1/SOURCE-zw-rsi-yq-ofts-fixed12-s1.job-1otcxo4s5vwd.txt](results/baidu/yq_ofts_fixed12_s1/SOURCE-zw-rsi-yq-ofts-fixed12-s1.job-1otcxo4s5vwd.txt)
- [results/baidu/yq_ofts_fixed12_s1/accepted.jsonl](results/baidu/yq_ofts_fixed12_s1/accepted.jsonl)
- [results/baidu/yq_ofts_fixed12_s1/backend-accounting.json](results/baidu/yq_ofts_fixed12_s1/backend-accounting.json)
- [results/baidu/yq_ofts_fixed12_s1/report.json](results/baidu/yq_ofts_fixed12_s1/report.json)
- [results/baidu/yq_ofts_fixed12_s1/retained.json](results/baidu/yq_ofts_fixed12_s1/retained.json)
- [results/baidu/yq_ofts_fixed12_s1/round-01.json](results/baidu/yq_ofts_fixed12_s1/round-01.json)
- [results/baidu/yq_ofts_fixed12_s1/round-02.json](results/baidu/yq_ofts_fixed12_s1/round-02.json)
- [results/baidu/yq_ofts_fixed12_s1/round-03.json](results/baidu/yq_ofts_fixed12_s1/round-03.json)
- [results/baidu/yq_ofts_fixed12_s1/round-04.json](results/baidu/yq_ofts_fixed12_s1/round-04.json)
- [results/baidu/yq_ofts_fixed12_s1/round-05.json](results/baidu/yq_ofts_fixed12_s1/round-05.json)
- [results/baidu/yq_ofts_fixed12_s1/round-06.json](results/baidu/yq_ofts_fixed12_s1/round-06.json)
- [results/baidu/yq_ofts_fixed12_s1/round-07.json](results/baidu/yq_ofts_fixed12_s1/round-07.json)
- [results/baidu/yq_ofts_fixed12_s1/round-08.json](results/baidu/yq_ofts_fixed12_s1/round-08.json)
- [results/baidu/yq_ofts_fixed12_s1/round-09.json](results/baidu/yq_ofts_fixed12_s1/round-09.json)
- [results/baidu/yq_ofts_fixed12_s1/round-10.json](results/baidu/yq_ofts_fixed12_s1/round-10.json)
- [results/baidu/yq_ofts_fixed12_s1/round-11.json](results/baidu/yq_ofts_fixed12_s1/round-11.json)
- [results/baidu/yq_ofts_fixed12_s1/round-12.json](results/baidu/yq_ofts_fixed12_s1/round-12.json)
- [results/baidu/yq_ofts_fixed12_s1/tests.txt](results/baidu/yq_ofts_fixed12_s1/tests.txt)
- [results/baidu/yq_ofts_fixed12_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s1-rep.job-px62coa58zi7.txt](results/baidu/yq_ofts_fixed12_s1_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s1-rep.job-px62coa58zi7.txt)
- [results/baidu/yq_ofts_fixed12_s1_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s1_rep/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s1_rep/tests.txt](results/baidu/yq_ofts_fixed12_s1_rep/tests.txt)
- [results/baidu/yq_ofts_fixed12_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s1-fresh.job-600ejaiwjb22.txt](results/baidu/yq_ofts_fixed12_s1_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s1-fresh.job-600ejaiwjb22.txt)
- [results/baidu/yq_ofts_fixed12_s1_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s1_fresh/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s1_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s1_fresh/tests.txt)

### yq_ofts_fixed12_s2

- [results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-kbdj1wgyi9jf.txt](results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-kbdj1wgyi9jf.txt)
- [results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-tvlypjmv56ku.txt](results/baidu/yq_ofts_fixed12_s2/SOURCE-zw-rsi-yq-ofts-fixed12-s2.job-tvlypjmv56ku.txt)
- [results/baidu/yq_ofts_fixed12_s2/accepted.jsonl](results/baidu/yq_ofts_fixed12_s2/accepted.jsonl)
- [results/baidu/yq_ofts_fixed12_s2/backend-accounting.json](results/baidu/yq_ofts_fixed12_s2/backend-accounting.json)
- [results/baidu/yq_ofts_fixed12_s2/failure.json](results/baidu/yq_ofts_fixed12_s2/failure.json)
- [results/baidu/yq_ofts_fixed12_s2/report.json](results/baidu/yq_ofts_fixed12_s2/report.json)
- [results/baidu/yq_ofts_fixed12_s2/retained.json](results/baidu/yq_ofts_fixed12_s2/retained.json)
- [results/baidu/yq_ofts_fixed12_s2/round-01.json](results/baidu/yq_ofts_fixed12_s2/round-01.json)
- [results/baidu/yq_ofts_fixed12_s2/round-02.json](results/baidu/yq_ofts_fixed12_s2/round-02.json)
- [results/baidu/yq_ofts_fixed12_s2/round-03.json](results/baidu/yq_ofts_fixed12_s2/round-03.json)
- [results/baidu/yq_ofts_fixed12_s2/round-04.json](results/baidu/yq_ofts_fixed12_s2/round-04.json)
- [results/baidu/yq_ofts_fixed12_s2/round-05.json](results/baidu/yq_ofts_fixed12_s2/round-05.json)
- [results/baidu/yq_ofts_fixed12_s2/round-06.json](results/baidu/yq_ofts_fixed12_s2/round-06.json)
- [results/baidu/yq_ofts_fixed12_s2/round-07.json](results/baidu/yq_ofts_fixed12_s2/round-07.json)
- [results/baidu/yq_ofts_fixed12_s2/round-08.json](results/baidu/yq_ofts_fixed12_s2/round-08.json)
- [results/baidu/yq_ofts_fixed12_s2/round-09.json](results/baidu/yq_ofts_fixed12_s2/round-09.json)
- [results/baidu/yq_ofts_fixed12_s2/round-10.json](results/baidu/yq_ofts_fixed12_s2/round-10.json)
- [results/baidu/yq_ofts_fixed12_s2/round-11.json](results/baidu/yq_ofts_fixed12_s2/round-11.json)
- [results/baidu/yq_ofts_fixed12_s2/round-12.json](results/baidu/yq_ofts_fixed12_s2/round-12.json)
- [results/baidu/yq_ofts_fixed12_s2/tests.txt](results/baidu/yq_ofts_fixed12_s2/tests.txt)
- [results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-20z213xryeb5.txt](results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-20z213xryeb5.txt)
- [results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-rmpuwh4lnr4p.txt](results/baidu/yq_ofts_fixed12_s2_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s2-rep.job-rmpuwh4lnr4p.txt)
- [results/baidu/yq_ofts_fixed12_s2_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s2_rep/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s2_rep/tests.txt](results/baidu/yq_ofts_fixed12_s2_rep/tests.txt)
- [results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-1gqg5wmyeipn.txt](results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-1gqg5wmyeipn.txt)
- [results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-orzet31zji4n.txt](results/baidu/yq_ofts_fixed12_s2_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s2-fresh.job-orzet31zji4n.txt)
- [results/baidu/yq_ofts_fixed12_s2_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s2_fresh/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s2_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s2_fresh/tests.txt)

### yq_ofts_fixed12_s3

- [results/baidu/yq_ofts_fixed12_s3/SOURCE-zw-rsi-yq-ofts-fixed12-s3.job-crj8uah8diwr.txt](results/baidu/yq_ofts_fixed12_s3/SOURCE-zw-rsi-yq-ofts-fixed12-s3.job-crj8uah8diwr.txt)
- [results/baidu/yq_ofts_fixed12_s3/accepted.jsonl](results/baidu/yq_ofts_fixed12_s3/accepted.jsonl)
- [results/baidu/yq_ofts_fixed12_s3/backend-accounting.json](results/baidu/yq_ofts_fixed12_s3/backend-accounting.json)
- [results/baidu/yq_ofts_fixed12_s3/report.json](results/baidu/yq_ofts_fixed12_s3/report.json)
- [results/baidu/yq_ofts_fixed12_s3/retained.json](results/baidu/yq_ofts_fixed12_s3/retained.json)
- [results/baidu/yq_ofts_fixed12_s3/round-01.json](results/baidu/yq_ofts_fixed12_s3/round-01.json)
- [results/baidu/yq_ofts_fixed12_s3/round-02.json](results/baidu/yq_ofts_fixed12_s3/round-02.json)
- [results/baidu/yq_ofts_fixed12_s3/round-03.json](results/baidu/yq_ofts_fixed12_s3/round-03.json)
- [results/baidu/yq_ofts_fixed12_s3/round-04.json](results/baidu/yq_ofts_fixed12_s3/round-04.json)
- [results/baidu/yq_ofts_fixed12_s3/round-05.json](results/baidu/yq_ofts_fixed12_s3/round-05.json)
- [results/baidu/yq_ofts_fixed12_s3/round-06.json](results/baidu/yq_ofts_fixed12_s3/round-06.json)
- [results/baidu/yq_ofts_fixed12_s3/round-07.json](results/baidu/yq_ofts_fixed12_s3/round-07.json)
- [results/baidu/yq_ofts_fixed12_s3/round-08.json](results/baidu/yq_ofts_fixed12_s3/round-08.json)
- [results/baidu/yq_ofts_fixed12_s3/round-09.json](results/baidu/yq_ofts_fixed12_s3/round-09.json)
- [results/baidu/yq_ofts_fixed12_s3/round-10.json](results/baidu/yq_ofts_fixed12_s3/round-10.json)
- [results/baidu/yq_ofts_fixed12_s3/round-11.json](results/baidu/yq_ofts_fixed12_s3/round-11.json)
- [results/baidu/yq_ofts_fixed12_s3/round-12.json](results/baidu/yq_ofts_fixed12_s3/round-12.json)
- [results/baidu/yq_ofts_fixed12_s3/tests.txt](results/baidu/yq_ofts_fixed12_s3/tests.txt)
- [results/baidu/yq_ofts_fixed12_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s3-rep.job-9g112ip74xjt.txt](results/baidu/yq_ofts_fixed12_s3_rep/SOURCE-zw-rsi-yq-ofts-fixed12-s3-rep.job-9g112ip74xjt.txt)
- [results/baidu/yq_ofts_fixed12_s3_rep/test_eval.json](results/baidu/yq_ofts_fixed12_s3_rep/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s3_rep/tests.txt](results/baidu/yq_ofts_fixed12_s3_rep/tests.txt)
- [results/baidu/yq_ofts_fixed12_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s3-fresh.job-bv4oak23ovma.txt](results/baidu/yq_ofts_fixed12_s3_fresh/SOURCE-zw-rsi-yq-ofts-fixed12-s3-fresh.job-bv4oak23ovma.txt)
- [results/baidu/yq_ofts_fixed12_s3_fresh/test_eval.json](results/baidu/yq_ofts_fixed12_s3_fresh/test_eval.json)
- [results/baidu/yq_ofts_fixed12_s3_fresh/tests.txt](results/baidu/yq_ofts_fixed12_s3_fresh/tests.txt)

### yq_ofts_nonrec12_s1

- [results/baidu/yq_ofts_nonrec12_s1/SOURCE-zw-rsi-yq-ofts-nonrec12-s1.job-e127wkwbtslp.txt](results/baidu/yq_ofts_nonrec12_s1/SOURCE-zw-rsi-yq-ofts-nonrec12-s1.job-e127wkwbtslp.txt)
- [results/baidu/yq_ofts_nonrec12_s1/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s1/accepted.jsonl)
- [results/baidu/yq_ofts_nonrec12_s1/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s1/backend-accounting.json)
- [results/baidu/yq_ofts_nonrec12_s1/report.json](results/baidu/yq_ofts_nonrec12_s1/report.json)
- [results/baidu/yq_ofts_nonrec12_s1/retained.json](results/baidu/yq_ofts_nonrec12_s1/retained.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-01.json](results/baidu/yq_ofts_nonrec12_s1/round-01.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-02.json](results/baidu/yq_ofts_nonrec12_s1/round-02.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-03.json](results/baidu/yq_ofts_nonrec12_s1/round-03.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-04.json](results/baidu/yq_ofts_nonrec12_s1/round-04.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-05.json](results/baidu/yq_ofts_nonrec12_s1/round-05.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-06.json](results/baidu/yq_ofts_nonrec12_s1/round-06.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-07.json](results/baidu/yq_ofts_nonrec12_s1/round-07.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-08.json](results/baidu/yq_ofts_nonrec12_s1/round-08.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-09.json](results/baidu/yq_ofts_nonrec12_s1/round-09.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-10.json](results/baidu/yq_ofts_nonrec12_s1/round-10.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-11.json](results/baidu/yq_ofts_nonrec12_s1/round-11.json)
- [results/baidu/yq_ofts_nonrec12_s1/round-12.json](results/baidu/yq_ofts_nonrec12_s1/round-12.json)
- [results/baidu/yq_ofts_nonrec12_s1/tests.txt](results/baidu/yq_ofts_nonrec12_s1/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s1_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-rep.job-2bdteuev4piw.txt](results/baidu/yq_ofts_nonrec12_s1_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-rep.job-2bdteuev4piw.txt)
- [results/baidu/yq_ofts_nonrec12_s1_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s1_rep/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s1_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s1_rep/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-fresh.job-mrccd8np8ayh.txt](results/baidu/yq_ofts_nonrec12_s1_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s1-fresh.job-mrccd8np8ayh.txt)
- [results/baidu/yq_ofts_nonrec12_s1_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s1_fresh/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s1_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s1_fresh/tests.txt)

### yq_ofts_nonrec12_s2

- [results/baidu/yq_ofts_nonrec12_s2/SOURCE-zw-rsi-yq-ofts-nonrec12-s2.job-39fu9qgar97l.txt](results/baidu/yq_ofts_nonrec12_s2/SOURCE-zw-rsi-yq-ofts-nonrec12-s2.job-39fu9qgar97l.txt)
- [results/baidu/yq_ofts_nonrec12_s2/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s2/accepted.jsonl)
- [results/baidu/yq_ofts_nonrec12_s2/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s2/backend-accounting.json)
- [results/baidu/yq_ofts_nonrec12_s2/report.json](results/baidu/yq_ofts_nonrec12_s2/report.json)
- [results/baidu/yq_ofts_nonrec12_s2/retained.json](results/baidu/yq_ofts_nonrec12_s2/retained.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-01.json](results/baidu/yq_ofts_nonrec12_s2/round-01.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-02.json](results/baidu/yq_ofts_nonrec12_s2/round-02.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-03.json](results/baidu/yq_ofts_nonrec12_s2/round-03.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-04.json](results/baidu/yq_ofts_nonrec12_s2/round-04.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-05.json](results/baidu/yq_ofts_nonrec12_s2/round-05.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-06.json](results/baidu/yq_ofts_nonrec12_s2/round-06.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-07.json](results/baidu/yq_ofts_nonrec12_s2/round-07.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-08.json](results/baidu/yq_ofts_nonrec12_s2/round-08.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-09.json](results/baidu/yq_ofts_nonrec12_s2/round-09.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-10.json](results/baidu/yq_ofts_nonrec12_s2/round-10.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-11.json](results/baidu/yq_ofts_nonrec12_s2/round-11.json)
- [results/baidu/yq_ofts_nonrec12_s2/round-12.json](results/baidu/yq_ofts_nonrec12_s2/round-12.json)
- [results/baidu/yq_ofts_nonrec12_s2/tests.txt](results/baidu/yq_ofts_nonrec12_s2/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s2_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-rep.job-op4yrzyrlyqu.txt](results/baidu/yq_ofts_nonrec12_s2_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-rep.job-op4yrzyrlyqu.txt)
- [results/baidu/yq_ofts_nonrec12_s2_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s2_rep/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s2_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s2_rep/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-fresh.job-thdw5mb6fnte.txt](results/baidu/yq_ofts_nonrec12_s2_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s2-fresh.job-thdw5mb6fnte.txt)
- [results/baidu/yq_ofts_nonrec12_s2_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s2_fresh/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s2_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s2_fresh/tests.txt)

### yq_ofts_nonrec12_s3

- [results/baidu/yq_ofts_nonrec12_s3/SOURCE-zw-rsi-yq-ofts-nonrec12-s3.job-ict95os7arqd.txt](results/baidu/yq_ofts_nonrec12_s3/SOURCE-zw-rsi-yq-ofts-nonrec12-s3.job-ict95os7arqd.txt)
- [results/baidu/yq_ofts_nonrec12_s3/accepted.jsonl](results/baidu/yq_ofts_nonrec12_s3/accepted.jsonl)
- [results/baidu/yq_ofts_nonrec12_s3/backend-accounting.json](results/baidu/yq_ofts_nonrec12_s3/backend-accounting.json)
- [results/baidu/yq_ofts_nonrec12_s3/report.json](results/baidu/yq_ofts_nonrec12_s3/report.json)
- [results/baidu/yq_ofts_nonrec12_s3/retained.json](results/baidu/yq_ofts_nonrec12_s3/retained.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-01.json](results/baidu/yq_ofts_nonrec12_s3/round-01.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-02.json](results/baidu/yq_ofts_nonrec12_s3/round-02.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-03.json](results/baidu/yq_ofts_nonrec12_s3/round-03.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-04.json](results/baidu/yq_ofts_nonrec12_s3/round-04.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-05.json](results/baidu/yq_ofts_nonrec12_s3/round-05.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-06.json](results/baidu/yq_ofts_nonrec12_s3/round-06.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-07.json](results/baidu/yq_ofts_nonrec12_s3/round-07.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-08.json](results/baidu/yq_ofts_nonrec12_s3/round-08.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-09.json](results/baidu/yq_ofts_nonrec12_s3/round-09.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-10.json](results/baidu/yq_ofts_nonrec12_s3/round-10.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-11.json](results/baidu/yq_ofts_nonrec12_s3/round-11.json)
- [results/baidu/yq_ofts_nonrec12_s3/round-12.json](results/baidu/yq_ofts_nonrec12_s3/round-12.json)
- [results/baidu/yq_ofts_nonrec12_s3/tests.txt](results/baidu/yq_ofts_nonrec12_s3/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s3_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-rep.job-zpo155dwl114.txt](results/baidu/yq_ofts_nonrec12_s3_rep/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-rep.job-zpo155dwl114.txt)
- [results/baidu/yq_ofts_nonrec12_s3_rep/test_eval.json](results/baidu/yq_ofts_nonrec12_s3_rep/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s3_rep/tests.txt](results/baidu/yq_ofts_nonrec12_s3_rep/tests.txt)
- [results/baidu/yq_ofts_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-fresh.job-fwg744geev32.txt](results/baidu/yq_ofts_nonrec12_s3_fresh/SOURCE-zw-rsi-yq-ofts-nonrec12-s3-fresh.job-fwg744geev32.txt)
- [results/baidu/yq_ofts_nonrec12_s3_fresh/test_eval.json](results/baidu/yq_ofts_nonrec12_s3_fresh/test_eval.json)
- [results/baidu/yq_ofts_nonrec12_s3_fresh/tests.txt](results/baidu/yq_ofts_nonrec12_s3_fresh/tests.txt)

### yq_ofts_guard12_s1

- [results/baidu/yq_ofts_guard12_s1/SOURCE-zw-rsi-yq-ofts-guard12-s1.job-vxncilkxz914.txt](results/baidu/yq_ofts_guard12_s1/SOURCE-zw-rsi-yq-ofts-guard12-s1.job-vxncilkxz914.txt)
- [results/baidu/yq_ofts_guard12_s1/accepted.jsonl](results/baidu/yq_ofts_guard12_s1/accepted.jsonl)
- [results/baidu/yq_ofts_guard12_s1/backend-accounting.json](results/baidu/yq_ofts_guard12_s1/backend-accounting.json)
- [results/baidu/yq_ofts_guard12_s1/report.json](results/baidu/yq_ofts_guard12_s1/report.json)
- [results/baidu/yq_ofts_guard12_s1/retained.json](results/baidu/yq_ofts_guard12_s1/retained.json)
- [results/baidu/yq_ofts_guard12_s1/round-01.json](results/baidu/yq_ofts_guard12_s1/round-01.json)
- [results/baidu/yq_ofts_guard12_s1/round-02.json](results/baidu/yq_ofts_guard12_s1/round-02.json)
- [results/baidu/yq_ofts_guard12_s1/round-03.json](results/baidu/yq_ofts_guard12_s1/round-03.json)
- [results/baidu/yq_ofts_guard12_s1/round-04.json](results/baidu/yq_ofts_guard12_s1/round-04.json)
- [results/baidu/yq_ofts_guard12_s1/round-05.json](results/baidu/yq_ofts_guard12_s1/round-05.json)
- [results/baidu/yq_ofts_guard12_s1/round-06.json](results/baidu/yq_ofts_guard12_s1/round-06.json)
- [results/baidu/yq_ofts_guard12_s1/round-07.json](results/baidu/yq_ofts_guard12_s1/round-07.json)
- [results/baidu/yq_ofts_guard12_s1/round-08.json](results/baidu/yq_ofts_guard12_s1/round-08.json)
- [results/baidu/yq_ofts_guard12_s1/round-09.json](results/baidu/yq_ofts_guard12_s1/round-09.json)
- [results/baidu/yq_ofts_guard12_s1/round-10.json](results/baidu/yq_ofts_guard12_s1/round-10.json)
- [results/baidu/yq_ofts_guard12_s1/round-11.json](results/baidu/yq_ofts_guard12_s1/round-11.json)
- [results/baidu/yq_ofts_guard12_s1/round-12.json](results/baidu/yq_ofts_guard12_s1/round-12.json)
- [results/baidu/yq_ofts_guard12_s1/tests.txt](results/baidu/yq_ofts_guard12_s1/tests.txt)
- [results/baidu/yq_ofts_guard12_s1_rep/SOURCE-zw-rsi-yq-ofts-guard12-s1-rep.job-8zq1r1mjtap2.txt](results/baidu/yq_ofts_guard12_s1_rep/SOURCE-zw-rsi-yq-ofts-guard12-s1-rep.job-8zq1r1mjtap2.txt)
- [results/baidu/yq_ofts_guard12_s1_rep/test_eval.json](results/baidu/yq_ofts_guard12_s1_rep/test_eval.json)
- [results/baidu/yq_ofts_guard12_s1_rep/tests.txt](results/baidu/yq_ofts_guard12_s1_rep/tests.txt)
- [results/baidu/yq_ofts_guard12_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s1-fresh.job-090oepab6ngy.txt](results/baidu/yq_ofts_guard12_s1_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s1-fresh.job-090oepab6ngy.txt)
- [results/baidu/yq_ofts_guard12_s1_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s1_fresh/test_eval.json)
- [results/baidu/yq_ofts_guard12_s1_fresh/tests.txt](results/baidu/yq_ofts_guard12_s1_fresh/tests.txt)

### yq_ofts_guard12_s2

- [results/baidu/yq_ofts_guard12_s2/SOURCE-zw-rsi-yq-ofts-guard12-s2.job-grh5jdus447h.txt](results/baidu/yq_ofts_guard12_s2/SOURCE-zw-rsi-yq-ofts-guard12-s2.job-grh5jdus447h.txt)
- [results/baidu/yq_ofts_guard12_s2/accepted.jsonl](results/baidu/yq_ofts_guard12_s2/accepted.jsonl)
- [results/baidu/yq_ofts_guard12_s2/backend-accounting.json](results/baidu/yq_ofts_guard12_s2/backend-accounting.json)
- [results/baidu/yq_ofts_guard12_s2/report.json](results/baidu/yq_ofts_guard12_s2/report.json)
- [results/baidu/yq_ofts_guard12_s2/retained.json](results/baidu/yq_ofts_guard12_s2/retained.json)
- [results/baidu/yq_ofts_guard12_s2/round-01.json](results/baidu/yq_ofts_guard12_s2/round-01.json)
- [results/baidu/yq_ofts_guard12_s2/round-02.json](results/baidu/yq_ofts_guard12_s2/round-02.json)
- [results/baidu/yq_ofts_guard12_s2/round-03.json](results/baidu/yq_ofts_guard12_s2/round-03.json)
- [results/baidu/yq_ofts_guard12_s2/round-04.json](results/baidu/yq_ofts_guard12_s2/round-04.json)
- [results/baidu/yq_ofts_guard12_s2/round-05.json](results/baidu/yq_ofts_guard12_s2/round-05.json)
- [results/baidu/yq_ofts_guard12_s2/round-06.json](results/baidu/yq_ofts_guard12_s2/round-06.json)
- [results/baidu/yq_ofts_guard12_s2/round-07.json](results/baidu/yq_ofts_guard12_s2/round-07.json)
- [results/baidu/yq_ofts_guard12_s2/round-08.json](results/baidu/yq_ofts_guard12_s2/round-08.json)
- [results/baidu/yq_ofts_guard12_s2/round-09.json](results/baidu/yq_ofts_guard12_s2/round-09.json)
- [results/baidu/yq_ofts_guard12_s2/round-10.json](results/baidu/yq_ofts_guard12_s2/round-10.json)
- [results/baidu/yq_ofts_guard12_s2/round-11.json](results/baidu/yq_ofts_guard12_s2/round-11.json)
- [results/baidu/yq_ofts_guard12_s2/round-12.json](results/baidu/yq_ofts_guard12_s2/round-12.json)
- [results/baidu/yq_ofts_guard12_s2/tests.txt](results/baidu/yq_ofts_guard12_s2/tests.txt)
- [results/baidu/yq_ofts_guard12_s2_rep/SOURCE-zw-rsi-yq-ofts-guard12-s2-rep.job-t9dplazqeesa.txt](results/baidu/yq_ofts_guard12_s2_rep/SOURCE-zw-rsi-yq-ofts-guard12-s2-rep.job-t9dplazqeesa.txt)
- [results/baidu/yq_ofts_guard12_s2_rep/test_eval.json](results/baidu/yq_ofts_guard12_s2_rep/test_eval.json)
- [results/baidu/yq_ofts_guard12_s2_rep/tests.txt](results/baidu/yq_ofts_guard12_s2_rep/tests.txt)
- [results/baidu/yq_ofts_guard12_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s2-fresh.job-pumd7vyzpwwx.txt](results/baidu/yq_ofts_guard12_s2_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s2-fresh.job-pumd7vyzpwwx.txt)
- [results/baidu/yq_ofts_guard12_s2_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s2_fresh/test_eval.json)
- [results/baidu/yq_ofts_guard12_s2_fresh/tests.txt](results/baidu/yq_ofts_guard12_s2_fresh/tests.txt)

### yq_ofts_guard12_s3

- [results/baidu/yq_ofts_guard12_s3/SOURCE-zw-rsi-yq-ofts-guard12-s3.job-7tir38px7755.txt](results/baidu/yq_ofts_guard12_s3/SOURCE-zw-rsi-yq-ofts-guard12-s3.job-7tir38px7755.txt)
- [results/baidu/yq_ofts_guard12_s3/accepted.jsonl](results/baidu/yq_ofts_guard12_s3/accepted.jsonl)
- [results/baidu/yq_ofts_guard12_s3/backend-accounting.json](results/baidu/yq_ofts_guard12_s3/backend-accounting.json)
- [results/baidu/yq_ofts_guard12_s3/report.json](results/baidu/yq_ofts_guard12_s3/report.json)
- [results/baidu/yq_ofts_guard12_s3/retained.json](results/baidu/yq_ofts_guard12_s3/retained.json)
- [results/baidu/yq_ofts_guard12_s3/round-01.json](results/baidu/yq_ofts_guard12_s3/round-01.json)
- [results/baidu/yq_ofts_guard12_s3/round-02.json](results/baidu/yq_ofts_guard12_s3/round-02.json)
- [results/baidu/yq_ofts_guard12_s3/round-03.json](results/baidu/yq_ofts_guard12_s3/round-03.json)
- [results/baidu/yq_ofts_guard12_s3/round-04.json](results/baidu/yq_ofts_guard12_s3/round-04.json)
- [results/baidu/yq_ofts_guard12_s3/round-05.json](results/baidu/yq_ofts_guard12_s3/round-05.json)
- [results/baidu/yq_ofts_guard12_s3/round-06.json](results/baidu/yq_ofts_guard12_s3/round-06.json)
- [results/baidu/yq_ofts_guard12_s3/round-07.json](results/baidu/yq_ofts_guard12_s3/round-07.json)
- [results/baidu/yq_ofts_guard12_s3/round-08.json](results/baidu/yq_ofts_guard12_s3/round-08.json)
- [results/baidu/yq_ofts_guard12_s3/round-09.json](results/baidu/yq_ofts_guard12_s3/round-09.json)
- [results/baidu/yq_ofts_guard12_s3/round-10.json](results/baidu/yq_ofts_guard12_s3/round-10.json)
- [results/baidu/yq_ofts_guard12_s3/round-11.json](results/baidu/yq_ofts_guard12_s3/round-11.json)
- [results/baidu/yq_ofts_guard12_s3/round-12.json](results/baidu/yq_ofts_guard12_s3/round-12.json)
- [results/baidu/yq_ofts_guard12_s3/tests.txt](results/baidu/yq_ofts_guard12_s3/tests.txt)
- [results/baidu/yq_ofts_guard12_s3_rep/SOURCE-zw-rsi-yq-ofts-guard12-s3-rep.job-7lw75ykjpkol.txt](results/baidu/yq_ofts_guard12_s3_rep/SOURCE-zw-rsi-yq-ofts-guard12-s3-rep.job-7lw75ykjpkol.txt)
- [results/baidu/yq_ofts_guard12_s3_rep/test_eval.json](results/baidu/yq_ofts_guard12_s3_rep/test_eval.json)
- [results/baidu/yq_ofts_guard12_s3_rep/tests.txt](results/baidu/yq_ofts_guard12_s3_rep/tests.txt)
- [results/baidu/yq_ofts_guard12_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s3-fresh.job-2rizf2ary0ih.txt](results/baidu/yq_ofts_guard12_s3_fresh/SOURCE-zw-rsi-yq-ofts-guard12-s3-fresh.job-2rizf2ary0ih.txt)
- [results/baidu/yq_ofts_guard12_s3_fresh/test_eval.json](results/baidu/yq_ofts_guard12_s3_fresh/test_eval.json)
- [results/baidu/yq_ofts_guard12_s3_fresh/tests.txt](results/baidu/yq_ofts_guard12_s3_fresh/tests.txt)

### yq_oftgb_fixed_s1

- [results/baidu/yq_oftgb_fixed_s1/SOURCE-zw-rsi-yq-oftgb-fixed-s1.job-vx48yb55dn28.txt](results/baidu/yq_oftgb_fixed_s1/SOURCE-zw-rsi-yq-oftgb-fixed-s1.job-vx48yb55dn28.txt)
- [results/baidu/yq_oftgb_fixed_s1/accepted.jsonl](results/baidu/yq_oftgb_fixed_s1/accepted.jsonl)
- [results/baidu/yq_oftgb_fixed_s1/backend-accounting.json](results/baidu/yq_oftgb_fixed_s1/backend-accounting.json)
- [results/baidu/yq_oftgb_fixed_s1/report.json](results/baidu/yq_oftgb_fixed_s1/report.json)
- [results/baidu/yq_oftgb_fixed_s1/retained.json](results/baidu/yq_oftgb_fixed_s1/retained.json)
- [results/baidu/yq_oftgb_fixed_s1/round-01.json](results/baidu/yq_oftgb_fixed_s1/round-01.json)
- [results/baidu/yq_oftgb_fixed_s1/round-02.json](results/baidu/yq_oftgb_fixed_s1/round-02.json)
- [results/baidu/yq_oftgb_fixed_s1/round-03.json](results/baidu/yq_oftgb_fixed_s1/round-03.json)
- [results/baidu/yq_oftgb_fixed_s1/round-04.json](results/baidu/yq_oftgb_fixed_s1/round-04.json)
- [results/baidu/yq_oftgb_fixed_s1/round-05.json](results/baidu/yq_oftgb_fixed_s1/round-05.json)
- [results/baidu/yq_oftgb_fixed_s1/round-06.json](results/baidu/yq_oftgb_fixed_s1/round-06.json)
- [results/baidu/yq_oftgb_fixed_s1/tests.txt](results/baidu/yq_oftgb_fixed_s1/tests.txt)
- [results/baidu/yq_oftgb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s1-rep.job-054gb6izh33m.txt](results/baidu/yq_oftgb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s1-rep.job-054gb6izh33m.txt)
- [results/baidu/yq_oftgb_fixed_s1_rep/test_eval.json](results/baidu/yq_oftgb_fixed_s1_rep/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s1_rep/tests.txt](results/baidu/yq_oftgb_fixed_s1_rep/tests.txt)
- [results/baidu/yq_oftgb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s1-fresh.job-17xdg4lp3690.txt](results/baidu/yq_oftgb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s1-fresh.job-17xdg4lp3690.txt)
- [results/baidu/yq_oftgb_fixed_s1_fresh/test_eval.json](results/baidu/yq_oftgb_fixed_s1_fresh/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s1_fresh/tests.txt](results/baidu/yq_oftgb_fixed_s1_fresh/tests.txt)

### yq_oftgb_fixed_s2

- [results/baidu/yq_oftgb_fixed_s2/SOURCE-zw-rsi-yq-oftgb-fixed-s2.job-bv6dlvbxznq5.txt](results/baidu/yq_oftgb_fixed_s2/SOURCE-zw-rsi-yq-oftgb-fixed-s2.job-bv6dlvbxznq5.txt)
- [results/baidu/yq_oftgb_fixed_s2/backend-accounting.json](results/baidu/yq_oftgb_fixed_s2/backend-accounting.json)
- [results/baidu/yq_oftgb_fixed_s2/report.json](results/baidu/yq_oftgb_fixed_s2/report.json)
- [results/baidu/yq_oftgb_fixed_s2/retained.json](results/baidu/yq_oftgb_fixed_s2/retained.json)
- [results/baidu/yq_oftgb_fixed_s2/round-01.json](results/baidu/yq_oftgb_fixed_s2/round-01.json)
- [results/baidu/yq_oftgb_fixed_s2/round-02.json](results/baidu/yq_oftgb_fixed_s2/round-02.json)
- [results/baidu/yq_oftgb_fixed_s2/round-03.json](results/baidu/yq_oftgb_fixed_s2/round-03.json)
- [results/baidu/yq_oftgb_fixed_s2/round-04.json](results/baidu/yq_oftgb_fixed_s2/round-04.json)
- [results/baidu/yq_oftgb_fixed_s2/round-05.json](results/baidu/yq_oftgb_fixed_s2/round-05.json)
- [results/baidu/yq_oftgb_fixed_s2/round-06.json](results/baidu/yq_oftgb_fixed_s2/round-06.json)
- [results/baidu/yq_oftgb_fixed_s2/tests.txt](results/baidu/yq_oftgb_fixed_s2/tests.txt)
- [results/baidu/yq_oftgb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s2-rep.job-nfdmqwx1k8x6.txt](results/baidu/yq_oftgb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s2-rep.job-nfdmqwx1k8x6.txt)
- [results/baidu/yq_oftgb_fixed_s2_rep/test_eval.json](results/baidu/yq_oftgb_fixed_s2_rep/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s2_rep/tests.txt](results/baidu/yq_oftgb_fixed_s2_rep/tests.txt)
- [results/baidu/yq_oftgb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s2-fresh.job-s9owb2jzgw76.txt](results/baidu/yq_oftgb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s2-fresh.job-s9owb2jzgw76.txt)
- [results/baidu/yq_oftgb_fixed_s2_fresh/test_eval.json](results/baidu/yq_oftgb_fixed_s2_fresh/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s2_fresh/tests.txt](results/baidu/yq_oftgb_fixed_s2_fresh/tests.txt)

### yq_oftgb_fixed_s3

- [results/baidu/yq_oftgb_fixed_s3/SOURCE-zw-rsi-yq-oftgb-fixed-s3.job-ljwhdzou3x5l.txt](results/baidu/yq_oftgb_fixed_s3/SOURCE-zw-rsi-yq-oftgb-fixed-s3.job-ljwhdzou3x5l.txt)
- [results/baidu/yq_oftgb_fixed_s3/accepted.jsonl](results/baidu/yq_oftgb_fixed_s3/accepted.jsonl)
- [results/baidu/yq_oftgb_fixed_s3/backend-accounting.json](results/baidu/yq_oftgb_fixed_s3/backend-accounting.json)
- [results/baidu/yq_oftgb_fixed_s3/report.json](results/baidu/yq_oftgb_fixed_s3/report.json)
- [results/baidu/yq_oftgb_fixed_s3/retained.json](results/baidu/yq_oftgb_fixed_s3/retained.json)
- [results/baidu/yq_oftgb_fixed_s3/round-01.json](results/baidu/yq_oftgb_fixed_s3/round-01.json)
- [results/baidu/yq_oftgb_fixed_s3/round-02.json](results/baidu/yq_oftgb_fixed_s3/round-02.json)
- [results/baidu/yq_oftgb_fixed_s3/round-03.json](results/baidu/yq_oftgb_fixed_s3/round-03.json)
- [results/baidu/yq_oftgb_fixed_s3/round-04.json](results/baidu/yq_oftgb_fixed_s3/round-04.json)
- [results/baidu/yq_oftgb_fixed_s3/round-05.json](results/baidu/yq_oftgb_fixed_s3/round-05.json)
- [results/baidu/yq_oftgb_fixed_s3/round-06.json](results/baidu/yq_oftgb_fixed_s3/round-06.json)
- [results/baidu/yq_oftgb_fixed_s3/tests.txt](results/baidu/yq_oftgb_fixed_s3/tests.txt)
- [results/baidu/yq_oftgb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s3-rep.job-xn5yqrat0q0a.txt](results/baidu/yq_oftgb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftgb-fixed-s3-rep.job-xn5yqrat0q0a.txt)
- [results/baidu/yq_oftgb_fixed_s3_rep/test_eval.json](results/baidu/yq_oftgb_fixed_s3_rep/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s3_rep/tests.txt](results/baidu/yq_oftgb_fixed_s3_rep/tests.txt)
- [results/baidu/yq_oftgb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s3-fresh.job-tag1xsbladfa.txt](results/baidu/yq_oftgb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftgb-fixed-s3-fresh.job-tag1xsbladfa.txt)
- [results/baidu/yq_oftgb_fixed_s3_fresh/test_eval.json](results/baidu/yq_oftgb_fixed_s3_fresh/test_eval.json)
- [results/baidu/yq_oftgb_fixed_s3_fresh/tests.txt](results/baidu/yq_oftgb_fixed_s3_fresh/tests.txt)

### yq_oftgb_nogate_s1

- [results/baidu/yq_oftgb_nogate_s1/SOURCE-zw-rsi-yq-oftgb-nogate-s1.job-e88rdaobdpbo.txt](results/baidu/yq_oftgb_nogate_s1/SOURCE-zw-rsi-yq-oftgb-nogate-s1.job-e88rdaobdpbo.txt)
- [results/baidu/yq_oftgb_nogate_s1/accepted.jsonl](results/baidu/yq_oftgb_nogate_s1/accepted.jsonl)
- [results/baidu/yq_oftgb_nogate_s1/backend-accounting.json](results/baidu/yq_oftgb_nogate_s1/backend-accounting.json)
- [results/baidu/yq_oftgb_nogate_s1/report.json](results/baidu/yq_oftgb_nogate_s1/report.json)
- [results/baidu/yq_oftgb_nogate_s1/retained.json](results/baidu/yq_oftgb_nogate_s1/retained.json)
- [results/baidu/yq_oftgb_nogate_s1/round-01.json](results/baidu/yq_oftgb_nogate_s1/round-01.json)
- [results/baidu/yq_oftgb_nogate_s1/round-02.json](results/baidu/yq_oftgb_nogate_s1/round-02.json)
- [results/baidu/yq_oftgb_nogate_s1/round-03.json](results/baidu/yq_oftgb_nogate_s1/round-03.json)
- [results/baidu/yq_oftgb_nogate_s1/round-04.json](results/baidu/yq_oftgb_nogate_s1/round-04.json)
- [results/baidu/yq_oftgb_nogate_s1/round-05.json](results/baidu/yq_oftgb_nogate_s1/round-05.json)
- [results/baidu/yq_oftgb_nogate_s1/round-06.json](results/baidu/yq_oftgb_nogate_s1/round-06.json)
- [results/baidu/yq_oftgb_nogate_s1/tests.txt](results/baidu/yq_oftgb_nogate_s1/tests.txt)
- [results/baidu/yq_oftgb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s1-rep.job-63pajpw5wla3.txt](results/baidu/yq_oftgb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s1-rep.job-63pajpw5wla3.txt)
- [results/baidu/yq_oftgb_nogate_s1_rep/test_eval.json](results/baidu/yq_oftgb_nogate_s1_rep/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s1_rep/tests.txt](results/baidu/yq_oftgb_nogate_s1_rep/tests.txt)
- [results/baidu/yq_oftgb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s1-fresh.job-p5gdijig4teb.txt](results/baidu/yq_oftgb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s1-fresh.job-p5gdijig4teb.txt)
- [results/baidu/yq_oftgb_nogate_s1_fresh/test_eval.json](results/baidu/yq_oftgb_nogate_s1_fresh/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s1_fresh/tests.txt](results/baidu/yq_oftgb_nogate_s1_fresh/tests.txt)

### yq_oftgb_nogate_s2

- [results/baidu/yq_oftgb_nogate_s2/SOURCE-zw-rsi-yq-oftgb-nogate-s2.job-8ktjo3p11r04.txt](results/baidu/yq_oftgb_nogate_s2/SOURCE-zw-rsi-yq-oftgb-nogate-s2.job-8ktjo3p11r04.txt)
- [results/baidu/yq_oftgb_nogate_s2/accepted.jsonl](results/baidu/yq_oftgb_nogate_s2/accepted.jsonl)
- [results/baidu/yq_oftgb_nogate_s2/backend-accounting.json](results/baidu/yq_oftgb_nogate_s2/backend-accounting.json)
- [results/baidu/yq_oftgb_nogate_s2/report.json](results/baidu/yq_oftgb_nogate_s2/report.json)
- [results/baidu/yq_oftgb_nogate_s2/retained.json](results/baidu/yq_oftgb_nogate_s2/retained.json)
- [results/baidu/yq_oftgb_nogate_s2/round-01.json](results/baidu/yq_oftgb_nogate_s2/round-01.json)
- [results/baidu/yq_oftgb_nogate_s2/round-02.json](results/baidu/yq_oftgb_nogate_s2/round-02.json)
- [results/baidu/yq_oftgb_nogate_s2/round-03.json](results/baidu/yq_oftgb_nogate_s2/round-03.json)
- [results/baidu/yq_oftgb_nogate_s2/round-04.json](results/baidu/yq_oftgb_nogate_s2/round-04.json)
- [results/baidu/yq_oftgb_nogate_s2/round-05.json](results/baidu/yq_oftgb_nogate_s2/round-05.json)
- [results/baidu/yq_oftgb_nogate_s2/round-06.json](results/baidu/yq_oftgb_nogate_s2/round-06.json)
- [results/baidu/yq_oftgb_nogate_s2/tests.txt](results/baidu/yq_oftgb_nogate_s2/tests.txt)
- [results/baidu/yq_oftgb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s2-rep.job-860bmihb6cez.txt](results/baidu/yq_oftgb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s2-rep.job-860bmihb6cez.txt)
- [results/baidu/yq_oftgb_nogate_s2_rep/test_eval.json](results/baidu/yq_oftgb_nogate_s2_rep/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s2_rep/tests.txt](results/baidu/yq_oftgb_nogate_s2_rep/tests.txt)
- [results/baidu/yq_oftgb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s2-fresh.job-14c4tpoajh0w.txt](results/baidu/yq_oftgb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s2-fresh.job-14c4tpoajh0w.txt)
- [results/baidu/yq_oftgb_nogate_s2_fresh/test_eval.json](results/baidu/yq_oftgb_nogate_s2_fresh/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s2_fresh/tests.txt](results/baidu/yq_oftgb_nogate_s2_fresh/tests.txt)

### yq_oftgb_nogate_s3

- [results/baidu/yq_oftgb_nogate_s3/SOURCE-zw-rsi-yq-oftgb-nogate-s3.job-5tdyl9twn22e.txt](results/baidu/yq_oftgb_nogate_s3/SOURCE-zw-rsi-yq-oftgb-nogate-s3.job-5tdyl9twn22e.txt)
- [results/baidu/yq_oftgb_nogate_s3/accepted.jsonl](results/baidu/yq_oftgb_nogate_s3/accepted.jsonl)
- [results/baidu/yq_oftgb_nogate_s3/backend-accounting.json](results/baidu/yq_oftgb_nogate_s3/backend-accounting.json)
- [results/baidu/yq_oftgb_nogate_s3/report.json](results/baidu/yq_oftgb_nogate_s3/report.json)
- [results/baidu/yq_oftgb_nogate_s3/retained.json](results/baidu/yq_oftgb_nogate_s3/retained.json)
- [results/baidu/yq_oftgb_nogate_s3/round-01.json](results/baidu/yq_oftgb_nogate_s3/round-01.json)
- [results/baidu/yq_oftgb_nogate_s3/round-02.json](results/baidu/yq_oftgb_nogate_s3/round-02.json)
- [results/baidu/yq_oftgb_nogate_s3/round-03.json](results/baidu/yq_oftgb_nogate_s3/round-03.json)
- [results/baidu/yq_oftgb_nogate_s3/round-04.json](results/baidu/yq_oftgb_nogate_s3/round-04.json)
- [results/baidu/yq_oftgb_nogate_s3/round-05.json](results/baidu/yq_oftgb_nogate_s3/round-05.json)
- [results/baidu/yq_oftgb_nogate_s3/round-06.json](results/baidu/yq_oftgb_nogate_s3/round-06.json)
- [results/baidu/yq_oftgb_nogate_s3/tests.txt](results/baidu/yq_oftgb_nogate_s3/tests.txt)
- [results/baidu/yq_oftgb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s3-rep.job-psktw5brhmlb.txt](results/baidu/yq_oftgb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftgb-nogate-s3-rep.job-psktw5brhmlb.txt)
- [results/baidu/yq_oftgb_nogate_s3_rep/test_eval.json](results/baidu/yq_oftgb_nogate_s3_rep/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s3_rep/tests.txt](results/baidu/yq_oftgb_nogate_s3_rep/tests.txt)
- [results/baidu/yq_oftgb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s3-fresh.job-ex0zdqpt6590.txt](results/baidu/yq_oftgb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftgb-nogate-s3-fresh.job-ex0zdqpt6590.txt)
- [results/baidu/yq_oftgb_nogate_s3_fresh/test_eval.json](results/baidu/yq_oftgb_nogate_s3_fresh/test_eval.json)
- [results/baidu/yq_oftgb_nogate_s3_fresh/tests.txt](results/baidu/yq_oftgb_nogate_s3_fresh/tests.txt)

### yq_oftgb_llm_harness_s1

- [results/baidu/yq_oftgb_llm_harness_s1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-resume11062008.job-ws2moqr8twkc.txt](results/baidu/yq_oftgb_llm_harness_s1/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-resume11062008.job-ws2moqr8twkc.txt)
- [results/baidu/yq_oftgb_llm_harness_s1/accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s1/accepted.jsonl)
- [results/baidu/yq_oftgb_llm_harness_s1/backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s1/backend-accounting.json)
- [results/baidu/yq_oftgb_llm_harness_s1/report.json](results/baidu/yq_oftgb_llm_harness_s1/report.json)
- [results/baidu/yq_oftgb_llm_harness_s1/retained.json](results/baidu/yq_oftgb_llm_harness_s1/retained.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-01.json](results/baidu/yq_oftgb_llm_harness_s1/round-01.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-02.json](results/baidu/yq_oftgb_llm_harness_s1/round-02.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-03.json](results/baidu/yq_oftgb_llm_harness_s1/round-03.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-04.json](results/baidu/yq_oftgb_llm_harness_s1/round-04.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-05.json](results/baidu/yq_oftgb_llm_harness_s1/round-05.json)
- [results/baidu/yq_oftgb_llm_harness_s1/round-06.json](results/baidu/yq_oftgb_llm_harness_s1/round-06.json)
- [results/baidu/yq_oftgb_llm_harness_s1/tests.txt](results/baidu/yq_oftgb_llm_harness_s1/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s1_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-rep.job-o6tmk3rvxhh2.txt](results/baidu/yq_oftgb_llm_harness_s1_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-rep.job-o6tmk3rvxhh2.txt)
- [results/baidu/yq_oftgb_llm_harness_s1_rep/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_rep/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s1_rep/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_rep/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s1_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh.job-fm7yr1g2pvwi.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s1-fresh.job-fm7yr1g2pvwi.txt)
- [results/baidu/yq_oftgb_llm_harness_s1_fresh/test_eval.json](results/baidu/yq_oftgb_llm_harness_s1_fresh/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s1_fresh/tests.txt](results/baidu/yq_oftgb_llm_harness_s1_fresh/tests.txt)

### yq_oftgb_llm_harness_s2

- [results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-resume11071339.job-y5zz0zgbmago.txt](results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-resume11071339.job-y5zz0zgbmago.txt)
- [results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2.job-ov65gen3qlvu.txt](results/baidu/yq_oftgb_llm_harness_s2/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2.job-ov65gen3qlvu.txt)
- [results/baidu/yq_oftgb_llm_harness_s2/accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s2/accepted.jsonl)
- [results/baidu/yq_oftgb_llm_harness_s2/backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s2/backend-accounting.json)
- [results/baidu/yq_oftgb_llm_harness_s2/report.json](results/baidu/yq_oftgb_llm_harness_s2/report.json)
- [results/baidu/yq_oftgb_llm_harness_s2/retained.json](results/baidu/yq_oftgb_llm_harness_s2/retained.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-01.json](results/baidu/yq_oftgb_llm_harness_s2/round-01.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-02.json](results/baidu/yq_oftgb_llm_harness_s2/round-02.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-03.json](results/baidu/yq_oftgb_llm_harness_s2/round-03.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-04.json](results/baidu/yq_oftgb_llm_harness_s2/round-04.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-05.json](results/baidu/yq_oftgb_llm_harness_s2/round-05.json)
- [results/baidu/yq_oftgb_llm_harness_s2/round-06.json](results/baidu/yq_oftgb_llm_harness_s2/round-06.json)
- [results/baidu/yq_oftgb_llm_harness_s2/tests.txt](results/baidu/yq_oftgb_llm_harness_s2/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s2_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-rep.job-dkiw8x1wej66.txt](results/baidu/yq_oftgb_llm_harness_s2_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-rep.job-dkiw8x1wej66.txt)
- [results/baidu/yq_oftgb_llm_harness_s2_rep/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_rep/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s2_rep/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_rep/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s2_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh.job-3ac3xqab75k1.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s2-fresh.job-3ac3xqab75k1.txt)
- [results/baidu/yq_oftgb_llm_harness_s2_fresh/test_eval.json](results/baidu/yq_oftgb_llm_harness_s2_fresh/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s2_fresh/tests.txt](results/baidu/yq_oftgb_llm_harness_s2_fresh/tests.txt)

### yq_oftgb_llm_harness_s3

- [results/baidu/yq_oftgb_llm_harness_s3/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-resume11062008.job-fatymmgiuz4d.txt](results/baidu/yq_oftgb_llm_harness_s3/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-resume11062008.job-fatymmgiuz4d.txt)
- [results/baidu/yq_oftgb_llm_harness_s3/accepted.jsonl](results/baidu/yq_oftgb_llm_harness_s3/accepted.jsonl)
- [results/baidu/yq_oftgb_llm_harness_s3/backend-accounting.json](results/baidu/yq_oftgb_llm_harness_s3/backend-accounting.json)
- [results/baidu/yq_oftgb_llm_harness_s3/report.json](results/baidu/yq_oftgb_llm_harness_s3/report.json)
- [results/baidu/yq_oftgb_llm_harness_s3/retained.json](results/baidu/yq_oftgb_llm_harness_s3/retained.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-01.json](results/baidu/yq_oftgb_llm_harness_s3/round-01.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-02.json](results/baidu/yq_oftgb_llm_harness_s3/round-02.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-03.json](results/baidu/yq_oftgb_llm_harness_s3/round-03.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-04.json](results/baidu/yq_oftgb_llm_harness_s3/round-04.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-05.json](results/baidu/yq_oftgb_llm_harness_s3/round-05.json)
- [results/baidu/yq_oftgb_llm_harness_s3/round-06.json](results/baidu/yq_oftgb_llm_harness_s3/round-06.json)
- [results/baidu/yq_oftgb_llm_harness_s3/tests.txt](results/baidu/yq_oftgb_llm_harness_s3/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s3_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-rep.job-4ta75jhcfe5y.txt](results/baidu/yq_oftgb_llm_harness_s3_rep/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-rep.job-4ta75jhcfe5y.txt)
- [results/baidu/yq_oftgb_llm_harness_s3_rep/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_rep/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s3_rep/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_rep/tests.txt)
- [results/baidu/yq_oftgb_llm_harness_s3_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh.job-cl49jmi7e512.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh/SOURCE-zw-rsi-yq-oftgb-llm-harness-s3-fresh.job-cl49jmi7e512.txt)
- [results/baidu/yq_oftgb_llm_harness_s3_fresh/test_eval.json](results/baidu/yq_oftgb_llm_harness_s3_fresh/test_eval.json)
- [results/baidu/yq_oftgb_llm_harness_s3_fresh/tests.txt](results/baidu/yq_oftgb_llm_harness_s3_fresh/tests.txt)

### yq_oftsb_fixed_s1

- [results/baidu/yq_oftsb_fixed_s1/SOURCE-zw-rsi-yq-oftsb-fixed-s1.job-n0gmy4g8pbzk.txt](results/baidu/yq_oftsb_fixed_s1/SOURCE-zw-rsi-yq-oftsb-fixed-s1.job-n0gmy4g8pbzk.txt)
- [results/baidu/yq_oftsb_fixed_s1/accepted.jsonl](results/baidu/yq_oftsb_fixed_s1/accepted.jsonl)
- [results/baidu/yq_oftsb_fixed_s1/backend-accounting.json](results/baidu/yq_oftsb_fixed_s1/backend-accounting.json)
- [results/baidu/yq_oftsb_fixed_s1/report.json](results/baidu/yq_oftsb_fixed_s1/report.json)
- [results/baidu/yq_oftsb_fixed_s1/retained.json](results/baidu/yq_oftsb_fixed_s1/retained.json)
- [results/baidu/yq_oftsb_fixed_s1/round-01.json](results/baidu/yq_oftsb_fixed_s1/round-01.json)
- [results/baidu/yq_oftsb_fixed_s1/round-02.json](results/baidu/yq_oftsb_fixed_s1/round-02.json)
- [results/baidu/yq_oftsb_fixed_s1/round-03.json](results/baidu/yq_oftsb_fixed_s1/round-03.json)
- [results/baidu/yq_oftsb_fixed_s1/round-04.json](results/baidu/yq_oftsb_fixed_s1/round-04.json)
- [results/baidu/yq_oftsb_fixed_s1/round-05.json](results/baidu/yq_oftsb_fixed_s1/round-05.json)
- [results/baidu/yq_oftsb_fixed_s1/round-06.json](results/baidu/yq_oftsb_fixed_s1/round-06.json)
- [results/baidu/yq_oftsb_fixed_s1/tests.txt](results/baidu/yq_oftsb_fixed_s1/tests.txt)
- [results/baidu/yq_oftsb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s1-rep.job-s0cb8h9rgm94.txt](results/baidu/yq_oftsb_fixed_s1_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s1-rep.job-s0cb8h9rgm94.txt)
- [results/baidu/yq_oftsb_fixed_s1_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s1_rep/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s1_rep/tests.txt](results/baidu/yq_oftsb_fixed_s1_rep/tests.txt)
- [results/baidu/yq_oftsb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s1-fresh.job-ngsnv7pop3ev.txt](results/baidu/yq_oftsb_fixed_s1_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s1-fresh.job-ngsnv7pop3ev.txt)
- [results/baidu/yq_oftsb_fixed_s1_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s1_fresh/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s1_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s1_fresh/tests.txt)

### yq_oftsb_fixed_s2

- [results/baidu/yq_oftsb_fixed_s2/SOURCE-zw-rsi-yq-oftsb-fixed-s2.job-6xylapl210xu.txt](results/baidu/yq_oftsb_fixed_s2/SOURCE-zw-rsi-yq-oftsb-fixed-s2.job-6xylapl210xu.txt)
- [results/baidu/yq_oftsb_fixed_s2/accepted.jsonl](results/baidu/yq_oftsb_fixed_s2/accepted.jsonl)
- [results/baidu/yq_oftsb_fixed_s2/backend-accounting.json](results/baidu/yq_oftsb_fixed_s2/backend-accounting.json)
- [results/baidu/yq_oftsb_fixed_s2/report.json](results/baidu/yq_oftsb_fixed_s2/report.json)
- [results/baidu/yq_oftsb_fixed_s2/retained.json](results/baidu/yq_oftsb_fixed_s2/retained.json)
- [results/baidu/yq_oftsb_fixed_s2/round-01.json](results/baidu/yq_oftsb_fixed_s2/round-01.json)
- [results/baidu/yq_oftsb_fixed_s2/round-02.json](results/baidu/yq_oftsb_fixed_s2/round-02.json)
- [results/baidu/yq_oftsb_fixed_s2/round-03.json](results/baidu/yq_oftsb_fixed_s2/round-03.json)
- [results/baidu/yq_oftsb_fixed_s2/round-04.json](results/baidu/yq_oftsb_fixed_s2/round-04.json)
- [results/baidu/yq_oftsb_fixed_s2/round-05.json](results/baidu/yq_oftsb_fixed_s2/round-05.json)
- [results/baidu/yq_oftsb_fixed_s2/round-06.json](results/baidu/yq_oftsb_fixed_s2/round-06.json)
- [results/baidu/yq_oftsb_fixed_s2/tests.txt](results/baidu/yq_oftsb_fixed_s2/tests.txt)
- [results/baidu/yq_oftsb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s2-rep.job-ercl1a63nhev.txt](results/baidu/yq_oftsb_fixed_s2_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s2-rep.job-ercl1a63nhev.txt)
- [results/baidu/yq_oftsb_fixed_s2_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s2_rep/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s2_rep/tests.txt](results/baidu/yq_oftsb_fixed_s2_rep/tests.txt)
- [results/baidu/yq_oftsb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s2-fresh.job-prw1wmfferi2.txt](results/baidu/yq_oftsb_fixed_s2_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s2-fresh.job-prw1wmfferi2.txt)
- [results/baidu/yq_oftsb_fixed_s2_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s2_fresh/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s2_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s2_fresh/tests.txt)

### yq_oftsb_fixed_s3

- [results/baidu/yq_oftsb_fixed_s3/SOURCE-zw-rsi-yq-oftsb-fixed-s3.job-6f5ro54xfi6y.txt](results/baidu/yq_oftsb_fixed_s3/SOURCE-zw-rsi-yq-oftsb-fixed-s3.job-6f5ro54xfi6y.txt)
- [results/baidu/yq_oftsb_fixed_s3/accepted.jsonl](results/baidu/yq_oftsb_fixed_s3/accepted.jsonl)
- [results/baidu/yq_oftsb_fixed_s3/backend-accounting.json](results/baidu/yq_oftsb_fixed_s3/backend-accounting.json)
- [results/baidu/yq_oftsb_fixed_s3/report.json](results/baidu/yq_oftsb_fixed_s3/report.json)
- [results/baidu/yq_oftsb_fixed_s3/retained.json](results/baidu/yq_oftsb_fixed_s3/retained.json)
- [results/baidu/yq_oftsb_fixed_s3/round-01.json](results/baidu/yq_oftsb_fixed_s3/round-01.json)
- [results/baidu/yq_oftsb_fixed_s3/round-02.json](results/baidu/yq_oftsb_fixed_s3/round-02.json)
- [results/baidu/yq_oftsb_fixed_s3/round-03.json](results/baidu/yq_oftsb_fixed_s3/round-03.json)
- [results/baidu/yq_oftsb_fixed_s3/round-04.json](results/baidu/yq_oftsb_fixed_s3/round-04.json)
- [results/baidu/yq_oftsb_fixed_s3/round-05.json](results/baidu/yq_oftsb_fixed_s3/round-05.json)
- [results/baidu/yq_oftsb_fixed_s3/round-06.json](results/baidu/yq_oftsb_fixed_s3/round-06.json)
- [results/baidu/yq_oftsb_fixed_s3/tests.txt](results/baidu/yq_oftsb_fixed_s3/tests.txt)
- [results/baidu/yq_oftsb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s3-rep.job-019axm8141wl.txt](results/baidu/yq_oftsb_fixed_s3_rep/SOURCE-zw-rsi-yq-oftsb-fixed-s3-rep.job-019axm8141wl.txt)
- [results/baidu/yq_oftsb_fixed_s3_rep/test_eval.json](results/baidu/yq_oftsb_fixed_s3_rep/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s3_rep/tests.txt](results/baidu/yq_oftsb_fixed_s3_rep/tests.txt)
- [results/baidu/yq_oftsb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s3-fresh.job-9od6lw5ul4pf.txt](results/baidu/yq_oftsb_fixed_s3_fresh/SOURCE-zw-rsi-yq-oftsb-fixed-s3-fresh.job-9od6lw5ul4pf.txt)
- [results/baidu/yq_oftsb_fixed_s3_fresh/test_eval.json](results/baidu/yq_oftsb_fixed_s3_fresh/test_eval.json)
- [results/baidu/yq_oftsb_fixed_s3_fresh/tests.txt](results/baidu/yq_oftsb_fixed_s3_fresh/tests.txt)

### yq_oftsb_nogate_s1

- [results/baidu/yq_oftsb_nogate_s1/SOURCE-zw-rsi-yq-oftsb-nogate-s1.job-i662avsthrlv.txt](results/baidu/yq_oftsb_nogate_s1/SOURCE-zw-rsi-yq-oftsb-nogate-s1.job-i662avsthrlv.txt)
- [results/baidu/yq_oftsb_nogate_s1/accepted.jsonl](results/baidu/yq_oftsb_nogate_s1/accepted.jsonl)
- [results/baidu/yq_oftsb_nogate_s1/backend-accounting.json](results/baidu/yq_oftsb_nogate_s1/backend-accounting.json)
- [results/baidu/yq_oftsb_nogate_s1/report.json](results/baidu/yq_oftsb_nogate_s1/report.json)
- [results/baidu/yq_oftsb_nogate_s1/retained.json](results/baidu/yq_oftsb_nogate_s1/retained.json)
- [results/baidu/yq_oftsb_nogate_s1/round-01.json](results/baidu/yq_oftsb_nogate_s1/round-01.json)
- [results/baidu/yq_oftsb_nogate_s1/round-02.json](results/baidu/yq_oftsb_nogate_s1/round-02.json)
- [results/baidu/yq_oftsb_nogate_s1/round-03.json](results/baidu/yq_oftsb_nogate_s1/round-03.json)
- [results/baidu/yq_oftsb_nogate_s1/round-04.json](results/baidu/yq_oftsb_nogate_s1/round-04.json)
- [results/baidu/yq_oftsb_nogate_s1/round-05.json](results/baidu/yq_oftsb_nogate_s1/round-05.json)
- [results/baidu/yq_oftsb_nogate_s1/round-06.json](results/baidu/yq_oftsb_nogate_s1/round-06.json)
- [results/baidu/yq_oftsb_nogate_s1/tests.txt](results/baidu/yq_oftsb_nogate_s1/tests.txt)
- [results/baidu/yq_oftsb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s1-rep.job-8nedmrol4bq9.txt](results/baidu/yq_oftsb_nogate_s1_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s1-rep.job-8nedmrol4bq9.txt)
- [results/baidu/yq_oftsb_nogate_s1_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s1_rep/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s1_rep/tests.txt](results/baidu/yq_oftsb_nogate_s1_rep/tests.txt)
- [results/baidu/yq_oftsb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s1-fresh.job-gh9kknis8b71.txt](results/baidu/yq_oftsb_nogate_s1_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s1-fresh.job-gh9kknis8b71.txt)
- [results/baidu/yq_oftsb_nogate_s1_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s1_fresh/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s1_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s1_fresh/tests.txt)

### yq_oftsb_nogate_s2

- [results/baidu/yq_oftsb_nogate_s2/SOURCE-zw-rsi-yq-oftsb-nogate-s2.job-qx6mkagov5s4.txt](results/baidu/yq_oftsb_nogate_s2/SOURCE-zw-rsi-yq-oftsb-nogate-s2.job-qx6mkagov5s4.txt)
- [results/baidu/yq_oftsb_nogate_s2/accepted.jsonl](results/baidu/yq_oftsb_nogate_s2/accepted.jsonl)
- [results/baidu/yq_oftsb_nogate_s2/backend-accounting.json](results/baidu/yq_oftsb_nogate_s2/backend-accounting.json)
- [results/baidu/yq_oftsb_nogate_s2/report.json](results/baidu/yq_oftsb_nogate_s2/report.json)
- [results/baidu/yq_oftsb_nogate_s2/retained.json](results/baidu/yq_oftsb_nogate_s2/retained.json)
- [results/baidu/yq_oftsb_nogate_s2/round-01.json](results/baidu/yq_oftsb_nogate_s2/round-01.json)
- [results/baidu/yq_oftsb_nogate_s2/round-02.json](results/baidu/yq_oftsb_nogate_s2/round-02.json)
- [results/baidu/yq_oftsb_nogate_s2/round-03.json](results/baidu/yq_oftsb_nogate_s2/round-03.json)
- [results/baidu/yq_oftsb_nogate_s2/round-04.json](results/baidu/yq_oftsb_nogate_s2/round-04.json)
- [results/baidu/yq_oftsb_nogate_s2/round-05.json](results/baidu/yq_oftsb_nogate_s2/round-05.json)
- [results/baidu/yq_oftsb_nogate_s2/round-06.json](results/baidu/yq_oftsb_nogate_s2/round-06.json)
- [results/baidu/yq_oftsb_nogate_s2/tests.txt](results/baidu/yq_oftsb_nogate_s2/tests.txt)
- [results/baidu/yq_oftsb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s2-rep.job-x40qjsn7b059.txt](results/baidu/yq_oftsb_nogate_s2_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s2-rep.job-x40qjsn7b059.txt)
- [results/baidu/yq_oftsb_nogate_s2_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s2_rep/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s2_rep/tests.txt](results/baidu/yq_oftsb_nogate_s2_rep/tests.txt)
- [results/baidu/yq_oftsb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s2-fresh.job-qiw3a2ls1t99.txt](results/baidu/yq_oftsb_nogate_s2_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s2-fresh.job-qiw3a2ls1t99.txt)
- [results/baidu/yq_oftsb_nogate_s2_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s2_fresh/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s2_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s2_fresh/tests.txt)

### yq_oftsb_nogate_s3

- [results/baidu/yq_oftsb_nogate_s3/SOURCE-zw-rsi-yq-oftsb-nogate-s3.job-khefn5fhnjji.txt](results/baidu/yq_oftsb_nogate_s3/SOURCE-zw-rsi-yq-oftsb-nogate-s3.job-khefn5fhnjji.txt)
- [results/baidu/yq_oftsb_nogate_s3/accepted.jsonl](results/baidu/yq_oftsb_nogate_s3/accepted.jsonl)
- [results/baidu/yq_oftsb_nogate_s3/backend-accounting.json](results/baidu/yq_oftsb_nogate_s3/backend-accounting.json)
- [results/baidu/yq_oftsb_nogate_s3/report.json](results/baidu/yq_oftsb_nogate_s3/report.json)
- [results/baidu/yq_oftsb_nogate_s3/retained.json](results/baidu/yq_oftsb_nogate_s3/retained.json)
- [results/baidu/yq_oftsb_nogate_s3/round-01.json](results/baidu/yq_oftsb_nogate_s3/round-01.json)
- [results/baidu/yq_oftsb_nogate_s3/round-02.json](results/baidu/yq_oftsb_nogate_s3/round-02.json)
- [results/baidu/yq_oftsb_nogate_s3/round-03.json](results/baidu/yq_oftsb_nogate_s3/round-03.json)
- [results/baidu/yq_oftsb_nogate_s3/round-04.json](results/baidu/yq_oftsb_nogate_s3/round-04.json)
- [results/baidu/yq_oftsb_nogate_s3/round-05.json](results/baidu/yq_oftsb_nogate_s3/round-05.json)
- [results/baidu/yq_oftsb_nogate_s3/round-06.json](results/baidu/yq_oftsb_nogate_s3/round-06.json)
- [results/baidu/yq_oftsb_nogate_s3/tests.txt](results/baidu/yq_oftsb_nogate_s3/tests.txt)
- [results/baidu/yq_oftsb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s3-rep.job-xib2v61ce17j.txt](results/baidu/yq_oftsb_nogate_s3_rep/SOURCE-zw-rsi-yq-oftsb-nogate-s3-rep.job-xib2v61ce17j.txt)
- [results/baidu/yq_oftsb_nogate_s3_rep/test_eval.json](results/baidu/yq_oftsb_nogate_s3_rep/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s3_rep/tests.txt](results/baidu/yq_oftsb_nogate_s3_rep/tests.txt)
- [results/baidu/yq_oftsb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s3-fresh.job-b8gxi9rn5i0a.txt](results/baidu/yq_oftsb_nogate_s3_fresh/SOURCE-zw-rsi-yq-oftsb-nogate-s3-fresh.job-b8gxi9rn5i0a.txt)
- [results/baidu/yq_oftsb_nogate_s3_fresh/test_eval.json](results/baidu/yq_oftsb_nogate_s3_fresh/test_eval.json)
- [results/baidu/yq_oftsb_nogate_s3_fresh/tests.txt](results/baidu/yq_oftsb_nogate_s3_fresh/tests.txt)

### yq_oftsb_meta3_s1

- [results/baidu/yq_oftsb_meta3_s1/SOURCE-zw-rsi-yq-oftsb-meta3-s1.job-tbz439hnaxty.txt](results/baidu/yq_oftsb_meta3_s1/SOURCE-zw-rsi-yq-oftsb-meta3-s1.job-tbz439hnaxty.txt)
- [results/baidu/yq_oftsb_meta3_s1/accepted.jsonl](results/baidu/yq_oftsb_meta3_s1/accepted.jsonl)
- [results/baidu/yq_oftsb_meta3_s1/backend-accounting.json](results/baidu/yq_oftsb_meta3_s1/backend-accounting.json)
- [results/baidu/yq_oftsb_meta3_s1/report.json](results/baidu/yq_oftsb_meta3_s1/report.json)
- [results/baidu/yq_oftsb_meta3_s1/retained.json](results/baidu/yq_oftsb_meta3_s1/retained.json)
- [results/baidu/yq_oftsb_meta3_s1/round-01.json](results/baidu/yq_oftsb_meta3_s1/round-01.json)
- [results/baidu/yq_oftsb_meta3_s1/round-02.json](results/baidu/yq_oftsb_meta3_s1/round-02.json)
- [results/baidu/yq_oftsb_meta3_s1/round-03.json](results/baidu/yq_oftsb_meta3_s1/round-03.json)
- [results/baidu/yq_oftsb_meta3_s1/round-04.json](results/baidu/yq_oftsb_meta3_s1/round-04.json)
- [results/baidu/yq_oftsb_meta3_s1/round-05.json](results/baidu/yq_oftsb_meta3_s1/round-05.json)
- [results/baidu/yq_oftsb_meta3_s1/round-06.json](results/baidu/yq_oftsb_meta3_s1/round-06.json)
- [results/baidu/yq_oftsb_meta3_s1/tests.txt](results/baidu/yq_oftsb_meta3_s1/tests.txt)
- [results/baidu/yq_oftsb_meta3_s1_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s1-rep.job-g5rhylypog4k.txt](results/baidu/yq_oftsb_meta3_s1_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s1-rep.job-g5rhylypog4k.txt)
- [results/baidu/yq_oftsb_meta3_s1_rep/test_eval.json](results/baidu/yq_oftsb_meta3_s1_rep/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s1_rep/tests.txt](results/baidu/yq_oftsb_meta3_s1_rep/tests.txt)
- [results/baidu/yq_oftsb_meta3_s1_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s1-fresh.job-9bf6hsm0wkdg.txt](results/baidu/yq_oftsb_meta3_s1_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s1-fresh.job-9bf6hsm0wkdg.txt)
- [results/baidu/yq_oftsb_meta3_s1_fresh/test_eval.json](results/baidu/yq_oftsb_meta3_s1_fresh/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s1_fresh/tests.txt](results/baidu/yq_oftsb_meta3_s1_fresh/tests.txt)

### yq_oftsb_meta3_s2

- [results/baidu/yq_oftsb_meta3_s2/SOURCE-zw-rsi-yq-oftsb-meta3-s2.job-0xq5cj9d2848.txt](results/baidu/yq_oftsb_meta3_s2/SOURCE-zw-rsi-yq-oftsb-meta3-s2.job-0xq5cj9d2848.txt)
- [results/baidu/yq_oftsb_meta3_s2/accepted.jsonl](results/baidu/yq_oftsb_meta3_s2/accepted.jsonl)
- [results/baidu/yq_oftsb_meta3_s2/backend-accounting.json](results/baidu/yq_oftsb_meta3_s2/backend-accounting.json)
- [results/baidu/yq_oftsb_meta3_s2/report.json](results/baidu/yq_oftsb_meta3_s2/report.json)
- [results/baidu/yq_oftsb_meta3_s2/retained.json](results/baidu/yq_oftsb_meta3_s2/retained.json)
- [results/baidu/yq_oftsb_meta3_s2/round-01.json](results/baidu/yq_oftsb_meta3_s2/round-01.json)
- [results/baidu/yq_oftsb_meta3_s2/round-02.json](results/baidu/yq_oftsb_meta3_s2/round-02.json)
- [results/baidu/yq_oftsb_meta3_s2/round-03.json](results/baidu/yq_oftsb_meta3_s2/round-03.json)
- [results/baidu/yq_oftsb_meta3_s2/round-04.json](results/baidu/yq_oftsb_meta3_s2/round-04.json)
- [results/baidu/yq_oftsb_meta3_s2/round-05.json](results/baidu/yq_oftsb_meta3_s2/round-05.json)
- [results/baidu/yq_oftsb_meta3_s2/round-06.json](results/baidu/yq_oftsb_meta3_s2/round-06.json)
- [results/baidu/yq_oftsb_meta3_s2/tests.txt](results/baidu/yq_oftsb_meta3_s2/tests.txt)
- [results/baidu/yq_oftsb_meta3_s2_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s2-rep.job-17fz2i319uuw.txt](results/baidu/yq_oftsb_meta3_s2_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s2-rep.job-17fz2i319uuw.txt)
- [results/baidu/yq_oftsb_meta3_s2_rep/test_eval.json](results/baidu/yq_oftsb_meta3_s2_rep/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s2_rep/tests.txt](results/baidu/yq_oftsb_meta3_s2_rep/tests.txt)
- [results/baidu/yq_oftsb_meta3_s2_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s2-fresh.job-bu3li0eczrte.txt](results/baidu/yq_oftsb_meta3_s2_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s2-fresh.job-bu3li0eczrte.txt)
- [results/baidu/yq_oftsb_meta3_s2_fresh/test_eval.json](results/baidu/yq_oftsb_meta3_s2_fresh/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s2_fresh/tests.txt](results/baidu/yq_oftsb_meta3_s2_fresh/tests.txt)

### yq_oftsb_meta3_s3

- [results/baidu/yq_oftsb_meta3_s3/SOURCE-zw-rsi-yq-oftsb-meta3-s3.job-9k77usuo38bz.txt](results/baidu/yq_oftsb_meta3_s3/SOURCE-zw-rsi-yq-oftsb-meta3-s3.job-9k77usuo38bz.txt)
- [results/baidu/yq_oftsb_meta3_s3/accepted.jsonl](results/baidu/yq_oftsb_meta3_s3/accepted.jsonl)
- [results/baidu/yq_oftsb_meta3_s3/backend-accounting.json](results/baidu/yq_oftsb_meta3_s3/backend-accounting.json)
- [results/baidu/yq_oftsb_meta3_s3/report.json](results/baidu/yq_oftsb_meta3_s3/report.json)
- [results/baidu/yq_oftsb_meta3_s3/retained.json](results/baidu/yq_oftsb_meta3_s3/retained.json)
- [results/baidu/yq_oftsb_meta3_s3/round-01.json](results/baidu/yq_oftsb_meta3_s3/round-01.json)
- [results/baidu/yq_oftsb_meta3_s3/round-02.json](results/baidu/yq_oftsb_meta3_s3/round-02.json)
- [results/baidu/yq_oftsb_meta3_s3/round-03.json](results/baidu/yq_oftsb_meta3_s3/round-03.json)
- [results/baidu/yq_oftsb_meta3_s3/round-04.json](results/baidu/yq_oftsb_meta3_s3/round-04.json)
- [results/baidu/yq_oftsb_meta3_s3/round-05.json](results/baidu/yq_oftsb_meta3_s3/round-05.json)
- [results/baidu/yq_oftsb_meta3_s3/round-06.json](results/baidu/yq_oftsb_meta3_s3/round-06.json)
- [results/baidu/yq_oftsb_meta3_s3/tests.txt](results/baidu/yq_oftsb_meta3_s3/tests.txt)
- [results/baidu/yq_oftsb_meta3_s3_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s3-rep.job-4d5u9g8q7pbd.txt](results/baidu/yq_oftsb_meta3_s3_rep/SOURCE-zw-rsi-yq-oftsb-meta3-s3-rep.job-4d5u9g8q7pbd.txt)
- [results/baidu/yq_oftsb_meta3_s3_rep/test_eval.json](results/baidu/yq_oftsb_meta3_s3_rep/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s3_rep/tests.txt](results/baidu/yq_oftsb_meta3_s3_rep/tests.txt)
- [results/baidu/yq_oftsb_meta3_s3_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s3-fresh.job-3g82cfaa8ird.txt](results/baidu/yq_oftsb_meta3_s3_fresh/SOURCE-zw-rsi-yq-oftsb-meta3-s3-fresh.job-3g82cfaa8ird.txt)
- [results/baidu/yq_oftsb_meta3_s3_fresh/test_eval.json](results/baidu/yq_oftsb_meta3_s3_fresh/test_eval.json)
- [results/baidu/yq_oftsb_meta3_s3_fresh/tests.txt](results/baidu/yq_oftsb_meta3_s3_fresh/tests.txt)

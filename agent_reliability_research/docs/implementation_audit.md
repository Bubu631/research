# 独立实现审计：首轮有限组reward审计study

审计时间：2026-09-12T16:16:28.754882+00:00。只读检查主实现与首轮预设study；没有修改正在运行或已执行的主源码、NPZ、CSV。本文件区分核心数学正确性与报告/成本比较问题，不将估计器通过测试等同于方法效益。

**结论：已检查的completion、nested-prefix估计与PPO sign split符合声明的数学目标，没有发现当前NPZ真实labels流入测试组query order/survival或开发调参的泄漏。首轮结果存在一个完整查询概率metadata错误，以及必须保留的校准费用负结果。** 后续model-only schedule不是本轮首发实现，需另行核验。

## 1. 核心目标与接口

`split_advantages`返回分块排列的正advantages与负advantages：[A1+,…,AG+,A1−,…,AG−]。它计算真实组均值与population SD，allsame输出0。代码没有把unbiased reward再送入同一非线性normalizer作为提出的方法；该操作仅保留为`ht_then_normalize`对照。

`completion(p)`对每个单位排除自身后构建其他Bernoulli成功总数的分布，再分别条件于自身label为1和0求期望。DP和正负公式正确，包括already-audited p_i=0/1及all-identical endpoint；单次completion为O(G³)，完整离线prefix path需要G次更新，通常O(G⁴)。预测模型正确性只用于效率分析，不用于telescoping的点态无偏。

`sequential_audit`在query开始前接收固定order和survival Q。一个uniform u构造嵌套inclusion：第k步当且仅当u<Q_k时调用oracle_query；更新后按1/Q_k加completion增量。该实现是fixed-survival版本，没有声称实现一般history-adaptive optimal schedule。所有未购买label均未通过callback返回；`completion_path`是明确标注的离线全路径evaluation helper，可以知道真值以精确计算audit随机化期望，但不能被当作在线廉价policy的一部分。

当前所有主调用的order来自stable argsort、确实是permutation；Q由非负指数和positive floor构造，确实非增且不为零。作为公开通用API，仍建议增加order全排列、len(order)=len(Q)=G、有限p/Q/正成本等输入校验。当前有效输入实验没有因此出错；不能把对正确输入的数学保证扩展到不受校验的任意外部输入。

`clipped_surrogate`以min/max ratio系数线性组合估计的A+、A−；`clipped_ratio_derivative`在非kink处的导数indicator正确。随机估计的正/负系数可能越过原取值符号，但实现没有再clamp或normalize，这是保留无偏性所需。这里的导数是固定ratio/参数的oracle clipped surrogate目标；不是最终优化轨迹或真实success objective无偏。

## 2. 实际验证

主仓库5个unit tests全部通过：completion与G2–7全枚举，G4所有真label与停止深度，callback仅访问已购label，sign-split clipped objective和finite-difference ratio导数，非均匀成本/positive survival。

另外，本审计未调用主DP来构造参考值，而从2^G reward configurations、各配置的model probability与条件mask直接积分，核验三个实际保存的evaluation group：

| 保存setting，均group0 | G | 每个prefix completion最大误差 | 9个RR/whole-group方法预算组合的已存metric最大误差 |
|---|---:|---:|---:|
| g4_p0.2_shifted | 4 | 2.22e−16 | 5.33e−15 |
| g8_p0.8_calibrated | 8 | 4.44e−16 | 1.78e−15 |
| g16_p0.05_overconfident | 16 | 7.50e−15 | 9.95e−14 |

参考积分独立构建Φ、每个prefix条件均值、停止质量、inverse-survival和向量/线性投影MSE；与保存结果相符。G4/G8 HT的所有2^G masks也与其保存conditional bias平方吻合。对G16一项预算.75的HT，精确bias平方.2418880483与1024-mask记录.2357651726有有限MC偏差；单个估计可以偏低，而bias-squared统计量在MC重复下有正偏。

整个首轮summary中whole_group_cv、rr_fixed、rr_development的conditional_bias_sq最高约4.87e−31，符合浮点消除误差；这不是统计意义上检测到的非零bias。

## 3. 调度开发与hidden-label边界

测试组order仅依p、已知成本和stable index；RR fixed survival依G、预算、成本及固定exponent。RR development的exponent仅由独立rngdev生成的64个完整calibration groups在候选{0,.5,1,2}中选择，未用rngtest的当前test labels。每个base setting的64个calibration groups被三个预算共享，不是每个预算再新增64组。

测试组所有r由离线simulator生成并保存，用于计算full target、全部可能prefix和exact/MCMC audit期望。这属于环境/评价有oracle而policy无oracle的正常分离；不能把主study称作在线实际购买了这些labels。实际callback接口另有测试，后续真实执行时需要以它或等价接口记录query。

`linear`为生成器随机给出的G×6 score-map，经固定ratio gate后成为2G×6线性算子。当前gradient_mse是这个**人造六维线性更新映射**的误差，不是已训练policy的真实梯度误差；生成器并没有证明这些随机scores可积成某个实际π。可以用来检验sign-split线性性和不同目标范数，但报告应写明proxy/update-map metric。

## 4. 方法和成本对照

### Whole-group CV是正确而强的基线

令所有Q_k=budget。中间停止深度质量均为零，因此该实现恰为：不查时返回F0，查时查询整组并返回F0+(Φtrue−F0)/budget。不存在通过提前用部分真label改善未查询分支的泄漏。每组成本已归一为Σc_i=G，故其期望成本为budget×G，查全概率为budget。该基线使用相同model completion，优于只用zero surrogate的简陋HT基线。

### 校准费不能消失

主study是given-probability controlled analysis。p不是从64个calibration groups训练出来的，所以64G真实labels的费用当前只用于RR development的exponent调参；不能将其标为所有baseline的必要shared model-training成本。

将这一次64G成本摊到本轮256个evaluation groups，相当于每组多.25G。若把同样总query预算交给无需此调参的whole-group CV，其可用q'=budget+.25（本轮最大1）。给定group，其MSE可直接精确换算为

MSE_whole(q') = MSE_whole(q) × (1/q'−1)/(1/q−1)。

实际全135个预算设置核算：

- 同evaluation query budget下，RR development的gradient_mse在79/135设置低于whole-group CV；中位MSE ratio约0.97129。
- **包含一次64G校准费并摊到256组后，RR development在0/135设置低于成本匹配的whole-group CV。**

这是必须保留的负结果，不是实现错误。长部署时可把开发成本摊到更多evaluation groups，但应明示真实/假定部署数量并画amortisation曲线，不能用未发生的无限摊销把本轮结果解释成经济优势。四个exponents共用同一份已购labels，因此不乘4；三个预算共用同一calibration set，因此也不乘3。

后续提出的model-only moment/PAVA方案可免除本项64G真label费，但它是在看到首轮结果后设计，应有独立exploratory protocol。预测/调度CPU依旧应测量并列出。

## 5. 需要修正或限定的报告字段

1. **完整组查询概率metadata有误。** 首轮`ht_then_normalize`与`partial_then_normalize`填0，真实每label独立查询概率为budget，因此完整组概率是budget^G。例如G4、budget.75时为.31640625。此项不影响MSE数值；应保留原run/source快照后修正字段、重算summary并记录修正manifest。
2. **G16 bias-squared为1024-mask估计，不是精确conditional bias。** 若B=||mean d||²、A=mean||d||²，M=1024，则真实||E d||²的无偏估计可由现有列计算为(M B−A)/(M−1)。gradient列同理。修正值可能负，不要截零；可新增明确命名列并保留原值。原MSE sample mean本身无此squared-sample-mean正偏。
3. **prevalence字段不是精确成功率。** z~N(logit(prevalence),1.2²)，p=sigmoid(z)。即使calibrated，E[p]通常不等于参数；overconfident/shifted又变换logit，shifted会反向。应称base-rate/logit-location parameter，并另外报告真实model marginal或观察率。原protocol的success prevalence措辞需解释性更正，保留原记录。
4. **Expected query cost不是端到端speedup。** 成本是人为lognormal并归一的单位，主study还知道所有true labels来精确评价。没有真实oracle timing或训练speedup结果。rr_development还用64个calibration groups；所有方法的completion、候选schedule评估和query_order计算都应单独计时。
5. **该study不是PAVA实证。** 其rr_development在四个幂次中以dev gradient_mse挑选，没有调用理论中的model-moment最优survival。不能把本轮结果放在“PAVA-optimal method”的图例下。
6. **留意protocol覆盖。** 当前输出七个方法（full/proxy/whole/RRfixed/RRdev/HT/partial）；protocol还列出noise-channel correction、unnormalized control、direction error和cost tails等更宽计划。没有实际输出的项目应标未完成或后续阶段，不能称所有预设comparators/metrics已完成。

## 6. 数量与不确定性单位

基础DGP设置为3个G×5个base-rate parameters×3种regime=45；再乘3 budgets得到135方法比较设置。七方法共945个summary rows。每个setting有256个evaluation groups，共45×256=11,520个独立base groups；跨budget和method重复使用，241,920个per-group result rows不是同样数量的独立轨迹组。

64个calibration groups×45=2,880组。由于G不同，实际calibration full-label总数为64×15×(4+8+16)=26,880，每个base setting只计一次。evaluation参考全集共有256×15×(4+8+16)=107,520个label；具体method-query成本按预算另算。

summary的SE是对各setting的256组metric求样本SD/√256，不是训练seed方差、人口推广区间或固定group内的置信区间。G16 HT/partial指标还混入inner-mask Monte Carlo噪声。比较方法应先做同一group上的差，再计算paired SE；不能把两个方法的边际SE独立相加，也不把135相关设置当成135个独立现场试验。

## 7. 状态与文件身份

上面的metadata、MC口径、base-rate命名、总成本视图已即时通知主任务。主任务确认保留校准成本负结果并准备透明修正；本文件记录首轮审计时状态，而非声称这些文件已经改好。后续model-derived方法应附独立实现核验。

| 文件 | 审计时SHA-256 |
|---|---|
| `src/reward_audit.py` | `52957e5692bec6f292673fda3def95f6e9cfb70ec0e3c7267f84298c96c469bb` |
| `experiments/estimation_study.py` | `958b9ee34a2187f3edc4c1e5df40b9b677ded61f63f4a4d8fe3fe48deb440a20` |
| `tests/test_reward_audit.py` | `f13aa2f553641231ecc533dc88cd3ada6a844cbb17d909324681f1e3d2c26399` |
| `results/estimation/manifest.json` | `74f4a8d2dcffd454d5cb4e1d116d1465c1e97ca8c7c29ece30dbf33a20215ecc` |
| `results/estimation/summary.csv` | `c2427a7d6d9643299ade72b66e682d5a25d1669408333f4dea5b3736db91161f` |
| `results/estimation/development_schedules.json` | `0aede3034deb316d63c3d5d5ff8b62af999d76ffeb7f1b00ad82582b38969e63` |

本审计未写入被审计源码/结果。数学原理及独立全枚举检查另见`docs/theory_feasibility.md`、`experiments/verify_theory_feasibility.py`及相应JSON。审计是独立实现/代码检查，不是外部人类同行评审或发表许可。

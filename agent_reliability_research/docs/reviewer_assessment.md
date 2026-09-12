# 独立审稿意见：当前稿件的科学定位与下一阶段

审阅日期：2026-09-12。审阅了当前 `paper/main.tex`、`proofs.tex`、`sign_degree.tex`、model-only 部分、stateful 结果及最新版文献对照。此时真实 Qwen 前向仍在主任务执行中；未把尚未看到的模型结果计入评价。本意见由另一条 AI 审阅流程形成，不是外部人类同行评审。

## 总体判断

目前是一篇有明确问题、专门理论结论和诚实负结果的研究稿，适合作为继续研究的基础。若以“高效软件智能体训练方法”投主流 ML 顶会，当前证据仍偏向拒稿：尚未证明新增顺序机制优于简单整组复核，更没有实际软件训练的端到端收益。增加更多合成设置或同一冻结模型的投影维度，不能解决这个核心缺口。

以“指定有限组目标的查询复杂度及何时无需复杂校正”为中心，定位较可防守。需要保持现在的克制，不能在标题、摘要或投稿信里又升级成一般无偏 RL、新 verifier learning 原理或已证明的训练提速。

## 可以防守的贡献

1. **专门函数的精确查询深度。** 从归一化二元组目标推导偶/奇组大小不同的 Boolean degree，非恒定 score 情形与端点约定明确。当前证明的系数推导、对称性消去、偶阶差分正性及 decision-tree 推论逻辑一致；我未发现明显反例。这不是对所有利用程序语义的算法的计算复杂度下界，而是对声明的 label-oracle 查询模型的下界。
2. **目标层次的清晰区分。** reward、normalized advantage、clipped surrogate 和优化器轨迹被分开，sign-separated 表达避免了把随机系数重新按符号 clip 的实现陷阱。`sign_degree.tex` 对真正用于 clipped 构造的向量给出更直接的度数结论，值得整合；同时要保留特定标量 clipping 权重可消去高阶项的限制。
3. **可核验的有限组实现与失效边界。** 精确 Bernoulli completion、model-moment 计算和 fixed-order PAVA 解有清楚的适用范围。校准费用消除初期收益、misspecification 下方差变大、homogeneous 情况退化为 WG，都属于可信的科学结果。

这些贡献的基础工具已有很强前人工作。degree/decision-tree、randomized telescoping、control variate、HT 和 allocation 都不是新原理。论文价值取决于专门结果是否足够有意义，以及实际使用者是否确实需要保留这个目标。

## 主要拒稿风险，按优先级

**R1：问题重要性与“必须保留 GRPO 目标”的理由不足。** 完整组归一化本来不是 population policy gradient 的无偏估计。审稿人可以合理问：为什么不直接换成固定尺度或线性目标？[Cai v4](https://arxiv.org/html/2510.00915v4) 已避免当前组 z-score，已有 HT appeals；[Noise-corrected GRPO v3](https://arxiv.org/html/2510.18924v3) 已区分 oracle-scale exactness 与 variance plug-in。不能靠批评一个他们已明确排除的 naïve 实现来证明优势。下一阶段必须直接比较这些不同目标的学习效用。

**R2：最强简单基线尚未被超越。** 180 个构造训练 run 中，SC−WG 三个 horizon 的区间全部跨零；SC 的真实本地耗时更高。model-only study 在正确模型下有效，但 shifted regime 的中位 coefficient-MSE ratio 为 2.243，最坏 6.68。若真实数据仍接近 WG 或显著更差，合理结论应是 WG 为实用默认，不能继续把 SC 包装成得到支持的高效方法。

**R3：下界与实践之间仍有距离。** 高阶谱尾在已报告 product distributions 下很小，说明“精确无偏需要深查询”不等于“有用近似需要深查询”。需报告实际任务上误差、方差、尾部更新、任务成功和成本的关系；不能让 exactness 替代 utility。真实 cheap-negative certificates 也会缩小可行 label cube，应让所有基线同享，不把完整 cube 下界直接套到已认证坐标。

**R4：实验外推有限。** 构造环境的初始 greedy workflow 已会做事，改善是随机执行可靠性；horizon 与链规模一起变化。SWE-Gym 是历史异构日志，固定 Qwen 的最后动作窗口和增加的参数子空间是合法诊断，但没有新 agent rollout、完整策略学习或实时测试。上述差异不是通过增加数字规模就能消除的。

**R5：调度优化范数与实际优化几何不同。** PAVA 优化独立工作模型下的 coefficient Euclidean MSE；真实参数梯度的内积结构、长度权重、当前 ratio 和学习率都会改变实际风险。不能把 coefficient 改善直接称作 gradient 或 convergence 改善。应保留针对 WG 的真实梯度、actual update norm、clip-active fraction 和 tail-weight 结果。

**R6：成本与适应性容易在工程中失真。** 需要 fresh audit randomness、实际旧策略概率、无未购买 label 泄漏、显式 predictor/calibration 费用和 CPU/GPU 重叠时间。若每个训练组都额外运行 full-label shadow verifier来算误差，则这部分不能从实际研究成本账本消失。反复使用同一估计优势更新多轮也不自动继承 fixed-θ 定理。

## 最值得做的下一项实验

优先做一个真正的 fresh-rollout 小模型、多轮 Python 代码修正研究，先用真实 public/hidden tests 测瓶颈，再用 3 个探索 seeds、5 个全新确认 seeds 验证。主要比较 SC 与相同 proxy 的 WG，并同时纳入完整验证、只生成较少但完整验证组的省计算流程、以及最新版 PGBC 固定尺度替代。只比较 HT-then-normalize 和 proxy-only 会显得刻意选择弱对照。

最关键的结果不是“估计无偏到 1e−14”，而是：在相同实际资源下能否达到更好的 heldout 程序通过率；或者在相近质量下是否减少真实参考测试 CPU、付费 GPU 占用或端到端时间。应展示全部失败、成本过高和 schedule→WG 的情形。

建议推进门槛是操作性而非正结果门槛：harness可靠、确有非平凡未知标签组、参考测试确实占据足够关键路径、预期节约能覆盖调度。若瓶颈不存在，不给免费 checker 加 sleep，也不通过无意义重复测试制造节约机会。先停止扩大当前基准的提速实验，再根据不同真实任务重新制定协议。

## 文字与提交前补严

- 将 `paper/verifier_related.tex` 的最新版比较整合进 main；目前相关工作段仍是旧的笼统表述。
- 在 affine invariance 段明确前人已识别该现象。HT 反例将 normalization 延伸到实数估计向量时可加一句定义，避免 F 的二元定义与 plug-in 输入域形式上脱节。
- 若整合 sign-degree 结果，清楚分开“完整向量必须有此度数”和“任意具体 clipped 标量都必须如此”；后者未被证明。
- 维持“independent implemented checks”与“外部专家审稿”的区别；缺失的 input/bibliography 文件属于当前组装状态，最终打包时再完整编译和交叉核验。

没有可诚实给出的顶会录用保证。若下一阶段仍未超过 WG，本稿仍可作为精确性、复杂度与实用默认之间的研究，但应围绕这个结论重写动机与贡献，而不是扩大效果用语。

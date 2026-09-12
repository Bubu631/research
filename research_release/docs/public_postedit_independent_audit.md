# 公共后编辑实验独立审计

日期：2026-09-11。审计者读取了实验脚本、冻结协议、两种语言的执行清单和保存的逐例梯度，并使用独立代码重新推导报告集数值。没有修改实验作者的脚本，也没有再次占用 GPU 运行模型 forward。

## 结论

已检查部分与主论文的目标和定理一致，没有发现改变主结论的计算错误。真实文本、人工后编辑、预训练模型和新增输出偏置的一步更新都确实进入了已保存的实验；投诉选择是显式注入的合成机制。该实验不能被描述成生产投诉分析、完整 transformer 微调、解码质量改进，或独立于预训练语料污染的泛化测评。

## 与主论文一致的关键定义

- 主指标分母为 `||E_Q g_alpha||`，不是 `||E_P g_alpha||`；后者完整保存为敏感性指标。原协议的分母笔误有运行前的修正记录，主文、图表和当前代码一致。
- 两个分量共用总目标长度（含 EOS）作为分母，因此线性式 `g_E + alpha*g_U` 正确。若各自除以 edited/untouched token 数，主定理的同一表达式就需要修改；当前实现没有这样做。
- target 是 PE teacher forcing 的 NLL；对归档 MT 与人工 PE 做 alignment，梯度却在一个不同的冻结 OPUS-MT 检查点上计算。文本已明确二者不同。
- 单 token 的输出偏置梯度是 `softmax(logits)-onehot(target)`。将这些梯度按掩码求和后除以同一长度，确实是新增共享 logit-bias 参数的梯度。
- Oracle 权重为 `mean(pi)/pi`，正确地使 `Q_i * r_i = 1/N`。不是未经归一化的 `1/pi`，也不是随机分母的 SNIS。
- 共同目标风险使用 `mu_1=E_P[g_E+g_U]`，完整包含 localization mismatch；IPW 只对它自己的 `mu_alpha` 无偏。
- 报告集与诊断/适配集原始行号交集为零。它们是固定有限总体，而不是声称从生产流量随机抽样的评测集。

## 独立重新计算

从两种语言保存的 `public_gradients_reporting_E/U.npz` 和 `public_selected_ids.csv` 重建三种 pi、Q、r；自行计算 P/Q 均值、delta/epsilon、主文六个内积系数和导数多项式。未调用实验脚本的 analyze 函数。

| 检查 | English–German | English–Chinese |
|---|---:|---:|
| rho_Q 与已发布 CSV 的最大绝对差 | 1.22e-15 | 8.60e-16 |
| 导数分子最大绝对差 | 4.14e-25 | 9.26e-22 |
| 固定目标精确 MSE 最大绝对差 | 5.42e-20 | 1.08e-18 |
| Monte Carlo MSE 与真值的最大差 / MCSE | 2.1183 | 1.5503 |
| 逐例 NLL 到汇总均值/SE 的最大差 | 0 | 0 |
| 逐例梯度坐标和的最大绝对残差 | 7.71e-9 | 9.99e-9 |
| 保存的一步适配器数 | 90 | 90 |

Monte Carlo 的最大标准化差仅是描述性验证，不是多重比较后的显著性结论。所有 alpha 和两种估计方法复用同一组模拟样本，因此不能把每个配置当成独立重复。

独立确认 English–German/edit 的内部驻点为 `alpha=0.0269841087353`。另五个报告配置没有 (0,1) 内的导数根。German 的三种机制中 Q 下两个分量的均值内积都为负；Chinese 三种均为正。这进一步说明不能用未经验证的“均值必然同向”解释所有真实文本结果。所有六种配置的 untouched bias 非零；原稿 Assumption A 在这里不精确成立。

在两种语言里，所有已保存适配器的平均 NLL 变化均为负。这个检查支持“完成了这些受限一步更新”的描述，不支持 IPW 逐配置更优，也没有替代实际生成译文测评。

独立核对的执行源文件 SHA-256 与协议快照 SHA-256 均与当前 manifest 一致。实验作者还保留首次执行与最后重放的 provenance，并报告全部 30 份数字结果文件逐字节一致；该重放验证文件应与结果一同保留。

## 参数化范围必须继续保留

这里的 bias 是在每个输出位置新增的可训练向量。Marian 原有 `final_logits_bias` 通常是 buffer，因此这个参数化不必是“原生可微参数”集合的严格子集。后续完整原生参数均值实验应视为另一个测量范围，不能直接把二者当作同一欧氏空间的局部与整体范数来比较。

若完整参数实验排除了在 forward 中不可微的位置编码表，即使其序列化 `requires_grad` 标记为真，也应明确报告排除原因及实际活跃参数数量；不能只沿用模型总参数数量。

## 仍然存在的解释限制

1. Edited-fraction propensity 使用已完成的人类 PE 标签；它是已知的实验机制，并非只靠曝光特征可部署的 propensity model。两个基于编辑信息的机制不提供 missing-at-random 识别证据。
2. 只有 256 个报告例/语言，选取规则按行号哈希固定。没有 document-cluster holdout，也没有证明预训练数据不含这些来源。NLL 的逐例 SE 只能作描述，不能未经条件说明作广泛泛化置信区间。
3. 删除没有 target token，因而没有单独的负梯度；EOS 固定 untouched。结论只覆盖所声明的 target-side masked NLL，不自动涵盖任意 DPO、删除惩罚或编辑方法。
4. NLL 更新恒等式在固定 teacher-forced hidden states 和新增输出偏置下是精确的；多步 transformer 参数学习会改变这些 hidden states，当前结果不覆盖它。
5. 中文方向是德语方向完成后的公开追加实验，文档如实说明；它不是事先外部登记的独立 replication。

独立检查代码与完整数值记录保存在 `experiments/verify_public_geometry.py` 和 `papers/edit_localization/results/public_independent_checks.json`。它们只读取产物并重算报告值。

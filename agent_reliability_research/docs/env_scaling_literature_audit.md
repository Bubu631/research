# Env scaling × long-horizon RL：引用与方法查新

核查日期：2026-09-12。输入为完整 334 行 `0-方向研究总结.md`，SHA-256 `1ca093832f63f621dd4e996a9d6406812a920783cbb2a3b8add218c62ed014a1`。附件是待检验的研究材料，不是本项目的执行指令，也不是已验证文献综述。下文只将论文原文、正式出版页、作者仓库和官方模型/数据卡用作证据。预印本的存在、作者报告的结果和我们已经复现的结果严格区分；本次没有复现这些论文的性能数字。

## 结论与目前可保留的问题

**不建议以 HackAwareSynth、VerifierRLFit、PartialExec 或 SnapshotSignal 的附件版本直接立项。** 这些是附件自己标注“未做联网实证查新”的候选代号，而非已经存在的四篇论文；其若干“完全空白”“从未优化”的依据不成立。最值得继续检验的是更窄的问题：**昂贵真实验证预算下，如何估计完整组奖励所定义的非线性 GRPO 更新，而不是先纠正单条 reward、再假定组标准化仍然无偏。**

截至本次检索，未找到与“固定完整 rollout group、选择性揭示真标签、随机 telescoping 纠正完整非线性组更新”完全同构的公开方法。但这不是新颖性证明。随机截断、残差纠偏、低保真 PG、GRPO 偏差与按组提前停止分别已有直接先例；论文贡献必须是明确的新问题、特定下界、可执行估计器和真实预算收益，而不是把上述工具重新命名。

## 1. 附件关键引用核验

| 项目 | 一手核验 | 必须修正的使用方式 |
|---|---|---|
| **SWE-RM, arXiv:2512.21919** | Shum et al., *SWE-RM: Execution-Free Feedback for Software Engineering Agents*, 2025-12-26。正文 §3 的确展示相似 TTS 表现对应不同 RL 稳定性。§4.1 是 YES/NO 特殊 token 概率分类。 | 该版本明确提出 AUC 与 calibration/ECE 补充 TTS，并有理论附录；不能据此写“没有任何事前属性”。附件的 0.77、61.4→70.8 和“必须带 CoT，否则短无效解导致崩溃”未在此版本定位，**不应归因给本篇**。其主要模型是 30B 总参数、3B 激活，不是本地可轻易训练的小模型。 [原文](https://arxiv.org/html/2512.21919v1) |
| **RECEIPT, arXiv:2607.18575** | Lyu, Shieh, Hou, Wang, Sen, Wagner，2026-07-20。用于 white-box agentic XSS discovery 的约束重放、环境隔离、角色分离和 verdict binding。 | 属特定安全任务的 verifier 设计，不能推广成所有环境/所有对抗策略下“形式化不可攻击”。其报告的零误报是该实验和检测定义下的观测，不是全域保证。 [原文](https://arxiv.org/html/2607.18575v1) |
| **Hack-Verifiable Environments, arXiv:2605.20744** | Roth, Samanta, Halevy, Levine, Efroni，2026-05-20。把可检测的作弊机会嵌入 TextArena，以便自动测量。 | “可验证是否作弊”不等于“验证器永远正确”，也不是“消除作弊”的训练算法。可以做已知代理/真实回报的机制实验，但需保留环境设计限制。 [原文/代码入口](https://arxiv.org/abs/2605.20744) |
| **EvilGenie, arXiv:2511.21654** | Gabor, Lynch, Rosenfeld，2025；当前 v2 为 2026-05-17。使用 LiveCodeBench 问题及三类作弊检测。 | 关于留出测试增益小、LLM judge 在无歧义情形有效，是特定实验结论，不能宣布 judge 或留出测试普遍可靠/无用。 [原文](https://arxiv.org/abs/2511.21654) |
| **“平均17.7%可攻破”** | 可追溯到 Bercovich et al., *Terminal Wrench*, arXiv:2604.17596，表1：五个来源的 **有重叠** 合计 348/1,968 =17.7%；去重范围为1,860任务、331确认环境。 | 不是所有合成流水线的总体攻击率；受来源选择、攻击模型、提示与搜索预算限制。不能放进新方法的前提当作总体参数。 [表1与方法](https://arxiv.org/html/2604.17596v1) |
| **HackAwareSynth / VerifierRLFit / PartialExec / SnapshotSignal** | 附件 §6.2 的 V01/V02/V09/V11 内部候选。 | 候选名检索没有产生足以建立其为独立发表工作的证据。其新颖性应与下节的真实方法逐项比较，不能把附件候选名写入相关工作作为已发表论文。 |

其他逻辑问题：终态二元奖励并不自动使损失“无界”；有限时域、有界奖励下回报有界，训练失稳或优化放大与数学无界不是同一命题。“可执行化已基本解决”也与附件自己引用的低 F2P 成功率冲突。构建准确率、测试通过率、reward 对意图的一致性不能混为同一指标。

## 2. 已有方法，不能换名字作为创新

| 既有工作 | 与候选的重合 | 仍需区分 |
|---|---|---|
| Liu et al., **A Multi-Fidelity Control Variate Approach for Policy Gradient Estimation**, TMLR 02/2026 | 少量高保真轨迹与大量低保真控制变量，构造无偏低方差 on-policy PG；包括奖励错设。 | 这已覆盖“cheap proxy + true-gradient correction”的总思路。当前候选若成立，区别应在**同一已生成组的缺失真标签、非线性标准化/裁剪、查询预算与顺序**，不是低/高保真两域本身。 [正式全文](https://openreview.net/pdf?id=zAo0L7Dcqt) / [作者项目](https://xinjie-liu.github.io/mfpg-rl/) |
| Zrnic & Candès, **Active Statistical Inference**, ICML 2024 | 根据预测残差的不确定性主动取真标签，AIPW/残差纠偏；覆盖序贯更新，不是只会随机抽样。 | 把 reward 换成 score-weighted reward 并写出 HT 恒等式，本身不足够新。需要证明学习中变化的、非线性的估计对象的额外性质。 [出版页](https://proceedings.mlr.press/v235/zrnic24a.html) |
| Li, Zrnic & Candès, **Robust Sampling for Active Statistical Inference**, NeurIPS 2025 | 不可靠的不确定度会使主动采样比均匀采样更差；已有稳健混合策略。 | “加均匀探索下限”不是新稳健性发现。应实证比较校准/错设/漂移条件，并避免误称无条件优于均匀。 [出版页](https://papers.neurips.cc/paper_files/paper/2025/hash/6389470564214983604d1ac81631c2c5-Abstract-Conference.html) |
| Cai et al., **Reinforcement Learning with Verifiable yet Noisy Rewards under Imperfect Verifiers**, arXiv:2510.00915 | 不对称噪声通道的 backward/forward correction，恢复 clean PG 或方向；含 appeal/recheck 机制，并实现到 GRPO 管线。 | 固定错误率假设与任意 instance-dependent error 不同；但“修正奖励使梯度可靠”已有直接工作。不能未经分析把其 clean-PG 证明扩展到任意归一化实现。 [原文](https://arxiv.org/html/2510.00915v1) |
| Egashira et al., **Delay, Plateau, or Collapse**, arXiv:2605.02909 | 系统性 false positive 的模式而非总体错误率决定 plateau/collapse；已有真实小模型算术训练研究。 | “相同accuracy却不同RL结果”不是可独占的新现象。新的审计方法需在这种失败模式下产生可重复的纠正收益。 [原文](https://arxiv.org/html/2605.02909v1) |
| Rothermel & Harrold, **A Safe, Efficient Regression Test Selection Technique**, ACM TOSEM 1997 | 根据程序修改和测试覆盖选取可保留故障检出的测试子集。 | 直接否定 PartialExec 的“测试子集选择从未被优化”。安全性需要具体条件，覆盖启发式不是语义完备证明。 [原文](https://www.cs.purdue.edu/homes/xyzhang/spring07/Papers/p173-rothermel.pdf) |
| Spieker et al., **Reinforcement Learning for Automatic Test Case Prioritization and Selection in Continuous Integration**, ISSTA 2017 | RETECS 用历史失败、持续时间和上次执行信息，在时间限制下学习测试排序。 | 用 RL 选择测试也不是新方法。区别可能是**被训练代码策略的 reward 估计偏差与算力联合目标**，不只是提高 fault detection。 [作者全文](https://hspieker.de/files/Spieker_et_al._-_2017_-_Reinforcement_Learning_for_Automatic_Test_Case_Prioritization_and_Selection_in_Continuous_Integration.pdf) |
| **Backplay** (2018) 与 **OmegaPRM** (2024) | 前者从示范中间状态启动学习；后者通过续写/搜索定位过程错误，生成过程监督。 | 快照、回滚、从中间点续写以形成训练信号早有先例；SnapshotSignal 的“快照只用于加速”不成立。 [Backplay](https://arxiv.org/abs/1807.06919) / [OmegaPRM](https://arxiv.org/abs/2406.06592) |
| Meng, **Policy-Conditioned Counterfactual Credit for Verifiable Reinforcement Learning of Long-Horizon Language Agents**, arXiv:2606.05263 | 摘要已包含冻结参考策略续写、干预有效性门控、selection-adjusted doubly robust contribution。 | **只核实存在与摘要；未审计其实现、理论与实证主张。** 仍是不能忽略的重合候选文献，不能把“反事实+DR+long horizon”整体宣称首次。 [预印本](https://arxiv.org/abs/2606.05263) |

“攻击者发现反例→修补→再验证”的循环也与 counterexample-guided synthesis/adversarial training 的既有逻辑相同。把角色放进环境合成流水线可能有工程或实证价值，但必须提出更具体的技术对象与可比较保证；有限攻击搜索失败不能推出不可攻击。

## 3. 新窄问题：有预算的完整组更新估计

建议把目标锁定为：给定生成完成的组、冻结的 policy checkpoint、明确的零方差约定、token/trajectory 长度加权方式及裁剪规则，完整真奖励向量 `R` 定义确定性更新 `U_theta(R)`。目标是估计该**完整数据更新**，不是声称 GRPO 本来就等于真实期望回报的无偏梯度。

单条残差纠偏 `m_i + I_i(R_i-m_i)/p_i` 的条件期望正确，不能推出将该随机向量代入组均值/标准差后的结果也正确。将真实标签依次揭示形成 `U_0,...,U_G`，并用有正生存概率的随机 telescoping 估计 `U_G`，是合理的候选构造，但其母方法已有下列直接来源。

| 近邻 | 本次已核实内容 | 当前问题可分开的地方 |
|---|---|---|
| Beatson & Adams, **Efficient Optimization of Loops and Limits with Randomized Telescoping Sums**, ICML 2019 | 已有随机 telescoping 梯度、有限/无限近似序列和在线成本/方差调参。 | 新稿必须引用它；有限组标签揭示、Boolean degree 查询障碍与组归一化特定的估计结构，才可能是新的贡献。 [出版页](https://proceedings.mlr.press/v97/beatson19a.html) |
| **SARA: Early Verdicts, Better Budgets**, arXiv:2607.26253 | §2–3 对组内早期结果使用 Beta 后验和停止规则，放弃推测饱和组，将生成预算移至新 prompt。正文检索未见将其调整回预先固定完整组更新的无偏恒等式。 | 是**rollout 生成/组选择**，并非对已经生成组的未知真实 labels 纠偏。不能因此忽略它作为预算基线。 [正文](https://arxiv.org/html/2607.26253v1) |
| **Discounted Beta–Bernoulli Reward Estimation**, arXiv:2603.18444 | 使用历史奖励统计改善 GRPO 归一化的稳定性；论文明确承认估计器有偏、以方差收益换取 MSE 降低。 | 不能用“无偏一定更好”的叙事；需与这一类有偏低方差方法比较真实学习效果。 [正文](https://arxiv.org/html/2603.18444v1) |
| Yang et al., **Your Group-Relative Advantage Is Biased**, arXiv:2601.08521 | 相对期望 advantage 的组估计偏差与难度加权。 | 与“缺失奖励导致对固定完整组更新的额外偏差”是两种估计对象；标题与定理应明确区分。 [原文](https://arxiv.org/abs/2601.08521) |
| **NAT: Not All Tokens Are Needed**, arXiv:2603.06619 | 用 HT 重加权子采样 token 的 PG，减少反传但不改变 reward 计算。 | 对比资源轴：这里省 token backward；候选省昂贵 reward verification，两者不可把开销混算。 [原文](https://arxiv.org/abs/2603.06619) |

重点检索过的词包括 `GRPO selective verification`、`partial reward evaluation`、`GRPO reward subsample`、`GRPO verification cost`、`randomized telescoping gradient`、`GRPO audit telescoping`、`prediction-powered policy gradient`、`multi-fidelity policy gradient`。搜索的未命中只能支持“尚未定位”，不能支持“世界首次”。检索到的二手页面仅用于找一手入口，没有用其摘要推导方法保证。

### 必须在算法和证明中处理的边界

1. **估计对象的非线性不能留到后面。** 无偏 advantage 再经过 `min/clip` 仍可能有偏。可对完整 clipped surrogate/gradient 做 telescoping，或按正负 advantage 拆分后正确组合；需独立验证代码与定理一致。
2. **条件化时点。** 明确冻结 checkpoint、rollout group、代理预测与审计前可见信息。复用一次审计随机性进行多轮 optimizer 更新，不自动获得每步条件无偏，更不使最终训练轨迹无偏。
3. **预算不是一种。** 期望预算允许少数完整审计；硬上限少于必要查询次数是不同约束。不能把低期望成本写成从不超过该成本。报告尾部成本与大权重。
4. **审计概率要可记录且严格正。** 自适应顺序和继续概率只能使用此前可见信息。按已知未审计真值选择概率是 oracle ablation；用事后估计错误率替代设计概率不能直接继承 HT 保证。
5. **真值层级。** 完整测试通过仍是任务正确性的 operational target，并非自动等于用户意图。部分测试遇到一次可靠失败可确定 AND 标签为0；“截至停止尚未失败”不能当作完整通过。
6. **无偏不是性能保证。** 稀疏全审计的高方差可能抵消成本收益；必须与均匀完整组审计、朴素 reward-HT、proxy-only、oracle、固定子集及较简单 RLOO/无标准差更新比较。

## 4. 可执行且足以决定是否继续的评估

推荐先做以下三层，并明确区分它们的证据。

- **精确机制层（CPU）：** 小组 `G=2,4,8` 的全部二元标签枚举，独立重算真组更新与所有审计路径；在零方差、单失败、单成功、裁剪两侧和极小继续概率上检验期望/方差。查询下界只对清楚声明的信息模型成立。不能用蒙特卡洛接近替代有限情形可精确验证的恒等式。
- **真实轨迹、冻结模型层：** 公共多轮代码生成/修复记录，逐 task 留出，再用本地小 checkpoint 重新计算 assistant-token log-prob 与梯度。记录来源行为模型不同于当前 checkpoint；这是固定经验组的梯度诊断，**不是当前模型的 on-policy RL 性能**。先比较同一完整组下误差、方向、方差、审计数与实际执行时间。
- **实际训练层（资源确认后）：** 1.5B/3B/7B 中可承担的至少两个规模，公开训练任务与全新 task-heldout 评价，多 seed；在 policy 主动向 proxy 错误处移动时测试保持真测试成功率的能力。将多轮交互次数与文本 token 长度分开；单轮生成长答案不能作为 long-horizon agent 的替代证据。

预算曲线的主横轴应包括真实验证 CPU秒/容器或API成本，另列 rollout GPU秒、训练GPU秒和总wall-clock；从缓存标签模拟查询只能报告 label-budget replay，不能标成实际训练加速。开发集先测成本结构：若验证在总成本中很小，则应否定“显著提速”的立项理由。不得人为 sleep 制造主结果。

先冻结基础/漂移/系统性false-positive/代理校准失效/测试时间异质等情景；保留方法反转。改进门槛建议是：在预定预算范围，相比**同成本均匀完整组审计**稳定改善真实测试回报或固定组更新 MSE，而且至少一个实际训练规模成立。若仅胜过有明显偏差的 proxy-only，却不能胜过均匀审计，就不足以支撑强方法论文。

## 5. 模型与公开数据的初步资源核查

- 官方 **Qwen2.5-Coder-1.5B-Instruct**：1.54B 参数、Apache-2.0；可作为本地固定 checkpoint 的候选。加载、梯度和最大长度是否适合16GB统一内存仍需实测，不能从参数数目保证可训练。7B及长上下文RL待外部GPU资源确认。[官方卡](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct)
- **EvalPlus**：官方提供 HumanEval+/MBPP+、基础/增强测试及快速 mini；仓库 Apache-2.0。其原始测试与增强测试天然形成便宜/更强验证层级，适合 CPU 诊断，但旧公开测试及参考解修订说明污染/真值版本需记录。测试集不应转成训练集后再声称该 benchmark 泛化。[官方仓库](https://github.com/evalplus/evalplus)
- **APPS**：作者仓库含训练/评估代码，数据下载约1.3GB，代码MIT。可按官方训练/测试分区做代码生成和多轮修复，执行侧不需逐仓库Docker；仍要隔离不受信任的生成代码、记录timeout与依赖。数据收录的原题来源权限不能仅由仓库MIT推导。[作者仓库](https://github.com/hendrycks/apps)
- **SWE-Gym OpenHands Verifier Trajectories**：公开Hub约119MB、约5.27k记录；另有6.06k sampled trajectories。比只含491成功轨迹的SFT集更适合错误/正确并存的审计诊断。它们的历史执行奖励可用于回放，但真实重新执行仓库测试仍有环境成本，不能暗示已摆脱SWE依赖。[官方数据入口](https://huggingface.co/SWE-Gym)
- **Cobalt/TACO** 是目前更贴切的多轮代码候选：作者提供processed TACO、public tests交互、hidden tests重新评分、轨迹处理及GRPO代码。其离线轨迹链接指向SharePoint，本次网页取回返回404，因此**暂不能声称已取得该轨迹档案**；下一步需查明可读数据字段/镜像或从其公开任务重新采样。[作者仓库](https://github.com/OSU-NLP-Group/cobalt)

这些都是待实测的数据/代码入口，不是本项目已执行的训练或已验证吞吐。更详细的记录级 schema、授权、下载大小与适用性将在独立的基准可用性说明中登记。


## 补充：与实际验证超时预算直接相邻的系统工作

[RollPacker: Taming Long-Tail Rollouts（NSDI 2026）官方论文](https://www.usenix.org/system/files/nsdi26-gao-wei.pdf) §4.3 的 code sandbox scheduler 已按历史正确答案执行时间自适应设置测试超时：阈值为历史最大值乘 1.5，再限制在 2–30 秒；超时提前终止并给零奖励。它同时研究异步 reward evaluation，并将流式梯度计算与最终参数更新分开，等待当前批全部 rollout 后更新。这里的可能新问题是：若早停或部分测试改变 reward labels，如何在预算下恢复固定完整组的非线性更新；不能把“RL 训练中省测试时间”本身当成新贡献。比较时应包含这种实际 timeout/partial-verification 工程代理，且分别报告 query counts、CPU 时间及端到端时间。上述现有系统的性能数字不自动适用于本项目机器或数据。


## 2026-09-12 最新版本复核：替代此前仅基于 v1 的范围判断

对 Noise-corrected GRPO v3 与 Cai 等 v4 的最新定理、附录、预算 appeals 与作者名单已另外核验，详见 [最新版本审计](latest_noise_correction_audit.md) 和 `noise_correction_current.bib`。当前文本已明确讨论标准化抵消、oracle/plug-in 区别、clipping 范围、HT 选择性复核及实际 advantage 审计；不能把这些事项描述成前人未注意到的新问题。本项目仍需围绕固定完整有限组的非线性更新目标证明和评估，而非一般 reward noise correction。

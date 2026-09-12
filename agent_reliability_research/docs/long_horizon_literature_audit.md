# Long-horizon × environment scaling：独立查新与理论边界审计

审计日期：2026-09-12。完整阅读输入文件 `/Users/shengweizhang/Downloads/0-方向研究总结(1).md`（386 行）；其中的任务安排、优先级、空白格和实验数字均作为待核验研究材料，不作为用户指令或事实。只用论文原文、作者网站、官方出版社和作者提交的预印本支持下述文献判断。原文的全部数十条书目没有逐一复现；本报告重点核验对选题有决定意义的近邻。未运行任何被引论文的作者实现，所述公开结果不是本项目结果。

## 1. 选题判断

附件的大方向成立，但目前不能直接把“快照分支 + 稠密信用 + 验证门控 + 记忆/依赖结构”写成新的总框架。相当接近的论文已公开，而且不只出现在 2026 年：中间状态 Monte Carlo 值估计、可学习记忆动作、跨会话依赖评测都有更早先例。现有工作的摘要不能代替对其定理假设、成本口径和开放实现的核对。

最值得推进的是一个明确的学习目标和一个可测量的资源约束。结合本项目当前 `study_protocol.md`，**固定轨迹组、少量昂贵终态验证、保持完整标签下的有限组更新目标**，比泛称“更好的长程因果信用”更容易形成可证和可反驳的贡献。它仍须面对既有随机截断估计、控制变量、主动统计推断与 noisy-GRPO 的先例；能否形成新贡献取决于对组内非线性归一化、查询限制和实际成本的具体结果，而不是这些模块的拼装。

第二个可独立验证的问题是：**局部分支估计和不完整回滚何时破坏早期依赖动作的学习信号？** 这适合做机制实验或备选论文，必须与完整的行为策略梯度、有限组 surrogate、参考策略反事实效应三个不同目标分开。

## 2. 已核验的近邻文献

日期优先记 arXiv 首次提交日，不用搜索引擎的抓取日期冒充发表日期。除特别标明外，2026 年条目在本次核查中只能确认为公开预印本；不自动称为顶会论文。F 表示已读有关方法/理论正文，A 表示已核验官方摘要与书目，不能据此声称所有实验细节都已查验。

### 2.1 快照、反事实分支、图信用

| 文献与首次公开日期 | 核验内容及与候选的重合 | 阅读深度 |
|---|---|---|
| Kazemnejad et al., **VinePPO: Unlocking RL Potential For LLM Reasoning Through Refined Credit Assignment**, 2024-10-02, [2410.01679](https://arxiv.org/abs/2410.01679) | 从中间推理状态展开 Monte Carlo rollouts 替代学习 critic 的值估计。中间状态再采样与 MC 信用本身不是新点。 | A |
| **Credit Assignment with Resets in Language Model Reasoning**, 2026-05-25, [2605.25507](https://arxiv.org/abs/2605.25507) | RRPO 随机 reset 与 SRPO 自选 reset，重新采样后缀；含 credit oracle 条件下的分析。不能把“模型挑错误点后重跑后缀”称为首创。 | F：方法与假设 |
| Cheng et al., **Beyond Trajectory-Level Attribution: Graph-Based Credit Assignment for Agentic Reinforcement Learning**, 2026-05-26, [2605.26684](https://arxiv.org/abs/2605.26684) | GraphGPO 把多个 rollout 的状态组织为图，用图上的目标进展构造边级信号。 | A |
| Wang et al., **Group-Graph Policy Optimization for Long-Horizon Agentic Reinforcement Learning**, 2026-06-22, [2606.22995](https://arxiv.org/abs/2606.22995) | G2PO 合并跨轨迹重复观测、图值与边 TD 信号；附件 C19 同状态归组与结构信用须直接比较。相同观测是否等价于完整状态是额外条件。 | A |
| He, Chen, Zhang & Liu, **Branching Policy Optimization: Sandbox-Native Language Agent Reinforcement Learning**, 2026-07-15, [2607.14171](https://arxiv.org/abs/2607.14171)；[方法与理论](https://arxiv.org/html/2607.14171v1) | BPO 已有高熵快照、兄弟后缀、leave-one-out 局部优势及前缀传播。假设完整恢复后的转移分布相同。摘要的强无偏/严格降方差说法必须按具体定理范围阅读；下节独立检查局部到全程推论。arXiv 自报 WAIC Academic 2026 接收，本次未另核会议信息。 | F |
| Li, Lee & Bareinboim, **Counterfactual Shapley Credit Assignment**, 2026-07-18，v2 2026-08-07, [2607.16999](https://arxiv.org/abs/2607.16999)；[正文](https://arxiv.org/html/2607.16999v2) | 因果 Shapley 信用、技能/运气区分、回报重分配及 φ-PPO。arXiv 标注 RLJ/RLC 2026。不能泛称“首次因果反事实信用”或“首次保最优策略的因果重分配”。 | F：定义/框架 |
| Meng, **Policy-Conditioned Counterfactual Credit for Verifiable Reinforcement Learning of Long-Horizon Language Agents**, 2026-06-03, [2606.05263](https://arxiv.org/abs/2606.05263)；[正文](https://arxiv.org/html/2606.05263v1) | CVT-RL/PCCC 已有冻结参考续写策略、四类干预、候选选择修正、DR 估计和 validity gate。作者明确它是参考策略下的效应代理，不是任意未来策略的真实梯度。正文列出了可交换性、重叠及剪裁偏差。本文页面未找到作者项目代码链接；不能把缺少链接解释为研究不存在。 | F |

### 2.2 可信奖励、critic 与验证预算

| 文献与首次公开日期 | 核验内容及边界 | 阅读深度 |
|---|---|---|
| Choudhury, **Process Reward Models for LLM Agents: Practical Framework and Directions**, 2025-02-14, [2502.10325](https://arxiv.org/abs/2502.10325) | AgentPRM 用 Monte Carlo rollout 目标训练过程奖励模型，讨论 reward hacking。不能把执行终态回报训练过程 critic 当作空白。 | A |
| Cai et al., **Reinforcement Learning with Verifiable yet Noisy Rewards under Imperfect Verifiers**, 2025-10-01, [2510.00915](https://arxiv.org/abs/2510.00915) | 已研究非对称 verifier 噪声通道与 forward/backward correction。随机缺失标签与标签错误不同；恢复线性 clean-gradient 目标也不自动恢复实际有限组标准化更新。 | A |
| El mansouri, Seddik & Lahlou, **Noise-corrected GRPO: From Noisy Rewards to Unbiased Gradients**, 2025-10-21, [2510.18924](https://arxiv.org/abs/2510.18924) | 已直接讨论 GRPO/Dr.GRPO 的 reward flip correction。论文题名与摘要的“无偏”必须对应其精确目标、归一化约定及噪声率假设，不能仅凭名字判断与当前方法等价。 | A；主项目另有专门理论审计 |
| Thaman, **Reward Hacking Benchmark: Measuring Exploits in LLM Agents with Tool Use**, 2026-05-03, [2605.02964](https://arxiv.org/abs/2605.02964) | 工具任务的验证跳过、metadata/evaluator 攻击与环境加固。需要测独立任务正确性，不能只测 critic 认可度。 | A |
| Wang et al., **The Verification Horizon: No Silver Bullet for Coding Agent Rewards**, 2026-06-24, [2606.26300](https://arxiv.org/abs/2606.26300) | 明确讨论 verifier 可扩展性、忠实性、稳健性，以及策略能力变化下固定奖励失效。不能把“验证器也是瓶颈”单独作为新科学发现。 | A |
| Wang et al., **Teach the Magnitude, Not the Direction: Verifier-Bounded Credit Assignment for Multi-Turn Multi-step LLM Agents**, 2026-08-13, [2608.13179](https://arxiv.org/abs/2608.13179)；[CrEST 正文](https://arxiv.org/html/2608.13179v1) | per-turn verified advantage × bounded teacher weight；附录 A 明确只保 token 标量系数符号，不能保证总参数梯度或全局 ceiling。正文部分更强措辞不可直接继承。实验是固定回合结构工具基准；单训练 seed、三次近确定解码不是三次独立训练。 | F |
| Kenton et al., **Debate Training Reduces Reward Hacking in RLAIF**, 2026-08-18, [2608.17776](https://arxiv.org/abs/2608.17776) | debate/critic 能改善监督也能学会攻击弱 judge；有 critic 长度限制研究。不能把“加 critic 即可靠”作为前提。 | A |
| Adeli, **Strategic Verification for Long-Running LLM Agents**, 2026-08-28, [Preprints.org 202608.2057](https://www.preprints.org/manuscript/202608.2057) | BAVAR 已做验证时机、对象、路由、信用及成本的序贯框架。作者页面明确未同行评审、结果为 illustrative simulation。它不是本项目已完成的真实 LLM 训练证据，也不提供当前有限组无偏目标的直接替代。 | F：框架、实验性质 |
| Wang, Zhang & Shao, **Auditing Harness Tampering in Self-Improving Agents**, 2026-08-30, [2609.00069](https://arxiv.org/abs/2609.00069) | 已有 harness tampering 分类/定位与良性修改对照。不得仅以 provenance 和受保护评估器声称首创。日期早于其 2609 编号月份，按官方提交史记录。 | A |
| Yao et al., **Forgetting Without Restarting: Execution-State Unlearning for Stateful LLM Agents**, 2026-09-04, [2609.04875](https://arxiv.org/abs/2609.04875) | execution state 包含 KV/memory/summary/plans；provenance-guided selective replay 清除污染。用途是状态遗忘，不等于 RL 信用，但完整/选择性回滚是明显先例。 | A |

### 2.3 记忆、依赖任务与足够强的 baseline

| 文献与首次公开日期 | 核验内容及边界 | 阅读深度 |
|---|---|---|
| **MemAgent: Reshaping Long-Context LLM with Multi-Conv RL-based Memory Agent**, 2025-07-03, [2507.02259](https://arxiv.org/abs/2507.02259) | 多轮 RL 与可覆盖更新的记忆；不是 2026 年才出现。 | A |
| **Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning**, 2025-08-27, [2508.19828](https://arxiv.org/abs/2508.19828) | RL Memory Manager 已有 ADD/UPDATE/DELETE/NOOP 动作；直接推翻附件 G01 对动作空间的空白判断。 | A |
| He et al., **MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks**, 2026-02-18, [2602.16313](https://arxiv.org/abs/2602.16313)；[正文](https://arxiv.org/html/2602.16313v1) | 明确跨 session、任务依赖与 memory–agent–environment loop；涵盖网页、规划、检索、形式推理。附件“现有评测全是单 session”不成立。 | F：任务设计 |
| **MemFactory: A Unified Inference and Training Framework for Agent Memory**, 2026-03-31, [2603.29493](https://arxiv.org/abs/2603.29493) | 多种 memory 策略的统一推理/训练框架，进一步限制“首次把记忆与 RL 打通”的叙述。 | A |
| **LongDS-Bench: On the Failure of Long-Horizon Agentic Data Analysis**, 2026-05-28, [2605.30434](https://arxiv.org/abs/2605.30434) | 从公共 Kaggle notebooks 构造长期依赖分析，包含 rollback/counterfactual perturbation 等能力。可以考察真实可执行 Python 任务子集；作者链接 [DataMind](https://github.com/zjunlp/DataMind) 的完整数据、许可、可复现性尚须下载前检查。 | A |
| Pu et al., **Explore More, Drift Less: Outcome-Only Reinforcement Learning Can Suffice for Long-Horizon Interactive Agents**, 2026-09-01, [2609.01245](https://arxiv.org/abs/2609.01245) | CANOPY 主张足够探索、on-policy/KL/action-token 约束后，纯 outcome RL 可表现很强。不能用偏弱探索预算的 GRPO 来证明必须引入密集信用。公开榜单成绩仅按作者报告，未独立复现。 | A |
| Yao et al., **Tracking the Moving Frontier: Long-Short Term Advantage Estimator**, 2026-09-06, [2609.06671](https://arxiv.org/abs/2609.06671) | 历史基线与短期状态经验、每 anchor 单条 rollout。若未来研究重用历史信用，需要比较该近期先例。 | A |

### 2.4 两个不可遗漏的经典边界

* Zeller & Hildebrandt，**Simplifying and Isolating Failure-Inducing Input**，IEEE TSE 28(2):183–200，2002 年 2 月；[官方 DOI](https://doi.org/10.1109/32.988498)，[作者论文页与 PDF](https://www.st.cs.uni-saarland.de/papers/tse2002/)。自动删除输入/修改并重跑以缩小故障集合，是 delta debugging 的既有方法。附件 MinPatchCredit 可以变成一种研究对象/基线，但不能宣称首次“最小化补丁后进行因果信用”。
* Liu et al.，**Multi-Fidelity Policy Gradient Algorithms**，2025-03-07，[2503.05696](https://arxiv.org/abs/2503.05696)；后续 TMLR 记录见 [OpenReview 正文](https://openreview.net/pdf?id=zAo0L7Dcqt)。低保真策略梯度控制变量已有直接先例。环境代理作为控制变量、同随机数配对、保留高保真残差，并非本项目首次。精确出版版本题名与详细定理由环境查新分工核验，本报告不另填未经核对的 DOI。

## 3. 附件中需要删除或降格的判断

| 附件判断 | 审计结果 | 可替代的研究表述 |
|---|---|---|
| 满足“10 轮、10^5 tokens、状态不可单轮恢复”中两条即为长程 | 可作为个人筛选口径，不能当共同定义。长 token 不是高依赖深度；确定性长脚本也可能很好恢复。 | 分开记录动作数、token 数、依赖跨度、不可逆性、部分可观测性。 |
| 记忆方向 8 篇均在 2605 以后 | 与自己表中的 2025 条目冲突；官方 Memory-R1/MemAgent 日期亦反证。 | 删除数量/时间断言，按每篇日期呈现。 |
| G01：ADD/UPDATE/DELETE 从未进入动作空间 | Memory-R1 直接反证。 | 限定新的写入质量目标、跨任务效应或噪声情境，再查新。 |
| G01/G02：现有评测均为单 session | MemoryArena 直接反证。 | 指定现有 benchmark 未覆盖的某项可控依赖或资源约束。 |
| C18/C19：snapshot siblings、同状态分组具有无人占据的结构红利 | BPO/G2PO/VinePPO 均直接相关。 | 比较精确目标、状态等价假设和计入 reset 的总成本。 |
| 稠密信用与 verified direction 自动避免 reward hacking | reward/critic 仍可能错误或受攻击；正权重不会保证总梯度方向。 | 单独测 verifier 正确性、有限组目标误差与隐藏测试真实性能。 |
| MinPatchCredit 得到“真正必要的修改” | 1-minimal 不是 minimum；充分子集可能不唯一；测试通过不是全语义正确。 | 明确编辑粒度、固定测试集合、最小性定义和允许的交互作用。 |
| “同预算”的 return 数等于相同 compute | 后缀长度、snapshot、模型/token、测试启动和缓存开销不同。 | 至少并列查询数、环境步、模型 tokens、wall clock；不混称总加速。 |
| 零外部信号/极低开销族里纳入 judge 分类 | 表内部“judge”与“零额外模型”口径冲突，实际要逐项计费。 | 分开训练标注、额外前向、外部模型以及固定规则成本。 |
| 空白格等于新颖性证明；局部节点已饱和 | 未提供系统检索、集合边界或排除证据。 | 标注待验证假设；以最接近论文的逐项差异代替。 |
| 8×A800 的周期直接当实施方案 | 与当前 M1 Pro 16GB/剩余约 17GB 磁盘不符。 | 小规模精确机制先执行；大模型 RL 单列 GPU/存储条件。 |

附件中跨论文的提升数字、作者 limitation 引语及缺少 arXiv ID 的名字，未经逐篇原表/设置核对不应搬到正文。没有在此表核验的条目不意味着不存在。

## 4. 独立理论检查：局部保证不能被升级成全局保证

以下是本审计自行构造的有限反例，不是对作者实验代码的复现。`experiments/literature_counterexamples.py` 使用有理数穷举，结果已保存 `results/literature_counterexamples.json`。

### 4.1 分支后的零均值对比会丢失早期动作的效应

设第一步 `a0 ~ Bernoulli(p)`，其后状态记录 `a0`，终态奖励 `R=a0`。第二步动作完全不影响奖励。从第二步精确恢复同一状态并采样任意多个兄弟，所有兄弟回报相同，局部 leave-one-out 优势恒为零。

但对第一步 logit 参数 `θ`，真实梯度 `d E[R]/dθ = p(1−p)` 严格为正。把第二步的局部优势乘任何折扣后传播到第一步仍为零；在 `p=1/4` 时，正确值为 `3/16`。若第一步熵低于第二步，可使 top-1 entropy scheduler 只选第二步。

这解释为什么 BPO 式局部无偏引理不能单独推出前缀传播后全梯度无偏。更一般地，若给定分支历史 `H_t` 有 `E[A_branch | H_t]=0`，早期 score `S_u`（`u<t`）对 `H_t` 可测，则 `E[S_u A_branch]=0`。它不能单独恢复早期决策改变后续状态分布所产生的项。

应保留正确的局部结论；若作者实现还保留完整 backbone 贡献或别的补偿项，必须分析完整估计器再下结论。不能据该反例宣称其所有实验无效。局部优势方差减少也不能代替梯度 MSE 或训练效率的比较。

### 4.2 正系数不会阻止总梯度反向

取两个一维 token 梯度贡献 `g1=1, g2=−0.99`，原和为 `0.01`。取权重 `w1=1, w2=1.084`，两个权重都正且只最多增幅 8.4%，新和为 `−0.07316`，方向反转。

普遍成立的是绝对扰动界

`||Σ_t (w_t−1) g_t|| ≤ δ Σ_t ||g_t||`，当 `|w_t−1|≤δ`。

一般不成立的是把右侧换成 `δ ||Σ_t g_t||`。CrEST 附录已明确这一绝对/相对区别，因此本例用于防止本项目误读“direction”，不是给其附录新增一个反驳。

### 4.3 最小化补丁不是唯一归因

假设 `{a}` 或 `{b,c}` 均足以让固定测试通过。`{b,c}` 删除任意一个元素都会失败，因此是 1-minimal；但最少元素的充分集合是 `{a}`。两个集合都不能自动定义策略训练中的唯一因果效应。固定测试看不见的语义还可以改变这一结论。

### 4.4 回滚相同观测不能识别相同潜在状态

可构造两个系统拥有相同文件/DOM 观测，而未恢复的数据库事务、随机数流、外部服务缓存或 agent memory 不同，导致同一动作的终态回报不同。仅比较文件哈希或当前输出不能排除这一情况。

若明确假设真实恢复与近似恢复的整个后缀回报分布 TV 距离至多 `ε`，且 `R∈[0,1]`，则均值偏差至多 `ε`；两种动作的差值偏差至多两个误差之和。这是经典 TV 期望界的应用，不是新定理；关键难点在于如何获得可检验且对应真实执行的误差条件。有限 sentinel 测试只对其覆盖的状态/动作提供证据，不能无条件证明所有未来恢复正确。

## 5. 两个可以做实的具体问题

### 问题 A（当前主方向）：验证查询怎样穿过有限组非线性归一化？

**对象。** 在 policy checkpoint 与 rollout group 固定后，终态 reward 尚未全部查询；cheap predictor 可任意错误。目标是完整标签下的实际有限组 GRPO/PPO surrogate 或其明确线性系数，不是泛称 population success gradient。

**有价值的结果。** 在精确随机审计设计下恢复该组目标，说明 hard cap 和 expected budget 的差别，明确 clipped surrogate 的正/负部分；同时给出 misspecified proxy 时的无偏性与方差失败区间。探索是否存在由标准化引入的必须联合观察的结构。只纠正每条 reward 后再归一化，通常不足以保证纠正归一化后的函数。

**已有与未有。** Randomized telescoping、Russian roulette、控制变量和抽样加权是既有数学工具；noise-channel correction 亦已有直接 GRPO 先例。BAVAR 已有预算分配框架。潜在贡献是特定有限组函数的查询下界、正确的构造、实际成本和失败区域的联合证据。此报告的定向检索未发现与当前完整目标相同的直接实现，但这不是无人做过的证明。主项目必须完成独立先例/定理核验。

**与 long horizon/env scaling 的实质连接。** 新环境的 terminal tests/远程工具验证比 rollout 生成更贵时，审计预算影响能训练多少环境实例；长程引起成功率极端化和组信号稀缺时，联合标签依赖改变审计效率。必须用测量体现这种关系，不能只把题目加上 long-horizon。

**CPU/MPS 可独立验证。** 小组全部二元标签枚举；固定组 Monte Carlo 的 bias/MSE/方向误差与权重尾部；真正执行的轻量 Python/SQLite 任务训练；隐藏 terminal verifier 标签在 audit 时才可见。至少加入 strong whole-group residual correction、完整验证、proxy-only、随机部分替换、reward-IPW-then-normalize，并与未标准化目标比较。开发时选 schedule，报告时冻结。最终报告查询、任务执行、预测器训练/前向、同步与 wall time 各成本。

**可能失败。** 罕见 mixed groups、误校准 proxy、审计成本不高、不可承受 correction tails 或过度昂贵完成期望计算，都可能让完整验证更优。无偏梯度经过 Adam/clip 后不等于完整验证的训练轨迹；不能借无偏定理跳过 end-to-end 学习。

### 问题 B（备选/诊断）：依赖深度与 reset fidelity 如何改变分支信用的有效性？

**对象。** 让动作数 H 与真正决定终态的依赖深度 D 正交变化，加入可恢复/不可完整恢复的外部状态。比较局部 credit 的好看方差与真实早期动作梯度。

**可证部分。** 上节条件零均值的消失项、正确轨迹目标的分解以及有条件的恢复误差界。修正可保留普通 backbone return，使用独立/留一 baseline 或正确 state occupancy 权重。这里的基础修正也有经典先例；不要先给算法起名字再寻找优势。

**最接近方法。** VinePPO、BPO、RRPO/SRPO、G2PO、PCCC、execution-state unlearning。新颖性应来自精确刻画“什么时候同前缀变成错误条件化”、依赖控制的真实执行基准，以及成本约束下经验证的改进，不是 snapshot primitive 本身。

**本地实验。** Tabular/小 MLP policy 的有限 MDP 给精确梯度；Python 状态机用文件、SQLite、随机数状态与 agent memory，分别完整恢复和故意缺失一种状态；任务含 fork/merge、覆盖、延迟 AND 依赖和独立 padding。测 early-action gradient、cosine/MSE、终态成功及 reset/rollout/verifier 成本。至少 20 个独立训练 seeds；horizon、dependency depth 与恢复错误概率为独立轴，保留所有格子。

**真实外部验证。** 若 LongDS-Bench 作者资源可运行且许可清楚，选固定可执行任务与干预协议，先做 replay/诊断，再考虑 LLM policy training。没有大模型训练时，只能说机制与执行环境证据，不能写已改善 7B agent。

## 6. 实施范围与仍需查验

当前 M1 Pro 16GB 足够完成有限函数穷举、tabular/小 MLP RL、轻量真实工具任务、成对 Monte Carlo 与小模型推理诊断。剩余约 17GB 磁盘不适合先下载完整 SWE-bench Docker 库或多个 7B checkpoint。附件以 8×A800 为基础的长上下文 RL 预算不能迁移到本机。

大型模型部分应在获得具体 GPU、存储、训练时长后单独冻结协议：至少一个真正更新策略的模型、足够强 outcome-only baseline、相同调参预算、多训练 seed、独立任务测试和真实成本账本。不能把模型输出回放写成训练，也不能把合成 noise 机制写成生产环境观测。

尚未完成事项：所有候选的代码/许可证下载检查、所有摘要成绩复现、所有发表状态的会议交叉核实、附件每个未列条目的原表对数、对当前随机审计方案的完整最新先例证明。它们不阻止先做精确机制实验，但会限制论文可以使用的实证与新颖性措辞。

## 7. 本审计可复现产物

* 查新记录：本文件；逐项给出 primary URLs 与日期。
* 独立有限反例：`experiments/literature_counterexamples.py`。
* 已执行结果：`results/literature_counterexamples.json`。无随机种子需求，使用 Python 标准库 Fraction 精确枚举；3 项断言全部通过。它们只检验本文写出的构造，不是任何被引论文的复现性能。

复跑：从项目上级工作区执行 `.venv/bin/python agent_reliability_research/experiments/literature_counterexamples.py`。未修改旧论文或主项目实验。

# 主动复测、独立验证与组内优先名单：理论及先例审计

独立审计日期：2026-09-11。范围为新项目 `nhs_aisi_research/`。原 `nhs_wellbeing_research/` 论文、数据和 release 未修改。本文件是研究设计与理论审计，不是正文，不承诺首创或录用。

## 1. 先例结论：不能把两类测量加 KG 当成新算法

当前候选方法是一个明确可实现的 **multi-information-source knowledge-gradient 应用**：对目标 θ 与持续偏差 b 建联合信念，比较继续从 θ+b 渠道取样和从另一个测量渠道获得信息的决策价值。其计算可透明、可复现，但以下组成均已有直接先例。

| 方向 | 已核实原始文献 | 与本项目的关系及区别 |
|---|---|---|
| Bayesian terminal value / knowledge gradient | Frazier, Powell & Dayanik (2008), *A Knowledge-Gradient Policy for Sequential Information Collection*, SIAM J. Control Optim., 47(5), 2410–2439. [出版社](https://epubs.siam.org/doi/abs/10.1137/070693424) | 选择下一测量以提升终端决策价值，并不是新思想。一步最优与固定多步预算最优不同。 |
| 相关 Gaussian KG | Frazier, Powell & Dayanik (2009), *The Knowledge-Gradient Policy for Correlated Normal Beliefs*, INFORMS J. Computing, 21(4), 599–613. [出版社](https://pubsonline.informs.org/doi/10.1287/ijoc.1080.0314), [作者全文](https://people.orie.cornell.edu/pfrazier/pub/CorrelatedKG.pdf) | 已处理观察一项改变多个候选信念；本项目独立单位模型是简化情形。下载的作者版本为扩展稿，不混作出版社分页。 |
| **最直接：有偏信息源 + KG/cost** | Poloczek, Wang & Frazier (2017), *Multi-Information Source Optimization*, NIPS 30. [官方论文页](https://proceedings.neurips.cc/paper_files/paper/2017/hash/df1f1d20ee86704251795841e6a9405a-Abstract.html), [全文](https://proceedings.neurips.cc/paper_files/paper/2017/file/df1f1d20ee86704251795841e6a9405a-Paper.pdf), [作者代码](https://github.com/misokg/NIPS2017) | 原文 §3.1 已用目标 GP 加独立 source discrepancy GP，§3.2 已以目标上的期望收益除测量成本。有限单位 θ_i+b_i、干净验证 θ_i 和 KG/cost 正是非常接近的有限域形式。不能以名称或社会应用替代这个引用。 |
| 信息价值不必凹、myopia 可失败 | Frazier & Powell (2010), *Paradoxes in Learning and the Marginal Value of Information*, Decision Analysis, 7(4), 378–403, DOI 10.1287/deca.1100.0190. [作者全文](https://optimallearning.princeton.edu/Papers/Frazier%20Powell%20-%20Paradoxes%20in%20learning%20and%20the%20marginal%20value%20of%20information.pdf) | 不能未经证明套用 diminishing returns、greedy 1−1/e 或固定预算最优保证。本文下面的简单反例是解释工具，不声称首次发现 myopic 失败。 |
| 经济价值与停止 | Chick & Frazier (2012), *Sequential Sampling with Economics of Selection Procedures*, Management Science, 58(3), 550–569, DOI 10.1287/mnsc.1110.1425. [作者全文](https://people.orie.cornell.edu/pfrazier/pub/2012_ChickFrazier.pdf), [出版社](https://pubsonline.informs.org/doi/10.1287/mnsc.1110.1425) | 已把测量成本和自适应停止的后续价值放入动态决策。期刊卷期为 2012，在线发表为 2011；二者不要误当两篇。 |
| Top-m OCBA | Chen, He, Fu & Lee (2008), *Efficient Simulation Budget Allocation for Selecting an Optimal Subset*, INFORMS J. Computing, 20(4), 579–595, DOI 10.1287/ijoc.1080.0268. [出版社](https://pubsonline.informs.org/doi/10.1287/ijoc.1080.0268) | 已在固定样本预算下最大化正确选出全部 top-m 的近似概率，并推导渐近 allocation。其目标是集合完全正确概率，不等同平均 severity regret。另下载的 [5 页 INFORMS 文档](https://higherlogicdownload.s3.amazonaws.com/INFORMS/ef27cc87-0593-4a9b-85b3-52b5bbeae306/UploadedImages/10.pdf) 是 **2007 workshop 前身**，不能声称已读取 2008 journal 全文。 |
| Online subset KG | Ryzhov & Powell (2009), *The Knowledge Gradient Algorithm for Online Subset Selection*, IEEE ADPRL, 137–144, DOI 10.1109/ADPRL.2009.4927537. [作者机构记录](https://collaborate.princeton.edu/en/publications/the-knowledge-gradient-algorithm-for-online-subset-selection), [作者稿](https://citeseerx.ist.psu.edu/document?doi=b19608601ab66f4d96cec56428ec1d7e045e77e0&repid=rep1&type=pdf) | 已有 subset + KG 的直接组合。不过该稿测量的是可能有交互的子集，并追求在线累计收益，并不等于本项目逐单位测量后的固定终端配额。 |
| PAC top-m / boundary sampling | Kalyanakrishnan, Tewari, Auer & Stone (2012), *PAC Subset Selection in Stochastic Multi-armed Bandits*, ICML, 655–662. [作者论文页及全文入口](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-ICML12-shivaram.html) | LUCB 已主动测量边界相关候选，不能声称“优先测 cutoff 附近”是新思想。其固定置信度目标与给定预算下平均严重度损失不同。 |
| Fixed-budget top-m | Bubeck, Wang & Viswanathan (2013), *Multiple Identifications in Multi-Armed Bandits*, ICML / PMLR 28(1), 258–265. [官方全文](https://proceedings.mlr.press/v28/bubeck13.pdf) | Successive accepts and rejects 已处理多个最优臂与多个 bandit 的识别。官网 BibTeX 的 Bubeck 名字有拼写错误，应以 PDF 标题页的 Sébastien 为准。 |
| 组合约束 / 配额 | Chen, Lin, King, Lyu & Chen (2014), *Combinatorial Pure Exploration of Multi-Armed Bandits*, NIPS 27. [官方页](https://papers.nips.cc/paper_files/paper/2014/hash/d3ea0f3316d2da934d79b8b344eafee4-Abstract.html), [全文](https://proceedings.neurips.cc/paper_files/paper/2014/file/d3ea0f3316d2da934d79b8b344eafee4-Paper.pdf) | 允许有组合结构的可行子集，并有固定预算/固定置信度结果。分组名额本身不是新 combinatorial exploration。 |
| Robust ranking | Gao, Xiao, Zhou & Chen (2017), *Robust Ranking and Selection with Optimal Computing Budget Allocation*, Automatica, 81, 30–36, DOI 10.1016/j.automatica.2017.03.019. [出版社](https://www.sciencedirect.com/science/article/pii/S0005109817301425) | 在有限输入情景中按每设计最坏表现选优。它与“同一真实目标被偏差污染、无法识别”并非相同 estimand，但 robust + OCBA 已有直接先例。出版社摘要可读，全文入口曾返回 403，未绕过访问控制。 |
| 多保真偏差与成本 | Poiani, Metelli & Restelli (2022), *Multi-Fidelity Best-Arm Identification*, NeurIPS 35. [官方页](https://proceedings.neurips.cc/paper_files/paper/2022/hash/71c31ebf577ffdad5f4a74156daad518-Abstract-Conference.html)；Poiani, Degenne, Kaufmann, Metelli & Restelli (2024), *Optimal Multi-Fidelity Best-Arm Identification*, NeurIPS 37. [官方全文](https://proceedings.neurips.cc/paper_files/paper/2024/file/dc9e095f668044e7a0909a4ea3926beb-Paper-Conference.pdf) | 已研究便宜有偏与昂贵高精度源的成本复杂度；2024 工作含紧的 instance-dependent 下界与渐近最优方法。其保证依赖已知 fidelity bias bounds 等条件；不能直接转给无法校准偏差的调查数据。 |
| 不可识别污染下的主动学习 | Altschuler, Brunel & Malek (2019), *Best Arm Identification for Contaminated Bandits*, JMLR 20(91), 1–39. [全文](https://jmlr.csail.mit.edu/papers/volume20/18-395/18-395.pdf) | 已明确处理无限样本仍部分不可识别及相应复杂度/下界。其 contamination 与本项目随机但 unit-persistent additive bias 不同；不可识别本身并不是新发现。 |
| **近期直接先例：代理 + 选择性审计** | Ao, Chen, Gao, Li & Simchi-Levi (2026), *Best Arm Identification with LLM Judges and Limited Human*, arXiv:2601.21471. [原始记录与全文](https://arxiv.org/abs/2601.21471) | 2026-01-29 预印本，标题按原文保留。已研究便宜有偏 proxy、昂贵 human audit、选择性标签和审计效率。其目标、context/IPW 框架与本项目 Bayesian 静态组内严重度损失不同，但两行动及不可消失误选有显著先例重合。引用其问题与方法，不把尚未独立核实的所有证明视为本项目可直接继承的保证。 |

### 先例对贡献定位的实际影响

目前不宜声称：新 KG、新 OCBA、新 top-k 识别、新多保真、首次主动审计、或首次发现持续偏差不能被平均消除。**更有希望的应用科学问题**是：在社会筛查里，哪些不确定性会改变实际名额名单；下一单位测量预算究竟应改善原渠道的精度，还是购买能区分目标与偏差的信息；在验证渠道也有偏差、测量延迟和组内配额时，这个答案如何改变。

这一研究仍须靠执行结果证明有用性。仅把经典方法与 NHS 标题放在一起，不足以自动产生新的 AISI 贡献。

## 2. 精确目标：不要让配额与归一化悄悄改变预算问题

单位分成已固定 benchmark groups。组 g 有 M_g 个单位，固定选择 k_g 个，K=Σ_g k_g。可行集合为

\[
\mathcal S=\{S: |S\cap g|=k_g\;\forall g\}.
\]

令较低 θ_i 表示较大需要。主目标可定义为所有入选单位的平均严重度后悔值：

\[
L(S,\theta)=K^{-1}\left[\sum_{i\in S}\theta_i-
                 \min_{A\in\mathcal S}\sum_{i\in A}\theta_i\right].
\]

给定完整测量历史 D，Bayes action 按每组后验目标均值 m_i=E(θ_i|D) 取最低 k_g。证明只是期望线性与可行集合固定，**不需要单位后验独立**。这不是成本—健康收益最优分配，也不是集合命中率最优规则。

如果改为各组等权平均后悔值 G⁻¹Σ_g L_g，则组 g 行动的价值要额外按 1/(G k_g) 加权。对所有被选单位等权时，统一的 1/K 不影响下一行动的排序。两种公平/效用选择可能分配不同的信息预算，应由问题定义决定。

## 3. 候选方法 A：目标与持续偏差分开的 quota-aware KG

这是已知 KG/MISO 的透明专门化，不命名为一个全新的算法。

### 3.1 联合 Gaussian 更新

给定历史，单位 i 的状态 (θ_i,b_i) 有均值 (m_i,a_i) 和协方差

\[
P_i=\begin{pmatrix}v_i&c_i\\c_i&q_i\end{pmatrix}\succeq0.
\]

重复渠道的 loading 是 h_R=(1,1)ᵀ，理想独立验证渠道是 h_A=(1,0)ᵀ。行动 d 的观察为

\[
W_{id}=h_d^T(\theta_i,b_i)+\epsilon_{id},\quad
\epsilon_{id}\mid(\theta_i,b_i),D\sim N(0,r_{id}),
\]

且新噪声独立于状态、历史和其他新噪声。定义 V_{id}=h_dᵀP_i h_d+r_{id}>0，则

\[
P_i^+=P_i-\frac{P_i h_d h_d^T P_i}{V_{id}},\qquad
m_i^+=m_i+\frac{(P_i h_d)_1}{\sqrt{V_{id}}}Z,
\quad Z\sim N(0,1).
\]

因此 posterior target mean 的创新标准差为

\[
s_{id}=\frac{|(P_i h_d)_1|}{\sqrt{V_{id}}}.
\]

这不是剩余 θ 不确定性 √v_i；它量化**本行动能够改变多少目标信念**。a 次条件独立同渠道测量的样本均值可把 r 替换为 r/a；持续 b 不随 a 消失。

### 3.2 命题：独立单位下的精确一步严重度价值

假设单位之间后验独立、超参数及分组固定，而且行动只更新 i 的均值。令 t_i 是同组其余 M_g−1 个单位中第 k_g 小的均值；这对 0<k_g<M_g 定义良好。设 Δ_i=|m_i−t_i|。则该行动的精确一步期望后悔值下降为

\[
\operatorname{KG}_{id}=\frac1K
\left[s_{id}\varphi(\Delta_i/s_{id})-
\Delta_i\Phi(-\Delta_i/s_{id})\right],
\]

其中 s=0 时取 0。若 k_g=0 或 M_g，局部测量不能改变该组的选择，价值为 0。

**证明。** 同组其余单位最低 k_g−1 项的均值和记为 C。不论测量结果怎样，测后最低 k_g 均值和是 C+min(m_i+sZ,t_i)。对正态截断期望积分，并用 tower property 使 oracle 项的前后期望抵消，得上式。当前已选 i 的 t_i 是全组第 k_g+1 项；当前未选 i 的 t_i 是全组第 k_g 项。这是对手阈值，不能不分情形统一取当前第 k_g 项。

对 s>0、Δ≥0，忽略统一 1/K 后有

\[
\frac{\partial\operatorname{KG}}{\partial s}=\varphi(\Delta/s)>0,
\qquad
\frac{\partial\operatorname{KG}}{\partial\Delta}=-\Phi(-\Delta/s)<0.
\]

所以决策价值同时依赖边界距离和**可约减**不确定性。组内最差单位、总方差最大单位和下一测量最有价值的单位可能不同。

### 3.3 一个方差优先规则失败的明确例子

两候选在各自相关边界的 gap 都是 .1。候选 A 的 P=[[1,−.99],[−.99,1]]，候选 B 的 P=diag(.25,0)，repeat noise variance 都为 .1。A 的目标方差是 B 的四倍，但 repeat 创新标准差分别为 .0288675 和 .4225771，未归一 KG 分别为 0.000001946 和 0.1232823。A 的大部分剩余目标不确定性与已知的 θ+b 方向正交，重复旧渠道几乎不能解决它。

这是可计算反例，不是“variance sampling 永远差”的定理。

### 3.4 成本归一不等于总预算最优

选择 max KG/cost 是有合理含义的 myopic cost-normalised policy，已有 MISO 先例，但没有自动的固定总预算最优性。在不同成本下，即便只允许再做一次行动，也应在可负担集合里最大化**总 KG**，而不是 KG/cost。

更强的两步反例：一个已知标准为 0，另一目标 θ~N(0,1)，选择二者较低者。两行动都直接测 θ，cheap 方差1、成本1；accurate 方差.1、成本2；总预算2。初始 KG/cost 分别 .2820948 和 .1901883，因此 ratio policy 先选 cheap，剩余预算只能再选 cheap。两次 cheap 的总期望价值为 .3257350；一次 accurate 的价值为 .3803765。这个反例完全在正确 Gaussian 模型内成立。

因此应保留 cost-matched uniform、两渠道固定比例、可约减方差/边界基线及准确标识的 KG 比较；若加 rollout 或预算预留，它仍是另一个待检验策略，不能不证明就称全局最优。

## 4. 候选科学问题 B：重复精度与偏差验证的不可约下界

最有用的理论输出是明确哪些信息方向重复再多也学不到，以及这些方向是否真的影响名额损失。

### 4.1 命题：重复同一有偏渠道的目标方差下界

静态、单单位模型 θ~N(μ,τ²)、b~N(0,β²)，二者独立。n 次重复为 W_j=θ+b+ε_j，ε_j iid N(0,r)。则

\[
\Var(\theta\mid W_{1:n})
=\tau^2-\frac{\tau^4}{\tau^2+\beta^2+r/n}
\longrightarrow\frac{\tau^2\beta^2}{\tau^2+\beta^2}.
\]

**证明。** 样本均值是充分统计量，以其和 θ 的二维联合 Gaussian 条件化。极限等于直接获知 T=θ+b 后的目标方差。

从一般当前后验 P=[[v,c],[c,q]] 开始，无限额外 repeat 的极限为

\[
v-\frac{(v+c)^2}{v+q+2c},
\]

当分母为0时 T 已确定，按 v 处理，不能产生0/0。当 T 已精确获知时 Cov(θ,T|T)=0，新 repeat 的 KG 为0；若此时目标方差仍为正、验证噪声有限且条件独立，非退化组内选择的理想验证 KG 严格为正。但只要验证成本超过余下预算，就不能执行该行动。

### 4.2 命题：独立单位偏差产生精确的两单位选择损失下界

两单位独立同分布，θ_i~N(0,τ²)，b_i~N(0,β²)，且 θ 与 b 独立；终端选一个最低 θ。即使免费获得两个精确的 T_i=θ_i+b_i，最优 Bayes 期望严重度后悔值仍为

\[
R_{\infty}^{\rm repeat}
=\frac{\tau}{\sqrt\pi}
\left(1-\frac{\tau}{\sqrt{\tau^2+\beta^2}}\right)>0
\quad(\tau,\beta>0).
\]

**证明。** m_i=τ²T_i/(τ²+β²)，其边际标准差为 τ²/√(τ²+β²)。两个独立中心正态的最低值期望等于标准差乘 −1/√π。将 E min_i m_i 与 E min_i θ_i 相减即得。任何仅观察 noisy repeats 的自适应策略，其信息均不多于精确 T，因此 Bayes 风险不能低于该值。这里无需把有限预算的 KG 当成最优策略。

参数 τ=.35、β=.30 时，该下界为 .047538721；独立 400,000 次 Monte Carlo 检查得到 .047708217，MCSE=.000190891，差异为 .888 个 MCSE。

也可给出不依赖 Gaussian 先验的两世界反例：世界一 θ=(−d,d), b=(d,−d)，世界二 θ=(d,−d), b=(−d,d)，两个世界的有偏渠道均值均为 (0,0)。所有 repeat-only 自适应轨迹同分布，但最佳单位相反。至少一个世界的误选率≥1/2，期望严重度后悔值≥d。这是经典不可识别/二点下界思路，与污染 bandits 和近期 proxy-audit 文献有先例联系。

### 4.3 关键反例：正水平方差下界不保证正排序下界

**命题（固定配额下的组内平移不变性）。** 若每组固定 k_g，则对任何常数或随机组偏移 a_g，令 θ'_i=θ_i+a_g，则对所有可行 S，

\[
L(S,\theta')=L(S,\theta).
\]

**证明。** 每个可行集合及 oracle 都在组 g 恰好包含 k_g 项，两个和中增加的 Σ_g k_g a_g 完全相消。

所以若 b_i=b_g 在组内完全共享，无限 repeat 能识别 θ_i−θ_j=T_i−T_j，进而恢复组内名单；单个单位水平的未识别部分不必影响固定配额的排序损失。4.2 的正选择下界依赖 unit-specific 偏差结构，不能推广到任何持续偏差。

同一事实也暴露了独立 KG 闭式的边界：若 θ_1=θ_2=Z，且共同信念方差为1，观察任一单位只是同时平移两均值，真实排序信息价值为0。若错误地只更新一个单位，独立公式会给出 .3989423 的虚假价值。共同均值、共同偏差或更新共享超参数时应使用 joint KG，或明确承认模型错误；不能继续套单单位闭式。

### 4.4 验证渠道自身有偏差时

“Independent audit”必须明确为给定单位目标后的零均值、重复间独立测量误差，而不是仅与原渠道的偏差不相关。若验证实际为 θ+d+η，d 是另一持续偏差，即使 d 与原 b 独立，重复也不会平均掉 d。

当 θ、b、d 独立且先验方差分别为 τ²、β²、δ²，免费精确知道 θ+b 和 θ+d 后仍有

\[
\Var(\theta\mid\theta+b,\theta+d)
=\left(\tau^{-2}+\beta^{-2}+\delta^{-2}\right)^{-1}>0.
\]

若两渠道共享完全相同 b，则第二渠道只是对同一偏差方向减少随机噪声，不能拆分 θ 与 b。声称“audit 必定解决偏差”需要更强测量设计或识别信息，本项目不能从 NHS 年度汇总证明它。

### 4.5 有用的同单位行动切换阈值

对同一单位、同一边界 gap，KG 随 s 单调增加。因此等成本下，理想验证优于 repeat 当且仅当

\[
\frac{v^2}{v+r_A}>
\frac{(v+c)^2}{v+q+2c+r_R}.
\]

独立初始信念 c=0 时，这简化为 r_A<q+r_R。成本不同时要比较完整 KG/cost；在恰处边界 Δ=0 时，则比较 s_A/c_A 与 s_R/c_R。远离边界时非线性尾部会改变成本阈值，不能只比较方差下降除成本。

这些结果支持绘制 **bias share × cost × boundary gap × covariance structure** 的行动切换/失败图。它是目标明确的应用结果，不以一个无根据的“全局最优资源分配”标签包装。

## 5. 实验建议与真实数据边界

1. NHS 年度汇总提供初始名单、组别、规模和真实分数分布；没有查询/重复个体测量日志或真实验证结果。用这些分数生成行动回报属于明确的 NHS-informed simulation，不能称实际开展了 NHS 主动验证。
2. 公共微数据可以产生有限总体参考均值、屏幕样本与查询池。需区分调查加权总体估计、有限公开样本的参考值、以及无法观测的真实人群状态。以公开样本均值作评估真值不证明临床真值或无响应偏差。
3. 如果原渠道的偏差由预先声明的选择机制人工制造，报告人工机制及其强度；不要把它写成观测识别的 NHS/BRFSS 偏差。查询算法仅能读取已查询样本，评估参考不能泄漏进初始模型或调参。
4. 信息成本为场景假设，不是现实采购价格。保留高验证成本、预算不足、验证自身偏差、目标漂移和模型低估/高估 β 的失败结果。
5. 至少说明 unit-specific 与组内共同偏差的差别。固定配额的鲁棒性可能来自共同平移抵消，而非算法成功学习了偏差。
6. 主比较需要相同总成本、相同可用行动、固定初始信息和配对随机性。把能使用干净 audit 的算法与只能 repeat 的算法比较，测到的是信息集与行动集差异，不是纯策略优势；应额外保留同一行动集上的基线。
7. MC 基线和主方法均使用真实目标损失评估；集合命中率可作为次指标。不要把 severity KG 改称身份概率最优，不要用平均 regret 小就宣称每个群体都获益。
8. 处理漂移时必须指定目标时间。若 θ_t 随时间变化，旧时测量的价值取决于它与 θ_target 的协方差；静态二变量公式不再自动是正确 posterior。可将漂移作为明确的错误指定压力测试。

## 6. 本轮已执行的独立检查

代码：`experiments/verify_theory.py`；结果：`results/theory_verification.json`。代码不导入主实验程序，也不读取 study outcomes。运行 `.venv/bin/python nhs_aisi_research/experiments/verify_theory.py`。

- 60 个随机有限 top-k 问题：闭式 KG 与独立直接积分最大差 4.72×10⁻¹⁶。
- 验证重复测量的有限 n 方差及不可约极限，核对精确 T 下 repeat 创新消失而独立验证仍有信息。
- 400,000 次两单位 Monte Carlo 独立验证明确的 Bayes selection floor。
- 200 个三组配额问题验证组内共同偏移下 regret 与 oracle memberships 不变，最大数值误差 1.89×10⁻¹⁵。
- 执行固定预算下 KG/cost 的反例，以及“更大总方差却更低 repeat 价值”的反例。
- 核查两个各自含持续偏差的渠道仍保留目标方差下界。

文献缓存位于上层工作区 `research_workspace/nhs_aisi_literature/`，不把第三方 PDF 包进公开源码许可证。缓存 `manifest.json` 记录已下载来源；其中 `chen2008.pdf` 的文件名仅为检索标签，其实际内容已确认为 2007 workshop 稿。

## 7. 推荐交付定位

可保留两个清楚且可以完整做成的模块：**(A) 已知 MISO/KG 思想在固定 benchmark 名额与持续测量偏差下的透明实现；(B) 重复渠道何时无法继续改善决策、哪些共享偏差又对名单无害，以及错误验证假设如何浪费预算的理论与实证诊断。**

目前能证明的是上述具体结果，不能证明“本项目首次解决该问题”，也不能把未知偏差参数的设定称为对真实人群的识别。AISI 竞争力应来自社会决策问题的必要性、数据与测量机制的可信性、可解释行动选择，以及对失败情况的完整验证。

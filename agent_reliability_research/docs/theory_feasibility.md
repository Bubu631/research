# 数学可行性备忘录：从逐条奖励纠错到有限组更新的审计复杂度

2026-09-12。研究设计备忘录，不是完成的论文；原项目未修改。以下区分已经存在的方法、这里给出的可复核推导、尚待检索确认的新颖性，以及必须实际验证的效益。本文没有声称任何真实 agent 训练改善。

## 结论与建议

**否决把“廉价奖励 + 少量可信审计 + HT/AIPW纠错 + 按score和残差分配预算”单独包装成新算法。** 同样，直接升级为“用高/低保真轨迹贡献的control variate纠正环境差异”也已有非常近的multi-fidelity policy-gradient先例。

更可落地的窄问题是：**在不假定verifier错误分布的情况下，有限组奖励归一化和PPO clipping究竟要求怎样的审计单位、最坏情况查询深度与预算随机化，才能恢复指定的oracle grouped update？** 该目标是给定rollout group和参数的完整奖励更新，不是未经限定的true policy gradient。

本备忘录证明了二元、未触发clipping的GRPO聚合更新的精确Boolean degree：若组大小为G≥2、固定score不全相等，则偶G的degree为G−1，奇G为G−2。由经典query-tree的多项式表示可知，硬性最多b次真实label查询且b低于该degree时，不存在对每个可能reward vector都无偏的估计器，适应性查询也不例外。G2/3的更新是线性的，是不可漏掉的例外。允许随机较长查询路径、仅约束期望成本时，有限Russian roulette telescoping可以保留完整组更新的无偏性；该randomization基础不是新方法。

较有希望的贡献组合是：特定有限组函数的精确审计障碍、reward-level纠错无法穿过归一化/clipping的具体失效、针对实际训练更新的completion/telescoping实现、以及在真实可执行长任务上报告成本—方差—更新偏差。若最终只有一个小Boolean degree推导和标准roulette包装，没有显示现实成本/方差优势，则仍不足以支持强论文。

## 1. 直接相关先例与不可占有的贡献

| 原始来源 | 已有内容与本选题的边界 |
|---|---|
| [Horvitz & Thompson, JASA1952](https://www.tandfonline.com/doi/abs/10.1080/01621459.1952.10483446) | 不等纳入概率的无偏估计及方差，不能将1/q纠偏称新。 |
| [Beygelzimer, Dasgupta & Langford, IWAL2009](https://www.microsoft.com/en-us/research/publication/importance-weighted-active-learning/) | 主动labeling下的重要性加权与方差控制已有。 |
| [Jiang & Li, ICML2016](https://proceedings.mlr.press/v48/jiang16.html) | DR off-policy RL评估。此处audit propensity与policy action propensity不是同一个概率。 |
| [Huang & Jiang, ICML2020](https://proceedings.mlr.press/v119/huang20b.html) | 从IS/DR推导policy-gradient与方差缩减。不能以“DR gradient”本身主张首创。 |
| [Kong & Yang, NeurIPS2022](https://proceedings.neurips.cc/paper/2022/hash/476c289f685e27936aa089e9d53a4213-Abstract-Conference.html) | 在明确函数类和探索条件下的active reward learning与反馈复杂度；本研究不能借用其PAC保证。 |
| [Zrnic & Candès, ICML2024](https://proceedings.mlr.press/v235/zrnic24a.html)；[Li, Zrnic & Candès, NeurIPS2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/6389470564214983604d1ac81631c2c5-Abstract-Conference.html) | Active statistical inference及错误uncertainty造成的采样效率下降、robust active/uniform混合，直接覆盖label-budget设计的基础思想。 |
| [Liu et al., MFPG作者项目](https://xinjie-liu.github.io/mfpg-rl/)；[TMLR论文PDF](https://openreview.net/attachment?id=zAo0L7Dcqt&name=pdf) | 2026 TMLR题名为“A Multi-Fidelity Control Variate Approach for Policy Gradient Estimation”；2025前稿arXiv2503.05696题名不同。已用少量高保真和大量低保真轨迹构造无偏、降方差PG，处理dynamics/reward gap。 |
| [Noise-corrected GRPO, arXiv2510.18924v1](https://arxiv.org/html/2510.18924v1) | 使用query/class-conditional binary flip模型及noise correction；理论主式使用per-prompt population mean/SD，另提供方差plug-in。不能把这些结论直接解释成任意固定有限reward group的normalized update无偏。 |
| [RL with Verifiable yet Noisy Rewards, arXiv2510.00915v1](https://arxiv.org/html/2510.00915v1) | 已讨论imperfect verifier、backward/forward PG correction与GRPO集成。Appendix B明确先对奖励做affine correction再计算组均值/SD；下面给出这一操作的代数边界，不将其全文实证简单否定。 |
| [DeepSeekMath, arXiv2402.03300](https://arxiv.org/abs/2402.03300) | GRPO及组内优势构造的直接来源。这里分析特定数学版本，不能暗称所有当前实现完全相同。 |
| [Rhee & Glynn, Operations Research2015](https://web.stanford.edu/~glynn/papers/2015/RheeG15.html) | 用随机截断的telescoping approximations恢复无偏性及优化随机化已有。有限label-prefix版本只能是该思想的任务化。 |
| [Kaniewski, Lee & de Wolf, Query Complexity in Expectation](https://arxiv.org/abs/1411.7280) | 已研究query-in-expectation与多项式关系；其非负输出模型以nonnegative literal degree刻画。这里允许有符号更新，所以应直接证明ordinary polynomial degree下界，不能误用其更强非负输出结论。 |

这是针对候选的原始文献排查，不是完整系统综述。未找到“有限二元GRPO聚合更新的精确degree公式”不构成首创证明；正式选题仍应检索该具体公式、有限组去偏和partial-label nonlinear estimators。

## 2. 原始逐轨迹方案：正确，但主要属于旧方法

### 2.1 精确目标与假设

固定当前参数θ，轨迹τ来自真实目标环境中的πθ。环境转移机制不直接依赖θ；终止/长度规则被纳入轨迹分布，满足score identity及可交换微分和积分。令

\[
 Z_\theta(\tau)=\nabla_\theta\log p_\theta(\tau)
 =\sum_{t=1}^{T(\tau)}\nabla_\theta\log\pi_\theta(a_t\mid h_t),
 \qquad g(\theta)=E_\theta[Z_\theta R].
\]

R是真实执行/可信oracle定义的奖励，非模型推断的latent truth。廉价信息X、surrogate m(X)、score Z都在审计前可用；允许X包含完整可见轨迹、长度和score。根据过去数据/独立pilot以及当前X确定q(X)>0，随后使用已知的真实随机概率抽I。要求I在给定审计前信息与完整潜在R之后仍为Bernoulli(q)，不能事后根据看到的R拒收label而继续使用旧q。假设相应二阶矩有限。

\[
 \widehat R=m+\frac{I}{q}(R-m),\qquad \widehat Y=Z\widehat R.
\]

条件于τ、R、m和q，E_I[\widehat R]=R，故E[\widehat Y]=g。m可以严重错误；这不是必须奖励模型正确才成立的渐近结论。但m、q必须在当前audit coin之前确定，计算policy gradient时停止通过m、q、audit weights反向传播。对这个有已知随机设计的任务，更准确的名称是augmented inverse-probability/design-unbiased correction，而不是以“两模型之一正确”作为主要贡献。

若以错的\hat q代替真实q，则偏差为

\[
 E\!\left[Z\left(1-\frac q{\hat q}\right)(m-R)\right].
\]

当X包含Z、且m=E[R|X]时该式可为零；若X不含Z，仅有m=E[R|X]不够，还要E[Z(R−m)|X]=0。不要把reward mean正确与gradient estimating equation正确混为一谈。

### 2.2 有限样本方差与成本最优概率

给定N条完整潜在轨迹，记e_i=R_i−m_i，独立Bernoulli audit，则

\[
 \operatorname{Cov}_I(\widehat g\mid\tau_{1:N},R_{1:N})
 =\frac1{N^2}\sum_i\left(\frac1{q_i}-1\right)e_i^2Z_iZ_i^\top.
\]

若轨迹iid，则全方差是

\[
 \operatorname{Cov}(\widehat g)=\frac1N\left\{
 \operatorname{Cov}(ZR)+E\left[\left(\frac1q-1\right)e^2ZZ^\top\right]\right\}.
\]

任意固定方向u有精确二阶矩，Chebyshev界为
Pr(|uᵀ(ĝ−g)|≥t)≤uᵀCov(ĝ)u/t²。固定预算的无放回audit不满足独立Bernoulli方差，应使用joint inclusion q_ij保留交叉项；其HT无偏性不能被误当成同一方差公式。

固定PSD评价矩阵W，定义

\[
 a(x)=E[e^2Z^\top WZ\mid X=x],\qquad c(x)=\text{完整审计的增量成本}.
\]

最小化trace(W Cov)且E[cq]≤b，概率上下界q_min≤q≤1时，标准凸优化给出

\[
 q^*(x)=\operatorname{clip}_{[q_{\min},1]}
 \sqrt{\frac{a(x)}{\lambda c(x)}}.
\]

这就是残差和目标estimating function加权的Neyman式分配，不是新的基础定理。a必须从独立pilot或过去audit估计，不能喂入当前未付费R。Euclidean score norm的“最优”依赖参数化；必须固定W和评价目标。按长度、verifier entropy或reward residual单独分配均不普遍最优。

长轨迹Z是各action score之和。若每步score为martingale difference且二阶矩有界、停止规则合适，E||Z||²按累积步数增长；不能一律声称H²爆炸。残差与Z的相关位置、policy drift以及q_min会改变实际方差。最坏逐样本界与平均二阶矩也不能混写。

### 2.3 反例与失效

- **Accuracy不决定梯度。** Bernoulli action p=.5，真实R恒为0。两个verifier都只在总概率ε的记录上误报1；一个只误报action1，另一个只误报action0。二者accuracy相同1−ε，score-weighted bias分别+ε/2与−ε/2。一个独立可见nuisance变量可以实现这两个固定错误集合。跨policy的离线accuracy更不能控制新policy的梯度方向。
- **同批自适应拟合m可破坏设计无偏。** 单条R=1、q=.5；看完audit后令m=I，即只有已查label的样本被模型记住。代入原公式输出恰为I，期望.5而非1。冻结/独立pilot/cross-fitting是实现条件，不是装饰。
- **动态训练仅有条件无偏。** 在θ_t和audit规则由过去确定、每步重新取当前on-policy轨迹时，误差可形成martingale difference。它不意味着优化后的θ_T或复用样本的训练路径等于oracle训练路径。旧policy轨迹还需独立处理off-policy权重。
- **可选停止的均值不自动无偏。** 两个iid Bernoulli(.5)样本：第一项为0就停止，否则取第二项。最终平均的期望.375，而非.5。对固定n估计量的无偏性不能直接移给随机停止的ratio。
- **纠错label不纠错环境。** 若cheap simulator改变状态转移/观察，E_cheap[Z_cheap R]仍不是E_full[Z_full R]。例如目标环境起点在s1、廉价环境起点在s0，π有独立参数θ_s0、θ_s1，reward为最后action1；cheap audit永远没有θ_s1的score，真实gradient却仅在该坐标非零。完整奖励oracle也无法补回缺失occupancy。需要完整trajectory-contribution correction或transition方法，而MFPG已有直接先例。

## 3. 正确的新目标：指定有限组的oracle更新

冻结rollout group、当前评价参数、token/trajectory权重等所有廉价可见量。将未知真实label向量记作r∈{0,1}^G。审计只揭示这些既定label，不改rollout轨迹或policy。

先研究无active clipping的标量投影（向量逐坐标同理）：

\[
 F(r)=\frac1G\sum_{i=1}^G s_i\frac{r_i-\bar r}{\sigma(r)},\qquad
 \sigma(r)=\sqrt{G^{-1}\sum_i(r_i-\bar r)^2},
\]

allsame时F=0。s_i是冻结的score/梯度方向投影；若包含token平均，长度因子也在s_i里明确固定。**F是finite-group oracle update，不是自动等于∇E[R]。** 即使去掉std，只使用同组均值baseline，iid同prompt条件下平均score×(R−组均值)的期望也为(1−1/G)g；leave-one-out baseline与随机std又是不同对象。

### 3.1 HT奖励之后normalize不无偏

G2、s=(1,−1)、r=(1,0)、m=(0,0)、q=.5。校正奖励为(2I,0)。有audit时F=1，无audit时allsame而F=0；E[F(校正奖励)]=.5，oracle F(r)=1。逐条奖励期望正确不能穿过随机分母。 这与G2的Boolean degree为1不矛盾：线性多项式在真实binary cube上等于F，但HT校正后的连续值通常离开该cube；应估计线性多项式本身，不能再调用非线性标准化。

另一个相关代数事实：对一组奖励做相同正affine变换ar+b，精确组标准化完全不变。因此用相同已知flip rates先做(r_noisy−ρ0)/(1−ρ0−ρ1)、再按同组均值/SD标准化，在分母无epsilon时逐样本与未校正的noisy advantages相同。若加epsilon，只等效改变epsilon的尺度。此事实不能否定flip模型下的线性PG correction；它否定的是未经证明把该结论搬到实际finite-group normalization。

## 4. 二元未clipped GRPO的精确审计深度定理

### 定理

G≥2，s不全相等。对所有r∈{0,1}^G采用上一节F，允许输出有符号实数且有限一阶矩的任意随机、适应性label-query算法。若每条执行路径最多查询b个不同label，则

\[
 E[\widehat F\mid r]=F(r)\quad\text{对所有r成立}
 \quad\Longrightarrow\quad
 b\ge d_G=\begin{cases}G-1,&G\text{偶},\\G-2,&G\text{奇}.\end{cases}
\]

在仅要求存在有限方差估计器、不要求方差大小或非负输出的意义下，这个hard-cap下界可达到。若s全相等则F≡0，degree为0；G1也平凡。

### 证明一：计算唯一multilinear polynomial的degree

令c_i=s_i−s̄，Σ_i c_i=0；k=Σ_i r_i。在0<k<G时

\[
 F(r)=\left(\sum_i c_i r_i\right)f(k),\qquad
 f(k)=\frac1{\sqrt{k(G-k)}}.
\]

记F(r)=Σ_{S⊆[G]}a_S∏_{i∈S}r_i。对S大小ℓ<G，通过Boolean Möbius inversion：

\[
\begin{aligned}
 a_S&=\sum_{T\subseteq S}(-1)^{\ell-|T|}F(1_T)\\
 &=\left(\sum_{i\in S}c_i\right)
 \sum_{j=1}^{\ell}(-1)^{\ell-j}{\ell-1\choose j-1}f(j)\\
 &=\left(\sum_{i\in S}c_i\right)\Delta^{\ell-1}f(1).
\end{aligned}
\]

Full-set系数为0：每个大小j的subset贡献的Σc_i总和等于C(G−1,j−1)Σc_i=0；两端F=0。注意这不是假定full-set函数没有依赖全部labels，而是其特定代数抵消。

令a=G/2、z=x−a，0<x<G，则

\[
 f(x)=\frac1a\left(1-\frac{z^2}{a^2}\right)^{-1/2}
 =\frac1a\sum_{n=0}^{\infty}\frac{{2n\choose n}}{4^n}\frac{z^{2n}}{a^{2n}}.
\]

在内点可逐项求导，所有偶阶导数f^(2j)(x)严格为正（包括n=j的正常数项）。因此区间在(0,G)内的所有偶阶有限差分严格为正，亦可用有限差分的迭代积分表示证明。

- G偶时，ℓ=G−1给出阶G−2的正偶阶差分。由于c非零，取S为去掉一个c_i≠0的单位，Σ_{S}c=−c_i≠0。因此存在非零G−1次项，full-G项为0，degree恰为G−1。
- G奇时，ℓ=G−1对应奇阶差分。采样点1,…,G−1关于G/2对称，f(j)=f(G−j)，奇差分各项两两抵消，故所有G−1次项为0。ℓ=G−2对应正偶阶G−3差分。若所有这种S的c和都为0，则所有互补pair的c_i+c_j都为0；G≥3时这迫使全部c=0，矛盾。因此degree恰为G−2。

所以G=2,3,4,5,6,7,8的degree分别1,1,3,3,5,5,7。sample SD只乘以与r无关的固定G因子，不改变此结论。加入不同的stabilizer、reward裁剪或PPO clipping必须重新分析，不能默默沿用。

### 证明二：适应性query算法也不能绕过

固定算法内部随机种子后，算法是一棵深度至多b的decision tree。每个叶子的可达事件是至多b个literal r_i或(1−r_i)的乘积。输出等于叶子输出常数乘该事件指示之和，所以唯一multilinear representation的degree≤b。对随机种子取期望仍在同一有限维degree≤b线性空间内。因此若F有degree d>b，点态无偏不可能。该论证不要求预先固定查询顺序；重复查询同一确定label无额外信息。

反向构造：从F的有限multilinear expansion随机选一个非零单项式S（概率p_S>0），查询S中全部label，输出a_S∏r_i/p_S，并处理常数项。期望为F且最多d次查询。这是存在性，不是实用低方差建议；系数抵消和稀有单项式可能使方差极大。

### 解释限制

1. 下界是worst-case硬cap，不是期望查询数下界；可用很小概率做较多查询换取更大权重/方差。
2. 标签域必须在固定廉价信息下仍允许所有cube配置。若有可信逻辑约束/已知noise model，则可识别集合更小，下界需重做；verifier的高accuracy本身不是这种约束。
3. 二元时full G查询并非总是必要，不能写“每个无偏算法必须查询全部组”；精确硬cap是d_G≈G。
4. 定理针对冻结s的聚合未clipped F，不是每个advantage正负部分，也不是真实优化轨迹的总体最优性。

## 5. 有限randomized telescoping：可行但必须承认既有基础

在固定廉价信息下选一条完整的label揭示顺序；可以预先按可信成本/模型信息排序，也可让下一单位依已揭示label选择，但不能偷看未来label。定义完整执行时的递增信息σ-field H_k、任意可计算completion F_k，且F_G=F(r)。最简单F_k是把已审位置换成真label、其余填surrogate；更稳定的模型completion见下一节。令D_k=F_k−F_{k−1}。

在查询k之前，以仅依H_{k−1}的概率q_k∈(0,1]继续；如果停止则不再查询。沿完整潜在路径的存活概率为Q_k=∏_{j≤k}q_j，实际到达指标C_k。估计器为

\[
 \widehat F=F_0+\sum_{k=1}^G\frac{C_k}{Q_k}D_k.
\]

对固定r及完整潜在随机顺序，每个E[C_k/Q_k|r]=1，所以有限和telescoping恰得E[\widehat F|r]=F(r)。顺序与continuation依已见label不会破坏这个结论；用停止后重新估出的边际概率替换实际沿路径Q_k则可能破坏。每个被审计label必须在查询前记录相应q_k/Q_k。

硬性在b<G处截断使Q_{b+1}=0，除非剩余总增量被一个另有无偏性的终端估计补回，否则只估F_b；不能一边设置死上限一边保留endpoint无偏宣称。允许偶尔查完整组是一种最简单可行设计，不能从期望成本小推断每组都便宜。

对于固定r、deterministic survival，条件方差的正确形式为

\[
 \operatorname{Var}(\widehat F\mid r)
 =\sum_j(Q_j^{-1}-1)D_j^2
 +2\sum_{j<k}(Q_j^{-1}-1)D_jD_k.
\]

向量形式用外积/内积。交叉项一般不为零；只有特定martingale completion在相应正确模型平均后才可消去。正概率保证无偏，不保证可接受方差；逐步q≥ρ仍可让Q_G≥ρ^G非常小。最好直接约束absolute survival的下界或重尾成本，并报告权重极值、方差和成本分位数。

必须比较的简单基线是**整组HT**：F(m)+I_group/q_group [F(r)−F(m)]。它天然纠正完整非线性函数，在期望budget b下可取q_group=b/G（等成本时）；RR若不能超过这个强且简单的基线，就没有充分方法效益。逐条HT再normalize应作为错误/有偏对照，而不是唯一竞争者。

## 6. Posterior completion、正交增量与静态最优survival

冻结一个由独立pilot/过去数据训练的联合预测分布P_m(r|X)。定义

\[
 F_k=E_m[\Phi(r)\mid H_k],\quad F_0=E_m[\Phi(r)\mid X],\quad F_G=\Phi(r).
\]

Φ可以是F、完整advantage向量，或下一节的正负advantages。**即使P_m错误，有限endpoint telescoping的点态无偏仍成立**。模型正确时，F_k是Doob martingale，E_m[D_k|H_{k−1}]=0，增量正交。令W固定PSD。

若query顺序、每步成本c_k和survival Q_k都在组开始前确定，则在P_m下

\[
 \operatorname{tr}W\operatorname{Cov}_m(\widehat\Phi)
 =\sum_{k=1}^G\frac{a_k}{Q_k},\quad
 a_k=E_m[D_k^\top W D_k],\qquad
 E[\text{cost}]=\sum_k c_kQ_k.
\]

oracle Φ本身的方差为Σa_k；新增audit方差是Σa_k(1/Q_k−1)。这里condition于固定X，F0非随机。predictable adaptive Q_k时仍可写ΣE_m[D_kᵀWD_k/Q_k]，但优化是分支树约束问题，不能直接使用以下一维PAVA。

固定链情况下，求解

\[
 \min_{1\ge Q_1\ge\cdots\ge Q_G>0}\sum_k a_k/Q_k,
 \quad \sum_k c_kQ_k\le b.
\]

对拉格朗日乘子λ，未考虑单调性的解是√(a_k/(λc_k))。若相邻块违反Q非增约束，合并它们：每块的共同解

\[
 Q_{\mathcal B}=\min\left\{1,
 \sqrt{\frac{\sum_{k\in\mathcal B}a_k}{\lambda\sum_{k\in\mathcal B}c_k}}\right\}.
\]

按块ratio Σa/Σc的非增性做PAVA，再以一维求根令预算匹配；这是该固定设计凸问题的解。允许positive floor时加入clip与可行预算。若模型认为a_k=0，不能因此把Q_k置零而继续声称对任意真实r无偏；需要保留positive survival，除非有确定性代数证明剩余增量为零。

模型错误会使martingale正交和上述最优性失效。应报告错误p、错误跨label依赖以及policy drift的敏感性，并用实际独立audit检验方差；不能仅报告模型预测variance。若按已审label自适应选顺序或Q，使用动态规划/树上凸问题做oracle比较，不能冒称静态PAVA为adaptive最优。

### 6.1 Completion计算可先枚举，再利用结构

G≤8/16时可直接枚举2^G个二元reward配置，对所有可能observed prefix精确求条件均值，无需模型采样。若P_m假设独立Bernoulli(p_i)，可以用Poisson-binomial DP提高效率：组优势只依各r_i及总成功数K。

\[
 A_i^+=1\{r_i=1,0<K<G\}\sqrt{(G-K)/K},\quad
 A_i^-=-1\{r_i=0,0<K<G\}\sqrt{K/(G-K)}.
\]

计算已查成功数加未查Bernoulli之和的分布，再对每个i使用包含/排除它的计数分布即可得到E_m[A_i^±|H_k]。端点K=0/G定义0。小组先用全枚举验证DP，不能只因代码更快就省掉核对。模型真实标签相关时，independent-Bernoulli只是completion工作模型；点态无偏不变，模型最优方差保证撤回。

## 7. PPO clipping需要纠正非线性函数本身

即使A估计无偏，也不能直接代入

\[
 \ell(\rho,A)=\min\{\rho A,\operatorname{clip}(\rho)A\}.
\]

例如真实A=0，无偏随机估计\widehat A取±1各一半，ρ=2、upper clip=1.2。oracle objective为0，E[ℓ(ρ,Â)]=.5(1.2−2)=−.4。

正确分解是A+=max(A,0)、A−=min(A,0)，以及冻结参数下的已知系数

\[
 \ell(\rho,A)=\min\{\rho,\operatorname{clip}(\rho)\}A^+
 +\max\{\rho,\operatorname{clip}(\rho)\}A^-.
\]

对Φ=(A_1+,A_1−,…,A_G+,A_G−)做completion/RR，得到两部分的无偏估计，再线性组合。固定θ处对ρ系数微分，得到同一oracle clipped surrogate的pointwise无偏梯度；kink使用一致的预定subgradient convention。KL等不依隐藏label的项直接保留。

**不要对RR输出再次clamp正负号或重新normalize。** 无偏Φ估计可以超出其原始取值范围；这属于随机加权估计，不是需要修成合法label的预测。

另外，上一节未clipped F的degree不直接适用于Φ：G2时A1+=r1(1−r2)已有degree2，而未clipped聚合F只有degree1。真实active clipping可改变最高交互阶，需另算；不能声称G2/3的clipped update一label就足够。

固定audit结果可作为随机surrogate函数用于多个θ的pointwise评估，但若θ是根据该同一随机函数优化选出的，E[误差(θ)]一般不再为零。方法不保证multi-epoch更新路径或最终policy无偏；要么每次更新用新audit，要么明确只比较固定batch objective/gradient估计，并另做优化效果实验。

## 8. 最小可落地环境及实验判据

建议先把finite-group审计层与长轨迹环境层分开核验，再组合，避免用复杂agent遮盖估计错误。

**层A：不训练的精确group实验。** 固定G∈{2,3,4,5,8,16}、可见scores/长度/cheap概率；枚举全部r。核对每种audit设计的点态bias、完整方差、expected/maximum/95th-percentile cost；比较oracle、cheap-only、逐条HT后normalize、整组HT、固定survival RR、completion RR、正确/错误模型下PAVA。包含不利结果和整组HT更好的设置。增加active clipping的固定ρ测试，分别报告oracle grouped update和true-reward PG。

**层B：精确DP的长任务。** 有限stage状态(t,z)，z∈{clean, compromised}是持续依赖是否已破坏；每步action为safe/shortcut，shortcut在某些branch以已知概率使z变坏，之后持续。终态真实成功取决于z及明确的最终task条件；cheap终态检查可忽略部分依赖或只查最后artifact。转移/奖励/cheap verifier全在配置中冻结，不从待报告结果反调。

状态数O(H)，动作数2，可反向DP得到真实V_t(z)、∇V、π诱导终态分布、不同cheap误差的score关联，H可扩到数百。可用一个或两个shared logistic参数让score可精确计算，并用forward DP记录所需count统计；做finite-difference核对梯度。组内多个独立rollout得到G个固定binary labels，额外full checker只揭示这些既定轨迹的真实执行结果，**不改rollout observations/动作**。若cheap与full运行会改变后续action轨迹，就属于另一environment-gap问题，应停止沿用reward-label theorem。

**层C：真实可执行长任务。** 寻找cheap final-state check与expensive full dependency check针对同一生成产物的环境，例如多步生成的程序/工作流及完整测试；记录真实wall-clock/执行调用数，而非仅人为设定“oracle cost=H”。先在固定checkpoint产生的轨迹组上离线估计oracle update，再进行少量可复现训练。参数规模不是必要条件，但至少一个真实执行成本场景会比纯toy更能说明environment scaling的意义。

最小主问题建议命名为“partial validation of finite-group policy updates”，将long horizon作为成本/score相关性的可测试轴，而非声称下面的query-degree定理依赖H。G控制非线性耦合的审计障碍，H影响每次真实label成本与score/residual分布；这是两个不同的复杂度轴。

### 不能预先承诺的结论

- 没有一般的“长轨迹越长，RR越有优势”；极少审计可导致高variance和优化不稳定。
- 没有一般的“completion比整组HT更好”；prefix查询可能付出成本却没有目标信息，尤其标签强相关/概率模型错误时。
- 没有一般的“纠正oracle GRPO更新就优化真实success最快”；oracle GRPO本身含std/length/clip相关目标差异。
- 不能把模型完备性、可信oracle或独立label当成已从现实agent数据识别的事实。

## 9. 本地已执行的数值检查

复现：在包含NumPy/SciPy的环境中运行 `python experiments/verify_theory_feasibility.py`。检查文件只写 `results/theory_feasibility_checks.json`，没有训练RL模型。

- G2–12全Boolean cube的Möbius系数与解析公式逐项相符，最高误差2.21e-14；degree序列1,1,3,3,5,5,7,7,9,9,11。
- G5全部32种固定真实reward vector，已见label驱动的adaptive continuation，RR点态均值最大误差5.56e-17；无须这些r服从completion模型。
- 正确Bernoulli completion模型下，精确枚举variance为0.19339599534935392，Σincrement variance/Q为0.19339599534935390；off-diagonal增量协方差最大2.15e-18。
- 20组静态survival优化，PAVA与独立SLSQP约束优化目标最大差2.08e-11，预算和非增约束均通过。
- 逐条HT后normalize反例：oracle1、期望.5；无偏advantage后clip反例：oracle0、期望−.4；共同positive affine correction后的标准化差为0。

这些是小规模精确代数/枚举证据，不能当作现实training收益。所有文件保留seed、源码SHA和计算时间；正式实验还要另冻protocol、成本定义及不能用于policy的oracle字段。

## 10. 首轮实验后提出的免真实label调参方案：精确model moment lemma

本节在查看首轮controlled study的校准费用问题后提出，因此属于后续探索设计；不能追溯称作首轮预先方案。它免除的是当前调度方案的真实label校准费，不免除预测、模型训练来源或completion/scheduling计算成本。

### Lemma：以prefix成功数压缩model coefficient moments

固定组内顺序，r_i独立服从Bernoulli(p_i)。Φ(r)是分块排列的(A_1+,…,A_G+,A_1−,…,A_G−)，使用population group SD且allsame为0。H_k观察前k个真实label，μ_k=E_m[Φ|H_k]。定义

\[
 M_k=E_m\|\mu_k\|_2^2,\quad v_k=E_m\|\mu_k-\mu_{k-1}\|_2^2=M_k-M_{k-1}\ge0.
\]

令S_k=Σ_{i≤k}r_i，U={k+1,…,G}，K_U=Σ_{i∈U}r_i，设

\[
 a(j)=\sqrt{(G-j)/j},\qquad b(j)=-\sqrt{j/(G-j)}
 \quad(0<j<G),
\]

并在j=0,G定义a(j)=b(j)=0。已查正例的conditional正优势为a_s=E_m[a(s+K_U)]，已查负例的conditional负优势为b_s=E_m[b(s+K_U)]。未查单位i∈U的两分量为

\[
 \alpha_i(s)=p_i E_m[a(s+1+K_{U\setminus i})],\qquad
 \beta_i(s)=(1-p_i) E_m[b(s+K_{U\setminus i})].
\]

则有精确公式

\[
 \boxed{M_k=\sum_{s=0}^k\Pr_m(S_k=s)
 \left\{s a_s^2+(k-s)b_s^2+
 \sum_{i\in U}[\alpha_i(s)^2+\beta_i(s)^2]\right\}.}
\]

**证明。** 给定任一observed prefix pattern，未查labels仍独立且分布只由各p_i决定。每个已查正例有相同a_s，每个已查负例有相同b_s；平方Euclidean范数不依赖正负已知label具体出现在哪个已查位置，只依赖其数量s。对未知i再条件于r_i=1或0得到上式两分量。最后对prefix count的Poisson-binomial分布平均。第二矩差等于增量平方均值来自conditional expectation的Hilbert-space投影/Doob martingale恒等式，不需要额外RL假设。证毕。

边界检查为

\[
 M_0=\|E_m\Phi\|^2,\qquad
 M_G=E_m\|\Phi\|^2
 =G\left[1-\prod_i p_i-\prod_i(1-p_i)\right].
\]

最后一个等式利用每个mixed binary group的normalized advantage平方和恰为G，allsame组为0。正确实现中M_k应非减；微小浮点负增量只能按明确数值容差处理，不能将显著负值静默截零。

### 计算与“最优”范围

每个k的prefix/suffix和leave-one-out count PMF可由多项式卷积得到。缓存不依s的PMF，再计算所有s和i的有限和，朴素实现可做到O(G^4)总工作量；不能在每个s内重新构建所有PMF而仍声称该复杂度。小G直接枚举2^G全部配置核对每个M_k，是独立验证的可靠方式。

得到v_k后可按第6节的PAVA选择固定survival，优化**该独立Bernoulli模型下、固定顺序的coefficient Euclidean MSE**。这不是实际错误模型下的最优，也不是random score projection或clipped-policy gradient的最优。若换成加权/相关的gradient范数，已查label位置会与其权重发生关系，仅按s压缩一般不够，需更多conditional sufficient statistics。

此方案不读取当前或校准组的真实labels；其输入只应包含当前cheap probabilities、排序规则、已知成本和预算。label-free scheduling不会解决错误p或跨label依赖，也没有消除model CPU overhead。新的结果应分别报告：(i)相同评价label预算，(ii)包括已付费校准、predictor来源与实际scheduler计算的总成本。

本节独立数值验证已执行：`experiments/verify_model_completion_lemma.py`不导入主实现，直接对全部label patterns条件分组积分，核对G2–8及G16。G16的65,536配置上，各prefix M_k与count压缩公式最大差4.45e−14；所有v_k非负且M_G端点闭式一致。结果存于`results/model_completion_lemma_checks.json`。

## 11. 与 clipped surrogate 直接衔接：sign-split vector 的精确查询次数门槛

**定理。** 对 G≥2、二元标签、population SD、epsilon=0，allsame 组优势设零。Φ=(A^+,A^−) 的每一个标量分量的 Boolean multilinear degree 都是 G（G 偶）或 G−1（G 奇）。因此一个对每个固定标签向量都无偏估计完整 Φ 的算法，在没有标签生成模型限制时，不能在每次运行硬性最多只查询 b<d 个真实标签；即使查询顺序依赖已见标签和随机数，也不能绕开此门槛。这是对 vector target 的结论，一般 scalar clipped objective 的特定权重可能发生额外抵消，不应给它不加条件地套用同一精确 degree。

**证明。** 固定 i，令 K=Σ_j r_j。A_i^+=r_i a(K)，其中 a(k)=sqrt((G−k)/k) 对 1≤k<G，且 a(G)=0。定义 f(x)=1/sqrt(x(G−x))，x∈(0,G)。不包含 i 的非空 monomial 系数为0，包含 i、大小为 l 的集合系数为 Δ^{l−1}a(1)。全 G 维系数按有限和直接改写为

\[
 c_{[G]}=\sum_{k=1}^{G-1}(-1)^{G-k}{G-1\choose k-1}(G-k)f(k)
 =-(G-1)\Delta^{G-2}f(1).
\]

这里用到 {G−1 choose k−1}(G−k)=(G−1){G−2 choose k−1}，求和不含奇异的端点 f(G)。f 关于 G/2 对称；其偶数阶导数在 (0,G) 严格为正。后一事实可从 f(G/2+t)=(2/G)(1−(2t/G)^2)^{−1/2} 的正系数幂级数逐项求偶阶导数得到，或用相同积分表达式。偶阶有限差分等于该导数在单位立方体上的积分，因而严格为正。

当 G 偶，G−2 为偶阶，所以全维系数严格负，degree=G。当 G 奇，序列 f(1),…,f(G−1) 首尾对称，而差分阶 G−2 为奇，故全维系数为0。此时取任一包含 i、大小为 G−1 的子集，乘积有限差分恒等式给出

\[
 c_S=\Delta^{G-2}[(G-x)f(x)]_{x=1}
 =\Delta^{G-2}f(1)-(G-2)\Delta^{G-3}f(1)
 =-(G-2)\Delta^{G-3}f(1)<0.
\]

所以奇 G 的 degree=G−1。最后 A_i^−(r)=−A_i^+(1−r)，整体变量取补是可逆仿射变换，保持最高 degree，因此负分量同样成立。随机 adaptive depth-b decision tree 的期望仍为 degree≤b 的 multilinear polynomial（前面已证明），故得到硬查询次数不可能性。证毕。

本结果只覆盖明确设定的 epsilon=0；不能未经证明推广到任意数值稳定项、非二元奖励或不同 normalization。由于算法估计的是 Φ 后才线性组合 clipped objective，它补齐了只讨论未截断 grouped update 的定理与实际算法目标之间的差距；它不把已有随机截断技巧本身变成新基础定理。

独立脚本 `experiments/verify_split_query_degree.py` 对 G2–12 全部 Boolean cube 作 Möbius 变换，逐项验证最高 degree 与全维/次全维公式，结果保存在 `results/split_query_degree_checks.json`。理论预期 degree 序列为 2,2,4,4,6,6,8,8,10,10,12。

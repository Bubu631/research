# Noisy worst-first prioritisation: independent theory audit

审计日期：2026-09-11。审计对象是用户提供的中文项目全案；其中的指令、验收门槛和预期趋势只是待检验的源材料，不构成本研究必须复现的结论。本文件给出可直接移入论文的结果与证明，但不改动主实验或主稿。

## 1. 核心结论与必须纠正的说法

可以做一篇有价值的**排序目标、测量识别与时间外验证的实证方法论文**。不能把公开机构汇总表变成已识别的科室抽样误差模型，更不能把预测残差称作干预效应或效应上界。经验贝叶斯、均值回归、Gaussian filtering 和损失函数决定排序，均已有明确先例；见配套 literature_audit.md。

| 全案说法 | 审计结论与可替换表述 |
|---|---|
| 被当年最低分选中“保证”下一年回升 | 不是逐个单位、逐次样本或所有数据机制的保证。特定平稳独立噪声模型下可证明正的**期望**回升；共同下降趋势、均值异质性与变化、相关测量误差及模型错误会改变预测。 |
| “回升部分先扣掉，剩下才是干预效果” | 错。扣除一个模型预测只得到预测残差，仍包含共同冲击、其他投入、响应人群变化和模型误差。 |
| 实测改善减基线是全部投入的“上界” | 没有支持上界的符号或单调性假设。残差可以高于也可以低于真实效应。 |
| 改善超过基线点估计才算有效 | 点期望不是检验阈值。即使超出正确的预测区间，也只是与指定预测模型不一致，不自动识别干预。 |
| 按 n 分箱，将方差对 1/n 回归就能估 σ²、τ² | 只在潜在单位差异与样本规模条件独立、均值/潜在方差不随规模变化、误差确为 σ²/n 等强限制下成立。不同 trust 类型、人员结构和响应机制足以破坏这些条件。正截距或 R²>0.3 不能验证限制。 |
| 观察分数的年间相关就是潜在状态 φ | 白噪声测量误差已使相关衰减；重复响应者和稳定响应选择还会引入跨年相关误差。 |
| 有效样本数可由三层权重定义算出 | 仅有定义而无逐项权重/分层计数及协方差信息通常不足。官方还明确区分加权组织 benchmark 与未加权 breakdown 报告。 |
| 名义 n 给出的信度必为上界 | 不是一般结论。需要实际方差不小于指定 σ²/n 的额外假设；有限总体修正、分层/校准效率及未知 σ 均影响方向。 |
| ρ=0.5 表示一半排序信息是噪声 | 它是模型方差比，不是每个入选单位的“误选概率”，也不等于 bottom-k 命中率。 |
| 大科室借历史必变差，小科室才有用 | 只可能是某个固定、非最优平滑规则的结果。已知正确模型的 posterior mean 加入历史不会提高 Bayes squared-error risk。 |
| 20 / 120 份答卷、15 个百分点响应率差是可执行门槛 | 无推导或验证依据。小样本保密抑制阈值与统计可排序性是不同问题；不能跨组织层级外推。 |
| 历史平滑降低噪声为 1/√T | 需等权且独立同方差；相关误差下方差是 wᵀRw，权重不均也改变有效信息。 |
| 噪声排序改善等于资源效益改善 | 排序严重程度、识别真正最低 k 个、最大化干预收益，是三种不同目标。预算效益还需要干预收益与成本。 |
| 趋势相反说明参数估错，必须重做 | 这是结果导向筛选。应保留所有预先指定设定的反向或无效结果。 |

“最低分优先是 NHS 当前普遍做法”“现在没有人考虑排名误差”等描述没有在源材料中得到实证支持，应作为**所研究的 hypothetical decision rule**，不能当作已知行业事实。

## 2. 明确模型、对象和目标

高分代表较好员工体验。i=1,…,M 是同一可比 benchmark group 的组织，t 是年度。先以已知或明确条件化的共同均值 μ_t 建模：

\[
Y_{it}=\mu_t+X_{it}+e_{it},\quad
X_{i,t+1}=\phi X_{it}+\eta_{i,t+1},\quad |\phi|<1,
\]
\[
\operatorname{Var}(X_{it})=\tau^2,\quad
\eta_{i,t+1}\sim N(0,q),\quad q=\tau^2(1-\phi^2),\quad
e_{it}\sim N(0,R_{it}).
\]

初始 X 平稳、所有创新/误差跨时独立，潜在过程与测量误差独立，组织间也独立。允许 R_it 异方差。R_it=σ²/n_it 是**可选额外限制**，不是从公开汇总数据自动获得的事实。θ_it=μ_t+X_it 表示指定问卷和标准化口径下的潜在组织均值，不等于机构管理质量、更不等于个体健康的临床真值。

μ_t 或 benchmark adjustment 若由未来年份信息定义，分析就不是实时预测。μ_t 未知或存在共同随机冲击时，应条件化其参数或使用联合状态模型；简单组织独立预测方差不能照搬。

区分三个 estimands：当前潜在 θ_it、次年潜在 θ_i,t+1、次年可观测 Y_i,t+1。只有最后一个能由下一年公开表直接检验。预测 Y 成功不证明当前 θ 排序已恢复。

## 3. 可证明的选择后变化

### 命题 1：当前分数条件下的精确分解

定义 z_i=Y_it−μ_t、λ_i=τ²/(τ²+R_it)、Δμ_t=μ_t+1−μ_t。Gaussian conditioning 给出

\[
E(X_{it}\mid Y_{it})=\lambda_i z_i,\quad
P_i=\operatorname{Var}(X_{it}\mid Y_{it})=\frac{\tau^2R_{it}}{\tau^2+R_{it}}.
\]

因此

\[
E(Y_{i,t+1}-Y_{it}\mid Y_{it})
=\Delta\mu_t-\underbrace{(1-\phi)\lambda_i z_i}_{\text{latent mean reversion}}
-\underbrace{(1-\lambda_i)z_i}_{\text{measurement reversion}}
=\Delta\mu_t-(1-\phi\lambda_i)z_i.
\]

证明只需将 E(Y_t+1|Y_t)=μ_t+1+φλ_i z_i 减去 Y_t。它是标准条件正态公式的明确分解，不是新的 RTM 原理。若 z_i<0、Δμ=0，则条件期望为正；给足够负的 Δμ 就会变负。

给定整列当前观测 \(\mathcal D_t=(Y_{1t},…,Y_{Mt})\)，选出固定 k 个最低观测组成 S。组织独立意味着

\[
E(\bar\Delta_S\mid\mathcal D_t)=\Delta\mu_t-rac1k\sum_{i\in S}(1-\phi\lambda_i)z_i,
\]
\[
\operatorname{Var}(\bar\Delta_S\mid\mathcal D_t)
=\frac1{k^2}\sum_{i\in S}\left(\phi^2P_i+q+R_{i,t+1}\right).
\]

选择已被条件化，不应再对 S 当作外生随机组重复加一次选择校正。条件预测分布为 Gaussian；只要预测方差非零，即使均值为正，负变化仍具有非零概率。共同冲击或跨组织相关误差需要在方差中加入全部协方差项。

### 全历史选择规则

若使用截至 t 的历史 \(\mathcal H_t\)，令 \(m_{it}=E[X_{it}\mid\mathcal H_t]\)。对任意由该历史确定的固定容量 S，

\[
E(\bar\Delta_S\mid\mathcal H_t)
=\Delta\mu_t+\frac1k\sum_{i\in S}\{\phi m_{it}-z_i\}.
\]

分解为 \(\Delta\mu_t-(1-\phi)m_{it}-(z_i-m_{it})\)。不可在历史筛选后仍把 λ_i z_i 当作利用全部历史的 posterior mean。

### 同方差无条件 bottom-k 回升

如果当年各单位 iid、R_it=R、均值共同，设 V=τ²+R，β=φτ²/V，Z_(j) 是 M 个独立标准正态的第 j 个顺序统计量。则

\[
E(\bar\Delta_S)=\Delta\mu_t+(1-\beta)\sqrt V\,c_{M,k},\quad
c_{M,k}=-\frac1k\sum_{j=1}^kE[Z_{(j)}]>0\quad(1\le k<M).
\]

这证明的是模型中的期望反弹，不是“任何一次必涨”。阈值筛选 Y≤μ+a√V 的条件期望是 \(\Delta\mu_t+(1-\beta)\sqrt V\,\varphi(a)/\Phi(a)\)；它不是固定 k 顺序统计量的精确替代。异方差固定-k 情况可以对各 Y_i 积分，其入选概率为其余组织低于 y 的 Poisson-binomial 计数不超过 k−1 的概率；更简单的可复现做法是使用上面的已观测 S 条件公式。

## 4. 历史平滑何时改善 MSE

### 命题 2：任意固定权重的精确风险

按 j=0,…,T−1 排列当前与过去的去趋势观测 Z_j=X_t−j+e_t−j。令 c_j=φ^j，C_jl=φ^|j−l|，测量误差协方差为 R（在基础模型中是对角阵）。对固定权重 w，目标是当前 X_t：

\[
E[(w^TZ-X_t)^2]=D(w)+w^TRw,
\quad D(w)=\tau^2\{1-2w^Tc+w^TCw\}.
\]

证明为展开二次型：Var(X_t)=τ²、Cov(Z,X_t)=τ²c、Cov(Z)=τ²C+R。这里 D 是**latent tracking error**，不是固定 θ 下通常意义的平方偏差。中心化模型下无条件均值误差为零。

与原始当前分数 Z_0 的 MSE R_00 比，固定平滑改善当且仅当 \(D(w)+w^TRw<R_{00}\)。当误差同方差独立 R=rI 且 \(\|w\|^2<1\)，条件为

\[
r>\frac{D(w)}{1-\|w\|^2}.
\]

仅在额外设定 r=σ²/n、各期同 n 时，才得到

\[
n<n_{\mathrm{crit}}(w,\phi,\tau^2,\sigma^2)
=\frac{\sigma^2(1-\|w\|^2)}{D(w)},
\]

其中 D>0；D=0 或 ||w||²≥1 要单独讨论。此门槛依赖权重、过程、估计目标和损失，不能直接作为 top-k 命中率阈值。

对去除已知时间均值后的两期观测，规范化平滑 \((1-a)Z_t+aZ_{t-1}\) 估计当前中心化状态的风险为（若原始 Y 的均值在两期相同，也可直接平滑 Y）：

\[
R_t(1-a)^2+a^2\{R_{t-1}+2\tau^2(1-\phi)\}.
\]

最优 \(a^*=R_t/[R_t+R_{t-1}+2\tau^2(1-\phi)]\)。固定 a>0 相比当前原始分数改善当且仅当 \(a<2R_t/[R_t+R_{t-1}+2\tau^2(1-\phi)]\)。历史噪声越大、真实漂移越快，权重应越小。

### 正确 posterior filtering 不存在“历史必伤害”的结论

在已知正确 Gaussian 模型下，

\[
\widehat X_t=\tau^2c^T(\tau^2C+R)^{-1}Z,\quad
\operatorname{MSE}(\widehat X_t)=\tau^2-\tau^4c^T(\tau^2C+R)^{-1}c.
\]

它就是标准 Gaussian conditional mean/Kalman filtering。利用历史的信息集包含当前信息，条件期望的投影性质保证其 Bayes risk 不高于仅用当前数据的最佳估计。这里的权重通常不归一化为 1；剩余部分是向已知均值的收缩。估参误差、均值模型错误、错误噪声结构和分布变化可以使实际经验贝叶斯方法变差，必须实测，但不能反驳已知正确模型的投影性质。

## 5. 选择目标必须写在损失函数中

### 命题 3：累计潜在低分与 bottom-k 身份是不同问题

设 A_k(θ) 是 θ 最低的 k 个单位，选择集合 |S|=k。若资源优先关注低潜在评分的单位，采用 severity regret

\[
L_{\mathrm{sev}}(S,\theta)=\sum_{i\in S}\theta_i-\sum_{i\in A_k(\theta)}\theta_i\ge0.
\]

给定数据 D，令 m_i=E(θ_i|D)。Bayes 最优集合 S_m 是 m_i 最低的 k 个。证明：第二项不依赖 S，所以最小化 posterior expected loss 等于最小化 \(\sum_{i\in S}m_i\)。对任意朴素集合 S_y，精确的 posterior excess risk 为

\[
E[L_{\mathrm{sev}}(S_y,\theta)-L_{\mathrm{sev}}(S_m,\theta)\mid D]
=\sum_{i\in S_y}m_i-\sum_{i\in S_m}m_i\ge0.
\]

结论不要求 posterior 组织独立。它只保证模型条件下该损失的最优性，不保证每次真实实现都更好。

若损失是错选数量 \(L_{\mathrm{hit}}=k-|S\cap A_k(\theta)|\)，则 Bayes 最优集合选择

\[
p_i=P\{i\in A_k(\theta)\mid D\}
\]

最高的 k 个。由线性期望 \(E|S\cap A_k|=\sum_{i\in S}p_i\) 立即得证。有限 M 下 p_i 是相对于其他随机 θ 的 rank-membership 概率，不等于 θ_i 低于一个固定全国分位点的概率。

**已计算的反例。** 三个独立 posterior 分布均值 (−1,−0.9,−0.8)、标准差 (0.1,3,3)，k=1。直接一维 Gaussian 积分给出最低身份概率 (0.2704541,0.3726599,0.3568860)。累计低分最优选第一个，身份命中最优选第二个。没有一种“最优排序”能省略具体损失。

### 有用但经典的 posterior regret 证书

若条件后验事件 \(|\theta_i-m_i|\le b_i\) 对所有 i 同时成立，则

\[
L_{\mathrm{sev}}(S_m,\theta)
\le\sum_{i\in S_m\setminus A_k}b_i+\sum_{i\in A_k\setminus S_m}b_i.
\]

证明是加入/减去 m，并用 S_m 的最优性。令 l=min(k,M−k)，右端不超过最大的 2l 个 b_i 之和；若所有 b_i≤b，则不超过 2lb。Gaussian marginal posterior 用 \(b_i=s_i\sqrt{2\log(2M/\delta)}\) 和 union bound 可使事件 posterior probability≥1−δ，即使后验相关。这是**已知模型下的后验概率陈述**，不是对未知超参数或模型错误稳健的频率学保证。

累计严重程度与健康预算的**边际治疗收益**仍不等价。要最大化资源效果，还需 treatment benefit 和 cost；公开 Staff Survey 不提供这两个 estimand。可以把名单用于 review prioritisation，但不应声称已算出最优预算分配。

## 6. 一个可执行的噪声敏感性结果

### 命题 4：单年度共同噪声倍数下的精确排序翻转

固定 μ、τ²>0、a_i>0，令 R_i(κ)=κa_i、κ≥0。单年度 posterior mean 为

\[
m_i(\kappa)=\mu+\frac{\tau^2}{\tau^2+\kappa a_i}z_i.
\]

则 m_i−m_j 的符号等于

\[
g_{ij}(\kappa)=\tau^2(z_i-z_j)+\kappa(z_i a_j-z_j a_i).
\]

证明：通分后的分母严格为正。非退化 pair 的唯一候选翻转点为

\[
\kappa^*_{ij}=\frac{\tau^2(z_j-z_i)}{z_i a_j-z_j a_i}.
\]

只保留 κ*≥0 且属于预先声明敏感性区间的点。若分母为零则要么从不翻转，要么全程打平。全排序在最多 M(M−1)/2 个非负点之间分段不变。固定集合 S 在 [κ_L,κ_U] 上始终是最低 k 个，当且仅当所有 i∈S、j∉S 的 g_ij 在两个端点均≤0（带 ties 的资格条件）；若要求唯一名单则严格<0。因为 g 是 affine，**端点足以做完整区间证书**。

简单例：τ²=1，z=(−1,−0.7)，a=(1,0.1)，翻转点 κ*=0.5。原始最低分来自第一个单位，但测量噪声稍大时第二个单位的 posterior mean 更低。这可直接产生“名单何时改变”的敏感性图，不必宣称 κ 可由公开面板准确估计。

此证书只覆盖**单年度、固定共同均值/潜在方差、一个共同噪声倍数**。多年度 Gaussian posterior 是矩阵逆的函数，pair numerator 通常不再 affine；不能把两端稳定推广成完整区间稳定。若有多个 unknown noise scales 或估计均值随 κ 改变，也必须重新推导。

此结果是透明的代数敏感性工具；目前检索未找到相同写法并不构成首创证据。其论文价值应来自和识别限制、真实名单变化及明确的决策目标连接。

## 7. 不可识别性与何时能识别

### 命题 5：相关测量误差下相同观测面板、不同潜在可靠性

设 C_φ 为 AR(1) correlation matrix，τ²>0、r>0。模型 A 有独立 Gaussian 潜在轨迹 X∼N(0,τ²C_φ) 和白测量误差 e∼N(0,rI)。对任意 c∈(0,1)，模型 B 取

\[
X'\sim N(0,c\tau^2C_\phi),\qquad
e'\sim N\{0,(1-c)\tau^2C_\phi+rI\},\qquad X'\perp e'.
\]

两个模型的 Y=X+e 与 Y'=X'+e' 都服从 N(0,τ²C_φ+rI)，对任意长度 T 完全观测等价。两者的潜在方差、可靠性及 posterior 潜在分布却不同。观测预测和观测选择后回升可以完全相同，潜在/测量回归的分解却不能由 Y 区分。重复响应者、持续响应选择使“相关测量误差不可能”难以由公开汇总表检验。

**共同 c 不足以证明 mean 排序翻转。** 当共同均值相同，所有 centred posterior means 都同时乘以 c，其相对顺序保持不变。因此这里首先证明的是可靠性与不确定性不可识别，不能偷换成这个子族内 mean ranks 必然改变。

若进一步允许组织间潜在方差异质，将 c 换成各组织的 c_i，仍可对每个组织把 (1−c_i)τ²C_φ 转给相关测量误差，从而保持全部观测分布相同，但 posterior centred mean 分别乘 c_i。具体单年度例：共同 μ=0、观察方差均为 2，观察 y=(−1,−0.8)。原模型潜在方差均为 1、测量方差均为 1，posterior means=(−0.5,−0.4)，第一个优先。替代模型潜在方差为 (0.2,0.8)、测量方差为 (1.8,1.2)，同一观测分布下 posterior means=(−0.1,−0.32)，第二个优先。多年度用上述 covariance 转移可保持整个观测面板等价。这个**排名不可识别反例需要放松共同 τ² 限制**；不能拿它否定一个严格坚持且正确的同方差潜在模型内部的可识别性。

这不是说 aggregate data 在任何模型下都不能识别参数。若**坚持白噪声、同方差、平稳共同 AR(1)** 且其 population lag covariances γ_1、γ_2 非零，则

\[
\phi=\gamma_2/\gamma_1,\quad
\tau^2=\gamma_1^2/\gamma_2,\quad
r=\gamma_0-\gamma_1^2/\gamma_2.
\]

这依赖可拒绝但无法由五年表完全验证的结构限制；φ=0 时 θ 和 e 都是时间白噪声，分解失去识别。异方差、类型差异和共同趋势要进入正确矩条件。有限 T=5 还意味着不稳定、边界估计及较大不确定性。

同样，单年度 n 分组方差满足的是

\[
\operatorname{Var}(Y\mid n)=\operatorname{Var}(\theta\mid n)
+\operatorname{Var}(e\mid n)+2\operatorname{Cov}(\theta,e\mid n).
\]

只有明确令第一项=τ²、第二项=σ²/n、第三项=0 才能得到全案的直线。组织规模与类型/真实体验相关时，把斜率解释成个体作答方差没有依据。

响应选择还可写成 Y_it=θ_it+b_it+ε_it。仅观察 Y 不能区分 θ 与 b。高回收率或职业加权不能证明 b=0；响应率差 15 个百分点也没有自动判定不可比的数学含义。

## 8. 为何模型残差没有因果上界

给选择组的观察变化写成 \(D=\mathrm{effect}+B_{\mathrm{untreated}}\)。减去模型基线 B_model 后，

\[
D-B_{\mathrm{model}}=\mathrm{effect}+
\{B_{\mathrm{untreated}}-B_{\mathrm{model}}\}.
\]

最后一项的符号未受约束，因此残差既可能上估也可能下估效应。即使模型完整拟合过去五年，那些年份包含未知 wellbeing 投入、共同冲击和选择变化，拟合也不能证明未干预 counterfactual。应称 **reference-model conditional change** 或 **model-implied predictive baseline**，不用“zero-intervention baseline”作为已识别事实。量表有界至多给出潜在结果本身的粗边界，不会使该残差成为有效的上界。

## 9. 公共面板与验证建议

1. 机构是正式实测层级；部门人数场景只能是明确合成外推，最好不产生真实科室可执行门槛。
2. 用官方 benchmark groups；区分比较 absolute level 与 benchmark residual，不能把调整后的低残差当成全国最低真实分。
3. 严格声明字段版本。2025 dashboard 官方说明历史年分数按 2025 occupational weights 重算；若统一使用 2025-vintage 回溯表，应称 retrospective temporal holdout，不能称实时前瞻部署检验。
4. 2024 development（2021–23 训练）与 2025 final temporal test（2021–24 训练）设计合理，但在看到 final outcomes 前固定候选与选择规则。未来年份均值不能作为预测输入；可以另报去共同趋势的 retrospective rank 分析并标识其 estimand。
5. 当前分数、简单历史平均、预先指定几何平均、静态 shrinkage、动态 Gaussian predictor 是合理基线。已知-parameter oracle 只在模拟里称 oracle。
6. 观测面板报告 forecast MAE/MSE、rank correlation、与未来**观测**bottom-k 的 overlap、benchmark composition；真实 latent overlap 只能在模拟或额外验证测量中计算。
7. 噪声尺度、相关误差、潜在 persistence、共同趋势、响应选择与 size–latent association 做分开的 sensitivity axes；不要用“低 n 趋势与原表一致”挑选参数。
8. 小于 10 份的官方抑制是保密规则，不是统计可排序性阈值。使用总问卷 n 要说明它不一定等于 sub-score 的有效答卷数。
9. 若 n_eligible 缺失，不应以全国响应率反推并当作机构回收率真值；保留缺失或明确作为情景插补。

## 10. 本次已经执行的审计计算

按全案代码的同一四参数 (μ,τ,σ,φ)=(5,0.35,2.5,0.85)、seed=20260819 和每组 4,000 repetitions 重跑，得到：

| n 范围 / 单位数 | 原始命中 | 几何五年命中 | 次年变化均值 | 模拟组均变化 10%–90% |
|---|---:|---:|---:|---:|
| 800–3000 / 206 | 0.900720 | 0.716457 | 0.087593 | 0.045605–0.129621 |
| 150–600 / 40 | 0.781156 | 0.691156 | 0.137482 | 0.015697–0.255721 |
| 40–250 / 40 | 0.672594 | 0.663313 | 0.236471 | 0.068404–0.406592 |
| 20–120 / 40 | 0.579938 | 0.623063 | 0.368548 | 0.148655–0.588852 |

这些支持原表的粗略趋势，不把模拟提升为真实 NHS 证据。各行还同时改变 M 和 n 范围，不能据此识别纯粹的样本数效应。numpy.integers 的上界是开区间。10%–90% 是重复模拟的组均变化分位数，不是均值估计的置信区间。

同样参数下，五年几何权重归一化后为 (0.2696413,0.2291951,0.1948158,0.1655934,0.1407544)，当前 latent tracking term D=0.02812056，独立同方差测量 r 的 MSE crossover=0.03561472，即等 n 下 n_crit≈175.489。它不能直接替代命中率 crossover。

第 5 节三单位 posterior counterexample 已以 SciPy 一维积分计算。所有这些审计数值都基于明确假设，不来自 NHS 实测个体或机构数据。

## 11. 合理的贡献定位

**经典工具：** 条件 Gaussian regression、RTM、Kalman filtering、posterior expected-loss 最优化、方差展开、union-bound regret certificate。

**可形成本文贡献的组合：** 公开面板中的观测可验证性与 latent 不可识别性分离；同一任务下 severity 与 membership 目标的实测/模拟差异；共同未知噪声尺度下精确名单翻转图与适用边界；使用已核查权重版本与 benchmark groups 的 NHS 时间外预测，并保留失败结果。

论文不应以“首次发现低分会回升”“新 Gaussian EB 排序算法”“给任何健康项目的最低有效门槛”作为贡献。一个诚实、可复现的 decision and identification audit，比基于未识别参数的强部署承诺更有价值。

## 12. 独立实现核查与可复现实验

新增 `experiments/theory_checks.py`；运行结果保存在 `results/theory_checks.json`，其中记录被核查脚本与协议的 SHA-256。执行命令为项目上层目录中的 `.venv/bin/python nhs_wellbeing_research/experiments/theory_checks.py`。该脚本是独立审计，不应作为额外主实验重复次数计入 600,000 面板。

### 12.1 已核对的实现

- `common.py::gaussian_weights` 的 current-state 交叉协方差为 τ²φ^lag；下一期 observation 同时包含 latent 的 φ 项与 measurement error 的 ψ 项。后一项对相关测量误差不可遗漏。条件方差使用对应下一期边际方差；φ=1、σ²=0 的奇异情形用伪逆处理。另行组装完整六波联合协方差、以特征分解条件化，60 个参数/单位组合的权重最大差 1.56×10⁻¹⁴，方差最大差 2.31×10⁻¹⁵。
- `simulate.py` 的 `latent_regret` 是选择组当前真实状态均值减去真正 bottom-k 组均值，符合 posterior mean 的 Bayes 目标。`hit` 是真实有限总体集合命中率，目标不同，不能用其某个劣势反驳前一个目标的 Bayes 最优性。
- 五种模拟选择规则均是观察历史的函数，故使用完整历史条件分布预测其下一期变化合法。独立审计采用 30,000 个面板、相关误差 ψ=.4 和负共同趋势 −.12；raw 与历史均值选择的条件残差 z 值为 −.481 和 −.365，符合零条件均值。即便平均变化为正，30.38% 和 45.72% 面板的选中组实际变化仍为负。
- `empirical.py::predict` 的 working-covariance 方法按每年 n 在对角线上加入不同测量方差，下一年 measurement error 假设独立，所以交叉协方差仅是 φ 的幂。独立线性系统计算的最大预测差 9.33×10⁻¹³。线性趋势方法的 next-year 时间索引也正确。预测函数没有读取目标年数值。
- 静态 pair crossing 的分母与方向正确。对 60 组随机输入检查 346 个无 crossing 区间以及 60 个端点 selection certificate 全部通过。两单位显式反转出现在 κ=.5；解析 crossing 处的浮点分数最大残差为 2.23×10⁻¹⁶。
- 非识别例额外核查了完整四波观测协方差相同，以及以完整历史条件化仍能发生异质 c_i 排名反转。共同 c 例保持均值排名。严格白噪声模型下的 lag-covariance 正识别公式亦通过。

### 12.2 结果解释必须保留的限定

1. 模拟采用已知 μ_t 和已知 DGP 参数；压力测试中时间汇总方法亦知道并去除了共同趋势。这不是模型成功预测未知共同趋势的证据。response-bias 和 heavy-tail 压力测试中的 Gaussian predictor 是错误指定的参考计算，代码用 `gaussian_exact=False` 正确区分。
2. 主模拟每个 cell 抽一次 n 向量，再在该设计下生成独立面板；全案 replay 每个 repetition 重新抽 n。二者不是相同模拟设计，其重复次数和输出不可合并。主实验同一面板上的方法与 fraction 彼此配对。
3. 经验 group mean 来自同组历史机构数据，具有估计误差，也造成中心化后跨机构依赖；因此应称 **working-covariance prediction**，不声称它是已知总体 μ 的精确条件后验。使用同组训练年数据并不构成读取目标年结果。
4. 配对 bootstrap 固定训练所得预测及超参数，重抽测试机构；它描述测试机构组成导致的条件性能差异，不包含重新训练、重新调参、任意机构间关联或新时间冲击的不确定性。
5. 五波完整且官方可比的 cohort 由回顾性可用性定义。年度原始发布版本敏感性改善 vintage 问题，但并不使研究变成当时已部署的 prospective evaluation。
6. `pair_crossings` 使用解析公式生成浮点端点，排序使用稳定的数值 argsort。一般位置下的所有开区间结果与证书可靠；若声称多个 crossing 恰好重合时还完全实现符号意义的 organisation-code tie policy，需要额外的显式容差或精确算术。这个小数值限定不能反向夸大为真实名单广泛不稳定。

未发现需要更改主 Gaussian 公式、选择损失或预测时间索引的实现错误。上述解释限定比增加一个与实现逐行同构的单元测试更重要。

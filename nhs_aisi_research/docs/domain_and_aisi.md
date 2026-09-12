# NHS 员工体验测量的实际流程与 AISI 研究定位

核验日期：2026-09-11。本文是公开资料研究和拟议使用场景，**未与 NHS 员工、管理者或调查承包商共同设计，未开展访谈、合作、现场试验或部署**。引用的其他团队的合作与实验不属于本项目。旧版 `nhs_wellbeing_research/` 及其交付不因本文改变。

## 结论与投稿时间

较可信的研究问题是：**在全员基础反馈渠道继续开放的前提下，如何分配额外的信息收集资源，帮助人员体验团队决定哪些单位需要进一步了解？** 这与分配治疗、健康福利或人员编制预算不同。本文支持这一问题的实际背景，不证明 NHS 已经采用本文算法，也不证明额外测量改善了员工健康。

AAAI-27 AISI 的摘要、全文、补充材料截止时间分别为 **2026-07-21、07-28、07-31 的 23:59，UTC−12**。因此在本次核验日，常规投稿窗口已经结束。官网保留的“submission is now open”文字不改变日期。本项目可向 AISI 的研究标准升级，不能表示仍能常规新投 AAAI-27，也不能把未来届次日期当成已公布。[AISI 官方 CFP](https://aaai.org/conference/aaai/aaai-27/aisi-call/)

## 已有流程：谁在什么时候使用什么信息

| 工具或阶段 | 官方用途与实际约束 | 对本研究的含义 |
|---|---|---|
| 年度 NHS Staff Survey（NSS） | 秋季开展，次年春季公布；普查邀请覆盖所有符合条件员工；组织使用结果制定行动。 | 年度公开组织分数提供背景与时间序列，无法观察额外抽样的效果。不能通过算法取消部分员工的基础邀请。 |
| National Quarterly Pulse Survey（NQPS） | Q1、Q2、Q4 的首月收集；所有员工须有回应机会。核心为九个 engagement 问题，涉及 motivation、involvement、advocacy。 | 其标准核心不等于七项 burnout 复合指标。不能把季度 engagement 当成同一 burnout 构念的重复测量。 |
| NHS People Pulse | 提供月度、可按本地需要调整频率的反馈；官方描述约五分钟完成。 | 可作为讨论补充测量流程的参照；五分钟是 People Pulse 的说明，不能直接当作本研究某个 burnout 题包的实测成本。 |
| 听取意见、讨论、行动、反馈 | Listening well 指导要求调查与团队讨论、员工网络及其他信息结合，纳入管理和董事会决策节奏，并把行动反馈给员工。 | 排名应帮助提出调查问题并解释不确定性；单一分数不回答原因，也不决定具体干预。 |

来源：[年度调查 FAQ](https://www.nhsstaffsurveys.com/faqs/)、[NQPS 实施指南，2023-06](https://www.england.nhs.uk/wp-content/uploads/2021/06/B0581-National-quarterly-pulse-survey-guidance-June-2023.pdf)、[People Pulse](https://www.england.nhs.uk/nhs-people-pulse/)、[Listening well](https://www.england.nhs.uk/long-read/listening-well-guidance/)。

官方列出的使用者包括 HR、staff experience/engagement leads、员工网络和管理层。拟议直接使用者为 workforce/OD analyst 与 staff experience lead；由人员管理负责人承接决策，由调查承包商管理个人回应。这些是**根据公开角色提出的使用设计**，尚未确认某家机构拥有跨组织额外测量预算或愿意使用工具。[调查 FAQ](https://www.nhsstaffsurveys.com/faqs/)

一个可核查的本地例子是 HPFT 的 2025 EDS 报告：其人员与 OD 报告向董事会提供缺勤趋势，在事业部层面支持讨论；People Promise 工作结合 NSS、ESR 离职、岗位空缺、自评和焦点小组。它说明实际管理采用多源信息，不说明所有 trust 的流程一致，更不构成本研究的合作证据。[HPFT 报告，第 24 页](https://www.hpft.nhs.uk/media/pqcgu3vi/equality-delivery-system-2025.pdf)

## 必须保留的测量与治理边界

1. **组织不等于科室。** 现有 NHS 研究的 190 个 reporting units 对应 189 个已识别法律实体；R1F1/R1F2 是同一实体的两个报告单位。公开组织面板不能称作 190 个科室。年度 benchmark 依职业组成加权；本地 directorate/breakdown 通常不加权，也没有同类标准化部门 benchmark。组织排序优先在相同 benchmark group 内解释。[调查 FAQ](https://www.nhsstaffsurveys.com/faqs/)
2. **不同渠道不是可直接互换的重复样本。** NSS 加权、NQPS 不加权，回应和季节亦不同。独立重新抽人不自动消除共同的不回应偏差、量表解释偏差或时点变化。第二渠道“无共享偏差”必须是被检验的模型假设，不能写成 NHS 已验证的 gold standard。[NQPS 指南](https://www.england.nhs.uk/wp-content/uploads/2021/06/B0581-National-quarterly-pulse-survey-guidance-June-2023.pdf)
3. **题目重用和隐私有具体规则。** 官方要求将 NSS 问卷或其子集用于其他目的取得 NHS England 明确许可；年度调查由独立承包商保密处理。少于十份回应的 breakdown 被抑制是保密规则，不是精度或代表性达标线。个人填写自愿；官方建议安排工作时间。[调查 FAQ](https://www.nhsstaffsurveys.com/faqs/)
4. **真实资源包括员工时间。** NQPS 指南明确要求考虑人员、成本和专业资源，并与员工代表讨论新增问题。拟议预算至少区分接触/提醒、完成、分析和报告成本；完成数随机，不能把一个抽样包解释成必然取得固定人数的独立答案。[NQPS 指南](https://www.england.nhs.uk/wp-content/uploads/2021/06/B0581-National-quarterly-pulse-survey-guidance-June-2023.pdf)
5. **信息收集服务于行动。** 官方指导指出，仅调查不能解释问题成因，需结合团队对话；持续询问而无可见反馈会削弱参与。因此更多问卷并非天然更好，低回应或不确定性高也不能成为减少支持的理由。[Listening well](https://www.england.nhs.uk/long-read/listening-well-guidance/)

**研究设计推论（不是官方现成算法要求）：** 先固定全员基础入口，再研究额外跟进；若涉及细分群体，预先规定最小汇报单位、差分披露检查和不回应处理；使用第二渠道时记录抽样机制、重叠受访者、量表对应和时差；资源优化中包含成本与覆盖约束；不确定性不足以排除严重问题，保留人工复核和现有紧急上报机制。

## People Promise 中真实行动与评价的例子

2025 年官方 Cohort 1 结项报告覆盖 23 家 trust，以多项 People Promise 措施组合为对象，整合过程评价、NHS England 分析员开展的离职率差分中的差分分析、年度调查及 People Promise manager 反馈。它提供了“措施记录—人员结果—问卷—实施过程”的实际评价链条。报告还说明部分主题分析只涵盖 19 家 acute/acute-and-community trust，并针对表现较好的案例深挖。[官方结项报告](https://www.england.nhs.uk/long-read/people-promise-exemplar-programme-cohort-1-close-of-programme-evaluation-report/)

**我们的解释：** 该报告包含非随机准实验分析，不能称为只有简单前后对比；也不能从其项目级结果推出本研究采样算法的因果效果。完整的平行趋势、选择机制和成本敏感性仍应按拟议研究自身设计核验。本文不借用其效应量或投资回报率作为算法收益。

## 四篇近期 AISI 录用全文：实际证据与可借鉴之处

四篇均核实位于 AAAI 2026 官方 **40(45), Special Track on AI for Social Impact I**，阅读了原文的研究问题、实验和限制部分。这是有目的选取的相关案例，非全部录用论文的系统综述，不能据此推算录用概率。[官方专辑](https://ojs.aaai.org/index.php/AAAI/issue/view/727)

| 论文 | 原文实际证据 | 对本项目的启示及不可照搬之处 |
|---|---|---|
| Betti et al., **Mapping on a Budget: Optimizing Spatial Data Collection for ML**, 38233–38241 | 为 Togo 的调查增补提出具体问题；在三国、四项任务上用已有真实标签模拟空间采样，包含异质采集成本。文中明确用于评估的稠密数据与动机中的 2,000 户原调查不同。 | 最接近本项目：写清预算、已有数据与新增采集；承认实验代理与实际流程的差距。其真实合作关系属于该作者团队。 [原文](https://ojs.aaai.org/index.php/AAAI/article/view/41162/45123) |
| Goebel et al., **Budgeted Online Active Learning with Expert Advice and Episodic Priors**, 38496–38504 | 农业模拟与真实葡萄耐寒记录；真实数据任务查询预算 2–5，查询模拟用插值标签，评估用实际测量；报告专家质量敏感性。 | 控制有限时域与预算，分清查询模拟和评估真值。不能把其结果描述成已证明农场增产，或把独立样本等同于无偏。 [原文](https://ojs.aaai.org/index.php/AAAI/article/view/41191/45152) |
| Chen, Sjoding & Wiens, **Measuring Model Performance in the Presence of an Intervention**, 38296–38303 | 理论、合成数据、AMR-UTI 数据构造的模拟随机化，以及 Michigan Medicine 的真实 readmission RCT（1,518 人）；比较存在干预时的模型评价。 | 真实试验与半合成试验须分别报告；反事实评价要有相应识别条件。NHS 公开面板没有因此获得干预识别能力。 [原文](https://ojs.aaai.org/index.php/AAAI/article/view/41169/45130) |
| Kothari et al., **When the Domain Expert Has No Time and the LLM Developer Has No Clinical Expertise: Real-World Lessons from LLM Co-Design in a Safety-Net Hospital**, 38754–38762 | 实际社会工作场景；99 名患者的 1,216 份记录用于迭代诊断，85 份记录用于人工验证；报告模型裁判与人工意见不一致的属性。 | 用户时间、任务定义和错误类型本身可以是研究贡献。其人工验证不等于我们已完成 NHS 用户验证，也不证明通用临床结局改善。 [原文](https://ojs.aaai.org/index.php/AAAI/article/view/41219/45180) |

**归纳判断：** 可复核的实际约束、强且公平的基线、真实数据与适当模拟的组合、成本/偏差失配和失败结果，比增加一个“社会影响”标题更有价值。上述证据不要求每篇论文同时包含部署、RCT 和新神经网络；也不能据这些案例为本项目免除实证或创新性要求。

## 补充三篇直接相关的原始医疗管理研究

| 原始研究 | 研究设计与本稿可合理使用的内容 | 不能推出的结论 |
|---|---|---|
| Powell et al. (2014), **Staff satisfaction and organisational performance: evidence from a longitudinal secondary analysis of the NHS staff survey and outcome data**, HS&DR 2(50), DOI 10.3310/hsdr02500 | 2009–2011 NSS 联合人员及组织结果，采用多层、增长曲线、交叉滞后等分析；员工体验与缺勤、患者满意度存在联系，也明确报告年度组织聚合和因果方向限制。 [NIHR 原报告](https://www.ncbi.nlm.nih.gov/books/n/ukhsdr0250/pdf/) | 不能据关联设定每改善一个 burnout 分数带来多少收益，或宣称通过本算法排序必然改善患者结果。 |
| Dixon-Woods et al. (2014), **Culture and behaviour in the English National Health Service: overview of lessons from a large multimethod study**, BMJ Quality & Safety 23(2):106–115 | NHS 2010–2012 多方法研究，结合访谈、观察、团队资料、董事会记录；区分主动发现问题与寻求表面安心的组织行为。适合解释为什么需多源信息、上下文与反馈。 [作者机构存档原文](https://publications.aston.ac.uk/id/eprint/22403/1/Culture_and_behaviour_in_the_English_National_Health_Service.pdf) | 数据更多或排行榜更精确并不自动形成行动；不能把其受访者、合作机构算入本项目。 |
| West et al. (2014), **Intervention to Promote Physician Well-being, Job Satisfaction, and Professionalism: A Randomized Clinical Trial**, JAMA Internal Medicine 174(4):527–533 | 单中心 74 名医生随机试验，两个随机组均有受保护时间，干预组另有 19 次小组课程；评价实际干预而非测量策略。报告部分维度改善和多项未显著差异。 [期刊原文](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/1828744) | 美国单中心医生结果不能直接外推到 NHS 全职业群体；不能把非随机外部队列比较当作随机组间效果。 |

这三篇是针对缺失的基础领域知识补充，**不是声称已完成截至 2026 年的系统性文献综述**；2025 People Promise 官方项目评价补充当前实践背景。相应题名、作者、年代、DOI 和入口保存在 `domain_and_aisi_references.bib`。

## 研究证据台账与下一步评估

| 可以验证的层次 | 新研究中的含义 | 保留的限制 |
|---|---|---|
| NHS 历史面板 | 组织年度体验、已有排名不确定性及假定信息预算下的场景 | 没有实际第二测量渠道、额外抽样、个人权重/回应轨迹或干预效果 |
| BRFSS 公开个人记录回放 | 在真实已记录回答的有限总体上揭示/抽取记录；可检验预算策略 | 美国居民心理健康天数不是 NHS 员工 burnout；人工改变招募概率是注入机制；全文件均值不是无偏人口真值 |
| 控制模拟 | 明确潜在状态、偏差、成本和变化机制，核验何时第二渠道有价值 | 参数并非估计的 NHS 实际成本/偏差；理论结论仅在所述假设下成立 |
| 拟议前瞻评估 | 对现有流程做任务核对、静默运行、成本和可用性评价 | 尚未实施；需要真实机构、员工代表与数据治理方参与，不能称 co-design 或 deployment |

AISI 官方强调数据收集、问题建模和实地评价，可在其中部分维度较强，并关注跨应用的技术或科学启示。本研究若贡献只是把现成 knowledge-gradient 换到 NHS 分数上，仍不足以支持强创新性；应论证**在持续渠道偏差、不同验证成本及共同偏差情形下，哪些信息真的改变固定名额选择、哪些只改变水平估计**，并用匹配推断条件的基线检验。该表述是研究定位建议，不是已取得的实验结论或录用判断。[AISI CFP](https://aaai.org/conference/aaai/aaai-27/aisi-call/)

在形式上，AAAI-27 规定正文最多七页、总计最多九页且额外两页仅参考文献；不能把关键依据全部放到可选补充材料。AI 辅助不转移作者对事实、引用和分析的责任。旧稿与扩展若重叠，应按实际贡献关系整合或明确披露，不能通过改写包装为重复投稿。[主技术轨 CFP 与政策摘要](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)

配套 `nhs_decision_brief.md` 和同名 PDF 为**尚未与真实使用者共创的一页讨论提案**；它们没有发送给任何 NHS 机构。

> Authorship update (2026-09-12): the edit-localization paper lists Shengwei Zhang, Haoda Dai, Yifei Li and Yuheng Song, all University of Pennsylvania. The base-model upgrade paper now lists Shengwei Zhang (University of Pennsylvania), Tao Wu and Fei Qian (both Alibaba International Digital Commerce). Earlier single-author statements in this dated document describe previous versions; reviewer-eligibility or quota conclusions relying on those assumptions require reassessment. Scientific result records are unchanged.

# 两篇论文的投稿准备度：审稿人视角

评估日期：2026-09-11。这是基于当前正文、已执行实验和一手文献的研究判断，不是录用预测。**现在已经有可以继续打磨、公开审查的完整研究稿；不能仅因章节齐全、公式正确和实验可复现，就把它称为成熟的 ICLR 主会论文。** 两篇都应保留诚实的贡献边界。

## 论文 A：有明确诊断价值，关键是让读者看到如何使用

目前最有说服力的部分，是把“局部编辑会放大选择偏差”改成可检验的几何条件：实际曲线可以放大、反转或非单调；IPW 去掉某个局部目标的选择偏差，并不去掉相对于完整目标的目标差异。两种语言的真实人工 post-edit、固定预训练模型、精确有限总体计算和完整重放记录，使它已经超出了纯概念说明。保留英文—德文的内部极大值，以及 IPW 一步更新不总优于未加权更新的结果，增强了可信度。

审稿人仍可能提出三个实质问题：二次式比值的求导本身较简单，新的研究价值究竟在何处；真实文本上的筛选概率仍是人为注入，尤其编辑比例使用事后 PE 标签；固定检查点的梯度现象能否帮助选择训练策略。共享输出偏置实验说明了一个受限参数块的行为。全参数梯度可以拓展其参数范围，但依然不能替代多步训练、独立选择超参数、译文质量及跨模型泛化证据。

因此最值得补强的不是再加一个定理名称，而是一个明确的实际决策：用独立诊断数据估计条件或选择保留系数，再在未参与选择的样本和检查点上验证预期误差／质量。至少还应检查对齐方式、EOS、句长归一化和参数化的敏感性。若没有这一步，合理定位是**关于纠错学习目标与选择偏差的分析型论文**；不应宣称已解决真实投诉渠道的去偏训练。[相关前例：CRM](https://proceedings.mlr.press/v37/swaminathan15.html)、[概率参考样本](https://www.tandfonline.com/doi/abs/10.1080/01621459.2019.1677241)、[真实 post-edit 偏好学习](https://aclanthology.org/2024.wmt-1.122/)

## 论文 B：统计方向已修正，研究增量仍需更强应用证据

现在最重要的正确结论，是“没有检出伤害”不等于“已经认证安全”，以及固定候选的所有切片联合成功与在多个候选中择优的多重性不同。配对差值、独立认证集、失败返回旧模型、精确旧模型锚点，都使发布流程清楚且可复现。

但这些构件分别已有成熟先例：[Learn then Test 已发表于 AOAS 2025](https://doi.org/10.1214/24-AOAS1998)，[Seldonian](https://people.cs.umass.edu/~bsilva/papers/seldonian_toolkit_ICSE_2023.pdf) 已有候选选择和安全测试分离；[MAP](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a3724221b623bf1966e92cd266ac6177-Abstract-Conference.html) 与 [Pareto Merging](https://proceedings.mlr.press/v267/chen25af.html) 已研究多目标合并；[Provably Safe Model Updates](https://arxiv.org/abs/2512.01899) 还包含安全参数域、旧模型锚点和有限样本论证。当前最容易被质疑的是：现有统计工具的合理组合，是否产生了足够新的可推广见解或实际能力。

公开 digits 初始实验是有效的流程验证，但其新模型故意只训练部分类别，属于遗忘压力测试。针对这一缺口，本次随后固定协议并执行了全部类别继续训练：平均整体准确率从 94.78% 提高到 95.94%，认证仍在全部五个种子上失败，分层合并也未显示优势。这个补充丰富了实际升级路径，但复用了初始 holdout，应作为描述性证据；它仍不能支持“真实大模型基座升级已被解决”。主会级应用证据应包括实际基座升级对、多个切片与样本预算、相同认证接口下的真实合并候选、接受率和保留效用，并同时展示无法认证的情形。当前更稳妥的定位是**切片非退化认证的完整方法说明与可复现研究**，而非新的模型融合算法。

## 可执行的投稿分流

| 路线 | 当前适配判断与时间 |
|---|---|
| ICLR 2027 | 两篇都可在主题范围内，但当前研究增量与实证广度仍有明显风险。摘要 **9 月 18 日**、全文 **9 月 25 日 23:59 AoE**。不应为赶截止扩大主张。新作者 reciprocal-reviewer 配额也可能使同一唯一作者本届只能投一篇。[官方 CFP](https://iclr.cc/Conferences/2027/CallForPapers)、[作者要求](https://iclr.cc/Conferences/2027/AuthorGuidelines) |
| SaTML 2027 | 论文 B 的可信发布与认证主题更直接。摘要 **9 月 22 日**、全文 **9 月 29 日 23:59 AoE**；Research/SoK 正文最多 12 页，IEEE 双栏。SoK 需要系统化分析和新见解，不能仅换标题。它与 ICLR 审稿期重叠，同一篇不能同时交全文。[官方 CFP](https://satml.org/call-for-papers/) |
| ARR → NAACL／COLING 2027 | 论文 A 的人工纠错与机器翻译主题自然；要清楚说明 NLP 读者能学到什么。相应 ARR 截止 **10 月 12 日 23:59 AoE**，不是等 ICLR 决定后的备用窗口。同一篇在另一处审稿时不能再交 ARR。[ARR 日期](https://aclrollingreview.org/dates)、[NAACL CFP](https://2027.naacl.org/calls/main_conference_papers/) |
| TMLR | 两篇都可考虑充分修订后滚动投稿。其标准重视可靠证据与读者能够学到的东西，并不要求每篇提出新方法；但这不意味着简单课程复现或缺乏人类深入参与的 AI 成稿会获接受。[官方标准](https://jmlr.org/tmlr/acceptance-criteria.html) |
| WMT | 论文 A 的专题匹配度较好，但 **WMT 2026 新稿窗口已关闭**：全文 8 月 7 日、ARR commitment 8 月 28 日。未来届次必须等官方征稿；不要把今天 9 月 11 日的 camera-ready 日期误认为新投稿截止。[WMT 2026](https://www2.statmt.org/wmt26/) |

如果只能集中资源推进一篇通用 ML 投稿，A 的“可测几何诊断＋保留失败案例”目前比 B 的“现有认证工具组合”更容易形成独立故事；B 可以进一步围绕可信发布的系统化研究发展。这个排序是研究判断，不覆盖作者的真正贡献偏好、共同作者安排或未来新增证据。

## 公开之前的实际门槛

arXiv 可以作为完整、诚实研究稿的公开入口，不要求先有会议录用；预印本公开也不等于同行评审通过。[arXiv 投稿说明](https://info.arxiv.org/help/submit/index.html)

两篇论文的单一作者和机构已由用户确认为 Shengwei Zhang，University of Pennsylvania。仍需完成的工作是：作者逐项理解和确认关键证明、实际运行结果、贡献来源与相关工作；确定公开权属与许可证；按目标会场制作匿名版与匿名代码；据实披露本次 AI 对推导修订、实验设计、代码和写作的参与。不能把这次工作只描述成英文润色，也不能预先声称人类复核已经完成。ICLR 和 SaTML 都有明确披露要求。[ICLR AI 政策](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)、[SaTML AI 政策](https://satml.org/call-for-papers/)

可复现性解决“这些结果是否真的这样算出来”；研究准备度还取决于“结果是否回答了重要问题、比已有工作多说明了什么、作者是否能为其负责”。这三件事应分别判断。

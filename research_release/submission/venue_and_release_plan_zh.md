> Authorship update (2026-09-12): the edit-localization paper lists Shengwei Zhang, Haoda Dai, Yifei Li and Yuheng Song, all University of Pennsylvania. The base-model upgrade paper now lists Shengwei Zhang (University of Pennsylvania), Tao Wu and Fei Qian (both Alibaba International Digital Commerce). Earlier single-author statements in this dated document describe previous versions; reviewer-eligibility or quota conclusions relying on those assumptions require reassessment. Scientific result records are unchanged.

# 两篇研究的投稿与公开发布路线

核验日期：2026 年 9 月 11 日；用户时区：America/New_York。以下会议事实均来自官方页面，路线选择是基于两篇原稿题目、摘要和研究范围的判断。本文是操作准备文件，不代表已经投稿、创建账号、联系任何人或公开发布。

## 1. 现在最影响决策的三件事

**ICLR 2027 的截稿已经很近。** 官方列出的摘要截止是 2026-09-18 23:59 AoE，全文截止是 2026-09-25 23:59 AoE；审稿公布 11 月 5 日，作者讨论 11 月 5–18 日，决定 12 月 16 日。AoE 是 UTC−12，不是纽约午夜。[ICLR 2027 CFP](https://iclr.cc/Conferences/2027/CallForPapers)

**两篇未必能同时投本届 ICLR。** 每位作者最多参与一篇“全体作者均不具备 reciprocal reviewer 资格”的投稿。资格按摘要截止时已被指定主会／期刊接收的论文判断；arXiv、workshop、industry track 等不能自动满足资格。两篇均已确认为 Shengwei Zhang 单独署名、机构为 University of Pennsylvania；若没有符合条件的既有论文，本届只能提交其中一篇。不能为绕过配额临时挂名共同作者。[ICLR 作者要求：Quotas 与 Reciprocal Reviewing](https://iclr.cc/Conferences/2027/AuthorGuidelines)

**arXiv 与顶会并不要求按“先被 arXiv 接收，才能投会议”的顺序进行。** ICLR 允许预印本；因此，不应为了抢 arXiv 编号而公开尚未核实的推导或实验。先把论文证据补齐，再分别制作公开版与匿名审稿版。[ICLR 2027 CFP](https://iclr.cc/Conferences/2027/CallForPapers)

## 2. 可以据此安排工作的日期

| 事项 | 官方截止（AoE，UTC−12） | 纽约当地时间 | 北京时间 | 来源 |
|---|---|---|---|---|
| ICLR 2027 摘要 | 2026-09-18 23:59 | 09-19 07:59 EDT | 09-19 19:59 | [ICLR](https://iclr.cc/Conferences/2027/CallForPapers) |
| ICLR 2027 全文及补充材料 | 2026-09-25 23:59 | 09-26 07:59 EDT | 09-26 19:59 | [ICLR](https://iclr.cc/Conferences/2027/AuthorGuidelines) |
| NAACL／COLING 对应 ARR 轮次 | 2026-10-12 23:59 | 10-13 07:59 EDT | 10-13 19:59 | [NAACL](https://2027.naacl.org/calls/main_conference_papers/) |
| NAACL／COLING commitment | 2026-12-23 23:59 | 12-24 06:59 EST | 12-24 19:59 | [NAACL](https://2027.naacl.org/calls/main_conference_papers/)、[COLING](https://2027.coling-iccl.org/) |

NAACL 2027 官方页列出 meta-review 在 2026-12-18 发布，接收通知为 2027-02-10。ARR 的日期表已把该轮结束和 commitment 更新为 12 月 23 日；搜索缓存／旧仓库摘要曾显示 12 月 20 日，本文件采用三个当前官方页面一致的 12 月 23 日。[ARR 当前日期](https://aclrollingreview.org/dates)、[NAACL 当前 CFP](https://2027.naacl.org/calls/main_conference_papers/)

ACL 2027 官网的 ARR 截止与 commitment 仍是 **TBA**；ARR 总表仅列 **January 2027**，尚不能据此编造具体日。ICML 2027 和 NeurIPS 2027 本次未核实到正式主会 CFP，官网首页仍展示 2026 届；不能把上一年的截稿、页数、AI 或作者政策当作 2027 规则。[ACL 2027](https://2027.aclweb.org/)、[ARR](https://aclrollingreview.org/dates)、[ICML](https://icml.cc/)、[NeurIPS](https://neurips.cc/)

历史参照仅用于排期背景：ICML 2026 全文在 1 月 28 日 AoE 截止、正文 8 页；NeurIPS 2026 全文在 5 月 6 日 AoE 截止。两者 2026 主会投稿均已结束。[ICML 2026 CFP](https://icml.cc/Conferences/2026/CallForPapers)、[NeurIPS 2026 CFP](https://neurips.cc/Conferences/2026/CallForPapers)

## 3. 两篇稿件怎样分流

| 稿件 | 研究中心 | 建议路线与需要补足的内容 |
|---|---|---|
| Selecting Base-Model Upgrades Under Per-Slice Non-Regression Constraints | 模型合并、相对非退化约束、选择之后的统计保证 | 优先按 ICLR／后续 ICML、NeurIPS 的通用 ML 稿准备。关键是正确的安全判据、选择与认证分离、多个模型与切片的真实实验。如果证据仅来自翻译场景，NAACL／ACL 也可以，但需明确语言任务贡献。 |
| Edit Localization Amplifies Selection Bias in Learning from Production Corrections | 生产纠错、编辑定位、选择偏差、校正训练目标 | 以 NAACL／ACL／EMNLP 的机器翻译、Human-Centered NLP 或 ML for NLP 方向最自然；补齐真实／公开纠错实验和偏差识别假设。要转向 ICLR／ICML，应证明结论跨越单一翻译任务并具有足够的方法或理论增量。 |

上表是选题匹配判断，不是录用预测。NAACL 明确接收理论、方法、实证和评估贡献，其主题包含机器翻译、多语言、泛化和迁移；ICLR 范围覆盖一般机器学习、不确定性与安全等主题。[NAACL 2027 CFP](https://2027.naacl.org/calls/main_conference_papers/)、[ICLR 2027 CFP](https://iclr.cc/Conferences/2027/CallForPapers)

可行的分流例子：两篇内容确实独立时，Base-Model 稿在满足质量与配额要求后投 ICLR，Edit Localization 稿投 10 月 ARR。**同一篇 ICLR 在审稿时，不能再投 10 月 ARR。** 若不赶本届 ICLR，可先完成实验，再选择未来已公布规则的轮次。NAACL 与 COLING 使用同一 ARR 轮次，在 commitment 时只能指定一个主会；官方提供有条件的另一会议考虑选项，不能理解为双投许可。[ARR 多重投稿政策](https://aclrollingreview.org/cfp)、[NAACL commitment 说明](https://2027.naacl.org/calls/main_conference_papers/)

## 4. 论文与匿名版的具体要求

### ICLR 2027

正文初投 **9 页以内**；rebuttal／终稿 10 页。参考文献和之后的附录不限页，但审稿人无义务阅读附录。使用 [官方 2027 LaTeX 模板](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip)。正文、补充材料和代码链接均须匿名；同作者相关工作用第三人称引用。摘要须真实，摘要截止后不能增删作者。全部作者应及早完成 OpenReview profile；非机构邮箱新账号审核可能需两周。投稿截止之后撤稿仍会保留公开记录，并立即去匿名。[ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines)

核验备注：该页部分 FAQ 仍有把“submission version”写为 10 页的残留措辞；明确的 Paper formatting 段落规定初投 9 页。因此当前准备按更严格的 **9 页**执行，最终上传前再核对。

**AI use statement 是必填论文部分，且提交表单也需填写。** 本次实际用到的理论批判、命题／证明修订、方法与实验设计、实现等协助不能只笼统写成英文润色；应逐项据实说明。作者必须核验最终内容并承担责任，不能预先声称已经完成尚未做过的人工验证。该声明不计入正文页数。[ICLR 2027 AI Policy for Authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)

### ARR／NAACL

长文正文 8 页，短文 4 页；Limitations 必须有，按规定放置时不占内容页数，参考文献与可选附录按 ARR 规则处理。正文与仓库链接仍须匿名。当前允许公开署名预印本；如果提交表单选择有约束力的“no non-anonymous preprint”，则必须遵守该轮约定，不能边选该项边上 arXiv。提交期间不能一稿多投。[ARR CFP](https://aclrollingreview.org/cfp)

## 5. arXiv 提交材料

1. **作者身份与类别。** 注册作者自行提交；初次投稿或进入新类别可能涉及 endorsement。根据内容，Edit Localization 可考虑主类 `cs.CL`、交叉 `cs.LG`；Base-Model 可考虑主类 `cs.LG`，若主要实证为语言模型再考虑 `cs.CL`。这是分类建议，最终由作者选择并接受平台 moderation。[arXiv 投稿概览](https://info.arxiv.org/help/submit/index.html)、[分类定义](https://arxiv.org/category_taxonomy)
2. **Endorsement。** 使用机构邮箱有帮助，但不能保证第一次投稿自动通过。当前规则说明，已认领合著论文并满足机构邮箱条件可能获得 endorsement；否则可找该领域有资格且了解工作的 arXiv 作者。系统在新建投稿、选择类别后提供请求信息。至少一个正面 endorsement 满足相应 endorsement 类别要求；endorsement 本身不是同行评审。[arXiv Endorsement](https://info.arxiv.org/help/endorsement.html)
3. **源文件包。** 既然论文用 LaTeX 编写，就准备能在干净目录编译的 `.tex`、实际使用的图、非标准样式和参考文献依赖。arXiv 不接受由 TeX 生成的 PDF 来替代 TeX 源文件。压缩包只含该篇所需文件；图必须随文提交，不能只放外链。文件名避免中文与空格；去掉本地绝对路径、无关备份和构建日志。[arXiv 投稿概览](https://info.arxiv.org/help/submit/index.html)、[TeX 投稿说明](https://info.arxiv.org/help/submit_tex.html)
4. **公开信息。** 准备题目、摘要、真实作者顺序与单位、类别、备注、许可证及公开仓库链接。不要填不存在的录用、DOI 或 arXiv 编号。许可证要与材料权属和后续出版安排相容；每个已发布版本的许可不可撤销。`CC BY 4.0` 与 arXiv 自身分发许可都在可选项中，但不是同一授权范围。[arXiv Licenses](https://info.arxiv.org/help/license/index.html)
5. **平台编译与最终检查。** 在平台生成 PDF 后逐页核对，完成最终提交步骤才进入队列。检查可能用 1–4 天或更久，通常周日至周四晚上公告，周五、周六不公告；正式编号在公开公告时生成，无法事先取得。后续修正走同一条目的新版本。[arXiv TeX](https://info.arxiv.org/help/submit_tex.html)、[公告时间](https://info.arxiv.org/help/availability.html)、[投稿概览](https://info.arxiv.org/help/submit/index.html)

## 6. GitHub 研究仓库的发布设计

建议一个研究总入口加两篇清晰独立的目录；每篇均能从 README 找到论文、方法概览、环境、数据取得方式、复现实验命令、结果文件和局限。仓库中的实测结果、合成验证和待做实验要明确区分。采用固定随机种子、环境锁定、配置文件、模型和数据版本、图表生成脚本及结果溯源，让论文中的每张表可以追到生成它的程序输出。

对外仓库应只发布有权发布的材料：原始采访／面试 skill、个人资料、公司内部日志、私有 checkpoint 和客户文本不能因为放进本地工作区就成为公开仓库内容。此处仅是针对现有材料的发布组织方案，不推断这些私有材料已经获准公开。

公开版可署名并链接 arXiv；匿名审稿包从同一实现导出，清理 README、元数据、历史、引用文件及链接中的身份信息。最好将代码作为补充 ZIP，并提供固定版本；不要在匿名论文中直接指向实名 GitHub 主页。ICLR 允许匿名补充代码或匿名仓库。[ICLR 代码补充材料要求](https://iclr.cc/Conferences/2027/AuthorGuidelines)

## 7. 真正按下发布按钮之前需要确定的事实

- 两篇已确认单一作者 Shengwei Zhang、机构 University of Pennsylvania；仍需填写平台要求的联系信息，并核实既有论文是否满足 ICLR 审稿资格。
- 论文所有主结论均有正确证明或真实结果支撑；没有把计划、模拟或示例误写为真实部署实验。
- 数据／模型许可、公开数据来源和私有经历边界已确认；代码和论文中不含内部标识或未授权材料。
- arXiv 账户与 endorsement 状态；真实 GitHub 用户／目标仓库；两篇各自的最终投稿路线。
- 公开 PDF、LaTeX 源文件包、匿名 PDF、补充代码 ZIP 均已实际编译或运行验证。

如果证据尚不足，继续做研究比用更强措辞包装现有结论更有效。arXiv 要求可供学术审查的科学贡献；顶会稿件需要完成度与创新性。排版完整、章节齐全和真实研究完成是不同的检查项。[arXiv Submission Guidelines](https://info.arxiv.org/help/submit/index.html)、[ICLR 给首次投稿者的说明](https://iclr.cc/Conferences/2027/CallForPapers)

## 8. 当日补充核验：SaTML、TMLR 与实证完成后的判断

**SaTML 2027 已公布正式 CFP**，最近更新于 2026-09-09。它直接覆盖可信机器学习与算法验证，是 Base-Model 稿值得认真评估的并行路线选择。以下均为 23:59 AoE：[官方 CFP](https://satml.org/call-for-papers/)

| 事项 | AoE 日期 | 纽约时间 | 北京时间 |
|---|---|---|---|
| 必须先注册摘要 | 2026-09-22 | 09-23 07:59 EDT | 09-23 19:59 |
| 全文 | 2026-09-29 | 09-30 07:59 EDT | 09-30 19:59 |
| 匿名 artifacts 更新期限 | 2026-10-02 | 10-03 07:59 EDT | 10-03 19:59 |

Research 与 SoK 正文上限 12 页，IEEE 双栏 10pt；SoK 必须有系统化分析与新见解。全部作者须在摘要截止前完成 ORCID 与 Author Certification。论文要求 Open Science 段；用过 LLM 的论文要求真实的 LLM usage considerations。允许预印本，但审稿材料和关联仓库须匿名。若另一会议仍在审，可以注册 SaTML 摘要，但交全文前须已拒稿或撤回；不能同时向 ICLR、SaTML 提交同一篇全文。接受稿还需公开固定 artifacts，具体要求以上述 CFP 为准。

**TMLR 可以滚动投稿**，稿长按内容合理性判断；允许署名预印本，但提交版本与补充材料须匿名，补充文件上限 100 MB。因此完整梯度数组不宜直接塞进其补充 ZIP，应准备代码、紧凑结果及可复现下载／生成说明。其接受标准是证据可靠且对部分研究者有可传达的价值，不强制每篇提出新方法，也不意味着简单复现或缺乏深入人类参与的成稿自然可以接收。[作者指南](https://jmlr.org/tmlr/author-guide.html)、[接受标准](https://jmlr.org/tmlr/acceptance-criteria.html)

**WMT 2026 已不接受新研究稿**：全文在 8 月 7 日、ARR commitment 在 8 月 28 日结束；9 月 11 日是 camera-ready 截止。未来 WMT 届次须另查官方征稿。[WMT 2026](https://www2.statmt.org/wmt26/)

第 3 节是根据原稿主题所作初步匹配。完成数学修复和公开实验后，更具体的准备度评估见 [审稿人视角](../docs/reviewer_readiness_zh.md)：A 的诊断性贡献与 B 的认证流程都可继续发展，但不能把当前证据包装成已经成熟的顶会结论。具体优先级应同时考虑真实贡献、补强证据、作者资格与匿名投稿要求。

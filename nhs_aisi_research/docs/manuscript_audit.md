# 最终论文科学内容审计

审计时间：2026-09-11T21:58:53.639912+00:00。范围为新项目 `nhs_aisi_research/`；旧三篇论文及其发布包未修改。审计以当前正文、扩展段落、技术补充、实际 CSV、生成机制和独立数值实现为依据，不把草稿中的陈述自动当成事实。

**结论：在已检查范围内，未发现会推翻主要结果的数学、数据规模、时序泄漏、实验计数或结果转录错误。** 已报告的小数舍入和功能边界问题均由主任务修正后复核。全文的成立范围是固定模型下的理论、真实记录上的人为采样回放、以及 NHS 聚合数据的条件示例；并无现实招募试验、机构合作、健康效果、全局最优或录用保证。本审计由单独的 AI 工作任务完成，含独立实现，不能替代具名作者审阅或外部同行评审。

## 1. 本轮修正及状态

| 检查点 | 原问题 | 复核状态 |
|---|---|---|
| synthetic validation spending | β=.70 的精确比例为0.9164583333，正文曾写0.917 | 当前三位小数0.916正确 |
| overestimated-bias baseline | ordinary KG regret 为0.0588464302732422，正文曾写0.0589 | 当前四位小数0.0588正确 |
| NHS 初始优先级 | 实际按 KG/cost 排序，依赖 packet=20、ordinary cost=1、validation cost=5 | 正文与补充现均明确这些条件 |
| replay 成本网格 | 仅 unweighted uniform 与 unweighted tilt-.50 扫成本2/5/10 | 正文限定清楚；其余三场景仅成本5 |
| 同行动集合比较 | validation-only 不能获得 ordinary packets | 当前与两通道KG/等行动随机/成本平衡随机区分，标为受限对照 |
| 停止/不测量 | 现有算法一直分配预算至无可负担行动，未优化是否测量 | 当前社会影响段明确为给定预算分配，不声称价值停止规则 |
| 第二渠道严格占优条件 | trivial quota 时两行动KG都为零 | 正文已补 nontrivial group quota，完整命题原本已有 |

## 2. 模型、损失与时序

- 固定组内配额下，按后验目标均值选最低项是期望线性的结果；该终端决策不要求目标独立。KG 的单坐标闭式则要求一次观察只改变该单位的后验均值，不能无条件用于共享状态/共享超参数更新。
- 一步价值使用“其他单位中第 k 小”的边界。已入选单位的替代边界是全组第 k+1 小，不是第 k 小。公式是正态正部期望，并除以全体固定名额 K。全局常数1/K可在行动argmax中省略，但不可据此改成每组等权损失。
- Gaussian innovation SD 是可被当前行动改变的后验均值的标准差，不能与剩余目标SD混淆。2×2 Gaussian更新、相关项和ordinary/validation loading与正文一致。
- 无限ordinary重复后的目标方差下界和两单位独立先验下的Bayes regret下界正确；共享组偏差在固定组名额损失中抵消，因此非零水平不确定性不等于排序损失。
- 第二验证渠道无偏是模型条件。独立但持续有偏的第二渠道仍留下正后验方差；KG/cost与variance-reduction/cost不同，也不保证固定预算全局最优。补充的成本反例0.325735 versus0.380377计算正确。
- 初始数据对所有政策相同，预算只计新增packet。每次选择检查可负担性，更新后重算边界；validation-only可留末尾余款。主算法不包含真实时延/成本货币估计，也没有价值停止规则。
- target_drift仅在共同初始观察之后、全部新增测量之前发生一次；此后目标静态。正文没有将它误称持续在线随机漂移。heteroscedastic stress的单位/replication固定SD乘数为exp(N(0,.4²))，推断仍用共同SD；它不是每次packet重新抽乘数。heavy-tail stress在packet层直接抽标准化t3，并非20个个体t3的均值。补充描述均匹配实际代码。

## 3. 实验规模与全文数字

实际主Gaussian CSV为24个参数/成本/预算设置×10政策=240行；七个stress×10=70行，合计310。24个主设置只重用四组各2,000个潜在世界，即8,000个独立主世界；另有14,000个stress世界。不能将所有政策或成本格当成独立世界。

主replay为五个采样场景，每场景1,000次有限文件采样重复。两个unweighted场景各3成本×2预算、其他三个各1成本×2预算，共18设置×10政策=180行。它们不代表180,000个新受访者、多个独立当前年份或五份独立人口样本。2024有限文件始终固定。

三个compact-grid表的每个表头、设置及政策顺序均与CSV对应；**240+70+180=490个均值逐格按四位小数核对通过**。正文的所有主要regret、paired interval、MSE、validation spending与CSV核对一致，包括：

| 条件 | ordinary KG | two-channel KG | 含义 |
|---|---:|---:|---|
| Gaussian β=.15, B120,c5 | .080440 | .086215 | 两通道更差；paired增加.005775，95% MC区间[.004223,.007327] |
| Gaussian β=.35, B120,c5 | .154137 | .136413 | 两通道更好 |
| Gaussian β=.70, B120,c5 | .250261 | .174288 | paired差−.075974，区间[−.080319,−.071629] |
| 主replay unweighted tilt.50,B144,c5 | .161456 | .185671 | 两通道更差；paired差+.024214，区间[.021239,.027190] |
| weighted tilt.50,B144,c5 | .177299 | .195876 | 加权有限文件目标，非人口估计 |
| validation自身tilt.25,B144,c5 | .161157 | .222585 | 独立符号不使第二渠道无偏 |

unweighted tilt.50 的MSE从.021830降至.021288而regret升高；weighted的MSE从.022501降至.021938而regret升高。正文正确将其解释为完整政策在不同损失函数上的描述性结果，没有声称唯一机制或因果分解。

## 4. 追加预算分析

`extended_content.tex`与当前正文都明确它在主结果之后设计，并在其自身执行前记录方案。独立seed、500次重复、五政策、四预算，20个结果格全部保留；并未替换主replay的1,000次结果。

B1440下two-channel regret=.090698，ordinary=.124217，paired差−.033518，区间[−.037933,−.029103]。B48/144/480下两通道仍比ordinary差。B480和B1440两通道KG将100%新增预算投向validation，故不能将最大预算改善归于成功混合两渠道。B1440下validation-only也花满预算且regret=.122878，其与KG的差异才体现同一validation渠道上选单位的分配区别。所有这些数字均与扩展CSV相符；没有据有限网格宣布准确cross-over阈值或普遍长预算优势。

预算1440等于48区域平均30个ordinary packet成本，或288个validation packets；每packet20次记录draw，不是288位、5,760位唯一受访者或实际完成招募。主材料对人工成本和采样假设的限制明确。

## 5. BRFSS来源、目标和信息隔离

2023与2024原文件分别433,323与457,670记录；全地区employed/self-employed分别215,794与225,524；有效心理不健康天数分别212,989与222,734；共同47州+DC主分析为206,098与214,151，总420,249记录。主区域最小/最大样本2023为1,247/13,474，2024为1,232/22,708。地理与清洗计数均匹配数据审计和CSV。

MENTHLTH=88映射0天，1–30有效，77/99/blank排除；EMPLOY1=1/2。health=(30-days)/3不是NHS burnout，也不是临床诊断、工作导致的健康或州人口患病率。权重字段为_LLCPWT。原始2024XPT与ASCII全部记录核查、四条Illinois核心/派生类别矛盾保留原核心、ASCII权重舍入最大差4.9965e-5的表述准确。

主目标是完整有效就业记录的非加权有限文件均值。加权敏感性把记录按原权重概率抽样并以完整加权分布均值为目标，不使用uniform子样本ratio来声称无偏人口估计。保留stratum/PSU不产生复杂抽样设计校正；Kish数仅是权重集中度。

2023常数μ=8.556929、τ=.138816；weighted μ=8.413416、τ=.144356；两个unweighted tilt下平均bias SD=.686502/1.495180，全与240行calibration独立重算一致。2024仅是采样环境与最终evaluation。算法看到初始/已获得的packet均值和冻结2023标定，不读取隐藏当前年均值、实现偏差或全文件variance。控制招募生成器必须知道记录值才能实施人为tilt，这不等于policy能看到隐藏目标。

计数依赖结果的自适应抽样会影响最终empirical mean的无偏性；补充准确区分固定长度iid primitive packet mean与最后的自适应/收缩估计。覆盖率是all-unit边际覆盖比例在重复实验上的诊断，不是选中条件下或全部同时覆盖，更非现实人口posterior保证。

## 6. NHS条件示例的独立复算

本轮不调用`Belief`、`thresholds`或`gaussian_improvement`，逐单位使用通用2×2矩阵条件化、显式排序其他单位、独立Gaussian正部公式，重新计算全部190×8=1,520行。

验证：posterior mean最大误差8.88e-16，posterior SD9.72e-17，两通道KG及per-cost最大误差约1.00e-16；所有选集、preferred channel及action priority rank逐项完全一致。原始输入有190 reporting units、189 legal entity codes，group sizes110/43/13/13/11，配额22/8/2/2/2，总36；2025 nominal burnout n中位数3140.5。

八个条件下top20 validation数分别为f=1时[0,20,20,20]，f=.25时[0,15,20,20]，β顺序[0,.15,.35,.70]。所以正文“15 versus20”不是描述性笔误。该状态使用2025组均值plug-in、假定τ=.35与个体SD2.5，名义n乘数不估计ESS。没有新NHS样本或干预结果，也未用历史多次得分伪装独立新增packet。它是条件敏感性说明，非前瞻验证或真实人员名单建议。

## 7. 引用、创新与社会影响边界

正文、扩展和理论片段共有20个被引用键，全部在references.bib定义，没有缺失引用。理论文献的原始来源逐项审计复用`docs/theory_prior_art.md`；AISI/NQPS的publisher/source证据复用`docs/domain_and_aisi.md`与`docs/domain_source_audit.json`，已与负责独立代理确认无未决元数据问题。尤其MISO2017是直接先例，Ao2026仍按原始v1预印本标题与身份引用，没有伪造会议发表。Health-service ranking背景不承担本项目的因果或部署结论。

全文明确KG/MISO为既有方法，边界heuristic不是LUCB，不声称固定预算最优、首创两渠道或首次发现有偏重复不能识别。NQPS全员机会、engagement与annual burnout差别、招募负担与confidentiality均留有明确边界。提及已有AISI实证论文没有冒称其合作或干预证据属于本项目。

引用验证不是截至2026年的系统综述；统计一致性也不保证AISI认可贡献强度。当前主要外部效度限制仍是：只有一个holdout记录年份、construct/domain差异、人工且部分已知的招募law、无实际reference渠道、无NHS stakeholder co-design或前瞻评价。文稿现已主动披露这些限制。

## 8. 机器验证记录与审计快照

完整verifier stdout已保存为`results/implementation_verification.json`；状态为passed，运行时间2026-09-11T21:49:53.913194+00:00，34项保护源/结果在运行中未变。该JSON SHA-256为`8523928cc14795ff42866894c58c4bbc776d2c93a12758d20c6f80cd0494cd6f`。本轮没有重跑整套主实验；只运行有界独立实现审计及NHS逐行复算、表格核对。六条synthetic路径的数学近并列分支已公开，不能夸称所有不同浮点实现逐位重放相同路径。

以下是审阅时文件身份；随后纯排版修改应另记，不要求篡改原实验执行快照。

| 文件 | 审计时SHA-256 |
|---|---|
| `paper/main_content.tex` | `757726bb448c26efed4dfce7921931fb3013c63cc82b7e2ababb4f1dee2dac97` |
| `paper/extended_content.tex` | `025a6656ceb09ee112a8616a0e1259c6ea886e9e8a5e163ca217cb224c3c4b90` |
| `paper/supplement_content.tex` | `2cddb6c573dbf01df72818f9b019878488687c0ab10e83a3324f8d23b206c689` |
| `paper/theory_sections.tex` | `1a51c9285b5c5d878bd1a56db2f8ccb92a9b9412f13343a64aef76ddc32f3232` |
| `paper/theory_proofs.tex` | `3559af3b4310a78bbe6b659c936084ebdf227bb54bae6fadd9caa3fe124df37a` |
| `paper/tables/compact_grid.tex` | `fa14de447a962c0b80f75c4568f9f41be2bd72843c88c4bdb384a77ecd822d33` |
| `results/synthetic.csv` | `3162608c221d187919257899e26cf43089f24ec98e6a7a81f3d986018c9d677a` |
| `results/synthetic_stress.csv` | `6ad80c383a2ba9be4b9f4dc12a18fc04dea829cd129651b9b56187eb5a61fae0` |
| `results/replay.csv` | `f70ce7987dfeac1d4f9eab9ada6452ec757aa67867b90d89c2441071998bd629` |
| `results/replay_budget_extension.csv` | `b9bfb084660745bd4e99cdf248c36e3e7aa1659f1e08e3433ada32b39d3dc5c3` |
| `results/nhs_scenarios.csv` | `34ff6adf8e5649539d5924ac84d3da09c7b084cbfea6dc5954ce11e4cedf90c5` |
| `results/nhs_scenario_summary.csv` | `bdd93b42a0aeae3662f63b7d7bb53b4a081b0815e2b990a2387ab5dcdd04119b` |
| `results/implementation_verification.json` | `8523928cc14795ff42866894c58c4bbc776d2c93a12758d20c6f80cd0494cd6f` |

PDF视觉、匿名性、格式页数、最终ZIP可恢复性与作者提交声明由各自发布检查负责。本文件不代表已上传arXiv、已投稿或已获准公开任何外部系统。

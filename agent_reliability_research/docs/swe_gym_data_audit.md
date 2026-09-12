# SWE-Gym 下载、分组与廉价代理审计

2026-09-12 完成。仅下载与解析公开材料，未运行任何轨迹里的命令、patch 或 Docker。此处数字是实际本地计算结果。

## 数据实际可用性

[官方数据](https://huggingface.co/datasets/SWE-Gym/OpenHands-Sampled-Trajectories) 固定 revision 为 `baf3a4e4bff514d48ddc08a93a2ade5c126212c7`。三片实际总计 301,095,609 bytes，全部与官方 API 提供的 LFS SHA-256 一致；逐文件 URL、字节数、校验值及 UTC 获取时间均在 `data/swe_gym/source_manifest.json`。没有填补、合成或重标注记录。

共有 6,055 条轨迹、2,438 个任务 ID；按 canonical messages + 最终 patch 做精确去重，重复数及冲突标签数均为零。这不代表已排除工具调用 ID 不同而行为相近的语义重复。原始标签中成功 491 条，empty-generation 标志 2,380 条。28 evaluator errors、7 failed patch applications、9 test timeouts 共 44 条保留在记录审计中，主要有效判定集合排除这些记录，剩余 6,011 条、2,421 个任务。没有把 empty generation 单独删掉来抬高成功率。

`run_id` 包含实际日志配置：GPT-4o 不同 temperature、30/50 次交互限制，以及 Claude。严格保持任务、日志配置及起始 prompt 一致时，每块最多 2 条，所以 G=4 和 G=8 **都没有可用组**。这项负面可用性结果保留在严格 `groups_g4.jsonl`、`groups_g8.jsonl` 和 `summary.json`，未被后续修订覆盖。

经过明确的可用性驱动协议修订，另建同任务、同起始 prompt 的 heterogeneous historical replay 组；不同日志模型与配置逐成员列出。每种组大小独立按内容哈希排序并切成不重叠完整组，未按成功标签或 mixedness 筛选。这些是固定经验组，不能称 on-policy GRPO 数据。

| 独立组大小 | 全部组 | 全部 mixed 组 | Heldout 组 | Heldout mixed 组 | Heldout 任务 |
|---|---:|---:|---:|---:|---:|
| G=4 | 453 | 106 | 99 | 33 | 50 |
| G=8 | 223 | 79 | 49 | 22 | 49 |

G=4 含 1,812 个成员、G=8 含 1,784 个成员；两种设置之间可复用轨迹，不应加总为独立样本。G=4 中 178 组跨日志模型，所有 453 组跨日志配置；G=8 中 178 组跨模型、全部 223 组跨配置。后续若只取 256/512 条做模型前向，必须再用与结果无关的固定组顺序选择并报告子集，而不是挑 mixed 或短且成功的组。

## 代理标签预测

在完整数据查看前，已指定按任务 SHA 划分 train/calibration/heldout，所有同任务轨迹共用 split。12 个输入只来自交互 `messages`：角色/工具调用/字符数量与 agent-visible tool output 中的测试状态词数量，全部取 log1p；没有将 `resolved`、`test_result`、最终 patch 或任务/模型身份列输入预测器。工具输出不等于官方标准 public-test split，更不等于新产生的审计标签。

按冻结配置使用 StandardScaler + L2 logistic regression，C=1、lbfgs、max_iter=2000，只拟合 train；没有用 heldout 做模型或超参数选择。初次成功运行环境是 Python 3.13、NumPy 2.5.3、PyArrow 25.0.1、scikit-learn 1.9.1、requests 2.34.2。模型参数与完整逐条概率都已保存。

| Split | 有效记录 | 任务 | 成功率 | AUC | Brier | Log loss |
|---|---:|---:|---:|---:|---:|---:|
| Train | 3,632 | 1,467 | 0.07627 | 0.80948 | 0.06442 | 0.22279 |
| Calibration | 1,131 | 468 | 0.06012 | 0.79510 | 0.05308 | 0.19479 |
| Heldout | 1,248 | 486 | 0.11699 | 0.81762 | 0.09193 | 0.29682 |

这些指标评估一个便宜代理，不证明预算审计方法有效；heldout 和 train 的成功基率明显不同，也不能把 AUC 等同于可靠校准。后续审计分配规则只能用训练和 calibration 信息调节。

## 字段字典与限制

| 输出字段／文件 | 解释 |
|---|---|
| `record_id`, `source_file`, `source_row` | 确定性分片名和行号，可回取原始 Parquet 消息，不需另存全文副本。 |
| `instance_id`, `split` | 原始任务标识与本研究任务级划分；不是原作者 train/test 声明。 |
| `run_id`, `behavior_config` | 完整日志标识，以及仅移除末尾重复运行号后的描述；温度、模型和步数信息保留。 |
| `content_sha256` | canonical messages 与最终 patch 的完整联合哈希，含原始工具调用 ID。 |
| `initial_prompt_sha256` | 第一个 assistant 动作前所有消息的 canonical 哈希。 |
| `resolved`, `report`, `eligible_evaluation` | 原始成功标签、评测状态与冻结排除规则；没有推断新标签。 |
| `counts`, `features` | 交互文本与动作计数，以及对应 log1p 代理输入。 |
| `runner_reported_seconds` | 最终测试输出的文本时间匹配，可能多段，不能直接当完整成本。 |
| `proxy_predictions.jsonl`, `proxy_model.json` | 每条有效轨迹的固定预测值、模型缩放和系数。 |
| `heterogeneous_groups_g4/g8.jsonl` | 固定经验组索引、全部成员配置、标签和代理概率，明确不是同策略采样。 |

assistant turns 的中位数为 14，95 分位为 50；全文／工具动作字符数中位数 41,249、95 分位 173,178.8。这些不是 tokenizer 长度。很多 assistant.content 为 null，实际动作存放在 tool_calls.function.arguments；后续梯度序列化不可把这些动作漏掉。完整长轨迹截为一个上下文窗口后，只能称明确窗口与参数子空间的梯度诊断。

没有专用成本或时间元数据字段。3,219 条 test_output 含 `in ...s` 文本，可能仅对应 pytest 或部分步骤；不能涵盖容器启动、排队、完整审计和整条 rollout。离线 query counts 不能直接变成 CPU 或端到端训练提速。

官方数据卡未声明明确的 dataset licence；不能从某个代码仓库的 MIT 许可推断整个轨迹和底层仓库代码都可重发。当前原始 Parquet 留作本地缓存。发布前应将 raw 和 tokenizer/model caches 排除在源码 ZIP 中，保留获取脚本、manifest、确定性索引与适当的派生数值。

## 复现与独立验收

在安装相应依赖的本地常驻 Python 环境中，从仓库根目录运行：

```sh
python experiments/swe_gym_data.py --fetch --parse --fit-proxy
python experiments/swe_gym_historical_groups.py
python experiments/verify_swe_gym_data.py
```

最后一个校验仅依赖 Python 标准库：检查原始 LFS 哈希、初次协议/脚本快照、无任务泄漏、严格块最大长度、组内元数据与标签、成员唯一性和当前 manifest。并且独立按保存的 scaler 和系数重建全部代理概率，最大误差 2.78×10^-16。验收结果为 `processed/validation.json`。

初次计算协议和脚本位于 `provenance/initial_strict_run/`。实际 run ID 使用 `-run_1`，而首版正则仅接受下划线分隔；后续只纠正描述字段并记录在 `metadata_correction.json`，标签、特征、概率、task split 和组成员不变。修订后的 parser 对全新复现会直接产生正确描述。用于该 metadata 修正的辅助脚本不是新实验，不应重算或选择结果。

旧 workspace `.venv` 曾因 macOS dataless 按需文件状态导致导入迟缓；没有修改用户 iCloud 设置。初次统计确已完成并保留原环境版本。校验和最终分组用本地常驻 bundled Python 完成，未再次拟合模型或改动科学输入。


## 已补充的实际 tokenizer 统计与模型输入

随后按另行冻结的 `swe_token_protocol.md` 完成全部6,055条的实际 token 计数。明确 role-header/body 分块 BPE 后，全文 token 中位数12,645、95分位52,052.1、最大170,387；这不是日志模型的原生token计数。全部49个heldout G8组、392条记录的最后一个非空assistant body已按1536 context/512 target规则生成NPZ，0条缺target。原有数据、分组与代理数值未改；新增 `token_lengths.jsonl` 和 `token_artifact_manifest.json` 保存逐条截断量与元数据。tokenizer记录与文本工具参数包含规则详见该协议；仅target被预测位置评分，模型前向和梯度由主实验另行进行。

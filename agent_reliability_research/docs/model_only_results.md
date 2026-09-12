# 模型内生调度后续实验：完整结果与独立验收

结论是有条件的。免真实标签调参的模型内生调度，在正确模型机制中优于整组残差抽查，但错误模型特别是反向漂移可显著增加方差。它没有推翻首次实验计入校准费用后无胜出的负结果，也没有建立训练质量或总运行时间优势。

## 设计与数据

运行前协议是 `docs/model_only_protocol.md`；新种子 20260914 是随机数标识，不是执行日期。实际执行时间为 2026-09-12 16:30:04–16:31:38 UTC，wall 93.71 秒，CPU 92.18 秒。45 个基础条件×3预算=135 设置；每个基础条件256组，因此共有11,520个唯一组、107,520个离线真实reference标签；三个方法与三个预算在相同组上配对评估。没有新增调参真实标签；概率模型直接由模拟机制提供，不曾从校准labels拟合，所以不能称其获取成本为零。

三种方法均用相同模型completion；`whole_group_cv` 用相同预期标签成本概率买全组，`rr_fixed` 用固定指数1，`rr_model` 由模型内的 sign-split coefficient Euclidean 增量方差及PAVA决定。p、cost决定顺序和Q；真实r、真实生成概率只用于评估。NPZ的r和oracle path不属于在线policy输入。每组穷举G+1个停止深度积分，故审计期望没有Monte Carlo误差；256个随机组仍有抽样误差。

所有135设置、所有组与零优势组都保留。base_rate_parameter是logistic-normal截距参数，不是实际成功比例；原始NPZ另存true_probability，CSV同时给realized_success_fraction与true_probability_mean。每行完整组查询概率是Q_G；预算是上界，实际成本是Q·c，实际标签数是ΣQ。

## 完整网格的描述性结果

下列比值均为每设置先对256组平均，再在各机制45设置取中位数；小于1表示rr_model更低。胜数只按点估计计数，不是多重检验后的显著性声明。三个预算共享组，不能把135设置当作135个独立重复。

| 对照 | 机制 | coefficient MSE比值 | 胜数 | 固定6维映射MSE比值 | 胜数 |
|---|---|---:|---:|---:|---:|
| whole_group_cv | calibrated | 0.747918 | 45/45 | 0.726283 | 45/45 |
| whole_group_cv | overconfident | 1.021451 | 18/45 | 0.983905 | 26/45 |
| whole_group_cv | shifted | 2.242589 | 0/45 | 1.898104 | 0/45 |
| rr_fixed | calibrated | 0.879394 | 43/45 | 0.878373 | 44/45 |
| rr_fixed | overconfident | 0.902679 | 37/45 | 0.912911 | 36/45 |
| rr_fixed | shifted | 0.955070 | 29/45 | 0.965437 | 28/45 |

相对whole_group_cv，全135设置的coefficient胜数63/135，中位比1.021451；固定6维映射胜数71/135，中位比.983905。最差shifted设置的coefficient和映射比值分别为6.678406、6.293374。相对rr_fixed的全网格胜数109/135与108/135，中位比.907246与.921481。不存在全面优于强基线的证据。

全部103,680方法行的最大条件coefficient偏差平方仅2.9376e−30。因而错误模型的损失是方差增加，不是无偏纠错失效。正确模型下的最优性是对标签分布求期望的Euclidean模型risk、给定顺序；不保证每个固定标签向量更低MSE，也不保证固定随机6维映射的最优性。有限256组下少数coefficient点估计不胜rr_fixed不违反该理论。

## 计算与标签成本分别核算

| G | 方法 | 平均调度CPU(ms) | 平均预期completion CPU(ms) | 二者合计(ms) |
|---:|---|---:|---:|---:|
| 4 | whole_group_cv | .0016 | .0759 | .0775 |
| 4 | rr_fixed | .2099 | .1895 | .3994 |
| 4 | rr_model | .4180 | .1869 | .6048 |
| 8 | whole_group_cv | .0018 | .1755 | .1773 |
| 8 | rr_fixed | .2123 | .8498 | 1.0621 |
| 8 | rr_model | 1.0855 | .8303 | 1.9158 |
| 16 | whole_group_cv | .0024 | .5469 | .5493 |
| 16 | rr_fixed | .2182 | 5.2815 | 5.4997 |
| 16 | rr_model | 5.2374 | 5.1402 | 10.3776 |

这是共享macOS机器上的单次Python微基准。`total_algorithm_cpu_seconds`字段是调度与预期completion两个已计时组件之和，**不包括**实际oracle执行、在线随机数/累加的少量bookkeeping、predictor训练或推理，也不是完整训练wall time。raw保存CPU与wall计时。whole-group买全后直接计算Φ，不为它虚增中间completion。RR的moment每组只算一次、三预算复用；比较每个独立预算时保守收费一次完整moment，原始共享时间也保留。全组最大标签成本G，不能以较小的预期成本声称每次都不超过budget。

## 实现修复及独立验收

发现并修复了真实数值错误：旧PAVA在Σv≤1e−15时把非零方差当成全零，违反共同正缩放不改变最优解的性质。对v=1e−20×[1,.01,.001]、cost=[1,1,1]、budget=1.2，旧返回[.4,.4,.4]；修复后[1,.1519493853,.0480506147]。改为只有精确全零走均匀解，其余先除max(v)，并显式处理正方差部分饱和、零方差尾部保持floor留下预算slack。例v=[1,0,0]、budget2、floor.01返回[1,.01,.01]，实际cost1.02，符合≤预算的最优条件。

修改前source快照、前后SHA、例子存 `results/model_only/implementation_fix_validation.json` 和 `source_snapshots/reward_audit_before_scale_fix.py`。新增4项测试加原5项测试全部通过，包含G2–8/G16与独立全cube矩计算、16个SLSQP约束优化对照、1e−100到1e100尺度不变性和退化边界。修复后的执行source SHA为 `fd68931e2378033d106d10408b6ab08cd64fff32e6f3e9d38d4a114b9e2c7423`。

`experiments/verify_model_only_study.py` 独立重算所有103,680行成本、尾概率和标签数，成本最大差为0；whole-group系数MSE闭式(1/q−1)||Φ−μ0||²全部通过，最大差2.14e−14。另对保存的G4 shifted、G8 calibrated、G16 overconfident各第0组，以完整16/256/65,536标签配置独立重算completion路径和model moments，再手工累加所有停止深度，无调用主metrics函数。最大路径误差1.96e−14、矩误差4.14e−14、MSE误差4.27e−14。所有原始study manifest列出的SHA均匹配；结论存 `results/model_only/independent_validation.json`。

验收脚本首个尝试因文件名`.2`而不是`0.2`在选定组读取处报FileNotFoundError，未改任何研究结果；修正路径并缓存NPZ数组后，完整独立验收1.76秒通过。这个错误只影响验收工具，不影响主实验。

## 文件与复现

主结果目录 `results/model_only/` 含45份NPZ、`per_group.csv`、`summary.csv`、`paired_comparisons.csv`、冻结协议与执行源码快照、执行manifest、独立验收JSON。`experiments/model_only_study.py` 完整运行；使用`--output`新目录可避免覆盖冻结结果。`experiments/verify_model_only_study.py` 重算验收；`experiments/summarize_model_only.py` 从冻结CSV重建描述性汇总JSON。首次study及其成本问题仍在 `results/estimation/` 和 `docs/implementation_audit.md`，没有被替换。

补充理论的sign-split最高degree已通过G2–12全cube检验；独立对query_spectrum的G2–7全部subset直接求product-basis内积，误差4.45e−16。uniform的unclipped contrast在G4/8/16、cap=G/2下的相对尾能量分别.00512834/.000376773/1.46136e−6。高degree仅说明精确点态无偏的硬门槛，不说明有用近似一定需要大量查询，也不说明给定均值函数的低方差估计容易。

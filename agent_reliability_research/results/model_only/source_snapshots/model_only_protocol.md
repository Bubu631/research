# 模型内生调度扩展：运行前冻结协议

本扩展是在首次实验发现真实标签校准收费会消除所观察到优势之后设计。它是明确的后续研究，不取代或改写 `results/estimation` 的初次结果；新的确认随机种子是 20260914。模拟提供的概率模型不是由本实验付费标签拟合得到，三个方法都能免费访问同一个已给定概率模型。因此本实验只比较给定模型条件下的审计，不证明获得该模型本身免费。

固定网格为 G={4,8,16}，base_rate_parameter={.05,.2,.5,.8,.95}，regime={calibrated,overconfident,shifted}，budget_fraction={.25,.5,.75}。共 45 个基本条件、135 个预算条件；每个基本条件 256 个独立组，所有三个预算与方法共享这些组。`base_rate_parameter` 是 logistic-normal 截距的参数，不是实际成功比例；保存每组真成功概率、实际成功比例以免误读。零优势组保留。

生成机制与原研究一致：z_i~N(logit(base_rate_parameter),1.2²)，p_i=sigmoid(z_i)。三个机制真概率依次为 sigmoid(z_i)、sigmoid(.45 z_i)、sigmoid(-.65 z_i)。条件独立生成 Bernoulli 标签。cost_i 为 lognormal(0,.55²) 后除组内均值，总完整标签成本为 G。score_i 为独立六维标准正态；ratio_i 为 exp(N(0,.25²))。固定线性映射为上下堆叠 score_i 1{ratio_i<1.2}/G 与 score_i 1{ratio_i>.8}/G。该映射只用于可复算的有限组线性更新诊断，不是实际语言模型梯度。

统一查询顺序按 p_i(1-p_i)/cost_i 降序、稳定打破平局。三臂为：`whole_group_cv`（以预算比例概率买全组，未查时用精确模型 completion）、`rr_fixed`（预先固定指数 1 的 survival）、`rr_model`（模型内生的 Euclidean sign-split coefficient 增量方差，固定顺序 weighted PAVA）。后两者正 survival floor=.005。三臂没有真实标签校准费。模型内生调度只读取 p 和 costs；真实标签和真生成概率只用于 oracle 目标及离线评估。不会看结果调参或丢弃不利设置。

每组对全部 G+1 个停止深度精确积分，不用审计蒙特卡洛。主指标为 coefficient MSE 与固定六维线性更新 MSE；报告每组条件偏差平方、实际预期成本 Q·c、实际预期标签数 ΣQ、完整组查询概率 Q_G、最大成本 G。理论预算是上限；零增量尾部可留下合法 slack。报告方法配对差值的标准误，而非把 3 个预算当作独立样本。

计算成本与标签成本分开：记录 order、F0 completion、每一步 completion、moment、PAVA/fixed schedule 的 CPU 时间和 wall time。三预算复用同一 moment；每个独立预算的调度时间保守计入完整 moment 时间，另保存共享的原始 moment 时间。whole-group 基线买全后直接计算 Φ，不必运行中间 completion。RR 的预期 completion CPU 是 F0 加 ΣQ_k times 单步 completion 计时；whole-group 为 F0 加 budget_fraction times 直接 Φ 计时。计时是单次 Python 微基准、受共享机器负载影响，不表示实际环境执行速度或训练提速。

保存每个基本条件 NPZ（p、r、true_probability、cost、score、ratio、linear、order、路径、moment、v、全部 Q、CPU/wall 计时），per_group.csv、summary.csv、paired_comparisons.csv、源文件快照与 SHA256 manifest。新脚本 `python experiments/model_only_study.py` 使用同一固定种子；可指定 `--output` 写入新目录。真实执行时间与论文显示日期分离。

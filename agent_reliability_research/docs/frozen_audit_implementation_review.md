# 冻结模型梯度度量审计：独立实现核验

本次只使用构造的p、查询顺序、线性映射L；没有加载正在提取的Qwen `gradient_bank.npz`，没有读取或改写最终frozen-audit结果。被审版本 `experiments/frozen_audit_study.py` SHA256为 `8d2329273d5fb2941d83f2834818a15f61cfff9e417db109c1bc43d4e18406c7`。核验脚本 `experiments/verify_frozen_audit_implementation.py`，结果 `results/frozen_audit_implementation_checks.json`。

## 数学与实现

`model_projected_moments(p,order,linear)` 对全部2^G二元配置按独立Bernoulli模型加权；每个k把配置按已见prefix pattern归组，先计算conditional projected mean，再计算其加权平方范数。因此它精确计算M_k=E_p||E_p[Φ(R)|H_k]L||²。这里conditional expectation与固定L可交换。v_k=M_k−M_{k−1}是该固定投影范数下的Doob增量二阶矩，适用于已实现的固定顺序PAVA目标。仅输入p/order/L，不读取实际gold。该方法枚举所有pattern，不依赖原来只按success count压缩的Euclidean公式，因而允许任意固定L及其非对角Gram结构。

独立实现没有调用主completion或moment helper：对每个已见prefix分别枚举未知suffix，显式计算未知标签概率、Φ及conditional mean。G={2,3,4,6,8}，各测试任意随机L、ratio=1形式的stack(score,score)/G、p含精确0与1，共15案例。所有完整标签向量的G+1个停止深度也独立积分。

- root moments与独立conditional枚举最大差2.85e−14。
- 模型平均投影MSE与Σv_k(1/Q_k−1)最大差4.27e−14。
- 每个固定r的投影条件偏差平方最大4.68e−30。
- 主metrics与手动投影MSE最大差3.64e−12，出现在floor=.005的退化概率案例；处于浮点累加尺度内。
- 将L整体乘1e−8，最优Q最大变化1.45e−15；修复后的PAVA不再因绝对方差量级改变解。
- 全部Q正、非增，实际ΣQ不超过预算；正确报告Q_G作为完整组查询概率。

## 真实诊断的明确边界

当前真实诊断L=stack(score,score)/G，policy ratio固定为1。于是正负分量相加就是普通group advantage；**没有实证触发PPO clipping**。它检验冻结历史轨迹的指定32维logit-bias线性更新，不是native或full-parameter梯度，也不是on-policy policy-gradient估计。Φ的较高query-degree定理依然数学成立，但不能把ratio=1这个投影实验宣称为高degree clipped-vector理论的专属实证；特殊投影会抵消高阶项。

额外预测模型、冻结score均为调度前信息，所以gradient-metric调度不新增gold校准标签。这不意味着获取模型、score bank或调度本身没有计算成本。`model_moment_seconds`使用perf_counter，记录的是一次moment计算wall time；每组该值在3预算中重复保存，表示同一预计算被复用，不能相加当作3次真实执行，也不是完整scheduler CPU或端到端时间。它不含PAVA、所有online completion、实际测试执行和冻结模型前向。

## 49任务的bootstrap和成本统计

直接检查当前processed metadata：49个heldout组、49个唯一instance_id、49个唯一group_id，392个唯一record。因此以49任务为配对重采样单位符合当前数据层级，不能把392条记录当独立任务。每次bootstrap共同重采样方法与whole-group的task index，取两个均值的比，算法正确；不是逐任务比值取均值。

构造49个正分母任务，使用主研究指定seed20260916、10,000次配对bootstrap；前50次与逐项手算最大差1.0e−15。a=.5b的控制例全部返回比值.5。由同一10,000组索引形成各方法各预算区间可保持配对关系，但不会自动获得同时95%覆盖。它们是条件于此历史任务集合的描述性percentile区间；无随机代表性任务抽样，不能声称对所有软件项目的严格总体覆盖。组内审计期望是精确积分，task bootstrap本身仍是有限Monte Carlo重采样。

unit cost下ΣQ是真实预期缓存verdict揭示数，full/whole/fixed/model/HT的ledger都与设计匹配。HT及partial的完整组揭示概率正确为budget^G。预算约束是期望而非每次硬cap；某次可购买全部8条标签。成本只计缓存reference verdict揭示，不代表重新运行软件测试的执行成本或wall-time提速。

建议最终真实运行前加入防错断言：group/task唯一；bank IDs与heldout record IDs集合相等且scores均有限；各方法与whole的group_id顺序一致；whole平均MSE及所有bootstrap分母严格正，否则把比值标记为不可定义并记录原因，不能悄然输出NaN或删除不利replicate。当前输入的49/392唯一性已实际通过；最终bank的数值与分母需等真实运行完成后再检查。

## 正文和证明核对

`paper/sign_degree.tex`以及`paper/proofs.tex`的最高Boolean degree、有限差分对称抵消、偶数阶严格正性、decision-tree门槛、固定r交叉方差项、model martingale方差、count-compressed moments和PAVA范围均未发现科学错误。主文已经正确区分vector Φ和特殊scalar/linear projection的抵消，也说明高degree不代表有用近似必然困难。

需明确一个无偏定理的规则：每个completion map必须是X和已见prefix的固定函数，或只用与审计随机数独立的辅助随机数；不能另外依赖决定停止的U。否则对固定r，D_k可与I_k相关，逐项期望不再自动消去Q_k。现有实际实现符合该要求，但“any completion sequence”的表述应加此限定。若允许模型p=0或1且实际gold违反模型，条件期望在零概率prefix上未定义；可以明确采用把已见坐标clamp、其余坐标保留原Bernoulli概率的扩展定义，或理论先写0<p_i<1。此点不影响全为内点的当前proxy输入。

## 最终真实bank及审计结果验收

在构造核验之后，完整392×32真实冻结score bank与最终frozen-audit结果已完成。新增独立脚本 `experiments/verify_frozen_audit_results.py` 不导入任何主estimator、completion、moment或path函数，直接从真实bank、组文件和保存的Q出发，用数学定义重建结果；结果保存在 `results/frozen_audit/validation.json`。本节是后续最终验收，不追溯改变前述构造审计的时间和范围。

核验bank所有值有限、392 IDs与49任务的392 records完全匹配。每个任务直接枚举256标签cube，计算模型权重并条件于实际prefix重建全部9个completion，核对target；因此不只是抽查三个任务。全部8方法×3预算×49任务=1,176行被独立复算，包括两种非线性normalize方法的全部256 masks、四种残差方法的全部9停止深度、full和proxy completion。

独立值与保存CSV最大绝对差：coefficient MSE为4.98e−14，projected MSE为1.74e−18，coefficient bias平方为2.40e−14，projected bias平方为5.43e−19；成本和完整查询概率误差精确为0。所有49任务、三个预算whole-group闭式projected MSE误差≤8.68e−19。HT与partial的full-group概率均正确为budget^8，所有Q成本按ΣQ且不超过预算。

预定索引0、24、48三个实际任务（含all-zero以及3-success混合组）另对所有可能prefix重建完整Euclidean和projected M_k，并以独立SLSQP约束求解检验两种model schedule、三个预算。18个优化比较全部成功，归一化目标最大差2.46e−11；可复算的moment向量、target范数和每个优化差值均保存在validation JSON。

24条汇总的平均/标准误最大误差3.56e−15。重建seed20260916的10,000次任务级配对bootstrap，对所有8方法及三个预算的ratio及percentile区间最大误差4.45e−15。没有零分母，最小bootstrap whole-group平均MSE为2.101559079e−5。原manifest的source SHA全部匹配；六份输入bank/组文件/manifest/CSV/schedules在核验前后逐字节不变。核验脚本SHA为 `6278101123e4e2fd70b209fd74947aa45278041391b3219bb020f0400f7367b8`，bank SHA为 `5074caf1858e1d60c02f4ab2f433792c7048641ebad0f62fb3453a572dcf3fca`。

### Five-sentence interpretation

Across 49 historical tasks, coefficient-based scheduling attained projected-MSE ratios of 0.831, 0.759, and 0.683 relative to whole-group correction at budgets of 2, 4, and 6 expected label reveals per eight-trajectory group. The corresponding pointwise 95% paired task-bootstrap intervals were [0.684, 0.992], [0.547, 0.996], and [0.348, 1.119]. These intervals do not establish simultaneous significance across budgets. Gradient-metric model scheduling gave smaller gains, which is compatible with misspecification of the completion model. This fixed historical 32-dimensional logit-bias diagnostic uses policy ratio one and demonstrates neither active-clipping behavior nor improved policy training.

# 当前版本 verifier correction 对照

完整复核、作者、具体章节与判断见 [最新版本审计](latest_noise_correction_audit.md)。本文件提供供正文使用的紧凑对照；检索日期 2026-09-12。

| 项目 | Noise-corrected GRPO v3 | Cai 等 v4 | 本项目实际目标 |
|---|---|---|---|
| 版本 | 2026-05-19 | 2026-05-22 | 固定完整有限组 |
| Normalization | 明确 affine invariance；oracle σ 下 exact，实际 sqrt(Z) 为 consistent plug-in | 明确当前组 z-score 抵消；使用直接系数与固定/EMA 尺度 | 保留该完整组原定义的随机 reward-dependent normalizer |
| Clipping | 主训练去clip，另有empirical clipping ablation | oracle PG 范围在clip前，θ=old时对接；另保留实用clipped训练 | sign-separated coefficient 对每个固定θ构造等式；不宣称优化轨迹无偏 |
| 验证预算 | 校准集估计噪声率 | 已有随机negative appeals、HT计数与调用量 | 已知审计设计下，直接估计指定组的非线性目标 |
| 噪声条件 | class-conditional flip模型；统计估计误差分开 | channel假设；instance-dependent残差明确 | 代理向量可任意，但参考标签定义固定且可查询 |

现版作者：

- Omar El Mansouri; **Fathinah Asma Izzati**; Mohamed El Amine Seddik; Salem Lahlou。[v3作者与历史](https://arxiv.org/abs/2510.18924v3)，[§5.1/Theorem5.4与Appendix C](https://arxiv.org/html/2510.18924v3)。
- Xin-Qiang Cai; Wei Wang; Feng Liu; Tongliang Liu; Gang Niu; Masashi Sugiyama。[v4作者与历史](https://arxiv.org/abs/2510.00915v4)，[Theorem3.3与Appendix B](https://arxiv.org/html/2510.00915v4)。

建议替换正文相关工作段的 LaTeX 在 `paper/verifier_related.tex`，沿用正文现有 `cai2025`、`mansouri2025` citation keys。BibTeX metadata在 `docs/noise_correction_current.bib`，整合时可仅改key、保留最新作者和版本note。

“HT + selective verification + RL”“发现 affine correction 被 normalization 抵消”“审计最终 advantage”不能作为本项目新颖性主张。仍需为完整固定组目标、query-depth结果、预算下实用性提供独立证据。

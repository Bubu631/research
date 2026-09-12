# 最新 reward-noise correction 版本复核

核验日期：2026-09-12。此前只读早期版本的判断不应继续充当最新相关工作结论。以下直接核验当前 arXiv HTML、摘要页及版本历史；没有据此认证作者实验已被本项目复现。

## Noise-corrected GRPO，v3

[当前全文](https://arxiv.org/html/2510.18924v3)／[版本与作者](https://arxiv.org/abs/2510.18924v3)：2026-05-19，作者为 Omar El Mansouri、**Fathinah Asma Izzati**、Mohamed El Amine Seddik、Salem Lahlou。

§5.1 已指出仿射 reward correction 会被组标准化抵消，并提出额外方差校正。Theorem 5.4 后明确区分：Dr.GRPO 的线性居中目标可 exact；GRPO 只有 oracle population σ 下 exact，实际 sqrt(Z) 是需截断负方差估计的 consistent plug-in。Appendix B.4 的主训练去掉 clipping；Appendix C 另做 clipping ablation。这不能称为对任意已实现有限组、随机部分标签下 clipped update 的精确无偏恢复。其标注预算用于估计 noise rates，不是直接估计每个完整组的非线性更新。

## Cai 等，v4

[当前全文](https://arxiv.org/html/2510.00915v4)／[版本与作者](https://arxiv.org/abs/2510.00915v4)：2026-05-22，作者仍为 Xin-Qiang Cai、Wei Wang、Feng Liu、Tongliang Liu、Gang Niu、Masashi Sugiyama。

Theorem 3.3 明示 oracle-rate population 范围，位于 finite-group normalization/clipping/KL 之前。Appendix B.2–B.5 改用直接系数、leave-one-out baseline 与固定/EMA 尺度，明确避免当前组 z-score；B.8 写出 instance-dependent 残差。**B.9 已有随机 appeals、HT 假阴性计数和期望额外调用量**；B.10 已检查真正进入训练的优势。B.1 的 PG 对接在 θ=θ_old、clipping inactive 处成立，并非所有 clipped iterates 的无偏证明。因此不能把“选择性审计+HT+RL”或“看实际优势而非 verifier accuracy”当新贡献。

## 对本项目的实际判断

这两篇最新版本没有在所核验的定理、算法和附录中给出本项目拟定的同一结论：在任意固定真实/代理 reward 向量上，按已知随机审计设计，直接无偏估计**原本完整有限组的 normalized 或 clipped surrogate update**。这是读源后的范围判断，不是“没有任何人做过”的证明。

可保留的研究问题应明确 target、conditioning、query model、预算及有限方差条件；不能退回泛泛的“对 noisy GRPO 去偏”。尤其要承认：若允许改用固定尺度或线性居中目标，当前相关工作已经提供更简单的替代路径。为何必须保留完整组目标，以及在同成本下相较 uniform full-group audit 是否有实用收益，需要本项目自己给出证据。随机 telescoping 本身也属于既有技术，不能另起名后声称新估计原理。

现版作者与版本信息的 BibTeX 在 `docs/noise_correction_current.bib`。年份保留首次 arXiv 发布年 2025，note 明确本次实际核验的 2026 修订版本，避免把 v1 的文字当成最新结论。

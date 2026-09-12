# Research on Reliable Learning and Decision-Making

**Research manuscripts, mathematical analysis, executable experiments, and recorded evidence.**

Maintained by **Shengwei Zhang · University of Pennsylvania**, with collaborators credited on each manuscript.

This collection brings together four research directions: learning from selectively observed corrections, certifying model upgrades, allocating measurement budgets for wellbeing decisions, and auditing group-relative policy updates. Each project includes its manuscript, implementation, experiment outputs, and a description of what the evidence establishes.

[Download the complete release assets](https://github.com/Bubu631/research/releases/tag/v1.0.0) · [Reproduction guide](REPRODUCIBILITY.md) · [Artifact index](ARTIFACTS.md) · [Citations](citations.bib)

## Papers

| Research direction | Manuscript | Read and reproduce |
|---|---|---|
| **Edit localization and selection bias** | *When Edit Localization Amplifies Relative Selection Bias: Gradient Geometry, Target Mismatch, and Importance Weighting* | [PDF](research_release/papers/edit_localization/main.pdf) · [Project](research_release/papers/edit_localization/README.md) · [LaTeX](research_release/papers/edit_localization/main.tex) |
| **Safe model upgrades** | *Certifying Model Upgrades with Slice-Wise Non-Regression and Incumbent Fallback* | [PDF](research_release/papers/base_upgrade/main.pdf) · [Project](research_release/papers/base_upgrade/README.md) · [LaTeX](research_release/papers/base_upgrade/main.tex) |
| **Wellbeing measurement and prioritisation** | *Which Uncertainty Is Worth Reducing? Budgeted Measurement for Wellbeing Prioritisation* | [PDF](nhs_aisi_research/paper/full.pdf) · [Project](nhs_aisi_research/README.md) · [LaTeX](nhs_aisi_research/paper/full.tex) |
| **Agent reward auditing** | *The Audit Complexity of Group-Relative Policy Updates* | [PDF](agent_reliability_research/paper/main.pdf) · [Project](agent_reliability_research/README.md) · [LaTeX](agent_reliability_research/paper/main.tex) |

The wellbeing research also preserves its preceding study, [*Before You Target: Ranking Sensitivity and Regression to the Mean in NHS Staff Wellbeing Data*](nhs_wellbeing_research/paper/main.pdf), with its [code, data provenance, and results](nhs_wellbeing_research/README.md). It is supporting work within the third direction.

## What each project studies

### 1. Learning from selective corrections

Human corrections identify editable spans, but the examples receiving corrections may be systematically selected. This project studies how edit localization changes **relative selection bias** and **error against a fixed gradient target**, including the distinction between the two. It derives a geometric criterion, exact finite-sample calculations, and importance-weighted estimators under explicit assumptions.

Recorded evidence includes finite-population simulations, human post-edit data in English–German and English–Chinese, and an English–German extension differentiating through 73.89 million active parameters at a fixed checkpoint. The selection mechanisms in the public-data experiments are deliberately constructed; these results do not estimate production complaint propensities or establish translation-quality improvements.

**Authors:** Shengwei Zhang, Haoda Dai, Yifei Li, and Yuheng Song — University of Pennsylvania.

### 2. Certifying model upgrades

An overall improvement can conceal regressions on individual slices. This project separates candidate construction from statistical release certification and uses the incumbent as a fallback when the candidate does not pass the declared non-regression gate.

The evidence includes controlled calibration and adaptive-selection experiments, plus two continuation paths for a small classifier on the public scikit-learn digits dataset. The balanced continuation improves average reporting accuracy, but all five proposals still fail the gate. Those failures remain part of the result; this is not a foundation-model deployment evaluation.

**Authors:** Shengwei Zhang — University of Pennsylvania; Tao Wu and Fei Qian — Alibaba International Digital Commerce.

### 3. Choosing which wellbeing uncertainty to reduce

Before allocating review slots, should a decision-maker collect more ordinary survey measurements or pay for a second measurement channel? This project applies established knowledge-gradient ideas to a budgeted, two-channel model where repeated measurements can reduce noise while leaving persistent bias unresolved.

The studies combine controlled paired simulations, a public BRFSS replay using 420,249 employed/self-employed respondent records, and an NHS illustration with 190 reporting units. Results include cost regimes where the extra channel is worse and a separately labelled exploratory budget extension. The NHS scenarios are model-conditional illustrations, not observed intervention effects or an operational hospital deployment.

**Author:** Shengwei Zhang — University of Pennsylvania.

### 4. Auditing group-relative policy updates

When a group-relative update depends nonlinearly on all verifier labels, selectively revealing individual labels changes the estimation problem. This project characterises exact Boolean query degree for specified GRPO coefficients and studies randomized correction under an expected audit budget.

Recorded studies include algebraic checks, controlled estimation, 180 constructed policy-optimization runs with 432,000 trajectories, and frozen-model diagnostics using historical SWE-Gym trajectories. The constructed training uses NumPy softmax policies; the Qwen diagnostic uses a fixed, 32-dimensional added logit-bias score. New on-policy language-model training is a documented future study. Negative regimes, calibration costs, and runtime costs are retained.

**Author:** Shengwei Zhang — University of Pennsylvania.

## Repository layout

```text
research_release/             Shared code and evidence for papers 1 and 2
  papers/edit_localization/   Edit-localization manuscript and results
  papers/base_upgrade/        Model-upgrade manuscript and results
nhs_aisi_research/            Main wellbeing measurement study
nhs_wellbeing_research/       Preserved preceding NHS ranking study
agent_reliability_research/   Agent-audit manuscript and experiments
release_metadata/            Original package manifests and checksums
README.md                    Collection overview
REPRODUCIBILITY.md            Setup, verification, and data restoration
ARTIFACTS.md                  Direct downloads for papers and evidence bundles
citations.bib                Manuscript-specific citation entries
```

## Get started

```bash
git clone https://github.com/Bubu631/research.git
cd research
```

Choose a project and follow its English README. Each has its own dependencies and recorded environment; a single shared Python environment is not assumed. Start with saved tables and existing verification routines before launching full experiments. Rerun experiments in a separate copy or use the documented output options to preserve the recorded evidence.

The repository contains the compact research trees. Additional per-record vocabulary-gradient arrays are available as a [release asset](https://github.com/Bubu631/research/releases/download/v1.0.0/public_gradient_evidence.zip); [restoration instructions](REPRODUCIBILITY.md#restore-the-edit-localization-gradient-evidence) explain where to extract them. Raw download caches and pretrained weights are obtained from the sources recorded in each project.

## Research status and attribution

These are research manuscripts with explicit assumptions and evidence boundaries. Public repository availability does not establish conference acceptance, arXiv listing, independent human review, or institutional endorsement. A venue name in a format file or research plan describes preparation, not acceptance. Historical manifests retain the status recorded when the corresponding experiment or package was created.

Please cite the individual manuscript you use; entries are in [citations.bib](citations.bib). Third-party data, model assets, and conference formatting files retain their original rights and attribution. See [data and rights notes](DATA_AND_RIGHTS.md) and the project source manifests.

The manuscripts disclose AI assistance in research development, writing, implementation, and checks. The named authors remain responsible for the scientific claims and interpretation.

# Data, provenance, and rights

This collection preserves source attribution and the evidence boundaries documented in each manuscript. Public access to this repository does not relicense third-party datasets, pretrained models, or conference formatting files. No blanket licence is assigned to those materials by this collection.

| Project | Included research evidence | Source and rights records |
|---|---|---|
| Edit localization | Derived numerical gradients, figures, selected-record identifiers, and experimental summaries; the large per-record gradient bundle is distributed separately | [Public post-edit protocol](research_release/docs/public_postedit_protocol.md), [English–German manifest](research_release/papers/edit_localization/results/public_manifest.json), [English–Chinese manifest](research_release/papers/edit_localization/results/public_en_zh/public_manifest.json) |
| Base-model upgrade | Small classifier checkpoints, data split identifiers, predictions, and numerical studies using the public scikit-learn digits dataset | [Digits protocol](research_release/docs/digits_protocol.md), [recorded experiment](research_release/papers/base_upgrade/results/digits_manifest.json) |
| Wellbeing measurement | Derived public BRFSS records and NHS panels, simulation/replay outputs, workbooks, and provenance | [Project rights notes](nhs_aisi_research/README.md#data-rights-intended-use-and-authorship), [CDC source manifest](nhs_aisi_research/data/brfss_source_manifest.json), [NHS source manifest](nhs_aisi_research/data/nhs_original_source_manifest.json) |
| Preceding NHS ranking study | Derived public panels, historical-vintage tables, and recorded backtests | [Project README](nhs_wellbeing_research/README.md), [source manifest](nhs_wellbeing_research/data/source_manifest.json) |
| Agent auditing | Derived SWE-Gym metadata, record/group identifiers, numerical features and scores; controlled experiment outputs | [SWE-Gym source manifest](agent_reliability_research/data/swe_gym/source_manifest.json), [data protocol](agent_reliability_research/docs/swe_gym_data_protocol.md) |

Original raw trajectory text, downloaded model weights, native mean-gradient caches, private interview materials, private direction notes, and local environments are not part of this collection. Reproduction scripts describe how to retrieve public upstream assets where needed. Upstream terms still apply when downloading them.

The included AAAI author-kit files retain the notices provided by their source. Their presence supplies a manuscript format and does not indicate conference submission or acceptance.

For reuse of original research code or manuscript material beyond rights already granted by the relevant rights holder, contact the corresponding authors. This repository does not assign a new blanket software or manuscript licence.

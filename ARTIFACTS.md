# Papers, source packages, and evidence downloads

All assets belong to [release v1.0.0](https://github.com/Bubu631/research/releases/tag/v1.0.0). The four research directions also have browsable source trees in this repository.

Project archives preserve the original delivered research snapshots, including their historical manifests. Updated English collection navigation lives in the repository. `arxiv` in a source-package filename identifies its packaging purpose, not a verified arXiv listing. Anonymous files identify a format, not a submission.

| Contents | Download | Size (MiB) |
|---|---|---:|
| Edit localization · paper | [edit_localization_4authors_paper.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/edit_localization_4authors_paper.pdf) | 0.74 |
| Edit localization · LaTeX source | [edit_localization_4authors_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/edit_localization_4authors_source.zip) | 0.36 |
| Model upgrades · paper | [base_upgrade_3authors_paper.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/base_upgrade_3authors_paper.pdf) | 0.50 |
| Model upgrades · LaTeX source | [base_upgrade_3authors_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/base_upgrade_3authors_source.zip) | 0.11 |
| Papers 1–2 · compact code, papers, and recorded evidence | [research_code_and_papers.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/research_code_and_papers.zip) | 86.44 |
| Edit localization · eight additional per-record gradient arrays | [public_gradient_evidence.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/public_gradient_evidence.zip) | 372.79 |
| Wellbeing measurement · full paper | [nhs_aisi_full_paper.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_full_paper.pdf) | 0.42 |
| Wellbeing measurement · named-author LaTeX source | [nhs_aisi_arxiv_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_arxiv_source.zip) | 0.10 |
| Wellbeing measurement · anonymous format | [nhs_aisi_anonymous.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_anonymous.pdf) | 0.25 |
| Wellbeing measurement · anonymous and supplement source | [nhs_aisi_anonymous_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_anonymous_source.zip) | 0.11 |
| Wellbeing measurement · supplement | [nhs_aisi_supplement.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_supplement.pdf) | 0.35 |
| Wellbeing measurement · decision brief | [nhs_aisi_decision_brief.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_decision_brief.pdf) | 0.00 |
| Wellbeing measurement · results workbook | [nhs_aisi_results.xlsx](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_results.xlsx) | 1.18 |
| Wellbeing measurement · code, derived data, results, and documents | [nhs_aisi_reproducibility.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_reproducibility.zip) | 37.30 |
| Preceding NHS ranking study · paper | [nhs_wellbeing_paper.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_wellbeing_paper.pdf) | 0.45 |
| Preceding NHS ranking study · LaTeX source | [nhs_wellbeing_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_wellbeing_source.zip) | 0.11 |
| Preceding NHS ranking study · full research bundle | [nhs_wellbeing_research.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_wellbeing_research.zip) | 1.84 |
| Agent auditing · paper | [agent_audit_paper.pdf](https://github.com/Bubu631/research/releases/download/v1.0.0/agent_audit_paper.pdf) | 0.87 |
| Agent auditing · LaTeX source | [agent_audit_arxiv_source.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/agent_audit_arxiv_source.zip) | 0.61 |
| Agent auditing · code, derived evidence, and documents | [agent_audit_reproducibility.zip](https://github.com/Bubu631/research/releases/download/v1.0.0/agent_audit_reproducibility.zip) | 95.47 |
| Papers 1–2 · original package manifest | [bundle_manifest.json](https://github.com/Bubu631/research/releases/download/v1.0.0/bundle_manifest.json) | 0.00 |
| Preceding NHS study · original package manifest | [nhs_wellbeing_manifest.json](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_wellbeing_manifest.json) | 0.04 |
| Wellbeing measurement · original package manifest | [nhs_aisi_release_manifest.json](https://github.com/Bubu631/research/releases/download/v1.0.0/nhs_aisi_release_manifest.json) | 0.00 |
| Agent auditing · original package manifest | [agent_audit_release_manifest.json](https://github.com/Bubu631/research/releases/download/v1.0.0/agent_audit_release_manifest.json) | 0.00 |

## Integrity and restoration

[SHA-256 checksums](release_metadata/SHA256SUMS.txt) and the [collection release manifest](release_metadata/github_release_manifest.json) record the byte size and checksum of every original artifact above. They are also attached to the release.

To verify a full asset download directory on macOS, run `shasum -a 256 -c SHA256SUMS.txt` from that directory. On Linux, use `sha256sum -c SHA256SUMS.txt`. The checksum file expects every listed asset; verify individual files when downloading only a subset.

Extract the large gradient archive from the collection root, as described in [the reproduction guide](REPRODUCIBILITY.md#restore-the-edit-localization-gradient-evidence). Each project reproducibility archive has its own project directory prefix. Extracting an original archive over the Git checkout can replace updated README files; use a separate directory to inspect the original delivered snapshot.

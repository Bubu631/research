# NHS research-line repository audit

Checked 2026-09-12 in the GitHub staging checkout. Scope: the latest `nhs_aisi_research/` project and the preserved sibling `nhs_wellbeing_research/` project. This is a bounded static/read-only content audit, not another execution of the scientific studies or an external human peer review.

## Changes made

Only the two project READMEs and this audit were authored during this audit. The READMEs now link directly to manuscripts, results, protocols and the other study; distinguish the two scientific questions; explain the parent-repository working directory; and identify optional tooling and original packaging dependencies. Existing numerical results, scientific code, source snapshots, CSVs, workbooks and PDFs were not modified.

The latest README uses its supplied requirements file, documents the explicit Make targets, and warns that plain `make` runs the complete suite. It names the exact `unweighted_tilt_05` scenario behind its existing negative result. This disambiguates the separately reported biased-validation scenario without changing a result.

## Offline checks completed

| Check | Preserved predecessor | Latest measurement study |
|---|---:|---:|
| Python files parsed successfully with `ast.parse`, including provenance copies | 30 | 75 |
| README local file/directory links resolved | 16 | 19 |
| `make -n all` completed | Yes | Yes |
| Included raw-download caches, virtual environments, model weights, private-key files or dependency directories detected | None | None |
| Narrow credential-pattern scan found private-key blocks or long GitHub/API-token patterns | None | None |

The latest README's 17 direct Python command paths existed. The predecessor uses Make targets; its dry run resolved the declared command structure. This is syntax/path checking, not an installation test, network-availability guarantee or claim that every optional helper is standalone.

The preserved NHS panel contains 1,190 rows. The latest primary BRFSS files contain 206,098 records for 2023 and 214,151 for 2024, each covering 48 areas. Saved vintage metrics and the latest primary/extension KG rows were read to confirm the README's existing rounded results and direction of effects. No study was rerun and no rows were selected for replacement or removal.

At inspection, the predecessor contained about 8.0 MB and the latest project about 146.1 MB. No individual file exceeded 50 MB. The largest file was the approximately 45.1 MB combined BRFSS derived CSV. Combined, year-specific and all-area public derived frames overlap intentionally; all were retained. The small variation introduced by subsequent README/audit text is not included in these inspection sizes.

## Portability and provenance boundaries

- **Prepared-data analysis is self-contained.** Scientific inputs, scripts and saved outputs are present in each project. Rebuilding raw sources additionally needs network access and upstream availability. Source workbooks, CDC ZIPs, questionnaires and full-text caches are intentionally absent.
- **Fresh official downloads are not fail-closed against the committed manifest.** Both official-source fetchers check already-cached files, but record fresh hashes when downloading an absent source. Preserve the committed manifest and compare refreshed payload hashes before claiming exact original-input reproduction. The predecessor's archived benchmark fetcher separately enforces its recorded SHA-256 and archive CDX SHA-1 for both new and cached payloads. The READMEs describe this distinction.
- **Historical packaging helpers have delivery-directory dependencies.** The latest `artifact_tools/package_release.py` expects `../output/release/nhs_wellbeing_paper.pdf` and checks a fixed predecessor hash. The predecessor's release builder also works through a sibling delivery directory. These helpers are not required for analysis or TeX compilation and are not advertised as self-contained GitHub release commands.
- **Optional artifact dependencies differ from scientific dependencies.** The predecessor workbook builder and latest workbook recalculation helper require `@oai/artifact-tool`; the latest ordinary workbook builder uses openpyxl. The optional latest decision-brief builder also requires ReportLab, absent from `requirements.txt`. Its rendered output is supplied. These distinctions are now explicit in the README.
- **The exploratory extension is Unix-specific.** It imports the standard-library `resource` module for the declared memory check. Its current entry point supports macOS/Linux, not native Windows. Main run evidence is from the recorded macOS environment; no new cross-platform test was performed here.
- **Historical machine paths remain in a result audit.** `results/reproduction_verification.json` records four original absolute interpreter paths. They are historical command metadata, not runtime dependencies or credentials. They were reported to the repository maintainer for a separate provenance-preserving sanitisation decision; this audit did not rewrite that JSON.

## Public-content boundaries

The BRFSS tables are derived from the CDC public-use files. The retained PSU/stratum codes are public survey-design fields, and the generated row hash is not a longitudinal identity or contact identifier. No names, contact records, private NHS staff microdata, clinical deployment logs or proprietary model weights were found in the audited project content. The NHS inputs are published organisation/reporting-unit aggregates, not department records. This bounded scan is not a guarantee that arbitrary future additions contain no sensitive material.

Original third-party rights and author-kit notices remain intact. NHS public accessibility is not relabelled as a blanket redistribution licence; no new licence was assigned to third-party material. The READMEs preserve the difference between simulations, finite-file replay and unobserved NHS scenarios, all reported reversals, AI assistance and author responsibility. No publication, institutional partnership, co-design, clinical effect or deployment claim was introduced.

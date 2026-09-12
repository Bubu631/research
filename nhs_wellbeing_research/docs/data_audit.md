# NHS Staff Survey data audit

Checked 11 September 2026. This audit concerns the English NHS substantive-staff survey, not the separate bank-worker survey. The project outline supplied by the user is background material; its simulated examples and authorship statements are not evidence about these data.

## Source and reproducible outputs

The primary source is the official [NSS Benchmark Report Excel Data for 2021–2025, updated 17 March 2026](https://www.nhsstaffsurveys.com/static/be505cf2e70c080aa35d34279f68e3f2/NSS-Benchmark-report-excel-data-for-2021-2025-v2.xlsx), linked from the [local results page](https://www.nhsstaffsurveys.com/results/local-results/). It supplies all five years in the **2025 reporting frame**. The separate [2025 detailed spreadsheets](https://www.nhsstaffsurveys.com/static/98d750b25a18cce79ff98383f0d6d1d4/NSS25-Detailed-spreadsheets.zip) provide response-option distributions but are not the primary panel source.

`data/source_manifest.json` records exact source and final URLs, access/download times in UTC, byte counts, SHA-256 digests, available HTTP metadata, local filenames, and licence uncertainty for 25 retrieved assets. Original files are retained locally in `data/raw/`. PDF text extraction records original PDF or ZIP-member hashes in `data/extracted/extraction_manifest.json`; extracted text is a navigation aid, not a replacement for the PDFs.

The principal machine-readable output is `data/processed/nhs_staff_survey_panel_2021_2025.csv`. Every retained numerical field has an Excel cell locator in `source_cells`, alongside the exact sheet, row, source filename and workbook SHA-256. `data_dictionary.json` describes every column; `source_variable_dictionary.json` preserves the workbook's variable descriptions and their Notes-sheet row numbers. The other outputs are `organisation_cohort.csv`, `historical_comparability_events.csv`, `missingness_cells.csv`, `panel_manifest.json`, and `validation_report.json`.

Reproduce from this project's directory with Python 3 and the dependencies pinned in `data_tools/requirements-data.txt`:

```sh
python data_tools/fetch_sources.py
python data_tools/extract_documentation.py
python data_tools/parse_panel.py
python data_tools/validate_panel.py
```

The fetcher reuses existing downloads only after verifying their recorded hashes. `--refresh` explicitly refetches the named URLs and updates the source manifest. Consequently a later upstream revision is observable rather than silently assumed identical. Current parsing uses openpyxl 3.1.5; PDF extraction uses pypdf 6.10.0. The parser and validator are separate programs. Validation checked all 14,280 retained source-cell values, all 25 raw-file hashes, key uniqueness, data-dictionary coverage, bounds, and count relationships. A separate RCF benchmark PDF also confirms that total questionnaires and valid burnout responses are distinct counts.

## Units and coverage

There are 238 reporting units, each represented for five survey years, giving 1,190 rows including explicit missing rows. This is not a census of every organisation that operated in every historical year. Organisation names and benchmark groups are those used in the 2025 release. Historical predecessors absent from that release are not independently added.

The five mandatory trust reporting groups contain 206 reporting units. The complete-history filter is `is_trust == 1` and `complete_five_year_history == 1`, yielding 190 reporting units and 950 institution-year rows. Selection is based on official history availability and comparability, not on observed outcome magnitudes.

| 2025 benchmark group | Trust reporting units | Complete 2021–2025 histories |
|---|---:|---:|
| Acute and acute/community | 121 | 110 |
| Acute specialist | 13 | 13 |
| Mental health/learning disability/community | 48 | 43 |
| Community | 13 | 13 |
| Ambulance | 11 | 11 |

The remaining units are ICBs, social enterprises and a community surgical service; these remain in the full exported panel but are outside the intended primary trust cohort. R1F1 and R1F2 are separate acute and ambulance reporting sectors of Isle of Wight NHS Trust, with common legal code R1F. Thus the 190-unit complete cohort has 189 known distinct legal identifiers, and must not be described as 190 independent legal trusts. The `legal_org_code` field records this known relationship without claiming a comprehensive legal-successor crosswalk.

`result_available` means a numerical burnout score was published for that row. `historically_comparable` additionally excludes organisations on the 2025 guide's no-history list; it can be true for available years of a partial history. `complete_five_year_history` is the stronger five-year criterion used above. None of these variables establishes stable staff membership, the absence of every service transfer, or an individual longitudinal panel.

## Measures and missing precision information

The official [2025 Technical Guide, version 2](https://www.nhsstaffsurveys.com/static/0e6b1554117a6a032f16a6cba7b4cc2d/NHS-Staff-Survey-2025-Technical-Guide-V2.pdf), section 4, defines the burnout subscore `PP4_2` from q12a–g. Each person's score averages available items when at least five of seven are answered. Items are coded from 10 for Never through 7.5, 5, 2.5 to 0 for Always. Therefore **higher published scores mean less burnout**. This is a survey scale, not a clinical diagnosis or a prevalence percentage.

| Panel field | Workbook variable | Interpretation |
|---|---|---|
| `burnout_score` | `PP4_2_YEAR` | Weighted organisation score, 0–10; higher is better |
| `burnout_n` | `PP4_2_n_YEAR` | Nominal valid composite-response count |
| `n_resp` | `response_rate_n_YEAR` | Total completed questionnaires |
| `response_rate` | `response_rate_YEAR` | Published organisation rate, 0–1 |
| `wellbeing_action` | `q11a_YEAR` | Proportion agreeing their organisation takes positive health/wellbeing action |
| `intent_leave` | `q26a_YEAR` | Proportion often thinking about leaving; not actual turnover |
| `thinking_about_leaving_score` | `M_1_YEAR` | Composite 0–10; higher means less intention to leave |
| `work_related_stress` | `q11c_YEAR` | Proportion reporting feeling unwell from work-related stress |

The benchmark workbook stores all four proportions as native Excel fractions, generally with percentage display formats, although some q26a cells have General formatting. They are exported unchanged: **no division by 100** is applied. This differs from the separate detailed-response workbook, whose percentage cells contain values on a 0–100 scale. Each optional measure retains its own nominal valid-response count.

During the supporting-workbook visual audit, an initial extra division by 100 was found and corrected for the three optional fields `wellbeing_action`, `intent_leave` and `work_related_stress`. The validator now also reconstructs all three 2025 proportions from the independent detailed-response workbook's named percentage columns, including adding Agree and Strongly agree where required. This correction did not change burnout scores, nominal counts, response rates, cohort membership, or primary forecasting inputs. The corrected panel hash is recorded in `panel_manifest.json` and `validation_report.json`; all later snapshots must use it.

The workbook does not directly publish eligible headcounts. `n_eligible` is therefore empty. `n_eligible_from_org_rate` is a separately named algebraic denominator, `n_resp / response_rate`, using that organisation's own rate. It is **derived, not directly observed**; limited source precision makes the 2021 values approximate. No national response rate is used to impute an organisation's eligibility.

The supplied aggregate outputs do not provide respondent-level analysis weights, the item-valid weight distribution, individual composite SDs, or burnout composite SEs. The corresponding `n_eff`, `burnout_individual_sd` and `burnout_se` columns remain empty. `burnout_n` may be used as an explicitly nominal size proxy; it is not an effective sample size. Seven marginal item distributions do not determine composite variance without the cross-item covariance. Occupational margins alone do not determine effective sample size for an item-missingness-conditioned composite. Suppression below ten responses is a confidentiality rule, not evidence that n=10 is a reliability threshold.

## Weighting and information vintage

The 2025 guide section 6 distinguishes **three types of weights**, not three sequential weighting layers: occupation-group weights for benchmarking, trust-size weights for national aggregation, and their product for outputs needing both. The organisation benchmark scores use occupation-group weighting across 13 broad groups, with individual occupation weights capped at five. ICB and community surgical-service benchmark data are unweighted; the exported metadata reflects this exception. Trust-size weights use eligible staff divided by total responses and are not a replacement for occupation weights.

Most importantly, section 6.1 explicitly states that 2021–2024 histories are reweighted to 2025 occupation-group proportions. The guide also describes historical cleaning and corrections. Analyses of this panel are consequently **retrospective exercises on harmonised historical data**, not strict simulations of what an analyst could have known at each past decision date. The classification and complete-history cohort also use the 2025 reporting frame. Original-vintage benchmark files are handled separately under `vintage_data/`; they should not be mixed into this panel without an explicit vintage definition. Official workbook notes recommend comparisons within the same benchmark group; a common unadjusted trust-wide score threshold across dissimilar groups is not the intended benchmark comparison.

## Question comparability and corrections

Burnout q12a–g was introduced in 2021 and its corresponding seven items and scoring rule are retained through 2025. No pre-2021 burnout series is manufactured. The question measuring frequent thoughts of leaving was numbered Q22a in 2021, Q24a in 2022, and Q26a from 2023 onward. The 2025 workbook harmonises the corresponding history under `q26a_YEAR`; the dictionary records the original numbering. q11a remains the perceived-positive-action measure across these years.

The [official 2023 data-collection issue explanation, available through survey documents](https://www.nhsstaffsurveys.com/survey-documents/) and 2025 guide section 6.4 identify corrections to q13/q14 and affected health-and-safety/negative-experience measures. **The burnout subscore PP4_2 is not one of the affected measures.** It must not be confused with its parent People Promise element PP4, which includes other subscales. Changes to q11b/q15 and q16c in 2025 likewise do not establish a change to burnout q12a–g. The parent PP4 definition was adjusted for comparability; this analysis retains PP4_2 specifically.

## Reorganisations and excluded histories

The [2025 guide](https://www.nhsstaffsurveys.com/static/0e6b1554117a6a032f16a6cba7b4cc2d/NHS-Staff-Survey-2025-Technical-Guide-V2.pdf), section 8.1, lists 15 reporting codes without historical comparisons: G6V2S, NDJ, NQV, NTV, QE1, QHM, QNC, RAL, RAX, RQ3, RTX, RW1, RXL, RXR and RXT. Reasons include acquisitions, workforce-size changes, service transfers and nonparticipation. Codes are preserved; their histories are not bridged or imputed.

Seven further trust units have partial histories explained by earlier official releases:

| Code(s) | Earliest available year | Official reason and guide |
|---|---:|---|
| RH8, RM3 | 2022 | Mergers; [2022 guide](https://www.nhsstaffsurveys.com/static/8dd604e04c547de7022d75c8fc4b6c97/P101646-NSS22-Technical-document-V1.1-2022-FINAL.pdf), section 8.1 |
| RA9, RWK | 2023 | Historical sample-drawing errors; [2023 guide](https://www.nhsstaffsurveys.com/static/67edc962a64e8dabc9ef584a18f1bf5a/NHS-Staff-Survey-2023-Technical-guide_V4.pdf), section 8.1 |
| RBN, RH5 | 2023 | Mergers; [2023 guide](https://www.nhsstaffsurveys.com/static/67edc962a64e8dabc9ef584a18f1bf5a/NHS-Staff-Survey-2023-Technical-guide_V4.pdf), section 8.1 |
| RX2 | 2024 | CAMHS transfer; [2024 guide](https://www.nhsstaffsurveys.com/static/e72dc1bd37edd8026aa06b4290a33dd0/NHS-Staff-Survey-2024-Technical-Guide-V5.pdf), section 8.1 |

The 2025 guide associates code NQV with the name Medway Community Healthcare, while the workbook associates NQV with Bromley Healthcare CIC. This code/name inconsistency is preserved in the audit rather than silently repaired. The unit is nontrust and outside the primary cohort. The 2023 guide's pre-2023 exclusion for RWK supersedes the earlier pre-2022 cutoff. The event CSV supplies each retained exclusion's source URL and source-file hash.

## Scope and reuse boundaries

These public records describe organisations and reporting sectors, not nationally standardised departments. Optional directorate breakdown reports use organisation-specific categories and unweighted figures; they do not supply the common department-year panel imagined in the project outline. There are no recorded budget assignments, intervention costs, randomisation indicators or verified intervention absences in this panel. Perceived organisational action is observational and does not identify a causal intervention effect. Subsequent survey changes cannot be labelled a zero-intervention counterfactual, and intention to leave cannot be labelled observed turnover.

Public access has been verified, but a current asset-specific permissive reuse licence has not. The technical guide is marked copyright Survey Coordination Centre, all rights reserved; the website also carries a copyright notice. An [older data.gov.uk catalogue entry](https://www.data.gov.uk/dataset/7e6cfa08-536a-4066-b7bd-a673c3034a49/national_nhs_staff_survey) names the Open Government Licence, but its old metadata does not verify that it covers these specific 2021–2025 assets. The [official FAQ](https://www.nhsstaffsurveys.com/faqs/) separately requires express NHS England permission to reuse the questionnaire for other purposes. No new questionnaire is administered here and no permission request has been sent.

For a public repository, retain the fetch/parse code, provenance and clearly attributed derived research outputs; keep downloaded third-party questionnaires, PDFs, workbooks and their extracted text outside a blanket software-licence claim. The local raw-source cache supports audit and reproducibility without asserting newly verified redistribution rights. This is a source-status finding, not a legal conclusion about every possible reuse.

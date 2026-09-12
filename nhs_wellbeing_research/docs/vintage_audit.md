# NHS Staff Survey reporting-vintage audit

Audit performed on 11 September 2026. This work obtains and checks public source data. It does not fit or evaluate a forecasting model.

## Main result

The actual 2023 and 2024 benchmark Excel releases have been recovered from archived captures of the official NHS Staff Survey website. Their payloads match both a locally recorded SHA-256 and the historical Internet Archive CDX SHA-1 digest. The currently live official static URLs return 404. The archive chain records the original official URL, the official page that linked to it, the file capture timestamp, retrieval time, file hashes, and source cell coordinates.

The ready-to-use file is `vintage_data/benchmark_vintage_panel.csv`. It contains **1,856 rows** with one organisation/survey-year observation within a specified release vintage. It supplies the original historical sequences required for a vintage-aware sensitivity, rather than reconstructing all earlier observations from the 2025 workbook.

| Reporting vintage | Historical workbook span | Available burnout years | Verified file capture (UTC) | Organisations | Trust reporting units | Complete, comparable trust histories |
|---|---|---|---|---:|---:|---:|
| 2023, corrected v2 | 2019–2023 | 2021–2023 | 2024-07-05 03:53:34 | 268 | 213 | 207 |
| 2024 | 2020–2024 | 2021–2024 | 2025-04-27 12:25:52 | 263 | 210 | 201 |

The 2025 primary cohort of **190 reporting units** is wholly contained in both sets of complete comparable histories. The three-vintage intersection remains 190, with no change in the canonical benchmark-group labels. This is a reporting-unit match, not proof of an unchanged workforce or legal organisation.

“Release vintage 2023” identifies the survey reporting frame, not a publication in calendar 2023. The 2023 survey results were released in 2024. The recovered corrected workbook was archived in July 2024. The 2024 results were first published on 13 March 2025, and the recovered file was archived in April 2025. Exact first-release-day byte availability is not claimed. Forecast origins using these files must be no earlier than the verified captures, unless earlier availability is separately established. The July 2024 and April 2025 captures precede the respective autumn 2024 and autumn 2025 survey fieldwork. [2023 release announcement](https://www.combined.nhs.uk/news/latest-updates/nhs-staff-survey-2023-results-confirm-combineds-support-for-staff/), [official 2024 release record](https://www.gov.uk/government/statistics/2024-national-nhs-staff-survey-results).

## Primary archived sources

- 2023: [official-page capture](https://web.archive.org/web/20240704161813id_/https://www.nhsstaffsurveys.com/results/local-results/) identifies the [archived official benchmark workbook](https://web.archive.org/web/20240705035334id_/https://www.nhsstaffsurveys.com/static/7d4ab30226c8780f12de6378d8208303/benchmark_report_excel_data_2019-2023_v2.xlsx). The original file is named `benchmark_report_excel_data_2019-2023_v2.xlsx`. SHA-256: `ce147719f3798cf597ea77509fea739a39a84a6e39d0fa0cd7c7ba49b8909929`.
- 2024: [official-page capture](https://web.archive.org/web/20250531050327id_/https://www.nhsstaffsurveys.com/results/local-results/) identifies the [archived official benchmark workbook](https://web.archive.org/web/20250427122552id_/https://www.nhsstaffsurveys.com/static/4393b3f78f0c9e6c06906310ee7ff6c3/Benchmark-report-Excel-data-for-2020-2024.xlsx). The file has an earlier, independently indexed April capture. SHA-256: `6939c8a0ebb2e0ba9a970952cc5dfbdfbb398fb8319ae8bbf7af9c8a9cb9978a`.

For 2024, a second attempted retrieval requested the 31 May capture but returned bytes matching the verified April capture, while that May CDX record advertised a different digest. This ambiguous May retrieval is retained in the provenance logs and **excluded as an independent version**. The primary file is specifically the April capture whose payload matches its own CDX digest. No difference between those two putative versions is inferred.

## Field definitions and parsing

The main CSV begins with the requested fields:

| Field | Definition |
|---|---|
| `release_vintage` | Survey reporting-frame year, 2023 or 2024 |
| `year` | Survey year of the observation |
| `org_code`, `org_name` | Exact reporting-unit identifier and name in that vintage |
| `benchmark_group` | Canonical organisation group based on the workbook sheet |
| `benchmark_group_original` | Original sheet-group label |
| `reporting_comparison_group` | Separate `org_type_reporting_name` field, which can differ for social enterprises |
| `burnout_score` | `PP4_2_YEAR`, range 0–10; higher scores indicate less burnout |
| `burnout_n` | `PP4_2_n_YEAR`, nominal valid composite-response count; not effective sample size |
| `is_trust` | 1 for the five official trust sheet groups, 0 for other organisation groups |
| `historically_comparable` | A score is provided and the organisation is absent from that vintage's technical-guide no-history list |
| `complete_history_in_vintage` | All available burnout years in the vintage are present and the organisation is absent from the no-history list |
| `archive_capture_utc` | Verified capture establishing an upper bound on when this archived payload was publicly observable |

Additional columns preserve source file, SHA-256, official and archive URLs, access time, worksheet, row, and individual cell coordinates. Missing scores and counts remain blank, accompanied by availability flags. Nothing is imputed. The two vintages contain 36 and 45 missing score cells respectively. Burnout was introduced in 2021, so the earlier headline workbook years do not supply earlier `PP4_2` observations.

The group mapping preserves the same five trust labels as the 2025 primary panel: `Acute&Acute Community Trusts`, `Acute Specialist Trusts`, `MH&LD, MH, LD&Community Trusts`, `Community Trusts`, and `Ambulance Trusts`. Social-enterprise comparison fields can name a trust benchmark group; using that field to determine trust membership would misclassify them. The parser uses the organisation's sheet group and preserves the comparison field separately.

Historical comparability follows each year's Section 8.1, rather than applying the 2025 exclusion list retrospectively. For 2023, exclusions are RWK, RA9, RBN, RH5, 0DE, NQ7, QHM, QOC, QOP, and QUE. For 2024, they are QOQ, RX2, RW1, and RY9. The lists include mergers, service transfers, sampling errors, and nonparticipation. The `historically_comparable` flag does not establish stable respondent membership. [2023 technical guide](https://www.nhsstaffsurveys.com/static/67edc962a64e8dabc9ef584a18f1bf5a/NHS-Staff-Survey-2023-Technical-guide_V4.pdf), [2024 technical guide](https://www.nhsstaffsurveys.com/static/e72dc1bd37edd8026aa06b4290a33dd0/NHS-Staff-Survey-2024-Technical-Guide-V5.pdf).

## What the vintage sensitivity changes

Historical scores are reweighted to the reporting year's occupational-group composition and may be reprocessed under current cleaning rules. Consequently, a 2023 observation taken from the 2025 workbook need not equal the observation available in the 2023 release. The 2023 guide Section 6.1 specifies use of 2023 proportions for its historical series; the 2024 guide specifies 2024 proportions. The intended comparison can therefore use 2023-vintage 2021–2023 inputs for a 2024 target, and 2024-vintage 2021–2024 inputs for a 2025 target. This is a sensitivity to the available reporting frame, not proof that every retrospective revision creates a large forecast effect.

Among the shared 190 units, comparisons to the 2025 reporting frame give:

| Earlier vintage | Matched score cells | Mean absolute score revision | Largest absolute score revision | Nominal base-count revisions |
|---|---:|---:|---:|---|
| 2023 | 570 | 0.0112988 | 0.0470074 | RL4, survey year 2023: 2,609 to 3,019 |
| 2024 | 760 | 0.00454756 | 0.0248069 | REF, survey year 2024: 3,445 to 3,437 |

Every matched score differs by more than `1e-10`; these are data revision diagnostics, not model-performance results. The 2024 technical guide Section 9.1 states that **412 total 2023 questionnaires** for Royal Wolverhampton (RL4) omitted from the original release were subsequently included in its 2023 history. The observed `PP4_2` base changes by **410 valid composite responses**, which is a different denominator. Thus vintage differences include revisions as well as reweighting. No cause is assigned here to REF's eight-response difference without additional source evidence.

## Independent verification

`vintage_data/validate_vintages.py` independently reads the workbook's raw OOXML numeric cells, using workbook relationships to locate each worksheet. It verifies **3,550 nonmissing score/count cells** against the exported CSV. It does not rely on the same openpyxl row extraction used by the parser.

The current-year score and count in each archived benchmark workbook were also compared to the separate official annual organisational detailed spreadsheet: all 268 organisations for 2023 and 263 for 2024 matched in nominal count, with maximum floating-point score difference `8.88e-16`. The shared 190-unit cohort and unchanged group labels were checked independently. Results and input hashes are in `vintage_data/independent_validation.json` and `vintage_data/parsing_manifest.json`.

Restore and recheck the two archived benchmark files with `python vintage_data/fetch_primary_benchmarks.py`. Recreate CSVs with `python vintage_data/parse_vintages.py`. Run the independent checks with `python vintage_data/validate_vintages.py`. Python with openpyxl is required for parsing; the independent OOXML checks use the standard library.

## Additional annual sources and department-level availability

The official [results archive](https://www.nhsstaffsurveys.com/results/results-archive/) also supplies annual detailed ZIPs for 2021–2024. Their organisational workbooks were copied without changes from the independently downloaded official sources; URLs, access timestamps and hashes are retained in `vintage_data/source_manifest.json`. `annual_release_current_year_panel.csv` contains 1,075 contemporaneous-year rows: 280, 264, 268, and 263 organisations respectively. These are useful crosschecks and a distinct annual-release panel, not a substitute for the single-vintage historical benchmark sequences above. The available annual workbooks are revised archive versions; they are not asserted to match first-publication-day bytes.

An additional [2021 benchmark workbook](https://web.archive.org/web/20220401110158id_/https://www.nhsstaffsurveys.com/static/ef4edcf3bb3c11b8694713f561b2670c/Benchmark_report_excel_data_2017-2021.xlsx) was recovered from the verified 1 April 2022 capture and retained as an optional raw source. Its SHA-256 is `ea7cdb814627be22f241f0225e2b35376eac71accbfbe7b7c03c97b7a25e442c`; its payload also matches the CDX SHA-1. It is not included in the primary two-vintage CSV. Archived official pages from 21 March and 9 June 2023 identify the original 2022 benchmark filename `benchmark_report_excel_data_2018-2022-v2.xlsx`, but exact-URL CDX queries returned no file capture. The 2022 annual detailed spreadsheet is available; a full 2022 historical benchmark payload is not asserted to have been recovered. Discovery attempts and hashes are retained in `earlier_benchmark_manifest.json` and the adjacent archive logs.

The 2023 annual workbook notes the corrected q13/q14 data issue, which affected other components of People Promise 4. `PP4_2` is the q12 burnout component; its current-year scores agree with the archived benchmark v2 as checked above. The parent analysis should not generalise that unaffected status to all People Promise 4 components.

Some public trusts publish optional local breakdown reports and department/team response-rate documents. For example, [Derbyshire Community Health Services' survey page](https://dchs.nhs.uk/my_dchs/i-want-more-information-on/corporate-services/staff-engagement/national-staff-survey) links benchmark/breakdown reports across several years and a 2021 department/team response-rate document. This does not establish a national harmonised department-level burnout panel or individual-level measurement variance. No department-level scores were reconstructed here.

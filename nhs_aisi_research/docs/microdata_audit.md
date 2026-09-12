# Public microdata provenance and finite-file replay audit

Data acquisition and checks were performed on 11 September 2026. This audit supplies data and independent parsing checks; it does not run or tune an acquisition policy. It leaves the earlier NHS-only research repository unchanged.

## Source and permitted scope

The additional source is the CDC **Behavioral Risk Factor Surveillance System (BRFSS)** combined landline/cellphone public-use file for [2023](https://www.cdc.gov/brfss/annual_data/annual_2023.html) and [2024](https://www.cdc.gov/brfss/annual_data/annual_2024.html). These files are directly downloadable without an account, authentication key or individual data application. They are annual cross-sectional telephone surveys of adults, not employee-panel follow-ups or records from hospital departments. BRFSS coverage is the noninstitutionalised adult population; survey response, telephone coverage and item missingness limit the composition of the observed file. [CDC survey documentation](https://www.cdc.gov/brfss/data_documentation/index.htm).

CDC's BRFSS-specific [FAQ, question 14](https://www.cdc.gov/brfss/about/brfss_faq.htm) states that federal-agency data/materials are generally in the public domain and asks published derivatives to acknowledge CDC BRFSS. The [agency-materials terms](https://www.cdc.gov/other/agencymaterials.html) specify attribution and no implied endorsement, while noting exceptions for some third-party/state materials. This study relies on the federally published BRFSS microdata and these stated terms; it does not invent a Creative Commons licence or apply a code licence to all agency materials. The original sources remain freely available from CDC. The cleaned files and rescaling are explicitly this study's derivatives, not replacement official releases.

**Source: CDC BRFSS. This independent research and its conclusions are not endorsed by CDC, HHS, or the United States Government.** No individual identity is sought or inferred. No telephone number, address, name, free-text employer, or private record linkage is included in the derived files. Published survey stratum/PSU codes remain available for design diagnostics.

Suggested attribution: Centers for Disease Control and Prevention (CDC). *Behavioral Risk Factor Surveillance System Survey Data*. Atlanta, Georgia: U.S. Department of Health and Human Services, Centers for Disease Control and Prevention, 2023 and 2024. [Official citation guidance](https://www.cdc.gov/brfss/questionnaires/index.htm).

## Download and version evidence

| Survey year / format | Actual compressed bytes | Complete public records | Actual ASCII record length |
|---|---:|---:|---:|
| 2023 ASCII ZIP | 60,057,185 | 433,323 | 2,111 characters |
| 2024 ASCII ZIP | 53,411,907 | 457,670 | 2,061 characters |
| 2024 SAS-transport ZIP, independent check | 83,007,956 | 457,670 | Not applicable |

Files are streamed from their ZIP members rather than expanding the roughly gigabyte-size ASCII payloads. The exact original URLs, UTC access times, response metadata, SHA-256 digests, member sizes and ZIP CRCs are in `data/brfss_source_manifest.json`. Those digests establish the acquired version and integrity; no CDC-published cryptographic checksum is claimed. The parser retains the source SHA in its own manifest.

The annual web pages contain some stale size/schema descriptions: in particular, the current 2024 page describes a 2,111-position ASCII file and 345 SAS variables, whereas the downloaded file has 2,061-character records and the SAS-transport file has 301 variables. The required field positions agree between the official SAS import programs and the relevant entries of the variable-layout pages. Actual byte sizes and record lengths are measured and retained; the narrative website descriptions are not used to guess offsets. [2023 variable layout](https://www.cdc.gov/brfss/annual_data/2023/llcp_varlayout_23_onecolumn.html), [2024 variable layout](https://www.cdc.gov/brfss/annual_data/2024/llcp_varlayout_24_onecolumn.html).

The live annual pages also disclose federal-policy-related removals from the public files. These acquired releases are not claimed to be immutable first-release-day versions. The study uses only the explicitly documented required fields and verifies their observed distributions. No removed field is reconstructed.

## Outcome, employment and groups

The original core variable `MENTHLTH` reports days in the last 30 on which mental health was not good, including stress, depression and emotional problems. The cleaning rule is fixed:

- Values 1–30 remain their reported number of days.
- Code 88 means no such days and is recoded to 0.
- Code 77 means unknown/not sure; 99 means refusal; blank means missing/not asked. These records are excluded from the complete-outcome frame.
- `EMPLOY1=1` selects people employed for wages; `EMPLOY1=2` selects self-employed adults. The remaining employment categories, refused responses and missing employment are outside the frame.
- The analysis score is `health=(30-days)/3`, bounded by 0 and 10, with higher values meaning fewer reported mentally unhealthy days.

This rescaling does **not** create a validated wellbeing instrument, measure a psychiatric diagnosis, attribute mental health to a person's job, or make the outcome equivalent to the NHS People Promise burnout composite. The population is employed adult survey respondents across industries, not NHS employees or healthcare workers specifically. Employment status is retained as a category; no industry is inferred. Public industry/occupation modules vary across states and questionnaire versions and are not used here. [CDC module coverage](https://www.cdc.gov/brfss/questionnaires/modules/category2024.htm).

The 2023 release includes 48 states, DC and three territories; Kentucky and Pennsylvania are absent. The 2024 release includes 49 states, DC and three territories; Tennessee is absent. The main cross-year frame uses their **47 common states plus DC, 48 groups**, excluding territories. The files are independent cross-sections; `anonymrow` is a deterministic file-row identifier and must not be used as a person identifier across years.

| Cleaning stage | 2023 | 2024 |
|---|---:|---:|
| Complete public annual file | 433,323 | 457,670 |
| Employed/self-employed, before outcome filtering | 215,794 | 225,524 |
| Employed with valid mental-health days, all reporting areas | 212,989 | 222,734 |
| Excluded employed records with unknown/refused/missing mental-health days, all areas | 2,805 | 2,790 |
| Main common-state/DC frame | **206,098** | **214,151** |
| Main groups | 48 | 48 |
| Smallest / largest group | 1,247 / 13,474 | 1,232 / 22,708 |

Every main group has more than 1,200 retained respondents. This permits modest within-file sampling experiments, but does not guarantee any precision or power for an actual recruitment campaign. The principal outputs are `data/processed/brfss_employed_2023.csv` and `brfss_employed_2024.csv`. Both contain `year,state,state_name,health,weight,stratum,psu,anonymrow`, plus the raw-day recoding and employment fields. State and design-code columns should be read as strings. A combined two-year file and separate all-reporting-area files preserve the exclusion trail. Field definitions are in `brfss_data_dictionary.json`.

## Fixed-file targets and survey weights

The main target for each state/year is the **unweighted average over its retained, complete, employed respondent records in this particular public file**. The full file serves as a finite reference frame for offline evaluation. It is not latent individual mental-health truth, a census of employed adults, an unbiased state population estimate, or evidence about intervention benefit. 2023 may supply the declared calibration/prior quantities; the complete 2024 reference means, variances and unrevealed outcomes are reserved for evaluation and must not enter an acquisition policy.

`_LLCPWT` is the official final combined telephone-frame survey weight; `FINALWT` is not the current field name. `_STSTR` and `_PSU` preserve survey-design information. The published weights include adjustments/raking for the BRFSS sample, but they do not establish representativeness of a newly recruited sample or repair all item nonresponse in this employed complete-case subset. The primary unweighted replay does not silently treat these weights as one or equate its target with a population prevalence. [2023 complex-sampling guidance](https://www.cdc.gov/brfss/annual_data/2023/pdf/Complex-Sampling-Weights-and-Preparing-Module-Data-for-Analysis-2023-508.pdf), [2024 complex-sampling guidance](https://www.cdc.gov/brfss/annual_data/2024/pdf/Complex-Sampling-Weights-and-Preparing-Module-Data-for-Analysis-2024-508.pdf).

The reference table includes a separately labelled complete-file weighted ratio, `sum(w*health)/sum(w)`, and the weight-concentration diagnostic `(sum w)^2/sum(w^2)`. The latter is a Kish-style concentration count, **not** a full survey-design effective sample size: it ignores clustering, stratification, outcome dependence and nonresponse. Its state ranges are approximately 538–8,515 in 2023 and 512–9,729 in 2024. No measurement-error variance or population confidence interval is inferred from that diagnostic alone.

If a weighted sensitivity samples records uniformly, the usual subset ratio `sum_sample(w*health)/sum_sample(w)` is generally not exactly design-unbiased for the full-file weighted ratio. With a fixed within-state sample size, known complete-frame total weight `W`, and uniform inclusion probability `n/N`, the estimator `N*sum_sample(w*health)/(n*W)` is design-unbiased for that weighted finite-frame target. This alternative assumes access to the full frame's weights and still requires separate care under outcome-dependent stopping or adaptive sample counts. The data provider does not prescribe it as a validated acquisition rule. Uniform revelation is a controlled offline assumption; artificial recruitment tilts are simulation stress mechanisms, not estimates of actual BRFSS or workplace response bias.

## Source checks and one documented discrepancy

The parser verifies all 890,993 source records against the published annual totals. The complete-file `MENTHLTH` frequency categories and the two included `EMPLOY1` counts match each annual codebook exactly. All included weights are finite and positive; the three missing/refusal codes are not recoded as zero; all outcome ranges and anonymised row-ID uniqueness checks pass. Required ASCII offsets are read from the official SAS programs and independently checked by the validator using fixed offsets.

For 2023, every included record's separately supplied `_MENT14D` category agrees with the category recomputed from the core `MENTHLTH` answer. In 2024, **four Illinois employed records disagree**: their core responses are 3, 0, 0 and 2 days, while the supplied category alternates between zero-day and 1–13-day classes in the opposite pairing. Both national marginals still match the codebook, so marginal validation alone would miss this row-level inconsistency. The main score retains the original core answer; no value is corrected, no inconsistent record is selectively removed, and no substantive explanation for the discrepancy is invented. The parser manifest records the exact physical record ordinals and source checksums for auditability.

`data_tools/validate_brfss.py` completed successfully. It independently checked **420,249 cleaned rows** against original ASCII slices and compared all **457,670 records** in the 2024 ASCII and SAS-transport formats across the seven core/design fields. The six categorical/design fields agree exactly. Weight differences are confined to the ASCII decimal representation, with maximum absolute error `4.996510506316554e-5`. The four Illinois core/category inconsistencies occur identically in both official formats, confirming that they were not introduced by this CSV parser. All six derived CSV hashes stayed unchanged. The executed evidence is `data/processed/brfss_independent_validation.json`.

## Reproduction

From the new repository root:

```sh
python data_tools/fetch_brfss.py
python data_tools/parse_brfss.py
python data_tools/validate_brfss.py
```

The first two scripts use the Python standard library. Independent SAS-transport validation additionally requires NumPy and pandas. Downloads verify cached SHA-256 values and ZIP CRCs; a changed cached payload fails rather than being silently used. Upstream availability remains an external dependency. The data parser creates only derived data/provenance files and never modifies the original downloaded assets. The validator checks protected derived CSV hashes before/after its read-only comparison and writes only its own audit JSON.

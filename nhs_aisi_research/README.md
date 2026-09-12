# Which Uncertainty Is Worth Reducing?

**Budgeted Measurement for Wellbeing Prioritisation**  
Shengwei Zhang, University of Pennsylvania

This repository studies which additional measurements are useful before selecting a fixed number of low-scoring units for further wellbeing review. Repeated measurements can reduce sampling noise while leaving persistent channel bias unresolved. A second measurement channel may help, but its cost, remaining bias and decision relevance matter.

The method applies established Gaussian knowledge-gradient and multi-information-source ideas to a two-channel decision model. It does not introduce knowledge-gradient, claim globally optimal finite-budget allocation, establish an NHS intervention effect, or report a deployed NHS system. The NHS motivation, controlled simulations and public-record replay provide different kinds of evidence.

## Start here

- [Full manuscript (PDF)](paper/full.pdf), [technical supplement](paper/supplement.pdf) and [LaTeX source](paper/full.tex).
- [Results workbook](results/nhs_aisi_results.xlsx), [primary replay results](results/replay.csv) and [exploratory budget extension](results/replay_budget_extension.csv).
- [Analysis protocol](docs/analysis_protocol.md), [data audit](docs/microdata_audit.md) and [reproduction audit](docs/reproduction_audit.md).
- [One-page NHS discussion proposal](docs/nhs_decision_brief.pdf), [中文说明](docs/upgrade_summary_zh.md) and [citation metadata](CITATION.cff).

The preserved predecessor, [Before You Target](../nhs_wellbeing_research/README.md), studies ranking sensitivity and regression to the mean. This follow-up asks which additional measurements to acquire. The directory name records the intended AISI audience, not a claim of conference submission or acceptance.

## Data and executed studies

| Study | Actual scope | Interpretation |
|---|---|---|
| Synthetic | 2,000 paired panels per world, 40 units, 10 policies; 24 base cost-budget settings and seven stress worlds | Known latent targets under controlled assumptions. Base worlds are reused across settings; settings are not independent new datasets. |
| Primary BRFSS replay | 420,249 retained employed/self-employed respondent records across 47 common states plus DC: 206,098 in 2023 and 214,151 in 2024. Five scenarios, 18 cost-budget settings, 1,000 paired panels per scenario, 10 policies | 2023 supplies calibration; 2024 supplies hidden evaluation outcomes. With-replacement sampling from the recorded finite file, not new recruitment. |
| NHS illustration | 190 reporting units, corresponding to 189 identified legal entities, with complete comparable 2021–2025 histories; 36 within-peer-group review slots | Eight model-conditional scenarios. Bias SD and precision multipliers are assumed, not estimated NHS response bias or effective sample size. No additional NHS responses are observed. |
| Exploratory budget extension | 500 paired panels; fixed BRFSS ordinary tilt 0.5, validation cost 5, budgets 48, 144, 480 and 1,440; five policies | Specified after primary results were known and reported separately. It does not replace the primary study. |

The BRFSS outcome is `(30 - mentally unhealthy days)/3`, with higher scores indicating fewer reported unhealthy days. It is not the NHS burnout composite, a clinical diagnosis, or a measure specific to healthcare workers. The primary reference is an unweighted complete-file mean; weighted replay is a separately labelled finite-file sensitivity. Injected recruitment tilts are controlled mechanisms, not estimates of actual survey nonresponse bias.

Results include reversals. In primary unweighted BRFSS replay with tilt 0.5, validation cost 5 and budget 144 (the `unweighted_tilt_05` scenario, with an unbiased validation channel), two-channel KG has mean regret **0.18567**, versus **0.16146** for ordinary-channel KG. Their paired difference is **+0.02421**, with an approximate 95% Monte Carlo interval **[0.02124, 0.02719]**; positive is worse. In the exploratory extension, two-channel KG remains worse at budgets 48, 144 and 480, and is better at 1,440 (**0.09070 vs 0.12422**). At budgets 480 and 1,440 it spends all additional budget on the validation channel, so that result is not evidence of a balanced channel mixture. These intervals describe simulation uncertainty conditional on the files and protocol, not population or clinical uncertainty.

## Reproduce

Run commands from this project directory. If you cloned the parent `Bubu631/research` repository, first run `cd nhs_aisi_research`. The executed analysis used Python 3.13.1, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1 and matplotlib 3.11.1. The [requirements file](requirements.txt) also includes data, workbook and PDF dependencies:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The prepared data and result tables support offline analysis after dependencies are installed. To rebuild the public BRFSS inputs from their sources, download, parse and independently validate them:

```sh
python data_tools/fetch_brfss.py
python data_tools/parse_brfss.py
python data_tools/validate_brfss.py
```

Raw downloads are not needed to inspect the provided result tables or rerun the experiments from the prepared CSV inputs. Full data reproduction requires network access and disk space for the CDC ZIP files and derived CSVs. The parser streams ZIP members rather than expanding the large ASCII files. Original URLs, download times and hashes are in [the BRFSS source manifest](data/brfss_source_manifest.json); parsing and independent validation have separate manifests. Existing cached downloads are checked against recorded hashes. Fresh downloads are recorded in a new manifest, so compare them with the committed manifest before claiming byte-identical reconstruction of the original inputs. The NHS illustration reads the supplied derived panel in `data/processed/`; [its source manifest](data/nhs_original_source_manifest.json) and the [predecessor's data workflow](../nhs_wellbeing_research/README.md#rebuild-the-public-data-inputs) document the NHS sources separately from BRFSS.

Reproduce the full primary studies and the NHS illustration:

```sh
python experiments/synthetic.py --reps 2000
python experiments/replay.py --reps 1000
python experiments/nhs_scenarios.py
```

These commands write the standard result filenames. To preserve the supplied primary results while checking execution, use separate smoke filenames:

```sh
python experiments/synthetic.py --smoke --reps 20 --output synthetic_local_check
python experiments/replay.py --smoke --reps 20 --output replay_local_check
```

Run the mathematical, implementation and saved-result checks:

```sh
python experiments/verify_theory.py
python experiments/verify_allocation.py
python experiments/verify_implementation.py
```

Reproduce the separately labelled exploratory extension and its checks:

```sh
python experiments/replay_budget_extension.py
python experiments/verify_budget_extension.py
```

The extension uses a larger paired packet bank and checks a declared 2 GB process-memory bound. It is not part of the lightweight smoke check. Run `python experiments/report.py` to regenerate manuscript figures and tables from saved results. See `docs/analysis_protocol.md`, `docs/budget_extension_protocol.md` and run manifests for seeds, exact settings and versioned source snapshots. Re-running regenerates timestamps and may create a new source snapshot even when numerical outputs agree.

The [Makefile](Makefile) provides the same stages as `make primary`, `make exploratory`, `make verify`, `make figures`, `make paper` and `make workbook`. Plain `make` runs the full suite and recompiles the papers; it is not a smoke test. Use the explicit Python smoke commands above for a small check. Full runs and reporting replace their corresponding generated outputs; run them in a separate checkout when preserving the supplied artifacts. Avoid `make -j all`, because reporting and verification consume outputs produced by earlier stages. The exploratory memory check uses Python's Unix `resource` module; its supplied entry point requires macOS or Linux rather than native Windows.

To compile the supplied manuscript sources without rerunning the scientific studies, run `make paper`. This requires `latexmk`, pdfLaTeX, BibTeX and the LaTeX packages used in `paper/`, installed separately from Python. The signed full paper, anonymous formatting variant and supplement are separate files; the anonymous variant is a formatting artifact, not evidence of submission.

## Results workbook

[The results workbook](results/nhs_aisi_results.xlsx) contains the complete primary summary grids, area allocations, NHS scenario tables and a separate **Exploratory** sheet. The first sheet compares both KG policies across every supplied setting. Its formulas compute differences, intervals from the **paired** Monte Carlo standard error, and descriptive relative changes with a zero-denominator guard. They do not infer paired uncertainty from independent-policy standard errors. The ReadMe sheet defines fields, units, policies and source hashes.

Rebuild the Excel supplement from existing result CSVs:

```sh
python -m pip install openpyxl==3.1.5
python artifact_tools/build_results.py
python artifact_tools/verify_results.py --formulas-only
```

Excel recalculates formulas on opening. The delivered copy was additionally recalculated, inspected and rendered with the bundled artifact-tool engine; that optional release-QA tool is not required to run the scientific experiments or rebuild the workbook with openpyxl. The scientific calculations remain in Python. Workbook formulas are intentionally limited to transparent summaries of frozen results.

After a spreadsheet engine has recalculated and saved the workbook, `python artifact_tools/verify_results.py` also checks cached formula values. The supplied `results/workbook_validation.json` records the delivered file's independent cell-by-cell verification.

## Files and provenance

```text
data_tools/       Fetch, parse and independently validate CDC files
data/processed/   Cleaned public records, group references and NHS panel
experiments/      Allocation model, simulations, replay, reporting and checks
results/          Frozen summary CSVs, manifests, workbook and source snapshots
paper/            Manuscript source, references, figures and tables
docs/             Protocols, domain research, audits and interpretation
artifact_tools/   Supporting workbook and one-page decision-brief builders
```

The `results/provenance/` snapshots preserve executed scientific sources. The protocol records later amendments transparently; it is a local timestamped specification, not an externally registered protocol. The prior `nhs_wellbeing_research/` project is a separate preserved study, not a hidden dependency required to execute these Python experiments with the supplied inputs.

`artifact_tools/package_release.py` is the historical local-delivery packager. It also expects the predecessor's signed PDF in a sibling `output/release/` directory and checks its recorded hash. That external delivery directory is not required for analysis, workbook rebuilding or TeX compilation; the packager is not a standalone GitHub release command. The optional spreadsheet recalculation script requires the separately supplied `@oai/artifact-tool` runtime. Neither helper is needed to inspect the included CSVs or PDFs.

The optional decision-brief builder, `artifact_tools/build_decision_brief.py`, additionally requires `reportlab`, which is not in the scientific requirements file. Install it separately if rebuilding that PDF; the already-rendered brief is included. The PDF helper does not produce or alter scientific results.

## Data rights, intended use and authorship

The source for BRFSS is **CDC BRFSS**. Its federally published data are supplied under CDC's stated public-domain and attribution guidance, with exceptions for some third-party materials. Original CDC materials are available without charge from the agency. The cleaning and score rescaling in this repository are project transformations, not replacement official CDC files. This independent research is **not endorsed by CDC, HHS or the United States Government**. See [CDC BRFSS FAQ](https://www.cdc.gov/brfss/about/brfss_faq.htm) and [agency-materials terms](https://www.cdc.gov/other/agencymaterials.html). NHS materials retain their original rights. Data and questionnaire permissions are separate from permission to use this project's code; no blanket licence is claimed for third-party sources. Questionnaire reuse and any future staff-data collection require the relevant permissions and governance.

No NHS partnership, stakeholder interview, co-design, additional survey, field trial or deployment took place. Proposed use concerns additional information gathering while preserving universal access to established feedback channels. It does not allocate clinical or wellbeing services. The one-page discussion proposal in `docs/nhs_decision_brief.pdf` has not been sent to NHS organisations.

AI assistance was used in literature research, code development, auditing and writing. The named author remains responsible for verifying the methods, data rights, findings and references, and for any submission or release. The repository is not evidence of publication or acceptance. AAAI-27's regular AISI submission deadline was 28 July 2026 and had passed when this work was prepared; an AISI-oriented manuscript is not an accepted or submitted AISI paper.

## Release verification

A fresh isolated-directory rerun in the same local runtime reproduced all 10 scientific result CSVs byte-for-byte and all 200 retained exploratory replication arrays exactly (maximum numerical difference zero). See `docs/reproduction_audit.md` and `results/reproduction_verification.json`. This is same-environment reproducibility, not evidence of cross-platform bitwise agreement or a new independent scientific sample. Independent implementations separately checked the mathematical updates and selected full result rows.

The signed paper has 24 pages, the AAAI-style anonymous paper 6 pages including references, and the technical supplement 15 pages. The locally extracted arXiv source archive compiled successfully and its extracted page text matched the signed PDF. This is a local TeX check, not arXiv moderation or a server-side acceptance test. All final PDF pages were rendered, references resolved and embedded fonts checked. Source/anonymous packages and the original release remain separate.

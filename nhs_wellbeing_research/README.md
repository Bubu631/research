# Before You Target

**Ranking Sensitivity and Regression to the Mean in NHS Staff Wellbeing Data**

Shengwei Zhang, University of Pennsylvania.

This repository contains the manuscript, executed analyses, source provenance and reproducibility checks for a study of selecting low-scoring organisations for additional wellbeing review. It contains no claim of journal acceptance or conference publication.

This is the preserved first study in the NHS wellbeing research line. The follow-up, [Which Uncertainty Is Worth Reducing?](../nhs_aisi_research/README.md), studies the choice of additional measurement channels and retains this study separately. The two projects answer different questions; the follow-up does not replace these data or results.

## Start here

- [Full manuscript (PDF)](paper/main.pdf) and [LaTeX source](paper/main.tex).
- [Results workbook](artifacts/nhs_wellbeing_results.xlsx), [harmonised results](results/harmonised/test_metrics.csv) and [historical-vintage results](results/vintage/test_metrics.csv).
- [Analysis protocol](docs/analysis_protocol.md), [data dictionary](data/processed/data_dictionary.json) and [independent empirical checks](docs/empirical_independent_audit.md).
- [中文说明](docs/第三篇论文说明.md).

## Scientific question

When a survey places an organisation near the bottom of its comparison group, how stable is that ranking to assumptions about measurement noise? Does averaging older surveys improve a forecast when underlying conditions change? What does a subsequent increase or decrease among selected organisations say about intervention effects?

The study distinguishes four targets: current latent severity, membership of a true lowest-scoring set, a future observed survey score, and the benefit of an intervention. They require different information and losses. Predicting a later observed score does not establish recovery of latent need or identify the effect of spending.

The statistical foundations are established: Gaussian conditioning, autoregressive working models, regression to the mean, empirical Bayes reasoning and loss-dependent ranking. The contribution is their explicit connection to this decision, with conditional identities, counterexamples, exact pair-crossing sensitivity calculations and a provenance-audited NHS application. This is not a new general empirical Bayes estimator or a claim to have discovered regression to the mean. Close prior work and the limits of novelty are documented in [the literature audit](docs/literature_audit.md).

## Actual data and experiments

The official English NHS Staff Survey provides organisation-level burnout sub-scores for 2021–2025. The public panel has 238 reporting units and 1,190 rows, including missing histories. The primary complete-history cohort has **190 reporting units representing 189 known legal entities**: R1F1 and R1F2 are two reports of the same legal trust. These records are organisations and reporting sectors, **not hospital departments**. Higher scores on the 0–10 burnout scale mean less burnout.

Two empirical analyses use the same seven predictor families and fixed development/test split:

- A harmonised historical holdout uses the 2025 workbook, whose older scores have been retrospectively reweighted and revised.
- A historical-vintage backtest uses the archived 2023 workbook for development predictors and the archived 2024 workbook for final predictors. The final target is the published 2025 score. Archive captures establish availability by their capture dates; they do not prove exact first-publication-day bytes. The cohort still depends on eventual five-year availability.

Development predicts 2024 from 2021–2023. Final evaluation predicts 2025 from 2021–2024 using the development-selected settings. All 58 candidate configurations and all seven methods are retained. Primary uncertainty uses 5,000 paired resamples of 189 legal entities, always taking the two R1F records together. These descriptive intervals condition on the selected predictions and do not incorporate every source of uncertainty.

The archived-vintage mean-reversion rule has RMSE 0.1274 versus 0.1301 for the latest-score baseline; its paired interval for improvement includes zero. The observed 2024 low-score group declines in 2025 even though it improves relative to its benchmark groups. Across the declared static working-model noise-ratio range, 34 of the 36 originally selected units remain selected throughout. These results do not justify a universal reliability cutoff or a claim that complex pooling always helps.

The standard simulation comprises **120 Gaussian parameter cells × 5,000 independent panel repetitions = 600,000 independent panel draws**. Each panel has 80 simulated units. Five methods and three selection fractions are evaluated on shared draws; they are not additional independent repetitions. Four separate stress cells examine heavy tails, a negative common trend, persistent response bias and strong temporal measurement-error dependence. Synthetic latent truth and the explicitly simulated no-intervention process are kept separate from NHS observations.

No available NHS field records intervention assignment, its cost, verified absence of intervention, or actual individual turnover. Nominal response counts are not effective sample sizes. The study does not estimate causal wellbeing effects, department-level reliability, or optimal monetary budget allocation. [Data audit](docs/data_audit.md), [historical-vintage audit](docs/vintage_audit.md), and [analysis protocol with amendments](docs/analysis_protocol.md) give the full scope.

## Environment and quick reproduction

The scientific runs used CPython 3.13.1 on macOS arm64 with the exact package versions in [requirements.txt](requirements.txt). The computations use CPU NumPy/SciPy; no pretrained model, GPU service or private dataset is required.

Run from this project directory. If you cloned the parent `Bubu631/research` repository, first run `cd nhs_wellbeing_research`:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make check-env
make help
```

`make` alone prints help. Every substantive stage is explicit. The prepared CSV data and saved result tables allow an offline scientific replay:

```sh
make analysis
make simulation
make checks
make report
make latex
```

Alternatively, `make all` runs those stages sequentially. It does not download data. It replaces each stage's generated outputs in `results/` and `paper/`; use a separate checkout if preserving the original generated files is important. Execution timestamps and environment metadata can differ on a replay. Numerical reproducibility should be checked at the tolerances documented by the verification scripts rather than by expecting every manifest to have an identical hash.

The full simulation took about 51 seconds on the original machine; timing is hardware-dependent. To check the simulation entry point without replacing manuscript results, run `make simulation-smoke`. This uses 20 repetitions per cell and writes `simulation_smoke*` files. Those files are not used to generate manuscript figures.

`make checks` executes independent algebra/implementation checks and an independent recomputation of the empirical predictors, metrics and static ranking geometry. It also tests that perturbing future scores and future nominal counts does not alter the fixed-cohort development settings or forecasts. The checks write their own audit JSON files and verify that protected empirical data and results remain unchanged. Passing them does not prove all model assumptions or constitute human peer review.

Set `PYTHON=/path/to/python` to use another environment. `make latex` requires an installed TeX distribution providing `latexmk`, pdfLaTeX, BibTeX and the packages listed in `paper/main.tex`; TeX Live or MacTeX provides these outside Python. It compiles existing generated figures and tables. Set `LATEXMK=/path/to/latexmk` if needed.

The code archive additionally includes `artifacts/nhs_wellbeing_results.xlsx` as a convenient static review snapshot. It is not required for scientific calculations. Its optional builder uses `@oai/artifact-tool` from the Codex bundled runtime (bundle 26.905.11957), outside the Python analysis dependencies. In an environment providing that package, `NHS_RESULTS_OUTPUT=artifacts node artifact_tools/build_results.mjs` rebuilds it inside the repository; without this override the builder uses `../output/release/` and creates that directory when needed. The saved-file verifier uses the same `NHS_RESULTS_OUTPUT` directory override. The standalone Python/TeX workflow does not require access to the artifact tool.

## Rebuild the public data inputs

Raw third-party workbooks, PDFs, questionnaires and extracted full texts are local audit caches rather than redistributable research-code assets. To obtain them again from the recorded official and archive URLs:

```sh
make data-fetch
make data-parse
make data-checks
make vintage-data
```

`vintage-data` also ensures the primary sources and parsed panel exist, copies the four unchanged annual detailed ZIPs to the vintage parser's expected cache paths, retrieves the two selected historical benchmark captures, and parses and validates them. Existing source files are verified and reused. Network access and continued upstream/archive availability are required for retrieval. The archived benchmark retriever checks newly fetched and cached files against the recorded SHA-256 and archive CDX SHA-1 digests. The official-source fetcher checks existing caches, but records new hashes when files are downloaded again. Preserve the committed source manifest and compare any refreshed hashes before treating newly downloaded files as the original study inputs. The official annual-release material is not substituted for the multi-year archived predictor histories used in the main vintage backtest.

The main data parser needs openpyxl, included in the analysis requirements. Optional PDF-to-text documentation extraction originally used a separate bundled environment pinned by [data_tools/requirements-data.txt](data_tools/requirements-data.txt), including pypdf 6.10.0. To replay that ancillary extraction, create a separate environment:

```sh
python3.13 -m venv .venv-data
.venv-data/bin/python -m pip install -r data_tools/requirements-data.txt
make data-docs DATA_PYTHON=.venv-data/bin/python
```

The original PDFs remain the documentation authority. The primary analysis does not depend on text-extraction output. Every published numerical source cell has a locator and source hash in the complete panel CSV. The recorded correction to three optional proportion fields affected none of the reported prediction or ranking inputs; the final parser and independent detailed-workbook comparison preserve their correct 0–1 units.

## Data rights and attribution

The [official local-results page](https://www.nhsstaffsurveys.com/results/local-results/) supplies the current benchmark data. The [official technical documentation](https://www.nhsstaffsurveys.com/survey-documents/) explains weighting, missingness and comparability. Exact URLs, retrieval times and digests appear in the source manifests.

Public accessibility does not establish a licence to redistribute every source file. A permissive asset-specific licence has not been verified for the current 2021–2025 files; older catalogue metadata is not treated as proof that its licence applies to these assets. The [official FAQ](https://www.nhsstaffsurveys.com/faqs/) separately describes permission requirements for reusing the survey questionnaire for other purposes. This project analyses published aggregate results and does not administer a new survey. No source data, questionnaire or technical guide is claimed as the author's original work or placed under a blanket software licence.

## Files

```text
paper/                 Manuscript source, bibliography, generated tables and figures
experiments/           Scientific analysis, simulation, reporting and verification
data_tools/            Official-source retrieval, panel parsing and validation
data/processed/        Tidy panel, dictionary, cohort/comparability and validation
data/source_manifest.json
                       Official source URLs, access times, hashes and rights status
vintage_data/          Archive-retrieval/parsing code, manifests and prepared vintage CSVs
results/               Executed scientific result tables and run/audit manifests
docs/                  Protocol, source/theory/literature audits and Chinese explanation
artifact_tools/        Optional supporting-workbook builder and saved-file verification
artifacts/             Supporting XLSX included by the code-archive packager
```

Large raw caches, generated Python environments, local dependency links and preview images are not required in a public source archive. The prepared CSVs and provenance enable inspection without silently treating raw source materials as newly licensed content.

`artifact_tools/build_release.py` preserves the original release-packaging workflow. It expects release outputs in a sibling `output/release/` directory and is not part of the commands needed to reproduce the scientific analysis. The files linked above can be read directly from this checkout.

## AI assistance and author responsibility

AI tools assisted with literature discovery, source retrieval, coding, mathematical review, writing and reproducibility checks. Automated results were compared with source records and independently implemented calculations where documented. Shengwei Zhang is the named author and remains responsible for the research claims, source attribution, code, data interpretation and any eventual submission. AI assistance and successful automated checks do not establish independent human scientific review, publisher acceptance or institutional endorsement.

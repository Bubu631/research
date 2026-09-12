# Independent empirical verification

Completed on 11 September 2026. The executable audit is `experiments/verify_empirical.py`; its complete checks, input/output SHA-256 hashes and recomputed values are in `results/empirical_independent_audit.json`. All **26 protected analysis inputs, source files and saved empirical outputs remained byte-identical** during this audit. No model, hyperparameter, cohort or result was changed.

## Result

The independent recomputation passed. It reconstructed the 190-unit cohort from the source CSV, checked that both historical predictor vintages contain these units with the same benchmark groups, and reproduced both empirical analyses:

- All **58 development configurations** per analysis, their order, scores and selected settings.
- All seven methods and **1,330 frozen 2025 predictions** per analysis.
- RMSE, MAE, Spearman correlation and observed bottom-10%, 20% and 30% overlap, globally and within all five benchmark groups.
- The point differences reported alongside the cluster-bootstrap intervals.
- All four observational selective-follow-up rows.
- The full static-rank crossing enumeration, interval envelope, five first-membership thresholds, seven sensitivity-grid summaries, and 1,330 grid membership records.

The verifier implements the predictors independently. It fits linear trends using an explicit least-squares design matrix and evaluates the working-covariance predictor using a direct linear-system solve for each unit. The singular persistence-one/no-noise case is evaluated by its exact rank-one mean formula. It does not call the original prediction function for these comparisons. Spearman correlation is independently computed as Pearson correlation of average-tie ranks. Bottom fractions use the declared floor rule and deterministic organisation-code order. Static crossings are recalculated with 60-digit Decimal arithmetic using a separately arranged rational equality, then checked at every crossing, interval midpoint and sensitivity-grid value.

There were **1,528 numeric comparison checks**. Prediction differences were at most `2.6645352591003757e-15`. The largest overall absolute difference, `2.346496330574155e-9`, occurred in a distant ranking threshold near 24,822, reflecting harmless floating-point group-mean/crossing arithmetic. All crossing counts, membership sets and declared thresholds agree at the stated precision.

## Recomputed outcomes

Both reporting-frame analyses choose geometric-history persistence 0, group mean reversion persistence 0.85, and working covariance persistence 0.85 with noise ratio 300. A persistence of 0 makes the selected geometric-history method exactly the latest-score baseline.

| Predictor | Harmonised 2025 RMSE | Historical-vintage 2025 RMSE | Harmonised bottom-20% overlap | Historical-vintage bottom-20% overlap |
|---|---:|---:|---:|---:|
| Latest score | 0.12962343 | 0.13007553 | 0.638889 | 0.638889 |
| Equal history | 0.13698942 | 0.13655499 | 0.527778 | 0.527778 |
| Group-centred equal history | 0.14677202 | 0.14720834 | 0.527778 | 0.527778 |
| Linear trend | 0.21131048 | 0.21259103 | 0.638889 | 0.638889 |
| Geometric history | 0.12962343 | 0.13007553 | 0.638889 | 0.638889 |
| Group mean reversion | 0.12701092 | 0.12744702 | 0.638889 | 0.638889 |
| Working covariance | 0.12855680 | 0.12905821 | 0.611111 | 0.638889 |

These are descriptive predictions of observed future scores. They do not establish latent-need accuracy, statistically established superiority, or intervention benefit. The larger working model has lower development MSE but is not the best final predictor on these point metrics. Its harmonised bottom-20% overlap is below the latest-score baseline.

For the static sensitivity over the prespecified ratio interval `[0, 3000]`, 270 distinct pair crossings yield 548 distinct crossing/midpoint/grid probes. Of the 36 originally selected units, **34 remain selected everywhere**, while **38 units are selected somewhere**. The first membership crossing for acute/acute-community trusts is approximately **234.599908**; the other four groups remain unchanged through 3000. Ambulance, community, and mental-health/learning-disability thresholds are approximately 11,990.8444, 3,377.42614, and 24,822.3610 respectively; the acute-specialist group has no finite first crossing. These are certificates conditional on the specified static model, centring, tie rule and ratio interval.

## Temporal information audit

The harmonised analysis selects settings by predicting 2024 using 2021–2023 scores from the 2025 reporting frame, then predicts 2025 from 2021–2024. Its historical observations incorporate the 2025 workbook's retrospective weighting and revisions, so it is not a real-time forecasting experiment.

The historical-vintage analysis uses 2023-vintage 2021–2023 inputs and 2024-vintage 2024 outcomes for development; it then freezes the selected settings and predicts 2025 from the 2024-vintage 2021–2024 sequence. Its target is the observed 2025 result. No numerical 2025 outcome or 2025 nominal count enters either setting selection or prediction. Capture times and exact-byte availability limits are documented in `docs/vintage_audit.md`.

A separate metamorphic test executes the **original**, unmodified analysis logic in isolated temporary directories. It replaces each available 2025 score with `10 - score` and multiplies each 2025 burnout base count by seven. In both variants, the 58-row development grid and selected-settings JSON remain byte-identical, and every one of the 1,330 predictor values remains identical. The target values do change, confirming that the perturbation actually reaches the evaluation data. The test intentionally bypasses bootstrap resampling and provenance writes inside the scratch runs; it does not edit the protected analysis outputs. This test exercises information flow and is distinct from the independent numerical implementation above.

Two qualifications remain essential. First, the cohort is retrospectively restricted to organisations with a complete, comparable 2021–2025 history and stable eventual group labels. Thus the vintage analysis removes historical **measurement-vintage** leakage conditional on this cohort, but does not establish a fully prospective cohort-selection process. Second, the source code and saved local timestamps support the documented workflow but cannot by themselves prove that an analyst never inspected outcomes before the recorded specification. The local protocol is not an externally registered trial or prospective deployment.

## Bootstrap interpretation and verification

The independent source `legal_org_code` field confirms 189 legal entities among 190 reporting units. The only repeated entity is R1F, represented by R1F1 and R1F2. The current implementation samples 189 entity labels with replacement, assigns both R1F records the same multiplicity, and divides weighted squared/absolute error by the realised number of reporting records. It applies the same resampling weights to each candidate and the latest-score baseline.

Thirty-seven independently generated explicit entity-block resamples confirm the weighting algebra, shared R1F multiplicity and variable denominator. All saved bootstrap point contrasts and repetition/cluster counts match. The saved 5,000-draw percentile limits were inspected but were **not independently regenerated** in this audit. The current code uses unstratified entity resampling; the protocol records its replacement of the original reporting-unit stratification, and the original stratified outputs remain separately labelled.

These intervals condition on the selected models, fitted predictions, reporting-unit cohort and one final year. They exclude hyperparameter-selection uncertainty, measurement-error identification, unknown dependence across legal entities and future deployment shifts. The ratio estimator continues to target an equally weighted reporting-unit average; it is not a workforce-size-weighted or equally weighted legal-entity estimand.

## Reproduction

After activating the repository environment with NumPy, pandas and SciPy, run:

```bash
python experiments/verify_empirical.py
```

The script writes only its own `results/empirical_independent_audit.json`. It asserts that all protected empirical result files and input sources retain their original hashes. Formula/metric recomputation requires NumPy; the isolated original-pipeline perturbation additionally uses pandas and SciPy.

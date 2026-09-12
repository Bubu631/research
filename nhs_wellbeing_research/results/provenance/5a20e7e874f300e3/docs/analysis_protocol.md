# Analysis protocol

Recorded on 2026-09-11 at 18:42 UTC, before the analyst inspected the NHS panel's numerical outcomes. This is a local, prospective analysis specification, not an externally registered protocol. The data-acquisition agent may inspect data to establish its schema and integrity. Deviations will be recorded rather than silently replaced.

## Question and scope

Evaluate how measurement noise, temporal change, and selective follow-up affect worst-first prioritisation using organisation-level NHS Staff Survey data. Lower burnout sub-scores indicate less favourable staff experience. The decisions studied are equal-cost selection of units for additional assessment; actual monetary allocation also requires intervention benefits, costs, workforce sizes, and equity objectives not supplied by these data.

The source outline is a research proposal, not empirical evidence. Its numerical tables, universal sample-size cutoffs, supposed guaranteed rebound, and causal upper-bound interpretation are not accepted as findings. Claimed personal authorship of another article in the outline is not attributed to Shengwei Zhang.

## Data

Use official NHS Staff Survey organisation-level burnout sub-scores for 2021–2025 and published respondent counts, response rates, organisation codes, benchmark groups, and explicit historical-comparability flags. Trusts with a comparable five-wave history form the primary cohort. Voluntary organisations, discontinuities, group changes, and missing cells are reported. No missing workforce denominator is reconstructed from a national response rate. Nominal respondent counts remain a size proxy, not an effective sample size. Do not derive individual-level variance or departmental error distributions from organisation means without additional assumptions.

## Empirical temporal split

- Development: predict 2024 from 2021–2023, using 2024 only to choose predeclared hyperparameters.
- Final evaluation: predict 2025 from 2021–2024 with development-selected settings. No changes to methods or tuning grids based on final test outcomes.
- Baselines: latest score; full-history equal-weight mean; recency-weighted mean; a fitted linear trend; a group-centred mean-reverting forecast; and a group-centred stationary Gaussian working-covariance predictor under fixed noise/persistence candidates.
- Persistence candidates: 0, 0.3, 0.6, 0.85, 0.97, 1. Noise-to-latent-variance ratios, multiplied by inverse nominal respondent count: 0, 10, 30, 100, 300, 1000, 3000. These are sensitivity/tuning parameters, not estimated individual response variances.
- Tune by equally weighted organisation-level squared prediction error. Resolve ties deterministically by declared candidate order. Report all development scores and frozen 2025 predictions.
- Evaluate RMSE, MAE, Spearman correlation, and overlap with the following year's observed bottom fraction within benchmark groups. Primary fraction 0.2; 0.1 and 0.3 are descriptive sensitivity analyses. This overlap is not accuracy against latent truth.
- Use paired bootstrap resampling of entire organisation trajectories within benchmark groups (5,000 repeats) for descriptive performance-difference uncertainty; this does not capture arbitrary between-organisation dependence or deployment shifts.

## Selective follow-up and robustness

For each consecutive year pair, select the current observed bottom 20% within benchmark group and report observed mean change, whole-group mean change, and their difference. These are observational descriptions, not zero-intervention estimates or causal effects. No unrecorded wellbeing intervention is treated as absent.

For static Gaussian shrinkage, vary the unidentified ratio of measurement to latent variance, obtain exact pair-crossing thresholds, and report how selected membership changes. Use within-group centring. A stability certificate is conditional on this working model and a specified parameter interval.

## Simulations

Simulations provide latent truth and an explicit no-intervention DGP, kept separate from real-data claims. Simulate five observed waves plus one next wave, independent organisations, latent stationary AR(1) states with mean 5 and standard deviation 0.35, and Gaussian observation error with variance proportional to inverse respondent count. Cross four size ranges (20–120, 40–250, 150–600, 800–3000), five persistence values (0, 0.3, 0.6, 0.85, 0.97), three noise scales (1, 6.25, 25), and two observation-error autocorrelations (0, 0.5). Use 5,000 independent panel repetitions per cell, 80 organisations, and report fractions 0.1, 0.2, 0.4 using shared panel draws. The multiple methods/fractions are paired evaluations, not independent repetitions.

Compare raw, equal-history, geometric-history, correctly specified Gaussian posterior, and posterior assuming independent measurement errors. Report latent selection regret, true-bottom-set overlap, state MSE, actual simulated rebound, and its analytically predicted conditional expectation. Additional prespecified stress cases use heavy-tailed observation errors, an adverse common trend, and persistent unit-specific response bias. Gaussian draws need not remain in [0,10]; report out-of-range frequency and do not represent these synthetic values as NHS records.

## Reporting discipline

Retain negative results and failed modelling assumptions. Distinguish verified algebra, Monte Carlo checks, model-dependent sensitivity, and observed outcomes. All figures and numerical tables must be generated from saved executed results. Human scientific review is not asserted by the presence of automated checks. Authorship is Shengwei Zhang, University of Pennsylvania; manuscript date does not replace actual acquisition and execution timestamps.

## Data-availability amendment before outcome analysis

On 2026-09-11, before running the empirical model comparison, official documentation showed that the 2025 benchmark workbook retrospectively reweights historical scores using 2025 occupational proportions. Its temporal split is therefore labelled a retrospectively harmonised holdout, not a real-time forecast. A second, explicitly reported annual-release sensitivity uses each survey year's original organisational-results workbook for its contemporaneously published score. Original files retrieved now may contain documented corrections; this is not a claim that every retrieved byte was available on the historical publication day. The same candidate grid, development/test years, and metrics apply to both panels. Valid burnout-composite counts are used as the nominal precision proxy where available. Officially non-comparable histories are excluded from the primary panel. Any restriction required to align cohorts across vintages will be reported.

## Dependence amendment after data provenance audit

The data audit established that the 190 complete trust reporting units include R1F1 and R1F2, two reports of the same legal organisation. The primary uncertainty analysis therefore resamples the 189 known legal entities and keeps these two records together. It uses 5,000 paired cluster-bootstrap samples and reweights the reporting-unit average by the realised number of resampled reporting records. This replaces reporting-unit stratification for the main intervals. The earlier stratified intervals are retained as a labelled sensitivity output. Predictions, tuning settings, point metrics and cohort membership are unchanged. This amendment was motivated by documented dependence, not by the direction of the intervals. It does not resolve unknown wider cross-organisation dependence or include training/hyperparameter uncertainty.

## Retrieved historical benchmark clarification

The data-availability amendment initially anticipated a fallback made by joining separately published annual scores. Subsequent archive retrieval recovered the actual multi-year benchmark workbooks: the 2023 release captured on 2024-07-05 and the 2024 release captured on 2025-04-27. The executed vintage backtest uses these single-release histories, rather than a splice of annual snapshots. All 190 primary units are comparable in both archives with the same canonical groups. The cohort remains defined using 2025 complete-history eligibility; this is disclosed. This clarification changes data sourcing, not the previously declared predictor families or hyperparameter grids.

## Optional-field unit correction

A supplementary-workbook visual check identified an erroneous factor of 0.01 in three optional proportion fields (wellbeing_action, intent_leave and work_related_stress). The primary burnout scores, nominal counts, response rates, cohort and all prediction inputs were unaffected. The parser and independent validation were strengthened against a separate detailed-results workbook, all three fields corrected, and derived cohort exports refreshed. Earlier files are retained locally for the audit, not presented as final data. None of these optional measures enters the reported prediction or ranking models.

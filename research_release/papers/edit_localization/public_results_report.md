# Public post-edit experiment: completed result report

This report describes 1,024 evaluated public human post-edit examples across two language pairs, including 256 reporting examples per pair and separate 256-example diagnostic populations. The original archived MT was produced by the dataset's logging systems, not by the OPUS-MT models used for fixed gradient evaluation here. All selection probabilities are injected; edit fraction uses completed PE labels and is an oracle experimental mechanism, not a preannotation observable deployed propensity model.

The parameters tested here are a new shared output-logit bias adapter. Losses use each sentence's mean over all PE tokens including EOS. All gradients are paired at one checkpoint. These results do not establish full-model behavior, real complaint identification, or decoded translation-quality gains.

## en-de: completed results

Frozen model: 74,410,496 parameters; 512 selected examples, 256 reporting; runtime 52.97 seconds (excluding initial downloads).

| Mechanism | rho_Q(0) | rho_Q(1) | rho_P(0) | rho_P(1) | ||b_U|| | Interior stationary alpha |
|---|---:|---:|---:|---:|---:|---|
| edit | 0.454296 | 0.347345 | 0.745369 | 0.381626 | 0.00308824 | 0.02698411 |
| length | 0.209910 | 0.130783 | 0.201990 | 0.129282 | 0.00141234 | none |
| edit_length | 0.227201 | 0.154086 | 0.273153 | 0.155924 | 0.00156677 | none |

Oracle density-ratio IPW recovers the matching localized mean to maximum norm residual 2.34e-18; this is a finite-population numerical identity under known injected selection, not propensity estimation from real complaints.

Baseline full-PE NLL: 0.792899 nats/token. Across the 90 predeclared one-step adapters, NLL changes ranged from -0.00120047 to -0.00000302. These models were adapted only on diagnostic examples.

| Mechanism, alpha=1, step=10 | Population P | Sampled Q | Oracle IPW |
|---|---:|---:|---:|
| edit | -0.00106773 | -0.00120047 | -0.00107502 |
| length | -0.00106773 | -0.00097301 | -0.00094216 |
| edit_length | -0.00106773 | -0.00114055 | -0.00115976 |

The following grid minima are descriptive, computed after reporting outcomes; they were **not** used to select any adapter or amend any protocol.

| Mechanism | Estimator | Fixed-target MSE minimum alpha | Exact MSE |
|---|---|---:|---:|
| edit | unweighted | 0.60 | 0.00018903124 |
| edit | oracle_ipw | 0.45 | 0.00012328386 |
| length | unweighted | 0.60 | 0.00012327882 |
| length | oracle_ipw | 0.55 | 0.00014292575 |
| edit_length | unweighted | 0.60 | 0.00014382988 |
| edit_length | oracle_ipw | 0.55 | 0.000125349 |

## en-zh: completed results

Frozen model: 77,943,296 parameters; 512 selected examples, 256 reporting; runtime 50.77 seconds (excluding initial downloads).

| Mechanism | rho_Q(0) | rho_Q(1) | rho_P(0) | rho_P(1) | ||b_U|| | Interior stationary alpha |
|---|---:|---:|---:|---:|---:|---|
| edit | 0.220391 | 0.087703 | 0.277139 | 0.092637 | 0.00444897 | none |
| length | 0.092798 | 0.036710 | 0.087348 | 0.036709 | 0.00213596 | none |
| edit_length | 0.114795 | 0.052881 | 0.126704 | 0.054384 | 0.00217097 | none |

Oracle density-ratio IPW recovers the matching localized mean to maximum norm residual 1.46e-17; this is a finite-population numerical identity under known injected selection, not propensity estimation from real complaints.

Baseline full-PE NLL: 1.970116 nats/token. Across the 90 predeclared one-step adapters, NLL changes ranged from -0.03935879 to -0.00127651. These models were adapted only on diagnostic examples.

| Mechanism, alpha=1, step=10 | Population P | Sampled Q | Oracle IPW |
|---|---:|---:|---:|
| edit | -0.03649765 | -0.03935879 | -0.03896258 |
| length | -0.03649765 | -0.03539278 | -0.03386450 |
| edit_length | -0.03649765 | -0.03632930 | -0.03439309 |

The following grid minima are descriptive, computed after reporting outcomes; they were **not** used to select any adapter or amend any protocol.

| Mechanism | Estimator | Fixed-target MSE minimum alpha | Exact MSE |
|---|---|---:|---:|
| edit | unweighted | 0.85 | 0.00032622596 |
| edit | oracle_ipw | 0.85 | 0.00042552972 |
| length | unweighted | 0.90 | 0.00030199129 |
| length | oracle_ipw | 0.90 | 0.00035000091 |
| edit_length | unweighted | 0.90 | 0.00030757448 |
| edit_length | oracle_ipw | 0.90 | 0.0003463067 |

## Interpretation

In all six reporting scenarios, alpha=0 has larger rho_Q than alpha=1. However, English–German edit-based selection is not globally monotone: the exact ratio-of-quadratics derivative has an interior maximum near alpha=0.026984. Its untouched-span bias is nonzero, so the unbiased-untouched simplification is not applicable. The measured inner products and complete polynomial coefficients support analysis by the general derivative criterion. Oracle IPW restores the localized expectation, but it does not uniformly beat unweighted sampled-Q adaptation on held-out NLL. Both observations are retained.

The second language extension was frozen after the first run and is disclosed as such. Model pretraining contamination was not measured. The full arrays, deterministic original line IDs, runtime versions, hashes, exact executed source snapshots, and protocol snapshots are in the corresponding results directories.

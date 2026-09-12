# Post-primary-run exploratory budget extension: complete results

Results were generated after the primary comparisons, under the prospectively recorded local extension grid. No primary result was replaced. All 20 requested policy/budget cells are included. This is 500 independent paired replay replications reused across the grid, not 10,000 independent frames.

## Fixed scenario

Unweighted 2024 BRFSS eligible-record frame, 48 areas, lowest nine selected; frozen 2023 calibration; controlled ordinary tilt kappa=0.5, uniform validation; packet size 20 draws with replacement; packet costs 1 and 5. Budget excludes the common initial 20 draws per area. The posterior remains a working Gaussian model; the controlled offsets have a two-point sign distribution and real finite-record outcomes are not Gaussian.

## All policy means

Average severity regret in the constructed 0–10 score units, lower is better. Parentheses contain MCSE.

| Additional budget | Ordinary KG | Two-channel KG | Balanced random mix | Validation-only random | Ordinary uniform |
|---|---:|---:|---:|---:|---:|
| 48 | 0.179383 (0.002085) | 0.195734 (0.001995) | 0.197175 (0.002053) | 0.198607 (0.001954) | 0.198785 (0.001977) |
| 144 | 0.159294 (0.002042) | 0.186679 (0.002048) | 0.189744 (0.002061) | 0.188214 (0.001941) | 0.181474 (0.002031) |
| 480 | 0.136747 (0.001912) | 0.149974 (0.001905) | 0.179953 (0.002086) | 0.163498 (0.001888) | 0.160498 (0.002067) |
| 1440 | 0.124217 (0.001787) | 0.090698 (0.001536) | 0.149887 (0.001840) | 0.122878 (0.001750) | 0.138042 (0.001909) |

## Paired two-channel KG differences

Positive differences mean greater regret. Intervals are mean +/- 1.96 paired Monte Carlo standard errors, conditional on the fixed frame and this sampling scenario; they are not survey confidence intervals or multiplicity-adjusted confirmatory tests.

| Budget | Versus ordinary KG | Paired MCSE | 95% MC interval | Versus ordinary uniform | Paired MCSE | 95% MC interval |
|---|---:|---:|---|---:|---:|---|
| 48 | +0.016350 | 0.001847 | [+0.012729, +0.019971] | -0.003051 | 0.001719 | [-0.006420, +0.000318] |
| 144 | +0.027385 | 0.002161 | [+0.023150, +0.031620] | +0.005204 | 0.002190 | [+0.000913, +0.009496] |
| 480 | +0.013227 | 0.002295 | [+0.008728, +0.017726] | -0.010525 | 0.002438 | [-0.015303, -0.005747] |
| 1440 | -0.033518 | 0.002253 | [-0.037933, -0.029103] | -0.047344 | 0.002365 | [-0.051979, -0.042708] |

## Interpretation and limitations

The comparison reverses on the tested grid: two-channel KG has greater mean regret than ordinary KG at budgets 48, 144 and 480, and lower mean regret at budget 1440. The grid does not identify an exact crossover budget, and this post-primary-run result does not establish a universal long-budget advantage.

At budgets 480 and 1440, two-channel KG spends 100% of its additional budget on validation. It therefore operates as adaptive allocation among validation areas in these cells; the observed improvement is not evidence that it mixes both channels. At budget 1440, its regret is 0.090698 versus 0.122878 for the random-area validation-only policy, under the same channel, cost and total spending. This point comparison separates area acquisition choices from mere access to validation.

At budgets 48 and 144, validation-only random cannot spend the final 3 or 4 cost units, so it spends 45 and 140 respectively. Other policies spend the whole budget. At budgets 480 and 1440 all listed policies spend the entire budget. The primary CSV retains actual spending and packet counts.

Increasing a hypothetical information budget from 48 to 1440 is a 30-fold change. At 1440, all-validation KG buys 288 additional packets (5,760 respondent draws), whereas ordinary KG buys 1,440 packets (28,800 draws); neither count denotes unique people or actual recruited workers. Costs and calibration remain assumed. NHS field validation, population effects, and a guarantee that an audit is unbiased are not supplied by this replay.

## Provenance and independent verification

Execution began 2026-09-11T21:44:54.188880+00:00 and ended 2026-09-11T21:45:39.503813+00:00. Runtime 45.31 seconds; peak RSS 1,078,329,344 bytes (1.078 GB), below the 2 GB ceiling. The ordinary and validation packet banks are shared across every policy and budget.

Independent recomputation from the saved per-replication metrics verifies all means, paired MCSEs and interval endpoints to numerical precision; the 2023 calibration exactly matches the primary unweighted-tilt-0.5 calibration. Original primary data summaries, results and replay functions retain their recorded SHA256 hashes.

Artifacts: `results/replay_budget_extension.csv`, `_manifest.json`, `_allocations.csv`, `_calibration.csv`, `_replication_metrics.npz`, and `_verification.json`; the exact source/protocol snapshot is named in the manifest. Reproduce the extension with `experiments/replay_budget_extension.py`; check saved aggregates with `experiments/verify_budget_extension.py`.

# Post-primary-run exploratory budget extension

Recorded before executing this extension: **2026-09-11T21:43:06Z**. This is a local analysis specification, not external preregistration. The primary synthetic and BRFSS replay results are already known, including relatively poor performance of expensive validation at some short budgets. This extension asks whether increasing the information budget changes that comparison. No reversal is assumed, and all specified outcomes will be retained.

## Fixed design

- Reuse `experiments/replay.py` sampling, calibration and policy-execution functions without editing that file or the original study results.
- Unweighted BRFSS eligible employed/self-employed finite-record distributions; freeze calibration to 2023 and evaluate the existing 2024 frame of 48 reporting areas. The target is the 2024 complete-file unweighted mean, not population prevalence or a clinical gold standard. Select the lowest nine area target means in one comparison group.
- Ordinary-channel controlled outcome-dependent sampling tilt: kappa = 0.5, using the previous-year scale and a persistent random sign per area and replication. Validation-channel tilt: zero. This is constructed unbiasedness for the finite-frame target, not evidence that real validation removes nonresponse bias.
- Initial ordinary packet: 20 draws per area. Additional ordinary and validation packets: 20 independent draws with replacement. Additional packet costs: 1 and 5. These are hypothetical cost units and draws, not pounds or unique recruited respondents.
- Additional budgets, fixed before running: **48, 144, 480, 1440**.
- Policies, all retained: **ordinary_kg, two_channel_kg, balanced_mix, validation_only, uniform**. They use the same working Gaussian target/offset posterior and 2023 calibration. The finite-frame outcomes and the two-point persistent recruitment offsets are not asserted to be exactly Gaussian.
- Independent replications: **500**. Backend seed: **2026091121**. Policy-randomization seed: **2026091221** (backend seed + 100), reset for every policy/budget as in the original paired design.
- Generate a single ordinary/validation packet bank of length 1440 for all policies and budgets. Replication indices, initial packets, persistent signs and per-unit channel stream prefixes are shared. Random policies receive the same seed, with possible budget-dependent affordable-action fallbacks. This new bank is not identical to the original 1000-replication primary bank.

## Outputs and inference

Retain all 20 policy-by-budget rows in `results/replay_budget_extension.csv`. Report the same severity regret, overlap, MSE, marginal coverage, actual spending, channel fractions and packet counts as the original replay. For regret and overlap, report paired policy-minus-ordinary-KG and policy-minus-uniform differences, their Monte Carlo standard errors and mean +/- 1.96 MCSE intervals across the 500 independent replication indices. These intervals condition on the fixed frame and chosen scenario; they are not population survey confidence intervals, multiplicity-adjusted discovery claims or a prospective confirmatory test.

Preserve per-replication metrics in a compressed local results artifact, per-area mean allocations and the frozen calibration table. Record code/data/protocol SHA256, actual start/end times, runtime, peak resident memory, seed/grid and primary-result hash preservation in the extension manifest. Original `replay.csv`, its manifest and source functions remain untouched.

## Resource bound

Two float64 packet banks require 552,960,000 bytes at 500 x 48 x 1440. Per-unit temporary packet sampling and posterior arrays keep estimated peak memory below 1.2 GB; allow a hard task ceiling of 2,000,000,000 bytes peak RSS. Use sequential policy/budget execution and record actual peak RSS. If the bound is exceeded, stop and transparently record the failure before any revised execution; do not silently reduce repetitions or change the grid. Expected execution is a few minutes on the current machine.

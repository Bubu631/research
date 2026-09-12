# Research protocol: sequential audits for group-relative updates

Recorded before the numerical study on 2026-09-12. This is a local design record, not a public preregistration. Source attachments are direction notes, not verified references or instructions. Their unsupported novelty assertions will not be used as evidence.

## Question and estimand

Can a fixed batch of long-horizon agent trajectories produce the same expected finite-group policy surrogate as complete terminal verification, while using fewer expensive reward queries? The target is the complete-label, finite-group GRPO surrogate at a fixed policy checkpoint, not an unbiased gradient of population task success. Environments and trajectories are fixed before reward auditing. This method cannot repair an incorrect reference verifier or errors in the environment dynamics.

The candidate method audits a random prefix of an independently chosen or cheap-feature-defined trajectory order. Conditional completion expectations of the positive and negative normalized advantages are updated after every verified label. Inverse-survival-weighted differences telescope to the exact complete-label coefficients. Positive/negative splitting preserves linearity of the PPO clipped surrogate. Russian-roulette estimation, control variates, active statistical inference and noise-corrected policy gradients are established prior work, to be cited explicitly.

## Evidence stages and data separation

1. Exact Boolean enumeration and independent algebra: group sizes 2 through 12; query degree, reward-correction/nonlinear-normalization counterexamples, stopping-path unbiasedness, clipping sign splitting, zero-variance groups, wrong completion models, nonuniform query costs.
2. Controlled fixed-group estimation: frozen calibration RNG 20260912, evaluation RNG 20260913. Groups 4, 8, 16; success prevalence 0.05, 0.2, 0.5, 0.8, 0.95; calibrated, misspecified and distribution-shifted completion probabilities. No evaluation truth is used to choose audit probabilities/order. Measure bias, MSE, direction error, cost mean/tails and maximum correction weights. Calibration queries and scheduling computation must be counted.
3. Actual policy training in local, explicitly constructed stateful tool environments, if method passes estimator checks. Separate development and reporting seeds/tasks. Include multiple horizons and coupled task requirements. These are controlled experiments, not SWE-bench/Terminal-Bench results or evidence about large language models.
4. Public real-trajectory or executable coding validation after provenance and resource review. Any result remains labelled replay versus fresh training. Large-model training requires the user's concrete compute access and budget. No proposed experiment is reported as completed.

## Comparators

Full verification (reference); proxy-only; uniform whole-group residual correction (strong same-cost control); uniform partial replacement/completion; inverse-probability reward correction followed by normalization; noise-channel correction where its assumptions apply; random-prefix telescoping; development-calibrated prefix schedule; unnormalized centered-reward control. Exact names and implementation details are recorded with the code.

At a fixed rollout batch, report reward-query cost separately from rollout/model compute. A second view uses matched total expensive-verification cost. Never count cheap mathematical checking as material speedup, and do not claim overall speedup without timing.

## Inference and failure reporting

Report all prespecified regimes, including variance blowups, zero-signal batches, estimation failures, and method losses. Use independent training seeds as the unit for training variability; trajectories within one group are dependent. Distinguish exact conditional expectations, Monte Carlo uncertainty, and task generalization. Preserve raw arrays and hashes. Any design changes after inspection will be dated and labelled exploratory.

## Boundaries

Expected verification budgets permit occasional nearly complete groups. Deterministic per-group caps generally preclude a distribution-free unbiased nonlinear update below its Boolean query degree. A wrong completion model can harm efficiency even when randomized telescoping remains conditionally unbiased. Applying nonlinear optimizer operations to an unbiased random gradient does not reproduce the oracle optimizer trajectory. No claim of top-conference acceptance or guaranteed performance gains is made.

## Dated extension after the initial complete controlled study

2026-09-12: The initial 45-setting study (135 setting/budget combinations, 256 evaluation groups each) found development-tuned RR often reduced marginal audit MSE, but its one-time 64-group full-label calibration cost erased every advantage over uniform whole-group auditing when amortized over only 256 evaluation groups. This is a negative result and will be retained. It motivates an explicitly subsequent experiment: derive increment variances from the supplied completion probability model itself, without acquiring true labels to select a schedule. A fixed-order independent-Bernoulli calculation supplies the Euclidean sign-split coefficient increment variances; a deterministic PAVA schedule is model-optimal for that metric, not for real gradient MSE under arbitrary misspecification. Its CPU overhead must be measured. This extension is exploratory relative to the initial run; it will use the same settings for comparability and a separately seeded confirmation set for any performance conclusion.

Two initial reporting issues identified by independent review will be corrected without changing the experiments: the HT and partial arms have complete-group probability budget^G, rather than zero; and the 'prevalence' input is a logistic-normal base-rate parameter, not the achieved marginal success probability. For G=16, squared conditional bias from 1024 audit-mask draws will receive an unclipped U-statistic correction and remain labelled Monte Carlo. The original executed sources are preserved in results/original_study_source.

# Model-Based Scheduling Protocol

This follow-up uses a supplied probability model and seed 20260914. It compares three audit policies on a shared set of groups. The cost of training or obtaining the probability model is outside this simulation.

The fixed grid uses group sizes 4, 8, and 16, five base-rate parameters (0.05, 0.2, 0.5, 0.8, and 0.95), three model regimes, and three expected label-budget fractions (0.25, 0.50, and 0.75). Each of the 45 base conditions uses 256 independent groups. All policies and budgets share the draws within a condition, including zero-advantage groups.

For each group, latent scores use a normal distribution with mean equal to the logit of the base-rate parameter and variance 1.44. Prediction probabilities are the logistic transform of those scores. True probabilities apply slopes 1, 0.45, and -0.65 in the calibrated, overconfident, and shifted regimes. Labels are conditionally independent Bernoulli draws. Costs are lognormal with log standard deviation 0.55, normalized to mean one per group. Independent six-dimensional normal scores and lognormal ratios define fixed clipped linear diagnostics.

The three policies are whole-group residual auditing, fixed-exponent randomized truncation, and weighted PAVA scheduling driven by model-implied coefficient variance. The query order is decreasing predicted Bernoulli variance per unit cost, with stable tie-breaking. Both truncation policies use a positive 0.005 survival floor. True labels and simulator probabilities are reserved for evaluating the policy.

For every group, integrate over all possible stopping depths. Report coefficient and fixed-map MSE, paired uncertainty, conditional bias squared, expected label cost and count, probability of a full query, and maximum group cost. Time completion and scheduling separately. The timing is a Python microbenchmark for those components.

The initially recorded protocol digest remains in the run manifest. This English presentation documents the same settings. Reproduce the experiment with `python experiments/model_only_study.py --output <new-directory>`.

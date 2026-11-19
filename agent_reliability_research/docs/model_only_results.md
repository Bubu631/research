# Model-Based Scheduling Results

The experiment used 11,520 independent groups across 45 base conditions, paired across three budgets and three methods. It recorded 103,680 method/group/budget rows. The estimator exactly integrates the stopping distribution for each simulated group.

| Baseline | Probability regime | Median coefficient MSE ratio | Model-based wins |
| --- | --- | ---: | ---: |
| Whole-group audit | Calibrated | 0.747918 | 45/45 |
| Whole-group audit | Overconfident | 1.021451 | 18/45 |
| Whole-group audit | Shifted | 2.242589 | 0/45 |
| Fixed-exponent truncation | Calibrated | 0.879394 | 43/45 |
| Fixed-exponent truncation | Overconfident | 0.902679 | 37/45 |
| Fixed-exponent truncation | Shifted | 0.955070 | 29/45 |

Ratios are medians across settings after averaging each over 256 groups. The model-based policy depends on the quality of its supplied probabilities. Reverse calibration increases variance. The earlier paid-calibration experiment remains in the estimation results.

See [the protocol](model_only_protocol.md), [paired results](../results/model_only/paired_comparisons.csv), and [numerical validation](../results/model_only/independent_validation.json).

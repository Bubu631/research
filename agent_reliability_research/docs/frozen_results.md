# Frozen historical score audit: completed results

All 49 heldout tasks / 392 records, all-equal groups included. This is historical empirical replay at a frozen Qwen checkpoint in a specified 32-dimensional added-logit-bias parameterization. It is not on-policy training, full-parameter differentiation or fresh software testing.

| Method | MSE / whole at q=.5 | Squared conditional gradient bias | Expected labels |
|---|---:|---:|---:|
| Complete labels | 0.00000 | 0 | 8 |
| Reward HT then normalize | 1.93748 | 1.97768e-05 | 4 |
| Partial replacement | 1.96523 | 7.63844e-05 | 4 |
| Proxy completion | 1.00000 | 0.000174543 | 0 |
| Fixed sequential | 1.35169 | 2.02612e-36 | 4 |
| Model coefficient schedule | 0.75907 | 1.50349e-36 | 4 |
| Model gradient schedule | 0.86147 | 3.04518e-36 | 4 |
| Whole-group residual | 1.00000 | 1.3135e-36 | 4 |

Coefficient-model schedule pointwise ratio intervals across q=.25/.5/.75: [0.684,0.992], [0.547,0.996], [0.348,1.119]. They are paired percentile intervals from 10,000 task bootstrap resamples, not simultaneous or on-policy inference. Biased estimators can win MSE at small budgets. All eight methods and three fractions are retained in the CSV.

Extraction: 57,948 scored target tokens, 763.195 recorded forward/score seconds, 778.819 total invocation seconds, 274 context-truncated records, 14 target-prefix truncations. Cached labels do not identify real execution latency. Model-moment schedule timing excludes full online completion and is not a total training-CPU measure.

# Allocation implementation: independent mathematical audit

Reviewed on 2026-09-11. Scope: `experiments/allocation.py` and `experiments/common.py`; not an audit of the complete synthetic or BRFSS data pipeline. The study programs were not modified or re-run for this audit.

The checked implementation matches the independent-unit, fixed-hyperparameter Gaussian model and the loss averaged across **all selected units**. `common.performance` divides total selected-minus-oracle severity by the sum of the within-group quotas, K. Therefore omitting the common 1/K factor in `choose_actions` does not change the cost-normalized KG maximizer. This would not be the correct policy normalization for an alternative objective that averages group-specific mean regrets with equal weight, unless the group quotas were equal.

`thresholds` correctly uses the outside replacement mean for an already selected unit and the last selected mean for an unselected unit. Stable index ties agree with `selected`; the optimum-sum KG remains well-defined at ties. A group containing one unit selects it under the current minimum-one-slot rule; its acquisition value is correctly zero. General quotas of zero are discussed by the theory but are not exposed by the current `fraction` implementation, which deliberately selects at least one per group. The tested study settings use this same convention.

Both ordinary and validation updates match general bivariate Gaussian conditioning. The innovation standard deviation uses the target--measurement covariance, rather than the remaining target standard deviation. The ordinary posterior uncertainty floor has a zero-denominator branch consistent with already knowing the ordinary linear combination. The implementation assumes per-unit independence even in deliberately misspecified shared-bias stress worlds; such stress performance must be described as model misspecification, not a correctly specified correlated-KG evaluation.

Cost-normalized KG is the stated heuristic. Its lack of global finite-budget optimality is already disclosed. The `two_channel_kg_terminal` option compares total KG when at most one minimum-cost action fits; the option does not supply a general multistep guarantee. No result from a fixed-confidence best-arm method can be inherited by the ordinary boundary heuristic.

## Executed independent checks

`experiments/verify_allocation.py` tests the implementation against independently written sorting and linear-conditioning references. `results/allocation_verification.json` records the exact hashes of the tested sources.

- 80 panels with unequal group sizes 1, 4, 8, 12 and quotas 1, 1, 2, 3, including deliberate posterior-mean ties: all thresholds agree with sorting the other units directly.
- Mean severity regret agrees with direct selected sums minus independently sorted group oracle sums, divided by K=7; maximum discrepancy 4.44e-16.
- 120 random positive-definite covariance matrices and both observation loadings: mean/covariance update discrepancies at most 8.88e-16; innovation standard-deviation discrepancy at most 4.44e-16.
- Maximizing KG/cost and KG/(K cost) returns identical actions, and fully selected groups have zero KG.

These are identity and implementation checks, not evidence of real-world calibration or optimality of the acquisition policy.

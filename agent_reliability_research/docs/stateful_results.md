# Constructed stateful training: complete result record

Executed 2026-09-12 with the frozen protocol: 6 methods × 3 horizons × 10 seeds × 300 updates, group size 8. All 180 runs completed. This is actual NumPy softmax policy optimization over deterministic stateful tools, with a scripted initial policy; it is not an LLM or public software benchmark.

Complete wall time: 259.068 seconds. Training generated 432,000 trajectories and executed 12,096,000 tool actions.

## Same-rollout endpoints

All rows use 2,400 training trajectories per run. Success is stochastic reference-verifier success on independent reporting episodes, averaged over 10 training seeds. SE is across seeds. Purchased queries are the per-run average; certified cheap negatives are free under all methods.

| H | Method | Reference success ± seed SE | Cheap success | Purchased queries |
|---:|---|---:|---:|---:|
| 12 | full | 94.06% ± 0.61 pp | 97.93% | 2202.0 |
| 12 | naive_reward_ht | 86.84% ± 0.47 pp | 95.20% | 1055.3 |
| 12 | partial_replacement | 91.13% ± 0.58 pp | 97.89% | 1106.5 |
| 12 | proxy | 17.42% ± 3.58 pp | 98.40% | 0.0 |
| 12 | rr_completion | 93.55% ± 0.63 pp | 97.62% | 1076.0 |
| 12 | whole_group_residual | 93.48% ± 0.71 pp | 97.62% | 1072.4 |
| 24 | full | 83.44% ± 1.03 pp | 94.10% | 2113.5 |
| 24 | naive_reward_ht | 68.91% ± 1.07 pp | 88.52% | 988.0 |
| 24 | partial_replacement | 75.08% ± 0.68 pp | 93.87% | 1047.1 |
| 24 | proxy | 19.84% ± 2.92 pp | 95.04% | 0.0 |
| 24 | rr_completion | 83.05% ± 0.88 pp | 94.14% | 1058.2 |
| 24 | whole_group_residual | 83.24% ± 1.05 pp | 94.53% | 1062.2 |
| 48 | full | 57.97% ± 0.96 pp | 89.10% | 1935.3 |
| 48 | naive_reward_ht | 32.23% ± 1.24 pp | 80.04% | 930.0 |
| 48 | partial_replacement | 29.96% ± 1.76 pp | 88.48% | 1001.9 |
| 48 | proxy | 3.59% ± 0.95 pp | 92.38% | 0.0 |
| 48 | rr_completion | 56.60% ± 1.72 pp | 86.76% | 956.6 |
| 48 | whole_group_residual | 55.27% ± 1.16 pp | 87.73% | 948.6 |

## Paired comparisons and limits

| H | RR minus baseline | Difference, pp | Pointwise 95% t interval, pp |
|---:|---|---:|---:|
| 12 | full | -0.508 | [-1.467, +0.452] |
| 12 | whole_group_residual | +0.078 | [-0.578, +0.734] |
| 24 | full | -0.391 | [-1.203, +0.421] |
| 24 | whole_group_residual | -0.195 | [-1.110, +0.720] |
| 48 | full | -1.367 | [-4.713, +1.979] |
| 48 | whole_group_residual | +1.328 | [-0.297, +2.953] |

RR and whole-group residual have close mean performance; all three pointwise RR-minus-whole-group intervals include zero. This study does not establish a distinct benefit from the fixed sequential schedule. RR also has slightly lower mean success than full-label training at every horizon; intervals overlapping zero are not proof of equivalence or non-regression.

Proxy optimization reaches high cheap-check scores while reference success can remain low or deteriorate. This demonstrates the specified omitted-invariant mechanism in the constructed environment, not general evidence about deceptive intent or all real-world verifiers.

The model-only analytical diagnostic, computed after smoke without outcome labels, gives Q_j=.5 for every candidate count M=1,...,8. Under this homogeneous p=.55 completion model and Euclidean coefficient metric, the monotone variance-optimal schedule is exactly whole-group residual correction. This is a meaningful degeneration boundary, not a reason to alter the frozen primary run.

## Real time and query accounting

| Method | Training seconds, summed over 30 runs | Estimation seconds | Purchased labels |
|---|---:|---:|---:|
| full | 19.790 | 0.404 | 62,508 |
| naive_reward_ht | 20.646 | 0.382 | 29,733 |
| partial_replacement | 19.696 | 0.355 | 31,555 |
| proxy | 19.518 | 0.262 | 0 |
| rr_completion | 29.082 | 9.248 | 30,908 |
| whole_group_residual | 21.348 | 1.870 | 30,832 |

The reference checker is extremely cheap here. RR has higher measured local training time than full verification and whole-group residual; reduced query count is not an end-to-end speedup. No synthetic sleep or artificial latency was added. These are diagnostic wall times on a shared host with a fixed method order, not an isolated randomized systems benchmark.

Purchased training checks: 185,536. Separately counted reporting checks: 599,040. Post-training offline diagnostic checks: 432,000. The latter labels were generated only after each complete optimization run and did not enter its updates.

The secondary `query_ceiling_view.csv` selects actual recorded checkpoints below a common descriptive ceiling and reports actual query/rollout counts. It is not an exactly matched-budget experiment; sparse checkpoints leave unequal unspent budget, and methods that buy fewer labels may execute more training trajectories. It must not be used to claim equal total compute.

## Independent checks and artifacts

All 5 numerical CSV hashes and all four executed-source snapshots match the run manifest. All 180 trajectory banks have finite coefficients/weights; query masks match purchased labels and independent post-run replay truth; no cheap-negative label is bought. Task streams and initial reporting outcomes match across paired methods. Maximum observed gradient norm 0.641970; clipped updates 0/54000.

Before full training, held-action score finite differences agreed to 1.40e-11, and exact integration over every RR stopping cutoff on generated releases agreed with the complete sign-split target to 4.44e-16. These checks do not claim independent re-execution of all 180 training runs.

Primary outputs: `results/stateful_training/{training,evaluation,summary,paired_endpoint,query_ceiling_view}.csv`, `manifest.json`, all action/policy/label banks under `trajectories/`, and the exact executed source under `executed_source/`. Machine-readable summary and ledger audit: `results/stateful_result_summary.json`.

The initial greedy policy already follows the known repair workflow. Reported improvement concerns stochastic execution reliability in this task family. Reporting draws are independent episodes, not unseen repositories or newly held-out task structures. Horizon and dependency-chain size co-vary, so their separate effects are not identified.

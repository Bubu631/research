# Native-gradient independent audit

Completed on 2026-09-11 after the 36.87-minute English–German native-gradient run. This is an independent calculation from saved results and a code/protocol review; it is not a second transformer execution.

The verifier `experiments/verify_native_geometry.py` imports neither the experiment nor its report implementation. It reconstructs an eight-vector Euclidean embedding from the released Gram matrix and directly evaluates gradient norms, relative biases, and directional derivatives in that embedding. This preserves exactly the geometric quantities accessible from the original mean vectors, up to floating-point roundoff. It also checks original artifact hashes, executed script/helper/protocol snapshots, the 256 reporting IDs against the previous public study, per-record loss reconstruction, and the previous independent forward baseline.

All checks passed. Gram reconstruction error is 4.44e-15. Maximum discrepancies are 7.22e-15 for the selected-mean relative ratio, 6.92e-15 for the target-mean ratio, 5.00e-15 for absolute bias, and 4.78e-15 for the squared-ratio derivative. Full NLL differs from the earlier unpadded forward implementation by at most 1.7294e-6, and edited plus untouched losses reconstruct full loss to 2.9803e-7. These last two errors are expected implementation differences between batched float32 cross entropy and the earlier CPU float64 probability calculation; they are reported rather than described as byte-identical.

| Selection | Relative bias, hard/full | Absolute bias, hard/full | Absolute-bias minimizing retention |
|---|---:|---:|---:|
| Edit fraction | 0.447477 / 0.331020 | 0.493396 / 0.656018 | 0.0793594 |
| Source length | 0.192671 / 0.104971 | 0.126841 / 0.201443 | 0.0438574 |
| Mixture | 0.224553 / 0.142858 | 0.183301 / 0.273325 | 0.0622149 |

The relative derivative is strictly negative over the whole interval for all three settings, verified by the maximum of its quadratic sign polynomial. Absolute bias instead initially decreases to a shallow interior minimum and then increases. The endpoint claims must therefore say that hard localization has lower absolute bias **than full retention**, not that absolute bias decreases monotonically with stronger localization.

The untouched biases are nonzero and selected component inner products are negative in all three settings. Consequently the simple unbiased-untouched/aligned-mean corollary cannot explain these curves. The general derivative theorem remains applicable. This reinforces the final title's explicit qualification of **relative** selection bias.

The mixed propensity is the arithmetic average of the two other propensities. Its normalized selected distribution uses edit weight 0.3881442. The three settings reuse the same records and are not independent replications; the ideal eight-vector Gram matrix has rank at most six. The computed matrix has two small positive eigenvalues (1.41e-9 and 2.17e-9) and relative mixture-relation norm residuals 7.05e-5 and 2.68e-5. These are useful consistency diagnostics, not bounds on total numerical gradient error or certificates of numerical exactness. No floating-point uncertainty bound is inferred from comparing those residuals with the observed endpoint gaps.

The full computation covers 73,886,208 native differentiable parameters, counts tied weights once, excludes the two fixed sinusoidal position tables, and does not include the hypothetical output-bias adapter. Thus the output-bias and native experiments use different parameterizations, not literal subset/superset blocks. The study reuses an already examined reporting population, performs no native update, and establishes neither an independent generalization result nor authentic complaint-propensity identification.

Machine-readable details are in `papers/edit_localization/results/full_parameter/independent_validation.json`. The original native output hashes all match their completion manifest; this audit adds its own new file rather than changing those original outputs.

# Independent acquisition-implementation audit

The final check invocation on 11 September 2026 at 21:44:26 UTC passed. The reproducible verifier is `experiments/verify_implementation.py`, SHA-256 `5875c8dc2500b3ad3bf168c024a98dfa974d09957cc79cc486967255ac7dd711`. It prints its full machine-readable audit to standard output and does not modify experiment code, data or scientific results. All protected source/input/result hashes stayed unchanged.

No substantive update, budget-accounting or held-out-information bug was found in the executed implementation. The checks do not establish global budget optimality, an unbiased real recruitment channel, clinical validity or posterior coverage under model misspecification.

## Independent calculations

The verifier uses full 2×2 covariance matrices and generic Gaussian conditioning, rather than the main implementation's five scalar state arrays. Ordinary measurements have loading `[1,1]`; validation measurements have loading `[1,0]`. It checks both target and offset means, both variances and the cross-covariance after 700 mixed sequential updates. The maximum state discrepancy was **8.88×10⁻¹⁶**, and covariance matrices remained positive semidefinite within floating-point tolerance.

The one-coordinate top-k value was independently integrated over a standard normal innovation in 80 random cases. Each case sorts the full changed vector inside the integral; it does not substitute the implementation's cutoff formula. The maximum discrepancy was **1.01×10⁻¹⁵**. This value is the improvement in the **sum** of selected posterior means. The reported severity regret divides by the fixed total selected count; that common factor does not alter the acquisition argmax. Independent-unit posterior structure is required for a single coordinate to change. Correlated shared-offset scenarios are therefore misspecification checks, not a proof that the independent-coordinate formula remains exact for a correlated posterior.

All ten declared policies were checked on small paired streams: 20 synthetic policy/budget cases with five replications each, and ten BRFSS replay policy cases with four replications each. Every action trace and posterior field matched the independent calculation. These cases include ordinary-only, bias-blind, uncertainty, boundary, equal-action two-channel random, cost-balanced random, validation-only and two-channel KG policies. The boundary rule is the implemented fixed-budget heuristic; no LUCB fixed-confidence theorem is transferred to it.

Every sampled action is checked for affordability before its observation is assimilated. Realised cost equals `ordinary_packets + audit_cost*validation_packets` and never exceeds the declared extra-acquisition budget. Each accepted packet adds 20 draws to its channel count; the common initial 20 ordinary draws per unit are counted in `ordinary_n` but excluded from the additional budget. Validation-only policies may leave a remainder smaller than the validation cost; that is permitted unused budget, not an overspend. Within each unit/channel, a counter takes the next unused packet from the shared array.

## Sampling and temporal information flow

The verifier independently reconstructs 2023 and 2024 histograms from the cleaned CSVs, and independently recomputes all **240 saved 2023 calibration rows**. It checks common prior mean, between-area SD, two-sign bias centre/SD, ordinary packet variance and validation packet variance. It also reconstructs the weighted finite-file histogram. The reference calibration uses stable moment expressions different from the main implementation's subtraction of raw second moments.

The histogram backend was compared with explicit uniform sampling from a tiny ordered record list, including a zero-frequency outcome bin: all **77 packets of 20 draws** agree exactly. Histogram compression is equivalent to record sampling for this single recorded outcome and declared sampling probabilities. It would not preserve unrepresented individual covariates or arbitrary joint outcomes. All replay draws are **with replacement**; these are respondent-record draws, not new unique people recruited into a real survey.

A metamorphic test replaces the complete 2024 mean metadata with `10 - original_mean`, multiplies its variance metadata by 999 and its frame-size metadata by seven, while keeping the outcome-frequency backend and 2023 calibration fixed. Across all ten policies:

- The initial, ordinary and validation packet arrays remain identical.
- Every acquisition choice, final target mean and posterior variance remains identical.
- The evaluation target changes and every policy's MSE changes.

This deliberately inconsistent oracle-metadata perturbation is a software information-flow check, not a fabricated alternative dataset. It establishes that these hidden 2024 summaries do not enter policy state. The ordinary and validation streams themselves necessarily depend on recorded 2024 outcomes because those are the replay environment. Only revealed initial/acquired packet means reach the update/action selector. The controlled recruitment-tilt generator can access hidden outcomes; the acquisition policy cannot access them. Prior parameters and tilt scales are constructed using 2023 only.

Within each synthetic bias setting or replay scenario, policies, costs and budgets use the same generated world and per-unit/per-channel packet streams. Counters restart for each policy. This supports paired differences conditional on that world. Different synthetic bias settings and different replay scenarios use distinct seeds and are not claimed to share identical draws. The saved contrast code subtracts policy metrics from comparator metrics replication by replication before computing its Monte Carlo standard error. It does not incorrectly treat policy evaluations on the same world as independent repetitions.

## Independent reproduction of saved rows

To avoid rerunning the entire suite, four complete saved rows were reconstructed at their actual repetition counts. Generic matrix updates, independently evaluated acquisition values and independently computed loss/coverage summaries reproduce the saved means, Monte Carlo standard errors and normal-approximation summary endpoints.

| Dataset / selected setting | Policy | Replications | Independently recomputed mean severity regret |
|---|---|---:|---:|
| Gaussian, bias SD 0.35, budget 40, validation cost 5 | Ordinary KG | 2,000 | 0.1751130620 |
| Same synthetic setting | Two-channel KG | 2,000 | 0.1761952461 |
| Unweighted BRFSS tilt 0.5, budget 48, validation cost 5 | Ordinary KG | 1,000 | 0.1804406975 |
| Same replay setting | Two-channel KG | 1,000 | 0.1941125753 |

These deliberately retained rows do not favour the two-channel method. They support neither universal improvement nor global budget optimality. The original stream-generation functions are used to reproduce the stored random streams for these full-size rows; the posterior, action-value and metric calculations are independent. The separate small-record and histogram checks establish the relevant generator mechanics.

There is one numerical qualification. In the full synthetic two-channel row, six of 2,000 paths encountered a mathematically tied or numerically indistinguishable boundary action. A different floating-point operation order in generic matrix conditioning can choose the other boundary unit. The largest independently recomputed value shortfall of the original chosen action was only **1.73×10⁻¹⁸**. The verifier therefore validates the original action's independently calculated greedy value at every step and follows the original execution branch for exact saved-row reproduction. It does not silently require a different numerical implementation to resolve every near-tie identically. Without following the recorded branch, the alternate independent implementation changes this row's regret mean by approximately 1.08×10⁻⁵; no main algorithm or saved result was altered to eliminate that harmless discrepancy. The other three checked rows had no such branch difference.

## Comparison and interpretation boundaries

**Separate acquisition strategy from available information.** `two_channel_kg`, `two_channel_uniform` and `balanced_mix` have the same two-channel action set, costs and bias-aware inference. These are the clearest allocation-strategy comparisons. Validation-only is a restricted-action diagnostic. Comparing two-channel KG with ordinary-only policies also changes the available information source, so any difference cannot be attributed solely to a superior allocator. `uniform_blind` and `bias_blind_kg` deliberately alter inference assumptions; they should not be presented as if only allocation changed.

**Cost-normalised KG is a myopic heuristic.** It selects the largest one-step expected gain per cost among affordable actions. The theory audit supplies a finite-budget counterexample. Repeating an ordinary channel can leave target-level uncertainty, but that fact alone does not establish positive ranking regret: common group shifts can cancel from fixed within-group selection. Those distinctions are implemented as explicit stress cases.

**Coverage has a specific experimental meaning.** The reported quantity is the fraction of units for which the supplied truth/reference lies within `posterior_mean ± 1.959963984540054*posterior_sd`, averaged over repeated worlds or sampling replications. It is not simultaneous coverage of every unit, coverage conditional on being selected, or a confidence guarantee after real workplace recruitment. Under the correctly specified synthetic Gaussian reference, posterior statements have their model-based interpretation. In BRFSS replay, targets are fixed empirical-file means, bias priors are moment-matched to a constructed two-sign recruitment law, and packet observations are discrete rather than exactly Gaussian; repeated-file coverage is an empirical diagnostic. It must not be described as a validated real-data posterior guarantee.

**Avoid an optional-stopping unbiasedness claim.** A prespecified-length iid uniform packet mean is unbiased for its finite-file outcome distribution. Weight-proportional iid draws similarly have the full weighted finite-distribution mean as their expectation; this does not use a ratio estimator from a uniformly sampled subset. Neither property implies that a final per-area mean after outcome-dependent allocation/stopping is unconditionally unbiased. The posterior estimator also intentionally shrinks. Uniform or weight-proportional access is an offline assumption, not evidence that a real validation campaign is free of nonresponse bias.

**Stress distributions must be named accurately.** The synthetic heavy-tail case adds a standardised Student-t₃ disturbance at the packet-mean level, scaled by `sigma/sqrt(packet)`. It is not explicitly the average of 20 independently sampled t₃ individuals; those distributions differ. The Gaussian case is distributionally equivalent to averaging Gaussian individuals. Shared-group offsets, target drift, heteroscedasticity and persistent validation bias are separately generated stresses. The BRFSS tilt is deliberately injected and partially known from a hypothetical 2023 calibration; it is not an estimated real survey or NHS recruitment bias.

**Count independent worlds correctly.** The main synthetic suite has 24 cost/budget/bias cells and seven stress cells, but the 24 main cells reuse four underlying bias-setting worlds. With 2,000 replications, there are 8,000 distinct main worlds and 14,000 stress worlds, reused across the ten policies. The replay reuses 1,000 sampling worlds within each of five scenarios, with the 2024 finite file fixed. Policy/cost/budget evaluations do not create new independent respondents or new independent latent worlds.

## Reproduction and scope

From this repository, run `python experiments/verify_implementation.py`. The command prints JSON containing the test counts, precise differences, numerical tie events and protected hashes. NumPy, pandas and SciPy are required. It creates no scientific result files and leaves the original prior NHS release untouched.

This implementation audit covers `allocation.py`, `synthetic.py`, `replay.py` and their shared selection/metric helpers. It does not independently validate the later NHS scenario demonstration, publication novelty, a stakeholder partnership, actual recruitment costs or a deployment process. Those require their own evidence and review.

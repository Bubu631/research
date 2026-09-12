# Reproducibility and evidence checklist

This is a research checklist, not an assertion that a conference submission has been made. The anonymous PDF follows the retrieved AAAI-27 submission style. Any future cycle's current rules must be checked at submission time.

| Item | Evidence / limitation |
|---|---|
| Research claim defined | Fixed-quota severity regret; measurement allocation under a given budget. No intervention-effect, globally optimal allocation or new-KG claim. |
| Model assumptions stated | Independent 2x2 Gaussian target/offset states, fixed hyperparameters, fresh packet noise and conditional validity of reference channel. Correlated-shift and invalid-validation failures described. |
| Complete proofs | Four propositions, proofs, current-posterior floor, shared-shift invariance, and a cost-greedy counterexample in the technical supplement. |
| Algorithms reproducible | All ten action rules, state updates, affordability, stable ties, stopping and paired streams documented in code and supplement. |
| Data access | Official public CDC URLs and preserved cleaned frames; source SHA-256, byte counts and retrieval times. NHS derived panel and its original source-cell provenance retained. |
| Sampling unit | Synthetic replication or conditional fixed-frame replay. Twenty with-replacement draws per packet, not newly recruited people. |
| Training/calibration separation | 2023 calibration; hidden 2024 targets used only for final evaluation. Artificial recruitment laws explicitly identified. |
| Hyperparameters | Primary protocol fixed before full runs; exact grids and seeds recorded. No tuning on hidden 2024 full-frame targets. |
| Exploratory work | Budget extension declared after primary outcomes, with separate dated protocol, new seed and all 20 policy-setting outcomes. |
| Baselines | Matched inference except labelled bias-blind policies. Same-action-set and restricted-channel comparisons distinguished. |
| Error bars | Across independent replications; differences are paired. No population or simultaneous-grid interval interpretation. |
| Compute | Local CPU, versions and measured timing/memory documented. No paid compute or private endpoints. |
| Results completeness | All 490 primary policy-setting rows and 20 exploratory rows; CSVs include MCSE, coverage, MSE, spending and relevant paired differences. |
| Independent verification | Separate numerical theory, full-matrix updates, source extraction, discrete sampling, budget and hidden-target checks; reports in docs/ and results/. |
| Negative findings | Small-budget, misspecified-bias, shared-shift, target-drift and invalid-validation failures retained. |
| Domain evidence | NHS guidance supports universal listening access; extra targeted follow-up is only proposed. Quarterly engagement is not relabelled as burnout. |
| Human evaluation | Not performed. No co-design, interviews, partnership, deployment or health improvement claimed. |
| Potential impact | Avoid wasteful measurement and improve scrutiny of review decisions; benefit is conditional and not yet prospectively established. |
| Confidentiality | Public records only; no names, addresses, employer identification, private linkage or attempted reidentification. |
| AI assistance | Disclosed in the full manuscript, technical supplement and README; named author must review and own all final claims. |
| Release and licence | Source data retain original terms; no blanket reassignment of third-party rights. Public upload and conference submission have not occurred as part of this upgrade. |

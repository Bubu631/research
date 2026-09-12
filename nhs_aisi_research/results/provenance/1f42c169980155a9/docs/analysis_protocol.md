# AISI research extension: local analysis protocol

Recorded: 2026-09-11T21:23:52.449166+00:00. This local specification is written before executing the extension's comparisons; it is not external preregistration. The original NHS study and its conclusions are already known. Data-acquisition agents may inspect source distributions for integrity. Amendments will be appended with reasons.

## Scope and decision

Study allocation of a fixed information-gathering budget before selecting low-scoring units for additional wellbeing review. Proposed users are workforce/wellbeing analysts; no collaboration, field deployment, intervention assignment or benefit is asserted. Information acquisition is distinct from intervention spending. The manuscript will follow the AISI emphasis on problem formulation, credible application pathways and transferable empirical insight, without treating AISI relevance as acceptance.

The decision compares repeating an existing measurement channel with obtaining a second, independently sampled measurement channel. The latter has assumed measurement properties and a higher cost. An actual independent assessment need not be unbiased; misspecification will be tested. Gaussian knowledge-gradient is existing prior art, not a newly invented algorithm.

## Reference model and decision rule

For unit i, target theta_i and persistent channel offset b_i have a bivariate Gaussian posterior. Ordinary measurement observes theta_i+b_i+noise; validation observes theta_i+noise in the reference model. The second channel's lack of shared bias is an explicit assumption. Acquisition reduces only uncertainty it can identify. The terminal loss is selected mean severity regret with fixed numbers of review slots within benchmark groups, using lower-is-worse scores. One-step expected improvement in the terminal posterior-mean decision is calculated exactly for each available unit/channel and divided by channel cost. This is a transparent application/specialisation of knowledge-gradient. No global finite-budget optimality is claimed.

Theoretical checks will cover the top-k one-coordinate Gaussian improvement identity, the posterior uncertainty floor after infinitely many ordinary measurements, the benefit of observing a different channel under known covariance, and failure cases under mis-specified bias/noise or greedy allocation. Any additional formal guarantees must be derived and independently checked before being claimed.

## Synthetic comparisons

Synthetic data provide known latent targets. Base setting: 40 units in four equal-size benchmark groups, bottom 20% of each group selected; theta mean 5 and SD 0.35; Gaussian individual measurement noise SD 2.5; initial 20 ordinary observations per unit; acquisition packets of 20 observations. Channel costs are 1 for an ordinary packet and 5 for a validation packet, varied in sensitivity. Budget is in ordinary-packet cost equivalents, not pounds and not estimated NHS costs. All data streams and target draws are paired across policies via deterministic streams.

Compare ordinary uniform sampling; ordinary uncertainty sampling; an ordinary boundary/LUCB-inspired rule; ordinary-channel knowledge-gradient ignoring persistent bias; ordinary-channel bias-aware knowledge-gradient; two-channel uniform allocation; and bias-aware, cost-normalised two-channel knowledge-gradient. Where a standard algorithm is adapted, document its changes and do not transfer an inapplicable theorem. Include validation-only sampling as an additional diagnostic.

Primary factors: persistent-bias SD in {0,0.15,0.35,0.7}, budget in {40,120}, and validation cost in {2,5,10}. Run paired independent Monte Carlo repetitions, increasing their count if needed for stable summaries without selecting a policy based on results. Keep negative results. Additional misspecification tests: assumed bias too low/high, biased validation, heavy-tailed errors, common or heterogeneous target drift, and heterogeneous response variance. Report true severity regret, bottom-set overlap, total information cost, fraction spent on validation, and uncertainty calibration. Standard errors concern independent panels; policies on the same panels are paired.

## Public individual-record replay

Acquire official CDC BRFSS 2023 and 2024 public microdata. Restrict to recorded employed/self-employed adults with valid mental-health-days responses; use common states plus DC and report exclusions. Construct a 0–10 higher-is-better score from (30-MENTHLTH)/3, with code 88 interpreted as zero days and refusal/unknown/missing excluded. This is not the NHS burnout composite.

Primary target is the complete-file unweighted mean among eligible recorded respondents within each reporting area, a finite-frame benchmark rather than a population prevalence or clinical gold standard. The original complex-survey weights, strata and PSU fields are retained. Any weighted sensitivity must state its estimand and sampling mechanism and must not treat a sample ratio as unbiased.

Reveal only an initial random sample and additional sampled records to each policy. Use separate paired sample streams per area/channel, and exclude hidden full-frame means from policy state. Uniform sampling from the finite file evaluates acquisition efficiency on real recorded outcomes. A second, explicitly synthetic recruitment-bias scenario changes ordinary-channel sampling probabilities according to observed outcomes while the validation channel samples uniformly; it does not estimate actual BRFSS or NHS nonresponse bias. Use 2023 for scale/prior construction and a frozen 2024 evaluation, plus year-specific sensitivity as feasible. Empirical policy choices must not be tuned on held-out 2024 full-frame outcomes.

## NHS application and evidence boundaries

Preserve the original 190-reporting-unit panel, its within-group review capacities, its vintage-aware prediction findings and its nominal-versus-effective-sample-size distinction. Use it to demonstrate model-conditional information-allocation scenarios, clearly separated from executed BRFSS replay and synthetic latent-truth experiments. No resurvey, validation channel, repeat respondent panel, intervention or monetary return is observed in NHS data. NHS quarterly engagement measures are not silently substituted for the burnout composite.

## Reporting and outputs

Write a self-contained AISI-oriented research manuscript, full supplementary methods/proofs and reproducible code/data manifests. Preserve the original release. Authorship remains Shengwei Zhang / University of Pennsylvania; submission copy must be anonymous. Compute and source timestamps remain actual. The 2027 AAAI/AISI deadline has passed; the resulting work is not represented as submitted or accepted. New policy promises and limitations must be supported by executed code, reviewed mathematics or cited sources. AI assistance and lack of stakeholder validation remain explicit.

## Before-main-run theoretical and domain amendment

2026-09-11T21:27:43.482608+00:00: Prior-art review identifies multi-information-source KG as a direct antecedent; the algorithm is framed accordingly. Add a shared-within-benchmark-group offset stress because a common shift cancels from fixed-within-group selection regret even when individual levels remain unidentified. Do not infer ranking loss directly from posterior level variance. Domain guidance also establishes universal staff response opportunity in relevant NHS quarterly rounds; proposed targeted acquisition concerns additional follow-up on top of universal access, not removing invitations or statutory participation opportunities. The simulated action cost buys a completed packet only within the controlled experiment, not a guaranteed number of real staff replies.

## Inference-versus-acquisition comparison clarification

Before the full run, all policies except explicitly named bias-blind baselines use the same assumed target/offset prior and update. Thus uniform, boundary, ordinary KG and two-channel KG are compared under matched inference; a separate uniform-blind baseline isolates inference misspecification. Add a cost-balanced random channel mixture: validation packet probability 1/(1+validation cost), so expected cost shares are equal before end-of-budget effects. The equal-action mixture is separately retained. Both comparisons prevent attributing a better prior to a better acquisition strategy.

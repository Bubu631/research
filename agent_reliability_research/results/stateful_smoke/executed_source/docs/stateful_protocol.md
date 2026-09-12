# Constructed stateful tool training: protocol before smoke

Recorded 2026-09-12 before the first rollout or training experiment. This is an internal design record, not a public preregistration. Full runs are pending review of this design and its bounded smoke. No large language model or public benchmark is used.

## Task and observation boundary

H=12/24/48 gives n=3/6/12 components in a directed dependency chain. The release initially has cached artifacts at version 0. A fixed task distribution changes the required version of exactly one component, uniformly within the first ceil(n/2) positions. This forces rebuilding downstream cached prefixes. Four rounds visit components in topological order: a preferred edit round, build round, attest round, publish round. Any of the five actions (noop/edit/build/attest/publish) remains legal on every visit. H is the actual number of executed state-changing or no-op tool actions, not padding inserted after completion.

An artifact stores the current built parent prefix plus the component's source version. Attestation and publication hold immutable fingerprints; they do not magically track later changes. Reference verification executes source, artifact-prefix, publication and attestation constraints for every component. The cheap verifier checks only each published artifact's local version. It omits dependency and attestation requirements.

The actor sees phase, local versions, inspectable equality metadata, position and remaining budget. It receives no reference label during action selection. Full-check callbacks are available only to the reward-audit estimator after trajectories end. Task requirements are public, as in normal repair tasks; hiding a terminal label is not the same as hiding the user's requirements.

The task is purpose-built and has a strong known workflow. It tests execution-state accumulation and terminal-signal use. It does not show general planning, language understanding, transfer to unseen software, or superhuman debugging. Both chain depth and H increase together, so these experiments do not isolate their separate causal effects.

## Shared policy and training parameters

NumPy linear softmax policy with 15 observable features and 5 actions. All methods initialize identically: probability .9 for the phase-appropriate action, .025 for each other action; remaining feature weights are zero. This explicit scripted initialization prevents nearly all-failure groups at longer horizons; it is not learned from reporting data. The greedy initial policy can already follow the known solution, so the study measures improvement in stochastic execution reliability, not discovery of a new repair algorithm.

Primary proposed grid: group size 8; H in {12,24,48}; 10 independent training seeds; 300 updates; one on-policy SGD update per group; learning rate .5; average action score within each trajectory; global gradient norm cap 1.0. No Adam, no PPO replay epochs, no learned critic. Sign-split coefficients are summed at ratio 1 for this on-policy update. Consequently these training runs do not empirically test off-policy PPO clipping, whose algebra is checked separately by the main study.

Evaluation: fixed independent reporting stream, 256 stochastic episodes per checkpoint, at update 0 and every 25 updates including the last. The same reporting random numbers are paired across methods and checkpoints for a seed. Inference uncertainty uses independent training seeds, not repeated checkpoints as independent observations. No reporting result selects an action, estimator schedule, stopping time, predictor, or hyperparameter.

Training/task stream uses SeedSequence([2026091207,seed,H,1001]); independent audit stream ends in 2001; reporting stream ends in 9001. Every method consumes the same numbers of uniforms per group. Methods diverge through their learned policy, so paired RNG is not a claim that they see identical later trajectories.

## Auditing and fair baselines

All methods exploit the valid implication cheap=0 => reference=0. Charging a full baseline to recheck certified failures would be unnecessarily weak. Of G=8 labels, M cheap-positive candidates remain. The complete-label surrogate still uses all eight labels; candidate indices remain in original order. All four partial methods have expected purchased labels .5*M (at most 4); actual costs are logged.

1. Full: buy all M candidate labels and compute the complete normalized vector.
2. Proxy: use cheap labels without purchases.
3. Whole-group residual: fixed completion vector + Bernoulli(.5)/.5 times the complete-group residual, purchasing all M candidates when selected.
4. RR completion: sequential online callback; a fixed nonincreasing survival schedule proportional to j^(-.5), clipped to [.005,1], scaled to sum .5*M; index order among candidates. No outcome-adaptive order.
5. Naive reward HT: independently buy candidates with probability .5, form queried_label/.5 (zero otherwise), then normalize this reward vector.
6. Partial replacement: independently buy candidates with probability .5, replace bought proxy labels, retain the rest, then normalize.

The fixed completion model assigns p=.55 to cheap positives and 0 to certified cheap negatives. There is no fitting/calibration data and no learned outcome-model claim. Its accuracy may change substantially across H and training. Correctness of the RR construction does not assume this model is correct; efficiency can fail.

Primary comparison holds rollout count/updates fixed and reports different true-query counts. A secondary descriptive view uses the RR final mean query count as a ceiling and selects actual observed checkpoints at or below it for each method/seed. It reports both actual residual budget and actual rollouts. This view is not exact equal-cost training, uses no interpolation, and is not a confirmatory paired-budget treatment effect. A genuinely budget-stopped training experiment would need a separate protocol.

## Ledgers, storage and timing

Save every action sequence, task changed-component index, proxy label, purchased label/mask, split coefficient and policy checkpoint in compressed NPZ. Replaying these deterministic tools reconstructs all final states. Save a readable example per run and all per-update/per-checkpoint tables.

After an entire run has ended, reconstruct all training final states and run reference checks to obtain offline diagnostic truth. These labels never enter training. Purchased training checks, reporting checks and offline diagnostic checks are separate ledger fields. Offline truth is needed to inspect unqueried trajectories honestly; it is not free operational supervision.

A reference query executes all 4*n constraints. Query and invariant-check counts are resource units, not a measured claim that these tiny Python checks are expensive. No artificial sleep is used. Report wall-clock rollout, estimation, optimization, reporting and diagnostic time; completion overhead can dominate locally. No overall speedup is asserted from query reduction.

## Smoke gate and reporting

Initial smoke is exactly 5 updates × 1 seed × 3 horizons × 6 methods; 64 reporting episodes at updates 0 and 5. Its purpose is correctness, runtime and signal-range diagnosis, not effect estimation or hyperparameter selection for declared primary results. Any later changes will be documented with their timing and motivation. No full run is launched by --smoke.

Report all methods/horizons/seeds including negative results, zero-signal groups, occasional large correction vectors and clipping. Keep the immutable initial smoke output if the implementation changes. Environment self-checks include correct release, missed dependency, missed attestation and missed edit. Purchased labels are independently checked against post-run replay truth.

Commands from the workspace above the project:

```
.venv/bin/python agent_reliability_research/experiments/stateful_training.py --smoke
# Proposed full run, not executed by the smoke:
.venv/bin/python agent_reliability_research/experiments/stateful_training.py --updates 300 --seeds 10 --eval-episodes 256
```

# Fresh coding-policy GPU study: protocol and launch inputs

Status: proposed, unexecuted, 2026-09-12. No machine has been rented, no account selected, and no price or future outcome is assumed. `configs/onpolicy_gpu_plan.json` fixes the scientific draft; resource caps and image/split hashes remain explicit required inputs. The accompanying planner validates this configuration and computes GPU-hour estimates from measured profiles. It does not implement or launch the future trainer.

## Scientific question and evidence needed

Does sequential completion (SC) improve the actual cost--quality frontier over whole-group residual correction (WG) when fresh language-model code trajectories receive incomplete but informative test feedback? A fixed-bank unbiasedness check is necessary implementation evidence, but the main endpoint is heldout reference-test success after real policy adaptation.

Use Qwen2.5-Coder-1.5B-Instruct at the pinned revision in the config, with shared initial LoRA adapters. This is genuine LoRA policy training, not full-parameter training. A 3B/7B confirmation is a later separately budgeted extension; do not provision it before the small-model result and resource profile justify it.

## Tasks, splits and reference semantics

Use [TACO-Cobalt](https://huggingface.co/datasets/osunlp/TACO-Cobalt), revision `88abc66029a542fceedf7b529816fd8cae9180ae`. The official release separates four public tests from hidden tests and supplies a [multi-turn implementation](https://github.com/OSU-NLP-Group/cobalt). Its advertised archived trajectories are not required; this study generates new samples.

Before generation, normalize questions by Unicode NFC plus whitespace collapse, compute hashes, and detect exact task/test duplicates across the source splits. Preserve the official 250-task validation split as final test, remove conflicting copies from training, and log every change. The remaining training tasks are ordered by the declared SHA rule: 128 pilot, 512 proxy fitting, 256 development, then the remaining training pool (4,957 before duplicate exclusions). All trajectories, code variants and turns of one task stay in its task partition. Final test content and outcomes must not select hyperparameters, schedules or models. Pretraining overlap is not established absent; do not call this an uncontaminated benchmark.

Define the reference reward as AND over the **union of public and hidden tests** under a pinned seeded runner. This is a deliberate stronger-test estimand and differs from reporting hidden-only pass rates. Any public-test failure is consequently an exact negative certificate, available to all methods, including full verification. Reference queries only buy unresolved hidden-test information for the final program; cached public results are reused when the program hash matches. Hidden tests can fail fast on the first failure because the reward is binary. Do not repeat tests or add sleep to create an artificial cost advantage.

Public execution feedback is visible during at most four code-revision turns, stopping early when the public suite passes. Hidden feedback is never sent to the actor. Report actual turns, tokens and context truncation rather than calling every trajectory four turns long. This is iterative code generation; it does not by itself demonstrate long-horizon planning or irreversible tool dependencies. Invalid/non-parsable outputs and timeouts follow a fixed declared grading rule and remain in the denominator.

## Isolation and evaluator validation

The current host's `docker info` check failed: the Docker daemon was unavailable at `unix:///Users/shengweizhang/.docker/run/docker.sock`. Do not execute generated programs on this host as a fallback.

Run candidate programs only in a dedicated remote checker using a reviewed microVM or [gVisor sandbox](https://gvisor.dev/docs/architecture_guide/security/). Ordinary container names alone do not establish isolation; [Docker's security documentation](https://docs.docker.com/engine/security/) identifies the relevant host/daemon boundaries. The config requires a pinned image digest, non-root execution, no network, read-only root, no credentials/private workspace/docker socket mounts, dropped capabilities, no new privileges, one CPU, 512 MB memory, 32 processes, a small scratch filesystem, bounded stdout and fixed time limits. Only the program and that test's input are supplied. Expected outputs and hidden-test metadata stay in the trusted controller.

Before model-generated execution, validate input/output comparison, expected failures, timeouts, cleanup and isolation on harmless deterministic fixtures. Check a fixed duplicate subset of program executions for unstable verdicts, and retain disagreements. A repeat-disagreement fraction above 0.5% stops training until explained. A frozen seeded verdict/cache definition is needed for the paper's deterministic reference-label model; genuine flakiness requires a different estimand. Timeout behavior, CPU quotas and hardware remain part of the declared benchmark criterion.

## Four required baselines

| Comparator | Purpose and controls |
|---|---|
| Full-reference GRPO | Complete-group target and learning reference. Shares cheap certificates, caching and optimized fail-fast evaluation. |
| Whole-group residual | Same learned predictor, completion function, task stream and expected unknown-label count as SC; buys all unresolved labels with one group coin. This is the main same-target competitor. |
| Fully verified smaller group batch | Selects fewer whole groups **before generating them**, fully labels them and trains on them. This tests the practical alternative of spending less generation compute. Its rollout/update counts differ and must be reported; it is not a same-fixed-bank MSE comparison. |
| PGBC with fixed scale | Implements Cai v4 direct coefficients, leave-one-out baseline and fixed positive scale, with effective channel rates estimated only from calibration data. No current-group z-score is applied. It intentionally changes the target; compare learning and cost, not its error against an objective it does not claim to recover. |

Proxy-only, label-HT-then-normalize and partial replacement are useful auxiliary fixed-bank checks. They cannot substitute for these four comparators. All methods use the same actor information and access the same logical certificates. Give baselines the same small learning-rate search budget; record failed candidates and tuning expense.

Fit a simple frozen proxy from the designated calibration trajectories using only pre-audit program/trajectory and public-test features. Use calibration generation seed 20260912 and save all calibration labels, including certified negatives. For PGBC, estimate the effective class-conditional rates from these data and use the fixed positive scale 0.5, the maximum standard deviation of a binary reward, not the current training group. The cheap verdict is public-suite success. Under the union-test definition its false-negative rate is zero by construction; estimate the false-positive rate empirically on calibration negatives. If either reference class is absent or the inverse-channel denominator is below 0.05, report an unidentified/unstable baseline and stop that run; do not silently clamp or replace it. Content dependence can still violate a constant false-positive channel. No exact channel-correction claim is made under that misspecification. These operational choices are this proposed baseline implementation, not claims that the cited paper mandates these constants.

## Fresh rollouts, clipping and audit conditioning

Each collection samples 16 prompt groups of 8 complete trajectories from one behavior checkpoint. Temperature is 1, top-p is 1 and top-k truncation is disabled, so saved behavior log probabilities correspond to the actual sampling distribution. Preserve all generated assistant tokens, stop reasons, public feedback, model revision and sampling seed. The training loss masks out prompt/tool tokens and applies the terminal group coefficient to generated assistant tokens.

Perform a single PPO-style pass over the collection in minibatches of two groups. Obtain fresh audit randomness **immediately before** each optimizer step, after fixing its current parameters and scores. Each group is used once. Thus parameters can move away from the behavior checkpoint and ratios can activate clipping, while the current group's audit coin has not already selected those parameters. Do not reuse one random advantage across several parameter updates and silently appeal to a fixed-parameter theorem. If later studying multiple epochs, write a new protocol accounting for revealed-label caches and fresh conditional audit designs.

SC uses the sign-separated coefficients directly in the clipped linear expression. An estimated positive block coefficient may be negative: do not re-clamp, normalize, or route it through an off-the-shelf trainer's ordinary advantage branch. Compare q=1 against the actual full-label loss and parameter gradients on a small real-model fixture, and verify zero-access controls. Set an explicit float32 reference tolerance before checking BF16 calculations. Record clip-active token fraction and gradient clipping; if clipping never activates, do not claim this training run empirically tests the clipping mechanism.

The primary audit setting is expected fraction 0.5 of still-unknown labels, survival floor 0.05, fixed pre-audit order and unit query costs. This preserves a clear query-budget comparison. Actual CPU time can differ across samples and methods; it is measured separately, not assumed known before the query. A cost-aware schedule needs a separately frozen cost predictor and its own stated sensitivity analysis.

## Stages, gates and stopping

1. **Pilot:** use the first 32 then up to 128 fixed pilot tasks, subject to the entered GPU-hour cap. Validate the evaluator, behavior probabilities, masks, complete-label equivalence, audit access barriers, memory and ledger. Measure actual public/hidden-check costs and overlap with generation. The speed-study branch proceeds only if at least 20% of groups have at least four unknown labels, reference evaluation contributes at least 20% of critical-path time, and projected net wall-time saving after scheduler overhead is at least 5%. These are relevance/resource gates, not criteria for selecting favorable observed method outcomes. If they fail, retain the result and do not scale a speedup study on this workload.
2. **Initial training:** five methods, three seeds (1101--1103), 25 collections each; use development outcomes only. Report all methods. A promising resource/quality tradeoff may motivate confirmation; an SC/WG tie or reversal should trigger a decision about paper positioning, not endless new hyperparameter variants. Any change is recorded before confirmation.
3. **Confirmation:** five entirely new seeds (2101--2105), 100 collections, same frozen protocol and all five methods. Open the sealed official validation only for prespecified evaluation. Failure or early resource termination is reported as a censored/failed run, not silently replaced. A larger model or new workload requires another cap and protocol.

Report paired seed differences, task-level uncertainty separately, actual run failures, reference success against GPU-hours/reference-CPU/query count, and all learning curves. A proposed 1 percentage-point quality margin is a research criterion, not an established application tolerance. Five seeds may be underpowered: use pilot variance to show prospective precision, and do not interpret overlapping intervals as equivalence. No significance-only continuation rule or optional stopping on the final test is allowed.

## Complete cost ledger and profiling formula

The append-only JSONL schema in the config includes IDs, actual behavior checkpoint, sampled audit design, all purchased labels, cache hits, retries, failures, generation/update GPU time, public/reference CPU time, scheduling/prediction time, calibration, evaluation and diagnostics. Exact timestamps determine end-to-end elapsed time; component times may overlap and must not simply be added. GPU allocation time includes idle waiting on verifiers when the accelerator remains allocated.

Do not secretly evaluate all training groups completely to calculate MSE. Complete-label diagnostic banks are separate, prespecified, unavailable to the optimizer, and charged in the research ledger. Show both physical experiment totals and per-method deployment costs. Shared physical calibration is purchased once, but a method that needs it must include its own realistic setup/amortization expense when comparing hypothetical deployment pipelines. Methods that do not require calibration must not be charged that cost to make SC look better.

For method m, profile end-to-end collection time t_m on the intended hardware, including actual overlap. With n GPUs, C collections, per-run setup S, evaluation E and diagnostics D, estimated occupied GPU-hours are

`H_m = n * (S + C * t_m + E + D) / 3600`.

Sum over methods and seeds, then add actual shared setup/calibration. Use measured p90 collection times and the configurable safety multiplier to reserve capacity; this is a planning estimate, not a billed price or a performance result. Record token throughput, peak memory, available VRAM, output storage and checkpoint sizes. The planning token ceiling is `C * groups_per_collection * G * max_turns * max_new_tokens`; it is an upper bound, not the number expected to be generated. For the smaller-batch comparator, use its actual smaller collection count/size in the profile.

The planner displays each initial/confirmation stage as a standalone forecast including its entered calibration charge once. If the same calibration is physically reused across both stages, subtract the duplicated calibration charge when summing the two stage forecasts. Add the actual paid pilot ledger separately; this pilot is bounded by its own entered cap and must not disappear from the total. The profile template contains no measured values, so it cannot yet support a numerical resource estimate.

Before any paid run, fill the per-stage aggregate GPU-hour caps, per-run wall cap, GPU count/memory and disk cap. The full suite launches only if the measured forecast fits the corresponding cap; stop after a completed atomic group/step when an entered limit is reached and report unspent/overrun overhead. No price lookup is needed for this planning decision.

## Executable planning check

```sh
python experiments/plan_onpolicy_gpu.py --config configs/onpolicy_gpu_plan.json
python experiments/plan_onpolicy_gpu.py --config configs/onpolicy_gpu_plan.json --profile measured_profile.json
```

The first command validates scientific configuration and prints missing launch inputs. The second computes method/seed GPU-hour forecasts from real measurements. Neither launches a trainer, Docker, cloud resource or paid API. A production trainer adapter, audited remote checker image, resolved dependency lock and actual caps are outstanding implementation/operational work; this document does not claim those pieces already exist.

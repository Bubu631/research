# Public benchmark availability for budgeted group verification

Checked 2026-09-12. This is an availability and design audit, not an experimental performance claim. Local resources are an Apple M1 Pro with 16 GB RAM and approximately 17 GB free disk at task start. No paid GPU, API service, code execution container or external collaboration has been assumed.

## Recommended division of evidence

1. **SWE-Gym historical trajectories for the first real-text diagnostic.** Actual multi-turn actions and historical evaluator labels are available now. Use the data to measure fixed empirical group-update bias, variance and query count. The downloaded release does **not** contain four repeated samples per task from the same complete logging configuration. Therefore it cannot supply an ordinary on-policy GRPO group of size 4 without new generation. A transparently labelled, same-base-model but mixed-temperature/iteration-limit historical group is a possible finite-population diagnostic; retain the strict empty-group result.
2. **TACO-Cobalt for genuinely rerunnable CPU verification and subsequent online RL.** Its Python tasks expose an existing split between public and hidden tests, so proxy errors need not be invented. Actual repeated trajectories must currently be generated: the authors' advertised offline-trajectory SharePoint URL returned HTTP 404 in both web and Python requests checks. Do not describe these missing trajectories as downloaded.
3. **A fresh small-model online experiment is necessary to claim learning or speed improvements.** Generate independent groups with the same pinned checkpoint, preserve all outcomes, run full hidden tests for a validation archive, and use the exact same rollout groups for budgeted verifier comparisons. Later, train 1.5B/3B/7B models on a funded cloud resource only after access and a budget are established. Historical replay is not a substitute for this experiment.

## SWE-Gym: actually downloaded

Source: [official sampled-trajectory dataset](https://huggingface.co/datasets/SWE-Gym/OpenHands-Sampled-Trajectories), revision `baf3a4e4bff514d48ddc08a93a2ade5c126212c7`. The three Parquet files total **301,095,609 bytes**, with 6,055 records and 2,438 task IDs. Exact source URLs and verified file hashes are in `data/swe_gym/source_manifest.json`.

Observed schema includes `instance_id`, `run_id`, `resolved`, `messages`, `tools`, and `test_result`. The latter contains `git_patch`, `apply_patch_output`, `report` and `test_output`; its report distinguishes empty output, patch-application failure, evaluator error and timeout. Many assistant messages have null text and put the actual action in `tool_calls.function.arguments`. Ignoring those fields would remove much of the policy action.

The release has nine `run_id` values spanning GPT-4o temperatures, 30/50-iteration caps, and Claude. There are no exact duplicates under the frozen message-plus-final-patch hash. Strict task/configuration/initial-prompt blocks contain at most two records, and consequently **zero complete G=4 or G=8 groups**. This is a data limitation, not a failed estimator result. Same-task grouping across these configurations is an explicitly different population.

The preserved index identifies the exact shard and row for every record. The label-independent task split, error exclusions, duplicate rule, group ordering and message-only logistic proxy were specified in `docs/swe_gym_data_protocol.md` before the full download. Empty generations remain visible failures; the 44 evaluator/patch/timeout cases are retained in raw audit outputs but excluded from primary valid-verdict groups. There is no outcome-selected mixed-group primary population.

Full trajectories have a median of 14 assistant turns and 41,249 serialized content/action characters; the 95th percentiles are 50 turns and 173,178.8 characters. These are **not token counts**. A bounded local gradient diagnostic will require an explicit transcript serialization, assistant/action loss mask, tokenizer revision and context-window truncation rule. Such a windowed gradient should not be called a full-trajectory gradient.

The source schema has no dedicated elapsed-time field. Textual `in ...s` strings occur in 3,219 final test outputs; they do not cover container setup, scheduling or complete trajectory costs and may contain multiple runner stages. They are unsuitable as a stand-alone end-to-end speed metric.

The dataset card currently lacks an explicit licence field. Code and source-repository licences do not automatically grant redistribution rights for all trajectory content. Keep raw Parquet files outside public source archives until rights are resolved; publishing deterministic IDs, hashes, an acquisition script and derived numerical diagnostics is a separate, reviewable release decision. The smaller [verifier dataset](https://huggingface.co/datasets/SWE-Gym/OpenHands-Verifier-Trajectories) has only `messages` and `resolved`; its mixture and component splits should not be added as independent records.

## TACO-Cobalt: tests available, advertised trajectory archive unavailable

The [official dataset card](https://huggingface.co/datasets/osunlp/TACO-Cobalt) at revision `88abc66029a542fceedf7b529816fd8cae9180ae` lists an MIT licence. Its 6,103 cleaned tasks have at least eight tests, with 5,853 training and 250 validation tasks. Four public cases were selected as the easiest according to 16 attempts of Qwen2.5-Coder-7B-Instruct; remaining cases are hidden. This construction itself induces a meaningful, model-dependent proxy/full-test discrepancy and should be disclosed.

An actual validation row was read successfully. Its fields are `id`, `difficulty`, `question`, `test_cases`, `instruction`, `public_test_cases` and `hidden_test_cases`. Test cases are JSON-encoded strings containing input/output arrays. The [official code](https://github.com/OSU-NLP-Group/cobalt) implements public-test multi-turn interaction followed by a separate hidden-test pass in `eval_multi_turn.py`. Its bundled veRL and vLLM training stack is intended for GPU execution, but the checker can be isolated without installing the complete stack. Generated programs are untrusted code; execution requires an appropriate isolated environment, bounded time and memory, and no access to private workspace files.

The code's downstream trajectory preprocessing includes dynamic sampling and a max-variance selection step; its test mode selects the trajectory with the lowest test improvement. Even if the offline archive becomes accessible, that processed set is not automatically an unbiased collection of all reference rollouts. Preserve upstream selection metadata and split by underlying problem, not individual turn. Original TACO draws from programming competition sites; retain provenance and inspect upstream rights in addition to the derivative card's licence.

## Other options and limits

| Candidate | Useful role | Why it is not the first main experiment |
|---|---|---|
| [EvalPlus](https://github.com/evalplus/evalplus) | Compact Python execution checks; ordinary versus extended test suites produce a proxy/full-suite contrast. | Principally single-turn; public benchmark contamination is possible; additional tests remain a finite correctness criterion. Use for evaluator validation or heldout evaluation, not training on the evaluation set. |
| [APPS](https://github.com/hendrycks/apps) | Public training problems and execution harness, suitable for future same-policy sampling. | Larger raw data than this task needs; does not directly solve the missing multi-turn trajectory issue. |
| [EvoCodeBench](https://github.com/UniPat-AI/EvoCodeBench) | Richer persistent multi-step coding environments and verifier audit cases. | Container/dependency footprint; the June 2026 revision reports grader leakage and test corrections in earlier versions. Pin the repaired version and audit, rather than reusing older scores. |
| [TerminalWrench](https://arxiv.org/html/2604.17596v1) | Real reward-hacking trajectories for a deliberately adversarial robustness extension. | Selected hackable tasks and adversarial sampling are not a representative training population; arbitrary shell/exploit traces must not be executed on this host. |

## Model and measurement bridge

The official [Qwen2.5-Coder-1.5B-Instruct card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) was queried directly: revision `2e1fd397ee46e1388853d2af2c993145b0f1098a`, ungated, Apache-2.0. Its model scale and context capacity do not establish that an arbitrary full-parameter training run fits this host. A frozen output-bias or another explicitly restricted gradient block can support the local estimator check; later full-parameter or LoRA RL must be evaluated separately.

For meaningful cost claims record verifier queries, actual CPU-seconds, timeout counts, peak memory, generation tokens, accelerator time and end-to-end wall time separately. Include a same-budget uniform full-group audit baseline, label-level correction followed by normalization, uncorrected proxy updates, deterministic truncation, and the proposed update-level correction. Include saturated groups and all reversals. Fixed-group unbiasedness does not establish unbiased adaptive optimizer trajectories, expected return improvement or a speedup when generation dominates verification.

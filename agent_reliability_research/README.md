# The Audit Complexity of Group-Relative Policy Updates

[Read the paper (PDF)](paper/main.pdf) · [LaTeX source](paper/main.tex) · [Reference implementation](src/reward_audit.py) · [Results and checks](results/) · [Research protocols](docs/)

How many expensive reference labels are needed to recover a group-relative policy update? This project studies the **fixed complete-label GRPO surrogate**: correcting individual rewards does not generally preserve group normalization or PPO clipping. Exact Boolean query-degree results characterize hard audit caps, while sequential completion uses randomized telescoping to recover the specified coefficients under an expected query budget.

The target is a fixed group's update, with trajectories and parameters held constant. It is distinct from the population policy gradient and the trajectory of an optimizer. Importance weighting, control variates, and randomized telescoping are established methods; the paper identifies their role and cites the relevant prior work.

## Executed studies and results

| Study | Scope | Main finding and evidence |
|---|---|---|
| Algebra and implementation | Complete Boolean cubes, including all 65,536 labels at G=16; independent optimizers | Exact identities and numerical implementations agree. [Theory checks](results/theory_feasibility_checks.json), [sign-separated degree](results/split_query_degree_checks.json), [model moments](results/model_completion_lemma_checks.json). |
| Initial controlled estimation | 45 base settings × 3 budgets; 256 evaluation and 64 separate development groups per base setting | Charging the development-label cost eliminates every tuned-schedule win over the cost-matched whole-group baseline. [Audit and correction explanation](docs/implementation_audit.md). |
| Subsequent model-only scheduling | Fresh seed; 11,520 unique groups and 103,680 method/group/budget rows | Model scheduling wins all 45 calibrated comparisons against whole-group correction and loses all 45 shifted comparisons. [Full results](docs/model_only_results.md), [summary CSV](results/model_only/summary.csv), [independent validation](results/model_only/independent_validation.json). |
| Constructed stateful training | 180 NumPy softmax-policy runs; 432,000 trajectories and 12,096,000 deterministic tool actions | Sequential and whole-group correction perform similarly; sequential correction takes more local computation. These policies are not language models. [Results](docs/stateful_results.md), [summary CSV](results/stateful_training/summary.csv). |
| Frozen historical software trajectories | 49 SWE-Gym tasks, 392 records; pinned Qwen checkpoint and a 32-dimensional added-logit-bias score | At four expected label reveals per eight-trajectory group, the coefficient schedule's projected-MSE ratio to whole-group correction is 0.759, with a pointwise task-bootstrap interval [0.547, 0.996]. [All eight methods](docs/frozen_results.md), [summary CSV](results/frozen_audit/summary.csv), [independent validation](results/frozen_audit/validation.json). |

The frozen-model diagnostic uses historical mixed-policy groups and policy ratio one. It does not test active clipping, full-parameter gradients, fresh software execution, or language-model policy training. Its intervals are pointwise rather than simultaneous across budgets. All adverse regimes and documented implementation/reporting corrections are retained.

## Quick offline checks

Run commands from this project directory, `research/agent_reliability_research`, rather than the parent repository root. Python 3.13 was used for most analysis; study manifests record the exact environment of each run. The constructed training used Python 3.12.14 and NumPy 2.3.5.

The core tests and the following saved-result validators need only NumPy and SciPy:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.5.3 scipy==1.18.1
PYTHONPATH=. python -m unittest discover -s tests -v
```

The validators below require no downloads, model loading, or new training. They rewrite their validation JSON reports, so use a separate working copy if you want to retain every delivered file unchanged.

```bash
python experiments/verify_model_only_study.py
python experiments/verify_frozen_audit_results.py
python experiments/verify_theory_feasibility.py
python experiments/verify_split_query_degree.py
python experiments/verify_model_completion_lemma.py
python experiments/verify_stateful.py
```

For the full analysis, plotting, data processing, and model-extraction dependencies, install [requirements.txt](requirements.txt). Device support and available package wheels may differ from the recorded execution environment.

```bash
python -m pip install -r requirements.txt
python experiments/model_only_study.py --output results/reproduction_model_only
python experiments/stateful_training.py --output results/reproduction_stateful
```

Both full rerun commands use new output directories. Other scripts can write to their default result directories; run those in a separate copy. The original controlled source remains in [results/original_study_source](results/original_study_source/). The current `estimation_study.py` fixes full-audit-probability reporting; `correct_initial_reporting.py` creates separate corrected tables from the original saved CSV, including a signed Monte Carlo squared-bias correction. A reporting correction is not a new experimental replicate.

## Data and frozen-model reproduction

The repository includes **derived metadata and numerical results**, not raw trajectories. In `records.jsonl` and `unique_records.jsonl`, content and prompt fields are SHA-256 hashes; other fields contain public identifiers, numeric features/counts, verdict flags, and split information. Original messages, patches, tool outputs, model weights, and token-ID arrays are excluded. Public-source provenance and dataset-card licensing information are recorded in [source_manifest.json](data/swe_gym/source_manifest.json).

Optional data restoration downloads the pinned public archive; it does not execute archived patches or tool commands. Run it in a separate reproduction copy because it regenerates data and provenance files:

```bash
python experiments/swe_gym_data.py --fetch --parse --fit-proxy
python experiments/swe_gym_metadata_correction.py
python experiments/swe_gym_historical_groups.py
python experiments/verify_swe_gym_data.py
```

<details>
<summary>Optional: restore the pinned tokenizer/model and recompute frozen scores</summary>

Install the full requirements first. The model weights alone are about 3.09 GB. Use explicit cache paths rather than the original author's machine-specific defaults retained in execution sources and manifests.

```bash
export AUDIT_MODEL_DIR="$HOME/.cache/group-relative-audit/qwen1.5b"
export AUDIT_TOKEN_PATH="$HOME/.cache/group-relative-audit/swe_tokens.npz"
python - <<'PY'
import hashlib, json, os, shutil
from pathlib import Path
from huggingface_hub import snapshot_download

metadata = json.loads(Path("data/swe_gym/processed/token_artifact_manifest.json").read_text())["tokenizer"]
model = Path(snapshot_download(
    repo_id=metadata["model"], revision=metadata["revision"],
    local_dir=os.environ["AUDIT_MODEL_DIR"],
    allow_patterns=["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
                    "merges.txt", "vocab.json", "generation_config.json"],
))
raw = (model / "tokenizer.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == metadata["sha256"]
cache = Path("data/swe_gym/tokenizer_cache")
cache.mkdir(parents=True, exist_ok=True)
shutil.copyfile(model / "tokenizer.json", cache / "tokenizer.json")
(cache / "manifest.json").write_text(json.dumps(metadata, indent=2))
Path(os.environ["AUDIT_TOKEN_PATH"]).parent.mkdir(parents=True, exist_ok=True)
PY
python experiments/swe_token_artifact.py --output "$AUDIT_TOKEN_PATH"
python experiments/verify_swe_tokens.py
python experiments/frozen_gradient_bank.py --model "$AUDIT_MODEL_DIR" --tokens "$AUDIT_TOKEN_PATH" --limit 1 --fresh
python experiments/frozen_gradient_bank.py --model "$AUDIT_MODEL_DIR" --tokens "$AUDIT_TOKEN_PATH" --fresh
python experiments/frozen_audit_study.py
```

The extractor verifies the pinned model weight hash. It defaults to Apple MPS; supply `--device cpu` for CPU execution. Device/dtype are part of the declared numerical target and resume fingerprint, so changing device is not a bitwise reproduction of the recorded result. `--fresh` archives the delivered completed output before starting in the reproduction copy; omit it when resuming a matching interrupted run. [Serialization protocol](docs/swe_token_protocol.md), [model code audit](docs/frozen_gradient_code_audit.md), and [final result audit](docs/frozen_audit_implementation_review.md) describe the checks and limitations. `verify_frozen_gradient.py` retains an original-machine model path; it is an execution-specific audit, not part of the portable offline quick check.

</details>

## Build the manuscript

The supplied PDF, bibliography output, figures, and LaTeX sources are in [paper/](paper/). A TeX installation with `latexmk` is required; it is separate from the Python requirements.

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Existing figures are sufficient to compile. To regenerate them from the saved studies, run `python experiments/make_paper_figures.py` from the project directory in a reproduction copy before compiling.

## Project map and future work

- [src/](src/): callback-based online auditing, completion moments, survival optimization, and the constructed stateful environment.
- [experiments/](experiments/) and [tests/](tests/): studies, independent validators, plotting, and unit tests.
- [results/](results/): executed results, costs/timings, checks, and frozen source snapshots.
- [docs/](docs/): protocols, literature comparisons, full results, and reviewer assessment.

The [on-policy GPU protocol](docs/onpolicy_gpu_protocol.md) describes **planned, unexecuted work**. It contributes no completed training results to this repository. The manuscript includes an AI-assistance disclosure and evidence limitations; arXiv submission and conference acceptance are not asserted, and a venue-specific submission still requires its own formatting and policy review.

# Certifying Model Upgrades with Slice-Wise Non-Regression and Incumbent Fallback

**Shengwei Zhang** — University of Pennsylvania  
**Tao Wu, Fei Qian** — Alibaba International Digital Commerce

Author order: Shengwei Zhang, Tao Wu, Fei Qian.

[Paper PDF](main.pdf) · [LaTeX source](main.tex) · [References](references.bib) · [Figures](figures/) · [Results](results/) · [Collection guide](../../README.md)

The paper separates candidate development from independent paired certification against a retained incumbent. It applies established non-inferiority, intersection–union, and Learn-then-Test principles to slice-wise release constraints, keeping the exact incumbent when the evidence does not certify an update. It does not claim a new general testing principle or merging operator.

## Reproduce

Start at the **repository root**. Install the core dependencies once:

```bash
cd research_release
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
```

Run the following from `research_release/` to reproduce the controlled studies and both digits continuation paths in their required order:

```bash
python experiments/base_upgrade.py --calibration-trials 20000 --search-trials 4000 --seed 20260911
python experiments/digits_upgrade.py
python experiments/plot_digits.py
python experiments/digits_balanced.py
python experiments/summarize_digits_paths.py
python -m unittest discover -s tests -p test_base_upgrade.py -v
python -m unittest discover -s tests -p test_digits_upgrade.py -v
```

`digits_balanced.py` checks the recreated incumbent and splits against the original path’s saved checkpoints, so run `digits_upgrade.py` first. The public dataset is included with scikit-learn; this study needs no pretrained-model download. See the [original digits protocol](../../docs/digits_protocol.md), [balanced-continuation protocol](../../docs/digits_balanced_protocol.md), [simulation manifest](results/manifest.json), [original digits manifest](results/digits_manifest.json), and [balanced digits manifest](results/digits_balanced/digits_manifest.json).

To build the PDF from `research_release/`:

```bash
cd papers/base_upgrade
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Use Python 3.13 for the recorded dependency set. Experiment commands overwrite their output directories; use a separate clone to preserve the included run. The saved tables and figures permit compilation without rerunning experiments. From `research_release/`, `python experiments/verify_artifact_integrity.py` checks the recorded evidence across both projects without training models.

## Results and limits

The synthetic populations expose the difference between failing to detect harm and certifying non-inferiority, including candidate-search and multiplicity effects. Those results are governed by the stated score families and assumptions.

The integration study trains a small NumPy classifier on scikit-learn’s **1,797-example digits dataset**, using five fixed seeds. It is not MNIST or a foundation-model benchmark. In both the selective-class and subsequent balanced continuation paths, every proposed release fails the gate and returns the incumbent. The balanced path raises mean reporting accuracy from 94.78% to 95.94%, but that aggregate gain is insufficient for the specified slice-wise certification. All failures are retained in the [per-seed comparison](results/digits_path_all_seeds.csv) and [path summary](results/digits_path_comparison.csv).

The later balanced path reuses the earlier holdouts and is explicitly descriptive, not fresh confirmatory evidence. Five training seeds share one underlying dataset; their variability is not an independent deployment confidence interval. The release guarantees require the specified separation of development and certification, sampling conditions, tolerances, and candidate-testing rule. No production or multilingual model-upgrade result is claimed.

# When Edit Localization Amplifies Relative Selection Bias: Gradient Geometry, Target Mismatch, and Importance Weighting

**Shengwei Zhang, Haoda Dai, Yifei Li, Yuheng Song**  
University of Pennsylvania

[Paper PDF](main.pdf) · [LaTeX source](main.tex) · [References](references.bib) · [Public-study references](public_references.bib) · [Figures](figures/) · [Results](results/) · [Collection guide](../../README.md)

At a fixed model checkpoint, the paper studies how retaining loss on untouched tokens changes selection bias, the learning target, and estimator variance. It gives a general derivative criterion for relative bias, counterexamples to universal amplification, and oracle fixed-target MSE calculations for retention and importance weighting.

## Reproduce

Start at the **repository root**. Install the core dependencies once:

```bash
cd research_release
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
```

Run the following from `research_release/`:

```bash
python experiments/edit_localization.py --repetitions 10000 --seed 20260911
python -m unittest discover -s tests -p test_edit_localization.py -v
```

The synthetic study uses five sample sizes and 10,000 independent repetitions per size. Each sampled dataset is reused across retention coefficients and estimators; the one million estimate rows are not one million independent experiments. See [exact population and simulation summary](results/summary.json) and [Monte Carlo summaries](results/monte_carlo_summary.csv).

For the public post-edit studies:

```bash
python -m pip install -r requirements-models.txt
make reproduce-public
python experiments/verify_public_geometry.py
```

This downloads the pinned public assets and regenerates the eight large per-record gradient arrays, which are omitted from the compact checkout and required by the final verification command. See the [protocol](../../docs/public_postedit_protocol.md), [English–German manifest](results/public_manifest.json), [English–Chinese manifest](results/public_en_zh/public_manifest.json), and [independent audit](../../docs/public_postedit_independent_audit.md).

For the native-parameter extension:

```bash
make reproduce-full
```

This uses 73,886,208 active parameters and needs 4.73 GB for a temporary mean-gradient bank, plus downloaded assets. The recorded M1 Pro run took 36.9 minutes. The [native protocol](../../docs/full_parameter_postedit_protocol.md), [manifest](results/full_parameter/manifest.json), and [Gram matrix](results/full_parameter/gram.npy) document the run. To check the retained Gram-based geometry without rerunning the model, use `python experiments/verify_native_geometry.py` from `research_release/`.

To build the PDF from `research_release/`:

```bash
cd papers/edit_localization
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Use Python 3.13 for the recorded dependency set. Experiment commands overwrite their output directories; reproduce in a separate clone to preserve the included run. Source fragments and generated tables are already included, so PDF compilation does not require rerunning the experiments.

## What the evidence establishes

The public studies use two translation directions, 512 human post-edits per direction, and declared synthetic selection. They are fixed-checkpoint diagnostics, with a small output-bias adaptation study; they do not identify production complaint propensities or demonstrate native-parameter fine-tuning gains.

In all three native endpoint comparisons, hard localization raises **relative** bias while lowering **absolute** bias. One output-bias curve is nonmonotone. The mechanisms reuse records and include a mixture, so they are not independent replications. The added output-bias parameterization and the native model are distinct. Oracle retention and clipping results use population information and do not constitute a deployed tuning procedure.

#!/usr/bin/env python3
"""Post-process completed native-parameter results; no model execution.

Interior roots are computed from all six recorded moments, independently of
the 0.05 plotting grid. This analysis never chooses or discards a mechanism.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers/edit_localization/results/full_parameter"


def extrema(row):
    a, b, c, d, e, f = [float(row[k]) for k in "abcdef"]
    polynomial = np.array([c*e-b*f, c*d-a*f, b*d-a*e])
    nonzero = np.flatnonzero(np.abs(polynomial) > 1e-13 * max(np.max(np.abs(polynomial)), 1e-300))
    roots = [] if not len(nonzero) else np.roots(polynomial[nonzero[0]:])
    interior = sorted(float(r.real) for r in roots if abs(r.imag) < 1e-9 and 0 < r.real < 1)
    candidates = [0.0, *interior, 1.0]
    def rho(alpha):
        return float(np.sqrt((a+2*b*alpha+c*alpha**2)/(d+2*e*alpha+f*alpha**2)))
    vals = [rho(t) for t in candidates]
    tests = [0., 1.]
    if polynomial[0] != 0:
        vertex = -polynomial[1]/(2*polynomial[0])
        if 0 < vertex < 1:
            tests.append(float(vertex))
    signs = [float(np.polyval(polynomial, t)) for t in tests]
    return dict(mechanism=row["mechanism"], rho_Q_0=rho(0), rho_Q_1=rho(1),
                interior_roots=interior, rho_at_roots=[rho(t) for t in interior],
                minimum_alpha=candidates[int(np.argmin(vals))], minimum_rho=min(vals),
                maximum_alpha=candidates[int(np.argmax(vals))], maximum_rho=max(vals),
                monotone_increasing=min(signs) >= 0,
                monotone_decreasing=max(signs) <= 0,
                edited_bias_norm=float(np.sqrt(a)), untouched_bias_norm=float(np.sqrt(c)),
                selected_component_cosine=e/np.sqrt(d*f),
                derivative_polynomial_descending=polynomial.tolist())


def publication_plot(coefficients):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.size":10, "axes.labelsize":10, "xtick.labelsize":9,
                         "ytick.labelsize":9, "legend.fontsize":9}):
        fig, axes = plt.subplots(1,2,figsize=(7.2,3.25))
        alpha = np.linspace(0,1,501)
        for row,color in zip(coefficients,["#3a7b98","#bd7344","#7470a1"]):
            a,b,c,d,e,f = [float(row[k]) for k in "abcdef"]
            bias = np.sqrt(np.maximum(a+2*b*alpha+c*alpha**2,0))
            rho = bias/np.sqrt(d+2*e*alpha+f*alpha**2)
            for ax,values in zip(axes,[rho,bias]):
                ax.plot(alpha,values,color=color,lw=2,label=row["mechanism"].replace("_"," + "))
                ax.set_xlabel(r"Untouched retention $\alpha$")
                ax.set_xlim(0,1)
                ax.grid(alpha=.2)
        axes[0].set_ylabel(r"Relative selection bias $\rho_Q$")
        axes[1].set_ylabel("Absolute gradient bias")
        fig.suptitle("Native translation-model gradients: English–German, n = 256",fontsize=10)
        fig.legend(*axes[0].get_legend_handles_labels(),loc="lower center",ncol=3,
                   frameon=False,bbox_to_anchor=(.5,-.015))
        fig.tight_layout(rect=(0,.08,1,.96))
        output=ROOT/"papers/edit_localization/figures"
        for suffix in ["pdf","png"]:
            fig.savefig(output/f"full_parameter_geometry.{suffix}",dpi=220,bbox_inches="tight")
        plt.close(fig)


def main():
    manifest = json.loads((OUT/"manifest.json").read_text())
    if manifest.get("completed") is not True:
        raise RuntimeError("The native-parameter experiment has not completed.")
    with (OUT/"coefficients.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    gram = np.load(OUT/"gram.npy")
    with (OUT/"public_selected_ids.csv").open() as handle:
        selected = [r for r in csv.DictReader(handle) if r["split"] == "reporting"]
    pe = np.array([.1+.8*float(r["edit_fraction"]) for r in selected])
    pl = np.array([.1+.8*min(float(r["source_length"])/64,1) for r in selected])
    mixing_weight = float(pe.sum()/(pe.sum()+pl.sum()))
    mixture_residuals = []
    for offset in [0,1]:
        contrast = np.zeros(8)
        contrast[6+offset] = 1
        contrast[2+offset] = -mixing_weight
        contrast[4+offset] = -(1-mixing_weight)
        # A Gram-derived squared norm can be slightly negative from cancellation.
        residual = float(contrast@gram@contrast)
        relative = residual/float(gram[6+offset,6+offset])
        if abs(relative) > 1e-8:
            raise AssertionError("The known mixture relation is inconsistent with the saved gradients.")
        mixture_residuals.append(dict(component="E" if offset==0 else "U",
                                      signed_squared_residual=residual,
                                      signed_relative_squared_residual=relative))
    results = [extrema(r) for r in rows]
    loss = np.genfromtxt(OUT/"per_sentence_losses.csv", delimiter=",", names=True)
    previous_nll = np.load(OUT.parent/"public_base_nll.npy")[256:]
    # Independent forward code: unpadded float64 CPU log-softmax versus
    # batched float32 model cross-entropy. Exact byte equality is not expected.
    cross_scope_nll_error = float(np.max(np.abs(previous_nll-loss["full_loss"])))
    if cross_scope_nll_error > 1e-3:
        raise AssertionError(f"Independent baseline NLL check failed: {cross_scope_nll_error}")
    report = dict(scope="Post-processing of all three completed native-parameter mechanisms",
                  sample_count=manifest["sample_count"],
                  trainable_parameter_count=manifest["trainable_parameter_count"],
                  runtime_seconds=manifest["runtime_seconds"],
                  gram_min_eigenvalue=float(np.linalg.eigvalsh(gram).min()),
                  mixture_edit_weight=mixing_weight,
                  mixture_identity_checks=mixture_residuals,
                  mixture_note="The mixed propensity averages edit and length propensities. The three Q settings are not independent replications; the exact eight-vector Gram rank is at most six.",
                  loss_decomposition_max_abs=float(np.max(np.abs(loss["edited_loss"]+loss["untouched_loss"]-loss["full_loss"]))),
                  independent_baseline_nll_max_abs=cross_scope_nll_error,
                  gram_sha256=hashlib.sha256((OUT/"gram.npy").read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  results=results)
    (OUT/"geometry_validation.json").write_text(json.dumps(report,indent=2)+"\n")
    publication_plot(rows)
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()

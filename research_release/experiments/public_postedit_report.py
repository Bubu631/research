#!/usr/bin/env python3
"""Rebuild the public post-edit cross-language figure and numerical report."""
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RELEASE = Path(__file__).resolve().parents[1]
PAPER = RELEASE / "papers/edit_localization"
BASE = PAPER / "results"
MECHANISMS = ["edit", "length", "edit_length"]
LABELS = {"edit":"Edit fraction", "length":"Source length", "edit_length":"Both"}
COLORS = {"edit":"#a6532b", "length":"#2b6886", "edit_length":"#6a568f"}


def read(path):
    return list(csv.DictReader(path.open()))


def stationary(row, suffix=""):
    keys = [f"derivative{suffix}_alpha{k}" for k in [2,1,0]]
    roots = np.roots([float(row[k]) for k in keys])
    return [float(r.real) for r in roots if abs(r.imag)<1e-12 and 0<r.real<1]


def main():
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
    fig, axes = plt.subplots(1,2,figsize=(8,3.25),layout="constrained")
    output, derivatives, sections, table = {}, [], [], []
    for ax,(pair,directory) in zip(axes,[("en-de",BASE),("en-zh",BASE/"public_en_zh")]):
        manifest=json.loads((directory/"public_manifest.json").read_text())
        coeff=[r for r in read(directory/"public_coefficients.csv") if r["split"]=="reporting"]
        curves=[r for r in read(directory/"public_bias_curves.csv") if r["split"]=="reporting"]
        adapters=read(directory/"public_adapter_nll.csv")
        selected=read(directory/"public_selected_ids.csv")
        risk=[r for r in read(directory/"public_fixed_target_risk.csv") if r["split"]=="reporting"]
        output[pair]={"manifest":manifest,"reporting_coefficients":coeff}
        sections.append(f"## {pair}: completed results\n\n")
        sections.append(f"Frozen model: {manifest['model_parameter_count']:,} parameters; 512 selected examples, 256 reporting; runtime {manifest['total_wall_seconds']:.2f} seconds (excluding initial downloads).\n\n")
        sections.append("| Mechanism | rho_Q(0) | rho_Q(1) | rho_P(0) | rho_P(1) | ||b_U|| | Interior stationary alpha |\n|---|---:|---:|---:|---:|---:|---|\n")
        for r in coeff:
            mech=r["mechanism"]
            roots=stationary(r)
            a,b,c=[float(r[f"numerator_alpha{k}"]) for k in [2,1,0]]
            d,h,f=[float(r[f"denominator_alpha{k}"]) for k in [2,1,0]]
            xs=np.linspace(0,1,1001)
            ys=np.sqrt((a*xs**2+b*xs+c)/(d*xs**2+h*xs+f))
            ax.plot(xs,ys,color=COLORS[mech],label=LABELS[mech],lw=1.7)
            for root in roots:
                value=float(np.sqrt((a*root**2+b*root+c)/(d*root**2+h*root+f)))
                ax.plot([root],[value],"o",color=COLORS[mech],markersize=4)
                derivatives.append({"pair":pair,"mechanism":mech,"stationary_alpha":root,"rho_Q":value})
            data=[r for r in curves if r["mechanism"]==mech]
            ax.scatter([float(r["alpha"]) for r in data][::5],[float(r["rho_Q"]) for r in data][::5],
                       s=11,color=COLORS[mech])
            sections.append(f"| {mech} | {float(r['rho_Q_0']):.6f} | {float(r['rho_Q_1']):.6f} | {float(r['rho_P_0']):.6f} | {float(r['rho_P_1']):.6f} | {float(r['b_U_norm']):.8f} | {', '.join(f'{x:.8f}' for x in roots) or 'none'} |\n")
            table.append(f"{pair} & {LABELS[mech]} & {float(r['rho_Q_0']):.3f} & {float(r['rho_Q_1']):.3f} & {float(r['b_U_norm']):.4f} " + chr(92)*2)
        ax.set(title=f"English–{'German' if pair=='en-de' else 'Chinese'} (256 reporting examples)",
               xlabel=r"Untouched-token weight $\alpha$",ylabel=r"Relative bias $\rho_Q(\alpha)$")
        ax.grid(alpha=.18)
        sections.append(f"\nOracle density-ratio IPW recovers the matching localized mean to maximum norm residual {manifest['max_oracle_ipw_population_bias']:.3g}; this is a finite-population numerical identity under known injected selection, not propensity estimation from real complaints.\n\n")
        sections.append(f"Baseline full-PE NLL: {float(adapters[0]['baseline_mean_nll']):.6f} nats/token. Across the 90 predeclared one-step adapters, NLL changes ranged from {min(float(r['nll_change']) for r in adapters):.8f} to {max(float(r['nll_change']) for r in adapters):.8f}. These models were adapted only on diagnostic examples.\n\n")
        sections.append("| Mechanism, alpha=1, step=10 | Population P | Sampled Q | Oracle IPW |\n|---|---:|---:|---:|\n")
        for mech in MECHANISMS:
            vals={r['method']:float(r['nll_change']) for r in adapters if r['mechanism']==mech and float(r['alpha'])==1 and float(r['step_size'])==10}
            sections.append(f"| {mech} | {vals['population_P']:.8f} | {vals['sampled_Q']:.8f} | {vals['oracle_ipw']:.8f} |\n")
        sections.append("\nThe following grid minima are descriptive, computed after reporting outcomes; they were **not** used to select any adapter or amend any protocol.\n\n| Mechanism | Estimator | Fixed-target MSE minimum alpha | Exact MSE |\n|---|---|---:|---:|\n")
        for mech in MECHANISMS:
            for method in ['unweighted','oracle_ipw']:
                best=min([r for r in risk if r['mechanism']==mech and r['method']==method],key=lambda r:float(r['exact_mse']))
                sections.append(f"| {mech} | {method} | {float(best['alpha']):.2f} | {float(best['exact_mse']):.8g} |\n")
        sections.append("\n")
    axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle("Public human post-edits + frozen Marian; shared output-bias gradients; synthetic selection",fontsize=10)
    for ext in ["pdf","png"]:
        fig.savefig(PAPER/f"figures/public_pair_comparison.{ext}",dpi=220)
    plt.close(fig)
    summary=("# Public post-edit experiment: completed result report\n\n"
             "This report describes 1,024 evaluated public human post-edit examples across two language pairs, "
             "including 256 reporting examples per pair and separate 256-example diagnostic populations. "
             "The original archived MT was produced by the dataset's logging systems, not by the OPUS-MT "
             "models used for fixed gradient evaluation here. All selection probabilities are injected; "
             "edit fraction uses completed PE labels and is an oracle experimental mechanism, not a "
             "preannotation observable deployed propensity model.\n\n"
             "The parameters tested here are a new shared output-logit bias adapter. Losses use each "
             "sentence's mean over all PE tokens including EOS. All gradients are paired at one checkpoint. "
             "These results do not establish full-model behavior, real complaint identification, or "
             "decoded translation-quality gains.\n\n"+"".join(sections)+
             "## Interpretation\n\n"
             "In all six reporting scenarios, alpha=0 has larger rho_Q than alpha=1. However, English–German "
             "edit-based selection is not globally monotone: the exact ratio-of-quadratics derivative "
             "has an interior maximum near alpha=0.026984. Its untouched-span bias is nonzero, so the "
             "unbiased-untouched simplification is not applicable. The measured inner products and "
             "complete polynomial coefficients support analysis by the general derivative criterion. "
             "Oracle IPW restores the localized expectation, but it does not uniformly beat unweighted "
             "sampled-Q adaptation on held-out NLL. Both observations are retained.\n\n"
             "The second language extension was frozen after the first run and is disclosed as such. "
             "Model pretraining contamination was not measured. The full arrays, deterministic original "
             "line IDs, runtime versions, hashes, exact executed source snapshots, and protocol snapshots "
             "are in the corresponding results directories.\n")
    (PAPER/"public_results_report.md").write_text(summary)
    (BASE/"public_cross_language_derivative.json").write_text(json.dumps(derivatives,indent=2)+"\n")
    (BASE/"public_endpoint_table.tex").write_text("\n".join(table)+"\n")


if __name__=="__main__":
    main()

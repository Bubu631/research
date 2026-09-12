"""Reproduce the synthetic study of edit localization and record selection.

All gradients are generated finite-population vectors, not language-model
gradients. Exact population moments and independent Monte Carlo repetitions
are saved separately. Run from any working directory with Python >= 3.10.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import platform
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers" / "edit_localization"
SEED = 20260911


def population(name="aligned"):
    signs = np.array(list(itertools.product([-1.0, 1.0], repeat=3)))
    s, z, t = signs.T
    p = np.full(8, 1 / 8)
    propensity = 0.5 * (1 + 0.8 * s)
    ge = np.column_stack([1 + 0.7 * s + 1.2 * z, 0.7 * s + 0.4 * t])
    gu = np.column_stack([1 + 0.15 * z, 0.25 + 0.15 * t])
    if name == "untouched_selected":
        ge = np.column_stack([1 + 0.15 * z, 0.2 + 0.1 * t])
        gu = np.column_stack([1 + 1.2 * s + 0.1 * z, 0.3 * s + 0.1 * t])
    elif name == "opposing":
        gu = np.tile([-2.0, 0.25], (8, 1))
    elif name == "uniform":
        propensity = np.full(8, 0.5)
    elif name != "aligned":
        raise ValueError(name)
    q = p * propensity / (p @ propensity)
    r = p / q
    return p, q, propensity, r, ge, gu


def mean(prob, values):
    return prob @ values


def trace_cov(prob, x, y):
    return float(prob @ np.sum(x * y, axis=1) - (prob @ x) @ (prob @ y))


def ratio_coefficients(p, q, ge, gu):
    u, v = q @ ge, q @ gu
    delta, eps = u - p @ ge, v - p @ gu
    a, b, c = delta @ delta, delta @ eps, eps @ eps
    d, e, f = u @ u, u @ v, v @ v
    return np.array([a, b, c, d, e, f])


def ratio_derivative(alpha, coeff):
    a, b, c, d, e, f = coeff
    denominator = d + 2 * e * alpha + f * alpha**2
    polynomial = (b * d - a * e) + (c * d - a * f) * alpha + (c * e - b * f) * alpha**2
    return 2 * polynomial / denominator**2


def fixed_target_mse(p, q, ge, gu, weights, alpha, n):
    target = p @ (ge + gu)
    ae, au = weights[:, None] * ge, weights[:, None] * gu
    contribution = ae + alpha * au
    bias = q @ contribution - target
    variance = trace_cov(q, contribution, contribution)
    return float(bias @ bias + variance / n)


def optimum_alpha(p, q, ge, gu, weights, n):
    target = p @ (ge + gu)
    ae, au = weights[:, None] * ge, weights[:, None] * gu
    mue, muu = q @ ae, q @ au
    cross = trace_cov(q, ae, au)
    varu = trace_cov(q, au, au)
    denominator = float(muu @ muu + varu / n)
    if denominator <= 0:
        return 0.0
    return float(np.clip((muu @ (target - mue) - cross / n) / denominator, 0, 1))


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig, stem):
    fig.savefig(PAPER / "figures" / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(PAPER / "figures" / f"{stem}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def exact_study():
    rows, summaries, poprows = [], {}, []
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.1))
    labels = ["A: aligned, unbiased U", "B: selection in U", "C: opposing means"]
    alphas = np.linspace(0, 1, 201)
    for ax, name, label in zip(axes, ["aligned", "untouched_selected", "opposing"], labels):
        p, q, propensity, r, ge, gu = population(name)
        coeff = ratio_coefficients(p, q, ge, gu)
        ratios, biases = [], []
        for i in range(len(p)):
            poprows.append(dict(scenario=name, unit=i, p=p[i], q=q[i], propensity=propensity[i], weight=r[i], ge_0=ge[i, 0], ge_1=ge[i, 1], gu_0=gu[i, 0], gu_1=gu[i, 1]))
        for alpha in alphas:
            h = ge + alpha * gu
            bias = q @ h - p @ h
            rho = np.linalg.norm(bias) / np.linalg.norm(q @ h)
            weighted_bias = np.linalg.norm(q @ (r[:, None] * h) - p @ h)
            ratios.append(rho)
            biases.append(np.linalg.norm(bias))
            rows.append(dict(scenario=name, alpha=alpha, relative_bias=rho, absolute_bias=np.linalg.norm(bias), derivative_squared=ratio_derivative(alpha, coeff), oracle_selection_bias=weighted_bias))
        ax.plot(alphas, ratios, color="#246A8B", lw=2.3, label="Relative bias")
        ax.plot(alphas, biases, color="#D48140", lw=1.8, ls="--", label="Absolute bias")
        ax.set(title=label, xlabel=r"Untouched retention $\alpha$")
        ax.grid(alpha=0.2)
        summaries[name] = dict(rho0=ratios[0], rho1=ratios[-1], rho_max=float(max(ratios)), alpha_max=float(alphas[np.argmax(ratios)]), bias_err=float(biases[0]), bias_untouched=float(np.linalg.norm(q @ gu - p @ gu)), mean_inner_product=float((q @ ge) @ (q @ gu)))
    axes[0].set_ylabel("Gradient discrepancy")
    axes[0].legend(fontsize=9)
    fig.tight_layout()
    save_figure(fig, "geometry")
    write_csv(PAPER / "results" / "geometry.csv", rows)
    write_csv(PAPER / "results" / "finite_population.csv", poprows)
    return summaries


def frontier_study():
    p, q, _, r, ge, gu = population()
    rows, summary = [], {}
    alpha_grid = np.linspace(0, 1, 201)
    caps = np.geomspace(r.min(), r.max(), 100)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.5))
    for n, color in zip([1, 4, 16, 64], ["#D48140", "#A35989", "#246A8B", "#39885A"]):
        values = [fixed_target_mse(p, q, ge, gu, r, a, n) for a in alpha_grid]
        optimum = optimum_alpha(p, q, ge, gu, r, n)
        minval = fixed_target_mse(p, q, ge, gu, r, optimum, n)
        summary[str(n)] = dict(oracle_alpha=optimum, oracle_mse=minval, hard_mse=values[0], full_mse=values[-1])
        axes[0].plot(alpha_grid, values, color=color, label=f"n = {n}")
        axes[0].scatter([optimum], [minval], color=color, s=25, zorder=4)
    axes[0].set(xlabel=r"Untouched retention $\alpha$", ylabel="MSE to full traffic gradient", yscale="log")
    axes[0].grid(alpha=0.2)
    axes[0].legend(fontsize=9)
    n = 4
    grid = np.zeros((len(caps), len(alpha_grid)))
    best = (float("inf"), None, None)
    for i, cap in enumerate(caps):
        clipped = np.minimum(r, cap)
        weights = clipped / (q @ clipped)  # population normalizer, not SNIS
        analytic_alpha = optimum_alpha(p, q, ge, gu, weights, n)
        analytic_mse = fixed_target_mse(p, q, ge, gu, weights, analytic_alpha, n)
        if analytic_mse < best[0]:
            best = (analytic_mse, cap, analytic_alpha)
        for j, alpha in enumerate(alpha_grid):
            grid[i, j] = fixed_target_mse(p, q, ge, gu, weights, alpha, n)
            rows.append(dict(n=n, cap=cap, alpha=alpha, mse=grid[i, j], analytic_alpha=analytic_alpha))
    mesh = axes[1].pcolormesh(alpha_grid, caps, grid, shading="nearest", cmap="viridis")
    axes[1].set(xlabel=r"Untouched retention $\alpha$", ylabel="Cap on density ratio r", yscale="log", title="Population-normalized clipping, n = 4")
    axes[1].scatter([best[2]], [best[1]], color="white", edgecolors="black", s=45, zorder=4)
    fig.colorbar(mesh, ax=axes[1], label="Fixed-target MSE")
    fig.tight_layout()
    save_figure(fig, "mse_frontier")
    summary["clipped_n4"] = dict(mse=best[0], cap=best[1], alpha=best[2], cap_grid_size=len(caps))
    write_csv(PAPER / "results" / "mse_frontier.csv", rows)
    return summary


def monte_carlo(repetitions, seed):
    p, q, _, r, ge, gu = population()
    rng = np.random.default_rng(seed)
    target_full = p @ (ge + gu)
    rows, aggregate, stored = [], [], {}
    ns = [1, 4, 16, 64, 256]
    alphas = [0, 0.25, 0.5, 0.75, 1]
    cap = 2.0
    clipped = np.minimum(r, cap)
    popclip = clipped / (q @ clipped)
    for n in ns:
        # Same draws across methods/alpha enable paired comparisons.
        counts = rng.multinomial(n, q, size=repetitions)
        stored[f"counts_n{n}"] = counts
        frequencies = counts / n
        for alpha in alphas:
            h = ge + alpha * gu
            target_own = p @ h
            estimates = {
                "unweighted": frequencies @ h,
                "oracle_ipw": frequencies @ (r[:, None] * h),
                "self_normalized": (frequencies @ (r[:, None] * h)) / (frequencies @ r)[:, None],
                "population_clipped": frequencies @ (popclip[:, None] * h),
            }
            for method, estimates_array in estimates.items():
                errors = np.sum((estimates_array - target_full)**2, axis=1)
                own_errors = np.sum((estimates_array - target_own)**2, axis=1)
                stderr = np.std(errors, ddof=1) / np.sqrt(repetitions)
                empirical_mse = np.mean(errors)
                exact = None
                if method != "self_normalized":
                    weights = {"unweighted": np.ones(8), "oracle_ipw": r, "population_clipped": popclip}[method]
                    exact = fixed_target_mse(p, q, ge, gu, weights, alpha, n)
                bias_own = estimates_array.mean(axis=0) - target_own
                record = dict(n=n, alpha=alpha, method=method, repetitions=repetitions,
                              mse_full=float(empirical_mse), mse_full_mcse=float(stderr),
                              ci_low=float(empirical_mse - 1.96 * stderr), ci_high=float(empirical_mse + 1.96 * stderr),
                              exact_mse_full=exact, mse_own=float(np.mean(own_errors)),
                              bias_own_0=float(bias_own[0]), bias_own_1=float(bias_own[1]),
                              mcse_mean_0=float(np.std(estimates_array[:, 0], ddof=1)/np.sqrt(repetitions)),
                              mcse_mean_1=float(np.std(estimates_array[:, 1], ddof=1)/np.sqrt(repetitions)))
                aggregate.append(record)
                for repetition, (estimate, error) in enumerate(zip(estimates_array, errors)):
                    rows.append(dict(n=n, alpha=alpha, method=method, replicate=repetition, estimate_0=estimate[0], estimate_1=estimate[1], squared_error_full=error))
    write_csv(PAPER / "results" / "monte_carlo_summary.csv", aggregate)
    # NPZ stores all 10,000 repeated multinomial samples losslessly; CSV all estimates.
    np.savez_compressed(PAPER / "results" / "monte_carlo_counts.npz", **stored)
    import gzip
    with gzip.open(PAPER / "results" / "monte_carlo_replicates.csv.gz", "wt", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.2))
    colors = {"unweighted": "#777777", "oracle_ipw": "#246A8B", "self_normalized": "#A35989", "population_clipped": "#D48140"}
    for ax, alpha in zip(axes, [0, 1]):
        for method, color in colors.items():
            records = [v for v in aggregate if v["alpha"] == alpha and v["method"] == method]
            ax.errorbar(ns, [v["mse_full"] for v in records], yerr=[1.96*v["mse_full_mcse"] for v in records], color=color, marker="o", ms=3, capsize=2, label=method.replace("_", " "))
        ax.set(xscale="log", yscale="log", xlabel="Complaint samples n", title=fr"Retention $\alpha = {alpha}$")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("MSE to full traffic gradient")
    axes[1].legend(fontsize=8.5)
    fig.tight_layout()
    save_figure(fig, "monte_carlo")
    return aggregate


def counterexamples():
    p, q, e, r, ge, gu = population()
    w = 1/e
    kappa = float((q @ w**2)/(q @ w)**2)
    floor_variance = trace_cov(q, (w*e)[:, None], (w*e)[:, None])
    # Fully observed two-stratum example: perfect propensity calibration but
    # omitted-outcome selection persists when the covariate V is constant.
    p2 = np.array([0.5, 0.5])
    e2 = np.array([0.1, 0.9])
    q2 = p2 * e2 / (p2 @ e2)
    h2 = np.array([0.0, 2.0])
    # Standard sequence-DPO common prefix is an algebraic observation;
    # no simulated model is used to claim language-level behavior.
    result = dict(weight_dispersion=kappa, alleged_floor=kappa-1,
                  actual_relative_variance_for_h_equals_e=floor_variance,
                  calibrated_coarse_propensity=float(p2 @ e2),
                  coarse_propensity_target=float(p2 @ h2),
                  coarse_propensity_weighted_mean=float(q2 @ h2),
                  coarse_propensity_bias=float(q2 @ h2 - p2 @ h2))
    return result


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if args.repetitions < 2:
        parser.error("At least two repetitions are required for Monte Carlo SE.")
    (PAPER / "results").mkdir(parents=True, exist_ok=True)
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42})
    summary = {"seed": args.seed, "repetitions": args.repetitions,
               "evidence_type": "synthetic finite-population gradients only",
               "geometry": exact_study(), "frontier": frontier_study(),
               "counterexamples": counterexamples()}
    mc = monte_carlo(args.repetitions, args.seed)
    deviations = [abs(row["mse_full"]-row["exact_mse_full"])/row["mse_full_mcse"] for row in mc if row["exact_mse_full"] is not None and row["mse_full_mcse"] > 0]
    summary["max_absolute_mse_standardized_mc_error"] = float(max(deviations))
    summary["selected_monte_carlo_rows"] = [row for row in mc if row["n"] in [1, 16, 256] and row["alpha"] in [0, 1]]
    summary["environment"] = dict(python=platform.python_version(), numpy=np.__version__, matplotlib=matplotlib.__version__, platform=platform.platform())
    summary["elapsed_seconds"] = time.perf_counter() - started
    summary["experiment_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (PAPER / "results" / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    lines = [r"\begin{tabular}{llrr}", r"\toprule", r"$n$ & Estimator & MSE to $\mu_1$ & Monte Carlo SE \\", r"\midrule"]
    labels = {"unweighted": "Unweighted", "oracle_ipw": "Oracle IPW", "self_normalized": "Self-normalized", "population_clipped": "Population-clipped ($M=2$)"}
    for n in [16, 256]:
        for method in labels:
            row = next(v for v in mc if v["n"] == n and v["alpha"] == 1 and v["method"] == method)
            lines.append(f"{n} & {labels[method]} & {row['mse_full']:.4f} & {row['mse_full_mcse']:.4f} " + r"\\")
        if n == 16:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (PAPER / "results" / "mc_table.tex").write_text("\n".join(lines)+"\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ["selected_monte_carlo_rows"]}, indent=2))


if __name__ == "__main__":
    main()

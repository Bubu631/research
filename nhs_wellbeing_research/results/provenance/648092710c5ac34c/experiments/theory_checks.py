"""Independent numerical checks of the theory and the analysis implementation.

This is an audit, not a second benchmark or proof by simulation.  The outline
replay deliberately retains its illustrative, uncalibrated parameters and RNG
ordering.  It is separate from the prospectively specified experiment grid.
Run from any directory with the project's Python environment.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.stats import norm

from common import (gaussian_weights, pair_crossings, first_membership_crossing,
                    static_shrinkage)
from empirical import predict
from simulate import generate

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not bool(condition):
        raise AssertionError(message)


def outline_replay():
    """Replay the source algorithm; regenerate n independently in every panel."""
    rng = np.random.default_rng(20260819)
    mu, tau, sigma, phi, reps, length = 5., .35, 2.5, .85, 4000, 5
    rows = []
    for lo, hi, units in [(800, 3000, 206), (150, 600, 40),
                           (40, 250, 40), (20, 120, 40)]:
        raw_hit, pooled_hit, rebound = [], [], []
        k = max(1, int(units*.2))
        for _ in range(reps):
            n = rng.integers(lo, hi, units)
            theta = np.empty((length+1, units))
            theta[0] = rng.normal(mu, tau, units)
            for t in range(1, length+1):
                theta[t] = mu + phi*(theta[t-1]-mu) + rng.normal(
                    0, tau*np.sqrt(1-phi**2), units)
            y = theta + rng.normal(0, sigma/np.sqrt(n), (length+1, units))
            true_set = set(np.argsort(theta[length-1])[:k])
            raw_set = set(np.argsort(y[length-1])[:k])
            w = np.array([phi**(length-1-t) for t in range(length)])[:, None]
            pooled = (w*y[:length]).sum(0)/w.sum()
            pooled_set = set(np.argsort(pooled)[:k])
            raw_hit.append(len(raw_set & true_set)/k)
            pooled_hit.append(len(pooled_set & true_set)/k)
            ids = np.array(sorted(raw_set))
            rebound.append(np.mean(y[length, ids]-y[length-1, ids]))
        raw_hit = np.asarray(raw_hit)
        pooled_hit = np.asarray(pooled_hit)
        rebound = np.asarray(rebound)
        rows.append(dict(n_lower_inclusive=lo, n_upper_exclusive=hi, units=units,
                         k=k, raw_hit=float(raw_hit.mean()),
                         geometric_hit=float(pooled_hit.mean()),
                         paired_hit_difference=float((pooled_hit-raw_hit).mean()),
                         paired_hit_difference_mcse=float(
                             (pooled_hit-raw_hit).std(ddof=1)/np.sqrt(reps)),
                         zero_intervention_rebound=float(rebound.mean()),
                         rebound_mcse=float(rebound.std(ddof=1)/np.sqrt(reps)),
                         rebound_q10=float(np.quantile(rebound, .1)),
                         rebound_q90=float(np.quantile(rebound, .9))))
    return dict(seed=20260819, repetitions_per_cell=reps,
                interpretation='Exact algorithm replay of illustrative source parameters; not NHS calibration',
                rows=rows)


def pooling_crossover():
    tau2, phi, sigma2, length = .35**2, .85, 6.25, 5
    w = phi**np.arange(length, dtype=float)
    w /= w.sum()
    cov = tau2*phi**np.abs(np.arange(length)[:, None]-np.arange(length)[None, :])
    cross = tau2*phi**np.arange(length)
    drift = tau2-2*w@cross+w@cov@w
    threshold_r = drift/(1-w@w)
    threshold_n = sigma2/threshold_r
    # Independent representation: the error's latent part is a contrast vector
    # applied to the full stationary latent covariance, current wave first.
    contrast = w.copy()
    contrast[0] -= 1
    drift_from_contrast = contrast@cov@contrast
    require(abs(drift-drift_from_contrast) < 1e-15, 'Latent tracking-risk identity')
    rows = []
    for n in [40., threshold_n, 1000.]:
        r = sigma2/n
        pooled_risk = drift+r*(w@w)
        direct_risk = contrast@cov@contrast + r*np.sum(w**2)
        require(abs(direct_risk-pooled_risk) < 1e-15, 'Pooling quadratic risk')
        rows.append(dict(n=n, raw_mse=r, geometric_mse=float(pooled_risk),
                         difference=float(pooled_risk-r)))
    require(rows[0]['difference'] < 0 and rows[2]['difference'] > 0,
            'Crossover has the stated direction')
    require(abs(rows[1]['difference']) < 1e-15, 'Exact crossover equality')
    # Two-wave optimum, allowing different current and previous noise levels.
    r_current, r_previous = .07, .14
    denom = r_current+r_previous+2*tau2*(1-phi)
    old_weight = r_current/denom
    grid = np.linspace(0, 1, 10001)
    risks = r_current*(1-grid)**2 + grid**2*(r_previous+2*tau2*(1-phi))
    optimum_risk = r_current-r_current**2/denom
    require(abs(grid[np.argmin(risks)]-old_weight) < 1.1e-4,
            'Two-wave analytic optimum agrees with an independent dense search')
    return dict(weights_current_to_oldest=w.tolist(), latent_tracking_mse=float(drift),
                noise_variance_crossover=float(threshold_r),
                illustrative_n_crossover=float(threshold_n), risks=rows,
                two_wave_old_weight=float(old_weight),
                two_wave_optimum_mse=float(optimum_risk),
                scope='Fixed-weight current-state MSE; not top-k overlap and not a universal departmental cutoff')


def mean_versus_overlap():
    means = np.array([-1., -.9, -.8])
    sd = np.array([.1, 3., 3.])
    probabilities = []
    integration_errors = []
    for i in range(3):
        others = np.arange(3) != i
        # Finite limits are >12 standard deviations beyond every mean; discarded
        # tails have the upper bound reported below and are negligible here.
        def integrand(x):
            return norm.pdf(x, means[i], sd[i])*np.prod(
                norm.sf(x, means[others], sd[others]))
        value, error = quad(integrand, -40, 40, epsabs=1e-11, epsrel=1e-11,
                            points=[-1., -.9, -.8], limit=300)
        probabilities.append(value)
        integration_errors.append(error)
    tail_bound = float(np.sum(norm.cdf(-40, means, sd)+norm.sf(40, means, sd)))
    require(abs(sum(probabilities)-1) < 1e-10, 'Finite-bottom-one probabilities sum to one')
    mean_choice = int(np.argmin(means))
    overlap_choice = int(np.argmax(probabilities))
    require(mean_choice != overlap_choice, 'Posterior objectives really select different units')
    return dict(posterior_independent=True, posterior_means=means.tolist(),
                posterior_standard_deviations=sd.tolist(), k=1,
                probability_of_true_finite_bottom_one=probabilities,
                quadrature_reported_errors=integration_errors,
                omitted_tail_union_bound=tail_bound,
                severity_optimal_unit_one_based=mean_choice+1,
                overlap_optimal_unit_one_based=overlap_choice+1,
                overlap_gain=float(probabilities[overlap_choice]-probabilities[mean_choice]),
                expected_severity_penalty=float(means[overlap_choice]-means[mean_choice]))


def gaussian_conditioning():
    """Compare implementation against an independently assembled joint matrix."""
    max_weight_error = 0.
    max_variance_error = 0.
    n = np.array([23., 71., 500.])
    length, tau2 = 5, .35**2
    cases = 0
    for phi in [0., .3, .85, .97, 1.]:
        for sigma2 in [0., 6.25]:
            for psi in [0., .5]:
                sw, fw, pv, fv = gaussian_weights(n, tau2, sigma2, phi, psi, length)
                for i, ni in enumerate(n):
                    full = np.array([[tau2*phi**abs(t-s)+(sigma2/ni)*psi**abs(t-s)
                                      for s in range(length+1)] for t in range(length+1)])
                    vals, vecs = np.linalg.eigh(full[:length, :length])
                    kept = vals > vals.max()*1e-12
                    inv = (vecs[:, kept]/vals[kept])@vecs[:, kept].T
                    cs = np.array([tau2*phi**(length-1-t) for t in range(length)])
                    cf = full[length, :length]
                    ref_sw, ref_fw = cs@inv, cf@inv
                    ref_pv, ref_fv = tau2-ref_sw@cs, full[length, length]-ref_fw@cf
                    max_weight_error = max(max_weight_error, np.max(abs(sw[i]-ref_sw)),
                                           np.max(abs(fw[i]-ref_fw)))
                    max_variance_error = max(max_variance_error, abs(pv[i]-ref_pv),
                                             abs(fv[i]-ref_fv))
                    cases += 1
    require(max_weight_error < 1e-10, 'Joint Gaussian conditional mean weights')
    require(max_variance_error < 1e-12, 'Joint Gaussian conditional variances')
    return dict(unit_parameter_cases=cases, maximum_weight_absolute_error=float(max_weight_error),
                maximum_variance_absolute_error=float(max_variance_error),
                includes_correlated_errors_and_singular_noiseless_phi_one=True)


def selected_rebound():
    # This audit uses a separate seed and moderate panel count. Its Monte Carlo
    # uncertainties are diagnostics, not additional main-experiment evidence.
    rng = np.random.default_rng(2026091107)
    reps, units, length, k = 30000, 12, 5, 3
    n = np.geomspace(20, 500, units)
    phi, psi, sigma2, trend, tau2 = .65, .4, 6.25, -.12, .35**2
    theta, y, mu = generate(rng, reps, units, length, n, phi=phi, psi=psi,
                            sigma2=sigma2, trend=trend)
    centred = y[:, :length]-mu[None, :length, None]
    next_means = np.empty((reps, units))
    for i, ni in enumerate(n):
        full = np.array([[tau2*phi**abs(t-s)+(sigma2/ni)*psi**abs(t-s)
                          for s in range(length+1)] for t in range(length+1)])
        coef = np.linalg.solve(full[:length, :length], full[:length, length])
        next_means[:, i] = mu[length]+centred[:, :, i]@coef
    rows = []
    for method, selection_score in [('current', y[:, length-1]),
                                     ('equal_history', centred.mean(axis=1))]:
        idx = np.argsort(selection_score, axis=1)[:, :k]
        actual = np.take_along_axis(y[:, length]-y[:, length-1], idx, axis=1).mean(1)
        predicted = np.take_along_axis(next_means-y[:, length-1], idx, axis=1).mean(1)
        residual = actual-predicted
        mcse = float(residual.std(ddof=1)/np.sqrt(reps))
        z = float(residual.mean()/mcse)
        require(abs(z) < 6, 'Selected-history conditional residual outside broad Monte Carlo diagnostic tolerance')
        rows.append(dict(selection_method=method, actual_mean_change=float(actual.mean()),
                         conditional_mean_change=float(predicted.mean()),
                         residual_mean=float(residual.mean()), residual_mcse=mcse, residual_z=z,
                         fraction_of_panels_with_negative_change=float(np.mean(actual < 0))))
    # Closed-form one-wave decomposition separately checks latent and measurement
    # reversion under independent errors (psi=0), unlike the history test above.
    r = sigma2/n
    reliability = tau2/(tau2+r)
    current_z = np.linspace(-.8, .3, units)
    direct = trend+phi*reliability*current_z-current_z
    three_terms = trend-(1-phi)*reliability*current_z-(1-reliability)*current_z
    require(np.max(abs(direct-three_terms)) < 1e-15, 'Three-term rebound decomposition')
    return dict(seed=2026091107, repetitions=reps, phi=phi, error_autocorrelation=psi,
                common_trend_per_wave=trend, rows=rows,
                one_wave_decomposition_error_autocorrelation=0.,
                one_wave_decomposition_max_error=float(np.max(abs(direct-three_terms))),
                conditioning='All five observed waves; selection is measurable with respect to that history')


def static_rank_geometry():
    z = np.array([-1., -.7])
    n = np.array([1., 10.])
    crossings = pair_crossings(z, n, 3.)
    first = first_membership_crossing(z, n, 1)
    require(abs(first-.5) < 1e-14 and abs(crossings[0][0]-.5) < 1e-14,
            'Two-unit rank reversal threshold')
    require(np.argmin(static_shrinkage(z, n, .49)) == 0 and
            np.argmin(static_shrinkage(z, n, .51)) == 1, 'Actual ranking changes around crossing')
    rng = np.random.default_rng(2026091108)
    max_root_residual, interval_checks, endpoint_checks = 0., 0, 0
    for _ in range(60):
        z = rng.normal(size=9)
        n = np.exp(rng.uniform(np.log(10), np.log(1000), size=9))
        roots = pair_crossings(z, n, 3000.)
        endpoints = sorted({0., 3000., *[row[0] for row in roots]})
        for root, i, j in roots:
            value = static_shrinkage(z, n, root)
            max_root_residual = max(max_root_residual, abs(value[i]-value[j]))
        # The complete rank, not just selected membership, is constant between
        # consecutive crossings. Avoid exact ties at interval endpoints.
        for lower, upper in zip(endpoints[:-1], endpoints[1:]):
            a = lower+.2*(upper-lower)
            b = lower+.8*(upper-lower)
            require(np.array_equal(np.argsort(static_shrinkage(z, n, a)),
                                   np.argsort(static_shrinkage(z, n, b))),
                    'Ranking remains constant in crossing-free intervals')
            interval_checks += 1
        # Independent endpoint certificate for a selected set over [a,b].
        a, b = sorted(rng.uniform(0, 3000, 2))
        chosen = np.argsort(static_shrinkage(z, n, a))[:3]
        other = np.setdiff1d(np.arange(len(n)), chosen)
        certified = True
        for i in chosen:
            for j in other:
                g_a = z[i]-z[j]+a*(z[i]/n[j]-z[j]/n[i])
                g_b = z[i]-z[j]+b*(z[i]/n[j]-z[j]/n[i])
                certified &= (g_a <= 0 and g_b <= 0)
        all_probes_same = all(set(np.argsort(static_shrinkage(z, n, value))[:3]) == set(chosen)
                              for value in np.linspace(a, b, 31))
        # Because every selected/excluded difference is affine, leaving and
        # returning to this same set within [a,b] is impossible.
        require(bool(certified) == all_probes_same, 'Endpoint selection certificate')
        endpoint_checks += 1
    require(max_root_residual < 1e-12, 'Numerical pair equality at analytic crossings')
    return dict(two_unit_crossing=.5, interval_checks=interval_checks,
                endpoint_certificate_checks=endpoint_checks,
                maximum_pair_score_residual_at_crossing=float(max_root_residual),
                exact_tie_scope='Algebra identifies ties; floating-point evaluation at a tie needs a declared numerical tie policy')


def nonidentification():
    phi, tau2, r = .7, 1., 1.
    times = np.arange(4)
    latent = tau2*phi**np.abs(times[:, None]-times[None, :])
    observed = latent+r*np.eye(4)
    covariance_residuals = []
    for c in [.2, .8]:
        alt_latent = c*latent
        alt_noise = (1-c)*latent+r*np.eye(4)
        covariance_residuals.append(float(np.max(abs(observed-alt_latent-alt_noise))))
        require(np.linalg.eigvalsh(alt_noise).min() > 0, 'Alternative error covariance valid')
    y = np.array([-1., -.8])
    original_means = .5*y
    common_c_means = .2*original_means
    heterogeneous_c = np.array([.2, .8])
    alternative_means = heterogeneous_c*original_means
    history_y = np.repeat(y[:, None], 4, axis=1)
    full_history_means = history_y@np.linalg.solve(observed, latent[-1])
    full_history_alternative = heterogeneous_c*full_history_means
    require(np.argmin(original_means) == np.argmin(common_c_means),
            'A common c does not reverse centred mean rankings')
    require(np.argmin(original_means) != np.argmin(alternative_means),
            'Heterogeneous latent variances permit observationally equivalent ranking reversal')
    require(np.argmin(full_history_means) != np.argmin(full_history_alternative),
            'Ranking reversal also holds given the entire observationally equivalent panel')
    gamma = [tau2+r, tau2*phi, tau2*phi**2]
    recovered = dict(phi=gamma[2]/gamma[1], tau2=gamma[1]**2/gamma[2],
                     noise_variance=gamma[0]-gamma[1]**2/gamma[2])
    require(max(abs(recovered['phi']-phi), abs(recovered['tau2']-tau2),
                abs(recovered['noise_variance']-r)) < 1e-14,
            'Positive identification under stronger white-noise assumptions')
    return dict(observed_covariance_max_residual=max(covariance_residuals),
                original_posterior_means=original_means.tolist(),
                common_c_posterior_means=common_c_means.tolist(),
                heterogeneous_c_posterior_means=alternative_means.tolist(),
                full_history_original_posterior_means=full_history_means.tolist(),
                full_history_alternative_posterior_means=full_history_alternative.tolist(),
                necessary_relaxation_for_reversal='Unit-specific latent variances and correlated measurement errors',
                stronger_white_noise_model_recovered_parameters=recovered)


def empirical_prediction_audit():
    rng = np.random.default_rng(2026091109)
    y = 5+rng.normal(size=(12, 4))
    n = rng.integers(20, 3000, size=y.shape).astype(float)
    groups = np.repeat(['a', 'b', 'c'], 4)
    max_error = 0.
    for phi in [.3, .85, 1.]:
        for ratio in [10., 300., 3000.]:
            actual = predict(y, n, groups, 'working_covariance', phi, ratio)
            expected = np.empty(len(y))
            for i in range(len(y)):
                group_mean = y[groups == groups[i]].mean(axis=0)
                covariance = np.array([[phi**abs(t-s)+(ratio/n[i, t] if t == s else 0.)
                                        for s in range(4)] for t in range(4)])
                cross_next = np.array([phi**(4-t) for t in range(4)])
                expected[i] = group_mean[-1]+cross_next@np.linalg.solve(
                    covariance, y[i]-group_mean)
            max_error = max(max_error, np.max(abs(actual-expected)))
    require(max_error < 1e-11, 'Empirical working-covariance forecast with changing n')
    # Check a deterministic linear trend is extrapolated to the next time.
    linear_y = np.array([2+.2*np.arange(4), 6-.1*np.arange(4)])
    linear_prediction = predict(linear_y, np.ones_like(linear_y),
                                np.array(['a', 'a']), 'linear_trend')
    require(np.max(abs(linear_prediction-np.array([2.8, 5.6]))) < 1e-14,
            'Linear forecast time index')
    return dict(maximum_working_forecast_error=float(max_error),
                parameters_cases=9, units_per_case=12,
                linear_trend_extrapolation_passed=True,
                scope='Conditional algebra with plug-in group means; no claim that estimated group means are known population means')


def main():
    results = dict(
        schema_version=1,
        status='all checks passed',
        interpretation='Independent executable algebra/implementation checks; simulations are not mathematical proofs',
        python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
        outline_replay=outline_replay(),
        pooling_crossover=pooling_crossover(),
        posterior_objective_counterexample=mean_versus_overlap(),
        gaussian_conditioning=gaussian_conditioning(),
        selected_rebound=selected_rebound(),
        static_rank_geometry=static_rank_geometry(),
        nonidentification=nonidentification(),
        empirical_prediction_audit=empirical_prediction_audit(),
    )
    paths = [Path(__file__), ROOT/'experiments/common.py', ROOT/'experiments/simulate.py',
             ROOT/'experiments/empirical.py', ROOT/'docs/analysis_protocol.md']
    results['checked_source_sha256'] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    output = ROOT/'results/theory_checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': results['status'], 'output': str(output),
                      'n_crossover': results['pooling_crossover']['illustrative_n_crossover'],
                      'posterior_bottom_one_probabilities': results['posterior_objective_counterexample'][
                          'probability_of_true_finite_bottom_one']}, indent=2))


if __name__ == '__main__':
    main()

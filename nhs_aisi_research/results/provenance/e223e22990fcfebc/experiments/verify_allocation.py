"""Independent finite-case checks of the implemented allocation identities.

This verifier imports the implementation under test, but computes references
with direct linear Gaussian conditioning and sorting among other units.
It does not re-run or tune a study experiment.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from allocation import Belief, gaussian_improvement
from common import thresholds, selected, performance


def main():
    rng = np.random.default_rng(2026091121)
    groups = np.repeat(np.arange(4), [1, 4, 8, 12])
    fraction = 0.25
    means = rng.normal(size=(80, len(groups)))
    # Deliberate ties: some groups have identical means and others straddle ties.
    means[::5] = np.round(means[::5])
    cuts = thresholds(means, groups, fraction)
    reference = np.empty_like(means)
    for row in range(len(means)):
        for i, group in enumerate(groups):
            ids = np.flatnonzero(groups == group)
            k = max(1, int(len(ids) * fraction))
            other = ids[ids != i]
            reference[row, i] = (np.inf if k == len(ids)
                                 else np.sort(means[row, other])[k - 1])
    assert np.array_equal(cuts, reference)
    assert np.all(selected(means, groups, fraction).sum(axis=1) == 7)

    truth = rng.normal(size=means.shape)
    observed = performance(means, np.ones_like(means), truth, groups, fraction)
    chosen = selected(means, groups, fraction)
    direct = []
    for row in range(len(means)):
        oracle_sum = 0.0
        for group in np.unique(groups):
            vals = truth[row, groups == group]
            k = max(1, int(len(vals) * fraction))
            oracle_sum += np.sort(vals)[:k].sum()
        direct.append((truth[row, chosen[row]].sum() - oracle_sum) / 7)
    regret_error = float(np.max(np.abs(observed['regret'] - direct)))
    assert regret_error < 1e-13

    max_mean_error = max_cov_error = max_sd_error = 0.0
    for _ in range(120):
        matrix = rng.normal(size=(2, 2))
        cov = matrix @ matrix.T + 0.01 * np.eye(2)
        mu = rng.normal(size=2)
        channel = int(rng.integers(2))
        h = np.array([1.0, float(channel == 0)])
        noise = float(rng.uniform(0.01, 3.0))
        value = float(rng.normal())
        state = Belief(mu[:1].reshape(1, 1).copy(), mu[1:].reshape(1, 1).copy(),
                       np.array([[cov[0, 0]]]), np.array([[cov[1, 1]]]),
                       np.array([[cov[0, 1]]]), np.zeros((1, 1)), np.zeros((1, 1)))
        denom = h @ cov @ h + noise
        expected_mu = mu + cov @ h * (value - h @ mu) / denom
        expected_cov = cov - np.outer(cov @ h, cov @ h) / denom
        expected_sd = abs((cov @ h)[0]) / np.sqrt(denom)
        obtained_sd = state.innovation_sd(noise, noise)[0, 0, channel]
        max_sd_error = max(max_sd_error, abs(expected_sd - obtained_sd))
        state.update(np.array([0]), np.array([0]), np.array([channel]),
                     np.array([value]), noise, 20)
        obtained_mu = np.array([state.mean.item(), state.bias_mean.item()])
        obtained_cov = np.array([[state.target_var.item(), state.cross.item()],
                                 [state.cross.item(), state.bias_var.item()]])
        max_mean_error = max(max_mean_error, float(np.max(np.abs(expected_mu - obtained_mu))))
        max_cov_error = max(max_cov_error, float(np.max(np.abs(expected_cov - obtained_cov))))
    assert max(max_mean_error, max_cov_error, max_sd_error) < 1e-12

    # K is common across groups and actions even when group sizes/quotas differ.
    sd = rng.uniform(0.01, 2, size=(*means.shape, 2))
    gains = gaussian_improvement((means - cuts)[:, :, None], sd)
    costs = np.array([1.0, 5.0])
    a = np.argmax((gains / costs).reshape(len(means), -1), axis=1)
    b = np.argmax((gains / (7 * costs)).reshape(len(means), -1), axis=1)
    assert np.array_equal(a, b)
    assert np.all(gains[:, groups == 0] == 0)
    result = {
        'status': 'all_checks_passed',
        'seed': 2026091121,
        'unequal_group_sizes': [1, 4, 8, 12],
        'fixed_quotas': [1, 1, 2, 3],
        'total_slots_K': 7,
        'threshold_panels_including_ties': 80,
        'max_average_severity_regret_error': regret_error,
        'gaussian_update_cases': 120,
        'max_posterior_mean_error': max_mean_error,
        'max_posterior_covariance_error': max_cov_error,
        'max_innovation_sd_error': float(max_sd_error),
        'common_one_over_K_action_argmax_identical': bool(np.array_equal(a, b)),
    }
    here = Path(__file__).resolve().parent
    result['source_sha256'] = {name: hashlib.sha256((here / name).read_bytes()).hexdigest()
                               for name in ['allocation.py', 'common.py', 'verify_allocation.py']}
    dest = here.parent / 'results' / 'allocation_verification.json'
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

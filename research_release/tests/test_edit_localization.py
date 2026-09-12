"""Independent numerical checks of the manuscript identities and boundaries."""
import importlib.util
import itertools
from pathlib import Path
import unittest

import numpy as np

PATH = Path(__file__).resolve().parents[1] / "experiments" / "edit_localization.py"
SPEC = importlib.util.spec_from_file_location("edit_localization", PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class TheoryChecks(unittest.TestCase):
    def test_general_derivative_matches_finite_difference(self):
        rng = np.random.default_rng(710)
        for _ in range(50):
            p = rng.dirichlet(np.ones(6))
            e = rng.uniform(0.05, 0.95, 6)
            q = p * e / (p @ e)
            ge, gu = rng.normal(size=(2, 6, 4))
            coeff = M.ratio_coefficients(p, q, ge, gu)
            for alpha in [0.1, 0.4, 0.8]:
                def ratio_squared(a):
                    h = ge + a * gu
                    return np.sum((q @ h - p @ h)**2) / np.sum((q @ h)**2)
                eps = 1e-6
                numerical = (ratio_squared(alpha + eps) - ratio_squared(alpha - eps))/(2*eps)
                np.testing.assert_allclose(M.ratio_derivative(alpha, coeff), numerical, rtol=2e-5, atol=2e-7)

    def test_ipw_identity_all_scenarios_and_alpha(self):
        for name in ["aligned", "untouched_selected", "opposing", "uniform"]:
            p, q, _, r, ge, gu = M.population(name)
            for alpha in np.linspace(0, 1, 17):
                h = ge + alpha * gu
                np.testing.assert_allclose(q @ (r[:, None]*h), p @ h, atol=1e-14)

    def test_mse_matches_exhaustive_sampling(self):
        # Independently enumerate all ordered samples; no covariance formula.
        p = np.array([0.3, 0.7])
        q = np.array([0.8, 0.2])
        ge = np.array([[1.2, -0.2], [-1.0, 2.0]])
        gu = np.array([[0.4, 0.7], [0.2, -0.1]])
        weights = np.array([0.7, 1.6])
        for n in [1, 2, 3, 4]:
            for alpha in [0, 0.37, 1]:
                exact = 0
                for indices in itertools.product(range(2), repeat=n):
                    index = np.array(indices)
                    probability = np.prod(q[index])
                    estimate = np.mean(weights[index, None]*(ge[index]+alpha*gu[index]), axis=0)
                    exact += probability*np.sum((estimate-p @ (ge+gu))**2)
                self.assertAlmostEqual(M.fixed_target_mse(p, q, ge, gu, weights, alpha, n), exact, places=12)

    def test_optimum_beats_dense_grid_for_general_weights(self):
        rng = np.random.default_rng(731)
        for _ in range(20):
            p, q = rng.dirichlet(np.ones(4), size=2)
            ge, gu = rng.normal(size=(2, 4, 3))
            weights = rng.uniform(0.1, 3, 4)
            optimum = M.optimum_alpha(p, q, ge, gu, weights, 5)
            best = M.fixed_target_mse(p, q, ge, gu, weights, optimum, 5)
            self.assertLessEqual(best, min(M.fixed_target_mse(p, q, ge, gu, weights, a, 5) for a in np.linspace(0, 1, 1001)) + 1e-12)

    def test_uniform_selection_does_not_equalize_alpha(self):
        p, q, _, r, ge, gu = M.population("uniform")
        np.testing.assert_array_equal(r, np.ones(8))
        self.assertGreater(np.linalg.norm(p @ ge - p @ (ge+gu)), 1)

    def test_no_weight_only_variance_floor(self):
        p, q, e, r, ge, gu = M.population()
        w = 1/e
        self.assertGreater((q @ w**2)/(q @ w)**2 - 1, 1)
        self.assertAlmostEqual(M.trace_cov(q, (w*e)[:, None], (w*e)[:, None]), 0, places=14)

    def test_snis_single_sample_is_unweighted(self):
        p, q, _, r, ge, gu = M.population()
        estimates = (r[:, None]*(ge+gu))/r[:, None]
        np.testing.assert_allclose(estimates, ge+gu)
        self.assertGreater(np.linalg.norm(q @ estimates - p @ (ge+gu)), 0.5)


if __name__ == "__main__":
    unittest.main()

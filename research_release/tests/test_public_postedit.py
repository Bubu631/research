"""Code-only checks: synthetic logits/gradients; no data or model downloads.

The optional public-model dependencies are required to import this experiment.
The dependency-light core suite remains usable without requirements-models.txt.
"""
import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

AVAILABLE = all(importlib.util.find_spec(name) for name in
                ["torch", "transformers", "sentencepiece", "sacremoses", "huggingface_hub", "requests"])
if AVAILABLE:
    import torch
    path = Path(__file__).resolve().parents[1] / "experiments/public_postedit.py"
    spec = importlib.util.spec_from_file_location("public_postedit_tested", path)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)


@unittest.skipUnless(AVAILABLE, "optional public-model dependencies are not installed")
class PublicPosteditChecks(unittest.TestCase):
    def test_identical_insertion_deletion_substitution_and_tie(self):
        cases = [
            ([1, 2], [1, 2], [False, False], 0, 0),
            ([1, 2], [1, 3, 2], [False, True, False], 1, 0),
            ([1, 3, 2], [1, 2], [False, False], 1, 1),
            ([1, 3, 2], [1, 4, 2], [False, True, False], 1, 0),
            # At the final equal diagonal, the last duplicate is retained.
            ([1], [1, 1], [True, False], 1, 0),
        ]
        for mt, pe, expected, distance, deletions in cases:
            with self.subTest(mt=mt, pe=pe):
                mask, actual_distance, actual_deletions = M.edit_mask(mt, pe)
                np.testing.assert_array_equal(mask, expected)
                self.assertEqual(actual_distance, distance)
                self.assertEqual(actual_deletions, deletions)

    def test_eos_is_untouched_and_both_components_use_full_length(self):
        # Three PE positions: unchanged, inserted, EOS. Different logits make
        # component-specific normalization observable rather than cancelling.
        logits = torch.tensor([[2., -1., .2], [-.3, .7, 1.1], [.4, -.6, 2.]], dtype=torch.float64)
        target = torch.tensor([0, 1, 2])
        mask, _, _ = M.edit_mask([0], [0, 1])
        record = {"line": 17, "mask": np.append(mask, False)}
        class FakeModel:
            class config:
                vocab_size = 3
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(M, "OUT", Path(temp)), patch.object(M, "logits_for", return_value=(logits, target)):
                u, e, nll, checks = M.gradients([record], FakeModel(), "cpu")
        bias = torch.zeros(3, dtype=torch.float64, requires_grad=True)
        losses = torch.nn.functional.cross_entropy(logits+bias, target, reduction="none")
        expected_e = torch.autograd.grad(losses[1]/3, bias, retain_graph=True)[0].numpy()
        expected_u = torch.autograd.grad((losses[0]+losses[2])/3, bias, retain_graph=True)[0].numpy()
        expected_full = torch.autograd.grad(losses.mean(), bias)[0].numpy()
        np.testing.assert_allclose(e[0], expected_e, atol=1e-8)
        np.testing.assert_allclose(u[0], expected_u, atol=1e-8)
        np.testing.assert_allclose(u[0]+e[0], expected_full, atol=1e-8)
        self.assertAlmostEqual(float(nll[0]), float(losses.detach().mean()), places=12)
        self.assertLess(checks["analytical_vs_autograd_max_abs"], 1e-7)

    def test_recorded_derivative_matches_independent_finite_difference(self):
        rng = np.random.default_rng(7014)
        u, e = rng.normal(size=(2, 512, 3))
        records = [{"edit_fraction": float(x), "source_length": int(y)}
                   for x, y in zip(rng.uniform(size=512), rng.integers(4, 80, size=512))]
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(M, "OUT", Path(temp)), contextlib.redirect_stdout(io.StringIO()):
                coefficients, _, _ = M.analyze(u, e, records)
        for row in coefficients:
            sl = slice(0,256) if row["split"] == "diagnostic" else slice(256,512)
            uu, ee = u[sl], e[sl]
            pi = M.propensity(records[sl], row["mechanism"])
            q = pi/pi.sum()
            def ratio_squared(alpha):
                g = ee + alpha*uu
                selected = q@g
                return np.sum((selected-g.mean(0))**2)/np.sum(selected**2)
            for alpha in [.1, .43, .8]:
                denominator = sum(row[f"denominator_alpha{k}"] * alpha**k for k in [0,1,2])
                analytic = sum(row[f"derivative_alpha{k}"] * alpha**k for k in [0,1,2])/denominator**2
                eps = 1e-6
                finite_difference = (ratio_squared(alpha+eps)-ratio_squared(alpha-eps))/(2*eps)
                np.testing.assert_allclose(analytic, finite_difference, rtol=1e-5, atol=1e-7)


if __name__ == "__main__":
    unittest.main()

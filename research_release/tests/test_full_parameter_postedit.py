"""Independent small-vector checks for the native-parameter analysis."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]/"experiments"
AVAILABLE = all(importlib.util.find_spec(k) for k in ["torch", "transformers"])


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPORT = load("full_parameter_report")
if AVAILABLE:
    FULL = load("full_parameter_postedit")


class FullParameterChecks(unittest.TestCase):
    @unittest.skipUnless(AVAILABLE, "optional model dependencies are not installed")
    def test_gram_export_matches_direct_vector_norms(self):
        bank = np.random.default_rng(1206).normal(size=(8, 31))
        curves, _ = FULL.curves_from_gram(bank@bank.T)
        for row in curves:
            j = ["edit", "length", "edit_length"].index(row["mechanism"])
            alpha = row["alpha"]
            target = bank[0]+alpha*bank[1]
            selected = bank[2+2*j]+alpha*bank[3+2*j]
            delta = selected-target
            self.assertAlmostEqual(row["absolute_bias"], np.linalg.norm(delta), places=11)
            self.assertAlmostEqual(row["rho_Q"], np.linalg.norm(delta)/np.linalg.norm(selected), places=11)
            self.assertAlmostEqual(row["rho_P"], np.linalg.norm(delta)/np.linalg.norm(target), places=11)

    def test_interior_extremum_is_not_replaced_by_endpoint_comparison(self):
        # numerator=1, denominator=(alpha-.37)^2+.2: strict interior maximum.
        row = dict(mechanism="synthetic", a=1., b=0., c=0., d=.37**2+.2, e=-.37, f=1.)
        result = REPORT.extrema(row)
        self.assertAlmostEqual(result["maximum_alpha"], .37, places=12)
        self.assertAlmostEqual(result["maximum_rho"], 1/np.sqrt(.2), places=12)
        self.assertFalse(result["monotone_increasing"])
        self.assertFalse(result["monotone_decreasing"])


if __name__ == "__main__":
    unittest.main()

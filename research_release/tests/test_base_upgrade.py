"""Meaningful checks of the release gates and declared synthetic geometry."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from scipy.stats import binom

spec=importlib.util.spec_from_file_location("base_upgrade",Path(__file__).resolve().parents[1]/"experiments"/"base_upgrade.py")
study=importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class ReleaseTests(unittest.TestCase):
    def test_exact_endpoint_and_perfectly_dependent_iut(self):
        for n in [8,32,128]:
            counts=np.arange(n+1)
            mass=binom.pmf(counts,n,.45)
            for alpha in [.01,.05,.2]:
                ps=study.candidate_iut_pvalues(np.repeat(counts[:,None],7,axis=1),n,.02)
                actual=np.sum(mass[ps<=alpha])
                self.assertLessEqual(actual,alpha+1e-12)

    def test_familywise_candidate_correction_exactly(self):
        n,j,alpha=128,100,.05
        counts=np.arange(n+1)
        p=binom.sf(counts-1,n,.45)
        one=np.sum(binom.pmf(counts,n,.45)[p<=alpha/j])
        self.assertLessEqual(1-(1-one)**j,alpha+1e-12)

    def test_fixed_sequence_stops_at_first_failure(self):
        actual=study.fixed_sequence(np.array([[.01,.30,.001],[.9,.001,.001],[.01,.02,.03]]))
        np.testing.assert_array_equal(actual,[[True,False,False],[False,False,False],[True,True,True]])

    def test_identity_is_exact_and_block_oracle_is_larger(self):
        mu,scalar,block=study.geometry()
        for library in [scalar,block]:
            np.testing.assert_array_equal(library[0],np.zeros(2))
            self.assertEqual(float(study.hoeffding_radius(.4*library[0].sum(),128,.05)),0)
        optimum=[]
        for library in [scalar,block]:
            d=library@mu.T
            feasible=np.all(d>=-.01-1e-12,axis=1)
            optimum.append(np.max(d[feasible].mean(axis=1)))
        self.assertGreater(optimum[1],3*optimum[0])
        self.assertAlmostEqual(optimum[0],.01725)
        self.assertAlmostEqual(optimum[1],.064625)

    def test_structural_score_bounds(self):
        mu,_,block=study.geometry()
        for a in [-1,1]:
            for b in [-1,1]:
                d=block@(mu+.06*np.array([a,b])).T
                width=.2*block.sum(axis=1)
                self.assertTrue(np.all(np.abs(d)<=width[:,None]+1e-12))
                # Add a shared incumbent score in [0.48,0.52].
                self.assertGreaterEqual(float(d.min())+.48,0)
                self.assertLessEqual(float(d.max())+.52,1)


if __name__ == "__main__":
    unittest.main()

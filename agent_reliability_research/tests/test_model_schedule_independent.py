"""Independent validation of the model-only moment/PAVA implementation."""
import unittest
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'experiments'))
from src.reward_audit import predicted_increment_variances, variance_optimal_survival
from verify_model_completion_lemma import moment_by_all_patterns


class ModelScheduleTests(unittest.TestCase):
    def test_moments_and_random_orders_against_full_patterns(self):
        rng=np.random.default_rng(2026091401)
        for G in list(range(2,9))+[16]:
            p=rng.uniform(.025,.975,G);order=rng.permutation(G)
            v,M=predicted_increment_variances(p,order)
            reference=moment_by_all_patterns(p[order])
            np.testing.assert_allclose(M,reference,rtol=0,atol=1e-11)
            np.testing.assert_allclose(v,np.diff(reference),rtol=0,atol=1e-11)
            self.assertTrue(np.all(v>=0))

    def test_deterministic_model_and_zero_variance_budget_slack(self):
        for p in [np.zeros(5),np.ones(5),np.array([0.,1.,1.,0.,1.])]:
            v,M=predicted_increment_variances(p)
            np.testing.assert_allclose(v,0,atol=1e-12)
        Q=variance_optimal_survival([1.,0.,0.],[1.,1.,1.],2.,floor=.01)
        np.testing.assert_allclose(Q,[1.,.01,.01],atol=1e-12)
        self.assertAlmostEqual(Q.sum(),1.02)
        self.assertLess(Q.sum(),2.)

    def test_scale_invariant_optimum(self):
        a=np.array([1.,.01,.001]);c=np.ones(3)
        expected=variance_optimal_survival(a,c,1.2)
        for scale in [1e-100,1e-20,1.,1e30,1e100]:
            actual=variance_optimal_survival(a*scale,c,1.2)
            np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12)

    def test_positive_variances_against_independent_constrained_optimizer(self):
        rng=np.random.default_rng(2026091402)
        for _ in range(16):
            G=7;v=rng.uniform(.1,2.,G);cost=rng.uniform(.2,3.,G);budget=.43*cost.sum()
            Q=variance_optimal_survival(v,cost,budget,floor=.015)
            constraints=[{'type':'ineq','fun':lambda x: x[:-1]-x[1:]},
                         {'type':'ineq','fun':lambda x: budget-cost@x}]
            fit=minimize(lambda x: float(np.sum(v/x)),np.full(G,.4),jac=lambda x:-v/x**2,
                         method='SLSQP',bounds=[(.015,1.)]*G,constraints=constraints,
                         options={'ftol':1e-11,'maxiter':1000})
            self.assertLess(abs(np.sum(v/Q)-fit.fun),1e-6)
            self.assertLessEqual(float(cost@Q),budget+1e-9)
            np.testing.assert_allclose(cost@Q,budget,atol=1e-9)
            self.assertTrue(np.all(np.diff(Q)<=1e-12))


if __name__=='__main__':unittest.main()

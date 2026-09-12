import itertools
import unittest
import numpy as np
from src.reward_audit import (split_advantages,completion,completion_path,
    make_survival,cutoff_probabilities,all_prefix_estimates,sequential_audit,
    clipped_surrogate,clipped_ratio_derivative)


class AuditTests(unittest.TestCase):
    def test_completion_against_exhaustive_truth(self):
        rng=np.random.default_rng(419)
        for g in range(2,8):
            labels=np.array(list(itertools.product([0.,1.],repeat=g)))
            for p in [rng.uniform(.03,.97,g),np.r_[np.zeros(g//2),np.ones(g-g//2)]]:
                w=np.prod(np.where(labels,p,1-p),axis=1)
                expected=w@split_advantages(labels)
                np.testing.assert_allclose(completion(p),expected,atol=1e-12)

    def test_every_truth_configuration_and_stop_depth(self):
        p=np.array([.17,.8,.48,.92]);order=np.array([2,0,3,1]);q=np.array([.9,.6,.3,.1])
        for r in itertools.product([0,1],repeat=4):
            path=completion_path(p,r,order)
            estimates=all_prefix_estimates(path,q)
            np.testing.assert_allclose(cutoff_probabilities(q)@estimates,split_advantages(r),atol=1e-12)

    def test_only_purchased_labels_reach_online_algorithm(self):
        p=np.array([.1,.9,.4,.3]);r=np.array([1,1,0,1]);order=np.array([2,0,3,1]);q=np.array([.8,.5,.3,.1])
        class FixedRng:
            def random(self): return .4
        calls=[]
        def oracle(i): calls.append(i);return r[i]
        estimate,bought=sequential_audit(p,oracle,order,q,FixedRng())
        self.assertEqual(calls,[2,0]);self.assertEqual(calls,bought)
        path=completion_path(p,r,order)
        np.testing.assert_allclose(estimate,all_prefix_estimates(path,q)[2])

    def test_sign_split_preserves_actual_clipped_objective(self):
        r=np.array([0,1,1,0.]);ratios=np.array([.7,1.5,.85,1.1]);a=split_advantages(r)
        signed=a[:4]+a[4:]
        reference=np.minimum(ratios*signed,np.clip(ratios,.8,1.2)*signed).mean()
        self.assertAlmostEqual(clipped_surrogate(a,ratios),reference)
        d=clipped_ratio_derivative(a,ratios)
        for i in range(4):
            shift=np.eye(4)[i]*1e-6
            fd=(clipped_surrogate(a,ratios+shift)-clipped_surrogate(a,ratios-shift))/2e-6
            self.assertAlmostEqual(fd,d[i],places=8)

    def test_cost_and_nonzero_tail(self):
        cost=np.array([.2,.5,1,3.])
        q=make_survival(4,1.7,1.4,costs=cost)
        self.assertAlmostEqual(q@cost,1.7,places=10)
        self.assertTrue(np.all(q>0));self.assertTrue(np.all(np.diff(q)<=0))
        self.assertAlmostEqual(cutoff_probabilities(q).sum(),1.)

if __name__=='__main__':unittest.main()

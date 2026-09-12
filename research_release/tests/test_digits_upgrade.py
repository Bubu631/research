import importlib.util
from pathlib import Path
import unittest
import numpy as np

path = Path(__file__).resolve().parents[1]/'experiments/digits_upgrade.py'
spec = importlib.util.spec_from_file_location('digits_upgrade',path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DigitsTests(unittest.TestCase):
    def test_gradient_finite_difference(self):
        rng=np.random.default_rng(99)
        params=module.initialize(rng)
        x=rng.normal(size=(5,64)); y=np.array([1,2,3,4,5])
        _, grads=module.loss_grads(params,x,y)
        for i in range(4):
            for _ in range(8):
                ix=tuple(rng.integers(k) for k in params[i].shape)
                orig=params[i][ix]; h=1e-5
                params[i][ix]=orig+h; a=module.loss_grads(params,x,y)[0]
                params[i][ix]=orig-h; b=module.loss_grads(params,x,y)[0]
                params[i][ix]=orig
                self.assertAlmostEqual((a-b)/(2*h),grads[i][ix],places=6)

    def test_disjoint_splits(self):
        y=np.tile(np.arange(10),180)
        parts=module.split_indices(y,1701)
        self.assertEqual(sum(map(len,parts.values())),len(y))
        self.assertEqual(len(np.unique(np.concatenate(list(parts.values())))),len(y))
        for p in parts.values():
            self.assertEqual(set(y[p]),set(range(10)))

    def test_identity_is_exact(self):
        rng=np.random.default_rng(12)
        old,new=module.initialize(rng),module.initialize(rng)
        for a,b in zip(old,module.merge(old,new,(0.,0.))):
            np.testing.assert_array_equal(a,b)

    def test_gating_direction_and_insufficient_data(self):
        y=np.tile(np.arange(10),4)
        passed,records=module.certify_one(y,y,y,0.03,0.05)
        # Prediction agreement alone is not structural model equality.
        self.assertFalse(passed)
        self.assertTrue(all(r['lower']<r['mean_difference'] for r in records))


if __name__=='__main__':
    unittest.main()

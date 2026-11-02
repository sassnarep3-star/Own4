"""Unit tests for the statistics helpers. Run: python -m unittest research.test_research  (needs pandas/numpy/scipy)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import engine
from config import BREAKEVEN, LEG_DECIMAL


class Helpers(unittest.TestCase):
    def test_breakeven(self):
        self.assertAlmostEqual(BREAKEVEN, 0.5238, places=3)
        self.assertAlmostEqual(1 / LEG_DECIMAL, BREAKEVEN)

    def test_holm_monotone_and_bounded(self):
        out = engine.holm({"a": 0.001, "b": 0.01, "c": 0.04, "d": 0.5})
        self.assertAlmostEqual(out["a"], 0.004); self.assertAlmostEqual(out["b"], 0.03)
        self.assertTrue(all(0 <= v <= 1 for v in out.values()))
        self.assertLessEqual(out["a"], out["b"]); self.assertLessEqual(out["b"], out["c"])

    def test_cluster_mean_matches_plain_when_one_obs_per_cluster(self):
        v = np.array([1., 0., 1., 1., 0., 1.]); m, se = engine.cluster_mean(v, np.arange(6))
        self.assertAlmostEqual(m, v.mean()); self.assertAlmostEqual(se, v.std(ddof=0) / np.sqrt(len(v)), places=6)

    def test_cluster_se_larger_when_clustered(self):
        v = np.array([1., 1., 0., 0., 1., 1., 0., 0.]); _, se_ind = engine.cluster_mean(v, np.arange(8))
        _, se_cl = engine.cluster_mean(v, np.array([0, 0, 1, 1, 2, 2, 3, 3]))
        self.assertGreater(se_cl, se_ind)

    def test_one_sided_p(self):
        self.assertLess(engine.one_sided_p(0.6, 0.01, 0.5238), 0.001)
        self.assertGreater(engine.one_sided_p(0.5, 0.01, 0.5238), 0.9)

    def test_model_no_look_ahead_columns(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({"raw": rng.normal(100, 5, 500), "x": rng.normal(0, 1, 500)})
        df["y"] = df["raw"] + 2 * df["x"] + rng.normal(0, 5, 500)
        m = engine.Model().fit(df, ["x"]); self.assertAlmostEqual(m.beta[0], 2.0, delta=0.6)

    def test_placebo_like_random_sides_centre_on_half(self):
        rng = np.random.default_rng(1); up = rng.random(20000) < 0.55
        hit = ((rng.random(20000) < 0.5) == up).mean(); self.assertAlmostEqual(hit, 0.5, delta=0.02)


if __name__ == "__main__":
    unittest.main()

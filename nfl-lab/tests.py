"""Unit and integration tests for the official-only NFL lab."""
import json
import math
import unittest
from pathlib import Path

import engine

ROOT = Path(__file__).resolve().parent


class StatTests(unittest.TestCase):
    def test_poisson_normalized(self):
        for lam in (1, 12.5, 30):
            p = engine.poisson(lam)
            self.assertAlmostEqual(sum(p), 1.0, places=12)
            self.assertAlmostEqual(sum(i * x for i, x in enumerate(p)), lam, places=6)

    def test_score_features_symmetry(self):
        a = engine.score_features(24, 20)
        b = engine.score_features(20, 24)
        self.assertAlmostEqual(a["p_a_winshare"] + b["p_a_winshare"], 1.0, places=10)
        self.assertAlmostEqual(a["mean_total"], b["mean_total"], places=10)
        self.assertEqual(a["total_line"], b["total_line"])

    def test_lines_are_half_integers(self):
        f = engine.score_features(23.4, 21.1)
        self.assertEqual((f["spread_a"] * 2) % 2, 1.0)
        self.assertEqual((f["total_line"] * 2) % 2, 1.0)
        self.assertTrue(0 <= f["spread_a_cover_p"] <= 1)
        self.assertTrue(0 <= f["total_over_p"] <= 1)

    def test_pearson_and_holm(self):
        self.assertAlmostEqual(engine.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertIsNone(engine.pearson([1, 1, 1], [1, 2, 3]))
        self.assertEqual(engine.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_cluster_ci_deterministic(self):
        vals = [1, 2, 3, 4, 5, 6]
        cl = ["a", "a", "b", "b", "c", "c"]
        self.assertEqual(engine.cluster_ci(vals, cl, reps=200), engine.cluster_ci(vals, cl, reps=200))

    def test_same_game_joint_bounds(self):
        c = engine.same_game_combo(22, 25)
        p1, p2, j = c["p_cover"], c["p_over"], c["p_joint_model"]
        self.assertGreaterEqual(j + 1e-12, max(0, p1 + p2 - 1))
        self.assertLessEqual(j, min(p1, p2) + 1e-12)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = engine.load("games.json")
        cls.standings = engine.load("standings.json")
        cls.players = engine.load("players.json")
        cls.sources = engine.load("sources.json")

    def test_counts_and_missing(self):
        self.assertEqual(len(self.games), 392)
        self.assertEqual(sum(g["season"] == 2025 for g in self.games), 272)
        self.assertEqual(sum(g["season"] == 2026 for g in self.games), 120)
        self.assertEqual(len(self.standings), 96)
        self.assertEqual(len(self.players), 28)
        self.assertEqual(sum(p[k] is None for p in self.players for k in ("value_a", "value_b")), 9)

    def test_integrity(self):
        self.assertTrue(engine.integrity_check(self.games, self.standings, self.players, self.sources)["pass"])

    def test_no_future_rating_update(self):
        model = engine.PointsModel(self.games, self.standings, self.sources)
        cfg = engine.PROTOCOL["models"]["M2"]
        # Before any 2026 week-8 game is processed, rating must not include week 8.
        model.hist["CHI"].append((2026, 8, 99, 0))
        off, deff, n = model.rating("CHI", 2026, 8, cfg)
        clean = engine.PointsModel(self.games, self.standings, self.sources)
        o2, d2, n2 = clean.rating("CHI", 2026, 8, cfg)
        self.assertEqual((off, deff, n), (o2, d2, n2))

    def test_leakage_perturbation(self):
        result = engine.leakage_test(self.games, self.standings, self.sources)
        self.assertTrue(result["pass"])
        self.assertGreater(result["rows_compared"], 1000)

    def test_gate_consistency(self):
        ev = json.loads((ROOT / "results" / "evaluation.json").read_text())
        lb = json.loads((ROOT / "results" / "leaderboard.json").read_text())
        for s in ev["strategies"]:
            self.assertEqual(s["eligible"], all(v == "pass" for v in s["gates"].values()))
        self.assertFalse(lb["eligible"])
        self.assertEqual(lb["reward_points_awarded"], 0)

    def test_market_fields_blank(self):
        current = json.loads((ROOT / "results" / "current_lines.json").read_text())
        for r in current:
            self.assertIsNone(r["market_spread"])
            self.assertIsNone(r["market_total"])
            self.assertIsNone(r["market_odds"])
            self.assertIsNone(r["edge"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

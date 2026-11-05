#!/usr/bin/env python3
"""Unit tests for the nba-lines engine and data contracts.

Run:  python3 -m unittest discover -s tests -v      (from nba-lines/)
"""

import json
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)

import engine  # noqa: E402


def load(name):
    with open(os.path.join(BASE, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


class TestDistributions(unittest.TestCase):
    def test_norm_cdf_symmetry(self):
        for x in (0.0, 0.5, 1.0, 2.5):
            self.assertAlmostEqual(engine.norm_cdf(x) + engine.norm_cdf(-x), 1.0, places=12)

    def test_t_pvalue_known(self):
        # two-sided p for t = 1.96 with 1000 df is about 0.0503
        self.assertAlmostEqual(engine.t_two_sided_p(1.96, 1000), 0.0503, places=3)

    def test_fisher_ci_brackets_r(self):
        lo, hi = engine.fisher_ci(0.3, 500)
        self.assertLess(lo, 0.3)
        self.assertGreater(hi, 0.3)
        self.assertLessEqual(lo, hi)

    def test_bh_fdr_properties(self):
        ps = [0.001, 0.02, 0.04, 0.2, 0.9]
        qs = engine.bh_fdr(ps)
        for p, q in zip(ps, qs):
            self.assertGreaterEqual(q, p - 1e-12)
            self.assertLessEqual(q, 1.0)
        self.assertLess(qs[0], 0.05)

    def test_american_odds(self):
        self.assertAlmostEqual(engine.american_odds(0.5), -100.0, places=6)
        self.assertAlmostEqual(engine.american_odds(0.75), -300.0, places=6)
        self.assertAlmostEqual(engine.american_odds(0.25), 300.0, places=6)
        self.assertIsNone(engine.american_odds(1.0))


class TestBivariateNormal(unittest.TestCase):
    """The closed form P(X>0, Y>0) = 1/4 + asin(rho)/(2*pi) is the reference."""

    def test_closed_form(self):
        for rho in (0.0, 0.1, 0.35, 0.6, -0.4):
            joint, p1, p2 = engine.joint_prob(0.0, 1.0, lambda x: x > 0,
                                             0.0, 1.0, lambda x: x > 0, rho)
            exact = 0.25 + math.asin(rho) / (2 * math.pi)
            self.assertAlmostEqual(joint, exact, places=3)
            self.assertAlmostEqual(p1, 0.5, places=4)
            self.assertAlmostEqual(p2, 0.5, places=4)

    def test_independence_factorises(self):
        joint, p1, p2 = engine.joint_prob(0.3, 1.0, lambda x: x > 0,
                                          0.0, 2.0, lambda x: x < 1.0, 0.0)
        self.assertAlmostEqual(joint, p1 * p2, places=6)

    def test_joint_bounded_by_marginals(self):
        joint, p1, p2 = engine.joint_prob(0.0, 1.0, lambda x: x > 1.5,
                                          0.0, 1.0, lambda x: x > 1.5, 0.5)
        self.assertLessEqual(joint, min(p1, p2) + 1e-12)
        self.assertGreater(joint, 0.0)


class TestRatingModel(unittest.TestCase):
    def _synthetic(self):
        """A league of four teams with known ratings and known home edge."""
        true = {"AAA": 8.0, "BBB": 3.0, "CCC": -2.0, "DDD": -9.0}
        home = 2.5
        games, gid = [], 0
        order = [("AAA", "BBB"), ("CCC", "DDD"), ("AAA", "CCC"), ("BBB", "DDD"),
                 ("BBB", "AAA"), ("DDD", "CCC"), ("CCC", "AAA"), ("DDD", "BBB"),
                 ("AAA", "DDD"), ("BBB", "CCC")] * 4
        for i, (h, a) in enumerate(order):
            margin = true[h] - true[a] + home
            gid += 1
            games.append({
                "date": "2026-10-%02d" % (1 + i // 5), "game_id": "g%03d" % gid,
                "home": h, "away": a,
                "home_pts": int(round(110 + margin / 2)), "away_pts": int(round(110 - margin / 2)),
                "overtime": False, "source_url": "x", "game_url": "x",
            })
        return true, home, games

    def test_recovers_known_ratings_without_shrinkage(self):
        """With lambda = 0 and a balanced schedule the fit must recover the truth."""
        true, home, games = self._synthetic()
        prior = {t: {"net": 0.0, "total": 220.0, "total_tendency": 0.0, "pts": 110.0, "gp": 82,
                     "source_url": "x"} for t in true}
        r, h, _ = engine.fit_ratings(games, prior, lam=0.0)
        for t in true:
            self.assertAlmostEqual(r[t], true[t], delta=0.6, msg=f"{t} not recovered")
        self.assertAlmostEqual(h, home, delta=0.4)

    def test_shrinkage_pulls_toward_prior(self):
        """With lambda = 12 and ten games, estimates must be pulled toward the prior."""
        true, home, games = self._synthetic()
        prior = {t: {"net": 0.0, "total": 220.0, "total_tendency": 0.0, "pts": 110.0, "gp": 82,
                     "source_url": "x"} for t in true}
        shrunk, _, _ = engine.fit_ratings(games, prior, lam=12.0)
        raw, _, _ = engine.fit_ratings(games, prior, lam=0.0)
        for t in true:
            self.assertLess(abs(shrunk[t]), abs(raw[t]) + 1e-9,
                            f"{t}: shrinkage did not reduce magnitude (raw {raw[t]:.2f})")
        self.assertGreater(shrunk["AAA"], shrunk["BBB"])
        self.assertGreater(shrunk["BBB"], shrunk["CCC"])
        self.assertGreater(shrunk["CCC"], shrunk["DDD"])

    def test_no_leakage_from_future_games(self):
        """A prediction must not change when later results change."""
        true, home, games = self._synthetic()
        prior = {t: {"net": 0.0, "total": 220.0, "total_tendency": 0.0, "pts": 110.0, "gp": 82,
                     "source_url": "x"} for t in true}
        base = engine.walk_forward(games, prior, 220.0)
        mutated = [dict(g) for g in games]
        for g in mutated[-5:]:
            g["home_pts"] += 25
        after = engine.walk_forward(mutated, prior, 220.0)
        for i in range(len(games) - 5):
            self.assertEqual(base[i], after[i], f"prediction {i} changed when only future games changed")

    def test_warmup_predictions_are_none(self):
        true, home, games = self._synthetic()
        prior = {t: {"net": 0.0, "total": 220.0, "total_tendency": 0.0, "pts": 110.0, "gp": 82,
                     "source_url": "x"} for t in true}
        preds = engine.walk_forward(games, prior, 220.0)
        for i in range(engine.WARMUP):
            self.assertIsNone(preds[i])


class TestCommittedData(unittest.TestCase):
    def test_results_shape(self):
        rows = load("results_2026-27.json")["rows"]
        self.assertEqual(len(rows), 121)
        self.assertEqual(len({r["game_id"] for r in rows}), 121, "duplicate game ids")
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://www.nba.com/games?date="))
            self.assertTrue(r["game_url"].startswith("https://www.nba.com/game/"))
            self.assertGreater(r["away_pts"], 0)

    def test_reconciliation_matches_standings(self):
        rows = load("results_2026-27.json")["rows"]
        standings = load("standings_2026-11-05.json")["rows"]
        w, l = {}, {}
        for r in rows:
            for t in (r["home"], r["away"]):
                w.setdefault(t, 0)
                l.setdefault(t, 0)
            if r["home_pts"] > r["away_pts"]:
                w[r["home"]] += 1
                l[r["away"]] += 1
            else:
                w[r["away"]] += 1
                l[r["home"]] += 1
        self.assertEqual(len(standings), 30)
        for s in standings:
            self.assertEqual((w[s["abbr"]], l[s["abbr"]]), (s["w"], s["l"]),
                             f"{s['club']} record does not reconcile")

    def test_standings_sources(self):
        for s in load("standings_2026-11-05.json")["rows"]:
            self.assertEqual(s["source_url"], "https://www.nba.com/standings")
            self.assertTrue(s["team_url"].startswith("https://www.nba.com/team/"))

    def test_injury_rows_sourced(self):
        inj = load("injuries_2026-11-05.json")
        self.assertGreaterEqual(len(inj["rows"]), 10)
        for r in inj["rows"]:
            self.assertTrue(r["source_url"].endswith(".pdf"))
            self.assertIn(r["status"], {"Out", "Available", "Probable", "Questionable", "Doubtful",
                                        "Day-To-Day", "NOT YET SUBMITTED"})

    def test_flags_and_review_all_linked(self):
        for f in load("flags.json")["rows"]:
            self.assertTrue(f["links"], f"flag {f['id']} has no link")
        for r in load("repo_review.json")["rows"]:
            self.assertTrue(r["links"], f"finding {r['id']} has no link")

    def test_sources_are_https_and_unique(self):
        src = load("sources.json")["sources"]
        self.assertGreaterEqual(len(src), 15)
        urls = [s["url"] for s in src]
        self.assertEqual(len(urls), len(set(urls)))
        for u in urls:
            self.assertTrue(u.startswith("https://"))

    def test_derived_invariants(self):
        d = load("derived.json")
        self.assertTrue(d["reconciliation"]["passed"])
        self.assertEqual(len(d["gates"]), 10)
        self.assertEqual(sum(1 for b in d["leaderboard"] if b["eligible"]), 0)
        self.assertEqual(sum(b["reward"] for b in d["leaderboard"]), 0)
        self.assertEqual(d["model"]["n"], 121 - engine.WARMUP)
        for c in d["correlations"]:
            self.assertGreaterEqual(c["n"], 3)
            self.assertIsNotNone(c["q"], f"correlation {c['pair']} missing BH q")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Tests for the NFL own-lines workspace. Standard library only.

Run: python3 -m unittest discover -s nfl-own/tests -v
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.dirname(HERE)
ROOT = os.path.dirname(OWN)
sys.path.insert(0, os.path.join(OWN, "engine"))

import analysis as A       # noqa: E402


def derived(name):
    with open(os.path.join(OWN, "data", "derived", name), encoding="utf-8") as fh:
        return json.load(fh)


def official(name):
    with open(os.path.join(OWN, "data", "official", name), encoding="utf-8") as fh:
        return json.load(fh)


class TestArchiveConvention(unittest.TestCase):
    """The sign convention of the third-party archive is the one place a silent error would
    destroy every result, so it is tested rather than assumed."""

    @classmethod
    def setUpClass(cls):
        cls.games = A.load_games()

    def test_spread_line_is_the_away_handicap(self):
        hold = [g for g in self.games if g["season"] >= 2017 and g["mkt_spread"] is not None]
        self.assertGreater(len(hold), 2000)
        # spread_line <= -7 means the VISITOR is a touchdown-plus favourite. Two consequences
        # pin the convention: the home club wins rarely in those games, and the visitor covers
        # at roughly a coin-flip rate.
        big = [g for g in hold if g["mkt_spread"] <= -7]
        self.assertGreater(len(big), 100)
        home_win = sum(1 for g in big if g["home_score"] > g["away_score"]) / len(big)
        away_covers = sum(1 for g in big
                          if (g["home_score"] - g["away_score"]) < g["mkt_spread"]) / len(big)
        self.assertLess(home_win, 0.35, "home clubs should rarely win as 7+ point underdogs")
        self.assertTrue(0.40 <= away_covers <= 0.60,
                        "the 7+ point visitor favourite should cover about half the time, got %.3f"
                        % away_covers)

    def test_mean_spread_tracks_mean_home_margin(self):
        hold = [g for g in self.games if g["season"] >= 2017 and g["mkt_spread"] is not None]
        mean_spread = sum(g["mkt_spread"] for g in hold) / len(hold)
        mean_margin = sum(g["home_score"] - g["away_score"] for g in hold) / len(hold)
        self.assertAlmostEqual(mean_spread, mean_margin, delta=1.0)

    def test_every_game_has_two_plausible_scores(self):
        for g in self.games:
            self.assertTrue(0 <= g["home_score"] <= 100, g)
            self.assertTrue(0 <= g["away_score"] <= 100, g)


class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = A.load_games()
        cls.forecasts = A.build_forecasts(cls.games)

    def test_no_look_ahead(self):
        """A forecast for season S must not change when later seasons are removed."""
        cut = [g for g in self.games if g["season"] <= 2020]
        fc_short = A.build_forecasts(cut)
        a = {f["game_id"]: f["own_margin"] for f in self.forecasts if f["season"] == 2020}
        b = {f["game_id"]: f["own_margin"] for f in fc_short if f["season"] == 2020}
        self.assertTrue(a)
        for k in a:
            self.assertAlmostEqual(a[k], b[k], places=9, msg=k)

    def test_own_line_is_worse_than_the_market_on_the_holdout(self):
        acc = derived("accuracy.json")
        self.assertGreater(acc["spread_mae_own"], acc["spread_mae_market"])
        self.assertGreater(acc["total_mae_own"], acc["total_mae_market"])

    def test_pushes_are_dropped_not_counted_as_wins(self):
        f = {"mkt_spread": -3.0, "mkt_total": 50.0, "own_margin": 6.0, "own_total": 55.0,
             "home_score": 24, "away_score": 27, "home_rest": 7, "away_rest": 7,
             "roof": "outdoors", "wind": 0, "is_div": False, "game_id": "x",
             "season": 2020, "week": 1}
        # home lost by 3, market home margin +3 => exact push => no bet
        self.assertEqual(A.select_legs(f, "S1"), [])


class TestGatesAndRewards(unittest.TestCase):
    def test_nothing_is_reward_eligible(self):
        board = derived("leaderboard.json")
        self.assertEqual(board["total_points_awarded"], 0)
        for r in board["rows"]:
            self.assertFalse(r["eligible"], r["id"])
            self.assertEqual(r["points_awarded"], 0, r["id"])
            self.assertNotEqual(r["gates_passed"], "12/12", r["id"])

    def test_every_strategy_fails_prospective_replication(self):
        strat = derived("strategies.json")
        for sid, r in strat["results"].items():
            self.assertFalse(r["gate_detail"]["G12"], sid)

    def test_expected_strategy_count(self):
        strat = derived("strategies.json")
        self.assertEqual(len(strat["results"]), 14)
        self.assertEqual(len(strat["definitions"]), 19)

    def test_no_strategy_survives_the_split_half_retest(self):
        elig = derived("eligibility.json")
        self.assertTrue(elig["rows"])
        for r in elig["rows"]:
            self.assertNotEqual(r.get("both_halves"), True, r["id"])


class TestProvenance(unittest.TestCase):
    def test_no_market_value_is_published(self):
        own = derived("own_lines.json")
        for r in own["rows"]:
            self.assertIsNone(r["market_spread"])
            self.assertIsNone(r["market_total"])
            self.assertIsNone(r["market_price"])

    def test_every_own_line_cites_the_official_schedule(self):
        own = derived("own_lines.json")
        for r in own["rows"]:
            self.assertIn("nfl.com", r["source_url"])
        self.assertEqual(len(own["rows"]), 13)

    def test_official_integrity_has_no_failures(self):
        integ = official("integrity_official.json")
        self.assertEqual(integ["summary"]["fail"], 0)
        self.assertGreaterEqual(integ["summary"]["pass"], 40)

    def test_player_logs_reconcile_to_season_totals(self):
        players = official("players_2026-11-13.json")
        for slug, p in players["logs"].items():
            if not p["season_totals"]:
                continue
            if p["kind"] == "passing":
                self.assertEqual(sum(g[4] for g in p["games"]), p["season_totals"]["cmp"], slug)
                self.assertEqual(sum(g[5] for g in p["games"]), p["season_totals"]["att"], slug)
                self.assertEqual(sum(g[6] for g in p["games"]), p["season_totals"]["yds"], slug)
            else:
                self.assertEqual(sum(g[4] for g in p["games"]), p["season_totals"]["rec"]
                                 if p["kind"] == "receiving" else p["season_totals"]["att"], slug)

    def test_correlations_publish_their_sample_size(self):
        corr = derived("correlations.json")
        for c in corr["rows"]:
            self.assertIsNotNone(c["n"], c["id"])
            if c["r"] is not None:
                self.assertGreaterEqual(c["n"], 4, c["id"])


class TestSite(unittest.TestCase):
    def test_verifier_passes(self):
        r = subprocess.run([sys.executable, os.path.join(OWN, "engine", "verify_site.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-2000:])
        self.assertIn("VERIFY PASSED", r.stdout)

    def test_every_page_links_back_home_and_to_the_flags(self):
        pages = os.path.join(OWN, "pages")
        for f in sorted(os.listdir(pages)):
            if not f.endswith(".html"):
                continue
            with open(os.path.join(pages, f), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn('href="../index.html"', body, f)
            self.assertIn("flagged.html", body, f)


if __name__ == "__main__":
    unittest.main()

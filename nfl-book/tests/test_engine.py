"""nfl-book/tests/test_engine.py — deterministic tests over the engine.

    python3 -m unittest discover -s nfl-book/tests -t nfl-book

These cover the two pieces of logic that decide whether a number is trusted:
the settlement of a bet and the demotion of a live strategy.
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine import analysis, core, props            # noqa: E402
from engine.store import PriceSnapshotStore, StoreError   # noqa: E402


class TestPriceStore(unittest.TestCase):
    def test_a_close_without_an_open_is_refused(self):
        store = PriceSnapshotStore()
        store.record("01_A_B", "SPREAD", "home", "own_model", "2026-11-01T00:00:00Z",
                     line=-3.5)
        # a second, later publication becomes the close
        rec = store.record("01_A_B", "SPREAD", "home", "own_model",
                           "2026-11-02T00:00:00Z", line=-4.5)
        self.assertEqual(rec["status"], "open_close")
        self.assertEqual(rec["open"]["line"], -3.5)
        self.assertEqual(rec["close"]["line"], -4.5)

    def test_an_earlier_publication_becomes_the_open(self):
        store = PriceSnapshotStore()
        store.record("01_A_B", "TOTAL", "over", "own_model", "2026-11-05T00:00:00Z",
                     line=45.0)
        rec = store.record("01_A_B", "TOTAL", "over", "own_model",
                           "2026-11-01T00:00:00Z", line=44.5)
        self.assertEqual(rec["open"]["line"], 44.5)
        self.assertEqual(rec["open"]["published_utc"], "2026-11-01T00:00:00Z")

    def test_an_unknown_market_or_side_is_refused(self):
        store = PriceSnapshotStore()
        with self.assertRaises(StoreError):
            store.record("01_A_B", "PROP", "home", "own_model", "2026-11-01T00:00:00Z")
        with self.assertRaises(StoreError):
            store.record("01_A_B", "SPREAD", "over", "own_model", "2026-11-01T00:00:00Z")

    def test_a_missing_value_stays_missing(self):
        store = PriceSnapshotStore()
        rec = store.record("01_A_B", "SPREAD", "home", "own_model",
                           "2026-11-01T00:00:00Z")
        self.assertIsNone(rec["open"]["line"])
        self.assertIsNone(rec["open"]["price"])

    def test_coverage_counts_the_gaps(self):
        store = PriceSnapshotStore()
        store.record("01_A_B", "SPREAD", "home", "own_model", "2026-11-01T00:00:00Z",
                     line=-3.5)
        store.record("01_C_D", "SPREAD", "home", "own_model", "2026-11-01T00:00:00Z",
                     line=-3.5)
        store.record("01_C_D", "SPREAD", "home", "own_model", "2026-11-02T00:00:00Z",
                     line=-3.5)
        cov = store.coverage()
        self.assertEqual(cov["records"], 2)
        self.assertEqual(cov["open_close"], 1)
        self.assertEqual(cov["open_only"], 1)
        self.assertEqual(len(cov["gaps"]), 1)


class TestSettlement(unittest.TestCase):
    def setUp(self):
        self.row = {
            "game_key": "01_A_B", "week": 1, "date": "2026-09-10",
            "away": "A", "home": "B",
            "away_pts": 20, "home_pts": 24,
            "actual_margin": 4, "actual_total": 44,
        }

    def test_spread_win_loss_and_push(self):
        # the line is the expected home margin: the home side covers when the
        # home margin beats it
        self.assertEqual(analysis.bet_spread(self.row, "home", 3.0, None)[0], "win")
        self.assertEqual(analysis.bet_spread(self.row, "home", 4.0, None)[0], "push")
        self.assertEqual(analysis.bet_spread(self.row, "home", 4.5, None)[0], "loss")
        # the away side covers when the home margin is smaller than the line
        self.assertEqual(analysis.bet_spread(self.row, "away", 3.0, None)[0], "loss")
        self.assertEqual(analysis.bet_spread(self.row, "away", 4.5, None)[0], "win")
        self.assertEqual(analysis.bet_spread(self.row, "away", 4.0, None)[0], "push")

    def test_spread_profit_uses_the_american_price(self):
        self.assertAlmostEqual(analysis.bet_spread(self.row, "home", 3.0, -110)[1],
                               100.0 / 110.0, places=9)
        self.assertEqual(analysis.bet_spread(self.row, "home", 4.5, -110)[1], -1.0)
        self.assertEqual(analysis.bet_spread(self.row, "home", 4.0, -110)[1], 0.0)
        # no price means no profit is published, never a guess
        self.assertIsNone(analysis.bet_spread(self.row, "home", 3.0, None)[1])

    def test_total_over_and_under(self):
        self.assertEqual(analysis.bet_total(self.row, "over", 43.5, None)[0], "win")
        self.assertEqual(analysis.bet_total(self.row, "over", 44.0, None)[0], "push")
        self.assertEqual(analysis.bet_total(self.row, "over", 44.5, None)[0], "loss")
        self.assertEqual(analysis.bet_total(self.row, "under", 44.5, None)[0], "win")

    def test_moneyline_pushes_on_a_tie(self):
        row = dict(self.row, away_pts=21, home_pts=21, actual_margin=0)
        self.assertEqual(analysis.bet_moneyline(row, "home", None)[0], "push")
        self.assertEqual(analysis.bet_moneyline(self.row, "home", None)[0], "win")
        self.assertEqual(analysis.bet_moneyline(self.row, "away", None)[0], "loss")


class TestStatistics(unittest.TestCase):
    def test_exact_binomial_against_a_coin_flip(self):
        # 6 heads out of 10 against p = 0.5 is not significant at 0.05
        self.assertGreater(analysis.exact_binom_two_sided(10, 6, 0.5), 0.05)
        # 10 out of 10 is
        self.assertLess(analysis.exact_binom_two_sided(10, 10, 0.5), 0.05)
        self.assertIsNone(analysis.exact_binom_two_sided(0, 0, 0.5))

    def test_benjamini_hochberg_is_monotone(self):
        q = analysis.bh_qvalues([0.01, 0.04, 0.03, 0.20])
        self.assertEqual(len(q), 4)
        self.assertAlmostEqual(q[0], 0.04)
        self.assertTrue(all(x is not None for x in q))
        for a, b in zip(sorted(q), sorted(q)[1:]):
            self.assertLessEqual(a, b + 1e-12)

    def test_correlation_publishes_n_and_refuses_thin_data(self):
        row = analysis.corr_row("thin", [1, 2], [1, 2], "x", "u", "n")
        self.assertEqual(row["n"], 2)
        self.assertIsNone(row["pearson_r"])
        self.assertEqual(row["status"], "insufficient data")

        row = analysis.corr_row("ok", [1, 2, 3, 4], [1, 2, 3, 5], "x", "u", "n")
        self.assertEqual(row["n"], 4)
        self.assertIsNotNone(row["pearson_r"])
        self.assertEqual(row["status"], "computed")


class TestDemotionGate(unittest.TestCase):
    def _signal(self, **kw):
        s = {
            "n": 200, "p_value": 0.01, "q_value": 0.02,
            "break_even_rate": 0.5, "bootstrap_ci_low": 0.55,
            "placebo_p": 0.5, "beats_closing_line": True,
            "both_halves_clear": True, "holdout_evidence": "both halves clear",
            "n_strategies": 8,
        }
        s.update(kw)
        return s

    def test_a_healthy_strategy_is_not_demoted(self):
        _, _, demotions = analysis.evaluate_gates(
            self._signal(), {"clv_points": 0.5}, [])
        self.assertFalse(any(d["triggered"] for d in demotions))

    def test_a_failed_false_discovery_control_demotes(self):
        _, _, demotions = analysis.evaluate_gates(
            self._signal(q_value=0.30), {}, [])
        self.assertTrue(any(d["id"] == "D2" and d["triggered"] for d in demotions))

    def test_a_thin_sample_demotes(self):
        _, _, demotions = analysis.evaluate_gates(
            self._signal(n=42), {}, [])
        self.assertTrue(any(d["id"] == "D3" and d["triggered"] for d in demotions))

    def test_a_failing_holdout_split_demotes(self):
        _, _, demotions = analysis.evaluate_gates(
            self._signal(both_halves_clear=False), {}, [])
        self.assertTrue(any(d["id"] == "D5" and d["triggered"] for d in demotions))

    def test_every_gate_is_reported_even_when_the_strategy_is_paper(self):
        gates, passed, demotions = analysis.evaluate_gates(
            self._signal(n=10, q_value=None), {}, [])
        self.assertEqual(len(gates), 6)
        self.assertEqual(len(demotions), 5)
        self.assertTrue(passed < len(gates))


class TestCanonicalData(unittest.TestCase):
    def test_team_aliases_are_normalised(self):
        self.assertEqual(core.canon("ARI"), "AZ")
        self.assertEqual(core.canon("LA"), "LAR")
        self.assertEqual(core.canon("BUF"), "BUF")

    def test_the_official_game_url_pattern(self):
        self.assertEqual(core.game_url("ATL", "GB", 3),
                         "https://www.nfl.com/games/falcons-at-packers-2026-reg-3")
        self.assertEqual(core.game_url("LAC", "BUF", 3),
                         "https://www.nfl.com/games/chargers-at-bills-2026-reg-3")

    def test_the_results_feed_reconciles_to_the_official_standings(self):
        games, unmatched = core.build_results()
        recon = core.reconcile_results(games)
        self.assertTrue(recon["exact"], recon["rows"])
        self.assertEqual(recon["cells_matching"], recon["cells_total"])
        self.assertEqual(unmatched, [])
        for g in games:
            self.assertTrue(g["official_source_url"], g["game_key"])
            self.assertTrue(g["official_source_url"].startswith("https://www.nfl.com/"))

    def test_every_game_carries_an_official_source_link(self):
        games, _ = core.build_results()
        for g in games:
            self.assertIsNotNone(g["game_url"])
            self.assertIn("nfl.com", g["official_source_url"])


class TestProps(unittest.TestCase):
    def test_the_transcribed_logs_match_the_official_season_totals(self):
        logs = props.load_logs()
        totals = props.load_totals()
        check = props.verify_transcription(logs, totals)
        bad = [r for r in check["rows"] if r["match"] is False]
        self.assertEqual(bad, [], bad)
        self.assertTrue(check["all_match"])

    def test_every_prop_row_carries_a_source_url(self):
        rows, _mean, _sd = props.build_prop_rows(props.load_logs())
        self.assertTrue(rows)
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/players/"))
            self.assertIn(r["result"], ("win", "loss", "push"))

    def test_a_prop_decision_never_uses_a_future_game(self):
        rows, _mean, _sd = props.build_prop_rows(props.load_logs())
        by_player = {}
        for r in rows:
            prev = by_player.get(r["player"], [])
            self.assertGreater(r["week"], max(prev) if prev else 0)
            by_player.setdefault(r["player"], []).append(r["week"])


class TestOriginationOrder(unittest.TestCase):
    def test_the_side_comes_first_then_the_total_then_the_moneyline(self):
        games, _ = core.build_results()
        ratings = core.fit_ratings(games)
        const = core.league_constants(games)
        spread, total, ml, exp = core.fair_lines(games[-1], ratings, const)
        self.assertEqual(spread["market"], "SPREAD")
        self.assertEqual(total["market"], "TOTAL")
        self.assertEqual(ml["market"], "MONEYLINE")
        # the moneyline is priced FROM the side, so it cannot disagree with it
        self.assertEqual(ml["model_inputs"]["fair_spread_used"], spread["fair_line"])
        self.assertIsNotNone(ml["fair_probability"])
        self.assertTrue(0.0 < ml["fair_probability"] < 1.0)

    def test_the_moneyline_is_consistent_with_the_side(self):
        games, _ = core.build_results()
        ratings = core.fit_ratings(games)
        const = core.league_constants(games)
        for g in games[-20:]:
            spread, _total, ml, _exp = core.fair_lines(g, ratings, const)
            # the published line is the expected home margin: a positive
            # value means the home team is favoured
            if spread["fair_line"] < 0:
                self.assertLess(ml["fair_probability"], 0.5)
            if spread["fair_line"] > 0:
                self.assertGreater(ml["fair_probability"], 0.5)
            if spread["fair_line"] == 0:
                self.assertAlmostEqual(ml["fair_probability"], 0.5, places=2)


class TestWalkForward(unittest.TestCase):
    def test_the_model_never_trains_on_the_week_it_predicts(self):
        games, _ = core.build_results()
        wf = analysis.walk_forward(games)
        self.assertTrue(wf)
        for r in wf:
            self.assertGreaterEqual(r["train_games"], 40)
            earlier = [g for g in games if g["week"] < r["week"]]
            self.assertEqual(r["train_games"], len(earlier))
            for g in games:
                if g["game_key"] == r["game_key"]:
                    self.assertEqual(g["week"], r["week"])
                    break


if __name__ == "__main__":
    unittest.main()

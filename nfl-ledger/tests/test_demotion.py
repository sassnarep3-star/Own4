"""Unit tests for the demotion gate, using SYNTHETIC inputs only (no published data is created here)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine'))
import demotion  # noqa: E402


def live(**kw):
    base = {'stage': 'live', 'live_n': 200, 'live_beats': 130, 'placebo_pct_300': 99,
            'drawdown': 0.02, 'missing_snapshot_rate': 0.0, 'unrecorded_depth_rate_out_weeks': 0.0,
            'failed_reviews': 0}
    base.update(kw)
    return base


class PromotionTests(unittest.TestCase):
    def test_no_prices_means_registered(self):
        stage, _ = demotion.promotion({'gates_passed': 10, 'graded_n': 400, 'beats': 260, 'placebo_pct': 99,
                                       'clean_windows': 2, 'snapshot_complete': True, 'has_prices': False})
        self.assertEqual(stage, 'registered')

    def test_all_rules_pass_means_live(self):
        stage, _ = demotion.promotion({'gates_passed': 10, 'graded_n': 400, 'beats': 260, 'placebo_pct': 99,
                                       'clean_windows': 2, 'snapshot_complete': True, 'has_prices': True})
        self.assertEqual(stage, 'live')

    def test_staking_fields_cannot_promote(self):
        # a huge bankroll gain with a failing signal must stay paper
        stage, reasons = demotion.promotion({'gates_passed': 10, 'graded_n': 400, 'beats': 200, 'placebo_pct': 40,
                                             'clean_windows': 2, 'snapshot_complete': True, 'has_prices': True,
                                             'roi': 0.9, 'drawdown': -0.5})
        self.assertEqual(stage, 'paper')
        self.assertTrue(any('P3' in r or 'P4' in r for r in reasons))

    def test_small_sample_stays_paper(self):
        stage, reasons = demotion.promotion({'gates_passed': 10, 'graded_n': 120, 'beats': 80, 'placebo_pct': 99,
                                             'clean_windows': 2, 'snapshot_complete': True, 'has_prices': True})
        self.assertEqual(stage, 'paper')
        self.assertTrue(any('P2' in r for r in reasons))


class DemotionTests(unittest.TestCase):
    def test_healthy_live_strategy_stays_live(self):
        self.assertEqual(demotion.demotion(live()), ('live', []))

    def test_signal_failure_demotes_even_with_great_staking(self):
        stage, hits = demotion.demotion(live(live_beats=60, live_n=200, drawdown=-0.4, placebo_pct_300=20))
        self.assertEqual(stage, 'paper')
        self.assertIn('D1', hits)

    def test_d2_placebo(self):
        _, hits = demotion.demotion(live(live_n=320, placebo_pct_300=80))
        self.assertIn('D2', hits)

    def test_drawdown_demotes(self):
        _, hits = demotion.demotion(live(drawdown=0.15))
        self.assertIn('D3', hits)

    def test_missing_snapshot_data_demotes(self):
        _, hits = demotion.demotion(live(missing_snapshot_rate=None))
        self.assertIn('D4', hits)

    def test_missing_depth_data_demotes(self):
        _, hits = demotion.demotion(live(unrecorded_depth_rate_out_weeks=0.3))
        self.assertIn('D5', hits)

    def test_two_failed_reviews_demote(self):
        _, hits = demotion.demotion(live(failed_reviews=2))
        self.assertIn('D6', hits)

    def test_paper_strategy_is_not_touched(self):
        self.assertEqual(demotion.demotion(live(stage='paper', drawdown=0.9)), ('paper', []))


class WilsonTests(unittest.TestCase):
    def test_bounds(self):
        lo, hi = demotion.wilson_bounds(50, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)


if __name__ == '__main__':
    unittest.main()

import unittest
from math import isclose
from nba_lab.engine import *
from nba_lab.analysis import load_inputs, run


class PricingTests(unittest.TestCase):
    def test_fair_price_round_trip(self):
        for p in (.1, .25, .5, .75, .99):
            self.assertAlmostEqual(implied_probability(fair_decimal(p)), p)

    def test_vig(self):
        a, b = remove_vig_two_way(1.90909090909, 1.90909090909)
        self.assertAlmostEqual(a + b, 1)
        self.assertAlmostEqual(a, .5)
        self.assertGreater(1/1.90909090909 * 2, 1)

    def test_ev(self):
        self.assertAlmostEqual(ev_per_unit(.5, 2), 0)
        self.assertAlmostEqual(ev_per_unit(.6, 2), .2)
        self.assertAlmostEqual(ev_per_unit(.4, 2), -.2)

    def test_invalid_inputs(self):
        for p in (-.1, 1.1, float('nan')):
            with self.assertRaises(ValueError): probability(p)
        with self.assertRaises(ValueError): fair_decimal(0)
        with self.assertRaises(ValueError): implied_probability(1)

    def test_kelly_cap_and_no_bet(self):
        self.assertEqual(kelly_fraction(.5, 1.9), 0)
        self.assertEqual(kelly_fraction(.9, 2), .01)

    def test_push_and_void_reduce_ticket(self):
        legs = [{'decimal':2,'result':'win'},{'decimal':3,'result':'push'}, {'decimal':4,'result':'void'}]
        self.assertEqual(settle_ticket(legs)['profit'], 1)
        legs[0]['result'] = 'loss'
        self.assertEqual(settle_ticket(legs)['profit'], -1)
        self.assertEqual(settle_ticket([{'decimal':2,'result':'void'}])['result'], 'push')
        with self.assertRaises(ValueError): settle_ticket([])

    def test_settlement(self):
        self.assertEqual(settle_single(100, 99.5, 'over'), 'win')
        self.assertEqual(settle_single(100, 100.5, 'over'), 'loss')
        self.assertEqual(settle_single(100, 100, 'under'), 'push')

    def test_half_lines_never_integer(self):
        for x in (-5, 0, 10, 10.25, 10.75):
            self.assertEqual(half_line(x) % 1, .5)


class StatisticsTests(unittest.TestCase):
    def test_correlation(self):
        self.assertAlmostEqual(pearson([1,2,3], [2,4,6]), 1)
        self.assertAlmostEqual(pearson([1,2,3], [6,4,2]), -1)
        self.assertIsNone(pearson([1,1,1], [1,2,3]))
        self.assertIsNone(pearson([1,2], [1,2]))

    def test_binary_joint_not_product(self):
        r = binary_correlation([1,1,0,0], [1,1,1,0])
        self.assertEqual(r['p_joint'], .5)
        self.assertEqual(r['independent_joint'], .375)
        self.assertAlmostEqual(r['phi'], pearson([1,1,0,0], [1,1,1,0]))

    def test_scores(self):
        self.assertEqual(brier([1,0], [1,0]), 0)
        self.assertEqual(brier([.5,.5], [1,0]), .25)
        self.assertLess(log_loss([.9,.1], [1,0]), log_loss([.6,.4], [1,0]))
        self.assertEqual(mae([1,2], [2,4]), 1.5)

    def test_wilson(self):
        lo, hi = wilson(0, 10)
        self.assertEqual(lo, 0)
        self.assertGreater(hi, 0)
        self.assertAlmostEqual(wilson(10,10)[1], 1)

    def test_holm(self):
        self.assertEqual(holm_adjust([.01,.02,.03]), [.03,.04,.04])

    def test_short_cluster_ci_suppressed(self):
        self.assertIsNone(date_cluster_bootstrap([{'date':'a','x':1}], 'x', 100, 1))

    def test_gates_fail_closed(self):
        gates = [{'id':'a','status':'pass'},{'id':'b','status':'unverified'}]
        self.assertFalse(release_gates(gates)['qualified'])
        gates[1]['status'] = 'fail'
        self.assertFalse(release_gates(gates)['qualified'])
        gates[1]['status'] = 'pass'
        self.assertTrue(release_gates(gates)['qualified'])
        with self.assertRaises(ValueError): release_gates([])


class DataAndLeakageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()
        cls.games, cls.players = load_inputs()

    def test_no_prediction_uses_same_or_future_date(self):
        for row in self.result['predictions']:
            inputs = [g for g in self.games if g['date'] < row['date'] and g['team1'] in (row['team1'],row['team2'])]
            # Stored prior-game counts refer to the specific team, not the whole league.
            for team, key in ((row['team1'],'prior_games1'),(row['team2'],'prior_games2')):
                self.assertEqual(row[key], sum(g['team1'] == team or g['team2'] == team for g in self.games if g['date'] < row['date']))

    def test_outcomes_not_overwritten_by_predictions(self):
        for row in self.result['predictions']:
            actual = next(g for g in self.games if g['game_id'] == row['game_id'])
            self.assertEqual(row['margin'], actual['margin'])
            self.assertEqual(row['total'], actual['total'])
        self.assertGreater(self.result['test']['margin_mae'], 1)

    def test_splits(self):
        self.assertEqual(self.result['sample']['train_games'], 23)
        self.assertEqual(self.result['sample']['validation_games'], 15)
        self.assertEqual(self.result['sample']['test_games'], 24)
        self.assertEqual(len(self.result['sample']['dates']), 8)

    def test_no_invented_market_results(self):
        self.assertEqual(self.result['official_price_rows'], 0)
        self.assertEqual(self.result['rewards_awarded'], 0)
        for s in self.result['strategies']:
            self.assertIsNone(s['measured_roi'])
            self.assertFalse(s['release']['qualified'])
        for p in self.result['predictions']:
            self.assertIsNone(p['book_decimal'])
            self.assertIsNone(p['estimated_price_edge'])

    def test_source_on_every_input(self):
        for r in self.games + self.players:
            self.assertTrue(r['source_url'].startswith('https://www.nba.com/'))
        self.assertEqual(len(self.result['source_rows']), 100)

    def test_deterministic(self):
        self.assertEqual(run(), self.result)

    def test_no_test_tuning(self):
        before = run()
        changed = [dict(g) for g in self.games]
        for g in changed:
            if g['date'] > '2025-01-05':
                g['score1'], g['score2'] = g['score2'], g['score1']
        # Independently reconstruct only the training state; test labels cannot alter it.
        from statistics import mean
        train = [g for g in changed if g['date'] <= '2025-01-03']
        m = RollingStrength(mean(s for g in train for s in (g['score1'],g['score2'])), 5)
        for g in train:m.update(g['team1'],g['score1'],g['team2'],g['score2'])
        original_train = [g for g in self.games if g['date'] <= '2025-01-03']
        m2 = RollingStrength(mean(s for g in original_train for s in (g['score1'],g['score2'])), 5)
        for g in original_train:m2.update(g['team1'],g['score1'],g['team2'],g['score2'])
        self.assertEqual(dict(m.stats),dict(m2.stats))
        self.assertEqual(before['logistic'], self.result['logistic'])

if __name__ == '__main__':unittest.main()

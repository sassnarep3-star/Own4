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

    def test_reliability_bins(self):
        rows = reliability_bins([.1, .2, .8], [0, 1, 1])
        self.assertEqual([r['n'] for r in rows], [2, 1])
        self.assertAlmostEqual(rows[0]['mean_probability'], .15)
        self.assertAlmostEqual(rows[0]['observed_rate'], .5)
        self.assertEqual(rows[1]['bin'], '[0.75, 1]')
        with self.assertRaises(ValueError): reliability_bins([.2], [2])

    def test_same_game_probabilities_ignore_observed_total(self):
        pregame = {'team1':'A','team2':'B','p1':.7,'predicted_margin':6.0,
                   'predicted_total':220.25,'total_line':220.5}
        residuals = [{'margin':3,'total':2},{'margin':-4,'total':-8},
                     {'margin':7,'total':1},{'margin':-2,'total':5}]
        high_final = same_game_probabilities({**pregame,'total':999}, residuals)
        low_final = same_game_probabilities({**pregame,'total':0}, residuals)
        self.assertEqual(high_final, low_final)
        self.assertNotIn('sgp_hit', high_final)
        self.assertNotIn('over_hit', high_final)
        self.assertEqual(high_final['residual_pairs'], 4)

    def test_same_game_shifts_margin_and_total_residuals(self):
        base = {'team1':'A','team2':'B','p1':.7,
                'predicted_total':100.0,'total_line':100.5}
        residuals = [{'margin':-10,'total':1},{'margin':10,'total':1}]
        large = same_game_probabilities({**base,'predicted_margin':20}, residuals)
        small = same_game_probabilities({**base,'predicted_margin':0}, residuals)
        self.assertAlmostEqual(large['p_sgp'], 2.5/3)
        self.assertAlmostEqual(small['p_sgp'], 1.5/3)
        self.assertEqual(large['p_over'], small['p_over'])


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

    def test_held_out_total_mutation_cannot_change_pregame_probabilities(self):
        from copy import deepcopy
        changed = deepcopy(self.games)
        last_date = self.result['protocol']['test_dates'][-1]
        for game in changed:
            if game['date'] == last_date:
                game['score1'] += 50
                game['score2'] += 50
                game['total'] += 100  # Margin and winner stay fixed; only total outcome changes.
        mutated = run(write=False, games_override=changed, players_override=self.players)
        original_rows = {r['game_id']:r for r in self.result['predictions'] if r['date'] == last_date}
        mutated_rows = {r['game_id']:r for r in mutated['predictions'] if r['date'] == last_date}
        self.assertEqual(original_rows.keys(), mutated_rows.keys())
        for game_id, original in original_rows.items():
            changed_row = mutated_rows[game_id]
            for key in ('p1','predicted_total','total_line','p_over','p_sgp','p_sgp_independent'):
                self.assertEqual(original[key], changed_row[key], (game_id,key))
        self.assertTrue(any(original_rows[game_id]['over_hit'] != mutated_rows[game_id]['over_hit']
                            for game_id in original_rows))

    def test_expanding_residuals_use_only_earlier_dates(self):
        residuals = self.result['training_residuals']
        self.assertEqual(len(residuals), 15)
        self.assertEqual(self.result['sgp']['training_pairs'], 15)
        self.assertEqual(self.result['sgp']['training_dates'], 2)
        for row in residuals:
            self.assertTrue(row['prior_dates'])
            self.assertLess(max(row['prior_dates']), row['date'])
            self.assertGreater(row['date'], '2025-01-01')

    def test_same_game_interval_remains_suppressed(self):
        self.assertEqual(self.result['sgp']['dates'], 3)
        self.assertIsNone(self.result['sgp']['brier_difference_ci'])
        self.assertEqual(self.result['revision']['id'], 'Q-LEAK-2026-11-05')

    def test_prop_diagnostic_rows_fail_closed(self):
        rows = self.result['prop_predictions']
        self.assertEqual(len(rows), 54)
        self.assertTrue(all(r['book_decimal'] is None and r['roi'] is None for r in rows))
        for prop in self.result['props']:
            own = [r for r in rows if r['prop_id'] == prop['id']]
            self.assertEqual(sum(r['actual_hit'] for r in own), prop['test_hits'])
            self.assertIsNone(prop['test_metrics']['brier_difference_ci'])
            self.assertTrue(all(r['forecast_probability'] == prop['forecast_probability'] for r in own))

    def test_leaderboards_rank_only_matched_divisions(self):
        for key, score in (('leaderboard','brier'),('point_leaderboard','mae')):
            rows = self.result[key]
            divisions = {r['division'] for r in rows}
            self.assertGreater(len(divisions), 1)
            for division in divisions:
                own = [r for r in rows if r['division'] == division]
                self.assertEqual([r[score] for r in own], sorted(r[score] for r in own))
                self.assertEqual(len({r['n'] for r in own}), 1)
                for row in own:
                    expected = 1 + sum(other[score] < row[score] for other in own)
                    self.assertEqual(row['diagnostic_rank'], expected)
        pra = [r for r in self.result['leaderboard'] if r['division'] == 'Player cohort / PRA']
        self.assertEqual({r['diagnostic_rank'] for r in pra}, {1})

if __name__ == '__main__':unittest.main()

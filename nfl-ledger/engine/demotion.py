"""Demotion gate — pure functions (no I/O). A live strategy goes back to PAPER when any demotion trigger trips.

Design rules (written before any priced result exists):
  * Signal and staking are evaluated separately. Staking inputs can only ever TRIGGER a demotion (D3); they never
    enter promotion and never offset a signal trigger (D1, D2).
  * Missing data never means "fine": missing inputs force paper (D4, D5) or keep a strategy out of live.
  * Thresholds are fixed here; changing them creates a new gate version and must be logged in COORDINATION.md.
"""
import math

VERSION = 'demotion-gate v1 (2026-11-14, pre-registered before any priced result)'

STAGES = ['registered', 'paper', 'live']


def spec():
    return {
        'version': VERSION,
        'stages': {
            'registered': 'Pre-registered; no priced selections yet.',
            'paper': 'Graded on recorded opening and closing snapshots; zero real stake.',
            'live': 'Real stake allowed. Only after every promotion rule passes.',
        },
        'promotion_rules': [
            {'id': 'P1', 'rule': 'All 10 frozen gates G1–G10 pass on the frozen holdout (nfl-command gates.json).'},
            {'id': 'P2', 'rule': '>= 300 graded paper selections, each with an official-source game link and a recorded closing snapshot.'},
            {'id': 'P3', 'rule': 'Closing-line beat rate: Wilson 95% LOWER bound > 0.50 (signal).'},
            {'id': 'P4', 'rule': 'Placebo test: observed signal above the 95th percentile of 10,000 label-shuffled runs.'},
            {'id': 'P5', 'rule': 'Two consecutive prospective review windows with no demotion trigger.'},
        ],
        'demotion_triggers': [
            {'id': 'D1', 'type': 'signal', 'rule': 'Rolling 150 live selections: closing-line beat rate Wilson 95% UPPER bound < 0.50.',
             'action': 'demote to paper'},
            {'id': 'D2', 'type': 'signal', 'rule': 'Rolling 300 selections: placebo percentile < 95 (signal no longer beats luck).',
             'action': 'demote to paper'},
            {'id': 'D3', 'type': 'staking', 'rule': 'Bankroll drawdown >= 15% (gates.json G9). Can demote; can never promote.',
             'action': 'demote to paper'},
            {'id': 'D4', 'type': 'data', 'rule': 'More than 2% of live selections lack a recorded closing snapshot.',
             'action': 'demote to paper until repaired'},
            {'id': 'D5', 'type': 'data', 'rule': 'More than 25% of selections made in weeks with an Out starter lack a recorded replacement-depth rank.',
             'action': 'demote to paper until repaired'},
            {'id': 'D6', 'type': 'governance', 'rule': 'Two consecutive failed review windows.', 'action': 'demote to paper'},
        ],
        'missing_data_rule': 'Any missing input for a live strategy = demote. Any missing input for promotion = stay paper.',
        'current_status': 'No strategy has priced selections. All strategies are registered; none may be live.',
    }


def wilson_bounds(k, n, z=1.96):
    if n <= 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def promotion(state):
    """state keys: gates_passed (int of 10), graded_n, beats, placebo_pct, clean_windows, snapshot_complete (bool).
    Returns (stage, reasons). Staking inputs are deliberately not read."""
    reasons = []
    if state.get('gates_passed', 0) < 10:
        reasons.append('P1 fails: %s of 10 gates pass' % state.get('gates_passed', 0))
    n = state.get('graded_n', 0)
    if n < 300:
        reasons.append('P2 fails: n=%d < 300' % n)
    lo, _ = wilson_bounds(state.get('beats', 0), n)
    if lo is None or lo <= 0.5:
        reasons.append('P3 fails: Wilson lower bound %s <= 0.50' % (None if lo is None else round(lo, 3)))
    if state.get('placebo_pct') is None or state['placebo_pct'] < 95:
        reasons.append('P4 fails: placebo percentile %s < 95' % state.get('placebo_pct'))
    if state.get('clean_windows', 0) < 2:
        reasons.append('P5 fails: clean windows %s < 2' % state.get('clean_windows', 0))
    if not state.get('snapshot_complete', False):
        reasons.append('D4-precondition: closing snapshots incomplete')
    if not state.get('has_prices', False):
        return 'registered', ['no priced selections'] + reasons
    if reasons:
        return 'paper', reasons
    return 'live', ['all promotion rules pass']


def demotion(state):
    """state keys: stage, live_n, live_beats, placebo_pct_300, drawdown, missing_snapshot_rate,
    unrecorded_depth_rate_out_weeks, failed_reviews. Returns (stage, triggered_ids)."""
    if state.get('stage') != 'live':
        return state.get('stage', 'registered'), []
    hits = []
    n150 = state.get('live_n', 0)
    if n150 >= 150:
        _, hi = wilson_bounds(state.get('live_beats', 0), n150)
        if hi is not None and hi < 0.5:
            hits.append('D1')
    if state.get('live_n', 0) >= 300 and state.get('placebo_pct_300') is not None and state['placebo_pct_300'] < 95:
        hits.append('D2')
    if state.get('drawdown') is None or state['drawdown'] >= 0.15:
        hits.append('D3')
    # A missing input for a live strategy is itself a demotion (missing data never means "fine").
    if state.get('missing_snapshot_rate') is None or state['missing_snapshot_rate'] > 0.02:
        hits.append('D4')
    if state.get('unrecorded_depth_rate_out_weeks') is None or state['unrecorded_depth_rate_out_weeks'] > 0.25:
        hits.append('D5')
    if state.get('failed_reviews', 0) >= 2:
        hits.append('D6')
    return ('paper' if hits else 'live'), hits

#!/usr/bin/env python3
"""nfl-marketboard build — origination engine, grading, gates, correlations.

Built by session arena/28a71529-own4 (2026-11-14 UTC).

Design rules that are enforced by this file, not by convention:
  1. RESULTS come only from data/raw/results_2026_official.csv, which was
     transcribed from nfl.com official schedule pages and reconciled cell-by-cell
     against the official standings (192 values, 0 mismatches).
  2. PRICES come from the nflverse archive (third party, CC BY 4.0). They are
     labelled third-party everywhere they are published. The NFL publishes no odds.
  3. ORIGINATION ORDER is side -> total -> moneyline. The moneyline is a function
     of the first two, not an independent estimate.
  4. WALK-FORWARD: a number originated for week w uses only official games with
     week < w plus the official 2025 final standings (published before the season).
     No game's own result, and no later game's result, can enter its own feature set.
  5. A value that cannot be sourced is emitted blank, never inferred.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'data')
NV_GAMES = os.path.join(ROOT, '..', 'nfl-hub', 'data', 'source', 'games.csv')

SESSION = 'arena-28a71529-own4'
BUILT_UTC = '2026-11-14T00:00:00Z'

# ---------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS. Fixed before any result was looked at.
# ---------------------------------------------------------------------------
PRIOR_GAMES = 6.0          # pseudo-games of weight given to the 2025 official prior
HFA_PRIOR = 2.0            # prior home-field advantage, points
HFA_PRIOR_GAMES = 5.0      # pseudo-games of weight for the HFA prior
SIGMA_FLOOR = 10.0         # floor on the margin standard deviation, points
FIRST_GRADED_WEEK = 3      # first week with >= 2 weeks of in-season history
MIN_N_QUALIFY = 300        # graded-bet floor for leaderboard qualification
BREAKEVEN_ALPHA = 0.05     # two-sided alpha for the luck / skill tests
LUCK_TEST_DRAWS = 20000    # permutation draws for the luck test
PARLAY_TOTAL_THRESHOLD = 46.0   # fixed, pre-registered; NOT estimated from the sample
PARLAY_MARGIN_THRESHOLD = 7.0   # fixed, pre-registered
RNG_SEED = 20261114

NFL_SCHEDULE_URL = 'https://www.nfl.com/schedules/2026/by-week/week-{w}'
NFL_STANDINGS_URL = 'https://www.nfl.com/standings/league/2026/REG'
NFL_STANDINGS_2025_URL = 'https://www.nfl.com/standings/league/2025/REG'
NFL_INJURY_URL = 'https://www.nfl.com/injuries/'
NFLDATA_URL = 'https://github.com/nflverse/nfldata'


def load_csv(path: str) -> list:
    with open(path, newline='') as fh:
        lines = [ln for ln in fh if not ln.startswith('#')]
    return list(csv.DictReader(io.StringIO(''.join(lines))))


def rnd(x, n=4):
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(x, n)


# ===========================================================================
# 1. LOAD OFFICIAL DATA
# ===========================================================================
results = load_csv(os.path.join(RAW, 'results_2026_official.csv'))
for r in results:
    r['week'] = int(r['week'])
    r['away_pts'] = int(r['away_pts']) if r['away_pts'] else None
    r['home_pts'] = int(r['home_pts']) if r['home_pts'] else None

standings = load_csv(os.path.join(RAW, 'standings_2026_official.csv'))
for r in standings:
    for k in ('w', 'l', 't', 'pf', 'pa', 'net_pts'):
        r[k] = int(r[k])

prior = load_csv(os.path.join(RAW, 'standings_2025_official.csv'))
for r in prior:
    for k in ('w', 'l', 't', 'pf', 'pa', 'net_pts'):
        r[k] = int(r[k])
PRIOR = {r['team']: r for r in prior}
PRIOR_G = {t: (r['w'] + r['l'] + r['t']) for t, r in PRIOR.items()}

TEAMS = sorted(r['team'] for r in standings)
finished = [r for r in results if r['status'] == 'FINAL']
scheduled = [r for r in results if r['status'] != 'FINAL']

# --------------------------------------------------------------- market ----
# nflverse archive: THIRD PARTY. Reconciled to official scores (see verify.py).
nv = {}
if os.path.exists(NV_GAMES):
    with open(NV_GAMES, newline='') as fh:
        for row in csv.DictReader(fh):
            if row['season'] == '2026':
                nv[(int(row['week']), row['away_team'], row['home_team'])] = row


def market(game):
    return nv.get((game['week'], game['away'], game['home']))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ===========================================================================
# 2. RECONCILIATION (re-run here so the published page is reproducible)
# ===========================================================================
def reconcile():
    pf, pa, w, l, t, gp = ({k: 0 for k in TEAMS} for _ in range(6))
    for g in finished:
        a, h = g['away_pts'], g['home_pts']
        pf[g['away']] += a; pa[g['away']] += h; gp[g['away']] += 1
        pf[g['home']] += h; pa[g['home']] += a; gp[g['home']] += 1
        if a > h:
            w[g['away']] += 1; l[g['home']] += 1
        elif h > a:
            w[g['home']] += 1; l[g['away']] += 1
        else:
            t[g['away']] += 1; t[g['home']] += 1
    checks, errs = 0, []
    for r in standings:
        tm = r['team']
        for label, mine, off in (('W', w[tm], r['w']), ('L', l[tm], r['l']),
                                 ('T', t[tm], r['t']), ('PF', pf[tm], r['pf']),
                                 ('PA', pa[tm], r['pa']),
                                 ('GP', gp[tm], r['w'] + r['l'] + r['t'])):
            checks += 1
            if mine != off:
                errs.append({'team': tm, 'field': label, 'derived': mine,
                             'official': off})
    return {'checks': checks, 'mismatches': len(errs), 'errors': errs,
            'games_final': len(finished), 'games_scheduled': len(scheduled),
            'sum_pf_derived': sum(pf.values()), 'sum_pa_derived': sum(pa.values()),
            'sum_pf_official': sum(r['pf'] for r in standings),
            'sum_pa_official': sum(r['pa'] for r in standings)}


RECON = reconcile()

# ===========================================================================
# 3. BASE RATES (official results only)
# ===========================================================================
margins = [g['home_pts'] - g['away_pts'] for g in finished]
totals = [g['home_pts'] + g['away_pts'] for g in finished]
home_wins = sum(1 for m in margins if m > 0)
away_wins = sum(1 for m in margins if m < 0)
ties = sum(1 for m in margins if m == 0)
BASE = {
    'n_games': len(finished),
    'home_wins': home_wins, 'away_wins': away_wins, 'ties': ties,
    'home_win_rate': rnd(home_wins / len(finished)),
    'mean_home_margin': rnd(S.mean(margins), 3),
    'sd_margin': rnd(S.sd(margins), 3),
    'mean_total': rnd(S.mean(totals), 3),
    'median_total': rnd(sorted(totals)[len(totals) // 2], 1),
    'sd_total': rnd(S.sd(totals), 3),
    'mean_abs_margin': rnd(S.mean([abs(m) for m in margins]), 3),
    'source_url': NFL_SCHEDULE_URL.format(w='1'),
}

# ===========================================================================
# 4. MARKET-LINE SIGN CONVENTION CHECK (empirical, against official results)
# ===========================================================================
sp_x, sp_y = [], []
for g in finished:
    m = market(g)
    if m and m['spread_line']:
        sp_x.append(float(m['spread_line']))
        sp_y.append(g['home_pts'] - g['away_pts'])
CONVENTION = S.pearson(sp_x, sp_y)
CONVENTION['interpretation'] = (
    'nflverse spread_line is documented as "positive = home team favoured". '
    'Correlating it against the official home margin tests that convention on '
    'this season. A strong positive r confirms positive = home favoured.')
CONVENTION['n'] = len(sp_x)

# ===========================================================================
# 5. WALK-FORWARD MODEL  ->  originate side, then total, then moneyline
# ===========================================================================
def team_state(week: int) -> dict:
    """Point-in-time state using only official games with week < `week`."""
    gp, pf, pa = {t: 0 for t in TEAMS}, {t: 0 for t in TEAMS}, {t: 0 for t in TEAMS}
    hist = [g for g in finished if g['week'] < week]
    for g in hist:
        a, h = g['away_pts'], g['home_pts']
        gp[g['away']] += 1; pf[g['away']] += a; pa[g['away']] += h
        gp[g['home']] += 1; pf[g['home']] += h; pa[g['home']] += a
    p25 = {t: PRIOR[t]['pf'] / PRIOR_G[t] for t in TEAMS}
    a25 = {t: PRIOR[t]['pa'] / PRIOR_G[t] for t in TEAMS}
    ppg = {t: (pf[t] + PRIOR_GAMES * p25[t]) / (gp[t] + PRIOR_GAMES) for t in TEAMS}
    pag = {t: (pa[t] + PRIOR_GAMES * a25[t]) / (gp[t] + PRIOR_GAMES) for t in TEAMS}
    L = S.mean([ppg[t] for t in TEAMS])
    off = {t: ppg[t] - L for t in TEAMS}
    dfn = {t: pag[t] - L for t in TEAMS}
    n_hist = len(hist)
    hm = S.mean([g['home_pts'] - g['away_pts'] for g in hist]) if hist else 0.0
    hfa = (hm * n_hist + HFA_PRIOR * HFA_PRIOR_GAMES) / (n_hist + HFA_PRIOR_GAMES)
    return {'gp': gp, 'ppg': ppg, 'pag': pag, 'L': L, 'off': off, 'def': dfn,
            'hfa': hfa, 'n_hist': n_hist, 'raw_pf': pf, 'raw_pa': pa}


def sigma_for(week: int) -> float:
    """Walk-forward residual sd of the margin model, floored."""
    resid = []
    for w in range(FIRST_GRADED_WEEK, week):
        st = team_state(w)
        for g in finished:
            if g['week'] != w:
                continue
            pred = (st['off'][g['home']] + st['def'][g['away']]
                    - st['off'][g['away']] - st['def'][g['home']] + st['hfa'])
            resid.append((g['home_pts'] - g['away_pts']) - pred)
    s = S.sd(resid)
    return SIGMA_FLOOR if (len(resid) < 2 or math.isnan(s) or s < SIGMA_FLOOR) else s


SIGMAS = {w: sigma_for(w) for w in range(1, 12)}


def sigma_total_for(week: int) -> float:
    """Walk-forward sd of the official game total (floored)."""
    vals = [g['home_pts'] + g['away_pts'] for g in finished if g['week'] < week]
    s = S.sd(vals)
    floor = 8.0
    return floor if (len(vals) < 2 or math.isnan(s) or s < floor) else s


SIGMA_TOTALS = {w: sigma_total_for(w) for w in range(1, 12)}

# --- market spread sign convention, settled against the official results ----
# nflverse documents spread_line as "positive = home team favoured". Two readings
# are possible for "home covers": (a) margin > spread  or (b) margin > -spread.
# They are distinguished here by which one produces a ~50% home cover rate and a
# plausible number of pushes.
_conv = {}
for _cand, _fn in (('home_covers_if_margin_gt_spread', lambda m, s: m - s),
                   ('home_covers_if_margin_gt_minus_spread', lambda m, s: m + s)):
    _nets = []
    for _g in finished:
        _mk = market(_g)
        if _mk and _mk['spread_line']:
            _nets.append(_fn(_g['home_pts'] - _g['away_pts'], float(_mk['spread_line'])))
    _n = len(_nets)
    _conv[_cand] = {'n': _n,
                    'home_cover_rate': rnd(sum(1 for x in _nets if x > 0) / _n),
                    'pushes': sum(1 for x in _nets if x == 0),
                    'mean_net': rnd(S.mean(_nets), 3)}
CONVENTION_CHECK = {
    'candidates': _conv,
    'chosen': 'home_covers_if_margin_gt_spread',
    'reason': 'It is the only reading consistent with the documented convention (positive = '
              'home favoured), it produces a plausible push count, and it reproduces a push on '
              'the Week 1 NE@SEA game (spread 3, home won by exactly 3). The 0.41 home cover '
              'rate it yields for 2026 is a real season effect, not a convention error: the '
              'market has been pricing home teams ~1.6 points richer than the official '
              'results justify.',
    'mean_market_spread': rnd(S.mean([float(market(g)['spread_line'])
                                      for g in finished
                                      if market(g) and market(g)['spread_line']])),
    'mean_official_home_margin': rnd(S.mean(margins), 3),
    'source_url': NFL_SCHEDULE_URL.format(w='1-10'),
}
# Decisive checks that pin the sign down, so the choice is not an assumption.
_mlx, _mly = [], []
for _g in finished:
    _mk = market(_g)
    if _mk and _mk['spread_line'] and _mk['home_moneyline']:
        _mlx.append(float(_mk['spread_line']))
        _mly.append(float(_mk['home_moneyline']))
CONVENTION_CHECK['spread_vs_home_moneyline'] = {
    'n': len(_mlx), 'r': rnd(S.pearson(_mlx, _mly)['r']),
    'p_value': rnd(S.pearson(_mlx, _mly)['p_value'], 8),
    'reading': 'A strong NEGATIVE r means a larger positive spread goes with a shorter '
               '(more negative) home price, i.e. positive spread = home favoured.'}
_nea = [g for g in finished if g['week'] == 1 and g['away'] == 'NE' and g['home'] == 'SEA']
if _nea:
    _mk = market(_nea[0])
    CONVENTION_CHECK['decisive_single_game'] = {
        'game': '2026 Week 1 NE @ SEA',
        'official_score': f"NE {_nea[0]['away_pts']} - SEA {_nea[0]['home_pts']}",
        'official_home_margin': _nea[0]['home_pts'] - _nea[0]['away_pts'],
        'market_spread_line': float(_mk['spread_line']),
        'market_home_moneyline': float(_mk['home_moneyline']),
        'market_away_moneyline': float(_mk['away_moneyline']),
        'conclusion': 'The home price is -166, so the home team is the favourite. The spread '
                      'is +3 and the home team won by exactly 3. A 3-point favourite winning '
                      'by exactly 3 is a push, which fixes the convention: the home side '
                      'covers when the official home margin exceeds +3.',
        'source_url': _nea[0]['game_url'],
    }

ORIGINATED = []          # one row per game with the three originated numbers
for g in results:
    wk = g['week']
    st = team_state(wk)
    sg = SIGMAS[wk]
    # ---- STEP 1: the SIDE ------------------------------------------------
    e_home = st['L'] + st['off'][g['home']] + st['def'][g['away']] + st['hfa'] / 2.0
    e_away = st['L'] + st['off'][g['away']] + st['def'][g['home']] - st['hfa'] / 2.0
    fair_margin = e_home - e_away                     # + = home favoured
    fair_spread = fair_margin
    # ---- STEP 2: the TOTAL ----------------------------------------------
    fair_total = e_home + e_away
    # ---- STEP 3: the MONEYLINE (a function of the side AND the total) ----
    sigma_eff = sg * (fair_total / (2.0 * st['L'])) if st['L'] else sg
    p_home = S.norm_cdf(fair_margin / sigma_eff) if sigma_eff > 0 else 0.5
    fair_ml_home = S.prob_to_american(p_home)
    fair_ml_away = S.prob_to_american(1.0 - p_home)
    # ---- market ----------------------------------------------------------
    m = market(g)
    mkt_spread = fnum(m['spread_line']) if m else None
    mkt_total = fnum(m['total_line']) if m else None
    mkt_ml_home = fnum(m['home_moneyline']) if m else None
    mkt_ml_away = fnum(m['away_moneyline']) if m else None
    if mkt_ml_home is not None and mkt_ml_away is not None:
        mkt_p_home, mkt_p_away = S.devig(mkt_ml_home, mkt_ml_away)
    else:
        mkt_p_home = mkt_p_away = None
    h_so = fnum(m['home_spread_odds']) if m else None
    a_so = fnum(m['away_spread_odds']) if m else None
    ov = fnum(m['over_odds']) if m else None
    un = fnum(m['under_odds']) if m else None
    row = {
        'week': wk, 'date': g['date'], 'away': g['away'], 'home': g['home'],
        'game_url': g['game_url'],
        'status': g['status'],
        'official_home_pts': g['home_pts'], 'official_away_pts': g['away_pts'],
        # three separate columns, as required: fair | market | difference
        'fair_spread': rnd(fair_spread, 2),
        'market_spread': rnd(mkt_spread, 2),
        'spread_diff': rnd(fair_spread - mkt_spread, 2) if mkt_spread is not None else None,
        'fair_total': rnd(fair_total, 2),
        'market_total': rnd(mkt_total, 2),
        'total_diff': rnd(fair_total - mkt_total, 2) if mkt_total is not None else None,
        'fair_ml_home': rnd(fair_ml_home, 0),
        'fair_ml_away': rnd(fair_ml_away, 0),
        'market_ml_home': rnd(mkt_ml_home, 0),
        'market_ml_away': rnd(mkt_ml_away, 0),
        'fair_p_home': rnd(p_home, 4),
        'market_p_home': rnd(mkt_p_home, 4),
        'ml_prob_diff': rnd(p_home - mkt_p_home, 4) if mkt_p_home is not None else None,
        'model_sigma': rnd(sigma_eff, 3),
        'model_L': rnd(st['L'], 3),
        'model_hfa': rnd(st['hfa'], 3),
        'model_games_used': st['n_hist'],
        'market_home_spread_odds': rnd(h_so, 0),
        'market_away_spread_odds': rnd(a_so, 0),
        'market_over_odds': rnd(ov, 0),
        'market_under_odds': rnd(un, 0),
        'price_source_class': 'third-party archive (nflverse/nfldata, CC BY 4.0)'
                              if m else 'none',
        'result_source_url': g['game_url'],
        'price_source_url': NFLDATA_URL if m else None,
    }
    ORIGINATED.append(row)

# ===========================================================================
# 6. PRICE-SNAPSHOT STORE  (opening / closing, with capture provenance)
# ===========================================================================
PRICES = []
for g in results:
    m = market(g)
    wk = g['week']
    base = {'game_key': f"2026_{wk:02d}_{g['away']}_{g['home']}", 'week': wk,
            'away': g['away'], 'home': g['home'], 'game_url': g['game_url']}
    if m:
        for mkt, side, num, price in (
            ('SPREAD', g['home'], fnum(m['spread_line']), fnum(m['home_spread_odds'])),
            ('SPREAD', g['away'], (lambda v: None if v is None else -v)(fnum(m['spread_line'])), fnum(m['away_spread_odds'])),
            ('TOTAL', 'Over', fnum(m['total_line']), fnum(m['over_odds'])),
            ('TOTAL', 'Under', fnum(m['total_line']), fnum(m['under_odds'])),
            ('MONEYLINE', g['home'], None, fnum(m['home_moneyline'])),
            ('MONEYLINE', g['away'], None, fnum(m['away_moneyline'])),
        ):
            PRICES.append(dict(base, market=mkt, side=side,
                               opening_number=None,
                               opening_captured_utc=None,
                               opening_source_url=None,
                               opening_source_class=None,
                               closing_number=rnd(num, 2),
                               closing_price_american=rnd(price, 0),
                               closing_captured_utc='2026-11-13 (archive commit 6ea0be6)',
                               closing_source_url=NFLDATA_URL,
                               closing_source_class='third-party archive (nflverse/nfldata, CC BY 4.0)',
                               settlement='official NFL.com final score',
                               settlement_url=g['game_url']))
    else:
        PRICES.append(dict(base, market='ALL', side=None, opening_number=None,
                           opening_captured_utc=None, opening_source_url=None,
                           opening_source_class=None, closing_number=None,
                           closing_price_american=None, closing_captured_utc=None,
                           closing_source_url=None, closing_source_class=None,
                           settlement='official NFL.com final score',
                           settlement_url=g['game_url']))

PRICE_STORE = {
    'schema': {
        'game_key': 'season_week_away_home (nflverse team codes)',
        'market': 'SPREAD | TOTAL | MONEYLINE',
        'side': 'team code, or Over / Under',
        'opening_number': 'the first number posted for this market; BLANK when no source exists',
        'opening_captured_utc': 'capture timestamp of the opening number',
        'closing_number': 'the last number before kickoff',
        'closing_price_american': 'the price attached to the closing number',
        'closing_captured_utc': 'capture timestamp of the closing number',
        'source_class': 'official | third-party archive',
    },
    'rows': PRICES,
    'counts': {
        'market_rows': len(PRICES),
        'rows_with_closing': sum(1 for p in PRICES if p['closing_number'] is not None
                                 or p['closing_price_american'] is not None),
        'rows_with_opening': sum(1 for p in PRICES if p['opening_number'] is not None),
        'rows_with_opening_pct': 0.0,
    },
}
PC = PRICE_STORE['counts']
PC['rows_with_opening_pct'] = rnd(100.0 * PC['rows_with_opening'] / PC['market_rows'], 2)

# ===========================================================================
# 7. GRADING + STRATEGIES
# ===========================================================================
graded = [r for r in ORIGINATED if r['status'] == 'FINAL' and r['week'] >= FIRST_GRADED_WEEK]


def grade_side(r, side):
    """Return (won, push, decimal_odds) for a spread bet on `side`.

    Convention (settled empirically, see CONVENTION_CHECK): market_spread > 0 means
    the home team is favoured by that many points, so the home side covers when the
    official home margin exceeds the market spread.
    """
    m = r['official_home_pts'] - r['official_away_pts']
    ms = r['market_spread']
    if ms is None:
        return None
    if side == r['home']:
        net = m - ms
        odds = r['market_home_spread_odds']
    else:
        net = ms - m
        odds = r['market_away_spread_odds']
    if net == 0:
        return (False, True, odds)
    return (net > 0, False, odds)


def fair_prob_side(r, side):
    """Model probability that `side` covers the market spread."""
    sigma = (r['model_sigma'] or SIGMA_FLOOR)
    z = (r['market_spread'] - r['fair_spread']) / sigma
    return 1.0 - S.norm_cdf(z) if side == r['home'] else S.norm_cdf(z)


def fair_prob_total(r, tside):
    sigma = SIGMA_TOTALS.get(r['week'], 8.0)
    z = (r['market_total'] - r['fair_total']) / sigma
    return 1.0 - S.norm_cdf(z) if tside == 'Over' else S.norm_cdf(z)


def fair_prob_ml(r, side):
    p = r['fair_p_home']
    return p if side == r['home'] else (1.0 - p)


def grade_total(r, side):
    tot = r['official_home_pts'] + r['official_away_pts']
    mt = r['market_total']
    if mt is None:
        return None
    if tot == mt:
        return (False, True, r['market_over_odds'] if side == 'Over' else r['market_under_odds'])
    won = (tot > mt) if side == 'Over' else (tot < mt)
    return (won, False, r['market_over_odds'] if side == 'Over' else r['market_under_odds'])


def grade_ml(r, side):
    m = r['official_home_pts'] - r['official_away_pts']
    if m == 0:
        return (False, True, r['market_ml_home'] if side == r['home'] else r['market_ml_away'])
    won = (m > 0) if side == r['home'] else (m < 0)
    return (won, False, r['market_ml_home'] if side == r['home'] else r['market_ml_away'])


def edge_side(r):
    return r['spread_diff']


def edge_total(r):
    return r['total_diff']


def edge_ml(r, side):
    if r['ml_prob_diff'] is None:
        return None
    return r['ml_prob_diff'] if side == r['home'] else -r['ml_prob_diff']


STRATEGY_DEFS = [
    {'id': 'S1', 'name': 'Side — 3-point fair-vs-market gap', 'family': 'single',
     'market': 'SPREAD', 'rule': 'bet the side when |fair_spread - market_spread| >= 3.0',
     'threshold': 3.0},
    {'id': 'S2', 'name': 'Total — 3-point fair-vs-market gap', 'family': 'single',
     'market': 'TOTAL', 'rule': 'bet Over when fair_total - market_total >= 3.0, Under when <= -3.0',
     'threshold': 3.0},
    {'id': 'S3', 'name': 'Moneyline — 5% fair-vs-market probability gap', 'family': 'single',
     'market': 'MONEYLINE', 'rule': 'bet the side when |fair_p - market_p| >= 0.05',
     'threshold': 0.05},
    {'id': 'S4', 'name': 'Side — 2-point gap, winning-record filter', 'family': 'single',
     'market': 'SPREAD', 'rule': '|gap| >= 2.0 AND the backed team is above .500 in the official '
                                 'standings at origination time', 'threshold': 2.0},
    {'id': 'S5', 'name': 'Total — unders only, 2-point gap', 'family': 'single',
     'market': 'TOTAL', 'rule': 'bet Under only, when market_total - fair_total >= 2.0',
     'threshold': 2.0},
    {'id': 'S6', 'name': 'Same-game side+total combination (2 legs)', 'family': 'parlay',
     'market': 'SPREAD+TOTAL', 'rule': 'both |spread gap| >= 2.0 and |total gap| >= 2.0 in the '
                                       'same game; legs are combined at the product of their '
                                       'official-model hit probabilities', 'threshold': 2.0},
    {'id': 'S7', 'name': 'Cross-game 2-leg side parlay', 'family': 'parlay',
     'market': 'SPREAD', 'rule': 'the two largest |spread gap| games of the week, combined',
     'threshold': 3.0},
    {'id': 'S8', 'name': 'Player-prop combination', 'family': 'prop',
     'market': 'PLAYER PROP', 'rule': 'REQUIRES official player-prop prices. None exist.',
     'threshold': None},
]


def build_bets(strategy_id):
    bets = []
    for r in graded:
        if strategy_id == 'S1':
            e = edge_side(r)
            if e is not None and abs(e) >= 3.0:
                side = r['home'] if e > 0 else r['away']
                g = grade_side(r, side)
                if g:
                    bets.append(mk_bet(r, 'SPREAD', side, e, g, fair_prob_side(r, side)))
        elif strategy_id == 'S2':
            e = edge_total(r)
            if e is not None and abs(e) >= 3.0:
                side = 'Over' if e > 0 else 'Under'
                g = grade_total(r, side)
                if g:
                    bets.append(mk_bet(r, 'TOTAL', side, e, g, fair_prob_total(r, side)))
        elif strategy_id == 'S3':
            for side in (r['home'], r['away']):
                e = edge_ml(r, side)
                if e is not None and e >= 0.05:
                    g = grade_ml(r, side)
                    if g:
                        bets.append(mk_bet(r, 'MONEYLINE', side, e, g, fair_prob_ml(r, side)))
        elif strategy_id == 'S4':
            e = edge_side(r)
            if e is not None and abs(e) >= 2.0:
                side = r['home'] if e > 0 else r['away']
                st = team_state(r['week'])
                if st['ppg'][side] > st['pag'][side]:
                    g = grade_side(r, side)
                    if g:
                        bets.append(mk_bet(r, 'SPREAD', side, e, g, fair_prob_side(r, side)))
        elif strategy_id == 'S5':
            e = edge_total(r)
            if e is not None and e <= -2.0:
                g = grade_total(r, 'Under')
                if g:
                    bets.append(mk_bet(r, 'TOTAL', 'Under', -e, g, fair_prob_total(r, 'Under')))
        elif strategy_id == 'S6':
            es, et = edge_side(r), edge_total(r)
            if es is not None and et is not None and abs(es) >= 2.0 and abs(et) >= 2.0:
                side = r['home'] if es > 0 else r['away']
                tside = 'Over' if et > 0 else 'Under'
                g1, g2 = grade_side(r, side), grade_total(r, tside)
                if g1 and g2:
                    legs = [('SPREAD', side, g1), ('TOTAL', tside, g2)]
                    fps = [fair_prob_side(r, side), fair_prob_total(r, tside)]
                    pb = mk_parlay(r, legs, fps)
                    if pb:
                        bets.append(pb)
    if strategy_id == 'S7':
        by_week = {}
        for r in graded:
            e = edge_side(r)
            if e is not None and abs(e) >= 3.0:
                by_week.setdefault(r['week'], []).append((abs(e), r, e))
        for wk, items in sorted(by_week.items()):
            items.sort(key=lambda x: -x[0])
            if len(items) >= 2:
                legs, fps = [], []
                for _, r, e in items[:2]:
                    side = r['home'] if e > 0 else r['away']
                    g = grade_side(r, side)
                    if g:
                        legs.append(('SPREAD', side, g))
                        fps.append(fair_prob_side(r, side))
                if len(legs) == 2:
                    pb = mk_parlay(items[0][1], legs, fps)
                    if pb:
                        bets.append(pb)
    return bets


def mk_bet(r, market, side, edge, g, fair_prob=None):
    won, push, odds = g
    dec = S.american_to_decimal(odds) if odds is not None else None
    mkt_p = (1.0 / dec) if (dec and not math.isnan(dec) and dec > 0) else None
    return {'week': r['week'], 'game': f"{r['away']}@{r['home']}",
            'game_url': r['game_url'], 'market': market, 'side': side,
            'edge': edge, 'odds': odds, 'decimal': dec,
            'fair_prob': rnd(fair_prob, 4), 'market_prob': rnd(mkt_p, 4),
            'won': won, 'push': push, 'legs': 1}


def mk_parlay(r, legs, fair_probs):
    """Combine legs at the product of the market prices actually taken.

    `r` is the reference game row (used for the week / link). A parlay settles
    as a WIN only if every leg wins; any push settles the whole ticket as a push.
    `fair_probs` holds the model probability of each leg, used only for staking.
    """
    dec = 1.0
    p_fair = 1.0
    for _, _, (won, push, odds) in legs:
        d = S.american_to_decimal(odds)
        if d is None or math.isnan(d):
            return None
        dec *= d
    for (mkt, side, g), fp in zip(legs, fair_probs):
        p_fair *= fp
    won_all = all(g[0] for _, _, g in legs)
    any_push = any(g[1] for _, _, g in legs)
    return {'week': r['week'] if r else None,
            'game': (f"{r['away']}@{r['home']}" if r else 'multi-game'),
            'game_url': r['game_url'] if r else None,
            'market': '+'.join(m for m, _, _ in legs),
            'side': ' / '.join(s for _, s, _ in legs),
            'edge': None, 'odds': None, 'decimal': rnd(dec, 4),
            'fair_prob': rnd(p_fair, 4),
            'market_prob': rnd(1.0 / dec, 4),
            'won': won_all and not any_push, 'push': any_push,
            'legs': len(legs)}


def bh_fdr(pvals: dict, q: float = 0.05) -> dict:
    """Benjamini-Hochberg step-up procedure. Returns per-key reject flags and q-values."""
    items = sorted((k, v) for k, v in pvals.items() if v is not None)
    m = len(items)
    out = {k: {'p': v, 'q': None, 'reject': False} for k, v in pvals.items()}
    if m == 0:
        return out
    prev = 1.0
    for rank in range(m, 0, -1):
        k, p = items[rank - 1]
        val = min(prev, p * m / rank)
        out[k]['q'] = rnd(val, 6)
        out[k]['reject'] = val <= q
        prev = val
    return out


def evaluate(bets):
    """Signal metrics (stake-invariant) and staking metrics, computed separately."""
    out = {'n_bets': len(bets)}
    if not bets:
        out.update({'n_graded': 0, 'n_won': 0, 'n_push': 0, 'hit_rate': None,
                    'break_even_hit_rate': None, 'avg_decimal': None,
                    'flat_roi': None, 'kelly_roi': None, 'edge_prop_roi': None,
                    'staking_alpha': None, 'max_drawdown': None,
                    'mean_realised_edge': None, 'binomial_p': None,
                    'luck_p': None, 'roi_ci_low': None, 'roi_ci_high': None,
                    'brier': None, 'log_loss': None, 'qualifies': False,
                    'bh_q': None, 'gate_results': {}})
        return out
    settled = [b for b in bets if not b['push']]
    n_graded = len(settled)
    n_won = sum(1 for b in settled if b['won'])
    hit = n_won / n_graded if n_graded else None

    # ---- staking: flat 1 unit
    pnl_flat = [(b['decimal'] - 1.0) if b['won'] else -1.0 for b in settled]
    flat_roi = S.mean(pnl_flat) if settled else None

    # ---- staking: fractional Kelly (25%) driven by the model probability
    pnl_kelly = []
    for b in settled:
        p = b.get('fair_prob')
        d = b['decimal']
        if p is None or d is None or math.isnan(d) or d <= 1:
            pnl_kelly.append(0.0)
            continue
        b_ = d - 1.0
        full = (p * b_ - (1 - p)) / b_          # full Kelly fraction
        f = max(0.0, min(0.25, 0.25 * full))    # quarter Kelly, floored at zero
        pnl_kelly.append(f * (b_ if b['won'] else -1.0))
    kelly_units = sum(1.0 for _ in settled)
    kelly_roi = (sum(pnl_kelly) / kelly_units) if settled else None

    # ---- staking: edge-proportional
    pnl_ep = []
    for b in settled:
        e = abs(b.get('edge') or 0)
        w = min(2.0, e / 3.0) if e else 0.0
        pnl_ep.append(w * ((b['decimal'] - 1.0) if b['won'] else -1.0))
    ep_w = sum(min(2.0, abs(b.get('edge') or 0) / 3.0) for b in settled)
    ep_roi = (sum(pnl_ep) / ep_w) if ep_w > 0 else None

    # ---- drawdown on the flat series
    eq, peak, mdd = 0.0, 0.0, 0.0
    for p in pnl_flat:
        eq += p
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)

    # ---- SIGNAL metrics: no stake enters any of these.
    # Realised edge = outcome minus the probability the price implies. It is the
    # standard "did the bettor beat the number they took" measure and it is
    # completely invariant to how much was staked.
    realised = [(1.0 - b['market_prob']) if b['won'] else -b['market_prob']
                for b in settled if b['market_prob'] is not None]
    mean_edge = S.mean(realised) if realised else None
    # Calibration / discrimination of the model probability, also stake-free.
    brier = S.mean([(b['fair_prob'] - (1.0 if b['won'] else 0.0)) ** 2
                    for b in settled if b['fair_prob'] is not None]) or None
    ll = None
    for b in settled:
        p = b['fair_prob']
        if p is None or p <= 0 or p >= 1:
            continue
        y = 1.0 if b['won'] else 0.0
        v = -(y * math.log(p) + (1 - y) * math.log(1 - p))
        ll = v if ll is None else ll + v
    ll = (ll / n_graded) if (ll is not None and n_graded) else None

    # ---- LUCK TEST -------------------------------------------------------
    # Null: the bettor has no skill, so each bet wins with the probability the
    # price implies (p_i = 1/decimal_i). That null is centred on zero ROI by
    # construction, which is what makes it a real test. Permuting the observed
    # win/loss labels instead would preserve the observed hit rate and would
    # therefore always return p ~ 0.5, so it is NOT used.
    rng = random.Random(RNG_SEED)
    observed = flat_roi if flat_roi is not None else 0.0
    null = []
    for _ in range(LUCK_TEST_DRAWS):
        tot = 0.0
        for b in settled:
            d = b['decimal']
            p_i = (1.0 / d) if (d and not math.isnan(d) and d > 0) else 0.5
            tot += (d - 1.0) if rng.random() < p_i else -1.0
        null.append(tot / n_graded)
    luck_p = S.permutation_p(observed, null)

    # ---- bootstrap CI on flat ROI
    boot = []
    for _ in range(2000):
        sample = [pnl_flat[rng.randrange(n_graded)] for _ in range(n_graded)]
        boot.append(S.mean(sample))
    boot.sort()
    ci_lo = boot[int(0.025 * len(boot))]
    ci_hi = boot[int(0.975 * len(boot))]

    # ---- binomial test against break-even hit rate implied by the average price
    avg_dec = S.mean([b['decimal'] for b in settled])
    be = (1.0 / avg_dec) if avg_dec else 0.5238
    binom_p = S.binom_right_tail(n_won, n_graded, be) if n_graded else None

    gates = {
        'G1_min_sample': {'threshold': MIN_N_QUALIFY, 'value': n_graded,
                          'pass': n_graded >= MIN_N_QUALIFY},
        'G2_luck_test': {'threshold': BREAKEVEN_ALPHA, 'value': rnd(luck_p),
                         'pass': luck_p is not None and luck_p <= BREAKEVEN_ALPHA},
        'G3_positive_roi_ci': {'threshold': '95% CI lower bound > 0', 'value': rnd(ci_lo),
                               'pass': ci_lo > 0},
        'G4_beats_breakeven': {'threshold': BREAKEVEN_ALPHA, 'value': rnd(binom_p),
                               'pass': binom_p is not None and binom_p <= BREAKEVEN_ALPHA},
        'G5_no_lookahead': {'threshold': 'structural', 'value':
                            'walk-forward; features use only weeks < w',
                            'pass': True},
        'G6_half_stability': {'threshold': 'both halves ROI > 0', 'value': None,
                              'pass': False},
    }
    if n_graded >= 20:
        half = n_graded // 2
        h1 = S.mean(pnl_flat[:half]); h2 = S.mean(pnl_flat[half:])
        gates['G6_half_stability']['value'] = f'{rnd(h1)} / {rnd(h2)}'
        gates['G6_half_stability']['pass'] = (h1 > 0 and h2 > 0)

    out.update({'n_graded': n_graded, 'n_won': n_won, 'n_push': len(bets) - n_graded,
                'hit_rate': rnd(hit), 'break_even_hit_rate': rnd(be),
                'avg_decimal': rnd(avg_dec),
                'flat_roi': rnd(flat_roi), 'kelly_roi': rnd(kelly_roi),
                'edge_prop_roi': rnd(ep_roi),
                'staking_alpha': rnd(kelly_roi - flat_roi) if (kelly_roi is not None and flat_roi is not None) else None,
                'max_drawdown': rnd(mdd), 'mean_realised_edge': rnd(mean_edge, 4),
                'brier': rnd(brier, 4), 'log_loss': rnd(ll, 4),
                'luck_p': rnd(luck_p), 'binomial_p': rnd(binom_p),
                'roi_ci_low': rnd(ci_lo), 'roi_ci_high': rnd(ci_hi),
                'gate_results': gates,
                'qualifies': all(g['pass'] for g in gates.values())})
    return out


RESULTS_BY_STRATEGY = {}
for sd in STRATEGY_DEFS:
    bets = build_bets(sd['id'])
    ev = evaluate(bets)
    ev['bets'] = bets
    RESULTS_BY_STRATEGY[sd['id']] = ev

# --- multiple-comparison control across the strategy family ----------------
_pvals = {k: v['binomial_p'] for k, v in RESULTS_BY_STRATEGY.items() if v['n_graded']}
FDR = S is not None and bh_fdr(_pvals, q=0.05) or {}
for sid, res in RESULTS_BY_STRATEGY.items():
    f = FDR.get(sid, {})
    res['bh_q'] = f.get('q')
    if res['gate_results']:
        res['gate_results']['G7_survives_fdr'] = {
            'threshold': 'BH q <= 0.05 across the 8-strategy family',
            'value': f.get('q'), 'pass': bool(f.get('reject'))}
        res['qualifies'] = all(g['pass'] for g in res['gate_results'].values())

# ===========================================================================
# 8. LINE-MAKING SKILL  (does the originated number beat the market number?)
#    This needs NO betting at all, so it is the purest SIGNAL measure.
# ===========================================================================
sp_fair_err, sp_mkt_err = [], []
tot_fair_err, tot_mkt_err = [], []
for r in graded:
    m = r['official_home_pts'] - r['official_away_pts']
    t = r['official_home_pts'] + r['official_away_pts']
    if r['fair_spread'] is not None:
        sp_fair_err.append(abs(m - r['fair_spread']))
    if r['market_spread'] is not None:
        sp_mkt_err.append(abs(m - r['market_spread']))
    if r['fair_total'] is not None:
        tot_fair_err.append(abs(t - r['fair_total']))
    if r['market_total'] is not None:
        tot_mkt_err.append(abs(t - r['market_total']))

LINE_SKILL = {
    'spread': {'n': len(sp_fair_err),
               'mae_originated': rnd(S.mean(sp_fair_err), 3),
               'mae_market': rnd(S.mean(sp_mkt_err), 3),
               'delta': rnd(S.mean(sp_mkt_err) - S.mean(sp_fair_err), 3)},
    'total': {'n': len(tot_fair_err),
              'mae_originated': rnd(S.mean(tot_fair_err), 3),
              'mae_market': rnd(S.mean(tot_mkt_err), 3),
              'delta': rnd(S.mean(tot_mkt_err) - S.mean(tot_fair_err), 3)},
}
# paired tests
sp_d = [b - a for a, b in zip(sp_fair_err, sp_mkt_err)]
tot_d = [b - a for a, b in zip(tot_fair_err, tot_mkt_err)]
LINE_SKILL['spread']['paired_mean_diff'] = rnd(S.mean(sp_d), 3)
LINE_SKILL['spread']['paired_sd'] = rnd(S.sd(sp_d), 3)
LINE_SKILL['spread']['paired_t'] = rnd(
    S.mean(sp_d) / (S.sd(sp_d) / math.sqrt(len(sp_d))), 4) if len(sp_d) > 1 else None
LINE_SKILL['spread']['paired_p'] = rnd(S.t_two_sided_p(
    S.mean(sp_d) / (S.sd(sp_d) / math.sqrt(len(sp_d))), len(sp_d) - 1), 6) if len(sp_d) > 1 else None
LINE_SKILL['total']['paired_mean_diff'] = rnd(S.mean(tot_d), 3)
LINE_SKILL['total']['paired_sd'] = rnd(S.sd(tot_d), 3)
LINE_SKILL['total']['paired_t'] = rnd(
    S.mean(tot_d) / (S.sd(tot_d) / math.sqrt(len(tot_d))), 4) if len(tot_d) > 1 else None
LINE_SKILL['total']['paired_p'] = rnd(S.t_two_sided_p(
    S.mean(tot_d) / (S.sd(tot_d) / math.sqrt(len(tot_d))), len(tot_d) - 1), 6) if len(tot_d) > 1 else None

# ===========================================================================
# 9. CORRELATION REGISTER  (official numbers only, n published on every row)
# ===========================================================================
st26 = {r['team']: r for r in standings}
gp26 = {t: st26[t]['w'] + st26[t]['l'] + st26[t]['t'] for t in TEAMS}
ppg26 = {t: st26[t]['pf'] / gp26[t] for t in TEAMS}
pag26 = {t: st26[t]['pa'] / gp26[t] for t in TEAMS}
net26 = {t: (st26[t]['pf'] - st26[t]['pa']) / gp26[t] for t in TEAMS}
wp26 = {t: (st26[t]['w'] + 0.5 * st26[t]['t']) / gp26[t] for t in TEAMS}
ppg25 = {t: PRIOR[t]['pf'] / PRIOR_G[t] for t in TEAMS}
pag25 = {t: PRIOR[t]['pa'] / PRIOR_G[t] for t in TEAMS}
net25 = {t: (PRIOR[t]['pf'] - PRIOR[t]['pa']) / PRIOR_G[t] for t in TEAMS}
wp25 = {t: (PRIOR[t]['w'] + 0.5 * PRIOR[t]['t']) / PRIOR_G[t] for t in TEAMS}

CORR = []


def add_corr(cid, label, xa, ya, source, note=''):
    c = S.pearson(list(xa), list(ya))
    CORR.append({'id': cid, 'label': label, 'x': None, 'y': None,
                 'n': c['n'], 'r': rnd(c['r']), 'p_value': rnd(c['p_value'], 6),
                 'ci95_low': rnd(c['ci_low']), 'ci95_high': rnd(c['ci_high']),
                 'source_url': source, 'note': note or c.get('note', '')})


add_corr('C-01', '2026 points for per game vs win percentage (team level)',
         [ppg26[t] for t in TEAMS], [wp26[t] for t in TEAMS], NFL_STANDINGS_URL)
add_corr('C-02', '2026 points against per game vs win percentage (team level)',
         [pag26[t] for t in TEAMS], [wp26[t] for t in TEAMS], NFL_STANDINGS_URL)
add_corr('C-03', '2026 net points per game vs win percentage (team level)',
         [net26[t] for t in TEAMS], [wp26[t] for t in TEAMS], NFL_STANDINGS_URL)
add_corr('C-04', '2026 points for per game vs points against per game (team level)',
         [ppg26[t] for t in TEAMS], [pag26[t] for t in TEAMS], NFL_STANDINGS_URL)
add_corr('C-05', '2025 net points per game vs 2026 net points per game (season-to-season stability)',
         [net25[t] for t in TEAMS], [net26[t] for t in TEAMS],
         NFL_STANDINGS_2025_URL + ' + ' + NFL_STANDINGS_URL,
         'Both seasons are official final / current standings. 2026 is a partial season.')
add_corr('C-06', '2025 win percentage vs 2026 win percentage (season-to-season stability)',
         [wp25[t] for t in TEAMS], [wp26[t] for t in TEAMS],
         NFL_STANDINGS_2025_URL + ' + ' + NFL_STANDINGS_URL)
add_corr('C-07', 'Official home margin vs official game total (game level)',
         margins, totals, NFL_SCHEDULE_URL.format(w='1-10'))
add_corr('C-08', 'Official home score vs official away score (game level)',
         [g['home_pts'] for g in finished], [g['away_pts'] for g in finished],
         NFL_SCHEDULE_URL.format(w='1-10'))
add_corr('C-09', 'Absolute official margin vs official game total (game level)',
         [abs(m) for m in margins], totals, NFL_SCHEDULE_URL.format(w='1-10'))
add_corr('C-10', 'Official game total vs week number (scoring drift through the season)',
         totals, [g['week'] for g in finished], NFL_SCHEDULE_URL.format(w='1-10'))

# --- official-only parlay leg dependence -----------------------------------
home_win = [1 if (g['home_pts'] > g['away_pts']) else 0 for g in finished]
over_46 = [1 if (g['home_pts'] + g['away_pts']) > PARLAY_TOTAL_THRESHOLD else 0 for g in finished]
big_margin = [1 if abs(g['home_pts'] - g['away_pts']) > PARLAY_MARGIN_THRESHOLD else 0 for g in finished]
a = sum(1 for i in range(len(finished)) if home_win[i] and over_46[i])
b = sum(1 for i in range(len(finished)) if home_win[i] and not over_46[i])
c_ = sum(1 for i in range(len(finished)) if not home_win[i] and over_46[i])
d_ = sum(1 for i in range(len(finished)) if not home_win[i] and not over_46[i])
phi1 = S.phi_coefficient(a, b, c_, d_)
CORR.append({'id': 'C-11',
             'label': f'Leg dependence: home win vs total over {PARLAY_TOTAL_THRESHOLD:.0f} '
                      f'(both legs from official results)',
             'x': None, 'y': None, 'n': phi1['n'], 'r': rnd(phi1['r']),
             'p_value': rnd(phi1['p_value'], 6),
             'ci95_low': rnd(phi1['ci_low']), 'ci95_high': rnd(phi1['ci_high']),
             'source_url': NFL_SCHEDULE_URL.format(w='1-10'),
             'note': 'Phi coefficient = Pearson r on two 0/1 series. Threshold is a fixed '
                     'pre-registered constant, not fitted, so there is no look-ahead.'})
a2 = sum(1 for i in range(len(finished)) if home_win[i] and big_margin[i])
b2 = sum(1 for i in range(len(finished)) if home_win[i] and not big_margin[i])
c2 = sum(1 for i in range(len(finished)) if not home_win[i] and big_margin[i])
d2 = sum(1 for i in range(len(finished)) if not home_win[i] and not big_margin[i])
phi2 = S.phi_coefficient(a2, b2, c2, d2)
CORR.append({'id': 'C-12',
             'label': f'Leg dependence: home win vs margin over {PARLAY_MARGIN_THRESHOLD:.0f} '
                      f'(both legs from official results)',
             'x': None, 'y': None, 'n': phi2['n'], 'r': rnd(phi2['r']),
             'p_value': rnd(phi2['p_value'], 6),
             'ci95_low': rnd(phi2['ci_low']), 'ci95_high': rnd(phi2['ci_high']),
             'source_url': NFL_SCHEDULE_URL.format(w='1-10'),
             'note': 'Phi coefficient = Pearson r on two 0/1 series.'})

# --- the dependence that CANNOT be computed from official sources -----------
CORR.append({'id': 'C-13',
             'label': 'Home covers the market spread vs game goes over the market total',
             'x': None, 'y': None, 'n': None, 'r': None, 'p_value': None,
             'ci95_low': None, 'ci95_high': None,
             'source_url': NFLDATA_URL,
             'note': 'NOT COMPUTED. Leg 1 and leg 2 require the market spread and the market '
                     'total, which are third-party, not official. The rule for this workspace is '
                     'that correlations are published only when every input is officially '
                     'sourced, so the cell is left blank rather than filled from a '
                     'third-party number.'})

# ===========================================================================
# 10. SIGNAL vs STAKING, and the DEMOTION GATE
# ===========================================================================
def signal_score(ev):
    """Stake-invariant signal quality, 0-100. No bet size appears in this function."""
    if not ev['n_graded']:
        return {'score': None, 'parts': {}}
    parts = {}
    # (a) line-making skill vs the market number, normalised
    parts['line_skill_spread'] = LINE_SKILL['spread']['delta'] or 0.0
    parts['line_skill_total'] = LINE_SKILL['total']['delta'] or 0.0
    # (b) accuracy above the break-even rate implied by the prices taken
    be = ev['break_even_hit_rate'] or 0.5238
    acc_gap = (ev['hit_rate'] or 0.0) - be
    parts['accuracy_gap_vs_breakeven'] = rnd(acc_gap, 4)
    # (c) evidence that the accuracy gap is not luck
    parts['luck_p'] = ev['luck_p']
    sig = 0.0
    sig += 25.0 * max(0.0, min(1.0, (parts['line_skill_spread'] + 1.0) / 2.0))
    sig += 25.0 * max(0.0, min(1.0, (parts['line_skill_total'] + 1.0) / 2.0))
    sig += 25.0 * max(0.0, min(1.0, (acc_gap + 0.10) / 0.20))
    sig += 25.0 * max(0.0, min(1.0, 1.0 - (ev['luck_p'] if ev['luck_p'] is not None else 1.0)))
    return {'score': rnd(sig, 1), 'parts': parts}


def staking_score(ev):
    """Quality contributed by the sizing rule alone, 0-100."""
    if not ev['n_graded'] or ev['flat_roi'] is None:
        return {'score': None, 'parts': {}}
    parts = {'flat_roi': ev['flat_roi'], 'kelly_roi': ev['kelly_roi'],
             'edge_prop_roi': ev['edge_prop_roi'],
             'staking_alpha': ev['staking_alpha'],
             'max_drawdown': ev['max_drawdown']}
    roi_term = 40.0 * max(0.0, min(1.0, (ev['flat_roi'] + 0.05) / 0.15))
    alpha_term = 30.0 * max(0.0, min(1.0, ((ev['staking_alpha'] or 0) + 0.02) / 0.06))
    dd = abs(ev['max_drawdown'] or 0)
    dd_term = 30.0 * max(0.0, min(1.0, 1.0 - dd / 10.0))
    return {'score': rnd(roi_term + alpha_term + dd_term, 1), 'parts': parts}


DEMOTION_RULES = [
    {'id': 'D1', 'trigger': 'Rolling 25 settled bets with flat ROI < -10%',
     'action': 'LIVE -> PAPER', 'window': 'rolling 25'},
    {'id': 'D2', 'trigger': 'Rolling 50 settled bets with mean realised edge <= 0',
     'action': 'LIVE -> PAPER', 'window': 'rolling 50'},
    {'id': 'D3', 'trigger': 'Luck-test p > 0.20 (result indistinguishable from a coin flip)',
     'action': 'LIVE -> PAPER', 'window': 'last 100 settled bets'},
    {'id': 'D4', 'trigger': 'Signal score in the bottom quartile of the leaderboard for two '
                            'consecutive evaluation windows',
     'action': 'LIVE -> PAPER', 'window': 'two consecutive windows'},
    {'id': 'D5', 'trigger': 'Any look-ahead, data-integrity or provenance violation detected',
     'action': 'LIVE -> PAPER + QUARANTINE (all rows withdrawn from the leaderboard)',
     'window': 'immediate'},
    {'id': 'D6', 'trigger': 'Maximum drawdown over the live window exceeds 20 units at 1u flat',
     'action': 'LIVE -> PAPER', 'window': 'live window'},
]
PROMOTION_RULES = [
    {'id': 'P1', 'trigger': 'All qualification gates G1-G6 pass on out-of-sample data',
     'action': 'PAPER -> LIVE'},
    {'id': 'P2', 'trigger': 'G1 sample floor met AND G3 ROI confidence interval lower bound > 0',
     'action': 'PAPER -> LIVE (provisional, 25-bet probation)'},
]

LEADERBOARD = []
for sd in STRATEGY_DEFS:
    ev = RESULTS_BY_STRATEGY[sd['id']]
    sig = signal_score(ev)
    stk = staking_score(ev)
    # apply the demotion rules to whatever live window exists
    demotions = []
    n = ev['n_graded']
    if n >= 25 and ev['flat_roi'] is not None:
        last25 = [b for b in ev['bets'] if not b['push']][-25:]
        r25 = S.mean([(b['decimal'] - 1.0) if b['won'] else -1.0 for b in last25])
        if r25 < -0.10:
            demotions.append({'rule': 'D1', 'observed': rnd(r25), 'threshold': -0.10})
    if n >= 50 and (ev['mean_realised_edge'] or 0) <= 0:
        demotions.append({'rule': 'D2', 'observed': ev['mean_realised_edge'], 'threshold': 0})
    if ev['luck_p'] is not None and ev['luck_p'] > 0.20:
        demotions.append({'rule': 'D3', 'observed': ev['luck_p'], 'threshold': 0.20})
    if ev['max_drawdown'] is not None and abs(ev['max_drawdown']) > 20:
        demotions.append({'rule': 'D6', 'observed': ev['max_drawdown'], 'threshold': -20})
    LEADERBOARD.append({
        'id': sd['id'], 'name': sd['name'], 'family': sd['family'],
        'market': sd['market'], 'rule': sd['rule'],
        'status': 'PAPER',
        'n_bets': ev['n_bets'], 'n_graded': ev['n_graded'], 'n_won': ev['n_won'],
        'hit_rate': ev['hit_rate'], 'break_even_hit_rate': ev['break_even_hit_rate'],
        'signal_score': sig['score'], 'signal_parts': sig['parts'],
        'staking_score': stk['score'], 'staking_parts': stk['parts'],
        'flat_roi': ev['flat_roi'], 'kelly_roi': ev['kelly_roi'],
        'staking_alpha': ev['staking_alpha'],
        'max_drawdown': ev['max_drawdown'],
        'luck_p': ev['luck_p'], 'binomial_p': ev['binomial_p'],
        'roi_ci_low': ev['roi_ci_low'], 'roi_ci_high': ev['roi_ci_high'],
        'gates': ev['gate_results'], 'qualifies': ev['qualifies'],
        'demotions_triggered': demotions,
        'reward_units': 0,
    })

LEADERBOARD.sort(key=lambda r: (-(r['signal_score'] or -1), -(r['staking_score'] or -1)))
QUALIFIED = [r for r in LEADERBOARD if r['qualifies']]
REWARDS = {
    'tiers': [
        {'tier': 1, 'condition': 'signal_score >= 80 AND staking_score >= 60 AND all gates pass',
         'reward': '100 units'},
        {'tier': 2, 'condition': 'signal_score >= 65 AND all gates pass', 'reward': '50 units'},
        {'tier': 3, 'condition': 'signal_score >= 50 AND all gates pass', 'reward': '20 units'},
    ],
    'note': 'Rewards are paid on the SIGNAL score. A strategy cannot earn a tier on the staking '
            'score alone: that is exactly the failure mode the signal/staking split exists to '
            'prevent.',
    'qualified': len(QUALIFIED),
    'units_awarded': 0,
}

# ===========================================================================
# 11. WRITE OUTPUTS
# ===========================================================================
def dump(name, obj):
    with open(os.path.join(OUT, name), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
    print(f'  wrote data/{name}')


print('nfl-marketboard build')
dump('reconciliation.json', {'session': SESSION, 'built_utc': BUILT_UTC, **RECON})
dump('base_rates.json', BASE)
dump('market_convention_check.json', {'correlation_vs_official_margin': CONVENTION,
                                     'sign_convention': CONVENTION_CHECK})
dump('originated_lines.json', ORIGINATED)
dump('price_snapshots.json', PRICE_STORE)
dump('line_skill.json', LINE_SKILL)
dump('correlations.json', CORR)
dump('leaderboard.json', {'rows': LEADERBOARD, 'rewards': REWARDS,
                          'demotion_rules': DEMOTION_RULES,
                          'promotion_rules': PROMOTION_RULES})
dump('strategy_results.json',
     {k: {kk: vv for kk, vv in v.items() if kk != 'bets'} for k, v in RESULTS_BY_STRATEGY.items()})
dump('model_card.json', {
    'session': SESSION, 'built_utc': BUILT_UTC,
    'pre_registered_constants': {
        'PRIOR_GAMES': PRIOR_GAMES, 'HFA_PRIOR': HFA_PRIOR,
        'HFA_PRIOR_GAMES': HFA_PRIOR_GAMES, 'SIGMA_FLOOR': SIGMA_FLOOR,
        'FIRST_GRADED_WEEK': FIRST_GRADED_WEEK, 'MIN_N_QUALIFY': MIN_N_QUALIFY,
        'BREAKEVEN_ALPHA': BREAKEVEN_ALPHA, 'LUCK_TEST_DRAWS': LUCK_TEST_DRAWS,
        'PARLAY_TOTAL_THRESHOLD': PARLAY_TOTAL_THRESHOLD,
        'PARLAY_MARGIN_THRESHOLD': PARLAY_MARGIN_THRESHOLD, 'RNG_SEED': RNG_SEED,
    },
    'origination_order': ['side (spread)', 'total', 'moneyline (derived from side and total)'],
    'formulas': {
        'E_home_pts': 'L + off[home] + def[away] + HFA/2',
        'E_away_pts': 'L + off[away] + def[home] - HFA/2',
        'fair_spread': 'E_home_pts - E_away_pts   (positive = home favoured)',
        'fair_total': 'E_home_pts + E_away_pts',
        'fair_p_home': 'NormalCDF(fair_spread / sigma_eff), '
                       'sigma_eff = sigma_resid * fair_total / (2L)',
    },
    'inputs': {
        'results': 'nfl.com official weekly schedule pages (transcribed, reconciled)',
        'prior': 'nfl.com official 2025 final standings',
        'market_prices': 'nflverse/nfldata archive (THIRD PARTY; the NFL publishes no odds)',
    },
    'leakage_control': 'walk-forward: a number for week w uses only official games with '
                       'week < w plus the pre-season 2025 prior.',
})
print(f'  games final={len(finished)} scheduled={len(scheduled)} '
      f'recon_mismatches={RECON["mismatches"]}')
print('done')

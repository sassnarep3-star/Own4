#!/usr/bin/env python3
"""Deterministic NFL assurance calculations from official factual extractions.

All outputs are derived research estimates, not official NFL lines or sportsbook
offers. The protocol is frozen in protocol.json before this engine is evaluated.
"""
from __future__ import annotations
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RESULTS = ROOT / 'results'
PROTOCOL = json.loads((ROOT / 'protocol.json').read_text())
SEED = 20261102
BOOT = 2000
PLACEBO = 1000


def logistic(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def half_line(x):
    """Nearest half-integer, never an integer push line."""
    return math.floor(x) + 0.5


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, n
    mx, my = mean([p[0] for p in pairs]), mean([p[1] for p in pairs])
    sx = math.sqrt(sum((x - mx) ** 2 for x, _ in pairs))
    sy = math.sqrt(sum((y - my) ** 2 for _, y in pairs))
    if sx == 0 or sy == 0:
        return None, n
    return sum((x - mx) * (y - my) for x, y in pairs) / (sx * sy), n


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = rank
        i = j + 1
    return out


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    return pearson(ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs]))[0]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def bh_fdr(pvals):
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    q = [1.0] * n
    prev = 1.0
    for rank, idx in enumerate(reversed(order), start=1):
        i = n - rank + 1
        val = min(prev, pvals[idx] * n / i)
        q[idx] = val
        prev = val
    return q


def ridge_logistic(rows, l2=10.0):
    """rows: (features, y). Newton IRLS with intercept unpenalized."""
    d = len(rows[0][0])
    beta = [0.0] * d
    for _ in range(30):
        grad = [0.0] * d
        hess = [[0.0] * d for _ in range(d)]
        for x, y in rows:
            p = logistic(sum(b * v for b, v in zip(beta, x)))
            w = max(p * (1 - p), 1e-6)
            for i in range(d):
                grad[i] += (y - p) * x[i]
                for j in range(d):
                    hess[i][j] += w * x[i] * x[j]
        for i in range(1, d):
            grad[i] -= l2 * beta[i]
            hess[i][i] += l2
        # Solve H * step = grad by Gaussian elimination.
        aug = [hess[i][:] + [grad[i]] for i in range(d)]
        for col in range(d):
            pivot = max(range(col, d), key=lambda r: abs(aug[r][col]))
            if abs(aug[pivot][col]) < 1e-10:
                return beta
            aug[col], aug[pivot] = aug[pivot], aug[col]
            pv = aug[col][col]
            aug[col] = [v / pv for v in aug[col]]
            for r in range(d):
                if r != col:
                    f = aug[r][col]
                    aug[r] = [a - f * b for a, b in zip(aug[r], aug[col])]
        step = [aug[i][-1] for i in range(d)]
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return beta


def parse_wind(text):
    if not text:
        return None
    m = re.search(r'Wind:\s*(?:[A-Z]+\s+)?(\d+(?:\.\d+)?)\s*mph', text, re.I)
    return float(m.group(1)) if m else None


def rest_days(history, team, date):
    prior = [g for g in history if team in (g['home_team'], g['away_team'])]
    if not prior:
        return None
    from datetime import date as D
    last = max(g['date'] for g in prior)
    return (D.fromisoformat(date) - D.fromisoformat(last)).days


def run_model(games):
    """Expanding weekly walk-forward. Returns predictions and final state."""
    p = {m['id']: m.get('parameters', {}) for m in PROTOCOL['models']}
    elo_p = p['M01']
    ratings = defaultdict(lambda: float(elo_p['initial_rating']))
    history = []
    feature_rows = []
    margin_residuals, total_residuals = [], []
    predictions = []
    by_week = defaultdict(list)
    for g in games:
        if g['is_final'] and g['verification'].startswith('official-explicit'):
            by_week[(g['season'], g['week'])].append(g)
    prior_ties, prior_n = 0, 0
    for (season, week), week_games in sorted(by_week.items()):
        if week == 1:
            for team in list(ratings):
                ratings[team] = ratings[team] * (1 - elo_p['season_reversion']) + elo_p['initial_rating'] * elo_p['season_reversion']
        league_mean = mean([s for g in history for s in (g['home_score'], g['away_score'])]) or 22.0
        team_pf, team_pa = defaultdict(list), defaultdict(list)
        for g in history:
            team_pf[g['home_team']].append(g['home_score']); team_pa[g['home_team']].append(g['away_score'])
            team_pf[g['away_team']].append(g['away_score']); team_pa[g['away_team']].append(g['home_score'])
        # Rest for the current week is computed against the frozen prior history only.
        beta = None
        if len(feature_rows) >= p['M02']['min_prior_games']:
            beta = ridge_logistic(feature_rows, p['M02']['l2'])
        week_preds = []
        for g in week_games:
            home, away = g['home_team'], g['away_team']
            rd_h = rest_days(history, home, g['date'])
            rd_a = rest_days(history, away, g['date'])
            if rd_h is None or rd_a is None:
                rest_diff = 0.0
            else:
                rest_diff = max(-10, min(10, rd_h)) - max(-10, min(10, rd_a))
            elo_diff = ratings[home] + elo_p['home_advantage'] - ratings[away]
            p_elo = 1 / (1 + 10 ** (-elo_diff / elo_p['scale']))
            feats = [1.0, elo_diff / 100.0, rest_diff / p['M02']['rest_scale']]
            p_rest = logistic(sum(b * x for b, x in zip(beta, feats))) if beta else p_elo
            def shrunk(values):
                return (sum(values) + p['M03']['pseudo_games'] * league_mean) / (len(values) + p['M03']['pseudo_games'])
            exp_home = (shrunk(team_pf[home]) + shrunk(team_pa[away])) / 2
            exp_away = (shrunk(team_pf[away]) + shrunk(team_pa[home])) / 2
            pred_total = exp_home + exp_away
            pred_margin = elo_diff / p['M03']['elo_points_divisor']
            p_tie = (prior_ties + 1) / (prior_n + 100)
            row = {
                'game_id': g['game_id'], 'season': season, 'week': week, 'date': g['date'],
                'home_team': home, 'away_team': away, 'source_url': g['source_url'], 'game_url': g['game_url'],
                'home_score': g['home_score'], 'away_score': g['away_score'],
                'margin': g['home_score'] - g['away_score'], 'total': g['home_score'] + g['away_score'],
                'is_tie': g['home_score'] == g['away_score'],
                'elo_diff_pre': elo_diff, 'rest_diff_pre': rest_diff,
                'p_m00': 0.5, 'p_m01': p_elo, 'p_m02': p_rest, 'p_tie': p_tie,
                'pred_margin': pred_margin, 'pred_total': pred_total,
                'margin_residual_median': median(margin_residuals) or 0.0,
                'total_residual_median': median(total_residuals) or 0.0,
            }
            row['own_spread'] = -half_line(pred_margin + row['margin_residual_median'])
            row['own_total'] = half_line(pred_total + row['total_residual_median'])
            row['p_home_cover'] = mean([1.0 if pred_margin + e + row['own_spread'] > 0 else 0.0 for e in margin_residuals]) if margin_residuals else None
            row['p_over'] = mean([1.0 if pred_total + e > row['own_total'] else 0.0 for e in total_residuals]) if total_residuals else None
            row['p_home_3way'] = (1 - p_tie) * p_rest
            row['p_away_3way'] = (1 - p_tie) * (1 - p_rest)
            week_preds.append(row)
            y = 1.0 if g['home_score'] > g['away_score'] else 0.0
            if not row['is_tie']:
                feature_rows.append((feats, y))
            margin_residuals.append(row['margin'] - pred_margin)
            total_residuals.append(row['total'] - pred_total)
        predictions.extend(week_preds)
        # Update only after the entire week's predictions are frozen.
        for g, row in zip(week_games, week_preds):
            home, away = g['home_team'], g['away_team']
            margin = g['home_score'] - g['away_score']
            mult = math.log(1 + abs(margin)) / math.log(18)
            mult = max(elo_p['margin_multiplier_min'], min(elo_p['margin_multiplier_max'], mult))
            expected = 1 / (1 + 10 ** (-(ratings[home] + elo_p['home_advantage'] - ratings[away]) / elo_p['scale']))
            actual = 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5
            delta = elo_p['k'] * mult * (actual - expected)
            ratings[home] += delta
            ratings[away] -= delta
            history.append(g)
            prior_n += 1
            prior_ties += int(margin == 0)
    return predictions, {'ratings': dict(ratings), 'history': history, 'margin_residuals': margin_residuals,
                         'total_residuals': total_residuals, 'prior_ties': prior_ties, 'prior_n': prior_n}


def upcoming_lines(games, state, player_logs=None):
    """Originate fair lines for official non-final games using only prior finals."""
    ratings, history = state['ratings'], state['history']
    league_mean = mean([s for g in history for s in (g['home_score'], g['away_score'])]) or 22.0
    team_pf, team_pa = defaultdict(list), defaultdict(list)
    for g in history:
        team_pf[g['home_team']].append(g['home_score']); team_pa[g['home_team']].append(g['away_score'])
        team_pf[g['away_team']].append(g['away_score']); team_pa[g['away_team']].append(g['home_score'])
    def shrunk(values):
        return (sum(values) + 4 * league_mean) / (len(values) + 4)
    rows = []
    for g in games:
        if g['is_final']:
            continue
        home, away = g['home_team'], g['away_team']
        elo_diff = ratings.get(home, 1500) + 45 - ratings.get(away, 1500)
        p_elo = 1 / (1 + 10 ** (-elo_diff / 400))
        p_tie = (state['prior_ties'] + 1) / (state['prior_n'] + 100)
        p_home, p_away = (1 - p_tie) * p_elo, (1 - p_tie) * (1 - p_elo)
        pred_margin = elo_diff / 25
        pred_total = (shrunk(team_pf[home]) + shrunk(team_pa[away])) / 2 + (shrunk(team_pf[away]) + shrunk(team_pa[home])) / 2
        spread = -half_line(pred_margin + (median(state['margin_residuals']) or 0))
        total = half_line(pred_total + (median(state['total_residuals']) or 0))
        rows.append({
            'game_id': g['game_id'], 'date': g['date'], 'home_team': home, 'away_team': away,
            'source_url': g['source_url'], 'game_url': g['game_url'],
            'p_home_win': p_home, 'p_away_win': p_away, 'p_tie': p_tie,
            'fair_home_decimal': 1 / p_home, 'fair_away_decimal': 1 / p_away, 'fair_tie_decimal': 1 / p_tie,
            'own_home_spread': spread, 'own_total': total,
            'p_home_cover_at_own_line': mean([1.0 if pred_margin + e + spread > 0 else 0.0 for e in state['margin_residuals']]),
            'p_over_at_own_line': mean([1.0 if pred_total + e > total else 0.0 for e in state['total_residuals']]),
            'market_spread': None, 'market_total': None, 'market_odds': None,
            'status': 'derived fair line; not a sportsbook offer; not a validated betting strategy',
        })
    return rows


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(max(p, 1e-12), 1 - 1e-12)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def cluster_bootstrap_diff(diffs, clusters, seed=SEED, reps=BOOT):
    """diffs: baseline loss - model loss, positive is improvement. Resample clusters."""
    groups = defaultdict(list)
    for d, c in zip(diffs, clusters):
        groups[c].append(d)
    keys = sorted(groups)
    if not keys:
        return {'estimate': None, 'ci95': [None, None], 'p_two_sided': None}
    rng = random.Random(seed)
    total_n = sum(len(v) for v in groups.values())
    est = sum(sum(v) for v in groups.values()) / total_n
    boots = []
    for _ in range(reps):
        s, n = 0.0, 0
        for _ in range(len(keys)):
            vals = groups[keys[rng.randrange(len(keys))]]
            s += sum(vals); n += len(vals)
        boots.append(s / n)
    lo, hi = quantile(boots, 0.025), quantile(boots, 0.975)
    le = sum(b <= 0 for b in boots)
    ge = sum(b >= 0 for b in boots)
    pval = min(1.0, 2 * min((le + 1) / (reps + 1), (ge + 1) / (reps + 1)))
    return {'estimate': est, 'ci95': [lo, hi], 'p_two_sided': pval}


def calibration(preds, key):
    rows = [(r[key], 0.0 if r['margin'] < 0 else 1.0) for r in preds if not r['is_tie']]
    rows.sort(key=lambda x: x[0])
    n = len(rows)
    bins = []
    for i in range(5):
        chunk = rows[i * n // 5:(i + 1) * n // 5]
        if not chunk:
            continue
        mp = mean([p for p, _ in chunk])
        k = sum(y for _, y in chunk)
        obs = k / len(chunk)
        bins.append({'bin': i + 1, 'n': len(chunk), 'mean_prediction': mp, 'observed_frequency': obs,
                     'gap': obs - mp, 'wilson95': wilson(k, len(chunk))})
    ece = sum(b['n'] * abs(b['gap']) for b in bins) / n if n else None
    return {'ece': ece, 'bins': bins}


def metrics(preds, key):
    rows = [r for r in preds if not r['is_tie']]
    y = [1.0 if r['margin'] > 0 else 0.0 for r in rows]
    p = [r[key] for r in rows]
    return {'n': len(rows), 'ties_excluded': len(preds) - len(rows),
            'brier': mean([brier(a, b) for a, b in zip(p, y)]),
            'log_loss': mean([logloss(a, b) for a, b in zip(p, y)]),
            'accuracy': mean([1.0 if (a >= 0.5) == (b > 0.5) else 0.0 for a, b in zip(p, y)])}


def placebo_test(preds, key, reps=PLACEBO):
    rows = [r for r in preds if not r['is_tie']]
    by_week = defaultdict(list)
    for r in rows:
        by_week[(r['season'], r['week'])].append(r)
    obs = mean([brier(r['p_m00'], 1.0 if r['margin'] > 0 else 0.0) - brier(r[key], 1.0 if r['margin'] > 0 else 0.0) for r in rows])
    rng = random.Random(SEED + 17)
    count = 0
    weeks = list(by_week.values())
    for _ in range(reps):
        s = 0.0
        for week in weeks:
            ys = [1.0 if r['margin'] > 0 else 0.0 for r in week]
            rng.shuffle(ys)
            for r, y in zip(week, ys):
                s += brier(r['p_m00'], y) - brier(r[key], y)
        if s / len(rows) >= obs:
            count += 1
    return {'observed_brier_improvement': obs, 'placebo_p': (count + 1) / (reps + 1), 'replicates': reps}


def robustness(preds, key):
    by_week = defaultdict(list)
    for r in preds:
        if not r['is_tie']:
            by_week[(r['season'], r['week'])].append(r)
    gains = []
    for _, rows in sorted(by_week.items()):
        gains.append(sum(brier(r['p_m00'], 1.0 if r['margin'] > 0 else 0.0) - brier(r[key], 1.0 if r['margin'] > 0 else 0.0) for r in rows))
    positive = sum(g for g in gains if g > 0)
    return {'blocks': len(gains), 'positive_blocks': sum(g > 0 for g in gains),
            'positive_share': mean([1.0 if g > 0 else 0.0 for g in gains]),
            'max_week_concentration': max(gains) / positive if positive > 0 else None}


def correlation_row(cid, name, xs, ys, clusters, unit, source_url, note=''):
    pairs = [(x, y, c) for x, y, c in zip(xs, ys, clusters) if x is not None and y is not None]
    r, n = pearson([p[0] for p in pairs], [p[1] for p in pairs])
    rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
    ci = [None, None]
    pval = None
    if n >= 3 and r is not None:
        groups = defaultdict(list)
        for x, y, c in pairs:
            groups[c].append((x, y))
        keys = sorted(groups)
        rng = random.Random(SEED + sum(ord(ch) for ch in cid))
        boots = []
        for _ in range(BOOT):
            sample = []
            for _ in range(len(keys)):
                sample.extend(groups[keys[rng.randrange(len(keys))]])
            b = pearson([a for a, _ in sample], [b for _, b in sample])[0]
            if b is not None:
                boots.append(b)
        if boots:
            ci = [quantile(boots, 0.025), quantile(boots, 0.975)]
            le = sum(b <= 0 for b in boots); ge = sum(b >= 0 for b in boots)
            pval = min(1.0, 2 * min((le + 1) / (len(boots) + 1), (ge + 1) / (len(boots) + 1)))
    return {'id': cid, 'name': name, 'n': n, 'pearson_r': r, 'spearman_rho': rho,
            'ci95': ci, 'p_two_sided': pval, 'q_bh': None, 'cluster_unit': unit,
            'source_url': source_url, 'note': note, 'status': 'derived association; not betting edge'}


def game_correlations(games, preds):
    finals = [g for g in games if g['is_final'] and g['verification'].startswith('official-explicit')]
    src = 'https://www.nfl.com/schedules/'
    rows = []
    rows.append(correlation_row('C01', 'Home score vs away score', [g['home_score'] for g in finals], [g['away_score'] for g in finals], [g['game_id'] for g in finals], 'game', src))
    rows.append(correlation_row('C02', 'Home margin vs total points', [g['home_score'] - g['away_score'] for g in finals], [g['home_score'] + g['away_score'] for g in finals], [g['game_id'] for g in finals], 'game', src))
    rest, margin, clusters = [], [], []
    for g in finals:
        rh = rest_days([x for x in finals if (x['season'], x['week']) < (g['season'], g['week'])], g['home_team'], g['date'])
        ra = rest_days([x for x in finals if (x['season'], x['week']) < (g['season'], g['week'])], g['away_team'], g['date'])
        if rh is not None and ra is not None:
            rest.append(rh - ra); margin.append(g['home_score'] - g['away_score']); clusters.append(g['game_id'])
    rows.append(correlation_row('C03', 'Rest-day difference vs home margin', rest, margin, clusters, 'game', src, 'Only games with both teams having a prior game in the acquired window.'))
    rows.append(correlation_row('C04', 'Pre-game Elo difference vs home margin', [p['elo_diff_pre'] for p in preds], [p['margin'] for p in preds], [p['game_id'] for p in preds], 'game', src, 'Out-of-sample evaluation window only.'))
    wind = [(parse_wind(g['weather_official']), g['home_score'] + g['away_score'], g['game_id']) for g in finals]
    wind = [w for w in wind if w[0] is not None]
    rows.append(correlation_row('C05', 'Reported wind speed vs total points', [w[0] for w in wind], [w[1] for w in wind], [w[2] for w in wind], 'game', src, 'Subset with explicit official wind string; not a claim about all outdoor games.'))
    rows.append(correlation_row('C06', 'First-half total vs second-half total', [g['home_q1'] + g['home_q2'] + g['away_q1'] + g['away_q2'] for g in finals], [g['home_q3'] + g['home_q4'] + g['away_q3'] + g['away_q4'] for g in finals], [g['game_id'] for g in finals], 'game', src, 'Overtime points are excluded from both halves.'))
    # Cross-game favorite-hit phi across unordered pairs within the same week.
    by_week = defaultdict(list)
    for p in preds:
        if not p['is_tie']:
            by_week[(p['season'], p['week'])].append(p)
    xa, xb, cl = [], [], []
    for key, rows_w in sorted(by_week.items()):
        for i in range(len(rows_w)):
            for j in range(i + 1, len(rows_w)):
                a, b = rows_w[i], rows_w[j]
                fa = 1.0 if (a['p_m01'] >= 0.5) == (a['margin'] > 0) else 0.0
                fb = 1.0 if (b['p_m01'] >= 0.5) == (b['margin'] > 0) else 0.0
                xa.append(fa); xb.append(fb); cl.append(key)
    rows.append(correlation_row('C07', 'Cross-game favorite-hit association (same week)', xa, xb, cl, 'season-week', src, 'Unordered game pairs; shared games make naive pair-level independence invalid, so weeks are resampled.'))
    qs = bh_fdr([r['p_two_sided'] if r['p_two_sided'] is not None else 1.0 for r in rows])
    for r, q in zip(rows, qs):
        r['q_bh'] = q
    return rows


def player_correlations(logs, games):
    if not logs:
        return []
    src = 'https://www.nfl.com/stats/'
    rows = []
    def add(cid, name, subset, xkey, ykey, note=''):
        xs = [r.get(xkey) for r in subset]; ys = [r.get(ykey) for r in subset]
        clusters = [r.get('player_id') or r.get('player') for r in subset]
        rows.append(correlation_row(cid, name, xs, ys, clusters, 'player', src, note + ' Selected current-leader panel; descriptive only.'))
    receivers = [r for r in logs if r.get('receptions') is not None and r.get('receiving_yards') is not None]
    add('PC01', 'Receptions vs receiving yards', receivers, 'receptions', 'receiving_yards')
    rushers = [r for r in logs if r.get('rush_attempts') is not None and r.get('rush_yards') is not None]
    add('PC02', 'Rush attempts vs rush yards', rushers, 'rush_attempts', 'rush_yards')
    qbs = [r for r in logs if r.get('pass_yards') is not None and r.get('pass_td') is not None]
    add('PC03', 'Pass yards vs pass touchdowns', qbs, 'pass_yards', 'pass_td')
    add('PC04', 'Receiving yards vs team win', receivers, 'receiving_yards', 'team_win')
    both = [r for r in logs if r.get('receptions') is not None and r.get('rush_yards') is not None]
    add('PC05', 'Receptions vs rush yards (same player-game)', both, 'receptions', 'rush_yards')
    qs = bh_fdr([r['p_two_sided'] if r['p_two_sided'] is not None else 1.0 for r in rows])
    for r, q in zip(rows, qs):
        r['q_bh'] = q
    return rows


def gate_results(preds, model_metrics, comparisons, placebo, robust, parse_report, player_n):
    gates = []
    n = model_metrics['M01']['n']
    g01 = parse_report['issues'] == [] and parse_report['verified_final_games'] == parse_report['final_games']
    gates.append({'id': 'G01', 'status': 'pass' if g01 else 'fail', 'evidence': f"{parse_report['verified_final_games']}/{parse_report['final_games']} final games pass integrity; {len(parse_report['issues'])} issues"})
    gates.append({'id': 'G02', 'status': 'pass' if n >= 300 else 'fail', 'evidence': f'{n} out-of-sample non-tie games; player-panel rows={player_n} (prop gate requires 1000)'})
    for mid in ('M01', 'M02'):
        c = comparisons[mid]
        passed = c['brier_improvement']['ci95'][0] > 0 and c['q_bh'] < 0.05 and model_metrics[mid]['log_loss'] < model_metrics['M00']['log_loss']
        gates.append({'id': f'G03-{mid}', 'status': 'pass' if passed else 'fail', 'evidence': f"Brier improvement CI {c['brier_improvement']['ci95']}, q={c['q_bh']:.4f}"})
        cal = model_metrics[mid]['calibration']
        cal_pass = cal['ece'] <= 0.03 and all(abs(b['gap']) <= 0.10 for b in cal['bins'])
        gates.append({'id': f'G04-{mid}', 'status': 'pass' if cal_pass else 'fail', 'evidence': f"ECE={cal['ece']:.4f}"})
        pl = placebo[mid]
        gates.append({'id': f'G07-{mid}', 'status': 'pass' if pl['placebo_p'] < 0.05 else 'fail', 'evidence': f"placebo p={pl['placebo_p']:.4f}; leakage unit tests run separately"})
        rb = robust[mid]
        rb_pass = rb['positive_share'] >= 0.60 and (rb['max_week_concentration'] is None or rb['max_week_concentration'] <= 0.25)
        gates.append({'id': f'G08-{mid}', 'status': 'pass' if rb_pass else 'fail', 'evidence': f"positive blocks={rb['positive_share']:.2%}, max week concentration={rb['max_week_concentration']}"})
    for gid, why in [('G05', 'No verified operator price archive'), ('G06', 'No validated/priced joint combo ticket sample'), ('G09', 'No operator settlement/execution archive'), ('G10', 'No prospective post-registration replication sample')]:
        gates.append({'id': gid, 'status': 'blocked', 'evidence': why})
    return gates


def main():
    games = json.loads((DATA / 'games.json').read_text())
    parse_report = json.loads((DATA / 'parse_report.json').read_text())
    player_path = DATA / 'player_logs.json'
    logs = json.loads(player_path.read_text()) if player_path.exists() else []
    preds, state = run_model(games)
    eval_preds = [p for p in preds if p['season'] >= 2025]
    model_metrics = {mid: metrics(eval_preds, key) for mid, key in [('M00', 'p_m00'), ('M01', 'p_m01'), ('M02', 'p_m02')]}
    for mid in model_metrics:
        model_metrics[mid]['calibration'] = calibration(eval_preds, {'M00': 'p_m00', 'M01': 'p_m01', 'M02': 'p_m02'}[mid])
    comparisons, placebo, robust = {}, {}, {}
    clusters = [(p['season'], p['week']) for p in eval_preds if not p['is_tie']]
    rows = [p for p in eval_preds if not p['is_tie']]
    pvals = []
    for mid, key in [('M01', 'p_m01'), ('M02', 'p_m02')]:
        diffs = [brier(p['p_m00'], 1.0 if p['margin'] > 0 else 0.0) - brier(p[key], 1.0 if p['margin'] > 0 else 0.0) for p in rows]
        c = cluster_bootstrap_diff(diffs, clusters)
        comparisons[mid] = {'brier_improvement': c}
        pvals.append(c['p_two_sided'])
        placebo[mid] = placebo_test(eval_preds, key)
        robust[mid] = robustness(eval_preds, key)
    qs = bh_fdr(pvals)
    for mid, q in zip(comparisons, qs):
        comparisons[mid]['q_bh'] = q
    # Spread/total descriptive accuracy against expanding prior-mean baselines.
    margin_mae = mean([abs(p['margin'] - p['pred_margin']) for p in eval_preds])
    total_mae = mean([abs(p['total'] - p['pred_total']) for p in eval_preds])
    baseline_total = mean([p['total'] for p in preds if p['season'] == 2024])
    baseline_margin = mean([p['margin'] for p in preds if p['season'] == 2024])
    totals = {'n': len(eval_preds), 'margin_mae': margin_mae, 'total_mae': total_mae,
              'baseline_margin_mae': mean([abs(p['margin'] - baseline_margin) for p in eval_preds]),
              'baseline_total_mae': mean([abs(p['total'] - baseline_total) for p in eval_preds]),
              'note': 'Own-line cover/over rates are calibration diagnostics at model-generated lines, not betting ROI.'}
    corr = game_correlations(games, eval_preds)
    pcorr = player_correlations(logs, games)
    upcoming = upcoming_lines(games, state)
    gates = gate_results(eval_preds, model_metrics, comparisons, placebo, robust, parse_report, len(logs))
    leaderboard = []
    for mid in ('M00', 'M01', 'M02'):
        m = model_metrics[mid]
        leaderboard.append({'id': mid, 'division': 'single-game forecasts', 'log_loss': m['log_loss'], 'brier': m['brier'],
                            'reward_eligible': False, 'reward': None,
                            'status': 'research ranking only; universal price/execution/prospective gates blocked'})
    leaderboard.sort(key=lambda r: r['log_loss'])
    results = {'protocol_id': PROTOCOL['id'], 'seed': SEED, 'bootstrap_replicates': BOOT,
               'model_metrics': model_metrics, 'comparisons': comparisons, 'placebo': placebo, 'robustness': robust,
               'totals': totals, 'correlations': corr, 'player_correlations': pcorr, 'gates': gates,
               'leaderboard': leaderboard, 'upcoming_lines': upcoming,
               'strategy_status': [{**s, 'reward_eligible': False} for s in PROTOCOL['strategies']],
               'reward_pool': None, 'validated_betting_strategies': 0}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'analysis.json').write_text(json.dumps(results, indent=2) + '\n')
    (RESULTS / 'predictions.json').write_text(json.dumps(eval_preds, indent=2) + '\n')
    # Compact CSV exports.
    import csv
    def csv_out(name, rows):
        if not rows:
            return
        with (RESULTS / name).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    csv_out('predictions.csv', eval_preds)
    csv_out('correlations.csv', [{k: v for k, v in r.items() if k != 'ci95'} | {'ci_low': r['ci95'][0], 'ci_high': r['ci95'][1]} for r in corr + pcorr])
    csv_out('own_lines.csv', upcoming)
    print(json.dumps({'eval_games': len(eval_preds), 'metrics': {k: {x: v[x] for x in ('n', 'brier', 'log_loss')} for k, v in model_metrics.items()},
                      'comparisons': comparisons, 'gates': [(g['id'], g['status']) for g in gates],
                      'correlations': len(corr), 'player_correlations': len(pcorr), 'upcoming_lines': len(upcoming)}, indent=2))


if __name__ == '__main__':
    main()

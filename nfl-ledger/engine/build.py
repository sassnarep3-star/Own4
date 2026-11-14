#!/usr/bin/env python3
"""nfl-ledger — gap-closure namespace for the NFL line-origination brief (session arena/6f0b80b2-own4).

Reads the peer namespace nfl-command/data READ-ONLY (never edits it), writes:
  nfl-ledger/data/*.json|csv   derived tables (results feed, reconciliation, origination, leaderboard split,
                               demotion gate, replacement depth, correlations, questions, suggestions, flags, sources)
  nfl-ledger/index.html + pages/*.html   static site (stdlib only)

Policy: a value is written only when it is present in an official nfl.com capture or is a deterministic
computation from such values. Market prices are never written (no official source exists) — the columns are
blank and flagged. Run:  python3 nfl-ledger/engine/build.py && python3 nfl-ledger/engine/verify.py
"""
import csv
import datetime as dt
import html
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # nfl-ledger/
REPO = os.path.dirname(ROOT)                 # repository root
SRC = os.path.join(REPO, 'nfl-command', 'data')
DATA = os.path.join(ROOT, 'data')
PAGES = os.path.join(ROOT, 'pages')
CAPTURED = '2026-11-14'
REPO_BLOB = 'https://github.com/sassnarep3-star/Own4/blob/main/'
sys.path.insert(0, HERE)
import demotion  # noqa: E402  (engine/demotion.py — pure functions, tested in tests/)


def load(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return json.load(f)


def save_json(name, obj):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write('\n')


def save_csv(name, header, rows):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        w.writerows(rows)


# ---------------------------------------------------------------- official captures (fetched 2026-11-14)
# nfl.com/standings/ — transcribed from the live capture on 2026-11-14 (abbr, W, L, T, PF, PA)
LIVE_STANDINGS = {
    'BUF': (7, 1, 0, 256, 187), 'NE': (5, 4, 0, 211, 207), 'NYJ': (2, 7, 0, 182, 223), 'MIA': (1, 7, 0, 126, 200),
    'PIT': (6, 2, 0, 180, 144), 'CIN': (6, 2, 0, 240, 175), 'CLE': (5, 4, 0, 161, 196), 'BAL': (4, 5, 0, 189, 236),
    'JAX': (6, 2, 0, 229, 121), 'HOU': (3, 5, 0, 209, 192), 'IND': (2, 7, 0, 184, 249), 'TEN': (1, 7, 0, 144, 199),
    'DEN': (7, 2, 0, 198, 186), 'KC': (6, 2, 0, 202, 143), 'LV': (4, 5, 0, 238, 268), 'LAC': (0, 8, 0, 121, 219),
    'NYG': (5, 3, 1, 203, 196), 'DAL': (4, 5, 0, 246, 236), 'WAS': (3, 5, 1, 196, 223), 'PHI': (2, 7, 0, 148, 221),
    'CHI': (7, 2, 0, 241, 184), 'DET': (6, 2, 0, 222, 189), 'MIN': (6, 2, 0, 146, 116), 'GB': (6, 3, 0, 216, 191),
    'CAR': (3, 5, 0, 199, 219), 'NO': (3, 5, 0, 185, 216), 'TB': (3, 6, 0, 202, 178), 'ATL': (3, 6, 0, 188, 223),
    'SF': (7, 1, 0, 235, 156), 'SEA': (5, 4, 0, 202, 162), 'LA': (5, 4, 0, 214, 181), 'AZ': (3, 6, 0, 178, 255),
}
# nfl.com/injuries/ — Week 10 rows spot-checked live on 2026-11-14: (team, player, injury, practice, game status)
LIVE_INJURY_SPOT = [
    ('WAS', 'Lucas Patrick', 'Concussion', 'Did Not Participate In Practice', 'Out'),
    ('WAS', 'Colson Yankoff', 'Knee', 'Did Not Participate In Practice', 'Out'),
    ('NYG', 'Malik Harrison', 'Groin', 'Limited Participation in Practice', 'Questionable'),
    ('NE', 'Ben Brown', 'Knee', 'Did Not Participate In Practice', 'Out'),
    ('NE', 'A.J. Brown', 'Ankle, Knee', 'Limited Participation in Practice', 'Questionable'),
    ('DET', 'Kerby Joseph', 'Knee', 'Did Not Participate In Practice', 'Out'),
    ('DET', 'Cade Mays', 'Ankle', 'Did Not Participate In Practice', 'Out'),
    ('DET', 'D.J. Reed', 'Hip', 'Did Not Participate In Practice', 'Out'),
    ('KC', 'Mansoor Delane', 'Shoulder', 'Full Participation in Practice', 'Questionable'),
]
# nfl.com/schedules/2026/by-week/week-11 — the 13 official Week 11 games (away, home) and 6 bye clubs
OFFICIAL_WEEK11 = {frozenset(p) for p in [
    ('IND', 'HOU'), ('MIA', 'BUF'), ('BAL', 'CAR'), ('NO', 'CHI'), ('TEN', 'DAL'), ('TB', 'DET'), ('AZ', 'KC'),
    ('PIT', 'PHI'), ('NYJ', 'LAC'), ('JAX', 'NYG'), ('LV', 'DEN'), ('MIN', 'SF'), ('CIN', 'WAS')]}
OFFICIAL_WEEK11_BYES = ['ATL', 'CLE', 'GB', 'LA', 'NE', 'SEA']
LIVE_FINAL_SPOT = {'patriots-at-seahawks-2026-reg-1': ('NE', 10, 'SEA', 13)}


def american_from_prob(p):
    """Fair American moneyline from a model probability (model-derived; NOT a market price)."""
    if p is None:
        return None
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def gh(path):
    return REPO_BLOB + path


# ---------------------------------------------------------------- 1. results feed + reconciliation
def build_results():
    g = load('games_2026_verified.json')
    rows = []
    for r in g['rows']:
        margin = r['home_pts'] - r['away_pts']
        rows.append({
            'game_key': f"2026-W{r['week']:02d}-{r['away']}@{r['home']}",
            'week': r['week'], 'date': r['date'], 'away': r['away'], 'away_pts': r['away_pts'],
            'home': r['home'], 'home_pts': r['home_pts'], 'home_margin': margin,
            'total': r['away_pts'] + r['home_pts'], 'source_url': r['source_url'],
            'official_week_page': r['official_week_page'],
            'live_recheck_2026_11_14': 'yes' if r['source_url'].rsplit('/', 1)[-1] in LIVE_FINAL_SPOT else 'no',
        })
    # reconciliation: recompute W-L-T, PF, PA from the 137 rows and compare with the live standings capture
    W, L, T, PF, PA = ({} for _ in range(5))
    for r in rows:
        a, h = r['away'], r['home']
        PF[a] = PF.get(a, 0) + r['away_pts']; PA[a] = PA.get(a, 0) + r['home_pts']
        PF[h] = PF.get(h, 0) + r['home_pts']; PA[h] = PA.get(h, 0) + r['away_pts']
        for t in (a, h):
            W.setdefault(t, 0); L.setdefault(t, 0); T.setdefault(t, 0)
        if r['away_pts'] > r['home_pts']:
            W[a] += 1; L[h] += 1
        elif r['home_pts'] > r['away_pts']:
            W[h] += 1; L[a] += 1
        else:
            T[a] += 1; T[h] += 1
    recon = []
    for team in sorted(LIVE_STANDINGS):
        w, l, t, pf, pa = LIVE_STANDINGS[team]
        mine = (W[team], L[team], T[team], PF[team], PA[team])
        recon.append({
            'team': team, 'nfl_W': w, 'nfl_L': l, 'nfl_T': t, 'nfl_PF': pf, 'nfl_PA': pa,
            'calc_W': mine[0], 'calc_L': mine[1], 'calc_T': mine[2], 'calc_PF': mine[3], 'calc_PA': mine[4],
            'match': (w, l, t, pf, pa) == mine,
            'source_url': 'https://www.nfl.com/standings/', 'n_games_in_archive': W[team] + L[team] + T[team],
        })
    sum_pf = sum(LIVE_STANDINGS[t][3] for t in LIVE_STANDINGS)
    sum_pa = sum(LIVE_STANDINGS[t][4] for t in LIVE_STANDINGS)
    meta = {
        'captured_utc': CAPTURED,
        'n_games': len(rows),
        'weeks': sorted({r['week'] for r in rows}),
        'reconciliation_matches': sum(1 for r in recon if r['match']),
        'reconciliation_total': len(recon),
        'league_pf': sum_pf, 'league_pa': sum_pa,
        'league_pf_equals_pa': sum_pf == sum_pa,
        'live_game_recheck': 'W1 NE 10 @ SEA 13 (Final) re-read from nfl.com 2026-11-14; matches row.',
        'source_of_rows': 'nfl-command/data/games_2026_verified.json (peer namespace, read-only copy)',
    }
    save_json('results_feed.json', {'title': 'Verified results feed — 2026 regular season', 'meta': meta, 'rows': rows})
    save_csv('results_feed.csv', list(rows[0].keys()), [list(r.values()) for r in rows])
    save_json('standings_reconciliation.json', {'title': 'Standings reconciliation (nfl.com live vs archive)', 'meta': meta, 'rows': recon})
    return rows, recon, meta


# ---------------------------------------------------------------- 2. price-snapshot store (schema only)
PRICE_FIELDS = ['snapshot_id', 'game_key', 'market', 'snapshot', 'book', 'captured_utc', 'line', 'price_american',
                'source_url', 'source_is_official', 'status']


def build_price_store():
    schema = {
        'title': 'Price-snapshot store — opening and closing numbers for every originated market',
        'status': 'EMPTY BY POLICY — 0 rows. No official source publishes betting lines (see F-L1).',
        'markets_in_order': ['spread (side)', 'total', 'moneyline'],
        'snapshots': ['open (first capture after the line is posted)', 'close (last capture before kickoff)'],
        'fields': PRICE_FIELDS,
        'validation_rules': [
            'snapshot_id unique; game_key must exist in results_feed.json',
            'market in {spread, total, moneyline}; snapshot in {open, close}; close captured_utc < kickoff',
            'source_url required; source_is_official must be true for any value shown on an official-only page',
            'a missing open or close is stored as status=missing (never back-filled or estimated)',
            'a row without a capture timestamp is rejected',
        ],
        'allowed_official_domains': ['https://www.nfl.com/'],
        'decision_needed': 'A licensed odds archive is not an official source. Choose SUG-L1 (licensed feed with a '
                           'labelled status) or keep the store empty. No value is entered until that decision is made.',
        'rows_stored': 0,
        'originated_markets_with_prices': 0,
    }
    save_json('price_snapshots_schema.json', schema)
    save_csv('price_snapshots.csv', PRICE_FIELDS, [])
    return schema


# ---------------------------------------------------------------- 3. origination (side -> total -> moneyline)
def build_origination():
    ol = load('own_lines_week11.json')['week11_own_lines']
    rows = []
    for i, g in enumerate(ol, 1):  # nfl-command order = official schedule order
        fair_margin = g['spread_home']
        fair_total = g['total']
        p = g['p_home_win']
        rows.append({
            'order': i, 'game': f"{g['away']} @ {g['home']}", 'kickoff_et': f"{g['date']} {g['time']}",
            'step1_fair_home_margin': fair_margin, 'step1_market_home_spread': '', 'step1_difference': '',
            'step2_fair_total': fair_total, 'step2_market_total': '', 'step2_difference': '',
            'step3_p_home_win': p, 'step3_fair_ml_home': american_from_prob(p), 'step3_market_ml_home': '',
            'step3_difference': '', 'n_graded': 0, 'source_url': g['game_url'],
        })
    # Verify the slate itself against the official Week 11 schedule (AZ = Arizona on nfl.com)
    slate_ok = {frozenset((r['game'].split(' @ ')[0], r['game'].split(' @ ')[1])) for r in rows} == OFFICIAL_WEEK11
    header = list(rows[0].keys())
    save_json('originated_lines_week11.json', {
        'title': 'Week 11 originated lines — origination order: side, then total, then moneyline',
        'meta': {'captured_utc': CAPTURED, 'slate_matches_official_schedule': slate_ok, 'n_games': len(rows),
                 'byes': OFFICIAL_WEEK11_BYES,
                 'market_columns': 'blank by policy: no official price source (F-L1)',
                 'ml_method': 'American odds derived from the model win probability (not a market price)',
                 'source_schedule': 'https://www.nfl.com/schedules/2026/by-week/week-11'},
        'rows': rows})
    save_csv('originated_lines_week11.csv', header, [list(r.values()) for r in rows])
    return rows, slate_ok


# ---------------------------------------------------------------- 4. leaderboard split (signal vs staking)
def build_leaderboard():
    lb = load('leaderboard.json')
    strategies = []
    for r in lb['results']:
        gates = r['gates']
        n_pass = sum(1 for v in gates.values() if str(v).startswith('pass'))
        strategies.append({
            'id': r['id'], 'name': r['name'], 'bet_type': r.get('bet_type', ''),
            'signal_gates_pass': n_pass, 'signal_gates_total': len(gates),
            'signal_status': 'NOT PROMOTED — ' + ('blocked: no market prices' if 'BLOCKED' in r['status'] else 'gates failed'),
            'signal_n_graded': 0,
            'staking_roi': '', 'staking_drawdown': '', 'staking_n': 0,
            'reward_eligible': False,
            'source_url': gh('nfl-command/data/leaderboard.json'),
        })
    lt = lb['luck_tests']
    model = {
        'id': 'M1', 'name': 'Own margin/total model (ridge-SRS, walk-forward) — margin vs naive baseline',
        'bet_type': 'Model signal (not a bet)',
        'signal_gates_pass': None, 'signal_gates_total': None,
        'signal_status': 'NOT PROMOTED — holdout MAE bootstrap 95%% CI %s includes 0' % lt['bootstrap_95ci_mae_improvement'],
        'signal_n_graded': lb['holdout_metrics']['n'],
        'staking_roi': '', 'staking_drawdown': '', 'staking_n': 0, 'reward_eligible': False,
        'signal_evidence': {
            'holdout_accuracy': round(lb['holdout_metrics']['accuracy'], 4),
            'naive_accuracy': round(lb['holdout_metrics']['base_accuracy'], 4),
            'placebo_p_accuracy': lt['placebo_p_accuracy_holdout'],
            'placebo_p_mae': lt['placebo_p_mae_improvement'],
            'mae_improvement_per_game': lt['mae_improvement_per_game'],
            'bootstrap_95ci_mae_improvement': lt['bootstrap_95ci_mae_improvement'],
        },
        'source_url': gh('nfl-command/data/leaderboard.json'),
    }
    rules = {
        'rule_1': 'Ranking uses signal columns ONLY. Staking columns are displayed but never change rank.',
        'rule_2': 'A strategy is reward-eligible only if signal gates pass AND n >= 300 graded selections (G2).',
        'rule_3': 'Staking results (ROI, bankroll path) cannot offset a failed signal gate; a strong staking run '
                  'with a failed signal is labelled "signal fail — staking ignored".',
        'rule_4': 'Missing staking or price data is blank and makes the strategy paper-only, never live.',
    }
    save_json('leaderboard_split.json', {
        'title': 'Leaderboard — signal and staking are scored separately', 'captured_utc': CAPTURED,
        'rules': rules, 'rows': strategies + [model],
        'reward_pool': lb['competition_design']['reward_pool'],
    })
    return strategies, model, rules


# ---------------------------------------------------------------- 5. demotion gate (data + engine)
def build_demotion(strategies):
    spec = demotion.spec()
    state_rows = []
    for s in strategies + []:
        state_rows.append({'id': s['id'], 'name': s['name'], 'stage': 'registered',
                           'stage_reason': 'no priced paper selections (no price archive, F-L1)',
                           'triggers_evaluable': 'no', 'source_url': s['source_url']})
    save_json('demotion_gate.json', {'title': 'Demotion gate — sends a live strategy back to paper',
                                     'captured_utc': CAPTURED, 'spec': spec, 'current_state': state_rows})
    return spec


# ---------------------------------------------------------------- 6. replacement depth (week 10 official rows)
def build_depth():
    inj = load('injuries_week10.json')
    rows = []
    for r in inj['rows']:
        if r['game_status'] not in ('Out', 'Questionable'):
            continue
        rows.append({
            'team': r['team'], 'player': r['player'], 'position': r['position'], 'side': r['side'],
            'injury': r['injury'], 'practice_status': r['practice_status'], 'game_status': r['game_status'],
            'starter_backup_official': '', 'replacement_player': '', 'replacement_depth_rank': '',
            'replacement_depth_tier': '', 'n_snaps_replacement': '', 'source_url': 'https://www.nfl.com/injuries/',
        })
    rows.sort(key=lambda x: (x['game_status'] != 'Out', x['team'], x['player']))
    spot = []
    PRACTICE = {'Did Not Participate In Practice': 'DNP', 'Limited Participation in Practice': 'Limited',
                'Full Participation in Practice': 'Full'}   # nfl.com wording -> stored abbreviation
    by_player = {(r['team'], r['player']): r for r in inj['rows']}
    for t in LIVE_INJURY_SPOT:
        st = by_player.get((t[0], t[1]))
        ok = bool(st) and st['injury'] == t[2] and st['practice_status'] == PRACTICE[t[3]] and st['game_status'] == t[4]
        diff = '' if ok else ('not in stored file' if not st else
                              'stored: injury=%r practice=%r game=%r' % (st['injury'], st['practice_status'], st['game_status']))
        spot.append({'team': t[0], 'player': t[1], 'live_nfl_com_row': list(t), 'matches_stored_row': ok,
                     'difference': diff})
    n_ok = sum(1 for s in spot if s['matches_stored_row'])
    meta = {'week': inj['week'], 'captured_utc': CAPTURED, 'n_rows': len(rows),
            'live_spot_check': spot, 'live_spot_check_passed': n_ok, 'live_spot_check_total': len(spot),
            'depth_status': 'UNVERIFIED — no official depth chart found in the pages checked '
                            '(nfl.com injuries, schedules, standings, game pages). Starter/backup and replacement '
                            'rank are blank by policy (F-L2).'}
    save_json('replacement_depth_week10.json', {'title': 'Replacement depth — Week 10 Out / Questionable players',
                                                'meta': meta, 'rows': rows})
    save_csv('replacement_depth_week10.csv', list(rows[0].keys()), [list(r.values()) for r in rows])
    return rows, meta


# ---------------------------------------------------------------- 7. correlations (copied with n)
def build_correlations():
    c = load('correlations.json')
    rows = []
    for m in c['measured']:
        rows.append({'pair': m['pair'], 'phi': m['phi'], 'n': m['n'], 'joint_rate': m['joint_rate'],
                     'independence_product': m['independence_product'],
                     'split_half_phi_early': m.get('split_half_phi_early', ''),
                     'split_half_phi_late': m.get('split_half_phi_late', ''),
                     'source_url': 'https://www.nfl.com/schedules/2026/'})
    blanks = [{'item': b['item'], 'reason': b['reason'], 'flag': b.get('flag', '')} for b in c['blank_unverified']]
    save_json('correlations.json', {'title': 'Correlations — official-source numbers only, n published with each value',
                                    'captured_utc': CAPTURED, 'method': c['method'], 'scope_warning': c['scope_warning'],
                                    'rows': rows, 'blank_unverified': blanks,
                                    'copied_from': 'nfl-command/data/correlations.json (read-only)'})
    return rows, blanks


# ---------------------------------------------------------------- 8. questions, suggestions, flags, sources
QUESTIONS = [
    ('Q-L1', 'Prices', 'Where can opening and closing lines for every originated market be obtained, with capture timestamps?',
     'No nfl.com page checked (standings, schedules, injuries, game pages) publishes betting lines.',
     'Whether any rights-cleared archive exists, its cost, and whether it may be stored here.', 'OPEN',
     'Decision on SUG-L1 (licensed feed with a labelled status).'),
    ('Q-L2', 'Results', 'Is the 2026 results feed complete and correct through Week 10?',
     'All 137 games are read from nfl.com game-page URLs; W-L-T/PF/PA reconcile 32/32 with the live standings captured 2026-11-14.',
     'Week 10 Sunday and Monday results (Nov 15–16) are not yet played as of the capture date.', 'ANSWERED (through W10 TNF)',
     'Re-run build after Nov 16 with a new capture.'),
    ('Q-L3', 'Depth', 'Which replacement is the depth chart rank of each Out/Questionable starter?',
     'Week 10 official injury rows (14 Out, 11 Questionable). Live spot check: 7 of 9 sample rows match; 2 differ (F-L9).',
     'Official starter/backup depth is not published on the pages checked; replacement rank is unknown.', 'OPEN',
     'Discover an official depth-chart source (SUG-L3).'),
    ('Q-L4', 'Signal', 'Does our model beat the naive baseline out of sample with enough certainty to earn a gate pass?',
     'Holdout (weeks 8–10, n=30): accuracy 0.733 vs 0.500; placebo p 0.0076 for accuracy.',
     'MAE-improvement bootstrap 95% CI [-2.47, 3.74] includes 0; holdout n=30 is far below G2 (300).', 'OPEN — NOT PROVEN',
     'More prospective weeks; more graded selections.'),
    ('Q-L5', 'Market', 'What closing-line beat rate does any strategy achieve?',
     'Nothing is measurable: no closing numbers exist in the repository.', 'Everything.', 'UNANSWERABLE NOW',
     'Depends on Q-L1.'),
    ('Q-L6', 'Staking', 'What stake size and bankroll rule should the staking column use?',
     'nfl-command gates.json sets a 2% maximum per selection and a -15% drawdown stop.',
     'Whether the bankroll rule is acceptable to the owner; no bankroll is defined.', 'OPEN (decision)',
     'Owner decision.'),
    ('Q-L7', 'Correlation', 'Are the correlations stable enough to use in pricing?',
     'Two model-internal phi values measured (n=105 each), with split-half values.',
     'Market correlations cannot be computed (Q-L1); player-prop correlations have no official data.', 'PARTIAL',
     'Q-L1 and an official player-log source (SUG-L4).'),
    ('Q-L8', 'Governance', 'Should any strategy be live at all this season?',
     'No strategy passes all gates (leaderboard.json: 0 of 6 registered).', 'Requires Q-L1, Q-L4 answers first.',
     'OPEN (decision)', 'Owner decision; the recommended default is paper-only.'),
]

SUGGESTIONS = [
    ('SUG-L1', 'Licensed closing-line feed, with a labelled "non-official" status',
     'Price-snapshot store is empty; every market-based gate (G6) and the demotion gate are unevaluable.',
     'Procure a rights-cleared archive of opening and closing spreads/totals/moneylines for 2026 weeks 1–18. Store '
     'with capture timestamps; show "licensed, non-official" status on every price cell.',
     'high', 'medium (cost, licence)', 'Relaxes the official-only rule for price data only — a policy change.',
     'Owner approval of the policy change; licence check.'),
    ('SUG-L2', 'Keep the price store empty and stay in research mode',
     'Without prices, no ROI or CLV can be computed honestly.',
     'Publish the framework only; do not paper-trade; revisit at the start of the 2027 season.',
     'low (no new information)', 'none', 'No validation of any strategy this season.',
     'Owner choice; this is the default if SUG-L1 is not chosen.'),
    ('SUG-L3', 'Find an official depth-chart source for starter/backup status',
     'Replacement depth cannot be tracked, so depth-based demotion (D5) and the injury model cannot run.',
     'Search nfl.com team pages and official NFL data pages for a published depth chart; if none exists, record the gap '
     'as permanent and use only official injury designations.',
     'medium', 'low (discovery step)', 'If none exists, depth tracking stays impossible.',
     'Discovery task; no code change until a source is confirmed.'),
    ('SUG-L4', 'Official per-game player logs for player-prop research',
     'Player-prop combos (S5, S6) have no official data source.',
     'Identify an official player-statistics page with per-game logs; add capture only after verification.',
     'medium', 'medium', 'Player-prop prices still needed for grading.', 'Discovery task.'),
    ('SUG-L5', 'Extend the walk-forward holdout before any promotion',
     'Holdout n=30 cannot support a signal claim (Q-L4).',
     'Keep predicting prospectively through Week 18 and re-run the frozen gates on the enlarged holdout.',
     'medium', 'low', 'Longer wait before any decision.', 'None; can start immediately.'),
    ('SUG-L6', 'Consolidate the 16 NFL namespaces into one generator',
     'Parallel namespaces repeat content and drift (the root generator drops hand-added links; see F-L4).',
     'Merge into one source of truth in a dedicated integration task; leave old URLs as redirects.',
     'medium', 'high (touches many files)', 'Risk of broken links during migration.',
     'Owner choice; should not be done in parallel with other sessions.'),
]

FLAGS = [
    ('F-L1', 'high', 'No betting-line data exists in any official source checked',
     'Price-snapshot store, market columns, closing-line gate G6 and all ROI/CLV figures are BLANK. '
     'Market lines are not published on the nfl.com pages checked (standings, schedules, injuries, game pages).',
     ['https://www.nfl.com/schedules/2026/by-week/week-11', 'https://www.nfl.com/standings/'],
     'SUG-L1 decision.'),
    ('F-L2', 'high', 'No official starter/backup depth chart found',
     'Replacement depth rank, replacement player and depth tier are blank on every Week 10 row. The injury report '
     'shows practice and game status only.',
     ['https://www.nfl.com/injuries/'], 'SUG-L3 discovery.'),
    ('F-L3', 'high', 'Model signal not proven; holdout too small',
     'Holdout n=30; bootstrap 95% CI for MAE improvement [-2.47, 3.74] includes 0; 0 of 6 strategies pass all gates.',
     ['https://www.nfl.com/standings/'], 'More prospective weeks (SUG-L5).'),
    ('F-L4', 'medium', 'Root generator drops hand-added NFL links (peer-logged defect, still present)',
     'verification/build.py regenerates index.html without hand-added NFL groups; nfl-ledger is NOT linked from the root '
     'page (request R-L1 logged to the integration session). Verified by grep: no hits for "nfl-ledger" in index.html.',
     ['https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md'], 'Integration session (R-L1).'),
    ('F-L5', 'medium', '"Gates frozen before backtest" cannot be confirmed from this clone',
     'nfl-command/data/gates.json states it was frozen at 2026-11-13T21:50Z before the backtest. In this clone the file\'s '
     'git history shows only the merge commit 02a8bdf (2026-11-14T07:27:34+09:00), so the earlier commit timing is not '
     'independently checkable here. Not used as evidence.',
     [gh('nfl-command/data/gates.json')], 'Owner to confirm from the original branch history.'),
    ('F-L6', 'low', 'Week 10 injury page: Sunday Nov 15 games listed under "Week 10"',
     'Checked against the official schedule convention: Week 10 TNF was Nov 12 and Week 11 starts Nov 19 (TNF). The '
     'Sunday Nov 15 games are Week 10, so the label is consistent. Recorded to show it was checked, not as an error.',
     ['https://www.nfl.com/injuries/', 'https://www.nfl.com/schedules/2026/by-week/week-11'], 'None — informational.'),
    ('F-L7', 'low', 'Abbreviation mismatch: Arizona is "AZ" on nfl.com, "ARI" in common usage',
     'The stored slate correctly uses AZ. A reviewer comparing with other feeds must map ARI→AZ. No value changed.',
     ['https://www.nfl.com/schedules/2026/by-week/week-11'], 'None.'),
    ('F-L9', 'high', 'Two Week 10 injury rows differ from the live nfl.com report (2026-11-14)',
     'Kerby Joseph (DET, S, knee): stored practice "Full" vs live "Did Not Participate In Practice" (game status Out in both). '
     'Mansoor Delane (KC, CB): stored injury and game status blank vs live "Shoulder" / "Questionable". Either the report was '
     'updated after the 2026-11-13 capture or the stored row is wrong. Not corrected here: the stored file is peer data and the '
     'live page is not a snapshot of a fixed time. Re-capture needed.',
     ['https://www.nfl.com/injuries/'], 'Re-capture the official Week 10 report; owner of nfl-command to confirm.'),
    ('F-L8', 'medium', 'Fair moneyline values are model-derived, not market prices',
     'American odds on the origination page are converted from the model probability. They are shown as a fair line only; '
     'the market column is blank.',
     [gh('nfl-command/data/own_lines_week11.json')], 'Labelled in the table header.'),
]

SOURCES = [
    ('NFL standings (live, all 32 clubs)', 'https://www.nfl.com/standings/', 'Reconciliation of 137 games; league PF=PA',
     CAPTURED, True),
    ('NFL Week 11 schedule (13 games + 6 byes)', 'https://www.nfl.com/schedules/2026/by-week/week-11', 'Official slate check',
     CAPTURED, True),
    ('NFL Week 10 injury report', 'https://www.nfl.com/injuries/', '14 Out / 11 Questionable rows; 9-row live spot check',
     CAPTURED, True),
    ('NFL game page W1 NE 10 @ SEA 13', 'https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1',
     'Final score re-read', CAPTURED, True),
    ('NFL Week 10 schedule (peer capture)', 'https://www.nfl.com/schedules/2026/by-week/week-10',
     'Used in peer namespace; not re-fetched this session', '2026-11-13 (peer)', True),
    ('nfl-command peer data (read-only)', gh('nfl-command/data/'), 'All derived model values, gates, correlations',
     '2026-11-13 (peer)', False),
]


def build_text_data():
    save_json('questions.json', {'title': 'Questions, information and answers', 'captured_utc': CAPTURED,
                                 'rows': [dict(zip(['id', 'topic', 'question', 'known', 'unknown', 'status', 'unlock'], q))
                                          for q in QUESTIONS]})
    save_json('suggestions.json', {'title': 'Suggestions — choose a path before anything is implemented',
                                   'captured_utc': CAPTURED,
                                   'how_to_read': 'Nothing here has been implemented. Pick one path per row; implementation starts only after the choice.',
                                   'rows': [dict(zip(['id', 'title', 'problem', 'proposal', 'impact', 'effort', 'risk',
                                                      'prerequisites'], s), status='AWAITING OWNER CHOICE')
                                            for s in SUGGESTIONS]})
    save_json('flags.json', {'title': 'Flagged for Review — irregularities and unverified items', 'captured_utc': CAPTURED,
                             'policy': 'Flags never block publication. Unverified values are BLANK, never zero or inferred.',
                             'rows': [dict(zip(['id', 'severity', 'item', 'detail', 'sources', 'next_step'], f)) for f in FLAGS]})
    save_json('sources.json', {'title': 'Source register', 'captured_utc': CAPTURED,
                               'rows': [dict(zip(['source', 'url', 'used_for', 'captured', 'official'], s)) for s in SOURCES]})


def main():
    os.makedirs(DATA, exist_ok=True)
    results, recon, meta = build_results()
    build_price_store()
    orig_rows, slate_ok = build_origination()
    strategies, model, rules = build_leaderboard()
    build_demotion(strategies)
    depth_rows, depth_meta = build_depth()
    corr_rows, corr_blanks = build_correlations()
    build_text_data()
    import render  # noqa: E402
    render.render_all(ROOT)
    print('results', meta['n_games'], 'recon', meta['reconciliation_matches'], '/', meta['reconciliation_total'],
          'slate_ok', slate_ok, 'depth_rows', len(depth_rows), 'depth_spot_ok', depth_meta['live_spot_check_passed'],
          '/', depth_meta['live_spot_check_total'],
          'corr_rows', len(corr_rows))


if __name__ == '__main__':
    main()

"""Static HTML renderer for nfl-ledger (stdlib only). Reads nfl-ledger/data/*.json written by build.py."""
import html
import json
import os

CSS = """
:root{--ink:#1d2330;--mut:#5b6472;--line:#e3e7ee;--bg:#f7f8fb;--acc:#1f5fbf;--warn:#fff4d6;--bad:#fde2e1;--ok:#e3f5e9}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#fff;border-bottom:1px solid var(--line);padding:14px 22px;position:sticky;top:0;z-index:2}
header a.brand{font-weight:700;color:var(--ink);text-decoration:none;margin-right:18px}
nav a{color:var(--acc);text-decoration:none;margin-right:12px;font-size:14px;white-space:nowrap}
main{max-width:1200px;margin:0 auto;padding:22px}
h1{font-size:24px;margin:6px 0 4px}h2{font-size:18px;margin:26px 0 8px}p.lead{color:var(--mut);margin-top:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:14px 0}
.tile{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tile b{display:block;font-size:22px}.tile span{color:var(--mut);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.card a{font-weight:600;color:var(--acc);text-decoration:none}.card p{margin:6px 0 0;color:var(--mut);font-size:14px}
.banner{background:var(--warn);border:1px solid #f0d78a;border-radius:8px;padding:10px 14px;margin:12px 0}
.banner.bad{background:var(--bad);border-color:#f2b8b5}.banner.ok{background:var(--ok);border-color:#b7e1c4}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:13px;margin:8px 0 14px}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef2f8;position:sticky;top:0;font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td.blank{background:repeating-linear-gradient(45deg,#fff,#fff 6px,#fbf6e6 6px,#fbf6e6 12px)}
td.fail{color:#9b1c1c}td.pass{color:#166534}
.wrap{overflow-x:auto}
.note{color:var(--mut);font-size:13px}
footer{color:var(--mut);font-size:12px;border-top:1px solid var(--line);margin-top:28px;padding:14px 22px;text-align:center}
code{background:#eef2f8;padding:1px 4px;border-radius:4px}
"""

NAV = [
    ('index.html', 'Dashboard'), ('pages/executive-summary.html', 'Executive summary'),
    ('pages/results-feed.html', 'Results feed'), ('pages/price-snapshots.html', 'Price snapshots'),
    ('pages/origination.html', 'Origination'), ('pages/leaderboard.html', 'Leaderboard'),
    ('pages/demotion.html', 'Demotion gate'), ('pages/replacement-depth.html', 'Replacement depth'),
    ('pages/correlations.html', 'Correlations'), ('pages/questions.html', 'Questions'),
    ('pages/suggestions.html', 'Suggestions'), ('pages/flagged.html', 'Flagged for Review'),
    ('pages/sources.html', 'Sources'),
]

FOOTER = ('Analytical research only — not wagering advice. Unverified values are blank, never zero or inferred. '
          'Problem gambling help (US): 1-800-MY-RESET · <a href="https://www.ncpgambling.org/help-treatment">'
          'ncpgambling.org/help-treatment</a>.')


def e(x):
    return html.escape('' if x is None else str(x))


def link(url, label=None):
    if not url:
        return ''
    return '<a href="%s" rel="noopener">%s</a>' % (e(url), e(label or url))


def table(headers, rows, num_cols=(), cls=''):
    out = ['<div class="wrap"><table class="%s"><thead><tr>' % cls]
    out += ['<th>%s</th>' % e(h) for h in headers]
    out.append('</tr></thead><tbody>')
    for r in rows:
        out.append('<tr>')
        for i, c in enumerate(r):
            raw = c if isinstance(c, Raw) else e(c)
            klass = []
            if i in num_cols:
                klass.append('num')
            if c == '' or c is None:
                klass.append('blank')
            out.append('<td class="%s">%s</td>' % (' '.join(klass), raw))
        out.append('</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


class Raw(str):
    """Marks an already-escaped HTML fragment (links)."""


def page(root_rel, title, lead, body, active):
    nav = ''.join('<a href="%s%s"%s>%s</a>' % (root_rel, href, ' aria-current="page"' if href.endswith(active) and active else '', e(label))
                  for href, label in NAV)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s · NFL Ledger</title><style>%s</style></head><body>'
            '<header><a class="brand" href="%sindex.html">NFL Ledger</a><nav>%s</nav></header>'
            '<main><h1>%s</h1><p class="lead">%s</p>%s</main>'
            '<footer>%s</footer></body></html>') % (e(title), CSS, root_rel, nav, e(title), e(lead), body, FOOTER)


def load(root, rel):
    with open(os.path.join(root, 'data', rel), encoding='utf-8') as f:
        return json.load(f)


def src(url, label='official source'):
    return Raw(link(url, label))


def render_all(root):
    R = lambda rel: load(root, rel)  # noqa: E731
    res = R('results_feed.json')
    rec = R('standings_reconciliation.json')
    sch = R('price_snapshots_schema.json')
    orig = R('originated_lines_week11.json')
    lb = R('leaderboard_split.json')
    dem = R('demotion_gate.json')
    dep = R('replacement_depth_week10.json')
    cor = R('correlations.json')
    qs = R('questions.json')
    sg = R('suggestions.json')
    fl = R('flags.json')
    so = R('sources.json')
    meta = res['meta']
    pages = {}

    # --- dashboard
    tiles = [
        (meta['n_games'], 'verified 2026 games (W1–W10) from nfl.com game URLs'),
        ('%d / %d' % (meta['reconciliation_matches'], meta['reconciliation_total']), 'clubs reconciled to the live nfl.com standings'),
        (0, 'price rows stored (no official price source — F-L1)'),
        (0, 'strategies live · 0 of 6 pass all gates'),
        (len(dep['rows']), 'Week 10 Out/Questionable rows; replacement depth blank (F-L2)'),
        (len(fl['rows']), 'items on Flagged for Review'),
    ]
    tile_html = ''.join('<div class="tile"><b>%s</b><span>%s</span></div>' % (e(a), e(b)) for a, b in tiles)
    cards = [
        ('pages/executive-summary.html', 'Executive summary', 'What is known, what is not, and the decisions needed.'),
        ('pages/results-feed.html', 'Results feed & reconciliation', '137 games with nfl.com links; 32-club standings check.'),
        ('pages/price-snapshots.html', 'Price-snapshot store', 'Opening and closing schema; empty by policy.'),
        ('pages/origination.html', 'Origination — Week 11', 'Side → total → moneyline; fair, market and difference columns.'),
        ('pages/leaderboard.html', 'Leaderboard: signal vs staking', 'Ranking uses signal only; staking cannot mask a bad signal.'),
        ('pages/demotion.html', 'Demotion gate', 'Live → paper triggers; promotion rules; missing-data rule.'),
        ('pages/replacement-depth.html', 'Replacement depth', 'Week 10 injuries and the depth-rank schema.'),
        ('pages/correlations.html', 'Correlations (with n)', 'Model-internal only; market correlations unavailable.'),
        ('pages/questions.html', 'Questions & answers', 'What is known, unknown, and what would unlock each decision.'),
        ('pages/suggestions.html', 'Suggestions (choose a path)', 'Nothing implemented until you pick a path.'),
        ('pages/flagged.html', 'Flagged for Review', 'Irregularities and unverified items with source links.'),
        ('pages/sources.html', 'Sources', 'Every official page captured this session, with date.'),
    ]
    card_html = ''.join('<div class="card"><a href="%s">%s</a><p>%s</p></div>' % (e(h), e(t), e(d)) for h, t, d in cards)
    body = ('<div class="banner">Status: <b>research only.</b> No market prices exist in any official source, so no ROI, '
            'closing-line result or live strategy can be published. Every number below is either an official nfl.com '
            'value or a computation from one.</div>'
            '<div class="tiles">%s</div><h2>Sections</h2><div class="cards">%s</div>') % (tile_html, card_html)
    pages['index.html'] = page('', 'NFL Ledger — dashboard',
                               'Results, prices, origination, leaderboard, demotion and depth — one place, every row sourced.',
                               body, 'index.html')

    # --- executive summary
    ok_w11 = orig['meta']['slate_matches_official_schedule']
    body = """
<h2>Bottom line</h2>
<ul>
<li><b>The results feed is solid.</b> %d games (weeks %s–%s) reconcile %d of %d clubs exactly with the live nfl.com
standings captured %s. League points for equal points against (%d = %d).</li>
<li><b>No strategy can be evaluated for profit.</b> Official sources do not publish betting lines. Opening and closing
prices, ROI, closing-line beat rate and market correlations are therefore blank. Nothing here claims a profit.</li>
<li><b>The model has not shown a proven signal.</b> On the holdout (weeks 8–10, n=30) accuracy was 0.733 against a
0.500 naive baseline, but the bootstrap 95%% interval for the MAE improvement, %s, includes 0. Gates require n ≥ 300.</li>
<li><b>Zero strategies are live, and none may be.</b> The demotion gate is written and unit-tested, but it has no priced
selections to act on.</li>
<li><b>Week 11 is ready for origination.</b> %s</li>
</ul>
<h2>What was built this session</h2>
<ul>
<li>Price-snapshot store: opening and closing schema, validation rules, empty store (no invented rows).</li>
<li>Results feed: 137 games with official game-page links; standings reconciliation 32/32 against nfl.com.</li>
<li>Origination order enforced in the table: <b>side → total → moneyline</b>, each with fair, market and difference columns.</li>
<li>Leaderboard split: signal and staking in separate columns; ranking uses signal only.</li>
<li>Demotion gate (D1–D6) with promotion rules P1–P5, implemented as pure functions and tested with synthetic inputs.</li>
<li>Replacement-depth schema for Week 10 Out/Questionable players; depth fields blank because no official depth chart was found.</li>
</ul>
<h2>Decisions needed from you (no action is taken until you choose)</h2>
<ol>
<li><b>Price data (SUG-L1 vs SUG-L2):</b> allow a licensed, labelled, non-official odds archive, or stay in research mode.</li>
<li><b>Depth data (SUG-L3):</b> approve a discovery step to find an official depth chart, or accept permanent blanks.</li>
<li><b>Staking (Q-L6):</b> approve a bankroll rule for the staking column. Current draft: 2%% per selection, −15%% drawdown stop.</li>
<li><b>Live status (Q-L8):</b> confirm the default of paper-only for this season.</li>
</ol>
<p class="note">Sources: see <a href="sources.html">Sources</a> and <a href="flagged.html">Flagged for Review</a>.</p>
""" % (meta['n_games'], meta['weeks'][0], meta['weeks'][-1], meta['reconciliation_matches'], meta['reconciliation_total'],
       meta['captured_utc'], meta['league_pf'], meta['league_pa'],
       lb['rows'][-1]['signal_evidence']['bootstrap_95ci_mae_improvement'],
       'Official 13-game slate matches the nfl.com Week 11 schedule (%s). Fair lines are in the table; market columns are blank.' %
       ('verified' if ok_w11 else 'NOT VERIFIED — see flags'))
    pages['pages/executive-summary.html'] = page('../', 'Executive summary',
                                                  'Plain-language summary of what is known and what is not.', body, 'executive-summary.html')

    # --- results feed
    recon_rows = []
    for r in rec['rows']:
        recon_rows.append([r['team'], '%d-%d-%d' % (r['nfl_W'], r['nfl_L'], r['nfl_T']), r['nfl_PF'], r['nfl_PA'],
                           '%d-%d-%d' % (r['calc_W'], r['calc_L'], r['calc_T']), r['calc_PF'], r['calc_PA'],
                           'match' if r['match'] else 'MISMATCH', src(r['source_url'], 'nfl.com/standings')])
    rrows = []
    for r in res['rows']:
        rrows.append([r['week'], r['date'], r['away'], r['away_pts'], r['home'], r['home_pts'], r['home_margin'],
                      r['total'], 'yes' if r['live_recheck_2026_11_14'] == 'yes' else 'no',
                      src(r['source_url'], 'nfl.com game page')])
    body = ('<div class="banner ok">Reconciliation: %d of %d clubs match exactly (W, L, T, PF, PA). '
            'Standings captured %s. League PF %d = PA %d.</div>'
            '<h2>Standings reconciliation (32 clubs)</h2>%s'
            '<h2>Games (%d)</h2><p class="note">Margin = home minus away. Source column links the official nfl.com game page '
            'for every row. "Re-read 2026-11-14" marks rows read again live.</p>%s') % (
        meta['reconciliation_matches'], meta['reconciliation_total'], meta['captured_utc'], meta['league_pf'], meta['league_pa'],
        table(['Club', 'nfl.com W-L-T', 'PF', 'PA', 'Recomputed W-L-T', 'PF', 'PA', 'Result', 'Source'], recon_rows, num_cols=(2, 3, 5, 6)),
        meta['n_games'],
        table(['Wk', 'Date', 'Away', 'Pts', 'Home', 'Pts', 'Margin', 'Total', 'Re-read 2026-11-14', 'Source'], rrows,
              num_cols=(0, 3, 5, 6, 7)))
    pages['pages/results-feed.html'] = page('../', 'Results feed & reconciliation',
                                            'Verified 2026 games and the standings check that proves the feed is complete.',
                                            body, 'results-feed.html')

    # --- price snapshots
    body = ('<div class="banner bad"><b>Empty by policy.</b> %s</div>'
            '<h2>Schema</h2>%s<h2>Validation rules</h2><ul>%s</ul>'
            '<h2>Store contents</h2>%s<p class="note">%s</p>') % (
        e(sch['status']),
        table(['Field', 'Meaning'], cls='ref', rows=[
            ['snapshot_id', 'Unique id for one captured price'], ['game_key', 'Joins to results_feed (e.g. 2026-W11-IND@HOU)'],
            ['market', 'spread (side) · total · moneyline'], ['snapshot', 'open (first capture) · close (last before kickoff)'],
            ['book', 'Source of the number (must be named)'], ['captured_utc', 'Capture timestamp (required)'],
            ['line / price_american', 'The number as captured'], ['source_url', 'Page the number came from (required)'],
            ['source_is_official', 'true only for official nfl.com pages'], ['status', 'ok · missing (never back-filled)'],
        ]),
        ''.join('<li>%s</li>' % e(r) for r in sch['validation_rules']),
        table(['snapshot_id', 'game_key', 'market', 'snapshot', 'captured_utc', 'line', 'price', 'source'],
              [['—', '—', '—', '—', '—', '', '', src('https://www.nfl.com/schedules/2026/by-week/week-11', 'no price on this official page')]]),
        'Decision needed: %s' % sch['decision_needed'])
    pages['pages/price-snapshots.html'] = page('../', 'Price-snapshot store',
                                               'Opening and closing numbers for every market we originate — schema ready, data not available.',
                                               body, 'price-snapshots.html')

    # --- origination
    orows = []
    for r in orig['rows']:
        orows.append([r['order'], r['game'], r['kickoff_et'],
                      # step 1 side
                      '%+.1f' % r['step1_fair_home_margin'], '', '',
                      # step 2 total
                      '%.1f' % r['step2_fair_total'], '', '',
                      # step 3 moneyline
                      '%.3f' % r['step3_p_home_win'], ('%+d' % r['step3_fair_ml_home']), '', '',
                      r['n_graded'], src(r['source_url'], 'nfl.com game page')])
    headers = ['#', 'Game (away @ home)', 'Kickoff (ET)',
               'S1 fair home margin', 'S1 market home spread', 'S1 difference',
               'S2 fair total', 'S2 market total', 'S2 difference',
               'S3 P(home win)', 'S3 fair ML home', 'S3 market ML home', 'S3 difference',
               'n graded', 'Source']
    body = ('<div class="banner">Origination order is <b>side (S1) → total (S2) → moneyline (S3)</b>. The model fair line '
            'is shown; market and difference columns are blank because no official price exists (F-L1). '
            'Fair ML is converted from the model probability (F-L8). Slate check vs official schedule: <b>%s</b>. '
            'Byes: %s.</div>%s<p class="note">Fair margin is expected home points minus away points. '
            'Model: nfl-command ridge-SRS (no market inputs).</p>') % (
        'verified (13 games, 13 matches)' if orig['meta']['slate_matches_official_schedule'] else 'NOT VERIFIED',
        ', '.join(orig['meta']['byes']), table(headers, orows, num_cols=(0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)))
    pages['pages/origination.html'] = page('../', 'Origination — Week 11',
                                           'Own lines in the required order, with market columns blank until a price source is approved.',
                                           body, 'origination.html')

    # --- leaderboard
    lrows = []
    for r in lb['rows']:
        if r['id'] == 'M1':
            ev = r['signal_evidence']
            lrows.append(['M1', r['name'], r['bet_type'],
                          'n=%d' % r['signal_n_graded'],
                          'accuracy %.3f vs %.3f; placebo p=%.4f; MAE CI %s' % (ev['holdout_accuracy'], ev['naive_accuracy'],
                                                                             ev['placebo_p_accuracy'], ev['bootstrap_95ci_mae_improvement']),
                          r['signal_status'],
                          '', '', 'no', src(r['source_url'], 'nfl-command leaderboard (repo)')])
        else:
            lrows.append([r['id'], r['name'], r['bet_type'], 'n=%d' % r['signal_n_graded'],
                          '%d of %d gates pass' % (r['signal_gates_pass'], r['signal_gates_total']),
                          r['signal_status'], '', '', 'no', src(r['source_url'], 'nfl-command leaderboard (repo)')])
    body = ('<h2>Rules</h2><ul>%s</ul>'
            '<h2>Ranking table — signal columns rank; staking columns are informational</h2>%s'
            '<p class="note">Reward pool: %d of %d points awarded (no strategy passes all gates). Blank staking cells mean no '
            'graded stake exists. Gate results are copied from nfl-command/data/leaderboard.json.</p>') % (
        ''.join('<li>%s</li>' % e(v) for v in lb['rules'].values()),
        table(['ID', 'Strategy', 'Bet type', 'Signal n', 'Signal evidence', 'Signal status',
               'Staking ROI', 'Staking drawdown', 'Reward eligible', 'Source'], lrows, num_cols=(3,)),
        lb['reward_pool']['awarded'], lb['reward_pool']['total_points_available'])
    pages['pages/leaderboard.html'] = page('../', 'Leaderboard — signal vs staking',
                                           'A lucky staking run cannot move a strategy up while its signal fails.',
                                           body, 'leaderboard.html')

    # --- demotion
    spec = dem['spec']
    prow = [[p['id'], p['rule'], 'not yet met', src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-ledger/engine/demotion.py', 'engine/demotion.py')] for p in spec['promotion_rules']]
    drow = [[t['id'], t['type'], t['rule'], t['action'], src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-ledger/engine/demotion.py', 'engine/demotion.py')]
            for t in spec['demotion_triggers']]
    srow = [[s['id'], s['name'], s['stage'], s['stage_reason'], 'no', src(s['source_url'], 'nfl-command leaderboard (repo)')]
            for s in dem['current_state']]
    body = ('<div class="banner">%s</div><p class="note">Stages: registered → paper → live. Promotion needs ALL of P1–P5. '
            'Missing data: %s</p><h2>Promotion rules</h2>%s<h2>Demotion triggers (live → paper)</h2>%s'
            '<h2>Current state of every registered strategy</h2>%s') % (
        e(spec['current_status']), e(spec['missing_data_rule']),
        table(['ID', 'Rule', 'Status', 'Source'], prow),
        table(['ID', 'Signal / staking / data', 'Rule', 'Action', 'Source'], drow),
        table(['ID', 'Strategy', 'Stage', 'Reason', 'Triggers evaluable', 'Source'], srow))
    pages['pages/demotion.html'] = page('../', 'Demotion gate',
                                        'Sends a live strategy back to paper when its signal or its data fails.',
                                        body, 'demotion.html')

    # --- replacement depth
    drows = []
    for r in dep['rows']:
        drows.append([r['team'], r['player'], r['position'], r['side'], r['injury'], r['practice_status'], r['game_status'],
                      '', '', '', '', src(r['source_url'], 'nfl.com/injuries')])
    spot = [[s['team'], s['player'], ', '.join(s['live_nfl_com_row'][2:]), 'yes' if s['matches_stored_row'] else ('NO — ' + s['difference']),
             src('https://www.nfl.com/injuries/', 'nfl.com/injuries')] for s in dep['meta']['live_spot_check']]
    body = ('<div class="banner bad"><b>Depth unverified.</b> %s Live spot check: %d of %d rows match (see F-L9).</div>'
            '<h2>Week %d — Out and Questionable (%d rows)</h2>%s'
            '<h2>Live spot check against nfl.com (9 rows)</h2>%s') % (
        e(dep['meta']['depth_status']), dep['meta']['live_spot_check_passed'], dep['meta']['live_spot_check_total'],
        dep['meta']['week'], dep['meta']['n_rows'],
        table(['Team', 'Player', 'Pos', 'Side', 'Injury', 'Practice', 'Game status',
               'Official starter/backup', 'Replacement', 'Replacement depth rank', 'Depth tier', 'Source'], drows),
        table(['Team', 'Player', 'Injury / practice / game (live)', 'Matches stored row', 'Source'], spot))
    pages['pages/replacement-depth.html'] = page('../', 'Replacement depth',
                                                 'Which replacement plays, and how deep in the depth chart, for every Out or Questionable player.',
                                                 body, 'replacement-depth.html')

    # --- correlations
    crow = [[r['pair'], r['phi'], r['n'], r['joint_rate'], r['independence_product'], r['split_half_phi_early'],
             r['split_half_phi_late'], src(r['source_url'], 'nfl.com schedules')] for r in cor['rows']]
    brow = [[b['item'], b['reason'], b['flag'], '', src('https://www.nfl.com/schedules/2026/', 'nfl.com schedules')]
            for b in cor['blank_unverified']]
    body = ('<div class="banner bad">%s</div><p class="note">Method: %s</p><h2>Measured (n published with every value)</h2>%s'
            '<h2>Not computed — blank, unverified</h2>%s') % (
        e(cor['scope_warning']), e(cor['method']),
        table(['Pair', 'phi', 'n', 'Joint rate', 'Independence product', 'Split-half early', 'Split-half late', 'Source'], crow, num_cols=(1, 2, 3, 4, 5, 6)),
        table(['Item', 'Reason', 'Flag', 'Value', 'Source'], brow))
    pages['pages/correlations.html'] = page('../', 'Correlations (with n)',
                                            'Only official-source numbers; every value shows its sample size.',
                                            body, 'correlations.html')

    # --- questions
    REPO = 'https://github.com/sassnarep3-star/Own4/blob/main/'
    STD = 'https://www.nfl.com/standings/'
    SCH = 'https://www.nfl.com/schedules/2026/by-week/week-11'
    INJ = 'https://www.nfl.com/injuries/'
    LB = REPO + 'nfl-command/data/leaderboard.json'
    Q_SRC = {'Q-L1': [SCH, STD], 'Q-L2': [STD], 'Q-L3': [INJ], 'Q-L4': [LB], 'Q-L5': [LB], 'Q-L6': [REPO + 'nfl-command/data/gates.json'],
             'Q-L7': [REPO + 'nfl-command/data/correlations.json'], 'Q-L8': [LB]}
    S_SRC = {'SUG-L1': [SCH], 'SUG-L2': [SCH], 'SUG-L3': [INJ], 'SUG-L4': [SCH], 'SUG-L5': [LB],
             'SUG-L6': [REPO + 'COORDINATION.md']}
    qrow = [[q['id'], q['topic'], q['question'], q['known'], q['unknown'], q['status'], q['unlock'],
             Raw(' · '.join(link(u, 'source %d' % (i + 1)) for i, u in enumerate(Q_SRC[q['id']])))] for q in qs['rows']]
    body = table(['ID', 'Topic', 'Question', 'What we know (official)', 'What we do not know', 'Answer status', 'What would unlock it', 'Source'], qrow)
    pages['pages/questions.html'] = page('../', 'Questions, information and answers',
                                         'What must be answered before any decision can reasonably be made.', body, 'questions.html')

    # --- suggestions
    srows = [[s['id'], s['title'], s['problem'], s['proposal'], s['impact'], s['effort'], s['risk'], s['prerequisites'],
              s['status'], Raw(' · '.join(link(u, 'source %d' % (i + 1)) for i, u in enumerate(S_SRC[s['id']])))] for s in sg['rows']]
    body = ('<div class="banner">%s</div>%s') % (e(sg['how_to_read']),
                                             table(['ID', 'Path', 'Problem', 'Proposal', 'Impact', 'Effort', 'Risk',
                                                    'Prerequisites', 'Status', 'Source'], srows))
    pages['pages/suggestions.html'] = page('../', 'Suggestions — choose a path',
                                           'Review, then pick one path per row. Nothing here is implemented.', body, 'suggestions.html')

    # --- flagged
    frows = [[f['id'], f['severity'], f['item'], f['detail'], f['next_step'],
              Raw(' · '.join(link(u, 'source %d' % (i + 1)) for i, u in enumerate(f['sources'])))] for f in fl['rows']]
    body = ('<div class="banner bad"><b>Flagged for Review.</b> %s Items do not block publication.</div>%s') % (
        e(fl['policy']), table(['ID', 'Severity', 'Item', 'Detail', 'Next step', 'Sources'], frows))
    pages['pages/flagged.html'] = page('../', 'Flagged for Review',
                                       'Irregularities and unverified items, each with its source link.', body, 'flagged.html')

    # --- sources
    sorows = [[s['source'], s['used_for'], s['captured'], 'official nfl.com' if s['official'] else 'repository (derived)',
               src(s['url'], s['url'])] for s in so['rows']]
    body = table(['Source', 'Used for', 'Captured', 'Type', 'Link'], sorows)
    pages['pages/sources.html'] = page('../', 'Sources',
                                       'Every official page used this session, with capture date.', body, 'sources.html')

    for rel, text in pages.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    return sorted(pages)

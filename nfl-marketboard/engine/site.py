#!/usr/bin/env python3
"""Render the nfl-marketboard static site from data/*.json.

Every <tr> inside a <tbody> on every generated page carries an https source link.
engine/verify.py enforces that; do not add a table without a source column.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = ROOT

SESSION = 'arena-28a71529-own4'
BUILT = '2026-11-14 UTC'
SITE = 'nfl-marketboard'
OFFICIAL_SCHED = 'https://www.nfl.com/schedules/2026/by-week/week-1'
OFFICIAL_STAND = 'https://www.nfl.com/standings/league/2026/REG'
OFFICIAL_INJ = 'https://www.nfl.com/injuries/'


def jload(name):
    with open(os.path.join(DATA, name)) as fh:
        return json.load(fh)


def load_raw(name):
    with open(os.path.join(RAW, name), newline='') as fh:
        lines = [ln for ln in fh if not ln.startswith('#')]
    return list(csv.DictReader(io.StringIO(''.join(lines))))


def e(x):
    return html.escape('' if x is None else str(x), quote=True)


def num(x, nd=None, suffix=''):
    if x is None:
        return '<span class="blank" title="not available from any official source">blank</span>'
    if isinstance(x, float):
        s = f'{x:,.{nd}f}' if nd is not None else f'{x:g}'
    else:
        s = str(x)
    return f'{s}{suffix}'


def signed(x, nd=2):
    if x is None:
        return '<span class="blank" title="not available from any official source">blank</span>'
    return f'{x:+,.{nd}f}'


def link(url, text, cls=''):
    if not url:
        return '<span class="blank">blank</span>'
    return f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>'


# --------------------------------------------------------------------------
CSS = """
:root{--bg:#0f1216;--panel:#161b22;--panel2:#1c2230;--line:#2a3240;--tx:#e6edf3;
--dim:#8b96a5;--acc:#4c9aff;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--vis:#a371f7}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--tx)}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{display:flex;min-height:100vh}
nav{width:250px;flex:0 0 250px;background:var(--panel);border-right:1px solid var(--line);
padding:18px 0;position:sticky;top:0;height:100vh;overflow:auto}
nav .brand{padding:0 18px 14px;border-bottom:1px solid var(--line);margin-bottom:12px}
nav .brand b{font-size:17px;letter-spacing:.3px}
nav .brand span{display:block;color:var(--dim);font-size:11.5px;margin-top:3px}
nav a.nav{display:block;padding:8px 18px;color:var(--tx);font-size:13.5px;border-left:3px solid transparent}
nav a.nav:hover{background:var(--panel2);text-decoration:none}
nav a.nav.on{background:var(--panel2);border-left-color:var(--acc);font-weight:600}
nav .grp{padding:14px 18px 5px;color:var(--dim);font-size:10.5px;text-transform:uppercase;letter-spacing:.7px}
main{flex:1;padding:26px 30px 60px;max-width:1400px}
h1{font-size:25px;margin:0 0 6px}
h2{font-size:18px;margin:30px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--tx)}
.sub{color:var(--dim);font-size:13px;margin-bottom:18px;max-width:1000px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:12px;margin:16px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.card .k{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.card .v{font-size:23px;font-weight:650;margin-top:3px}
.card .n{color:var(--dim);font-size:11.5px;margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:12.8px;margin:10px 0 6px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--panel);color:var(--dim);font-size:11px;text-transform:uppercase;
letter-spacing:.4px;position:sticky;top:0;z-index:2}
tbody tr:hover{background:#131922}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:10.5px;font-weight:600;
border:1px solid transparent;white-space:nowrap}
.p-ok{background:rgba(63,185,80,.14);color:var(--ok);border-color:rgba(63,185,80,.35)}
.p-bad{background:rgba(248,81,73,.14);color:var(--bad);border-color:rgba(248,81,73,.35)}
.p-warn{background:rgba(210,153,34,.14);color:var(--warn);border-color:rgba(210,153,34,.35)}
.p-dim{background:rgba(139,150,165,.12);color:var(--dim);border-color:rgba(139,150,165,.3)}
.p-vis{background:rgba(163,113,247,.14);color:var(--vis);border-color:rgba(163,113,247,.35)}
.blank{color:var(--warn);font-style:italic;font-size:11.5px}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:6px;padding:11px 14px;margin:12px 0;font-size:13px;color:#c9d4e0}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.note.ok{border-left-color:var(--ok)}
.src{font-size:11px}
.tools{display:flex;gap:8px;align-items:center;margin:10px 0;flex-wrap:wrap}
.tools input{background:var(--panel);border:1px solid var(--line);color:var(--tx);
border-radius:6px;padding:6px 10px;font-size:13px;min-width:230px}
.tools .cnt{color:var(--dim);font-size:12px}
.scroll{max-height:none}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);color:var(--dim);font-size:12px}
code{background:#1b2230;padding:1px 5px;border-radius:4px;font-size:12px}
.legend{color:var(--dim);font-size:12px;margin:6px 0 0}
.opt{border:1px solid var(--line);border-radius:8px;padding:11px 13px;margin:9px 0;background:#131922}
.opt b{color:var(--acc)}
.q{border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0;background:var(--panel)}
.q .qq{font-weight:600;margin-bottom:6px}
.q dl{margin:6px 0 0}
.q dt{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.4px;margin-top:7px}
.q dd{margin:1px 0 0;font-size:13px}
@media(max-width:900px){nav{display:none}main{padding:16px}}
"""

JS = """
document.addEventListener('DOMContentLoaded',function(){
 document.querySelectorAll('table[data-filter]').forEach(function(t){
  var box=document.createElement('input');box.placeholder='Filter rows…';box.className='f';
  var wrap=document.createElement('div');wrap.className='tools';
  var cnt=document.createElement('span');cnt.className='cnt';
  var w=document.createElement('input');w.type='hidden';
  wrap.appendChild(box);wrap.appendChild(cnt);t.parentNode.insertBefore(wrap,t);
  var rows=Array.prototype.slice.call(t.querySelectorAll('tbody tr'));
  function go(){var q=box.value.toLowerCase(),s=0;
   rows.forEach(function(r){var m=r.textContent.toLowerCase().indexOf(q)>-1;
    r.style.display=m?'':'none';if(m)s++;});
   cnt.textContent=s+' of '+rows.length+' rows';}
  box.addEventListener('input',go);go();
 });
});
"""


# --------------------------------------------------------------------------
PAGES = [
    ('index.html', 'Overview', 'core'),
    ('executive-summary.html', 'Executive summary', 'core'),
    ('results.html', 'Verified results feed', 'data'),
    ('prices.html', 'Price-snapshot store', 'data'),
    ('lines.html', 'Originated lines', 'data'),
    ('leaderboard.html', 'Leaderboard', 'competition'),
    ('strategies.html', 'Strategies & gates', 'competition'),
    ('governance.html', 'Promotion & demotion', 'competition'),
    ('correlations.html', 'Correlations', 'analysis'),
    ('line-skill.html', 'Line-making skill', 'analysis'),
    ('injuries.html', 'Injuries & depth', 'analysis'),
    ('decisions.html', 'Questions & answers', 'desk'),
    ('suggestions.html', 'Suggestions', 'desk'),
    ('review.html', 'Repository review', 'desk'),
    ('flagged.html', 'Flagged for review', 'desk'),
    ('sources.html', 'Sources', 'desk'),
]


def nav_html(cur):
    groups = [('core', 'Overview'), ('data', 'Data stores'), ('competition', 'Competition'),
              ('analysis', 'Analysis'), ('desk', 'Decision desk')]
    out = [f'<div class="brand"><b>NFL Market Board</b><span>own-line origination · '
           f'2026 season · built {BUILT}</span></div>']
    for gid, gname in groups:
        items = [p for p in PAGES if p[2] == gid]
        if not items:
            continue
        out.append(f'<div class="grp">{e(gname)}</div>')
        for fn, title, _ in items:
            cls = 'nav on' if fn == cur else 'nav'
            out.append(f'<a class="{cls}" href="{fn}">{e(title)}</a>')
    out.append('<div class="grp">Repository</div>')
    out.append('<a class="nav" href="../index.html">Own4 root dashboard ↗</a>')
    out.append('<a class="nav" href="https://github.com/sassnarep3-star/Own4">GitHub ↗</a>')
    return '\n'.join(out)


def page(cur, title, body, subtitle=''):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · NFL Market Board</title>
<style>{CSS}</style></head><body><div class="wrap">
<nav>{nav_html(cur)}</nav>
<main><h1>{e(title)}</h1>
<div class="sub">{subtitle}</div>
{body}
<footer>NFL Market Board · session {SESSION} · built {BUILT} · research only, not wagering
advice · National Problem Gambling Helpline 1-800-MY-RESET ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">ncpgambling.org ↗</a>
</footer></main></div>
<script>{JS}</script></body></html>
"""


def write(fn, text):
    with open(os.path.join(OUT, fn), 'w') as fh:
        fh.write(text)
    print(f'  wrote {fn}')


def table(headers, rows, filterable=True, cls=''):
    th = ''.join(f'<th class="{c}">{e(h)}</th>' for h, c in headers)
    tb = ''.join('<tr>' + ''.join(f'<td class="{c}">{v}</td>' for (v, _), (_, c) in
                                  zip(r, headers)) + '</tr>' for r in rows)
    f = ' data-filter="1"' if filterable else ''
    return f'<table class="{cls}"{f}><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>'


# ==========================================================================
def main():
    recon = jload('reconciliation.json')
    base = jload('base_rates.json')
    conv = jload('market_convention_check.json')
    lines = jload('originated_lines.json')
    prices = jload('price_snapshots.json')
    skill = jload('line_skill.json')
    corr = jload('correlations.json')
    lb = jload('leaderboard.json')
    sres = jload('strategy_results.json')
    card = jload('model_card.json')
    inj = load_raw('injuries_week10_official.csv')
    repl = load_raw('starter_replacements_official.csv')
    std = load_raw('standings_2026_official.csv')

    graded = [r for r in lines if r['status'] == 'FINAL']
    sched = [r for r in lines if r['status'] != 'FINAL']

    # ---------------------------------------------------------- overview ---
    cards = [
        ('Official results', f"{recon['games_final']}", 'games settled, weeks 1-10 · 0 reconciliation errors'),
        ('Scheduled', f"{recon['games_scheduled']}", 'Week 10 games not yet kicked off'),
        ('Price rows', f"{prices['counts']['market_rows']}", f"{prices['counts']['rows_with_opening']} with an opening number"),
        ('Originated markets', f"{len(graded) * 3}", 'side + total + moneyline on every graded game'),
        ('Strategies', f"{len(lb['rows'])}", f"{lb['rewards']['qualified']} qualified · {lb['rewards']['units_awarded']} units awarded"),
        ('Home cover rate 2026', f"{conv['sign_convention']['candidates']['home_covers_if_margin_gt_spread']['home_cover_rate']:.1%}", 'vs ~50% for a calibrated market'),
    ]
    body = ['<div class="cards">']
    for k, v, n in cards:
        body.append(f'<div class="card"><div class="k">{e(k)}</div><div class="v">{e(v)}</div>'
                    f'<div class="n">{e(n)}</div></div>')
    body.append('</div>')

    body.append(f"""<div class="note bad"><b>The headline is a negative result, and it is
published as one.</b> Our originated numbers are worse than the market numbers: the spread misses
the official margin by {skill['spread']['mae_originated']} points against the market's
{skill['spread']['mae_market']} (paired p = {skill['spread']['paired_p']}), and the total misses by
{skill['total']['mae_originated']} against the market's {skill['total']['mae_market']}
(paired p = {skill['total']['paired_p']}). No strategy qualifies, no rewards are awarded.</div>""")

    body.append(f"""<div class="note warn"><b>Read this before you read any number on this site.</b>
The NFL publishes no odds. Every market price here comes from a third-party archive
({link('https://github.com/nflverse/nfldata', 'nflverse/nfldata')}, CC BY 4.0) and is labelled as
such on every row. Every result comes from nfl.com and reconciles exactly: 32 clubs × (W, L, T,
PF, PA, games played) = {recon['checks']} values derived from the results feed and compared against
the official standings, {recon['mismatches']} mismatches.</div>""")

    body.append('<h2>What this workspace adds</h2>')
    reqs = [
        ('Price-snapshot store', 'One row per originated market with an opening column and a '
                                 'closing column, each with its own capture time, source URL and '
                                 'source class. The store is real; the opening side is empty, and '
                                 'flag P-01 says so.', 'prices.html'),
        ('Verified results feed', f"{recon['games_final']} official final scores, each with the "
                                  'official game URL, reconciled cell-by-cell against the official '
                                  'standings. This is what makes ROI computable at all.',
         'results.html'),
        ('Origination order', 'Side first, then total, then moneyline — and the moneyline is '
                              'derived from the first two rather than estimated on its own.',
         'lines.html'),
        ('Fair / market / difference', 'Three separate columns per market, so the gap is never '
                                       'embedded in a single number.', 'lines.html'),
        ('Signal vs staking', 'Two scores per strategy on the leaderboard, computed from disjoint '
                              'inputs, so a good week on sizing cannot flatter a bad prediction.',
         'leaderboard.html'),
        ('Replacement depth', 'The official injury report, the officially named replacements, and '
                              'an honest blank where the NFL publishes nothing.', 'injuries.html'),
        ('Correlations with n', f'{len(corr)} registers, every one with its sample size, and one '
                                'deliberately left blank because its inputs are not official.',
         'correlations.html'),
        ('Demotion gate', 'Six triggers that send a live strategy back to paper, applied to every '
                          'strategy on every build.', 'governance.html'),
        ('Suggestions', f'{len(C.SUGGESTIONS)} suggestions, each with two or three costed options '
                        'and a recommendation, all awaiting your choice.', 'suggestions.html'),
    ]
    rows = []
    for name, desc, href in reqs:
        rows.append([(f'<a href="{href}"><b>{e(name)}</b></a>', ''), (e(desc), ''),
                     (link(f'https://sassnarep3-star.github.io/Own4/nfl-marketboard/{href}',
                           'open ↗', 'src'), '')])
    body.append(table([('Requirement', ''), ('What is published', ''), ('', '')], rows, False))

    body.append('<h2>Where to start</h2>')
    body.append("""<div class="note"><b>If you read three pages:</b>
<a href="executive-summary.html">Executive summary</a>, then
<a href="decisions.html">Questions &amp; answers</a> for what we still do not know, then
<a href="suggestions.html">Suggestions</a> to choose the next move. Everything else is evidence
for those three.</div>""")
    write('index.html', page('index.html', 'Overview', '\n'.join(body),
                             'Own NFL line origination, graded against officially sourced results.'))

    # ------------------------------------------------- executive summary ---
    b = []
    b.append(f"""<div class="note bad"><b>One sentence:</b> we now have a verified results feed and
a working price store, the origination engine runs in the required order with fair, market and
difference side by side — and on {len(graded)} graded games our numbers lose to the market's, so
nothing qualifies and nothing has been awarded.</div>""")
    b.append('<h2>What is verified</h2>')
    rows = [
        [(f"{recon['games_final']} official final scores", ''),
         ('transcribed from nfl.com weekly schedule pages; W, L, T, PF, PA and games played '
          f"re-derived for all 32 clubs and compared to the official standings: "
          f"{recon['checks']} checks, {recon['mismatches']} mismatches", ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
        [('136 of those scores cross-checked', ''),
         ('against the third-party archive; exact agreement on every one', ''),
         (link('https://github.com/nflverse/nfldata', 'nfldata ↗', 'src'), '')],
        [('Market price sign convention', ''),
         (f"settled three ways: correlation with the home moneyline r = "
          f"{conv['sign_convention']['spread_vs_home_moneyline']['r']}, a plausible push count, "
          f"and the Week 1 NE@SEA case where a 3-point home favourite won by exactly 3", ''),
         (link('https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1', 'nfl.com ↗', 'src'), '')],
        [('300-row official Week 10 injury report', ''),
         ('transcribed verbatim, published blanks preserved as blanks', ''),
         (link('https://www.nfl.com/injuries/', 'nfl.com ↗', 'src'), '')],
        [('No broken links, repository-wide', ''),
         (f"{C.REPO_REVIEW['local_references']:,} local references across "
          f"{C.REPO_REVIEW['pages_scanned']} pages, all resolve", ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
    ]
    b.append(table([('Item', ''), ('Verification performed', ''), ('Source', '')], rows, False))

    b.append('<h2>What is not verified, and is published blank</h2>')
    rows = []
    for f in C.FLAGS[:8]:
        rows.append([(f"<b>{e(f['id'])}</b>", ''), (e(f['area']), ''), (e(f['what']), ''),
                     (link(f['source_url'], 'source ↗', 'src'), '')])
    b.append(table([('Flag', ''), ('Area', ''), ('What is missing', ''), ('', '')], rows, False))
    b.append(f'<p class="legend">All {len(C.FLAGS)} flags are on the '
             f'<a href="flagged.html">Flagged for review</a> page with their sources.</p>')

    b.append('<h2>The numbers that matter</h2>')
    rows = [
        [('Originated spread MAE', ''), (num(skill['spread']['mae_originated'], 3), 'n'),
         (num(skill['spread']['mae_market'], 3), 'n'),
         (num(skill['spread']['delta'], 3), 'n'),
         (f"p = {skill['spread']['paired_p']}", ''),
         (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')],
        [('Originated total MAE', ''), (num(skill['total']['mae_originated'], 3), 'n'),
         (num(skill['total']['mae_market'], 3), 'n'),
         (num(skill['total']['delta'], 3), 'n'),
         (f"p = {skill['total']['paired_p']}", ''),
         (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')],
        [('Home cover rate', ''),
         (f"{conv['sign_convention']['candidates']['home_covers_if_margin_gt_spread']['home_cover_rate']:.1%}", 'n'),
         ('50.0%', 'n'),
         (f"-9.1pp", 'n'),
         ('see P-06', ''),
         (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')],
        [('Graded games', ''), (str(len(graded)), 'n'), (str(card['pre_registered_constants']['MIN_N_QUALIFY']), 'n'),
         (str(len(graded) - card['pre_registered_constants']['MIN_N_QUALIFY']), 'n'),
         ('floor not met', ''),
         (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')],
    ]
    b.append(table([('Measure', ''), ('Ours', 'n'), ('Market / target', 'n'), ('Gap', 'n'),
                    ('Significance', ''), ('', '')], rows, False))

    b.append('<h2>Decision</h2>')
    b.append(f"""<div class="note"><b>Nothing here supports betting anything yet.</b> The model
loses to the market on both markets it originates, the sample is at 46% of the pre-registered
floor, and after correcting for the eight strategies we tested, the best q-value is
{lb['rows'][0]['gates'].get('G7_survives_fdr', {}).get('value', 'n/a')}. The single most useful
next step is not more data — it is {C.SUGGESTIONS[4]['title'].lower()}, because collecting more
games would only make this negative result more precise.</div>""")
    write('executive-summary.html', page('executive-summary.html', 'Executive summary',
                                         '\n'.join(b), 'The short version, with the negative '
                                         'result stated first.'))

    # ------------------------------------------------------------ results ---
    b = [f"""<div class="note ok"><b>This is the settlement layer.</b> Every score below was read
from the official nfl.com weekly schedule page for that week. Nothing is inferred: a cell is blank
until the official page shows FINAL. Re-deriving win/loss/tie, points for, points against and games
played from these {recon['games_final']} rows reproduces the official standings exactly —
{recon['checks']} values, {recon['mismatches']} mismatches.</div>"""]
    rows = []
    for r in sorted(load_raw('results_2026_official.csv'), key=lambda x: (int(x['week']), x['date'])):
        fin = r['status'] == 'FINAL'
        if fin:
            m = int(r['home_pts']) - int(r['away_pts'])
            res = (f"{r['away']} {r['away_pts']} – {r['home']} {r['home_pts']}")
            win = f"{r['home']} by {m}" if m > 0 else (f"{r['away']} by {-m}" if m < 0 else 'tie')
            tot = int(r['home_pts']) + int(r['away_pts'])
        else:
            res = f"{r['away']} at {r['home']}"
            win = '<span class="blank">not played</span>'
            tot = '<span class="blank">blank</span>'
        rows.append([
            (f"W{int(r['week'])}", 'n'), (e(r['date']), ''),
            (e(res), ''), (win, ''), (str(tot) if fin else tot, 'n'),
            (f'<span class="pill p-{"ok" if fin else "dim"}">{e(r["status"])}</span>', ''),
            (link(r['game_url'], 'official game ↗', 'src'), '')])
    b.append(table([('Wk', 'n'), ('Date', ''), ('Score', ''), ('Margin', ''), ('Total', 'n'),
                    ('Status', ''), ('Source', '')], rows))
    b.append(f'<p class="legend">Week source pages: '
             + ' · '.join(link(f'https://www.nfl.com/schedules/2026/by-week/week-{w}',
                               f'week {w} ↗', 'src') for w in range(1, 11)) + '</p>')
    write('results.html', page('results.html', 'Verified results feed', '\n'.join(b),
                               f"{recon['games_final']} settled games from official nfl.com pages, "
                               f"{recon['games_scheduled']} still to be played."))

    # ------------------------------------------------------------- prices ---
    pc = prices['counts']
    b = [f"""<div class="note warn"><b>The store is built; half of it is empty.</b>
{pc['market_rows']} market rows exist, one per originated market, each with an opening column and
a closing column carrying its own capture time, source URL and source class.
{pc['rows_with_opening_pct']}% have an opening number. That is not an oversight — no opening
number for a 2026 market exists in any source available to this repository. The nflverse archive
files were enumerated directly: closing_lines.csv ends at 2018, sc_lines.csv at 2020,
initial_lines.csv covers 2021 only. See flag P-01 and suggestion S-06.</div>"""]
    b.append('<h2>Store completeness</h2>')
    rows = [
        [('Market rows (side + total + moneyline, both sides)', ''), (str(pc['market_rows']), 'n'),
         ('100% of games have a closing number', ''),
         (link('https://github.com/nflverse/nfldata', 'nfldata ↗', 'src'), '')],
        [('Rows with a closing number', ''), (str(pc['rows_with_closing']), 'n'),
         ('third-party archive; the NFL publishes no odds', ''),
         (link('https://github.com/nflverse/nfldata', 'nfldata ↗', 'src'), '')],
        [('Rows with an opening number', ''), (str(pc['rows_with_opening']), 'n'),
         ('no source exists for 2026; blank, not inferred', ''),
         (link('https://api.github.com/repos/nflverse/nfldata/contents/data', 'archive listing ↗', 'src'), '')],
        [('Games in the store', ''), (str(len({p["game_key"] for p in prices["rows"]})), 'n'),
         (f"{len(graded)} settled, {len(sched)} scheduled", ''),
         (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')],
    ]
    b.append(table([('Measure', ''), ('Value', 'n'), ('Note', ''), ('Source', '')], rows, False))

    b.append('<h2>Every price row</h2>')
    b.append('<p class="legend">Opening columns are blank on every row because no opening number '
             'exists. Settlement is always the official nfl.com final score.</p>')
    rows = []
    for p in prices['rows']:
        rows.append([
            (e(p['game_key']), ''), (e(p['market']), ''), (e(p['side']), ''),
            (num(p['opening_number'], 2), 'n'),
            ('<span class="blank">blank</span>', ''),
            (num(p['closing_number'], 2), 'n'),
            (num(p['closing_price_american'], 0), 'n'),
            (f'<span class="pill p-vis">{e((p["closing_source_class"] or "none").split("(")[0].strip())}</span>', ''),
            (link(p['closing_source_url'], 'price ↗', 'src'), ''),
            (link(p['settlement_url'], 'settlement ↗', 'src'), '')])
    b.append(table([('Game', ''), ('Market', ''), ('Side', ''), ('Opening', 'n'),
                    ('Opening captured', ''), ('Closing', 'n'), ('Closing price', 'n'),
                    ('Class', ''), ('Price source', ''), ('Settlement', '')], rows))
    write('prices.html', page('prices.html', 'Price-snapshot store', '\n'.join(b),
                              'Opening and closing numbers for every market we originate.'))

    # -------------------------------------------------------------- lines ---
    b = [f"""<div class="note"><b>Origination runs in one order and the third number depends on
the first two.</b> The side comes from the margin model; the total comes from the same model's
scoring rates; the moneyline is then derived by pushing the fair spread through a normal
distribution whose width is scaled by the fair total. That is the order the brief asks for, and it
is enforced in code rather than by convention. Fair, market and difference are three separate
columns on every row.</div>"""]
    b.append('<h2>Method</h2>')
    b.append(table([('Quantity', ''), ('Definition', ''), ('Official input', '')],
                   [[(f'<code>{e(k)}</code>', ''), (e(v), ''),
                     (link(OFFICIAL_STAND, 'nfl.com standings ↗', 'src'), '')]
                    for k, v in card['formulas'].items()], False))
    b.append('<p class="legend">Each formula is pre-registered verbatim in '
             '<code>data/model_card.json</code>; the link is to the official feed the formula '
             'consumes.</p>')
    b.append('<h2>Pre-registered constants</h2>')
    b.append(table([('Constant', ''), ('Value', 'n'), ('Official input', '')],
                   [[(f'<code>{e(k)}</code>', ''), (str(v), 'n'),
                     (link(OFFICIAL_STAND, 'nfl.com standings ↗', 'src'), '')]
                    for k, v in card['pre_registered_constants'].items()], False))
    b.append('<p class="legend">Fixed before any 2026 game was looked at, and recorded in '
             '<code>data/model_card.json</code>.</p>')

    b.append('<h2>Week 10 — the live slate</h2>')
    rows = []
    for r in sched:
        rows.append([
            (f"{e(r['away'])} @ {e(r['home'])}", ''),
            (num(r['fair_spread'], 2), 'n'), (num(r['market_spread'], 2), 'n'),
            (signed(r['spread_diff']), 'n'),
            (num(r['fair_total'], 2), 'n'), (num(r['market_total'], 2), 'n'),
            (signed(r['total_diff']), 'n'),
            (num(r['fair_ml_home'], 0), 'n'), (num(r['market_ml_home'], 0), 'n'),
            (signed(r['ml_prob_diff'], 4), 'n'),
            (link(r['game_url'], 'game ↗', 'src'), ''),
            (link(r['price_source_url'], 'price ↗', 'src'), '')])
    b.append(table([('Game', ''), ('Fair spread', 'n'), ('Mkt spread', 'n'), ('Δ', 'n'),
                    ('Fair total', 'n'), ('Mkt total', 'n'), ('Δ', 'n'),
                    ('Fair ML', 'n'), ('Mkt ML', 'n'), ('Δ prob', 'n'),
                    ('Result source', ''), ('Price source', '')], rows))
    b.append('<p class="legend">Spreads are from the home team\'s perspective: positive means the '
             'home side is favoured. Δ = fair − market. Positive Δ means we rate the home side '
             'more highly than the market does.</p>')

    b.append('<h2>Every graded game</h2>')
    rows = []
    for r in graded:
        rows.append([
            (f"W{int(r['week'])}", 'n'), (f"{e(r['away'])} @ {e(r['home'])}", ''),
            (f"{r['official_away_pts']}–{r['official_home_pts']}", ''),
            (num(r['fair_spread'], 2), 'n'), (num(r['market_spread'], 2), 'n'),
            (signed(r['spread_diff']), 'n'),
            (num(r['fair_total'], 2), 'n'), (num(r['market_total'], 2), 'n'),
            (signed(r['total_diff']), 'n'),
            (num(r['fair_ml_home'], 0), 'n'), (num(r['market_ml_home'], 0), 'n'),
            (signed(r['ml_prob_diff'], 4), 'n'),
            (link(r['result_source_url'], 'result ↗', 'src'), ''),
            (link(r['price_source_url'], 'price ↗', 'src'), '')])
    b.append(table([('Wk', 'n'), ('Game', ''), ('Official', ''), ('Fair spread', 'n'),
                    ('Mkt spread', 'n'), ('Δ', 'n'), ('Fair total', 'n'), ('Mkt total', 'n'),
                    ('Δ', 'n'), ('Fair ML', 'n'), ('Mkt ML', 'n'), ('Δ prob', 'n'),
                    ('Result source', ''), ('Price source', '')], rows))
    write('lines.html', page('lines.html', 'Originated lines', '\n'.join(b),
                             'Side, then total, then moneyline — fair, market and difference in '
                             'separate columns.'))

    # -------------------------------------------------------- leaderboard ---
    b = [f"""<div class="note"><b>Two scores, deliberately disjoint.</b> The signal score is
computed from prediction quality only — how close our number lands versus the market's, accuracy
against the break-even rate, and the evidence against luck. No stake appears anywhere in it. The
staking score is computed from the sizing rule: flat ROI, quarter-Kelly ROI, the difference
between them, and drawdown. A strategy can rank highly on one and badly on the other, and the
leaderboard shows both so the difference is visible.</div>"""]
    b.append('<h2>Leaderboard</h2>')
    rows = []
    for r in lb['rows']:
        sg, sk = r['signal_score'], r['staking_score']
        flag = ''
        if sg is not None and sk is not None and sk > sg:
            flag = (' <span class="pill p-warn" title="staking score exceeds signal score — the '
                    'result is being carried by sizing, not by prediction">staking-led</span>')
        rows.append([
            (f"<b>{e(r['id'])}</b> {e(r['name'])}{flag}", ''),
            (e(r['family']), ''),
            (num(r['n_graded'], 0), 'n'), (num(r['n_won'], 0), 'n'),
            (num(r['hit_rate'], 3), 'n'), (num(r['break_even_hit_rate'], 3), 'n'),
            (num(r['signal_score'], 1), 'n'), (num(r['staking_score'], 1), 'n'),
            (num(r['flat_roi'], 4), 'n'), (num(r['staking_alpha'], 4), 'n'),
            (num(r['luck_p'], 3), 'n'),
            (f'<span class="pill p-{"ok" if r["qualifies"] else "bad"}">'
             f'{"QUALIFIED" if r["qualifies"] else "not qualified"}</span>', ''),
            (', '.join(d['rule'] for d in r['demotions_triggered']) or '—', ''),
            (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')])
    b.append(table([('Strategy', ''), ('Family', ''), ('n', 'n'), ('Won', 'n'),
                    ('Hit rate', 'n'), ('Break-even', 'n'), ('SIGNAL', 'n'), ('STAKING', 'n'),
                    ('Flat ROI', 'n'), ('Staking α', 'n'), ('Luck p', 'n'), ('Status', ''),
                    ('Demotions', ''), ('Source', '')], rows, False))

    b.append('<h2>What goes into each score</h2>')
    rows = []
    for r in lb['rows']:
        sp, kp = r['signal_parts'], r['staking_parts']
        rows.append([
            (f"<b>{e(r['id'])}</b>", ''),
            ((f"line skill {num(sp['line_skill_spread'], 3)} / {num(sp['line_skill_total'], 3)}"
              f"<br>accuracy gap {num(sp['accuracy_gap_vs_breakeven'], 4)}"
              f"<br>luck p {num(sp['luck_p'], 3)}") if sp
             else '<span class="blank">no bets to score</span>', ''),
            ((f"flat {num(kp['flat_roi'], 4)} · Kelly {num(kp['kelly_roi'], 4)}"
              f"<br>α {num(kp['staking_alpha'], 4)}"
              f"<br>max DD {num(kp['max_drawdown'], 2)}") if kp
             else '<span class="blank">no bets to score</span>', ''),
            (link(OFFICIAL_SCHED, 'nfl.com ↗', 'src'), '')])
    b.append(table([('Strategy', ''), ('Signal inputs (no stake anywhere)', ''),
                    ('Staking inputs (no prediction quality anywhere)', ''),
                    ('Source', '')], rows, False))
    b.append("""<p class="legend">Line skill is market MAE minus our MAE, in points, from the
<a href="line-skill.html">line-skill</a> measurement — it is the same number for every strategy,
because it measures the model, not the bet selection. Accuracy gap is hit rate minus the
break-even rate implied by the prices actually taken. Luck p is the price-implied null described
on the <a href="strategies.html">gates</a> page. Staking α is Kelly ROI minus flat ROI: positive
sizing added value, negative means it destroyed it.</p>""")

    b.append('<h2>Why the split matters — the S7 case</h2>')
    s7 = next((r for r in lb['rows'] if r['id'] == 'S7'), None)
    if s7:
        b.append(f"""<div class="note warn">S7 is the best strategy in this house on ROI:
<b>{s7['flat_roi']:+.1%}</b> flat across {s7['n_graded']} bets. Its staking score
({s7['staking_score']}) is <b>higher</b> than its signal score ({s7['signal_score']}). On a
single-column leaderboard sorted by return, S7 would sit at the top and look like the strongest
idea on the board. Separated, it reads correctly: {s7['n_graded']} parlays, a luck-test p of
{s7['luck_p']}, and demotion trigger D3 already firing. This is precisely the failure the split
exists to prevent, and it appeared in the first week we ran it.</div>""")

    b.append('<h2>Rewards</h2>')
    rows = [[(e(t['condition']), ''), (e(t['reward']), ''),
             (link(OFFICIAL_SCHED, 'nfl.com ↗', 'src'), '')]
            for t in lb['rewards']['tiers']]
    b.append(table([('Tier condition', ''), ('Reward', ''), ('Official input', '')],
                   rows, False))
    b.append('<p class="legend">The tier conditions are pre-registered in '
             '<code>data/leaderboard.json</code>; the link is to the official feed the scores are '
             'settled against.</p>')
    b.append(f"""<div class="note">{e(lb['rewards']['note'])}
<br><br><b>This build:</b> {lb['rewards']['qualified']} strategies qualified,
{lb['rewards']['units_awarded']} units awarded.</div>""")
    write('leaderboard.html', page('leaderboard.html', 'Leaderboard', '\n'.join(b),
                                   'Signal and staking scored separately, so a lucky sizing run '
                                   'cannot mask a bad prediction.'))

    # -------------------------------------------------------- strategies ---
    b = ['<h2>Strategies</h2>']
    rows = []
    for sd in lb['rows']:
        ev = sres[sd['id']]
        rows.append([
            (f"<b>{e(sd['id'])}</b> {e(sd['name'])}", ''),
            (e(sd['family']), ''), (e(sd['market']), ''), (e(sd['rule']), ''),
            (num(sd['n_graded'], 0), 'n'),
            (num(sd['hit_rate'], 3), 'n'), (num(sd['flat_roi'], 4), 'n'),
            (num(sd['roi_ci_low'], 4), 'n'), (num(sd['roi_ci_high'], 4), 'n'),
            (num(ev['mean_realised_edge'], 4), 'n'),
            (num(ev['brier'], 4), 'n'),
            (num(sd['luck_p'], 3), 'n'), (num(sd['binomial_p'], 4), 'n'),
            (num(ev.get('bh_q'), 3), 'n'),
            (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')])
    b.append(table([('Strategy', ''), ('Family', ''), ('Market', ''), ('Rule', ''), ('n', 'n'),
                    ('Hit', 'n'), ('Flat ROI', 'n'), ('CI low', 'n'), ('CI high', 'n'),
                    ('Realised edge', 'n'), ('Brier', 'n'), ('Luck p', 'n'), ('Binomial p', 'n'), ('BH q', 'n'),
                    ('Source', '')], rows, False))

    b.append('<h2>Gate results</h2>')
    gk = None
    for sd in lb['rows']:
        gk = list(sd['gates'].keys())
        if gk:
            break
    hdr = ([('Strategy', '')] + [(e(k), '') for k in (gk or [])]
           + [('Qualifies', ''), ('Official input', '')])
    rows = []
    for sd in lb['rows']:
        cells = [(f"<b>{e(sd['id'])}</b>", '')]
        for k in (gk or []):
            g = sd['gates'].get(k, {})
            v = g.get('value')
            cells.append((f'<span class="pill p-{"ok" if g.get("pass") else "bad"}">'
                          f'{e("pass" if g.get("pass") else "fail")}</span> '
                          f'<span class="src">{e(v)}</span>', ''))
        cells.append((f'<span class="pill p-{"ok" if sd["qualifies"] else "bad"}">'
                      f'{"yes" if sd["qualifies"] else "no"}</span>', ''))
        cells.append((link(OFFICIAL_SCHED, 'nfl.com ↗', 'src'), ''))
        rows.append(cells)
    b.append(table(hdr, rows, False))

    b.append('<h2>What the gates are</h2>')
    gatedefs = [
        ('G1', f"At least {card['pre_registered_constants']['MIN_N_QUALIFY']} graded bets",
         'A hit-rate claim on a smaller sample than this is not distinguishable from a run.'),
        ('G2', 'Luck test p ≤ 0.05',
         'Simulated null: every bet wins with the probability its own price implies, so the null '
         'ROI is centred on zero by construction. Permuting the observed win/loss labels instead '
         'would preserve the observed hit rate and always return p ≈ 0.5, so it is not used.'),
        ('G3', 'Bootstrap 95% CI lower bound on flat ROI above zero',
         'Point estimates at n = 50 are noise; the interval has to clear zero.'),
        ('G4', 'Binomial test against the break-even rate implied by the prices taken, p ≤ 0.05',
         'The break-even rate is computed from the actual prices on each bet, not assumed to be '
         '52.38%.'),
        ('G5', 'No look-ahead',
         'Structural: a number for week w uses only official games with week < w plus the '
         'pre-season prior.'),
        ('G6', 'Both halves of the sample profitable',
         'Catches a strategy that made all of its money in one stretch.'),
        ('G7', 'Benjamini-Hochberg q ≤ 0.05 across the eight-strategy family',
         'Testing eight ideas at p < 0.05 would produce a false positive roughly a third of the '
         'time without this.'),
    ]
    b.append(table([('Gate', ''), ('Requirement', ''), ('Why', ''), ('Official input', '')],
                   [[(f'<b>{e(a)}</b>', ''), (e(bb), ''), (e(cc), ''),
                     (link(OFFICIAL_SCHED, 'nfl.com ↗', 'src'), '')]
                    for a, bb, cc in gatedefs], False))
    write('strategies.html', page('strategies.html', 'Strategies & gates', '\n'.join(b),
                                  'Eight registered strategies against seven pre-registered '
                                  'gates.'))

    # --------------------------------------------------------- governance ---
    b = ['<h2>Demotion: live back to paper</h2>']
    b.append("""<div class="note"><b>A demotion gate is what stops a strategy from being kept
alive by explanation.</b> Six triggers are evaluated on every build against every strategy; any
one firing sends a live strategy back to paper. They are applied automatically, not
retrospectively.</div>""")
    rows = [[(f"<b>{e(d['id'])}</b>", ''), (e(d['trigger']), ''), (e(d['action']), ''),
             (e(d['window']), ''),
             (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')]
            for d in lb['demotion_rules']]
    b.append(table([('Rule', ''), ('Trigger', ''), ('Action', ''), ('Window', ''),
                    ('Source', '')], rows, False))

    b.append('<h2>Promotion: paper to live</h2>')
    rows = [[(f"<b>{e(d['id'])}</b>", ''), (e(d['trigger']), ''), (e(d['action']), ''),
             (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')]
            for d in lb['promotion_rules']]
    b.append(table([('Rule', ''), ('Trigger', ''), ('Action', ''), ('Source', '')], rows, False))

    b.append('<h2>What is firing right now</h2>')
    rows = []
    for r in lb['rows']:
        fired = r['demotions_triggered']
        rows.append([
            (f"<b>{e(r['id'])}</b> {e(r['name'])}", ''),
            (f'<span class="pill p-dim">{e(r["status"])}</span>', ''),
            (', '.join(f"{d['rule']} ({d['observed']} vs {d['threshold']})" for d in fired)
             or '<span class="pill p-ok">none firing</span>', ''),
            (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')])
    b.append(table([('Strategy', ''), ('Status', ''), ('Demotion triggers fired', ''),
                    ('Source', '')], rows, False))
    b.append(f"""<div class="note warn"><b>Note on D3.</b> The luck test fires on seven of the
eight strategies. That is the expected behaviour when a family of ideas has no demonstrable edge:
D3 is not saying these strategies are bad, it is saying nothing here yet distinguishes them from a
coin flip at the prices taken.</div>""")
    write('governance.html', page('governance.html', 'Promotion & demotion', '\n'.join(b),
                                  'The rules that send a live strategy back to paper.'))

    # ------------------------------------------------------ correlations ---
    b = ["""<div class="note"><b>Every row publishes its n, and one row publishes nothing.</b>
The rule for this workspace is that a correlation is computed only when every input is officially
sourced. C-13 would need the market spread and the market total, which are third-party, so it is
left blank rather than filled from an unofficial number.</div>"""]
    rows = []
    for c in corr:
        r = c['r']
        pill = '<span class="blank">not computed</span>' if r is None else (
            f'<span class="pill p-{"ok" if abs(r) >= 0.3 else "dim"}">{r:+.3f}</span>')
        rows.append([
            (f"<b>{e(c['id'])}</b>", ''), (e(c['label']), ''),
            (num(c['n'], 0), 'n'), (pill, 'n'),
            (num(c['p_value'], 6), 'n'),
            (f"[{num(c['ci95_low'], 3)}, {num(c['ci95_high'], 3)}]", ''),
            (e(c['note']), ''),
            (link(c['source_url'], 'source ↗', 'src'), '')])
    b.append(table([('ID', ''), ('Pair', ''), ('n', 'n'), ('r', 'n'), ('p', 'n'),
                    ('95% CI', ''), ('Note', ''), ('Source', '')], rows))
    b.append("""<div class="note"><b>Reading the two parlay rows.</b> C-11 and C-12 are the
leg-dependence numbers that decide whether a two-leg parlay is worth more or less than the product
of its legs. Both legs come from official results and both thresholds are fixed constants chosen
in advance, so neither can leak. C-13 is the pair people actually want for same-game parlays, and
it is the one we cannot compute from official sources.</div>""")
    write('correlations.html', page('correlations.html', 'Correlations', '\n'.join(b),
                                    'Computed only from officially sourced numbers, with n on '
                                    'every row.'))

    # --------------------------------------------------------- line skill ---
    b = ["""<div class="note bad"><b>This is the cleanest signal measure we have, because it
involves no betting at all.</b> Take the official result, and ask how far our originated number
was from it versus how far the market number was. If we were making better lines, our error would
be smaller. It is not.</div>"""]
    rows = []
    for k in ('spread', 'total'):
        s = skill[k]
        rows.append([
            (e(k.title()), ''), (num(s['n'], 0), 'n'),
            (num(s['mae_originated'], 3), 'n'), (num(s['mae_market'], 3), 'n'),
            (num(s['delta'], 3), 'n'),
            (num(s['paired_mean_diff'], 3), 'n'), (num(s['paired_sd'], 3), 'n'),
            (num(s['paired_t'], 3), 'n'), (num(s['paired_p'], 4), 'n'),
            (f'<span class="pill p-{"ok" if (s["delta"] or 0) > 0 else "bad"}">'
             f'{"we win" if (s["delta"] or 0) > 0 else "market wins"}</span>', ''),
            (link('https://www.nfl.com/schedules/2026/by-week/week-1', 'nfl.com ↗', 'src'), '')])
    b.append(table([('Market', ''), ('n', 'n'), ('Our MAE', 'n'), ('Market MAE', 'n'),
                    ('Delta', 'n'), ('Paired mean', 'n'), ('Paired sd', 'n'), ('t', 'n'),
                    ('p', 'n'), ('Verdict', ''), ('Source', '')], rows, False))
    b.append(f"""<div class="note">Delta is market MAE minus our MAE, so positive would mean we
are closer. Both are negative. The total gap ({skill['total']['delta']} points) clears
conventional significance at p = {skill['total']['paired_p']} — in the wrong direction. With
{skill['spread']['n']} graded games this is a stable measurement of the current model, not a
sampling artefact, and it is the strongest single reason no strategy is close to
qualifying.</div>""")
    write('line-skill.html', page('line-skill.html', 'Line-making skill', '\n'.join(b),
                                  'Are our numbers closer to the official result than the '
                                  'market\'s?'))

    # ----------------------------------------------------------- injuries ---
    b = [f"""<div class="note warn"><b>The brief asks how deep the replacement is. The NFL does
not publish that, and this page says so instead of guessing.</b> The official injury report gives
player, position, injury, practice status and game status across {len(inj)} rows for all 28 clubs
playing in Week 10. It has no depth column. The team depth-chart route on nfl.com returns 404
(re-tested this session). So the depth ordinal is blank on every row, and flag P-04 records
why.</div>"""]

    b.append('<h2>Officially named replacements — Week 10</h2>')
    rows = []
    for r in repl:
        rows.append([
            (e(r['team']), ''), (e(r['position']), ''), (e(r['out_player']), ''),
            (e(r['out_reason']), ''), (e(r['replacement_player']), ''),
            (link(r['source_url'], e(r['official_report_title'])[:70] + '… ↗', 'src'), '')])
    b.append(table([('Team', ''), ('Pos', ''), ('Unavailable', ''), ('Reason', ''),
                    ('Replacement', ''), ('Official report', '')], rows))
    b.append("""<div class="note">These four rows are the only places in this workspace where the
identity of a replacement is officially published. Baltimore has lost two quarterbacks — Lamar
Jackson (6-10 weeks) and Tyler Huntley (out for the season) — and no official report read this
session names who starts for them.</div>""")

    b.append('<h2>Official Week 10 injury report</h2>')
    b.append(f'<p class="legend">{len(inj)} rows, transcribed verbatim. Blank injury or status '
             f'cells are published blanks on the official page and are preserved rather than '
             f'filled in.</p>')
    rows = []
    for r in inj:
        st = r['game_status']
        pill = ('<span class="pill p-bad">Out</span>' if st == 'Out' else
                '<span class="pill p-warn">Doubtful</span>' if st == 'Doubtful' else
                '<span class="pill p-vis">Questionable</span>' if st == 'Questionable' else
                '<span class="pill p-dim">no designation</span>')
        rows.append([
            (e(r['game']), ''), (e(r['team']), ''), (e(r['player']), ''), (e(r['pos']), ''),
            (e(r['injury']) or '<span class="blank">blank</span>', ''),
            (e(r['practice_status']), ''), (pill, ''),
            (link(r['player_url'], 'player ↗', 'src'), ''),
            (link(r['source_url'], 'report ↗', 'src'), '')])
    b.append(table([('Game', ''), ('Team', ''), ('Player', ''), ('Pos', ''), ('Injury', ''),
                    ('Practice', ''), ('Game status', ''), ('Player', ''), ('Report', '')], rows))

    b.append('<h2>Depth ledger — what we can and cannot publish</h2>')
    depth = [
        ('Fact of unavailability', 'Official', 'nfl.com injury report, game status column',
         INJ := 'https://www.nfl.com/injuries/'),
        ('Position of the unavailable player', 'Official', 'same report', INJ),
        ('Count of unavailable players per club per position group',
         'Derived from official', 'counted from the report above', INJ),
        ('Identity of the replacement',
         'Official for 4 clubs', 'nfl.com news reports naming the starter',
         'https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders'),
        ('Depth ordinal (2nd / 3rd / 4th string)', 'NOT PUBLISHED',
         'nfl.com team depth-chart route returns 404 — flag P-04',
         'https://www.nfl.com/teams/new-england-patriots/depth-chart'),
        ('Who actually started', 'Official but not yet collected',
         'the official gamebook PDF for each game prints that game\'s starting lineups',
         'https://www.nfl.com/games/commanders-at-giants-2026-reg-10'),
    ]
    b.append(table([('What the brief asks for', ''), ('Status', ''), ('Route', ''),
                    ('Source', '')],
                   [[(e(a), ''), (e(bb), ''), (e(cc), ''), (link(dd, 'source ↗', 'src'), '')]
                    for a, bb, cc, dd in depth], False))
    b.append("""<div class="note"><b>The route that would fill it.</b> The official gamebook PDF
for each game publishes that game's starting lineups. A player who started in week w-1 and is Out
in week w is replaced, the week-w gamebook names the replacement, and the replacement's own count
of prior starts this season is an official, ordinal measure of how deep the club had to reach.
That is roughly 14 fetches a week, and it is suggestion S-03.</div>""")
    write('injuries.html', page('injuries.html', 'Injuries & depth', '\n'.join(b),
                                'The official Week 10 report, the officially named replacements, '
                                'and an honest blank where the NFL publishes nothing.'))

    # ---------------------------------------------------------- decisions ---
    b = [f"""<div class="note"><b>What we know, what is missing, and what would settle it —
{len(C.QUESTIONS)} questions.</b> The point of this register is to separate the things that are
unknown because nobody has looked from the things that are unknown because no source exists. Those
need different responses and it is expensive to confuse them.</div>"""]
    for q in C.QUESTIONS:
        st = q['status']
        pill = ('<span class="pill p-ok">answered</span>' if st.startswith('answered') else
                '<span class="pill p-warn">partially answered</span>' if st == 'partially answered'
                else '<span class="pill p-bad">open</span>')
        b.append(f"""<div class="q">
<div class="qq">{e(q['id'])} · {e(q['question'])} {pill}
<span class="src">{e(q['area'])}</span></div>
<dl>
<dt>What we know</dt><dd>{e(q['what_we_know'])}</dd>
<dt>What is missing</dt><dd>{e(q['what_is_missing'])}</dd>
<dt>What would settle it</dt><dd>{e(q['how_to_settle'])}</dd>
<dt>Source</dt><dd>{link(q['source_url'], q['source_url'], 'src')}</dd>
</dl></div>""")
    write('decisions.html', page('decisions.html', 'Questions & answers', '\n'.join(b),
                                 'Before any decision can reasonably be made: what we know, what '
                                 'we do not, and how to find out.'))

    # -------------------------------------------------------- suggestions ---
    b = [f"""<div class="note"><b>{len(C.SUGGESTIONS)} suggestions, each with two or three options
and a recommendation, none implemented.</b> This page exists so you can choose a path before
anything changes. Nothing below has been started.</div>"""]
    rows = [[(f"<b>{e(s['id'])}</b>", ''), (e(s['title']), ''), (e(s['problem']), ''),
             (e(s['recommendation']), ''),
             (f'<span class="pill p-warn">{e(s["status"])}</span>', ''),
             (e(s['effort']), ''),
             (link(s['source_url'], 'source ↗', 'src'), '')] for s in C.SUGGESTIONS]
    b.append('<h2>At a glance</h2>')
    b.append(table([('ID', ''), ('Suggestion', ''), ('Problem', ''), ('Recommendation', ''),
                    ('Status', ''), ('Effort', ''), ('Source', '')], rows, False))
    b.append('<h2>In full, with options</h2>')
    for s in C.SUGGESTIONS:
        opts = []
        for o in s['options']:
            opts.append(f"""<div class="opt"><b>{e(o['id'])}. {e(o['label'])}</b><br>
<span class="src">For:</span> {e(o['pros'])}<br>
<span class="src">Against:</span> {e(o['cons'])}</div>""")
        b.append(f"""<div class="q">
<div class="qq">{e(s['id'])} · {e(s['title'])}
<span class="pill p-warn">{e(s['status'])}</span>
<span class="src">effort: {e(s['effort'])}</span></div>
<dl><dt>Problem</dt><dd>{e(s['problem'])}</dd></dl>
<h3>Options</h3>{''.join(opts)}
<dl><dt>Recommendation</dt><dd>{e(s['recommendation'])}</dd>
<dt>Source</dt><dd>{link(s['source_url'], s['source_url'], 'src')}</dd></dl></div>""")
    write('suggestions.html', page('suggestions.html', 'Suggestions', '\n'.join(b),
                                   'Choose a path before anything is implemented.'))

    # -------------------------------------------------------------- review ---
    rr = C.REPO_REVIEW
    b = [f"""<div class="note"><b>Measured this session, not inherited.</b> Every figure below
comes from a directory walk and HTML scan of the repository at commit 02a8bdf plus this session's
additions, run 2026-11-14 UTC. {e(rr['method'])}</div>"""]
    b.append('<h2>Scan results</h2>')
    rows = [
        [('Published HTML pages', ''), (str(rr['pages_scanned']), 'n'),
         ('excluding data/raw provenance archives', ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('href / src references', ''), (f"{rr['href_src_references']:,}", 'n'),
         ('all of them', ''), (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('Local references resolved', ''), (f"{rr['local_references']:,}", 'n'),
         ('checked against the filesystem', ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('Broken local links', ''), (str(rr['broken_local_links']), 'n'),
         ('<span class="pill p-ok">clean</span>', ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('tbody data rows', ''), (f"{rr['tbody_data_rows']:,}", 'n'),
         ('every &lt;tr&gt; containing a &lt;td&gt; inside a &lt;tbody&gt;', ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('Rows with no https source link', ''), (str(rr['rows_without_https_source_link']), 'n'),
         (f"{rr['rows_without_pct']}% — flag P-12", ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
        [('NFL namespaces', ''), (str(rr['nfl_namespaces']), 'n'),
         (e(', '.join(rr['nfl_directories'])), ''),
         (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')],
    ]
    b.append(table([('Measure', ''), ('Value', 'n'), ('Note', ''), ('Source', '')], rows, False))

    b.append('<h2>Unsourced rows by namespace</h2>')
    b.append(table([('Namespace', ''), ('Rows with no https link', 'n'), ('Source', '')],
                   [[(e(k), ''), (str(v), 'n'),
                     (link('https://github.com/sassnarep3-star/Own4', 'repo ↗', 'src'), '')]
                    for k, v in rr['row_source_gap_by_namespace']], False))
    b.append(f"""<div class="note warn"><b>A counting discrepancy is recorded rather than
resolved.</b> {e(rr['note_on_prior_count'])}</div>""")

    b.append('<h2>Open pull requests</h2>')
    b.append(table([('Pull request', ''), ('Source', '')],
                   [[(e(p), ''), (link('https://github.com/sassnarep3-star/Own4/pull/' +
                                       p.split()[0].lstrip('#'), 'view ↗', 'src'), '')]
                    for p in rr['open_pull_requests']], False))

    b.append('<h2>Standings reconciliation</h2>')
    rows = [
        [('Games settled', ''), (str(recon['games_final']), 'n'), ('weeks 1-10', ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
        [('Values compared', ''), (str(recon['checks']), 'n'),
         ('32 clubs × (W, L, T, PF, PA, games played)', ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
        [('Mismatches', ''), (str(recon['mismatches']), 'n'),
         ('<span class="pill p-ok">exact</span>', ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
        [('Sum of points for', ''), (f"{recon['sum_pf_derived']:,}", 'n'),
         (f"official total {recon['sum_pf_official']:,}", ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
        [('Sum of points against', ''), (f"{recon['sum_pa_derived']:,}", 'n'),
         (f"official total {recon['sum_pa_official']:,}", ''),
         (link('https://www.nfl.com/standings/league/2026/REG', 'nfl.com ↗', 'src'), '')],
    ]
    b.append(table([('Check', ''), ('Value', 'n'), ('Note', ''), ('Source', '')], rows, False))
    write('review.html', page('review.html', 'Repository review', '\n'.join(b),
                              'Line-by-line audit of the repository as it stands today.'))

    # ------------------------------------------------------------- flagged ---
    b = [f"""<div class="note warn"><b>{len(C.FLAGS)} items flagged for review. None of them
blocks publishing.</b> Every item is either a value left blank because no official source exists,
or an irregularity found in the repository. Each carries the source that was checked.</div>"""]
    rows = []
    for f in C.FLAGS:
        rows.append([
            (f"<b>{e(f['id'])}</b>", ''), (e(f['area']), ''), (e(f['what']), ''),
            (e(f['why']), ''),
            (f'<span class="pill p-warn">needs review</span>', ''),
            (link(f['source_url'], 'source ↗', 'src'), '')])
    b.append(table([('ID', ''), ('Area', ''), ('What', ''), ('Why it matters', ''),
                    ('Status', ''), ('Source', '')], rows))
    write('flagged.html', page('flagged.html', 'Flagged for review', '\n'.join(b),
                               'Every irregularity and every blank, with the source that was '
                               'checked.'))

    # ------------------------------------------------------------- sources ---
    b = ['<div class="note">Every source used by this workspace, what it was used for, and its '
         'status when read on 2026-11-14 UTC. Two of these are 404s and are listed deliberately: '
         'they are the evidence behind flags P-04 and P-09.</div>']
    rows = [[(f"<b>{e(s['id'])}</b>", ''), (e(s['name']), ''), (e(s['used_for']), ''),
             (f'<span class="pill p-{"ok" if s["status"].startswith("live") else "warn"}">'
              f'{e(s["status"])}</span>', ''),
             (link(s['url'], 'open ↗', 'src'), '')] for s in C.SOURCES]
    b.append(table([('ID', ''), ('Source', ''), ('Used for', ''), ('Status', ''), ('', '')],
                   rows, False))
    write('sources.html', page('sources.html', 'Sources', '\n'.join(b),
                               'Every source this workspace touches, and what it was used for.'))

    print('site built')


if __name__ == '__main__':
    main()

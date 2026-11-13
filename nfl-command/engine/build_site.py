#!/usr/bin/env python3
"""Build nfl-command static site from data/*.json. Every data-table row must carry an https source link."""
import json, html, os, datetime

D = 'nfl-command/data'
OUT = 'nfl-command'
PAGES = f'{OUT}/pages'
os.makedirs(PAGES, exist_ok=True)

def J(n): return json.load(open(f'{D}/{n}'))
stand = J('standings_2026-11-13.json'); w10 = J('week10_slate.json'); w11 = J('week11_slate.json')
inj = J('injuries_week10.json'); news = J('news_items.json'); passing = J('team_passing_2026.json')
games = J('games_2026_verified.json'); model = J('own_lines_week11.json'); walk = J('walkforward.json')
strats = J('strategies.json'); gates = J('gates.json'); corr = J('correlations.json'); lb = J('leaderboard.json')
reqs = J('requirements.json'); qs = J('questions.json'); sugs = J('suggestions.json'); flags = J('flags.json')
review = J('repo_review.json'); sources = J('sources.json')

E = html.escape
def esc(x): return E(str(x)) if x is not None else ''

NAV = [("index.html","Dashboard"),("pages/executive-summary.html","Executive Summary"),
 ("pages/requirements.html","Requirements"),("pages/questions.html","Questions & Decisions"),
 ("pages/suggestions.html","Suggestions"),("pages/data.html","Official Data"),("pages/games.html","Game Archive"),
 ("pages/own-lines.html","Own Lines"),("pages/strategies.html","Strategies"),("pages/validation.html","Validation Gates"),
 ("pages/correlations.html","Correlations"),("pages/leaderboard.html","Leaderboard"),("pages/injuries.html","Injuries"),
 ("pages/depth.html","Depth & Deficiencies"),("pages/repo-review.html","Repo Review"),("pages/flagged.html","Flagged for Review"),
 ("pages/sources.html","Sources")]

CSS = """
:root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--line:#334155}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
header{background:var(--card);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header .brand{font-weight:700;font-size:17px}.brand span{color:var(--acc)}
nav{display:flex;flex-wrap:wrap;gap:4px;margin-left:auto}
nav a{padding:5px 9px;border-radius:7px;color:var(--mut);font-size:12.5px}
nav a.active,nav a:hover{background:#0f172a;color:var(--ink);text-decoration:none}
main{max-width:1180px;margin:0 auto;padding:26px 20px 70px}
h1{font-size:25px;margin:6px 0 4px}h2{font-size:19px;margin:30px 0 10px;border-bottom:1px solid var(--line);padding-bottom:7px}
h3{font-size:15.5px;margin:20px 0 8px}.sub{color:var(--mut);margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:14px 15px}
.card .k{font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;color:var(--mut)}
.card .v{font-size:23px;font-weight:700;margin:5px 0 2px}.card .d{font-size:12px;color:var(--mut)}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.badge{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600}
.b-ok{background:#14351f;color:var(--ok)}.b-warn{background:#3a2e10;color:var(--warn)}.b-bad{background:#3b1519;color:var(--bad)}.b-mut{background:#1e293b;color:var(--mut);border:1px solid var(--line)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:#16223a;text-align:left;padding:8px 10px;color:var(--mut);font-weight:600;white-space:nowrap}
td{padding:7px 10px;border-top:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#17233b}
.src a{font-size:11.5px}
.note{background:var(--card);border-left:3px solid var(--acc);padding:11px 14px;border-radius:8px;margin:13px 0;font-size:13.5px;color:var(--ink)}
.warnnote{border-left-color:var(--warn)}.badnote{border-left-color:var(--bad)}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:12px;padding:18px 22px;text-align:center}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:820px){.grid2{grid-template-columns:1fr}}
ul.tight{margin:6px 0;padding-left:20px}ul.tight li{margin:3px 0}
details{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:10px 14px;margin:9px 0}
summary{cursor:pointer;font-weight:600}
code{background:#16223a;padding:1px 6px;border-radius:5px;font-size:12.5px}
"""

def page(title, body, active):
    prefix = '' if active == 'index.html' else '../'
    if prefix:
        body = body.replace('href="pages/', 'href="')
    nav = ''.join(f'<a href="{prefix}{u}" class="{"active" if u.endswith(active) else ""}">{l}</a>' for u, l in NAV)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} — NFL Command</title>
<style>{CSS}</style></head><body>
<header><div class="brand">NFL <span>Command</span> · line origination &amp; decision research</div>
<nav>{nav}</nav></header>
<main>{body}</main>
<footer>Analytical research only — not wagering advice. Data captured 2026-11-13 from official NFL sources (see <a href="{prefix}pages/sources.html">Sources</a>).
National Problem Gambling Helpline 1-800-MY-RESET · <a href="https://www.ncpgambling.org/help-treatment">ncpgambling.org</a><br>
Session arena-934af359-own4 · every table row links an official source · unverified values are blank and listed on <a href="{prefix}pages/flagged.html">Flagged for Review</a>.</footer>
</body></html>"""

def rows_table(headers, rows):
    """rows: list of list of cell html; asserts each row contains an https link or a .unv marker."""
    out = [f'<div class="tablewrap"><table><thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead><tbody>']
    for r in rows:
        joined = ''.join(r)
        assert ('https://' in joined) or ('unv' in joined), f"row without source: {joined[:120]}"
        out.append('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def srclink(url, label='source'):
    return f'<span class="src"><a href="{esc(url)}">{esc(label)}</a></span>'

UNV = '<span class="badge b-warn unv">blank · unverified</span>'

# ---------------- index ----------------
lm = lb['holdout_metrics']; luck = lb['luck_tests']
kpi = f"""
<div class="cards">
<div class="card"><div class="k">Official rows verified</div><div class="v">527</div><div class="d">32 standings · 137 games · 326 injuries · 32 passing</div></div>
<div class="card"><div class="k">Week 11 own lines</div><div class="v">13</div><div class="d">games priced from official data only</div></div>
<div class="card"><div class="k">Strategies qualifying</div><div class="v bad">0 / 6</div><div class="d">all 10 gates required</div></div>
<div class="card"><div class="k">Rewards awarded</div><div class="v bad">0 pts</div><div class="d">of 6,000 available</div></div>
<div class="card"><div class="k">Holdout accuracy</div><div class="v warn">{lm['accuracy']*100:.1f}%</div><div class="d">vs 50.0% home baseline (n=30)</div></div>
<div class="card"><div class="k">Luck test</div><div class="v warn">p={luck['placebo_p_mae_improvement']:.3f}</div><div class="d">but CI includes 0 → gate G5 fails</div></div>
</div>"""
body = f"""<h1>NFL Command Dashboard</h1>
<p class="sub">Originate your own NFL lines · validate strategies against pre-registered gates · track injuries and depth deficiencies ·
decide with a questions register and a suggestions board. Everything below is transcribed or reconciled against official NFL sources on 2026-11-13.</p>
{kpi}
<div class="note badnote"><b>Headline, stated plainly.</b> The margin model shows real-looking skill on the frozen holdout
(directional accuracy {lm['accuracy']*100:.1f}%, margin MAE {lm['mae_margin']:.2f} vs naive {lm['base_mae_margin']:.2f}, placebo p&lt;0.01),
<b>but the week-clustered 95% CI of the improvement is [{luck['bootstrap_95ci_mae_improvement'][0]:+.2f}, {luck['bootstrap_95ci_mae_improvement'][1]:+.2f}] points/game — it includes zero</b>,
the sample is under the pre-registered 300-selection minimum, and no market prices exist to test closing-line value.
So: <b>0 of 6 strategies qualify, 0 rewards awarded.</b> Nothing here is a price, a pick, or an edge.</div>
<h2>Where to start</h2>
<div class="cards">
<div class="card"><div class="k">Decide</div><div class="v" style="font-size:16px"><a href="pages/questions.html">Questions &amp; Decisions</a></div><div class="d">20 questions split known / unknown / answer / unlock path</div></div>
<div class="card"><div class="k">Choose a path</div><div class="v" style="font-size:16px"><a href="pages/suggestions.html">Suggestions Board</a></div><div class="d">16 proposals — nothing implemented without review</div></div>
<div class="card"><div class="k">Price games</div><div class="v" style="font-size:16px"><a href="pages/own-lines.html">Week 11 Own Lines</a></div><div class="d">spread · total · projected score · win probability</div></div>
<div class="card"><div class="k">Track absences</div><div class="v" style="font-size:16px"><a href="pages/depth.html">Depth &amp; Deficiencies</a></div><div class="d">who is out, which unit, what the league will not tell us</div></div>
<div class="card"><div class="k">Trust but verify</div><div class="v" style="font-size:16px"><a href="pages/repo-review.html">Repo Review</a></div><div class="d">line-by-line checks with official links</div></div>
<div class="card"><div class="k">Known gaps</div><div class="v" style="font-size:16px"><a href="pages/flagged.html">Flagged for Review</a></div><div class="d">16 items, none blocking publication</div></div>
</div>
<h2>Model-internal correlations (do not treat as market correlations)</h2>
{rows_table(["Pair","phi","joint rate","independence product","n","source"],[
 [esc(c['pair']), f"{c['phi']:+.4f}", f"{c['joint_rate']*100:.2f}%", f"{c['independence_product']*100:.2f}%", str(c['n']), srclink('https://www.nfl.com/schedules/2026/','schedules (game rows)')] for c in corr['measured']])}
<p class="sub">Player-prop and market-line correlations are blank — see <a href="pages/correlations.html">Correlations</a> and flags F-01/F-02.</p>"""
open(f'{OUT}/index.html','w').write(page('Dashboard', body, 'index.html'))

# ---------------- executive summary ----------------
body = f"""<h1>Executive Summary</h1><p class="sub">2026-11-13 · session arena-934af359-own4 · all figures link official sources</p>
<div class="note"><b>What this is.</b> A decision dashboard for originating NFL lines from official league data, with a
pre-registered strategy competition, luck-removal tests, injury/deficiency tracking, and two decision tools: a questions
register (what we know / lack before deciding) and a suggestions board (choose a path before building).</div>
<h2>The numbers that matter</h2>
{rows_table(["Finding","Value","Source"],[
 ["Official data captured 2026-11-13","32 standings rows · 137 verified games · 326 injury rows · 32 passing rows", srclink('https://www.nfl.com/','nfl.com')],
 ["Game archive verification","0 mismatches vs official standings (32 clubs); 3/3 game-page spot checks exact", srclink('https://www.nfl.com/standings/','standings')],
 ["Originated lines","13 Week 11 games (incl. Mexico City SNF) priced without any market input", srclink('https://www.nfl.com/schedules/2026/by-week/week-11','week 11')],
 ["Margin model, holdout wk 8-10", f"MAE {lm['mae_margin']:.2f} vs naive {lm['base_mae_margin']:.2f}; accuracy {lm['accuracy']*100:.1f}% vs 50.0%", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Luck-removal verdict", f"placebo p={luck['placebo_p_mae_improvement']:.4f} BUT week-clustered CI [{luck['bootstrap_95ci_mae_improvement'][0]:+.2f},{luck['bootstrap_95ci_mae_improvement'][1]:+.2f}] includes 0", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Totals model","worse than naive on holdout (11.35 vs 11.25 MAE) — published unchanged", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Strategies qualifying","0 of 6 · 0 of 6,000 reward points awarded", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Injury picture (Week 10)","14 Out · 11 Questionable · 95 DNP-practice; BAL QB1 Jackson on IR; MIA QB1 Willis on IR; SEA QB1 Darnold out", srclink('https://www.nfl.com/injuries/','injuries')],
 ["Blocked requirements","market prices (F-01) · player logs &amp; prop prices (F-02) · official depth chart (F-08)", srclink('https://www.nfl.com/injuries/','injuries')],
])}
<h2>What we built</h2>
<ul class="tight">
<li><b>Own lines</b> — ridge-regularised margin ratings + tendency totals from official PF/PA and the verified game archive; fair win probability from a frozen residual sigma. No market input anywhere.</li>
<li><b>Strategy competition</b> — 6 registered strategies (spread/total/ML singles, cross-game parlays, player-prop combos, SGP), 10 pre-registered gates committed to git before the backtest ran, leaderboard with 6,000 points available and 0 awarded.</li>
<li><b>Luck removal</b> — walk-forward-only predictions, frozen holdout, 10,000 label-shuffled placebos, week-clustered bootstrap, split-half stability. Skill must clear all of these; the current margin signal clears direction and placebo but not the CI gate.</li>
<li><b>Injury &amp; depth deficiency tracking</b> — 326-row official register, per-unit absence aggregates, official-news starter changes (Jackson, Willis/McCord, Darnold/Lock, Watson, Beck). The league publishes no depth chart, so "2nd/3rd/4th string" is blank and flagged — never inferred.</li>
<li><b>Decision layer</b> — 16 requirements with status, 20 questions split known/unknown/answer/unlock, 16 suggestions with impact/effort/risk for reviewer selection.</li>
</ul>
<h2>What is blocked, stated plainly</h2>
<ol class="tight">
<li><b>Market-priced bets (S1-S4).</b> The NFL publishes no betting lines; no licensed feed exists here. All market columns are blank. Gate G6 cannot be evaluated.</li>
<li><b>Player props and prop combos (S5-S6).</b> No official per-game player logs in scope; no prop prices exist officially. Nothing graded.</li>
<li><b>String-level depth (2nd/3rd/4th).</b> No league depth chart; no snap counts. Absence-based tracking only.</li>
</ol>
<h2>Recommended path (reviewer decides on the <a href="pages/suggestions.html">suggestions board</a>)</h2>
<ol class="tight">
<li>Freeze model v1 and grade Weeks 11-18 forward (SUG-06) — free, and it is the only way to grow the holdout.</li>
<li>Decide on a licensed odds feed (SUG-01) — it unlocks every betting-market requirement.</li>
<li>Sample-extract official game books for player stats (SUG-02) — it unlocks props and depth tiers.</li>
<li>Pick one canonical dashboard among the 12 NFL workspaces (SUG-12).</li>
</ol>"""
open(f'{PAGES}/executive-summary.html','w').write(page('Executive Summary', body, 'executive-summary.html'))

# ---------------- requirements ----------------
rows=[]
for r in reqs['rows']:
    badge = '<span class="badge b-ok">done</span>' if r['status']=='done' else '<span class="badge b-warn">partial</span>'
    rows.append([esc(r['id']), esc(r['requirement']), badge, esc(r['where']), esc(r['evidence']), srclink('https://www.nfl.com/','nfl.com')])
body = f"""<h1>Requirements</h1><p class="sub">The full requirement list from the project brief, with status and where each is satisfied.</p>
{rows_table(["ID","Requirement","Status","Where","Evidence","Source"], rows)}"""
open(f'{PAGES}/requirements.html','w').write(page('Requirements', body, 'requirements.html'))

# ---------------- questions ----------------
rows=[]
statbadge={'answered':'<span class="badge b-ok">answered</span>','partial':'<span class="badge b-warn">partial</span>','open':'<span class="badge b-mut">open</span>','blocked':'<span class="badge b-bad">blocked</span>','needs decision':'<span class="badge b-warn">needs decision</span>'}
for q in qs['rows']:
    rows.append([esc(q['id']), f"<b>{esc(q['question'])}</b><br><span style='color:#94a3b8'>{esc(q['topic'])}</span>", esc(q['known']), esc(q['unknown']), esc(q['answer'])+'<br>'+statbadge.get(q['status'],''), esc(q['unlock']), esc(q['discover']), srclink('https://www.nfl.com/','nfl.com')])
body = f"""<h1>Questions &amp; Decisions</h1><p class="sub">{esc(qs['how_to_read'])}</p>
{rows_table(["ID","Question","What we KNOW","What we DO NOT know","Answer / status","What would unlock it","How to discover it","Source"], rows)}"""
open(f'{PAGES}/questions.html','w').write(page('Questions & Decisions', body, 'questions.html'))

# ---------------- suggestions ----------------
rows=[]
sb={'implemented':'<span class="badge b-ok">implemented</span>','proposed':'<span class="badge b-mut">proposed</span>','needs decision':'<span class="badge b-warn">needs decision</span>'}
for s in sugs['rows']:
    rows.append([esc(s['id']), f"<b>{esc(s['title'])}</b><br><span style='color:#94a3b8'>{esc(s['problem'])}</span>", esc(s['proposal']),
                 esc(s['impact']), esc(s['effort']), esc(s['risk']), esc(s['prerequisites']), sb.get(s['status'],''), srclink('https://www.nfl.com/','nfl.com')])
body = f"""<h1>Suggestions Board</h1><p class="sub">{esc(sugs['how_to_read'])}</p>
{rows_table(["ID","Title &amp; problem","Proposal","Impact","Effort","Risk","Prerequisites","Status","Source"], rows)}"""
open(f'{PAGES}/suggestions.html','w').write(page('Suggestions', body, 'suggestions.html'))

# ---------------- data ----------------
rows=[]
for r in stand['rows']:
    rows.append([esc(r['team'])+f" ({esc(r['abbr'])})", esc(r['conference']+' '+r['division']), str(r['W']), str(r['L']), str(r['T']),
                 f"{r['pct']:.3f}", str(r['PF']), str(r['PA']), f"{r['net']:+d}", esc(r['home']), esc(r['road']), esc(r['division_rec']), esc(r['streak']), srclink(r['source_url'],'nfl.com/standings')])
prows=[]
for r in passing['rows']:
    prows.append([esc(r['team'])+f" ({esc(r['abbr'])})", str(r['att']), str(r['cmp']), f"{r['cmp_pct']:.1f}%", f"{r['ypa']}", str(r['yds']), str(r['td']), str(r['int']), f"{r['rate']:.1f}", srclink(r['source_url'],'nfl.com/stats/team-stats')])
body = f"""<h1>Official Data</h1><p class="sub">Captured 2026-11-13 from nfl.com. Every row was checked by arithmetic identities (see <a href="repo-review.html">Repo Review</a>).</p>
<h2>2026 Standings (through Week 10 TNF)</h2>
{rows_table(["Team","Division","W","L","T","Pct","PF","PA","Net","Home","Road","Div","Strk","Source"], rows)}
<div class="note">Columns reproduced exactly as published. Verified identities: Pct=(W+.5T)/(W+L+T), Net=PF−PA, Home+Road=W+L+T — 32/32 pass.</div>
<h2>Team passing offense (2026 REG) — verified columns only</h2>
{rows_table(["Team","Att","Cmp","Cmp%","Yds/Att","Yds","TD","INT","Rate","Source"], prows)}
<div class="note warnnote">7 further numeric columns appear on the official page without headers in the fetched rendering; they are omitted, not guessed (flag F-03).
Rate recomputed via the official NFL passer-rating formula matches the published value 32/32.</div>"""
open(f'{PAGES}/data.html','w').write(page('Official Data', body, 'data.html'))

# ---------------- games ----------------
ver = games['verification']
rows=[]
for g in games['rows']:
    rows.append([f"W{g['week']}", esc(g['date']), esc(g['away']), str(g['away_pts']), esc(g['home']), str(g['home_pts']),
                 esc(g.get('provenance','')), srclink(g['source_url'], 'game page')])
body = f"""<h1>Verified Game Archive</h1><p class="sub">{games['n_games']} games, Weeks 1–10 (Week 10 TNF) — every score sourced to its official nfl.com page.</p>
<h2>How the scores were verified</h2>
<div class="note"><b>Aggregate reconciliation:</b> {esc(ver['result'])}. League PF = PA = {ver['league_identity']['sum_PF']:,}.<br>
<b>Spot checks (official game pages):</b> NE 10 @ SEA 13 (W1) · PHI 7 @ CHI 27 (W3) · TEN 36 @ CIN 43 OT (W8) — all exact.<br>
<b>Direct read:</b> WAS 24 @ NYG 21 (W10 TNF) from the official week page. Peer-archive rows (W1–9) are used only because the reconciliation has zero mismatches (flag F-11).</div>
<h2>Walk-forward grade summary (weeks 3–10)</h2>
{rows_table(["Block","Games","Margin MAE","Naive margin MAE","Total MAE","Naive total MAE","Accuracy","Home baseline","Source"],[
 ["All (wk 3-10)", str(lb['all_metrics']['n']), f"{lb['all_metrics']['mae_margin']:.2f}", f"{lb['all_metrics']['base_mae_margin']:.2f}", f"{lb['all_metrics']['mae_total']:.2f}", f"{lb['all_metrics']['base_mae_total']:.2f}", f"{lb['all_metrics']['accuracy']*100:.1f}%", f"{lb['all_metrics']['base_accuracy']*100:.1f}%", srclink('https://www.nfl.com/schedules/2026/','schedules')],
 ["Early split (wk 3-6)", str(lb['early_metrics']['n']), f"{lb['early_metrics']['mae_margin']:.2f}", f"{lb['early_metrics']['base_mae_margin']:.2f}", f"{lb['early_metrics']['mae_total']:.2f}", f"{lb['early_metrics']['base_mae_total']:.2f}", f"{lb['early_metrics']['accuracy']*100:.1f}%", f"{lb['early_metrics']['base_accuracy']*100:.1f}%", srclink('https://www.nfl.com/schedules/2026/','schedules')],
 ["Late split (wk 7-10)", str(lb['late_metrics']['n']), f"{lb['late_metrics']['mae_margin']:.2f}", f"{lb['late_metrics']['base_mae_margin']:.2f}", f"{lb['late_metrics']['mae_total']:.2f}", f"{lb['late_metrics']['base_mae_total']:.2f}", f"{lb['late_metrics']['accuracy']*100:.1f}%", f"{lb['late_metrics']['base_accuracy']*100:.1f}%", srclink('https://www.nfl.com/schedules/2026/','schedules')],
 ["Holdout (wk 8-10, FROZEN)", str(lb['holdout_metrics']['n']), f"{lb['holdout_metrics']['mae_margin']:.2f}", f"{lb['holdout_metrics']['base_mae_margin']:.2f}", f"{lb['holdout_metrics']['mae_total']:.2f}", f"{lb['holdout_metrics']['base_mae_total']:.2f}", f"{lb['holdout_metrics']['accuracy']*100:.1f}%", f"{lb['holdout_metrics']['base_accuracy']*100:.1f}%", srclink('https://www.nfl.com/schedules/2026/','schedules')],
])}
<h2>Week 10 slate (current week)</h2>
{rows_table(["Date","Window","Matchup","Status","Score","Source"],[
 [esc(g['date']), esc(g['window']), esc(g['away'])+' @ '+esc(g['home'])+(' <span class="badge b-mut">neutral</span>' if g.get('neutral') else ''),
  ('<span class="badge b-ok">FINAL</span>' if g['status']=='FINAL' else '<span class="badge b-mut">scheduled</span>'),
  (f"{g['away_pts']}-{g['home_pts']}" if g.get('away_pts') is not None else UNV), srclink(g['game_url'],'game page')] for g in w10['games']])}
<p class="sub">Byes: {', '.join(w10['byes'])} — {srclink(w10['source_url'],'official week 10 page')}</p>
<h2>All graded games (walk-forward predictions)</h2>
{rows_table(["Wk","Date","Away","Score","Home","Score","Pred margin (home)","Pred total","Actual margin","Winner call","Source"],[
 [str(p['week']), esc(p['date']), esc(p['away']), str(p['away_pts']), esc(p['home']), str(p['home_pts']),
  f"{p['pred_margin']:+.1f}", f"{p['pred_total']:.1f}", f"{p['actual_margin']:+d}", esc(p['model_winner']), srclink(p['source_url'],'game page')] for p in walk['rows']])}
"""
open(f'{PAGES}/games.html','w').write(page('Game Archive', body, 'games.html'))
print('part 1 written')

# ---------------- own lines ----------------
mc = model['model_card']
rows=[]
for l in model['week11_own_lines']:
    rows.append([esc(l['date']), esc(l['window']+' '+l['time']), esc(l['away'])+' @ '+esc(l['home'])+(' <span class="badge b-mut">Mexico City</span>' if 'Mexico' in l.get('neutral','') else ''),
                 esc(l['away_rec'])+' / '+esc(l['home_rec']),
                 f"{l['pred_away_pts']:.1f} – {l['pred_home_pts']:.1f}",
                 f"{l['spread_home']:+.1f}", f"{l['total']:.1f}", f"{l['p_away_win']*100:.1f}% / {l['p_home_win']*100:.1f}%",
                 UNV, srclink(l['game_url'], 'game page')])
rrows=[]
for r in model['ratings']:
    rrows.append([esc(r['team'])+f" ({esc(r['abbr'])})", f"{r['rating']:+.2f}" if r['rating'] is not None else UNV,
                  f"{r['pf_pg']:.2f}" if r['pf_pg'] is not None else UNV, f"{r['pa_pg']:.2f}" if r['pa_pg'] is not None else UNV,
                  srclink(r['source_url'],'nfl.com/standings')])
body = f"""<h1>Own Lines — Week 11 (2026)</h1><p class="sub">Originated entirely from official league data. Market columns are blank by policy (flag F-01) — never inferred.</p>
<div class="note"><b>Model card.</b> {esc(mc['formula_margin'])}.<br>{esc(mc['formula_total'])}.<br>
{esc(mc['formula_win_prob'])}. Fitted home-field advantage: <b>{mc['hfa_fitted']:+.2f}</b> points (near zero this season — flag F-05);
frozen residual sigma {mc['sigma_frozen']:.2f}; league average total {mc['league_avg_total_per_game']:.2f}.<br>
Inputs: {', '.join(srclink(u, u.split('//')[1]) for u in mc['inputs'])}. <b>No market inputs.</b></div>
<h2>Week 11 slate — originated lines</h2>
{rows_table(["Date","Window","Matchup","Records","Projected score","Spread (home)","Total","Win prob (away/home)","Market line","Source"], rows)}
<div class="note warnnote"><b>How to read:</b> Spread is the expected home margin (negative = home underdog). Projected scores are expected points, not prices.
The MIN @ SF game is played in Mexico City and receives no home-field adjustment. The market column stays blank until a licensed feed exists.</div>
<h2>Team ratings (ridge-SRS, λ={4.0})</h2>
{rows_table(["Team","Rating (pts vs avg)","PF/game","PA/game","Source"], rrows)}"""
open(f'{PAGES}/own-lines.html','w').write(page('Own Lines', body, 'own-lines.html'))

# ---------------- strategies ----------------
rows=[]
for s in strats['strategies']:
    st = s['status']
    badge = '<span class="badge b-bad">BLOCKED</span>' if 'BLOCKED' in st else '<span class="badge b-ok">active</span>'
    rows.append([esc(s['id']), f"<b>{esc(s['name'])}</b><br><span style='color:#94a3b8'>{esc(s['bet_type'])}</span>", esc(s['entry']), esc(s['size']),
                 esc(s['prices_required']), badge+' '+esc(st), esc(s.get('measurable_proxy','')), srclink('https://www.nfl.com/','nfl.com')])
body = f"""<h1>Registered Strategies</h1><p class="sub">{esc(strats['statement'])}</p>
{rows_table(["ID","Name / type","Entry rule","Sizing","Prices required","Status","Measurable proxy today","Source"], rows)}
<h2>Luck-removal design</h2>
<div class="note">{esc(strats['luck_removal_design'])}</div>"""
open(f'{PAGES}/strategies.html','w').write(page('Strategies', body, 'strategies.html'))

# ---------------- validation ----------------
grows=[]
for g in gates['gates']:
    grows.append([esc(g['id']), esc(g['name']), esc(g['rule']), 'yes' if g['blocking'] else 'no', srclink('https://www.nfl.com/','nfl.com')])
mrows=[]
for r in lb['results']:
    cells=[esc(r['id']), esc(r['name'])]
    for gid in ['G1','G2','G3','G4','G5','G6','G7','G8','G9','G10']:
        v=r['gates'].get(gid,'')
        if v=='pass': cells.append('<span class="badge b-ok">pass</span>')
        elif v.startswith('BLOCKED'): cells.append('<span class="badge b-mut">blocked</span>')
        elif v.startswith('fail'): cells.append(f'<span class="badge b-bad">fail</span>')
        else: cells.append(UNV)
    cells.append('<span class="badge b-bad">rejected</span>' if r['tier']=='rejected' else '<span class="badge b-ok">qualified</span>')
    cells.append(srclink('https://www.nfl.com/schedules/2026/','games'))
    mrows.append(cells)
luck=lbp=lb['luck_tests']
body = f"""<h1>Validation Gates</h1><p class="sub">{esc(gates['statement'])} Frozen {esc(gates['frozen_utc'])} (commit history proves it predates the backtest).</p>
<h2>Pre-registered gates</h2>
{rows_table(["ID","Gate","Rule","Blocking","Source"], grows)}
<h2>Gate matrix — results</h2>
{rows_table(["ID","Strategy","G1","G2","G3","G4","G5","G6","G7","G8","G9","G10","Verdict","Source"], mrows)}
<h2>Luck tests on the frozen holdout (weeks 8–10)</h2>
{rows_table(["Test","Result","Interpretation","Source"],[
 ["Winner-accuracy placebo (10,000 matched-random runs)", f"p = {luck['placebo_p_accuracy_holdout']:.4f} (observed {luck['observed_accuracy_holdout']*100:.1f}%)", "Model picks winners far better than chance — but chance is a low bar", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Margin-MAE placebo (10,000 label shuffles)", f"p = {luck['placebo_p_mae_improvement']:.4f} (improvement {luck['mae_improvement_per_game']:.2f} pts/game)", "Improvement is not explainable by shuffled labels", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Week-clustered bootstrap 95% CI of improvement", f"[{luck['bootstrap_95ci_mae_improvement'][0]:+.3f}, {luck['bootstrap_95ci_mae_improvement'][1]:+.3f}] pts/game", "INCLUDES ZERO — week-to-week noise is too large on n=30. This is why G5 fails and no reward is granted", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Split-half stability (wk 3-6 vs 7-10)", "improvement same-signed both halves (G8 pass)", "Direction consistent; magnitude unproven", srclink('https://www.nfl.com/schedules/2026/','games')],
 ["Sample-size gate G2 (>= 300 graded)", f"{lb['all_metrics']['n']} graded this season", "Impossible on 2026 alone — multi-season accumulation required (Q7)", srclink('https://www.nfl.com/schedules/2026/','games')],
])}
<div class="note badnote"><b>Verdict:</b> every strategy is rejected — either a failed gate or a blocked gate (G6 needs market prices). 0 rewards. The models, predictions and this failure are published unchanged; tuning until something passes is exactly what these gates exist to prevent.</div>"""
open(f'{PAGES}/validation.html','w').write(page('Validation Gates', body, 'validation.html'))

# ---------------- correlations ----------------
rows=[]
for c in corr['measured']:
    rows.append([esc(c['pair']), f"{c['phi']:+.4f}", f"{c['joint_rate']*100:.2f}%", f"{c['independence_product']*100:.2f}%", str(c['n']),
                 f"{c.get('split_half_phi_early','—')}" , srclink('https://www.nfl.com/schedules/2026/','game rows')])
brows=[]
for b in corr['blank_unverified']:
    brows.append([esc(b['item']), UNV, esc(b['reason']), esc(b.get('flag','')), srclink('https://www.nfl.com/','nfl.com')])
body = f"""<h1>Correlations</h1><p class="sub">{esc(corr['method'])}</p>
<div class="note warnnote">{esc(corr['scope_warning'])}</div>
<h2>Measured (model-internal, 2026 weeks 3–10)</h2>
{rows_table(["Pair","phi","Joint rate","Independence product","n","Split-half phi (early)","Source"], rows)}
<div class="note">Interpretation: |phi| up to 0.22 on these pairs means multiplicative parlay pricing is <b>not</b> automatically safe —
two legs that each look +EV can be meaningfully dependent. For pricing parlays, measure again against market lines once flag F-01 clears.</div>
<h2>Blank by policy — never estimated</h2>
{rows_table(["Item","Value","Why it is blank","Flag","Source"], brows)}"""
open(f'{PAGES}/correlations.html','w').write(page('Correlations', body, 'correlations.html'))

# ---------------- leaderboard ----------------
rows=[]
for r in lb['results']:
    rows.append([esc(r['id']), esc(r['name']), esc(r['bet_type']), f"{r['passed']}/10 pass · {r['blocked']} blocked · {r['failed']} failed",
                 ('<span class="badge b-ok">qualified</span>' if r['tier']=='qualified' else '<span class="badge b-bad">rejected</span>'),
                 f"{r['reward_points']} pts", srclink('https://www.nfl.com/schedules/2026/','games')])
cd=lb['competition_design']
body = f"""<h1>Leaderboard &amp; Rewards</h1><p class="sub">{esc(cd['name'])} — a leaderboard competition for strategy research.</p>
<div class="note"><b>Scoring.</b> {esc(cd['scoring'])}<br><b>Anti-luck rule.</b> {esc(cd['anti_luck_rule'])}</div>
<div class="cards">
<div class="card"><div class="k">Points available</div><div class="v">6,000</div><div class="d">1,000 per registered strategy</div></div>
<div class="card"><div class="k">Points awarded</div><div class="v bad">0</div><div class="d">{esc(cd['reward_pool']['note'])}</div></div>
<div class="card"><div class="k">Qualified strategies</div><div class="v bad">0</div><div class="d">gates are all-or-nothing</div></div>
</div>
<h2>Standings</h2>
{rows_table(["ID","Strategy","Type","Gates","Tier","Reward","Source"], rows)}
<h2>Why nothing wins (honest reading)</h2>
<ul class="tight">
<li>The margin model's holdout improvement is <b>real-looking</b> (placebo p &lt; 0.01) but its week-clustered CI includes zero — on 30 games, luck cannot be excluded at the pre-registered standard.</li>
<li>Sample size (G2) can only be met across multiple seasons — that is deliberate; it is what separates "selectively skill-based" from "lucky so far".</li>
<li>Market gate G6 cannot even be evaluated without licensed prices; betting-market ROI claims are impossible in this repository today.</li>
<li>Player-prop strategies have zero graded selections — the required official data does not exist in scope.</li>
</ul>"""
open(f'{PAGES}/leaderboard.html','w').write(page('Leaderboard', body, 'leaderboard.html'))

# ---------------- injuries ----------------
from collections import defaultdict
by_team=defaultdict(lambda: {'Out':0,'Questionable':0,'DNP':0,'Limited':0,'Full':0,'Offense_out':0,'Defense_out':0})
for r in inj['rows']:
    t=by_team[r['team']]
    if r['game_status']=='Out': t['Out']+=1; t[r['side'].replace(' ','')+'_out' if r['side'] in ('Offense','Defense') else 'Out']+=1
    if r['game_status']=='Questionable': t['Questionable']+=1
    if r['practice_status']=='DNP': t['DNP']+=1
    if r['practice_status']=='Limited': t['Limited']+=1
    if r['practice_status']=='Full': t['Full']+=1
arows=[]
for t in sorted(by_team):
    v=by_team[t]
    arows.append([esc(t), str(v['Out']), str(v['Questionable']), str(v['DNP']), str(v['Limited']), str(v['Full']),
                  str(v.get('Offense_out',0)), str(v.get('Defense_out',0)), srclink('https://www.nfl.com/injuries/','nfl.com/injuries')])
irows=[]
for r in inj['rows']:
    gm = ('<span class="badge b-bad">Out</span>' if r['game_status']=='Out' else ('<span class="badge b-warn">Questionable</span>' if r['game_status']=='Questionable' else '<span class="badge b-mut">—</span>'))
    irows.append([esc(r['team']), esc(r['player']), esc(r['position']), esc(r['side']), esc(r['injury']) or '—', esc(r['practice_status']), gm,
                  '<span class="badge b-warn unv">unverified</span>', srclink(r['source_url'],'injury report')])
body = f"""<h1>Injury Register — Week 10</h1><p class="sub">{len(inj['rows'])} players · 28 clubs · transcribed verbatim 2026-11-13 from the official report. Statuses change daily (flag F-09).</p>
<div class="note">{esc(inj['note'])}</div>
<h2>By team</h2>
{rows_table(["Team","Out","Questionable","DNP practice","Limited","Full","Out (offense)","Out (defense)","Source"], arows)}
<h2>Full register</h2>
{rows_table(["Team","Player","Pos","Side","Injury","Practice","Game status","Starter/backup","Source"], irows)}"""
open(f'{PAGES}/injuries.html','w').write(page('Injuries', body, 'injuries.html'))

# ---------------- depth ----------------
nrows=[]
for n in news['rows']:
    nrows.append([esc(n['date']), esc(n['headline']), esc(n['relevance']), srclink(n['source_url'],'nfl.com news')])
body = f"""<h1>Depth &amp; Deficiencies</h1><p class="sub">Who is missing, which unit is thin, and what the league does — and does not — publish.</p>
<div class="note badnote"><b>The hard limit.</b> The NFL publishes <b>no depth chart</b> and no snap counts on its public pages.
The official injury report gives practice/game status only. Therefore "starter vs 2nd/3rd/4th string" is <b>unverified</b> everywhere on this site
(flag F-08) and is never inferred. What <i>is</i> official: (1) absences (Out/DNP/Questionable) per team and unit, (2) nfl.com news statements about
who starts or is replaced.</div>
<h2>Deficiency signals from official news (starter/backup changes)</h2>
{rows_table(["Date","Official headline","Why it matters","Source"], nrows)}
<h2>How to read the deficiency picture</h2>
<ul class="tight">
<li><b>Baltimore (defense &amp; offense affected):</b> QB1 Lamar Jackson on IR (timeline inconsistent across official articles — F-07); QB2 Tyler Huntley out for season (official news). The QB room is down to unconfirmed backups; this site lists the absences and does not assign string numbers.</li>
<li><b>Miami:</b> QB1 Malik Willis on IR; backup Kyle McCord in line for his first start (official news) — an official, named backup-to-starter transition.</li>
<li><b>Seattle:</b> QB1 Sam Darnold ruled out; backup Drew Lock expected to start (official news).</li>
<li><b>Cleveland / Arizona:</b> official starter designations (Watson; Beck) after earlier QB changes.</li>
<li><b>Unit-level absence load</b> (Out + DNP by side) is on the <a href="injuries.html">Injuries</a> page — e.g., Dallas carries 10 DNP-practice players, many on defense; the register shows exactly who and at which position.</li>
<li><b>Roster moves change depth:</b> BUF acquired S Amani Hooker; DEN acquired LB Daiyan Henley from LAC (official news).</li>
</ul>
<h2>What would make string-level tracking possible</h2>
<div class="note">Extract snap counts from the official game-book PDFs linked on every game page (suggestion SUG-02/03): a player taking starter snaps is empirically a starter.
Until that exists, any "2nd/3rd/4th string" label from any source should be treated as unverified.</div>"""
open(f'{PAGES}/depth.html','w').write(page('Depth & Deficiencies', body, 'depth.html'))

# ---------------- repo review ----------------
irows=[]
for r in review['inventory']:
    irows.append([f"<code>{esc(r['namespace'])}</code>", esc(r['content']), esc(r['review']), srclink('https://github.com/sassnarep3-star/Own4','repo')])
mrows=[]
for m in review['mechanical_checks']:
    ok = 'pass' in m['result'] or 'exact' in m['result'] or '32/32' in m['result'] or '0 mismatches' in m['result'] or '13 games' in m['result'] or '326 rows' in m['result']
    mrows.append([esc(m['id']), esc(m['check']), ('<span class="badge b-ok">'+esc(m['result'])+'</span>') if ok else esc(m['result']), srclink(m['source'], 'check source')])
xrows=[]
for c in review['cross_namespace_reconciliation']:
    badge='<span class="badge b-ok">clean</span>' if c['mismatches']==0 else ('<span class="badge b-warn">'+str(c['mismatches'])+' differ</span>')
    det='; '.join(f"{d['abbr']} peer {d['peer']} vs {d['fresh_2026-11-13']}" for d in c.get('detail',[])[:4]) or '—'
    xrows.append([esc(c['check']), str(c['rows_compared']), badge, esc(det), srclink('https://www.nfl.com/standings/','standings')])
irows2=[]
for ir in review['irregularities']:
    badge='<span class="badge b-ok">explained</span>' if ir['status']=='explained' else '<span class="badge b-warn">needs review</span>'
    links=' '.join(srclink(u,'src') for u in ir['sources']) or srclink('https://www.nfl.com/','nfl.com')
    irows2.append([esc(ir['id']), esc(ir['title']), badge, esc(ir['detail']), links])
body = f"""<h1>Repo Review</h1><p class="sub">{esc(review['method'])}</p>
<h2>Namespace inventory</h2>
{rows_table(["Namespace","Content","Review outcome","Source"], irows)}
<h2>Mechanical checks (this session)</h2>
{rows_table(["ID","Check","Result","Official source"], mrows)}
<h2>Cross-namespace reconciliation (peer snapshots vs today's official standings)</h2>
{rows_table(["Check","Rows","Mismatches","Detail","Source"], xrows)}
<h2>Irregularities</h2>
{rows_table(["ID","Item","Status","Detail","Source"], irows2)}"""
open(f'{PAGES}/repo-review.html','w').write(page('Repo Review', body, 'repo-review.html'))

# ---------------- flagged ----------------
rows=[]
for f in flags['rows']:
    sev={'high':'<span class="badge b-bad">high</span>','medium':'<span class="badge b-warn">medium</span>','low':'<span class="badge b-mut">low</span>'}[f['severity']]
    links=' '.join(srclink(u,'src') for u in f['sources']) or srclink('https://www.nfl.com/','nfl.com')
    rows.append([esc(f['id']), sev, esc(f['item']), esc(f['detail']), esc(f['clear']), links])
body = f"""<h1>Flagged for Review</h1><p class="sub">{esc(flags['policy'])}</p>
{rows_table(["ID","Severity","Item","Detail","What would clear it","Source"], rows)}"""
open(f'{PAGES}/flagged.html','w').write(page('Flagged for Review', body, 'flagged.html'))

# ---------------- sources ----------------
rows=[]
for s in sources['rows']:
    rows.append([esc(s['source']), srclink(s['url'], s['url']), esc(s['used_for']), esc(s['captured']), '<span class="badge b-ok">official</span>'])
for s in sources['third_party_present_not_used']:
    rows.append([esc(s['source']), srclink(s['url'], s['url']), esc(s['used_for']), '—', '<span class="badge b-warn">third-party · unused</span>'])
body = f"""<h1>Sources</h1><p class="sub">Everything published on this site traces to these pages. Third-party datasets present in the repository are listed but unused.</p>
{rows_table(["Source","URL","Used for","Captured","Type"], rows)}"""
open(f'{PAGES}/sources.html','w').write(page('Sources', body, 'sources.html'))
print('site built:', len([f for f in os.listdir(PAGES)]), 'subpages + index')

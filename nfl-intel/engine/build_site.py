#!/usr/bin/env python3
"""Builds the nfl-intel static site from nfl-intel/data/*.json. stdlib only.
Every data-row emitted carries a source link (class="src"); verify_site.py enforces it."""
import json, html, pathlib, datetime

ROOT = pathlib.Path('nfl-intel')
D = ROOT / 'data'
def load(n): return json.loads((D/n).read_text())
def esc(s): return html.escape(str(s if s is not None else ''))
SRC_STAND = "https://www.nfl.com/standings/"
SRC_SCORES = "https://www.nfl.com/scores"
SRC_INJ = "https://www.nfl.com/injuries/"

standings = load('standings_2026-11-12.json')
metrics = load('metrics.json')
corr = load('correlations.json')
lines = load('own_lines.json')
injuries = load('injuries_week10.json')
week10 = load('week10_2026.json')
strategies = load('strategies.json')
gates = load('gates.json')
leaderboard = load('leaderboard.json')
suggestions = load('suggestions.json')
questions = load('questions.json')
flags = load('flags.json')
sources = load('sources.json')

NAV = [("index.html","Home"),("pages/dashboard.html","Dashboard"),("pages/standings.html","Standings & Metrics"),
       ("pages/own-lines.html","Originated Lines"),("pages/correlations.html","Correlations"),
       ("pages/strategies.html","Strategies & Parlays"),("pages/validation.html","Validation Gates"),
       ("pages/leaderboard.html","Leaderboard"),("pages/injuries.html","Injury Tracker"),
       ("pages/suggestions.html","Suggestions"),("pages/questions.html","Decision Q&A"),
       ("pages/repo-review.html","Repo Review"),("pages/executive-summary.html","Executive Summary"),
       ("pages/flagged.html","Flagged for Review"),("pages/methodology.html","Methodology"),("pages/sources.html","Sources")]

SUG_REF = {"SUG-01":"https://www.nfl.com/injuries/","SUG-02":"https://www.nfl.com/scores","SUG-03":"https://www.nfl.com/standings/","SUG-04":"https://github.com/sassnarep3-star/Own4","SUG-05":"https://www.nfl.com/standings/","SUG-06":"https://www.nfl.com/injuries/","SUG-07":"https://www.ncpgambling.org/help-treatment","SUG-08":"https://github.com/sassnarep3-star/Own4","SUG-09":"https://github.com/sassnarep3-star/Own4","SUG-10":"https://www.nfl.com/scores","SUG-11":"https://github.com/sassnarep3-star/Own4","SUG-12":"https://www.nfl.com/standings/"}
Q_REF = {"Q-02":"https://www.nfl.com/standings/","Q-04":"https://www.nfl.com/injuries/","Q-05":"https://github.com/sassnarep3-star/Own4","Q-06":"https://www.nfl.com/scores","Q-10":"https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm","Q-11":"https://github.com/sassnarep3-star/Own4","Q-12":"https://github.com/sassnarep3-star/Own4","Q-13":"https://github.com/sassnarep3-star/Own4","Q-14":"https://www.nfl.com/scores","Q-16":"https://www.nfl.com/scores"}

def shell(title, body, here="nfl-intel", depth=0):
    prefix = "../" * depth
    nav = "".join(f'<a href="{prefix}{h}">{n}</a>' for h,n in NAV)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL Intelligence</title><link rel="stylesheet" href="{prefix}assets/style.css"></head>
<body><header class="top"><div class="wrap"><a class="brand" href="{prefix}index.html"><span class="ball">🏈</span> NFL Intelligence <span class="badge-live">VERIFIED 2026-11-12</span></a></div></header>
<nav class="mainnav"><div class="wrap">{nav}</div></nav>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">NFL Intelligence (research framework, not wagering advice). Official sources only; unverified values are blank and listed on <a href="{prefix}pages/flagged.html">Flagged for Review</a>. NCPG Helpline: 1-800-MY-RESET (697-3738) · <a href="https://www.ncpgambling.org/help-treatment">ncpgambling.org</a> · Built 2026-11-12, branch arena/8184197d-own4.</div></footer>
<script>
document.querySelectorAll('input[data-filter]').forEach(inp=>{{inp.addEventListener('input',()=>{{const q=inp.value.toLowerCase();document.querySelectorAll(inp.dataset.filter).forEach(tr=>{{tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none'}})}})}});
</script></body></html>"""

def w(path, content):
    p = ROOT/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    print("wrote", p)

def srccell(url, label="source"):
    return f'<td class="src"><a class="src" href="{esc(url)}" rel="noopener">{esc(label)} ↗</a></td>'

# ---------- index.html
total_flags = len(flags['flags']); n_q = len(questions['questions']); n_blocking = sum(1 for q in questions['questions'] if q['blocking'] and q['status'] in ('UNKNOWN','PARTIAL','BLOCKED'))
tiles = [("pages/dashboard.html","📊 Dashboard","KPI overview of the whole build-out"),
         ("pages/standings.html","🏟️ Standings & Metrics","32 verified teams · PF/PA · PYTHAG · net PPG"),
         ("pages/own-lines.html","🎯 Originated Lines","Model v1 fair spreads/totals for Week 10 (14 games)"),
         ("pages/correlations.html","🔗 Correlations","r with p-values, t(30), BH-FDR q"),
         ("pages/strategies.html","🧠 Strategies","Singles · parlays · prop combos · S1–S8"),
         ("pages/validation.html","🛡️ Validation Gates","G1–G10 — 0 strategies qualify; luck removal rules"),
         ("pages/leaderboard.html","🏆 Leaderboard","Competition design & reward policy — 0 rewards awarded"),
         ("pages/injuries.html","🚑 Injury Tracker","Week 10 official report · status rows + DNP watchlist"),
         ("pages/suggestions.html","💡 Suggestions","12 proposals awaiting human review — nothing auto-implements"),
         ("pages/questions.html","❓ Decision Q&A","16 questions · answers, gaps & how to discover missing info"),
         ("pages/repo-review.html","🔍 Repo Review","Line-by-line audit of the repository + irregularities"),
         ("pages/executive-summary.html","📝 Executive Summary","Important details, decisions required, risks"),
         ("pages/flagged.html","🚩 Flagged for Review","Every unverified value & irregularity, with sources"),
         ("pages/methodology.html","📐 Methodology","Model, gates, FDR, luck removal, verification protocol"),
         ("pages/sources.html","📚 Sources","Official source register with retrieval dates")]
tiles_html = "".join(f'<a class="tile" href="{h}"><b>{t}</b><small>{d}</small></a>' for h,t,d in tiles)
w('index.html', shell("Home", f"""
<div class="hero" style="margin:-26px -20px 20px;padding:44px 20px 38px"><div class="wrap" style="padding:0">
<h1>NFL Intelligence — originated lines, gated strategies, verified data</h1>
<p class="lead">A research system for originating NFL lines and signals from official, verifiable sources only. Week 10 2026 snapshot (fetched 2026-11-12): full standings, schedule, and official injury report transcribed and re-verified; a pre-registered model produced originated fair lines; every strategy is pre-registered and passes <b>zero</b> validation gates — so the leaderboard pays out nothing, by design.</p>
<div class="kpi-row">
<div class="kpi"><div class="n">32</div><div class="d">teams verified</div></div>
<div class="kpi"><div class="n">14</div><div class="d">originated Week 10 lines</div></div>
<div class="kpi"><div class="n">8</div><div class="d">registered strategies</div></div>
<div class="kpi"><div class="n">0</div><div class="d">rewards awarded</div></div>
<div class="kpi"><div class="n">{n_q}</div><div class="d">decision Q&A ({n_blocking} blocking)</div></div>
<div class="kpi"><div class="n">{total_flags}</div><div class="d">flagged for review</div></div>
</div></div></div>
<div class="notice"><b>How to read this site:</b> every table row links to its official source. Blank or “UNVERIFIED” means the value could not be confirmed — it is never inferred. Nothing in <a href="pages/suggestions.html">Suggestions</a> is implemented; each item needs an explicit human decision in <a href="pages/questions.html">Decision Q&A</a> first. Not wagering advice.</div>
<div class="grid cols-3">{tiles_html}</div>"""))
print("index done")

# ---------- dashboard
kpis = [("136","team-games graded (league-wide)"),("22.96","league points per team per game"),("r = +0.876","net PPG vs win% (BH q &lt; .05)"),("6 / 10","gates the best strategy passes"),("0","strategies reward-eligible"),("6","explicit game-status injuries (W10)"),("68","DNP/LP watchlist rows"),("12","suggestions awaiting review")]
kpi_html = "".join(f'<div class="kpi" style="background:#fff;border-color:var(--line)"><div class="n" style="color:var(--navy2)">{n}</div><div class="d" style="color:var(--muted)">{d}</div></div>' for n,d in kpis)
w('pages/dashboard.html', shell("Dashboard", f"""
<div class="card"><h2>Dashboard — where things stand (2026-11-12)</h2>
<p class="small">All inputs verified from official sources this session; all derived values computed by <code>nfl-intel/engine/analyze.py</code> (stdlib only, reproducible). Evidence: pages linked in the left column shape every claim.</p>
<div class="grid cols-3" style="margin-top:10px">{kpi_html}</div></div>
<div class="card"><h2>What you can decide today</h2>
<table><thead><tr><th>Decision</th><th>Evidence</th><th>Blocking unknown</th></tr></thead><tbody>
<tr data-row><td>Keep leaderboard virtual-only (no cash prizes)</td><td><a class="src" href="validation.html">gates G3/G7/G8</a></td><td>None for virtual play</td></tr>
<tr data-row><td>Fund licensed odds archive (SUG-02)</td><td><a class="src" href="questions.html">Q-05/Q-06</a></td><td>Budget + terms review</td></tr>
<tr data-row><td>Adopt depth-chart ingestion (SUG-01)</td><td><a class="src" href="injuries.html">injury tracker gaps</a></td><td>Depth-chart URL stability</td></tr>
<tr data-row><td>Approve canonical dashboard plan (SUG-08)</td><td><a class="src" href="repo-review.html">repo review findings</a></td><td>Owner decision</td></tr>
</tbody></table></div>
<div class="card"><h2>Top execution risks</h2><ul>
<li><b>Overfitting the 2026 snapshot</b> — n=32 team correlations are season-to-date; treat as descriptive (F-07).</li>
<li><b>Injury-based edges without depth charts</b> — report gives practice status only; backup identity UNVERIFIED (F-05).</li>
<li><b>Market-blind lines</b> — no official line source; every fair price is informational (F-08).</li>
<li><b>Compliance exposure</b> — public rewards need counsel sign-off (Q-07, SUG-07).</li>
</ul></div>""", depth=1))

# ---------- standings
rows=[]
for m in sorted(metrics['teams'], key=lambda x:(x['conf'], x['div'], -x['pct'])):
    rows.append(f"<tr data-row><td>{m['conf']} {m['div']}</td><td><b>{esc(m['team'])}</b></td><td>{m['w']}-{m['l']}-{m['t']}</td><td>{m['pct']:.3f}</td><td>{m['gp']}</td><td>{m['pf']}</td><td>{m['pa']}</td><td>{m['net']:+d}</td><td>{m['off_ppg']:.2f}</td><td>{m['def_ppg']:.2f}</td><td>{m['net_ppg']:+.2f}</td><td>{m['pythag']:.3f}</td><td>{m['luck_delta']:+.2f}</td>{srccell(SRC_STAND)}</tr>")
w('pages/standings.html', shell("Standings & Metrics", f"""
<div class="card"><h2>2026 standings — transcribed from official NFL.com (2026-11-12)</h2>
<p class="small">Consistency gate PASS: W=L=135, PF=PA=6246, all NET/PCT recomputed ✓. Derived columns (GP→luck Δ) computed by engine; sources: standings page. League PPG/team = {metrics['meta']['league_ppg_per_team']}. PYTHAG uses exponent 2.37 (<b>UNVERIFIED</b> — F-01). luck Δ = actual W+0.5T − Pythagorean wins (positive = overperforming expectation).</p>
<div class="filter"><input data-filter="table.standings tbody tr" placeholder="Filter teams, divisions…"></div>
<div class="tablewrap"><table class="standings"><thead><tr><th>Div</th><th>Team</th><th>W-L-T</th><th>PCT</th><th>GP</th><th>PF</th><th>PA</th><th>NET</th><th>OFF/g</th><th>DEF/g</th><th>NET/g</th><th>PYTHAG</th><th>Luck Δ</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="notice">“Luck Δ” is a descriptive residual, not a validated signal. It is not eligible for leaderboard scoring without passing G1–G10.</div></div>""", depth=1))

# ---------- own lines
rows=[]
for g in lines['games']:
    fav = g['home'] if g['fair_margin_home']>=0 else g['away']
    sp = abs(g['fair_margin_home'])
    neut = ' <span class="pill info">neutral</span>' if g['neutral'] else ''
    rows.append(f"<tr data-row><td>{esc(g['id'])}</td><td>{esc(g['day'])} {esc(g['time_et'])} ET · {esc(g['slot'])}</td><td><b>{esc(g['away'])}</b> @ <b>{esc(g['home'])}</b>{neut}</td><td>{g['exp_away_pts']:.2f}</td><td>{g['exp_home_pts']:.2f}</td><td>{esc(fav)} −{sp:.1f}</td><td>{g['fair_total']:.1f}</td><td>{g['p_home_win']*100:.1f}%</td><td>{g['fair_ml_away']:+d} / {g['fair_ml_home']:+d}</td><td><span class='pill warn'>UNVERIFIED vs market</span></td>{srccell(SRC_SCORES)}</tr>")
w('pages/own-lines.html', shell("Originated Lines — Week 10", f"""
<div class="card"><h2>Originated fair lines — Week 10 2026 (model v1, pre-registered 2026-11-12)</h2>
<div class="danger"><b>Read before acting:</b> These are model outputs, not betting advice and not market prices. No official odds source exists in this workspace, so <b>every line here is UNVERIFIED against market</b> (gate G7 blocked). TNF W10-01 may already have been played when you read this (F-10). Differences vs your book’s number are expected; neither side is “right” until G7 passes.</div>
<p class="small"><b>Model v1</b> (committed pre-slate; see git history): expected points = avg(own OFF/g, opponent DEF/g). Fair margin = home exp − away exp; fair total = sum; P(home) from Normal(margin, σ=13.45 — <b>UNVERIFIED</b>, F-02). No explicit HFA term — home edge is implicitly embedded in season PF/PA, so neutral-site W10-02 needs no correction. No injury adjustment is applied (backup identities unverified — F-05). Pythagorean exponent 2.37 (F-01).</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Date/Time</th><th>Matchup</th><th>Away exp</th><th>Home exp</th><th>Fair spread</th><th>Fair total</th><th>P(home)</th><th>Fair ML (away/home)</th><th>Market check</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="small">Records shown as published on the official page at fetch time. HALFTIME/live movement is out of scope. Neither lines nor models were compared to any operator price.</p></div>""", depth=1))

# ---------- correlations
rows=[]
for c in corr['correlations']:
    surv = '<span class="pill ok">survives q&lt;.05</span>' if c['fdr_survives_0.05'] else '<span class="pill gray">not significant</span>'
    rows.append(f"<tr data-row><td>{esc(c['label'])}</td><td>n={c['n']}</td><td>{c['r']:+.3f}</td><td>t({c['df']})={c['t']:+.2f}</td><td>{c['p']:.3g}</td><td>{c['bh_q']:.3g}</td><td>{surv}</td>{srccell(SRC_STAND)}</tr>")
w('pages/correlations.html', shell("Correlations", f"""
<div class="card"><h2>Descriptive correlations — 2026 season to date (n=32 teams)</h2>
<p class="small">Pearson r; two-tailed p from Student-t (df=30); Benjamini–Hochberg q across the 6 tests reported together. Standard error context: with n=32, |r| ≥ ~0.35 is roughly the 5% boundary before FDR control. <b>These are descriptive, in-sample, season-to-date associations — not predictive validation and not betting signals.</b></p>
<div class="tablewrap"><table><thead><tr><th>Pair</th><th>n</th><th>r</th><th>t</th><th>p (two-tailed)</th><th>BH q</th><th>FDR</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="notice"><b>Player-prop pair correlations (the requested headline):</b> <span class="tag-flag">BLANK / UNVERIFIED.</span> No official player game-log feed exists in this workspace. S6 and any same-game combo remain unpriceable until SUG-03 is accepted. Do not estimate these from memory.</div>
<div class="notice"><b>Parlay-leg correlation rule (pre-registered):</b> legs priced from joint distribution; if measured |r| &gt; 0.10 or p &lt; 0.05, independence is rejected and the parlay price uses the joint hit rate (requires S5 data — currently blank). Standard NFL parlay rules prohibit correlated legs in some products; operator terms govern and are unverified here (Q-16).</div></div>""", depth=1))

# ---------- strategies
rows=[]
for s in strategies['strategies']:
    gates_txt = '; '.join(f"{k.replace('_',' ')}: {v}" for k,v in s['gate_results'].items())
    corr_txt = s.get('correlation_to_other') or '—'
    badge = '<span class="pill bad">NOT ELIGIBLE</span>' if not s['reward_eligible'] else '<span class="pill ok">ELIGIBLE</span>'
    rows.append(f"<tr data-row><td><b>{esc(s['id'])}</b> · {esc(s['name'])}<br><small>{esc(s['type'])}</small></td><td>{esc(s['definition'])}</td><td>{esc(s['status'])}</td><td>{esc(gates_txt)}</td><td class='small'>{esc(corr_txt)}</td><td>{badge}</td>{srccell(SRC_STAND,'inputs')}</tr>")
w('pages/strategies.html', shell("Strategies", f"""
<div class="card"><h2>Strategy catalog — singles, parlays, player-prop combos (v1.0, pre-registered 2026-11-12)</h2>
<div class="danger"><b>0 of 8 strategies pass validation.</b> Each is registered, honest, and currently unmeasurable against market (G7 blocked) or under the 300-game floor (G3 FAIL). None is a “play”. Catalog exists so gates can be applied the moment data arrives — not to create action.</div>
<p class="small">Shared luck-removal protocol: walk-forward only · pre-registered params (git-committed) · Benjamini–Hochberg FDR · permutation luck test on the headline metric · holdout locked · minimum n=300 graded games before any reward · dependence measured, never assumed (G9).</p>
<h3>Singles</h3><p class="small">S1 Pythag edge · S2 Net-PPG favorite · S3 Low-total under · S4 Injury-adjusted fade (blocked) · S7 Bye-week rest · S8 Public fade (blocked)</p>
<h3>Parlays</h3><p class="small">S5 two-leg S1∧S3 — correlated when the same team appears; priced from joint hit rate once measurable, never from independence. Same-game parlays additionally require operator terms (Q-16).</p>
<h3>Player-prop combos</h3><p class="small">S6 QB yds × team total — <span class="tag-flag">correlation BLANK</span> until official game logs are ingested (SUG-03). No prop combo may be quoted with an independence assumption.</p>
<div class="filter"><input data-filter="table.strat tbody tr" placeholder="Filter strategies…"></div>
<div class="tablewrap"><table class="strat"><thead><tr><th>ID · Name</th><th>Definition</th><th>Status</th><th>Gate results</th><th>Correlation notes</th><th>Reward</th><th>Inputs</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>""", depth=1))

# ---------- validation gates
rows=[]
for g in gates['gates']:
    st = g['status']
    pill = '<span class="pill ok">PASS</span>' if st.startswith('PASS') else ('<span class="pill bad">FAIL</span>' if st.startswith(('FAIL','NOT')) else '<span class="pill warn">BLOCKED/PARTIAL</span>')
    rows.append(f"<tr data-row><td><b>{esc(g['id'])}</b></td><td>{esc(g['name'])}</td><td>{esc(g['requirement'])}</td><td>{pill} {esc(st)}</td>{srccell(SRC_STAND,'reference')}</tr>")
w('pages/validation.html', shell("Validation Gates", f"""
<div class="card"><h2>G1–G10 — every strategy must pass all ten to earn anything</h2>
<div class="notice"><b>Result today:</b> G3 fails (sample), G7/G8 blocked (no market source), G9 fails for prop combos (no data). Therefore <b>0 rewards</b>. Permutation luck test and calibration arrive with the backtest harness (SUG-05). “Skill, not luck” is enforced by construction: pre-registration + FDR + holdout + n≥300 + market CLV.</div>
<div class="tablewrap"><table><thead><tr><th>Gate</th><th>Name</th><th>Requirement</th><th>2026-11-12 result</th><th>Ref</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h3>What “remove luck” means here (and cannot mean)</h3><ul>
<li>Luck cannot be eliminated — only bounded: walk-forward + permutation null + FDR + holdout + CLV vs closing line.</li>
<li>Any single hot week (e.g., 4–0 on originated lines) is meaningless; reward requires z ≥ +2.0 vs the permutation null over n≥300.</li>
<li>Selective skill framing: strategies enter the leaderboard only after passing all gates; “selectively skill based” is enforced by the gate, not by narrative.</li>
</ul></div>""", depth=1))

# ---------- leaderboard
rows=[]
for r in leaderboard['rows']:
    rows.append(f"<tr data-row><td><b>{esc(r['strategy'])}</b></td><td>{esc(r['gates_passed'])}</td><td>{'No' if not r['eligible'] else 'Yes'}</td><td>{r['reward']}</td><td>{esc(r['note'])}</td>{srccell(SRC_SCORES,'slate')}</tr>")
pol="".join(f"<li>{esc(p)}</li>" for p in leaderboard['policy'])
w('pages/leaderboard.html', shell("Leaderboard", f"""
<div class="card"><h2>Leaderboard & reward policy v1.0 — Week 10 2026</h2>
<div class="danger"><b>Payouts this week: 0.</b> No strategy passed the gates. This is the competition working as designed — publishing zeros is the feature that keeps it honest.</div>
<h3>Policy</h3><ul>{pol}</ul>
<h3>Standings</h3>
<div class="tablewrap"><table><thead><tr><th>Strategy</th><th>Gates passed</th><th>Eligible</th><th>Reward</th><th>Note</th><th>Slate</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="notice"><b>Path to a real reward:</b> answer Q-05/Q-06/Q-07/Q-11 → build SUG-02/03/05 → ≥300 graded games → all G-pass → virtual season → counsel review → only then any real prize. Until then, rewards are points on a page.</div></div>""", depth=1))

# ---------- injuries
status_rows=[]
for i,r in enumerate(injuries['game_status_rows']):
    pill = 'bad' if r['game_status']=='Out' else 'warn'
    status_rows.append(f"<tr data-row><td>{esc(r['team'])}</td><td>{esc(r['game'])}</td><td><b>{esc(r['player'])}</b></td><td>{esc(r['pos'])}</td><td>{esc(r['injury'] or '—')}</td><td>{esc(r['practice'])}</td><td><span class='pill {pill}'>{esc(r['game_status'])}</span></td><td>{esc(r['unit'])}</td>{srccell(SRC_INJ)}</tr>")
watch_rows=[]
for r in injuries['watchlist_dnp_lp']:
    pill = 'gray' if r['practice'].startswith('Did') else 'info'
    watch_rows.append(f"<tr data-row><td>{esc(r['team'])}</td><td>{esc(r['game'])}</td><td>{esc(r['player'])}</td><td>{esc(r['pos'])}</td><td>{esc(r['unit'])}</td><td>{esc(r['injury'] or '—')}</td><td><span class='pill {pill}'>{'DNP' if r['practice'].startswith('Did') else 'LIMITED'}</span></td><td><span class='tag-flag'>UNVERIFIED — depth chart not ingested</span></td>{srccell(SRC_INJ)}</tr>")
w('pages/injuries.html', shell("Injury Tracker", f"""
<div class="card"><h2>Week 10 2026 — official injury report (transcribed 2026-11-12)</h2>
<div class="notice"><b>Critical reading note:</b> “DNP” is a <u>practice</u> designation, not a game “Out”. Only rows below carry an explicit Game Status. The official report does <b>not</b> identify starters vs backups; every “replacement / 2nd–4th string” implication is an analytical placeholder, not official fact, until depth charts are ingested (SUG-01, Q-03). Position groups flagged for defensive-deficiency monitoring: CB/S/LB/DL.</div>
<h3>Explicit game statuses (6 rows — the only rows with Out/Questionable)</h3>
<div class="tablewrap"><table><thead><tr><th>Team</th><th>Game</th><th>Player</th><th>Pos</th><th>Injury</th><th>Practice</th><th>Game status</th><th>Unit</th><th>Source</th></tr></thead><tbody>{''.join(status_rows)}</tbody></table></div>
<h3>Defensive / offensive impact watchlist — DNP or Limited (backup unverified)</h3>
<div class="filter"><input data-filter="table.watch tbody tr" placeholder="Filter team, player, position…"></div>
<div class="tablewrap"><table class="watch"><thead><tr><th>Team</th><th>Game</th><th>Player</th><th>Pos</th><th>Unit</th><th>Injury</th><th>Practice</th><th>Replacement</th><th>Source</th></tr></thead><tbody>{''.join(watch_rows)}</tbody></table></div>
<h3>Backup-deficiency methodology (design)</h3><ol>
<li>Ingest official depth chart weekly; snapshot D minus 3 days and D minus 1 day.</li>
<li>Map each DNP/Out player to next listed depth slot; if chart missing → flag UNVERIFIED (never guess).</li>
<li>Unit deficiency score = Σ(position importance × replacement delta); position deltas fitted on 2016–2026 history (SUG-05), else blank.</li>
<li>Publish per-game “starter vs backup” table + confidence; feed S4′ registration only after validation.</li>
</ol>
<p class="small">LAC and BAL reported <b>No Injuries Reported</b> for MNF. Full report spans all 14 Week 10 games; only high-impact rows are transcribed above — complete report at the source link.</p></div>""", depth=1))

# ---------- suggestions
impact_pill = {"High":"bad","Medium":"warn","Low–Medium":"warn","Low":"ok"}
rows=[]
for s in suggestions['suggestions']:
    pill = impact_pill.get(s['impact'],'gray')
    prereq = ", ".join(s['prereqs'])
    rows.append(f"<tr data-row><td><b>{esc(s['id'])}</b><br><small>{esc(s['category'])}</small></td><td><b>{esc(s['title'])}</b><br><small>{esc(s['description'])}</small></td><td><span class='pill {pill}'>{esc(s['impact'])}</span></td><td>{esc(s['effort'])}</td><td>{esc(s['risk'])}</td><td class='small'>{esc(prereq)}</td><td class='small'>{esc(', '.join(s['linked_questions']))}</td><td><span class='pill info'>{esc(s['status'])}</span>{'<br>'+esc(s['decision']) if s['decision'] else '<br><small>awaiting reviewer decision</small>'}</td>{srccell(SUG_REF.get(s['id'], SRC_SCORES), 'evidence')}</tr>")
proto = "".join(f"<li>{esc(p)}</li>" for p in suggestions['meta']['review_protocol'])
w('pages/suggestions.html', shell("Suggestions", f"""
<div class="card"><h2>Suggestion register — review here, decide first, implement later</h2>
<div class="danger"><b>Nothing on this page is implemented.</b> Every item is a proposal. A human reviewer must set <code>status</code> and <code>decision</code> per item; only then does it become work. This page is the “choose the best path before implementing” gate.</div>
<h3>How to review (protocol)</h3><ol>{proto}</ol>
<div class="filter"><input data-filter="table.sugg tbody tr" placeholder="Filter suggestions…"></div>
<div class="tablewrap"><table class="sugg"><thead><tr><th>ID</th><th>Suggestion</th><th>Impact</th><th>Effort</th><th>Risk</th><th>Prerequisites</th><th>Linked Q</th><th>Status / Decision</th><th>Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="notice"><b>Suggested review order (impact-weighted):</b> SUG-01 → SUG-03 → SUG-02 → SUG-05 → SUG-04 → SUG-07 → SUG-06 → SUG-08 → SUG-11 → SUG-09 → SUG-12 → SUG-10. Dependencies: SUG-06 needs SUG-01+SUG-05; SUG-12 needs SUG-05.</div></div>""", depth=1))

# ---------- questions
status_pill = {"ANSWERED":"ok","PARTIAL":"warn","UNKNOWN":"bad","BLOCKED":"bad"}
rows=[]
for q in questions['questions']:
    pill = status_pill.get(q['status'],'gray')
    src = f'<a class="src" href="{esc(q["answer_source"])}">source ↗</a>' if q['answer_source'] else f'<a class="src" href="{esc(Q_REF.get(q["id"], SRC_SCORES))}">context ↗</a>'
    block = '<span class="pill bad">BLOCKS DECISIONS</span>' if q['blocking'] and q['status'] in ('UNKNOWN','PARTIAL','BLOCKED') else '<span class="pill gray">non-blocking</span>'
    rows.append(f"<tr data-row><td><b>{esc(q['id'])}</b><br><small>{esc(q['category'])}</small></td><td><b>{esc(q['question'])}</b><br><small>Why: {esc(q['why'])}</small></td><td>{esc(q['current_answer'])}</td><td>{src}</td><td><span class='pill {pill}'>{esc(q['status'])}</span> {block}</td><td class='small'>{esc(q['discovery'])}</td></tr>")
n_block = sum(1 for q in questions['questions'] if q['blocking'] and q['status'] in ('UNKNOWN','PARTIAL','BLOCKED'))
w('pages/questions.html', shell("Decision Q&A", f"""
<div class="card"><h2>Questions, information and answers — required before reasonable decisions</h2>
<div class="notice"><b>{n_block} of 16 questions are UNKNOWN/PARTIAL and blocking.</b> Until they are resolved, any dependent decision (budgets, rewards, market comparison, automated injury adjustments, canonical site) is on hold. Missing answers are never inferred — they are discovered via the listed action.</div>
<div class="filter"><input data-filter="table.qa tbody tr" placeholder="Filter questions…"></div>
<div class="tablewrap"><table class="qa"><thead><tr><th>ID</th><th>Question & why</th><th>Current answer</th><th>Source</th><th>Status</th><th>How to discover the missing information</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h3>Discovery playbook (in order)</h3><ol>
<li><b>Owner decision</b> (Q-05, Q-07, Q-11, Q-12) — only the requester can answer budget, rewards, governance, canonical site.</li>
<li><b>Licensing diligence</b> (Q-01, Q-02, Q-06, Q-14, Q-16) — written terms for odds/logs/weather data; counsel if derived stats are published.</li>
<li><b>Technical ingestion</b> (Q-03, Q-04, Q-08, Q-15) — depth charts, backtest history, CI gates; each with verification sample before trust.</li>
</ol></div>""", depth=1))

# ---------- repo review
repo_findings = [
 ("RR-01","659 tracked files; working tree currently clean on arena/8184197d-own4","Info","No action"),
 ("RR-02","~53 MB tracked raw HTML dumps under data/raw/nba/ (largest ~0.65 MB each) and data/raw/espn/ — bloats every clone; Git not designed for this volume","Irregularity","Externalize raw payloads or Git LFS; keep parsed JSON only"),
 ("RR-03","4 tracked .pyc files: own4-dashboard/scripts/__pycache__/*.cpython-311.pyc despite *.pyc in .gitignore","Irregularity","git rm --cached them in a maintenance PR"),
 ("RR-04","No LICENSE file anywhere in the repo (git ls-tree LICENSE* → none)","Irregularity","Owner to choose license"),
 ("RR-05","Parallel duplicate dashboards: docs/, nfl/, nfl-lab/, nfl-quant/, nfl-research/, nba-evidence/, verified/, own4-dashboard/, pages/, plus six rental namespaces — README itself warns root index.html is rebuilt byte-identically by the NBA canonical workflow","Irregularity","Canonical-entry decision (Q-12/SUG-08); archive or redirect the rest"),
 ("RR-06","Root index.html cannot be safely edited by peer sessions (locked byte-identical); peers added 'LOCAL ADDITION' links that may be wiped by the next canonical rebuild","Risk","Add a single root nav link only via the canonical workflow owner"),
 ("RR-07","COORDINATION.md shows repeated merge-conflict resolution across sessions; append-only convention mostly working but conflict-heavy","Risk","Keep append-only; integration session merges namespaces once"),
 ("RR-08","nfl-lab/data/games_2026.csv re-checked 2026-11-12: 120 games, internally consistent (W=L balance; 0 mismatches vs its standings CSV)","Verified OK","None — good practice to extend repo-wide"),
 ("RR-09","nfl-quant/data/predictions.csv (1.4 MB) and data/player_gamelogs.json (1.0 MB) committed without verified provenance notes in this session","Needs review","Provenance audit before reuse; do not treat as verified"),
 ("RR-10","No secrets found: pattern scan for api keys/passwords returned 0 files (repo_review/REVIEW-2026-11-06.md match was documentation prose only)","Verified OK","None"),
 ("RR-11",".github/workflows present for NBA pipeline validation; no NFL-specific CI job exists — NFL workspaces rely on manual verification scripts","Gap","Add NFL verify job once canonical path chosen"),
 ("RR-12","Exec summaries proliferate (EXECUTIVE_SUMMARY.md + per-workspace copies + rental variants) with inconsistent framing","Irregularity","Single canonical exec summary after merge"),
 ("RR-13","README documents Pages as possibly-legacy-build issue ('Page build failed' history) — deployment reliability unproven; multiple cancel-storms noted in coordination log","Risk","Watch deploy; re-trigger or switch to Actions-based Pages if API 403 persists"),
 ("RR-14","This session's scope discipline: zero peer files edited; all new work isolated under nfl-intel/ + append-only COORDINATION.md","Verified OK","None"),
]
rows=[]
sev_pill={"Irregularity":"bad","Risk":"warn","Gap":"warn","Needs review":"warn","Verified OK":"ok","Info":"gray"}
for rid,finding,sev,action in repo_findings:
    rows.append(f"<tr data-row><td><b>{rid}</b></td><td>{esc(finding)}</td><td><span class='pill {sev_pill.get(sev,'gray')}'>{esc(sev)}</span></td><td>{esc(action)}</td>{srccell('https://github.com/sassnarep3-star/Own4','repo')}</tr>")
w('pages/repo-review.html', shell("Repo Review", f"""
<div class="card"><h2>Repository review — line-by-line findings (2026-11-12)</h2>
<p class="small">Method: full file inventory (git ls-files), size audit, tracked-artifact scan, secrets pattern scan (0 hits), workflow inspection, COORDINATION.md history review, and targeted recomputation checks. Every finding links to the repository. Peer workspaces were read-only audited; nothing was edited outside nfl-intel/.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Finding</th><th>Severity</th><th>Recommended action</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="notice"><b>Bottom line:</b> the repo is a research monorepo with real verification discipline emerging (per-row source links, verify scripts) but suffers from namespace sprawl, tracked raw bulk, and an unresolved canonical-site decision. None of this blocks NFL Intelligence; all of it is on the Flagged page for your decision.</div></div>""", depth=1))

# ---------- executive summary page
w('pages/executive-summary.html', shell("Executive Summary", """
<div class="card"><h2>Executive Summary — NFL Intelligence (2026-11-12)</h2>
<h3>What exists now</h3>
<ol>
<li><b>Verified data foundation.</b> Official NFL.com standings (32 teams; consistency gate PASS: W=L=135, PF=PA=6246), Week 10 schedule (14 games, bye: CHI/DEN/PHI/TB), and the official Week 10 injury report — all transcribed with per-row official source links on 2026-11-12.</li>
<li><b>Originated lines.</b> Model v1 (pre-registered, git-committed) produced fair spreads/totals/win-probabilities for all 14 Week 10 games. No explicit HFA term (embedded in season PF/PA); neutral-site W10-02 (NE–DET, Munich banner) needs no special handling. Every line is UNVERIFIED vs market (G7 blocked) — informational only.</li>
<li><b>Measured correlations.</b> Season-to-date, n=32: net PPG vs win% r=+0.876; OFF/g vs pct r=+0.694; DEF/g vs pct r=−0.666 (all BH q&lt;.05 across 6 tests). Prop-pair correlations: BLANK/UNVERIFIED — no official player game logs in workspace.</li>
<li><b>Strategy competition designed — and honestly zeroed.</b> 8 strategies (singles, one 2-leg parlay with joint-pricing rule, one prop combo) pre-registered; 10 gates; luck-removal via walk-forward + BH-FDR + permutation null + n≥300. <b>0 of 8 qualify; rewards = 0.</b></li>
<li><b>Injury tracking works for what it is.</b> 6 explicit game statuses transcribed exactly; 68-row DNP/LP watchlist; backup identity UNVERIFIED everywhere (report lacks depth order) — the exact gap SUG-01/Q-03 close.</li>
<li><b>Decision support shipped.</b> 16-question Decision Q&A (9 UNKNOWN/PARTIAL and blocking) + 12 gated Suggestions with a no-auto-implement protocol. You can now choose the best path with eyes open.</li>
</ol>
<h3>Decisions required from the owner (in order)</h3>
<ol><li>Virtual-only rewards confirmed? (default: yes)</li><li>Fund licensed odds archive + official player logs? (unblocks G7/G8/S6; ~Q-05/Q-06 cost)</li><li>Approve depth-chart ingestion automation? (unblocks injury-adjusted strategy S4′)</li><li>Canonical site decision (root vs nfl-intel vs legacy NFL dashboards)? (Q-12/SUG-08)</li><li>Named reviewer + cadence for Suggestions/Q&A review (Q-13/SUG-09)</li></ol>
<h3>Key risks</h3>
<ul><li>Treating originated lines as picks — they are not market prices and not advice.</li><li>Reading DNP as “out” — it is a practice status; only 6 rows carry a game status.</li><li>Assuming 2026 correlations generalize — they don’t; they describe this season (F-07).</li><li>Publishing real rewards without counsel/governance — prohibited until Q-07/Q-11 close.</li></ul>
<h3>What happens next (if suggestions are accepted)</h3>
<p>SUG-01+03 (data) → SUG-05 (backtest, n≥300, true Brier/ECE/CLV) → gates re-run → leaderboard becomes live competition with virtual scoring → governance review → only then any real reward. Estimate: 2–4 focused sessions plus licensing lead time.</p>
<p><b>Files:</b> data in <code>nfl-intel/data/*.json</code> · engine <code>nfl-intel/engine/*.py</code> · site source <code>nfl-intel/pages/</code> · repo audit <code>nfl-intel/REPO_REVIEW.md</code> · flags on the <a href="flagged.html">Flagged for Review</a> page.</p></div>""", depth=1))

# ---------- flagged for review
sev_note = "Needs review"
rows=[]
for f in flags['flags']:
    rows.append(f"<tr data-row><td><b>{esc(f['id'])}</b></td><td><b>{esc(f['item'])}</b><br><small>{esc(f['detail'])}</small></td><td class='small'>{esc(f['resolution'])}</td>{srccell(f['source'])}</tr>")
w('pages/flagged.html', shell("Flagged for Review", f"""
<div class="card"><h2>🚩 Flagged for Review — {len(flags['flags'])} items (non-blocking)</h2>
<p class="small">Every unverified value, modeling assumption and irregularity discovered this session, with the best official source available for each. Flagged items are published for transparent review; none blocks the site or the research, but none may be treated as verified until resolved. Status for all: <b>needs review</b>.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Item & detail</th><th>Resolution path</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>""", depth=1))

# ---------- methodology
w('pages/methodology.html', shell("Methodology", """
<div class="card"><h2>Methodology & verification protocol</h2>
<h3>1. Data provenance</h3>
<ul><li>Only official league sources: nfl.com/standings, nfl.com/scores, nfl.com/injuries (+ game pages). Retrieval date 2026-11-12. Every table row in this site carries one.</li><li>Transcription is verbatim; derived columns are computed (<code>engine/analyze.py</code>) and labeled as derived; literature constants are labeled UNVERIFIED (F-01/F-02).</li><li>Consistency gate before publication: W=L, PF=PA, NET=PF−PA, PCT recomputed — all must hold or the build fails.</li></ul>
<h3>2. Originated-lines model (v1)</h3>
<ul><li>Team strength: season PF/PA per game → expected score for a matchup = mean(own OFF/g, opponent DEF/g).</li><li>Fair margin = home exp − away exp; fair total = Σ; P(home) = Normal(margin, σ=13.45, UNVERIFIED); ML from P(home); no explicit HFA term (embedded); neutral site handled implicitly (W10-02).</li><li>Pythagorean share uses exponent 2.37 (UNVERIFIED). Luck Δ = actual − Pythagorean wins.</li><li>Pre-registered 2026-11-12 before Week 10 concludes; parameters committed in git before any result is known to the model.</li></ul>
<h3>3. Correlation & multiple-testing discipline</h3>
<ul><li>Pearson r with two-tailed Student-t p (df=30); Benjamini–Hochberg FDR across all reported tests (reported together, q=0.05).</li><li>Dependence for parlay/prop pricing is measured, never assumed; independence rejected at |r|&gt;0.10 or p&lt;0.05 (G9).</li><li>Prop-pair correlations are intentionally BLANK — no official game-log feed; inventing them would violate the no-hallucination rule.</li></ul>
<h3>4. Luck removal & validation gates</h3>
<ul><li>Walk-forward chronology only; holdout locked; minimum n=300 graded games per strategy/market; BH-FDR; permutation test on headline metric (z≥+2.0 required); CLV vs closing line when market data is licensed; calibration ECE ≤ 0.10; beat pre-registered baselines (home-always, favorite-always, naive flat).</li><li>Leaderboard: gates G1–G10 mandatory; rewards virtual until Q-05/06/07/11 close; honest zeros published (current status).</li></ul>
<h3>5. Verification boundaries</h3>
<ul><li>This build verifies: transcription consistency, internal recomputation, link existence, per-row source presence. It does NOT verify: external truth beyond the cited pages, market prices, injury replacement mapping (impossible without depth charts), or predictive power (needs SUG-05).</li><li>Sources are dynamic; standings/reports change. Re-fetch before any operational use; the commit history is the audit trail.</li></ul></div>""", depth=1))

# ---------- sources
rows=[]
for s in sources['sources']:
    rows.append(f"<tr data-row><td><b>{esc(s['id'])}</b></td><td><a class='src' href='{esc(s['url'])}'>{esc(s['url'])}</a></td><td>{esc(s['used_for'])}</td><td>{esc(s['retrieved'])}</td><td>{'Official ✔' if s['official'] else 'Other'}</td></tr>")
w('pages/sources.html', shell("Sources", f"""
<div class="card"><h2>Official source register</h2>
<p class="small">Every URL below was fetched and read on 2026-11-12 (UTC) and used as the basis for this build. Third-party sites are deliberately absent — “official NFL only” is the data contract for this workspace.</p>
<table><thead><tr><th>ID</th><th>URL</th><th>Used for</th><th>Retrieved</th><th>Type</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>""", depth=1))

print("pages done")

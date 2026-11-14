#!/usr/bin/env python3
"""nfl-core site builder — deterministic CSV -> static HTML.

Every generated table row carries a source link. Values that cannot be
confirmed from a source are left blank and carry a flag (never-infer policy).
"""
import csv
import html
import os

CORE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(CORE, "data")
PAGES = os.path.join(CORE, "pages")

CSS = """
:root{--bg:#0f1420;--card:#171e2e;--ink:#e8ecf4;--dim:#98a2b8;--line:#26304a;--acc:#4da3ff;--ok:#37c978;--warn:#ffb84d;--bad:#ff6b6b;--pill:#222c44}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{background:var(--card);border-bottom:1px solid var(--line);padding:18px 28px;position:sticky;top:0;z-index:20}
header h1{margin:0;font-size:20px}header h1 a{color:var(--ink);text-decoration:none}
nav{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}
nav a{color:var(--dim);text-decoration:none;font-size:13px;padding:5px 11px;border:1px solid var(--line);border-radius:999px}
nav a:hover{color:var(--ink);border-color:var(--acc)}
nav a.on{background:var(--acc);color:#08111f;border-color:var(--acc);font-weight:600}
main{max-width:1280px;margin:0 auto;padding:26px 22px 80px}
h2{font-size:24px;margin:30px 0 6px}h3{font-size:17px;margin:24px 0 6px}
p.lede{color:var(--dim);margin:4px 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card .k{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
.card .v{font-size:26px;font-weight:700;margin:4px 0}
.card .s{font-size:12px;color:var(--dim)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:13px}
th{background:#1c2438;text-align:left;padding:9px 10px;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#b9c4da;position:sticky;top:0}
td{padding:8px 10px;border-top:1px solid var(--line);vertical-align:top}
tr:nth-child(even){background:#141b2b}
td.n{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.wrap{overflow-x:auto;border-radius:12px;margin:14px 0}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:600;background:var(--pill);color:var(--ink)}
.badge.ok{background:rgba(55,201,120,.16);color:var(--ok)}
.badge.warn{background:rgba(255,184,77,.15);color:var(--warn)}
.badge.bad{background:rgba(255,107,107,.15);color:var(--bad)}
.badge.info{background:rgba(77,163,255,.15);color:var(--acc)}
a{color:var(--acc)}
.src{font-size:11.5px;white-space:nowrap}
.filter{margin:12px 0;display:flex;gap:10px;align-items:center}
.filter input{flex:1;max-width:420px;background:#111827;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:8px 12px;font-size:13px}
.filter .cnt{color:var(--dim);font-size:12px}
.note{background:var(--card);border-left:3px solid var(--acc);padding:12px 16px;border-radius:0 10px 10px 0;margin:16px 0;color:var(--dim);font-size:13.5px}
.note.warn{border-color:var(--warn)}
.note strong{color:var(--ink)}
footer{color:var(--dim);font-size:12px;padding:26px 22px;border-top:1px solid var(--line);margin-top:40px}
.toc{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.toc a{background:var(--card);border:1px solid var(--line);padding:10px 14px;border-radius:10px;text-decoration:none;color:var(--ink);font-size:13px;min-width:210px}
.toc a small{display:block;color:var(--dim);font-size:11px}
"""

JS = """
function wireFilter(inputId, tableId){
  var q=document.getElementById(inputId), t=document.getElementById(tableId), c=document.getElementById(inputId+'-cnt');
  if(!q||!t) return;
  q.addEventListener('input',function(){
    var s=q.value.toLowerCase(), rows=t.tBodies[0].rows, shown=0;
    for (var i=0;i<rows.length;i++){
      var hit=rows[i].innerText.toLowerCase().indexOf(s)>=0;
      rows[i].style.display=hit?'':'none'; if(hit) shown++;
    }
    if(c) c.textContent=shown+' / '+rows.length+' rows';
  });
}
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('input[data-filter-table]').forEach(function(q){
    wireFilter(q.id, q.getAttribute('data-filter-table'));
  });
});
"""

NAV = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/origination.html", "Origination (side→total→ML)"),
    ("pages/prices.html", "Price snapshots"),
    ("pages/results.html", "Results feed"),
    ("pages/leaderboard.html", "Leaderboard (signal vs staking)"),
    ("pages/gates.html", "Validation & demotion gates"),
    ("pages/depth.html", "Injuries & replacement depth"),
    ("pages/correlations.html", "Correlations (with n)"),
    ("pages/questions.html", "Questions & answers"),
    ("pages/suggestions.html", "Suggestions board"),
    ("pages/d1-canonical-choice.html", "D-1 canonical choice"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources & verification"),
]

BUILD_STAMP = "Built 2026-11-14 by session arena-a437d20c-own4 · data rebuilt from nfl-core/build_data.py · site rebuilt from nfl-core/build_site.py"


def esc(x):
    return html.escape(str(x if x is not None else ""))


def link_cell(v):
    v = "" if v is None else str(v)
    if v.startswith("https://"):
        return '<a class="src" href="%s">%s</a>' % (esc(v), esc(v.replace("https://www.", "").replace("https://", "")[:44] + ("…" if len(v) > 52 else "")))
    return esc(v)


def render_table(table_id, rows, cols, numeric=(), link_cols=(), badge_col=None, badge_map=None):
    out = ['<div class="wrap"><table id="%s"><thead><tr>' % table_id]
    for c in cols:
        out.append("<th>%s</th>" % esc(c.replace("_", " ")))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for c in cols:
            v = r.get(c, "")
            cls = ' class="n"' if c in numeric else ""
            if c in link_cols:
                cell = link_cell(v)
            elif badge_col and c == badge_col and badge_map:
                b = badge_map(v)
                cell = '<span class="badge %s">%s</span>' % (b, esc(v)) if v else ""
            else:
                cell = esc(v)
            out.append("<td%s>%s</td>" % (cls, cell))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def filter_box(table_id, idx):
    fid = "f%d" % idx
    return ('<div class="filter"><input id="%s" data-filter-table="%s" placeholder="Filter rows…">'
            '<span class="cnt" id="%s-cnt"></span></div>' % (fid, table_id, fid))


def page(path, title, body, active):
    if path.startswith("pages/"):
        nav = "".join('<a href="%s"%s>%s</a>' % (
            h.replace("pages/", "") if h.startswith("pages/") else "../" + h,
            ' class="on"' if h == active else "", l) for h, l in NAV)
    else:
        nav = "".join('<a href="%s"%s>%s</a>' % (
            h, ' class="on"' if h == active else "", l) for h, l in NAV)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · NFL Core Requirements</title>
<link rel="stylesheet" href="%sassets/style.css"></head>
<body><header><h1><a href="%sindex.html">NFL Core Requirements · nfl-core</a></h1>
<nav>%s</nav></header><main>%s</main>
<footer>%s<br>Every table row carries a source link. Unconfirmable values are blank and flagged — never inferred.</footer>
<script>%s</script></body></html>""" % (
        esc(title), "" if not path.startswith("pages/") else "../",
        "" if not path.startswith("pages/") else "../", nav, body, esc(BUILD_STAMP), JS)


def read_csv(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def write(path, content):
    full = os.path.join(CORE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)


def status_badge(v):
    v = (v or "").upper()
    if any(k in v for k in ("FAIL", "CRITICAL", "OUT", "UNVERIFIED", "BLOCKED", "DEAD")):
        return "bad"
    if any(k in v for k in ("PARTIAL", "QUESTIONABLE", "DOUBTFUL", "PENDING", "ARMED", "PROPOSED", "SCHEDULED", "NEEDS")):
        return "warn"
    if any(k in v for k in ("PASS", "OK", "FINAL", "VERIFIED", "DONE", "RESOLVED", "CHOSEN")):
        return "ok"
    return "info"


results = read_csv("results_feed_2026.csv")
snaps = read_csv("price_snapshots_2026.csv")
origs = read_csv("originations_2026.csv")
signal = read_csv("leaderboard_signal.csv")
staking = read_csv("leaderboard_staking.csv")
gates = read_csv("gates.csv")
depth = read_csv("depth_week10.csv")
corrs = read_csv("correlations_n.csv")
questions = read_csv("questions.csv")
suggestions = read_csv("suggestions.csv")
flagged = read_csv("flagged.csv")

n_final = sum(1 for r in results if r["status"] == "FINAL")
n_sched = sum(1 for r in results if r["status"] == "SCHEDULED")
n_markets = len(snaps)

# ------------------------------------------------------------------ dashboard
dash = []
dash.append('<h2>NFL core requirements — live dashboard</h2>')
dash.append('<p class="lede">One workspace implementing the eight core requirements end-to-end: a price-snapshot store '
            '(opening + closing per market), a verified results feed (backtests and ROI computable), side→total→moneyline '
            'origination with model/market/difference columns, a leaderboard that separates signal from staking, '
            'replacement-depth tracking, correlations published with n, and a demotion gate. '
            'Nothing on these pages is inferred: every value comes from a linked source, everything else is blank and flagged.</p>')
dash.append('<div class="grid">')
for k, v, s in [
    ("2026 REG games tracked", str(len(results)), "%d final · %d scheduled (feed verified vs official standings)" % (n_final, n_sched)),
    ("Markets in price store", str(n_markets), "3 per game: SIDE, TOTAL, MONEYLINE — open + close + settlement"),
    ("Originated markets", str(len(origs)), "weeks 10–18 · ordered SIDE → TOTAL → MONEYLINE"),
    ("Strategies on leaderboard", str(len(signal)), "signal rank independent of staking; 0 reward-eligible"),
    ("Correlation values with n", str(sum(1 for c in corrs if c["n"])), "player-level rows blank + flagged (no verified inputs)"),
    ("Demotion gates armed", str(sum(1 for g in gates if g["gate_id"].startswith("DG"))), "live → paper triggers; see gates page"),
]:
    dash.append('<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>' % (esc(k), esc(v), esc(s)))
dash.append("</div>")
dash.append('<div class="note"><strong>Reading the numbers.</strong> Spread columns use the nflverse documented convention: '
            'a positive spread is the number of points the <em>home</em> team is favored by '
            '(source: <a href="https://github.com/nflverse/nfldata/blob/master/DATASETS.md">DATASETS.md</a>, read 2026-11-14). '
            'Market prices are third-party (the NFL publishes no odds) and are labeled as such; scores and standings are official.</div>')
dash.append("<h3>Requirements coverage</h3>")
cover = [
    ("Price-snapshot store", "prices.html", "OPEN + CLOSE + settlement per market, capture timestamps, provenance"),
    ("Verified results feed", "results.html", "272 games, per-game official URL, reconciled to official standings"),
    ("Origination order + fair/market/diff", "origination.html", "seq 1 SIDE, 2 TOTAL, 3 MONEYLINE; three separate columns"),
    ("Signal vs staking", "leaderboard.html", "two tables; ranking cannot be influenced by stake sizing"),
    ("Replacement depth", "depth.html", "who replaces the absent player and which string they are"),
    ("Correlations with n", "correlations.html", "every r carries its n; official-derived inputs labeled"),
    ("Demotion gate", "gates.html", "DG-1..DG-4: live strategies go back to paper on defined triggers"),
    ("Questions / suggestions", "questions.html", "decision register: known / missing / what settles it"),
]
dash.append('<div class="toc">')
for label, href, sub in cover:
    dash.append('<a href="pages/%s">%s<small>%s</small></a>' % (href, esc(label), esc(sub)))
dash.append("</div>")
write("index.html", page("index.html", "Dashboard", "".join(dash), "index.html"))

# ------------------------------------------------------------ executive summary
body = []
body.append('<h2>Executive summary</h2><p class="lede">The state of the NFL origination system as of 2026-11-14, '
            'every claim source-linked. Companion markdown: <a href="../EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a>.</p>')
body.append("""<div class="note"><strong>Bottom line.</strong> The system now records, for every market it originates, an opening and a
closing number with provenance and settlement, and a verified results feed that makes backtests and ROI computable at all.
On the evidence available today, <strong>no strategy has yet cleared the luck barrier</strong> (best BH-adjusted p = 0.44),
so the leaderboard currently ranks <em>skill signals</em> honestly and holds all rewards. One real signal worth continued
paper tracking: unders in outdoor games with wind ≥ 15 mph (n=303, hit 55.4%, z=1.43) — not yet distinguishable from luck.
Week 10 injury-driven deficiencies are concrete: Minnesota is down to backup quarterback (Kyler Murray Out, official report),
Green Bay is without Josh Jacobs, Micah Parsons and center Sean Rhyan; Detroit is without center Cade Mays and corner D.J. Reed —
each replacement's depth string is tracked on the depth page.</div>""")
body.append("<h3>What is solid (verified)</h3><ul>"
            "<li>Results feed: 137 settled 2026 REG games, each row carrying its official nfl.com game URL; per-team W-L-T/PF/PA "
            "reconciled cell-by-cell against the official standings read 2026-11-14 (32/32 teams, ΣW=ΣL=136, ΣT=2).</li>"
            "<li>Price-snapshot store: 816 market rows with OPEN/CLOSE columns; WAS@NYG shows the mechanism working "
            "(open NYG −2.5 → close NYG −1.5, settlement documented; resolves the older A-06 “1.5 vs 2.5” flag as open-vs-close movement).</li>"
            "<li>Convention settled: spread_line positive = home favored (nflverse DATASETS.md, verified against 162/163 ML pairs).</li>"
            "</ul>")
body.append("<h3>What is deliberately blank (never inferred)</h3><ul>"
            "<li>Opening lines for 2026 weeks 1–9: no capture exists anywhere in the repo (F-C02) — cells blank + flagged.</li>"
            "<li>Player-prop prices: the NFL publishes none (A-13) — prop correlation rows blank + flagged.</li>"
            "<li>Replacement depth strings where the club's own chart does not answer (e.g., DET S behind Kerby Joseph) — blank + flagged.</li>"
            "</ul>")
body.append("<h3>Decisions needed from the owner</h3><ul>"
            "<li>Choose the demotion-gate thresholds (S-C04) — currently project-defined and armed.</li>"
            "<li>Choose among the suggestions board paths before anything is implemented (suggestions.html).</li>"
            "<li>Decide whether to license a closing-line feed (D2) to fill the opening/closing gap.</li></ul>")
write("pages/executive-summary.html", page("pages/executive-summary.html", "Executive summary", "".join(body), "pages/executive-summary.html"))

# ------------------------------------------------------------- origination page
body = []
body.append('<h2>Origination — side first, then the total, then the moneyline</h2>')
body.append('<p class="lede">Every market the model originates, in fixed pipeline order: seq 1 SIDE, seq 2 TOTAL, seq 3 MONEYLINE. '
            'For each market the model’s fair line, the market line and the difference are published as separate columns. '
            'difference = model_fair − market (moneyline rows use win-probability points). Model output is this repo’s walk-forward '
            'model; market lines are third-party captures dated %s.</p>' % esc("2026-11-13"))
body.append(filter_box("t-orig", 1))
body.append(render_table("t-orig", origs,
    ["origination_seq", "market_type", "week", "gameday", "matchup", "model_fair_line", "market_line", "difference",
     "direction_note", "match_url", "market_source", "verification", "flag"],
    numeric=("origination_seq",),
    link_cols=("match_url", "market_source")))
write("pages/origination.html", page("pages/origination.html", "Origination", "".join(body), "pages/origination.html"))

# ------------------------------------------------------------ price snapshots
body = []
body.append('<h2>Price-snapshot store — opening and closing numbers</h2>')
body.append('<p class="lede">One row per market (SIDE / TOTAL / MONEYLINE) for every 2026 REG game we originate or reference, '
            'with the opening number, the closing number, their capture times, and settlement. '
            'Where no verified opening capture exists (weeks 1–9, 2026) the open cells are blank and flagged — never filled in. '
            'Market prices are third-party by nature (the NFL publishes no odds); settlements are verified against official scores.</p>')
body.append('<div class="note"><strong>Example (the store doing its job):</strong> WAS @ NYG, week 10 — SIDE open 2.5 (pre-game capture) '
            '→ close 1.5 (settled archive). The older A-06 flag treated 1.5 vs 2.5 as a discrepancy; the store shows it as '
            'open-vs-close line movement with both sources recorded.</div>')
body.append("<h3>Originated slate (weeks 10–18)</h3>")
body.append(filter_box("t-snap1", 2))
snaps_o = [r for r in snaps if int(r["week"]) >= 10]
body.append(render_table("t-snap1", snaps_o,
    ["market_id", "origination_seq", "market_type", "open_price", "open_captured_utc", "close_price", "close_captured_utc",
     "settlement", "open_source", "close_source", "settlement_source", "game_url", "verification", "flag"],
    numeric=("origination_seq",),
    link_cols=("open_source", "close_source", "settlement_source", "game_url")))
body.append("<h3>Settled 2026 markets (weeks 1–10) — closes for settlement and backtests</h3>")
body.append(filter_box("t-snap2", 3))
snaps_s = [r for r in snaps if int(r["week"]) < 10]
body.append(render_table("t-snap2", snaps_s,
    ["market_id", "market_type", "close_price", "settlement", "close_source", "settlement_source", "game_url", "verification", "flag"],
    link_cols=("close_source", "settlement_source", "game_url")))
write("pages/prices.html", page("pages/prices.html", "Price snapshots", "".join(body), "pages/prices.html"))

# ---------------------------------------------------------------- results page
body = []
body.append('<h2>Verified results feed</h2>')
body.append('<p class="lede">Every 2026 regular-season game with its final score (or scheduled time), closing market numbers, '
            'and settlement of SIDE / TOTAL / MONEYLINE — the join that makes backtests and ROI computable at all. '
            'Every row carries its official nfl.com game URL. Scores reconcile to the official standings '
            '(<a href="https://www.nfl.com/standings/league/2026/REG">nfl.com standings</a>, read 2026-11-14): '
            'the verification script recomputes W-L-T and PF-PA for all 32 teams from this feed and compares cell-by-cell.</p>')
body.append('<div class="note warn"><strong>Settlement block:</strong> 13 rows settle totals and moneylines only — '
            'their closing spread cells are blank in the archive, so the spread settlement is marked SETTLE-BLOCKED rather than guessed.</div>')
body.append(filter_box("t-res", 4))
body.append(render_table("t-res", results,
    ["week", "gameday", "away_team", "away_score", "home_team", "home_score", "status",
     "close_spread_home_fav_by", "close_total", "close_away_ml", "close_home_ml",
     "spread_settlement", "total_settlement", "ml_settlement", "game_url", "verification", "flag"],
    numeric=("week", "away_score", "home_score", "close_spread_home_fav_by", "close_total", "close_away_ml", "close_home_ml"),
    link_cols=("game_url",),
    badge_col="status", badge_map=status_badge))
write("pages/results.html", page("pages/results.html", "Results feed", "".join(body), "pages/results.html"))

# -------------------------------------------------------------- leaderboard
body = []
body.append('<h2>Leaderboard — signal separated from staking</h2>')
body.append('<p class="lede">A lucky staking run cannot mask a bad signal: ranking uses <strong>signal metrics only</strong> '
            '(hit-rate z against break-even at flat prices). Stake-level outcomes (ROI, drawdown) are published in a separate '
            'table that never affects ranks. All prices are third-party; settlements come from the verified results feed.</p>')
body.append("<h3>Signal table (this determines rank)</h3>")
body.append(filter_box("t-sig", 5))
body.append(render_table("t-sig", signal,
    ["signal_rank", "strategy_id", "family", "name", "n_settled", "wins", "hit_rate", "break_even_rate",
     "z_vs_breakeven", "p_value", "p_value_bh", "wilson95", "signal_verdict", "source_url", "verification", "flag"],
    numeric=("signal_rank", "n_settled", "wins", "hit_rate", "break_even_rate", "z_vs_breakeven", "p_value", "p_value_bh"),
    link_cols=("source_url",)))
body.append("<h3>Staking table (cannot influence rank)</h3>")
body.append(filter_box("t-stk", 6))
body.append(render_table("t-stk", staking,
    ["strategy_id", "family", "name", "flat_stake_roi_all", "pnl_units_flat", "staked_units_flat",
     "confirmation_n", "confirmation_roi_flat", "max_drawdown_units", "reward_eligible",
     "staked_at_current_plan", "source_url", "verification", "flag"],
    numeric=("flat_stake_roi_all", "pnl_units_flat", "staked_units_flat", "confirmation_n", "confirmation_roi_flat", "max_drawdown_units"),
    link_cols=("source_url",),
    badge_col="reward_eligible", badge_map=status_badge))
body.append('<div class="note"><strong>Demotion gate.</strong> Any LIVE strategy returns to PAPER when a trigger in '
            '<a href="gates.html">DG-1..DG-4</a> fires. No strategy is live today (none has passed G4), so the gates are armed, not firing.</div>')
write("pages/leaderboard.html", page("pages/leaderboard.html", "Leaderboard", "".join(body), "pages/leaderboard.html"))

# -------------------------------------------------------------------- gates
body = []
body.append('<h2>Validation gates and the demotion gate</h2>')
body.append('<p class="lede">A strategy must pass the validation gates G1–G8 before it can be promoted or rewarded. '
            'The demotion gates DG-1..DG-4 send a live strategy back to paper when their trigger fires. '
            'Thresholds not fixed by an external standard are marked project-defined and appear on the '
            '<a href="suggestions.html">suggestions board</a> for owner choice.</p>')
body.append(render_table("t-gates", gates,
    ["gate_id", "name", "rule", "threshold_origin", "current_status", "note", "source_url"],
    link_cols=("source_url",),
    badge_col="current_status", badge_map=status_badge))
write("pages/gates.html", page("pages/gates.html", "Gates", "".join(body), "pages/gates.html"))

# -------------------------------------------------------------------- depth
body = []
body.append('<h2>Injuries & replacement depth</h2>')
body.append('<p class="lede">Not just the fact of a replacement — the <strong>depth of the replacement</strong>: which player steps '
            'in, and which string (2nd, 3rd, 4th) that player is on the club’s own depth chart. Injury statuses come from the '
            'official week-10 report (<a href="https://www.nfl.com/injuries/">nfl.com/injuries</a>, read 2026-11-14); depth strings '
            'come from official club sites where read this session. Where no chart answer exists, cells stay blank and flagged.</p>')
body.append('<div class="note"><strong>Correction to prior flag A-12:</strong> NFL club sites DO publish unofficial depth charts '
            '(compiled by club football communications / site writers) — e.g. '
            '<a href="https://www.detroitlions.com/team/depth-chart">detroitlions.com</a> and '
            '<a href="https://www.patriots.com/team/depth-chart">patriots.com</a>, both read 2026-11-14. The league-level route on '
            'nfl.com remains 404. Charts are labeled “unofficial” by the clubs themselves.</div>')
body.append(filter_box("t-depth", 7))
body.append(render_table("t-depth", depth,
    ["team", "position", "absent_player", "official_game_status", "chart_position", "replacement",
     "replacement_depth_string", "further_depth", "injury_report_url", "depth_chart_url", "verification", "flag"],
    link_cols=("injury_report_url", "depth_chart_url"),
    badge_col="official_game_status", badge_map=status_badge))
body.append('<h3>Why the string matters (week 10 examples)</h3><ul>'
            '<li><strong>MIN QB:</strong> Kyler Murray Out — the Vikings play with their backup. Replacement name/string not '
            'verifiable from a chart read this session → blank, flagged (the official report lists Carson Wentz as a full '
            'participant, but listing him as the starter would be an inference).</li>'
            '<li><strong>NE interior line:</strong> Ben Brown is Out — he is LG-1 <em>and</em> the only listed backup center. '
            'His replacement at LG (Walter Rouse) is 2nd string; if Jared Wilson is also lost, no 3rd-string center is listed.</li>'
            '<li><strong>DET secondary:</strong> D.J. Reed Out → Rock Ya-Sin is the 2nd-string corner on the club chart. '
            'Kerby Joseph Out at safety, but the club chart does not list him among its two S slots → replacement blank + flagged.</li></ul>')
write("pages/depth.html", page("pages/depth.html", "Depth", "".join(body), "pages/depth.html"))

# ------------------------------------------------------------- correlations
body = []
body.append('<h2>Correlations — officially sourced inputs, n published with every value</h2>')
body.append('<p class="lede">Every correlation value on this page carries its n. Values are computed only on officially sourced '
            'numbers (game scores from the official-derived archive, reconciled to nfl.com) — where market prices are part of the '
            'input the row says so. Player-level pairs remain blank: no verified player-level series exists (A-13/Q-09).</p>')
body.append(render_table("t-corr", corrs,
    ["id", "group", "pair", "n", "pearson_r", "ci95", "p_value", "inputs_official", "reading", "source_url", "verification", "flag"],
    numeric=("n", "pearson_r", "p_value"),
    link_cols=("source_url",)))
write("pages/correlations.html", page("pages/correlations.html", "Correlations", "".join(body), "pages/correlations.html"))

# ----------------------------------------------------------------- questions
body = []
body.append('<h2>Questions, information and answers — decision register</h2>')
body.append('<p class="lede">The list of questions that must be answered before any decision can reasonably be made: what we know, '
            'what is missing, and exactly what evidence would settle each one. Questions are also how we discover missing '
            'information — every blank cell in this workspace should trace back to a row here.</p>')
body.append(render_table("t-q", questions,
    ["id", "question", "information_known", "information_missing", "answer_status", "evidence_that_would_settle", "source_url", "status"],
    link_cols=("source_url",),
    badge_col="status", badge_map=status_badge))
write("pages/questions.html", page("pages/questions.html", "Questions", "".join(body), "pages/questions.html"))

# --------------------------------------------------------------- suggestions
body = []
body.append('<h2>Suggestions board — review and choose the path before implementation</h2>')
body.append('<p class="lede">Improvements to the system and site that would sharpen decision-making. Each suggestion lists options '
            'and a recommended path, and <strong>nothing is implemented until the owner chooses</strong> — the review column must move '
            'from “proposed” to “chosen” first. Status column tracks that choice.</p>')
body.append(render_table("t-sug", suggestions,
    ["id", "suggestion", "why_it_helps_decisions", "options", "recommended_path", "review_status", "implementation_state", "source_url"],
    link_cols=("source_url",),
    badge_col="review_status", badge_map=status_badge))
write("pages/suggestions.html", page("pages/suggestions.html", "Suggestions", "".join(body), "pages/suggestions.html"))

# -------------------------------------------------------------------- flagged
body = []
body.append('<h2>Flagged for review</h2>')
body.append('<p class="lede">Irregularities, unverified values and corrections found while building this workspace. '
            'None of these block use of the site; each carries its source links so the owner can review after the site is live '
            'and request changes.</p>')
body.append(render_table("t-flag", flagged,
    ["id", "severity", "what", "evidence", "source_url", "status"],
    link_cols=("source_url",),
    badge_col="status", badge_map=status_badge))
write("pages/flagged.html", page("pages/flagged.html", "Flagged", "".join(body), "pages/flagged.html"))

# -------------------------------------------------------------------- sources
body = []
body.append('<h2>Sources & verification</h2>')
body.append('<p class="lede">Everything this workspace was verified against, with what was checked and when. '
            'Official = published by the NFL or its clubs; third-party = everything else (market prices, model archives).</p>')
import json
reads = json.load(open(os.path.join(DATA, "official_reads_2026-11-14.json")))
srows = []
for r in reads["official_reads"]:
    is_official = ("nfl.com" in r["url"]) or (".com/team/" in r["url"])
    srows.append({"id": r["id"], "publisher": ("NFL.com / official club site" if is_official else "nflverse (third-party dataset docs)"),
                  "url": r["url"], "title": r["title"], "read_utc": r["read_utc"], "what_was_read": r["what"],
                  "tier": "OFFICIAL" if is_official else "THIRD-PARTY"})
body.append(render_table("t-src", srows,
    ["id", "tier", "publisher", "title", "url", "read_utc", "what_was_read"], link_cols=("url",)))
body.append("<h3>Upstream repository datasets (reused, provenance kept)</h3>")
body.append(render_table("t-src2", [
    {"id": "UP-01", "tier": "THIRD-PARTY", "publisher": "nflverse/nfldata (Lee Sharpe)", "title": "games dataset (pinned copy)",
     "url": "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "read_utc": "2026-11-14",
     "what_was_read": "column definitions quoted in official_reads OR-06; pinned copy at nfl-arena/data/raw/games.csv"},
    {"id": "UP-02", "tier": "MODEL-INTERNAL", "publisher": "this repository (nfl-lines)", "title": "walk-forward model output",
     "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/own_lines_week10.json", "read_utc": "2026-11-14",
     "what_was_read": "fair lines + market captures for the weeks 10–18 origination slate"},
    {"id": "UP-03", "tier": "MODEL-INTERNAL", "publisher": "this repository (nfl-lines/nfl-arena)", "title": "strategy settlement metrics",
     "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json", "read_utc": "2026-11-14",
     "what_was_read": "per-strategy n/wins/ROI/drawdown splits used in the leaderboard tables"},
], ["id", "tier", "publisher", "title", "url", "read_utc", "what_was_read"], link_cols=("url",)))
body.append('<div class="note"><strong>Verification method (this session, 2026-11-14).</strong> '
            '(1) Official pages fetched and read directly (list above). '
            '(2) Results feed reconciled cell-by-cell against the official standings for all 32 teams by verify.py. '
            '(3) Game-URL slug pattern verified against live nfl.com pages (commanders-at-giants, giants-at-commanders, packers-at-patriots patterns). '
            '(4) Spread convention verified against 163 settled/in-lined 2026 games (162/163 ML-consistency) and quoted from DATASETS.md. '
            '(5) Every generated table row checked for a source link by verify.py; blanks allowed only with a flag.</div>')
write("pages/sources.html", page("pages/sources.html", "Sources", "".join(body), "pages/sources.html"))

print("site written: %d pages + index" % (len(NAV) - 1))

# ------------------------------------------------------- D-1 canonical choice
body = []
body.append('<h2>D-1 — choose the canonical NFL requirements workspace</h2>')
body.append('<p class="lede">Decision page for the owner. Four namespaces now implement the same core-requirements brief '
            '(a peer session recorded this as decision <strong>D-1</strong> in COORDINATION.md after a third implementation '
            'merged on 2026-11-14). Nothing here is a decision — it is the comparison the decision needs. '
            'All counts below were measured directly from the files on 2026-11-14 (session arena-a437d20c-own4, read-only).</p>')
d1 = [
    {"requirement": "Price-snapshot store (open + close)",
     "nfl-core": "816 market rows: 81 with OPEN + capture date, 489 with CLOSE, 411 settled (WAS@NYG shows open 2.5 -> close 1.5)",
     "nfl-market": "84 store rows (data/derived/store.json, integrity_all_pass=true)",
     "nfl-ledger": "0 rows — their own flag F-L1: no official price source",
     "nfl-price-snapshot": "39 snapshots (data/derived/price_snapshots.json)",
     "evidence": "https://github.com/sassnarep3-star/Own4/tree/main/nfl-core/data"},
    {"requirement": "Verified results feed (ROI computable)",
     "nfl-core": "272 games (137 final) + settlement columns; 32/32 teams exact vs official standings (verify.py V3)",
     "nfl-market": "3 rows published in data/derived/results_feed.json (store covers the week-10 slate)",
     "nfl-ledger": "137 games (W1-W10); standings reconciliation 32/32 (their claim, L3)",
     "nfl-price-snapshot": "week-10 feed: 14 games, 1 completed at capture",
     "evidence": "https://github.com/sassnarep3-star/Own4/tree/main/nfl-ledger/data"},
    {"requirement": "Origination order side -> total -> ML + fair/market/diff columns",
     "nfl-core": "408 rows (136 games x 3), seq 1/2/3 enforced (verify.py V6), difference arithmetic exact",
     "nfl-market": "data/derived/origination.json (week-10 slate)",
     "nfl-ledger": "week 11: 13 games, order documented; market columns blank (their L4)",
     "nfl-price-snapshot": "data/derived/originated_lines.json",
     "evidence": "https://github.com/sassnarep3-star/Own4/tree/main/nfl-core/data"},
    {"requirement": "Signal separated from staking (rank cannot be masked)",
     "nfl-core": "two tables + verify.py V7 enforces z-only sort; staking unplugged from rank",
     "nfl-market": "data/derived/leaderboard.json",
     "nfl-ledger": "data/leaderboard_split.json (rank on signal only)",
     "nfl-price-snapshot": "data/derived/leaderboard.json",
     "evidence": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_signal.csv"},
    {"requirement": "Replacement depth (string of the replacement)",
     "nfl-core": "official club depth charts read live (DET, NE) -> replacement + 2nd/3rd string; other clubs blank + flagged",
     "nfl-market": "data/official/official_lineups.json",
     "nfl-ledger": "depth fields blank — their flag F-L2 (no chart found)",
     "nfl-price-snapshot": "injuries pages",
     "evidence": "https://www.detroitlions.com/team/depth-chart"},
    {"requirement": "Correlations with n, officially sourced inputs",
     "nfl-core": "every r carries n; price-input rows labeled; player-level blank + flagged",
     "nfl-market": "data/derived/correlations.json",
     "nfl-ledger": "data/correlations.json (n = 105 per their record)",
     "nfl-price-snapshot": "data/derived/correlations.json",
     "evidence": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/correlations_n.csv"},
    {"requirement": "Demotion gate (live -> paper)",
     "nfl-core": "DG-1..DG-4 (skill regression, CLV, drawdown, data integrity) + G1-G8 validation gates",
     "nfl-market": "data/derived/demotion.json",
     "nfl-ledger": "D1-D6 demotion + P1-P5 promotion (13 unit tests)",
     "nfl-price-snapshot": "data/derived/gates.json",
     "evidence": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/gates.csv"},
    {"requirement": "Spread-sign convention resolved (old A-06 / Q-05)",
     "nfl-core": "RESOLVED + documented: positive = home favored (DATASETS.md quote + 162/163 ML check); A-06 explained as open->close movement",
     "nfl-market": "data/spread_convention_determination.json (in nfl-command-center peer) / movement.json",
     "nfl-ledger": "not published",
     "nfl-price-snapshot": "not published",
     "evidence": "https://github.com/nflverse/nfldata/blob/master/DATASETS.md"},
]
body.append(render_table("t-d1", d1,
    ["requirement", "nfl-core", "nfl-market", "nfl-ledger", "nfl-price-snapshot", "evidence"],
    link_cols=("evidence",)))
body.append('<h3>Options</h3><ul>'
            '<li><strong>A — one canonical workspace.</strong> Owner picks the strongest implementation from the matrix; '
            'the others stay published as archived evidence (nothing is deleted; each keeps its namespace and PR history).</li>'
            '<li><strong>B — canonical + satellites.</strong> One workspace owns the stores; the others link into it for '
            'their specialized extras (e.g., nfl-ledger’s promotion/demotion unit tests, nfl-command-center’s repo audit).</li>'
            '<li><strong>C — keep all four independent.</strong> No consolidation; reviewers read all four (status quo, '
            'highest review cost).</li></ul>')
body.append('<div class="note"><strong>Recommendation (a suggestion — the owner decides):</strong> Option B, with '
            '<em>nfl-core</em> as the store-of-record: it is the only implementation whose price store actually holds '
            'opening <em>and</em> closing numbers with settlement (81 open / 489 close vs 84, 0 and 39 rows elsewhere), the only '
            'one whose results feed is re-verified against the official standings inside its own verifier, and it publishes the '
            'resolved spread convention that the other workspaces’ flags still list as open. Peer workspaces would remain '
            'published and linked — nothing discarded. If the owner prefers another workspace as canonical, the same matrix '
            'supports that choice.</div>')
body.append('<div class="note warn"><strong>Status: proposed.</strong> This page implements nothing. Until the owner marks '
            'S-C11 “chosen” on the <a href="suggestions.html">suggestions board</a>, all four workspaces remain as published.</div>')
write("pages/d1-canonical-choice.html", page("pages/d1-canonical-choice.html", "D-1 canonical choice", "".join(body), "pages/d1-canonical-choice.html"))

print("site written: %d pages + index" % (len(NAV) - 1))

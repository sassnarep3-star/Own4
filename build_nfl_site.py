#!/usr/bin/env python3
"""Own4 NFL root-site builder — deterministic CSV -> static HTML.

Reads the verified nfl-core/data CSVs (already source-linked, never-infer
policy) and renders the root GitHub Pages site: one clean NFL landing page
with a decision-readiness table, plus category subpages (price snapshots,
results feed, origination, leaderboards split signal/staking, gates, depth,
correlations, questions, suggestions, flagged, sources).

Every generated table row carries a source link. Values that cannot be
confirmed from a source are left blank and flagged — never inferred.
"""
import csv
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "nfl-core", "data")
PAGES = os.path.join(ROOT, "pages")
CSS_PATH = "assets/nfl.css"

CSS = open(os.path.join(ROOT, "assets", "nfl.css")).read()

JS = """
function wireFilter(inputId, tableId){
  var q=document.getElementById(inputId), t=document.getElementById(tableId),
      c=document.getElementById(inputId+'-cnt');
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

# Root-level pages link assets/nfl.css directly; pages/ pages need ../assets/nfl.css
NAV_ROOT = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/prices.html", "Price snapshots"),
    ("pages/results.html", "Results feed"),
    ("pages/origination.html", "Origination (side -> total -> ML)"),
    ("pages/leaderboard.html", "Leaderboard (signal vs staking)"),
    ("pages/gates.html", "Validation & demotion gates"),
    ("pages/depth.html", "Injuries & replacement depth"),
    ("pages/correlations.html", "Correlations (with n)"),
    ("pages/questions.html", "Questions & answers"),
    ("pages/suggestions.html", "Suggestions board"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources & verification"),
]

BUILD_STAMP = "Built 2026-11-16 from verified nfl-core data · never-infer policy: blanks are flagged, never filled"

READY = [
    # id, requirement, gate_blocking, number_to_clear, status, source
    ("R-01", "Price-snapshot store: opening + closing number for every originated market",
     "G3 — prices at settlement time",
     "137 settled 2026 games carry CLOSE + settlement; OPEN missing for weeks 1-9 (F-C02)",
     "PARTIAL", "data/price_snapshots_2026.csv"),
    ("R-02", "Verified results feed so backtests and ROI are computable",
     "G1 — data sufficiency (n >= 300)",
     "137 settled 2026 REG games (walk-forward corpus n = 4,055); 32/32 teams reconcile to official standings",
     "PASS", "data/results_feed_2026.csv"),
    ("R-03", "Originate the side first, then the total, then the moneyline",
     "Pre-registration (rule frozen before results)",
     "408 originated markets, weeks 10-18, fixed seq 1 SIDE / 2 TOTAL / 3 MONEYLINE",
     "PASS", "data/originations_2026.csv"),
    ("R-04", "Publish model fair line, market line, difference as separate columns",
     "Origination order (R-03)",
     "Three separate columns per market: model_fair_line, market_line, difference",
     "PASS", "data/originations_2026.csv"),
    ("R-05", "Separate signal from staking in the leaderboard",
     "G7 — leaderboard ranks on signal only",
     "Signal table ranked by z_vs_breakeven at flat stakes; staking ROI/drawdown in a separate table that cannot alter rank",
     "PASS", "data/leaderboard_signal.csv"),
    ("R-06", "Track the depth of the replacement (which string), not just the fact",
     "Depth-chart coverage (S-C03)",
     "Replacement + depth string tracked where the official club chart answers (DET, NE read); other clubs blank + flagged",
     "PARTIAL", "data/depth_week10.csv"),
    ("R-07", "Compute correlations only from officially sourced numbers; publish n with each value",
     "Official-inputs rule (Q-C09)",
     "Every correlation row publishes n; price-input rows labeled THIRD-PARTY; player-level pairs blank + flagged",
     "PASS", "data/correlations_n.csv"),
    ("R-08", "Define a demotion gate sending a live strategy back to paper",
     "DG-1 .. DG-4 armed",
     "Four triggers: skill regression (z<0 over 200 settled), negative CLV over >=50 picks, drawdown >20 units, data-integrity failure",
     "ARMED", "data/gates.csv"),
    ("R-09", "Pre-register every strategy; forbid backtest numbers on the leaderboard",
     "Pre-registration + G4/G5",
     "Strategy definition frozen before results are seen; leaderboard shows prospective signal only",
     "PASS (documented)", "nfl-lines/data/model_params.json"),
    ("R-10", "Build the availability graph as a first-class dataset",
     "Official club depth charts (one fetch per club)",
     "Two of 32 clubs charted this session (DET, NE); remaining 30 blank + flagged pending S-C03",
     "PARTIAL", "https://www.nfl.com/injuries/"),
    ("R-11", "Model depth from playing time, not jersey order",
     "Depth-slot grouping rule",
     "Depth slots modeled as groups (multiple rank-1 players allowed); jersey-number derivation rejected",
     "PASS (policy)", "pages/depth.html"),
    ("R-12", "Injury signal as a surprise, never a level",
     "Designation reliability scoring",
     "No designation-to-play-rate conversion published yet; injury treated as timestamped series",
     "BLOCKED", "Q-C04"),
    ("R-13", "32-team roster/IR sweep before trusting any team-level model",
     "Roster-turnover versioning",
     "Not yet completed for all 32 clubs; flagged as missing evidence",
     "BLOCKED", "S-C03"),
    ("R-14", "Fixture-context feature set from published schedule facts only",
     "Official schedule facts",
     "Venue transcribed per fixture from game centre; schedule announcement beside live schedule",
     "PARTIAL", "results_feed game_url"),
    ("R-15", "Store every model output as a probability plus its inputs",
     "Model-output registry",
     "Walk-forward model outputs recorded with inputs; per-game probability + inputs not yet published as a standalone table",
     "PARTIAL", "nfl-lines/data/derived/own_lines_week10.json"),
]

def esc(x):
    return html.escape(str(x if x is not None else ""))

def link_cell(v):
    v = "" if v is None else str(v)
    parts = re.split(r'(https?://\S+)', v)
    out = []
    for p in parts:
        if p.startswith(("http://", "https://")):
            label = p.replace("https://www.", "").replace("https://", "")
            out.append('<a class="src" href="%s">%s%s</a>' % (
                esc(p), esc(label[:44]), "…" if len(label) > 44 else ""))
        else:
            out.append(esc(p))
    return "".join(out)

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

def status_badge(v):
    v = (v or "").upper()
    if any(k in v for k in ("FAIL", "CRITICAL", "OUT", "UNVERIFIED", "BLOCKED", "DEAD", "NEEDS")):
        return "bad"
    if any(k in v for k in ("PARTIAL", "QUESTIONABLE", "DOUBTFUL", "PENDING", "ARMED", "PROPOSED", "SCHEDULED", "OPEN")):
        return "warn"
    if any(k in v for k in ("PASS", "OK", "FINAL", "VERIFIED", "DONE", "RESOLVED", "CHOSEN")):
        return "ok"
    return "info"

def nav(active, prefix):
    return "".join(
        '<a href="%s%s"%s>%s</a>' % (prefix, h, (' class="on"' if h == active else ""), l)
        for h, l in NAV_ROOT)

def page(title, body, active, prefix=""):
    css = prefix + CSS_PATH
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · Own4 NFL</title>
<link rel="stylesheet" href="%s"></head>
<body><header><h1><a href="%sindex.html">Own4 · NFL line origination</a></h1>
<div class="tag">Verified NFL data · official sources only · never-infer policy</div>
<nav>%s</nav></header><main>%s</main>
<footer>%s<br>Every table row carries a source link. Unconfirmable values are blank and flagged — never inferred.</footer>
<script>%s</script></body></html>""" % (
    esc(title), css, prefix, nav(active, prefix), body, esc(BUILD_STAMP), JS)

def read_csv(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ---------------- load data ----------------
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
n_orig = len(origs)
n_dg = sum(1 for g in gates if g["gate_id"].startswith("DG"))
n_corr_n = sum(1 for c in corrs if c["n"])

# ---------------- landing page ----------------
dash = []
dash.append('<h2>NFL line origination — decision dashboard</h2>')
dash.append('<p class="lede">Own4 originates its own NFL lines from verifiable signals and ranks strategies on '
            'calibrated skill, not win rate or short-run ROI. Everything below is re-read from linked sources; '
            'nothing is inferred. Market prices are third-party (the NFL publishes no odds) and are labeled as such; '
            'scores and standings are official-derived.</p>')
dash.append('<div class="grid">')
for k, v, s in [
    ("2026 REG games tracked", str(len(results)), "%d final · %d scheduled (feed reconciled to official standings)" % (n_final, n_sched)),
    ("Markets in price store", str(n_markets), "3 per game: SIDE, TOTAL, MONEYLINE — open + close + settlement"),
    ("Originated markets", str(n_orig), "weeks 10–18 · ordered SIDE → TOTAL → MONEYLINE"),
    ("Strategies on leaderboard", str(len(signal)), "signal rank independent of staking · 0 reward-eligible"),
    ("Correlation values with n", str(n_corr_n), "every r publishes n; player-level rows blank + flagged"),
    ("Demotion gates armed", str(n_dg), "live → paper triggers · see gates page"),
]:
    dash.append('<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>' % (esc(k), esc(v), esc(s)))
dash.append("</div>")

# Decision-readiness table
dash.append('<h3>Decision-readiness table — one row per requirement</h3>')
dash.append('<p class="caption">Each row states the requirement, the gate that blocks it, and the number that would clear it. '
            'Gates are enforced by verify.py; nothing is promoted until its gate passes.</p>')
dash.append('<div class="wrap"><table id="t-ready"><thead><tr>'
            '<th>ID</th><th>Requirement</th><th>Gate that blocks it</th>'
            '<th>Number that would clear it</th><th>Status</th><th>Source</th></tr></thead><tbody>')
for rid, req, gate, number, status, src in READY:
    dash.append('<tr><td class="n">%s</td><td>%s</td><td>%s</td><td>%s</td>'
                '<td><span class="badge %s">%s</span></td><td class="src">%s</td></tr>' % (
        esc(rid), esc(req), esc(gate), esc(number),
        status_badge(status), esc(status), link_cell(src)))
dash.append("</tbody></table></div>")

dash.append('<h3>Category subpages</h3>')
cover = [
    ("Price-snapshot store", "pages/prices.html", "Opening + closing number per market, capture timestamps, provenance"),
    ("Verified results feed", "pages/results.html", "272 games, per-game official URL, reconciled to official standings"),
    ("Origination (side -> total -> ML)", "pages/origination.html", "Fair line / market line / difference as separate columns"),
    ("Leaderboard — signal vs staking", "pages/leaderboard.html", "Two tables; staking cannot influence signal rank"),
    ("Validation & demotion gates", "pages/gates.html", "G1–G8 validation + DG-1–DG-4 live→paper triggers"),
    ("Injuries & replacement depth", "pages/depth.html", "Which string replaces the absent player"),
    ("Correlations with n", "pages/correlations.html", "Every r carries its n; official-derived inputs labeled"),
    ("Questions & answers", "pages/questions.html", "Known / missing / what would settle each decision"),
    ("Suggestions board", "pages/suggestions.html", "Review and choose a path before implementing"),
    ("Flagged for review", "pages/flagged.html", "Irregularities and unverified values, source-linked"),
    ("Sources & verification", "pages/sources.html", "Everything verified against, with what was read and when"),
]
dash.append('<div class="toc">')
for label, href, sub in cover:
    pref = "" if href.startswith("pages/") else ""
    dash.append('<a href="%s">%s<small>%s</small></a>' % (href, esc(label), esc(sub)))
dash.append("</div>")

write("index.html", page("Dashboard", "".join(dash), "index.html"))

# ---------------- executive summary page ----------------
body = []
body.append('<h2>Executive summary</h2>')
body.append('<p class="lede">State of the NFL origination system, every claim source-linked. '
            'Companion markdown: <a href="../EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a>.</p>')
body.append('<div class="note"><strong>Bottom line.</strong> The system now records, for every market it originates, an '
            'opening and a closing number with provenance and settlement, and a verified results feed that makes '
            'backtests and ROI computable at all. On the evidence available today, <strong>no strategy has yet cleared '
            'the luck barrier</strong> (best BH-adjusted p = 0.44), so the leaderboard ranks skill signals honestly and '
            'holds all rewards. One signal under continued paper tracking: unders in outdoor games with wind ≥ 15 mph '
            '(n=303, hit 55.4%, z=1.43) — not yet distinguishable from luck.</div>')
body.append('<h3>What is solid (verified)</h3><ul>'
    '<li>Results feed: 137 settled 2026 REG games, each row carrying its official nfl.com game URL; per-team W-L-T/PF-PA '
    'reconciled cell-by-cell against the official standings (32/32 teams).</li>'
    '<li>Price-snapshot store: 816 market rows with OPEN/CLOSE columns; WAS@NYG shows the mechanism (open NYG −2.5 → close NYG −1.5).</li>'
    '<li>Convention settled: spread_line positive = home favored (nflverse DATASETS.md, 162/163 moneyline-consistency).</li>'
    '<li>Leaderboard separates signal from staking; rank determined by signal metrics only.</li>'
    '</ul>')
body.append('<h3>What is deliberately blank (never inferred)</h3><ul>'
    '<li>Opening lines for 2026 weeks 1–9: no capture exists anywhere in the repo (F-C02) — blank + flagged.</li>'
    '<li>Player-prop prices: the NFL publishes none (A-13) — prop rows blank + flagged.</li>'
    '<li>Replacement depth for clubs whose chart does not answer — blank + flagged.</li>'
    '</ul>')
body.append('<h3>Decisions needed from the owner</h3><ul>'
    '<li>Choose the demotion-gate thresholds (S-C04) — currently project-defined and armed.</li>'
    '<li>Choose among the suggestions board paths before anything is implemented (suggestions.html).</li>'
    '<li>Decide whether to license a closing-line feed to fill the opening/closing gap (S-C02).</li>'
    '</ul>')
write("pages/executive-summary.html", page("Executive summary", "".join(body), "pages/executive-summary.html", prefix="../"))

# ---------------- origination ----------------
body = []
body.append('<h2>Origination — side first, then the total, then the moneyline</h2>')
body.append('<p class="lede">Every market the model originates, in fixed pipeline order: seq 1 SIDE, seq 2 TOTAL, '
            'seq 3 MONEYLINE. For each market the model’s fair line, the market line and the difference are published '
            'as separate columns. difference = model_fair − market (moneyline rows use win-probability points). '
            'Model output is this repo’s walk-forward model; market lines are third-party captures dated 2026-11-13.</p>')
body.append(filter_box("t-orig", 1))
body.append(render_table("t-orig", origs,
    ["origination_seq", "market_type", "week", "gameday", "matchup", "model_fair_line", "market_line",
     "difference", "direction_note", "match_url", "market_source", "verification", "flag"],
    numeric=("origination_seq",), link_cols=("match_url", "market_source")))
write("pages/origination.html", page("Origination", "".join(body), "pages/origination.html", prefix="../"))

# ---------------- price snapshots ----------------
body = []
body.append('<h2>Price-snapshot store — opening and closing numbers</h2>')
body.append('<p class="lede">One row per market (SIDE / TOTAL / MONEYLINE) for every 2026 REG game we originate or '
            'reference, with the opening number, the closing number, their capture times, and settlement. '
            'Where no verified opening capture exists (weeks 1–9, 2026) the open cells are blank and flagged — never '
            'filled in. Market prices are third-party by nature; settlements are verified against official scores.</p>')
body.append('<div class="note"><strong>Example — the store doing its job:</strong> WAS @ NYG, week 10 — SIDE open '
            '2.5 (pre-game capture) → close 1.5 (settled archive). The older A-06 flag treated 1.5 vs 2.5 as a '
            'discrepancy; the store shows it as open→close line movement with both sources recorded.</div>')
body.append('<h3>Originated slate (weeks 10–18)</h3>')
body.append(filter_box("t-snap1", 2))
snaps_o = [r for r in snaps if int(r["week"]) >= 10]
body.append(render_table("t-snap1", snaps_o,
    ["market_id", "origination_seq", "market_type", "open_price", "open_captured_utc", "close_price",
     "close_captured_utc", "settlement", "open_source", "close_source", "settlement_source", "game_url",
     "verification", "flag"],
    numeric=("origination_seq",),
    link_cols=("open_source", "close_source", "settlement_source", "game_url")))
body.append('<h3>Settled 2026 markets (weeks 1–10) — closes for settlement and backtests</h3>')
body.append(filter_box("t-snap2", 3))
snaps_s = [r for r in snaps if int(r["week"]) < 10]
body.append(render_table("t-snap2", snaps_s,
    ["market_id", "market_type", "close_price", "settlement", "close_source", "settlement_source",
     "game_url", "verification", "flag"],
    link_cols=("close_source", "settlement_source", "game_url")))
write("pages/prices.html", page("Price snapshots", "".join(body), "pages/prices.html", prefix="../"))

# ---------------- results ----------------
body = []
body.append('<h2>Verified results feed</h2>')
body.append('<p class="lede">Every 2026 regular-season game with its final score (or scheduled time), closing market '
            'numbers, and settlement of SIDE / TOTAL / MONEYLINE — the join that makes backtests and ROI computable '
            'at all. Every row carries its official nfl.com game URL. Scores reconcile to the official standings '
            '(<a href="https://www.nfl.com/standings/league/2026/REG">nfl.com standings</a>, read 2026-11-14): '
            'the verification script recomputes W-L-T and PF-PA for all 32 teams from this feed and compares '
            'cell-by-cell.</p>')
body.append('<div class="note warn"><strong>Settlement block:</strong> 13 rows settle totals and moneylines only — '
            'their closing spread cells are blank in the archive, so the spread settlement is marked '
            'SETTLE-BLOCKED rather than guessed.</div>')
body.append(filter_box("t-res", 4))
body.append(render_table("t-res", results,
    ["week", "gameday", "away_team", "away_score", "home_team", "home_score", "status",
     "close_spread_home_fav_by", "close_total", "close_away_ml", "close_home_ml",
     "spread_settlement", "total_settlement", "ml_settlement", "game_url", "verification", "flag"],
    numeric=("week", "away_score", "home_score", "close_spread_home_fav_by", "close_total",
             "close_away_ml", "close_home_ml"),
    link_cols=("game_url",), badge_col="status", badge_map=status_badge))
write("pages/results.html", page("Results feed", "".join(body), "pages/results.html", prefix="../"))

# ---------------- leaderboard ----------------
body = []
body.append('<h2>Leaderboard — signal separated from staking</h2>')
body.append('<p class="lede">A lucky staking run cannot mask a bad signal: ranking uses <strong>signal metrics only</strong> '
            '(hit-rate z against break-even at flat prices). Stake-level outcomes (ROI, drawdown) are published in a '
            'separate table that never affects ranks. All prices are third-party; settlements come from the verified '
            'results feed.</p>')
body.append('<h3>Signal table (this determines rank)</h3>')
body.append(filter_box("t-sig", 5))
body.append(render_table("t-sig", signal,
    ["signal_rank", "strategy_id", "family", "name", "rule", "n_settled", "wins", "hit_rate",
     "break_even_rate", "z_vs_breakeven", "p_value", "p_value_bh", "wilson95", "signal_verdict",
     "signal_rank_basis", "source_url", "verification", "flag"],
    numeric=("signal_rank", "n_settled", "wins", "hit_rate", "break_even_rate", "z_vs_breakeven",
             "p_value", "p_value_bh"),
    link_cols=("source_url",)))
body.append('<h3>Staking table (cannot influence rank)</h3>')
body.append(filter_box("t-stk", 6))
body.append(render_table("t-stk", staking,
    ["strategy_id", "family", "name", "flat_stake_roi_all", "pnl_units_flat", "staked_units_flat",
     "confirmation_n", "confirmation_roi_flat", "max_drawdown_units", "reward_eligible",
     "staked_at_current_plan", "source_url", "verification", "flag"],
    numeric=("flat_stake_roi_all", "pnl_units_flat", "staked_units_flat", "confirmation_n",
             "confirmation_roi_flat", "max_drawdown_units"),
    link_cols=("source_url",), badge_col="reward_eligible", badge_map=status_badge))
body.append('<div class="note"><strong>Demotion gate:</strong> any LIVE strategy returns to PAPER when a trigger in '
            '<a href="gates.html">DG-1..DG-4</a> fires. No strategy is live today (none has passed G4), so the gates '
            'are armed, not firing.</div>')
write("pages/leaderboard.html", page("Leaderboard", "".join(body), "pages/leaderboard.html", prefix="../"))

# ---------------- gates ----------------
body = []
body.append('<h2>Validation gates and the demotion gate</h2>')
body.append('<p class="lede">A strategy must pass the validation gates G1–G8 before it can be promoted or rewarded. '
            'The demotion gates DG-1..DG-4 send a live strategy back to paper when their trigger fires. '
            'Thresholds not fixed by an external standard are marked project-defined and appear on the '
            '<a href="suggestions.html">suggestions board</a> for owner choice.</p>')
body.append(render_table("t-gates", gates,
    ["gate_id", "name", "rule", "threshold_origin", "current_status", "note", "source_url"],
    link_cols=("source_url",), badge_col="current_status", badge_map=status_badge))
write("pages/gates.html", page("Gates", "".join(body), "pages/gates.html", prefix="../"))

# ---------------- depth ----------------
body = []
body.append('<h2>Injuries & replacement depth</h2>')
body.append('<p class="lede">Not just the fact of a replacement — the <strong>depth of the replacement</strong>: which '
            'player steps in, and which string (2nd, 3rd, 4th) that player is on the club’s own depth chart. Injury '
            'statuses come from the official week-10 report (<a href="https://www.nfl.com/injuries/">nfl.com/injuries</a>, '
            'read 2026-11-14); depth strings come from official club sites where read this session. Where no chart '
            'answer exists, cells stay blank and flagged.</p>')
body.append('<div class="note"><strong>Club sites DO publish depth charts:</strong> e.g. '
            '<a href="https://www.detroitlions.com/team/depth-chart">detroitlions.com</a> and '
            '<a href="https://www.patriots.com/team/depth-chart">patriots.com</a>, both read 2026-11-14. The charts '
            'label themselves “unofficial”; the league-level route on nfl.com remains 404.</div>')
body.append(filter_box("t-depth", 7))
body.append(render_table("t-depth", depth,
    ["team", "position", "absent_player", "official_game_status", "chart_position", "replacement",
     "replacement_depth_string", "further_depth", "injury_report_url", "depth_chart_url", "verification", "flag"],
    link_cols=("injury_report_url", "depth_chart_url"),
    badge_col="official_game_status", badge_map=status_badge))
body.append('<h3>Why the string matters (week 10 examples)</h3><ul>'
    '<li><strong>DET C:</strong> Cade Mays Out → Juice Scruggs, 2nd-string C (club chart).</li>'
    '<li><strong>DET CB:</strong> D.J. Reed Out → Rock Ya-Sin, 2nd-string CB.</li>'
    '<li><strong>DET S:</strong> Kerby Joseph Out, but the club chart does not list him at S → replacement blank + flagged.</li>'
    '</ul>')
write("pages/depth.html", page("Depth", "".join(body), "pages/depth.html", prefix="../"))

# ---------------- correlations ----------------
body = []
body.append('<h2>Correlations — officially sourced inputs, n published with every value</h2>')
body.append('<p class="lede">Every correlation value carries its n. Values are computed only on officially sourced '
            'numbers (game scores from the official-derived archive, reconciled to nfl.com) — where market prices are '
            'part of the input the row says so. Player-level pairs remain blank: no verified player-level series '
            'exists (Q-C08/Q-09).</p>')
body.append(render_table("t-corr", corrs,
    ["id", "group", "pair", "n", "pearson_r", "ci95", "p_value", "inputs_official", "reading",
     "source_url", "verification", "flag"],
    numeric=("n", "pearson_r", "p_value"), link_cols=("source_url",)))
write("pages/correlations.html", page("Correlations", "".join(body), "pages/correlations.html", prefix="../"))

# ---------------- questions ----------------
body = []
body.append('<h2>Questions, information and answers — decision register</h2>')
body.append('<p class="lede">The questions that must be answered before any decision can reasonably be made: what we '
            'know, what is missing, and exactly what evidence would settle each one. Questions are also how we discover '
            'missing information — every blank cell in this workspace should trace back to a row here.</p>')
body.append(render_table("t-q", questions,
    ["id", "question", "information_known", "information_missing", "answer_status",
     "evidence_that_would_settle", "source_url", "status"],
    link_cols=("source_url",), badge_col="status", badge_map=status_badge))
write("pages/questions.html", page("Questions", "".join(body), "pages/questions.html", prefix="../"))

# ---------------- suggestions ----------------
body = []
body.append('<h2>Suggestions board — review and choose the path before implementation</h2>')
body.append('<p class="lede">Improvements to the system and site that would sharpen decision-making. Each suggestion '
            'lists options and a recommended path, and <strong>nothing is implemented until the owner chooses</strong> — '
            'the review column must move from “proposed” to “chosen” first.</p>')
body.append(render_table("t-sug", suggestions,
    ["id", "suggestion", "why_it_helps_decisions", "options", "recommended_path",
     "review_status", "implementation_state", "source_url"],
    link_cols=("source_url",), badge_col="review_status", badge_map=status_badge))
write("pages/suggestions.html", page("Suggestions", "".join(body), "pages/suggestions.html", prefix="../"))

# ---------------- flagged ----------------
body = []
body.append('<h2>Flagged for review</h2>')
body.append('<p class="lede">Irregularities, unverified values and corrections found while building this workspace. '
            'None of these block use of the site; each carries its source links so the owner can review after the site '
            'is live and request changes.</p>')
body.append(render_table("t-flag", flagged,
    ["id", "severity", "what", "evidence", "source_url", "status"],
    link_cols=("source_url",), badge_col="status", badge_map=status_badge))
write("pages/flagged.html", page("Flagged", "".join(body), "pages/flagged.html", prefix="../"))

# ---------------- sources ----------------
body = []
body.append('<h2>Sources & verification</h2>')
body.append('<p class="lede">Everything this workspace was verified against, with what was checked and when. '
            'Official = published by the NFL or its clubs; third-party = everything else (market prices, model archives).</p>')
try:
    reads = json.load(open(os.path.join(DATA, "official_reads_2026-11-14.json")))
    srows = []
    for r in reads.get("official_reads", []):
        is_official = ("nfl.com" in r["url"]) or (".com/team/" in r["url"])
        srows.append({"id": r["id"],
                      "publisher": ("NFL.com / official club site" if is_official else "nflverse (third-party dataset docs)"),
                      "url": r["url"], "title": r["title"], "read_utc": r["read_utc"],
                      "what_was_read": r["what"],
                      "tier": "OFFICIAL" if is_official else "THIRD-PARTY"})
    body.append(render_table("t-src", srows,
        ["id", "tier", "publisher", "title", "url", "read_utc", "what_was_read"], link_cols=("url",)))
except Exception as e:
    body.append('<p class="note warn">Could not load official reads: %s</p>' % esc(str(e)))
body.append('<h3>Upstream repository datasets (reused, provenance kept)</h3>')
body.append(render_table("t-src2", [
    {"id": "UP-01", "tier": "THIRD-PARTY", "publisher": "nflverse/nfldata (Lee Sharpe)",
     "title": "games dataset (pinned copy)", "url": "https://github.com/nflverse/nfldata/blob/master/DATASETS.md",
     "read_utc": "2026-11-14", "what_was_read": "column definitions quoted in official_reads OR-06; pinned copy at nfl-arena/data/raw/games.csv"},
    {"id": "UP-02", "tier": "MODEL-INTERNAL", "publisher": "this repository (nfl-lines)",
     "title": "walk-forward model output", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/own_lines_week10.json",
     "read_utc": "2026-11-14", "what_was_read": "fair lines + market captures for the weeks 10–18 origination slate"},
    {"id": "UP-03", "tier": "MODEL-INTERNAL", "publisher": "this repository (nfl-lines/nfl-arena)",
     "title": "strategy settlement metrics", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json",
     "read_utc": "2026-11-14", "what_was_read": "per-strategy n/wins/ROI/drawdown splits used in the leaderboard tables"},
], ["id", "tier", "publisher", "title", "url", "read_utc", "what_was_read"], link_cols=("url",)))
body.append('<div class="note"><strong>Verification method.</strong> (1) Official pages fetched and read directly '
            '(sources table). (2) Results feed reconciled cell-by-cell against the official standings for all 32 teams '
            'by verify.py. (3) Spread convention verified against 163 settled/in-lined 2026 games (162/163 ML-consistency) '
            'and quoted from DATASETS.md. (4) Every generated table row checked for a source link; blanks allowed only '
            'with a flag.</div>')
write("pages/sources.html", page("Sources", "".join(body), "pages/sources.html", prefix="../"))

print("site written: %d pages + index" % (len(NAV_ROOT) - 1))

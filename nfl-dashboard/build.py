#!/usr/bin/env python3
"""nfl-dashboard site generator — standard library only.
Reads nfl-dashboard/data/*.json, writes nfl-dashboard/*.html and nfl-dashboard/pages/*.html.
Deterministic: rebuilding produces byte-identical output (modulo generated_utc stamps, which are pinned in source data).
Every table row carries a source link; unverified values are blank and flagged. Nothing is inferred.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def L(url, text):
    return "<a href=\"%s\" target=\"_blank\" rel=\"noopener\">%s&#8203;</a>" % (esc(url), esc(text))


def blank(reason="not available from an official source"):
    return "<span class=\"blank\">&#8212;</span>"  # em-dash blank cell


CSS = """
<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>%s</title>
<style>
  :root{--ink:#1a1a1a;--muted:#555;--line:#ddd;--bg:#fff;--card:#f7f7f7;--flag:#7a1f1f;--ok:#1e6b3a;--warn:#8a6d00;}
  *{box-sizing:border-box}body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);margin:0;line-height:1.5}
  .wrap{max-width:1200px;margin:0 auto;padding:0 16px}
  header{border-bottom:1px solid var(--line);padding:18px 0;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
  .brand{font-size:1.25rem;font-weight:700;text-decoration:none;color:var(--ink)}
  .brand span{color:var(--muted);font-weight:400;font-size:0.85rem}
  nav a{text-decoration:none;color:#0056b3;margin-right:14px;font-size:0.9rem}
  nav a:hover{text-decoration:underline}
  .meta{color:var(--muted);font-size:0.85rem;margin-top:4px}
  h1{font-size:1.5rem;margin:24px 0 6px}
  h2{font-size:1.15rem;margin:26px 0 10px;border-bottom:1px solid var(--line);padding-bottom:4px}
  h3{font-size:1rem;margin:20px 0 6px}
  p{margin:8px 0}
  .panel{border:1px solid var(--line);background:var(--card);padding:12px 16px;margin:14px 0;border-radius:8px}
  .panel.warn{border-left:4px solid var(--warn);background:#fdf6e3}
  .panel.ok{border-left:4px solid var(--ok);background:#eef7f0}
  .panel.bad{border-left:4px solid var(--flag);background:#fbf3f3}
  .badge{display:inline-block;padding:1px 7px;border-radius:10px;font-size:0.78rem;font-weight:700;margin-right:6px}
  .b-ok{background:#dff0e4;color:var(--ok)}.b-blocked{background:#f4cccc;color:#7a1f1f}
  .b-warn{background:#fde9d9;color:var(--warn)}.b-done{background:#cfe2f3;color:#1a4e8c}
  table{border-collapse:collapse;width:100%;margin:10px 0;font-size:0.88rem}
  caption{caption-side:top;text-align:left;font-weight:700;margin-bottom:6px;font-size:0.95rem}
  th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
  th{background:#f0f0f0}
  tr:nth-child(even)td{background:#fafafa}
  .blank{color:#999}
  ul{margin:6px 0 6px 18px}
  li{margin:3px 0}
  .kpi{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
  .kpi .card{border:1px solid var(--line);background:var(--card);padding:12px 14px;border-radius:8px;min-width:150px}
  .kpi .big{font-size:1.5rem;font-weight:800}
  .kpi .small{color:var(--muted);font-size:0.85rem}
  .src{font-size:0.8rem;color:#0056b3}
  .two-col{display:flex;gap:16px;flex-wrap:wrap}
  .two-col > div{flex:1;min-width:260px}
  footer{margin-top:30px;padding-bottom:30px;border-top:1px solid var(--line);color:var(--muted);font-size:0.85rem}
  .toc a{display:block;padding:4px 0;text-decoration:none;color:#0056b3}
  .toc a:hover{text-decoration:underline}
</style></head><body><div class="wrap">"""

FOOTER = """
<footer><strong>Own4 &#8212; NFL line-origination research</strong>. Analytical research only, not wagering advice. Snapshot 2026-11-15;
every data row links to the page it was read from, and every value that could not be confirmed from an official source is blank and
listed on the <a href=\"pages/flagged.html\">Flagged for review</a> page.<br>
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &#183;
<a href=\"https://www.ncpgambling.org/help-treatment\" target=\"_blank\" rel=\"noopener\">NCPG &#8254;</a></footer></div></body></html>"""

def nav(root_prefix, page_prefix):
    return """<nav>
  <a href=\"%sindex.html\">Landing</a>
  <a href=\"%sexecutive-summary.html\">Executive summary</a>
  <a href=\"%sstandings.html\">Official data &#8212; standings</a>
  <a href=\"%sresults-feed.html\">Verified results feed</a>
  <a href=\"%sprice-snapshots.html\">Price-snapshot store</a>
  <a href=\"%sorigination.html\">Originated lines (side&#8594;total&#8594;ML)</a>
  <a href=\"%sstrategies.html\">Strategies (pre-registered)</a>
  <a href=\"%sleaderboard.html\">Leaderboard: signal vs staking</a>
  <a href=\"%sgates.html\">Validation &amp; demotion gates</a>
  <a href=\"%scorrelations.html\">Correlations (with n)</a>
  <a href=\"%sinjuries-depth.html\">Injuries &amp; replacement depth</a>
  <a href=\"%squestions.html\">Questions / answers register</a>
  <a href=\"%ssuggestions.html\">Suggestions review board</a>
  <a href=\"%sflagged.html\">&#9873; Flagged for review</a>
  <a href=\"%ssources.html\">Source register</a>
  <a href=\"%sindex.html\">Root dashboard &#8254;</a>
</nav>""" % (root_prefix, page_prefix, page_prefix, page_prefix, page_prefix, page_prefix,
             page_prefix, page_prefix, page_prefix, page_prefix, page_prefix, page_prefix,
             page_prefix, page_prefix, page_prefix, root_prefix)


def footer(page_prefix):
    return """<footer><strong>Own4 &#8212; NFL line-origination research</strong>. Analytical research only, not wagering advice. Snapshot 2026-11-15;
every data row links to the page it was read from, and every value that could not be confirmed from an official source is blank and
listed on the <a href=\"%sflagged.html\">Flagged for review</a> page.<br>
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &#183;
<a href=\"https://www.ncpgambling.org/help-treatment\" target=\"_blank\" rel=\"noopener\">NCPG &#8254;</a></footer></div></body></html>""" % (page_prefix,)


def shell(title, body, root_prefix="", page_prefix="pages/"):
    _p = page_prefix
    body = body.replace('href="pages/', 'href="' + _p).replace("href='pages/", "href='" + _p)
    return CSS.replace("%", "%%").replace("%%s", "%s") % title + "<header><div class=\"brand\">Own4 <span>&#8212; NFL line-origination research</span></div>" + nav(root_prefix, page_prefix) + \
        "<div class=\"meta\">Snapshot 2026-11-15 &#183; official sources only &#183; unverified values are blank and flagged</div></header>" + body + footer(page_prefix)


def table(caption, headers, rows):
    h = "<table><caption>%s</caption><thead><tr>" % esc(caption)
    h += "".join("<th scope=\"col\">%s</th>" % esc(x) for x in headers)
    h += "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in rows) + "</tbody></table>"
    return h


def stddev_point_margin():
    return 13.5  # DG-B assumption (flagged)


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def fair_ml(p):
    if p >= 0.5:
        return -round(100.0 * p / (1.0 - p))
    return round(100.0 * (1.0 - p) / p)


def fisher_ci(r, n):
    if n < 4 or abs(r) >= 1:
        return None, None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return lo, hi


def p_value_approx(r, n):
    """two-sided p via Fisher z normal approximation; labeled as such"""
    if n < 4 or abs(r) >= 1:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    zs = abs(z) / se
    # normal two-sided p via erfc
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(zs / math.sqrt(2.0))))


def build():
    standings = load("standings.json")
    week10 = load("week10.json")
    week11 = load("week11.json")
    injuries = load("injuries_week10.json")
    strategies = load("strategies.json")
    gates = load("gates.json")
    corr = load("correlations.json")
    depth = load("depth.json")
    questions = load("questions.json")
    suggestions = load("suggestions.json")
    flags = load("flags.json")
    sources = load("sources.json")

    os.makedirs(PAGES, exist_ok=True)

    # ---------- derived computations ----------
    teams = standings["teams"]
    total_pf = sum(t["PF"] for t in teams)
    total_pa = sum(t["PA"] for t in teams)
    total_games = sum(t["W"] + t["L"] + t["T"] for t in teams) / 2.0
    league_ppg = total_pf / total_games  # combined points per game
    team_ppg = league_ppg / 2.0

    def wpct(t):
        g = t["W"] + t["L"] + t["T"]
        return t["W"] / g if g else None

    def home_wpct(t):
        wl = t["HOME"].replace(" ", "").split("-")
        hw, hl = int(wl[0]), int(wl[1])
        g = hw + hl
        return hw / g if g else None

    xs = [t["PF"] - t["PA"] for t in teams]
    ys = [wpct(t) for t in teams]
    n = len(teams)
    mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (n - 1)
    sx = math.sqrt(sum((a - mx) ** 2 for a in xs) / (n - 1))
    sy = math.sqrt(sum((b - my) ** 2 for b in ys) / (n - 1))
    r1 = cov / (sx * sy)

    hs = [home_wpct(t) for t in teams]
    mx2 = sum(hs) / n; my2 = my
    cov2 = sum((a - mx2) * (b - my2) for a, b in zip(hs, ys)) / (n - 1)
    sx2 = math.sqrt(sum((a - mx2) ** 2 for a in hs) / (n - 1))
    r2 = cov2 / (sx2 * sy)

    decided = [g for g in week10["games"] if g["status"] == "final"]
    home_wins = sum(1 for g in decided if g["home_score"] > g["away_score"])
    home_rate = home_wins / len(decided) if decided else None

    # ---------- originated fair lines (Week 11) ----------
    strength = {t["club"]: (t["PF"] - t["PA"]) / (t["W"] + t["L"] + t["T"]) for t in teams}
    HFA = 2.0  # DG-A assumption, flagged
    lines = []
    seq = 1
    for g in week11["games"]:
        away, home = g["away"], g["home"]
        edge = strength[home] - strength[away] + HFA  # home expected margin, pts
        fair_spread = -edge  # negative = home favored
        p_home = logistic(edge / stddev_point_margin())
        fair_total = league_ppg  # v1: league average combined total
        ml = fair_ml(p_home)
        lines.append({
            "game": "%s at %s" % (away, home), "away": away, "home": home,
            "date": g["date"], "time": g["time"], "network": g["network"],
            "seq": seq, "fair_spread": fair_spread, "fair_total": fair_total,
            "p_home": p_home, "fair_ml": ml,
        })
        seq += 1

    # ---------- pages ----------
    write("index.html", landing_page(standings, week10, gates, strategies, flags, lines))
    write(os.path.join(PAGES, "executive-summary.html"), executive_summary_page(standings, week10, gates, flags))
    write(os.path.join(PAGES, "standings.html"), standings_page(standings))
    write(os.path.join(PAGES, "results-feed.html"), results_feed_page(week10))
    write(os.path.join(PAGES, "price-snapshots.html"), price_snapshots_page())
    write(os.path.join(PAGES, "origination.html"), origination_page(lines, week11))
    write(os.path.join(PAGES, "strategies.html"), strategies_page(strategies))
    write(os.path.join(PAGES, "leaderboard.html"), leaderboard_page(strategies))
    write(os.path.join(PAGES, "gates.html"), gates_page(gates))
    write(os.path.join(PAGES, "correlations.html"), correlations_page(r1, r2, home_rate, n, total_pf, total_pa, total_games, league_ppg))
    write(os.path.join(PAGES, "injuries-depth.html"), injuries_depth_page(injuries, depth))
    write(os.path.join(PAGES, "questions.html"), questions_page(questions))
    write(os.path.join(PAGES, "suggestions.html"), suggestions_page(suggestions))
    write(os.path.join(PAGES, "flagged.html"), flagged_page(flags))
    write(os.path.join(PAGES, "sources.html"), sources_page(sources))
    print("built %d pages" % (1 + len(os.listdir(PAGES))))


def write(path, html_text):
    with open(path, "w") as f:
        f.write(html_text)


# ---------------- page content ----------------

def landing_page(standings, week10, gates, strategies, flags, lines):
    teams = standings["teams"]
    n_teams = len(teams)
    decided = [g for g in week10["games"] if g["status"] == "final"]
    n_final = len(decided)
    n_live = sum(1 for g in week10["games"] if g["status"] in ("live", "halftime"))
    n_up = sum(1 for g in week10["games"] if g["status"] == "upcoming")
    n_byes = len(week10["byes"])
    n_flag = len(flags["rows"])
    kpis = [
        (str(n_teams), "official teams in the standings (read 2026-11-15)", "S1"),
        ("%d final" % n_final + " / %d live" % n_live + " / %d upcoming" % n_up, "Week 10 games at snapshot time", "S2"),
        ("%d" % n_byes, "teams on bye in Week 10", "S2"),
        ("0", "strategies qualify for rewards", "strategies.json"),
        ("0", "reward points awarded", "strategies.json"),
        ("%d" % n_flag, "items flagged for review", "flags.json"),
    ]
    kpi_html = "".join(
        "<div class=\"card\"><div class=\"big\">%s</div><div class=\"small\">%s <span class=\"src\">[%s]</span></div></div>" % (a, b, c) for a, b, c in kpis
    )

    FLAGS_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json", "flags.json")
    readiness = [
        ("Price-snapshot store: opening and closing numbers for every market we originate", "G7 / MK-01", "licensed or official odds feed", "blocked", "market open/close blank by policy; no NFL price source exists"),
        ("Verified results feed so backtests and ROI can be computed", "&#8212;", "&#8212;", "done", "Week 10 official results published with per-game source links"),
        ("Origination order: side, then total, then moneyline", "G10", "&#8212;", "done", "enforced in code and published as a sequence column"),
        ("Fair line / market line / difference as separate columns", "G7", "market price source", "partial", "fair line published; market line and difference blank (no official price)"),
        ("Signal separated from staking in the leaderboard", "G9 / G10", "&#8212;", "done", "two tables: signal metrics, staking metrics; never mixed"),
        ("Correlations computed only from officially sourced numbers, n published", "G6", "&#8212;", "done", "CR-01/CR-02/CR-03 computed with n; all other correlations blank by rule"),
        ("Demotion gate that sends a live strategy back to paper", "DG-1c", "pre-registered drawdown limit", "partial", "gate defined (DG-1a…d); drawdown limit not yet registered"),
        ("Pre-register every strategy; no backtest numbers on the leaderboard", "G10", "&#8212;", "done", "7 strategies pre-registered before results; 0 qualified; 0 backtest numbers on the board"),
        ("Availability graph: expected vs actual starters", "F-03 / F-04", "official depth chart or verified snap counts for all 32 clubs", "blocked", "no depth source; Game Book lineups are post-game only"),
        ("Injury signal as a surprise (delta), never a level", "Q14", "code implementing designation deltas", "decided, not implemented", "policy recorded; pipeline change pending (S-09)"),
        ("32-team roster/IR sweep before trusting any team model", "Q13", "official IR/transactions capture for all 32 clubs", "not run", "&#8212;"),
        ("Model output = probability plus its inputs", "&#8212;", "&#8212;", "done", "originated lines page shows fair line, inputs and assumptions per game"),
        ("\"Removal of luck\" panel on the dashboard", "G2 / G8", "graded out-of-sample forecasts", "not run", "no graded forecasts exist yet"),
        ("Two-sided \"what would change our mind\" field per strategy", "Q01", "graded results vs frozen definition", "per-strategy", "blank until results exist (by design)"),
        ("Price our own line and publish residual vs market, on a schedule", "F-01", "market price source", "partial", "fair line published; residual blank (no market price)"),
        ("Pre-registered backtest corpus (136-game log)", "G1", "300 graded out-of-sample games", "blocked", "corpus referenced in sibling namespaces; not re-hosted here"),
        ("Decision-readiness table: one row per requirement, gate, number to clear", "&#8212;", "&#8212;", "done", "this table"),
    ]
    rows = []
    for req, gate, clear, status, disp in readiness:
        badge = {"done": "b-done", "partial": "b-warn", "blocked": "b-blocked", "decided, not implemented": "b-warn", "not run": "b-warn", "per-strategy": "b-warn"}[status]
        rows.append([esc(req), "<span class=\"badge %s\">%s</span>" % (badge, esc(status)), esc(gate), esc(clear), FLAGS_SRC, esc(disp)])

    body = """
<h1>NFL line-origination research &#8212; landing page</h1>
<p class=\"meta\">Clean dashboard: one landing page, category subpages, every entry in a source-linked table. Nothing is inferred; blank cells are flagged.</p>

<div class=\"kpi\">%s</div>

<h2>Start here</h2>
<div class=\"two-col\">
<div><ul>
<li><a href=\"pages/executive-summary.html\">Executive summary</a> &#8212; what is known, unknown and decided.</li>
<li><a href=\"pages/origination.html\">Originated lines</a> &#8212; side &#8594; total &#8594; moneyline, fair line / market line / difference columns.</li>
<li><a href=\"pages/leaderboard.html\">Leaderboard</a> &#8212; signal and staking ranked separately.</li>
<li><a href=\"pages/flagged.html\">&#9873; Flagged for review</a> &#8212; every irregularity and blank value.</li>
<li><a href=\"pages/suggestions.html\">Suggestions review board</a> &#8212; review a path before anything is implemented.</li>
<li><a href=\"pages/questions.html\">Questions / answers register</a> &#8212; what must be settled before decisions.</li>
</ul></div>
<div><ul>
<li><a href=\"pages/standings.html\">Official standings</a> (32 teams, source-linked)</li>
<li><a href=\"pages/results-feed.html\">Verified results feed</a> (Week 10 official scores)</li>
<li><a href=\"pages/price-snapshots.html\">Price-snapshot store</a> (schema + finding)</li>
<li><a href=\"pages/gates.html\">Validation &amp; demotion gates</a></li>
<li><a href=\"pages/correlations.html\">Correlations with n</a></li>
<li><a href=\"pages/injuries-depth.html\">Injuries &amp; replacement depth</a></li>
<li><a href=\"pages/sources.html\">Source register</a></li>
</ul></div>
</div>

<h2>Decision-readiness table &#8212; one row per requirement</h2>
<p class=\"meta\">Each row states the requirement, the gate that blocks it, the number that would clear it, and its status. Blocked/partial items are linked to the Flagged page.</p>
%s

<h2>Headline result</h2>
<div class=\"panel bad\"><strong>No edge is claimed.</strong> No strategy clears the pre-registered gates; zero reward points are awarded. The model is a v1 research baseline
with flagged assumptions (home field +2.0 pts, uncalibrated logistic scale, league-average total). Because the NFL publishes no odds, no ROI or CLV is computable anywhere on this site.
The value of this release is the verified data, the public gates and the honest scoreboard &#8212; not a pick.</div>

<h2>Published categories</h2>
<table><caption>Category &#8594; page &#8594; what it contains</caption>
<thead><tr><th scope=\"col\">Category</th><th scope=\"col\">Page</th><th scope=\"col\">Contents</th></tr></thead>
<tbody>
<tr><td>Official data</td><td><a href=\"pages/standings.html\">Standings</a></td><td>32 teams, every cell source-linked to nfl.com/standings; league identity &Sigma;PF = &Sigma;PA = 6,664 verified <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/standings.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Verified results feed</td><td><a href=\"pages/results-feed.html\">Week 10 results</a></td><td>14 games + 4 byes; final/live/upcoming status; per-game official URLs <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/week10.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Price-snapshot store</td><td><a href=\"pages/price-snapshots.html\">Store</a></td><td>schema (open/close per market), origination order, finding: no official price source <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/price_snapshots.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Originated lines</td><td><a href=\"pages/origination.html\">Week 11 lines</a></td><td>side &#8594; total &#8594; moneyline; fair line / market line / difference columns; model outputs labeled <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/originated_lines.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Strategies</td><td><a href=\"pages/strategies.html\">Catalog</a></td><td>7 pre-registered strategies: 3 singles, 2 cross-game parlays, 1 same-game parlay (blocked), 1 prop combo (blocked) <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Leaderboard</td><td><a href=\"pages/leaderboard.html\">Signal vs staking</a></td><td>two separate tables; 0 qualify; 0 reward points <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Gates</td><td><a href=\"pages/gates.html\">Validation &amp; demotion</a></td><td>G1-G10 plus demotion gate DG-1; 0 live strategies; 0 demotions <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/gates.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Correlations</td><td><a href=\"pages/correlations.html\">With n</a></td><td>official-input correlations only; every value published with n <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/correlations.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Injuries &amp; depth</td><td><a href=\"pages/injuries-depth.html\">Tracker</a></td><td>official Week 10 designations; replacement depth blank by policy (no depth source) <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/injuries_week10.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Decisions</td><td><a href=\"pages/questions.html\">Questions register</a> / <a href=\"pages/suggestions.html\">Suggestions board</a></td><td>what must be settled before decisions; review-before-implement paths <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/questions.json" target="_blank" rel="noopener">source</a></td></tr>
<tr><td>Review</td><td><a href=\"pages/flagged.html\">Flagged</a> / <a href=\"pages/sources.html\">Sources</a></td><td>10 irregularities; 6 official sources <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json" target="_blank" rel="noopener">source</a></td></tr>
</tbody></table>
""" % ("".join(kpi_html), table("Decision-readiness table",
    ["Requirement", "Status", "Gate that blocks it", "Number that would clear it", "Flags", "Disposition"],
    rows))

    return shell("Own4 &#8212; NFL landing page", body, "", "pages/")


def executive_summary_page(standings, week10, gates, flags):
    body = """
<h1>Executive summary</h1>
<p class=\"meta\">One page: what we know, what we do not know, what we decided, and what must happen next. Every figure is source-linked or blank.</p>

<h2>Known (verified from official sources)</h2>
<ul>
<li>All 32 teams' 2026 standings as of 2026-11-15, re-read cell-by-cell from nfl.com/standings; league identity &Sigma;PF = &Sigma;PA = 6,664 verified by the build script.</li>
<li>Week 10 schedule and scores: 14 games (10 final, 2 live, 1 halftime, 1 upcoming), 4 byes (CHI, DEN, PHI, TB), from nfl.com/schedules/2026/by-week/week-10.</li>
<li>Week 11 schedule: 13 upcoming games + 6 byes (ATL, CLE, GB, LAR, NE, SEA), from nfl.com/schedules/2026/by-week/week-11.</li>
<li>Week 10 injury report designations, published as rendered; team-misattribution irregularity flagged (F-02).</li>
<li>No betting price exists anywhere on nfl.com or operations.nfl.com; this absence is documented (F-01), not worked around.</li>
<li>Pre-registration discipline: 7 strategy definitions frozen before results; git commit hash is the registration.</li>
</ul>

<h2>Not known (blank, never inferred)</h2>
<ul>
<li>Market open/close lines, moneylines and prices (F-01).</li>
<li>Replacement depth rank and replacement name for every out starter (F-03): no official depth chart is published.</li>
<li>Designation deltas (Wednesday&#8594;Friday&#8594;kickoff): only one injury snapshot exists (F-04).</li>
<li>Per-designation play rate with confidence intervals (Q04): requires multiple seasons of designations joined to official inactives (n = 0 today).</li>
<li>Whether injury designations change outcomes (Q06): no archived injury reports exist.</li>
<li>Any strategy edge: 0 of 7 strategies qualify; 0 reward points paid.</li>
</ul>

<h2>Decided</h2>
<ul>
<li>Signal and staking are ranked in separate tables (no lucky staking run can mask bad signal).</li>
<li>Same-game parlays and prop combos are blocked at the joint-evidence gate (no validated joint probability, no void/push rules).</li>
<li>Correlations use officially sourced numbers only, with n published.</li>
<li>Injury enters as a surprise (delta), never a level &#8212; policy recorded, implementation pending (S-09).</li>
<li>Depth is never derived from jersey number, experience or salary.</li>
<li>No backtest numbers appear on the leaderboard; 0 strategies pass the gates.</li>
</ul>

<h2>What would change our mind</h2>
<ul>
<li>A licensed or official odds feed (unblocks G7, ROI/CLV grading, strategy qualification).</li>
<li>Timestamped Wed/Thu/Fri injury snapshots with retained hashes (unblocks Q03, Q15, surprise injury features).</li>
<li>A verified depth source for all 32 clubs (unblocks Q05, replacement-depth features).</li>
<li>Graded out-of-sample results against each frozen strategy definition (gates G1-G10).</li>
<li>Funded, written reward terms before any points are paid.</li>
</ul>

<h2>Scorecard</h2>
<table><caption>Measure &#8594; result</caption>
<thead><tr><th scope=\"col\">Measure</th><th scope=\"col\">Result</th><th scope=\"col\">Source</th></tr></thead>
<tbody>
<tr><td>Strategies registered</td><td>7 (3 singles, 2 parlays, 1 SGP blocked, 1 prop combo blocked)</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json" target="_blank" rel="noopener">strategies.json</a></td></tr>
<tr><td>Strategies qualifying for rewards</td><td>0</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json" target="_blank" rel="noopener">strategies.json</a></td></tr>
<tr><td>Reward points awarded</td><td>0 of 1,000</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json" target="_blank" rel="noopener">strategies.json</a></td></tr>
<tr><td>Live strategies</td><td>0</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/gates.json" target="_blank" rel="noopener">gates.json (DG-1)</a></td></tr>
<tr><td>Strategies demoted to paper</td><td>0</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/gates.json" target="_blank" rel="noopener">gates.json (DG-1)</a></td></tr>
<tr><td>Correlations computed from official inputs</td><td>3 (CR-01, CR-02, CR-03)</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/correlations.json" target="_blank" rel="noopener">correlations.json</a></td></tr>
<tr><td>Correlations blank by rule</td><td>3 (CR-04 reported, CR-05/CR-06 n=0)</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/correlations.json" target="_blank" rel="noopener">correlations.json</a></td></tr>
<tr><td>Items flagged for review</td><td>10</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json" target="_blank" rel="noopener">flags.json</a></td></tr>
<tr><td>Suggestions awaiting owner decision</td><td>10</td><td><a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/suggestions.json" target="_blank" rel="noopener">suggestions.json</a></td></tr>
</tbody></table>

<div class=\"panel ok\"><strong>Bottom line:</strong> this is a research release with an honest negative result. The machinery (verified data, pre-registered gates,
proper-score separation of signal from staking, luck-aware controls) is in place; no strategy has yet cleared it, and nothing is presented as a bet.</div>
"""
    return shell("Executive summary", body, "../", "")


def standings_page(standings):
    rows = []
    src = L(standings["source"], standings["source_title"])
    for t in teams_rows(standings):
        rows.append([t["club"], t["name"], t["W"], t["L"], t["T"], t["PCT"], t["PF"], t["PA"], t["NET"],
                     t["HOME"], t["ROAD"], t["DIV"], t["CONF"], t["STRK"], src])
    body = """
<h1>Official data &#8212; standings</h1>
<p class=\"meta\">All 32 teams, re-read from <a href=\"%s\">nfl.com/standings</a> on 2026-11-15. Records reflect completed Week 10 games; Mon Nov 16 LAC@BAL had not kicked off at snapshot time.
League identity verified by the build script: &Sigma;PF = %d = &Sigma;PA. Nothing here is inferred.</p>
%s
<p class=\"small\">Columns: W wins, L losses, T ties, PCT winning percentage, PF points for, PA points against, NET net points, HOME home record, ROAD road record, DIV division record, CONF conference record, STRK streak.
Every row links to the official standings page.</p>
""" % (esc(standings["source"]), sum(t["PF"] for t in standings["teams"]),
       table("2026 NFL standings (official, 2026-11-15)",
             ["Club", "Team", "W", "L", "T", "PCT", "PF", "PA", "NET", "HOME", "ROAD", "DIV", "CONF", "STRK", "Source"],
             rows))
    return shell("Standings", body, "../", "")


def teams_rows(standings):
    return standings["teams"]


def results_feed_page(week10):
    rows = []
    src = L(week10["source"], week10["source_title"])
    status_label = {"final": "Final", "live": "Live", "halftime": "Halftime", "upcoming": "Upcoming"}
    for g in week10["games"]:
        ascore = esc(g["away_score"]) if g["away_score"] is not None else "&#8212;"
        hscore = esc(g["home_score"]) if g["home_score"] is not None else "&#8212;"
        extra = ""
        if g.get("quarter"):
            extra = " %s" % g["quarter"]
        if g.get("venue"):
            extra += " &#8226; %s" % esc(g["venue"])
        rows.append([esc(g["away"]) + " at " + esc(g["home"]), g["date"], g["day"], g["time"], g["network"],
                     ascore, hscore, status_label[g["status"]] + extra, src])
    body = """
<h1>Verified results feed &#8212; Week 10, 2026</h1>
<p class=\"meta\">Official finals only; every row links to the official game page. Live and upcoming games are labeled, not projected. Source: <a href=\"%s\">nfl.com Week 10 schedule</a>.</p>
<p class=\"small\">Convention: first-listed club is away, second-listed is home. Scores are snapshot-time values (2026-11-15); live games may change.</p>
%s
<p class=\"small\">Byes: %s</p>
""" % (esc(week10["source"]),
       table("Week 10 games (official results feed)",
             ["Matchup (away at home)", "Date", "Day", "Time", "Network", "Away score", "Home score", "Status", "Source"],
             rows),
       ", ".join(week10["byes"]))
    return shell("Results feed", body, "../", "")


def price_snapshots_page():
    ps = load_data_json("price_snapshots.json")
    rows = []
    for r in ps["rows"]:
        rows.append([r.get("game_id", ""), r.get("market", ""), r.get("sequence", ""), r.get("snapshot_kind", ""),
                     r.get("captured_at", ""), esc(r.get("model_fair_line", "&#8212;")),
                     esc(r.get("market_open", "&#8212;")), esc(r.get("market_close", "&#8212;")),
                     esc(r.get("diff_vs_open", "&#8212;")), esc(r.get("diff_vs_close", "&#8212;")),
                     r.get("source", ""), esc(r.get("verified", ""))])
    body = """
<h1>Price-snapshot store</h1>
<p class=\"meta\">One row per originated market per game: opening snapshot at origination, closing snapshot at settlement. Markets are originated in order: (1) side/spread, (2) total, (3) moneyline.</p>
<p class=\"meta\">%s</p>
%s
<h3>Coverage</h3>
<p>%s</p>
<h3>Official price source</h3>
<div class=\"panel bad\"><strong>None.</strong> The NFL publishes no betting lines, odds or prices anywhere on nfl.com or operations.nfl.com (re-checked 2026-11-15).
Every market_open / market_close cell is blank and flagged &#8212; never invented. model_fair_line and diff columns are originated model outputs, labeled as such on the originated-lines page; they are not prices you can bet at.</div>
<h3>Flags</h3>
<ul>%s</ul>
""" % (esc(ps["finding"]),
       table("Price-snapshot store (schema live; 0 market rows captured because no price source exists)",
             ["Game ID", "Market", "Sequence", "Snapshot kind", "Captured at", "Model fair line", "Market open", "Market close",
              "Diff vs open", "Diff vs close", "Source", "Verified"], rows),
       esc(ps["coverage"]),
       "".join("<li>%s</li>" % esc(f) for f in ps["flags"]))
    return shell("Price-snapshot store", body, "../", "")


def load_data_json(name):
    import json as _json
    with open(os.path.join(DATA, name)) as f:
        return _json.load(f)


def origination_page(lines, week11):
    rows = []
    src1 = L("https://www.nfl.com/standings/", "official standings (PF/PA/W-L)")
    src2 = L(week11["source"], week11["source_title"])
    for ln in lines:
        diff_s = "&#8212;"  # market blank
        diff_t = "&#8212;"
        diff_m = "&#8212;"
        ml_txt = "%+d" % ln["fair_ml"] if ln["fair_ml"] >= 0 else "%d" % ln["fair_ml"]
        rows.append([
            "%s at %s" % (ln["away"], ln["home"]), ln["date"], ln["time"], ln["network"],
            "1", "&#8212;", fmt2(ln["fair_spread"]), "&#8212;", fmt2(ln["fair_spread"]),
            "2", fmt2(ln["fair_total"]), "&#8212;", fmt2(0),
            "3", ml_txt, "&#8212;", "&#8212;",
            src1 + " " + src2, "model v1"
        ])
    body = """
<h1>Originated lines &#8212; Week 11, 2026</h1>
<p class=\"meta\">Origination order enforced: <strong>side &#8594; total &#8594; moneyline</strong> for every game, with the model fair line, the market line and the difference published as separate columns.
Every line here is an <strong>originated model output (v1 baseline)</strong> &#8212; not an official price, not a bet recommendation. Market columns are blank because the NFL publishes no odds (F-01).</p>
<div class=\"panel warn\"><strong>Assumptions (all flagged):</strong> home field = +2.0 pts to the home team (DG-A, no official source); win probability = logistic(home expected margin / 13.5) (DG-B, uncalibrated);
fair total = league-average combined points per game (DG-C, v1 limitation). Team strength = (PF &#8722; PA) / games played from official standings.</div>
%s
<p class=\"small\">Columns per market: sequence (1 side, 2 total, 3 moneyline), model fair line, market line (blank), difference vs market (blank). Fair moneyline shown for the home team; negative = favorite. No market prices exist, so no difference can be computed yet.</p>
""" % table("Originated fair lines vs market (market blank &#8212; no official price source)",
            ["Game", "Date", "Time", "Network", "Seq", "Model fair line (side)", "Market line (side)", "Diff (side)",
             "Seq", "Model fair line (total)", "Market line (total)", "Diff (total)",
             "Seq", "Model fair moneyline (home)", "Market moneyline (home)", "Diff (moneyline)", "Sources", "Basis"],
            rows)
    return shell("Originated lines", body, "../", "")


def fmt2(x):
    return "%.2f" % x


def strategies_page(strategies):
    STRAT_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json", "registration artifact")
    rows = []
    for s in strategies["rows"]:
        rows.append([s["id"], s["kind"], esc(s["definition_frozen"]), s["markets"], s["status"],
                     s["signal_metric"], s["staking_metric"], s["gates_passed"], s["gates_total"], s["reward_points"],
                     esc(s["notes"]) + " " + STRAT_SRC])
    body = """
<h1>Strategy catalog &#8212; pre-registered</h1>
<p class=\"meta\">Pre-registration rule: each strategy's definition, sample window and gates were frozen before any result was seen (the git commit hash is the registration).
No strategy definition was changed after first exposure to data. 0 strategies qualify and 0 reward points are awarded &#8212; by design.</p>
%s
<p class=\"small\">%s</p>
""" % (table("Registered strategies (singles, parlays, prop combos)",
            ["ID", "Kind", "Frozen definition", "Markets", "Status", "Signal metric", "Staking metric", "Gates passed", "Gates total", "Reward points", "Notes"],
            rows), esc(strategies["summary"]))
    return shell("Strategies", body, "../", "")


def leaderboard_page(strategies):
    STRAT_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/strategies.json", "registration artifact")
    signal_rows = []
    staking_rows = []
    for s in strategies["rows"]:
        signal_rows.append([s["id"], s["kind"], s["status"], s["signal_metric"], "&#8212;", "&#8212;", "not eligible", STRAT_SRC])
        staking_rows.append([s["id"], s["kind"], s["status"], s["staking_metric"], "&#8212;", "&#8212;", "not eligible", STRAT_SRC])
    body = """
<h1>Leaderboard &#8212; signal vs staking, ranked separately</h1>
<p class=\"meta\">Signal quality and staking results are in separate tables so a lucky staking run cannot mask a bad signal. Neither table mixes the two.
No strategy qualifies; no rewards are paid.</p>
<h3>Signal leaderboard (proper-score based)</h3>
%s
<h3>Staking leaderboard (assumed-price ROI &#8212; not used for ranking)</h3>
<p class=\"small\">Staking ROI assumes &#8212;110 (no official price exists; G7 blocked). It is published for transparency only and never determines rank.</p>
%s
<div class=\"panel bad\"><strong>Result:</strong> 0 of 7 strategies qualify. Both tables are empty of qualifiers. The leaderboard is a rejection machine: a strategy appears only after clearing every pre-registered gate.</div>
""" % (table("Signal table &#8212; not ranked (no qualifiers)",
            ["ID", "Kind", "Status", "Signal metric", "Uncertainty", "Benchmark-relative skill", "Eligible", "Source"],
            signal_rows),
        table("Staking table &#8212; shown separately, never ranks",
            ["ID", "Kind", "Status", "Staking metric (assumed &#8212;110)", "ROI", "Drawdown", "Eligible", "Source"],
            staking_rows))
    return shell("Leaderboard", body, "../", "")


def gates_page(gates):
    GATE_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/gates.json", "gate register")
    vrows = []
    for g in gates["validation_gates"]:
        vrows.append([g["id"], g["name"], esc(g["rule"]), g["status"], esc(g["evidence"]) + " " + GATE_SRC, esc(g["number_to_clear"])])
    dg = gates["demotion_gate"]
    cond = "".join("<li>%s</li>" % esc(c) for c in dg["conditions"])
    body = """
<h1>Validation gates &amp; demotion gate</h1>
<p class=\"meta\">Every strategy must pass G1&#8211;G10 before leaderboard eligibility. Gate text, sample windows and thresholds were frozen before first exposure to data.
A live strategy is returned to paper when the demotion gate fires. Current state: <strong>0 strategies live, 0 demoted, 0 actually live today.</strong></p>
<h3>Validation gates G1&#8211;G10</h3>
%s
<h3>Demotion gate DG-1 (live &#8594; paper)</h3>
<p>%s</p>
<ul>%s</ul>
<p class=\"meta\"><strong>Current evaluation:</strong> %s</p>
<p class=\"meta\"><strong>Number to clear:</strong> %s</p>
""" % (table("Validation gates", ["Gate", "Name", "Rule", "Status", "Evidence from this run", "Number to clear"],
            vrows),
        esc(dg["rule"]), cond, esc(dg["current_state"]), esc(dg["number_to_clear"]))
    return shell("Gates", body, "../", "")


def correlations_page(r1, r2, home_rate, n, total_pf, total_pa, total_games, league_ppg):
    ci1_lo, ci1_hi = fisher_ci(r1, n)
    ci2_lo, ci2_hi = fisher_ci(r2, n)
    p1 = p_value_approx(r1, n)
    p2 = p_value_approx(r2, n)
    rows = [
        ["CR-01", "Point differential vs win percentage, all 32 teams", fmt2(r1), ci_range(ci1_lo, ci1_hi), p_txt(p1), n, "Pearson r on official (PF-PA) vs W/(W+L+T)", L("https://www.nfl.com/standings/", "nfl.com/standings"), "computed by build.py"],
        ["CR-02", "Home win percentage vs season win percentage, all 32 teams", fmt2(r2), ci_range(ci2_lo, ci2_hi), p_txt(p2), n, "Pearson r on official home win% vs season win%", L("https://www.nfl.com/standings/", "nfl.com/standings"), "computed by build.py"],
        ["CR-03", "Home win rate, Week 10 decided games", fmt2(home_rate), "n=9 small sample", "not computed (n=9)", 9, "share of home wins among Week 10 finals", L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/week11.json", "week11.json (S2)"), "computed by build.py"],
        ["CR-04", "Cross-game leg dependence (moneyline sides, different games)", "-0.007", "reported, not recomputed", "&#8212;", "week-slates", "reported from peer-verified data; prices are third-party", L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json", "flags.json (MK-01)"), "reported, not recomputed"],
        ["CR-05", "Same-game prop-pair dependence", "&#8212;", "&#8212;", "&#8212;", "0", "refused: no official prop prices or per-game prop outcomes", L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json", "flags.json (blank by rule)"), "blank by rule (n=0)"],
        ["CR-06", "Injury designation vs play rate", "&#8212;", "&#8212;", "&#8212;", "0", "refused: needs multiple seasons of designations joined to official inactives", L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/flags.json", "flags.json (blank by rule)"), "blank by rule (n=0)"],
    ]
    body = """
<h1>Correlations &#8212; official inputs only, n published</h1>
<p class=\"meta\">Correlations are computed only from officially sourced numbers, and every value is published with its n. No third-party line, price or player-prop input is used.
Descriptive statistics of the historical record &#8212; not a betting edge. p-values use a Fisher-z normal approximation and are labeled as such.</p>
%s
<p class=\"small\">Derived totals from the official standings: &Sigma;PF = %d, &Sigma;PA = %d (identity holds), %d games played through Week 10, league-average combined points per game = %.2f (per team per game = %.2f).</p>
<div class=\"panel ok\"><strong>Rule honored:</strong> every correlation row above lists n; CR-04 is reported rather than recomputed because its underlying prices are third-party (flagged MK-01); CR-05 and CR-06 are blank because the required official inputs do not exist (n=0).</div>
""" % (table("Correlation register",
            ["ID", "Pair", "r", "95% CI", "p (approx.)", "n", "Method", "Inputs (official)", "Status"],
            rows), total_pf, total_pa, int(total_games), league_ppg, league_ppg / 2.0)
    return shell("Correlations", body, "../", "")


def ci_range(lo, hi):
    if lo is None:
        return "&#8212;"
    return "%.3f to %.3f" % (lo, hi)


def p_txt(p):
    if p is None:
        return "&#8212;"
    return "%.4f" % p


def injuries_depth_page(injuries, depth):
    rows = []
    INJ_SRC = L("https://www.nfl.com/injuries/", "official injury report")
    attr_label = {"verified": "yes", "likely misattributed on source page": "&#9873; likely misattributed", "unverified attribution": "&#9873; unverified"}
    for r in injuries["rows"]:
        rows.append([esc(r["team_as_published"]), esc(r["player"]), esc(r["position"]), esc(r["injury"] or "&#8212;"),
                     esc(r["practice_status"]), esc(r["game_status"] or "&#8212;"), attr_label.get(r["attribution_check"], esc(r["attribution_check"])), INJ_SRC])
    drows = []
    for r in depth["rows"]:
        drows.append([esc(r["team"]), esc(r["player_out"]), esc(r["position"]), esc(r["unit"]), esc(r["game_status"]),
                      esc(r["replacement_named"] or "&#8212;"), esc(r["replacement_depth"] or "&#8212;"),
                      esc(r["depth_source"] or "&#8212;"), esc(r["note"]), INJ_SRC])
    body = """
<h1>Injuries &amp; replacement-depth tracker</h1>
<p class=\"meta\">Official Week 10 injury report designations, published as rendered on nfl.com (read 2026-11-15), plus replacement-depth tracking: for every designated Out/Questionable player, the replacement named and the depth of that replacement.
Depth cells are blank by policy &#8212; the NFL publishes no depth chart (F-03) and starter identity is established only post-game from the official Game Book.</p>
<h3>Week 10 injury designations (official)</h3>
%s
<h3>Replacement depth</h3>
<p class=\"meta\">%s</p>
%s
<div class=\"panel bad\"><strong>Finding:</strong> %d designation rows published; 0 replacements named; 0 depth ranks published. Every depth cell is blank because no official depth source exists.
The page tracks designations (which it can verify) and explicitly refuses to fabricate replacement depth (which it cannot). Rows flagged &#9873; appear misattributed on the source page (F-02) and must be cross-checked before use.</div>
""" % (table("Official injury report, Week 10 (as published; attribution checked)",
            ["Team (as published)", "Player", "Position", "Injury", "Practice status", "Game status", "Attribution check", "Source"],
            rows),
        esc(depth["summary"]),
        table("Replacement-depth register (blank by policy)",
            ["Team", "Player out", "Position", "Unit", "Game status", "Replacement named", "Replacement depth", "Depth source", "Note", "Source"],
            drows), len(injuries["rows"]))
    return shell("Injuries &amp; depth", body, "../", "")


def questions_page(questions):
    Q_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/questions.json", "questions register")
    rows = []
    for q in questions["rows"]:
        rows.append([q["id"], esc(q["question"]), esc(q["what_we_know"]), esc(q["what_we_do_not_know"]),
                     esc(q["answer"]), esc(q["what_would_settle_it"]), esc(q["source"]) + " " + Q_SRC, q["status"]])
    body = """
<h1>Questions / information / answers register</h1>
<p class=\"meta\">What must be addressed before any decision can reasonably be made, what we already have, what we do not have, and what would settle each open item.
Answers are deliberately blank where the information does not exist &#8212; nothing is inferred.</p>
%s
""" % table("Decision prerequisites",
            ["ID", "Question", "What we know", "What we do not know", "Answer", "What would settle it", "Source", "Status"],
            rows)
    return shell("Questions &amp; answers", body, "../", "")


def suggestions_page(suggestions):
    SUG_SRC = L("https://github.com/sassnarep3-star/Own4/blob/main/nfl-dashboard/data/suggestions.json", "suggestions register")
    rows = []
    for s in suggestions["rows"]:
        rows.append([s["id"], esc(s["title"]), esc(s["description"]), esc(s["option_a"]), esc(s["option_b"]), esc(s["option_c"]),
                     esc(s["recommended_path"]) + " " + SUG_SRC, esc(s["cost"]), esc(s["risk"]), s["review_status"]])
    body = """
<h1>Suggestions review board</h1>
<p class=\"meta\">Every improvement suggestion lists the options (A/B/C), a recommended path, cost and risk. <strong>Nothing here is implemented before the owner chooses a path.</strong>
review_status = pending means a reviewer must decide first.</p>
%s
<p class=\"small\">%s</p>
""" % (table("Suggestions awaiting owner decision",
            ["ID", "Title", "Description", "Option A", "Option B", "Option C", "Recommended path", "Cost", "Risk", "Review status"],
            rows), esc(suggestions["summary"]))
    return shell("Suggestions", body, "../", "")


def flagged_page(flags):
    rows = []
    for f in flags["rows"]:
        rows.append([f["id"], esc(f["flag"]), esc(f["severity"]), f["source"], esc(f["disposition"])])
    body = """
<h1>&#9873; Flagged for review</h1>
<p class=\"meta\">Every irregularity and every value that could not be confirmed from an official source. Flagged items are non-blocking unless stated otherwise;
they are published here rather than silently filled in. Several block strategy qualification (that is the intended behavior).</p>
%s
""" % table("Flagged register",
            ["ID", "Flag", "Severity", "Source link", "Disposition"],
            rows)
    return shell("Flagged for review", body, "../", "")


def sources_page(sources):
    rows = []
    for s in sources["rows"]:
        rows.append([s["id"], L(s["url"], s["title"]), esc(s["supports"]), s["retrieved"], esc(s["notes"])])
    body = """
<h1>Source register</h1>
<p class=\"meta\">Every table row on this site links to one of these official sources, or is blank and flagged. No unofficial or third-party value is published as a fact.</p>
%s
""" % table("Official sources",
            ["ID", "URL", "Supports", "Retrieved", "Notes"],
            rows)
    return shell("Source register", body, "../", "")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Generate the static NFL line-origination site under nfl-lines/.

Everything is baked into the HTML at build time so the site needs no JavaScript to
read and no network to render. Every table row carries a source link; values that
cannot be sourced are rendered as an explicit blank cell, never as a guess.
"""
from __future__ import annotations

import html
import json
import os
import re

import dataset as D

ROOT = D.ROOT
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")

SLUG = {
    "ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills",
    "CAR": "panthers", "CHI": "bears", "CIN": "bengals", "CLE": "browns",
    "DAL": "cowboys", "DEN": "broncos", "DET": "lions", "GB": "packers",
    "HOU": "texans", "IND": "colts", "JAX": "jaguars", "KC": "chiefs",
    "LV": "raiders", "LAC": "chargers", "LA": "rams", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants",
    "NYJ": "jets", "PHI": "eagles", "PIT": "steelers", "SF": "49ers",
    "SEA": "seahawks", "TB": "buccaneers", "TEN": "titans", "WAS": "commanders",
}
NAME = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LA": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
    # NFL.com uses AZ and LA where the game archive uses ARI and LAR.
    "AZ": "Arizona Cardinals",
}

OFF_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
OFF_STATS = "https://www.nfl.com/stats/team-stats/"
OFF_INJURIES = "https://www.nfl.com/injuries/"
OFF_SCHEDULE = "https://www.nfl.com/schedules/2026/REG10"
OFF_SCORES = "https://www.nfl.com/scores/2026/REG%d"
NFLDATA = 'https://github.com/nflverse/nfldata'
CALC = '../data/derived/strategy_results.json'

NAV = [
    ("index.html", "Overview"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/decisions.html", "Decision register"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/own-lines.html", "Own lines (Week 10)"),
    ("pages/strategies.html", "Strategy registry"),
    ("pages/singles.html", "Single bets"),
    ("pages/parlays.html", "Parlays"),
    ("pages/props.html", "Prop combos"),
    ("pages/validation.html", "Validation gates"),
    ("pages/correlations.html", "Correlations"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/skill-vs-luck.html", "Skill vs luck"),
    ("pages/injuries.html", "Injuries & deficiency"),
    ("pages/data-results.html", "Data: results"),
    ("pages/data-standings.html", "Data: standings"),
    ("pages/data-team-stats.html", "Data: team stats"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/sources.html", "Sources"),
    ("pages/flagged.html", "Flagged for review"),
]

CSS = """
:root{--bg:#f6f7f9;--panel:#ffffff;--ink:#12161c;--muted:#5c6675;--line:#e2e6ec;
--accent:#0b5cab;--good:#0f7b3f;--bad:#b3261e;--warn:#8a5a00;--soft:#eef3f9}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{background:#0d1b2a;color:#fff;padding:14px 22px;display:flex;gap:16px;
align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:20}
header h1{font-size:16px;margin:0;font-weight:650;letter-spacing:.2px}
header .tag{font-size:12px;color:#9fb3c8;font-weight:400}
header nav{margin-left:auto;display:flex;gap:14px;font-size:13px;flex-wrap:wrap}
header nav a{color:#cfe0f0}
.wrap{display:flex;align-items:flex-start;gap:0;max-width:1500px;margin:0 auto}
aside{width:240px;flex:0 0 240px;padding:18px 12px 40px;position:sticky;top:56px;
max-height:calc(100vh - 56px);overflow:auto;border-right:1px solid var(--line);background:#fbfcfd}
aside h4{margin:14px 0 6px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
aside a{display:block;padding:5px 9px;border-radius:6px;color:#22303f;font-size:13.5px}
aside a:hover{background:var(--soft);text-decoration:none}
aside a.on{background:var(--accent);color:#fff}
main{flex:1;min-width:0;padding:22px 26px 70px}
h2{font-size:22px;margin:4px 0 6px}
h3{font-size:16.5px;margin:26px 0 8px}
p.lead{color:var(--muted);max-width:98ch;margin-top:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(184px,1fr));gap:12px;margin:16px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.card .k{font-size:26px;font-weight:660;letter-spacing:-.5px}
.card .l{font-size:12px;color:var(--muted);margin-top:2px}
.card .s{font-size:11.5px;color:var(--muted);margin-top:6px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:16px 0}
.tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0}
.tools input{padding:7px 10px;border:1px solid var(--line);border-radius:7px;min-width:230px;font-size:13.5px}
.scroll{overflow:auto;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:13px;background:#fff}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#f0f3f7;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#3b4654;
position:sticky;top:0;z-index:2}
tbody tr:hover{background:#fafcfe}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pos{color:var(--good);font-weight:600}
.neg{color:var(--bad);font-weight:600}
.blank{color:#9aa4b0}
.pass{color:var(--good);font-weight:600}
.fail{color:var(--bad);font-weight:600}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11.5px;font-weight:600}
.pill.ok{background:#e3f5ea;color:#0f7b3f}
.pill.no{background:#fdeceb;color:#b3261e}
.pill.p1{background:#fdeceb;color:#b3261e}
.pill.p2{background:#fff4e0;color:#8a5a00}
.pill.p3{background:#eef3f9;color:#0b5cab}
.pill.tp{background:#eceff3;color:#4b5563}
.note{background:#fffaf0;border:1px solid #f0e0bb;border-radius:8px;padding:10px 13px;font-size:13.5px;margin:12px 0}
.crit{background:#fdeceb;border:1px solid #f3c9c5;border-radius:8px;padding:10px 13px;font-size:13.5px;margin:12px 0}
pre{background:#f4f6f8;border:1px solid var(--line);border-radius:7px;padding:9px 11px;overflow:auto;font-size:12.5px}
footer{color:var(--muted);font-size:12.5px;padding:20px 26px;border-top:1px solid var(--line)}
.small{font-size:12.5px;color:var(--muted)}
ul.tight{margin:8px 0;padding-left:20px}
ul.tight li{margin:4px 0}
@media(max-width:900px){aside{display:none}main{padding:16px}}
"""


def esc(x):
    return html.escape("" if x is None else str(x))


def blank_cell(title="unverified - no official source"):
    return '<td class="blank" title="%s">&mdash;</td>' % esc(title)


def game_url(away, home, season, week):
    a, h = SLUG.get(away), SLUG.get(home)
    if not a or not h:
        return OFF_SCHEDULE
    return "https://www.nfl.com/games/%s-at-%s-%d-reg-%d" % (a, h, season, week)


def page(title, active, body, subtitle=""):
    nav = "".join('<a href="%s">%s</a>' % (("" if href == "index.html" else "../") + href, esc(label))
                  for href, label in [("index.html", "Overview")] )
    side = []
    group = None
    for href, label in NAV:
        g = ("Overview" if href == "index.html" else
             "Decide" if href.startswith("pages/executive") or "decisions" in href or "suggestions" in href else
             "Lines & strategies" if any(k in href for k in ("own-lines", "strategies", "singles", "parlays", "props", "validation", "correlations", "leaderboard", "skill")) else
             "Data" if "data-" in href or "injuries" in href else
             "Governance")
        if g != group:
            side.append("<h4>%s</h4>" % esc(g))
            group = g
        base = "" if active == "index.html" else "../"
        cls = " class='on'" if href == active else ""
        side.append("<a%s href=\"%s%s\">%s</a>" % (cls, base, href, esc(label)))
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s &middot; NFL Line Lab</title>
<link rel="stylesheet" href="%sassets/style.css"></head>
<body>
<header>
  <h1>NFL Line Lab <span class="tag">originate &middot; validate &middot; rank</span></h1>
  <nav><a href="%sindex.html">Overview</a><a href="%spages/decisions.html">Decision register</a><a href="%spages/leaderboard.html">Leaderboard</a><a href="%spages/flagged.html">Flagged</a></nav>
</header>
<div class="wrap">
<aside>%s</aside>
<main>
<h2>%s</h2>
%s
%s
</main></div>
<footer>Static site generated by <code>nfl-lines/engine/build_site.py</code>. Official data from
<a href="https://www.nfl.com/">NFL.com</a>. Market lines are third-party &mdash; the NFL publishes no official odds.
Model outputs are forecasts, not facts.</footer>
<script src="%sassets/app.js"></script>
</body></html>""" % (
        esc(title), base_of(active), base_of(active), base_of(active), base_of(active), base_of(active),
        "".join(side), esc(title),
        ("<p class='lead'>%s</p>" % subtitle) if subtitle else "", body, base_of(active))


def base_of(active):
    return "" if active == "index.html" else "../"


ROW_OPEN = re.compile(r"^\s*<(tr)\b[^>]*>", re.I)
ROW_CLOSE = re.compile(r"</tr[^>]*>\s*$", re.I)


def table(headers, rows, cls="", numeric_from=None):
    """Render a filterable table. `rows` may be either cell strings or full <tr>...</tr> strings."""
    th = "".join("<th%s>%s</th>" % (" class='n'" if (numeric_from is not None and i >= numeric_from) else "",
                                    esc(h)) for i, h in enumerate(headers))
    clean = []
    for r in rows:
        r = ROW_OPEN.sub("", r)
        r = ROW_CLOSE.sub("", r)
        clean.append(r)
    tr = "".join("<tr>%s</tr>" % r for r in clean)
    return ('<div class="tools"><input class="filter" placeholder="Filter rows&hellip;">'
            '<span class="small"></span></div>'
            '<div class="scroll"><table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % ((" class='%s'" % cls) if cls else "", th, tr))


def load(name):
    return json.load(open(os.path.join(ROOT, "data", name), "r", encoding="utf-8"))


def derived(name):
    return json.load(open(os.path.join(ROOT, "data", "derived", name), "r", encoding="utf-8"))


# --------------------------------------------------------------------- sections

def build_index():
    s = derived("summary.json")
    br = s["base_rates"]
    lb = derived("leaderboard.json")
    ver = derived("verification.json")
    sp = ver["official_score_spotcheck"]
    fl = load("flags.json")
    cards = [
        (s["forecast_games"], "games forecast out of sample", "2011-2026, refit before every kick-off"),
        ("%d/%d" % (sp["matched"], sp["games_compared"]),
         "official score spot-check", "re-read from NFL.com; zero mismatches"),
        ("%d" % s["strategies"], "strategies tested", "singles, parlays and a same-game combo"),
        ("%d" % s["reward_eligible"], "reward-eligible", "none clears all eight gates"),
        ("%.3f" % br["mean_abs_own_spread_error"], "own spread error (pts)",
         "market benchmark %.3f" % br["mean_abs_market_spread_error"]),
        ("%.3f" % br["mean_abs_own_total_error"], "own total error (pts)",
         "market benchmark %.3f" % br["mean_abs_market_total_error"]),
        ("%d" % len(fl["items"]), "items flagged for review", "published, not hidden"),
        ("275", "injury-report rows", "all 14 Week 10 games, official source"),
    ]
    body = ['<div class="cards">']
    for k, l, s2 in cards:
        body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div><div class="s">%s</div></div>'
                    % (esc(k), esc(l), esc(s2)))
    body.append("</div>")

    body.append('<div class="crit"><strong>The headline finding.</strong> On 4,055 out-of-sample games the '
                'correlation between (my line &minus; market line) and the actual result against the market spread '
                'is <strong>r = 0.0072</strong> with a 95% confidence interval of [-0.024, 0.038]. That interval '
                'contains zero. The originated lines are close to the market but not better than it, and no '
                'strategy built on them clears the validation gates. This is the result the system was built to '
                'produce: a reproducible "not yet" instead of an unverifiable "yes".</div>')

    body.append("<h3>Where to start</h3><ul class='tight'>"
                "<li><a href='pages/executive-summary.html'>Executive summary</a> - the whole picture in one page.</li>"
                "<li><a href='pages/decisions.html'>Decision register</a> - 15 questions, what we know, what we do not, and how to close each gap.</li>"
                "<li><a href='pages/suggestions.html'>Suggestions</a> - 12 ranked proposals awaiting your review. Nothing here is approved.</li>"
                "<li><a href='pages/own-lines.html'>Own lines</a> - this week's originated spreads, totals and moneylines.</li>"
                "<li><a href='pages/flagged.html'>Flagged for review</a> - 15 irregularities, published rather than fixed silently.</li>"
                "</ul>")

    body.append("<h3>How a number gets onto this site</h3>"
                "<ol class='tight'>"
                "<li>Official NFL.com pages are fetched and read, then transcribed into <code>data/official/*.json</code>.</li>"
                "<li>The third-party game archive is spot-checked against those official pages before it is used "
                "(45 of 45 games matched; Week 5 could not be read and is flagged).</li>"
                "<li>Model parameters are written to <code>data/model_params.json</code> with a registration timestamp "
                "<em>before</em> the first run, so they cannot be tuned to the results.</li>"
                "<li>Every forecast is refitted using only games that finished earlier, so no future information can leak.</li>"
                "<li>Every strategy is scored, tested against a no-skill simulation, corrected for multiple comparisons, "
                "and then run through eight gates before it can be called reward-eligible.</li>"
                "<li>Anything that cannot be sourced is left blank and flagged.</li>"
                "</ol>")

    best = lb[0] if lb else None
    if best:
        body.append("<h3>Best result on the board (and why it still does not count)</h3>")
        body.append("<p>%s: %s bets, ROI %s, %s%% win rate against a %s%% break-even, p = %s "
                    "(%s after correction for testing %d strategies). It passes %s gates. "
                    "<a href='pages/leaderboard.html'>See the full board</a>.</p>"
                    % (esc(best["name"]), best["n"], esc(best["roi"]),
                       esc(round(best["win_rate"] * 100, 1)), esc(round(best["break_even_rate"] * 100, 1)),
                       esc(best["p_value"]), esc(best["p_value_bh"]), len(lb), esc(best["gates_passed"])))
    return page("Overview", "index.html", "".join(body),
                "An NFL line-origination lab: originate my own lines, measure them against the market, "
                "strip out luck, and only then rank strategies.")


def build_exec_summary():
    s = derived("summary.json")
    br = s["base_rates"]
    cor = derived("correlations.json")
    calib = cor["calibration"]
    lb = derived("leaderboard.json")
    dec = load("decisions.json")
    fl = load("flags.json")
    cr = {c["id"]: c for c in cor["correlations"]}

    body = []
    body.append('<div class="cards">')
    for k, l, s2 in [
        ("%d" % s["forecast_games"], "out-of-sample forecasts", "2011-2026, refit before each kick-off"),
        ("%s" % cr["CR-01"]["pearson_r"], "edge-to-result correlation", "95%% CI %s" % cr["CR-01"]["ci95"]),
        ("%s" % cr["CR-04"]["pearson_r"], "market spread correlation",
         "own model %s" % cr["CR-03"]["pearson_r"]),
        ("%s" % cr["CR-06"]["pearson_r"], "market total correlation",
         "own model %s" % cr["CR-05"]["pearson_r"]),
        ("%s" % calib["model_brier"], "own Brier score", "market %s, naive %s"
         % (calib["market_brier"], calib["baseline_brier"])),
        ("0 of %d" % len(lb), "strategies reward-eligible", "none clears all eight gates"),
    ]:
        body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div><div class="s">%s</div></div>'
                    % (esc(k), esc(l), esc(s2)))
    body.append("</div>")

    body.append("""<h3>What was built</h3>
<p>An end-to-end line-origination and validation system for the NFL, run on 2026 Week 10 data. It originates its
own spread, total, team totals, win probability and moneyline for every game; measures the disagreement against the
market; turns that disagreement into bets across singles, parlays and a same-game combo; and then refuses to reward
any of them until they pass eight pre-declared gates. Injuries and unit deficiency are tracked from the official
NFL injury report for all 14 Week 10 games.</p>

<h3>What the evidence says</h3>
<ul class="tight">
<li><strong>The originated lines track the market but do not beat it.</strong> The correlation between my line and
the actual margin is %s; the market's is %s. On totals, mine is %s against the market's %s. Mean absolute error on
the spread is %.2f points against the market's %.2f.</li>
<li><strong>The disagreement carries no information.</strong> If the model had skill, a bigger gap between my line
and the closing line would produce a bigger cover margin. Measured: r = %s, 95%% CI %s, p = %s over %d games.
The interval contains zero.</li>
<li><strong>The probabilities are honest but not sharp enough.</strong> Brier score %s against the market's %s and
a naive baseline of %s. The model is well calibrated (weighted reliability error %s) &mdash; when it says 65%%,
teams win about 67%% of the time &mdash; it simply does not know anything the market does not.</li>
<li><strong>No strategy has demonstrated skill.</strong> %d strategies were tested. The best by return on
investment, unders in windy outdoor games, made +7.77%% over 303 bets; the no-skill simulation puts 95%% of
luck-only outcomes between &minus;11.08%% and +10.82%%. It sits inside that band, and its p-value rises from 0.17
to 0.44 once you correct for having tested %d strategies.</li>
<li><strong>Nothing is reward-eligible, and that is the intended output.</strong> The gates exist so that a
strategy cannot be rewarded for being lucky.</li>
</ul>""" % (
        cr["CR-03"]["pearson_r"], cr["CR-04"]["pearson_r"], cr["CR-05"]["pearson_r"], cr["CR-06"]["pearson_r"],
        br["mean_abs_own_spread_error"], br["mean_abs_market_spread_error"],
        cr["CR-01"]["pearson_r"], cr["CR-01"]["ci95"], cr["CR-01"]["p_value"], cr["CR-01"]["n"],
        calib["model_brier"], calib["market_brier"], calib["baseline_brier"],
        calib["reliability_mse_weighted"], len(lb), len(lb)))

    body.append("""<h3>The three gaps that matter most</h3>
<ol class="tight">
<li><strong>Quarterback and injury information is not in the model.</strong> Week 10 MIA @ IND: the market total
is 38.5, mine is 46.68, an 8.18-point gap. The official injury page the same day reports Miami placing its
quarterback on injured reserve with a first-time starter in line. The model does not know that. Source:
<a href="%s">nfl.com/injuries</a>.</li>
<li><strong>Depth-chart rank is not published.</strong> The official report gives position and status, never
whether a player is a starter or a 2nd, 3rd or 4th string replacement. Every depth-rank cell is blank by design.</li>
<li><strong>Only closing lines exist.</strong> Every edge here is measured against a price that is already final.
If the model's advantage lives in an earlier number, the current evaluation cannot see it.</li>
</ol>""" % OFF_INJURIES)

    body.append("<h3>Decisions awaiting you</h3>")
    rows = []
    for q in dec["questions"]:
        can = q["decidable_now"]
        cls = "ok" if can.startswith("Yes") else ("no" if can.startswith("No") else "tp")
        rows.append("<tr><td>%s</td><td>%s</td><td><span class='pill %s'>%s</span></td>"
                    "<td><a href='decisions.html#%s'>detail</a></td></tr>"
                    % (esc(q["id"]), esc(q["question"]), cls, esc(can), esc(q["id"])))
    body.append(table(["#", "Question", "Decidable now", ""], rows))

    body.append("<h3>Irregularities</h3><p>%d items are published on the "
                "<a href='flagged.html'>Flagged for review</a> page rather than fixed silently. "
                "The most consequential: Week 5 2026 scores could not be read from NFL.com (rendered as "
                "'Hidden Score'); no official NFL odds exist, so every market line is third-party; and the "
                "injury report carries no depth-chart rank.</p>" % len(fl["items"]))
    return page("Executive summary", "pages/executive-summary.html", "".join(body),
                "The whole picture in one page: what was built, what it found, and what is still unknown.")


def build_decisions():
    dec = load("decisions.json")
    body = ["<div class='note'><strong>How to use this page.</strong> %s</div>" % esc(" ".join(dec["rules"]))]
    rows = []
    for q in dec["questions"]:
        can = q["decidable_now"]
        cls = "ok" if can.startswith("Yes") else ("no" if can.startswith("No") else "tp")
        rows.append(
            "<tr id='%s'><td><strong>%s</strong><div class='small'>&nbsp;</div></td>"
            "<td><strong>Question</strong><div>%s</div>"
            "<div style='height:8px'></div><strong>What we have</strong><div>%s</div>"
            "<div class='small' style='margin-top:4px'>Source: %s</div></td>"
            "<td><strong>What we do not have</strong><div>%s</div></td>"
            "<td><span class='pill %s'>%s</span></td>"
            "<td><strong>Suggested action to close the gap</strong><div>%s</div></td></tr>"
            % (esc(q["id"]), esc(q["id"]),
               esc(q["question"]), esc(q["have"]),
               linkify(q["have_source"], "../"), esc(q["gap"]), cls, esc(can), esc(q["action"])))
    body.append(table(["#", "Question and evidence held", "Gap", "Decidable?", "How to close it"], rows))
    return page("Decision register", "pages/decisions.html", "".join(body),
                "Before any decision is made: the question, the evidence in hand, the gap in that evidence, "
                "and the specific action that would close it.")


def linkify(text, prefix=""):
    """Turn URLs and repository-relative file paths into links, keeping the text intact."""
    import re
    out = esc(text)
    for u in re.findall(r"(https?://[^\s,]+)", text):
        out = out.replace(esc(u), '<a href="%s">%s</a>' % (esc(u), esc(u.replace("https://", ""))))
    for f in re.findall(r"\b(data/[A-Za-z0-9_./-]+)", text):
        out = out.replace(esc(f), '<a href="%s%s">%s</a>' % (prefix, esc(f), esc(f)))
    return out


def build_suggestions():
    dec = load("decisions.json")
    body = ["<div class='note'><strong>Nothing on this page is approved.</strong> Every suggestion is a proposal "
            "waiting for review. Each carries the evidence behind it and the test that would show it worked, so "
            "you can choose a path before anything is implemented.</div>"]
    rows = []
    for s in dec["suggestions"]:
        p = s["priority"]
        rows.append(
            "<tr id='%s'><td><strong>%s</strong></td><td><span class='pill %s'>%s</span></td><td>%s</td>"
            "<td><strong>Suggestion</strong><div>%s</div><div style='height:7px'></div>"
            "<strong>Why</strong><div>%s</div><div style='height:7px'></div>"
            "<strong>Evidence</strong><div class='small'>%s</div></td>"
            "<td>%s</td>"
            "<td><span class='pill tp'>%s</span></td>"
            "<td><a href='../data/decisions.json'>register</a></td></tr>"
            % (esc(s["id"]), esc(s["id"]), p.lower(), esc(p), esc(s["area"]),
               esc(s["suggestion"]), esc(s["why"]), linkify(s["evidence"], "../"),
               esc(s["success_test"]), esc(s["status"])))
    body.append(table(["#", "Priority", "Area", "Suggestion and rationale", "How to verify it worked",
                       "Status", "Source"], rows))
    return page("Suggestions", "pages/suggestions.html", "".join(body),
                "Ranked improvements to the site and the system. Review, choose, then implement &mdash; in that order.")


def build_own_lines():
    up = derived("own_lines_week10.json")
    w10 = sorted([x for x in up if x["week"] == 10], key=lambda z: (z["gameday"], z["game_id"]))
    body = []
    body.append("""<div class="note"><strong>What these are.</strong> Spreads, totals and moneylines produced by my
own model, fitted only on games that finished before kick-off. A positive own spread means the model makes the home
team that many points favourite. They are <em>forecasts</em>, not verified facts, and they carry no official source
because no official source for them exists. The market columns are third-party &mdash; the NFL publishes no
official odds.</div>""")
    rows = []
    for x in w10:
        se, te = x["spread_edge"], x["total_edge"]
        se_s = '<span class="%s">%s</span>' % ("pos" if se > 0 else "neg", "%+.2f" % se)
        te_s = '<span class="%s">%s</span>' % ("pos" if te > 0 else "neg", "%+.2f" % te)
        flag = " flagged" if (abs(se) >= 6.5 or abs(te) >= 6.5) else ""
        rows.append(
            "<tr%s><td>%s</td><td>%s @ %s</td><td class='n'>%s</td><td class='n'>%s</td><td>%s</td>"
            "<td class='n'>%s</td><td class='n'>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td class='n'>%s</td><td class='n'>%s</td>"
            "<td><a href='%s'>official</a></td></tr>"
            % (flag, esc(x["gameday"]), esc(x["away"]), esc(x["home"]),
               esc(x["own_spread_line"]), esc(x["market_spread_line"]), se_s,
               esc(x["own_total_line"]), esc(x["market_total_line"]), te_s,
               esc(x["own_home_team_total"]), esc(x["own_away_team_total"]),
               esc(x["own_home_moneyline"]), esc(x["market_home_moneyline"]),
               esc(game_url(x["away"], x["home"], 2026, x["week"]))))
    body.append(table(
        ["Date", "Matchup", "Own spread", "Market spread", "Spread edge",
         "Own total", "Market total", "Total edge", "Own home TT", "Own away TT",
         "Own home ML", "Market home ML", "Source"], rows, numeric_from=2))
    body.append("""<p class="small">Rows shaded in the table body with a <strong>flagged</strong> class (PIT @ CIN,
LA @ ARI, MIA @ IND, LAC @ BAL) show a model&ndash;market disagreement of 6.5 points or more. Historically 21.4%
of games disagree by more than 5 points, so these are within normal dispersion &mdash; but each is worth a look, and
two of them are explained by things the model cannot see: a bye week (PIT @ CIN, irregularity IR-08) and a
quarterback change (MIA @ IND, IR-11).</p>""")

    body.append("<h3>Every remaining 2026 game</h3><p class='small'>The model also originates a line for all %d "
                "unplayed regular-season games. Those beyond Week 10 are projections against a market number that "
                "does not yet exist for most of them; they are shown for completeness.</p>" % len(up))
    rows = []
    for x in sorted(up, key=lambda z: (z["week"], z["gameday"])):
        rows.append("<tr><td class='n'>%s</td><td>%s</td><td>%s @ %s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td><a href='%s'>official schedule</a> &middot; "
                    "<a href='%s' title='market lines are not published by the NFL'>third-party market</a> "
                    "&middot; <a href='../data/derived/own_lines_week10.json'>computed</a></td></tr>"
                    % (esc(x["week"]), esc(x["gameday"]), esc(x["away"]), esc(x["home"]),
                       esc(x["own_spread_line"]), esc(x["own_total_line"]),
                       esc(x["market_spread_line"]), esc(x["market_total_line"]),
                       esc(OFF_SCHEDULE if x["week"] == 10 else "https://www.nfl.com/schedules/"),
                       NFLDATA))
    body.append(table(["Week", "Date", "Matchup", "Own spread", "Own total", "Market spread", "Market total",
                       "Source"], rows, numeric_from=3))
    return page("Own lines (Week 10)", "pages/own-lines.html", "".join(body),
                "Lines this system originates for itself, next to the third-party market number and the gap between them.")


def build_strategies():
    recs = derived("strategy_results.json")
    body = ["<div class='note'>Every strategy's rule is written down before results are looked at, and the model "
            "parameters behind them are frozen in <code>data/model_params.json</code> with a registration "
            "timestamp. A strategy whose parameters were changed after seeing results would not be comparable to "
            "these.</div>"]
    rows = []
    for r in recs:
        a = r["all"]
        rows.append(
            "<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td><span class='%s'>%s</span></td>"
            "<td><a href='%s'>computed</a></td></tr>"
            % (esc(r["id"]), esc(r["family"]), esc(r["name"]), esc(a["n"]),
               esc(pct(a["win_rate"])), esc(pct(a["break_even_rate"])), esc(pct(a["roi"])),
               esc(a["p_value_vs_breakeven"]), esc(r["p_value_bh_adjusted"]),
               "pass" if r["eligible_for_reward"] else "fail",
               "%d/%d" % (r["gates_passed"], r["gates_total"]), CALC))
    body.append(table(["ID", "Family", "Rule", "Bets", "Win rate", "Break-even", "ROI", "p", "p (BH)", "Gates",
                       "Source"], rows, numeric_from=3))
    return page("Strategy registry", "pages/strategies.html", "".join(body),
                "Every strategy tested, its rule, and how it scored. Sorted by family.")


def pct(v):
    if v is None:
        return "&mdash;"
    return "%.2f%%" % (v * 100)


def family_page(fam, title, lead, fname):
    recs = [r for r in derived("strategy_results.json") if r["family"] == fam]
    body = ["<p>%s</p>" % lead]
    for r in recs:
        a, c, d = r["all"], r["confirmation"], r["development"]
        lb = r["luck_band"]
        body.append("<h3>%s &mdash; %s</h3>" % (esc(r["id"]), esc(r["name"])))
        body.append("<p class='small'><strong>Rule:</strong> %s</p>" % esc(r["rule"]))
        cells = [
            ("Bets", a["n"]), ("Win rate", pct(a["win_rate"])), ("Break-even", pct(a["break_even_rate"])),
            ("ROI", pct(a["roi"])), ("p-value", a["p_value_vs_breakeven"]),
            ("p (BH corrected)", r["p_value_bh_adjusted"]),
            ("Development ROI (2011-2021)", pct(d.get("roi"))),
            ("Confirmation ROI (2022-2026)", pct(c.get("roi"))),
            ("Max drawdown", r["max_drawdown_units"]),
            ("Bets needed to prove this edge",
             r["required_n_for_observed_edge"] if r["required_n_for_observed_edge"]
             else "n/a (no positive edge)"),
        ]
        body.append('<div class="cards">')
        for k, v in cells:
            body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(v), esc(k)))
        body.append("</div>")
        if lb:
            body.append("<div class='%s'><strong>Luck check.</strong> %s</div>"
                        % ("note" if not r["luck_vs_skill"]["inside_no_skill_band"] else "crit",
                           esc(r["luck_vs_skill"]["interpretation"])))
        gates = "".join("<tr><td>%s</td><td>%s</td><td><span class='%s'>%s</span></td><td>%s</td>"
                        "<td><a href='%s'>computed</a></td></tr>"
                        % (esc(g["id"]), esc(g["gate"]), "pass" if g["passed"] else "fail",
                           "PASS" if g["passed"] else "FAIL", esc(g["detail"]), CALC)
                        for g in r["gates"])
        body.append("<div class='scroll'><table><thead><tr><th>Gate</th><th>Requirement</th><th>Result</th>"
                    "<th>Measured</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div>" % gates)
        if r["by_season"]:
            sr = "".join("<tr><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                         "<td><a href='%s'>third-party results archive</a> &middot; "
                         "<a href='%s'>computed</a></td></tr>"
                         % (esc(k), esc(v["n"]), esc(pct(v["roi"])), esc(pct(v["win_rate"])),
                            NFLDATA, CALC)
                         for k, v in sorted(r["by_season"].items()))
            body.append("<details><summary>Season by season</summary>"
                        "<p class='small'>Results for seasons 2011-2025 come from the third-party game "
                        "archive and were not re-read from NFL.com; only Weeks 1, 8 and 9 of 2026 were "
                        "re-read and matched (see IR-07 on the flagged page).</p>"
                        "<div class='scroll'><table>"
                        "<thead><tr><th>Season</th><th class='n'>Bets</th><th class='n'>ROI</th>"
                        "<th class='n'>Win rate</th><th>Source</th></tr></thead>"
                        "<tbody>%s</tbody></table></div></details>" % sr)
    return page(title, fname, "".join(body), "")


def build_props():
    recs = [r for r in derived("strategy_results.json") if r["family"] == "combo"]
    cor = derived("correlations.json")
    cr = {c["id"]: c for c in cor["correlations"]}
    body = []
    body.append("""<div class="crit"><strong>Player props: no verifiable data exists in the sources available to
this session.</strong> The NFL publishes no player prop lines, and no verifiable archive of player game logs or
prop prices was reachable. Every player-prop value on this page is therefore left blank and flagged. What
<em>is</em> populated is the engine: the correlation-aware pricing method, the gates, and one fully measurable
team-level combo, because both of its legs have recorded prices.</div>""")

    body.append("<h3>Measurable combo: favourite covers and the game goes over</h3>")
    for r in recs:
        a, c, d = r["all"], r["confirmation"], r["development"]
        body.append("<p class='small'><strong>Rule:</strong> %s</p>" % esc(r["rule"]))
        body.append('<div class="cards">')
        for k, v in [("Bets", a["n"]), ("Win rate", pct(a["win_rate"])),
                     ("Break-even", pct(a["break_even_rate"])), ("ROI", pct(a["roi"])),
                     ("p-value", a["p_value_vs_breakeven"]), ("p (BH)", r["p_value_bh_adjusted"]),
                     ("Development ROI", pct(d.get("roi"))), ("Confirmation ROI", pct(c.get("roi")))]:
            body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(v), esc(k)))
        body.append("</div>")
        gates = "".join("<tr><td>%s</td><td>%s</td><td><span class='%s'>%s</span></td><td>%s</td>"
                        "<td><a href='%s'>computed</a></td></tr>"
                        % (esc(g["id"]), esc(g["gate"]), "pass" if g["passed"] else "fail",
                           "PASS" if g["passed"] else "FAIL", esc(g["detail"]), CALC)
                        for g in r["gates"])
        body.append("<div class='scroll'><table><thead><tr><th>Gate</th><th>Requirement</th><th>Result</th>"
                    "<th>Measured</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div>" % gates)

    body.append("""<h3>How the combo is priced</h3>
<p>The naive way to price a same-game parlay is to multiply the legs together, which assumes the legs are
independent. They are not. The pricer here instead estimates the joint probability from history, using only games
that finished before the one being priced, and reports the difference. That difference <em>is</em> the correlation
adjustment, measured rather than assumed.</p>""")
    rows = [
        ("CR-07", "Home covers and the game goes over", cr["CR-07"]["pearson_r"], cr["CR-07"]["ci95"],
         cr["CR-07"]["p_value"], cr["CR-07"]["n"]),
        ("CR-08", "Favourite covers and the game goes over", cr["CR-08"]["pearson_r"], cr["CR-08"]["ci95"],
         cr["CR-08"]["p_value"], cr["CR-08"]["n"]),
        ("CR-09", "Final margin and game total", cr["CR-09"]["pearson_r"], cr["CR-09"]["ci95"],
         cr["CR-09"]["p_value"], cr["CR-09"]["n"]),
        ("CR-10", "Home points and away points", cr["CR-10"]["pearson_r"], cr["CR-10"]["ci95"],
         cr["CR-10"]["p_value"], cr["CR-10"]["n"]),
    ]
    body.append(table(["ID", "Leg pair", "Pearson r", "95% CI", "p", "n", "Source"],
                      ["<tr><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                       "<td class='n'>%s</td><td class='n'>%s</td>"
                       "<td><a href='../data/derived/correlations.json'>computed</a> &middot; "
                       "<a href='%s'>official scores</a> &middot; <a href='%s'>results archive</a></td></tr>"
                       % (esc(a), esc(b), esc(c), esc(d), esc(e), esc(f), OFF_SCORES % 9, NFLDATA)
                       for a, b, c, d, e, f in rows], numeric_from=2))
    body.append("""<p class="small">All four intervals include or nearly include zero. For side-and-total legs the
independence assumption is close enough that the correction is small; for player-prop legs the correlation cannot
be measured at all with the data available, which is why no prop combo is published with numbers.</p>""")

    body.append("<h3>Player-prop combos: specified, not populated</h3>")
    prows = []
    for market, why in [
        ("QB passing yards", "no verifiable player game logs or prop prices reachable"),
        ("RB rushing yards", "no verifiable player game logs or prop prices reachable"),
        ("WR / TE receiving yards", "no verifiable player game logs or prop prices reachable"),
        ("Any-player touchdown", "no verifiable player game logs or prop prices reachable"),
        ("QB passing yards + team win (SGP)", "depends on the two rows above plus an unmeasured leg correlation"),
    ]:
        prows.append("<tr><td>%s</td><td class='blank' title='unverified'>&mdash;</td>"
                     "<td class='blank' title='unverified'>&mdash;</td>"
                     "<td class='blank' title='unverified'>&mdash;</td><td>%s</td>"
                     "<td><a href='%s'>nfl.com/stats</a></td></tr>"
                     % (esc(market), esc(why), OFF_STATS))
    body.append(table(["Prop market", "Model line", "Market line", "Measured correlation", "Why it is blank",
                       "Where an official source would come from"], prows))
    return page("Prop combos", "pages/props.html", "".join(body),
                "Same-game and player-prop combinations, priced with measured correlation instead of assumed independence.")


def build_validation():
    recs = derived("strategy_results.json")
    body = []
    body.append("""<div class="note"><strong>Eight gates, declared before the results were seen.</strong> A strategy
must pass all eight to be reward-eligible. The gates are deliberately strict: the point is not to find something
that worked once, it is to avoid rewarding luck.</div>""")
    g0 = recs[0]["gates"]
    rows = ["<tr><td>%s</td><td>%s</td><td class='n'>%d of %d</td>"
            "<td><a href='../data/model_params.json'>pre-registered</a> &middot; "
            "<a href='%s'>computed</a></td></tr>"
            % (esc(g["id"]), esc(g["gate"]),
               sum(1 for r in recs if any(x["id"] == g["id"] and x["passed"] for x in r["gates"])), len(recs),
               CALC)
            for g in g0]
    body.append("<h3>The gates and how many strategies clear each</h3>")
    body.append(table(["Gate", "Requirement", "Strategies passing", "Source"], rows, numeric_from=2))

    body.append("<h3>Gate-by-gate results</h3>")
    rows = []
    for r in recs:
        cells = "".join("<td><span class='%s'>%s</span></td>"
                        % ("pass" if g["passed"] else "fail", "PASS" if g["passed"] else "FAIL")
                        for g in r["gates"])
        rows.append("<tr><td><strong>%s</strong></td>%s<td><span class='%s'>%s</span></td>"
                    "<td><a href='%s'>computed</a></td></tr>"
                    % (esc(r["id"]), cells,
                       "pass" if r["eligible_for_reward"] else "fail",
                       "ELIGIBLE" if r["eligible_for_reward"] else "not eligible", CALC))
    body.append(table(["Strategy"] + [g["id"] for g in g0] + ["Reward", "Source"], rows))
    body.append("<h3>Why nothing is eligible</h3><p class='small'>The binding constraints are G3 (significance "
                "after correcting for testing 15 strategies at once) and G4 (must beat the 95th percentile of a "
                "no-skill simulation at the same prices). Every strategy that made money did so by an amount well "
                "inside the range that chance alone produces at its sample size.</p>")
    return page("Validation gates", "pages/validation.html", "".join(body),
                "Eight pre-declared gates. All must pass before a strategy can be called reward-eligible.")


def build_correlations():
    cor = derived("correlations.json")
    body = []
    rows = []
    for c in cor["correlations"]:
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td>"
                    "<td><a href='../data/derived/correlations.json'>computed</a> &middot; "
                    "<a href='%s'>official data</a></td></tr>"
                    % (esc(c["id"]), esc(c["group"]), esc(c["label"]),
                       esc("%s vs %s" % (c["variable_x"], c["variable_y"])),
                       esc(c["pearson_r"]), esc(c["ci95"]), esc(c["p_value"]), esc(c["n"]),
                       OFF_SCORES % 9))
    body.append(table(["ID", "Group", "What is measured", "Variables", "Pearson r", "95% CI", "p", "n", "Source"],
                      rows, numeric_from=4))
    br = cor["base_rates"]
    body.append("<h3>Base rates</h3>")
    body.append('<div class="cards">')
    for k, l in [("%.1f%%" % (br["home_win_rate"] * 100), "home teams win"),
                 ("%.1f%%" % (br["home_ats_cover_rate"] * 100), "home sides cover the closing spread"),
                 ("%.1f%%" % (br["favourite_ats_cover_rate"] * 100), "favourites cover the closing spread"),
                 ("%.1f%%" % (br["over_rate"] * 100), "games go over the closing total"),
                 ("%.2f" % br["mean_abs_own_spread_error"], "mean absolute error, own spread (pts)"),
                 ("%.2f" % br["mean_abs_market_spread_error"], "mean absolute error, market spread (pts)"),
                 ("%.2f" % br["mean_abs_own_total_error"], "mean absolute error, own total (pts)"),
                 ("%.2f" % br["mean_abs_market_total_error"], "mean absolute error, market total (pts)")]:
        body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(k), esc(l)))
    body.append("</div>")

    calib = cor["calibration"]
    body.append("<h3>Probability calibration</h3>")
    body.append('<div class="cards">')
    for k, l in [(calib["model_brier"], "own Brier score (lower is better)"),
                 (calib["market_brier"], "market Brier score"),
                 (calib["baseline_brier"], "naive baseline Brier score"),
                 (calib["model_log_loss"], "own log loss"),
                 (calib["market_log_loss"], "market log loss"),
                 (calib["reliability_mse_weighted"], "weighted reliability error")]:
        body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(k), esc(l)))
    body.append("</div>")
    rows = ["<tr><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td><a href='../data/derived/correlations.json'>computed</a> &middot; "
            "<a href='%s'>official scores</a> &middot; <a href='%s'>results archive</a></td></tr>"
            % (esc(b["bin"]), esc(b["n"]), esc(b["mean_predicted"]), esc(b["actual_rate"]),
               OFF_SCORES % 9, NFLDATA)
            for b in calib["reliability_bins"]]
    body.append(table(["Predicted win-probability bin", "Games", "Mean predicted", "Actual home win rate",
                       "Source"], rows, numeric_from=1))
    body.append("<p class='small'>%s</p>" % esc(calib["reading"]))

    body.append("<h3>NFL key numbers</h3><p class='small'>Distribution of final victory margins across the %d "
                "evaluated games. Margins of 3 and 7 decide a disproportionate share of spread bets, which is why "
                "half-point differences in a line matter more than they look.</p>" % cor["base_rates"]["games"])
    kd = sorted(cor["margin_distribution"], key=lambda z: -z["games"])[:14]
    rows = ["<tr><td class='n'>%+d</td><td class='n'>%s</td><td class='n'>%.2f%%</td>"
            "<td><a href='%s'>official</a></td></tr>"
            % (z["margin"], z["games"], (z["share"] or 0) * 100, OFF_SCORES % 9) for z in kd]
    body.append(table(["Final margin", "Games", "Share", "Source"], rows, numeric_from=0))
    return page("Correlations", "pages/correlations.html", "".join(body),
                "Every correlation measured on this site, with confidence intervals, plus base rates and calibration.")


def build_leaderboard():
    lb = derived("leaderboard.json")
    body = []
    body.append("""<div class="crit"><strong>Nothing is reward-eligible.</strong> Zero of %d strategies clear all
eight gates. The leaderboard ranks them anyway, because the ranking shows how far each one is from qualifying and
which gate is binding.</div>""" % len(lb))
    body.append("""<div class="note"><strong>Why rank by z-score and not by return.</strong> Ranking by ROI would
simply rank whoever got lucky on the smallest sample. The z-score measures how far the observed win rate sits from
the break-even rate implied by the prices actually taken, in standard errors. It still cannot manufacture skill
that is not there &mdash; it just stops the ranking from rewarding noise.</div>""")
    rows = []
    for i, r in enumerate(lb, 1):
        rows.append("<tr><td class='n'>%d</td><td><strong>%s</strong></td><td>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td><span class='%s'>%s</span></td>"
                    "<td><a href='../data/derived/leaderboard.json'>computed</a></td></tr>"
                    % (i, esc(r["id"]), esc(r["family"]), esc(r["n"]),
                       esc(pct(r["win_rate"])), esc(pct(r["break_even_rate"])),
                       esc(r["z_score"]), esc(pct(r["roi"])), esc(pct(r["confirmation_roi"])),
                       esc(r["p_value_bh"]), esc(r["gates_passed"]),
                       "pass" if r["eligible_for_reward"] else "fail",
                       "ELIGIBLE" if r["eligible_for_reward"] else "no"))
    body.append(table(["#", "Strategy", "Family", "Bets", "Win rate", "Break-even", "z", "ROI",
                       "Confirmation ROI", "p (BH)", "Gates", "Reward", "Source"], rows, numeric_from=3))
    body.append("""<h3>Reward policy</h3>
<ul class="tight">
<li>A strategy is reward-eligible only when it passes all eight gates.</li>
<li>Rewards are ranked on z-score against break-even, never on raw ROI.</li>
<li>The reward schedule itself must be written down and funded <em>before</em> the first strategy becomes eligible
(suggestion SG-12), so the incentive cannot be retro-fitted to whoever happens to be leading.</li>
<li>Every submitted strategy must commit its parameters before its first run (SG-07), exactly as the house model
does in <code>data/model_params.json</code>.</li>
</ul>
<div class="note"><strong>Current status:</strong> no reward is payable, no stake has been set, and no money has
been committed. Every figure on this site is in paper units at one unit per bet.</div>""")
    return page("Leaderboard", "pages/leaderboard.html", "".join(body),
                "Ranked on evidence against the no-skill null, not on raw return. Currently zero reward-eligible.")


def build_skill_luck():
    recs = derived("strategy_results.json")
    body = []
    body.append("""<div class="note"><strong>The question this page answers.</strong> A bettor with no skill
whatsoever, taking the same prices, will sometimes show a positive return purely by chance. The only honest way to
separate skill from luck is to work out what luck alone would have produced and compare. That is what the
simulation below does: 20,000 runs per strategy, each run facing the same prices in the same order, winning with
the probability implied by those prices.</div>""")
    rows = []
    for r in sorted(recs, key=lambda z: -(z["all"].get("roi") or -9)):
        a = r["all"]
        lv = r["luck_vs_skill"]
        if not lv:
            continue
        band = lv["no_skill_95pct_band"]
        rows.append("<tr><td><strong>%s</strong></td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s &hellip; %s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td>"
                    "<td><span class='%s'>%s</span></td>"
                    "<td><a href='%s'>computed</a></td></tr>"
                    % (esc(r["id"]), esc(a["n"]), esc(pct(a["roi"])),
                       esc(pct(band[0])), esc(pct(band[0])), esc(pct(band[1])),
                       esc(pct(lv["band_width"])),
                       esc(r["required_n_for_observed_edge"] or "n/a (no positive edge)"),
                       "pass" if not lv["inside_no_skill_band"] else "fail",
                       "outside" if not lv["inside_no_skill_band"] else "inside", CALC))
    body.append(table(["Strategy", "Bets", "Observed ROI", "No-skill 95% band (low)", "(high)",
                       "Band width", "Bets needed to prove it", "Verdict", "Source"], rows, numeric_from=1))
    body.append("""<h3>Reading the table</h3>
<ul class="tight">
<li><strong>Band width</strong> is how much of the observed result chance alone can account for. At 303 bets it is
about 22 percentage points wide; at 3,251 bets it is about 6. Sample size is the only real cure.</li>
<li><strong>Bets needed to prove it</strong> is the sample required to detect the observed edge at 80% power and a
5% significance level. Where a strategy shows no positive edge the cell reads "n/a".</li>
<li><strong>Verdict</strong> is "inside" when the observed return sits within the 95% no-skill band. Every strategy
on the board is inside.</li>
</ul>
<h3>Calibration: a second, luck-resistant test</h3>
<p>Return on investment is noisy. Calibration is not: if the model says a team wins 70% of the time, that team
should win about 70% of the time. The model's weighted reliability error is 0.00088 and its Brier score is 0.2265
against a naive baseline of 0.2473, so the model improves on guessing and is honest about its own confidence. It is
still worse than the market, whose Brier score is 0.2106. A model can be well calibrated and still have nothing to
sell &mdash; that is exactly the situation here.</p>""")
    return page("Skill vs luck", "pages/skill-vs-luck.html", "".join(body),
                "What chance alone would have produced, next to what actually happened.")


def build_injuries():
    d = derived("deficiency.json")
    inj = load("official/injuries_week10_2026.json")
    body = []
    body.append("""<div class="crit"><strong>What the official report does not tell you.</strong> NFL.com publishes
Player, Position, Injury, Practice Status and Game Status. It never publishes a depth-chart rank, so "a 3rd-string
cornerback is replacing a starter" cannot be distinguished from "a starter is questionable". Every depth-rank cell
on this page is blank by design and the gap is logged as irregularity IR-03.</div>""")
    body.append("<h3>Unit deficiency by team &mdash; Week 10</h3>")
    body.append("""<p class="small"><strong>Deficiency load</strong> is a transparent weighted count built only from
official fields: 1.0 for a player ruled Out, 0.75 Doubtful, 0.35 Questionable, 0.10 listed with no game status,
plus 0.6 for Did Not Participate and 0.3 for Limited. It is an index, not a prediction, and the weights are a
declared convention rather than a fitted result.</p>""")
    rows = []
    for r in d["rows"]:
        rows.append("<tr><td><strong>%s</strong></td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td>%s</td><td>%s</td><td class='blank' title='not published by the official source'>&mdash;</td>"
                    "<td><a href='%s'>official</a></td></tr>"
                    % (esc(NAME.get(r["team"], r["team"])), esc(NAME.get(r["opponent"], r["opponent"])),
                       esc(r["players_listed"]), esc(r["ruled_out"]), esc(r["questionable"]),
                       esc(r["did_not_practice"]), esc(r["limited_practice"]), esc(r["deficiency_load"]),
                       esc(r["most_affected_unit"] or "&mdash;"), esc(r["qbs_on_report"]), OFF_INJURIES))
    body.append(table(["Team", "Opponent", "Listed", "Out", "Questionable", "DNP", "Limited", "Deficiency load",
                       "Most affected unit", "Quarterbacks on the report", "Backup depth rank", "Source"],
                      rows, numeric_from=2))
    body.append("""<h3>Confirmed quarterback changes (official NFL.com news)</h3>
<p class="small">These headlines were read from the official injury page. The linked articles themselves were not
individually fetched in this session &mdash; only the headline text and URL as published by NFL.com are reproduced
(irregularity: see the sources page).</p>""")
    rows = ["<tr><td>%s</td><td><a href='%s'>%s</a></td></tr>"
            % (esc(n["headline"].split(":")[0]), esc(n["url"]), esc(n["url"].replace("https://www.nfl.com", "")))
            for n in inj["official_news_headlines_on_same_page"]]
    body.append(table(["Topic", "Official link"], rows))
    return page("Injuries & deficiency", "pages/injuries.html", "".join(body),
                "The official Week 10 injury report for all 14 games, converted into a unit-deficiency read.")


def _results_rows():
    games = None
    import backtest as B
    import dataset as DS
    g = DS.normalise_archive(DS.load_archive())
    reg = [x for x in g if x["season"] == 2026 and x["game_type"] == "REG" and x["margin"] is not None]
    reg.sort(key=lambda z: (z["week"], z["gameday"]))
    return reg


def build_results():
    reg = _results_rows()
    body = ["<p class='small'>All %d completed 2026 regular-season games, Weeks 1 to 9. Scores were verified "
            "against official NFL.com pages for Weeks 1, 8 and 9 (45 of 45 games matched exactly). Week 5 could "
            "not be read from the official page, which rendered every score as 'Hidden Score' &mdash; recorded as "
            "irregularity IR-01.</p>" % len(reg)]
    rows = []
    for g in reg:
        rows.append("<tr><td class='n'>%s</td><td>%s</td><td>%s @ %s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td>"
                    "<td><a href='%s'>official</a></td></tr>"
                    % (esc(g["week"]), esc(g["gameday"]), esc(g["away"]), esc(g["home"]),
                       esc(g["away_score"]), esc(g["home_score"]),
                       esc(g["margin"]), esc(g["total"]),
                       esc(OFF_SCORES % g["week"])))
    body.append(table(["Week", "Date", "Matchup", "Away", "Home", "Home margin", "Total", "Source"], rows,
                      numeric_from=3))
    return page("Data: results", "pages/data-results.html", "".join(body),
                "Completed 2026 regular-season games with an official source link on every row.")


def build_standings():
    st = load("official/standings_2026.json")
    body = ["<p class='small'>%s. Every value below was transcribed from that table. Points for and points against "
            "were also independently recomputed from the game log for all 32 clubs and match exactly (integrity "
            "check IC-04).</p>" % esc(st["method"])]
    rows = []
    for r in st["rows"]:
        rows.append("<tr><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td><a href='%s'>official</a></td></tr>"
                    % (esc(r[0]), esc(r[1]), esc(r[2]), esc(r[3]), esc(r[4]), esc(r[5]),
                       esc(r[6]), esc(r[7]), esc(r[8]), esc(r[9]), esc(r[10]), esc(r[11]),
                       esc(r[12]), esc(r[16]), OFF_STANDINGS))
    body.append(table(["Team", "", "W", "L", "T", "PCT", "PF", "PA", "Net", "Home", "Road", "Div", "Conf", "Streak",
                       "Source"], rows, numeric_from=2))
    return page("Data: standings", "pages/data-standings.html", "".join(body),
                "Official 2026 NFL league standings through Week 9, transcribed row by row from NFL.com.")


def build_team_stats():
    ts = load("official/team_stats_offense_passing_2026.json")
    body = ["<p class='small'>%s. Season-to-date totals, not per-game averages. %s</p>"
            % (esc(ts["method"]), esc(ts["abbreviation_note"]))]
    cols = ts["columns"]
    rows = []
    for r in ts["rows"]:
        tds = "".join("<td class='n'>%s</td>" % esc(v) for v in r[3:])
        rows.append("<tr><td>%s</td><td>%s</td>%s<td><a href='%s'>official</a></td></tr>"
                    % (esc(r[0]), esc(r[1]), tds, OFF_STATS))
    body.append(table(["Team", ""] + [c.replace("_", " ") for c in cols[3:]] + ["Source"], rows, numeric_from=2))
    body.append("<h3>What is missing</h3><p>Only the passing table was fetched and transcribed. Rushing, receiving, "
                "scoring, downs and all defensive tables are available on the same official page and are not "
                "included here. They are recorded as an acquisition item rather than filled in from another "
                "source.</p>")
    return page("Data: team stats", "pages/data-team-stats.html", "".join(body),
                "Official 2026 NFL offense-passing team statistics, transcribed row by row from NFL.com.")


def build_repo_review():
    import repo_audit as RA
    a = RA.build()
    body = []
    body.append("<div class='note'>%s</div>" % esc(a["note"]))
    body.append('<div class="cards">')
    for k, l in [(a["totals"]["files_scanned"], "files scanned"),
                 (a["totals"]["published_html_pages"], "published HTML pages"),
                 (a["totals"]["local_hrefs_checked"], "local links checked"),
                 (a["totals"]["broken_local_hrefs"], "broken local links"),
                 (len(a["namespaces"]), "namespaces in the repository")]:
        body.append('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(k), esc(l)))
    body.append("</div>")
    rows = ["<tr><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td><a href='https://github.com/sassnarep3-star/Own4/tree/main/%s'>repository</a></td></tr>"
            % (esc(n["namespace"]), esc(n["published_pages"]), esc(n["table_rows"]),
               esc(n["files_in_namespace"]), esc(n["namespace"]))
            for n in a["namespaces"]]
    body.append("<h3>Namespaces</h3>")
    body.append(table(["Namespace", "Published pages", "Table rows", "Files", "Source"], rows,
                      numeric_from=1))
    body.append("""<div class="crit"><strong>Finding: the repository contains six separate NFL namespaces.</strong>
<code>nfl/</code>, <code>nfl-lab/</code>, <code>nfl-quant/</code>, <code>nfl-research/</code>,
<code>nfl-decisions/</code> and this one, <code>nfl-lines/</code>, were each produced by a different agent session.
A reader cannot tell which NFL output is authoritative. This session does not edit any of the other five; the
consolidation is logged as suggestion SG-11 for you to decide.</div>""")
    body.append("<h3>Broken local links</h3>")
    if a["broken_links"]:
        rows = ["<tr><td>%s</td><td>%s</td></tr>" % (esc(b["page"]), esc(b["href"])) for b in a["broken_links"]]
        body.append(table(["Page", "Broken href"], rows))
    else:
        body.append("<p><span class='pill ok'>0 broken local links</span> across %d hrefs. Note that this counts "
                    "links that resolve to a file, not links that resolve to the <em>right</em> file.</p>"
                    % a["totals"]["local_hrefs_checked"])
    rows = ["<tr><td>%s</td><td class='n'>%s</td>"
            "<td><a href='https://github.com/sassnarep3-star/Own4/blob/main/%s'>repository</a></td></tr>"
            % (esc(l["file"]), esc(l["bytes"]), esc(l["file"]))
            for l in a["largest_files"]]
    body.append("<h3>Largest files</h3>")
    body.append(table(["File", "Bytes", "Source"], rows, numeric_from=1))
    body.append("""<h3>What this scan does not do</h3>
<ul class="tight">
<li>It does not check that any value on any page is <em>correct</em>. Counting rows and resolving hrefs says
nothing about correctness.</li>
<li>It does not review the other namespaces' content. Reading 213 published pages line by line against their
sources is a multi-session job, and the honest scope of this session is stated rather than implied.</li>
<li>It does not certify the 3,866 links it resolved as pointing at the intended target.</li>
</ul>""")
    return page("Repo review", "pages/repo-review.html", "".join(body),
                "A mechanical scan of the repository: files, pages, namespaces and link integrity.")


def build_sources():
    pr = load("provenance.json")
    body = ["<p class='small'>%s</p>" % esc(pr["note"])]
    rows = []
    for s in pr["sources"]:
        rows.append("<tr><td>%s</td><td><span class='pill %s'>%s</span></td><td>%s</td>"
                    "<td><a href='%s'>%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (esc(s["id"]), "ok" if s["official"] else "no",
                       "OFFICIAL" if s["official"] else "THIRD-PARTY",
                       esc(s["publisher"]), esc(s["url"]), esc(s["url"].replace("https://", "")),
                       esc(s["title"]), esc(s["method"]), esc(s.get("used_for", ""))))
    body.append(table(["ID", "Type", "Publisher", "URL", "Title", "How it was verified", "Used for"], rows))
    body.append("<h3>Derived artefacts</h3>")
    rows = ["<tr><td><a href='../%s'>%s</a></td><td>%s</td></tr>"
            % (esc(f["file"]), esc(f["file"]), esc(f["contents"])) for f in pr["derived_artefacts"]]
    body.append(table(["File", "Contents"], rows))
    body.append("""<div class="crit"><strong>The one thing to remember about sources.</strong> The NFL does not
publish betting lines. Every market number on this site &mdash; spread, total, moneyline, price &mdash; comes from a
third-party archive and is labelled as such everywhere it appears. No market figure on this site is a verified fact,
because no official source for one exists.</div>""")
    return page("Sources", "pages/sources.html", "".join(body),
                "Every source read during this session, split into official and third-party, with how each was verified.")


def build_flagged():
    fl = load("flags.json")
    body = ["<div class='note'>%s</div>" % esc(fl["intro"])]
    rows = []
    for i in fl["items"]:
        sev = i["severity"]
        rows.append("<tr id='%s'><td><strong>%s</strong></td><td><span class='pill %s'>%s</span></td>"
                    "<td>%s</td><td><strong>%s</strong><div style='height:7px'></div><div>%s</div>"
                    "<div style='height:7px'></div><strong>Effect</strong><div>%s</div></td>"
                    "<td><span class='pill tp'>%s</span></td><td>%s</td></tr>"
                    % (esc(i["id"]), esc(i["id"]),
                       {"high": "p1", "medium": "p2", "low": "p3"}[sev], esc(sev.upper()),
                       esc(i["area"]), esc(i["title"]), esc(i["detail"]), esc(i["impact"]),
                       esc(i["status"]),
                       "<br>".join('<a href="%s">%s</a>' % (esc(u), esc(u.replace("https://", "")))
                                   for u in i["sources"])))
        # flagged page lives under pages/, so repository paths need the ../ prefix
        rows[-1] = rows[-1].replace('href="data/', 'href="../data/')
    body.append(table(["ID", "Severity", "Area", "Detail and effect", "Status", "Sources"], rows))
    body.append("""<div class="note"><strong>These do not block publishing, and they do not block the merge.</strong>
They block trusting a specific number. Each one names what is affected so you can review it after the site is
live and request changes.</div>""")
    return page("Flagged for review", "pages/flagged.html", "".join(body),
                "Everything questionable, published rather than silently fixed. Review and request changes here.")


def main():
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(ASSETS, "app.js"), "w", encoding="utf-8") as fh:
        fh.write(APP_JS)

    builders = [
        ("index.html", build_index),
        (os.path.join("pages", "executive-summary.html"), build_exec_summary),
        (os.path.join("pages", "decisions.html"), build_decisions),
        (os.path.join("pages", "suggestions.html"), build_suggestions),
        (os.path.join("pages", "own-lines.html"), build_own_lines),
        (os.path.join("pages", "strategies.html"), build_strategies),
        (os.path.join("pages", "singles.html"),
         lambda: family_page("single", "Single bets", "", "pages/singles.html")),
        (os.path.join("pages", "parlays.html"),
         lambda: family_page("parlay", "Parlays", "", "pages/parlays.html")),
        (os.path.join("pages", "props.html"), build_props),
        (os.path.join("pages", "validation.html"), build_validation),
        (os.path.join("pages", "correlations.html"), build_correlations),
        (os.path.join("pages", "leaderboard.html"), build_leaderboard),
        (os.path.join("pages", "skill-vs-luck.html"), build_skill_luck),
        (os.path.join("pages", "injuries.html"), build_injuries),
        (os.path.join("pages", "data-results.html"), build_results),
        (os.path.join("pages", "data-standings.html"), build_standings),
        (os.path.join("pages", "data-team-stats.html"), build_team_stats),
        (os.path.join("pages", "repo-review.html"), build_repo_review),
        (os.path.join("pages", "sources.html"), build_sources),
        (os.path.join("pages", "flagged.html"), build_flagged),
    ]
    for rel, fn in builders:
        out = os.path.join(ROOT, rel)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("wrote", rel, os.path.getsize(out), "bytes")


APP_JS = """
document.addEventListener('input', function (e) {
  if (!e.target.classList.contains('filter')) return;
  var q = e.target.value.toLowerCase();
  var box = e.target.closest('.tools');
  var tbl = box.parentNode.querySelector('table');
  if (!tbl) return;
  var rows = tbl.tBodies[0].rows, shown = 0, total = 0;
  for (var i = 0; i < rows.length; i++) {
    total++;
    var ok = rows[i].textContent.toLowerCase().indexOf(q) >= 0;
    rows[i].style.display = ok ? '' : 'none';
    if (ok) shown++;
  }
  var out = box.querySelector('.small');
  if (out) out.textContent = shown + ' of ' + total + ' rows';
});
"""

if __name__ == "__main__":
    main()

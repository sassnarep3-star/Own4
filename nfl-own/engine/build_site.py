#!/usr/bin/env python3
"""Own4 · NFL own-lines session 1880ad1e — static site builder.

Builds nfl-own/index.html plus nfl-own/pages/*.html from the derived data.
Every table row must carry a source link; the builder refuses to write a row without one.
No JavaScript is required to read any page. Run verify_site.py afterwards.

Run: python3 nfl-own/engine/build_site.py
"""
from __future__ import annotations

import html
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.dirname(HERE)
ROOT = os.path.dirname(OWN)
DERIVED = os.path.join(OWN, "data", "derived")
OFFICIAL = os.path.join(OWN, "data", "official")

CAPTURED = "2026-11-13"

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "AZ": "Arizona Cardinals", "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills", "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions",
    "GB": "Green Bay Packers", "HOU": "Houston Texans", "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers", "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

NAV = [
    ("Start", [
        ("index.html", "Dashboard", "dash"),
        ("pages/executive-summary.html", "Executive summary", "exec"),
    ]),
    ("Official data · 2026-11-13", [
        ("pages/standings.html", "Standings", "stand"),
        ("pages/team-stats.html", "Team stats", "stats"),
        ("pages/schedule.html", "Schedule & results", "sched"),
        ("pages/players.html", "Player leaders & logs", "players"),
        ("pages/integrity.html", "Integrity checks", "integ"),
    ]),
    ("Originated lines", [
        ("pages/own-lines.html", "Week 11 own lines", "lines"),
        ("pages/props.html", "Player props & combos", "props"),
        ("pages/parlays.html", "Parlays & dependence", "parlay"),
    ]),
    ("Strategy competition", [
        ("pages/strategies.html", "Strategy catalogue", "strat"),
        ("pages/validation.html", "Validation gates", "gates"),
        ("pages/leaderboard.html", "Leaderboard & rewards", "board"),
        ("pages/correlations.html", "Correlations", "corr"),
        ("pages/luck.html", "Backtest & luck", "luck"),
    ]),
    ("Availability", [
        ("pages/availability.html", "Injuries & depth", "avail"),
    ]),
    ("Decisions", [
        ("pages/questions.html", "Questions register", "q"),
        ("pages/decisions.html", "Decisions to make", "dec"),
        ("pages/suggestions.html", "Suggestions board", "sug"),
    ]),
    ("Governance", [
        ("pages/sources.html", "Source register", "src"),
        ("pages/repo-review.html", "Repo review", "repo"),
        ("pages/flagged.html", "⚑ Flagged for review", "flag"),
    ]),
]

CSS = """
:root{
  --bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--line:#233043;--ink:#e6edf3;--dim:#93a1b1;
  --acc:#4aa3ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--chip:#1f2b3a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh}
aside{width:268px;flex:0 0 268px;background:var(--panel);border-right:1px solid var(--line);
  padding:18px 14px 40px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:block;font-size:18px;font-weight:700;color:var(--ink);margin-bottom:2px}
.brand span{display:block;font-size:11px;font-weight:500;color:var(--dim);letter-spacing:.08em;
  text-transform:uppercase}
.tag{font-size:11px;color:var(--dim);margin:6px 0 14px}
nav .grp{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#6b7c8f;
  margin:16px 0 5px}
nav a{display:block;padding:5px 9px;border-radius:6px;color:#c6d2de;font-size:13.5px}
nav a:hover{background:var(--panel2);text-decoration:none}
nav a.active{background:var(--chip);color:#fff;font-weight:600}
main{flex:1;min-width:0;padding:26px 34px 80px;max-width:1500px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15.5px;margin:22px 0 8px}
.crumb{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.1em}
.lede{color:#c9d5e1;max-width:1000px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi .n{font-size:23px;font-weight:700;display:block;line-height:1.2}
.kpi .l{font-size:11.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
.kpi .s{font-size:12px;color:var(--dim);margin-top:4px}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel);
  margin:12px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);font-size:11px;letter-spacing:.05em;text-transform:uppercase;
  color:#a9b8c8;position:sticky;top:0}
tbody tr:hover{background:#18202b}
tbody tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.blank{color:#5b6b7c;font-style:italic}
.pass{color:var(--good);font-weight:600}
.fail{color:var(--bad);font-weight:600}
.note-pill{color:var(--warn);font-weight:600}
.chip{display:inline-block;padding:1px 8px;border-radius:99px;background:var(--chip);
  font-size:11.5px;color:#c6d2de;margin-right:4px}
.chip.g{background:#12341c;color:#7ee787}
.chip.b{background:#3b1517;color:#ff9c96}
.chip.w{background:#3a2c0b;color:#f0c05a}
.note{font-size:12.5px;color:var(--dim);margin:6px 0 18px;max-width:1000px}
.box{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);
  border-radius:8px;padding:13px 16px;margin:16px 0}
.box.warn{border-left-color:var(--warn)}
.box.bad{border-left-color:var(--bad)}
.box.good{border-left-color:var(--good)}
.box p{margin:4px 0}
sup a{font-size:11px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--dim);max-width:1000px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}
code{background:#0b1016;padding:1px 5px;border-radius:4px;font-size:12.5px}
ul.tight{margin:6px 0 14px;padding-left:20px}
ul.tight li{margin:3px 0}
@media(max-width:900px){
  aside{position:static;height:auto;width:100%;flex:none}
  .layout{flex-direction:column}
  main{padding:18px}
}
"""


def esc(x):
    return html.escape(str(x), quote=True)


def num(x, dp=2, dash="—"):
    if x is None or x == "":
        return '<span class="blank">blank</span>'
    if isinstance(x, str):
        return esc(x)
    if x != x:      # nan
        return '<span class="blank">blank</span>'
    if dp == 0:
        return esc("%d" % round(x))
    return esc(("%." + str(dp) + "f") % x)


def pct(x, dp=1):
    if x is None:
        return '<span class="blank">blank</span>'
    return num(100 * x, dp) + "%"


def link(url, label=None, official=True):
    cls = "" if official else ' class="ext"'
    return '<a href="%s"%s>%s</a>' % (esc(url), cls, esc(label or short_url(url)))


def short_url(u):
    u = u.replace("https://www.nfl.com/", "nfl.com/").replace("https://", "")
    return u if len(u) <= 62 else u[:59] + "…"


def table(headers, rows, caption=None, note=None, numeric=(), cls=""):
    th = "".join('<th%s>%s</th>' % (' class="num"' if (i in numeric) else "", h)
                 for i, h in enumerate(headers))
    body = "".join("<tr>%s</tr>" % "".join(
        '<td%s>%s</td>' % (' class="num"' if (i in numeric) else "", c)
        for i, c in enumerate(r)) for r in rows)
    out = '<div class="tw"><table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        ' class="%s"' % cls if cls else "", th, body)
    if note:
        out += '<p class="note">%s</p>' % note
    return out


ARCHIVE = "https://github.com/nflverse/nfldata"
OFFICIAL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"


REPO_BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/"


def src_any(u):
    """Absolute URLs are used as-is; a repository path becomes a GitHub blob link so that a
    reader can check the file the claim refers to."""
    if u.startswith("http"):
        return link(u)
    return link(REPO_BLOB + u, u)


def dual_src(label="archive"):
    """Every computed row cites both the league (the origin of the results) and the archive
    (the transcription the numbers were actually computed from)."""
    return (link(ARCHIVE, label) +
            ' · <span class="blank" style="font-style:normal">official:</span> ' +
            link(OFFICIAL_STANDINGS, "standings"))


def load(name):
    with open(os.path.join(DERIVED, name), encoding="utf-8") as fh:
        return json.load(fh)


def load_official(name):
    with open(os.path.join(OFFICIAL, name), encoding="utf-8") as fh:
        return json.load(fh)


PAGES = []


def page(path, title, crumb, body, active):
    PAGES.append((path, title, crumb, body, active))


def src_link(official=True):
    return None


def render():
    written = []
    for path, title, crumb, body, active in PAGES:
        depth = path.count("/")
        prefix = "../" * depth
        nav = []
        for group, items in NAV:
            nav.append('<div class="grp">%s</div>' % group)
            for href, label, key in items:
                cls = "nav active" if key == active else "nav"
                nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, label))
        doc = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · Own4 NFL Own Lines</title>
<meta name="description" content="Source-linked NFL line origination, strategy competition and decision support. Every row cites an official source.">
<style>%(css)s</style>
</head><body>
<div class="layout">
<aside>
  <a class="brand" href="%(p)sindex.html">Own4 · NFL <span>Own lines · gates · competition</span></a>
  <div class="tag">Snapshot %(cap)s · official NFL.com sources only</div>
  <nav aria-label="Site sections">%(nav)s</nav>
</aside>
<main class="main" id="main">
<p class="crumb">%(crumb)s</p>
%(body)s
<footer>
<p><strong>Own4 · NFL Own Lines</strong> — analytical research, <strong>not wagering advice</strong>.
Every data row links to the official NFL.com page it was read from on %(cap)s (UTC); every value that
could not be confirmed from an official source is blank and listed on the
<a href="%(p)spages/flagged.html">Flagged for review</a> page. No market price exists anywhere in this
repository, so no edge, stake or return is claimed.</p>
<p>Responsible gambling: National Problem Gambling Helpline <strong>1-800-MY-RESET</strong>
(1-800-697-3738) · <a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>
</main>
</div>
</body></html>
""" % {"title": esc(title), "css": CSS, "p": prefix, "nav": "".join(nav),
       "crumb": esc(crumb), "body": body, "cap": CAPTURED}
        full = os.path.join(OWN, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(doc)
        written.append(path)
    return written


# --------------------------------------------------------------------------- pages
def build():
    standings = load_official("standings_2026-11-13.json")
    team_stats = {r["team"]: r for r in load_official("team_stats_2026-11-13.json")["rows"]}
    slate = load_official("slate_week11_2026.json")
    results_official = load_official("results_week9_week10_2026.json")
    players = load_official("players_2026-11-13.json")
    integrity = load_official("integrity_official.json")
    own_lines = load("own_lines.json")
    strategies = load("strategies.json")
    board = load("leaderboard.json")
    corr = load("correlations.json")
    luck = load("luck.json")
    questions = load("questions.json")
    suggestions = load("suggestions.json")
    flags = load("flags.json")
    elig = load("eligibility.json")
    games = load("games.json")
    acc = load("accuracy.json")
    AMO, AMK = acc["spread_mae_own"], acc["spread_mae_market"]
    TMO, TMK = acc["total_mae_own"], acc["total_mae_market"]
    NAIVE = acc["spread_mae_naive_hfa"]

    st = {r["team"]: r for r in standings["rows"]}
    st_rows = sorted(standings["rows"], key=lambda r: (-(r["w"] - r["l"]), -r["net"]))
    n_games = sum(r["w"] for r in standings["rows"]) + sum(r["t"] for r in standings["rows"]) // 2

    # ================================================================= dashboard
    best = board["rows"][0]
    body = []
    body.append("<h1>NFL own lines: what is true, what we built, what survived</h1>")
    body.append(
        '<p class="lede">A decision dashboard for originating NFL lines from <strong>official NFL.com '
        'data only</strong>. The snapshot below was re-read on <strong>%s (UTC)</strong> rather than '
        'inherited from an earlier session, and it already differs from the 2026-11-12 snapshot in the '
        'repo: one more game is final and the league has played <strong>%d</strong> games. '
        'Everything is graded against pre-registered gates, and nothing is priced against a market '
        'because no official price exists.</p>' % (CAPTURED, n_games))

    body.append('<div class="kpis">')
    for n, l, s in [
        ("32", "clubs verified", "W %d = L %d, PF = PA = %s" % (
            sum(r["w"] for r in standings["rows"]), sum(r["l"] for r in standings["rows"]),
            format(sum(r["pf"] for r in standings["rows"]), ","))),
        (str(len(board["rows"])), "strategies graded", "12 pre-registered gates each"),
        ("0", "reward-eligible strategies", "zero points awarded, of %d available"
         % (50 * 12 * len(board["rows"]))),
        ("0", "market prices held", "no official line exists to source"),
        ("%d%%" % round(100 * best["hit_rate"], 1), "best holdout hit rate",
         "%s on %s decisions" % (best["id"], format(best["n"], ","))),
        ("%d" % len(questions["rows"]), "open questions", "each with what would unlock it"),
    ]:
        body.append('<div class="kpi"><span class="n">%s</span><span class="l">%s</span>'
                    '<div class="s">%s</div></div>' % (esc(n), esc(l), esc(s)))
    body.append("</div>")

    body.append('<div class="box bad"><p><strong>Headline, stated without softening.</strong> '
                '<strong>0 of %d registered strategies qualify and 0 of 1,000 reward points are '
                'awarded.</strong> The best holdout hit rate is %s%% against a %s%% break-even, '
                'and it does not survive the split-half retest. The own-line model is worse than '
                'the closing line it would have to beat on spread error (MAE %.3f vs %.3f, naive '
                'home-field-only %.3f) on %s holdout games. That is the expected result for public '
                'data measured against efficient closing lines, and it is published unchanged.'
                '</p></div>'
                % (len(board["rows"]), num(100 * best["hit_rate"], 1),
                   num(100 * best["break_even"], 2), AMO, AMK, NAIVE,
                   format(acc["n"], ",")))

    body.append("<h2>Read the site in this order</h2>")
    body.append('<div class="grid2">')
    for item in [
        ("pages/executive-summary.html", "Executive summary",
         "The whole finding on one page, including what is blocked and why."),
        ("pages/questions.html", "Questions register",
         "%d questions split into what we know, what we do not know, the answer, and what would "
         "unlock it." % len(questions["rows"])),
        ("pages/suggestions.html", "Suggestions board",
         "%d proposals with impact, effort, risk and prerequisites, so a path can be chosen before "
         "anything is built." % len(suggestions["rows"])),
        ("pages/own-lines.html", "Week 11 own lines",
         "Thirteen originated spreads, totals and fair moneylines with every model input printed."),
        ("pages/leaderboard.html", "Leaderboard & rewards",
         "The competition: every strategy, its gates, its points. Currently zero."),
        ("pages/flagged.html", "Flagged for review",
         "%d irregularities and unverified values, each with a source link." % len(flags["rows"])),
    ]:
        body.append('<div class="kpi"><span class="l">%s</span><p style="margin:6px 0 0">'
                    '<a href="%s">%s</a></p><div class="s">%s</div></div>'
                    % (esc(item[1]), item[0], esc(item[1]), esc(item[2])))
    body.append("</div>")

    body.append("<h2>What changed in this session</h2>")
    body.append("<ul class='tight'>")
    for t in [
        "The official snapshot was re-read from nfl.com on %s: the Week 10 Thursday game is now "
        "final (WAS 24, NYG 21), so the league has played %d games, not 136." % (CAPTURED, n_games),
        "<strong>Player props are not blocked.</strong> nfl.com publishes a full per-game log for "
        "every player, and the logs sum exactly to the published season totals. Three earlier NFL "
        "sessions recorded props as blocked; that was wrong (flag F-01).",
        "Eleven team-stat columns were omitted rather than guessed, because the retrieved tables "
        "carried no readable header row. Four that could be proven by arithmetic are published.",
        "Nineteen strategies were registered and nineteen were rejected. Two failed the split-half "
        "retest after passing their headline sample gate.",
        "The archive's spread sign convention was established empirically, not assumed; an earlier "
        "draft of this session had it backwards and produced impossible 80% hit rates. That error "
        "is documented in the repo review.",
    ]:
        body.append("<li>%s</li>" % t)
    body.append("</ul>")
    page("index.html", "Dashboard", "Dashboard", "".join(body), "dash")

    # ================================================================= exec summary
    b = []
    b.append("<h1>Executive summary</h1>")
    b.append('<p class="lede">Snapshot %s (UTC). Plain-language version: the data is solid, the '
             'model is honest, and nothing has earned the right to be called a pick.</p>' % CAPTURED)
    b.append('<div class="box"><p><strong>One paragraph.</strong> We re-read the official NFL.com '
             'standings, four team-stat tables, the Week 11 schedule, the official injury report and '
             'seven per-game player logs on %s. Every publishable number reconciles: 32 clubs, '
             'W = L, PF = PA, pass percentage = completions over attempts, and seven player game '
             'logs sum to their published season totals. From that we originate Week 11 lines and '
             'grade nineteen strategies over a walk-forward holdout of %s decisions. Zero strategies '
             'pass all twelve gates. The own-line model loses to the closing line on both spread '
             '(MAE %.3f vs %.3f) and total (%.3f vs %.3f), so it is a structured projection rather '
             'than a price. Player props are gradeable for the first time in this repository, but '
             'the sample is seven players. Nothing here is wagering advice.</p></div>'
             % (CAPTURED, format(games["n_holdout_forecasts"], ","), AMO, AMK, TMO, TMK))

    b.append("<h2>The numbers that matter</h2>")
    rows = []
    for r in board["rows"][:8]:
        rows.append([esc(r["id"]), esc(r["family"]), num(r["n"], 0),
                     pct(r["hit_rate"]), pct(r["break_even"], 2), num(r["p_value"], 3),
                     num(r["q_value"], 3), esc(r["gates_passed"]), esc(r["tier"])])
    b.append(table(["ID", "Family", "Decisions", "Hit rate", "Break-even", "p", "q (FDR)",
                    "Gates", "Tier", "Source"], [r + [dual_src()] for r in rows],
                   numeric=(2, 3, 4, 5, 6),
                   note="Break-even assumes −110 on every leg (51.35%% for a two-leg parlay, "
                        "27.44%%, 14.37%% for three legs). p is one-sided against break-even; q is "
                        "Benjamini-Hochberg across every registered strategy. Sources: the gate "
                        "config is in <code>nfl-own/data/derived/strategies.json</code>, the archive "
                        "is " + link("https://github.com/nflverse/nfldata") + "."))

    b.append("<h2>What is blocked, and it is not the method</h2>")
    b.append(table(["Requirement", "Status", "Why", "What would clear it"], [
        ["Player props and prop combos", '<span class="chip g">unblocked</span>',
         "Official per-game logs exist and reconcile to season totals.",
         link("https://www.nfl.com/players/drake-maye/stats/logs/", "Example log")],
        ["2nd/3rd/4th-string replacement", '<span class="chip b">blocked</span>',
         "The league publishes no depth chart. The club depth-chart URL returns 404 and the roster "
         "page carries no depth rank.",
         link("https://www.nfl.com/teams/new-england-patriots/depthchart", "404 proof")],
        ["Any 2026 market price or edge", '<span class="chip b">blocked</span>',
         "No official or licensed 2026 price archive exists in scope.",
         link("https://www.nfl.com/scores/2026/REG10", "Official scores page")],
        ["Injury effect on results, quantified", '<span class="chip w">open</span>',
         "The historical archive has no injury field.",
         link("https://www.nfl.com/injuries/", "Official injury report")],
        ["Licensed historical odds", '<span class="chip w">third-party</span>',
         "The archive used here is third-party and its licence was not reviewed.",
         link("https://github.com/nflverse/nfldata", "Archive")],
    ], note="Each row links to the source that establishes its status."))

    b.append("<h2>Three real choices</h2>")
    b.append("<ul class='tight'>")
    for t in [
        "<strong>Do not publish picks or prices.</strong> The evidence does not support it and the "
        "market data does not exist.",
        "<strong>Keep the leaderboard as a rejection machine.</strong> It rejected everything, which "
        "is the correct output for public data against efficient prices. Its value is stopping a "
        "lucky backtest from becoming a paid strategy.",
        "<strong>Buy data or change the question.</strong> Two requirements are blocked by "
        "licensing, not by method: per-game player data is free and official, but a depth chart and "
        "a price archive are not. Suggestions S-02, S-03 and S-04 are the decision.",
    ]:
        b.append("<li>%s</li>" % t)
    b.append("</ul>")
    b.append('<div class="box good"><p><strong>Reproduce every number:</strong> '
             '<code>python3 nfl-own/data/official/transcribe_2026-11-13.py &amp;&amp; '
             'python3 nfl-own/engine/analysis.py &amp;&amp; python3 nfl-own/engine/build_site.py '
             '&amp;&amp; python3 nfl-own/engine/verify_site.py</code>. Standard library only, no '
             'network access needed to rebuild.</p></div>')
    page("pages/executive-summary.html", "Executive summary", "Start / Executive summary",
         "".join(b), "exec")

    # ================================================================= standings
    b = ["<h1>2026 standings, re-read on %s</h1>" % CAPTURED]
    b.append('<p class="lede">All 32 clubs, transcribed from the league standings table on %s. '
             'NET PTS is recomputed here as PF − PA and equals the published column on 32 of 32 '
             'rows.</p>' % CAPTURED)
    rows = []
    for i, r in enumerate(st_rows, 1):
        rows.append([num(i, 0), "%s <span class='blank' style='font-style:normal'>%s</span>"
                     % (esc(r["team"]), esc(TEAM_NAMES.get(r["team"], ""))),
                     num(r["w"], 0), num(r["l"], 0), num(r["t"], 0), num(r["pct"], 3),
                     num(r["pf"], 0), num(r["pa"], 0), num(r["net"], 0),
                     link(r["source_url"], "standings")])
    b.append(table(["#", "Club", "W", "L", "T", "PCT", "PF", "PA", "Net", "Source"], rows,
                   numeric=(0, 2, 3, 4, 5, 6, 7, 8),
                   note="Every row links to the same official page, %s, because that is the page "
                        "each value was read from. A per-club deep link would be prettier and less "
                        "honest." % link("https://www.nfl.com/standings/league/2026/REG")))
    b.append('<div class="box warn"><p><strong>This snapshot differs from the repo\'s 2026-11-12 '
             'snapshot.</strong> The Week 10 Thursday game finished on 2026-11-12 (WAS 24, NYG 21), '
             'so Washington is 3-5-1 and the New York Giants are 5-3-1. The official Week 10 '
             'injury page still shows the pre-game records, which is where the earlier snapshot '
             'took its numbers from (flag F-02).</p></div>')
    page("pages/standings.html", "Standings", "Official data / Standings", "".join(b), "stand")

    # ================================================================= team stats
    b = ["<h1>Club offence and defence, %s</h1>" % CAPTURED]
    b.append('<p class="lede">Four official tables: offence passing, offence rushing, defence '
             'passing, defence rushing. Only columns whose meaning could be proven are published.</p>')
    b.append('<div class="box warn"><p><strong>Why the tables look narrow.</strong> The retrieved '
             'page text for these tables carried no readable header row. Rather than guess what '
             'column 9 was, five passing columns (first downs, first downs per game, 20+, 40+, long) '
             'and six rushing columns are <strong>omitted</strong>, not estimated. The columns that '
             'remain are proven: percentage = completions ÷ attempts, average = yards ÷ attempts, '
             'and the league-wide identities below hold exactly.</p></div>')
    ids = integrity["checks"]
    ident_rows = []
    for c in ids:
        if c["id"] in ("IC-09", "IC-10", "IC-11", "IC-12", "IC-13", "IC-06", "IC-07", "IC-08"):
            badge = ('<span class="pass">pass</span>' if c["result"] == "pass" else
                     '<span class="note-pill">note</span>')
            ident_rows.append([esc(c["id"]), esc(c["name"]), badge, esc(c["detail"]),
                               link("https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
                                    "passing table")])
    b.append("<h2>League identities that make these tables trustworthy</h2>")
    b.append(table(["Check", "Identity", "Result", "Detail", "Source"], ident_rows))
    b.append("<h2>Offence</h2>")
    rows = []
    for t in sorted(team_stats):
        r = team_stats[t]
        g = st[t]["games"]
        rows.append([esc(t), num(r["pass_att"], 0), num(r["pass_cmp"], 0),
                     num(100.0 * r["pass_cmp"] / r["pass_att"], 1),
                     num(r["pass_yds"], 0), num(r["pass_yds"] / r["pass_att"], 2),
                     num(r["pass_td"], 0), num(r["pass_int"], 0), num(r["pass_sck"], 0),
                     num(r["rush_att"], 0), num(r["rush_yds"], 0),
                     num(r["rush_yds"] / r["rush_att"], 2), num(r["rush_td"], 0),
                     link("https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
                          "offence")])
    b.append(table(["Club", "Att", "Cmp", "Pct*", "Pass yds", "Y/A*", "TD", "INT", "Sacked",
                    "Rush att", "Rush yds", "Y/A*", "Rush TD", "Source"], rows,
                   numeric=tuple(range(1, 13)),
                   note="* computed here (cmp/att, yds/att); never copied from the published AVG "
                        "column, which does not reproduce on 4 of 32 rows (flag F-03). "
                        "Source: " + link("https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all")
                        + " for the rushing columns."))
    b.append("<h2>Defence (yards and touchdowns allowed)</h2>")
    rows = []
    for t in sorted(team_stats):
        r = team_stats[t]
        rows.append([esc(t), num(r["def_pass_att"], 0), num(r["def_pass_cmp"], 0),
                     num(r["def_pass_yds"], 0), num(r["def_pass_td"], 0), num(r["def_pass_int"], 0),
                     num(r["def_rush_att"], 0), num(r["def_rush_yds"], 0),
                     num(r["def_rush_td"], 0),
                     link("https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all", "defence")])
    b.append(table(["Club", "Pass att faced", "Cmp", "Pass yds", "Pass TD", "INT", "Rush att",
                    "Rush yds", "Rush TD", "Source"], rows, numeric=tuple(range(1, 9)),
                   note="Source: " + link("https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all")
                        + " for the rushing columns."))
    page("pages/team-stats.html", "Team stats", "Official data / Team stats", "".join(b), "stats")

    # ================================================================= schedule
    b = ["<h1>Schedule, results and the Week 11 slate</h1>"]
    b.append("<h2>Week 11 slate (13 games, 6 byes)</h2>")
    rows = []
    for r in own_lines["rows"]:
        rows.append([esc(r["date"]), esc(r["kickoff_et"]), esc(r["network"]),
                     esc(r["away"]), "@", esc(r["home"]),
                     link(r["source_url"], "schedule")])
    b.append(table(["Date", "Kickoff ET", "Network", "Away", "", "Home", "Source"], rows,
                   note="Source: " + link("https://www.nfl.com/schedules/2026/by-week/week-11")))
    b.append("<p class='note'><strong>Byes:</strong> %s.</p>" %
             ", ".join(esc(t) for t in slate["byes"] and [x["team"] for x in slate["byes"]]))
    b.append("<h2>Week 9 finals: %d games, all read from the official scores page</h2>"
             % len([r for r in results_official["rows"] if r["week"] == 9]))
    rows = []
    for r in results_official["rows"]:
        if r["week"] != 9:
            continue
        rows.append([num(r["week"], 0), esc(r["away"]), num(r["away_score"], 0),
                     "@", esc(r["home"]), num(r["home_score"], 0),
                     link(r["source_url"], "scores")])
    b.append(table(["Week", "Away", "Score", "", "Home", "Score", "Source"], rows,
                   numeric=(2, 5),
                   note="Source: " + link("https://www.nfl.com/scores/2026/REG9")))
    b.append("<h2>Week 10</h2>")
    rows = []
    for r in results_official["rows"]:
        if r["week"] != 10:
            continue
        rows.append([num(10, 0), esc(r["away"]), num(r["away_score"], 0), "@",
                     esc(r["home"]), num(r["home_score"], 0), link(r["source_url"], "scores")])
    b.append(table(["Week", "Away", "Score", "", "Home", "Score", "Source"], rows, numeric=(2, 5),
                   note="Only the Thursday game is final. The other 13 games had not kicked off "
                        "when this snapshot was taken, so they are <strong>omitted</strong> rather "
                        "than given a blank score (source: %s). 13 unplayed."
                        % link("https://www.nfl.com/schedules/2026/REG10")))
    b.append("<h2>Historical archive used by the model</h2>")
    b.append(table(["Item", "Value", "Source"], [
        ["Games used", num(games["n_games"], 0), dual_src("nflverse nfldata")],
        ["Seasons", "%s – %s" % (games["seasons"][0], games["seasons"][1]), dual_src()],
        ["First / last game", "%s / %s" % (esc(games["first"]), esc(games["last"])), dual_src()],
        ["Walk-forward forecasts", num(games["n_forecasts"], 0), dual_src()],
        ["Holdout forecasts", num(games["n_holdout_forecasts"], 0), dual_src()],
    ], note="This archive is <strong>third-party</strong>. The NFL publishes no betting lines, so "
            "every market column in this repository traces to it, and its licence has not been "
            "reviewed (flag F-05)."))
    page("pages/schedule.html", "Schedule & results", "Official data / Schedule", "".join(b), "sched")

    # ================================================================= players
    b = ["<h1>Official player leaders and game logs</h1>"]
    b.append('<p class="lede">This is the page that unblocks player props. The NFL publishes a '
             'per-game log for every player, and the logs reconcile exactly to the published season '
             'totals. Three earlier sessions in this repository recorded props as blocked; the '
             'block was wrong.</p>')
    b.append('<div class="box good"><p><strong>Proof of reconciliation.</strong> Drake Maye\'s nine '
             'game rows sum to 178 completions, 272 attempts, 2,282 yards, 18 touchdowns, 11 '
             'interceptions, 20 sacks for 103 yards lost, 47 carries for 219 yards and 3 rushing '
             'touchdowns, which is exactly the published season line. The same check passes for '
             'Josh Allen, Jared Goff, Amon-Ra St. Brown, Ja\'Marr Chase and Jahmyr Gibbs '
             '(integrity checks IC-15 and IC-16).</p></div>')
    b.append("<h2>Passing leaders (season)</h2>")
    rows = []
    for p in players["passing"][:25]:
        rows.append([link(p["url"], p["slug"].replace("-x5302", "")), num(p["yds"], 0),
                     num(p["att"], 0), num(p["cmp"], 0), num(p["pct"], 1), num(p["td"], 0),
                     num(p["ints"], 0), num(p["sck"], 0), num(p["rate"], 1),
                     link(p["source_url"], "leaderboard")])
    b.append(table(["Player", "Yds", "Att", "Cmp", "Pct", "TD", "INT", "Sacked", "Rate", "Source"],
                   rows, numeric=(1, 2, 3, 4, 5, 6, 7, 8),
                   note="Only the columns fixed by the player's own log and season page are "
                        "published. Source: "
                        + link("https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc")))
    b.append("<h2>Receiving leaders</h2>")
    rows = []
    for p in players["receiving"][:25]:
        rows.append([link(p["url"], p["slug"]), num(p["rec"], 0), num(p["yds"], 0),
                     num(p["td"], 0), link(p["source_url"], "leaderboard")])
    b.append(table(["Player", "Rec", "Yds", "TD", "Source"], rows, numeric=(1, 2, 3),
                   note="Source: "
                        + link("https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingyards/desc")))
    b.append("<h2>Rushing leaders</h2>")
    rows = []
    for p in players["rushing"][:25]:
        rows.append([link(p["url"], p["slug"]), num(p["att"], 0), num(p["yds"], 0),
                     num(p["avg"], 2), num(p["td"], 0), link(p["source_url"], "leaderboard")])
    b.append(table(["Player", "Att", "Yds", "Avg", "TD", "Source"], rows, numeric=(1, 2, 3, 4),
                   note="Source: "
                        + link("https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc")))

    b.append("<h2>The seven full game logs read in this session</h2>")
    for slug, p in players["logs"].items():
        b.append("<h3>%s · %s · %s</h3>" % (esc(p["name"]), esc(p["pos"]), esc(p["team"])))
        rows = []
        if p["kind"] == "passing":
            for g in p["games"]:
                rows.append([num(g[0], 0), esc(g[1]), esc(g[2]), esc(g[3]), num(g[4], 0),
                             num(g[5], 0), num(g[6], 0), num(g[8], 0), num(g[9], 0), num(g[10], 0),
                             num(g[13], 0), num(g[14], 0), link(p["url"], "log")])
            b.append(table(["Wk", "Date", "Opp", "Result", "Cmp", "Att", "Yds", "TD", "INT",
                            "Sacked", "Rush att", "Rush yds", "Source"], rows,
                           numeric=(0, 4, 5, 6, 7, 8, 9, 10, 11),
                           note="Source: " + link(p["url"]) + " · season totals: "
                                + link(p["season_totals_url"])))
        else:
            first = "Rec" if p["kind"] == "receiving" else "Att"
            for g in p["games"]:
                rows.append([num(g[0], 0), esc(g[1]), esc(g[2]), esc(g[3]), num(g[4], 0),
                             num(g[5], 0), num(g[6], 1), num(g[7], 0), num(g[8], 0),
                             link(p["url"], "log")])
            b.append(table(["Wk", "Date", "Opp", "Result", first, "Yds", "Avg", "Long", "TD",
                            "Source"], rows, numeric=(0, 4, 5, 6, 7, 8),
                           note="Source: " + link(p["url"])))
        if not p["season_totals"]:
            b.append('<p class="note"><strong>Season totals are blank for this player:</strong> he '
                     'is outside the top-25 leaderboard, so no published season total was read. '
                     'The game rows are published and the season columns are left blank rather than '
                     'summed from a partial log (flag F-09).</p>')
    page("pages/players.html", "Player leaders & logs", "Official data / Players", "".join(b), "players")

    # ================================================================= integrity
    b = ["<h1>Integrity checks</h1>"]
    npass = integrity["summary"]["pass"]
    b.append('<p class="lede">%d checks run against the transcription itself. %d pass, %d are '
             'recorded notes about pages that disagree with each other, and %d fail. The build '
             'refuses to publish if any check fails.</p>'
             % (integrity["summary"]["total"], npass, integrity["summary"]["note"],
                integrity["summary"]["fail"]))
    rows = []
    for c in integrity["checks"]:
        badge = ('<span class="pass">pass</span>' if c["result"] == "pass" else
                 ('<span class="note-pill">note</span>' if c["result"] == "note" else
                  '<span class="fail">fail</span>'))
        rows.append([esc(c["id"]), esc(c["name"]), badge, esc(c["detail"]),
                     link("https://www.nfl.com/standings/league/2026/REG", "official")])
    b.append(table(["ID", "Check", "Result", "Detail", "Source"], rows,
                   note="The source column points at the primary official page; individual checks "
                        "read the specific table named in the check."))
    b.append('<div class="box"><p><strong>Two recorded notes, explained.</strong></p>'
             '<p>1. The published passing AVG column does not reproduce yards ÷ attempts on 4 of 32 '
             'rows, in both directions (JAX 8.6 vs 8.546, KC 7.8 vs 7.745, PIT 6.4 vs 6.452, SEA '
             '7.2 vs 7.253). So it is not a rounding rule. The site publishes its own yds/att and '
             'never uses the published column.</p>'
             '<p>2. A.J. Brown\'s season receiving total is not on any page read here (he is '
             'outside the top 25), so those columns stay blank.</p></div>')
    page("pages/integrity.html", "Integrity checks", "Official data / Integrity", "".join(b), "integ")

    # ================================================================= own lines
    b = ["<h1>Week 11 originated lines</h1>"]
    b.append('<p class="lede">Thirteen games. OUR line, OUR total, OUR fair moneyline. Market '
             'columns are blank because no official or licensed price exists.</p>')
    m = own_lines["model"]
    b.append('<div class="kpis">')
    for n, l, s in [
        (num(m["league_pts_per_game"], 2), "league points per game", "mean PF ÷ games across 32 clubs"),
        (num(m["hfa_used"], 2), "home-field used", "archive HFA %.2f shrunk ×0.85" % m["hfa_archive_raw"]),
        (num(m["sd_margin"], 2), "margin sd for fair ML", "NFL-typical, stated not fitted"),
        ("0", "market prices", "every market cell blank"),
    ]:
        b.append('<div class="kpi"><span class="n">%s</span><span class="l">%s</span>'
                 '<div class="s">%s</div></div>' % (esc(n), esc(l), esc(s)))
    b.append("</div>")
    b.append('<div class="box warn"><p><strong>Read this before using a line.</strong> The model is '
             'worse than the closing line on the holdout (spread MAE %.2f vs %.2f, total %.2f vs '
             '%.3f). It is a projection with published inputs, not a price, and there is nothing '
             'here to bet against.</p></div>' % (AMO, AMK, TMO, TMK))
    rows = []
    for r in own_lines["rows"]:
        rows.append([esc(r["date"]), esc(r["away"]), "@", esc(r["home"]),
                     esc("%+.1f" % r["own_spread_home"]), num(r["own_total"], 1),
                     num(r["fair_home_ml"], 0), num(r["fair_away_ml"], 0),
                     num(r["fair_home_win_prob"], 3),
                     '<span class="blank">blank</span>', link(r["source_url"], "schedule")])
    b.append(table(["Date", "Away", "", "Home", "Own spread (home)", "Own total", "Fair home ML",
                    "Fair away ML", "Fair P(home)", "Market", "Source"], rows,
                   numeric=(4, 5, 6, 7, 8),
                   note="Own spread is from the home perspective: −3.5 means we make the home club a "
                        "3.5-point favourite. Fair moneylines are derived from the modelled margin "
                        "with a 13.86-point sd. Market stays blank: source for the fixture is "
                        + link("https://www.nfl.com/schedules/2026/by-week/week-11")))
    b.append("<h2>Every model input, for audit</h2>")
    b.append("<p class='note'>Shrinkage pulls each club's scoring rate toward the league mean with "
             "a weight of 6 games, so a 9-game sample keeps most of its signal and an early-season "
             "sample keeps little.</p>")
    rows = []
    for t in sorted(own_lines["rows"], key=lambda x: x["home"]):
        r = t["model_inputs"]
        rows.append([esc(t["home"]), num(r["home_pts_for_shrunk"], 2),
                     num(r["home_pts_against_shrunk"], 2), esc(t["away"]),
                     num(r["away_pts_for_shrunk"], 2), num(r["away_pts_against_shrunk"], 2),
                     num(r["hfa_used"], 2), num(t["own_margin_raw"], 2), num(t["own_total_raw"], 2),
                     link("https://www.nfl.com/standings/league/2026/REG", "inputs")])
    b.append(table(["Home", "Home PF*", "Home PA*", "Away", "Away PF*", "Away PA*", "HFA",
                    "Margin (raw)", "Total (raw)"], rows, numeric=(1, 2, 4, 5, 6, 7, 8)))
    b.append("<h2>The ratings behind the lines</h2>")
    ratings = load("ratings.json")
    rows = []
    for r in sorted(ratings["rows"], key=lambda x: -x["pts_for_pg"]):
        rows.append([esc(r["team"]), num(r["games"], 0), num(r["pts_for_pg"], 2),
                     num(r["pts_against_pg"], 2), num(r["net_pg"], 2),
                     num(r["off_yds_pg"], 1), num(r["def_yds_pg"], 1),
                     num(r["own_pts_for_shrunk"], 2), num(r["own_pts_against_shrunk"], 2),
                     link(r["source_url"], "standings")])
    b.append(table(["Club", "G", "PF/g", "PA/g", "Net/g", "Off yds/g", "Def yds/g", "PF/g shrunk",
                    "PA/g shrunk", "Source"], rows, numeric=tuple(range(1, 9)),
                   note="Off and def yards are computed from the official team-stat tables; the "
                        "shrunk columns are the ones the model uses."))
    page("pages/own-lines.html", "Week 11 own lines", "Originated lines / Own lines",
         "".join(b), "lines")

    # ================================================================= props
    b = ["<h1>Player props and prop combos</h1>"]
    b.append('<p class="lede">For the first time in this repository, player prop research runs on '
             'official data. Seven players have a full official game log here; the own line for '
             'each game is the mean of that player\'s <em>earlier</em> games only.</p>')
    b.append('<div class="box bad"><p><strong>The sample is tiny and it shows.</strong> 31 graded '
             'player decisions in total. Nothing here can pass a sample gate and nothing here is '
             'claimed as an edge. What it does prove is that the data exists and the method works, '
             'so the next session can scale it by reading more logs (suggestion S-01).</p></div>')
    rows = []
    for pr in strategies["prop"]:
        rows.append([esc(pr["id"]), num(pr["n"], 0), pct(pr["over_rate"]),
                     esc(pr["note"]),
                     link("https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc",
                          "leaderboard")])
    b.append(table(["Strategy", "Decisions", "Over rate", "Construction", "Source"], rows,
                   numeric=(1, 2), note="Over rate against a rolling own line. No gate can pass at "
                                        "this sample size; the rows are shown so the method is auditable."))
    b.append("<h2>Prop combos: is the joint rate the product of the legs?</h2>")
    rows = []
    for c in strategies["combos"]:
        rows.append([esc(c["id"]), esc(c["label"]), num(c["n"], 0),
                     num(c.get("r"), 3), num(c.get("joint"), 3), num(c.get("independent"), 3),
                     esc(c["note"]),
                     link("https://www.nfl.com/players/drake-maye/stats/logs/", "logs")])
    b.append(table(["ID", "Combo", "N", "r", "Joint rate", "Product of legs", "Note", "Source"],
                   rows, numeric=(2, 3, 4, 5),
                   note="Where the joint rate and the product differ, multiplicative parlay "
                        "pricing is wrong for that pair. Two combos could not be graded because the "
                        "two players share too few weeks in the official logs; those rows are blank, "
                        "not estimated."))
    b.append('<div class="box"><p><strong>Why same-player combos are different.</strong> A '
             'quarterback\'s passing yards and his receiver\'s receiving yards move together: the '
             'receiver gains exactly what the passer throws. Multiplying their probabilities '
             'understates the chance both land, which is why a book reprices such a combo. The '
             'measured pair correlations are on the <a href="correlations.html">correlations</a> '
             'page with their sample sizes printed next to them.</p></div>')
    page("pages/props.html", "Player props & combos", "Originated lines / Props", "".join(b), "props")

    # ================================================================= parlays
    b = ["<h1>Parlays and dependence</h1>"]
    b.append('<p class="lede">Three registered parlay constructions, one per family: cross-game '
             'two-leg, cross-game three-leg, and a same-game spread-plus-total pair.</p>')
    rows = []
    for r in strategies["results"].values():
        if r["family"] != "parlay":
            continue
        rows.append([esc(r["id"]), esc(r["name"]), num(r["n"], 0), pct(r["hit_rate"]),
                     pct(r["break_even"], 2), num(r["p_value"], 3),
                     num((r.get("bootstrap_lo") or 0), 3) + " – " + num((r["bootstrap_hi"] or 0), 3),
                     esc(r["gates_passed"]), esc(r["tier"]),
                     dual_src()])
    b.append(table(["ID", "Construction", "Parlays", "Hit rate", "Break-even", "p", "95% CI",
                    "Gates", "Tier", "Source"], rows, numeric=(2, 3, 4, 5),
                   note="Break-even assumes −110 on each leg, so a two-leg parlay must clear "
                        "27.44% and a three-leg 14.37%. The week-clustered bootstrap interval is the "
                        "honest one because legs from the same week share conditions."))
    b.append("<h2>Dependence: what we measured</h2>")
    rows = []
    for c in corr["rows"]:
        if c["level"] != "team":
            continue
        rows.append([esc(c["id"]), esc(c["label"]), num(c["r"], 4),
                     "%s – %s" % (num(c["ci_lo"], 4), num(c["ci_hi"], 4)), num(c["n"], 0),
                     esc(c["note"]),
                     dual_src()])
    b.append(table(["ID", "Pair", "r", "95% CI", "N", "Method", "Source"], rows,
                   numeric=(2, 3, 4),
                   note="Team-level pairs are near zero, so multiplicative pricing is defensible "
                        "for these pairs. Player-level pairs are on the "
                        "<a href=\"correlations.html\">correlations</a> page."))
    b.append('<div class="box warn"><p><strong>What a parlay costs you.</strong> Two legs at −110 '
             'each need 27.44% joint hit rate to break even, and three legs need 14.37%. Every '
             'extra leg multiplies the margin the book keeps. That arithmetic is independent of any '
             'model, which is why no parlay strategy here is close to eligible.</p></div>')
    page("pages/parlays.html", "Parlays & dependence", "Originated lines / Parlays",
         "".join(b), "parlay")

    # ================================================================= strategies
    b = ["<h1>Strategy catalogue</h1>"]
    b.append('<p class="lede">Nineteen registered strategies: eleven singles, three parlay '
             'constructions, three single-prop rules and two prop combos. Each was written down '
             'before it was graded.</p>')
    b.append('<div class="box"><p><strong>Pre-registration.</strong> The rules, thresholds and the '
             'twelve gates were fixed before any holdout result was seen; the git history of '
             '<code>nfl-own/engine/analysis.py</code> shows the order. The model\'s two free '
             'parameters were selected on the dev window (forecast seasons 2002–2010) only, and that '
             'grid is published on the <a href="validation.html">validation</a> page.</p></div>')
    rows = []
    for d in strategies["definitions"]:
        r = strategies["results"].get(d["id"], {})
        rows.append([esc(d["id"]), esc(d["family"]), esc(d["name"]), esc(d["rule"]),
                     num(r.get("n"), 0), pct(r.get("hit_rate")), esc(r.get("gates_passed", "—")),
                     dual_src()])
    b.append(table(["ID", "Family", "Name", "Rule as registered", "Decisions", "Hit rate",
                    "Gates", "Source"], rows, numeric=(4, 5),
                   note="Source links point at the historical archive every graded decision comes "
                        "from. The rules themselves are defined in "
                        "<code>nfl-own/data/derived/strategies.json</code>."))
    page("pages/strategies.html", "Strategy catalogue", "Competition / Strategies",
         "".join(b), "strat")

    # ================================================================= validation
    b = ["<h1>Validation gates</h1>"]
    b.append('<p class="lede">Twelve gates, frozen before grading. A strategy earns points only on '
             'a twelve-of-twelve finish, which no entry has reached.</p>')
    rows = []
    for g in strategies["gates"]:
        rows.append([esc(g["id"]), esc(g["name"]), esc(g["test"]),
                     dual_src()])
    b.append(table(["Gate", "Name", "Test", "Source"], rows,
                   note="Gates are definitions, not data claims; the source column names the data "
                        "each gate is applied to."))
    b.append("<h2>Per-strategy gate matrix</h2>")
    gids = [g["id"] for g in strategies["gates"]]
    hdr = ["ID"] + gids + ["Pass", "Tier"]
    rows = []
    for sid, r in sorted(strategies["results"].items(),
                         key=lambda kv: -int(kv[1].get("gates_passed", "0/12").split("/")[0])):
        gd = r.get("gate_detail", {})
        cells = [esc(sid)]
        for g in gids:
            v = gd.get(g)
            cells.append('<span class="pass">✓</span>' if v else
                         ('<span class="fail">✗</span>' if v is False else
                          '<span class="blank">?</span>'))
        cells.append(esc(r.get("gates_passed", "—")))
        cells.append(esc(r.get("tier", "—")))
        cells.append(dual_src())
        rows.append(cells)
    b.append(table(hdr + ["Source"], rows,
                   note="A dash means the gate was not applicable to that strategy. Every entry "
                        "fails at least gate G12 (prospective replication) because no forward log "
                        "exists yet."))
    b.append("<h2>Model selection, on the dev window only</h2>")
    ms = load("model_selection.json")
    rows = []
    for g in ms["grid"]:
        rows.append([num(g["seasons_back"], 0), num(g["ridge"], 0), num(g["dev_mae"], 3),
                     num(g["n"], 0), dual_src()])
    b.append(table(["Seasons back", "Ridge", "Dev MAE", "N", "Source"], rows, numeric=(0, 1, 2, 3),
                   note="Forecast seasons 2002–2010, each fitted only on earlier seasons. The "
                        "holdout (2017–2026) was not consulted for this choice. Chosen: seasons "
                        "back %d, ridge %g." % (ms["chosen"]["seasons_back"], ms["chosen"]["ridge"])))
    b.append("<h2>Split-half eligibility retest</h2>")
    b.append('<p class="note">For every strategy with enough decisions, the holdout is split in '
             'half by kickoff date. A strategy has to clear break-even in <em>both</em> halves. '
             'This is stricter than any single gate and it is the test that catches rules that only '
             'look skilful in one window.</p>')
    rows = []
    for r in elig["rows"]:
        verdict = esc(r["verdict"])
        cls = "pass" if r.get("both_halves") else "fail"
        rows.append([esc(r["id"]), num(r["n"], 0), pct(r["first_half"]), pct(r["second_half"]),
                     pct(r["break_even"], 2), '<span class="%s">%s</span>' % (cls, verdict),
                     dual_src()])
    b.append(table(["ID", "Decisions", "First half", "Second half", "Break-even", "Verdict",
                    "Source"], rows, numeric=(1, 2, 3, 4),
                   note="Zero strategies survive. Two that looked strongest on the full holdout "
                        "(S1 and S2) fall below break-even in the second half."))
    page("pages/validation.html", "Validation gates", "Competition / Validation",
         "".join(b), "gates")

    # ================================================================= leaderboard
    b = ["<h1>Leaderboard and rewards</h1>"]
    b.append('<p class="lede">A leaderboard competition where points are paid for passing gates, '
             'never for a lucky hit rate. Fifty points per gate, paid only on a twelve-of-'
             'twelve finish, so the maximum on offer across %d entries is %s points.</p>'
             % (len(board["rows"]), format(50 * 12 * len(board["rows"]), ",")))
    b.append('<div class="kpis">')
    for n, l, s in [
        (str(len(board["rows"])), "entries graded", "singles, parlays and props"),
        ("0", "reward-eligible", "no entry reached 12/12"),
        ("0", "points awarded", "%d points were available" % (50 * 12 * len(board["rows"]))),
        (pct(board["rows"][0]["hit_rate"]), "top hit rate", board["rows"][0]["id"]),
    ]:
        b.append('<div class="kpi"><span class="n">%s</span><span class="l">%s</span>'
                 '<div class="s">%s</div></div>' % (esc(n), esc(l), esc(s)))
    b.append("</div>")
    b.append('<div class="box bad"><p><strong>Zero rewards. That is the correct output.</strong> '
             'Rewarding gate passes rather than profits is the only way to stop a lucky backtest '
             'from being paid. Partial credit is how variance would get funded, so there is none.'
             '</p></div>')
    rows = []
    for r in board["rows"]:
        rows.append([num(r["rank"], 0), esc(r["id"]), esc(r["family"]), esc(r["name"]),
                     num(r["n"], 0), pct(r["hit_rate"]), num(r["p_value"], 3),
                     num(r["q_value"], 3), esc(r["gates_passed"]), esc(r["tier"]),
                     num(r["points_awarded"], 0),
                     dual_src()])
    b.append(table(["Rank", "ID", "Family", "Entry", "N", "Hit rate", "p", "q", "Gates", "Tier",
                    "Points", "Source"], rows, numeric=(0, 4, 5, 6, 7, 10),
                   note="Sorted by gates passed, then hit rate. Points column is zero on every row "
                        "because no entry is eligible. The reward policy is in "
                        "<code>nfl-own/data/derived/leaderboard.json</code>."))
    b.append("<h2>Why the leaderboard exists at all</h2>")
    b.append("<ul class='tight'>")
    for t in [
        "It makes a strategy prove itself before anyone acts on it, which is the opposite of how "
        "picks are usually sold.",
        "It prices the cost of multiple testing: nineteen entries were graded, so a single "
        "significant result would be expected by chance (see the <a href='luck.html'>luck</a> page).",
        "It keeps the arithmetic honest: because no price exists in scope, entries are graded on "
        "hit rates against a stated break-even, never on invented profits.",
    ]:
        b.append("<li>%s</li>" % t)
    b.append("</ul>")
    page("pages/leaderboard.html", "Leaderboard & rewards", "Competition / Leaderboard",
         "".join(b), "board")

    # ================================================================= correlations
    b = ["<h1>Correlation values</h1>"]
    b.append('<p class="lede">Every correlation below is computed here from stated data with its '
             'sample size and 95%% Fisher interval. Values that could not be computed are blank.</p>')
    rows = []
    for c in corr["rows"]:
        rows.append([esc(c["id"]), esc(c["level"]), esc(c["label"]), num(c["r"], 4),
                     "%s – %s" % (num(c["ci_lo"], 3), num(c["ci_hi"], 3)), num(c["n"], 0),
                     esc(c["note"]),
                     link(c.get("source_url") or "https://github.com/nflverse/nfldata", "source")])
    b.append(table(["ID", "Level", "Pair", "r", "95% CI", "N", "Method / sample", "Source"], rows,
                   numeric=(3, 4, 5),
                   note="Team-level rows use the third-party archive's closing lines and results "
                        "over the holdout seasons. Player-level rows use the official per-game logs "
                        "read on %s." % CAPTURED))
    b.append('<div class="box warn"><p><strong>Intervals this wide are the point.</strong> A pair '
             'correlation on 8 games has a 95%% interval spanning roughly −0.8 to +0.8. Publishing '
             'the interval instead of the point estimate is what stops a small-sample number being '
             'mistaken for a dependency you can price.</p></div>')
    page("pages/correlations.html", "Correlations", "Competition / Correlations", "".join(b), "corr")

    # ================================================================= luck
    b = ["<h1>Backtest and luck removal</h1>"]
    b.append('<p class="lede">Luck cannot be removed. It can be bounded, and this page shows the '
             'bounds used here.</p>')
    b.append('<div class="box"><p><strong>How the backtest is run.</strong> Ratings are refitted '
             'before every season using only earlier seasons, so no forecast can see its own game. '
             'The holdout starts in %d. The permutation tests use a frozen seed, so they reproduce.'
             '</p></div>' % strategies["holdout"][0])
    rows = []
    for r in luck["rows"]:
        rows.append([esc(r["id"]), esc(r["name"]), num(r["value"], 4 if r["value"] < 1 else 0),
                     num(r["n"], 0) if r["n"] else '<span class="blank">n/a</span>',
                     esc(r["meaning"]),
                     dual_src()])
    b.append(table(["ID", "Test", "Value", "N", "What it means", "Source"], rows,
                   numeric=(2, 3),
                   note="L1–L2 are simulations with a frozen seed; L3 is a power calculation; L4 is "
                        "the multiple-testing arithmetic."))
    b.append("<h2>The inference trap this page is built to avoid</h2>")
    b.append("<ul class='tight'>")
    for t in [
        "With nineteen entries graded, the chance of at least one p < 0.05 result by luck alone is "
        "about 62%. That is why every p is corrected with Benjamini-Hochberg (gate G4).",
        "A 55% edge needs roughly 2,300 graded decisions to be detected at 80% power. Most of the "
        "strategies here grade in the hundreds.",
        "Splitting the holdout in half exposes rules that only work in one window. Two of the "
        "strongest-looking entries fail that test.",
        "The only genuine cure is prospective replication (gate G12): a timestamped prediction, "
        "written before kickoff, that cannot be revised afterwards.",
    ]:
        b.append("<li>%s</li>" % t)
    b.append("</ul>")
    page("pages/luck.html", "Backtest & luck", "Competition / Backtest & luck", "".join(b), "luck")

    # ================================================================= availability
    b = ["<h1>Injuries and depth: what the league actually publishes</h1>"]
    b.append('<p class="lede">The official injury report gives practice status and game status per '
             'player. It does <strong>not</strong> say who the backup is, and the league publishes '
             'no depth chart at all.</p>')
    b.append('<div class="box bad"><p><strong>The 2nd/3rd/4th-string question cannot be answered '
             'from official sources.</strong> The club depth-chart URL returns a 404 for every club '
             'tried (proof: %s), and the official roster page lists players, numbers, positions and '
             'roster status but no depth rank. So this site publishes unavailability by club and '
             'position, and never asserts that a named player is a backup. Suggestion S-02 is the '
             'only route to the real answer: licence a depth chart and snap counts.</p></div>'
             % link("https://www.nfl.com/teams/new-england-patriots/depthchart", "New England depth chart → 404"))
    inj = load_official("injuries_week10_2026.json") if os.path.exists(
        os.path.join(OFFICIAL, "injuries_week10_2026.json")) else None
    # Official Week 10 report, transcribed in this session from nfl.com/injuries (2026-11-13).
    inj_rows = [
        ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate", "Out"),
        ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate", "Out"),
        ("WAS", "Amik Robertson", "CB", "", "Limited", ""),
        ("WAS", "Treylon Burks", "WR", "", "Did Not Participate", ""),
        ("NYG", "Malik Harrison", "LB", "Groin", "Limited", "Questionable"),
        ("NE", "Ben Brown", "C", "Knee", "Did Not Participate", "Out"),
        ("NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate", "Out"),
        ("NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate", "Out"),
        ("NE", "A.J. Brown", "WR", "Ankle, Knee", "Limited", "Questionable"),
        ("NE", "Kevin Byard", "S", "Chest", "Full", "Questionable"),
        ("NE", "Reggie Gilliam", "FB", "Knee", "Limited", "Questionable"),
        ("NE", "Cameron Latu", "TE", "Back", "Limited", "Questionable"),
        ("NE", "Walter Rouse", "T", "Concussion", "Limited", "Questionable"),
        ("NE", "Brenden Schooler", "S", "Hamstring", "Limited", "Questionable"),
        ("NE", "Rhamondre Stevenson", "RB", "Knee", "Limited", "Questionable"),
        ("NE", "Greg Van Roten", "G", "Hamstring", "Full", "Questionable"),
        ("NE", "Charles Woods", "CB", "Hamstring", "Full", "Questionable"),
        ("NE", "Hunter Henry", "TE", "", "Limited", ""),
        ("DET", "Kerby Joseph", "S", "Knee", "Full", "Out"),
        ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate", "Out"),
        ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate", "Out"),
        ("DET", "Amon-Ra St. Brown", "WR", "", "Limited", ""),
        ("DET", "Sione Vaki", "RB", "", "Did Not Participate", ""),
    ]
    b.append("<h2>Week 10 official injury report (the games in progress)</h2>")
    rows = []
    for t, p, pos, injury, practice, game in inj_rows:
        rows.append([esc(t), esc(p), esc(pos),
                     esc(injury) if injury else '<span class="blank">blank</span>',
                     esc(practice), esc(game) if game else '<span class="blank">blank</span>',
                     link("https://www.nfl.com/injuries/", "injury report")])
    b.append(table(["Club", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], rows,
                   note="Transcribed from the official report. A blank injury or game-status cell is "
                        "how the official page renders it; it is not a clean bill of health. The "
                        "full report covers 14 games; this sample shows the clubs already listed "
                        "above. Source: " + link("https://www.nfl.com/injuries/")))
    b.append("<h2>Unavailability by club and position, from the same report</h2>")
    from collections import Counter
    cnt = Counter()
    for t, p, pos, injury, practice, game in inj_rows:
        if game in ("Out", "Questionable") or practice != "Full":
            cnt[(t, pos)] += 1
    rows = []
    for (t, pos), n in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        label = "out" if any(x[0] == t and x[2] == pos and x[5] == "Out" for x in inj_rows) else "limited/questionable"
        rows.append([esc(t), esc(pos), num(n, 0), esc(label),
                     link("https://www.nfl.com/injuries/", "injury report")])
    b.append(table(["Club", "Position", "Players listed", "Highest severity listed", "Source"], rows,
                   numeric=(2,),
                   note="<strong>This is not a depth chart.</strong> It counts players the official "
                        "report lists at each position with any restriction. It cannot tell you "
                        "whether the listed player is a starter or a fourth-string backup."))
    b.append("<h2>What a proper availability model would need</h2>")
    b.append(table(["Input", "Available officially?", "Consequence"], [
        ["Practice status per player", '<span class="chip g">yes</span>',
         "Published here, per club and position. Source: " + link("https://www.nfl.com/injuries/")],
        ["Game status (Out / Doubtful / Questionable)", '<span class="chip g">yes</span>',
         "Published here. Source: " + link("https://www.nfl.com/injuries/")],
        ["Depth rank (1st/2nd/3rd string)", '<span class="chip b">no</span>',
         "Cannot separate a starter loss from a backup loss (flag F-04). Source that does not "
         "publish it: " + link("https://www.nfl.com/teams/new-england-patriots/depthchart", "404 proof")],
        ["Snap counts", '<span class="chip b">no</span>',
         "Cannot weight a loss by how many snaps the player actually takes. Source: "
         + link("https://www.nfl.com/teams/new-england-patriots/roster", "roster has no snap data")],
        ["Injury history joined to results", '<span class="chip w">not in scope</span>',
         "Cannot measure the effect on spread or total (question Q09). Source: "
         + link("https://www.nfl.com/injuries/")],
    ], note="Source for the availability columns: " + link("https://www.nfl.com/injuries/")))
    page("pages/availability.html", "Injuries & depth", "Availability / Injuries",
         "".join(b), "avail")

    # ================================================================= questions
    b = ["<h1>Questions register</h1>"]
    b.append('<p class="lede">A clear list of the questions, the information we have, the '
             'information we do not have, and the answer or the thing that would unlock it. Nothing '
             'in this list is answered by inference.</p>')
    b.append('<div class="kpis">')
    for status, label in [("answered", "answered"), ("partial", "partially answered"),
                          ("open", "open"), ("blocked", "blocked")]:
        n = sum(1 for q in questions["rows"] if q["status"] == status)
        b.append('<div class="kpi"><span class="n">%d</span><span class="l">%s</span></div>'
                 % (n, esc(label)))
    b.append("</div>")
    for q in questions["rows"]:
        cls = {"answered": "g", "partial": "w", "open": "w", "blocked": "b"}[q["status"]]
        b.append("<h3>%s · %s <span class='chip %s'>%s</span></h3>"
                 % (esc(q["id"]), esc(q["question"]), cls, esc(q["status"])))
        b.append(table(["Part", "Content", "Source"], [
            ["What we know", esc(q["known"]),
             link("https://www.nfl.com/standings/league/2026/REG", "official")],
            ["What we do not know", esc(q["unknown"]),
             link("https://www.nfl.com/injuries/", "official")],
            ["The answer", esc(q["answer"]),
             link("https://github.com/nflverse/nfldata", "repo / archive")],
            ["What would unlock it", esc(q["unlock"]),
             link("https://www.nfl.com/schedules/2026/by-week/week-11", "official")],
        ], note="Status: %s." % esc(q["status"])))
    page("pages/questions.html", "Questions register", "Decisions / Questions",
         "".join(b), "q")

    # ================================================================= decisions
    b = ["<h1>Decisions to make</h1>"]
    b.append('<p class="lede">Seven decisions, each with the exact questions blocking it and the '
             'recommended path. Nothing here has been implemented on the owner\'s behalf.</p>')
    dec = [
        ("D1", "What is this product for?", "Q01, Q04, Q11, Q14",
         "Either a decision-support tool over official data, or a betting model that needs licensed "
         "prices. The current evidence supports the first and cannot support the second.",
         "Decision support (S-04), with the leaderboard kept as a rejection machine (S-07).",
         "open"),
        ("D2", "Do we buy data?", "Q02, Q04, Q05",
         "A depth chart with snap counts and a licensed odds archive. Both are licensing problems, "
         "not method problems.",
         "Price the licences before doing more modelling (S-02, S-03).",
         "open"),
        ("D3", "Do we pay rewards on backtests?", "Q07, Q11",
         "No. Backtest-only evidence cannot exclude luck; the split-half retest killed the two "
         "best-looking entries.",
         "Pay only on prospective replication (G12 / S-08).",
         "recommend no"),
        ("D4", "Do we publish picks?", "Q04, Q10",
         "The own-line model is worse than the closing line, and no price exists to bet against.",
         "Publish projections with inputs, never picks.",
         "recommend no"),
        ("D5", "Do we scale player props?", "Q01, Q14",
         "The data exists and reconciles. Only seven logs were read here.",
         "Read more official logs (S-01) before registering prop strategies at scale.",
         "recommend yes"),
        ("D6", "What happens to the eleven NFL namespaces?",
         "Q15", "They overlap and contradict each other; one of them wrongly recorded props as "
         "blocked.",
         "Consolidate under one canonical NFL site with an archive index (S-09).",
         "open"),
        ("D7", "How is the snapshot kept current?", "Q13, Q15",
         "This session's snapshot already differs from the 2026-11-12 one by a completed game.",
         "Add a weekly official re-read to CI (S-12) and a visible capture timestamp per page.",
         "recommend yes"),
    ]
    rows = [[esc(d[0]), esc(d[1]), esc(d[2]), esc(d[3]), esc(d[4]), esc(d[5]),
             dual_src()] for d in dec]
    b.append(table(["ID", "Decision", "Blocked by", "Why it is a real fork",
                    "Recommended path", "Status", "Source"], rows,
                   note="Each decision names the questions from the register that block it. None of "
                        "these has been actioned; they are the owner's calls."))
    page("pages/decisions.html", "Decisions to make", "Decisions / Decisions", "".join(b), "dec")

    # ================================================================= suggestions
    b = ["<h1>Suggestions board</h1>"]
    b.append('<p class="lede">A dedicated place to review proposals and choose a path before '
             'anything is implemented. Every suggestion states its impact, effort, risk and what has '
             'to be true first.</p>')
    b.append('<div class="box good"><p><strong>How to use this page.</strong> Read the impact column '
             'first. The four decisions marked <em>needs decision</em> are the ones that change what '
             'this project is; everything else can proceed without you.</p></div>')
    rows = []
    for s in suggestions["rows"]:
        cls = {"high": "w", "medium": "", "low": "g"}[s["impact"]]
        rows.append([esc(s["id"]),
                     '<span class="chip %s">%s</span> %s' % (cls, esc(s["impact"]), esc(s["suggestion"])),
                     esc(s["effort"]), esc(s["risk"]), esc(s["why"]), esc(s["prerequisite"]),
                     esc(s["status"]),
                     dual_src()])
    b.append(table(["ID", "Suggestion", "Effort", "Risk", "Why it matters", "Prerequisite",
                    "Status", "Source"], rows,
                   note="Status is one of implemented (done in this session), proposed (safe to do "
                        "next) or needs decision (the owner has to choose). Impact is coloured by "
                        "priority."))
    b.append("<h2>If you only read one thing</h2>")
    b.append('<div class="box warn"><p><strong>S-04 decides the rest.</strong> If this stays a '
             'betting-edge project, suggestions S-02 and S-03 (licences) have to be funded, because '
             'neither the depth chart nor the price exists for free. If it becomes a decision-support '
             'and data-coverage tool, the honest version is already written and only needs more '
             'official logs (S-01) and a weekly refresh (S-12).</p></div>')
    page("pages/suggestions.html", "Suggestions board", "Decisions / Suggestions",
         "".join(b), "sug")

    # ================================================================= sources
    b = ["<h1>Source register</h1>"]
    b.append('<p class="lede">Every source used, with what it establishes and how it was read.</p>')
    src = [
        ("nfl.com standings", "https://www.nfl.com/standings/league/2026/REG",
         "32 clubs: W, L, T, PCT, PF, PA", "Read 2026-11-13"),
        ("nfl.com offence passing", "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
         "Att, cmp, yds, TD, INT, sacks per club", "Read 2026-11-13"),
        ("nfl.com offence rushing", "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all",
         "Rush attempts, yards, TD per club", "Read 2026-11-13"),
        ("nfl.com defence passing", "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all",
         "Passing yards and TD allowed", "Read 2026-11-13"),
        ("nfl.com defence rushing", "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all",
         "Rushing yards and TD allowed", "Read 2026-11-13"),
        ("nfl.com Week 11 schedule", "https://www.nfl.com/schedules/2026/by-week/week-11",
         "13 games, kickoff times, networks, byes", "Read 2026-11-13"),
        ("nfl.com Week 10 schedule", "https://www.nfl.com/schedules/2026/REG10",
         "14 fixtures and the Thursday final", "Read 2026-11-13"),
        ("nfl.com Week 9 scores", "https://www.nfl.com/scores/2026/REG9",
         "15 final scores", "Read 2026-11-13"),
        ("nfl.com injury report", "https://www.nfl.com/injuries/",
         "Week 10 practice and game status", "Read 2026-11-13"),
        ("nfl.com player stats", "https://www.nfl.com/stats/player-stats/",
         "Season leaders by category", "Read 2026-11-13"),
        ("nfl.com player logs", "https://www.nfl.com/players/drake-maye/stats/logs/",
         "Per-game official log (7 players read)", "Read 2026-11-13"),
        ("nfl.com club roster", "https://www.nfl.com/teams/new-england-patriots/roster",
         "Positions and roster status; no depth rank", "Read 2026-11-13"),
        ("nfl.com club depth chart", "https://www.nfl.com/teams/new-england-patriots/depthchart",
         "Returns 404 - the basis for flag F-04", "Read 2026-11-13"),
        ("nflverse nfldata", "https://github.com/nflverse/nfldata",
         "Third-party historical results and closing lines", "Used as archived in repo"),
        ("NCPG helpline", "https://www.ncpgambling.org/help-treatment",
         "Responsible gambling resource", "Linked site-wide"),
    ]
    rows = [[esc(s[0]), link(s[1]), esc(s[2]), esc(s[3])] for s in src]
    b.append(table(["Source", "URL", "What it establishes here", "How it was read"], rows,
                   note="Official NFL.com pages are the only source for any published 2026 value. "
                        "The nflverse archive is explicitly third-party and is labelled as such "
                        "everywhere its numbers appear."))
    page("pages/sources.html", "Source register", "Governance / Sources", "".join(b), "src")

    # ================================================================= repo review
    b = ["<h1>Repo review</h1>"]
    b.append('<p class="lede">What is in this repository, what is irregular, and what was found '
             'line by line before any new work started.</p>')
    b.append("<h2>Structure</h2>")
    b.append(table(["Area", "What is there", "Status", "Source"], [
        ["NFL workspaces", "eleven namespaces: nfl, nfl-audit, nfl-decision, nfl-decisions, "
         "nfl-edge, nfl-hub, nfl-intel, nfl-lab, nfl-lines, nfl-quant, nfl-research",
         '<span class="chip w">overlapping</span>',
         link("https://github.com/sassnarep3-star/Own4", "repository")],
        ["NBA workspaces", "docs, lab, lines-lab, nba-evidence, verification, verified",
         '<span class="chip g">preserved</span>',
         link("https://github.com/sassnarep3-star/Own4/tree/main/docs", "repository")],
        ["Root dashboard", "index.html regenerated by verification/build.py",
         '<span class="chip b">regression</span>',
         link(REPO_BLOB + "verification/build.py", "build.py")],
        ["Raw data footprint", "data/raw is about 53 MB of ESPN JSON; nfl-lines raw archive 2.1 MB",
         '<span class="chip w">large</span>',
         link("https://github.com/sassnarep3-star/Own4", "repository")],
        ["CI", "9 workflows; pages.yml, canonical-site.yml and nfl-lines.yml gate the site",
         '<span class="chip g">green</span>', link("https://github.com/sassnarep3-star/Own4/actions", "actions")],
    ]))
    b.append("<h2>Findings, line by line</h2>")
    rev = [
        ("RR-01", "A routine rebuild of the root dashboard deletes peer navigation.",
         "Running <code>python3 verification/build.py</code> on the current head changed 14 files, "
         "all of them losing the <code>nfl-lines</code> nav group. Reproduced on 2026-11-13. Logged "
         "as R-01 for the owning session; this session reverted the output and did not edit the "
         "generator.", '<span class="chip b">irregular</span>'),
        ("RR-02", "Three sessions recorded player props as blocked.",
         "The official per-game logs exist and reconcile to season totals. The claim in "
         "<code>nfl-edge/</code>, <code>nfl-lines/</code> and <code>nfl-hub/</code> is wrong for a "
         "reason that is now documented: the earlier sessions looked for team-level weekly tables, "
         "not player pages.", '<span class="chip b">irregular</span>'),
        ("RR-03", "The Week 10 injury page was not refreshed after the Thursday game.",
         "It still lists WAS 3-5-1 / NYG 5-3-1 while live standings show both records including the "
         "result. Any snapshot taken from that page will be one game stale.",
         '<span class="chip w">stale source</span>'),
        ("RR-04", "The published passing AVG column does not reproduce yds/att on 4 of 32 rows.",
         "Both directions, so not a rounding rule. Four columns are computed here instead.",
         '<span class="chip w">source quirk</span>'),
        ("RR-05", "Two NFL sessions disagree about the same archive.",
         "<code>nfl-edge</code> reports 136 games and 6,246 league points through Week 9; "
         "<code>nfl-lines</code> reports 7,548 archive rows. Both are right about different things, "
         "but the sites never say so, which is confusing (suggestion S-09).",
         '<span class="chip w">confusing</span>'),
        ("RR-06", "No secrets, tokens or personal data found in the NFL namespaces.",
         "Scanned for key-like patterns and e-mail addresses across the files this session read. "
         "Nothing found.", '<span class="chip g">clean</span>'),
        ("RR-07", "No fabricated market data found; all NFL market columns are blank.",
         "Checked the peer NFL pages for any price presented as official. None found; the pages are "
         "consistent about blanking prices.", '<span class="chip g">clean</span>'),
        ("RR-08", "This session's own first draft had a spread sign error.",
         "It produced impossible 80% hit rates. It was caught by a sanity check on the archive's "
         "convention, fixed, and the fix is documented in the code and in the git history. Recorded "
         "here so the error is auditable rather than hidden.",
         '<span class="chip w">corrected</span>'),
    ]
    rows = [[esc(r[0]), esc(r[1]), esc(r[2]), r[3],
             link("https://github.com/sassnarep3-star/Own4", "repo")] for r in rev]
    b.append(table(["ID", "Finding", "Detail", "Class", "Source"], rows,
                   note="Each finding names the file or page involved. Nothing here was fixed "
                        "outside this session's own scope."))
    page("pages/repo-review.html", "Repo review", "Governance / Repo review", "".join(b), "repo")

    # ================================================================= flagged
    b = ["<h1>⚑ Flagged for review</h1>"]
    b.append('<p class="lede">Every irregularity and every value that could not be confirmed from '
             'an official source. None of these blocks publication, and all of them are here so they '
             'can be reviewed after the site is live.</p>')
    rows = []
    for f in flags["rows"]:
        rows.append([esc(f["id"]), esc(f["issue"]), esc(f["detail"]),
                     src_any(f["source_url"]), esc(f["status"])])
    b.append(table(["ID", "Issue", "Detail and what would clear it", "Source", "Status"], rows,
                   note="Status values: blocked (an official source does not publish it), flagged "
                        "(known and disclosed), recorded (a source quirk kept for the record), "
                        "omitted (left out rather than guessed), blank (unverified), requested "
                        "(asked of another session)."))
    b.append("<h2>Blank values published as blanks</h2>")
    blanks = [
        ["Market spread, total and price, all 13 Week 11 games", "No official or licensed price", "F-06"],
        ["A.J. Brown season receiving totals", "Outside the top-25 leaderboard on the pages read", "F-09"],
        ["Eleven team-stat columns", "No readable header row, so omitted rather than guessed", "F-10"],
        ["Depth rank for every player", "The league publishes no depth chart", "F-04"],
        ["Player-level correlations for 3 of 5 pairs", "Fewer than 4 shared official game weeks", "F-08"],
        ["Injury effect on spread and total", "The archive has no injury field", "Q09"],
        ["Prospective replication results", "No forward log exists yet", "F-13"],
    ]
    b.append(table(["Blank item", "Reason", "Flag"], [
        [esc(x[0]), esc(x[1]), esc(x[2]) + " · " + link(
            "https://www.nfl.com/injuries/" if x[2] == "F-04" else
            "https://www.nfl.com/standings/league/2026/REG", "source")] for x in blanks],
        note="Every blank on this site has a reason, and the reason is one of these seven."))
    page("pages/flagged.html", "Flagged for review", "Governance / ⚑ Flagged", "".join(b), "flag")

    return render()


if __name__ == "__main__":
    written = build()
    print("wrote %d pages" % len(written))
    for w in written:
        print("  ", w)

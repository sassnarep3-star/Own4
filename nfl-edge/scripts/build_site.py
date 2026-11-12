#!/usr/bin/env python3
"""Build the nfl-edge static site from the JSON datasets.

Every table row is emitted through row() which REQUIRES a source URL; the build
refuses to write a page with an unsourced row. verify_site.py then re-reads the
written HTML and enforces the same rule plus link integrity.

Run:  python3 nfl-edge/scripts/build_site.py
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)              # nfl-edge/
D = os.path.join(SITE, "data")

SRC_LABEL = {
    "https://www.nfl.com": "NFL.com",
}

NAV = [
    ("Overview", [
        ("index.html", "Dashboard", "dash"),
        ("pages/executive-summary.html", "Executive summary", "exec"),
    ]),
    ("Official data", [
        ("pages/standings.html", "Standings", "stand"),
        ("pages/team-stats.html", "Team statistics", "stats"),
        ("pages/scores.html", "Games & scores", "games"),
        ("pages/schedule.html", "Week 10 schedule", "sched"),
    ]),
    ("Own lines", [
        ("pages/own-lines.html", "Originated lines", "lines"),
        ("pages/correlations.html", "Correlation", "corr"),
    ]),
    ("Strategies", [
        ("pages/strategies.html", "Signal catalogue", "strat"),
        ("pages/singles.html", "Single bets", "singles"),
        ("pages/parlays.html", "Parlays", "parlays"),
        ("pages/props.html", "Player props", "props"),
        ("pages/validation.html", "Validation & luck", "valid"),
        ("pages/leaderboard.html", "Leaderboard & rewards", "board"),
    ]),
    ("Availability", [
        ("pages/availability.html", "Injuries & backups", "avail"),
    ]),
    ("Decision support", [
        ("pages/requirements.html", "Requirements", "req"),
        ("pages/decisions.html", "Questions & decisions", "dec"),
        ("pages/suggestions.html", "Suggestions", "sugg"),
    ]),
    ("Governance", [
        ("pages/sources.html", "Source register", "src"),
        ("pages/integrity.html", "Integrity checks", "integ"),
        ("pages/repo-review.html", "Repo review", "repo"),
        ("pages/flagged.html", "Flagged for review", "flags"),
    ]),
]

FOOTER = """<footer>
<p><strong>Own4 &middot; NFL Edge</strong> &mdash; analytical research only, <strong>not wagering advice</strong>.
Snapshot 2026-11-12. Every table row links to the source it was read from; every value that could not be
confirmed from an official source is blank and listed on the <a href="{p}pages/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &middot;
<a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">NCPG &nearr;</a></p>
</footer>"""

CSS = os.path.join(SITE, "assets", "style.css")


def load(name):
    with open(os.path.join(D, name)) as f:
        return json.load(f)


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def fmt(v, nd=None):
    if v is None or v == "":
        return '<span class="blank">blank</span>'
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float) and nd is not None:
        return ("%." + str(nd) + "f") % v
    return esc(v)


def src(url, label=None):
    if not url:
        raise ValueError("row without source url")
    if not url.startswith("http"):
        raise ValueError("source must be absolute: %r" % url)
    if label:
        text = label
    elif url.startswith("https://www.nfl.com/"):
        text = "nfl.com"
    elif "github.com/sassnarep3-star/Own4/blob/main/" in url:
        text = url.rsplit("/", 1)[-1] + " \u2197"
    elif "github.com" in url:
        text = "repository \u2197"
    else:
        text = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return '<a class="src" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(text))


def table(headers, rows, cap=None, cls="", numeric=(), note=None, source_header=None):
    """rows: list of lists; the LAST cell of each row must be a pre-rendered source link."""
    out = ['<div class="tw">']
    out.append('<table%s>' % (' class="%s"' % cls if cls else ""))
    if cap:
        out.append("<caption>%s</caption>" % cap)
    out.append("<thead><tr>" + "".join("<th>%s</th>" % h for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        if not r or "<a class=\"src\"" not in r[-1]:
            raise ValueError("unsourced table row in %r: %r" % (cap, r))
        cells = []
        for i, c in enumerate(r):
            cl = ' class="num"' if i in numeric else ""
            cells.append("<td%s>%s</td>" % (cl, c))
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    if note:
        out.append('<p class="note">%s</p>' % note)
    return "\n".join(out)


def badge(text, kind="ok"):
    return '<span class="badge %s">%s</span>' % (kind, esc(text))


def page(path, title, crumb, body, active, desc):
    depth = path.count("/")
    prefix = "../" * depth
    nav = []
    for group, items in NAV:
        nav.append('<div class="grp">%s</div>' % group)
        for href, label, key in items:
            cls = "nav active" if key == active else "nav"
            nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, label))
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s &middot; NFL Edge</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(p)sassets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(p)sindex.html">NFL Edge <span>Own4 &middot; line origination</span></a>
  <div class="tag">Snapshot <strong>2026-11-12</strong> &middot; official sources only</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <a class="flaglink" href="%(p)spages/flagged.html">&#9873; 16 items flagged for review</a>
  <div class="sidefoot">0 of 4 strategies qualify<br>0 reward points awarded</div>
</aside>
<main class="main" id="main">
<div class="crumb">%(crumb)s</div>
%(body)s
%(footer)s
</main>
</div>
<script src="%(p)sassets/app.js" defer></script>
</body>
</html>
""" % {"title": esc(title), "desc": esc(desc), "p": prefix, "nav": "".join(nav), "crumb": crumb,
       "body": body, "footer": FOOTER.format(p=prefix)}
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full) or SITE, exist_ok=True)
    with open(full, "w") as f:
        f.write(doc)
    return path


# --------------------------------------------------------------------------- pages
def build_dashboard():
    st = load("official_standings.json")["rows"]
    integ = load("integrity.json")
    res = load("results.json")
    own = load("own_lines_2026.json")["rows"]
    inj = load("injuries_week10.json")
    q = load("questions.json")
    flags = load("flags.json")["flags"]
    m = res["metrics"]
    n_open = sum(1 for x in q["questions"] if x["status"] != "ANSWERED")
    body = []
    body.append('<h1>NFL Edge &mdash; own lines, validated signals, and the evidence that most of them fail</h1>')
    body.append('<p class="lede">A decision dashboard for originating NFL lines from official league data. '
                'It answers three questions in order: what is true (sourced data), what we built from it '
                '(own lines and strategies), and what survived validation (almost nothing). '
                '<strong>Headline: 0 of 4 registered strategies qualify. Our spread model beats a naive '
                'baseline but loses to the closing line by 0.63 points, so nothing here is a price to bet.</strong></p>')

    cards = [
        ("136", "official games archived, weeks 1-9", ""),
        ("32", "clubs reconciled: 0 mismatches", ""),
        ("14", "Week 10 games with own lines", "accent"),
        ("275", "players on the official Week 10 injury report", ""),
        ("10", "pre-registered validation gates", ""),
        ("0/4", "strategies qualified", "warn"),
        ("0", "reward points awarded", "warn"),
        ("%d" % integ["n_pass"] + "/" + str(integ["n_checks"]), "integrity checks passing", ""),
    ]
    body.append('<div class="cards">' + "".join(
        '<div class="card %s"><b>%s</b><span>%s</span></div>' % (k, v, d) for v, d, k in cards) + "</div>")

    body.append('<div class="panel warn"><strong>Read this before anything else.</strong> '
                'The model is less accurate than the market it would have to beat (spread MAE %.3f vs %.3f points). '
                'No strategy clears the gates, no reward points are payable, and 2026 market prices do not exist in '
                'this repository, so every 2026 edge and ROI cell is deliberately blank. '
                '<a href="pages/leaderboard.html">See the leaderboard &rarr;</a></div>'
                % (m["spread_mae"]["own_model"], m["spread_mae"]["market_closing_line"]))

    # headline results table
    rows = []
    for s in res["strategies"]:
        rows.append([
            "<strong>%s</strong>" % esc(s["id"]),
            esc(s["label"]),
            fmt(s["n_bets"]),
            (("%.2f%%" % (s["roi"] * 100)) if s["roi"] is not None else fmt(None)),
            ("[%.2f%%, %.2f%%]" % (s["roi_ci95"][0] * 100, s["roi_ci95"][1] * 100)) if s["roi_ci95"] else fmt(None),
            fmt(s["permutation_p"]),
            "%d/%d" % (s["gates_passed"], s["gates_total"]),
            badge(s["tier"], "ok" if s["tier"] == "Qualified" else ("warn" if "Bronze" in s["tier"] else "fail")),
            src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json"),
        ])
    body.append("<h2>Leaderboard, holdout 2017&ndash;2025, frozen configuration</h2>")
    body.append(table(["ID", "Strategy", "Bets", "ROI", "Bootstrap 95% CI", "Placebo p", "Gates", "Tier", "Source"],
                      rows, cap="Four registered strategies, graded unchanged against closing lines",
                      numeric=(2, 3, 4, 5, 6)))
    body.append('<p class="note">Closing lines are a third-party archive (no official NFL odds source exists &mdash; '
                'flag F-01). Negative ROI of roughly the vig is the expected result for public-data rules '
                'against efficient prices; it is published unchanged.</p>')

    # week 10 own lines preview
    rows = []
    for r in own:
        rows.append([
            esc(r["date"]), esc(r["kickoff_et"]),
            "%s at %s" % (esc(r["away"]), esc(r["home"])),
            ("%.1f" % r["own_spread_home"]), ("%.1f" % r["own_total"]),
            esc(r["own_ml_home"]), esc(r["own_ml_away"]),
            fmt(None), fmt(None),
            src(r["source_url"]),
        ])
    body.append("<h2>Originated lines &mdash; official 2026 Week 10 slate</h2>")
    body.append(table(["Date", "Kickoff ET", "Game", "Own spread (home)", "Own total", "Own ML home", "Own ML away",
                       "Market spread", "Market total", "Source"], rows,
                      cap="Own lines from official team statistics; market columns blank by design",
                      numeric=(3, 4, 5, 6, 7, 8)))
    body.append('<p class="note">A negative home spread means the home team is favoured. Market columns are blank '
                'because no official or licensed 2026 price archive is available; they are not zero and not estimated. '
                '<a href="pages/own-lines.html">Full model and assumptions &rarr;</a></p>')

    # decision status
    rows = []
    for d in q["decisions_blocked"]:
        rows.append(["<strong>%s</strong>" % esc(d["id"]), esc(d["decision"]), badge(d["status"], "fail" if d["status"].startswith(("BLOCKED", "NO")) else "warn"),
                     esc(", ".join(d["blocking_questions"])), esc(d["what_would_unblock"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/questions.json")])
    body.append("<h2>What cannot be decided yet</h2>")
    body.append(table(["Decision", "Question", "Status", "Blocked by", "What would unblock it", "Source"], rows,
                      cap="%d of %d register questions are not answered" % (n_open, len(q["questions"]))))
    body.append('<p class="note">The full register separates what we know from what we do not, question by question: '
                '<a href="pages/decisions.html">%d questions &rarr;</a> &middot; '
                '<a href="pages/suggestions.html">16 suggested changes &rarr;</a></p>' % len(q["questions"]))

    # top flags
    rows = []
    for f in flags[:5]:
        rows.append(["<strong>%s</strong>" % esc(f["id"]), esc(f["area"]), esc(f["item"]), esc(f["severity"]),
                     src(f["source_url"])])
    body.append("<h2>Flagged for review</h2>")
    body.append(table(["ID", "Area", "Finding", "Severity", "Source"], rows,
                      cap="First five of 16 &mdash; full list on the Flagged for review page"))
    body.append('<p class="note"><a href="pages/flagged.html">All 16 flagged items &rarr;</a> '
                'Flagged items do not block publication; they block specific claims.</p>')

    return page("index.html", "Dashboard", "Overview / Dashboard", "\n".join(body), "dash",
                "NFL line origination research dashboard: official 2026 data, own lines, pre-registered validation gates and a leaderboard that awards no points because nothing qualifies.")


def build_exec():
    q = load("questions.json")
    res = load("results.json")
    m = res["metrics"]
    own = load("own_lines_2026.json")
    body = ['<h1>Executive summary</h1>',
            '<p class="lede">What was built, what the evidence says, what is blocked, and what to do next. '
            'One screen, no adjectives.</p>']

    rows = [
        ["Data", "2026 standings, 32 clubs", "Read from nfl.com; PF&minus;PA reproduces NET PTS on all 32 rows and league PF = league PA = 6,246.",
         badge("OFFICIAL"), src("https://www.nfl.com/standings/")],
        ["Data", "2026 team statistics, offence and defence", "32 clubs x scoring/passing/rushing on both sides of the ball; six league-wide identities reconcile exactly.",
         badge("OFFICIAL"), src("https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all")],
        ["Data", "Game archive, weeks 1&ndash;9", "136 games. 16 were missing from the peer archive and were restored from official week pages; the archive now reproduces every club's record and points for/against exactly.",
         badge("RECONCILED"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/integrity.json")],
        ["Data", "Week 10 injury report", "275 players across 28 clubs with practice and game status. No depth chart exists in the source.",
         badge("OFFICIAL"), src("https://www.nfl.com/injuries/")],
        ["Lines", "Own lines, Week 10", "14 games: spread, total, projected points and fair moneyline, from official team stats.",
         badge("DERIVED"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/own_lines_2026.json")],
        ["Evidence", "Forecast accuracy", "Spread MAE %.3f (own) vs %.3f (closing line) vs %.3f (naive zero margin). Total MAE %.3f vs %.3f vs %.3f."
         % (m["spread_mae"]["own_model"], m["spread_mae"]["market_closing_line"], m["spread_mae"]["naive_zero_margin"],
            m["total_mae"]["own_model"], m["total_mae"]["market_closing_line"], m["total_mae"]["naive_holdout_mean"]),
         badge("NEGATIVE", "fail"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Evidence", "Strategy results", "S1 &minus;3.12% (n=1,540), S2 &minus;5.32% (n=1,187), S3 &minus;8.45% (n=2,060), S4 &minus;15.74% (n=155). No gate set is passed.",
         badge("NEGATIVE", "fail"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Evidence", "Luck", "Week-clustered bootstrap CIs, matched-random placebo (p 0.37&ndash;0.63), season stability, residual persistence +0.40. Nothing survives.",
         badge("MEASURED"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/correlations.json")],
        ["Blocked", "Player props and prop combos", "No official player-game logs and no prop prices. Correlation cells are blank, not estimated.",
         badge("BLOCKED", "fail"), src("https://www.nfl.com/stats/player-stats/")],
        ["Blocked", "Starter vs 2nd/3rd/4th string", "The official source publishes no depth chart (the depth-chart URL returns 404) and no snap counts. No starter/backup claim is made anywhere.",
         badge("BLOCKED", "fail"), src("https://www.nfl.com/teams/washington-commanders/roster")],
        ["Blocked", "Any 2026 price or edge", "No official NFL odds source exists; no licensed 2026 price archive is in scope. Market cells are blank.",
         badge("BLOCKED", "fail"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ]
    body.append("<h2>One line per finding</h2>")
    body.append(table(["Category", "Item", "Finding", "Status", "Source"], rows))

    body.append("<h2>The three decisions this evidence supports</h2>")
    body.append('<ol class="tight">'
                '<li><strong>Do not publish picks or prices.</strong> Our own lines are a model output; the market '
                'they would be compared with does not exist in this repository, and our model is worse than the '
                'closing line on accuracy anyway.</li>'
                '<li><strong>Keep the leaderboard as a rejection machine.</strong> Its job is to stop a lucky '
                'backtest from becoming a paid strategy. Today it rejected everything, which is the correct '
                'output for public-data rules against efficient prices.</li>'
                '<li><strong>Buy data or change the question.</strong> The two blocked requirements (props and '
                'starter/backup effects) are blocked by licensing, not by method. Either licence the data or '
                'redefine the product as a decision-support and data-coverage tool.</li></ol>')

    body.append('<h2>What to read next</h2>')
    body.append('<p><a href="decisions.html">Questions and decisions</a> (what is answered, what is not, and '
                'what would unlock each one) &middot; <a href="suggestions.html">Suggestions</a> (16 changes '
                'with impact, effort, risk and prerequisites) &middot; <a href="flagged.html">Flagged for '
                'review</a> (16 irregularities and caveats) &middot; <a href="validation.html">Validation and '
                'luck</a> (the ten gates).</p>')

    rows = []
    for s in q["decisions_blocked"]:
        rows.append(["<strong>%s</strong>" % esc(s["id"]), esc(s["decision"]), esc(s["status"]),
                     esc(", ".join(s["blocking_questions"])), esc(s["what_would_unblock"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/questions.json")])
    body.append("<h2>Decisions blocked</h2>")
    body.append(table(["ID", "Decision", "Status", "Blocked by questions", "Unlock condition", "Source"], rows))
    return page("pages/executive-summary.html", "Executive summary", "Overview / Executive summary",
                "\n".join(body), "exec", "One-screen executive summary of the NFL edge research: findings, negative results, blocked items and next steps.")


def build_standings():
    st = load("official_standings.json")
    rows = []
    for r in st["rows"]:
        rows.append([
            '<a href="https://www.nfl.com/teams/%s/" target="_blank" rel="noopener">%s</a>' % (esc(r["name"].lower().replace(" ", "-")), esc(r["name"])),
            esc(r["conference"]), esc(r["division"]),
            "%d-%d-%d" % (r["w"], r["l"], r["t"]), ("%.3f" % r["pct"]),
            esc(r["pf"]), esc(r["pa"]), esc(r["net_pts"]),
            esc(r["home"]), esc(r["road"]), esc(r["div"]), esc(r["conf"]), esc(r["strk"]),
            src(st["source_url"]),
        ])
    body = ['<h1>2026 standings</h1>',
            '<p class="lede">All 32 clubs as published on nfl.com, with the league\'s own column definitions. '
            'The table is reproduced row for row; %s</p>' % '<em>nothing is computed except the checks described below.</em>']
    body.append(table(["Team", "Conf", "Division", "W-L-T", "PCT", "PF", "PA", "Net", "Home", "Road", "Div", "Conf", "Strk", "Source"],
                      rows, cap="Official 2026 regular-season standings, division view", numeric=(3, 4, 5, 6, 7)))
    body.append('<div class="panel info"><h3>What was checked on these rows</h3><ul class="tight">'
                '<li>PF &minus; PA equals the published NET PTS on all 32 rows.</li>'
                '<li>Sum of PF (6,246) equals sum of PA (6,246); sum of W (135) equals sum of L (135) with 2 ties.</li>'
                '<li>Sum of PF also equals the league total on the official offence-scoring page (6,246), so the two official pages agree.</li>'
                '<li>W-L-T, PF and PA recomputed from the 136-game archive match every club with 0 mismatches.</li>'
                '</ul><p class="note">These are consistency checks on the transcription. They cannot detect a typo that '
                'is internally consistent; that is flag F-10.</p></div>')
    body.append('<p class="note">Column meaning as defined in the page&rsquo;s own legend: PF total points for, PA total '
                'points against, NET PTS net points, STRK current streak. Team names link to the official club page.</p>')
    return page("pages/standings.html", "Standings", "Official data / Standings", "\n".join(body), "stand",
                "Official 2026 NFL standings with integrity checks: net points, league totals and archive reconciliation.")


def build_team_stats():
    off = load("team_stats_2026.json")
    dfn = load("team_stats_defense_2026.json")
    dmap = {r["team"]: r for r in dfn["rows"]}
    rows = []
    for r in off["rows"]:
        d = dmap[r["team"]]
        rows.append([
            esc(r["name"]), esc(r["record"]), esc(r["g"]),
            esc(r["pts"]), ("%.1f" % r["pts_pg"]), esc(r["pass_yds"]), esc(r["pass_td"]), esc(r["rush_yds"]), esc(r["rush_td"]),
            esc(d["pts"]), ("%.1f" % d["pts_pg"]), esc(d["pass_yds"]), esc(d["rush_yds"]),
            src(off["source_url"]),
        ])
    body = ['<h1>2026 team statistics</h1>',
            '<p class="lede">Offence and defence side by side, straight from the official team-statistics pages. '
            'These are the only inputs to the line model &mdash; no external ratings, no market data.</p>']
    body.append(table(["Team", "Rec", "G", "PF", "PF/G", "Pass yd", "Pass TD", "Rush yd", "Rush TD",
                       "PA", "PA/G", "Opp pass yd", "Opp rush yd", "Source"],
                      rows, cap="Official 2026 team offence and defence, through Week 9 (9 games per club)",
                      numeric=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)))
    body.append('<div class="panel info"><h3>Six league-wide identities, all exact</h3><ul class="tight">'
                '<li>Offence pass yards = defence pass yards allowed: 63,556</li>'
                '<li>Offence pass TD = defence pass TD allowed: 411</li>'
                '<li>Offence rush yards = defence rush yards allowed: 30,580</li>'
                '<li>Offence rush TD = defence rush TD allowed: 257</li>'
                '<li>League points for = league points against = 6,246</li>'
                '</ul><p class="note">Every offence row must equal the matching defence row league-wide. The fact that '
                'all six do is what makes the transcription credible.</p></div>')
    body.append("<h2>Rate splits used by the model</h2>")
    rows = []
    for r in off["rows"]:
        d = dmap[r["team"]]
        rows.append([esc(r["name"]), ("%.1f" % r["pass_yds_pg"]), ("%.1f" % r["rush_yds_pg"]),
                     ("%.1f" % d["pass_yds_pg"]), ("%.1f" % d["rush_yds_pg"]),
                     src(off["source_url_passing"])])
    body.append(table(["Team", "Pass yd/g", "Rush yd/g", "Opp pass yd/g", "Opp rush yd/g", "Source"], rows,
                      cap="Per-game splits (season totals divided by 9 games)", numeric=(1, 2, 3, 4)))
    body.append('<p class="note">Per-game values are season totals divided by the 9 games every club has played; '
                'that division is arithmetic on official totals, not a published NFL rate statistic.</p>')
    return page("pages/team-stats.html", "Team statistics", "Official data / Team statistics", "\n".join(body), "stats",
                "Official 2026 NFL team offence and defence statistics with six league-wide identity checks.")


def build_scores():
    g = load("games_2026.json")
    rows = []
    for r in sorted(g["rows"], key=lambda x: (x["week"], x["date"], x["away"])):
        prov = badge("read official", "ok") if r["provenance"] == "read_from_official_week_page" else badge("reconciled", "derived")
        rows.append([
            esc(r["week"]), esc(r["date"]),
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(r["source_url"]), esc("%s at %s" % (r["away"], r["home"]))),
            "%s&ndash;%s" % (esc(r["away_pts"]), esc(r["home_pts"])),
            ("%+d" % (r["home_pts"] - r["away_pts"])),
            prov,
            src(r.get("score_source_url") or r["source_url"], "week page" if r["provenance"] == "read_from_official_week_page" else "game page"),
        ])
    body = ['<h1>Games and scores, 2026 weeks 1&ndash;9</h1>',
            '<p class="lede">136 completed games. Each row links to the official game page; the 16 games this session '
            'read directly from the official week pages are marked.</p>']
    body.append('<div class="panel warn"><strong>Correction made in this session.</strong> The peer archive '
                '<code>nfl-lab/data/games_2026.csv</code> contained 120 of these 136 games: it had no Week 9 at all and '
                'no Week 8 Monday game. Those 16 games were read from the official week pages here. The peer file was '
                'not modified. Proof that the completed archive is right: recomputing every club&rsquo;s W-L-T, PF and PA '
                'from the 136 rows reproduces the official standings with <strong>0 mismatches</strong>.</div>')
    body.append(table(["Wk", "Date", "Game", "Score", "Home margin", "Provenance", "Source"],
                      rows, cap="All 2026 regular-season games through Week 9", numeric=(0, 3, 4)))
    body.append('<p class="note">"reconciled" means the score comes from the peer archive (which cites the official '
                'game page) and is corroborated by the league-wide aggregate reconciliation; "read official" means this '
                'session read the score off an official nfl.com page. See flag F-09.</p>')
    return page("pages/scores.html", "Games & scores", "Official data / Games & scores", "\n".join(body), "games",
                "All 2026 NFL games through week 9 with scores, margins and official source links, including 16 games restored from official week pages.")


def build_schedule():
    s = load("slate_week10.json")
    rows = []
    for r in s["rows"]:
        rows.append([
            esc(r["date"]), esc(r["kickoff_et"]), esc(r["network"]),
            '<a href="%s" target="_blank" rel="noopener">%s at %s</a>' % (esc(r["source_url"]), esc(r["away"]), esc(r["home"])),
            ("Munich" if r["neutral"] else "home field"),
            src(r["source_url_schedule"], "week 10 page"),
        ])
    body = ['<h1>Week 10 slate, 2026</h1>',
            '<p class="lede">The 14 games scheduled for 12&ndash;16 November 2026, as printed on the official by-week '
            'page. Four clubs are on bye, so this week has 14 games, not 16.</p>']
    body.append(table(["Date", "Kickoff ET", "Network", "Game", "Site", "Source"], rows,
                      cap="Official 2026 Week 10 schedule"))
    body.append('<div class="panel info"><strong>Byes:</strong> %s. The official page lists exactly these four clubs under '
                '&ldquo;Teams on Bye&rdquo;, which is why 14 games (28 clubs) is the correct count and a 16-game '
                'assumption would be wrong.</div>' % ", ".join(s["byes"]))
    body.append('<p class="note">Week 16&ndash;18 kickoff times are flex-scheduled and announced later; that is stated on '
                'the official page and is repeated here rather than guessed.</p>')
    return page("pages/schedule.html", "Week 10 schedule", "Official data / Week 10 schedule", "\n".join(body), "sched",
                "Official 2026 NFL Week 10 schedule with 14 games, four byes, kickoff times and networks.")


def build_own_lines():
    o = load("own_lines_2026.json")
    body = ['<h1>Originated lines</h1>',
            '<p class="lede">Our own spread, total and fair moneyline for every Week 10 game, built only from the '
            'official team statistics on this site. These are <strong>model outputs, not prices, not predictions and '
            'not recommendations</strong>.</p>']
    body.append('<div class="panel info"><h3>The model, in full</h3><ul class="tight">'
                '<li>Home points = (home offence points/game + away defence points/game) / 2 + home-field / 2</li>'
                '<li>Away points = (away offence points/game + home defence points/game) / 2 &minus; home-field / 2</li>'
                '<li>Spread = &minus;(home points &minus; away points); total = home + away</li>'
                '<li>Moneyline = the fair (no-vig) price implied by a normal model of the margin with &sigma; = %.3f '
                'points, the holdout residual standard deviation</li>'
                '<li>Home-field = <strong>1.5 points</strong>, a stated assumption (flag F-04), not an official value</li>'
                '</ul><p class="note">That is the entire model. It has three parameters and no proprietary inputs, which '
                'is exactly why it loses to the closing line by 0.63 points.</p></div>' % o["model"]["sigma_margin_holdout"])
    rows = []
    for r in o["rows"]:
        rows.append([
            esc(r["date"]), esc(r["kickoff_et"]), esc(r["network"]),
            "%s at %s" % (esc(r["away"]), esc(r["home"])),
            ("%.1f" % r["own_home_pts"]), ("%.1f" % r["own_away_pts"]),
            ("%.1f" % r["own_spread_home"]), ("%.1f" % r["own_total"]),
            ("%.3f" % r["p_home_win"]), esc(r["own_ml_home"]), esc(r["own_ml_away"]),
            fmt(None),
            src(r["source_url"]),
        ])
    body.append("<h2>Week 10 originated lines</h2>")
    body.append(table(["Date", "Kickoff", "TV", "Game", "Home pts", "Away pts", "Spread (home)", "Total",
                       "P(home win)", "Fair ML home", "Fair ML away", "Market", "Source"],
                      rows, cap="Own lines for the 14-game Week 10 slate", numeric=(4, 5, 6, 7, 8, 9, 10)))
    body.append('<p class="note">A negative spread means the home side is favoured. The Market column is blank for every '
                'row: no official or licensed 2026 price archive exists in this repository, so a divergence cannot be '
                'computed and is not estimated (flag F-01).</p>')

    body.append("<h2>Input ratings, per club</h2>")
    r = load("ratings_2026.json")
    rows = []
    for x in r["rows"]:
        rows.append([esc(x["name"]), ("%.1f" % x["off_pts_pg"]) if x["off_pts_pg"] is not None else fmt(None),
                     ("%.1f" % x["def_pts_pg"]) if x["def_pts_pg"] is not None else fmt(None),
                     ("%.1f" % x["pass_yds_pg"]) if x["pass_yds_pg"] is not None else fmt(None),
                     ("%.1f" % x["rush_yds_pg"]) if x["rush_yds_pg"] is not None else fmt(None),
                     ("%.1f" % x["def_pass_yds_pg"]) if x["def_pass_yds_pg"] is not None else fmt(None),
                     ("%.1f" % x["def_rush_yds_pg"]) if x["def_rush_yds_pg"] is not None else fmt(None),
                     src(r["source_url_offense_scoring"])])
    body.append(table(["Team", "PF/G", "PA/G", "Pass yd/G", "Rush yd/G", "Opp pass yd/G", "Opp rush yd/G", "Source"],
                      rows, cap="The exact inputs feeding the model above", numeric=(1, 2, 3, 4, 5, 6)))
    body.append('<p class="note">Shrinkage and season-carryover are used in the historical backtest only; the 2026 '
                'lines above use the same-season rates directly because every club has a full 9 games.</p>')
    return page("pages/own-lines.html", "Originated lines", "Own lines / Originated lines", "\n".join(body), "lines",
                "Own NFL lines for the 2026 Week 10 slate built from official team statistics, with the full model and its assumptions.")


def build_correlations():
    c = load("correlations.json")
    body = ['<h1>Correlation and dependence</h1>',
            '<p class="lede">What parlay legs do to each other, measured. Two team-level pairs are measured; every '
            'player-level pair is blank because the data does not exist here.</p>']
    rows = []
    for l in c["legs"]:
        rows.append([esc(l["pair"]), esc(l["method"]),
                     ("%.4f" % l["phi"]) if l["phi"] is not None else fmt(None),
                     ("%.2f%%" % (l["joint_rate"] * 100)), ("%.2f%%" % (l["independent_expectation"] * 100)),
                     esc(l["interpretation"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/correlations.json")])
    body.append(table(["Leg pair", "Method", "phi", "Joint rate", "If independent", "Reading", "Source"], rows,
                      cap="Measured on %d holdout games (2017&ndash;2025)" % c["n"], numeric=(2, 3, 4)))
    body.append('<div class="panel info"><h3>How to read phi</h3><p>phi is the correlation between two yes/no outcomes. '
                'Zero means the legs are independent, so multiplying their probabilities gives the right joint price. '
                'Positive means they co-move and multiplying <em>understates</em> the true joint price; negative means '
                'multiplying overstates it. Both values above are within 0.011 of zero, so for these two team-level '
                'pairs, multiplication is a defensible approximation on this sample.</p></div>')

    body.append("<h2>The anti-luck test: does the model&rsquo;s error persist?</h2>")
    rp = c["residual_persistence"]
    rows = [[esc("Consecutive-season mean spread error"), esc(rp["method"]),
             ("%.4f" % rp["value"]) if rp["value"] is not None else fmt(None), esc(rp["interpretation"]),
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/correlations.json")]]
    body.append(table(["Quantity", "Method", "Value", "Reading", "Source"], rows, numeric=(2,)))
    body.append('<p class="note">A value near +0.40 means the model is <em>consistently wrong in the same direction</em> '
                'about a third of the time &mdash; that is a bias to fix, not an edge to sell. Genuine skill would show '
                'up as profits persisting, which the leaderboard does not find.</p>')

    body.append("<h2>Not measured, and why</h2>")
    rows = []
    for x in c["not_measured"]:
        rows.append([esc(x["pair"]), badge("BLANK", "fail"), esc(x["reason"]), src(x["source_url"])])
    body.append(table(["Leg pair", "Status", "Reason it is blank", "Source"], rows,
                      cap="Correlations that would be needed for player-prop combos"))
    body.append('<p class="note">These blanks are the honest answer to "determine correlation values": the team-level '
                'values are measured, the player-level values cannot be, because there are no official player-game logs '
                'and no prop prices in scope (flags F-02, F-03).</p>')
    return page("pages/correlations.html", "Correlation", "Own lines / Correlation", "\n".join(body), "corr",
                "Measured NFL parlay-leg correlation with phi coefficients, residual persistence, and an explicit list of what cannot be measured.")


def build_strategies():
    res = load("results.json")
    body = ['<h1>Signal catalogue</h1>',
            '<p class="lede">Ten candidate signals, each with an explicit verdict. Three were measured and rejected; '
            'seven were not measured and say so. Nothing is described as promising when it is untested.</p>']
    rows = []
    for s in res["signals_considered"]:
        rows.append(["<strong>%s</strong>" % esc(s["id"]), esc(s["signal"]), esc(s["evidence_in_repo"]),
                     esc(s["verdict"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")])
    body.append(table(["ID", "Signal", "Evidence in this repo", "Verdict", "Source"], rows,
                      cap="Signal catalogue with verdicts"))
    body.append('<div class="panel warn"><strong>Why most signals are unmeasured rather than tested.</strong> '
                'Rest, weather, officials, key numbers and injury timing all need a data source this repository does '
                'not hold. Listing them as "unmeasured" is the only honest option; testing them on a proxy would '
                'produce numbers that look like evidence and are not.</div>')

    body.append("<h2>Registered strategies and their results</h2>")
    rows = []
    for s in res["strategies"]:
        rows.append(["<strong>%s</strong>" % esc(s["id"]), esc(s["label"]), fmt(s["n_bets"]),
                     ("%.2f%%" % (s["roi"] * 100)) if s["roi"] is not None else fmt(None),
                     ("%.2f" % s["permutation_p"]) if s["permutation_p"] is not None else fmt(None),
                     "%d/%d" % (s["gates_passed"], s["gates_total"]), badge(s["tier"], "fail"),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")])
    body.append(table(["ID", "Rule", "Bets", "ROI", "Placebo p", "Gates", "Tier", "Source"], rows, numeric=(2, 3, 4, 5)))
    body.append('<p class="note">The full gate-by-gate breakdown is on the '
                '<a href="validation.html">validation page</a>; per-strategy detail on '
                '<a href="singles.html">singles</a> and <a href="parlays.html">parlays</a>.</p>')
    return page("pages/strategies.html", "Signal catalogue", "Strategies / Signal catalogue", "\n".join(body), "strat",
                "Ten NFL betting signal candidates with explicit verdicts, and the four strategies that were actually backtested.")


def gate_rows(strategy):
    rows = []
    gates = {g["id"]: g for g in load("gates.json")["gates"]}
    for gid, v in strategy["gates"].items():
        g = gates[gid]
        rows.append(["<strong>%s</strong>" % gid, esc(g["name"]), esc(g["rule"]),
                     badge("pass", "ok") if v["pass"] else badge("fail", "fail"),
                     esc(v["detail"]), esc(g["why"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")])
    return rows


def build_singles():
    res = load("results.json")
    m = res["metrics"]
    body = ['<h1>Single bets</h1>',
            '<p class="lede">Three single-bet rules, each requiring a stated divergence between our line and the '
            'closing line before a bet is taken. All three lose. The point is the gate table underneath, which shows '
            'exactly where each one fails.</p>']
    body.append("<h2>Forecast accuracy first</h2>")
    rows = [
        ["Spread", ("%.3f" % m["spread_mae"]["own_model"]), ("%.3f" % m["spread_mae"]["market_closing_line"]),
         ("%.3f" % m["spread_mae"]["naive_zero_margin"]), badge("loses to market", "fail"),
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Total", ("%.3f" % m["total_mae"]["own_model"]), ("%.3f" % m["total_mae"]["market_closing_line"]),
         ("%.3f" % m["total_mae"]["naive_holdout_mean"]), badge("loses to market", "fail"),
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
    ]
    body.append(table(["Market", "Our MAE", "Closing-line MAE", "Naive baseline MAE", "Verdict", "Source"], rows,
                      cap="Mean absolute error on %d holdout games" % m["n_holdout_games"], numeric=(1, 2, 3)))
    body.append('<p class="note">Winner accuracy is %.4f against a home-team baseline of %.4f on the same games. '
                'Beating the home baseline is easy; beating the closing line is the only thing that pays.</p>'
                % (m["winner_accuracy"], m["home_baseline_accuracy"]))

    names = {"S1_spread": "Spread divergence", "S2_total": "Total divergence", "S3_moneyline": "Fair-moneyline value"}
    for s in res["strategies"]:
        if s["id"] not in names:
            continue
        body.append("<h2>%s &mdash; %s</h2>" % (esc(s["id"]), esc(names[s["id"]])))
        body.append('<p><strong>Rule:</strong> %s. <strong>Bets:</strong> %s. <strong>ROI:</strong> %s. '
                    '<strong>95%% CI:</strong> %s.</p>' % (
                        esc(s["label"]), fmt(s["n_bets"]),
                        ("%.2f%%" % (s["roi"] * 100)) if s["roi"] is not None else fmt(None),
                        ("[%.2f%%, %.2f%%]" % (s["roi_ci95"][0] * 100, s["roi_ci95"][1] * 100)) if s["roi_ci95"] else fmt(None)))
        body.append(table(["Gate", "Name", "Pre-registered rule", "Result", "Measured value", "Why it matters", "Source"],
                          gate_rows(s), cap="Gate-by-gate result for %s" % s["id"]))
    body.append('<p class="note">Thresholds were frozen before the backtest ran (gates v1.0). Changing one after seeing a '
                'result is the failure mode the file exists to prevent.</p>')
    return page("pages/singles.html", "Single bets", "Strategies / Single bets", "\n".join(body), "singles",
                "NFL single-bet strategy results with gate-by-gate pass/fail, forecast MAE against the closing line, and confidence intervals.")


def build_parlays():
    res = load("results.json")
    s = [x for x in res["strategies"] if x["id"] == "S4_parlay"][0]
    body = ['<h1>Parlays</h1>',
            '<p class="lede">Cross-game two-leg parlays built from the strongest single-bet legs each week. '
            'Same-game combinations are excluded on purpose: their legs are not independent, and this repository '
            'cannot price them without archived same-game prices.</p>']
    body.append('<div class="panel info"><h3>Pricing rule</h3><p>Two legs at &minus;110 have a true payout of '
                '(1.9091&sup2; &minus; 1) = <strong>2.6458</strong> units profit per unit staked. A push leg voids that '
                'leg rather than the ticket. No same-game correlation adjustment is applied because cross-game legs '
                'are independent by construction; where legs <em>are</em> correlated, the measured phi values are on the '
                '<a href="correlations.html">correlation page</a>.</p></div>')
    rows = [["<strong>S4</strong>", esc(s["label"]), fmt(s["n_bets"]),
             ("%.2f%%" % (s["roi"] * 100)) if s["roi"] is not None else fmt(None),
             '<span class="blank">not tested</span>' if s["permutation_p"] is None else ("%.2f" % s["permutation_p"]),
             badge("fail", "fail"), "%d/%d" % (s["gates_passed"], s["gates_total"]),
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")]]
    body.append(table(["ID", "Construction", "Parlays", "ROI", "Placebo p", "Verdict", "Gates", "Source"], rows, numeric=(2, 3, 4, 6),
                      cap="Cross-game 2-leg parlay result"))
    body.append(table(["Gate", "Name", "Pre-registered rule", "Result", "Measured value", "Why it matters", "Source"],
                      gate_rows(s), cap="Gate-by-gate result for S4"))
    body.append('<div class="panel warn"><strong>Why parlays lose more than singles.</strong> Each leg carries the same '
                'negative expectation, and multiplying them compounds it: &minus;3.1% per leg becomes &minus;15.7% per '
                'two-leg ticket. A parlay is not a way to amplify an edge that is not there.</div>')
    body.append('<p class="note">n = 155 is far below the 300-bet floor, so even a positive result here could not have '
                'been certified. The gate table says so explicitly rather than leaving the reader to notice.</p>')
    return page("pages/parlays.html", "Parlays", "Strategies / Parlays", "\n".join(body), "parlays",
                "Cross-game NFL parlay results with true two-leg pricing, gate results and the compounding-vig explanation.")


def build_props():
    body = ['<h1>Player props</h1>',
            '<p class="lede">This page is deliberately empty of results. Player-prop strategies cannot be graded with '
            'the sources this project is allowed to use, and inventing a proxy would produce numbers that look like '
            'evidence and are not.</p>']
    body.append('<div class="panel warn"><strong>Blocked, with the reason named.</strong> Grading a prop requires two '
                'things: official player-game outcomes, and the price the market actually offered. nfl.com publishes '
                'season-to-date player leaderboards only (no per-game logs in machine-readable form), and no prop '
                'prices exist anywhere in this repository. Without both, a "prop strategy" is a guess about a guess.</div>')
    rows = [
        ["Prop singles (over/under on a player stat)", badge("BLOCKED", "fail"),
         "Needs per-game player outcomes and archived prop prices", fmt(None),
         src("https://www.nfl.com/stats/player-stats/")],
        ["Prop combos (2+ props, same game)", badge("BLOCKED", "fail"),
         "Needs the above plus measured joint dependence; multiplying legs is invalid where they co-move",
         fmt(None), src("https://www.nfl.com/stats/player-stats/")],
        ["QB / WR correlation", badge("BLOCKED", "fail"), "Player-level pair; no logs in scope", fmt(None),
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/correlations.json")],
        ["Season-to-date player leaderboards", badge("AVAILABLE", "ok"),
         "Published by the league and readable; they are season aggregates, not per-game outcomes, so they cannot settle a single-game prop",
         "readable", src("https://www.nfl.com/stats/player-stats/")],
    ]
    body.append(table(["Item", "Status", "Requirement or note", "Result", "Source"], rows,
                      cap="What exists, what is missing, and why nothing is graded"))
    body.append("<h2>What would make this page real</h2>")
    body.append('<ol class="tight"><li>An authorised per-game player-stat feed (the league publishes aggregates; '
                'per-game data is licensed).</li><li>An archived prop price with a timestamp, so the price being '
                'tested is the price that existed.</li><li>A pre-registered gate version that adds a dependence '
                'correction for same-game combos.</li></ol>')
    body.append('<p class="note">A peer workspace in this repository reported a QB-over + WR1-over joint lift of 1.45x. '
                'It was measured against a rolling-mean <em>proxy</em> line, not a sportsbook, and that workspace\'s own '
                'flags record the gate as failed. It is not imported here (see Q10).</p>')
    return page("pages/props.html", "Player props", "Strategies / Player props", "\n".join(body), "props",
                "Why player-prop strategies are blocked in this project: no official per-game player logs and no archived prop prices.")


def build_validation():
    g = load("gates.json")
    res = load("results.json")
    body = ['<h1>Validation and luck</h1>',
            '<p class="lede">Ten gates, frozen before any result was produced, plus four separate bounds on luck. '
            'A strategy qualifies only if all ten pass. None does.</p>']
    rows = []
    for x in g["gates"]:
        res_all = ", ".join("%s %s" % (s["id"], "pass" if s["gates"][x["id"]]["pass"] else "fail") for s in res["strategies"])
        rows.append(["<strong>%s</strong>" % esc(x["id"]), esc(x["name"]), esc(x["rule"]), esc(x["why"]),
                     esc(res_all), "", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")])
    body.append(table(["Gate", "Name", "Pre-registered rule", "Why it exists", "Result by strategy", "", "Source"],
                      rows, cap="The ten pre-registered gates and how each strategy fared"))
    body.append('<p class="note">Thresholds are design choices, not official NFL values (flag F-11). '
                'Tier policy: Qualified = all ten pass and earns points; Bronze = 5-9; Rejected = fewer than 5. '
                'Only Qualified earns any of the 1,000-point pool.</p>')

    body.append("<h2>How luck is bounded</h2>")
    rows = [
        ["Week-clustered bootstrap", "Resample weeks, not bets, 4,000 times; report the 2.5th and 97.5th percentile ROI",
         "Bets inside a week share injuries, weather and referee crews, so resampling individual bets understates uncertainty",
         "gate G5", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Matched-random placebo", "Bet the same number of bets in the same weeks on random sides, 2,000 times; p = share of placebo runs at least as good",
         "If random sides do as well, the rule added nothing", "gate G6", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Season stability", "Positive ROI in >= 60% of holdout seasons that had bets",
         "One hot season is a story; a rule should repeat", "gate G7", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
        ["Residual persistence", "Correlation of consecutive-season mean spread error", "Persistent error is a bias to fix, not skill to sell",
         "diagnostic", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/correlations.json")],
        ["Prospective replication", "Freeze the rule, then grade games played after the freeze", "The only test that removes researcher choice",
         "gate G8 (not yet possible)", src("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ]
    body.append(table(["Bound", "Method", "What it rules out", "Where it enters", "Source"], rows))
    body.append('<div class="panel warn"><strong>Luck cannot be removed.</strong> It can only be bounded, and the bounds '
                'can only fail a strategy or leave it unproven. Nothing in this repository certifies skill; the '
                'strongest honest statement is that every registered rule is statistically indistinguishable from '
                'chance after costs, and three are worse than chance.</div>')

    body.append("<h2>Splits and frozen configuration</h2>")
    rows = [[esc("Dev"), "1999&ndash;2012", "design and parameter choice",
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
            [esc("Validation"), "2013&ndash;2016", "sanity check, no tuning",
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")],
            [esc("Holdout"), "2017&ndash;2025 (%d games)" % res["metrics"]["n_holdout_games"], "reported once, unchanged",
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")]]
    body.append(table(["Split", "Seasons", "Use", "Source"], rows, cap="Chronological splits; no shuffling, no look-ahead"))
    body.append('<p class="note">Frozen configuration: edge threshold %.1f points, prior %.1f games, carryover %.2f, '
                'moneyline edge 3 points, 4,000 bootstrap resamples, 2,000 placebo permutations.</p>'
                % (res["frozen_config"]["edge_threshold_pts"], res["frozen_config"]["prior_games"], res["frozen_config"]["carryover"]))
    return page("pages/validation.html", "Validation & luck", "Strategies / Validation & luck", "\n".join(body), "valid",
                "Ten pre-registered validation gates plus four bounds on luck, with the measured value for every gate.")


def build_leaderboard():
    res = load("results.json")
    g = load("gates.json")
    body = ['<h1>Leaderboard and rewards</h1>',
            '<p class="lede">The competition structure, the scoring, and the result: no strategy qualifies, so no '
            'reward points are awarded. The pool is non-monetary and stays unspent.</p>']
    body.append('<div class="panel warn"><strong>0 of 4 strategies qualified. 0 of %d reward points awarded.</strong> '
                'This is the designed outcome when public-data rules meet efficient closing lines, not a temporary '
                'setback to be tuned away.</div>' % g["reward_policy"]["total_points_in_pool"])
    rows = []
    for s in sorted(res["strategies"], key=lambda x: -(x["roi"] or -9)):
        rows.append(["<strong>%s</strong>" % esc(s["id"]), esc(s["label"]), fmt(s["n_bets"]),
                     ("%.2f%%" % (s["roi"] * 100)) if s["roi"] is not None else fmt(None),
                     ("[%.2f%%, %.2f%%]" % (s["roi_ci95"][0] * 100, s["roi_ci95"][1] * 100)) if s["roi_ci95"] else fmt(None),
                     ("%.2f" % s["permutation_p"]) if s["permutation_p"] is not None else fmt(None),
                     "%d/%d" % (s["gates_passed"], s["gates_total"]),
                     badge(s["tier"], "ok" if s["tier"] == "Qualified" else ("warn" if "Bronze" in s["tier"] else "fail")),
                     esc(s["reward_points"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/results.json")])
    body.append(table(["ID", "Strategy", "Bets", "ROI", "Bootstrap 95% CI", "Placebo p", "Gates", "Tier", "Points", "Source"],
                      rows, cap="Strategies ranked by holdout ROI (negative is worse)", numeric=(2, 3, 4, 5, 6, 8)))

    body.append("<h2>Reward and tier policy</h2>")
    rows = [[esc("Pool"), esc(g["reward_policy"]["total_points_in_pool"]), esc(g["reward_policy"]["points_awarded_rule"]),
             esc(g["reward_policy"]["cash_or_prize_value"]), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")],
            [esc("Qualified"), esc("all 10 gates"), esc(g["tier_policy"]["Qualified"]), esc("1000"),
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")],
            [esc("Bronze (no reward)"), esc("5-9 gates"), esc(g["tier_policy"]["Bronze (no reward)"]), esc("0"),
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")],
            [esc("Rejected"), esc("<5 gates"), esc(g["tier_policy"]["Rejected"]), esc("0"),
             src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")]]
    body.append(table(["Tier", "Requirement", "Meaning", "Points", "Source"], rows, numeric=(3,)))
    body.append('<p class="note">Cash value is zero by policy: a cash prize on an unvalidated model turns research into '
                'advertising. Points are a ranking device, nothing more (decision D2).</p>')

    body.append("<h2>How a strategy enters the competition</h2>")
    body.append('<ol class="tight"><li>Write the rule down: the exact trigger, the market, and the size rule.</li>'
                '<li>Register it in the strategy catalogue and in the gate file, with a version number, before running it.</li>'
                '<li>Run it once on the holdout with the frozen configuration and publish the result whatever it is.</li>'
                '<li>Only a full gate pass earns points. A change to the rule starts a new version with its own line in the catalogue.</li></ol>')
    return page("pages/leaderboard.html", "Leaderboard & rewards", "Strategies / Leaderboard & rewards", "\n".join(body), "board",
                "NFL strategy leaderboard: tiers, gates, bootstrap intervals and a non-monetary reward pool that awarded zero points because nothing qualified.")


def build_availability():
    a = load("availability.json")
    inj = load("injuries_week10.json")
    body = ['<h1>Injuries and backup depth</h1>',
            '<p class="lede">What the league actually discloses about availability, and an explicit statement of the '
            'part it does not disclose: who is a starter and who is a backup.</p>']
    body.append('<div class="panel warn"><strong>The requirement that cannot be met from official sources.</strong> '
                'You asked to track second-, third- and fourth-string players replacing starters. The NFL does not '
                'publish a depth chart on nfl.com &mdash; the team depth-chart URL returns a 404 &mdash; and it does not '
                'publish snap counts. The injury report gives practice and game status only. So this page reports '
                '<em>who is unavailable and at which position</em>, and never claims a player is a backup. Guessing '
                'would be the one thing that makes the rest of this site worthless.</div>')
    rows = []
    for r in a["rows"]:
        rows.append([esc(r["club"]), esc(r["game"]), esc(r["n_listed"]), esc(r["n_dnp"]), esc(r["n_limited"]),
                     esc(r["n_out"]), esc(r["n_questionable"]), esc(r["confirmed_out_named"]),
                     src(r["source_url"])])
    body.append("<h2>Weekly unavailability by club</h2>")
    body.append(table(["Club", "Week 10 game", "Listed", "Did not practise", "Limited", "Ruled out", "Questionable",
                       "Ruled out, by name", "Source"], rows,
                      cap="Derived strictly from fields the clubs themselves filed", numeric=(2, 3, 4, 5, 6)))
    body.append('<p class="note">%d players across %d clubs. Two clubs (Chargers, Ravens) filed no new listings &mdash; '
                'that is not a claim that their rosters are healthy. Practice status is the club&rsquo;s own designation: '
                '&ldquo;did not participate&rdquo;, &ldquo;limited&rdquo; or &ldquo;full&rdquo;.</p>'
                % (a["totals"]["players_listed"], a["totals"]["clubs"]))

    body.append("<h2>Full Week 10 injury report</h2>")
    rows = []
    for t in inj["teams"]:
        for p in t["players"]:
            rows.append([esc(t["club"]), esc(p["player"]), esc(p["position"]),
                         esc(p["injury"]) if p["injury"] else '<span class="blank">not disclosed</span>',
                         esc(p["practice_status"]),
                         esc(p["game_status"]) if p["game_status"] else '<span class="blank">not set</span>',
                         src(p["source_url"])])
    body.append(table(["Club", "Player", "Pos", "Injury", "Practice status", "Game status", "Source"], rows,
                      cap="Every player on the official Week 10 report (%d rows)" % len(rows)))
    body.append('<p class="note">The report is a snapshot read on 2026-11-12 and game status is only final 90 minutes '
                'before kickoff (flag F-14). Positions are the codes printed on the report; they are not depth ranks.</p>')

    body.append("<h2>What it would take to answer the backup question</h2>")
    rows = [["Starter/backup designation", badge("BLOCKED", "fail"),
             "Not published by the league; the depth-chart URL 404s", fmt(None), src("https://www.nfl.com/teams/washington-commanders/roster")],
            ["Snap counts / participation", badge("BLOCKED", "fail"), "Licensed product; not on nfl.com", fmt(None),
             src("https://www.nfl.com/stats/player-stats/")],
            ["Who is unavailable, and where", badge("AVAILABLE", "ok"), "Official injury report, captured above",
             "275 players", src("https://www.nfl.com/injuries/")],
            ["Coaching-staff depth comments", badge("AVAILABLE (unstructured)", "warn"),
             "nfl.com news items do say things like 'expected to start again'; they are prose, not a dataset, and would need manual reading per game",
             "prose", src("https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again")]]
    body.append(table(["Requirement", "Status", "Note", "Value in repo", "Source"], rows))
    body.append('<p class="note">Example of the prose that does exist: an official nfl.com report states that Seahawks QB '
                'Sam Darnold is out for Week 10 and that backup Drew Lock is expected to start again. That is a citable '
                'fact for one player in one game; it is not a systematic depth chart, and building the general '
                'starter-vs-backup model from such sentences would need one read per club per week (suggestions S-08, S-09).</p>')
    return page("pages/availability.html", "Injuries & backups", "Availability / Injuries & backups", "\n".join(body), "avail",
                "Official NFL Week 10 injury report by club and position, plus an explicit account of why starter-versus-backup analysis is not possible from official sources.")


def build_requirements():
    r = load("requirements.json")
    body = ['<h1>Requirements and what was delivered</h1>',
            '<p class="lede">The complete list of requirements from the request, one row each, with what was '
            'delivered, where it lives, and an honest status. Four items are BLOCKED rather than pretended.</p>']
    counts = {}
    for x in r["requirements"]:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    body.append('<div class="cards">' + "".join(
        '<div class="card %s"><b>%d</b><span>%s</span></div>' % (
            "warn" if k in ("BLOCKED", "PARTIAL") else "", v, k.lower()) for k, v in sorted(counts.items(), key=lambda z: -z[1])) + "</div>")
    rows = []
    for x in r["requirements"]:
        st = x["status"]
        kind = "ok" if st == "DONE" else ("warn" if st in ("PARTIAL", "DONE - NEGATIVE RESULT") else "fail")
        where = x["where"]
        # link the first local page mentioned, if it exists
        m = re.search(r"(pages/[a-z-]+\.html)", where)
        if m:
            rest = where[m.end():]
            if os.path.exists(os.path.join(SITE, m.group(1))):
                name = m.group(1).split("/")[-1]
                where = '<a href="%s">%s</a>%s' % (name, esc(where[:m.end()]), esc(rest))
            else:
                where = esc(where.replace(m.group(1), m.group(1).split("/")[-1]))
        else:
            where = esc(where)
        rows.append(["<strong>%s</strong>" % esc(x["id"]), esc(x["requirement"]), badge(st.lower(), kind),
                     esc(x["delivered"]), where, esc(x["evidence"]), src(x["source_url"])])
    body.append(table(["ID", "Requirement", "Status", "What was delivered", "Where it lives", "Evidence", "Source"],
                      rows, cap="%d requirements from the request" % len(r["requirements"])))
    body.append('<div class="panel warn"><strong>How to read the blocked rows.</strong> R13 (player props), R19 and R20 '
                '(second/third/fourth-string replacement) are blocked because the official sources do not publish '
                'per-game player logs, prop prices, depth charts or snap counts. Nothing was substituted: those cells '
                'are blank on the site and the reason is on the Flagged for review page (F-02, F-03).</div>')
    body.append('<p class="note">Status vocabulary: DONE = delivered and reproducible. DONE - NEGATIVE RESULT = the '
                'analysis was completed and the answer is no, which is the deliverable. PARTIAL = delivered in part '
                'with the missing part named. BLOCKED = the source does not exist in scope.</p>')
    return page("pages/requirements.html", "Requirements", "Decision support / Requirements", "\n".join(body), "req",
                "Every requirement from the request traced to what was delivered, where it lives, and its status including blocked items.")


def build_decisions():
    q = load("questions.json")
    body = ['<h1>Questions, information and decisions</h1>',
            '<p class="lede">The complete register: what we know, what we do not know, what the answer is, and what '
            'would unlock each open question. Nothing here is marked answered without a source.</p>']
    counts = {}
    for x in q["questions"]:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    body.append('<div class="cards">' + "".join(
        '<div class="card %s"><b>%d</b><span>%s</span></div>' % (
            "warn" if k != "ANSWERED" else "", v, k.lower()) for k, v in sorted(counts.items(), key=lambda z: -z[1])) +
        '<div class="card warn"><b>%d</b><span>decisions blocked</span></div></div>' % len(q["decisions_blocked"]))

    body.append("<h2>Decisions that cannot be made yet</h2>")
    rows = []
    for d in q["decisions_blocked"]:
        rows.append(["<strong>%s</strong>" % esc(d["id"]), esc(d["decision"]),
                     badge(d["status"], "fail" if any(w in d["status"] for w in ("BLOCKED", "NO")) else "warn"),
                     esc(", ".join(d["blocking_questions"])), esc(d["what_would_unblock"]),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/questions.json")])
    body.append(table(["ID", "Decision", "Status", "Blocked by", "What would unblock it", "Source"], rows,
                      cap="Each decision names the exact questions that stop it"))

    body.append("<h2>The register</h2>")
    rows = []
    for x in q["questions"]:
        rows.append(["<strong>%s</strong>" % esc(x["id"]), esc(x["question"]),
                     badge(x["status"], "ok" if x["status"] == "ANSWERED" else ("warn" if x["status"] == "PARTIAL" else "fail")),
                     esc(x["known"]), esc(x["unknown"]) if x["unknown"] else '<span class="blank">none identified</span>',
                     esc(x["answer"]) if x["answer"] else '<span class="blank">no answer available</span>',
                     esc(x["unlocks"]), src(x["source_url"])])
    body.append(table(["ID", "Question", "Status", "What we know", "What we do not know", "Answer", "What unlocks it", "Source"],
                      rows, cap="%d questions: answered, partial, open or blocked" % len(q["questions"])))
    body.append('<p class="note">Reading rule: an OPEN or BLOCKED question never gets a filled-in number anywhere on '
                'this site. That is why so many cells are blank &mdash; the blank is the answer.</p>')

    body.append("<h2>How to discover the missing information</h2>")
    rows = [
        ["Licensed data", "Player-game logs, prop prices, snap counts, depth charts", "Clears Q9, Q13, Q15 and unblocks the prop and backup requirements",
         badge("COST", "warn"), src("https://www.nfl.com/stats/player-stats/")],
        ["Scheduled capture", "Daily injury-report snapshots with timestamps", "Makes injury timing testable (Q14, suggestion S-09)",
         badge("BUILDABLE", "ok"), src("https://www.nfl.com/injuries/")],
        ["Official page reading", "Weekly schedule and result pages", "Fills archive holes cheaply; found 16 missing games this session (Q20)",
         badge("DONE", "ok"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Owner decision", "Which sport is canonical, whether the pool is money, what the project is for", "Clears Q18, Q19, Q22 and D7",
         badge("NEEDS YOU", "warn"), src("https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md")],
        ["Independent review", "A statistician reviewing gate thresholds and the placebo design", "Hardens G1-G10 before any reward is paid (F-11)",
         badge("EXTERNAL", "warn"), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json")],
    ]
    body.append(table(["Route", "What it supplies", "Questions it unlocks", "Status", "Source"], rows))
    return page("pages/decisions.html", "Questions & decisions", "Decision support / Questions & decisions", "\n".join(body), "dec",
                "The complete decision register: 22 questions with what is known, what is unknown, the answer, and what would unlock each one.")


def build_suggestions():
    s = load("suggestions.json")
    body = ['<h1>Suggestions</h1>',
            '<p class="lede">Sixteen proposed changes to improve decision making and the site, each with impact, effort, '
            'risk, the questions that must be answered first, and its current status. Pick a path here before '
            'implementing anything.</p>']
    counts = {}
    for x in s["suggestions"]:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    body.append('<div class="cards">' + "".join(
        '<div class="card"><b>%d</b><span>%s</span></div>' % (v, k.lower().replace("_", " "))
        for k, v in sorted(counts.items())) + "</div>")
    body.append('<div class="panel info"><strong>How to use this page.</strong> Every row is a proposal. Only rows marked '
                '<span class="badge ok">implemented</span> exist today. To accept one, change its <code>status</code> in '
                '<code>nfl-edge/data/suggestions.json</code> and rebuild &mdash; the page renders from that file and '
                'nothing else, so the list can never drift from what was actually done.</div>')
    rows = []
    for x in s["suggestions"]:
        st = x["status"]
        kind = "ok" if st == "IMPLEMENTED" else ("warn" if st == "NEEDS DECISION" else "derived")
        prereq = ", ".join(x["prerequisites"]) if x["prerequisites"] else "none"
        rows.append(["<strong>%s</strong>" % esc(x["id"]), esc(x["area"]),
                     badge(st.replace("_", " ").lower(), kind),
                     esc(x["suggestion"]), esc(x["why"]),
                     esc(x["impact"]), esc(x["effort"]), esc(x["risk"]), esc(prereq),
                     src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/suggestions.json")])
    body.append(table(["ID", "Area", "Status", "Suggestion", "Why it improves decisions", "Impact", "Effort", "Risk",
                       "Needs first", "Source"], rows, cap="All 16 suggestions"))
    body.append('<p class="note">Impact, effort and risk are this session\'s judgement, not measurements, and are '
                'labelled as such. Prerequisites are the Q-ids from the <a href="decisions.html">decision register</a>.</p>')

    body.append("<h2>The three that matter most</h2>")
    body.append('<ol class="tight">'
                '<li><strong>S-03 (needs your decision):</strong> decide what the project is for &mdash; a rigorous '
                'no-edge lab, a data-coverage product, or a hunt for proprietary signal that needs a licence. Every '
                'other priority follows from this.</li>'
                '<li><strong>S-11 (needs your decision):</strong> consolidate the repository. Twenty parallel workspaces '
                'with duplicated dashboards are now a correctness risk, not just clutter.</li>'
                '<li><strong>S-08 (proposed):</strong> the only way to answer the backup-deficiency question with '
                'numbers is a licensed depth chart plus snap counts. Nothing buildable from nfl.com will get there.</li></ol>')
    return page("pages/suggestions.html", "Suggestions", "Decision support / Suggestions", "\n".join(body), "sugg",
                "Sixteen prioritised suggestions to improve the site and decision making, each with impact, effort, risk, prerequisites and status.")


def build_sources():
    body = ['<h1>Source register</h1>',
            '<p class="lede">Every source used, what it was used for, and what it does not cover. If a claim is not in '
            'this table, it is not a verified claim on this site.</p>']
    rows = [
        ["Standings", "2026 W-L-T, PCT, PF, PA, net points, records, streaks", "All 32 rows",
         "Does not publish anything about prices or depth charts", src("https://www.nfl.com/standings/")],
        ["Schedule, by week", "Game matchups, dates, kickoff times, networks, byes, final scores", "Weeks 1&ndash;10",
         "Week 16&ndash;18 kickoff times are undetermined and announced later", src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Game pages", "Per-game canonical URL used as the row source for every score", "136 games + 14 Week 10 games",
         "No prices", src("https://www.nfl.com/games/commanders-at-giants-2026-reg-10")],
        ["Team stats, offence - scoring", "Points for per club", "32 clubs", "Season aggregate only", src("https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all")],
        ["Team stats, offence - passing", "Pass yards and passing touchdowns", "32 clubs", "No per-game or per-player splits", src("https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all")],
        ["Team stats, offence - rushing", "Rush yards and rushing touchdowns", "32 clubs", "No per-game or per-player splits", src("https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all")],
        ["Team stats, defence - scoring", "Points allowed per club", "32 clubs", "Season aggregate only", src("https://www.nfl.com/stats/team-stats/defense/scoring/2026/reg/all")],
        ["Team stats, defence - passing", "Opponent pass yards and passing touchdowns", "32 clubs", "No coverage or pressure detail", src("https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all")],
        ["Team stats, defence - rushing", "Opponent rush yards and rushing touchdowns", "32 clubs", "No situational splits", src("https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all")],
        ["Injuries, Week 10", "Player, position, injury, practice status, game status", "275 players, 28 clubs",
         "No depth chart, no snap counts, changes daily", src("https://www.nfl.com/injuries/")],
        ["Player stats (leaderboards)", "Season-to-date player leaders", "Used only to establish what is and is not published",
         "Aggregates only; cannot settle a single-game prop", src("https://www.nfl.com/stats/player-stats/")],
        ["Club roster pages", "Position, number, physicals, experience, college", "Used to show that no depth rank is published",
         "No starter/backup designation", src("https://www.nfl.com/teams/washington-commanders/roster")],
        ["Official news item", "Confirms one availability fact (Darnold out, Lock expected to start)", "1 article",
         "Prose, not a dataset", src("https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again")],
        ["NCPG helpline", "Responsible-gambling resource on every page", "site-wide", "Not evidence about football", src("https://www.ncpgambling.org/help-treatment/")],
        ["Peer closing-line archive (third party)", "Historical closing spreads, totals and moneylines, 1999&ndash;2025",
         "7,087 completed games with a recorded result",
         "THIRD-PARTY, not official; no 2026 prices; contains 2026 rows the owning session must explain (F-08)",
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/predictions.csv")],
        ["Peer game archive (this repository)", "2026 scores and game URLs, weeks 1&ndash;8", "120 games (16 were missing)",
         "Incomplete when found; corrected copy in nfl-edge/data/games_2026.json (F-07)",
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/games_2026.csv")],
    ]
    body.append(table(["Source", "What it provides", "Coverage here", "What it does not cover", "Link"], rows))
    body.append('<div class="panel warn"><strong>What is missing from every official source.</strong> Betting lines, '
                'prop prices, depth charts, snap counts and per-game player logs. Those five absences explain every '
                'blank cell on this site.</div>')
    return page("pages/sources.html", "Source register", "Governance / Source register", "\n".join(body), "src",
                "Register of every source used on the NFL Edge site, with coverage and the specific gaps in each.")


def build_integrity():
    i = load("integrity.json")
    body = ['<h1>Integrity checks</h1>',
            '<p class="lede">Fifteen mechanical checks that must pass or the build refuses to publish. They test '
            'whether the official numbers agree with each other and with the game archive &mdash; not whether a third '
            'party re-read the pages.</p>']
    rows = []
    for c in i["checks"]:
        rows.append(["<strong>%s</strong>" % esc(c["id"]), esc(c["check"]),
                     badge("pass", "ok") if c["pass"] else badge("fail", "fail"),
                     esc(c["detail"]), src(c["source_url"])])
    body.append(table(["ID", "Check", "Result", "Measured detail", "Source"], rows,
                      cap="%d of %d checks pass" % (i["n_pass"], i["n_checks"])))
    body.append('<div class="panel info"><h3>What these checks can and cannot prove</h3>'
                '<p>They prove the transcribed official values are mutually consistent, and that the game archive '
                'reproduces every club&rsquo;s record and points exactly. They cannot catch a typo that is internally '
                'consistent, and they do not certify that an outgoing link still resolves to the same content today. '
                'That gap is flag F-10 and suggestion S-16.</p></div>')
    body.append('<p class="note">Regenerate with <code>python3 nfl-edge/scripts/build_stats.py</code>, which exits '
                'non-zero on any failure.</p>')
    return page("pages/integrity.html", "Integrity checks", "Governance / Integrity checks", "\n".join(body), "integ",
                "Fifteen mechanical integrity checks over the transcribed official NFL values, all passing.")


def build_repo_review():
    body = ['<h1>Repository review</h1>',
            '<p class="lede">A file-by-file review of the repository as found, with a verdict on each existing NFL '
            'workspace and the irregularities worth fixing.</p>']
    body.append("<h2>Inventory at the start of this session</h2>")
    rows = [
        ["Files tracked", "675", "Excluding .git", src("https://github.com/sassnarep3-star/Own4")],
        ["HTML pages", "220", "Many are generated duplicates across workspaces", src("https://github.com/sassnarep3-star/Own4")],
        ["Raw scrape dump", "53 MB in data/raw/", "Committed archive of ESPN/NBA HTML and JSON; not used by the canonical site", src("https://github.com/sassnarep3-star/Own4/tree/main/data/raw")],
        ["Tracked .pyc files", "4", "Build artefacts under own4-dashboard/scripts/__pycache__ (F-12)", src("https://github.com/sassnarep3-star/Own4/tree/main/own4-dashboard/scripts")],
        ["Parallel workspaces", "~20", "NBA (x8), NFL (x4), SF rental (x6), status, evidence", src("https://github.com/sassnarep3-star/Own4")],
        ["Merge-conflict markers", "0", "Scanned every .md/.json/.csv/.html/.py file", src("https://github.com/sassnarep3-star/Own4")],
    ]
    body.append(table(["Item", "Value", "Note", "Source"], rows, numeric=(1,)))

    body.append("<h2>Verdict on each existing NFL workspace</h2>")
    rows = [
        ["nfl/", "Specification pages: strategies, gates, leaderboard design, source list. HTML only.",
         badge("superseded", "warn"),
         "Design without measured results; correctly labels its own unverified values. Kept as-is.",
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl/index.html")],
        ["nfl-research/", "A short generated site with a builder and a test script.", badge("superseded", "warn"),
         "Small; overlaps nfl/ in purpose. No measured backtest.", src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-research/index.html")],
        ["nfl-lab/", "2026 season archive: games, standings, team passing, own lines, signals, leaderboard.", badge("useful but incomplete", "fail"),
         "Its games file is missing 16 of 136 games (F-07). The rest of the workspace is usable and its own-lines table is well structured.",
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/games_2026.csv")],
        ["nfl-quant/", "The largest measured workspace: 1999-2026 archive, walk-forward model, 5 strategies, 16 correlations, 3 MB of outputs.", badge("most developed", "ok"),
         "Good method and an honest negative result. Two issues: its 2026 archive rows cannot all be real games (F-08), and its prop results are priced against a proxy line (Q10).",
         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/EXECUTIVE_SUMMARY.md")],
    ]
    body.append(table(["Workspace", "What it contains", "Verdict", "Reason", "Source"], rows))
    body.append('<p class="note">This session did not modify any of the four. All are preserved verbatim; the new '
                'workspace is <code>nfl-edge/</code>.</p>')

    body.append("<h2>Irregularities found</h2>")
    flags = load("flags.json")["flags"]
    rows = []
    for f in flags:
        rows.append(["<strong>%s</strong>" % esc(f["id"]), esc(f["area"]), esc(f["item"]), esc(f["action"]),
                     src(f["source_url"])])
    body.append(table(["ID", "Area", "Finding", "Recommended action", "Source"], rows,
                      cap="All 16 flagged items (also on the Flagged for review page)"))
    body.append('<div class="panel warn"><strong>The one that mattered.</strong> The peer game archive was missing every '
                'Week 9 game and the Week 8 Monday game. Any rate statistic computed from it would have been wrong for '
                '16 of 136 games &mdash; about 12% of the season. That is why every data file on this site is now checked '
                'against the official standings before it is used.</div>')
    return page("pages/repo-review.html", "Repo review", "Governance / Repo review", "\n".join(body), "repo",
                "Repository review: inventory, verdict on each existing NFL workspace, and the irregularities found.")


def build_flagged():
    f = load("flags.json")["flags"]
    body = ['<h1>Flagged for review</h1>',
            '<p class="lede">Everything irregular, unverified, blocked or caveated, in one place. None of it blocks '
            'publication; several items block specific claims. Each row says what would clear it.</p>']
    body.append('<div class="panel warn"><strong>None of these items blocks the site.</strong> They block claims: '
                'F-01 and F-02 block any 2026 price or prop claim, F-03 blocks any starter/backup claim, and F-04 to F-06 '
                'block any claim that the model has skill. The pages that would otherwise make those claims say so '
                'instead.</div>')
    rows = []
    for x in f:
        sev = x["severity"]
        kind = "fail" if sev.startswith("BLOCKING") else ("warn" if "IRREGULARITY" in sev else "derived")
        rows.append(["<strong>%s</strong>" % esc(x["id"]), badge(sev, kind), esc(x["area"]),
                     esc(x["item"]), esc(x["detail"]), esc(x["action"]), src(x["source_url"])])
    body.append(table(["ID", "Severity", "Area", "What was found", "Detail", "Action to clear it", "Source"], rows,
                      cap="%d flagged items, all non-blocking for publication" % len(f)))
    body.append('<p class="note">Severity vocabulary: BLOCKING means it blocks a named claim, not the site. '
                'IRREGULARITY means something in the repository is inconsistent. CAVEAT means the number is usable '
                'but must be read with the stated limit.</p>')
    return page("pages/flagged.html", "Flagged for review", "Governance / Flagged for review", "\n".join(body), "flags",
                "All flagged irregularities, blocked claims and caveats for the NFL Edge site, each with the source and the action that would clear it.")


def build_assets():
    css = """/* NFL Edge - single stylesheet, no build step, no framework */
:root{--bg:#0f1216;--panel:#161b22;--panel2:#1b2129;--line:#262d38;--ink:#e6edf3;--dim:#9aa7b4;--acc:#4ea1ff;
--ok:#2ea043;--warn:#d29922;--fail:#f85149;--derived:#a371f7}
@media(prefers-color-scheme:light){:root{--bg:#f7f9fc;--panel:#fff;--panel2:#f0f3f8;--line:#dfe5ee;--ink:#12161c;
--dim:#5b6675;--acc:#0b62d1;--ok:#1a7f37;--warn:#9a6700;--fail:#cf222e;--derived:#6f42c1}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.skip{position:absolute;left:-9999px}
.wrap{display:flex;min-height:100vh}
.side{width:250px;flex:0 0 250px;background:var(--panel);border-right:1px solid var(--line);padding:18px 14px;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{display:block;font-weight:700;font-size:17px;color:var(--ink);margin-bottom:4px}
.brand span{display:block;font-weight:400;font-size:11px;color:var(--dim);letter-spacing:.03em;text-transform:uppercase}
.tag{font-size:11px;color:var(--dim);margin:8px 0 14px;line-height:1.4}
.grp{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);margin:14px 0 5px;font-weight:700}
.nav{display:block;padding:5px 8px;border-radius:6px;color:var(--ink);font-size:13.5px}
.nav:hover{background:var(--panel2);text-decoration:none}
.nav.active{background:var(--acc);color:#fff}
.flaglink{display:block;margin-top:16px;padding:7px 9px;border:1px solid var(--warn);border-radius:6px;color:var(--warn);font-size:12.5px}
.sidefoot{margin-top:12px;font-size:11.5px;color:var(--dim);line-height:1.5}
.main{flex:1;min-width:0;padding:22px 30px 60px;max-width:1280px}
.crumb{font-size:12px;color:var(--dim);margin-bottom:10px}
h1{font-size:26px;line-height:1.25;margin:0 0 10px;letter-spacing:-.01em}
h2{font-size:18px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:0 0 6px}
.lede{font-size:15.5px;color:var(--dim);max-width:80ch;margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0 22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 13px}
.card b{display:block;font-size:22px;line-height:1.1;margin-bottom:3px}
.card span{font-size:11.5px;color:var(--dim);line-height:1.35;display:block}
.card.accent b{color:var(--acc)}.card.warn b{color:var(--warn)}
.panel{background:var(--panel);border:1px solid var(--line);border-left-width:4px;border-radius:8px;padding:13px 15px;margin:16px 0}
.panel.warn{border-left-color:var(--warn)}.panel.info{border-left-color:var(--acc)}
.panel p{margin:6px 0}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:9px;background:var(--panel);margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:12.8px}
caption{caption-side:top;text-align:left;padding:9px 12px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}
th{text-align:left;padding:8px 10px;background:var(--panel2);font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--dim);white-space:nowrap;position:sticky;top:0}
td{padding:7px 10px;border-top:1px solid var(--line);vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr:hover{background:var(--panel2)}
.src{font-size:11px;white-space:nowrap}
.badge{display:inline-block;padding:1px 6px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.02em;text-transform:uppercase;border:1px solid}
.badge.ok{color:var(--ok);border-color:var(--ok)}
.badge.warn{color:var(--warn);border-color:var(--warn)}
.badge.fail{color:var(--fail);border-color:var(--fail)}
.badge.derived{color:var(--derived);border-color:var(--derived)}
.blank{color:var(--dim);font-style:italic;opacity:.75}
.note{font-size:12px;color:var(--dim);max-width:95ch}
.tight{margin:6px 0;padding-left:20px}.tight li{margin:4px 0}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
footer{margin-top:36px;padding-top:14px;border-top:1px solid var(--line);font-size:11.5px;color:var(--dim)}
footer p{margin:5px 0}
.filterbox{margin:8px 0 0;display:none}
.filterbox input{background:var(--panel2);border:1px solid var(--line);color:var(--ink);padding:6px 10px;border-radius:6px;font-size:13px;width:260px;max-width:100%}
@media(max-width:860px){
 .wrap{flex-direction:column}
 .side{position:static;width:auto;height:auto;flex:none;border-right:0;border-bottom:1px solid var(--line)}
 .main{padding:18px 14px 48px}
 h1{font-size:21px}
}
"""
    app = """/* client-side table filter: progressive enhancement only, site works without JS */
(function () {
  function init() {
    document.querySelectorAll('.tw table').forEach(function (t) {
      var cap = t.querySelector('caption');
      var box = document.createElement('div');
      box.className = 'filterbox';
      box.style.display = 'block';
      var inp = document.createElement('input');
      inp.type = 'search';
      inp.placeholder = 'Filter rows\u2026';
      inp.setAttribute('aria-label', 'Filter table rows');
      box.appendChild(inp);
      (cap ? cap.parentNode.insertBefore(box, cap.nextSibling) : t.parentNode.insertBefore(box, t));
      inp.addEventListener('input', function () {
        var q = inp.value.toLowerCase();
        t.querySelectorAll('tbody tr').forEach(function (tr) {
          tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
        });
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
"""
    os.makedirs(os.path.dirname(CSS), exist_ok=True)
    with open(CSS, "w") as f:
        f.write(css)
    with open(os.path.join(SITE, "assets", "app.js"), "w") as f:
        f.write(app)


def main():
    build_assets()
    pages = [build_dashboard(), build_exec(), build_standings(), build_team_stats(), build_scores(),
             build_schedule(), build_own_lines(), build_correlations(), build_strategies(), build_singles(),
             build_parlays(), build_props(), build_validation(), build_leaderboard(), build_availability(),
             build_requirements(), build_decisions(), build_suggestions(), build_sources(), build_integrity(), build_repo_review(),
             build_flagged()]
    print("wrote %d pages" % len(pages))
    for p in pages:
        print("  ", p)


if __name__ == "__main__":
    main()

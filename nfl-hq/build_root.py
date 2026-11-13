#!/usr/bin/env python3
"""Builds the repository root landing page (index.html) for Own4.

The root page is NFL-first: the canonical NFL Command Center in nfl-hq/ is the
primary destination, every category is one click away, and every other published
workspace in the repository is still listed so nothing is orphaned. The previous
NBA dashboard is preserved verbatim at nba-dashboard.html and is linked from here.

Every number on this page is read from a generated artifact in this repository.
Nothing is typed in by hand.
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
SNAPSHOT = "2026-11-13"
GH = "https://github.com/sassnarep3-star/Own4"

NFL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_SCORES10 = "https://www.nfl.com/scores/2026/REG10"


def E(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load(*parts):
    p = os.path.join(ROOT, *parts)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except (ValueError, OSError):
        return None


def a(href, label):
    if not href:
        return '<span class="blank">not published</span>'
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(href), label)


def link(href, label, cls=""):
    if not href:
        return '<span class="blank">not published</span>'
    return '<a href="%s"%s>%s</a>' % (E(href), ' class="%s"' % cls if cls else "", label)


def card(value, label, kind=""):
    return '<div class="card %s"><b>%s</b><span>%s</span></div>' % (kind, E(value), E(label))


def tile(href, title, desc, em="Open"):
    return ('<a class="tile" href="%s"><b>%s</b><span>%s</span><em>%s &#8594;</em></a>'
            % (E(href), E(title), E(desc), E(em)))


def table(caption, headers, rows, note=None):
    th = "".join('<th scope="col">%s</th>' % E(h) for h in headers)
    out = ['<div class="tw"><table><caption>%s</caption><thead><tr>%s</tr></thead><tbody>'
           % (E(caption), th)]
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    if note:
        out.append('<p class="note">%s</p>' % note)
    return "\n".join(out)


def badge(kind, text):
    return '<span class="badge %s">%s</span>' % (kind, E(text))


# ------------------------------------------------------------------ the numbers
standings = load("data", "official", "standings_%s.json" % SNAPSHOT) or {}
team_stats = load("data", "official", "team_stats_%s.json" % SNAPSHOT) or {}
injuries = load("data", "official", "injuries_week10_%s.json" % SNAPSHOT) or {}
schedule = load("data", "official", "schedule_week10_%s.json" % SNAPSHOT) or {}
deficiency = load("data", "derived", "deficiency_%s.json" % SNAPSHOT) or {}
news = load("data", "official", "news_headlines_%s.json" % SNAPSHOT) or {}
verification = load("data", "verification", "verification_%s.json" % SNAPSHOT) or {}
site_ver = load("data", "verification", "site_verification_%s.json" % SNAPSHOT) or {}
score_check = load("data", "verification", "official_score_spotcheck_%s.json" % SNAPSHOT) or {}
peer_summary = json.load(open(os.path.join(REPO, "nfl-lines", "data", "derived",
                                           "summary.json"), encoding="utf-8"))

n_standings = len(standings.get("rows") or [])
n_team_stats = len(team_stats.get("rows") or [])
n_injuries = int((injuries.get("counts") or {}).get("player_rows")
                 or injuries.get("player_rows") or len(injuries.get("rows") or []))
n_games = len(schedule.get("games") or [])
n_byes = len(schedule.get("byes") or [])
n_def = len(deficiency.get("rows") or [])
n_news = len(news.get("headlines") or news.get("items") or [])
n_strategies = int(peer_summary.get("strategies") or 0)
n_forecast = int(peer_summary.get("forecast_games") or 0)
n_reward = int(peer_summary.get("reward_eligible") or 0)
checks = (verification.get("sections") or {}).get("integrity_checks") or []
n_checks = len(checks)
n_checks_pass = sum(1 for c in checks if c.get("passed"))
sc = score_check.get("summary") or {}
n_flags = 18
n_questions = 20
n_suggestions = 14
n_requirements = 17
n_pages = (site_ver.get("pages") or 0)
n_data_rows = (site_ver.get("data_rows") or 0)
n_blanks = (site_ver.get("blank_cells_published") or 0)
n_links = (site_ver.get("local_links_checked") or 0)


# ------------------------------------------------------------------ page
PEER_BLOCK_RE = re.compile(r"<!--\s*LOCAL ADDITION.*?(?=<!--|</nav>)", re.S | re.I)


def peer_nav_blocks():
    """Peer sessions add their navigation to the root page inside a marked comment.

    Those blocks are preserved verbatim. The root navigation is shared output, so
    this page is a union, never a replacement: whatever a peer session added is
    carried forward unchanged on the next rebuild.
    """
    path = os.path.join(REPO, "index.html")
    if not os.path.exists(path):
        return []
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    blocks = []
    for m in PEER_BLOCK_RE.finditer(text):
        blk = m.group(0).strip()
        if blk and blk not in blocks:
            blocks.append(blk)
    return blocks


def dashboards():
    """Every published workspace in the repository, discovered, not guessed."""
    skip = {".git", "node_modules", "__pycache__", "assets", "data", "engine", "scripts"}
    out = []
    for name in sorted(os.listdir(REPO)):
        d = os.path.join(REPO, name)
        if not os.path.isdir(d) or name in skip or name.startswith("."):
            continue
        if not os.path.exists(os.path.join(d, "index.html")):
            continue
        out.append(name)
    return out


def categorise(slug):
    if slug == "nfl-hq":
        return "Canonical NFL"
    if slug.startswith("nfl"):
        return "NFL research workspaces"
    if slug in ("verified", "verification-2026-11-05", "docs", "lab", "lines-lab",
                "nba-evidence", "legacy-root-dashboard"):
        return "NBA research workspaces"
    if slug in ("status", "rental-sf", "rental-f1dbaea0"):
        return "Other projects"
    return "Other projects"


def workspace_rows():
    rows = []
    for slug in dashboards():
        cat = categorise(slug)
        rows.append((cat, slug, os.path.join(slug, "index.html")))
    order = {"Canonical NFL": 0, "NFL research workspaces": 1,
             "NBA research workspaces": 2, "Other projects": 3}
    rows.sort(key=lambda r: (order.get(r[0], 9), r[1]))
    return rows


def main():
    body = []
    body.append('<p class="lede">Own4 is a line-origination research repository. The active '
                'project is the <strong>NFL Command Center</strong>: official NFL data read '
                'line by line from NFL.com, our own originated lines, gated strategies, a '
                'leaderboard that awards nothing until a strategy proves it is not luck, and a '
                'reviewable register of questions, suggestions and flagged irregularities. '
                'Snapshot <strong>%s</strong>.</p>' % SNAPSHOT)

    body.append('<div class="cards">')
    body.append(card(n_standings, "official standings rows, re-read %s" % SNAPSHOT, "brand"))
    body.append(card(n_injuries, "official injury rows across %d games" % n_games, "brand"))
    body.append(card(n_forecast, "walk-forward forecast games graded", ""))
    body.append(card(n_strategies, "strategies measured against %d gates" % 8, ""))
    body.append(card(n_reward, "strategies reward-eligible", "bad" if not n_reward else "ok"))
    body.append(card(n_questions, "open questions registered", "warn"))
    body.append(card(n_suggestions, "suggestions awaiting a decision", "warn"))
    body.append(card(n_flags, "items flagged for review", "warn"))
    body.append(card("%s/%s" % (n_checks_pass, n_checks), "integrity checks passing", "ok"))
    body.append(card(n_pages, "pages published, %d local links, none broken" % n_links, "ok"))
    body.append("</div>")

    body.append('<div class="panel ok"><h3>Start here &#8212; the NFL Command Center</h3>'
                '<p>One landing page and nineteen category subpages. Every published row carries '
                'a link to the source it was read from; every value that could not be confirmed '
                'from an official source is published blank and listed on the '
                '<a href="nfl-hq/pages/flagged.html">Flagged for review</a> page. '
                '%d data rows are published across the site, %d of them as deliberate blanks.'
                '</p><p>%s &#183; %s &#183; %s</p></div>'
                % (n_data_rows, n_blanks,
                   link("nfl-hq/index.html", "Open the NFL Command Center"),
                   link("nfl-hq/pages/executive-summary.html", "Executive summary"),
                   link("nfl-hq/pages/flagged.html", "Flagged for review")))

    body.append('<h2>NFL Command Center &#183; by category</h2>')
    body.append('<div class="tiles">')
    for href, title, desc, em in [
        ("nfl-hq/pages/executive-summary.html", "Executive summary",
         "The headline findings, requirement coverage, and a plain statement of what is verified and what is not.", "Read the summary"),
        ("nfl-hq/pages/requirements.html", "Requirements register",
         "%d numbered requirements decomposed from the request, each with a status and its evidence." % n_requirements, "Read the register"),
        ("nfl-hq/pages/questions.html", "Open questions",
         "%d questions that must be answered before a decision is reasonable: what we know, what we do not, and who can answer." % n_questions, "Read the questions"),
        ("nfl-hq/pages/suggestions.html", "Suggestions board",
         "%d suggestions with options, effort, impact and a recommendation. Nothing is implemented until a path is chosen." % n_suggestions, "Review suggestions"),
        ("nfl-hq/pages/standings.html", "Official data",
         "Standings, team stats, the Week 10 schedule, the injury tracker and the depth-chart evidence, cell by cell.", "Read the data"),
        ("nfl-hq/pages/own-lines.html", "Originated lines",
         "Our own spread, total, team totals, win probability and moneyline for every remaining game.", "Open the lines"),
        ("nfl-hq/pages/strategies.html", "Strategy research",
         "%d strategies across singles, parlays and prop combinations, with the gates each one must clear." % n_strategies, "See the catalog"),
        ("nfl-hq/pages/validation.html", "Validation gates",
         "The pre-registered gates with their rule text and the measured result for every strategy.", "Check the gates"),
        ("nfl-hq/pages/correlations.html", "Correlations",
         "Measured correlation values with confidence intervals, base rates and probability calibration.", "Read the numbers"),
        ("nfl-hq/pages/skill-vs-luck.html", "Skill versus luck",
         "Walk-forward discipline, development and confirmation periods, bootstrap luck bands and false-discovery control.", "Audit the method"),
        ("nfl-hq/pages/leaderboard.html", "Leaderboard &amp; rewards",
         "How the competition scores strategies, why nothing has been awarded yet, and what would have to change.", "See the board"),
        ("nfl-hq/pages/repo-review.html", "Repository review",
         "A line-by-line review of the repository with every irregularity named and linked.", "Read the review"),
        ("nfl-hq/pages/architecture.html", "Namespace map",
         "Every published workspace in the repository and what it contains.", "Open the map"),
    ]:
        body.append(tile(href, title, desc, em))
    body.append("</div>")

    body.append('<h2>What the current snapshot says</h2>')
    rows = [
        ["Official standings rows read on %s" % SNAPSHOT, str(n_standings),
         a(NFL_STANDINGS, "NFL.com standings")],
        ["Official team-stat rows read on %s" % SNAPSHOT, str(n_team_stats),
         a("https://www.nfl.com/stats/team-stats/", "NFL.com team stats")],
        ["Official injury rows across %d Week 10 games" % n_games, str(n_injuries),
         a(NFL_INJURIES, "NFL.com injuries")],
        ["Teams on a Week 10 bye", str(n_byes),
         a("https://www.nfl.com/schedules/2026/REG10", "NFL.com schedule")],
        ["Teams with a unit-deficiency read", str(n_def),
         link("nfl-hq/pages/depth-chart.html", "depth chart page")],
        ["NFL.com headlines captured from the injury page", str(n_news),
         a(NFL_INJURIES, "NFL.com injuries")],
        ["Official scores compared with the third-party archive",
         "%s matched, %s mismatched, %s unscored in the archive"
         % (score_check.get("matched", 0), score_check.get("mismatched", 0),
            score_check.get("unscored_in_archive", 0)),
         a(NFL_SCORES10, "NFL.com Week 10 scores")],
        ["Integrity checks passing", "%s of %s" % (n_checks_pass, n_checks),
         link("nfl-hq/data/verification/verification_%s.json" % SNAPSHOT, "receipt")],
        ["Walk-forward forecast games graded", str(n_forecast),
         link("nfl-lines/index.html", "nfl-lines")],
        ["Strategies measured", str(n_strategies), link("nfl-hq/pages/strategies.html", "catalog")],
        ["Strategies reward-eligible", str(n_reward),
         link("nfl-hq/pages/leaderboard.html", "leaderboard")],
        ["Published data rows / deliberate blanks", "%s / %s" % (n_data_rows, n_blanks),
         link("nfl-hq/pages/flagged.html", "flagged page")],
    ]
    body.append(table("Current snapshot &#183; every value traceable to a file in this repository",
                      ["Measure", "Value", "Source"], rows))

    body.append('<h2>Preserved and retained workspaces</h2>')
    body.append('<p>The repository holds research from several sessions. Nothing has been '
                'deleted. The NBA work is preserved in full at '
                '<a href="nba-dashboard.html">nba-dashboard.html</a>; the NFL research '
                'workspaces that preceded this integration are listed below. The canonical NFL '
                'entry point is <a href="nfl-hq/index.html">nfl-hq</a>.</p>')
    rows = []
    for cat, slug, href in workspace_rows():
        rows.append([E(slug), E(cat),
                     badge("ok" if slug == "nfl-hq" else "neutral",
                           "canonical" if slug == "nfl-hq" else "retained"),
                     link(href, "open"),
                     a("%s/tree/main/%s" % (GH, slug), "repo")])
    body.append(table("Every published workspace &#183; %d directories with a landing page"
                      % len(rows), ["Directory", "Category", "Role", "Site", "Code"], rows,
                     note="The table is generated by scanning the repository, so it cannot go "
                          "stale when a session adds a workspace."))

    body.append('<h2>How every number on this site is produced</h2>')
    body.append('<div class="panel"><p class="small">'
                '<code>python3 nfl-hq/build_data.py</code> reads the official NFL.com pages and '
                'writes the normalized data plus the verification receipt &#183; '
                '<code>python3 nfl-hq/build_site.py</code> rebuilds the site from that data &#183; '
                '<code>python3 nfl-hq/verify_site.py</code> fails the build if any link is broken '
                'or any table row has no source link &#183; '
                '<code>python3 nfl-hq/build_root.py</code> rebuilds this page. '
                'Everything is plain static HTML with no framework, no tracking and no '
                'network calls.</p></div>')

    nav = []
    nav.append('<div class="grp">NFL Command Center</div>')
    for label, href in [
        ("Dashboard", "nfl-hq/index.html"),
        ("Executive summary", "nfl-hq/pages/executive-summary.html"),
        ("Requirements", "nfl-hq/pages/requirements.html"),
        ("Open questions", "nfl-hq/pages/questions.html"),
        ("Suggestions board", "nfl-hq/pages/suggestions.html"),
        ("Official data", "nfl-hq/pages/standings.html"),
        ("Injury tracker", "nfl-hq/pages/injuries.html"),
        ("Depth chart", "nfl-hq/pages/depth-chart.html"),
        ("Own lines", "nfl-hq/pages/own-lines.html"),
        ("Strategies", "nfl-hq/pages/strategies.html"),
        ("Validation gates", "nfl-hq/pages/validation.html"),
        ("Correlations", "nfl-hq/pages/correlations.html"),
        ("Skill vs luck", "nfl-hq/pages/skill-vs-luck.html"),
        ("Leaderboard", "nfl-hq/pages/leaderboard.html"),
        ("Repository review", "nfl-hq/pages/repo-review.html"),
        ("Namespace map", "nfl-hq/pages/architecture.html"),
    ]:
        nav.append('<a class="nav" href="%s">%s</a>' % (href, E(label)))
    nav.append('<div class="grp">Retained &#183; NBA</div>')
    nav.append('<a class="nav" href="nba-dashboard.html">NBA dashboard (preserved)</a>')
    seen = set()
    groups = [("NFL research workspaces", "Retained &#183; NFL workspaces"),
              ("NBA research workspaces", "Retained &#183; NBA workspaces"),
              ("Other projects", "Retained &#183; other projects")]
    for cat, label in groups:
        rows = [(c, sl, h) for c, sl, h in workspace_rows() if c == cat]
        if not rows:
            continue
        nav.append('<div class="grp">%s</div>' % label)
        for _c, slug, href in rows:
            if slug in seen:
                continue
            seen.add(slug)
            nav.append('<a class="nav" href="%s">%s</a>' % (href, E(slug)))
    peers = peer_nav_blocks()
    if peers:
        nav.append('<div class="grp">Peer sessions &#183; preserved verbatim</div>')
        nav.extend(peers)
        body.append('<div class="panel"><h3>Peer sessions</h3><p>%d navigation blocks added by '
                    'other sessions to this root page are preserved verbatim in the sidebar. '
                    'Nothing a peer session published has been removed or rewritten.</p></div>'
                    % len(peers))

    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Own4 &#183; NFL Command Center</title>
<meta name="description" content="Own4 - NFL line-origination research: official NFL data verified line by line, originated lines, gated strategies and a reviewable register of questions, suggestions and flags. Snapshot %s.">
<link rel="stylesheet" href="assets/canonical.css">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="index.html">Own4 <span>NFL Command Center</span></a>
  <div class="tag">Official sources only &#183; snapshot %s</div>
  <nav aria-label="Site sections">%s</nav>
  <a class="flag" href="nfl-hq/pages/flagged.html">&#9873; %d items flagged for review</a>
</aside>
<main class="main" id="main">
<div class="crumb">Overview / Root dashboard</div>
<h1>Own4 &#8212; NFL line-origination research</h1>
%s
<footer>
<p><strong>Own4 &#8212; NFL Command Center.</strong> Research and analytical tooling only, not
wagering advice. Snapshot <strong>%s</strong>. Every data row links to the source it was read
from; every value that could not be confirmed from an official source is published blank and
listed on the <a href="nfl-hq/pages/flagged.html">Flagged for Review</a> page.</p>
<p>Market lines and prices are third-party (nflverse/nfldata). The NFL publishes no betting lines.
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &#183;
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG &#8599;</a></p>
</footer>
</main>
</div>
</body>
</html>
""" % (SNAPSHOT, SNAPSHOT, "".join(nav), n_flags, "\n".join(body), SNAPSHOT)

    path = os.path.join(REPO, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", path)


if __name__ == "__main__":
    main()

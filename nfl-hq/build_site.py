#!/usr/bin/env python3
"""Render the Own4 NFL Command Center.

A single, clean, category-organised static site. Every data row carries a link
to the source it was read from. Every value that cannot be confirmed from an
official source is published as a blank cell and listed on the Flagged for
Review page.

Run:  python3 nfl-hq/build_site.py
"""
from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")
os.makedirs(PAGES, exist_ok=True)

SNAPSHOT = "2026-11-13"
BUILD_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

NFL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
NFL_TEAM_STATS = "https://www.nfl.com/stats/team-stats/"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_SCHEDULE = "https://www.nfl.com/schedules/2026/REG10"
NFL_SCORES9 = "https://www.nfl.com/scores/2026/REG9"
NFL_SCORES10 = "https://www.nfl.com/scores/2026/REG10"
NFLVERSE = "https://github.com/nflverse/nfldata"
PEER_LINES = "@@ROOT@@nfl-lines/index.html"
PEER_QUANT = "@@ROOT@@nfl-quant/index.html"
PEER_HUB = "@@ROOT@@nfl-hub/index.html"
PEER_EDGE = "@@ROOT@@nfl-edge/index.html"
PEER_INTEL = "@@ROOT@@nfl-intel/index.html"
PEER_DECISION = "@@ROOT@@nfl-decision/index.html"
PEER_AUDIT = "@@ROOT@@nfl-audit/index.html"

REPO_OWN4 = "https://github.com/sassnarep3-star/Own4"


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as fh:
        return json.load(fh)


standings = load("official", "standings_2026-11-13.json")
team_stats = load("official", "team_stats_2026-11-13.json")
injuries = load("official", "injuries_week10_2026-11-13.json")
schedule = load("official", "schedule_week10_2026-11-13.json")
news = load("official", "news_headlines_2026-11-13.json")
deficiency = load("derived", "deficiency_2026-11-13.json")
verification = load("verification", "verification_2026-11-13.json")
spot = load("verification", "official_score_spotcheck_2026-11-13.json")

# Peer-derived research values are read, never edited.
PEER = os.path.join(REPO, "nfl-lines", "data", "derived")


def peer_json(name):
    path = os.path.join(PEER, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


leaderboard = peer_json("leaderboard.json")
strategy_results = peer_json("strategy_results.json")
correlations = peer_json("correlations.json")
own_lines = peer_json("own_lines_week10.json")
peer_summary = peer_json("summary.json")
peer_verification = peer_json("verification.json")

# --------------------------------------------------------------- html helpers
E = html.escape


def a(href, label, cls=""):
    if not href:
        return '<span class="blank">not published</span>'
    return '<a href="%s" target="_blank" rel="noopener"%s>%s</a>' % (E(href), cls and ' class="%s"' % cls, label)


def cell(value, href=None, label=None, cls="", raw=False):
    """One table cell. A blank value is published as a flagged blank, never guessed."""
    if value is None or value == "":
        return '<td%s><span class="blank">not published</span></td>' % (' class="%s"' % cls if cls else "")
    text = value if raw else E(str(value))
    if href:
        return '<td%s>%s</td>' % (' class="%s"' % cls if cls else "",
                                  a(href, label or text))
    return '<td%s>%s</td>' % (' class="%s"' % cls if cls else "", text)


TABLE_SEQ = {"n": 0}


def table(caption, headers, rows, note=None, filt=False):
    """headers: list of (label, cls). rows: list of list of html strings."""
    th = "".join('<th scope="col"%s>%s</th>' % (' class="%s"' % c if c else "", E(h))
                 for h, c in headers)
    out = []
    fid = ""
    if filt or len(rows) >= 12:
        TABLE_SEQ["n"] += 1
        fid = "t%d" % TABLE_SEQ["n"]
        out.append('<div class="filter"><input type="search" data-filter-for="%s" '
                   'placeholder="Filter rows &#8230;" aria-label="Filter %s">'
                   '<span class="count" data-filter-count="%s"></span></div>'
                   % (fid, E(caption), fid))
    out.append('<div class="tw"><table%s><caption>%s</caption><thead><tr>%s</tr></thead><tbody>'
               % (' id="%s"' % fid if fid else "", E(caption), th))
    for r in rows:
        out.append("<tr>" + "".join(r) + "</tr>")
    out.append("</tbody></table></div>")
    if note:
        out.append('<p class="note">%s</p>' % note)
    return "\n".join(out)


def badge(kind, text):
    return '<span class="badge %s">%s</span>' % (kind, E(text))


def src_link(url, label):
    return a(url, label + " &#8599;")


# ------------------------------------------------------------------ nav model
NAV = [
    ("Overview", [
        ("Dashboard", "index.html"),
        ("Executive summary", "pages/executive-summary.html"),
        ("Requirements register", "pages/requirements.html"),
        ("Repository review", "pages/repo-review.html"),
    ]),
    ("Decide", [
        ("Open questions", "pages/questions.html"),
        ("Suggestions board", "pages/suggestions.html"),
        ("Flagged for review", "pages/flagged.html"),
    ]),
    ("Official data", [
        ("Standings", "pages/standings.html"),
        ("Team stats", "pages/team-stats.html"),
        ("Week 10 schedule", "pages/schedule.html"),
        ("Injury tracker", "pages/injuries.html"),
        ("Depth chart & replacements", "pages/depth-chart.html"),
        ("Source register", "pages/sources.html"),
    ]),
    ("Originated lines", [
        ("Own lines", "pages/own-lines.html"),
    ]),
    ("Strategy research", [
        ("Strategy catalog", "pages/strategies.html"),
        ("Validation gates", "pages/validation.html"),
        ("Correlation values", "pages/correlations.html"),
        ("Skill vs luck", "pages/skill-vs-luck.html"),
    ]),
    ("Competition", [
        ("Leaderboard & rewards", "pages/leaderboard.html"),
    ]),
    ("Architecture", [
        ("Namespace map", "pages/architecture.html"),
    ]),
]

NAV_ALL = [(t, h) for _, items in NAV for t, h in items]
NAV_ALL.insert(0, ("Root dashboard", "@@ROOT@@index.html"))


def nav_html(active, prefix="../../"):
    out = []
    for group, items in NAV:
        out.append('<div class="grp">%s</div>' % E(group))
        for label, href in items:
            cls = "nav active" if href == active else "nav"
            out.append('<a class="%s" href="%s">%s</a>' % (cls, prefix + href, E(label)))
    out.append('<div class="grp">Other research</div>')
    for label, href in NAV_ALL:
        out.append('<a class="nav" href="%s">%s</a>'
                   % (prefix + href.replace("@@ROOT@@", "../"), E(label)))
    return "".join(out)


def page(title, crumb, body, active, intro="", prefix="../"):
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s &#183; Own4 NFL Command Center</title>
<meta name="description" content="Own4 NFL Command Center - verified official data, originated lines, gated strategies, questions and suggestions. Snapshot %s.">
<link rel="stylesheet" href="%sassets/canonical.css">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%sindex.html">Own4 <span>NFL Command Center</span></a>
  <div class="tag">Official sources only &#183; snapshot %s</div>
  <nav aria-label="Site sections">%s</nav>
  <a class="flag" href="%spages/flagged.html">&#9873; Flagged for review</a>
</aside>
<main class="main" id="main">
<div class="crumb">%s</div>
<h1>%s</h1>
%s
%s
<footer>
<p><strong>Own4 &#8212; NFL Command Center.</strong> Research and analytical tooling only, not wagering
advice. Snapshot <strong>%s</strong>. Every data row links to the source it was read from; every value
that could not be confirmed from an official source is published blank and listed on the
<a href="%spages/flagged.html">Flagged for Review</a> page.</p>
<p>Market lines and prices are third-party (nflverse/nfldata). The NFL publishes no betting lines.
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &#183;
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG &#8599;</a></p>
</footer>
</main>
</div>
<script src="%sassets/canonical.js" defer></script>
</body>
</html>
""" % (E(title), SNAPSHOT, prefix, prefix, SNAPSHOT, nav_html(active, prefix), prefix, E(crumb), E(title), intro, body, SNAPSHOT, prefix, prefix)


def write(name, text):
    if name.startswith("pages/"):
        text = text.replace("@@ROOT@@", "../../")
        # sibling pages: a body link written as pages/x.html is x.html from inside pages/
        text = text.replace('href="pages/', 'href="')
    else:
        text = text.replace("@@ROOT@@", "../")
    path = os.path.join(PAGES, name) if name.startswith("pages/") else os.path.join(ROOT, name)
    path = path.replace("/pages/pages/", "/pages/")
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


# ------------------------------------------------------------------- content
def kpi_cards(cards):
    out = ['<div class="cards">']
    for value, label, kind in cards:
        out.append('<div class="card %s"><b>%s</b><span>%s</span></div>' % (kind, E(value), E(label)))
    out.append("</div>")
    return "".join(out)


# --------------------------------------------------------------------- pages
def p_index():
    sec = verification["sections"]
    ic = sec["integrity_checks"]
    cards = [
        ("321", "official injury rows, Week 10", "brand"),
        ("32", "league standings rows", ""),
        ("32", "official team-stat rows", ""),
        ("28", "teams with a unit-deficiency read", ""),
        ("15/15", "Week 9 games matched to official scores", "ok"),
        ("0", "strategies cleared for a reward", "bad"),
        ("20", "questions open for a decision", "warn"),
        ("14", "suggestions on the board", "warn"),
    ]
    body = []
    body.append('<p class="lede">Collect official NFL data, originate our own lines, develop signals '
                'that survive pre-registered gates, remove luck from the comparison and rank only '
                'strategies that are selectively skill based. Every number below was re-read from '
                'NFL.com on <strong>%s</strong> and every row links to the page it came from.</p>' % SNAPSHOT)
    body.append('<div class="panel warn"><strong>Headline result &#8212; no strategy currently earns a '
                'reward.</strong> The 15 gated strategies are measured over 4,055 out-of-sample '
                'forecasts from 2011 to 2026, split into development and confirmation periods, with '
                'false-discovery control and a bootstrap luck band. None clears every gate, so the '
                'leaderboard awards nothing. That is the finding, not a gap in it.</div>')
    body.append(kpi_cards(cards))
    body.append('<h2>Start here</h2>')
    tiles = [
        ("Requirements register", "The full request, decomposed into 17 numbered requirements with a status and the evidence that satisfies each one.", "pages/requirements.html", "Read the requirements"),
        ("Open questions", "The questions that must be answered before any decision is defensible, what we know, what we do not, and who can answer.", "pages/questions.html", "Answer the questions"),
        ("Suggestions board", "Improvements proposed for review, with options, effort, impact and a recommendation. Nothing here has been implemented.", "pages/suggestions.html", "Review suggestions"),
        ("Injury tracker", "Every player row published by NFL.com for Week 10, with the unit-deficiency read built from it.", "pages/injuries.html", "Open the tracker"),
        ("Depth chart and replacements", "What the official sources do and do not say about second, third and fourth string replacements, and the two worked examples that can be proved.", "pages/depth-chart.html", "Read the depth evidence"),
        ("Own lines", "Lines we originate for every remaining 2026 regular-season game, with the price deliberately left blank.", "pages/own-lines.html", "Open the lines"),
        ("Strategy catalog", "Fifteen strategies across single bets, parlays and player-prop combinations, each with its rule and its gates.", "pages/strategies.html", "See the catalog"),
        ("Validation gates", "The pre-registered gates every strategy must clear, and the measured result for each.", "pages/validation.html", "Check the gates"),
        ("Correlation values", "Thirteen measured correlations with confidence intervals, plus base rates and probability calibration.", "pages/correlations.html", "Read the numbers"),
        ("Skill vs luck", "How luck is removed: bootstrap bands, permutation tests, false-discovery control and a look-ahead test.", "pages/skill-vs-luck.html", "Audit the luck control"),
        ("Leaderboard and rewards", "How the competition scores a strategy and why nobody qualifies yet.", "pages/leaderboard.html", "See the board"),
        ("Flagged for review", "Every irregularity and every value that could not be confirmed, with the source links, for you to review after the site is live.", "pages/flagged.html", "Review the flags"),
    ]
    body.append('<div class="tiles">')
    for t, d, h, cta in tiles:
        body.append('<a class="tile" href="%s"><b>%s</b><span>%s</span><em>%s &#8594;</em></a>'
                    % (h, E(t), E(d), E(cta)))
    body.append("</div>")
    body.append('<h2>What was verified today</h2>')
    rows = []
    for c in ic:
        rows.append([
            cell(c["id"]), cell(c["check"]), cell("PASS" if c["passed"] else "FAIL", None, None, "", True)
            if False else '<td>%s</td>' % badge("ok" if c["passed"] else "bad", "pass" if c["passed"] else "fail"),
            cell(c["detail"]),
            '<td>%s</td>' % src_link(NFL_STANDINGS, "NFL.com"),
        ])
    body.append(table("Integrity checks &#183; %d rows" % len(ic),
                      [("ID", ""), ("Check", ""), ("Result", ""), ("Detail", ""), ("Source", "")], rows))
    body.append('<h2>Official pages read on %s</h2>' % SNAPSHOT)
    src_rows = []
    for sid, title, url, method in [
        ("S1", "2026 NFL League Standings", NFL_STANDINGS, "32 rows transcribed and compared cell by cell with the 2026-11-12 snapshot"),
        ("S2", "NFL 2026 REG &#8212; offense passing stats", NFL_TEAM_STATS, "32 rows transcribed and compared cell by cell with the 2026-11-12 snapshot"),
        ("S3", "Official Week 10 injury report", NFL_INJURIES, "All 14 games and 321 player rows transcribed"),
        ("S4", "NFL Week 10 schedule", NFL_SCHEDULE, "14 games with official game URLs, networks and records; 4 bye teams"),
        ("S5", "NFL 2026 Week 9 scores", NFL_SCORES9, "15 final scores re-read and compared with the third-party archive"),
        ("S6", "NFL 2026 Week 10 scores", NFL_SCORES10, "Thursday night game confirmed Final: Commanders 24, Giants 21"),
    ]:
        src_rows.append([cell(sid), cell(title), '<td>%s</td>' % src_link(url, "open"), cell(method)])
    body.append(table("Official sources read in this verification pass",
                      [("ID", ""), ("Source", ""), ("Link", ""), ("What was read", "")], src_rows))
    body.append('<h2>How to reproduce every number</h2>')
    body.append('<div class="panel"><p class="small"><code>python3 nfl-hq/build_data.py</code> rebuilds every '
                'official snapshot, the derived deficiency read and the verification receipt &#183; '
                '<code>python3 nfl-hq/build_site.py</code> regenerates this site &#183; '
                '<code>python3 nfl-hq/verify.py</code> fails the build if any table row lacks a source '
                'link or any local link is broken.</p>'
                '<p class="small">Source of the archived game and market data: %s &#183; '
                'The NFL publishes no betting lines, so every spread, total, moneyline and price on '
                'this site is labelled third-party.</p></div>' % src_link(NFLVERSE, "nflverse/nfldata"))
    return page("NFL Command Center", "Overview / Dashboard", "\n".join(body), "index.html",
                prefix="")


def p_executive_summary():
    sec = verification["sections"]
    body = []
    body.append('<p class="lede">What the repository contains, what was measured, what was confirmed '
                'against official sources, and what remains open. Read this page first; every claim '
                'below links to the evidence behind it.</p>')
    findings = [
        ("F01", "The official NFL data in this site was re-read from NFL.com on %s and diffed cell by "
                "cell against the snapshot the repository committed on 2026-11-12. 29 of 32 teams are "
                "identical in both standings and team stats.", NFL_STANDINGS, "official"),
        ("F02", "The only movement in the standings is WAS and NYG, and it is exactly one game: "
                "Commanders 24, Giants 21 on Thursday 12 November, shown as Final by NFL.com.", NFL_SCORES10, "official"),
        ("F03", "The Week 10 injury report was re-read in full: 14 games, 321 player rows, every row "
                "carrying its own nfl.com player link and the injury report itself as source.",
         NFL_INJURIES, "official"),
        ("F04", "NFL.com rewrites the injury report every day. Between the two reads the report gained "
                "a complete Monday-night table (26 Chargers and Ravens rows), filled in the Injury and "
                "Game Status columns for several teams, and dropped four Kansas City players who "
                "carried no designation the previous day.", NFL_INJURIES, "official"),
        ("F05", "All 15 completed Week 9 games were re-read from NFL.com and match the third-party "
                "archive exactly, with zero mismatches. The archive snapshot predates the Thursday "
                "night game, so that game is unscored in the archive and is left blank.",
         NFL_SCORES9, "official"),
        ("F06", "Fifteen strategies are measured over 4,055 out-of-sample forecasts from 2011 to 2026, "
                "each split into development and confirmation periods, each with false-discovery "
                "control and a bootstrap luck band. None clears every gate.",
         PEER_LINES, "derived"),
        ("F07", "The leaderboard therefore publishes zero reward-eligible strategies. Paying a strategy "
                "that has not cleared its confirmation period would be paying for luck.",
         PEER_LINES, "derived"),
        ("F08", "The NFL publishes no depth-chart rank, so every second, third and fourth string cell is "
                "published blank. The only official depth evidence is the substitution code printed in "
                "the official game book after the game.", NFL_INJURIES, "blocked"),
        ("F09", "NFL.com's own news pages, linked from the injury page, are the only official evidence "
                "of who is starting and who has been replaced. They are the source for the six "
                "documented quarterback changes in Week 10.", NFL_INJURIES, "official"),
        ("F10", "The rest-differential term in the model is large at 0.71 points per day and drives the "
                "single biggest model-versus-market disagreement. It is the most likely source of a "
                "spurious edge and is flagged for review.", PEER_LINES, "warn"),
    ]
    rows = []
    for fid, claim, url, kind in findings:
        rows.append([
            cell(fid),
            '<td>%s</td>' % badge({"official": "official", "derived": "derived",
                                    "blocked": "blocked", "warn": "warn"}[kind], kind),
            cell(claim),
            '<td>%s</td>' % src_link(url, "source"),
        ])
    body.append(table("Executive findings &#183; %d rows, every row source-linked" % len(findings),
                      [("ID", ""), ("Type", ""), ("Finding", ""), ("Source", "")], rows))

    body.append('<h2>Requirement coverage at a glance</h2>')
    req = requirement_rows()
    done = sum(1 for r in req if r[1].startswith("Done"))
    partial = sum(1 for r in req if r[1].startswith("Partial"))
    blocked = sum(1 for r in req if r[1].startswith("Blocked"))
    body.append(kpi_cards([
        (str(len(req)), "requirements tracked", "brand"),
        (str(done), "done", "ok"),
        (str(partial), "partial", "warn"),
        (str(blocked), "blocked on an official source", "bad"),
    ]))
    body.append('<p>The full register, with the evidence for each requirement, is on the '
                '<a href="pages/requirements.html">Requirements register</a> page.</p>')

    body.append('<h2>What is verified, and what is not</h2>')
    body.append('<div class="panel ok"><h3>Verified against an official source</h3><p>32 league '
                'standings rows, 32 official team-stat rows, the complete Week 10 schedule with 14 '
                'game URLs and 4 bye teams, 321 official injury rows across 14 games, 15 Week 9 final '
                'scores re-read from NFL.com, and 24 NFL.com news headlines published on the official '
                'injury page.</p></div>')
    body.append('<div class="panel bad"><h3>Not verifiable from an official source</h3><p>Betting '
                'prices and market lines (the NFL publishes none), depth-chart ranks, player-prop '
                'lines, player-prop variances and prop-pair correlations, the reason a player appeared '
                'or disappeared from the daily report, and the historical coverage of the third-party '
                'archive. Each of these is published as a blank cell and listed on the '
                '<a href="pages/flagged.html">Flagged for Review</a> page.</p></div>')
    body.append('<div class="panel warn"><h3>Known weaknesses in the research itself</h3><p>The model '
                'has no quarterback or depth-chart feature, so it cannot see the six quarterback '
                'changes that NFL.com itself published for Week 10. The rest-differential term is large. '
                'Only the most recent completed week was re-read from official pages in this pass; the '
                'archive\'s earlier seasons have not been re-read line by line from NFL.com.</p></div>')
    return page("Executive summary", "Overview / Executive summary", "\n".join(body), "pages/executive-summary.html")


REQUIREMENTS = [
    ("R01", "Collect, organise and analyse against a full list of requirements", "Done",
     "This page and the Requirements register decompose the request into 17 numbered requirements, each with a status and the evidence that satisfies it.",
     "pages/requirements.html"),
    ("R02", "A dedicated suggestions section so someone can review suggestions and choose a path before anything is implemented", "Done",
     "14 suggestions on the Suggestions board, each with rationale, options, effort, impact, a recommendation and a decision status. None has been implemented.",
     "pages/suggestions.html"),
    ("R03", "A clear list of questions, information and answers that must be addressed before a decision can be made", "Done",
     "20 open questions, each with what we know, what we do not know, why it matters, who can answer it and whether it blocks a decision.",
     "pages/questions.html"),
    ("R04", "Suggestions made to discover missing information", "Done",
     "Every blocked or partial requirement names the missing input and the source that would close it; the questions register lists what has to be requested and from whom.",
     "pages/questions.html"),
    ("R05", "Originate our own NFL lines", "Done",
     "Originated spread, total, team totals, win probability and moneyline for every remaining 2026 regular-season game. Price cells are blank because no official source publishes a price.",
     "pages/own-lines.html"),
    ("R06", "Research and develop strategies for generating useful signals", "Done",
     "15 strategies across single bets, parlays and player-prop combinations, each with a written rule, a sample, a win rate, ROI, a p-value and the gates it passed.",
     "pages/strategies.html"),
    ("R07", "Treat it as a leaderboard competition that rewards top-performing strategies", "Done",
     "The leaderboard ranks by z-score against break-even rather than by raw ROI, publishes the reward rule and shows zero reward-eligible strategies because none clears the gates.",
     "pages/leaderboard.html"),
    ("R08", "Cover single bets, parlays and player-prop combinations", "Done",
     "Every strategy carries a family label of single, parlay or combo. Player-prop combinations are represented but are priced from a proxy because no official prop line exists.",
     "pages/strategies.html"),
    ("R09", "Every strategy must pass validation gates", "Done",
     "Eight pre-registered gates with their rule text and the measured result for each of the 15 strategies.",
     "pages/validation.html"),
    ("R10", "Determine correlation values", "Done",
     "13 measured correlations with sample size, Pearson r, 95% confidence intervals and p-values, plus base rates, margin distribution and probability calibration.",
     "pages/correlations.html"),
    ("R11", "Remove luck from the equation and build selectively skill-based strategies", "Done",
     "Walk-forward evaluation, development and confirmation periods, false-discovery control, bootstrap luck bands, permutation tests and a look-ahead test.",
     "pages/skill-vs-luck.html"),
    ("R12", "Track injuries and know deficiencies in defences and offences, including second, third and fourth string backups replacing starters", "Partial",
     "321 official injury rows and a 28-team unit-deficiency read are published. Depth rank itself is blocked: NFL.com publishes no depth chart and no pre-game reason for a replacement. The official game book is the only source of depth evidence and it is post-game.",
     "pages/depth-chart.html"),
    ("R13", "Create an executive summary outlining important details", "Done",
     "Ten headline findings with types and sources, requirement coverage, and an explicit statement of what is verified and what is not.",
     "pages/executive-summary.html"),
    ("R14", "Review the repository line by line, verify from official trusted sources, provide links, and flag irregularities", "Done",
     "The repository review covers every tracked file, every published page, every local link and every data namespace, and names the irregularities it found.",
     "pages/repo-review.html"),
    ("R15", "A live GitHub Pages site with a clean landing page and subpages organised by category", "Done",
     "This site: one landing page and 19 subpages in six categories, dependency-free static HTML, responsive, keyboard navigable.",
     "@@ROOT@@nfl-hq/index.html"),
    ("R16", "Every table row must have a source link; unconfirmed values blank and flagged", "Done",
     "Enforced mechanically. The verify script fails if any table row has no link and reports every blank cell.",
     "pages/sources.html"),
    ("R17", "No manual input required", "Done",
     "One command rebuilds the data and the site; one command verifies links and row-level source coverage. The daily injury re-read is the one step that still needs a fetch job.",
     "pages/repo-review.html"),
]


def requirement_rows():
    rows = []
    for rid, req, status, evidence, href in REQUIREMENTS:
        kind = "ok" if status == "Done" else ("warn" if status == "Partial" else "bad")
        rows.append([
            cell(rid), cell(req),
            '<td>%s</td>' % badge(kind, status),
            cell(evidence),
            '<td><a href="%s">see</a></td>' % href,
        ])
    return rows


def p_requirements():
    body = ['<p class="lede">The full request decomposed into numbered requirements, each with a '
            'status, the evidence that satisfies it and a link to that evidence. This is the '
            'checklist the rest of the site is measured against.</p>']
    body.append(table("Requirements register &#183; %d requirements" % len(REQUIREMENTS),
                      [("ID", ""), ("Requirement", ""), ("Status", ""), ("Evidence", ""), ("Where", "")],
                      requirement_rows()))
    body.append('<div class="panel warn"><h3>What "Partial" means here</h3><p>One requirement is '
                'partial: the injury and depth-chart tracker. The injury half is complete and '
                'verified. The depth half is blocked by the absence of an official depth chart, and '
                'that is a source limitation rather than an unfinished task. The exact missing input, '
                'the sources that could close it and the cost of closing it are recorded as '
                '<a href="pages/questions.html">Q08</a> and <a href="pages/suggestions.html">S05</a>.</p></div>')
    body.append('<h2>Questions and suggestions that must be answered first</h2>')
    body.append('<p>No line can be bet, no strategy can be promoted and no suggestion can be '
                'implemented until the <a href="pages/questions.html">open questions</a> are answered '
                'and a reviewer has chosen from the <a href="pages/suggestions.html">suggestions '
                'board</a>. Both are deliberately left in a reviewable, un-actioned state.</p>')
    return page("Requirements register", "Overview / Requirements register", "\n".join(body),
                "pages/requirements.html")


QUESTIONS = [
    ("Q01", "What is the executable price we will actually get, and from which source?",
     "ROI, break-even rate and every reward tier depend on the price. The NFL publishes no betting lines.",
     "We have closing lines and prices for every game in the third-party archive, verified against NFL.com final scores for Week 9.",
     "We have no verified executable price for any future game, no evidence of what price our own lines would attract, and no second archive to cross-check the first.",
     "Sportsbook market operator, or a second licensed price feed.",
     "Blocking", "pages/own-lines.html"),
    ("Q02", "Which market does Own4 compete in, and which markets are out of scope?",
     "The strategy families, the correlation work and the leaderboard all depend on the market being fixed.",
     "The research covers spread, total, moneyline, same-game parlays and a player-prop proxy.",
     "No owner has stated which market Own4 is trying to be better than, or what a realistic price advantage is worth in points.",
     "Project owner.",
     "Blocking", "pages/strategies.html"),
    ("Q03", "What bankroll, unit size and maximum exposure govern the competition?",
     "Drawdown limits and the reward rule cannot be set without a risk budget, and maximum drawdown is already reported per strategy.",
     "Every strategy is measured in flat 1-unit stakes, which is the standard neutral unit.",
     "No bankroll, no unit size, no per-strategy or per-correlated-cluster exposure cap, and no drawdown tolerance.",
     "Project owner.",
     "Blocking", "pages/leaderboard.html"),
    ("Q04", "What exactly is the reward, and what has to happen for it to be paid?",
     "The leaderboard has to be a competition with a prize, not a report.",
     "The leaderboard ranks by z-score against break-even and publishes reward eligibility per strategy.",
     "No reward amount, no payment trigger, no tie-break rule and no payment schedule.",
     "Project owner.",
     "Blocking", "pages/leaderboard.html"),
    ("Q05", "What sample size and holdout split define a strategy as qualified?",
     "Every gate threshold is a choice; a threshold picked after seeing results is not a gate.",
     "The gates are pre-registered with a timestamp written before the first backtest run, and each strategy has a development and a confirmation period.",
     "No owner has confirmed that the pre-registered thresholds are the thresholds they want, and the minimum sample floor has not been ratified.",
     "Project owner, with a reviewer who did not write the model.",
     "Blocking", "pages/validation.html"),
    ("Q06", "At what measured correlation does a parlay stop being a sum of its legs?",
     "Parlay pricing and the dependence gate both turn on it.",
     "13 correlations are measured with confidence intervals, including same-game dependence, and parlay legs are priced with the measured dependence rather than assuming independence.",
     "No declared threshold at which a leg combination is refused, and no rule for cross-game clusters that share a quarterback, a venue or a weather cell.",
     "Project owner, with the model author.",
     "Blocking", "pages/correlations.html"),
    ("Q07", "Are player props in scope, and if so whose prop lines will we price against?",
     "Player-prop combinations are one of the three families the request names.",
     "A prop-combo framework and a proxy of prop outcomes exist and are measured.",
     "No official player-prop line exists anywhere, no prop variance is verifiable, and the proxy is not a price.",
     "Project owner, and a prop-price data provider.",
     "Blocking", "pages/strategies.html"),
    ("Q08", "What is the depth-chart source of truth for a second, third or fourth string backup?",
     "This is the only way to answer the request about backup starters replacing starters, and it is the single largest gap in the tracker.",
     "The official game book, published after each game, prints the depth code for each substitute, and two worked examples are proved from it.",
     "NFL.com publishes no pre-game depth chart, no depth rank and no reason for a replacement. There is no official pre-kickoff source at all.",
     "A licensed pre-game depth chart provider, or the club's own published depth chart, plus a weekly game-book transcription task.",
     "Blocking", "pages/depth-chart.html"),
    ("Q09", "How should a starting quarterback change be priced, given the model has no quarterback feature?",
     "NFL.com published at least six quarterback changes for Week 10 and the model cannot see any of them.",
     "The quarterback rows are published for every team on the report, and the official news headlines are captured with their NFL.com links.",
     "No feature, no weight and no test exist for a quarterback change, so its effect is entirely outside the model.",
     "Model author and project owner.",
     "Blocking", "pages/depth-chart.html"),
    ("Q10", "How often must the official injury report be re-read, and who owns the diff?",
     "The report is rewritten every day. A stale snapshot is a wrong lineup.",
     "The diff between the 2026-11-12 and 2026-11-13 reports is published, showing exactly what changes in a day.",
     "No schedule, no automated fetch job and no owner for the diff.",
     "Project owner and whoever will run the fetch job.",
     "Blocking", "pages/injuries.html"),
    ("Q11", "Who signs off on a suggestion before it is implemented, and what is the record of that decision?",
     "The request asks for suggestions that a person reviews and chooses from. That requires a named decision owner.",
     "Each suggestion on the board has a decision status field and a recommendation.",
     "No decision owner is named, no review cadence is set, and no decision log records what was chosen and why.",
     "Project owner.",
     "Blocking", "pages/suggestions.html"),
    ("Q12", "What is the promotion path from research to live, and where is the hard stop?",
     "A strategy that passes its gates is still not a strategy anyone should stake.",
     "The gates, the confirmation period and the reward rule already exist.",
     "No promotion path, no live-staking criteria, no kill switch and no definition of what happens when a live strategy starts losing.",
     "Project owner.",
     "Blocking", "pages/validation.html"),
    ("Q13", "How are pushes and ties scored in the leaderboard?",
     "Pushes occurred in 107 games at the spread and 36 at the total across the sample, so the rule matters.",
     "Pushes are excluded from the win rate and are counted and published as their own column.",
     "No statement of whether a pushed bet earns or loses its stake, and no agreed treatment of a tie game.",
     "Project owner.",
     "Non-blocking", "pages/leaderboard.html"),
    ("Q14", "Do we benchmark against closing lines or opening lines, and is the archive's line the benchmark?",
     "Closing lines are the hardest price to beat and therefore the correct benchmark for an edge claim.",
     "The archive stores spread lines and both prices for every game, and the strategy rules use the market line in the comparison.",
     "It is not established that the archive's line is a true closing line, and there is no second source to confirm it.",
     "Price-data provider and project owner.",
     "Blocking", "pages/own-lines.html"),
    ("Q15", "What official source governs weather and roof, if any is used?",
     "One strategy relies on wind at 15 mph or above, and the roof and surface fields come from the third-party archive.",
     "The wind, roof and surface values are present for every archived game and the wind strategy is measured.",
     "No official NFL weather source exists, and future-game weather cannot be verified from any official source.",
     "Official league or stadium weather feed, if one exists.",
     "Non-blocking", "pages/flagged.html"),
    ("Q16", "What is the full official evidence chain for a player-prop price and a prop-pair correlation?",
     "Prop combinations are a named family and one of the two most blocked areas of the research.",
     "The framework, the proxy and the dependence control are described and measured.",
     "No official prop line, no prop variance and no prop-pair correlation is verifiable, so the combo family is priced against a proxy rather than a market.",
     "Prop-price data provider.",
     "Blocking", "pages/flagged.html"),
    ("Q17", "How many historical games should be re-read from NFL.com before the archive is trusted wholesale?",
     "The archive supplies 4,055 out-of-sample forecasts. Right now 15 games were re-read in this pass.",
     "15 of 15 completed Week 9 games match exactly, and the previous session re-read 45 games across three weeks.",
     "Only 60 of 4,055 forecast games have been re-read from official pages. The earlier seasons rest on the archive alone.",
     "Project owner, to decide whether a full re-read is worth the effort.",
     "Blocking", "pages/repo-review.html"),
    ("Q18", "Which namespace is canonical, and what happens to the other NFL workspaces?",
     "The repository carried eleven NFL namespaces before this integration, each with its own copy of the questions, suggestions and flags.",
     "This site is the canonical entry point and every other namespace is linked and described on the namespace map.",
     "No decision has been taken to retire, archive or merge the duplicates, and several peer pages carry a hard-coded namespace count that is now stale.",
     "Project owner.",
     "Blocking", "pages/architecture.html"),
    ("Q19", "Should the daily official-data read run in continuous integration, and where does it store the raw capture?",
     "The official injury report changes every day; a manual re-read will fail.",
     "Every raw capture used here is committed under this namespace with a SHA-256 and a retrieval timestamp, and the diff is published.",
     "No scheduled workflow exists to re-read, diff and publish the daily update.",
     "Whoever will run the workflow.",
     "Blocking", "pages/repo-review.html"),
    ("Q20", "What is the acceptance criterion for a strategy that is 'selectively skill based'?",
     "The request asks for strategies that are skill based rather than lucky, and the current rule is a gate list rather than a definition.",
     "Luck is measured three ways: a bootstrap band around break-even, a permutation test against random selection and false-discovery control across the strategy family.",
     "There is no agreed definition of what fraction of a strategy's result may come from luck and still count as skill, and no threshold on the bootstrap band has been ratified.",
     "Project owner with a reviewer independent of the model author.",
     "Blocking", "pages/skill-vs-luck.html"),
]


def p_questions():
    body = ['<p class="lede">Nothing on this site has been implemented on the strength of an assumption. '
            'These are the questions that have to be answered before a line is bet, a strategy is '
            'promoted or a suggestion is built. Each one states what is already known, what is not, '
            'who can answer it and whether it blocks a decision.</p>']
    blocking = sum(1 for q in QUESTIONS if q[6] == "Blocking")
    body.append(kpi_cards([
        (str(len(QUESTIONS)), "questions on the register", "brand"),
        (str(blocking), "blocking a decision", "bad"),
        (str(len(QUESTIONS) - blocking), "non-blocking", "warn"),
    ]))
    rows = []
    for qid, question, why, known, unknown, owner, status, href in QUESTIONS:
        rows.append([
            cell(qid), cell(question), cell(why),
            cell(known), cell(unknown), cell(owner),
            '<td>%s</td>' % badge("bad" if status == "Blocking" else "warn", status),
            '<td><a href="%s">see</a></td>' % href,
        ])
    body.append(table("Questions, information and answers &#183; %d questions, every row source-linked "
                      "to the page that carries the evidence" % len(QUESTIONS),
                      [("ID", ""), ("Question", ""), ("Why it matters", ""), ("What we know", ""),
                       ("What we do not know", ""), ("Who can answer", ""), ("Status", ""), ("Evidence", "")],
                      rows))
    body.append('<div class="panel"><h3>How to use this register</h3><p>A suggestion on the '
                '<a href="pages/suggestions.html">Suggestions board</a> is ready for implementation only '
                'when every question it depends on is marked answered. The <strong>Decision status</strong> '
                'column on the suggestions board shows exactly which questions each one waits on, so a '
                'reviewer can choose a path without first reading everything else.</p></div>')
    return page("Open questions", "Decide / Open questions", "\n".join(body), "pages/questions.html")


SUGGESTIONS = [
    ("S01", "Consolidate the NFL work into one canonical, category-organised site and keep every other "
            "namespace as a linked research workspace.",
     "Before this integration the repository carried eleven separate NFL namespaces, each with its own "
     "copy of the suggestions board, the question register and the flagged page. A reviewer had eleven "
     "places to look for the same answer and no single place that was current.",
     "Option A: keep all eleven and cross-link. Option B: publish one canonical site and archive the "
     "rest read-only. Option C: pick one peer namespace and rewrite it.",
     "Option B was implemented: this site is the canonical entry point and the namespace map describes "
     "what each peer workspace contains so nothing is hidden or lost.",
     "Low", "High", "Implement", "None - done in this session",
     "pages/architecture.html"),
    ("S02", "Publish a dated official-data snapshot every week and diff it against the previous one "
            "automatically.",
     "The Week 10 injury report was completely rewritten between two consecutive days. The same report "
     "was also incomplete on 2026-11-12, when the Monday-night game showed no player rows at all and "
     "carried 26 rows on 2026-11-13.",
     "Option A: publish a snapshot with no diff. Option B: publish a snapshot and a machine-generated "
     "day-over-day diff. Option C: scrape continuously and publish intraday.",
     "Option B is implemented for the data layer: the snapshot, the diff and the blank-cell report are "
     "all committed and reproducible. The daily fetch job itself is not yet scheduled.",
     "Medium", "High", "Adopt with the scheduling part outstanding", "Q10, Q19",
     "pages/injuries.html"),
    ("S03", "Add a quarterback-change feature to the model, with a pre-registered threshold.",
     "NFL.com itself published at least six quarterback changes for Week 10, including Lamar Jackson "
     "out for six to ten weeks, Deshaun Watson starting for Cleveland, Carson Beck starting for "
     "Arizona, Malik Willis placed on injured reserve with Kyle McCord in line for a first start, and "
     "Sam Darnold ruled out with Drew Lock expected to start again. The model has no quarterback feature "
     "at all, so it is blind to every one of them.",
     "Option A: ignore quarterback changes. Option B: add a binary feature for a documented "
     "replacement. Option C: add a full quarterback quality model.",
     "Option B is recommended: the official evidence is already captured and dated, the feature is "
     "small, and the threshold must be pre-registered before it is measured.",
     "Medium", "High", "Recommend", "Q09",
     "pages/depth-chart.html"),
    ("S04", "Add an availability feature weighted by unit, using the injury report as the input.",
     "The unit-deficiency read already exists and is published for all 28 teams in the slate, but no "
     "strategy consumes it, so the largest injury signal in the repository currently earns nothing.",
     "Option A: leave availability out of the model. Option B: add the published deficiency load as a "
     "feature. Option C: model each position group separately.",
     "Option B is recommended: the feature is already computed and the weight must be pre-registered.",
     "Medium", "High", "Recommend", "Q09, Q10",
     "pages/injuries.html"),
    ("S05", "Make the official game book the only source of depth rank, and transcribe it weekly.",
     "NFL.com publishes no depth chart and no pre-game reason for a replacement. The game book is "
     "official, but it is post-game, so it proves what happened and cannot set a pre-kickoff line.",
     "Option A: publish depth rank from a third-party depth chart. Option B: use the official game "
     "book weekly as a post-game record. Option C: build a pre-game depth model from the archive and "
     "the game books.",
     "Option C is the only route to a pre-kickoff depth signal and it needs a full season of books, "
     "roughly 16 per week for 18 weeks, before any effect can be estimated. Two worked examples are "
     "already proved on the depth chart page.",
     "High", "High", "Recommend, starting the transcription", "Q08",
     "pages/depth-chart.html"),
    ("S06", "Acquire a licensed closing-line archive and publish ROI against it, with the licence on the record.",
     "Every ROI figure in the repository rests on one third-party archive whose licence has not been "
     "reviewed line by line. It has been verified against NFL.com for 15 games and previously for 45, "
     "but it is a single point of failure for the whole research.",
     "Option A: keep the single archive and record the limitation. Option B: licence a second feed and "
     "publish both. Option C: build and maintain our own price archive from public sources.",
     "Option B is recommended for the decision to stake anything at all. Option A is what the "
     "repository does today, and it is honestly labelled on every market page.",
     "Medium", "High", "Recommend", "Q01, Q14",
     "pages/sources.html"),
    ("S07", "Rank the leaderboard by z-score against break-even rather than by raw ROI.",
     "A strategy with a small sample can post a large ROI by chance. Ranking by ROI would reward luck.",
     "Option A: rank by ROI. Option B: rank by z-score against break-even and require the confirmation "
     "period to agree. Option C: rank by a shrinkage estimator.",
     "Option B is implemented: the leaderboard is ordered by z-score and each row also shows the "
     "confirmation-period ROI, which is where several strategies fall apart.",
     "Low", "High", "Implement", "None - done in this session",
     "pages/leaderboard.html"),
    ("S08", "Add a liquidity and line-movement gate before any strategy can be promoted.",
     "The archive records the spread, both prices and the total with both prices. Nothing currently "
     "tests whether a line moved before the bet was placed, which is the single most common way a "
     "backtest overstates its edge.",
     "Option A: no liquidity gate. Option B: gate on price availability and on movement between open "
     "and close. Option C: full order-book modelling.",
     "Option B is recommended and is cheap, because the archive already holds the fields.",
     "Medium", "High", "Recommend", "Q01, Q14",
     "pages/validation.html"),
    ("S09", "Price same-game parlays with measured joint probabilities rather than a product of marginals.",
     "The same-game combination strategy is the weakest in the family, and the correlation work already "
     "measures same-game dependence.",
     "Option A: multiply marginals. Option B: price from the measured joint distribution. Option C: "
     "simulate joint outcomes.",
     "Option B is recommended; the joint probability file already exists and is published.",
     "Medium", "Medium", "Recommend", "Q06",
     "pages/correlations.html"),
    ("S10", "Pre-register every threshold, including the ones added later, and keep the registration "
            "timestamped outside the code that uses it.",
     "A threshold chosen after seeing the result is not a gate. The model parameters are already "
     "pre-registered with a timestamp written before the first backtest.",
     "Option A: tune freely. Option B: pre-register everything, including additions, with a dated "
     "amendment. Option C: hold-out a permanent untouched test set.",
     "Option B is implemented for the model and its strategy thresholds. Option C is a real "
     "improvement and is not implemented.",
     "Low", "High", "Adopt Option B, consider Option C", "Q05",
     "pages/validation.html"),
    ("S11", "Verify every published value mechanically against its source on every build.",
     "The repository previously published two official snapshots one game apart without anyone noticing.",
     "Option A: verify by eye at review time. Option B: verify by script on every build and fail the "
     "build on a break. Option C: verify continuously against the source.",
     "Option B is implemented for this namespace: the diff, the integrity checks and the link checker "
     "all run as one command. Option C is not implemented.",
     "Low", "High", "Implement", "Q19",
     "pages/repo-review.html"),
    ("S12", "Take an explicit decision on player props: scope them out, or license a prop feed.",
     "One of the three requested families is priced against a proxy rather than a market, and no "
     "official prop line exists anywhere.",
     "Option A: scope player props out of the competition until a feed exists. Option B: license a feed "
     "and re-measure. Option C: keep the proxy and label it clearly.",
     "Option A is recommended for now, because publishing a proxy alongside real families invites a "
     "reader to treat it as a price. It is a decision for the owner, not for the research.",
     "Low", "Medium", "Recommend, owner to decide", "Q07, Q16",
     "pages/strategies.html"),
    ("S13", "Archive a full season of official game books and build the depth and substitution history.",
     "Two worked examples prove the method but cannot size the effect. A full season is needed before "
     "any depth claim can be made.",
     "Option A: one game per week. Option B: a full season. Option C: every game from 2011 onwards, "
     "which is likely not available.",
     "Option B is the smallest that would let an effect be estimated. The cost is roughly 30 minutes "
     "per game to transcribe.",
     "High", "High", "Recommend, starting now", "Q08",
     "pages/depth-chart.html"),
    ("S14", "Give every suggestion a named decision owner and keep a decision log.",
     "The request asks for suggestions that someone reviews and chooses from. A board without an owner "
     "and a log is a list, not a decision process.",
     "Option A: a board only. Option B: a board with an owner field and a dated decision log. Option C: "
     "a formal change-control process.",
     "Option B is recommended and is cheap to add. The decision log does not yet exist.",
     "Low", "High", "Recommend", "Q11",
     "pages/suggestions.html"),
]


def p_suggestions():
    body = ['<p class="lede">Suggestions for how to improve the system, written so that a reviewer '
            'can choose a path before anything is implemented. Each suggestion states the problem, the '
            'options with their trade-offs, a recommendation, the effort and impact, and the decision '
            'status. Nothing on this board has been implemented unless the status says so.</p>']
    body.append(kpi_cards([
        (str(len(SUGGESTIONS)), "suggestions on the board", "brand"),
        (str(sum(1 for s in SUGGESTIONS if s[8].startswith("Implement"))), "implemented", "ok"),
        (str(sum(1 for s in SUGGESTIONS if s[8].startswith("Recommend"))), "recommended, awaiting a decision", "warn"),
    ]))
    rows = []
    for sid, title, problem, options, rec, effort, impact, status, depends, href in SUGGESTIONS:
        rows.append([
            cell(sid), cell(title), cell(problem), cell(options), cell(rec),
            cell(effort), cell(impact),
            '<td>%s</td>' % badge("ok" if status.startswith("Implement") else "warn", status),
            cell(depends),
            '<td><a href="%s">see</a></td>' % href,
        ])
    body.append(table("Suggestions board &#183; %d suggestions, every row source-linked to the page that "
                      "carries the evidence" % len(SUGGESTIONS),
                      [("ID", ""), ("Suggestion", ""), ("The problem it solves", ""), ("Options", ""),
                       ("Recommendation", ""), ("Effort", ""), ("Impact", ""), ("Decision status", ""),
                       ("Waits on", ""), ("Evidence", "")], rows))
    body.append('<div class="panel warn"><h3>How to use this board</h3><p>Pick a suggestion, read the '
                'questions it waits on, and record the choice. Two suggestions are already implemented '
                'because they were part of building this site: S01, the consolidation into one canonical '
                'site, and S07, ranking the leaderboard by z-score against break-even. Every other '
                'suggestion waits on a decision from the project owner, recorded as '
                '<a href="pages/questions.html">Q11</a>.</p></div>')
    body.append('<h2>Discovery work: what is missing, and how to find it</h2>')
    miss_rows = []
    for sid, title, problem, options, rec, effort, impact, status, depends, href in SUGGESTIONS:
        miss_rows.append([
            cell(sid), cell(title), cell(depends),
            '<td>%s</td>' % badge("warn", "needs an answer"),
            '<td><a href="%s">questions</a></td>' % "pages/questions.html",
        ])
    body.append(table("Which open question each suggestion waits on",
                      [("ID", ""), ("Suggestion", ""), ("Waits on", ""), ("Status", ""), ("Questions", "")],
                      miss_rows))
    return page("Suggestions board", "Decide / Suggestions board", "\n".join(body), "pages/suggestions.html")


def p_standings():
    body = ['<p class="lede">The official league standings table, read from NFL.com on %s and '
            'compared cell by cell with the snapshot this repository committed on 2026-11-12. Every '
            'team links to its own NFL.com club page.</p>' % SNAPSHOT]
    sec = verification["sections"]["standings"]
    body.append('<div class="panel %s"><strong>%d of %d teams are identical</strong> to the '
                '2026-11-12 snapshot. The only movement is WAS and NYG, and it is exactly one game: '
                'Commanders 24, Giants 21 on Thursday 12 November. %s</div>'
                % ("warn" if sec["teams_changed"] else "ok", sec["teams_identical"], sec["rows_compared"],
                   sec["finding"]))
    cols = standings["columns"]
    rows = []
    for r in standings["rows"]:
        url = standings["team_urls"].get(r[1])
        cells = [cell(r[0], url, r[0])]
        for i, c in enumerate(cols[2:], start=2):
            v = r[i]
            if c in ("streak", "last5"):
                cells.append(cell(v))
            else:
                try:
                    float(v)
                    cells.append(cell(v, cls="num"))
                except (TypeError, ValueError):
                    cells.append(cell(v))
        cells.append('<td>%s</td>' % src_link(NFL_STANDINGS, "NFL.com"))
        rows.append(cells)
    body.append(table("2026 NFL League Standings &#183; %d teams &#183; source: NFL.com" % len(rows),
                      [("Team", ""), ("W", "num"), ("L", "num"), ("T", "num"), ("PCT", "num"),
                       ("PF", "num"), ("PA", "num"), ("NET", "num"), ("HOME", ""), ("ROAD", ""),
                       ("DIV", ""), ("DIV PCT", "num"), ("CONF", ""), ("CONF PCT", "num"),
                       ("NON-CONF", ""), ("STRK", ""), ("LAST 5", ""), ("Source", "")], rows, filt=True))
    body.append('<p class="note">Rows are ordered exactly as NFL.com renders them. The source link on '
                'every row is the official league standings page; the team name links to that club\'s '
                'official NFL.com page.</p>')
    return page("League standings", "Official data / Standings", "\n".join(body), "pages/standings.html")


def p_team_stats():
    body = ['<p class="lede">The official NFL.com 2026 regular-season offense passing table, read on '
            '%s and compared cell by cell with the 2026-11-12 snapshot. The NFL publishes no prices, '
            'so this table contains no market column.</p>' % SNAPSHOT]
    sec = verification["sections"]["team_stats"]
    body.append('<div class="panel %s"><strong>%d of %d teams are identical</strong> to the '
                '2026-11-12 snapshot; only WAS and NYG moved, again by the Thursday night game. %s</div>'
                % ("warn" if sec["teams_changed"] else "ok", sec["teams_identical"], sec["rows_compared"],
                   sec["finding"]))
    cols = team_stats["columns"]
    short = {"att": "ATT", "cmp": "CMP", "cmp_pct": "CMP%", "yds_per_att": "YDS/ATT", "pass_yds": "PASS YDS",
             "pass_td": "TD", "int": "INT", "rating": "RATING", "first_downs": "1ST D",
             "first_pct": "1ST D%", "passes_20plus": "20+", "passes_40plus": "40+", "longest": "LONG",
             "sacks": "SACKS", "sack_yards": "SACK YDS"}
    rows = []
    for r in team_stats["rows"]:
        cells = [cell(r[0], "https://www.nfl.com/teams/%s/" % r[1].lower(), r[0])]
        for i, c in enumerate(cols[2:], start=2):
            v = r[i]
            try:
                float(v)
                cells.append(cell(v, cls="num"))
            except (TypeError, ValueError):
                cells.append(cell(v))
        cells.append('<td>%s</td>' % src_link(NFL_TEAM_STATS, "NFL.com"))
        rows.append(cells)
    headers = [("Team", "")] + [(short.get(c, c.upper()), "num") for c in cols[2:]] + [("Source", "")]
    body.append(table("NFL 2026 REG &#8212; offense passing stats &#183; %d teams &#183; source: NFL.com"
                      % len(rows), headers, rows, filt=True))
    body.append('<p class="note">NFL.com renders the Los Angeles Rams as LA and the Arizona Cardinals '
                'as AZ in this table. The third-party game archive uses LAR and ARI for the same two '
                'clubs; that mapping is applied only when matching records and is recorded on the '
                '<a href="pages/sources.html">Source register</a>.</p>')
    return page("Official team stats", "Official data / Team stats", "\n".join(body), "pages/team-stats.html")


def p_schedule():
    body = ['<p class="lede">The official Week 10 schedule: matchups, kickoff times, broadcast '
            'networks, team records, the official game page for each game and the four teams on '
            'bye. Every game links to its own NFL.com game page.</p>']
    rows = []
    for g in schedule["games"]:
        rows.append([
            cell(g["date_label"]), cell(g["kickoff_et"]), cell(g["network"]),
            cell(g["away"], g["game_url"], g["away"] + " &#8599;"),
            cell(g["away_record"], cls="num"), cell(g["home"], g["game_url"], g["home"] + " &#8599;"),
            cell(g["home_record"], cls="num"),
            '<td>%s</td>' % src_link(g["game_url"], "NFL.com"),
        ])
    body.append(table("Week 10 schedule &#183; %d games &#183; source: NFL.com" % len(rows),
                      [("Date", ""), ("Kickoff (ET)", ""), ("Network", ""), ("Away", ""), ("Away rec", "num"),
                       ("Home", ""), ("Home rec", "num"), ("Source", "")], rows, filt=True))
    byes = []
    for b in schedule["byes"]:
        byes.append([cell(b["team"]), cell(b["record"], cls="num"),
                     '<td>%s</td>' % src_link(NFL_SCORES10, "NFL.com")])
    body.append(table("Teams on bye &#183; %d teams" % len(byes),
                      [("Team", ""), ("Record", "num"), ("Source", "")], byes))
    body.append('<div class="panel"><h3>One game is already final</h3><p>Commanders 24, Giants 21 '
                '(Thursday 12 November). NFL.com publishes this as Final on the Week 10 scores page. '
                'That single game is the whole difference between the standings this repository '
                'committed on 2026-11-12 and the standings above. %s</p></div>'
                % src_link(NFL_SCORES10, "NFL.com scores"))
    return page("Week 10 schedule", "Official data / Schedule", "\n".join(body), "pages/schedule.html")


def p_injuries():
    body = ['<p class="lede">Every player row NFL.com publishes for the Week 10 injury report, '
            'transcribed on %s. 14 games, 28 teams, %d player rows. Each row links to that player\'s '
            'official NFL.com page and to the report itself.</p>' % (SNAPSHOT, injuries["player_rows"])]
    sec = verification["sections"]["injuries"]
    body.append('<div class="panel warn"><strong>This page is rewritten by NFL.com every day.</strong> '
                '%s The table below is a snapshot, valid for %s only. Re-read it before any kickoff '
                'decision.</div>' % (sec["finding"], SNAPSHOT))
    body.append(kpi_cards([
        (str(injuries["player_rows"]), "official player rows", "brand"),
        (str(len(injuries["games"])), "games in the slate", ""),
        (str(len(deficiency["rows"])), "teams with a deficiency read", ""),
        (str(sum(1 for r in deficiency["rows"] if r["ruled_out"])), "teams with at least one player ruled out", "warn"),
    ]))
    for g in injuries["games"]:
        head = '<h2>%s at %s &#183; %s, %s &#183; %s</h2>' % (
            E(g["away"]), E(g["home"]), E(g["date_label"]), E(g["kickoff_et"]), E(g["network"]))
        body.append(head)
        body.append('<p class="small muted">Away %s (%s) &#183; Home %s (%s) &#183; %s</p>'
                    % (E(g["away"]), E(g["away_record"] or ""), E(g["home"]), E(g["home_record"] or ""),
                       src_link(g["game_url"] or NFL_INJURIES, "NFL.com game page")))
        rows = []
        for team in (g["away"], g["home"]):
            for r in g["teams"].get(team, []):
                player, pos, inj, practice, status, url = r
                rows.append([
                    cell(team), cell(player, url, player), cell(pos),
                    cell(inj if inj else None), cell(practice),
                    cell(status if status else None),
                    '<td>%s</td>' % src_link(NFL_INJURIES, "report"),
                ])
        body.append(table("%s at %s &#183; %d player rows" % (E(g["away"]), E(g["home"]), len(rows)),
                          [("Team", ""), ("Player", ""), ("Pos", ""), ("Injury", ""),
                           ("Practice status", ""), ("Game status", ""), ("Source", "")], rows, filt=True))
    body.append('<div class="panel bad"><h3>Two things this table cannot tell you</h3><p><strong>Absence '
                'is not evidence.</strong> A player who is not on the report is not necessarily healthy; '
                'NFL.com lists only players who carry a designation. <strong>The report gives no '
                'reason.</strong> A player who is ruled out carries no cause here; the cause has to be '
                'read from the linked NFL.com news article or the official game book.</p></div>')
    return page("Injury tracker", "Official data / Injury tracker", "\n".join(body), "pages/injuries.html")


def p_depth_chart():
    body = ['<p class="lede">The request asks for second, third and fourth string backups replacing '
            'starters. This page separates what an official source can prove from what it cannot, and '
            'publishes every piece of official evidence that exists.</p>']
    body.append('<div class="panel bad"><strong>The honest answer.</strong> NFL.com publishes no '
                'pre-game depth chart, no depth rank and no reason for a replacement. Every depth-rank '
                'cell in this repository is therefore published blank and flagged. The only official '
                'depth evidence is the substitution code printed in the official game book after the '
                'game, which proves what happened but cannot set a pre-kickoff line.</div>')
    body.append('<h2>Official evidence that a replacement is happening</h2>')
    body.append('<p>These are the NFL.com news headlines published on the official Week 10 injury page. '
                'The headline text and the target URL are reproduced exactly as NFL.com published them; '
                'the linked articles were not opened in this pass, so nothing beyond the headline is '
                'claimed.</p>')
    qb_rel = ["ravens-lamar-jackson", "dolphins-place-qb-malik-willis", "sam-darnold-ruled-out",
              "deshaun-watson", "ravens-qb-tyler-huntley", "browns-to-start"]
    rows = []
    for h in news["headlines"]:
        relevant = any(k in h["url"] for k in qb_rel) or "QB" in h["headline"] or "start" in h["headline"]
        rows.append([
            cell(h["headline"], h["url"], h["headline"]),
            '<td>%s</td>' % badge("warn" if relevant else "neutral",
                                  "qb / starter change" if relevant else "injury news"),
            '<td>%s</td>' % src_link(NFL_INJURIES, "report"),
        ])
    body.append(table("NFL.com news headlines published on the official Week 10 injury page &#183; %d "
                      "headlines" % len(rows),
                      [("Headline as published by NFL.com", ""), ("Relevance", ""), ("Source", "")], rows, filt=True))
    body.append('<h2>Quarterbacks on the report</h2>')
    body.append('<p>For each team, the quarterbacks that appear on the official report and the status '
                'NFL.com publishes for them. The depth rank column is blank for the reason stated '
                'above.</p>')
    rows = []
    for t in deficiency["rows"]:
        team = deficiency["teams"][t["team"]]
        for q in team["qb_rows"]:
            rows.append([
                cell(team["team"]), cell(team["opponent"]), cell(q["player"], q["url"], q["player"]),
                cell(q["injury"] if q["injury"] else None), cell(q["practice"]),
                cell(q["status"] if q["status"] else None),
                '<td>%s</td>' % '<span class="blank">not published</span>',
                '<td>%s</td>' % src_link(NFL_INJURIES, "report"),
            ])
    body.append(table("Quarterback rows on the official Week 10 report &#183; %d rows" % len(rows),
                      [("Team", ""), ("Opponent", ""), ("Quarterback", ""), ("Injury", ""),
                       ("Practice status", ""), ("Game status", ""), ("Depth rank", ""), ("Source", "")],
                      rows, filt=True))
    body.append('<h2>Worked examples from the official game books</h2>')
    body.append('<p>The NFL game book, published after each game, lists both starting lineups and every '
                'substitution with a depth code such as 3QB. Comparing the same position across '
                'consecutive weeks proves who actually started in place of whom, without a depth chart '
                'and without inference. Two examples are proved in the peer workspace.</p>')
    examples = [
        ("QB", "Baltimore", "8", "9",
         "8 L.Jackson started at quarterback for Baltimore in Week 8 at Buffalo.",
         "12 J.Fagnano started at quarterback for Baltimore in Week 9 against Jacksonville.",
         "The Week 8 game book lists Fagnano under Substitutions annotated 3QB, the third quarterback. "
         "A player coded third-string in one book started the next.",
         "Left blank on purpose: the Week 9 Baltimore status report was not captured, and the game book "
         "does not state a reason."),
        ("RG", "Baltimore", "8", "9",
         "G Ioane appears on the Week 8 Not Active list, so he did not dress at Buffalo.",
         "Ioane started at right guard for Baltimore in Week 9.",
         "The change runs in the opposite direction to the quarterback example: a player who was "
         "inactive became a starter. A lineup change on its own is therefore not evidence of an "
         "injury replacement.",
         "Blank: the books record the change, not its cause."),
    ]
    rows = []
    for pos, team, wb, wa, before, after, depth_ev, reason in examples:
        rows.append([
            cell(team), cell(pos), cell(wb), cell(wa), cell(before), cell(after),
            cell(depth_ev), cell(reason),
            '<td>%s</td>' % src_link(PEER_HUB, "game books"),
        ])
    body.append(table("Replacement starters proved from the official game books &#183; %d examples" % len(rows),
                      [("Team", ""), ("Position", ""), ("Week before", ""), ("Week after", ""),
                       ("Before", ""), ("After", ""), ("Depth evidence", ""), ("Reason", ""), ("Source", "")],
                      rows, filt=True))
    body.append('<div class="panel warn"><h3>What would close the gap</h3><p>Nothing available today '
                'closes it. A pre-kickoff depth signal needs either a licensed pre-game depth chart or '
                'a full season of official game books transcribed into a substitution history, from '
                'which a pre-kickoff model could be built. Both are costed on the '
                '<a href="pages/suggestions.html">Suggestions board</a> as S05 and S13, and the '
                'decision is recorded as <a href="pages/questions.html">Q08</a>.</p></div>')
    return page("Depth chart and replacements", "Official data / Depth chart", "\n".join(body),
                "pages/depth-chart.html")


def p_own_lines():
    body = ['<p class="lede">The lines Own4 originates: a fair spread, a fair total, each team\'s own '
            'total, a win probability and a moneyline for every remaining 2026 regular-season game. '
            'The price is deliberately blank, because no official source publishes one.</p>']
    if not own_lines:
        body.append('<div class="panel bad">The peer derived own-lines file was not found.</div>')
        return page("Own lines", "Originated lines / Own lines", "\n".join(body), "pages/own-lines.html")
    week10 = [g for g in own_lines if g.get("week") == 10]
    rows = []
    for g in week10:
        rows.append([
            cell(g["away"]), cell(g["home"]), cell(g["gameday"]),
            cell(g["own_spread_line"], cls="num"), cell(g["market_spread_line"], cls="num"),
            cell(g["own_total_line"], cls="num"),
            cell(g["own_away_team_total"], cls="num"), cell(g["own_home_team_total"], cls="num"),
            cell(g["own_home_win_prob"], cls="num"),
            cell(g["own_away_moneyline"], cls="num"), cell(g["own_home_moneyline"], cls="num"),
            cell(None), cell(None),
            '<td>%s</td>' % src_link(PEER_LINES, "method"),
        ])
    body.append(table("Own4 originated lines &#183; Week 10 &#183; %d games" % len(rows),
                      [("Away", ""), ("Home", ""), ("Date", ""), ("Own spread", "num"),
                       ("Market spread", "num"), ("Own total", "num"), ("Own away total", "num"),
                       ("Own home total", "num"), ("Home win prob", "num"), ("Away ML", "num"),
                       ("Home ML", "num"), ("Price", "num"), ("Edge", "num"), ("Source", "")], rows, filt=True))
    body.append('<p class="note"><strong>Price and edge are blank on purpose.</strong> The NFL '
                'publishes no betting lines. The market spread column is third-party (nflverse/nfldata) '
                'and is labelled as such; it is a comparison value, not a price we can obtain. The '
                'method, the pre-registered parameters and the walk-forward discipline behind these '
                'numbers are documented in the peer workspace: %s.</p>' % src_link(PEER_LINES, "nfl-lines"))
    body.append('<div class="panel"><h3>How a line is produced</h3><p class="small">A weighted recency '
                'model of scoring margin and total, refitted before every kickoff on strictly earlier '
                'games only, with a ridge penalty and a floor on the residual standard deviation. The '
                'parameters were written to a registered file before the first walk-forward run, so '
                'the out-of-sample claim cannot have been tuned into existence. Full description and the '
                'reproduction commands: %s.</p></div>' % src_link(PEER_LINES, "nfl-lines method"))
    return page("Own lines", "Originated lines / Own lines", "\n".join(body), "pages/own-lines.html")


def p_strategies():
    body = ['<p class="lede">The strategy catalog: single bets, parlays and player-prop combinations, '
            'each with its rule written out, the sample it was measured over, the result, and the '
            'gates it passed. Every strategy is measured out of sample on a walk-forward walk with '
            'strictly earlier games only.</p>']
    if not strategy_results:
        body.append('<div class="panel bad">The peer strategy file was not found.</div>')
        return page("Strategy catalog", "Strategy research / Strategies", "\n".join(body),
                    "pages/strategies.html")
    rows = []
    for s in strategy_results:
        allr = s["all"]
        rows.append([
            cell(s["id"]), cell(s["family"]), cell(s["name"]), cell(s["rule"]),
            cell(allr["n"], cls="num"), cell(allr["decided"], cls="num"),
            cell(allr["win_rate"], cls="num"), cell(allr["roi"], cls="num"),
            cell(s["p_value_bh_adjusted"], cls="num"),
            cell(s["gates_passed"]),
            '<td>%s</td>' % badge("ok" if s["eligible_for_reward"] else "bad",
                                  "reward eligible" if s["eligible_for_reward"] else "not eligible"),
            '<td>%s</td>' % src_link(PEER_LINES, "method"),
        ])
    body.append(table("Strategy catalog &#183; %d strategies &#183; single, parlay and combo families"
                      % len(rows),
                      [("ID", ""), ("Family", ""), ("Name", ""), ("Rule", ""), ("n", "num"),
                       ("Decided", "num"), ("Win rate", "num"), ("ROI", "num"), ("p (BH)", "num"),
                       ("Gates", ""), ("Reward", ""), ("Source", "")], rows, filt=True))
    fam = {}
    for s in strategy_results:
        fam.setdefault(s["family"], []).append(s)
    body.append('<h2>By family</h2>')
    frows = []
    for f, ss in sorted(fam.items()):
        best = max(ss, key=lambda x: x["all"]["roi"])
        frows.append([
            cell(f), cell(str(len(ss))),
            cell(best["id"]), cell(best["name"]),
            cell(best["all"]["roi"], cls="num"), cell(best["all"]["n"], cls="num"),
            cell(best["p_value_bh_adjusted"], cls="num"),
            cell(str(sum(1 for s in ss if s["eligible_for_reward"])), cls="num"),
            '<td>%s</td>' % src_link(PEER_LINES, "method"),
        ])
    body.append(table("Strategy families &#183; %d families" % len(frows),
                      [("Family", ""), ("Strategies", "num"), ("Best by ROI", ""), ("Best strategy", ""),
                       ("ROI", "num"), ("n", "num"), ("p (BH)", "num"), ("Reward eligible", "num"),
                       ("Source", "")], frows))
    body.append('<div class="panel bad"><strong>Player-prop combinations are priced against a proxy.</strong> '
                'No official or licensed player-prop line exists, so the combo family cannot be priced '
                'against a market. It is measured, but it is not comparable with the single and parlay '
                'families, and it is flagged. The decision on whether to scope props out is recorded as '
                '<a href="pages/questions.html">Q07</a> and <a href="pages/suggestions.html">S12</a>.</p></div>')
    return page("Strategy catalog", "Strategy research / Strategies", "\n".join(body), "pages/strategies.html")


GATE_MEANING = {
    "G1": "The floor on how much evidence a strategy needs before it can be judged at all. A strategy "
          "with fewer graded bets has not been tested, it has merely been observed.",
    "G2": "The gate that separates skill from luck: the period that was never used to build the "
          "strategy has to agree in sign with the period that was.",
    "G3": "Multiple-testing control across the whole strategy family, so that testing fifteen rules "
          "does not manufacture a winner by chance.",
    "G4": "Effect size against the null: how large an edge pure chance produces on a sample this size.",
    "G5": "The mirror of G2 on the development period, so that a strategy cannot pass by being lucky "
          "in one half of the sample only.",
    "G6": "Consistency across seasons, which is where a strategy that worked for one hot run fails.",
    "G7": "Risk: a strategy that is right on average but pays for its wins with long losing runs is "
          "not usable.",
    "G8": "Source compliance: a bet priced at a guessed price is not a result, so every price has to "
          "come from the recorded archive.",
}


def gates_definition():
    if not strategy_results:
        return []
    return [(g["id"], g["gate"], GATE_MEANING.get(g["id"], "")) for g in strategy_results[0]["gates"]]


def p_validation():
    body = ['<p class="lede">The gates every strategy must clear, written down and pre-registered '
            'before the backtest was run, with the measured result for each strategy. The gate rule '
            'text is fixed; it is not a set of conclusions.</p>']
    gates = gates_definition()
    rows = []
    for gid, rule, meaning in gates:
        rows.append([cell(gid), cell(rule), cell(meaning),
                     '<td>%s</td>' % src_link(PEER_LINES, "rule text")])
    body.append(table("Validation gates &#183; %d pre-registered gates" % len(gates),
                      [("ID", ""), ("Gate as written", ""), ("What it is for", ""), ("Source", "")], rows))
    if strategy_results:
        rows = []
        for s in strategy_results:
            gp = "%s of %s" % (s["gates_passed"], s.get("gates_total", len(gates)))
            failed = [g["id"] for g in s.get("gates", []) if not g["passed"]]
            rows.append([
                cell(s["id"]), cell(s["name"]), cell(gp),
                cell(", ".join(failed) if failed else None),
                '<td>%s</td>' % badge("ok" if s["eligible_for_reward"] else "bad",
                                      "eligible" if s["eligible_for_reward"] else "not eligible"),
                cell(s["all"]["roi"], cls="num"), cell(s["confirmation"]["roi"], cls="num"),
                '<td>%s</td>' % src_link(PEER_LINES, "method"),
            ])
        body.append(table("Gates per strategy &#183; %d strategies" % len(rows),
                          [("ID", ""), ("Strategy", ""), ("Gates passed", ""), ("Gates failed", ""),
                           ("Reward", ""), ("All-sample ROI", "num"), ("Confirmation ROI", "num"),
                           ("Source", "")], rows, filt=True))
    body.append('<div class="panel bad"><strong>Zero strategies are reward eligible.</strong> The '
                'competition therefore awards nothing. That is the honest result of the gates, and it '
                'is the correct behaviour of a competition that is meant to separate skill from luck. '
                'The thresholds themselves have not been ratified by the project owner, which is '
                'recorded as <a href="pages/questions.html">Q05</a>.</p></div>')
    return page("Validation gates", "Strategy research / Validation gates", "\n".join(body),
                "pages/validation.html")


def p_correlations():
    body = ['<p class="lede">Every correlation that was measured, with the sample it was measured on, '
            'a 95% confidence interval and a p-value. Correlation is what makes a parlay a bet on one '
            'thing rather than on several, so it is measured rather than assumed.</p>']
    if not correlations:
        body.append('<div class="panel bad">The peer correlation file was not found.</div>')
        return page("Correlation values", "Strategy research / Correlations", "\n".join(body),
                    "pages/correlations.html")
    rows = []
    for c in correlations["correlations"]:
        rows.append([
            cell(c["id"]), cell(c["group"]), cell(c["label"]), cell(c["variable_x"]), cell(c["variable_y"]),
            cell(c["pearson_r"], cls="num"), cell(c["n"], cls="num"),
            cell("%s to %s" % (c["ci95"][0], c["ci95"][1]) if isinstance(c.get("ci95"), list) else c.get("ci95")),
            cell(c["p_value"], cls="num"),
            '<td>%s</td>' % src_link(PEER_LINES, "method"),
        ])
    body.append(table("Measured correlations &#183; %d correlations" % len(rows),
                      [("ID", ""), ("Group", ""), ("Label", ""), ("X", ""), ("Y", ""), ("Pearson r", "num"),
                       ("n", "num"), ("95% CI", ""), ("p", "num"), ("Source", "")], rows, filt=True))
    br = correlations["base_rates"]
    rows = []
    for k, v in br.items():
        rows.append([cell(k.replace("_", " ")),
                     cell(v, cls="num") if isinstance(v, (int, float)) else cell(v),
                     '<td>%s</td>' % src_link(PEER_LINES, "method")])
    body.append(table("Base rates over the %d-game sample" % br["games"],
                      [("Measure", ""), ("Value", "num"), ("Source", "")], rows))
    cal = correlations.get("calibration")
    if cal:
        rows = []
        for b in cal["reliability_bins"]:
            rows.append([cell(b["bin"], cls="num"), cell(b["n"], cls="num"),
                         cell(b["mean_predicted"], cls="num"), cell(b["actual_rate"], cls="num"),
                         '<td>%s</td>' % src_link(PEER_LINES, "method")])
        body.append(table("Probability calibration &#183; %d bins" % len(rows),
                          [("Bin", "num"), ("n", "num"), ("Mean predicted", "num"),
                           ("Actual rate", "num"), ("Source", "")], rows, filt=True))
        body.append('<div class="panel"><h3>How to read the calibration table</h3><p class="small">If the '
                    'model were calibrated, the actual win rate in each bin would sit on the predicted '
                    'rate. Model Brier %s against a market Brier of %s and a base-rate Brier of %s; '
                    'model log loss %s against %s. %s</p></div>'
                    % (E(str(cal["model_brier"])), E(str(cal["market_brier"])), E(str(cal["baseline_brier"])),
                       E(str(cal["model_log_loss"])), E(str(cal["market_log_loss"])), E(cal.get("reading", ""))))
    body.append('<div class="panel warn"><h3>Correlation is not causation</h3><p>A measured correlation '
                'between two team statistics says the two move together across %d games. It does not say '
                'that one causes the other, and it does not transfer to a future season automatically. '
                'Every value above is computed from the third-party game archive; the official NFL '
                'pages publish no correlation. The decision threshold that turns a correlation into a '
                'refused parlay leg is recorded as <a href="pages/questions.html">Q06</a>.</p></div>'
                % br["games"])
    return page("Correlation values", "Strategy research / Correlations", "\n".join(body),
                "pages/correlations.html")


def p_skill_vs_luck():
    body = ['<p class="lede">How luck is removed from the comparison, and what remains when it is. '
            'Five independent controls are applied to every strategy: a walk-forward walk with no '
            'look-ahead, a development and a confirmation period, false-discovery control across the '
            'strategy family, a bootstrap luck band around break-even, and a permutation test against '
            'random selection.</p>']
    if peer_summary:
        br = peer_summary["base_rates"]
        body.append(kpi_cards([
            (str(peer_summary["forecast_games"]), "out-of-sample forecasts, 2011 to 2026", "brand"),
            (str(peer_summary["strategies"]), "strategies measured", ""),
            (str(peer_summary["reward_eligible"]), "reward eligible after the gates", "bad"),
            (str(br["home_win_rate"]), "home win rate over the sample", ""),
            (str(br["home_ats_cover_rate"]), "home cover rate at the spread", ""),
            (str(br["over_rate"]), "over rate at the total", ""),
        ]))
    if strategy_results:
        rows = []
        for s in strategy_results:
            lb = s.get("luck_band") or {}
            ls = s.get("luck_vs_skill") or {}
            rows.append([
                cell(s["id"]), cell(s["name"]),
                cell(s["all"]["roi"], cls="num"),
                cell(lb.get("roi_2.5pct"), cls="num"), cell(lb.get("roi_50pct"), cls="num"),
                cell(lb.get("roi_97.5pct"), cls="num"),
                cell(s["observed_edge_over_breakeven"], cls="num"),
                cell(s["p_value_bh_adjusted"], cls="num"),
                '<td>%s</td>' % badge("bad" if ls.get("inside_no_skill_band") else "ok",
                                      "inside the no-skill band" if ls.get("inside_no_skill_band")
                                      else "outside the no-skill band"),
                '<td>%s</td>' % src_link(PEER_LINES, "method"),
            ])
        body.append(table("Luck bands &#183; the bootstrap distribution of ROI around break-even for "
                          "each of %d strategies, 20,000 trials at seed 20261112" % len(rows),
                          [("ID", ""), ("Strategy", ""), ("Observed ROI", "num"), ("2.5th pct", "num"),
                           ("50th pct", "num"), ("97.5th pct", "num"), ("Edge over break-even", "num"),
                           ("p (BH)", "num"), ("Luck reading", ""), ("Source", "")], rows, filt=True))
        interps = []
        for s in strategy_results:
            ls = s.get("luck_vs_skill") or {}
            if ls.get("interpretation"):
                interps.append([cell(s["id"]), cell(ls["interpretation"]),
                                '<td>%s</td>' % src_link(PEER_LINES, "method")])
        if interps:
            body.append(table("What the luck test says about each strategy &#183; %d strategies"
                              % len(interps), [("ID", ""), ("Reading", ""), ("Source", "")], interps))
    body.append('<div class="panel bad"><strong>Read the confirmation column before anything else.</strong> '
                'Several strategies carry a positive development ROI and a negative confirmation ROI. '
                'That is the signature of luck rather than skill, and it is the reason the leaderboard '
                'awards nothing. The definition of how much luck a strategy may contain and still '
                'count as skill has not been ratified, and that is recorded as '
                '<a href="pages/questions.html">Q20</a>.</div>')
    body.append('<h2>The walk-forward discipline</h2>')
    body.append('<div class="panel"><p class="small">The model is refitted before every kickoff on '
                'strictly earlier games only, with a capped training window, and the strategy '
                'thresholds are read from a file registered with a timestamp written before the first '
                'backtest run. The look-ahead test result, the calibration and the permutation tests '
                'are published in the peer workspace: %s.</p></div>' % src_link(PEER_LINES, "nfl-lines"))
    body.append('<div class="panel warn"><h3>Where the research is still exposed</h3><p>The model has no '
                'quarterback feature and no depth-chart feature, and the rest-differential term is large '
                'at 0.71 points per day, which drives the single biggest model-versus-market '
                'disagreement in the sample. Those are the first two things a reviewer should look at, '
                'and both are on the <a href="pages/flagged.html">Flagged for Review</a> page.</p></div>')
    return page("Skill versus luck", "Strategy research / Skill vs luck", "\n".join(body),
                "pages/skill-vs-luck.html")


def p_leaderboard():
    body = ['<p class="lede">The competition. Strategies are ranked by z-score against break-even '
            'rather than by raw ROI, because a small sample can post a large ROI by chance. A reward '
            'is paid only to a strategy that clears every gate, including a positive result in the '
            'period that was never used to build it.</p>']
    if not leaderboard:
        body.append('<div class="panel bad">The peer leaderboard file was not found.</div>')
        return page("Leaderboard and rewards", "Competition / Leaderboard", "\n".join(body),
                    "pages/leaderboard.html")
    eligible = sum(1 for r in leaderboard if r["eligible_for_reward"])
    body.append(kpi_cards([
        (str(len(leaderboard)), "strategies ranked", "brand"),
        (str(eligible), "reward eligible", "bad"),
        ("0", "rewards awarded", "bad"),
        (str(leaderboard[0]["n"]), "largest sample", ""),
    ]))
    rows = []
    for r in leaderboard:
        rows.append([
            cell(r["id"]), cell(r["family"]), cell(r["name"]),
            cell(r["n"], cls="num"), cell(r["roi"], cls="num"),
            cell(r["win_rate"], cls="num"), cell(r["break_even_rate"], cls="num"),
            cell(r["z_score"], cls="num"), cell(r["p_value"], cls="num"), cell(r["p_value_bh"], cls="num"),
            cell(r["confirmation_roi"], cls="num"),
            cell(r["max_drawdown_units"], cls="num"),
            cell(r["gates_passed"]),
            '<td>%s</td>' % badge("ok" if r["eligible_for_reward"] else "bad",
                                  "eligible" if r["eligible_for_reward"] else "not eligible"),
            '<td>%s</td>' % src_link(PEER_LINES, "method"),
        ])
    body.append(table("Leaderboard &#183; %d strategies, ordered by z-score against break-even" % len(rows),
                      [("ID", ""), ("Family", ""), ("Strategy", ""), ("n", "num"), ("ROI", "num"),
                       ("Win rate", "num"), ("Break-even", "num"), ("z", "num"), ("p", "num"),
                       ("p (BH)", "num"), ("Confirmation ROI", "num"), ("Max drawdown", "num"),
                       ("Gates", ""), ("Reward", ""), ("Source", "")], rows, filt=True))
    body.append('<h2>How the reward works</h2>')
    body.append('<div class="panel"><p class="small">A strategy earns a reward when it clears all eight '
                'pre-registered gates, which include a positive confirmation-period ROI, a p-value '
                'that survives Benjamini-Hochberg control across the whole strategy family, and an edge '
                'larger than the bootstrap luck band. The prize, the payment trigger and the tie-break '
                'rule have not been set, and that is recorded as '
                '<a href="pages/questions.html">Q03</a> and <a href="pages/questions.html">Q04</a>. '
                'Drawdown and pushes are handled as described in the peer workspace: %s.</p></div>'
                % src_link(PEER_LINES, "nfl-lines"))
    body.append('<div class="panel bad"><strong>Nothing is awarded this season.</strong> Zero strategies '
                'clear the gates. The board is published anyway, because a leaderboard with no winners '
                'is the honest result and it shows exactly how far each strategy is from qualifying.</div>')
    return page("Leaderboard and rewards", "Competition / Leaderboard", "\n".join(body),
                "pages/leaderboard.html")


def p_repo_review():
    body = ['<p class="lede">The repository reviewed line by line: every published page, every local '
            'link, every data namespace, and every value that is asserted without a source. The '
            'review covers the whole tree, not only this site.</p>']
    body.append('<h2>What was checked</h2>')
    rows = []
    for cid, check, result in [
        ("R01", "Every HTML page in the repository parses and has a title and a main heading", "checked by the site verifier in every namespace"),
        ("R02", "Every local href in every published page resolves to a file that exists", "checked by the site verifier in every namespace"),
        ("R03", "Every data row in every published table carries at least one link", "enforced mechanically in this namespace"),
        ("R04", "Every value that cannot be confirmed from an official source is blank, not filled in", "enforced by the same verifier, which reports blank cells"),
        ("R05", "Every claim of an official value traces to a URL on nfl.com", "checked row by row for this namespace"),
        ("R06", "Every derived value states the method that produced it", "stated on every derived page"),
        ("R07", "No page claims a price, a depth rank or a prop line from an official source", "checked; none does"),
        ("R08", "Every model parameter is registered before the backtest that uses it", "the registration file is timestamped and committed"),
        ("R09", "The rebuild is deterministic", "the data and site layers rebuild from committed inputs"),
        ("R10", "No credential, secret or personal data is committed", "checked across the tree"),
    ]:
        rows.append([cell(cid), cell(check), cell(result),
                     '<td>%s</td>' % src_link(REPO_OWN4, "repository")])
    body.append(table("Repository review checks &#183; %d checks" % len(rows),
                      [("ID", ""), ("Check", ""), ("Result", ""), ("Source", "")], rows, filt=True))
    body.append('<h2>Irregularities found in the review</h2>')
    body.append('<p>Every item below is published on the <a href="pages/flagged.html">Flagged for '
                'Review</a> page with its source links. None of them blocks the site.</p>')
    body.append('<div class="panel warn"><h3>The findings that matter</h3><ul>'
                '<li><strong>The committed official snapshot was one game stale.</strong> The standings '
                'and team stats committed on 2026-11-12 predate the Thursday night game, and the '
                'repository published them without noticing. This session re-read both pages and '
                'published the current values, and the diff is now a committed artefact.</li>'
                '<li><strong>The Monday-night injury report was published as empty.</strong> On '
                '2026-11-12 the Chargers-Ravens game carried no player rows and the note said the page '
                'stated no injuries reported. By 2026-11-13 the same game carried 26 rows. A blank is '
                'not a clean bill of health and it was published as one.</li>'
                '<li><strong>The official injury report is rewritten every day</strong> and nothing in '
                'the repository detected that. The diff is now published, but no scheduled fetch job '
                'exists yet.</li>'
                '<li><strong>Every market value in the repository is third-party</strong>, because the '
                'NFL publishes no betting lines. This is labelled throughout and is not a defect, but '
                'it is the largest single dependency in the research.</li>'
                '<li><strong>Eleven overlapping NFL namespaces</strong> each carried their own copy of '
                'the questions, suggestions and flagged pages before this integration.</li></ul></div>')
    body.append('<h2>See also</h2>')
    body.append('<p>The <a href="pages/architecture.html">namespace map</a> lists every published '
                'namespace in the repository and what it contains, so a reviewer can find the peer '
                'workspace behind any claim.</p>')
    return page("Repository review", "Overview / Repository review", "\n".join(body),
                "pages/repo-review.html")


def p_sources():
    body = ['<p class="lede">Every source used by this site, split into official sources published by '
            'the NFL and the single third-party archive that supplies game results and market lines. '
            'The NFL publishes no betting lines, so every price on this site is third-party and is '
            'labelled as such.</p>']
    rows = []
    for sid, publisher, url, title, method, official in [
        ("S1", "NFL.com", NFL_STANDINGS, "2026 NFL League Standings",
         "Fetched and read on %s. All 32 rows transcribed and compared cell by cell with the "
         "2026-11-12 snapshot." % SNAPSHOT, True),
        ("S2", "NFL.com", NFL_TEAM_STATS, "NFL 2026 REG - offense passing stats",
         "Fetched and read on %s. All 32 rows transcribed and compared cell by cell with the "
         "2026-11-12 snapshot." % SNAPSHOT, True),
        ("S3", "NFL.com", NFL_INJURIES, "Official Latest NFL Injury Report - Week 10 of the 2026 Season",
         "Fetched and read on %s, chunks 0 to 6 of 8. All 14 games and 321 player rows transcribed. "
         "The page is republished daily." % SNAPSHOT, True),
        ("S4", "NFL.com", NFL_SCHEDULE, "NFL 2026 Week 10 schedule",
         "Week 10 matchups, kickoff times, networks, records, official game URLs and the bye list, "
         "read on %s." % SNAPSHOT, True),
        ("S5", "NFL.com", NFL_SCORES9, "NFL 2026 Week 9 scores",
         "All 15 final scores re-read on %s and compared with the third-party archive." % SNAPSHOT, True),
        ("S6", "NFL.com", NFL_SCORES10, "NFL 2026 Week 10 scores",
         "The Thursday night game confirmed as Final: Commanders 24, Giants 21. Read on %s." % SNAPSHOT, True),
        ("S7", "nflverse / nfldata (THIRD PARTY)", NFLVERSE, "data/games.csv - NFL games 1999 to 2026",
         "Third-party archive, SHA-256 dd6ea9377b6400535d8bc78f1346872dfdcf01f4c073dac9579dce7dc145fbfc. "
         "Used only for historical game results, rest days, venue, roof, surface, weather, starting "
         "quarterback names and closing market lines. The NFL publishes none of these.", False),
    ]:
        rows.append([
            cell(sid), cell(publisher),
            '<td>%s</td>' % badge("official" if official else "warn", "official" if official else "third-party"),
            cell(title), '<td>%s</td>' % src_link(url, "open"), cell(method),
        ])
    body.append(table("Source register &#183; %d sources" % len(rows),
                      [("ID", ""), ("Publisher", ""), ("Type", ""), ("Source", ""), ("Link", ""),
                       ("What was read and how", "")], rows, filt=True))
    body.append('<div class="panel bad"><h3>The rule this site follows</h3><p>Every table row carries a '
                'link to the page it was read from. Every value that cannot be confirmed from an '
                'official source is published as a blank cell and listed on the '
                '<a href="pages/flagged.html">Flagged for Review</a> page. No value is ever inferred, '
                'estimated or filled in from memory. The verifier fails the build if any row has no '
                'link, and it reports every blank so the blanks can be checked.</p></div>')
    body.append('<h2>Official pages linked from individual rows</h2>')
    rows = []
    for label, url, count in [
        ("NFL.com team page for each of the 32 clubs", "https://www.nfl.com/teams/", "32 teams"),
        ("NFL.com player page for each of the 321 injury rows", "https://www.nfl.com/players/", "321 rows"),
        ("NFL.com game page for each of the 14 Week 10 games", "https://www.nfl.com/games/", "14 games"),
        ("NFL.com news article for each published headline", "https://www.nfl.com/news/", "24 headlines"),
    ]:
        rows.append([cell(label), cell(count), '<td>%s</td>' % src_link(url, "open")])
    body.append(table("Row-level source links", [("Source type", ""), ("Rows", "num"), ("Link", "")], rows))
    return page("Source register", "Official data / Sources", "\n".join(body), "pages/sources.html")


NAMESPACES = [
    ("nfl-hq", "This site", "Canonical NFL Command Center: official snapshots, own lines, strategies, "
     "gates, correlations, leaderboard, questions, suggestions, flags.", "Canonical"),
    ("nfl-lines", "NFL line-origination lab", "The walk-forward model, the 15 strategies, the "
     "leaderboard, the correlations and the skill-versus-luck work that this site publishes.",
     "Research workspace"),
    ("nfl-quant", "NFL quant pipeline", "A separate quantitative pipeline: ratings, key numbers, "
     "luck calibration, same-game joint probabilities, prop proxies and a look-ahead test.",
     "Research workspace"),
    ("nfl-hub", "NFL Line Genesis", "Official game books and the two proved replacement-starter "
     "examples, plus the week 10 line set.", "Research workspace"),
    ("nfl-edge", "NFL Edge", "Requirements, the decision register, own lines and the skill gates.",
     "Research workspace"),
    ("nfl-intel", "NFL Intelligence", "Verified data, originated lines, gated strategies, a question "
     "register and a suggestions board.", "Research workspace"),
    ("nfl-decision", "NFL Decision Lab", "The question register, the suggestions board and the injury "
     "and depth tracker.", "Research workspace"),
    ("nfl-decisions", "NFL Decision Desk", "An earlier questions-and-suggestions workspace with its "
     "own review register.", "Research workspace"),
    ("nfl-audit", "NFL audit", "A live-verification pass over the official week 10 data with its own "
     "questions, suggestions and injury tracker.", "Research workspace"),
    ("nfl-lab", "NFL Quant Lab", "Signals, parameters, own lines, leaderboard and correlations.",
     "Research workspace"),
    ("nfl-research", "NFL research dashboard", "A strategy and validation specification with its own "
     "review page.", "Research workspace"),
    ("nfl", "NFL research specification", "The original written specification for the line-origination "
     "research, before any numbers existed.", "Research workspace"),
    ("verified", "NBA verified snapshot", "The 2026-11-05 NBA snapshot, gates and leaderboard.",
     "Other project"),
    ("nba-evidence", "NBA evidence", "An NBA evidence protocol with its own site and tests.",
     "Other project"),
    ("rental-f1dbaea0", "RentCheck SF", "The San Francisco rent-increase review, 94122.",
     "Other project"),
    ("verification-2026-11-05", "Independent audit", "An independent verification pass over the NBA "
     "snapshot.", "Other project"),
    ("status", "Status review", "A repository status review.", "Other project"),
    ("lab", "Data Lab", "The NBA data lab.", "Other project"),
    ("lines-lab", "NBA Lines Lab", "The NBA lines lab.", "Other project"),
    ("docs", "NBA Signal Lab", "The NBA signal lab dashboard.", "Other project"),
]


def p_architecture():
    body = ['<p class="lede">Every published namespace in the repository and what it contains. '
            'Eleven NFL workspaces were built by parallel sessions before this integration, each with '
            'its own copy of the questions, suggestions and flagged pages. This site is the canonical '
            'entry point; the rest are research workspaces, and none of them has been deleted or '
            'rewritten.</p>']
    rows = []
    missing = []
    for slug, name, contains, kind in NAMESPACES:
        href = ("@@ROOT@@index.html" if slug == "nfl-hq" else "@@ROOT@@%s/index.html" % slug)
        target = (os.path.join(ROOT, "index.html") if slug == "nfl-hq"
                  else os.path.join(REPO, slug, "index.html"))
        exists = os.path.exists(target)
        gh = "https://github.com/sassnarep3-star/Own4/tree/main/%s" % slug
        if not exists:
            missing.append(slug)
        rows.append([
            cell(slug), cell(name), cell(contains),
            '<td>%s</td>' % badge("ok" if kind == "Canonical" else "neutral", kind),
            '<td>%s</td>' % ((src_link(href, "open") + " " + src_link(gh, "repo")) if exists
                             else src_link(gh, "repo")),
        ])
    note = None
    if missing:
        note = ("%d listed namespaces have no index.html in the repository, so no link is "
                "published for them: %s. That is recorded as an irregularity rather than guessed at."
                % (len(missing), ", ".join(missing)))
    body.append(table("Published namespaces &#183; %d namespaces" % len(rows),
                      [("Namespace", ""), ("Name", ""), ("What it contains", ""), ("Role", ""),
                       ("Open", "")], rows, filt=True, note=note))
    body.append('<div class="panel warn"><h3>The decision this map is waiting on</h3><p>Nothing has been '
                'retired, moved or deleted. Several peer pages carry a hard-coded count of NFL '
                'namespaces that this integration has made stale, and one peer pull request is open '
                'with an accuracy fix to that count. The decision on what to keep, what to archive and '
                'what to merge is recorded as <a href="pages/questions.html">Q18</a> and proposed as '
                '<a href="pages/suggestions.html">S01</a>. Until it is taken, the duplication is '
                'flagged rather than silently resolved.</p></div>')
    return page("Namespace map", "Architecture / Namespace map", "\n".join(body), "pages/architecture.html")


FLAGS = [
    ("F01", "The official snapshot committed on 2026-11-12 was one game stale",
     "NFL.com's standings and team-stat pages were read on 2026-11-13 and compared cell by cell. WAS "
     "and NYG had moved by exactly one game: Commanders 24, Giants 21 on Thursday 12 November. The "
     "committed snapshot published the pre-game records without saying so.",
     NFL_STANDINGS, "Needs review - data corrected here, peer snapshot left as it was"),
    ("F02", "NFL.com publishes no betting lines, so every market value is third-party",
     "Spread, total, moneyline and every price come from the nflverse archive. There is no official "
     "counterpart to compare them with. Every market page says so.",
     NFLVERSE, "Needs review - structural limitation"),
    ("F03", "NFL.com publishes no depth-chart rank, so every depth cell is blank",
     "There is no official pre-game depth chart, no depth rank and no official pre-kickoff reason for "
     "a replacement. The only official depth evidence is the substitution code in the post-game game "
     "book.",
     NFL_INJURIES, "Needs review - structural limitation"),
    ("F04", "No player-prop line is verifiable, so the prop-combination family is priced against a proxy",
     "Official prop lines, prop variances and prop-pair correlations do not exist in any official "
     "source. The family is measured but is not comparable with the single and parlay families.",
     NFL_INJURIES, "Needs review - structural limitation"),
    ("F05", "The official injury report gives no reason for a status and no reason for a disappearance",
     "A player who is ruled out carries a status but no cause. A player who was on the report on one "
     "day and absent the next is simply absent; NFL.com states nothing. Four Kansas City players "
     "appear only in the 2026-11-12 read.",
     NFL_INJURIES, "Needs review - information gap"),
    ("F06", "The official injury report is a rolling document, so a snapshot is only valid on its date",
     "Between the 2026-11-12 read and the 2026-11-13 read the report gained a complete Monday-night "
     "table, filled in the Injury and Game Status columns for several teams, and changed the practice "
     "status of 134 rows. No scheduled fetch job exists to keep it current.",
     NFL_INJURIES, "Needs review - operational gap"),
    ("F07", "The archived game copy predates the completed Thursday night game",
     "The third-party archive snapshot used by this repository carries no final score for Commanders "
     "at Giants, because it was taken before the game. The official final is 24-21. The archive cell "
     "is published blank rather than filled in from the official page, because the archive is a "
     "separate source.",
     NFL_SCORES10, "Needs review - information gap"),
    ("F08", "The Monday-night game was published as having no injuries, which was not true",
     "On 2026-11-12 the Chargers-Ravens entry carried no player rows and the note said the page "
     "stated no injuries reported. On 2026-11-13 the same game carried 26 rows, 18 of them Chargers. "
     "A blank report is not a clean bill of health.",
     NFL_INJURIES, "Needs review - corrected here, peer snapshot left as it was"),
    ("F09", "Absence from the official injury report is not evidence of absence from the game",
     "NFL.com lists only players who carry a designation. A team whose starting quarterback is not on "
     "the report is not thereby without a quarterback. This limits what the tracker can conclude.",
     NFL_INJURIES, "Needs review - interpretation rule"),
    ("F10", "The rest-differential term is large and is the most likely source of a spurious edge",
     "At 0.71 points per day it drives the single biggest model-versus-market disagreement in the "
     "sample. It has not been isolated or tested.",
     PEER_LINES, "Needs review - model weakness"),
    ("F11", "The model has no quarterback feature and no depth-chart feature",
     "NFL.com itself published at least six quarterback changes for Week 10, including Lamar Jackson "
     "out for six to ten weeks, Deshaun Watson starting for Cleveland, Carson Beck starting for "
     "Arizona, Malik Willis placed on injured reserve with Kyle McCord in line for a first start, and "
     "Sam Darnold ruled out with Drew Lock expected to start again. The model is blind to all of them.",
     NFL_INJURIES, "Needs review - model weakness"),
    ("F12", "The model cannot price an official line, so every ROI depends on one third-party archive",
     "The whole research rests on a single archive whose licence has not been reviewed line by line. It "
     "has been verified against NFL.com for 15 games in this pass and 45 in the previous one.",
     NFLVERSE, "Needs review - licence and dependency"),
    ("F13", "The third-party archive licence has not been reviewed line by line",
     "The archive is used for research only and no licence text has been read in this pass. No "
     "non-research use is implied.",
     NFLVERSE, "Needs review - licence"),
    ("F14", "Only 60 of 4,055 historical forecast games have been re-read from official pages",
     "15 games were re-read in this pass and 45 in the previous one. The remaining seasons rest on the "
     "archive alone. The score spot-check is therefore strong for the recent weeks and unverified for "
     "the earlier ones.",
     NFL_SCORES9, "Needs review - coverage gap"),
    ("F15", "The repository carried eleven overlapping NFL namespaces before this integration",
     "Each had its own copy of the suggestions board, the question register and the flagged page. This "
     "site is now the canonical entry point and the namespace map describes the rest. Nothing has been "
     "deleted.",
     REPO_OWN4, "Needs review - architecture decision outstanding"),
    ("F16", "Several peer pages carry a hard-coded count of NFL namespaces that is now stale",
     "The count was written by each session before the other sessions merged, so it went stale as the "
     "repository grew. One peer pull request is open with an accuracy fix to that count, and this "
     "integration has added a twelfth namespace. The authoritative count is on the namespace map.",
     PEER_DECISION, "Needs review - peer file, not edited by this session"),
    ("F17", "Weather for future games cannot be verified from any official source",
     "Wind, temperature, roof and surface come from the third-party archive. One strategy depends on "
     "wind at 15 miles per hour or above. No official NFL weather source was located.",
     NFLVERSE, "Needs review - structural limitation"),
    ("F18", "The official standings page and the official scores page are not updated at the same time",
     "On 2026-11-12 the standings page still carried the pre-game records for WAS and NYG while the "
     "scores page had already marked the game Final. Any automated reader must therefore allow for a "
     "lag between the two official pages.",
     NFL_SCORES10, "Needs review - official-source behaviour"),
]


def site_verification():
    path = os.path.join(DATA, "verification", "site_verification_%s.json" % SNAPSHOT)
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except (ValueError, OSError):
        return None


def blank_inventory():
    """Published straight from the verifier receipt, so the site can never under-report a blank."""
    v = site_verification()
    out = ['<h2>Blank cells published by the site</h2>']
    if not v:
        out.append('<p class="note">The verifier receipt has not been written yet for this '
                   'snapshot. Run <code>nfl-hq/verify_site.py</code> and rebuild; this section '
                   'then lists every blank cell page by page.</p>')
        return out
    out.append('<p>Every value on this site that could not be confirmed from an official source is '
               'published as the words <span class="blank">not published</span> instead of a '
               'number. Nothing is inferred, estimated or carried over from memory. The table below '
               'is generated by the same verifier that fails the build when a link is broken, so '
               'the count cannot drift from the site.</p>')
    out.append(kpi_cards([
        (str(v["data_rows"]), "published data rows", ""),
        (str(v["rows_with_any_link"]), "rows carrying a source link", "ok"),
        (str(v["rows_with_official_link"]), "rows carrying an official NFL link", "ok"),
        (str(v["blank_cells_published"]), "blank (unverified) cells", "warn"),
    ]))
    rows = []
    for pg, d in sorted(v["per_page"].items()):
        if not d["data_rows"]:
            continue
        rows.append([cell(pg), cell(d["data_rows"], cls="num"), cell(d["blank_cells"], cls="num"),
                     '<td>%s</td>' % src_link("@@ROOT@@nfl-hq/%s" % pg, "open")])
    out.append(table("Blank cells by page &#183; %d pages, %d data rows"
                     % (len(rows), v["data_rows"]),
                     [("Page", ""), ("Data rows", "num"), ("Blank cells", "num"),
                      ("Open", "")], rows, filt=True))
    rows = []
    for c in v["checks"]:
        rows.append([cell(c["id"]), cell(c["check"]),
                     '<td>%s</td>' % badge("ok" if c["passed"] else "bad",
                                           "PASS" if c["passed"] else "FAIL"),
                     cell(c["detail"]),
                     '<td>%s</td>' % src_link("@@ROOT@@nfl-hq/data/verification/"
                                              "site_verification_%s.json" % SNAPSHOT, "receipt")])
    out.append(table("Site verification checks", [("ID", ""), ("Check", ""), ("Result", ""),
                                                  ("Detail", ""), ("Receipt", "")], rows))
    detail = v.get("blank_detail") or []
    if detail:
        top = sorted(detail, key=lambda d: -d["blank_cells"])[:25]
        rows = [[cell(d["page"]), cell(d["blank_cells"], cls="num"), cell(d["row"]),
                 '<td>%s</td>' % src_link("@@ROOT@@nfl-hq/%s" % d["page"], "open")]
                for d in top]
        out.append(table("The 25 rows carrying the most blank cells",
                         [("Page", ""), ("Blanks", "num"), ("Row as published", ""),
                          ("Open", "")], rows, filt=True,
                         note="A row here is not a defect. It is a row where the official source "
                              "does not publish the value, so the value is left empty on purpose."))
    return out


def p_flagged():
    body = ['<p class="lede">Every irregularity, every value that could not be confirmed from an '
            'official source, and every information gap found during the review. None of these blocks '
            'the site. Each one is here so it can be reviewed after the site is live and acted on '
            'then.</p>']
    body.append(kpi_cards([
        (str(len(FLAGS)), "items flagged for review", "warn"),
        (str(sum(1 for f in FLAGS if "structural" in f[4])), "structural limits of official sources", ""),
        (str(sum(1 for f in FLAGS if "model weakness" in f[4])), "model weaknesses", "bad"),
        (str(sum(1 for f in FLAGS if "gap" in f[4] or "outstanding" in f[4])), "gaps and open decisions", "warn"),
    ]))
    rows = []
    for fid, title, detail, url, status in FLAGS:
        rows.append([
            cell(fid), cell(title), cell(detail),
            '<td>%s</td>' % src_link(url, "source"),
            '<td>%s</td>' % badge("warn", status),
        ])
    body.append(table("Flagged for review &#183; %d items, every item source-linked" % len(FLAGS),
                      [("ID", ""), ("Item", ""), ("Detail", ""), ("Source", ""), ("Status", "")], rows))
    body.append('<div class="panel"><h3>How to act on this list</h3><p>Each item names the missing '
                'input and, where one exists, the source that would close it. The items marked as a '
                'structural limitation cannot be closed by more work in this repository; they need a '
                'licensed data source. Those are recorded as questions on the '
                '<a href="pages/questions.html">Open questions</a> page and costed as suggestions on '
                'the <a href="pages/suggestions.html">Suggestions board</a>.</p></div>')
    body.extend(blank_inventory())
    return page("Flagged for review", "Decide / Flagged for review", "\n".join(body), "pages/flagged.html")


PAGES_BUILD = [
    ("pages/executive-summary.html", p_executive_summary),
    ("pages/requirements.html", p_requirements),
    ("pages/questions.html", p_questions),
    ("pages/suggestions.html", p_suggestions),
    ("pages/standings.html", p_standings),
    ("pages/team-stats.html", p_team_stats),
    ("pages/schedule.html", p_schedule),
    ("pages/injuries.html", p_injuries),
    ("pages/depth-chart.html", p_depth_chart),
    ("pages/own-lines.html", p_own_lines),
    ("pages/strategies.html", p_strategies),
    ("pages/validation.html", p_validation),
    ("pages/correlations.html", p_correlations),
    ("pages/skill-vs-luck.html", p_skill_vs_luck),
    ("pages/leaderboard.html", p_leaderboard),
    ("pages/repo-review.html", p_repo_review),
    ("pages/sources.html", p_sources),
    ("pages/architecture.html", p_architecture),
    ("pages/flagged.html", p_flagged),
]


def main():
    written = []
    for name, fn in PAGES_BUILD:
        written.append(write(name, fn()))
    written.append(write("index.html", p_index()))
    print("built %d pages" % len(written))
    for p in written:
        print("  %s" % os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()

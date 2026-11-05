#!/usr/bin/env python3
"""
Own4 — canonical dashboard builder (2026-11-05 verified snapshot).

Writes the root landing page (index.html) and the category subpages under
verified/. Pure standard library; no template engine, no JavaScript dependency,
no external assets. Every data table row carries at least one source link.

Run:  python3 verification/collect_2026-11-05.py
      python3 verification/reconcile.py
      python3 verification/analysis.py
      python3 verification/build.py
      python3 verification/verify_site.py
"""

import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
SNAPSHOT = "2026-11-05"

AN = json.load(open(os.path.join(OUT, "analysis.json")))
REC = json.load(open(os.path.join(OUT, "reconciliation.json")))
SRC = {s["id"]: s for s in json.load(open(os.path.join(DATA, "sources.json")))["sources"]}
FLAGS = json.load(open(os.path.join(DATA, "flags.json")))["flags"]
STAND = json.load(open(os.path.join(DATA, "standings.json")))["rows"]
TSTATS = json.load(open(os.path.join(DATA, "team_stats.json")))["rows"]
FRESH = json.load(open(os.path.join(DATA, "games_fresh.json")))["rows"]
SLATE = json.load(open(os.path.join(DATA, "slate.json")))["rows"]
LEAD = json.load(open(os.path.join(DATA, "season_leaders.json")))["rows"]
CAL = json.load(open(os.path.join(DATA, "calendar.json")))["days"]
OLDG = json.load(open(os.path.join(ROOT, "official", "games.json")))["rows"]
GATES = json.load(open(os.path.join(DATA, "gates.json")))

M = AN["metrics"]
TEAM = {r["abbr"]: r["team"] for r in TSTATS}


# ---------------------------------------------------------------- helpers
def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def num(x, nd=1, sign=False):
    if x is None or x == "":
        return '<span class="blank">blank — unverified</span>'
    f = ("%+." if sign else "%.") + str(nd) + "f"
    return esc(f % x)


def pct(x, nd=1):
    if x is None:
        return '<span class="blank">blank — unverified</span>'
    return esc(("%." + str(nd) + "f%%") % (100.0 * x))


def pval(p):
    if p is None:
        return '<span class="blank">blank — unverified</span>'
    if p < 0.0001:
        return "&lt;0.0001"
    return esc("%.4f" % p)


def ext(url, label):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label))


def src(sid, label=None):
    s = SRC[sid]
    return ext(s["url"], label or ("%s ↗" % sid))


def repo(path, label="Repo ↗"):
    return ext(REPO + path, label)


def badge(text, kind="neutral"):
    return '<span class="badge %s">%s</span>' % (kind, esc(text))


def table(headers, rows, caption="", numeric=(), cls="", note=""):
    cap = '<caption>%s</caption>' % caption if caption else ""
    th = "".join('<th scope="col"%s>%s</th>' % (' class="num"' if i in numeric else "", esc(h))
                 for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join('<td%s>%s</td>' % (' class="num"' if i in numeric else "", c) for i, c in enumerate(r))
        body.append("<tr>%s</tr>" % tds)
    out = ('<div class="tw"><table%s>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
           % (' class="%s"' % cls if cls else "", cap, th, "".join(body)))
    if note:
        out += '<p class="note">%s</p>' % note
    return out


NAV = [
    ("Overview", [
        ("index.html", "Dashboard", "dash"),
        ("verified/executive-summary.html", "Executive summary", "summary"),
    ]),
    ("Official data · 2026-11-05", [
        ("verified/standings.html", "Standings", "stand"),
        ("verified/team-stats.html", "Team stats", "stats"),
        ("verified/games.html", "Games &amp; scores", "games"),
    ]),
    ("Originated lines", [
        ("verified/own-lines.html", "Singles", "lines"),
        ("verified/own-lines.html#parlays", "Parlays &amp; dependence", "lines"),
        ("verified/own-lines.html#props", "Player props", "lines"),
    ]),
    ("Strategy research", [
        ("verified/strategies.html", "Strategy catalog", "strat"),
        ("verified/validation.html", "Validation gates", "gates"),
        ("verified/correlations.html", "Correlations", "corr"),
        ("verified/backtest.html", "Backtest &amp; luck", "back"),
    ]),
    ("Competition", [
        ("verified/leaderboard.html", "Leaderboard &amp; rewards", "board"),
    ]),
    ("Governance", [
        ("verified/sources.html", "Source register", "sources"),
        ("verified/audit.html", "Repo audit", "audit"),
        ("verified/flagged.html", "⚑ Flagged for review", "flags"),
    ]),
    ("Retained workspaces", [
        ("pages/legacy-root-dashboard.html", "Previous root dashboard", "legacy"),
        ("docs/index.html", "NBA Signal Lab", "legacy"),
        ("lab/index.html", "Data Lab", "legacy"),
        ("lines-lab/index.html", "NBA Lines Lab", "legacy"),
        ("nba-evidence/site/index.html", "NBA Evidence", "legacy"),
    ]),
]

FOOTER = """<footer>
<p><strong>Own4</strong> — NBA line-origination research. Analytical research only, not wagering advice.
Snapshot <strong>%(snap)s</strong>; every data row links to the official page it was read from, and every value that
could not be confirmed from an official source is blank and listed on the
<a href="%(p)sverified/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>"""


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
<title>%(title)s · Own4</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(prefix)sassets/canonical.css">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(prefix)sindex.html">Own4 <span>NBA line origination</span></a>
  <div class="tag">Verified snapshot %(snap)s · official sources only</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <a class="flag" href="%(prefix)sverified/flagged.html">⚑ %(nflags)d items flagged for review</a>
</aside>
<main class="main" id="main">
<div class="crumb">%(crumb)s</div>
%(body)s
%(footer)s
</main>
</div>
<script src="%(prefix)sassets/canonical.js" defer></script>
</body>
</html>
""" % {
        "title": esc(title), "desc": esc(desc), "prefix": prefix, "snap": SNAPSHOT,
        "nav": "".join(nav), "crumb": crumb, "body": body, "nflags": len(FLAGS),
        "footer": FOOTER % {"snap": SNAPSHOT, "p": prefix},
    }
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(doc)
    return path


# ---------------------------------------------------------------- pages
def build_index():
    g = AN["gates"]
    n_pass = sum(1 for x in g if x["status"] == "PASS")
    n_fail = sum(1 for x in g if x["status"] == "FAIL")
    n_block = sum(1 for x in g if x["status"] == "BLOCKED")
    cards = [
        ("85", "official game rows in the verified sample", ""),
        ("30", "standings rows, re-read 2026-11-05", ""),
        ("30", "team-stat rows, re-read 2026-11-05", ""),
        ("10", "team correlations measured (r, CI, FDR)", "brand"),
        ("%d" % len(AN["own_lines"]), "matches with originated fair lines", "brand"),
        ("%d/%d/%d" % (n_pass, n_fail, n_block), "gates pass / fail / blocked", "warn"),
        ("%d" % len(AN["strategies"]), "strategies in the catalog", ""),
        ("0", "strategies that qualify", "bad"),
        ("0", "rewards awarded", "bad"),
        ("%d" % len(FLAGS), "items flagged for review", "warn"),
    ]
    cardhtml = "".join('<div class="card %s"><b>%s</b><span>%s</span></div>' % (c[2], c[0], c[1]) for c in cards)

    findings = [
        ("F01", "The stored snapshot was 2026-11-02 and the league has since played 36 more games. This site publishes a fresh 2026-11-05 snapshot instead of republishing stale values.",
         badge("fresh — read 2026-11-05", "official"), [src("S1"), src("S2")]),
        ("F02", "All 30 teams' W-L advance exactly by their results in the re-read games: inherited snapshot + 29 freshly verified finals = live records, 30 of 30 teams.",
         badge("verified — 30/30", "official"), [repo("verification/out/reconciliation.json", "Check C05 ↗")]),
        ("F03", "Two independently rendered official pages (standings and teams-traditional) agree on W-L for all 30 teams, and league wins equal league losses (121 = 121).",
         badge("verified — cross-page", "official"), [src("S1"), src("S2")]),
        ("F04", "The verified sample holds 85 of the 121 games played (70.2%). Seven October dates, 36 games, are not in the sample and no number here uses them.",
         badge("derived — coverage audit", "derived"), [src("S6"), src("S7")]),
        ("F05", "Own4 originated fair totals and spreads for the two 11/05 games from official final scores only. Every price field is blank: no official NBA source publishes a price.",
         badge("derived — originated", "derived"), [src("S5")]),
        ("F06", "Ten team-level correlations were measured with 95% confidence intervals and Benjamini-Hochberg control; five survive (point differential, points, FG%, 3P%, turnovers).",
         badge("derived — measured", "derived"), [src("S2"), src("S1")]),
        ("F07", "Walk-forward backtest: winner accuracy 0.5714 on 35 graded games versus a 0.6000 home-team baseline (one-sided p = 0.7003). The model does not beat home advantage.",
         badge("derived — backtest", "derived"), [repo("verification/out/analysis.json", "Analysis ↗")]),
        ("F08", "The originated total beat the naive baseline by 0.74 points of MAE (permutation p = 0.0261), but fails the 300-game floor and fails Benjamini-Hochberg at q = 0.05 once both strategy tests are counted.",
         badge("derived — not an edge", "derived"), [repo("verification/out/analysis.json", "Analysis ↗")]),
        ("F09", "No strategy passes all ten gates. The leaderboard is published with zero qualifiers and zero rewards, because paying a strategy that has not cleared its sample would be paying for luck.",
         badge("derived — gate result", "derived"), [repo("verification/data/gates.json", "Gates ↗")]),
        ("F10", "Player-prop combinations are blocked at the data layer: official season averages exist, official per-game logs do not, so no prop variance or prop-pair correlation is published.",
         badge("blocked — data", "blocked"), [src("S5")]),
    ]
    frows = [(a, b, c, d) for a, b, c, d in findings]

    tiles = [
        ("verified/standings.html", "Official data", "30 standings rows and 30 team-stat rows, each with the exact nba.com URL and the official team link.", "Read the data"),
        ("verified/own-lines.html", "Originated lines", "Fair totals, spreads and win probabilities for the 11/05 slate; single bets, parlay dependence and player props.", "Open the lines"),
        ("verified/strategies.html", "Strategy research", "Eight strategies across singles, parlays and prop combos, with the gates each one must clear.", "See the catalog"),
        ("verified/validation.html", "Validation gates", "The ten pre-registered gates, evaluated against measured numbers, with the rule text that defines each one.", "Check the gates"),
        ("verified/correlations.html", "Correlations", "Measured correlation values with confidence intervals and FDR control, including same-game dependence for parlays.", "Read the numbers"),
        ("verified/backtest.html", "Backtest &amp; luck removal", "Walk-forward grading, bootstrap and permutation tests, power analysis, and the full graded game list.", "Audit the backtest"),
        ("verified/leaderboard.html", "Leaderboard &amp; rewards", "How the competition scores strategies, why nobody qualified, and what would have to change for a reward.", "See the board"),
        ("verified/flagged.html", "⚑ Flagged for review", "Every irregularity and every value that could not be confirmed from an official source, with links.", "Review the flags"),
    ]
    tilehtml = "".join('<a class="tile" href="%s"><b>%s</b><span>%s</span><em>%s →</em></a>' % t for t in tiles)

    gatestat = table(
        ["Gate", "Name", "Status", "Evidence from this run", "Definition"],
        [(x["id"], esc(x["name"]), badge(x["status"].lower(), {"PASS": "pass", "FAIL": "fail", "BLOCKED": "blocked"}[x["status"]]),
          esc(x["evidence"]), repo("verification/data/gates.json", "Rule ↗")) for x in g],
        caption="Gate status summary · full text on the Validation gates page",
        numeric=(),
    )

    body = """
<h1>NBA line origination — verified research dashboard</h1>
<p class="lede">Collect official NBA data, originate our own lines, develop signals that survive pre-registered
gates, remove luck from the comparison, and rank only strategies that are selectively skill based.
Snapshot <strong>%(snap)s</strong>: everything below was re-read from nba.com on that date, and nothing is inferred.</p>

<div class="panel warn"><strong>Headline result — no edge is claimed.</strong> On the verified sample the originated
winner picks do not beat the free home-team baseline (0.5714 vs 0.6000, one-sided p = 0.7003), the one nominal
totals result does not survive multiple-testing control, and no strategy clears the ten gates. The competition
therefore awards nothing. The value of this release is the verified data, the measurement machinery and the
honest scoreboard, not a pick.</div>

<div class="cards">%(cards)s</div>

<h2>Start here</h2>
<div class="tiles">%(tiles)s</div>

<h2>Executive findings</h2>
<p>Each row is a claim made by this release. The badge says what kind of value it is: <strong>fresh</strong> values
were read from an official page on %(snap)s, <strong>derived</strong> values are reproducible computations from
those inputs, <strong>blocked</strong> means the required official input does not exist.</p>
%(findings)s

<h2>Gate scoreboard</h2>
%(gatestat)s

<h2>What is verified, and what is not</h2>
<div class="panel ok"><h3>Verified</h3><p>30 standings rows, 30 team-stat rows and 2 scheduled games re-read from
nba.com on %(snap)s; 29 final scores re-read from the official games pages; 56 inherited final scores corroborated
date-by-date and league-wide; all 13 reconciliation checks pass or are explicitly noted.</p></div>
<div class="panel bad"><h3>Not verified — published as blank or blocked</h3><p>Betting prices (no official source),
player per-game logs (not available under the official-source rule), player availability, prop variances and
prop-pair correlations, and the 36 games on the seven October dates that were never captured. These are listed on
the <a href="verified/flagged.html">Flagged for review</a> page rather than filled in.</p></div>

<h2>How to reproduce every number on this site</h2>
<div class="panel"><p class="small"><code>python3 verification/collect_2026-11-05.py</code> writes the transcription ·
<code>python3 verification/reconcile.py</code> runs the 13 audit checks ·
<code>python3 verification/analysis.py</code> rebuilds the model, gates and correlations ·
<code>python3 verification/build.py</code> rebuilds this site ·
<code>python3 verification/verify_site.py</code> checks every local link and every table row's source link.</p>
<p class="small">Sources: %(s1)s standings · %(s2)s team stats · %(s3)s 11/02 finals · %(s4)s 11/04 finals ·
%(s5)s 11/05 slate and season leaders. Usage restriction: %(s9)s.</p></div>
""" % {
        "snap": SNAPSHOT, "cards": cardhtml, "tiles": tilehtml,
        "findings": table(["ID", "Finding", "Value type", "Source"],
                          frows, caption="Executive findings · %d rows, every row source-linked" % len(frows)),
        "gatestat": gatestat,
        "s1": src("S1", "nba.com/standings ↗"), "s2": src("S2", "nba.com/stats/teams/traditional ↗"),
        "s3": src("S3", "nba.com/games 11/02 ↗"), "s4": src("S4", "nba.com/games 11/04 ↗"),
        "s5": src("S5", "nba.com/games 11/05 ↗"), "s9": src("S9", "NBA Stats FAQ ↗"),
    }
    return page("index.html", "Dashboard", "Overview / Dashboard", body, "dash",
                "Own4 — verified NBA line-origination research dashboard, snapshot 2026-11-05.")


def build_standings():
    rows = []
    for r in STAND:
        rows.append((
            esc(r["conference"]), esc(str(r["rank"])), "<strong>%s</strong> %s" % (esc(r["abbr"]), esc(r["team"])),
            esc(str(r["W"])), esc(str(r["L"])), esc(r["win_pct"]), esc(r["GB"]),
            esc(r["CONF"]), esc(r["DIV"]), esc(r["HOME"]), esc(r["ROAD"]), esc(r["OT"]),
            esc(r["LAST10"]), esc(r["STREAK"]),
            src("S1", "Standings ↗") + " " + ext(r["team_url"], "Team ↗"),
        ))
    body = """
<h1>Official standings · 2026-27</h1>
<p class="lede">All 30 teams, transcribed line by line from the official standings table on %(snap)s. Values are
shown exactly as displayed; the two right-hand links are the standings page itself and that team's official page.</p>
<div class="panel">Read from %(s1)s. Every one of the 30 rows was cross-checked against the independently rendered
teams-traditional table on %(s2)s, and the two agree on W-L for all 30 teams (audit check C01). League wins equal
league losses: 121 = 121.</div>
%(t)s
<p class="note">Note on <strong>GB</strong>: the official table prints "--" for the Lakers and Rockets although
Portland leads the West on win percentage, because games-behind is computed from wins and losses, not from win
percentage. That is the displayed value and it is not adjusted here.</p>
""" % {"snap": SNAPSHOT, "s1": src("S1", "nba.com/standings ↗"), "s2": src("S2", "teams-traditional ↗"),
       "t": table(["Conf", "Rank", "Team", "W", "L", "WIN%", "GB", "CONF", "DIV", "HOME", "ROAD", "OT",
                   "LAST10", "STREAK", "Official source"],
                  rows, caption="2026-27 regular-season standings · %d rows · read %s" % (len(rows), SNAPSHOT),
                  numeric=(1, 3, 4, 5, 6))}
    return page("verified/standings.html", "Standings", "Official data / Standings", body, "stand",
                "NBA 2026-27 standings transcribed from nba.com on 2026-11-05.")


def build_stats():
    rows = []
    for r in sorted(TSTATS, key=lambda x: (-x["W"], x["L"])):
        rows.append((
            "<strong>%s</strong> %s" % (esc(r["abbr"]), esc(r["team"])),
            esc(str(r["GP"])), esc(str(r["W"])), esc(str(r["L"])),
            num(r["PTS"]), num(r["FG_pct"]), num(r["3P_pct"]), num(r["FT_pct"]),
            num(r["REB"]), num(r["AST"]), num(r["TOV"]), num(r["STL"]), num(r["BLK"]),
            num(r["plus_minus"], 1, sign=True),
            src("S2", "Team table ↗") + " " + ext(r["team_stats_url"], "Team ↗"),
        ))
    body = """
<h1>Official team statistics · 2026-27 (per game)</h1>
<p class="lede">All 30 rows of the official <em>Teams — Traditional</em> table in its default per-game mode,
transcribed on %(snap)s. Column definitions come from the official stats glossary.</p>
<div class="panel warn"><h3>One published column is flagged, not fixed</h3><p>The 30 published <code>+/-</code> values
sum to <strong>%(pm)+.1f</strong>. Every game awards the same points to both teams, so that sum must be exactly zero;
mean points scored is %(mean_pts).2f against %(mean_allowed).2f implied points allowed. The gap is larger than one-decimal rounding can
explain, so the column is published exactly as displayed and is <strong>not used as an input</strong> to any model
on this site (flag F-PLUSMINUS).</p></div>
%(t)s
<p class="note">Read from %(s2)s; definitions at %(gloss)s. W-L in this table agrees with the standings page for all
30 teams.</p>
""" % {"snap": SNAPSHOT, "t": table(
        ["Team", "GP", "W", "L", "PTS", "FG%", "3P%", "FT%", "REB", "AST", "TOV", "STL", "BLK", "+/-", "Official source"],
        rows, caption="Official team table, per game · %d rows · read %s" % (len(rows), SNAPSHOT),
        numeric=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)),
        "s2": src("S2", "nba.com/stats/teams/traditional ↗"),
        "gloss": src("S8", "glossary ↗"),
        "pm": sum(r["plus_minus"] for r in TSTATS),
        "mean_pts": sum(r["PTS"] for r in TSTATS) / 30.0,
        "mean_allowed": sum(r["PTS"] - r["plus_minus"] for r in TSTATS) / 30.0}
    return page("verified/team-stats.html", "Team stats", "Official data / Team stats", body, "stats",
                "NBA 2026-27 team statistics transcribed from nba.com on 2026-11-05.")


def build_games():
    rows = []
    for r in OLDG:
        rows.append(("2026-10-21" if False else r["date"], r["game_id"],
                     "%s @ %s" % (esc(r["team_a"]), esc(r["team_b"])),
                     "%d–%d" % (r["team_a_pts"], r["team_b_pts"]), esc(str(r["total_pts"])),
                     ("%+d" % r["margin_a"]), badge("inherited · corroborated", "neutral"),
                     ext(r["source_url"], "Date page ↗") + " " + ext(r["game_url"], "Game ↗")))
    for r in FRESH:
        rows.append((r["date"], r["game_id"], "%s @ %s" % (esc(r["away"]), esc(r["home"])),
                     "%d–%d" % (r["away_pts"], r["home_pts"]), esc(str(r["total"])),
                     ("%+d" % r["margin_home"]) + (" (OT)" if r["ot"] else ""),
                     badge("re-read 2026-11-05", "official"),
                     ext(r["source_url"], "Date page ↗") + " " + ext(r["game_url"], "Game ↗")))
    rows.sort(key=lambda x: (x[0], x[1]))

    counts = {}
    for r in OLDG:
        counts[r["date"]] = counts.get(r["date"], 0) + 1
    for r in FRESH:
        counts[r["date"]] = counts.get(r["date"], 0) + 1
    cov = []
    for d in sorted(CAL):
        official = CAL[d]
        got = counts.get(d, 0)
        if official == 0:
            state = badge("no games scheduled", "neutral")
        elif got == official:
            state = badge("complete", "pass")
        elif got == 0:
            state = badge("not captured", "fail")
        else:
            state = badge("partial", "warn")
        cov.append((d, esc(str(official)), esc(str(got)),
                    "%d" % (official - got), state, src("S6", "Calendar ↗")))
    missing = sum(CAL[d] for d in CAL if d < SNAPSHOT and counts.get(d, 0) == 0)

    body = """
<h1>Official games &amp; scores</h1>
<p class="lede">Every final score this research uses, with its date page and its official game link. Two provenance
labels appear: rows <strong>re-read on 2026-11-05</strong> were fetched in this session; rows labelled
<strong>inherited</strong> were already in the repository from 2026-11-02 and are corroborated, not re-fetched.</p>
<div class="panel"><p><strong>%(n)d games in the verified sample</strong> against <strong>121 games played</strong>
league-wide as of the snapshot (%(pct).1f%% coverage). %(missing)d games on seven October dates were never
captured; they appear in no table and in no calculation. The per-date audit below shows exactly where the holes
are. Official calendar counts come from %(cal)s.</p></div>
%(cov)s
%(t)s
""" % {"n": len(rows), "pct": REC["summary"]["coverage_pct"], "missing": missing,
       "cal": src("S6", "nba.com/games (October calendar) ↗"),
       "cov": table(["Date", "Games on official calendar", "Games in sample", "Missing", "State", "Source"],
                    cov, caption="Coverage audit by date · %d dates" % len(cov), numeric=(1, 2, 3)),
       "t": table(["Date", "Game ID", "Matchup (away @ home)", "Final", "Total", "Home margin", "Provenance", "Official source"],
                  rows, caption="Final scores in the verified sample · %d rows" % len(rows), numeric=(4, 5))}
    return page("verified/games.html", "Games & scores", "Official data / Games", body, "games",
                "Every NBA final score used in this research, with official source links.")


def build_lines():
    lines = AN["own_lines"]
    rows = []
    for l in lines:
        m = l["fair_margin_home"]
        spread = ("%s −%.1f" % (esc(l["home"]), abs(l["fair_line_home"]))) if m > 0 else \
                 ("%s −%.1f" % (esc(l["away"]), abs(l["fair_line_home"])))
        breakeven = (1.0 / l["home_win_prob"]) if l["home_win_prob"] else None
        rows.append((
            "<strong>%s @ %s</strong><br><span class='small muted'>%s · tip %s</span>" % (
                esc(l["away_name"]), esc(l["home_name"]), esc(l["away"]), esc(l["tip_et"])),
            num(l["fair_away_pts"]), num(l["fair_home_pts"]),
            "%+.1f" % m,
            "<strong>%s</strong>" % esc(spread),
            "<strong>%s</strong>" % num(l["fair_total_line"]),
            pct(l["home_win_prob"]),
            num(breakeven, 2),
            '<span class="blank">blank — unverified</span>',
            ext(l["source_url"], "Slate ↗") + " " + ext(l["game_url"], "Game ↗"),
        ))
    ratings = sorted(AN["ratings"], key=lambda r: -(r["off"] - r["def"]))[:10]
    rrows = [("<strong>%s</strong> %s" % (esc(r["abbr"]), esc(r["team"])), esc(str(r["n"])),
              num(r["off"]), num(r["def"]), num(r["off"] - r["def"], 1, sign=True),
              src("S2", "Team table ↗")) for r in ratings]
    prows = [(esc(p["player"]), "%s %s" % (esc(p["team"]), esc(p["team_name"])), "Points",
              num(p["reference_line"]), num(p["rpg"]), num(p["apg"]),
              '<span class="blank">blank — unverified</span>', '<span class="blank">blank — unverified</span>',
              badge("reference only", "blocked"), ext(p["source_url"], "Season leaders ↗")) for p in AN["props"]]
    pd_ = AN["parlay_dependence"]

    body = """
<h1 id="singles">Originated lines — singles, parlays and props</h1>
<p class="lede">Own4's own numbers for the two games scheduled on %(snap)s. The model turns official final scores
into shrunk offense and defense ratings, then produces a fair total, a fair spread and a win probability.
No bookmaker price is used, because no official NBA source publishes one.</p>

<div class="panel warn"><strong>Availability-blind and price-blind.</strong> These are team-strength lines. They do
not know who is injured (the official injury report was not transcribed, flag F-INJURY) and they are not compared
with any market, so no edge, stake or expected return is claimed. Every price column is blank by design.</div>

<h2>Single bets — one market, one game</h2>
%(t)s
<p class="note">"Fair line" is the negative of the originated home margin rounded to the nearest half point;
"fair total" is the originated total rounded to the nearest half point. Win probability uses the residual standard
deviation of the walk-forward margin model (σ = %(sigma).2f) applied to the originated margin. The rating table
below shows the inputs: shrunk points scored and allowed per game, where the shrinkage constant k = %(k)d was
pre-registered before the run.</p>

<h3>Model inputs — ten strongest ratings</h3>
%(r)s

<h2 id="parlays">Parlays — why the legs cannot be multiplied</h2>
<p>Inside a single game the legs are not independent. Two measurable dependencies matter for a winner-plus-total
parlay, and both are reported with a confidence interval on the <a href="correlations.html">Correlations</a> page.
On the graded sample the observed joint hit rate of the originated winner and the originated over was
<strong>%(joint).4f</strong> against an independence product of <strong>%(indep).4f</strong> — a gap of
<strong>%(gap)+.4f</strong> on %(n)d games. The gap is descriptive, not significant, and it is the reason gate G6
forbids independence pricing.</p>
%(pd)s

<h2 id="props">Player props — reference points only</h2>
<p>Official season averages exist for the leading player of each team on the slate. Per-game distributions do not:
no official game logs are available under the official-source rule, so variance, hit rate around a line and
teammate-to-teammate correlation cannot be measured. Rather than invent them, the probability and edge columns are
blank and strategies S6 and S7 are blocked (flag F-PROPS).</p>
%(p)s
<p class="note">A "reference line" is the player's official season average, which is a description of the past,
not a forecast. No over/under probability is published for any player.</p>
""" % {
        "snap": SNAPSHOT,
        "t": table(["Game", "Fair away pts", "Fair home pts", "Originated margin (home)",
                    "Fair spread", "Fair total", "Home win prob.",
                    "Break-even decimal odds (derived)", "Market price / edge", "Official source"],
                   rows, caption="Originated lines for 2026-11-05 · %d games" % len(rows),
                   numeric=(1, 2, 3, 5, 6, 7)),
        "sigma": M["sigma_margin"], "k": GATES["model_parameters"]["shrinkage_k_offense_defense"],
        "r": table(["Team", "Games in sample", "Points scored (shrunk)", "Points allowed (shrunk)", "Net", "Official source"],
                   rrows, caption="Top ten ratings after empirical-Bayes shrinkage", numeric=(1, 2, 3, 4)),
        "joint": pd_["p_joint_observed"], "indep": pd_["p_independent"], "gap": pd_["gap"], "n": pd_["n"],
        "pd": table(["Parlay structure", "Leg 1 prob.", "Leg 2 prob.", "Independence product", "Observed joint", "Gap", "Source"],
                    [("Originated winner + over the originated total (same game)", pct(pd_["p_leg1"]),
                      pct(pd_["p_leg2"]), pct(pd_["p_independent"]), pct(pd_["p_joint_observed"]),
                      "%+.4f" % pd_["gap"], repo("verification/out/analysis.json", "Analysis ↗"))],
                    caption="Measured dependence for a same-game parlay · %d graded games" % pd_["n"], numeric=(1, 2, 3, 4, 5)),
        "p": table(["Player", "Team", "Market", "Reference line (season avg)", "RPG", "APG",
                    "Over probability", "Edge", "Status", "Official source"],
                   prows, caption="Player-prop reference points for 2026-11-05 · %d rows" % len(prows),
                   numeric=(3, 4, 5)),
    }
    return page("verified/own-lines.html", "Originated lines", "Originated lines / Singles", body, "lines",
                "Originated NBA fair totals, spreads and win probabilities for 2026-11-05, plus parlay dependence and prop reference lines.")


def build_strategies():
    rows = []
    for s in AN["strategies"]:
        rows.append((esc(s["id"]), "<strong>%s</strong>" % esc(s["name"]), esc(s["family"]),
                     esc(s["priced_by"]), "%d / %d" % (s["gates_passed"], s["gates_total"]),
                     badge("no qualification", "fail"), esc(s["blocked_reason"]),
                     repo("verification/data/gates.json", "Definition ↗")))
    fam_src = repo("verification/data/gates.json", "Gates ↗")
    fam = [
        ("Singles", "One market, one game.",
         "The only family where a signal can be measured cleanly: one Bernoulli draw per game, no joint distribution to estimate.",
         fam_src),
        ("Parlays", "Two or more markets multiplied into one ticket.",
         "Profitable only if the joint probability is priced with measured dependence; pricing legs as independent inflates every long shot.",
         fam_src),
        ("Player-prop combos", "Two or more player markets in the same game.",
         "The entire edge lives in the correlation between the players' outcomes, and that correlation cannot be measured without per-game logs.",
         fam_src),
    ]
    body = """
<h1 id="catalog">Strategy catalog</h1>
<p class="lede">Eight strategies across three families. Each one is a candidate hypothesis, not a recommendation.
A hypothesis becomes eligible for the leaderboard only by passing all ten gates on the Validation page.</p>
<div class="panel bad"><strong>Current status: 0 of 8 qualify.</strong> Four required inputs are simply absent —
an official price, player game logs, availability data and a large enough graded sample. Those absences are
published, not papered over.</div>
%(t)s
<h2>Why these three families</h2>
%(f)s
<h2>What would make a strategy eligible</h2>
<div class="panel"><p>A strategy needs, in order: an official or licensed price to compare against; a sample of at
least 300 graded games; a probabilistic edge that survives multiple-testing control; and the same sign of edge in
three separate time blocks. Reaching 300 graded games at this sample's coverage would require roughly nine weeks of
the season, so no shortcut exists.</p></div>
""" % {"t": table(["ID", "Strategy", "Family", "Priced by", "Gates passed", "Status", "Why it cannot qualify now", "Definition"],
                  rows, caption="Strategy universe · %d strategies, pre-registered in gates.json" % len(rows)),
       "f": table(["Family", "What it is", "Why it is hard", "Source"], fam,
                  caption="The three strategy families")}
    return page("verified/strategies.html", "Strategy catalog", "Strategy research / Catalog", body, "strat",
                "Eight NBA betting strategy hypotheses across singles, parlays and player-prop combinations.")


def build_gates():
    rows = []
    for g in AN["gates"]:
        kind = {"PASS": "pass", "FAIL": "fail", "BLOCKED": "blocked"}[g["status"]]
        rows.append((esc(g["id"]), "<strong>%s</strong>" % esc(g["name"]), badge(g["status"].lower(), kind),
                     esc(g["rule"]), esc(g["evidence"]), esc(g["type"]),
                     repo("verification/data/gates.json", "Rule source ↗")))
    cal = AN["calibration"]
    crows = [(esc(c["bin"]), esc(str(c["games"])), pct(c["predicted_mean"]), pct(c["observed_home_win_rate"]),
              repo("verification/out/analysis.json", "Analysis ↗")) for c in cal]
    body = """
<h1>Validation gates</h1>
<p class="lede">Ten gates, written to <code>verification/data/gates.json</code> before the analysis was run.
Two of them are checks on the research itself (source compliance, reproducibility); seven are statistical; one is
market access. A strategy is eligible only if all ten pass.</p>
<div class="panel warn"><strong>Scoreboard: %(npass)d pass, %(nfail)d fail, %(nblock)d blocked.</strong>
The failures are not close calls. The sample floor is missed by 265 games, the winner model loses to the free home
baseline, and the single nominal result fails multiple-testing control once both strategy tests are counted.</div>
%(t)s
<h2>Calibration of the originated win probability</h2>
<p>A probability is only useful if games predicted at 60%% happen about 60%% of the time. With %(n)d graded games the
buckets are small, and the middle bucket is visibly noisy — which is exactly the point of the sample floor.</p>
%(c)s
<p class="note">Gate G7 is <strong>blocked</strong>, not failed: it demands a price that no official NBA source
publishes. Gate G6 and G9 pass because dependence is measured and every row is source-linked; they do not make a
strategy profitable.</p>
""" % {"t": table(["ID", "Gate", "Status", "Rule", "Evidence from this run", "Type", "Source"],
                  rows, caption="All ten gates, evaluated · %d rows" % len(rows)),
       "c": table(["Predicted home-win probability", "Games", "Mean predicted", "Observed home-win rate", "Source"],
                  crows, caption="Calibration buckets", numeric=(1, 2, 3)),
       "n": M["graded"],
       "npass": sum(1 for g in AN["gates"] if g["status"] == "PASS"),
       "nfail": sum(1 for g in AN["gates"] if g["status"] == "FAIL"),
       "nblock": sum(1 for g in AN["gates"] if g["status"] == "BLOCKED")}
    return page("verified/validation.html", "Validation gates", "Strategy research / Gates", body, "gates",
                "Ten pre-registered validation gates for NBA betting strategies, evaluated against measured data.")


def build_correlations():
    trows = []
    for c in AN["team_correlations"]:
        v = badge("survives FDR", "pass") if c["bh_reject"] else badge("does not survive", "neutral")
        trows.append((esc(c["label"]), esc(str(c["n"])), num(c["r"], 4),
                      "[%s, %s]" % (num(c["ci_low"], 4), num(c["ci_high"], 4)), pval(c["p"]), v,
                      src("S2", "Team table ↗") + " " + src("S1", "Standings ↗")))
    grows = [(esc(c["label"]), esc(str(c["n"])), num(c["r"], 4),
              "[%s, %s]" % (num(c["ci_low"], 4), num(c["ci_high"], 4)), pval(c["p"]), esc(c["why"]),
              ext(c["source_url"], "Games ↗")) for c in AN["game_correlations"]]
    pd_ = AN["parlay_dependence"]
    body = """
<h1>Correlations</h1>
<p class="lede">Every correlation on this page is computed from the verified snapshot, carries a 95%% confidence
interval from the Fisher z transform, and is tested against a null of zero. The team table applies
Benjamini-Hochberg control because ten features were tested at once.</p>

<h2>Team-level: what tracks winning</h2>
%(t)s
<p class="note">n = 30 teams, so these are relationships between team season-to-date statistics, not betting signals.
Point differential explains most of the variance in win percentage by construction. The interesting measurements are
the ones that survive FDR but are not mechanical: three-point percentage (r = %(r3p).3f) and turnovers
(r = %(rtov).3f, negative). Free-throw percentage, rebounds, assists, steals and blocks do not survive.</p>

<h2>Game-level: dependence that a parlay must price</h2>
%(g)s
<p class="note">The first row is the pace dependence that makes two teams' points move together; here it is small
(r = %(rpace).3f) on %(npace)s games, which is itself a finding: on this sample, a game's two totals are close to
independent. The second row is the dependence between the two legs of a winner-plus-total same-game parlay.</p>

<h2>Parlay dependence, priced</h2>
<div class="panel"><p>Leg 1: originated winner (hit rate <strong>%(p1).4f</strong>). Leg 2: over the originated total
(hit rate <strong>%(p2).4f</strong>). Multiplying gives <strong>%(pi).4f</strong>; the observed joint hit rate is
<strong>%(pj).4f</strong> over %(n)s graded games, a gap of <strong>%(gap)+.4f</strong>. With n = %(n)s the
interval around that gap is wide, so the number is published as a measured quantity with its uncertainty, not as a
pricing rule. This is the reason gate G6 exists.</p></div>

<h2>What cannot be measured, and is therefore blank</h2>
<div class="panel bad"><p><strong>Teammate-to-teammate player correlations are blank.</strong> A prop combo's edge
lives almost entirely in the correlation between the two players' outcomes (shared minutes, shared pace, shared
garbage time). Measuring it needs per-game logs, which the official-source rule does not provide here. The
corresponding strategies are blocked, not assumed independent — assuming independence would be the single easiest
way to manufacture a fake edge on this page.</p></div>
""" % {
        "t": table(["Feature (from official team table)", "n", "r vs win%", "95% CI", "p", "FDR", "Official sources"],
                   trows, caption="Team-level correlation with win percentage · n = 30 · BH at q = 0.05",
                   numeric=(1, 2, 4)),
        "g": table(["Measured relationship", "n", "r", "95% CI", "p", "What it means", "Official source"],
                   grows, caption="Game-level dependence in the verified sample", numeric=(1, 2, 4)),
        "r3p": [c for c in AN["team_correlations"] if c["feature"] == "3P_pct"][0]["r"],
        "rtov": [c for c in AN["team_correlations"] if c["feature"] == "TOV"][0]["r"],
        "rpace": AN["game_correlations"][0]["r"], "npace": AN["game_correlations"][0]["n"],
        "p1": pd_["p_leg1"], "p2": pd_["p_leg2"], "pi": pd_["p_independent"],
        "pj": pd_["p_joint_observed"], "n": pd_["n"], "gap": pd_["gap"],
    }
    return page("verified/correlations.html", "Correlations", "Strategy research / Correlations", body, "corr",
                "Measured NBA correlations with confidence intervals and FDR control, including same-game parlay dependence.")


def build_backtest():
    blocks = AN["blocks"]
    brows = [(esc(str(b["block"])), "%s → %s" % (esc(b["from"]), esc(b["to"])), esc(str(b["games"])),
              pct(b["accuracy"]), num(b["mae_total"]),
              badge("beats baseline", "pass") if b["over_baseline"] else badge("loses to baseline", "fail"),
              repo("verification/out/analysis.json", "Analysis ↗")) for b in blocks]
    g_rows = []
    for g in AN["graded_games"]:
        g_rows.append((esc(g["date"]), esc(g["game_id"]), "%s @ %s" % (esc(g["away"]), esc(g["home"])),
                       "%+.1f" % g["pred_margin"], "%+.0f" % g["actual_margin"],
                       num(g["pred_total"]), esc(str(g["actual_total"])),
                       badge("hit", "pass") if g["winner_correct"] else badge("miss", "fail"),
                       ext(g["source_url"], "Date ↗") + " " + ext(g["game_url"], "Game ↗")))
    body = """
<h1>Backtest and luck removal</h1>
<p class="lede">The model is graded strictly out of sample: every prediction for a game uses only games that were
played before it. Nothing is fitted on the games it is scored on. The question is not whether it made money but
whether anything it does could be distinguished from luck.</p>

<h2>Headline numbers</h2>
<div class="cards">
  <div class="card"><b>%(acc).4f</b><span>winner accuracy, %(wins)d of %(n)d graded</span></div>
  <div class="card"><b>%(home).4f</b><span>always-pick-home baseline on the same games</span></div>
  <div class="card bad"><b>%(pvhome).4f</b><span>one-sided p that the model beats that baseline</span></div>
  <div class="card"><b>%(maet).3f</b><span>MAE of the originated total</span></div>
  <div class="card"><b>%(maeb).3f</b><span>MAE of the naive running-average total</span></div>
  <div class="card warn"><b>%(pper).4f</b><span>permutation p for the totals improvement</span></div>
  <div class="card bad"><b>%(power)s</b><span>games needed to detect a real 55%% edge at 80%% power</span></div>
  <div class="card bad"><b>0</b><span>strategies that clear the gates</span></div>
</div>

<div class="panel bad"><h3>Reading the result honestly</h3><p>The model's winner picks are <em>worse</em> than
picking the home team every time (0.5714 vs 0.6000). Its bootstrap accuracy interval runs from
<strong>%(cilo).4f</strong> to <strong>%(cihi).4f</strong> on %(n)d games — so wide that neither skill nor
incompetence is established. The totals model does beat the naive baseline by %(gain).3f points of MAE with
permutation p = %(pper).4f, but that p-value is one of two tests in this run, so Benjamini-Hochberg at q = 0.05
requires p ≤ 0.025, and it therefore fails. This is precisely the situation the gates exist to catch.</p></div>

<h2>Stability across time blocks</h2>
%(b)s
<p class="note">Block accuracies swing from 0.4545 to 0.7273 across eleven-game blocks. That oscillation is what
sampling noise looks like, and it is why gate G5 requires a consistent sign in every block rather than a good
average.</p>

<h2>Luck tests</h2>
%(l)s

<h2>Every graded game</h2>
<p>%(n)d games carry a prediction and an official source link. Games without three prior appearances by both teams
are excluded rather than back-filled: %(skip)d games were skipped for that reason.</p>
%(g)s
""" % {
        "acc": M["winner_accuracy"], "wins": M["wins"], "n": M["graded"], "home": M["home_baseline_accuracy"],
        "pvhome": M["binom_p_vs_home_baseline"], "maet": M["mae_total"], "maeb": M["mae_total_baseline"],
        "pper": M["permutation_p_totals"], "power": M["power_games_needed_for_55pct_edge"],
        "cilo": M["accuracy_bootstrap_ci"][0], "cihi": M["accuracy_bootstrap_ci"][1],
        "gain": M["mae_total_improvement"], "skip": AN["sample"]["skipped_insufficient_history"],
        "b": table(["Block", "Dates", "Games", "Winner accuracy", "MAE total", "Totals vs baseline", "Source"],
                   brows, caption="Three disjoint time blocks", numeric=(2, 3, 4)),
        "g": table(["Date", "Game ID", "Matchup", "Originated margin", "Actual margin",
                    "Originated total", "Actual total", "Pick", "Official source"],
                   g_rows, caption="Every graded game · %d rows · strict walk-forward" % len(g_rows),
                   numeric=(3, 4, 5, 6)),
        "l": table(["Test", "What it asks", "Result", "Verdict", "Source"], [
            ("Exact binomial, two-sided, vs 0.5", "Could this hit rate come from a coin flip?",
             "p = %s" % pval(M["binom_p_vs_0_5"]), badge("not significant", "neutral") if (M["binom_p_vs_0_5"] or 1) > 0.05 else badge("significant", "pass"),
             repo("verification/out/analysis.json", "Analysis ↗")),
            ("Exact binomial, one-sided, vs home baseline", "Is the model better than free information?",
             "p = %s" % pval(M["binom_p_vs_home_baseline"]), badge("no — model is worse", "fail"),
             repo("verification/out/analysis.json", "Analysis ↗")),
            ("Paired bootstrap, 10,000 resamples", "How wide is the accuracy interval?",
             "[%.4f, %.4f]" % (M["accuracy_bootstrap_ci"][0], M["accuracy_bootstrap_ci"][1]), badge("inconclusive", "blocked"),
             repo("verification/analysis.py", "Code ↗")),
            ("Permutation, 10,000 shuffles", "Is the totals improvement better than chance pairing?",
             "p = %s" % pval(M["permutation_p_totals"]), badge("nominal only — fails FDR", "fail"),
             repo("verification/analysis.py", "Code ↗")),
            ("Benjamini-Hochberg, m = 2, q = 0.05", "Does any result survive multiple testing?",
             "smallest admissible p = 0.0250", badge("nothing survives", "fail"),
             repo("verification/data/gates.json", "Gates ↗")),
            ("Power analysis", "How many games would a real 55% edge need?",
             "%d games at 80%% power" % M["power_games_needed_for_55pct_edge"], badge("far out of reach", "fail"),
             repo("verification/analysis.py", "Code ↗")),
        ], caption="Luck-removal battery")}
    return page("verified/backtest.html", "Backtest & luck", "Strategy research / Backtest", body, "back",
                "Walk-forward NBA backtest with bootstrap, permutation and power analysis; no edge established.")


def build_leaderboard():
    rows = []
    for s in AN["strategies"]:
        rows.append((esc(s["id"]), esc(s["name"]), esc(s["family"]), "%d / %d" % (s["gates_passed"], s["gates_total"]),
                     badge("no qualification", "fail"), "0", esc(s["blocked_reason"]),
                     repo("verification/out/analysis.json", "Scoring input ↗")))
    body = """
<h1>Leaderboard and rewards</h1>
<p class="lede">The competition is designed to reward demonstrated, replicated skill — not a hot week. A strategy
earns a place only by clearing all ten gates; until then its reward is exactly zero, however good its record looks.</p>

<div class="panel"><h3>Scoring rules</h3><p>Eligibility: all ten gates must pass on the same locked snapshot.
Ranking among eligible strategies is by <strong>out-of-sample Brier score</strong> for probability markets and by
<strong>MAE</strong> for line markets, with the sample size and the FDR-adjusted p-value published next to each rank.
A strategy that fails a gate scores nothing — there is no partial credit for a good-looking record, because partial
credit is how luck gets paid.</p></div>

<div class="panel bad"><h3>Standings: no qualified entries</h3><p>Zero of eight strategies qualify, so the reward
pool is unpaid. This is the correct output of the design, not a failure of it: the sample is 35 graded games against
a 300-game floor, and the one nominal signal does not survive multiple-testing control.</p></div>
%(t)s

<h2>What a qualifying submission would look like</h2>
<div class="panel"><p>It would need a locked, timestamped snapshot; at least 300 graded games; a price from an
official or licensed source so expected value is computable; a measured dependence adjustment for every combination;
FDR survival across every test in the run; and the same sign of edge in three separate time blocks. None of those
conditions is met by anything published so far in this repository.</p></div>
""" % {"t": table(["ID", "Strategy", "Family", "Gates passed", "Status", "Reward", "Why", "Source"],
                  rows, caption="Leaderboard · snapshot %s · rewards awarded: 0" % SNAPSHOT)}
    return page("verified/leaderboard.html", "Leaderboard & rewards", "Competition / Leaderboard", body, "board",
                "NBA strategy competition leaderboard with zero qualified strategies and zero rewards awarded.")


def build_sources():
    rows = []
    for sid in sorted(SRC, key=lambda k: int(k[1:])):
        s = SRC[sid]
        rows.append((esc(sid), "<strong>%s</strong>" % esc(s["name"]), ext(s["url"], "Open ↗"),
                     esc(s["read_scope"]), esc(s["read_on"]),
                     badge("official", "official") if s["official"] else badge("third party", "warn")))
    body = """
<h1>Source register</h1>
<p class="lede">Every source this snapshot touches, what was read from it, and when. If a value is not in this
register, it is not on this site.</p>
<div class="panel warn"><strong>Usage restriction.</strong> The NBA Stats FAQ states that statistics are not available
for download for either academic or personal use. This session therefore transcribed only the values needed for the
research, with the exact page retained on every row. It did not scrape, call an API or bulk-copy. See flag F-RIGHTS
on the <a href="flagged.html">Flagged for review</a> page.</div>
%(t)s
<h2>Rules applied to every value</h2>
<div class="panel"><p><strong>Official or blank.</strong> A number appears only if it was read from an official page
and is reproduced with its URL. If it cannot be confirmed, the cell is blank and the reason is flagged.
<strong>No inference.</strong> Missing games are not estimated, missing prices are not guessed, and missing player
logs are not simulated. <strong>Provenance on every row.</strong> Tables separate fresh transcription from inherited,
corroborated data so a reader always knows which is which.</p></div>
""" % {"t": table(["ID", "Source", "Link", "What was read", "Read on", "Type"],
                  rows, caption="Source register · %d entries" % len(rows))}
    return page("verified/sources.html", "Source register", "Governance / Sources", body, "sources",
                "Register of every official NBA source used in the 2026-11-05 snapshot.")


def build_audit():
    rows = []
    for c in REC["checks"]:
        kind = {"PASS": "pass", "FAIL": "fail", "NOTE": "blocked"}[c["status"]]
        rows.append((esc(c["id"]), esc(c["name"]), badge(c["status"].lower(), kind),
                     esc(c["expected"]), esc(c["actual"]), esc(c["note"]),
                     ext(c["source_url"], "Official ↗")))
    findings = [
        ("A01", "The inherited snapshot is internally consistent", "Standings and team stats in official/ agree on W-L for all 30 teams (check C11), and both reconcile to the live tables once the newly verified games are added (C05).", "verified", repo("official/standings.json")),
        ("A02", "Every sampled date is complete", "Six inherited dates hold exactly the number of games the official calendar lists: 11, 12, 12, 10, 7 and 4. No date is short a game.", "verified", src("S6")),
        ("A03", "36 games were never captured", "Seven October dates (10/20, 10/22, 10/24, 10/25, 10/26, 10/27, 10/29) are absent from the sample. Coverage is 85 of 121 games.", "flagged", src("S6")),
        ("A04", "The published +/- column is not internally consistent", "The 30 values sum to -5.3 instead of 0. Cause unexplained; the column is displayed but not used as a model input.", "flagged", src("S2")),
        ("A05", "Third-party data exists in the repository", "data/raw/espn/ holds ESPN scoreboard and summary JSON, and other workspaces were built on a third-party mirror. None of it is official and none of it is used here.", "excluded", repo("data/raw/espn")),
        ("A06", "Multiple overlapping dashboards", "Root, pages/, docs/, lab/, lines-lab/, nba-evidence/ and four NFL workspaces. This release makes the root page canonical and links the rest; no peer file was edited or deleted.", "retained", repo("COORDINATION.md")),
        ("A07", "The previous landing page presented 2026-11-02 values as current", "It carried the correct date but is now stale. A copy is preserved at pages/legacy-root-dashboard.html and linked from the sidebar.", "superseded", repo("pages/legacy-root-dashboard.html")),
        ("A08", "No automated check tied published numbers to their data files", "This session adds verification/verify_site.py, which fails when a table row lacks a source link, a local link is broken, or a page is missing its navigation and helpline footer.", "fixed", repo("verification/verify_site.py")),
        ("A09", "GitHub Pages serves the repository root through the legacy configuration", "The Pages API reports build_type legacy, source main, path /, status built. No settings change was needed or attempted.", "verified", src("S11")),
        ("A10", "Player-level data was never available in this repository", "No workspace has official per-game player logs; prop work everywhere in the repo is therefore descriptive, not predictive.", "flagged", repo("nba-evidence/data/players.csv")),
    ]
    body = """
<h1>Repository audit</h1>
<p class="lede">What was already in the repository, checked mechanically against the official pages re-read on
%(snap)s. Thirteen checks: %(p)d pass, %(f)d fail, %(n)d explicit notes. Nothing was silently corrected — a
discrepancy is reported with its numbers so it can be re-run.</p>

<h2>Reconciliation checks</h2>
%(t)s

<h2>Findings on the inherited work</h2>
%(a)s

<h2>What this session changed, and what it did not</h2>
<div class="panel"><p><strong>Added:</strong> verification/ (transcription, reconciliation, analysis, builder and site
checks), the root dashboard you are reading, the verified/ category pages, and append-only entries in README.md and
COORDINATION.md. <strong>Preserved unmodified:</strong> every peer workspace (docs/, lab/, lines-lab/, nba-evidence/,
nfl*), the legacy root dashboard (copied to pages/legacy-root-dashboard.html) and all prior data files.
<strong>Not done:</strong> no value was edited to make it agree with another value; no missing game, price or player
log was inferred.</p></div>
""" % {"snap": SNAPSHOT, "p": REC["summary"]["pass"], "f": REC["summary"]["fail"], "n": REC["summary"]["note"],
       "t": table(["ID", "Check", "Result", "Expected", "Actual", "Note", "Source"],
                  rows, caption="Reconciliation of the repository against official pages · 13 checks"),
       "a": table(["ID", "Finding", "Detail", "Verdict", "Source"],
                  [(a, "<strong>%s</strong>" % b, c,
                    badge(d, {"verified": "pass", "flagged": "blocked", "excluded": "warn",
                              "retained": "neutral", "superseded": "neutral", "fixed": "pass"}[d]), e)
                   for a, b, c, d, e in findings],
                  caption="Ten findings on the inherited material")}
    return page("verified/audit.html", "Repo audit", "Governance / Repo audit", body, "audit",
                "Line-by-line audit of the repository's NBA data against official pages, with reconciliation checks.")


def build_flags():
    rows = []
    for f in FLAGS:
        sev = {"high": "fail", "medium": "blocked", "low": "neutral"}[f["severity"]]
        rows.append((esc(f["id"]), badge(f["severity"], sev), "<strong>%s</strong>" % esc(f["item"]),
                     esc(f["detail"]), esc(f["impact"]),
                     ext(f["source_url"], "Official ↗") + " " + ext(f["repo_url"], "Repo ↗")))
    body = """
<h1>⚑ Flagged for review</h1>
<p class="lede">Every irregularity and every value that could not be confirmed from an official source. None of
these blocks publication; all of them block a claim. Each entry carries the official page and the repository file
behind it so it can be reviewed directly.</p>
<div class="panel warn"><strong>%(n)d flags: %(h)d high, %(m)d medium, %(l)d low.</strong> They fall into three
kinds — data that is absent (prices, player logs, availability), data that is partial (36 uncaptured games, 56
un-re-fetched rows), and data that is present but internally odd (the +/- sum). The third kind is the most
interesting, because it is the only one an official page itself could resolve.</div>
%(t)s
<h2>How to request a change</h2>
<div class="panel"><p>Each row above names the file and the official page. Re-fetch the page, compare it with the
published value, and either confirm the value or open an issue quoting both. A flag is closed only by an official
page, never by a calculation.</p></div>
""" % {"n": len(FLAGS),
       "h": sum(1 for f in FLAGS if f["severity"] == "high"),
       "m": sum(1 for f in FLAGS if f["severity"] == "medium"),
       "l": sum(1 for f in FLAGS if f["severity"] == "low"),
       "t": table(["ID", "Severity", "Item", "What was found", "Impact on published numbers", "Sources"],
                  rows, caption="Flagged for review · %d entries" % len(FLAGS))}
    return page("verified/flagged.html", "Flagged for review", "Governance / Flagged for review", body, "flags",
                "Every irregularity and unverified value in the Own4 NBA research, with source links.")


def spread_text(line):
    m = line["fair_margin_home"]
    if m > 0:
        return "fair spread %s −%.1f" % (esc(line["home"]), abs(line["fair_line_home"]))
    return "fair spread %s −%.1f" % (esc(line["away"]), abs(line["fair_line_home"]))


def build_summary():
    M_ = M
    gates = AN["gates"]
    corr = AN["team_correlations"]
    surv = [c for c in corr if c["bh_reject"]]
    body = """
<h1>Executive summary</h1>
<p class="lede">Own4 builds its own NBA numbers from official league data, tests whether any of them carry signal
after luck is removed, and publishes the scoreboard even when the answer is no. Snapshot <strong>%(snap)s</strong>.</p>

<h2>1. What this release is</h2>
<p>A verified data snapshot, a transparent line-origination model, a pre-registered gate system, and a competition
design that pays nothing until a strategy clears every gate. It is research infrastructure with an honest scoreboard,
not a tip sheet.</p>

<h2>2. Data</h2>
<p>%(stand)d standings rows, %(tstat)d team-stat rows and %(slate)d scheduled games were read from nba.com on
%(snap)s. %(fresh)d final scores were read from the official games pages for 2026-11-02 and 2026-11-04.
%(inherited)d further final scores were already in the repository from 2026-11-02 and were corroborated rather than
re-fetched: each sampled date holds exactly the number of games the official calendar lists, and all 30 teams'
records advance exactly by their results in the newly verified games. The sample covers <strong>%(cov).1f%%</strong>
of the season to date (%(samp)d of %(off)d games); seven October dates, %(miss)d games, were never captured and are
excluded from every calculation.</p>

<h2>3. Originated lines</h2>
<p>The model converts official final scores into shrunk per-team offense and defense ratings and produces a fair
total, a fair spread and a win probability. For 2026-11-05 it originates
<strong>%(g1)s at %(h1)s</strong>: fair total <strong>%(t1)s</strong>, %(sp1)s. And
<strong>%(g2)s at %(h2)s</strong>: fair total <strong>%(t2)s</strong>, %(sp2)s. Every price field is blank:
no official NBA source publishes a price, and the official games page's odds toggle exposed no values to this
session. No expected value, stake or return is claimed.</p>

<h2>4. Signal research</h2>
<p>Ten team-level correlations were measured with confidence intervals and FDR control; <strong>%(nsurv)d survive</strong>
at q = 0.05 — point differential (r = %(r1).3f), points per game (r = %(r2).3f), field-goal percentage
(r = %(r3).3f), three-point percentage (r = %(r4).3f) and turnovers (r = %(r5).3f, negative). Same-game pace
dependence between the two teams' points is small (r = %(rpace).3f on %(npace)d games), which is itself a useful
negative result for parlay pricing. Player-to-player prop correlations cannot be measured at all without per-game
logs, so they are blank rather than assumed.</p>

<h2>5. Luck removal</h2>
<p>The strict walk-forward backtest grades %(n)d games. Winner accuracy is <strong>%(acc).4f</strong> against a
free home-team baseline of <strong>%(home).4f</strong> — the model loses, with a one-sided p of %(pvhome).4f. The
bootstrap interval on accuracy runs [%(cilo).4f, %(cihi).4f] and establishes nothing either way. The totals model
does beat its naive baseline by %(gain).3f points of MAE (permutation p = %(pper).4f), but fails the 300-game floor
and fails Benjamini-Hochberg once both strategy tests are counted. A real 55%% edge would need about
<strong>%(power)s graded games</strong> to be detected with 80%% power.</p>

<h2>6. Gates and competition</h2>
<p>Of ten pre-registered gates, %(npass)d pass, %(nfail)d fail and %(nblock)d is blocked for lack of a price.
<strong>Zero of eight strategies qualify and zero rewards are awarded.</strong> The leaderboard is published empty on
purpose: partial credit is how variance gets paid.</p>

<h2>7. What is not known</h2>
<p>Prices, player game logs, player availability and %(miss)d games of this season are missing. The published +/-
column does not sum to zero. The inherited game rows were not individually re-fetched. These are listed on the
<a href="flagged.html">Flagged for review</a> page with the page and file behind each one.</p>

<h2>8. What would change the conclusion</h2>
<p>In order: an official or licensed price history so that expected value is computable; a complete season of
official finals to clear the sample floor; official per-game player logs to make prop work possible at all; and
availability data so team lines stop being strength-only. Until then the correct output of this system is a verified
dataset and a scoreboard of zeroes.</p>

<h2>Reference</h2>
%(refs)s
""" % {
        "snap": SNAPSHOT, "stand": len(STAND), "tstat": len(TSTATS), "slate": len(SLATE),
        "fresh": len(FRESH), "inherited": len(OLDG),
        "cov": REC["summary"]["coverage_pct"], "samp": REC["summary"]["sample_games"],
        "off": REC["summary"]["official_games"], "miss": REC["summary"]["missing_games"],
        "g1": AN["own_lines"][0]["away"], "g2": AN["own_lines"][1]["away"],
        "t1": num(AN["own_lines"][0]["fair_total_line"]), "t2": num(AN["own_lines"][1]["fair_total_line"]),
        "h1": esc(AN["own_lines"][0]["home"]), "h2": esc(AN["own_lines"][1]["home"]),
        "sp1": spread_text(AN["own_lines"][0]), "sp2": spread_text(AN["own_lines"][1]),
        "nsurv": len(surv),
        "r1": corr[0]["r"], "r2": corr[1]["r"], "r3": corr[2]["r"], "r4": corr[3]["r"], "r5": corr[7]["r"],
        "rpace": AN["game_correlations"][0]["r"], "npace": AN["game_correlations"][0]["n"],
        "n": M_["graded"], "acc": M_["winner_accuracy"], "home": M_["home_baseline_accuracy"],
        "pvhome": M_["binom_p_vs_home_baseline"],
        "cilo": M_["accuracy_bootstrap_ci"][0], "cihi": M_["accuracy_bootstrap_ci"][1],
        "gain": M_["mae_total_improvement"], "pper": M_["permutation_p_totals"],
        "power": M_["power_games_needed_for_55pct_edge"],
        "npass": sum(1 for g in gates if g["status"] == "PASS"),
        "nfail": sum(1 for g in gates if g["status"] == "FAIL"),
        "nblock": sum(1 for g in gates if g["status"] == "BLOCKED"),
        "refs": table(["Reference", "Used for", "Link"], [
            ("NBA.com standings", "30 standings rows", src("S1", "Open ↗")),
            ("NBA.com Teams — Traditional", "30 team-stat rows", src("S2", "Open ↗")),
            ("NBA.com Games &amp; Scores", "All final scores and the 11/05 slate", src("S4", "Open ↗")),
            ("NBA Stats glossary", "Column definitions", src("S8", "Open ↗")),
            ("NBA Stats FAQ", "Usage restriction", src("S9", "Open ↗")),
            ("NBA injury report 2026-27", "Required availability check (not transcribed)", src("S10", "Open ↗")),
            ("NCPG helpline", "Responsible gambling footer", src("S12", "Open ↗")),
        ], caption="References")}
    return page("verified/executive-summary.html", "Executive summary", "Overview / Executive summary", body, "summary",
                "Executive summary of the Own4 NBA line-origination research, snapshot 2026-11-05.")


def main():
    written = [
        build_index(), build_summary(), build_standings(), build_stats(), build_games(),
        build_lines(), build_strategies(), build_gates(), build_correlations(),
        build_backtest(), build_leaderboard(), build_sources(), build_audit(), build_flags(),
    ]
    print("wrote %d pages:" % len(written))
    for p in written:
        print("  ", p)


if __name__ == "__main__":
    main()

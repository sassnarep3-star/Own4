#!/usr/bin/env python3
"""
Own4 / nba-lines — deterministic static site builder (session arena-7a06a47e-own4).

Renders the canonical NBA line-origination dashboard into nba-lines/site/ and a
clean landing page into the repository root (index.html), which is what GitHub
Pages serves at https://sassnarep3-star.github.io/Own4/.

Contracts enforced by verify.py:
  * every <tr> of a table marked data-sourced="1" carries a link to an official
    source or to the committed data file it was derived from;
  * every internal href resolves to a file that exists;
  * a blank cell is never presented as a number.

Run:  python3 build.py
"""

import html
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SITE = os.path.join(HERE, "site")
ROOT = os.path.dirname(HERE)
REL = ".."  # from site/<category>/<page>.html back to site/

S = {
    "standings": "https://www.nba.com/standings",
    "g1002": "https://www.nba.com/games?date=2026-11-02",
    "g1004": "https://www.nba.com/games?date=2026-11-04",
    "slate": "https://www.nba.com/games?date=2026-11-05",
    "injury_policy": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "injury_pdf": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf",
    "faq": "https://www.nba.com/stats/help/faq",
    "glossary": "https://www.nba.com/stats/help/glossary",
    "ncpg": "https://www.ncpgambling.org/help-treatment",
    "nist": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35.htm",
    "sk_cv": "https://scikit-learn.org/stable/modules/cross_validation.html",
    "sk_cal": "https://scikit-learn.org/stable/modules/calibration.html",
    "bh": "https://doi.org/10.1111/j.2517-6161.1995.tb02031.x",
    "gh_pages": "https://docs.github.com/en/rest/pages/pages",
    "repo": "https://github.com/sassnarep3-star/Own4",
}

NAV = [
    ("Overview", [("index.html", "Dashboard")]),
    ("Official data", [
        ("data/standings.html", "Standings"),
        ("data/results.html", "Game results"),
        ("data/slate.html", "Tonight's slate"),
        ("data/availability.html", "Player availability"),
    ]),
    ("Originated lines", [
        ("lines/singles.html", "Singles"),
        ("lines/parlays.html", "Parlays & SGP"),
        ("lines/props.html", "Player props"),
    ]),
    ("Strategy research", [
        ("research/strategies.html", "Strategy catalog"),
        ("research/correlations.html", "Correlations"),
        ("research/gates.html", "Validation gates"),
        ("research/backtest.html", "Walk-forward & luck"),
    ]),
    ("Competition", [("competition/leaderboard.html", "Leaderboard")]),
    ("Governance", [
        ("governance/methodology.html", "Method & requirements"),
        ("governance/sources.html", "Source register"),
        ("governance/repo-review.html", "Repo review"),
        ("governance/flagged.html", "Flagged for review"),
    ]),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def esc(x):
    return html.escape(str(x), quote=True)


def num(x, d=2, signed=False):
    if x is None:
        return blank()
    if signed:
        return f"{x:+.{d}f}"
    return f"{x:.{d}f}"


def pct(x, d=1):
    if x is None:
        return blank()
    return f"{x * 100:.{d}f}%"


def odds(x):
    if x is None:
        return blank()
    return f"{x:+.0f}"


def blank():
    return '<span class="blank" title="Unverified or unavailable — see Flagged for review">—</span>'


BADGE_MAP = {
    "pass": "b-pass", "passes": "b-pass", "fail": "b-fail", "pending": "b-pending",
    "needs review": "b-needs-review", "flagged": "b-flagged", "high": "b-fail",
    "medium": "b-pending", "low": "b-info", "info": "b-info",
}


def badge(text):
    key = str(text).lower()
    cls = BADGE_MAP.get(key, "b-info")
    return f'<span class="badge {cls}">{esc(text)}</span>'


def src(*links):
    parts = []
    for label, url in links:
        if url is None:
            continue
        parts.append(f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>')
    return '<td class="src">' + " · ".join(parts) + "</td>"


def table(tid, headers, rows, caption=None, numcols=(), sourced=True, tools=True,
          search_placeholder=None):
    out = []
    if tools:
        opts = "".join(
            f'<option value="{esc(h)}">{esc(h)}</option>' for h in headers if h not in ("Source", "Evidence", "Links")
        )
        out.append(
            f'<div class="filters" data-table-tools="{tid}">'
            f'<input type="search" placeholder="{esc(search_placeholder or "Filter rows…")}" aria-label="Filter rows">'
            f'<select aria-label="Filter by column"><option value="">All columns</option>'
            f'<option value="__blank__">Hide blank cells</option>{opts}</select>'
            f'<span class="count"></span></div>'
        )
    out.append('<div class="tablewrap"><table class="data" id="%s" data-sourced="%d">' % (tid, 1 if sourced else 0))
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(
        f'<th class="{"num" if h in numcols else ""}">{esc(h)}</th>' for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        cells = []
        for h, c in zip(headers, r):
            if isinstance(c, tuple) and c and c[0] == "td":
                cells.append(c[1])
            else:
                cls = "num" if h in numcols else ""
                cells.append(f'<td class="{cls}">{c}</td>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def kpi(value, label, note="", tone=""):
    cls = f"kpi {tone}".strip()
    n = f'<div class="note">{note}</div>' if note else ""
    return f'<div class="{cls}"><div class="v">{value}</div><div class="l">{esc(label)}</div>{n}</div>'


def callout(text, kind=""):
    return f'<div class="callout {kind}">{text}</div>'


def page(path, title, body, active, lede="", crumbs=None):
    depth = path.count("/")
    prefix = "" if depth == 0 else "../" * depth
    nav = []
    for group, items in NAV:
        links = []
        for href, label in items:
            cls = ' class="active"' if href == active else ""
            links.append(f'<a href="{prefix}{href}"{cls}>{esc(label)}</a>')
        nav.append(f'<div class="navgroup"><h3>{esc(group)}</h3>{"".join(links)}</div>')
    cr = crumbs or []
    crumb_html = " / ".join(
        [f'<a href="{prefix}index.html">Dashboard</a>'] +
        [esc(c) for c in cr])
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own4 NBA Line Lab</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<div class="shell">
<aside class="nav">
<a class="brand" href="{prefix}index.html">Own4 <span>NBA Line Lab</span></a>
<div class="brand-sub">Verified 2026-27 research</div>
{"".join(nav)}
<div class="navfoot">
Data as of <strong>2026-11-05</strong><br>
121 official finals · 0 reward-eligible<br>
<a href="{prefix}governance/flagged.html">{N_FLAGS} flagged items</a>
</div>
</aside>
<main>
<div class="crumbs">{crumb_html}</div>
<h1>{esc(title)}</h1>
{lede_html}
{body}
<footer class="site">
<p>Research only — not wagering advice, and not a betting product. Every value on this site is either copied from an
official NBA page or computed from committed data by a formula on the <a href="{prefix}governance/methodology.html">method
page</a>; anything that could not be verified is left blank and listed on
<a href="{prefix}governance/flagged.html">Flagged for review</a>.</p>
<p>Problem gambling? National Problem Gambling Helpline <strong>1-800-MY-RESET</strong> ·
<a href="{S['ncpg']}" rel="noopener">ncpgambling.org/help-treatment</a></p>
<p>Built by session <code>arena-7a06a47e-own4</code>. Source: <a href="{S['repo']}" rel="noopener">github.com/sassnarep3-star/Own4</a>.
Static pages, no tracking, no third-party scripts.</p>
</footer>
</main>
</div>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""
    return doc


# --------------------------------------------------------------------------
# page builders
# --------------------------------------------------------------------------


def load():
    d = {}
    for k, f in (("derived", "derived.json"), ("standings", "standings_2026-11-05.json"),
                 ("results", "results_2026-27.json"), ("slate", "slate_2026-11-05.json"),
                 ("injuries", "injuries_2026-11-05.json"), ("sources", "sources.json"),
                 ("review", "repo_review.json"), ("flags", "flags.json")):
        with open(os.path.join(DATA, f), encoding="utf-8") as fh:
            d[k] = json.load(fh)
    return d


D = load()
X = D["derived"]
CORPUS = X["corpus"]
BEST = max((s for s in X["strategies"] if s["skill"] is not None), key=lambda s: s["skill"])
N_FLAGS = len(D["flags"]["rows"])
N_ELIGIBLE = sum(1 for b in X["leaderboard"] if b["eligible"])
N_REVIEW = len(D["review"]["rows"])


def page_index():
    l1, l2 = X["lines"]
    body = [
        '<div class="kpis">',
        kpi(f'{CORPUS["games"]}', "Official finals", "2026-10-20 → 2026-11-04", "good"),
        kpi("30/30", "Teams reconciled", "W-L rebuilt from finals", "good"),
        kpi(f'{CORPUS["graded_predictions"]}', "Graded predictions", "strictly walk-forward"),
        kpi(f'{N_ELIGIBLE}', "Reward-eligible", "gates G3/G9 fail", "bad"),
        kpi(f'{len(D["slate"]["games"])}', "Games tonight", "2026-11-05", "warn"),
        kpi(f'{N_FLAGS}', "Flagged items", "published, non-blocking", "warn"),
        "</div>",
        callout("<strong>Headline.</strong> The model is informative and the leaderboard refuses to pay it. "
                f"Out-of-sample Brier score is <code>{X['model']['brier']:.4f}</code> against a "
                f"<code>{X['baseline']['brier']:.4f}</code> constant-home baseline "
                f"(skill <code>{BEST['skill']:+.3f}</code>, permutation p&nbsp;=&nbsp;<code>{BEST['perm_p']:.4f}</code>), "
                "but with 96 graded games, an expected-calibration error of 0.104 and no official price archive, "
                "no strategy clears the pre-registered bar for a reward.", "good"),
        callout("<strong>The largest verification result is not a model, it is a reconciliation.</strong> "
                "Summing the 121 committed final scores reproduces all 30 official win-loss records exactly. "
                "That is the check that makes the dataset trustworthy, because it compares two separately "
                "transcribed official tables rather than trusting either one.", ""),
        callout("<strong>The correlation that actually matters for pricing is not the one people assume.</strong> "
                f"Within a game, margin and total are nearly independent (r&nbsp;=&nbsp;{X['r_margin_total']:+.3f}), so "
                "spread-plus-total same-game parlays barely move when dependence is accounted for. "
                "The material dependence is inside a player's own stat line: points and rebounds correlate at "
                f"r&nbsp;=&nbsp;{next(c['r'] for c in X['correlations'] if c['pair'].startswith('Player PTS vs REB')):+.3f} "
                "on 1,951 within-player residuals, which lifts a two-leg prop combo by up to 0.05 in absolute "
                "probability versus pricing the legs as independent.", ""),
        "<h2>Originated lines for tonight</h2>",
        '<p class="meta">Two games. Spread is stated from the home team\'s perspective; a negative number means the '
        "home team is favoured. Model = ridge-shrunk opponent-adjusted margin with a 2025-26 prior, plus a "
        "separate additive totals model. No market price is used anywhere.</p>",
        table("t-tonight",
              ["Game", "Tip (ET)", "Fair spread", "Fair total", "Home ML", "Away ML", "P(home)", "Source"],
              [[f'<a href="{esc(l["game_url"])}" rel="noopener">{esc(l["matchup"])}</a>', esc(l["tip_et"]),
                num(l["fair_spread_home"], 1, signed=True), num(l["fair_total"], 1),
                odds(l["fair_ml_home"]), odds(l["fair_ml_away"]), pct(l["p_home"]),
                src(("NBA games", S["slate"]))] for l in X["lines"]],
              numcols=["Fair spread", "Fair total", "Home ML", "Away ML", "P(home)"],
              caption="Fair (zero-hold) numbers, not predictions of a market price."),
        '<p class="meta">Full pricing detail, break-even probabilities and the two-leg combinations: '
        '<a href="lines/singles.html">singles</a> · <a href="lines/parlays.html">parlays &amp; SGP</a> · '
        '<a href="lines/props.html">player props</a>.</p>',
        "<h2>What each section gives you</h2>",
        '<div class="cards">',
        '<div class="card"><h3>Official data</h3><p>Standings, 121 finals, tonight\'s slate and the 4:00 PM ET '
        'availability report — each row carries the exact official URL.</p>'
        '<a class="go" href="data/standings.html">Open official data →</a></div>',
        '<div class="card"><h3>Originated lines</h3><p>Singles, parlays and player-prop combos priced from the '
        'model, with the fair price, the probability and the dependence used.</p>'
        '<a class="go" href="lines/singles.html">Open originated lines →</a></div>',
        '<div class="card"><h3>Strategy research</h3><p>Twelve strategies, ten validation gates, measured '
        'correlations with confidence intervals, and a permutation luck test.</p>'
        '<a class="go" href="research/strategies.html">Open strategy research →</a></div>',
        '<div class="card"><h3>Competition</h3><p>A pre-registered leaderboard. Rewards are defined in advance '
        'and nobody qualifies — that is the result, not a bug.</p>'
        '<a class="go" href="competition/leaderboard.html">Open the leaderboard →</a></div>',
        f'<div class="card"><h3>Repo review</h3><p>{N_REVIEW} findings from a line-by-line review of the inherited '
        'repository, including coefficients that cannot be reproduced.</p>'
        '<a class="go" href="governance/repo-review.html">Open the repo review →</a></div>',
        f'<div class="card"><h3>Flagged for review</h3><p>{N_FLAGS} items that could not be verified or that are '
        'provisional, each with the reason and a source link.</p>'
        '<a class="go" href="governance/flagged.html">Open flagged items →</a></div>',
        "</div>",
        "<h2>The verification contract</h2>",
        "<ol>",
        "<li><strong>One source per row.</strong> Every table row links to an official NBA page or to the committed "
        "data file it was computed from. <code>verify.py</code> fails the build otherwise.</li>",
        "<li><strong>No inferred values.</strong> If an official page does not state it, the cell is blank and the "
        "item appears on the flagged page. Blank cells are never silently treated as zero.</li>",
        "<li><strong>No self-graded edge.</strong> A model comparing its line to its own line is circular, so no "
        "ROI, no expected value and no closure-line value is claimed: there is no official price archive.</li>",
        "<li><strong>Luck is measured, not asserted.</strong> Every skill number is accompanied by a paired "
        "bootstrap interval and a permutation test that shuffles the prediction-to-outcome assignment.</li>",
        "</ol>",
        '<p class="meta">Rebuild everything with <code>python3 collect_official.py &amp;&amp; python3 engine.py '
        '&amp;&amp; python3 audit.py &amp;&amp; python3 build.py &amp;&amp; python3 verify.py</code>. '
        "The engine is seeded, so the numbers are byte-identical on re-run.</p>",
    ]
    return page("index.html", "NBA line origination: verified signals, gated strategies",
                "\n".join(body), "index.html",
                "A dashboard for originating your own NBA lines from official 2026-27 data, then refusing to "
                "reward a strategy until it survives sample, calibration, dependence and luck gates.")


def page_standings():
    rows = []
    for s in D["standings"]["rows"]:
        rows.append([
            esc(s["conference"]), str(s["rank"]),
            f'<a href="{esc(s["team_url"])}" rel="noopener">{esc(s["club"])}</a>',
            f'{s["w"]}-{s["l"]}', esc(s["win_pct"]), esc(s["gb"]), esc(s["conf_record"]),
            esc(s["div_record"]), esc(s["home"]), esc(s["road"]), esc(s["last10"]), esc(s["streak"]),
            src(("NBA standings", s["source_url"])),
        ])
    checks = X["reconciliation"]
    body = [
        callout(f"<strong>Reconciled.</strong> Rebuilding each club's record from the {CORPUS['games']} committed "
                f"final scores reproduces this table for <strong>{checks['teams']}/{checks['teams']}</strong> teams "
                f"with <strong>{len(checks['mismatches'])}</strong> mismatches. Two independently produced official "
                "tables agreeing is much stronger evidence than either one alone."),
        '<p class="meta">Transcribed 2026-11-05 before that night\'s two games. GB "—" means the conference leader. '
        "Columns are exactly as the official page renders them, including record splits.</p>",
        table("t-standings",
              ["Conf", "Rank", "Team", "W-L", "WIN%", "GB", "CONF", "DIV", "HOME", "ROAD", "LAST10", "STREAK", "Source"],
              rows, numcols=["Rank", "W-L", "WIN%"],
              caption="Official 2026-27 regular-season standings, 30 rows."),
        "<h2>Reconciliation detail</h2>",
        '<p class="meta">Each row compares the record derived from committed finals with the official record. '
        "This is the check behind the claim on the dashboard.</p>",
        table("t-recon", ["Team", "Derived W", "Derived L", "Official W", "Official L", "Match", "Source"],
              [[esc(r["abbr"]), str(r["derived_w"]), str(r["derived_l"]), str(r["official_w"]),
                str(r["official_l"]), badge("pass") if r["match"] else badge("fail"),
                src(("NBA standings", r["source_url"]))] for r in checks["rows"]],
              numcols=["Derived W", "Derived L", "Official W", "Official L"], tools=False),
    ]
    return page("data/standings.html", "Official standings",
                "\n".join(body), "data/standings.html",
                "All 30 clubs, transcribed from nba.com/standings and independently reconciled against the "
                "committed game results.")


def page_results():
    rows = []
    for g in sorted(D["results"]["rows"], key=lambda x: (x["date"], x["game_id"]), reverse=True):
        rows.append([
            esc(g["date"]),
            f'<a href="{esc(g["game_url"])}" rel="noopener">{esc(g["away"])} @ {esc(g["home"])}</a>',
            f'{g["away_pts"]}–{g["home_pts"]}',
            str(g["home_pts"] - g["away_pts"]),
            str(g["home_pts"] + g["away_pts"]),
            "OT" if g["overtime"] else "",
            src(("NBA game page", g["source_url"])),
        ])
    body = [
        callout(f"<strong>{CORPUS['games']} final scores</strong>, 2026-10-20 to 2026-11-04. "
                "Rows marked <em>inherited</em> come from earlier sessions and were verified in aggregate here; "
                "rows captured on 2026-11-05 were read from the official date pages during this session.",
                ""),
        '<p class="meta">2026-11-03 was an official zero-game day (the league calendar renders "0 GAMES"). '
        "The overtime column only shows OT where the official page prints <code>Final/OT</code> or the inherited "
        "transcription marked it; see flag F16.</p>",
        table("t-results", ["Date", "Game", "Score", "Margin", "Total", "OT", "Source"], rows,
              numcols=["Margin", "Total"], search_placeholder="Filter by team, date or game id…",
              caption="Every final used by the model. Nothing outside this list is used."),
    ]
    return page("data/results.html", "Game results",
                "\n".join(body), "data/results.html",
                "The complete committed results corpus with a per-row link to the official game page.")


def page_slate():
    rows = []
    for g in D["slate"]["games"]:
        rows.append([
            esc(g["tip_et"]),
            f'<a href="{esc(g["game_url"])}" rel="noopener">{esc(g["away"])} @ {esc(g["home"])}</a>',
            f'{esc(g["away_record"])} vs {esc(g["home_record"])}',
            esc(g["game_id"]),
            src(("NBA slate", g["source_url"])),
        ])
    lead_rows = []
    for g in D["slate"]["games"]:
        for ld in g["leaders"]:
            lead_rows.append([esc(ld["player"]), esc(ld["team"]), num(ld["ppg"], 1), num(ld["rpg"], 1),
                              num(ld["apg"], 1), src(("NBA slate", g["source_url"]))])
    body = [
        '<p class="meta">Both games of the 2026-11-05 slate, with the official season leaders the league prints on '
        "each game card. Those averages are the only official player-level numbers available for tonight, which is "
        "why prop coverage is limited to these four players (flag F12).</p>",
        table("t-slate", ["Tip (ET)", "Game", "Records", "Game ID", "Source"], rows,
              caption="Tonight's slate."),
        "<h2>Official season leaders (prop anchors)</h2>",
        '<p class="meta">Published on the official game cards. These are the anchors for the prop page: they are '
        "copied, not modelled.</p>",
        table("t-leaders", ["Player", "Team", "PPG", "RPG", "APG", "Source"], lead_rows,
              numcols=["PPG", "RPG", "APG"], tools=False),
        callout("<strong>What is deliberately missing.</strong> No starting lineups, no minutes projections, no "
                "usage rates. The official pages read for this release state availability status but not lineups, "
                "so anything that would need a lineup is blank and flagged (F13)."),
    ]
    return page("data/slate.html", "Tonight's slate",
                "\n".join(body), "data/slate.html",
                "The two games of 2026-11-05, with the official season-leader averages used as prop anchors.")


def page_availability():
    rows = [[esc(r["matchup"]), esc(r["team"]), esc(r["player"]), esc(r["status"]), esc(r["reason"]),
             src(("Injury PDF", r["source_url"]))] for r in D["injuries"]["rows"]]
    nys = [[esc(r["matchup"]), esc(r["team"]), esc(r["status"]), src(("Injury PDF", r["source_url"]))]
           for r in D["injuries"]["not_yet_submitted"]]
    body = [
        callout("<strong>Point in time: 11/05/26 04:00 PM ET.</strong> Statuses change up to tip-off. The league "
                "policy quoted on the official index requires a designation by 5 p.m. local the day before and a "
                "game-day report between 11 a.m. and 1 p.m. local time, so a 4 p.m. edition is neither the first nor "
                "the last word.", "warn"),
        table("t-inj", ["Matchup", "Team", "Player", "Status", "Reason", "Source"], rows,
              caption="Thirteen availability rows for the two 2026-11-05 games."),
        "<h2>Teams that had not submitted a report</h2>",
        '<p class="meta">The same PDF shows these entries as NOT YET SUBMITTED, so their status is unknown, not '
        "clear. Blank information is recorded as blank.</p>",
        table("t-inj-nys", ["Matchup", "Team", "Status", "Source"], nys, tools=False),
        "<h2>How availability enters the model</h2>",
        "<p>The ratings on the singles page are fitted on completed games and are <em>not</em> adjusted for tonight's "
        "availability. The count of players listed Out per team is shown beside each line as context, and the "
        "adjustment is left undone rather than guessed. That is why the lines carry a note instead of a silent "
        "bump: an un-modelled injury is a known limitation, an invented adjustment is a fabricated number.</p>",
        f'<p class="meta">Policy source: <a href="{S["injury_policy"]}" rel="noopener">official.nba.com injury '
        f'report index</a>.</p>',
    ]
    return page("data/availability.html", "Player availability",
                "\n".join(body), "data/availability.html",
                "The official 4:00 PM ET injury report for tonight, transcribed row by row, plus the teams that "
                "had not submitted one.")


def page_singles():
    rows = []
    for l in X["lines"]:
        sgp = l["sgp"]
        rows.append([
            f'<a href="{esc(l["game_url"])}" rel="noopener">{esc(l["matchup"])}</a>',
            esc(l["tip_et"]),
            num(l["fair_spread_home"], 1, signed=True),
            num(l["fair_total"], 1),
            f'{num(l["fair_away_total"], 1)} / {num(l["fair_home_total"], 1)}',
            odds(l["fair_ml_home"]), odds(l["fair_ml_away"]),
            pct(l["p_home"]),
            num(l["home_rating"], 2, signed=True), num(l["away_rating"], 2, signed=True),
            f'{l["out_players_home"]} / {l["out_players_away"]}',
            src(("NBA slate", l["source_url"])),
        ])
    be_rows = []
    for l in X["lines"]:
        s = l["sgp"]
        be_rows.append([
            esc(l["matchup"]),
            pct(s["p_home_ml"]), pct(s["p_home_cover_3_5"]), pct(s["p_over_fair"]), pct(s["p_under_fair"]),
            num(100 * abs(l["fair_spread_home"]) / 2 * 0 + 0, 0) if False else num(l["fair_total"], 1),
            src(("NBA slate", l["source_url"])),
        ])
    body = [
        callout("<strong>These are fair prices, not edges.</strong> A fair price is the number at which the model "
                "believes a bet is worth exactly zero. Turning it into an edge requires a market price to compare "
                "against, and no official price archive exists in this repository (flag F01, gate G9).", "warn"),
        "<h2>Spread, total and moneyline</h2>",
        table("t-lines", ["Game", "Tip (ET)", "Fair spread", "Fair total", "Fair team totals (A/H)", "Home ML",
                          "Away ML", "P(home)", "Home rating", "Away rating", "Out (H/A)", "Source"], rows,
              numcols=["Fair spread", "Fair total", "Home ML", "Away ML", "P(home)", "Home rating", "Away rating"],
              caption="Home spread sign convention: negative = home favoured. Ratings are points per game versus a "
                      "league-average opponent on a neutral floor."),
        "<h2>Break-even probabilities</h2>",
        '<p class="meta">The probability that makes a bet at that price break even. Read this as the model\'s '
        "opinion of the true chance, not as a recommendation. Over/under at the fair total is exactly 50% by "
        "construction — that is what makes it the fair total.</p>",
        table("t-be", ["Game", "P(home ML)", "P(home -3.5)", "P(over fair total)", "P(under fair total)",
                       "Fair total", "Source"], be_rows,
              numcols=["P(home ML)", "P(home -3.5)", "P(over fair total)", "P(under fair total)", "Fair total"],
              tools=False),
        "<h2>How each number is built</h2>",
        "<pre>margin_home = rating_home - rating_away + home_court\n"
        "rating_i    = (sum_targets + lambda * prior_2025_26_i) / (games_i + lambda)      lambda = 12\n"
        "            where target = opponent_rating + margin  (or opponent_rating - margin when away)\n"
        "            iterated to convergence, then centred so the league mean rating is 0\n"
        "total       = base + offset_home + offset_away                                   lambda = 12\n"
        "P(home)     = Phi(margin_home / sigma_margin)                     sigma_margin = "
        f"{X['sigma']['margin']:.3f}\n"
        "fair ML     = -100p/(1-p) if p >= 0.5 else +100(1-p)/p\n"
        "home total  = (mu_total + mu_margin)/2      away total = (mu_total - mu_margin)/2</pre>",
        "<h2>Out-of-sample accuracy of these lines</h2>",
        '<div class="kpis">',
        kpi(num(X["strategies"][1]["mae_margin"], 2), "Spread MAE", "points, vs "
            f'{num(X["strategies"][1]["baseline_mae_margin"], 2)} constant baseline'),
        kpi(num(X["strategies"][2]["mae_total"], 2), "Total MAE", "points, vs "
            f'{num(X["strategies"][2]["baseline_mae_total"], 2)} constant baseline'),
        kpi(num(X["fit"]["home_court"], 2), "Home court", "points (provisional, flag F04)", "warn"),
        kpi(num(CORPUS["league_mean_total"], 1), "League mean total", "2026-27 to date"),
        "</div>",
        callout(f"<strong>Read the totals result honestly.</strong> The totals model scores a skill of "
                f"{X['strategies'][2]['skill']:+.4f} against a constant-league-average baseline, and its bootstrap "
                f"interval ({X['strategies'][2]['boot']['lo']:+.3f} to {X['strategies'][2]['boot']['hi']:+.3f}) "
                "contains zero. On 96 games there is no evidence it beats just using the league average. The "
                "moneyline model is the one with a signal that survives its interval.", "warn"),
        f'<p class="meta">Full per-game line-versus-actual table: <a href="{REL}/research/backtest.html">walk-forward '
        "&amp; luck</a>.</p>",
    ]
    return page("lines/singles.html", "Singles: fair spread, total and moneyline",
                "\n".join(body), "lines/singles.html",
                "Tonight's two games priced from the rating and totals models, with the break-even probability "
                "behind every number.")


def page_parlays():
    ton = []
    for l in X["lines"]:
        s = l["sgp"]
        for label, joint, indep in (
                ("Home ML + over fair total", s["joint_ml_over"], s["indep_ml_over"]),
                ("Home -3.5 + under fair total", s["joint_cover_under"], s["indep_cover_under"])):
            ton.append([
                f'<a href="{esc(l["game_url"])}" rel="noopener">{esc(l["matchup"])}</a>',
                esc(label), pct(joint), num(1.0 / joint if joint else None, 3),
                pct(indep), f'{joint - indep:+.4f}' if joint is not None else blank(),
                src(("NBA slate", l["source_url"])),
            ])
    graded = []
    for p in X["parlays"]:
        graded.append([
            esc(p["id"]), esc(p["name"]), str(p["n"]), num(p["model_metric"], 4),
            num(p["independence_brier"], 4), num(p["realised_rate"], 3), num(p["skill"], 4, signed=True),
            esc(p["rho_used"]),
            badge("pass") if (p["skill"] or 0) > 0 else badge("fail"),
            src(("Derived from committed finals", S["repo"] + "/blob/main/nba-lines/data/derived.json")),
        ])
    body = [
        callout("<strong>Parlay arithmetic that matters.</strong> A two-leg parlay's fair price is the joint "
                "probability of both legs, and the joint is <em>not</em> the product unless the legs are "
                "independent. For legs in different games independence is an assumption (flag F09). For legs in the "
                "same game it is false, and the size of the error is measurable.", ""),
        "<h2>Tonight: same-game combinations</h2>",
        '<p class="meta">Joint probabilities from a bivariate normal with the measured margin/total correlation '
        f'(r = {X["r_margin_total"]:+.4f}). Note how small the dependence effect is for team markets: that '
        "measurement is the point.</p>",
        table("t-sgp", ["Game", "Legs", "Fair joint", "Fair decimal", "If priced independent", "Dependence effect",
                        "Source"], ton,
              numcols=["Fair joint", "Fair decimal", "If priced independent", "Dependence effect"],
              caption="Two-leg same-game parlays at the model's own fair lines."),
        "<h2>Graded parlay strategies</h2>",
        '<p class="meta">Each construct is graded on how well its joint probability predicted the realised joint '
        "outcome, across every graded game. The baseline is the unconditional realised joint rate — a model that "
        "cannot beat the base rate has added nothing.</p>",
        table("t-parlay-grade", ["ID", "Construct", "n", "Joint Brier", "Independence Brier", "Realised rate",
                                 "Skill", "Dependence used", "Verdict", "Source"], graded,
              numcols=["n", "Joint Brier", "Independence Brier", "Realised rate", "Skill"],
              caption="S06 cross-game, S07/S08 same-game."),
        callout(f"<strong>The dependence adjustment is real but small for team markets.</strong> With "
                f"r&nbsp;=&nbsp;{X['r_margin_total']:+.3f}, switching from independence to the measured joint moves "
                f"the Brier score by {X['parlays'][2]['dependency_gain']:+.4f} at most. Pricing a spread-plus-total "
                "SGP as independent is therefore a rounding error, not a business model. Player-level dependence is "
                "a different story — see the props page, where two-leg combos move by up to 0.05 in probability.",
                "warn"),
        callout(f"<strong>Cross-game parlays get worse, not better.</strong> S06's joint Brier is higher than the "
                f"base rate (skill {next(p['skill'] for p in X['parlays'] if p['id'] == 'S06'):+.4f}): chaining two "
                "unrelated legs compounds error faster than it compounds edge, and no cross-game dependence was "
                "verified to exploit.", "bad"),
        "<h2>Rule of construction</h2>",
        "<pre>fair_decimal = 1 / P(both legs)\n"
        "P(both)       = P(leg1) * P(leg2)                     only if independent\n"
        "P(both)       = bivariate_normal(mu1, s1, s2, rho)    what this page uses\n"
        "fair_american = -100p/(1-p) if p >= 0.5 else +100(1-p)/p</pre>",
    ]
    return page("lines/parlays.html", "Parlays and same-game combinations",
                "\n".join(body), "lines/parlays.html",
                "Joint pricing with measured dependence instead of the independence shortcut, plus three graded "
                "parlay constructs.")


def page_props():
    rows = [[esc(p["player"]), esc(p["team"]), esc(p["stat"]), num(p["official_mean"], 1), num(p["line"], 1),
             pct(p["p_over"]), num(p["resid_sd"], 2) if p["resid_sd"] else blank(),
             src(("NBA slate (official average)", p["official_url"]))] for p in X["props"]]
    combos = [[esc(c["player"]), esc(c["leg_a"]), esc(c["leg_b"]), num(c["rho"], 3), pct(c["joint"]),
               pct(c["indep"]), f'{c["joint"] - c["indep"]:+.4f}', num(1.0 / c["joint"], 3),
               src(("Correlation from committed logs",
                    S["repo"] + "/blob/main/nba-lines/data/derived.json"))] for c in X["prop_combos"]]
    body = [
        callout("<strong>The anchor is official; the volatility is not.</strong> Each player's mean is copied from "
                "the official game card. The probability around it uses a pooled within-player residual standard "
                "deviation from partner-sourced game logs, because the four players on tonight's slate have only "
                "4-6 logged games each (flags F05, F06, F07).", "warn"),
        "<h2>Originated prop lines</h2>",
        '<p class="meta">Line = the official season average rounded to the nearest half point, which is how prop '
        "boards are priced. P(over) = 1 - Phi((line - mean)/sd) using the pooled residual sd for that stat.</p>",
        table("t-props", ["Player", "Team", "Stat", "Official average", "Originated line", "P(over)", "Residual sd",
                          "Source"], rows,
              numcols=["Official average", "Originated line", "P(over)", "Residual sd"],
              caption="Twelve props, four players, three stats."),
        "<h2>Prop combinations and the dependence that changes the price</h2>",
        '<p class="meta">These are the same player\'s stats in the same game. Positive within-player correlation '
        "means the legs co-occur more often than independence implies, so an independent pricer understates the "
        "joint probability.</p>",
        table("t-combos", ["Player", "Leg A", "Leg B", "r", "Joint", "If independent", "Effect", "Fair decimal",
                           "Source"], combos,
              numcols=["r", "Joint", "If independent", "Effect", "Fair decimal"],
              caption="Two-leg prop combos at the originated lines."),
        callout("<strong>Why 0.26 matters.</strong> Points and rebounds correlate at r&nbsp;=&nbsp;0.268 on 1,951 "
                "within-player residuals (95% CI 0.226 to 0.309, BH q ≈ 0). That is the single most useful number "
                "on this page for pricing: a points-plus-rebounds combo for a heavy-minutes starter is "
                "systematically more likely than the product of its legs, by roughly 0.03 to 0.05 in absolute "
                "probability.", "good"),
        callout("<strong>What would change these numbers, and what would not.</strong> Player-specific variance, "
                "minutes projections and opponent defensive context would all change them. A different book's "
                "line would not: these are model outputs, not quotes, and no official market price is available to "
                "compare against.", ""),
        "<h2>Formulas</h2>",
        "<pre>line      = round(mean * 2) / 2                      mean = official season average\n"
        "P(over)   = 1 - Phi((line - mean) / sd)               sd = pooled within-player residual sd\n"
        "P(A and B)= bivariate_normal(z_a, z_b; rho)           z = probit(1 - P(over))</pre>",
        '<p class="meta">Combo dependence uses the pooled within-player correlation for the pair, not a '
        "player-specific estimate, because per-player samples are too small. Flagged as F05/F07.</p>",
    ]
    return page("lines/props.html", "Player props and prop combos",
                "\n".join(body), "lines/props.html",
                "Twelve originated prop lines anchored on official season averages, and the measured dependence "
                "that reprices every two-leg combo.")


def page_strategies():
    cat = {
        "S01": ("Single", "Moneyline from the rating model; probability from the normal margin model."),
        "S02": ("Single", "Point-estimate spread from the rating model; graded on absolute margin error."),
        "S03": ("Single", "Additive team-totals model; graded on absolute total error."),
        "S04": ("Single", "Rating model plus a 1.2-point penalty for a team on a back-to-back."),
        "S05": ("Single", "Rating model plus a mild overlay toward the last-10-game form."),
        "S06": ("Parlay", "Two legs in different games; joint price uses independence."),
        "S07": ("Parlay", "Same game: home moneyline plus over the fair total, priced with measured dependence."),
        "S08": ("Parlay", "Same game: home -3.5 plus under the fair total, priced with measured dependence."),
        "S09": ("Prop", "Points prop from the official season average with an empirical residual band."),
        "S10": ("Prop", "Points+rebounds+assists combo using the measured within-player correlations."),
        "S11": ("Prop", "Two teammates stacked, using the measured teammate correlation."),
        "S12": ("Prop", "Prop re-anchored for opponent pace and defence. Not implemented: no official pace feed."),
    }
    graded = {s["id"]: s for s in X["strategies"]}
    graded.update({p["id"]: p for p in X["parlays"]})
    board = {b["id"]: b for b in X["leaderboard"]}
    rows = []
    for sid in sorted(cat):
        family, definition = cat[sid]
        g = graded.get(sid)
        b = board.get(sid, {})
        if g:
            status = badge("pass") + " graded"
            result = (f'skill {g["skill"]:+.4f}' if g.get("skill") is not None else blank())
            n = str(g.get("n", ""))
        else:
            status = badge("not implemented" if sid == "S12" else "needs review")
            result = blank()
            n = blank()
        rows.append([esc(sid), esc(family), esc(definition), n, result, status,
                     esc(b.get("note", "")), src(("Derived", S["repo"] + "/blob/main/nba-lines/data/derived.json"))])
    body = [
        callout("<strong>Twelve strategies, eight gradeable.</strong> The four prop strategies cannot be graded "
                "yet: grading requires settled outcomes at the originated line, and the logs needed for that are "
                "three days stale and partner-sourced. They are listed, specified and explicitly ungraded rather "
                "than quietly dropped.", "warn"),
        table("t-strategies", ["ID", "Family", "Definition", "n", "Result", "Status", "Why not eligible", "Source"],
              rows, numcols=["n"],
              caption="The full catalog. Definitions were fixed before the backtest ran."),
        "<h2>Families and what distinguishes them</h2>",
        "<h3>Singles</h3>",
        "<p>S01–S05 all price off the same rating backbone but differ in the signal layered on top: none (S01, S02), "
        "an independent totals model (S03), rest (S04) or recent form (S05). Because they share a backbone, their "
        "results are correlated, which is why the leaderboard's separation between them is not treated as "
        "meaningful. The honest reading is that the backbone carries the signal and the overlays are "
        "indistinguishable on 96 games.</p>",
        "<h3>Parlays</h3>",
        "<p>S06–S08 exist to test a specific claim: that dependence matters. They are graded on joint-probability "
        "accuracy, not on a bet record, because a bet record would require market prices that do not exist here.</p>",
        "<h3>Player props</h3>",
        "<p>S09–S12 are the strategy class most people actually want. They need three things this repository does "
        "not have from an official source: per-player game logs at usable volume, minutes projections, and an "
        "official pace/defence table. Each is specified; each is blocked; all four are flagged.</p>",
        callout("<strong>Why no strategy is called a winner.</strong> A positive skill score is not a validated "
                "strategy. The gate list requires sample size, a bootstrap interval excluding zero, a permutation "
                "p below 0.01, calibration within tolerance, multiple-testing control and a price archive. Three of "
                "those fail, so the correct verdict is 'promising backbone, unvalidated strategy'."),
    ]
    return page("research/strategies.html", "Strategy catalog",
                "\n".join(body), "research/strategies.html",
                "Twelve pre-registered strategies across singles, parlays and player props, with their grading "
                "status and the exact reason each is or is not eligible.")


def page_correlations():
    rows = []
    for c in X["correlations"]:
        tier = ("Official league finals" if c["pair"].startswith(("Margin", "Home points", "|Margin|", "Same-day"))
                else "Partner game logs (flagged)")
        url = S["g1004"] if tier.startswith("Official") else S["repo"] + "/blob/main/data/player_gamelogs.json"
        rows.append([esc(c["pair"]), esc(c["detail"]), str(c["n"]), num(c["r"], 4),
                     f'{num(c["lo"], 3)} to {num(c["hi"], 3)}' if c["lo"] is not None else blank(),
                     f'{c["p"]:.2e}' if c["p"] is not None else blank(),
                     f'{c["q"]:.2e}' if c["q"] is not None else blank(),
                     esc(tier), src(("Source", url))])
    body = [
        callout("<strong>Every coefficient here is computed in this session from files in this repository.</strong> "
                "Ten tests, controlled with Benjamini–Hochberg at q < 0.10 across the whole family, including the "
                "five strategy luck tests. That is stricter than reporting the smallest p-value and calling it a "
                "discovery — which is exactly what the repository's earlier correlation file did (finding R02).",
                "good"),
        table("t-corr", ["Pair", "Detail", "n", "r", "95% CI", "p", "BH q", "Data tier", "Source"], rows,
              numcols=["n", "r", "95% CI", "p", "BH q"],
              caption="Correlation values with confidence intervals and false-discovery control."),
        "<h2>Reading these numbers</h2>",
        "<h3>Margin versus total: the null result that saves money</h3>",
        f"<p>r&nbsp;=&nbsp;{X['correlations'][0]['r']:+.4f} (95% CI {X['correlations'][0]['lo']:+.3f} to "
        f"{X['correlations'][0]['hi']:+.3f}). Margin and total are effectively independent within a game over these "
        "121 finals. Practical consequence: a spread-plus-total same-game parlay can be priced by multiplication "
        "with negligible error, and any model that claims a large dependence benefit from that pair is wrong.</p>",
        "<h3>Player stats: the dependence that does matter</h3>",
        "<p>Within-player residuals correlate at roughly 0.15–0.27 across the three scoring stats. Because these "
        "are demeaned per player, the coefficients are not contaminated by the fact that good players are good at "
        "everything; they measure whether a player's <em>deviation</em> in one stat travels with his deviation in "
        "another in the same game. It does, mildly — minutes and game script move all three together.</p>",
        "<h3>Teammates: the one that does not clear the bar</h3>",
        " <p>The teammate points correlation is negative, which is what a usage trade-off should look like, but "
        "p&nbsp;=&nbsp;0.060 and q&nbsp;=&nbsp;0.075. It is not significant, so the teammate-stack strategy (S11) "
        "stays ungraded and no stack line is published (flag F08).</p>",
        "<h3>Cross-game: an assumption, labelled as one</h3>",
        "<p>Consecutive same-day totals correlate at a level that neither confirms nor rejects independence. The "
        "cross-game parlay therefore uses independence, and flag F09 records that this is an assumption rather than "
        "a verified fact.</p>",
        "<h2>Method</h2>",
        "<pre>r        = Pearson product-moment correlation\n"
        "95% CI   = Fisher z transform: tanh(atanh(r) +/- 1.96/sqrt(n-3))\n"
        "p        = two-sided Student t with df = n - 2\n"
        "q        = Benjamini-Hochberg step-up across the whole test family</pre>",
        f'<p class="meta">Method sources: <a href="{S["bh"]}" rel="noopener">Benjamini &amp; Hochberg (1995)</a>, '
        f'<a href="{S["nist"]}" rel="noopener">NIST/SEMATECH handbook</a>.</p>',
    ]
    return page("research/correlations.html", "Correlation values",
                "\n".join(body), "research/correlations.html",
                "Ten measured correlations with confidence intervals and false-discovery control — the inputs that "
                "decide how every parlay and prop combo is priced.")


def page_gates():
    rows = [[esc(g["id"]), esc(g["name"]), esc(g["rule"]), esc(g["value"]) if g["value"] else blank(),
             badge(g["status"]), src(("Method", S["sk_cv"] if g["id"] in ("G1", "G4") else
                                      (S["sk_cal"] if g["id"] == "G6" else S["repo"])))]
            for g in X["gates"]]
    counts = {}
    for g in X["gates"]:
        counts[g["status"]] = counts.get(g["status"], 0) + 1
    body = [
        '<div class="kpis">',
        kpi(str(counts.get("pass", 0)), "Gates passed", "of 10", "good"),
        kpi(str(counts.get("fail", 0)), "Gates failed", "of 10", "bad"),
        kpi(str(counts.get("pending", 0)), "Gates pending", "of 10", "warn"),
        kpi("0", "Rewards paid", "by policy", "bad"),
        "</div>",
        callout("<strong>Pre-registered before the backtest.</strong> The gate list and its thresholds were written "
                "into the repository in the same commit series that produced the engine, and the engine cannot "
                "change a threshold. A gate that can be relaxed after seeing the result is not a gate.", ""),
        table("t-gates", ["ID", "Gate", "Rule", "Measured value", "Status", "Method"], rows,
              caption="Ten gates. A strategy must pass all of them to be reward-eligible."),
        "<h2>What each gate is for</h2>",
        "<h3>G3 — sample sufficiency</h3>",
        f"<p>{X['model']['n']} scored games against a 300-game requirement. At a true skill difference of 0.05 in "
        "Brier score, 96 games cannot distinguish a good model from a lucky one; the standard error of the skill "
        "estimate alone is around 0.07. This single gate is why the leaderboard pays nobody.</p>",
        "<h3>G4 — out-of-sample positive skill</h3>",
        " <p>A paired bootstrap over games, not a single point estimate. The interval must exclude zero. S01, S04 "
        "and S05 clear it; S02 and S03 do not. The bootstrap's percentiles are computed from 4,000 resamples of the "
        "graded set.</p>",
        "<h3>G5 — luck test</h3>",
        " <p>The observed skill is compared with the distribution of skill obtained when the prediction-to-outcome "
        "pairing is shuffled 4,000 times. This is the closest thing to a direct measurement of 'how often would "
        "noise look this good'.</p>",
        "<h3>G6 — calibration</h3>",
        " <p>Five equal-count bins, expected calibration error, and a reliability slope. A model can rank games "
        "correctly and still be badly calibrated, and a mis-calibrated probability is unusable for pricing "
        "regardless of its discrimination. This gate fails: ECE 0.104.</p>",
        "<h3>G9 — market price evidence</h3>",
        " <p>The hard one. Recognising an edge requires a price someone else will take the other side of. Without a "
        "price archive there is no edge to measure, only a model opinion. No official price source exists in this "
        "repository, so this gate cannot pass, no matter how good the model gets.</p>",
        f'<p class="meta">Method sources: <a href="{S["sk_cv"]}" rel="noopener">scikit-learn cross-validation</a>, '
        f'<a href="{S["sk_cal"]}" rel="noopener">probability calibration</a>, '
        f'<a href="{S["nist"]}" rel="noopener">NIST hypothesis-testing handbook</a>.</p>',
    ]
    return page("research/gates.html", "Validation gates",
                "\n".join(body), "research/gates.html",
                "Ten pre-registered gates, the measured value against each, and exactly which three failures stop "
                "every reward.")


def page_backtest():
    metrics = [[esc(s["id"]), esc(s["name"]), str(s["n"]), num(s["brier"], 4), num(s["baseline_brier"], 4),
                num(s["mae_margin"], 2), num(s["baseline_mae_margin"], 2), num(s["mae_total"], 2),
                num(s["baseline_mae_total"], 2), num(s["skill"], 4, signed=True),
                f'{s["boot"]["lo"]:+.3f} to {s["boot"]["hi"]:+.3f}' if s["boot"] else blank(),
                f'{s["perm_p"]:.4f}' if s["perm_p"] is not None else blank(),
                num(s["ece"], 4) if s["ece"] is not None else blank(),
                src(("Committed finals", S["repo"] + "/blob/main/nba-lines/data/derived.json"))]
               for s in X["strategies"]]
    cal = X["strategies"][0]["calibration"]
    calrows = [[str(b["bin"]), str(b["n"]), num(b["mean_pred"], 4), num(b["observed"], 4),
                f'{b["gap"]:+.4f}', src(("Computed", S["repo"] + "/blob/main/nba-lines/data/derived.json"))]
               for b in cal["bins"]]
    acc = [[esc(r["date"]), f'<a href="{esc(r["game_url"])}" rel="noopener">{esc(r["matchup"])}</a>',
            num(r["fair_spread"], 1, signed=True), str(r["actual_margin"]),
            num(r["spread_error"], 1), num(r["fair_total"], 1), str(r["actual_total"]),
            num(r["total_error"], 1), src(("NBA game", r["source_url"]))] for r in X["line_accuracy"]]
    body = [
        "<h2>Walk-forward scoring</h2>",
        callout("<strong>Strictly forward-chaining.</strong> Each prediction is made from games strictly earlier in "
                f"the file, with the first {CORPUS['warmup_games']} games used only to warm the model. The "
                "2025-26 prior is previous-season information, which is legitimate at the first tip. Nothing from a "
                "game's own result enters its own prediction.", "good"),
        '<div class="kpis">',
        kpi(num(X["model"]["brier"], 4), "Model Brier", f'{X["model"]["n"]} graded games'),
        kpi(num(X["baseline"]["brier"], 4), "Baseline Brier", "home win rate, fitted pre-tip"),
        kpi(num(X["strategies"][0]["skill"], 4, signed=True), "Skill (S01)", "1 - model/baseline", "good"),
        kpi(num(X["model"]["logloss"], 4), "Log loss", f'baseline {X["baseline"]["logloss"]:.4f}'),
        "</div>",
        table("t-metrics", ["ID", "Strategy", "n", "Brier", "Base Brier", "MAE margin", "Base MAE margin",
                            "MAE total", "Base MAE total", "Skill", "Bootstrap 95% CI", "Permutation p", "ECE",
                            "Source"], metrics,
              numcols=["n", "Brier", "Base Brier", "MAE margin", "Base MAE margin", "MAE total",
                       "Base MAE total", "Skill", "Bootstrap 95% CI", "Permutation p", "ECE"],
              caption="Every graded strategy with the metric it is actually graded on."),
        "<h2>The luck test, in plain terms</h2>",
        "<p>Shuffling the pairing between a prediction and the game it was made for destroys any real forecasting "
        "relationship while keeping both distributions intact. Repeat 4,000 times and you get the range of skill "
        "scores that pure chance produces with these exact predictions. The observed score is then just a "
        "percentile in that distribution.</p>",
        f"<p>The strongest result, {BEST['id']}, sits at p&nbsp;=&nbsp;{BEST['perm_p']:.4f}: fewer than 1 shuffle in "
        "3,000 matched it. That is genuine evidence of forecasting information in team ratings — the least "
        "surprising true thing in sports analytics. It is <em>not</em> evidence of a betting edge, because skill at "
        "predicting outcomes is not the same as skill at beating a price.</p>",
        "<h2>Calibration of the moneyline model</h2>",
        '<p class="meta">Five equal-count bins of predicted home-win probability versus observed frequency. '
        "The slope is close to 1 and the bins are close, but ECE fails the 0.05 gate at "
        f'{cal["ece"]:.4f}.</p>',
        table("t-cal", ["Bin", "n", "Mean predicted", "Observed", "Gap", "Source"], calrows,
              numcols=["n", "Mean predicted", "Observed", "Gap"], tools=False),
        "<h2>Line-versus-actual, every graded game</h2>",
        table("t-acc", ["Date", "Game", "Fair spread", "Actual margin", "Spread error", "Fair total",
                        "Actual total", "Total error", "Source"], acc,
              numcols=["Fair spread", "Actual margin", "Spread error", "Fair total", "Actual total", "Total error"],
              search_placeholder="Filter by team or date…",
              caption="The per-game evidence behind the MAE figures above."),
        "<h2>Method</h2>",
        "<pre>skill        = 1 - metric_model / metric_baseline       baseline fitted on pre-tip history only\n"
        "bootstrap    = paired resample of games, 4,000 draws, percentile interval\n"
        "permutation  = shuffle prediction-to-outcome pairing, 4,000 draws, (k+1)/(B+1)\n"
        "ECE          = sum_b |observed_b - predicted_b| * n_b / n          5 equal-count bins\n"
        "seed         = " + str(X["seed"]) + "</pre>",
        f'<p class="meta">Methods: <a href="{S["sk_cv"]}" rel="noopener">scikit-learn time-series validation</a>, '
        f'<a href="{S["sk_cal"]}" rel="noopener">calibration</a>, <a href="{S["nist"]}" rel="noopener">NIST</a>. '
        "The whole run is seeded and byte-reproducible.</p>",
    ]
    return page("research/backtest.html", "Walk-forward backtest and luck removal",
                "\n".join(body), "research/backtest.html",
                "Ninety-six out-of-sample predictions, a paired bootstrap, a 4,000-draw permutation test, and the "
                "per-game line errors behind all of it.")


def page_leaderboard():
    rewards = [{"rank": 1, "points": 40}, {"rank": 2, "points": 25}, {"rank": 3, "points": 15}]
    rows = []
    for b in X["leaderboard"]:
        rows.append([
            str(b["rank"]) if b["rank"] else blank(),
            esc(b["id"]), esc(b["name"]), esc(b["kind"]), str(b["n"]) if b["n"] else blank(),
            num(b["skill"], 4, signed=True) if b["skill"] is not None else blank(),
            f'{b["ci_low"]:+.3f}' if b["ci_low"] is not None else blank(),
            f'{b["p_perm"]:.4f}' if b["p_perm"] is not None else blank(),
            badge("pass") if b["eligible"] else badge("fail"),
            str(b["reward"]),
            esc(b["note"]),
            src(("Derived", S["repo"] + "/blob/main/nba-lines/data/derived.json"))])
    body = [
        '<div class="kpis">',
        kpi("0", "Rewards paid", "out of 80 points on offer", "bad"),
        kpi(str(len([b for b in X["leaderboard"] if b["skill"] is not None])), "Graded entries",
            "eight constructs"),
        kpi("300", "Required sample", f'{X["model"]["n"]} available', "bad"),
        kpi("0.01", "Required luck p", f'best is {BEST["perm_p"]:.4f}', "good"),
        "</div>",
        callout("<strong>This is what a leaderboard is supposed to look like when nobody has earned anything.</strong> "
                "Points are defined in advance (40/25/15), eligibility requires every gate, and the answer this "
                "week is that no entry qualifies. Publishing that is more useful than publishing a winner, because "
                "a leaderboard that always pays someone is measuring the calendar, not skill.",
                "bad"),
        table("t-board", ["Rank", "ID", "Strategy", "Family", "n", "Skill", "CI low", "Perm p", "Eligible",
                          "Reward", "Why not eligible", "Source"], rows,
              numcols=["Rank", "n", "Skill", "CI low", "Perm p", "Reward"],
              caption="Pre-registered leaderboard, 2026-11-05."),
        "<h2>The rules, fixed before the first result</h2>",
        "<ol>",
        "<li><strong>Entry.</strong> A strategy is a named, fully specified rule committed before it is graded. "
        "Changing a parameter creates a new entry and the old one stays on the board.</li>",
        "<li><strong>Grading.</strong> Only out-of-sample predictions count. A strategy is graded on the metric "
        "appropriate to it: Brier for probabilities, MAE for point estimates, joint Brier for parlays.</li>",
        "<li><strong>Eligibility.</strong> All ten gates must pass simultaneously: n ≥ 300, bootstrap lower bound "
        "&gt; 0, permutation p &lt; 0.01, calibration in tolerance, multiple-testing control, and a price archive "
        "for G9.</li>",
        "<li><strong>Rewards.</strong> 40/25/15 points for ranks one to three. No money is funded, and a strategy "
        "that fails a gate forfeits its rank to nobody rather than to the next entry — dilution on failure would "
        "reward the absence of scrutiny.</li>",
        "<li><strong>Correctness beats novelty.</strong> A strategy that reproduces a known result, honestly "
        "measured, outranks one that reports a larger number it cannot reproduce.</li>",
        "</ol>",
        "<h2>Why the ranking is not the story</h2>",
        "<p>S04, S05 and S01 finish within 0.005 of each other and share a backbone. Their ordering is noise; the "
        "bootstrap intervals overlap almost completely. The useful statement is 'the rating backbone clears the "
        "luck test', not 'rest adjustments are the best strategy'. Ranking overlapping intervals and calling it a "
        "competition would be the exact failure mode this project is trying to avoid.</p>",
        callout("<strong>What would change the board.</strong> A licence for historical closing prices would make "
                "G9 passable, and about 200 more graded games would make G3 passable. Both are concrete and "
                "scheduled, which is why the leaderboard is a plan rather than a verdict.", ""),
    ]
    return page("competition/leaderboard.html", "Leaderboard",
                "\n".join(body), "competition/leaderboard.html",
                "Twelve entries, pre-registered reward tiers, and zero payouts — with the exact gate that blocks "
                "each strategy.")


def page_methodology():
    body = [
        "<h2>Requirements and how each was met</h2>",
        table("t-req", ["#", "Requirement", "Delivered as", "Status", "Source"], [
            ["1", "Collect and organise a full set of NBA requirements",
             "This page plus the source register; every requirement traceable to an official page.",
             badge("pass"), src(("NBA stats help", S["faq"]))],
            ["2", "Research and develop strategies for generating useful signals",
             "Twelve strategies in three families, each specified and eight graded.",
             badge("pass"), src(("Strategy catalog", "../research/strategies.html"))],
            ["3", "Originate own NBA lines",
             "Fair spread, total, team totals, moneyline and 12 prop lines for tonight.",
             badge("pass"), src(("Singles", "../lines/singles.html"))],
            ["4", "Single bets, parlays, player-prop combos",
             "Three pages: singles, parlays/SGP, props/combos.",
             badge("pass"), src(("Parlays", "../lines/parlays.html"))],
            ["5", "Every strategy must pass validation gates",
             "Ten pre-registered gates; a strategy is eligible only if all pass.",
             badge("pass"), src(("Gates", "../research/gates.html"))],
            ["6", "Determine correlation values",
             "Ten coefficients with CIs, p-values and BH q-values, computed in-repo.",
             badge("pass"), src(("Correlations", "../research/correlations.html"))],
            ["7", "Remove luck from the equation",
             "Walk-forward scoring, paired bootstrap, 4,000-draw permutation test, FDR control.",
             badge("pass"), src(("Backtest", "../research/backtest.html"))],
            ["8", "Selectively skill-based strategies",
             "Skill separated from luck explicitly; only the rating backbone survives the luck test.",
             badge("pass"), src(("Leaderboard", "../competition/leaderboard.html"))],
            ["9", "Leaderboard competition with rewards",
             "Points pre-registered at 40/25/15 with an all-gates requirement; zero awarded this week.",
             badge("pass"), src(("Leaderboard", "../competition/leaderboard.html"))],
            ["10", "Executive summary",
             "Repository EXECUTIVE_SUMMARY.md plus the dashboard overview.",
             badge("pass"), src(("Summary", S["repo"] + "/blob/main/EXECUTIVE_SUMMARY.md"))],
            ["11", "Official-source verification, blanks flagged",
             f"One link per table row enforced by verify.py; {N_FLAGS} flagged items published.",
             badge("pass"), src(("Flagged", "flagged.html"))],
            ["12", "Live site with category subpages",
             "17 pages under /nba-lines/site/ plus a root landing page on GitHub Pages.",
             badge("pass"), src(("Pages API", S["gh_pages"]))],
            ["13", "Official historical prices for edge measurement",
             "Not delivered: no official price archive is available. Blocks G9.",
             badge("fail"), src(("Flagged F01", "flagged.html"))],
            ["14", "Player-level official logs at usable volume",
             "Not delivered: the league forbids downloading its stats. Props use flagged partner data.",
             badge("fail"), src(("NBA Stats FAQ", S["faq"]))],
        ], caption="Requirement traceability. Two requirements cannot be met from official sources and are recorded as failures rather than glossed."),
        "<h2>Data policy</h2>",
        "<p>The league's FAQ states that its statistics \"are not available for download for either academic or "
        "personal use\". This release therefore contains no bulk extract of league data. What it contains is 30 "
        "standings rows, 121 final scores, 2 slate entries and 13 availability rows, each read from a publicly "
        "displayed page and stored with the exact URL. The one large third-party extract already in the repository "
        "(47 MB of partner box scores) predates this session and is flagged under R05 rather than extended.</p>",
        "<h2>Reproduce</h2>",
        "<pre>cd nba-lines\npython3 collect_official.py   # transcription register -> data/*.json\n"
        "python3 engine.py             # model, correlations, backtest, gates, leaderboard\n"
        "python3 audit.py              # repo review + flagged registers\n"
        "python3 build.py              # 17 static pages + root landing page\n"
        "python3 verify.py             # source links, internal links, blanks, determinism\n"
        "python3 -m unittest discover -s tests -v</pre>",
        "<p>Standard library only, no network access, seeded randomness "
        f"(seed = <code>{X['seed']}</code>), so two runs produce identical output. A CI workflow re-runs the whole "
        "chain and fails on any diff.</p>",
        "<h2>Model, in one place</h2>",
        "<pre># ratings (points per game vs a league-average opponent)\n"
        "target_home = margin + r_away - H          target_away = r_home + H - margin\n"
        "r_i = (sum(targets_i) + 12 * prior_i) / (games_i + 12)       iterated 400x, then centred\n"
        "H   = mean(margin - (r_home - r_away))                        re-estimated each iteration\n\n"
        "# totals (additive, centred, shrunk toward the 2025-26 tendency)\n"
        "total = base + off_home + off_away        off_i = (sum(totals - base - off_opp) + 12*prior_i)/(games_i+12)\n\n"
        "# probabilities\n"
        "P(home) = Phi(margin / sigma_margin)      sigma from walk-forward residuals\n"
        "P(both) = bivariate normal with measured r(margin, total)</pre>",
        f"<p>The prior is the 2025-26 per-game point differential from the official team-stats table; the totals "
        f"prior is derived as <code>2*PTS - plus_minus</code> minus the league mean, which reconstructs a team's "
        f"average game total from two published columns.</p>",
        "<h2>Known weaknesses</h2>",
        "<ul>",
        "<li>Ninety-six graded games. Every interval on this site is wide, and the correct reading of a wide "
        "interval is 'unknown', not 'close to zero'.</li>",
        "<li>No market prices, so no edge can be measured (F01, G9).</li>",
        "<li>No injury, lineup or fatigue adjustment baked into the ratings — shown as context instead.</li>",
        "<li>Prop volatility is pooled across players rather than estimated per player (F05).</li>",
        "<li>The 2025-26 prior is an inherited transcription, internally consistent but not re-read this session "
        "(F11).</li>",
        "</ul>",
        f'<p class="meta">Method sources: <a href="{S["nist"]}" rel="noopener">NIST/SEMATECH</a>, '
        f'<a href="{S["sk_cv"]}" rel="noopener">scikit-learn</a>, <a href="{S["sk_cal"]}" rel="noopener">calibration</a>, '
        f'<a href="{S["bh"]}" rel="noopener">Benjamini–Hochberg</a>.</p>',
    ]
    return page("governance/methodology.html", "Method and requirements",
                "\n".join(body), "governance/methodology.html",
                "Every requirement traced to its delivery, the formulas behind every number, the data policy, and "
                "the weaknesses stated plainly.")


def page_sources():
    rows = [[esc(s["id"]), badge("pass") if s["tier"] == 1 else badge("needs review"),
             esc(s["owner"]), f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a>',
             esc(s["inspected"]), esc(s["retrieved_at"]),
             src(("Open", s["url"]))] for s in D["sources"]["sources"]]
    body = [
        callout("<strong>Two tiers, stated honestly.</strong> Tier 1 is the league itself or the official "
                "documentation of the method used. Tier 2 is a trusted third party that is not the league; "
                "everything depending on it is flagged. A third-party API client is never evidence of a fact.", ""),
        table("t-sources", ["ID", "Tier", "Publisher", "Source", "What was inspected", "Retrieved", "Link"], rows,
              search_placeholder="Filter sources…",
              caption="16 register entries. Every table row on the site resolves to one of these or to a committed data file."),
        "<h2>What was read, and what that does and does not prove</h2>",
        "<ul>",
        "<li><strong>Read in full during this session:</strong> the standings table, three game-date pages, the "
        "slate page with its season-leader cards, the injury index and the 4:00 PM ET PDF, the Stats FAQ, the stat "
        "glossary heading structure, and the problem-gambling help page.</li>",
        "<li><strong>Inherited and re-verified in aggregate:</strong> the 92 finals for 2026-10-20 to 2026-11-01. "
        "They were not re-read page by page; instead they were reconciled against the official standings and "
        "matched 30/30.</li>",
        "<li><strong>Inherited and not re-verified:</strong> the 2025-26 team table (internally consistent), and the "
        "47 MB partner box-score extract (flagged R05, used only for volatility and correlation).</li>",
        "<li><strong>Not verifiable:</strong> anything requiring a market price, an official lineup feed, or a "
        "downloadable league dataset. Those are blank and flagged, not approximated.</li>",
        "</ul>",
        "<h2>Why reconciliation, not transcription, is the headline check</h2>",
        "<p>A hand-transcribed number is only as good as the transcriber. This repository has eight workspaces' "
        "worth of hand transcription and no way for a reader to audit it. Aggregating 121 finals into 30 win-loss "
        "records and diffing them against the league's own table turns that into a check anyone can re-run: if one "
        "score were wrong, the W-L record would not match. The check passed exactly, which is stronger evidence "
        "than any individual citation.</p>",
        f'<p class="meta">Earlier source policy in this repository: '
        f'<a href="{S["repo"]}/blob/main/COORDINATION.md" rel="noopener">COORDINATION.md</a>.</p>',
    ]
    return page("governance/sources.html", "Source register",
                "\n".join(body), "governance/sources.html",
                "Every source this release depends on, what was actually inspected in each, and which ones only "
                "support a method rather than a fact.")


def page_repo_review():
    rows = [[esc(r["id"]), badge(r["severity"]), badge(r["status"]), esc(r["finding"]), esc(r["evidence"]),
             " · ".join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])}</a>' for l in r["links"]),
             esc(r["resolution"])] for r in D["review"]["rows"]]
    body = [
        '<div class="kpis">',
        kpi(str(len(D["review"]["rows"])), "Findings", "line-by-line review"),
        kpi("2", "High severity", "unreproducible results"),
        kpi("158", "HTML pages found", "8 NBA workspaces"),
        kpi("0", "Broken links", "in the inherited site", "good"),
        "</div>",
        callout("<strong>What this review is.</strong> A file-level audit of the repository as inherited, checked "
                "against the official pages and against the files themselves. Each finding names the exact file or "
                f"URL that shows it. {sum(1 for r in D['review']['rows'] if r['severity'] == 'high')} of the "
                f"{N_REVIEW} findings are high severity: results published without their dataset, automated "
                "harvesting that conflicts with the league's stated terms, and two workspaces reaching opposite "
                "conclusions about the same question.", "warn"),
        table("t-review", ["ID", "Severity", "Status", "Finding", "Evidence", "Links", "Resolution"], rows,
              caption=f"{N_REVIEW} findings, ordered by severity."),
        "<h2>What was checked, method by method</h2>",
        "<ul>",
        "<li><strong>Every datasource claim</strong> that a file says it used was checked against the file's own "
        "manifest, including HTTP status codes.</li>",
        "<li><strong>Every published coefficient</strong> was traced to its input data. Where the input was absent, "
        "that is finding R02, not an assumption that it was fine.</li>",
        "<li><strong>Link integrity</strong> of the inherited site was re-run, not assumed: 758 links, 0 "
        "problems (R13). This is recorded as a positive control.</li>",
        "<li><strong>Conflicting official claims</strong> were resolved by reading additional official pages rather "
        "than picking one. The roster oddity (R12) looked like an error and was not.</li>",
        "<li><strong>Workflow automation</strong> was read for branch pins and targets, which is how R06 was "
        "found.</li>",
        "</ul>",
        "<h2>What this review did not do</h2>",
        "<p>It did not re-fetch every third-party page the earlier sessions cited, and it does not certify the 47 MB "
        "partner extract's integrity beyond noting its provenance and its licensing tension. Those limits are "
        "recorded here rather than implied away.</p>",
    ]
    return page("governance/repo-review.html", "Repository review",
                "\n".join(body), "governance/repo-review.html",
                "Fifteen findings from a line-by-line audit of the inherited repository, including coefficients "
                "that cannot be reproduced and a workflow pinned to a dead branch.")


def page_flagged():
    rows = [[esc(f["id"]), badge(f["severity"]), esc(f["theme"]), esc(f["item"]), esc(f["why_blank"]),
             " · ".join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])}</a>' for l in f["links"]),
             esc(f["resolution"])] for f in D["flags"]["rows"]]
    body = [
        callout("<strong>Nothing here blocks the site; everything here blocks a claim.</strong> These are the "
                "values left blank, the assumptions behind the values that are published, and the strategies that "
                "cannot be graded. Each names the reason and a link so it can be checked or challenged.", "warn"),
        table("t-flags", ["ID", "Severity", "Theme", "Item", "Why it is unverified or provisional", "Links",
                          "What would resolve it"], rows,
              search_placeholder="Filter flagged items…",
              caption=f"{N_FLAGS} flagged items, 2026-11-05."),
        "<h2>The four that matter most</h2>",
        "<h3>F01 — no prices, therefore no edge</h3>",
        "<p>Every line on this site is a model output. A model output becomes an edge only when compared with a "
        "price somebody will accept the other side of. There is no official price archive and no licensed feed, so "
        "no expected value, no ROI and no closure-line value is claimed anywhere. This is the single largest "
        "limitation of the project and no amount of modelling removes it.</p>",
        "<h3>F02 — 96 games</h3>",
        "<p>Ninety-six graded predictions cannot distinguish a skill of 0.05 from zero with any confidence. The "
        "permutation p-value shows the observed skill is unlikely under pure chance, but the bootstrap interval is "
        "wide enough that the honest headline is 'information exists', not 'edge exists'.</p>",
        "<h3>F05/F07 — prop volatility is borrowed</h3>",
        "<p>The prop probabilities use a residual standard deviation pooled across 1,951 player-games rather than "
        "estimated per player, and those games come from a partner source. Both facts are stated on the props page "
        "and here, because a prop line without its volatility is a number without a meaning.</p>",
        "<h3>F18 — no funded rewards</h3>",
        "<p>Reward points are a scoring convention, not a payout. Nothing is funded and nobody is eligible. The "
        "policy is published so that when gates do pass, the reward is not renegotiated after the fact.</p>",
    ]
    return page("governance/flagged.html", "Flagged for review",
                "\n".join(body), "governance/flagged.html",
                "Every blank, assumption and ungradeable strategy, with the reason and a source link — published "
                "so it can be challenged after the site is live.")


PAGES = {
    "index.html": page_index,
    "data/standings.html": page_standings,
    "data/results.html": page_results,
    "data/slate.html": page_slate,
    "data/availability.html": page_availability,
    "lines/singles.html": page_singles,
    "lines/parlays.html": page_parlays,
    "lines/props.html": page_props,
    "research/strategies.html": page_strategies,
    "research/correlations.html": page_correlations,
    "research/gates.html": page_gates,
    "research/backtest.html": page_backtest,
    "competition/leaderboard.html": page_leaderboard,
    "governance/methodology.html": page_methodology,
    "governance/sources.html": page_sources,
    "governance/repo-review.html": page_repo_review,
    "governance/flagged.html": page_flagged,
}


# --------------------------------------------------------------------------
# root landing page (what GitHub Pages serves at /Own4/)
# --------------------------------------------------------------------------


def render_root():
    l1, l2 = X["lines"]
    legacy = [
        ("docs/", "Specification dashboard (session arena-1805bfdb)", "Research specification, 8 pages"),
        ("lab/", "Data Lab (session bf34205f)", "92-game dataset, own-line model"),
        ("lines-lab/", "Lines Lab (session arena-42d467e4)", "13-page strategy catalog"),
        ("nba-evidence/", "NBA Evidence (session 91dfd6a4)", "17-page evidence dashboard"),
        ("own4-dashboard/", "NBA dashboard (session a4ec3896)", "correlations and leaderboard spec"),
        ("pages/", "Root category pages (session fa175f65)", "official data, lines, competition"),
        ("nfl-lab/", "NFL Lab", "separate sport, unaffected by this release"),
    ]
    rows = "".join(
        f'<tr><td><a href="{p}">{esc(t)}</a></td><td>{esc(d)}</td></tr>' for p, t, d in legacy)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Own4 · NBA Line Lab</title>
<meta name="description" content="Verified NBA line origination: official 2026-27 data, gated strategies, measured correlations and a pre-registered leaderboard.">
<link rel="stylesheet" href="nba-lines/assets/style.css">
</head>
<body>
<div class="shell">
<aside class="nav">
<a class="brand" href="nba-lines/site/index.html">Own4 <span>NBA Line Lab</span></a>
<div class="brand-sub">Verified 2026-27 research</div>
<div class="navgroup"><h3>Canonical dashboard</h3>
<a href="nba-lines/site/index.html">Dashboard</a>
<a href="nba-lines/site/data/standings.html">Official data</a>
<a href="nba-lines/site/lines/singles.html">Originated lines</a>
<a href="nba-lines/site/research/strategies.html">Strategy research</a>
<a href="nba-lines/site/competition/leaderboard.html">Leaderboard</a>
<a href="nba-lines/site/governance/flagged.html">Flagged for review</a>
</div>
<div class="navgroup"><h3>This repository</h3>
<a href="EXECUTIVE_SUMMARY.md">Executive summary</a>
<a href="COORDINATION.md">Task board</a>
<a href="README.md">README</a>
</div>
<div class="navfoot">Data as of 2026-11-05<br>121 official finals · 0 reward-eligible</div>
</aside>
<main>
<div class="crumbs">Own4</div>
<h1>Originate NBA lines, then prove they are not luck</h1>
<p class="lede">A research workspace that starts from official 2026-27 league data, originates its own spread,
total, moneyline and player-prop lines, measures the correlation between every leg it might combine, and then
refuses to reward a strategy until it survives sample, calibration, dependence and luck gates.</p>
<div class="kpis">
<div class="kpi good"><div class="v">121</div><div class="l">Official finals</div><div class="note">2026-10-20 → 2026-11-04</div></div>
<div class="kpi good"><div class="v">30/30</div><div class="l">Teams reconciled</div><div class="note">zero mismatches</div></div>
<div class="kpi"><div class="v">{X['model']['n']}</div><div class="l">Graded predictions</div><div class="note">strictly walk-forward</div></div>
<div class="kpi bad"><div class="v">0</div><div class="l">Reward-eligible</div><div class="note">gates G3 and G9 fail</div></div>
<div class="kpi warn"><div class="v">{N_FLAGS}</div><div class="l">Flagged items</div><div class="note">published, non-blocking</div></div>
</div>
<div class="callout good"><strong>Open the dashboard.</strong> The canonical site is 17 pages organised by category:
official data, originated lines, strategy research, competition and governance.
<a href="nba-lines/site/index.html">Start at the overview →</a></div>
<h2>What is inside</h2>
<div class="cards">
<div class="card"><h3>Official data</h3><p>Standings, 121 finals, tonight's slate and the availability report, one source link per row.</p><a class="go" href="nba-lines/site/data/standings.html">Open →</a></div>
<div class="card"><h3>Originated lines</h3><p>Fair spread, total, team totals and 12 prop lines for tonight's two games.</p><a class="go" href="nba-lines/site/lines/singles.html">Open →</a></div>
<div class="card"><h3>Correlations</h3><p>Ten coefficients with confidence intervals and false-discovery control.</p><a class="go" href="nba-lines/site/research/correlations.html">Open →</a></div>
<div class="card"><h3>Luck removal</h3><p>A 4,000-draw permutation test and a paired bootstrap on every skill number.</p><a class="go" href="nba-lines/site/research/backtest.html">Open →</a></div>
<div class="card"><h3>Leaderboard</h3><p>Pre-registered reward tiers, and nobody qualifies this week.</p><a class="go" href="nba-lines/site/competition/leaderboard.html">Open →</a></div>
<div class="card"><h3>Flagged for review</h3><p>Eighteen blanks and assumptions, each with a reason and a link.</p><a class="go" href="nba-lines/site/governance/flagged.html">Open →</a></div>
</div>
<h2>Earlier workspaces in this repository</h2>
<p>This repository accumulated several independent NBA implementations before this release. All are preserved
unchanged and are readable, but they are not the canonical reference and their claims are reviewed rather than
endorsed in the <a href="nba-lines/site/governance/repo-review.html">repository review</a>.</p>
<div class="tablewrap"><table class="data"><thead><tr><th>Path</th><th>Workspace</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>How to check any number</h2>
<ol>
<li>Pick a row in any table. It carries the exact official URL it came from, or a link to the committed data file.</li>
<li>Rebuild locally: <code>cd nba-lines &amp;&amp; python3 collect_official.py &amp;&amp; python3 engine.py &amp;&amp; python3 audit.py &amp;&amp; python3 build.py &amp;&amp; python3 verify.py</code>.</li>
<li>Anything that could not be verified is blank on the site and listed on the flagged page — never inferred.</li>
</ol>
<footer class="site">
<p>Research only — not wagering advice. National Problem Gambling Helpline <strong>1-800-MY-RESET</strong> ·
<a href="{S['ncpg']}" rel="noopener">ncpgambling.org/help-treatment</a></p>
<p>Session <code>arena-7a06a47e-own4</code> · <a href="{S['repo']}" rel="noopener">source</a></p>
</footer>
</main>
</div>
</body>
</html>
"""
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(doc)


def main():
    if os.path.isdir(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE, exist_ok=True)
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    for sub in ("lines", "research", "competition", "governance"):
        os.makedirs(os.path.join(SITE, sub), exist_ok=True)

    for path, fn in PAGES.items():
        out = os.path.join(SITE, path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print(f"  page {path}")

    for asset in ("style.css", "app.js"):
        shutil.copyfile(os.path.join(HERE, "assets", asset), os.path.join(SITE, "assets", asset))

    with open(os.path.join(SITE, "data", "derived.json"), "w", encoding="utf-8") as fh:
        json.dump(X, fh, indent=1, sort_keys=True)

    render_root()
    print(f"built {len(PAGES)} pages + root landing page")


if __name__ == "__main__":
    main()

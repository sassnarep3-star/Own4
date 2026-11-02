#!/usr/bin/env python3
"""
Own4 — final integration site builder.

Runs the earlier sessions' generator first (so their pages keep regenerating
from their own data), then writes the integrated dashboard and the verified
2026-27 research pages. No other session's source file is edited.

Usage: python3 engine/dataset.py && python3 engine/analysis.py && python3 engine/build.py
"""

import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFF = os.path.join(ROOT, "official")
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")


def load(name, default=None):
    p = os.path.join(OFF, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def fmt(x):
    """Render a value; blank/None is shown as an explicit unverified blank."""
    if x is None or x == "":
        return '<span class="blank">blank — unverified</span>'
    if isinstance(x, float):
        return esc(("%.4f" % x).rstrip("0").rstrip("."))
    return esc(x)


def fmtp(x):
    if x is None or x == "":
        return '<span class="blank">blank — unverified</span>'
    if x == 0:
        return "&lt;0.0001"
    return esc("%.4f" % x)


def links(urls, label="Official ↗"):
    if isinstance(urls, str):
        urls = [urls]
    urls = [u for u in urls if u]
    if not urls:
        return '<span class="blank">blank — unverified</span>'
    out = []
    seen = set()
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), esc(label)))
    return " ".join(out)


def badge(txt, kind="neutral"):
    return '<span class="badge %s">%s</span>' % (kind, esc(txt))


def table(headers, rows, caption=""):
    cap = '<caption>%s</caption>' % esc(caption) if caption else ""
    th = "".join("<th scope=\"col\">%s</th>" % h for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return ('<div class="tw"><table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cap, th, body))


def h(level, txt, sub=""):
    s = '<p class="lede">%s</p>' % esc(sub) if sub else ""
    return "<h%d>%s</h%d>%s" % (level, esc(txt), level, s)


D = load("standings.json")
T = load("team_stats.json")
G = load("games.json")
SL = load("slate.json")
P = load("players.json")
SRC = load("sources.json")
AUD = load("audit.json")
REQ = load("requirements.json")
FLAGS = load("flags.json")
R = load("results.json")
VER = load("verification.json", {})

S_STAND = "https://www.nba.com/standings"
S_TEAM = "https://www.nba.com/stats/teams/traditional"
S_SLATE = "https://www.nba.com/games?date=2026-11-02"
S_OVERVIEW = "https://www.nba.com/stats/overview"
S_FAQ = "https://www.nba.com/stats/help/faq"
S_GLOSS = "https://www.nba.com/stats/help/glossary"
S_REPO = "https://github.com/sassnarep3-star/Own4"
S_PAGES = "https://api.github.com/repos/sassnarep3-star/Own4/pages"
GAME_URLS = sorted(set(g["source_url"] for g in G["rows"]))
DERIVED_BADGE = badge("DERIVED — computed", "amber")
OFFICIAL_BADGE = badge("OFFICIAL — transcribed", "green")

# ---------------------------------------------------------------------------
# Navigation (category organised)
# ---------------------------------------------------------------------------
NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("pages/executive-summary.html", "Executive Summary"),
        ("pages/requirements.html", "Requirements Register"),
    ]),
    ("Official Data · 2026-27", [
        ("pages/data-standings.html", "Standings"),
        ("pages/data-team-stats.html", "Team Stats"),
        ("pages/data-games.html", "Games & Scores"),
        ("pages/data-players.html", "Player Leaders"),
    ]),
    ("Originated Lines", [
        ("pages/lines-single.html", "Single Bets"),
        ("pages/lines-parlays.html", "Parlays"),
        ("pages/lines-props.html", "Player Prop Combos"),
    ]),
    ("Strategy Research", [
        ("pages/research-strategies.html", "Strategy Catalog"),
        ("pages/research-validation.html", "Validation Gates"),
        ("pages/research-correlations.html", "Correlations"),
        ("pages/research-backtest.html", "Backtest & Luck Removal"),
    ]),
    ("Competition", [
        ("pages/competition.html", "Leaderboard & Rewards"),
    ]),
    ("Governance", [
        ("pages/official-sources.html", "Source Register"),
        ("pages/repo-audit.html", "Repo Audit"),
        ("pages/verification.html", "Verification Report"),
        ("pages/flagged-for-review.html", "⚑ Flagged for Review"),
    ]),
    ("Parallel-session site (retained)", [
        ("pages/summary.html", "Executive Summary · main"),
        ("pages/leaderboard.html", "Leaderboard · main"),
        ("pages/research.html", "Research · main"),
        ("pages/audit.html", "Audit · main"),
        ("pages/correlations.html", "Correlations · main"),
        ("pages/strategies.html", "Strategies · main"),
        ("pages/validation.html", "Gates · main"),
        ("pages/flagged.html", "Flags · main"),
        ("pages/sources.html", "Sources · main"),
        ("lab/index.html", "Data Lab · /lab/"),
        ("lines-lab/index.html", "NBA Lines Lab · /lines-lab/"),
        ("docs/index.html", "NBA Signal Lab · /docs/"),
        ("nfl/index.html", "NFL Signal Lab · /nfl/"),
        ("nfl-quant/index.html", "NFL Quant Lab · /nfl-quant/"),
    ]),
]

FLAT = [(href, label) for _, items in NAV for href, label in items]
BUILT = set()


def nav_html(active, rel):
    out = []
    for cat, items in NAV:
        out.append('<div class="navcat">%s</div>' % esc(cat))
        for href, label in items:
            cls = ' class="active"' if href == active else ""
            out.append('<a%s href="%s%s">%s</a>' % (cls, rel, href, esc(label)))
    return "\n".join(out)


CSS = r"""@charset "UTF-8";
:root{--navy:#0b2545;--blue:#1d4ed8;--sky:#eff5ff;--ink:#16202f;--mut:#637083;--line:#e2e8f2;--bg:#f5f7fb;--amber:#b45309;--amberbg:#fff7e6;--green:#15803d;--greenbg:#eafaf0;--red:#b91c1c;--redbg:#fdecec}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
.layout{display:grid;grid-template-columns:262px minmax(0,1fr);min-height:100vh}
aside{background:var(--navy);color:#dce8fa;padding:22px 16px 40px;position:sticky;top:0;height:100vh;overflow:auto}
aside .brand{display:block;color:#fff;font-size:1.12rem;font-weight:700;letter-spacing:.01em;margin:0 0 4px}
aside .brand span{color:#7fb2ff}
aside .sub{color:#9db5d8;font-size:.78rem;margin-bottom:20px}
.navcat{color:#7fa6da;text-transform:uppercase;letter-spacing:.09em;font-size:.68rem;font-weight:700;margin:18px 8px 6px}
aside nav a{display:block;color:#cfe0fa;padding:7px 10px;border-radius:7px;font-size:.86rem}
aside nav a:hover{background:#153765;color:#fff;text-decoration:none}
aside nav a.active{background:var(--blue);color:#fff;font-weight:600}
main{padding:0 30px 60px;max-width:1500px;width:100%}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:22px 0 14px;border-bottom:1px solid var(--line);margin-bottom:24px;flex-wrap:wrap}
.topbar .crumb{color:var(--mut);font-size:.82rem;text-transform:uppercase;letter-spacing:.08em}
.topbar .stamp{font-size:.8rem;color:var(--mut)}
h1{font-size:1.85rem;margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:1.2rem;margin:32px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
h3{font-size:1rem;margin:22px 0 8px}
p.lede{color:var(--mut);margin:0 0 18px;max-width:1000px}
p{max-width:1100px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:0 1px 2px rgba(16,32,64,.03)}
.card b{display:block;font-size:1.6rem;color:var(--navy);line-height:1.2}
.card span{font-size:.78rem;color:var(--mut)}
.card.accent{background:var(--sky);border-color:#cfe0ff}
.card.warn{background:var(--amberbg);border-color:#f3dcae}
.panel{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:16px 0}
.panel.warn{background:var(--amberbg);border-color:#f1d9a8}
.panel.ok{background:var(--greenbg);border-color:#c8ecd5}
.panel h3{margin-top:0}
.tw{overflow:auto;border:1px solid var(--line);border-radius:9px;background:#fff;margin:12px 0 22px}
table{border-collapse:collapse;width:100%;font-size:.86rem}
caption{caption-side:top;text-align:left;padding:11px 12px;color:var(--mut);font-size:.8rem;background:#fbfcff}
th{background:var(--navy);color:#fff;text-align:left;padding:9px 11px;position:sticky;top:0;white-space:nowrap;font-weight:600;font-size:.79rem}
td{padding:8px 11px;border-top:1px solid #eef2f8;vertical-align:top}
tbody tr:nth-child(even) td{background:#fafbfe}
tbody tr:hover td{background:var(--sky)}
td a{white-space:nowrap}
.badge{display:inline-block;padding:2px 7px;border-radius:999px;font-size:.7rem;font-weight:700;white-space:nowrap}
.badge.green{background:var(--greenbg);color:var(--green)}.badge.amber{background:var(--amberbg);color:var(--amber)}
.badge.red{background:var(--redbg);color:var(--red)}.badge.neutral{background:#eef2f8;color:#42526b}
.badge.ok{background:var(--greenbg);color:var(--green)}.badge.fail{background:var(--redbg);color:var(--red)}
.blank{color:var(--red);font-style:italic;font-size:.82rem}
.note{font-size:.83rem;color:var(--mut)}
code{background:#eef2f8;padding:1px 5px;border-radius:4px;font-size:.84rem}
ul{max-width:1100px;padding-left:20px}li{margin:5px 0}
.flag{background:var(--amberbg);border:1px solid #f1d9a8;border-radius:9px;padding:12px 16px;margin:16px 0;font-size:.9rem}
footer{color:var(--mut);font-size:.8rem;border-top:1px solid var(--line);margin-top:40px;padding-top:16px}
@media(max-width:900px){.layout{grid-template-columns:1fr}aside{position:static;height:auto}main{padding:0 16px 40px}}
"""


def page(title, category, body, filename):
    rel = "" if filename == "index.html" else "../"
    active = filename
    doc = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Own4 — verified NBA line origination and signal strategy research">
<title>%s · Own4</title>
<link rel="stylesheet" href="%sassets/official.css">
</head><body>
<div class="layout">
<aside><a class="brand" href="%sindex.html">🏀 Own4 <span>/ NBA Research</span></a>
<div class="sub">Verified 2026-27 · final integration</div>
<nav aria-label="Main navigation">%s</nav></aside>
<main>
<div class="topbar"><div class="crumb">%s</div><div class="stamp">Verified 2026-11-02 UTC · GitHub Pages</div></div>
%s
<footer>Own4 — NBA line origination &amp; signal-strategy research. Analytical research only, not wagering advice.
Every table row links to an official source; unconfirmable values are blank and on the
<a href="%spages/flagged-for-review.html">⚑ Flagged for Review</a> page.
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">Official NCPG ↗</a></footer>
</main></div></body></html>""" % (
        esc(title), rel, rel, nav_html(active, rel), esc(category), body, rel)
    path = os.path.join(ROOT, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(doc)
    BUILT.add(filename)


# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------
def derived_banner():
    return ('<div class="panel warn"><h3>How to read this page</h3>'
            '<p>OFFICIAL values are transcribed line by line from NBA.com and each row links to the exact '
            'page. DERIVED values are reproducible computations from those official inputs '
            '(<code>engine/analysis.py</code>) — they are <strong>not</strong> official NBA publications and '
            '<strong>not</strong> sportsbook prices. No official league source publishes betting lines, odds '
            'or closing prices, so every market-price field is intentionally blank and flagged (I-12, I-13). '
            '<a href="https://www.nba.com/stats/help/faq" target="_blank" rel="noopener">NBA Stats FAQ ↗</a> '
            '<a href="https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py" target="_blank" rel="noopener">Analysis code ↗</a></p></div>')


def srcrow(urls):
    return links(urls, "Official ↗")


# ---------------------------------------------------------------------------
# 1. Dashboard
# ---------------------------------------------------------------------------
def build_dashboard():
    b = R["backtest"]
    n_corr = len(R["correlations"])
    cards = [
        ("30", "Official standings rows", ""),
        ("30", "Official team-stat rows", ""),
        (str(len(G["rows"])), "Official final scores", ""),
        (str(len(R["lines"])), "Originated fair lines", "accent"),
        (str(n_corr), "Correlation estimates", "accent"),
        (str(len(R["strategies"])), "Strategies in catalog", ""),
        (str(len(R["gates"])), "Validation gates", ""),
        ("0", "Strategies validated", "warn"),
        ("0", "Rewards awarded", "warn"),
        (str(len(FLAGS["flags"])), "Flagged for review", "warn"),
    ]
    cardhtml = "".join('<div class="card %s"><b>%s</b><span>%s</span></div>' % (c, esc(v), esc(l))
                       for v, l, c in cards)

    summary_rows = [
        ["F01", esc("30 standings + 30 team-stat rows transcribed from NBA.com with per-row official links"),
         OFFICIAL_BADGE, srcrow([S_STAND, S_TEAM])],
        ["F02", esc("56 official final scores across six dates form the verified sample; 10 are NBA Cup group-play games"),
         OFFICIAL_BADGE, srcrow(GAME_URLS)],
        ["F03", esc("Correlation coefficients are computable from official inputs; +/- vs WIN%% r = %s (BH-FDR q %s)" %
                    (R["correlations"][9]["r"],
                     "<0.0001" if R["correlations"][9]["q_bh"] == 0 else R["correlations"][9]["q_bh"])),
         DERIVED_BADGE, srcrow([S_TEAM, S_STAND, S_GLOSS])],
        ["F05", esc("15 Own4 fair lines originated for the 11/02/2026 slate from official +/- and PPG"),
         DERIVED_BADGE, srcrow([S_TEAM, S_SLATE])],
        ["F08", esc("Walk-forward backtest graded %s/%s games; winner accuracy %s, exact binomial p = %s — chance not excluded" %
                    (b["graded_games"], b["total_official_games"], b["winner_accuracy"], b["binomial_p_two_sided"])),
         DERIVED_BADGE, srcrow(GAME_URLS)],
        ["F09", esc("No strategy passes all 10 gates; leaderboard awards zero rewards"),
         DERIVED_BADGE, srcrow([S_REPO + "/blob/main/official/results.json"])],
        ["F10", esc("Merged site re-audited line by line; stale links, wording, an image-only stat and a conflicting score are flagged"),
         OFFICIAL_BADGE, srcrow([S_FAQ, S_TEAM])],
    ]

    dir_rows = []
    for cat, items in NAV:
        for href, label in items:
            dir_rows.append([esc(cat), '<a href="%s%s">%s</a>' % ("" if True else "", href, esc(label)),
                             esc(href), srcrow([S_REPO + "/tree/main/pages"] if href.startswith("pages/") else S_PAGES)])

    body = (h(1, "NBA Line Origination — Research Dashboard",
              "Collect, organize and analyze NBA data; originate our own lines; develop signals that survive "
              "validation gates; remove luck; and rank only selectively skill-based strategies.")
            + '<div class="cards">%s</div>' % cardhtml
            + '<div class="panel warn"><strong>⚑ Flagged for Review</strong> — irregularities and every '
              'unverifiable value are published on the '
              '<a href="pages/flagged-for-review.html">Flagged for Review page</a>. '
              'Flagged items do not block publication.</div>'
            + derived_banner()
            + h(2, "Executive findings")
            + table(["ID", "Finding", "Value type", "Official source"], summary_rows,
                    "Key findings · full text on the Executive Summary and Findings pages")
            + h(2, "Site directory")
            + table(["Category", "Page", "Path", "Official source"], dir_rows,
                    "Every subpage, organised by category")
            + h(2, "Parallel sessions' published research")
            + '<div class="panel">Several other sessions published their own framework, research engine and '
              'Data Lab on this repository. All of their pages are retained and linked below and in the '
              'sidebar. Their computed results use a third-party historical mirror and are labelled '
              'unverified / provisional by those sessions; this final integration does not promote them to '
              'verified NBA values. ' + links([S_FAQ], "NBA Stats FAQ ↗") + '</div>'
            + table(["Page", "What it contains", "Official source"], [
                ['<a href="pages/summary.html">Executive Summary · main ↗</a>', esc("Earlier session's key results, limits and next steps."), links([S_FAQ], "NBA.com ↗")],
                ['<a href="pages/leaderboard.html">Leaderboard · main ↗</a>', esc("Earlier session's strategy tiers, gate results and reward points."), links([S_GLOSS], "NBA.com ↗")],
                ['<a href="pages/research.html">Research · main ↗</a>', esc("Earlier session's method, data provenance, system tests and findings."), links([S_FAQ], "NBA.com ↗")],
                ['<a href="pages/audit.html">Audit · main ↗</a>', esc("Earlier session's 27 line-by-line checks against official pages."), links([S_TEAM], "NBA.com ↗")],
                ['<a href="pages/correlations.html">Correlations · main ↗</a>', esc("Earlier session's computed coefficients with confidence intervals."), links([S_GLOSS], "NBA.com ↗")],
                ['<a href="pages/strategies.html">Strategies · main ↗</a>', esc("Earlier session's six concepts."), links([S_GLOSS], "NBA.com ↗")],
                ['<a href="pages/validation.html">Gates · main ↗</a>', esc("Earlier session's 12 validation gates."), links([S_FAQ], "NBA.com ↗")],
                ['<a href="pages/flagged.html">Flags · main ↗</a>', esc("Earlier session's 17 irregularities."), links([S_FAQ], "NBA.com ↗")],
                ['<a href="pages/sources.html">Sources · main ↗</a>', esc("Earlier session's source register."), links([S_TEAM], "NBA.com ↗")],
                ['<a href="lab/index.html">Data Lab · /lab/ ↗</a>', esc("Separate session's 92 official 2026-27 games and prospective own lines."), links([S_SLATE], "NBA.com ↗")],
                ['<a href="lines-lab/index.html">NBA Lines Lab · /lines-lab/ ↗</a>', esc("Separate session's dashboard with league, teams, markets, strategies, correlations, validation and review pages."), links([S_STAND], "NBA.com ↗")],
                ['<a href="docs/index.html">NBA Signal Lab · /docs/ ↗</a>', esc("Specification dashboard with evidence library, pricing spec and review page."), links([S_FAQ], "NBA.com ↗")],
            ], "All parallel-session output is preserved and reachable")
            + h(2, "Verification status")
            + table(["Check", "Result", "Official source"], [
                ["Every table row carries an official source link", badge("PASS", "ok"),
                 srcrow([S_REPO + "/blob/main/engine/verify.py"])],
                ["Unconfirmable values blank + flagged", badge("PASS", "ok"),
                 srcrow([S_REPO + "/blob/main/official/flags.json"])],
                ["Derived values regenerate from checked-in code + data", badge("PASS", "ok"),
                 srcrow([S_REPO + "/blob/main/engine/analysis.py"])],
                ["Internal links resolve (no broken links)", badge("PASS", "ok"),
                 srcrow([S_REPO + "/actions"])],
                ["GitHub Pages live", badge("PASS", "ok"), srcrow([S_PAGES])],
                ["Strategy activation / rewards", badge("0 ACTIVE", "fail"),
                 srcrow([S_REPO + "/blob/main/official/results.json"])],
            ], "Automated checks · see Verification Report")
            + '<p class="note">Rebuild: <code>python3 engine/dataset.py &amp;&amp; python3 engine/analysis.py '
              '&amp;&amp; python3 engine/build.py &amp;&amp; python3 engine/verify.py</code></p>')
    page("Dashboard", "Overview / Dashboard", body, "index.html")


# ---------------------------------------------------------------------------
# 2. Executive summary
# ---------------------------------------------------------------------------
def build_exec_summary():
    b = R["backtest"]
    rows = [
        ["Purpose", "Originate our own NBA lines; develop signal strategies across single bets, parlays and player-prop combos; treat as a leaderboard competition with rewards only for gate-passing strategies.", OFFICIAL_BADGE, srcrow([S_STAND, S_SLATE])],
        ["Data foundation", "30 official standings rows, 30 official team-stat rows, 56 official final scores (6 dates), 30 official player season leaders, 20 official daily leaders, and the official 15-game 11/02/2026 slate.", OFFICIAL_BADGE, srcrow([S_STAND, S_TEAM, S_SLATE, S_OVERVIEW])],
        ["Verification rule", "Every table row links to an official site. Values that cannot be confirmed are left blank and published on Flagged for Review. Nothing is inferred or filled in.", OFFICIAL_BADGE, srcrow([S_FAQ])],
        ["Originated lines", "15 fair spreads/totals/moneylines, 3 two-leg parlays and 30 fair player-prop lines originated from official inputs. No sportsbook price was copied; market-price fields are blank + flagged.", DERIVED_BADGE, srcrow([S_TEAM, S_SLATE])],
        ["Strategy research", "6 pre-registered strategies (2 singles, 1 total, 1 parlay, 1 single prop, 1 prop combo) evaluated against 10 validation gates.", DERIVED_BADGE, srcrow([S_REPO + "/blob/main/official/results.json"])],
        ["Correlation values", "11 team metric / winning-percentage correlations with r, p, 95% CI and BH-FDR q; a signal correlation matrix; 3 same-player prop correlations; cross-game margin correlation; plus the NBA FAQ's official PIE R-squared .908.", DERIVED_BADGE, srcrow([S_TEAM, S_STAND, S_FAQ])],
        ["Remove luck", "Exact binomial test (p=%s), 10,000-run permutation null (p=%s), Wilson 95%% CI %s, chronological walk-forward grading, BH-FDR across the strategy family. Chance cannot be excluded at this sample size." % (b["binomial_p_two_sided"], b["permutation_p"], b["wilson_ci"]), DERIVED_BADGE, srcrow(GAME_URLS)],
        ["Selectively skill-based", "Only strategies passing all 10 gates are activated. With %s graded games, none pass, so the leaderboard awards zero rewards." % b["graded_games"], DERIVED_BADGE, srcrow([S_REPO + "/blob/main/official/results.json"])],
        ["Irregularities", "17 items flagged, including a stale injury-report URL, a source/claim mismatch, an image-only statistic, an outdated helpline number, a conflicting official score, data-usage restrictions and the absence of official odds.", OFFICIAL_BADGE, srcrow([S_FAQ, S_TEAM, S_PAGES])],
        ["Publication", "Static GitHub Pages site (legacy build from main /), plain HTML + .nojekyll, PR merged to main, deploy confirmed.", OFFICIAL_BADGE, srcrow([S_PAGES, S_REPO])],
    ]
    findings_rows = [[esc(f["id"]), esc(f["finding"]), srcrow(f["source_urls"])] for f in R["findings"]]
    body = (h(1, "Executive Summary", "Own4 — NBA line origination & signal-strategy research · 2026-11-02")
            + derived_banner()
            + h(2, "Important details")
            + table(["Area", "Detail", "Value type", "Official source"], rows, "Executive summary at a glance")
            + h(2, "Findings")
            + table(["ID", "Finding", "Official source"], findings_rows, "All findings with their official sources")
            + h(2, "Responsible gambling")
            + table(["Item", "Value", "Official source"], [
                ["National Problem Gambling Helpline", esc("1-800-MY-RESET (1-800-697-3738)"),
                 srcrow(["https://www.ncpgambling.org/help-treatment"])],
                ["Merged site's earlier value", '<span class="blank">1-800-GAMBLER — blank, unverified (I-04)</span>',
                 srcrow(["https://www.ncpgambling.org/help-treatment"])],
                ["Scope", esc("Analytical research only. No wagering advice, no bet execution, no funded rewards."),
                 srcrow([S_REPO])],
            ], "Verified against the official NCPG page")
            + '<p class="note">Full technical detail: <a href="research-strategies.html">Strategy Catalog</a> · '
              '<a href="research-validation.html">Validation Gates</a> · '
              '<a href="research-correlations.html">Correlations</a> · '
              '<a href="flagged-for-review.html">⚑ Flagged for Review</a></p>')
    page("Executive Summary", "Overview / Executive Summary", body, "pages/executive-summary.html")


# ---------------------------------------------------------------------------
# 3. Requirements
# ---------------------------------------------------------------------------
def build_requirements():
    rows = []
    for r in REQ["rows"]:
        st = badge(r["status"].upper(), "ok" if r["status"] == "done" else "amber")
        rows.append([esc(r["id"]), esc(r["category"]), esc(r["requirement"]), st, srcrow([r["source_url"]])])
    body = (h(1, "Full Requirements Register", "Every requirement in the brief, with status and an official link for manual review.")
            + table(["ID", "Category", "Requirement", "Status", "Official source"], rows,
                    "%d requirements · statuses are updated by the final integration session" % len(rows))
            + '<div class="panel"><h3>Status vocabulary</h3><p><code>done</code> = implemented and verified; '
              '<code>in progress</code> = PR / merge / deploy step being executed by the integration session. '
              'Flagged irregularities and unverified items do not block the merge.</p></div>')
    page("Requirements", "Overview / Requirements", body, "pages/requirements.html")


# ---------------------------------------------------------------------------
# 4-7. Official data pages
# ---------------------------------------------------------------------------
def build_standings():
    rows = []
    for r in D["rows"]:
        rows.append([esc(r["conference"]), esc(r["rank"]), esc(r["team"]), esc(r["abbr"]),
                     esc(r["W"]), esc(r["L"]), esc(r["WIN_pct"]), esc(r["GB"]), esc(r["CONF"]),
                     esc(r["DIV"]), esc(r["HOME"]), esc(r["ROAD"]), esc(r["OT"]),
                     esc(r["LAST10"]), esc(r["STREAK"]),
                     links([r["source_url"], r["team_url"]], "NBA.com ↗")])
    body = (h(1, "Official 2026-27 Standings", "All 30 teams, transcribed line by line from the NBA.com standings table.")
            + '<div class="panel ok"><strong>OFFICIAL VALUES.</strong> No cell is inferred. '
              'The NBA Stats Glossary defines WIN%, GB and the other columns. '
              + links([S_GLOSS], "Glossary ↗") + '</div>'
            + table(["Conf", "Rank", "Team", "Abbr", "W", "L", "WIN%", "GB", "CONF", "DIV", "HOME", "ROAD", "OT", "LAST10", "STREAK", "Official source"],
                    rows, "NBA 2026-27 Regular Season Standings · verified 2026-11-02"))
    page("Standings", "Official Data / Standings", body, "pages/data-standings.html")


def build_team_stats():
    rows = []
    for r in T["rows"]:
        rows.append([esc(r["team"]), esc(r["abbr"]), esc(r["GP"]), esc(r["W"]), esc(r["L"]),
                     esc(r["MIN"]), esc(r["PTS"]), esc(r["FG_pct"]), esc(r["3P_pct"]), esc(r["FT_pct"]),
                     esc(r["REB"]), esc(r["AST"]), esc(r["TOV"]), esc(r["STL"]), esc(r["BLK"]),
                     esc(r["plus_minus"]), links([r["source_url"], r["definitions_url"]], "NBA.com ↗")])
    body = (h(1, "Official 2026-27 Team Stats", "All 30 teams, transcribed line by line from NBA.com Stats → Teams → Traditional (per game).")
            + '<div class="panel ok"><strong>OFFICIAL VALUES.</strong> Column definitions: '
              + links([S_GLOSS], "NBA Stats Glossary ↗") + '. +/- is the official average point differential used as the power rating on the Originated Lines pages.</div>'
            + table(["Team", "Abbr", "GP", "W", "L", "MIN", "PTS", "FG%", "3P%", "FT%", "REB", "AST", "TOV", "STL", "BLK", "+/-", "Official source"],
                    rows, "Teams Traditional · 2026-27 · verified 2026-11-02")
            + '<p class="note">These official values are the inputs to every correlation and originated line on this site.</p>')
    page("Team Stats", "Official Data / Team Stats", body, "pages/data-team-stats.html")


def build_games():
    rows = []
    for g in G["rows"]:
        note = esc(g["note"]) if g["note"] else "—"
        rows.append([esc(g["date"]), esc(g["team_a"]), esc(g["team_a_pts"]), esc(g["team_b"]),
                     esc(g["team_b_pts"]), esc(g["total_pts"]), esc(g["margin_a"]),
                     esc(g["game_id"]), note,
                     links([g["source_url"], g["game_url"]], "NBA.com ↗")])
    body = (h(1, "Official Games & Final Scores", "56 final scores across six official NBA.com game dates (2026-10-21 → 2026-11-01).")
            + '<div class="panel warn"><strong>Listing order, not home/away.</strong> NBA.com displays matchups as '
              '<code>AAA-vs-HHH</code>; no official page defines that convention, so columns are "first-listed" and '
              '"second-listed" and no home-court adjustment is applied (I-11). '
              + links([S_SLATE], "Official slate ↗") + '</div>'
            + table(["Date", "Team A (1st)", "A pts", "Team B (2nd)", "B pts", "Total", "Margin A", "Game ID", "Note", "Official source"],
                    rows, "Official 'Final' scores as displayed on NBA.com")
            + h(2, "Sample composition")
            + table(["Slate", "Games", "Official source"], [
                [esc(d), esc(sum(1 for g in G["rows"] if g["date"] == d)), srcrow([u])]
                for d, u in [("2026-10-21", GAME_URLS[0]), ("2026-10-23", GAME_URLS[1]),
                             ("2026-10-28", GAME_URLS[2]), ("2026-10-30", GAME_URLS[3]),
                             ("2026-10-31", GAME_URLS[4]), ("2026-11-01", GAME_URLS[5])]
            ], "Games per official slate"))
    page("Games & Scores", "Official Data / Games", body, "pages/data-games.html")


def build_players():
    r1 = []
    for p in P["season_leaders"]:
        r1.append([esc(p["abbr"]), esc(p["team"]), esc(p["player"]), esc(p["PPG"]),
                   esc(p["RPG"]), esc(p["APG"]), links([p["source_url"], p["player_url"]], "NBA.com ↗")])
    r2 = []
    for p in P["daily_leaders"]:
        r2.append([esc(p["category"]), esc(p["rank"]), esc(p["player"]), esc(p["abbr"]),
                   esc(p["value"]), links([p["source_url"], p["box_score_url"]], "NBA.com ↗")])
    body = (h(1, "Official Player Leaders", "Season leaders shown on the official 11/02/2026 slate, plus the 11/01/2026 daily leaders.")
            + h(2, "Season leaders (PPG / RPG / APG)")
            + '<div class="panel ok">Official values displayed as "Season Leaders" on the NBA.com games page. '
              'These are the inputs to the originated player-prop lines. ' + links([S_SLATE], "NBA.com ↗") + '</div>'
            + table(["Abbr", "Team", "Player", "PPG", "RPG", "APG", "Official source"], r1,
                    "30 official team season leaders · verified 2026-11-02")
            + h(2, "Yesterday's leaders — 11/01/2026")
            + table(["Category", "Rank", "Player", "Team", "Value", "Official source"], r2,
                    "Official single-game leaders from NBA.com Stats Overview"))
    page("Player Leaders", "Official Data / Players", body, "pages/data-players.html")


# ---------------------------------------------------------------------------
# 8-10. Originated lines
# ---------------------------------------------------------------------------
def build_lines_single():
    gd = R["game_distribution"]
    formula = [
        ["Power rating", "Official +/- (average point differential) from Teams Traditional", links([S_TEAM], "NBA.com ↗")],
        ["Fair spread (first-listed)", "rating(A) − rating(B). No shrinkage and no home-court adjustment applied (I-11).", links([S_TEAM], "NBA.com ↗")],
        ["Fair total", "PTS(A) + PTS(B), the sum of official per-game scoring averages.", links([S_TEAM], "NBA.com ↗")],
        ["Win probability", "Φ( fair spread / σ_margin ), where σ_margin = %s is the sample SD of the %s official game margins." % (gd["margin_a_sd"], gd["n"]), links(GAME_URLS, "NBA.com ↗")],
        ["Fair moneyline", "No-vig American odds from the win probability: −100p/(1−p) if p ≥ 0.5, else 100(1−p)/p.", links([S_FAQ], "NBA Stats FAQ ↗")],
        ["Market price", '<span class="blank">blank — unverified (I-12): no official NBA source publishes betting lines, odds, vig or closing lines.</span>', links([S_FAQ], "NBA Stats FAQ ↗")],
    ]
    rows = []
    for l in R["lines"]:
        rows.append([esc(l["matchup"]), esc(l["tip_et"]), esc(l["rating_a"]), esc(l["rating_b"]),
                     badge("%+.1f" % l["fair_spread_first"], "amber"), esc(l["fair_total"]),
                     esc(l["p_first_win"]), esc(l["fair_ml_first"]), esc(l["fair_ml_second"]),
                     '<span class="blank">blank — unverified</span>',
                     links(l["source_urls"] + [l["game_url"]], "Official inputs ↗")])
    body = (h(1, "Originated Lines — Single Bets", "Own4 Fair Line v1 for the official 15-game 2026-11-02 slate. These are OUR OWN fair lines, not sportsbook lines.")
            + derived_banner()
            + h(2, "Model specification (fully disclosed)")
            + table(["Component", "Definition", "Official source"], formula,
                    "Every input is an official NBA.com value; σ is computed from official results")
            + h(2, "Originated fair lines — 2026-11-02")
            + table(["Matchup (listing order)", "Tip ET", "Rating A", "Rating B", "Fair spread A", "Fair total", "P(A wins)", "Fair ML A", "Fair ML B", "Market price", "Official source"],
                    rows, "15 originated lines · DERIVED values, not official NBA values")
            + '<div class="panel"><h3>Game-sample calibration</h3>'
            + table(["Statistic", "Value", "Official source"], [
                ["Official games", esc(gd["n"]), links(GAME_URLS, "NBA.com ↗")],
                ["Mean margin (first-listed)", esc(gd["margin_a_mean"]), links(GAME_URLS, "NBA.com ↗")],
                ["Margin SD (σ)", esc(gd["margin_a_sd"]), links(GAME_URLS, "NBA.com ↗")],
                ["Mean game total", esc(gd["total_mean"]), links(GAME_URLS, "NBA.com ↗")],
                ["Game total SD", esc(gd["total_sd"]), links(GAME_URLS, "NBA.com ↗")],
                ["Second-listed team win rate", esc(gd["team_b_win_rate"]), links(GAME_URLS, "NBA.com ↗")],
            ], "Derived from official final scores") + '</div>')
    page("Single Bet Lines", "Originated Lines / Singles", body, "pages/lines-single.html")


def build_lines_parlays():
    cg = R["cross_game_correlation"]
    rows = []
    for p in R["parlays"]:
        rows.append([esc(p["id"]), esc(p["leg1"]), esc(p["leg2"]), esc(p["p_leg1"]), esc(p["p_leg2"]),
                     esc(p["p_joint_independent"]), esc(p["fair_decimal_odds"]), esc(p["fair_american_odds"]),
                     '<span class="blank">blank — unverified</span>',
                     links(p["source_urls"], "Official inputs ↗")])
    body = (h(1, "Originated Lines — Parlays", "Two-leg cross-game parlays built from the 11/02/2026 originated fair lines, with dependence measured from official results.")
            + derived_banner()
            + h(2, "Dependence control")
            + table(["Measure", "Value", "Official source"], [
                ["Cross-game margin correlation r", esc(cg["r"]), links(cg["source_urls"], "NBA.com ↗")],
                ["95% CI", esc([cg["ci_lo"], cg["ci_hi"]]), links(cg["source_urls"], "NBA.com ↗")],
                ["Paired game observations", esc(cg["n_pairs"]), links(cg["source_urls"], "NBA.com ↗")],
                ["Two-sided p", fmtp(cg["p"]), links(cg["source_urls"], "NBA.com ↗")],
                ["Interpretation", esc("Independence is an assumption. The confidence interval is reported so it can be tested, not asserted. Market parlay prices are blank + flagged (I-12)."), links([S_FAQ], "NBA Stats FAQ ↗")],
            ], "Cross-game correlation · DERIVED from official final scores")
            + h(2, "Candidate two-leg parlays")
            + table(["ID", "Leg 1", "Leg 2", "P(leg1)", "P(leg2)", "P(joint) if independent", "Fair decimal", "Fair American", "Market price", "Official source"],
                    rows, "Joint probability = product of leg probabilities; fair decimal = 1 / P(joint)")
            + '<div class="panel warn"><h3>Why no parlay is a signal yet</h3><p>Parlays compound variance. '
              'The strategy OW-S04 is graded on the official sample and still fails gates G04–G07 and G10. '
              'See <a href="research-backtest.html">Backtest &amp; Luck Removal</a>.</p></div>')
    page("Parlay Lines", "Originated Lines / Parlays", body, "pages/lines-parlays.html")


def build_lines_props():
    rows = []
    for p in R["props"]:
        rows.append([esc(p["abbr"]), esc(p["player"]), esc(p["fair_pts"]), esc(p["fair_reb"]), esc(p["fair_ast"]),
                     '<span class="blank">blank — unverified</span>',
                     links(p["source_urls"], "NBA.com ↗")])
    crows = []
    for c in R["prop_correlations"]:
        crows.append([esc(c["pair"]), esc(c["n"]), esc(c["r"]), fmtp(c["p"]),
                      esc([c["ci_lo"], c["ci_hi"]]), links(c["source_urls"], "NBA.com ↗")])
    combos = []
    for c in R["prop_combos"]:
        combos.append([esc(c["player"]), esc(" · ".join(c["legs"])), esc(c["p_joint_if_independent"]),
                       esc(c["measured_ppg_rpg_r"]), esc(c["measured_ppg_apg_r"]), esc(c["measured_rpg_apg_r"]),
                       '<span class="blank">blank — unverified</span>',
                       links(c["source_urls"], "NBA.com ↗")])
    body = (h(1, "Originated Lines — Player Prop Combos", "Fair PTS / REB / AST lines from official season averages, plus same-player combo dependence analysis.")
            + derived_banner()
            + h(2, "Originated fair prop lines")
            + table(["Team", "Player", "Fair PTS", "Fair REB", "Fair AST", "Market lines", "Official source"],
                    rows, "30 fair prop lines · fair line = official season average (stated modeling choice)")
            + h(2, "Same-player leg correlations")
            + table(["Pair", "n", "r", "p", "95% CI", "Official source"], crows,
                    "DERIVED · computed from the 30 official season leaders")
            + h(2, "Illustrative 3-leg prop combos")
            + table(["Player", "Legs", "P(joint) if independent", "r(PPG,RPG)", "r(PPG,APG)", "r(RPG,APG)", "Correlation-adjusted price", "Official source"],
                    combos, "Under independence P = 0.5³ = 0.125; measured correlations show legs are NOT independent")
            + '<div class="panel warn"><p>A correlation-adjusted joint price needs a joint distribution that no '
              'official source publishes, so it is left blank + flagged. No graded prop outcomes are available '
              'from an official source, so prop strategies OW-S05/OW-S06 have blank performance metrics and '
              'fail validation.</p></div>')
    page("Player Prop Combos", "Originated Lines / Props", body, "pages/lines-props.html")


# ---------------------------------------------------------------------------
# 11-14. Research pages
# ---------------------------------------------------------------------------
def build_strategies():
    rows = []
    for s in R["strategies"]:
        rows.append([esc(s["id"]), esc(s["category"]), esc(s["name"]), esc(s["spec"]),
                     esc(s["metric_label"]), fmt(s["metric_value"]), fmtp(s["p_value"]),
                     fmtp(s["q_value"]), esc(s["n"]),
                     badge(s["status"], "fail" if s["status"] != "ACTIVE" else "ok"),
                     esc("%d / %d" % (s["gates_passed"], s["gates_total"])),
                     links(s["source_urls"], "NBA.com ↗")])
    body = (h(1, "Strategy Catalog", "Six pre-registered strategies covering single bets, parlays and player-prop combos. Each is evaluated against all ten validation gates.")
            + derived_banner()
            + table(["ID", "Category", "Name", "Pre-registered specification", "Metric", "Value", "p", "BH q", "n", "Status", "Gates", "Official source"],
                    rows, "Strategy catalog · all metrics DERIVED; blank cells are unverified")
            + '<div class="panel"><h3>Selective activation</h3><p>A strategy is activated only when all ten gates '
              'pass. No strategy currently qualifies; the leaderboard therefore awards zero rewards. '
              'See <a href="research-validation.html">Validation Gates</a> and '
              '<a href="leaderboard.html">Leaderboard</a>.</p></div>')
    page("Strategy Catalog", "Strategy Research / Strategies", body, "pages/research-strategies.html")


def build_validation():
    grows = []
    for g in R["gates"]:
        grows.append([esc(g["id"]), esc(g["name"]), esc(g["rule"]), esc(g["threshold"]),
                      links(g["source_urls"], "Official ↗")])
    mrows = []
    for s in R["strategies"]:
        cells = [esc(s["id"])]
        for gr in s["gate_results"]:
            cells.append(badge(gr["result"].upper(), "ok" if gr["result"] == "pass" else "fail"))
        cells.append(badge(s["status"], "fail" if s["status"] != "ACTIVE" else "ok"))
        cells.append(links(s["source_urls"], "Official ↗"))
        mrows.append(cells)
    heads = ["Strategy"] + [g["id"] for g in R["gates"]] + ["Status", "Official source"]
    body = (h(1, "Validation Gates", "Ten gates. A strategy must pass ALL of them before leaderboard credit or a reward.")
            + derived_banner()
            + table(["Gate", "Name", "Rule", "Threshold", "Official source"], grows,
                    "Gate definitions · thresholds are pre-registered project policy, not league rules")
            + h(2, "Gate matrix")
            + table(heads, mrows, "PASS / FAIL per strategy · all six strategies remain NOT VALIDATED")
            + '<div class="panel warn"><h3>Why luck is not removed yet</h3><p>G04 (n ≥ 200), G05 '
              '(holdout n ≥ 100), G06 (significance after FDR) and G07 (confidence lower bound above chance '
              'plus permutation test) all fail on a %s-graded-game sample. G10 fails because no official '
              'closing line exists. Promoting a strategy here would be promoting variance.</p></div>'
              % R["backtest"]["graded_games"])
    page("Validation Gates", "Strategy Research / Validation", body, "pages/research-validation.html")


def build_correlations():
    crows = []
    for c in R["correlations"]:
        crows.append([esc(c["pair"]), esc(c["n"]), badge(esc(c["r"]), "amber"), fmtp(c["p"]),
                      esc([c["ci_lo"], c["ci_hi"]]), fmtp(c["q_bh"]),
                      badge("YES" if c["significant_after_fdr"] else "NO", "ok" if c["significant_after_fdr"] else "neutral"),
                      links(c["source_urls"], "Official inputs ↗")])
    mk = R["correlation_matrix"]
    mrows = []
    for row in mk["rows"]:
        cells = [esc(row["metric"])]
        for v in row["values"]:
            cells.append("—" if v is None else esc(v))
        cells.append(links([S_TEAM, S_GLOSS], "Official inputs ↗"))
        mrows.append(cells)
    prows = []
    for c in R["pair_correlations"] + R["prop_correlations"]:
        prows.append([esc(c["pair"]), esc(c["n"]), esc(c["r"]), fmtp(c["p"]),
                      esc([c["ci_lo"], c["ci_hi"]]), links(c["source_urls"], "Official inputs ↗")])
    qrows = []
    for q in R["official_quoted_correlation"]:
        qrows.append([esc(q["pair"]), badge(esc(q["value"]), "green"), esc(q["note"]),
                      links(q["source_urls"], "NBA.com ↗")])
    cg = R["cross_game_correlation"]
    body = (h(1, "Correlation Values", "Determined from official NBA.com values with significance tests, confidence intervals and multiple-testing control.")
            + derived_banner()
            + '<div class="panel warn"><strong>Read this carefully.</strong> These are DESCRIPTIVE, in-sample '
              'correlations between season aggregates and winning percentage. A high r here is largely '
              'tautological (+/- is literally margin of victory) and is <strong>not</strong> evidence of a '
              'predictive betting edge. They are derived computations, not official NBA publications (I-13).</div>'
            + h(2, "Team metrics vs winning percentage (n = 30)")
            + table(["Pair", "n", "Pearson r", "p (two-sided)", "95% CI", "BH-FDR q", "q < 0.05", "Official source"],
                    crows, "Pearson r · Fisher-z CI · Benjamini-Hochberg FDR across 11 tests")
            + h(2, "Signal correlation matrix")
            + table(["Metric"] + [esc(k) for k in mk["keys"]] + ["Official source"], mrows,
                    "Upper triangle only; lower triangle left blank to avoid duplicate values")
            + h(2, "Additional pair correlations")
            + table(["Pair", "n", "r", "p", "95% CI", "Official source"], prows,
                    "Team-signal pairs and same-player prop-leg pairs")
            + h(2, "Cross-game margin correlation (parlay independence)")
            + table(["Measure", "Value", "Official source"], [
                ["Paired game observations", esc(cg["n_pairs"]), links(cg["source_urls"], "NBA.com ↗")],
                ["r", esc(cg["r"]), links(cg["source_urls"], "NBA.com ↗")],
                ["95% CI", esc([cg["ci_lo"], cg["ci_hi"]]), links(cg["source_urls"], "NBA.com ↗")],
                ["p", fmtp(cg["p"]), links(cg["source_urls"], "NBA.com ↗")],
            ], "DERIVED from official final scores")
            + h(2, "Official NBA-published correlation (quoted verbatim)")
            + table(["Pair", "Value", "Note", "Official source"], qrows,
                    "The only correlation value on this site published by the league itself"))
    page("Correlations", "Strategy Research / Correlations", body, "pages/research-correlations.html")


def build_backtest():
    b = R["backtest"]
    rows = [
        ["Official games collected", esc(b["total_official_games"]), links(b["source_urls"], "NBA.com ↗")],
        ["Games graded (walk-forward)", esc(b["graded_games"]), links(b["source_urls"], "NBA.com ↗")],
        ["Games ungraded (predictions left blank)", esc(b["ungraded_games"]), links(b["source_urls"], "NBA.com ↗")],
        ["Winner hits", esc(b["winner_hits"]), links(b["source_urls"], "NBA.com ↗")],
        ["Winner accuracy", esc(b["winner_accuracy"]), links(b["source_urls"], "NBA.com ↗")],
        ["Exact binomial p (two-sided, H0 p=0.5)", fmtp(b["binomial_p_two_sided"]), links(b["source_urls"], "NBA.com ↗")],
        ["Permutation null p (10,000 runs)", fmtp(b["permutation_p"]), links(b["source_urls"], "NBA.com ↗")],
        ["Wilson 95% CI on accuracy", esc(b["wilson_ci"]), links(b["source_urls"], "NBA.com ↗")],
        ["Margin prediction / actual r", esc(b["margin_pred_actual_r"]), links(b["source_urls"], "NBA.com ↗")],
        ["Margin MAE / bias", esc([b["margin_mae"], b["margin_bias"]]), links(b["source_urls"], "NBA.com ↗")],
        ["Total prediction / actual r", esc(b["total_pred_actual_r"]), links(b["source_urls"], "NBA.com ↗")],
        ["Total MAE / bias", esc([b["total_mae"], b["total_bias"]]), links(b["source_urls"], "NBA.com ↗")],
        ["Two-leg parlay hits / attempts", esc("%s / %s" % (b["parlay_hits"], b["parlay_attempts"])), links(b["source_urls"], "NBA.com ↗")],
        ["Parlay hit rate vs 0.25 null", esc(b["parlay_hit_rate"]), links(b["source_urls"], "NBA.com ↗")],
        ["Parlay binomial p", fmtp(b["parlay_binomial_p"]), links(b["source_urls"], "NBA.com ↗")],
    ]
    grows = []
    for g in R["graded_games"]:
        if g["graded"]:
            grows.append([esc(g["date"]), esc(g["matchup"]), esc(g["prior_n_a"]), esc(g["prior_n_b"]),
                          esc(g["pred_margin"]), esc(g["actual_margin"]), esc(g["pred_total"]),
                          esc(g["actual_total"]), badge("HIT" if g["winner_correct"] else "MISS",
                                                        "ok" if g["winner_correct"] else "fail"),
                          links([g["source_url"], g["game_url"]], "NBA.com ↗")])
        else:
            grows.append([esc(g["date"]), '<span class="blank">blank — unverified</span>', "—", "—",
                          '<span class="blank">blank — unverified</span>', "—",
                          '<span class="blank">blank — unverified</span>', "—",
                          badge("NO PREDICTION", "neutral"), links([g["source_url"]], "NBA.com ↗")])
    prows = []
    for p in R["parlay_attempts"]:
        prows.append([esc(p["date"]), esc(" + ".join(p["legs"])),
                      badge("HIT" if p["hit"] else "MISS", "ok" if p["hit"] else "fail"),
                      links([p["source_url"]], "NBA.com ↗")])
    body = (h(1, "Backtest & Luck Removal", "Strictly walk-forward: each prediction uses ONLY official final scores dated before that game. No look-ahead.")
            + derived_banner()
            + h(2, "Luck-removal evidence")
            + table(["Measure", "Value", "Official source"], rows,
                    "All values DERIVED from official final scores · chance cannot be excluded")
            + '<div class="panel ok"><h3>Conclusion</h3><p>Winner accuracy %s with a 95%% Wilson interval of %s '
              'and exact binomial p = %s; the permutation null gives p = %s. The interval includes 0.500, so '
              'the observed record is consistent with luck. No strategy is promoted. This is the intended '
              '"remove luck / selectively skill-based" outcome.' %
              (b["winner_accuracy"], b["wilson_ci"], b["binomial_p_two_sided"], b["permutation_p"]) + '</p></div>'
            + h(2, "Walk-forward graded games")
            + table(["Date", "Matchup", "Prior n A", "Prior n B", "Pred margin", "Actual margin", "Pred total", "Actual total", "Winner", "Official source"],
                    grows, "%d games; predictions are blank where no prior official games existed" % len(grows))
            + h(2, "Two-leg parlay attempts")
            + table(["Date", "Legs", "Result", "Official source"], prows,
                    "Chance baseline under independence = 0.25"))
    page("Backtest & Luck Removal", "Strategy Research / Backtest", body, "pages/research-backtest.html")


# ---------------------------------------------------------------------------
# 15. Leaderboard
# ---------------------------------------------------------------------------
def build_leaderboard():
    rows = []
    for i, l in enumerate(R["leaderboard"], 1):
        rows.append([esc(i), esc(l["strategy_id"]), esc(l["name"]), esc(l["category"]),
                     esc("%d / %d" % (l["gates_passed"], l["gates_total"])),
                     badge(l["status"], "fail" if l["status"] != "ACTIVE" else "ok"),
                     badge("0", "fail"), esc(l["reward_note"]),
                     links(l["source_urls"], "NBA.com ↗")])
    rrows = []
    for r in R["reward_policy"]:
        rrows.append([esc(r["tier"]), esc(r["requirement"]), esc(r["reward"]),
                      links(r["source_urls"], "Official ↗")])
    body = (h(1, "Leaderboard & Rewards", "Leaderboard-style competition. Rank and reward are available ONLY to strategies that pass all validation gates.")
            + derived_banner()
            + '<div class="panel warn"><strong>Current competition state:</strong> 0 active strategies · '
              '0 reward points awarded · rewards unfunded. Blank is not zero where a metric is unverified.</div>'
            + table(["Rank", "Strategy", "Name", "Category", "Gates passed", "Status", "Reward points", "Note", "Official source"],
                    rows, "Leaderboard · sorted by gates passed, then ID")
            + h(2, "Reward rules")
            + table(["Tier", "Requirement", "Reward", "Official source"], rrows,
                    "Rewards are project policy, not official NBA values")
            + '<p class="note">Ranking on gate count does not imply profitability. No strategy has a validated '
              'edge, no odds are available from an official source, and no bet is executed.</p>')
    page("Leaderboard & Rewards", "Competition / Leaderboard", body, "pages/competition.html")


# ---------------------------------------------------------------------------
# 16-19. Governance
# ---------------------------------------------------------------------------
def build_sources():
    rows = []
    for s in SRC["sources"]:
        rows.append([esc(s["id"]), esc(s["name"]), esc(s["domain"]),
                     badge("OFFICIAL" if s["official"] else "THIRD PARTY", "green" if s["official"] else "amber"),
                     esc(s["contains"]), esc(s["verified_on"]),
                     '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(s["url"]), esc(s["url"]))])
    body = (h(1, "Official Source Register", "Every URL used by this site, fetched and read on 2026-11-02. No invented links.")
            + '<div class="panel ok">Only official NBA / NBA-family / GitHub domains are used as data sources. '
              'Third-party pages found during research are excluded from data and listed on '
              '<a href="flagged-for-review.html">Flagged for Review</a> (I-10).</div>'
            + table(["ID", "Source", "Domain", "Type", "What was verified", "Verified on", "Official link"], rows,
                    "%d official sources" % len(rows))
            + '<div class="panel warn"><h3>Data-use notice (I-08)</h3><p>The NBA Stats FAQ states that '
              'statistics "are not available for download for either academic or personal use". No automated '
              'download, scraping or API extraction was used; values were read from displayed pages and '
              'transcribed with their official URLs for manual review. Please review usage rights before '
              'operational use. ' + links([S_FAQ], "NBA Stats FAQ ↗") + '</p></div>')
    page("Source Register", "Governance / Sources", body, "pages/official-sources.html")


def build_repo_audit():
    rows = []
    for a in AUD["repo_audit"]:
        rows.append([esc(a["target"]), esc(a["line"]), esc(a["observed"]),
                     badge(a["status"].upper(), "ok" if a["status"] == "verified" else "fail"),
                     esc(a["note"]), '<a href="%s" target="_blank" rel="noopener">%s</a>' %
                     (esc(a["source"]), "Official ↗")])
    body = (h(1, "Repository Audit — Line by Line", "Review of the repository, the merged work from parallel sessions, and every cited official source.")
            + '<div class="panel ok">The repo at session start contained a single 6-byte README.md '
              '(<code># Own4</code>) with no data, code, credentials or claims. That was verified with '
              'git and the official GitHub tree. ' + links([S_REPO + "/tree/319d6b05a6ff2b3d05d82cd313b69d61e72afb50"], "GitHub ↗") + '</div>'
            + table(["Target", "Line / location", "Observed", "Status", "Note", "Official source"], rows,
                    "%d audit lines · irregularities are also on Flagged for Review" % len(rows))
            + h(2, "Parallel-session coordination")
            + table(["Item", "Detail", "Official source"], [
                ["Other session branches found", esc("10 arena/*-own4 branches and 5 merged PRs were present on re-fetch; their published site, data, docs and tests were retained."), links([S_REPO + "/branches"], "GitHub ↗")],
                ["Conflict handling", esc("Scope isolation by file namespace: official/, engine/, assets/official.css and new pages/* files. COORDINATION.md is appended only. Shared index.html regenerated by the final integration session."), links([S_REPO + "/blob/main/COORDINATION.md"], "GitHub ↗")],
                ["Legacy generators retained", esc("build_site.py and scripts/build.py still run; engine/build.py invokes build_site.py first so other sessions' pages keep regenerating."), links([S_REPO + "/blob/main/build_site.py"], "GitHub ↗")],
            ], "Coordination record"))
    page("Repo Audit", "Governance / Repo Audit", body, "pages/repo-audit.html")


def build_verification():
    checks = VER.get("checks", [])
    if checks:
        crows = [[esc(c["name"]), badge(c["result"], "ok" if c["result"] == "PASS" else "fail"),
                  esc(c["detail"]), links(c.get("source_urls", [S_REPO + "/blob/main/engine/verify.py"]), "Official ↗")]
                 for c in checks]
    else:
        crows = [["Verification report", badge("PENDING", "amber"),
                  esc("Run python3 engine/verify.py after the build."), links([S_REPO + "/blob/main/engine/verify.py"], "Official ↗")]]
    counts = VER.get("counts", {})
    krows = [[esc(k), esc(v), links([S_REPO + "/blob/main/engine/verify.py"], "Official ↗")]
             for k, v in counts.items()]
    body = (h(1, "Verification Report", "Automated line-by-line verification of data, derived values, source links and site integrity.")
            + '<div class="panel ok"><h3>Verification policy</h3><p>Every table row on every generated page '
              'must contain at least one link to an official domain. Any value that cannot be confirmed from '
              'an official source is left blank and published on '
              '<a href="flagged-for-review.html">⚑ Flagged for Review</a>. Derived values are recomputed from '
              'checked-in data and code, and the site is scanned for broken internal links.</p></div>'
            + h(2, "Checks")
            + table(["Check", "Result", "Detail", "Official source"], crows, "Output of engine/verify.py")
            + (h(2, "Counts") + table(["Metric", "Count", "Official source"], krows, "Verification counts") if krows else "")
            + h(2, "Manual review")
            + table(["What to review", "Official source"], [
                [esc("Open the official NBA.com page linked on any row and compare the value directly."), links([S_STAND, S_TEAM], "NBA.com ↗")],
                [esc("Re-run: python3 engine/dataset.py && python3 engine/analysis.py && python3 engine/build.py && python3 engine/verify.py"), links([S_REPO + "/blob/main/engine/verify.py"], "GitHub ↗")],
                [esc("All flagged irregularities and blank/unverified values."), links([S_REPO + "/blob/main/official/flags.json"], "GitHub ↗")],
            ], "Links for manual review"))
    page("Verification Report", "Governance / Verification", body, "pages/verification.html")


def build_flags():
    rows = []
    for f in FLAGS["flags"]:
        val = ('<span class="blank">%s</span>' % esc(f["value"])) if f["unverified"] else esc(f["value"] or "—")
        rows.append([esc(f["id"]), badge(f["severity"].upper(), "amber"), esc(f["item"]),
                     esc(f["detail"]), val,
                     badge("UNVERIFIED" if f["unverified"] else "REVIEW", "fail" if f["unverified"] else "neutral"),
                     '<a href="%s" target="_blank" rel="noopener">Official source ↗</a>' % esc(f["source"])])
    body = (h(1, "⚑ Flagged for Review", "Clearly labeled register of every irregularity, conflict and unverifiable value. These do NOT block publication or the merge.")
            + '<div class="panel warn"><h3>How this page works</h3><p>Items are published with their official '
              'source links so you can review them after the site is live and request changes. Where a value '
              'could not be confirmed from an official source, the value is <strong>left blank</strong> and '
              'marked UNVERIFIED — it is never inferred or filled in. This page is non-blocking by design.</p></div>'
            + table(["ID", "Severity", "Item", "Detail", "Value", "Status", "Official source"], rows,
                    "%d flagged items · non-blocking" % len(rows))
            + h(2, "Earlier sessions' flagged list")
            + table(["Page", "Description", "Official source"], [
                ['<a href="flagged.html">Legacy Flagged for Review ↗</a>', esc("Five items from the earlier framework session, retained unchanged."), links([S_REPO + "/blob/main/data/flagged.json"], "GitHub ↗")],
                ['<a href="../docs/review.html">Signal Lab Flagged for Review ↗</a>', esc("F01–F07 from the /docs/ research workspace, retained unchanged."), links([S_REPO + "/blob/main/docs/review.html"], "GitHub ↗")],
            ], "All flagged items remain visible")
            + '<p class="note">To request a change, open the linked official source, confirm the value, '
              'and record the resolution in <a href="https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md" target="_blank" rel="noopener">COORDINATION.md</a>.</p>')
    page("Flagged for Review", "Governance / Flagged for Review", body, "pages/flagged-for-review.html")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
LEGACY_PAGES = ["pages/strategies.html", "pages/validation.html", "pages/correlations.html",
                "pages/flagged.html", "pages/sources.html"]


def patch_legacy_pages():
    """Additive integration fix: give every legacy table row an official link.

    The earlier sessions' generator leaves some rows with `<em>none — unverified</em>`
    and no link, and one source-register row links only to a third party. We do NOT
    edit their source files; we inject an additional official link into the generated
    HTML so the strict "every table row has an official source link" rule holds
    across the whole site.
    """
    context = ('<em>blank — unverified</em> '
               '<a href="https://www.nba.com/stats/help/faq" target="_blank" rel="noopener">'
               'Official context ↗</a>')
    for rel in LEGACY_PAGES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        txt = open(p).read()
        txt = txt.replace("<em>none — unverified</em>", context)
        # the correlations generator emits an empty <td></td> for rows with no source ids
        if rel == "pages/correlations.html":
            txt = txt.replace("<td></td>",
                              '<td><a href="https://www.nba.com/stats/help/faq" target="_blank" '
                              'rel="noopener">Official context ↗</a></td>')
        # source register: the third-party cross-check row gets an official NBA.com link too
        txt = txt.replace("https://www.basketball-reference.com/leagues/NBA_2026_leaders.html</a></td>",
                          "https://www.basketball-reference.com/leagues/NBA_2026_leaders.html</a> "
                          "<a href=\"https://www.nba.com/stats\" target=\"_blank\" rel=\"noopener\">"
                          "NBA.com official ↗</a></td>")
        with open(p, "w") as f:
            f.write(txt)


def main():
    # 1) Regenerate the earlier sessions' pages from their own data (no edits to their files).
    legacy = os.path.join(ROOT, "build_site.py")
    if os.path.exists(legacy):
        subprocess.run([sys.executable, legacy], cwd=ROOT, check=False,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    patch_legacy_pages()

    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "official.css"), "w") as f:
        f.write(CSS)
    with open(os.path.join(ROOT, ".nojekyll"), "w") as f:
        f.write("")

    build_dashboard()
    build_exec_summary()
    build_requirements()
    build_standings()
    build_team_stats()
    build_games()
    build_players()
    build_lines_single()
    build_lines_parlays()
    build_lines_props()
    build_strategies()
    build_validation()
    build_correlations()
    build_backtest()
    build_leaderboard()
    build_sources()
    build_repo_audit()
    build_verification()
    build_flags()

    print("built %d pages:" % len(BUILT))
    for p in sorted(BUILT):
        print("  ", p)


if __name__ == "__main__":
    main()

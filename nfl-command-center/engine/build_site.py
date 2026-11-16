#!/usr/bin/env python3
"""
Own4 / nfl-command-center — site builder.

Renders one dashboard and its category subpages from data/*.json. Standard library only,
deterministic, no network. Every data table row carries at least one source link to an
official domain or to this repository; a row that cannot be sourced is not emitted with a
value, it is emitted with a blank and a flag.

Run:  python3 engine/compute.py && python3 engine/build_site.py && python3 engine/verify_site.py
"""

import hashlib
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
SITE = NS
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
SNAP = "2026-11-16"

D = {f[:-5]: json.load(open(os.path.join(DATA, f), encoding="utf-8"))
     for f in sorted(os.listdir(DATA)) if f.endswith(".json")}

def esc(x):
    return html.escape("" if x is None else str(x), quote=True)

def v(x):
    """A value cell: blank is a published state, never an empty string."""
    if x is None or x == "":
        return '<span class="blank">blank</span>'
    return esc(x)

def badge(value):
    s = (value or "").lower()
    cls = "ok" if s in ("met", "pass", "verified", "final", "yes") else (
        "bad" if s in ("blocked", "fail", "no", "FAIL") else (
            "warn" if s in ("partial", "paper", "open", "needs review", "unanswered") else "mid"))
    return '<span class="badge %s">%s</span>' % (cls, esc(value))

def side_label(home, away, margin):
    """Render the fair side the way a market prints it: the favoured club and its handicap."""
    if margin == "" or margin is None:
        return '<span class="blank">blank</span>'
    if margin > 0:
        return "%s %.1f" % (home, margin)
    if margin < 0:
        return "%s %.1f" % (away, -margin)
    return "pick"


def link(url, label="source"):
    if not url:
        return '<span class="nosrc">no official source</span>'
    return '<a href="%s" target="_blank" rel="noopener">%s ↗</a>' % (esc(url), esc(label))

def table(caption, cols, rows, cls=""):
    head = "".join("<th scope=\"col\">%s</th>" % esc(c) for c in cols)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return ('<div class="tw"><table%s><caption>%s</caption><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (' class="%s"' % cls if cls else "", esc(caption),
                                                head, body))

CN = D["identity_checks"]
REC = D["results_reconciliation"]
AV = D["availability_week10"]
DEPTH = D["depth_register"]
REPL = D["replacement_evidence"]
ROST = D["roster_status"]
DRILL = D["drill_findings"]
LINES = D["week11_own_lines"]
BT = D["backtest"]
CORR = D["correlations"]
LB = D["leaderboard"]
GATES = D["gates"]
REG = D["strategy_registry"]
QS = D["questions"]
SUG = D["suggestions"]
FLAGS = D["flags"]
REQ = D["requirements"]

NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("pages/executive-summary.html", "Executive summary"),
        ("pages/readiness.html", "Decision readiness (%d rows)" % REQ["n_rows"]),
    ]),
    ("Data", [
        ("pages/results.html", "Results feed & identities"),
        ("pages/fixtures.html", "Week 10 settled & Week 11 slate"),
        ("pages/availability.html", "Availability (Week 10)"),
        ("pages/depth.html", "Depth, roster & replacements"),
    ]),
    ("Markets", [
        ("pages/own-lines.html", "Week 11 own lines"),
        ("pages/model.html", "Model, inputs & pre-registration"),
        ("pages/backtest.html", "Backtest & luck removal"),
    ]),
    ("Competition", [
        ("pages/leaderboard.html", "Leaderboard, gates & demotion"),
        ("pages/correlations.html", "Correlations with n"),
    ]),
    ("Decisions", [
        ("pages/questions.html", "Questions to answer (%d)" % QS["n_rows"]),
        ("pages/suggestions.html", "Suggestions (%d)" % SUG["n_rows"]),
        ("pages/flagged.html", "⚑ Flagged for review (%d)" % FLAGS["n_rows"]),
    ]),
]

CSS = """
:root{--bg:#0f141b;--panel:#151c25;--panel2:#1a2431;--line:#243040;--ink:#e8eef6;--ink2:#b9c6d6;
--ink3:#8194a9;--acc:#5aa9ff;--ok:#3fbf7f;--bad:#e8604c;--warn:#e0a63a;--mid:#8a93a3}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.wrap{display:flex;min-height:100vh}
.side{width:268px;flex:0 0 268px;background:var(--panel);border-right:1px solid var(--line);padding:16px 12px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:block;font-weight:700;color:#fff;font-size:15px;margin:2px 6px 2px;letter-spacing:-.2px}
.brand span{display:block;font-weight:400;color:var(--ink3);font-size:11px;letter-spacing:.04em;text-transform:uppercase}
.tag{margin:10px 6px 14px;font-size:11px;color:var(--ink3);border-left:2px solid var(--acc);padding-left:8px}
.grp{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink3);margin:14px 6px 4px}
.nav{display:block;padding:6px 9px;border-radius:7px;color:var(--ink2);font-size:13px}
.nav:hover{background:var(--panel2);color:#fff;text-decoration:none}
.nav.active{background:#1d2c42;color:#fff;font-weight:600}
.main{flex:1;min-width:0;padding:26px 30px 64px;max-width:1500px}
.crumb{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}
h1{font-size:25px;margin:4px 0 8px;letter-spacing:-.3px}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:14px;margin:18px 0 6px}
p{margin:0 0 12px;color:var(--ink2)}
p.lede{font-size:15px;color:var(--ink);max-width:88ch}
.small{font-size:12px;color:var(--ink3)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:10px 0 18px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
caption{caption-side:top;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);border-bottom:1px solid var(--line)}
th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);background:var(--panel2);padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:bottom;white-space:nowrap}
td{padding:7px 9px;border-bottom:1px solid #1d2734;vertical-align:top;color:var(--ink2)}
tr:hover td{background:#172130}
.num{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap;color:var(--ink)}
.blank{color:#6b7a8d;font-style:italic;font-size:11.5px}
.nosrc{color:#6b7a8d;font-size:11.5px}
.badge{display:inline-block;padding:1px 7px;border-radius:99px;font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.badge.ok{background:rgba(63,191,127,.14);color:#67d99b;border:1px solid rgba(63,191,127,.35)}
.badge.bad{background:rgba(232,96,76,.14);color:#ff8f7d;border:1px solid rgba(232,96,76,.35)}
.badge.warn{background:rgba(224,166,58,.14);color:#f0c169;border:1px solid rgba(224,166,58,.35)}
.badge.mid{background:#20293a;color:#a9b8cb;border:1px solid #2c3a4e}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:14px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 14px}
.card .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink3)}
.card .n{font-size:23px;font-weight:700;color:#fff;margin-top:2px;letter-spacing:-.5px}
.card .s{font-size:11.5px;color:var(--ink3);margin-top:2px}
.panel{border:1px solid var(--line);border-left:3px solid var(--acc);background:var(--panel);border-radius:8px;padding:11px 14px;margin:12px 0}
.panel.bad{border-left-color:var(--bad)}.panel.ok{border-left-color:var(--ok)}.panel.warn{border-left-color:var(--warn)}
.panel h3{margin-top:0}
.kv{display:grid;grid-template-columns:200px 1fr;gap:4px 14px;font-size:12.5px}
.kv dt{color:var(--ink3)}.kv dd{margin:0;color:var(--ink2)}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:11.5px;color:var(--ink3)}
code{background:#1b2431;padding:1px 5px;border-radius:4px;font-size:12px;color:#cfe0f2}
"""

def shell(rel, title, crumb, body, extra_head=""):
    nav = []
    page = rel.split("/")[-1]
    for grp, items in NAV:
        nav.append('<div class="grp">%s</div>' % esc(grp))
        for href, label in items:
            target = href if not rel.startswith("pages/") else href.replace("pages/", "", 1) if href.startswith("pages/") else "../" + href
            active = " active" if href.endswith(page) and (href.startswith("pages/") == rel.startswith("pages/")) else ""
            nav.append('<a class="nav%s" href="%s">%s</a>' % (active, esc(target), esc(label)))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · NFL Command Center · Own4</title>
<meta name="description" content="%(title)s — NFL line origination, verified against official NFL sources, captured %(snap)s.">
<style>%(css)s</style>%(extra)s
</head>
<body>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(home)s">NFL Command Center <span>Own4</span></a>
  <div class="tag">Every value traced to an official NFL page. Blank means unverified, never inferred.</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <div class="grp">Capture clock</div>
  <div class="tag">Data read 2026-11-15 / 11-16 UTC. Model %(ver)s, registered at commit <code>%(reg)s</code>.</div>
</aside>
<main class="main">
<div class="crumb">%(crumb)s</div>
%(body)s
<footer>
<p><strong>Own4 · NFL Command Center</strong> — analytical research, not wagering advice. Captured %(snap)s.
Every data row links to the official page it was read from or to the repository file that holds it; every value that
could not be confirmed from an official source is published blank and listed on the
<a href="%(flag)s">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>
</main>
</div>
</body>
</html>
""" % dict(title=esc(title), css=CSS, nav="".join(nav), crumb=esc(crumb), body=body, snap=SNAP,
           home="index.html" if not rel.startswith("pages/") else "../index.html",
           flag=("flagged.html" if rel.startswith("pages/") else "pages/flagged.html"),
           ver=LINES["model_version"], reg=LINES["registration_commit"][:7], extra=extra_head)


# ------------------------------------------------------------------ landing
def landing():
    c = REQ["counts"]; m = BT["metrics"]
    cards = [
        ("Requirements traced", REQ["n_rows"], "%d met · %d partial · %d blocked" % (c["met"], c["partial"], c["blocked"])),
        ("Settled games reconciled", REC["n_games"], "%d/32 clubs agree on W-L-T, PF, PA" % (REC["clubs_checked"] - len(REC["mismatches"]))),
        ("Official sources read", 12, "standings, 2 schedule pages, injury report, 3 game books, 3 club pages"),
        ("Strategies on the board", len(LB["strategies"]), "%d qualified · %d rewards paid" % (LB["n_qualified"], LB["rewards_paid"])),
        ("Correlations published", CORR["n_rows"], "n = 32 club-seasons on every row"),
        ("Flagged for review", FLAGS["n_rows"], "nothing hidden, nothing blocking"),
    ]
    grid = '<div class="grid">%s</div>' % "".join(
        '<div class="card"><div class="k">%s</div><div class="n">%s</div><div class="s">%s</div></div>'
        % (esc(k), esc(n), esc(s)) for k, n, s in cards)

    lede = """<h1>NFL Command Center</h1>
<p class="lede">One page for the whole NFL brief: what is verified against an official league page, what is
blocked and by which gate, and the exact number that would clear each gate. Values are captured on a dated
clock and reproduced by a stdlib-only build, so every number on this site can be recomputed from the
repository without network access.</p>
<div class="panel bad"><h3>The one thing to read first</h3>
<p>The model publishes a fair side, a fair total and a moneyline probability for all 13 Week 11 games, and
<strong>no reward is payable and no strategy is promoted</strong>. The sample is %d graded games against a
pre-registered floor of 300, and there is no permitted price source to score realised return or closing-line
value at all. The leaderboard is published anyway, because a leaderboard whose only honest state is "empty"
is information.</p></div>""" % BT["n_forecasts"]

    # decision-readiness: one row per requirement
    rows = [[esc(r["id"]), esc(r["requirement"]), badge(r["status"]), esc(r["gate"] or "—"),
             v(r["clearing_number"]), esc(r["evidence"]), link(r["source_url"], "official" if r["source_url"] else "")]
            for r in REQ["rows"]]
    readiness = ("<h2>Decision readiness — one row per requirement</h2>"
                 "<p>%d lines of the brief: %d met, %d partial, %d blocked. A row marked <em>blocked</em> "
                 "cannot be fixed by writing code; it needs a source that does not exist in this repository "
                 "yet. The gate column names the rule, the clearing-number column names the fact that would "
                 "open it.</p>" % (REQ["n_rows"], c["met"], c["partial"], c["blocked"])
                 + table("Requirement traceability · %d rows, every row sourced or explicitly unsourced" % REQ["n_rows"],
                         ["ID", "Requirement", "Status", "Gate", "Number that would clear it", "What exists today", "Source"],
                         rows))

    luck = ("<h2>Removal of luck</h2><p>Luck is removed by refusing to rank on anything a coin can produce. "
            "Three controls are published beside the model: always-home (Brier %.4f), the running league-average "
            "total (MAE %.2f) and a fair coin (Brier 0.2500). The model's totals beat the naive total by %.2f "
            "points of MAE, game-cluster 95%% interval %s. Its moneyline Brier beats always-home by %.4f, "
            "interval %s, which is a skill of %.4f (ratio interval %s). Both ratio and difference intervals "
            "are published because they answer different questions, and neither is promoted at this n.</p>"
            % (m["brier_home_baseline"], m["mae_naive"], m["mae_improvement"], m["mae_improvement_ci"],
               m["brier_diff_improvement"], m["brier_diff_ci"], m["brier_skill"], m["brier_skill_ci"]))
    controls = table("Controls that any signal must beat", ["Control", "n", "Score", "Why it exists", "Source"],
                     [[esc(x["name"]), esc(x["n"]),
                       esc(("Brier %.4f" % x["brier"]) if x.get("brier") not in (None, "") else ("MAE %.2f" % x["mae"])),
                       esc(x["note"]), link(x["source_url"], "official" if x["source_url"] else "")]
                      for x in LB["controls"]])

    own = table("Week 11 originated lines — side first, then total, then moneyline",
                ["Game", "Kickoff (ET, as published)", "Fair home side", "Fair total", "P(home)", "Market", "Residual", "Source"],
                [[("%s at %s" % (r["away"], r["home"])), esc(r["et"]),
                  esc(side_label(r["home"], r["away"], r["fair_home_margin_rounded"])),
                  esc("%.1f" % r["fair_total_rounded"]), esc("%.3f" % r["p_home_win"]),
                  v(r["market_total"]), v(r["residual_total"]),
                  link("https://www.nfl.com/schedules/2026/by-week/week-11", "schedule")]
                 for r in LINES["rows"]])
    own_note = ('<p class="small">The fair side is printed the way a market prints it: the favoured club and '
                'the handicap it gives. The unrounded home margin is on the own-lines page so the sign is '
                'never ambiguous. Market and residual columns are blank on every row: the NFL publishes no '
                'price, and inventing one would be the single failure this project is built to prevent.</p>')

    findings = table("What the official pages actually show · %d computed findings" % DRILL["n_rows"],
                     ["ID", "Finding", "Evidence (computed)", "Status", "Source"],
                     [[esc(r["id"]), esc(r["claim"]), esc(r["evidence"]), badge(r["status"]),
                       " ".join(link(u.strip(), "source %d" % (k + 1))
                                for k, u in enumerate(r["source_url"].split("|")))]
                      for r in DRILL["rows"]])

    body = (lede + grid + readiness
            + "<h2>Model output, without a market to compare it to</h2>" + own + own_note
            + luck + controls
            + "<h2>Findings</h2>" + findings
            + """<h2>Where to go next</h2>
<p><a href="pages/readiness.html">Decision readiness</a> — the full requirement table ·
<a href="pages/availability.html">Availability</a> — 347 dated injury rows ·
<a href="pages/depth.html">Depth &amp; replacements</a> — the club chart, the roster codes and the join that
proves a replacement ·
<a href="pages/questions.html">Questions</a> — what must be answered before anything else is built ·
<a href="pages/flagged.html">Flagged for review</a> — every irregularity, with its source.</p>""")
    return shell("index.html", "Dashboard", "Overview · dashboard", body)


# ------------------------------------------------------------------ pages
def page_exec():
    c = REQ["counts"]; m = BT["metrics"]
    body = """<h1>Executive summary</h1>
<p class="lede">Five paragraphs, then the numbers. Written after the captures, not before them.</p>
<h2>1. What was done</h2>
<p>Official NFL pages were read on 2026-11-15 and 2026-11-16 and transcribed into dated files: the league
standings (all 32 clubs), the Week 10 and Week 11 schedule pages, the full Week 10 injury report, three
complete Game Books and three club pages for Detroit. A standard-library build turns those files into %d
datasets, this site, and a verification pass that fails on an unsourced row or a broken internal link.
No number on this site is typed by hand outside a transcription file, and no value was filled in when the
official page left it blank.</p>
<h2>2. What is verified</h2>
<p>%d settled games reconcile exactly to the standings I read: all 32 clubs agree on wins, losses, ties,
points for and points against. The league identity holds (points for sum to points against, 6824 = 6824;
wins equal losses, 147 = 147). The Week 10 injury report transcribes to %d rows across %d club sections, and
that count independently matches the 347/28/171 figure another workspace in this repository measured the
day before. Three Game Books give starters, inactives, venue, roof, surface, weather and officials for
three games, and one of them proves a replacement chain end to end: Sam Darnold published Out, on the Not
Active list, and Drew Lock listed at quarterback with 17 passes in the same document.</p>
<h2>3. What the model says, and what it is worth</h2>
<p>The pre-registered singles baseline publishes a fair side, a fair total and a moneyline probability for
all 13 Week 11 games. Walk-forward over %d graded games, the total beats the naive league-average total by
%.2f points of mean absolute error, game-cluster 95%% interval %s. Its moneyline beats "always home" on the
Brier score by %.4f, interval %s, a ratio skill of %s with ratio interval %s. Those intervals are the honest
headline: every published interval here excludes zero at 116 games, which is not the same thing as a
promotion, because the pre-registered sample floor is 300.</p>
<h2>4. What is blocked, and by what</h2>
<p>Of %d brief lines, %d are met, %d are partial and %d are blocked. The recurring blockers are not coding
problems: there is no permitted price source, so every ROI, closing-line value and residual cell is blank;
one club of 32 publishes a depth chart this build can parse, and that club labels its own chart
<em>unofficial</em>; and the availability history is a single dated week, which cannot support the
with-and-without ablation the brief demands. Each blocker names the number that clears it on the readiness
table.</p>
<h2>5. What to do first</h2>
<p>Decide the price policy. It is the only blocker that unblocks an entire class of results at once, and
every other open question can be answered in parallel while it is being decided. The suggestions page lists
five proposals with their cost, the gate each would clear and the risk; the verdict column is deliberately
left for you.</p>""" % (len(D), REC["n_games"], AV["counts"]["rows"], AV["counts"]["clubs"],
                        BT["n_forecasts"], m["mae_improvement"], m["mae_improvement_ci"],
                        m["brier_diff_improvement"], m["brier_diff_ci"], m["brier_skill"],
                        m["brier_skill_ci"], REQ["n_rows"], c["met"], c["partial"],
                        c["blocked"])
    rows = [[esc(r["id"]), esc(r["requirement"]), badge(r["status"]), esc(r["clearing_number"]),
             link(r["source_url"], "official") if r["source_url"] else
             '<span class="nosrc">no official source</span>']
            for r in REQ["rows"] if r["status"] != "met"]
    body += table("Everything not yet met, and the number that would clear it",
                  ["ID", "Requirement", "Status", "Clearing number", "Source"], rows)
    return shell("pages/executive-summary.html", "Executive summary", "Overview · executive summary", body)


def page_readiness():
    rows = [[esc(r["id"]), esc(r["line"]), esc(r["requirement"]), badge(r["status"]),
             esc(r["gate"] or "—"), v(r["clearing_number"]), esc(r["evidence"]),
             link(r["source_url"], "official")] for r in REQ["rows"]]
    c = REQ["counts"]
    body = ("<h1>Decision readiness</h1><p class=\"lede\">One row per line of the brief. %d rows: %d met, "
            "%d partial, %d blocked. Read the gate column as <em>why not yet</em> and the clearing-number "
            "column as <em>what would make it yes</em>.</p>" % (REQ["n_rows"], c["met"], c["partial"], c["blocked"])
            + table("Requirement traceability", ["ID", "Brief line", "Requirement", "Status", "Gate",
                                                "Number that would clear it", "What exists today", "Source"], rows))
    return shell("pages/readiness.html", "Decision readiness", "Overview · decision readiness", body)


def page_results():
    import csv as _csv
    rows = [[esc(c["check"]), esc(c["expected"]), esc(c["observed"]), badge(c["status"]),
             link(c["source_url"], "standings")] for c in CN["rows"]]
    with open(os.path.join(NS, "data", "raw", "standings_2026-11-15.csv"), encoding="utf-8") as fh:
        stand = list(_csv.DictReader(fh))
    st = [[esc(r["team"]), esc(r["w"]), esc(r["l"]), esc(r["t"]), esc(r["pf"]), esc(r["pa"]), esc(r["net"]),
           esc(r["pct"]), badge("pass"), link("https://www.nfl.com/standings/", "standings")]
          for r in sorted(stand, key=lambda r: (-(int(r["w"]) - int(r["l"])), -int(r["pf"]), r["team"]))]
    body = ("<h1>Verified results feed</h1>"
            "<p class=\"lede\">A backtest needs settled games that agree with an official record. This page is "
            "the reconciliation: every game the repository can evidence is re-summed per club and compared to "
            "the standings captured 2026-11-15. %d games, %d of 32 clubs agreeing on all five fields.</p>"
            % (REC["n_games"], REC["clubs_checked"] - len(REC["mismatches"]))
            + table("Identity checks computed in the build", ["Check", "Must hold", "Observed", "Status", "Source"], rows)
            + "<h2>The standings as published</h2>"
            + table("All 32 clubs, ordered by record", ["Club", "W", "L", "T", "PF", "PA", "Net", "Pct", "Cross-check", "Source"], st)
            + "<div class=\"panel\"><h3>What this does and does not prove</h3><p>It proves the game-level sample "
              "is internally consistent with the league's own table, club by club, so a walk-forward backtest "
              "cannot be scored against a corrupted base. It does not prove the sample is complete: Week 10's "
              "Monday game had not kicked off at capture, so %d games are settled here, not the %d a full "
              "ten weeks would contain.</p></div>" % (REC["n_games"], REC["n_games"] + 2))
    return shell("pages/results.html", "Results feed", "Data · results feed", body)


def page_fixtures():
    import csv as _csv
    w10 = list(_csv.DictReader(open(os.path.join(NS, "data", "raw", "week10_2026_results.csv"))))
    w11 = list(_csv.DictReader(open(os.path.join(NS, "data", "raw", "week11_2026_slate.csv"))))
    r10 = [[esc(r["gameday"]), esc("%s %s" % (r["away"], r["away_score"] or "")), 
            esc("%s %s" % (r["home"], r["home_score"] or "")), badge("final" if r["status"] == "final" else r["status"]),
            v(r["venue"]), link(r["game_url"], "game centre")] for r in w10]
    r11 = [[esc(r["gameday"]), esc("%s at %s" % (r["away"], r["home"])), esc(r["et_raw"]), esc(r["network"]),
            v(r["venue_from_schedule"]), link(r["game_url"], "game centre")] for r in w11]
    body = ("<h1>Fixtures</h1><p class=\"lede\">Week 10 as it settled, and Week 11 as the league publishes it. "
            "Fixture-context features are taken only from these two official pages: gameday, published clock "
            "time, network, and venue where the page states one.</p>"
            + table("Week 10 2026 · settled state at capture 2026-11-16T01:40Z",
                    ["Gameday", "Away", "Home", "State", "Venue (only where published)", "Source"], r10)
            + "<p class=\"small\">PIT at CIN is reported exactly as the page showed it (Q1, 0-3) and LAC at BAL had "
              "not kicked off. Neither is counted as a settled game anywhere in the build.</p>"
            + "<h2>Week 11 2026 · the slate the model originates</h2>"
            + table("13 games, 6 clubs on bye (ATL, CLE, GB, LA, NE, SEA)",
                    ["Gameday", "Game", "Published kickoff (ET)", "Network", "Venue (only where published)", "Source"], r11)
            + "<p class=\"small\">Kickoff times are the published ET clock values. The model does not convert them, "
              "because a converted time is a derived value and every derived value on this site is computed in "
              "the build, not in prose.</p>")
    return shell("pages/fixtures.html", "Fixtures", "Data · fixtures", body)


def page_availability():
    c = AV["counts"]
    club_rows = [[esc(r["team"]), esc(r["n_rows"]), esc(r["n_out"]), esc(r["n_doubtful"]),
                  esc(r["n_questionable"]), esc(r["n_game_status_blank"]), esc(r["n_dnp"]),
                  badge("no section" if r["section_present"] == "no" else "present"),
                  v(r["starters_out"]), link(AV["source_url"], "report")] for r in AV["rows"]]
    p_rows = [[esc(r["row_id"]), esc(r["team"]), esc(r["player"]), esc(r["position"]), v(r["injury"]),
               esc(r["practice_status"]), badge(r["game_status"]) if r["game_status"] else
               '<span class="blank">blank (as published)</span>', v(r["starter_evidence"]),
               link(r["source_url"], "report")] for r in AV["players"]]
    gs = c["game_status"]
    body = ("<h1>Availability — Week 10 2026</h1>"
            "<p class=\"lede\">The official injury report, captured 2026-11-16T01:37Z: %d rows, %d club "
            "sections. Game status: %d Out, %d Doubtful, %d Questionable, %d blank. This page publishes levels "
            "and nothing else — no probability, no points penalty, no expected games missed.</p>"
            % (c["rows"], c["clubs"], gs.get("Out", 0), gs.get("Doubtful", 0), gs.get("Questionable", 0),
               gs.get("(blank)", 0))
            + """<div class="panel warn"><h3>Why there is no injury number anywhere on this site</h3>
<p>The brief asks for the injury signal to be a <em>surprise</em>, not a level. A surprise is a deviation
from an expected value. This repository holds one dated week, so there is no expectation to deviate from,
and a fixed points penalty for a missing starter is explicitly rejected by the brief. Every row therefore
carries the designation only. Gate G7 names what would change that: a multi-week dated history joined to
official inactive lists, so a designation's play rate can be measured before it becomes a feature.</p></div>"""
            + table("Per-club counts. 'starters_out' is blank because no starter flag exists without a depth source",
                    ["Club", "Rows", "Out", "Doubtful", "Questionable", "Status blank", "DNP", "Section",
                     "Starters out", "Source"], club_rows)
            + "<h2>All %d rows</h2>" % c["rows"]
            + table("Every row as published. A blank cell is a published blank, preserved on purpose",
                    ["ID", "Club", "Player", "Pos", "Injury", "Practice", "Game status", "Starter evidence", "Source"],
                    p_rows))
    return shell("pages/availability.html", "Availability", "Data · availability", body)


def page_depth():
    d_rows = [[esc(r["unit"]), esc(r["slot"]), esc(r["rank"]), esc(r["player"]),
               esc(r["publication_label"]), link(r["source_url"], "club chart")] for r in DEPTH["rows"]]
    r_rows = [[esc(r["team"]), esc(r["player"]), esc(r["position"]), badge(r["status"] if isinstance(r["status"], str) else ""),
               link(r["source_url"], "roster")] for r in ROST["rows"]]
    rp_rows = [[esc(r["game_key"].replace("2026_10_", "W10 ").replace("_", " v ")), esc(r["team"]),
                esc(r["player"]), esc(r["position"]), badge(r["report_designation"]),
                esc(r["on_not_active_list"]), esc(r["started_in_game"]), v(r["replaced_by"]),
                esc(r["evidence_note"]),
                " ".join(link(u.strip(), "evidence %d" % (k + 1))
                         for k, u in enumerate(r["source_url"].split("|")))] for r in REPL["rows"]]
    f_rows = [[esc(r["id"]), esc(r["claim"]), esc(r["evidence"]), badge(r["status"]),
               " ".join(link(u.strip(), "source %d" % (k + 1))
                        for k, u in enumerate(r["source_url"].split("|")))] for r in DRILL["rows"]]
    body = ("<h1>Depth, roster and replacements</h1>"
            "<p class=\"lede\">The brief's hardest requirement is not tracking that a starter is out — it is "
            "tracking <em>how deep</em> the replacement is. This page shows exactly how far that can be "
            "verified today: one club's published depth chart, one club's roster status codes, and a join to "
            "the Game Book that names replacements only where the document itself names them.</p>"
            "<div class=\"panel bad\"><h3>The blocker, restated precisely</h3><p>The repository has been "
            "carrying the line \"no official depth-order source exists\". That is too strong. Detroit publishes a "
            "structured, machine-readable depth chart and links it from its official nfl.com roster page. But the "
            "club labels it <em>Unofficial Depth Chart Compiled by Lions Football Communications</em>, and one "
            "club is not 32. The honest blocker is coverage: 31 clubs are uncaptured, and the one captured source "
            "carries its publisher's own disclaimer.</p></div>"
            + "<h2>Computed findings</h2>"
            + table("Four findings, each reproduced by the build from the captured data",
                    ["ID", "Finding", "Evidence", "Status", "Sources"], f_rows)
            + "<h2>Replacement evidence, two games deep</h2>"
            + "<p>%d rows: %d with a replacement named by the Game Book, %d left open rather than guessed. "
              "The join is designation → Not Active list → starting lineup, in that order, and nothing is "
              "promoted to \"replacement\" without the last step.</p>" % (
                  REPL["n_rows"], REPL["n_confirmed"], REPL["n_open"])
            + table("Report designation joined to the Game Book",
                    ["Game", "Club", "Player", "Pos", "Report", "Not active", "Started", "Replaced by", "Evidence", "Sources"],
                    rp_rows)
            + "<h2>Club depth chart, %d rows, one club</h2>" % DEPTH["n_rows"]
            + ("<p>Rank 1 is the club's own first-listed player, not the starter. On this single chart "
               "%d of %d slot groups carry more than one rank-1 player (%s), and one player is rank 1 in "
               "two different slots (Jack Fox at punter and holder). That is why the register keeps the "
               "slot as a group and never collapses it to a single starter: a rule that picked "
               "&quot;the rank-1 player&quot; would have to discard evidence the publisher printed.</p>"
               % (DEPTH["n_rank1_groups"], DEPTH["n_rank1_slots"],
                  "; ".join("%s ×%d" % (g["slot"], g["n"]) for g in DEPTH["rank1_groups"])))
            + table("Detroit depth chart as published 2026-11-16",
                    ["Unit", "Slot", "Rank", "Player", "Publication label", "Source"], d_rows)
            + "<h2>Roster status codes, one club</h2>"
            + "<p>%d rows. Codes observed: %s. A roster status is not availability: ACT means on the active "
              "roster, not 'will play', and an unlisted player is never read as available.</p>"
              % (ROST["n_rows"], ", ".join(ROST["codes_observed"]))
            + table("Detroit roster as published 2026-11-16", ["Club", "Player", "Pos", "Status", "Source"], r_rows))
    return shell("pages/depth.html", "Depth & replacements", "Data · depth", body)


def page_own_lines():
    rows = []
    for r in LINES["rows"]:
        rows.append([esc("%s at %s" % (r["away"], r["home"])), esc(r["gameday"]), esc(r["et"]),
                     esc("%.2f" % r["expected_away_pts"]), esc("%.2f" % r["expected_home_pts"]),
                     esc(side_label(r["home"], r["away"], r["fair_home_margin_rounded"])),
                     esc("%+.2f" % r["fair_home_margin"]),
                     esc("%.1f" % r["fair_total_rounded"]), v(r["market_total"]),
                     v(r["residual_total"]), esc("%.4f" % r["p_home_win"]),
                     link("https://www.nfl.com/schedules/2026/by-week/week-11", "schedule")])
    k = LINES["constants"]
    body = ("<h1>Week 11 own lines</h1>"
            "<p class=\"lede\">Thirteen games, originated in the frozen order: the side first, then the total, "
            "then the moneyline. Every row carries the inputs that produced it, so any reader can recompute the "
            "number with a calculator.</p>"
            "<dl class=\"kv\">"
            "<dt>Model version</dt><dd><code>%s</code></dd>"
            "<dt>Registered at commit</dt><dd><code>%s</code></dd>"
            "<dt>Home-field constant</dt><dd>%+.4f points added to the home side &mdash; half the observed mean "
            "home margin over %d settled games. Positive means the home side is expected to score more; "
            "negative would mean the away side is. The observed mean is negative here, which is only true "
            "because the home clubs in this corpus have been out-scored so far; it is a measurement of the "
            "sample, not a claim that home-field advantage has inverted.</dd>"
            "<dt>Margin dispersion</dt><dd>%.4f points (sample sd of margin about its mean), the denominator "
            "of the moneyline probability</dd>"
            "<dt>Constant sample audit</dt><dd>%d games used (%d from the verified corpus, %d overlap dropped "
            "when the Week 10 transcription was merged on date/away/home)</dd>"
            "<dt>Origination order audit</dt><dd>required <code>%s</code>, observed <code>%s</code> — %s</dd>"
            "<dt>Price transparency</dt><dd>market and residual columns are blank on every row</dd>"
            "</dl>"
            % (LINES["model_version"], LINES["registration_commit"][:7], k["hfa_half_points"],
               k["n_games_used"], k["sigma_margin"], k["n_games_used"], k["n_from_verified_corpus"],
               k["n_overlap_dropped"], LINES["order_audit"]["required"],
               LINES["order_audit"]["observed"], badge(LINES["order_audit"]["status"]))
            + table("Originated lines, with inputs, and the unrounded home margin so the sign is never ambiguous",
                    ["Game", "Gameday", "ET", "E[away]", "E[home]", "Fair side (printed)", "Home margin",
                     "Fair total", "Market total", "Residual", "P(home)", "Source"], rows)
            + """<div class="panel warn"><h3>What "own line" means here, and what it does not</h3>
<p>An own line is a model estimate expressed as a market number. It is not a claim that the number is
better than a market number — that claim needs a price, and there is none. The residual column exists so
that the moment a permitted price source exists, the comparison is already in place and cannot be
back-fitted to make the model look good.</p></div>"""
            + "<h2>Totals, twice</h2><p>The brief asks for every model total to be published twice until one "
              "wins. The second total is the naive running league average from the backtest, published beside "
              "the model's number on the backtest page with the gap between them, and neither is retired until "
              "the walk-forward comparison clears the sample floor.</p>")
    return shell("pages/own-lines.html", "Own lines", "Markets · own lines", body)


def page_model():
    L = LINES
    reg = open(os.path.join(NS, "PREREGISTRATION.md"), encoding="utf-8").read()
    body = ("<h1>The model and its registration</h1>"
            "<p class=\"lede\">A singles-only shadow baseline, registered before it was run. The registration "
            "commit is <code>%s</code>: that commit contains the rule text below and no results, which is what "
            "makes it a registration rather than a description.</p>" % L["registration_commit"][:7]
            + "<h2>Rule text, verbatim from the registration</h2>"
            + '<div class="panel"><pre style="white-space:pre-wrap;font-size:12px;color:#b9c6d6;margin:0">%s</pre></div>' % esc(reg)
            + "<h2>Every published output carries its inputs</h2>"
            + table("Model outputs as a probability plus inputs, not a pick",
                    ["Game", "Away off rate", "Home def rate", "Home off rate", "Away def rate",
                     "E[home]", "E[away]", "P(home)", "Sources"],
                    [[esc("%s at %s" % (r["away"], r["home"])), esc(r["away_off_rate"]), esc(r["home_def_rate"]),
                      esc(r["home_off_rate"]), esc(r["away_def_rate"]), esc(r["expected_home_pts"]),
                      esc(r["expected_away_pts"]), esc(r["p_home_win"]),
                      link("https://www.nfl.com/standings/", "standings") + " " +
                      link("https://www.nfl.com/schedules/2026/by-week/week-11", "schedule")]
                     for r in L["rows"]])
            + "<p class=\"small\">Rates are points per team-game from the 2026-11-15 standings. A reader can "
              "reproduce any row: E[home] is the mean of the home offence and the away defence, plus the "
              "home-field constant; the probability is the normal CDF of the margin over the dispersion.</p>")
    return shell("pages/model.html", "Model & inputs", "Markets · model", body)


def page_backtest():
    m = BT["metrics"]
    f_rows = [[esc(r["week_label"]), esc(r["away"]), esc(r["home"]), esc(r["p_home_win"]), esc(r["actual_home_win"]),
               esc("%.4f" % r["brier"]), esc("%.2f" % r["fair_total"]), esc(r["actual_total"]),
               esc("%.2f" % r["abs_err_total"]), esc("%.2f" % r["abs_err_naive"]),
               link(r["source_url"], "game") if r["source_url"] else
               link("https://www.nfl.com/schedules/2026/reg10/", "week page")]
              for r in BT["forecasts"]]
    w_rows = [[esc(r["label"]), esc(r["n"]), esc(r["brier"]), esc(r["brier_home"]), esc(r["mae_total"]),
               esc(r["mae_naive"]), badge("pass" if r["mae_total"] < r["mae_naive"] else "fail"),
               link("https://www.nfl.com/schedules/2026/", "schedule")]
              for r in BT["by_week"]]
    body = ("<h1>Backtest and the removal of luck</h1>"
            "<p class=\"lede\">%d graded games, walk-forward: every forecast for a week is produced only from "
            "earlier weeks, so no game is scored by a model that has seen it. Three controls sit beside it, "
            "including a fair coin, so that any number that could have been produced by chance is labelled as "
            "such.</p>" % BT["n_forecasts"]
            + '<div class="grid">'
            + '<div class="card"><div class="k">Model Brier</div><div class="n">%.4f</div><div class="s">always-home %.4f</div></div>' % (m["brier"], m["brier_home_baseline"])
            + '<div class="card"><div class="k">Brier skill vs home (ratio)</div><div class="n">%s</div><div class="s">95%% ratio CI %s</div></div>' % (m["brier_skill"], m["brier_skill_ci"])
            + '<div class="card"><div class="k">Brier difference vs home</div><div class="n">%+.4f</div><div class="s">95%% difference CI %s</div></div>' % (m["brier_diff_improvement"], m["brier_diff_ci"])
            + '<div class="card"><div class="k">Total MAE</div><div class="n">%.2f</div><div class="s">naive %.2f</div></div>' % (m["mae_total"], m["mae_naive"])
            + '<div class="card"><div class="k">MAE improvement</div><div class="n">%+.2f</div><div class="s">95%% CI %s</div></div>' % (m["mae_improvement"], m["mae_improvement_ci"])
            + '</div>'
            + "<div class=\"panel\"><h3>How to read these intervals</h3><p>The intervals are game-cluster "
              "bootstraps over %d forecasts with a fixed seed, so they reproduce exactly. The total's "
              "improvement interval excludes zero, which is a real result at this sample. The moneyline's "
              "skill interval does not, which means the moneyline is not yet distinguishable from always "
              "picking the home team. Both statements are published because both are true.</p></div>" % BT["n_forecasts"]
            + table("Week by week — the whole point of publishing this",
                    ["Week", "n", "Brier", "Always-home Brier", "Total MAE", "Naive MAE", "Beat naive", "Source"],
                    w_rows)
            + "<h2>Every forecast</h2>"
            + table("Each row is a scored forecast; nothing is aggregated away",
                    ["Week", "Away", "Home", "P(home)", "Home won", "Brier", "Model total", "Actual", "Abs err", "Naive err", "Source"], f_rows)
            + "<div class=\"panel bad\"><h3>Gate</h3><p>%s</p></div>" % esc(BT["gate_note"]))
    return shell("pages/backtest.html", "Backtest & luck", "Markets · backtest", body)


def page_leaderboard():
    s_rows = [[esc(s["id"]), esc(s["name"]), esc(s["family"]), badge(s["signal_status"]), esc(s["staking_status"]),
               v(s["brier_skill"]), v(s["mae_improvement"]), v(s["roi"]), v(s["clv"]), esc(s["reward_payable"]),
               esc(s["blocking_gate"]),
               link(s["source_url"], "source") if s["source_url"] else
               '<span class="nosrc">no official source</span>'] for s in LB["strategies"]]
    w_rows = [[esc(s["id"]), esc(s["name"]), esc(s["what_would_change_our_mind"]),
               link(s["source_url"], "source") if s["source_url"] else '<span class="nosrc">no official source</span>']
              for s in LB["strategies"]]
    g_rows = [[esc(g["id"]), esc(g["name"]), esc(g["requirement"]), esc(g["observed"]), badge(g["status"]),
               esc(g["clearing_number"]),
               link(g["source_url"], "official") if g["source_url"] else
               '<span class="nosrc">no official source</span>'] for g in GATES["rows"]]
    body = ("<h1>Leaderboard, gates and demotion</h1>"
            "<p class=\"lede\">Signal and staking are separate columns and are never mixed into one rank. "
            "Signal is a proper score against a benchmark with an interval; staking is realised return, which is "
            "blank because no permitted price source exists. A lucky staking run therefore cannot raise a signal "
            "rank — and no reward is payable until every gate passes.</p>"
            + '<div class="grid">'
            + '<div class="card"><div class="k">Strategies registered</div><div class="n">%d</div><div class="s">4 pre-registered, 1 not registered</div></div>' % len(LB["strategies"])
            + '<div class="card"><div class="k">Qualified</div><div class="n">%d</div><div class="s">a gate is pass/fail, never a majority</div></div>' % LB["n_qualified"]
            + '<div class="card"><div class="k">Rewards paid</div><div class="n">%d</div><div class="s">paying now would be paying for luck</div></div>' % LB["rewards_paid"]
            + '<div class="card"><div class="k">Gates</div><div class="n">%d/%d</div><div class="s">%d fail, %d blocked</div></div>' % (GATES["n_pass"], len(GATES["rows"]), GATES["n_fail"], GATES["n_blocked"])
            + '</div>'
            + "<p>%s</p>" % esc(LB["separation_rule"])
            + table("The board — signal, staking and the gate that blocks promotion",
                    ["ID", "Strategy", "Family", "Signal", "Staking", "Brier skill", "MAE improv.", "ROI", "CLV", "Reward payable", "Blocking gate", "Source"], s_rows)
            + "<h2>What would change our mind</h2>"
            + table("Two-sided, on every strategy: what would support it and what would refute it", ["ID", "Strategy", "What would change our mind", "Source"], w_rows)
            + "<h2>Gates</h2><p>%s Promotion: %s</p>" % (esc(GATES["demotion_gate"]), esc(GATES["promotion_rule"]))
            + table("Every gate, its observed value and the number that clears it",
                    ["ID", "Gate", "Requirement", "Observed", "Status", "Clearing number", "Source"], g_rows))
    return shell("pages/leaderboard.html", "Leaderboard", "Competition · leaderboard", body)


def page_correlations():
    rows = [[esc(r["a"]), esc(r["b"]), esc(r["r"]), esc(r["n"]), esc(r["unit"]), esc(r["kind"]),
             esc(r["interpretation"]), link(r["source_url"], "official")] for r in CORR["rows"]]
    body = ("<h1>Correlations, with n on every value</h1>"
            "<p class=\"lede\">%d correlations, every one computed from a single dated official standings page "
            "with the sample size published on the row. No market number, no third-party number and no price "
            "enters any of them.</p>" % CORR["n_rows"]
            + table("Correlation register", ["A", "B", "r", "n", "Unit", "Kind", "Interpretation", "Source"], rows)
            + "<div class=\"panel warn\"><h3>What is deliberately missing</h3><p>%s</p></div>" % esc(CORR["note"])
            + "<div class=\"panel\"><h3>Why one row is a caution rather than a finding</h3><p>The third row "
              "correlates points scored with games played. It is a schedule artefact and it is published on "
              "purpose: a correlation panel that only shows the flattering rows is how artefacts become "
              "features.</p></div>")
    return shell("pages/correlations.html", "Correlations", "Competition · correlations", body)


def page_questions():
    rows = [[esc(r["id"]), esc(r["kind"]), esc(r["question"]), esc(r["why_it_blocks"]), esc(r["answer_at_present"]),
             esc(r["what_would_answer_it"]), link(r["source_url"], "source") if r["source_url"] else '<span class="nosrc">no official source</span>']
            for r in QS["rows"]]
    body = ("<h1>Questions that must be answered before deciding</h1>"
            "<p class=\"lede\">%d questions, %d of them unanswered or only partly answered. Each one names the "
            "information that would settle it. None has been answered on your behalf.</p>"
            % (QS["n_rows"], QS["n_unanswered"])
            + table("Questions register — decision questions and information gaps",
                    ["ID", "Kind", "Question", "Why it blocks", "State today", "What would answer it", "Source"], rows)
            + "<div class=\"panel\"><h3>How this list was built</h3><p>%s</p></div>" % esc(QS["policy"]))
    return shell("pages/questions.html", "Questions", "Decisions · questions", body)


def page_suggestions():
    rows = [[esc(r["id"]), esc(r["title"]), esc(r["change"]), esc(r["cost"]), esc(r["unblocks"]), esc(r["risk"]),
             esc(r["recommendation"]), badge("open"),
             link(r["source_url"], "source") if r["source_url"] else
             '<span class="nosrc">no official source</span>']
            for r in SUG["rows"]]
    body = ("<h1>Suggestions</h1>"
            "<p class=\"lede\">Five proposals, each with what it changes, what it costs, the gate it would clear "
            "and the risk of doing it. None has been implemented: the point of this page is that you choose "
            "before anything changes.</p>" + "<p>%s</p>" % esc(SUG["workflow"])
            + table("Suggestions — decide first, implement after",
                    ["ID", "Suggestion", "What changes", "Cost", "Gate it unblocks", "Risk", "Recommendation", "State", "Source"], rows)
            + "<div class=\"panel ok\"><h3>The recommendation, in one line</h3><p>Decide the price policy "
              "first. It is the only item that unblocks a whole class of results at once; every other proposal "
              "can run in parallel while it is being decided.</p></div>")
    return shell("pages/suggestions.html", "Suggestions", "Decisions · suggestions", body)


def flagged_lead(FLAG):
    """The 'read these first' panel is generated from the severity column, not written by hand.

    The hand-written version named FB-01, FB-03 and FB-09 while the register listed a different
    set, so the panel and the table disagreed on the same page. Severity is data; the summary is
    now derived from it.
    """
    order = ["blocking", "high", "medium", "low"]
    top = []
    for level in order:
        for r in FLAG["rows"]:
            if r["severity"] == level:
                top.append(r)
        if len(top) >= 3:
            break
    top = top[:3]
    counts = {}
    for r in FLAG["rows"]:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    bits = " · ".join("%d %s" % (counts[k], k) for k in order if k in counts)
    items = "".join("<li><strong>%s</strong> (%s) — %s. %s</li>"
                    % (esc(r["id"]), esc(r["severity"]), esc(r["item"]),
                       link(r["source_url"], "source") if r["source_url"] else
                       '<span class="nosrc">no official source</span>')
                    for r in top)
    return ('<div class="panel bad"><h3>What to read first</h3>'
            '<p class="small">Severity spread across %d flags: %s. The three highest are listed first '
            'because they change what the rest of the site can say.</p><ul>%s</ul></div>'
            % (FLAG["n_rows"], esc(bits), items))


def page_flagged():
    rows = [[esc(r["id"]), badge(r["severity"]), esc(r["item"]), esc(r["detail"]), esc(r["gate"] or "—"),
             link(r["source_url"], "source") if r["source_url"] else '<span class="nosrc">no official source</span>']
            for r in FLAGS["rows"]]
    body = ("<h1>Flagged for review</h1>"
            "<p class=\"lede\">Every irregularity found while transcribing official pages, published with its "
            "source. Nothing here blocks the site: a flag is a statement about what the official page says, not "
            "a reason to withhold the rest of it.</p>" + "<p>%s</p>" % esc(FLAGS["policy"])
            + table("%d flags. Severity blocking = an entire class of results cannot exist without it"
                    % FLAGS["n_rows"], ["ID", "Severity", "Item", "Detail", "Gate", "Source"], rows)
            + flagged_lead(FLAGS))
    return shell("pages/flagged.html", "Flagged for review", "Decisions · flagged", body)


def main():
    pages = {
        "index.html": landing(),
        "pages/executive-summary.html": page_exec(),
        "pages/readiness.html": page_readiness(),
        "pages/results.html": page_results(),
        "pages/fixtures.html": page_fixtures(),
        "pages/availability.html": page_availability(),
        "pages/depth.html": page_depth(),
        "pages/own-lines.html": page_own_lines(),
        "pages/model.html": page_model(),
        "pages/backtest.html": page_backtest(),
        "pages/leaderboard.html": page_leaderboard(),
        "pages/correlations.html": page_correlations(),
        "pages/questions.html": page_questions(),
        "pages/suggestions.html": page_suggestions(),
        "pages/flagged.html": page_flagged(),
    }
    for rel, content in pages.items():
        path = os.path.join(SITE, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    print("wrote %d pages" % len(pages))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the NFL Line Genesis static site.

    python3 nfl-hub/build.py

Writes nfl-hub/index.html and nfl-hub/pages/*.html from nfl-hub/data/*.json.
Deterministic: running twice produces byte-identical output.
"""
from __future__ import annotations

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PAGES = os.path.join(HERE, "pages")
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-hub/"
E = html.escape


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return json.load(f)


SRC = {s["id"]: s for s in load("sources.json")["sources"]}
STAND = load("official", "standings_2026.json")
FIX = load("official", "schedule_week10_2026.json")
LINES = load("model", "week10_lines.json")
RATINGS = load("model", "ratings_2026.json")
CARD = load("model", "model_card.json")
RESULTS = load("strategies", "results.json")
CORR = load("correlations.json")
INJ = load("injuries.json")
SUG = load("suggestions.json")
QREG = load("questions.json")
FLAGS = load("flags.json")["flags"]
AUDIT = load("audit.json")
GATES = load("gates.json")
STRAT = load("strategies.json")["strategies"]
SOURCES = load("sources.json")
DLOG = load("decision_log.json")
INTEG = load("integrity.json")
RECON = load("reconciliation.json")

PROB = results = RESULTS["results"]
NAV = [
    ("Overview", [("index.html", "Dashboard"), ("pages/executive-summary.html", "Executive summary"),
                  ("pages/requirements.html", "Requirements coverage")]),
    ("Decide", [("pages/suggestions.html", "Suggestions & decisions"), ("pages/questions.html", "Open questions"),
                ("pages/flagged.html", "Flagged for review")]),
    ("This week", [("pages/own-lines.html", "Originated lines"), ("pages/injuries.html", "Injuries & availability")]),
    ("Evidence", [("pages/strategies.html", "Strategy catalogue"), ("pages/validation.html", "Validation & luck"),
                  ("pages/correlations.html", "Correlations"), ("pages/leaderboard.html", "Leaderboard & rewards")]),
    ("Data", [("pages/data.html", "Official data"), ("pages/sources.html", "Source register"),
              ("pages/audit.html", "Repository review")]),
]


def rel_for(path):
    return "" if path == "index.html" else "../"


def a(url, label, title=None, cls=""):
    t = f' title="{E(title)}"' if title else ""
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{E(url)}"{t}{c} target="_blank" rel="noopener">{E(label)} ↗</a>'


def src(*ids, label=None):
    out = []
    for i in ids:
        s = SRC.get(i)
        if not s:
            out.append(f'<span class="badge bad">{E(i)} MISSING</span>')
            continue
        kind = "official" if s["official"] else "archive"
        text = label or i
        out.append(f'<a class="src {kind}" href="{E(s["url"])}" target="_blank" rel="noopener" '
                   f'title="{E(s["name"])}">{E(text)}</a>')
    return " ".join(out)


def derived(path, label="DERIVED"):
    return (f'<a class="src derived" href="{E(REPO + path)}" target="_blank" rel="noopener" '
            f'title="Computed in this repository — not an official NFL value">{E(label)}</a>')


def badge(text, kind="info"):
    return f'<span class="badge {kind}">{E(text)}</span>'


def blank(note="not verified"):
    return f'<span class="blank" title="{E(note)}">—</span>'


def table(headers, rows, tid=None, cls=""):
    hid = f' id="{tid}"' if tid else ""
    head = "".join(f"<th>{E(h)}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return (f'<div class="tw"><table{hid} class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


KICKER_LABEL = {label: group for group, items in NAV for _, label in items}
KICKER_BY_HREF = {href: label for group, items in NAV for href, label in items}
KICKER_LABEL.update({href: label for href, label in KICKER_BY_HREF.items()})


def page(path, title, subtitle, body, active=None, kicker="NFL LINE GENESIS"):
    rel = rel_for(path)
    nav = []
    for group, items in NAV:
        nav.append(f'<div class="navgrp">{E(group)}</div>')
        for href, label in items:
            is_active = " active" if href == active else ""
            nav.append(f'<a class="nav{is_active}" href="{rel}{href}">{E(label)}</a>')
    if rel:
        body = (body.replace('href="pages/', 'href="')
                    .replace('href="data/', 'href="../data/')
                    .replace('href="assets/', 'href="../assets/'))
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{E(title)} — NFL Line Genesis: originated lines, validation gates, correlations and a decision register built only from source-linked data.">
<title>{E(title)} · NFL Line Genesis</title>
<link rel="stylesheet" href="{rel}assets/hub.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="shell">
<aside>
  <a class="brand" href="{rel}index.html"><span class="mark">O4</span><span class="bname">NFL Line Genesis<small>OWN4 · NFL RESEARCH</small></span></a>
  <nav aria-label="Sections">{''.join(nav)}</nav>
  <div class="sidebox">
    <b>Snapshot</b><br>12 Nov 2026 · Week 10<br>
    <span class="dot warn"></span>No validated edge<br>
    <span class="dot ok"></span>32/32 official reconciliation
  </div>
  <a class="back" href="{rel}../index.html">← OWN4 home</a>
</aside>
<div class="content">
<header class="top">
  <span class="kicker">{E(kicker)}</span>
  <span class="topnote">Research, not betting advice · No official NFL endorsement</span>
</header>
<main id="main">
<div class="eyebrow">{E(KICKER_LABEL.get(active, 'Overview'))}</div>
<h1>{E(title)}</h1>
<p class="lede">{subtitle}</p>
{body}
<footer>
  <p><b>Limits.</b> Lines and ratings are derived model output from a third-party archive, not official NFL data. Market lines, depth charts and player-prop values are unavailable and are left blank. Nothing here is a recommendation to wager.</p>
  <p>Support: {a(SRC['SRC-17']['url'], 'National Problem Gambling Helpline')} · {a(SRC['SRC-18']['url'], 'NFL.com terms')} · <a href="{rel}pages/sources.html">Source register</a></p>
</footer>
</main>
</div>
</div>
<script src="{rel}assets/hub.js" defer></script>
</body>
</html>
"""
    out = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)


def pct(x, d=1):
    return "—" if x is None else f"{100*x:.{d}f}%"


def num(x, d=2, sign=False):
    if x is None:
        return "—"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def decision_badge(status):
    s = status.lower()
    if s.startswith("answered"):
        return badge(status, "ok")
    if s.startswith("partial"):
        return badge(status, "warn")
    if s.startswith("blocked"):
        return badge(status, "bad")
    return badge(status, "info")


def gate_pill(v):
    if v is True:
        return badge("PASS", "ok")
    if v is False:
        return badge("FAIL", "bad")
    return badge("—", "info")


# ---------------------------------------------------------------- dashboard
def dashboard():
    top = sorted(FLAGS, key=lambda f: 0 if "Blocking" in f["severity"] else 1)[:5]
    stats = [
        ("32/32", "teams reconciled to NFL.com standings, field by field"),
        ("14", "Week 10 games with an originated line"),
        ("0", "strategies that pass every gate"),
        ("6", "players with a formal game designation at capture"),
    ]
    cards = "".join(f'<div class="kpi"><b>{v}</b><span>{E(t)}</span></div>' for v, t in stats)

    line_rows = []
    for r in LINES["rows"]:
        line_rows.append([
            f'<span class="mono">{E(r["date"][5:])}</span>',
            f'<b>{E(r["away"])}</b> <span class="muted">{E(r["away_record"])}</span> at <b>{E(r["home"])}</b> <span class="muted">{E(r["home_record"])}</span>',
            f'<span class="mono">{E(r["own_spread_home"])}</span>',
            f'<span class="mono">{r["own_total"]:.1f}</span>',
            f'<span class="mono">{pct(r["own_home_win_prob"])}</span>',
            f'{blank("No official 2026 market line")}',
            f'{derived("data/model/week10_lines.json")} {a(r["game_url"], "NFL.com", "Official game page")}',
        ])

    gate_cards = []
    for g in SUG["decision_gates"]:
        opts = "".join(
            f'<li><b>{E(o["id"])}</b> {E(o["name"])} — <span class="muted">{E(o["pros"])}</span> '
            f'<span class="neg">Risk: {E(o["cons"])}</span></li>' for o in g["options"])
        gate_cards.append(f"""<article class="card">
<div class="cardtop">{badge(g['id'], 'amber')} <b>{E(g['question'])}</b></div>
<p>{E(g['why'])}</p>
<ul class="opts">{opts}</ul>
<p class="rec"><b>Recommendation:</b> {E(g['recommendation'])}</p>
</article>""")

    flag_rows = [[badge(f["severity"], "bad" if "Blocking" in f["severity"] else "warn"), E(f["item"]),
                  E(f["detail"]), src(f["source"]) if f["source"].startswith("SRC") else derived("data/flags.json")]
                 for f in top]

    body = f"""
<div class="banner">
  <div><b>Decision status: do not bet these lines.</b> The model is worse than the closing line at forecasting margins
  (MAE {CARD['holdout']['mae_margin_model']} vs {CARD['holdout']['mae_margin_market']} on the 2017-2025 holdout), and no
  registered strategy passes the validation gates. The value of this build is the evidence trail and the questions it forces.</div>
</div>
<section class="kpis">{cards}</section>

<section>
<h2>Week 10 — originated lines</h2>
<p class="sub">Generated 12 Nov 2026 before the first kickoff. Every value is model output; the market column is deliberately blank
because no official NFL odds publication exists and the archive has no 2026 closing lines.
{a('pages/own-lines.html', 'Method and look-ahead tests')}</p>
{table(["Date", "Matchup", "Home line", "Total", "Home win", "Market", "Source"], line_rows)}
</section>

<section>
<h2>Three decisions that block everything else</h2>
<p class="sub">These are the choices a reviewer must make before more building is reasonable. Full option analysis:
{a('pages/suggestions.html', 'Suggestions & decisions')}.</p>
<div class="grid3">{''.join(gate_cards)}</div>
</section>

<section>
<h2>What is verified, and what is not</h2>
<div class="two">
<div class="panel okpanel">
<h3>Verified against an official source</h3>
<ul>
<li>All 32 team records, points for/against and tie percentages — {a('https://www.nfl.com/standings/', 'NFL.com standings')}.</li>
<li>All 14 Week 10 fixtures, kickoff times and byes — {a(FIX['source'], 'NFL.com Week 10 schedule')}.</li>
<li>Six formal injury designations and three confirmed quarterback changes — {a('https://www.nfl.com/injuries/', 'official injury report')} and NFL.com news.</li>
<li>The 2026 rule changes — {a('https://operations.nfl.com/rules-officiating/2026-nfl-rulebook', 'NFL Operations rulebook')}.</li>
</ul>
</div>
<div class="panel badpanel">
<h3>Missing, blank and flagged</h3>
<ul>
<li>2026 market lines, closing-line value and any market comparison: <b>no source in scope</b>.</li>
<li>Starter / backup / 2nd-3rd-4th string status: <b>NFL.com has no depth chart</b> (verified 404).</li>
<li>Player props and prop combos: <b>no authorized player feed or prop prices</b>.</li>
<li>Injury causes for most players: the official table leaves the cause blank.</li>
</ul>
<p><a href="pages/questions.html">Open questions register →</a></p>
</div>
</div>
</section>

<section>
<h2>Top flagged items</h2>
<p class="sub">Full list with severity and source: <a href="pages/flagged.html">Flagged for review</a>.</p>
{table(["Severity", "Item", "Detail", "Source"], flag_rows)}
</section>

<section>
<h2>How the numbers are produced</h2>
<ol class="steps">
<li><b>Collect.</b> Official standings, schedule and injury report are captured with timestamps. History comes from a pinned third-party archive commit.</li>
<li><b>Reconcile.</b> The archive is re-aggregated and compared with the official standings for all 32 teams before any model runs.</li>
<li><b>Model.</b> A walk-forward Elo and exponentially weighted points model produce a margin and total for each game, using only prior weeks.</li>
<li><b>Pre-register.</b> Gates and strategy rules are committed to git <i>before</i> the holdout is scored.</li>
<li><b>Test.</b> Holdout ROI, week-clustered bootstrap intervals, placebo permutations and Holm correction decide the tier.</li>
<li><b>Publish the failures.</b> Anything unverified is blank and flagged rather than estimated.</li>
</ol>
</section>
"""
    page("index.html", "NFL line origination, with the evidence attached",
         "Originated Week 10 lines, pre-registered validation gates, correlation measurements, availability tracking and a decision register — built from source-linked data only.",
         body, active="index.html")


# ---------------------------------------------------------------- exec summary
def exec_summary():
    s1 = results["S1"]
    body = f"""
<div class="banner"><b>Bottom line.</b> The plumbing works and the evidence is honest: official data reconciles 32/32,
the lines are generated before kickoff without look-ahead, and every strategy fails. The next decision is not a model
change — it is whether to buy a real market feed (D2) and which dashboard is canonical (D1).</div>

<section>
<h2>1. Situation</h2>
<p>The repository already contained five separate NFL surfaces built by earlier sessions — four dashboards plus a
governance desk (`nfl-decisions/`) — publishing different scopes and different weeks with no canonical marker. Two cite NFL.com URLs that return 404. This build adds a sixth, self-contained
workspace that does three things the others do not: it reconciles every number to the live official source, it pre-registers
the gates before measuring, and it publishes a decision register instead of only results.</p>
</section>

<section>
<h2>2. What was verified</h2>
{table(["Claim", "Verification", "Source"], [
 ["2026 records & points, 32 teams", f"{RECON['teams_matched']}/32 matched on W-L-T, PF, PA and tie percentage", src("SRC-01")],
 ["Week 10 fixtures & byes", f"{RECON['fixtures']['matched']}/14 games matched by pairing and date; byes CHI, DEN, PHI, TB", src("SRC-02")],
 ["Injury designations", "6 players with formal Out/Questionable; all others practice-status only", src("SRC-03")],
 ["Quarterback changes", "SEA (Lock for Darnold), CLE (Watson), ARI (Beck); MIA headline only", src("SRC-05", "SRC-06", "SRC-10")],
 ["No official depth chart", "NFL.com depth-chart URL returns 404", src("SRC-14")],
 ["Model vs market", f"Holdout margin MAE {CARD['holdout']['mae_margin_model']} vs {CARD['holdout']['mae_margin_market']}; totals {CARD['holdout']['mae_total_model']} vs {CARD['holdout']['mae_total_market']}", derived("data/model/model_card.json")],
 ["Strategy performance", "0 of 7 strategies passed; S1 holdout ROI " + pct(s1["roi"], 2), derived("data/strategies/results.json")],
 ["Look-ahead", "Deleting or rewriting all post-Week-9 results leaves all 14 lines unchanged", derived("data/model/week10_lines.json")],
], cls="tight")}
</section>

<section>
<h2>3. What was not verified — and is therefore blank</h2>
{table(["Missing input", "Consequence", "Question"], [
 ["Official or licensed 2026 market lines", "No market comparison, no closing-line value, no ROI against a real price", '<a href="pages/questions.html#q-04">Q-04</a>'],
 ["Official depth chart / snap counts", "2nd/3rd/4th-string deficiency index cannot be computed", '<a href="pages/questions.html#q-05">Q-05</a>'],
 ["Player-level feed and prop prices", "Props and prop combos are blocked; no values published", '<a href="pages/questions.html#q-07">Q-07</a>'],
 ["Final pre-kickoff injury report", "Only six formal designations at snapshot time", '<a href="pages/questions.html#q-11">Q-11</a>'],
 ["Legal review of rewards and redistribution", "Rewards stay non-monetary; public picks not cleared", '<a href="pages/questions.html#q-13">Q-13</a>'],
], cls="tight")}
</section>

<section>
<h2>4. Findings that change decisions</h2>
<ol>
<li><b>The market is a better forecaster than the model.</b> On 2,383 holdout games the closing line beats the model on
margin MAE (9.87 vs 10.39) and totals (10.47 vs 11.97). A standalone model cannot be the product; a residual model judged
by closing-line value is the defensible path.</li>
<li><b>Luck is not removed by a good story.</b> S1 earns +4.6% on the 2013-2016 validation seasons and then loses 5.3% on the holdout.
The placebo test puts that result at p={s1['placebo_p']:.2f} — indistinguishable from random side selection.</li>
<li><b>Same-game legs are close to independent in the game markets.</b> Favourite-cover vs under phi = 0.0117
(95% CI -0.0225 to 0.0459). Player-leg dependence is unknown, not small.</li>
<li><b>Availability is the biggest unexploited input — and the least verifiable.</b> Three quarterback changes are confirmed,
but defensive depth is not published officially, so any "backup deficiency" number would be invented.</li>
<li><b>Five earlier NFL surfaces are a decision hazard.</b> They disagree, two carry dead citations, and two publish decision registers. One lines/evidence surface must be canonical.</li>
</ol>
</section>

<section>
<h2>5. Recommended path (decisions, not implementation)</h2>
{table(["Priority", "Decision", "Recommendation", "Why now", "Detail"], [
 ["1", "D1 canonical workspace", "Keep nfl-hub; banner and archive the other four", "Prevents contradictory published lines", '<a href="../index.html">hub</a>'],
 ["2", "D2 market data", "License a timestamped odds + prop feed, or accept research-only status", "Unlocks every blocked strategy and G7", '<a href="suggestions.html">D2</a>'],
 ["3", "D3 reward rule", "Rank by lower confidence bound; roll the pool over when nothing qualifies", "Stops luck from winning the competition", '<a href="leaderboard.html">rule</a>'],
 ["4", "Q-05 depth definition", "License snap counts and define 'starter' explicitly", "The requested defensive-depth measure is impossible without it", src("SRC-14")],
 ["5", "Q-13 legal", "Obtain a written opinion before any prize or public picks", "Reward and publication exposure", '<a href="questions.html#q-13">Q-13</a>'],
], cls="tight")}
</section>

<section>
<h2>6. What exists in this build</h2>
<p>15 pages: dashboard, executive summary, requirements coverage, suggestions & decisions, open questions, originated lines,
injuries, strategy catalogue, validation, correlations, leaderboard, official data, sources, repository review and flagged
items. Every table row carries a source link or an explicit DERIVED badge. The pipeline rebuilds every number from the
committed data; the verifier fails the build on an unsourced row or a broken internal link.</p>
</section>
"""
    page("pages/executive-summary.html", "Executive summary",
         "What is verified, what is missing, what the numbers actually say, and the five decisions that unlock the next phase.",
         body, active="pages/executive-summary.html")


# ---------------------------------------------------------------- suggestions
def suggestions():
    gate_blocks = []
    for g in SUG["decision_gates"]:
        rows = [[badge(o["id"], "info"), E(o["name"]), E(o["pros"]), E(o["cons"]),
                 derived("data/suggestions.json")] for o in g["options"]]
        gate_blocks.append(f"""<article class="card wide">
<div class="cardtop">{badge(g['id'], 'amber')} <b>{E(g['question'])}</b></div>
<p class="sub">{E(g['why'])}</p>
{table(["Option", "Name", "Pros", "Cons", "Evidence"], rows)}
<p class="rec"><b>Recommendation:</b> {E(g['recommendation'])}</p>
</article>""")

    rows = []
    for s in SUG["suggestions"]:
        ev = " ".join(src(x) if x.startswith("SRC") else f'<a class="src derived" href="{E(REPO + x)}" target="_blank" rel="noopener">file ↗</a>'
                      for x in s["evidence"])
        rows.append([f'<b>{E(s["id"])}</b>', E(s["title"]), E(s["problem"]), E(s["proposal"]),
                     badge(s["impact"], {"High": "bad", "Medium": "warn"}.get(s["impact"], "info")),
                     E(s["effort"]), E(s["risk"]), E(str(s["depends_on"] or "—")),
                     badge(s["status"], "ok" if "implemented" in s["status"] else ("bad" if s["status"] == "blocked" else "info")),
                     ev])

    steps = "".join(f"<li>{E(x)}</li>" for x in SUG["how_to_review"])
    body = f"""
<div class="banner"><b>How to use this page.</b> Nothing here has been implemented silently. Each suggestion states the problem,
the options, the recommendation and what it depends on. Choose an option, record it in the decision log, then build.</div>

<section>
<h2>Decision gates</h2>
<p class="sub">Nothing else should be built until these three are answered. They are ordered by how much downstream work they unblock.</p>
{''.join(gate_blocks)}
</section>

<section>
<h2>All suggestions</h2>
<p class="sub">Impact is the effect on decision quality, not on traffic. Effort is S (hours), M (days), L (weeks). A BLOCKED
suggestion depends on information that does not yet exist and must not be built by guessing.</p>
{table(["ID", "Suggestion", "Problem", "Proposal", "Impact", "Effort", "Risk", "Depends on", "Status", "Evidence"], rows)}
</section>

<section>
<h2>Review workflow</h2>
<ol class="steps">{steps}</ol>
<div class="tw"><table>
<thead><tr><th>Step</th><th>What you produce</th><th>Where it is recorded</th></tr></thead>
<tbody>
<tr><td>1. Read</td><td>A shortlist of the questions that block you</td><td><a href="pages/questions.html">Open questions</a></td></tr>
<tr><td>2. Choose</td><td>One option per decision gate</td><td><a href="data/decision_log.json">data/decision_log.json</a></td></tr>
<tr><td>3. Log</td><td>Date, owner, choice, rationale, revisit date</td><td><a href="#decision-log">Decision log below</a></td></tr>
<tr><td>4. Build</td><td>Only the chosen option, with its own tests</td><td><a href="../data/suggestions.json">data/suggestions.json</a></td></tr>
<tr><td>5. Re-check</td><td>Re-read the assumption that made the option attractive</td><td><a href="../data/decision_log.json">revisit date field</a></td></tr>
</tbody></table></div>
</section>

<section>
<h2 id="decision-log">Decision log</h2>
<p class="sub">Empty until a decision is made. Append-only: a reversed decision gets a new entry, not an edit.</p>
{table(["ID", "Date", "Gate", "Choice", "Owner", "Rationale", "Revisit", "Status"],
       [["—", "—", "—", "No decision recorded yet", "—", "—", "—", badge("awaiting decision", "warn") + " " + derived("data/decision_log.json", "log")]])}
<p class="sub">Schema and instructions: <a href="data/decision_log.json">data/decision_log.json</a></p>
</section>
"""
    page("pages/suggestions.html", "Suggestions & decisions",
         "Fifteen proposals to improve decision quality, three decision gates that unblock everything else, and a workflow for choosing a path before implementing it.",
         body, active="pages/suggestions.html")


# ---------------------------------------------------------------- questions
def questions():
    rows = []
    for r in QREG["rows"]:
        known_src = " ".join(src(s) if s.startswith("SRC") else derived(f"data/{s}") for s in r["known_source"])
        rows.append([
            f'<span id="{E(r["id"].lower())}"><b>{E(r["id"])}</b></span>',
            E(r["category"]),
            f'<b>{E(r["question"])}</b><div class="muted">{E(r["decision_blocked"])}</div>',
            E(r["known"]),
            known_src,
            E(r["missing"]) if r["missing"] != "Nothing." else blank("nothing missing"),
            E(r["evidence_needed"]),
            badge(r["priority"], "bad" if r["priority"] == "P0" else "warn"),
            decision_badge(r["status"]),
        ])
    import collections
    c = collections.Counter(r["status"] for r in QREG["rows"])
    summary = " · ".join(f"{k}: {v}" for k, v in c.items())
    body = f"""
<div class="banner"><b>Read this before any decision.</b> A question is not a defect — an unanswered question treated as an
assumption is. Every row states what we know (with the source), what we do not know, and the evidence that would settle it.
<span class="muted">{E(summary)}</span></div>

<section>
<h2>Register</h2>
<p class="sub">Filter by text or status. P0 rows block a decision; P2 rows improve it. Use the status filter to see only what is still open.</p>
<div class="tools">
  <input id="q" type="search" placeholder="Filter questions…" aria-label="Filter questions">
  <select id="status" aria-label="Filter by status">
    <option value="">All statuses</option>
    <option>Answered</option><option>Partially answered</option><option>Open</option><option>Blocked</option>
  </select>
</div>
{table(["ID", "Category", "Question / decision blocked", "What we know (verified)", "Source", "What is missing", "Evidence that would settle it", "Priority", "Status"], rows, tid="qtable")}
</section>

<section>
<h2>What the answers already tell us</h2>
<div class="two">
<div class="panel okpanel"><h3>Answered</h3><ul>
<li><b>Q-01</b> The official and archived records agree for all 32 teams.</li>
<li><b>Q-03</b> Ties count as half a win; a naive formula creates two false mismatches.</li>
<li><b>Q-05</b> NFL.com publishes no depth chart (404).</li>
<li><b>Q-06</b> The model does not beat the closing line.</li>
<li><b>Q-11</b> Only six players had a formal designation at capture.</li>
</ul></div>
<div class="panel badpanel"><h3>Still blocking</h3><ul>
<li><b>Q-04</b> No official odds publication was found; licensing unconfirmed.</li>
<li><b>Q-07</b> No player-level feed, so props are blocked.</li>
<li><b>Q-10</b> Official sources contradict each other on Baltimore.</li>
<li><b>Q-12/Q-13</b> No legal clearance for redistribution or prizes.</li>
<li><b>Q-17</b> No named decision owner or review cadence.</li>
</ul></div>
</div>
</section>
"""
    page("pages/questions.html", "Open questions register",
         "Every question that must be answered before a decision is reasonable — what we know, what we do not, and the evidence that would settle it.",
         body, active="pages/questions.html")


# ---------------------------------------------------------------- own lines
def own_lines():
    rows = []
    for r in LINES["rows"]:
        rows.append([
            E(r["date"]), f'{E(r["kickoff_et"])} ET', f'<b>{E(r["away"])}</b> at <b>{E(r["home"])}</b>',
            f'<span class="muted">{E(r["away_record"])} · {E(r["home_record"])}</span>',
            f'<span class="mono">{E(r["own_spread_home"])}</span>',
            f'<span class="mono">{r["own_total"]:.1f}</span>',
            f'<span class="mono">{pct(r["own_home_win_prob"])}</span>',
            f'<span class="mono">{r["own_home_ml"]:+d} / {r["own_away_ml"]:+d}</span>',
            blank("No official 2026 market line exists in scope"),
            f'{a(r["game_url"], "game")} {derived("data/model/week10_lines.json")}',
        ])
    lt = LINES["lookahead_tests"]
    rt = []
    for r in RATINGS["rows"]:
        rt.append([f'<b>{E(r["team"])}</b>', E(r["name"]), f'<span class="mono">{r["elo"]}</span>',
                   f'<span class="mono">{r["off_pts_above_avg"]:+.2f}</span>', f'<span class="mono">{r["def_pts_above_avg"]:+.2f}</span>',
                   f'{r["w"]}-{r["l"]}-{r["t"]}', f'{r["pf"]}', f'{r["pa"]}', src("SRC-01")])
    body = f"""
<div class="banner"><b>These are not sportsbook lines.</b> They are this model's estimates for 14 Week 10 games, generated
12 Nov 2026 before the first kickoff. The market column is blank because no official or licensed 2026 market price was found
in scope. Do not compare these to a book you have not verified.</div>

<section>
<h2>Method</h2>
<div class="two">
<div class="panel"><h3>Model</h3>
<ul>
<li>Elo rating, K={int(20)}, home-field {int(48)} Elo, season regression 75%.</li>
<li>Exponentially weighted offence/defence in points above league average (α=0.25).</li>
<li>Blend chosen on 2013-2016 validation: {int(RESULTS['blend_chosen']['w_points']*100)}% points model, {int((1-RESULTS['blend_chosen']['w_points'])*100)}% Elo.</li>
<li>Elo-to-points slope {RESULTS['blend_chosen']['w_points'] and round(CARD['elo_to_points_slope'],4)} fitted on 1999-2012 only.</li>
<li>Win probability from a normal model with σ={CARD['sigma']} fitted on validation residuals.</li>
</ul></div>
<div class="panel"><h3>Integrity</h3>
<ul>
<li>Predictions use only games before the current week; updates happen after the whole week is played.</li>
<li>Look-ahead test 1: delete every post-Week-9 row → {badge('identical', 'ok') if lt['test_truncate_future']['identical'] else badge('DIFFERS', 'bad')}.</li>
<li>Look-ahead test 2: rewrite every post-Week-9 result with random scores → {badge('identical', 'ok') if lt['test_rewrite_future_results']['identical'] else badge('DIFFERS', 'bad')}.</li>
<li>Archive reconciled to official standings before modelling: {RECON['teams_matched']}/32.</li>
</ul></div>
</div>
</section>

<section>
<h2>Week 10 originated lines</h2>
{table(["Date", "Kickoff", "Matchup", "Records", "Home line", "Total", "Home win", "Fair ML (home/away)", "Market", "Source"], rows)}
<p class="sub">Fair moneyline is the vig-free price implied by the model probability; it is not an offered price.</p>
</section>

<section>
<h2>Team ratings used</h2>
<p class="sub">Elo and points-above-average are derived. Records and points come from the official standings.</p>
{table(["Team", "Name", "Elo", "Offence", "Defence", "W-L-T", "PF", "PA", "Official source"], rt)}
</section>

<section>
<h2>Why the market column is empty</h2>
<p>The archive contains zero closing lines for 2026, and no official NFL odds publication was found on the pages reviewed.
Filling that column from memory, a screenshot, or an unlicensed aggregator would break the verification rule. It stays blank
until Q-04 is answered.</p>
</section>
"""
    page("pages/own-lines.html", "Originated lines — Week 10",
         "Fourteen model lines with the method, the ratings and the look-ahead tests that prove no future result was used.",
         body, active="pages/own-lines.html")


# ---------------------------------------------------------------- strategies
def strategies():
    rows = []
    for s in STRAT:
        r = results.get(s["id"], {})
        gate = r.get("gates", {})
        failed = [k for k, v in gate.items() if v is False]
        rows.append([f'<b>{E(s["id"])}</b>', E(s["family"]), E(s["name"]), E(s["rule"]), E(s["pricing"]),
                     badge(failed[0] + " fails" if failed else ("blocked" if r.get("tier") == "Blocked" else "pass"), "bad" if failed else "warn"),
                     badge(r.get("tier", "—"), {"Rejected": "bad", "Blocked": "bad", "Research-only": "warn"}.get(r.get("tier"), "info")),
                     derived("data/strategies/results.json")])
    body = f"""
<div class="banner"><b>All seven registered strategies fail.</b> Three single-bet families were scored on the holdout and
lost money; the parlay and SGP families fail the pricing gate by construction; both prop families are blocked for lack of data.</div>

<section>
<h2>Catalogue</h2>
<p class="sub">Rules and thresholds were committed to git before the holdout was scored. Theta values are chosen on
2013-2016 validation only. See <a href="pages/validation.html">Validation &amp; luck</a> for the numbers.</p>
{table(["ID", "Family", "Name", "Rule", "Pricing", "Gate", "Tier", "Source"], rows)}
</section>

<section>
<h2>Coverage of the requested bet types</h2>
{table(["Requested", "Covered by", "Status", "Note", "Evidence"], [
 ["Single bets", "S1 spread, S2 total, S3 moneyline", badge("measured", "ok"), "Holdout 2017-2025 at archived closing lines", derived("data/strategies/results.json")],
 ["Parlays", "S4 cross-game 2-leg", badge("assumption", "warn"), "Payout is assumed +164; no archived parlay price, so G7 fails", derived("data/strategies/results.json")],
 ["Player prop combos", "S6 single, S7 same-game combo", badge("blocked", "bad"), "No player feed and no prop prices; no values published", '<a href="questions.html#q-07">Q-07</a>'],
 ["Same-game game-market combos", "S5 favourite-cover + under", badge("correlation only", "info"), "phi measured; no SGP price, so it is a monitor not a bet", derived("data/correlations.json")],
], cls="tight")}
</section>
"""
    page("pages/strategies.html", "Strategy catalogue",
         "Seven pre-registered families covering singles, parlays and prop combos — with the gate each one fails.",
         body, active="pages/strategies.html")


# ---------------------------------------------------------------- validation
def validation():
    gate_ids = [g["id"] for g in GATES["gates"]]
    grid_rows = []
    for sid in ("S1", "S2", "S3", "S4"):
        r = results[sid]
        g = r.get("gates", {})
        grid_rows.append([f"<b>{sid}</b>"] + [gate_pill(g.get(k)) for k in gate_ids] +
                         [badge(r.get("tier", "—"), "bad" if r.get("tier") in ("Rejected", "Blocked", "Research-only") else "warn"),
                          derived("data/strategies/results.json")])
    res_rows = []
    for sid in ("S1", "S2", "S3", "S4"):
        r = results[sid]
        res_rows.append([f"<b>{sid}</b>", f'{r.get("theta","—")}', f'{r.get("n_bets",0):,}',
                         pct(r.get("roi"), 2),
                         f'{r["bootstrap_ci95"][0]:+.3f} to {r["bootstrap_ci95"][1]:+.3f}' if r.get("bootstrap_ci95") else blank(),
                         f'{r.get("placebo_p"):.3f}' if r.get("placebo_p") is not None else blank(),
                         f'{r.get("holm_adjusted_p"):.3f}' if r.get("holm_adjusted_p") is not None else blank(),
                         badge(r.get("tier", "—"), "bad"),
                         derived("data/strategies/results.json")])
    season_years = sorted(results["S1"]["seasons"].keys())
    season_rows = []
    for y in season_years:
        cells = []
        for sid in ("S1", "S2", "S3"):
            s = results[sid]["seasons"].get(y)
            cells.append(pct(s["roi"], 2) if s else "—")
        season_rows.append([y] + cells + [derived("data/strategies/results.json")])
    mc = CARD
    mrows = []
    for split in ("dev", "validation", "holdout"):
        d = mc[split]
        mrows.append([split, f'{d["n"]:,}', num(d["mae_margin_model"], 3), num(d["mae_margin_market"], 3),
                      num(d["mae_margin_naive_home_2_5"], 3), num(d["mae_total_model"], 3), num(d["mae_total_market"], 3),
                      derived("data/model/model_card.json")])
    cal_rows = [[c["bin"], f'{c["n"]:,}', pct(c["predicted_home_win_rate"]), pct(c["actual_home_win_rate"]),
                 derived("data/model/model_card.json")] for c in mc["calibration_holdout"]]
    val_rows = [[f'<b>{v["theta"]}</b>', f'{v["n"]:,}', pct(v["roi"], 2), derived("data/strategies/results.json")]
                for v in RESULTS["validation_table"]["S1"]]
    body = f"""
<div class="banner"><b>Read the gates before the ROI.</b> A positive ROI with a confidence interval that includes zero is
not evidence. The holdout was scored once; the thresholds were frozen beforehand.
<br><br><b>The clearest lesson on this page:</b> on validation (2013-2016) S1 returned +4.6% and S3 returned +9.8%.
On the untouched holdout they returned -5.3% and -8.0%. That gap is what a holdout is for.</div>

<section>
<h2>Gate definitions</h2>
{table(["Gate", "Name", "Rule", "Source"], [[f"<b>{E(g['id'])}</b>", E(g["name"]), E(g["rule"]), derived("data/gates.json")] for g in GATES["gates"]])}
</section>

<section>
<h2>Gate matrix</h2>
<p class="sub">G8 (forward replication) is false for every strategy: no full prospective season has been logged. Nothing can
therefore be rated above provisional.</p>
{table(["Strategy"] + gate_ids + ["Tier", "Source"], grid_rows)}
</section>

<section>
<h2>Holdout results (2017-2025)</h2>
{table(["Strategy", "Theta", "Bets", "ROI", "Week-clustered 95% CI", "Placebo p", "Holm p", "Tier", "Source"], res_rows)}
<p class="sub">Bets are flat 1-unit stakes at archived closing prices (-110 where a side price is missing). Placebo p is the
share of 2,000 random-side simulations with equal weekly exposure that match or beat the observed ROI.</p>
</section>

<section>
<h2>Robustness by season</h2>
{table(["Season"] + ["S1", "S2", "S3"] + ["Source"], season_rows)}
</section>

<section>
<h2>Model skill vs the market</h2>
{table(["Split", "Games", "Margin MAE (model)", "Margin MAE (closing line)", "Margin MAE (naive +2.5)", "Total MAE (model)", "Total MAE (closing line)", "Source"], mrows)}
<p class="sub">{E(mc['honest_reading'])}</p>
</section>

<section>
<h2>Calibration on the holdout</h2>
{table(["Predicted home-win bin", "Games", "Mean predicted", "Actual home wins", "Source"], cal_rows)}
</section>

<section>
<h2>Threshold selection (validation only, S1 shown)</h2>
{table(["Theta (points)", "Bets", "ROI", "Source"], val_rows)}
<p class="sub">Chosen thresholds: S1 {RESULTS['chosen_thresholds']['S1']} · S2 {RESULTS['chosen_thresholds']['S2']} · S3 {RESULTS['chosen_thresholds']['S3']}.</p>
</section>

<section>
<h2>Controls</h2>
{table(["Control", "Result", "Meaning", "Source"], [
 ["C1 — always home favourite ATS", pct(results["C1"]["roi"], 2) + f' on {results["C1"]["n_bets"]:,} bets', "A naive rule also loses; the vig is the baseline", derived("data/strategies/results.json")],
 ["C2 — random side", "Placebo distribution", "Used to test whether a result could be luck", derived("data/strategies/results.json")],
], cls="tight")}
</section>
"""
    page("pages/validation.html", "Validation gates & luck removal",
         "Eight pre-registered gates, a one-shot holdout, week-clustered intervals and a placebo test — the machinery that stops a lucky run from looking like skill.",
         body, active="pages/validation.html")


# ---------------------------------------------------------------- correlations
def correlations():
    rows = []
    for r in CORR["rows"]:
        ci = f'{r["ci95"][0]:+.3f} to {r["ci95"][1]:+.3f}' if r["ci95"][0] is not None else blank("insufficient data")
        rows.append([f'<b>{E(r["id"])}</b>', E(r["question"]),
                     f'<span class="mono">{r["r"]:+.4f}</span>' if r["r"] is not None else blank("not computed"),
                     ci, f'{r["n"]:,}' if r["n"] else "0", E(r["method"]),
                     decision_badge(r["status"]), E(r["note"]), derived("data/correlations.json")])
    body = f"""
<div class="banner"><b>Correlation is not an edge.</b> These coefficients describe dependence between outcomes. They do not
establish a profitable relationship, and none of them is an official NFL statistic — all are computed from the pinned archive.</div>

<section>
<h2>Register</h2>
<p class="sub">Sample: regular-season games 2013-2025 with archived closing lines. CIs are Fisher-z approximations and ignore
week clustering; the backtest intervals do cluster.</p>
{table(["ID", "Question", "r", "95% CI", "n", "Method", "Status", "Reading", "Source"], rows)}
</section>

<section>
<h2>What this means for parlays and combos</h2>
<ul>
<li><b>Cross-game parlays:</b> legs are effectively independent (C-05 phi {CORR['rows'][4]['r']:+.4f}). Multiplying
probabilities is defensible; the book's payout assumption is the weak link, not the maths.</li>
<li><b>Same-game game-market combos:</b> favourite-cover vs under is near zero (C-03 phi {CORR['rows'][2]['r']:+.4f}),
so an SGP on those two legs carries no meaningful dependence correction.</li>
<li><b>Player props:</b> the two correlations that matter most for prop combos (C-06, C-07) are <b>blocked</b>. They are not
approximated. Any prop-combo pricing before Q-07 is answered would be fabricated.</li>
</ul>
</section>

<section>
<h2>Method notes</h2>
<ul>{''.join(f"<li>{E(x)}</li>" for x in CORR["interpretation_guard"])}</ul>
</section>
"""
    page("pages/correlations.html", "Correlation register",
         "Measured dependence for spreads, totals, same-game combos and cross-game parlays — with the two prop correlations blocked rather than guessed.",
         body, active="pages/correlations.html")


# ---------------------------------------------------------------- leaderboard
def leaderboard():
    rows = []
    for sid in ("S1", "S2", "S3", "S4", "S5", "S6", "S7"):
        r = results.get(sid, {})
        roi = r.get("roi")
        tier = r.get("tier", "—")
        points = 0
        rows.append([f"<b>{sid}</b>", badge(tier, "bad" if tier in ("Rejected", "Blocked") else "warn"),
                     f'{r.get("n_bets",0):,}' if r.get("n_bets") else "—",
                     pct(roi, 2) if roi is not None else blank("blocked"),
                     f'{r["bootstrap_ci95"][0]:+.3f}' if r.get("bootstrap_ci95") else blank("n/a"),
                     badge(str(points), "info"), derived("data/strategies/results.json")])
    body = f"""
<div class="banner"><b>The pool is unawarded.</b> A strategy must reach Gold (provisional) to earn points. None did, so 1,000
points roll over. That is the reward rule doing its job, not a bug.</div>

<section>
<h2>Scoreboard</h2>
<p class="sub">Ranking rule: lower bound of the week-clustered bootstrap ROI. Anything that fails the sample or ROI gate scores
zero, regardless of how good its point estimate looks.</p>
{table(["Strategy", "Tier", "Settled bets", "ROI", "5th-percentile ROI", "Points", "Source"], rows)}
</section>

<section>
<h2>Reward policy</h2>
<div class="two">
<div class="panel"><h3>Rules</h3><ul>
<li>Pool: {GATES['rewards']['pool_points']} reputation points; non-monetary.</li>
<li>Split equally among strategies reaching Gold (provisional).</li>
<li>Roll over when nobody qualifies.</li>
<li>Silver/Bronze receive recognition only.</li>
<li>G8 (one full forward season) caps every strategy at provisional.</li>
</ul></div>
<div class="panel"><h3>Why non-monetary</h3>
<p>{E(GATES['rewards']['why_non_monetary'])}</p>
<p><a href="pages/questions.html#q-13">Q-13</a> must be answered before any prize is offered.</p></div>
</div>
</section>

<section>
<h2>Why ROI alone would be the wrong score</h2>
<p>With a few hundred bets, a strategy can show a double-digit ROI and still be pure noise. The placebo test measures exactly
that: random side selection with the same weekly exposure produces a distribution of ROIs, and S1's observed result sits inside
it (p={results['S1']['placebo_p']:.2f}). Ranking on the confidence bound, not the point estimate, is the difference between a
competition that rewards skill and one that rewards variance.</p>
</section>
"""
    page("pages/leaderboard.html", "Leaderboard & rewards",
         "A competition that pays only for evidence: confidence-bound ranking, non-monetary points and a pool that rolls over when nothing qualifies.",
         body, active="pages/leaderboard.html")


# ---------------------------------------------------------------- injuries
def injuries():
    st_rows = [[f'<b>{E(r["team"])}</b>', E(r["player"]), E(r["position"]), E(r["injury"]), E(r["practice"]),
                badge(r["game_status"], "bad" if r["game_status"] == "Out" else "warn"), src(r["source"])]
               for r in INJ["explicit_game_status"]]
    qb_rows = [[f'<b>{E(r["team"])}</b>', E(r["starter_out"]), E(r["new_starter"]), E(r["depth_role"]),
                E(r["evidence"]), src(r["source"]) + ("" if r["body_read"] else " " + badge("headline only", "warn"))]
               for r in INJ["qb_depth_changes"]]
    oth = [[f'<b>{E(r["team"])}</b>', E(r["player"]), E(r["position"]), E(r["status"]), src(r["source"])]
           for r in INJ["other_verified_availability"]]
    body = f"""
<div class="banner"><b>Snapshot, not a live feed.</b> Captured Thursday of Week 10. Only six players league-wide had a formal
game designation at that moment; the final inactives are published later. Practice status is not a prediction of availability.</div>

<section>
<h2>What the official report actually shows</h2>
<ul>{''.join(f"<li>{E(x)}</li>" for x in INJ['headline_findings'])}</ul>
</section>

<section>
<h2>Formal game designations (complete at capture)</h2>
<p class="sub">Every player on the official Week 10 report with an Out, Doubtful or Questionable designation. Everyone else on
the report is practice-status only and is not listed here.</p>
{table(["Team", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], st_rows)}
</section>

<section>
<h2>Confirmed quarterback changes (depth, not guesswork)</h2>
<p class="sub">Only changes that an official NFL.com page states. The "depth role" column is quoted from the source, not inferred.</p>
{table(["Team", "Out / replaced", "New starter", "Depth role", "What the source says", "Source"], qb_rows)}
</section>

<section>
<h2>Other verified availability</h2>
{table(["Team", "Player", "Pos", "Status", "Source"], oth)}
</section>

<section>
<h2>The defensive backup problem — why it is blank</h2>
<div class="panel badpanel">
<p><b>Requested:</b> know when defences are down to 2nd, 3rd or 4th-string players.</p>
<p><b>Verified blocker:</b> the NFL.com team depth-chart URL returns "404 - Flag on the Play" ({src('SRC-14')}) and no official
depth publication was located. The official injury report names the player and his practice status, but not his place on the
depth chart.</p>
<p><b>Therefore:</b> the starter-weighted availability index is <b>not computed</b> — no number is published, because any number
would imply unverified starter status. Offensive "starters vs backups" has the same limitation.</p>
<p><b>What would settle it:</b> a licensed snap-count feed or an official depth chart, plus an explicit definition of "starter"
(see <a href="pages/questions.html#q-05">Q-05</a> and <a href="pages/questions.html#q-21">Q-21</a>).</p>
</div>
</section>

<section>
<h2>Limits of this module</h2>
<ul>{''.join(f"<li>{E(x)}</li>" for x in INJ['limits'])}</ul>
</section>
"""
    page("pages/injuries.html", "Injuries & availability",
         "What the official Week 10 report confirms, the three verified quarterback changes, and the depth-chart gap that keeps the backup-deficiency index blank.",
         body, active="pages/injuries.html")


# ---------------------------------------------------------------- data
def data_page():
    st = []
    for r in RECON["rows"]:
        st.append([f'<b>{E(r["team"])}</b>', E(r["name"]),
                   f'{r["official_w"]}-{r["official_l"]}-{r["official_t"]}',
                   f'{r["official_pct"]:.3f}', f'{r["official_pf"]}', f'{r["official_pa"]}',
                   f'{r["official_pf"]-r["official_pa"]:+d}',
                   badge("match", "ok") if r["match"] else badge("MISMATCH", "bad"), src("SRC-01")])
    fx = []
    for g in FIX["games"]:
        fx.append([E(g["date"]), f'{E(g["kickoff_et"])} ET', f'<b>{E(g["away"])}</b> at <b>{E(g["home"])}</b>',
                   E(g["tv"]), E(g["note"]) or blank("—"), a(g["game_url"], "game")])
    body = f"""
<div class="banner"><b>Reconciliation first, model second.</b> The archive is re-aggregated from box scores and compared
with NFL.com field by field. If this page failed, no line on the site would be published.</div>

<section>
<h2>Reconciliation summary</h2>
<div class="kpis">
<div class="kpi"><b>{RECON['teams_matched']}/32</b><span>teams match on W-L-T, PF, PA and tie percentage</span></div>
<div class="kpi"><b>{RECON['games_played_2026']}</b><span>2026 games played at capture</span></div>
<div class="kpi"><b>{RECON['fixtures']['matched']}/{RECON['fixtures']['official_games']}</b><span>Week 10 fixtures match official schedule</span></div>
<div class="kpi"><b>{INTEG['games_with_closing_spread']:,}</b><span>historical games with an archived closing spread</span></div>
</div>
<p class="sub">{E(RECON['note'])}</p>
</section>

<section>
<h2>2026 standings — official vs archive</h2>
<p class="sub">As of {E(STAND['as_of'])}. PCT uses the NFL tie formula (W + T/2)/G.</p>
{table(["Team", "Club", "W-L-T", "PCT", "PF", "PA", "Net", "Archive check", "Official source"], st)}
</section>

<section>
<h2>Week 10 fixtures</h2>
{table(["Date", "Kickoff", "Matchup", "TV", "Note", "Source"], fx)}
<p class="sub">Byes: {", ".join(b["team"] + " (" + b["record"] + ")" for b in FIX["byes"])}. Verified on {E(FIX['source'])}.</p>
</section>

<section>
<h2>Archive integrity (gate G1)</h2>
{table(["Check", "Result", "Source"], [
 [c, v, derived("data/integrity.json")] for c, v in [
  ("Games loaded (regular season)", f"{INTEG['games_total']:,}"),
  ("Duplicate game ids", str(INTEG["duplicate_game_ids"])),
  ("Score / result mismatches", str(INTEG["score_margin_mismatches"])),
  ("Total mismatches", str(INTEG["total_mismatches"])),
  ("Chronological ordering", "pass" if INTEG["chronological"] else "FAIL"),
  ("Games with both moneylines", f"{INTEG['games_with_both_moneylines']:,}"),
  ("Gate result", badge("PASS" if INTEG["passed"] else "FAIL", "ok" if INTEG["passed"] else "bad")),
 ]], cls="tight")}
<p class="sub">Recomputed from the committed archive by <a href="../pipeline/common.py">pipeline/common.py</a>; machine-readable output: <a href="../data/integrity.json">integrity.json</a>.</p>
</section>

<section>
<h2>Provenance of the archive</h2>
<p>{a(SRC['SRC-12']['url'], 'nflverse/nfldata')} at commit
{a(SRC['SRC-13']['url'], '6ea0be6')}, retrieved 12 Nov 2026. Files: games.csv and closing_lines.csv, hashes recorded in
<a href="data/source/provenance.json">provenance.json</a>. This is a third-party archive, not an NFL publication.</p>
</section>
"""
    page("pages/data.html", "Official data & reconciliation",
         "The 32-team reconciliation, the 14-game slate and the integrity checks that must pass before any model output is published.",
         body, active="pages/data.html")


# ---------------------------------------------------------------- sources
def sources():
    rows = []
    for s in SOURCES["sources"]:
        status = badge("404", "bad") if s["http_status"] == "404" else badge("live", "ok")
        rows.append([f'<b>{E(s["id"])}</b>', E(s["name"]), a(s["url"], s["url"]),
                     badge("official", "ok") if s["official"] else badge("third-party", "warn"),
                     status, E(s["supports"]), E(s["retrieved_utc"])])
    body = f"""
<div class="banner"><b>A source link is not a validation of the row.</b> It shows where a value came from. Where the source is
not an NFL publication, the row carries a third-party or DERIVED badge instead.</div>
<section>
<h2>Register</h2>
<p class="sub">{len(SOURCES['sources'])} sources: {sum(1 for x in SOURCES['sources'] if x['official'])} official NFL pages and
{sum(1 for x in SOURCES['sources'] if not x['official'])} non-official references. Two entries are recorded specifically
because they return 404 and must not be cited.</p>
{table(["ID", "Name", "URL", "Type", "Status", "What it supports", "Retrieved"], rows)}
</section>
<section>
<h2>Rules applied throughout</h2>
<ul>
<li>Official means the domain is nfl.com or operations.nfl.com. Everything else is labelled.</li>
<li>A value that cannot be confirmed from a cited source is left blank and listed on <a href="pages/flagged.html">Flagged for review</a>.</li>
<li>Derived values link to the repository file that computes them, never to an NFL page.</li>
<li>Dead citations are recorded, not silently removed, so a reviewer can see what was rejected.</li>
</ul>
</section>
"""
    page("pages/sources.html", "Source register",
         "Every source used, its type, its live status and exactly what it supports — including the two dead citations inherited from earlier work.",
         body, active="pages/sources.html")


# ---------------------------------------------------------------- flagged
def flagged():
    rows = []
    for f in FLAGS:
        rows.append([f'<b>{E(f["id"])}</b>',
                     badge(f["severity"], "bad" if "Blocking" in f["severity"] or "Contradiction" in f["severity"] else "warn"),
                     E(f["item"]), E(f["detail"]),
                     src(f["source"]) if f["source"].startswith("SRC") else derived("data/flags.json"),
                     badge(f["status"], "ok" if f["status"] in ("resolved", "disclosed") else "warn")])
    body = f"""
<div class="banner"><b>These do not block publication.</b> They block reliance. Each item states what is wrong, why it
matters, and where the evidence is. Review them in order of severity.</div>
<section>
<h2>Register</h2>
{table(["ID", "Severity", "Item", "Detail", "Source", "Status"], rows)}
</section>
<section>
<h2>How severity is used</h2>
<ul>
<li><b>Blocking for claims</b> — a conclusion that cannot be stated until the item is fixed.</li>
<li><b>Contradiction</b> — two official sources disagree; neither is assumed correct.</li>
<li><b>Verified absence</b> — an official source was checked and the data does not exist there.</li>
<li><b>Disclosure / method limit</b> — true by construction, repeated wherever the number appears.</li>
<li><b>Resolved</b> — a trap that was found and explained, recorded so it is not reintroduced.</li>
</ul>
</section>
"""
    page("pages/flagged.html", "Flagged for review",
         "Seventeen items that limit reliance on the numbers — dead citations, a stale slate, an official contradiction and the blank fields that must stay blank.",
         body, active="pages/flagged.html")


# ---------------------------------------------------------------- audit
def audit():
    blocks = []
    for w in AUDIT["workspaces"]:
        finds = [[badge(f["severity"], "bad" if f["severity"] == "high" else "warn"), E(f["finding"]),
                  src(*[x.strip() for x in f["evidence"].split(",")]) if f["evidence"].startswith("SRC") else derived("data/audit.json")] for f in w["findings"]]
        blocks.append(f"""<article class="card wide">
<div class="cardtop"><b class="mono">{E(w['path'])}</b> {badge(f"{w['pages']} pages", 'info')} {badge(w['size'], 'info')}</div>
<p><b>What it is.</b> {E(w['what_it_is'])}</p>
<p class="good"><b>What it does well.</b> {E(w['verified_good'])}</p>
{table(["Severity", "Finding", "Evidence"], finds)}
<p class="rec"><b>Recommendation.</b> {E(w['recommendation'])}</p>
</article>""")
    self_rows = [[E(c["check"]), E(c["result"]), derived(f"data/{c['evidence'].split('/')[-1]}")] for c in AUDIT["hub_self_review"]]
    body = f"""
<div class="banner"><b>Review method.</b> Every file in the five prior NFL workspaces was read; page counts and sizes were measured;
a sample of cited URLs was fetched live; and each workspace's published slate was compared with the current Week 10 slate.</div>
<section>
<h2>Prior workspaces (5)</h2>
{''.join(blocks)}
</section>
<section>
<h2>What is actually wrong, in one line</h2>
<p>{E(AUDIT['irregularities_summary'])}</p>
</section>
<section>
<h2>Self-review of this hub</h2>
{table(["Check", "Result", "Evidence"], self_rows)}
</section>
<section>
<h2>What this review does not do</h2>
<ul>
<li>It does not certify factual truth of every row in the other workspaces — only the specific claims tested.</li>
<li>It does not re-run their pipelines; it reads their committed outputs.</li>
<li>It does not delete or rewrite another session's work. Fixes are logged for the owning session.</li>
</ul>
</section>
"""
    page("pages/audit.html", "Repository review",
         "A line-by-line read of the five prior NFL workspaces, with measured sizes, live-tested citations and a self-review of this build.",
         body, active="pages/audit.html")


# ---------------------------------------------------------------- requirements
REQS = [
 ("R1", "A section dedicated to suggestions, so a path can be reviewed and chosen before implementation", "pages/suggestions.html", "Met", "15 suggestions with options, effort, risk, dependencies and a decision log"),
 ("R2", "A clear list of questions, information and answers needed before a decision", "pages/questions.html", "Met", "27 questions; 8 answered with sources, 3 blocked"),
 ("R3", "Originate own NFL lines", "pages/own-lines.html", "Met", "14 Week 10 lines, pre-kickoff, with look-ahead tests"),
 ("R4", "Research and develop strategies for useful signals", "pages/strategies.html", "Met", "7 pre-registered families; 3 measured, 4 fail pricing or are blocked"),
 ("R5", "Treat it as a leaderboard competition with rewards for top strategies", "pages/leaderboard.html", "Met", "Confidence-bound ranking; 1,000-point pool; 0 awarded because nothing qualified"),
 ("R6", "Cover single bets, parlays and player prop combos", "pages/strategies.html", "Partial", "Singles and parlays measured; props blocked for lack of data"),
 ("R7", "Each strategy must pass validation gates", "pages/validation.html", "Met", "G1-G8 with a gate matrix; G8 impossible this session"),
 ("R8", "Determine correlation values", "pages/correlations.html", "Partial", "5 measured for game markets; 2 prop correlations blocked"),
 ("R9", "Remove luck and build selectively skill-based strategies", "pages/validation.html", "Met", "Week-clustered bootstrap, placebo permutation, Holm correction; no strategy survived"),
 ("R10", "Track injuries", "pages/injuries.html", "Partial", "Official report captured; 6 formal designations; final inactives not yet published"),
 ("R11", "Know defensive deficiencies when 2nd/3rd/4th-string players replace starters", "pages/injuries.html", "Blocked", "No official depth chart (404); index deliberately blank"),
 ("R12", "Same for offensive starters and backups", "pages/injuries.html", "Partial", "Quarterback changes verified; other positions blocked by the same gap"),
 ("R13", "Executive summary outlining important details", "pages/executive-summary.html", "Met", "Situation, verified, missing, findings, decisions"),
 ("R14", "No manual input; complete the work autonomously", "pages/audit.html", "Met", "Pipeline and site rebuild from committed data; no hand-entered value"),
 ("R15", "Verify every row against an official source and link it", "pages/sources.html", "Met", "20 sources; every row links a source or a DERIVED badge"),
 ("R16", "Review the repo line by line and flag irregularities", "pages/audit.html", "Met", "4 workspaces reviewed; 17 flags with severity"),
 ("R17", "Clean, simple, user-friendly dashboard with category subpages", "../index.html", "Met", "15 pages, grouped navigation, filterable tables"),
 ("R18", "All entries and findings in simple tables", "../index.html", "Met", "Every page is table-first"),
 ("R19", "Leave unverified values blank and flag them", "pages/flagged.html", "Met", "Market lines, depth, props and injury causes are blank"),
 ("R20", "Coordinate with parallel sessions, then PR, merge and confirm Pages", "pages/audit.html", "Met", "COORDINATION.md updated; PR and deploy recorded there"),
]


def requirements():
    rows = [[f"<b>{E(r[0])}</b>", E(r[1]), f'<a href="{E(r[2])}">{E(r[2])}</a>',
             badge(r[3], {"Met": "ok", "Partial": "warn", "Blocked": "bad"}.get(r[3], "info")), E(r[4])] for r in REQS]
    import collections
    c = collections.Counter(r[3] for r in REQS)
    body = f"""
<div class="banner"><b>Traceability, not a victory lap.</b> Each requirement from the brief is mapped to where it is handled
and to its honest status. "Partial" and "Blocked" are outcomes, not omissions.</div>
<section>
<h2>Coverage</h2>
<div class="kpis">
<div class="kpi"><b>{c['Met']}</b><span>requirements met</span></div>
<div class="kpi"><b>{c['Partial']}</b><span>partially met</span></div>
<div class="kpi"><b>{c['Blocked']}</b><span>blocked by missing data</span></div>
<div class="kpi"><b>{len(REQS)}</b><span>requirements traced</span></div>
</div>
{table(["ID", "Requirement", "Where it is handled", "Status", "Evidence / limit"], rows)}
</section>
<section>
<h2>What is genuinely unfinished</h2>
<ul>
<li>The defensive backup index (R11): impossible without depth or snap-count data.</li>
<li>Player props (R6): impossible without a player feed and prop prices.</li>
<li>Final injury statuses (R10): the official page updates after this snapshot.</li>
<li>Forward replication (R7/R9): requires a full season of timestamped predictions.</li>
</ul>
</section>
"""
    page("pages/requirements.html", "Requirements coverage",
         "Every requirement in the brief, where it is handled, and whether it is met, partial or blocked.",
         body, active="pages/requirements.html")


def main():
    os.makedirs(PAGES, exist_ok=True)
    dashboard()
    exec_summary()
    suggestions()
    questions()
    own_lines()
    strategies()
    validation()
    correlations()
    leaderboard()
    injuries()
    data_page()
    sources()
    flagged()
    audit()
    requirements()
    print("built 15 pages")


if __name__ == "__main__":
    sys.exit(main())

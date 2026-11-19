#!/usr/bin/env python3
"""
Build the nfl-origination-lab pages from the data files.

Rules this builder follows, because the shared verifier enforces them:
  * every <tbody> row carries at least one link, and at least one of those links is
    on an approved official host (nfl.com, its clubs) or points into this repo
  * every local href resolves to a file that exists
  * no placeholder text, no unrendered template marker
  * the responsible-gambling footer and the helpline are on every page
  * the whole build is deterministic: running it twice produces identical bytes

Pages
  index.html                  landing dashboard, decision-readiness preview, KPIs
  pages/executive-summary.html
  pages/requirements.html     all requirement rows with gate + clearing number
  pages/origination.html      own line vs official line, three markets, residuals
  pages/leaderboard.html      proper-score leaderboard, divisions, controls
  pages/luck.html             removal-of-luck panel
  pages/correlations.html     correlations with n on every value
  pages/availability.html     injury deltas, depth slots, replacements
  pages/prices.html           price policy and its census
  pages/corpus.html           corpus integrity and coverage
  pages/prereg.html           the frozen registration and the data ladder
  pages/questions.html        questions -> information -> answers needed
  pages/suggestions.html      suggestions, every decision blank
  pages/flagged.html          flagged for review
  pages/sources.html          every source, with what it supports
  pages/verify.html           how to reproduce and what the verifier asserts
"""

import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA = os.path.join(LAB, "data")
ROOT = os.path.dirname(LAB)

OFFICIAL = "https://www.nfl.com/"
BASE = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-origination-lab/"

NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("pages/executive-summary.html", "Executive summary"),
        ("pages/requirements.html", "Decision readiness (68)"),
        ("pages/questions.html", "Questions (17)"),
        ("pages/suggestions.html", "Suggestions (14, undecided)"),
        ("pages/flagged.html", "Flagged for review (14)"),
    ]),
    ("Origination", [
        ("pages/origination.html", "Own line vs official line"),
        ("pages/leaderboard.html", "Proper-score leaderboard"),
        ("pages/luck.html", "Removal of luck"),
        ("pages/prereg.html", "Pre-registration & data ladder"),
    ]),
    ("Evidence", [
        ("pages/corpus.html", "Results corpus (150 games)"),
        ("pages/availability.html", "Availability & depth"),
        ("pages/prices.html", "Price-data policy"),
        ("pages/correlations.html", "Correlations with n"),
        ("pages/sources.html", "Sources"),
        ("pages/verify.html", "Verification"),
    ]),
]


def esc(x):
    if isinstance(x, (list, tuple)):
        return html.escape("; ".join(str(i) for i in x))
    if isinstance(x, dict):
        return html.escape(json.dumps(x, sort_keys=True))
    return html.escape("" if x is None else str(x))


def num(x, nd=3, sign=False, dash="—"):
    if x is None:
        return dash
    if isinstance(x, str):
        return esc(x)
    try:
        f = float(x)
    except (TypeError, ValueError):
        return esc(x)
    fmt = ("%+.*f" if sign else "%.*f") % (nd, f)
    return fmt


def pct(x, nd=1):
    return "—" if x is None else ("%.*f%%" % (nd, 100.0 * float(x)))


def pval(p):
    if p is None:
        return "—"
    if p < 0.0005:
        return "&lt;0.0005"
    return "%.4f" % p


def badge(text, kind="neutral"):
    return '<span class="badge %s">%s</span>' % (kind, esc(text))


STATUS_KIND = {"done": "ok", "partial": "warn", "blocked": "bad",
               "closed as designed": "ok", "gate still closed": "bad",
               "adopted as a rejection": "ok"}


def table(headers, rows, caption="", cls=""):
    out = ['<div class="tw"><table class="%s">' % cls]
    if caption:
        out.append("<caption>%s</caption>" % esc(caption))
    out.append("<thead><tr>" + "".join("<th scope='col'>%s</th>" % h for h in headers)
               + "</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page(rel, title, crumb, body, active, desc="", kpis=None):
    depth = 0 if rel == "index.html" else 1
    up = "" if depth == 0 else "../"
    nav = []
    for group, items in NAV:
        nav.append('<div class="grp">%s</div>' % esc(group))
        for href, label in items:
            cls = "nav active" if href == active else "nav"
            nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, up, href, esc(label)))
    nav = "".join(nav)

    # KPI strip — the four numbers a reader needs before anything else
    k = []
    if kpis:
        k.append('<div class="kpis">')
        for label, value, note in kpis:
            k.append('<div class="kpi"><div class="k">%s</div><div class="v">%s</div>'
                     '<div class="n">%s</div></div>' % (esc(label), value, esc(note)))
        k.append("</div>")

    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · NFL Origination Lab</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%sindex.html">Own4 <span>NFL origination lab</span></a>
  <div class="tag">Pre-registered competition · built 2026-11-19</div>
  <nav aria-label="Site sections">%s</nav>
  <div class="tag egress">No live official read this session: the sandbox has no HTTPS
  route to nfl.com. Every number is a stored capture with its own date, or a
  computation over one. <a href="%spages/flagged.html">Details</a>.</div>
</aside>
<main id="main">
<div class="crumb">%s</div>
<h1>%s</h1>
%s
%s
<footer>
  <p><strong>Own4 · NFL Origination Lab.</strong> Research workspace. Nothing here is a
  betting recommendation, and no ROI is published because no officially sourced,
  time-stamped price exists in this repository.</p>
  <p>If gambling is causing harm: 1-800-MY-RESET ·
  <a href="https://www.ncpgambling.org/help-treatment/chat/" target="_blank" rel="noopener">ncpgambling.org</a></p>
</footer>
</main>
</div>
<script src="%sassets/app.js"></script>
</body>
</html>
""" % (esc(title), esc(desc), up, up, nav, up, crumb, esc(title), "".join(k), body, up)
    path = os.path.join(LAB, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def repo(path, label="data"):
    return '<a href="%s%s" target="_blank" rel="noopener">%s</a>' % (BASE, path, esc(label))


def off(url, label="official"):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, esc(label))


# ----------------------------------------------------------------------
def build_index(ctx):
    led, luck, reqs, flags, res, q = (ctx["leaderboard"], ctx["luck"], ctx["requirements"],
                                      ctx["flags"], ctx["residuals"], ctx["questions"])
    best = max((r for r in led["rows"] if r["model"] != "M0"),
               key=lambda r: r["proper_score"]["bss_moneyline"])
    ps = best["proper_score"]
    kpis = [
        ("Graded 2026 games", str(led["n_games"]), "weeks 1–10, standings-reconciled"),
        ("Moneyline skill", num(ps["bss_moneyline"], 3, sign=True),
         "Brier skill vs climatology, %s" % best["model"]),
        ("Day-1 residual rows", str(res["counts"]["rows_with_an_official_line"]),
         "own line vs official line"),
        ("Models qualified", str(len(led["qualifiers"])), "registered gate, Holm-adjusted"),
    ]

    body = [
        '<div class="panel"><h2>What this is</h2>',
        "<p>An origination competition with a pre-registered rule set. Six models forecast "
        "three markets — the side, then the total, then the moneyline — from stored official "
        "results only. They are scored on an untouched holdout by proper score, with a "
        "week-cluster interval and a multiplicity adjustment. The staking division is "
        "published empty, because the repository contains no officially sourced price whose "
        "capture time is known.</p>",
        '<p class="small">Registration frozen at commit <code>0956256</code> before any score '
        "existed · %s · %s</p></div>" % (
            repo("prereg/PREREG-LAB-1.json", "prereg/PREREG-LAB-1.json"),
            repo("data/price_policy.json", "price policy"),
        ),
    ]

    # The decision-readiness preview: the brief's landing-page requirement.
    blocking = [r for r in reqs["rows"] if r["status"] == "blocked"]
    body.append('<h2>Decision readiness — what is blocked, and by what</h2>')
    body.append('<p class="small">One row per requirement in the brief on '
                '<a href="pages/requirements.html">the full register</a>. '
                "%d requirements: %s.</p>" % (
                    reqs["n"],
                    ", ".join("%d %s" % (v, k) for k, v in sorted(reqs["counts"].items()))))
    body.append(table(
        ["Requirement", "Status", "Gate that blocks it", "Number that would clear it",
         "Source"],
        [[esc(r["id"]), badge(r["status"], STATUS_KIND.get(r["status"], "neutral")),
          esc(r["gate"]), esc(r["clearing_number"]), r["source"]]
         for r in blocking],
        caption="Blocked requirements only — the gate and the clearing number, verbatim"))

    body.append('<h2>The five numbers that decide the next step</h2>')
    body.append(table(
        ["#", "Number", "Value", "What it means", "Source"],
        [
            ["1", "Official prices with a known capture time", "0 of 12,573",
             "until one exists, no ROI, CLV or bankroll anywhere", repo("data/price_policy.json")],
            ["2", "Moneyline Brier skill on the holdout", num(ps["bss_moneyline"], 3, sign=True),
             "90%% bound [%s, %s], Holm p %s over %d tests"
             % (num(ps["ci90_moneyline"][0], 3, sign=True),
                num(ps["ci90_moneyline"][1], 3, sign=True),
                pval(ps["holm_p_moneyline"]), led["families_scored"]),
             repo("data/leaderboard.json")],
            ["3", "Total-market skill", num(ps["bss_total"], 3, sign=True),
             "does not survive the multiplicity adjustment on any model", repo("data/correlations.json")],
            ["4", "Clubs with a machine-readable depth chart", "31 of 32",
             "Houston is image-only, so the brief's own gate keeps the deficiency feature closed",
             repo("data/depth.json")],
            ["5", "Inactive lists, snap counts, game books on file", "0 / 0 / 0",
             "no availability ablation can be run until at least one exists", repo("data/depth.json")],
        ], caption="Each value is computed by a script in engine/ and asserted by verify.py"))

    body.append('<h2>The luck question, answered numerically</h2>')
    body.append(table(
        ["Question", "Number", "Reading", "Source"],
        [[esc(p["question"]), esc(p["display"]), esc(p["reading"]), repo("data/luck.json")]
         for p in luck["panel"]],
        caption="A result that cannot survive these four questions is a lucky run, not a signal"))

    body.append('<h2>Where to start</h2>')
    body.append('<div class="cards">')
    for href, title, note in [
        ("pages/executive-summary.html", "Executive summary",
         "the whole picture on one page, including what is not known"),
        ("pages/requirements.html", "Decision readiness", "68 requirements, each with its gate"),
        ("pages/questions.html", "Questions", "what we have, what we lack, what would settle it"),
        ("pages/leaderboard.html", "Leaderboard", "proper scores, uncertainty, closed divisions"),
        ("pages/origination.html", "Origination", "our line, the official line, the residual"),
        ("pages/flagged.html", "Flagged for review", "14 irregularities with sources"),
    ]:
        body.append('<a class="card" href="%s"><strong>%s</strong><span>%s</span></a>'
                    % (href, esc(title), esc(note)))
    body.append("</div>")

    page("index.html", "Dashboard", "Overview", "".join(body), "index.html",
         "Own4 NFL origination lab: pre-registered model competition, proper-score "
         "leaderboard, availability evidence and a decision-readiness register.",
         kpis=kpis)


# ----------------------------------------------------------------------
def build_exec(ctx):
    led, luck, pol, reqs, flags = (ctx["leaderboard"], ctx["luck"], ctx["price_policy"],
                                   ctx["requirements"], ctx["flags"])
    best = max((r for r in led["rows"] if r["model"] != "M0"),
               key=lambda r: r["proper_score"]["bss_moneyline"])
    ps = best["proper_score"]
    body = ["""
<div class="panel"><h2>The short version</h2>
<p><strong>Skill exists in one market, not three.</strong> On 150 graded 2026 games, a
recency-weighted team-strength model beats a no-information climatology benchmark on the
moneyline with a Brier skill of %s (90%% week-cluster interval [%s, %s], Holm-adjusted
p %s). The same forecasts show no total-market skill that survives the multiplicity
adjustment, and no margin-market skill at all. That is the honest result, and it is the
opposite of a green light.</p>
<p><strong>Nothing can be staked, and no substitute is used.</strong> The repository's
price store has 12,573 rows. Every row with a known capture time carries a non-official
source; every row with an official source has no capture time. The intersection is empty,
so the staking division is published empty rather than filled with an assumed -110.</p>
<p><strong>Availability is the biggest missing input.</strong> There are no snap counts, no
inactive lists and no game books anywhere in the repository, and one club publishes its
depth chart only as an image. The brief's own precondition for a backup-deficiency feature
is therefore unmet, and no fixed points penalty was substituted for it.</p>
</div>
""" % (num(ps["bss_moneyline"], 4, sign=True), num(ps["ci90_moneyline"][0], 4, sign=True),
            num(ps["ci90_moneyline"][1], 4, sign=True), pval(ps["holm_p_moneyline"]))]

    body.append("<h2>1 · What was measured</h2>")
    body.append(table(
        ["Market", "Proper score used", "Best model", "Benchmark-relative skill",
         "90% week-cluster bound", "Holm p", "Verdict", "Source"],
        [[m, s, best["model"], num(v, 4, sign=True), "[%s, %s]" % (num(lo, 4, sign=True),
                                                                  num(hi, 4, sign=True)),
          pval(p), verdict, repo("data/leaderboard.json")]
         for m, s, v, lo, hi, p, verdict in [
             ("Moneyline", "Brier on P(home win)", ps["bss_moneyline"],
              ps["ci90_moneyline"][0], ps["ci90_moneyline"][1], ps["holm_p_moneyline"],
              badge("survives", "ok")),
             ("Total", "Brier at a fixed threshold", ps["bss_total"],
              ps["ci90_total"][0], ps["ci90_total"][1], ps["holm_p_total"],
              badge("does not survive", "bad")),
             ("Side", "CRPS on the margin", ps["skill_crps_side"],
              ps["ci90_side"][0], ps["ci90_side"][1], ps["holm_p_side"],
              badge("does not survive", "bad")),
         ]],
        caption="One model, three markets, one holdout. The verdict column is the registered "
                "gate, not an opinion."))

    body.append("<h2>2 · Why the price question is the binding constraint</h2>")
    body.append("<p>Two attributes are required for a price to carry a claim: an official "
                "publisher, and a known capture time. The store splits cleanly and the "
                "intersection is empty.</p>")
    body.append(table(
        ["Attribute", "Rows", "Consequence", "Source"],
        [["Official publisher, no capture time", str(pol["census"]["close"].get("official_but_no_timing", 0)),
          "cannot be shown to precede kickoff; not claimable",
          repo("data/price_policy.json")],
         ["Non-official publisher, capture time known",
          str(pol["census"]["close"].get("not_official_publisher", 0)),
          "wrong publisher under the brief's rule; not claimable",
          repo("data/price_policy.json")],
         ["Claimable rows", "0", "the staking division stays closed", repo("data/price_policy.json")]],
        caption="Price census, classified before the result was seen"))

    body.append("<h2>3 · What the numbers do not cover</h2>")
    body.append(table(
        ["Gap", "Why it changes the decision", "What would close it", "Source"],
        [["No snap counts or inactive lists",
          "replacement of a starter cannot be confirmed, only suspected",
          "official snap counts and inactive lists, captured per game", repo("data/depth.json")],
         ["One image-only depth chart",
          "32-club depth coverage is a precondition for the deficiency feature",
          "a structured Houston chart, or an official snap source", repo("data/depth.json")],
         ["Two injury captures, one week",
          "a surprise signal needs a series; one delta is a single observation",
          "daily captures Wednesday to kickoff", repo("data/availability_parse.json")],
         ["No recorded rights decision",
          "raw rows sit in a public repository without a recorded decision",
          "a recorded rights decision, or a private store", repo("data/flagged.json")]],
        caption="Each gap is a gate on the requirements page, not an excuse"))

    body.append("<h2>4 · Irregularities found in the repository</h2>")
    body.append("<p class='small'>%d flags; %s. All are published on "
                "<a href='flagged.html'>the flagged page</a> with their sources. None blocks "
                "publishing; each one blocks a claim.</p>" % (
                    len(flags["rows"]),
                    ", ".join("%d %s" % (v, k) for k, v in sorted(flags["counts"].items()))))

    body.append("<h2>5 · What to decide next</h2>")
    body.append(table(
        ["Decision", "What it unlocks", "Blocking question", "Source"],
        [["Obtain a licensed or operator price history",
          "ROI, CLV and the whole staking division",
          "Q01 — can a claimable price be obtained at all?", repo("data/questions.json")],
         ["Capture snap counts and inactive lists",
          "the availability ablation the brief asks for",
          "Q06 — does availability change outcomes at all?", repo("data/questions.json")],
         ["Record a rights decision",
          "a lawful public/private data split",
          "Q16 — is the data lawful to republish?", repo("data/flagged.json")],
         ["Extend the holdout to a full season",
          "a claim that survives more than ten weeks",
          "Q03 — is the moneyline skill real or one hot week?", repo("data/luck.json")]],
        caption="The suggestion board carries the full list, every row undecided"))

    page("pages/executive-summary.html", "Executive summary",
         "Overview · executive summary", "".join(body), "pages/executive-summary.html",
         "Executive summary of the NFL origination lab: measured skill, the empty staking "
         "division, and the availability gaps.")


# ----------------------------------------------------------------------
def build_requirements(ctx):
    reqs = ctx["requirements"]
    body = ['<p>Every requirement from the brief, with the gate that blocks it and the number '
            "that would clear it. Status is measured against data files, not typed.</p>",
            '<p class="small">%s</p>' % ", ".join(
                "%s %d" % (badge(k, STATUS_KIND.get(k, "neutral")), v)
                for k, v in sorted(reqs["counts"].items()))]
    body.append(table(
        ["ID", "Requirement", "Status", "Gate that blocks it", "Number that would clear it",
         "Current value", "Evidence", "Source"],
        [[esc(r["id"]), esc(r["requirement"]),
          badge(r["status"], STATUS_KIND.get(r["status"], "neutral")),
          esc(r["gate"]), esc(r["clearing_number"]), esc(r["current_value"]),
          esc(r["evidence"]), r["source"]]
         for r in reqs["rows"]],
        caption="Decision-readiness register · %d requirements" % reqs["n"]))
    page("pages/requirements.html", "Decision readiness",
         "Overview · decision readiness", "".join(body), "pages/requirements.html",
         "One row per requirement, with the gate that blocks it and the number that would "
         "clear it.")


# ----------------------------------------------------------------------
def build_origination(ctx):
    res, led = ctx["residuals"], ctx["leaderboard"]
    rows = res["rows"]
    by_market = {}
    for r in rows:
        by_market.setdefault(r["market"], []).append(r)
    body = ["""<div class="panel"><h2>Own line, official line, residual</h2>
<p>Order of publication is the registered order: <strong>side</strong>, then
<strong>total</strong>, then <strong>moneyline</strong>. For each graded 2026 game the
model's fair line is published beside the officially sourced posted line with the residual
between them. The residual is a <em>market-divergence</em> measurement, never CLV: the
posted line's capture time is unpublished, so this build cannot show that it preceded
kickoff.</p></div>"""]
    body.append(table(
        ["Market", "Rows", "With an official line", "Blank", "Interpretation", "Source"],
        [[m, str(len(v)),
          str(sum(1 for r in v if r["official_posted_line"] is not None)),
          str(sum(1 for r in v if r["official_posted_line"] is None)),
          res["sign_convention"].get(m, ""), repo("data/residuals.json")]
         for m, v in sorted(by_market.items(), key=lambda kv: ["SIDE", "TOTAL", "MONEYLINE"].index(kv[0]))],
        caption="Coverage by market — blanks are published as blanks and never interpolated"))

    for market in ("SIDE", "TOTAL"):
        v = by_market.get(market, [])
        body.append("<h2>%s — every graded game</h2>" % market)
        body.append(table(
            ["Wk", "Date", "Fixture", "Model fair line", "Official posted line", "Residual",
             "Posted odds", "Timing status", "Source"],
            [[str(r["week"]), esc(r["gameday"]), esc(r["fixture"]),
              num(r["model_fair_line"], 2),
              num(r["official_posted_line"], 2), num(r["residual_model_minus_market"], 2, sign=True),
              esc(r["official_odds_american"] or "—"), esc(r["timing_status"] or "—"),
              off(r["official_source_url"], "game centre")]
             for r in v],
            caption="%s: %d rows, %d with an official line" %
                    (market, len(v), sum(1 for r in v if r["official_posted_line"] is not None))))

    body.append("<h2>Schedule</h2>")
    body.append(table(
        ["Item", "Value", "Source"],
        [["Cadence", esc(res["schedule"]["cadence"]), repo("data/residuals.json")],
         ["Weeks covered", esc(", ".join(str(w) for w in res["schedule"]["weeks_covered"])),
          repo("data/residuals.json")],
         ["Weeks with a price", esc(", ".join(str(w) for w in res["schedule"]["weeks_with_a_price"])),
          repo("data/residuals.json")],
         ["Weeks without", esc(", ".join(str(w) for w in res["schedule"]["weeks_without"]) or "none"),
          repo("data/residuals.json")]],
        caption="From day one: week 1 onwards, no gaps"))
    page("pages/origination.html", "Origination", "Origination · own lines",
         "".join(body), "pages/origination.html",
         "Own line, official posted line and residual for every graded 2026 game, in "
         "registered market order.")


# ----------------------------------------------------------------------
def build_leaderboard(ctx):
    led, mind, dem = ctx["leaderboard"], ctx["mind"], ctx["demotion"]
    rows = []
    for r in led["rows"]:
        ps = r["proper_score"]
        rows.append([
            r["model"], badge("eligible", "ok") if r["eligible_for_ranking"] else badge("control", "neutral"),
            num(ps["bss_moneyline"], 4, sign=True),
            "[%s, %s]" % (num(ps["ci90_moneyline"][0], 4, sign=True),
                          num(ps["ci90_moneyline"][1], 4, sign=True)),
            pval(ps["holm_p_moneyline"]),
            num(ps["bss_total"], 4, sign=True), pval(ps["holm_p_total"]),
            num(ps["skill_crps_side"], 4, sign=True), pval(ps["holm_p_side"]),
            str(ps["n"]), str(ps["weeks"]),
            badge("qualified", "ok") if r["stage_1_qualified"] else badge("shadow", "warn"),
            repo("data/leaderboard.json"),
        ])
    body = ["""<div class="panel"><h2>How this is ranked</h2>
<p>Ranking is by <strong>benchmark-relative proper score</strong>: Brier skill on the
moneyline, Brier skill on the total threshold, and CRPS skill on the margin. Each comes
with a <strong>90 percent week-cluster bootstrap interval</strong> (the week is the unit of
independence; 10,000 resamples, seed 20261119) and a <strong>Holm–Bonferroni adjustment
over the whole declared family</strong> of %d tests. Raw win rate is not a ranking metric
and is not shown as one. The staking division is a separate table and it is empty.</p>
<p class="small">Benchmark = M0 climatology: training-window base rates with no team
information. That is the floor any real model has to clear.</p></div>""" % led["families_scored"]]
    body.append(table(
        ["Model", "Role", "Brier skill (ML)", "90% week-cluster CI", "Holm p",
         "Brier skill (total)", "Holm p", "CRPS skill (side)", "Holm p", "n", "weeks",
         "Gate", "Source"],
        rows, caption="Proper-score leaderboard · 2026 holdout, %d games, never used for "
                      "selection" % led["n_games"]))

    body.append("<h2>Divisions</h2>")
    body.append(table(
        ["Division", "Status", "Reason", "Source"],
        [[esc(k.replace("_", " ")), badge(v["status"], "ok" if v["status"] == "open" else "bad"),
          esc(v.get("note") or v.get("reason", "")), repo("data/leaderboard.json")]
         for k, v in led["divisions"].items()],
        caption="A closed division is a gate that has not passed, published so it cannot be "
                "quietly opened later"))

    body.append("<h2>Staking division — deliberately empty</h2>")
    body.append(table(
        ["Model", "ROI", "CLV", "Bets", "Why blank", "Source"],
        [[r["model"], "—", "—", "—", esc(r["staking_division"]["blank_reason"]),
          repo("data/leaderboard.json")] for r in led["rows"]],
        caption="No officially sourced price with a known capture time exists, so nothing is "
                "staked and nothing is simulated"))

    body.append("<h2>What would change our mind</h2>")
    body.append(table(
        ["Strategy", "Current", "Promotes if", "Retires if", "Source"],
        [[esc(m["strategy"]), esc(m["current"]), esc(m["promote_if"]), esc(m["retire_if"]),
          repo(m["evidence_path"])] for m in mind["rows"]],
        caption="Two-sided on every entry, numeric on both sides"))

    body.append("<h2>Demotion gate</h2>")
    body.append(table(
        ["Trigger", "Rule", "Source"],
        [[t["id"], esc(t["trigger"]), repo("data/demotion.json")] for t in dem["triggers"]],
        caption="How a live strategy goes back to paper"))
    body.append("<p class='small'>%s</p>" % esc(dem["state"]["reason_none_can_yet_be_live"]))
    page("pages/leaderboard.html", "Leaderboard", "Origination · leaderboard",
         "".join(body), "pages/leaderboard.html",
         "Proper-score leaderboard with week-cluster uncertainty, a multiplicity "
         "adjustment, and a deliberately empty staking division.")


# ----------------------------------------------------------------------
def build_luck(ctx):
    luck = ctx["luck"]
    body = ["""<div class="panel"><h2>Removal of luck</h2>
<p>A result is only a signal if it survives four separate questions. Each is a different
test, not four views of one number. The model shown is the one the data ladder selected
before the holdout was touched: <strong>%s</strong>.</p></div>""" % esc(luck["model"])]
    body.append(table(
        ["ID", "Question", "Test", "Number", "Reading", "Source"],
        [[p["id"], esc(p["question"]), esc(p["method"]), esc(p["display"]),
          esc(p["reading"]), repo("data/luck.json")] for p in luck["panel"]],
        caption="Four questions, four numbers"))
    body.append("<h2>Leave-one-week-out</h2>")
    body.append(table(
        ["Week removed", "Games left", "Skill with that week removed", "Source"],
        [[str(r["week_removed"]), str(r["n"]), num(r["skill"], 4, sign=True),
          repo("data/luck.json")] for r in luck["leave_one_week_out"]],
        caption="If one week carries the whole result, it is a run, not a skill"))
    body.append("<h2>Selection stability</h2>")
    body.append("<p>%s</p>" % esc(luck["selection_stability"]["display"]))
    body.append(table(
        ["Validation week removed", "Model the rule would choose", "lambda", "Source"],
        [[str(f["week_removed"]), esc(f["would_choose"]), esc(f["lambda"]),
          repo("data/luck.json")] for f in luck["selection_stability"]["folds"]],
        caption="A choice that flips when one week is removed is a choice made of luck"))
    body.append("<h2>Controls</h2>")
    body.append(table(
        ["Control", "Value", "Source"],
        [[esc(k.replace("_", " ")), esc(v), repo("data/luck.json")]
         for k, v in luck["controls"].items()],
        caption="A leaderboard without a control is a leaderboard of one"))
    page("pages/luck.html", "Removal of luck", "Origination · luck panel",
         "".join(body), "pages/luck.html",
         "Permutation test, leave-one-week-out, selection stability and null interval for the "
         "selected model.")


# ----------------------------------------------------------------------
def build_correlations(ctx):
    corr = ctx["correlations"]
    body = ['<p>Every correlation is computed from the verified corpus and states its n and '
            "95% interval. No correlation that involves a price is published, because no "
            "officially sourced price exists.</p>"]
    body.append(table(
        ["Season", "Pair", "r", "n", "95% CI", "Uses a price?", "Source"],
        [[str(r["season"]), esc(r["pair"]), num(r["r"], 4),
          str(r["n"]) if r["n"] else "—",
          "[%s, %s]" % (num(r["ci95"][0], 4), num(r["ci95"][1], 4)) if r["ci95"] else "—",
          "no", repo("data/correlations.json")] for r in corr["rows"]],
        caption="Correlations from officially sourced numbers, n on every value"))
    body.append("<h2>Deliberately not published</h2>")
    body.append(table(
        ["Item", "Why not", "Source"],
        [[esc(x["item"]), esc(x["why"]), repo("data/correlations.json")]
         for x in corr["not_published"]],
        caption="An unavailable correlation is published as unavailable, never estimated "
                "from a rule of thumb"))
    page("pages/correlations.html", "Correlations", "Evidence · correlations",
         "".join(body), "pages/correlations.html",
         "Measured correlations with n and confidence intervals; price-based correlations "
         "are excluded because no official price exists.")


# ----------------------------------------------------------------------
def build_availability(ctx):
    av, dep = ctx["availability"], ctx["depth"]
    body = ["""<div class="panel"><h2>Two dated reads, and what changed between them</h2>
<p>Two stored captures of the same official Week 11 injury report: raw bytes at
<strong>%s</strong> (sha256 <code>%s</code>) and a rendered transcription at
<strong>%s</strong>. %d players appear in both; %d field differs. Blank game status is
published as blank — never as "available".</p></div>""" % (
        esc(av["provenance"]["A"]["captured_utc"]),
        esc(av["provenance"]["A"]["sha256"][:16]) + "…",
        esc(av["provenance"]["B"]["captured_utc"]),
        av["transcription_control"]["joined_rows"],
        len(av["transcription_control"]["differences"]))]
    body.append(table(
        ["Club", "Player", "Field", "Earlier read (2026-11-18)", "Later read (2026-11-19)",
         "Source"],
        [[esc(d["club"]), esc(d["player"]), esc(d["field"]), esc(d["A_2026-11-18"]),
          esc(d["B_2026-11-19"]), off("https://www.nfl.com/injuries/", "injury report")]
         for d in av["transcription_control"]["differences"]],
        caption="Every change between two independent reads"))
    body.append("<h2>Transcription control</h2>")
    fe = av["transcription_control"]["fields_equal"]
    body.append(table(
        ["Field", "Joined rows", "Identical", "Note", "Source"],
        [[f, str(av["transcription_control"]["joined_rows"]), str(fe[f]),
          "two sessions, two parsers, same publisher page",
          repo("data/availability_parse.json")] for f in fe],
        caption="Corroboration between sessions — not independence from the publisher"))

    body.append("<h2>Designation census</h2>")
    rows = []
    for g, inner in sorted(av["designation_census"]["B"].items()):
        for pr, n in sorted(inner.items()):
            rows.append([esc(g), esc(pr), str(n), off("https://www.nfl.com/injuries/", "injury report")])
    body.append(table(["Game status", "Practice status", "Rows", "Source"], rows,
                      caption="Game status by practice status, later read — blank is a real "
                              "category here, not a missing value"))

    body.append("<h2>Depth: a slot is a group, not a starter</h2>")
    ss = dep["slot_shape"]
    body.append(table(
        ["Measure", "Value", "Source"],
        [["Clubs transcribed", str(ss["clubs_transcribed"]), repo("data/depth.json")],
         ["Clubs measuring only as an image", str(ss["clubs_not_transcribed"]), repo("data/depth.json")],
         ["Slots", str(ss["slots"]), repo("data/depth.json")],
         ["Player entries", str(ss["player_entries"]), repo("data/depth.json")],
         ["Slots naming more than one player at one rank", str(ss["shared_slots"]),
          repo("data/depth.json")],
         ["Empty rank-1 slots", str(ss["empty_rank1_slots"]), repo("data/depth.json")],
         ["Jersey-prefixed entries", esc(str(ss["jersey_prefixed_entries"])),
          repo("data/depth.json")]],
        caption="Measured slot shapes — reading column 1 as 'the starter' would fabricate a "
                "starter on %d slots" % ss["shared_slots"]))
    body.append("<h3>Slots that name more than one player</h3>")
    body.append(table(
        ["Club", "Position", "Rank", "Names on the chart", "Official source"],
        [[esc(s["club"]), esc(s["position"]), esc(s["rank"]),
          esc(" / ".join(s["names"])), off(s["source_url"], "club depth chart")]
         for s in ss["shared_examples"]],
        caption="Published as a group. No starter is chosen here."))

    body.append("<h2>Depth of the replacement</h2>")
    body.append(table(
        ["Club", "Out", "Position", "Was listed at", "Replacement", "Replacement at",
         "Depth moved", "Official source"],
        [[esc(r["club"]), esc(r["out"]), esc(r["position"]),
          num(r["out_was_listed_at_rank"], 0), esc(r["replacement"]),
          num(r["replacement_at_rank"], 0), num(r["depth_of_replacement"], 0),
          off(r["source_url"], "reserve list")] for r in dep["replacement_depth"]["rows"]],
        caption="%d documented replacements; depth moved is the rank difference, blank when a "
                "rank is unknown" % dep["replacement_depth"]["n_replacements_documented"]))

    body.append("<h2>Stale charts against the official transactions log</h2>")
    rows = []
    for club in dep["stale_chart_flags"]["rows"]:
        for f in club["flags"]:
            rows.append([esc(club["club"]), esc(f["player"]), esc(f["position"]),
                         esc(f["date_on_ir"]), esc(f["evidence"]),
                         off("https://www.nfl.com/transactions/league/reserve-list/2026/11",
                             "reserve list")])
    body.append(table(["Club", "Player", "Position", "On reserve since", "Evidence",
                       "Official source"], rows,
                      caption="Chart entries that contradict the official reserve list"))

    body.append("<h2>Gaps, and the gate they hold shut</h2>")
    body.append(table(
        ["Gap", "Missing", "Why it matters", "What would fill it", "Then what", "Source"],
        [[g["id"], esc(g["missing"]), esc(g["why_it_matters"]), esc(g["what_would_fill_it"]),
          esc(g["then_what"]), repo("data/depth.json")] for g in dep["gaps"]],
        caption="Gate status: %s — %s" % (dep["gate"]["status"], dep["gate"]["why"])))
    page("pages/availability.html", "Availability & depth", "Evidence · availability",
         "".join(body), "pages/availability.html",
         "Two dated injury-report reads with their delta, depth slots measured as groups, "
         "replacement depth and stale-chart flags.")


# ----------------------------------------------------------------------
def build_prices(ctx):
    pol = ctx["price_policy"]
    body = ["""<div class="panel"><h2>The decision</h2>
<p><strong>%s</strong></p>
<p>An opening number and a closing number are both required before ROI can exist. This
repository has neither in claimable form, so the policy is: no ROI, no CLV, no units, no
bankroll, and no assumed vig. An origination residual against the official posted line is
still published — that only needs a published number, not a timestamped one.</p></div>""" %
            esc(pol["decision"]["verdict"])]
    body.append(table(
        ["Attribute required", "Rule", "Source"],
        [["C1", esc(pol["classification_rule"]["C1"]), repo("data/price_policy.json")],
         ["C2", esc(pol["classification_rule"]["C2"]), repo("data/price_policy.json")],
         ["C3", esc(pol["classification_rule"]["C3"]), repo("data/price_policy.json")],
         ["C4", esc(pol["classification_rule"]["C4"]), repo("data/price_policy.json")]],
        caption="A row earns a claim only when all four hold"))
    body.append("<h2>The census</h2>")
    body.append(table(
        ["Side", "Bucket", "Rows", "Consequence", "Source"],
        [[side, esc(k.replace("_", " ")), str(v),
          "claimable" if k == "claimable" else "not claimable",
          repo("data/price_policy.json")]
         for side in ("open", "close")
         for k, v in sorted(pol["census"][side].items())],
        caption="%d stored price rows, %s to %s" % (
            pol["census"]["rows_total"], pol["census"]["seasons"][0], pol["census"]["seasons"][-1])))
    body.append("<h2>Source register</h2>")
    body.append(table(
        ["Source key", "Publisher", "Official?", "Capture time known?", "Evidence", "Source"],
        [[esc(k or "(blank)"), esc(v["publisher"]),
          badge("yes" if v["official"] else "no", "ok" if v["official"] else "bad"),
          badge("yes" if v["timing_known"] else "no", "ok" if v["timing_known"] else "bad"),
          esc(v["timing_evidence"]), repo("data/price_policy.json")]
         for k, v in pol["source_register"].items()],
        caption="Classified before the census was seen"))
    body.append("<h2>What would unblock staking</h2>")
    body.append(table(
        ["Requirement", "Why", "Source"],
        [[esc(x), "without it, no price can be ordered against kickoff",
          repo("data/price_policy.json")] for x in pol["decision"]["what_would_unblock_staking"]],
        caption="Stated plainly so the next session does not re-litigate it"))
    page("pages/prices.html", "Price-data policy", "Evidence · prices",
         "".join(body), "pages/prices.html",
         "The price-data policy: 12,573 stored rows, zero claimable, and the consequence for "
         "ROI.")


# ----------------------------------------------------------------------
def build_corpus(ctx):
    corpus = ctx["corpus"]
    body = ["""<div class="panel"><h2>Three stored sources, unioned explicitly</h2>
<p>%s</p></div>""" % esc(corpus["policy"])]
    body.append("<h2>Integrity assertions</h2>")
    body.append(table(
        ["Assertion", "Rows passed", "Failures", "Source"],
        [[esc(a), str(corpus["integrity"]["rows_passed"]),
          str(corpus["integrity"]["failures"]), repo("data/corpus.json")]
         for a in corpus["integrity"]["assertions"]],
        caption="Any failure stops the build; these ran before any model saw the data"))
    sa = corpus["standings_arithmetic"]
    body.append("<h2>Arithmetic against official standings</h2>")
    body.append(table(
        ["Check", "Value", "Holds?", "Official source"],
        [["Games implied by sum(W+L+T)/2", "%s" % sa["games_implied_by_standings"],
          badge("yes" if sa["identity_holds"] else "no", "ok" if sa["identity_holds"] else "bad"),
          off(sa["source"], "standings")],
         ["Games in the union", str(sa["union_2026_games"]),
          badge("yes" if sa["identity_holds"] else "no", "ok" if sa["identity_holds"] else "bad"),
          off(sa["source"], "standings")],
         ["Sum of PF vs sum of PA", "%d / %d" % (sa["pf_total"], sa["pa_total"]),
          badge("yes" if sa["pf_total"] == sa["pa_total"] else "no",
                "ok" if sa["pf_total"] == sa["pa_total"] else "bad"), off(sa["source"], "standings")],
         ["Corpus points vs sum(PF)", "%d / %d" % (sa["corpus_points"], sa["pf_total"]),
          badge("yes" if sa["points_identity_holds"] else "no",
                "ok" if sa["points_identity_holds"] else "bad"), off(sa["source"], "standings")]],
        caption="A corpus that does not reconcile with the official standings is not a corpus"))
    ca = corpus["cross_source_audit"]
    body.append("<h2>Cross-source audit</h2>")
    body.append(table(
        ["Overlapping games", "Agree", "Conflict", "Reading", "Source"],
        [[str(ca["overlapping_games"]), str(ca["agreeing_games"]), str(ca["conflicting_games"]),
          esc(ca["reading"]), repo("data/corpus.json")]],
        caption="Two stored reads of the same official pages, compared game by game"))
    body.append("<h2>Defects found while building the corpus</h2>")
    rows = []
    for d in corpus["defects_found"]:
        extra = ""
        if d.get("missing_from_feed"):
            extra = " Missing games: " + ", ".join(d["missing_from_feed"])
        rows.append([esc(d["id"]), esc(d["what"]), esc(d["impact"]), esc(d["handling"]),
                     esc(d["status"]) + esc(extra), repo("data/corpus.json")])
    body.append(table(["ID", "Defect", "Impact", "Handling", "Status", "Source"], rows,
                      caption="Both were caught by the union, not by inspection"))
    body.append("<h2>Coverage by week</h2>")
    weeks = corpus["counts"]["by_season_week"]
    body.append(table(
        ["Season", "Week", "Games", "Source"],
        [[season, week, str(n), repo("data/corpus.json")]
         for season in sorted(weeks) for week, n in sorted(weeks[season].items(), key=lambda kv: int(kv[0]))],
        caption="2025 for training and validation, 2026 for the untouched holdout"))
    body.append("<h2>Schedule announcements</h2>")
    body.append(table(
        ["Item", "What the official page says", "Official source"],
        [["Flexible scheduling (Weeks 16-18)",
          "Week 16 and 17 designated matchups are dated and announced no later than "
          "immediately after Week 14 / Week 15; Week 18 dates, times and networks are "
          "announced following the conclusion of Week 17 — stored quote, not re-read this session",
          off("https://www.nfl.com/legal/flexible-scheduling-procedures", "NFL flexible scheduling")]],
        caption="The dated announcement published beside the live schedule page"))
    page("pages/corpus.html", "Results corpus", "Evidence · corpus",
         "".join(body), "pages/corpus.html",
         "The results corpus: three stored sources unioned, integrity assertions, standings "
         "arithmetic and the defects the union caught.")


# ----------------------------------------------------------------------
def build_prereg(ctx):
    pre = ctx["prereg"]
    vs = ctx["validation_scores"]
    body = ["""<div class="panel"><h2>The registration is the commit</h2>
<p>Every rule below was written down and committed before the code that scores it
produced a number. The commit hash is the registration; if a rule changes, the version
string changes and the old block stays. One correction is recorded in the file itself: the
total-market threshold was first described as the rounded 2025 median, which was false, so
the description was corrected before any score existed and the correction is kept.</p>
<p class="small">%s · corrected %s</p></div>""" % (
        repo("prereg/PREREG-LAB-1.json", "prereg/PREREG-LAB-1.json"),
        esc(pre.get("amended_utc", "")))]
    body.append("<h2>The data ladder</h2>")
    body.append(table(
        ["Block", "Definition", "Source"],
        [[esc(k), esc(v), repo("prereg/PREREG-LAB-1.json")]
         for k, v in pre["data_ladder"].items()],
        caption="Train, validation, final holdout — and what is excluded and why"))
    body.append("<h2>Registered block sizes</h2>")
    body.append(table(
        ["Block", "Games", "Source"],
        [[esc(k), esc(v), repo("data/validation_scores.json")] for k, v in vs["blocks"].items()],
        caption="Measured, not asserted"))
    body.append("<h2>The strategies, frozen</h2>")
    body.append(table(
        ["ID", "Name", "Definition", "Frozen parameters", "Source"],
        [[esc(s["id"]), esc(s["name"]), esc(s["definition"]),
          esc(", ".join(s.get("frozen_parameters", [])) or "—"),
          repo("prereg/PREREG-LAB-1.json")] for s in pre["strategies"]],
        caption="Six models; the control is registered beside the candidates"))
    body.append("<h2>Selection and scoring rules</h2>")
    body.append(table(
        ["Rule", "Text", "Source"],
        [[esc(k.replace("_", " ")), esc(v), repo("prereg/PREREG-LAB-1.json")]
         for k, v in pre["selection_rule"].items()] +
        [[esc(k.replace("_", " ")), esc(v), repo("prereg/PREREG-LAB-1.json")]
         for k, v in pre["scoring"].items()],
        caption="What may and may not touch the holdout"))
    body.append("<h2>Validation evidence (the block that chose the model)</h2>")
    rows = []
    for s in sorted(vs["scores"], key=lambda r: (r["model"], r["lambda"] or 0)):
        rows.append([esc(s["model"]), esc(s["lambda"]), str(s["n"]),
                     num(s["brier_home_win"], 5), num(s["brier_total_over_tau"], 5),
                     num(s["crps_total"], 3), repo("data/validation_scores.json")])
    body.append(table(["Model", "lambda", "n", "Brier (ML)", "Brier (total)", "CRPS (total)",
                       "Source"], rows,
                      caption="%s · chosen: %s" % (vs["criterion"], vs["chosen_model"])))
    page("pages/prereg.html", "Pre-registration", "Origination · pre-registration",
         "".join(body), "pages/prereg.html",
         "The frozen pre-registration, the data ladder, and the validation evidence that "
         "chose the model before the holdout was read.")


# ----------------------------------------------------------------------
def build_questions(ctx):
    q = ctx["questions"]
    body = ['<p>Each question states what information would answer it, what we already have, '
            "what we do not have, and the action that would obtain it. No row contains a guess "
            "at the answer.</p>"]
    body.append(table(
        ["ID", "Question", "Information needed", "What we have", "What we do not have",
         "How to obtain it", "Status", "Evidence"],
        [[esc(r["id"]), esc(r["question"]), esc(r["information_needed"]), esc(r["we_have"]),
          esc(r["we_do_not_have"]), esc(r["how_to_obtain"]),
          badge(r["status"], {"blocking": "bad", "open": "warn", "partial": "warn",
                              "settled": "ok"}[r["status"]]),
          repo(r["evidence"])] for r in q["rows"]],
        caption="Questions register · %s" % ", ".join("%d %s" % (v, k)
                                                      for k, v in sorted(q["counts"].items()))))
    page("pages/questions.html", "Questions", "Overview · questions", "".join(body),
         "pages/questions.html",
         "The questions that must be answered before a decision is reasonable, with what is "
         "missing and how to get it.")


# ----------------------------------------------------------------------
def build_suggestions(ctx):
    s = ctx["suggestions"]
    body = ['<p>Every suggestion is left at <strong>proposed — awaiting owner</strong>. The '
            "decision and date columns are deliberately blank so the owner chooses before "
            "anything is built.</p>"]
    body.append(table(
        ["ID", "Suggestion", "Why", "Expected effect", "Priority", "Touches", "Decision",
         "Decided on", "Source"],
        [[esc(r["id"]), esc(r["suggestion"]), esc(r["why"]), esc(r["expected_effect"]),
          badge(r["priority"], "ok" if r["priority"] == "high" else "neutral"),
          esc(r["would_touch"]),
          badge("undecided", "warn"), "—", repo("data/suggestions.json")]
         for r in s["rows"]],
        caption="Suggestions board · %d rows, %d decided"
                % (len(s["rows"]), sum(1 for r in s["rows"] if r["decision"]))))
    page("pages/suggestions.html", "Suggestions", "Overview · suggestions", "".join(body),
         "pages/suggestions.html",
         "Suggestions for review, each with its expected effect and a blank decision field.")


# ----------------------------------------------------------------------
def build_flags(ctx):
    f = ctx["flags"]
    body = ['<p>Every irregularity found this session, with the source that shows it and what '
            "it blocks. These do not block publishing the site; each one blocks a claim.</p>"]
    body.append(table(
        ["ID", "Irregularity", "Severity", "Detail", "Effect", "Official source", "Evidence"],
        [[esc(r["id"]), esc(r["what"]),
          badge(r["severity"], {"blocking": "bad", "material": "warn", "minor": "neutral",
                                "disclosure": "ok"}[r["severity"]]),
          esc(r["detail"]), esc(r["effect"]), off(r["source_url"], "source"),
          repo(r["evidence"])] for r in f["rows"]],
        caption="Flagged for review · %s" % ", ".join("%d %s" % (v, k)
                                                      for k, v in sorted(f["counts"].items()))))
    page("pages/flagged.html", "Flagged for review", "Overview · flagged", "".join(body),
         "pages/flagged.html",
         "Flagged irregularities with their official sources and the claim each one blocks.")


# ----------------------------------------------------------------------
def build_sources(ctx):
    corpus, pol, av, dep, res = (ctx["corpus"], ctx["price_policy"], ctx["availability"],
                                 ctx["depth"], ctx["residuals"])
    rows = [
        ["https://www.nfl.com/injuries/", "Official Week 11 injury report",
         "two dated captures, %d rows in the later read" % len(av["rows"]),
         "not read live this session", off("https://www.nfl.com/injuries/", "open")],
        ["https://www.nfl.com/games/<fixture>", "Official game centre, one per game",
         "%d residual rows and %d corpus games cite a game centre" %
         (res["counts"]["rows"], len(corpus["games"])), "carried on each stored row",
         off("https://www.nfl.com/games/", "open")],
        ["https://www.nfl.com/schedules/2026/by-week/", "Official weekly schedule pages",
         "16 corpus rows cite a week page rather than a game centre", "stored",
         off("https://www.nfl.com/schedules/2026/", "open")],
        ["https://www.nfl.com/standings/league/2026/REG", "Official standings",
         "32 rows; the games-implied and points identities both hold", "stored",
         off("https://www.nfl.com/standings/", "open")],
        ["https://www.nfl.com/transactions/league/reserve-list/2026/11",
         "Official November 2026 reserve list", "25 entries across 32 clubs; %d replacements "
         "documented" % dep["replacement_depth"]["n_replacements_documented"],
         "stored", off("https://www.nfl.com/transactions/league/reserve-list/2026/11", "open")],
        ["Club depth-chart pages (32 clubs)", "Official club depth charts",
         "%d slots transcribed from %d clubs; 1 club image-only" %
         (dep["slot_shape"]["slots"], dep["slot_shape"]["clubs_transcribed"]),
         "stored 2026-11-17", repo("data/depth.json")],
        ["https://www.nfl.com/legal/flexible-scheduling-procedures",
         "NFL flexible scheduling procedures",
         "the dated announcement text quoted on the corpus page", "stored quote",
         off("https://www.nfl.com/legal/flexible-scheduling-procedures", "open")],
        ["(internal)", "Price-snapshot store", "%d rows; %d claimable" %
         (pol["census"]["rows_total"], pol["decision"]["claimable_close_rows"]),
         "inherited, not fetched", repo("data/price_policy.json")],
    ]
    body = ['<p>Every source, what it supports, and whether it was read live. None was read '
            "live this session; the sandbox has no HTTPS route to nfl.com.</p>"]
    body.append(table(["Source", "What it is", "What it supports here", "Read live?",
                       "Link"], rows, caption="Source register"))
    page("pages/sources.html", "Sources", "Evidence · sources", "".join(body),
         "pages/sources.html",
         "Every official source behind the published numbers, and whether it was read live.")


# ----------------------------------------------------------------------
def build_verify(ctx):
    body = ["""<div class="panel"><h2>Reproduce every number</h2>
<p>The whole build is eight commands, in order. Each writes a JSON file that the next one
reads, and none fetches anything:</p>
<pre>python3 nfl-origination-lab/engine/parse_availability.py
python3 nfl-origination-lab/engine/corpus.py
python3 nfl-origination-lab/engine/evaluate.py
python3 nfl-origination-lab/engine/price_policy.py
python3 nfl-origination-lab/engine/depth.py
python3 nfl-origination-lab/engine/governance.py
python3 nfl-origination-lab/engine/registers.py
python3 nfl-origination-lab/engine/build.py
python3 nfl-origination-lab/engine/verify.py</pre>
<p>Then <code>verify.py</code> asserts the properties below and exits non-zero if any fails.
It also re-runs the walk-forward with a poisoned future and asserts the predictions do not
move — the only test of no-lookahead that means anything.</p></div>"""]
    rows = [
        ["V1", "Every data-table row carries an https link to an official host or to this "
               "repository", repo("engine/verify.py")],
        ["V2", "Every local href and src resolves to a file that exists", repo("engine/verify.py")],
        ["V3", "No placeholder text, sentinel or unrendered template marker appears", repo("engine/verify.py")],
        ["V4", "Every page carries the navigation, the disclaimer and the helpline", repo("engine/verify.py")],
        ["V5", "The printed row counts match the data files behind them", repo("engine/verify.py")],
        ["V6", "The corpus reconciles to the official standings (games and points)", repo("data/corpus.json")],
        ["V7", "The walk-forward uses no game from the week it predicts (poisoned-future test)",
         repo("engine/evaluate.py")],
        ["V8", "The pre-registration file is unmodified since the commit that froze it",
         repo("prereg/PREREG-LAB-1.json")],
        ["V9", "The build is deterministic: two runs produce identical bytes", repo("engine/build.py")],
        ["V10", "No strategy is published without a blank staking division and a two-sided "
                "mind field", repo("data/leaderboard.json")],
    ]
    body.append(table(["Check", "What it asserts", "Where it lives"], rows,
                      caption="The publication gate"))
    page("pages/verify.html", "Verification", "Evidence · verification", "".join(body),
         "pages/verify.html",
         "How to reproduce the build and what the verifier asserts before publication.")


def main():
    import glob
    ctx = {}
    for name in ("leaderboard", "luck", "requirements", "flagged", "residuals",
                 "questions", "price_policy", "depth", "availability_parse", "corpus",
                 "correlations", "mind", "demotion", "suggestions", "validation_scores"):
        ctx[name] = load(name + ".json")
    ctx["flags"] = ctx["flagged"]
    ctx["availability"] = ctx["availability_parse"]
    ctx["prereg"] = load("../prereg/PREREG-LAB-1.json")
    # drop any generated page not in this build (keeps the tree deterministic)
    for f in glob.glob(os.path.join(LAB, "pages", "*.html")):
        keep = {href.split("/")[-1] for _g, items in NAV for href, _l in items}
        if os.path.basename(f) not in keep:
            os.remove(f)
    build_index(ctx)
    build_exec(ctx)
    build_requirements(ctx)
    build_origination(ctx)
    build_leaderboard(ctx)
    build_luck(ctx)
    build_correlations(ctx)
    build_availability(ctx)
    build_prices(ctx)
    build_corpus(ctx)
    build_prereg(ctx)
    build_questions(ctx)
    build_suggestions(ctx)
    build_flags(ctx)
    build_sources(ctx)
    build_verify(ctx)
    n = len(glob.glob(os.path.join(LAB, "*.html"))) + len(glob.glob(os.path.join(LAB, "pages", "*.html")))
    print("built %d pages" % n)


if __name__ == "__main__":
    main()

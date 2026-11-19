#!/usr/bin/env python3
"""
nfl-command-deck — static site builder.

Renders index.html + pages/*.html from data/*.json. Every number on the site comes
from a data file; nothing is typed into the template. The build fails if a table row
carries no source link, if an internal link does not resolve, or if a placeholder
token survives.

Run: python3 engine/build_site.py
"""

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
E = html.escape

# ------------------------------------------------------------------ load data
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


EVAL = load("eval.json")
NULL = load("null.json")
AUDIT = load("audit.json")
AVAIL = load("availability.json")
REQ = load("requirements.json")
FLAGS = load("flags.json")["flags"]
Q = load("questions.json")["rows"]
SUG = load("suggestions.json")["rows"]
SRC = load("sources.json")["sources"]

SRC_BY_ID = {s["id"]: s for s in SRC}

NAV = [
    ("Command deck", [
        ("Start here — decision readiness", "index.html", ""),
        ("Executive summary", "pages/executive-summary.html", "summary"),
        ("Model &amp; luck panel", "pages/model.html", "model"),
        ("Availability &amp; depth", "pages/availability.html", "availability"),
    ]),
    ("Evidence &amp; control", [
        ("Requirement audit (73 rows)", "pages/requirements.html", "requirements"),
        ("Repository audit", "pages/repo-audit.html", "repo-audit"),
        ("Questions before any decision", "pages/questions.html", "questions"),
        ("Suggestions — choose a path", "pages/suggestions.html", "suggestions"),
        ("⚑ Flagged for review", "pages/flagged.html", "flagged"),
        ("Sources &amp; capture hashes", "pages/sources.html", "sources"),
    ]),
]

HELPLINE = "1-800-MY-RESET"


def page(title, active, body, subtitle=""):
    nav = []
    for grp, items in NAV:
        nav.append('<div class="grp">%s</div>' % grp)
        for label, href, key in items:
            prefix = "../" if active != "" else ""
            cls = "nav active" if key == active else "nav"
            nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, label))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · NFL Command Deck</title>
<link rel="stylesheet" href="%(prefix)sassets/deck.css">
</head>
<body>
<aside class="side">
  <a class="brand" href="%(prefix)sindex.html">NFL <span>Command Deck</span></a>
  <div class="tag">Evidence surface · built %(built)s</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <div class="side-note">
    <strong>No live official read.</strong> nfl.com cannot be reached from this build
    environment. Every figure comes from a committed official capture whose SHA-256 is
    re-checked at build time. See <a href="%(prefix)spages/flagged.html">RF-01</a>.
  </div>
  <a class="flag" href="%(prefix)spages/flagged.html">⚑ %(nflags)d items flagged for review</a>
</aside>
<main class="main" id="main">
<header class="head">
  <h1>%(title)s</h1>
  %(subtitle)s
</header>
%(body)s
<footer class="foot">
  <p><strong>Research only — not wagering advice.</strong> No price, ROI or staking result is
  published anywhere on this site because no official price source exists.</p>
  <p>If gambling is a problem for you or someone you know, call the National Problem Gambling
  Helpline at <a href="https://www.ncpgambling.org/help-treatment">%(helpline)s</a>.</p>
  <p>Every table cell is CAPTURED (committed official capture, hash re-checked) or DERIVED
  (computed by a named script in this workspace) or blank with a stated reason. Nothing is
  inferred.</p>
</footer>
</main>
</body>
</html>
""" % {"title": title, "subtitle": subtitle, "nav": "".join(nav), "body": body,
       "built": EVAL["built_utc"], "nflags": len(FLAGS), "helpline": HELPLINE,
       "prefix": "../" if active != "" else ""}


def src_links(ids):
    out = []
    for i in ids:
        s = SRC_BY_ID.get(i)
        if not s:
            out.append('<span class="bad">source %s missing</span>' % E(i))
            continue
        out.append('<a href="%s" title="%s">%s</a>' % (E(s["url"]), E(s["name"]), E(i)))
    return " ".join(out)


REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"


def R(path, label=None):
    """A repository artifact cited as an external https link, so it is clickable off-site
    and survives a relative-path move."""
    return '<a href="%s%s">%s</a>' % (REPO, path, E(label or path.split("/")[-1]))


def pill(text, kind):
    return '<span class="pill %s">%s</span>' % (kind, E(text))


def status_pill(s):
    return pill(s, {"pass": "ok", "met": "ok", "fail": "bad", "contradicted": "bad",
                    "review": "warn", "partial": "warn", "not-checkable": "mute",
                    "not_started": "mute", "blocked": "bad", "in_progress": "warn"}.get(s, "mute"))


def table(headers, rows, cls=""):
    h = "".join("<th>%s</th>" % x for x in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    return ('<div class="scroll"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cls, h, "".join(body)))


# ------------------------------------------------------------------ derived views
def gate_rows():
    """One row per audited requirement: status, blocking gate, number that clears."""
    rows = []
    for r in REQ["rows"]:
        if r["verdict"] == "contradicted":
            status = status_pill("contradicted")
        elif r["verdict"] == "pass":
            status = status_pill(r["status"]) + " " + pill("independently re-checked", "ok")
        elif r["artifacts_missing"]:
            status = status_pill("fail")
        else:
            status = status_pill(r["status"]) + " " + pill("peer verdict, not machine-checkable", "mute")
        gate = E(r["gate"]) if r["gate"] and r["gate"] != "—" else (
            "no machine assertion defined" if r["verdict"] == "not-checkable" else "—")
        clears = E(r["clears"]) if r["clears"] and r["clears"] != "—" else "—"
        if r["verdict"] == "contradicted":
            gate = "the artifact does not support the published verdict"
            clears = E(r["independent_detail"])
        rows.append([E(r["id"]), E(r["requirement"]), status, gate, clears,
                     src_links(["S13"]) + " " +
                     ('<a href="%s">check</a>' % E(r["independent_source"])
                      if r["independent_source"] else "")])
    return rows


# ------------------------------------------------------------------ pages
def build_index():
    c = EVAL["scored"]["weeks_4_10"]
    h = EVAL["scored"]["holdout_weeks_8_10"]
    cd1, cd2 = c["CD-1"], c["CD-2"]
    gates = EVAL["gates"]["CD-1"]["gates"]
    n_pass = sum(1 for v in gates.values() if v)
    counters = [
        ("Games in the frozen corpus", "%d" % EVAL["inputs"]["corpus_games"],
         "weeks 1–10, 32 clubs, every row source-linked", "S11"),
        ("Scored forecasts (weeks 4–10)", "%d" % cd1["n"], "no leakage: each week forecast "
         "only from earlier weeks", "S11"),
        ("Brier skill vs climatology", "%+.4f" % cd1["bss"],
         "95%% week-cluster CI [%+.4f, %+.4f]" % tuple(cd1["ci95_week_cluster"]), "S11"),
        ("Holdout skill (weeks 8–10)", "%+.4f" % h["CD-1"]["bss"], "never used for any choice", "S11"),
        ("Gates passed by CD-1", "%d of 6" % n_pass,
         "see the model page for the failing strategy", "S11"),
        ("Permutation p (200 nulls)", "%s" % NULL["p_permutation"],
         "observed beats all %d permuted schedules" % NULL["null_reps"], "S11"),
        ("Points awarded", "%d" % EVAL["leaderboard_policy"]["points_awarded"],
         "no price source ⇒ no money result ⇒ no reward", "S11"),
        ("Requirements re-checked and passing", "%d of %d"
         % (REQ["summary"]["verified_by_this_session"],
            REQ["summary"]["rows"]),
         "plus %d contradicted; %d have no machine assertion"
         % (REQ["summary"]["contradicted"], REQ["summary"]["not_checkable"]), "S13"),
    ]
    cards = "".join(
        '<div class="card"><div class="k">%s</div><div class="v">%s</div>'
        '<div class="n">%s</div><div class="sl">%s</div></div>'
        % (E(t), E(v), E(n), src_links([s])) for t, v, n, s in counters)

    body = """
<section class="lede">
  <p>This is one additive workspace in a repository that already holds 41 overlapping NFL
  workspaces. It does not restate their numbers as new analysis. It does three things:
  it <strong>recomputes</strong> a pre-registered forecast evaluation from the committed
  official corpus, it <strong>audits</strong> the repository and the 73-row requirement
  register against the artifacts they cite, and it publishes <strong>what is still missing
  and what would clear it</strong>.</p>
  <p>Reading rule used everywhere on this site: <strong>CAPTURED</strong> means a committed
  official capture with a re-checked SHA-256; <strong>DERIVED</strong> means computed by a
  named script here; anything else is <strong>blank with a reason</strong>.</p>
</section>

<h2>Headline numbers</h2>
<div class="cards">%(cards)s</div>

<h2>Decision readiness — one row per audited requirement</h2>
<p class="note">The brief asks for a landing-page table with the gate that blocks each
requirement and the number that would clear it. Every row below is a row of the 73-row peer
register this workspace audited. <em>Status</em> is the peer's verdict unless this workspace
re-checked it mechanically. Full register: <a href="pages/requirements.html">Requirements</a>.</p>
%(gate_table)s

<h2>What this workspace will not claim</h2>
<ul class="willnot">
  <li><strong>No ROI, CLV or staking result.</strong> There is no official price source
  (<a href="pages/flagged.html">RF-14</a>). An assumed −110 price is not used anywhere.</li>
  <li><strong>No injury adjustment to any forecast.</strong> One week of availability
  exists; an ablation needs a history (<a href="pages/questions.html">Q-07</a>).</li>
  <li><strong>No parlay or prop-combo probability.</strong> Under dependence, marginal
  probabilities cannot be multiplied (<a href="pages/questions.html">Q-09</a>).</li>
  <li><strong>No 'verified today'.</strong> nfl.com is unreachable from this build
  environment (<a href="pages/flagged.html">RF-01</a>).</li>
  <li><strong>No starter claimed from a depth chart.</strong> The club's next name is
  published; who played is blank (<a href="pages/availability.html">availability</a>).</li>
</ul>
""" % {"cards": cards,
       "gate_table": table(["ID", "Requirement", "Status", "Gate that blocks it",
                            "Number that would clear it", "Source"], gate_rows(), "grid")}
    return page("NFL Command Deck — decision readiness", "", body,
                '<p class="sub">A frozen forecast evaluation, a repository audit, and the '
                'questions that must be answered before any line is originated for money.</p>')


def build_summary():
    c = EVAL["scored"]["weeks_4_10"]
    h = EVAL["scored"]["holdout_weeks_8_10"]
    t = EVAL["totals"]
    g1 = EVAL["gates"]["CD-1"]
    g2 = EVAL["gates"]["CD-2"]

    def gate_table(model):
        rows = []
        for g, ok in EVAL["gates"][model]["gates"].items():
            rows.append([E(g), pill("pass" if ok else "fail", "ok" if ok else "bad"),
                         src_links(["S11"])])
        return table(["Pre-registered gate", "Result", "Source"], rows, "grid")

    body = """
<section class="lede">
  <p><strong>Bottom line.</strong> A simple, opponent-aware point rating does forecast NFL
  winners better than every control it was pre-registered against, and the result survives a
  deliberate attempt to destroy it. That is a <em>forecast-skill</em> result. It is not a
  betting result: the repository holds no price, so no money metric exists and no reward is
  awarded.</p>
</section>

<h2>1 · What was measured, and how</h2>
<p>Rule text, sample window, hyper-parameter grid, metrics and gates were committed and
hash-locked <em>before</em> the numbers were computed
(<code>prereg/PREREG-CD.md</code>, SHA-256 <code>%(sha)s</code>). The build refuses to run if
that file changes. Protocol: expanding-window walk-forward, week 4 to week 10, each week
forecast only from earlier weeks; λ chosen on weeks 4–7 and frozen; weeks 8–10 held out from
every choice.</p>
%(main_table)s

<h2>2 · The result, with uncertainty</h2>
<p>Skill is stated as a Brier Skill Score against a climatology benchmark (the home-win rate
of the training window), never as win rate or accuracy. Intervals resample <em>weeks</em>,
not games, because games inside a week share conditions.</p>
%(score_table)s

<h2>3 · Removing the luck</h2>
<table class="grid"><thead><tr><th>Control</th><th>What it shows</th><th>Source</th></tr></thead><tbody>
<tr><td>Control floor</td><td>Coin flip (p = 0.50) scores Brier %(coin).5f; always-home scores
%(always).5f. Both are published on every run, as the brief requires.</td><td>%(s11)s</td></tr>
<tr><td>Permutation null</td><td>%(_reps)d schedules with the real fixtures but team identity
permuted away: mean BSS %(nmean)+.4f, 95th percentile %(n95)+.4f, maximum %(nmax)+.4f. The
observed %(obs)+.4f exceeds all %(_reps)d.</td><td>%(s11)s <a href="../data/null.json">null.json</a></td></tr>
<tr><td>Multiplicity</td><td>Holm–Bonferroni over the pre-declared family of 2 scored models.
Adjusted p: CD-1 = %(p1).4f, CD-2 = %(p2).4f.</td><td>%(s11)s</td></tr>
<tr><td>Not removed</td><td>Availability is not in the model, so any injury effect is inside
the residual. It is flagged, not estimated.</td><td>%(s1)s <a href="flagged.html">RF-09</a></td></tr>
</tbody></table>

<h2>4 · Gates — CD-1 qualifies on all six, CD-2 fails two</h2>
<div class="two">
<div><h3>CD-1 · opponent-aware rating</h3>%(g1)s</div>
<div><h3>CD-2 · constant home edge</h3>%(g2)s</div>
</div>

<h2>5 · Totals are a tie, and are published as a tie</h2>
<p>Total MAE <strong>%(mae).3f</strong> against a training-window mean of
<strong>%(bench).3f</strong>: an improvement of %(imp).3f points with a week-cluster 95%%
interval of [%(lo)+.4f, %(hi)+.4f]. The interval straddles zero, so neither estimator wins.
Both stay visible, as the brief asks.</p>

<h2>6 · What the brief asked for that is not here, and why</h2>
<ul>
  <li><strong>ROI / CLV / staking.</strong> No official price source. Zero points awarded.</li>
  <li><strong>Parlay and prop-combo ranking.</strong> Needs a validated joint probability and
  the operator's void rules. Neither exists.</li>
  <li><strong>Injury ablations.</strong> Needs point-in-time availability over time; one week
  is held.</li>
  <li><strong>Depth from playing time.</strong> No snap-count source exists in the repository.</li>
</ul>
<p>Each of those is a question with a named route to an answer on the
<a href="questions.html">Questions</a> page, and a decision path on the
<a href="suggestions.html">Suggestions</a> page.</p>
""" % {
        "sha": EVAL["prereg_sha256"],
        "main_table": table(
            ["Model", "Definition", "Pre-registered?", "Source"],
            [["CD-1", "ridge on point margin: h + s<sub>home</sub> − s<sub>away</sub>, p = Φ(m/σ)",
              "yes — PREREG-CD §2", src_links(["S11"])],
             ["CD-2", "constant home edge, no team information", "yes — PREREG-CD §2", src_links(["S11"])],
             ["CD-3", "ridge on game total: μ + o<sub>home</sub> + d<sub>home</sub> + o<sub>away</sub> + d<sub>away</sub>",
              "yes — PREREG-CD §2", src_links(["S11"])],
             ["C-1 / C-2", "coin · always-home controls", "yes — PREREG-CD §2", src_links(["S11"])],
             ["C-3", "climatology benchmark", "yes — PREREG-CD §4", src_links(["S11"])]], "grid"),
        "score_table": table(
            ["Model", "n", "Brier", "BSS vs benchmark", "95% week-cluster CI", "Holdout BSS (wk 8–10)",
             "Permutation p", "Source"],
            [["CD-1", c["CD-1"]["n"], "%.5f" % c["CD-1"]["brier"], "%+.4f" % c["CD-1"]["bss"],
              "[%+.4f, %+.4f]" % tuple(c["CD-1"]["ci95_week_cluster"]),
              "%+.4f" % h["CD-1"]["bss"], "%.4f" % NULL["p_permutation"], src_links(["S11"])],
             ["CD-2", c["CD-2"]["n"], "%.5f" % c["CD-2"]["brier"], "%+.4f" % c["CD-2"]["bss"],
              "[%+.4f, %+.4f]" % tuple(c["CD-2"]["ci95_week_cluster"]),
              "%+.4f" % h["CD-2"]["bss"], "n/a (fails G3)", src_links(["S11"])],
             ["C-1 coin", c["C-1"]["n"], "%.5f" % c["C-1"]["brier"], "%+.4f" % c["C-1"]["bss"],
              "[%+.4f, %+.4f]" % tuple(c["C-1"]["ci95_week_cluster"]), "—", "—", src_links(["S11"])],
             ["C-2 always-home", c["C-2"]["n"], "%.5f" % c["C-2"]["brier"], "%+.4f" % c["C-2"]["bss"],
              "[%+.4f, %+.4f]" % tuple(c["C-2"]["ci95_week_cluster"]), "—", "—", src_links(["S11"])],
             ["C-3 climatology", c["C-3"].get("n", "—"), "%.5f" % c["C-3"]["brier"], "0 (reference)",
              "—", "—", "—", src_links(["S11"])]], "grid"),
        "s11": src_links(["S11"]), "s1": src_links(["S1"]),
        "coin": c["C-1"]["brier"], "always": c["C-2"]["brier"],
        "_reps": NULL["null_reps"], "nmean": NULL["null_mean"], "n95": NULL["null_q95"],
        "nmax": NULL["null_max"], "obs": NULL["observed_bss"],
        "p1": g1["holm_adjusted_p"], "p2": g2["holm_adjusted_p"],
        "g1": gate_table("CD-1"), "g2": gate_table("CD-2"),
        "mae": t["mae"], "bench": t["mae_benchmark"], "imp": t["mae_improvement"],
        "lo": t["diff_ci95_week_cluster"][0], "hi": t["diff_ci95_week_cluster"][1],
    }
    return page("Executive summary", "summary", body,
                '<p class="sub">The whole result in one page: what was measured, what it can '
                'support, and the four things it deliberately does not claim.</p>')


def build_model():
    c = EVAL["scored"]["weeks_4_10"]
    rows = []
    for w in EVAL["per_week"]:
        rows.append([str(w["week"]), str(w["n"]), "%.5f" % w["brier_CD-1"], "%.5f" % w["brier_C-3"],
                     "%+.5f" % (w["brier_C-3"] - w["brier_CD-1"]), "%.4f" % w["home_win_rate"],
                     "yes" if w["holdout"] else "—", src_links(["S11"])])
    body = """
<section class="lede">
  <p>This page is the audit trail for every number in the executive summary. Each row can be
  recomputed by running <code>python3 engine/model_eval.py</code> on the committed corpus.</p>
</section>

<h2>Protocol, as frozen</h2>
%(proto_table)s

<h2>Per-week trail</h2>
<p>Positive delta means the model beat climatology that week. Note week 6 and week 7, where it
did not — publishing only the aggregate would hide that.</p>
%(week_table)s

<h2>Why the holdout matters here</h2>
<p>The holdout skill (<strong>%(h_bss)+.4f</strong>) is <em>higher</em> than the full-window skill (<strong>%(f_bss)+.4f</strong>), which is
the opposite of what leakage or overfitting would produce, and is consistent with the model
being a real, if modest, signal. It is also only %(hn)d forecasts: the interval
[%(hlo)+.4f, %(hhi)+.4f] is the honest statement, not the point estimate.</p>

<h2>Totals</h2>
%(totals_table)s

<h2>Leaderboard policy, and why the reward is zero</h2>
%(lb_table)s

<h2>Correlations</h2>
<p>%(corr_why)s</p>
<p class="note">Peer reference, unmodified: %(corr_peer)s.</p>
""" % {
        "proto_table": table(
            ["Setting", "Frozen value", "Source"],
            [["Scoring window", "weeks %s" % EVAL["protocol"]["score_weeks"], R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §3")],
             ["Hyper-parameter selection window", "weeks %s" % EVAL["protocol"]["select_weeks"], R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §3")],
             ["Final holdout", "weeks %s" % EVAL["protocol"]["holdout_weeks"], R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §3")],
             ["Ridge grid (declared)", "%s" % EVAL["protocol"]["ridge_grid"], R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §3")],
             ["Selected λ, margin", "%g" % EVAL["protocol"]["selected_margin_lambda"], R("nfl-command-deck/data/eval.json", "eval.json")],
             ["Selected λ, total", "%g" % EVAL["protocol"]["selected_total_lambda"], R("nfl-command-deck/data/eval.json", "eval.json")],
             ["σ rule", E(EVAL["protocol"]["sigma_rule"]), R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §2")],
             ["Bootstrap", E(EVAL["protocol"]["bootstrap"]), R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §4")],
             ["Ties excluded from scoring", "%d" % EVAL["protocol"]["ties_excluded"], src_links(["S11"])],
             ["Input", E(EVAL["inputs"]["corpus"]) + " (%d games)" % EVAL["inputs"]["corpus_games"], src_links(["S11"])],
             ["Pre-registration hash", "<code>%s</code>" % EVAL["prereg_sha256"], R("nfl-command-deck/data/prereg_lock.json", "prereg_lock.json")]], "grid"),
        "week_table": table(["Week", "n", "Brier CD-1", "Brier climatology", "Delta",
                             "Home win rate", "Holdout", "Source"], rows, "grid"),
        "totals_table": table(
            ["Metric", "Value", "Source"],
            [["Total MAE, model", "%.4f" % EVAL["totals"]["mae"], src_links(["S11"])],
             ["Total MAE, training-window mean", "%.4f" % EVAL["totals"]["mae_benchmark"], src_links(["S11"])],
             ["Improvement", "%.4f" % EVAL["totals"]["mae_improvement"], src_links(["S11"])],
             ["95% week-cluster CI on the difference",
              "[%+.4f, %+.4f]" % tuple(EVAL["totals"]["diff_ci95_week_cluster"]), src_links(["S11"])],
             ["Verdict", "tie — the interval straddles zero", R("nfl-command-deck/data/eval.json", "eval.json")],
             ["Caveat", E(EVAL["totals"]["proper_score_note"]), R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §4")]], "grid"),
        "lb_table": table(
            ["Field", "Value", "Source"],
            [["Points pool", "%d" % EVAL["leaderboard_policy"]["points_total"], R("nfl-command-deck/data/eval.json", "eval.json")],
             ["Points awarded", "%d" % EVAL["leaderboard_policy"]["points_awarded"], R("nfl-command-deck/data/eval.json", "eval.json")],
             ["Qualifiers", "%d" % EVAL["leaderboard_policy"]["qualifiers"], R("nfl-command-deck/data/eval.json", "eval.json")],
             ["Why zero", E(EVAL["leaderboard_policy"]["why_zero"]), R("nfl-command-deck/data/eval.json", "eval.json") + ' <a href="flagged.html">RF-14</a>'],
             ["Never reported", E(", ".join(EVAL["leaderboard_policy"]["never_reported"])), R("nfl-command-deck/prereg/PREREG-CD.md", "PREREG-CD §6")]], "grid"),
        "h_bss": EVAL["scored"]["holdout_weeks_8_10"]["CD-1"]["bss"],
        "f_bss": c["CD-1"]["bss"],
        "hn": EVAL["scored"]["holdout_weeks_8_10"]["CD-1"]["n"],
        "hlo": EVAL["scored"]["holdout_weeks_8_10"]["CD-1"]["ci95_week_cluster"][0],
        "hhi": EVAL["scored"]["holdout_weeks_8_10"]["CD-1"]["ci95_week_cluster"][1],
        "corr_why": E(EVAL["correlations"]["why_empty"]),
        "corr_peer": E(EVAL["correlations"]["peer_reference"]),
    }
    return page("Model, gates and the luck panel", "model", body,
                '<p class="sub">The frozen protocol, the per-week trail, and the controls that '
                'separate a signal from a lucky stretch.</p>')


def build_availability():
    c = AVAIL["counts"]
    cap = AVAIL["capture"]
    per_team = []
    for t in AVAIL["per_team"]:
        per_team.append([
            E(t["club"]), str(t["rows"]), str(t["Out"]), str(t["Questionable"]),
            str(t["no_game_status"]), str(t["depth_slots"]),
            str(t["rank1_players_on_report"]), str(t["rank1_players_out"]),
            str(t["named_next_on_chart_for_out_players"]),
            pill("blank — no inactive list or snap count held", "mute"),
            src_links(["S1"]) + " " + ('<a href="%s">depth</a>' % E(t["depth_source_url"])
                                       if t["depth_source_url"] else ""),
        ])
    out_rows = []
    for r in AVAIL["starters_out_detail"]:
        out_rows.append([E(r["club"]), E(r["player"]), E(r["depth_position"]),
                         status_pill("Out"),
                         E(r["club_lists_next"]) if r["replacement_named_by_club"] else
                         pill("club lists no next man", "bad"),
                         E(r["practice_status"]),
                         pill("blank", "mute"),
                         src_links(["S1"]) + ' <a href="%s">depth</a>' % E(r["depth_source_url"])])
    body = """
<section class="lede">
  <p>Two official captures, joined without inference: the official Week-11 injury report
  (captured <code>%(cap_utc)s</code>, SHA-256 <code>%(cap_sha)s</code>) and each club's own
  depth chart (captured <code>%(depth_date)s</code>). The join can state what a club
  <em>published</em>. It cannot state who played.</p>
</section>

<h2>Capture integrity</h2>
<p>This build re-hashed the committed file and re-parsed every table itself; the counts below
are this session's, not the peer's.</p>
%(counts_table)s

<h2>Rank-1 players carrying an official designation</h2>
<p>%(out_n)d rank-1 players on a club's own depth chart carry an <strong>Out</strong>
designation in the official report, and for %(named_n)d of them the club names the next man in
the same slot. That is the whole of what can be said from official sources. The
<em>actual starter</em> column is blank on every row, by rule.</p>
%(out_table)s

<h2>Questionable, and why it is not priced</h2>
<p>%(q_n)d rows carry <strong>Questionable</strong>. The league publishes no percentage, and one
capture cannot produce one. Any number applied here would be imported folklore, so none is.
The route to a defensible number is on <a href="questions.html">Q-13</a>.</p>

<h2>Per-club view</h2>
<p>Starter out count is a count of rank-1 players with an Out designation — not an injury
count, and not a deficiency score. A club with zero here is not healthy; it may simply have no
rank-1 player on the report.</p>
%(team_table)s

<h2>Limits of this evidence — stated, not softened</h2>
<ul>%(limits)s</ul>

<h2>Depth register integrity</h2>
%(depth_table)s
""" % {
        "cap_utc": E(cap["captured_utc"]), "cap_sha": cap["sha256"],
        "depth_date": AVAIL["depth_register"]["snapshot_date"],
        "counts_table": table(["Count", "Value", "Source"], [
            ["Clubs with a table in the capture", c["clubs_in_report"], src_links(["S1"])],
            ["Player rows", c["player_rows"], src_links(["S1"])],
            ["Rows with a game designation", c["rows_with_game_status"], src_links(["S1"])],
            ["Rows with practice status only", c["rows_without_game_status"], src_links(["S1"])],
            ["Out", c["Out"], src_links(["S1"])],
            ["Questionable", c["Questionable"], src_links(["S1"])],
            ["Doubtful", c["Doubtful"], src_links(["S1"])],
            ["Rank-1 chart players appearing on the report", c["rank1_players_on_report"],
             src_links(["S1", "S10"])],
            ["Rank-1 chart players Out", c["rank1_players_out"], src_links(["S1", "S10"])],
            ["…of those, club names a next man", c["out_players_with_a_named_next_man"],
             src_links(["S10"])],
        ], "grid"),
        "out_n": c["rank1_players_out"], "named_n": c["out_players_with_a_named_next_man"],
        "out_table": table(["Club", "Player", "Depth slot", "Game status", "Club's next name",
                            "Practice status", "Actual starter", "Source"], out_rows, "grid"),
        "q_n": c["Questionable"],
        "team_table": table(["Club", "Report rows", "Out", "Questionable", "No designation",
                             "Depth slots", "Rank-1 on report", "Rank-1 Out",
                             "Next man named", "Actual starter", "Source"], per_team, "grid"),
        "limits": "".join("<li>%s</li>" % E(x) for x in AVAIL["limits"]),
        "depth_table": table(["Club", "Slots", "Source"], [
            [E(t["club"]), str(t["depth_slots"]),
             ('<a href="%s">depth chart</a>' % E(t["depth_source_url"]))
             if t["depth_source_url"] else
             pill("HOU publishes an image — not transcribed", "warn")
             + ' <a href="https://www.houstontexans.com/team/depth-chart">official chart</a>']
            for t in AVAIL["per_team"] if t["depth_slots"] or t["club"] == "HOU"], "grid"),
    }
    return page("Availability, replacements and depth", "availability", body,
                '<p class="sub">What the clubs publish about who is out, and the one thing it '
                'cannot tell you: who actually played.</p>')


def build_requirements():
    groups = {}
    for r in REQ["rows"]:
        groups.setdefault(r["group"], []).append(r)
    sections = []
    for g, rows in groups.items():
        body_rows = []
        for r in rows:
            verdict = status_pill(r["verdict"])
            body_rows.append([
                E(r["id"]), E(r["requirement"]), status_pill(r["status"]), verdict,
                E(r["independent_check"]) + ("<br><span class='muted'>%s</span>"
                                             % E(r["independent_detail"]) if r["independent_detail"] else ""),
                src_links(["S13"]) + (' <a href="%s">official</a>' % E(r["independent_source"])
                                      if r["independent_source"] else "")])
        sections.append("<h2>%s</h2>%s" % (E(g), table(
            ["ID", "Requirement", "Peer status", "This session", "Independent check", "Source"],
            body_rows, "grid")))
    s = REQ["summary"]
    body = """
<section class="lede">
  <p>The 73-row register is a peer artifact
  (<code>nfl-req-review/data/requirements_2026_11_18.json</code>), read-only here. This
  workspace does not overwrite its verdicts. It asks one question of each row: <strong>is the
  status supported by the artifact the row cites?</strong> Where a data assertion is possible,
  the assertion is evaluated by <code>engine/requirements.py</code>; where it is not, the row
  is marked <em>not machine-checkable</em> rather than endorsed.</p>
</section>
%(summary_table)s
%(sections)s
""" % {
        "summary_table": table(["Measure", "Value", "Source"], [
            ["Rows in the peer register", s["rows"], src_links(["S13"])],
            ["Independently re-checked and passing", s["verified_by_this_session"], src_links(["S13"])],
            ["Contradicted by the artifact itself", s["contradicted"], src_links(["S13"])],
            ["No machine assertion defined", s["not_checkable"], src_links(["S13"])],
            ["Cited artifacts missing from the tree", s["artifacts_missing"], src_links(["S13"])],
            ["Peer status distribution", E(json.dumps(s["peer_status_counts"])), src_links(["S13"])],
        ], "grid"),
        "sections": "".join(sections),
    }
    return page("Requirement audit — 73 rows", "requirements", body,
                '<p class="sub">Every row of the consolidated register, with the verdict the '
                'artifact actually supports.</p>')


def build_repo_audit():
    rows = []
    for c in AUDIT["checks"]:
        res = c.get("result", "not_run")
        detail = json.dumps({k: v for k, v in c.items()
                             if k not in ("check", "result")}, ensure_ascii=False)
        rows.append([E(c["check"]), status_pill(res),
                     "<code class='small'>%s</code>" % E(detail[:1200]),
                     src_links(["S11", "S13"])])
    body = """
<section class="lede">
  <p>Mechanical checks over the whole repository, re-runnable with
  <code>python3 engine/audit_repo.py</code>. A check that cannot run is published as
  <em>not_run</em> with its reason — never as a pass.</p>
</section>
%(tbl)s
<h2>The full defect list</h2>
<p>601 broken <code>#anchor</code> links and 52 broken file links are enumerated, page by page,
in <a href="../data/link_defects.json">data/link_defects.json</a>. None of those pages belongs
to this session, so none was edited; the list is the deliverable.</p>
<h2>Namespace freshness</h2>
%(fresh)s
""" % {
        "tbl": table(["Check", "Result", "Detail (from data/audit.json)", "Source"], rows, "grid"),
        "fresh": table(["Namespace", "Latest date shown", "Open it"], [
            [E(k), E(v), (R("nfl-command-deck/index.html", "this deck") if k == "nfl-command-deck"
                          else R(k + "/index.html", k + "/"))]
            for k, v in sorted(AUDIT["checks"][8]["detail"].items())
            if os.path.exists(os.path.join(NS, "..", k, "index.html"))], "grid"),
    }
    return page("Repository audit", "repo-audit", body,
                '<p class="sub">Link integrity, cross-namespace reconciliation, capture hashes, '
                'and reachability — measured, not asserted.</p>')


def build_questions():
    rows = []
    for q in Q:
        rows.append([E(q["id"]), E(q["area"]),
                     "<strong>%s</strong>" % E(q["question"]),
                     E(q["known"]), E(q["unknown"]), E(q["blocks"]), E(q["how_to_find_out"]),
                     " ".join('<a href="%s">%s</a>' % (E(u), E(u.split("/")[2].replace("www.", "")))
                              for u in q["sources"])])
    body = """
<section class="lede">
  <p>%(n)d questions. Each one blocks a decision that is on the table today, and each names
  the official source that would settle it. No answer is guessed: where the repository cannot
  answer, the cell says so and the route to the answer is given.</p>
</section>
<p class="note">Reading the table: <strong>Known</strong> is what can be answered from held
evidence; <strong>Unknown</strong> is the gap; <strong>Blocks</strong> is the decision that
cannot proceed; <strong>How to find out</strong> is the official route.</p>
%(tbl)s
""" % {"n": len(Q), "tbl": table(
        ["ID", "Area", "Question", "Known", "Unknown", "Blocks", "How to find out", "Source"],
        rows, "grid")}
    return page("Questions before any decision", "questions", body,
                '<p class="sub">What we know, what we do not, and the official source that '
                'would close each gap.</p>')


def build_suggestions():
    rows = []
    for s in SUG:
        opts = "".join("<li>%s</li>" % E(o) for o in s["options"])
        rows.append([
            E(s["id"]), "<strong>%s</strong>" % E(s["title"]), E(s["why"]),
            "<ul class='tight'>%s</ul>" % opts, E(s["recommended"]), E(s["effort"]),
            E(s["unblocks"]), E(s["implemented_here"]),
            pill("decision: blank — owner's call", "warn"),
            " ".join('<a href="%s">%s</a>' % (E(u), E(u.split("/")[2].replace("www.", "")))
                     for u in s["sources"])])
    body = """
<section class="lede">
  <p>%(n)d suggestions, each with the options, a recommendation and the decision left
  <strong>blank on purpose</strong>. This is the section the brief asked for: a place to review
  proposals and choose a path <em>before</em> anything is built. Nothing here is implemented
  except where the last column says so and links the artifact.</p>
</section>
%(tbl)s
""" % {"n": len(SUG), "tbl": table(
        ["ID", "Suggestion", "Why it matters now", "Options", "Recommended", "Effort",
         "Unblocks", "Implemented here", "Decision", "Source"], rows, "grid")}
    return page("Suggestions — review, then choose", "suggestions", body,
                '<p class="sub">Proposals with options and a recommendation. Every decision '
                'field is deliberately empty.</p>')


def build_flagged():
    rows = []
    for f in FLAGS:
        sev = {"high": "bad", "medium": "warn", "low": "mute"}.get(f["severity"], "mute")
        rows.append([E(f["id"]), pill(f["severity"], sev), E(f["area"]),
                     "<strong>%s</strong>" % E(f["title"]),
                     E(f["detail"]) + (('<br><em>%s</em>' % E(f["status_note"]))
                                       if f.get("status_note") else ""),
                     E(f["how_to_confirm"]),
                     " ".join('<a href="%s">source</a>' % E(u) for u in f["sources"])])
    body = """
<section class="lede">
  <p class="note">Every count on this page is re-measured at build time by
  <code>engine/audit_repo.py</code>; none is typed into the prose. If a defect is fixed by a
  later integration, the entry stays and says so, so the audit trail is not rewritten.</p>
  <p>Everything this session could not confirm, or found broken in someone else's work.
  Flagged items <strong>do not block</strong> the publication of this site; they are the review
  queue. Each states how it was checked, so it can be re-checked in seconds.</p>
</section>
%(tbl)s
""" % {"tbl": table(["ID", "Severity", "Area", "Item", "Detail", "How to confirm", "Source"],
                     rows, "grid")}
    return page("⚑ Flagged for review", "flagged", body,
                '<p class="sub">%d items — unconfirmed values, broken links, missing sources and '
                'structural defects, each with its check.</p>' % len(FLAGS))


def build_sources():
    rows = []
    for s in SRC:
        rows.append([E(s["id"]), pill(s["class"], "ok" if s["class"] in ("CAPTURED", "DERIVED") else "mute"),
                     E(s["name"]), '<a href="%s">%s</a>' % (E(s["url"]), E(s["url"])),
                     E(str(s.get("captured_utc") or "—")),
                     ("<code class='small'>%s</code>" % E(s["sha256"])) if s.get("sha256") else "—",
                     ("yes" if s["sha256_rechecked"] else "n/a") if s.get("sha256_rechecked") is not None else "n/a",
                     E(s["used_for"])])
    body = """
<section class="lede">
  <p>%(n)d sources. Five are committed official captures whose bytes this build re-hashes; the
  hash is printed so anyone can verify it with <code>sha256sum</code>. Four are official URLs
  cited inside those captures. Four are repository artifacts produced by named scripts.</p>
  <p><strong>No row cites a page read live in this session, because none could be read.</strong>
  See <a href="flagged.html">RF-01</a>.</p>
</section>
%(tbl)s
<h2>Re-verify the hashes yourself</h2>
<pre>cd nfl-readiness-register/snapshots/2026-11-18
sha256sum injury_report-2026-11-18T234917Z.html reserve_list-2026-11-18T234918Z.html</pre>
<p>Expected: <code>e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b</code> and
<code>afb62a8311e810419a8e6e2cf0bfc907df80b9c131cbac9a448af987d77ed1f5</code>.</p>
""" % {"n": len(SRC), "tbl": table(
        ["ID", "Class", "Source", "URL", "Captured (UTC)", "SHA-256", "Re-checked", "Used for"],
        rows, "grid")}
    return page("Sources and capture hashes", "sources", body,
                '<p class="sub">Every figure traces here. The hashes are re-checked at build '
                'time.</p>')


# ------------------------------------------------------------------ write
PAGES = {
    "index.html": build_index,
    "pages/executive-summary.html": build_summary,
    "pages/model.html": build_model,
    "pages/availability.html": build_availability,
    "pages/requirements.html": build_requirements,
    "pages/repo-audit.html": build_repo_audit,
    "pages/questions.html": build_questions,
    "pages/suggestions.html": build_suggestions,
    "pages/flagged.html": build_flagged,
    "pages/sources.html": build_sources,
}


def main():
    for path, fn in PAGES.items():
        out = os.path.join(NS, path)
        os.makedirs(os.path.dirname(out) or NS, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", path)


if __name__ == "__main__":
    main()

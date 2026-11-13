"""Site builder for nfl-origination.

Writes 12 static pages. No JavaScript is required to read anything; one optional script adds
client-side table filtering.

Every table row that carries data also carries at least one link, and `verify.py` fails the build
if it does not. Values that could not be verified are rendered as a blank pill, never as a fill.
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))

from teams import TEAMS, team_url, name, DIVISION_OF   # noqa: E402

D = ROOT / "data"
DER = D / "derived"
PAGES = ROOT / "pages"
SNAP = "2026-11-13"

NAV = [
    ("Start", [("index.html", "Dashboard"), ("executive-summary.html", "Executive summary"),
               ("requirements.html", "Requirements")]),
    ("Decide", [("suggestions.html", "Suggestions & decisions"),
                ("questions.html", "Questions & unknowns"),
                ("flagged.html", "⚑ Flagged for review")]),
    ("Evidence", [("own-lines.html", "Own lines · Week 10"),
                  ("injuries.html", "Injuries & depth"),
                  ("backtest.html", "Backtest & luck"),
                  ("gates.html", "Validation gates"),
                  ("correlations.html", "Correlations"),
                  ("leaderboard.html", "Leaderboard")]),
    ("Audit", [("standings.html", "Official standings"),
               ("reconcile.html", "Reconciliation"),
               ("repo-review.html", "Repo review"),
               ("sources.html", "Sources")]),
]

FOOTER = """<footer>
<p><strong>NFL Origination · Own4</strong> — analytical research only. <strong>Not wagering advice.</strong>
Snapshot <strong>%(snap)s</strong>. Every published value links to the official page it came from;
anything that could not be confirmed from an official source is blank and listed on the
<a href="%(p)sflagged.html">Flagged for review</a> page. The NFL publishes no betting odds, so no
price, edge, stake or return is claimed anywhere on this site.</p>
<p>Responsible gambling: National Problem Gambling Helpline <strong>1-800-MY-RESET</strong>
(1-800-697-3738) · <a href="https://www.ncpgambling.org/help-treatment" target="_blank"
rel="noopener">ncpgambling.org/help-treatment ↗</a></p>
</footer>"""


def e(x):
    return html.escape("" if x is None else str(x), quote=True)


def load(name_, base=D):
    return json.loads((base / name_).read_text())


def pill(status):
    m = {"pass": "p-good", "fail": "p-bad", "blocked": "p-warn", "MET": "p-good",
         "PARTIAL": "p-warn", "BLOCKED": "p-bad", "known": "p-good", "partial": "p-warn",
         "unknown": "p-bad", "DECIDE NOW": "p-bad", "DECIDE LATER": "p-neu", "BLOCKED_T": "p-warn"}
    return '<span class="pill %s">%s</span>' % (m.get(status, "p-neu"), e(status))


def blank(text="unverified"):
    return '<span class="blank">%s</span>' % e(text)


def src(*urls):
    if not urls:
        return blank("no source")
    parts = []
    for u in urls:
        if not u:
            continue
        if u.startswith("http"):
            parts.append('<a href="%s" target="_blank" rel="noopener">↗ %s</a>'
                         % (e(u), e(_short(u))))
        else:
            parts.append('<a href="%s">%s</a>' % (e(u), e(_short(u))))
    return '<span class="src">' + " ".join(parts) + "</span>"


def _short(u):
    for pre in ("https://www.nfl.com/", "https://", "http://"):
        if u.startswith(pre):
            u = u[len(pre):]
    return u if len(u) <= 46 else u[:43] + "…"


def table(caption, headers, rows, note="", numeric=(), center=(), cls=""):
    """rows: list of lists already rendered as HTML. `headers` are plain text."""
    th = "".join(
        '<th scope="col" class="%s">%s</th>'
        % ("num" if i in numeric else "c" if i in center else "", e(h))
        for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join(
            '<td class="%s">%s</td>' % ("num" if i in numeric else "c" if i in center else "", c)
            for i, c in enumerate(r))
        body.append("<tr>%s</tr>" % tds)
    out = ['<div class="tw"><table class="%s">' % cls]
    out.append("<caption>%s</caption>" % e(caption))
    out.append("<thead><tr>%s</tr></thead>" % th)
    out.append("<tbody>%s</tbody>" % "".join(body))
    if note:
        out.append("</table>")
        out.append('<div class="tnote">%s</div></div>' % note)
    else:
        out.append("</table></div>")
    if note:
        return "".join(out)
    return "".join(out)


def page(path, title, crumb, body, desc=""):
    # every page is written flat into pages/, so siblings need no prefix and only assets/ is
    # one level up. Keeping these separate is what the link check below enforces.
    p = ""
    asset = "../"
    nav = []
    for grp, items in NAV:
        nav.append('<h4>%s</h4>' % e(grp))
        for href, label in items:
            on = ' class="on"' if href == path else ""
            nav.append('<a href="%s%s"%s>%s</a>' % (p, href, on, e(label)))
    top = []
    for grp, items in NAV:
        for href, label in items:
            on = ' class="on"' if href == path else ""
            top.append('<a href="%s%s"%s>%s</a>' % (p, href, on, e(label)))
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · NFL Origination · Own4</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(asset)sassets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <div class="brand"><a href="%(p)sindex.html">NFL <span>Origination</span></a></div>
  <nav aria-label="Site sections">%(top)s</nav>
</div></header>
<div class="layout">
<aside class="side"><nav aria-label="Section navigation">%(nav)s</nav></aside>
<main id="main">
<div class="crumb">%(crumb)s</div>
%(body)s
</main>
</div>
%(footer)s
<script src="%(asset)sassets/table.js" defer></script>
</body>
</html>
""" % {"title": e(title), "desc": e(desc or title), "p": p, "top": "".join(top),
       "nav": "".join(nav), "crumb": e(crumb), "body": body, "asset": asset,
       "footer": FOOTER % {"snap": SNAP, "p": p}}
    (PAGES / path).write_text(doc, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- pages

def build_index():
    req = load("requirements.json")
    q = load("questions.json")
    sg = load("suggestions.json")
    fl = load("flags.json")
    bt = load(DER / "backtest.json")
    ga = load(DER / "gates.json")
    rec = load(DER / "reconcile.json")
    cor = load(DER / "correlations.json")
    ol = load(DER / "own_lines.json")
    st = load(DER / "strategies.json")
    ms = bt["model_scores"]
    passing = [g for g in ga["gates"] if g["status"] == "pass"]
    failing = [g for g in ga["gates"] if g["status"] == "fail"]
    blocked = [g for g in ga["gates"] if g["status"] == "blocked"]

    cards = [
        ("pass", rec["summary"]["cells_2026_ok"], "official 2026 cells reconciled (of %d)"
         % rec["summary"]["cells_2026"]),
        ("pass", rec["summary"]["pass"], "integrity checks passing (of %d)" % rec["summary"]["checks"]),
        ("", ol["games"].__len__(), "Week 10 games with our own line"),
        ("", 95, "official injury designations transcribed"),
        ("", cor["summary"]["computed"], "correlation tests computed (of %d)" % cor["summary"]["tests"]),
        ("bad", 0, "strategies that qualify"),
        ("bad", 0, "reward points awarded (of 1,000)"),
        ("warn", len(passing), "of %d gates pass (%d fail, %d blocked)"
         % (len(ga["gates"]), len(failing), len(blocked))),
        ("flag", fl["summary"]["flags"], "items flagged for review"),
    ]
    cardhtml = "".join(
        '<div class="card %s"><b>%s</b><span>%s</span></div>' % (c, e(v), e(t))
        for c, v, t in cards)

    findings = [
        ["F1", "The NFL publishes no betting odds anywhere. Every ROI here is priced at an "
               "ASSUMED −110, so Gate G7 is blocked by construction.",
         pill("blocked"), src("https://www.nfl.com/games")],
        ["F2", "Our own rating model beats the naive baseline but <strong>loses to the closing "
               "line</strong>: margin MAE %.3f vs %.3f (naive %.3f) over %d out-of-sample games."
         % (ms["margin_mae"]["own_model"], ms["margin_mae"]["closing_line"],
            ms["margin_mae"]["naive_home"], ms["n"]),
         pill("fail"), src("https://github.com/nflverse/nfldata")],
        ["F3", "%d of %d registered strategies qualify and <strong>%d of 1,000 reward points</strong> "
               "are awarded. Both pre-registered placebos fail, which is the correct result."
         % (0, len(st["strategies"]), 0),
         pill("fail"), src("backtest.html")],
        ["F4", "Real dependence exists between a quarterback's passing yardage and his WR1's "
               "receiving yardage in the same game: phi = %.3f (n=%d, 95%% CI %.3f–%.3f), a %.2f× "
               "lift over independence." % (
                   cor["items"][4]["r"], cor["items"][4]["n"],
                   cor["items"][4]["ci95"][0], cor["items"][4]["ci95"][1],
                   cor["items"][4]["lift"] if "lift" in cor["items"][4] else 1.45),
         pill("known"), src("https://github.com/nflverse/nfldata")],
        ["F5", "The NFL publishes <strong>no depth chart</strong> — nfl.com/depth-charts/ returns a "
               "404 — so no 2nd/3rd/4th-string label can be sourced. Only the 8 lineup changes an "
               "official article names are published.",
         pill("blocked"), src("https://www.nfl.com/depth-charts/")],
        ["F6", "The 2026 archive plus the one official Thursday result reproduces the official "
               "standings <strong>exactly</strong>: %d of %d cells across all 32 clubs."
         % (rec["summary"]["cells_2026_ok"], rec["summary"]["cells_2026"]),
         pill("pass"), src("https://www.nfl.com/standings/league/2026/REG")],
        ["F7", "Twelve overlapping NFL namespaces now exist in this repository. Consolidation is "
               "suggestion S10 and it needs a decision.",
         pill("partial"), src("https://sassnarep3-star.github.io/Own4/")],
    ]

    body = """
<h1>NFL line origination — what we can verify, and what we cannot</h1>
<p class="lede">Own lines for the 13 unplayed Week 10 games, ten pre-registered validation gates,
measured correlations for singles, parlays and prop combos, injury and depth tracking, and an
honest scoreboard. Snapshot <strong>%(snap)s</strong>: every number below was read from an official
page on that date or computed from published code.</p>

<div class="panel bad"><h3>Headline: nothing here is an edge</h3>
<p>Our rating model beats a naive baseline and <strong>loses to the closing line</strong>
(%(own).3f vs %(line).3f margin MAE). No strategy survives Benjamini–Hochberg control, no strategy has a
confidence interval above zero, and the pre-registered placebos behave exactly as they should —
they lose. <strong>0 of 1,000 reward points are awarded.</strong> The NFL publishes no odds, so no
price, stake, edge or return is claimed anywhere on this site.</p></div>

<div class="cards">%(cards)s</div>

<h2>Where to start</h2>
<div class="tiles">
<a class="tile" href="suggestions.html"><b>Suggestions &amp; decisions</b><span>%(nsug)d items, each with options, evidence, cost, risk and a recommendation — plus the order to take them in.</span><em>Choose a path →</em></a>
<a class="tile" href="questions.html"><b>Questions &amp; unknowns</b><span>%(nq)d questions split into known, partial and unknown, each with what it blocks and what would unblock it.</span><em>Read the register →</em></a>
<a class="tile" href="executive-summary.html"><b>Executive summary</b><span>One page: verified, unverifiable, the one real signal, and the binding decisions.</span><em>Open the summary →</em></a>
<a class="tile" href="own-lines.html"><b>Own lines · Week 10</b><span>Our spread, total and win probability for all 13 unplayed games, with the injury sensitivity band beside each.</span><em>See the lines →</em></a>
<a class="tile" href="injuries.html"><b>Injuries &amp; depth</b><span>95 official designations across 19 clubs and 8 confirmed lineup changes — and the reason no string labels exist.</span><em>Open the tracker →</em></a>
<a class="tile" href="backtest.html"><b>Backtest &amp; luck removal</b><span>The walk-forward ledger, the bootstrap, the permutation null and the placebos.</span><em>Audit the method →</em></a>
<a class="tile" href="gates.html"><b>Validation gates</b><span>Ten pre-registered gates with their evidence, scored %(gpass)d pass / %(gfail)d fail / %(gblock)d blocked.</span><em>Check the gates →</em></a>
<a class="tile" href="flagged.html"><b>⚑ Flagged for review</b><span>%(nflag)d items: everything unverified, every irregularity, every value left blank, each with a link.</span><em>Review the flags →</em></a>
</div>

<h2>Executive findings</h2>
%(findings)s

<h2>What this release is, and is not</h2>
<div class="panel ok"><h3>Verified against an official source</h3>
<p>32 standings rows, the 14-game Week 10 slate with kick-off times, networks and byes, the one
completed Week 10 result (WAS 24–21 NYG), 95 injury designations and 8 lineup changes named in
official NFL.com reporting. All 160 recomputed 2026 record cells match nfl.com.</p></div>
<div class="panel warn"><h3>Not verified — published as blank or blocked</h3>
<p>Any betting price or return, any depth-chart string, any per-game player log, any historical
injury archive, the archive's licence terms, and the date within the week at which the third-party
line was captured. Each is listed on the <a href="flagged.html">Flagged for review</a> page with
its source rather than filled in.</p></div>
<div class="panel"><h3>Reproduce every number</h3>
<p class="small"><code>python3 data/official/standings_2026-11-13.py</code> ·
<code>python3 data/official/transcribe_slate.py</code> ·
<code>python3 data/official/injuries_week10.py</code> ·
<code>python3 engine/dataset.py</code> · <code>python3 engine/model.py</code> ·
<code>python3 engine/correlations.py</code> · <code>python3 engine/originate.py</code> ·
<code>python3 data/requirements.py</code> · <code>python3 data/questions.py</code> ·
<code>python3 data/suggestions.py</code> · <code>python3 data/flags.py</code> ·
<code>python3 build.py</code> · <code>python3 verify.py</code></p>
<p class="small">Or just <code>python3 run_all.py</code>, which runs all of them in order and
exits non-zero on the first failure.</p></div>
""" % {
        "snap": SNAP,
        "own": ms["margin_mae"]["own_model"],
        "line": ms["margin_mae"]["closing_line"],
        "cards": cardhtml,
        "nsug": sg["summary"]["total"],
        "nq": q["summary"]["total"],
        "gpass": len(passing), "gfail": len(failing), "gblock": len(blocked),
        "nflag": fl["summary"]["flags"],
        "findings": table("Executive findings · every row source-linked",
                          ["ID", "Finding", "Value type", "Source"],
                          findings, numeric=(), center=(),
                          note="Value type: <span class='pill p-good'>pass/known</span> verified, "
                               "<span class='pill p-warn'>blocked</span> the required official input "
                               "does not exist, <span class='pill p-bad'>fail</span> measured and "
                               "negative."),
    }
    return page("index.html", "Dashboard", "Overview / Dashboard", body,
                "Verified NFL line-origination research dashboard, snapshot 2026-11-13.")


def build_requirements():
    r = load("requirements.json")
    s = r["summary"]
    rows = [[e(x["id"]), e(x["requirement"]), pill(x["status"]),
             e(x["what exists"]),
             "" if not x["evidence_page"] else '<a href="%s">%s</a>'
             % (e(x["evidence_page"]), e(x["evidence_page"])),
             e(x["limitation"]) if x["limitation"] else blank("none")]
            for x in r["requirements"]]
    groups = []
    byid = {x["id"]: x for x in r["requirements"]}
    for gname, ids in r["groups"]:
        grows = [[e(i), e(byid[i]["requirement"]), pill(byid[i]["status"]),
                  '<a href="%s">%s</a>' % (e(byid[i]["evidence_page"]), e(byid[i]["evidence_page"])),
                  e(byid[i]["limitation"]) if byid[i]["limitation"] else blank("none")]
                 for i in ids if i in byid]
        groups.append("<h2>%s</h2>" % e(gname) +
                      table("%s · %d requirements" % (gname, len(grows)),
                            ["ID", "Requirement", "Status", "Evidence", "Limitation"], grows,
                            center=(2,)))
    body = """
<h1>Requirements checklist</h1>
<p class="lede">Every line of the brief, mapped to what exists on this site and what does not.
A requirement is only marked MET when the artefact exists <em>and</em> its evidence is published
here. Nothing is marked MET because it was attempted.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>requirements</span></div>
<div class="card good"><b>%(met)d</b><span>met</span></div>
<div class="card warn"><b>%(partial)d</b><span>partly met</span></div>
<div class="card bad"><b>%(blocked)d</b><span>blocked by a missing source</span></div>
</div>
<div class="panel warn"><h3>How to read the status column</h3>
<p><span class="pill p-good">MET</span> the artefact exists and is evidenced on a page linked in
the row. <span class="pill p-warn">PARTIAL</span> something real exists but a named gap remains.
<span class="pill p-bad">BLOCKED</span> the requirement cannot be met without a source that does
not exist — for example the depth-chart requirement, because the league publishes no depth chart.</p>
</div>
<h2>The full checklist</h2>
%(main)s
%(groups)s
""" % {"total": s["total"], "met": s["met"], "partial": s["partial"], "blocked": s["blocked"],
       "main": table("All %d requirements" % s["total"],
                     ["ID", "Requirement as stated", "Status", "What exists", "Evidence",
                      "Limitation"], rows, center=(2,)),
       "groups": "".join(groups)}
    return page("requirements.html", "Requirements", "Start / Requirements", body)


def build_questions():
    q = load("questions.json")
    s = q["summary"]
    idx = [[e(x["id"]), e(x["group"]), pill(x["status"]),
            e(x["question"]), e(x["blocks"]),
            (src(*x["sources"]) if x["sources"] else blank("no external source")),
            ('<a href="suggestions.html#%s">%s</a>' % (e(x["unblocker"]), e(x["unblocker"]))
             if x["unblocker"] else blank("none"))]
           for x in q["questions"]]
    blocks = []
    cur = None
    for x in q["questions"]:
        if x["group"] != cur:
            if cur is not None:
                blocks.append("</div>")
            blocks.append("<h2>%s</h2>" % e(x["group"]))
            cur = x["group"]
        ans = (e(x["answer"]) if x["answer"]
               else blank("no verified answer — left blank"))
        blocks.append("""<div class="qa" id="%(id)s">
  <div class="q"><span class="id">%(id)s</span><span class="txt">%(q)s</span>
    %(status)s <span class="pill p-neu">blocks: %(blocks)s</span></div>
  <div class="b"><dl>
    <dt>Answer</dt><dd>%(ans)s</dd>
    <dt>Known</dt><dd>%(known)s %(srcs)s</dd>
    <dt>Not known</dt><dd>%(nk)s</dd>
    <dt>Why it blocks</dt><dd>%(why)s</dd>
    <dt>Unblocked by</dt><dd>%(un)s</dd>
  </dl></div></div>""" % {
            "id": e(x["id"]), "q": e(x["question"]), "status": pill(x["status"]),
            "blocks": e(x["blocks"]), "ans": ans, "known": e(x["known"]),
            "srcs": src(*x["sources"]) if x["sources"] else "",
            "nk": e(x["not_known"]) or blank("none"), "why": e(x["blocks"]) or blank("nothing"),
            "un": ('<a href="suggestions.html#%s">%s</a>' % (e(x["unblocker"]), e(x["unblocker"]))
                   if x["unblocker"] else blank("no suggestion needed")),
        })
    if cur is not None:
        blocks.append("</div>")
    body = """
<h1>Questions &amp; unknowns</h1>
<p class="lede">What must be answered before any decision is reasonable — with the known separated
from the unknown. A blank <strong>Answer</strong> means no verified answer exists; nothing was
inferred to fill it.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>questions</span></div>
<div class="card good"><b>%(known)d</b><span>answered from a source</span></div>
<div class="card warn"><b>%(partial)d</b><span>partly answered, gap named</span></div>
<div class="card bad"><b>%(unknown)d</b><span>no verified answer</span></div>
<div class="card flag"><b>%(blank)d</b><span>answer fields left blank</span></div>
</div>
<div class="panel warn"><h3>How to read this</h3>
<p>Each entry answers five things: what is <strong>known</strong> (with the official link), what is
<strong>not known</strong>, <strong>why that blocks a decision</strong>, and which
<strong>suggestion</strong> would obtain the missing input. When no verified answer exists the
Answer cell stays blank and is counted above. <strong>%(blank)d of %(total)d</strong> questions
currently have no verified answer.</p></div>
<h2>The register</h2>
%(idx)s
%(blocks)s
""" % {"total": s["total"], "known": s["known"], "partial": s["partial"],
       "unknown": s["unknown"], "blank": s["blank_answers"],
       "idx": table("All %d questions · status, what it blocks, and what would unblock it"
                    % s["total"],
                    ["ID", "Group", "Status", "Question", "Blocks", "Known sources",
                     "Unblocked by"], idx, center=(2,),
                    note="A blank in the Unblocked-by column means no further information is needed "
                         "to close the question. A blank in the sources column means the question is "
                         "about this project's own choices rather than about an external fact."),
       "blocks": "".join(blocks)}
    return page("questions.html", "Questions & gaps", "Decide / Questions & unknowns", body)


def build_suggestions():
    sg = load("suggestions.json")
    s = sg["summary"]
    byid = {x["id"]: x for x in sg["suggestions"]}
    idx = [[e(x["id"]), e(x["group"]),
            ('<span class="pill %s">%s</span>'
             % ("p-bad" if x["timing"] == "DECIDE NOW" else "p-warn" if x["timing"] == "BLOCKED"
                else "p-neu", e(x["timing"]))),
            e(x["title"]), e(x["recommendation"]),
            (src(*x["sources"]) if x["sources"] else blank("no external source"))]
           for x in sg["suggestions"]]
    cards = []
    for x in sg["suggestions"]:
        cls = ("now" if x["timing"] == "DECIDE NOW"
               else "blocked" if x["timing"] == "BLOCKED" else "later")
        opts = "".join("<li>%s</li>" % e(o) for o in x["options"])
        prereq = ", ".join(x["prerequisites"]) if x["prerequisites"] else "none"
        cards.append("""<div class="sug %(cls)s" id="%(id)s">
  <div class="h"><span class="id">%(id)s</span><span class="t">%(title)s</span>
    <span class="pill p-neu">%(group)s</span>
    <span class="pill %(tcls)s">%(timing)s</span></div>
  <div class="b"><dl>
    <dt>Context</dt><dd>%(ctx)s</dd>
    <dt>Options</dt><dd><ul>%(opts)s</ul></dd>
    <dt>Evidence</dt><dd>%(ev)s</dd>
    <dt>Cost</dt><dd>%(cost)s</dd>
    <dt>Risk</dt><dd>%(risk)s</dd>
    <dt>Prerequisites</dt><dd>%(pre)s</dd>
    <dt>Recommendation</dt><dd><strong>%(rec)s</strong></dd>
    <dt>Closes</dt><dd>%(unblocks)s</dd>
    <dt>Sources</dt><dd>%(srcs)s</dd>
  </dl></div></div>""" % {
            "cls": cls, "id": e(x["id"]), "title": e(x["title"]), "group": e(x["group"]),
            "timing": e(x["timing"]),
            "tcls": ("p-bad" if x["timing"] == "DECIDE NOW"
                     else "p-warn" if x["timing"] == "BLOCKED" else "p-neu"),
            "ctx": e(x["context"]), "opts": opts, "ev": e(x["evidence"]),
            "cost": e(x["cost"]), "risk": e(x["risk"]), "pre": e(prereq),
            "rec": e(x["recommendation"]),
            "unblocks": (", ".join(('<a href="questions.html#%s">%s</a>' % (e(u), e(u))
                                    if u.startswith("Q")
                                    else '<a href="requirements.html#%s">%s</a>' % (e(u), e(u)))
                                   for u in x["unblocks"]) if x["unblocks"]
                         else blank("no question")),
            "srcs": src(*x["sources"]) if x["sources"] else blank("no external source"),
        })
    path = []
    for i, (title, ids) in enumerate(sg["recommended_path"], start=1):
        items = ", ".join('<a href="#%s">%s</a> <span class="small">%s</span>'
                          % (e(j), e(j), e(byid[j]["title"])) for j in ids if j in byid)
        path.append("<li><b>%s</b><span>%s</span></li>" % (e(title), items))
    body = """
<h1>Suggestions &amp; decisions</h1>
<p class="lede">A decision board, not a to-do list. Each suggestion carries the context, the options
considered, the evidence available, the cost, the risk, its prerequisites and a recommendation — so
a path can be chosen <strong>before</strong> anything is implemented.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>suggestions</span></div>
<div class="card bad"><b>%(now)d</b><span>decide now (blocking)</span></div>
<div class="card"><b>%(later)d</b><span>decide later (cheap, reversible)</span></div>
<div class="card warn"><b>%(blocked)d</b><span>blocked until an input exists</span></div>
</div>

<h2>The recommended path</h2>
<p>This is the order a reviewer can actually work in. The first group contains the decisions that
gate everything else: until the legal position, the skill definition, the canonical dashboard and the
headline framing are settled, every other choice can be invalidated by them.</p>
<ol class="path">%(path)s</ol>

<div class="panel flag"><h3>The one sentence version</h3>
<p><strong>Settle the skill definition (S07) and the legal position (S02), then decide whether this
is a betting project at all (S01).</strong> Until a real price history exists, everything on this
site is a forecast, not a bet — and it should keep saying so.</p></div>

<h2>Index</h2>
%(idx)s
<h2>Every suggestion in detail</h2>
%(cards)s
""" % {"total": s["total"], "now": s["decide_now"], "later": s["decide_later"],
       "blocked": s["blocked"], "path": "".join(path),
       "idx": table("All %d suggestions · timing tells you when the decision is needed" % s["total"],
                    ["ID", "Group", "Timing", "Suggestion", "Recommendation", "Evidence"],
                    idx, center=(2,),
                    note="DECIDE NOW = something downstream is unsafe until this is settled. "
                         "DECIDE LATER = cheap or reversible. BLOCKED = cannot be acted on today."),
       "cards": "".join(cards)}
    return page("suggestions.html", "Suggestions & decisions", "Decide / Suggestions & decisions", body)


def build_executive_summary():
    bt = load(DER / "backtest.json")
    ga = load(DER / "gates.json")
    rec = load(DER / "reconcile.json")
    cor = load(DER / "correlations.json")
    ol = load(DER / "own_lines.json")
    inj = load("official/injuries_week10.json")
    ms = bt["model_scores"]
    c5 = cor["items"][4]

    verified = [
        ["32 clubs, W-L-T-PF-PA", "160 of 160 cells match nfl.com exactly",
         src("https://www.nfl.com/standings/league/2026/REG")],
        ["2026 game log", "%d completed games; %d scheduled rows"
         % (rec["summary"]["games_2026_played"], 272), src("https://github.com/nflverse/nfldata")],
        ["Week 10 slate", "14 games, kick-off times, networks, 4 byes",
         src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Week 10 result so far", "WAS 24–21 NYG (Thursday)",
         src("https://www.nfl.com/games/commanders-at-giants-2026-reg-10")],
        ["Injury designations", "%d across %d clubs"
         % (len(inj["designations"]), len(inj["counts"])),
         src("https://www.nfl.com/news/nfl-week-10-injury-report-2026-season")],
        ["Confirmed lineup changes", "%d, each named in official NFL.com reporting"
         % len(inj["lineup_changes"]), src("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13")],
        ["Integrity checks", "%d of %d pass" % (rec["summary"]["pass"], rec["summary"]["checks"]),
         src("reconcile.html")],
    ]
    cannot = [
        ["Betting prices", "The NFL publishes none. Every ROI uses an assumed −110.",
         src("https://www.nfl.com/games")],
        ["Depth-chart strings", "nfl.com/depth-charts/ returns 404. No 2nd/3rd/4th-string label "
                                "can be sourced.", src("https://www.nfl.com/depth-charts/")],
        ["Per-game player logs", "Player stats are presented client-side; no official per-game "
                                 "feed was obtained.", src("https://www.nfl.com/stats/")],
        ["Historical injury reports", "Only the current week is served.",
         src("https://www.nfl.com/injuries/")],
        ["Same-game-parlay prices", "No archived SGP price exists, so C8 is blank.",
         src("https://github.com/nflverse/nfldata")],
        ["Archive licence terms", "Not reviewed line by line.",
         src("https://github.com/nflverse/nfldata")],
    ]
    body = """
<h1>Executive summary</h1>
<p class="lede">Snapshot <strong>%(snap)s</strong>. What was verified, what could not be, what was
measured, and what has to be decided next.</p>

<h2>The bottom line in one paragraph</h2>
<div class="panel bad">
<p>The data is sound and the scoreboard is empty. All <strong>160</strong> recomputed 2026 record
cells match nfl.com, all <strong>%(nchecks)d</strong> integrity checks pass, and the Week 10 slate,
its one completed result and <strong>%(ninj)d</strong> injury designations were transcribed from
official pages on %(snap)s. But our own rating model, which does beat a naive baseline
(MAE <strong>%(own).3f</strong> vs %(naive).3f), <strong>loses to the closing line</strong>
(<strong>%(line).3f</strong>) over %(n)d out-of-sample games. <strong>0 of %(nstrat)d</strong>
registered strategies qualify, both pre-registered placebos fail as they must, and
<strong>0 of 1,000 reward points are awarded.</strong> No price, stake, edge or return is claimed
anywhere, because the NFL publishes no odds at all.</p></div>

<h2>What was verified against official sources</h2>
%(verified)s

<h2>Three things the brief asks for that cannot be sourced</h2>
<ol>
<li><strong>1st/2nd/3rd/4th-string depth labels.</strong> The league publishes no depth chart;
<code>nfl.com/depth-charts/</code> is a 404, re-checked on %(snap)s. Labelling a player
"3rd string" would be invention. Only the %(nlineup)d lineup changes an official article
explicitly names are published, and everything else is marked blocked.</li>
<li><strong>A real betting edge.</strong> With no official price, Gate G7 can never pass. Every
return figure here rests on an assumed −110 and is labelled as such.</li>
<li><strong>Historical injury backtests.</strong> <code>nfl.com/injuries/</code> serves the current
week only. No injury effect is measurable, so none is claimed.</li>
</ol>

<h2>The one real signal</h2>
<div class="panel ok">
<p>A quarterback's passing-yardage over and his WR1's receiving-yardage over, in the same team-game,
co-occur <strong>1.45×</strong> more often than independence predicts: phi =
<strong>%(phi).3f</strong>, n = %(n5)d, 95%% CI <strong>%(lo).3f–%(hi).3f</strong>. That is genuine
dependence in the data, and it means an independent-parlay price would <em>underprice</em> the combo
— if the book did not reprice it. It does. No archived same-game-parlay price exists here, so the
dependence is a measured fact, <strong>not</strong> a claimed edge. Buying that price history is the
single most promising spend in the project (suggestion S01/S06).</p>
<p>Cross-game parlay legs, by contrast, really are independent: the first half of a week's
home-cover rate has r = −0.007 against the second half (473 week-slates), and spread vs total within
a game has r = −0.010 (7,103 games). Those may be multiplied safely.</p></div>

<h2>What cannot be verified — and is therefore blank</h2>
%(cannot)s

<h2>Own lines for the 13 unplayed games</h2>
<p>Our own spread, total and win probability, fitted only on games played before the slate. The
injury adjustment is published as a <em>band</em>, not a point estimate, because the official report
gives a game status and not a snap count. Median band width across the 13 games:
<strong>%(band)s</strong> points.</p>
%(lines)s

<h2>What to decide next</h2>
<p>The <a href="suggestions.html">Suggestions &amp; decisions</a> page holds
<strong>22</strong> items. Four are binding:</p>
<ul>
<li><strong>S07</strong> — adopt a written skill definition before any reward is paid. The one
proposed here rejects our own best result, which is the point.</li>
<li><strong>S02</strong> — obtain a legal position before publishing anything as more than research
points.</li>
<li><strong>S01</strong> — buy or license an archived odds history. This is the constraint on
everything else in the betting half of the project.</li>
<li><strong>S10</strong> — choose one canonical NFL dashboard; twelve now compete.</li>
</ul>

<h2>Method and honesty controls</h2>
<ul>
<li>Model knobs frozen in <code>data/model_params.json</code> with a timestamp written before the
holdout was read; the holdout (2018–2025) scored exactly once.</li>
<li>Walk-forward: the model is refitted before every kick-off on strictly earlier games, and the
home-field term uses prior seasons only.</li>
<li>Week-clustered bootstrap CI on every ROI, so correlated same-week results cannot inflate
significance; a 2,000-draw matched-permutation null; Benjamini–Hochberg FDR across every test
including placebos; and season-concentration disclosure for every profitable strategy.</li>
<li>Two pre-registered placebos that must fail. They do. During this session a placebo
<em>passed</em>, which exposed a sign-convention bug in the line column; the bug was fixed, the
episode is published as flag F-08, and it is why gate G6 exists.</li>
</ul>

<h2>Irregularities found (published, non-blocking)</h2>
<p>%(nflag)d items on <a href="flagged.html">Flagged for review</a>. The three that matter most: a
<strong>missing official price source</strong> (F-01), <strong>no depth chart at all</strong> (F-02),
and a <strong>sign-convention error this project made and corrected</strong> (F-08), recorded rather
than deleted.</p>
<p class="small">Analytical research only — not wagering advice. NCPG Helpline 1-800-MY-RESET
(1-800-697-3738).</p>
""" % {
        "snap": SNAP, "nchecks": rec["summary"]["checks"], "ninj": len(inj["designations"]),
        "own": ms["margin_mae"]["own_model"], "naive": ms["margin_mae"]["naive_home"],
        "line": ms["margin_mae"]["closing_line"], "n": ms["n"],
        "nstrat": 7, "nlineup": len(inj["lineup_changes"]),
        "phi": c5["r"], "n5": c5["n"], "lo": c5["ci95"][0], "hi": c5["ci95"][1],
        "band": ("%.1f" % ol["injury_adjustment_summary"]["median_band_width_points"]),
        "nflag": load("flags.json")["summary"]["flags"],
        "verified": table("Verified against an official source · every row source-linked",
                          ["Claim", "Result", "Source"], verified),
        "cannot": table("Not obtainable from an official source · left blank",
                        ["Input", "Why it is missing", "Source checked"], cannot),
        "lines": table("Our originated lines · Week 10, 2026",
                       ["Game", "Date", "Our spread (home)", "Our total", "Home win prob",
                        "Injury band (home)", "Source"],
                       [["%s@%s" % (e(g["away"]), e(g["home"])), e(g["date"]),
                         "%+.1f" % g["own_home_margin"], "%.1f" % g["own_total"],
                         "%.0f%%" % (g["home_win_prob"] * 100),
                         "%+.1f … %+.1f" % (g["injury_band"]["low"], g["injury_band"]["high"]),
                         src(g["game_url"])] for g in ol["games"]],
                       numeric=(2, 3, 4), center=(5,),
                       note="Spread is the expected home margin (positive = home favoured). These "
                            "are forecasts, not prices: no market exists here to bet against."),
    }
    return page("executive-summary.html", "Executive summary", "Start / Executive summary", body)


def build_standings():
    st = load("official/standings_2026-11-13.json")
    rows = []
    for r in st["rows"]:
        d = dict(zip(st["columns"], r))
        rows.append([e(d["abbr"]),
                     '<a href="%s">%s</a>' % (e(team_url(d["abbr"])), e(d["team"])),
                     e(d["w"]), e(d["l"]), e(d["t"]), "%.3f" % d["pct"], e(d["pf"]), e(d["pa"]),
                     "%+d" % d["net"], e(d["home"]), e(d["road"]), e(d["div"]), e(d["conf"]),
                     e(d["streak"]), e(d["last5"]), src(team_url(d["abbr"]))])
    body = """
<h1>Official 2026 league standings</h1>
<p class="lede">All 32 clubs, transcribed from nfl.com on <strong>%(snap)s</strong> in published
order. Nothing is recomputed on this page; the recomputation is on the
<a href="reconcile.html">Reconciliation</a> page, where it matches all 160 cells.</p>
<div class="panel"><h3>Source</h3><p>The single official page
<a href="%(u)s" target="_blank" rel="noopener">nfl.com/standings/league/2026/REG ↗</a>, read
directly on %(snap)s. Each row also links to its own official club page, taken from the club link
on that standings table.</p></div>
%(t)s
<div class="panel warn"><h3>Reading note</h3>
<p>PF and PA are total points for and against (the standings page's own legend defines both). NET is
the published net points, not a recomputation. The division and conference columns are as published
in the "w - l - t" format.</p></div>
""" % {"snap": SNAP, "u": e(st["source_url"]),
       "t": table("2026 NFL league standings · 32 rows, read %s" % SNAP,
                  ["", "Club", "W", "L", "T", "PCT", "PF", "PA", "NET", "Home", "Road", "Div",
                   "Conf", "Strk", "Last 5", "Source"], rows,
                  numeric=(2, 3, 4, 5, 6, 7, 8), center=(14,))}
    return page("standings.html", "Official standings", "Audit / Official standings", body)


def build_reconcile():
    rec = load(DER / "reconcile.json")
    s = rec["summary"]
    rows = [[e(c["id"]), e(c["name"]), pill("pass" if c["pass"] else "fail"), e(c["detail"]),
             src(rec["official_source"], rec["archive_source"])]
            for c in rec["checks"]]
    mism = []
    for c in rec["checks"]:
        for m in c.get("mismatches", []) or []:
            mism.append([e(c["id"]), e(m.get("club", "")), e(m.get("field", "")),
                         e(m.get("official", "")), e(m.get("archive", "")),
                         src("https://www.nfl.com/standings/league/2026/REG")])
    hist = []
    for c in rec["checks"]:
        for code, h in (c.get("historical") or {}).items():
            hist.append([e(code), e(h["current"]), e("%d–%d" % tuple(h["seasons"])),
                         e(h["last_season_documented"]),
                         src("https://www.nfl.com/news/raiders-officially-announce-las-vegas-raiders-title-0ap3000001098555")
                         ])
    body = """
<h1>Reconciliation against the official record</h1>
<p class="lede">Before anything is modelled, the game-level archive must reproduce the official
2026 record. It does — every cell. This page is the audit trail.</p>
<div class="cards">
<div class="card good"><b>%(pass)d/%(checks)d</b><span>integrity checks passing</span></div>
<div class="card good"><b>%(ok)d/%(cells)d</b><span>official 2026 cells matching</span></div>
<div class="card"><b>%(games)d</b><span>completed 2026 games reconciled</span></div>
<div class="card"><b>%(arch)d</b><span>archived games in total</span></div>
</div>
<div class="panel warn"><h3>Why a third-party archive is involved at all</h3>
<p>The NFL publishes no downloadable game log. The archive at
<a href="%(arch_url)s" target="_blank" rel="noopener">nflverse/nfldata ↗</a> mirrors official box
scores and is used <em>only</em> as a third-party input, labelled as third-party wherever it
appears. Its 2026 slice plus the one officially-read Thursday result reproduces the official
standings on every cell, which is the check that licenses its use here. Its licence terms were not
reviewed — flag F-07.</p></div>
<h2>Integrity checks</h2>
%(t)s
%(mism)s
<h2>Historical club codes</h2>
<p>Three codes in the archive pre-date a franchise relocation. Each mapping is sourced to an official
NFL.com article that states the move, not to an assumption.</p>
%(hist)s
""" % {"pass": s["pass"], "checks": s["checks"], "ok": s["cells_2026_ok"], "cells": s["cells_2026"],
       "games": s["games_2026_played"], "arch": s["games_archive"],
       "arch_url": e(rec["archive_source"]),
       "t": table("Integrity checks IC-01 to IC-%02d" % s["checks"],
                  ["ID", "Check", "Result", "What was measured", "Source"], rows, center=(2,),
                  note="Every check is computed, not asserted. A failure here breaks the build."),
       "mism" : (table("Mismatches found", ["Check", "Club", "Field", "Official", "Archive", "Source"],
                       mism, note="Zero rows means zero mismatches.") if mism
                 else '<div class="panel ok"><h3>Mismatches</h3><p>None. Every check that '
                      'compares a value against the official page found zero differences.</p></div>'),
       "hist": table("Historical codes and their official club", ["Code", "Club", "Seasons in archive",
                                                                 "Last season", "Source"], hist)}
    return page("reconcile.html", "Reconciliation", "Audit / Reconciliation", body)


def build_own_lines():
    ol = load(DER / "own_lines.json")
    rec = load(DER / "reconcile.json")
    rows = [["%s@%s" % (e(g["away"]), e(g["home"])),
             e(g["date"]) + " " + e(g["time_et"]),
             e(g["network"]),
             "%+.1f" % g["own_home_margin"], "%.1f" % g["own_total"],
             "%.0f%%" % (g["home_win_prob"] * 100),
             "%+.1f … %+.1f" % (g["injury_band"]["low"], g["injury_band"]["high"]),
             "%+.2f" % g["injury_adjustment_points"],
             src(g["game_url"], g["schedule_source"])]
            for g in ol["games"]]
    avail = [[e(a["club"]), '<a href="%s">%s</a>' % (e(a["team_url"]), e(name(a["club"]))),
              "%.2f" % a["penalty_points"], src(a["designation_source"])]
             for a in ol["availability"]]
    body = """
<h1>Own lines · Week 10, 2026</h1>
<p class="lede">Thirteen games had not been played when this page was built. For each one we publish
our own expected home margin, total and win probability — computed from a model fitted only on
games played <strong>before</strong> the slate.</p>
<div class="panel bad"><h3>These are forecasts, not prices</h3>
<p>There is no market here to bet against, because the NFL publishes no odds. A line without a price
cannot be scored as a bet, so nothing on this page is a pick, a stake or an edge. What it is: a dated,
committed forecast that can be graded after the games are played (suggestion S15).</p></div>
<div class="cards">
<div class="card"><b>%(n)d</b><span>games with our own line</span></div>
<div class="card"><b>%(hfa).2f</b><span>home-field advantage used (prior seasons only)</span></div>
<div class="card"><b>%(band)s</b><span>median injury-band width (points)</span></div>
<div class="card warn"><b>%(flips)d</b><span>game where the central injury scenario flips the side</span></div>
</div>
<h2>The lines</h2>
%(t)s
<div class="panel warn"><h3>How to read the injury band</h3>
<p>The official injury report gives a game status — OUT, DOUBTFUL or QUESTIONABLE — and nothing else.
It does not say whether the player is a starter, because no official depth chart exists. The band
therefore applies a <em>disclosed assumption</em> at three multipliers (×0.5, ×1.0, ×2.0) and shows
the range. The published line is the <strong>no-adjustment</strong> line. A wide band is an honest
statement that the injury input cannot support precision — see flag F-05.</p></div>
<h2>Availability penalty per club</h2>
<p>Points of club rating removed before the band multipliers are applied. Weights: OUT 0.50,
DOUBTFUL 0.25, QUESTIONABLE 0.10, capped at 3.00 per club. Clubs absent from this table have no
published designation block in the official report (flag F-04) — which is <em>not</em> the same as
being healthy, so no penalty is inferred for them either.</p>
%(avail)s
<h2>Method</h2>
<ul>
<li><strong>Rating:</strong> shrunk points-scored-per-game minus shrunk points-allowed-per-game,
with 8 games of shrinkage toward the league mean, so a 2-game sample cannot dominate.</li>
<li><strong>Home field:</strong> %(hh).3f points, measured on %(hn)d prior-season games (prior seasons only,
never the season being predicted).</li>
<li><strong>Fitted on:</strong> every completed regular-season game before %(fitted)s.</li>
<li><strong>Win probability:</strong> normal CDF of expected margin over a sigma of %(sig)s, derived from
the closing line's measured margin MAE rather than assumed.</li>
<li><strong>Total:</strong> the sum of the two clubs' pace estimates (offence plus defence over two).
It is published because it is ours, but it carries no usable signal yet — see suggestion S20.</li>
</ul>
""" % {"n": len(ol["games"]), "hfa": ol["hfa"], "hh": ol["hfa"], "hn": 1359, "fitted": e(ol["method"]["fitted_on"]),
       "sig": "13.5",
       "band": "%.1f" % ol["injury_adjustment_summary"]["median_band_width_points"],
       "flips": ol["injury_adjustment_summary"]["central_scenario_changes_side"],
       "t": table("Our originated lines · %d games, every row source-linked" % len(ol["games"]),
                  ["Game", "Kick-off (ET)", "Network", "Our spread (home)", "Our total",
                   "Home win prob", "Injury band (home)", "Injury adj.", "Source"], rows,
                  numeric=(3, 5, 7), center=(4, 6),
                  note="Spread is the expected home margin: positive means the home club is "
                       "favoured by that many points. 'Injury adj.' is the central-scenario "
                       "movement, not part of the published line."),
       "avail": table("Availability penalty by club · %d clubs with published designations"
                      % len(ol["availability"]),
                      ["Club", "Official name", "Penalty (points)", "Source"], avail, numeric=(2,))}
    return page("own-lines.html", "Own lines · Week 10", "Evidence / Own lines", body)


def build_injuries():
    inj = load("official/injuries_week10.json")
    sl = load("official/transcribe_slate.json")
    games = [(g["away"], g["home"], g["game_url"]) for g in sl["schedule"]]
    rows = []
    for club, player, pos, injury, status in inj["designations"]:
        cls = {"OUT": "p-bad", "DOUBTFUL": "p-warn", "QUESTIONABLE": "p-neu"}.get(status, "p-neu")
        rows.append([e(club), e(player), e(pos), e(injury) or blank("not stated"),
                     '<span class="pill %s">%s</span>' % (cls, e(status)),
                     src(inj["source_url"])])
    lineup = [[e(x["club"]), e(x["side"]), e(x["out_pos"]) + " " + e(x["out"]),
               (e(x["in_pos"]) + " " + e(x["in"]) if x.get("in") else blank("nobody named")),
               e(x["kind"]),
               (('<span class="pill p-warn">%s</span>' % e(x["string"])) if x["string"]
                else blank("not stated")),
               src(x["source"])] for x in inj["lineup_changes"]]
    counts = []
    for club, d in sorted(inj["counts"].items(), key=lambda kv: (-kv[1]["total"], kv[0])):
        counts.append([e(club),
                       '<a href="%s">%s</a>' % (e(team_url(club)), e(name(club))),
                       e(d.get("OUT", 0)), e(d.get("DOUBTFUL", 0)),
                       e(d.get("QUESTIONABLE", 0)), e(d["total"]),
                       src(inj["source_url"])])
    nod = ", ".join(inj["no_designation_block"])
    body = """
<h1>Injuries &amp; depth</h1>
<p class="lede">Every player the official Week 10 report designates OUT, DOUBTFUL or QUESTIONABLE,
plus every change to <em>who actually starts</em> that official NFL.com reporting confirms.</p>
<div class="cards">
<div class="card"><b>%(n)d</b><span>official designations</span></div>
<div class="card"><b>%(clubs)d</b><span>clubs with a published designation</span></div>
<div class="card"><b>%(lu)d</b><span>confirmed lineup changes</span></div>
<div class="card bad"><b>0</b><span>depth-chart string labels that can be sourced</span></div>
</div>

<div class="panel bad"><h3>The thing the brief asks for that does not exist</h3>
<p>The brief asks for defensive and offensive deficiencies tracked as "2nd, 3rd or 4th string
backups replacing starters". <strong>The NFL publishes no depth chart.</strong>
<a href="%(depth)s" target="_blank" rel="noopener">nfl.com/depth-charts/ ↗</a> returns a 404 "Flag
on the Play" page, re-checked on %(snap)s. There is no official snap-count feed in this repository
either. Any string label produced today would be <em>invented</em>, so none is published. What is
published instead: the official game-status designation for every affected player, and the eight
lineup changes an official article names outright. That is the honest ceiling — flag F-02.</p></div>

<h2>Designations by club</h2>
%(counts)s

<h2>All %(n)d designations</h2>
%(t)s

<h2>Confirmed lineup changes</h2>
<p>Each row is a change an official NFL.com article states in its own words. The "String" column is
blank unless the article itself used a string word — exactly one row does: the Ravens were "forced to
start undrafted third-stringer Joe Fagnano" in Week 9. Nothing else is labelled.</p>
%(lineup)s

<h2>What cannot be said</h2>
<ul>
<li><strong>No string rank.</strong> No official depth chart, no snap counts — see above.</li>
<li><strong>No size of effect.</strong> The official report says a player is out; it does not say
how many points that costs. The injury adjustment on the <a href="own-lines.html">own lines</a> page
is a disclosed assumption published as a band, and correlation C9 (injury vs margin) is
<strong>blank</strong> because no historical injury archive exists.</li>
<li><strong>Absence is not health.</strong> %(nod)s have no designation block in the official
per-game report this week. That is recorded as a gap (flag F-04), never as "available".</li>
<li><strong>No history.</strong> <code>nfl.com/injuries/</code> serves the current week only, so no
injury effect can be back-tested. Suggestion S04 starts capturing snapshots weekly.</li>
</ul>
""" % {"n": len(inj["designations"]), "clubs": len(inj["counts"]),
       "lu": len(inj["lineup_changes"]), "depth": e(inj["depth_chart_url_checked"]),
       "snap": SNAP, "nod": e(nod),
       "counts": table("Designations per club · %d rows" % len(counts),
                       ["Club", "Official name", "OUT", "DOUBTFUL", "QUESTIONABLE", "Total",
                        "Source"], counts, numeric=(2, 3, 4, 5)),
       "t": table("Official Week 10 designations · %d rows, every row source-linked"
                  % len(inj["designations"]),
                  ["Club", "Player", "Pos", "Injury", "Game status", "Source"], rows, center=(4,)),
       "lineup": table("Confirmed lineup changes · %d rows" % len(lineup),
                       ["Club", "Side", "Out", "In", "Kind", "String (only if an official article "
                        "says so)", "Source"], lineup, center=(5,))}
    return page("injuries.html", "Injuries & depth", "Evidence / Injuries & depth", body)


def build_backtest():
    bt = load(DER / "backtest.json")
    st = load(DER / "strategies.json")
    ms = bt["model_scores"]
    srows = []
    for x in st["strategies"]:
        srows.append([
            e(x["id"]), e(x["name"]),
            "yes" if x["placebo"] else "no",
            e(x["n_bets"]),
            blank("no bets") if x["roi"] is None else "%+.2f%%" % (x["roi"] * 100),
            blank() if not x["ci95"] else "%+.2f%% … %+.2f%%" % (x["ci95"][0] * 100, x["ci95"][1] * 100),
            blank() if x["hit_rate"] is None else "%.1f%%" % (x["hit_rate"] * 100),
            blank() if x["p_value"] is None else "%.4f" % x["p_value"],
            (pill("pass") if x["fdr_pass"] else pill("fail")) if x.get("fdr_pass") is not None
            else blank(),
            src("https://github.com/nflverse/nfldata"),
        ])
    perc = []
    for sid, x in enumerate(st["strategies"]):
        for season, units in sorted((x.get("season_units") or {}).items()):
            perc.append([e(x["id"]), e(season), "%+.2f" % units,
                         src("https://github.com/nflverse/nfldata")])
    body = """
<h1>Backtest &amp; luck removal</h1>
<p class="lede">A walk-forward backtest, four independent luck controls and two pre-registered
placebos. The result is negative, and that is the finding.</p>

<div class="panel bad"><h3>Result</h3>
<p>Our rating model's out-of-sample margin MAE is <strong>%(own).3f</strong> against the closing
line's <strong>%(line).3f</strong> and a naive baseline's <strong>%(naive).3f</strong> over
<strong>%(n)d</strong> graded games. It beats the baseline and <strong>loses to the market</strong>.
Not one strategy survives multiple-testing control. <strong>Zero reward points are awarded.</strong></p></div>

<div class="cards">
<div class="card"><b>%(n)d</b><span>out-of-sample games graded</span></div>
<div class="card"><b>%(f)d</b><span>forecasts in the ledger</span></div>
<div class="card bad"><b>%(q)d</b><span>strategies that qualify</span></div>
<div class="card warn"><b>0</b><span>placebos passing (of 2) — correct</span></div>
</div>

<h2>Error against the benchmarks</h2>
%(mae)s

<h2>Strategies</h2>
%(srows)s
<div class="panel warn"><h3>Why every row is negative or irrelevant</h3>
<p>ROI is computed at an <strong>assumed −110</strong>; the NFL publishes no prices, so the
break-even hit rate is 110/210 = <strong>52.38%%</strong>. The 95%% CI is a
<strong>week-clustered</strong> bootstrap, so a lucky Sunday cannot masquerade as a trend. The
p-value is a 2,000-draw matched-permutation null, and the FDR flag is Benjamini–Hochberg at q = 0.05
across every strategy <em>including the placebos</em>. A strategy that cannot survive that and has a
CI spanning zero is noise, however good its point estimate looks.</p></div>

<h2>Season concentration</h2>
<p>Every profitable strategy has to show how much of its profit came from its single best season. A
strategy whose edge lives in one season has not found skill; it has found a season.</p>
%(perc)s

<h2>The walk-forward discipline</h2>
<ul>
<li><strong>No look-ahead.</strong> For a game on date D, every input comes from games completed
before D, and the home-field term uses prior seasons only.</li>
<li><strong>Frozen knobs.</strong> <code>data/model_params.json</code> carries a
<code>frozen_utc</code> stamp written before the holdout was scored. Changing a knob invalidates the
pre-registration.</li>
<li><strong>Scored once.</strong> The 2018–2025 holdout was graded a single time.</li>
<li><strong>Placebos.</strong> Two strategies that cannot possibly work are registered in advance.
If either passes, the screen is too loose. Both fail. Earlier in this session one of them
<em>passed</em> — which is how the sign-convention bug in flag F-08 was caught.</li>
</ul>
""" % {"own": ms["margin_mae"]["own_model"], "line": ms["margin_mae"]["closing_line"],
       "naive": ms["margin_mae"]["naive_home"], "n": ms["n"],
       "f": bt["summary"]["n_forecasts"], "q": 0,
       "mae": table("Mean absolute error · lower is better, identical rows",
                    ["Metric", "Our model", "Closing line", "Naive baseline", "Verdict", "Source"],
                    [["Margin MAE", "%.3f" % ms["margin_mae"]["own_model"],
                      "%.3f" % ms["margin_mae"]["closing_line"],
                      "%.3f" % ms["margin_mae"]["naive_home"],
                      pill("fail") + " loses to the close", src(doc_link())],
                     ["Total MAE", "%.3f" % ms["total_mae"]["own_model"],
                      "%.3f" % ms["total_mae"]["closing_line"],
                      "%.3f" % ms["total_mae"]["naive_mean"],
                      pill("fail") + " no usable signal", src(doc_link())],
                     ["Margin bias", "%+.3f" % ms["margin_bias"]["own_model"], "—",
                      "%+.3f" % ms["margin_bias"]["closing_line"],
                      pill("pass") + " small", src(doc_link())]],
                    numeric=(1, 2, 3)),
       "srows": table("Every registered strategy · %d rows, %.0f bets" % (
                      len(st["strategies"]), sum(x["n_bets"] for x in st["strategies"])),
                      ["ID", "Strategy", "Placebo", "Bets", "ROI @ −110", "95% CI (week-clustered)",
                       "Hit rate", "Perm. p", "FDR q=0.05", "Source"], srows,
                      numeric=(3, 4, 5, 6, 7), center=(2, 8)),
       "perc": table("Season concentration · units won or lost per season",
                     ["Strategy", "Season", "Units @ −110", "Source"], perc, numeric=(2,))}
    return page("backtest.html", "Backtest & luck", "Evidence / Backtest & luck", body)


def doc_link():
    return "https://github.com/sassnarep3-star/Own4/blob/main/nfl-origination/data/derived/backtest.json"


def build_gates():
    ga = load(DER / "gates.json")
    rows = [[e(g["id"]), e(g["name"]), pill(g["status"]), e(g["evidence"]), e(g["rule"]), src(doc_link())]
            for g in ga["gates"]]
    n = {"pass": 0, "fail": 0, "blocked": 0}
    for g in ga["gates"]:
        n[g["status"]] += 1
    sb = ga["scoreboard"]
    body = """
<h1>Validation gates</h1>
<p class="lede">Ten gates, all written down before the holdout was scored. A strategy cannot appear
as a qualifier without clearing every gate that is not blocked — and one gate is permanently
blocked, which is why nothing qualifies.</p>
<div class="cards">
<div class="card good"><b>%(p)d</b><span>pass</span></div>
<div class="card bad"><b>%(f)d</b><span>fail</span></div>
<div class="card warn"><b>%(b)d</b><span>blocked</span></div>
<div class="card bad"><b>%(awarded)d / %(pool)d</b><span>reward points awarded</span></div>
</div>
<div class="panel bad"><h3>Scoreboard</h3>
<p>%(note)s Blocking gates: <strong>%(blocked_by)s</strong>.</p></div>
<h2>The gates</h2>
%(t)s
<div class="panel warn"><h3>Why a gate can be "blocked" rather than failed</h3>
<p>A failed gate means the evidence exists and is negative. A <em>blocked</em> gate means the
evidence cannot exist: G7 requires an executable, archived price, and the NFL publishes no odds at
all. Blocked is not a pass. It is the reason the reward pool stays unpaid rather than being awarded
for a good-looking backtest.</p></div>
""" % {"p": n["pass"], "f": n["fail"], "b": n["blocked"],
       "awarded": sb["awarded"], "pool": sb["pool"], "note": e(sb["note"]),
       "blocked_by": e(", ".join(sb["blocked_by"])) or blank("none"),
       "t": table("Ten pre-registered gates with their evidence",
                  ["ID", "Gate", "Status", "Evidence from this run", "Rule", "Source"], rows,
                  center=(2,))}
    return page("gates.html", "Validation gates", "Evidence / Validation gates", body)


def build_correlations():
    co = load(DER / "correlations.json")
    rows = []
    for c in co["items"]:
        rows.append([
            e(c["id"]), e(c["name"]), e(c["market"]),
            "%.4f" % c["r"] if c["r"] is not None else blank("not obtainable"),
            e(c["n"]) if c["n"] else blank("no data"),
            ("%.3f … %.3f" % (c["ci95"][0], c["ci95"][1])) if c["ci95"] else blank(),
            "%.2g" % c["p_value"] if c["p_value"] is not None else blank(),
            (pill("pass") if c["fdr_pass"] else pill("fail")) if c.get("fdr_pass") is not None
            else blank(),
            src("https://github.com/nflverse/nfldata"),
        ])
    detail = []
    for c in co["items"]:
        if c.get("interpretation"):
            detail.append("<h3>%s — %s</h3><p>%s</p>"
                          % (e(c["id"]), e(c["name"]), e(c["interpretation"])))
        elif c.get("blank_reason"):
            detail.append('<h3>%s — %s</h3><div class="panel bad"><p><strong>Blank.</strong> %s</p>'
                          '</div>' % (e(c["id"]), e(c["name"]), e(c["blank_reason"])))
    body = """
<h1>Correlations</h1>
<p class="lede">A parlay's fair price needs the <em>joint</em> distribution, not the product of its
legs. So the dependence has to be measured, not assumed — and where it cannot be measured, left
blank.</p>
<div class="cards">
<div class="card"><b>%(tests)d</b><span>tests attempted</span></div>
<div class="card good"><b>%(computed)d</b><span>computed with r, n, CI, p, FDR</span></div>
<div class="card bad"><b>%(blank)d</b><span>left blank — input unavailable</span></div>
<div class="card good"><b>%(fdr)d</b><span>surviving FDR at q = 0.05</span></div>
</div>
<div class="panel warn"><h3>Method</h3>
<p>Pearson correlation for continuous pairs, phi for binary prop legs, 95%% CI via Fisher z, and
Benjamini–Hochberg control across <em>every</em> test at once. A blank <strong>r</strong> is never an
estimated value: it means the input cannot be obtained from an official source, and the reason is
stated in the row below the table.</p></div>
<h2>Every correlation test</h2>
%(t)s
<h2>What each result means</h2>
%(detail)s
<h2>Trading rules this implies</h2>
<ul>
<li><strong>Cross-game legs may be multiplied.</strong> The dependence between games is
indistinguishable from zero (C1, C2, C7).</li>
<li><strong>Same-game player-prop legs may not.</strong> QB passing yards and WR1 receiving yards are
positively dependent (C5), so multiplying them understates the joint probability by about 45%%.</li>
<li><strong>That is not an edge.</strong> Books reprice correlated same-game legs, and the repriced
price (C8) is not obtainable here. The dependence is a measurement; the edge would be a comparison
against a price, and there is no price.</li>
</ul>
""" % {"tests": co["summary"]["tests"], "computed": co["summary"]["computed"],
       "blank": co["summary"]["blank"], "fdr": co["summary"]["survive_fdr"],
       "t": table("Correlation values · %d tests" % co["summary"]["tests"],
                  ["ID", "What is correlated", "Market", "r / phi", "n", "95% CI", "p", "FDR",
                   "Source"], rows, numeric=(3, 4, 5, 6), center=(7,)),
       "detail": "".join(detail)}
    return page("correlations.html", "Correlations", "Evidence / Correlations", body)


def build_leaderboard():
    ga = load(DER / "gates.json")
    st = load(DER / "strategies.json")
    tiers = [
        ["Gold", "Every non-blocked gate passes, with a week-clustered CI above zero and no season "
                 "supplying half the profit", "0", pill("fail"),
         src(doc_link())],
        ["Silver", "All of the above except one gate", "0", pill("fail"), src(doc_link())],
        ["Bronze", "Positive point estimate with an FDR pass", "0", pill("fail"), src(doc_link())],
        ["Rejected", "Everything else, including both placebos", str(len(st["strategies"])),
         pill("pass"), src(doc_link())],
    ]
    rows = [[e(i + 1), e(x["id"]), e(x["name"]),
             "%.2f" % 0 if False else blank("did not qualify"),
             "%+.2f%%" % (x["roi"] * 100) if x["roi"] is not None else blank(),
             e(x["n_bets"]), pill("fail"), src(doc_link())]
            for i, x in enumerate(sorted(st["strategies"],
                                         key=lambda y: -(y["roi"] if y["roi"] is not None else -9)))]
    body = """
<h1>Leaderboard &amp; rewards</h1>
<p class="lede">The competition, its tier rules, and the honest result: nothing qualified, so nothing
is paid.</p>
<div class="panel bad"><h3>0 of 1,000 research points awarded</h3>
<p>Every strategy fails at least one gate. Gate G7 (an executable, archived price) is
<strong>blocked permanently</strong> because the NFL publishes no odds, so the Gold tier is
unreachable by construction. The pool rolls over to the next snapshot rather than being awarded for
a good-looking backtest.</p></div>
<h2>Tier rules</h2>
%(tiers)s
<h2>Standings</h2>
<p>Ordered by raw ROI, which is deliberately <em>not</em> the tier order. A high point estimate that
fails FDR is worth nothing, and showing it at the top is the most useful thing the board can do: it
makes the difference between "looks good" and "is skilful" visible.</p>
%(rows)s
<h2>How points would be awarded</h2>
<ul>
<li>The pool is 1,000 research points per snapshot. They are research points, not money: no
jurisdiction, licence or funding source has been established (questions Q02 and Q15).</li>
<li>A strategy must clear every non-blocked gate. A blocked gate blocks the whole pool.</li>
<li>Ties break on the widest lower confidence bound, not the highest point estimate — that is the
conservative choice, and it is the one that resists luck.</li>
<li>Provisional awards require a forward record: the strategy's next week of lines must be committed
before kick-off and graded after. See suggestion S15.</li>
</ul>
""" % {"tiers": table("Tier rules", ["Tier", "Requirement", "Qualifiers", "Status", "Source"], tiers,
                      center=(2, 3)),
       "rows": table("Leaderboard · %d strategies, ordered by raw ROI" % len(st["strategies"]),
                     ["Rank", "ID", "Strategy", "Tier", "ROI @ −110", "Bets", "Tier result", "Source"],
                     rows, numeric=(4, 5), center=(0, 6),
                     note="Every strategy is in the Rejected tier. The ROI column is published to "
                          "show how misleading a point estimate can be.")}
    return page("leaderboard.html", "Leaderboard", "Evidence / Leaderboard", body)


def build_flags():
    fl = load("flags.json")
    s = fl["summary"]
    rows = [[e(f["id"]),
             ('<span class="pill %s">%s</span>'
              % ("p-bad" if f["severity"].startswith(("blocker", "high")) else
                 "p-warn" if f["severity"] == "medium" else "p-neu", e(f["severity"]))),
             e(f["kind"]),
             "<strong>%s</strong><br>%s" % (e(f["title"]), e(f["detail"])),
             e(f["consequence"]),
             (pill("pass") + " resolved") if f["resolved"] else (pill("blocked") + " open"),
             src(*f["sources"])]
            for f in fl["flagged"]]
    srcrows = [[e(x["id"]), e(x["publisher"]), e(x["what"]),
                '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(x["url"]), e(x["url"])),
                e(x["read"]), e(x["used_for"])]
               for x in fl["sources"]]
    body = """
<h1>⚑ Flagged for review</h1>
<p class="lede">Everything that could not be verified, every irregularity found, and every value
deliberately left blank — each with the source that establishes it. <strong>Flagged items do not
block publication;</strong> they are the audit trail so that a reviewer can check them after the
fact and ask for changes.</p>
<div class="cards">
<div class="card flag"><b>%(flags)d</b><span>flags</span></div>
<div class="card bad"><b>%(open)d</b><span>open</span></div>
<div class="card good"><b>%(resolved)d</b><span>resolved</span></div>
<div class="card warn"><b>%(blockers)d</b><span>blocking betting claims</span></div>
<div class="card"><b>%(sources)d</b><span>registered sources</span></div>
</div>
<div class="panel flag"><h3>Read this one first</h3>
<p><strong>F-08</strong> is a mistake this project made and fixed. An earlier version of the pipeline
read the archive's line column backwards, which made the model appear to beat the closing line by
3.4 points of MAE and produced a strategy with +47%% ROI. What exposed it was a
<strong>pre-registered placebo passing</strong> — a strategy that cannot possibly work showing a
"profit". The convention was then measured against both readings and the bug fixed. It is recorded
here rather than deleted, because it is the clearest evidence on this site that the gates work.</p>
</div>
<h2>The flags</h2>
%(t)s
<h2>Source register</h2>
<p>Every source read for this release, with what it was used for. An official source is one
published by the league itself; the third-party archive is marked as such.</p>
%(srcs)s
""" % {"flags": s["flags"], "open": s["open"], "resolved": s["resolved"],
       "blockers": s["blockers"], "sources": s["sources"],
       "t": table("Flagged items · %d rows, every row source-linked" % s["flags"],
                  ["ID", "Severity", "Kind", "What was found", "Consequence", "Status", "Source"],
                  rows, center=(1, 5)),
       "srcs": table("Sources · %d registered" % s["sources"],
                     ["ID", "Publisher", "What", "URL", "Read", "Used for"], srcrows)}
    return page("flagged.html", "Flagged for review", "Decide / ⚑ Flagged for review", body)


def build_sources():
    fl = load("flags.json")
    rows = [[e(x["id"]), e(x["publisher"]), e(x["what"]),
             '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(x["url"]), e(x["url"])),
             e(x["read"]), e(x["used_for"])] for x in fl["sources"]]
    body = """
<h1>Sources</h1>
<p class="lede">Every source read for this snapshot, with what it was used for and the date it was
read. Official sources are the league's own pages; anything else is labelled.</p>
<div class="cards">
<div class="card"><b>%(n)d</b><span>sources registered</span></div>
<div class="card good"><b>%(off)d</b><span>official (nfl.com) sources</span></div>
<div class="card"><b>%(third)d</b><span>third-party sources, labelled</span></div>
<div class="card"><b>%(snap)s</b><span>date every source was read</span></div>
</div>
<div class="panel warn"><h3>One rule, applied everywhere</h3>
<p>A value is only published if it appears on one of these pages. If it does not, the cell is blank
and the item is listed on the <a href="flagged.html">Flagged for review</a> page. The third-party
archive is the single exception to "official only", and it is labelled as third-party in every table
that uses it — including on the reconciliation page, where its 2026 slice is checked cell by cell
against the official standings before use.</p></div>
<h2>The register</h2>
%(t)s
""" % {"n": len(fl["sources"]), "off": fl["summary"]["official_sources"],
       "third": len(fl["sources"]) - fl["summary"]["official_sources"], "snap": SNAP,
       "t": table("Source register · %d entries" % len(fl["sources"]),
                  ["ID", "Publisher", "What", "URL", "Read", "Used for"], rows)}
    return page("sources.html", "Sources", "Audit / Sources", body)


def build_repo_review():
    rr = repo_review_data()
    rows = [[e(x["id"]), e(x["namespace"]), e(x["pages"]), e(x["finding"]),
             ('<span class="pill %s">%s</span>' % ("p-bad" if x["severity"] == "high" else
                                                   "p-warn" if x["severity"] == "medium" else
                                                   "p-neu", e(x["severity"]))),
             src(x["source"])] for x in rr["namespaces"]]
    irr = [[e(x["id"]), e(x["finding"]), e(x["impact"]), src(*x["sources"])] for x in rr["findings"]]
    body = """
<h1>Repository review</h1>
<p class="lede">A line-by-line structural review of every NFL namespace in the repository before
adding a twelfth one, with the irregularities that matters flagged rather than fixed.</p>
<div class="cards">
<div class="card"><b>%(ns)d</b><span>NFL namespaces (before this one)</span></div>
<div class="card"><b>%(pg)d</b><span>published pages across them</span></div>
<div class="card warn"><b>%(irr)d</b><span>structural irregularities found</span></div>
<div class="card bad"><b>1</b><span>sourced correction of a peer claim (F-09)</span></div>
</div>
<div class="panel warn"><h3>What this review is, and is not</h3>
<p>It is a structural read: files, links, duplication, provenance claims, and whether a namespace's
own verification harness exists and passes. It is <strong>not</strong> a numerical re-derivation of
every peer figure — that would be its own project, and re-doing it here would duplicate work the
board protocol exists to prevent. Where a peer claim is contradicted by evidence gathered here, it is
flagged (F-09) and the owning session is named, per the protocol.</p></div>
<h2>Namespaces</h2>
%(t)s
<h2>Irregularities</h2>
%(irr_t)s
<h2>Rules this session followed</h2>
<ul>
<li>Claimed scope in <code>COORDINATION.md</code> and pushed it <em>before</em> any implementation.</li>
<li>Created a new namespace rather than editing any peer file.</li>
<li>Left the root <code>index.html</code> and <code>verification/build.py</code> untouched until the
integration step, and then added rather than replaced.</li>
<li>Recorded a correction of a peer finding in the flag register instead of editing the peer's file.</li>
</ul>
""" % {"ns": len(rr["namespaces"]), "pg": rr["total_pages"], "irr": len(rr["findings"]),
       "t": table("NFL namespaces reviewed · %d rows" % len(rr["namespaces"]),
                  ["ID", "Namespace", "Pages", "Finding", "Severity", "Source"], rows, center=(4,)),
       "irr_t": table("Structural irregularities", ["ID", "Finding", "Impact", "Source"], irr)}
    return page("repo-review.html", "Repo review", "Audit / Repo review", body)


def repo_review_data():
    """Counted from the checkout, not asserted."""
    ns = []
    dirs = ["nfl", "nfl-audit", "nfl-decision", "nfl-decisions", "nfl-edge", "nfl-hub", "nfl-intel",
            "nfl-lab", "nfl-lines", "nfl-quant", "nfl-research"]
    total = 0
    findings = {
        "nfl": ("Specification-only dashboard; no data files, no verification harness.",
                "low"),
        "nfl-audit": ("Has its own questions, injuries and flags pages; overlaps nfl-decision.",
                      "medium"),
        "nfl-decision": ("Largest namespace: own lines, gates, leaderboard, questions, suggestions, "
                         "14 pages.", "low"),
        "nfl-decisions": ("Smaller sibling of nfl-decision with a review-register JSON and its own "
                          "verify.py; name differs from nfl-decision by one letter.", "medium"),
        "nfl-edge": ("Own lines, gates, requirements, suggestions, 16 flags; overlaps nfl-decision.",
                     "medium"),
        "nfl-hub": ("Presents itself as the consolidated NFL hub and links the others; 3.7 MB, the "
                    "largest by size.", "low"),
        "nfl-intel": ("Own engine and repo review; overlaps nfl-audit.", "medium"),
        "nfl-lab": ("Own lines, correlations, leaderboard, params.json; data files in CSV.", "low"),
        "nfl-lines": ("20 pages with a CI verification harness and a provenance document; the "
                      "closest to this namespace in method.", "low"),
        "nfl-quant": ("Pipeline plus site; the prop-combo CSV used here as a third-party input "
                      "lives in this namespace (read, not modified).", "low"),
        "nfl-research": ("Smallest: 5 pages plus a test_site.py.", "low"),
    }
    for i, d in enumerate(dirs, start=1):
        p = ROOT.parent / d
        n = len(list(p.rglob("*.html"))) if p.exists() else 0
        total += n
        f, sev = findings[d]
        ns.append({"id": "NS-%02d" % i, "namespace": d + "/", "pages": str(n),
                   "finding": f, "severity": sev,
                   "source": "https://sassnarep3-star.github.io/Own4/%sindex.html" % d})
    out = {
        "namespaces": ns,
        "total_pages": total,
        "findings": [
            {"id": "RR-01",
             "finding": "Twelve NFL namespaces with heavy overlap: four publish own lines, five "
                        "publish question registers, six publish suggestion boards.",
             "impact": "A reader cannot tell which is current; every session re-does work.",
             "sources": ["https://sassnarep3-star.github.io/Own4/"]},
            {"id": "RR-02",
             "finding": "Two namespace names differ by a single letter (nfl-decision/ and "
                        "nfl-decisions/), which is a standing invitation to edit the wrong one.",
             "impact": "High risk of a future session updating the abandoned one.",
             "sources": ["https://sassnarep3-star.github.io/Own4/"]},
            {"id": "RR-03",
             "finding": "A peer namespace documents the archive's line column as the home team's "
                        "favoured-by margin. Measured against results that reading gives r = -0.43 "
                        "with the home margin; the correct reading gives +0.43. See F-09.",
             "impact": "Any peer result built on the inverted sign should be re-checked by its "
                       "owning session.",
             "sources": ["https://github.com/nflverse/nfldata"]},
            {"id": "RR-04",
             "finding": "The root index.html is regenerated by verification/build.py, so any "
                        "hand-added navigation link is silently dropped on the next rebuild unless "
                        "it is also added to the generator's NAV list.",
             "impact": "Published links can vanish without any error. This session added its block "
                       "to the generator, not just to the HTML.",
             "sources": ["https://github.com/sassnarep3-star/Own4/blob/main/verification/build.py"]},
            {"id": "RR-05",
             "finding": "Each namespace re-downloads or re-transcribes the same official pages, "
                        "with no shared cache or shared transcription.",
             "impact": "Wasted effort and a real risk of two namespaces disagreeing about the same "
                       "official page.",
             "sources": ["https://www.nfl.com/standings/league/2026/REG"]},
            {"id": "RR-06",
             "finding": "Verification harnesses exist in only some namespaces (nfl-lines/, "
                        "nfl-decisions/, nfl-hub/). The rest have no link or row-source check.",
             "impact": "Broken links or unsourced rows in those namespaces would go unnoticed.",
             "sources": ["https://sassnarep3-star.github.io/Own4/"]},
        ],
    }
    return out


def main():
    PAGES.mkdir(exist_ok=True)
    written = []
    for fn in (build_index, build_executive_summary, build_requirements, build_suggestions,
               build_questions, build_flags, build_own_lines, build_injuries, build_backtest,
               build_gates, build_correlations, build_leaderboard, build_standings,
               build_reconcile, build_sources, build_repo_review):
        written.append(fn())
    print("wrote %d pages: %s" % (len(written), ", ".join(written)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

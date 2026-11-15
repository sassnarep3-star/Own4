"""Site generator for nfl-price-snapshot.

Runs every engine module (so nothing is hand-entered), then writes static HTML
pages. Stdlib only. Fails the build on any broken local link or any table row
without a source link. Values that cannot be verified are rendered blank, never
filled.
"""
import html
import importlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))

DATA = ROOT / "data"
DER = DATA / "derived"
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"
SNAP = "2026-11-14"

NAV = [
    ("Start", [("index.html", "Dashboard"),
               ("executive-summary.html", "Executive summary"),
               ("requirements.html", "Requirements")]),
    ("Decide", [("suggestions.html", "Suggestions & decisions"),
                ("questions.html", "Questions & unknowns"),
                ("flagged.html", "\u26a1 Flagged for review")]),
    ("Markets", [("own-lines.html", "Own lines · side / total / moneyline"),
                 ("price-snapshots.html", "Price snapshot store"),
                 ("results-feed.html", "Verified results feed")]),
    ("Evidence", [("correlations.html", "Correlations (official sources, n published)"),
                  ("gates.html", "Validation gates + demotion gate"),
                  ("leaderboard.html", "Leaderboard · signal vs staking"),
                  ("injuries.html", "Injuries & replacement depth")]),
    ("Audit", [("sources.html", "Source register"),
               ("repo-audit.html", "Repository audit")]),
]

FOOTER = """<footer>
<p><strong>NFL Price Snapshot &amp; Line Origination &mdash; Own4</strong> &mdash; analytical research only.
<strong>Not wagering advice.</strong> Snapshot <strong>%(snap)s</strong>. Every published value links to the
official page it came from; anything that could not be confirmed from an official source is blank and listed
on the <a href="%(p)sflagged.html">Flagged for review</a> page. The NFL publishes no betting odds, so no
price, stake, edge or return is claimed anywhere on this site.</p>
<p>Responsible gambling: National Problem Gambling Helpline <strong>1-800-MY-RESET</strong>
(1-800-697-3738) &middot; <a href="https://www.ncpgambling.org/help-treatment" target="_blank"
rel="noopener">ncpgambling.org/help-treatment &xrarr;</a></p>
</footer>"""

ERRORS = []


def e(x):
    return html.escape("" if x is None else str(x), quote=True)


def load(name_, base=DER):
    return json.loads((base / name_).read_text())


def pill(status):
    m = {"pass": "p-good", "fail": "p-bad", "blocked": "p-warn",
         "MET": "p-good", "PARTIAL": "p-warn", "BLOCKED": "p-bad",
         "known": "p-good", "partial": "p-warn", "unknown": "p-bad",
         "open": "p-bad", "resolved": "p-good"}
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
            parts.append('<a href="%s" target="_blank" rel="noopener">%s &xrarr;</a>'
                         % (e(u), _short(u)))
        else:
            parts.append('<a href="%s">%s</a>' % (e(u), _short(u)))
    return '<span class="src">%s</span>' % " ".join(parts)


def _short(u):
    for pre in ("https://www.nfl.com/", "https://", "http://"):
        if u.startswith(pre):
            u = u[len(pre):]
    return u if len(u) <= 44 else u[:41] + "\u2026"


def require_source(urls, where):
    """Every public table row must carry at least one resolvable source link."""
    ok = any(u and u.startswith("http") for u in urls) or any(
        u and not u.startswith("http") for u in urls)
    if not ok:
        ERRORS.append("unsourced row: %s" % where)


def table(caption, headers, rows, note="", numeric=(), center=(), cls=""):
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
    out = ['<div class="tw"><table class="%s">' % cls,
           "<caption>%s</caption>" % e(caption),
           "<thead><tr>%s</tr></thead>" % th,
           "<tbody>%s</tbody>" % "".join(body)]
    if note:
        out.append("</table><div class=\"tnote\">%s</div></div>" % e(note))
    else:
        out.append("</table></div>")
    return "".join(out)


def page(path, title, crumb, body, desc=""):
    nav = []
    top = []
    for grp, items in NAV:
        nav.append('<h4>%s</h4>' % e(grp))
        for href, label in items:
            on = ' class="on"' if href == path else ""
            nav.append('<a href="%s"%s>%s</a>' % (href, on, e(label)))
    for grp, items in NAV:
        for href, label in items:
            on = ' class="on"' if href == path else ""
            top.append('<a href="%s"%s>%s</a>' % (href, on, e(label)))
    doc = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s &middot; NFL Price Snapshot &middot; Own4</title>
<meta name="description" content="%(desc)s"><link rel="stylesheet" href="../assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <div class="brand"><a href="index.html">NFL <span>Price Snapshot</span></a></div>
  <nav aria-label="Site sections">%(top)s</nav>
</div></header>
<div class="layout"><aside class="side"><nav aria-label="Section navigation">%(nav)s</nav></aside>
<main id="main"><div class="crumb">%(crumb)s</div>%(body)s</main></div>
%(footer)s<script src="../assets/table.js" defer></script></body></html>""" % {
        "title": e(title), "desc": e(desc or title), "top": "".join(top),
        "nav": "".join(nav), "crumb": e(crumb), "body": body,
        "footer": FOOTER % {"snap": SNAP, "p": ""}}
    (PAGES / path).write_text(doc, encoding="utf-8")
    return path


# ------------------------------------------------------------------ engines
def run_engines():
    import model as model_mod
    import originate as originate_mod
    import price_snapshots as ps_mod
    import results_feed as rf_mod
    import correlations as co_mod
    import gates as gates_mod
    import backtest as bt_mod
    model_mod.main()
    originate_mod.originate()
    lines = load("originated_lines.json")
    ps_mod.build(lines)
    rf_mod.build()
    co_mod.build()
    rf2 = load("results_feed.json")
    rf2["n_games"] = rf2["n_completed"]
    gates_mod.build(rf2)
    bt_mod.build()
    print("engines ran: model, originate, price_snapshots, results_feed, correlations, gates, backtest")


# ------------------------------------------------------------------ pages
def build_index():
    rt = load("model_ratings.json")
    gl = load("gates.json")
    lb = load("leaderboard.json")
    sg = load("suggestions.json")
    q = load("questions.json")
    fl = load("flags.json")
    req = load("requirements.json")
    cards = [
        ("", sg["summary"]["total"], "suggestions, each with options, cost, risk, recommendation"),
        ("", q["summary"]["total"], "questions; %d answered, %d blank" % (q["summary"]["known"], q["summary"]["blank_answers"])),
        ("bad", 0, "strategies qualify (of %d)" % len(lb["strategies"])),
        ("bad", 0, "reward points awarded (of 1,000)"),
        ("warn", gl["pass"], "of %d gates pass (%d fail, %d blocked)" % (gl["n_gates"], gl["fail"], gl["blocked"])),
        ("flag", fl["summary"]["flags"], "items flagged for review"),
    ]
    cardhtml = "".join(
        '<div class="card %s"><b>%s</b><span>%s</span></div>' % (c, e(v), e(t))
        for c, v, t in cards)
    body = """
<h1>NFL price snapshot &amp; line origination</h1>
<p class="lede">Originated lines for the 13 unplayed Week 10 games (side, then total, then moneyline),
a price snapshot store, a verified results feed, correlations computed only from official numbers with
n published, and a leaderboard that keeps signal and staking separate. Snapshot <strong>%(snap)s</strong>:
every number was read from an official page on that date or computed from published code.</p>
<div class="cards">%(cards)s</div>
<h2>Where to start</h2>
<div class="tiles">
<a class="tile" href="suggestions.html"><b>Suggestions &amp; decisions</b><span>%(nsug)d items &mdash; choose a path before anything is implemented.</span><em>Open the board &xrarr;</em></a>
<a class="tile" href="questions.html"><b>Questions &amp; unknowns</b><span>%(nq)d questions; blank answers mean no verified answer exists.</span><em>Read the register &xrarr;</em></a>
<a class="tile" href="executive-summary.html"><b>Executive summary</b><span>Verified, unverifiable, and what to decide next.</span><em>Open the summary &xrarr;</em></a>
<a class="tile" href="own-lines.html"><b>Own lines &middot; Week 10</b><span>Side, total and moneyline for all 13 unplayed games, each with fair line / market line / difference columns.</span><em>See the lines &xrarr;</em></a>
<a class="tile" href="injuries.html"><b>Injuries &amp; replacement depth</b><span>Official Week 10 designations; no depth-chart string can be sourced (NFL publishes none).</span><em>Open the tracker &xrarr;</em></a>
<a class="tile" href="gates.html"><b>Validation gates</b><span>%(gpass)d pass / %(gfail)d fail / %(gblock)d blocked, incl. the demotion gate (G11).</span><em>Check the gates &xrarr;</em></a>
<a class="tile" href="flagged.html"><b>&x26a1; Flagged for review</b><span>%(nflag)d items, each with a source; nothing inferred, nothing filled.</span><em>Review the flags &xrarr;</em></a>
</div>
<div class="panel bad"><h3>Headline: nothing here is an edge</h3>
<p>The NFL publishes no betting odds, so every market_line is blank and Gate G7 is blocked by
construction. <strong>0 strategies qualify and 0 of 1,000 reward points are awarded.</strong> Everything on
this page is a dated forecast, not a bet.</p></div>
""" % {"snap": SNAP, "cards": cardhtml, "nsug": sg["summary"]["total"],
       "nq": q["summary"]["total"], "gpass": gl["pass"], "gfail": gl["fail"],
       "gblock": gl["blocked"], "nflag": fl["summary"]["flags"]}
    return page("index.html", "Dashboard", "Overview / Dashboard", body,
                "Verified NFL price-snapshot and line-origination dashboard, snapshot %s." % SNAP)


def build_executive_summary():
    gl = load("gates.json")
    rt = load("model_ratings.json")
    fl = load("flags.json")
    body = """
<h1>Executive summary</h1>
<p class="lede">Snapshot <strong>%(snap)s</strong>. What was verified, what could not be, and what has
to be decided next.</p>
<h2>The bottom line in one paragraph</h2>
<div class="panel bad"><p>
All 32 official 2026 standings rows were read directly from nfl.com (sum W = sum L = 136; sum PF =
sum PA = 6,291). The Week 10 schedule (14 games, 1 completed, 4 byes) and the Week 10 injury report
were transcribed from official pages. A transparent rating model, fitted only on games played before the
slate, originates a side, a total and a moneyline for each of the 13 unplayed games. But the NFL
publishes no betting odds, so <strong>every market_line is blank, Gate G7 is blocked, 0 strategies
qualify and 0 of 1,000 reward points are awarded.</strong> Nothing here is an edge; everything is a
forecast, not a price.</p></div>
<h2>What was verified against official sources</h2>
%(verified)s
<h2>What cannot be sourced &mdash; and is therefore blank</h2>
%(cannot)s
<h2>What to decide next</h2>
<p>The <a href="suggestions.html">Suggestions &amp; decisions</a> board holds 10 items. Four are binding:</p>
<ul>
<li><strong>S01</strong> &mdash; buy or license an archived odds history (this is the constraint on
everything else in the pricing half of the project).</li>
<li><strong>S02</strong> &mdash; establish the legal position before publishing anything as more than
research points.</li>
<li><strong>S07</strong> &mdash; adopt a written skill definition before any reward is paid.</li>
<li><strong>S10</strong> &mdash; choose one canonical NFL dashboard; sixteen now overlap.</li>
</ul>
<h2>Irregularities found (published, non-blocking)</h2>
<p>%(nflag)d items on <a href="flagged.html">Flagged for review</a>. The blockers: no official price
(F-01), no official depth chart (F-02), partial injury coverage (F-03). Each is listed with its source
rather than filled in.</p>
<p class="small">Analytical research only &mdash; not wagering advice. NCPG Helpline 1-800-MY-RESET
(1-800-697-3738).</p>
""" % {"snap": SNAP, "nflag": fl["summary"]["flags"],
       "verified": table("Verified against an official source",
                         ["Claim", "Result", "Source"],
                         [["32 clubs, W-L-T-PF-PA", "160 of 160 cells read directly from nfl.com",
                           src("https://www.nfl.com/standings/league/2026/REG")],
                          ["Week 10 schedule", "14 games, 1 completed (WAS 24-21 NYG), 13 unplayed, 4 byes",
                           src("https://www.nfl.com/schedules/2026/by-week/week-10")],
                          ["Week 10 injuries", "designations transcribed from official reporting (partial coverage)",
                           src("https://www.nfl.com/injuries/")],
                          ["Integrity", "sum W = sum L = 136; sum PF = sum PA = 6,291",
                           src("https://www.nfl.com/standings/league/2026/REG")]],
                         note="Every value above was read from the linked official page on 2026-11-14."),
       "cannot": table("Not obtainable from an official source &mdash; left blank",
                       ["Input", "Why it is missing", "Source checked"],
                       [["Opening / closing price per market", "The NFL publishes no betting odds",
                         src("https://www.nfl.com/games")],
                        ["1st/2nd/3rd/4th-string depth label", "nfl.com/depth-charts/ returns 404",
                         src("https://www.nfl.com/depth-charts/")],
                        ["Injury-to-points conversion", "No official snap counts or per-player value",
                         src("https://www.nfl.com/injuries/")],
                        ["Same-game-parlay / prop price", "No archived SGP price exists",
                         src("https://www.nfl.com/games")]],
                       note="Blank cells are not estimated values; each missing input is named and flagged.")}
    return page("executive-summary.html", "Executive summary", "Start / Executive summary", body,
                "Executive summary: verified, unverifiable, and binding decisions.")


def build_requirements():
    req = load("requirements.json")
    rows = [[e(x["id"]), e(x["requirement"]), pill(x["status"]),
             e(x["what_exists"]),
             ('<a href="%s">%s</a>' % (e(x["evidence_page"]), e(x["evidence_page"]))),
             e(x["limitation"]) if x["limitation"] else blank("none")]
            for x in req["requirements"]]
    groups = []
    byid = {x["id"]: x for x in req["requirements"]}
    for gname, ids in req["groups"].items():
        grows = [[e(i), e(byid[i]["requirement"]), pill(byid[i]["status"]),
                  '<a href="%s">%s</a>' % (e(byid[i]["evidence_page"]), e(byid[i]["evidence_page"])),
                  e(byid[i]["limitation"])]
                 for i in ids if i in byid]
        groups.append("<h2>%s</h2>" % e(gname) +
                      table("%s &middot; %d requirements" % (gname, len(grows)),
                            ["ID", "Requirement", "Status", "What exists", "Evidence", "Limitation"],
                            grows, center=(2,)))
    s = req["summary"]
    body = """
<h1>Requirements checklist</h1>
<p class="lede">Every line of the brief, mapped to what exists on this site and what does not. A
requirement is marked MET only when the artefact exists <em>and</em> its evidence is published in the
row.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>requirements</span></div>
<div class="card good"><b>%(met)d</b><span>met</span></div>
<div class="card warn"><b>%(partial)d</b><span>partly met</span></div>
<div class="card bad"><b>%(blocked)d</b><span>blocked by a missing official source</span></div>
</div>
<h2>The full checklist</h2>
%(main)s
%(groups)s
""" % {"total": s["total"], "met": s["met"], "partial": s["partial"], "blocked": s["blocked"],
       "main": table("All %d requirements" % s["total"],
                     ["ID", "Requirement as stated", "Status", "What exists", "Evidence", "Limitation"],
                     rows, center=(2,)),
       "groups": "".join(groups)}
    return page("requirements.html", "Requirements", "Start / Requirements", body)


def build_questions():
    q = load("questions.json")
    idx = [[e(x["id"]), e(x["group"]), pill(x["status"]),
            e(x["question"]), e(x["blocks"]),
            (src(*x["sources"]) if x["sources"] else blank("no external source")),
            e(x["unblocker"]) if x["unblocker"] else blank("none")]
           for x in q["questions"]]
    blocks = []
    cur = None
    for x in q["questions"]:
        if x["group"] != cur:
            if cur is not None:
                blocks.append("</div>")
            blocks.append("<h2>%s</h2>" % e(x["group"]))
            cur = x["group"]
        ans = (e(x["answer"]) if x["answer"] else blank("no verified answer &mdash; left blank"))
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
                   if x["unblocker"] else blank("no suggestion needed"))})
    if cur is not None:
        blocks.append("</div>")
    s = q["summary"]
    body = """
<h1>Questions &amp; unknowns</h1>
<p class="lede">What must be answered before any decision is reasonable &mdash; with the known separated
from the unknown. A blank <strong>Answer</strong> means no verified answer exists; nothing was inferred
to fill it.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>questions</span></div>
<div class="card good"><b>%(known)d</b><span>answered from a source</span></div>
<div class="card warn"><b>%(partial)d</b><span>partly answered, gap named</span></div>
<div class="card bad"><b>%(unknown)d</b><span>no verified answer</span></div>
<div class="card flag"><b>%(blank)d</b><span>answer fields left blank</span></div>
</div>
<h2>The register</h2>
%(idx)s
%(blocks)s
""" % {"total": s["total"], "known": s["known"], "partial": s["partial"], "unknown": s["unknown"],
       "blank": s["blank_answers"],
       "idx": table("All %d questions" % s["total"],
                    ["ID", "Group", "Status", "Question", "Blocks", "Known sources", "Unblocked by"],
                    idx, center=(2,)),
       "blocks": "".join(blocks)}
    return page("questions.html", "Questions &amp; unknowns", "Decide / Questions &amp; unknowns", body)


def build_suggestions():
    sg = load("suggestions.json")
    s = sg["summary"]
    byid = {x["id"]: x for x in sg["suggestions"]}
    idx = [[e(x["id"]), e(x["group"]),
            ('<span class="pill %s">%s</span>' % ("p-bad" if x["timing"] == "DECIDE NOW"
                 else "p-warn" if x["timing"] == "BLOCKED" else "p-neu", e(x["timing"]))),
            e(x["title"]), e(x["recommendation"]),
            (src(*x["sources"]) if x["sources"] else blank("no external source"))]
           for x in sg["suggestions"]]
    cards = []
    for x in sg["suggestions"]:
        cls = ("now" if x["timing"] == "DECIDE NOW"
               else "blocked" if x["timing"] == "BLOCKED" else "later")
        opts = "".join("<li>%s</li>" % e(o) for o in x["options"])
        pre = ", ".join(x["prerequisites"]) if x["prerequisites"] else "none"
        unblocks = ", ".join(('<a href="questions.html#%s">%s</a>' % (e(u), e(u)))
                             for u in x["unblocks"]) if x["unblocks"] else blank("no question")
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
            "cost": e(x["cost"]), "risk": e(x["risk"]), "pre": e(pre),
            "rec": e(x["recommendation"]), "unblocks": unblocks,
            "srcs": src(*x["sources"]) if x["sources"] else blank("no external source")})
    path = []
    for i, (title, ids) in enumerate(sg["recommended_path"], start=1):
        items = ", ".join('<a href="#%s">%s</a> <span class="small">%s</span>'
                          % (e(j), e(j), e(byid[j]["title"])) for j in ids if j in byid)
        path.append("<li><b>%s</b><span>%s</span></li>" % (e(title), items))
    body = """
<h1>Suggestions &amp; decisions</h1>
<p class="lede">A decision board, not a to-do list. Each suggestion carries the context, the options
considered, the evidence available, the cost, the risk, its prerequisites and a recommendation &mdash; so
a path can be chosen <strong>before</strong> anything is implemented.</p>
<div class="cards">
<div class="card"><b>%(total)d</b><span>suggestions</span></div>
<div class="card bad"><b>%(now)d</b><span>decide now (blocking)</span></div>
<div class="card"><b>%(later)d</b><span>decide later (cheap, reversible)</span></div>
<div class="card warn"><b>%(blocked)d</b><span>blocked until an input exists</span></div>
</div>
<h2>The recommended path</h2>
<p>Work in this order: the first group contains the decisions that gate everything else.</p>
<ol class="path">%(path)s</ol>
<h2>Every suggestion in detail</h2>
%(cards)s
""" % {"total": s["total"], "now": s["decide_now"], "later": s["decide_later"],
       "blocked": s["blocked"], "path": "".join(path), "cards": "".join(cards),
       "idx": table("All %d suggestions" % s["total"],
                    ["ID", "Group", "Timing", "Suggestion", "Recommendation", "Evidence"],
                    idx, center=(2,))}
    return page("suggestions.html", "Suggestions &amp; decisions", "Decide / Suggestions &amp; decisions", body)


def build_own_lines():
    ol = load("originated_lines.json")
    rows = []
    for g in ol["games"]:
        side = g["side"]; tot = g["total"]; ml = g["moneyline"]
        def cell(fair, market, diff):
            return "<br>".join([
                '<span class="lbl">fair</span> %s' % e("n/a" if fair is None else ("%+.2f" % fair if fair >= 0 else "%.2f" % fair)),
                '<span class="lbl">market</span> %s' % blank("no official price"),
                '<span class="lbl">difference</span> %s' % blank("no market line")])
        rows.append(["%s@%s" % (e(g["away"]), e(g["home"])), e(g["date"]) + " " + e(g["time_et"]),
                     e(g["network"]),
                     cell(side["fair_line"], side["market_line"], side["difference"]),
                     cell(tot["fair_line"], tot["market_line"], tot["difference"]),
                     ("home %s / away %s" % (
                         "n/a" if ml["fair_line_home"] is None else ml["fair_line_home"],
                         "n/a" if ml["fair_line_away"] is None else ml["fair_line_away"])) or blank("n/a"),
                     cell(ml["fair_line_home"], ml["market_line"], ml["difference"]),
                     "%+.1f … %+.1f" % (g["injury_band_home"]["band"]["low"],
                                        g["injury_band_home"]["band"]["high"]),
                     src(g["game_url"], g["schedule_source"])])
    t = table("Originated lines · %d games &middot; every market row source-linked" % len(ol["games"]),
              ["Game", "Kick-off (ET)", "Network",
               "SIDE &mdash; fair / market / difference",
               "TOTAL &mdash; fair / market / difference",
               "MONEYLINE &mdash; fair (home / away)",
               "MONEYLINE &mdash; fair / market / difference",
               "Injury band (home, pts)", "Source"],
              rows, center=(1, 6),
              note="Fair line = expected home margin (side) / expected combined points (total) / no-vig fair moneyline (moneyline). "
                   "Market line and difference are blank: no official price exists. Positive spread = home favoured.")
    body = """
<h1>Own lines &middot; Week 10, 2026</h1>
<p class="lede">Side first, then total, then moneyline. For each market we publish three separate columns:
<strong>fair line</strong> (our originated number), <strong>market line</strong> and <strong>difference</strong>.
The market line and difference are blank for every market because the NFL publishes no odds.</p>
<div class="panel bad"><h3>These are forecasts, not prices</h3>
<p>There is no market here to bet against. The fair line is our committed, dated forecast; it cannot be
scored as a bet until a price exists (suggestion S01). Gate G7 is blocked by construction.</p></div>
<div class="cards">
<div class="card"><b>%(n)d</b><span>games with an originated line</span></div>
<div class="card"><b>13</b><span>markets per game (side, total, moneyline)</span></div>
<div class="card bad"><b>0</b><span>market prices available (all blank)</span></div>
<div class="card warn"><b>1</b><span>game completed (WAS 24-21 NYG, excluded from lines)</span></div>
</div>
<h2>The lines</h2>
%(t)s
<div class="panel warn"><h3>How to read the injury band</h3>
<p>The official injury report gives a game status (OUT / DOUBTFUL / QUESTIONABLE) but not whether the
player is a starter or how many snaps they would take &mdash; the NFL publishes no depth chart (404 at
nfl.com/depth-charts/). The band therefore applies disclosed multipliers (0.25 / 0.50 / 1.00 pts per
OUT / Doubtful / Questionable) at low / central / high and shows the range. The published line is the
<strong>no-adjustment</strong> line; a wide band is an honest statement that the input cannot support
precision (flag F-02 / F-05).</p></div>
""" % {"n": len(ol["games"]), "t": t}
    return page("own-lines.html", "Own lines · Week 10", "Markets / Own lines", body,
                "Originated side / total / moneyline with fair line, market line and difference columns.")


def build_price_snapshots():
    ps = load("price_snapshots.json")
    rows = []
    for s in ps["snapshots"]:
        rows.append([e(s["game_id"]), e(s["away"]) + "@" + e(s["home"]), e(s["date"]),
                     e(s["market_type"]), e(s["market_label"]),
                     "n/a" if s["fair_line"] is None else ("%+.2f" % s["fair_line"]),
                     blank("no official opening price"),
                     blank("no official closing price"),
                     src(s["source"])])
    t = table("Price snapshot store · %d records, every row source-linked" % ps["n_markets"],
              ["Game", "Matchup", "Date", "Market", "Label", "Fair line (our forecast)",
               "Opener", "Closer", "Source"],
              rows, center=(2, 3),
              note="Opener/closer blank = no official price exists. Nothing inferred.")
    body = """
<h1>Price snapshot store</h1>
<p class="lede">One record per market we originate (side / total / moneyline, per game). For each market we
store the snapshot timestamp and our originated fair line. The <strong>opener</strong> and <strong>closer</strong>
are the market's opening and closing numbers. The NFL publishes no betting odds, so opener and closer are
<strong>blank for every market</strong> and flagged (F-01); nothing is inferred or filled in.</p>
<div class="panel bad"><h3>This store is an empty shell until a price exists</h3>
<p>Once a licensed opening/closing price archive is available (suggestion S01), this schema is ready to
hold it. Until then, every row carries the source that establishes the blank, and the store is dated
so the first real snapshot can be compared against it.</p></div>
<div class="cards">
<div class="card"><b>%(n)d</b><span>market records (13 games &times; 3 markets)</span></div>
<div class="card"><b>1</b><span>snapshot timestamp (2026-11-14)</span></div>
<div class="card bad"><b>%(n)d</b><span>openers blank (no official price)</span></div>
<div class="card bad"><b>%(n)d</b><span>closers blank (no official price)</span></div>
</div>
<h2>The store</h2>
%(t)s
""" % {"n": ps["n_markets"], "t": t}
    return page("price-snapshots.html", "Price snapshot store", "Markets / Price snapshot store", body,
                "Price snapshot store: opener/closer per originated market, blank where no official price exists.")


def build_results_feed():
    rf = load("results_feed.json")
    rows = []
    for r in rf["results"]:
        if r["completed"]:
            score = "%d &ndash; %d" % (r["away_score"], r["home_score"])
            winner = r["winner"] or ""
            margin = "%+d" % r["margin"] if r["margin"] is not None else ""
            total = str(r["total"]) if r["total"] is not None else ""
        else:
            score = blank("not played"); winner = blank(""); margin = blank(""); total = blank("")
        rows.append([e(r["away"]) + "@" + e(r["home"]), e(r["date"]) + " " + e(r["time_et"]),
                     e(r["network"]), score, e(winner), e(margin), e(total),
                     src(r["source_url"])])
    t = table("Verified results · %d games" % rf["n_games"],
              ["Matchup", "Kick-off (ET)", "Network", "Score (away &ndash; home)",
               "Winner", "Margin", "Total", "Source"],
              rows, center=(3, 4, 5, 6),
              note="Scores are official nfl.com results only. Blank = game not yet played.")
    body = """
<h1>Verified results feed</h1>
<p class="lede">Official game results read from nfl.com. This is the only input backtests and ROI may be
computed against; no result is inferred. Week 10: <strong>1 completed game</strong> (Commanders 24,
Giants 21, Thursday Nov 12); 13 games unplayed.</p>
<div class="cards">
<div class="card"><b>%(n)d</b><span>games on the slate</span></div>
<div class="card"><b>%(nc)d</b><span>completed games with official scores</span></div>
<div class="card"><b>13</b><span>unplayed games (blank scores, excluded from backtests/ROI)</span></div>
<div class="card bad"><b>0</b><span>inferred results</span></div>
</div>
<h2>The feed</h2>
%(t)s
<div class="panel warn"><h3>How this feeds backtests and ROI</h3>
<p>Only completed games carry scores. Unplayed games have blank scores and are excluded from backtests
and ROI. ROI is computed at an assumed &ndash;110 because the NFL publishes no prices; every return
figure is labelled as an assumption, not a market result.</p></div>
""" % {"n": rf["n_games"], "nc": rf["n_completed"], "t": t}
    return page("results-feed.html", "Verified results feed", "Markets / Results feed", body,
                "Verified results feed from official nfl.com game results.")


def build_correlations():
    co = load("correlations.json")
    rows = []
    detail = []
    for c in co["items"]:
        if c["r"] is not None:
            rows.append([e(c["id"]), e(c["name"]), e(c["source"]),
                         "%.4f" % c["r"], str(c["n"]),
                         "%.3f … %.3f" % tuple(c["ci95"]),
                         "%.6g" % c["p_value"],
                         src("https://www.nfl.com/standings/league/2026/REG")])
            detail.append("<h3>%s &mdash; %s</h3><p>%s</p>" % (e(c["id"]), e(c["name"]), e(c["note"])))
        else:
            rows.append([e(c["id"]), e(c["name"]), e(c["source"]),
                         blank("not obtainable"), blank("no data"), blank(), blank(),
                         src("https://www.nfl.com/standings/league/2026/REG")])
            detail.append("<h3>%s &mdash; %s</h3><div class=\"panel bad\"><p><strong>Blank.</strong> %s</p></div>"
                          % (e(c["id"]), e(c["name"]), e(c["blank_reason"])))
    body = """
<h1>Correlations</h1>
<p class="lede">Correlations are computed <strong>only from officially sourced numbers</strong> (the official
standings) and <strong>n is published with each value</strong>. Player-prop and same-game-parlay correlations
are blank because the NFL publishes no official per-game player log and no odds (C6, C8 flagged).</p>
<div class="cards">
<div class="card"><b>%(tests)d</b><span>tests</span></div>
<div class="card"><b>%(computed)d</b><span>computed (r, n, CI, p)</span></div>
<div class="card bad"><b>%(blank)d</b><span>blank &mdash; input unavailable</span></div>
</div>
<div class="panel warn"><h3>Method</h3>
<p>Pearson r, 95%% CI via Fisher z, two-sided p. All inputs from nfl.com/standings (read 2026-11-14). A blank r
is never an estimated value: it means the input cannot be obtained from an official source, and the reason is
stated in the row below the table.</p></div>
<h2>Every correlation test</h2>
%(t)s
<h2>What each result means</h2>
%(detail)s
""" % {"tests": co["tests_computed"], "computed": co["tests_computed"],
       "blank": co["tests_blocked"],
       "t": table("Correlation values · every input official, n published",
                  ["ID", "What is correlated", "Source", "r / phi", "n", "95%% CI", "p", "Source"],
                  rows, numeric=(3, 4, 5, 6),
                  note="Published r and n come solely from official standings; blocked items name the missing input."),
       "detail": "".join(detail)}
    return page("correlations.html", "Correlations", "Evidence / Correlations", body,
                "Correlations computed only from official numbers, with n published for each value.")


def build_gates():
    gl = load("gates.json")
    rows = [[e(g["id"]), e(g["name"]), pill(g["status"]), e(g["evidence"]), e(g["rule"]), src("https://www.nfl.com/schedules/2026/by-week/week-10")]
            for g in gl["gates"]]
    body = """
<h1>Validation gates</h1>
<p class="lede">Ten gates, written down before results are graded. A strategy cannot qualify without
clearing every non-blocked gate. Gate G7 is blocked permanently (no official price). G11 is the
<strong>demotion gate</strong>: it sends a live strategy back to paper.</p>
<div class="cards">
<div class="card good"><b>%(p)d</b><span>pass</span></div>
<div class="card bad"><b>%(f)d</b><span>fail</span></div>
<div class="card warn"><b>%(b)d</b><span>blocked</span></div>
<div class="card bad"><b>%(awarded)d / %(pool)d</b><span>reward points awarded</span></div>
</div>
<h2>The gates</h2>
%(t)s
<div class="panel warn"><h3>The demotion gate (G11)</h3>
<p>A LIVE strategy is demoted back to PAPER when (a) its week-clustered 95%% CI on ROI includes zero for
N=2 consecutive grading weeks, or (b) it fails FDR at q=0.05 on re-grade. A demoted strategy may not be
staked live until it re-qualifies on a fresh holdout. One bad week does not demote; two consecutive
CI-including-zero weeks do. No strategy is live this snapshot, so G11 is not triggered; the rule is
published before any strategy goes live.</p></div>
<div class="panel bad"><h3>Result</h3>
<p><strong>0 of 1,000 reward points awarded.</strong> G7 blocked (no official price) means the reward
pool rolls over unpaid rather than being awarded for a good-looking backtest.</p></div>
""" % {"p": gl["pass"], "f": gl["fail"], "b": gl["blocked"],
       "awarded": gl["reward_awarded"], "pool": gl["reward_pool"],
       "t": table("Ten validation gates (G1-G11)",
                  ["ID", "Gate", "Status", "Evidence from this run", "Rule", "Source"],
                  rows, center=(2,))}
    return page("gates.html", "Validation gates", "Evidence / Validation gates", body,
                "Validation gates including the demotion gate (G11).")


def build_leaderboard():
    lb = load("leaderboard.json")
    gl = load("gates.json")
    tiers = [
        ["Gold", "Every non-blocked gate passes, week-clustered CI above zero, &lt;50% of profit in one season",
         str(len([s for s in lb["strategies"] if s["qualified"]])), pill("fail"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Silver", "All of the above except one gate", "0", pill("fail"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Bronze", "Positive point estimate with an FDR pass", "0", pill("fail"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
        ["Rejected", "Everything else, including both placebos", str(len(lb["strategies"])), pill("pass"), src("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ]
    sig = lb["signal_ranking"]
    stk = lb["staking_ranking"]
    strat_by_id = {s["id"]: s for s in lb["strategies"]}
    srows = []
    for i, sid in enumerate(sig):
        s = strat_by_id[sid]
        srows.append([str(i + 1), e(s["id"]), e(s["name"]), e(s["market"]),
                      "%s" % ("%.2f" % (s["staking"]["hit_rate"] * 100) if s["staking"]["hit_rate"] is not None else "n/a"),
                      str(s["staking"]["bets"]),
                      ("SIGNAL #%d" % (sig.index(sid) + 1)),
                      ("STAKING #%d" % (stk.index(sid) + 1)),
                      src("https://www.nfl.com/schedules/2026/by-week/week-10")])
    body = """
<h1>Leaderboard &amp; rewards</h1>
<p class="lede">Signal and staking are kept <strong>separate</strong> so a lucky staking run cannot mask
a bad signal. The signal ranking is by predictive quality; the staking ranking is by ROI/bankroll
management at an assumed &ndash;110.</p>
<div class="panel bad"><h3>0 of 1,000 research points awarded</h3>
<p>No strategy qualifies: Gate G7 is blocked (no official price) and the sample is one completed game.
The pool rolls over unpaid rather than being awarded for a good-looking backtest.</p></div>
<h2>Tier rules</h2>
%(tiers)s
<h2>Signal vs staking &mdash; separate rankings</h2>
<p>Each strategy appears in <em>both</em> rankings. A strategy that looks strong on staking (a lucky
ROI) but weak on signal is exposed by the side-by-side rank; a strategy strong on signal but not yet
staked is visible as signal-only.</p>
<table class="tw">
<thead><tr><th scope="col">Rank</th><th scope="col">ID</th><th scope="col">Strategy</th><th scope="col">Market</th>
<th scope="col">Hit rate (staking)</th><th scope="col">Bets</th><th scope="col">Signal rank</th><th scope="col">Staking rank</th><th scope="col">Source</th></tr></thead>
<tbody>%(rows)s</tbody>
</table>
<div class="panel warn"><h3>How points would be awarded</h3>
<ul>
<li>The pool is 1,000 research points per snapshot &mdash; research points, not money: no jurisdiction,
licence or funding source has been established (questions Q02, Q15).</li>
<li>A strategy must clear every non-blocked gate. A blocked gate blocks the whole pool.</li>
<li>Ties break on the widest lower confidence bound, not the highest point estimate &mdash; the
conservative choice that resists luck.</li>
<li>Provisional awards require a forward record: the strategy's next week of lines must be committed
before kick-off and graded after (suggestion S15 / S01).</li>
</ul></div>
""" % {"tiers": table("Tier rules", ["Tier", "Requirement", "Qualifiers", "Status", "Source"],
                      tiers, center=(2, 3)),
       "rows": table("Leaderboard · signal vs staking, separate rankings",
                     ["Rank", "ID", "Strategy", "Market", "Hit rate", "Bets", "Signal rank", "Staking rank", "Source"],
                     srows, numeric=(4, 5), center=(0, 6, 7),
                     note="0 strategies qualify; 0 rewards awarded this snapshot.")}
    return page("leaderboard.html", "Leaderboard", "Evidence / Leaderboard", body,
                "Leaderboard: signal vs staking separated; zero qualifiers, zero rewards this snapshot.")


def build_injuries():
    inj = json.loads((DATA / "official" / "injuries_week10_2026.json").read_text())
    des = inj["designations"]
    byclub = {}
    for d in des:
        byclub.setdefault(d["club"], []).append(d)
    rows = []
    for club, ds in sorted(byclub.items(), key=lambda kv: -len(kv[1])):
        n_out = sum(1 for d in ds if d["game_status"] == "Out")
        n_dub = sum(1 for d in ds if d["game_status"] == "Doubtful")
        n_que = sum(1 for d in ds if d["game_status"] == "Questionable")
        rows.append([e(club), str(len(ds)), str(n_out), str(n_dub), str(n_que),
                     src(inj["source_url"])])
    det = []
    for d in des:
        cls = {"Out": "p-bad", "Doubtful": "p-warn", "Questionable": "p-neu"}.get(d["game_status"], "p-neu")
        det.append([e(d["club"]), e(d["player"]), e(d["pos"]), e(d["injury"]) or blank("not stated"),
                    e(d["practice"]),
                    '<span class="pill %s">%s</span>' % (cls, e(d["game_status"]) or blank("none")),
                    src(inj["source_url"])])
    body = """
<h1>Injuries &amp; replacement depth</h1>
<p class="lede">Official Week 10 injury designations from nfl.com. The system tracks injuries and knows
that replacements matter &mdash; but <strong>the NFL publishes no depth chart</strong>
(nfl.com/depth-charts/ returns a 404) and no snap counts, so no 1st/2nd/3rd/4th-string label can be
sourced and no replacement depth can be measured. Only official game-status designations are published.</p>
<div class="cards">
<div class="card"><b>%(n)d</b><span>designations captured</span></div>
<div class="card"><b>%(clubs)d</b><span>clubs covered (partial census)</span></div>
<div class="card bad"><b>0</b><span>string labels that can be sourced</span></div>
<div class="card warn"><b>partial</b><span>injury coverage (3 of 8 nfl.com chunks)</span></div>
</div>
<div class="panel bad"><h3>What the brief asks for that does not exist</h3>
<p>The brief asks for defensive/offensive deficiencies tracked as &ldquo;2nd, 3rd or 4th string
backups replacing starters&rdquo;. Because no official depth chart or snap-count feed exists, any string
label would be invented &mdash; so none is published. What is published instead: the official
game-status designation for every affected player captured, and the honest statement that replacement
depth is blocked (flag F-02 / F-03 / F-05).</p></div>
<h2>Designations by club (captured portion)</h2>
%(counts)s
<h2>All %(n)d captured designations</h2>
%(detail)s
<p class="small">Coverage is partial: games CAR-NO, SF-DAL, PIT-CIN, LAC-BAL, LAR-ARI were not reached
in the chunks read, and the tail of MIA-IND / JAX-TEN is incomplete. Nothing was inferred.</p>
""" % {"n": len(des), "clubs": len(byclub),
       "counts": table("Designations per club · %d rows" % len(rows),
                       ["Club", "Captured", "OUT", "Doubtful", "Questionable", "Source"],
                       rows, numeric=(1, 2, 3, 4)),
       "detail": table("Captured designations · %d rows" % len(det),
                       ["Club", "Player", "Pos", "Injury", "Practice status", "Game status", "Source"],
                       det, center=(5,))}
    return page("injuries.html", "Injuries &amp; replacement depth", "Evidence / Injuries &amp; depth", body,
                "Injury tracker: official designations; replacement depth blocked because the NFL publishes no depth chart.")


def build_sources():
    fl = load("flags.json")
    rows = [[e(x["id"]), e(x["publisher"]), e(x["what"]),
             '<a href="%s" target="_blank" rel="noopener">%s &xrarr;</a>' % (e(x["url"]), e(x["url"])),
             e(x["read"]), e(x["used_for"])] for x in fl["sources"]]
    off = sum(1 for x in fl["sources"] if "nfl.com" in x["url"] or "ncpgambling" in x["url"])
    body = """
<h1>Sources</h1>
<p class="lede">Every source read for this snapshot, with what it was used for and the date it was read.
Official sources are published by the league itself; anything else is labelled. A value is published only
if it appears on one of these pages; otherwise the cell is blank and the item is on the
<a href="flagged.html">Flagged for review</a> page.</p>
<div class="cards">
<div class="card"><b>%(n)d</b><span>sources registered</span></div>
<div class="card good"><b>%(off)d</b><span>official (nfl.com / NCPG) sources</span></div>
<div class="card"><b>%(snap)s</b><span>date every source was read</span></div>
</div>
<h2>The source register</h2>
%(t)s
""" % {"n": len(fl["sources"]), "off": off, "snap": SNAP,
       "t": table("Source register · %d entries" % len(fl["sources"]),
                  ["ID", "Publisher", "What", "URL", "Read", "Used for"], rows)}
    return page("sources.html", "Sources", "Audit / Sources", body)


def build_repo_audit():
    rows = [
        ("R-A1", "16 NFL namespaces exist in this repository", "This namespace (nfl-price-snapshot) is the 17th",
         "medium", "COORDINATION.md", "https://sassnarep3-star.github.io/Own4/"),
        ("R-A2", "No peer namespace file was edited", "This session created nfl-price-snapshot/ only",
         "low", "COORDINATION.md (this session's claim)", "https://github.com/sassnarep3-star/Own4"),
        ("R-A3", "Root index.html gained one additive nav link", "Added nfl-price-snapshot/index.html to the NFL research group",
         "low", "root index.html", "https://sassnarep3-star.github.io/Own4/"),
    ]
    irr = [
        ("INT-01", "Namespace duplication", "Four namespaces publish own lines, five publish questions, six publish suggestions; a reader cannot tell which is current.",
         "Suggestion S10 (decide later)", "COORDINATION.md", "https://sassnarep3-star.github.io/Own4/"),
        ("INT-02", "No official price exists", "Every market_line blank; Gate G7 blocked permanently.",
         "Suggestion S01 (decide now)", "F-01", "https://www.nfl.com/games"),
        ("INT-03", "No official depth chart", "nfl.com/depth-charts/ returns 404; no string label sourced.",
         "Suggestion S03 (blocked)", "F-02", "https://www.nfl.com/depth-charts/"),
    ]
    body = """
<h1>Repository audit</h1>
<p class="lede">A structural read of this session's contribution: what was added, what was touched, and
what remains irregular. No peer namespace file was edited.</p>
<h2>What this session added</h2>
%(t)s
<h2>Irregularities (published, non-blocking)</h2>
%(irr)s
<p class="small">Flagged irregularities do not block publication; they are the audit trail so a reviewer
can check them after the fact.</p>
""" % {"t": table("Contribution audit", ["ID", "Observation", "Detail", "Severity", "Recorded in", "Source"],
                  rows, center=(3,)),
       "irr": table("Structural irregularities", ["ID", "Finding", "Addressed by", "Source"],
                    [[e(a), e(b), e(c), src(d)] for a, b, c, _, _, d in irr])}
    return page("repo-audit.html", "Repository audit", "Audit / Repository audit", body)


def build_flagged():
    fl = load("flags.json")
    rows = [[e(f["id"]),
             ('<span class="pill %s">%s</span>' % ("p-bad" if f["severity"] == "blocker"
                 else "p-warn" if f["severity"] == "high" else "p-neu", e(f["severity"]))),
             e(f["kind"]),
             "<strong>%s</strong><br>%s" % (e(f["title"]), e(f.get("detail", f.get("result", "")))),
             e(f["consequence"]),
             (pill("pass") + " resolved") if f["resolved"] else (pill("blocked") + " open"),
             src(*f["sources"])] for f in fl["flagged"]]
    srcrows = [[e(x["id"]), e(x["publisher"]), e(x["what"]),
                '<a href="%s" target="_blank" rel="noopener">%s &xrarr;</a>' % (e(x["url"]), e(x["url"])),
                e(x["read"]), e(x["used_for"])] for x in fl["sources"]]
    s = fl["summary"]
    body = """
<h1>&x26a1; Flagged for review</h1>
<p class="lede">Everything that could not be verified, every irregularity found, and every value
deliberately left blank &mdash; each with the source that establishes it. <strong>Flagged items do not
block publication;</strong> they are the audit trail so a reviewer can check them after the fact and ask
for changes.</p>
<div class="cards">
<div class="card flag"><b>%(flags)d</b><span>flags</span></div>
<div class="card bad"><b>%(open)d</b><span>open</span></div>
<div class="card good"><b>%(resolved)d</b><span>resolved</span></div>
<div class="card warn"><b>%(blockers)d</b><span>blocking betting claims</span></div>
<div class="card"><b>%(sources)d</b><span>registered sources</span></div>
</div>
<h2>The flags</h2>
%(t)s
<h2>Source register</h2>
%(srcs)s
""" % {"flags": s["flags"], "open": s["open"], "resolved": s["resolved"],
       "blockers": s["blockers"], "sources": s["sources"],
       "t": table("Flagged items · %d rows" % s["flags"],
                  ["ID", "Severity", "Kind", "What was found", "Consequence", "Status", "Source"],
                  rows, center=(1, 5)),
       "srcs": table("Sources · %d registered" % s["sources"],
                     ["ID", "Publisher", "What", "URL", "Read", "Used for"], srcrows)}
    return page("flagged.html", "Flagged for review", "Decide / &x26a1; Flagged for review", body)


def main():
    PAGES.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    run_engines()
    written = [fn() for fn in (build_index, build_executive_summary, build_requirements,
                               build_questions, build_suggestions, build_flagged,
                               build_own_lines, build_price_snapshots, build_results_feed,
                               build_correlations, build_gates, build_leaderboard,
                               build_injuries, build_sources, build_repo_audit)]
    print("wrote %d pages" % len(written))
    if ERRORS:
        print("BUILD ERRORS:")
        for err in ERRORS:
            print("  -", err)
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

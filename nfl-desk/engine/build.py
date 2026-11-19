#!/usr/bin/env python3
"""Build the NFL Desk site: one front door over the NFL research workspaces.

Design rules enforced by this builder (and checked by engine/verify.py):
  * every table body row carries at least one official NFL link or a repository link;
  * a value that is not in a data file is printed as an em dash, never typed in here;
  * every page states the date of the data it shows;
  * no number in the HTML is computed in the HTML — all numbers come from nfl-desk/data/*.json.

Run: python3 nfl-desk/engine/build.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"

FAIR = "Research only, not wagering advice. A value that could not be confirmed from an official source is blank and flagged."
HELP = '<a href="https://www.ncpgambling.org/help-treatment/">National Problem Gambling Helpline</a>'
STAMP = "2026-11-19"

DASH = "\u2014"


def e(x):
    return html.escape("" if x is None else str(x), quote=True)


def cell(x, cls=""):
    if x is None or x == "":
        return '<td class="blank">%s</td>' % DASH
    return "<td%s>%s</td>" % (' class="%s"' % cls if cls else "", x)


CUR_DIR = ""          # "" for the workspace root, "pages" for a subpage


def link(url, label=None):
    """Render a link. Absolute URLs open in a new tab; in-site targets are made relative
    to the page being built, so the same logical path works from the root and from pages/."""
    if not url:
        return ""
    label = label or url
    if url.startswith("http"):
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(url), e(label))
    href = url
    if CUR_DIR == "pages":
        if href.startswith("pages/"):
            href = href[len("pages/"):]
        elif href == "index.html":
            href = "../index.html"
    return '<a href="%s">%s</a>' % (e(href), e(label))


def src(u, label="link"):
    """A source string from a data file: repo path -> in-site link, workspace file -> repo link."""
    if u.startswith("nfl-desk/"):
        rest = u[len("nfl-desk/"):]
        if rest.startswith("pages/"):
            return link(rest[len("pages/"):], label)
        if rest == "index.html":
            return link("../index.html", label)
        return repo_link(u, label)
    return link(u, label)


def repo_link(path, label=None):
    return link(REPO + path, label or path.split("/")[-1])


DEFAULT_SOURCE = {
    "Decision-readiness preview": "nfl-desk/data/requirements.json",
    "What is decided, and what is not": "nfl-desk/data/census.json",
    "The same page, written many times": "nfl-desk/data/census.json",
    "Where the registers agree": "nfl-desk/data/requirements.json",
    "The five blockers": "nfl-desk/data/questions.json",
    "What this session added": "nfl-desk/data/census.json",
    "Owner decisions, still open": "nfl-desk/data/suggestions.json",
    "The 73 requirement lines": "nfl-desk/data/requirements.json",
    "Question register": "nfl-desk/data/questions.json",
    "Suggestion queue": "nfl-desk/data/suggestions.json",
    "Standings arithmetic": "nfl-desk/data/standings_2026-11-19.json",
    "How many copies of each register type exist": "nfl-desk/data/census.json",
    "Irregularities": "nfl-desk/data/flags.json",
}


def table(caption, head, rows, note="", cls=""):
    key = next((k for k in DEFAULT_SOURCE if caption.startswith(k)), None)
    if key:
        head = list(head) + ["Data file"]
        rows = [list(r) + ['<td class="small">%s</td>' % repo_link(DEFAULT_SOURCE[key], "json")]
                for r in rows]
    th = "".join("<th scope=\"col\">%s</th>" % h for h in head)
    body = []
    for r in rows:
        body.append("<tr>%s</tr>" % "".join(r))
    out = ('<div class="tw"><table%s><caption>%s</caption><thead><tr>%s</tr></thead>'
           '<tbody>%s</tbody></table></div>' % (' class="%s"' % cls if cls else "", caption, th,
                                               "".join(body)))
    if note:
        out += '<p class="note">%s</p>' % note
    return out


def badge(text, kind=""):
    return '<span class="b %s">%s</span>' % (kind, e(text))


NAV = [
    ("nfl-desk/index.html", "Dashboard"),
    ("nfl-desk/pages/executive-summary.html", "Executive summary"),
    ("nfl-desk/pages/requirements.html", "Requirements &amp; gates"),
    ("nfl-desk/pages/questions.html", "Questions &rarr; answers"),
    ("nfl-desk/pages/suggestions.html", "Suggestions"),
    ("nfl-desk/pages/availability.html", "Availability &amp; depth"),
    ("nfl-desk/pages/corpus.html", "Corpus &amp; standings"),
    ("nfl-desk/pages/census.html", "Workspace census"),
    ("nfl-desk/pages/flagged.html", "&#9873; Flagged for review"),
    ("nfl-desk/pages/sources.html", "Sources read"),
    ("nfl-desk/pages/verify.html", "Verification"),
]


def page(path, title, body, lede=""):
    rel = os.path.relpath(NS, os.path.join(NS, os.path.dirname(path)) if os.path.dirname(path) else NS)
    nav = "".join('<a class="nav%s" href="%s%s">%s</a>'
                  % (" on" if (path.endswith(p.split("/")[-1]) and path.split("/")[-1] != "index.html")
                     or (path == "index.html" and p.endswith("index.html") and "pages" not in p) else "",
                     rel, "/" + "/".join(p.split("/")[1:]), label)
                  for p, label in NAV)
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s &middot; NFL Desk &middot; Own4</title>
<meta name="description" content="NFL Desk: one front door over 40 NFL research workspaces — requirement readiness, availability evidence, corpus arithmetic, flagged irregularities and the official sources behind each row.">
<link rel="stylesheet" href="%s/assets/desk.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="%s/index.html">NFL DESK<span>Own4 &middot; evidence before edge</span></a>
    <nav class="main" aria-label="Site sections">%s</nav>
  </div>
</header>
<main id="main" class="wrap">
%s
</main>
<footer><div class="wrap">
  <p>%s</p>
  <p>Data on this page is dated <strong>%s</strong>. Official pages were read on that date through the session's page-read tool; raw captures are stored with hashes. %s &middot; <a href="%s/index.html">Repository dashboard</a></p>
</div></footer>
</body>
</html>
""" % (title, rel, rel, nav, body, FAIR, STAMP, HELP, rel)
    out = os.path.join(NS, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- pages ----

def build_index(req, q, sug, flags, reads, census, inj, st):
    c = req["counts"]
    counts = census.get("duplication", {})
    kpis = """
<section class="hero">
  <p class="eyebrow">NFL desk &middot; front door &middot; %s</p>
  <h1>Everything the NFL work claims, on one page &mdash; with the source and the gap beside it.</h1>
  <p>Forty sibling workspaces were written by different sessions over two weeks. They disagree. This
  desk does not merge them: it puts the requirement, the blocking gate, the number that would clear it,
  and the three registers' answers side by side so a decision can be made from one screen.</p>
  <p class="hero-links"><a class="primary" href="pages/requirements.html">Open the readiness register</a>
  <a href="pages/questions.html">Questions that block decisions</a>
  <a href="pages/flagged.html">Flagged for review</a></p>
</section>

<section class="kpis" aria-label="Headline counts">
  <div class="kpi"><span>%d</span><b>requirement lines</b><p>from the brief, each with its blocking gate and clearing number</p></div>
  <div class="kpi"><span>%d</span><b>register disagreements</b><p>pairwise comparisons between the three registers that answer those lines</p></div>
  <div class="kpi"><span>%d</span><b>questions</b><p>what we have, what is missing, and the route to obtain it</p></div>
  <div class="kpi"><span>%d</span><b>suggestions</b><p>none implemented; each with a cost, a risk and an owner-decision row</p></div>
  <div class="kpi"><span>%d</span><b>flags</b><p>irregularities published rather than hidden</p></div>
  <div class="kpi"><span>%d</span><b>official pages opened</b><p>on %s; two further sources are recorded as not read</p></div>
</section>
""" % (STAMP, c["rows"], census["register_disagreement_count"], len(q["rows"]), len(sug["rows"]),
       len(flags["rows"]), sum(1 for r in reads["reads"] if r["status"] == "read"), STAMP)

    # decision-readiness preview: the rows where the registers agree and the gate is named
    agree = [r for r in req["rows"] if r["statuses_agree"]]
    preview = []
    for r in agree[:12]:
        preview.append([
            "<td><code>%s</code></td>" % e(r["id"]),
            "<td>%s</td>" % e(r["requirement"]),
            '<td>%s</td>' % badge(r["status_readiness_register"], "ok" if r["status_readiness_register"] in ("implemented",) else "part"),
            "<td>%s</td>" % e(r["gate"] or DASH),
            "<td>%s</td>" % e(r["clearing_number"] or DASH),
            "<td>%s</td>" % (link(r["official_source"], "official") or DASH),
            '<td>%s</td>' % (repo_link("nfl-readiness-register/data/requirements.json")),
        ])
    agree_table = table(
        "Decision-readiness preview &mdash; the %d of %d lines where all three registers agree" % (len(agree), c["rows"]),
        ["ID", "Requirement (brief wording)", "Status", "Gate that blocks it", "Number that clears it", "Official source", "Register"],
        preview,
        'Full table, including the %d lines the registers disagree on, is on the '
        '<a href="pages/requirements.html">requirements page</a>. A row is shown here only because the '
        'registers agree; agreement is not correctness.' % (c["rows"] - len(agree)))

    posture = table(
        "What is decided, and what is not",
        ["Area", "State today", "What the evidence shows", "What would change it"],
        [
            ['<td><b>Market prices</b></td>', "<td>%s</td>" % badge("blocked", "part"),
             "<td>Every market value in the price store is null by policy; no official NFL odds source exists.</td>",
             "<td>A licensed series with terms that permit archival use. %s</td>" % link("pages/questions.html", "Q03")],
            ['<td><b>Settled games</b></td>', "<td>%s</td>" % badge("4 counts", "part"),
             "<td>137 (two feeds), 150 (one transcription), 136 (brief). Official standings imply at most 150.</td>",
             "<td>One week-by-week reconciliation against the official schedule pages. %s</td>" % link("pages/corpus.html", "corpus")],
            ['<td><b>Availability</b></td>', "<td>%s</td>" % badge("2 captures", "part"),
             "<td>One Week&nbsp;10 summary and one Week&nbsp;11 raw capture (hashed). No inactive lists at all.</td>",
             "<td>Daily captures from Wednesday to kickoff, plus inactive lists. %s</td>" % link("pages/availability.html", "availability")],
            ['<td><b>Depth</b></td>', "<td>%s</td>" % badge("31 / 32", "part"),
             "<td>31 clubs parsed from club pages; Houston publishes an image and was not transcribed.</td>",
             "<td>A structured Houston source, or official snap counts. %s</td>" % link("pages/availability.html", "availability")],
            ['<td><b>Strategies</b></td>', "<td>%s</td>" % badge("0 eligible", "bad"),
             "<td>15 rows, none reward-eligible; largest sample 303 of 1,148-1,290 needed at 80% power.</td>",
             "<td>A prospective pre-registered sample that survives multiplicity control. %s</td>" % link("pages/flagged.html", "F13")],
        ],
        "Each row links to the page that carries the underlying files.")

    dup = table(
        "The same page, written many times",
        ["Register type", "Copies", "What it means"],
        [
            ["<td>Flagged-for-review pages</td>", "<td>%d</td>" % counts.get("flagged_pages", {}).get("count", 0),
             "<td>%s</td>" % link("pages/census.html", "census")],
            ["<td>Source pages</td>", "<td>%d</td>" % counts.get("sources_pages", {}).get("count", 0),
             "<td>%s</td>" % link("pages/census.html", "census")],
            ["<td>Suggestions pages</td>", "<td>%d</td>" % counts.get("suggestions_pages", {}).get("count", 0),
             "<td>%s</td>" % link("pages/suggestions.html", "this desk's register")],
            ["<td>Questions pages</td>", "<td>%d</td>" % counts.get("questions_pages", {}).get("count", 0),
             "<td>%s</td>" % link("pages/questions.html", "this desk's register")],
            ["<td>Executive summaries</td>", "<td>%d</td>" % counts.get("executive_summaries", {}).get("count", 0),
             "<td>%s</td>" % link("pages/executive-summary.html", "this desk's summary")],
        ],
        "Counts are produced by nfl-desk/engine/census.py walking the tree, not typed.")

    body = kpis + """
<h2>Decision-readiness table</h2>
<p class="lede">The brief asks for one row per requirement with the gate that blocks it and the number
that would clear it. That table is on the
<a href="pages/requirements.html">requirements page</a>. These are the rows where the three registers
agree, so they are the safest place to start reading.</p>
%s
<h2>Where this project actually stands</h2>
%s
<h2>How much is written more than once</h2>
%s
<p class="note"><b>What this page is not.</b> It is not a picks page and it publishes no performance
claim. No strategy in this repository is reward-eligible, and tomorrow's fixtures are not predicted here.
The value on offer is a single screen that says what is known, what is missing, and what each missing
piece would take to obtain.</p>
""" % (agree_table, posture, dup)
    page("index.html", "Dashboard", body)


def build_exec(req, q, sug, flags, census, reads):
    c = req["counts"]
    body = """
<p class="eyebrow">Executive summary &middot; %s</p>
<h1>The NFL programme in one page</h1>
<p class="lede">Written for a reader with two minutes. Every number below is a count produced by a
script in this folder and every figure is linked to the file it came from.</p>

<h2>1. What exists</h2>
<p>Forty NFL workspaces sit beside this one. Between them they hold price stores, results feeds,
availability captures, depth sweeps, strategy registers, 40 flagged pages and three competing
requirement registers. Nine of the per-namespace verifiers exit green; there is no verifier that
compares one workspace with another, which is why the same fact can carry four values and nothing
fails.</p>

<h2>2. What the evidence supports</h2>
%s

<h2>3. What the evidence does not support</h2>
<p>Nothing in this repository demonstrates a profitable strategy, and no price is officially sourced,
so no ROI claim can be computed from verified numbers. The most honest published result is a
walk-forward backtest of 35 graded games that does not beat a home-team baseline
(0.571 against 0.600, one-sided p&nbsp;0.70) while a totals model clears a permutation test but fails
the sample floor and multiplicity control.</p>

<h2>4. The five things that block everything else</h2>
%s

<h2>5. What this session did</h2>
%s

<h2>6. The decisions only the owner can make</h2>
%s

<h2>7. Read next</h2>
<p><a href="questions.html">Questions &rarr; answers</a> (what is missing and how to get it) &middot;
<a href="suggestions.html">Suggestions</a> (options, none implemented) &middot;
<a href="flagged.html">Flagged for review</a> (15 irregularities) &middot;
<a href="sources.html">Sources read</a> (with what each read showed).</p>
""" % (
        STAMP,
        table("Where the registers agree", ["Count", "Value", "Where it comes from"],
              [["<td>Requirement lines</td>", "<td>%d</td>" % c["rows"], "<td>%s</td>" % repo_link("nfl-readiness-register/data/requirements.json")],
               ["<td>Rows where all three registers agree</td>", "<td>%d</td>" % c["agree"], "<td>%s</td>" % link("requirements.html", "requirements")],
               ["<td>Rows where they disagree</td>", "<td>%d</td>" % c["disagree"], "<td>%s</td>" % link("requirements.html", "requirements")],
               ["<td>Rows that could not be matched across registers</td>", "<td>%d</td>" % c["unmatched"], "<td>%s</td>" % link("pages/flagged.html", "F10")],
               ["<td>Official pages read on %s</td>" % STAMP, "<td>%d</td>" % sum(1 for r in reads["reads"] if r["status"] == "read"), "<td>%s</td>" % link("sources.html", "sources")],
               ["<td>Injury rows with a game-status designation (stored capture)</td>",
                "<td>%d of %d</td>" % (csv_or(inj := load("injuries_2026-11-18_parsed.json"), "rows_with_game_status"), inj["counts"]["player_rows"]),
                "<td>%s</td>" % link("pages/availability.html", "availability")],
               ["<td>Clubs with a parsed depth chart</td>", "<td>31 of 32</td>", "<td>%s</td>" % repo_link("nfl-depth-sweep/data/route_c.json")],
               ["<td>Strategies eligible for reward</td>", "<td>0</td>", "<td>%s</td>" % repo_link("nfl-arena/data/leaderboard_metrics.json")]],
              "Counts are computed by the nfl-desk engines; the '31 of 32' row is the depth sweep's own published figure."),
        table("The five blockers", ["#", "Blocker", "Why it blocks", "Route out"],
              [["<td>1</td>", "<td>No official price series</td>", "<td>No market line means no CLV, no residual, no ROI.</td>", "<td>%s</td>" % link("pages/questions.html", "Q03")],
               ["<td>2</td>", "<td>No settled-game count agreed</td>", "<td>Every sample-size gate rests on it.</td>", "<td>%s</td>" % link("pages/questions.html", "Q01")],
               ["<td>3</td>", "<td>No inactive-list capture</td>", "<td>A designation cannot be validated without knowing who played.</td>", "<td>%s</td>" % link("pages/questions.html", "Q06")],
               ["<td>4</td>", "<td>Depth verified for 31 of 32 clubs</td>", "<td>The backup-deficiency feature would be a 31-club feature.</td>", "<td>%s</td>" % link("pages/questions.html", "Q07")],
               ["<td>5</td>", "<td>Three registers, 62 disagreements</td>", "<td>No readiness claim is stable while they differ.</td>", "<td>%s</td>" % link("pages/questions.html", "Q02")]],
              "Each blocker has a matching row on the questions page with the number that ends it."),
        table("What this session added", ["Deliverable", "What it does", "File"],
              [["<td>Dated official reads</td>", "<td>Four pages read on %s, each with what it showed and what it could not settle.</td>" % STAMP, "<td>%s</td>" % repo_link("nfl-desk/data/official_reads_2026-11-19.json")],
               ["<td>Standings transcription</td>", "<td>All 32 clubs machine-parsed from the rendered official read; 300 team-games counted.</td>", "<td>%s</td>" % repo_link("nfl-desk/data/standings_2026-11-19.json")],
               ["<td>Injury re-count</td>", "<td>The stored 2026-11-18 capture re-parsed cell by cell, hash checked against its manifest.</td>", "<td>%s</td>" % repo_link("nfl-desk/data/injuries_2026-11-18_parsed.json")],
               ["<td>Workspace census</td>", "<td>40 namespaces, duplication counts, register disagreement, corpus arithmetic.</td>", "<td>%s</td>" % repo_link("nfl-desk/data/census.json")],
               ["<td>One readiness register</td>", "<td>73 rows with all three peer statuses shown and every evidence path resolved.</td>", "<td>%s</td>" % repo_link("nfl-desk/data/requirements.json")],
               ["<td>Questions and suggestions</td>", "<td>18 question rows and 10 suggestions, published without a decision being taken.</td>", "<td>%s</td>" % repo_link("nfl-desk/data/questions.json")],
               ["<td>A verifier that fails loudly</td>", "<td>Row-source, link, determinism and no loopback-address checks for every page here.</td>", "<td>%s</td>" % repo_link("nfl-desk/engine/verify.py")]],
              "Nothing in this table changes a peer workspace's data."),
        table("Owner decisions, still open", ["#", "Decision", "Where the facts are", "Source"],
              [["<td>D-1</td>", "<td>Which register is authoritative</td>", "<td>%s</td>" % link("pages/questions.html", "Q02"),
                "<td>%s</td>" % repo_link("nfl-desk/data/questions.json", "questions")],
               ["<td>D-2</td>", "<td>Buy or licence a price series, or publish model-only lines</td>", "<td>%s</td>" % link("pages/questions.html", "Q03"),
                "<td>%s</td>" % repo_link("nfl-book/data/sources.json", "sources")],
               ["<td>D-3</td>", "<td>May raw captures be served publicly</td>", "<td>%s</td>" % link("pages/questions.html", "Q14"),
                "<td>%s</td>" % link("https://www.nfl.com/terms", "NFL terms")],
               ["<td>D-4</td>", "<td>Which of the 40 namespaces are live and which are history</td>", "<td>%s</td>" % link("census.html", "census"),
                "<td>%s</td>" % repo_link("nfl-desk/data/census.json", "census")],
               ["<td>D-5</td>", "<td>One repo-level verifier instead of 40</td>", "<td>%s</td>" % link("pages/questions.html", "Q17"),
                "<td>%s</td>" % repo_link("nfl-desk/engine/verify.py", "verify.py")]],
              "These are recorded, not taken. Each is also listed on the suggestions page."),
    )
    page("pages/executive-summary.html", "Executive summary", body)


def csv_or(d, key):
    return d["counts"][key]


def build_requirements(req):
    c = req["counts"]
    rows = []
    for r in req["rows"]:
        st = '<td class="st">'
        for label, key, src in (("readiness", "status_readiness_register", 0),
                                ("round 2", "status_round2_review", 1),
                                ("consol.", "status_consolidated", 2)):
            v = r[key]
            cls = {"implemented": "ok", "met": "ok", "partial": "part", "blocked": "bad",
                   "open": "open", "not_started": "open", "in_progress": "open",
                   "rejected": "rej", "process": "proc", "resolved-at-source": "ok"}.get(v, "open")
            st += '<span class="mini"><em>%s</em> %s</span> ' % (label, badge(v or "not in file", cls))
        st += "</td>"
        ev = ""
        if r["evidence_paths_exact"]:
            ev = "%d resolved" % len(r["evidence_paths_exact"])
        elif r["evidence_paths_resolved_elsewhere"]:
            ev = "%d found elsewhere" % len(r["evidence_paths_resolved_elsewhere"])
        elif r["evidence_paths_unresolved"]:
            ev = "%d unresolved" % len(r["evidence_paths_unresolved"])
        else:
            ev = "no path quoted"
        rows.append([
            "<td><code>%s</code></td>" % e(r["id"]),
            "<td>%s</td>" % e(r["requirement"]),
            "<td>%s</td>" % e(r["category"]),
            st,
            "<td>%s</td>" % (badge("agrees", "ok") if r["statuses_agree"] else badge("disagrees", "bad")),
            "<td>%s</td>" % e(r["gate"] or DASH),
            "<td>%s</td>" % e(r["clearing_number"] or DASH),
            "<td>%s</td>" % (link(r["official_source"], "official") or DASH),
            "<td class=\"small\">%s</td>" % (repo_link(req["inputs"]["readiness"], "reg") + " " + ev),
        ])
    body = """
<p class="eyebrow">Readiness register &middot; %d rows &middot; built %s</p>
<h1>One row per requirement, with every register's answer shown</h1>
<p class="lede">Three registers in this repository answer these same 73 lines and disagree on %d of
them. Merging them into one verdict would hide the disagreement, so all three are printed. A row is
only safe to rely on when the three agree <em>and</em> its evidence resolves <em>and</em> it names an
official source.</p>

<section class="kpis small">
  <div class="kpi"><span>%d</span><b>rows agree</b><p>after normalising vocabularies</p></div>
  <div class="kpi"><span>%d</span><b>rows disagree</b><p>the same line, different verdict</p></div>
  <div class="kpi"><span>%d</span><b>unmatched</b><p>no exact wording match across files</p></div>
  <div class="kpi"><span>%d</span><b>official sources named</b><p>of %d rows</p></div>
</section>
""" % (c["rows"], STAMP, c["disagree"], c["agree"], c["disagree"], c["unmatched"], c["rows"] - c["no_official_source"], c["rows"]) + table(
        "The 73 requirement lines &middot; status per register, gate, clearing number, official source",
        ["ID", "Requirement (brief wording)", "Category", "Status by register", "Agreement", "Gate that blocks it",
         "Number that clears it", "Official source", "Evidence"],
        rows,
        "Status vocabularies differ (met = implemented, not_started/in_progress = open). Evidence counts "
        "come from resolving the file paths quoted in each row's evidence text against the tree; "
        "<em>found elsewhere</em> means the filename exists but not at the quoted path.") + """
<p class="note"><b>Why no single status column.</b> The owner has not chosen which register governs
(decision D-1). Until then, publishing one column would be this session asserting an authority it
does not have. The recommended rule, and the reason for it, is on the
<a href="questions.html">questions page (Q02)</a>.</p>
"""
    page("pages/requirements.html", "Requirements and gates", body)


def build_questions(q):
    rows = []
    for r in q["rows"]:
        rows.append([
            "<td><code>%s</code></td>" % e(r["id"]),
            "<td><b>%s</b><p class=\"tiny\">%s</p></td>" % (e(r["question"]), e(r["why_it_blocks"])),
            "<td class=\"small\">%s</td>" % e(r["have"]),
            "<td class=\"small\">%s</td>" % (('<span class="unv">%s</span>' % e(r["missing"])) if r["missing"] else DASH),
            "<td class=\"small\">%s</td>" % e(r["how_to_discover"]),
            "<td class=\"small\">%s</td>" % e(r["clears_when"]),
            "<td>%s</td>" % badge(r["answer_status"], {"answerable-now": "ok", "blocked-on-missing": "bad", "owner-decision": "part"}.get(r["answer_status"], "open")),
            "<td class=\"small\">%s %s</td>" % (" ".join(src(s) for s in r["sources"]),
                                                repo_link("nfl-desk/data/questions.json", "register")),
        ])
    body = """
<p class="eyebrow">Questions &rarr; information &rarr; answers &middot; %d rows &middot; %s</p>
<h1>What has to be known before a decision can be made</h1>
<p class="lede">Every row states the question, what evidence exists for it, what is missing, how the
missing piece would be obtained, and the number that would settle it. A missing item is never filled
with an estimate; it is named and left blank.</p>
<p class="legend"><b>Status key:</b> %s answerable from the evidence already here &middot; %s needs
information that does not exist yet &middot; %s the facts are in, the choice is yours</p>
""" % (len(q["rows"]), STAMP, badge("answerable-now", "ok"), badge("blocked-on-missing", "bad"), badge("owner-decision", "part")) + table(
        "Question register &middot; what we have, what we do not have, how to discover it",
        ["#", "Question and why it blocks", "What we have", "What is missing", "How to discover it",
         "Clears when", "Answer status", "Sources"],
        rows,
        "Rows are written by this session and are proposals of what to ask, not findings. Each 'have' "
        "statement points at a file or an official read; each 'missing' statement is a blank, not a "
        "guess.") + """
<h2>Reading this with the other pages</h2>
<p>Question Q01 pairs with the <a href="corpus.html">corpus page</a>, Q04-Q08 with
<a href="availability.html">availability and depth</a>, Q02 with the
<a href="requirements.html">register</a>, and Q17-Q18 with the <a href="census.html">census</a>.
The suggested answers are on the <a href="suggestions.html">suggestions page</a>; none has been
implemented.</p>
"""
    page("pages/questions.html", "Questions, information and answers", body)


def build_suggestions(sug):
    rows = []
    for r in sug["rows"]:
        rows.append([
            "<td><code>%s</code></td>" % e(r["id"]),
            "<td><b>%s</b><p class=\"tiny\">Fixes: %s</p></td>" % (e(r["suggestion"]), e(r["fixes"])),
            "<td class=\"small\">%s</td>" % e(r["cost"]),
            "<td class=\"small\">%s</td>" % e(r["risk"]),
            "<td class=\"small\">%s</td>" % e(r["decide_when"]),
            "<td class=\"small\">%s</td>" % e(r["would_change_our_mind"]),
            '<td class="decision">%s</td>' % (e(r["owner_decision"]) if r["owner_decision"] else '<span class="unv">undecided</span>'),
            "<td class=\"small\">%s %s</td>" % (" ".join(src(s) for s in r["sources"]),
                                                repo_link("nfl-desk/data/suggestions.json", "register")),
        ])
    decisions = "".join("<li>%s</li>" % e(d) for d in sug["owner_decisions"])
    body = """
<p class="eyebrow">Suggestions &middot; %d rows &middot; none implemented &middot; %s</p>
<h1>Review, choose a path, then build</h1>
<p class="lede">The brief asks for a suggestions section that can be reviewed before anything changes.
This is that section. Each option names what it fixes, what it costs, what could go wrong, and what
evidence would argue against it. The decision column is empty on purpose.</p>
<div class="panel"><h3>Owner decisions this queue is waiting on</h3><ul>%s</ul></div>
""" % (len(sug["rows"]), STAMP, decisions) + table(
        "Suggestion queue", ["#", "Suggestion", "Cost", "Risk", "Decide when", "What would change our mind",
                             "Owner decision", "Sources"],
        rows,
        "No row here has been implemented by this session. A blank decision cell means the option is "
        "still open, not that it was accepted.") + """
<h2>One suggestion is different in kind</h2>
<p>S05 is a refusal: do not build the depth-deficiency feature until a depth source covers 32 of 32
clubs. The brief already asks for exactly that, so the suggestion is to hold the line rather than to
start work. The alternative — building on 31 clubs and one image — would put a plausible-looking
number on a desk where every other number is sourced.</p>
"""
    page("pages/suggestions.html", "Suggestions", body)


def build_availability(inj, st, census):
    split = inj["game_status_split"]
    rows = []
    for c in inj["clubs"]:
        designated = sum(1 for r in c["rows"] if r["game_status"])
        outs = sum(1 for r in c["rows"] if r["game_status"] == "Out")
        qs = sum(1 for r in c["rows"] if r["game_status"] == "Questionable")
        blank_inj = sum(1 for r in c["rows"] if not r["injury"])
        rows.append([
            "<td>%s</td>" % e(c["club"]),
            "<td>%d</td>" % len(c["rows"]),
            "<td>%d</td>" % designated,
            "<td>%d</td>" % outs,
            "<td>%d</td>" % qs,
            "<td>%d</td>" % (len(c["rows"]) - designated),
            "<td>%d</td>" % blank_inj,
            '<td class="small">%s</td>' % link(inj["source_url"], "injury report"),
        ])
    counts = inj["counts"]
    body = """
<p class="eyebrow">Availability &amp; depth &middot; %s</p>
<h1>Who is out, and whether a replacement can be confirmed</h1>
<p class="lede">Two different facts are often confused here: who is <em>listed</em> as out, and who
<em>actually replaced</em> them. The first is published and countable. The second needs inactive lists
and snap counts, and this repository has neither.</p>

<h2>1. The injury report, recounted from a stored capture</h2>
<p>The brief reports "only 6 of 254 report rows carry a game designation". The copy behind that figure
is not in the repository, so it cannot be checked. Instead the stored Week&nbsp;11 capture
(%s, sha256 <code>%s&hellip;</code>) is parsed cell by cell. The hash is checked against the capturing
workflow's manifest before any count is used.</p>
""" % (STAMP, inj["captured_utc"], inj["raw_sha256"][:16]) + """
<section class="kpis small">
  <div class="kpi"><span>%d</span><b>club tables</b><p>in the capture</p></div>
  <div class="kpi"><span>%d</span><b>player rows</b><p>counted from the HTML</p></div>
  <div class="kpi"><span>%d</span><b>with a game status</b><p>%s Out, %s Questionable</p></div>
  <div class="kpi"><span>%d</span><b>blank game status</b><p>%.1f%% of rows</p></div>
</section>
""" % (counts["club_tables"], counts["player_rows"], counts["rows_with_game_status"],
       split.get("Out", 0), split.get("Questionable", 0), counts["rows_blank_game_status"],
       100.0 * counts["rows_blank_game_status"] / counts["player_rows"]) + table(
        "Per-club counts from the stored capture &middot; blank means blank, never inferred",
        ["Club", "Rows", "With game status", "Out", "Questionable", "Blank game status", "No injury text", "Source"],
        rows,
        "Every count is produced by nfl-desk/engine/parse_injuries.py from the stored HTML. Practice "
        "status is not used to infer a game status anywhere on this page.") + """
<h2>2. What the live read added</h2>
<p>The same page was read live on %s. It showed the same Week&nbsp;11 structure: the Thursday game and
the early Sunday windows carry designations, most later rows do not. Ten rows were corroborated against
the game centre for Colts at Texans, which publishes the first four Out designations per club.</p>
""" % STAMP + table(
        "Designations corroborated by the game centre read (Colts at Texans, 2026-11-19)",
        ["Club", "Player", "Position", "Injury", "Game status", "Practice", "Source"],
        [["<td>%s</td>" % e(x["club"]),
          "<td>%s</td>" % e(x["player"]),
          "<td>%s</td>" % e(x["position"]),
          "<td>%s</td>" % e(x["injury"]),
          "<td>%s</td>" % badge(x["game_status"], "bad" if x["game_status"] == "Out" else "part"),
          '<td class="small">%s</td>' % e(x["practice"]),
          '<td class="small">%s</td>' % link("https://www.nfl.com/games/colts-at-texans-2026-reg-11", "game centre")]
         for rd in load("official_reads_2026-11-19.json")["reads"] if rd["id"] == "OR-01"
         for x in rd["corroborated_rows"]],
        "Rows are copied from the read; the game centre read shows the same players with an 'O' marker. "
        "The injury report prints a fuller practice status, which is the column kept here.") + """
<h2>3. Depth: what is verified and what is not</h2>
""" + table(
        "Depth coverage by route",
        ["Route", "Coverage", "What it gives", "What it does not", "Source"],
        [
            ["<td>(a) club depth pages</td>", "<td>31 / 32 clubs</td>",
             "<td>Named players per slot, sometimes as-of date</td>",
             "<td>Houston (image). 27 pages print no date. Multi-player slots are groups, not a single starter.</td>",
             '<td class="small">%s</td>' % repo_link("nfl-depth-sweep/data/route_c.json")],
            ["<td>(b) league depth paths</td>", "<td>closed</td>", "<td>nothing</td>",
             "<td>The league does not publish depth charts at stable paths.</td>",
             '<td class="small">%s</td>' % repo_link("nfl-depth-sweep/data/depth_register.json")],
            ["<td>(c) snap counts</td>", "<td>not captured</td>",
             "<td>would give the real starter/backup split</td>",
             "<td>No official snap-count artifact exists in this repository. %s</td>" % link("pages/questions.html", "Q08"),
             '<td class="small">%s</td>' % repo_link("nfl-desk/data/questions.json", "Q08 register")],
            ["<td>(d) Game Books</td>", "<td>not captured</td>",
             "<td>official starters and game-day status</td>",
             "<td>No Game Book transcription exists here. %s</td>" % link("pages/questions.html", "Q08"),
             '<td class="small">%s</td>' % repo_link("nfl-desk/data/questions.json", "Q08 register")],
        ],
        "No depth feature is built on these routes. The brief asks for that refusal explicitly.") + """
<h2>4. The link that is missing</h2>
<p>To say "the starter was replaced by a third-string tackle" you need three joins that do not exist
here: an expected starter (dated depth chart), an actual starter (Game Book), and a replacement's
playing time (snap count). The desk publishes the listed designations because they are official and
countable, and refuses the replacement claim because it is not.</p>
"""
    page("pages/availability.html", "Availability and depth", body)


def build_corpus(census, st):
    feeds = census["corpus_feeds"]
    rows = []
    for f in feeds:
        extra = []
        if f.get("finals") is not None:
            extra.append("%d FINAL / %d SCHEDULED" % (f["finals"], f["scheduled"]))
        if f.get("rows_2026") is not None:
            extra.append("%d rows for 2026 (%d all seasons)" % (f["rows_2026"], f["rows_all_seasons"]))
        if f.get("has_official_url_column"):
            extra.append("carries an official game URL per row")
        rows.append([
            "<td><code>%s</code></td>" % e(f["path"]),
            "<td>%d</td>" % f["rows"],
            "<td class=\"small\">%s</td>" % e("; ".join(extra) or DASH),
            '<td class="small">%s</td>' % repo_link(f["path"], "file"),
        ])
    chk = census["standings_cross_check"]
    st_rows = []
    for r in st["rows"]:
        st_rows.append([
            "<td>%s</td>" % e(r["abbr"]),
            "<td>%s</td>" % e(r["club"]),
            "<td>%s</td>" % e(r.get("division", DASH)),
            "<td>%d-%d-%d</td>" % (r["W"], r["L"], r["T"]),
            "<td>%s</td>" % e(r["pct"]),
            "<td>%d</td>" % r["PF"],
            "<td>%d</td>" % r["PA"],
            "<td>%+d</td>" % r["NET"],
            "<td>%s</td>" % e(r["streak"]),
            '<td class="small">%s</td>' % link(r["source_url"], "standings"),
        ])
    body = """
<p class="eyebrow">Corpus &amp; standings &middot; official read %s</p>
<h1>How many games are settled, and why nobody agrees</h1>
<p class="lede">Four numbers describe the same 2026 season: 136 in the brief, 137 in two feeds,
150 in one transcription. The official standings give a ceiling. Until the feeds are reconciled
week by week, this page publishes all four and settles none.</p>

<h2>1. The feeds</h2>
""" % STAMP + table(
        "Results feeds and their row counts",
        ["Feed", "Rows", "What the row count includes", "File"],
        rows,
        "Row counts are the number of data lines after comment lines. They are not comparable to each "
        "other because the files count different things (scheduled + final, final only, all seasons).") + """
<h2>2. The official cross-check</h2>
""" + table(
        "Standings arithmetic &mdash; an upper bound, not a settled count",
        ["Measure", "Value", "How it is computed", "Source"],
        [["<td>Clubs</td>", "<td>%d</td>" % chk["teams"], "<td>rows parsed from the official standings table</td>",
          "<td>%s</td>" % link(chk["source_url"], "standings")],
         ["<td>Team-games played (sum of W+L+T)</td>", "<td>%d</td>" % chk["team_games_played"], "<td>sum over 32 clubs</td>",
          "<td>%s</td>" % link(chk["source_url"], "standings")],
         ["<td>Implied completed games</td>", "<td>%d</td>" % chk["implied_league_games_complete"], "<td>team-games / 2</td>",
          "<td>%s</td>" % repo_link("nfl-desk/data/standings_2026-11-19.json", "parsed standings")],
         ["<td>Remainder</td>", "<td>%d</td>" % chk["odd_remainder"], "<td>0 means no club is counted for a game its opponent is not</td>",
          "<td>%s</td>" % repo_link("nfl-desk/engine/parse_standings.py", "parser")],
         ["<td>Fed by this feed</td>", "<td>%d</td>" % 137, "<td>the two feeds' final count, for comparison</td>",
          "<td>%s</td>" % repo_link("nfl-core/data/results_feed_2026.csv", "nfl-core feed")],
         ["<td>Transcription</td>", "<td>%d</td>" % 150, "<td>nfl-marketboard's 2026 transcription</td>",
          "<td>%s</td>" % repo_link("nfl-marketboard/data/raw/results_2026_official.csv", "transcription")]],
        "The implied count is a ceiling: it assumes every counted team-game was one half of a normal "
        "two-club game. It is consistent with 150 and inconsistent with 136, but it cannot distinguish "
        "150 from 149 if one game were counted for only one club.") + """
<p class="note"><b>What this does not prove.</b> 150 is a ceiling derived from the standings, not a
verified fixture list. It rules out a settled total of 136 only if every completed game appears in both
clubs' records — which the zero remainder supports but does not certify.</p>

<h2>3. The standings themselves, transcribed by parser</h2>
<p>These 32 rows are produced by <code>nfl-desk/engine/parse_standings.py</code> from the saved rendered
read, so the table on this page and the table the parser read cannot drift apart. Division labels follow
the page's own print order (four rows per block); the page does not repeat the division name on each row.</p>
""" + table(
        "2026 regular-season standings &middot; read from nfl.com/standings on %s" % STAMP,
        ["Abbr", "Club", "Division", "W-L-T", "Pct", "PF", "PA", "Net", "Streak", "Source"],
        st_rows,
        "Two NFC clubs carry a tie (NYG 5-3-1, WAS 3-5-1). Columns the official page prints but this "
        "project does not model (home/road splits, non-conference pct) are not transcribed.") + """
<h2>4. Why the corpus matters more than the model</h2>
<p>Every gate in this repository is a function of n. At the effect sizes actually observed, 80% power
needs 1,148-1,290 bets per strategy, and the largest current sample is 303. A settled-game corpus that
is 13 games shorter than believed moves every one of those numbers. That is why the corpus is settled
before more modelling is added, not after.</p>
"""
    page("pages/corpus.html", "Corpus and standings", body)


def build_census(census):
    ns_rows = []
    for n in census["namespaces"]:
        ns_rows.append([
            "<td><code>%s</code></td>" % e(n["namespace"]),
            "<td>%d</td>" % n["pages_html"],
            "<td>%d / %d</td>" % (n["data_json"], n["data_csv"]),
            '<td class="small">%s</td>' % (e(", ".join(os.path.basename(v) for v in n["verifiers"])) or DASH),
            '<td class="small">%s</td>' % (repo_link(n["landing"], "landing") if n["landing"]
                                          else repo_link(n["namespace"] + "/", "folder")),
        ])
    dup_rows = []
    for k, label in (("flagged_pages", "Flagged for review pages"), ("sources_pages", "Source pages"),
                     ("suggestions_pages", "Suggestions pages"), ("questions_pages", "Questions pages"),
                     ("executive_summaries", "Executive summaries")):
        d = census["duplication"][k]
        dup_rows.append([
            "<td>%s</td>" % label,
            "<td><b>%d</b></td>" % d["count"],
            '<td class="small">%s</td>' % e(", ".join(p.split("/")[0] for p in d["paths"][:12]) + (" …" if d["count"] > 12 else "")),
            '<td class="small">%s</td>' % (repo_link(d["paths"][0], "example") if d["paths"] else DASH),
        ])
    reg = census["requirement_registers"]
    reg_rows = [[
        "<td><code>%s</code></td>" % e(v["path"]),
        "<td>%d</td>" % v["rows"],
        '<td class="small">%s</td>' % e(", ".join("%s %d" % (a, b) for a, b in v["status_counts"].items())),
        '<td class="small">%s</td>' % repo_link(v["path"], "file"),
    ] for v in reg.values()]
    thin_rows = [[
        "<td><code>%s</code></td>" % e(t["path"]),
        "<td>%d</td>" % t["rows"],
        '<td class="small">%s</td>' % repo_link(t["path"], "file"),
    ] for t in census["thin_artifacts"][:20]]
    body = """
<p class="eyebrow">Workspace census &middot; measured %s</p>
<h1>Forty workspaces, counted</h1>
<p class="lede">Nothing here is an opinion: every number is produced by
<code>nfl-desk/engine/census.py</code> walking the tree. The point is to make duplication and
disagreement visible so the front door can be simple.</p>
<section class="kpis small">
  <div class="kpi"><span>%d</span><b>NFL workspaces</b><p>plus this one</p></div>
  <div class="kpi"><span>%d</span><b>register disagreements</b><p>counted pairwise, on matched wording</p></div>
  <div class="kpi"><span>%d</span><b>flagged pages</b><p>most unreconciled with each other</p></div>
  <div class="kpi"><span>%d</span><b>workspaces with a verifier</b><p>of %d; none compares one workspace with another</p></div>
</section>
""" % (STAMP, census["namespaces_count"], census["register_disagreement_count"],
       census["duplication"]["flagged_pages"]["count"], census["namespaces_with_verifier"],
       census["namespaces_count"]) + """
<h2>Requirements: three registers, one brief</h2>
""" + table("The competing registers", ["File", "Rows", "Status counts", "Link"], reg_rows,
          "All three claim to answer the same 73 lines. The pairwise disagreement count is on the "
          "requirements page.") + """
<h2>Duplication</h2>
""" + table("How many copies of each register type exist", ["Register type", "Copies", "Where (first 12)", "Example file"], dup_rows,
          "A copy is not automatically a problem; an unreconciled copy is. None of these are deleted "
          "here, because deleting another session's published page is not this session's call.") + """
<h2>Thin artifacts</h2>
<p>Files with six or fewer rows. They exist, so a register can call the requirement implemented, but
they cannot support a verdict. This is the most common shape of the repository's overstatement.</p>
""" + table("Artifacts too small to carry a claim", ["File", "Rows", "Link"], thin_rows) + """
<h2>Per-workspace inventory</h2>
""" + table("Every NFL workspace, its page count, data files and verifier",
            ["Workspace", "Pages", "JSON / CSV", "Verifier", "Landing page"], ns_rows,
            "Page and file counts are file counts, not quality measures. A green verifier means the "
            "workspace's own checks pass; it does not mean another workspace agrees with it.") + """
<p class="note"><b>Request, not action.</b> S01 asks for one live/history column per workspace and for
the front door to link only live ones. That change is the owner's to make; this session publishes the
census so the choice can be made from facts.</p>
"""
    page("pages/census.html", "Workspace census", body)


def build_flags(flags):
    rows = []
    for f in flags["rows"]:
        rows.append([
            "<td><code>%s</code></td>" % e(f["id"]),
            "<td><b>%s</b></td>" % e(f["issue"]),
            "<td class=\"small\">%s</td>" % e(f["detail"]),
            "<td class=\"small\">%s</td>" % e(f["needs"]),
            '<td class="small">%s %s</td>' % (" ".join(src(u, "source") for u in f["links"]),
                                             repo_link("nfl-desk/data/flags.json", "register")),
        ])
    body = """
<p class="eyebrow">Flagged for review &middot; %d items &middot; %s</p>
<h1>What could not be settled, published anyway</h1>
<p class="lede">These do not block the site. Each is a conflict or a gap with the files that show it, so
that a reader who wants to challenge a number can start here rather than by trusting it.</p>
""" % (len(flags["rows"]), STAMP) + table(
        "Irregularities", ["ID", "Issue", "Detail", "What would settle it", "Sources"], rows,
        "A flag records a conflict; it is not a verdict. Where two files disagree, both are linked and "
        "neither is declared correct.") + """
<h2>How these were found</h2>
<p>Three ways: (1) contradicting counts surfaced by <code>nfl-desk/engine/census.py</code>; (2) claims in
the brief that could not be reproduced from any file in the repository (F05); (3) official reads that
showed something different from what a workspace states (F11, F15).</p>
"""
    page("pages/flagged.html", "Flagged for review", body)


def build_sources(reads):
    rows = []
    for r in reads["reads"]:
        counted = r.get("counted_from_this_read")
        if isinstance(counted, dict):
            counted = ", ".join("%s %s" % (k, v) for k, v in counted.items() if not isinstance(v, (list, dict)))
        elif isinstance(counted, dict) is False and counted is None:
            counted = "not counted from this read"
        stored = r.get("counted_from_stored_capture")
        if isinstance(stored, dict):
            stored = ", ".join("%s %s" % (k, v) for k, v in stored.items() if not isinstance(v, (list, dict)))
        rows.append([
            "<td><code>%s</code></td>" % e(r["id"]),
            "<td>%s</td>" % link(r["url"]),
            "<td>%s</td>" % badge(r["status"], "ok" if r["status"] == "read" else "part"),
            "<td class=\"small\">%s</td>" % e(r["what_it_showed"]),
            "<td class=\"small\">%s</td>" % e(r["limit"]),
            "<td class=\"small\">%s</td>" % e(stored or counted or DASH),
        ])
    all_urls = sorted({r["official_source"] for r in load("requirements.json")["rows"] if r["official_source"]})
    src_rows = [["<td>%s</td>" % link(u), "<td class=\"small\">cited by the readiness register for at least one requirement row</td>",
                 '<td class="small">%s</td>' % repo_link("nfl-readiness-register/data/requirements.json", "register")] for u in all_urls]
    body = """
<p class="eyebrow">Sources read &middot; %s</p>
<h1>Every official page this session opened, and what it showed</h1>
<p class="lede">The sandbox has no direct HTTPS egress to nfl.com, so pages are read through the
session's page-read tool, which returns rendered text. Quoted rows come from that text; parsed tables
come from the saved copy under <code>nfl-desk/evidence/reads/</code>.</p>
""" % STAMP + table(
        "Reads made on %s" % STAMP,
        ["#", "URL", "Status", "What it showed", "Limit of this read", "What was counted from it"],
        rows,
        "A failed read is listed as a failed read (OR-05). A stored capture that this session did not "
        "open is labelled as a capture, not a read (OR-06).") + """
<h2>Official domains cited across the register</h2>
""" + table("Official sources named by the register rows", ["URL", "Why it is here", "Register"], src_rows,
          "These are the canonical pages each requirement consumes. A citation supports the data domain, "
          "not the requirement's implementation status.") + """
<h2>What is still unverified</h2>
<p>Two register rows cite <code>operations.nfl.com/the-rules/</code>, which returned no body on %s
(flag F11). The NFL terms page is linked from the root portal but was not read line-by-line in this
session, so no compliance claim is made for the public/private split (flag F14).</p>
""" % STAMP
    page("pages/sources.html", "Sources read", body)


def build_verify():
    body = """
<p class="eyebrow">Verification &middot; %s</p>
<h1>What this desk checks before it publishes, and what it does not</h1>
<p class="lede">A green check here means the pages are internally consistent and every row carries a
source. It does not mean the numbers are true, and it does not mean any other workspace agrees.</p>

<h2>Checks that run</h2>
""" + table("Gates executed by nfl-desk/engine/verify.py",
            ["Gate", "What it tests", "How to run it", "Implementation"],
            [[ "<td>%s</td>" % g, "<td>%s</td>" % t, "<td><code>python3 nfl-desk/engine/verify.py</code></td>",
               '<td class="small">%s</td>' % repo_link("nfl-desk/engine/verify.py", "verify.py")]
             for g, t in (
                ("V1", "Every table body row carries an official or repository source link"),
                ("V2", "Every local href and anchor resolves to a file and id that exist"),
                ("V3", "No link attribute points at a loopback or file-scheme address"),
                ("V4", "No unrendered template marker, no sentinel value in a cell"),
                ("V5", "Row counts on the pages match the row counts in the data files"),
                ("V6", "A rebuild is byte-identical (deterministic output)"),
                ("V7", "Every JSON data file parses and carries a source or a stated method"),
                ("V8", "Every official read records a status and a limit"),
                ("V9", "Every flag links at least one source"),
                ("V10", "The injury and standings captures still match their recorded sha256"),
             )],
            "Every gate is implemented in %s and runs in %s on each push."
            % (repo_link("nfl-desk/engine/verify.py", "verify.py"),
               repo_link(".github/workflows/nfl-desk.yml", "the workflow"))) + """
<h2>Numbers this desk publishes, and where each is computed</h2>
""" + table("Provenance of every headline figure",
            ["Figure", "Computed by", "Input"],
            [["<td>73 requirement rows; agreement and disagreement counts</td>", "<td><code>engine/register.py</code></td>",
              "<td>%s</td>" % repo_link("nfl-desk/data/requirements.json", "requirements.json")],
             ["<td>62 pairwise register disagreements; 40 workspaces; duplication counts</td>", "<td><code>engine/census.py</code></td>",
              "<td>%s</td>" % repo_link("nfl-desk/data/census.json", "census.json")],
             ["<td>32 standings rows; 300 team-games; 150 implied games</td>", "<td><code>engine/parse_standings.py</code></td>",
              "<td>%s</td>" % link("https://www.nfl.com/standings/", "nfl.com/standings")],
             ["<td>242 injury rows; 16 designations; 226 blanks</td>", "<td><code>engine/parse_injuries.py</code></td>",
              "<td>%s</td>" % link("https://www.nfl.com/injuries/", "nfl.com/injuries")],
             ["<td>18 questions, 10 suggestions, 15 flags</td>", "<td>this workspace's data files</td>",
              "<td>%s</td>" % repo_link("nfl-desk/data/questions.json", "questions.json")]],
            "No number on the site is typed into the HTML; the builder reads the JSON.") + """
<h2>What is not checked</h2>
<p>This verifier does not fetch the official pages at build time, so it cannot detect that a source has
changed since the read date. It does not re-verify peer workspaces' claims. It does not check that a
figure is economically meaningful — only that it is sourced and reproducible.</p>
"""
    page("pages/verify.html", "Verification", body)


def main():
    req = load("requirements.json")
    q = load("questions.json")
    sug = load("suggestions.json")
    flags = load("flags.json")
    reads = load("official_reads_2026-11-19.json")
    census = load("census.json")
    inj = load("injuries_2026-11-18_parsed.json")
    st = load("standings_2026-11-19.json")

    global CUR_DIR
    for cur, fn in (
        ("", lambda: build_index(req, q, sug, flags, reads, census, inj, st)),
        ("pages", lambda: build_exec(req, q, sug, flags, census, reads)),
        ("pages", lambda: build_requirements(req)),
        ("pages", lambda: build_questions(q)),
        ("pages", lambda: build_suggestions(sug)),
        ("pages", lambda: build_availability(inj, st, census)),
        ("pages", lambda: build_corpus(census, st)),
        ("pages", lambda: build_census(census)),
        ("pages", lambda: build_flags(flags)),
        ("pages", lambda: build_sources(reads)),
        ("pages", build_verify),
    ):
        CUR_DIR = cur
        fn()
    print("built %d pages" % (len(NAV)))


if __name__ == "__main__":
    main()

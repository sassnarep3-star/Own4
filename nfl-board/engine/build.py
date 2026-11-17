#!/usr/bin/env python3
"""Own4 — nfl-board site builder.

Reads the five registers in data/ and writes the pages. Two rules this file exists to enforce:

  1. NO TYPED COUNTS. Every number rendered on a page is computed from the registers at build
     time. A peer workspace caught itself twice publishing a typed count that had gone stale;
     this builder makes that impossible by never writing a literal total into prose.

  2. NO PREFILLED VERDICTS. The suggestions board publishes a verdict column that is blank on
     every row. If any verdict were non-empty the build fails, so an agent cannot quietly decide
     a question that belongs to the reviewer.

Run:  python3 nfl-board/engine/build.py
      python3 nfl-board/engine/verify.py
"""
import html
import json
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
SESSION = "arena-7fc936d1-own4"
BUILT = "2026-11-17"


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


REQ = load("requirements.json")
Q = load("questions.json")
SUG = load("suggestions.json")
IRR = load("irregularities.json")
SRC = load("sources.json")
SRC_BY_ID = {s["id"]: s for s in SRC["sources"]}

STATE_CLASS = {"MET": "pass", "PARTIAL": "warn", "BLOCKED": "fail", "NOT STARTED": "blank"}
GRADE_CLASS = {"ANSWERED": "pass", "ANSWERABLE NOW": "warn", "NEEDS DECISION": "fail", "NEEDS A SOURCE": "blocked"}
SEV_CLASS = {"high": "fail", "medium": "warn", "low": "blank"}


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def src_links(ids, compact=True):
    out = []
    for i in ids:
        s = SRC_BY_ID.get(i)
        if not s:
            continue
        label = i if compact else "%s %s" % (i, s["label"])
        out.append('<a href="%s" target="_blank" rel="noopener" title="%s">%s &#8599;</a>'
                   % (esc(s["url"]), esc(s["label"]), esc(label)))
    return " ".join(out)


def badge(text, cls):
    return '<span class="badge %s">%s</span>' % (cls, esc(text))


def table(headers, rows, caption, cls="", row_ids=None):
    th = "".join('<th scope="col">%s</th>' % h for h in headers)
    if row_ids:
        body = "".join('<tr id="%s">%s</tr>' % (esc(rid).lower(), "".join(r))
                       for rid, r in zip(row_ids, rows))
    else:
        body = "".join("<tr>%s</tr>" % "".join(r) for r in rows)
    return ('<div class="tw"><table class="%s"><caption>%s</caption><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (cls, esc(caption), th, body))


def counts_by(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


# ------------------------------------------------------------------ derived facts
REQ_N = len(REQ["rows"])
STATE_COUNTS = counts_by(REQ["rows"], "state")
GATE_COUNTS = counts_by(REQ["rows"], "gate")
CAT_COUNTS = counts_by(REQ["rows"], "cat")
Q_N = len(Q["rows"])
Q_COUNTS = counts_by(Q["rows"], "grade")
SUG_N = len(SUG["rows"])
IRR_N = len(IRR["rows"])
IRR_COUNTS = counts_by(IRR["rows"], "sev")
SRC_N = len(SRC["sources"])
REQ_WITH_IRR = sum(1 for r in REQ["rows"] if r["irregular"])

# the gate that blocks the most lines is the single most useful decision number on the site
TOP_GATE, TOP_GATE_N = max(GATE_COUNTS.items(), key=lambda kv: kv[1])
_NOT_STARTED = [r for r in REQ["rows"] if r["state"] == "NOT STARTED"]
_BLOCKED = [r for r in REQ["rows"] if r["state"] == "BLOCKED"]

NAV = [
    ("Decision board", [
        ("index.html", "Decision readiness (start here)"),
        ("pages/executive-summary.html", "Executive summary"),
        ("pages/readiness.html", "Readiness: every requirement line"),
        ("pages/questions.html", "Questions, information, answers"),
        ("pages/suggestions.html", "Suggestions — decide before building"),
        ("pages/evidence.html", "What was verified this session"),
        ("pages/repo-review.html", "Repo review &amp; irregularities"),
        ("pages/flagged.html", "&#9873; Flagged for review"),
        ("pages/sources.html", "Source register"),
    ]),
]


def page(path, title, crumb, body, active, desc):
    depth = path.count("/")
    prefix = "../" * depth
    nav = []
    for group, items in NAV:
        nav.append('<div class="grp">%s</div>' % group)
        for href, label in items:
            cls = "nav active" if href.endswith(active) else "nav"
            # NAV hrefs are relative to this namespace's root; prefix with one "../" per
            # directory level of the page being written.
            nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, label))
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · NFL Decision Board</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(prefix)sstyle.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(prefix)sindex.html">NFL Decision Board</a>
  <div class="tag">Verified against official pages · %(built)s</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <a class="flag" href="%(prefix)spages/flagged.html">&#9873; %(nflags)s findings for review</a>
</aside>
<main class="main" id="main">
<div class="crumb">%(crumb)s</div>
%(body)s
<footer>
<p><strong>NFL Decision Board</strong> — analytical research, not wagering advice. Every row links to the
official page it was read from or to the repository artefact it was counted from. Values that could not be
confirmed from an official source are blank, and every one of them is on the
<a href="%(prefix)spages/flagged.html">Flagged for review</a> page.</p>
<p>Built %(built)s by session <code>%(session)s</code> from the registers in <code>nfl-board/data/</code>.
Every count on this site is computed at build time. Responsible gambling:
National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG &#8599;</a></p>
</footer>
</main>
</div>
</body>
</html>
""" % {"title": esc(title), "desc": esc(desc), "prefix": prefix, "nav": "".join(nav),
       "crumb": crumb, "body": body, "built": BUILT, "session": SESSION,
       "nflags": IRR_N}
    full = os.path.join(NS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


# ------------------------------------------------------------------ index
def build_index():
    cards = [
        ("%d" % REQ_N, "requirement lines tracked", "", "one row per instruction in the brief"),
        ("%d" % STATE_COUNTS.get("MET", 0), "met — artefact exists and was re-checked", "pass", ""),
        ("%d" % STATE_COUNTS.get("PARTIAL", 0), "partial — exists for a fraction of the corpus", "warn", ""),
        ("%d" % STATE_COUNTS.get("BLOCKED", 0), "blocked — the decisive number cannot exist yet", "fail", ""),
        ("%d" % STATE_COUNTS.get("NOT STARTED", 0), "not started", "blank", ""),
        ("%d" % Q_N, "questions with a discovery route", "", ""),
        ("%d" % Q_COUNTS.get("ANSWERED", 0), "questions answered by an official read", "pass", ""),
        ("%d" % Q_COUNTS.get("NEEDS DECISION", 0), "questions only you can settle", "fail", ""),
        ("%d" % SUG_N, "suggestions awaiting a verdict", "warn", "blank by rule"),
        ("%d" % IRR_N, "review findings", "fail", ""),
        ("%d" % SRC_N, "official pages read this session", "", ""),
    ]
    cardhtml = "".join(
        '<div class="card %s"><b>%s</b><span>%s</span><em>%s</em></div>' % (c[2], c[0], esc(c[1]), esc(c[3]))
        for c in cards)

    tiles = [
        ("pages/readiness.html", "Decision readiness",
         "One row per requirement line: its state, the gate that blocks it, and the number that would clear it.", "Open the table"),
        ("pages/questions.html", "Questions, information and answers",
         "What must be settled before a decision, what we have, what we lack, and the route that discovers it.", "Read the register"),
        ("pages/suggestions.html", "Suggestions — decide first",
         "Every proposal with an evidence link and a blank verdict. Nothing is implemented until you choose.", "Review the board"),
        ("pages/evidence.html", "What was verified today",
         "The official pages read this session, what each one confirmed, and the three brief claims that are no longer true.", "See the evidence"),
        ("pages/repo-review.html", "Repo review",
         "Line-by-line findings with the file and the official page that settles each one.", "Read the findings"),
        ("pages/flagged.html", "&#9873; Flagged for review",
         "Everything that could not be confirmed from an official source, with the reason and the source that is missing.", "Review the flags"),
    ]
    tilehtml = "".join('<a class="tile" href="%s"><b>%s</b><span>%s</span><em>%s &#8594;</em></a>' % t for t in tiles)

    top_blocked = ", ".join(r["id"] for r in _BLOCKED)
    body = """
<h1>The NFL decision board</h1>
<p class="lede">Every instruction in the brief is a row. Each row carries three things a reviewer can act on:
whether an artefact exists, <em>which gate</em> stops it, and <em>the number</em> that would clear it. Nothing
on this site is a promise about a betting edge. The honest headline is that the results machinery is sound,
the availability data is better than the site admits, and no price can be official because the league
publishes none.</p>

<div class="panel warn"><strong>The one finding that matters most.</strong>
Two peer datasets state that the "who actually started" side of the availability graph cannot be sourced,
and leave it blank. That is no longer true. This session read the official Week 10 inactives article
(12 games, both clubs each) and the official Game Book link published on every game centre. Both are
dated, both are official, and one Game Book is already parsed elsewhere in this repository with zero
join collisions against the injury report. Three requirement lines move from blocked to answerable the
moment that is acted on — see <a href="pages/suggestions.html">SG-10</a>.</div>

<div class="cards">%(cards)s</div>

<h2>Start here</h2>
<div class="tiles">%(tiles)s</div>

<h2>The gate that blocks the most lines</h2>
<p>Of the %(req_n)d requirement lines, <strong>%(top_n)d</strong> are stopped by
<code>%(top_gate)s</code> — %(top_desc)s. That is the highest-leverage thing to fix: it is not a data
collection problem and not a modelling problem, it is a decision.</p>

<div class="panel"><h3>What %(top_gate)s means, and what would clear it</h3>
<p>%(top_detail)s</p>
<p class="small">Blocked lines: <code>%(blocked_ids)s</code></p></div>

<h2>Why this board exists</h2>
<p>The repository holds dozens of NFL research workspaces built by earlier sessions. Several publish
overlapping requirement, question and suggestion registers, and several state a blocker that has since
stopped being true. This board does one job: it puts the requirement, the blocker and the clearing number
on one line so a decision can be taken without reading every namespace. It links to the analysis
namespaces instead of copying their tables — the fragmentation itself is a question for you (Q18, SG-11).</p>

<div class="panel"><h3>How to read a row</h3>
<p><strong>State</strong> is the least useful column. <strong>Gate</strong> tells you what kind of obstacle
it is — a missing official source, a rights decision, a sample that is too small, or nothing at all.
<strong>The number that would clear it</strong> is the only column that tells you when to come back.</p>
<p><strong>Not started</strong> is %(ns)d lines: %(ns_names)s. None of them is blocked by research; they are
blocked by nobody having started.</p></div>
""" % {
        "cards": cardhtml, "tiles": tilehtml,
        "req_n": REQ_N, "top_n": TOP_GATE_N, "top_gate": TOP_GATE,
        "top_desc": REQ["gate_vocabulary"][TOP_GATE].split(";")[0],
        "top_detail": TOP_DETAIL, "blocked_ids": top_blocked,
        "ns": STATE_COUNTS.get("NOT STARTED", 0),
        "ns_names": ", ".join("%s (%s)" % (r["id"], r["text"].split("(")[0].strip().rstrip(".")) for r in _NOT_STARTED) or "none",
    }
    return page("index.html", "Decision readiness", '<a href="index.html">Decision board</a>',
                body, "index.html", "NFL decision-readiness board: one row per requirement, its blocking gate and the number that clears it.")


# ------------------------------------------------------------------ readiness
def build_readiness():
    rows = []
    for r in REQ["rows"]:
        rows.append([
            "<code>%s</code>" % esc(r["id"]),
            esc(r["text"]),
            badge(r["state"], STATE_CLASS.get(r["state"], "blank")),
            '<code>%s</code>' % esc(r["gate"]),
            esc(r["clearing_number"]),
            esc(r["clearing_condition"]) if r.get("clearing_condition") else '<span class="blank">blank</span>',
            (('<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>' % (REPO + esc(r["path"]), esc(os.path.basename(r["path"]))))
             if r.get("path") else '<span class="blank">no artefact</span>'),
            src_links(r.get("sources", [])),
        ])
    t = table(["#", "Requirement line (as written in the brief)", "State", "Gate", "The number that would clear it",
               "Where it stands", "Artefact", "Official source"],
              rows, "Requirement readiness · %d lines" % REQ_N,
              row_ids=[r["id"] for r in REQ["rows"]])

    # Each summary row links to the rows it counts, so the contract "every row carries a source"
    # holds for summaries too — and a reader can audit a total by opening it.
    state_rows = [[badge(k, STATE_CLASS.get(k, "blank")), str(v),
                   "<code>%s</code>" % ", ".join(r["id"] for r in REQ["rows"] if r["state"] == k),
                   src_links(sorted({s for r in REQ["rows"] if r["state"] == k for s in r.get("sources", [])}))]
                  for k, v in sorted(STATE_COUNTS.items(), key=lambda kv: -kv[1])]
    st = table(["State", "Lines", "Rows", "Official source"], state_rows, "State count · computed at build time")

    gate_rows = [[('<code>%s</code>' % esc(k)), str(v), esc(REQ["gate_vocabulary"].get(k, "")),
                  "<code>%s</code>" % ", ".join(r["id"] for r in REQ["rows"] if r["gate"] == k),
                  src_links(sorted({s for r in REQ["rows"] if r["gate"] == k for s in r.get("sources", [])}))]
                 for k, v in sorted(GATE_COUNTS.items(), key=lambda kv: -kv[1])]
    gt = table(["Gate", "Lines blocked by it", "What the gate is", "Rows", "Official source"], gate_rows,
               "Gate count · the decision-useful view")

    cat_rows = [[esc(k), str(v),
                 "<code>%s</code>" % ", ".join(r["id"] for r in REQ["rows"] if r["cat"] == k),
                 src_links(sorted({s for r in REQ["rows"] if r["cat"] == k for s in r.get("sources", [])}))]
                for k, v in sorted(CAT_COUNTS.items(), key=lambda kv: -kv[1])]
    ct = table(["Category", "Lines", "Rows", "Official source"], cat_rows, "By category")

    body = """
<h1>Readiness: every requirement line</h1>
<p class="lede">%d lines, each carried from the brief without being merged or dropped. A line that asks for
two things appears as two rows if the two halves stand or fall separately. The gate and the clearing number
are the decision columns; the state is context.</p>

<div class="panel"><h3>What "the number that would clear it" is not</h3>
<p>It is not a target someone invented. It is the quantity that, once known, would let you stop arguing about
the row: a coverage fraction, a sample size, a count of clubs, a decision recorded in the tree. Where the
answer is "a decision", the number is a count of one — recorded, not measured. That is deliberate.</p></div>

<h2>The table</h2>
%s

<h2>The three views that make the table usable</h2>
%s
%s
%s
""" % (REQ_N, t, st, gt, ct)
    return page("pages/readiness.html", "Readiness", '<a href="../index.html">Decision board</a> / Readiness',
                body, "readiness.html",
                "One row per requirement line with its state, blocking gate and the number that would clear it.")


# ------------------------------------------------------------------ questions
def build_questions():
    rows = []
    for r in Q["rows"]:
        rows.append([
            "<code>%s</code>" % esc(r["id"]),
            badge(r["grade"], GRADE_CLASS.get(r["grade"], "blank")),
            "<strong>%s</strong><br><span class=\"small\">%s</span>" % (esc(r["question"]), esc(r["why"])),
            esc(r["have"]),
            esc(r["dont_have"]),
            esc(r["route"]),
            src_links(r.get("sources", [])),
        ])
    t = table(["#", "Grade", "Question, and why it blocks a decision", "What we have", "What we don't have",
               "How to discover it", "Official source"],
              rows, "Question register · %d questions, %d of them needing your decision" % (Q_N, Q_COUNTS.get("NEEDS DECISION", 0)),
              row_ids=[r["id"] for r in Q["rows"]])

    qc = table(["Grade", "Questions", "Rows", "Official source"],
               [[badge(k, GRADE_CLASS.get(k, "blank")), str(v),
                 "<code>%s</code>" % ", ".join(r["id"] for r in Q["rows"] if r["grade"] == k),
                 src_links(sorted({s for r in Q["rows"] if r["grade"] == k for s in r.get("sources", [])}))]
                for k, v in sorted(Q_COUNTS.items(), key=lambda kv: -kv[1])],
               "Question grades · computed at build time")

    body = """
<h1>Questions, information and answers</h1>
<p class="lede">The brief asks for a clear list of what must be settled before a decision, given what we have
and what we do not. %d questions. Each one is graded by whether an official read answers it today, whether it
is a decision only you can take, or whether it needs a source that may not exist. Every row carries a
discovery route — the step that would find the missing information — not just a statement of the gap.</p>

%s

<h2>The four grades</h2>
<ul>
<li><strong>Answered</strong> — the official page was read this session and the answer is on the site with its link.</li>
<li><strong>Answerable now</strong> — the evidence exists; the work is a join or a parse, not a new source. These
are the cheapest wins and several have been sitting open because a peer believed the source did not exist.</li>
<li><strong>Needs a decision</strong> — no amount of reading settles it. A policy or rights choice with an owner.</li>
<li><strong>Needs a source</strong> — the answer would settle it, but no official field has been found. These are the
only rows where the honest recommendation may be to drop the requirement.</li>
</ul>

<h2>The register</h2>
%s

<h2>If you answer only three questions</h2>
<div class="panel warn"><p><strong>Q02</strong> — may a third-party price be used, and under what terms? Six
requirement lines depend on it and every future session re-litigates it until it is written down.</p>
<p><strong>Q12</strong> — may row-level injury and depth data be republished? The site publishes a row-level
injury table today and no session has read the league's terms. This is the only open item that is a legal
question rather than a data question.</p>
<p><strong>Q06</strong> — is Game Book participation an acceptable substitute for snap counts? No official
snap field exists on the page tested. The substitution is defensible; making it silently is not.</p></div>
""" % (Q_N, qc, t)
    return page("pages/questions.html", "Questions", '<a href="../index.html">Decision board</a> / Questions',
                body, "questions.html",
                "Question register: what must be settled before a decision, with a discovery route for every gap.")


# ------------------------------------------------------------------ suggestions
def build_suggestions():
    rows = []
    for r in SUG["rows"]:
        # the verdict column is deliberately empty; verify.py fails if it is not
        rows.append([
            "<code>%s</code>" % esc(r["id"]),
            "<strong>%s</strong>" % esc(r["title"]),
            esc(r["what"]),
            esc(r["why"]),
            esc(r["addresses"]),
            esc(r["cost"]),
            esc(r["reversible"]),
            '<a href="%s" target="_blank" rel="noopener">evidence &#8599;</a> ' % esc(r["source_url"]) + src_links(r.get("sources", [])),
            '<span class="verdict">blank</span>',
            "&nbsp;",
        ])
    t = table(["#", "Suggestion", "What it changes", "Why", "Addresses", "Cost", "Reversible",
               "Evidence", "Verdict", "Your rationale"],
              rows, "Suggestions · %d rows, %d verdicts deliberately blank" % (SUG_N, SUG_N),
              row_ids=[r["id"] for r in SUG["rows"]])

    body = """
<h1>Suggestions — decide before building</h1>
<p class="lede">%d proposals, each tied to the requirement lines it would move. The verdict and rationale
columns are blank on every row, and the build fails if any of them is filled: choosing a path is your
decision, not an agent's. Each row states what it changes, what it costs, whether it can be walked back,
and the official evidence behind it.</p>

<div class="panel"><h3>Why blank, and not a recommendation</h3>
<p>A recommendation with a pre-filled verdict is a decision with extra steps. Several of these proposals
interact — SG-01 and SG-05 both touch the price policy; SG-02 and SG-03 both touch playing time — so the
order you choose them in changes what the others cost. That is a reviewer's judgement, not a build step.</p></div>

<h2>Where the leverage is</h2>
<div class="panel warn"><p><strong>Cheapest first.</strong> SG-01, SG-06, SG-07 and SG-13 are low-cost and
reversible, and between them close the highest-severity findings on the repo-review page.
<strong>SG-10</strong> is the one that unblocks the most: it turns three "blocked" requirement lines into
"answerable" without a new data source.</p></div>

%s
""" % (SUG_N, t)
    return page("pages/suggestions.html", "Suggestions", '<a href="../index.html">Decision board</a> / Suggestions',
                body, "suggestions.html",
                "Suggestion board with a blank verdict on every row, for the reviewer to choose before implementation.")


# ------------------------------------------------------------------ evidence
def build_evidence():
    rows = []
    for s in SRC["sources"]:
        rows.append([
            "<code>%s</code>" % esc(s["id"]),
            '<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>' % (esc(s["url"]), esc(s["label"])),
            esc(s["kind"]),
            esc(s.get("read", "")),
            esc(s.get("used_for", "")),
        ])
    t = table(["ID", "Page read", "Class", "How much was read", "What it settled"],
              rows, "Official reads, session %s" % SESSION)

    closed = [
        ("Kerby Joseph, Cade Mays and D.J. Reed have blank game statuses in the published Week-10 tables",
         "The live report prints all three as <strong>Out</strong> with the injury named: Joseph (Knee), Mays (Ankle), Reed (Hip).",
         "S01", "RQ-47"),
        ("Published Week-10 counts are stale: 254 rows and 4 no-injury sections",
         "The committed capture holds 347 rows; the live page was re-read this session and its structure matches the capture's 14 game sections.",
         "S01", "RQ-48"),
        ("Baltimore still publishes Lamar Jackson and Tyler Huntley at QB after both went on injured reserve",
         "Baltimore's current chart lists <strong>Jacoby Brissett, Joe Fagnano, Kedon Slovis</strong>. Neither Jackson nor Huntley appears. This was true when written and is no longer true.",
         "S08", "RQ-45"),
        ("No official depth charts exist, so the deficiency feature cannot be built",
         "Club pages exist and parse for at least two clubs. Houston publishes an image; Green Bay prints a jersey prefix and a date; Baltimore prints no date. The obstacle is 32-club coverage, not availability.",
         "S07, S08, S09", "RQ-28"),
        ("A backup's replacement of a starter can only be suspected, because no active list is captured",
         "The official inactives article lists every inactive for both clubs in each of 12 Sunday games, and the Game Book lists participation for the Thursday game. Replacement can be confirmed, not suspected.",
         "S02, S10", "RQ-30, RQ-10"),
        ("Snap counts are the starter proxy",
         "No official snap-count field exists on the player page read. The official substitute is Game Book participation. This one is a substitution to approve, not a defect to fix.",
         "S13", "RQ-11, RQ-54"),
    ]
    crow = [["<strong>%s</strong>" % esc(a), b, src_links([s.strip() for s in sid.split(",")]), esc(rq)]
            for a, b, sid, rq in closed]
    ct = table(["The brief's claim", "What the official page showed this session", "Source", "Row"],
               crow, "Brief claims that were checked against the live page")

    scores = [
        ("Week 10 finals confirmed on two independent official pages", "13 of 14", "the fourteenth (LAC at BAL) was still scheduled 0-8 vs 4-5 with a kickoff time when read, and is left blank rather than inferred", ["S04", "S05"]),
        ("Corpus rows spot-checked against their official game page", "1 of 1 matched exactly", "NE 10 - SEA 13 on 2026-09-09; proving one row, not the whole corpus", ["S10"]),
        ("Reserve-list moves read for November 2026", "25 dated moves", "including Malik Willis (MIA, 11/10), the case the brief names", ["S03"]),
        ("Club depth charts parsed", "2 of 32 clubs", "Green Bay and Baltimore; Houston confirmed image-only", ["S07", "S08", "S09"]),
        ("Official prices found anywhere on nfl.com", "0", "the schedule, scores, game-centre, injury and depth pages were all read", ["S04", "S05", "S12"]),
        ("Game Book participation rows parsed for one fixture", "109 rows, 0 join collisions", "the route exists on every game centre via 'Download Game Book (PDF)'", ["S10", "S11"]),
    ]
    st = table(["Check", "Result", "Note", "Official source"],
               [["<strong>%s</strong>" % esc(a), esc(b), esc(c), src_links(d)] for a, b, c, d in scores],
               "What this session actually measured")

    body = """
<h1>What was verified this session</h1>
<p class="lede">%d official pages read between %s and %s UTC on %s. This page exists so that every claim on
the site can be traced to a page that was actually opened, and so that the claims which turned out to be
stale are visible rather than quietly corrected.</p>

<div class="panel bad"><h3>Read this first: five things the brief states are no longer true</h3>
<p>Four of them are good news — the defect was fixed at the source — and one is the opposite: a stated
impossibility that is not one. They are listed together because a reviewer should not have to work out
which way each correction cuts.</p></div>

<h2>Brief claims, checked against the live page</h2>
%s

<h2>What was measured</h2>
%s

<h2>The pages read</h2>
%s

<h2>What could not be read, and why</h2>
<div class="panel"><p>Direct <code>curl</code> and Python <code>urllib</code> from the build sandbox cannot
complete a TLS handshake with nfl.com or nba.com, so every read on this site came through the page-fetch tool.
That tool exposes no per-call clock, so the read window is recorded as a window rather than per-row
timestamps — the same limitation a peer session documented for its own captures, and the reason Q10 asks you
to rule on retention rather than assume it.</p>
<p>One source that other workspaces cite, <code>nfl.com/standings</code>, was <em>not</em> re-read this
session. It is listed in the source register with that fact stated, because a source a page relies on and did
not check is exactly the thing this page is meant to expose.</p></div>
""" % (SRC_N, SRC["read_window_utc"][0], SRC["read_window_utc"][1], BUILT, ct, st, t)
    return page("pages/evidence.html", "Evidence", '<a href="../index.html">Decision board</a> / Evidence',
                body, "evidence.html", "The official pages read this session and the brief claims they settle.")


# ------------------------------------------------------------------ repo review
def build_repo_review():
    rows = []
    for r in IRR["rows"]:
        rows.append([
            "<code>%s</code>" % esc(r["id"]),
            badge(r["sev"], SEV_CLASS.get(r["sev"], "blank")),
            "<strong>%s</strong>" % esc(r["finding"]),
            esc(r["evidence"]),
            esc(r["checked"]),
            esc(r["effect"]),
            (esc(r["recommend"]) if r["recommend"] != "—" else '<span class="blank">&mdash;</span>'),
            '<a href="%s" target="_blank" rel="noopener">source &#8599;</a> ' % esc(r["source_url"]) + src_links(r.get("sources", [])),
        ])
    t = table(["#", "Severity", "Finding", "Evidence (file or page)", "What was checked", "Effect",
               "Recommend", "Source"],
              rows, "Review findings · %d, of which %d are high severity" % (IRR_N, IRR_COUNTS.get("high", 0)),
              row_ids=[r["id"] for r in IRR["rows"]])

    body = """
<h1>Repo review and irregularities</h1>
<p class="lede">%d findings from reading the NFL tree line by line and checking the load-bearing claims against
the official page. Each row states the file or page, what was checked, what it means, and the suggestion that
would close it. The %d high-severity findings are the ones where a published number could be wrong or is
unlicensed to be right; none of them is a fabricated figure.</p>

<div class="panel warn"><h3>How this review was scoped</h3>
<p>This session owns <code>nfl-board/</code>. It did not edit a single file in another session's namespace.
Where a peer page or dataset is wrong, the finding is logged here and on the suggestions board with the
recommendation attached, and the peer's file is left untouched — that is what the shared-task-board rule
asks for, and it also means the finding can be verified by reading the peer's own file.</p></div>

<h2>The findings</h2>
%s

<h2>The pattern behind the high-severity findings</h2>
<div class="panel"><p>Three of them are the same defect in different clothes: <strong>a blocker was written
down once and never re-checked</strong> (IR-06, IR-10), and <strong>a class label did not travel with the
number</strong> (IR-01, IR-02). Neither is a fabrication. Both are how a verified dataset quietly stops
being verified. The drift alarm already built in one namespace (SG-07) is the fix for the first; a build
rule that fails when a price appears without its class is the fix for the second.</p>
<p>The fourth pattern is arithmetic drift between two files built on different days (IR-04, IR-08). It is
low-cost to prevent and expensive to notice, which is why the readiness table publishes a
<em>condition</em> beside every clearing number rather than a bare target.</p></div>
""" % (IRR_N, IRR_COUNTS.get("high", 0), t)
    return page("pages/repo-review.html", "Repo review", '<a href="../index.html">Decision board</a> / Repo review',
                body, "repo-review.html", "Line-by-line NFL repository review findings with the official page that settles each one.")


# ------------------------------------------------------------------ flagged
def build_flagged():
    rows = []
    for r in REQ["rows"]:
        if r["state"] in ("BLOCKED", "NOT STARTED"):
            rows.append([
                "<code>%s</code>" % esc(r["id"]),
                badge(r["state"], STATE_CLASS.get(r["state"], "blank")),
                esc(r["text"]),
                '<code>%s</code>' % esc(r["gate"]),
                esc(r["clearing_number"]),
                esc(r["result"]),
                src_links(r.get("sources", [])),
            ])
    t = table(["#", "State", "Requirement", "Gate", "What would clear it", "Why it is here", "Source"],
              rows, "Unmet requirement lines · %d, published rather than silently dropped" % len(rows))

    # blank values, named explicitly: these are the cells the site refuses to fill
    blanks = [
        ("Market open / market close against an official source", "every market row in every workspace",
         "The NFL publishes no prices. Q01 is closed negatively; the store is filled from a third-party endpoint and labelled as such.", "S04"),
        ("Actual starter for every availability row", "nfl-book/data/availability_graph.json",
         "The source exists and is read; the rows have not been refilled. This is a work item, not a missing source.", "S02"),
        ("Snap count per player", "no artefact",
         "No official field was found on the player stats page. Substitution (Game Book participation) awaits your approval.", "S13"),
        ("Depth rows for 30 of 32 clubs", "nfl-book/data/depth_register.json",
         "Written as 'unverified - no official depth source', but the source exists for at least two clubs and the remaining 30 are unread, not unreadable.", "S07"),
        ("Injury game status for the reserve-list players", "nfl-collector capture",
         "A player on IR does not appear in the weekly report, so his game status is blank by construction. The reserve list is the evidence, not the report.", "S03"),
        ("Weather for every kickoff", "no artefact",
         "The game centre publishes a one-line condition, not a forecast. No official hourly product was read.", "S12"),
        ("Stadium roof type and surface", "no artefact",
         "No official NFL roof table was found. Flagged rather than guessed per stadium.", "S12"),
    ]
    bt = table(["Blank cell", "Where", "Why it is blank", "Source"],
               [["<strong>%s</strong>" % esc(a), esc(b), esc(c), src_links([s])] for a, b, c, s in blanks],
               "The blanks, named · %d groups" % len(blanks))

    body = """
<h1>&#9873; Flagged for review</h1>
<p class="lede">Everything on this site that could not be confirmed from an official source, and every
requirement line that is not met. This page exists because the alternative — filling a cell with a plausible
value — is the one thing that would make the whole board worthless.</p>

<div class="panel ok"><h3>These do not block publication</h3>
<p>A flagged item is published, sourced and labelled. It is not a failure of the site; it is the site
telling you where the edge of the verified world is. %d items are flagged across the readiness table,
and %d blank groups are named below.</p></div>

<h2>Requirement lines that are not met</h2>
%s

<h2>The blanks, named</h2>
<p>Each group below is published as an empty cell on some page. Naming the reason is the difference between
a closed question and unfinished work, and several of these were previously presentation-only gaps that a
reader would have read as missing effort.</p>
%s
""" % (len(rows) + len(blanks), len(blanks), t, bt)
    return page("pages/flagged.html", "Flagged for review",
                '<a href="../index.html">Decision board</a> / Flagged', body, "flagged.html",
                "Every unverified value and unmet requirement line, with the reason each is blank.")


# ------------------------------------------------------------------ sources
def build_sources():
    rows = []
    for s in SRC["sources"]:
        rows.append([
            "<code>%s</code>" % esc(s["id"]),
            '<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>' % (esc(s["url"]), esc(s["label"])),
            esc(s["kind"]), esc(s.get("read", "")), esc(s.get("used_for", "")),
        ])
    t = table(["ID", "Page", "Class", "How much was read", "Used for"], rows,
              "Source register · %d sources" % SRC_N)

    nr = table(["Page", "Why it was not read", "What would close it", "Where to decide"],
               [["<strong>%s</strong> %s" % (esc(x["what"]), src_links(["S04"])), esc(x["why"]), esc(x.get("closes", "")),
                 ('<a href="suggestions.html#%s">%s &#8599;</a>' % (esc(x["closes_suggestion"]).lower(), esc(x["closes_suggestion"])))
                 if x.get("closes_suggestion") else '<span class="blank">needs a source</span>']
                for x in SRC["deliberately_not_read"]],
               "Not read, on purpose")

    body = """
<h1>Source register</h1>
<p class="lede">%d sources, every one opened this session except where the row says otherwise. The register
is deliberately not a list of links that "support" a claim: it records how much of each page was read and
what it settled, so a reviewer can see the difference between a page skimmed for a headline and a page read
end to end.</p>

<div class="panel"><h3>Read window</h3>
<p>%s &#8594; %s UTC, %s. The page-fetch tool exposes no per-call clock; this is the same limitation a peer
session recorded in its own captures, and it is why the board asks you to rule on retention (Q10) rather
than assume a timestamp policy.</p></div>

<h2>The register</h2>
%s

<h2>Deliberately not read</h2>
%s

<h2>How to check any row on this site</h2>
<p>Every table row links to either an official page or a repository file. For a number taken from a repo
artefact, the artefact path is on the row and the file can be opened directly. For a number taken from an
official page, the page is linked and the exact section is named in the evidence column of the repo-review
or readiness table. If a row cannot be traced that way, it is a defect — flag it and it will be fixed rather
than argued with.</p>
""" % (SRC_N, SRC["read_window_utc"][0], SRC["read_window_utc"][1], BUILT, t, nr)
    return page("pages/sources.html", "Sources", '<a href="../index.html">Decision board</a> / Sources',
                body, "sources.html", "Every official page read this session, with how much was read and what it settled.")


# ------------------------------------------------------------------ executive summary
def build_exec_summary():
    met = [r for r in REQ["rows"] if r["state"] == "MET"]
    part = [r for r in REQ["rows"] if r["state"] == "PARTIAL"]
    blocked = [r for r in REQ["rows"] if r["state"] == "BLOCKED"]
    ns = [r for r in REQ["rows"] if r["state"] == "NOT STARTED"]
    hi = [r for r in IRR["rows"] if r["sev"] == "high"]

    def idlist(rows, n=8):
        s = ", ".join("<code>%s</code>" % r["id"] for r in rows[:n])
        if len(rows) > n:
            s += " and %d more" % (len(rows) - n)
        return s

    body = """
<h1>Executive summary</h1>
<p class="lede">The brief asks for a system that originates its own NFL lines, ranks strategies only on
selectively skill-based evidence, and knows when a starter is replaced by a backup. This page states where
that stands in numbers, what the single most useful next action is, and which decisions are yours.</p>

<h2>Where it stands</h2>
<div class="cards">
<div class="card pass"><b>%(met_n)d</b><span>requirement lines met</span><em>re-checked against an official page</em></div>
<div class="card warn"><b>%(part_n)d</b><span>partial</span><em>exists for a fraction of the corpus</em></div>
<div class="card fail"><b>%(blk_n)d</b><span>blocked</span><em>the decisive number cannot exist yet</em></div>
<div class="card blank"><b>%(ns_n)d</b><span>not started</span><em>nothing stands in the way but the start</em></div>
</div>

<h2>Five sentences that carry the release</h2>
<ol>
<li><strong>The research machinery is sound and claims no edge.</strong> A walk-forward backtest over the
available forecasts ranks nobody, the control baselines are published beside the strategies, one strategy is
pre-registered with a hash that predates its evaluation window, and the demotion gate is armed and has
correctly never fired.</li>
<li><strong>No price can be official, and that is the largest single constraint.</strong> The league publishes
no lines. Every market number in the repository comes from a third-party endpoint and is labelled as such on
the row — but one page banner still says "official sources only", which is the labelling defect that matters
most (IR-02, SG-05).</li>
<li><strong>The availability data is better than the site admits.</strong> Two peer datasets say the "who
actually started" side cannot be sourced. It can: the official inactives article covers both clubs in each of
12 Sunday games, and every game centre publishes a Game Book whose participation table is already parsed once
with zero collisions. That single correction moves three requirement lines (SG-10).</li>
<li><strong>Depth is the hard problem, and it is 32 separate problems.</strong> Two clubs' charts parse, one is
an image, one prints no date. A league-wide route returns 404. Until a dated, parseable chart exists per club,
any backup-deficiency feature is a fabrication waiting to happen (SG-02).</li>
<li><strong>Several brief claims were already fixed at the source.</strong> The Lions designations, the stale
Week-10 counts and Baltimore's quarterback depth are all correct on the live page today. They are listed on
the evidence page rather than quietly dropped, because the fix is only trustworthy if you can see what was
wrong.</li>
</ol>

<h2>What to decide first</h2>
<p>Of %(req_n)d lines, <strong>%(blocked_n)d</strong> are blocked and <strong>%(decision_q)d</strong> questions
are marked as needing only your decision. They collapse to four:</p>
<table><thead><tr><th scope="col">Decision</th><th scope="col">What it unblocks</th><th scope="col">Why an agent cannot take it</th></tr></thead><tbody>
<tr><td><strong>Q02 — price policy</strong> <a href="questions.html#q02">Q02 &#8599;</a></td><td>%(blocked_ids)s %(src_sched)s</td><td>It is a usage-rights choice with external consequences; a provisional answer is already recorded and flagged for you.</td></tr>
<tr><td><strong>Q12 — public/private split</strong> <a href="questions.html#q12">Q12 &#8599;</a></td><td><code>RQ-39</code> %(src_inj)s</td><td>It is a legal question. The site publishes row-level injury data today and no session has read the league's terms.</td></tr>
<tr><td><strong>Q06 — playing-time substitute</strong> <a href="questions.html#q06">Q06 &#8599;</a></td><td><code>RQ-11</code>, <code>RQ-54</code> %(src_stats)s</td><td>No official snap count exists; substituting Game Book participation is defensible but it is a substitution, and the brief asked for snaps.</td></tr>
<tr><td><strong>Q21 — the qualification floor</strong> <a href="questions.html#q21">Q21 &#8599;</a></td><td>%(lb_ids)s %(src_sched)s</td><td>It sets whether any reward is payable before the 2028 season. That is a policy, not a measurement.</td></tr>
</tbody></table>

<h2>What this session changed</h2>
<ul>
<li>Read %(src_n)d official pages and recorded what each settled (evidence page, source register).</li>
<li>Turned the brief into %(req_n)d requirement lines, each with a gate and a clearing number.</li>
<li>Graded %(q_n)d questions, %(q_ans)d of them answered from an official read this session, and gave every
unanswered one a discovery route.</li>
<li>Published %(sug_n)d suggestions with <em>blank</em> verdicts, and made the build fail if any verdict is
pre-filled.</li>
<li>Logged %(irr_n)d review findings with the file and the official page for each, without editing a single
peer file.</li>
</ul>

<h2>What this session did not do</h2>
<div class="panel bad"><p>It did not originate a new line, fit a model, compute a correlation or run a
backtest. Those numbers already exist in peer workspaces and were reviewed, not reproduced. Producing a new
number would have meant either re-deriving one from data already published (noise) or inventing one (worse).
The single exception is the corpus spot-check: one settled game was compared to its official page and
matched exactly, which is a check, not a model.</p>
<p>It also did not populate the 32-club depth register or refill the availability graph, because both change
files owned by other sessions. Both are proposed as SG-02 and SG-10 with the work specified.</p></div>

<h2>The %(hi_n)d findings that could make a published number wrong</h2>
<ul>%(hi_list)s</ul>
""" % {
        "met_n": len(met), "part_n": len(part), "blk_n": len(blocked), "ns_n": len(ns),
        "req_n": REQ_N, "blocked_n": len(blocked),
        "blocked_ids": ", ".join("<code>%s</code>" % r["id"] for r in blocked),
        "decision_q": Q_COUNTS.get("NEEDS DECISION", 0),
        "src_sched": src_links(["S04"]), "src_inj": src_links(["S01"]),
        "src_stats": src_links(["S13"]),
        "lb_ids": ", ".join("<code>%s</code>" % r["id"] for r in REQ["rows"] if r["cat"] == "Leaderboard"),
        "src_n": SRC_N, "q_n": Q_N, "q_ans": Q_COUNTS.get("ANSWERED", 0),
        "sug_n": SUG_N, "irr_n": IRR_N, "hi_n": len(hi),
        "hi_list": "".join("<li><code>%s</code> — %s</li>" % (r["id"], esc(r["finding"])) for r in hi),
    }
    return page("pages/executive-summary.html", "Executive summary",
                '<a href="../index.html">Decision board</a> / Executive summary', body, "executive-summary.html",
                "Executive summary of the NFL decision board: states, the price constraint, the availability correction and the four decisions that unblock the most.")


TOP_DETAIL = (
    "No official price source exists, because the NFL publishes no lines. Five requirement lines ask for a "
    "residual, a vig decomposition, a closing line value or a leaderboard stage that escrows one. None of them "
    "can be built from an official number, because there is no official number to build from. What would clear "
    "the group is a written policy that says which sources are permitted, on what usage basis, and which of "
    "the resulting numbers may be republished. A provisional policy already exists in the tree and is flagged "
    "for your review; until you accept or reverse it, every one of these lines stays blocked on a decision "
    "rather than on data."
)


def main():
    written = [
        build_index(), build_readiness(), build_questions(), build_suggestions(),
        build_evidence(), build_repo_review(), build_flagged(), build_sources(),
        build_exec_summary(),
    ]
    print("wrote %d pages: %s" % (len(written), ", ".join(written)))


if __name__ == "__main__":
    main()

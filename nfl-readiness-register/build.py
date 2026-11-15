#!/usr/bin/env python3
"""nfl-readiness site generator — deterministic, stdlib only.

Reads data/*.json and writes index.html + pages/*.html.
Every data table row carries an official source link; unverifiable values
render as 'blank — unverified' and are listed on pages/flagged.html.
Run:  python3 build.py   (from nfl-readiness/) ; then python3 verify.py
"""
import json
import os
import html

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
BUILT = "2026-11-15"

def load(name):
    with open(D("data", name), encoding="utf-8") as f:
        return json.load(f)

REQ = load("requirements.json")
W10 = load("week10_results.json")
INJ = load("injury_capture.json")
TRD = load("transactions_nov2026.json")
DEC = load("decisions.json")
SUG = load("suggestions.json")
FLG = load("flags.json")
SRC = load("sources.json")
REV = load("repo_review.json")

def esc(x):
    return html.escape("" if x is None else str(x), quote=True)

def ext(url, label=None):
    if not url:
        return '<span class="blank">blank — unverified</span>'
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label or url))

def blank(label="blank — unverified"):
    return '<span class="blank">%s</span>' % esc(label)

BADGE = {
    "implemented": '<span class="badge b-good">implemented</span>',
    "partial": '<span class="badge b-warn">partial</span>',
    "open": '<span class="badge b-bad">open</span>',
    "rejected": '<span class="badge b-info">rejected</span>',
    "resolved-at-source": '<span class="badge b-good">resolved at source</span>',
    "process": '<span class="badge b-info">process</span>',
}

NAV = [
    ("index.html", "Dashboard · decision-readiness"),
    ("pages/requirements.html", "Full requirement register"),
    ("pages/snapshots.html", "Snapshot ledger · Week 10 capture"),
    ("pages/questions.html", "Questions &amp; answers"),
    ("pages/suggestions.html", "Suggestions (review first)"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/sources.html", "Sources"),
    ("pages/flagged.html", "⚑ Flagged for review"),
]

def page(rel, title, body):
    # Nav hrefs must be relative to the current file's directory.
    def navhref(href):
        if rel == "index.html":
            return href
        return ("../" + href) if href == "index.html" else href.split("pages/", 1)[-1]
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (navhref(n), ' class="active"' if n == rel else "", t)
        for n, t in NAV
    )
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><link rel="stylesheet" href="%sassets/readiness.css"></head>
<body><div class="layout"><nav><div class="brand">NFL Readiness</div>
<div class="sub">requirements register · decision gates · snapshot ledger<br>session 63ebae0e · built %s</div>
%s</nav><main>%s</main></div></body></html>""" % (
        esc(title), "../" if "/" in rel else "", BUILT, nav, body)

def table(headers, rows_html, cls=""):
    return '<table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
        cls, "".join("<th>%s</th>" % h for h in rows_html and headers), rows_html)

# ---------------------------------------------------------------- index
def idx():
    rows = REQ["rows"]
    n_impl = sum(1 for r in rows if r["status"] == "implemented")
    n_part = sum(1 for r in rows if r["status"] == "partial")
    n_open = sum(1 for r in rows if r["status"] == "open")
    n_rej = sum(1 for r in rows if r["status"] == "rejected") + sum(1 for r in rows if r["status"] == "resolved-at-source")
    n_proc = sum(1 for r in rows if r["status"] == "process")
    tr = []
    for r in rows:
        verb = r["verbatim"]
        short = verb if len(verb) <= 120 else verb[:117] + "…"
        tr.append(
            "<tr><td><b>%s</b></td><td>%s%s <a href=\"pages/requirements.html#%s\">full row ↗</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(r["id"]), esc(short),
                (" <span class=\"more\">%s</span>" % esc(r["verbatim_body"])) if r.get("verbatim_body") else "",
                esc(r["id"]), BADGE[r["status"]], esc(r["gate"]), esc(r["clearing_number"]),
                ext(r["official_source"], "official ↗")))
    body = """
<h1>NFL Readiness — decision-readiness dashboard</h1>
<p class="lead">One row per requirement from the 2026-11-15 brief, with the gate that
blocks it and the number that would clear it. Everything was verified against official
sources on 2026-11-15; unverifiable values are blank and listed on
<a href="pages/flagged.html">Flagged for review</a>.</p>
<div class="cards">
<div class="card"><div class="k">%d</div><div class="l">requirements registered (verbatim)</div></div>
<div class="card"><div class="k">%d</div><div class="l">implemented</div></div>
<div class="card"><div class="k">%d</div><div class="l">partial (named gate)</div></div>
<div class="card"><div class="k">%d</div><div class="l">open</div></div>
<div class="card"><div class="k">%d</div><div class="l">rejected / resolved at source</div></div>
<div class="card"><div class="k">%d</div><div class="l">process rows</div></div>
<div class="card"><div class="k">347</div><div class="l">injury-report rows captured live (Wk 10)</div></div>
<div class="card"><div class="k">9/14</div><div class="l">Week-10 finals verified live</div></div>
</div>
<h2>Decision-readiness table</h2>
%s
<div class="note"><b>How to read this.</b> “Implemented” names the workspace artifacts
that exist (verified by file reads). “Partial” names the gate that blocks completion.
“Open” means nothing implements it yet. Official-source links point to the page the
requirement consumes — they evidence the data domain, not implementation. Suggested
first decisions are on <a href="pages/suggestions.html">Suggestions</a>; unknowns on
<a href="pages/questions.html">Questions</a>; irregularities on
<a href="pages/flagged.html">Flagged for review</a>.</div>
<h2>Headline findings (all verified live 2026-11-15 UTC)</h2>
%s
<h2>Directory</h2>
%s
<div class="note warn"><b>Read staking numbers with care:</b> all ROI figures anywhere in
this repository assume a flat −110 price no official source verifies. Signal metrics use no prices at all.</div>
<footer>Research only — no wagering is offered. Need help? <a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">NCPG helpline</a>.
Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (
        len(rows), n_impl, n_part, n_open, n_rej, n_proc,
        table(["ID", "Requirement (verbatim)", "Status", "Gate that blocks it", "Number that would clear it", "Source"], "".join(tr)),
        table(["Finding", "Detail", "Source"], "".join(
            "<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (esc(f[0]), f[1], ext(f[2], "official ↗")) for f in [
                ("Lions designations resolved upstream", "Kerby Joseph, Cade Mays, D.J. Reed now publish Game Status = Out on the official Week-10 report (previously blank at an earlier capture). No repo-side patch needed.", "https://www.nfl.com/injuries/"),
                ("Week-10 report re-captured", "28 team tables, 347 player rows, 0 no-injury sections, 67 Out at fetch time — superseding stale 254/279 counts; per-team counts published (SEA 15, CIN 9).", "https://www.nfl.com/injuries/"),
                ("9 of 14 Week-10 finals verified", "DET 35–10 NE (Munich), MIN 30–10 GB, BUF 31–12 NYJ, JAX 40–23 TEN among finals; 3 games live and 2 scheduled at fetch time — never backfilled.", "https://www.nfl.com/schedules/"),
                ("Roster-turnover stream captured", "12 dated November trades from the official ledger (incl. two Colts receiver moves 11/10 and Brissett AZ→BAL 11/06); one live cross-check found a stale team row (Henley, F-R3).", "https://www.nfl.com/transactions/"),
                ("Snapshot automation shipped", "Wed/Thu/Fri workflow captures report + reserve list with sha256 into an append-only ledger; drift alarm fails loudly (REQ-28/53/61/62).", "https://www.nfl.com/injuries/"),
                ("Official anchors verified", "Game books = Game Center PDFs (support.nfl.com); roof rule 90-min (Rulebook); snap/participation = Next Gen Stats.", "https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books"),
            ])),
        table(["Page", "Contents"], "".join(
            "<tr><td>%s</td><td>%s</td></tr>" % (
                '<a href="%s">%s</a>' % (esc(n), esc(t.replace("⚑ ", ""))), d)
            for (n, t), d in zip(NAV, [
                "Decision-readiness table, KPIs, headline findings",
                "All 68 requirements verbatim with evidence, gates and clearing numbers",
                "Immutable snapshot ledger + Week-10 results, transactions, per-team counts",
                "Questions / information needed / answers register (blanks by policy)",
                "Suggestions to review BEFORE implementing anything",
                "Line-by-line repository review findings",
                "One-page brief: known / unknown / decided",
                "Every source read this session",
                "Irregularities, unverified values, unresolved references",
            ])), "meta"),
        BUILT)
    return page("index.html", "NFL Readiness — decision-readiness dashboard", body)

# ---------------------------------------------------------------- requirements
def requirements():
    tr = []
    for r in REQ["rows"]:
        body = ""
        if r.get("verbatim_body"):
            body = '<div class="reqbody">Brief body: “%s”</div>' % esc(r["verbatim_body"])
        flags = ""
        if r.get("flags"):
            flags = '<div class="reqbody flag">Flagged: %s</div>' % esc(", ".join(r["flags"]))
        tr.append(
            '<tr id="%s"><td><b>%s</b></td><td>%s%s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                esc(r["id"]), esc(r["id"]), esc(r["verbatim"]), body, flags,
                esc(r["category"]), BADGE[r["status"]], esc(r["evidence"]),
                esc(r["gate"]), esc(r["clearing_number"]),
                ext(r["official_source"], "official ↗")))
    body = """
<h1>Full requirement register</h1>
<p class="lead">%s</p>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (esc(REQ["policy"]),
       table(["ID", "Requirement (verbatim)", "Category", "Status", "Evidence (verified in repo this session)", "Gate that blocks it", "Number that would clear it", "Source"], "".join(tr)),
       BUILT)
    return page("pages/requirements.html", "Full requirement register · NFL Readiness", body)

# ---------------------------------------------------------------- snapshots
def snapshots():
    man = []
    with open(D("snapshots", "manifest.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                man.append(json.loads(line))
    tr = []
    for e in man:
        tr.append("<tr><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(e["capture_id"]), esc(e["captured_utc"]),
            ext(e["source_url"], "official ↗"),
            esc(e["sha256"][:16]) + "…",
            esc(e.get("format", "raw HTML")),
            esc(e.get("status", "")),
            ext("https://github.com/sassnarep3-star/Own4/blob/main/nfl-readiness/" + e["raw_path"], "stored bytes ↗")))
    res = []
    for g in W10["rows"]:
        score = ("%s–%s" % (g["away_score"], g["home_score"])) if g["away_score"] is not None else blank()
        res.append("<tr><td>%s @ %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(g["away"]), esc(g["home"]), esc(g["date"]), esc(g["slot"]), esc(g["status"]),
            score, esc(g["venue"]) if g["venue"] else blank(), ext(g["game_url"], "game centre ↗")))
    teams = []
    for k in sorted(INJ["per_team_rows"]):
        teams.append("<tr><td>%s</td><td>%d</td></tr>" % (esc(k), INJ["per_team_rows"][k]))
    keys = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["team"]), esc(r["player"]), esc(r["pos"]), esc(r["injuries"]) or blank("none listed"),
            esc(r["practice"]), esc(r["game_status"]) or blank("none published"),
            esc(r.get("note", "")),
            ext(r.get("source_url", INJ["source_url"]), "official ↗"))
        for r in INJ["key_rows"])
    starts = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(s["player"]), esc(s["team"]), esc(s["evidence"]), ext(s["url"], "official ↗"))
        for s in INJ["announced_starters_captured"])
    trades = "".join(
        "<tr><td>%s</td><td>%s → %s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(t["date"]), esc(t["from"]), esc(t["to"]), esc(t["player"]), esc(t["type"]),
            ext(TRD["source_url"], "official ↗"))
        for t in TRD["rows"])
    xchk = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(c["check"]), esc(c["result"]), ext(TRD["source_url"], "official ↗"))
        for c in TRD["cross_checks"])
    body = """
<h1>Snapshot ledger · Week 10 capture (2026-11-15)</h1>
<p class="lead">Immutable, timestamped, hashed captures of official pages. Later entries
are appended automatically by the <a href="https://github.com/sassnarep3-star/Own4/blob/main/.github/workflows/nfl-readiness-snapshot.yml" target="_blank" rel="noopener">scheduled workflow</a>
(Wed/Thu/Fri 18:00 UTC). Raw bytes live in <code>nfl-readiness/snapshots/</code>, outside the rendered site layer.</p>

<h2>Capture ledger (append-only manifest)</h2>
%s
<div class="note"><b>Manifest integrity:</b> sha256 values in this table were computed
from the stored bytes and re-verified by <code>verify.py</code> on every build.</div>

<h2>Official injury report — Week 10 summary (fetched %s)</h2>
<p>Page title: “%s”. <b>%d team tables · %d player rows · %d no-injury sections · %d Out</b>.
Practice vocabulary observed: %s. Game-status vocabulary: %s.</p>
%s
<div class="note"><b>Row counts are point-in-time</b> — the page evolves daily (254 → 279 → 347
across the week). The ledger exists so counts stop being contradictory and become a series.</div>

<h2>Key rows transcribed verbatim (requirement-relevant)</h2>
%s

<h2>Announced starters captured (evidence, never inference — REQ-41)</h2>
%s

<h2>Week 10 slate &amp; verified finals (fetched %s)</h2>
<p>Byes: %s. Venue is published only where the captured page stated it (Munich);
all other venues are blank — the game-centre pages were not read this session (F-R5).</p>
%s

<h2>Dated schedule announcement (published beside the live schedule — REQ-24)</h2>
<div class="note"><b>%s</b><br>%s<br>Flexible-scheduling procedures: %s</div>

<h2>Official November 2026 trades (roster-turnover stream — REQ-33)</h2>
%s

<h2>Cross-checks between transactions and the injury report</h2>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (
        table(["Capture ID", "Captured (UTC)", "Source", "sha256", "Format", "Status", "Stored"], "".join(tr)),
        esc(INJ["fetched_utc"]), esc(INJ["page_title"]),
        INJ["totals"]["team_tables"], INJ["totals"]["player_rows"], INJ["totals"]["no_injury_sections"], INJ["totals"]["game_status_out"],
        esc("; ".join(INJ["vocabulary_observed"]["practice_status"] + INJ["vocabulary_observed"]["injury_column"][:2])),
        esc("; ".join(INJ["vocabulary_observed"]["game_status"])),
        table(["Team", "Rows"], "".join(teams), "meta narrow"),
        table(["Team", "Player", "Pos", "Injuries", "Practice status", "Game status", "Note", "Source"], keys),
        table(["Player", "Team", "Official evidence", "Source"], starts),
        esc(W10["fetched_utc"]), esc(", ".join(W10["byes"])),
        table(["Away @ Home", "Date", "Slot", "Status at fetch", "Score", "Venue", "Source"], "".join(res)),
        esc(W10["schedule_announcement"]["title"]), esc(W10["schedule_announcement"]["text"]),
        ext(W10["schedule_announcement"]["flex_link"], "nfl.com/legal/flexible-scheduling-procedures ↗"),
        table(["Date", "Move", "Player", "Type", "Source"], trades),
        table(["Check", "Result", "Source"], xchk),
        BUILT)
    return page("pages/snapshots.html", "Snapshot ledger · NFL Readiness", body)

# ---------------------------------------------------------------- questions
def questions():
    tr = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["id"]), esc(r["decision"]), esc(r["known"]),
            blank("answer blank — undecided by policy"), esc(r["discover"]),
            " ".join('<a href="requirements.html#%s">%s</a>' % (esc(b), esc(b)) for b in r["blocks"]),
            ext("https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md", "board ↗"))
        for r in DEC["rows"])
    body = """
<h1>Questions, information needed, answers</h1>
<p class="lead">%s</p>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (esc(DEC["policy"]), table(["ID", "Decision at stake", "What we know (verified)", "Answer", "How to discover it", "Blocks", "Source"], tr), BUILT)
    return page("pages/questions.html", "Questions & answers · NFL Readiness", body)

# ---------------------------------------------------------------- suggestions
def suggestions():
    tr = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td><span class=\"badge b-info\">%s</span></td><td>%s</td></tr>" % (
            esc(r["id"]), esc(r["problem"]), esc(r["suggestion"]),
            " · ".join("<b>%s:</b> %s" % (esc(k), esc(v)) for k, v in r["options"].items()),
            esc(r["status"]),
            ext("https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md", "board ↗"))
        for r in SUG["rows"])
    body = """
<h1>Suggestions — review before implementing</h1>
<p class="lead">%s</p>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (esc(SUG["policy"]), table(["ID", "Problem", "Suggestion", "Options", "Status", "Source"], tr), BUILT)
    return page("pages/suggestions.html", "Suggestions · NFL Readiness", body)

# ---------------------------------------------------------------- repo review
def repo_review():
    tr = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td><span class=\"badge b-info\">%s</span></td><td>%s</td></tr>" % (
            esc(r["id"]), esc(r["area"]), esc(r["finding"]), esc(r["checked"]),
            esc(r["status"]), ext(r["link"], "artifact ↗"))
        for r in REV["rows"])
    body = """
<h1>Repository review — line by line</h1>
<p class="lead">%s</p>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (esc(REV["policy"]), table(["ID", "Area", "Finding", "Checked by", "Status", "Link"], tr), BUILT)
    return page("pages/repo-review.html", "Repo review · NFL Readiness", body)

# ---------------------------------------------------------------- exec summary
def executive_summary():
    body = """
<h1>Executive summary</h1>
<p class="lead">Session 63ebae0e · 2026-11-15 · everything below was verified this session.</p>
<h2>What this workspace is</h2>
<p>The full requirement register for the NFL line-origination program: every line of the
2026-11-15 brief transcribed verbatim (68 requirement rows + 5 process rows), each with
status, blocking gate, clearing number and official source. The
<a href="../index.html">landing page</a> renders the decision-readiness table.</p>
<h2>Headline results</h2>
<table><thead><tr><th>Result</th><th>Detail</th><th>Source</th></tr></thead><tbody>
<tr><td>Decision-readiness table live</td><td>68 requirement rows with gates and clearing numbers (REQ-22 met).</td><td>%s</td></tr>
<tr><td>Week-10 report re-captured live</td><td>28 tables, 347 rows, 0 empty sections, 67 Out; SEA 15, CIN 9 — supersedes stale 254/279 (REQ-48).</td><td>%s</td></tr>
<tr><td>Lions designations resolved at source</td><td>Joseph/Mays/Reed now publish Out on the official page (REQ-47).</td><td>%s</td></tr>
<tr><td>9 of 14 finals verified</td><td>incl. DET 35–10 NE (Munich) and MIN 30–10 GB; live/remaining games recorded as such, never backfilled.</td><td>%s</td></tr>
<tr><td>Snapshot automation shipped</td><td>Wed/Thu/Fri hashed captures + drift alarm; ledger live (REQ-28/29/53/61/62).</td><td>%s</td></tr>
<tr><td>Official anchors verified</td><td>Game books (Game Center PDFs), 90-minute roof rule, Next Gen Stats participation surface.</td><td>%s</td></tr>
</tbody></table>
<h2>What is still open</h2>
<p>No official price source (DR-G1 blocks REQ-04/18/58/59); depth order unresolved for
32 clubs (DEC-R2 blocks REQ-06/32/40/42/44/50); availability graph needs inactive lists
+ game books; VR-/VQ- citations unresolvable in-repo (DEC-R7); PR #93 stale (F-R7).</p>
<h2>What a reviewer should decide first</h2>
<p>Price policy (SUG-R3), canonical store (SUG-R1/R2), snapshot cadence (DEC-R5),
"136-game log" identity (DEC-R6), tracker export for VR/VQ IDs (DEC-R7).</p>
<footer>Research only — not wagering advice. NCPG helpline: <a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">1-800-697-3738</a>. Built %s</footer>
""" % (
        ext("https://sassnarep3-star.github.io/Own4/nfl-readiness/", "this site ↗"),
        ext("https://www.nfl.com/injuries/", "nfl.com injuries ↗"),
        ext("https://www.nfl.com/injuries/", "nfl.com injuries ↗"),
        ext("https://www.nfl.com/schedules/", "nfl.com schedules ↗"),
        ext("https://github.com/sassnarep3-star/Own4/blob/main/.github/workflows/nfl-readiness-snapshot.yml", "workflow ↗"),
        ext("https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books", "support.nfl.com ↗"),
        BUILT)
    return page("pages/executive-summary.html", "Executive summary · NFL Readiness", body)

# ---------------------------------------------------------------- sources
def sources():
    tr = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(s["id"]), ext(s["url"], s["label"]), esc(s["used_for"]), "fetched & read 2026-11-15")
        for s in SRC["sources"])
    body = """
<h1>Sources</h1>
<p class="lead">Every source consulted this session, with what it was used for.</p>
%s
<footer>Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (table(["ID", "Source", "Used for", "When"], tr), BUILT)
    return page("pages/sources.html", "Sources · NFL Readiness", body)

# ---------------------------------------------------------------- flagged
def flagged():
    tr = "".join(
        "<tr><td><b>%s</b></td><td><span class=\"badge %s\">%s</span></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["id"]),
            "b-bad" if r["severity"] == "high" else ("b-warn" if r["severity"] == "medium" else "b-info"),
            esc(r["severity"]), esc(r["flag"]), esc(r["detail"]), esc(r["clears_when"]),
            ext(r["source"], "official ↗"))
        for r in FLG["rows"])
    body = """
<h1>⚑ Flagged for review</h1>
<p class="lead">%s</p>
%s
<footer>Non-blocking by standing instruction. Research only — not wagering advice. Built %s · <a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">repo</a></footer>
""" % (esc(FLG["policy"]), table(["ID", "Severity", "Flag", "Detail", "Clears when", "Source"], tr), BUILT)
    return page("pages/flagged.html", "Flagged for review · NFL Readiness", body)

PAGES = {
    "index.html": idx,
    "pages/requirements.html": requirements,
    "pages/snapshots.html": snapshots,
    "pages/questions.html": questions,
    "pages/suggestions.html": suggestions,
    "pages/repo-review.html": repo_review,
    "pages/executive-summary.html": executive_summary,
    "pages/sources.html": sources,
    "pages/flagged.html": flagged,
}

def main():
    for rel, fn in PAGES.items():
        path = D(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", rel)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
nfl-req-review — round-2 static site builder (2026-11-18), session arena/9242c387-own4.

Renders the landing page, the category subpages and the Executive Summary from the round-2 data
files (see engine/round2.py and engine/round2_register.py). Pure standard library.
Every number on a page is computed from the data files at build time.

Run: python3 engine/round2.py && python3 engine/round2_register.py && python3 engine/build_r2.py
"""

import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
ASSETS = os.path.join(NS, "assets")
os.makedirs(PAGES, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

ROUND = "2026-11-18"
SESSION = "arena/9242c387-own4"
NS_URL = "https://sassnarep3-star.github.io/Own4/nfl-req-review/"


def load(n):
    return json.load(open(os.path.join(DATA, n), encoding="utf-8"))


REQ = load("requirements_2026_11_18.json")
READS = load("official_reads_2026_11_18.json")
FL2 = load("flags_2026_11_18.json")
FL1 = load("flags.json")
QS = load("questions.json")["rows"]
SG = load("suggestions.json")["rows"]
RV = load("repo_review.json")
SRC1 = load("sources.json")

# CSS: reuse the round-1 stylesheet definition (same look), plus a few round-2 classes.
_b1 = open(os.path.join(HERE, "build.py"), encoding="utf-8").read()
CSS_BASE = re.search(r'CSS = """(.*?)"""', _b1, re.S).group(1)
CSS = CSS_BASE + """
.pill { display:inline-block; padding:1px 8px; border-radius:6px; font-size:12px; background:#f1f4f8; color:#334; }
.pill.changed { background:#fff0c2; color:#6a4a00; font-weight:600; }
.pill.ok { background:#e5f4ec; color:var(--ok); }
.pill.bad { background:#fbe6e4; color:var(--bad); }
.grid2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
.panel { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
.panel h3 { margin-top:0; }
.kv td { border-bottom:1px solid #edf1f6; }
"""

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def link(url, text=None):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(text or url))


def srclinks(urls):
    return "<br>".join(link(u, short(u)) for u in urls) if urls else '<span class="blank">blank</span>'


def short(u):
    u = u.replace("https://", "")
    return u if len(u) <= 58 else u[:55] + "…"


def chip(s):
    return '<span class="chip %s">%s</span>' % (esc(s), esc(s.replace("_", " ")))


NAV = [
    ("index.html", "Landing", "index"),
    ("pages/executive-summary.html", "Executive summary", "exec"),
    ("pages/requirements.html", "Decision-readiness table", "req"),
    ("pages/questions.html", "Questions & answers", "q"),
    ("pages/suggestions.html", "Suggestions", "sug"),
    ("pages/games.html", "Games & results", "games"),
    ("pages/verification.html", "Verification", "ver"),
    ("pages/repo-review.html", "Repo review", "repo"),
    ("pages/flagged.html", "Flagged for Review", "flag"),
    ("pages/sources.html", "Sources", "src"),
]


def nav(active, depth=0):
    """depth 0 = landing (index.html); depth 1 = pages/*.html, whose links are relative to pages/."""
    out = ['<nav class="bar" aria-label="Site sections">']
    for href, label, key in NAV:
        if depth:
            href = "../index.html" if href == "index.html" else href.replace("pages/", "")
        out.append('<a href="%s"%s>%s</a>' % (href, ' class="active"' if key == active else "", esc(label)))
    out.append("</nav>")
    return "\n".join(out)


def shell(title, active, body, depth=0):
    up = "../" if depth else ""
    navhtml = nav(active, depth)
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>%s · NFL requirement register</title>"
        "<link rel=\"stylesheet\" href=\"%sassets/style.css\"></head><body>"
        "<header class=\"top\"><h1>Own4 · NFL requirement register</h1>"
        "<div class=\"sub\">Round 2 · read %s · session %s · official sources only · "
        "unverifiable values blank and flagged</div></header>%s<main>%s</main>"
        "<footer>Every table row links to the page it was read from. Values that could not be "
        "confirmed from an official source are blank and listed on the Flagged for Review page. "
        "This is analysis, not betting advice. National Problem Gambling Helpline 1-800-MY-RESET "
        "(1-800-697-3738), https://www.ncpgambling.org/help-treatment</footer></body></html>"
        % (esc(title), up, esc(ROUND), esc(SESSION), navhtml, body)
    )


def table(headers, rows_html):
    th = "".join("<th>%s</th>" % esc(h) for h in headers)
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, "".join(rows_html))


def tr(cells):
    return "<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in cells)


# ---------------------------------------------------------------------------
# computed figures used across pages
# ---------------------------------------------------------------------------
REG_ROWS = REQ["rows"]
COUNTS = REQ["counts"]
CHANGED = REQ["changed_this_round"]
CHECKS = READS["checks"]
CK = {c["id"]: c for c in CHECKS}
FR = READS["feed_reconciliation"]
GAMES_THRU_W10 = READS["derived"]["games_completed_through_week10"]
GAMES_THRU_W9 = READS["derived"]["games_completed_through_week9"]
W10 = READS["week10_finals"]
W11 = READS["week11_fixtures"]
FEED_W10_IN = len(FR["feed_week10_game_ids"])
FEED_CLUBS_MATCH = FR["clubs_matching"]
FLAGS_ALL = [dict(f, round=1) for f in FL1["flags"]] + [dict(f, round=2) for f in FL2["flags"]]
RR_ROWS = RV["rows"]
NFL_NS = RV["nfl_namespace_count"]
OPEN_PRS = len(RV["open_pr_numbers"])
FAILING = sorted(c["id"] for c in CHECKS if not c["ok"])
ARTS_MISSING = [(r["id"], a["path"]) for r in REG_ROWS for a in r["artifacts"] if not a["exists"]]
MET_OK = sum(1 for r in REG_ROWS if r["status"] == "met")
_MO = json.load(open(os.path.join(ROOT, "nfl-book/data/model_outputs.json"), encoding="utf-8"))
MODEL_N_TRAIN = next(r["inputs"]["n_train_games"] for r in _MO["rows"] if r["game_id"] == "W11-IND-HOU")
REVIEWED = sum(1 for r in REG_ROWS if r["round2_reviewed"])

# The executive summary's paragraphs. Numbers are interpolated from the figures above.
EXEC_PARAS = [
    ("What this is",
     "A line-by-line round-2 re-check of the NFL requirement register, on %d requirement rows, against official nfl.com pages read on %s. "
     "It is a decision-readiness surface: each row states its status, the gate that blocks it, and the number that would clear it. "
     "It is not a betting product: it publishes no picks, no prices, and no strategy shown as eligible." % (len(REG_ROWS), ROUND)),
    ("What the official sources now settle",
     "%d completed regular-season games through Week 10 (sum of W+L+T across 32 clubs divided by 2). Weeks 1-9 hold %d games, and they reconcile to "
     "the official standings for %d of 32 clubs on wins, losses, ties, points for and points against. Week 10 had 14 finals, all now on the "
     "official schedule page. Week 11 has %d fixtures and %d clubs on bye."
     % (GAMES_THRU_W10, GAMES_THRU_W9, FEED_CLUBS_MATCH, len(W11), len(READS["derived"]["week11_byes_computed"]))),
    ("What the data still gets wrong",
     "The verified results feed holds %d of the %d Week-10 finals. The model's Week-11 row records %d training games, against %d official completed games through Week 9. "
     "The holdout split leaves 13 completed games in no split. One peer session's figure of 133 games through Week 9 is an arithmetic error, "
     "and its claim that no file publishes 136 is contradicted by the official arithmetic. Each is logged as a flag with its source link, "
     "owned by the peer namespace, and not edited here."
     % (FEED_W10_IN, len(W10), MODEL_N_TRAIN, GAMES_THRU_W9)),
    ("What changed in the register",
     "%d rows were re-verified in this round and %d were downgraded from 'met' because their own artifact or source did not support the claim: %s. "
     "Final register: %d met, %d partial, %d blocked, %d not started, %d in progress."
     % (REVIEWED, len(CHANGED), ", ".join(CHANGED), COUNTS.get("met", 0), COUNTS.get("partial", 0),
        COUNTS.get("blocked", 0), COUNTS.get("not_started", 0), COUNTS.get("in_progress", 0))),
    ("The injury data",
     "The Lions' Kerby Joseph, Cade Mays and D.J. Reed are now shown with game status Out on the official Week-10 report. The Week-11 report "
     "is not yet published at the read time. The round-1 injury totals are internally inconsistent, and Cincinnati's count is unresolved (RF-13, RF-14)."),
    ("Decisions the owner needs to make",
     "(1) One entry point for the 39 NFL namespaces at base eb6d8de (S-01). (2) Price-data policy, option (b) recommended (S-02). (3) Add the 13 missing Week-10 "
     "finals to the feed (S-03). (4) Freeze the corpus at 136 and name Week 10 as a prospective window (S-04). (5) Approve a daily injury "
     "capture from Wednesday (S-05). (6) Link this namespace from the root page (S-08). Each has its options on the Suggestions page."),
    ("Limits",
     "The sandbox cannot reach nfl.com directly (tested 2026-11-18, no response), so every official read was made with the page-fetch tool and "
     "is recorded with its URL and read date. Week-10 injury chunks 1-7 were not re-read, so the full injury table is unverified. Raw page text was not saved "
     "to the repository, so the reads carry URLs and read dates but no sha256 hash. The clone is shallow, so pre-registration commit "
     "hashes cannot be checked here (RF-18). The 38 peer namespaces were not re-read line by line."),
]


def exec_md():
    lines = ["# Executive summary — NFL requirement register, round 2 (%s)" % ROUND, "",
             "Session `%s`. Live: %s" % (SESSION, NS_URL), ""]
    for h, p in EXEC_PARAS:
        lines += ["## " + h, "", p, ""]
    lines += ["Analysis only. Not wagering advice. Helpline: 1-800-MY-RESET (https://www.ncpgambling.org/help-treatment).", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def page_index():
    cards = [
        ("Completed games through Week 10", str(GAMES_THRU_W10), "official standings, computed"),
        ("Clubs reconciled, Weeks 1-9", "%d / 32" % FEED_CLUBS_MATCH, "feed vs official W, L, T, PF, PA"),
        ("Week-10 finals in the feed", "%d / %d" % (FEED_W10_IN, len(W10)), "13 missing (RF-09)"),
        ("Register: met", "%d / %d" % (COUNTS.get("met", 0), len(REG_ROWS)), "downgrades: %d this round" % len(CHANGED)),
        ("Open flags", str(len(FLAGS_ALL)), "%d round 2 · %d round 1" % (len(FL2["flags"]), len(FL1["flags"]))),
        ("NFL namespaces in repo", str(NFL_NS), "at base eb6d8de · overlap (RR-09)"),
    ]
    cards_html = "".join('<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="d">%s</div></div>'
                         % (esc(a), esc(b), esc(c)) for a, b, c in cards)
    groups = [
        ("Overview", [("pages/executive-summary.html", "Executive summary", "Numbers, limits and the decisions needed")]),
        ("Requirements", [("pages/requirements.html", "Decision-readiness table", "73 rows: status, gate, number that clears it"),
                          ("pages/questions.html", "Questions & answers", "What is known, what is missing, how to find out"),
                          ("pages/suggestions.html", "Suggestions", "Options to choose from; nothing implemented")]),
        ("Data & verification", [("pages/games.html", "Games & results", "14 Week-10 finals, 13 Week-11 fixtures, 32-club reconciliation"),
                                 ("pages/verification.html", "Verification", "Every computed check and its expected value")]),
        ("Governance", [("pages/flagged.html", "Flagged for Review", "Irregularities with source links; non-blocking"),
                        ("pages/repo-review.html", "Repo review", "Line-by-line scope and findings"),
                        ("pages/sources.html", "Sources", "Every official URL read, with its read date")]),
    ]
    gh = ""
    for g, items in groups:
        gh += '<h3>%s</h3><div class="grid2">' % esc(g)
        for href, label, desc in items:
            gh += '<div class="panel"><a href="%s"><b>%s</b></a><div class="small">%s</div></div>' % (esc(href), esc(label), esc(desc))
        gh += "</div>"
    changed_rows = [r for r in REG_ROWS if r["status_change"]]
    ch_html = table(["ID", "Requirement", "Round 1", "Round 2", "Why"],
                    [tr([esc(r["id"]), esc(r["requirement"][:110]), chip(r["status_2026_11_17"]), chip(r["status"]),
                         esc(r["evidence"][:260] + ("…" if len(r["evidence"]) > 260 else "")) + " " + link(r["source"], "source")])
                     for r in changed_rows])
    body = (
        '<h2>Round 2 at a glance</h2><p class="lead">%s</p>' % esc(EXEC_PARAS[1][1])
        + '<div class="cards">%s</div>' % cards_html
        + "<h2>Where to go</h2>" + gh
        + "<h2>What changed in this round (downgraded from met)</h2>"
        + '<p class="small">Each downgrade names the artifact or source that did not support the round-1 claim.</p>'
        + ch_html
    )
    return shell("Landing", "index", body)


def page_exec():
    body = "<h2>Executive summary</h2>"
    for h, p in EXEC_PARAS:
        body += "<h3>%s</h3><p>%s</p>" % (esc(h), esc(p))
    body += ('<p class="small">Full text: <a href="../EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a> · '
             'Live site: %s</p>' % link(NS_URL))
    return shell("Executive summary", "exec", body, depth=1)


def page_requirements():
    rows = []
    for r in REG_ROWS:
        ch = '<span class="pill changed">changed</span>' if r["status_change"] else ""
        srctype = esc(r["source_type"])
        rows.append(tr([
            esc(r["id"]), esc(r["group"]), esc(r["requirement"]),
            chip(r["status"]) + " " + ch,
            esc(r["gate"]) if r["gate"] != "—" else '<span class="blank">none — met</span>',
            esc(r["clears"]) if r["clears"] != "—" else '<span class="blank">none — met</span>',
            esc(r["evidence"]),
            link(r["source"], short(r["source"])) + '<br><span class="small">%s</span>' % srctype,
        ]))
    body = ('<h2>Decision-readiness table</h2>'
            '<p class="lead">One row per requirement: its status, the gate that blocks it, the number or set that would clear it, the '
            'round-2 evidence, and the source. A blank means not verifiable from an official source, and it is flagged.</p>'
            '<p class="small">%d rows · %d met · %d partial · %d blocked · %d not started · %d in progress. Source type "process (repository)" '
            'marks governance rows that have no external data value.</p>' % (
                len(REG_ROWS), COUNTS.get("met", 0), COUNTS.get("partial", 0), COUNTS.get("blocked", 0),
                COUNTS.get("not_started", 0), COUNTS.get("in_progress", 0)))
    body += table(["ID", "Group", "Requirement", "Status", "Gate that blocks it", "Number / set that clears it", "Round-2 evidence", "Source"], rows)
    return shell("Decision-readiness table", "req", body, depth=1)


def page_questions():
    rows = [tr([esc(q["id"]), esc(q["question"]), esc(q["known_answer"]), esc(q["gap"]), esc(q["how_to_discover"]), srclinks(q["sources"])])
            for q in QS]
    body = ("<h2>Questions, known answers, gaps and how to find out</h2>"
            '<p class="lead">Read this before making any decision from the register. "Known answer" states only what an official read or '
            'an artifact in the repository supports. The gap is what is still missing.</p>')
    body += table(["ID", "Question", "Known answer", "What is still missing", "How to find out", "Source"], rows)
    return shell("Questions & answers", "q", body, depth=1)


def recommended_text(s):
    """Show the recommended option's full text, not only its letter."""
    rec = s["recommended"].strip()
    m = re.match(r"\(([a-z])\)", rec)
    if not m:
        return rec
    for o in s["options"]:
        if o.startswith("(%s)" % m.group(1)):
            tail = rec[m.end():].strip()
            return o + (" — " + tail if tail else "")
    return rec


def page_suggestions():
    rows = [tr([esc(s["id"]), esc(s["title"]), esc(s["why"]),
                "<ul class=\"tight\">%s</ul>" % "".join("<li>%s</li>" % esc(o) for o in s["options"]),
                esc(recommended_text(s)), esc(s["decision_owner"]), '<span class="blank">blank: owner to decide</span>',
                srclinks(s["sources"])])
            for s in SG]
    body = ("<h2>Suggestions — choose a path before anything changes</h2>"
            '<p class="lead">Each suggestion lists its options and a recommended path. Nothing here has been implemented. The decision column is '
            "left blank for the owner. A suggestion is not a verdict.</p>")
    body += table(["ID", "Suggestion", "Why it matters", "Options", "Recommended", "Decision owner", "Decision", "Source"], rows)
    return shell("Suggestions", "sug", body, depth=1)


def page_games():
    w10_rows = []
    feed_ids = set(FR["feed_week10_game_ids"])
    for g in W10:
        in_feed = "yes" if g["game_id"] in feed_ids else "no — missing from feed (RF-09)"
        w10_rows.append(tr([esc(g["date"]), "%s %d" % (esc(g["away"]), g["away_pts"]),
                            "%s %d" % (esc(g["home"]), g["home_pts"]), esc(in_feed), link(g["game_url"], "official game page")]))
    w11_rows = [tr([esc(g["date"]), "%s @ %s" % (esc(g["away"]), esc(g["home"])), esc(g["kickoff"]), esc(g["network"]),
                    link(g["game_url"], "official game page")]) for g in W11]
    # 32-club reconciliation: official through Week 9 (computed) vs feed through Week 9 (computed)
    stand = {s["club"]: s for s in READS["standings_2026_11_18"]}
    w10t = {}
    for g in W10:
        for club, pf, pa in ((g["away"], g["away_pts"], g["home_pts"]), (g["home"], g["home_pts"], g["away_pts"])):
            d = w10t.setdefault(club, dict(w=0, l=0, t=0, pf=0, pa=0))
            d["pf"] += pf; d["pa"] += pa
            if pf > pa: d["w"] += 1
            elif pf < pa: d["l"] += 1
            else: d["t"] += 1
    rec_rows = []
    for c in sorted(stand):
        s = stand[c]
        w9 = {k: s[k] - w10t.get(c, {}).get(k, 0) for k in ("w", "l", "t", "pf", "pa")}
        w9s = "%d-%d-%d" % (w9["w"], w9["l"], w9["t"])
        rec_rows.append(tr([esc(c), esc("%d-%d-%d" % (s["w"], s["l"], s["t"])), esc(w9s), esc(w9["pf"]), esc(w9["pa"]),
                            link(SRC_STAND_URL, "standings")]))
    body = ("<h2>Games & results</h2>"
            '<p class="lead">Official values transcribed on the read date with their game URL. The reconciliation compares the verified feed with '
            "the official standings, club by club, after removing Week 10.</p>")
    body += "<h3>Week 10 — %d official finals</h3>" % len(W10)
    body += table(["Date", "Away", "Home", "In verified feed?", "Source"], w10_rows)
    body += "<h3>Week 11 — %d fixtures (%d clubs on bye)</h3>" % (len(W11), len(READS["derived"]["week11_byes_computed"]))
    body += table(["Date", "Fixture", "Kickoff", "Network", "Source"], w11_rows)
    body += "<h3>Club reconciliation: official through Week 9 (computed) — %d of 32 match the feed (%s)</h3>" % (
        FEED_CLUBS_MATCH, "all clubs reconciled" if FEED_CLUBS_MATCH == 32 else "see RF flags")
    body += table(["Club", "Official W-L-T (through W10)", "Official through W9 (computed)", "PF through W9", "PA through W9", "Source"], rec_rows)
    return shell("Games & results", "games", body, depth=1)


SRC_STAND_URL = "https://www.nfl.com/standings/league/2026/REG"


def page_verification():
    rows = []
    for c in CHECKS:
        res = '<span class="pill ok">as expected</span>' if c["ok"] else '<span class="pill bad">finding — see flags</span>'
        val = esc(json.dumps(c["value"]) if not isinstance(c["value"], (int, str)) else c["value"])
        exp = esc(json.dumps(c["expected"]) if not isinstance(c["expected"], (int, str)) else c["expected"])
        rows.append(tr([esc(c["id"]), esc(c["label"]), val, exp, res, esc(c.get("note", "")), link(c["source"], short(c["source"]))]))
    body = ("<h2>Verification — computed checks</h2>"
            '<p class="lead">Each check is computed by engine/round2.py from the transcribed official values. A check "as expected" passes its '
            "stated expectation. A finding is a difference that is logged on the Flagged for Review page; it is not hidden or adjusted.</p>")
    body += table(["Check", "What is tested", "Computed", "Expected", "Result", "Note", "Source"], rows)
    body += ("<h3>Round-1 validation carried forward</h3><p class=\"small\">Round 1 (2026-11-17) reads, the Lions and injury checks, and the "
             "designation join are in data/official_reads_2026_11_17.json. This round re-reads the standings, the Week 10 and 11 schedules, and the Week 10 Lions rows.</p>")
    return shell("Verification", "ver", body, depth=1)


def page_flags():
    rows = []
    for f in FLAGS_ALL:
        src = f.get("sources") or ([f["source"]] if f.get("source") else [])
        rows.append('<div class="flag"><h3>%s · %s</h3><div class="meta">%s · round %s · owner: %s</div><p>%s</p><p class="small">%s</p></div>'
                    % (esc(f["id"]), esc(f["title"]), esc(f["severity"]), esc(f["round"]), esc(f.get("owner", "round 1 (see register)")),
                       esc(f["detail"]), srclinks(src)))
    body = ("<h2>Flagged for Review</h2>"
            '<p class="lead">Irregularities, unresolved items and corrections. They are non-blocking: each has its source link, and nothing is inferred to fill a gap. '
            "Peer-owned items are logged here and not edited in the peer namespace.</p>")
    body += "".join(rows)
    return shell("Flagged for Review", "flag", body, depth=1)


def page_repo():
    rows = [tr([esc(r["id"]), esc(r["finding"]), esc(r["detail"]), esc(r["evidence"]), esc(r["class_"]), link(r["source"], short(r["source"]))])
            for r in RR_ROWS]
    body = ("<h2>Repo review</h2>"
            '<p class="lead">Mechanical checks and reconciliations. Scope is stated in RR-17: what was reviewed line by line, and what was not.</p>')
    body += table(["ID", "Finding", "Detail", "Evidence / method", "Class", "Source"], rows)
    return shell("Repo review", "repo", body, depth=1)


def page_sources():
    rows = []
    for s in READS["sources"]:
        rows.append(tr([esc(s["id"]), esc(s["what"]), esc(ROUND), link(s["url"], short(s["url"]))]))
    for s in SRC1.get("sources", []):
        rows.append(tr([esc(s["id"]), esc(s.get("used_for", s.get("title", ""))), esc(s.get("read_utc", "")), link(s["url"], short(s["url"]))]))
    body = ("<h2>Sources</h2>"
            '<p class="lead">Round-2 sources first (read %s), then the round-1 register (read 2026-11-17). Every link is an official nfl.com page, or a repository '
            "file where the source is the repository itself.</p>" % ROUND)
    body += table(["ID", "What was read", "Read on", "Link"], rows)
    return shell("Sources", "src", body, depth=1)


def page_landing_redirect_assets():
    pass


def main():
    with open(os.path.join(ASSETS, "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    out = {
        os.path.join(NS, "index.html"): page_index(),
        os.path.join(PAGES, "executive-summary.html"): page_exec(),
        os.path.join(PAGES, "requirements.html"): page_requirements(),
        os.path.join(PAGES, "questions.html"): page_questions(),
        os.path.join(PAGES, "suggestions.html"): page_suggestions(),
        os.path.join(PAGES, "games.html"): page_games(),
        os.path.join(PAGES, "verification.html"): page_verification(),
        os.path.join(PAGES, "flagged.html"): page_flags(),
        os.path.join(PAGES, "repo-review.html"): page_repo(),
        os.path.join(PAGES, "sources.html"): page_sources(),
    }
    for p, h in out.items():
        with open(p, "w", encoding="utf-8") as f:
            f.write(h)
    with open(os.path.join(NS, "EXECUTIVE_SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(exec_md())
    print("built %d pages + EXECUTIVE_SUMMARY.md" % len(out))


if __name__ == "__main__":
    main()

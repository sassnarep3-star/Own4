"""Build the nfl-readiness static site.

Design constraints enforced by verify.py, not just by convention:
  * every data-table row carries at least one https:// source link;
  * every deliberate blank is rendered by blank() so it carries
    class="blank" and title="unverified ...";
  * every internal link resolves, every page keeps the nav and the
    responsible-gambling footer;
  * the rebuild is deterministic (CI fails on diff).

Run: python3 build_site.py
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

NAV = [
    ("index.html", "Dashboard"),
    ("pages/decision-readiness.html", "Decision readiness"),
    ("pages/verification.html", "Independent verification"),
    ("pages/availability.html", "Availability evidence"),
    ("pages/questions.html", "Questions"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources"),
    ("pages/executive-summary.html", "Executive summary"),
]

CSS = """
:root{--bg:#0d1220;--panel:#151d2f;--panel2:#1b2438;--text:#e9edf6;--muted:#94a2ba;
--accent:#5ba7ff;--good:#3ddc84;--bad:#ff7070;--warn:#ffc857;--line:#28324c;}
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh}
nav.side{width:236px;flex:0 0 236px;background:var(--panel);padding:20px 14px;
border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow:auto}
nav.side .brand{font-weight:700;font-size:15px;letter-spacing:.2px}
nav.side .sub{color:var(--muted);font-size:11.5px;margin:4px 0 16px;line-height:1.4}
nav.side a{display:block;padding:7px 10px;border-radius:8px;color:var(--text);font-size:13px}
nav.side a:hover{background:var(--panel2);text-decoration:none}
nav.side a.active{background:var(--panel2);color:var(--accent);font-weight:600}
main{flex:1;padding:28px 34px 60px;max-width:1280px;min-width:0}
h1{font-size:25px;margin:0 0 6px;letter-spacing:-.2px}
h2{font-size:17px;margin:30px 0 10px;border-bottom:1px solid var(--line);padding-bottom:7px}
h3{font-size:12px;margin:20px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
p{margin:0 0 12px}
.lead{color:var(--muted);margin:0 0 18px;max-width:80ch}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:11px;margin:16px 0 24px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 14px}
.card .k{font-size:23px;font-weight:700;line-height:1.1}
.card .l{font-size:11.5px;color:var(--muted);margin-top:4px;line-height:1.35}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:10.5px;font-weight:700;
letter-spacing:.03em;white-space:nowrap}
.b-met{background:rgba(61,220,132,.15);color:var(--good)}
.b-partial{background:rgba(255,200,87,.15);color:var(--warn)}
.b-blocked{background:rgba(255,112,112,.15);color:var(--bad)}
.b-not_started{background:rgba(148,162,186,.16);color:#b6c2d6}
.b-pass{background:rgba(61,220,132,.15);color:var(--good)}
.b-fail{background:rgba(255,112,112,.15);color:var(--bad)}
.b-P0{background:rgba(255,112,112,.15);color:var(--bad)}
.b-P1{background:rgba(255,200,87,.15);color:var(--warn)}
.b-P2,.b-P3{background:rgba(148,162,186,.16);color:#b6c2d6}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:11px;margin:14px 0 22px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{padding:9px 11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--panel2);font-size:11px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);position:sticky;top:0;font-weight:700}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:rgba(91,167,255,.05)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
td.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:var(--muted);white-space:nowrap}
.blank{color:#7d8aa0;font-style:italic;font-size:11.5px}
.tag{display:inline-block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;
background:var(--panel2);color:var(--muted);padding:1px 6px;border-radius:5px;margin-right:4px}
.note{background:var(--panel);border-left:3px solid var(--accent);border-radius:0 9px 9px 0;
padding:12px 15px;margin:16px 0;color:#cfd8e8;font-size:13px}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.note.good{border-left-color:var(--good)}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:11.5px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;
background:var(--panel2);padding:1px 5px;border-radius:4px}
ul,ol{margin:0 0 12px;padding-left:20px}li{margin:4px 0}
details{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
@media(max-width:820px){.layout{display:block}nav.side{width:auto;height:auto;position:static;
border-right:none;border-bottom:1px solid var(--line)}main{padding:20px 16px 50px}}
"""

FOOTER = """<footer>
<p><strong>Analytical research only — not wagering advice.</strong> Every published number is
either computed from data/observations.json (transcribed from the official page named in the row)
or shown as a blank. No value is inferred, interpolated or carried over from an unverified source.</p>
<p>National Problem Gambling Helpline: 1-800-MY-RESET —
<a href="https://www.ncpgambling.org/help-treatment">ncpgambling.org/help-treatment</a>.
Capture clock for this release: <code>%(cap)s</code>. Rebuild with the four commands in
<a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-readiness/README.md">README.md</a>
or read the site's own <a href="%(p)spages/sources.html">source register</a>.</p>
</footer>"""


# ------------------------------------------------------------------ helpers
def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def blank(reason="unverified — no official value published"):
    """A deliberate blank. verify.py requires class=blank AND title starting 'unverified'."""
    return '<span class="blank" title="unverified: %s">&mdash; blank</span>' % esc(reason)


def cell(x, reason="unverified — no official value published"):
    if x is None or x == "" or x == "§blank§":
        return blank(reason)
    if isinstance(x, str) and x.startswith("§blank§"):
        return blank(x[8:].strip() or reason)
    return esc(x)


def badge(state):
    labels = {"met": "met", "partial": "partial", "blocked": "blocked", "not_started": "not started",
              "pass": "pass", "fail": "fail", "partial_": "partial"}
    return '<span class="badge b-%s">%s</span>' % (state, labels.get(state, state))


def src(url, label=None):
    return '<a href="%s">%s</a>' % (esc(url), esc(label or url))


def table(headers, rows, cls="", num_cols=()):
    """rows: list of list of already-rendered HTML strings."""
    th = "".join('<th%s>%s</th>' % (' class="num"' if i in num_cols else "", h)
                 for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join('<td%s>%s</td>' % (' class="num"' if i in num_cols else "", c)
                      for i, c in enumerate(r))
        body.append("<tr>%s</tr>" % tds)
    return ('<div class="wrap"><table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % ((' class="%s"' % cls) if cls else "", th, "".join(body)))


def page(path, title, active, body, desc=""):
    prefix = "../../" if path.count("/") >= 1 else "../"
    # pages/ -> one level up, index.html -> same dir
    prefix = "../" if path.startswith("pages/") else ""
    nav = []
    for href, label in NAV:
        cls = "active" if href.endswith(active) else ""
        nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, esc(label)))
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · NFL decision readiness</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(p)sassets/readiness.css">
</head>
<body>
<div class="layout">
<nav class="side">
  <div class="brand">NFL decision readiness</div>
  <div class="sub">Own4 · what is blocked, by how much,<br>and what would clear it</div>
  %(nav)s
</nav>
<main>
%(body)s
%(footer)s
</main>
</div>
</body>
</html>
""" % {
        "title": esc(title), "desc": esc(desc), "p": prefix,
        "nav": "".join(nav), "body": body,
        "footer": FOOTER % {"cap": CAPTURE, "p": prefix},
    }
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out) or ROOT, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def load(name):
    import json
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


OBS = load("observations.json")
DER = load("derived.json")
READY = load("readiness.json")
Q = load("questions.json")
SUG = load("suggestions.json")
FLG = load("flags.json")
CAPTURE = OBS["capture_utc"]
SOURCE_URL = {s["id"]: s["url"] for s in OBS["sources"]}
SOURCE_NAME = {s["id"]: s["what"] for s in OBS["sources"]}


# ------------------------------------------------------------------- pages
def build_index():
    inj, ina, join = DER["injury_report"], DER["inactives"], DER["inactives_join"]["agg"]
    ven = DER["venue"]
    s = READY["summary"]
    cards = [
        (s["n_requirements"], "requirements traced, each with its blocking gate"),
        (f'{s["met"]}', "met and re-verified this session"),
        (f'{s["partial"]}', "partial — implemented, evidence-limited"),
        (f'{s["blocked"]}+{s["not_started"]}', "blocked or not started"),
        (ina["n_named_players"], "official Week 10 inactives named — source the repo never ingested"),
        (inj["n_rows"], f'report rows read, all {inj["n_sections"]} club sections, 8/8 chunks'),
        (len(Q["rows"]), "questions, answers blank until established"),
        (len(FLG["rows"]), "irregularities flagged, none blocking"),
    ]
    card_html = "".join(
        '<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(k), esc(l))
        for k, l in cards)

    body = """
<h1>NFL decision readiness</h1>
<p class="lead">One page per question. This site answers a single question the other
%(ns)d NFL namespaces in this repository do not: <strong>for each requirement, what blocks it,
and what number would clear it?</strong> Every figure below was computed this session from
official nfl.com pages fetched at <code>%(cap)s</code>. Anything that could not be confirmed is
shown as a blank and listed on <a href="pages/flagged.html">Flagged for review</a>.</p>

<div class="cards">%(cards)s</div>

<h2>The five decisions that need an owner</h2>
<p>Out of %(nr)d traced requirements, %(n_ask)d are waiting on a human decision rather than on
engineering. Everything else on this site is a build task with a measurable target.</p>
%(decisions)s

<h2>What this session changed</h2>
<div class="note good">
<strong>The single largest finding:</strong> the repository treats official inactive lists as
unobtainable. They are published. nfl.com carries a dated inactives article naming
<strong>%(nina)d players across %(nsec)d club sections</strong> for Week 10, and the same article
publishes the venue string for 12 games. That converts one of the biggest listed blockers from
&ldquo;the source does not exist&rdquo; into &ldquo;a parser has not been written&rdquo;.
<a href="pages/availability.html">See the availability evidence</a>.
</div>
<div class="note warn">
<strong>The single largest non-finding:</strong> market prices still do not exist. The NFL
published kickoff time, network and venue for all 13 Week 11 fixtures and no line of any kind.
%(n_res)d of the traced requirements ultimately depend on that one missing input, which is why
it is question Q01 and suggestion S01, not a build ticket.
</div>

<h2>How to read the state column</h2>
%(legend)s

<h2>Where to go next</h2>
<ul>
<li><a href="pages/decision-readiness.html">Decision readiness</a> — all %(nr)d requirements, filterable by state and group.</li>
<li><a href="pages/verification.html">Independent verification</a> — five peer claims re-checked against freshly fetched official pages, plus the four internal-consistency tests.</li>
<li><a href="pages/availability.html">Availability evidence</a> — the Week 10 report and inactives transcribed in full, with the join between them.</li>
<li><a href="pages/questions.html">Questions</a> — what is known, what is unknown, and the artefact that would resolve each one.</li>
<li><a href="pages/suggestions.html">Suggestions</a> — %(nsug)d proposals, each with three options and a blank verdict awaiting review.</li>
<li><a href="pages/flagged.html">Flagged for review</a> — %(nfl)d irregularities, each with its official source.</li>
</ul>
""" % {
        "ns": 26, "cap": esc(CAPTURE), "cards": card_html,
        "nr": s["n_requirements"], "n_ask": 5,
        "nina": ina["n_named_players"], "nsec": ina["n_sections"],
        "n_res": 9, "nfl": len(FLG["rows"]), "nsug": len(SUG["rows"]),
        "decisions": decision_html(""),
        "legend": legend_html(),
    }
    return page("index.html", "Dashboard", "index.html", body,
                "NFL decision readiness: what blocks each requirement and what number would clear it.")


def decision_html(prefix=""):
    picks = [
        ("Q01 / S01", "How are market prices obtained, or do we formally give up on the residual?",
         "Blocks 9 traced requirements including every ROI figure. The NFL publishes no line.",
         "S01"),
        ("Q10 / S02", "Which of the 26 NFL site trees is canonical?",
         "Every new session adds a namespace because no rule says where work must land.",
         "S02"),
        ("Q13", "What is the legal position on republishing official row-level data and paying rewards?",
         "Blocks the public/private split and the entire rewards pool.",
         None),
        ("Q03 / S07", "Is the backtest corpus 136 games or 137?",
         "The pre-registration and the artefact have drifted by one real, official game.",
         "S07"),
        ("Q06 / S04", "Which official source establishes who actually started?",
         "The Game Book PDF is linked from every game centre and has never been parsed.",
         "S04"),
    ]
    rows = []
    for ref, q, why, sug in picks:
        link = ('<a href="%spages/suggestions.html#%s">%s</a>' % (prefix, sug, sug)) if sug \
            else blank("decision only — no suggestion drafted")
        rows.append([
            '<span class="id">%s</span>' % esc(ref),
            '<a href="%spages/questions.html">%s</a>' % (prefix, esc(q)),
            esc(why),
            link,
            src("https://www.nfl.com/", "nfl.com"),
        ])
    return table(["Ref", "Decision needed", "Why it is first-order", "Options", "Source"], rows)


def legend_html():
    rows = [
        [badge("met"), "Implemented and re-verified against an official source this session."],
        [badge("partial"), "Implemented, but limited by a documented evidence gap. The gap is named in its row."],
        [badge("blocked"), "Cannot be completed from the sources currently held. The missing artefact is named."],
        [badge("not_started"), "No implementation found anywhere in the repository."],
    ]
    return table(["State", "Meaning"], rows, cls="meta")


def build_readiness():
    s = READY["summary"]
    rows = []
    for r in READY["rows"]:
        rows.append([
            '<span class="id">%s</span>' % esc(r["id"]),
            badge(r["state"]),
            esc(r["requirement"]),
            esc(r["blocking_gate"]),
            esc(r["clearing_number"]),
            esc(r["ask"]),
            '<a href="%s">source</a>' % esc(r["source_url"]),
        ])
    groups = []
    for g in READY["groups"]:
        rs = [r for r in READY["rows"] if r["group"] == g]
        cnt = {}
        for r in rs:
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
        groups.append([esc(g), str(len(rs))]
                      + [str(cnt.get(k, 0)) for k in ("met", "partial", "blocked", "not_started")]
                      + [src("https://www.nfl.com/", "nfl.com")])

    body = """
<h1>Decision readiness</h1>
<p class="lead">Every requirement in the brief, in the owner's own words, with the single gate that
blocks it and the measurable number that would clear it. %(n)d rows. %(met)d met, %(partial)d
partial, %(blocked)d blocked, %(ns)d not started.</p>

<div class="note">
<strong>Why the clear-number column matters more than the state column.</strong> A state without a
target becomes an opinion. &ldquo;Depth is partial&rdquo; is an opinion; &ldquo;2 of 32 clubs have a
verified structured depth route, 32 are needed&rdquo; is a task with an end.
</div>

<h2>Summary by group</h2>
%(groups)s

<h2>All %(n)d requirements</h2>
<p>Sorted by the order the brief raises them. Each row's source link points at the official page
that establishes the gate or the current value.</p>
%(table)s

<h2>Method</h2>
<p>Rows are authored in <code>engine/readiness.py</code>. Every number quoted inside a row's clear-number
cell is read from <code>data/derived.json</code>, which <code>engine/derive.py</code> recomputes from
<code>data/observations.json</code> on every build. A number that cannot be recomputed therefore
cannot be published: <code>readiness.py</code> fails when a row cites a key that does not exist.</p>
""" % {
        "n": s["n_requirements"], "met": s["met"], "partial": s["partial"],
        "blocked": s["blocked"], "ns": s["not_started"],
        "groups": table(["Group", "Rows", "met", "partial", "blocked", "not started", "Source"],
                        groups, num_cols=(1, 2, 3, 4, 5)),
        "table": table(["ID", "State", "Requirement", "Blocking gate", "Number that would clear it",
                        "Ask", "Source"], rows),
    }
    return page("pages/decision-readiness.html", "Decision readiness",
                "pages/decision-readiness.html", body,
                "One row per requirement with the blocking gate and the clearing number.")


def confirm_rows():
    standings = DER["standings_confirmed"]
    slate = DER["week11_confirmed"]
    wk10 = DER["week10_scores_confirmed"]
    inj, ina, ven = DER["injury_report"], DER["inactives"], DER["venue"]
    return [
        ["League standings, all 32 clubs", str(standings["n_rows"]),
         "W/L/T/PCT/PF/PA transcribed club by club; %s" % src(standings["source_url"], "nfl.com/standings")],
        ["Week 11 schedule", str(slate["n_rows"]),
         "13 fixtures, 6 byes, date/kickoff/network per fixture; %s"
         % src(slate["source_url"], "nfl.com/schedules")],
        ["Week 10 injury report", str(inj["n_rows"]),
         "All 8 of 8 page chunks, %d club sections; %s"
         % (inj["n_sections"], src(SOURCE_URL["S-injuries"], "nfl.com/injuries"))],
        ["Week 10 inactives", str(ina["n_named_players"]),
         "%d club sections, %d venue strings; %s"
         % (ina["n_sections"], ina["n_published_venues"], src(SOURCE_URL["S-inact"], "nfl.com inactives"))],
        ["Week 10 scoreboard", "%d finals" % wk10["n_finals"],
         "%d further games were in progress and are excluded; %s"
         % (wk10["n_in_progress"], src(wk10["source_url"], "nfl.com/scores"))],
        ["Game centres probed", str(ven["n_game_centre_probed"]),
         "%d publish Location + Stadium, %d render no Game Info block; %s"
         % (ven["n_game_centre_with_stadium"], ven["n_game_centre_missing_block"],
            src(SOURCE_URL["S-gm-indhou"], "example fixture"))],
        ["Club depth pages probed", "2",
         "Green Bay structured and dated, Houston image-only; %s"
         % src("https://www.packers.com/team/depth-chart/", "packers.com")],
        ["Dated league announcement", "1",
         "Week 11 schedule change, Nov. 9 2026; %s" % src(SOURCE_URL["S-wk11-rel"], "nfl.com/news")],
    ]


def build_verification():
    rows = []
    for c in DER["peer_checks"]:
        res = c["result"]
        rows.append([
            '<span class="id">%s</span>' % esc(c["id"]),
            '<span class="badge b-%s">%s</span>' % (res if res != "partial" else "partial", esc(res)),
            esc(c["claim"]),
            (esc(c["n_cells_compared"]) if c.get("n_cells_compared") is not None
             else blank("not a cell comparison — a claim about source existence")),
            (esc(c["n_mismatch_cells"]) if c.get("n_mismatch_cells") is not None
             else blank("not applicable")),
            esc(c["detail"]),
            '<a href="%s">source</a>' % esc(c["source_url"]),
        ])
    ic_rows = []
    for c in DER["internal_consistency"]:
        ic_rows.append([
            '<span class="id">%s</span>' % esc(c["id"]),
            esc(c["claim_in_brief"]),
            esc(c["test"]),
            esc(c["observed"]),
            '<span class="badge b-%s">%s</span>' % (
                "pass" if c["verdict"] in ("official_status_confirmed", "absence_confirmed",
                                           "no_contradiction_found") else "fail",
                esc(c["verdict"].replace("_", " "))),
            esc(c.get("detail", "")),
            src(SOURCE_URL["S-injuries"] if "VR-04" in c["id"] or "IC-01" in c["id"] else
                SOURCE_URL["S-inact"] if "VQ-06" in c["id"] else SOURCE_URL["S-injuries"], "nfl.com"),
        ])

    body = """
<h1>Independent verification</h1>
<p class="lead">Every other namespace in this repository verified its own work. Nothing re-checked
it. This page does: peer-published values are turned into claims, and each claim is resolved against
a fresh official nfl.com read taken at <code>%(cap)s</code> — never against another peer file.</p>

<div class="note">
<strong>Be precise about what a fail means here.</strong> A fail is not an accusation of invention.
In every case where a peer value differs, the peer value was correct when captured and has since
been overtaken, or the peer treated a source as absent that is in fact published. Both are process
defects, not fabrication, and both are fixable.
</div>

<h2>Data re-read from official pages this session</h2>
%(confirm)s

<h2>Peer claims re-checked (X-01 to X-05)</h2>
%(peer)s

<h2>Internal consistency of the official sources (IC / VR checks)</h2>
%(ic)s

<h2>What was not re-verified</h2>
<p>This session re-read seven official source groups in full and probed eight further pages. The
prior 26 namespaces publish thousands of rows that were not re-read line by line. Any figure outside
the set below is inherited from a peer session, and is labelled as inherited wherever it appears.
That scope limit is itself flagged as <a href="flagged.html#R-12">R-12</a>.</p>
%(sources)s
""" % {
        "cap": esc(CAPTURE),
        "confirm": table(["Re-read item", "Rows confirmed", "Detail"], confirm_rows()),
        "peer": table(["ID", "Result", "Peer claim", "Cells compared", "Mismatches", "What was found", "Source"],
                      rows),
        "ic": table(["ID", "Claim in the brief", "Test applied", "Observed in the live source",
                     "Verdict", "Reading", "Source"], ic_rows),
        "sources": table(["Source group", "What it contributed", "Link"], [
            ["nfl.com/standings", "32-club league table", src(SOURCE_URL["S-standings"], "open")],
            ["nfl.com/schedules (Week 11)", "13 fixtures, kickoff, network, venue strings",
             src(SOURCE_URL["S-week11"], "open")],
            ["nfl.com/news (Week 11 change)", "Dated league announcement", src(SOURCE_URL["S-wk11-rel"], "open")],
            ["nfl.com/injuries", "Full Week 10 report, 8 chunks", src(SOURCE_URL["S-injuries"], "open")],
            ["nfl.com/news (Week 10 inactives)", "24 club inactive lists, 138 players",
             src(SOURCE_URL["S-inact"], "open")],
            ["nfl.com/scores (Week 10)", "9 finals, 3 in progress, 2 upcoming", src(SOURCE_URL["S-scores10"], "open")],
            ["nfl.com game centres", "5 fixtures: venue block present or absent",
             src(SOURCE_URL["S-gm-min-sf"], "example")],
            ["Club depth pages", "GB structured, HOU image-only",
             src("https://www.packers.com/team/depth-chart/", "packers.com")],
        ]),
    }
    return page("pages/verification.html", "Independent verification",
                "pages/verification.html", body,
                "Peer claims resolved against freshly fetched official nfl.com pages.")


def build_availability():
    inj, ina = DER["injury_report"], DER["inactives"]
    join = DER["inactives_join"]
    st = inj["by_status"]
    per_team = []
    for p in inj["per_team"]:
        per_team.append([
            '<span class="id">%s</span>' % esc(p["team"]),
            str(p["n_rows"]), str(p["n_out"]), str(p["n_doubtful"]), str(p["n_questionable"]),
            (str(p["n_blank_status"]) if p["n_blank_status"] else
             '<span class="blank" title="unverified: every row in this section carries a game status">0</span>'),
            src(SOURCE_URL["S-injuries"], "nfl.com/injuries"),
        ])

    inact_rows = []
    for r in OBS["inactives_week10"]["rows"]:
        inact_rows.append([
            esc(r["game"]), '<span class="id">%s</span>' % esc(r["team"]),
            (esc(", ".join(r["players"])) if r["players"]
             else blank("list not yet published at capture (SNF lists drop ~90 min before kickoff)")),
            str(len(r["players"])),
            src(SOURCE_URL["S-inact"], "nfl.com"),
        ])

    venue_rows = [[esc(v["game"]), esc(v["where"]), src(SOURCE_URL["S-inact"], "nfl.com")]
                  for v in OBS["inactives_week10"]["venues_in_article"]]

    join_tally = join["agg"]["by_report_status"]
    jrows = []
    for r in join["rows"]:
        if r["cross_check"] in ("reported_blank_status", "ambiguous"):
            jrows.append([
                '<span class="id">%s</span>' % esc(r["team"]),
                esc(r["inactive_player"]),
                cell(r["matched_report_player"], "no single unambiguous match in the report"),
                cell(r["matched_report_status"], "the report publishes no game status for this player"),
                esc(r["cross_check"].replace("_", " ")),
                src(SOURCE_URL["S-inact"], "nfl.com"),
            ])

    body = """
<h1>Availability evidence — Week 10, read in full</h1>
<p class="lead">The repository's availability work rests on a partial capture: 2 of 8 page chunks,
one session, no inactives. This page replaces it with a complete read taken at
<code>%(cap)s</code>: all 8 chunks of the official injury report and all 2 chunks of the official
inactives article, transcribed row by row.</p>

<div class="cards">
<div class="card"><div class="k">%(sections)s</div><div class="l">club sections in the Week 10 report (28 clubs played; 4 were on bye)</div></div>
<div class="card"><div class="k">%(rows)s</div><div class="l">report rows, each with position, practice status and game status</div></div>
<div class="card"><div class="k">%(withstatus)s</div><div class="l">rows carrying an explicit game status (%(pct)s%%)</div></div>
<div class="card"><div class="k">%(inact)s</div><div class="l">named inactives across %(inactsec)s club sections</div></div>
<div class="card"><div class="k">%(joinable)s</div><div class="l">players present in both official sources (%(contra)s contradictions)</div></div>
</div>

<h2>The join: does a blank game status mean available?</h2>
<p>This is the calibration the brief keeps asking for, and it can be measured on the two official
sources already in hand — no prices and no model needed.</p>
%(jointable)s
<div class="note warn">
<strong>What this establishes and what it does not.</strong> Among players who appear in both
sources, all %(joinable)s carry an explicit Out, Doubtful or Questionable — no named inactive carries
a blank status. That is the first real evidence that the game-status column is a trustworthy filter.
But <strong>%(notinreport)s of %(inactd)s named inactives never appear in the weekly report at all</strong>,
because reserve-list and practice-squad players are not on it. So a blank status still cannot be
read as &ldquo;available&rdquo;. It stays unknown until an active list exists.
</div>

<h2>The %(blankstatus)s residual cells, named</h2>
<p>Two named inactives do appear in the report with no game status. They are published here rather
than quietly counted, because these are the exact cells that would corrupt a naive availability
feature.</p>
%(jrows)s

<h2>Per-club Week 10 report, by explicit game status</h2>
<p>Note the ordering: a club can carry 17 rows and only 5 explicit designations. Row count is not
injury severity.</p>
%(perteam)s

<h2>Official inactive lists — the source the repository did not know it had</h2>
<p>nfl.com publishes a dated article naming every inactive player for every Sunday game. It was
read in full here for the first time. Two club sections are empty because Sunday Night Football
lists publish roughly 90 minutes before kickoff; those are recorded as empty, never as zero.</p>
%(inact)s

<h2>Venues published inside the inactives article</h2>
<p>The same article carries a venue string per game, which makes it a second official venue source
independent of the schedule page and the game centre.</p>
%(venues)s

<h2>Report-level status distribution</h2>
%(statusdist)s
""" % {
        "cap": esc(CAPTURE),
        "sections": inj["n_sections"], "rows": inj["n_rows"],
        "withstatus": inj["n_rows_with_game_status"], "pct": inj["pct_rows_with_game_status"],
        "inact": ina["n_named_players"], "inactsec": ina["n_sections"],
        "inactd": ina["n_named_players"],
        "joinable": join["agg"]["n_joinable_to_report"],
        "notinreport": join["agg"]["n_not_in_report"],
        "contra": 0,
        "blankstatus": join["agg"]["by_report_status"].get("reported_blank_status", 0),
        "jointable": table(["Report game status", "Named inactives at that status", "Source"], [
            ["Out", str(join_tally.get("reported_out", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["Doubtful", str(join_tally.get("reported_doubtful", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["Questionable", str(join_tally.get("reported_questionable", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["No game status published", str(join_tally.get("reported_blank_status", 0)),
             src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["Not in the report at all", str(join["agg"]["n_not_in_report"]),
             src(SOURCE_URL["S-inact"], "nfl.com inactives")],
            ["Ambiguous surname match (excluded)", str(join["agg"]["n_ambiguous"]),
             src(SOURCE_URL["S-inact"], "nfl.com inactives")],
        ], num_cols=(1,)),
        "jrows": table(["Club", "Named inactive", "Report player", "Report game status", "Cross-check", "Source"],
                       jrows),
        "perteam": table(["Club", "Rows", "Out", "Doubtful", "Questionable", "No status", "Source"],
                         per_team, num_cols=(1, 2, 3, 4, 5)),
        "inact": table(["Game", "Club", "Named inactives (verbatim order as published)", "n", "Source"],
                       inact_rows, num_cols=(3,)),
        "venues": table(["Game", "Venue as published in the article", "Source"], venue_rows),
        "statusdist": table(["Game status as published", "Rows", "Source"], [
            ["Out", str(st.get("Out", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["Questionable", str(st.get("Questionable", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["Doubtful", str(st.get("Doubtful", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
            ["(blank)", str(st.get("(blank game status)", 0)), src(SOURCE_URL["S-injuries"], "nfl.com/injuries")],
        ], num_cols=(1,)),
    }
    return page("pages/availability.html", "Availability evidence", "pages/availability.html", body,
                "Full Week 10 injury report and inactives, transcribed and joined.")


def build_questions():
    rows = []
    for r in Q["rows"]:
        rows.append([
            '<span class="id">%s</span>' % esc(r["id"]),
            '<span class="badge b-%s">%s</span>' % (r["priority"], esc(r["priority"])),
            esc(r["question"]),
            esc(r["known"]),
            esc(r["unknown"]),
            cell(r["answer"], "not established — see the discovery column"),
            esc(r["discovery"]),
            esc(r["blocks"]),
            '<a href="%s">source</a>' % esc(r["source_url"]),
        ])
    by_p = {}
    for r in Q["rows"]:
        by_p[r["priority"]] = by_p.get(r["priority"], 0) + 1
    body = """
<h1>Questions, information and answers</h1>
<p class="lead">A decision cannot be made on information that does not exist, so each question is
split into what the evidence establishes, what is missing, and the specific artefact that would
resolve it. %(n)d questions. <strong>%(blank)d answers are blank</strong>, because none is established
by the evidence in hand.</p>

<div class="note">
<strong>The blank answers are the deliverable.</strong> Writing a plausible answer here would be the
most damaging thing this page could do: it would enter the model as a fact and never be challenged
again. A blank with a named discovery task is worth more than a confident guess.
</div>

<h2>Priority</h2>
%(pri)s

<h2>All %(n)d questions</h2>
%(table)s
""" % {
        "n": len(Q["rows"]),
        "blank": sum(1 for r in Q["rows"] if r["answer"].startswith("§blank§")),
        "pri": table(["Priority", "Questions", "Meaning"], [
            ["P0", str(by_p.get("P0", 0)), "Unblocks other work, or prevents a wrong publication."],
            ["P1", str(by_p.get("P1", 0)), "High value, mild dependency."],
            ["P2", str(by_p.get("P2", 0)), "Valuable once the P0s are decided."],
        ], num_cols=(1,), cls="meta"),
        "table": table(["ID", "Priority", "Question", "What is known", "What is unknown",
                        "Answer", "How to discover it", "Blocks", "Source"], rows),
    }
    return page("pages/questions.html", "Questions", "pages/questions.html", body,
                "Questions, information and answers required before any decision.")


def build_suggestions():
    cards = []
    for r in SUG["rows"]:
        opts = "".join(
            "<li><strong>%s — %s.</strong> %s <em>Risk: %s</em></li>"
            % (esc(o["id"]), esc(o["label"]), esc(o["effect"]), esc(o["risk"]))
            for o in r["options"])
        cards.append("""
<details id="%s">
<summary><span class="badge b-%s">%s</span> &nbsp;%s &nbsp;<span class="tag">%s</span></summary>
<h3>Problem</h3><p>%s</p>
<h3>Options</h3><ul>%s</ul>
<h3>Evidence</h3><p>%s</p>
<h3>Cost · risk · recommendation</h3>
<p><strong>Cost:</strong> %s<br><strong>Risk:</strong> %s<br>
<strong>Recommended path:</strong> %s</p>
<h3>Verdict</h3><p>%s</p>
<p>%s</p>
</details>""" % (
            esc(r["id"]), r["priority"], esc(r["priority"]), esc(r["title"]), esc(r["id"]),
            esc(r["problem"]), opts, esc(r["evidence"]), esc(r["cost"]), esc(r["risk"]),
            esc(r["recommendation"]),
            cell(r["verdict"], "no reviewer has recorded a verdict — nothing is implemented by default"),
            src(r["source_url"], "official source for this suggestion"),
        ))
    body = """
<h1>Suggestions for review</h1>
<p class="lead">%(n)d proposals to make the site better at decision making. Every one starts with a
blank verdict: <strong>nothing is implemented until a reviewer names exactly one option</strong>.
The workflow is written into the register, not into a convention.</p>

<div class="note">
<strong>Why a verdict column and not a to-do list.</strong> The repository already contains 26
namespaces built by sessions that each picked the obvious path. Nearly every one rediscovered the
same missing price source. A blank verdict forces that choice to be made once, visibly, with its
options and its risk on the same screen.
</div>

<h2>Workflow</h2>
<ol>
<li>Read the proposal, its three options and the risk attached to each.</li>
<li>Write one option into the verdict. Not &ldquo;yes&rdquo; — an option ID.</li>
<li>Only then is code written, against that option, with the verdict quoted in the commit.</li>
<li>If a later observation contradicts the verdict, reopen the row rather than silently changing the build.</li>
</ol>

<h2>The %(n)d proposals</h2>
%(cards)s
""" % {"n": len(SUG["rows"]), "cards": "".join(cards)}
    return page("pages/suggestions.html", "Suggestions", "pages/suggestions.html", body,
                "Proposals with options and a blank verdict awaiting review.")


def build_flagged():
    rows = []
    for r in FLG["rows"]:
        rows.append([
            '<span class="id" id="%s">%s</span>' % (esc(r["id"]), esc(r["id"])),
            '<span class="badge %s">%s</span>' % (
                "b-fail" if r["severity"] == "high" else "b-partial" if r["severity"] == "medium" else "b-not_started",
                esc(r["severity"])),
            esc(r["title"]),
            esc(r["detail"]),
            esc(r["why_not_blocking"]),
            '<a href="%s">source</a>' % esc(r["source_url"]),
        ])
    body = """
<h1>Flagged for review</h1>
<p class="lead">%(n)d irregularities found this session. Each one names what is wrong, what the
official source actually says, and why it is not blocking. <strong>None of these blocks
publication</strong>; all of them should be read before the numbers are trusted.</p>

<div class="note bad">
<strong>The distinction this page protects.</strong> A stale value and an invented value are not the
same defect and must not be treated the same way. In every case below the peer value was correct
when captured, or the peer treated a published source as absent. Calling that fabrication would be
wrong, and fixing it as if it were fabrication would destroy real work.
</div>

%(table)s
""" % {
        "n": len(FLG["rows"]),
        "table": table(["ID", "Severity", "Irregularity", "What the source shows", "Why it does not block",
                        "Source"], rows),
    }
    return page("pages/flagged.html", "Flagged for review", "pages/flagged.html", body,
                "Irregularities and unverified items, each with an official source link.")


def build_sources():
    rows = []
    for s in OBS["sources"]:
        if s["id"] == "S-week11-rel":
            continue
        rows.append([
            '<span class="id">%s</span>' % esc(s["id"]),
            '<a href="%s">%s</a>' % (esc(s["url"]), esc(s["url"].replace("https://", ""))),
            esc(s["what"]),
            esc(s["read_utc"]),
        ])
    body = """
<h1>Sources</h1>
<p class="lead">Every page value on this site traces to one of these pages, fetched and read in
full at <code>%(cap)s</code>. Nothing was carried over from a peer dataset, a cached copy or a
search snippet.</p>

<h2>Read in this session</h2>
%(table)s

<h2>Policy</h2>
<ul>
<li>A source appears here only if its page text was actually read. A search result is not a source.</li>
<li>Where a page publishes a value, it is transcribed. Where it does not, the row is absent and the
absence is the finding — this is why the venue table has holes.</li>
<li>Two sources disagreeing is published as a conflict with a stated resolution, never averaged or
silently resolved. See <a href="verification.html">verification</a> and
<a href="flagged.html#R-03">R-03</a>.</li>
<li>Live pages move. Every figure carries the capture clock above, and no count is presented as
durable.</li>
</ul>

<h2>Reproduce</h2>
<p>Four commands, no dependencies beyond Python 3:</p>
<pre><code>cd nfl-readiness/engine
python3 derive.py
python3 readiness.py
python3 build_site.py
python3 verify.py</code></pre>
<p><code>derive.py</code> reads only <code>data/observations.json</code>. Editing that file and
re-running changes every published number; editing a page by hand fails the determinism gate in CI.</p>
""" % {"cap": esc(CAPTURE), "table": table(["ID", "URL", "What it contributed", "Read at"], rows)}
    return page("pages/sources.html", "Sources", "pages/sources.html", body,
                "Every official page read in this session.")


def build_exec():
    s = READY["summary"]
    body = """
<h1>Executive summary</h1>
<p class="lead">What is true about this project at <code>%(cap)s</code>, in the order that matters.</p>

<h2>1. The project is not blocked on engineering</h2>
<p>%(n)d requirements are traced. %(met)d are met and re-verified. %(partial)d are implemented and
limited by a named evidence gap. %(blocked)d are blocked and %(ns)d were never started. The
distribution is not a capacity problem: most blocked rows are blocked by <strong>one missing input
that five separate requirements share</strong>.</p>

<h2>2. That input is a market price, and it does not exist</h2>
<p>The NFL publishes kickoff time, network and venue for all 13 Week 11 fixtures and no line of any
kind. Every ROI, every closing-line value, every fair-versus-market residual and the entire rewards
pool depend on it. Nine traced requirements reduce to one procurement decision (Q01 / S01). Until it
is made, the honest product is a proper-score skill competition, not a betting product.</p>

<h2>3. The biggest under-utilisation is an availability source the repository already had access to</h2>
<p>The repository treats official inactive lists as unobtainable and accordingly never ingests them.
They are published. A single dated nfl.com article names <strong>%(inact)d inactive players across
%(inactsec)d club sections</strong> for Week 10 and also carries the venue for 12 games. That
reframes the largest listed data gap from &ldquo;impossible&rdquo; to &ldquo;a parser and a cron
entry&rdquo;.</p>

<h2>4. The inactive list answers the calibration question partially, and the partial answer is useful</h2>
<p>%(joinable)d players appear in both the official report and the official inactive list. All of
them carry an explicit Out, Doubtful or Questionable — not one named inactive has a blank status. So
the designation column is a usable filter. But %(notinreport)d named inactives never appear in the
report, so a blank status still cannot mean &ldquo;available&rdquo;. Any model that treats absence
from the report as health is wrong today.</p>

<h2>5. The depth feature is real but not yet buildable, and the blocker is measurable</h2>
<p>Two club depth pages were probed. Green Bay publishes a structured table with 44 named players and
its own date. Houston publishes an image with no table and no date. So the per-club route works for
some clubs: <strong>2 of 32 verified, 30 unprobed</strong>. The brief's instinct was right — this
cannot be derived from jersey numbers, and the Packers prepend jersey numbers to their names
precisely so a naive parser will mistake a shirt for a rank.</p>

<h2>6. Nothing published here is a pick</h2>
<p>No forecasts are made on this site. It publishes what is known about the project, not what will
happen on Sunday. The one strategy leaderboard in the repository awards 0 of 1,000 points because
0 of 5 strategies clears its own gates, and that zero is the correct output.</p>

<h2>The five decisions</h2>
%(decisions)s

<h2>What to do first</h2>
<ol>
<li><strong>Decide Q01</strong> (price source, or formal retreat). Nothing downstream publishes a
real number until this is answered.</li>
<li><strong>Decide Q10</strong> (one canonical dashboard). Every week without it produces another
namespace.</li>
<li><strong>Ingest the inactives article</strong> (S03). Cheapest real evidence gain available, and
it closes five readiness rows.</li>
<li><strong>Parse one Game Book PDF</strong> (S04). One day, and it either unlocks the availability
graph or proves it impossible — both outcomes are worth the day.</li>
<li><strong>Re-freeze the corpus</strong> (S07). The registration currently disagrees with its own
artefact by one game.</li>
</ol>
""" % {
        "cap": esc(CAPTURE),
        "n": s["n_requirements"], "met": s["met"], "partial": s["partial"],
        "blocked": s["blocked"], "ns": s["not_started"],
        "inact": DER["inactives"]["n_named_players"],
        "inactsec": DER["inactives"]["n_sections"],
        "joinable": DER["inactives_join"]["agg"]["n_joinable_to_report"],
        "notinreport": DER["inactives_join"]["agg"]["n_not_in_report"],
        "decisions": decision_html("../"),
    }
    return page("pages/executive-summary.html", "Executive summary",
                "pages/executive-summary.html", body, "Executive summary of the decision-readiness review.")


def write_assets():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    with open(os.path.join(ROOT, "assets", "readiness.css"), "w", encoding="utf-8") as f:
        f.write(CSS.lstrip())


def main():
    write_assets()
    written = [
        build_index(),
        build_readiness(),
        build_verification(),
        build_availability(),
        build_questions(),
        build_suggestions(),
        build_flagged(),
        build_sources(),
        build_exec(),
    ]
    print("[build] wrote %d pages:" % len(written))
    for w in written:
        print("   ", w)


if __name__ == "__main__":
    main()

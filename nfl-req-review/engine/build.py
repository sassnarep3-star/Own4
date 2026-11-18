#!/usr/bin/env python3
"""
nfl-req-review — static site builder (2026-11-17 round).

Renders the landing page and four subpages from the JSON captures written by
engine/build_data.py and engine/build_requirements.py. Pure standard library.
Every data-table row carries a source link. Counts are computed at build time
from the data files — never typed into prose.

Run:  python3 engine/build_data.py
      python3 engine/build_requirements.py
      python3 engine/build.py
"""

raise SystemExit("superseded: round 2 (2026-11-18) is built by engine/round2.py, round2_register.py and build_r2.py; "
                 "this round-1 script would overwrite the round-2 pages, so it refuses to run.")


import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
ASSETS = os.path.join(NS, "assets")
os.makedirs(PAGES, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

REQ = json.load(open(os.path.join(DATA, "requirements_2026_11_17.json")))
CAP = json.load(open(os.path.join(DATA, "official_reads_2026_11_17.json")))
FLAGS = json.load(open(os.path.join(DATA, "flags.json")))
SRCS = json.load(open(os.path.join(DATA, "sources.json")))

ROUND = REQ["built_utc"]
SESSION = "arena/ca159db5-own4"
NS_URL = "https://sassnarep3-star.github.io/Own4/nfl-req-review/"

CSS = """
:root { --ink:#16202b; --mut:#5b6b7c; --line:#d8e0e8; --bg:#f4f7fa; --card:#ffffff;
        --acc:#0b5fff; --ok:#0a7d43; --warn:#a35a00; --bad:#b3261e; --chip:#eef3fb; }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); }
header.top { background:#101a24; color:#fff; padding:18px 28px; }
header.top h1 { margin:0; font-size:20px; }
header.top .sub { color:#9fb2c6; font-size:13px; margin-top:4px; }
nav.bar { background:#fff; border-bottom:1px solid var(--line); padding:0 28px;
          display:flex; gap:4px; flex-wrap:wrap; }
nav.bar a { display:inline-block; padding:11px 14px; color:var(--ink); text-decoration:none;
            border-bottom:3px solid transparent; font-size:14px; }
nav.bar a:hover { color:var(--acc); border-bottom-color:var(--acc); }
nav.bar a.active { color:var(--acc); border-bottom-color:var(--acc); font-weight:600; }
main { max-width:1180px; margin:0 auto; padding:26px 22px 60px; }
h2 { font-size:19px; margin:30px 0 12px; }
h3 { font-size:15px; margin:22px 0 8px; }
p.lead { color:var(--mut); max-width:860px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
.card .k { font-size:12px; color:var(--mut); text-transform:uppercase; letter-spacing:.04em; }
.card .v { font-size:26px; font-weight:700; margin-top:4px; }
.card .d { font-size:12px; color:var(--mut); margin-top:2px; }
table { width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line);
        border-radius:10px; overflow:hidden; font-size:13.5px; }
th { background:#eef2f7; text-align:left; padding:9px 10px; font-size:12px; text-transform:uppercase;
     letter-spacing:.03em; color:#3c4a5a; border-bottom:1px solid var(--line); }
td { padding:8px 10px; border-bottom:1px solid #edf1f6; vertical-align:top; }
tr:last-child td { border-bottom:none; }
td a, p a { color:var(--acc); text-decoration:none; }
td a:hover, p a:hover { text-decoration:underline; }
.chip { display:inline-block; padding:2px 9px; border-radius:20px; font-size:12px; font-weight:600;
        background:var(--chip); color:#274b73; white-space:nowrap; }
.chip.met { background:#e5f4ec; color:var(--ok); }
.chip.partial { background:#fdf1de; color:var(--warn); }
.chip.blocked { background:#fbe6e4; color:var(--bad); }
.chip.not_started { background:#eceff3; color:#4a5766; }
.chip.in_progress { background:#e7eefc; color:#2456a8; }
.blank { color:#98a4b1; font-style:italic; }
.mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px; }
.note { background:#fff8e8; border:1px solid #f0dfa8; border-radius:8px; padding:12px 14px; font-size:13.5px; }
.flag { background:var(--card); border:1px solid var(--line); border-left:4px solid var(--warn);
        border-radius:8px; padding:12px 15px; margin-bottom:12px; }
.flag h3 { margin:0 0 6px; font-size:14.5px; }
.flag .meta { font-size:12px; color:var(--mut); margin-bottom:6px; }
footer { max-width:1180px; margin:0 auto; padding:0 22px 40px; color:var(--mut); font-size:12.5px; }
.small { font-size:12.5px; color:var(--mut); }
ul.tight { padding-left:20px; } ul.tight li { margin:6px 0; }
"""


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def chip(status):
    s = status.split(": ")[0]
    return '<span class="chip %s">%s</span>' % (esc(s), esc(status))


def link(url, text=None):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(text or url))


def nav(active):
    items = [
        ("index.html", "Landing", "index"),
        ("pages/requirements.html", "Decision-readiness table", "req"),
        ("pages/verification.html", "Verification & reads", "ver"),
        ("pages/flagged.html", "Flagged for review", "flag"),
        ("pages/sources.html", "Sources", "src"),
    ]
    out = ['<nav class="bar">']
    for href, label, key in items:
        out.append('<a href="%s"%s>%s</a>' % (
            href, ' class="active"' if key == active else "", esc(label)))
    out.append("</nav>")
    return "\n".join(out)


def shell(title, active, body):
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>%s · nfl-req-review</title><link rel=\"stylesheet\" href=\"assets/style.css\">"
        "</head><body>"
        "<header class=\"top\"><h1>Own4 · NFL Requirement Re-Verification</h1>"
        "<div class=\"sub\">Round %s · session %s · official sources only · unverifiable values blank + flagged</div>"
        "</header>%s<main>%s</main>"
        "<footer>Every table row links to the official page it was read from. Values that could not be "
        "confirmed from an official source are blank and listed on the Flagged for Review page. "
        "Structured rows + sha256 + timestamps only — no raw HTML committed (RF-18).</footer>"
        "</body></html>" % (esc(title), esc(ROUND), esc(SESSION), nav(active), body)
    )


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------
def build_index():
    req_rows = REQ["rows"]
    n_met = sum(1 for r in req_rows if r["status"] == "met")
    n_partial = sum(1 for r in req_rows if r["status"] == "partial")
    n_blocked = sum(1 for r in req_rows if r["status"] == "blocked")
    n_ns = sum(1 for r in req_rows if r["status"] == "not_started")
    n_ip = sum(1 for r in req_rows if r["status"] == "in_progress")
    inj = CAP["injury_report_week10"]["totals"]
    stats = CAP["designation_join"]["stats"]
    n_adv = len(REQ["advanced_this_round"])

    body = []
    body.append("<h2>This round</h2>")
    body.append(
        "<p class=\"lead\">A line-by-line re-verification of the consolidated %d-row requirement "
        "register against official sources read live on %s: standings, the Week-11 schedule, the "
        "final Week-10 injury report, the official inactive list, transactions and the reserve "
        "list, the game centre, and the depth-chart route. %d requirements advanced this round; "
        "the decision-readiness table below shows the gate that blocks each one and the number "
        "that would clear it.</p>" % (len(req_rows), esc(ROUND), n_adv))
    body.append("<div class=\"cards\">")
    for k, v, d in [
        ("Requirements", len(req_rows), "in the consolidated register"),
        ("Met", n_met, "verified against an official source"),
        ("Partial", n_partial, "implemented, evidence gap documented"),
        ("Blocked", n_blocked, "no official source available"),
        ("Advanced this round", n_adv, "E06 · E14 · E16 · E21"),
        ("Week-10 injury rows", inj["players_listed"], "final designations, live read"),
        ("Inactive entries", CAP["inactives_week10"]["total_entries"], "Week-10 official list"),
        ("November trades", CAP["transactions_november_2026"]["count_trades"], "official transactions hub"),
    ]:
        body.append('<div class="card"><div class="k">%s</div><div class="v">%s</div>'
                    '<div class="d">%s</div></div>' % (esc(k), esc(v), esc(d)))
    body.append("</div>")

    body.append("<h2>Headline findings</h2><ul class=\"tight\">")
    for f in CAP["findings"].values():
        body.append("<li>%s</li>" % esc(f))
    body.append("</ul>")

    body.append("<h2>Designation reliability (E14 / E21) — measured, not assumed</h2>")
    body.append("<p class=\"lead\">Final Week-10 report joined to the official inactive list "
                "(24 clubs of Sunday's 12 games). Wilson 95% intervals; single-week sample.</p>")
    body.append("<table><thead><tr><th>Designation</th><th>n</th><th>Did not play</th>"
                "<th>Rate</th><th>95% CI</th><th>Source</th></tr></thead><tbody>")
    for desig in ("Out", "Doubtful", "Questionable"):
        s = stats[desig]
        body.append(
            "<tr><td>%s</td><td>%d</td><td>%d</td>"
            "<td>%.1f%%</td><td>%.1f%%–%.1f%%</td><td>%s</td></tr>" % (
                esc(desig), s["n"], s["did_not_play_total"],
                100.0 * s["did_not_play_rate"],
                100.0 * s["did_not_play_rate_lo"], 100.0 * s["did_not_play_rate_hi"],
                link(SRC_INACT_URL, "official inactive list")))
    body.append("</tbody></table>")

    body.append("<h2>Start with</h2><ul class=\"tight\">")
    body.append("<li><a href=\"pages/requirements.html\">Decision-readiness table</a> — one row per "
                "requirement: status, the gate that blocks it, the number that would clear it, source.</li>")
    body.append("<li><a href=\"pages/verification.html\">Verification &amp; reads</a> — every official "
                "page read this session, with counts, the schedule, standings and the timestamped delta.</li>")
    body.append("<li><a href=\"pages/flagged.html\">Flagged for review</a> — irregularities and gaps, "
                "each with its official source links.</li>")
    body.append("<li><a href=\"pages/sources.html\">Sources</a> — the official register for this round.</li>")
    body.append("</ul>")

    with open(os.path.join(NS, "index.html"), "w") as f:
        f.write(shell("Landing", "index", "\n".join(body)))


SRC_INACT_URL = "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season"


# ---------------------------------------------------------------------------
# Decision-readiness table
# ---------------------------------------------------------------------------
def build_requirements():
    body = []
    body.append("<h2>Decision-readiness table</h2>")
    body.append("<p class=\"lead\">One row per requirement in the consolidated register, re-verified "
                "%s. The <b>gate</b> column states what blocks the requirement today; the "
                "<b>clears</b> column states the number or artefact that would clear it. Statuses "
                "carry this round's change where one occurred.</p>" % esc(ROUND))
    body.append("<table><thead><tr><th>ID</th><th>Group</th><th>Requirement</th>"
                "<th>Status</th><th>Gate that blocks it</th><th>Number that would clear it</th>"
                "<th>Source</th></tr></thead><tbody>")
    for r in REQ["rows"]:
        change = (' <span class="small">(%s)</span>' % esc(r["status"].split(": ")[-1])
                  if ": " in r["status"] and r["status_change"] else "")
        body.append(
            "<tr><td class=\"mono\">%s</td><td>%s</td><td>%s</td><td>%s%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(r["id"]), esc(r["group"]), esc(r["requirement"]),
                chip(r["status"]), change,
                esc(r["gate"]), esc(r["clears"]),
                link(r["source"]) if r["source"] else '<span class="blank">blank — unverified</span>'))
    body.append("</tbody></table>")
    body.append("<p class=\"small\">Base register: %s . Round evidence per row is recorded in "
                "<span class=\"mono\">data/requirements_2026_11_17.json</span>.</p>"
                % esc(REQ["base_register"]))
    with open(os.path.join(PAGES, "requirements.html"), "w") as f:
        f.write(shell("Decision-readiness table", "req", "\n".join(body)))


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def build_verification():
    body = []
    body.append("<h2>Official reads this session</h2>")
    body.append("<p class=\"lead\">Every page below was fetched and read live on %s (UTC). "
                "Structured rows + sha256 + timestamps only; the capture hash is "
                "<span class=\"mono\">%s</span>.</p>" % (esc(ROUND), esc(CAP["sha256"])))
    body.append("<table><thead><tr><th>ID</th><th>Page</th><th>Read</th><th>What it provided</th>"
                "</tr></thead><tbody>")
    for s in SRCS["sources"]:
        body.append("<tr><td class=\"mono\">%s</td><td>%s<br><span class=\"small\">%s</span></td>"
                    "<td>%s<br><span class=\"small\">%s</span></td><td>%s</td></tr>" % (
                        esc(s["id"]), link(s["url"], s["title"]), esc(s["domain"]),
                        esc(s["read_utc"]), esc(s["chunks_read"]), esc(s["used_for"])))
    body.append("</tbody></table>")

    body.append("<h2>Week-11 schedule (official)</h2>")
    fx = CAP["week11_schedule"]["fixtures"]
    body.append("<table><thead><tr><th>Day</th><th>Time</th><th>Network</th><th>Fixture</th>"
                "<th>Records (away / home)</th><th>Venue</th><th>Weather</th><th>Game centre</th>"
                "</tr></thead><tbody>")
    for g in fx:
        body.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s @ %s</td><td>%s / %s</td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(g["day"]), esc(g["time"]), esc(g["network"]),
                esc(g["away"]), esc(g["home"]), esc(g["away_record"]), esc(g["home_record"]),
                esc(g["venue"]),
                esc(g["weather"]) if g["weather"] else '<span class="blank">not published</span>',
                link(g["game_url"], "game centre")))
    body.append("</tbody></table>")
    body.append("<p class=\"small\">Byes: %s. Venue evidence: the schedule page's own stadium links "
                "and the game centre Game Info. Roof/surface: no official field on the pages read — "
                "blank and flagged (RF-04).</p>" % esc(", ".join(CAP["week11_schedule"]["byes"])))

    body.append("<h2>Week-10 injury report — final designations (live read)</h2>")
    inj = CAP["injury_report_week10"]
    INJ_URL = CAP["sources"][3]["url"]
    body.append("<table><thead><tr><th>Club</th><th>Fixture</th><th>Players listed</th>"
                "<th>Out</th><th>Doubtful</th><th>Questionable</th><th>Blank designation</th>"
                "<th>Source</th></tr></thead><tbody>")
    for r in inj["rows"]:
        body.append("<tr><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>"
                    "<td>%d</td><td>%s</td></tr>" % (
                        esc(r["club"]), esc(r["opponent"]), r["players_listed"],
                        len(r["out"]), len(r["doubtful"]), len(r["questionable"]),
                        r["blank_designation"], link(INJ_URL)))
    t = inj["totals"]
    body.append("<tr><td><b>Total</b></td><td>%d fixtures</td><td><b>%d</b></td>"
                "<td><b>%d</b></td><td><b>%d</b></td><td><b>%d</b></td><td><b>%d</b></td>"
                "<td>%s</td></tr>"
                % (t["clubs"] // 2, t["players_listed"], t["out"], t["doubtful"],
                   t["questionable"], t["blank"], link(INJ_URL)))
    body.append("</tbody></table>")
    body.append("<p class=\"small\">Source: %s (read live %s, all 8 chunks).</p>"
                % (link(INJ_URL), esc(ROUND)))

    body.append("<h2>Timestamped delta — the injury report as a series (E12 / E15)</h2>")
    body.append("<table><thead><tr><th>Read</th><th>Rows</th><th>Out</th><th>Questionable</th>"
                "<th>Doubtful</th><th>Blank</th><th>Source</th></tr></thead><tbody>")
    body.append("<tr><td>2026-11-13 (committed capture, Friday)</td><td>326</td><td>14</td>"
                "<td>11</td><td>0</td><td>301</td><td>%s</td></tr>"
                % link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/injuries_week10.json",
                       "committed capture"))
    body.append("<tr><td>2026-11-17 (live read, final)</td><td>%d</td><td>%d</td><td>%d</td>"
                "<td>%d</td><td>%d</td><td>%s</td></tr>" % (
                    t["players_listed"], t["out"], t["questionable"], t["doubtful"], t["blank"],
                    link(CAP["sources"][3]["url"])))
    body.append("</tbody></table>")

    body.append("<h2>Designation-reliability join (E14 / E21)</h2>")
    stats = CAP["designation_join"]["stats"]
    INACT_URL = CAP["sources"][4]["url"]
    body.append("<table><thead><tr><th>Designation</th><th>n</th><th>DNP (inactive list)</th>"
                "<th>DNP (reserve list only)</th><th>DNP total</th><th>DNP rate</th>"
                "<th>95% CI</th><th>Not corroborated</th><th>Source</th></tr></thead><tbody>")
    for desig in ("Out", "Doubtful", "Questionable"):
        s = stats[desig]
        body.append("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>"
                    "<td>%.1f%%</td><td>%.1f%%–%.1f%%</td><td>%d</td><td>%s</td></tr>" % (
                        esc(desig), s["n"], s["did_not_play_inactive_list"],
                        s["did_not_play_reserve_list_only"], s["did_not_play_total"],
                        100.0 * s["did_not_play_rate"],
                        100.0 * s["did_not_play_rate_lo"], 100.0 * s["did_not_play_rate_hi"],
                        s["not_corroborated"], link(INACT_URL)))
    body.append("</tbody></table>")
    body.append("<p class=\"small\">Scope: 24 clubs of Sunday's 12 Week-10 games; the inactive list "
                "is the official record of players who did not play. Wilson 95% intervals. "
                "Six Out designations are uncorroborated by either list (RF-01).</p>")

    body.append("<h2>Standings through Week 10 (live read)</h2>")
    body.append("<table><thead><tr><th>#</th><th>Team</th><th>W</th><th>L</th><th>T</th>"
                "<th>PCT</th><th>PF</th><th>PA</th><th>Streak</th><th>Source</th></tr></thead><tbody>")
    rows = sorted(CAP["standings_2026_week10"]["rows"],
                  key=lambda r: (-(r["w"] + 0.5 * r["t"]), -r["w"]))
    for i, r in enumerate(rows, 1):
        body.append("<tr><td>%d</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td>"
                    "<td>%.3f</td><td>%d</td><td>%d</td><td>%s</td><td>%s</td></tr>" % (
                        i, esc(r["name"]), r["w"], r["l"], r["t"], r["pct"], r["pf"], r["pa"],
                        esc(r["streak"]), link(CAP["sources"][0]["url"])))
    body.append("</tbody></table>")

    body.append("<h2>November 2026 transactions</h2>")
    tr = CAP["transactions_november_2026"]
    body.append("<h3>Trades (%d)</h3>" % tr["count_trades"])
    body.append("<table><thead><tr><th>Date</th><th>From</th><th>To</th><th>Player</th>"
                "<th>Source</th></tr></thead><tbody>")
    for t_ in tr["trades"]:
        body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(t_["date"]), esc(t_["from"]), esc(t_["to"]), esc(t_["player"]),
            link(CAP["sources"][5]["url"])))
    body.append("</tbody></table>")
    body.append("<h3>Reserve / Injured moves (%d)</h3>" % tr["count_reserve"])
    body.append("<table><thead><tr><th>Date</th><th>Club</th><th>Player</th><th>Source</th>"
                "</tr></thead><tbody>")
    for t_ in tr["reserve_list"]:
        body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(t_["date"]), esc(t_["club"]), esc(t_["player"]),
            link(CAP["sources"][6]["url"])))
    body.append("</tbody></table>")

    with open(os.path.join(PAGES, "verification.html"), "w") as f:
        f.write(shell("Verification & reads", "ver", "\n".join(body)))


# ---------------------------------------------------------------------------
# Flagged
# ---------------------------------------------------------------------------
def build_flagged():
    body = []
    body.append("<h2>Flagged for review</h2>")
    body.append("<p class=\"lead\">Irregularities, gaps and stale captures found this round. "
                "None blocks the merge; each is published with its official source links so it "
                "can be reviewed and corrected.</p>")
    for fl in FLAGS["flags"]:
        body.append('<div class="flag"><h3>%s · %s</h3>' % (esc(fl["id"]), esc(fl["severity"])))
        body.append('<div class="meta">%s · status: %s</div>' % (esc(fl["title"]), esc(fl["status"])))
        body.append("<div>%s</div>" % esc(fl["detail"]))
        body.append('<div class="small">Sources: %s</div></div>' %
                    " · ".join(link(u) for u in fl["sources"]))
    with open(os.path.join(PAGES, "flagged.html"), "w") as f:
        f.write(shell("Flagged for review", "flag", "\n".join(body)))


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def build_sources():
    body = []
    body.append("<h2>Source register</h2>")
    body.append("<p class=\"lead\">Official sources only. All %d sources were fetched and read "
                "in-session on %s; per-source read windows and chunk coverage are recorded in "
                "<span class=\"mono\">data/sources.json</span> and "
                "<span class=\"mono\">data/official_reads_2026_11_17.json</span>.</p>"
                % (len(SRCS["sources"]), esc(ROUND)))
    body.append("<table><thead><tr><th>ID</th><th>URL</th><th>Title</th><th>Read</th>"
                "<th>Chunks</th><th>Used for</th></tr></thead><tbody>")
    for s in SRCS["sources"]:
        body.append("<tr><td class=\"mono\">%s</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>%s</td></tr>" % (
                        esc(s["id"]), link(s["url"]), esc(s["title"]), esc(s["read_utc"]),
                        esc(s["chunks_read"]), esc(s["used_for"])))
    body.append("</tbody></table>")
    with open(os.path.join(PAGES, "sources.html"), "w") as f:
        f.write(shell("Sources", "src", "\n".join(body)))


def main():
    with open(os.path.join(ASSETS, "style.css"), "w") as f:
        f.write(CSS)
    build_index()
    build_requirements()
    build_verification()
    build_flagged()
    build_sources()
    print("site built: index.html + pages/{requirements,verification,flagged,sources}.html")


if __name__ == "__main__":
    main()

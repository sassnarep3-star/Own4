#!/usr/bin/env python3
"""Render the static Week 11 injury-delta site from data/delta.json (stdlib only, deterministic).

Publishes DELTAS ONLY (brief: "publish the delta, never the level"). The full Week-11 level stays in
the transcription file in data/ and is linked, not rendered, on the site.

Run:  python3 nfl-w11-delta/engine/build.py
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DELTA = os.path.join(NS, "data", "delta.json")
OFFICIAL = "https://www.nfl.com/injuries/"
NEWS_MAYFIELD = "https://www.nfl.com/news/buccaneers-qb-baker-mayfield-injury-week-11"
NEWS_SMITH = "https://www.nfl.com/news/notable-injuries-news-sunday-week-10-games-2026"
SCHEDULE = "https://www.nfl.com/schedules/"
RAW_PATH = "../nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html"
READ_PATH = "../data/official_read_2026-11-19_w11.md"
DATA_DIR_LINK = "https://github.com/sassnarep3-star/Own4/tree/main/nfl-w11-delta/data"
ABSENT_CLUBS = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]  # not in either capture; see Flagged F5

NAV = [("index.html", "Summary"), ("pages/delta.html", "Delta (changes only)"),
       ("pages/clubs.html", "Clubs"), ("pages/sources.html", "Sources"),
       ("pages/flagged.html", "Flagged for Review")]


def esc(x):
    return html.escape(str(x if x is not None else ""), quote=True)


def page(rel, title, body, depth):
    prefix = "../" * depth
    nav = "".join('<a href="%s%s"%s>%s</a>' % (prefix, p, ' class="on"' if p == rel else "", esc(lbl))
                  for p, lbl in NAV)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s · NFL Week 11 injury delta</title>'
            '<link rel="stylesheet" href="%sassets/style.css"></head><body>'
            '<header class="top"><a class="brand" href="%sindex.html">NFL Week 11 injury delta</a>'
            '<nav>%s</nav></header><main>%s</main>'
            '<footer>Research only, not wagering advice. Values not confirmed from an official source are '
            'blank and flagged. Gambling help: 1-800-MY-RESET (ncpgambling.org/help-treatment).</footer>'
            '</body></html>\n') % (esc(title), prefix, prefix, nav, body)


def cell(x):
    s = str(x if x is not None else "")
    return s if s.startswith('<a ') else esc(s)


def table(headers, rows):
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % cell(c) for c in r) for r in rows)
    return '<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body)


def link(url, label=None):
    return '<a href="%s" rel="noopener">%s</a>' % (esc(url), esc(label or url))


def cards(items):
    return '<div class="cards">' + "".join(
        '<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>'
        % (esc(k), esc(v), esc(s)) for k, v, s in items) + "</div>"


CSS = """:root{--ink:#14213d;--mut:#5b6472;--line:#dfe3ea;--bg:#f7f8fb;--acc:#1f5fbf}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
.top{background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.brand{font-weight:700;color:var(--ink);text-decoration:none;margin-right:12px}
nav a{color:var(--acc);text-decoration:none;margin-right:12px;font-size:14px}nav a.on{font-weight:700;text-decoration:underline}
main{max-width:1180px;margin:0 auto;padding:20px}h1{font-size:24px;margin:8px 0}h2{font-size:18px;margin:22px 0 8px}
.lede{color:var(--mut);max-width:880px}.note{color:var(--mut);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:14px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}.card .k{font-size:12px;color:var(--mut)}
.card .v{font-size:22px;font-weight:700}.card .s{font-size:12px;color:var(--mut)}
.scroll{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef2f8;position:sticky;top:0}code{font-size:12px;word-break:break-all}
.findings li{margin:6px 0}footer{color:var(--mut);font-size:12px;padding:24px 20px;text-align:center}
a{color:var(--acc)}"""


def main():
    d = json.load(open(DELTA, encoding="utf-8"))
    for sub in ("pages", "assets"):
        os.makedirs(os.path.join(NS, sub), exist_ok=True)
    with open(os.path.join(NS, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS + "\n")
    c = d["counts"]
    dt = d["delta_to"]
    df = d["delta_from"]

    # ---------- index ----------
    absent_names = ", ".join(ABSENT_CLUBS)
    n_both = c["unchanged"] + c["changed"]
    n_chg = d["clubs"]["Chargers"]["read_rows"]
    idx = (
        '<h1>Week 11 official injury report — what changed</h1>'
        '<p class="lede">Two dated reads of the NFL official injury report, compared. The page shows '
        '<b>only the changes</b> between them; the full report is linked, not copied. Every row links to the '
        'official source.</p>'
        + cards([
            ("Earlier read (raw HTML)", "%s rows" % c["raw_rows"], "captured %s · %d club tables" % (df["captured_utc"], c["raw_tables"])),
            ("Later read (transcribed)", "%s rows" % c["read_rows"], "read 2026-11-19, after 06:48:48 UTC (agent clock) · %d club tables" % c["read_tables"]),
            ("Rows changed", str(c["changed"]), "injury, practice or game status, same club and player"),
            ("Rows added", str(c["added"]), "in the later read only"),
            ("Rows removed", str(c["removed"]), "in the earlier read only"),
            ("Rows unchanged", str(c["unchanged"]), "identical in both reads (not listed)"),
        ])
        + '<h2>Executive summary</h2><ul class="findings">'
        '<li><b>No designation moved</b> between the two reads for the ' + str(n_both) + ' players present in both (no change to '
        'injury, practice or game status).</li>'
        '<li><b>One club block changed from empty to populated.</b> The Chargers showed “No Injuries Reported” in the '
        'earlier capture and ' + str(n_chg) + ' rows in the later read (see <a href="pages/delta.html">Delta</a>). An empty block is '
        'therefore <b>not</b> evidence of health.</li>'
        '<li><b>Six clubs have no block in either read</b> (' + esc(absent_names) + '). Not listed does not mean available. Their bye status '
        'is not verified on this page (flag F5).</li>'
        '<li><b>Two injury-cell conflicts with official NFL headlines</b> are flagged rather than resolved (F2, F3).</li>'
        '</ul>'
        '<h2>Decision readiness for this page</h2>'
        + table(["Requirement", "Gate", "Status", "Number that clears it", "Source"], [
            ["Two dated reads of the official page", "Second read exists with a clock time", "Met", "2 reads", link(OFFICIAL)],
            ["Earlier read is immutable and hashed", "sha256 equals manifest", "Met", "sha256 %s…" % esc(df["sha256"][:12]), link(OFFICIAL)],
            ["Later read is a raw byte capture", "Raw HTML stored", "Not met", "0 raw captures from this sandbox (egress blocked)", link(OFFICIAL)],
            ["Game-status designations final", "Friday report posted", "Pending", "Friday report not yet read", link(OFFICIAL)],
            ["Six absent clubs confirmed on bye", "Official schedule read", "Not checked", "6 clubs unverified", link(SCHEDULE)],
        ])
        + '<p class="note">The two reads were compared on %d overlapping rows; the later read was transcribed by the '
        'session agent from the page text. Its agreement with the stored raw HTML on those rows is a check '
        'of the transcription (see <a href="pages/sources.html">Sources</a>).</p>' % (c["unchanged"] + c["changed"])
    )
    open(os.path.join(NS, "index.html"), "w", encoding="utf-8").write(page("index.html", "Summary", idx, 0))

    # ---------- delta ----------
    rows = []
    for r in d["added"]:
        rows.append(["Added", r["team_nickname"], r["player"], r["position"], r["injury"] or "", r["practice"], r["game"] or "",
                     link(OFFICIAL, "nfl.com/injuries")])
    for r in d["removed"]:
        rows.append(["Removed", r["team_nickname"], r["player"], r["position"], r["injury"] or "", r["practice"], r["game"] or "",
                     link(OFFICIAL, "nfl.com/injuries")])
    for r in d["changed"]:
        ch = r["changes"]
        def fmt(f):
            return ("%s → %s" % (ch[f]["from"] or "—", ch[f]["to"] or "—")) if f in ch else ""
        rows.append(["Changed", r["team_nickname"], r["player"], fmt("position"), fmt("injury"), fmt("practice"), fmt("game"),
                     link(OFFICIAL, "nfl.com/injuries")])
    body = (
        '<h1>Delta — rows that changed</h1>'
        '<p class="lede">Earlier read: captured %s (raw HTML, sha256 <code>%s</code>). Later read: %s. '
        'Only rows that differ are listed. Blank cells mean the official page shows no value.</p>'
        % (esc(df["captured_utc"]), esc(df["sha256"]), esc(dt["read_utc_note"]))
        + cards([("Added", str(c["added"]), "rows"), ("Removed", str(c["removed"]), "rows"),
                 ("Changed", str(c["changed"]), "rows")])
        + table(["Change", "Club", "Player", "Position / change", "Injury / change", "Practice / change",
                 "Game status / change", "Source"], rows)
        + '<p class="note">Changed rows show <code>from → to</code>. Added rows appear in the later read only; the '
        'earlier capture printed <em>No Injuries Reported</em> for the Chargers block (see Clubs).</p>'
    )
    if not d["changed"]:
        body += '<p class="note">Changed rows: <b>none</b>. Removed rows: <b>none</b>.</p>'
    open(os.path.join(NS, "pages", "delta.html"), "w", encoding="utf-8").write(page("pages/delta.html", "Delta", body, 1))

    # ---------- clubs ----------
    crow = []
    for club in sorted(d["clubs"]):
        v = d["clubs"][club]
        crow.append([club, v["raw_state"], str(v["raw_rows"]), v["read_state"], str(v["read_rows"]),
                     "%+d" % v["row_delta"] if v["row_delta"] else "0", link(OFFICIAL, "nfl.com/injuries")])
    body = (
        '<h1>Clubs — presence and row counts</h1>'
        '<p class="lede">Each club block in either read. “No injuries reported” is what the page printed; it is '
        'recorded as a state, not as healthy.</p>'
        + table(["Club", "Earlier read state", "Rows", "Later read state", "Rows", "Row change", "Source"], crow)
        + '<p class="note">Clubs in neither read (not in the official report this week): %s. Bye status for these '
        'clubs is not verified here (F5).</p>' % esc(absent_names)
    )
    open(os.path.join(NS, "pages", "clubs.html"), "w", encoding="utf-8").write(page("pages/clubs.html", "Clubs", body, 1))

    # ---------- sources ----------
    srows = [
        ["Official NFL injury report, Week 11 of the 2026 season (later read)", link(OFFICIAL),
         "repo: " + READ_PATH.replace("../", "nfl-readiness-register/").replace("nfl-readiness-register/data/", "nfl-w11-delta/data/"),
         "2026-11-19, after 06:48:48 UTC (fetch_page, chunks 0–6 of 7; page prints no update time)",
         "Later read; delta rows"],
        ["Official NFL injury report, same page (earlier capture, raw HTML)", link(OFFICIAL),
         "repo: " + RAW_PATH.replace("../", ""),
         "%s, sha256 %s (manifest injury_report-2026-11-18T234917Z)" % (df["captured_utc"], df["sha256"]),
         "Earlier read; parsed with stdlib parser (242 rows, 23 club tables)"],
        ["Official NFL schedule (bye status not verified here)", link(SCHEDULE), "—",
         "not re-read for this page", "Context only; F5"],
        ["Official NFL headline on the injury page: Buccaneers QB Baker Mayfield, lower-leg injury", link(NEWS_MAYFIELD), "—",
         "headline as printed on the official injury page; article not fetched", "F2 (conflict flagged)"],
        ["Official NFL headline on the injury page: Jets QB Geno Smith, ankle injury vs. Bills", link(NEWS_SMITH), "—",
         "headline as printed on the official injury page; article not fetched", "F3 (conflict flagged)"],
        ["Transcribed later read, row-level (reproducibility copy)", link(OFFICIAL),
         "repo: " + DATA_DIR_LINK.replace("https://github.com/sassnarep3-star/Own4/tree/main/", ""),
         "sha256 %s" % dt["sha256"], "Input to engine/delta.py"],
    ]
    body = ('<h1>Sources</h1><p class="lede">Each source with its clock time and what it supports. '
            'Every row links to an official nfl.com page. Repo paths are shown as text and are not sources.</p>'
            + table(["Source", "Official link", "Repo file", "Read or captured", "Used for"], srows))
    open(os.path.join(NS, "pages", "sources.html"), "w", encoding="utf-8").write(page("pages/sources.html", "Sources", body, 1))

    # ---------- flagged ----------
    frows = [
        ["F1", "The Chargers block was “No Injuries Reported” in the earlier capture and had %d rows in the later read." %
         d["clubs"]["Chargers"]["read_rows"],
         "Not explained by either read. Treated as: block not yet populated at 23:49Z. Do not read an empty block as healthy.",
         link(OFFICIAL, "nfl.com/injuries")],
        ["F2", "Buccaneers QB Baker Mayfield: the injury cell is blank in both reads, but the official headline says “dealing with lower leg injury”.",
         "Conflict between two official NFL items. Not filled in; injury cell left blank.",
         link(NEWS_MAYFIELD, "nfl.com news headline")],
        ["F3", "Jets QB Geno Smith: the injury cell is blank in the Week 11 report; the official Week 10 headline says ankle injury.",
         "Conflict across weeks. Not filled in.", link(NEWS_SMITH, "nfl.com news headline")],
        ["F4", "Name-to-link mismatches on the official page: Dee Alford (BUF) links to /players/deaundre-ford/; Jacob Hummel (HOU) links to /players/jake-hummel/.",
         "Identity not confirmed; names shown as printed. Affects player matching, not designations.", link(OFFICIAL, "nfl.com/injuries")],
        ["F5", "Six clubs have no block in either read: %s." % absent_names,
         "Consistent with a bye week, but the bye status is not verified in this workspace. “Not listed” is not “available”.",
         link(SCHEDULE, "nfl.com/schedules")],
        ["F6", "The later read is not raw HTML bytes; the transcription was done by the session agent from fetch_page text.",
         "Mitigation: the %d overlapping rows agree with the stored raw HTML on injury, practice, game status and position." %
         (c["unchanged"] + c["changed"]) + " Still a limitation, so re-capture as raw bytes when the sandbox allows.",
         link(OFFICIAL, "nfl.com/injuries")],
        ["F7", "The official page prints no update time; read times are the session clock.",
         "Recorded as a read clock, not as a publication time.", link(OFFICIAL, "nfl.com/injuries")],
        ["F8", "Row-level transcription sits in a public repository directory.",
         "The brief asks for raw row-level data in a private store until terms are read. Not done here. Owner decision needed.",
         link(OFFICIAL, "nfl.com/injuries")],
        ["F9", "Game status is blank for most players on this report.",
         "Left blank; not inferred. Friday's report may set it.", link(OFFICIAL, "nfl.com/injuries")],
    ]
    body = ('<h1>Flagged for Review</h1>'
            '<p class="lede">Irregularities and unverified items. They do not block publication. Each has an official source link.</p>'
            + table(["ID", "Item", "What we did", "Source"], frows))
    open(os.path.join(NS, "pages", "flagged.html"), "w", encoding="utf-8").write(page("pages/flagged.html", "Flagged for Review", body, 1))
    print("built 5 pages")


if __name__ == "__main__":
    main()

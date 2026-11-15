#!/usr/bin/env python3
"""Render nfl-availability-desk: a decision-support dashboard built entirely from this namespace's data files.

Design rules enforced here (they are the brief's rules, not decoration):
  * every data row carries a source link, or it prints 'UNVERIFIED' with a flag id;
  * values that could not be confirmed are left blank and flagged, never inferred;
  * the landing page's first table is the decision-readiness register: one row per requirement,
    the gate that blocks it, and the number that would clear it;
  * nothing is fetched at build time - the pages are a pure function of the checked-in artefacts,
    which is what lets CI prove the published numbers again.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
DER = os.path.join(DATA, "derived")
PAGES = os.path.join(NS, "pages")

NAV = OrderedDict([
    ("index.html", "Decision readiness"),
    ("pages/availability.html", "Availability capture"),
    ("pages/snapshot-delta.html", "Snapshot ledger & delta"),
    ("pages/fixtures.html", "Fixtures, venues & standings"),
    ("pages/evidence.html", "Official evidence log"),
    ("pages/questions.html", "Questions to answer"),
    ("pages/suggestions.html", "Suggestions to review"),
    ("pages/governance.html", "Governance & gates"),
    ("pages/repo-review.html", "Repository review"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/sources.html", "Source register"),
])

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#15181d;--mut:#5b6472;--line:#e3e6ea;--ok:#0f7b4d;
--warn:#a56a00;--bad:#b3261e;--info:#1b5eab;--chip:#eef1f5}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",
Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--info);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#0d1117;color:#fff;padding:14px 20px}
header.top .wrap{max-width:1280px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px;
align-items:baseline;justify-content:space-between}
header.top h1{font-size:16px;margin:0;letter-spacing:.2px}
header.top .meta{color:#9aa7b6;font-size:12px}
nav.sub{background:#12171f;padding:8px 20px;position:sticky;top:0;z-index:5}
nav.sub .wrap{max-width:1280px;margin:0 auto;display:flex;flex-wrap:wrap;gap:6px}
nav.sub a{color:#c9d3df;font-size:12.5px;padding:4px 9px;border-radius:999px}
nav.sub a.on{background:#22314a;color:#fff}
main{max-width:1280px;margin:0 auto;padding:20px}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;
margin:0 0 18px;overflow:hidden}
section>.h{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;
justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
section>.h h2{font-size:15px;margin:0}section>.h .s{color:var(--mut);font-size:12.5px}
section>.b{padding:14px 16px}.lead{color:var(--mut);margin:0 0 12px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-top:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}
th{background:#f0f2f5;font-weight:600;position:sticky;top:41px;z-index:1;font-size:12px;
text-transform:uppercase;letter-spacing:.3px;color:#414a57}
tbody tr:nth-child(even){background:#fbfcfd}td.num{text-align:right;font-variant-numeric:tabular-nums}
td.blank{color:#9aa4b0;font-style:italic}.chip{display:inline-block;background:var(--chip);
border-radius:999px;padding:1px 8px;font-size:11.5px;white-space:nowrap}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.info{color:var(--info)}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi .v{font-size:22px;font-weight:650;letter-spacing:-.3px}.kpi .l{color:var(--mut);font-size:12px}
.note{background:#fff8e6;border:1px solid #f0dca0;border-radius:8px;padding:10px 12px;
font-size:13px;margin:0 0 14px}.note.blue{background:#eef4fd;border-color:#c9dcf7}
.note.red{background:#fdeeee;border-color:#f0c6c2}
ul.tight{margin:6px 0 0;padding-left:18px}ul.tight li{margin:0 0 5px}
.scroll{overflow:auto;max-height:70vh}.src{font-size:11.5px;color:var(--mut);word-break:break-all}
code{background:#f0f2f5;padding:1px 4px;border-radius:4px;font-size:12px}
footer{max-width:1280px;margin:0 auto;padding:6px 20px 34px;color:var(--mut);font-size:12px}
@media(max-width:700px){th{position:static}}
"""

OPEN = '<a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'


def esc(v) -> str:
    return html.escape("" if v is None else str(v))


def link(url: str, text: str = "") -> str:
    if not url:
        return ""
    return OPEN.format(u=esc(url), t=esc(text or url))


def chip(text: str, cls: str = "") -> str:
    return f'<span class="chip {cls}">{esc(text)}</span>'


def jload(name: str, base: str = DATA):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return json.load(fh)


def cload(name: str, base: str = DATA):
    with open(os.path.join(base, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# page frame
# --------------------------------------------------------------------------- #
def frame(active: str, title: str, h1: str, body: str, sub: str = "") -> str:
    navs = []
    base = "" if active == "index.html" else "../"
    for href, label in NAV.items():
        cls = ' class="on"' if href == active else ""
        navs.append(f'<a href="{base}{href}"{cls}>{esc(label)}</a>')
    subtitle = f'<div class="meta">{esc(sub)}</div>' if sub else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><link rel="stylesheet" href="{base}assets/readiness.css"></head>
<body>
<header class="top"><div class="wrap"><h1>NFL Line Origination &middot; Decision Readiness</h1>{subtitle}</div></header>
<nav class="sub"><div class="wrap">{''.join(navs)}</div></nav>
<main><h2 id="pageh1" style="font-size:19px;margin:2px 0 14px">{esc(h1)}</h2>
{body}</main>
<footer>Built by session <code>arena-d941f3c1-own4</code> from the artefacts in <code>nfl-availability-desk/data/</code>.
Every table row carries its source; unverifiable values are blank and flagged, never inferred.
Reproduce with <code>python3 engine/capture.py &amp;&amp; python3 engine/audit.py &amp;&amp; python3 engine/drift.py &amp;&amp; python3 engine/repo_review.py &amp;&amp; python3 engine/build_site.py &amp;&amp; python3 engine/verify_site.py</code> — no step fetches anything.
Gambling involves risk — beaware: this is a research dashboard, not betting advice; if gambling stops being fun, call the National Problem Gambling Helpline 1-800-522-4700.</footer>
</body></html>
"""


def section(title: str, body: str, sub: str = "", cls: str = "") -> str:
    head = f'<div class="h"><h2>{esc(title)}</h2>' + (f'<div class="s">{sub}</div>' if sub else "") + "</div>"
    return f'<section class="{cls}">{head}<div class="b">{body}</div></section>'


def table(cols, rows, scroll=True) -> str:
    thead = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = []
    for r in rows:
        tds = []
        for cell in r:
            if isinstance(cell, tuple):
                tds.append(cell[0])
            else:
                txt = "" if cell is None else str(cell)
                klass = ' class="blank"' if txt in ("", "—") else ""
                tds.append(f"<td{klass}>{txt if txt else '—'}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    wrap = '<div class="scroll">' if scroll else ""
    return f'{wrap}<table><thead><tr>{thead}</tr></thead><tbody>{"".join(body)}</tbody></table>{"</div>" if scroll else ""}'


def src_cell(url: str, label: str = "official page", extra: str = "") -> str:
    if not url:
        return '<span class="bad">UNVERIFIED</span>' + (f" {extra}" if extra else "")
    s = link(url, label)
    if extra:
        s += f'<div class="src">{extra}</div>'
    return s


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #
def page_index(readiness, audit, valid, st, fl) -> str:
    n_high = sum(1 for x in fl["rows"] if x["severity"] == "high")
    groups = OrderedDict()
    for r in readiness["rows"]:
        groups.setdefault(r["group"], []).append(r)
    total = len(readiness["rows"])
    counts = {}
    for r in readiness["rows"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = ["delivered", "delivered-partially", "delivered-elsewhere", "blocked", "rejected", "governance"]
    status_html = " &middot; ".join(
        f'{chip(f"{counts[k]} {k}", "ok" if k.startswith("delivered") else ("bad" if k == "blocked" else ""))}'
        for k in order if k in counts)

    kpis = [
        (str(valid["rows"]), f"availability rows captured ({valid['club_sections']} club sections)"),
        (f'{valid["designation_coverage_pct"]}%', "rows carrying an official game designation"),
        (str(st["backtest_corpus"]["games_credited_to_date"]), "games credited in the official standings"),
        (str(total), "requirements in the readiness register"),
        (str(counts.get("blocked", 0)), "requirements blocked by a named source gap"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div></div>'
                      for v, l in kpis)

    rows = []
    for r in readiness["rows"]:
        cls = {"delivered": "ok", "delivered-partially": "warn", "delivered-elsewhere": "info",
               "blocked": "bad", "rejected": "", "governance": ""}.get(r["status"], "")
        rows.append([
            f'<b>{esc(r["id"])}</b>',
            esc(r["requirement"]),
            chip(r["status"], cls),
            esc(r["gate"]),
            f'<b>{esc(r["clearing_number"])}</b>',
            src_cell(r["source"], "source", esc(r["evidence"])),
        ])
    body = (
        f'<div class="note blue"><b>What this page is for.</b> Every requirement in the brief is one row '
        f'below, with the specific gate that blocks it and the specific number that would clear it. '
        f'Nothing here is a promise of work: rows marked <i>delivered-elsewhere</i> point at a peer '
        f'namespace in this repository that already carries the artefact, and this session did not '
        f're-verify that namespace line by line. <b>Read the flags first:</b> '
        f'{link("pages/flagged.html", str(len(fl["rows"])) + " flagged irregularities")} — '
        f'{n_high} of them are marked high severity, and every blocked row below names the flag or '
        f'source it is waiting on.</div>'
        f'<div class="grid" style="margin-bottom:18px">{kpi_html}</div>'
        + section(
            "Decision-readiness register", f"{status_html}",
            table(["id", "requirement", "status", "gate that blocks it", "number that clears it", "evidence / source"], rows))
        + section("How the numbers on this page were produced", "engine/capture.py &rarr; engine/audit.py &rarr; this file",
                  "<ul class='tight'>"
                  f"<li><b>Capture validation</b> (machine-checked, <code>data/derived/capture_validation.json</code>): "
                  f"{valid['rows']} rows, {valid['club_sections']} club sections, {valid['fixtures']} fixtures, "
                  f"{valid['rows_with_injury_text']} rows carrying injury text, {valid['rows_with_non_injury_reason']} "
                  f"rows carrying a non-injury reason, verdict <b class='ok'>{valid['verdict']}</b>.</li>"
                  f"<li><b>Standings identities</b> (<code>data/derived/standings_check.json</code>): 32 clubs, "
                  f"sum PF {st['sum_pf']} = sum PA {st['sum_pa']} &rarr; <b class='ok'>{st['pf_equals_pa']}</b>; "
                  f"net-points identity {st['net_points_identity_holds']}; win-pct mismatches "
                  f"{len(st['win_pct_mismatches'])}; games played {st['games_played_derived']} "
                  f"(sum GP {st['sum_games_played']} / 2).</li>"
                  f"<li><b>Coverage</b>: {audit['rows']} rows &times; 8 required fields &times; 0 blanks in a required "
                  f"field; {len(audit['sections_with_zero_injury_labels'])} club sections without an injury "
                  f"label; {len(audit['clubs_with_no_section'])} clubs publish no section and they are exactly "
                  f"the official bye list ({esc(', '.join(st['teams_on_bye_derived']))}).</li></ul>")
        + section("The four decisions this whole project waits on", "", (
            "<ul class='tight'>"
            "<li><b>DEC-P1 — what counts as a price.</b> Until it is answered, the snapshot store, the "
            "difference column, the residual, CLV, vig decomposition and every reward stay structurally empty "
            "(<a href='pages/suggestions.html'>SUG-01</a>).</li>"
            "<li><b>Collector or manual.</b> Dated captures exist only because separate agent sessions happened "
            "to read the page on separate days; the cadence the brief assumes does not run "
            "(<a href='pages/suggestions.html'>SUG-02</a>).</li>"
            "<li><b>Game books before models.</b> 'Who actually started' is the one field that turns the "
            "availability graph into a testable claim, and its official PDF is already linked per fixture "
            "(<a href='pages/suggestions.html'>SUG-03</a>).</li>"
            "<li><b>Canonical namespace.</b> 22 NFL namespaces in one repo meet the same brief 22 different "
            "ways (<a href='pages/suggestions.html'>SUG-08</a>).</li></ul>"))
    )
    return frame("index.html", "NFL decision readiness", "Decision readiness", body,
                 f"read window {audit.get('capture_id','')} · built {readiness['built_utc']}")


def page_availability(audit, valid, snap) -> str:
    per = audit["per_team"]
    rows = []
    for t, d in per.items():
        rows.append([
            f"<b>{esc(t)}</b>", str(d["rows"]),
            str(d["out"]), str(d["questionable"]), str(d["doubtful"]),
            str(d["no_game_status"]),
            f'{d["dnp"]} / {d["lp"]} / {d["fp"]}',
            str(d["injury_labelled"]), str(d["non_injury_label"]),
            src_cell("https://www.nfl.com/injuries/", "official report",
                     "section counted from the transcribed capture; re-derived by engine/audit.py"),
        ])
    tot = {k: sum(d[k] for d in per.values()) for k in
           ("rows", "out", "questionable", "doubtful", "no_game_status", "dnp", "lp", "fp",
            "injury_labelled", "non_injury_label")}
    rows.append([("<b>total (28 sections)</b>")[:60], f"<b>{tot['rows']}</b>", f"<b>{tot['out']}</b>",
                  f"<b>{tot['questionable']}</b>", f"<b>{tot['doubtful']}</b>", f"<b>{tot['no_game_status']}</b>",
                  f"<b>{tot['dnp']} / {tot['lp']} / {tot['fp']}</b>", f"<b>{tot['injury_labelled']}</b>",
                  f"<b>{tot['non_injury_label']}</b>",
                  "<code>engine/audit.py</code> — sum of the club sections above, recomputed at "
                  "every build"])

    vocab = "".join(
        "<li>" + esc(k) + f": <b>{v}</b></li>" for k, v in sorted(audit["game_status_vocabulary"].items(),
                                                                 key=lambda kv: -kv[1]))
    pvoc = "".join("<li>" + esc(k) + f": <b>{v}</b></li>"
                   for k, v in sorted(audit["practice_status_vocabulary"].items(), key=lambda kv: -kv[1]))

    bye = ", ".join(audit["clubs_with_no_section"])

    body = (
        f'<div class="note"><b>What the official report publishes, and what it does not.</b> The five columns '
        f'above are the entire vocabulary of the source: Player, Position, Injuries, Practice Status, Game '
        f'Status. There is no depth rank, no starter/backup flag, no snap count and no roster status, so none '
        f'appears anywhere on this page. <b>{len(audit["clubs_with_no_section"])} clubs publish no section at '
        f'all</b> ({esc(bye)}) and the official schedule page\'s own '
        f'&ldquo;Teams on Bye&rdquo; block names the same four — an absent club is a bye, not a healthy roster.</div>'
        + section("Per-club availability ledger, Week 10",
                  f"{valid['club_sections']} club sections · {valid['rows']} rows",
                  table(["club", "rows", "out", "questionable", "doubtful", "no designation",
                         "DNP / LP / FP", "injury text", "non-injury reason", "source"], rows))
        + section("Game-status vocabulary as published", "", f"<ul class='tight'>{vocab}</ul>"
                  + "<div class='note' style='margin-top:12px'>The vocabulary is <b>not</b> a probability. "
                    "No percentage may attach to &lsquo;Questionable&rsquo; until designations are joined to "
                    "played/inactive outcomes across seasons (readiness R-44, R-53).</div>",
                  )
        + section("Practice-status vocabulary as published", "", f"<ul class='tight'>{pvoc}</ul>")
        + section("Non-injury reasons inside the Injuries column", "flag RF-11",
                  "<div class='note red'>The official Injuries column also carries non-injury reasons. "
                  f"This capture contains <b>{valid['rows_with_non_injury_reason']}</b> such rows: "
                  "&lsquo;Not injury related - resting player&rsquo; and &lsquo;Not injury related - personal "
                  "matter&rsquo;. Any feature that counts injury labels counts a rest day as an injury. "
                  "Rows: " + esc("; ".join(
                      f"{r['team']} {r['player']} ({r['injury']})" for r in snap if "Not injury related" in r["injury"]))
                  + "</div>")
        + section("Every row of the capture", f"{len(snap)} rows · blank cells are blank on the official page",
                  table(["club", "opp", "player", "pos", "injury", "practice", "game status", "source"],
                        [[esc(r["team"]), esc(r["opp"]), esc(r["player"]), esc(r["pos"]),
                          esc(r["injury"]) or "", esc(r["practice_status"]),
                          (f"<b>{esc(r['game_status'])}</b>" if r["game_status"] else ""),
                          src_cell("https://www.nfl.com/injuries/", "report",
                                    "player page: " + link(f"https://www.nfl.com/players/{r['player_slug']}/", r["player"]))]
                         for r in snap]))
    )
    return frame("pages/availability.html", "Availability capture", "Week 10 official availability capture", body,
                 "read 2026-11-15 · nfl.com/injuries · 8 of 8 page chunks")


def page_delta(diffs, delta, valid) -> str:
    n_subsets = sum(1 for d in diffs if d["peer_rows_are_a_strict_subset_of_this_capture"])
    n_ties = sum(1 for d in diffs if d["row_delta"] == 0)
    counts_txt = f"{valid['rows']}, " + ", ".join(str(d["peer_rows"]) for d in diffs)
    gaps = sorted({abs(d["row_delta"]) for d in diffs if d["row_delta"]})
    gap_txt = " and ".join(f"{g}-row" for g in gaps) if gaps else "no row"
    tie = next((d for d in diffs if d["row_delta"] == 0), None)
    tie_moved = (len(tie["players_in_this_capture_only"]) + len(tie["players_in_peer_only"])) if tie else None
    by_club = delta.get("game_status_changes_by_club") or {}
    by_club_txt = ", ".join(f"{t} {n}" for t, n in sorted(by_club.items(), key=lambda kv: -kv[1])) or "none"
    drows = []
    for d in diffs:
        verdict = ("identical row set" if d["row_delta"] == 0 and not d["players_in_peer_only"] else
                   ("subset of this capture (rows missing)" if d["peer_rows_are_a_strict_subset_of_this_capture"] else
                    "divergent"))
        drows.append([
            f"<code>{esc(d['peer'])}</code>", esc(d["peer_captured"] or "date not stated"),
            str(d["peer_rows"]), f'{d["row_delta"]:+d}',
            f'{d["peer_designation_rows"]} / {d["this_capture_designation_rows"]}',
            f'{d["teams_where_peer_is_a_prefix_of_this"]} / {d["teams_compared"]}',
            esc(verdict),
            (f'only in peer: {len(d["players_in_peer_only"])} · only here: {len(d["players_in_this_capture_only"])}'),
            src_cell("https://github.com/sassnarep3-star/Own4/blob/main/" + d["peer"],
                     "file in this repository", esc(d["peer_source"])),
        ])
    grows = [[f"<b>{esc(r['team'])}</b>", esc(r["player"]), esc(r["pos"]),
              esc(r["as_of_2026-11-14"]), f"<b>{esc(r['as_of_2026-11-15'])}</b>",
              src_cell("https://www.nfl.com/injuries/", "official report",
                       "both renders are repo files: nfl-marketboard 2026-11-14 and this capture 2026-11-15")]
             for r in delta["game_status_changes"]]
    prows = [[f"<b>{esc(r['team'])}</b>", esc(r["player"]), esc(r["as_of_2026-11-14"]),
              esc(r["as_of_2026-11-15"]), src_cell("https://www.nfl.com/injuries/", "official report")]
             for r in delta["practice_status_changes"]]
    irows = [[f"<b>{esc(r['team'])}</b>", esc(r["player"]), esc(r["as_of_2026-11-14"]),
              esc(r["as_of_2026-11-15"]), src_cell("https://www.nfl.com/injuries/", "official report")]
             for r in delta["injury_label_changes"]]

    body = (
        f'<div class="note blue"><b>Why this page exists.</b> The brief asks for the delta, never the level. '
        f'{len(diffs) + 1} dated captures of one official page sit in this repository, and their row counts '
        f'are {counts_txt}. The same page read on different days produces different datasets: '
        f'{n_subsets} of the {len(diffs)} comparisons are strict subsets of the fullest and {n_ties} ties it '
        f'exactly. Below is the arithmetic that makes that visible, and the one place where two complete '
        f'captures can be compared row by row.</div>'
        + section("Point-in-time ledger: this capture against every stored capture",
                  "computed by engine/audit.py · club codes normalised (ARI&rarr;AZ, LA&rarr;LAR) and no player data touched",
                  table(["stored capture", "captured", "rows", "&Delta; rows vs 2026-11-15",
                         "designation rows (peer / this)", "clubs where peer is a prefix of this",
                         "verdict", "row-set difference", "source"], drows))
        + section(f"Designation delta, 2026-11-14 &rarr; 2026-11-15", f'{len(grows)} rows changed game status',
                  "<p class='lead'>" + esc(delta["reading"]) + "</p>"
                  + table(["club", "player", "pos", "14 Nov", "15 Nov", "source"], grows))
        + section(f"Practice-status delta, 2026-11-14 &rarr; 2026-11-15", f"{len(prows)} rows",
                  table(["club", "player", "14 Nov", "15 Nov", "source"], prows))
        + section(f"Injury-label delta, 2026-11-14 &rarr; 2026-11-15", f"{len(irows)} rows gained or lost a label",
                  table(["club", "player", "14 Nov", "15 Nov", "source"], irows))
        + section("What a delta changes in practice", "",
                  "<ul class='tight'>"
                  f"<li>The {len(grows)} changed designations sit in {len(by_club)} clubs "
                  f"({by_club_txt}) — the two Monday-night fixtures. A Sunday capture of a Monday game is "
                  f"not late: it is a different fact.</li>"
                  f"<li>Designation coverage in this capture: <b>{valid['designation_rows']}/{valid['rows']} "
                  f"({valid['designation_coverage_pct']}%)</b>. Coverage is a property of the day, so it is stored "
                  "with the read window, never as a table-wide statistic.</li>"
                  + (f"<li>{tie_moved} rows were added or removed between the two renders that tie, so the "
                   f"difference between those two is a clock difference, not a coverage failure — while the "
                   f"{gap_txt} gaps against the older captures <b>are</b> coverage failures. That is the "
                   f"difference between a good capture and a complete one.</li>"
                   if tie else "<li>no two captures tie on row count.</li>") + "</ul>"))
    return frame("pages/snapshot-delta.html", "Snapshot ledger & delta", "Snapshot ledger &amp; delta", body,
                 "the level is a row; the delta is the signal")


def page_fixtures(fixtures, st, audit) -> str:
    with_venue = [f for f in fixtures if f["venue_published"]]
    n_venue = len(with_venue)
    venues_txt = "; ".join(f"{f['away']}@{f['home']}: {f['venue_published']}" for f in with_venue)
    rows = []
    for f in fixtures:
        state = f["schedule_state_at_capture"]
        cls = "ok" if state == "Final" else ("warn" if state.startswith("In progress") else "info")
        venue = f["venue_published"]
        rows.append([
            f"<b>{esc(f['game_no'])}</b>", esc(f["day"]), esc(f["date_local"]), esc(f["slot_et"]),
            esc(f["broadcast"]), esc(f["away"]), esc(f["home"]),
            (esc(venue) if venue else "<span class='bad'>not published on the pages read</span>"),
            chip(state, cls), esc(f["score_at_capture"] or "—"), esc(f["injury_report_records"]),
            src_cell(f["game_centre_url"], "game centre",
                     "schedule card: " + link("https://www.nfl.com/schedules/2026/by-week/week-10", "Week 10 schedule")),
        ])
    srows = []
    for r in jload("standings_2026-11-15.json")["rows"]:
        gp = r["W"] + r["L"] + r["T"]
        srows.append([f"<b>{esc(r['club'])}</b>", str(r["W"]), str(r["L"]), str(r["T"]),
                      f"{r['pct']:.3f}", str(r["PF"]), str(r["PA"]), str(r["net_pts"]), str(gp),
                      esc(r["streak"]),
                      src_cell("https://www.nfl.com/standings/league/2026/REG", "official standings",
                               "GP is derived here as W+L+T; the page prints no GP column")])
    bc = st["backtest_corpus"]
    corpus_rows = [
        ["Games credited in the live standings", f'<b>{bc["games_credited_to_date"]}</b>',
         "sum(W+L+T) over 32 clubs / 2", "<a href=\"https://www.nfl.com/standings/league/2026/REG\">official standings</a> + <code>engine/audit.py</code>"],
        ["Week 10 games credited at read time", f'<b>{bc["week10_games_credited_at_read"]}</b>',
         f'{bc["week10_games_final_at_read"]} final + {st["week10_in_progress_at_read"]} in progress', "<code>engine/audit.py</code>"],
        ["Games through Week 9", f'<b>{bc["games_through_week9"]}</b>',
         "credited-to-date minus Week 10 credited", "<code>engine/audit.py</code>"],
        ["Week 10 slate size", f'<b>{bc["week10_slate_size"]}</b>',
         "14 fixtures (Thu 1, Sun 12, Mon 1)", "<a href=\"https://www.nfl.com/schedules/2026/by-week/week-10\">official Week 10 schedule page</a>"],
        ["Corpus when Week 10 completes", f'<b>{bc["games_after_week10_completes"]}</b>',
         "through-Week-9 + slate", "<code>engine/audit.py</code>"],
        ["Figure quoted in the brief", "<span class='bad'>136</span>",
         "not reproducible from any repo file or from the official standings", "<a href=\"flagged.html\">flag RF-01</a>"],
    ]
    body = (
        f'<div class="note"><b>Venues.</b> The official schedule card prints no venue text; it exposes venue '
        f"only through the fixture's own ticket/hotel locator. {n_venue} of {len(fixtures)} fixtures have a "
        f"venue recorded here ({esc(venues_txt)}). The other {len(fixtures) - n_venue} are blank and listed, not "
        f"guessed — the gate is {len(fixtures)} of {len(fixtures)} game centres opened (readiness R-23).</div>"
        + section("Week 10 fixtures, as the official page states them", "14 fixtures · state shown is the state at read time",
                  table(["#", "day", "date", "slot ET", "broadcast", "away", "home", "venue", "state", "score", "report records", "source"], rows))
        + section("Fixture-context fields built only from published schedule facts", "",
                  "<ul class='tight'>"
                  "<li><b>Slot &amp; day</b> — from the schedule page's own headers (Thursday / Sunday 9:30 / "
                  "Sunday 1:00 / 4:05 / 4:25 / 8:20 / Monday). Travel and rest consequences are stated as a "
                  "question, not scored, because rest-days need the prior week's dates per club.</li>"
                  "<li><b>Bye block</b> — read from the same page: CHI 7-2, DEN 7-2, PHI 2-7, TB 3-6. This is "
                  f"the only reason {len(audit['clubs_with_no_section'])} clubs are absent from the report.</li>"
                  "<li><b>International marker</b> — the schedule page labels NE@DET as an International Game "
                  "at Munich; the game centre prints Location MUNICH and Stadium FC BAYERN MUNICH STADIUM.</li>"
                  "<li><b>Flexible-scheduling notice</b> — the page's own footer text on Week 16/17/18 "
                  "flexibility, with the legal page linked: "
                  + link("https://www.nfl.com/legal/flexible-scheduling-procedures", "flexible scheduling procedures")
                  + ".</li>"
                  "<li><b>Weather</b> — the only official weather string seen on the pages read is the Monday "
                  "card's &lsquo;Weather Clearnight&rsquo;. No roof/surface register and no NWS join exists, so "
                  "readiness R-58 stays blocked (it would otherwise be invented).</li></ul>")
        + section("League standings, transcribed, with the integrity checks that make them usable",
                  "32 clubs · derived columns labelled as derived",
                  table(["club", "W", "L", "T", "PCT", "PF", "PA", "net", "GP (derived)", "streak", "source"], srows, scroll=False)
                  + f"<div class='note' style='margin-top:12px'><b>Identities:</b> sum PF <b>{st['sum_pf']}</b> = sum PA "
                    f"<b>{st['sum_pa']}</b> ({'PASS' if st['pf_equals_pa'] else 'FAIL'}); net-points identity "
                    f"{'holds' if st['net_points_identity_holds'] else 'BROKEN'} for all 32; win-pct recomputation "
                    f"mismatches: <b>{len(st['win_pct_mismatches'])}</b>. A feed where points-for and points-against "
                    f"do not balance cannot be used to grade anything.</div>")
        + section("Backtest corpus size (the 136-game question)", "readiness R-19 · flag RF-01",
                  table(["quantity", "value", "how derived", "where"], corpus_rows, scroll=False)
                  + "<div class='note red' style='margin-top:12px'>The brief instructs: &lsquo;turn the 136-game "
                    "log into the pre-registered backtest corpus&rsquo;. The number 136 does not exist in any file "
                    "at the base commit and does not satisfy the official standings arithmetic. Both are published "
                    "here; the corpus is registered by its <b>definition</b> (see PREREG-001 §2), which is stable "
                    "even while the count is disputed.</div>")
    )
    return frame("pages/fixtures.html", "Fixtures, venues & standings", "Fixtures, venues &amp; standings", body,
                 "week 10 of 2026 · read 2026-11-15")


def page_evidence(ev, reads, man) -> str:
    rows = []
    for r in ev["rows"]:
        v = r["verified"]
        cls = "ok" if v.startswith("roundup body") else ("warn" if "not opened" in v or "not" in v else "info")
        rows.append([f"<b>{esc(r['id'])}</b>", esc(r["as_of"]), esc(r["club"]), chip(r["kind"]),
                     esc(r["text"]), chip(v, cls), src_cell(r["url"], "official source")])
    rrows = [[str(r["read_no"]), src_cell(r["url"], "url"), esc(r["chunks_read"]),
              esc(r.get("page_title_as_published", "")), esc(r["used_for"][:300])]
             for r in reads["reads"]]
    body = (
        f'<div class="note blue"><b>Provenance grading.</b> Two grades appear in this table. '
        f'&lsquo;roundup body read this session&rsquo; means the sentence was read in the article body. '
        f'&lsquo;headline + URL read in the official news module&rsquo; means only the headline and its link were '
        f'read (on the injury-report page itself) and the article was not opened — those rows are evidence of '
        f'what the league published and when, not of the full text. That distinction is on the row, not in a '
        f'footnote. IR and transaction facts are <b>not</b> available as a structured list on the pages read '
        f'(readiness R-64).</div>'
        + section(f"Dated official text used as evidence ({len(ev['rows'])} rows)", ev["title"],
                  table(["id", "as of", "club", "kind", "what the source says", "provenance grade", "source"], rows))
        + section("Official pages read in this session", "read window "
                  + esc(reads["read_window_utc"]["start"]) + " → " + esc(reads["read_window_utc"]["end"]) + " UTC",
                  table(["#", "page", "chunks read", "title as published", "used for"], rrows, scroll=False)
                  + "<div class='note' style='margin-top:12px'>" + esc(reads["read_window_utc"]["note"]) + "</div>"
                  + "<div class='note red' style='margin-top:12px'><b>Immutability limitation.</b> "
                    + esc(man["immutability_limitation"]) + "</div>")
    )
    return frame("pages/evidence.html", "Official evidence log", "Official evidence log", body,
                 "transaction, IR and starter announcements with their dates")


def page_questions(q) -> str:
    rows = []
    for r in q["rows"]:
        ans = r["answer"]
        rows.append([f"<b>{esc(r['id'])}</b>", chip(r["blocks"], "bad" if r["blocks"] == "blocking" else "info"),
                      f"<b>{esc(r['question'])}</b>", esc(r["know"]), esc(r["dont_know"]),
                      (esc(ans) if ans else "<span class='bad'>UNANSWERED</span>"),
                      esc(r["discovery"]), esc(r["asked_by"]),
                      src_cell(r.get("source", ""), "source")])
    n_blocking = sum(1 for r in q["rows"] if r["blocks"] == "blocking")
    n_ans = sum(1 for r in q["rows"] if r["answer"])
    body = (
        f'<div class="note"><b>{len(q["rows"])} questions, {n_blocking} blocking, {n_ans} with a partial or '
        f'full answer from what was read this session.</b> An answer appears only when a specific official page '
        f'settled it; where the answer is &lsquo;partially resolved&rsquo; the row says exactly which part. '
        f'&lsquo;UNANSWERED&rsquo; rows are the queue: they are the reason the blocked requirements in the '
        f'register stay blocked.</div>'
        + section("Questions, information and answers", "one row per question",
                  table(["id", "blocks", "question", "what we know (sourced)", "what we do not know",
                         "answer", "how to discover it", "which requirements", "source"], rows))
    )
    return frame("pages/questions.html", "Questions to answer", "Questions, information and answers", body,
                 f"{n_ans} of {len(q['rows'])} answered from official reads")


def page_suggestions(s) -> str:
    rows = []
    for r in s["rows"]:
        opts = "<ul class='tight'>" + "".join(
            f"<li><b>{esc(o['id'])}</b> — {esc(o['text'])}</li>" for o in r["options"]) + "</ul>"
        rows.append([f"<b>{esc(r['id'])}</b>", chip(r["priority"], {"P1": "bad", "P2": "warn"}.get(r["priority"], "")),
                      f"<b>{esc(r['title'])}</b>", esc(r["why"]), opts, esc(r["cost"]),
                      esc(r["unblocks"]), (esc(r["verdict"]) if r["verdict"] else
                                           "<span class='bad'>blank — reviewer decision required</span>")])
    body = (
        f'<div class="note blue"><b>Nothing on this page is implemented.</b> Each row is a proposal with '
        f'options, what each costs, and what it unblocks. A verdict is written by the reviewer into '
        f'<code>data/suggestions.json</code>; only then does a session build it. {len(s["rows"])} suggestions, '
        f'{sum(1 for r in s["rows"] if not r["verdict"])} awaiting a verdict.</div>'
        + section("Suggestions for review", s["workflow"],
                  table(["id", "priority", "suggestion", "why it matters", "options", "cost", "unblocks", "verdict"], rows))
    )
    return frame("pages/suggestions.html", "Suggestions to review", "Suggestions — review before implementing", body,
                 "a proposal register, not a work log")


def render_value(v) -> str:
    """Readably render a nested rule value without dumping raw JSON on the page."""
    if isinstance(v, dict):
        items = "".join(f"<li><b>{esc(k)}</b> — {render_value(x)}</li>" for k, x in v.items())
        return f"<ul class='tight'>{items}</ul>"
    if isinstance(v, list):
        return ("<ul class='tight'>" + "".join(f"<li>{render_value(x)}</li>" for x in v) + "</ul>")
    if isinstance(v, bool):
        return "<b class='ok'>yes</b>" if v else "<b class='bad'>no</b>"
    if v in ("", None):
        return "<span class='blank'>—</span>"
    return esc(v)


def page_governance(g, valid, st) -> str:
    def kv_rows(d):
        return [[f"<b>{esc(k)}</b>", render_value(v)] for k, v in d.items()]

    body = (
        '<div class="note"><b>This is the part of the project that does not need any missing data.</b> '
        'Gates, prohibitions and publication rules are written before results exist, so the record shows the '
        'rules were fixed in advance and not adjusted afterwards.</div>'
        + section("Rules that bind every strategy", "", table(["rule", "as frozen"], kv_rows({
            "leaderboard_rule": g["leaderboard_rule"], "divisions": g["divisions"],
            "joint_evidence_gate": g["joint_evidence_gate"], "control_baselines": g["control_baselines"],
            "price_data_policy": g["price_data_policy"], "depth_rule": g["depth_rule"],
            "correlation_policy": g["correlation_policy"], "splits": g["splits"],
            "publication_contract": g["publication_contract"]}), scroll=False))
        + section("Demotion gate (live &rarr; paper)", g["demotion_gate"]["current_evaluation"],
                  "<ol class='tight'>" + "".join(f"<li>{esc(x)}</li>" for x in
                                                 [g["demotion_gate"]["rule"], g["demotion_gate"]["on_demotion"]]) + "</ol>")
        + section("Ablation protocol, frozen and unrun", f'{g["ablation_spec"]["current_weeks_available"]} of '
                  f'{g["ablation_spec"]["min_weeks"]} required weeks available',
                  table(["element", "specification"], kv_rows(g["ablation_spec"]), scroll=False)
                  + "<div class='note red' style='margin-top:12px'>Not executed. The brief's own rule — test the "
                    "same model with and without the personnel features and report the difference with uncertainty "
                    "— needs dated availability history that does not exist yet; the alternative is a fixed points "
                    "penalty, which the brief forbids. Freezing the protocol now is what stops it being designed "
                    "around a result.</div>")
        + section("Removal-of-luck panel", "2 of 4 components computable from official data today",
                  "<b>Live</b><ul class='tight'>" + "".join(
                      f"<li><b>{esc(c['name'])}</b> — {esc(c['input'])}</li>" for c in
                      g["removal_of_luck_panel"]["components_live"]) + "</ul>"
                  + "<b>Blocked</b><ul class='tight'>" + "".join(
                      f"<li><b>{esc(c['name'])}</b> — {esc(c['blocked_by'])}</li>" for c in
                      g["removal_of_luck_panel"]["components_blocked"]) + "</ul>")
        + section("Pre-registration", "the commit hash is the registration",
                  "<ul class='tight'>" + "".join(
                      f"<li><b>{esc(r['id'])}</b> — <code>{esc(r['file'])}</code> — {esc(r['scope'])} — "
                      f"status: {esc(r['status'])}</li>" for r in g["preregistration"]["registered"]) + "</ul>"
                  + "<div class='note' style='margin-top:12px'>" + esc(g["preregistration"]["rule"])
                  + " The hash itself is recorded in <code>data/prereg.json</code> and re-checked against git "
                    "history by <code>engine/preregister.py --check</code>, which fails the build when a frozen "
                    "rule has been edited after its registration commit.</div>")
        + section("Data layer and cadence", "", table(["key", "value"], kv_rows({
            "data_layer": g["data_layer"], "capture_cadence": g["capture_cadence"]}), scroll=False))
    )
    return frame("pages/governance.html", "Governance & gates", "Governance, gates and pre-registration", body,
                 "rules fixed before results")


def page_repo_review(review, audit, valid, st, ev, diffs) -> str:
    rows = []
    for e in review["entries"]:
        rows.append([f"<code>{esc(e['path'])}</code>", chip(e["family"]),
                     esc(e["index_h1"] or e["index_title"] or "(no index title)"),
                     str(e["html_pages"]), str(e["data_files"]), str(e["python"]), str(e["rows_on_index"]),
                     chip("README" if e["has_readme"] else "no README"),
                     chip("exec summary" if e["has_exec_summary"] else "—"),
                     src_cell("", "in this repository", f"{ROOT}/{e['path']}")])
    body = (
        f'<div class="note"><b>How to read this table.</b> Counts are from a filesystem walk '
        f'(<code>engine/repo_review.py</code>); the title column is the namespace\'s own <code>&lt;h1&gt;</code>. '
        f'Rows on a namespace\'s index page are counted, not verified. This session did <b>not</b> re-check other '
        f'namespaces\' figures — where this site cites a peer number it says &lsquo;peer:&rsquo; and names the '
        f'file, so a reviewer can open it. The repo-level finding is the shape of the last column group: '
        f'{review["namespaces"]} namespaces, one brief.</div>'
        + section(f"Namespace inventory ({review['namespaces']} directories)",
                  "generated from the checked-out tree at build time",
                  table(["path", "family", "index h1 / title", "html pages", "data files", "python files",
                         "rows on index", "docs", "summary", "where"], rows))
        + section("What the walk shows", "computed, not asserted",
                  "<ul class='tight'>" + "".join(f"<li>{esc(o)}</li>" for o in review["observations"]) + "</ul>")
        + section("What this session verified independently", "",
                  "<ul class='tight'>"
                  f"<li><b>Availability capture</b>: {valid['rows']} rows / {valid['club_sections']} club "
                  f"sections and {valid['designation_rows']} designations, machine-validated "
                  f"(<code>data/derived/capture_validation.json</code>, verdict {esc(valid_verdict(audit))}).</li>"
                  f"<li><b>Cross-capture reconciliation</b> of {len(diffs) + 1} dated renders of the same "
                  f"official page: {sum(1 for d in diffs if d['row_delta'] == 0)} tie the row count exactly, "
                  f"{sum(1 for d in diffs if d['peer_rows_are_a_strict_subset_of_this_capture'])} are strict "
                  f"subsets, and {sum(1 for d in diffs if d['players_in_peer_only'])} rows exist in a peer but "
                  f"not here (0 means this capture is a superset of all of them).</li>"
                  f"<li><b>Standings identities</b>: sum PF = sum PA across {st['clubs']} clubs; "
                  f"{len(st['win_pct_mismatches'])} win-pct recomputation mismatches; the backtest corpus "
                  f"{st['backtest_corpus']['games_credited_to_date']} credited / "
                  f"{st['backtest_corpus']['games_through_week9']} through Week 9 / "
                  f"{st['backtest_corpus']['games_after_week10_completes']} when Week 10 completes.</li>"
                  f"<li><b>{len(ev['rows'])} dated official evidence rows</b> with 2 hard contradictions caught "
                  "(a traded player still on his old club's report; a blank injury cell against a named-IR headline).</li>"
                  f"<li><b>Record-field behaviour</b>: the bracketed W-L on the report is a live join "
                  f"({st['report_record_vs_live_standings']['matching']}/{st['report_record_vs_live_standings']['clubs_compared']} "
                  f"clubs equal the live standings at read time), so it may not be stored as an attribute of the "
                  f"snapshot.</li>"
                  "</ul>"))
    return frame("pages/repo-review.html", "Repository review", "Repository review", body,
                 "what exists, what is duplicated, what is missing")


def valid_verdict(audit):
    p = os.path.join(DER, "capture_validation.json")
    if os.path.exists(p):
        return jload("capture_validation.json", DER)["verdict"]
    return "not run"


def page_flagged(fl) -> str:
    rows = []
    for r in fl["rows"]:
        rows.append([f"<b>{esc(r['id'])}</b>", chip(r["kind"], "bad" if r["kind"] == "conflict" else ""),
                     chip(r["severity"], {"high": "bad", "medium": "warn"}.get(r["severity"], "")),
                     esc(r["finding"]), esc(r["measured"]), esc(r["action"]),
                     src_cell(r["source_url"], "official source")])
    counts = {}
    for r in fl["rows"]:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    body = (
        '<div class="note red"><b>None of these block publication.</b> They block <i>decisions</i> — each row '
        'names the artefact or the source that would resolve it, and the register rows they hold blocked. Four '
        'flags (RF-01, RF-02, RF-04, RF-16) are the reason five requirement families cannot be delivered from '
        'official data at all.</div>'
        + section(f"Flagged for review ({len(fl['rows'])} items · "
                  + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) + ")",
                  "status: needs review — published, not resolved",
                  table(["id", "kind", "severity", "finding", "what was measured", "what would resolve it", "source"], rows))
    )
    return frame("pages/flagged.html", "Flagged for review", "Flagged for review", body, "irregularities, with sources")


def page_exec(readiness, valid, st, fl, audit, diffs, review) -> str:
    counts = {}
    for r in readiness["rows"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    rows = [[f"<b>{esc(k)}</b>", str(v), esc({"delivered": "done and checkable in this namespace",
             "delivered-partially": "structure and real data published; one stated part impossible from official sources",
             "delivered-elsewhere": "another namespace in this repo carries it; this session located, did not re-verify",
             "blocked": "cannot be built honestly until a named source exists",
             "rejected": "the brief itself rejects it; recorded so it is not re-proposed"}.get(k, ""))]
            for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    bc = st["backtest_corpus"]
    n_subsets = sum(1 for d in diffs if d["peer_rows_are_a_strict_subset_of_this_capture"])
    n_block = sum(1 for r in readiness["rows"] if r["status"] == "blocked")
    n_partial = sum(1 for r in readiness["rows"] if r["status"] == "delivered-partially")
    n_elsewhere = sum(1 for r in readiness["rows"] if r["status"] == "delivered-elsewhere")
    n_delivered = sum(1 for r in readiness["rows"] if r["status"] == "delivered")
    body = (
        f'<div class="note blue"><b>{n_delivered} delivered · {n_partial} partial · '
        f'{n_elsewhere} held by a sibling workspace · {n_block} blocked · '
        f'{len(readiness["rows"])} requirements.</b> The data foundation the brief asks for now exists for '
        'availability and is still missing for prices. Everything else — signals, leaderboards, rewards — is '
        'one decision (what counts as a price) and one pipeline (a scheduled capture) away from being real, '
        'and nothing else. No strategy on this site earns a reward today, and that is the correct result of '
        'the gates, not a failure of them.</div>'
        + section(f"Requirement status counts ({len(counts)} distinct statuses)",
                  f"{len(readiness['rows'])} requirements",
                  table(["status", "rows", "meaning"], rows, scroll=False))
        + section("The five findings that change how the project should be run", "",
                  "<ol class='tight'>"
                  f"<li><b>The Week 10 report is {valid['rows']} rows across {valid['club_sections']} clubs, "
                  f"not the 254 or 279 the brief quotes.</b> {len(diffs) + 1} dated captures of the same official "
                  f"page sit in this repository and disagree ({', '.join(str(d['peer_rows']) for d in diffs)}, "
                  f"plus this capture at {valid['rows']}). {n_subsets} are strict subsets: the failure mode here "
                  f"is coverage, not accuracy. "
                  f"Designation coverage is {valid['designation_rows']}/{valid['rows']} rows "
                  f"({valid['designation_coverage_pct']}%).</li>"
                  f"<li><b>{len(audit['sections_with_zero_injury_labels'])} clubs publish a section with no "
                  f"injury label</b> — the brief's 'four no-injury sections' and 'Seattle and Cincinnati "
                  f"injury-free' statements do not reproduce; the {len(audit['clubs_with_no_section'])} missing "
                  f"clubs are the official bye block ({', '.join(st['teams_on_bye_derived'])}), reconciled by "
                  f"the build.</li>"
                  "<li><b>The three Lions designations (Joseph, Mays, Reed) are published as Out</b>, with the "
                  "injury names and DNP practice status — the fix the brief asked for is already in the live data, "
                  "and this capture proves it row by row.</li>"
                  "<li><b>Two hard official contradictions, both decision-grade:</b> a traded player (Henley) is "
                  "still on his former club's report five days after the trade was announced; and Nacua's report "
                  "row leaves the injury cell blank while dated text says IR with three named injuries. The report "
                  "cannot be trusted as durable or as a severity source without a transaction join.</li>"
                  f"<li><b>The corpus number in the brief does not reproduce, and the right number is "
                  f"derivable:</b> {bc['games_credited_to_date']} games credited in the official standings now, "
                  f"{bc['games_through_week9']} through Week 9, {bc['games_after_week10_completes']} when Week 10 "
                  f"finishes; "
                  f"the standings balance exactly (sum PF {st['sum_pf']} = sum PA {st['sum_pa']}), which is what "
                  f"makes a results feed gradeable at all.</li></ol>")
        + section("What is deliberately not on this site, and why", "",
                  "<ul class='tight'>"
                  "<li><b>No price, no residual, no ROI, no CLV, no rewards paid.</b> Not a gap in the effort — "
                  f"the league publishes none, and {review['nfl_namespaces']} sibling workspaces of blanks "
                  f"prove it. DEC-P1 is the owner's to make.</li>"
                  "<li><b>No starter/backup rank and no snap counts.</b> The report publishes neither; the brief "
                  "forbids inferring them from jersey order, salary or an image read by eye.</li>"
                  "<li><b>No win-rate or ROI leaderboard.</b> Rankings require a proper score with an interval and "
                  "a sample floor of n ≥ 300, so the board is empty by rule.</li>"
                  "<li><b>No ablation result.</b> The with/without-personnel-features comparison is specified and "
                  "frozen, but one dated capture cannot support it.</li>"
                  "<li><b>No 136-game claim.</b> The count is published as measured, with the discrepancy named.</li>"
                  "</ul>")
        + section("If a reviewer does three things", "",
                  "<ol class='tight'>"
                  "<li><b>Answer DEC-P1</b> (price policy, SUG-01) — it decides six blocked requirement rows and "
                  "is the only blocker for the whole market side of the project.</li>"
                  "<li><b>Approve the scheduled collector</b> (SUG-02 A) — the code half is done (capture + drift "
                  "alarm); the schedule half is one workflow, and it converts every single-week limitation into a "
                  "series: deltas, ablations, designation reliability, point-in-time replay.</li>"
                  "<li><b>Approve the game-book parser</b> (SUG-03 A) — one official PDF per fixture already "
                  "exists and is linked here; parsing it is what makes 'who actually started' a dataset instead "
                  "of a suspicion.</li></ol>"
                  f"<div class='note' style='margin-top:12px'>Full requirement-by-requirement detail is on the "
                  f"<a href='../index.html'>landing page</a>; the {len(fl['rows'])} irregularities with their sources "
                  f"are on <a href='flagged.html'>Flagged for review</a>.</div>")
    )
    return frame("pages/executive-summary.html", "Executive summary", "Executive summary", body,
                  "the four things that actually move the project")


def page_sources(sources) -> str:
    rows = [[src_cell(s["url"], "open"), f"<b>{esc(s['publisher'])}</b>", esc(s["kind"]),
             chip(s["official"], "ok" if s["official"] == "official" else "warn"),
             esc(s["used_for"]), esc(s.get("status", ""))] for s in sources["rows"]]
    body = (
        '<div class="note"><b>Every link a reviewer can check by hand.</b> The pages marked '
        '<i>official</i> are nfl.com or the league\'s own asset host; everything else is labelled. '
        'No third-party source was used for a published value in this namespace.</div>'
        + section("Source register", "one row per source read or cited",
                  table(["source", "publisher", "kind", "grade", "used for", "state"], rows, scroll=False))
    )
    return frame("pages/sources.html", "Source register", "Source register", body, "manual review links")


# --------------------------------------------------------------------------- #
def main() -> int:
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(os.path.join(NS, "assets"), exist_ok=True)
    with open(os.path.join(NS, "assets", "readiness.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS.strip() + "\n")

    snap = cload("availability_snapshot_2026-11-15.csv")
    fixtures = cload("fixtures_week10.csv")
    readiness = jload("readiness.json")
    audit = jload("capture_audit.json", DER)
    audit["capture_id"] = jload("capture_manifest.json")["capture_id"]
    valid = jload("capture_validation.json", DER)
    st = jload("standings_check.json", DER)
    diffs = jload("capture_diffs.json", DER)["diffs"]
    delta = jload("designation_delta.json", DER)
    ev = jload("evidence.json")
    reads = jload("official_reads.json")
    man = jload("capture_manifest.json")
    q = jload("questions.json")
    s = jload("suggestions.json")
    g = jload("governance.json")
    fl = jload("flags.json")
    review = jload("repo_review.json", DER)
    sources = jload("sources.json")

    write("index.html", page_index(readiness, audit, valid, st, fl))
    write(os.path.join("pages", "availability.html"), page_availability(audit, valid, snap))
    write(os.path.join("pages", "snapshot-delta.html"), page_delta(diffs, delta, valid))
    write(os.path.join("pages", "fixtures.html"), page_fixtures(fixtures, st, audit))
    write(os.path.join("pages", "evidence.html"), page_evidence(ev, reads, man))
    write(os.path.join("pages", "questions.html"), page_questions(q))
    write(os.path.join("pages", "suggestions.html"), page_suggestions(s))
    write(os.path.join("pages", "governance.html"), page_governance(g, valid, st))
    write(os.path.join("pages", "repo-review.html"), page_repo_review(review, audit, valid, st, ev, diffs))
    write(os.path.join("pages", "flagged.html"), page_flagged(fl))
    write(os.path.join("pages", "executive-summary.html"),
          page_exec(readiness, valid, st, fl, audit, diffs, review))
    write(os.path.join("pages", "sources.html"), page_sources(sources))

    # status_totals on the register, computed rather than typed
    counts = {}
    for r in readiness["rows"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"pages written: {len(NAV)} · register rows: {len(readiness['rows'])} · "
          f"statuses: {counts} · capture rows: {len(snap)}")
    return 0


def write(rel: str, doc: str) -> None:
    path = os.path.join(NS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc.strip() + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

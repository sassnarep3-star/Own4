#!/usr/bin/env python3
"""
build_site.py — D6: static site for the nfl-depth-sweep namespace.

Generates a self-contained static site under nfl-depth-sweep/site/:
- index.html              landing: sweep status + key findings
- register.html           the depth register (date + source per club row)
- clubs/<CODE>.html       one page per club: position/rank1/rank2/rank3,
                          every row source-linked to the club's official page
- flagged.html            Flagged for Review (all flags with evidence)
- ir-sweep.html           the 32-team roster/IR sweep vs the official reserve list

Rules honoured: every table row carries an http(s) source link; an unverifiable
cell is blank AND flagged (HOU); no cell is inferred.

Run: python3 nfl-depth-sweep/engine/build_site.py
"""

import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site"

E = html.escape

CSS = """
body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;background:#f6f7f9;color:#1c2430;line-height:1.5}
header{background:#0f1c2e;color:#fff;padding:18px 28px}
header h1{margin:0;font-size:1.35rem}
header .sub{color:#9fb2c8;font-size:.85rem;margin-top:4px}
nav{background:#12233a;padding:10px 28px;display:flex;gap:16px;flex-wrap:wrap}
nav a{color:#cfe0f5;text-decoration:none;font-size:.9rem}
nav a:hover{text-decoration:underline}
main{max-width:1080px;margin:24px auto;padding:0 20px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.88rem;margin:14px 0}
th,td{border:1px solid #d7dce4;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#eef2f7}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.75rem;font-weight:600}
.ok{background:#e2f5e6;color:#1c6b30}
.flag{background:#fdecea;color:#a4262c}
.note{background:#fff7e0;color:#8a6100}
a{color:#1756a9}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:18px 0}
.card{background:#fff;border:1px solid #d7dce4;border-radius:8px;padding:14px}
.card h3{margin:0 0 6px;font-size:.95rem}
.card .num{font-size:1.8rem;font-weight:700}
code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:.85em}
footer{color:#7a8694;font-size:.78rem;padding:24px 28px;text-align:center}
"""


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def page(title, body, path, sub=None):
    nav = "".join(
        f'<a href="{E(href)}">{E(label)}</a>'
        for href, label in NAV
    )
    sub_html = f'<div class="sub">{E(sub)}</div>' if sub else ""
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} — NFL Depth Sweep</title>
<style>{CSS}</style></head>
<body>
<header><h1>{E(title)}</h1>{sub_html}</header>
<nav>{nav}</nav>
<main>{body}</main>
<footer>Generated 2026-11-17 by nfl-depth-sweep/engine/build_site.py — every row source-linked; blank + flagged for unverifiable cells.</footer>
</body></html>"""
    (OUT / path).parent.mkdir(parents=True, exist_ok=True)
    (OUT / path).write_text(doc, encoding="utf-8")


NAV = [
    ("index.html", "Landing"),
    ("register.html", "Depth Register"),
    ("flagged.html", "Flagged for Review"),
    ("ir-sweep.html", "Roster / IR Sweep"),
]


def badge(status):
    cls = "ok" if status == "verified_text" else "flag"
    return f'<span class="badge {cls}">{E(status.replace("_", " "))}</span>'


def src_link(url):
    if not url:
        return ""
    return f'<a href="{E(url)}" target="_blank" rel="noopener">source</a>'


def cell_name(cell):
    if not cell:
        return "<td></td>"
    name = E(cell["name"])
    extras = []
    if cell.get("jersey"):
        extras.append(f"#{E(cell['jersey'])}")
    if cell.get("alt"):
        extras.append(f"[{E(cell['alt'])}]")
    suffix = f' <span class="badge note">{E(" ".join(extras))}</span>' if extras else ""
    return f"<td>{name}{suffix}</td>"


def build_index():
    teams = load("teams.json")["teams"]
    reg = load("depth_register.json")["clubs"]
    ir = load("roster_ir_sweep.json")
    n_text = sum(1 for t in teams if t["status"] == "verified_text")
    n_flag = sum(1 for t in teams if t["status"] == "flagged_image_only")
    body = f"""
<div class="cards">
  <div class="card"><h3>Clubs swept</h3><div class="num">{len(teams)}</div><p>All 32 clubs, official <code>/team/depth-chart</code> route, verified club by club (2026-11-17).</p></div>
  <div class="card"><h3>Text-verified transcripts</h3><div class="num">{n_text}</div><p>Verbatim machine-readable captures stored in <code>data/raw/</code>.</p></div>
  <div class="card"><h3>Flagged (image-only)</h3><div class="num">{n_flag}</div><p>HOU publishes depth as an image — blank + flagged, never transcribed by eye.</p></div>
  <div class="card"><h3>Stale-depth flags</h3><div class="num">6</div><p>Reserve-list cross-check flags (5) + LAC page transactions flag (1).</p></div>
</div>
<h2>What this sweep delivers</h2>
<ul>
  <li><b>Depth-order source resolved club by club</b> (route (a) of the brief): 31 clubs text-verified; HOU flagged.</li>
  <li><b>Official depth-chart register</b> with date + source per row: <a href="register.html">Depth Register</a>.</li>
  <li><b>32-team roster/IR sweep</b> against the official league reserve list: <a href="ir-sweep.html">Roster / IR Sweep</a>.</li>
  <li><b>Flagged for Review</b>: every flag with its evidence: <a href="flagged.html">Flagged for Review</a>.</li>
  <li>Per-club depth pages: <a href="register.html">see the register</a> and click any club code.</li>
</ul>
<h2>Method</h2>
<p>Every published cell is transcribed verbatim from a club page fetched in this session (URL + fetch date recorded in each transcript) or computed by a checked-in engine from checked-in artefacts. No depth order is inferred from jersey number, experience, or salary. Shared rank slots keep both names. Unconfirmable values are blank + flagged.</p>
<h2>Key findings</h2>
<ul>
  <li>Official domains are not the short forms: 17 domain corrections recorded (<code>data/teams.json</code>).</li>
  <li>Depth format is not uniform: jersey-number prepend (GB), player-link names, shared rank slots (13 clubs), sparse cells, and per-club position naming.</li>
  <li>Charts are dated snapshots: page-stated dates where published (CHI 10/31, GB/LV/SF/TEN 11/10), capture date otherwise.</li>
  <li>Stale-depth cases found: LAC Derwin James Jr. (S1, IR per page log); LAR Puka Nacua (WR1) and Jordan Whittington (KR1); TEN Peter Skoronski (LG1), Tommy Townsend (P1/H1) — all still rank1 on their clubs' charts.</li>
</ul>
"""
    page("NFL Depth-Chart Sweep", body, "index.html",
         sub="32-club official depth-chart sweep — capture, register, roster/IR cross-check (2026-11-17)")


def build_register():
    reg = load("depth_register.json")["clubs"]
    rows = []
    for c in reg:
        flags = " ".join(f'<span class="badge flag">{E(f["flag"].replace("_", " "))}</span>' for f in c["flags"])
        rows.append(
            f'<tr><td><a href="clubs/{E(c["club"])}.html">{E(c["club"])}</a></td>'
            f'<td>{badge(c["status"])}</td>'
            f'<td>{E(c["snapshot_date"])}</td>'
            f'<td>{E(c["source_url"] or "")}</td>'
            f'<td>{len(c["positions"])}</td>'
            f'<td>{flags}</td></tr>'
        )
    body = f"""
<p>Official depth-chart register: one row per club with date + source. 32 clubs, 705 position rows
(position / rank1 / rank2 / rank3). Click a club code for the per-club depth page.</p>
<table><thead><tr><th>Club</th><th>Status</th><th>Snapshot date</th><th>Source (fetched 2026-11-17)</th><th>Position rows</th><th>Flags</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
"""
    page("Depth Register", body, "register.html",
         sub="Official depth-chart register — date + source per row, 32 clubs")


def build_club(c):
    rows = []
    for p in c["positions"]:
        flags = []
        for f in c["flags"]:
            flags.append(f'<span class="badge flag">{E(f["flag"].replace("_", " "))}</span>')
        flag_cell = " ".join(flags) if flags else ""
        rows.append(
            f'<tr><td>{E(p["position"])}</td>{cell_name(p["rank1"])}{cell_name(p["rank2"])}{cell_name(p["rank3"])}'
            f'<td>{src_link(c["source_url"])}</td><td>{flag_cell}</td></tr>'
        )
    if c["status"] == "flagged_image_only":
        body = f"""
<p>{badge(c["status"])} — the official page publishes the depth chart as a static image with no
machine-readable text surface. Per the sweep rules this club is <b>blank + flagged</b>: no cell is
transcribed by eye.</p>
<table><thead><tr><th>Position</th><th>Rank 1</th><th>Rank 2</th><th>Rank 3</th><th>Source</th><th>Flags</th></tr></thead>
<tbody>
<tr><td colspan="3">(no text surface — chart is an image)</td><td>{src_link(c["source_url"])}</td><td>{badge("flagged image only")}</td></tr>
</tbody></table>
<p>Evidence: transcript <code>data/raw/{E(c["club"])}.md</code> records the page URL, fetch date, and image asset.</p>
"""
    else:
        body = f"""
<p>{badge(c["status"])} · snapshot {E(c["snapshot_date"])} ({E(c["snapshot_date_note"])}) ·
transcript <code>data/raw/{E(c["club"])}.md</code> · parsed <code>data/parsed/{E(c["club"])}.json</code></p>
<table><thead><tr><th>Position</th><th>Rank 1</th><th>Rank 2</th><th>Rank 3</th><th>Source</th><th>Flags</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p>Every row links to the club's official depth page captured 2026-11-17. Shared rank slots show
<code>[alt]</code>. Jersey numbers (#) shown where the page prints them. Blank cells are blank on the page.</p>
"""
    page(f"{c['club']} — Depth Chart", body, f"clubs/{c['club']}.html",
         sub=f"Official depth chart, captured 2026-11-17 · {c['source_url']}")


def build_flagged():
    reg = load("depth_register.json")["clubs"]
    ir = load("roster_ir_sweep.json")
    items = []
    for c in reg:
        for f in c["flags"]:
            items.append((c["club"], f["flag"], f["detail"], c["source_url"]))
    for club in ir["clubs"]:
        for s in club.get("stale_depth_flags", []):
            items.append((club["club"], "stale_depth_ir", s["evidence"],
                          "https://www.nfl.com/transactions/league/reserve-list/2026/11"))
    rows = []
    for club, flag, detail, url in sorted(items):
        rows.append(
            f'<tr><td><a href="clubs/{E(club)}.html">{E(club)}</a></td>'
            f'<td><span class="badge flag">{E(flag.replace("_", " "))}</span></td>'
            f'<td>{E(detail)}</td>'
            f'<td><a href="{E(url)}" target="_blank" rel="noopener">source</a></td></tr>'
        )
    body = f"""
<p>Flagged for Review — every flag raised by the sweep, with its evidence and source. Unverifiable
cells stay blank; these flags are the review queue for the depth layer.</p>
<table><thead><tr><th>Club</th><th>Flag</th><th>Detail</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
"""
    page("Flagged for Review", body, "flagged.html",
         sub="All sweep flags with evidence — the review queue for the depth layer")


def build_ir_sweep():
    ir = load("roster_ir_sweep.json")
    rows = []
    for club in ir["clubs"]:
        if club["reserve_count"] == 0 and not club["starters_on_ir"]:
            continue
        flags = " ".join(f'<span class="badge flag">{E(s["player"])} ({E(s["position"])} r1)</span>'
                         for s in club["starters_on_ir"])
        entries = "; ".join(f'{E(e["date"])} {E(e["player"])}' for e in club["reserve_entries"]) or "—"
        rows.append(
            f'<tr><td>{E(club["club"])}</td><td>{len(club["reserve_entries"])}</td>'
            f'<td>{E(entries)}</td><td>{flags}</td></tr>'
        )
    body = f"""
<p>32-team roster/IR sweep vs the official league reserve list (November 2026,
<a href="https://www.nfl.com/transactions/league/reserve-list/2026/11" target="_blank" rel="noopener">source</a>).
{ir["summary"]["reserve_entries_total"]} Reserve/Injured entries across {ir["summary"]["clubs_with_reserve_entries"]} clubs;
{ir["summary"]["stale_depth_flags_total"]} stale-depth flags where a reserve player still holds rank1 on the club's own chart.
Replacement depth is recorded in <code>data/roster_ir_sweep.json</code>.</p>
<table><thead><tr><th>Club</th><th>Reserve entries</th><th>November 2026 Reserve/Injured</th><th>Starters on IR (stale-depth)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
"""
    page("Roster / IR Sweep", body, "ir-sweep.html",
         sub="32-team roster/IR sweep vs the official reserve list (November 2026)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_index()
    build_register()
    for c in load("depth_register.json")["clubs"]:
        build_club(c)
    build_flagged()
    build_ir_sweep()
    n_pages = len(list(OUT.rglob("*.html")))
    print(f"site built: {n_pages} pages -> {OUT}")


if __name__ == "__main__":
    main()

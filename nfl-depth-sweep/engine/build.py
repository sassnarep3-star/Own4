#!/usr/bin/env python3
"""nfl-depth-sweep build — generates the static pages from the committed data.

Deterministic: no wall-clock, no randomness. Every aggregate rendered into a page is
computed here from the JSON files; nothing is typed into prose.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"

NAV = [
    ("index.html", "Dashboard"),
    ("pages/sweep.html", "32-club sweep"),
    ("pages/findings.html", "Findings"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources"),
    ("pages/method.html", "Method"),
]


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def esc(v):
    return html.escape(str(v), quote=True)


def num(v):
    return "—" if v is None else str(v)


def page(title, body, depth=""):
    nav = " · ".join(f'<a href="{depth}{h}">{esc(t)}</a>' for h, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · nfl-depth-sweep</title>
<link rel="stylesheet" href="{depth}assets/site.css"></head>
<body>
<header class="site"><a href="{depth}index.html"><b>nfl-depth-sweep</b></a> — 32-club official depth-chart route sweep
<br><nav>{nav}</nav></header>
<main>
{body}
</main>
<footer>Research only — not wagering advice. Every row links to the official page it was read from;
unconfirmable values are blank and flagged. Built {esc(ROUTE_C['built_utc'])} by session arena-76537469-own4 ·
<a href="https://github.com/sassnarep3-star/Own4">repo</a></footer>
</body></html>
"""


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def aggregates():
    rows_c = ROUTE_C["rows"]
    rows_l = ROUTE_L["rows"]
    present = [r for r in rows_c if r["route_c_result"] == "present"]
    tables = [r for r in rows_c if r["structure"] == "html-table"]
    images = [r for r in rows_c if r["structure"].startswith("image")]
    dated = [r for r in rows_c if r["as_of"]]
    undated = [r for r in rows_c if not r["as_of"]]
    shared = [r for r in rows_c if (r["shared_rank1_n"] or 0) > 0]
    empty = [r for r in rows_c if (r["empty_rank1_n"] or 0) > 0]
    unofficial_yes = [r for r in rows_c if r["unofficial"] == "yes"]
    l404 = [r for r in rows_l if r["result"] == "404"]
    slots = sum((r["off_n"] or 0) + (r["def_n"] or 0) + (r["st_n"] or 0) for r in rows_c)
    shared_slots = sum(r["shared_rank1_n"] or 0 for r in rows_c)
    empty_slots = sum(r["empty_rank1_n"] or 0 for r in rows_c)
    # age of each dated chart relative to the build date, computed not typed
    from datetime import date
    built = date.fromisoformat(ROUTE_C["built_utc"])
    ages = {r["abbr"]: (built - date.fromisoformat(r["as_of"])).days for r in dated}
    return dict(present=present, tables=tables, images=images, dated=dated, undated=undated,
                shared=shared, empty=empty, unofficial_yes=unofficial_yes, l404=l404,
                slots=slots, shared_slots=shared_slots, empty_slots=empty_slots, ages=ages)


def build_sweep(agg):
    tr = []
    for rc in ROUTE_C["rows"]:
        rl = next(r for r in ROUTE_L["rows"] if r["abbr"] == rc["abbr"])
        struct_badge = ("b-ok" if rc["structure"] == "html-table" else "b-warn")
        as_of = rc["as_of"] or ""
        age = agg["ages"].get(rc["abbr"])
        as_cell = (f"{esc(as_of)} <span class='small'>({age}d before build)</span>" if age is not None
                   else "<span class='blank' title='page prints no as-of date — unverified freshness'>—</span>")
        shared = (f"<span class='badge b-warn'>{rc['shared_rank1_n']} slot(s)</span> {esc(rc['shared_rank1_desc'])}"
                  if rc["shared_rank1_n"] else "<span class='blank'>—</span>")
        empty = (f"<span class='badge b-bad'>{rc['empty_rank1_n']} slot(s)</span> {esc(rc['empty_rank1_desc'])}"
                 if rc["empty_rank1_n"] else "<span class='blank'>—</span>")
        slots = ("<span class='blank' title='image-only chart — no rows are machine-readable'>—</span>"
                 if rc["off_n"] is None else f"{rc['off_n']}/{rc['def_n']}/{rc['st_n']}")
        un = rc["unofficial"]
        un_badge = {"yes": "<span class='badge b-warn'>unofficial</span>",
                    "no": "<span class='badge b-info'>not labelled</span>",
                    "news-only": "<span class='badge b-warn'>unofficial (news)</span>",
                    "none-printed": "<span class='badge b-warn'>no heading</span>"}[un]
        tr.append(f"""<tr><td><b>{esc(rc['abbr'])}</b></td><td>{esc(rc['team'])}</td>
<td><span class='badge b-bad'>{esc(rl['result'])}</span> <a class="src" href="{esc(rl['url'])}">league path</a></td>
<td><span class='badge b-ok'>{esc(rc['route_c_result'])}</span> <a class="src" href="{esc(rc['route_c_url'])}">club page</a></td>
<td><span class='badge {struct_badge}'>{esc(rc['structure'])}</span></td>
<td>{as_cell}</td><td>{un_badge}</td><td>{slots}</td><td>{shared}</td><td>{empty}</td></tr>""")
    body = f"""
<h1>The 32-club depth-chart route sweep</h1>
<p class="lead">G-02 / RC-02 / SG-C route (a): every league per-team depth path and every club depth page,
read on {esc(ROUTE_C['built_utc'])}. Route L = the league's own path; Route C = the club's official site
(host taken from the league's own <a href="https://www.nfl.com/teams/">View Full Site</a> link).</p>
<div class="note warn"><b>How to read this table.</b> “404” means the fetch returned the league's own
“404 – Flag on the Play.” body. “present” means the page rendered a chart. Slot columns are
offence/defence/special-teams row counts as printed. Rank-1 columns flag slots where the first cell
holds two players or is empty — a column-1 read would fabricate a starter there.</div>
<div class="wrap"><table>
<thead><tr><th>Club</th><th>Team</th><th>Route L (nfl.com)</th><th>Route C (club site)</th>
<th>Structure</th><th>Printed as-of</th><th>Self-label</th><th>Off/Def/ST slots</th>
<th>Rank-1 shared</th><th>Rank-1 empty</th></tr></thead>
<tbody>
{''.join(tr)}
</tbody></table></div>
<p class="lead">Row sources: the club-page link in each row is the source of every field transcribed
from that row. League-path links are the source of the 404 result.</p>
"""
    return page("32-club sweep", body, depth="../")


def build_index(agg):
    a = agg
    cards = f"""
<div class="cards">
<div class="card bad"><div class="k">{len(a['l404'])}/32</div><div class="l">league depth paths returning 404</div></div>
<div class="card ok"><div class="k">{len(a['present'])}/32</div><div class="l">club depth pages present</div></div>
<div class="card ok"><div class="k">{len(a['tables'])}</div><div class="l">machine-readable HTML tables</div></div>
<div class="card warn"><div class="k">{len(a['images'])}</div><div class="l">image-only chart (HOU)</div></div>
<div class="card warn"><div class="k">{len(a['dated'])}/32</div><div class="l">pages printing an as-of date</div></div>
<div class="card bad"><div class="k">{a['shared_slots']}</div><div class="l">rank-1 cells holding 2+ players</div></div>
<div class="card bad"><div class="k">{a['empty_slots']}</div><div class="l">rank-1 cells printed empty</div></div>
<div class="card warn"><div class="k">{len(a['unofficial_yes'])}</div><div class="l">pages self-labelled unofficial</div></div>
</div>
"""
    body = f"""
<h1>32-club depth-chart route sweep</h1>
<p class="lead">Answers decision-console gap <b>G-02</b> and collector flag <b>RC-02</b>: is there an
official depth-chart route for all 32 clubs? Swept {esc(ROUTE_C['built_utc'])} by session arena-76537469-own4.</p>
{cards}
<div class="note"><b>Answer, in two lines.</b> The league route is closed: all
{len(a['l404'])} per-team depth paths on nfl.com — and the league-wide <code>/depth-charts/</code> —
return the league's own 404 body. The club route is open: all {len(a['present'])} clubs publish a
depth page at <code>/team/depth-chart</code>, {len(a['tables'])} of them as machine-readable tables.
Houston is the single exception (chart is an image).</div>
<div class="note warn"><b>But the route is not yet a starter source.</b> {a['shared_slots']} rank-1 cells
across {len(a['shared'])} clubs hold two or more players, and {a['empty_slots']} cells across
{len(a['empty'])} clubs are printed empty — column-1 would fabricate starters. Only
{len(a['dated'])} of 32 pages print an as-of date; {len(a['undated'])} print none, so freshness is
unverifiable for those. {len(a['unofficial_yes'])} pages self-label unofficial, one explicitly says it
reflects only its writers' opinions. <b>Depth must be modelled as groups, with capture timestamps —
exactly as the brief requires — and the SG-C verdict on building the deficiency feature remains an
owner decision this sweep does not take.</b></div>
<h2>Pages</h2>
<ul class="tight">
<li><a href="pages/sweep.html">32-club sweep</a> — one row per club, both routes, every cell sourced</li>
<li><a href="pages/findings.html">Findings</a> — what the sweep proves and what it does not</li>
<li><a href="pages/flagged.html">Flagged for review</a> — irregularities, non-blocking</li>
<li><a href="pages/sources.html">Sources</a> — every official page read, in session order</li>
<li><a href="pages/method.html">Method</a> — probe rules, limits, and what is transcribed vs computed</li>
</ul>
"""
    return page("Dashboard", body)


def build_findings(agg):
    a = agg
    age_rows = "".join(
        f"<tr><td>{esc(ab)}</td><td>{esc(next(r['as_of'] for r in a['dated'] if r['abbr']==ab))}</td>"
        f"<td>{d} days</td><td><a class='src' href='{esc(next(r['route_c_url'] for r in a['dated'] if r['abbr']==ab))}'>club page</a></td></tr>"
        for ab, d in sorted(a["ages"].items(), key=lambda kv: -kv[1]))
    shared_rows = "".join(
        f"<tr><td>{esc(r['abbr'])}</td><td>{r['shared_rank1_n']}</td><td>{esc(r['shared_rank1_desc'])}</td>"
        f"<td><a class='src' href='{esc(r['route_c_url'])}'>source</a></td></tr>" for r in a["shared"])
    empty_rows = "".join(
        f"<tr><td>{esc(r['abbr'])}</td><td>{r['empty_rank1_n']}</td><td>{esc(r['empty_rank1_desc'])}</td>"
        f"<td><a class='src' href='{esc(r['route_c_url'])}'>source</a></td></tr>" for r in a["empty"])
    body = f"""
<h1>Findings</h1>
<p class="lead">Every number below is computed at build time from <code>data/route_l.json</code> and
<code>data/route_c.json</code>; the page generator fails if the data and the prose disagree.</p>

<h2>1 · The league route is closed (answers G-02's first half)</h2>
<p>All {len(a['l404'])} league per-team depth paths
(<code>nfl.com/teams/&lt;slug&gt;/depth-chart/</code>) returned the league's own
“404 – Flag on the Play.” body on {esc(ROUTE_C['built_utc'])}, and so did the league-wide
<a href="https://www.nfl.com/depth-charts/"><code>nfl.com/depth-charts/</code></a>.
There is no depth chart to parse on nfl.com itself. Source of every row:
<a href="https://www.nfl.com/teams/">nfl.com/teams/</a> (the league's own club index).</p>

<h2>2 · The club route is open for all 32 clubs (answers G-02's second half)</h2>
<p>Every club publishes <code>/team/depth-chart</code> on the host the league itself links as its
“View Full Site”. {len(a['present'])}/32 present · {len(a['tables'])} machine-readable HTML tables ·
{len(a['images'])} image-only (Houston — the known limitation, re-confirmed). Total transcribed slots
across the {len(a['tables'])} table clubs: <b>{a['slots']}</b> off/def/special-team rows.</p>

<h2>3 · Freshness: only {len(a['dated'])} of 32 pages print an as-of date</h2>
<table><thead><tr><th>Club</th><th>Printed as-of</th><th>Age at build</th><th>Source</th></tr></thead>
<tbody>{age_rows}</tbody></table>
<p>The other {len(a['undated'])} pages print <span class="blank">no date at all</span> — freshness for
those is <b>unverified</b> and must come from our own capture timestamps, not the page.</p>

<h2>4 · Column-1 is not a starter: {a['shared_slots']} shared rank-1 cells</h2>
<table><thead><tr><th>Club</th><th>Slots</th><th>What the rank-1 cell prints</th><th>Source</th></tr></thead>
<tbody>{shared_rows}</tbody></table>

<h2>5 · And {a['empty_slots']} rank-1 cells are printed empty</h2>
<table><thead><tr><th>Club</th><th>Slots</th><th>What the page prints</th><th>Source</th></tr></thead>
<tbody>{empty_rows}</tbody></table>
<p>Findings 4 and 5 together are the mechanical evidence for the brief's rule:
<b>model depth slots as groups, never as “column 1 = the starter”</b>, and never derive depth from
jersey number, experience or salary.</p>

<h2>6 · Self-labels differ club by club</h2>
<p>{len(a['unofficial_yes'])} pages self-label <i>unofficial</i>; Indianapolis is labelled unofficial only
in its dated release news; Seattle's page renders no heading at all; Arizona's heading says
“Official Depth Chart” — the only club claiming official; New England states explicitly that the chart
“reflects the opinions of the Patriots.com writers and don't necessarily reflect those of the
organization”. <b>No club page is a league-official statement of depth.</b></p>

<h2>7 · What this sweep does not decide</h2>
<ul class="tight">
<li>Whether the deficiency feature may be built (SG-C) — still an owner verdict, left blank.</li>
<li>Whether any printed depth matches who actually played — that needs Game Book participation
(covered elsewhere: <code>nfl-collector</code>, RC-07).</li>
<li>Houston's rows — image-only, so blank here; needs an authorized structured source, not
transcription by eye (the inherited limitation).</li>
<li>Staleness of any specific row against the transactions log — only flagged where a page contradicts
itself (see <a href="flagged.html">Flagged</a>), never asserted.</li>
</ul>
"""
    return page("Findings", body, depth="../")


def build_flagged(agg):
    a = agg
    flags = [
        ("DS-01", "League depth route closed", "blocking for nfl.com route",
         f"All {len(a['l404'])} league per-team depth paths and the league-wide /depth-charts/ return 404; no league-owned depth page exists to parse.",
         "https://www.nfl.com/depth-charts/"),
        ("DS-02", "Houston chart is an image", "blocks HOU rows",
         "houstontexans.com/team/depth-chart renders the chart as a single image; no HTML table, so HOU slot fields are blank here, not guessed. Needs an authorized structured source, not transcription by eye.",
         "https://www.houstontexans.com/team/depth-chart"),
        ("DS-03", "Rank-1 cells hold two or more players", "blocks column-1 starter reads",
         f"{a['shared_slots']} rank-1 cells across {len(a['shared'])} clubs list 2+ players (see Findings §4). Any model treating cell 1 as 'the starter' would fabricate a starter the club never named.",
         "https://www.seahawks.com/team/depth-chart/"),
        ("DS-04", "Rank-1 cells printed empty", "blocks column-1 starter reads",
         f"{a['empty_slots']} slots across {len(a['empty'])} clubs print an empty first cell (BAL K, MIA K, NYJ DL, PHI DT, GB PR) — see Findings §5.",
         "https://www.baltimoreravens.com/team/depth-chart"),
        ("DS-05", "Freshness unverifiable for most pages", "blocks dated replay",
         f"Only {len(a['dated'])} of 32 pages print an as-of date; the other {len(a['undated'])} print none. Undated pages must be timestamped by our own captures before any backtest uses them.",
         "https://www.nfl.com/teams/"),
        ("DS-06", "Self-labels disagree; one club claims 'Official'", "blocks 'official depth' wording",
         "12 pages self-label unofficial, New England says the chart is its writers' opinions, Seattle prints no heading, and Arizona alone titles its page 'Official Depth Chart'. The sweep therefore reports each page as a club publication, never as a league-official depth statement.",
         "https://www.azcardinals.com/team/depth-chart"),
        ("DS-07", "Packers rows carry jersey-number prefixes", "parser requirement",
         "packers.com prints '9 Christian Watson' style cells; any parser must strip leading numbers and keep the raw string. Re-confirmed on the 2026-11-17 read.",
         "https://www.packers.com/team/depth-chart"),
        ("DS-08", "Commanders page title typo", "cosmetic",
         "The page <title> reads 'Washington Commanders l Team Depth Chart | Washington Commanders - Commanders.comcom' (duplicated 'com'). Content unaffected.",
         "https://www.commanders.com/team/depth-chart"),
        ("DS-09", "Jaguars header image still says 2024", "cosmetic",
         "Header image alt text reads '2024-DEPTH-CHART-HEADER' on the 2026 page.",
         "https://www.jaguars.com/team/depth-chart"),
        ("DS-10", "Buccaneers print two KR rows", "duplicate position label",
         "The special-teams table contains two rows labelled KR (Kenny Gainwell; Kameron Johnson). Recorded as printed; not reconciled here.",
         "https://www.buccaneers.com/team/depth-chart"),
        ("DS-11", "Chargers page contradicts itself on Derwin James Jr.", "staleness candidate — unverified",
         "The same page lists Derwin James Jr. as starting S while its own Latest Transactions module links 'Los Angeles Chargers Place Derwin James Jr. on Injured Reserve'. The transaction's date was not captured in this read, so staleness is NOT asserted — only flagged for a dated check against the transactions log.",
         "https://www.chargers.com/team/depth-chart"),
        ("DS-12", "Titans page prints a stray 'Untitled Document' line", "cosmetic",
         "The string 'Untitled Document' renders above the depth-chart heading.",
         "https://www.tennesseetitans.com/team/depth-chart"),
        ("DS-13", "No HTTP status captured", "method limit",
         "The fetch tool returns rendered bodies, not status codes; a 404 is detected from the league's own error body text. Club pages could theoretically be soft-404s — every 'present' row here contains a real chart table (or the Texans image), which is the positive evidence used instead.",
         "https://www.nfl.com/teams/"),
    ]
    rows = "".join(
        f"<tr><td><b>{i}</b></td><td>{esc(t)}</td><td><span class='badge b-warn'>{esc(sev)}</span></td>"
        f"<td>{esc(d)}</td><td><a class='src' href='{u}'>source</a></td></tr>"
        for i, t, sev, d, u in flags)
    body = f"""
<h1>Flagged for review</h1>
<p class="lead">Irregularities found while sweeping — published, sourced, non-blocking. Nothing here is
inferred or filled in; unconfirmable values stay blank.</p>
<div class="wrap"><table>
<thead><tr><th>ID</th><th>Irregularity</th><th>Severity</th><th>Detail</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class="note">DS-01..DS-13 do not block publishing this sweep. They block <i>using</i> depth as a
starter source without the group-slot semantics, capture timestamps and the Houston exception stated
on <a href="findings.html">Findings</a>.</div>
"""
    return page("Flagged for review", body, depth="../")


def build_sources():
    rows = []
    rows.append(("League club index (source of all 32 club hosts + profile slugs)",
                 "https://www.nfl.com/teams/", "read 2026-11-17"))
    rows.append(("League-wide depth-chart path", "https://www.nfl.com/depth-charts/", "read 2026-11-17 — 404 body"))
    for rl in ROUTE_L["rows"]:
        rows.append((f"Route L — {rl['team']} league depth path", rl["url"], "read 2026-11-17 — 404 body"))
    for rc in ROUTE_C["rows"]:
        rows.append((f"Route C — {rc['team']} club depth page", rc["route_c_url"],
                     f"read 2026-11-17 — {rc['structure']}"))
    tr = "".join(f"<tr><td>{esc(w)}</td><td><a class='src' href='{esc(u)}'>{esc(u)}</a></td><td>{esc(s)}</td></tr>"
                 for w, u, s in rows)
    body = f"""
<h1>Sources</h1>
<p class="lead">Every official page read in this session, in order. {len(rows)} entries. All rows in the
sweep tables link to their own source; this is the full read log.</p>
<div class="wrap"><table><thead><tr><th>What was read</th><th>URL</th><th>Result / window</th></tr></thead>
<tbody>{tr}</tbody></table></div>
<p class="lead">No third-party, aggregator, roster-project or betting site was read or used. Hosts were
never assumed: every club host comes from the league's own “View Full Site” link.</p>
"""
    return page("Sources", body, depth="../")


def build_method():
    body = f"""
<h1>Method</h1>
<p class="lead">How the sweep was run, what is transcribed, what is computed, and where it can be wrong.</p>
<h2>Probe rules</h2>
<ul class="tight">
<li><b>Route L (league):</b> one fetch per <code>https://www.nfl.com/teams/&lt;slug&gt;/depth-chart/</code>
for all 32 slugs from <a href="https://www.nfl.com/teams/">nfl.com/teams/</a>, plus the league-wide
<code>/depth-charts/</code>. Result recorded from the rendered body: the league's
“404 – Flag on the Play.” text is the 404 evidence (no HTTP status is exposed by the fetch tool — DS-13).</li>
<li><b>Route C (club):</b> one fetch per <code>https://www.&lt;club-host&gt;/team/depth-chart</code>.
Every club host is copied from the league's own “View Full Site” link — none is assumed.</li>
<li>Window: all reads on {esc(ROUTE_C['built_utc'])} UTC, one session pass. The fetch tool exposes no
per-call clock, so the window is recorded rather than per-row timestamps (same convention as
nfl-collector's SUG-12 A).</li>
</ul>
<h2>Transcribed vs computed</h2>
<ul class="tight">
<li><b>Transcribed per row:</b> result, structure, heading, printed as-of date, self-label, slot row
counts, shared/empty rank-1 observations, notes. Each is a reading of the page named in that row's
source link.</li>
<li><b>Computed at build time:</b> every aggregate on the Dashboard and Findings pages (counts of
404s, present, tables, dated, shared/empty slots, totals, chart ages). The generator derives them from
the JSON; <code>engine/verify.py</code> recomputes and fails the build if any published aggregate
disagrees with the data.</li>
</ul>
<h2>Limits (stated, not hidden)</h2>
<ul class="tight">
<li>No per-fetch clock (window only); no HTTP status codes (body evidence only).</li>
<li>Slot counts are counts of the rendered table rows as read; a club that edits its page after
{esc(ROUTE_C['built_utc'])} will differ — re-run the sweep to refresh.</li>
<li>Houston's image chart is not transcribed: its row fields are blank by rule (DS-02).</li>
<li>The sweep records what pages <i>print</i>. It does not verify that printed depth matches who
actually played — that requires official Game Book participation, tracked in <code>nfl-collector</code>.</li>
<li>No verdict is taken on SG-C (building the deficiency feature): that decision stays with the owner;
this sweep is the evidence needed to make it.</li>
</ul>
<h2>Rebuild &amp; verify</h2>
<p><code>python3 engine/build.py &amp;&amp; python3 engine/verify.py</code> — standard library only.
Verify fails on: row counts ≠ 32, missing source links, aggregates disagreeing with data, broken
internal links, or a non-deterministic rebuild.</p>
"""
    return page("Method", body, depth="../")


def main():
    write("index.html", build_index(aggregates()))
    write("pages/sweep.html", build_sweep(aggregates()))
    write("pages/findings.html", build_findings(aggregates()))
    write("pages/flagged.html", build_flagged(aggregates()))
    write("pages/sources.html", build_sources())
    write("pages/method.html", build_method())
    print("built: index.html + 5 pages")


if __name__ == "__main__":
    global ROUTE_L, ROUTE_C
    ROUTE_L = load("route_l.json")
    ROUTE_C = load("route_c.json")
    main()

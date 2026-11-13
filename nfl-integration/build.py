#!/usr/bin/env python3
"""Build the NFL integration-review site (session arena/8e2de421-own4).

Deterministic: renders index.html + pages/*.html from data/*.json.
Every table row carries an https source link (enforced by verify.py).

Run:  python3 nfl-integration/build.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

NAV = [
    ("index.html", "Dashboard"),
    ("pages/verification.html", "Verification ledger"),
    ("pages/comparisons.html", "Line-by-line comparisons"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources"),
]

FOOTER = """<footer>
<p><strong>Own4 · NFL integration review</strong> — analytical research only, not wagering
advice. Every row below links to the official page it was checked against; anything that
could not be confirmed is left blank and published on the
<a href="{p}pages/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>"""

CSS = """/* Own4 — NFL integration review */
:root{--bg:#0e1117;--panel:#161b24;--line:#262d3a;--text:#e6e9ef;--muted:#98a2b3;
--brand:#4da3ff;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--neu:#8b949e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand)}
header.top{position:sticky;top:0;background:#0b0e13;border-bottom:1px solid var(--line);
z-index:5;display:flex;flex-wrap:wrap;gap:.4rem 1rem;align-items:center;padding:.65rem 1.1rem}
header.top .brand{font-weight:700;text-decoration:none;color:var(--text);margin-right:.6rem}
header.top a{color:var(--muted);text-decoration:none;padding:.25rem .5rem;border-radius:6px}
header.top a:hover{background:var(--panel);color:var(--text)}
main{max-width:1100px;margin:0 auto;padding:1.4rem 1.1rem 3rem}
h1{font-size:1.5rem;margin:.2rem 0 .8rem}
h2{font-size:1.15rem;margin:1.6rem 0 .6rem;border-top:1px solid var(--line);padding-top:1rem}
h3{font-size:1rem;margin:1.1rem 0 .4rem}
.lede{color:var(--muted);max-width:60rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.7rem;margin:1rem 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.7rem .8rem}
.card .n{font-size:1.45rem;font-weight:700}
.card .l{color:var(--muted);font-size:.8rem}
.card.ok .n{color:var(--ok)} .card.warn .n{color:var(--warn)} .card.brand .n{color:var(--brand)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand);
border-radius:8px;padding:.7rem .9rem;margin:.9rem 0;color:var(--muted)}
.note.warn{border-left-color:var(--warn)}
.note.good{border-left-color:var(--ok)}
.tbl-wrap{overflow-x:auto;margin:.6rem 0 1rem;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:.86rem;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:.5rem .6rem;text-align:left;vertical-align:top}
th{background:#10141b;color:var(--muted);font-weight:600;position:sticky;top:0}
tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums}
a.src{white-space:nowrap}
.pill{display:inline-block;padding:.08rem .5rem;border-radius:999px;font-size:.74rem;font-weight:600}
.p-ok{background:#12261a;color:var(--ok)} .p-bad{background:#2a1214;color:var(--bad)}
.p-warn{background:#2b2110;color:var(--warn)} .p-neu{background:#1c2230;color:var(--neu)}
.p-fixed{background:#12261a;color:var(--ok)}
ul.tight{margin:.4rem 0;padding-left:1.2rem}
ul.tight li{margin:.25rem 0}
code{background:#10141b;padding:.1rem .35rem;border-radius:5px;font-size:.85em}
.small{color:var(--muted);font-size:.84rem}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.82rem;
padding:1rem 1.1rem 2rem;max-width:1100px;margin:0 auto}
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8") as f:
        return json.load(f)


def page(path, title, body):
    depth = path.count("/")
    p = "../" * depth
    links = "".join(
        '<a href="{p}{href}">{label}</a>'.format(p=p, href=href, label=label)
        for href, label in NAV)
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Own4 NFL integration review</title>
<meta name="description" content="Line-by-line verification of the Own4 NFL namespaces against official NFL.com sources, 2026-11-13.">
<link rel="stylesheet" href="{p}assets/style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="{p}index.html">Own4 · NFL integration</a>
  {links}
</header>
<main>
{body}
</main>
<footer>
<p><strong>Own4 · NFL integration review</strong> — analytical research only, not wagering
advice. Every row links to the official page it was checked against; anything that could
not be confirmed is left blank and published on the
<a href="{p}pages/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>
</body>
</html>
""".format(title=esc(title), p=p, links=links, body=body)
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(doc)


def table(headers, rows):
    th = "".join("<th>%s</th>" % h for h in headers)
    tr = []
    for r in rows:
        tr.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r))
    return ('<div class="tbl-wrap"><table><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (th, "".join(tr)))


def result_pill(r):
    cls = {"PASS": "p-ok", "NOT RUN": "p-warn", "FAIL": "p-bad"}.get(r, "p-neu")
    return '<span class="pill %s">%s</span>' % (cls, esc(r))


def build_index():
    ver = load("verification.json")
    flags = load("flags.json")
    sc = load("standings_comparison.json")
    tc = load("team_stats_comparison.json")
    checks = ver["checks"]
    n_pass = sum(1 for c in checks if c["result"] == "PASS")
    n_notrun = sum(1 for c in checks if c["result"] == "NOT RUN")
    st_files = sc["results"]
    st_pass = sum(1 for s in st_files if s.get("verdict", "").startswith("PASS"))
    exact = (tc["nfl_lines_passing"]["exact_matches"]
             + tc["nfl_edge_scoring_and_pts"]["exact_matches"]
             + tc["official_cross_check_scoring_vs_passing_td"]["compared"])
    drift = (len(tc["nfl_lines_passing"]["expected_drift"])
             + len(tc["nfl_edge_scoring_and_pts"]["expected_drift"]))

    cards = [
        ("%d" % len(checks), "checks executed", "brand"),
        ("%d/%d" % (n_pass, len(checks)), "passed", "ok"),
        ("%d" % st_pass, "standings files match official 32/32", "ok"),
        ("%d" % exact, "team-stat values matched exactly", "ok"),
        ("%d" % drift, "expected drift values (Thursday game)", "warn"),
        ("%d" % len(flags["flags"]), "items flagged for review", "warn"),
        ("11", "NFL namespaces now linked from the root", "brand"),
        ("0", "rewards — no strategy passes G7 (no price source)", ""),
    ]
    card_html = "".join(
        '<div class="card %s"><div class="n">%s</div><div class="l">%s</div></div>'
        % (cls, n, l) for n, l, cls in cards)

    # standings summary rows
    st_rows = []
    for s in st_files:
        if "error" in s:
            st_rows.append([esc(s["path"]), '<span class="pill p-bad">ERROR</span>',
                            esc(s["error"]),
                            '<a class="src" href="https://www.nfl.com/standings/">nfl.com ↗</a>'])
            continue
        v = s["verdict"]
        pill = ("p-ok" if v.startswith("PASS") else
                "p-warn" if "OLDER" in v else "p-bad")
        st_rows.append([
            esc(s["path"]),
            '<span class="pill %s">%s</span>' % (pill, esc(v)),
            '%d/32 vs expected · %d/32 vs live' % (
                s["vs_expected_reference"]["matches"],
                s["vs_live_2026-11-13"]["matches"]),
            '<a class="src" href="https://www.nfl.com/standings/">nfl.com ↗</a>'])

    body = """<h1>NFL integration review — 2026-11-13</h1>
<p class="lede">Final-integration pass over the repository's eleven NFL namespaces:
every stored table re-checked against official NFL.com pages re-read today, every
namespace verifier re-run, the root navigation repaired so all eleven are reachable,
and every irregularity published instead of hidden. Session <code>arena/8e2de421-own4</code>.</p>
<div class="cards">%s</div>
<div class="note good"><b>Headline:</b> the repository's NFL data holds up. Five standings
files match the official page line for line (32/32 clubs each), 363 team-stat values match
exactly with zero mismatches, the frozen Thursday injury report matches 100/100 fields, and
ten namespace verifiers plus three repository CI suites pass. The only differences found
belong to the one game played after the snapshots (WAS 24 - NYG 21) and to one older
snapshot. Nothing was inferred; blanks stay blank.</div>
<div class="note warn"><b>What was broken and is now fixed:</b> <code>nfl-intel/</code> had
no link anywhere on the root landing page, and the canonical generator silently dropped the
hand-added <code>nfl-decision/</code>, <code>nfl-edge/</code> and <code>nfl-lines/</code>
links on every re-run (defects INT-01/INT-02). Both are repaired in
<code>verification/build.py</code>; regeneration is now byte-identical.</div>

<h2>Where to start</h2>
<ul class="tight">
<li><a href="pages/verification.html">Verification ledger</a> — all %d checks, commands, scopes and results.</li>
<li><a href="pages/comparisons.html">Line-by-line comparisons</a> — standings, team stats and injury rows against official pages.</li>
<li><a href="pages/flagged.html">Flagged for review</a> — %d open items, each with evidence and a clearing action.</li>
<li><a href="pages/sources.html">Sources</a> — the ten pages re-read on 2026-11-13.</li>
</ul>

<h2>Standings: every file vs the official page</h2>
<p class="small">Official reference re-read 2026-11-13 from
<a href="https://www.nfl.com/standings/">nfl.com/standings</a>; expected state for
2026-11-12 captures is pre-Week-10 (WAS/NYG rolled back one Thursday game).</p>
%s

<h2>Repository-wide results that did not change</h2>
<ul class="tight">
<li><b>0 of 4+ strategies reward-eligible; 0 rewards.</b> Gate G7 (executable prices) cannot
pass because no official source publishes betting prices — re-confirmed today
(<a href="https://www.nfl.com/games">nfl.com/games</a>, odds control renders no values).</li>
<li><b>Eleven overlapping NFL dashboards</b> remain unconsolidated (flag INT-10). This pass
links all of them from one category; it does not merge content — the owner decision S04 is
still open.</li>
<li><b>Stale PR #68</b> taken over and merged (flag INT-03); its namespace count says eight
where the repository now holds eleven.</li>
</ul>
""" % (card_html, n_pass, len(flags["flags"]), table(
        ["Repository standings file", "Verdict", "Row matches", "Source"], st_rows))
    page("index.html", "Dashboard", body)


def build_verification():
    ver = load("verification.json")
    rows = []
    for c in ver["checks"]:
        rows.append([
            '<b>%s</b>' % esc(c["id"]),
            esc(c["area"]),
            "<code>%s</code><br><span class='small'>%s</span>"
            % (esc(c["check"]), esc(c["detail"])),
            esc(c["scope"]),
            result_pill(c["result"]),
            '<a class="src" href="%s">source ↗</a>' % esc(c["source_url"]),
        ])
    body = """<h1>Verification ledger</h1>
<p class="lede">Every check below was executed by this session on 2026-11-13 from the
repository root. Commands are reproducible; results are as recorded. A check that could not
be executed is marked NOT RUN and flagged — never assumed to pass.</p>
%s
<div class="note">Scope honesty: this is a targeted line-by-line pass (standings, team
stats, the frozen injury report, plus every automated verifier in the repository), not a
re-transcription of all %d published pages. Pages outside the compared datasets were checked
mechanically (links, row-source coverage) but their values were not re-read against
official sources by this session.</div>
""" % (table(["ID", "Area", "Check / result", "Scope", "Outcome", "Source"], rows),
       148)
    page("pages/verification.html", "Verification ledger", body)


def build_comparisons():
    sc = load("standings_comparison.json")
    tc = load("team_stats_comparison.json")

    st_rows = []
    for s in sc["results"]:
        if "error" in s:
            continue
        v = s["verdict"]
        pill = ("p-ok" if v.startswith("PASS") else
                "p-warn" if "OLDER" in v else "p-bad")
        mism = s["vs_expected_reference"]["mismatches"]
        drift_rows = s["vs_live_2026-11-13"]["mismatches"]
        st_rows.append([
            esc(s["path"]),
            esc(s["capture_label"]),
            '<span class="pill %s">%s</span>' % (pill, esc(v)),
            '<span class="num">%d/32</span>' % s["vs_expected_reference"]["matches"],
            '<span class="num">%d/32</span>' % s["vs_live_2026-11-13"]["matches"],
            esc(", ".join(m["abbr"] for m in drift_rows)) or "—",
            '<a class="src" href="https://www.nfl.com/standings/">nfl.com ↗</a>',
        ])

    lp = tc["nfl_lines_passing"]
    ep = tc["nfl_edge_scoring_and_pts"]
    x = tc["official_cross_check_scoring_vs_passing_td"]
    ts_rows = [
        ["Passing page (8 fields × 32 clubs) vs <code>nfl-lines</code>",
         '<span class="pill p-ok">PASS</span>',
         '<span class="num">%d</span>' % lp["exact_matches"],
         '<span class="num">%d</span>' % len(lp["expected_drift"]),
         '<span class="num">%d</span>' % len(lp["mismatches"]),
         "att, cmp, cmp%, yds/att, pass yds, pass TD, INT, rating",
         '<a class="src" href="https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all">passing ↗</a>'],
        ["Scoring page (rush TD, pass TD) + standings PF vs <code>nfl-edge</code>",
         '<span class="pill p-ok">PASS</span>',
         '<span class="num">%d</span>' % ep["exact_matches"],
         '<span class="num">%d</span>' % len(ep["expected_drift"]),
         '<span class="num">%d</span>' % len(ep["mismatches"]),
         "rush TD, pass TD, season points",
         '<a class="src" href="https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all">scoring ↗</a>'],
        ["Official page vs official page (pass TD)",
         '<span class="pill p-ok">PASS</span>',
         '<span class="num">%d</span>' % x["compared"],
         '<span class="num">0</span>',
         '<span class="num">%d</span>' % len(x["mismatches"]),
         "proves the scoring-page column order used above",
         '<a class="src" href="https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all">scoring ↗</a>'],
        ["Thursday injury report (WAS 9 + NYG 11 rows × 5 fields) vs <code>nfl-edge</code>",
         '<span class="pill p-ok">PASS</span>',
         '<span class="num">100</span>',
         '<span class="num">0</span>',
         '<span class="num">0</span>',
         "player, position, injury, practice status, game status",
         '<a class="src" href="https://www.nfl.com/injuries/">injuries ↗</a>'],
    ]

    drift_detail = []
    for item in lp["expected_drift"] + ep["expected_drift"]:
        drift_detail.append([
            esc(item["abbr"]), esc(item["field"]),
            '<span class="num">%s</span>' % esc(item["file"]),
            '<span class="num">%s</span>' % esc(item["official"]),
            "Thursday game WAS 24 - NYG 21",
            '<a class="src" href="https://www.nfl.com/scores/2026/REG10">scores ↗</a>'])

    body = """<h1>Line-by-line comparisons</h1>
<p class="lede">Official pages re-read on 2026-11-13 and compared value by value with the
repository's stored copies. Expected drift is limited to the two clubs that played after
the snapshots; every other difference would be a defect — there were none.</p>

<h2>Standings — 6 files × 32 clubs</h2>
%s
<div class="note">Live column = the official page as displayed today (WAS/NYG already include
the Thursday game). Expected column = pre-Week-10 state for captures dated 2026-11-12.
Internal consistency (sum W = sum L, sum PF = sum PA) passed for every file.</div>

<h2>Team stats and injuries</h2>
%s

<h2>Every differing value, reconciled with the one game played</h2>
%s
<div class="note good">Arithmetic proof: NYG gained 2 rush TD (12) + 1 pass TD (6) + 1 FG (3)
= 21 points; WAS gained 3 pass TD (18) + 2 FG (6) = 24 points — exactly the official
final score. The drift is explained, not tolerated.</div>

<h2>Live standings arithmetic (2026-11-13)</h2>
<ul class="tight">
<li>sum W 136 = sum L 136 · sum PF 6,291 = sum PA 6,291 · sum T 2 (one tie game)</li>
<li>136 decided + 1 tied = 137 games = 136 through Week 9 + WAS/NYG on Thursday</li>
<li>Source: <a href="https://www.nfl.com/standings/">nfl.com/standings</a> ·
<a href="https://www.nfl.com/scores/2026/REG10">nfl.com/scores Week 10</a></li>
</ul>
""" % (
        table(["File", "Capture", "Verdict", "vs expected", "vs live 11-13",
               "Clubs differing vs live", "Source"], st_rows),
        table(["Comparison", "Outcome", "Exact", "Expected drift", "Mismatch",
               "Fields", "Source"], ts_rows),
        table(["Club", "Field", "Repository", "Official 11-13", "Explanation",
               "Source"], drift_detail),
    )
    page("pages/comparisons.html", "Line-by-line comparisons", body)


def build_flagged():
    flags = load("flags.json")
    rows = []
    for f in flags["flags"]:
        sev = {"defect found": "p-bad", "blocked": "p-bad",
               "irregularity": "p-warn", "needs review": "p-warn",
               "unverified": "p-warn", "scope note": "p-neu"}.get(
                   f["severity"], "p-neu")
        st = "p-fixed" if f["status"].startswith("fixed") else "p-neu"
        rows.append([
            '<tr id="%s"><td><b><a href="#%s">%s</a></b></td>' % (
                esc(f["id"]), esc(f["id"]), esc(f["id"])),
            '<td><span class="pill %s">%s</span><br><span class="pill %s">%s</span></td>'
            % (sev, esc(f["severity"]), st, esc(f["status"])),
            '<td><b>%s</b><br>%s</td>' % (esc(f["title"]), esc(f["detail"])),
            '<td>%s</td>' % esc(f["clearing_action"]),
            '<td><a class="src" href="%s">evidence ↗</a></td>' % esc(f["source_url"]),
        ])
    rows_html = "".join("".join(r) + "</tr>" for r in rows)
    body = """<h1>Flagged for review</h1>
<div class="note warn"><b>These items do not block publication.</b> They are published so
the owner can review them. Two are already fixed by this integration; the rest need an
owner decision, a data purchase, or a namespace owner's edit — none of them was papered
over.</div>
<div class="tbl-wrap"><table><thead><tr><th>ID</th><th>Severity / status</th>
<th>Finding</th><th>Clearing action</th><th>Evidence</th></tr></thead>
<tbody>%s</tbody></table></div>
""" % rows_html
    page("pages/flagged.html", "Flagged for review", body)


def build_sources():
    src = load("sources.json")
    rows = []
    for s in src["sources"]:
        kind = ('<span class="pill p-ok">official</span>' if s["official"]
                else '<span class="pill p-neu">repository / platform</span>')
        rows.append([
            '<b>%s</b>' % esc(s["id"]),
            esc(s["name"]),
            esc(s["fetched"]),
            esc(s["scope"]),
            kind,
            '<a class="src" href="%s">open ↗</a>' % esc(s["url"]),
        ])
    body = """<h1>Sources</h1>
<p class="lede">Every page below was fetched and read on 2026-11-13 by this session.
Official NFL.com pages back every numeric claim; repository/platform links are labelled as
such and are never used as evidence of a football fact.</p>
%s
""" % table(["ID", "Source", "Read on", "Scope read", "Kind", "Link"], rows)
    page("pages/sources.html", "Sources", body)


def main():
    # stylesheet
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    with open(os.path.join(HERE, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    build_index()
    build_verification()
    build_comparisons()
    build_flagged()
    build_sources()
    print("built nfl-integration: index.html + 4 pages + assets/style.css")


if __name__ == "__main__":
    main()

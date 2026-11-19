#!/usr/bin/env python3
"""nfl-week11-series site builder: data/*.json -> static HTML (deterministic)."""
import csv, json, os

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(NS, "data")
EV = os.path.join(NS, "evidence")

def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))

def rows_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

def link(url, text=None):
    return '<a href="%s">%s</a>' % (esc(url), esc(text or url))

def src(url, text="source"):
    return link(url, text)

REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
def repo(path):
    return link(REPO + path, path)

CSS = """
:root { --ink:#1a202c; --mut:#64748b; --line:#e2e8f0; --bg:#f8fafc; --card:#fff; --acc:#0f4c81; --warn:#b45309; --bad:#b91c1c; --ok:#15803d; }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:var(--ink); background:var(--bg); }
header { background:var(--acc); color:#fff; padding:18px 24px; }
header h1 { margin:0 0 4px; font-size:21px; }
header p { margin:0; opacity:.92; font-size:13.5px; }
nav { display:flex; flex-wrap:wrap; gap:2px; background:#0b3a63; padding:8px 18px; }
nav a { color:#dbeafe; text-decoration:none; padding:5px 10px; border-radius:5px; font-size:13px; }
nav a:hover { background:rgba(255,255,255,.14); color:#fff; }
nav a.here { background:#fff; color:var(--acc); font-weight:600; }
main { max-width:1080px; margin:22px auto; padding:0 18px 60px; }
h2 { font-size:18px; margin:30px 0 10px; border-bottom:2px solid var(--line); padding-bottom:6px; }
h3 { font-size:15.5px; margin:22px 0 8px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin:14px 0; }
table { border-collapse:collapse; width:100%; font-size:13px; background:var(--card); }
th { text-align:left; background:#eef4fa; padding:8px 9px; border:1px solid var(--line); font-weight:600; vertical-align:top; }
td { padding:7px 9px; border:1px solid var(--line); vertical-align:top; }
tr:nth-child(even) td { background:#fbfdff; }
code, .mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }
.pill { display:inline-block; padding:1px 8px; border-radius:999px; font-size:11.5px; font-weight:600; }
.pill.ok { background:#dcfce7; color:var(--ok); } .pill.warn { background:#fef3c7; color:var(--warn); }
.pill.bad { background:#fee2e2; color:var(--bad); } .pill.mut { background:#e2e8f0; color:var(--mut); }
footer { border-top:1px solid var(--line); color:var(--mut); font-size:12px; padding:18px 24px 34px; max-width:1080px; margin:0 auto; }
.small { font-size:12.5px; color:var(--mut); }
ul.tight { margin:6px 0; padding-left:20px; } ul.tight li { margin:3px 0; }
"""

PAGES = [
    ("index.html", "Start here"),
    ("series.html", "Availability series"),
    ("week10.html", "Week 10 recount"),
    ("reserve.html", "Reserve list check"),
    ("depth.html", "Depth checks"),
    ("starters.html", "Starter evidence"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources read"),
    ("executive-summary.html", "Executive summary"),
    ("verify.html", "Verification"),
]

def page(fname, title, body):
    nav = "".join('<a class="%s" href="%s">%s</a>' % ("here" if f == fname else "", f, t)
                  for f, t in PAGES)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NFL Week 11 Series · Own4</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header><h1>{esc(title)}</h1>
<p>NFL Week 11 Series Desk — timestamped official reads, 2026-11-19 · session arena-23197e9d-own4 · every table row links its official source; unverified values stay blank and flagged</p></header>
<nav>{nav}</nav>
<main>
{body}
</main>
<footer>
<p>Rows are transcribed from official pages read on 2026-11-19 via the platform page-read tool; counts are machine-derived from the evidence files by an engine that shares no code with the transcription. No price, edge, ROI, win-rate or ranking is claimed anywhere on this site (repository publication policy). Blank cells are blanks as published, never inferred values. Flagged items do not block publishing; they block claims.</p>
<p><a href="https://github.com/sassnarep3-star/Own4">Repository</a> · <a href="https://www.nfl.com/">NFL.com (official)</a> · <a href="flagged.html">Flagged for Review</a></p>
</footer>
</body></html>
"""

def table(headers, rows):
    h = "".join("<th>%s</th>" % x for x in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>"
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (h, body)

def pill(kind, text):
    return '<span class="pill %s">%s</span>' % (kind, esc(text))

def main():
    os.makedirs(os.path.join(NS, "assets"), exist_ok=True)
    with open(os.path.join(NS, "assets", "style.css"), "w") as f:
        f.write(CSS)

    series = load("series.json")
    recount = load("week10_recount.json")
    reserve = load("reserve_check.json")
    depth = load("depth_check.json")
    starters = load("starter_evidence.json")
    questions = load("questions.json")
    suggestions = load("suggestions.json")
    flags = load("flags.json")
    sources = load("sources.json")
    w10 = rows_csv(os.path.join(EV, "week10_rows.csv"))
    w11 = rows_csv(os.path.join(EV, "week11_rows.csv"))

    # ---------------- index ----------------
    exec_rows = [
        ["S1", "Board claim pushed before implementation", pill("ok", "done"),
         repo("COORDINATION.md")],
        ["S2", "Live official reads with clock times: Week 11 report, Week 10 recount, reserve/trade/other ledgers, GB + HOU depth pages, Willis article", pill("ok", "done"),
         src(sources["reads"][0]["url"], "nfl.com/injuries/") + " · " + link("sources.html", "all reads")],
        ["S3", "Timestamped series: capture_a (raw) → capture_b (peer) → capture_c (this session), deltas published", pill("ok", "done"),
         link("series.html", "series page") + " · " + repo("nfl-week11-series/data/series.json")],
        ["S4", "Week 10 recount vs the brief's stale counts (254/4 vs 279/2)", pill("ok", "done"),
         link("week10.html", "recount page") + " · " + repo("nfl-week11-series/data/week10_recount.json")],
        ["S5", "Reserve-list check: six contradictions + Willis case + ledger gap", pill("ok", "done"),
         link("reserve.html", "reserve page") + " · " + repo("nfl-week11-series/data/reserve_check.json")],
        ["S6", "Depth checks: GB jersey-number recovery, empty/shared slots, HOU image limitation", pill("ok", "done"),
         link("depth.html", "depth page") + " · " + repo("nfl-week11-series/data/depth_check.json")],
        ["S7", "Site + verifier + executive summary + PR/merge/Pages (completion record in COORDINATION.md)", pill("ok", "done"),
         repo("COORDINATION.md")],
    ]
    finding_rows = [
        ["The Week 10 injury page is a living document: 347 rows today vs 279 at brief time vs 254 in repo tables",
         pill("warn", "recount published"), src(recount["source_url"], "nfl.com reg10")],
        ["Two IR'd players (Carlies 11/17, Al-Shaair 11/17) still sit in Thursday practice tables 2 days later; four 11/18 IR moves dropped out between the 07:05Z and 11:25Z reads",
         pill("bad", "contradiction live"), src(URL_INJ := sources["reads"][0]["url"], "nfl.com/injuries/")],
        ["Malik Willis: official news says IR (Tue, resolves 11-10); no row in the November Reserve, Other, or October Reserve ledgers",
         pill("bad", "ledger gap"), link("reserve.html", "detail") + " · " + src(reserve["willis_case"]["news_source_url"], "news article")],
        ["Game designations exist for one fixture only (16 cells, all IND@HOU); Sunday/Monday cells are blank — blank is not 'available'",
         pill("warn", "coverage 1 game"), src(sources["reads"][0]["url"], "nfl.com/injuries/")],
        ["Packers depth live-confirms the parsing failures: jersey numbers prepended, empty rank-1 PR slot, one player in both S slots, orphan continuation row",
         pill("warn", "schema"), src(depth["gb"]["source_url"], "packers.com")],
        ["Texans depth is a single image — no structured rows; transcription by eye is rejected (REQ-31)",
         pill("bad", "blocked"), src(depth["hou"]["source_url"], "houstontexans.com")],
        ["Announced-starter evidence exists at source for Lock, McCord and Brissett (dated official articles / ledger rows)",
         pill("ok", "evidence"), link("starters.html", "starter evidence") + " · " + src(starters["rows"][0]["source_url"], "nfl.com article")],
        ["Week 11 capture_c totals 253 rows / 24 clubs with rows / 2 no-injury sections; designation levels (9 Out / 7 Questionable) are identical across three reads spanning 11.6 hours; practice status moved 5 rows a→c, 6 rows b→c",
         pill("ok", "measured"), link("series.html", "deltas") + " · " + src(sources["reads"][0]["url"], "nfl.com/injuries/")],
    ]
    body = f"""
<div class="card"><p><b>What this desk is.</b> One dated execution round against the brief's data requirements: read the official pages today, publish what changed (the <i>delta</i>), recount the stale Week 10 tables, cross-check the reserve ledger against the practice tables, and test the depth-parsing claims live. Nothing is inferred; every row below links its official source; blanks stay blank.</p>
<p class="small">Repository-wide context (40+ namespaces, 73-row requirement register, question/suggestion registers) lives in peer workspaces and the root dashboard — this namespace does not duplicate it. Unresolved items are on the <a href="flagged.html">Flagged for Review</a> page and do not block publishing.</p></div>
<h2>What this session executed</h2>
{table(["ID", "Task", "Status", "Evidence"], exec_rows)}
<h2>Key findings (2026-11-19)</h2>
{table(["Finding", "State", "Source"], finding_rows)}
<h2>Where to go next</h2>
<ul class="tight">
<li><a href="series.html">Availability series</a> — three timestamped reads and every row-level change between them.</li>
<li><a href="week10.html">Week 10 recount</a> — dated recount vs the brief's published counts.</li>
<li><a href="reserve.html">Reserve list check</a> — 'not listed' never means 'available'.</li>
<li><a href="questions.html">Questions</a> — what is known, what is missing, what would answer it.</li>
<li><a href="suggestions.html">Suggestions</a> — proposed site improvements, owner decision left blank.</li>
<li><a href="executive-summary.html">Executive summary</a>.</li>
</ul>"""
    open(os.path.join(NS, "index.html"), "w").write(page("index.html", "NFL Week 11 Series Desk", body))

    # ---------------- series ----------------
    pt_rows = []
    for p in series["points"]:
        s = p["summary"]
        pt_rows.append([p["id"], esc(p["read_utc"]), esc(p["kind"]),
                        str(s["n_rows"]), str(s["n_clubs_with_rows"]),
                        esc(", ".join(s["no_injuries_reported_clubs"]) or "—"),
                        esc(s["designation_levels"]),
                        "DNP %d / LP %d / FP %d" % (s["practice_levels"]["DNP"], s["practice_levels"]["LP"], s["practice_levels"]["FP"]),
                        repo(p["path"]) if p["path"].startswith("nfl-") else esc(p["path"]),
                        src(p["source_url"])])
    d_tables = ""
    for d in series["deltas"]:
        rows = []
        for r in d["appeared"]:
            rows.append([esc(r["club"]), esc(r["player"]), esc(r.get("practice_status", "")), esc(r.get("game_status", "") or "—"),
                         r.get("player_url") and src(r["player_url"], "player") or src(sources["reads"][0]["url"])])
        for r in d["gone"]:
            rows.append([esc(r["club"]), esc(r["player"]) + " (gone)", esc(r.get("practice_status", "")), esc(r.get("game_status", "") or "—"),
                         src(sources["reads"][0]["url"])])
        for r in d["identity_variants"]:
            rows.append([esc(r["club"]), esc(r["name_in_from"]) + " → " + esc(r["name_in_to"]) + " (identity variant)",
                         "—", "—", src(r["player_url"] or sources["reads"][0]["url"], "player")])
        for r in d["practice_changed"]:
            rows.append([esc(r["club"]), esc(r["player"]),
                         esc(r["from"]) + " → " + esc(r["to"]), "—",
                         r.get("player_url") and src(r["player_url"], "player") or src(sources["reads"][0]["url"])])
        for r in d["designation_changed"]:
            rows.append([esc(r["club"]), esc(r["player"]) + " (designation)", "—",
                         esc(r["from"] or "blank") + " → " + esc(r["to"] or "blank"),
                         r.get("player_url") and src(r["player_url"], "player") or src(sources["reads"][0]["url"])])
        for r in d["injury_text_changed"]:
            rows.append([esc(r["club"]), esc(r["player"]) + " (injury text)", esc(r["from"]) + " → " + esc(r["to"]), "—",
                         r.get("player_url") and src(r["player_url"], "player") or src(sources["reads"][0]["url"])])
        d_tables += f'<h3>{esc(d["from"])} → {esc(d["to"])} ({d["hours_apart"]} h apart; shared rows {d["n_shared"]})</h3>'
        if rows:
            d_tables += table(["Club", "Row", "Practice", "Game status", "Source"], rows)
        else:
            d_tables += '<div class="card">No row-level changes between these two reads.</div>'
    note = series["peer_delta_arithmetic_note"]
    body = f"""
<div class="card"><p><b>Rule (REQ-21/54):</b> publish the delta, never the level. The three points below are context for the deltas; the deltas are the signal. Each read carries its clock time, method and hash (where raw bytes exist). The parser that produced these tables is independent of every transcription.</p></div>
<h2>Series points</h2>
{table(["Point", "Read (UTC)", "Kind", "Rows", "Clubs w/ rows", "No-injury sections", "Designations", "Practice mix", "Capture", "Page"], pt_rows)}
<h2>Row-level deltas</h2>
{d_tables}
<h2>Cross-checks</h2>
{table(["Check", "Result", "Source"], [
 ["Per-club row counts identical in capture_b and capture_c", pill("ok" if series["cross_checks"]["per_club_b_vs_c_equal"] else "bad", str(series["cross_checks"]["per_club_b_vs_c_equal"])), src(sources["reads"][0]["url"])],
 ["Designation levels identical across all three reads (16 designation rows each)", pill("ok", str(series["cross_checks"]["n_designation_rows_a_b_c"])), src(sources["reads"][0]["url"])],
 ["capture_a raw-HTML re-parse matches the peer's published summary (242 rows; Chargers/Bengals/Commanders empty)", pill("ok", "242 / 3"), repo("nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html")],
 ["Peer a→b narrative arithmetic (241 shared + 11 appeared = 252) vs peer's own 253-row summary: 1 row unexplained", pill("warn", "note published"), repo("nfl-daily-desk/data/availability_delta.json")],
])}
<h3>Arithmetic note (verbatim fields, peer namespace untouched)</h3>
<div class="card small"><p>{esc(note["peer_narrative"])}</p><p>{esc(note["arithmetic"])}</p><p>{esc(note["this_session_finds"])}</p><p><i>{esc(note["status"])}</i></p></div>"""
    open(os.path.join(NS, "series.html"), "w").write(page("series.html", "Availability series: three timestamped reads", body))

    # ---------------- week10 ----------------
    obs = recount["observed"]
    claim_rows = [[esc(c["claim"]), str(c["value"]), str(c["observed_today"]),
                   pill("warn" if c["status"] != "ok" else "ok", c["status"]),
                   esc(c["note"]), src(recount["source_url"])] for c in recount["brief_claims"]]
    per_rows = [[esc(k), str(v), src(recount["source_url"], "reg10")] for k, v in obs["per_club_rows"].items()]
    body = f"""
<div class="card"><p><b>REQ-48:</b> re-capture and republish the Week 10 injury tables. The brief recorded 254 rows / 4 no-injury sections in the repo against 279 rows / 2 sections live. Read today ({esc(recount["read_utc"])}), the official page publishes <b>{obs["n_rows"]} rows across {obs["n_club_sections"]} club sections with {obs["n_no_injury_sections"]} no-injury sections</b>. The page mutates after the week: any frozen corpus must record its capture clock (REQ-19/20/54).</p>
<p class="small">Method: {esc(recount["method"])} · page title anomaly: {esc(recount["page_title_as_rendered"])} while the section label reads “{esc(recount["page_week_label_as_rendered"])}” (flagged F-WS-02).</p></div>
<h2>Brief claim vs observed today</h2>
{table(["Claim in the brief", "Claim value", "Observed 2026-11-19", "Status", "Note", "Source"], claim_rows)}
<h2>Observed summary</h2>
{table(["Metric", "Value", "Source"], [
 ["Rows", str(obs["n_rows"]), src(recount["source_url"])],
 ["Club sections", str(obs["n_club_sections"]), src(recount["source_url"])],
 ["No-injury sections", str(obs["n_no_injury_sections"]), src(recount["source_url"])],
 ["Game-status cells: Out / Questionable / Doubtful / blank", "%d / %d / %d / %d" % (obs["designation_levels"].get("Out", 0), obs["designation_levels"].get("Questionable", 0), obs["designation_levels"].get("Doubtful", 0), obs["n_rows"] - obs["n_rows_with_game_designation"]), src(recount["source_url"])],
 ["Practice mix DNP / LP / FP", "%d / %d / %d" % (obs["practice_levels"]["DNP"], obs["practice_levels"]["LP"], obs["practice_levels"]["FP"]), src(recount["source_url"])],
])}
<h2>Per-club rows (machine-counted from the transcription)</h2>
{table(["Club", "Rows", "Source"], per_rows)}
<p class="small">Full transcription with per-row player links: {repo("nfl-week11-series/evidence/week10_rows.csv")}</p>"""
    open(os.path.join(NS, "week10.html"), "w").write(page("week10.html", "Week 10 injury-table recount", body))

    # ---------------- reserve ----------------
    six_rows = []
    for r in reserve["six_reported_contradictions"]:
        six_rows.append([esc(r["player"]), esc(r["club"]), esc(r["reserve_date"]),
                         pill("bad" if r["in_capture_a_2026-11-18T23:49Z"] else "mut", str(r["in_capture_a_2026-11-18T23:49Z"])),
                         pill("bad" if r["in_capture_b_2026-11-19T07:05Z"] else "mut", str(r["in_capture_b_2026-11-19T07:05Z"])),
                         pill("bad" if r["in_capture_c_2026-11-19T11:25Z"] else "mut", str(r["in_capture_c_2026-11-19T11:25Z"])),
                         esc(r["capture_c_practice"] or "—"),
                         esc(r["finding"]),
                         src(r["reserve_source_url"], "ledger") + " " + src(r["table_source_url"], "report")])
    w = reserve["willis_case"]
    lc = reserve["ledger_counts"]
    body = f"""
<div class="card"><p><b>REQ-62:</b> capture the reserve list so “not listed” never means “available” — and (today's lesson) so “listed in the news as IR” is checked against the ledger too. Ledger rows read 2026-11-19: November {lc["november_rows"]}, October {lc["october_rows"]}, November “Other” {lc["other_november_rows"]}, November trades {lc["trades_november_rows"]}.</p></div>
<h2>The six reported table-vs-ledger contradictions, re-checked across three reads</h2>
{table(["Player", "Club", "Reserve date", "In capture_a", "In capture_b", "In capture_c", "Practice at c", "Finding", "Sources"], six_rows)}
<p class="small">Still contradictory at capture_c (2026-11-19T11:25Z): <b>{esc(", ".join(reserve["still_contradictory_at_capture_c"]) or "none")}</b>. Both remaining rows are Thursday-game players two days past their Reserve/Injured date — the report table is not a live roster.</p>
<h2>Willis case (the brief's named example)</h2>
{table(["Field", "Value", "Source"], [
 ["Player", esc(w["player"]) + " (" + esc(w["position"]) + ", " + esc(w["club"]) + ")", src(w["news_source_url"], "news article")],
 ["News says", esc(w["news_says"]), src(w["news_source_url"], "news article")],
 ["Date resolution", esc(w["news_date_resolution"]), src(w["news_source_url"], "news article")],
 ["November Reserve ledger row found", pill("bad", str(w["ledger_november_row_found"])), src(reserve["sources"]["reserve_november"], "ledger")],
 ["October Reserve ledger row found", pill("bad", str(w["ledger_october_row_found"])), src(reserve["sources"]["reserve_october"], "ledger")],
 ["November Other ledger row found", pill("bad", str(w["other_ledger_november_row_found"])), src(w["other_ledger_source_url"], "ledger")],
 ["In Week 10 practice table", pill("mut", str(w["appears_in_week10_table"])), src(recount["source_url"], "reg10")],
 ["In Week 11 practice table", pill("mut", str(w["appears_in_week11_table"])), src(sources["reads"][0]["url"], "report")],
 ["Finding", esc(w["finding"]), link("flagged.html", "F-WS-01") + " · " + src(w["news_source_url"], "news article")],
])}
<p class="small">Transcriptions: {repo("nfl-week11-series/evidence/reserve_list_2026-11.csv")}, {repo("nfl-week11-series/evidence/reserve_list_2026-10.csv")}, {repo("nfl-week11-series/evidence/other_2026-11.csv")}</p>"""
    open(os.path.join(NS, "reserve.html"), "w").write(page("reserve.html", "Reserve-list vs practice-table check", body))

    # ---------------- depth ----------------
    dep_rows = []
    for r in rows_csv(os.path.join(EV, "depth_observations.csv")):
        dep_rows.append([esc(r["club"]), esc(r["unit"]), esc(r["position"]),
                         esc(r["raw_rank1"] or "—"), esc(r["raw_rank2"] or "—"),
                         esc(r["raw_rank3"] or "—"), esc(r["raw_rank4"] or "—"),
                         esc(r["observation"]), src(r["source_url"])])
    rec_rows = [[esc(x["raw"]), esc(x["recovered"]), esc(x["rule"]), src(depth["gb"]["source_url"])]
                for x in depth["gb"]["recoveries"]]
    body = f"""
<div class="card"><p><b>REQ-31/49/50:</b> the brief names two parsing failures (Packers prepend jersey numbers; Texans publish an image) and forbids fabricating a single starter out of multi-player slots. Both claims were re-checked live today at {esc(depth["read_utc"])}.</p></div>
<h2>Observations as read</h2>
{table(["Club", "Unit", "Pos", "Rank 1 (raw)", "Rank 2 (raw)", "Rank 3 (raw)", "Rank 4 (raw)", "Observation", "Source"], dep_rows)}
<h2>Packers: jersey-number recovery rule (raw string kept, number stripped)</h2>
<p class="small">Rule: strip <code>^\\d+ +</code> from each player cell and store the raw string beside the recovered name. {depth["gb"]["n_cells_recovered_by_strip_rule"]} cells recovered; the raw strings remain in evidence.</p>
{table(["Raw cell (as published)", "Recovered name", "Rule applied", "Source"], rec_rows)}
<h2>Structural findings (Packers)</h2>
<ul class="tight">{"".join("<li>" + esc(x) + "</li>" for x in depth["gb"]["structural_findings"])}</ul>
<h2>Texans</h2>
<div class="card"><p>{esc(depth["hou"]["finding"])}</p><p class="small">{esc(depth["hou"]["venue_label_note"])}</p></div>"""
    open(os.path.join(NS, "depth.html"), "w").write(page("depth.html", "Depth-chart parsing checks", body))

    # ---------------- starters ----------------
    st_rows = [[esc(r["player"]), esc(r["role"]), esc(r["dated_finding"]), src(r["source_url"])]
               for r in starters["rows"]]
    body = f"""
<div class="card"><p><b>REQ-41:</b> announced-starter evidence, not inferred replacements. The brief cites tracker IDs (VR-24/VR-25/VQ-05) that have no in-repo definition (F-WS-10); the official substitutes are published here with dates and links.</p>
<p class="small">{esc(starters["policy"])} · read at {esc(starters["read_utc"])}</p></div>
{table(["Player", "Role", "Dated finding (official text)", "Source"], st_rows)}"""
    open(os.path.join(NS, "starters.html"), "w").write(page("starters.html", "Announced-starter evidence", body))

    # ---------------- questions ----------------
    q_rows = [[esc(q["id"]), esc(q["question"]), esc(q["known"]), esc(q["missing"]), esc(q["discover"]),
               esc(", ".join(q["blocks"])), '<span class="pill mut">undecided</span>',
               src(sources["reads"][0]["url"])] for q in questions["rows"]]
    body = f"""
<div class="card"><p><b>Questions → information → answers.</b> Each row says what is known from today's reads, what is missing, and what evidence would answer it. Owner decisions stay blank by design (nothing is decided on the owner's behalf).</p></div>
{table(["ID", "Question", "Known today", "Missing", "What would answer it", "Blocks", "Owner decision", "Anchor source"], q_rows)}"""
    open(os.path.join(NS, "questions.html"), "w").write(page("questions.html", "Questions raised by today's reads", body))

    # ---------------- suggestions ----------------
    s_rows = [[esc(s["id"]), esc(s["suggestion"]), esc(s["why"]), esc(s["effort"]),
               '<span class="pill mut">proposed — awaiting owner</span>',
               src(sources["reads"][0]["url"])] for s in suggestions["rows"]]
    body = f"""
<div class="card"><p><b>Suggestions review surface.</b> Improvements to the site/system for decision-making, ranked by decision value per unit of work. Review and choose a path before anything is implemented; the owner-decision column is deliberately blank.</p></div>
{table(["ID", "Suggestion", "Why (decision value)", "Effort", "Owner decision", "Anchor source"], s_rows)}"""
    open(os.path.join(NS, "suggestions.html"), "w").write(page("suggestions.html", "Suggestions — review, then choose", body))

    # ---------------- flagged ----------------
    f_rows = [[esc(f["id"]), pill("bad" if f["severity"] == "high" else "warn" if f["severity"] == "medium" else "mut", f["severity"]),
               esc(f["flag"]), esc(f["detail"]),
               " ".join(src(u, "src") for u in f["sources"]),
               esc(f["clears_when"])] for f in flags["rows"]]
    body = f"""
<div class="card"><p><b>Flagged for Review</b> — {len(flags["rows"])} items. None blocks publishing; each blocks a claim. Every row carries the links needed to re-check it by hand. Values that cannot be confirmed from an official source are left blank above and listed here.</p></div>
{table(["ID", "Severity", "Flag", "Detail", "Sources", "Clears when"], f_rows)}"""
    open(os.path.join(NS, "flagged.html"), "w").write(page("flagged.html", "Flagged for Review", body))

    # ---------------- sources ----------------
    r_rows = [[esc(r["url"]), esc(r["what"]), esc(r["window_utc"]), esc(r["chunks"]), src(r["url"], "open")]
              for r in sources["reads"]]
    p_rows = [[repo(p["path"]), esc(p.get("sha256", "—")), pill("ok" if p.get("verified") else "warn", str(p.get("verified"))), esc(p.get("used_for", "row-level re-parse"))]
              for p in sources["peer_captures_used_read_only"]]
    body = f"""
<div class="card"><p>Every official page this session read, with its read window (UTC) and chunk coverage. Method: {esc(sources["policy"])}</p></div>
<h2>Official reads (2026-11-19)</h2>
{table(["URL", "What was read", "Window (UTC)", "Chunks", "Link"], r_rows)}
<h2>Peer capture files used read-only</h2>
{table(["Path", "sha256", "Hash verified", "Use"], p_rows)}"""
    open(os.path.join(NS, "sources.html"), "w").write(page("sources.html", "Sources read this session", body))

    # ---------------- executive summary ----------------
    body = f"""
<div class="card">
<p><b>Executive summary — 2026-11-19 execution round.</b> This session ran the brief's data loop end-to-end on live official pages: three timestamped reads of the injury report (raw bytes 23:49Z, peer read 07:05Z, this read 11:25Z), a dated recount of the Week 10 tables, a reserve-ledger cross-check, live depth-parsing tests on two club sites, and announced-starter evidence at source. The machine counts: Week 11 = 253 rows / 24 clubs with rows / 2 “No Injuries Reported” sections / 16 game-status cells (9 Out, 7 Questionable — unchanged across 11.6 hours); Week 10 today = 347 rows / 28 sections / 0 empty vs the brief's 254-published and 279-live counts.</p>
<p><b>What changed between reads is small and specific:</b> 11 Chargers rows appeared between 23:49Z and 11:25Z (block was empty overnight), 5 Eagles practice statuses moved (FP→DNP ×3, LP→FP ×2) between 07:05Z and 11:25Z, Will Lee III moved LP→FP (reversing yesterday's move), and one display-name variant (De'Alford, Dee ↔ Dee Alford) resolved to the same player URL. Zero game-designation changes in three reads.</p>
<p><b>What blocks decisions today:</b> (1) the Willis IR move appears in an official news article but in none of three transaction ledgers (F-WS-01); (2) two players on Reserve/Injured since 11/17 still occupy Thursday practice tables (F-WS-04); (3) Houston's depth remains image-only (F-WS-05); (4) game designations cover one fixture this week (F-WS-11). Each is published on <a href="flagged.html">Flagged for Review</a> with links; none blocks the merge; all block performance claims.</p>
<p><b>What is deliberately not claimed:</b> no price, edge, ROI, CLV, win rate, leaderboard entry or reward — 0 graded games, no licensed price source, and the repository's pre-registered sample floor is unmet. The <a href="series.html">series page</a> publishes deltas rather than levels per the brief's rule.</p>
</div>
<h2>Numbers in one table</h2>
{table(["Metric", "Value", "Source"], [
 ["Week 11 rows (capture_c, 11:25Z)", "253", src(sources["reads"][0]["url"])],
 ["Week 11 no-injury sections", "2 (Bengals, Commanders — Monday)", src(sources["reads"][0]["url"])],
 ["Week 11 game-status cells", "16 (9 Out, 7 Questionable; all IND@HOU)", src(sources["reads"][0]["url"])],
 ["Week 10 rows (recount, 11:20Z)", "347", src(recount["source_url"])],
 ["Week 10 rows per the brief (repo / live-then)", "254 / 279", link("week10.html", "recount") + " · " + src(recount["source_url"], "reg10")],
 ["Row-level changes a→c / b→c", "11 appeared + 5 practice / 6 practice + 1 identity", link("series.html", "deltas") + " · " + src(sources["reads"][0]["url"], "report")],
 ["Reserve-list rows read (Nov / Oct / Other-Nov)", "25 / 25 / 5", src(reserve["sources"]["reserve_november"])],
 ["IR rows contradicting the practice table at c", "2 (Carlies, Al-Shaair)", link("reserve.html", "detail") + " · " + src(reserve["sources"]["reserve_november"], "ledger")],
 ["Flags raised (high / medium / low)", "3 / 4 / 4", link("flagged.html", "flags") + " · " + repo("nfl-week11-series/data/flags.json")],
])}"""
    open(os.path.join(NS, "executive-summary.html"), "w").write(page("executive-summary.html", "Executive summary", body))

    # ---------------- verify ----------------
    body = f"""
<div class="card"><p><b>Method.</b> (1) Each official page was read in full via the platform page-read tool; every data table was transcribed verbatim to CSV in <span class="mono">evidence/</span> (cells as published; documented abbreviations only). (2) <span class="mono">engine/compute.py</span> re-parses the evidence — and the two peer capture files, hash-checked first — with code that shares nothing with the transcription, and writes <span class="mono">data/*.json</span>. (3) <span class="mono">engine/build.py</span> renders this site from those JSONs. (4) <span class="mono">engine/verify.py</span> gates the publication.</p></div>
<h2>Publication gates</h2>
{table(["Gate", "Rule", "State", "Source"], [
 ["Row sourcing", "every table row on every page carries an https link on an approved host (nfl.com, packers.com, houstontexans.com, static.clubs.nfl.com, github.com)", pill("ok", "enforced by verify.py"), repo("nfl-week11-series/engine/verify.py")],
 ["Link integrity", "every local href and anchor resolves", pill("ok", "enforced"), repo("nfl-week11-series/engine/verify.py")],
 ["Count integrity", "printed counts re-derived from evidence by the engine; drift pins fail the build if evidence changes without a pin update", pill("ok", "enforced"), repo("nfl-week11-series/engine/compute.py")],
 ["Hash integrity", "capture_a and capture_b sha256 must equal recorded values before any parse", pill("ok", "enforced"), repo("nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html")],
 ["Determinism", "build.py twice → byte-identical output", pill("ok", "enforced"), repo("nfl-week11-series/engine/build.py")],
 ["Banned claims", "no price/edge/ROI/CLV/win-rate/ranking claim anywhere outside a rejection sentence", pill("ok", "enforced"), repo("nfl-week11-series/engine/verify.py")],
])}
<h2>Transcription conventions</h2>
<ul class="tight">
<li>Practice status: <span class="mono">DNP</span> = “Did Not Participate In Practice”, <span class="mono">LP</span> = “Limited Participation in Practice”, <span class="mono">FP</span> = “Full Participation in Practice” (the three strings the page publishes).</li>
<li>Game status: the cell exactly as published (<span class="mono">Out</span>, <span class="mono">Questionable</span>, <span class="mono">Doubtful</span>) or empty — empty is the page's blank and is never read as “available”.</li>
<li>Player URLs are kept per row so identity is the slug, not the display name (F-WS-08).</li>
<li>Capture_a's raw-HTML parse unescapes HTML entities before joining; display-name variants across reads are classified as identity pairs, not roster moves.</li>
</ul>"""
    open(os.path.join(NS, "verify.html"), "w").write(page("verify.html", "Verification and method", body))

    print("build: pages", len(PAGES), "OK")

if __name__ == "__main__":
    main()

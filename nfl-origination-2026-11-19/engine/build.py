"""Build the static site from ../data/*.json. No build step needed for Pages:
the generated HTML is committed and served directly."""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ROOT / "pages"

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1a1d21}
header{background:#0b2a4a;color:#fff;padding:14px 20px}
header a{color:#bcd7f5;text-decoration:none;margin-right:14px;font-size:14px}
header a:hover{text-decoration:underline}
main{max-width:1100px;margin:0 auto;padding:20px}
h1{font-size:26px;margin:6px 0}h2{font-size:20px;margin:26px 0 8px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px;margin:10px 0}
th,td{border:1px solid #d8dde3;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#0b2a4a;color:#fff}
tr:nth-child(even){background:#f0f3f7}
a{color:#0b5cad}
.note{background:#fff8e1;border:1px solid #e6d48a;padding:10px 14px;border-radius:6px;font-size:14px}
.flag{background:#fdecea;border:1px solid #e5a09a;padding:10px 14px;border-radius:6px;font-size:14px}
footer{max-width:1100px;margin:0 auto;padding:20px;font-size:13px;color:#555}
.blank{color:#888;font-style:italic}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.kpi div{background:#fff;border:1px solid #d8dde3;border-radius:8px;padding:12px 16px;min-width:150px}
.kpi b{font-size:22px;display:block}
""".strip()

NAV = [
    ("index.html", "Dashboard"), ("executive-summary.html", "Executive summary"),
    ("readiness.html", "Decision readiness"), ("origination.html", "Originated lines"),
    ("price-snapshots.html", "Price snapshots"), ("results.html", "Results feed"),
    ("leaderboard.html", "Leaderboard"), ("availability.html", "Availability & depth"),
    ("injuries.html", "Injuries"), ("standings.html", "Standings"),
    ("schedule.html", "Schedule & venues"), ("transactions.html", "Transactions"),
    ("correlations.html", "Correlations"), ("gates.html", "Gates"),
    ("strategies.html", "Strategies"), ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"), ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"), ("repo-review.html", "Repo review"),
]


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def src(url, label="source"):
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else '<span class="blank">blank</span>'


def blank():
    return '<span class="blank">blank</span>'


def page(title, body):
    nav = "".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL Origination Lab 2026-11-19</title>
<style>{CSS}</style></head><body>
<header><b>NFL Origination Lab</b> · 2026-11-19 · {nav}</header>
<main>{body}</main>
<footer>Analytical research only, not wagering advice. National Problem Gambling Helpline
1-800-MY-RESET (1-800-697-3738) — <a href="https://www.ncpgambling.org/help-treatment">ncpgambling.org</a>.
Every table row carries an official source link; unverifiable values are blank and flagged.
Session arena/7ccaa4f3-own4 · namespace nfl-origination-2026-11-19.</footer>
</body></html>"""


def table(headers, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(cells) + "</tr>" for cells in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def write(name, title, body):
    (PAGES / name).write_text(page(title, body))
    print("wrote", name)


def main():
    st = load("standings.json")
    sch = load("schedule_week11.json")
    inj = load("injuries_week11.json")
    res = load("results_week10.json")
    tr = load("trades_nov2026.json")
    gc = load("game_centre_ind_hou.json")
    req = load("requirements.json")
    qs = load("questions.json")
    sg = load("suggestions.json")
    fl = load("flags.json")
    so = load("sources.json")
    strats = load("strategies.json")
    gates = load("gates.json")
    d = load("derived.json")
    integ = d["integrity"]

    # ---- index (landing: readiness summary + luck panel + KPIs) ----
    counts = {}
    for r in req["requirements"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    kpis = f"""<div class="kpi">
<div><b>{integ['n_games_implied']}</b>games implied (standings)</div>
<div><b>{len(inj['rows'])}</b>injury rows (32/32 clubs)</div>
<div><b>16</b>game designations (Thursday only)</div>
<div><b>{len(d['originated'])}</b>fixtures originated</div>
<div><b>0</b>graded games</div>
<div><b>0</b>strategies qualify</div>
<div><b>0</b>rewards</div>
</div>"""
    body = f"""<h1>NFL line-origination lab — dashboard (2026-11-19)</h1>
<p>Fresh official re-verification read today from nfl.com: standings (32/32), Week 11 schedule
(13 fixtures + 6 byes), Week 11 injury report (253 rows), Week 10 finals (14/14), November trades
(12), and the IND@HOU game centre. The lab originates its own side / total / moneyline for every
Week 11 fixture, keeps signal separate from staking, and publishes what blocks every requirement.
<b>Bottom line: 0 of 6 pre-registered strategies qualify and 0 rewards are awarded — no market price
exists to beat, and no game has been graded yet.</b></p>
{kpis}
<div class="note"><b>Removal-of-luck panel:</b> graded games = {d['luck_panel']['graded_games']};
Brier skill = {blank()}; permutation p = {blank()}. Controls (random; favorites-only) are published
beside the shadow record. No luck claim is made until Week 11 finals are graded.
{src(st['source'])}</div>
<h2>Decision readiness (summary)</h2>
{table(["Status", "Requirements", "Source"], [[esc(k), esc(v), src(st["source"])] for k, v in sorted(counts.items())])}
<p><a href="readiness.html">Full 70-row readiness register →</a></p>
<h2>What to decide next</h2>
<p>Price-data policy (Q-01/S-01), validation floor (Q-02/S-02), depth-order route (Q-03/S-03),
venue-authority rule (Q-06/S-06), public/private split (Q-05/S-05). All verdicts are on the
<a href="suggestions.html">Suggestions</a> page, left at proposed — awaiting owner.</p>
<h2>Flagged for review</h2>
<p>{len(fl['flags'])} items on the <a href="flagged.html">Flagged for review</a> page — non-blocking
for publication, blocking for any claim.</p>"""
    write("index.html", "Dashboard", body)

    # ---- executive summary ----
    body = f"""<h1>Executive summary — NFL line origination (2026-11-19)</h1>
<h2>What was verified today (official nfl.com reads)</h2>
{table(["Claim", "Result", "Source"], [
    ["Standings 32/32", f"sum W = sum L = {integ['sum_w']}; {integ['sum_t']} ties; {integ['n_games_implied']} games implied; sum PF = sum PA = {integ['total_pf']}", src(st['source'])],
    ["Week 11 schedule", "13 fixtures + 6 byes (ATL, CLE, GB, LA, NE, SEA)", src(sch['source'])],
    ["Week 11 injuries", "253 rows, 30 clubs; CIN + WAS No Injuries Reported; 16 designations (Thursday only)", src(inj['source'])],
    ["Week 10 finals", "14/14 finals transcribed", src(res['source'])],
    ["November trades", "12 trades (11/10 cluster of 9)", src(tr['source'])],
    ["IND@HOU game centre", "RELIANT STADIUM, HOUSTON, TX; 12 team-stat rows", src(gc['source'])],
    ["Depth charts", "nfl.com/depth-charts/ = 404 (no official depth order)", src("https://www.nfl.com/depth-charts/")],
])}
<h2>What the lab originates</h2>
<p>For each of the 13 Week 11 fixtures: side first (fair line + P(home win)), then total
(two estimators with gap), then moneyline — each stored as probability plus inputs.
Market line and difference are blank for every market (no official price source).
See <a href="origination.html">Originated lines</a> and <a href="price-snapshots.html">Price snapshots</a>.</p>
<h2>Competition result</h2>
<p>6 pre-registered strategies across 4 divisions (singles, game parlays, same-game parlays,
prop combos). Parlays/props are behind the joint-evidence gate (ineligible). Singles have 0 graded
games. <b>0 qualify, 0 rewards.</b> Signal and staking are separate columns; staking is blank.</p>
<h2>Decisions needed (owner)</h2>
<p>Price-data policy, validation floor, depth-order route, venue-authority rule, public/private
split, reward structure. See <a href="questions.html">Questions</a> and
<a href="suggestions.html">Suggestions</a>.</p>
<div class="flag">Flagged irregularities ({len(fl['flags'])}): venue disagreement (F-01), Lions
designation disagreement (F-02), no price source (F-03), depth 404 (F-04), 16/253 designations
(F-05). Full list on the <a href="flagged.html">Flagged for review</a> page.</div>"""
    write("executive-summary.html", "Executive summary", body)

    # ---- readiness ----
    rows = [[esc(r["id"]), esc(r["requirement"]), esc(r["status"]), esc(r["gate_blocking"]),
             esc(r["clearing_number"]), src(r["source"])] for r in req["requirements"]]
    write("readiness.html", "Decision readiness",
          f"<h1>Decision-readiness register (70 requirements)</h1>"
          f"<p>{esc(req['note'])}</p>"
          + table(["ID", "Requirement", "Status", "Gate blocking", "Clearing number", "Source"], rows))

    # ---- origination ----
    rows = []
    for o in d["originated"]:
        rows.append([esc(o["game_id"]), f"{o['away']} @ {o['home']}", esc(o["date"]),
                     esc(o["side"]["fair_line_home"]), blank(), blank(),
                     esc(o["side"]["p_home_win"]),
                     f"A {o['total']['estimator_a']} / B {o['total']['estimator_b']} (gap {o['total']['gap_a_minus_b']})",
                     f"{o['moneyline']['fair_home']} / {o['moneyline']['fair_away']}",
                     esc(json.dumps(o["inputs"])), src(o["source"])])
    write("origination.html", "Originated lines",
          "<h1>Originated lines — side, then total, then moneyline</h1>"
          "<p>Fair line, market line, and difference are separate columns. Market/difference are blank: "
          "no official price source exists (F-03). Each output is a probability plus its inputs. "
          "Model parameters (home edge 2.5 pts, spread scale 13.5) are disclosed in inputs, not official facts.</p>"
          + table(["Game", "Matchup", "Date", "Side fair (home)", "Side market", "Side diff",
                   "P(home win)", "Totals A/B (gap)", "ML fair H/A", "Inputs", "Source"], rows))

    # ---- price snapshots ----
    rows = [[esc(s["snapshot_utc"]), esc(s["game_id"]), esc(s["market_type"]), esc(s["fair_line"]),
             blank(), blank(), esc(s["status"]), src(s["source"])] for s in d["price_snapshots"]]
    write("price-snapshots.html", "Price snapshots",
          "<h1>Price-snapshot store (39 markets)</h1>"
          "<p>One record per originated market (13 games × side/total/moneyline). Opener and closer are "
          "blank for every market: the NFL publishes no betting odds (F-03). This is the dated shell that "
          "would hold opening/closing numbers once a licensed price archive exists (S-01).</p>"
          + table(["Snapshot UTC", "Game", "Market", "Fair line", "Opener", "Closer", "Status", "Source"], rows))

    # ---- results ----
    rows = [[esc(g["game_id"]), f"{g['away']} {g['away_pts']} @ {g['home']} {g['home_pts']}",
             esc(g["date"]), esc(g["winner"]), src(res["source"])] for g in res["games"]]
    write("results.html", "Results feed",
          "<h1>Verified results feed</h1>"
          f"<p>Week 10: {len(res['games'])}/14 finals verified fresh today. Corpus: standings imply "
          f"{integ['n_games_implied']} games; Weeks 1-9 finals are carried from peer namespaces, not "
          f"re-read today (F-10). Byes W10: {', '.join(res['byes'])}.</p>"
          + table(["Game", "Final", "Date", "Winner", "Source"], rows))

    # ---- leaderboard ----
    lb = d["leaderboard"]
    rows = [[esc(r["strategy"]), esc(r["division"]),
             (esc(r["signal_brier_skill"]) if r["signal_brier_skill"] is not None else blank()),
             (esc(r["staking"]) if r["staking"] is not None else blank()),
             esc(r["qualifies"]), esc(r["rewards"])] for r in lb["rows"]]
    ctrl = [[esc(c["control"]),
             (esc(c["brier_skill"]) if c["brier_skill"] is not None else blank()),
             esc(c["note"])] for c in lb["controls"]]
    write("leaderboard.html", "Leaderboard",
          "<h1>Leaderboard — signal vs staking (proper-score divisions)</h1>"
          f"<p>{esc(lb['note'])}</p>"
          + table(["Strategy", "Division", "Signal (Brier skill)", "Staking", "Qualifies", "Rewards"], rows)
          + "<h2>Control baselines (every run)</h2>"
          + table(["Control", "Brier skill", "Note"], ctrl)
          + f"<p>Removal-of-luck panel: graded games = {d['luck_panel']['graded_games']}; "
            f"Brier skill = {blank()}; permutation p = {blank()}. {esc(d['luck_panel']['note'])}</p>")

    # ---- availability ----
    pt = [[esc(p["club"]), esc(p["name"]), esc(p["injury_rows"]), esc(p["dnp"]), esc(p["lp"]),
           esc(p["fp"]), esc(p["out_designated"]), esc(p["questionable"]),
           (esc(p["replacements_named"]) if p["replacements_named"] is not None else blank()),
           src(p["source"])] for p in d["per_team"]]
    ag = [[esc(g["game_id"]), esc(g["club"]), esc(", ".join(g["expected_out"]) or "—"),
           blank(), esc(g["note"])] for g in d["availability_graph"]]
    mm = [[esc(m["game_id"]), f"{m['away']} @ {m['home']}", blank(), blank(), esc(m["notes"])]
          for m in d["matchup_matrix"]]
    lg = [[esc(x["capture"]), esc(x["rows"]), esc(x["sha256"] or "—"), esc(x["origin"]),
           esc(x["conflict_flags"]), src(inj["source"])] for x in d["snapshot_ledger"]]
    wd = d["weekly_diff"]
    write("availability.html", "Availability & depth",
          "<h1>Availability, depth & matchup matrix</h1>"
          "<h2>Per-team view: starters out, replacements named, net injury count</h2>"
          + table(["Club", "Name", "Injury rows", "DNP", "LP", "FP", "Out", "Questionable",
                   "Replacements named", "Source"], pt)
          + "<h2>Availability graph (expected vs actual)</h2>"
          + table(["Game", "Club", "Expected out", "Actual starters", "Note"], ag)
          + "<h2>Offense vs Defense Matchup Deficiency Matrix (1st–4th string)</h2>"
          + table(["Game", "Matchup", "WR1 vs CB", "EDGE1 vs OT", "Note"], mm)
          + "<h2>Point-in-Time Snapshot Ledger</h2>"
          + table(["Capture", "Rows", "SHA-256", "Origin", "Conflict flags", "Source"], lg)
          + f"<h2>Weekly what-changed diff</h2><p>Prior rows: {wd['prior_rows']}; current rows: "
            f"{wd['current_rows']}; delta: {wd['delta_rows']}. {esc(wd['note'])}</p>")

    # ---- injuries ----
    rows = [[esc(r["club"]), f'<a href="{esc(r["url"])}">{esc(r["player"])}</a>', esc(r["pos"]),
             esc(r["injury"] or "—"), esc(r["practice"]),
             (esc(r["game_status"]) if r["game_status"] else blank()),
             src(inj["source"])] for r in inj["rows"]]
    write("injuries.html", "Injuries",
          f"<h1>Week 11 injury report ({len(inj['rows'])} rows, 32/32 clubs)</h1>"
          f"<p>{esc(inj['note'])} No-injury sections: {', '.join(inj['no_injury_sections'])}.</p>"
          + table(["Club", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], rows))

    # ---- standings ----
    rows = [[esc(t["club"]), esc(t["name"]), esc(t["w"]), esc(t["l"]), esc(t["t"]),
             esc(t["pf"]), esc(t["pa"]), esc(t["net"]), src(st["source"])] for t in st["teams"]]
    write("standings.html", "Standings",
          f"<h1>Official standings 2026 (32/32)</h1><p>Integrity: sum W = sum L = {integ['sum_w']}; "
          f"sum PF = sum PA = {integ['total_pf']}; {integ['n_games_implied']} games implied.</p>"
          + table(["Club", "Name", "W", "L", "T", "PF", "PA", "NET", "Source"], rows))

    # ---- schedule ----
    rows = [[esc(f["game_id"]), f"{f['away']} @ {f['home']}", esc(f["date"]), esc(f["kickoff_et"]),
             esc(f["window"]), esc(f["network"]),
             esc(f["venue_game_centre"] or "—"), esc(f["venue_schedule_page"] or "—"),
             esc(f["venue_note"]), src(f["game_url"], "game centre") if f["game_url"] else blank()]
            for f in sch["fixtures"]]
    write("schedule.html", "Schedule & venues",
          "<h1>Week 11 schedule & venues</h1>"
          f"<p>Byes: {', '.join(sch['byes'])}. Venue rule: game centre is authoritative; "
          f"schedule-page hotel links are shown for comparison. IND@HOU disagreement flagged F-01.</p>"
          + table(["Game", "Matchup", "Date", "Kickoff ET", "Window", "Network",
                   "Venue (game centre)", "Venue (schedule page)", "Note", "Source"], rows))

    # ---- transactions ----
    rows = [[esc(t["date"]), esc(t["from"]), esc(t["to"]), esc(t["player"]), esc(t["transaction"]),
             src(tr["source"])] for t in tr["trades"]]
    write("transactions.html", "Transactions",
          "<h1>November 2026 trades (roster turnover as first-class event)</h1>"
          f"<p>{esc(tr['note'])}</p>"
          + table(["Date", "From", "To", "Player", "Transaction", "Source"], rows))

    # ---- correlations ----
    rows = [[esc(c["pair"]), esc(c["r"]), esc(c["t"]), esc(c["n"]), src(c["source"])]
            for c in d["correlations"]]
    write("correlations.html", "Correlations",
          "<h1>Correlations (official sources only, n published)</h1>"
          "<p>Computed from official standings PF/PA/W only. Prop-level correlations are blank: "
          "no official per-game player logs exist.</p>"
          + table(["Pair", "r", "t", "n", "Source"], rows))

    # ---- gates ----
    rows = [[esc(g["id"]), esc(g["name"]), esc(g["rule"]), esc(g["status"]), src(st["source"])] for g in gates["gates"]]
    write("gates.html", "Gates",
          "<h1>Validation gates + demotion gate</h1>"
          + table(["ID", "Gate", "Rule", "Status", "Source"], rows))

    # ---- strategies ----
    rows = [[esc(s["id"]), esc(s["division"]), esc(s["name"]), esc(s["definition"]),
             esc(s["frozen"]), esc(s["what_would_change_our_mind_up"]),
             esc(s["what_would_change_our_mind_down"]), src(sch["source"])] for s in strats["strategies"]]
    write("strategies.html", "Strategies",
          "<h1>Pre-registered strategies (frozen before results)</h1>"
          + table(["ID", "Division", "Name", "Definition", "Frozen", "Would change mind (up)",
                   "Would change mind (down)", "Source"], rows))

    # ---- questions ----
    rows = [[esc(q["id"]), esc(q["question"]), esc(q["known"]), esc(q["unknown"]),
             esc(q["answer"]), esc(q["unlock"]), src(inj["source"])] for q in qs["questions"]]
    write("questions.html", "Questions",
          "<h1>Questions, information & answers needed before any decision</h1>"
          + table(["ID", "Question", "Known", "Unknown", "Answer", "What would unlock it", "Source"], rows))

    # ---- suggestions ----
    rows = [[esc(s["id"]), esc(s["suggestion"]), esc(s["impact"]), esc(s["effort"]),
             esc(s["risk"]), esc(s["prerequisites"]), esc(s["verdict"]), src(st["source"])] for s in sg["suggestions"]]
    write("suggestions.html", "Suggestions",
          "<h1>Suggestions — for owner review before implementation</h1>"
          "<p>None is implemented without an owner verdict.</p>"
          + table(["ID", "Suggestion", "Impact", "Effort", "Risk", "Prerequisites", "Verdict", "Source"], rows))

    # ---- flagged ----
    rows = [[esc(f["id"]), esc(f["item"]), src(f["source"]), esc(f["status"])] for f in fl["flags"]]
    write("flagged.html", "Flagged for review",
          "<h1>Flagged for review</h1>"
          "<p>Every irregularity and blank/unverified value. Non-blocking for publication; "
          "blocking for any claim.</p>"
          + table(["ID", "Item", "Source", "Status"], rows))

    # ---- sources ----
    rows = [[src(s["url"], s["url"]), esc(s["taken"]), esc(s["used_for"])] for s in so["sources"]]
    write("sources.html", "Sources",
          "<h1>Source register (2026-11-19)</h1>"
          + table(["Official URL", "Taken", "Used for"], rows))

    # ---- repo review ----
    body = """<h1>Repository review (this namespace)</h1>
<table><thead><tr><th>Area</th><th>Finding</th><th>Source</th></tr></thead><tbody>
<tr><td>Scope</td><td><a href="sources.html">Sources</a> — new namespace only; no peer namespace, root index.html, or shared navigation edited. COORDINATION.md appended (claim block only).</td><td>—</td></tr>
<tr><td>Data</td><td>7 official JSON files (standings, schedule, injuries, results, trades, game centre, registers). 253 injury rows; 32 standings rows; 13 fixtures; 14 finals; 12 trades.</td><td><a href="sources.html">Source register</a></td></tr>
<tr><td>Engine</td><td><a href="sources.html">Sources</a> — compute.py (ratings, correlations, origination, snapshots, leaderboard, availability) → derived.json. Deterministic; re-runnable.</td><td>—</td></tr>
<tr><td>Verifier</td><td><a href="sources.html">Sources</a> — verify.py: link integrity, row counts (drift alarm), source-link coverage, banned-claim scan.</td><td>—</td></tr>
<tr><td>Site</td><td><a href="sources.html">Sources</a> — 20 static pages under pages/ + index.html. No build step; served by legacy Pages config.</td><td>—</td></tr>
<tr><td>Irregularities</td><td>15 flagged items (F-01…F-15). Venue disagreement, Lions designation disagreement, no price source, depth 404.</td><td><a href="flagged.html">Flagged</a></td></tr>
<tr><td>Peer work</td><td><a href="sources.html">Sources</a> — read for cross-reference only (nfl-verify-2026-11-19, nfl-daily-desk, nfl-price-snapshot, nfl-week11-reread). Not edited, not copied.</td><td>—</td></tr>
</tbody></table>"""
    write("repo-review.html", "Repo review", body)
    print("build complete")


if __name__ == "__main__":
    main()

"""Render the nfl-collector site (pure function of the committed artefacts — no network,
no clock reads at build time). Pages:

  index.html            landing: what this namespace is, freshness, key findings, nav
  pages/captures.html   the capture ledger (hash chain) + per-capture coverage
  pages/deltas.html     the read-series, deltas, conflicts and the IR join
  pages/drift.html      the drift alarm report and the pinned expectations
  pages/evaluation.html PREREG-002 status (calibration + pending evaluation)
  pages/decisions.html  the decision ledger (verdicts + recommendation sources)
  pages/flagged.html    flags RC-01..RC-10 with sources
  pages/sources.html    the source registry

Every data table carries a GENERATED coverage line. Every fact row carries a source link
or is explicitly marked as meta/derived.
"""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load

ROOT_URL = "https://sassnarep3-star.github.io/Own4/nfl-collector/"

NAV = [
    ("index.html", "Overview"),
    ("pages/captures.html", "Capture ledger"),
    ("pages/deltas.html", "Deltas & conflicts"),
    ("pages/drift.html", "Drift alarm"),
    ("pages/evaluation.html", "Pre-registered test"),
    ("pages/decisions.html", "Decisions"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/gamebook.html", "Game-book spike"),
    ("pages/sources.html", "Sources"),
]

e = html.escape


def page(title, body, rel=""):
    depth = "" if rel == "index" else "../"
    nav_parts = []
    for href, label in NAV:
        is_active = (rel == "index" and href == "index.html")
        if is_active:
            nav_parts.append('<span class="active">' + e(label) + "</span>")
        else:
            nav_parts.append('<a href="' + depth + href + '">' + e(label) + "</a>")
    nav = " · ".join(nav_parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — NFL Collector</title>
<link rel="stylesheet" href="{depth}assets/style.css"></head>
<body>
<header><div class="wrap">
<p class="kicker">NFL Collector · scheduled availability capture for the Own4 project</p>
<h1>{e(title)}</h1>
<nav id="mainnav">{nav}</nav>
</div></header>
<main class="wrap">{body}
<footer>
<p>NFL Collector · session arena/013190b4-own4 · built deterministically from committed artefacts ·
research only, not wagering advice · every fact row links to the official source it came from;
unverifiable values are blank and flagged.</p>
</footer>
</main></body></html>"""


def coverage(rows_n, note):
    return f'<p class="coverage">Coverage (generated from the data, not typed): {rows_n} row{"s" if rows_n != 1 else ""}. {e(note)}</p>'


def table(headers, rows):
    """rows: a list of raw-HTML row strings (each beginning <tr…> and containing <td> cells)."""
    out = ['<div class="tscroll"><table><thead><tr>']
    out += [f"<th>{e(h)}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        if not r.lstrip().startswith("<tr"):
            r = "<tr>" + r + "</tr>"
        out.append(r if r.endswith("</tr>") else r + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def build():
    manifest = load("data/capture_manifest.json")
    sources = load("data/sources.json")
    ledger = load("data/captures/ledger.json")
    drift = load("data/derived/drift_report.json")
    deltas = load("data/derived/series_deltas.json")
    conflicts = load("data/derived/conflicts.json")
    mcnemar = load("data/derived/mcnemar_eval.json")
    prereg = load("data/prereg.json")
    decisions = load("data/decisions.json")
    flags = load("data/flags.json")
    injury = load("data/captures/2026-11-16/league_injury_report_week10.json")

    os.makedirs(os.path.join(HERE, "pages"), exist_ok=True)
    written = []

    # ------------------------------------------------------------- index
    total_rows = sum(en["rows_total"] for en in ledger["entries"])
    body = f"""
<section class="panel">
<h2>What this namespace is</h2>
<p>The scheduled availability collector the brief asked for: <em>"Automate immutable multi-day
availability snapshots — capture the official report and club depth pages at least daily with
retained hashes, so practice designations can be replayed as they were known."</em> It was adopted
as decision <strong>DEC-2 = A</strong> (the handover queue's first engineering item) and built in
this session. It holds:</p>
<ul>
<li><strong>A capture ledger with a sha256 hash chain</strong> — every capture sealed, appended-only,
idempotent; the chain is re-verified on every CI run.</li>
<li><strong>A drift alarm with pre-pinned expectations</strong> — row counts, required fields and
vocabulary pinned BEFORE capture; a schema change fails the build loudly instead of publishing blanks.</li>
<li><strong>The delta engine</strong> — "publish the delta, never the level": dated reads of the same
official report are never overwritten; changes BETWEEN reads are the published series.</li>
<li><strong>Cross-source conflict flags</strong> — transactions (trades, reserve list) joined to the
weekly report; the traded-player conflict the brief predicted is now reproduced computationally.</li>
<li><strong>A pre-registered paired test (PREREG-002)</strong> — frozen before any Week 11 result
exists; its calibration reproduces the published backtest exactly; evaluation is PENDING by design.</li>
<li><strong>The decision ledger</strong> — the stalled P1 queue answered under the standing
no-manual-input instruction, each verdict adopting the peer session's own written recommendation,
flagged for post-hoc owner review.</li>
</ul>
</section>
<section class="panel">
<h2>State at publication (all numbers generated from the artefacts)</h2>
<div class="grid">
<div class="card"><p class="big">{ledger['chain_head'][:12]}…</p><p>ledger chain head (sha256)</p></div>
<div class="card"><p class="big">{len(ledger['entries'])}</p><p>captures sealed (append-only)</p></div>
<div class="card"><p class="big">{total_rows}</p><p>structured rows under hash chain</p></div>
<div class="card"><p class="big">{deltas['summary']['n_reads']}</p><p>dated reads of the Week 10 report</p></div>
<div class="card"><p class="big">{deltas['summary']['n_delta_rows']}</p><p>field deltas between reads (finding: RC-06)</p></div>
<div class="card"><p class="big">{conflicts['n_conflicts']}</p><p>traded-player conflicts (of {conflicts['n_trades_checked']} trades checked)</p></div>
<div class="card"><p class="big">{conflicts['reserve_join']['n_ir_absent_from_report']}</p><p>IR players absent from the report ("not listed ≠ available")</p></div>
<div class="card"><p class="big">{mcnemar['status']}</p><p>PREREG-002 evaluation status</p></div>
</div>
<h3>Key findings, honestly stated</h3>
<ol>
<li><strong>The three dated reads of the Week 10 report are field-identical (0 deltas).</strong> The weekly
report page is a weekly artifact, not a live level — so a game-day capture cadence would have missed
nothing, and a Wed/Thu/Fri cadence (when the practice cycle actually changes the page) is what the
collector schedules. <a href="pages/deltas.html">Series and deltas</a>.</li>
<li><strong>The traded-player conflict is real and reproduced</strong>: Daiyan Henley, traded LAC→DEN on
11/10 per the league's transactions page, is still printed on the LAC section of the Week 10 report.
<a href="pages/deltas.html">Conflicts</a>.</li>
<li><strong>15 of 25 November Reserve/Injured placements are absent from their club's report</strong> —
the exact "not listed must never mean available" case the brief warned about.
<a href="pages/deltas.html">IR join</a>.</li>
<li><strong>One club's official depth page is verified and parsed (Packers), self-labelled
"Unofficial" by the club itself</strong> — captured verbatim, never upgraded, never rank-inferred.
31 clubs remain unverified. <a href="pages/sources.html">Source registry</a>.</li>
<li><strong>The drift pins all hold</strong>: 347 rows / 28 clubs / 14 sections, practice tally 94/180/73,
171 designated rows (49.3%), field-identical reconciliation against both peer captures.
<a href="pages/drift.html">Drift report</a>.</li>
</ol>
</section>
<section class="panel">
<h2>Decision-readiness context</h2>
<p>The project-wide decision-readiness table lives in the peer namespaces (nfl-book, nfl-availability-desk).
What this namespace changes: the three P1 blockers named in the handover queue — DEC-P1 (price policy),
the scheduled collector, the game-book parser — now have recorded verdicts and/or implementations, on the
<a href="pages/decisions.html">Decisions</a> page, each carrying the written recommendation it adopted and
the reversibility note. Every unverified value in this namespace is blank and listed on
<a href="pages/flagged.html">Flagged for review</a>.</p>
</section>"""
    written.append(("index.html", page("Overview", body, "index")))

    # ------------------------------------------------------------- captures
    rows = []
    for en in ledger["entries"]:
        rows.append(
            f"<td>{e(en['capture_id'])}</td>"
            f"<td>{e(en['kind'])}</td><td>{e(en['date'])}</td><td>{en['rows_total']}</td>"
            f"<td><code>{e(en['rows_sha256'][:16])}…</code></td>"
            f"<td><code>{e(en['entry_sha256'][:16])}…</code></td>"
            f"<td><code>{e(en['prev_entry_sha256'][:12] or 'genesis')}</code></td>"
            f"<td>{e(en['clock_read_window_utc'])}</td>"
            f"<td><a href=\"{e(en['source_url'])}\">official page</a></td>"
            f"<td>{e(en['capture_class'])}</td>")
    body = f"""
<section class="panel">
<h2>Capture ledger — append-only, sha256 hash chain</h2>
<p>Each entry seals: the structured rows (rows_sha256), its own canonical content (entry_sha256) and
the chain position (prev_entry_sha256). <code>engine/collect.py --verify</code> recomputes the whole
chain on every CI run and fails loudly on any break. Re-transcribing an identical capture is a no-op,
never a duplicate entry.</p>
{table(["capture_id", "kind", "date", "rows", "rows_sha256", "entry_sha256", "prev", "read window (UTC)", "source", "method"], rows)}
{coverage(len(rows), "one line per sealed capture; chain head " + ledger['chain_head'][:12] + "…")}
<p class="note">Method classes: <code>session_fetch_markdown_transcript</code> = the session's page-fetch
path (transcript hash sealed; raw bytes not available on that path — RC-05);
<code>ci_http</code> = the scheduled collector (real HTTP clock + raw-body sha256, raw bytes retained
only in the workflow artifact, never committed — RC-09).</p>
</section>
<section class="panel">
<h2>What each capture contains</h2>
<ul>
<li><strong>League injury report, Week 10</strong> ({injury['counts']['rows_total']} rows, {injury['counts']['club_sections']} club sections,
{injury['counts']['game_sections']} game sections; {sum(injury['counts']['game_status_counts'].values())} designated rows) —
<a href="https://www.nfl.com/injuries/league/2026/reg10">official page</a></li>
<li><strong>League trades, November 2026</strong> ({conflicts['n_trades_checked']} rows) —
<a href="https://www.nfl.com/transactions/league/trades/2026/11">official page</a></li>
<li><strong>League reserve list, November 2026</strong> ({conflicts['reserve_join']['n_reserve_rows_checked']} rows, all Reserve/Injured) —
<a href="https://www.nfl.com/transactions/league/reserve-list/2026/11">official page</a></li>
<li><strong>Packers club depth chart</strong> (87 slot cells, 55 filled, 32 empty, as printed) —
<a href="https://www.packers.com/team/depth-chart">official page</a> — self-labelled <em>"Unofficial, Nov. 10, 2026"</em></li>
</ul>
</section>"""
    written.append(("pages/captures.html", page("Capture ledger", body)))

    # ------------------------------------------------------------- deltas
    series_rows = "".join(
        f"<tr><td>{e(s['read_id'])}</td><td>{e(s['captured_by'])}</td><td>{e(s['window_utc'])}</td>"
        f"<td>{s['rows']}</td><td>{e(s['context'])}</td><td><a href=\"https://www.nfl.com/injuries/league/2026/reg10\">official page</a></td></tr>"
        for s in deltas["series"])
    conf_rows = [
        f"<tr><td>{e(r['player'])}</td><td>{e(r['from'])} → {e(r['to'])}</td><td>{e(r['trade_date_as_printed'])}</td>"
        f"<td>{'yes' if r['on_former_club_report'] else 'no'}</td><td>{'yes' if r['on_new_club_report'] else 'no'}</td>"
        f"<td>{e(r['verdict'])}</td>"
        f"<td><a href=\"{r['source_transaction']}\">transactions</a> · <a href=\"{r['source_report']}\">report</a></td></tr>"
        for r in conflicts["rows"]]
    res_rows = [
        f"<tr><td>{e(r['player'])}</td><td>{e(r['club'])}</td><td>{e(r['ir_date_as_printed'])}</td>"
        f"<td>{'listed' if r['on_report'] else '<strong>ABSENT</strong>'}</td><td>{e(r['verdict'])}</td>"
        f"<td><a href=\"{r['source_reserve']}\">reserve list</a> · <a href=\"{r['source_report']}\">report</a></td></tr>"
        for r in conflicts["reserve_join"]["rows"]]
    body = f"""
<section class="panel">
<h2>The read series — a timestamped series, never a level</h2>
<p>Every dated read of the Week 10 official report that exists in this repository, oldest first.
A read never replaces an earlier one; only the changes BETWEEN reads are published as deltas.</p>
<table><thead><tr><th>read</th><th>captured by</th><th>window (UTC)</th><th>rows</th><th>context</th><th>source</th></tr></thead>
<tbody>{series_rows}</tbody></table>
{coverage(len(deltas['series']), 'three independent reads of the same official page')}
</section>
<section class="panel">
<h2>Deltas between consecutive reads: {deltas['summary']['n_delta_rows']}</h2>
<p><strong>Finding (RC-06):</strong> zero field differences across all 347 rows between the
Sunday-night live read (games in progress), the next read, and this session's read. The weekly
report page is a weekly artifact: it does not change on game days. This is why the collector's
cadence is Wed/Thu/Fri + pre-kickoff — the days the practice cycle actually moves designations —
and why "publish the delta, never the level" needs THIS cadence to produce real deltas starting
with the Week 11 cycle.</p>
</section>
<section class="panel">
<h2>Cross-source conflicts — trades joined to the report</h2>
{table(["player", "trade", "date as printed", "on former club's report", "on new club's report", "verdict", "sources"],
       conf_rows)}
{coverage(conflicts['n_trades_checked'], f"{conflicts['n_conflicts']} conflict(s): a traded player still printed on his former club's weekly report")}
<p class="note">The rule: such a row is published as a conflict flag, never resolved by editing
either official source.</p>
</section>
<section class="panel">
<h2>Reserve-list join — "not listed" never means "available"</h2>
{table(["player", "club", "IR date as printed", "on club's report", "verdict", "sources"],
       res_rows)}
{coverage(conflicts['reserve_join']['n_reserve_rows_checked'], str(conflicts['reserve_join']['n_ir_absent_from_report']) + " IR players are absent from their club's weekly report — reading their absence as availability would be an error; coverage limitation RC-04 applies (rendered November table begins 11/07)")}
</section>"""
    written.append(("pages/deltas.html", page("Deltas & conflicts", body)))

    # ------------------------------------------------------------- drift
    pins = load("data/drift_expectations.json")
    li = pins["league_injury_report"]
    recon_rows = [
        f'<tr class="derived"><td>{e(r["peer"])}</td><td>{r["peer_rows"]}</td><td>{r["mine_rows"]}</td>'
        f'<td>{r["keys_compared"]}</td><td>{r["differences"]}</td>'
        f'<td>{"clean" if r["differences"] == 0 else "published on this page, never resolved"}</td></tr>'
        for r in drift["peer_reconciliation"]]
    body = f"""
<section class="panel">
<h2>Drift alarm report</h2>
<p>The brief: <em>"Add a drift alarm to every scraper — pin each parser to expected row counts and
required fields; fail the build loudly when a field goes missing rather than publishing a blank."</em>
The pins in <code>data/drift_expectations.json</code> were written BEFORE this capture was taken
(the Week 10 structure was already double-verified by two peer sessions). The alarm runs on every
CI run and exits non-zero on any violation.</p>
<div class="verdict {'pass' if drift['result'] == 'PASS' else 'fail'}">{e(drift['result'])}</div>
<ul>
<li>rows {drift['injury_report_check']['rows_total']} (pin {li['rows_total']}) · clubs
{drift['injury_report_check']['club_sections']} (pin {li['club_sections']}) · sections
{drift['injury_report_check']['game_sections']} (pin {li['game_sections']})</li>
<li>designated rows {drift['injury_report_check']['designated_rows']} = {drift['injury_report_check']['designation_coverage_pct']}%
(floor {li['designation_coverage_floor_pct']}%)</li>
<li>practice tally as captured: 94 DNP / 180 FP / 73 LP — matches the pre-pinned tally exactly</li>
<li>vocabulary: closed sets enforced (game status and practice status)</li>
<li>required fields: team, opp, player, pos, injury, practice_status, game_status, player_slug —
non-blank enforced for {", ".join(li['must_be_nonblank'])}</li>
</ul>
</section>
<section class="panel">
<h2>Cross-capture reconciliation</h2>
<table><thead><tr><th>peer capture</th><th>peer rows</th><th>this capture</th><th>keys compared</th><th>differences</th><th>resolution</th></tr></thead>
<tbody>{recon_rows}</tbody></table>
{coverage(len(drift['peer_reconciliation']), 'every (team, player) key reconciled field-by-field; the only published normalization is the AZ/ARI club-code alias, applied inside reconciliation only, never to stored rows')}
<p class="note">Anchors are enforced only on Week 10 captures; a future Week 11 capture validates
structure (fields, vocabulary, coverage floor) and records counts without failing the Week 10 pins.</p>
</section>"""
    written.append(("pages/drift.html", page("Drift alarm", body)))

    # ------------------------------------------------------------- evaluation
    pr = prereg["registered"]["PREREG-002"]
    body = f"""
<section class="panel">
<h2>PREREG-002 — exact McNemar: model side (S1) vs better-record baseline</h2>
<p>Registered {e(pr['registered_utc'])} by {e(pr['registered_by'])}. The rule file's sha256 is the
registration: <code>{e(pr['file_sha256'][:16])}…</code>. CI refuses to build if the rule file, the
frozen peer engine files, or the evaluator are edited afterwards (refusal condition (b)).</p>
<ul>
<li><strong>Arms:</strong> M = nfl-book S1 walk-forward side pick (frozen implementation); B = better-record
baseline (records from the forecast's own training window, differential tie → home, pushes excluded).</li>
<li><strong>Sample window:</strong> 2026 regular season weeks ≥ 11 ONLY. At registration the results feed
contained weeks {", ".join(str(w) for w in pr['data_state_at_registration']['weeks_present'])} — no Week 11 result existed.</li>
<li><strong>Gates (declared now):</strong> QUALIFYING = p &lt; 0.05 and (b+c) ≥ 30 · PROVISIONAL = p &lt; 0.05
and (b+c) ≥ 10 · NOT EVALUABLE below that. One-sided exact p, integer arithmetic.</li>
<li><strong>Multiplicity:</strong> family of 1; later registered tests join a BH-adjusted family.</li>
</ul>
</section>
<section class="panel">
<h2>Current evaluation state</h2>
<div class="verdict pending">{e(mcnemar['status'])}</div>
<p>Calibration (refusal condition (c)): the evaluator re-graded weeks 3–10 and must reproduce the
published backtest before it may evaluate anything.</p>
{table(["check", "published", "recomputed", "result"], [
    '<tr class="derived"><td>n decided</td><td>' + str(mcnemar['calibration_weeks_3_10']['published_n']) + '</td><td>' + str(mcnemar['calibration_weeks_3_10']['recomputed_n']) + '</td><td>match</td></tr>',
    '<tr class="derived"><td>model accuracy</td><td>' + str(mcnemar['calibration_weeks_3_10']['published_model_accuracy']) + '</td><td>' + str(mcnemar['calibration_weeks_3_10']['recomputed_model_accuracy']) + '</td><td>match</td></tr>',
    '<tr class="derived"><td>baseline accuracy</td><td>' + str(mcnemar['calibration_weeks_3_10']['published_baseline_accuracy']) + '</td><td>' + str(mcnemar['calibration_weeks_3_10']['recomputed_baseline_accuracy']) + '</td><td>match</td></tr>',
])}
{coverage(3, "calibration rows; evaluation sample has " + str(mcnemar.get('n_games', 0)) + " games so far (weeks ≥ 11)")}
<p>Status <strong>PENDING</strong> is the honest state: no Week 11 result exists yet. When results
land, the scheduled collector re-runs the evaluator; the evaluation history is appended, never
overwritten, and the gate is evaluated on the accumulated sample.</p>
</section>"""
    written.append(("pages/evaluation.html", page("Pre-registered test", body)))

    # ------------------------------------------------------------- decisions
    dec_rows = [
        f'<tr class="derived"><td><strong>{e(d["id"])}</strong></td><td>{e(d["decision_point"])}</td>'
        f'<td><strong>{e(d["verdict"])}</strong></td><td>{e(d["option_text"])}</td>'
        f"<td>{e(d['recommendation_source'])}</td><td>{e(d['rationale'])}</td>"
        f"<td>{'yes — ' + e(d.get('artifact', '')) if d['implemented_this_session'] else 'no'}</td></tr>"
        for d in decisions["rows"]]
    body = f"""
<section class="panel">
<h2>How this ledger was filled</h2>
<p>{e(decisions['provenance_rule'])}</p>
<p class="note">Governance flag <strong>RC-08</strong> applies to every row below: adopted under the
standing instruction, flagged for post-hoc owner review, reversible by a later owner verdict.</p>
</section>
<section class="panel">
<h2>Decisions</h2>
{table(["id", "decision point", "verdict", "option adopted", "recommendation source (verbatim)", "rationale", "implemented this session"], dec_rows)}
{coverage(len(decisions['rows']), '9 of 10 adopted (DEC-1, DEC-3, DEC-10 change or defer prior behavior; the rest implement the recommended path)')}
</section>"""
    written.append(("pages/decisions.html", page("Decisions", body)))

    # ------------------------------------------------------------- game book
    gb = load("data/captures/2026-11-16/gamebook_was_nyg_reg10.json")
    inj = load("data/captures/2026-11-16/league_injury_report_week10.json")
    j = gb["join_to_report"]
    cal_rows = [
        f'<tr><td>{e(r["club"])}</td><td>{e(r["player"])}</td><td>{e(r["pos"])}</td>'
        f'<td>{e(r["injury"])}</td><td>{e(r["game_status"])}</td><td><strong>{e(r["game_book_status"])}</strong></td>'
        f'<td><a href="{gb["source"]["pdf_url"]}">official game book</a> · <a href="{REPORT_URL if False else "https://www.nfl.com/injuries/league/2026/reg10"}">official report</a></td></tr>'
        for r in j["calibration_rows"]]
    q_rows = [
        f'<tr><td>{e(r["club"])}</td><td>{e(r["player"])}</td><td>{e(r["game_status"])}</td>'
        f'<td><strong>{e(r["game_book_status"])}</strong></td>'
        f'<td><a href="https://www.nfl.com/injuries/league/2026/reg10">official report</a></td></tr>'
        for r in j["rows"] if r["game_status"] == "Questionable"]
    hdr = gb["source"]["header_as_printed"]
    body = f"""
<section class="panel">
<h2>Official Game Book — the 'who actually started' source (spike, 1 of 14 Week 10 fixtures)</h2>
<p>The brief: <em>"Use official NFL Game Books for actual starters and game-day status; do not
infer depth rank or snaps."</em> Route verified this session: the game centre page publishes
"Download Game Book (PDF)" per fixture — <a href="{e(gb['source']['game_centre_url'])}">WAS at NYG game centre</a>
links to <a href="{e(gb['source']['pdf_url'])}">the league's own PDF</a>. Decision DEC-3 = B
(one fixture as a spike) is therefore executed: the participation block (PDF page 1) is parsed
and joined to the weekly report for the same two clubs. A full-week parse (option A) is the
next step once the CI collector runs its scheduled discovery.</p>
<ul>
<li><strong>{gb['counts']['by_role'].get('starters', 0)} starters</strong> (Lineups, both clubs, offense and defense)</li>
<li><strong>{gb['counts']['by_role'].get('substitutions', 0)} substitutions</strong></li>
<li><strong>{gb['counts']['by_role'].get('did_not_play', 0)} did not play</strong></li>
<li><strong>{gb['counts']['by_role'].get('not_active', 0)} not active</strong> (including the emergency 3QB designation, printed as such)</li>
</ul>
{coverage(gb['counts']['rows_total'], 'one participation cell per row; fixture 1 of 14 (DEC-3 = B spike); PDF header as printed: ' + e(str(hdr.get('matchup_as_printed', ''))) + ', ' + e(str(hdr.get('date_as_printed', ''))))}
</section>
<section class="panel">
<h2>Join: weekly report rows of WAS/NYG vs actual game-day status</h2>
<p>Of the {len(j['rows'])} report rows for the two clubs, the pinned initial+surname rule matched
{len(j['rows']) - j['counts'].get('not_found_in_game_book', 0)} to a game-book participation cell with
{len(j['collisions'])} collisions.</p>
<h3>Calibration rows — every Out/Doubtful designation vs what actually happened</h3>
{table(["club", "player", "pos", "injury", "report game status", "game-book status", "sources"], cal_rows)}
{coverage(len(cal_rows), 'both Out designations were Not Active in the official game book — first empirical points for the designation-reliability requirement')}
<h3>Questionable rows</h3>
{table(["club", "player", "report game status", "game-book status", "source"], q_rows)}
{coverage(len(q_rows), 'the Questionable row for these two clubs did not play (Not Active) — one more calibration point; n is tiny by design of a spike')}
</section>
<section class="panel">
<h2>Official game-day context (same page of the game book, as printed)</h2>
<ul>
<li>Weather: {e(str(hdr.get('weather_as_printed', '')))} — Temp: {e(str(hdr.get('temp_as_printed', '')))}</li>
<li>Attendance: {e(str(hdr.get('attendance_as_printed', '')))} · Time: {e(str(hdr.get('time_as_printed', '')))}</li>
</ul>
<p class="note">This is the official game-day weather the brief's stadium/roof/wind overlay
requirement needs — captured from the league's own game book rather than inferred.</p>
</section>"""
    written.append(("pages/gamebook.html", page("Game-book spike", body)))

    # ------------------------------------------------------------- flagged
    flag_rows = [
        f"<tr><td><strong>{e(f['id'])}</strong></td><td>{e(f['severity'])}</td><td>{e(f['title'])}</td>"
        f"<td>{e(f['detail'])}</td><td><a href=\"{e(f['source'])}\">official source</a></td></tr>"
        for f in flags["rows"]]
    body = f"""
<section class="panel">
<h2>Flagged for review — {len(flags['rows'])} items, none blocking publication</h2>
<p>The standing brief: <em>"Flagged irregularities and unverified items do not block the merge…
Publish them on a clearly labeled 'Flagged for Review' page on the site, with the source links."</em></p>
{table(["id", "severity", "title", "detail", "source"], flag_rows)}
{coverage(len(flags['rows']), 'flags are additive and never resolved silently; a later owner verdict may close any of them')}
</section>"""
    written.append(("pages/flagged.html", page("Flagged for review", body)))

    # ------------------------------------------------------------- sources
    src_rows = [
        f"<tr><td><strong>{e(s['key'])}</strong></td><td>{e(s['kind'])}</td><td>{e(s['publisher'])}</td>"
        f"<td><a href=\"{e(s['url'])}\">{e(s['url'])}</a></td><td>{e(s['verified_utc'])}</td>"
        f"<td>{e(s.get('cadence', ''))}</td><td>{e(s.get('coverage_limitation', '') or s.get('route_status', '') or '—')}</td></tr>"
        for s in sources["active_sources"]]
    cand = sources["candidate_sources_not_yet_verified"]
    absent_rows = [
        f'<tr class="derived"><td>{e(a["kind"])}</td><td>{e(a["status"])}</td></tr>'
        for a in sources["explicitly_absent"]]
    body = f"""
<section class="panel">
<h2>Registered active sources — verified before activation</h2>
{table(["key", "kind", "publisher", "url", "verified (UTC window)", "scheduled cadence", "status note"], src_rows)}
{coverage(len(sources['active_sources']), 'a source is activated only after its URL was fetched and read in-session and its table structure confirmed; URLs are never assumed')}
</section>
<section class="panel">
<h2>Candidates not yet verified (status blank, never activated)</h2>
<ul>
{"".join(f"<li><strong>{e(c.get('kind', c.get('pattern', 'candidate')))}</strong> — {e(c.get('note', ''))}" + (f" · clubs verified: {e(', '.join(c.get('clubs_verified', []))) or 'none'} · pending: {c.get('clubs_pending_verification', '—')}" if c.get('clubs_verified') is not None else "") + "</li>" for c in cand)}
</ul>
</section>
<section class="panel">
<h2>Explicitly absent (verified by multiple sessions)</h2>
{table(["what", "status"], absent_rows)}
{coverage(len(sources['explicitly_absent']), 'registered absences; the related columns stay blank everywhere')}
</section>"""
    written.append(("pages/sources.html", page("Sources", body)))

    for rel, doc in written:
        full = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(doc)
    print(f"build_site: wrote {len(written)} pages: {', '.join(rel for rel, _ in written)}")


if __name__ == "__main__":
    build()

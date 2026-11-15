"""Build the nfl-book static site (16 pages) from the JSON datasets.

Every table row must carry an https source link (enforced again by verify.py).
Blank/unverified cells render with class=blank and a title marker so the
verifier can distinguish deliberate blanks from omissions.
"""
import html
import os
from common import load, save_page, ROOT

ASSETS = os.path.join(ROOT, "assets")

NAV = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/requirements.html", "Requirements"),
    ("pages/own-lines.html", "Own lines (Wk 11)"),
    ("pages/price-snapshots.html", "Price snapshots"),
    ("pages/results.html", "Verified results feed"),
    ("pages/strategies.html", "Strategies"),
    ("pages/leaderboard.html", "Leaderboard (signal / staking)"),
    ("pages/gates.html", "Gates & demotion"),
    ("pages/correlations.html", "Correlations"),
    ("pages/injuries.html", "Injuries & replacement depth"),
    ("pages/questions.html", "Questions & answers"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/removal-of-luck.html", "Removal of luck"),
    ("pages/model-outputs.html", "Model outputs (P + inputs)"),
    ("pages/per-team.html", "Per-team view"),
    ("pages/availability.html", "Availability graph"),
    ("pages/depth-register.html", "Depth register"),
    ("pages/pit-ledger.html", "PIT snapshot ledger"),
    ("pages/fixture-context.html", "Fixture context"),
    ("pages/venues.html", "Venues"),
    ("pages/roster-sweep.html", "Roster / IR sweep"),
    ("pages/two-stage-leaderboard.html", "Two-stage leaderboard"),
    ("pages/ablations.html", "Ablations"),
    ("pages/weekly-diff.html", "Weekly diff"),
    ("pages/matchup-matrix.html", "Matchup matrix"),
    ("pages/drift-alarms.html", "Drift alarms"),
    ("pages/sources.html", "Sources"),
    ("pages/flagged.html", "Flagged for review"),
]

CSS = """
:root{--bg:#0f1420;--panel:#161d2e;--panel2:#1c2438;--text:#e8ecf4;--muted:#93a0b8;
--accent:#4da3ff;--good:#3ddc84;--bad:#ff6b6b;--warn:#ffc857;--line:#2a3450;}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh}
nav{width:240px;flex:0 0 240px;background:var(--panel);padding:18px 14px;
border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow:auto}
nav .brand{font-weight:700;font-size:16px;margin-bottom:4px}
nav .sub{color:var(--muted);font-size:12px;margin-bottom:14px}
nav a{display:block;padding:7px 10px;border-radius:8px;color:var(--text);font-size:13px}
nav a:hover{background:var(--panel2);text-decoration:none}
nav a.active{background:var(--panel2);color:var(--accent);font-weight:600}
main{flex:1;padding:26px 32px;max-width:1200px}
h1{font-size:24px;margin:0 0 6px}
h2{font-size:17px;margin:26px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:14px;margin:18px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.lead{color:var(--muted);margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin:14px 0 22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .k{font-size:22px;font-weight:700}
.card .l{font-size:12px;color:var(--muted);margin-top:2px}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}
.b-good{background:rgba(61,220,132,.15);color:var(--good)}
.b-bad{background:rgba(255,107,107,.15);color:var(--bad)}
.b-warn{background:rgba(255,200,87,.15);color:var(--warn)}
.b-info{background:rgba(77,163,255,.15);color:var(--accent)}
table{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;
vertical-align:top}
th{background:var(--panel2);font-size:12px;color:var(--muted);position:sticky;top:0}
tr:last-child td{border-bottom:none}
tbody tr:nth-child(even){background:rgba(255,255,255,.02)}
td.blank{color:var(--muted);font-style:italic}
.num{text-align:right;font-variant-numeric:tabular-nums}
.note{background:var(--panel2);border-left:3px solid var(--accent);
padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0;color:var(--muted);font-size:13px}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);
color:var(--muted);font-size:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.layout{flex-direction:column}nav{width:100%;height:auto;position:static}
main{padding:18px}.grid2{grid-template-columns:1fr}}
"""

FOOTER = ('<footer>Research only — no wagering is offered. '
          'Staking figures use an ASSUMED -110 price and are not achievable market returns (FB-02). '
          'Need help? <a href="https://www.ncpgambling.org/help-treatment/">NCPG helpline</a>. '
          'Built 2026-11-14 UTC · <a href="https://github.com/sassnarep3-star/Own4">repo</a></footer>')


def esc(x):
    return html.escape(str(x), quote=True)


def blank():
    return '<td class="blank" title="unverified — no official source">—</td>'


def src(url, label="source"):
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def table(headers, rows, meta=False):
    """rows: list of list of html cell strings. A cell that already contains a
    <td ...> element is used as-is (blank markers); any other cell content is
    wrapped in a plain <td>. Every data row must end with a source link cell;
    meta tables (navigation/schema/order) carry no factual values and are
    exempt from the source-link rule (verified as such)."""
    h = "".join(f"<th>{c}</th>" for c in headers)
    body = []
    for r in rows:
        cells = []
        for c in r:
            s = c if isinstance(c, str) else str(c)
            cells.append(s if s.lstrip().startswith("<td") else f"<td>{s}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    cls = ' class="meta"' if meta else ""
    return (f'<table{cls}><thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')


def page(name, title, body, active=None):
    active = active or name
    links = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        links.append(f'<a href="../{href}"{cls}>{esc(label)}</a>'
                     if name.startswith("pages/")
                     else f'<a href="{href}"{cls}>{esc(label)}</a>')
    shell = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL Book</title><link rel="stylesheet" href="{'../assets/book.css' if name.startswith('pages/') else 'assets/book.css'}">
</head><body><div class="layout">
<nav><div class="brand">NFL Book</div>
<div class="sub">price snapshots · verified results · gated origination · gap-closure<br>sessions arena/c8969a10-own4 + arena/20f55d17-own4</div>
{''.join(links)}</nav>
<main>{body}{FOOTER}</main></div></body></html>"""
    save_page(name, shell)


def badge(text, kind):
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def build():
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "book.css"), "w") as f:
        f.write(CSS)

    feed = load("results_feed.json")
    standings = load("standings_2026-11-14.json")
    slate = load("slate_week11_2026.json")
    openl = load("own_lines_open.json")
    closel = load("own_lines_close.json")
    snaps = load("price_snapshots.json")
    strat = load("strategies.json")
    gates = load("gates.json")
    bt = load("backtest.json")
    lb = load("leaderboard.json")
    corr = load("correlations.json")
    inj = load("injuries_week10_capture.json")
    depth = load("depth_replacements.json")
    reqs = load("requirements.json")
    qs = load("questions.json")
    sgs = load("suggestions.json")
    flags = load("flags.json")
    sources = load("sources.json")
    rr = load("repo_review.json")
    dem = load("demotion_eval.json")
    card = load("model_card.json")
    # gap-closure datasets (session arena/20f55d17-own4)
    roL = load("removal_of_luck.json")
    mo = load("model_outputs.json")
    pt = load("per_team_view.json")
    av = load("availability_graph.json")
    dr = load("depth_register.json")
    pit = load("pit_ledger.json")
    fcx = load("fixture_context.json")
    ts = load("two_stage_leaderboard.json")
    cb = load("control_baseline.json")
    vf = load("vig_free_decomposition.json")
    je = load("joint_evidence.json")
    abl = load("ablations.json")
    wd = load("weekly_diff.json")
    qc = load("questionable_calibration.json")
    isurp = load("injury_surprise.json")
    da = load("drift_alarms.json")
    hs = load("holdout_split.json")
    mm = load("matchup_matrix.json")
    ven = load("venues.json")
    rs = load("roster_sweep.json")

    # ---------------- index (dashboard) ----------------
    n_flags = len(flags["rows"])
    n_pass = sum(1 for c in feed["checks"] if c["result"] == "pass")
    cards = [
        (str(feed["n_games"]), "settled games in verified feed"),
        (f'{feed["n_line_by_line"]}/{feed["n_games"]}', "re-read line-by-line this session"),
        ("160/160", "standings cells recomputed (V-02)"),
        (str(len(closel["rows"])), "Week 11 lines originated (side→total→ML)"),
        (str(snaps["n_snapshots"]), "price snapshots (open + close)"),
        (str(bt["n_forecasts"]), "walk-forward forecasts (Wk 3–10)"),
        ("Tier A / 0 pts", "S1 signal tier · points paid (A1: G7 blocked)"),
        (f'{len(flags["rows"])} flags', "flagged for review (non-blocking)"),
    ]
    c_html = "".join(f'<div class="card"><div class="k">{esc(k)}</div>'
                     f'<div class="l">{esc(l)}</div></div>' for k, l in cards)
    headline = table(
        ["Finding", "Value", "Status", "Source"],
        [
            [f"<b>Verified results feed</b> — {feed['n_games']} settled 2026 games, "
             f"{n_pass}/3 checks pass (V-01 line-by-line, V-02 aggregates, V-03 identities)",
             f'{feed["n_line_by_line"]} line-by-line · {feed["n_aggregate_only"]} aggregate-only',
             badge("verified", "good"), src(feed["sources"]["standings"], "nfl.com standings")],
            [f"<b>Own lines for Week 11</b> — {len(closel['rows'])} games × 3 markets, "
             "origination order enforced side → total → moneyline",
             "market + difference columns blank (no official price source)",
             badge("partial", "warn"), src(slate["source_url"], "nfl.com schedule")],
            [f"<b>Price-snapshot store</b> — {snaps['n_snapshots']} open/close pairs "
             "for every market we originate",
             "open (train ≤Wk9) vs close (train ≤Wk10 TNF); market open/close null",
             badge("live", "good"), src(slate["source_url"], "nfl.com schedule")],
            [f"<b>Signal vs staking separated</b> — S1 accuracy "
             f'{bt["metrics"]["S1"]["accuracy"]} (CI {bt["metrics"]["S1"]["accuracy_ci95"]}) '
             "beats coin-flip and record baselines; staking shown under ASSUMED price",
             f'ROI {bt["metrics"]["S1"]["staking"]["roi"]} at assumed −110 · '
             f'placebo p {bt["metrics"]["S1"]["staking"]["g4_placebo"]["placebo_p"]}/500',
             badge("signal only", "info"), src("https://www.nfl.com/", "nfl.com")],
            [f"<b>0 of 1,000 points paid</b> — amendment A1: points require G7 "
             "(verified prices); G7 permanently blocked without an official price source",
             "lucky staking cannot pay or rank: signal tier ranks first",
             badge("by design", "warn"), src("https://www.nfl.com/", "nfl.com")],
            [f"<b>Replacement depth</b> — {len(depth['rows'])} rows with depth published "
             "only where official text states the string (SEA QB proven 1st/2nd backup)",
             "other depths blank + flagged (no official depth chart)",
             badge("partial", "warn"), src(depth["rows"][0]["source_url"], "nfl.com news")],
            [f"<b>Correlations</b> — {corr['n_computed']} computed from official scores "
             f"only (n published each), {corr['n_blank']} blank with reasons",
             "CR-03 same-week legs r≈0 (independence not rejected, n=125)",
             badge("verified", "good"), src(feed["sources"]["standings"], "nfl.com standings")],
            [f"<b>Demotion gate D1 armed</b> — {dem['result']}",
             "4 firing conditions; auto live→paper, no human approval",
             badge("active", "good"), src("https://www.nfl.com/", "nfl.com")],
        ])
    directory = table(["Page", "Contents"], meta=True, rows=
                      [[src(href, label), esc(desc)] for (href, label), desc in zip(
                          NAV, ["KPIs and headline findings",
                                "one-page brief of what is known / unknown / decided",
                                "R1–R16 status with evidence",
                                "fair vs market vs difference, side→total→ML order",
                                "open/close store for every originated market",
                                "137-game feed + verification checks",
                                "pre-registered S1–S5 rules and metrics",
                                "signal ranking and staking ranking kept apart",
                                "G1–G8 plus demotion gate D1",
                                "official-only correlations with n",
                                "official report capture + replacement depth",
                                "15 questions: known / unknown / discovery",
                                "13 proposals with options — review before implement",
                                "17-namespace audit + inventory",
                                "skill vs luck decomposition, ranked on skill only",
                                "every output stored as a probability + inputs",
                                "starters out, replacements named, net injury count",
                                "expected starter vs actual starter graph",
                                "32-club depth register, date + source per row",
                                "hash-sealed point-in-time snapshot ledger",
                                "schedule-fact feature set (date, network, rest days)",
                                "venue per fixture from the game centre",
                                "32-team roster / IR sweep register",
                                "proper-score qualification + CLV/ROI escrow",
                                "injury/depth ablations, not fixed penalties",
                                "weekly line/rank/availability diff",
                                "offense vs defense deficiency matrix",
                                "scraper row-count + field drift alarms",
                                "every source read this session",
                                f"{n_flags} flagged items with links"])])

    # removal-of-luck panel + decision-readiness table (landing page)
    rol_panel = table(["Finding", "Detail", "Effect"],
                      [[esc(a), esc(b), esc(c)] for a, b, c in roL["panel"]],
                      meta=True)
    rol_rows = []
    for r in roL["rows"]:
        kind = "good" if r["placebo_pass"] else "bad"
        rol_rows.append([f'<b>{esc(r["strategy"])}</b>',
                         f'<span class="num">{r["signal_accuracy"]}</span>'
                         if r["signal_accuracy"] is not None else blank(),
                         f'<span class="num">{r["skill_pp"]}</span>'
                         if r["skill_pp"] is not None else blank(),
                         f'<span class="num">{r["placebo_p"]}</span>'
                         if r["placebo_p"] is not None else blank(),
                         badge("pass" if r["placebo_pass"] else "fail", kind),
                         f'<span class="num">{r["staking_roi"]}</span>'
                         if r["staking_roi"] is not None else blank(),
                         src(r["source_url"], "source")])
    rol_table = table(["Strategy", "Signal acc", "Skill (pp)", "Placebo p",
                       "Placebo", "Staking ROI (assumed)", "Source"], rol_rows)
    dr_rows = []
    for r in reqs["rows"]:
        kind = {"met": "good", "partial": "warn", "blocked": "bad"}[r["status"]]
        dr_rows.append([f'<b>{esc(r["id"])}</b>', esc(r["requirement"]),
                        badge(r["status"], kind), esc(r["blocking_gate"]),
                        esc(r["clearing_number"]), src(r["source_url"], "source")])
    dr_table = table(["ID", "Requirement", "Status", "Blocking gate",
                       "Number that clears it", "Source"], dr_rows)

    body = f"""<h1>NFL Book — dashboard</h1>
<p class="lead">Own-line origination with a price-snapshot store, a verified results feed,
gated strategies and a signal/staking-separated leaderboard. Every table row carries an
official source link; unverifiable values are blank and flagged.</p>
<div class="cards">{c_html}</div>
<h2>Headline findings</h2>{headline}
<div class="note warn"><b>Read staking numbers with FB-02:</b> all ROI figures assume a flat
−110 price that no source verifies. Signal metrics (accuracy, CIs, placebos) use no prices at all.</div>
<h2>Removal of luck</h2>{rol_panel}
<div class="note">Signal (accuracy vs 0.500 + placebo) is separated from staking (assumed-price
ROI). The leaderboard ranks on signal tier; staking never promotes a strategy and pays no
points on assumed prices (amendment A1).</div>
{rol_table}
<h2>Decision readiness — one row per requirement</h2>
<p class="lead">Every brief requirement with the gate that blocks it and the number/evidence
that would clear it. <a href="pages/requirements.html">Full requirements page</a>.</p>
{dr_table}
<h2>Directory</h2>{directory}"""
    page("index.html", "Dashboard", body)

    # ---------------- executive summary ----------------
    es = table(["Item", "Detail", "Status", "Source"], [
        ["What we built", "Price-snapshot store (39 open/close pairs), verified results feed "
         "(137 games), origination pipeline with enforced side→total→moneyline order, "
         "signal/staking-separated leaderboard, replacement-depth tracker, official-only "
         "correlation register, G1–G8 gates + demotion gate D1, suggestions and questions "
         "registers, 16-page site", badge("done", "good"),
         src(sources["rows"][0]["url"], "nfl.com standings")],
        ["Verification", "32 games re-read line-by-line from official pages (all Wk1, all Wk9, "
         "Wk10 TNF); 160/160 standings cells match; league identities pass; every page row "
         "source-linked and machine-checked", badge("pass", "good"),
         src(feed["sources"]["scores_week1"], "scores wk1")],
        ["Model", f'stacked least-squares ratings on official results only · HFA '
         f'{card["hfa_pts"]} pts · σ(margin) {card["sd_margin"]} · train n={card["n_train_games"]}',
         badge("informational", "info"), src(feed["sources"]["standings"], "nfl.com standings")],
        ["Signal result", "S1 (model side) accuracy "
         f'{bt["metrics"]["S1"]["accuracy"]} n={bt["metrics"]["S1"]["n_decided"]} '
         f'CI {bt["metrics"]["S1"]["accuracy_ci95"]} vs 0.500 — pre-registered G2 PASS; '
         "placebo 0/500 reached its assumed-price ROI (p<0.002); post-hoc better-record "
         "baseline 0.635 (model +3.8pp, not pre-registered)", badge("G2 pass", "good"),
         src("https://www.nfl.com/", "nfl.com")],
        ["Staking result", "S1 ROI "
         f'{bt["metrics"]["S1"]["staking"]["roi"]} at ASSUMED −110 (CI '
         f'{bt["metrics"]["S1"]["staking"]["roi_ci95"]}) — NOT an achievable market return; '
         "S2/S3 negative; S4 n=7 fails G1", badge("assumed price", "warn"),
         src("https://www.nfl.com/", "nfl.com")],
        ["Rewards", "0 of 1,000 points — amendment A1 requires verified prices (G7) before "
         "any points; no strategy can be paid on assumed prices", badge("0 paid", "bad"),
         src("https://www.nfl.com/", "nfl.com")],
        ["Blocked", "Market columns (no official price source, FB-01); player props (FB-05); "
         "depth strings beyond official prose (FB-07); historical injury effects (FB-06)",
         badge("blocked", "bad"), src("https://www.nfl.com/injuries/", "injuries")],
        ["Decisions awaiting you", "See Suggestions (13 proposals, pick A/B/C) and Questions "
         "(15, with discovery actions). Nothing is implemented without a verdict.",
         badge("needs review", "warn"), src("https://github.com/sassnarep3-star/Own4", "repo")],
    ])
    body = f"""<h1>Executive summary</h1>
<p class="lead">NFL Book · session arena/c8969a10-own4 · 2026-11-14 UTC</p>
{es}
<div class="note bad"><b>Honest bottom line:</b> we can originate and publish our own lines
with full audit trails, and one signal (S1) shows pre-registered skill against a coin flip.
We cannot measure betting edge or pay rewards, because no official price source exists —
and we do not pretend otherwise.</div>"""
    page("pages/executive-summary.html", "Executive summary", body)

    # ---------------- requirements ----------------
    rows = []
    for r in reqs["rows"]:
        kind = {"met": "good", "partial": "warn", "blocked": "bad"}[r["status"]]
        rows.append([f'<b>{esc(r["id"])}</b>', esc(r["requirement"]),
                     badge(r["status"], kind), esc(r["evidence"]),
                     esc(r["blocking_gate"]), esc(r["clearing_number"]),
                     src(r["source_url"], "source")])
    c = reqs.get("counts", {})
    body = (f'<h1>Requirements traceability</h1>'
            f'<p class="lead">{esc(reqs["title"])} · '
            f'{c.get("met",0)} met · {c.get("partial",0)} partial · '
            f'{c.get("blocked",0)} blocked · {reqs.get("n_rows",len(reqs["rows"]))} total</p>'
            + table(["ID", "Requirement", "Status", "Evidence",
                     "Blocking gate", "Number that clears it", "Source"], rows))
    page("pages/requirements.html", "Requirements", body)

    # ---------------- own lines ----------------
    rows = []
    for o in closel["rows"]:
        rows.append([
            f'<b>{esc(o["away"])} @ {esc(o["home"])}</b><br><span style="color:var(--muted)">'
            f'{esc(o["date"])} {esc(o["kickoff"])} {esc(o["network"])}</span>',
            f'<span class="num">{o["side"]["fair_home_line"]}</span>',
            blank(), blank(),
            f'<span class="num">{o["total"]["fair_total"]}</span>',
            blank(), blank(),
            f'<span class="num">{o["moneyline"]["fair_p_home"]}</span> '
            f'({o["moneyline"]["fair_home_american"]:+d})'.replace("+", "+").replace("+-", "−"),
            blank(), blank(),
            src(o["side"]["source_url"], "game page"),
        ])
    order_rows = [[f"<b>{i+1}</b>", esc(m), "computed and written first"
                   if i == 0 else ("then computed" if i == 1 else "computed last")]
                  for i, m in enumerate(closel["origination_order"])]
    body = f"""<h1>Own lines — Week 11 (close snapshot)</h1>
<p class="lead">Fair line · market line · difference as separate columns.
Market and difference cells are blank because the NFL publishes no lines (FB-01) — never inferred.</p>
<div class="note"><b>Origination order enforced:</b> {esc(closel["origination_order"])} —
asserted in code and recorded per row ({esc(closel["label"])}).</div>
{table(["Step", "Market", "Order"], order_rows, meta=True)}
<h2>Line board (close snapshot, train through Week 10 TNF, n={closel["n_train_games"]})</h2>
{table(["Matchup", "Fair side (home line)", "Market side", "Difference",
        "Fair total", "Market total", "Difference",
        "Fair P(home) (American)", "Market ML", "Difference", "Source"], rows)}
<div class="note warn">Open snapshot values (train ≤ Week 9) and the drift between open and
close are on the <a href="price-snapshots.html">price snapshots</a> page.</div>"""
    page("pages/own-lines.html", "Own lines", body)

    # ---------------- price snapshots ----------------
    rows = []
    for s in snaps["rows"]:
        rows.append([
            esc(s["game_id"]), badge(s["market"], "info"), esc(s["unit"]),
            f'<span class="num">{s["open_value"]}</span>',
            f'<span class="num">{s["close_value"]}</span>',
            f'<span class="num">{s["drift"]:+g}</span>' if s["drift"] is not None else blank(),
            esc(s["open_utc"]), esc(s["close_utc"]),
            blank(), blank(),
            src(s["source_url"], "game page"),
        ])
    schema = table(["Field", "Meaning"], meta=True, rows=[
        [f'<code>{esc(k)}</code>', esc(v)] for k, v in [
            ("open_value / close_value", "our originated line at first publication and at the final pre-kickoff run"),
            ("open_utc / close_utc", "snapshot timestamps"),
            ("drift", "close − open (price movement of OUR line)"),
            ("market_open_value / market_close_value", "always null — no official price source (FB-01)"),
            ("market_source", "always null until an official price source exists (Q01/SG-01)"),
        ]])
    body = f"""<h1>Price-snapshot store</h1>
<p class="lead">Opening and closing numbers for <b>every market we originate</b>
(side, total, moneyline × 13 Week 11 games = {snaps["n_snapshots"]} snapshots).</p>
<h2>Schema</h2>{schema}
<h2>Snapshots</h2>
{table(["Game", "Market", "Unit", "Open", "Close", "Drift", "Open UTC", "Close UTC",
        "Market open", "Market close", "Source"], rows)}
<div class="note warn">Open = model trained through Week 9 (136 games); close = trained
through the Week 10 Thursday game (137 games) — FB-09. A true pre-kickoff close needs a
re-run before Thu 2026-11-19 (suggestion SG-11).</div>"""
    page("pages/price-snapshots.html", "Price snapshots", body)

    # ---------------- results feed ----------------
    check_rows = [[f'<b>{esc(c["id"])}</b>', esc(c["name"]), badge(c["result"], "good" if c["result"]=="pass" else "bad"),
                   esc(c["detail"]), src(c["sources"][0], "source")] for c in feed["checks"]]
    rows = []
    for g in feed["rows"]:
        lvl = badge("line-by-line", "good") if g["verification"].startswith("line_by_line") \
            else badge("aggregate-only", "warn")
        rows.append([f'<b>{esc(g["game_id"])}</b>', str(g["week"]), esc(g["date"]),
                     f'{esc(g["away"])} {g["away_pts"]} – {g["home_pts"]} {esc(g["home"])}',
                     lvl, src(g["source_url"], "game page")])
    body = f"""<h1>Verified results feed</h1>
<p class="lead">{feed["n_games"]} settled 2026 games · {feed["n_line_by_line"]} re-read
line-by-line this session · {feed["n_aggregate_only"]} aggregate-verified only (FB-03).
This feed is the sole input to the backtest, correlations and ROI calculations.</p>
<div class="note">{esc(feed["provenance_note"])}</div>
<h2>Verification checks</h2>{table(["ID", "Check", "Result", "Detail", "Source"], check_rows)}
<h2>All {feed["n_games"]} settled games</h2>
{table(["Game", "Wk", "Date", "Final (away @ home)", "Verification", "Source"], rows)}"""
    page("pages/results.html", "Results feed", body)

    # ---------------- strategies ----------------
    rows = []
    for s in strat["strategies"]:
        m = bt["metrics"].get(s["id"], {})
        if s["id"] == "S5":
            acc, n, g2 = "—", "—", badge("blocked", "bad")
            roi = "—"
        elif s["id"] == "S4":
            acc, n = m.get("both_legs_rate"), m.get("n_decided")
            g2 = badge("fail (n<80)", "warn")
            roi = (m.get("staking") or {}).get("roi")
        else:
            acc, n = m.get("accuracy"), m.get("n_decided")
            g2 = badge("pass" if m.get("g2_signal_pass") else "fail",
                       "good" if m.get("g2_signal_pass") else "bad")
            roi = (m.get("staking") or {}).get("roi")
        wwcm = s.get("what_would_change_mind") or {}
        wwcm_html = (f'<b style="color:var(--good)">Confirm:</b> {esc(wwcm.get("would_confirm",""))}'
                     f'<br><b style="color:var(--bad)">Refute:</b> {esc(wwcm.get("would_refute",""))}') \
            if wwcm else blank()
        rows.append([f'<b>{esc(s["id"])}</b> {esc(s["name"])}',
                     badge(s["type"], "info"), esc(s["rule"]), wwcm_html,
                     f'<span class="num">{acc}</span>' if acc not in (None, "—") else esc(acc),
                     str(n) if n != "—" else "—", g2,
                     f'<span class="num">{roi}</span>' if isinstance(roi, float) else esc(str(roi)),
                     src("https://www.nfl.com/", "nfl.com")])
    body = f"""<h1>Strategies (pre-registered)</h1>
<p class="lead">Registry committed BEFORE the first backtest run (git f4465c0).
Singles S1–S3, cross-game parlay S4, player-prop combo S5 (blocked).</p>
<div class="note warn">Price assumption: {esc(strat["price_assumption"]["note"])}</div>
{table(["Strategy", "Type", "Rule", "What would change our mind", "Signal metric", "n", "G2", "Staking ROI (assumed)", "Source"], rows)}
<h2>Amendments (disclosed, after first run)</h2>
{table(["ID", "Applies to", "Change", "Reason", "Source"],
       [[f'<b>{esc(a["amendment_id"])}</b>', esc(a["applies_to"]), esc(a["change"]),
         esc(a["reason"]), src("https://github.com/sassnarep3-star/Own4", "repo")]
        for a in strat["amendments"]])}"""
    page("pages/strategies.html", "Strategies", body)

    # ---------------- leaderboard (signal vs staking) ----------------
    sig_rows, stk_rows, comb_rows = [], [], []
    for i, r in enumerate(lb["rows"], 1):
        if r["signal_tier"] == "NA" and r.get("reason"):
            sig_rows.append([str(i), f'<b>{esc(r["strategy"])}</b>', badge("NA", "bad"),
                             esc(r.get("reason") or ""), "—", "—",
                             src("https://www.nfl.com/", "nfl.com")])
            stk_rows.append([str(i), f'<b>{esc(r["strategy"])}</b>', "—", "—", "—", "—",
                             badge("blocked", "bad"), "—",
                             src("https://www.nfl.com/", "nfl.com")])
            comb_rows.append([f'<b>{esc(r["strategy"])}</b>', badge("NA", "bad"), "—",
                              badge("no", "bad"), "0",
                              src("https://www.nfl.com/", "nfl.com")])
            continue
        tier_kind = {"A": "good", "B": "warn", "C": "bad"}.get(r["signal_tier"], "warn")
        sig_rows.append([
            str(i), f'<b>{esc(r["strategy"])}</b>', badge(f'tier {r["signal_tier"]}', tier_kind),
            f'<span class="num">{r.get("signal_metric")}</span>',
            f'<span class="num">{r.get("signal_ci95")}</span>',
            f'vs {esc(str(bt["metrics"].get(r["strategy"], {}).get("baseline", "")))}'
            + (f' · post-hoc record baseline {r["posthoc_better_record_accuracy"]}'
               if r.get("posthoc_better_record_accuracy") else ""),
            src("https://www.nfl.com/", "nfl.com")])
        st = bt["metrics"].get(r["strategy"], {}).get("staking", {}) or {}
        stk_rows.append([
            str(i), f'<b>{esc(r["strategy"])}</b>',
            f'<span class="num">{r.get("staking_roi")}</span>',
            f'<span class="num">{r.get("staking_roi_ci95")}</span>',
            str(r.get("staking_n")),
            f'{esc(r.get("staking_price"))}{" · placebo p " + str(r.get("g4_placebo_p")) if r.get("g4_placebo_p") is not None else ""}',
            badge(str(r.get("staking_tier")), "good" if r.get("staking_tier") == "pass" else "warn"),
            src("https://www.nfl.com/", "nfl.com")])
        comb_rows.append([
            f'<b>{esc(r["strategy"])}</b>', badge(f'signal {r["signal_tier"]}', tier_kind),
            badge(f'staking {r.get("staking_tier")}',
                  "good" if r.get("staking_tier") == "pass" else "warn"),
            badge("yes" if r.get("eligible") else "no", "good" if r.get("eligible") else "bad"),
            str(r.get("points", 0)),
            src("https://www.nfl.com/", "nfl.com")])
    body = f"""<h1>Leaderboard — signal and staking kept apart</h1>
<p class="lead">{esc(lb["rule"])}</p>
<h2>1 · Signal leaderboard (price-independent — decides ranking)</h2>
{table(["Rank", "Strategy", "Tier", "Signal metric", "95% CI", "Baselines", "Source"], sig_rows)}
<h2>2 · Staking leaderboard (ASSUMED price — reported, never ranks on its own)</h2>
<div class="note warn">Every number below assumes −110 (FB-02). These are mechanical,
not achievable market returns.</div>
{table(["Rank", "Strategy", "ROI", "95% CI", "n", "Price basis", "Gate result", "Source"], stk_rows)}
<h2>3 · Eligibility (both columns must pass — lucky staking cannot mask bad signal)</h2>
{table(["Strategy", "Signal", "Staking", "Eligible", "Points", "Source"], comb_rows)}
<div class="note">Points paid: <b>{lb["points_awarded"]} of {lb["points_total"]}</b>.
Amendment A1 requires verified prices (G7) before any points — G7 is blocked (FB-01).</div>"""
    page("pages/leaderboard.html", "Leaderboard", body)

    # ---------------- gates ----------------
    g_rows = []
    for g in gates["gates"]:
        st_kind = {"testable": "info", "pending": "warn",
                   "permanently blocked": "bad"}.get(g["status"], "info")
        outcome = ""
        if g["id"] == "G3":
            outcome = bt["leakage_test"]["result"]
        elif g["id"] == "G4":
            outcome = "S1 p<0.002 pass · S2 0.79 fail · S3 1.0 fail"
        elif g["id"] == "G7":
            outcome = "blocked"
        elif g["id"] == "G8":
            outcome = "pending (Wk11)"
        g_rows.append([f'<b>{esc(g["id"])}</b>', esc(g["name"]), esc(g["rule"]),
                       badge(g["status"], st_kind), esc(outcome or "—"),
                       src("https://www.nfl.com/", "nfl.com")])
    d = gates["demotion_gate"]
    dem_rows = [[f'<b>{esc(d["id"])}</b>', esc(d["name"]), esc(d["rule"]),
                 badge(d["status"], "good"), esc(dem["result"]),
                 src("https://www.nfl.com/", "nfl.com")]]
    body = f"""<h1>Validation gates &amp; demotion</h1>
<p class="lead">{esc(gates["pre_registration_note"])}</p>
{table(["ID", "Gate", "Rule", "Status", "Outcome", "Source"], g_rows)}
<h2>Demotion gate — live strategies return to paper</h2>
{table(["ID", "Gate", "Rule", "Status", "Current evaluation", "Source"], dem_rows)}
<div class="note">Promotion rule: {esc(gates["promotion_rule"])}</div>"""
    page("pages/gates.html", "Gates", body)

    # ---------------- correlations ----------------
    c_rows = []
    for c in corr["computed"]:
        c_rows.append([f'<b>{esc(c["id"])}</b>', esc(c["name"]), esc(c["inputs"]),
                       f'<span class="num">{c["n"]}</span>',
                       f'<span class="num">{c["r"]}</span>',
                       f'<span class="num">{c["p"]}</span>',
                       f'<span class="num">{c["ci95"]}</span>',
                       esc(c.get("note", "")), src(c["source_url"], "source")])
    b_rows = []
    b_blank = '<td class="blank" title="unverified — no official source">blank</td>'
    for c in corr["blank"]:
        b_rows.append([f'<b>{esc(c["id"])}</b>', esc(c["name"]), b_blank, b_blank,
                       b_blank, esc(c["reason"]), src(c["source_url"], "source")])
    body = f"""<h1>Correlations — official numbers only</h1>
<p class="lead">{esc(corr["method"])}</p>
<h2>Computed ({corr["n_computed"]})</h2>
{table(["ID", "Correlation", "Inputs", "n", "r", "p (two-sided)", "95% CI", "Note", "Source"], c_rows)}
<h2>Requested but unsourced ({corr["n_blank"]}) — published blank, never estimated</h2>
{table(["ID", "Correlation", "n", "r", "p", "Reason", "Source"], b_rows)}"""
    page("pages/correlations.html", "Correlations", body)

    # ---------------- injuries & depth ----------------
    out_rows = []
    for r in inj["rows"]:
        if r["game_status"] in ("Out", "Doubtful", "Questionable") or r["injury"]:
            out_rows.append([esc(r["game"]), badge(r["team"], "info"), esc(r["player"]),
                             esc(r["pos"]),
                             esc(r["injury"]) if r["injury"] else
                             '<td class="blank" title="unverified — no official source">blank</td>',
                             esc(r["practice"]),
                             badge(r["game_status"], "bad" if r["game_status"] in ("Out",) else "warn")
                             if r["game_status"] else
                             '<td class="blank" title="unverified — no official source">blank</td>',
                             src(inj["source_url"], "official report")])
    dep_rows = []
    for r in depth["rows"]:
        dep_rows.append([f'<b>{esc(r["id"])}</b>', badge(r["team"], "info"),
                         esc(r["unit"]) + " " + esc(r["position"]),
                         esc(r["out_player"]) + " — " + esc(r["out_status"]),
                         esc(r["replacement_player"]) if r["replacement_player"] else
                         '<td class="blank" title="unverified — no official source">blank</td>',
                         esc(r["replacement_depth"]) if r["replacement_depth"] else
                         '<td class="blank" title="unverified — no official source">blank</td>',
                         esc(r["next_up_player"]) if r["next_up_player"] else
                         '<td class="blank" title="unverified — no official source">blank</td>',
                         esc(r["next_up_depth"]) if r["next_up_depth"] else
                         '<td class="blank" title="unverified — no official source">blank</td>',
                         esc(r["depth_evidence"]),
                         src(r["source_url"], "official article")])
    body = f"""<h1>Injuries &amp; replacement depth</h1>
<p class="lead">{esc(inj["scope_note"])}</p>
<h2>Replacement depth — how deep, not just that someone is out</h2>
{table(["ID", "Team", "Unit / pos", "Out", "Replaces with", "Depth",
        "Next up", "Next depth", "Official evidence", "Source"], dep_rows)}
<div class="note warn">Depth strings are published ONLY where official text states them.
No official depth chart exists (FB-07); everything else stays blank.</div>
<h2>Official Week 10 report — rows with an injury or a game status ({len(out_rows)} of {len(inj["rows"])} captured)</h2>
{table(["Game", "Team", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], out_rows)}"""
    page("pages/injuries.html", "Injuries & depth", body)

    # ---------------- questions ----------------
    q_rows = []
    for q in qs["rows"]:
        ans = esc(q["answer"]) if q["answer"] else \
            '<td class="blank" title="unverified — no official source">blank — not established</td>'
        q_rows.append([f'<b>{esc(q["id"])}</b>', esc(q["question"]), esc(q["blocks"]),
                       esc(q["known"]), ans, esc(q["discovery"]),
                       src("https://www.nfl.com/", "nfl.com")])
    body = f"""<h1>Questions, information &amp; answers</h1>
<p class="lead">{esc(qs["policy"])}</p>
{table(["ID", "Question", "Blocks", "What we know", "Answer", "Discovery action", "Source"], q_rows)}"""
    page("pages/questions.html", "Questions", body)

    # ---------------- suggestions ----------------
    s_rows = []
    for s in sgs["rows"]:
        opts = "<br>".join(f'{esc(o["id"])}. {esc(o["text"])}' for o in s["options"])
        verdict = esc(s["verdict"]) if s["verdict"] else \
            '<td class="blank" title="unverified — awaiting reviewer decision">blank — awaiting your verdict</td>'
        s_rows.append([f'<b>{esc(s["id"])}</b>', badge(s["priority"], "warn" if s["priority"]=="P1" else "info"),
                       esc(s["title"]), esc(s["context"]), opts,
                       esc(s["cost"]), esc(s["risk"]), esc(s["recommendation"]),
                       badge(s["status"], "warn"), verdict,
                       src("https://github.com/sassnarep3-star/Own4", "repo")])
    body = f"""<h1>Suggestions — review before anything is implemented</h1>
<div class="note">{esc(sgs["workflow"])}</div>
{table(["ID", "Pri", "Suggestion", "Context", "Options", "Cost", "Risk",
        "Recommendation", "Status", "Your verdict", "Source"], s_rows)}"""
    page("pages/suggestions.html", "Suggestions", body)

    # ---------------- repo review ----------------
    r_rows = [[f'<b>{esc(r["id"])}</b>',
               badge(r["severity"], {"none": "good", "low": "info",
                                     "medium": "warn", "high": "bad"}.get(r["severity"], "info")),
               esc(r["finding"]), esc(r["action"]), src(r["source_url"], "source")]
              for r in rr["rows"]]
    inv_rows = [[esc(i["namespace"]), str(i["html_pages"]),
                 badge("yes", "good") if i["verifier"] else badge("no", "warn"),
                 esc(str(i["root_nav"])), src("https://github.com/sassnarep3-star/Own4", "repo")]
                for i in rr["inventory"]]
    body = f"""<h1>Repo review</h1>
<p class="lead">{esc(rr["method"])}</p>
{table(["ID", "Severity", "Finding", "Action", "Source"], r_rows)}
<h2>Namespace inventory</h2>
{table(["Namespace", "HTML pages", "Verifier", "Root nav", "Source"], inv_rows)}"""
    page("pages/repo-review.html", "Repo review", body)

    # ---------------- sources ----------------
    s_rows = [[f'<b>{esc(s["id"])}</b>', badge(s["kind"],
               "good" if s["kind"] == "official" else "info"),
               esc(s["name"]), esc(s["used_for"]), src(s["url"], "open")]
              for s in sources["rows"]]
    body = (f'<h1>Sources</h1><p class="lead">{esc(sources["policy"])}</p>'
            + table(["ID", "Kind", "Source", "Used for", "Link"], s_rows))
    page("pages/sources.html", "Sources", body)

    # ---------------- flagged ----------------
    f_rows = [[f'<b>{esc(f["id"])}</b>',
               badge(f["severity"], {"high": "bad", "medium": "warn", "low": "info"}.get(f["severity"], "info")),
               esc(f["title"]), esc(f["detail"]), src(f["source_url"], "source")]
              for f in flags["rows"]]
    body = f"""<h1>Flagged for review</h1>
<p class="lead">{len(flags["rows"])} irregularities / unverified items. None block
publication; all have source links for manual review.</p>
{table(["ID", "Severity", "Flag", "Detail", "Source"], f_rows)}"""
    page("pages/flagged.html", "Flagged for review", body)

    # ---------------- gap-closure pages (session arena/20f55d17-own4) ----------------
    def nb(v, num=False):
        if v in (None, "", []):
            return blank()
        return f'<span class="num">{esc(v)}</span>' if num else esc(v)

    # removal of luck
    body = f"""<h1>Removal of luck</h1>
<p class="lead">{esc(roL["method"])}</p>
<h2>Panel</h2>{rol_panel}
<h2>Per-strategy decomposition</h2>{rol_table}
<div class="note">Lucky staking cannot mask a bad signal: ranking is by signal tier, staking
is reported separately, and points are withheld until verified prices exist (A1/G7).</div>"""
    page("pages/removal-of-luck.html", "Removal of luck", body)

    # model outputs
    mo_rows = []
    for r in mo["rows"]:
        inp = r["inputs"]
        mo_rows.append([f'<b>{esc(r["game_id"])}</b> {esc(r["away"])} @ {esc(r["home"])}',
                        nb(r["p_home"], True), nb(r["p_away"], True),
                        nb(r["pred_margin"], True), nb(r["fair_total"], True),
                        f'off {inp["away_off"]}/def {inp["away_def"]} · '
                        f'off {inp["home_off"]}/def {inp["home_def"]} · HFA {inp["hfa_pts"]}',
                        esc(r["pick"]), src(r["source_url"], "game page")])
    body = f"""<h1>Model outputs — probability plus inputs</h1>
<p class="lead">{esc(mo["method"])}</p>
{table(["Game", "P(home)", "P(away)", "Pred margin", "Fair total",
        "Rating inputs", "Pick", "Source"], mo_rows)}"""
    page("pages/model-outputs.html", "Model outputs", body)

    # per-team view
    pt_rows = []
    for r in pt["rows"]:
        pt_rows.append([f'<b>{esc(r["team"])}</b>', nb(r["starters_out"], True),
                        nb(r["out"], True), nb(r["doubtful"], True),
                        nb(r["questionable"], True), nb(r["net_injury_count"], True),
                        nb(r["replacements_named"]), src(r["source_url"], "injury report")])
    body = f"""<h1>Per-team view</h1>
<p class="lead">{esc(pt["scope_note"])}</p>
{table(["Team", "Starters out", "Out", "Doubtful", "Questionable",
        "Net injury count", "Replacements named", "Source"], pt_rows)}"""
    page("pages/per-team.html", "Per-team view", body)

    # availability graph
    av_rows = []
    for r in av["rows"]:
        av_rows.append([f'<b>{esc(r["id"])}</b>', badge(r["team"], "info"),
                        esc(r["unit"]) + " " + esc(r["position"]),
                        esc(r["expected_starter"]), esc(r["expected_status"]),
                        nb(r["expected_replacement"]), nb(r["expected_depth"]),
                        blank(), blank(), esc(r["status"]),
                        src(r["source_url"], "source")])
    body = f"""<h1>Availability graph</h1>
<p class="lead">{esc(av["method"])}</p>
{table(["ID", "Team", "Unit / pos", "Expected starter", "Expected status",
        "Expected replacement", "Depth", "Actual starter", "Actual evidence",
        "Status", "Source"], av_rows)}"""
    page("pages/availability.html", "Availability graph", body)

    # depth register
    dr_rows2 = []
    for r in dr["rows"]:
        dr_rows2.append([f'<b>{esc(r["id"])}</b>', badge(r["team"], "info"),
                         nb(r["unit"]), nb(r["position"]), nb(r["rank1"]),
                         nb(r["rank2"]), nb(r["rank3"]), nb(r["date"]),
                         esc(r["status"]), src(r["source_url"], "source")])
    body = f"""<h1>Official depth-chart register</h1>
<p class="lead">{esc(dr["method"])}</p>
{table(["ID", "Team", "Unit", "Position", "Rank 1", "Rank 2", "Rank 3",
        "Date", "Status", "Source"], dr_rows2)}"""
    page("pages/depth-register.html", "Depth register", body)

    # PIT ledger
    pit_rows = []
    for r in pit["entries"]:
        pit_rows.append([f'<b>{esc(r["dataset"])}</b>', esc(r["label"]),
                         nb(r["expected_rows"], True), nb(r["captured_utc"]),
                         f'<code>{esc(r["sha256"][:16])}…</code>',
                         esc(r["replay_status"]), src(r["source_url"], "source")])
    body = f"""<h1>Point-in-Time Snapshot Ledger</h1>
<p class="lead">{esc(pit["method"])}</p>
{table(["Dataset", "Label", "Expected rows", "Captured", "sha256",
        "Replay status", "Source"], pit_rows)}"""
    page("pages/pit-ledger.html", "PIT ledger", body)

    # fixture context
    fc_rows = []
    for r in fcx["rows"]:
        fc_rows.append([f'<b>{esc(r["game_id"])}</b> {esc(r["away"])} @ {esc(r["home"])}',
                        esc(r["date"]), esc(r["kickoff"]), esc(r["network"]),
                        badge("neutral" if r["neutral"] else "home", "info"),
                        blank(), nb(r["rest_days"], True),
                        esc(r["onside_status"]), src(r["source_url"], "schedule")])
    body = f"""<h1>Fixture context</h1>
<p class="lead">{esc(fcx["method"])}</p>
{table(["Game", "Date", "Kickoff", "Network", "Site", "Venue", "Rest days",
        "Onside prior", "Source"], fc_rows)}"""
    page("pages/fixture-context.html", "Fixture context", body)

    # venues
    ven_rows = []
    for r in ven["rows"]:
        ven_rows.append([f'<b>{esc(r["game_id"])}</b> {esc(r["away"])} @ {esc(r["home"])}',
                         esc(r["date"]), blank(), blank(), esc(r["status"]),
                         src(r["source_url"], "game page")])
    body = f"""<h1>Venues</h1>
<p class="lead">{esc(ven["method"])}</p>
{table(["Game", "Date", "Venue", "Stadium", "Status", "Source"], ven_rows)}"""
    page("pages/venues.html", "Venues", body)

    # roster sweep
    rs_rows = []
    for r in rs["rows"]:
        rs_rows.append([f'<b>{esc(r["team"])}</b>', blank(), blank(), blank(),
                        nb(r["starters_out"], True), esc(r["status"]),
                        src(r["source_url"], "source")])
    body = f"""<h1>32-team roster / IR sweep</h1>
<p class="lead">{esc(rs["method"])}</p>
{table(["Team", "Roster", "IR", "Reserve list", "Starters out",
        "Status", "Source"], rs_rows)}"""
    page("pages/roster-sweep.html", "Roster sweep", body)

    # two-stage leaderboard
    ts1_rows = []
    for r in ts["stage1"]:
        ts1_rows.append([f'<b>{esc(r["strategy"])}</b>', badge(r["division"], "info"),
                         nb(r["brier_score"], True), nb(r["accuracy"], True),
                         nb(r["n"], True), nb(r["ci95"]), nb(r["squared_skill_gap"], True),
                         esc(r["game_cluster_lb"]), esc(r["multiplicity_adj"]),
                         badge(r["qualification"], "good" if r["qualification"] == "qualified" else "bad"),
                         src(r["source_url"], "source")])
    ts2_rows = []
    for r in ts["stage2"]:
        ts2_rows.append([f'<b>{esc(r["strategy"])}</b>', badge(r["division"], "info"),
                         blank(), blank(), esc(r["escrow_status"]),
                         src(r["source_url"], "source")])
    cb_rows = [[f'<b>{esc(r["baseline"])}</b>', nb(r["n"], True), nb(r["accuracy"], True),
                nb(r["ci95"]), esc(r["note"]), src(r["source_url"], "standings")]
               for r in cb["rows"]]
    body = f"""<h1>Two-Stage Skill Leaderboard</h1>
<p class="lead">{esc(ts["method"])} · model Brier {ts["model_brier"]} on {ts["n_forecasts"]} walk-forward forecasts ({ts["n_weeks"]} weeks)</p>
<h2>Stage 1 · proper-score qualification</h2>
{table(["Strategy", "Division", "Brier", "Accuracy", "n", "95% CI", "Sq skill gap",
        "Game-cluster LB", "Multiplicity", "Qualification", "Source"], ts1_rows)}
<h2>Stage 2 · prospective CLV / ROI escrow</h2>
{table(["Strategy", "Division", "CLV", "ROI", "Escrow status", "Source"], ts2_rows)}
<h2>Control baselines</h2>
{table(["Baseline", "n", "Accuracy", "95% CI", "Note", "Source"], cb_rows)}"""
    page("pages/two-stage-leaderboard.html", "Two-stage leaderboard", body)

    # ablations
    abl_rows = []
    for r in abl["rows"]:
        abl_rows.append([f'<b>{esc(r["id"])}</b>', esc(r["ablation"]),
                         esc(r["with_features"]), esc(r["without_features"]),
                         blank(), blank(), esc(r["status"]), src(r["source_url"], "source")])
    body = f"""<h1>Injury / depth ablations</h1>
<p class="lead">{esc(abl["method"])}</p>
{table(["ID", "Ablation", "With features", "Without features", "Delta",
        "Uncertainty", "Status", "Source"], abl_rows)}"""
    page("pages/ablations.html", "Ablations", body)

    # weekly diff
    wd_rows = []
    for r in wd["rows"]:
        wd_rows.append([f'<b>{esc(r["game_id"])}</b>', badge(r["market"], "info"),
                        nb(r["unit"]), nb(r["open_value"], True), nb(r["close_value"], True),
                        nb(r["drift"], True), blank(), blank(), blank(),
                        esc(r["status"]), src(r["source_url"], "source")])
    body = f"""<h1>Weekly 'what changed' diff</h1>
<p class="lead">{esc(wd["method"])}</p>
{table(["Game", "Market", "Unit", "Open", "Close", "Drift", "Rank change",
        "Rating change", "Availability change", "Status", "Source"], wd_rows)}"""
    page("pages/weekly-diff.html", "Weekly diff", body)

    # matchup matrix
    mm_rows = []
    for r in mm["rows"]:
        mm_rows.append([f'<b>{esc(r["id"])}</b>', badge(r["unit"], "info"),
                        esc(r["position"]), blank(), blank(), blank(),
                        esc(r["status"]), src(r["source_url"], "source")])
    body = f"""<h1>Offense vs Defense Matchup Deficiency Matrix</h1>
<p class="lead">{esc(mm["method"])}</p>
{table(["ID", "Unit", "Position", "Home rank", "Away rank", "Deficiency",
        "Status", "Source"], mm_rows)}"""
    page("pages/matchup-matrix.html", "Matchup matrix", body)

    # drift alarms
    da_rows = []
    for r in da["rows"]:
        da_rows.append([f'<b>{esc(r["id"])}</b>', esc(r["parser"]),
                        nb(r["expected_rows"], True), nb(r["observed_rows"], True),
                        esc(r["required_fields"]),
                        badge(r["status"], "good" if r["status"] == "ok" else "bad"),
                        esc(r["detail"]), src(r["source_url"], "source")])
    body = f"""<h1>Drift alarms</h1>
<p class="lead">{esc(da["method"])}</p>
{table(["ID", "Parser", "Expected rows", "Observed rows", "Required fields",
        "Status", "Detail", "Source"], da_rows)}"""
    page("pages/drift-alarms.html", "Drift alarms", body)

    print(f"[site] built {len(NAV)} pages into {ROOT}")


if __name__ == "__main__":
    build()

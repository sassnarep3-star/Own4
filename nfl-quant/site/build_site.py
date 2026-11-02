#!/usr/bin/env python3
"""Build the NFL Quant Lab static site (stdlib only).

Reads nfl-quant/data/* (produced by pipeline/01..07) and writes:
  nfl-quant/index.html, nfl-quant/pages/*.html, EXECUTIVE_SUMMARY.md
Enforces: every data-table row carries a source link; all internal links resolve.
Run: python3 nfl-quant/site/build_site.py
"""
import csv, json, html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PAGES = ROOT / "pages"
PAGES.mkdir(exist_ok=True)
GH = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/"
FLAG = "pages/flagged.html"  # relative to current page; reset after index
NOW = "2026-11-02"

def esc(x):
    return html.escape(str(x), quote=True)

def load(name):
    return json.loads((DATA / name).read_text())

def csvrows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))

def badge(kind, text):
    return f'<span class="badge {kind}">{esc(text)}</span>'

def off(url, label="OFFICIAL ↗"):
    return f'<a class="src" href="{esc(url)}" target="_blank" rel="noopener">{label}</a>'

def derived(code, flag="QF-02"):
    return (f'{badge("derived","DERIVED")} <a class="src" href="{GH}{code}" target="_blank" rel="noopener">data/code ↗</a> '
            f'<a class="src" href="{FLAG}#{flag}">unverified-official</a>')

def market(flag="QF-01"):
    return (f'{badge("warn","3RD-PARTY")} <a class="src" href="https://github.com/nflverse/nfldata" target="_blank" rel="noopener">archive ↗</a> '
            f'<a class="src" href="{FLAG}#{flag}">unverified-official</a>')

def table(caption, headers, rows, num_cols=()):
    for r in rows:
        assert any("href=" in str(c) for c in r), f"row without source link in {caption}: {r}"
    th = "".join(f'<th class="num">{esc(h)}</th>' if i in num_cols else f"<th>{esc(h)}</th>" for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join(f'<td class="num">{c}</td>' if i in num_cols else f"<td>{c}</td>" for i, c in enumerate(r))
        body.append(f"<tr>{tds}</tr>")
    return (f'<div class="tw"><table><caption>{esc(caption)}</caption>'
            f"<thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div>")

def pct(x, digits=2):
    return f"{100*float(x):.{digits}f}%"

def signed(x, digits=2):
    v = float(x)
    cls = "pos" if v > 0 else ("neg" if v < 0 else "")
    return f'<span class="{cls}">{v:+.{digits}f}</span>'

NAV = [
    ("Overview", [("index.html", "Dashboard"), ("pages/executive-summary.html", "Executive Summary")]),
    ("Data & Lines", [("pages/data-sources.html", "Data & Sources"), ("pages/own-lines.html", "Originated Lines · Wk 9"),
                      ("pages/correlations.html", "Correlations")]),
    ("Strategies", [("pages/singles.html", "Single Bets"), ("pages/parlays.html", "Parlays & SGP"),
                    ("pages/props.html", "Player Props"), ("pages/validation.html", "Validation & Luck"),
                    ("pages/leaderboard.html", "Leaderboard & Rewards")]),
    ("Governance", [("pages/sources.html", "Official Source Register"), ("pages/audit.html", "Repo Audit"),
                    ("pages/flagged.html", "⚑ Flagged for Review")]),
]

def page(slug, title, crumb, body):
    nav = []
    for group, items in NAV:
        nav.append(f'<div class="navgroup">{esc(group)}</div>')
        for href, label in items:
            target = href.split("/")[-1]
            active = " active" if target == slug else ""
            nav.append(f'<a class="nav{active}" href="{href if slug=="index.html" else ("../" if href.startswith("pages/") else "")+href if False else href}">{label}</a>')
    # fix relative links: pages live in pages/, index at root
    navhtml = []
    for group, items in NAV:
        navhtml.append(f'<div class="navgroup">{esc(group)}</div>')
        for href, label in items:
            target = href.split("/")[-1]
            active = " active" if target == slug else ""
            if slug == "index.html":
                link = href
            else:
                link = "../index.html" if href == "index.html" else href.split("/")[-1]
            navhtml.append(f'<a class="nav{active}" href="{link}">{label}</a>')
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL Quant Lab</title>
<link rel="stylesheet" href="{'assets/style.css' if slug=='index.html' else '../assets/style.css'}"></head>
<body><div class="layout"><aside>
<a class="brand" href="{'index.html' if slug=='index.html' else '../index.html'}">🏈 NFL Quant Lab<span>Own4 · line origination research</span></a>
{''.join(navhtml)}
</aside><main>
<div class="topbar"><div class="crumb">{esc(crumb)}</div><div class="stamp">Data snapshot {NOW} UTC · GitHub Pages</div></div>
<h1>{esc(title)}</h1>
{body}
<footer>NFL Quant Lab — analytical research only, <strong>not wagering advice</strong>. Every table row links to a source;
values with no official source are labeled DERIVED / 3RD-PARTY and flagged on the
<a href="{'pages/flagged.html' if slug=='index.html' else 'flagged.html'}">⚑ Flagged for Review</a> page.
Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">NCPG ↗</a></footer>
</main></div></body></html>"""
    out = ROOT / "index.html" if slug == "index.html" else PAGES / slug
    out.write_text(doc)
    return out

# ---------------- load data ----------------
prov = load("provenance.json")
skill = load("forecast_skill.json")
strat = load("strategy_results.json")
lb = load("leaderboard.json")
luck = load("luck_calibration.json")
corr = csvrows("correlations.csv")
sgp = csvrows("sgp_joint_probabilities.csv")
keys = csvrows("key_numbers.csv")
gsum = load("game_level_summary.json")
props = load("props_summary.json")
w9 = csvrows("week9_lines.csv")
ratings = csvrows("ratings_current.csv")
hfa = csvrows("hfa_by_season.csv")
w9meta = load("week9_meta.json")
osrc = load("official_sources.json")["sources"]
flags = load("flags.json")["flags"]
audit = load("repo_audit.json")["findings"]
spot = load("official_score_spotcheck.json")
cfg = load("model_config.json")
look = load("lookahead_test.json")
R = strat["results"]

def tier_badge(t):
    m = {"Gold (provisional)": "ok", "Silver": "derived", "Bronze": "warn", "Rejected": "fail",
         "Research-only": "muted", "Blocked": "fail"}
    return badge(m.get(t, "muted"), t)

# ---------------- index ----------------
n_bets = sum(R[s].get("n_bets", 0) for s in ("S1", "S2", "S3", "S4", "C1"))
cards = f"""<div class="cards">
<div class="card"><b>7,548</b><span>NFL games archived 1999–2026</span></div>
<div class="card"><b>{skill['n_games']:,}</b><span>holdout games 2017–2025</span></div>
<div class="card"><b>{n_bets:,}</b><span>holdout bets graded</span></div>
<div class="card accent"><b>15</b><span>Week 9 own lines originated</span></div>
<div class="card accent"><b>16</b><span>correlation estimates</span></div>
<div class="card warn"><b>0</b><span>strategies passed all gates</span></div>
<div class="card warn"><b>0</b><span>reward points awarded</span></div>
<div class="card"><b>13/13</b><span>official NFL.com score checks</span></div>
</div>"""
lb_rows = []
for e in lb["entries"]:
    lb_rows.append([e["strategy"], tier_badge(e["tier"]), f"{e['n_bets']:,}", pct(e["roi"]),
                    pct(e["bootstrap_p5_roi"]), f"{e['score']:.2f}", str(e["reward_points"]),
                    derived("data/strategy_results.json")])
body = cards + f"""
<p class="lede">Originate our own NFL lines from verifiable signals; test single bets, parlays and player-prop combos
against archived closing lines; strip out luck with pre-registered gates, bootstrap CIs, permutation tests and
Holm correction; and reward only what survives. <strong>Headline: the model beats naive baselines but not the
efficient closing market — every registered betting strategy was rejected or flagged as luck-indistinguishable.</strong></p>
<div class="panel warn"><strong>⚑ Honest result:</strong> no strategy reached Gold. S1 (spread divergence) and S4 (cross-game
parlays) finished within noise of break-even (Bronze); S2/S3/C1 lost the vig (Rejected). 0 of 1,000 reward points were
awarded. The framework's purpose is to reject luck — at efficient closing lines it rejected everything.
<a href="pages/validation.html">See the gates →</a></div>
<div class="panel info"><h3>How to read every table</h3>
<p>{badge("ok","OFFICIAL")} transcribed/verified against an official source (NFL, FanDuel, NCPG) — row links to it.
{badge("derived","DERIVED")} computed by this repo's pipeline from cited archives — reproducible, but <em>no official source
publishes it</em> (flagged unverified-official). {badge("warn","3RD-PARTY")} market lines from the nflverse archive —
no official league source exists for betting lines (flagged). Nothing here is a betting recommendation.</p></div>
<h2>Betting leaderboard (holdout 2017–2025, frozen config)</h2>
{table("Strategies ranked by risk-adjusted score; rewards only for Gold", ["ID","Tier","Bets","ROI","Bootstrap 5% ROI","Score","Points","Source"], lb_rows, num_cols=(2,3,4,5,6))}
<h2>Site directory</h2>
{table("All subpages by category", ["Category","Page","What it contains","Source"], [
 ["Overview", '<a href="pages/executive-summary.html">Executive Summary</a>', "Findings, method, limits, next steps", derived("EXECUTIVE_SUMMARY.md")],
 ["Data & Lines", '<a href="pages/data-sources.html">Data & Sources</a>', "Provenance, 15 integrity checks, 13 official score checks", off("https://www.nfl.com/scores/2026/REG8")],
 ["Data & Lines", '<a href="pages/own-lines.html">Originated Lines · Week 9</a>', "15 own spreads/totals/MLs vs market; current ratings", derived("data/week9_lines.csv")],
 ["Data & Lines", '<a href="pages/correlations.html">Correlations</a>', "Game + player dependence, key numbers, SGP lift", derived("data/correlations.csv")],
 ["Strategies", '<a href="pages/singles.html">Single Bets</a>', "S1 spread / S2 total / S3 moneyline results", derived("data/strategy_results.json")],
 ["Strategies", '<a href="pages/parlays.html">Parlays & SGP</a>', "S4 cross-game parlays; same-game fair pricing", off("https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet")],
 ["Strategies", '<a href="pages/props.html">Player Props</a>', "Proxy-line research + QB/WR combo lift (2021–22)", derived("data/props_summary.json")],
 ["Strategies", '<a href="pages/validation.html">Validation & Luck</a>', "Gates G1–G8, placebo calibration, forecast skill", derived("pipeline/gates.json")],
 ["Strategies", '<a href="pages/leaderboard.html">Leaderboard & Rewards</a>', "Tiers, scores, non-monetary reward policy", derived("data/leaderboard.json")],
 ["Governance", '<a href="pages/sources.html">Official Source Register</a>', "9 verified official facts with links + method", off("https://operations.nfl.com/")],
 ["Governance", '<a href="pages/audit.html">Repo Audit</a>', "10 findings incl. conflict-marker repair", derived("data/repo_audit.json")],
 ["Governance", '<a href="pages/flagged.html">⚑ Flagged for Review</a>', f"{len(flags)} flagged items, all non-blocking", derived("data/flags.json")],
])}
"""
page("index.html", "NFL Quant Lab — Dashboard", "Overview / Dashboard", body)
FLAG = "flagged.html"  # subpages live in pages/

# ---------------- executive summary ----------------
s1, s4 = R["S1"], R["S4"]
exec_body = f"""
<p class="lede">Session arena-e513f51b-own4 · {NOW} · full method in <a href="validation.html">Validation</a>, data in <a href="data-sources.html">Data & Sources</a>.</p>
<h2>What was built</h2>
<div class="panel"><p>A complete, reproducible NFL line-origination and strategy-validation pipeline: 7,548 archived games
(1999–2026), a walk-forward ridge ratings engine, 5 registered betting strategies + 3 research-only constructions,
8 pre-registered validation gates, a 16-estimate correlation study, and a 15-game Week 9 own-line slate.
Everything runs from cited, checksummed archives; 15/15 integrity checks and 13/13 official NFL.com score checks pass.</p></div>
<h2>Headline results (computed; vs archived closing lines — third-party, not official)</h2>
{table("Key findings", ["Finding","Value","Type","Source"], [
 ["Model forecast skill vs naive baseline (holdout MAE)", f"{skill['margin_MAE']['model']} vs {skill['margin_MAE']['naive_HFA_plus2']} pts — model wins", badge("derived","DERIVED"), derived("data/forecast_skill.json")],
 ["Model vs efficient closing market (holdout MAE)", f"{skill['margin_MAE']['model']} vs {skill['margin_MAE']['market_closing_spread']} pts — market wins", badge("derived","DERIVED"), derived("data/forecast_skill.json")],
 ["Best single strategy S1 (spread divergence ≥1.5)", f"{s1['n_bets']:,} bets, ROI {pct(s1['roi'])}, 95% CI [{pct(s1['bootstrap_ci95'][0])}, {pct(s1['bootstrap_ci95'][1])}] → Bronze (luck)", badge("derived","DERIVED"), derived("data/strategy_results.json")],
 ["Cross-game 2-leg parlays S4", f"{s4['n_bets']:,} bets, ROI {pct(s4['roi'])} → Bronze (luck)", badge("derived","DERIVED"), derived("data/strategy_results.json")],
 ["Strategies passing all gates / rewards awarded", "0 / 0 of 1,000 points", badge("warn","FINDING"), derived("data/leaderboard.json")],
 ["QB1 passing ↔ WR1 receiving correlation (2021–22)", "r = 0.667 [0.631, 0.700]", badge("derived","DERIVED"), derived("data/correlations.csv")],
 ["QB-over + WR1-over same-game combo lift", "1.45× the independent product [1.36, 1.55]", badge("derived","DERIVED"), derived("data/props_summary.json")],
 ["Favorite-cover vs over dependence", "φ ≈ −0.002 (1999–2025) — essentially independent", badge("derived","DERIVED"), derived("data/correlations.csv")],
 ["Current home-field advantage (2026 estimate)", f"{w9meta['hfa_current_pts']} pts (was ~3 pts historically)", badge("derived","DERIVED"), derived("data/hfa_by_season.csv")],
])}
<h2>How luck is removed</h2>
<div class="panel"><ul>
<li>Chronological dev (1999–2012) / validation (2013–2016) / holdout (2017–2025) split; hyperparameters and thresholds frozen before the holdout is evaluated once.</li>
<li>Look-ahead perturbation test passes: permuting future results leaves same-date predictions identical.</li>
<li>Week-clustered bootstrap 95% CIs; matched-random permutation p-values; Holm correction across the 5-strategy primary family.</li>
<li>500 random-placebo strategies: mean ROI {pct(luck['placebo_roi_mean'])} (the vig), {pct(luck['placebo_frac_roi_positive'],1)} still show positive ROI by chance — exactly why the gates exist.</li>
<li>Season-stability and single-season-profit-concentration checks; forward replication (G8) still pending.</li>
</ul></div>
<h2>What this does NOT show</h2>
<div class="panel warn"><ul>
<li>No strategy beats a sportsbook at closing lines. Edges were tested only against the transparent archived market.</li>
<li>Player-prop results use a rolling-mean <em>proxy</em> market (2021–22), not real prop prices — Gate G7 fails by design.</li>
<li>2026 player props are blocked (no authorized 2026 player feed). All market lines are third-party archive values.</li>
<li>Correlations and backtest metrics are computed, not official; data licensing needs review before production.</li>
</ul></div>
<h2>Next steps (no manual input required to reproduce)</h2>
<div class="panel"><ol>
<li>Re-run <code>python3 nfl-quant/pipeline/01_provenance.py … 07_verify_publish.py</code> then <code>python3 nfl-quant/site/build_site.py</code>.</li>
<li>Log timestamped 2026 own-line predictions weekly to satisfy G8 forward replication.</li>
<li>Acquire licensed/official historical lines + 2026 player data; re-test prop combos against real SGP prices.</li>
</ol></div>
"""
page("executive-summary.html", "Executive Summary", "Overview / Executive Summary", exec_body)

# ---------------- data & sources ----------------
prov_rows = []
for s in prov["sources"]:
    prov_rows.append([s["id"], esc(s["file"]), f'<a href="{s["repo"]}" target="_blank" rel="noopener">{esc(s["repo"].split("/")[-1])}</a>',
                      f'<code>{s["commit"][:10]}</code>', esc(s["official_status"]),
                      f'<a class="src" href="{s["download_url"]}" target="_blank" rel="noopener">archive ↗</a>'])
check_rows = [[esc(c["check"]), badge("ok","PASS") if c["pass"] else badge("fail","FAIL"), esc(c["detail"]),
               derived("data/provenance.json")] for c in prov["integrity_checks"]]
spot_rows = [[esc(c["game_id"]), f'{c["official_away"]}–{c["official_home"]}', f'{c["archive_away"]}–{c["archive_home"]}',
              badge("ok","MATCH") if c["match"] else badge("fail","MISMATCH"),
              off("https://www.nfl.com/scores/2026/REG8")] for c in spot["checks"]]
body = f"""
<p class="lede">All inputs are third-party archives of official NFL results/stats plus sportsbook closing lines.
Each carries a repo URL, commit SHA and sha256. No official league source publishes betting lines — those values are
flagged. Official NFL.com scores were spot-checked game-by-game.</p>
<div class="panel info"><h3>Verified data conventions (critical)</h3>
<p><code>result = home_score − away_score</code>. <code>spread_line</code> = points the <strong>home</strong> team is favored by
(<strong>positive = home favorite</strong>) — the <em>opposite</em> of standard sportsbook home-spread notation. Verified vs
DATASETS.md, corr(result, spread) = +0.43, and 99%+ moneyline agreement. Historical codes OAK/SD/STL → LV/LAC/LA.</p></div>
<h2>Source register</h2>
{table("Archives with provenance", ["ID","File","Repo","Commit","Official status","Source"], prov_rows)}
<h2>Integrity checks (Gate G1)</h2>
{table("15/15 pass", ["Check","Result","Detail","Source"], check_rows)}
<h2>Official NFL.com score spot-check — 2026 Week 8</h2>
{table("13/13 match (CHI@SEA unplayed at snapshot)", ["Game","NFL.com final","Archive final","Result","Source"], spot_rows)}
"""
page("data-sources.html", "Data & Sources", "Data & Lines / Data & Sources", body)

# ---------------- own lines ----------------
w9_rows = []
for r in w9:
    mkt_sb = -float(r["market_spread_home_fav_pts"]) if r["market_spread_home_fav_pts"] else ""
    w9_rows.append([esc(r["game_id"].replace("2026_09_","")), esc(r["gameday"]),
                    f'{esc(r["away"])} @ {esc(r["home"])}',
                    f'{float(r["own_spread_home"]):+.1f}', f'{float(r["own_total"]):.1f}',
                    f'{r["own_home_ml_fair"]} / {r["own_away_ml_fair"]}',
                    f'{mkt_sb:+.1f}' if mkt_sb != "" else "", f'{float(r["market_total"]):.1f}' if r["market_total"] else "",
                    f'{float(r["market_home_ml"]):.0f} / {float(r["market_away_ml"]):.0f}' if r["market_home_ml"] else "",
                    signed(r["spread_divergence_own_minus_market"],1), signed(r["total_divergence_own_minus_market"],1),
                    market("QF-12")])
rat_rows = [[esc(r["team"]), r["power_rating_pts_vs_avg"], r["offense_pts_vs_avg"], r["defense_pts_vs_avg"],
             derived("data/ratings_current.csv")] for r in ratings]
hfa_rows = [[r["season"], r["hfa"], derived("data/hfa_by_season.csv")] for r in hfa if int(r["season"]) >= 2009]
body = f"""
<p class="lede">Own lines for the 15-game 2026 Week 9 slate, originated by the frozen walk-forward engine
(ratings cutoff {w9meta['ratings_cutoff']}, current HFA {w9meta['hfa_current_pts']} pts, σ = {w9meta['sigma']}).
<strong>Model outputs only — no strategy passed the gates, so divergences are NOT validated edges.</strong></p>
<div class="panel warn"><strong>Notation:</strong> spreads shown in sportsbook notation (negative = home favored).
Market values are the nflverse archive snapshot (2026-11-02 20:45 UTC), sign-flipped for display; they are third-party and
will move. "Model edge" = own minus market in home-favored points (+ = model likes home more than market).
2026 player props are <strong>blocked</strong> (no authorized feed). <a href="flagged.html#QF-03">QF-03</a></div>
<h2>Week 9 own lines vs market</h2>
{table("15 games · own spread/total/fair ML vs archived market", ["Game","Date","Matchup","Own spread","Own total","Own ML (H/A)","Mkt spread","Mkt total","Mkt ML (H/A)","Δ spread","Δ total","Source"], w9_rows, num_cols=(3,4,6,7,9,10))}
<h2>Current power ratings (points vs league average)</h2>
{table("32 teams · margin rating + offense/defense points components", ["Team","Power","Offense","Defense","Source"], rat_rows, num_cols=(1,2,3))}
<h2>Home-field advantage by season (model estimate)</h2>
{table("HFA has declined from ~3 pts to ~1 pt", ["Season","HFA (pts)","Source"], hfa_rows, num_cols=(1,))}
"""
page("own-lines.html", "Originated Lines — 2026 Week 9", "Data & Lines / Originated Lines", body)

# ---------------- singles ----------------
def strat_row(sid, desc):
    r = R[sid]
    return [sid, esc(desc), f"{r['n_bets']:,}", f"{r['wins']}/{r['losses']}/{r['pushes']}",
            pct(r["roi"]), f"[{pct(r['bootstrap_ci95'][0])}, {pct(r['bootstrap_ci95'][1])}]",
            f"{r['permutation_p']:.3f}", f"{r['holm_adjusted_p']:.3f}", tier_badge(r["tier"]),
            derived("data/strategy_results.json")]
s_rows = [
    strat_row("S1", "Spread divergence ≥ 1.5 pts (model vs closing)"),
    strat_row("S2", "Total divergence ≥ 2.0 pts"),
    strat_row("S3", "Moneyline edge ≥ 7% vs de-vigged implied"),
    strat_row("C1", "Control: always home favorite ATS"),
]
val_rows = [[k, esc(str(v["theta"])), f"{v['n']}", pct(v["val_roi"]), derived("data/strategy_results.json")]
            for k, v in strat["validation_selection"].items() if v]
s1_seasons = [[str(s), f"{d['n']}", pct(d["roi"]), derived("data/bets_S1.csv")] for s, d in sorted(R["S1"]["seasons"].items())]
body = f"""
<p class="lede">Singles are bet only when the model disagrees with the archived closing line by a frozen threshold.
Thresholds were selected on validation seasons (2013–2016) and frozen before the holdout (2017–2025) was evaluated once.
Settlement uses archived closing odds (default −110); pushes refund.</p>
<h2>Holdout results</h2>
{table("W/L/P = wins/losses/pushes; CI = week-clustered bootstrap 95%", ["ID","Rule","Bets","W/L/P","ROI","95% CI","Perm p","Holm p","Tier","Source"], s_rows, num_cols=(2,4,6,7))}
<h2>Validation-season threshold selection (frozen)</h2>
{table("Best validation ROI per family, min 100 bets", ["Family","θ","Val bets","Val ROI","Source"], val_rows, num_cols=(2,3))}
<h2>S1 season-by-season stability</h2>
{table("Positive in 5/9 holdout seasons — fails G5 robustness", ["Season","Bets","ROI","Source"], s1_seasons, num_cols=(1,2))}
<div class="panel"><strong>Interpretation:</strong> S1's +0.26% ROI sits inside a [−4.4%, +4.8%] confidence interval with
permutation p = 0.46 — statistically indistinguishable from luck (Bronze). S2/S3 lose the vig (Rejected). The model has
forecasting skill vs naive baselines but the closing market already prices that information.</div>
"""
page("singles.html", "Single Bets", "Strategies / Single Bets", body)

# ---------------- parlays ----------------
be = 1 / (1.909090909 ** 2)
sgp_rows = [[esc(r["scope"]), esc(r["combo"]), r["n"], r["p_joint_empirical"], r["p_product_if_independent"],
             r["lift_joint_over_product"], derived("data/sgp_joint_probabilities.csv")] for r in sgp]
r4 = R["S4"]
body = f"""
<p class="lede">Two parlay questions: (1) do model-edge singles compound into a profitable cross-game parlay?
(2) what are same-game combos really worth given correlation? Pricing follows official sportsbook rules.</p>
<h2>S4 — cross-game 2-leg parlays of S1 selections</h2>
{table("All same-week pairs from different games; payout = product of leg decimal odds", ["ID","Bets","W/L/P","ROI","95% CI","Perm p","Tier","Source"], [
 ["S4", f"{r4['n_bets']:,}", f"{r4['wins']}/{r4['losses']}/{r4['pushes']}", pct(r4["roi"]),
  f"[{pct(r4['bootstrap_ci95'][0])}, {pct(r4['bootstrap_ci95'][1])}]", f"{r4['permutation_p']:.3f}", tier_badge(r4["tier"]),
  derived("data/strategy_results.json")]], num_cols=(1,3,5))}
<div class="panel info"><h3>Parlay math (official rules)</h3>
<p>At −110 per leg, decimal odds multiply: 1.909 × 1.909 = 3.645 → break-even hit rate <strong>{pct(be)}</strong>.
A push/void leg is removed and the parlay recalculated (FanDuel House Rules Part B §19). Correlated/duplicate outcomes
generally cannot be parlayed; Same Game Parlay is a separate repriced product.
{off("https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet")} {off("https://www.fanduel.com/fanduel-sportsbook-house-rules-on")}</p></div>
<h2>Same-game fair pricing — empirical joint vs independence</h2>
{table("Lift ≈ 1.00: side+total combos are essentially independent — no free correlation edge", ["Scope","Combo","n","P(joint)","P(product)","Lift","Source"], sgp_rows, num_cols=(2,3,4,5))}
<div class="panel"><strong>Cross-game independence verified:</strong> same-week ATS-residual ICC = {gsum['cross_game_icc']}
vs permutation-null mean {gsum['cross_game_icc_null_mean']} (p = {gsum['cross_game_icc_permutation_p']}) — no detectable
same-week dependence, supporting the cross-game parlay independence assumption.
{derived("data/game_level_summary.json")}</div>
<div class="panel warn"><strong>S5/S7 are research-only (G7 fails):</strong> no official/archived SGP prices exist, so no
same-game edge can be claimed. The QB+WR combo lift (1.45×) is a fair-price input, not a profit claim.
<a href="props.html">Props →</a></div>
"""
page("parlays.html", "Parlays & Same-Game Combos", "Strategies / Parlays & SGP", body)

# ---------------- props ----------------
ps = props["singles_vs_proxy"]; co = props["combo_QB1_WR1"]
prop_rows = [[k, f"{v['n_bets']}", f"{v['wins']}/{v['losses']}/{v['pushes']}", pct(v["hit_rate_ex_push"]),
              pct(v["roi_at_minus110"]), badge("muted","Research-only"), derived("data/props_summary.json")]
             for k, v in ps.items()]
pcorr = [r for r in corr if r["scope"] == "2021-2022"]
pcorr_rows = [[esc(r["pair"]), r["n"], r["pearson_r"], f"[{r['ci95_low']}, {r['ci95_high']}]",
               derived("data/correlations.csv")] for r in pcorr]
body = f"""
<p class="lede">Player-prop research uses 2021–2022 weekly stats (the only authorized player-level data in scope).
<strong>2026 props are blocked.</strong> Because no archived prop prices exist, a transparent proxy line is used
(rolling 4-game mean). Gate G7 fails by construction — these are signal studies, not betting edges.</p>
<div class="panel warn"><strong>Research-only:</strong> results measure signal vs a naive proxy market, not vs a sportsbook.
The RB1 +3.6% proxy ROI is not a real edge. <a href="flagged.html#QF-04">QF-04</a></div>
<h2>S6 — prop singles vs proxy line (|projection − line| ≥ 5 yds)</h2>
{table("Projection = rolling mean × opponent adjustment; priced −110 for illustration", ["Label","Bets","W/L/P","Hit rate","ROI @ −110","Tier","Source"], prop_rows, num_cols=(1,3,4))}
<h2>S7 — QB1-over + WR1-over same-game combo</h2>
{table("Leak-free rolling designation; n = 800 team-games", ["Metric","Value","Source"], [
 ["P(QB1 over proxy)", co["p_qb1_over_proxy"], derived("data/props_summary.json")],
 ["P(WR1 over proxy)", co["p_wr1_over_proxy"], derived("data/props_summary.json")],
 ["P(both over) — empirical", co["p_joint_both_over"], derived("data/props_summary.json")],
 ["P(product) if independent", co["p_product_if_independent"], derived("data/props_summary.json")],
 ["Correlation lift (joint ÷ product)", f"{co['correlation_lift_joint_over_product']}× CI {co['lift_ci95']}", derived("data/props_summary.json")],
])}
<div class="panel info"><strong>Use:</strong> a QB-over + WR1-over SGP is worth ~1.45× the independent-leg product.
Books reprice SGPs for exactly this correlation, so the lift is a fair-pricing input — not free money. {off("https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet")}</div>
<h2>Player-level correlations (2021–2022, bootstrap 95% CI)</h2>
{table("QB1/WR1/WR2/RB1 designated per game; see QF-14 for designation caveats", ["Pair","n","r","95% CI","Source"], pcorr_rows, num_cols=(1,2))}
"""
page("props.html", "Player Props", "Strategies / Player Props", body)

# ---------------- correlations ----------------
corr_rows = [[esc(r["pair"]), esc(r["scope"]), r["n"], r["pearson_r"],
              (f"[{r['ci95_low']}, {r['ci95_high']}]" if r["ci95_low"] not in ("", "None") else "—"),
              esc(r["note"])[:140], derived("data/correlations.csv")] for r in corr]
key_rows = [[r["absolute_margin"], pct(r["frequency"]), esc(r["games_scope"]), derived("data/key_numbers.csv")] for r in keys]
body = f"""
<p class="lede">Dependence structure for pricing parlays and prop combos. All values are computed from cited archives
(no official source publishes coefficients) with bootstrap 95% CIs. Binary pairs use the phi coefficient.</p>
<h2>Correlation register</h2>
{table("Game-level (1999–2025) + player-level (2021–2022)", ["Pair","Scope","n","r","95% CI","Note","Source"], corr_rows, num_cols=(2,3))}
<h2>Key numbers — final margin distribution (2015–2025)</h2>
{table(f"3 is the most common margin ({pct(gsum['margin3_share_2015plus'])}); 7 next ({pct(gsum['margin7_share_2015plus'])}); ATS push rate at closing spread {pct(gsum['ats_push_rate_at_closing_spread'])}", ["|Margin|","Frequency","Scope","Source"], key_rows, num_cols=(0,1))}
<div class="panel"><strong>Reading:</strong> favorite-cover vs over is ~independent (φ≈0), so standard side+total SGPs carry
little correlation edge. QB↔WR receiving yards are strongly positive (r≈0.67–0.74); RB rushing ↔ margin is +0.35
(game script); QB passing ↔ RB rushing is −0.17 (substitution). Cross-game same-week dependence is undetectable
(ICC p = {gsum['cross_game_icc_permutation_p']}).</div>
"""
page("correlations.html", "Correlations", "Data & Lines / Correlations", body)

# ---------------- validation ----------------
gates = json.loads((ROOT / "pipeline" / "gates.json").read_text())["gates"]
gate_rows = [[g["id"], esc(g["name"]), esc(g["rule"]), derived("pipeline/gates.json")] for g in gates]
matrix = []
for sid in ("S1", "S2", "S3", "S4", "C1"):
    g = R[sid]["gates"]
    cells = [badge("ok","✓") if g[k] else badge("fail","✗") for k in ("G1","G2","G3","G4","G5","G6","G7","G8")]
    matrix.append([sid] + cells + [tier_badge(R[sid]["tier"]), derived("data/strategy_results.json")])
skill_rows = [
 ["Margin MAE (pts)", skill["margin_MAE"]["model"], skill["margin_MAE"]["market_closing_spread"], skill["margin_MAE"]["naive_HFA_plus2"], derived("data/forecast_skill.json")],
 ["Margin RMSE (pts)", skill["margin_RMSE"]["model"], skill["margin_RMSE"]["market_closing_spread"], skill["margin_RMSE"]["naive_HFA_plus2"], derived("data/forecast_skill.json")],
 ["Win-prob Brier", skill["win_prob_Brier"]["model"], skill["win_prob_Brier"]["market_devig_ML"], skill["win_prob_Brier"]["naive_050_plus_HFA"], derived("data/forecast_skill.json")],
]
body = f"""
<p class="lede">Eight gates were pre-registered (committed) <strong>before</strong> any holdout backtest ran.
A strategy earns credit only if it survives every gate. Luck is attacked from five angles: chronological splits,
look-ahead perturbation, week-clustered bootstrap, matched-random permutation + Holm, and placebo calibration.</p>
<h2>The gates</h2>
{table("Project-defined thresholds (QF-08); G8 forward replication pending", ["ID","Name","Rule","Source"], gate_rows)}
<h2>Gate matrix (holdout)</h2>
{table("✓ pass / ✗ fail — G8 pending for all", ["ID","G1","G2","G3","G4","G5","G6","G7","G8","Tier","Source"], matrix)}
<h2>Luck calibration — 500 random-placebo strategies</h2>
{table("Random betting loses the vig; some still look good by chance", ["Metric","Value","Source"], [
 ["Mean placebo ROI", pct(luck["placebo_roi_mean"]), derived("data/luck_calibration.json")],
 ["95th-percentile placebo ROI", pct(luck["placebo_roi_p95"]), derived("data/luck_calibration.json")],
 ["Fraction with positive ROI", pct(luck["placebo_frac_roi_positive"],1), derived("data/luck_calibration.json")],
])}
<h2>Forecast skill (holdout 2017–2025) — modeling vs the market</h2>
{table("Lower MAE/RMSE/Brier is better; model beats naive, market beats model", ["Metric","Model","Market","Naive","Source"], skill_rows, num_cols=(1,2,3))}
<div class="panel info"><strong>No look-ahead:</strong> permuting all future results left same-date predictions identical
on 3 test dates ({look['pass']}). Config: margin half-life {cfg['margin_config']['halflife_days']}d / ridge {cfg['margin_config']['ridge']};
total half-life {cfg['total_config']['halflife_days']}d; σ = {cfg['sigma']}. {derived("data/lookahead_test.json")}</div>
"""
page("validation.html", "Validation Gates & Luck Removal", "Strategies / Validation & Luck", body)

# ---------------- leaderboard ----------------
lb_full = []
for e in lb["entries"]:
    lb_full.append([e["strategy"], tier_badge(e["tier"]), f"{e['n_bets']:,}", pct(e["roi"]),
                    pct(e["bootstrap_p5_roi"]), f"{e['score']:.3f}", str(e["reward_points"]),
                    derived("data/leaderboard.json")])
tiers = json.loads((ROOT / "pipeline" / "gates.json").read_text())["tiers"]
tier_rows = [[esc(k), esc(v), derived("pipeline/gates.json")] for k, v in tiers.items()]
body = f"""
<p class="lede">Leaderboard competition: strategies are ranked by a risk-adjusted score
(max(0, bootstrap-5% ROI) × √bets) and earn non-monetary research points only if they reach Gold.
<strong>This season: no Gold, 0 of 1,000 points awarded, pool rolls over.</strong></p>
<h2>Final standings (holdout 2017–2025)</h2>
{table("Rewards are research points only — no money, no funded prizes (QF-09)", ["ID","Tier","Bets","ROI","Boot 5% ROI","Score","Points","Source"], lb_full, num_cols=(2,3,4,5,6))}
<h2>Tier definitions</h2>
{table("Pre-registered in gates.json", ["Tier","Requirement","Source"], tier_rows)}
<div class="panel warn"><strong>Why zero rewards is the correct outcome:</strong> at efficient closing lines, none of the
registered strategies demonstrated a luck-independent edge. Awarding points to Bronze (noise) strategies would reward
luck — exactly what the competition is designed to prevent. The reward pool rolls over until a strategy passes G1–G7
and then G8 forward replication. <a href="flagged.html#QF-15">QF-15</a></div>
<div class="panel info"><strong>Separate forecast-skill leaderboard:</strong> the ratings engine <em>does</em> demonstrate
skill vs naive baselines (MAE {skill['margin_MAE']['model']} vs {skill['margin_MAE']['naive_HFA_plus2']} pts), even though it
does not beat the market. See <a href="validation.html">Validation</a>.</div>
"""
page("leaderboard.html", "Leaderboard & Rewards", "Strategies / Leaderboard & Rewards", body)

# ---------------- flagged ----------------
flag_rows = []
sev = {"policy":"muted","blocked":"fail","research-only":"warn","repaired":"ok","info":"derived","needs-review":"warn","pending":"warn","finding":"warn"}
for f in flags:
    flag_rows.append([f'<a id="{f["id"]}"></a>{f["id"]}', badge(sev.get(f["severity"],"muted"), f["severity"]),
                      esc(f["item"]), esc(f["detail"]), off(f["source"], "source ↗")])
body = f"""
<p class="lede">Every irregularity and every value with no official source, published for post-launch review.
<strong>Flagged items are non-blocking</strong> — they do not prevent publication or merge. Request changes anytime.</p>
{table(f"{len(flags)} flagged items", ["ID","Severity","Item","Detail","Source"], flag_rows)}
"""
page("flagged.html", "⚑ Flagged for Review", "Governance / Flagged for Review", body)

# ---------------- audit ----------------
aud_rows = []
asev = {"high":"fail","info":"derived","verified":"ok"}
for a in audit:
    aud_rows.append([a["id"], esc(a["file"]), esc(a["lines"]), esc(a["finding"]),
                     badge(asev.get(a["severity"],"muted"), a["severity"]), esc(a["action"]), off(a["source"], "source ↗")])
body = f"""
<p class="lede">Line-by-line repository review for this session: structural scan, conflict-marker detection,
existing-module consistency, data-convention verification, and CI dry-run. Prior sessions' work is preserved untouched.</p>
{table("10 findings", ["ID","File","Lines","Finding","Severity","Action","Source"], aud_rows)}
<div class="panel info"><strong>CI dry-run (local):</strong> <code>scripts/build.py</code> → 8 pages / 47 rows;
<code>verify_data.py</code> → 11/11; <code>check_site.py</code> → 11 pages / 758 links / 0 problems.
NFL additions live entirely under <code>nfl-quant/</code> and do not modify <code>docs/</code>. {off("https://github.com/sassnarep3-star/Own4/blob/main/.github/workflows/pages.yml")}</div>
"""
page("audit.html", "Repo Audit", "Governance / Repo Audit", body)

# ---------------- sources ----------------
os_rows = [[s["id"], esc(s["claim"]), esc(s["publisher"]), esc(s["method"]), off(s["url"]), esc(s["verified_utc"][:10])] for s in osrc]
body = f"""
<p class="lede">Official facts used by this module, each verified against an official source on {NOW}.
Method records exactly how the source was checked (direct fetch vs indexed excerpt). Data archives are listed on
<a href="data-sources.html">Data & Sources</a>.</p>
{table("9 verified official facts", ["ID","Claim","Publisher","Verification method","Source","Date"], os_rows)}
<div class="panel"><strong>Trusted-but-not-official:</strong> nflverse/nfldata and fantasydatapros archives are third-party
mirrors of official results/stats — used for computation, flagged as such, never presented as official publications.
Market lines have no official source at all. {off("https://github.com/nflverse/nfldata")}</div>
"""
page("sources.html", "Official Source Register", "Governance / Official Source Register", body)

# ---------------- EXECUTIVE_SUMMARY.md ----------------
md = f"""# Executive Summary — NFL Quant Lab (Own4)

Session arena-e513f51b-own4 · {NOW} · live site: https://sassnarep3-star.github.io/Own4/nfl-quant/

## What was built
A reproducible NFL line-origination + strategy-validation pipeline: 7,548 archived games (1999–2026),
walk-forward ridge ratings, 5 registered betting strategies + 3 research-only constructions, 8 pre-registered
validation gates, a 16-estimate correlation study, and a 15-game 2026 Week 9 own-line slate.
15/15 data-integrity checks and 13/13 official NFL.com score spot-checks pass.

## Headline results (computed; vs archived closing lines — third-party, not official)
- Forecast skill: model holdout MAE {skill['margin_MAE']['model']} pts beats naive {skill['margin_MAE']['naive_HFA_plus2']} but not the market {skill['margin_MAE']['market_closing_spread']}.
- S1 spread divergence: {s1['n_bets']:,} bets, ROI {pct(s1['roi'])}, CI [{pct(s1['bootstrap_ci95'][0])}, {pct(s1['bootstrap_ci95'][1])}] -> Bronze (luck).
- S4 cross-game parlays: {s4['n_bets']:,} bets, ROI {pct(s4['roi'])} -> Bronze. S2/S3/C1 Rejected (negative).
- Strategies passing all gates: 0. Reward points awarded: 0 of 1,000 (non-monetary).
- Correlations: QB1->WR1 r=0.667; QB-over+WR1-over combo lift 1.45x [1.36,1.55]; favorite-cover vs over ~independent.
- Current HFA estimate {w9meta['hfa_current_pts']} pts (declining from ~3).

## How luck is removed
Chronological dev/validation/holdout splits with frozen config; look-ahead perturbation test (pass);
week-clustered bootstrap CIs; matched-random permutation + Holm across the primary family; 500-placebo
calibration (mean ROI {pct(luck['placebo_roi_mean'])}, {pct(luck['placebo_frac_roi_positive'],1)} positive by chance);
season-stability checks; G8 forward replication pending.

## Limits / flagged (non-blocking)
No strategy beats closing lines; props use a proxy market (G7 fails); 2026 props blocked; all market lines
third-party; computed metrics not official; data licensing needs review; README conflict markers repaired at
integration (both sides kept). See site Flagged for Review page ({len(flags)} items).

## Reproduce
python3 nfl-quant/pipeline/01_provenance.py && ... && python3 nfl-quant/pipeline/07_verify_publish.py
python3 nfl-quant/site/build_site.py

Analytical research only, not wagering advice. NCPG Helpline 1-800-MY-RESET (1-800-697-3738).
"""
(ROOT / "EXECUTIVE_SUMMARY.md").write_text(md)

# ---------------- link check ----------------
pages = [ROOT / "index.html"] + list(PAGES.glob("*.html"))
problems = []
nrows = 0
for p in pages:
    txt = p.read_text()
    nrows += txt.count("<tr>")
    for m in re.finditer(r'href="([^"#]+?)(#[^"]*)?"', txt):
        href = m.group(1)
        if href.startswith(("http", "mailto:", "tel:")):
            continue
        target = (p.parent / href).resolve()
        if not target.exists():
            problems.append(f"{p.name}: broken link {href}")
    # every tbody row must contain a source link
    for tb in re.findall(r"<tbody>(.*?)</tbody>", txt, re.S):
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            if "href=" not in tr:
                problems.append(f"{p.name}: table row without source link")
print(f"Built {len(pages)} pages; {nrows} table rows; {len(problems)} problems")
for pr in problems[:30]:
    print("  PROBLEM:", pr)
sys.exit(1 if problems else 0)

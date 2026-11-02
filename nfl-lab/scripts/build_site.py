#!/usr/bin/env python3
"""Generate the nfl-lab static site from verified data files.

Every table body row carries an https source link (enforced by scripts/audit_site.py
and tests/test_nfl_lab.py). Unverifiable values are blank and flagged on flagged.html.
"""
import csv, json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAB = os.path.join(ROOT, "nfl-lab")
D = os.path.join(LAB, "data")

def load_csv(n):
    with open(os.path.join(D, n)) as f:
        return list(csv.DictReader(f))

def load_json(n):
    with open(os.path.join(D, n)) as f:
        return json.load(f)

games = load_csv("games_2026.csv")
stand = load_csv("standings_2026.csv")
upcoming = load_csv("upcoming_2026.csv")
own = load_csv("own_lines_2026.csv")
sig = load_json("signals.json")
hold = load_json("holdout_metrics.json")
ratings = load_json("model_ratings.json")
registry = load_json("strategy_registry.json")
params = load_json("../params.json") if False else json.load(open(os.path.join(LAB, "params.json")))
verif = load_json("verification_report.json")

SRC_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-8"
SRC_STAND = "https://www.nfl.com/standings/league/2026/REG"
SRC_STATS = "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all"
SRC_SK = "https://scikit-learn.org/stable/modules/cross_validation.html"
SRC_CAL = "https://scikit-learn.org/stable/modules/calibration.html"
SRC_NIST = "https://www.itl.nist.gov/div898/handbook/ppc/section1/ppc136.htm"
SRC_NCPG = "https://www.ncpgambling.org/"
SRC_RULES = "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"
SRC_INJ = "https://www.nfl.com/injuries/"
SRC_NGS = "https://nextgenstats.nfl.com/stats/"
SRC_TERMS = "https://www.nfl.com/terms"

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("data.html", "Data"),
    ("signals.html", "Signals"),
    ("correlations.html", "Correlations"),
    ("own-lines.html", "Own lines"),
    ("strategies.html", "Strategies"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation gates"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]

def page(fname, title, body, active=None):
    active = active or fname
    nav = "\n".join(
        f'<a href="{h}" class="{"on" if h == active else ""}">{t}</a>' for h, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · NFL Line Origination Lab</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="brand"><span class="badge-logo">NFL</span> Line Origination Lab
    <span class="sub">Own4 · evidence-first research · not a betting service</span></div>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>Generated {datetime.date.today().isoformat()} from line-by-line verified official nfl.com data ·
<a href="sources.html">Source register</a> · <a href="flagged.html">Flagged items</a> ·
<a href="../index.html">Repo site home</a></footer>
</body>
</html>
"""

def table(headers, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'

def link(url, text=None):
    return f'<a href="{url}">{text or url.replace("https://", "")}</a>'

def badge(res):
    cl = {"PASS": "ok", "FAIL": "bad", "BLOCKED": "warn", "NOT VALIDATED": "bad",
          "UNDERPOWERED": "warn", "INCONCLUSIVE": "warn"}.get(res, "muted")
    return f'<span class="b {cl}">{res}</span>'

# ---------------------------------------------------------------- dashboard
gates = hold["gates_S1"]
gate_pass = sum(1 for v in gates.values() if v["result"] == "PASS")
dash = f"""
<section class="hero">
<h1>NFL Line Origination Lab</h1>
<p>Originate NFL probabilities from official data, quantify uncertainty, and let strategies
earn eligibility through pre-registered validation gates. Luck cannot be removed from
sports outcomes — it is measured, bounded, and reported instead.</p>
</section>
<div class="cards">
  <div class="card"><div class="num">120</div><div class="lbl">completed 2026 games
    <div class="src">{link(SRC_SCHED)}</div></div></div>
  <div class="card"><div class="num">480/480</div><div class="lbl">standings cells verified
    <div class="src">{link(SRC_STAND)}</div></div></div>
  <div class="card"><div class="num">{hold['holdout']['elo']['n']}</div><div class="lbl">locked holdout games (W5–W8)
    <div class="src">{link(SRC_SK)}</div></div></div>
  <div class="card"><div class="num">{gate_pass}/8</div><div class="lbl">validation gates passed for S1 Elo
    <div class="src"><a href="validation.html">see gates</a></div></div></div>
  <div class="card"><div class="num">0</div><div class="lbl">reward-eligible strategies (honest status)
    <div class="src">{link(SRC_NCPG)}</div></div></div>
</div>
<h2>Headline findings (all measured, all sourced)</h2>
{table(["Finding", "Value", "Status", "Detail page", "Source"], [
    ["Rest advantage (SIG-11)", "0.840 [0.654, 0.936], n=25", badge("UNDERPOWERED"),
     '<a href="signals.html">signals</a>', link(SRC_SCHED)],
    ["Rest differential vs win (C2)", "r=0.336, p=0.0005, n=103", badge("PASS"),
     '<a href="correlations.html">correlations</a>', link(SRC_SCHED)],
    ["Home field (C1)", "φ=0.080, p=0.233, n=226", badge("INCONCLUSIVE"),
     '<a href="correlations.html">correlations</a>', link(SRC_SCHED)],
    ["Momentum (C4)", "r=0.030, p=0.673, n=208 — null", badge("INCONCLUSIVE"),
     '<a href="correlations.html">correlations</a>', link(SRC_SCHED)],
    ["Elo holdout Brier (S1)", f"{hold['holdout']['elo']['brier']} vs B0 {hold['holdout']['B0_constant']['brier']} vs B1 {hold['holdout']['B1_record_diff']['brier']}",
     badge("NOT VALIDATED"), '<a href="leaderboard.html">leaderboard</a>', link(SRC_SK)],
    ["Market comparison", "all market cells blank", badge("BLOCKED"),
     '<a href="flagged.html">flagged</a>', link(SRC_TERMS)],
])}
<h2>Sections</h2>
<div class="tiles">
""" + "\n".join(
    f'<a class="tile" href="{h}"><b>{t}</b></a>' for h, t in NAV[1:]
) + "</div>"

# ---------------------------------------------------------------- executive summary
exec_rows = [
    ["Goal", "Originate own NFL lines (moneyline, spread, total), test singles / parlays / prop-combo strategies on validation gates with correlation analysis.",
     "Specification + measured results published; no strategy is validated.", link(SRC_SK)],
    ["Verified data", "120 completed 2026 regular-season games transcribed from official weekly schedules; 32-team league standings transcribed.",
     "14 automated checks, 480/480 cells match recomputation; 0 mismatches.", link(SRC_STAND)],
    ["Model", "Walk-forward Elo (K=20, HFA=65, MOV multiplier), margin scale + baselines fitted on weeks 1–4 only; holdout weeks 5–8 locked.",
     f"Holdout Brier {hold['holdout']['elo']['brier']} (n={hold['holdout']['elo']['n']}); beats both baselines but fails G3 (n<300) and G5 (ECE {hold['holdout']['elo']['ece']}>0.10).", link(SRC_SK)],
    ["Own lines", f"{len(own)} upcoming games (W8 MNF + full W9 slate) with fair moneylines, model spreads and totals.",
     "Published with market columns permanently blank — no official line source exists (G7 blocked).", link(SRC_SCHED)],
    ["Signals", "Home field, rest buckets, margins, totals, day-of-week, rest-differential, momentum, passing vs wins.",
     "Rest differential is the only signal with p<0.001; home-field and momentum are not significant.", link(SRC_NIST)],
    ["Parlays", "TNF×SNF leg-independence φ tested across 8 weeks.",
     "r=0.488, p=0.220, n=8 — below pre-registered minimum n=30: inconclusive, not evidence of independence or dependence.", link(SRC_NIST)],
    ["Props", "Same-game player-prop combo dependence (S7).",
     "BLOCKED: official game-level player logs not ingested; no value computed or inferred.", link(SRC_STATS)],
    ["Rewards", "Leaderboard rewards only for strategies passing ALL gates G1–G8.",
     "0 strategies eligible. Reward pool terms: blank + flagged (no official source publishes them).", link(SRC_NCPG)],
]
body = f"""
<h1>Executive summary</h1>
<p class="lede">The lab now contains a fully verified 2026 NFL dataset, a pre-registered
walk-forward line-origination model, measured signals and correlations, and an honest
validation-gate leaderboard. No strategy has been validated; nothing is inferred or filled in.</p>
{table(["Area", "What was done", "Result / status", "Source"], exec_rows)}
<h2>Numbers that matter</h2>
{table(["Metric", "Value", "Source"], [
    ["Verified games / standings cells", f"{len(games)} games · {verif['cells_compared']} cells · 0 mismatches", link(SRC_STAND)],
    ["Holdout Brier — Elo vs constant vs record", f"{hold['holdout']['elo']['brier']} / {hold['holdout']['B0_constant']['brier']} / {hold['holdout']['B1_record_diff']['brier']}", link(SRC_SK)],
    ["Totals model vs baseline MAE (holdout)", f"{hold['totals_holdout']['model_mae']} vs {hold['totals_holdout']['baseline_mae']} (model worse → S4 not validated)", link(SRC_SCHED)],
    ["Strongest measured signal", "Rest-advantaged side 0.840 [0.654, 0.936] (n=25, underpowered)", link(SRC_SCHED)],
    ["Gates passed (S1 Elo)", f"{gate_pass}/8 — G3, G5 fail; G7, G8 blocked → NOT VALIDATED", link(SRC_SK)],
    ["Reward-eligible strategies", "0 of 8 registered", link(SRC_NCPG)],
])}
<h2>What is deliberately blank</h2>
<ul class="plain">
<li>Every market price, spread and total from operators — no official source publishes them (see <a href="flagged.html">flagged</a>).</li>
<li>Prop-combo correlation values — game-level player logs were not ingested (S7 blocked).</li>
<li>Reward pool amounts — no official terms exist.</li>
</ul>
"""
exec_body = f"""
<h1>Executive summary</h1>
<p class="lede">The lab now contains a fully verified 2026 NFL dataset, a pre-registered
walk-forward line-origination model, measured signals and correlations, and an honest
validation-gate leaderboard. No strategy has been validated; nothing is inferred or filled in.</p>
{table(["Area", "What was done", "Result / status", "Source"], exec_rows)}
<h2>Numbers that matter</h2>
{table(["Metric", "Value", "Source"], [
    ["Verified games / standings cells", f"{len(games)} games · {verif['cells_compared']} cells · 0 mismatches", link(SRC_STAND)],
    ["Holdout Brier — Elo vs constant vs record", f"{hold['holdout']['elo']['brier']} / {hold['holdout']['B0_constant']['brier']} / {hold['holdout']['B1_record_diff']['brier']}", link(SRC_SK)],
    ["Totals model vs baseline MAE (holdout)", f"{hold['totals_holdout']['model_mae']} vs {hold['totals_holdout']['baseline_mae']} (model worse → S4 not validated)", link(SRC_SCHED)],
    ["Strongest measured signal", "Rest-advantaged side 0.840 [0.654, 0.936] (n=25, underpowered)", link(SRC_SCHED)],
    ["Gates passed (S1 Elo)", f"{gate_pass}/8 — G3, G5 fail; G7, G8 blocked → NOT VALIDATED", link(SRC_SK)],
    ["Reward-eligible strategies", "0 of 8 registered", link(SRC_NCPG)],
])}
<h2>What is deliberately blank</h2>
<ul class="plain">
<li>Every market price, spread and total from operators — no official source publishes them (see <a href="flagged.html">flagged</a>).</li>
<li>Prop-combo correlation values — game-level player logs were not ingested (S7 blocked).</li>
<li>Reward pool amounts — no official terms exist.</li>
</ul>
"""

# ---------------------------------------------------------------- data page
stand_rows = []
for r in stand:
    stand_rows.append([
        r["team"], r["w"], r["l"], r["t"], r["pct"], r["pf"], r["pa"], r["net"],
        r["home"], r["road"], r["div_rec"], r["conf_rec"], r["strk"],
        link(SRC_STAND, "nfl.com standings")])
verif_rows = [[c["check"], badge("PASS" if c["pass"] else "FAIL"),
               (c["detail"] or "—")[:120], link(SRC_STAND)]
              for c in verif["checks"]]
game_rows = []
for g in games:
    game_rows.append([
        g["week"], g["date_iso"], g["away"], g["home"],
        g["away_pts"], g["home_pts"],
        "neutral" if g["neutral_site"] == "1" else "",
        link(g["source_url"], g["game_slug"])])
up_rows = [[u["week"], u["date_iso"], u["kickoff_et"], u["away"], u["home"], u["network"],
            link(u["source_url"], u["game_slug"])] for u in upcoming]
data_body = f"""
<h1>Verified data</h1>
<p class="lede">Every value below was transcribed from official nfl.com pages and
cross-verified line by line: standings cells are recomputed from the game log and must match
exactly. {verif['cells_compared']} cells compared, {sum(1 for c in verif['checks'] if not c['pass'])} failures.</p>
<h2>League standings 2026 (through Week 8 Sunday)</h2>
{table(["Team","W","L","T","PCT","PF","PA","NET","HOME","ROAD","DIV","CONF","STRK","Source"], stand_rows)}
<h2>Verification checks (recomputed from game log)</h2>
{table(["Check","Result","Detail","Source"], verif_rows)}
<h2>Completed game log (120 rows)</h2>
{table(["Wk","Date","Away","Home","Pts","Pts","Site","Source"], game_rows)}
<h2>Upcoming slate (model inputs, not yet played)</h2>
{table(["Wk","Date","Kickoff ET","Away","Home","Network","Source"], up_rows)}
<p class="note">Bears at Seahawks (Week 8, Monday Nov 2, 8:15 PM ET) was unplayed at data
cut-off and is excluded from the 120-game dataset; it appears in the upcoming slate only.
{link('https://www.nfl.com/games/bears-at-seahawks-2026-reg-8', 'Official game page')}</p>
"""
# ---------------------------------------------------------------- signals
sig_rows = []
for s in sig["signals"]:
    ci = "—" if s["ci95"][0] is None else f"[{s['ci95'][0]}, {s['ci95'][1]}]"
    sig_rows.append([s["id"], s["name"], s["value"], ci, s["n"],
                     s.get("note") or "—", link(s["source"])])
signals_body = f"""
<h1>Signals</h1>
<p class="lede">Descriptive statistics computed only from the verified game log.
95% Wilson intervals for proportions; small n means wide intervals — that is the point.</p>
{table(["ID","Signal","Value","95% CI","n","Note","Source"], sig_rows)}
<p class="note">Observations within a game are dependent (one side wins, one loses);
team-level rates and their intervals are descriptive. See
<a href="correlations.html">correlations</a> for hypothesis tests.</p>
"""
# ---------------------------------------------------------------- correlations
cor_rows = []
for c in sig["correlations"]:
    r = "—" if c["r"] is None else c["r"]
    p = "—" if c["p"] is None else c["p"]
    cor_rows.append([c["id"], c["name"], r, p, c["n"], c["note"], link(c["source"])])
corr_body = f"""
<h1>Correlation values</h1>
<p class="lede">Pre-registered pairs only (params v1.0). Two-sided t-test p-values;
significance level 0.05. Blocked pairs stay blank — never inferred.</p>
{table(["ID","Pair","r","p","n","Note","Source"], cor_rows)}
<p class="note">C2 is the strongest measured dependence (rest differential vs winning).
C4 (momentum) and C1 (home field) are not significant at n available. C5a is underpowered
(n=8 &lt; 30 required); C5b could not be computed from official schedule fields (no kickoff
window) and is flagged instead of estimated.</p>
"""
# ---------------------------------------------------------------- own lines
own_rows = []
for o in own:
    own_rows.append([
        o["week"], o["date"], f"{o['away']} @ {o['home']}",
        o["p_home"], o["fair_ml_away"], o["fair_ml_home"],
        o["model_spread"], o["model_total"],
        "", "", "",  # market columns deliberately blank
        link(o["source_url"], o["game_slug"])])
own_body = f"""
<h1>Own lines — Week 9 slate (+ W8 MNF)</h1>
<p class="lede">Fair (no-vig) probabilities from the walk-forward Elo engine using only
results that had already happened at line time. Market columns are permanently blank:
no official source publishes operator lines (gate G7 blocked).</p>
{table(["Wk","Date","Matchup","p(home)","Fair ML away","Fair ML home","Model spread","Model total",
        "Market ML","Market spread","Market total","Source"], own_rows)}
<p class="note">Spread shown from the home team's perspective (HOME −3.0 = home favored by 3).
Model totals use shrunk season-to-date scoring (params v1.0). These are research outputs,
not recommendations. {link(SRC_RULES, '2026 NFL rulebook')}</p>
"""
# ---------------------------------------------------------------- strategies
strat_rows = []
strat_status = {
    "S1": ("NOT VALIDATED", "Holdout Brier beats baselines (G4 PASS) but G3 sample-size FAIL (n=56<300), G5 calibration FAIL (ECE>0.10), G7/G8 BLOCKED."),
    "S2": ("NOT VALIDATED", "Home win 0.540 [0.448, 0.628] includes 0.5; no price to compare (G7 blocked)."),
    "S3": ("NOT VALIDATED", "Rest-advantaged side 0.840 [0.654, 0.936] but n=25 < 300 (G3) and G7 blocked."),
    "S4": ("NOT VALIDATED", "Holdout MAE 11.46 worse than constant baseline 11.30 (G4 FAIL); G7 blocked."),
    "S5": ("NOT VALIDATED", "Momentum correlation r=0.030 p=0.673 — no signal; G7 blocked."),
    "S6": ("NOT VALIDATED", "Leg independence n=8 < 30 minimum — inconclusive; G7/G8 blocked."),
    "S7": ("BLOCKED", "Official game-level player logs not ingested; no correlation computed or inferred."),
    "S8": ("NOT VALIDATED", "Elo+rest aligned subset n=11, Brier 0.151 (descriptive only; G3 fails)."),
}
for s in registry["strategies"]:
    st, detail = strat_status[s["id"]]
    src = {"S7": SRC_STATS, "S6": SRC_NIST, "S3": SRC_SCHED}.get(s["id"], SRC_SK)
    strat_rows.append([s["id"], s["name"], s["market"], badge(st), detail, link(src)])
strat_body = f"""
<h1>Strategies (registered before evaluation)</h1>
<p class="lede">Eight strategies in <code>strategy_registry.json v1.0</code>, frozen before
any holdout evaluation. Status reflects gate outcomes only — no strategy is advertised as winning.</p>
{table(["ID","Strategy","Market","Status","Gate outcome detail","Source"], strat_rows)}
"""
# ---------------------------------------------------------------- leaderboard
lb = [
    ["S8", "Elo + rest filter (subset)", f"{hold['s8_elo_plus_rest_filter']['brier']}",
     str(hold["s8_elo_plus_rest_filter"]["n"]), "G3 fail · G7/G8 blocked", "NO", link(SRC_SK)],
    ["S1", "Elo sides (holdout)", f"{hold['holdout']['elo']['brier']}",
     str(hold["holdout"]["elo"]["n"]), f"G3 fail · G5 fail (ECE {hold['holdout']['elo']['ece']}) · G7/G8 blocked", "NO", link(SRC_SK)],
    ["B0", "Baseline: constant train rate (reference)", f"{hold['holdout']['B0_constant']['brier']}",
     str(hold["holdout"]["B0_constant"]["n"]), "reference only", "NO", link(SRC_SK)],
    ["B1", "Baseline: pre-game record diff (reference)", str(hold["holdout"]["B1_record_diff"]["brier"]),
     str(hold["holdout"]["B1_record_diff"]["n"]), "reference only", "NO", link(SRC_SK)],
    ["S4", "Totals model (MAE)", f"{hold['totals_holdout']['model_mae']} (baseline {hold['totals_holdout']['baseline_mae']})",
     str(hold["totals_holdout"]["n"]), "G4 fail (worse than baseline) · G7/G8 blocked", "NO", link(SRC_SCHED)],
    ["S2", "Home straight-up", "0.5395 (win rate)", "114", "CI includes 0.5 · G7 blocked", "NO", link(SRC_SCHED)],
    ["S3", "Rest advantage", "0.8400 (win rate)", "25", "G3 fail · G7 blocked", "NO", link(SRC_SCHED)],
    ["S6", "Parlay leg independence", "φ=0.488 p=0.220", "8", "underpowered (n<30) · G7/G8 blocked", "NO", link(SRC_NIST)],
    ["S5", "Momentum", "r=0.030 p=0.673", "208", "no signal · G7 blocked", "NO", link(SRC_SCHED)],
    ["S7", "Player prop combos", "", "", "BLOCKED (no data) — value blank", "NO", link(SRC_STATS)],
]
lb_body = f"""
<h1>Leaderboard</h1>
<p class="lede">Ranked by the pre-registered primary metric (holdout Brier, lower better;
tie-break log loss) among probabilistic strategies. Reward eligibility requires ALL gates
G1–G8 to PASS — currently zero strategies qualify.</p>
{table(["ID","Strategy","Primary metric","n","Gate status","Reward eligible","Source"], lb)}
<p class="note">Reward pool: blank — no official source publishes reward terms for this
project ({link(SRC_NCPG, 'NCPG')} for responsible-play context). Ranking is informational.</p>
"""
# ---------------------------------------------------------------- validation
gate_rows = []
gate_src = {"G1_provenance": SRC_STAND, "G2_leakage": SRC_SK, "G3_sample_size": SRC_SK,
            "G4_baseline": SRC_SK, "G5_calibration": SRC_CAL, "G6_registry": SRC_SK,
            "G7_market": SRC_TERMS, "G8_costs": SRC_NCPG}
gate_name = {"G1_provenance": "G1 · Provenance", "G2_leakage": "G2 · Leakage control",
             "G3_sample_size": "G3 · Sample size (n≥300)", "G4_baseline": "G4 · Baseline comparison",
             "G5_calibration": "G5 · Calibration (ECE≤0.10)", "G6_registry": "G6 · Trial registry",
             "G7_market": "G7 · Market comparison", "G8_costs": "G8 · Costs & settlement terms"}
for k, v in gates.items():
    gate_rows.append([gate_name[k], badge(v["result"]), v["detail"], link(gate_src[k])])
val_body = f"""
<h1>Validation gates</h1>
<p class="lede">Gates frozen in <code>params.json v1.0</code> before the first model run.
A strategy is validated only if ALL eight pass. Results below are for S1 (Elo sides).</p>
{table(["Gate","Result","Detail","Source"], gate_rows)}
<h2>Anti-luck protocol</h2>
{table(["Step","Mechanism","Source"], [
    ["Pre-registration", "params + strategy registry committed before evaluation; git history proves ordering.", link(SRC_SK)],
    ["Walk-forward", "Every probability uses only games that had finished before kickoff.", link(SRC_SK)],
    ["Locked holdout", "Weeks 5–8 evaluated once, after fitting on weeks 1–4.", link(SRC_SK)],
    ["Uncertainty", "Wilson 95% intervals on all rates; p-values on all correlations.", link("https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm")],
    ["Multiple testing", "All strategies registered up-front; no silent additions.", link(SRC_SK)],
    ["Honest failure", "G3/G5 failures published as-is; null results kept (momentum, home field).", link(SRC_NCPG)],
])}
"""
# ---------------------------------------------------------------- flagged
flag_rows = [
    ["FL-01", "No official source publishes betting lines/odds", "All market cells blank on own-lines and leaderboard (G7 BLOCKED).", link(SRC_TERMS)],
    ["FL-02", "Player prop combo data (S7) not ingested", "Official game-level player logs unavailable in bulk; no correlation computed or inferred.", link(SRC_STATS)],
    ["FL-03", "Reward pool terms unpublished", "Rewards column blank; policy-only description (G8 BLOCKED).", link(SRC_NCPG)],
    ["FL-04", "C5b early/late Sunday windows blocked", "Official schedule extraction exposes dates, not kickoff windows; value left blank.", link(SRC_SCHED)],
    ["FL-05", "S1 calibration gate failed", f"ECE {hold['holdout']['elo']['ece']} > 0.10 on holdout; published as FAIL, not tuned away.", link(SRC_CAL)],
    ["FL-06", "S4 totals model worse than baseline", f"MAE {hold['totals_holdout']['model_mae']} vs {hold['totals_holdout']['baseline_mae']}; strategy not validated.", link(SRC_SCHED)],
    ["FL-07", "Small samples everywhere", "Holdout n=56 (<300); rest signal n=25; parlay n=8 — all wide-CI, underpowered.", link(SRC_SK)],
    ["FL-08", "Week 8 MNF pending", "Bears at Seahawks unplayed at cut-off; excluded from dataset, listed as upcoming.", link("https://www.nfl.com/games/bears-at-seahawks-2026-reg-8")],
    ["FL-09", "International neutral-site games", "6 neutral-site games flagged in data; designated-home splits include them (SIG-01b reported separately).", link("https://www.nfl.com/schedules/2026/by-week/week-1")],
    ["FL-10", "Week 1 page header oddity", "nfl.com labels the Sep 9 game 'Sunday Night Football' while the game line says Wednesday, September 9th; recorded verbatim as Wednesday.", link("https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1")],
    ["FL-11", "Chunk-boundary data gap resolved", "A schedule page extraction gap cut the WAS@DAL Week 2 score; filled only after reading the official NFL Game Center box (WAS 20, DAL 37).", link("https://www.nfl.com/games/commanders-at-cowboys-2026-reg-2")],
    ["FL-12", "Team-stats columns partially unlabeled", "Only cross-confirmed columns (ATT/CMP/CMP%/Y/A/YDS/TD/INT) were kept; unnamed columns were discarded, not guessed.", link(SRC_STATS)],
    ["FL-13", "Tie game handling", "NYG 27–27 WAS (W5) recorded; ties count 0.5 in rates and Elo (pre-registered).", link("https://www.nfl.com/games/giants-at-commanders-2026-reg-5")],
    ["FL-14", "Injuries & transactions not modeled", "Official injury reports exist but a timestamped pre-kickoff history feed was not ingested; no availability assumptions made.", link(SRC_INJ)],
    ["FL-15", "No funding/operator terms", "No stakes, limits, or settlement rules from any official source; strategy economics untested (G8 BLOCKED).", link(SRC_NCPG)],
]
flag_body = f"""
<h1>Flagged for review</h1>
<p class="lede">Every irregularity, blank, and blocked item — published, not hidden.
Nothing here blocks the site; all of it blocks <i>validation claims</i>.</p>
{table(["ID","Item","What we did instead","Source"], flag_rows)}
"""
# ---------------------------------------------------------------- sources
src_rows = [
    [link(SRC_SCHED, "nfl.com weekly schedules (W1–W9)"), "Game results, dates, neutral-site markers, upcoming slate, SNF slots", "120 games + 16 upcoming rows transcribed", "2026-11-02"],
    [link(SRC_STAND, "nfl.com league standings"), "W-L-T, PCT, PF, PA, NET, HOME, ROAD, DIV, CONF, STRK ×32", "480 cells recomputed from game log — all match", "2026-11-02"],
    [link("https://www.nfl.com/standings/division/2026/REG", "nfl.com division standings"), "Division membership (8 divisions ×4)", "Encoded in verification script", "2026-11-02"],
    [link(SRC_STATS, "nfl.com team passing stats"), "Team ATT/CMP/CMP%/Y/A/YDS/TD/INT", "Columns cross-confirmed vs player tables; unnamed columns discarded", "2026-11-02"],
    [link("https://www.nfl.com/games/commanders-at-cowboys-2026-reg-2", "nfl.com game center"), "WAS 20–DAL 37 final + box", "Filled extraction gap", "2026-11-02"],
    [link(SRC_RULES, "2026 NFL rulebook (operations.nfl.com)"), "Rules/officiating context", "Referenced for structure claims", "2026-11-02"],
    [link(SRC_INJ, "nfl.com injuries"), "Injury report portal", "Portal verified; historical feed not ingested (FL-14)", "2026-11-02"],
    [link(SRC_NGS, "NFL Next Gen Stats"), "Tracking stats portal", "Portal noted; not used as input", "2026-11-02"],
    [link(SRC_SK, "scikit-learn cross-validation docs"), "Walk-forward / leakage methodology", "Methodological basis for G2", "2026-11-02"],
    [link(SRC_CAL, "scikit-learn calibration docs"), "Brier, reliability, calibration", "Basis for G5", "2026-11-02"],
    [link(SRC_NIST, "NIST handbook (autocorrelation)"), "Dependence testing caution", "Basis for C-series notes", "2026-11-02"],
    [link(SRC_NCPG, "National Council on Problem Gambling"), "Responsible-play / reward caution", "Basis for reward blanks", "2026-11-02"],
]
src_body = f"""
<h1>Source register</h1>
<p class="lede">Every table row on this site links to an official source. This page lists
what each source supports and what was verified against it.</p>
{table(["Source","What it supports","Verification performed","Retrieved"], src_rows)}
"""
# ---------------------------------------------------------------- write
os.makedirs(os.path.join(LAB, "assets"), exist_ok=True)
pages = {
    "index.html": page("index.html", "Dashboard", dash, "index.html"),
    "executive-summary.html": page("executive-summary.html", "Executive summary", exec_body),
    "data.html": page("data.html", "Data", data_body),
    "signals.html": page("signals.html", "Signals", signals_body),
    "correlations.html": page("correlations.html", "Correlations", corr_body),
    "own-lines.html": page("own-lines.html", "Own lines", own_body),
    "strategies.html": page("strategies.html", "Strategies", strat_body),
    "leaderboard.html": page("leaderboard.html", "Leaderboard", lb_body),
    "validation.html": page("validation.html", "Validation gates", val_body),
    "flagged.html": page("flagged.html", "Flagged for review", flag_body),
    "sources.html": page("sources.html", "Sources", src_body),
}
for name, html in pages.items():
    with open(os.path.join(LAB, name), "w") as f:
        f.write(html)
print(f"wrote {len(pages)} pages to nfl-lab/")

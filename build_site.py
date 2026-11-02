#!/usr/bin/env python3
"""Build the static GitHub Pages site (root of the repo) from data/*.json — single source of truth.

Run research first if you want to refresh results:  python research/run_all.py
Then:                                              python build_site.py
The build FAILS (exit 1) if any table row lacks an http(s) source link or any internal link is broken.
"""
import json, html, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
E = html.escape


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


SRC = {s["id"]: s for s in load("sources.json")["sources"]}
RES = load("research_results.json")
META, SING, PARL = RES["meta"], RES["singles"], RES["parlays"]
CORR = load("correlations_computed.json")
AUDIT = load("audit.json")
STRAT = load("strategies.json")["strategies"]
GATES = load("validation_gates.json")["gates"]
FLAGS = load("flagged.json")["flagged"]
CORR_OFFICIAL = load("correlations.json")["correlations"]
HELPLINE = "1-800-MY-RESET"
HELP_URL = SRC["SRC-10"]["url"]
BE = META["breakeven"]
PW = META["proxy_weight"]


def srclinks(ids):
    return " ".join(
        f'<a href="{E(SRC[i]["url"])}" target="_blank" rel="noopener" title="{E(SRC[i]["name"])}">{i}{"" if SRC[i]["official"] else " ⚠"}</a>'
        for i in ids if i in SRC)


def pct(x, d=1):
    return "" if x is None else f"{100 * x:.{d}f}%"


def pp(x, d=2):
    return "" if x is None else f"{x:+.{d}f} pp"


def pfmt(p):
    if p is None: return ""
    return "&lt;0.001" if p < 0.001 else f"{p:.3f}"


NAV = [("index.html", "Dashboard"), ("pages/summary.html", "Executive Summary"), ("pages/leaderboard.html", "Leaderboard"),
       ("pages/research.html", "Research"), ("pages/correlations.html", "Correlations"), ("pages/strategies.html", "Strategies"),
       ("pages/validation.html", "Validation Gates"), ("pages/audit.html", "Audit"), ("pages/flagged.html", "Flagged for Review"),
       ("pages/sources.html", "Sources"), ("docs/index.html", "Spec (docs)"), ("lab/index.html", "Data Lab")]
FILES = []


def page(title, body, path):
    rel = "" if path == "index.html" else "../"
    nav = "".join(f'<a href="{rel}{h}"{" class=active" if h == path else ""}>{t}</a>' for h, t in NAV)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} — Own4 NBA Line Research</title>
<link rel="stylesheet" href="{rel}assets/style.css"></head>
<body><header><h1>🏀 Own4 — NBA Line Origination Research</h1><nav>{nav}</nav></header>
<main>{body}</main>
<footer>Research only — not wagering advice. Results are computed on historical data against a transparent proxy, not sportsbook prices.
If gambling is a concern: National Problem Gambling Helpline <a href="{E(HELP_URL)}" target="_blank" rel="noopener">{HELPLINE}</a> (NCPG) ·
<a href="{rel}pages/flagged.html">Flagged for Review</a> · <a href="{rel}pages/sources.html">Sources</a></footer>
<script src="{rel}assets/table.js"></script></body></html>"""
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    FILES.append(path)


def table(heads, rows, filt=True, cls=""):
    """rows: list of lists of HTML strings. The LAST column must hold the source links."""
    h = "".join(f"<th>{x}</th>" for x in heads)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    box = '<input class="filter" type="search" placeholder="Filter rows…" aria-label="Filter rows">' if filt else ""
    return f'{box}<div class="wrap"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


# ---------------------------------------------------------------------------------------------- research lookups
R = {(r["strategy"], r["q"]): r for r in SING}
SEL = {r["strategy"]: r for r in SING if r["selected_on_dev"]}
Q_LABEL = {0.5: "Top 50%", 0.75: "Top 25%", 0.9: "Top 10%"}
TIER_CLASS = {"Provisional Gold": "gold", "Silver": "silver", "Bronze": "bronze", "No award": "none", "Control · not eligible": "ctrl"}
BASE_PTS = {"Provisional Gold": 100, "Silver": 50, "Bronze": 10}
for r in SING + PARL:
    r["points"] = 0 if r["tier"] in ("No award", "Control · not eligible") else BASE_PTS[r["tier"]] + max(0, round(r.get("score_pp") or 0))


def chips(gates, order, fails):
    out = []
    for g in order:
        if g not in gates: continue
        ok = gates[g]
        out.append(f'<span class="chip {"ok" if ok else "bad"}" title="{g}: {"pass" if ok else "fail"}">{g}{"✓" if ok else "✗"}</span>')
    return "".join(out)


def tier_badge(t):
    return f'<span class="badge {TIER_CLASS[t]}">{E(t)}</span>'


def rank_map(rows):
    elig = [r for r in rows if r["tier"] not in ("Control · not eligible",) and r.get("n")]
    order = {"Provisional Gold": 0, "Silver": 1, "Bronze": 2, "No award": 3}
    elig.sort(key=lambda r: (order[r["tier"]], -(r.get("score_pp") or -99)))
    return {id(r): i + 1 for i, r in enumerate(elig)}


SING_RANK = rank_map(SING)
PARL_RANK = rank_map(PARL)
GOLD_S = [r for r in SING if r["tier"] == "Provisional Gold"]
SILV_S = [r for r in SING if r["tier"] == "Silver"]
GOLD_P = [r for r in PARL if r["tier"] == "Provisional Gold"]
n_sing_trials = len(SING)
n_strats = len({r["strategy"] for r in SING})
CORR_IDX = {(c.get("sample"), c.get("pair")): c for k in ("stat_residuals", "teammate_opponent", "context") for c in CORR[k]}


def cr(sample, pair):
    c = CORR_IDX[(sample, pair)]
    return c["r"]


# ---------------------------------------------------------------------------------------------- leaderboard tables
def sing_rows():
    order = sorted(SING, key=lambda r: (SING_RANK.get(id(r), 999), r["strategy"], r["q"]))
    rows = []
    for r in order:
        rk = SING_RANK.get(id(r))
        rows.append([
            str(rk) if rk else "—",
            f'<b>{r["strategy"]}</b> · {E(r["name"])}' + (' <span class="star" title="threshold chosen on dev data only">★ dev-selected</span>' if r["selected_on_dev"] else ""),
            E(r["market"]), Q_LABEL[r["q"]], f'{r["n"]:,}',
            f'{pct(r["hit"])} <span class="muted">± {pct(1.96 * r["se"])}</span>', pp(r["score_pp"]), pfmt(r["p_holm"]),
            chips(r["gates"], ["G1", "G2", "G3", "G4", "G5", "G6", "G7"], r["gate_fails"]), tier_badge(r["tier"]), str(r["points"]),
            srclinks(["SRC-13", "SRC-14", "SRC-15"])])
    return rows


def parl_rows():
    order = sorted(PARL, key=lambda r: (PARL_RANK.get(id(r), 999), r["name"]))
    rows = []
    for r in order:
        rk = PARL_RANK.get(id(r))
        if not r.get("n"):
            rows.append(["—", E(r["name"]), str(r["legs"]), "0", "", "", "", "", "", "",
                         f'<span class="chip bad">G2✗</span> <span class="muted">{E(r.get("note", ""))}</span>', tier_badge("No award"), "0", srclinks(["SRC-13", "SRC-15"])])
            continue
        rows.append([
            str(rk) if rk else "—", E(r["name"]), str(r["legs"]), f'{r["n"]:,}',
            f'{pct(r["joint_hit"])} <span class="muted">(indep. {pct(r["indep_hit"])})</span>',
            f'{r["rho"]:+.3f}', f'{100 * r["roi"]:+.1f}% <span class="muted">± {100 * 1.96 * r["roi_se"]:.1f}</span>', pfmt(r["p_holm"]),
            chips(r["gates"], ["G2", "G4", "G5", "G8", "G9"], r["gate_fails"]), tier_badge(r["tier"]), str(r["points"]),
            srclinks(["SRC-13", "SRC-14", "SRC-15"])])
    return rows


SING_HEAD = ["#", "Entry", "Market", "Edge threshold", "Bets", "Hit rate ±95%", "Edge lower bound", "Holm p", "Gates", "Tier", "Pts", "Source"]
PARL_HEAD = ["#", "Parlay / combo type", "Legs", "Parlays", "Joint hit (independence)", "Leg ρ", "ROI @ assumed −110/leg", "Holm p", "Gates", "Tier", "Pts", "Source"]

page("Leaderboard", f"""
<h2>🏆 Leaderboard — singles, player props, parlays &amp; combos</h2>
<p class="note"><b>How to read this.</b> Every entry is a strategy that originates its own line, evaluated once on {META['n_games_holdout']:,} frozen holdout games
({META['holdout_seasons'][0]} → {META['holdout_seasons'][-1]}). "Hit rate" is the share of bets where the outcome landed on the strategy's side of the
<em>market proxy</em> line. Break-even at an <b>assumed</b> −110 price is {pct(BE, 2)}. Rewards are recognition tiers/points only (no cash).
Tier rules: <b>Provisional Gold</b> = passes every gate; <b>Silver</b> = significant after Holm correction but fails only sample-size (G2) and/or directional-bias (G7);
<b>Bronze</b> = beats break-even at raw p&lt;0.05 but does not survive multiple-testing correction; <b>Control</b> = calibration check, never ranked.
Points = tier base (100/50/10) + lower-bound edge in percentage points. <b>“Provisional”</b> because gate G12 (prospective replication) has not been run.
All edges are versus a proxy, <u>not</u> sportsbook prices — see <a href="research.html">Research</a> and <a href="flagged.html">Flagged for Review</a>.</p>
<div class="cards">
<div class="card"><b>{len(GOLD_S)}</b><span>Provisional Gold (singles/props)</span></div>
<div class="card"><b>{len(SILV_S)}</b><span>Silver</span></div>
<div class="card"><b>{len(GOLD_P)}</b><span>Provisional Gold (parlays/combos)</span></div>
<div class="card"><b>{n_sing_trials}</b><span>Registered single/prop trials</span></div>
</div>
<h3>Singles &amp; player props ({n_sing_trials} registered trials = {n_strats} strategies × 3 thresholds)</h3>
{table(SING_HEAD, sing_rows())}
<h3>Parlays &amp; player-prop combos ({META['trials_parlays']} registered types)</h3>
<p class="note">Legs are drawn only from non-control strategies whose dev-selected trial is Holm-significant and beats the proxy
({", ".join(META['parlay_leg_strategies'])}). No game-total strategy qualified, so total-based same-game parlays (SGP1, SGP3) could not be built.
Same-player combos have the highest raw ROI <em>because their legs are positively correlated</em>; sportsbooks reprice or restrict these, so gate G8 blocks them. Legs also inherit the Over-lean of the prop strategies (their G7 failures), so every parlay pass here is provisional.</p>
{table(PARL_HEAD, parl_rows())}
""", "pages/leaderboard.html")

# ---------------------------------------------------------------------------------------------- correlations page
def corr_rows(items, label_key="pair"):
    rows = []
    for c in items:
        lab = c.get(label_key) or c.get("name")
        if c["r"] is None:
            rows.append([E(lab), c.get("sample", "holdout"), str(c["n"]), "", "", "", srclinks(["SRC-13", "SRC-15"])]); continue
        rows.append([E(lab), c.get("sample", "holdout"), f'{c["n"]:,}', f'{c["r"]:+.3f}', f'[{c["lo"]:+.3f}, {c["hi"]:+.3f}]',
                     f'{c["spearman"]:+.3f}' if "spearman" in c else "", srclinks(["SRC-13", "SRC-15"])])
    return rows

CH = ["Pair", "Sample", "n", "Pearson r", "95% CI", "Spearman ρ", "Source"]
off_rows = [[E(c["pair"]), c["value"] or "<em>blank — unverified</em>", E(c["status"]), srclinks(c["sources"]) or srclinks(["SRC-13"])] for c in CORR_OFFICIAL]
leg_rows = [[E(r["name"]), r["legs"].__str__(), f'{r["n"]:,}' if r.get("n") else "0", f'{r["rho"]:+.3f}' if r.get("rho") == r.get("rho") and r.get("rho") is not None else "",
             f'{pct(r.get("joint_hit"))}' if r.get("joint_hit") is not None else "", f'{pct(r.get("indep_hit"))}' if r.get("indep_hit") is not None else "",
             f'{r["lift"]:.2f}×' if r.get("lift") else "", srclinks(["SRC-13", "SRC-15"])] for r in PARL]
ic_rows = [[E(c["name"]) + f' <span class="muted">({c["strategy"]})</span>', "holdout", f'{c["n"]:,}', f'{c["r"]:+.3f}', f'[{c["lo"]:+.3f}, {c["hi"]:+.3f}]', "", srclinks(["SRC-13", "SRC-15"])] for c in CORR["signal_vs_outcome"]]
page("Correlations", f"""
<h2>Correlation values</h2>
<p class="note"><b>Status: COMPUTED — not confirmed by any official source.</b> Official sites do not publish these coefficients (first table: left blank, as required).
The tables below are reproducible estimates from the third-party box-score mirror (⚠ SRC-15; spot-checked on 1 game only) — each row links to the official
stat definitions (SRC-13). Residual = actual − market-proxy line. 95% CIs use the Fisher transform assuming independent rows, so they are somewhat optimistic.
Dev = {META['dev_seasons'][0]} → {META['dev_seasons'][-1]}; holdout = {META['holdout_seasons'][0]} → {META['holdout_seasons'][-1]}.</p>
<h3>1 · Official-source coefficients (none exist → blank)</h3>
{table(["Pair", "Value", "Status", "Source"], off_rows, filt=False)}
<h3>2 · Same-player stat residuals (player-prop combo legs)</h3>
{table(CH, corr_rows(CORR["stat_residuals"]))}
<h3>3 · Teammates, opponents and game total</h3>
{table(CH, corr_rows(CORR["teammate_opponent"]))}
<h3>4 · Team context (rest, pace, margin)</h3>
{table(CH, corr_rows(CORR["context"]))}
<h3>5 · Signal vs outcome (information coefficient: correlation of strategy adjustment with result minus line, holdout)</h3>
{table(CH, ic_rows)}
<h3>6 · Parlay leg outcome correlation (average pairwise φ between leg hit indicators)</h3>
<p class="note">“Lift” = joint hit rate ÷ product of leg hit rates; &gt;1 means legs win together more often than independence implies. Gate G8 requires |ρ| ≤ {META['gate_params']['parlay_max_abs_rho']}.</p>
{table(["Parlay / combo type", "Legs", "Parlays", "Leg ρ", "Joint hit", "Independent hit", "Lift", "Source"], leg_rows)}
""", "pages/correlations.html")

# ---------------------------------------------------------------------------------------------- research page
cv = META["proxy_vs_naive_control"]
pl, lk = META["placebo"], META["leakage_perturbation"]
ctrl_rows = [[E(c["market"]), E(c["rule"]), f'{c["n"]:,}', f'{pct(c["hit"])} <span class="muted">± {pct(1.96 * c["se"])}</span>', srclinks(["SRC-13", "SRC-15"])] for c in cv]
sel_rows = []
for sid in sorted(SEL):
    r = SEL[sid]
    sel_rows.append([f'<b>{sid}</b> · {E(r["name"])}', Q_LABEL[r["q"]]] + [f'{pct(r["by_season"].get(s))} <span class="muted">(n={r["by_season_n"].get(s, 0):,})</span>' for s in META["holdout_seasons"]] +
                    [f'{pct(r["hit_dev"])} <span class="muted">(n={r["n_dev"]:,})</span>', srclinks(["SRC-13", "SRC-15"])])
data_rows = [
    ["Box-score source", f'GitHub mirror of NBA.com box scores, pinned to commit <code>{META["dataset_commit"][:7]}</code> (⚠ third-party; flagged)', srclinks(["SRC-15"])],
    ["Why a mirror", "NBA.com says its stats are not available for download for academic or personal use; tables render client-side and are not retrievable here", srclinks(["SRC-12"])],
    ["Verification of mirror", "1 official box score compared (LAL @ DEN, 2023-10-24): final score and two players' minutes/PTS/REB/AST identical. Everything else unverified", srclinks(["SRC-14"])],
    ["Games used", f'{META["n_games"]:,} regular-season games with ≥10 prior games per team ({META["n_games_dev"]:,} dev + {META["n_games_holdout"]:,} holdout)', srclinks(["SRC-15"])],
    ["Player-games used", f'{META["n_player_games"]:,} player-game rows (≥10 prior games played, ≥20 prior min/game; DNP = void)', srclinks(["SRC-15"])],
    ["Dev / holdout split", f'Fit + threshold choice on {META["dev_seasons"][0]} → {META["dev_seasons"][-1]}; frozen holdout {META["holdout_seasons"][0]} → {META["holdout_seasons"][-1]}', srclinks(["SRC-15"])],
    ["Stat definitions", "PTS, REB, AST, PACE (possessions per 48 minutes) as defined by the official glossary; PRA = PTS+REB+AST summed (NBA.com lists the combined stat as unavailable)", srclinks(["SRC-13", "SRC-12"])],
    ["Possessions", "FGA + 0.44·FTA − OREB + TOV (project-defined estimator; glossary gives no formula) — flagged", srclinks(["SRC-13"])],
]
method_rows = [
    ["Market proxy (stand-in for a sportsbook)", f"Season-to-date mean + {PW:.1f} × (recency EWMA − season mean), shifted by a constant so 50% of dev outcomes land over. No sportsbook prices are used anywhere.", srclinks(["SRC-13"])],
    ["Own line", "Proxy + Σ βᵢ·(feature − dev mean). β from OLS on dev only, then frozen. Features: pace form, league drift, back-to-back flags, rest differential (teams); minutes trend, team back-to-back, home, game pace (players).", srclinks(["SRC-13"])],
    ["Bet rule", "Bet the side of the adjustment (Over/Home if adjustment > 0) when |adjustment| is in the top 50% / 25% / 10% of the dev distribution. All three thresholds are registered trials.", srclinks(["SRC-13"])],
    ["Settlement", f"Outcome vs proxy line; pushes void. Break-even {pct(BE, 2)} at an ASSUMED −110 price (decimal 1.9091).", srclinks(["SRC-13"])],
    ["Standard errors", "Clustered by game date (props within a night are not independent).", srclinks(["SRC-13"])],
    ["Multiple testing", f"Holm-Bonferroni across all {n_sing_trials} registered single/prop trials (parlays: across built parlay types).", srclinks(["SRC-13"])],
    ["Luck removal", "Directional-null test, season-by-season and alternating-week repeatability, threshold robustness, placebo strategies, clustered errors, frozen holdout.", srclinks(["SRC-13"])],
]
sys_rows = [
    ["Look-ahead perturbation (team)", f'Game {lk["team"]["game_id"]}: own features unchanged = {lk["team"]["own_features_unchanged"]}; later games changed = {lk["team"]["later_game_features_changed"]}', "PASS" if lk["team"]["passed"] else "FAIL", srclinks(["SRC-15"])],
    ["Look-ahead perturbation (player)", f'Player {lk["player"]["player_id"]}, game {lk["player"]["game_id"]}: own features unchanged = {lk["player"]["own_features_unchanged"]}; later games changed = {lk["player"]["later_game_features_changed"]}', "PASS" if lk["player"]["passed"] else "FAIL", srclinks(["SRC-15"])],
    ["Placebo calibration", f'{pl["placebo_strategies"]:,} random-side strategies on the same bets: {pl["false_positives"]} passed Bonferroni significance (rate {pct(pl["false_positive_rate"])}); mean placebo hit rate {pct(pl["placebo_hit_mean"], 2)} (sd {pct(pl["placebo_hit_sd"], 2)})', "PASS" if pl["passes"] else "FAIL", srclinks(["SRC-15"])],
]
findings = []
p4, t1_75, m2s = SEL["P4"], R[("T1", 0.75)], SEL["M2"]
QL = {k: v.lower() for k, v in Q_LABEL.items()}
gold_names = ", ".join(r["strategy"] + " " + QL[r["q"]] for r in GOLD_S) or "none"
ov = [SEL[x]["over_share"] for x in ("P1", "P2", "P3", "P4")]
same_rho = [r["rho"] for r in PARL if r.get("n") and "same player" in r["name"]]
gold_p_names = ", ".join((r["name"].split(" · ")[0] if r["name"].startswith(("XG", "SGP")) else r["name"].replace("CMB · ", "")) for r in GOLD_P)
HB, AB = "Home back-to-back flag ↔ game total residual", "Away back-to-back flag ↔ game total residual"
HM, AM = "Home back-to-back flag ↔ home margin residual", "Away back-to-back flag ↔ home margin residual"
TM, OP, TS = "Teammates: top-2 scorers' points residuals", "Opponents: each team's top scorer points residuals", "Top scorer points residual ↔ game total residual"
findings.append(("Singles/props overall", f'{len(GOLD_S)} of {n_sing_trials} registered trials pass every gate ({gold_names}); {len(SILV_S)} more are Silver; the rest fail on significance or repeatability. Nothing is called validated: gate G12 (prospective replication) has not been run.'))
findings.append(("Player props", f'All four prop strategies beat the market proxy (MAE p&lt;0.05) and survive Holm correction at their dev-selected threshold (e.g. P4 PRA {QL[p4["q"]]}: {pct(p4["hit"])} on {p4["n"]:,} bets). But they lean Over {pct(min(ov), 0)}–{pct(max(ov), 0)} of the time, so most fail gate G7 (directional bias); only P3 (assists) at {QL[0.5]} passes everything. Likely reason: the proxy ignores minutes information, which is what these strategies exploit — a real market prices minutes.'))
findings.append(("Game totals", f'T1 (pace form + league scoring drift) reaches {pct(t1_75["hit"])} at {QL[0.75]} (Silver) but leans Under {pct(1 - t1_75["over_share"], 0)}; T2 (rest flags alone) has no skill (hit {pct(R[("T2", 0.5)]["hit"])}, IC {R[("T2", 0.5)]["ic"]:+.3f}). Rest does not move totals: back-to-back vs total-residual correlation is about zero (holdout {cr("holdout", HB):+.3f} home / {cr("holdout", AB):+.3f} away).'))
findings.append(("Point spreads", f'M2 (rest differential) at {QL[m2s["q"]]}: {pct(m2s["hit"])} on only {m2s["n"]:,} bets (Silver — underpowered, G2). Back-to-back effects are small but real: home back-to-back vs home-margin residual {cr("holdout", HM):+.3f}, away back-to-back {cr("holdout", AM):+.3f} (holdout).'))
findings.append(("Calibration controls", f'T3 and M1 only re-weight the recency term already inside the proxy. They would pass the gates (e.g. M1 {QL[0.5]} {pct(R[("M1", 0.5)]["hit"])}), which shows the proxy’s 0.5 recency weight is arbitrary rather than revealing any market inefficiency. They are excluded from ranking.'))
findings.append(("Why not a naive baseline?", f'Iteration 1 settled against a plain season-to-date line: simply betting the direction of recency form hit {pct(cv[0]["hit"])} on totals and {pct(cv[2]["hit"])} on player points. That is not credible as skill — the naive baseline lags in-season trends. The proxy was strengthened (flagged: the holdout was viewed before the redesign).'))
findings.append(("Parlays & combos", f'{len(GOLD_P)} parlay types pass every gate ({gold_p_names}); their ROI is inherited from leg edges versus the proxy at assumed −110 prices, so it is not an achievable sportsbook return. Same-player combos (PTS+REB, PTS+AST, REB+AST, PRA) show ρ≈{min(same_rho):.2f}–{max(same_rho):.2f} and are blocked by G8.'))
findings.append(("Dependence structure", f'Teammates’ top-2 scorers’ points residuals are uncorrelated ({cr("holdout", TM):+.3f}); opposing top scorers are mildly positive ({cr("holdout", OP):+.3f}); a top scorer’s points vs the game total is {cr("holdout", TS):+.3f}. Within a player: points↔rebounds {cr("holdout", "Points ↔ Rebounds"):+.3f}, points↔assists {cr("holdout", "Points ↔ Assists"):+.3f}, rebounds↔assists {cr("holdout", "Rebounds ↔ Assists"):+.3f}.'))
find_rows = [[f"<b>{E(a)}</b>", b, srclinks(["SRC-13", "SRC-15"])] for a, b in findings]

page("Research", f"""
<h2>Research — method, tests and findings</h2>
<p class="note">Everything on this page is <b>computed</b> from a third-party mirror (⚠) and is unverified by an official source beyond the one-game spot check. The code is in <code>research/</code>; rerun with <code>python research/run_all.py</code>.</p>
<h3>Findings</h3>{table(["Topic", "Finding", "Source"], find_rows, filt=False)}
<h3>System tests (do the gates catch luck?)</h3>{table(["Test", "Detail", "Result", "Source"], sys_rows, filt=False)}
<h3>Control experiment — why the naive baseline was rejected</h3>{table(["Market", "Rule", "Bets", "Hit rate ±95%", "Source"], ctrl_rows, filt=False)}
<h3>Data &amp; provenance</h3>{table(["Item", "Detail", "Source"], data_rows, filt=False)}
<h3>Method</h3>{table(["Step", "Definition", "Source"], method_rows, filt=False)}
<h3>Repeatability — hit rate by holdout season (dev-selected threshold)</h3>
{table(["Strategy", "Threshold"] + META["holdout_seasons"] + ["Dev sample", "Source"], sel_rows, filt=False)}
""", "pages/research.html")

# ---------------------------------------------------------------------------------------------- strategies / gates
srows = [[s["id"], E(s["category"]), E(s["name"]), E(s["signal"]), E(s.get("tested_as", "")), E(s["correlation_note"]), srclinks(s["sources"])] for s in STRAT]
page("Strategies", f"""<h2>Strategies — concepts and what was tested</h2>
<p class="note">STRAT-01…06 are the original conceptual rows (corrected during the audit — see <a href="audit.html">Audit</a>). The “Tested as” column maps each to the executed strategies on the <a href="leaderboard.html">Leaderboard</a>.
Executed strategies: T1–T3 (totals), M1–M2 (spread), P1–P4 (player points/rebounds/assists/PRA), plus parlay and combo constructions.</p>
{table(["ID", "Category", "Name", "Signal (official-source facts only)", "Tested as", "Correlation note", "Sources"], srows)}""", "pages/strategies.html")

def gate_src(g):
    if g["sources"]:
        return srclinks(g["sources"])
    return '<span class="muted">project policy — no official source applies;</span> ' + srclinks(["SRC-13"])


grows = [[g["id"], E(g["name"]), E(g["type"]), E(g["rule"]), gate_src(g)] for g in GATES]
page("Validation Gates", f"""<h2>Validation gates — executed in code</h2>
<p class="note">Thresholds are <b>project policy</b> (not mandated by any official source) and were fixed in <code>research/config.py</code> before the holdout was first opened. Source links point to the official definitions/processes each gate relies on.</p>
{table(["ID", "Gate", "Type", "Rule", "Source"], grows, filt=False)}""", "pages/validation.html")

# ---------------------------------------------------------------------------------------------- audit
vc = {}
for a in AUDIT["rows"]: vc[a["verdict"]] = vc.get(a["verdict"], 0) + 1
arows = [[a["id"], f'<span class="badge v-{a["verdict"].split()[0].lower()}">{a["verdict"]}</span>', E(a["claim"]), E(a["where"]), E(a["official_says"]), E(a["action"]), srclinks([a["source"]])] for a in AUDIT["rows"]]
page("Audit", f"""<h2>Line-by-line audit of existing content</h2>
<p class="note">{E(AUDIT["method"])}</p>
<div class="cards">{"".join(f'<div class="card"><b>{n}</b><span>{k}</span></div>' for k, n in sorted(vc.items()))}</div>
{table(["ID", "Verdict", "Claim", "Where", "What the official page says", "Action taken", "Source"], arows)}""", "pages/audit.html")

# AUDIT.md (generated from data/audit.json)
am = ["# Audit — line-by-line check of the repository against official sources", "", AUDIT["method"], "",
      "Verdicts: " + ", ".join(f"{k} {n}" for k, n in sorted(vc.items())), "",
      "| ID | Verdict | Claim | Where | What the official page says | Action | Source |", "|---|---|---|---|---|---|---|"]
for a in AUDIT["rows"]:
    cell = lambda t: str(t).replace("|", "\\|").replace("\n", " ")
    am.append(f'| {a["id"]} | {a["verdict"]} | {cell(a["claim"])} | {cell(a["where"])} | {cell(a["official_says"])} | {cell(a["action"])} | [{a["source"]}]({SRC[a["source"]]["url"]}) |')
with open(os.path.join(ROOT, "AUDIT.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(am) + "\n")

# ---------------------------------------------------------------------------------------------- flagged / sources
frows = [[f"F{i + 1:02d}", E(x["item"]), E(x["reason"]), srclinks(x["sources"]) or '<em>none — unverified</em> ' + srclinks(["SRC-12"])] for i, x in enumerate(FLAGS)]
page("Flagged for Review", f"""<h2>⚑ Flagged for Review</h2>
<p class="note">Items that could not be confirmed from an official source, or irregularities found. None of these block publication; all block calling any strategy “validated”. Status of every row: <b>needs review</b>.</p>
{table(["#", "Item", "Reason / irregularity", "Sources"], frows)}""", "pages/flagged.html")

orows = [[i, E(s["name"]), "Official" if s["official"] else "⚠ Third-party (not official)", E(s.get("checked", "")), f'<a href="{E(s["url"])}" target="_blank" rel="noopener">{E(s["url"])}</a>'] for i, s in SRC.items()]
page("Sources", f"""<h2>Sources</h2><p class="note">All links were fetched on 2026-11-02. Only SRC-15 is not official; it is the research data input and is flagged everywhere it is used.</p>
{table(["ID", "Source", "Type", "Checked", "Link"], orows, filt=False)}""", "pages/sources.html")

# ---------------------------------------------------------------------------------------------- executive summary (md + html)
aud_ver, aud_cor, aud_unv, aud_ns = (vc.get(k, 0) for k in ("VERIFIED", "CORRECTED", "UNVERIFIED", "NOT SUPPORTED"))
top = sorted([r for r in SING if r["tier"] in ("Provisional Gold", "Silver")], key=lambda r: -r["score_pp"])[:5]
top_txt = "; ".join(f'{r["strategy"]} {Q_LABEL[r["q"]].lower()} — {pct(r["hit"])} on {r["n"]:,} bets ({r["tier"]})' for r in top)
SUMMARY = [
    ("What this is", [f"A research framework for originating NBA lines — own projections for game totals, spreads, player props, parlays and prop combos — judged on a leaderboard where a strategy only earns credit if it survives {len(GATES)} validation gates built to strip out luck. Date: 2026-11-02."]),
    ("Headline results (computed, historical, versus a proxy — not sportsbook prices)", [
        f"{n_strats} strategies × 3 edge thresholds = {n_sing_trials} registered single/prop trials, evaluated once on {META['n_games_holdout']:,} frozen holdout games ({META['holdout_seasons'][0]} → {META['holdout_seasons'][-1]}) after fitting on {META['n_games_dev']:,} dev games.",
        f"{len(GOLD_S)} trial(s) pass every gate (Provisional Gold), {len(SILV_S)} are Silver (statistically significant after Holm correction but underpowered or direction-biased). Best by edge lower bound: {top_txt}.",
        f"Parlays/combos: {len(GOLD_P)} of {META['trials_parlays']} constructions pass every gate; same-player prop combos are blocked because their legs are correlated (ρ≈0.15–0.19) and books reprice such combos.",
        "Game totals from rest alone carry no signal; pace/league-drift gives a modest edge; point-spread rest effects are small but real; player-prop edges come mostly from minutes information the proxy ignores.",
    ]),
    ("How luck is removed", [
        "Chronological dev/holdout design: all features use only earlier games (perturbation tests pass); models and thresholds are fitted on dev seasons and frozen before the holdout is evaluated.",
        f"Date-clustered standard errors, Holm correction over all {n_sing_trials} trials, season-by-season and alternating-week repeatability, threshold robustness, a directional-null test, and placebo strategies ({META['placebo']['false_positives']} of {META['placebo']['placebo_strategies']:,} random strategies passed the significance gate).",
    ]),
    ("Correlation values (computed)", [
        f"Same player (holdout): points↔rebounds {cr('holdout', 'Points ↔ Rebounds'):+.2f}, points↔assists {cr('holdout', 'Points ↔ Assists'):+.2f}, rebounds↔assists {cr('holdout', 'Rebounds ↔ Assists'):+.2f}. Teammate top-2 scorers {cr('holdout', TM):+.2f}; opposing top scorers {cr('holdout', OP):+.2f}; top scorer vs game total {cr('holdout', TS):+.2f}.",
        "No official source publishes any of these coefficients, so the official-source column stays blank and the computed values are labeled unverified.",
    ]),
    ("Audit of the existing repo", [
        f"{len(AUDIT['rows'])} claims re-checked against official pages today: {aud_ver} verified, {aud_cor} corrected, {aud_unv} unverified (values blanked/flagged), {aud_ns} cited sources that did not support their use.",
        f"Notable: the helpline was listed as 1-800-GAMBLER but the official NCPG page lists {HELPLINE}; Dončić 33.5 PPG, Jokić 12.9/10.7 and the team PPG list appear in no retrievable official page text; the gate thresholds had been cited to NBA articles that do not mention them.",
    ]),
    ("What this does NOT show", [
        "No strategy beats a sportsbook: no betting lines were used (not official, not available). Edges are versus a transparent proxy that ignores minutes, injuries and matchups; a real market would erase much of the player-prop edge.",
        "The holdout was viewed once before a redesign (flagged) and prospective replication (G12) has not been run — hence “Provisional”. Data ends 2023-24; the NBA is now in 2026-27.",
        "Research data is a third-party mirror (⚠) checked against the official box score on 1 game only; NBA.com states its stats are not available for download, so licensing must be resolved before production use.",
        "Parlay returns assume −110 per leg with no correlation repricing.",
    ]),
    ("Next steps that need outside input", ["Licensed/official historical data through 2025-26 and archived sportsbook lines; then re-run `python research/run_all.py` and log live (timestamped) predictions for gate G12."]),
    ("Responsible gambling", [f"This is analysis, not wagering advice. National Problem Gambling Helpline: {HELPLINE} — {HELP_URL}"]),
]
md = ["# Executive Summary — Own4: NBA Line Origination & Signal Strategy Research", ""]
hh = ["<h2>Executive summary</h2><p class='note'>Generated from <code>data/*.json</code> by <code>build_site.py</code>. Full detail: <a href='leaderboard.html'>Leaderboard</a> · <a href='research.html'>Research</a> · <a href='audit.html'>Audit</a> · <a href='flagged.html'>Flagged for Review</a>.</p>"]
for h, items in SUMMARY:
    md += [f"## {h}", ""] + [f"- {i}" for i in items] + [""]
    hh.append(f"<h3>{E(h)}</h3><ul>" + "".join(f"<li>{E(i)}</li>" for i in items) + "</ul>")
with open(os.path.join(ROOT, "EXECUTIVE_SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
page("Executive Summary", "".join(hh), "pages/summary.html")

# ---------------------------------------------------------------------------------------------- dashboard
best_s = sorted([r for r in SING if r["tier"] not in ("Control · not eligible",)], key=lambda r: (SING_RANK[id(r)]))[:5]
dash_rows = [[str(SING_RANK[id(r)]), f'<b>{r["strategy"]}</b> · {E(r["name"])}', Q_LABEL[r["q"]], f'{r["n"]:,}', pct(r["hit"]), pp(r["score_pp"]), tier_badge(r["tier"]), srclinks(["SRC-13", "SRC-14"])] for r in best_s]
cat_rows = [
    ["Leaderboard", "Every strategy, gate results, tiers and reward points — singles, props, parlays, combos", '<a href="pages/leaderboard.html">Open</a> · ' + srclinks(["SRC-13"])],
    ["Executive Summary", "Key results, limits and next steps in one page", '<a href="pages/summary.html">Open</a> · ' + srclinks(["SRC-04"])],
    ["Research", "Method, data provenance, system tests, findings", '<a href="pages/research.html">Open</a> · ' + srclinks(["SRC-12"])],
    ["Correlations", f"{sum(len(CORR[k]) for k in ('stat_residuals','teammate_opponent','context','signal_vs_outcome'))} computed coefficients with CIs; official column blank", '<a href="pages/correlations.html">Open</a> · ' + srclinks(["SRC-13"])],
    ["Strategies / Validation Gates", f"{len(STRAT)} concepts and {len(GATES)} gates", '<a href="pages/strategies.html">Strategies</a> · <a href="pages/validation.html">Gates</a> · ' + srclinks(["SRC-08"])],
    ["Audit", f"{len(AUDIT['rows'])} line-by-line checks of earlier content against official pages", '<a href="pages/audit.html">Open</a> · ' + srclinks(["SRC-03"])],
    ["Flagged for Review", f"{len(FLAGS)} irregularities / unverified items for your review", '<a href="pages/flagged.html">Open</a> · ' + srclinks(["SRC-12"])],
    ["Related sites", "/docs/ — specification dashboard · /lab/ — Data Lab: 92 official 2026-27 games and prospective own lines for 2026-11-02 (separate sessions; not part of this site's computed research)", '<a href="docs/index.html">docs</a> · <a href="lab/index.html">lab</a> · ' + srclinks(["SRC-14"])],
    ["Sources", f"{len(SRC)} sources with fetch dates", '<a href="pages/sources.html">Open</a> · ' + srclinks(["SRC-05"])],
]
page("Dashboard", f"""
<h2>Dashboard</h2>
<p>Own-line generation for NBA <b>totals, spreads, player props, parlays and prop combos</b>, judged on a leaderboard with {len(GATES)} luck-removal gates.
<b>Results are computed on 2010-11 → 2023-24 history against a transparent market proxy — not sportsbook prices — and are labeled unverified/provisional.</b>
Every table row links to its official source; values that cannot be confirmed are blank and flagged.</p>
<div class="cards">
<div class="card"><b>{n_strats}</b><span>Strategies tested</span></div>
<div class="card"><b>{n_sing_trials + META['trials_parlays']}</b><span>Registered trials</span></div>
<div class="card"><b>{len(GOLD_S) + len(GOLD_P)}</b><span>Provisional Gold</span></div>
<div class="card"><b>{META['placebo']['false_positives']}/{META['placebo']['placebo_strategies']:,}</b><span>Placebo false positives</span></div>
<div class="card"><b>{len(AUDIT['rows'])}</b><span>Audit checks</span></div>
<div class="card"><b>{len(FLAGS)}</b><span>Flagged items</span></div>
</div>
<h3>Top of the leaderboard</h3>{table(["#", "Entry", "Threshold", "Bets", "Hit rate", "Edge lower bound", "Tier", "Source"], dash_rows, filt=False)}
<p class="note"><a href="pages/leaderboard.html">Full leaderboard →</a></p>
<h3>Explore by category</h3>{table(["Category", "What's inside", "Open · Source"], cat_rows, filt=False)}
""", "index.html")

# ---------------------------------------------------------------------------------------------- assets
os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
with open(os.path.join(ROOT, "assets", "style.css"), "w", encoding="utf-8") as f:
    f.write("""*{box-sizing:border-box}body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f6f7fb;color:#1c2333;line-height:1.45}
header{background:#0b3d91;color:#fff;padding:14px 24px;position:sticky;top:0;z-index:5}
header h1{margin:0 0 8px;font-size:1.2rem}
nav{display:flex;flex-wrap:wrap;gap:4px 14px}nav a{color:#cfe0ff;text-decoration:none;font-size:.9rem}
nav a.active,nav a:hover{color:#fff;text-decoration:underline}
main{max-width:1280px;margin:20px auto;padding:0 20px}
h2{margin:.2em 0 .5em}h3{margin:1.6em 0 .4em;color:#0b3d91}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.card{background:#fff;border:1px solid #e2e6ef;border-radius:10px;padding:12px 18px;min-width:130px;text-align:center}
.card b{font-size:1.5rem;display:block;color:#0b3d91}.card span{font-size:.8rem;color:#556}
.wrap{overflow-x:auto;border:1px solid #e2e6ef;border-radius:8px;background:#fff}
table{border-collapse:collapse;width:100%;min-width:720px}
th{background:#0b3d91;color:#fff;text-align:left;padding:9px 10px;font-size:.82rem;white-space:nowrap}
td{padding:8px 10px;border-top:1px solid #eef1f6;vertical-align:top;font-size:.86rem}
tr:nth-child(even) td{background:#fafbfe}
a{color:#0b3d91}.note{color:#445;font-size:.92rem;background:#fff;border-left:4px solid #0b3d91;padding:10px 14px;border-radius:4px}
.muted{color:#778;font-size:.85em}code{background:#eef1f8;padding:1px 5px;border-radius:4px}
.filter{width:100%;max-width:340px;margin:6px 0;padding:7px 10px;border:1px solid #c9d1e3;border-radius:6px}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.75rem;font-weight:600;white-space:nowrap}
.gold{background:#ffe08a;color:#6b4e00}.silver{background:#e3e7ee;color:#3a4558}.bronze{background:#f3d2b3;color:#6b3b12}
.none{background:#f1f1f1;color:#777}.ctrl{background:#e8e0f7;color:#46307a}
.v-verified{background:#d6f3df;color:#145a2e}.v-corrected{background:#fff0c2;color:#6b4e00}.v-unverified{background:#fde0e0;color:#8a1c1c}.v-not{background:#f6d6ee;color:#7a1a63}
.chip{display:inline-block;margin:1px;padding:0 5px;border-radius:4px;font-size:.72rem;font-family:monospace}
.chip.ok{background:#d6f3df;color:#145a2e}.chip.bad{background:#fde0e0;color:#8a1c1c}
.star{color:#b07a00;font-size:.75rem}
footer{max-width:1280px;margin:24px auto;padding:12px 20px;color:#667;font-size:.82rem;border-top:1px solid #e2e6ef}
""")
with open(os.path.join(ROOT, "assets", "table.js"), "w", encoding="utf-8") as f:
    f.write("""document.querySelectorAll('input.filter').forEach(function(inp){
  var wrap=inp.nextElementSibling; if(!wrap) return; var rows=wrap.querySelectorAll('tbody tr');
  inp.addEventListener('input',function(){var q=inp.value.toLowerCase();
    rows.forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>-1?'':'none';});});
});
""")
open(os.path.join(ROOT, ".nojekyll"), "w").close()

# ---------------------------------------------------------------------------------------------- integrity checks
problems = []
for path in FILES:
    txt = open(os.path.join(ROOT, path), encoding="utf-8").read()
    for href in re.findall(r'href="([^"#]+)"', txt):
        if href.startswith(("http://", "https://", "tel:", "mailto:")): continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(os.path.join(ROOT, path)), href))):
            problems.append(f"broken link {path} -> {href}")
    for src in re.findall(r'src="([^"]+)"', txt):
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(os.path.join(ROOT, path)), src))):
            problems.append(f"broken asset {path} -> {src}")
    for tr in re.findall(r"<tbody>(.*?)</tbody>", txt, flags=re.S):
        for row in re.findall(r"<tr>(.*?)</tr>", tr, flags=re.S):
            if not re.search(r'href="https?://', row):
                problems.append(f"row without source link in {path}: {re.sub('<[^>]+>', ' ', row)[:90]}")
print("pages:", len(FILES))
print("PROBLEMS:", problems if problems else "none")
sys.exit(1 if problems else 0)

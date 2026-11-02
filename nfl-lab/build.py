"""Generate the clean static NFL dashboard. No external assets or JavaScript deps."""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SITE = ROOT / "site"
PAGES = SITE / "pages"
DATA = ROOT / "data"
RES = ROOT / "results"
AUDIT = ROOT / "audit"


def load(path):
    return json.loads(path.read_text())


SOURCES = load(DATA / "sources.json")
GAMES = load(DATA / "games.json")
STANDINGS = load(DATA / "standings.json")
PLAYERS = load(DATA / "players.json")
UPCOMING = load(DATA / "upcoming.json")
EVAL = load(RES / "evaluation.json")
CURRENT = load(RES / "current_lines.json")
SGP = load(RES / "same_game_combo.json")
PLINES = load(RES / "player_lines.json")
PCOMBOS = load(RES / "player_combos.json")
CORR = load(RES / "correlations.json")
LEADER = load(RES / "leaderboard.json")
SUMMARY = load(RES / "summary.json")
INTEGRITY = load(RES / "integrity.json")
LEAK = load(RES / "leakage.json")
FLAGS = load(ROOT / "flags.json")
PROTOCOL = load(ROOT / "protocol.json")
AUDIT_SUMMARY = load(AUDIT / "summary.json") if (AUDIT / "summary.json").exists() else {}
VERIFY = load(RES / "verification.json") if (RES / "verification.json").exists() else None
PREDICTIONS = []
with (RES / "predictions.csv").open() as f:
    import csv
    PREDICTIONS = list(csv.DictReader(f))
PARLAYS = []
with (RES / "parlays.csv").open() as f:
    import csv
    PARLAYS = list(csv.DictReader(f))

NAV = [
    ("Overview", [("index.html", "Dashboard"), ("pages/executive-summary.html", "Executive summary"), ("pages/own-lines.html", "Originated lines")]),
    ("Markets", [("pages/singles.html", "Singles"), ("pages/parlays.html", "Parlays & same-game"), ("pages/props.html", "Player props & combos"), ("pages/leaderboard.html", "Strategy leaderboard")]),
    ("Research", [("pages/correlations.html", "Correlations & luck"), ("pages/validation.html", "Validation gates"), ("pages/methodology.html", "Methodology")]),
    ("Data", [("pages/data-games.html", "Official games"), ("pages/data-standings.html", "Official standings"), ("pages/data-players.html", "Player game logs"), ("pages/data-predictions.html", "Walk-forward predictions")]),
    ("Governance", [("pages/sources.html", "Source register"), ("pages/repository-audit.html", "Repository audit"), ("pages/flagged.html", "Flagged for review"), ("pages/verification.html", "Verification & deployment")]),
]
ARCHIVES = [
    ("NFL Quant Lab (separate contribution)", "../../../nfl-quant/", "https://github.com/sassnarep3-star/Own4/tree/main/nfl-quant"),
    ("NFL specification module", "../../../nfl/", "https://github.com/sassnarep3-star/Own4/tree/main/nfl"),
    ("Legacy NBA pipeline", "../../../pipeline/", "https://github.com/sassnarep3-star/Own4/tree/main/pipeline"),
    ("Legacy NBA research dashboard", "../../../pages/executive-summary.html", "https://github.com/sassnarep3-star/Own4/tree/main/pages"),
    ("Coordination board", "../../../COORDINATION.md", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("Legacy NBA README (preserved copy)", "../../legacy/README_NBA.md", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/legacy/README_NBA.md"),
    ("Legacy NBA executive summary (preserved copy)", "../../legacy/EXECUTIVE_SUMMARY_NBA.md", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/legacy/EXECUTIVE_SUMMARY_NBA.md"),
]


def e(x):
    return html.escape(str(x), quote=True)


def blank():
    return '<span class="blank" title="Unverified — intentionally left blank" aria-label="Unverified blank"></span>'


def fmt(x, digits=3):
    if x is None or x == "":
        return blank()
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return e(x)


def pct(x, digits=1):
    return blank() if x is None or x == "" else f"{float(x)*100:.{digits}f}%"


def signed(x, digits=1):
    if x is None or x == "":
        return blank()
    return f"{float(x):+.{digits}f}"


def src(sid, label=None):
    s = SOURCES.get(sid, {})
    url = s.get("url", "https://github.com/sassnarep3-star/Own4")
    return f'<a href="{e(url)}" rel="noopener">{e(label or s.get("title", sid))} ↗</a>'


def src_url(url, label="Official source"):
    return f'<a href="{e(url)}" rel="noopener">{e(label)} ↗</a>'


def table(headers, rows, caption=None, tid=None, filterable=False):
    cap = f"<caption>{e(caption)}</caption>" if caption else ""
    tidattr = f' id="{e(tid)}"' if tid else ""
    filt = f'<label class="filter">Filter rows <input type="search" data-filter="{e(tid or "")}" placeholder="Type to filter…"></label>' if filterable and tid else ""
    head = "".join(f"<th scope=\"col\">{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'{filt}<div class="table-wrap"><table{tidattr}>{cap}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def callout(text, kind="warn"):
    return f'<div class="callout {kind}">{text}</div>'


def kpi(label, value, note=""):
    return f'<div class="kpi"><div class="kpi-value">{e(value)}</div><div class="kpi-label">{e(label)}</div><div class="kpi-note">{e(note)}</div></div>'


def nav_html(prefix, active):
    out = []
    for group, items in NAV:
        links = []
        for href, label in items:
            target = prefix + href if href != "index.html" else prefix + "index.html"
            cls = ' class="active"' if href.endswith(active) or (active == "index.html" and href == "index.html") else ""
            links.append(f'<a href="{e(target)}"{cls}>{e(label)}</a>')
        out.append(f'<div class="nav-group"><div class="nav-title">{e(group)}</div>{"".join(links)}</div>')
    return "".join(out)


def page(slug, title, subtitle, body, prefix="../"):
    active = "index.html" if slug == "index" else f"pages/{slug}.html"
    css = prefix + "assets/style.css"
    js = prefix + "assets/app.js"
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NFL Line Lab</title><meta name="description" content="{e(subtitle)}">
<link rel="stylesheet" href="{e(css)}"></head>
<body><a class="skip" href="#main">Skip to content</a><div class="layout">
<aside class="sidebar"><a class="brand" href="{e(prefix)}index.html">NFL<span>Line Lab</span></a><nav aria-label="Primary">{nav_html(prefix, active)}</nav></aside>
<div class="content"><header class="topbar"><div><strong>{e(title)}</strong><span class="crumb">Official-only research snapshot</span></div><span class="badge">Nov 2, 2026 · Research only</span></header>
<main id="main"><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p>{body}</main>
<footer>Research only — not betting advice. No validated edge or reward is claimed. <a href="https://www.ncpgambling.org/help-treatment/" rel="noopener">Problem gambling support ↗</a> · <a href="{e(prefix)}pages/sources.html">Sources</a> · <a href="{e(prefix)}pages/flagged.html">Flagged for review</a></footer>
</div></div><script src="{e(js)}"></script></body></html>"""
    return doc


def build_index(prefix=""):
    m2 = next(r for r in CURRENT if r["model"] == "M2")
    cards = "".join([
        kpi("Official final games", SUMMARY["official_games"], "2025 full season + 2026 through Nov 1"),
        kpi("Walk-forward evaluation", SUMMARY["evaluation_games"], "21 season-week clusters"),
        kpi("Eligible strategies", SUMMARY["eligible_strategies"], "Every gate required"),
        kpi("Reward points", SUMMARY["reward_points"], "Virtual badges only; unfunded"),
        kpi("Source records", len(SOURCES), "Official NFL + method/governance"),
        kpi("Missing player cells", SUMMARY["missing_player_cells"], "Preserved blank, never zero-filled"),
    ])
    findings = [
        ["Input integrity", f'{INTEGRITY["standings_cells_matched"]}/320 team-season cells reconcile to official standings.', src("STAND-2026")],
        ["Leakage control", "Future-score perturbation leaves every earlier prediction unchanged.", src("SPLITS")],
        ["Best win-share Brier", "M2 0.23102 vs prior baseline 0.25406; improvement is not betting ROI.", src("CALIBRATION")],
        ["Multiplicity", "No primary trial survives Holm correction at 0.05.", src("FDR")],
        ["Market release", "Odds, CLV, ROI and edge remain blank; G08/G09/G10 blocked.", src("GAME")],
        ["Current research line", f'CHI {signed(m2["away_spread"])} / SEA {signed(-m2["away_spread"])}, total {m2["total"]:g}; M2 fair win-share SEA {pct(m2["home_winshare_p"])}.', src("GAME")],
    ]
    cats = [
        ("Singles", "Win-share, spread and total calibration with pre-registered gates.", "pages/singles.html"),
        ("Parlays", "Cross-game dependence, joint probabilities and same-game Poisson combos.", "pages/parlays.html"),
        ("Player props", "Official game logs, descriptive fair lines and same-player combos.", "pages/props.html"),
        ("Correlations", "Measured associations, confidence intervals and permutation tests.", "pages/correlations.html"),
        ("Leaderboard", "Reward-based competition rules; no winner manufactured.", "pages/leaderboard.html"),
        ("Flagged for review", "Unverified inputs, scope mismatches and non-blocking issues.", "pages/flagged.html"),
    ]
    cat_html = "".join(f'<a class="card" href="{e(prefix + href)}"><h3>{e(t)}</h3><p>{e(d)}</p><span>Open →</span></a>' for t, d, href in cats)
    body = f"""
<div class="hero"><div><p class="eyebrow">NFL line origination & signal research</p><h2>Originate lines. Test skill. Block unearned claims.</h2><p>This dashboard separates official NFL observations, reproducible model calculations and unverified market fields. It preserves prior repository work while making the NFL evidence boundary explicit.</p></div><div class="hero-status"><span class="dot"></span> No strategy passed every gate</div></div>
<div class="kpis">{cards}</div>
{callout('<strong>Executive conclusion:</strong> The official-only points models improve several probability metrics over a prior-season baseline, but no primary trial survives multiplicity correction and no executable market edge is verified. <strong>0 eligible strategies, 0 reward points.</strong>')}
<h2>Key findings</h2>{table(['Entry', 'Finding / analysis', 'Official or method source'], findings, 'Evidence-first summary')}
<h2>Explore the research</h2><div class="cards">{cat_html}</div>
<h2>Current slate</h2>{table(['Model', 'Matchup', 'CHI points', 'SEA points', 'CHI spread', 'Total', 'SEA fair win-share', 'Market odds', 'Source'], [[r['model'], 'CHI at SEA', fmt(r['away_points'],2), fmt(r['home_points'],2), signed(r['away_spread']), fmt(r['total'],1), pct(r['home_winshare_p']), blank(), src('GAME')] for r in CURRENT], 'Research lines only; market fields intentionally blank')}
<p><a href="{e(prefix)}pages/own-lines.html">Full originated-line analysis →</a> · <a href="{e(prefix)}pages/repository-audit.html#archives">Legacy and parallel-session archives →</a></p>
"""
    return page("index", "NFL Line Origination Lab", "Official-only NFL evidence, reproducible line origination and gated strategy research.", body, prefix)


def build_pages():
    PAGES.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    pages = {}
    # Executive summary
    rows = [
        ["Scope", "NFL only. Legacy NBA files are archived, not reused as NFL evidence.", src("REPO")],
        ["Data", "392 official final games; 96 standings rows; 28 player rows; 9 missing player cells preserved.", src("STAND-2026")],
        ["Validation", "314 chronological evaluation games across 21 season-weeks; future-score perturbation test passes.", src("SPLITS")],
        ["Skill", "M2 win-share Brier improves 0.02303 vs prior; M4 margin MSE improves 15.397. Neither is betting ROI.", src("CALIBRATION")],
        ["Luck control", "Whole-week bootstrap, sign-flip permutation null and Holm correction across six primary trials.", src("BOOTSTRAP")],
        ["Dependence", "Cross-game parlay dependence estimate is near zero; joint model does not beat independent product with positive lower CI.", src("CORRELATION")],
        ["Props", "Small official logs support descriptive lines only; cross-player same-game dependence is blank/blocked.", src("PLAYER-JSN")],
        ["Release decision", "No strategy passes all gates. Market, availability and prospective gates remain blocked.", src("GAME")],
        ["Rewards", "Virtual badges only; no eligible strategy, no points, no funded prize.", src("REPO")],
    ]
    pages["executive-summary"] = ("Executive summary", "Decision-grade summary of evidence, uncertainty and release status.", table(["Entry", "Finding / analysis", "Source"], rows) + callout("The correct output is a research dashboard and a blocked release, not a manufactured betting edge."))
    # Own lines
    rows = [[r["model"], r["model_name"], fmt(r["away_points"],2), fmt(r["home_points"],2), signed(r["away_spread"]), signed(-r["away_spread"]), fmt(r["total"],1), pct(r["away_winshare_p"]), pct(r["home_winshare_p"]), fmt(r["away_fair_decimal"],3), fmt(r["home_fair_decimal"],3), blank(), blank(), src("GAME")] for r in CURRENT]
    sgp_rows = [[SGP["game"], "SEA" if SGP["favorite"]=="B" else "CHI", signed(SGP["favorite_spread"]), fmt(SGP["total_line"],1), pct(SGP["p_cover"]), pct(SGP["p_over"]), pct(SGP["p_joint_model"]), pct(SGP["p_independent_product"]), fmt(SGP["phi_model"],4), blank(), src("GAME")]]
    pages["own-lines"] = ("Originated lines", "CHI at SEA · official date 2026-11-02 · venue Lumen Field. Derived fair lines, not sportsbook prices.",
        callout("Market spread, total, odds and edge are intentionally blank. The model omits historical venue, injuries, weather and roster adjustments.") +
        table(["Model", "Name", "CHI xPts", "SEA xPts", "CHI spread", "SEA spread", "Total", "CHI win-share", "SEA win-share", "CHI fair dec.", "SEA fair dec.", "Market odds", "Edge", "Source"], rows, "Four pre-registered models") +
        "<h2>Same-game spread + total combo</h2>" + table(["Game", "Favorite", "Favorite spread", "Total", "P(cover)", "P(over)", "P(joint, model)", "Independent product", "φ model", "Market price", "Source"], sgp_rows, "Model-implied joint probability from one Poisson score grid; not empirical sportsbook correlation") +
        "<h2>Interpretation</h2>" + table(["Entry", "Analysis", "Source"], [["M2", "Shrunk rolling points balances prior-season strength and 2026 form.", src("STAND-2025")], ["M4", "Online rest overlay uses only earlier residuals; current rest difference is +3 days for CHI.", src("GAME")], ["Release", "All lines are research-only because G08–G10 are blocked.", src("GAME")]]))
    # Singles
    strat = [s for s in EVAL["strategies"] if s["division"] == "Singles"]
    rows = [[s["id"], s["name"], s["n"], s["weeks"], fmt(s["loss"],5), signed(s["improvement_vs_prior"],5), f'{fmt(s["ci95"][0],5)} to {fmt(s["ci95"][1],5)}', fmt(s["p_holm"],4), "Blocked", blank(), src("CALIBRATION")] for s in strat]
    mrows = [[m, EVAL["metrics"][m]["n"], fmt(EVAL["metrics"][m]["win_brier"],5), fmt(EVAL["metrics"][m]["margin_mae"],3), fmt(EVAL["metrics"][m]["total_mae"],3), fmt(EVAL["metrics"][m]["calibration"]["ece"],4), src("STAND-2025")] for m in ("M1","M2","M3","M4")]
    pages["singles"] = ("Singles", "Win-share, spread and total research. Probability skill is not betting ROI.",
        table(["ID", "Strategy", "n", "Weeks", "Loss", "Improvement vs prior", "95% week-bootstrap CI", "Holm p", "Market status", "ROI", "Source"], rows, "Primary single-market trials", "singles-table", True) +
        "<h2>Model comparison</h2>" + table(["Model", "n", "Win Brier", "Margin MAE", "Total MAE", "Win ECE", "Source"], mrows) +
        callout("M3 is a sensitivity model, not a primary trial. No single-market strategy passes every gate."))
    # Parlays
    par = [s for s in EVAL["strategies"] if s["division"] == "Parlays"]
    rows = [[s["id"], s["name"], s["n"], s["weeks"], fmt(s["loss"],5), fmt(EVAL["parlays"].get(s["id"].split("-")[0],{}).get("hit_rate"),4), signed(s["improvement_vs_prior"],6), f'{fmt(s["ci95"][0],6)} to {fmt(s["ci95"][1],6)}', "Blocked", src("BOOTSTRAP")] for s in par]
    ticket_rows = [[r["model"], r["season"], r["week"], r["favorite_1"], r["favorite_2"], pct(float(r["p1"])), pct(float(r["p2"])), pct(float(r["p_joint"])), pct(float(r["p_independent"])), r["hit"], src_url(r["source_url"], "NFL schedule")] for r in PARLAYS if r["evaluation"] == "True"]
    pages["parlays"] = ("Parlays & same-game combinations", "Cross-game favorite pairs and a model-implied same-game spread/total combo.",
        table(["ID", "Strategy", "n", "Weeks", "Joint Brier", "Hit rate", "Improvement vs independent", "95% CI", "Market", "Source"], rows, "Cross-game research events: outright wins; ties lose") +
        "<h2>Same-game combo</h2>" + table(["Game", "P(joint)", "Independent product", "φ model", "Status", "Source"], [[SGP["game"], pct(SGP["p_joint_model"]), pct(SGP["p_independent_product"]), fmt(SGP["phi_model"],4), "Model-implied only; blocked", src("GAME")]]) +
        "<h2>Evaluated cross-game tickets</h2>" + table(["Model", "Season", "Week", "Leg 1 favorite", "Leg 2 favorite", "p1", "p2", "Joint p", "Independent p", "Both hit", "Source"], ticket_rows, "All evaluated tickets", "parlay-table", True))
    # Props
    rows = [[r["player"], r["team"], r["metric"], r["observed_n"], r["missing_n"], fmt(r["median"],1), fmt(r["own_line"],1), pct(r["empirical_over_p"]), blank(), blank(), src(r["source_id"])] for r in PLINES]
    crows = [[c["player"], c["legs"], c["n"], c["joint_hits"], pct(c["p_joint_empirical"]), pct(c["p_independent_product"]), fmt(c["phi_empirical"],4), "Blocked", src(c["source_id"])] for c in PCOMBOS]
    logrows = [[p["player"], p["team"], p["week"], p["date"], p["metric_a"], fmt(p["value_a"],0), p["metric_b"], fmt(p["value_b"],0), src(p["source_id"])] for p in PLAYERS]
    pages["props"] = ("Player props & combinations", "Official 2026 game logs only. Descriptive fair lines; no availability or market-edge claim.",
        callout("Every player market fails the 100-observation gate. Missing cells remain blank. Active profile status is not a pregame availability guarantee.") +
        table(["Player", "Team", "Metric", "Observed n", "Missing n", "Median", "Own line", "Empirical over", "Market line", "Market odds", "Source"], rows, "Descriptive player prop lines") +
        "<h2>Same-player combinations</h2>" + table(["Player", "Legs", "n", "Joint hits", "Empirical joint", "Independent product", "φ empirical", "Status", "Source"], crows) +
        "<h2>Cross-player same-game</h2>" + table(["Pair", "n", "Correlation", "Joint price", "Status", "Source"], [["Smith-Njigba + Burden receiving yards", 0, blank(), blank(), "Unverified — no paired same-game sample", src("GAME")]]) +
        "<h2>Official player game logs</h2>" + table(["Player", "Team", "Week", "Date", "Metric A", "Value A", "Metric B", "Value B", "Source"], logrows, "Blank numeric cells are missing in the official source", "player-log-table", True))
    # Correlations
    rows = [[c["id"], c["pair"], c["kind"], c["n"], fmt(c["r"],4), f'{fmt(c["ci95"][0],4)} to {fmt(c["ci95"][1],4)}', fmt(c["p"],4), c["status"], src(c["source_id"])] for c in CORR]
    pages["correlations"] = ("Correlations & luck controls", "Measured associations with uncertainty. Correlation is not causation or a betting edge.",
        table(["ID", "Pair", "Type", "n", "Estimate", "95% CI", "Permutation p", "Status", "Source"], rows, "Game-level and player-level dependence", "corr-table", True) +
        "<h2>Luck-removal controls</h2>" + table(["Control", "Implementation", "Limit", "Source"], [["Temporal isolation", "Only earlier games update ratings; future-score perturbation test passes.", "Does not remove sport randomness.", src("SPLITS")], ["Dependence-aware uncertainty", "Whole season-week bootstrap and sign-flip permutation null.", "Exchangeability and limited clusters remain assumptions.", src("BOOTSTRAP")], ["Multiplicity", "Holm correction across six primary trials; sensitivity models are exploratory.", "Cannot rescue a blocked market gate.", src("FDR")], ["Causality", "Associations are not interpreted as causal effects.", "NIST: correlation does not imply causality.", src("CORRELATION")]]))
    # Leaderboard
    rows = []
    for s in EVAL["strategies"]:
        gates = s["gates"]
        passed = sum(v == "pass" for v in gates.values())
        rows.append([s["id"], s["division"], s["name"], s["n"], f"{passed}/12", "Eligible" if s["eligible"] else "Research only / blocked", s["reward"], blank(), src_url(s["source_url"], "Source")])
    pages["leaderboard"] = ("Strategy leaderboard", "Reward-based competition. No eligible strategy means no ranking and no reward.",
        callout("<strong>0 eligible strategies · 0 reward points.</strong> Probability research is displayed separately from betting ROI. No winner is manufactured.") +
        table(["ID", "Division", "Strategy", "n", "Gates passed", "Status", "Reward points", "Market ROI", "Source"], rows, "All registered strategies", "leaderboard-table", True) +
        "<h2>Reward rules</h2>" + table(["Tier", "Rule", "Funded?", "Source"], [["Gold", "Every applicable gate plus 100 prospective selections.", "No — virtual badge only", src("REPO")], ["Silver", "All retrospective gates; prospective replication pending. No reward.", "No", src("REPO")], ["Research only", "Any failed or blocked gate. No reward.", "No", src("REPO")]]))
    # Validation
    grows = [[g["id"], g["name"], g["rule"], ", ".join(g["source_ids"]), src(g["source_ids"][0])] for g in PROTOCOL["gates"]]
    primary = []
    for mid in ("M2","M4"):
        for metric in ("win","margin","total"):
            d = EVAL["improvements"][mid][metric]
            primary.append([f"{mid}-{metric}", signed(d["mean_improvement"],5), f'{fmt(d["ci95"][0],5)} to {fmt(d["ci95"][1],5)}', fmt(d["p_perm"],4), fmt(d["p_holm"],4), "Pass" if d["ci95"][0] > 0 and d["p_holm"] < .05 else "Fail", src("FDR")])
    matrix = []
    for s in EVAL["strategies"]:
        matrix.append([s["id"]] + [s["gates"][f"G{i:02}"] for i in range(1,13)] + [src_url(s["source_url"], "Source")])
    pages["validation"] = ("Validation gates", "Every strategy must pass every applicable gate. Blocked is not passed.",
        table(["Gate", "Name", "Rule", "Source IDs", "Source"], grows, "Pre-registered gates") +
        "<h2>Primary trial family</h2>" + table(["Trial", "Mean improvement", "95% CI", "Permutation p", "Holm p", "G04", "Source"], primary) +
        "<h2>Gate matrix</h2>" + table(["Strategy"] + [f"G{i:02}" for i in range(1,13)] + ["Source"], matrix, "Pass / fail / blocked by strategy", "gate-matrix", True))
    # Methodology
    mrows = [[k, v["name"], v["role"], v["prior_weight"], v["decay"], "Yes" if v["rest"] else "No", src("STAND-2025")] for k,v in PROTOCOL["models"].items()]
    lrows = [[k, v, src("RULES")] for k,v in PROTOCOL["line_definitions"].items()]
    drows = [[d, src("REPO")] for d in PROTOCOL["disclosures"]]
    pages["methodology"] = ("Methodology", "Frozen protocol, line definitions and explicit modeling assumptions.",
        table(["Model", "Name", "Role", "Prior weight", "Decay", "Rest overlay", "Source"], mrows) +
        "<h2>Line definitions</h2>" + table(["Object", "Definition", "Source"], lrows) +
        "<h2>Disclosures</h2>" + table(["Disclosure", "Source"], drows) +
        f'<p>Full protocol: <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/protocol.json" rel="noopener">protocol.json ↗</a></p>')
    # Data games
    grows = [[g["season"], g["week"], g["date"], g["team_a"], g["score_a"], g["team_b"], g["score_b"], "Final", src(g["source_id"], "NFL schedule")] for g in GAMES]
    pages["data-games"] = ("Official games", "392 final-score observations. Listing order is not an inferred home/away assignment.",
        table(["Season", "Week", "Date", "Team A", "Score A", "Team B", "Score B", "Status", "Source"], grows, "Official NFL schedule observations", "games-table", True))
    # Standings
    srows = [[r["season"], r["team"], r["team_name"], r["w"], r["l"], r["t"], r["pf"], r["pa"], src(r["source_id"], "NFL standings")] for r in STANDINGS]
    pages["data-standings"] = ("Official standings", "2024 prior, 2025 full season and 2026 snapshot through November 1.",
        table(["Season", "Team", "Name", "W", "L", "T", "PF", "PA", "Source"], srows, "Official standings rows", "standings-table", True))
    # Players
    prows = [[p["player"], p["team"], p["season"], p["week"], p["date"], p["metric_a"], fmt(p["value_a"],0), p["metric_b"], fmt(p["value_b"],0), src(p["source_id"])] for p in PLAYERS]
    pages["data-players"] = ("Player game logs", "Official 2026 regular-season rows. Missing numeric cells are preserved blank.",
        table(["Player", "Team", "Season", "Week", "Date", "Metric A", "Value A", "Metric B", "Value B", "Source"], prows, "Official player logs", "players-table", True))
    # Predictions
    predrows = [[r["model"], r["season"], r["week"], r["date"], r["team_a"], r["team_b"], fmt(float(r["mean_margin"]),2), fmt(float(r["mean_total"]),2), signed(float(r["spread_a"])), fmt(float(r["total_line"]),1), pct(float(r["p_a_winshare"])), r["actual_margin"], r["actual_total"], "Yes" if r["evaluation"]=="True" else "Dev", src_url(r["source_url"], "NFL schedule")] for r in PREDICTIONS]
    pages["data-predictions"] = ("Walk-forward predictions", "All 1,568 model-game predictions. Derived values, not official NFL lines.",
        table(["Model", "Season", "Week", "Date", "Team A", "Team B", "Margin", "Total", "A spread", "Total line", "A win-share", "Actual margin", "Actual total", "Split", "Source"], predrows, "Chronological predictions", "predictions-table", True))
    # Sources
    srcrows = [[s["id"], s["title"], s["publisher"], s["observed_on"], s["inspection"], s["supports"], src_url(s["url"], "Open source")] for s in SOURCES.values()]
    pages["sources"] = ("Source register", "Official NFL observations plus official method/governance references. Raw HTML is not archived.",
        table(["ID", "Title", "Publisher", "Observed", "Inspection", "Supports", "Link"], srcrows, "Source register", "sources-table", True))
    # Repository audit
    a = AUDIT_SUMMARY
    arows = [["Files inventoried", a.get("files",0), src("REPO")], ["Text lines scanned", a.get("text_lines",0), src("REPO")], ["HTML data rows", a.get("html_data_rows",0), src("REPO")], ["CSV rows", a.get("csv_rows",0), src("REPO")], ["Automated findings", a.get("findings",0), src("REPO")]]
    statusrows = [[k, v, src("REPO")] for k,v in a.get("html_status_counts",{}).items()]
    csvstatus = [[k, v, src("REPO")] for k,v in a.get("csv_status_counts",{}).items()]
    archives = [[name, f'<a href="{e(href)}">Open archive →</a>', src_url(url, "Repository directory")] for name,href,url in ARCHIVES]
    files = []
    if (AUDIT / "files.csv").exists():
        import csv
        with (AUDIT / "files.csv").open() as f:
            files = list(csv.DictReader(f))
    frows = [[r["path"], r["scope"], r["lines"], r["bytes"], src_url(r["source_url"], "File")] for r in files]
    pages["repository-audit"] = ("Repository audit", "Exhaustive inventory and source-relevance boundary. Legacy NBA/third-party claims are not certified as NFL evidence.",
        table(["Entry", "Count", "Source"], arows) +
        "<h2>HTML row source coverage</h2>" + table(["Status", "Rows", "Source"], statusrows) +
        "<h2>CSV row source coverage</h2>" + table(["Status", "Rows", "Source"], csvstatus) +
        callout("Full ledgers: <a href='https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/audit/files.csv'>files.csv</a>, <a href='https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/audit/html_rows.csv'>html_rows.csv</a>, <a href='https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/audit/csv_rows.csv'>csv_rows.csv</a>. Inventory is exhaustive; claim-level certification is limited to the official-only nfl-lab snapshot.") +
        '<h2 id="archives">Preserved archives</h2>' + table(["Archive", "Local link", "Source"], archives) +
        "<h2>File inventory</h2>" + table(["Path", "Scope", "Lines", "Bytes", "Source"], frows, "All scanned files", "files-table", True))
    # Flagged
    frows = [[f["id"], f["severity"], f["status"], f["title"], f["finding"], src_url(f["source_url"], f["source_label"])] for f in FLAGS]
    pages["flagged"] = ("Flagged for review", "Non-blocking issues and unverified fields. Nothing here is silently filled or inferred.",
        table(["ID", "Severity", "Status", "Issue", "Finding / required review", "Source"], frows, "Review register", "flags-table", True))
    # Verification
    if VERIFY:
        vrows = [[c["name"], c["status"], c["detail"], src_url(c.get("source_url", "https://github.com/sassnarep3-star/Own4"), "Evidence")] for c in VERIFY["checks"]]
        vbody = table(["Check", "Status", "Detail", "Source"], vrows) + callout(VERIFY.get("conclusion", ""), "ok" if VERIFY.get("pass") else "warn")
    else:
        vbody = callout("Verification report pending. Run verify.py after build.")
    pages["verification"] = ("Verification & deployment", "Automated checks, source coverage and publication evidence.", vbody)
    for slug, (title, subtitle, body) in pages.items():
        (PAGES / f"{slug}.html").write_text(page(slug, title, subtitle, body))
    (SITE / "index.html").write_text(build_index(""))
    # Root canonical NFL landing, preserving legacy archives via governance page.
    (REPO / "index.html").write_text(build_index("nfl-lab/site/"))


def assets():
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    css = """
:root{--bg:#f5f7fa;--panel:#fff;--ink:#10202b;--muted:#5b6b78;--line:#dce4ec;--nav:#0d1b2a;--nav2:#13293d;--accent:#0f8b8d;--accent2:#0b6e6f;--warn:#fff6e5;--warnline:#e8b04b;--ok:#e8f6ef;--bad:#fdecec;--radius:12px}*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}a{color:var(--accent2);text-decoration:none}a:hover{text-decoration:underline}.skip{position:absolute;left:-999px;top:0;background:#fff;padding:8px;z-index:10}.skip:focus{left:8px}.layout{display:grid;grid-template-columns:250px 1fr;min-height:100vh}.sidebar{background:var(--nav);color:#dbe7f0;padding:22px 16px;position:sticky;top:0;height:100vh;overflow:auto}.brand{display:block;color:#fff;font-weight:800;font-size:22px;margin:0 8px 22px}.brand span{display:block;color:#7fd1d3;font-size:13px;letter-spacing:.12em;text-transform:uppercase}.nav-group{margin-bottom:18px}.nav-title{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#8aa2b5;margin:0 8px 6px}.sidebar nav a{display:block;color:#dbe7f0;padding:7px 10px;border-radius:8px;font-size:14px}.sidebar nav a:hover,.sidebar nav a.active{background:var(--nav2);color:#fff;text-decoration:none}.content{min-width:0;display:flex;flex-direction:column}.topbar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 28px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.crumb{display:block;color:var(--muted);font-size:12px}.badge{background:#e6f4f4;color:var(--accent2);border:1px solid #bfe1e1;border-radius:999px;padding:5px 12px;font-size:12px;font-weight:700;white-space:nowrap}main{padding:28px;max-width:1400px;width:100%;margin:0 auto}h1{font-size:30px;margin:0 0 6px}h2{font-size:21px;margin:30px 0 12px}.subtitle{color:var(--muted);margin:0 0 22px;max-width:900px}.hero{display:flex;justify-content:space-between;gap:24px;background:linear-gradient(135deg,#0d1b2a,#133a4a);color:#fff;border-radius:var(--radius);padding:28px;margin-bottom:22px}.hero h2{margin:6px 0 10px;font-size:26px}.hero p{color:#cfe0ea;max-width:720px}.eyebrow{letter-spacing:.12em;text-transform:uppercase;font-size:12px;color:#7fd1d3!important;font-weight:700}.hero-status{align-self:flex-start;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:8px 14px;font-size:13px;white-space:nowrap}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#f0b429;margin-right:6px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:18px 0}.kpi{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:16px}.kpi-value{font-size:28px;font-weight:800;color:var(--nav)}.kpi-label{font-weight:700;margin-top:2px}.kpi-note{color:var(--muted);font-size:12px;margin-top:4px}.callout{background:var(--warn);border:1px solid var(--warnline);border-left:5px solid var(--warnline);border-radius:10px;padding:14px 16px;margin:18px 0}.callout.ok{background:var(--ok);border-color:#79c99e;border-left-color:#2f9e68}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:18px;color:var(--ink)}.card:hover{border-color:var(--accent);text-decoration:none}.card h3{margin:0 0 6px}.card p{color:var(--muted);margin:0 0 10px}.card span{color:var(--accent2);font-weight:700}.table-wrap{overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);margin:10px 0 22px}table{border-collapse:collapse;width:100%;font-size:13.5px}caption{text-align:left;padding:12px 14px;font-weight:700;color:var(--muted);border-bottom:1px solid var(--line)}th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}thead th{background:#eef3f7;position:sticky;top:0;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#33475b}tbody tr:nth-child(even){background:#fafcfd}tbody tr:hover{background:#f0f7f7}.blank{display:inline-block;min-width:28px;min-height:14px;border-bottom:2px dotted #b9c6d2}.filter{display:flex;align-items:center;gap:10px;margin:10px 0;color:var(--muted);font-size:13px}.filter input{padding:8px 12px;border:1px solid var(--line);border-radius:8px;min-width:260px;font:inherit}footer{margin-top:auto;padding:20px 28px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;background:#fff}@media(max-width:900px){.layout{grid-template-columns:1fr}.sidebar{position:static;height:auto}.sidebar nav{display:flex;flex-wrap:wrap;gap:4px}.nav-group{margin:0}.nav-title{display:none}.hero{flex-direction:column}.topbar{position:static}main{padding:18px}}@media print{.sidebar,.topbar,.filter,.skip{display:none}.layout{display:block}main{max-width:none}.table-wrap{overflow:visible;border:none}table{font-size:10px}}
"""
    js = """
document.querySelectorAll('input[data-filter]').forEach(function(input){input.addEventListener('input',function(){var q=this.value.toLowerCase();var id=this.getAttribute('data-filter');var table=id?document.getElementById(id):this.closest('main').querySelector('table');if(!table)return;table.querySelectorAll('tbody tr').forEach(function(tr){tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';});});});
"""
    (SITE / "assets" / "style.css").write_text(css)
    (SITE / "assets" / "app.js").write_text(js)


if __name__ == "__main__":
    assets()
    build_pages()
    print(f"Built {len(list(PAGES.glob('*.html')))} subpages + site index + canonical root index")

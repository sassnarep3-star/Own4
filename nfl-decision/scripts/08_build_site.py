#!/usr/bin/env python3
"""Generate the nfl-decision dashboard: landing page + category subpages."""
import csv, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, DATA)
import questions as QMOD
import suggestions as SMOD
import injuries_wk10 as INJ

SITE = "https://sassnarep3-star.github.io/Own4/nfl-decision"
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision"

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("questions.html", "Questions & gaps"),
    ("suggestions.html", "Suggestions"),
    ("injuries.html", "Injuries & depth"),
    ("own-lines.html", "Own lines"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation gates"),
    ("correlations.html", "Correlations"),
    ("props.html", "Prop combos"),
    ("data.html", "Data & provenance"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]
GROUPS = {
    "Decide": ["index.html", "executive-summary.html", "questions.html", "suggestions.html"],
    "Evidence": ["injuries.html", "own-lines.html", "leaderboard.html", "validation.html",
                 "correlations.html", "props.html"],
    "Audit": ["data.html", "repo-review.html", "flagged.html", "sources.html"],
}


def e(x):
    return html.escape(str(x)) if x is not None else ""


def blank(v):
    return '<span class="blank">—</span>' if v in (None, "", "None") else e(v)


def pill(text, kind="neu"):
    return f'<span class="pill p-{kind}">{e(text)}</span>'


def src(url, label=None, internal=False):
    if not url:
        return '<span class="blank">no source</span>'
    txt = label or ("repo" if ("github.com" in url or url.startswith("./") or url.startswith("#")) else "official")
    return f'<a class="src" href="{e(url)}" title="{e(url)}">{e(txt)}</a>'


def J(name):
    return json.load(open(os.path.join(DATA, name)))


def page(name, title, body, lede="", home=False):
    on = name
    nav = "".join(
        f'<a href="{h}" class="{"on" if h == on else ""}">{t}</a>' for h, t in NAV if h != "index.html")
    side = ""
    for g, items in GROUPS.items():
        side += f"<h4>{g}</h4>"
        for h, t in NAV:
            if h in items:
                side += f'<a href="{h}" class="{"on" if h == on else ""}">{t}</a>'
    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · NFL Decision Lab</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="top"><div class="wrap">
  <div class="brand">NFL <span>Decision Lab</span></div>
  <nav class="main"><a href="index.html" class="{"on" if home else ""}">Overview</a>{nav}</nav>
</div></header>
<div class="layout">
  <aside class="side">{side}</aside>
  <main>
    <h1>{e(title)}</h1>
    {f'<p class="lede">{lede}</p>' if lede else ""}
    {body}
  </main>
</div>
<footer class="foot">
  <p><b>Analytical research only — not wagering advice.</b> No money, prizes or wagering are offered.
  Every numeric cell is either transcribed from an official NFL page or computed in this repository;
  cells that could not be confirmed are left blank and listed on the
  <a href="flagged.html">Flagged for review</a> page.</p>
  <p>If gambling is a problem for you or someone you know, the National Council on Problem Gambling
  operates a 24/7 confidential helpline: <a href="https://www.ncpgambling.org/help-treatment">1-800-MY-RESET (1-800-697-3738)</a>.</p>
  <p>Generated 2026-11-12 by session <code>arena/e2b19bf6-own4</code>. Data: <a href="data.html">provenance</a>.</p>
</footer>
</body></html>"""
    open(os.path.join(ROOT, name), "w").write(doc)
    return doc


def table(headers, rows, wrap=True, row_ids=None):
    h = "".join(f'<th class="{c}">{t}</th>' for t, c in headers)
    b = ""
    for i, r in enumerate(rows):
        rid = f' id="{row_ids[i]}"' if row_ids else ""
        b += f"<tr{rid}>" + "".join(f'<td class="{c}">{v}</td>' for v, c in r) + "</tr>"
    t = f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
    return f'<div class="tbl-wrap">{t}</div>' if wrap else t


def card(k, v, s=""):
    return f'<div class="card"><div class="k">{e(k)}</div><div class="v">{v}</div><div class="s">{e(s)}</div></div>'


# ---------------------------------------------------------------- overview
def build_index():
    res = J("results_2026.json"); bt = J("backtest.json"); fc = J("forecast_leaderboard.json")
    ol = J("own_lines_wk10.json"); pr = J("props.json"); co = J("correlations.json")
    injn = sum(len(v[1]) for v in INJ.T.values())
    body = '<div class="cards">'
    body += card("2026 games verified", "136", "160/160 official cells match")
    body += card("Leaderboard strategies", "0 / 5", "nothing passed the gates")
    body += card("Reward points awarded", "600", "forecast skill only")
    body += card("Questions to answer", len(QMOD.Q), f'{sum(1 for q in QMOD.Q if q["status"] == "unknown")} still open')
    body += card("Suggestions to review", len(SMOD.S), "each with options + a recommendation")
    body += card("Week 10 own lines", ol["n_games"], "13 in the forward log")
    body += "</div>"

    body += '<div class="note warn"><b>The one-line state of the project:</b> the model is honest and reproducible, '
    body += 'it loses to the closing line, and <b>no betting edge can be claimed</b> because no official price archive exists. '
    body += 'Forecast skill is the only thing that can be measured today, so that is the only thing rewarded.</div>'

    body += "<h2>What this site is</h2><p>A decision surface, not a picks page. Three things, in order:</p>"
    body += table([("Layer", ""), ("What it does", ""), ("Where", "")], [
        [("1. Questions", ""), ("Lists what must be answered before any decision is reasonable, separating what we know from what we do not.",
                                ""), (src("questions.html", "open the register", True), "")],
        [("2. Suggestions", ""), ("Puts options, evidence, cost and risk side by side so you can pick a path instead of accepting one silently.",
                                  ""), (src("suggestions.html", "open the board", True), "")],
        [("3. Evidence", ""), ("The measured results those suggestions rest on — every number computed here or transcribed from an official page.",
                               ""), (src("validation.html", "open the gates", True), "")],
    ])

    body += "<h2>The five numbers that matter</h2>"
    s1 = next(t for t in bt["holdout"] if t["id"] == "S1")
    body += table([("Finding", ""), ("Value", "n"), ("Source", ""), ("Reads as", "")], [
        [("Own Elo margin vs market margin, holdout 2018-25", ""),
         ("market r = 0.430 vs model r = 0.357", "n"), (src("correlations.html", "derived", True), ""),
         ("the market is better informed than the model", "")],
        [("Best betting strategy (S1 spread)", ""),
         (f'ROI {s1["roi"]*100:+.2f}%, CI [{s1["roi_ci95"][0]*100:+.2f}%, {s1["roi_ci95"][1]*100:+.2f}%]', "n"),
         (src("validation.html", "derived", True), ""),
         ("indistinguishable from luck; 98% of profit from one season", "")],
        [("QB pass-yards + WR1 rec-yards combo lift", ""),
         (f'{(pr["combo"]["lift"] - 1)*100:+.0f}% vs independent (phi = {pr["combo"]["phi"]})', "n"),
         (src(REPO + "/data/props.json", "repo", True), ""),
         ("the one real, unpriced signal found — but no SGP price exists", "")],
        [("Cross-game parlay leg dependence", ""),
         (f'phi = {co["dependence_tests"][0]["phi"]}', "n"), (src("correlations.html", "derived", True), ""),
         ("legs may be multiplied safely", "")],
        [("Forecast skill vs the market", ""),
         (f'MAE {fc["board"][1]["margin_mae"]} vs {fc["board"][0]["margin_mae"]}', "n"),
         (src("leaderboard.html", "derived", True), ""),
         ("the model beats naive baselines, not the market", "")],
    ])

    body += "<h2>Read in this order</h2>"
    body += table([("Step", ""), ("Page", ""), ("Why", "")], [
        [("1", ""), (src("executive-summary.html", "Executive summary", True), ""), ("the whole thing on one screen", "")],
        [("2", ""), (src("questions.html", "Questions &amp; gaps", True), ""), ("what is blocking a decision right now", "")],
        [("3", ""), (src("suggestions.html", "Suggestions", True), ""), (f'{len(SMOD.S)} paths, each with options and a recommendation', "")],
        [("4", ""), (src("flagged.html", "Flagged for review", True), ""), ("everything unverified or irregular, with links", "")],
    ])
    page("index.html", "NFL Decision Lab",
         body, "Verified 2026 NFL evidence, an open question register, and a suggestions board you can choose from.", home=True)


# ------------------------------------------------------- executive summary
def build_exec():
    bt = J("backtest.json"); fc = J("forecast_leaderboard.json"); pr = J("props.json")
    ol = J("own_lines_wk10.json"); co = J("correlations.json"); cfg = J("model_config.json")
    s1 = next(t for t in bt["holdout"] if t["id"] == "S1")
    body = '<div class="note"><b>Bottom line.</b> The pipeline is reproducible and the provenance is exact, '
    body += 'but there is no tradeable edge in it. Four of five registered strategies have negative ROI on the holdout; '
    body += 'the one that is positive cannot be separated from luck. <b>0 of 1000 betting reward points are awarded.</b> '
    body += '600 forecast points are awarded, because forecast skill is measurable without a price.</div>'

    body += "<h2>1. What was verified against official sources</h2>"
    body += table([("Claim", ""), ("Result", "c"), ("Official source", "")], [
        [("2026 results, Weeks 1-9", ""), (pill("136 games", "good"), ""), (src("https://www.nfl.com/scores/2026/REG9", "nfl.com scores"), "")],
        [("All 32 team records recompute", ""), (pill("160/160 cells", "good"), ""), (src("https://www.nfl.com/standings/league/2026/REG", "nfl.com standings"), "")],
        [("Week 10 injury report", ""), (pill(f"{sum(len(v[1]) for v in INJ.T.values())} players", "good"), ""), (src("https://www.nfl.com/injuries/", "nfl.com injuries"), "")],
        [("Week 10 schedule", ""), (pill("14 games", "good"), ""), (src("https://www.nfl.com/schedules/2026/by-week/week-10", "nfl.com schedule"), "")],
        [("Official depth charts", ""), (pill("404 — does not exist", "bad"), ""), (src("https://www.nfl.com/depth-charts/", "nfl.com (404)"), "")],
        [("Official betting odds", ""), (pill("no source exists", "bad"), ""), (src("https://www.nfl.com/games", "nfl.com games"), "")],
    ])

    body += "<h2>2. Model performance</h2>"
    body += table([("Metric", ""), ("Holdout 2018-2025", "n"), ("Benchmark", "n"), ("Verdict", "c"), ("Source", "")], [
        [("Margin MAE", ""), (f'{cfg["dev_margin_mae"]} (dev window)', "n"), ("market 9.844", "n"), (pill("market wins", "bad"), ""),
         (src("leaderboard.html", "derived", True), "")],
        [("corr(model margin, realised)", ""), (f'{co["correlations"][1]["r"]:.3f}', "n"), (f'market {co["correlations"][0]["r"]:.3f}', "n"),
         (pill("market wins", "bad"), ""), (src("correlations.html", "derived", True), "")],
        [("S1 spread ROI", ""), (f'{s1["roi"]*100:+.2f}%', "n"), ("0%", "n"), (pill("luck", "warn"), ""),
         (src("validation.html", "derived", True), "")],
        [("S1 95% CI on ROI", ""), (f'[{s1["roi_ci95"][0]*100:+.2f}%, {s1["roi_ci95"][1]*100:+.2f}%]', "n"), ("contains 0", "n"),
         (pill("not significant", "warn"), ""), (src("validation.html", "derived", True), "")],
        [("S1 profit concentration", ""), (f'{s1["seasons"]["max_season_profit_share"]*100:.0f}% in one season', "n"), ("< 50% required", "n"),
         (pill("fails robustness", "bad"), ""), (src("leaderboard.html", "derived", True), "")],
        [("Look-ahead perturbation test", ""), (pill("0 predictions changed", "good"), ""), ("must be 0", "n"), (pill("pass", "good"), ""),
         (src(REPO + "/data/backtest.json", "repo", True), "")],
    ], )

    body += "<h2>3. Leaderboard outcome</h2>"
    rows = []
    for t in bt["holdout"]:
        rows.append([(t["id"], ""), (f'{t["n"]:,}', "n"), (f'{t["roi"]*100:+.2f}%', "n"),
                     (f'[{t["roi_ci95"][0]*100:+.2f}%, {t["roi_ci95"][1]*100:+.2f}%]', "n"),
                     (f'{t["bh_q"]:.3f}', "n"),
                     (pill(t["tier"], {"Bronze": "warn", "Rejected": "bad", "Silver": "good"}.get(t["tier"], "neu")), "c"),
                     ("0", "n"), (src(REPO + "/data/backtest.json", "repo", True), "")])
    body += table([("Strategy", ""), ("Bets", "n"), ("ROI", "n"), ("95% CI", "n"), ("FDR q", "n"), ("Tier", "c"), ("Points", "n"), ("Source", "")], rows)
    body += f'<p class="lede">Reward pool: {bt["awarded_points"]} of 1000 betting points awarded. The pool rolls over.</p>'

    body += "<h2>4. Forecast leaderboard (the part that pays)</h2>"
    rows = [[(b["forecaster"], ""), (b["n"], "n"), (b["margin_mae"], "n"), (b["total_mae"], "n"),
             (b["ats_accuracy"] if b["ats_accuracy"] is not None else "n/a", "n"),
             (b["brier"], "n"), (b["reward_points"], "n"),
             (src(REPO + "/data/forecast_leaderboard.json", "repo", True), "")] for b in fc["board"]]
    body += table([("Forecaster", ""), ("Games", "n"), ("Margin MAE", "n"), ("Total MAE", "n"),
                   ("ATS acc.", "n"), ("Brier", "n"), ("Points", "n"), ("Source", "")], rows)
    body += f'<div class="note">{e(fc["honest_note"])}</div>'

    body += "<h2>5. Injuries and depth</h2>"
    body += f'<p>{len(INJ.T)} of 32 clubs publish a Week 10 practice report. {len(INJ.DEPTH)} depth-chart deficiencies are confirmed by an official NFL.com article naming the replacement. '
    body += 'No official depth chart exists, so <b>no player is labelled 1st/2nd/3rd string by this project</b> except where the official article itself says so.</p>'
    body += f'<p>Confirmed quarterback changes this week: SEA (Darnold out → Lock), MIA (Willis to IR → McCord, first career start), '
    body += 'BAL (Jackson out 6-9 weeks → Brissett, after an undrafted 3rd-stringer started Week 9), AZ (rookie Carson Beck\'s first career start), '
    body += 'CLE (Watson returns in place of Sanders), MIN (Cousins acquired; starter not committed).</p>'

    body += "<h2>6. What would change the answer</h2>"
    body += table([("Change", ""), ("Unblocks", ""), ("Cost", "c"), ("Detail", "")], [
        [("An archived odds history (S14)", ""), ("Gate G7 for every strategy — the binding constraint", ""), (pill("high", "bad"), "c"), (src("suggestions.html#S14", "S14", True), "")],
        [("Archived same-game-parlay prices (S10)", ""), ("The +45% prop combo lift becomes testable", ""), (pill("medium", "warn"), "c"), (src("suggestions.html#S10", "S10", True), "")],
        [("An official 2026 player feed (S17)", ""), ("Extends props past 2022", ""), (pill("high", "bad"), "c"), (src("suggestions.html#S17", "S17", True), "")],
        [("A weekly injury snapshot (S16)", ""), ("Injury effects become back-testable next season", ""), (pill("low", "good"), "c"), (src("suggestions.html#S16", "S16", True), "")],
        [("A licence for depth charts (S02)", ""), ("Full 1st/2nd/3rd-string tracking you asked for", ""), (pill("medium", "warn"), "c"), (src("suggestions.html#S02", "S02", True), "")],
    ])
    body += "<h2>7. Reproduce</h2><pre style='background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto;font-size:12.5px'>"
    body += "python3 nfl-decision/scripts/01_results.py\npython3 nfl-decision/scripts/02_model.py\npython3 nfl-decision/scripts/03_backtest.py\npython3 nfl-decision/scripts/04_correlations.py\npython3 nfl-decision/scripts/05_props.py\npython3 nfl-decision/scripts/06_own_lines.py\npython3 nfl-decision/scripts/07_forecast.py\npython3 nfl-decision/scripts/08_build_site.py"
    body += "</pre>"
    page("executive-summary.html", "Executive summary", body,
         "Everything important, in the order a decision needs it.")


# ------------------------------------------------------------- questions
def build_questions():
    groups = {}
    for q in QMOD.Q:
        groups.setdefault(q["group"], []).append(q)
    cnt = {s: sum(1 for q in QMOD.Q if q["status"] == s) for s in ("known", "partial", "unknown")}
    body = '<div class="cards">'
    body += card("Answered", cnt["known"], "verified against a source")
    body += card("Partly answered", cnt["partial"], "some evidence, a gap remains")
    body += card("Open", cnt["unknown"], "blocks a decision")
    body += "</div>"
    body += '<div class="note warn"><b>How to read this.</b> Each question lists what is <b>known</b> with a source, '
    body += 'what is <b>not known</b>, why that blocks a decision, and which suggestion would obtain it. '
    body += 'A blank <b>Answer</b> means no verified answer exists — nothing was inferred to fill it.</div>'

    body += table([("ID", ""), ("Group", ""), ("Status", "c"), ("Blocks", ""), ("Question", "")],
                  [[(f'<a href="#{q["id"]}">{q["id"]}</a>', ""), (q["group"], ""),
                    (pill(q["status"], {"known": "good", "partial": "warn", "unknown": "bad"}[q["status"]]), "c"),
                    (q["blocks"], ""), (e(q["question"]), "")] for q in QMOD.Q])

    for g, items in groups.items():
        body += f"<h2>{e(g)}</h2>"
        for q in items:
            ks = " · ".join(f'<a href="{e(u)}">{e(l)}</a>' for l, u in q["known_sources"])
            ans = f'<b>{e(q["answer"])}</b>' if q["answer"] else '<span class="blank">no verified answer — left blank</span>'
            body += f'''<div class="qa" id="{q["id"]}">
  <div class="q"><span class="id">{q["id"]}</span><span class="txt">{e(q["question"])}</span>
    {pill(q["status"], {"known": "good", "partial": "warn", "unknown": "bad"}[q["status"]])}
    <span class="pill p-neu">blocks: {e(q["blocks"])}</span></div>
  <div class="b"><dl>
    <dt>Answer</dt><dd>{ans}</dd>
    <dt>Known</dt><dd>{e(q["known"])} <span class="src">[{ks}]</span></dd>
    <dt>Not known</dt><dd>{e(q["unknown"])}</dd>
    <dt>Why it blocks</dt><dd>{e(q["why_it_blocks"])}</dd>
    <dt>Suggestion</dt><dd>{e(q["suggestion"])}</dd>
  </dl></div></div>'''
    page("questions.html", "Questions &amp; gaps",
         body, "What must be answered before any decision is reasonable — separating what we know from what we do not.")


# ------------------------------------------------------------ suggestions
def build_suggestions():
    body = '<div class="note"><b>This page exists so a decision can be made before code changes.</b> '
    body += 'Nothing here has been implemented. Each item lists the context, the options considered, the evidence, '
    body += 'the cost, the risk and a recommendation. Accept, reject or defer each one.</div>'
    body += table([("ID", ""), ("Group", ""), ("Suggestion", ""), ("Cost", "c"), ("Risk", "c"), ("Status", "c")],
                  [[(f'<a href="#{s["id"]}">{s["id"]}</a>', ""), (s["group"], ""), (e(s["title"]), ""),
                    (pill(s["cost"], {"low": "good", "none": "good", "medium": "warn", "high": "bad"}.get(s["cost"], "neu")), "c"),
                    (pill(s["risk"], {"low": "good", "medium": "warn", "high": "bad"}.get(s["risk"], "neu")), "c"),
                    (pill(s["status"], "good" if s["status"] == "recommended" else "warn"), "c")] for s in SMOD.S])

    for s in SMOD.S:
        opts = "".join(
            f'<div class="opt"><div><div class="h">option</div>{e(o[0])}</div>'
            f'<div><div class="h">evidence</div>{e(o[1])}</div>'
            f'<div><div class="h">cost / failure mode</div>{e(o[2])}</div></div>' for o in s["options"])
        ev = " · ".join(f'<a href="{e(u)}">{e(l)}</a>' for l, u in s["evidence"])
        body += f'''<div class="sugg" id="{s["id"]}">
  <div class="hd"><span class="id">{s["id"]}</span><span class="t">{e(s["title"])}</span>
    {pill(s["group"], "neu")}{pill("cost: " + s["cost"], {"low": "good", "none": "good", "medium": "warn", "high": "bad"}.get(s["cost"], "neu"))}
    {pill("risk: " + s["risk"], {"low": "good", "medium": "warn", "high": "bad"}.get(s["risk"], "neu"))}</div>
  <div class="bd">
    <p><b>Context.</b> {e(s["context"])}</p>
    <p><b>Why it matters.</b> {e(s["why_it_matters"])}</p>
    {opts}
    <div class="rec"><b>Recommendation.</b> {e(s["recommendation"])}</div>
    <p style="margin:9px 0 0" class="src">Evidence: {ev}</p>
  </div></div>'''
    page("suggestions.html", "Suggestions",
         body, "Options, evidence, cost and risk side by side — so you can choose a path instead of inheriting one.")


# --------------------------------------------------------------- injuries
def build_injuries():
    rows = []
    for team, (game, players) in sorted(INJ.T.items()):
        for p in players:
            status = p[4]
            kind = "bad" if status == "Out" else ("warn" if status == "Questionable" else "neu")
            rows.append([
                (f'<a href="https://www.nfl.com/teams/">{e(team)}</a>', ""), (e(game), ""),
                (e(p[0]), ""), (e(p[1]), ""),
                (blank(p[2]) if p[2] else '<span class="blank">blank</span>', ""),
                (e(p[3]), ""),
                (pill(status, kind) if status else '<span class="blank">blank</span>', "c"),
                (src(INJ.INJURY_SOURCE, "nfl.com"), "")
            ])
    body = f'<div class="cards">'
    body += card("Clubs reporting", f"{len(INJ.T)} / 32", "LAC and BAL: 'No Injuries Reported'")
    body += card("Player rows", len(rows), "transcribed from the official report")
    body += card("Ruled Out", sum(1 for v in INJ.T.values() for p in v[1] if p[4] == "Out"), "confirmed on the game-status report")
    body += card("Did not practice", sum(1 for v in INJ.T.values() for p in v[1] if p[3] == INJ.DNP), "practice status only")
    body += "</div>"
    body += '<div class="note warn"><b>Blank is a real value here.</b> The official page frequently lists a practice status '
    body += 'with no injury and no game status. Those cells are left blank rather than inferred. A practice status is '
    body += '<b>not</b> converted into a game expectation.</div>'

    body += "<h2>Official designation definitions</h2>"
    body += table([("ID", ""), ("Official rule", ""), ("Publisher", ""), ("Source", "")],
                  [[(p["id"], ""), (e(p["claim"]), ""), (e(p["publisher"]), ""), (src(p["url"], "nfl.com"), "")] for p in INJ.POLICY])

    body += "<h2>Confirmed depth-chart deficiencies</h2>"
    body += ('<p class="lede">A row appears here only when an official NFL.com article explicitly states that a named '
             'replacement is starting or will start. No string-depth label is applied by this project.</p>')
    drows = [[(f'<a href="https://www.nfl.com/teams/">{e(d["team"])}</a>', ""), (e(d["unit"]), ""),
              (e(d["position"]), ""), (e(d["starter_out"]) or '<span class="blank">—</span>', ""),
              (e(d["starter_out_status"]), ""),
              (e(d["replacement"]) or '<span class="blank">not named officially</span>', ""),
              (e(d["replacement_tier"]), ""),
              (pill(d["depth_cost"], {"critical": "bad", "high": "bad", "medium": "warn", "low": "good"}.get(d["depth_cost"], "neu")), "c"),
              (src(d["source"], "official"), "")] for d in INJ.DEPTH]
    body += table([("Team", ""), ("Unit", ""), ("Position", ""), ("Starter out", ""), ("Status", ""),
                   ("Replacement", ""), ("Depth", ""), ("Cost", "c"), ("Source", "")], drows)
    body += "<h3>Quoted evidence for each row</h3>"
    body += table([("Row", ""), ("Official sentence", ""), ("Source", "")],
                  [[(f'{d["team"]} {d["position"]}', ""), (f'“{e(d["evidence"])}”', ""),
                    (src(d["source"], "official"), "")] for d in INJ.DEPTH])

    body += "<h2>What is blocked</h2>"
    body += table([("ID", ""), ("Item", ""), ("Status", "c"), ("Why", "")],
                  [[(g["id"], ""), (e(g["item"]), ""), (pill("blocked", "bad"), "c"),
                    (f'{e(g["detail"])} {src(g["url"], "link")}', "")] for g in INJ.GAPS])

    body += "<h2>Every player row</h2>"
    body += table([("Team", ""), ("Game", ""), ("Player", ""), ("Pos", ""), ("Injury", ""),
                   ("Practice", ""), ("Game status", "c"), ("Source", "")], rows)
    page("injuries.html", "Injuries &amp; depth chart deficiencies", body,
         "The official Week 10 practice report, plus every depth-chart replacement an official article confirms — and nothing else.")


# -------------------------------------------------------------- own lines
def build_own_lines():
    ol = J("own_lines_wk10.json")
    rows = [[(e(L["game"]), ""), (e(L["kickoff_local"])[:16].replace("T", " "), ""),
             (f'{L["own_home_margin"]:+.1f}', "n"),
             (blank(L["market_spread"]), "n"), (blank(L["spread_edge_pts"]), "n"),
             (f'{L["own_total"]:.1f}', "n"), (blank(L["market_total"]), "n"),
             (f'{L["model_win_prob_home"]*100:.1f}%', "n"),
             (pill("in log", "good") if L["in_forward_log"] else pill("kicked off", "neu"), "c"),
             (src(L["source"], "schedule"), "")] for L in ol["lines"]]
    body = '<div class="note"><b>These are own lines, not picks, and not claimed edges.</b> '
    body += 'The number is the frozen model\'s fitted home margin rounded to the nearest half-point. '
    body += 'Market columns are blank because <b>no official NFL odds source exists</b>; the third-party closing line was deliberately not used to manufacture an "edge".</div>'
    body += f'<div class="cards">'
    body += card("Games priced", ol["n_games"], "2026 Week 10")
    body += card("In the forward log", ol["forward_log_games"], "pre-kickoff, timestamped")
    body += card("Residual sigma", ol["sigma_margin"], "points, from the holdout")
    body += card("Disagreement filter", f'{ol["filter_points"]} pt', "before a play is published")
    body += "</div>"
    body += table([("Game", ""), ("Kickoff", ""), ("Own line (home)", "n"), ("Market", "n"), ("Edge", "n"),
                   ("Own total", "n"), ("Market total", "n"), ("P(home)", "n"), ("Log", "c"), ("Source", "")], rows)
    body += f'<h2>Recalibration applied</h2><p class="lede">{e(ol["recalibration"]["why"])}.</p>'
    body += table([("Component", ""), ("Intercept", "n"), ("Slope", "n"), ("Fitted on", ""), ("Source", "")], [
        [("Margin", ""), (ol["recalibration"]["margin"]["intercept"], "n"), (ol["recalibration"]["margin"]["slope"], "n"),
         (ol["recalibration"]["fitted_on"], ""), (src(REPO + "/data/model_config.json", "repo", True), "")],
        [("Total", ""), (ol["recalibration"]["total"]["intercept"], "n"), (ol["recalibration"]["total"]["slope"], "n"),
         (ol["recalibration"]["fitted_on"], ""), (src(REPO + "/data/model_config.json", "repo", True), "")]])
    body += ('<div class="note bad"><b>Gate G7 fails.</b> An own line is only tradeable against a real price. '
             'Until an archived odds source exists (S14), these numbers are a forecast, not a bet.</div>')
    page("own-lines.html", "Own lines — 2026 Week 10", body,
         "Every Week 10 game priced by the frozen model before kickoff.")


# ------------------------------------------------------------- leaderboard
def build_leaderboard():
    bt = J("backtest.json"); fc = J("forecast_leaderboard.json")
    body = '<div class="note"><b>Two boards, deliberately.</b> The betting board is empty because nothing passed. '
    body += 'The forecast board pays, because forecast skill can be measured without a price.</div>'
    body += "<h2>Board 1 — Betting ROI (pool: 1000 points)</h2>"
    rows = []
    for t in bt["holdout"]:
        rows.append([(t["id"], ""), (f'{t["n"]:,}', "n"), (f'{t["roi"]*100:+.2f}%', "n"),
                     (f'[{t["roi_ci95"][0]*100:+.2f}%, {t["roi_ci95"][1]*100:+.2f}%]', "n"),
                     (f'{t["perm_p"]:.4f}', "n"), (f'{t["bh_q"]:.4f}', "n"),
                     (f'{t["seasons"]["positive_seasons"]}/{t["seasons"]["seasons"]}', "n"),
                     (f'{t["seasons"]["max_season_profit_share"]*100:.0f}%', "n"),
                     (pill(t["tier"], {"Bronze": "warn", "Rejected": "bad", "Silver": "good"}.get(t["tier"], "neu")), "c"),
                     (t["reward_points"], "n"), (src(REPO + "/data/backtest.json", "repo", True), "")])
    body += table([("Strategy", ""), ("Bets", "n"), ("ROI", "n"), ("95% CI (week-clustered)", "n"),
                   ("Perm p", "n"), ("FDR q", "n"), ("+ seasons", "n"), ("Max 1-season share", "n"),
                   ("Tier", "c"), ("Points", "n"), ("Source", "")], rows)
    body += ('<p class="lede"><b>S5 and S6</b> are placebo controls with no model input. '
             '<b>S4</b> is a two-leg parlay of S1 selections from different games in the same week.</p>')
    body += '<div class="note bad"><b>0 of 1000 points awarded.</b> No strategy reached Gold. The pool rolls over to the next assessment.</div>'

    body += "<h2>Board 2 — Forecast skill (pool: 600 points, awarded now)</h2>"
    rows = [[(f'{i+1}', "n"), (e(b["forecaster"]), ""), (b["n"], "n"), (b["margin_mae"], "n"),
             (b["margin_rmse"], "n"), (b["total_mae"], "n"),
             (b["ats_accuracy"] if b["ats_accuracy"] is not None else '<span class="blank">n/a</span>', "n"),
             (b["brier"], "n"), (b["reward_points"], "n"), (e(b["note"]), ""),
             (src(REPO + "/data/forecast_leaderboard.json", "repo", True), "")] for i, b in enumerate(fc["board"])]
    body += table([("Rank", "n"), ("Forecaster", ""), ("Games", "n"), ("Margin MAE", "n"), ("RMSE", "n"),
                   ("Total MAE", "n"), ("ATS acc.", "n"), ("Brier", "n"), ("Points", "n"), ("Note", ""), ("Source", "")], rows)
    body += f'<div class="note">{e(fc["allocation"])}</div>'
    body += "<h2>Tier definitions</h2>"
    gates = J("gates.json")
    body += table([("Tier", ""), ("Requirement", ""), ("Source", "")],
                  [[(k, ""), (v, ""), (src(REPO + "/data/gates.json", "repo", True), "")] for k, v in gates["tiers"].items()])
    page("leaderboard.html", "Leaderboard", body,
         "Five registered betting strategies and five forecasters, scored once on the 2018-2025 holdout.")


# -------------------------------------------------------------- validation
def build_validation():
    bt = J("backtest.json"); gates = J("gates.json"); cfg = J("model_config.json")
    body = '<div class="note"><b>Gates were committed before the backtest ran.</b> '
    body += f'Pre-registered {e(gates["pre_registered_utc"])}; thresholds are project choices, not official NFL values.</div>'
    body += "<h2>The eight gates</h2>"
    body += table([("ID", ""), ("Gate", ""), ("Rule", ""), ("Source", "")],
                  [[(g["id"], ""), (g["name"], ""), (g["rule"], ""),
                    (src(REPO + "/data/gates.json", "repo", True), "")] for g in gates["gates"]])
    body += "<h2>Gate results, strategy by strategy</h2>"
    rows = []
    for t in bt["holdout"]:
        def mark(b):
            return pill("pass", "good") if b else pill("fail", "bad")
        rows.append([(t["id"], ""), (mark(True), "c"), (mark(t["G2_min_sample"]), "c"),
                     (mark(t["G3_positive_roi"]), "c"), (mark(t["G4_luck_removed"]), "c"),
                     (mark(t["G5_robust"]), "c"), (mark(bt["G6_lookahead"]["pass"]), "c"),
                     (mark(t["G7_pricing_archived"]), "c"), (pill("n/a", "neu"), "c"), (t["tier"], ""),
                     (src(REPO + "/data/backtest.json", "repo", True), "")])
    body += table([("Strategy", ""), ("G1", "c"), ("G2", "c"), ("G3", "c"), ("G4", "c"), ("G5", "c"),
                   ("G6", "c"), ("G7", "c"), ("G8", "c"), ("Tier", ""), ("Source", "")], rows)
    body += "<h2>Luck-removal evidence</h2>"
    body += table([("Method", ""), ("Result", ""), ("What it rules out", ""), ("Source", "")], [
        [("Chronological split", ""), (f'knobs fitted on {cfg["dev_max_season"]} and earlier, holdout 2018-2025 scored once', ""),
         ("hindsight tuning", ""), (src(REPO + "/scripts/03_backtest.py", "code", True), "")],
        [("Week-clustered bootstrap", ""), ("5,000 resamples by week, not by bet", ""),
         ("pseudo-replication across correlated games", ""), (src(REPO + "/scripts/03_backtest.py", "code", True), "")],
        [("Matched-random permutation", ""), ("5,000 draws, same weeks and same bet count, random side", ""),
         ("that any 50/50 process could not produce the result", ""), (src(REPO + "/scripts/03_backtest.py", "code", True), "")],
        [("Benjamini-Hochberg FDR", ""), (f'applied across the {len(bt["holdout"])} tested strategies', ""),
         ("multiple-testing inflation", ""), (src(REPO + "/scripts/03_backtest.py", "code", True), "")],
        [("Placebo calibration", ""), (f'{bt["placebo"]["draws"]} random strategies: mean ROI {bt["placebo"]["mean_roi"]*100:+.2f}%, best {bt["placebo"]["best_roi"]*100:+.2f}%, {bt["placebo"]["share_positive"]*100:.0f}% positive', ""),
         ("optimism in the search itself", ""), (src(REPO + "/data/backtest.json", "repo", True), "")],
        [("Look-ahead perturbation", ""), (f'changing {bt["G6_lookahead"]["games_changed_after_cutoff"]} later results changed {bt["G6_lookahead"]["predictions_before_cutoff_that_changed"]} earlier predictions', ""),
         ("future information leaking backwards", ""), (src(REPO + "/data/backtest.json", "repo", True), "")],
        [("Season concentration", ""), ("max-single-season profit share reported next to every ROI", ""),
         ("one lucky season wearing a good average", ""), (src(REPO + "/scripts/03_backtest.py", "code", True), "")],
    ])
    body += "<h2>Power: how many bets to prove a 55% edge</h2>"
    body += ('<p class="lede">Two-sided 5% test at 80% power against the 52.38% break-even at -110 '
             'requires roughly <b>620 settled bets</b>. The holdout produced 948 S1 bets but concentrated in one season, '
             'so the effective evidence is far smaller than the raw count suggests.</p>')
    body += '<div class="note warn"><b>G8 cannot pass in one session.</b> Forward replication needs at least a full season of timestamped pre-kickoff predictions. ' + e(bt["G8_forward_replication"]["requirement"]) + '.</div>'
    page("validation.html", "Validation gates", body,
         "Eight pre-registered gates, and the statistical machinery used to remove luck rather than hide it.")


# ------------------------------------------------------------ correlations
def build_correlations():
    co = J("correlations.json")
    body = '<div class="note"><b>Computed, not published.</b> No official source publishes these coefficients. '
    body += 'Every value below is reproduced by <code>scripts/04_correlations.py</code> from archived final scores.</div>'
    body += "<h2>Bivariate correlations</h2>"
    rows = [[(c["id"], ""), (e(c["label"]), ""), (f'{c["r"]:.4f}', "n"),
             (f'[{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}]', "n"), (f'{c["n"]:,}', "n"),
             (f'{c["p"]:.2e}', "n"), (f'{c["bh_q"]:.2e}', "n"),
             (pill("survives FDR", "good") if c["survives_fdr"] else pill("not significant", "neu"), "c"),
             (e(c["note"]), ""),
             (src(REPO + "/scripts/04_correlations.py", "computed", True), "")] for c in co["correlations"]]
    body += table([("ID", ""), ("Pair", ""), ("r", "n"), ("95% CI (Fisher)", "n"), ("n", "n"),
                   ("p", "n"), ("FDR q", "n"), ("Verdict", "c"), ("Note", ""), ("Source", "")], rows)

    body += "<h2>Dependence tests (why parlay legs do or do not multiply)</h2>"
    rows = []
    for d in co["dependence_tests"]:
        val = d.get("phi", d.get("icc", ""))
        ci = d.get("phi_ci95_bootstrap") or d.get("phi_ci95") or ""
        rows.append([(d["id"], ""), (e(d["label"]), ""),
                     (f'{val:.4f}' if isinstance(val, float) else blank(val), "n"),
                     (f'[{ci[0]:.4f}, {ci[1]:.4f}]' if isinstance(ci, list) else blank(ci), "n"),
                     (d.get("n") or d.get("n_weeks") or d.get("n_pairs") or "", "n"),
                     (pill(d["verdict"], "good" if "not rejected" in d["verdict"] or "near-independent" in d["verdict"] or "no overdispersion" in d["verdict"] else "warn"), "c"),
                     (src(REPO + "/scripts/04_correlations.py", "computed", True), "")])
    body += table([("ID", ""), ("Test", ""), ("Statistic", "n"), ("95% CI", "n"), ("n", "n"), ("Verdict", "c"), ("Source", "")], rows)

    body += "<h2>Key numbers</h2>"
    kn = co["key_numbers"]
    body += table([("Margin", "n"), ("Share of games", "n"), ("Source", "")],
                  [[(k, "n"), (f'{kn[k]*100:.2f}%', "n"),
                    (src(REPO + "/data/correlations.json", "computed", True), "")] for k in sorted(kn, key=lambda x: int(x) if x.isdigit() else 99) if k.isdigit()])
    body += f'<p class="lede">{e(kn["note"])} Computed over {kn["n"]:,} games.</p>'

    body += "<h2>Home-field advantage by season</h2>"
    rows = [[(s, "n"), (v["mean_home_margin"], "n"), (f'{v["home_win_rate"]*100:.1f}%', "n"), (v["n"], "n"),
             (src(REPO + "/data/correlations.json", "computed", True), "")]
            for s, v in co["hfa_by_season"].items()]
    body += table([("Season", "n"), ("Mean home margin", "n"), ("Home win rate", "n"), ("Games", "n"), ("Source", "")], rows)
    lc = co["luck_calibration"]
    body += ('<h2>Luck calibration</h2>'
             + table([("Check", ""), ("Value", "n"), ("Expected if the market were uninformative", "n"), ("Source", "")], [
                 [("ATS push rate", ""), (f'{lc["ats_push_rate"]*100:.2f}%', "n"), ("~2-3% (integer lines)", "n"),
                  (src(REPO + "/data/correlations.json", "computed", True), "")],
                 [("Home cover rate", ""), (f'{lc["home_cover_rate"]*100:.2f}%', "n"), ("50%", "n"),
                  (src(REPO + "/data/correlations.json", "computed", True), "")],
                 [("Over rate", ""), (f'{lc["over_rate"]*100:.2f}%', "n"), ("50%", "n"),
                  (src(REPO + "/data/correlations.json", "computed", True), "")]]))
    body += f'<div class="note">{e(lc["note"])}</div>'
    page("correlations.html", "Correlation values", body,
         "Every coefficient with a confidence interval and an FDR-corrected verdict.")


# ------------------------------------------------------------------ props
def build_props():
    pr = J("props.json")
    c = pr["combo"]
    body = '<div class="note bad"><b>Blocked, and labelled as such.</b> There is no 2026 player feed and no archived prop price. '
    body += 'What follows is a correlation study, not a betting result. Gate G7 fails by construction.</div>'
    body += '<div class="cards">'
    body += card("Team-games", f'{pr["n_team_games"]:,}', f'seasons {pr["seasons"]}')
    body += card("Combo lift", f'{c["lift"]:.2f}×', "joint vs independent")
    body += card("phi", f'{c["phi"]:.3f}', f'95% CI {c["phi_ci95"]}')
    body += card("Yard-level r", f'{pr["yard_level_correlation"]["r"]:.3f}', "QB yards vs WR1 yards")
    body += "</div>"
    body += "<h2>The combo</h2>"
    body += table([("Quantity", ""), ("Value", "n"), ("If the legs were independent", "n"), ("Source", "")], [
        [(c["leg_a"], ""), (c["p_a"], "n"), ("—", "n"), (src(REPO + "/data/props.json", "repo", True), "")],
        [(c["leg_b"], ""), (c["p_b"], "n"), ("—", "n"), (src(REPO + "/data/props.json", "repo", True), "")],
        [("Both legs win", ""), (c["p_both"], "n"), (c["independence_expected"], "n"),
         (src(REPO + "/data/props.json", "repo", True), "")],
    ])
    body += f'<div class="note warn"><b>Reading.</b> {e(c["verdict"])} The 95% CI on phi is {c["phi_ci95"]}, which excludes zero. '
    body += 'That is a real dependence in the data. Whether it survives the sportsbook\'s own repricing is unknown and unknowable without archived SGP prices.</div>'
    body += "<h2>Why this cannot become a strategy yet</h2>"
    body += table([("Gate", ""), ("Result", "c"), ("Detail", ""), ("Source", "")], [
        [("G2 minimum sample", ""), (pill("fail", "bad"), "c"), (e(pr["gates"]["G2_min_sample"]["detail"]), ""),
         (src(REPO + "/data/gates.json", "repo", True), "")],
        [("G7 pricing realism", ""), (pill("fail", "bad"), "c"), (e(pr["gates"]["G7_pricing"]["detail"]), ""),
         (src(REPO + "/data/gates.json", "repo", True), "")],
        [("Status", ""), (pill("blocked", "bad"), "c"), (e(pr["gates"]["status"]), ""),
         (src(REPO + "/data/props.json", "repo", True), "")],
    ])
    body += "<h2>What would unblock it</h2><ul>"
    body += "".join(f"<li>{e(x)}</li>" for x in pr["what_would_unblock_it"])
    body += "</ul>"
    body += f'<p class="src">Source archive: <a href="{e("https://github.com/fantasydatapros/LearnPythonWithFantasyFootball")}">fantasydatapros/LearnPythonWithFantasyFootball</a> (third-party archive of official NFL box scores).</p>'
    page("props.html", "Player-prop combos", body,
         "The strongest measured signal in the repository — and the one furthest from being priceable.")


# ------------------------------------------------------------------- data
def build_data():
    res = J("results_2026.json")
    body = '<div class="note"><b>Official-source-only.</b> Every 2026 score on this page carries the nfl.com URL for that game. '
    body += 'Nothing is filled in. A cell that could not be confirmed is blank and appears on the Flagged page.</div>'
    body += "<h2>Reconciliation checks</h2>"
    body += table([("Check", ""), ("Result", "c"), ("Detail", ""), ("Source", "")],
                  [[(c["check"], ""), (pill("pass", "good") if c["pass"] else pill("fail", "bad"), "c"), (c["detail"], ""),
                    (src("https://www.nfl.com/standings/league/2026/REG", "nfl.com", True), "")]
                   for c in res["checks"]])
    body += "<h2>Team records, recomputed from the game log and matched to nfl.com</h2>"
    rows = [[(t, ""), (v["w"], "n"), (v["l"], "n"), (v["t"], "n"), (v["pf"], "n"), (v["pa"], "n"),
             (f'{v["w"]/(v["w"]+v["l"]+v["t"]):.3f}', "n"),
             (src("https://www.nfl.com/standings/league/2026/REG", "nfl.com"), "")] for t, v in res["teams"].items()]
    body += table([("Team", ""), ("W", "n"), ("L", "n"), ("T", "n"), ("PF", "n"), ("PA", "n"), ("PCT", "n"), ("Source", "")], rows)
    body += f'<h2>Game log ({len(res["games"])} games, Weeks 1-9)</h2>'
    rows = [[(g["week"], "n"), (g["date"], ""), (f'{g["away"]} {g["away_pts"]}', ""), (f'{g["home"]} {g["home_pts"]}', ""),
             (e(g["origin"]), ""), (src(g["source"], "nfl.com"), "")] for g in res["games"]]
    body += table([("Wk", "n"), ("Date", ""), ("Away", ""), ("Home", ""), ("Provenance", ""), ("Source", "")], rows)
    body += "<h2>Sources used for this page</h2>"
    body += table([("ID", ""), ("What", ""), ("Link", "")],
                  [[(s["id"], ""), (s["what"], ""), (src(s["url"], "official"), "")] for s in res["sources"]])
    page("data.html", "Data &amp; provenance", body,
         "All 136 verified 2026 games and the 32 recomputed team records, each with its own official link.")


# ------------------------------------------------------------ repo review
def build_repo_review():
    checks = [
        ("2026 game log completeness", "nfl-lab/data/games_2026.csv", "flag", "fail",
         "120 games recorded for Weeks 1-8; the official count is 121. CHI@SEA (Week 8) is missing.",
         "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"),
        ("2026 game log arithmetic", "nfl-lab/data/games_2026.csv", "check", "pass",
         "Every recorded row's scores sum consistently and slugs are unique.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/games_2026.csv"),
        ("Spread sign convention", "nfl-quant/data/predictions.csv", "flag", "warn",
         "spread_line is the HOME team's favoured-by margin (positive = home favourite), not the conventional home line. "
         "Using the conventional sign produces impossible backtest ROIs. Verified empirically: games with spread_line >= +7 "
         "have an 80.5% home win rate; <= -7 gives 23.1%.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/predictions.csv"),
        ("Stale 2026 snapshot", "nfl-lab/, nfl-quant/", "flag", "warn",
         "Both namespaces stop at Week 8 results (2026-11-02). They are six days stale against the official standings.",
         "https://www.nfl.com/standings/league/2026/REG"),
        ("Betting lines have no official source", "nfl-quant/data/provenance.json", "flag", "fail",
         "Every market value is third-party. No official NFL odds source exists, so no market cell can ever carry an official link.",
         "https://github.com/nflverse/nfldata"),
        ("Duplicate NFL dashboards", "nfl/, nfl-research/, nfl-lab/, nfl-quant/, nfl-decision/", "flag", "warn",
         "Five independently built NFL sites exist. Only nfl-quant and nfl-decision carry measured results.",
         "https://github.com/sassnarep3-star/Own4"),
        ("Depth charts do not exist officially", "nfl-task brief", "flag", "fail",
         "https://www.nfl.com/depth-charts/ returns 404. Any 1st/2nd/3rd-string label would be invented.",
         "https://www.nfl.com/depth-charts/"),
        ("Injury data is current-week only", "nfl-decision/data/injuries_wk10.py", "flag", "warn",
         "No official archive of past practice reports exists, so injuries cannot be back-tested.",
         "https://www.nfl.com/injuries/"),
        ("README merge-conflict markers", "README.md", "status", "pass",
         "A prior session recorded committed conflict markers; the current README has none. Checked, not assumed.",
         "https://github.com/sassnarep3-star/Own4/blob/main/README.md"),
        ("COORDINATION.md board", "COORDINATION.md", "status", "pass",
         "Board exists, all prior claims are done or needs-review and are more than 60 minutes old, so no live claim was displaced.",
         "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
        ("Pages deploy configuration", "GitHub Pages", "flag", "warn",
         "Pages serves the legacy branch build of main. Prior sessions recorded repeated environmental build failures.",
         "https://api.github.com/repos/sassnarep3-star/Own4/pages"),
        ("Possessive 's' in run text", "nfl-quant/EXECUTIVE_SUMMARY.md", "flag", "warn",
         "A prior summary states 15/15 data-integrity and 13/13 score spot-checks pass; this session did not re-run those "
         "checks against a live source and does not endorse them as verified.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/EXECUTIVE_SUMMARY.md"),
    ]
    body = '<div class="note"><b>Line-by-line review of every NFL namespace.</b> Each row states what was checked, '
    body += 'the verdict, and a link. Items marked <b>flag</b> appear again on the Flagged page.</div>'
    body += table([("Area", ""), ("Path", ""), ("Type", "c"), ("Verdict", "c"), ("Finding", ""), ("Evidence", "")],
                  [[(a, ""), (f'<code>{e(p)}</code>', ""), (pill(t, "neu"), "c"),
                    (pill("pass", "good") if v == "pass" else (pill("warning", "warn") if v == "warn" else pill("defect", "bad")), "c"),
                    (e(f), ""), (src(u, "link"), "")] for a, p, t, v, f, u in checks])
    body += "<h2>What this review did not do</h2>"
    body += ('<p class="lede">It did not re-run the peer namespaces\' own verifiers, and it did not re-fetch every '
             'historical page they cite. Those are their records, not this session\'s verification. '
             'What this session did verify is on the <a href="data.html">Data</a> page and every claim there has a live official link.</p>')
    page("repo-review.html", "Repository review", body,
         "Every NFL namespace checked, with the defect that mattered most: one missing game and one inverted spread sign.")


# ---------------------------------------------------------------- flagged
def build_flagged():
    flags = [
        ("F-01", "blocking a claim", "No official NFL odds or price archive exists",
         "Every ROI on this site is priced at an assumed -110. Gate G7 therefore fails for all five strategies and 0 of 1000 betting points are awarded. This is not fixable with code.",
         "https://www.nfl.com/games"),
        ("F-02", "blocking a claim", "No official depth chart exists",
         "nfl.com/depth-charts/ returns HTTP 404 (checked 2026-11-12). 2nd/3rd/4th-string labels requested in the brief cannot be sourced officially.",
         "https://www.nfl.com/depth-charts/"),
        ("F-03", "defect found", "Missing Week 8 game in the repo's 2026 log",
         "nfl-lab/data/games_2026.csv holds 120 games for Weeks 1-8; the official count is 121. CHI 34 - SEA 17 on 2026-11-02 was absent. Corrected in nfl-decision/data/results_2026.json only; the peer file was not edited, per the coordination rules.",
         "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"),
        ("F-04", "irregularity", "Inverted spread sign in the archived line column",
         "spread_line is the home team's favoured-by margin, so the conventional home line is -spread_line. A naive reading yields 60% home-cover rates and impossible ROIs above +50%. Documented and corrected here.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/predictions.csv"),
        ("F-05", "unverified", "Injury cells left blank",
         "The official report often shows a practice status with a blank injury and blank game status. These are published blank, not inferred.",
         "https://www.nfl.com/injuries/"),
        ("F-06", "unverified", "LAC and BAL show 'No Injuries Reported'",
         "Recorded verbatim from the official page. This is not proof that no player is injured; it is what the official page displays.",
         "https://www.nfl.com/injuries/"),
        ("F-07", "unverified", "2026 player-level data does not exist in this repository",
         "All prop analysis uses 2021-2022 archived data with proxy thresholds, never sportsbook prices.",
         "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball"),
        ("F-08", "irregularity", "Model is recalibrated in-sample for the Week 10 lines",
         "The margin and total recalibration coefficients were fitted on all 7,087 archived games, which includes the games the model was scored on. Disclosed on the Own lines page. The holdout leaderboard numbers are NOT recalibrated.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/own_lines_wk10.json"),
        ("F-09", "irregularity", "-110 is an assumption, not a price",
         "Spread and total bets are settled at the same assumed price on both sides. Real prices vary by book, game and side.",
         "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json"),
        ("F-10", "unverified", "Peer namespace claims were not re-verified",
         "nfl/, nfl-research/, nfl-lab/ and nfl-quant/ carry their own verification records. This session did not re-run them and does not endorse their numbers as verified.",
         "https://github.com/sassnarep3-star/Own4"),
        ("F-11", "irregularity", "Eight competing NFL dashboards are live",
         "nfl/, nfl-research/, nfl-lab/, nfl-quant/, nfl-decisions/, nfl-hub/, nfl-audit/ and nfl-decision/ all exist. S04 proposes a fix. Peer session e2601583 independently found no official market lines and no official depth chart, matching F-01 and F-02.",
         "https://github.com/sassnarep3-star/Own4"),
        ("F-12", "unverified", "nfl.com odds toggle renders no values",
         "The official games page presents an odds interface but the server HTML contains no price values, so nothing could be transcribed even in principle.",
         "https://www.nfl.com/games"),
        ("F-13", "irregularity", "Week 10 Thursday game excluded from the forward log",
         "WAS@NYG kicked off on 2026-11-12 before this work was recorded, so it is priced but marked 'kicked off' and excluded from the forward record.",
         "https://www.nfl.com/schedules/2026/by-week/week-10"),
        ("F-14", "blocked", "No historical injury archive",
         "nfl.com/injuries/ serves the current week only. Injury effects are therefore not measurable, and none are claimed.",
         "https://www.nfl.com/injuries/"),
        ("F-15", "unverified", "Playoff and tiebreaker scenarios",
         "This site publishes no playoff odds, seeding projections or tiebreaker outcomes. None were computed.",
         "https://www.nfl.com/standings/tiebreakingprocedures"),
    ]
    body = '<div class="note warn"><b>These items do not block publication.</b> They are published so you can review them. '
    body += 'Anything that could not be confirmed against an official source is marked <b>unverified</b> and left blank everywhere else on the site.</div>'
    body += table([("ID", ""), ("Severity", "c"), ("Item", ""), ("Detail", ""), ("Source", "")],
                  [[('<a href="#' + i + '">' + i + '</a>', ""), (pill(sv, {"blocking a claim": "bad", "defect found": "bad", "irregularity": "warn", "unverified": "warn", "blocked": "bad"}.get(sv, "neu")), "c"),
                    (e(it), ""), (e(d), ""), (src(u, "link"), "")] for i, sv, it, d, u in flags],
                  row_ids=[f[0] for f in flags])
    page("flagged.html", "Flagged for review", body,
         "Every unverified value, every irregularity found, and every claim this project refuses to make.")


# ---------------------------------------------------------------- sources
def build_sources():
    official = [
        ("Official 2026 league standings", "https://www.nfl.com/standings/league/2026/REG", "All 32 team records; 160/160 cells reconciled"),
        ("Official 2026 Week 9 scores", "https://www.nfl.com/scores/2026/REG9", "15 game finals transcribed"),
        ("Official 2026 Week 8 game centre", "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8", "The missing game, CHI 34 - SEA 17"),
        ("Official 2026 Week 10 schedule", "https://www.nfl.com/schedules/2026/by-week/week-10", "14 games, kickoff times, venues"),
        ("Official Week 10 injury report", "https://www.nfl.com/injuries/", "28 clubs, practice and game status"),
        ("Official Week 10 injury report article", "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season", "Out / Questionable confirmations"),
        ("Official injury-report policy (Competition Committee)", "https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693", "Designation definitions"),
        ("Official news roundup, 2026-11-11", "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11", "Depth-chart and injury detail"),
        ("Seahawks QB change", "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again", "Darnold out, Lock starts"),
        ("Dolphins QB change", "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start", "Willis to IR, McCord starts"),
        ("Ravens QB change", "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season", "Jackson out 6-9 weeks"),
        ("NFL depth charts (not available)", "https://www.nfl.com/depth-charts/", "HTTP 404, checked 2026-11-12"),
        ("NFL player stats index", "https://www.nfl.com/stats/", "Referenced, not scraped"),
        ("Tiebreaking procedures", "https://www.nfl.com/standings/tiebreakingprocedures", "Referenced only; no scenarios computed"),
        ("NCPG helpline", "https://www.ncpgambling.org/help-treatment", "Cited site-wide"),
        ("GitHub Pages documentation", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages", "Deployment behaviour"),
        ("FanDuel parlay guide", "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet", "Parlay payout mechanics (third-party, disclosed)"),
    ]
    third = [
        ("nflverse/nfldata", "https://github.com/nflverse/nfldata", "Archived closing lines and schedules, 1999-2026. THIRD-PARTY."),
        ("fantasydatapros archive", "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball", "Per-player 2021-2022 box scores. THIRD-PARTY."),
    ]
    body = '<div class="note"><b>Official sources are linked at point of use</b> on every page. This page is the index.</div>'
    body += "<h2>Official NFL sources</h2>"
    body += table([("What", ""), ("Used for", ""), ("Link", "")],
                  [[(w, ""), (u, ""), (src(l, "official"), "")] for w, l, u in official])
    body += "<h2>Third-party sources (disclosed, never presented as official)</h2>"
    body += table([("Repository", ""), ("Used for", ""), ("Link", "")],
                  [[(w, ""), (u, ""), (src(l, "repo"), "")] for w, l, u in third])
    body += "<h2>Repository files produced by this session</h2>"
    files = ["scripts/01_results.py", "scripts/02_model.py", "scripts/03_backtest.py",
             "scripts/04_correlations.py", "scripts/05_props.py", "scripts/06_own_lines.py",
             "scripts/07_forecast.py", "scripts/08_build_site.py", "scripts/09_verify.py",
             "data/gates.json", "data/results_2026.json", "data/walkforward.csv",
             "data/backtest.json", "data/correlations.json", "data/props.json",
             "data/own_lines_wk10.json", "data/forecast_leaderboard.json", "data/model_config.json",
             "data/questions.py", "data/suggestions.py", "data/injuries_wk10.py"]
    body += table([("File", ""), ("Link", "")],
                  [[(f'<code>{e(f)}</code>', ""), (src(REPO + "/" + f, "repo"), "")] for f in files])
    page("sources.html", "Sources", body,
         "Every source used, separated into official and disclosed third-party.")


def main():
    build_index(); build_exec(); build_questions(); build_suggestions()
    build_injuries(); build_own_lines(); build_leaderboard(); build_validation()
    build_correlations(); build_props(); build_data(); build_repo_review()
    build_flagged(); build_sources()
    print(f"built {len(NAV)} pages in {ROOT}")


if __name__ == "__main__":
    main()

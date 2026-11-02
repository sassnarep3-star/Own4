#!/usr/bin/env python3
"""Static-site generator.  Reads data/*.csv + model/results.json, writes index.html and pages/*.html.
Run from anywhere:  python3 site_src/build_site.py"""
import csv, html, json, os, datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "lab")   # published at /Own4/lab/ (root index/pages/docs belong to other sessions' framework site)
REPO = "https://github.com/sassnarep3-star/Own4"
def rd(n): return list(csv.DictReader(open(os.path.join(D, n), newline="")))
E = html.escape
res = json.load(open(os.path.join(ROOT, "model", "results.json")))
gates = json.load(open(os.path.join(ROOT, "strategies", "gates.json")))
ver = json.load(open(os.path.join(D, "verification_report.json")))
teams = {t["abbr"]: t for t in rd("teams.csv")}
games = rd("games_2026-27.csv"); lines = rd("own_lines_2026-11-02.csv"); flags = rd("flags.csv"); lb = rd("leaderboard.csv")
corr = rd("correlations.csv"); parlay = rd("parlay_examples_2026-11-02.csv")
BUILT = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
def a(url, label="source"): return f'<a href="{E(url)}" target="_blank" rel="noopener">{E(label)}</a>'
def tname(x): return E(teams[x]["team"]) if x in teams else E(x)
def f(x, d=2):
    try: return f"{float(x):.{d}f}"
    except Exception: return E(str(x))
def tag(txt, kind=""): return f'<span class="tag {kind}">{E(txt)}</span>'
def table(headers, rows, tid=None, filt=False, wrapcols=()):
    """headers: list of str; rows: list of lists of (html) strings; numeric-looking cells right aligned."""
    h = "".join(f'<th class="{"wrap" if i in wrapcols else ""}">{E(x)}</th>' for i, x in enumerate(headers))
    def cell(i, c):
        s = str(c); plain = s.replace("-", "", 1).replace(".", "", 1).replace("+", "", 1)
        cls = "wrap" if i in wrapcols else ("n" if plain.isdigit() else "")
        return f'<td class="{cls}">{s}</td>'
    body = "".join("<tr>" + "".join(cell(i, c) for i, c in enumerate(r)) + "</tr>" for r in rows)
    box = f'<input class="filter" placeholder="Filter rows…" data-for="{tid}">' if filt else ""
    return f'{box}<div class="tw"><table id="{tid or ""}"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'
NAV = [("index.html", "Dashboard"), ("pages/executive-summary.html", "Executive summary"), ("pages/leaderboard.html", "Leaderboard"), ("pages/own-lines.html", "Own lines (Nov 2)"),
       ("pages/games.html", "Games"), ("pages/standings.html", "Standings"), ("pages/team-stats.html", "Team stats"), ("pages/correlations.html", "Correlations"),
       ("pages/repo-review.html", "Repo review"), ("pages/flagged.html", "Flagged for review"), ("pages/methodology.html", "Methodology & sources")]
JS = """<script>
document.querySelectorAll('input.filter').forEach(i=>i.addEventListener('input',()=>{const q=i.value.toLowerCase();document.querySelectorAll('#'+i.dataset.for+' tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')}));
document.querySelectorAll('th').forEach(th=>th.addEventListener('click',()=>{const t=th.closest('table'),b=t.tBodies[0],i=[...th.parentNode.children].indexOf(th),d=th.dataset.d=th.dataset.d=='1'?-1:1;
[...b.rows].sort((x,y)=>{const p=x.cells[i].textContent.trim(),q=y.cells[i].textContent.trim(),m=parseFloat(p),n=parseFloat(q);return d*((isNaN(m)||isNaN(n))?p.localeCompare(q):m-n)}).forEach(r=>b.appendChild(r))}));
</script>"""
def page(path, title, body, lead=""):
    depth = path.count("/"); pre = "../" * depth
    nav = "".join(f'<a href="{pre}{h}" class="{"on" if h == path else ""}">{E(t)}</a>' for h, t in NAV) + f'<a href="{pre}../index.html">Research framework site ↗</a>'
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Own4</title><link rel="stylesheet" href="{pre}assets/style.css"></head><body>
<header class="top"><a class="brand" href="{pre}index.html">Own4 · NBA own-line data lab</a><nav>{nav}</nav></header>
<main><h1>{E(title)}</h1><p class="lead">{lead}</p>{body}</main>
<footer>Built {BUILT} from <a href="{REPO}">{REPO.split('//')[1]}</a>. Source data: nba.com official pages (links in every table row). Research output only — virtual rewards, not betting advice, no real-money stakes.</footer>{JS}</body></html>"""
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(out)
SCORE = "https://www.nba.com/games?date=2026-11-01"
nflag = len(flags); nval = sum(1 for x in lb if x["tier"] in ("Forecast-validated",))
m = res["margin"]; tt = res["total"]; ts = res["tests"]; pr = res["prob"]
npass = ver["passed"]; ntot = ver["total"]
def ci(t, key="ci95"): return f"[{t[key][0]:+.2f}, {t[key][1]:+.2f}]"
# ------------------------------------------------------------ dashboard
cards = [("Games in sample", res["n_games"], "official finals Oct 20 – Nov 1", "pages/games.html"),
         ("Data checks passed", f"{npass}/{ntot}", "scripts/verify_data.py", "pages/methodology.html"),
         ("Validated strategies", nval, "0 of 6 testable; 3 blocked (no data)", "pages/leaderboard.html"),
         ("Nov 2 own lines", len(lines), "committed before tip-off", "pages/own-lines.html"),
         ("Flagged items", nflag, "none block the build", "pages/flagged.html"),
         ("BLEND-41 MAE", f"{m['BLEND-41']['MAE']:.1f}", f"vs {m['BASE-HCA']['MAE']:.1f} home-court-only", "pages/leaderboard.html")]
body = '<div class="cards">' + "".join(f'<div class="card"><a href="{h}"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></a></div>' for k, v, s, h in cards) + "</div>"
body += '<div class="note"><b>Headline.</b> The model beats a home-court-only baseline on average (margin MAE %.2f vs %.2f points) but with 92 games the difference is <b>not statistically distinguishable from luck</b> (95%% bootstrap CI %s). By the pre-registered gates, <b>no strategy is validated</b> and no reward is paid. See the <a href="pages/executive-summary.html">executive summary</a> and <a href="pages/flagged.html">flagged items</a>.</div>' % (m["BLEND-41"]["MAE"], m["BASE-HCA"]["MAE"], ci(ts["BLEND-41"]))
body += "<h2>Browse by category</h2><div class='nav-cards'>" + "".join(f"<a href='{h}'><b>{t}</b><span>{d}</span></a>" for h, t, d in [
 ("pages/executive-summary.html", "Executive summary", "What was built, what was found, what is not proven."),
 ("pages/leaderboard.html", "Strategy leaderboard", "Gates, scores, tiers and virtual rewards."),
 ("pages/own-lines.html", "Own lines – 2 Nov 2026", "Model spread, total, win probability, fair price per game."),
 ("pages/games.html", "All 92 games", "Every final with scoreboard and game-page links."),
 ("pages/standings.html", "Standings", "2026-27 to date and 2025-26 final."),
 ("pages/team-stats.html", "Team stats", "Points and +/- per game, three scopes."),
 ("pages/correlations.html", "Correlations", "Game-level r with CIs; same-game-parlay haircut; player level blank."),
 ("pages/repo-review.html", "Repo review", "File-by-file review with source coverage."),
 ("pages/flagged.html", "Flagged for review", "Irregularities and unverified values with links."),
 ("pages/methodology.html", "Methodology & sources", "Model, gates, luck-removal, all official sources.")]) + "</div>"
sl = [[f"{tname(l['away'])} @ {tname(l['home'])}", l["tip_et"], f"{l['home']} {float(l['own_spread_home']):+.1f}", l["own_total"], f"{float(l['p_home_win'])*100:.0f}%", a(l["game_page_url"], "game page")] for l in lines]
body += "<h2>Tonight's own lines (preview)</h2>" + table(["Game", "Tip", "Own spread (home)", "Own total", "Home win prob", "Source"], sl, "dash")
page("index.html", "Own4 dashboard", body, "Model-originated NBA lines, strategy leaderboard, correlations and a line-by-line data audit. Every row links to an official nba.com page.")
# ------------------------------------------------------------ executive summary
bl, br = ts["BLEND-41"], res["nested_k"]
hit = m["BLEND-41"]
es = f"""
<h2>What this project did</h2>
<ul><li>Transcribed every official 2026-27 final to date ({res['n_games']} games, Oct 20 – Nov 1) and the official 2025-26 and 2026-27 standings and team tables from nba.com, with a source link on every row. {npass} of {ntot} consistency checks pass (game-level sums reproduce the official team table for all 30 teams on games, wins, losses and +/-).</li>
<li>Built an <b>own-line model</b> (<code>BLEND-41</code>): team rating = current-season margin shrunk toward last season's with weight k=41 (declared before testing), plus a home-court term of {res['H']:+.2f} points from 2025-26 home games. It produces a spread, total, win probability and fair price for each game — not copied from any sportsbook.</li>
<li>Pre-registered seven validation gates and a strategy catalogue <i>before</i> running any evaluation, then scored every strategy walk-forward (a game is predicted only from strictly earlier games).</li></ul>
<h2>What was found</h2>
{table(['Finding','Number','Reading','Source'],[
 ['Margin error, BLEND-41 vs home-court-only', f"MAE {m['BLEND-41']['MAE']:.2f} vs {m['BASE-HCA']['MAE']:.2f} pts", f"gain {bl['mean_diff']:.2f} pts, 95% CI {ci(bl)}: includes 0 → not significant", a(SCORE,'92 finals')],
 ['Same, Bonferroni-adjusted (6 tests)', f"CI {ci(bl,'ci_family')}", 'includes 0', a(REPO+'/blob/main/data/leaderboard.csv','leaderboard.csv')],
 ['Picking straight-up winners', f"{hit['hits']}/{res['n_games']} = {hit['straight_up_hit']*100:.0f}%", f"95% Wilson interval {hit['hit_wilson95'][0]*100:.0f}–{hit['hit_wilson95'][1]*100:.0f}%; home-court-only baseline {m['BASE-HCA']['straight_up_hit']*100:.0f}%. Not a gate (hit rate is luck-prone).", a(SCORE,'92 finals')],
 ['Total (over/under) model', f"MAE {tt['BLEND-41-TOTAL']['MAE']:.2f} vs {tt['BASE-LGTOTAL']['MAE']:.2f}", f"bias +{tt['BLEND-41-TOTAL']['bias']:.1f} pts (league scoring is down vs 2025-26): no demonstrated edge", a(SCORE,'92 finals')],
 ['Win probability (56 games after warm-up)', f"Brier {pr['win']['brier_strategy']:.3f} vs {pr['win']['brier_baseline']:.3f}", f"gain {ts['BLEND-41-WIN']['mean_diff']:.3f}, 95% CI {ci(ts['BLEND-41-WIN'])}: includes 0", a(SCORE,'92 finals')],
 ['Current-season-only ratings', f"MAE {m['CURRENT-ONLY']['MAE']:.2f}", 'worse than home-court-only: small samples are noise — why shrinkage to last season matters', a(SCORE,'92 finals')],
 ['Correlation: home margin vs total', f"r = {corr[0]['r']} (n=92)", f"95% CI [{corr[0]['ci95_lo']}, {corr[0]['ci95_hi']}] → ~0", a(SCORE,'92 finals')],
 ['Correlation: home pts vs away pts', f"r = {corr[1]['r']} (n=92)", f"95% CI [{corr[1]['ci95_lo']}, {corr[1]['ci95_hi']}] → weak/uncertain", a(SCORE,'92 finals')],
],'es1',wrapcols=(2,))}
<h2>Leaderboard verdict</h2>
<p><b>No strategy is validated and no reward is paid.</b> Pre-registered requirement: ≥300 out-of-sample games (we have {res['n_games']}) and a bootstrap CI above zero (none). The best-scoring entries are <i>Provisional</i> (point estimate beats baseline; monitored, reward 0). Player-prop strategies and market-edge singles are <i>Blocked</i>: no official bulk player logs and no official odds source were available, so nothing was inferred or filled in. Parlay: the same-game correlation haircut is tiny (rho ≈ {res['own_lines_sigma']['rho_margin_total_residual']:.2f}, CI about ±0.2) and does not improve Brier score.</p>
<h2>How luck was removed</h2>
<ul><li>Walk-forward only (no look-ahead; asserted in code); parameters declared a priori; nested check tunes k on early games and tests on later ones (chosen k={br['k_chosen']}: test MAE {br['test_MAE_chosen']:.2f} vs {br['test_MAE_k41']:.2f} for k=41 — immaterial).</li>
<li>Proper scoring rules (MAE, Brier), paired bootstrap CIs with Bonferroni correction, minimum-sample gate, half-sample stability gate. ROI and win/loss records are not used because they are dominated by luck at this sample size and no official odds exist.</li>
<li>Rewards go only to strategies that clear sample-size <i>and</i> significance gates; otherwise the 1,000 virtual units stay unallocated.</li></ul>
<h2>Own lines for 2 Nov 2026</h2>
<p>Fifteen games, generated from data through Nov 1 and committed to git before the first tip-off. See <a href="own-lines.html">own lines</a>. They ignore injuries and rest (8 teams are on back-to-backs). They are model prices, not recommendations.</p>
<h2>Biggest caveats</h2>
<ul>{''.join(f"<li><b>{E(x['flag_id'])}</b> ({E(x['severity'])}): {E(x['description'][:190])}…</li>" for x in flags if x['severity']=='High')}<li>All {nflag} flagged items: <a href="flagged.html">Flagged for Review</a>.</li></ul>
<h2>What would change the verdict</h2>
<p>~210 more games (about 3 more weeks) to reach 300 out-of-sample; an official odds source to test closing-line value; official player box-score logs to evaluate prop strategies and player-level correlations.</p>"""
page("pages/executive-summary.html", "Executive summary", es, f"As of {BUILT}. Every figure is computed by <code>model/evaluate.py</code> and shown with its source.")
# ------------------------------------------------------------ leaderboard
rows = []
for x in sorted(lb, key=lambda r: -float(r["score"] or 0)):
    kind = {"Forecast-validated": "ok", "Provisional": "warn", "Rejected": "bad", "Blocked": ""}[x["tier"]]
    if x["tier"] == "Blocked":
        rows.append([x["id"], E(x["target"]), tag("Blocked"), "", "", "", "", "0", "0", E(x.get("reason", "")), a(REPO + "/blob/main/strategies/gates.json", "gates.json")]); continue
    g = " ".join(("✔" if int(x[k] or 0) > 0 else "✘") + k for k in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"))
    rows.append([E(x["id"]), E(x["target"]), tag(x["tier"], kind), f"{x['metric']}: {f(x['strategy_value'],3)} vs {f(x['baseline_value'],3)}",
                 f"{float(x['gain']):+.3f}", f"[{float(x['ci95_lo']):+.3f}, {float(x['ci95_hi']):+.3f}]", x["n_eval"], x["score"], x["reward_units"], g, a("https://www.nba.com/games?date=2026-10-20", "scoreboards") + " · " + a(REPO + "/blob/main/data/walk_forward_predictions.csv", "predictions")])
body = table(["Strategy", "Target", "Tier", "Metric: strategy vs baseline", "Gain", "95% CI of gain", "n", "Score /100", "Reward units", "Gates (✘ = failed / not testable)", "Sources"], rows, "lb", True)
body += f"""<div class="note"><b>Rules (pre-registered in commit 0b97f52 before any evaluation).</b> Gain = baseline error − strategy error (positive = better). Tiers: <b>Forecast-validated</b> needs G3 (n≥300) and G4 (Bonferroni CI lower bound &gt;0) and score ≥60; <b>Betting-validated</b> additionally needs G6 (beats an official closing price — not testable, no official odds). Pool: 1,000 <i>virtual</i> units (not money), split only among Forecast-validated strategies; currently unallocated ({res['reward_pool_allocated']:.0f} paid).</div>"""
body += "<h2>Gate definitions</h2>" + table(["Gate", "Name", "Points", "Required", "Rule", "Source"], [[g["id"], g["name"], g["points"], "yes" if g["required"] else "no", E(g["rule"]), a(REPO + "/blob/main/strategies/gates.json", "gates.json")] for g in gates["gates"]], "gates", wrapcols=(4,))
body += "<h2>Baselines (never rewarded)</h2>" + table(["Baseline", "Target", "Definition", "Result", "Source"], [
  ["BASE-HCA", "margin", "home-court only", f"MAE {m['BASE-HCA']['MAE']:.2f}, bias {m['BASE-HCA']['bias']:+.2f}", a("https://www.nba.com/games?date=2026-10-20", "scoreboards")],
  ["BASE-LGTOTAL", "total", "league-average total so far", f"MAE {tt['BASE-LGTOTAL']['MAE']:.2f}, bias {tt['BASE-LGTOTAL']['bias']:+.2f}", a("https://www.nba.com/games?date=2026-10-20", "scoreboards")],
  ["BASE-HOMEWIN", "win", f"P(home)=2025-26 home win rate {res['home_win_rate_2025_26']*100:.1f}%", f"Brier {pr['win']['brier_baseline']:.3f}", a("https://www.nba.com/standings?Season=2025-26", "2025-26 standings")],
  ["BASE-INDEP", "parlay", "product of leg probabilities", f"Brier {pr['parlay']['brier_indep']:.3f}", a("https://www.nba.com/games?date=2026-10-20", "scoreboards")]], "base", wrapcols=(2,))
body += "<h2>Sensitivity to k (exploratory, not used for ranking)</h2>" + table(["k", "Margin MAE", "Total MAE", "Source"], [[k, f"{v['margin_MAE']:.2f}", f"{v['total_MAE']:.2f}" if k != "0" else "n/a (no prior)", a("https://www.nba.com/games?date=2026-10-20", "scoreboards")] for k, v in res["k_sensitivity"].items()], "ks")
body += f"<p>k=0 is current-season-only. Nested check: k tuned on games through Oct 26 ({br['tune_n']} games) chose k={br['k_chosen']}; on the {br['test_n']} later games its MAE is {br['test_MAE_chosen']:.2f} vs {br['test_MAE_k41']:.2f} for k=41 and {br['test_MAE_HCA']:.2f} for home-court-only.</p>"
page("pages/leaderboard.html", "Strategy leaderboard", body, "Competition among model strategies, scored on skill (error vs a baseline) — not on win/loss streaks or ROI.")
# ------------------------------------------------------------ own lines
hist = {g["game_id"]: g for g in games}
rows = []
for l in lines:
    g = hist.get(l["game_id"])
    result = f"{l['away']} {g['away_pts']} – {l['home']} {g['home_pts']}" if g else "pending (not in data yet)"
    fav = l["home"] if float(l["model_margin_home"]) > 0 else l["away"]
    rows.append([f"{tname(l['away'])} @ {tname(l['home'])}", l["tip_et"], f"{l['home']} {float(l['own_spread_home']):+.1f}", l["own_total"],
                 f"{l['model_away_pts']} – {l['model_home_pts']}", f"{float(l['p_home_win'])*100:.1f}%", f"{int(l['fair_ml_home']):+d} / {int(l['fair_ml_away']):+d}",
                 f"{l['exploratory_total_minus_observed_bias']}", "B2B: " + ", ".join(t for t, k in ((l['away'], 'away_played_nov1'), (l['home'], 'home_played_nov1')) if l[k] == 'yes') if "yes" in (l['home_played_nov1'], l['away_played_nov1']) else "–",
                 result, a(l["game_page_url"], "game page") + " · " + a(l["source_url"], "schedule")])
body = f"""<div class="note"><b>Prospective.</b> Generated {E(lines[0]['generated_utc'])} from {res['n_games']} games through Nov 1; committed to git before the first tip-off (7:00 PM ET = 00:00 UTC Nov 3). Spread is the home side's line (negative = home favourite), rounded to 0.5. Model: <code>{E(lines[0]['model'])}</code>; σ(margin)={lines[0]['sigma_margin']}, σ(total)={lines[0]['sigma_total']}. Fair price = no-vig price implied by the model probability. <b>Not modelled:</b> injuries, rest, travel, lineups. These are research prices, not recommendations; no official market line was available to compare (flag F-07).</div>"""
body += table(["Game", "Tip", "Own spread", "Own total", "Model score (away – home)", "Home win %", "Fair ML (home / away)", "Exploratory bias-adj. total", "Back-to-back (played Nov 1)", "Result", "Sources"], rows, "ol", True)
body += "<h2>Same-game parlay examples: favourite wins + OVER own total</h2><p>Joint probability under a bivariate normal with the estimated correlation, versus naive independence. The adjustment is small and statistically indistinguishable from zero (see <a href='correlations.html'>correlations</a>).</p>"
body += table(["Game", "Leg 1", "Leg 2", "P(leg 1)", "P(leg 2)", "Joint if independent", "Joint (correlated)", "Haircut (pts)", "ρ used", "Source"],
              [[E(p["matchup"]), E(p["leg1"]), E(p["leg2"]), p["p_leg1"], p["p_leg2"], p["p_joint_if_independent"], p["p_joint_correlated"], p["haircut_pct_points"], p["rho_used"], a(p["source_url"], "game page")] for p in parlay], "par")
body += "<h2>Player-prop combos</h2><p><b>Blocked:</b> no official player game logs or prop lines were available. Nothing was inferred. See flag F-08.</p>"
page("pages/own-lines.html", "Own lines – Monday 2 November 2026", body, "Model-originated lines for the 15-game slate.")
# ------------------------------------------------------------ games
rows = []
for g in sorted(games, key=lambda r: (r["date"], r["game_id"]), reverse=True):
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    rows.append([g["date"], g["game_id"], f"{tname(g['away'])}", ap, f"{tname(g['home'])}", hp, f"{hp-ap:+d}", ap + hp, g["overtime"] or "–", a(g["scoreboard_source_url"], "scoreboard") + " · " + a(g["game_page_url"], "game page")])
page("pages/games.html", "All games 2026-27 (to Nov 1)", table(["Date", "Game ID", "Away", "Pts", "Home", "Pts", "Home margin", "Total", "OT", "Sources"], rows, "gm", True) +
     "<p>Flags on specific games: F-01, F-02 (score vs recap-title mismatch), F-04 (47-pt outlier), F-05 (game ID out of sequence) — see <a href='flagged.html'>Flagged for Review</a>.</p>", f"{len(games)} official finals. Scoreboard values as shown on nba.com.")
# ------------------------------------------------------------ standings
def srows(fn):
    out = []
    for r in rd(fn):
        w, l = int(r["W"]), int(r["L"])
        out.append([tname(r["abbr"]), r["conference"], w, l, f"{w/(w+l):.3f}", r["home_W-L"], r["road_W-L"], r["neutral_W-L"], a(r["source_url"], "nba.com standings")])
    return sorted(out, key=lambda x: (-float(x[4]), x[0]))
hd = ["Team", "Conf", "W", "L", "Win%", "Home", "Road", "Neutral", "Source"]
st26 = rd("standings_2026-27.csv")[0]["season"]
body = f"<h2>2026-27 — {E(st26)}</h2>" + table(hd, srows("standings_2026-27.csv"), "s26", True) + "<h2>2025-26 final</h2>" + table(hd, srows("standings_2025-26.csv"), "s25", True) + \
       "<p>Win% computed from the official W and L. Home/road/neutral splits are transcribed from the official standings and reconciled to game-level data (check: 2026-27 splits reproduced from the 92 games for all 30 teams).</p>"
page("pages/standings.html", "Standings", body, "Transcribed from nba.com/standings.")
# ------------------------------------------------------------ team stats
def strows(fn):
    return [[tname(r["abbr"]), r["GP"], r["W"], r["L"], r["PTS_per_game"], r["plus_minus_per_game"], a(r["source_url"], "nba.com stats")] for r in sorted(rd(fn), key=lambda r: -float(r["plus_minus_per_game"]))]
hs = ["Team", "GP", "W", "L", "PTS/g", "+/- per game", "Source"]
body = "<h2>2026-27 to Nov 1, all games</h2>" + table(hs, strows("team_stats_2026-27.csv"), "t26", True) + "<h2>2025-26 regular season, all games</h2>" + table(hs, strows("team_stats_2025-26.csv"), "t25") + \
       "<h2>2025-26 regular season, home games only</h2>" + table(hs, strows("team_stats_2025-26_home.csv"), "t25h") + \
       f"<p>League mean 2025-26 home +/- (GP-weighted) = <b>{res['H']:+.3f}</b> points over 1,225 home games (home win rate {res['home_win_rate_2025_26']*100:.1f}%) — this is the model's home-court term. See flags F-03 (DAL/ATL PTS/g) and F-15 (home GP).</p>"
page("pages/team-stats.html", "Team stats", body, "Per-game traditional team stats, transcribed from nba.com/stats.")
# ------------------------------------------------------------ correlations
rows = [[E(c["pair"]), c["n"] or "", c["r"] or "<i>blank</i>", c["ci95_lo"], c["ci95_hi"], c["p_value"], (tag("UNVERIFIED", "bad") if "UNVERIFIED" in c["reading"] else E(c["reading"])), E(c["definition"]), a(c["source_url"].split(" ")[0], "nba.com")] for c in corr]
body = table(["Pair", "n", "r", "CI low", "CI high", "p (uncorrected)", "Reading", "Definition", "Source"], rows, "co", wrapcols=(7,))
body += """<p>CIs by Fisher z (±1.96/√(n−3)). With n=92 a correlation must exceed about ±0.20 to be distinguishable from zero, and 7 tests are shown, so a single CI that just excludes 0 (favourite wins vs OVER, n=56) is weak evidence and is not used as a correlation in the model — the model uses the residual correlation (row 6). Player-level rows are blank by design: official player logs were not retrievable, and nothing was inferred.</p>"""
page("pages/correlations.html", "Correlations", body, "Game-level only; computed by analysis/correlations.py on the official finals.")
# ------------------------------------------------------------ flagged
sev = {"High": "bad", "Medium": "warn", "Low": "", "Info": ""}
rows = [[x["flag_id"], tag(x["severity"], sev[x["severity"]]), E(x["area"]), E(x["description"]), E(x["evidence"]), E(x["resolution_needed"]), tag(x["status"], "warn"),
         a(x["source_url"], "official source") + " · " + a(x["second_source_url"], "2nd link")] for x in flags]
body = "<p>Irregularities, unverified values and known limits. None blocks the build; each has an official link for manual review. Values that could not be confirmed were left blank, not inferred.</p>" + \
       table(["ID", "Severity", "Area", "Description", "Evidence", "Resolution needed", "Status", "Links"], rows, "fl", True, wrapcols=(3, 5))
page("pages/flagged.html", "Flagged for review", body, f"{len(flags)} items — machine-readable copy: <a href='../../data/flags.csv'>data/flags.csv</a>.")
# ------------------------------------------------------------ repo review
rr = rd("../repo_review/files.csv"); rf = rd("../repo_review/findings.csv")
body = "<h2>Findings</h2>" + table(["ID", "Finding", "Evidence", "Official reference", "Status"], [[x["id"], E(x["finding"]), E(x["evidence"]), a(x["reference_url"], "link"), tag(x["status"], "warn" if x["status"] != "ok" else "ok")] for x in rf], "rf", wrapcols=(1, 2)) + \
       "<h2>Every tracked file</h2>" + table(["Path", "Kind", "Lines", "Data rows", "Rows with official nba.com source", "Git blob", "Author", "Link"], [[E(x["path"]), x["kind"], x["lines"], x["data_rows"], x["rows_with_nba_source"], x["git_blob_sha"][:10], x["author"], a(x["github_url"], "view on GitHub")] for x in rr], "rfiles", True) + \
       "<p>The repository as received had one file (<code>README.md</code>, one line <code>"+"# Own4"+"</code>, no trailing newline) — see <a href='"+REPO+"/blob/319d6b05a6ff2b3d05d82cd313b69d61e72afb50/README.md'>the original commit</a>. Everything else was added in this work. Data rows are reviewed against official pages through the source links and <code>scripts/verify_data.py</code> (see methodology).</p>"
page("pages/repo-review.html", "Repo review", body, "Line-by-line inventory of the repository with source coverage; generated by scripts/make_repo_review.py.")
# ------------------------------------------------------------ methodology
vrows = [[E(c["check"]), tag("PASS" if c["pass"] else "FAIL", "ok" if c["pass"] else "bad"), E(c["detail"][:160]), a(REPO + "/blob/main/scripts/verify_data.py", "verify_data.py")] for c in ver["checks"]]
srcs = [("https://www.nba.com/standings", "Standings 2026-27 (and ?Season=2025-26)", "standings_*.csv"), ("https://www.nba.com/stats/teams/traditional", "Team traditional stats (and Season/Location filters)", "team_stats_*.csv"),
        ("https://www.nba.com/games?date=2026-10-20", "Daily scoreboards, one URL per date (Oct 20 – Nov 1)", "games_2026-27.csv"), ("https://www.nba.com/schedule?month=11", "Nov 2026 schedule (tip times, slate)", "slate_2026-11-02.csv"),
        ("https://www.nba.com/teams", "Team pages / IDs (nba.com/team/<id>)", "teams.csv"), ("https://www.nba.com/stats/players/boxscores", "Player box-score logs — NOT retrieved (blank/unverified)", "correlations.csv (blank rows)")]
body = f"""<h2>Model</h2><ul><li><b>Rating</b>: R = (Σ margin + k·R₂₅)/(n + k), k=41, n = games played; R₂₅ = official 2025-26 +/- per game.</li>
<li><b>Margin</b> = R_home − R_away + H, H = {res['H']:.3f} (GP-weighted mean 2025-26 home +/-).</li>
<li><b>Total</b> = O_h + D_a + O_a + D_h − 2·L with O = points for, D = points against per game (same blend), L = league mean O.</li>
<li><b>Probabilities</b>: Φ(margin/σ), σ = expanding-window residual RMSE (needs ≥30 earlier games). Same-game parlays: bivariate normal with the residual margin–total correlation.</li>
<li><b>Own line</b> = model margin/total rounded to 0.5; fair price = no-vig price of the model probability.</li>
<li><b>Limitations</b>: no opponent adjustment of current-season margins, no injuries/rest/travel, tiny sample.</li></ul>
<h2>Luck-removal protocol</h2><ul><li>Gates and strategy catalogue committed before evaluation (<a href="{REPO}/commit/0b97f52">commit 0b97f52</a>); walk-forward with strict date cut-off; proper scoring rules; paired bootstrap (10,000 reps, seed 20261102); Bonferroni across 6 tests; min n=300; half-sample stability; market gate for any real-money use.</li></ul>
<h2>Data checks (<code>scripts/verify_data.py</code>)</h2>{table(['Check','Result','Detail','Source'],vrows,'vc',wrapcols=(0,2))}
<h2>Official sources used</h2>{table(['URL','Content','Used in','Link'],[[E(u),E(d),E(f_),a(u,'open')] for u,d,f_ in srcs],'src',wrapcols=(1,))}
<h2>Downloads</h2><p>{' · '.join(a('../../data/'+n,n) for n in sorted(x for x in os.listdir(D) if x.endswith('.csv')))}</p>
<h2>Reproduce</h2><pre><code>python3 scripts/verify_data.py\npython3 model/evaluate.py\npython3 analysis/correlations.py\npython3 scripts/make_repo_review.py\npython3 site_src/build_site.py\npython3 scripts/check_site.py</code></pre>"""
page("pages/methodology.html", "Methodology & sources", body, "How lines are made, how strategies are judged, where every number comes from.")
print("site built", BUILT)

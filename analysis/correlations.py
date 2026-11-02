#!/usr/bin/env python3
"""Game-level correlations from the 92 official 2026-27 box-score finals (+ same-game-parlay joint-probability haircut).
Player-level correlations need official player box-score logs, which were not retrieved -> left blank and flagged unverified."""
import csv, math, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from model import *
ROOT = os.path.join(os.path.dirname(__file__), "..")
prior_t, H, HOMEWIN, LG0 = prior()
games = load_games(); N = len(games)
pe = rd("probability_evaluation.csv")
def fisher(r, n):
    if n < 4: return ("", "", "")
    z = math.atanh(r); se = 1 / math.sqrt(n - 3)
    p = math.erfc(abs(z / se) / math.sqrt(2))
    return (math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se), p)
def row(pair, x, y, why, src):
    r = corr(x, y); lo, hi, p = fisher(r, len(x))
    return dict(pair=pair, n=len(x), r=round(r, 3), ci95_lo=round(lo, 3), ci95_hi=round(hi, 3), p_value=round(p, 3),
                reading=("indistinguishable from 0 at this n" if lo <= 0 <= hi else "CI excludes 0"), definition=why, source_url=src)
src = "https://www.nba.com/games?date=2026-10-20 .. 2026-11-01 (92 finals; per-game URLs in data/games_2026-27.csv)"
hm = [g["hp"] - g["ap"] for g in games]; tot = [g["hp"] + g["ap"] for g in games]
hp = [g["hp"] for g in games]; ap = [g["ap"] for g in games]
absm = [abs(m) for m in hm]
out = [
 row("home margin vs game total", hm, tot, "Pearson r, (home pts - away pts) vs (home pts + away pts)", src),
 row("home points vs away points", hp, ap, "Pearson r of the two teams' scores in the same game", src),
 row("|margin| vs game total", absm, tot, "do blowouts coincide with higher totals?", src),
 row("home win (0/1) vs game total", [1.0 if m > 0 else 0.0 for m in hm], tot, "point-biserial", src),
]
# walk-forward residual correlation and leg correlation on probability sample
res = json.load(open(os.path.join(ROOT, "model", "results.json")))
# favourite wins vs over own line (phi coefficient) on the 56 evaluated games
wf = {r["game_id"]: r for r in rd("walk_forward_predictions.csv")}
fw, ov = [], []
for r in pe:
    g = next(x for x in games if x["game_id"] == r["game_id"])
    fav_home = float(wf[r["game_id"]]["pred_margin_BLEND-41"]) > 0
    fw.append(1.0 if ((g["hp"] > g["ap"]) == fav_home) else 0.0)
    ov.append(1.0 if g["hp"] + g["ap"] > float(r["own_total_line"]) else 0.0)
out.append(row("favourite wins vs OVER own total line", fw, ov, "phi coefficient; legs of the PARLAY-CORR strategy (games with >=30 earlier games)", src))
r_res = res["own_lines_sigma"]["rho_margin_total_residual"]
em_ = [g["hp"] - g["ap"] - float(wf[g["game_id"]]["pred_margin_BLEND-41"]) for g in games]
et_ = [g["hp"] + g["ap"] - float(wf[g["game_id"]]["pred_total_BLEND-41"]) for g in games]
out.append(row("model margin error vs model total error", em_, et_, "residual correlation used as rho in PARLAY-CORR (walk-forward predictions)", src))
# player-level: blank + unverified
for pair in ("player points vs same player assists", "player points vs same player rebounds", "player points vs team total", "player points vs teammate points",
             "player points vs opponent defensive rating", "player minutes vs player points"):
    out.append(dict(pair=pair, n="", r="", ci95_lo="", ci95_hi="", p_value="", reading="UNVERIFIED - not computed", definition="needs official player box-score logs (nba.com/stats player game logs) which were not retrievable here",
                    source_url="https://www.nba.com/stats/players/boxscores"))
with open(os.path.join(ROOT, "data", "correlations.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
# parlay haircut for the Nov 2 slate (favourite ML + OVER own total)
lines = rd("own_lines_2026-11-02.csv")
sm, st, rho = res["own_lines_sigma"]["sigma_margin"], res["own_lines_sigma"]["sigma_total"], res["own_lines_sigma"]["rho_margin_total_residual"]
pr = []
for l in lines:
    m, t, L = float(l["model_margin_home"]), float(l["model_total"]), float(l["own_total"])
    fav_home = m > 0
    p1 = phi(abs(m) / sm); p2 = 1 - phi((L - t) / st)
    j = orthant(-abs(m) / sm, (L - t) / st, rho if fav_home else -rho)
    pr.append(dict(date=l["date"], game_id=l["game_id"], matchup=f"{l['away']} @ {l['home']}", leg1="favourite " + (l["home"] if fav_home else l["away"]) + " wins", leg2=f"OVER {L}",
                   p_leg1=round(p1, 4), p_leg2=round(p2, 4), p_joint_if_independent=round(p1 * p2, 4), p_joint_correlated=round(j, 4),
                   haircut_pct_points=round(100 * (j - p1 * p2), 2), rho_used=round(rho if fav_home else -rho, 3),
                   note="rho estimated on 92 games; 95% CI roughly +/-0.20 so the adjustment is NOT statistically distinguishable from zero",
                   source_url=l["game_page_url"]))
with open(os.path.join(ROOT, "data", "parlay_examples_2026-11-02.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, list(pr[0].keys())); w.writeheader(); w.writerows(pr)
for o in out: print(o["pair"], o["n"], o["r"], o["ci95_lo"], o["ci95_hi"])
print(max(abs(p["haircut_pct_points"]) for p in pr))

#!/usr/bin/env python3
"""Walk-forward evaluation + leaderboard + own lines for the 2026-11-02 slate.
Run:  python3 model/evaluate.py [--refresh-lines]
Thresholds come from strategies/gates.json (pre-registered in commit 0b97f52 before this code was run)."""
import csv, json, math, os, subprocess, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
from model import *

ROOT = os.path.join(os.path.dirname(__file__), "..")
GATES = json.load(open(os.path.join(ROOT, "strategies", "gates.json")))
K_GRID = [0, 10, 20, 41, 60, 82, 1000]
prior_t, H, HOMEWIN, LG0 = prior()
games = load_games()
rows, final_sums = walk_forward(games, K_GRID, prior_t, H, LG0)
N = len(rows)

def mae(xs): return mean(abs(x) for x in xs)
def rmse(xs): return math.sqrt(mean(x * x for x in xs))
def err(rows_, pred, actual): return [r[pred] - r[actual] for r in rows_]

res = {"n_games": N, "H": H, "home_win_rate_2025_26": HOMEWIN, "league_avg_pts_per_team_2025_26": LG0}
# ---------- point forecasts on all games
def summarize(pred, actual):
    e = err(rows, pred, actual)
    return dict(MAE=mae(e), RMSE=rmse(e), bias=mean(e), n=len(e))
margin_models = {"BASE-HCA": "m_hca", "PRIOR-ONLY": "m_prior", "CURRENT-ONLY": "m_cur", "BLEND-41": "m_k41"}
res["margin"] = {k: summarize(v, "margin") for k, v in margin_models.items()}
for k, v in margin_models.items():
    res["margin"][k]["straight_up_hit"] = mean(1.0 if (r[v] > 0) == (r["margin"] > 0) else 0.0 for r in rows)
res["total"] = {"BASE-LGTOTAL": summarize("t_lg", "total"), "BLEND-41-TOTAL": summarize("t_k41", "total")}
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - r) / d, (c + r) / d]
for k_, v_ in margin_models.items():
    hits = round(res["margin"][k_]["straight_up_hit"] * N)
    res["margin"][k_]["hits"] = hits; res["margin"][k_]["hit_wilson95"] = wilson(hits, N)
res["home_win_rate_2026_27_so_far"] = mean(1.0 if r["margin"] > 0 else 0.0 for r in rows)
res["mean_margin_2026_27"] = mean(r["margin"] for r in rows)
res["mean_total_2026_27"] = mean(r["total"] for r in rows)
# sensitivity grid (exploratory, not for ranking)
res["k_sensitivity"] = {str(k): dict(margin_MAE=mae(err(rows, f"m_k{k}", "margin")), total_MAE=mae(err(rows, f"t_k{k}", "total"))) for k in K_GRID}
# nested tuning check
tune = [r for r in rows if r["date"] <= "2026-10-26"]; test = [r for r in rows if r["date"] > "2026-10-26"]
kbest = min(K_GRID, key=lambda k: mae(err(tune, f"m_k{k}", "margin")))
res["nested_k"] = dict(tune_n=len(tune), test_n=len(test), k_chosen=kbest,
                        test_MAE_chosen=mae(err(test, f"m_k{kbest}", "margin")), test_MAE_k41=mae(err(test, "m_k41", "margin")),
                        test_MAE_HCA=mae(err(test, "m_hca", "margin")),
                        tune_MAE_by_k={str(k): mae(err(tune, f"m_k{k}", "margin")) for k in K_GRID})
# ---------- probability targets (need >=30 earlier games)
def sigma_rho(past):
    em = [r["margin"] - r["m_k41"] for r in past]; et = [r["total"] - r["t_k41"] for r in past]
    return rmse(em), rmse(et), corr(em, et)
prob_rows = []
for r in rows:
    past = [x for x in rows if x["date"] < r["date"]]
    assert all(x["date"] < r["date"] for x in past)
    if len(past) < 30: continue
    sm, st, rho = sigma_rho(past)
    m, t = r["m_k41"], r["t_k41"]
    p_win = phi(m / sm); y_win = 1.0 if r["margin"] > 0 else 0.0
    fav_home = m > 0
    line = round_half(t)
    p1 = phi(abs(m) / sm); p2 = 1 - phi((line - t) / st)
    rs = rho if fav_home else -rho
    joint = orthant(-abs(m) / sm, (line - t) / st, rs)
    fav_won = (r["margin"] > 0) == fav_home; over = r["total"] > line
    y_par = 1.0 if (fav_won and over) else 0.0
    prob_rows.append(dict(r, sigma_m=sm, sigma_t=st, rho=rho, p_win=p_win, y_win=y_win, p_base=HOMEWIN,
                          line=line, p1=p1, p2=p2, p_indep=p1 * p2, p_corr=joint, y_par=y_par, y_over=1.0 if over else 0.0, y_fav=1.0 if fav_won else 0.0))
NP = len(prob_rows)
brier = lambda ps, ys: mean((p - y) ** 2 for p, y in zip(ps, ys))
res["prob"] = dict(n=NP,
    win=dict(brier_strategy=brier([r["p_win"] for r in prob_rows], [r["y_win"] for r in prob_rows]),
             brier_baseline=brier([r["p_base"] for r in prob_rows], [r["y_win"] for r in prob_rows]),
             mean_pred=mean(r["p_win"] for r in prob_rows), observed=mean(r["y_win"] for r in prob_rows),
             logloss_strategy=mean(-(math.log(r["p_win"]) if r["y_win"] else math.log(1 - r["p_win"])) for r in prob_rows),
             logloss_baseline=mean(-(math.log(r["p_base"]) if r["y_win"] else math.log(1 - r["p_base"])) for r in prob_rows)),
    parlay=dict(brier_corr=brier([r["p_corr"] for r in prob_rows], [r["y_par"] for r in prob_rows]),
                brier_indep=brier([r["p_indep"] for r in prob_rows], [r["y_par"] for r in prob_rows]),
                mean_pred_corr=mean(r["p_corr"] for r in prob_rows), mean_pred_indep=mean(r["p_indep"] for r in prob_rows),
                observed=mean(r["y_par"] for r in prob_rows)))
# ---------- bootstrap tests (G4) and gates
M = 6
LEVEL_FAMILY = 1 - 0.05 / M
def paired(diffs):
    lo_f, hi_f = boot_ci(diffs, LEVEL_FAMILY); lo, hi = boot_ci(diffs, 0.95)
    h = len(diffs) // 2
    return dict(mean_diff=mean(diffs), ci_family=[lo_f, hi_f], ci95=[lo, hi], half1=mean(diffs[:h]), half2=mean(diffs[h:]), n=len(diffs))
tests = {}
for sid, col in (("PRIOR-ONLY", "m_prior"), ("CURRENT-ONLY", "m_cur"), ("BLEND-41", "m_k41")):
    tests[sid] = paired([abs(r["m_hca"] - r["margin"]) - abs(r[col] - r["margin"]) for r in rows])
tests["BLEND-41-TOTAL"] = paired([abs(r["t_lg"] - r["total"]) - abs(r["t_k41"] - r["total"]) for r in rows])
tests["BLEND-41-WIN"] = paired([(r["p_base"] - r["y_win"]) ** 2 - (r["p_win"] - r["y_win"]) ** 2 for r in prob_rows])
tests["PARLAY-CORR"] = paired([(r["p_indep"] - r["y_par"]) ** 2 - (r["p_corr"] - r["y_par"]) ** 2 for r in prob_rows])
# exploratory head-to-head (not part of the gates)
res["exploratory"] = {"BLEND-41 vs PRIOR-ONLY (MAE gain)": paired([abs(r["m_prior"] - r["margin"]) - abs(r["m_k41"] - r["margin"]) for r in rows]),
                      "BLEND-41 vs CURRENT-ONLY (MAE gain)": paired([abs(r["m_cur"] - r["margin"]) - abs(r["m_k41"] - r["margin"]) for r in rows])}
res["tests"] = tests
ok_verify = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_data.py")], capture_output=True).returncode == 0
G = {g["id"]: g for g in GATES["gates"]}
def gate_scores(sid, n_eval, t, kind):
    pts = {}
    pts["G1"] = G["G1"]["points"] if ok_verify else 0
    pts["G2"] = G["G2"]["points"]  # asserted in walk_forward() and in the probability loop
    pts["G3"] = G["G3"]["points"] if n_eval >= 300 else 0
    pts["G4"] = G["G4"]["points"] if t["ci_family"][0] > 0 else 0
    if kind == "point":
        bias = {"BLEND-41": res["margin"]["BLEND-41"]["bias"], "PRIOR-ONLY": res["margin"]["PRIOR-ONLY"]["bias"],
                "CURRENT-ONLY": res["margin"]["CURRENT-ONLY"]["bias"], "BLEND-41-TOTAL": res["total"]["BLEND-41-TOTAL"]["bias"]}[sid]
        pts["G5"] = G["G5"]["points"] if (abs(bias) <= 1.5 and t["mean_diff"] > 0) else 0
    elif sid == "BLEND-41-WIN":
        w = res["prob"]["win"]
        pts["G5"] = G["G5"]["points"] if (w["brier_strategy"] <= w["brier_baseline"] and abs(w["mean_pred"] - w["observed"]) <= 0.05) else 0
    else:
        p = res["prob"]["parlay"]
        pts["G5"] = G["G5"]["points"] if (p["brier_corr"] <= p["brier_indep"] and abs(p["mean_pred_corr"] - p["observed"]) <= 0.05) else 0
    pts["G6"] = 0
    pts["G7"] = G["G7"]["points"] if (t["half1"] > 0 and t["half2"] > 0) else 0
    return pts
lb = []
def add(sid, target, metric, sval, bval, n_eval, kind):
    t = tests[sid]; pts = gate_scores(sid, n_eval, t, kind); total = sum(pts.values())
    fv = pts["G3"] and pts["G4"] and total >= 60
    if fv: tier = "Forecast-validated"
    elif pts["G1"] and pts["G2"] and t["mean_diff"] > 0: tier = "Provisional"
    else: tier = "Rejected"
    lb.append(dict(id=sid, target=target, metric=metric, strategy_value=sval, baseline_value=bval, gain=t["mean_diff"],
                   ci_family_lo=t["ci_family"][0], ci_family_hi=t["ci_family"][1], ci95_lo=t["ci95"][0], ci95_hi=t["ci95"][1],
                   n_eval=n_eval, **{k: v for k, v in pts.items()}, score=total, tier=tier, reward_units=0))
for sid in ("PRIOR-ONLY", "CURRENT-ONLY", "BLEND-41"):
    add(sid, "margin", "MAE (pts)", res["margin"][sid]["MAE"], res["margin"]["BASE-HCA"]["MAE"], N, "point")
add("BLEND-41-TOTAL", "total", "MAE (pts)", res["total"]["BLEND-41-TOTAL"]["MAE"], res["total"]["BASE-LGTOTAL"]["MAE"], N, "point")
add("BLEND-41-WIN", "win", "Brier", res["prob"]["win"]["brier_strategy"], res["prob"]["win"]["brier_baseline"], NP, "prob")
add("PARLAY-CORR", "parlay", "Brier", res["prob"]["parlay"]["brier_corr"], res["prob"]["parlay"]["brier_indep"], NP, "parlay")
# reward allocation per pre-registered rule
q = [x for x in lb if x["tier"] == "Forecast-validated"]
tot = sum(x["score"] for x in q)
for x in q: x["reward_units"] = round(1000 * x["score"] / tot, 1)
res["reward_pool_allocated"] = sum(x["reward_units"] for x in lb)
res["leaderboard_tiers"] = {x["id"]: x["tier"] for x in lb}
for b in GATES["catalogue"]:
    if b.get("status") == "Blocked":
        lb.append(dict(id=b["id"], target=b["target"], metric="", strategy_value="", baseline_value="", gain="", ci_family_lo="", ci_family_hi="", ci95_lo="", ci95_hi="",
                       n_eval=0, G1="", G2="", G3="", G4="", G5="", G6="", G7="", score=0, tier="Blocked", reward_units=0, reason=b["reason"]))
for x in lb:
    x["source_url"] = "https://www.nba.com/stats/players/boxscores" if x["id"].startswith("PROP") else ("https://www.nba.com/games" if x["id"] == "MARKET-SINGLES" else "https://www.nba.com/games?date=2026-10-20")
fields = ["id", "target", "metric", "strategy_value", "baseline_value", "gain", "ci_family_lo", "ci_family_hi", "ci95_lo", "ci95_hi", "n_eval",
          "G1", "G2", "G3", "G4", "G5", "G6", "G7", "score", "tier", "reward_units", "reason", "source_url"]
with open(os.path.join(D, "leaderboard.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fields, extrasaction="ignore"); w.writeheader()
    for x in lb:
        w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()})
# per-game walk-forward predictions
with open(os.path.join(D, "walk_forward_predictions.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "game_id", "away", "home", "away_pts", "home_pts", "games_played_before", "pred_margin_BASE-HCA", "pred_margin_PRIOR-ONLY", "pred_margin_CURRENT-ONLY",
                "pred_margin_BLEND-41", "pred_total_BASE-LGTOTAL", "pred_total_BLEND-41", "source_url"])
    for r in rows:
        w.writerow([r["date"], r["game_id"], r["away"], r["home"], r["ap"], r["hp"], r["n_before"]] + [round(r[c], 2) for c in ("m_hca", "m_prior", "m_cur", "m_k41", "t_lg", "t_k41")]
                   + [f"https://www.nba.com/games?date={r['date']}"])
with open(os.path.join(D, "probability_evaluation.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "game_id", "away", "home", "p_home_win", "home_won", "own_total_line", "p_fav_wins", "p_over", "p_parlay_indep", "p_parlay_corr", "parlay_hit", "sigma_margin", "sigma_total", "rho", "source_url"])
    for r in prob_rows:
        w.writerow([r["date"], r["game_id"], r["away"], r["home"], round(r["p_win"], 4), int(r["y_win"]), r["line"], round(r["p1"], 4), round(r["p2"], 4), round(r["p_indep"], 4), round(r["p_corr"], 4),
                    int(r["y_par"]), round(r["sigma_m"], 2), round(r["sigma_t"], 2), round(r["rho"], 3), f"https://www.nba.com/games?date={r['date']}"])
# ---------- own lines for the 2026-11-02 slate (ratings use all 92 games through 2026-11-01)
slate = rd("slate_2026-11-02.csv")
rt = ratings(prior_t, final_sums, 41)
sm, st, rho = sigma_rho(rows)
played_nov1 = {g["home"] for g in games if g["date"] == "2026-11-01"} | {g["away"] for g in games if g["date"] == "2026-11-01"}
mean_O = mean(v["O"] for v in rt.values())
def american(p):
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))
lines = []
for s in slate:
    h, a = s["home"], s["away"]
    m, t = predict(rt, h, a, H)
    hp = (rt[h]["O"] + rt[a]["Dn"] - mean_O); ap = (rt[a]["O"] + rt[h]["Dn"] - mean_O)
    pw = phi(m / sm); L = round_half(t)
    lines.append({"date": s["date"], "game_id": s["game_id"], "away": a, "home": h, "tip_et": s["tip_et"],
                  "own_spread_home": -round_half(m) + 0.0, "own_total": L, "model_margin_home": round(m, 2), "model_total": round(t, 2),
                  "model_home_pts": round(hp, 1), "model_away_pts": round(ap, 1), "p_home_win": round(pw, 4),
                  "fair_ml_home": american(pw), "fair_ml_away": american(1 - pw), "p_over_own_total": round(1 - phi((L - t) / st), 3),
                  "sigma_margin": round(sm, 2), "sigma_total": round(st, 2), "games_played_home": final_sums[h][0], "games_played_away": final_sums[a][0],
                  "home_played_nov1": "yes" if h in played_nov1 else "no", "away_played_nov1": "yes" if a in played_nov1 else "no",
                  "model": "BLEND-41 (k=41, H=%.3f)" % H, "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                  "exploratory_total_minus_observed_bias": round(t - res["total"]["BLEND-41-TOTAL"]["bias"], 1), "not_modelled": "injuries, rest/back-to-back, travel, lineup",
                  "source_url": s["source_url"], "game_page_url": s["game_page_url"]})
# Prospective lines are FROZEN once written (committed before tip-off); pass --refresh-lines to overwrite deliberately.
if "--refresh-lines" in sys.argv or not os.path.exists(os.path.join(D, "own_lines_2026-11-02.csv")):
    with open(os.path.join(D, "own_lines_2026-11-02.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, list(lines[0].keys())); w.writeheader(); w.writerows(lines)
res["own_lines_sigma"] = dict(sigma_margin=sm, sigma_total=st, rho_margin_total_residual=rho)
res["own_lines_note"] = "uses all 92 games to 2026-11-01"
json.dump(res, open(os.path.join(ROOT, "model", "results.json"), "w"), indent=1)
print(json.dumps({k: res[k] for k in ("margin", "total", "nested_k", "prob", "own_lines_sigma", "k_sensitivity", "exploratory")}, indent=1))
print(json.dumps(tests, indent=1))
for x in lb: print(x["id"], x["tier"], x["score"], x.get("G3"), x.get("G4"), x.get("G5"), x.get("G7"))

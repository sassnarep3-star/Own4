#!/usr/bin/env python3
"""Own-line engine: strictly walk-forward Elo + regressed points-per-game totals.

All parameters are read from nfl/data/preregistration.json (frozen before analysis).
Produces nfl/data/walk_forward.csv, nfl/data/own_lines.csv, nfl/data/model_results.json.
"""
from __future__ import annotations
import math, sys
from collections import defaultdict
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import (DATA, TEAM_ABBR, TEAM_NAME, S_STAND25, WEEK_URL,
                    read_csv, write_csv, save_json, load_json, normal_cdf,
                    american_odds, mean, links)


def initial_ratings(params):
    e = params["prior_pythagorean_exponent"]
    scale = params["prior_rating_scale"]
    out = {}
    for r in read_csv("standings_2025.csv"):
        pf, pa = float(r["PF"]), float(r["PA"])
        pyth = pf ** e / (pf ** e + pa ** e)
        out[r["abbr"]] = params["initial_rating"] + (pyth - 0.5) * scale
    return out


def team_state(prior_games, params):
    st = {a: dict(gp=0, pf=0, pa=0) for a in TEAM_ABBR.values()}
    for g in prior_games:
        st[g["away"]]["gp"] += 1
        st[g["home"]]["gp"] += 1
        st[g["away"]]["pf"] += g["away_pts"]; st[g["away"]]["pa"] += g["home_pts"]
        st[g["home"]]["pf"] += g["home_pts"]; st[g["home"]]["pa"] += g["away_pts"]
    lg_total = mean([g["total_pts"] for g in prior_games])
    lg_ppg = lg_total / 2.0
    min_g = params["min_team_games_for_total"]
    for a, s in st.items():
        if s["gp"] < min_g:
            s["pf_pg"], s["pa_pg"] = lg_ppg, lg_ppg
        else:
            s["pf_pg"], s["pa_pg"] = s["pf"] / s["gp"], s["pa"] / s["gp"]
        s["net_pg"] = s["pf_pg"] - s["pa_pg"]
    return st, lg_total, lg_ppg


def expected_win(ratings, away, home, params, neutral=False):
    hfa = 0.0 if neutral else params["home_advantage_points"]
    margin = (ratings[home] - ratings[away]) / params["rating_to_points_divisor"] + hfa
    return margin, normal_cdf(margin, 0, params["margin_sigma_points"])


def predict_game(g, week, ratings, st, lg_total, params, init_ratings_, neutral=False):
    away, home = g["away"], g["home"]
    margin, p = expected_win(ratings, away, home, params, neutral)
    hfa = 0.0 if neutral else params["home_advantage_points"]
    static_margin = (init_ratings_[home] - init_ratings_[away]) / params["rating_to_points_divisor"] + hfa
    static_p = normal_cdf(static_margin, 0, params["margin_sigma_points"])
    raw_total = ((st[away]["pf_pg"] + st[home]["pa_pg"]) / 2.0
                 + (st[home]["pf_pg"] + st[away]["pa_pg"]) / 2.0)
    pred_total = lg_total + params["total_shrink"] * (raw_total - lg_total)
    return {
        "game_id": g["game_id"], "week": week, "date": g.get("date", ""),
        "away": away, "home": home,
        "away_name": TEAM_NAME[away], "home_name": TEAM_NAME[home],
        "elo_rating_away": round(ratings[away], 3),
        "elo_rating_home": round(ratings[home], 3),
        "pred_home_margin": round(margin, 4),
        "p_home_win": round(p, 6),
        "fair_spread_home": round(-margin, 3),
        "fair_total": round(pred_total, 3),
        "fair_moneyline_home": american_odds(p),
        "fair_moneyline_away": american_odds(1 - p),
        "league_prior_mean_total": round(lg_total, 3),
        "static_p_home_win": round(static_p, 6),
        "prior_net_pg_away": round(st[away]["net_pg"], 3),
        "prior_net_pg_home": round(st[home]["net_pg"], 3),
        "prior_gp_away": st[away]["gp"], "prior_gp_home": st[home]["gp"],
        "actual_away_pts": g.get("away_pts", 0), "actual_home_pts": g.get("home_pts", 0),
        "actual_home_margin": g.get("home_margin", 0), "actual_total": g.get("total_pts", 0),
        "home_win": g.get("home_win", 0.5),
        "source_url": g["source_url"], "week_url": g["week_url"],
    }


def run(games, params, holdout_start=3):
    if holdout_start is None:
        holdout_start = 3
    init = initial_ratings(params)
    ratings = dict(init)
    weeks = sorted({g["week"] for g in games})
    preds = []
    for w in weeks:
        prior = [g for g in games if g["week"] < w]
        st, lg_total, _ = team_state(prior, params)
        here = [g for g in games if g["week"] == w]
        if w >= holdout_start:
            for g in here:
                preds.append(predict_game(g, w, ratings, st, lg_total, params, init))
        deltas = defaultdict(float)
        for g in here:
            _, p = expected_win(ratings, g["away"], g["home"], params)
            mov = min(2.0, math.log(abs(g["home_margin"]) + 1) / math.log(16))
            delta = params["k_factor"] * (g["home_win"] - p) * mov
            deltas[g["home"]] += delta
            deltas[g["away"]] -= delta
        for a, d in deltas.items():
            ratings[a] += d
    return ratings, preds, init


def evaluate(preds, half_split):
    ties = [p for p in preds if p["home_win"] == 0.5]
    graded = [p for p in preds if p["home_win"] != 0.5]
    correct = 0
    brier = brier_const = brier_static = logloss = 0.0
    margin_mae = total_mae = 0.0
    for p in preds:
        y = p["home_win"]
        q = min(1 - 1e-12, max(1e-12, p["p_home_win"]))
        qs = min(1 - 1e-12, max(1e-12, p["static_p_home_win"]))
        brier += (q - y) ** 2
        brier_const += (0.5 - y) ** 2
        brier_static += (qs - y) ** 2
        logloss -= (y * math.log(q) + (1 - y) * math.log(1 - q))
        margin_mae += abs(p["pred_home_margin"] - p["actual_home_margin"])
        total_mae += abs(p["fair_total"] - p["actual_total"])
        if y != 0.5:
            pick_home = p["p_home_win"] >= 0.5
            if (pick_home and y == 1) or ((not pick_home) and y == 0):
                correct += 1
    n = len(preds)
    halves = {}
    for weeks in half_split:
        label = f"W{min(weeks)}-{max(weeks)}"
        rows = [p for p in preds if p["week"] in weeks and p["home_win"] != 0.5]
        c = sum(1 for p in rows if ((p["p_home_win"] >= 0.5 and p["home_win"] == 1)
                                    or (p["p_home_win"] < 0.5 and p["home_win"] == 0)))
        halves[label] = {"n": len(rows), "correct": c,
                         "accuracy": c / len(rows) if rows else None}
    return {
        "n_predictions": n, "n_graded_winners": len(graded), "n_ties": len(ties),
        "winner_correct": correct,
        "winner_accuracy": correct / len(graded) if graded else None,
        "brier": brier / n, "brier_baseline_050": brier_const / n,
        "brier_static_prior_model": brier_static / n,
        "brier_skill_vs_baseline": (brier_const - brier) / n,
        "log_loss": logloss / n,
        "margin_mae": margin_mae / n, "total_mae": total_mae / n,
        "beats_constant_baseline": brier < brier_const,
        "beats_static_prior_model": brier < brier_static,
        "half_split": halves,
        "note": "Brier and log loss include the single tie as y=0.5; winner accuracy excludes ties.",
    }


def no_lookahead_test(games, params, preds, holdout_start=3):
    """Change a Week 8 final score; no Week 3-7 prediction may change."""
    target = next(g for g in games if g["week"] == 8)
    perturbed = []
    for g in games:
        h = dict(g)
        if h["game_id"] == target["game_id"]:
            h["home_pts"] += 7
            h["total_pts"] += 7
            h["home_margin"] += 7
            h["abs_home_margin"] = abs(h["home_margin"])
            h["home_win"] = 1 if h["home_margin"] > 0 else (0 if h["home_margin"] < 0 else 0.5)
        perturbed.append(h)
    _, preds2, _ = run(perturbed, params, holdout_start)
    key = lambda p: (p["game_id"], p["pred_home_margin"], p["p_home_win"], p["fair_total"])
    first = [p for p in preds if p["week"] <= 7]
    second = [p for p in preds2 if p["week"] <= 7]
    return {
        "test": "Perturb one Week 8 official score by +7 home points and recompute",
        "weeks_compared": "3-7 (plus all 8 holdout weeks checked)",
        "predictions_compared": len(first),
        "identical": [key(p) for p in first] == [key(p) for p in second]
                      and [key(p) for p in preds] == [key(p) for p in preds2],
        "conclusion": "No future information enters a prediction" ,
        "method_source": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm",
        "data_source": target["source_url"],
    }


def own_lines(upcoming, games, ratings, params, init):
    st, lg_total, _ = team_state(games, params)
    out = []
    for r in upcoming:
        neutral = r.get("neutral_site", "").strip().lower() == "yes"
        g = {"game_id": r["source_url"].rstrip("/").split("/")[-1],
             "away": r["away"], "home": r["home"], "date": r["kickoff_local"],
             "source_url": r["source_url"], "week_url": r["week_url"]}
        p = predict_game(g, int(r["week"]), ratings, st, lg_total, params, init, neutral)
        out.append({
            "week": r["week"], "kickoff_local": r["kickoff_local"],
            "away": r["away"], "home": r["home"],
            "away_name": TEAM_NAME[r["away"]], "home_name": TEAM_NAME[r["home"]],
            "elo_rating_away": p["elo_rating_away"], "elo_rating_home": p["elo_rating_home"],
            "fair_spread_home": p["fair_spread_home"],
            "fair_total": p["fair_total"],
            "p_home_win": p["p_home_win"],
            "fair_moneyline_home": p["fair_moneyline_home"],
            "fair_moneyline_away": p["fair_moneyline_away"],
            "market_spread": "", "market_total": "", "market_moneyline": "",
            "closing_line": "",
            "neutral_site": "yes" if neutral else "",
            "note": r["note"],
            "source_url": r["source_url"], "week_url": r["week_url"],
        })
    return out


def main():
    reg = load_json("preregistration.json")
    params = reg["model"]["params"]
    games = load_json("games.json")["games"]
    games.sort(key=lambda g: (g["week"], g["game_id"]))
    holdout = reg["data"]["holdout_start_week"]
    ratings, preds, init = run(games, params, holdout)
    results = evaluate(preds, reg["luck_removal"]["half_split"])
    perturb = no_lookahead_test(games, params, preds, holdout)
    lines = own_lines(read_csv("upcoming_2026.csv"), games, ratings, params, init)

    wf_fields = list(preds[0].keys())
    write_csv("walk_forward.csv", preds, wf_fields)
    ol_fields = list(lines[0].keys())
    write_csv("own_lines.csv", lines, ol_fields)
    save_json("model_results.json", {
        "model": reg["model"]["name"],
        "parameters": params,
        "parameters_are_project_defined": True,
        "walk_forward": results,
        "no_lookahead_perturbation": perturb,
        "final_ratings": {a: round(v, 3) for a, v in sorted(ratings.items())},
        "own_line_count": len(lines),
        "official_data_sources": [WEEK_URL[w] for w in range(1, 10)] + [S_STAND25],
        "method_sources": [
            "https://scikit-learn.org/stable/modules/calibration.html",
            "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm",
        ],
    })
    r = results
    print(f"walk-forward n={r['n_predictions']} graded={r['n_graded_winners']} ties={r['n_ties']}")
    print(f"winner accuracy={r['winner_accuracy']:.4f} Brier={r['brier']:.4f} "
          f"baseline={r['brier_baseline_050']:.4f} static={r['brier_static_prior_model']:.4f}")
    print(f"margin MAE={r['margin_mae']:.2f} total MAE={r['total_mae']:.2f} "
          f"no-lookahead identical={perturb['identical']}")
    print(f"own lines produced={len(lines)}")
    if not perturb["identical"]:
        raise SystemExit("no-lookahead perturbation FAILED")


if __name__ == "__main__":
    main()

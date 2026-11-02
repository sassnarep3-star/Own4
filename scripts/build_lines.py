"""T04 — Originate our own NBA lines and run the no-lookahead settlement backtest.

Outputs:
  data/derived/lines.json     our own fair lines for the 2026-11-04 official slate
  data/derived/backtest.json  out-of-sample settlement metrics for the prior-season model

Every input is read from ``data/raw/`` (official NBA.com transcriptions). No market odds,
no home-court adjustment and no blend weights are invented: those cells are emitted as null
with an explicit ``unverified`` flag.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (RAW, DERIVED, SRC, TEAMS, binom_two_sided, fmt,  # noqa: E402
                    pearson, permutation_p, read_json, wilson_ci, write_json)
from model import league_avg, normal_cdf, price, project, residual_sd, season_ratings  # noqa: E402

R25 = season_ratings(RAW / "advanced_2025_26.json")
R26 = season_ratings(RAW / "advanced_2026_27.json")
L25 = league_avg(R25)
L26 = league_avg(R26)

SETTLED = read_json(RAW / "settled_games.json")["rows"]
SLATE = read_json(RAW / "slate_2026_11_04.json")["rows"]

TRAIN = [g for g in SETTLED if g["date"] <= "2026-10-28"]
HOLDOUT = [g for g in SETTLED if g["date"] >= "2026-10-30"]

SIGMA, TRAIN_BIAS = residual_sd(TRAIN, R25, L25)


def evaluate(games, label):
    rows = []
    for g in games:
        pr = project(g["team_a"], g["team_b"], R25, L25)
        prc = price(pr["margin"], SIGMA)
        am = g["score_a"] - g["score_b"]
        at = g["score_a"] + g["score_b"]
        outcome = 1 if am > 0 else 0
        rows.append({
            "date": g["date"],
            "game_id": g["game_id"],
            "team_a": g["team_a"],
            "team_b": g["team_b"],
            "score_a": g["score_a"],
            "score_b": g["score_b"],
            "pred_margin": pr["margin"],
            "pred_total": pr["total"],
            "actual_margin": am,
            "actual_total": at,
            "margin_error": am - pr["margin"],
            "total_error": at - pr["total"],
            "p_a": prc["p_a"],
            "outcome_a": outcome,
            "winner_correct": (pr["margin"] > 0) == (am > 0),
            "brier": (prc["p_a"] - outcome) ** 2,
            "source": g["source"],
            "game_url": g["game_url"],
        })
    n = len(rows)
    if n == 0:
        return {"window": label, "n": 0}
    k = sum(1 for r in rows if r["winner_correct"])
    acc = k / n
    lo, hi = wilson_ci(k, n)
    brier = sum(r["brier"] for r in rows) / n
    margin_mae = sum(abs(r["margin_error"]) for r in rows) / n
    total_mae = sum(abs(r["total_error"]) for r in rows) / n
    margin_bias = sum(r["margin_error"] for r in rows) / n
    total_bias = sum(r["total_error"] for r in rows) / n
    r_margin = pearson([r["pred_margin"] for r in rows], [r["actual_margin"] for r in rows])
    p_perm = permutation_p([r["pred_margin"] for r in rows], [r["actual_margin"] for r in rows])
    # naive baseline: pick the team with the better official 2025-26 W-L record
    base_correct = sum(
        1 for r in rows
        if ((R25[r["team_a"]]["w"] > R25[r["team_b"]]["w"]) == (r["actual_margin"] > 0))
    )
    return {
        "window": label,
        "n": n,
        "winner_correct": k,
        "winner_accuracy": acc,
        "accuracy_wilson_95ci": [lo, hi],
        "binomial_p_two_sided_vs_0_5": binom_two_sided(k, n, 0.5),
        "naive_prior_record_baseline_correct": base_correct,
        "naive_prior_record_baseline_accuracy": base_correct / n,
        "brier_score": brier,
        "brier_skill_score_vs_0_5": 1.0 - brier / 0.25,
        "margin_mae": margin_mae,
        "margin_bias": margin_bias,
        "total_mae": total_mae,
        "total_bias": total_bias,
        "pred_vs_actual_margin_pearson_r": r_margin,
        "pred_vs_actual_margin_permutation_p": p_perm,
        "rows": rows,
        "sources": [SRC["adv_2025"], SRC["games_1023"], SRC["games_1024"], SRC["games_1026"],
                    SRC["games_1028"], SRC["games_1030"], SRC["games_1031"], SRC["games_1101"]],
    }


TRAIN_M = evaluate(TRAIN, "train 2026-10-23..2026-10-28 (used to estimate sigma)")
HOLDOUT_M = evaluate(HOLDOUT, "holdout 2026-10-30..2026-11-01 (out-of-sample)")
ALL_M = evaluate(SETTLED, "all 62 settled games (descriptive only)")

lines = []
for g in SLATE:
    a, b = g["team_a"], g["team_b"]
    p25 = project(a, b, R25, L25)
    p26 = project(a, b, R26, L26)
    prc = price(p25["margin"], SIGMA)
    lines.append({
        "game_id": g["game_id"],
        "date": "2026-11-04",
        "time_et": g["time_et"],
        "team_a": a,
        "team_a_name": TEAMS[a]["name"],
        "team_b": b,
        "team_b_name": TEAMS[b]["name"],
        # primary line set: prior-season model (only model validated out-of-sample)
        "model": "M1 prior-season additive ratings (2025-26 official, 82 GP per team)",
        "poss": p25["poss"],
        "proj_score_a": p25["score_a"],
        "proj_score_b": p25["score_b"],
        "fair_spread_a": -p25["margin"],
        "fair_spread_b": p25["margin"],
        "fair_total": p25["total"],
        "fair_win_prob_a": prc["p_a"],
        "fair_win_prob_b": prc["p_b"],
        "fair_ml_a": prc["ml_a"],
        "fair_ml_b": prc["ml_b"],
        # secondary line set: current-season official ratings (small sample, uncalibrated)
        "m2_proj_score_a": p26["score_a"],
        "m2_proj_score_b": p26["score_b"],
        "m2_fair_spread_a": -p26["margin"],
        "m2_fair_total": p26["total"],
        "m2_fair_ml_a": None,
        "m2_fair_ml_b": None,
        # unverified fields, deliberately blank
        "market_spread_a": None,
        "market_total": None,
        "market_ml_a": None,
        "market_ml_b": None,
        "home_court_adjustment": None,
        "edge_vs_market": None,
        "prop_fair_line_pts_a": None,
        "prop_fair_line_pts_b": None,
        "unverified": ["market_spread_a", "market_total", "market_ml_a", "market_ml_b",
                       "home_court_adjustment", "edge_vs_market",
                       "m2_fair_ml_a", "m2_fair_ml_b",
                       "prop_fair_line_pts_a", "prop_fair_line_pts_b"],
        "leader_a": g["leader_a"],
        "leader_a_ppg": g["ppg_a"],
        "leader_a_rpg": g["rpg_a"],
        "leader_a_apg": g["apg_a"],
        "leader_b": g["leader_b"],
        "leader_b_ppg": g["ppg_b"],
        "leader_b_rpg": g["rpg_b"],
        "leader_b_apg": g["apg_b"],
        "sources": [SRC["adv_2025"], SRC["adv_2026"], SRC["games_1104"], SRC["glossary"],
                    SRC["games_1023"], SRC["games_1028"]],
        "game_url": g["game_url"],
        "source": SRC["games_1104"],
    })

meta = {
    "retrieved_utc": "2026-11-02",
    "league_avg_2025_26": L25,
    "league_avg_2026_27": L26,
    "sigma_residual_margin": SIGMA,
    "sigma_train_bias": TRAIN_BIAS,
    "train_games": len(TRAIN),
    "holdout_games": len(HOLDOUT),
    "settled_games_total": len(SETTLED),
    "slate_games": len(SLATE),
    "formulas": [
        "L = (mean(OffRtg) + mean(DefRtg)) / 2 over the 30 official team rows of one season",
        "P = (PACE_a + PACE_b) / 2",
        "E_a = OffRtg_a + DefRtg_b - L ; E_b = OffRtg_b + DefRtg_a - L",
        "S_a = E_a * P / 100 ; S_b = E_b * P / 100",
        "fair_spread_a = -(S_a - S_b) ; fair_total = S_a + S_b",
        "sigma = sd( (actual margin) - (projected margin) ) over TRAIN settled games only",
        "p_a = Phi( (S_a - S_b) / sigma ) ; fair American odds from p (zero margin)",
    ],
    "sources": [SRC["adv_2025"], SRC["adv_2026"], SRC["glossary"], SRC["games_1104"],
                SRC["games_1023"], SRC["games_1024"], SRC["games_1026"], SRC["games_1028"],
                SRC["games_1030"], SRC["games_1031"], SRC["games_1101"]],
    "caveats": [
        "No home/away designation is asserted; per-game home-court adjustment is UNVERIFIED.",
        "No market or closing odds are available from free official NBA pages (IR-04); all market columns are blank.",
        "M2 (current-season) lines use only 4-7 games per team and have no out-of-sample calibration; their moneyline is blank.",
        "Fair prices are zero-margin model outputs, NOT sportsbook prices and NOT betting advice.",
    ],
}

write_json(DERIVED / "lines.json", {"meta": meta, "rows": lines})
write_json(DERIVED / "backtest.json", {
    "meta": meta,
    "train": TRAIN_M,
    "holdout": HOLDOUT_M,
    "all": ALL_M,
})

if __name__ == "__main__":
    print(f"league_avg 2025-26 = {L25:.4f}; 2026-27 = {L26:.4f}")
    print(f"sigma (train residual margin sd) = {SIGMA:.4f}; train bias = {TRAIN_BIAS:.4f}")
    print(f"train n={TRAIN_M['n']}, holdout n={HOLDOUT_M['n']}, total n={ALL_M['n']}")
    print(f"holdout winner accuracy = {fmt(HOLDOUT_M['winner_accuracy'])} "
          f"(p={fmt(HOLDOUT_M['binomial_p_two_sided_vs_0_5'],4)}, "
          f"CI {fmt(HOLDOUT_M['accuracy_wilson_95ci'][0])}..{fmt(HOLDOUT_M['accuracy_wilson_95ci'][1])})")
    print(f"holdout margin MAE = {fmt(HOLDOUT_M['margin_mae'])}, total MAE = {fmt(HOLDOUT_M['total_mae'])}")
    print(f"wrote {len(lines)} lines -> data/derived/lines.json")

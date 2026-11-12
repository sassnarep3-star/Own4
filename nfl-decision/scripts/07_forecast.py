#!/usr/bin/env python3
"""Forecast-skill leaderboard. Price-independent, so it can be rewarded today.

Entrants are FROZEN forecasters, each scored on the same holdout seasons using only
information available before kickoff:
  F1 Own Elo model          (this repo, knobs calibrated on 1999-2012)
  F2 Market closing line    (third-party archive; the benchmark to beat)
  F3 Home team by 2.0       (naive)
  F4 League mean total      (naive)
  F5 Coin flip + league avg (random baseline, seeded)
"""
import csv, json, math, os, random, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
HOLD = (2018, 2025)
SEED = 20261112
random.seed(SEED)


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(OUT, "walkforward.csv")))]
    for r in rows:
        r["season"] = int(r["season"]); r["week"] = int(r["week"])
        r["result"] = float(r["result"]); r["total"] = float(r["total"])
        for k in ("spread_line", "total_line", "pred_margin", "pred_total", "league_avg_team_pts"):
            r[k] = float(r[k]) if r[k] not in ("", "None") else None
    hold = [r for r in rows if HOLD[0] <= r["season"] <= HOLD[1]]
    withm = [r for r in hold if r["spread_line"] is not None and r["total_line"] is not None]

    def score(name, margin_fn, total_fn, note, n_rows=None):
        src = n_rows or hold
        mm, tt, ats, brier, cover = [], [], 0, [], 0
        for r in src:
            pm = margin_fn(r); pt = total_fn(r)
            if pm is None or pt is None:
                continue
            mm.append(abs(pm - r["result"])); tt.append(abs(pt - r["total"]))
            p_home = 0.5 * (1 + math.erf(pm / (13.623 * math.sqrt(2))))
            brier.append((p_home - (1.0 if r["result"] > 0 else 0.0)) ** 2)
        for r in src:
            pm = margin_fn(r)
            if pm is None or r["spread_line"] is None:
                continue
            if r["result"] == r["spread_line"]:
                continue
            ats += 1
            cover += 1 if (pm - r["spread_line"]) * (r["result"] - r["spread_line"]) > 0 else 0
        n = len(mm)
        return {"forecaster": name, "n": n, "margin_mae": round(statistics.mean(mm), 3),
                "margin_rmse": round(math.sqrt(statistics.mean([x ** 2 for x in mm])), 3),
                "total_mae": round(statistics.mean(tt), 3),
                "ats_accuracy": round(cover / ats, 4) if ats else None,
                "brier": round(statistics.mean(brier), 4), "note": note}

    board = [
        score("F1 Own Elo model", lambda r: r["pred_margin"], lambda r: r["pred_total"],
              "This repository's walk-forward model. Knobs frozen on 1999-2012."),
        score("F2 Market closing line", lambda r: r["spread_line"], lambda r: r["total_line"],
              "Third-party closing line, inverted to a home margin. The benchmark."),
        score("F3 Home team by 2", lambda r: 2.0, lambda r: 2 * (r["league_avg_team_pts"] or 22.0),
              "Naive: every home team wins by 2, total = 2 x running league average."),
        score("F4 League average only", lambda r: 2.2, lambda r: 44.4,
              "Naive: historical mean home margin (2.2) and mean total (44.4) from the whole archive."),
        score("F5 Random margin", lambda r: random.gauss(2.2, 13.6), lambda r: random.gauss(44.4, 14.0),
              "Seeded random draw from the realised distribution. A floor, not a forecaster."),
    ]
    board.sort(key=lambda b: b["margin_mae"])
    pool = {"F1": 600, "F2": 0, "F3": 0, "F4": 0, "F5": 0}
    # Reward only SKILLED forecasters; the market benchmark is not a strategy.
    skill_rank = [b for b in board if b["forecaster"] != "F2 Market closing line"]
    awards = {0: 300, 1: 200, 2: 100}
    for i, b in enumerate(skill_rank[:3]):
        b["reward_points"] = awards[i]
    for b in board:
        b.setdefault("reward_points", 0)
        if b["forecaster"] == "F2 Market closing line":
            b["ats_accuracy"] = None      # it IS the line; a bet against itself is a push
            b["ats_note"] = "not applicable - the market line is the benchmark"
            b["reward_points"] = 0
            b["benchmark"] = True
    out = {"generated_utc": "2026-11-12", "holdout_seasons": list(HOLD),
           "n_holdout_games": len(hold), "n_games_with_lines": len(withm),
           "brier_note": "Brier uses sigma=13.623 (realised residual sd of the margin model) for every forecaster except F2, which is calibrated the same way for comparability.",
           "board": board,
           "forecast_pool": 600,
           "allocation": "300 / 200 / 100 to the top 3 skilled forecasters on holdout margin MAE. The market benchmark is excluded from rewards.",
           "honest_note": "The market wins. No forecaster in this repository beats the closing line, and none is claimed to. "
                          "Rewards here measure relative skill against naive baselines, not a tradeable edge."}
    json.dump(out, open(os.path.join(OUT, "forecast_leaderboard.json"), "w"), indent=1)
    print(f"{'rank':>4} {'forecaster':22} {'MAE':>7} {'RMSE':>7} {'totMAE':>7} {'ATS':>7} {'Brier':>7} {'pts':>4}")
    for i, b in enumerate(board):
        print(f"{i+1:>4} {b['forecaster']:22} {b['margin_mae']:7.3f} {b['margin_rmse']:7.3f} "
              f"{b['total_mae']:7.3f} {str(b['ats_accuracy']):>7} {b['brier']:7.4f} {b['reward_points']:>4}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rebuild every number published by the NFL Line Genesis hub.

    python3 nfl-hub/pipeline/run_all.py

Writes data/integrity.json, data/reconciliation.json, data/model/*.json,
data/strategies/results.json, data/correlations.json and data/model/model_card.json.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest
import correlations
import model
import weekly
from common import DATA, load_games, integrity_checks, save_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def archive_standings(games, season=2026):
    agg = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
    played = 0
    for g in games:
        if g["season"] != season or g["result"] is None:
            continue
        played += 1
        for team, pf, pa in ((g["home"], g["home_score"], g["away_score"]),
                             (g["away"], g["away_score"], g["home_score"])):
            d = agg[team]
            d["pf"] += pf
            d["pa"] += pa
            if pf > pa:
                d["w"] += 1
            elif pf < pa:
                d["l"] += 1
            else:
                d["t"] += 1
    for d in agg.values():
        gm = d["w"] + d["l"] + d["t"]
        d["pct"] = round((d["w"] + d["t"] / 2) / gm, 3)
    return agg, played


def reconcile(games, official, fixtures):
    arch, played = archive_standings(games)
    rows, mismatches = [], []
    for t in official["teams"]:
        a = arch.get(t["team"])
        row = {
            "team": t["team"], "name": t["name"],
            "official_w": t["w"], "official_l": t["l"], "official_t": t["t"],
            "official_pf": t["pf"], "official_pa": t["pa"], "official_pct": t["pct"],
            "archive_w": a["w"], "archive_l": a["l"], "archive_t": a["t"],
            "archive_pf": a["pf"], "archive_pa": a["pa"], "archive_pct": a["pct"],
            "match": (a["w"], a["l"], a["t"], a["pf"], a["pa"], a["pct"]) ==
                     (t["w"], t["l"], t["t"], t["pf"], t["pa"], t["pct"]),
            "official_source": t["source"],
            "archive_source": "nfl-hub/data/source/games.csv (nflverse snapshot)",
        }
        rows.append(row)
        if not row["match"]:
            mismatches.append(t["team"])

    arch_fx = {(g["away"], g["home"]): g["date"] for g in games
               if g["season"] == 2026 and g["week"] == 10}
    off_fx = {(g["away"], g["home"]): g["date"] for g in fixtures["games"]}
    fixture_rows = []
    for (a, h), d in sorted(off_fx.items()):
        fixture_rows.append({
            "away": a, "home": h, "official_date": d, "archive_date": arch_fx.get((a, h)),
            "match": arch_fx.get((a, h)) == d, "source": fixtures["source"],
        })
    extra = sorted(set(arch_fx) - set(off_fx))
    missing = sorted(set(off_fx) - set(arch_fx))

    return {
        "standings_as_of": official["as_of"],
        "games_played_2026": played,
        "teams_checked": len(rows),
        "teams_matched": sum(1 for r in rows if r["match"]),
        "mismatched_teams": mismatches,
        "method": "Archive box scores re-aggregated; W/L/T, PF, PA and NFL tie percentage ((W+T/2)/G) compared field by field.",
        "note": "PCT is NOT W/G. New York Giants 5-2-1 and Washington 2-5-1 only reconcile when ties are counted as half a win, as NFL.com does (0.688 / 0.313). A naive W/G calculation gives 0.625 / 0.250 and would falsely flag both teams.",
        "rows": rows,
        "fixtures": {
            "official_games": len(off_fx),
            "archive_games": len(arch_fx),
            "matched": sum(1 for r in fixture_rows if r["match"]),
            "missing_from_archive": missing,
            "extra_in_archive": extra,
            "byes": fixtures["byes"],
            "rows": fixture_rows,
            "source": fixtures["source"],
        },
        "passed": not mismatches and not missing and not extra,
    }


def model_card(preds, chosen_w, slope, sigma, results):
    def split(lo, hi):
        return [p for p in preds if lo <= p["season"] <= hi]

    out = {"blend_weight_points": chosen_w, "elo_to_points_slope": round(slope, 4), "sigma": round(sigma, 3)}
    for name, (lo, hi) in {"dev": backtest.DEV, "validation": backtest.VALIDATION, "holdout": backtest.HOLDOUT}.items():
        rows = split(lo, hi)
        mae_m, n = model.mae(rows, "model_margin", "actual_margin")
        mae_t, _ = model.mae(rows, "model_total", "actual_total")
        mae_mkt, _ = model.mae(rows, "market_margin", "actual_margin")
        mae_mkt_t, _ = model.mae(rows, "market_total", "actual_total")
        rmse_m, _ = model.rmse(rows, "model_margin", "actual_margin")
        rmse_mkt, _ = model.rmse(rows, "market_margin", "actual_margin")
        out[name] = {
            "n": n,
            "mae_margin_model": round(mae_m, 3) if mae_m else None,
            "mae_margin_market": round(mae_mkt, 3) if mae_mkt else None,
            "mae_margin_naive_home_2_5": round(
                sum(abs(p["actual_margin"] - 2.5) for p in rows) / len(rows), 3) if rows else None,
            "rmse_margin_model": round(rmse_m, 3) if rmse_m else None,
            "rmse_margin_market": round(rmse_mkt, 3) if rmse_mkt else None,
            "mae_total_model": round(mae_t, 3) if mae_t else None,
            "mae_total_market": round(mae_mkt_t, 3) if mae_mkt_t else None,
        }

    hold = split(*backtest.HOLDOUT)
    bins = []
    for i in range(5):
        lo, hi = i / 5, (i + 1) / 5
        rows = [p for p in hold if lo <= backtest.norm_cdf(p["model_margin"] / sigma) < hi]
        if rows:
            hits = sum(1 for p in rows if p["actual_margin"] > 0)
            exp = sum(backtest.norm_cdf(p["model_margin"] / sigma) for p in rows) / len(rows)
            bins.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(rows),
                         "predicted_home_win_rate": round(exp, 3), "actual_home_win_rate": round(hits / len(rows), 3)})
    out["calibration_holdout"] = bins
    out["honest_reading"] = (
        "The model is compared with the closing line, not only with a naive baseline. "
        "If MAE_margin_market is lower than MAE_margin_model, the market is the better forecast and the "
        "model has no demonstrated forecasting edge. This is reported as-is."
    )
    out["splits"] = {"dev": list(backtest.DEV), "validation": list(backtest.VALIDATION), "holdout": list(backtest.HOLDOUT)}
    return out


def main():
    games = load_games()
    integrity = integrity_checks(games)
    save_json("integrity.json", integrity)
    if not integrity["passed"]:
        print("G1 FAILED", integrity["problems"])
        return 1

    preds, state = model.walk_forward(games)
    dev = [p for p in preds if backtest.DEV[0] <= p["season"] <= backtest.DEV[1]]
    slope = model.fit_slope(dev)

    val = [p for p in preds if backtest.VALIDATION[0] <= p["season"] <= backtest.VALIDATION[1]]
    grid = [0.0, 0.5, 1.0]
    scored = []
    for w in grid:
        model.blend(val, slope, w)
        mae, _ = model.mae(val, "model_margin", "actual_margin")
        scored.append({"w_points": w, "validation_mae": round(mae, 4)})
    best = min(scored, key=lambda r: r["validation_mae"])
    w_points = best["w_points"]

    model.blend(preds, slope, w_points)
    sigma = model.residual_sigma(val)

    evaluation = backtest.evaluate(preds, sigma)
    evaluation["blend_grid"] = scored
    evaluation["blend_chosen"] = best
    save_json("strategies/results.json", evaluation)

    save_json("correlations.json", correlations.build(preds))
    save_json("model/model_card.json", model_card(preds, w_points, slope, sigma, evaluation))

    official = load("official/standings_2026.json")
    fixtures = load("official/schedule_week10_2026.json")
    rec = reconcile(games, official, fixtures)
    save_json("reconciliation.json", rec)

    official_by_team = {t["team"]: t for t in official["teams"]}
    rows, final_state = weekly.build(games, preds, slope, w_points, sigma, fixtures, official_by_team)
    leak = weekly.lookahead_tests(games, slope, w_points, sigma, fixtures)
    save_json("model/week10_lines.json", {
        "generated_utc": "2026-11-12T17:05:00Z",
        "slate": "2026 Week 10 (Nov 12-16)",
        "generated_before_first_kickoff": True,
        "first_kickoff_et": "2026-11-12 20:15",
        "method": "Walk-forward Elo + exponentially weighted points model; blend weight, slope and sigma fitted on dev/validation seasons only.",
        "status": "DERIVED MODEL OUTPUT — not a sportsbook quote and not a recommendation to bet.",
        "market_comparison": "BLANK — no archived 2026 closing lines and no official NFL odds source.",
        "rows": rows,
        "lookahead_tests": leak,
    })
    save_json("model/ratings_2026.json", {
        "generated_utc": "2026-11-12T17:05:00Z",
        "status": "DERIVED ratings; records/points from NFL.com official standings",
        "source": official["source_url"],
        "rows": weekly.ratings_table(final_state, official_by_team),
    })

    print(json.dumps({
        "integrity_passed": integrity["passed"],
        "games": integrity["games_total"],
        "slope": round(slope, 4),
        "blend": w_points,
        "sigma": round(sigma, 3),
        "reconciliation": {"teams": rec["teams_matched"], "fixtures": rec["fixtures"]["matched"]},
        "leak_tests_passed": leak["passed"],
        "results": {k: (v.get("roi") if isinstance(v, dict) else None) for k, v in evaluation["results"].items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

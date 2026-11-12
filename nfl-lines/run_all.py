#!/usr/bin/env python3
"""Run every stage of the NFL line-origination lab and write data/derived/*.json.

Stages: load -> official cross-verification -> walk-forward forecast -> strategies ->
validation gates -> correlations -> luck decomposition -> leaderboard -> Week 10 own
lines -> injury/deficiency read.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))

import backtest as B          # noqa: E402
import calibration as CAL     # noqa: E402
import correlations as CR     # noqa: E402
import dataset as D           # noqa: E402
import evaluate as EV         # noqa: E402
import injuries as INJ        # noqa: E402
import model as M             # noqa: E402

DERIVED = D.DERIVED


def main():
    os.makedirs(DERIVED, exist_ok=True)
    params = M.load_params()
    games = D.normalise_archive(D.load_archive())
    reg = B.prepare(games)

    print("[1/8] official cross-verification")
    verification = D.verify_against_official(games)
    standings = D.load_json(D.OFFICIAL + "/standings_2026.json")
    integrity = D.integrity_checks(games, standings)
    print("      spot-check %d/%d match; %d/%d integrity checks pass"
          % (verification["matched"], verification["games_compared"],
             sum(1 for c in integrity if c["passed"]), len(integrity)))
    for c in integrity:
        if not c["passed"]:
            print("      FAIL", c["id"], c["detail"])

    print("[2/8] walk-forward forecast")
    rows = B.run(reg, params)
    print("      %d forecast rows, seasons %d-%d"
          % (len(rows), min(r["season"] for r in rows), max(r["season"] for r in rows)))

    print("[3/8] strategies")
    strategies = EV.build_strategies(rows, params)
    strategies.update(EV.build_parlays(rows, params))
    strategies.update(EV.build_sgp(rows, params))
    print("      %d strategies" % len(strategies))

    print("[4/8] gates, luck decomposition and leaderboard")
    conf = params["evaluation"]["confirmation_seasons"]
    recs = EV.evaluate_strategies(strategies, params, conf)
    board = EV.leaderboard(recs)
    print("      %d reward-eligible" % sum(1 for b in board if b["eligible_for_reward"]))

    print("[5/8] correlations, calibration and base rates")
    cors = CR.compute(rows)
    base = CR.base_rates(rows)
    keys = CR.key_numbers(rows, -21, 21)
    calib = CAL.compute(rows)

    print("[6/8] Week 10 own lines")
    upcoming = forecast_upcoming(reg, params)
    print("      %d games" % len(upcoming))

    print("[7/8] injury / unit deficiency")
    inj = INJ.build()
    inj_rows = INJ.deficiency_table(inj)

    print("[8/8] writing derived data")
    D.dump_json(os.path.join(DERIVED, "verification.json"), {
        "official_score_spotcheck": verification,
        "integrity_checks": integrity,
    })
    D.dump_json(os.path.join(DERIVED, "walkforward_forecasts.json"), rows)
    D.dump_json(os.path.join(DERIVED, "strategy_results.json"), recs)
    D.dump_json(os.path.join(DERIVED, "leaderboard.json"), board)
    D.dump_json(os.path.join(DERIVED, "correlations.json"), {
        "correlations": cors, "base_rates": base, "margin_distribution": keys,
        "calibration": calib})
    D.dump_json(os.path.join(DERIVED, "own_lines_week10.json"), upcoming)
    D.dump_json(os.path.join(DERIVED, "deficiency.json"),
                {"rows": inj_rows,
                 "teams": {k: {kk: vv for kk, vv in v.items()}
                           for k, v in inj["teams"].items()}})
    D.dump_json(os.path.join(DERIVED, "summary.json"), {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_games": len(rows),
        "seasons": sorted({r["season"] for r in rows}),
        "strategies": len(strategies),
        "reward_eligible": sum(1 for b in board if b["eligible_for_reward"]),
        "base_rates": base,
    })
    print("done")


def forecast_upcoming(reg, params):
    """Originate a line for every 2026 game that has no final score yet."""
    future = [g for g in reg if g["season"] == 2026 and g["margin"] is None]
    if not future:
        return []
    mm, tm = M.MarginModel(params["model"]), M.TotalModel(params["model"])
    all_teams = sorted({M.franchise(g["home"]) for g in reg} | {M.franchise(g["away"]) for g in reg})
    mm._ensure_index(all_teams)
    tm._ensure_index(all_teams)
    out = []
    for day in sorted({g["_ord"] for g in future}):
        train = [g for g in reg if g["_ord"] < day and g["margin"] is not None]
        cutoff = day - int(365.25 * 14)
        train = [g for g in train if g["_ord"] >= cutoff]
        mm.fit(train, day)
        tm.fit(train, day)
        if mm.coef is None or tm.coef is None:
            continue
        for g in [x for x in future if x["_ord"] == day]:
            ms = mm.predict(g)
            tt = tm.predict(g)
            if ms is None or tt is None:
                continue
            prob = mm.home_win_prob(g)
            out.append({
                "game_id": g["game_id"], "gameday": g["gameday"], "week": g["week"],
                "away": g["away"], "home": g["home"],
                "own_spread_line": round(ms, 2),
                "own_total_line": round(tt, 2),
                "own_home_team_total": round((tt + ms) / 2.0, 2),
                "own_away_team_total": round((tt - ms) / 2.0, 2),
                "own_home_win_prob": round(prob, 4),
                "own_home_moneyline": M.decimal_to_american(1.0 / prob) if prob > 0 else None,
                "own_away_moneyline": M.decimal_to_american(1.0 / (1.0 - prob)) if prob < 1 else None,
                "model_sigma_margin": round(mm.sigma, 3),
                "market_spread_line": g["spread_line"],
                "market_total_line": g["total_line"],
                "market_home_moneyline": g["home_moneyline"],
                "market_away_moneyline": g["away_moneyline"],
                "spread_edge": None if g["spread_line"] is None else round(ms - g["spread_line"], 2),
                "total_edge": None if g["total_line"] is None else round(tt - g["total_line"], 2),
                "home_rest": g["home_rest"], "away_rest": g["away_rest"],
                "roof": g["roof"], "surface": g["surface"],
            })
    return out


if __name__ == "__main__":
    main()

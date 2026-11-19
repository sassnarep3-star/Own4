"""Origination engine: ratings, correlations, originated lines, price snapshots,
leaderboard, availability graph, matchup matrix, snapshot ledger, per-team view.

All inputs are the official reads in ../data/*.json (2026-11-19). Model
parameters (home edge, spread-to-probability scale) are disclosed as model
parameters, not official facts. Market lines are blank: no official price
source exists. Nothing is inferred or filled in.
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

HOME_EDGE = 2.5        # model parameter (points), disclosed, not official
SPREAD_SCALE = 13.5    # model parameter: P(home) = Phi(spread / scale)
SNAP_UTC = "2026-11-19"


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    r = sxy / math.sqrt(sxx * syy)
    # t statistic, df = n-2
    t = r * math.sqrt((n - 2) / (1 - r * r)) if abs(r) < 1 else float("inf")
    return r, t, n


def main():
    standings = load("standings.json")
    schedule = load("schedule_week11.json")
    injuries = load("injuries_week11.json")
    results = load("results_week10.json")

    teams = {t["club"]: t for t in standings["teams"]}
    # integrity checks
    assert len(teams) == 32, "expected 32 clubs"
    for t in standings["teams"]:
        assert t["net"] == t["pf"] - t["pa"], f"NET identity failed for {t['club']}"
    sum_w = sum(t["w"] for t in standings["teams"])
    sum_l = sum(t["l"] for t in standings["teams"])
    sum_t = sum(t["t"] for t in standings["teams"])
    assert sum_w == sum_l, "W != L"
    n_games = (sum_w + sum_l + sum_t) // 2
    total_pf = sum(t["pf"] for t in standings["teams"])
    total_pa = sum(t["pa"] for t in standings["teams"])
    assert total_pf == total_pa, "PF != PA"
    league_mean_total = total_pf / n_games

    # ratings: NET per game (opponent-aware in aggregate from season PF/PA)
    ratings = {}
    for club, t in teams.items():
        g = t["w"] + t["l"] + t["t"]
        ratings[club] = {
            "club": club, "name": t["name"], "games": g,
            "net_per_game": round(t["net"] / g, 3),
            "pf_per_game": round(t["pf"] / g, 2),
            "pa_per_game": round(t["pa"] / g, 2),
            "pace_per_game": round((t["pf"] + t["pa"]) / g, 2),
        }

    # correlations from official standings numbers only, n published
    pf = [t["pf"] for t in standings["teams"]]
    pa = [t["pa"] for t in standings["teams"]]
    net = [t["net"] for t in standings["teams"]]
    w = [t["w"] for t in standings["teams"]]
    corrs = []
    for label, xs, ys in [
        ("PF vs PA", pf, pa),
        ("NET vs W", net, w),
        ("PF vs W", pf, w),
        ("PA vs W", pa, w),
        ("NET vs PF", net, pf),
    ]:
        r, t, n = pearson(xs, ys)
        corrs.append({"pair": label, "r": round(r, 4), "t": round(t, 3), "n": n,
                      "source": standings["source"]})

    # origination: side first, then total, then moneyline
    originated = []
    snapshots = []
    for fx in schedule["fixtures"]:
        a, h = fx["away"], fx["home"]
        ra, rh = ratings[a], ratings[h]
        spread = round((rh["net_per_game"] - ra["net_per_game"]) + HOME_EDGE, 2)
        p_home = round(phi(spread / SPREAD_SCALE), 4)
        # two total estimators, published side by side until one wins
        total_a = round((rh["pace_per_game"] + ra["pace_per_game"]) / 2, 2)
        total_b = round(league_mean_total + 0.5 * (rh["net_per_game"] + ra["net_per_game"]), 2)
        gap = round(total_a - total_b, 2)
        # moneyline from probability (American odds)
        if p_home > 0.5:
            ml_home = round(-100 * p_home / (1 - p_home))
        elif p_home < 0.5:
            ml_home = round(100 * (1 - p_home) / p_home)
        else:
            ml_home = 100
        ml_away = round(-100 * (1 - p_home) / p_home) if p_home < 0.5 else round(100 * p_home / (1 - p_home))
        inputs = {
            "home_net_per_game": rh["net_per_game"], "away_net_per_game": ra["net_per_game"],
            "home_edge_pts": HOME_EDGE, "spread_scale": SPREAD_SCALE,
            "home_pace": rh["pace_per_game"], "away_pace": ra["pace_per_game"],
            "league_mean_total": round(league_mean_total, 2),
            "injury_features": "none in v1 (blocked: no verified availability features)",
        }
        originated.append({
            "game_id": fx["game_id"], "away": a, "home": h, "date": fx["date"],
            "side": {"fair_line_home": spread, "market_line": None, "difference": None,
                     "p_home_win": p_home},
            "total": {"estimator_a": total_a, "estimator_b": total_b, "gap_a_minus_b": gap,
                      "market_line": None, "difference": None},
            "moneyline": {"fair_home": ml_home, "fair_away": ml_away,
                          "market_line": None, "difference": None},
            "inputs": inputs,
            "source": standings["source"],
        })
        for market, fair in [("side", spread), ("total", total_a), ("moneyline", ml_home)]:
            snapshots.append({
                "snapshot_utc": SNAP_UTC, "game_id": fx["game_id"],
                "away": a, "home": h, "date": fx["date"], "market_type": market,
                "fair_line": fair, "opener": None, "closer": None,
                "opener_source": None, "closer_source": None,
                "status": "no_official_price",
                "source": "https://www.nfl.com/games",
            })

    # per-team injury view: net injury count, DNP count, Out count (Thursday only)
    per_team = []
    for club in sorted(teams):
        rows = [r for r in injuries["rows"] if r["club"] == club]
        per_team.append({
            "club": club, "name": teams[club]["name"],
            "injury_rows": len(rows),
            "dnp": sum(1 for r in rows if r["practice"] == "DNP"),
            "lp": sum(1 for r in rows if r["practice"] == "LP"),
            "fp": sum(1 for r in rows if r["practice"] == "FP"),
            "out_designated": sum(1 for r in rows if r["game_status"] == "Out"),
            "questionable": sum(1 for r in rows if r["game_status"] == "Questionable"),
            "replacements_named": None,  # blank: no depth source (R-06)
            "source": injuries["source"],
        })

    # availability graph: expected (Out designations) vs actual (blank)
    graph = []
    for fx in schedule["fixtures"]:
        for club in (fx["away"], fx["home"]):
            outs = [r["player"] for r in injuries["rows"]
                    if r["club"] == club and r["game_status"] == "Out"]
            graph.append({
                "game_id": fx["game_id"], "club": club,
                "expected_out": outs, "actual_starters": None,
                "actual_source": None,
                "note": "Actual starters unknown: no Game Book / snap source (R-25).",
            })

    # matchup deficiency matrix: structure only, cells blank (blocked R-44)
    matrix = []
    for fx in schedule["fixtures"]:
        matrix.append({
            "game_id": fx["game_id"], "away": fx["away"], "home": fx["home"],
            "wr1_vs_cb": None, "edge1_vs_ot": None, "notes": "Blocked: no verified depth order (R-06).",
        })

    # snapshot ledger
    ledger = [
        {"capture": "2026-11-18T23:49:17Z", "source": injuries["source"],
         "sha256": "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b",
         "rows": 242, "origin": "repo-carried raw capture (nfl-readiness-register/snapshots/2026-11-18/)",
         "conflict_flags": "none recorded"},
        {"capture": "2026-11-19 (date only; no clock time)", "source": injuries["source"],
         "sha256": None, "rows": len(injuries["rows"]),
         "origin": "this session's transcription (no raw file)",
         "conflict_flags": "F-02 Lions designation disagreement; F-11 no clock time"},
    ]

    # weekly diff: today vs prior capture (cross-parser, disclosed)
    diff = {
        "prior_rows": 242, "current_rows": len(injuries["rows"]),
        "delta_rows": len(injuries["rows"]) - 242,
        "note": "Cross-parser comparison (prior capture parsed by peer session; today transcribed by this session). Delta is structural, not a per-player surprise measurement.",
    }

    # leaderboard: signal vs staking, divisions, controls
    leaderboard = {
        "graded_games": 0,
        "note": "0 graded games (Week 11 unplayed). Signal and staking are separate columns; staking is blank (no prices). 0 of 6 strategies qualify; 0 rewards.",
        "rows": [
            {"strategy": "ST-01 shadow singles", "division": "singles",
             "signal_brier_skill": None, "staking": None, "qualifies": "no", "rewards": 0},
            {"strategy": "ST-02 totals A", "division": "singles",
             "signal_brier_skill": None, "staking": None, "qualifies": "no", "rewards": 0},
            {"strategy": "ST-03 totals B", "division": "singles",
             "signal_brier_skill": None, "staking": None, "qualifies": "no", "rewards": 0},
            {"strategy": "ST-04 two-leg parlay", "division": "game parlays",
             "signal_brier_skill": None, "staking": None, "qualifies": "no (joint-evidence gate)", "rewards": 0},
            {"strategy": "ST-05 same-game parlay", "division": "same-game parlays",
             "signal_brier_skill": None, "staking": None, "qualifies": "no (joint-evidence gate)", "rewards": 0},
            {"strategy": "ST-06 prop combo", "division": "prop combos",
             "signal_brier_skill": None, "staking": None, "qualifies": "no (joint-evidence gate)", "rewards": 0},
        ],
        "controls": [
            {"control": "random picks", "brier_skill": None, "note": "published beside shadow record; empirical value awaits graded games"},
            {"control": "favorites only", "brier_skill": None, "note": "published beside shadow record; empirical value awaits graded games"},
        ],
    }

    # removal-of-luck panel (structural until graded games exist)
    luck = {
        "graded_games": 0,
        "brier_skill": None,
        "permutation_p": None,
        "note": "Panel published with controls and pre-registered floors; values are blank until Week 11 finals are graded. No luck claim is made.",
    }

    out = {
        "integrity": {"sum_w": sum_w, "sum_l": sum_l, "sum_t": sum_t,
                      "n_games_implied": n_games, "total_pf": total_pf,
                      "total_pa": total_pa, "league_mean_total": round(league_mean_total, 2),
                      "week10_finals_verified": len(results["games"])},
        "ratings": ratings, "correlations": corrs, "originated": originated,
        "price_snapshots": snapshots, "per_team": per_team, "availability_graph": graph,
        "matchup_matrix": matrix, "snapshot_ledger": ledger, "weekly_diff": diff,
        "leaderboard": leaderboard, "luck_panel": luck,
    }
    with open(DATA / "derived.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"derived: {n_games} games implied, mean total {league_mean_total:.2f}, "
          f"{len(originated)} originated, {len(snapshots)} snapshots, "
          f"{len(injuries['rows'])} injury rows")


if __name__ == "__main__":
    main()

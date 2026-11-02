"""Run the full pipeline: fit on dev, evaluate once on the frozen holdout, apply gates, write JSON for the site.
Usage: python research/run_all.py   (set NBA_DATA_DIR to reuse a local clone of the dataset)"""
import json, os, sys, subprocess, datetime
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import prep, engine
from config import *

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
rng = np.random.default_rng(SEED)


def leakage_perturbation_test():
    """Altering a game's OWN result must not change that game's pre-game features (but must change later games')."""
    base = prep.build_games(prep.load_teams())
    row = base[base["season"] == "2015-16"].iloc[400]
    gid = row["game_id"]; hid, aid = row["h_team_id"], row["a_team_id"]
    def mut(df):
        df = df.copy(); m = df["game_id"] == gid; df.loc[m, "pts"] = df.loc[m, "pts"] + 40; return df
    alt = prep.build_games(prep.load_teams(mutate=mut))
    cols = ["raw_total", "f_t1", "f_t2", "raw_spread", "f_m1", "h_pts_s", "h_pts_ew", "a_margin_ew", "league_drift"]
    a = base[base["game_id"] == gid][cols].iloc[0]; b = alt[alt["game_id"] == gid][cols].iloc[0]
    same_own = bool(np.allclose(a.values.astype(float), b.values.astype(float), equal_nan=True))
    later = base[(base["date"] > row["date"]) & ((base["h_team_id"] == hid) | (base["a_team_id"] == hid)) & (base["season"] == "2015-16")].iloc[0]["game_id"]
    a2 = base[base["game_id"] == later][cols].iloc[0]; b2 = alt[alt["game_id"] == later][cols].iloc[0]
    changed_later = not np.allclose(a2.values.astype(float), b2.values.astype(float), equal_nan=True)
    team_res = dict(game_id=int(gid), own_features_unchanged=same_own, later_game_features_changed=changed_later, passed=bool(same_own and changed_later))
    # player-level perturbation
    t0 = prep.load_teams(); g0 = prep.build_games(t0)
    pb = prep.load_players(t0, g0)
    k = pb[(pb["season"] == "2015-16") & (pb["gp_before"] > 30)].iloc[500]
    pid, pgid, pdate = k["pid"], k["game_id"], k["date"]
    def pmut(df):
        df = df.copy(); m = (df["pid"] == pid) & (df["game_id"] == pgid); df.loc[m, "pts"] = df.loc[m, "pts"] + 30; return df
    pa = prep.load_players(t0, g0, mutate=pmut)
    pc = ["pts_s", "pts_ew", "f_pts", "mins_s", "f_mins", "pra_s", "f_pra"]
    x = pb[(pb["pid"] == pid) & (pb["game_id"] == pgid)][pc].iloc[0].astype(float); y = pa[(pa["pid"] == pid) & (pa["game_id"] == pgid)][pc].iloc[0].astype(float)
    nxt = pb[(pb["pid"] == pid) & (pb["date"] > pdate) & (pb["season"] == "2015-16")].iloc[0]["game_id"]
    x2 = pb[(pb["pid"] == pid) & (pb["game_id"] == nxt)][pc].iloc[0].astype(float); y2 = pa[(pa["pid"] == pid) & (pa["game_id"] == nxt)][pc].iloc[0].astype(float)
    p_same = bool(np.allclose(x.values, y.values, equal_nan=True)); p_chg = not np.allclose(x2.values, y2.values, equal_nan=True)
    player_res = dict(player_id=int(pid), game_id=int(pgid), own_features_unchanged=p_same, later_game_features_changed=p_chg, passed=bool(p_same and p_chg))
    return dict(team=team_res, player=player_res, passed=bool(team_res["passed"] and player_res["passed"]))


def main():
    t = prep.load_teams(); games = prep.build_games(t); players = prep.load_players(t, games)
    perturb = leakage_perturbation_test()
    print('perturbation test:', perturb)
    rows, legs, extras = engine.run_singles(games, players, rng)
    rows = engine.gate_singles(rows, perturb['passed'])
    control = engine.proxy_vs_naive(games, players)
    placebo = engine.placebo_calibration(rows, games, players, rng)
    # parlay legs: only from non-control strategies whose dev-selected trial is Holm-significant AND beats the proxy in MAE
    elig = sorted({x["strategy"] for x in rows if x["selected_on_dev"] and not x["control"] and x["gates"]["G3"] and x["p_holm"] < ALPHA})
    print("parlay-eligible leg strategies:", elig)
    parlays = engine.evaluate_parlays(engine.build_parlays(legs[legs["strat"].isin(elig)]))
    rows = engine.assign_tiers(rows); parlays = engine.assign_tiers(parlays)
    corr = engine.compute_correlations(extras, games)
    # signal-vs-outcome correlations (information coefficients), holdout
    seen = set()
    for r in rows:
        if r["strategy"] in seen: continue
        seen.add(r["strategy"])
        corr["signal_vs_outcome"].append(dict(strategy=r["strategy"], name=r["name"], n=r["n_rows"], r=r["ic"], lo=r["ic_lo"], hi=r["ic_hi"]))
    meta = dict(
        generated=datetime.date(2026, 11, 2).isoformat(), dataset_repo=DATASET_REPO, dataset_commit=DATASET_COMMIT,
        dev_seasons=DEV_SEASONS, holdout_seasons=HOLDOUT_SEASONS, n_games=int(len(games)), n_player_games=int(len(players)),
        n_games_dev=int(games["season"].isin(DEV_SEASONS).sum()), n_games_holdout=int(games["season"].isin(HOLDOUT_SEASONS).sum()),
        leg_decimal=LEG_DECIMAL, breakeven=BREAKEVEN, alpha=ALPHA, quantiles=QUANTILES, seed=SEED,
        trials_singles=len(rows), trials_parlays=len(parlays), parlay_leg_strategies=elig,
        gate_params=dict(min_bets_single=MIN_BETS_SINGLE, min_bets_parlay=MIN_BETS_PARLAY, side_balance=SIDE_BALANCE,
                         parlay_max_abs_rho=PARLAY_MAX_ABS_RHO, parlay_max_legs=PARLAY_MAX_LEGS),
        placebo=placebo, leakage_perturbation=perturb, proxy_vs_naive_control=control, proxy_weight=engine.PROXY_W)
    json.dump(dict(meta=meta, singles=rows, parlays=parlays), open(f"{OUT}/research_results.json", "w"), indent=1, default=float)
    json.dump(dict(meta=dict(dataset_commit=DATASET_COMMIT, holdout=HOLDOUT_SEASONS, dev=DEV_SEASONS), **corr), open(f"{OUT}/correlations_computed.json", "w"), indent=1, default=float)
    print("singles trials:", len(rows), "passed all gates:", sum(r["passed_all"] for r in rows))
    print("parlay trials:", len(parlays), "passed all gates:", sum(r["passed_all"] for r in parlays))
    print("placebo:", placebo)


if __name__ == "__main__":
    main()

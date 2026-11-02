"""Load box-score data and build leak-free pre-game features.

Every feature for a game is computed from games strictly BEFORE it (same season), via shift(1).
Data: third-party GitHub mirror of NBA.com box scores (see config.py); NOT an official source —
spot-check results are published on the site's Audit page.
"""
import os, subprocess
import numpy as np, pandas as pd
from config import *

CACHE = os.environ.get("NBA_DATA_DIR", os.path.join(os.path.dirname(__file__), ".cache", "nba-data"))


def ensure_dataset():
    if not os.path.isdir(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        subprocess.check_call(["git", "clone", "-q", DATASET_REPO, CACHE])
    subprocess.check_call(["git", "-C", CACHE, "checkout", "-q", DATASET_COMMIT])
    return CACHE


def load_teams(mutate=None):
    d = ensure_dataset()
    t = pd.read_csv(f"{d}/regular_season_totals_2010_2024.csv",
                    usecols=["SEASON_YEAR", "TEAM_ID", "TEAM_ABBREVIATION", "GAME_ID", "GAME_DATE", "MATCHUP",
                             "MIN", "FGA", "FTA", "OREB", "TOV", "PTS"])
    t.columns = ["season", "team_id", "abbr", "game_id", "date", "matchup", "min", "fga", "fta", "oreb", "tov", "pts"]
    if mutate is not None:
        t = mutate(t)
    t["date"] = pd.to_datetime(t["date"]).dt.normalize()
    t["home"] = t["matchup"].str.contains("vs.", regex=False)
    t["poss"] = t["fga"] + 0.44 * t["fta"] - t["oreb"] + t["tov"]
    o = t[["game_id", "team_id", "pts", "poss"]].rename(columns={"team_id": "opp_id", "pts": "opp_pts", "poss": "opp_poss"})
    t = t.merge(o, on="game_id")
    t = t[t["team_id"] != t["opp_id"]].copy()
    t["margin"] = t["pts"] - t["opp_pts"]
    t["pace"] = 48 * (t["poss"] + t["opp_poss"]) / 2 / (t["min"] / 5)
    t = t.sort_values(["team_id", "date", "game_id"]).reset_index(drop=True)
    g = t.groupby(["team_id", "season"], sort=False)
    t["rest"] = g["date"].diff().dt.days.fillna(7).clip(upper=7)
    t["b2b"] = (t["rest"] == 1).astype(float)
    t["gp_before"] = g.cumcount()
    for c in ["pts", "opp_pts", "margin", "pace"]:
        s = g[c].shift(1)
        t[f"{c}_s"] = s.groupby([t["team_id"], t["season"]]).expanding().mean().reset_index(level=[0, 1], drop=True)
        t[f"{c}_ew"] = g[c].transform(lambda x: x.shift(1).ewm(halflife=EWM_HALFLIFE_GAMES, min_periods=3).mean())
    return t


def build_games(t):
    h = t[t["home"]].add_prefix("h_")
    a = t[~t["home"]].add_prefix("a_")
    g = h.merge(a, left_on="h_game_id", right_on="a_game_id")
    g = g.rename(columns={"h_game_id": "game_id", "h_season": "season", "h_date": "date"})
    g = g[(g["h_gp_before"] >= MIN_TEAM_GAMES) & (g["a_gp_before"] >= MIN_TEAM_GAMES)].copy()
    g["total"] = g["h_pts"] + g["a_pts"]
    g["hmargin"] = g["h_pts"] - g["a_pts"]
    # league drift: trailing-14-day league mean total minus season-to-date mean total, using dates strictly before
    daily = g.groupby(["season", "date"]).agg(n=("total", "size"), s=("total", "sum")).reset_index().sort_values(["season", "date"])
    out = []
    for season, d in daily.groupby("season"):
        d = d.set_index("date")
        cs, cn = d["s"].cumsum().shift(1), d["n"].cumsum().shift(1)
        r14s = d["s"].rolling("14D", closed="left").sum()
        r14n = d["n"].rolling("14D", closed="left").sum()
        drift = (r14s / r14n) - (cs / cn)
        out.append(pd.DataFrame({"season": season, "date": d.index, "league_drift": drift.values}))
    g = g.merge(pd.concat(out), on=["season", "date"], how="left")
    g["league_drift"] = g["league_drift"].fillna(0.0)
    # model inputs
    g["raw_total"] = (g["h_pts_s"] + g["h_opp_pts_s"] + g["a_pts_s"] + g["a_opp_pts_s"]) / 2
    g["f_t1"] = (g["h_pts_ew"] + g["h_opp_pts_ew"] + g["a_pts_ew"] + g["a_opp_pts_ew"]) / 2 - g["raw_total"]
    g["f_t2"] = (g["h_pace_ew"] + g["a_pace_ew"]) / 2 - (g["h_pace_s"] + g["a_pace_s"]) / 2
    g["raw_spread"] = g["h_margin_s"] - g["a_margin_s"]
    g["f_m1"] = (g["h_margin_ew"] - g["a_margin_ew"]) - g["raw_spread"]
    g["f_restdiff"] = (g["h_rest"].clip(upper=4) - g["a_rest"].clip(upper=4))
    g["game_pace_exp"] = (g["h_pace_s"] + g["a_pace_s"]) / 2
    return g.dropna(subset=["raw_total", "f_t1", "f_t2", "raw_spread", "f_m1"]).reset_index(drop=True)


def load_players(t, games, mutate=None):
    d = ensure_dataset()
    cols = ["season_year", "game_date", "gameId", "matchup", "teamId", "personId", "personName",
            "minutes", "reboundsTotal", "assists", "points"]
    p = pd.concat([pd.read_csv(f"{d}/regular_season_box_scores_2010_2024_part_{i}.csv", usecols=cols) for i in (1, 2, 3)],
                  ignore_index=True)
    p.columns = ["season", "date", "game_id", "matchup", "team_id", "pid", "name", "min", "reb", "ast", "pts"]
    if mutate is not None:
        p = mutate(p)
    p["date"] = pd.to_datetime(p["date"]).dt.normalize()
    mm = p["min"].astype(str).str.extract(r"^(\d+):(\d+)$").astype(float)
    p["mins"] = mm[0] + mm[1] / 60
    p = p[p["mins"].fillna(0) > 0].copy()                      # DNP rows void (as books void non-participants)
    p["home"] = p["matchup"].str.contains("vs.", regex=False).astype(float)
    p["pra"] = p["pts"] + p["reb"] + p["ast"]
    p = p.sort_values(["pid", "date", "game_id"]).reset_index(drop=True)
    g = p.groupby(["pid", "season"], sort=False)
    p["gp_before"] = g.cumcount()
    for c in ["pts", "reb", "ast", "pra", "mins"]:
        sh = g[c].shift(1)
        p[f"{c}_s"] = sh.groupby([p["pid"], p["season"]]).expanding().mean().reset_index(level=[0, 1], drop=True)
    hl = {"pts": EWM_HALFLIFE_GAMES, "reb": EWM_HALFLIFE_GAMES, "ast": EWM_HALFLIFE_GAMES, "pra": EWM_HALFLIFE_GAMES, "mins": EWM_HALFLIFE_MIN}
    for c, h in hl.items():
        p[f"{c}_ew"] = g[c].transform(lambda x, h=h: x.shift(1).ewm(halflife=h, min_periods=3).mean())
    tm = t[["game_id", "team_id", "b2b", "opp_id"]].rename(columns={"b2b": "team_b2b"})
    p = p.merge(tm, on=["game_id", "team_id"], how="inner")
    gp = games[["game_id", "game_pace_exp", "total", "raw_total"]]
    p = p.merge(gp, on="game_id", how="inner")                # restricts to games where both teams have >=10 prior games
    p = p[(p["gp_before"] >= MIN_PLAYER_GAMES) & (p["mins_s"] >= MIN_PLAYER_MPG)].copy()
    p["f_mins"] = p["mins_ew"] - p["mins_s"]
    for c in ["pts", "reb", "ast", "pra"]:
        p[f"f_{c}"] = p[f"{c}_ew"] - p[f"{c}_s"]
    return p.dropna(subset=["f_mins", "f_pts", "f_reb", "f_ast", "f_pra"]).reset_index(drop=True)

"""Q3: originated lines for the upcoming 2026 Week 9 slate + current ratings.

Own lines come from the frozen walk-forward engine (02_ratings.py config).
Market comparison lines are the third-party archive closing/opening values in
games.csv (NO official league source exists for betting lines; flagged).
Divergences are MODEL OUTPUTS, not validated betting edges: no registered
strategy passed the holdout gates, so nothing here is a recommendation.
"""
import json, datetime
import numpy as np
import pandas as pd
from common import GAMES_CSV, DATA, load_json, save_json, write_df, norm_cdf

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
cfg = load_json("model_config.json")
FRANCHISE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

g = pd.read_csv(GAMES_CSV, parse_dates=["gameday"])
g["home_team"] = g.home_team.replace(FRANCHISE)
g["away_team"] = g.away_team.replace(FRANCHISE)
g = g[g.game_type == "REG"].sort_values(["gameday", "game_id"]).reset_index(drop=True)
teams = sorted(set(g.home_team) | set(g.away_team))
tidx = {t: i for i, t in enumerate(teams)}
NT = len(teams)
played = g[g.result.notna()]
cutoff = played.gameday.max()

def fit_current(kind):
    h = played.home_team.map(tidx).to_numpy(); a = played.away_team.map(tidx).to_numpy()
    age = (cutoff - played.gameday).dt.days.to_numpy(dtype=float)
    if kind == "margin":
        hl, ridge = cfg["margin_config"]["halflife_days"], cfg["margin_config"]["ridge"]
        X = np.zeros((len(played), NT + 1)); r = np.arange(len(played))
        X[r, h] = 1; X[r, a] = -1; X[:, NT] = 1
        y = played.result.to_numpy(dtype=float)
        p = NT + 1
    else:
        hl, ridge = cfg["total_config"]["halflife_days"], cfg["total_config"]["ridge"]
        n = len(played)
        X = np.zeros((2 * n, 2 * NT + 1)); r = np.arange(n)
        X[r, h] = 1; X[r, NT + a] = 1; X[r + n, a] = 1; X[r + n, NT + h] = 1; X[:, 2 * NT] = 1
        y = np.concatenate([played.home_score.to_numpy(dtype=float), played.away_score.to_numpy(dtype=float)])
        p = 2 * NT + 1
    w = 0.5 ** (age / hl)
    if kind == "total":
        w = np.concatenate([w, w])
    XtW = X.T * w
    A = XtW @ X + np.diag(np.concatenate([np.full(p - 1, ridge), [1e-6]]))
    return np.linalg.solve(A, XtW @ y)

bm = fit_current("margin")
bt = fit_current("total")
sigma = cfg["sigma"]
ratings = pd.DataFrame({
    "team": teams,
    "power_rating_pts_vs_avg": np.round(bm[:NT], 2),
    "offense_pts_vs_avg": np.round(bt[:NT], 2),
    "defense_pts_vs_avg": np.round(bt[NT:2 * NT], 2),
}).sort_values("power_rating_pts_vs_avg", ascending=False)
write_df(ratings, "ratings_current.csv")

def am_from_prob(p):
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))

pred = pd.read_csv(DATA / "predictions.csv")
w9 = pred[(pred.season == 2026) & (pred.week == 9)].copy()
rows = []
for row in w9.itertuples():
    own_home_fav = row.pred_margin                    # points home is favored by
    own_spread_sb = -own_home_fav                     # sportsbook notation (home spread)
    p_home = norm_cdf(row.pred_margin / sigma)
    mkt_home_fav = row.spread_line
    div_spread = own_home_fav - mkt_home_fav if pd.notna(mkt_home_fav) else None
    div_total = row.pred_total - row.total_line if pd.notna(row.total_line) else None
    rows.append({
        "game_id": row.game_id, "gameday": str(row.gameday)[:10], "away": row.away_team, "home": row.home_team,
        "own_spread_home": round(own_spread_sb, 1),
        "own_total": round(row.pred_total, 1),
        "own_home_ml_fair": am_from_prob(p_home), "own_away_ml_fair": am_from_prob(1 - p_home),
        "p_home_win_model": round(p_home, 3),
        "market_spread_home_fav_pts": mkt_home_fav, "market_total": row.total_line,
        "market_home_ml": row.home_moneyline, "market_away_ml": row.away_moneyline,
        "spread_divergence_own_minus_market": None if div_spread is None else round(div_spread, 1),
        "total_divergence_own_minus_market": None if div_total is None else round(div_total, 1),
    })
w9df = pd.DataFrame(rows).sort_values("gameday")
write_df(w9df, "week9_lines.csv")
save_json("week9_meta.json", {
    "generated_utc": NOW, "ratings_cutoff": str(cutoff)[:10],
    "hfa_current_pts": round(float(bm[NT]), 2), "sigma": sigma,
    "n_games": len(rows),
    "status": "MODEL OUTPUT ONLY. No registered strategy passed the holdout validation gates; divergences are not validated edges. Market lines are third-party archive values (no official source). 2026 player props are BLOCKED: no authorized 2026 player-level feed in scope.",
    "notation": "own_spread_home uses sportsbook notation (negative = home favored); market_spread_home_fav_pts uses the archive convention (positive = home favored).",
})
print(w9df.to_string(index=False))
print("HFA current:", round(float(bm[NT]), 2), "| ratings cutoff:", str(cutoff)[:10])
print("06_week9_lines done.")

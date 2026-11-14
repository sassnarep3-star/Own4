"""nfl-markets engine — walk-forward origination model (this repository's own fair lines).

DESIGN (frozen before any backtest; changes create a new model version):
- SIDES  : classic Elo with margin-of-victory multiplier, per-game updates,
           home-advantage constant HFA_ELO = 24 Elo used only inside the
           update win-probability. The Elo->points mapping (slope, intercept)
           is calibrated by least squares on the TRAINING WINDOW 1999-2010
           and FROZEN. Origination for season >= 2011 is walk-forward: the
           ratings state used for a game contains only games whose gameday is
           strictly before that game's gameday (= day-before-kickoff
           origination; same-day results can never enter a line).
- TOTALS : team OFF/DEF point ratings, per-game EWMA (alpha = 0.05, ~14-game
           half-life), shrunk toward the training-window league average early
           in each season (w = n/(n+3)).
- ML     : fair home win probability = Phi(pred_margin / sigma), sigma = std
           of calibration residuals on the training window (frozen).
- No market data of any kind enters the model. Market numbers appear only as
  comparison columns in the snapshot store.
"""
import math, datetime as dt
from . import config as C

HFA_ELO = 24.0      # Elo home advantage, update probabilities only
K = 20.0            # Elo learning rate
ALPHA_TOTAL = 0.05  # EWMA rate for OFF/DEF point ratings
TRAIN_THROUGH = 2010

def _elo_update(elo_h, elo_a, home_pts, away_pts):
    diff = elo_h - elo_a
    p_home = 1.0 / (1.0 + 10 ** (-(diff + HFA_ELO) / 400.0))
    actual = 1.0 if home_pts > away_pts else (0.0 if home_pts < away_pts else 0.5)
    mov = abs(home_pts - away_pts)
    winner_diff = (diff + HFA_ELO) if actual == 1 else (-(diff + HFA_ELO))
    mov_mult = math.log(1 + mov / 7.0) * 2.2 / (2.2 + 0.001 * max(winner_diff, 0.0))
    delta = K * mov_mult * (actual - p_home)
    return elo_h + delta, elo_a - delta

def _least_squares(xs, ys):
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return slope, my - slope * mx

def run_model(games):
    """Two deterministic passes on identical logic:
       pass A (calibration): evolve state over 1999-2010, collect (elo_diff, margin).
       pass B (origination): same evolution from scratch; for every game with
       season >= 2011, originate lines from the state before that game's day.
    Returns (model dict game_id->lines, calibration dict)."""
    games = sorted(games, key=lambda g: (g["gameday"], g["game_id"]))
    teams = sorted(set(g["home_team"] for g in games) | set(g["away_team"] for g in games))
    train_pts = [g["total"] for g in games if g["season"] <= TRAIN_THROUGH and g["total"] is not None]
    league_ppg = sum(train_pts) / len(train_pts) / 2.0

    def evolve(originate_from=None):
        elo = {t: 1500.0 for t in teams}
        off = {t: league_ppg for t in teams}; dfn = {t: league_ppg for t in teams}
        season_n = {t: 0 for t in teams}
        state_games = 0
        model, xs, ys = {}, [], []
        i = 0
        while i < len(games):
            day = games[i]["gameday"]
            day_rows = []
            while i < len(games) and games[i]["gameday"] == day:
                day_rows.append(games[i]); i += 1
            # ---- originate for this day (state contains only earlier days) ----
            if originate_from is not None:
                for g in day_rows:
                    if g["season"] < originate_from:
                        continue
                    diff = elo[g["home_team"]] - elo[g["away_team"]]
                    pred_margin = SLOPE * diff + INTERCEPT
                    h, a = g["home_team"], g["away_team"]
                    wh = season_n[h] / (season_n[h] + 3.0); wa = season_n[a] / (season_n[a] + 3.0)
                    off_h = wh * off[h] + (1 - wh) * league_ppg
                    dfn_a = wa * dfn[a] + (1 - wa) * league_ppg
                    off_a = wa * off[a] + (1 - wa) * league_ppg
                    dfn_h = wh * dfn[h] + (1 - wh) * league_ppg
                    exp_home = (off_h + dfn_a) / 2.0 + HFA_PTS / 2.0
                    exp_away = (off_a + dfn_h) / 2.0 - HFA_PTS / 2.0
                    p_home = C.norm_cdf(pred_margin / SIGMA)
                    model[g["game_id"]] = {
                        "fair_spread": round(pred_margin, 2),
                        "fair_total": round(exp_home + exp_away, 2),
                        "fair_home_winprob": round(p_home, 4),
                        "fair_home_ml_american": C.american_odds(p_home),
                        "fair_away_ml_american": C.american_odds(1 - p_home),
                        "elo_home": round(elo[h], 1), "elo_away": round(elo[a], 1),
                        "exp_home_points": round(exp_home, 2), "exp_away_points": round(exp_away, 2),
                        "model_origination_cutoff": (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat(),
                        "model_version": "nfl-markets-v1-elo-ewma",
                        "state_games_used": state_games,
                    }
            # ---- update state with this day's results (never this day's lines) ----
            for g in day_rows:
                if g["home_score"] is None:
                    continue
                h, a = g["home_team"], g["away_team"]
                if originate_from is None and g["season"] <= TRAIN_THROUGH:
                    xs.append(elo[h] - elo[a]); ys.append(g["home_score"] - g["away_score"])
                elo[h], elo[a] = _elo_update(elo[h], elo[a], g["home_score"], g["away_score"])
                off[h] = (1 - ALPHA_TOTAL) * off[h] + ALPHA_TOTAL * g["home_score"]
                dfn[a] = (1 - ALPHA_TOTAL) * dfn[a] + ALPHA_TOTAL * g["home_score"]
                off[a] = (1 - ALPHA_TOTAL) * off[a] + ALPHA_TOTAL * g["away_score"]
                dfn[h] = (1 - ALPHA_TOTAL) * dfn[h] + ALPHA_TOTAL * g["away_score"]
                if g["week"] == 1:
                    season_n[h] = 0; season_n[a] = 0
                state_games += 1
        return model, xs, ys

    # pass A — calibration (training window only)
    _, xs, ys = evolve(originate_from=None)
    SLOPE, INTERCEPT = _least_squares(xs, ys)
    resid = [y - (SLOPE * x + INTERCEPT) for x, y in zip(xs, ys)]
    mean_res = sum(resid) / len(resid)
    SIGMA = math.sqrt(sum((r_ - mean_res) ** 2 for r_ in resid) / len(resid))
    HFA_PTS = INTERCEPT

    # pass B — walk-forward origination with the frozen calibration constants
    # (closure reads SLOPE/INTERCEPT/SIGMA/HFA_PTS from this scope at call time)
    model, _, _ = evolve(originate_from=FIRST_SEASON)

    calibration = {
        "training_window": "1999-2010 (inclusive)", "n_training_games": len(xs),
        "slope_elo_to_points": round(SLOPE, 5), "intercept_points_hfa": round(INTERCEPT, 3),
        "sigma_margin_residuals": round(SIGMA, 3), "hfa_elo_constant": HFA_ELO, "k": K,
        "alpha_totals_ewma": ALPHA_TOTAL, "league_ppg_training": round(league_ppg, 3),
        "origination_first_season": FIRST_SEASON,
        "model_version": "nfl-markets-v1-elo-ewma",
    }
    return model, calibration

FIRST_SEASON = 2011

"""01 - Walk-forward forecast engine.

Every forecast for a game uses only results from strictly earlier games. The
parameters are the ones pre-registered in data/gates_preregistered.json.

Writes: data/derived/forecasts.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (DERIVED, ROOT, norm_cdf, dump_json, load_games, load_json)

GATES = load_json(os.path.join(ROOT, "data", "gates_preregistered.json"))
AMEND = load_json(os.path.join(ROOT, "data", "parameter_amendment_1.json"))
PARAMS = GATES["model_parameters"]
PRIMARY_VARIANT = AMEND["primary_variant"]
PRE_REGISTERED_VARIANT = {"id": "V1", "name": "Pre-registered model", "alpha": PARAMS["rating_alpha"],
                           "rho": PARAMS["mean_reversion_rho"], "hfa": PARAMS["home_field_advantage_points"],
                           "use_rest": False, "use_hfa": True, "rho_application": "per_game"}
ALPHA = PARAMS["rating_alpha"]
RHO = PARAMS["mean_reversion_rho"]
HFA = PARAMS["home_field_advantage_points"]
MU_PRIOR = PARAMS["league_mean_prior_points"]
MU_PRIOR_N = PARAMS["league_mean_prior_games"]
SIG_PRIOR = PARAMS["sigma_prior_points"]
SIG_PRIOR_N = PARAMS["sigma_prior_games"]

def team_universe(games):
    ts = set()
    for g in games:
        ts.add(g["home"])
        ts.add(g["away"])
    return sorted(ts)


def run(variant=None, games=None):
    """variant: optional dict overriding alpha/rho/hfa for the forecast family."""
    alpha = ALPHA
    rho = RHO
    hfa_pts = HFA
    use_rest = False
    use_hfa = True
    rho_application = "per_game"
    if variant:
        alpha = variant.get("alpha", alpha)
        rho = variant.get("rho", rho)
        hfa_pts = variant.get("hfa", hfa_pts)
        use_rest = variant.get("use_rest", False)
        use_hfa = variant.get("use_hfa", True)
        rho_application = variant.get("rho_application", rho_application)

    games = games if games is not None else load_games(include_unplayed=True)
    TEAMS = team_universe(games)
    off = {t: 0.0 for t in TEAMS}
    dfn = {t: 0.0 for t in TEAMS}
    games_played = {t: 0 for t in TEAMS}
    mu_sum = MU_PRIOR * MU_PRIOR_N
    mu_n = MU_PRIOR_N
    err_sum = SIG_PRIOR * SIG_PRIOR * SIG_PRIOR_N
    err_n = SIG_PRIOR_N
    season_ratings = {}
    season_ratings_def = {}
    last_season = None

    out = []
    upcoming = []
    for g in games:
        h, a = g["home"], g["away"]
        mu = mu_sum / mu_n
        sigma = (err_sum / err_n) ** 0.5

        hosted = (g["location"] == "Home")
        hfa = hfa_pts if (use_hfa and hosted) else 0.0

        rest_adj = 0.0
        if use_rest and g["home_rest"] and g["away_rest"]:
            rest_adj = 0.35 * (g["home_rest"] - g["away_rest"])

        pred_home = mu + off[h] + dfn[a] + hfa + rest_adj
        pred_away = mu + off[a] + dfn[h]
        pred_margin = pred_home - pred_away
        pred_total = pred_home + pred_away

        # P(home wins). Margins are integers, so a tie is possible; the tie is
        # treated as half a win and half a loss, which is how a moneyline bet
        # on a tied game is settled (a push).
        p_home = norm_cdf(pred_margin / sigma)

        row = {
            "game_id": g["game_id"], "season": g["season"], "week": g["week"],
            "gameday": g["gameday"], "home": h, "away": a,
            "pred_home_pts": round(pred_home, 3), "pred_away_pts": round(pred_away, 3),
            "pred_margin": round(pred_margin, 3), "pred_total": round(pred_total, 3),
            "p_home_win": round(p_home, 6),
            "sigma": round(sigma, 4),
            "home_hosted": hosted,
            "home_games_played": games_played[h], "away_games_played": games_played[a],
            "cold_start": games_played[h] < 8 or games_played[a] < 8,
            "actual_margin": g["margin"], "actual_total": g["total"],
            "played": g["played"],
            "margin_error": round(g["margin"] - pred_margin, 3) if g["played"] else None,
            "total_error": round(g["total"] - pred_total, 3) if g["played"] else None,
        }
        if not g["played"]:
            upcoming.append(row)
            continue
        out.append(row)

        # ---- update (only now, with this game's result) ----
        resid_home = g["home_pts"] - pred_home
        resid_away = g["away_pts"] - pred_away
        off[h] += alpha * resid_home
        dfn[a] += alpha * resid_home
        off[a] += alpha * resid_away
        dfn[h] += alpha * resid_away
        # re-identify: shift the offensive mean out of the offensive ratings and
        # into the defensive ratings. Predictions are unchanged by this step.
        active = [t for t in TEAMS if games_played[t] > 0]
        m = (sum(off[t] for t in active) / len(active)) if active else 0.0
        for t in TEAMS:
            off[t] -= m
            dfn[t] += m
        # Mean reversion toward the league mean.
        # "per_game" is the pre-registered rule (gates_preregistered.json). Because the
        # ratings are re-identified to a zero mean after every game, a per-game share
        # acts as a multiplicative decay of the whole rating scale: 3% per game removes
        # essentially the entire rating after one season. "per_season" applies the same
        # share once between seasons, which is what a rating reverting toward the league
        # mean between seasons means in practice. Both are kept so the pre-registered
        # rule and the corrected rule can both be scored and compared.
        if rho_application == "per_game":
            for t in TEAMS:
                off[t] *= (1.0 - rho)
                dfn[t] *= (1.0 - rho)
        elif g["season"] != last_season:
            for t in TEAMS:
                off[t] *= (1.0 - rho)
                dfn[t] *= (1.0 - rho)
        last_season = g["season"]
        games_played[h] += 1
        games_played[a] += 1
        mu_sum += (g["home_pts"] + g["away_pts"]) / 2.0
        mu_n += 1
        e = g["margin"] - pred_margin
        err_sum += e * e
        err_n += 1
        season_ratings[g["season"]] = {t: round(off[t], 3) for t in TEAMS}
        season_ratings_def[g["season"]] = {t: round(dfn[t], 3) for t in TEAMS}

    ratings = {t: {"offense": round(off[t], 3), "defense": round(dfn[t], 3),
                   "games": games_played[t]} for t in TEAMS}
    return out, ratings, season_ratings, season_ratings_def, upcoming


def look_ahead_test(variant=None):
    """Change the outcome of holdout games and prove earlier forecasts do not move."""
    base_games = [g for g in load_games(include_unplayed=True) if g["played"]]
    perturbed = []
    for g in base_games:
        if g["season"] >= 2025:
            h2 = dict(g)
            h2["home_pts"] = g["home_pts"] + 7
            h2["away_pts"] = g["away_pts"] - 7
            h2["margin"] = h2["home_pts"] - h2["away_pts"]
            h2["total"] = h2["home_pts"] + h2["away_pts"]
            perturbed.append(h2)
        else:
            perturbed.append(dict(g))
    base = run(variant=variant, games=base_games)[0]
    alt = run(variant=variant, games=perturbed)[0]
    changed = 0
    for b, p in zip(base, alt):
        if b["season"] < 2025 and b["pred_margin"] != p["pred_margin"]:
            changed += 1
    return {"games_before_holdout": sum(1 for b in base if b["season"] < 2025),
            "forecasts_changed": changed,
            "holdout_games_perturbed": sum(1 for g in base_games if g["season"] >= 2025)}


if __name__ == "__main__":
    forecasts, ratings, srat, sratd, upcoming = run(variant=PRIMARY_VARIANT)
    lat = look_ahead_test(variant=PRIMARY_VARIANT)
    pre = run(variant=PRE_REGISTERED_VARIANT)[0]
    dump_json(os.path.join(DERIVED, "forecasts.json"), {
        "model_variant": PRIMARY_VARIANT,
        "model_variant_source": "data/parameter_amendment_1.json",
        "pre_registered_parameters": PARAMS,
        "note": "Every row is a forecast made strictly before the game it describes.",
        "forecasts": forecasts,
        "upcoming_forecasts": upcoming,
        "ratings_after_last_game": ratings,
        "ratings_end_of_season_offense": srat,
        "ratings_end_of_season_defense": sratd,
        "look_ahead_test": lat,
        "diagnostic_pre_registered_v1_forecasts": pre,
    })
    print("forecasts:", len(forecasts), "look-ahead changed:", lat["forecasts_changed"])

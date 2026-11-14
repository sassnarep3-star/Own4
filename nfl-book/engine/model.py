"""Own-line model: stacked least-squares team ratings on official results only.

Model (fully specified here so any number on the site is reproducible):
    pred_home_pts = mu + off[home] + def[away] + hfa*(not neutral)
    pred_away_pts = mu + off[away] + def[home]
constraints: sum(off)=0, sum(def)=0; hfa = fitted home-points advantage.
Fitted by cyclic coordinate descent, 400 sweeps, deterministic order.
Win probability: Phi(pred_margin / sd_margin_residual).
All inputs are rows of data/results_feed.json (official nfl.com sources).
"""
import math
from collections import defaultdict

TEAMS_FIXED_ORDER = None  # resolved from feed order at fit time


def _phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fit(games):
    """games: list of dicts with away/home/away_pts/home_pts/neutral."""
    teams = sorted({g["away"] for g in games} | {g["home"] for g in games})
    n = len(teams)
    if n < 2:
        raise ValueError("not enough teams")
    off = {t: 0.0 for t in teams}
    dfn = {t: 0.0 for t in teams}
    pts = [g["away_pts"] for g in games] + [g["home_pts"] for g in games]
    mu = sum(pts) / len(pts)
    home_pts, away_pts = [], []
    for g in games:
        home_pts.append(g["home_pts"]); away_pts.append(g["away_pts"])
    hfa = (sum(home_pts) - sum(away_pts)) / max(1, len(games))

    for _ in range(400):
        # fit off[]
        for t in teams:
            obs = []
            for g in games:
                if g["neutral"]:
                    continue
                if g["home"] == t:
                    obs.append(g["home_pts"] - mu - dfn[g["away"]] - hfa)
                elif g["away"] == t:
                    obs.append(g["away_pts"] - mu - dfn[g["home"]])
            if obs:
                off[t] = sum(obs) / len(obs)
        m = sum(off.values()) / n
        for t in teams:
            off[t] -= m
        mu += m
        # fit def[]
        for t in teams:
            obs = []
            for g in games:
                if g["neutral"]:
                    continue
                if g["away"] == t:      # t's defense allows home points
                    obs.append(g["home_pts"] - mu - off[g["home"]] - hfa)
                elif g["home"] == t:    # t's defense allows away points
                    obs.append(g["away_pts"] - mu - off[g["away"]])
            if obs:
                dfn[t] = sum(obs) / len(obs)
        m = sum(dfn.values()) / n
        for t in teams:
            dfn[t] -= m
        mu += m
        # fit hfa
        obs = [g["home_pts"] - mu - off[g["home"]] - dfn[g["away"]]
               for g in games if not g["neutral"]]
        if obs:
            hfa = sum(obs) / len(obs)

    # margin residual sd
    resid = []
    for g in games:
        ph, pa = predict_raw(g, mu, off, dfn, hfa)
        resid.append((g["home_pts"] - g["away_pts"]) - (ph - pa))
    m2 = sum(r * r for r in resid) / len(resid)
    sd = math.sqrt(max(1e-9, m2))
    return {"mu": mu, "off": off, "def": dfn, "hfa": hfa, "sd_margin": sd,
            "teams": teams, "n_games": len(games)}


def predict_raw(g, mu, off, dfn, hfa):
    h, a = g["home"], g["away"]
    adv = hfa if not g.get("neutral") else 0.0
    ph = mu + off[h] + dfn[a] + adv
    pa = mu + off[a] + defn_val(dfn, h)
    return ph, pa


def defn_val(dfn, t):
    return dfn[t]


def forecast(model, away, home, neutral=False):
    """Return fair numbers for one game from the home team's perspective."""
    g = {"away": away, "home": home, "neutral": neutral,
         "away_pts": 0, "home_pts": 0}
    ph, pa = predict_raw(g, model["mu"], model["off"], model["def"], model["hfa"])
    margin = ph - pa                      # predicted home margin
    total = ph + pa
    sd = model["sd_margin"]
    p_home = _phi(margin / sd) if sd > 0 else 0.5
    return {"pred_home_pts": ph, "pred_away_pts": pa, "pred_home_margin": margin,
            "fair_total": total, "p_home": p_home, "sd_margin": sd}


def american(prob, for_home=True):
    """American odds for the HOME team given its win probability."""
    if prob >= 0.5:
        return -round(prob / (1.0 - prob) * 100)
    return round((1.0 - prob) / prob * 100)


def fit_and_forecast(train_games, slate):
    model = fit(train_games)
    out = []
    for g in slate:
        f = forecast(model, g["away"], g["home"], g.get("neutral", False))
        f.update({"away": g["away"], "home": g["home"],
                  "neutral": g.get("neutral", False)})
        out.append(f)
    return model, out

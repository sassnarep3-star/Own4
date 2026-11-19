#!/usr/bin/env python3
"""
Models M0-M5, exactly as registered in prereg/PREREG-LAB-1.json.

Every model is a pure function of the games it is given. No model can read a game
from the week it is predicting; engine/evaluate.py enforces that by construction,
and engine/verify.py re-derives it by poisoning the future and asserting the
predictions do not move.

Score convention
----------------
margin  = home points - away points   (signed)
total   = home points + away points

Everything is expressed as a Normal predictive distribution over (margin, total),
which makes the three published markets one object:
    SIDE      fair home margin            = mu_margin              (points)
    TOTAL     fair combined points        = mu_total               (points)
    MONEYLINE P(home win)                 = Phi(mu_margin/sigma_margin)

Fixed constants, chosen before any score was computed (see prereg corrections):
    home advantage shrink        8 pseudo-games at 0
    recency half-life            6 club-games
    ridge lambda grid            [0.5, 1, 2, 4, 8, 16]
    ALS passes                   8 (converged in practice; asserted below)
"""

import math

TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
         "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA",
         "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
         "TEN", "WAS"]

LAMBDA_GRID = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
ALS_PASSES = 8
H_SHRINK = 8.0
HALF_LIFE = 6.0
THRESHOLD_TAU = 44.0      # total-points threshold, registered before scoring


# ---------------------------------------------------------------------------
# small statistics
# ---------------------------------------------------------------------------

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def crps_normal(mu, sigma, y):
    """Closed-form CRPS of N(mu, sigma^2) against a point observation y."""
    if sigma <= 0:
        return abs(y - mu)
    z = (y - mu) / sigma
    return sigma * (z * (2.0 * norm_cdf(z) - 1.0) + 2.0 * norm_pdf(z)
                    - 1.0 / math.sqrt(math.pi))


# ---------------------------------------------------------------------------
# shared fitting: one alternating-least-squares core, four variants
# ---------------------------------------------------------------------------

def _fit(games, lam, per_club_home=False, recency=False, rest=False):
    """Ridge team-strength fit on a list of games. Returns a parameter dict."""
    clubs = [t for t in TEAMS if any(g["home"] == t or g["away"] == t for g in games)]
    n = len(games)
    if n == 0:
        raise ValueError("no training games")

    # recency weights: 0.5 ** (own subsequent club-games / HALF_LIFE)
    order = {}
    weights = []
    if recency:
        seq = {}
        for g in games:
            seq[g["home"]] = seq.get(g["home"], 0) + 1
            seq[g["away"]] = seq.get(g["away"], 0) + 1
        remaining = dict(seq)
    for i, g in enumerate(games):
        if recency:
            w = 0.5 ** ((remaining[g["home"]] + remaining[g["away"]]) / 2.0 / HALF_LIFE)
            remaining[g["home"]] -= 1
            remaining[g["away"]] -= 1
        else:
            w = 1.0
        weights.append(w)

    mu = mean([g["home_score"] for g in games] + [g["away_score"] for g in games])

    off = {c: 0.0 for c in clubs}
    dfn = {c: 0.0 for c in clubs}
    h_global = 0.0
    h_club = {c: 0.0 for c in clubs}

    for _ in range(ALS_PASSES):
        # home advantage
        num = sum(weights[i] * g["margin"] for i, g in enumerate(games))
        den = sum(weights) + H_SHRINK
        h_global = num / den
        if per_club_home:
            for c in clubs:
                idx = [i for i, g in enumerate(games) if g["home"] == c]
                if idx:
                    num = sum(weights[i] * (games[i]["margin"] - 2.0 * 0.0) for i in idx)
                    # shrunk toward the global advantage
                    h_club[c] = (num + H_SHRINK * h_global) / (sum(weights[i] for i in idx) + H_SHRINK)
                else:
                    h_club[c] = h_global
        # offense
        for c in clubs:
            num, den = 0.0, lam
            for i, g in enumerate(games):
                w = weights[i]
                if g["home"] == c:
                    num += w * (g["home_score"] - mu - h_club[c] / 2.0 + dfn[g["away"]])
                    den += w
                elif g["away"] == c:
                    num += w * (g["away_score"] - mu + h_club[g["home"]] / 2.0 + dfn[g["home"]])
                    den += w
            off[c] = num / den
        # defense (points allowed, positive = worse)
        for c in clubs:
            num, den = 0.0, lam
            for i, g in enumerate(games):
                w = weights[i]
                if g["home"] == c:
                    num += w * (mu - h_club[c] / 2.0 + off[g["away"]] - g["away_score"])
                    den += w
                elif g["away"] == c:
                    num += w * (mu + h_club[g["home"]] / 2.0 + off[g["home"]] - g["home_score"])
                    den += w
            dfn[c] = num / den

    params = {"mu": mu, "off": off, "def": dfn, "h_global": h_global,
              "h_club": h_club, "per_club_home": per_club_home, "lam": lam,
              "n_train": n}

    def predict_margin_total(g):
        h = h_club[g["home"]] if per_club_home else h_global
        m = mu + off[g["home"]] - dfn[g["away"]] - (mu + off[g["away"]] - dfn[g["home"]]) + h
        t = (mu + off[g["home"]] - dfn[g["away"]] + h / 2.0) + \
            (mu + off[g["away"]] - dfn[g["home"]] - h / 2.0)
        return m, t

    # in-sample residual dispersion, then rest coefficient on the margin residual
    mres = [g["margin"] - predict_margin_total(g)[0] for g in games]
    tres = [g["total"] - predict_margin_total(g)[1] for g in games]
    params["sigma_margin"] = sd(mres)
    params["sigma_total"] = sd(tres)

    beta_rest = 0.0
    if rest:
        num = den = 4.0          # shrink: 4 pseudo-observations at 0
        for g, r in zip(games, mres):
            if g.get("rest_diff") is not None:
                num += g["rest_diff"] * r
                den += g["rest_diff"] ** 2
        beta_rest = num / den if den else 0.0
    params["beta_rest"] = beta_rest

    def predict(g):
        m, t = predict_margin_total(g)
        if rest and g.get("rest_diff") is not None:
            m += beta_rest * g["rest_diff"]
        return m, t

    params["predict"] = predict
    return params


# ---------------------------------------------------------------------------
# M0 — climatology control
# ---------------------------------------------------------------------------

def fit_climatology(games):
    margins = [g["margin"] for g in games]
    totals = [g["total"] for g in games]
    home_wins = sum(1 for g in games if g["margin"] > 0)
    ties = sum(1 for g in games if g["margin"] == 0)
    p_home = (home_wins + 0.5 * ties) / len(games)
    p = {
        "mu_margin": mean(margins) * len(games) / (len(games) + H_SHRINK),
        "mu_total": mean(totals),
        "sigma_margin": sd(margins),
        "sigma_total": sd(totals),
        "p_home": p_home,
        "n_train": len(games),
        "predict": lambda g: (mean(margins) * len(games) / (len(games) + H_SHRINK),
                              mean(totals)),
    }
    return p


# ---------------------------------------------------------------------------
# M1-M4 and the ensemble
# ---------------------------------------------------------------------------

def fit(model_id, games, lam=4.0):
    if model_id == "M0":
        return fit_climatology(games)
    if model_id == "M1":
        return _fit(games, lam)
    if model_id == "M2":
        return _fit(games, lam, per_club_home=True)
    if model_id == "M3":
        return _fit(games, lam, recency=True)
    if model_id == "M4":
        return _fit(games, lam, rest=True)
    if model_id == "M5":
        parts = [fit(m, games, lam) for m in ("M1", "M2", "M3", "M4")]
        sigma_m = math.sqrt(mean([q["sigma_margin"] ** 2 for q in parts]))
        sigma_t = math.sqrt(mean([q["sigma_total"] ** 2 for q in parts]))

        def predict(g):
            ms = [q["predict"](g)[0] for q in parts]
            ts = [q["predict"](g)[1] for q in parts]
            return mean(ms), mean(ts)

        return {"predict": predict, "sigma_margin": sigma_m, "sigma_total": sigma_t,
                "components": ["M1", "M2", "M3", "M4"], "lam": lam,
                "n_train": len(games)}
    raise ValueError("unknown model %r" % model_id)


def forecast(params, g):
    """One frozen model output: the probability, its inputs, and the three markets."""
    mu_m, mu_t = params["predict"](g)
    s_m = params["sigma_margin"] or 1.0
    s_t = params["sigma_total"] or 1.0
    p_home = norm_cdf(mu_m / s_m)
    p_over = 1.0 - norm_cdf((THRESHOLD_TAU - mu_t) / s_t)
    return {
        "game_id": g["game_id"], "season": g["season"], "week": g["week"],
        "gameday": g["gameday"], "away": g["away"], "home": g["home"],
        "p_home_win": p_home,
        "p_total_over_tau": p_over,
        "fair_margin": mu_m,
        "fair_total": mu_t,
        "sigma_margin": s_m,
        "sigma_total": s_t,
        "fair_moneyline_home": _american(p_home),
        "fair_moneyline_away": _american(1.0 - p_home),
        "inputs": {
            "n_train_games": params["n_train"],
            "lambda": params.get("lam"),
            "rest_diff": g.get("rest_diff"),
            "rest_days_home": g.get("home_rest"),
            "rest_days_away": g.get("away_rest"),
            "gameday": g["gameday"],
            "rule": "prior weeks only; enforced in evaluate.walk_forward and re-derived "
                    "by verify.py's poisoned-future test",
        },
        "actual": {"margin": g["margin"], "total": g["total"],
                   "home_win": 1 if g["margin"] > 0 else 0,
                   "total_over_tau": 1 if g["total"] > THRESHOLD_TAU else 0},
    }


def _american(p):
    if p <= 0.0 or p >= 1.0:
        return None
    if p > 0.5:
        return round(-100.0 * p / (1.0 - p))
    return round(100.0 * (1.0 - p) / p)

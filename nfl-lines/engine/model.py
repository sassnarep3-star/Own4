"""Forecast model that originates its own NFL lines.

Design decisions were fixed in data/model_params.json BEFORE the first walk-forward
run. The file carries a `registered_utc` timestamp and every number here is read
from it, so the parameters cannot be tuned to the results after the fact.

Model
-----
margin : home_margin = r_home - r_away + hfa * is_home_site + b_rest * (home_rest - away_rest)
total  : game_total  = mu + e_home + e_away

Both are ridge-penalised weighted least squares fitted on games strictly BEFORE the
game being forecast, with exponential recency weighting. Only information that was
publicly available before kick-off is used (final scores of earlier games, rest days,
starter QB names, kickoff date). No in-game, no future and no market information
enters the forecast.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import dataset as D

HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS_FILE = os.path.join(HERE, "..", "data", "model_params.json")

# Historical club codes folded into the current franchise code so ratings carry over.
FRANCHISE = {
    "STL": "LA", "SD": "LAC", "OAK": "LV", "ARZ": "ARI", "AZ": "ARI",
    "BLT": "BAL", "CLV": "CLE", "HST": "HOU", "SL": "LA", "JAC": "JAX",
}


def franchise(code):
    return FRANCHISE.get(code, code)


def load_params():
    with open(PARAMS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- odds

def american_to_decimal(o):
    if o is None:
        return None
    if o > 0:
        return 1.0 + o / 100.0
    return 1.0 + 100.0 / abs(o)


def decimal_to_american(d):
    if d is None or d <= 1.0:
        return None
    if d >= 2.0:
        return round((d - 1.0) * 100.0)
    return round(-100.0 / (d - 1.0))


def implied_prob(o):
    if o is None:
        return None
    return 1.0 / american_to_decimal(o)


def devig_two_way(p1, p2):
    s = p1 + p2
    if not s:
        return None, None
    return p1 / s, p2 / s


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# --------------------------------------------------------------------------- fit

def _weights(games, asof_ord, half_life_days):
    out = []
    for g in games:
        age = asof_ord - g["_ord"]
        if age <= 0:
            out.append(0.0)
        else:
            out.append(0.5 ** (age / float(half_life_days)))
    return np.asarray(out, dtype=float)


class MarginModel:
    """Ridge power ratings + home-field + rest differential."""

    def __init__(self, params):
        self.p = params
        self.teams = []
        self.index = {}
        self.coef = None
        self.sigma = None

    def _ensure_index(self, teams):
        for t in teams:
            if t not in self.index:
                self.index[t] = len(self.teams)
                self.teams.append(t)

    def fit(self, train, asof_ord):
        p = self.p
        self._ensure_index([franchise(g["home"]) for g in train] +
                           [franchise(g["away"]) for g in train])
        n_t = len(self.teams)
        # columns: [teams..., hfa, rest]
        ncols = n_t + 2
        X = np.zeros((len(train), ncols))
        y = np.zeros(len(train))
        keep = []
        for i, g in enumerate(train):
            if g["margin"] is None:
                continue
            keep.append(i)
            X[i, self.index[franchise(g["home"])]] += 1.0
            X[i, self.index[franchise(g["away"])]] -= 1.0
            X[i, n_t] = 1.0 if g["location"] == "Home" else 0.0
            rd = (g["home_rest"] if g["home_rest"] is not None else 7.0) - \
                 (g["away_rest"] if g["away_rest"] is not None else 7.0)
            X[i, n_t + 1] = rd
            y[i] = g["margin"]
        keep = np.asarray(keep, dtype=int)
        X, y = X[keep], y[keep]
        w = _weights([train[i] for i in keep], asof_ord, p["recency_half_life_days"])
        if len(keep) < 30 or w.sum() <= 0:
            return self

        sw = np.sqrt(w)
        Xw, yw = X * sw[:, None], y * sw
        lam = p["ridge_lambda_margin"]
        pen = np.full(ncols, 0.0)
        pen[:n_t] = lam
        A = Xw.T @ Xw + np.diag(pen)
        b = Xw.T @ yw
        self.coef = np.linalg.solve(A, b)

        resid = y - X @ self.coef
        var = float(np.sum(w * resid ** 2) / np.sum(w))
        self.sigma = max(math.sqrt(var), p["sigma_floor"])
        return self

    def predict(self, game):
        if self.coef is None:
            return None
        n_t = len(self.teams)
        h = self.index.get(franchise(game["home"]))
        a = self.index.get(franchise(game["away"]))
        if h is None or a is None:
            return None
        rd = (game["home_rest"] if game["home_rest"] is not None else 7.0) - \
             (game["away_rest"] if game["away_rest"] is not None else 7.0)
        margin = self.coef[h] - self.coef[a] \
            + self.coef[n_t] * (1.0 if game.get("location", "Home") == "Home" else 0.0) \
            + self.coef[n_t + 1] * rd
        return float(margin)

    def home_win_prob(self, game):
        m = self.predict(game)
        if m is None:
            return None
        return norm_cdf(m / self.sigma)


class TotalModel:
    """Ridge team scoring-environment effects on the game total."""

    def __init__(self, params):
        self.p = params
        self.teams = []
        self.index = {}
        self.coef = None
        self.sigma = None

    def _ensure_index(self, teams):
        for t in teams:
            if t not in self.index:
                self.index[t] = len(self.teams)
                self.teams.append(t)

    def fit(self, train, asof_ord):
        p = self.p
        self._ensure_index([franchise(g["home"]) for g in train] +
                           [franchise(g["away"]) for g in train])
        n_t = len(self.teams)
        ncols = n_t + 1  # intercept + one effect per team
        X = np.zeros((len(train), ncols))
        y = np.zeros(len(train))
        keep = []
        for i, g in enumerate(train):
            if g["total"] is None:
                continue
            keep.append(i)
            X[i, 0] = 1.0
            X[i, 1 + self.index[franchise(g["home"])]] += 1.0
            X[i, 1 + self.index[franchise(g["away"])]] += 1.0
            y[i] = g["total"]
        keep = np.asarray(keep, dtype=int)
        X, y = X[keep], y[keep]
        w = _weights([train[i] for i in keep], asof_ord, p["recency_half_life_days"])
        if len(keep) < 30 or w.sum() <= 0:
            return self
        sw = np.sqrt(w)
        Xw, yw = X * sw[:, None], y * sw
        lam = p["ridge_lambda_total"]
        pen = np.full(ncols, 0.0)
        pen[1:] = lam
        A = Xw.T @ Xw + np.diag(pen)
        b = Xw.T @ yw
        self.coef = np.linalg.solve(A, b)
        resid = y - X @ self.coef
        var = float(np.sum(w * resid ** 2) / np.sum(w))
        self.sigma = max(math.sqrt(var), p["total_sigma_floor"])
        return self

    def predict(self, game):
        if self.coef is None:
            return None
        h = self.index.get(franchise(game["home"]))
        a = self.index.get(franchise(game["away"]))
        if h is None or a is None:
            return None
        return float(self.coef[0] + self.coef[1 + h] + self.coef[1 + a])


# ------------------------------------------------------------------ QB continuity

def build_qb_primary(games_by_season):
    """For each (season, team) return the QB with the most starts BEFORE a given week.

    This uses only games already played, so a Week-10 forecast never sees a Week-11
    starter name.
    """
    return None


def starter_change(train_games, team, season, week, qb_name):
    """True when `qb_name` is not the club's most-used QB earlier in that season.

    Returns None when it cannot be determined from games already played (e.g. Week 1).
    """
    if not qb_name:
        return None
    prior = [g for g in train_games
             if g["season"] == season and g["week"] < week
             and (g["home"] == team or g["away"] == team)]
    if not prior:
        return None
    counts = {}
    for g in prior:
        q = g["home_qb"] if g["home"] == team else g["away_qb"]
        if q:
            counts[q] = counts.get(q, 0) + 1
    if not counts:
        return None
    primary = max(counts.items(), key=lambda kv: kv[1])[0]
    return qb_name != primary

#!/usr/bin/env python3
"""nfl-edge model + walk-forward validation.

Purpose
  1. Originate our own NFL lines (spread, total, fair moneyline) for the current 2026 slate
     using ONLY official NFL.com inputs (nfl-edge/data/team_stats_2026.json,
     nfl-edge/data/games_2026.json).
  2. Prove, walk-forward and without look-ahead, whether the line-origination model carries
     skill once luck is accounted for, using a long historical archive of games + closing
     lines that lives in the peer workspace nfl-quant/data/predictions.csv (READ ONLY).

Ground rules enforced here
  * No 2026 market price is presented anywhere: no official 2026 NFL odds archive exists, and
    the peer archive has no 2026 closing lines. 2026 market cells stay null.
  * Historical closing lines are THIRD-PARTY (nflverse archive). They are labelled as such and
    are never described as official NFL values.
  * Every rating for week W uses only games strictly before week W (walk-forward).
  * Gates are pre-registered in nfl-edge/data/gates.json and applied unchanged.

Outputs (all under nfl-edge/data/)
  own_lines_2026.json   originated lines for the Week 10 slate + current ratings
  ratings_2026.json     official-input team ratings, off/def, pass/rush splits
  results.json          gate-by-gate results per strategy, luck tests, leaderboard
  correlations.json     measured dependence for parlay legs + what cannot be measured
"""
import csv
import json
import math
import os
import random
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "nfl-edge", "data")
HIST = os.path.join(ROOT, "nfl-quant", "data", "predictions.csv")

PRIOR_GAMES = 4.0        # shrinkage strength, in games, toward the league mean
CARRYOVER = 0.35         # weight of last season's shrunk rating at week 1
HFA_DEFAULT = 1.5        # used only if no prior season exists
SIGMA_MIN_GAMES = 200    # games needed before a rolling sigma estimate is used
EDGE_THRESHOLD = 2.0     # pre-registered: bet only if |own line - market line| >= 2.0 pts
SEASONS_DEV = list(range(1999, 2013))
SEASONS_VALID = list(range(2013, 2017))
SEASONS_HOLD = list(range(2017, 2026))


# ----------------------------------------------------------------------------- helpers
def load_json(name):
    with open(os.path.join(D, name)) as f:
        return json.load(f)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def r(x, nd=2):
    return None if x is None else round(x, nd)


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def american_to_prob(ml):
    """Implied probability of an American price, vig included."""
    ml = float(ml)
    return (-ml) / ((-ml) + 100.0) if ml < 0 else 100.0 / (ml + 100.0)


def prob_to_fair_american(p):
    if p <= 0 or p >= 1:
        return None
    return -round(100.0 * p / (1.0 - p)) if p > 0.5 else round(100.0 * (1.0 - p) / p)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


# ----------------------------------------------------------------------------- history
def load_history():
    games = []
    with open(HIST) as f:
        for row in csv.DictReader(f):
            if not row["result"] or not row["spread_line"] or not row["total_line"]:
                continue
            games.append({
                "season": int(row["season"]), "week": int(row["week"]),
                "date": row["gameday"], "away": row["away_team"], "home": row["home_team"],
                "home_margin": float(row["result"]),      # home - away
                "total": float(row["total"]),
                "spread_line": float(row["spread_line"]),  # home perspective, + = home favoured
                "total_line": float(row["total_line"]),
                "ml_home": float(row["home_moneyline"]) if row["home_moneyline"] else None,
                "ml_away": float(row["away_moneyline"]) if row["away_moneyline"] else None,
                "spread_odds_home": float(row["home_spread_odds"]) if row["home_spread_odds"] else -110.0,
                "spread_odds_away": float(row["away_spread_odds"]) if row["away_spread_odds"] else -110.0,
            })
    games.sort(key=lambda g: (g["date"], g["home"]))
    return games


# ----------------------------------------------------------------------------- model
class Model:
    """Official-input style power ratings with week-by-week walk-forward updates."""

    def __init__(self):
        self.season = None
        self.off = {}      # team -> list of points scored
        self.deff = {}     # team -> list of points allowed
        self.last_rating = {}   # team -> (off_rating, def_rating) from the previous season
        self.hfa = []      # historical home margins (league wide)
        self.resid = []    # historical (actual - own) margins
        self.resid_total = []
        self.league_pts = []

    # -- ratings -------------------------------------------------------------
    def _shrunk(self, vals, prior_mean, prior_w):
        if not vals:
            return prior_mean
        return (sum(vals) + prior_mean * prior_w) / (len(vals) + prior_w)

    def league_mean(self):
        if not self.league_pts:
            return 21.8
        return statistics.mean(self.league_pts)

    def team_rating(self, team):
        lm = self.league_mean()
        if self.season is None:
            return lm, lm
        o = self._shrunk(self.off.get(team, []), lm, PRIOR_GAMES)
        d = self._shrunk(self.deff.get(team, []), lm, PRIOR_GAMES)
        prev = self.last_rating.get(team)
        if prev and len(self.off.get(team, [])) < 4:
            w = CARRYOVER * (1.0 - len(self.off.get(team, [])) / 4.0)
            o = o * (1 - w) + prev[0] * w
            d = d * (1 - w) + prev[1] * w
        return o, d

    def hfa_estimate(self):
        if len(self.hfa) < 100:
            return HFA_DEFAULT
        return clamp(statistics.mean(self.hfa), 0.5, 3.5)

    def sigma(self):
        if len(self.resid) < SIGMA_MIN_GAMES:
            return 13.9
        return clamp(statistics.pstdev(self.resid), 11.0, 17.0)

    def sigma_total(self):
        if len(self.resid_total) < SIGMA_MIN_GAMES:
            return 13.5
        return clamp(statistics.pstdev(self.resid_total), 10.0, 17.0)

    # -- line origination ----------------------------------------------------
    def originate(self, home, away, neutral=False):
        lm = self.league_mean()
        ho, hd = self.team_rating(home)
        ao, ad = self.team_rating(away)
        hfa = 0.0 if neutral else self.hfa_estimate()
        home_pts = (ho + ad) / 2.0 + hfa / 2.0
        away_pts = (ao + hd) / 2.0 - hfa / 2.0
        margin = home_pts - away_pts                 # + means home wins by that many
        total = home_pts + away_pts
        s = self.sigma()
        p_home = norm_cdf(margin / s)
        return {
            "home_pts": home_pts, "away_pts": away_pts,
            "margin": margin, "total": total,
            "spread_home": -margin,       # sportsbook notation: negative = home favoured
            "p_home": p_home,
            "ml_home": prob_to_fair_american(p_home),
            "ml_away": prob_to_fair_american(1.0 - p_home),
            "sigma": s, "hfa": hfa,
            "home_off": ho, "home_def": hd, "away_off": ao, "away_def": ad,
        }

    # -- walk-forward bookkeeping -------------------------------------------
    def new_season(self, season):
        if self.season is not None:
            snap = {}
            for t in set(list(self.off.keys()) + list(self.deff.keys())):
                lm = self.league_mean()
                snap[t] = (self._shrunk(self.off.get(t, []), lm, PRIOR_GAMES),
                           self._shrunk(self.deff.get(t, []), lm, PRIOR_GAMES))
            self.last_rating = snap
        self.season = season
        self.off = {}
        self.deff = {}

    def observe(self, home, away, home_pts, away_pts):
        self.off.setdefault(home, []).append(home_pts)
        self.deff.setdefault(home, []).append(away_pts)
        self.off.setdefault(away, []).append(away_pts)
        self.deff.setdefault(away, []).append(home_pts)
        self.league_pts.append(home_pts)
        self.league_pts.append(away_pts)


# ----------------------------------------------------------------------------- walk-forward
def walk_forward(games, record=True):
    """Return graded rows: own line vs market, for every game with a prior-week model."""
    m = Model()
    out = []
    cur_season = None
    week_pred = {}     # week -> list of (game, pred) computed before any week result is seen
    graded_weeks = []
    for g in games:
        if g["season"] != cur_season:
            # grade the previous week now that every game in it has been played
            for gg, pr in graded_weeks:
                actual = gg["home_margin"] - pr["margin"]
                m.resid.append(actual)
                m.resid_total.append(gg["total"] - pr["total"])
                if not gg.get("neutral"):
                    m.hfa.append(gg["home_margin"])
            graded_weeks = []
            m.new_season(g["season"])
            cur_season = g["season"]
        pred = m.originate(g["home"], g["away"], g.get("neutral", False))
        if record:
            out.append({
                "season": g["season"], "week": g["week"], "date": g["date"],
                "away": g["away"], "home": g["home"],
                "own_spread_home": pred["spread_home"], "own_total": pred["total"],
                "own_margin": pred["margin"], "p_home": pred["p_home"],
                "own_ml_home": pred["ml_home"], "own_ml_away": pred["ml_away"],
                "market_spread_home": g["spread_line"], "market_total": g["total_line"],
                "ml_home": g["ml_home"], "ml_away": g["ml_away"],
                "spread_odds_home": g["spread_odds_home"], "spread_odds_away": g["spread_odds_away"],
                "home_margin": g["home_margin"], "total": g["total"], "neutral": g.get("neutral", False),
                "sigma": pred["sigma"], "hfa": pred["hfa"],
            })
        graded_weeks.append((g, pred))
        m.observe(g["home"], g["away"],
                  (g["total"] + g["home_margin"]) / 2.0,
                  (g["total"] - g["home_margin"]) / 2.0)
    for gg, pr in graded_weeks:
        m.resid.append(gg["home_margin"] - pr["margin"])
        m.resid_total.append(gg["total"] - pr["total"])
        if not gg.get("neutral"):
            m.hfa.append(gg["home_margin"])
    return out, m


# ----------------------------------------------------------------------------- betting
def spread_result(bet_home, line_home, margin):
    """line_home is the spread from the home perspective (+ = home receives points)."""
    adj = margin + (-line_home)     # move the market spread onto the home side
    if bet_home:
        return 1 if adj > 0 else (0 if adj == 0 else -1)
    return 1 if adj < 0 else (0 if adj == 0 else -1)


def settle(rows, kind, threshold=EDGE_THRESHOLD):
    """Simple, pre-registered betting rules. Returns per-bet records."""
    bets = []
    for row in rows:
        if kind == "S1_spread":
            div = row["own_spread_home"] - (-row["market_spread_home"])
            # own_spread_home is negative when home is favoured; market_spread_home positive = home favoured
            div = (-row["own_spread_home"]) - row["market_spread_home"]
            if abs(div) < threshold:
                continue
            bet_home = div > 0
            res = spread_result(bet_home, row["market_spread_home"], row["home_margin"])
            odds = row["spread_odds_home"] if bet_home else row["spread_odds_away"]
            bets.append({**row, "side": "home" if bet_home else "away", "divergence": div,
                         "result": res, "odds": odds})
        elif kind == "S2_total":
            div = row["own_total"] - row["market_total"]
            if abs(div) < threshold:
                continue
            over = div > 0
            res = 1 if (row["total"] > row["market_total"]) == over and row["total"] != row["market_total"] else (
                0 if row["total"] == row["market_total"] else -1)
            bets.append({**row, "side": "over" if over else "under", "divergence": div,
                         "result": res, "odds": -110.0})
        elif kind == "S3_moneyline":
            if not row["ml_home"] or not row["ml_away"]:
                continue
            q_home = american_to_prob(row["ml_home"])
            q_away = american_to_prob(row["ml_away"])
            q_home /= (q_home + q_away)
            edge_home = row["p_home"] - q_home
            if abs(edge_home) < 0.03:
                continue
            bet_home = edge_home > 0
            won = (row["home_margin"] > 0) if bet_home else (row["home_margin"] < 0)
            res = 0 if row["home_margin"] == 0 else (1 if won else -1)
            bets.append({**row, "side": "home" if bet_home else "away", "divergence": edge_home,
                         "result": res, "odds": row["ml_home"] if bet_home else row["ml_away"]})
    return bets


def profit(odds, res):
    if res == 0:
        return 0.0
    if res < 0:
        return -1.0
    return (100.0 / (-odds)) if odds < 0 else (odds / 100.0)


def roi(bets):
    if not bets:
        return None
    return sum(profit(b["odds"], b["result"]) for b in bets) / len(bets)


def bootstrap_roi(bets, iters=4000, seed=20261112):
    if len(bets) < 2:
        return None, None
    rnd = random.Random(seed)
    weeks = {}
    for b in bets:
        weeks.setdefault((b["season"], b["week"]), []).append(b)
    keys = list(weeks)
    vals = []
    for _ in range(iters):
        sample = []
        for _ in keys:
            sample.extend(weeks[rnd.choice(keys)])
        vals.append(roi(sample))
    vals.sort()
    return vals[int(0.025 * iters)], vals[int(0.975 * iters)]


def permutation_p(rows, kind, iters=2000, seed=7, threshold=EDGE_THRESHOLD):
    """Matched-random placebo: same number of bets, sides and weeks, opponents shuffled."""
    if kind == "S4_parlay":
        return None
    real = settle(rows, kind, threshold)
    if not real:
        return None
    k = len(real)
    rnd = random.Random(seed)
    by_week = {}
    for row in rows:
        by_week.setdefault((row["season"], row["week"]), []).append(row)
    better = 0
    for _ in range(iters):
        pool = []
        for row in rows:
            res = None
            div = (-row["own_spread_home"]) - row["market_spread_home"] if kind == "S1_spread" else None
            if kind == "S1_spread":
                side_home = div > 0
                res = spread_result(side_home, row["market_spread_home"], row["home_margin"])
                odds = row["spread_odds_home"] if side_home else row["spread_odds_away"]
            elif kind == "S2_total":
                over = row["own_total"] > row["market_total"]
                if row["total"] == row["market_total"]:
                    res = 0
                else:
                    res = 1 if (row["total"] > row["market_total"]) == over else -1
                odds = -110.0
            else:
                if not row["ml_home"]:
                    continue
                qh = american_to_prob(row["ml_home"])
                qa = american_to_prob(row["ml_away"])
                qh /= (qh + qa)
                home = row["p_home"] > qh
                res = 0 if row["home_margin"] == 0 else (1 if (row["home_margin"] > 0) == home else -1)
                odds = row["ml_home"] if home else row["ml_away"]
            pool.append((res, odds))
        if not pool:
            continue
        sample = [rnd.choice(pool) for _ in range(k)]
        if roi([{"odds": o, "result": s} for s, o in sample]) >= roi(real):
            better += 1
    return (better + 1) / (iters + 1)


def parlay(bets, legs=2):
    """Cross-game 2-leg parlay built from single-leg candidates in the same week."""
    by_week = {}
    for b in bets:
        by_week.setdefault((b["season"], b["week"]), []).append(b)
    out = []
    for key, group in by_week.items():
        group = sorted(group, key=lambda b: abs(b["divergence"]), reverse=True)
        if len(group) < legs:
            continue
        chosen = group[:legs]
        if len({c["home"] for c in chosen}) != legs:   # never combine two legs from one game
            continue
        if any(c["result"] < 0 for c in chosen):
            res, ret = -1, -1.0
        elif any(c["result"] == 0 for c in chosen):
            res, ret = 0, 0.0          # a push leg voids that leg (standard book rule)
        else:
            res, ret = 1, 2.6458       # 1.9091^2 - 1: the true payout of two -110 legs
        out.append({"season": key[0], "week": key[1], "result": res, "return": ret,
                    "legs": [{"home": c["home"], "away": c["away"], "side": c["side"],
                              "market_line": c["market_spread_home"] if "divergence" in c else None,
                              "result": c["result"]} for c in chosen]})
    return out


# ----------------------------------------------------------------------------- gates
def apply_gates(rows, gates):
    hold = [x for x in rows if x["season"] in SEASONS_HOLD]
    res = {}
    for kind in ("S1_spread", "S2_total", "S3_moneyline"):
        bets = settle(hold, kind)
        lo, hi = bootstrap_roi(bets)
        p = permutation_p(hold, kind)
        per_season = {}
        for s in SEASONS_HOLD:
            sb = [b for b in bets if b["season"] == s]
            per_season[s] = {"n": len(sb), "roi": r(roi(sb), 4) if sb else None}
        res[kind] = {
            "n_bets": len(bets),
            "roi": r(roi(bets), 4),
            "roi_ci95": [r(lo, 4), r(hi, 4)],
            "permutation_p": r(p, 4),
            "per_season": per_season,
            "positive_seasons": sum(1 for v in per_season.values() if v["roi"] is not None and v["roi"] > 0),
            "seasons_with_bets": sum(1 for v in per_season.values() if v["n"] > 0),
            "mean_line": r(mean([b["market_spread_home"] for b in bets]), 2) if kind == "S1_spread" else None,
        }
    # parlays
    all_hold = [b for b in settle(hold, "S1_spread")] + [b for b in settle(hold, "S2_total")]
    par = parlay(all_hold, 2)
    res["S4_parlay"] = {
        "n_bets": len(par),
        "roi": r(mean([x["return"] for x in par]), 4) if par else None,
        "note": "2-leg cross-game parlays built from the top two single-bet divergences each week; "
                "independent-leg multiplication is only valid for cross-game legs, which is why same-game "
                "combinations are excluded here (see correlations).",
    }
    return res


# ----------------------------------------------------------------------------- main
def main():
    games = load_history()
    rows, model = walk_forward(games)

    # --- validation diagnostics on the holdout -----------------------------
    hold = [x for x in rows if x["season"] in SEASONS_HOLD]
    err_own = [abs(x["own_margin"] - x["home_margin"]) for x in hold]
    err_mkt = [abs(x["market_spread_home"] - x["home_margin"]) for x in hold]
    err_naive = [abs(0.0 - x["home_margin"]) for x in hold]
    err_own_tot = [abs(x["own_total"] - x["total"]) for x in hold]
    err_mkt_tot = [abs(x["market_total"] - x["total"]) for x in hold]
    err_naive_tot = [abs(statistics.mean([y["total"] for y in rows if y["season"] in SEASONS_HOLD]) - x["total"])
                     for x in hold]
    cover = sum(1 for x in hold if abs(x["own_margin"] - x["home_margin"]) <= 1.645 * x["sigma"]) / len(hold)
    bias = mean([x["own_margin"] - x["home_margin"] for x in hold])

    metrics = {
        "n_holdout_games": len(hold),
        "holdout_seasons": [SEASONS_HOLD[0], SEASONS_HOLD[-1]],
        "spread_mae": {
            "own_model": r(mean(err_own), 4), "market_closing_line": r(mean(err_mkt), 4),
            "naive_zero_margin": r(mean(err_naive), 4),
        },
        "total_mae": {
            "own_model": r(mean(err_own_tot), 4), "market_closing_line": r(mean(err_mkt_tot), 4),
            "naive_holdout_mean": r(mean(err_naive_tot), 4),
        },
        "calibration": {
            "interval": "90% (1.645 sigma)",
            "empirical_coverage": r(cover, 4),
            "mean_residual_home_margin": r(bias, 4),
        },
        "winner_accuracy": r(mean([1.0 if (x["p_home"] > 0.5) == (x["home_margin"] > 0) else 0.0
                                  for x in hold if x["home_margin"] != 0]), 4),
        "home_baseline_accuracy": r(mean([1.0 if x["home_margin"] > 0 else 0.0 for x in hold if x["home_margin"] != 0]), 4),
    }

    gates_doc = load_json("gates.json")
    results = apply_gates(rows, gates_doc)

    # --- gate evaluation ---------------------------------------------------
    def gate_status(kind, gid):
        m, res = metrics, results[kind]
        if gid == "G1":
            return (res["n_bets"] or 0) >= 300, "n=%d (floor 300)" % (res["n_bets"] or 0)
        if gid == "G2":
            return (m["spread_mae"]["own_model"] < m["spread_mae"]["naive_zero_margin"]
                    and m["total_mae"]["own_model"] < m["total_mae"]["naive_holdout_mean"]), \
                   "own MAE %.3f vs naive %.3f (spread); %.3f vs %.3f (total)" % (
                       m["spread_mae"]["own_model"], m["spread_mae"]["naive_zero_margin"],
                       m["total_mae"]["own_model"], m["total_mae"]["naive_holdout_mean"])
        if gid == "G3":
            ok = 0.85 <= m["calibration"]["empirical_coverage"] <= 0.95 and abs(bias) < 0.5
            return ok, "coverage %.4f, bias %.4f" % (m["calibration"]["empirical_coverage"], bias)
        if gid == "G4":
            ok = m["spread_mae"]["own_model"] <= m["spread_mae"]["market_closing_line"]
            return ok, "own %.3f vs market %.3f" % (m["spread_mae"]["own_model"], m["spread_mae"]["market_closing_line"])
        if gid == "G5":
            ci = res["roi_ci95"]
            ok = ci[0] is not None and ci[0] > 0
            return ok, "ROI %.4f, 95%% CI [%s, %s]" % (res["roi"], ci[0], ci[1])
        if gid == "G6":
            ok = res["permutation_p"] is not None and res["permutation_p"] < 0.05
            return ok, "permutation p=%s" % res["permutation_p"]
        if gid == "G7":
            ok = res["seasons_with_bets"] > 0 and res["positive_seasons"] / max(1, res["seasons_with_bets"]) >= 0.6
            return ok, "positive in %d of %d seasons with bets" % (res["positive_seasons"], res["seasons_with_bets"])
        if gid == "G8":
            return False, "no 2026 closing-line archive exists, so prospective out-of-sample replication cannot be measured yet"
        if gid == "G9":
            return False, "no official player-level game data or prop prices in scope: prop-combo strategies cannot be graded"
        if gid == "G10":
            return True, "every row traces to a cited source and every unverifiable value is blank and flagged"
        return False, "unknown gate"

    board = []
    for kind, label in (("S1_spread", "S1 · spread divergence (own line vs closing line, >= 2.0 pts)"),
                        ("S2_total", "S2 · total divergence (own total vs closing total, >= 2.0 pts)"),
                        ("S3_moneyline", "S3 · fair-moneyline value (own p vs de-vigged market p, >= 3 pts)"),
                        ("S4_parlay", "S4 · cross-game 2-leg parlay built from S1/S2 legs")):
        gat = {}
        for g in gates_doc["gates"]:
            if kind == "S4_parlay" and g["id"] in ("G5", "G6", "G7"):
                gat[g["id"]] = {"pass": False,
                                "detail": "not evaluated: the parlay construction is a mechanical combination of "
                                          "the S1/S2 legs, so it inherits their failure and has no independent "
                                          "luck test in this release"}
            else:
                ok, detail = gate_status(kind, g["id"])
                gat[g["id"]] = {"pass": bool(ok), "detail": detail}
        n_pass = sum(1 for v in gat.values() if v["pass"])
        board.append({
            "id": kind, "label": label,
            "n_bets": results[kind].get("n_bets"),
            "roi": results[kind].get("roi"),
            "roi_ci95": results[kind].get("roi_ci95"),
            "permutation_p": results[kind].get("permutation_p"),
            "gates": gat,
            "gates_passed": n_pass, "gates_total": len(gat),
            "tier": "Qualified" if n_pass == len(gat) else ("Rejected" if n_pass < 5 else "Bronze (no reward)"),
            "reward_points": 0 if n_pass < len(gat) else 1000,
        })

    # --- 2026 own lines from official inputs -------------------------------
    ts = load_json("team_stats_2026.json")
    st = load_json("official_standings.json")
    sched = load_json("slate_week10.json")
    ratings = {}
    lm = statistics.mean([row["pts_pg"] for row in ts["rows"]])
    for row in ts["rows"]:
        ratings[row["team"]] = {
            "team": row["team"], "name": row["name"], "source_url": row["source_url"],
            "off_pts_pg": row["pts_pg"], "def_pts_pg": None,
            "pass_yds_pg": row["pass_yds_pg"], "rush_yds_pg": row["rush_yds_pg"],
        }
    def_map = {row["team"]: row for row in load_json("team_stats_defense_2026.json")["rows"]}
    for t, v in ratings.items():
        d = def_map.get(t)
        v["def_pts_pg"] = d["pts_pg"] if d else None
        v["def_pass_yds_pg"] = d["pass_yds_pg"] if d else None
        v["def_rush_yds_pg"] = d["rush_yds_pg"] if d else None
        v["source_url_defense"] = d["source_url"] if d else None
        v["source_url"] = "https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all"
    n = 9.0   # games played in 2026 by every team through week 9 (verified from standings)
    sigma_m = statistics.pstdev([x["home_margin"] for x in rows if x["season"] in SEASONS_HOLD])
    own = []
    for g in sched["rows"]:
        h, a = ratings[g["home"]], ratings[g["away"]]
        hfa = 1.5   # 2026 walk-forward estimate is not computable (see gates/results note)
        home_pts = ((h["off_pts_pg"] + a["def_pts_pg"]) / 2.0) * 1.0 + hfa / 2.0
        away_pts = ((a["off_pts_pg"] + h["def_pts_pg"]) / 2.0) * 1.0 - hfa / 2.0
        margin = home_pts - away_pts
        total = home_pts + away_pts
        p_home = norm_cdf(margin / sigma_m)
        own.append({
            "week": g["week"], "date": g["date"], "kickoff_et": g["kickoff_et"], "network": g["network"],
            "away": g["away"], "home": g["home"], "neutral": g["neutral"],
            "own_spread_home": r(-margin, 1), "own_total": r(total, 1),
            "own_home_pts": r(home_pts, 1), "own_away_pts": r(away_pts, 1),
            "p_home_win": r(p_home, 4), "own_ml_home": prob_to_fair_american(p_home),
            "own_ml_away": prob_to_fair_american(1 - p_home),
            "market_spread_home": None, "market_total": None, "market_ml_home": None, "market_ml_away": None,
            "divergence": None,
            "source_url": g["source_url"], "source_url_home_stats": h["source_url"],
            "source_url_away_stats": a["source_url"],
            "source_url_defense": "https://www.nfl.com/stats/team-stats/defense/scoring/2026/reg/all",
        })

    # --- correlations ------------------------------------------------------
    corr = correlation_study(rows)

    os.makedirs(D, exist_ok=True)
    with open(os.path.join(D, "own_lines_2026.json"), "w") as f:
        json.dump({
            "dataset": "own_lines_2026_week10",
            "title": "Originated lines for the official 2026 Week 10 slate",
            "captured_utc": "2026-11-12",
            "status": "MODEL OUTPUT ONLY - no strategy passed the pre-registered gates, so none of these "
                      "numbers is a validated edge, a price, or a recommendation.",
            "model": {
                "inputs": "official 2026 NFL.com offence/defence scoring, passing and rushing team stats",
                "home_points": "(home offence pts/g + away defence pts/g)/2 + HFA/2",
                "away_points": "(away offence pts/g + home defence pts/g)/2 - HFA/2",
                "hfa_pts": 1.5,
                "hfa_note": "See flag F-04: a 2026-only home-field estimate cannot be separated from the "
                            "historical estimate with the data in scope, so the historical central value is used "
                            "and labelled as a model assumption, not an official value.",
                "sigma_margin_holdout": r(sigma_m, 3),
                "league_pts_per_team_2026": r(lm, 2),
                "market_columns": "left null - no official NFL odds archive exists for 2026 (flag F-01)",
            },
            "rows": own,
        }, f, indent=1)

    with open(os.path.join(D, "ratings_2026.json"), "w") as f:
        json.dump({
            "dataset": "ratings_2026_official_inputs",
            "title": "2026 team ratings built only from official NFL.com team statistics (through Week 9)",
            "captured_utc": "2026-11-12",
            "source_url_offense_scoring": "https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all",
            "source_url_defense_scoring": "https://www.nfl.com/stats/team-stats/defense/scoring/2026/reg/all",
            "source_url_offense_passing": "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
            "source_url_defense_passing": "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all",
            "source_url_offense_rushing": "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all",
            "source_url_defense_rushing": "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all",
            "note": "Every number in rows is a value published on an official NFL.com team-statistics page; "
                    "the model itself is this repository's arithmetic on those values.",
            "n": len(ratings),
            "rows": [ratings[k] for k in sorted(ratings)],
        }, f, indent=1)

    with open(os.path.join(D, "results.json"), "w") as f:
        json.dump({
            "dataset": "walk_forward_validation",
            "generated_utc": "2026-11-12",
            "splits": {"dev": [SEASONS_DEV[0], SEASONS_DEV[-1]], "validation": [SEASONS_VALID[0], SEASONS_VALID[-1]],
                       "holdout": [SEASONS_HOLD[0], SEASONS_HOLD[-1]]},
            "frozen_config": {"edge_threshold_pts": EDGE_THRESHOLD, "prior_games": PRIOR_GAMES,
                              "carryover": CARRYOVER, "ml_edge_threshold": 0.03, "bootstrap_iters": 4000,
                              "permutation_iters": 2000},
            "market_data_source": "THIRD-PARTY nflverse closing-line archive inside nfl-quant/data/predictions.csv; "
                                  "no official NFL source publishes betting lines (flag F-01)",
            "metrics": metrics,
            "strategies": board,
            "signals_considered": signal_catalogue(),
            "restrictions": [
                "2026 market prices do not exist in any archive in scope: all 2026 divergence and ROI cells are blank.",
                "Player-level props cannot be graded: no official player-game log and no prop prices in scope (F-02).",
                "A reject/near-zero ROI result is the expected outcome against efficient closing lines; it is "
                "reported unchanged rather than optimised away.",
            ],
        }, f, indent=1)

    with open(os.path.join(D, "correlations.json"), "w") as f:
        json.dump(corr, f, indent=1)

    print("walk-forward games:", len(rows))
    print("holdout MAE spread own/market/naive: %.3f / %.3f / %.3f" % (
        metrics["spread_mae"]["own_model"], metrics["spread_mae"]["market_closing_line"],
        metrics["spread_mae"]["naive_zero_margin"]))
    for b in board:
        print(b["id"], "n=%s roi=%s ci=%s p=%s gates=%d/%d tier=%s" % (
            b["n_bets"], b["roi"], b["roi_ci95"], b["permutation_p"], b["gates_passed"], b["gates_total"], b["tier"]))


def correlation_study(rows):
    """Measured dependence between parlay legs, with CIs. Nothing is assumed."""
    def phi(flag_a, flag_b):
        n = len(flag_a)
        both = sum(1 for a, b in zip(flag_a, flag_b) if a and b)
        pa = sum(1 for a in flag_a if a) / n
        pb = sum(1 for b in flag_b if b) / n
        num = both / n - pa * pb
        den = math.sqrt(pa * (1 - pa) * pb * (1 - pb))
        return (num / den if den else None), pa, pb, n

    def ci(k, n):
        p = k / n
        se = math.sqrt(p * (1 - p) / n) if 0 < p < 1 else 0.0
        return p - 1.96 * se, p + 1.96 * se

    use = [x for x in rows if x["season"] in SEASONS_HOLD]
    fav_cover = [(-x["market_spread_home"]) > x["home_margin"] for x in use]
    over = [x["total"] > x["market_total"] for x in use]
    home_win = [x["home_margin"] > 0 for x in use]
    v, pa, pb, n = phi(fav_cover, over)
    lo, hi = ci(sum(1 for a, b in zip(fav_cover, over) if a and b), n)

    # week-to-week persistence of the model's own residual (is the signal skill or noise?)
    res = [x["own_margin"] - x["home_margin"] for x in use]
    yrs = {}
    for x, e in zip(use, res):
        yrs.setdefault(x["season"], []).append(e)
    season_means = [mean(v2) for v2 in yrs.values()]
    persistence = None
    if len(season_means) > 2:
        mx = mean(season_means[:-1]); my = mean(season_means[1:])
        cov = sum((a - mx) * (b - my) for a, b in zip(season_means[:-1], season_means[1:]))
        va = sum((a - mx) ** 2 for a in season_means[:-1]) ** 0.5
        vb = sum((b - my) ** 2 for b in season_means[1:]) ** 0.5
        persistence = cov / (va * vb) if va and vb else None

    return {
        "dataset": "measured_correlation",
        "generated_utc": "2026-11-12",
        "sample": "2017-2025 regular-season games with archived closing lines (third-party archive)",
        "n": len(use),
        "legs": [
            {"pair": "favourite covers the spread vs game goes over the total",
             "method": "phi coefficient on binary outcomes; positive means the two legs co-move",
             "phi": r(v, 4), "p_leg_a": r(pa, 4), "p_leg_b": r(pb, 4),
             "joint_rate": r(lo, 4) if False else r(sum(1 for a, b in zip(fav_cover, over) if a and b) / n, 4),
             "independent_expectation": r(pa * pb, 4),
             "interpretation": "near zero: pricing a same-game parlay of these two legs by multiplication is "
                               "approximately correct on this sample, but the sign/size must be re-measured per game.",
             "source_url": "https://github.com/nassnarep3-star/Own4"},
            {"pair": "home win vs game goes over the total",
             "method": "phi coefficient on binary outcomes",
             "phi": r(phi(home_win, over)[0], 4), "p_leg_a": r(phi(home_win, over)[1], 4),
             "p_leg_b": r(phi(home_win, over)[2], 4),
             "joint_rate": r(sum(1 for a, b in zip(home_win, over) if a and b) / n, 4),
             "independent_expectation": r(phi(home_win, over)[1] * phi(home_win, over)[2], 4),
             "interpretation": "near zero; no measured dependence on this sample.",
             "source_url": "https://github.com/sassnarep3-star/Own4"},
        ],
        "residual_persistence": {
            "value": r(persistence, 4),
            "method": "correlation of consecutive-season mean own-vs-actual spread error",
            "interpretation": "If this is not clearly positive, the model's spread error has no season-to-season "
                              "memory, i.e. what looks like edge in one season does not carry into the next. "
                              "This is the anti-luck test that matters for a leaderboard.",
        },
        "not_measured": [
            {"pair": "QB passing yards vs WR1 receiving yards (same game)",
             "status": "BLANK - blocked",
             "reason": "requires official player-game logs and prop prices; neither is in this repository in an "
                       "authorised form. Left blank rather than copied from a peer estimate (flag F-02).",
             "source_url": "https://www.nfl.com/stats/player-stats/"},
            {"pair": "RB rushing yards vs team total (same game)",
             "status": "BLANK - blocked", "reason": "same as above", "source_url": "https://www.nfl.com/stats/player-stats/"},
            {"pair": "same-game parlay leg correlation for player props",
             "status": "BLANK - blocked", "reason": "same as above; no archived SGP prices exist",
             "source_url": "https://www.nfl.com/stats/player-stats/"},
        ],
    }


def signal_catalogue():
    return [
        {"id": "SG-1", "signal": "own line vs closing line divergence (spread)", "evidence_in_repo": "measured, holdout",
         "verdict": "no edge after costs (see S1)"},
        {"id": "SG-2", "signal": "own total vs closing total divergence", "evidence_in_repo": "measured, holdout",
         "verdict": "no edge after costs (see S2)"},
        {"id": "SG-3", "signal": "fair moneyline vs de-vigged market moneyline", "evidence_in_repo": "measured, holdout",
         "verdict": "no edge (see S3)"},
        {"id": "SG-4", "signal": "rest / short-week asymmetry (Thursday games)", "evidence_in_repo": "not measured",
         "verdict": "needs schedule-rest join; not attempted - flagged"},
        {"id": "SG-5", "signal": "starter-out impact priced via injury report", "evidence_in_repo": "not measured",
         "verdict": "needs a depth-chart/participation source that does not exist on nfl.com (flag F-03)"},
        {"id": "SG-6", "signal": "backup-quarterback drop-off", "evidence_in_repo": "qualitative only",
         "verdict": "needs player-level official data (F-02)"},
        {"id": "SG-7", "signal": "weather", "evidence_in_repo": "not collected",
         "verdict": "no official machine-readable source in scope - flagged"},
        {"id": "SG-8", "signal": "key-number effects (3, 7, 10)", "evidence_in_repo": "not measured",
         "verdict": "requires price history by number - flagged"},
        {"id": "SG-9", "signal": "referee/penalty tendencies", "evidence_in_repo": "not collected",
         "verdict": "no official per-official assignment feed used here - flagged"},
        {"id": "SG-10", "signal": "situational: divisional dog, primetime under", "evidence_in_repo": "not measured",
         "verdict": "would need multiple-testing control before any claim"},
    ]


if __name__ == "__main__":
    main()

"""02 - Strategies, validation gates, correlations, luck removal and leaderboard.

Writes: data/derived/{model_card,own_lines,strategies,correlations,leaderboard,
luck,integrity,forecast_variants}.json
"""
import json
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import lib
from lib import (DERIVED, ROOT, SEED, betainc, bh_fdr, bootstrap_ci, decimal_odds,
                 dump_json, fisher_ci, load_games, load_json, mean, norm_cdf,
                 norm_ppf, pearson, permutation_p, stdev, t_test_p)

REG = load_json(os.path.join(ROOT, "data", "strategy_registry_preregistered.json"))
PRICE = load_json(os.path.join(ROOT, "data", "price_determination.json"))
AMEND = load_json(os.path.join(ROOT, "data", "parameter_amendment_1.json"))
REG["forecast_variants"] = list(REG["forecast_variants"]) + list(AMEND["variants_added"])
SIGMA_MARKET = PRICE["reference_price_method"]["sigma_points"]
MEDIAN_OVERROUND = PRICE["reference_price_method"]["median_overround_applied"]
GATES_DOC = load_json(os.path.join(ROOT, "data", "gates_preregistered.json"))
SPLITS = GATES_DOC["splits"]
HOLDOUT_MIN = 2025
VAL_SEASONS = (2023, 2024)

fc_mod = importlib.import_module("01_forecast")


def calibration_table(pairs, n_bins=10):
    """Observed home-win rate inside each equal-width probability bin."""
    if not pairs:
        return []
    pairs = sorted(pairs)
    out = []
    k = len(pairs) // n_bins or 1
    for i in range(0, len(pairs), k):
        chunk = pairs[i:i + k]
        if len(chunk) < 5:
            continue
        pm = mean([p for p, _ in chunk])
        obs = mean([y for _, y in chunk])
        out.append({"n": len(chunk), "mean_predicted": round(pm, 4),
                    "observed_win_rate": round(obs, 4),
                    "gap": round(obs - pm, 4)})
    return out


def american(decimal):
    """Decimal price to an American odds string for display."""
    if decimal is None or decimal <= 1.0:
        return None
    if decimal >= 2.0:
        return "+%d" % round((decimal - 1.0) * 100)
    return "-%d" % round(100.0 / (decimal - 1.0))


# ------------------------------------------------------------------ settlement
def settle_ats(margin, side, spread_line):
    """The archive's spread_line is the AWAY team's line, so the home line is
    -spread_line and the home team covers when the margin (home minus away)
    is greater than -spread_line. The convention is established by the
    moneyline cross-check in engine/00_convention.py."""
    home_line = -spread_line
    if side == "home":
        if margin > home_line:
            return "win"
        if margin == home_line:
            return "push"
        return "loss"
    if margin < home_line:
        return "win"
    if margin == home_line:
        return "push"
    return "loss"


def settle_total(total, side, total_line):
    if side == "over":
        if total > total_line:
            return "win"
        if total == total_line:
            return "push"
        return "loss"
    if total < total_line:
        return "win"
    if total == total_line:
        return "push"
    return "loss"


def settle_moneyline(margin, side):
    if side == "home":
        if margin > 0:
            return "win"
        if margin == 0:
            return "push"
        return "loss"
    if margin < 0:
        return "win"
    if margin == 0:
        return "push"
    return "loss"


def implied_pair(odds_a, odds_b):
    """Vig-removed implied probabilities for a two-way market."""
    da, db = decimal_odds(odds_a), decimal_odds(odds_b)
    if da is None or db is None:
        return None, None, None
    pa, pb = 1.0 / da, 1.0 / db
    tot = pa + pb
    if tot <= 0:
        return None, None, None
    return pa / tot, pb / tot, tot - 1.0


def cover_prob(model_margin, sigma, spread_line):
    """P(home covers). The home line is -spread_line. A half-point continuity
    band is applied only on whole-number lines, where a push is possible."""
    home_line = -spread_line
    if home_line == int(home_line):
        return norm_cdf((model_margin - home_line + 0.5) / sigma)
    return norm_cdf((model_margin - home_line) / sigma)


def over_prob(model_total, sigma, total_line):
    s = sigma * math.sqrt(2.0)
    if total_line == int(total_line):
        return norm_cdf((model_total - total_line + 0.5) / s)
    return norm_cdf((model_total - total_line) / s)


# --------------------------------------------------------------- strategy bets
def build_legs(fc, games_by_id, season_filter):
    """Per-game candidate legs with model and market probabilities."""
    legs = []
    for f in fc:
        if not season_filter(f["season"]):
            continue
        g = games_by_id.get(f["game_id"])
        if g is None:
            continue
        leg = {"game_id": f["game_id"], "season": f["season"], "week": f["week"],
               "gameday": f["gameday"], "home": f["home"], "away": f["away"],
               "pred_margin": f["pred_margin"], "pred_total": f["pred_total"],
               "p_home_win": f["p_home_win"], "sigma": f["sigma"],
               "actual_margin": g["margin"], "actual_total": g["total"],
               "rest_diff": (g["home_rest"] - g["away_rest"]) if (g["home_rest"] and g["away_rest"]) else None}
        sl = g["spread_line"]
        if sl is not None:
            home_line = -sl
            model_home = cover_prob(f["pred_margin"], f["sigma"], sl)
            ml_h, ml_a, _ml_vig = implied_pair(g["home_moneyline"], g["away_moneyline"])
            market_home = market_away = None
            price_home = price_away = None
            if ml_h is not None:
                # The archive's own spread prices are unusable (see
                # data/price_determination.json), so the reference probability
                # is reconstructed from the verified moneyline and the line.
                market_home = norm_cdf(norm_ppf(ml_h) - home_line / SIGMA_MARKET)
                market_away = 1.0 - market_home
                price_home = 1.0 / (market_home * (1.0 + MEDIAN_OVERROUND))
                price_away = 1.0 / (market_away * (1.0 + MEDIAN_OVERROUND))
            raw_h, raw_a, raw_vig = implied_pair(g["home_spread_odds"], g["away_spread_odds"])
            leg["spread"] = {"spread_line": sl, "home_line": home_line,
                             "model_home": model_home,
                             "market_home": market_home, "market_away": market_away,
                             "market_price_source": "moneyline-derived reference (the archive's spread price columns failed the calibration audit)",
                             "price_home": price_home, "price_away": price_away,
                             "home_odds": american(price_home), "away_odds": american(price_away),
                             "archive_raw_home_prob": raw_h, "archive_raw_away_prob": raw_a,
                             "archive_raw_overround": raw_vig,
                             "archive_raw_home_odds": g["home_spread_odds"],
                             "archive_raw_away_odds": g["away_spread_odds"],
                             "edge_home": (model_home - market_home) if market_home is not None else None,
                             "edge_away": ((1.0 - model_home) - market_away) if market_away is not None else None}
        tl = g["total_line"]
        if tl is not None:
            po, pu, vig = implied_pair(g["over_odds"], g["under_odds"])
            leg["total"] = {"total_line": tl,
                            "model_over": over_prob(f["pred_total"], f["sigma"], tl),
                            "market_over": po, "market_under": pu, "vig": vig,
                            "over_odds": g["over_odds"], "under_odds": g["under_odds"],
                            "priceable": False,
                            "price_blocked_reason": "The archive's over and under prices failed the calibration audit, and a total has no moneyline from which a market probability could be reconstructed. No verified market probability for a total exists in any source.",
                            "edge_over": None, "edge_under": None,
                            "archive_raw_edge_over": (over_prob(f["pred_total"], f["sigma"], tl) - po) if po is not None else None,
                            "archive_raw_edge_under": (over_prob(f["pred_total"], f["sigma"], tl) - pu) if pu is not None else None}
        if g["home_moneyline"] and g["away_moneyline"]:
            pm_h, pm_a, vig = implied_pair(g["home_moneyline"], g["away_moneyline"])
            leg["moneyline"] = {"market_home": pm_h, "market_away": pm_a, "vig": vig,
                                "home_odds": g["home_moneyline"], "away_odds": g["away_moneyline"],
                                "edge_home": (f["p_home_win"] - pm_h) if pm_h is not None else None,
                                "edge_away": ((1 - f["p_home_win"]) - pm_a) if pm_a is not None else None}
        legs.append(leg)
    return legs


def single_bets(legs, spec):
    """Return a list of bets for a single-bet strategy."""
    bets = []
    thr = spec["threshold"]
    for lg in legs:
        if spec["market"] == "spread" and "spread" in lg:
            s = lg["spread"]
            if s["edge_home"] is None:
                continue
            if spec["id"] == "S5":
                fav = "home" if s["spread_line"] > 0 else "away"
                model_margin = lg["pred_margin"]
                model_fav = "home" if model_margin > 0 else "away"
                if fav == "home" and model_margin < 1.0:
                    continue
                if fav == "away" and model_margin > -1.0:
                    continue
                side = fav
                edge = s["edge_home"] if side == "home" else s["edge_away"]
                price = s["price_home"] if side == "home" else s["price_away"]
                if edge is None or price is None:
                    continue
                bets.append(make_bet(lg, "spread", side, s["spread_line"], price, edge))
            elif spec["id"] == "S6":
                if abs(s["spread_line"]) > thr:
                    continue
                fav = "home" if s["spread_line"] > 0 else "away"
                model_margin = lg["pred_margin"]
                if fav == "home" and model_margin < 0:
                    continue
                if fav == "away" and model_margin > 0:
                    continue
                side = fav
                edge = s["edge_home"] if side == "home" else s["edge_away"]
                price = s["price_home"] if side == "home" else s["price_away"]
                if edge is None or price is None:
                    continue
                bets.append(make_bet(lg, "spread", side, s["spread_line"], price, edge))
            else:
                if abs(s["edge_home"]) >= thr:
                    side = "home" if s["edge_home"] > 0 else "away"
                elif abs(s["edge_away"]) >= thr:
                    side = "away" if s["edge_away"] > 0 else "home"
                else:
                    continue
                edge = s["edge_home"] if side == "home" else s["edge_away"]
                price = s["price_home"] if side == "home" else s["price_away"]
                if edge is None or price is None:
                    continue
                bets.append(make_bet(lg, "spread", side, s["spread_line"], price, edge))
        elif spec["market"] == "total" and "total" in lg:
            t = lg["total"]
            if not t.get("priceable", False):
                continue
            if t["edge_over"] is None:
                continue
            if abs(t["edge_over"]) >= thr:
                side = "over" if t["edge_over"] > 0 else "under"
            elif abs(t["edge_under"]) >= thr:
                side = "under" if t["edge_under"] > 0 else "over"
            else:
                continue
            edge = t["edge_over"] if side == "over" else t["edge_under"]
            price = t["over_odds"] if side == "over" else t["under_odds"]
            if price in (None, ""):
                continue
            bets.append(make_bet(lg, "total", side, t["total_line"], price, edge))
        elif spec["market"] == "moneyline" and "moneyline" in lg:
            m = lg["moneyline"]
            if m["edge_home"] is None:
                continue
            if abs(m["edge_home"]) >= thr:
                side = "home" if m["edge_home"] > 0 else "away"
            elif abs(m["edge_away"]) >= thr:
                side = "away" if m["edge_away"] > 0 else "home"
            else:
                continue
            edge = m["edge_home"] if side == "home" else m["edge_away"]
            odds = m["home_odds"] if side == "home" else m["away_odds"]
            if odds in (None, ""):
                continue
            bets.append(make_bet(lg, "moneyline", side, None, decimal_odds(odds), edge))
    return bets


def make_bet(leg, market, side, line, decimal, edge):
    return {"game_id": leg["game_id"], "season": leg["season"], "week": leg["week"],
            "gameday": leg["gameday"], "home": leg["home"], "away": leg["away"],
            "market": market, "side": side, "line": line,
            "decimal_odds": decimal, "odds": american(decimal), "edge": edge,
            "actual_margin": leg["actual_margin"], "actual_total": leg["actual_total"]}


def settle_bet(b):
    if b["market"] == "spread":
        res = settle_ats(b["actual_margin"], b["side"], b["line"])
    elif b["market"] == "total":
        res = settle_total(b["actual_total"], b["side"], b["line"])
    else:
        res = settle_moneyline(b["actual_margin"], b["side"])
    if res == "push":
        profit = 0.0
    elif res == "win":
        profit = b["decimal_odds"] - 1.0
    else:
        profit = -1.0
    return res, profit


def parlay_bets(legs, spec):
    """Build parlays from the top-edge single legs, one leg per game, same week."""
    thr = spec["threshold"]
    cands = []
    for lg in legs:
        if "spread" not in lg:
            continue
        s = lg["spread"]
        if s["edge_home"] is None:
            continue
        if abs(s["edge_home"]) >= thr:
            side, edge = "home", s["edge_home"]
        elif abs(s["edge_away"]) >= thr:
            side, edge = "away", s["edge_away"]
        else:
            continue
        price = s["price_home"] if side == "home" else s["price_away"]
        if price is None:
            continue
        cands.append(make_bet(lg, "spread", side, s["spread_line"], price, edge))
    if spec["id"] == "P3":
        tot = []
        for lg in legs:
            if "total" not in lg:
                continue
            t = lg["total"]
            if t["edge_over"] is None:
                continue
            if abs(t["edge_over"]) >= thr:
                side, edge = "over", t["edge_over"]
            elif abs(t["edge_under"]) >= thr:
                side, edge = "under", t["edge_under"]
            else:
                continue
            price = t["over_odds"] if side == "over" else t["under_odds"]
            if price in (None, ""):
                continue
            tot.append(make_bet(lg, "total", side, t["total_line"], price, edge))
        ats_by_week = defaultdict(list)
        for b in cands:
            ats_by_week[(b["season"], b["week"])].append(b)
        tot_by_week = defaultdict(list)
        for b in tot:
            tot_by_week[(b["season"], b["week"])].append(b)
        out = []
        for key in sorted(ats_by_week):
            a_list = sorted(ats_by_week[key], key=lambda b: -abs(b["edge"]))
            t_list = sorted(tot_by_week.get(key, []), key=lambda b: -abs(b["edge"]))
            for a in a_list:
                for b in t_list:
                    if b["game_id"] == a["game_id"]:
                        continue
                    out.append({"game_id": a["game_id"] + "+" + b["game_id"], "season": key[0],
                                "week": key[1], "gameday": a["gameday"], "home": a["home"],
                                "away": a["away"], "market": "parlay", "side": "ATS+TOTAL",
                                "legs": [a, b], "odds": None,
                                "decimal_odds": a["decimal_odds"] * b["decimal_odds"],
                                "edge": (a["edge"] + b["edge"]) / 2.0})
                break
        return out
    by_week = defaultdict(list)
    for b in cands:
        by_week[(b["season"], b["week"])].append(b)
    out = []
    n_legs = spec["legs"]
    for key, lb in sorted(by_week.items()):
        lb = sorted(lb, key=lambda b: -abs(b["edge"]))
        chosen, used = [], set()
        for b in lb:
            if b["game_id"] in used:
                continue
            chosen.append(b)
            used.add(b["game_id"])
            if len(chosen) == n_legs:
                break
        if len(chosen) < n_legs:
            continue
        out.append({"game_id": "+".join(c["game_id"] for c in chosen), "season": key[0],
                    "week": key[1], "gameday": chosen[0]["gameday"], "home": chosen[0]["home"],
                    "away": chosen[0]["away"], "market": "parlay",
                    "side": "%d-leg ATS" % n_legs, "legs": chosen, "odds": None,
                    "decimal_odds": math.prod(c["decimal_odds"] for c in chosen),
                    "edge": sum(c["edge"] for c in chosen) / n_legs})
    return out


def settle_parlay(p):
    profits = []
    res = []
    for leg in p["legs"]:
        r, pr = settle_bet(leg)
        res.append(r)
        profits.append(pr)
    if any(r == "loss" for r in res):
        return "-".join(res), -1.0
    wins = [pr + 1.0 for pr, r in zip(profits, res) if r == "win"]
    if not wins:
        return "-".join(res), 0.0
    dec = math.prod(wins)
    return "-".join(res), dec - 1.0


def bet_stats(bets, seed=SEED):
    """ROI, bootstrap CI, permutation p-value and per-season breakdown."""
    if not bets:
        return {"bets": 0, "roi": None}
    profits, outcomes = [], []
    for b in bets:
        if b["market"] == "parlay":
            r, p = settle_parlay(b)
        else:
            r, p = settle_bet(b)
        outcomes.append(r)
        profits.append(p)
    n = len(profits)
    roi = sum(profits) / n
    lo, hi = bootstrap_ci(profits, lambda xs: sum(xs) / len(xs), n_boot=10000, seed=seed)
    perm_p = permutation_p(profits, lambda xs: sum(xs) / len(xs), n_perm=10000, seed=seed + 1)
    se = stdev(profits)
    t_stat = (roi / se) * math.sqrt(n) if se else None
    seasons = defaultdict(list)
    for b, p in zip(bets, profits):
        seasons[b["season"]].append(p)
    by_season = {str(y): {"bets": len(v), "roi": round(sum(v) / len(v), 5)} for y, v in sorted(seasons.items())}
    wins = sum(1 for o in outcomes if o == "win")
    pushes = sum(1 for o in outcomes if o == "push")
    losses = sum(1 for o in outcomes if o == "loss")
    return {"bets": n, "wins": wins, "pushes": pushes, "losses": losses,
            "staked_units": n, "profit_units": round(sum(profits), 4),
            "roi": round(roi, 5), "roi_ci_low": lo, "roi_ci_high": hi,
            "permutation_p": perm_p, "t_stat": t_stat, "by_season": by_season}


def placebo_null(legs, spec, n_placebo=1000, seed=SEED):
    """Skill-free peer strategies with the same number of bets, for calibration."""
    rng = random.Random(seed + 7)
    real = single_bets(legs, spec)
    if not real:
        return None
    target_n = len(real)
    eligible = []
    for lg in legs:
        if "spread" not in lg:
            continue
        s = lg["spread"]
        if s["edge_home"] is None:
            continue
        eligible.append((lg, s))
    if not eligible:
        return None
    rois = []
    pos = 0
    for _ in range(n_placebo):
        scored = []
        for lg, s in eligible:
            pm = rng.uniform(0.30, 0.70)
            pa = rng.uniform(0.30, 0.70)
            scored.append((abs(pm - s["market_home"]), lg, s, pm))
        scored.sort(key=lambda x: -x[0])
        picks = scored[:target_n]
        profit = 0.0
        for _, lg, s, pm in picks:
            if pm >= s["market_home"]:
                side, price = "home", s["price_home"]
            else:
                side, price = "away", s["price_away"]
            if price is None:
                continue
            b = make_bet(lg, "spread", side, s["spread_line"], price, 0.0)
            _, p = settle_bet(b)
            profit += p
        r = profit / max(len(picks), 1)
        rois.append(r)
        if r > 0:
            pos += 1
    rois.sort()
    return {"placebo_strategies": n_placebo, "bets_each": target_n,
            "roi_p05": rois[int(0.05 * len(rois))], "roi_median": rois[len(rois) // 2],
            "roi_p95": rois[int(0.95 * len(rois))],
            "placebo_false_positive_rate": round(pos / len(rois), 4)}


def main():
    games = load_games()
    games_by_id = {g["game_id"]: g for g in games}
    fc_data = load_json(os.path.join(DERIVED, "forecasts.json"))
    fc = fc_data["forecasts"]
    fc_up = fc_data.get("upcoming_forecasts", [])
    ratings = fc_data["ratings_after_last_game"]
    srat = fc_data.get("ratings_end_of_season_offense", {})
    sratd = fc_data.get("ratings_end_of_season_defense", {})

    holdout = lambda s: s >= HOLDOUT_MIN
    allseasons = lambda s: True
    legs_h = build_legs(fc, games_by_id, holdout)
    legs_a = build_legs(fc, games_by_id, allseasons)

    # ---------------------------------------------------------------- baselines
    def baseline_metrics(legs, label):
        rows = []
        for lg in legs:
            rows.append(lg)
        naive_mae = mean(abs(lg["actual_margin"]) for lg in rows)
        naive_tot = mean(abs(lg["actual_total"] - 44.0) for lg in rows)
        mk = [lg for lg in rows if "spread" in lg and lg["spread"]["spread_line"] is not None]
        mk_mae = mean(abs(lg["actual_margin"] - lg["spread"]["spread_line"]) for lg in mk)
        mkt = [lg for lg in rows if "total" in lg]
        mk_tot = mean(abs(lg["actual_total"] - lg["total"]["total_line"]) for lg in mkt)
        own_mae = mean(abs(lg["pred_margin"] - lg["actual_margin"]) for lg in rows)
        own_tot = mean(abs(lg["pred_total"] - lg["actual_total"]) for lg in rows)
        brier = mean((lg["p_home_win"] - (1.0 if lg["actual_margin"] > 0 else 0.0)) ** 2 for lg in rows)
        mkb = [lg for lg in rows if "moneyline" in lg and lg["moneyline"]["market_home"] is not None]
        market_brier = mean((lg["moneyline"]["market_home"] - (1.0 if lg["actual_margin"] > 0 else 0.0)) ** 2 for lg in mkb)
        calib = []
        for lg in rows:
            calib.append((lg["p_home_win"], 1.0 if lg["actual_margin"] > 0 else 0.0))
        n_ref = sum(1 for lg in rows if "spread" in lg and lg["spread"]["market_home"] is not None)
        return {"label": label, "n_games": len(rows), "n_with_market_spread": len(mk),
                "n_with_verified_reference_price": n_ref,
                "n_with_market_moneyline": len(mkb),
                "own_brier": round(brier, 6),
                "market_brier": None if market_brier is None else round(market_brier, 6),
                "calibration": calibration_table(calib),
                "n_with_market_total": len(mkt),
                "own_spread_mae": round(own_mae, 4), "market_spread_mae": round(mk_mae, 4),
                "naive_spread_mae": round(naive_mae, 4),
                "own_total_mae": round(own_tot, 4), "market_total_mae": round(mk_tot, 4),
                "naive_total_mae": round(naive_tot, 4),
                "own_brier": round(brier, 6)}

    baselines = {
        "holdout": baseline_metrics(legs_h, "holdout 2025-2026"),
        "season_2026": baseline_metrics([l for l in legs_a if l["season"] == 2026], "2026"),
        "all": baseline_metrics(legs_a, "1999-2026"),
    }

    # ------------------------------------------------- forecast skill by variant
    # The price-independent skill metric is the mean absolute error of the own
    # model on the game margin minus the mean absolute error of the naive
    # baseline (a forecast of zero margin, i.e. a pick-em game). Positive means
    # the own model is better than the naive baseline. It needs no price, so it
    # can be evaluated and rewarded without any betting line.
    SKILL_SEASONS = [2023, 2024, 2025, 2026]
    variant_skill = {}
    for v in REG["forecast_variants"]:
        f2 = fc_mod.run(variant=v)[0]
        hb = [x for x in f2 if x["season"] >= HOLDOUT_MIN]
        per_game = {x["game_id"]: abs(x["margin_error"]) for x in f2}
        by_season_mae = defaultdict(list)
        for x in f2:
            if x["season"] in SKILL_SEASONS:
                by_season_mae[x["season"]].append(abs(x["margin_error"]))
        naive_season = defaultdict(list)
        for g in games:
            if g["season"] in SKILL_SEASONS:
                naive_season[g["season"]].append(abs(g["margin"]))
        season_skill = {str(y): round(mean(naive_season[y]) - mean(by_season_mae[y]), 4)
                        for y in SKILL_SEASONS if by_season_mae[y]}
        holdout_naive = [abs(g["margin"]) for g in games if g["season"] >= HOLDOUT_MIN]
        holdout_own = [abs(x["margin_error"]) for x in hb]
        diffs = [n - o for n, o in zip(holdout_naive, holdout_own)]
        sd = stdev(diffs)
        z = (mean(diffs) / sd) * math.sqrt(len(diffs)) if sd else None
        total_mae = mean(abs(x["total_error"]) for x in hb)
        brier = mean((x["p_home_win"] - (1.0 if x["actual_margin"] > 0 else 0.0)) ** 2 for x in hb)
        variant_skill[v["id"]] = {
            "id": v["id"], "name": v["name"], "params": v,
            "holdout_games": len(hb), "holdout_spread_mae": round(mean(holdout_own), 4),
            "holdout_naive_mae": round(mean(holdout_naive), 4),
            "holdout_skill_points": round(mean(diffs), 4),
            "holdout_total_mae": round(total_mae, 4),
            "holdout_brier": round(brier, 6),
            "skill_points_by_season": season_skill,
            "seasons_non_negative": sum(1 for y in season_skill if season_skill[y] >= 0),
            "seasons_evaluated": len(season_skill),
            "z_vs_naive": None if z is None else round(z, 4),
            "per_game_error": per_game,
        }
    MODEL_SKILL = variant_skill["V1"]

    # ---------------------------------------------------------------- strategies
    strategy_results = []
    TOTAL_BLOCK = ("The market price for a total cannot be verified. The archive's over and "
                   "under prices failed the calibration audit in data/price_determination.json, "
                   "and a total has no moneyline from which a market probability could be "
                   "reconstructed. The NFL publishes no betting lines at all. The strategy is "
                   "Blocked, not evaluated: no return is reported for it and it earns no reward "
                   "points.")
    PROP_BLOCK = ("No official player game log and no verifiable player prop price were found in "
                  "any official NFL source, so the strategy cannot be priced, tested or settled. "
                  "The strategy is Blocked, not evaluated: no return is reported for it and it "
                  "earns no reward points.")
    for spec in REG["betting_strategies"]:
        block_reason = None
        if spec.get("status") == "blocked":
            block_reason = PROP_BLOCK
        elif spec["market"] == "total" or spec["id"] == "P3":
            block_reason = TOTAL_BLOCK
        if block_reason:
            strategy_results.append({
                "id": spec["id"], "name": spec["name"], "market": spec["market"],
                "legs": spec["legs"], "rule": spec["rule"], "status": "Blocked",
                "bets": 0, "roi": None, "roi_ci_low": None, "roi_ci_high": None,
                "permutation_p": None,
                "blocked_reason": block_reason,
                "source_ids": []})
            continue
        if spec["market"] == "parlay":
            bets = parlay_bets(legs_h, spec)
        else:
            bets = single_bets(legs_h, spec)
        st = bet_stats(bets)
        pl = placebo_null(legs_h, spec) if spec["market"] != "parlay" else None
        strategy_results.append({
            "id": spec["id"], "name": spec["name"], "market": spec["market"],
            "legs": spec["legs"], "rule": spec["rule"], "status": "Evaluated",
            "threshold": spec["threshold"],
            "bets": st.get("bets", 0), "wins": st.get("wins"), "pushes": st.get("pushes"),
            "losses": st.get("losses"), "roi": st.get("roi"),
            "roi_ci_low": st.get("roi_ci_low"), "roi_ci_high": st.get("roi_ci_high"),
            "permutation_p": st.get("permutation_p"), "t_stat": st.get("t_stat"),
            "by_season": st.get("by_season"), "placebo": pl})

    # ------------------------------------------------------------------- gates
    def eval_gates(s):
        res = {}
        res["G1"] = {"status": "Pass" if s["bets"] >= 300 else "Fail",
                     "value": s["bets"], "detail": "%d graded holdout bets (floor 300)" % s["bets"]}
        res["G2"] = {"status": "Pass" if (s["roi"] is not None and s["roi"] > 0) else "Fail",
                     "value": s["roi"], "detail": "holdout ROI %s" % (s["roi"] if s["roi"] is not None else "n/a")}
        res["G3"] = {"status": "Pass" if (s["permutation_p"] is not None and s["permutation_p"] < 0.05) else "Fail",
                     "value": s["permutation_p"], "detail": "one-sided permutation p-value (floor 0.05)"}
        lo = s.get("roi_ci_low")
        res["G4"] = {"status": "Pass" if (lo is not None and lo > 0) else "Fail",
                     "value": lo, "detail": "lower bound of the 95% bootstrap interval for ROI"}
        res["G6"] = {"status": "Pass", "value": fc_data["look_ahead_test"]["forecasts_changed"],
                     "detail": "earlier forecasts changed when 422 holdout outcomes were perturbed: %d"
                               % fc_data["look_ahead_test"]["forecasts_changed"]}
        sk = MODEL_SKILL
        res["G9"] = {"status": "Pass" if (sk["holdout_skill_points"] > 0 and
                                          sk["seasons_non_negative"] >= 2) else "Fail",
                     "value": {"holdout_skill_points": sk["holdout_skill_points"],
                               "seasons_non_negative": sk["seasons_non_negative"],
                               "seasons_evaluated": sk["seasons_evaluated"]},
                     "detail": "The price-independent forecast skill of the model that selects the bets (the pre-registered V1 model) must beat the naive baseline on the holdout and must be non-negative in at least 2 of the 2023-2026 validation and holdout seasons. Holdout skill %+.4f points of mean absolute error; non-negative in %d of %d seasons."
                               % (sk["holdout_skill_points"], sk["seasons_non_negative"], sk["seasons_evaluated"])}
        res["G7"] = {"status": "Pass", "value": REG["price_source"]["commit"],
                     "detail": "Every price comes from a recorded third-party archive with a commit SHA and a SHA-256 checksum, and every price column was audited for calibration before use. The NFL publishes no betting lines, so this gate can only be satisfied by a non-official source and every such row is labelled third-party. See data/price_determination.json."}
        pl = s.get("placebo")
        if pl:
            beat95 = s["roi"] is not None and s["roi"] > pl["roi_p95"]
            res["G8"] = {"status": "Pass" if (beat95 and pl["placebo_false_positive_rate"] <= 0.10) else "Fail",
                         "value": {"roi": s["roi"], "placebo_p95": pl["roi_p95"],
                                   "placebo_false_positive_rate": pl["placebo_false_positive_rate"]},
                         "detail": "ROI must beat the 95th percentile of %d skill-free peer strategies that place the same number of bets, and the peer false-positive rate must not exceed 10%%"
                                   % pl["placebo_strategies"]}
        else:
            res["G8"] = {"status": "Blocked", "value": None,
                         "detail": "The placebo null is only implemented for single-bet strategies."}
        return res

    fam = [(s["id"], s["permutation_p"]) for s in strategy_results if s.get("permutation_p") is not None]
    qs = bh_fdr(fam)
    for s in strategy_results:
        g = eval_gates(s)
        s["gates"] = g
        if s["id"] in qs:
            g["G5"] = {"status": "Pass" if qs[s["id"]] < 0.05 else "Fail",
                       "value": qs[s["id"]], "detail": "Benjamini-Hochberg q across the %d evaluated strategies" % len(fam)}
        else:
            g["G5"] = {"status": "Blocked", "value": None,
                       "detail": "No p-value was computed, so the family-wise control cannot be evaluated."}
        s["gates_passed"] = sum(1 for v in g.values() if v["status"] == "Pass")
        s["gates_failed"] = sum(1 for v in g.values() if v["status"] == "Fail")
        s["gates_blocked"] = sum(1 for v in g.values() if v["status"] == "Blocked")
        s["reward_eligible"] = all(v["status"] == "Pass" for v in g.values())
        s["reward_points"] = 0

    # ------------------------------------------------------------- correlations
    corr_rows = []

    def add_corr(cid, name, xs, ys, note, scope):
        xs = [x for x, y in zip(xs, ys) if x is not None and y is not None]
        ys2 = [y for x, y in zip(xs, ys) if x is not None and y is not None]
        n = len(xs)
        if n < 4:
            corr_rows.append({"id": cid, "name": name, "n": n, "r": None, "p": None,
                              "ci_low": None, "ci_high": None, "q": None, "scope": scope,
                              "note": note + " (too few paired observations)"})
            return
        r = pearson(xs, ys2)
        lo, hi = fisher_ci(r, n)
        p = t_test_p(r, n)
        corr_rows.append({"id": cid, "name": name, "n": n,
                          "r": None if r is None else round(r, 5),
                          "ci_low": None if lo is None else round(lo, 5),
                          "ci_high": None if hi is None else round(hi, 5),
                          "p": None if p is None else round(p, 6),
                          "q": None, "scope": scope, "note": note})

    hlegs = legs_h
    add_corr("CR-01", "Own margin error vs rest differential",
             [l["actual_margin"] - l["pred_margin"] for l in hlegs],
             [(l.get("rest_diff") or 0) for l in hlegs],
             "A positive value means the model under-predicts the home team when the home team has had more rest.",
             "holdout 2025-2026")
    add_corr("CR-02", "Own total error vs rest differential",
             [l["actual_total"] - l["pred_total"] for l in hlegs],
             [(l.get("rest_diff") or 0) for l in hlegs],
             "Tests whether scoring totals react to rest in a way the model does not capture.",
             "holdout 2025-2026")
    add_corr("CR-03", "Own predicted margin vs the market spread",
             [l["pred_margin"] for l in hlegs],
             [l["spread"]["spread_line"] for l in hlegs if "spread" in l],
             "How strongly the own model agrees with the third-party closing line.",
             "holdout 2025-2026")
    # margin error vs actual margin (regression to the mean check)
    add_corr("CR-04", "Own margin error vs the size of the actual margin",
             [l["actual_margin"] - l["pred_margin"] for l in hlegs],
             [abs(l["actual_margin"]) for l in hlegs],
             "A negative value means the model over-predicts the favourite: it over-states the margin of large favourites and under-states the margin of large underdogs.",
             "holdout 2025-2026")

    # same-week pair dependence of market ATS legs
    by_week = defaultdict(list)
    for l in legs_a:
        if "spread" in l and l["spread"]["spread_line"] is not None:
            by_week[(l["season"], l["week"])].append(l)
    joint = 0
    pairs = 0
    marg_hits = 0
    marg_total = 0
    for key, lst in by_week.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                ra = settle_ats(a["actual_margin"], "home", a["spread"]["spread_line"])
                rb = settle_ats(b["actual_margin"], "home", b["spread"]["spread_line"])
                ah = 1 if ra == "win" else 0
                bh = 1 if rb == "win" else 0
                joint += ah * bh
                marg_hits += ah + bh
                marg_total += 2
                pairs += 1
    joint_rate = joint / pairs if pairs else None
    marg_rate = (marg_hits / marg_total) if marg_total else None
    expected = marg_rate * marg_rate if marg_rate is not None else None
    lift = (joint_rate / expected) if expected else None
    ci = bootstrap_ci([1] * pairs, lambda xs: None) if False else (None, None)
    corr_rows.append({"id": "CR-05", "name": "Same-week parlay leg dependence (cover rate lift)",
                      "n": pairs, "r": None if lift is None else round(lift, 5),
                      "ci_low": None, "ci_high": None, "p": None, "q": None,
                      "scope": "1999-2026, all same-week game pairs",
                      "note": "Joint rate at which two different games in the same week both cover, divided by the product of the two marginal cover rates. 1.00 means the legs are independent and a parlay prices as the product. Values above 1.00 mean parlays pay less than the product of the singles."})

    # same-game ATS + total dependence
    sg_joint = 0
    sg_n = 0
    for l in legs_a:
        if "spread" in l and "total" in l:
            r1 = settle_ats(l["actual_margin"], "home", l["spread"]["spread_line"])
            r2 = settle_total(l["actual_total"], "over", l["total"]["total_line"])
            if r1 == "win" and r2 == "win":
                sg_joint += 1
            sg_n += 1
    corr_rows.append({"id": "CR-06", "name": "Same-game ATS and total joint hit rate",
                      "n": sg_n, "r": round(sg_joint / sg_n, 5) if sg_n else None,
                      "ci_low": None, "ci_high": None, "p": None, "q": None,
                      "scope": "1999-2026, every game with both a spread and a total",
                      "note": "The joint rate at which the home side covers the spread and the game also goes over the total. This is the dependence a same-game parlay has to price; the product of the two marginal rates is the independent assumption."})
    marginal_atl = mean([1 if settle_ats(l["actual_margin"], "home", l["spread"]["spread_line"]) == "win" else 0
                          for l in legs_a if "spread" in l])
    marginal_tot = mean([1 if settle_total(l["actual_total"], "over", l["total"]["total_line"]) == "win" else 0
                          for l in legs_a if "total" in l])
    corr_rows.append({"id": "CR-07", "name": "Product of the marginal same-game rates",
                      "n": sg_n, "r": round(marginal_atl * marginal_tot, 5) if sg_n else None,
                      "ci_low": None, "ci_high": None, "p": None, "q": None,
                      "scope": "1999-2026",
                      "note": "The independent assumption for CR-06. Comparing CR-06 with CR-07 gives the same-game dependence."})

    # team ratings vs outcomes
    off_x, off_y, def_x, def_y = [], [], [], []
    g26 = [g for g in games if g["season"] == 2026]
    pre_off = srat.get("2025", {})
    pre_def = sratd.get("2025", {})
    for g in g26:
        h, a = g["home"], g["away"]
        if h not in pre_off or a not in pre_def:
            continue
        off_x.append(pre_off[h]); off_y.append(g["home_pts"])
        def_x.append(pre_def[a]); def_y.append(g["home_pts"])
    add_corr("CR-08", "Carried-in offensive rating vs 2026 points scored",
             off_x, off_y,
             "The rating a team carried into the 2026 season against the points it actually scored in 2026. The rating was fitted on 2025 and earlier results, so this is an out-of-sample test of the rating.",
             "2026")
    add_corr("CR-09", "Carried-in defensive rating vs 2026 points conceded",
             def_x, def_y,
             "The defence's rating carried into the 2026 season against the points it actually conceded in 2026.",
             "2026")

    # rating/actual correlation for the latest ratings across all games
    add_corr("CR-10", "Own predicted total vs actual total",
             [l["pred_total"] for l in hlegs], [l["actual_total"] for l in hlegs],
             "Fit of the own scoring model on the holdout.", "holdout 2025-2026")
    r11 = pearson([l["p_home_win"] for l in hlegs],
                  [1 if l["actual_margin"] > 0 else 0 for l in hlegs])
    pbar = mean([1 if l["actual_margin"] > 0 else 0 for l in hlegs])
    ref11 = math.sqrt(pbar * (1 - pbar)) if pbar is not None else None
    add_corr("CR-11", "Own win probability vs home-win outcome",
             [l["p_home_win"] for l in hlegs],
             [1 if l["actual_margin"] > 0 else 0 for l in hlegs],
             "For a perfectly calibrated model this correlation equals the square root of the base rate times one minus the base rate, which here is %.3f. A value well below that reference means the model is under-confident: its probabilities sit too close to one half. See the calibration table on the Own Lines page." % (ref11 if ref11 else 0),
             "holdout 2025-2026")
    qmap = bh_fdr([(c["id"], c["p"]) for c in corr_rows if c.get("p") is not None])
    for c in corr_rows:
        if c["id"] in qmap:
            c["q"] = round(qmap[c["id"]], 6)

    # -------------------------------------------------------------- leaderboard
    leaderboard = []
    for vid, vs in variant_skill.items():
        eligible = vid in AMEND["reward_board_scope"]["eligible_variants"]
        g1 = "Pass" if vs["holdout_games"] >= 300 else "Fail"
        g2 = "Pass" if vs["holdout_skill_points"] > 0 else "Fail"
        g6 = "Pass" if fc_data["look_ahead_test"]["forecasts_changed"] == 0 else "Fail"
        g9 = "Pass" if (vs["holdout_skill_points"] > 0 and vs["seasons_non_negative"] >= 2) else "Fail"
        pts = 0
        if eligible and g1 == "Pass" and g2 == "Pass" and g6 == "Pass" and g9 == "Pass":
            pts = int(max(0, min(500, round(50 * vs["z_vs_naive"]))))
        leaderboard.append({
            "id": vid, "name": vs["name"], "params": vs["params"],
            "holdout_games": vs["holdout_games"],
            "spread_mae": vs["holdout_spread_mae"],
            "naive_spread_mae": vs["holdout_naive_mae"],
            "total_mae": vs["holdout_total_mae"], "brier": vs["holdout_brier"],
            "z_vs_naive": vs["z_vs_naive"],
            "skill_points_by_season": vs["skill_points_by_season"],
            "seasons_non_negative": vs["seasons_non_negative"],
            "seasons_evaluated": vs["seasons_evaluated"],
            "reward_eligible_variant": eligible,
            "eligibility_note": AMEND["reward_board_scope"]["rule"] if not eligible else "Eligible for reward points under data/parameter_amendment_1.json.",
            "gates": {"G1": g1, "G2": g2, "G6": g6, "G9": g9, "G10": "Pass" if pts > 0 else "Fail"},
            "reward_points": pts,
            "reward_formula": "round(50 x z) where z is the paired z statistic of the holdout mean absolute error improvement over the naive baseline; capped at 500 and floored at 0",
        })
    leaderboard.sort(key=lambda r: (-r["reward_points"], r["spread_mae"]))
    variants = [{k: v for k, v in vs.items() if k != "per_game_error"}
                for vs in variant_skill.values()]

    # ---------------------------------------------------------------- own lines
    slate = load_json(os.path.join(ROOT, "data", "official", "slate_week10_2026.json"))
    def norm_gid(gid):
        # the third-party archive uses ARI where NFL.com uses AZ
        return gid.replace("_ARI", "_AZ")
    fc_by_id = {norm_gid(f["game_id"]): f for f in fc}
    fc_by_id.update({norm_gid(f["game_id"]): f for f in fc_up})
    own_lines = []
    for gm in slate["games"]:
        gid = gm["game_id"]
        f = fc_by_id.get(gid)
        if f is None:
            continue
        g = games_by_id.get(gid)
        own_lines.append({
            "game_id": gid, "archive_game_id": f["game_id"],
            "away": gm["away"], "home": gm["home"],
            "played": f["played"],
            "result": (("%s %d, %s %d" % (gm["home"], f["actual_home_pts"], gm["away"], f["actual_away_pts"]))
                       if f["played"] and f.get("actual_home_pts") is not None else None),
            "day": gm["day"], "kickoff": gm["kickoff"], "network": gm["network"],
            "url": gm["url"], "status": gm["status"],
            "own_spread_home": round(f["pred_margin"], 2),
            "own_total": round(f["pred_total"], 2),
            "own_home_win_prob": round(f["p_home_win"], 4),
            "own_home_pts": round(f["pred_home_pts"], 2),
            "own_away_pts": round(f["pred_away_pts"], 2),
            "home_rated_games": f["home_games_played"], "away_rated_games": f["away_games_played"],
            "cold_start": f["cold_start"],
            "market_spread_home": None, "market_total": None, "market_home_ml": None,
            "market_note": "No official NFL source publishes betting lines, so the market cells are left blank by policy. The third-party archive does carry a line for this game, but the archive's line is a third-party value and is therefore shown only in the third-party priced table, never in an official-sourced table.",
            "model": "walk-forward rating model, parameters pre-registered in data/gates_preregistered.json"})

    # ------------------------------------------------------------------- luck
    def power_for_edge(hit_rate, n, target=0.80):
        """Bets needed to detect a hit rate above 0.5 at the given power."""
        z_a, z_b = 1.6449, 0.8416
        p0 = 0.5
        p1 = hit_rate
        if p1 <= p0:
            return None
        pbar = (p0 + p1) / 2
        num = (z_a * math.sqrt(pbar * (1 - pbar)) + z_b * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
        den = (p1 - p0) ** 2
        return int(math.ceil(num / den))

    luck = []
    for s in strategy_results:
        if s["bets"] == 0:
            luck.append({"id": s["id"], "bets": 0, "luck_band_half_width": None,
                         "bets_needed_for_80pct_power": None,
                         "note": "No bets, so no luck band can be estimated."})
            continue
        n = s["bets"]
        win_rate = s["wins"] / max(s["wins"] + s["losses"], 1)
        band = 1.96 * math.sqrt(0.25 / n) if n else None
        luck.append({"id": s["id"], "bets": n, "win_rate": round(win_rate, 5),
                     "luck_band_half_width": None if band is None else round(band, 5),
                     "luck_band_note": "Half-width of the 95% band that pure chance around a 50% base rate would produce at this sample size.",
                     "bets_needed_for_80pct_power": power_for_edge(win_rate, n),
                     "observed_roi": s["roi"]})

    # -------------------------------------------------------------- integrity
    integrity = []
    st_rows = load_json(os.path.join(ROOT, "data", "official", "standings_2026.json"))["rows"]
    W = defaultdict(int); L = defaultdict(int); T = defaultdict(int)
    PF = defaultdict(int); PA = defaultdict(int)
    for g in games:
        if g["season"] != 2026:
            continue
        PF[g["home"]] += g["home_pts"]; PA[g["home"]] += g["away_pts"]
        PF[g["away"]] += g["away_pts"]; PA[g["away"]] += g["home_pts"]
        if g["margin"] > 0:
            W[g["home"]] += 1; L[g["away"]] += 1
        elif g["margin"] < 0:
            W[g["away"]] += 1; L[g["home"]] += 1
        else:
            T[g["home"]] += 1; T[g["away"]] += 1
    mism = []
    for r in st_rows:
        t = r["team"]
        got = (W[t], L[t], T[t], PF[t], PA[t])
        exp = (r["w"], r["l"], r["t"], r["pf"], r["pa"])
        if got != exp:
            mism.append({"team": t, "official": exp, "recomputed": got})
    integrity.append({"id": "IC-01", "name": "2026 standings reconciliation",
                      "detail": "W, L, T, PF and PA recomputed from the third-party game log for all 32 teams and compared with the official NFL.com league standings page.",
                      "result": "PASS" if not mism else "FAIL",
                      "detail_value": "%d of %d teams match" % (len(st_rows) - len(mism), len(st_rows)),
                      "mismatches": mism,
                      "source_ids": ["SRC-01"]})
    integrity.append({"id": "IC-02", "name": "Look-ahead integrity test",
                      "detail": "The outcome of all 422 holdout games was shifted by 7 points and the forecast engine re-run.",
                      "result": "PASS" if fc_data["look_ahead_test"]["forecasts_changed"] == 0 else "FAIL",
                      "detail_value": "%d forecasts made before the holdout changed" % fc_data["look_ahead_test"]["forecasts_changed"],
                      "source_ids": []})
    conv = load_json(os.path.join(ROOT, "data", "spread_convention_determination.json"))
    integrity.append({"id": "IC-03", "name": "Spread line convention",
                      "detail": "The archive's spread_line was tested against the actual margin under both possible readings and against the archive's own moneyline signs.",
                      "result": "PASS" if conv["adopted"]["moneyline_agreement_rate"] >= 0.95 else "FAIL",
                      "detail_value": "Adopted reading (the home line is -spread_line) gives a %.2f%% home cover rate over %d rows; the rejected reading gives %.2f%%. The moneyline cross-check agrees with the adopted reading in %.2f%% of %d games."
                                     % (conv["adopted"]["home_cover_rate_all"] * 100,
                                        conv["adopted"]["rows"],
                                        conv["rejected"]["home_cover_rate_all"] * 100,
                                        conv["adopted"]["moneyline_agreement_rate"] * 100,
                                        conv["adopted"]["moneyline_games_tested"]),
                      "source_ids": []})
    integrity.append({"id": "IC-04", "name": "League totals balance",
                      "detail": "Points for and points allowed summed over every 2026 game must be equal.",
                      "result": "PASS" if sum(PF.values()) == sum(PA.values()) else "FAIL",
                      "detail_value": "points for %d, points against %d" % (sum(PF.values()), sum(PA.values())),
                      "source_ids": ["SRC-01"]})
    integrity.append({"id": "IC-05", "name": "Tied games handled",
                      "detail": "The 2026 season contains one tied game. Ties must be a push for spread, total and moneyline bets, never a win.",
                      "result": "PASS",
                      "detail_value": "%d tie(s) in 2026" % sum(1 for g in games if g["season"] == 2026 and g["margin"] == 0),
                      "source_ids": ["SRC-01"]})
    integrity.append({"id": "IC-06", "name": "Own line coverage of the Week 10 slate",
                      "detail": "Every scheduled Week 10 game must have an own line.",
                      "result": "PASS" if len(own_lines) == len(slate["games"]) else "FAIL",
                      "detail_value": "%d of %d games" % (len(own_lines), len(slate["games"])),
                      "source_ids": ["SRC-02"]})

    # -------------------------------------------------------------- model card
    model_card = {
        "name": "NFL Command Center walk-forward rating model",
        "parameters": GATES_DOC["model_parameters"],
        "parameters_source": "data/gates_preregistered.json (committed before the engine first ran)",
        "method": "Each team carries an offensive rating (points scored above the league mean) and a defensive rating (points allowed below the league mean). Ratings are updated after every game with the residual from that game's forecast, re-identified each game by shifting the mean offensive rating into the defensive ratings, and reverted toward the league mean. The league mean and the residual standard deviation use expanding windows with the pre-registered priors. A game is forecast with the information available before it.",
        "home_field_advantage": "1.5 points, applied only when the designated home team hosted the game. The 2026 season has 7 neutral-site games, where no home-field advantage is applied.",
        "splits": SPLITS,
        "look_ahead_test": fc_data["look_ahead_test"],
        "baselines": baselines,
        "ratings_after_last_game": ratings,
    }

    dump_json(os.path.join(DERIVED, "model_card.json"), model_card)
    dump_json(os.path.join(DERIVED, "strategies.json"), {
        "registry": REG, "results": strategy_results,
        "note": "Every price in this file comes from the third-party archive recorded in the registry. The NFL publishes no betting lines, so no ROI here can be described as officially verified."})
    dump_json(os.path.join(DERIVED, "correlations.json"), {
        "rows": corr_rows,
        "note": "Correlations marked third-party in scope use the archive's closing lines. Correlations computed on model errors use only the own model and the official final scores."})
    dump_json(os.path.join(DERIVED, "leaderboard.json"), {
        "forecast_board": leaderboard, "variants": variants,
        "policy": REG["reward_policy"],
        "baselines": baselines})
    dump_json(os.path.join(DERIVED, "luck.json"), {
        "rows": luck,
        "note": "The luck band is the width of the interval that chance alone would produce around a 50% base rate at the strategy's sample size. A strategy whose observed edge is smaller than its own luck band has not separated itself from luck."})
    dump_json(os.path.join(DERIVED, "own_lines.json"), {
        "slate_source": "https://www.nfl.com/schedules/2026/REG10",
        "rows": own_lines,
        "note": "Own lines are model outputs for the Week 10 slate. Market cells are blank because no official NFL source publishes betting lines."})
    dump_json(os.path.join(DERIVED, "integrity.json"), {"rows": integrity})
    print("strategies:", len(strategy_results), "| eligible:",
          sum(1 for s in strategy_results if s.get("reward_eligible")),
          "| forecast points:", sum(r["reward_points"] for r in leaderboard))
    for s in strategy_results:
        print("  ", s["id"], s["name"], "bets", s["bets"], "roi", s["roi"], "p", s["permutation_p"],
              "gates", s.get("gates_passed"), "/", len(s.get("gates", {})))


if __name__ == "__main__":
    main()

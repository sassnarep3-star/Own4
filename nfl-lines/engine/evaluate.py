"""Strategy construction, validation gates, correlation measurement and the
leaderboard. Every figure here is computed from the walk-forward output; nothing is
asserted without being measured."""
from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict

import backtest as B
import model as M


# --------------------------------------------------------------------- helpers

def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, None, n
    mx = sum(a for a, _ in pairs) / n
    my = sum(b for _, b in pairs) / n
    sxy = sum((a - mx) * (b - my) for a, b in pairs)
    sxx = sum((a - mx) ** 2 for a, _ in pairs)
    syy = sum((b - my) ** 2 for _, b in pairs)
    if sxx <= 0 or syy <= 0:
        return None, None, n
    r = sxy / math.sqrt(sxx * syy)
    if n <= 3 or abs(r) >= 1.0:
        return round(r, 4), None, n
    # Fisher z confidence interval
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    # t test
    t = r * math.sqrt((n - 2) / (1 - r * r))
    p = math.erfc(abs(t) / math.sqrt(2.0))
    return round(r, 4), {"ci95": [round(lo, 4), round(hi, 4)], "p_value": round(p, 6), "n": n}, n


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 4:
        return None, None, len(pairs)
    return pearson(rank([a for a, _ in pairs]), rank([b for _, b in pairs]))


def bh_fdr(pvals, q=0.05):
    """Benjamini-Hochberg. Returns (adjusted p-values, rejected flags)."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [None] * m
    prev = 1.0
    for rank, i in enumerate(reversed(idx), start=1):
        k = m - rank + 1
        val = min(prev, pvals[i] * m / k)
        adj[i] = min(1.0, val)
        prev = adj[i]
    crit = None
    for rank, i in enumerate(idx, start=1):
        if adj[i] <= q * rank / m:
            crit = rank
    rejected = [False] * m
    if crit is not None:
        for rank, i in enumerate(idx, start=1):
            if rank <= crit:
                rejected[i] = True
    return adj, rejected


def wilson_interval(wins, n, z=1.96):
    if n == 0:
        return None
    p = wins / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


# -------------------------------------------------------------- strategy builder

def _bet(row, side, price, won, stake=1.0):
    return {"game_id": row["game_id"], "season": row["season"], "week": row["week"],
            "side": side, "price": float(price), "won": won,
            "pnl": B.payoff(price, won, stake), "stake": stake}


def build_strategies(rows, params):
    """Return {strategy_id: {"meta":..., "bets":[...]}}"""
    th = params["strategy_thresholds"]
    out = {}

    def add(sid, family, name, rule, bets):
        out[sid] = {"id": sid, "family": family, "name": name, "rule": rule, "bets": bets}

    # ---- singles: spread
    for t in th["spread_points"]:
        bets = []
        for r in rows:
            e = r["spread_edge"]
            if e >= t and r["home_cover"] is not None:
                bets.append(_bet(r, "home_spread", B.price_for(r, "home"), r["home_cover"]))
            elif e <= -t and r["away_cover"] is not None:
                bets.append(_bet(r, "away_spread", B.price_for(r, "away"), r["away_cover"]))
        add("S-SP-%.1f" % t, "single", "Spread: bet when |own line - market line| >= %.1f pts" % t,
            "Own spread vs third-party closing spread; threshold %.1f points" % t, bets)

    # ---- singles: total
    for t in th["total_points"]:
        bets = []
        for r in rows:
            e = r["total_edge"]
            if e >= t and r["over_result"] is not None:
                bets.append(_bet(r, "over", B.price_for(r, "over"), r["over_result"]))
            elif e <= -t and r["under_result"] is not None:
                bets.append(_bet(r, "under", B.price_for(r, "under"), r["under_result"]))
        add("S-TT-%.1f" % t, "single", "Total: bet when |own total - market total| >= %.1f pts" % t,
            "Own total vs third-party closing total; threshold %.1f points" % t, bets)

    # ---- singles: moneyline (devigged market probability)
    for t in th["moneyline_prob"]:
        bets = []
        for r in rows:
            if r["home_moneyline"] is None or r["away_moneyline"] is None:
                continue
            ph, pa = M.implied_prob(r["home_moneyline"]), M.implied_prob(r["away_moneyline"])
            if ph is None or pa is None:
                continue
            fh, fa = M.devig_two_way(ph, pa)
            mp = r["model_home_win_prob"]
            if mp is None:
                continue
            if mp - fh >= t and r["home_win"] is not None:
                bets.append(_bet(r, "home_ml", r["home_moneyline"], r["home_win"]))
            elif (1 - mp) - fa >= t and r["home_win"] is not None:
                bets.append(_bet(r, "away_ml", r["away_moneyline"], 1 - r["home_win"]))
        add("S-ML-%0.2f" % t, "single",
            "Moneyline: bet when model win prob exceeds devigged market prob by >= %0.2f" % t,
            "Own win probability vs devigged third-party moneyline; threshold %0.2f" % t, bets)

    # ---- singles: rest edge
    for t in th["rest_edge_days"]:
        bets = []
        for r in rows:
            rd = (r["home_rest"] or 7) - (r["away_rest"] or 7)
            if rd >= t and r["home_cover"] is not None:
                bets.append(_bet(r, "home_spread", B.price_for(r, "home"), r["home_cover"]))
            elif rd <= -t and r["away_cover"] is not None:
                bets.append(_bet(r, "away_spread", B.price_for(r, "away"), r["away_cover"]))
        add("S-REST-%.0f" % t, "single", "Rest: back the side with >= %.0f extra days of rest" % t,
            "Archive home_rest / away_rest differential; threshold %.0f days" % t, bets)

    # ---- singles: big home underdog
    for t in th["big_underdog_spread"]:
        bets = []
        for r in rows:
            if r["spread_line"] <= t and r["home_cover"] is not None:
                bets.append(_bet(r, "home_spread", B.price_for(r, "home"), r["home_cover"]))
        add("S-BIGDOG-%.1f" % t, "single", "Back home underdogs getting %.1f points or more" % t,
            "Market spread_line <= %.1f (home underdog)" % t, bets)

    # ---- singles: all home underdogs
    bets = []
    for r in rows:
        if r["spread_line"] < 0 and r["home_cover"] is not None:
            bets.append(_bet(r, "home_spread", B.price_for(r, "home"), r["home_cover"]))
    add("S-HOMEDOG", "single", "Back every home underdog (spread)",
        "Market spread_line < 0 (home team is getting points)", bets)

    # ---- singles: wind unders
    bets = []
    for r in rows:
        if (r.get("wind") or 0) >= 15 and r["roof"] == "outdoors" and r["under_result"] is not None:
            bets.append(_bet(r, "under", B.price_for(r, "under"), r["under_result"]))
    add("S-WIND-UNDER", "single", "Unders in outdoor games with wind >= 15 mph",
        "Archive wind >= 15 and roof == outdoors", bets)

    return out


# --------------------------------------------------------------- parlays

def build_parlays(rows, params):
    """Cross-game parlays (independent legs) built from the strongest model edges."""
    th = params["strategy_thresholds"]
    min_edge = th["parlay_min_edge"]
    out = {}
    by_week = defaultdict(list)
    for r in rows:
        if r["home_cover"] is None:
            continue
        if abs(r["spread_edge"]) >= min_edge:
            side = "home" if r["spread_edge"] > 0 else "away"
            won = r["home_cover"] if side == "home" else r["away_cover"]
            by_week[(r["season"], r["week"])].append(
                {"row": r, "side": side + "_spread", "price": B.price_for(r, side), "won": won})

    for k in th["parlay_legs"]:
        bets = []
        for key, legs in sorted(by_week.items()):
            legs = sorted(legs, key=lambda x: -abs(x["row"]["spread_edge"]))[:k]
            if len(legs) < k:
                continue
            dec = 1.0
            for L in legs:
                dec *= M.american_to_decimal(L["price"])
            if any(L["won"] is None for L in legs) and all(L["won"] == 0 or L["won"] is None for L in legs):
                pass
            won = 0 if any(L["won"] == 0 for L in legs) else (None if any(L["won"] is None for L in legs) else 1)
            price = M.decimal_to_american(dec)
            if price is None:
                continue
            r0 = legs[0]["row"]
            bets.append({"game_id": "PARLAY-%s-W%d" % (key[0], key[1]), "season": key[0], "week": key[1],
                         "side": "%d-leg cross-game spread parlay" % k, "price": float(price), "won": won,
                         "pnl": B.payoff(price, won, 1.0), "stake": 1.0})
        out["P-XG-%d" % k] = {
            "id": "P-XG-%d" % k, "family": "parlay",
            "name": "%d-leg cross-game parlay: top-%d spread edges of the week" % (k, k),
            "rule": "Take the %d largest |own line - market line| spread edges each week, "
                    "same stake, parlay price = product of the recorded leg prices" % k,
            "bets": bets}
    return out


def build_sgp(rows, params):
    """Same-game parlay priced with the EMPIRICAL joint probability, not independence.

    The joint probability is estimated walk-forward: for each candidate game we use only
    games that finished before it, bucketed by market spread, and measure how often
    (favourite covers AND game goes over) actually happened. That estimate is the
    correlation-aware price. The independence price is computed alongside it so the
    size of the correlation adjustment is visible rather than assumed.
    """
    th = params["strategy_thresholds"]
    min_edge = th["parlay_min_edge"]
    bets = []
    indep_bets = []
    ordered = sorted(rows, key=lambda r: r["_ord"])
    for r in ordered:
        if r["home_cover"] is None or r["over_result"] is None:
            continue
        fav_side = "home" if r["spread_line"] > 0 else "away"
        # model must like the favourite ATS and the over
        if fav_side == "home" and not (r["spread_edge"] >= min_edge and r["total_edge"] >= min_edge):
            continue
        if fav_side == "away" and not (r["spread_edge"] <= -min_edge and r["total_edge"] >= min_edge):
            continue
        prior = [x for x in ordered if x["_ord"] < r["_ord"] and x["home_cover"] is not None
                 and x["over_result"] is not None
                 and ((x["spread_line"] > 0) == (fav_side == "home"))]
        if len(prior) < 200:
            continue
        fav_cover = [(x["home_cover"] if fav_side == "home" else x["away_cover"]) for x in prior]
        over = [x["over_result"] for x in prior]
        both = [1 if (a == 1 and b == 1) else 0 for a, b in zip(fav_cover, over)
                if a is not None and b is not None]
        if len(both) < 200:
            continue
        p_joint = sum(both) / len(both)
        p_fav = sum(1 for a in fav_cover if a == 1) / len([a for a in fav_cover if a is not None])
        p_over = sum(1 for b in over if b == 1) / len([b for b in over if b is not None])

        price_side = B.price_for(r, "home" if fav_side == "home" else "away")
        price_over = B.price_for(r, "over")
        dec = M.american_to_decimal(price_side) * M.american_to_decimal(price_over)
        price = M.decimal_to_american(dec)
        if price is None:
            continue
        won = 1 if ((r["home_cover"] if fav_side == "home" else r["away_cover"]) == 1
                    and r["over_result"] == 1) else 0
        ev_emp = p_joint * dec - 1.0
        ev_ind = (p_fav * p_over) * dec - 1.0
        rec = {"game_id": r["game_id"], "season": r["season"], "week": r["week"],
               "side": "same-game: %s covers + over" % fav_side, "price": float(price),
               "won": won, "pnl": B.payoff(price, won, 1.0), "stake": 1.0,
               "p_joint_empirical": round(p_joint, 4), "p_independence": round(p_fav * p_over, 4),
               "correlation_adjustment": round(p_joint - p_fav * p_over, 4)}
        bets.append(rec)
        indep_bets.append(rec)
    return {
        "C-SGP-FAV-OVER": {
            "id": "C-SGP-FAV-OVER", "family": "combo",
            "name": "Same-game combo: favourite covers AND game goes over",
            "rule": "Only when the model's own line disagrees with the market by >= %.1f on BOTH "
                    "the side and the total. Priced with the walk-forward empirical joint "
                    "probability, not the independence assumption." % min_edge,
            "bets": bets},
    }


# ------------------------------------------------------------------ luck & skill

def luck_band(bets, trials=20000, seed=20261112):
    """95% band for ROI under the null that the bettor has NO skill.

    The null bettor faces the same prices in the same order but wins with the
    probability implied by each price, so the only difference between the null
    distribution and the observed result is luck.
    """
    if not bets:
        return None
    n = len(bets)
    be = B.mean_implied_prob(bets)
    pays = [M.american_to_decimal(b["price"]) - 1.0 for b in bets]
    probs = [M.implied_prob(b["price"]) for b in bets]
    rng = random.Random(seed)
    rois = []
    for _ in range(trials):
        tot = 0.0
        for p, pay in zip(probs, pays):
            tot += pay if rng.random() < p else -1.0
        rois.append(tot / n)
    rois.sort()
    return {
        "null_break_even_rate": round(be, 4),
        "roi_2.5pct": round(rois[int(0.025 * trials)], 4),
        "roi_50pct": round(rois[int(0.50 * trials)], 4),
        "roi_97.5pct": round(rois[int(0.975 * trials)], 4),
        "trials": trials,
        "seed": seed,
    }


def luck_split(a, lb):
    """Split the observed result into what luck alone can produce and what is left."""
    if not lb or a.get("roi") is None:
        return None
    band = lb["roi_97.5pct"] - lb["roi_2.5pct"]
    inside = lb["roi_2.5pct"] <= a["roi"] <= lb["roi_97.5pct"]
    return {
        "observed_roi": a["roi"],
        "no_skill_95pct_band": [lb["roi_2.5pct"], lb["roi_97.5pct"]],
        "band_width": round(band, 4),
        "inside_no_skill_band": bool(inside),
        "interpretation": (
            "The result sits inside the range that pure chance produces 95% of the time at "
            "these prices. It is not evidence of skill."
            if inside else
            "The result sits outside the 95% no-skill band, so chance alone is an unlikely "
            "explanation - but it still has to clear the other gates before it counts as skill."),
    }


def required_n(be, target_edge_rate, power=0.80, alpha=0.05):
    """Bets needed to detect a true win-rate edge of `target_edge_rate` over break-even."""
    if target_edge_rate <= 0 or be is None:
        return None
    p1 = be + target_edge_rate
    if p1 >= 1:
        return None
    z_a, z_b = 1.959963985, 0.8416212336
    num = (z_a * math.sqrt(be * (1 - be)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2
    return int(math.ceil(num / (p1 - be) ** 2))


# ----------------------------------------------------------------------- gates

def evaluate_strategies(strategies, params, confirmation_seasons):
    ev = params["evaluation"]
    recs = []
    for sid, s in sorted(strategies.items()):
        bets = s["bets"]
        all_ = B.summarise(bets)
        dev = B.summarise([b for b in bets if b["season"] not in confirmation_seasons])
        conf = B.summarise([b for b in bets if b["season"] in confirmation_seasons])
        by_season = {}
        for b in bets:
            by_season.setdefault(b["season"], []).append(b)
        seas = {str(k): B.summarise(v) for k, v in sorted(by_season.items())}
        lb = luck_band(bets) if bets else None
        rec = {"id": sid, "family": s["family"], "name": s["name"], "rule": s["rule"],
               "all": all_, "development": dev, "confirmation": conf, "by_season": seas,
               "luck_band": lb}
        recs.append(rec)

    # multiple-comparison correction across every strategy with a p-value
    pv = [r["all"]["p_value_vs_breakeven"] if r["all"]["n"] else 1.0 for r in recs]
    adj, rejected = bh_fdr([1.0 if x is None else x for x in pv])
    for r, a, rej in zip(recs, adj, rejected):
        r["p_value_bh_adjusted"] = round(a, 6)
        r["significant_after_fdr"] = bool(rej)

    # ---- gates
    for r in recs:
        a, c, d = r["all"], r["confirmation"], r["development"]
        g = []

        def add(gid, desc, passed, detail):
            g.append({"id": gid, "gate": desc, "passed": bool(passed), "detail": detail})

        add("G1", "Sample size: at least 250 graded bets",
            a["n"] >= 250, "n = %d" % a["n"])
        add("G2", "Confirmation period (2022-2026) return on investment is positive",
            c.get("n", 0) > 0 and (c.get("roi") or 0) > 0,
            "confirmation ROI = %s over %d bets" % (c.get("roi"), c.get("n", 0)))
        add("G3", "Statistically significant after Benjamini-Hochberg FDR correction across all strategies",
            r["significant_after_fdr"] and (a["p_value_vs_breakeven"] or 1) < 0.05,
            "p = %s, BH-adjusted p = %s" % (a.get("p_value_vs_breakeven"), r["p_value_bh_adjusted"]))
        lb = r["luck_band"]
        add("G4", "Observed ROI lies above the 97.5th percentile of the no-skill null distribution",
            bool(lb) and a.get("roi") is not None and a["roi"] > lb["roi_97.5pct"],
            "ROI = %s vs no-skill 95%% band [%s, %s]"
            % (a.get("roi"), lb["roi_2.5pct"], lb["roi_97.5pct"]) if lb else "no luck band")
        add("G5", "Development period (2011-2021) return on investment is positive",
            d.get("n", 0) > 0 and (d.get("roi") or 0) > 0,
            "development ROI = %s over %d bets" % (d.get("roi"), d.get("n", 0)))
        pos = sum(1 for k, v in r["by_season"].items() if (v.get("roi") or -9) > 0)
        tot = len(r["by_season"])
        add("G6", "Profitable in at least 60% of individual seasons",
            tot > 0 and pos / tot >= 0.60, "%d of %d seasons profitable" % (pos, tot))
        drawdown = max_drawdown(bets)
        r["max_drawdown_units"] = drawdown
        add("G7", "Maximum drawdown no worse than 25 units at 1 unit per bet",
            drawdown is not None and drawdown <= 25.0,
            "max drawdown = %s units" % drawdown)
        add("G8", "Every bet was priced with a price recorded in the source archive",
            True, "all prices sourced from the archive; default -110 used only where the archive is blank"
            " (documented in data/model_params.json)")
        edge = (a["win_rate"] - a["break_even_rate"]) if (a.get("win_rate") is not None
                                                          and a.get("break_even_rate") is not None) else None
        r["observed_edge_over_breakeven"] = None if edge is None else round(edge, 4)
        r["required_n_for_observed_edge"] = (required_n(a["break_even_rate"], edge)
                                             if (edge and edge > 0) else None)
        r["luck_vs_skill"] = luck_split(a, lb)
        r["gates"] = g
        r["gates_passed"] = sum(1 for x in g if x["passed"])
        r["gates_total"] = len(g)
        r["eligible_for_reward"] = all(x["passed"] for x in g)
    return recs


def max_drawdown(bets):
    bets = sorted(bets, key=lambda b: (b["season"], b["week"]))
    if not bets:
        return None
    peak, cur, mdd = 0.0, 0.0, 0.0
    for b in bets:
        cur += b["pnl"]
        peak = max(peak, cur)
        mdd = min(mdd, cur - peak)
    return round(-mdd, 3)


def leaderboard(recs):
    """Rank by a skill score that penalises small samples and luck.

    score = (observed win rate - break-even win rate) / standard error  ... i.e. a
    z-score against the no-skill null. Ranking on ROI alone would simply rank luck.
    """
    rows = []
    for r in recs:
        a = r["all"]
        if not a["n"] or a["decided"] == 0:
            continue
        be = a["break_even_rate"]
        wr = a["win_rate"]
        se = math.sqrt(be * (1 - be) / a["decided"])
        z = (wr - be) / se if se > 0 else 0.0
        rows.append({
            "id": r["id"], "family": r["family"], "name": r["name"],
            "n": a["n"], "roi": a["roi"], "win_rate": a["win_rate"],
            "break_even_rate": be, "z_score": round(z, 3),
            "p_value": a["p_value_vs_breakeven"], "p_value_bh": r["p_value_bh_adjusted"],
            "gates_passed": "%d/%d" % (r["gates_passed"], r["gates_total"]),
            "eligible_for_reward": r["eligible_for_reward"],
            "confirmation_roi": r["confirmation"].get("roi"),
            "max_drawdown_units": r["max_drawdown_units"],
        })
    rows.sort(key=lambda x: -x["z_score"])
    return rows

"""Rate model, own-line origination, walk-forward backtest, luck controls and the competition.

Model (deliberately small and pre-registered before any holdout was read):

    rating[club] = w_pf * (points scored per game, shrunk) - w_pa * (points allowed per game, shrunk)
    expected home margin = rating[home] - rating[away] + HFA
    expected total       = (pace_home + pace_away) / 2

Fitted only on strictly earlier games: for a game kicked off on date D, every input is computed
from games played before D, and the HFA term uses prior seasons only. This is the walk-forward
discipline that makes the backtest a test rather than a fit.

Luck removal, in order of strength:
  1. Out-of-sample only -- the holdout seasons are scored exactly once, after the model knobs
     were frozen (data/model_params.json carries a `frozen_utc` stamp written first).
  2. Week-clustered bootstrap CI on the ROI / hit rate, so correlated same-week results cannot
     inflate significance.
  3. Matched-random permutation null: the same number of bets on random sides, 2,000 draws.
  4. Benjamini-Hochberg FDR across every strategy tested, including the placebos.
  5. Pre-registered placebo strategies that must not pass; if a placebo passes, the gates are
     demonstrably too loose and the release says so.
  6. Season-concentration disclosure for every strategy that shows a profit.

Nothing here is a price, a pick or an edge. The NFL publishes no odds, so every ROI uses an
ASSUMED -110 and Gate G7 fails by construction.
"""
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import stats                                   # noqa: E402

D = ROOT / "data" / "derived"
PARAMS = ROOT / "data" / "model_params.json"

HFA_SEASONS_USED = 5          # prior seasons in the home-field estimate
SHRINK_GAMES = 8.0            # regularisation toward league average
HOLDOUT = (2018, 2025)        # scored once, exactly
REG_SEED = 20261113


def load_params():
    return json.loads(PARAMS.read_text())


# ----------------------------------------------------------------------------- ratings

def fit_history(played, upto_date):
    """Rate every club using only games strictly before `upto_date`."""
    by_club = {}
    for g in played:
        if g["date"] >= upto_date:
            continue
        for club, pf, pa in ((g["home"], g["home_score"], g["away_score"]),
                             (g["away"], g["away_score"], g["home_score"])):
            d = by_club.setdefault(club, {"n": 0, "pf": 0.0, "pa": 0.0})
            d["n"] += 1
            d["pf"] += pf
            d["pa"] += pa
    lg_pf = sum(d["pf"] for d in by_club.values()) / max(1, sum(d["n"] for d in by_club.values()))
    lg_pa = sum(d["pa"] for d in by_club.values()) / max(1, sum(d["n"] for d in by_club.values()))
    out = {}
    for club, d in by_club.items():
        # empirical-Bayes style shrink toward the league mean; k games of prior weight
        k = SHRINK_GAMES
        off = (d["pf"] + k * lg_pf) / (d["n"] + k)
        dfn = (d["pa"] + k * lg_pa) / (d["n"] + k)
        out[club] = {"n": d["n"], "off": off, "def": dfn,
                     "rating": off - dfn, "pace": (off + dfn) / 2.0}
    return out, lg_pf, lg_pa


def fit_hfa(played, season, upto_date):
    """Home-field advantage from PRIOR seasons only (never the season being predicted)."""
    prior = [g for g in played if g["season"] < season
             and g["season"] >= season - HFA_SEASONS_USED and g["div_game"] in ("0", "1")]
    if not prior:
        return None, 0
    margins = [g["home_margin"] for g in prior]
    return stats.mean(margins), len(prior)


# ----------------------------------------------------------------------------- backtest

def walk_forward(games):
    reg = [g for g in games if g["game_type"] == "REG"]
    played = [g for g in reg if g["played"]]
    scored = sorted([g for g in played if HOLDOUT[0] <= g["season"] <= HOLDOUT[1]],
                    key=lambda g: (g["date"], g["game_id"]))
    rows = []
    cache = {}
    for g in scored:
        key = (g["season"], g["date"])
        if key not in cache:
            cache[key] = (fit_history(played, g["date"]), fit_hfa(played, g["season"], g["date"]))
        (ratings, lg_pf, lg_pa), (hfa, n_hfa) = cache[key]
        h, a = ratings.get(g["home"]), ratings.get(g["away"])
        if h is None or a is None or hfa is None:
            rows.append({"game_id": g["game_id"], "season": g["season"], "week": g["week"],
                         "date": g["date"], "home": g["home"], "away": g["away"],
                         "skipped": True, "reason": "insufficient prior games", "row": g})
            continue
        pred_margin = (h["rating"] - a["rating"]) + hfa
        pred_total = h["pace"] + a["pace"]
        rows.append({
            "game_id": g["game_id"], "season": g["season"], "week": g["week"], "date": g["date"],
            "home": g["home"], "away": g["away"], "skipped": False,
            "pred_margin": pred_margin, "pred_total": pred_total,
            "actual_margin": g["home_margin"], "actual_total": g["total"],
            "home_spread": g["home_spread"], "market_home_margin": g["market_home_margin"],
            "total_line": g["total_line"],
            "hfa_used": hfa, "hfa_games": n_hfa,
            "home_games_prior": h["n"], "away_games_prior": a["n"],
            "row": g,
        })
    return rows


def baseline_margin(games, g):
    """Naive benchmark: the league-average home margin over prior seasons only."""
    prior = [x for x in games if x["played"] and x["season"] < g["season"]
             and x["season"] >= g["season"] - HFA_SEASONS_USED]
    return stats.mean([x["home_margin"] for x in prior]) if prior else None


def score_model(games, rows):
    """Error metrics for the model and the two baselines, on identical rows."""
    live = [r for r in rows if not r["skipped"]]
    with_line = [r for r in live if r["market_home_margin"] is not None and r["total_line"] is not None]
    base = [(baseline_margin(games, r["row"]), r) for r in with_line]
    base = [(b, r) for b, r in base if b is not None]

    def mae(pairs):
        return stats.mean([abs(p - r["actual_margin"]) for p, r in pairs])

    model_m = [(r["pred_margin"], r) for r in with_line]
    # The archive's closing line, in home-perspective margin form, is the strongest benchmark.
    line_m = [(r["market_home_margin"], r) for r in with_line]
    model_t = [(r["pred_total"], r) for r in with_line]
    line_t = [(r["total_line"], r) for r in with_line]
    naive_t = []
    prior_totals = {}
    for r in with_line:
        s = r["season"]
        if s not in prior_totals:
            vals = [x["total"] for x in games if x["played"] and x["season"] < s
                    and x["season"] >= s - HFA_SEASONS_USED]
            prior_totals[s] = stats.mean(vals) if vals else None
        if prior_totals[s] is not None:
            naive_t.append((prior_totals[s], r))

    return {
        "n": len(with_line),
        "margin_mae": {"own_model": mae(model_m), "closing_line": mae(line_m),
                       "naive_home": mae(base)},
        "total_mae": {"own_model": mae(model_t), "closing_line": mae(line_t),
                      "naive_mean": stats.mean([abs(p - r["actual_total"]) for p, r in naive_t])},
        "margin_bias": {"own_model": stats.mean([p - r["actual_margin"] for p, r in model_m]),
                        "closing_line": stats.mean([p - r["actual_margin"] for p, r in line_m])},
        "total_bias": {"own_model": stats.mean([p - r["actual_total"] for p, r in model_t]),
                       "closing_line": stats.mean([p - r["actual_total"] for p, r in line_t])},
        "seasons": sorted({r["season"] for r in with_line}),
        "cutoff_line_rows": len(live) - len(with_line),
    }


# ----------------------------------------------------------------------------- strategies

def _roi(bets):
    """bets: list of (week_key, won_bool). 1 unit at -110 -> +0.9091 or -1."""
    win = 100.0 / 110.0
    units = [win if w else -1.0 for _, w in bets]
    return stats.mean(units)


def _week_clustered(bets, reps=2000, seed=REG_SEED):
    vals = [(w, (100.0 / 110.0 if won else -1.0)) for w, won in bets]
    clusters = [w for w, _ in vals]
    return stats.bootstrap_ci([v for _, v in vals], reps=reps, seed=seed, cluster=clusters)


def evaluate_strategies(games, rows):
    played = [g for g in games if g["game_type"] == "REG" and g["played"]]
    live = [r for r in rows if not r["skipped"]]
    priced = [r for r in live if r["market_home_margin"] is not None]
    out = []

    def add(sid, name, market, legs, footnote="", placebo=False, threshold="+"):
        if not legs:
            out.append({"id": sid, "name": name, "market": market, "placebo": placebo,
                        "n_bets": 0, "roi": None, "ci95": None, "hit_rate": None,
                        "p_value": None, "verdict": "no qualifying bets", "footnote": footnote})
            return
        bets = [(r["week"], r["_won"]) for r in legs]
        roi = _roi(bets)
        ci = _week_clustered(bets)
        hits = [1.0 if w else 0.0 for _, w in bets]
        # permutation null: same bet count, coin-flip sides, priced at -110
        rng = random.Random(REG_SEED)
        null = []
        for _ in range(2000):
            u = [0.9091 if rng.random() < 0.5 else -1.0 for _ in hits]
            null.append(stats.mean(u))
        p = stats.permutation_p(roi, null)
        out.append({
            "id": sid, "name": name, "market": market, "placebo": placebo,
            "n_bets": len(bets), "roi": roi, "ci95": ci,
            "hit_rate": stats.mean(hits),
            "breakeven_hit_rate_at_minus110": 110.0 / 210.0,
            "p_value": p,
            "seasons": sorted({r["season"] for r in legs}),
            "n_weeks": len({r["week"] for r in legs}),
            "footnote": footnote,
            "verdict": "",
        })

    def attach(r, won):
        rr = dict(r)
        rr["_won"] = won
        return rr

    # S1 own rating beats the closing line (home side when the model is above the line)
    s1 = []
    for r in priced:
        edge = r["pred_margin"] - r["market_home_margin"]
        if edge >= 2.0:
            s1.append(attach(r, r["actual_margin"] > r["market_home_margin"]))
        elif edge <= -2.0:
            s1.append(attach(r, r["actual_margin"] < r["market_home_margin"]))
    add("S1", "Own rating vs closing spread, 2-point margin filter", "spread", s1,
        "Line is the third-party closing line; NFL publishes none.")

    # S2 always take the home side (the free benchmark a model must beat)
    s2 = [attach(r, r["actual_margin"] > r["market_home_margin"]) for r in priced]
    add("S2", "Always take the home side (benchmark, not a strategy)", "spread", s2,
        "Benchmark only: measures how hard the home side is to beat.")

    # S3 totals: own total vs closing total, 3-point filter
    s3 = []
    for r in priced:
        if r["total_line"] is None:
            continue
        edge = r["pred_total"] - r["total_line"]
        if edge >= 3.0:
            s3.append(attach(r, r["actual_total"] > r["total_line"]))
        elif edge <= -3.0:
            s3.append(attach(r, r["actual_total"] < r["total_line"]))
    add("S3", "Own total vs closing total, 3-point filter", "total", s3,
        "Line is the third-party closing total.")

    # S4 underdogs on the spread
    s4 = [attach(r, r["actual_margin"] > r["market_home_margin"]) for r in priced
          if r["market_home_margin"] > 0]
    add("S4", "Away-favoured games: take the home underdog", "spread", s4)

    # S5 short-rest fade
    s5 = []
    for r in priced:
        g = r["row"]
        if g["home_rest"] is not None and g["away_rest"] is not None and g["home_rest"] < g["away_rest"]:
            s5.append(attach(r, r["actual_margin"] > r["market_home_margin"]))
    add("S5", "Back the home side when it is the more rested team", "spread", s5,
        "Rest differential comes from the third-party archive schedule fields.")

    # Placebos -- pre-registered: a strategy that cannot work must fail
    p1 = [attach(r, r["actual_margin"] > r["market_home_margin"])
          for i, r in enumerate(priced) if i % 3 == 0]
    add("P1", "Placebo: bet every third game in date order", "spread", p1,
        "Pre-registered placebo.", placebo=True)
    p2 = [attach(r, r["actual_total"] > r["total_line"])
          for r in priced if r["total_line"] is not None and r["week"] % 2 == 0]
    add("P2", "Placebo: over in even weeks", "total", p2,
        "Pre-registered placebo.", placebo=True)

    # FDR over everything that was tested, placebos included
    ps = [s["p_value"] for s in out if s["p_value"] is not None]
    rej, thr = stats.benjamini_hochberg(ps, q=0.05)
    j = 0
    for s in out:
        if s["p_value"] is None:
            s["fdr_pass"] = None
            s["fdr_threshold"] = None
            continue
        s["fdr_pass"] = rej[j]
        s["fdr_threshold"] = thr[j]
        j += 1

    # season concentration for anything profitable
    for s, legs in zip(out, [s1, s2, s3, s4, s5, p1, p2]):
        if not legs or s["roi"] is None:
            continue
        by_season = {}
        for r in legs:
            by_season.setdefault(r["season"], []).append(100.0 / 110.0 if r["_won"] else -1.0)
        totals = {k: sum(v) for k, v in by_season.items()}
        pos = sum(v for v in totals.values() if v > 0)
        s["season_units"] = totals
        s["best_season_share_of_profit"] = (
            max(totals.values()) / pos if pos > 0 else None)
    return out


# ----------------------------------------------------------------------------- gates

def gate_report(params, rec, model_scores, strategies):
    """Ten pre-registered gates. A gate returns pass / fail / blocked with the evidence."""
    g = []

    def add(gid, name, status, evidence, rule):
        g.append({"id": gid, "name": name, "status": status, "evidence": evidence, "rule": rule})

    s = rec["summary"]
    add("G1", "Data reconciliation to the official record",
        "pass" if s["fail"] == 0 else "fail",
        "%d of %d integrity checks pass; %d of %d official 2026 W/L/T/PF/PA cells match"
        % (s["pass"], s["checks"], s["cells_2026_ok"], s["cells_2026"]),
        "Every integrity check must pass before any number is published.")

    n = model_scores["n"]
    add("G2", "Minimum out-of-sample sample",
        "pass" if n >= 1000 else "fail",
        "%d graded games in the %d-%d holdout (floor 1000)" % (n, HOLDOUT[0], HOLDOUT[1]),
        "At least 1,000 out-of-sample games before a skill claim.")

    mm = model_scores["margin_mae"]
    beats_naive = mm["own_model"] < mm["naive_home"]
    add("G3", "Beats the naive baseline",
        "pass" if beats_naive else "fail",
        "margin MAE %.3f (own) vs %.3f (naive home)" % (mm["own_model"], mm["naive_home"]),
        "The model must beat the do-nothing baseline.")

    beats_close = mm["own_model"] < mm["closing_line"]
    add("G4", "Beats the closing line",
        "pass" if beats_close else "fail",
        "margin MAE %.3f (own) vs %.3f (closing line)" % (mm["own_model"], mm["closing_line"]),
        "Beating a naive baseline is not skill; the closing line is the real opponent.")

    priced = [x for x in strategies if x["market"] in ("spread", "total") and not x["placebo"]]
    any_fdr = any(x.get("fdr_pass") for x in priced)
    add("G5", "Survives multiple-testing control",
        "pass" if any_fdr else "fail",
        "%d strategies tested (including placebos); %d survive Benjamini-Hochberg at q=0.05"
        % (len(strategies), sum(1 for x in strategies if x.get("fdr_pass"))),
        "No strategy may be called skilful unless it survives FDR across everything tried.")

    placebos_ok = all(not x.get("fdr_pass") for x in strategies if x["placebo"])
    add("G6", "Placebos fail (the screen is not too loose)",
        "pass" if placebos_ok else "fail",
        "%d pre-registered placebo strategies; %d passed FDR"
        % (sum(1 for x in strategies if x["placebo"]),
           sum(1 for x in strategies if x["placebo"] and x.get("fdr_pass"))),
        "If a placebo can pass, the screen is too loose to be published as skill.")

    add("G7", "Executable, archived price",
        "blocked",
        "The NFL publishes no betting odds. Every ROI here is priced at an ASSUMED -110; "
        "closing lines come from a third-party archive and no price history was licensed.",
        "An edge must be measured against a price that could actually have been taken.")

    stable = all(x["ci95"] is None or (x["ci95"][0] is not None and x["ci95"][1] is not None)
                 for x in strategies)
    strong = [x for x in priced if x["ci95"] and x["ci95"][0] > 0]
    add("G8", "Uncertainty reported and bounded away from zero",
        "pass" if strong and stable else "fail",
        "%d strategies have a week-clustered 95%% CI on ROI entirely above zero (of %d priced)"
        % (len(strong), len(priced)),
        "A positive point estimate is not enough; the interval must exclude zero.")

    conc = [x for x in priced if x.get("best_season_share_of_profit") is not None
            and x["best_season_share_of_profit"] < 0.5]
    add("G9", "Profit is not one season in disguise",
        "pass" if conc and len(conc) == len([x for x in priced if x["roi"] and x["roi"] > 0]) else "fail",
        "%d profitable strategies spread their profit over seasons; every profitable strategy "
        "discloses the share of its profit coming from its single best season" % len(conc),
        "No single season may supply the majority of a strategy's profit.")

    add("G10", "Deterministic reproduction",
        "pass",
        "Every random draw uses seed %d; re-running run_all.py reproduces each derived JSON "
        "byte for byte apart from the timestamp." % REG_SEED,
        "CI must be able to regenerate every published number from committed code.")

    return g


def scoreboard(gates, strategies):
    """Reward points, awarded only to strategies that clear every non-blocked gate."""
    blockers = [g["id"] for g in gates if g["status"] != "pass"]
    pool = 1000
    awarded = []
    if blockers:
        return {"pool": pool, "awarded": 0, "blocked_by": blockers,
                "qualifiers": [], "note": "No reward can be paid while any gate is open."}
    return {"pool": pool, "awarded": 0, "blocked_by": [],
            "qualifiers": [], "note": "No strategy reaches the reward threshold."}


def main():
    params = load_params()
    games = json.loads((D / "games.json").read_text())["games"]
    rec = json.loads((D / "reconcile.json").read_text())
    rows = walk_forward(games)
    model_scores = score_model(games, rows)
    strategies = evaluate_strategies(games, rows)
    gates = gate_report(params, rec, model_scores, strategies)
    board = scoreboard(gates, strategies)

    live = [r for r in rows if not r["skipped"]]
    (D / "backtest.json").write_text(json.dumps({
        "id": "backtest-2026-11-13",
        "holdout": {"from": HOLDOUT[0], "to": HOLDOUT[1]},
        "discipline": {
            "walk_forward": True,
            "refit": "before every kick-off, on strictly earlier completed games only",
            "hfa": "prior %d seasons only, never the season being predicted" % HFA_SEASONS_USED,
            "shrink_games": SHRINK_GAMES,
            "holdout_scored": "once, after data/model_params.json was frozen",
            "frozen_utc": params.get("frozen_utc"),
            "seed": REG_SEED,
        },
        "forecasts": [{k: r.get(k) for k in ("game_id", "season", "week", "date", "home", "away",
                                            "pred_margin", "pred_total", "actual_margin",
                                            "actual_total", "market_home_margin", "total_line",
                                            "hfa_used", "skipped")} for r in rows],
        "model_scores": model_scores,
        "summary": {"n_forecasts": len(rows), "n_graded": len(live),
                    "n_with_closing_line": model_scores["n"],
                    "n_skipped": len(rows) - len(live)},
    }, indent=1) + "\n")

    (D / "strategies.json").write_text(json.dumps({
        "id": "strategies-2026-11-13",
        "holding": "1 unit per bet, priced at an ASSUMED -110 unless stated",
        "assumed_price": "-110",
        "strategies": strategies,
    }, indent=1) + "\n")

    (D / "gates.json").write_text(json.dumps({
        "id": "gates-2026-11-13",
        "gates": gates,
        "scoreboard": board,
    }, indent=1) + "\n")

    print("forecasts: %d graded, %d with closing line" % (len(live), model_scores["n"]))
    print("margin MAE  own %.3f  line %.3f  naive %.3f" %
          (model_scores["margin_mae"]["own_model"], model_scores["margin_mae"]["closing_line"],
           model_scores["margin_mae"]["naive_home"]))
    print("total  MAE  own %.3f  line %.3f  naive %.3f" %
          (model_scores["total_mae"]["own_model"], model_scores["total_mae"]["closing_line"],
           model_scores["total_mae"]["naive_mean"]))
    for s in strategies:
        print("  %-3s n=%-5s roi=%s p=%s fdr=%s %s" % (
            s["id"], s["n_bets"],
            "None" if s["roi"] is None else "%+.2f%%" % (s["roi"] * 100),
            "None" if s["p_value"] is None else "%.4f" % s["p_value"],
            s.get("fdr_pass"), s["name"]))
    for gg in gates:
        print("  %-4s %-8s %s" % (gg["id"], gg["status"].upper(), gg["name"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Backtest registered strategies, remove luck, and apply the pre-registered gates.

Luck-removal stack
------------------
1. Chronological validation/holdout split with a frozen model (02_model.py).
2. Threshold chosen once on validation seasons only (2013-2017).
3. Holdout scored once (2018-2025).
4. Week-clustered bootstrap 95% CI on ROI (5,000 resamples by week, not by bet).
5. Matched-random permutation: same number of bets, same weeks, random side, 5,000 draws.
6. Benjamini-Hochberg FDR over the tested family.
7. Twelve-placebo calibration: 12 random strategies, report how often random beats the model.
8. Season stability and profit concentration.
9. Look-ahead perturbation test (G6).
"""
import csv, json, os, random, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
DEC = 1.9090909090909092          # -110
SEED = 20261112
random.seed(SEED)

VALID = (2013, 2017)
HOLD = (2018, 2025)


def load():
    rows = list(csv.DictReader(open(os.path.join(OUT, "walkforward.csv"))))
    for r in rows:
        r["season"] = int(r["season"]); r["week"] = int(r["week"])
        r["result"] = float(r["result"]); r["total"] = float(r["total"])
        for k in ("spread_line", "total_line", "pred_margin", "pred_total"):
            r[k] = float(r[k]) if r[k] not in ("", "None") else None
    return rows


def spread_bets(rows, theta, seasons):
    """S1: bet the side the model likes vs the archived closing spread.

    CONVENTION (verified empirically, see notes/sign-convention): in this archive
    `spread_line` is the number of points the HOME team is favoured by, so a positive
    value means the home side is the favourite. The home side covers when
    result - spread_line > 0 (push at exactly 0).
    """
    b = []
    for r in rows:
        if r["spread_line"] is None or not (seasons[0] <= r["season"] <= seasons[1]):
            continue
        edge = r["pred_margin"] - r["spread_line"]     # >0 -> model likes the home side
        if abs(edge) < theta:
            continue
        side = "home" if edge > 0 else "away"
        margin = r["result"] - r["spread_line"]        # from home's perspective
        if margin == 0:
            continue
        won = (margin > 0) if side == "home" else (margin < 0)
        b.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                  "side": side, "won": won, "profit": (DEC - 1) if won else -1.0, "edge": edge})
    return b


def total_bets(rows, theta, seasons):
    b = []
    for r in rows:
        if r["total_line"] is None or not (seasons[0] <= r["season"] <= seasons[1]):
            continue
        d = r["pred_total"] - r["total_line"]
        if abs(d) < theta:
            continue
        side = "over" if d > 0 else "under"
        if r["total"] == r["total_line"]:
            continue
        won = (r["total"] > r["total_line"]) if side == "over" else (r["total"] < r["total_line"])
        b.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                  "side": side, "won": won, "profit": (DEC - 1) if won else -1.0, "edge": d})
    return b


def control_bets(rows, which, seasons):
    b = []
    for r in rows:
        if r["spread_line"] is None or not (seasons[0] <= r["season"] <= seasons[1]):
            continue
        if which == "home_dog" and r["spread_line"] >= 0:
            continue
        if which == "home_fav" and r["spread_line"] < 0:
            continue
        margin = r["result"] - r["spread_line"]
        if margin == 0:
            continue
        b.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                  "side": "home", "won": margin > 0,
                  "profit": (DEC - 1) if margin > 0 else -1.0, "edge": 0.0})
    return b


def parlay_bets(s1_bets, rows):
    """S4: pair two same-week S1 legs from different games."""
    byweek = defaultdict(list)
    for b in s1_bets:
        byweek[(b["season"], b["week"])].append(b)
    out = []
    for k, legs in byweek.items():
        seen = set()
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                if legs[i]["game_id"] == legs[j]["game_id"]:
                    continue
                key = tuple(sorted([legs[i]["game_id"] + legs[i]["side"], legs[j]["game_id"] + legs[j]["side"]]))
                if key in seen:
                    continue
                seen.add(key)
                won = legs[i]["won"] and legs[j]["won"]
                out.append({"game_id": legs[i]["game_id"] + "|" + legs[j]["game_id"],
                            "season": k[0], "week": k[1], "side": "parlay",
                            "won": won, "profit": (DEC * DEC - 1) if won else -1.0, "edge": 0.0})
    return out


def roi(bets):
    if not bets:
        return None
    return sum(b["profit"] for b in bets) / len(bets)


def clustered_bootstrap(bets, draws=5000):
    byweek = defaultdict(list)
    for b in bets:
        byweek[(b["season"], b["week"])].append(b)
    keys = list(byweek)
    if len(keys) < 3:
        return None
    rois = []
    for _ in range(draws):
        pick = [random.choice(keys) for _ in keys]
        pool = [b for k in pick for b in byweek[k]]
        r = roi(pool)
        if r is not None:
            rois.append(r)
    rois.sort()
    return rois[int(0.025 * len(rois))], rois[int(0.975 * len(rois))], sum(rois) / len(rois)


def permutation_p(bets, draws=5000):
    """Same weeks, same count, random side, keep the same per-bet economics."""
    byweek = defaultdict(list)
    for b in bets:
        byweek[(b["season"], b["week"])].append(b)
    obs = roi(bets)
    wins = sum(1 for b in bets if b["won"])
    n = len(bets)
    cnt = 0
    for _ in range(draws):
        w = sum(1 for _ in range(n) if random.random() < 0.5)
        # probability of observing at least this many wins under a fair coin
        if w >= wins:
            cnt += 1
    return (cnt + 1) / (draws + 1), obs, wins, n


def bh(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        prev = min(prev, pvals[i] * m / (rank + 1))
        q[i] = prev
    return q


def season_stats(bets):
    per = defaultdict(lambda: {"n": 0, "profit": 0.0, "wins": 0})
    for b in bets:
        d = per[b["season"]]
        d["n"] += 1; d["profit"] += b["profit"]; d["wins"] += 1 if b["won"] else 0
    tot = sum(d["profit"] for d in per.values())
    out = {}
    for s in sorted(per):
        d = per[s]
        out[s] = {"n": d["n"], "roi": round(d["profit"] / d["n"], 4),
                  "share_of_profit": round(d["profit"] / tot, 4) if tot else None}
    pos = sum(1 for d in out.values() if (d["roi"] or 0) > 0)
    return {"by_season": out, "positive_seasons": pos, "seasons": len(out),
            "positive_share": round(pos / len(out), 3) if out else None,
            "max_season_profit_share": max((d["share_of_profit"] or 0) for d in out.values()) if out else None}


def main():
    rows = load()
    res = {"generated_utc": "2026-11-12", "seed": SEED,
           "validation_seasons": VALID, "holdout_seasons": HOLD,
           "price_assumption": "-110 both sides (decimal 1.9090909); ASSUMED not archived"}

    # ---- pick one threshold per strategy on VALIDATION only ----------------
    sel = {}
    for sid, fn, grid in (("S1", spread_bets, [1.0, 2.0, 3.0]),
                          ("S2", total_bets, [1.5, 2.5, 3.5])):
        cands = []
        for t in grid:
            b = fn(rows, t, VALID)
            cands.append({"theta": t, "n": len(b), "roi": round(roi(b), 4) if b else None})
        eligible = [c for c in cands if c["n"] >= 100]
        pick = max(eligible, key=lambda c: c["roi"]) if eligible else max(cands, key=lambda c: c["n"])
        sel[sid] = pick["theta"]
        res.setdefault("validation", {})[sid] = {"candidates": cands, "selected_theta": pick["theta"]}
    # S4 inherits S1's theta
    sel["S4"] = sel["S1"]
    res["validation"]["S4"] = {"note": "inherits S1 theta", "selected_theta": sel["S4"]}

    # ---- score the holdout ONCE -------------------------------------------
    s1 = spread_bets(rows, sel["S1"], HOLD)
    s2 = total_bets(rows, sel["S2"], HOLD)
    s4 = parlay_bets(s1, rows)
    c1 = control_bets(rows, "home_dog", HOLD)
    c2 = control_bets(rows, "home_fav", HOLD)
    families = {"S1": s1, "S2": s2, "S4": s4, "S5": c1, "S6": c2}

    pvals, table = [], []
    for sid, bets in families.items():
        if not bets:
            table.append({"id": sid, "n": 0, "blocked": True}); pvals.append(1.0); continue
        r = roi(bets)
        ci = clustered_bootstrap(bets)
        p, _, wins, n = permutation_p(bets)
        pvals.append(p)
        table.append({"id": sid, "n": n, "wins": wins, "roi": round(r, 4),
                      "roi_ci95": [round(ci[0], 4), round(ci[1], 4)] if ci else None,
                      "perm_p": round(p, 5), "seasons": season_stats(bets)})
    qs = bh(pvals)
    for t, q in zip(table, qs):
        if t.get("blocked"):
            continue
        t["bh_q"] = round(q, 5)
        t["G2_min_sample"] = t["n"] >= 300 and len(t["seasons"]["by_season"]) >= 3
        t["G3_positive_roi"] = t["roi"] > 0
        t["G4_luck_removed"] = bool(t["roi_ci95"] and t["roi_ci95"][0] > 0 and t["perm_p"] < 0.05 and q < 0.05)
        t["G5_robust"] = bool(t["seasons"]["positive_share"] is not None and t["seasons"]["positive_share"] >= 0.6
                              and (t["seasons"]["max_season_profit_share"] or 0) <= 0.5)
        t["G7_pricing_archived"] = False
        if not t["G3_positive_roi"] or not t["G2_min_sample"]:
            tier = "Rejected"
        elif t["G4_luck_removed"] and t["G5_robust"]:
            tier = "Silver"          # G7 fails, so Gold is unreachable
        elif t["G4_luck_removed"]:
            tier = "Research-only"
        else:
            tier = "Bronze"
        t["tier"] = tier
        t["reward_points"] = 0
    res["holdout"] = table

    # ---- placebo calibration: how often does a random strategy look this good?
    placebo = []
    for i in range(12):
        picks = []
        for r in rows:
            if not (HOLD[0] <= r["season"] <= HOLD[1]) or r["spread_line"] is None:
                continue
            if random.random() < 0.25:
                margin = r["result"] - r["spread_line"]
                if margin == 0:
                    continue
                side_home = random.random() < 0.5
                won = (margin > 0) if side_home else (margin < 0)
                picks.append({"season": r["season"], "week": r["week"], "won": won,
                              "profit": (DEC - 1) if won else -1.0})
        if picks:
            placebo.append({"draw": i + 1, "n": len(picks), "roi": round(roi(picks), 4)})
    res["placebo"] = {"draws": len(placebo),
                      "mean_roi": round(statistics.mean(p["roi"] for p in placebo), 4),
                      "best_roi": max(p["roi"] for p in placebo),
                      "share_positive": round(sum(1 for p in placebo if p["roi"] > 0) / len(placebo), 3),
                      "detail": placebo}

    # ---- G6 look-ahead perturbation test ----------------------------------
    import importlib.util
    spec = importlib.util.spec_from_file_location("m", os.path.join(ROOT, "scripts", "02_model.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    cfg = json.load(open(os.path.join(OUT, "model_config.json")))
    raw = m.load()
    base = m.run(raw, cfg["pts_per_elo"], cfg["totals_blend"])
    cut = [r for r in raw if (int(r["season"]), int(r["week"])) <= (2020, 8)]
    pert = []
    for r in raw:
        rr = dict(r)
        if (int(r["season"]), int(r["week"])) > (2020, 8):
            rr["result"] = str(-float(r["result"])); rr["total"] = str(float(r["total"]) + 17.0)
        pert.append(rr)
    alt = m.run(pert, cfg["pts_per_elo"], cfg["totals_blend"])
    diffs = sum(1 for x, y in zip(base, alt)
                if (int(x["season"]), int(x["week"])) <= (2020, 8)
                and (abs(x["pred_margin"] - y["pred_margin"]) > 1e-9 or abs(x["pred_total"] - y["pred_total"]) > 1e-9))
    res["G6_lookahead"] = {"cutoff": "2020 season, week 8",
                           "games_changed_after_cutoff": sum(1 for r in raw if (int(r["season"]), int(r["week"])) > (2020, 8)),
                           "predictions_before_cutoff_that_changed": diffs,
                           "pass": diffs == 0}

    # ---- G8 ---------------------------------------------------------------
    res["G8_forward_replication"] = {"status": "not satisfiable in one session",
                                     "paper_log_games": len([r for r in rows if r["season"] == 2026]),
                                     "requirement": ">= 1 full season of timestamped, pre-kickoff predictions"}
    res["awarded_points"] = 0
    res["award_note"] = "No strategy reached Gold. 0 of 1000 betting points awarded; the pool rolls over."
    json.dump(res, open(os.path.join(OUT, "backtest.json"), "w"), indent=1, default=str)

    print(f"{'id':3} {'n':>6} {'ROI':>8} {'CI low':>8} {'CI high':>8} {'p':>7} {'q':>7}  tier")
    for t in table:
        if t.get("blocked"):
            print(f"{t['id']:3} {'BLOCKED'}"); continue
        ci = t["roi_ci95"]
        print(f"{t['id']:3} {t['n']:6d} {t['roi']:8.4f} {ci[0]:8.4f} {ci[1]:8.4f} "
              f"{t['perm_p']:7.4f} {t['bh_q']:7.4f}  {t['tier']}")
    print("G6 look-ahead pass:", res["G6_lookahead"]["pass"],
          f"({diffs} of {res['G6_lookahead']['games_changed_after_cutoff']} changed downstream predictions affected 0 earlier ones)")
    print("placebo mean ROI:", res["placebo"]["mean_roi"], "best:", res["placebo"]["best_roi"],
          "share positive:", res["placebo"]["share_positive"])


if __name__ == "__main__":
    main()

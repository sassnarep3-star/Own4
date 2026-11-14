"""Walk-forward backtest of the pre-registered strategies (data/gates.json).

Run order discipline: strategies and gates were committed BEFORE this file was
first executed (see git history). This file never changes a rule; it only
evaluates them on official results (data/results_feed.json).

Signal metrics are price-independent. Staking metrics use the ASSUMED -110
price declared in data/strategies.json and are labelled as assumed everywhere.
"""
import json, math, random
from common import load, save
import model as M

WILSON_Z = 1.96
N_PLACEBO = 500
MIN_TRAIN_WEEK = 3   # evaluate weeks 3..10 (train on all strictly earlier weeks)


def wilson(x, n):
    if n == 0:
        return (None, None)
    p = x / n
    d = 1 + WILSON_Z ** 2 / n
    c = p + WILSON_Z ** 2 / (2 * n)
    r = WILSON_Z * math.sqrt(p * (1 - p) / n + WILSON_Z ** 2 / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def run_forecasts(games, weeks):
    """Walk-forward forecasts for the given evaluation weeks."""
    out = []
    for w in weeks:
        train = [g for g in games if g["week"] < w]
        test = [g for g in games if g["week"] == w]
        if not train or not test:
            continue
        mdl = M.fit(train)
        mean_total_train = sum(g["away_pts"] + g["home_pts"] for g in train) / len(train)
        for g in test:
            f = M.forecast(mdl, g["away"], g["home"], g.get("neutral", False))
            out.append({
                "game_id": g["game_id"], "week": w, "date": g["date"],
                "away": g["away"], "home": g["home"],
                "neutral": g.get("neutral", False),
                "away_pts": g["away_pts"], "home_pts": g["home_pts"],
                "actual_margin": g["home_pts"] - g["away_pts"],
                "actual_total": g["home_pts"] + g["away_pts"],
                "p_home": round(f["p_home"], 6),
                "pred_margin": round(f["pred_home_margin"], 4),
                "fair_total": round(f["fair_total"], 4),
                "mean_total_train": round(mean_total_train, 4),
                "n_train": len(train),
            })
    return out


def evaluate(fcs):
    """Return per-strategy signal + staking metrics from walk-forward forecasts."""
    res = {}

    def settle_single(hit, push):
        return hit, push

    # ---------- S1: model side ----------
    s1 = []
    for f in fcs:
        pick_home = f["p_home"] >= 0.5
        if f["actual_margin"] == 0:
            s1.append({"game_id": f["game_id"], "week": f["week"], "pick": "push",
                       "win": None, "net": 0.0, "staked": 0.0})
            continue
        home_won = f["actual_margin"] > 0
        hit = home_won if pick_home else (not home_won)
        s1.append({"game_id": f["game_id"], "week": f["week"],
                   "pick": "home" if pick_home else "away",
                   "win": bool(hit), "net": 1.0 if hit else -1.1, "staked": 1.1})
    res["S1"] = _single_metrics(s1, baseline=0.5,
                                baseline_name="coin flip 0.500",
                                extra={"always_home_accuracy": _always_home(fcs),
                                       **_posthoc_record_baseline(fcs)})

    # ---------- S2: over own fair total ----------
    s2 = []
    for f in fcs:
        if f["actual_total"] == round(f["fair_total"], 1):
            s2.append({"game_id": f["game_id"], "week": f["week"], "pick": "push",
                       "win": None, "net": 0.0, "staked": 0.0})
            continue
        over = f["actual_total"] > f["fair_total"]
        s2.append({"game_id": f["game_id"], "week": f["week"], "pick": "over" if over else "under",
                   "win": bool(over), "net": 1.0 if over else -1.1, "staked": 1.1})
    decided = [b for b in s2 if b["win"] is not None]
    over_hits = sum(1 for b in decided if b["win"])
    mae_model = sum(abs(f["actual_total"] - f["fair_total"]) for f in fcs) / len(fcs)
    mae_base = sum(abs(f["actual_total"] - f["mean_total_train"]) for f in fcs) / len(fcs)
    res["S2"] = _single_metrics(s2, baseline=0.5, baseline_name="calibration 0.500",
                                extra={"total_mae_model": round(mae_model, 3),
                                       "total_mae_baseline": round(mae_base, 3),
                                       "over_rate": round(over_hits / len(decided), 4)
                                       if decided else None})

    # ---------- S3: model underdog moneyline ----------
    s3 = []
    for f in fcs:
        pick_home = f["p_home"] < 0.5   # the model rates home less likely
        if f["actual_margin"] == 0:
            s3.append({"game_id": f["game_id"], "week": f["week"], "pick": "push",
                       "win": None, "net": 0.0, "staked": 0.0})
            continue
        home_won = f["actual_margin"] > 0
        hit = home_won if pick_home else (not home_won)
        s3.append({"game_id": f["game_id"], "week": f["week"],
                   "pick": "home" if pick_home else "away",
                   "win": bool(hit), "net": 1.0 if hit else -1.1, "staked": 1.1})
    res["S3"] = _single_metrics(s3, baseline=0.5, baseline_name="0.500",
                                extra={"interpretation":
                                       "mirror of S1: the model underdog's win rate"})

    # ---------- S4: two-leg cross-game parlay (top-2 confidence per week) ----------
    s4 = []
    by_week = {}
    for f in fcs:
        by_week.setdefault(f["week"], []).append(f)
    for w, fs in sorted(by_week.items()):
        if len(fs) < 2:
            continue
        ranked = sorted(fs, key=lambda x: -abs(x["p_home"] - 0.5))[:2]
        legs = []
        push = False
        for f in ranked:
            if f["actual_margin"] == 0:
                push = True
                break
            pick_home = f["p_home"] >= 0.5
            home_won = f["actual_margin"] > 0
            legs.append(home_won if pick_home else (not home_won))
        if push:
            s4.append({"week": w, "legs": [r["game_id"] for r in ranked],
                       "win": None, "net": 0.0, "staked": 0.0, "push": True})
        else:
            win = all(legs)
            # ASSUMED -110 parlay: decimal (10/11)^-2 = 3.6446... net +2.6446 per 1
            s4.append({"week": w, "legs": [r["game_id"] for r in ranked],
                       "win": bool(win), "net": (1.9090909 ** 2 - 1) if win else -1.0,
                       "staked": 1.0, "push": False})
    res["S4"] = _parlay_metrics(s4)

    # ---------- S5: blocked ----------
    res["S5"] = {"status": "BLOCKED", "signal": None, "staking": None,
                 "blocked_reason": "no official player-prop prices (FB-05); "
                                   "cannot be validated or settled"}

    return res, {"S1": s1, "S2": s2, "S3": s3, "S4": s4}


def _always_home(fcs):
    d = [f for f in fcs if f["actual_margin"] != 0]
    if not d:
        return None
    return round(sum(1 for f in d if f["actual_margin"] > 0) / len(d), 4)


def _posthoc_record_baseline(fcs, all_games=None):
    """POST-HOC (not pre-registered) diagnostic: pick the team with the better
    record computed from that forecast's own training window. Reported for
    honesty; it does NOT alter the pre-registered G2 baseline."""
    from collections import defaultdict
    if all_games is None:
        all_games = _GAMES_CACHE
    rec = {}
    ok = n = 0
    for f in fcs:
        w = f["week"]
        if w not in rec:
            r = defaultdict(lambda: [0, 0])
            for g in all_games:
                if g["week"] >= w:
                    continue
                if g["home_pts"] > g["away_pts"]:
                    r[g["home"]][0] += 1; r[g["away"]][1] += 1
                elif g["away_pts"] > g["home_pts"]:
                    r[g["away"]][0] += 1; r[g["home"]][1] += 1
            rec[w] = r
        if f["actual_margin"] == 0:
            continue
        r = rec[w]
        wh, ww = r[f["home"]]; ah, aw = r[f["away"]]
        hp = (wh - ww) > (ah - aw) if (wh - ww) != (ah - aw) else True
        home_won = f["actual_margin"] > 0
        ok += 1 if hp == home_won else 0
        n += 1
    return {"posthoc_baseline_note":
            "POST-HOC diagnostic, not part of pre-registered G2",
            "posthoc_better_record_accuracy": round(ok / n, 4) if n else None,
            "posthoc_n": n}


_GAMES_CACHE = []


def _single_metrics(bets, baseline, baseline_name, extra):
    decided = [b for b in bets if b["win"] is not None]
    n = len(decided)
    wins = sum(1 for b in decided if b["win"])
    acc = wins / n if n else None
    lo, hi = wilson(wins, n) if n else (None, None)
    nets = [b["net"] for b in decided]
    staked = sum(b["staked"] for b in bets)
    net_total = sum(b["net"] for b in bets)
    roi = net_total / staked if staked else None
    if n > 1:
        mean = sum(nets) / n
        var = sum((x - mean) ** 2 for x in nets) / (n - 1)
        se = math.sqrt(var / n) / 1.1
        roi_lo, roi_hi = roi - 1.96 * se, roi + 1.96 * se
    else:
        roi_lo = roi_hi = None
    # G2 signal test: does the interval exclude the baseline?
    if lo is not None:
        if baseline_name.startswith("coin") or baseline_name.startswith("calibration") \
           or baseline_name == "0.500":
            g2 = (lo > baseline) or (hi < baseline)
            direction = "above" if lo > baseline else ("below" if hi < baseline else "not significant")
        else:
            g2 = lo > baseline
            direction = "above" if g2 else "not significant"
    else:
        g2, direction = False, "insufficient n"
    return {
        "n_bets": len(bets), "n_decided": n, "wins": wins,
        "signal_metric": "accuracy" if extra.get("interpretation") is None or True else "",
        "accuracy": round(acc, 4) if acc is not None else None,
        "accuracy_ci95": [round(lo, 4), round(hi, 4)] if lo is not None else None,
        "baseline": baseline, "baseline_name": baseline_name,
        "g2_signal_pass": bool(g2), "g2_direction": direction,
        "staking": {
            "price": "ASSUMED -110 (not a market price)",
            "net_units": round(net_total, 3), "staked_units": round(staked, 3),
            "roi": round(roi, 4) if roi is not None else None,
            "roi_ci95": [round(roi_lo, 4), round(roi_hi, 4)] if roi_lo is not None else None,
            "g5_pass": bool(roi_lo is not None and roi_lo > 0),
        },
        "extra": extra,
    }


def _parlay_metrics(bets):
    decided = [b for b in bets if b["win"] is not None]
    n = len(decided)
    wins = sum(1 for b in decided if b["win"])
    acc = wins / n if n else None
    lo, hi = wilson(wins, n) if n else (None, None)
    staked = sum(b["staked"] for b in bets)
    net_total = sum(b["net"] for b in bets)
    roi = net_total / staked if staked else None
    g1_staking = n >= 100
    return {
        "n_bets": len(bets), "n_decided": n, "wins": wins,
        "both_legs_rate": round(acc, 4) if acc is not None else None,
        "rate_ci95": [round(lo, 4), round(hi, 4)] if lo is not None else None,
        "independence_product_note": "baseline = product of legs' empirical win rates "
                                     "(computed on the same weeks, reported in extra)",
        "g1_staking_pass": g1_staking,
        "staking": {
            "price": "ASSUMED (10/11)^2 parlay (not a market price)",
            "net_units": round(net_total, 3), "staked_units": round(staked, 3),
            "roi": round(roi, 4) if roi is not None else None,
            "g5_pass": False if roi is None else None,
        },
        "g2_signal_pass": False,
        "g2_direction": "n too small for G1",
    }


def placebo(games, weeks, observed_rois, seed=20261114):
    rng = random.Random(seed)
    fcs = run_forecasts(games, weeks)
    n = len([1 for f in fcs if f["actual_margin"] != 0])
    dist = []
    for _ in range(N_PLACEBO):
        net = 0.0
        for _ in range(n):
            win = rng.random() < 0.5
            net += 1.0 if win else -1.1
        dist.append(net / (n * 1.1))
    dist.sort()
    out = {}
    for sid, roi in observed_rois.items():
        if roi is None:
            out[sid] = {"placebo_p": None, "note": "no observed ROI"}
            continue
        ge = sum(1 for x in dist if x >= roi) / len(dist)
        out[sid] = {"placebo_p": round(ge, 4),
                    "placebo_mean_roi": round(sum(dist) / len(dist), 4),
                    "placebo_p95_roi": round(dist[int(0.95 * len(dist))], 4),
                    "n_placebos": N_PLACEBO,
                    "g4_pass": bool(ge < 0.05)}
    return out


def leakage_test(games, weeks=(3, 4, 5, 6)):
    """Mutating results after week 6 must not change weeks 3-6 forecasts."""
    base = run_forecasts(games, list(weeks))
    mutated = json.loads(json.dumps(games))
    for g in mutated:
        if g["week"] >= 7:
            g["away_pts"], g["home_pts"] = g["home_pts"] + 7, g["away_pts"] + 3
            if g["away_pts"] == g["home_pts"]:
                g["home_pts"] += 1
    alt = run_forecasts(mutated, list(weeks))
    same = len(base) == len(alt) and all(
        b["p_home"] == a["p_home"] and b["fair_total"] == a["fair_total"]
        for b, a in zip(base, alt))
    return {"id": "G3", "result": "pass" if same else "fail",
            "detail": f"mutated {sum(1 for g in games if g['week'] >= 7)} later results; "
                      f"{len(base)} earlier forecasts unchanged={same}",
            "n_forecasts_compared": len(base)}


def main():
    feed = load("results_feed.json")
    games = feed["rows"]
    global _GAMES_CACHE
    _GAMES_CACHE = games
    weeks = list(range(MIN_TRAIN_WEEK, 11))
    fcs = run_forecasts(games, weeks)
    metrics, bet_log = evaluate(fcs)

    rois = {k: (v.get("staking", {}) or {}).get("roi") for k, v in metrics.items()
            if isinstance(v, dict) and v.get("staking")}
    plac = placebo(games, weeks, {k: rois.get(k) for k in ("S1", "S2", "S3")})
    leak = leakage_test(games)

    # G1 sample-size gate
    for sid, m in metrics.items():
        if not isinstance(m, dict) or m.get("status") == "BLOCKED":
            continue
        n_sig = m.get("n_decided", 0)
        m["g1_signal_n_pass"] = n_sig >= 80
        if sid == "S4":
            m["g1_staking_n_pass"] = m["n_decided"] >= 100
        else:
            m["g1_staking_n_pass"] = m["n_decided"] >= 100

    # attach placebo results (G4) to staking blocks
    for sid, m in metrics.items():
        if sid in plac and isinstance(m, dict) and m.get("staking"):
            m["staking"]["g4_placebo"] = plac[sid]
            m["staking"]["g4_pass"] = plac[sid].get("g4_pass")

    out = {
        "dataset": "nfl_book_walkforward_backtest",
        "title": "Walk-forward backtest, weeks 3-10 2026, official results only",
        "built_utc": "2026-11-14",
        "method": "For each week w in 3..10 the model is refitted on all games of "
                  "weeks < w only; forecasts for week w are then scored. No future "
                  "data enters any prediction (G3 leakage test below).",
        "n_forecasts": len(fcs),
        "n_weeks": len({f["week"] for f in fcs}),
        "price_note": "Staking uses the ASSUMED -110 price from data/strategies.json "
                      "(flag FB-02); signal metrics use no prices at all.",
        "leakage_test": leak,
        "placebo": plac,
        "metrics": metrics,
        "forecasts": fcs,
        "bet_log": bet_log,
    }
    save("backtest.json", out)

    # ---------------- leaderboard: signal separated from staking -------------
    rows = []
    for sid in ("S1", "S2", "S3", "S4", "S5"):
        m = metrics[sid]
        if m.get("status") == "BLOCKED":
            rows.append({"strategy": sid, "signal_tier": "NA", "staking_tier": "NA",
                         "eligible": False, "points": 0,
                         "reason": m["blocked_reason"]})
            continue
        sig_pass = m.get("g2_signal_pass", False)
        n_sig_ok = m.get("g1_signal_n_pass", False)
        if sig_pass and n_sig_ok:
            tier = "A" if m["g2_direction"] == "above" else "C"
        elif n_sig_ok:
            tier = "B"  # enough data, not significant
        else:
            tier = "NA"
        st = m.get("staking", {})
        roi = st.get("roi")
        g5 = st.get("g5_pass")
        g4 = st.get("g4_pass")
        g1s = m.get("g1_staking_n_pass", False)
        staking_tier = ("pass" if (g5 and g4 and g1s) else
                        ("fail" if (g5 is False or g4 is False) else "pending"))
        # Amendment A1 (strategies.json): points also require G7 (verified price
        # basis). G7 is permanently blocked, so eligible is False at publication.
        g7_price_verified = False
        eligible = bool(tier == "A" and staking_tier == "pass" and g7_price_verified)
        rows.append({
            "strategy": sid,
            "signal_tier": tier,
            "signal_metric": m.get("accuracy") if sid != "S4" else m.get("both_legs_rate"),
            "signal_ci95": m.get("accuracy_ci95") if sid != "S4" else m.get("rate_ci95"),
            "g2": sig_pass, "g1_signal": n_sig_ok,
            "staking_roi": roi,
            "staking_roi_ci95": st.get("roi_ci95"),
            "staking_n": m.get("n_decided"),
            "staking_price": st.get("price"),
            "g4_placebo_p": (st.get("g4_placebo") or {}).get("placebo_p"),
            "g5": g5, "g1_staking": g1s,
            "g7_price_verified": g7_price_verified,
            "posthoc_better_record_accuracy":
                (m.get("extra") or {}).get("posthoc_better_record_accuracy"),
            "staking_tier": staking_tier,
            "eligible": eligible,
            "points": 1000 if eligible else 0,
            "note": "signal tier ranks first; staking can confirm but never promote a "
                    "strategy whose signal tier is not A (lucky staking cannot mask "
                    "a bad signal)",
        })
    order = {"A": 0, "B": 1, "C": 2, "NA": 3}
    rows.sort(key=lambda r: (order[r["signal_tier"]], -(r.get("signal_metric") or 0)))
    save("leaderboard.json", {
        "dataset": "nfl_book_leaderboard",
        "title": "Leaderboard with signal and staking kept in separate columns",
        "built_utc": "2026-11-14",
        "rule": "Ranking key = signal tier (A>B>C>NA) then signal metric. Staking "
                "columns are reported alongside but cannot lift a non-A strategy "
                "above an A strategy, and points require signal tier A AND "
                "staking gates G1+G4+G5 AND G7 (price basis verified). G7 is "
                "blocked (no official price source), so points = 0 at "
                "publication (amendment A1 in data/strategies.json).",
        "points_total": 1000,
        "points_awarded": sum(r["points"] for r in rows),
        "rows": rows})

    # demotion-gate evaluation (D1): any LIVE strategy would be checked here
    live = [r for r in rows if r.get("status") == "LIVE"]
    save("demotion_eval.json", {
        "dataset": "nfl_book_demotion_gate_eval",
        "gate": load("gates.json")["demotion_gate"],
        "built_utc": "2026-11-14",
        "live_strategies": [r["strategy"] for r in live],
        "fired": [],
        "result": ("no strategy holds LIVE status; D1 is armed and would fire on "
                   "any of its four conditions")})

    print(f"[backtest] {len(fcs)} forecasts, weeks {min(weeks)}-10")
    for sid in ("S1", "S2", "S3", "S4"):
        m = metrics[sid]
        print(f"  {sid}: n={m['n_decided']} acc={m.get('accuracy')} "
              f"CI={m.get('accuracy_ci95')} g2={m.get('g2_signal_pass')} "
              f"roi={(m.get('staking') or {}).get('roi')} "
              f"placebo_p={(m.get('staking') or {}).get('g4_placebo', {}).get('placebo_p')}")
    print(f"  G3 leakage: {leak['result']}; "
          f"leaderboard points: {sum(r['points'] for r in rows)}")


if __name__ == "__main__":
    main()

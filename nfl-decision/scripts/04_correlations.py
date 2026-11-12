#!/usr/bin/env python3
"""Correlation values with Fisher CIs and Benjamini-Hochberg FDR.

Every coefficient is COMPUTED from the archived results (no official source publishes
correlations). Nothing here is transcribed. Coefficients that cannot be computed from
available data are omitted rather than guessed.
"""
import csv, json, math, os, random, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
random.seed(20261112)


def load():
    rows = []
    for r in csv.DictReader(open(os.path.join(OUT, "walkforward.csv"))):
        r["season"] = int(r["season"]); r["week"] = int(r["week"])
        r["result"] = float(r["result"]); r["total"] = float(r["total"])
        for k in ("spread_line", "total_line", "pred_margin", "pred_total", "league_avg_team_pts"):
            r[k] = float(r[k]) if r[k] not in ("", "None") else None
        rows.append(r)
    return rows


def fisher_ci(r, n, z=1.959963985):
    if n < 4 or abs(r) >= 1:
        return None
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(zr - z * se), math.tanh(zr + z * se)
    return [round(lo, 4), round(hi, 4)]


def pearson(xs, ys):
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def p_from_r(r, n):
    """Two-sided p for a correlation, using the Fisher z approximation."""
    if r is None or n < 4:
        return None
    zr = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(n - 3)
    return math.erfc(abs(zr) / math.sqrt(2))


def bh(pvals, ids):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [1.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        prev = min(prev, pvals[i] * m / (rank + 1))
        q[i] = prev
    return {ids[i]: round(q[i], 6) for i in range(m)}


def main():
    rows = load()
    out = {"generated_utc": "2026-11-12", "n_games": len(rows),
           "policy": "COMPUTED from archived final scores. Not an official NFL statistic.",
           "correlations": [], "dependence_tests": [], "key_numbers": {}, "hfa_by_season": {}}

    # ---------------- bivariate correlations ------------------------------
    pairs = []

    def add(cid, label, xs, ys, note=""):
        r = pearson(xs, ys)
        n = len(xs)
        p = p_from_r(r, n)
        pairs.append({"id": cid, "label": label, "r": r, "n": n, "p": p,
                      "ci95": fisher_ci(r, n), "note": note})

    with_lines = [r for r in rows if r["spread_line"] is not None]
    add("C1", "Market spread vs realised home margin", [r["spread_line"] for r in with_lines],
        [r["result"] for r in with_lines], "Market efficiency benchmark.")
    add("C2", "Model margin vs realised home margin", [r["pred_margin"] for r in with_lines],
        [r["result"] for r in with_lines], "Own-line explanatory power.")
    with_tot = [r for r in rows if r["total_line"] is not None]
    add("C3", "Market total vs realised total", [r["total_line"] for r in with_tot],
        [r["total"] for r in with_tot], "")
    add("C4", "Model total vs realised total", [r["pred_total"] for r in with_tot],
        [r["total"] for r in with_tot], "")
    add("C5", "Home margin vs game total (SGP leg dependence)", [r["result"] for r in rows],
        [r["total"] for r in rows], "Negative r means favourites win lower-scoring games.")
    add("C6", "Absolute margin vs game total", [abs(r["result"]) for r in rows],
        [r["total"] for r in rows], "")
    add("C7", "Model margin vs market spread (own-line vs market)", [r["pred_margin"] for r in with_lines],
        [r["spread_line"] for r in with_lines], "Low r means the model genuinely disagrees with the market.")
    add("C8", "Model total vs market total", [r["pred_total"] for r in with_tot],
        [r["total_line"] for r in with_tot], "")
    # rest-days effect is not computable: no official rest-day field was collected.

    ids = [p["id"] for p in pairs]
    q = bh([p["p"] if p["p"] is not None else 1.0 for p in pairs], ids)
    for p in pairs:
        p["r"] = round(p["r"], 4) if p["r"] is not None else None
        p["p"] = round(p["p"], 8) if p["p"] is not None else None
        p["bh_q"] = q[p["id"]]
        p["survives_fdr"] = bool(p["bh_q"] < 0.05)
        out["correlations"].append(p)

    # ---------------- dependence tests (for parlay / SGP legs) -------------
    # 1. Are two legs from the same week independent?
    s1_ok = []
    for r in with_lines:
        margin = r["result"] - r["spread_line"]
        if margin != 0:
            s1_ok.append({"season": r["season"], "week": r["week"], "cover": margin > 0})
    byweek = defaultdict(list)
    for b in s1_ok:
        byweek[(b["season"], b["week"])].append(b["cover"])
    # (a) direct phi over every unordered PAIR of games inside the same week
    pair_a, pair_b, pair_week = [], [], []
    for k, v in byweek.items():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                pair_a.append(1.0 if v[i] else 0.0)
                pair_b.append(1.0 if v[j] else 0.0)
                pair_week.append(k)
    if pair_a:
        pa = sum(pair_a) / len(pair_a); pb = sum(pair_b) / len(pair_b)
        p_both = sum(1 for x, y in zip(pair_a, pair_b) if x and y) / len(pair_a)
        phi = pearson(pair_a, pair_b)
        # week-clustered bootstrap for the CI (resample weeks, keep all pairs in them)
        byw = defaultdict(list)
        for x, y, k in zip(pair_a, pair_b, pair_week):
            byw[k].append((x, y))
        keys = list(byw)
        draws = []
        for _ in range(2000):
            pick = [random.choice(keys) for _ in keys]
            xs = [a for k in pick for a, _ in byw[k]]
            ys = [b for k in pick for _, b in byw[k]]
            v = pearson(xs, ys)
            if v is not None:
                draws.append(v)
        draws.sort()
        out["dependence_tests"].append({
            "id": "D1",
            "label": "Cross-game same-week 2-leg parlay: is the second leg independent of the first?",
            "n_games": len(s1_ok), "n_pairs": len(pair_a), "n_weeks": len(byweek),
            "p_leg_a": round(pa, 4), "p_leg_b": round(pb, 4), "p_both": round(p_both, 4),
            "independence_expected": round(pa * pb, 4),
            "lift": round(p_both / (pa * pb), 4) if pa * pb else None,
            "phi": round(phi, 4), "phi_ci95_bootstrap": [round(draws[int(0.025 * len(draws))], 4),
                                                         round(draws[int(0.975 * len(draws))], 4)],
            "verdict": ("independence NOT rejected (CI contains 0)" if draws[int(0.025*len(draws))] < 0 < draws[int(0.975*len(draws))]
                        else "dependence detected"),
            "implication": "Cross-game parlay legs may be multiplied; no correlation repricing is required."})

    # (b) overdispersion: are covers independent across games within a week?
    weeks2 = [(k, v) for k, v in byweek.items() if len(v) >= 4]
    obs_chi = sum((sum(1 for x in v if x) - len(v) * 0.5) ** 2 / (len(v) * 0.25) for _, v in weeks2)
    df = len(weeks2)
    out["dependence_tests"].append({
        "id": "D1b", "label": "Overdispersion of same-week cover counts vs a coin",
        "n_weeks": df, "chi_square": round(obs_chi, 1), "df": df,
        "chi_over_df": round(obs_chi / df, 4) if df else None,
        "verdict": "no overdispersion (ratio ~ 1.0 means legs behave independently within a week)"
                   if df and 0.85 <= obs_chi / df <= 1.15 else "investigate clustering"})

    # 2. Over/under leg vs cover leg inside one game (SGP dependence)
    cov = []; ov = []
    for r in with_tot:
        if r["spread_line"] is None:
            continue
        margin = r["result"] - r["spread_line"]
        if margin == 0 or r["total"] == r["total_line"]:
            continue
        cov.append(1.0 if margin > 0 else 0.0)
        ov.append(1.0 if r["total"] > r["total_line"] else 0.0)
    if cov:
        phi = pearson(cov, ov)
        out["dependence_tests"].append({
            "id": "D2", "label": "Same-game: home-cover leg vs over leg",
            "n": len(cov), "phi": round(phi, 4),
            "phi_ci95": fisher_ci(phi, len(cov)),
            "p_value": round(p_from_r(phi, len(cov)), 6),
            "verdict": "near-independent" if abs(phi) < 0.10 else "materially dependent",
            "pricing_implication": "A sportsbook same-game-parlay price must be repriced if |phi| is material. "
                                   "No official SGP price archive exists, so no price is claimed."})
    # 3. Cross-week stability of the model's edge (ICC-style)
    weeks = defaultdict(list)
    for r in with_lines:
        e = r["pred_margin"] - r["spread_line"]
        weeks[(r["season"], r["week"])].append(e)
    grp = [v for v in weeks.values() if len(v) >= 2]
    if grp:
        gm = statistics.mean(statistics.mean(g) for g in grp)
        between = sum(len(g) * (statistics.mean(g) - gm) ** 2 for g in grp)
        within = sum((x - statistics.mean(g)) ** 2 for g in grp for x in g)
        icc = between / (between + within) if (between + within) else None
        out["dependence_tests"].append({
            "id": "D3", "label": "Week-level clustering of model edge (ICC)",
            "n_weeks": len(grp), "icc": round(icc, 4) if icc else None,
            "verdict": "edge is not concentrated in a few weeks" if icc is not None and icc < 0.10
                       else "edge clusters by week - a red flag for overfitting"})

    # ---------------- key numbers from realised margins -------------------
    absm = [abs(r["result"]) for r in rows]
    n = len(absm)
    for k in (1, 2, 3, 4, 6, 7, 8, 10, 14):
        out["key_numbers"][str(k)] = round(sum(1 for x in absm if x == k) / n, 4)
    out["key_numbers"]["n"] = n
    out["key_numbers"]["note"] = "Share of games whose final margin equals the number. Buyers of 3 and 7 pay a premium for this."

    # ---------------- home-field advantage by season ----------------------
    bys = defaultdict(list)
    for r in rows:
        bys[r["season"]].append(r["result"])
    for s in sorted(bys):
        v = bys[s]
        out["hfa_by_season"][s] = {"mean_home_margin": round(statistics.mean(v), 3),
                                   "home_win_rate": round(sum(1 for x in v if x > 0) / len(v), 4), "n": len(v)}

    # ---------------- luck calibration ------------------------------------
    out["luck_calibration"] = {
        "ats_push_rate": round(sum(1 for r in with_lines if r["result"] == r["spread_line"]) / len(with_lines), 4),
        "home_cover_rate": round(sum(1 for r in with_lines if r["result"] - r["spread_line"] > 0) /
                                 sum(1 for r in with_lines if r["result"] != r["spread_line"]), 4),
        "over_rate": round(sum(1 for r in with_tot if r["total"] > r["total_line"]) /
                           sum(1 for r in with_tot if r["total"] != r["total_line"]), 4),
        "note": "A market with no information is expected to be 0.50 on each. Deviations are vig, not edge."}

    json.dump(out, open(os.path.join(OUT, "correlations.json"), "w"), indent=1)
    print(f"{'id':4} {'r':>8} {'CI low':>9} {'CI high':>9} {'n':>6}  {'FDR':>6}  label")
    for p in out["correlations"]:
        ci = p["ci95"] or [float('nan'), float('nan')]
        print(f"{p['id']:4} {p['r']:8.4f} {ci[0]:9.4f} {ci[1]:9.4f} {p['n']:6d}  {'yes' if p['survives_fdr'] else 'no':>6}  {p['label']}")
    print()
    for d in out["dependence_tests"]:
        print(d["id"], d["label"], "| n=", d.get("n") or d.get("n_weeks"),
              "| ", {k: v for k, v in d.items() if k in ("phi", "lift", "icc")}, "|", d["verdict"])
    print("key numbers:", {k: v for k, v in out["key_numbers"].items() if k in ("3", "7")})


if __name__ == "__main__":
    main()

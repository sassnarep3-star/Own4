"""T06 — Determine correlation values from verified official values only.

Outputs:
  data/correlations/correlations.json  every correlation with n, Pearson r, Spearman rho,
                                       permutation p, Benjamini-Hochberg q, bootstrap 95% CI
  data/correlations/skill_luck.json    variance decomposition / luck-removal diagnostics
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (RAW, CORRELATIONS, SRC, bootstrap_ci, pearson,  # noqa: E402
                    permutation_p, read_json, spearman, write_json)

A25 = {r["code"]: r for r in read_json(RAW / "advanced_2025_26.json")["rows"]}
A26 = {r["code"]: r for r in read_json(RAW / "advanced_2026_27.json")["rows"]}
T26 = {r["code"]: r for r in read_json(RAW / "traditional_2026_27.json")["rows"]}
S26 = {r["code"]: r for r in read_json(RAW / "standings_2026_27.json")["rows"]}
SLATE = read_json(RAW / "slate_2026_11_04.json")["rows"]
SETTLED = read_json(RAW / "settled_games.json")["rows"]
BT = read_json(Path(__file__).resolve().parent.parent / "data" / "derived" / "backtest.json")
CODES = sorted(A25.keys())


def pair(name, group, xs, ys, sources, note):
    return {
        "id": name,
        "group": group,
        "n": len(xs),
        "x": name.split(" ~ ")[1] if " ~ " in name else "x",
        "y": name.split(" ~ ")[0] if " ~ " in name else "y",
        "pearson_r": pearson(xs, ys),
        "spearman_rho": spearman(xs, ys),
        "permutation_p": permutation_p(xs, ys),
        "bootstrap_ci95": list(bootstrap_ci(xs, ys)),
        "r_squared": (pearson(xs, ys) ** 2) if pearson(xs, ys) is not None else None,
        "sources": sources,
        "note": note,
    }


def winpct(r):
    return r["w"] / (r["w"] + r["l"])


rows = []
S25 = SRC["adv_2025"]
S26a = SRC["adv_2026"]
S26t = SRC["trad_2026"]
Sst = SRC["standings"]
Ssl = SRC["games_1104"]
Sgl = SRC["glossary"]

# ---- 1. Within 2025-26 (completed 82-game season) -------------------------------
w25 = [winpct(A25[c]) for c in CODES]
net25 = [A25[c]["net_rtg"] for c in CODES]
off25 = [A25[c]["off_rtg"] for c in CODES]
def25 = [A25[c]["def_rtg"] for c in CODES]
pace25 = [A25[c]["pace"] for c in CODES]
rows.append(pair("2025-26 WIN% ~ NetRtg", "2025-26 season (n=30, 82 GP each)", net25, w25,
                 [S25, Sgl], "Systematic strength vs wins over a full official season."))
rows.append(pair("2025-26 WIN% ~ OffRtg", "2025-26 season (n=30, 82 GP each)", off25, w25,
                 [S25, Sgl], "Offensive rating alone."))
rows.append(pair("2025-26 WIN% ~ DefRtg", "2025-26 season (n=30, 82 GP each)", def25, w25,
                 [S25, Sgl], "Defensive rating alone; a negative r is expected."))
rows.append(pair("2025-26 WIN% ~ PACE", "2025-26 season (n=30, 82 GP each)", pace25, w25,
                 [S25, Sgl], "Pace is a null-style control signal."))
rows.append(pair("2025-26 NetRtg ~ PACE", "2025-26 season (n=30, 82 GP each)", pace25, net25,
                 [S25, Sgl], "Parlay-leg check: are strength and pace independent legs?"))
rows.append(pair("2025-26 OffRtg ~ PACE", "2025-26 season (n=30, 82 GP each)", pace25, off25,
                 [S25, Sgl], "Parlay-leg check: offense vs pace."))
rows.append(pair("2025-26 OffRtg ~ DefRtg", "2025-26 season (n=30, 82 GP each)", def25, off25,
                 [S25, Sgl], "Do teams trade offence for defence?"))

# ---- 2. Within 2026-27 (season in progress) -------------------------------------
w26 = [winpct(S26[c]) for c in CODES]
net26 = [A26[c]["net_rtg"] for c in CODES]
off26 = [A26[c]["off_rtg"] for c in CODES]
def26 = [A26[c]["def_rtg"] for c in CODES]
pace26 = [A26[c]["pace"] for c in CODES]
pts26 = [T26[c]["pts"] for c in CODES]
rows.append(pair("2026-27 WIN% ~ NetRtg", "2026-27 season (n=30, 4-7 GP each)", net26, w26,
                 [S26a, Sst, Sgl], "Concurrent, small-sample; NOT out-of-sample."))
rows.append(pair("2026-27 WIN% ~ OffRtg", "2026-27 season (n=30, 4-7 GP each)", off26, w26,
                 [S26a, Sst], "Concurrent."))
rows.append(pair("2026-27 WIN% ~ DefRtg", "2026-27 season (n=30, 4-7 GP each)", def26, w26,
                 [S26a, Sst], "Concurrent."))
rows.append(pair("2026-27 PTS ~ NetRtg", "2026-27 season (n=30, 4-7 GP each)", net26, pts26,
                 [S26a, S26t], "Parlay-leg check: team points vs strength."))
rows.append(pair("2026-27 PTS ~ PACE", "2026-27 season (n=30, 4-7 GP each)", pace26, pts26,
                 [S26a, S26t, Sgl], "Parlay-leg check: totals legs."))
rows.append(pair("2026-27 NetRtg ~ PACE", "2026-27 season (n=30, 4-7 GP each)", pace26, net26,
                 [S26a, Sgl], "Parlay-leg check."))
rows.append(pair("2026-27 NetRtg ~ +/- (traditional)", "2026-27 season (n=30, 4-7 GP each)",
                 [T26[c]["plus_minus"] for c in CODES], net26, [S26a, S26t],
                 "Cross-table consistency check between two official tables."))

# ---- 3. Cross-season / TRUE out-of-sample predictive signals --------------------
rows.append(pair("2026-27 WIN% ~ 2025-26 NetRtg", "Cross-season OUT-OF-SAMPLE (n=30)", net25, w26,
                 [S25, Sst], "Prior-season strength predicting next-season win rate."))
rows.append(pair("2026-27 NetRtg ~ 2025-26 NetRtg", "Cross-season OUT-OF-SAMPLE (n=30)",
                 net25, net26, [S25, S26a], "Rating stability across seasons (roster/regime change)."))
rows.append(pair("2026-27 WIN% ~ 2025-26 WIN%", "Cross-season OUT-OF-SAMPLE (n=30)",
                 w25, w26, [S25, Sst], "Naive persistence baseline."))
rows.append(pair("2026-27 PACE ~ 2025-26 PACE", "Cross-season OUT-OF-SAMPLE (n=30)",
                 pace25, pace26, [S25, S26a], "Is pace a repeatable (skill-like) team trait?"))
rows.append(pair("2026-27 PTS ~ 2025-26 NetRtg", "Cross-season OUT-OF-SAMPLE (n=30)",
                 net25, pts26, [S25, S26t], "Prior strength vs current scoring (null-style check)."))

# ---- 4. Player-prop leg correlations (official season-leader baselines) ---------
ppg, rpg, apg = [], [], []
for g in SLATE:
    ppg.extend([g["ppg_a"], g["ppg_b"]])
    rpg.extend([g["rpg_a"], g["rpg_b"]])
    apg.extend([g["apg_a"], g["apg_b"]])
rows.append(pair("Prop leg RPG ~ PPG", "Player prop combos (n=28 official team leaders)", ppg, rpg,
                 [Ssl], "Correlation between two same-game prop legs."))
rows.append(pair("Prop leg APG ~ PPG", "Player prop combos (n=28 official team leaders)", ppg, apg,
                 [Ssl], "Correlation between two same-game prop legs."))
rows.append(pair("Prop leg APG ~ RPG", "Player prop combos (n=28 official team leaders)", rpg, apg,
                 [Ssl], "Correlation between two same-game prop legs."))

# ---- 5. Home-court / standings legs ---------------------------------------------
home_wp = [S26[c]["home_w"] / max(1, S26[c]["home_w"] + S26[c]["home_l"]) for c in CODES]
road_wp = [S26[c]["road_w"] / max(1, S26[c]["road_w"] + S26[c]["road_l"]) for c in CODES]
rows.append(pair("2026-27 HOME WIN% ~ OVERALL WIN%", "Standings legs (n=30)", w26, home_wp,
                 [Sst], "Parlay-leg dependence: home form is not independent of overall form."))
rows.append(pair("2026-27 ROAD WIN% ~ HOME WIN%", "Standings legs (n=30)", home_wp, road_wp,
                 [Sst], "Home/road split reliability."))

# ---- Benjamini-Hochberg FDR correction across all reported correlations ----------
ps = [r["permutation_p"] for r in rows]
order = sorted(range(len(rows)), key=lambda i: ps[i])
m = len(rows)
prev = 1.0
for rank_pos, i in enumerate(reversed(order), start=1):
    j = m - rank_pos + 1
    q = min(prev, ps[i] * m / j)
    rows[i]["bh_q"] = min(1.0, q)
    prev = rows[i]["bh_q"]

for r in rows:
    r["significant_after_fdr"] = r["bh_q"] < 0.05
    r["interpretation"] = (
        "significant after BH-FDR correction" if r["significant_after_fdr"]
        else "not significant after BH-FDR correction"
    )

write_json(CORRELATIONS / "correlations.json", {
    "retrieved_utc": "2026-11-02",
    "method": ("Pearson r and Spearman rho on official NBA.com values. Two-sided permutation "
               "p-value (20,000 shuffles, seed 20261102). Percentile bootstrap 95% CI "
               "(5,000 resamples, seed 20261102). Benjamini-Hochberg FDR q across all "
               f"{m} reported correlations."),
    "sources": [S25, S26a, S26t, Sst, Ssl, Sgl],
    "count": m,
    "rows": rows,
})

# ---- Skill vs luck decomposition -------------------------------------------------
def dec(label, xs, ys, sources):
    r = pearson(xs, ys)
    return {
        "label": label,
        "n": len(xs),
        "pearson_r": r,
        "systematic_variance_share_r2": r * r if r is not None else None,
        "residual_variance_share": 1 - r * r if r is not None else None,
        "sources": sources,
        "note": ("Descriptive variance partition only. The residual share combines genuine "
                 "team change, schedule effects, injuries and chance; it is NOT a causal "
                 "estimate of luck."),
    }


h = BT["holdout"]
t = BT["train"]
decomp = [
    dec("2025-26 full season: WIN% explained by NetRtg", net25, w25, [S25, Sgl]),
    dec("2026-27 in progress: WIN% explained by NetRtg", net26, w26, [S26a, Sst]),
    dec("Cross-season: 2026-27 WIN% explained by 2025-26 NetRtg", net25, w26, [S25, Sst]),
]

write_json(CORRELATIONS / "skill_luck.json", {
    "retrieved_utc": "2026-11-02",
    "luck_removal_method": [
        "Pre-register hypotheses before looking at results (see REQUIREMENTS.md R1.09-R1.12).",
        "Use only out-of-sample seasons / chronological train-holdout splits; no in-sample tuning counts as skill.",
        "Compare against exact binomial nulls (coin flip) and permutation nulls for correlations.",
        "Report 95% Wilson intervals for accuracy and bootstrap intervals for correlations.",
        "Apply Benjamini-Hochberg FDR correction across the full family of tested correlations.",
        "Require positive Brier skill score on the holdout window before any reward is assigned.",
        "Require minimum sample size (G3) and verified market prices (G7) before a bet strategy can be deployed.",
    ],
    "decomposition": decomp,
    "backtest_evidence": {
        "train": {k: t[k] for k in ("n", "winner_accuracy", "binomial_p_two_sided_vs_0_5",
                                    "brier_score", "brier_skill_score_vs_0_5",
                                    "pred_vs_actual_margin_permutation_p")},
        "holdout": {k: h[k] for k in ("n", "winner_accuracy", "binomial_p_two_sided_vs_0_5",
                                      "brier_score", "brier_skill_score_vs_0_5",
                                      "pred_vs_actual_margin_permutation_p")},
        "sources": [S25, SRC["games_1023"], SRC["games_1028"], SRC["games_1030"], SRC["games_1101"]],
    },
    "finding": ("The prior-season rating model looks strong in the training window but its "
                "holdout winner accuracy is below 50% and its holdout Brier skill score is "
                "negative. Under the pre-registered luck-removal rules it is therefore "
                "classified as NOT skill-based and is ineligible for rewards."),
})

if __name__ == "__main__":
    for r in rows:
        print(f"{r['id']:<48} n={r['n']:<3} r={r['pearson_r']:+.3f} "
              f"rho={r['spearman_rho']:+.3f} p={r['permutation_p']:.4f} q={r['bh_q']:.4f}")

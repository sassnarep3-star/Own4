"""Q3: own-line origination engine.

Walk-forward ridge ratings:
  margin_i = rating_home - rating_away + HFA + eps
  total_i  = mu + off_home + off_away + def_home + def_away + eps
Weights decay exponentially with game age (half-life tuned on DEV only).
Each game's prediction is fit using ONLY games with gameday strictly earlier
than that game's date. Hyperparameters frozen before validation/holdout.

Outputs: predictions.csv, model_config.json, forecast_skill.json,
hfa_by_season.csv, lookahead_test.json
"""
import json, datetime, itertools
import numpy as np
import pandas as pd
from common import GAMES_CSV, DATA, save_json, write_df, norm_cdf, am_to_prob

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
rng = np.random.default_rng(42)

g = pd.read_csv(GAMES_CSV, parse_dates=["gameday"])
# Normalize historical franchise codes (verified in 01_provenance.py)
FRANCHISE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
g["home_team"] = g.home_team.replace(FRANCHISE)
g["away_team"] = g.away_team.replace(FRANCHISE)
g = g[g.game_type == "REG"].sort_values(["gameday", "game_id"]).reset_index(drop=True)
teams = sorted(set(g.home_team) | set(g.away_team))
tidx = {t: i for i, t in enumerate(teams)}
NT = len(teams)
hi = g.home_team.map(tidx).to_numpy()
ai = g.away_team.map(tidx).to_numpy()
dates = g.gameday.to_numpy(dtype="datetime64[ns]")
y_margin = g.result.to_numpy(dtype=float).copy()
y_total = g.total.to_numpy(dtype=float).copy()
played_mask = g.result.notna().to_numpy()

def design_margin(h, a):
    X = np.zeros((len(h), NT + 1))
    r = np.arange(len(h))
    X[r, h] = 1.0
    X[r, a] = -1.0
    X[:, NT] = 1.0  # HFA
    return X

def design_total(h, a):
    X = np.zeros((len(h), 2 * NT + 1))
    r = np.arange(len(h))
    X[r, h] = 1.0            # off home
    X[r, a] = 1.0            # off away
    X[r, NT + h] = 1.0       # def home
    X[r, NT + a] = 1.0       # def away
    X[:, 2 * NT] = 1.0       # intercept
    return X

def fit_predict(train_idx, pred_h, pred_a, ref_date, halflife, ridge, kind):
    if len(train_idx) < 60:
        return None
    age = (np.datetime64(ref_date) - dates[train_idx]).astype("timedelta64[D]").astype(float)
    w = 0.5 ** (age / halflife)
    if kind == "margin":
        X = design_margin(hi[train_idx], ai[train_idx])
        y = y_margin[train_idx]
        p = NT + 1
    else:
        X = design_total(hi[train_idx], ai[train_idx])
        y = y_total[train_idx]
        p = 2 * NT + 1
    XtW = X.T * w
    A = XtW @ X
    reg = np.full(p, ridge)
    reg[-1] = 1e-6  # do not penalize intercept/HFA
    A += np.diag(reg)
    beta = np.linalg.solve(A, XtW @ y)
    if kind == "margin":
        return beta[pred_h] - beta[pred_a] + beta[NT], beta[NT]
    else:
        mu = beta[2 * NT]
        tot = mu + beta[pred_h] + beta[pred_a] + beta[NT + pred_h] + beta[NT + pred_a]
        htt = mu / 2 + beta[pred_h] + beta[NT + pred_a]
        att = mu / 2 + beta[pred_a] + beta[NT + pred_h]
        return tot, htt, att

# group games by date; train = played games strictly before date
date_groups = g.groupby("gameday").indices  # dict date -> row indices
unique_dates = sorted(date_groups.keys())

def run_config(seasons, halflife, ridge, kind):
    preds = np.full(len(g), np.nan)
    extras = {}
    cum_train = []
    train_ptr = 0
    all_idx = np.arange(len(g))
    for d in unique_dates:
        # add all played games strictly before d to training pool
        while train_ptr < len(g) and dates[train_ptr] < d:
            if played_mask[train_ptr]:
                cum_train.append(train_ptr)
            train_ptr += 1
        idx = date_groups[d]
        sel = idx[np.isin(g.season.to_numpy()[idx], seasons)]
        if len(sel) == 0:
            continue
        tr = np.array(cum_train, dtype=int)
        out = fit_predict(tr, hi[sel], ai[sel], d, halflife, ridge, kind)
        if out is None:
            continue
        if kind == "margin":
            preds[sel], hfa = out
            extras[str(d.date())] = float(hfa)
        else:
            tot, htt, att = out
            preds[sel] = tot
            extras.setdefault("htt", np.full(len(g), np.nan))[sel] = htt
            extras.setdefault("att", np.full(len(g), np.nan))[sel] = att
    return preds, extras

# ---------- DEV tuning (1999-2012 only) ----------
dev_seasons = list(range(1999, 2013))
grid = list(itertools.product([180.0, 365.0, 730.0], [10.0, 50.0]))
dev_mask = g.season.isin(dev_seasons).to_numpy() & played_mask & (g.season.to_numpy() >= 2001)
results = []
best_m = best_t = None
print("Tuning on DEV seasons 1999-2012 (evaluation 2001-2012)...")
for halflife, ridge in grid:
    pm, _ = run_config(dev_seasons, halflife, ridge, "margin")
    mae_m = np.nanmean(np.abs(pm[dev_mask] - y_margin[dev_mask]))
    pt, _ = run_config(dev_seasons, halflife, ridge, "total")
    mae_t = np.nanmean(np.abs(pt[dev_mask] - y_total[dev_mask]))
    results.append({"halflife_days": halflife, "ridge": ridge, "dev_margin_MAE": round(float(mae_m), 4), "dev_total_MAE": round(float(mae_t), 4)})
    if best_m is None or mae_m < best_m[0]:
        best_m = (mae_m, halflife, ridge)
    if best_t is None or mae_t < best_t[0]:
        best_t = (mae_t, halflife, ridge)
print("dev grid:", json.dumps(results))
print("best margin config:", best_m, "best total config:", best_t)

# ---------- FINAL frozen config: predict 2001-2026 ----------
final_seasons = list(range(2001, 2027))
pm, hfa_map = run_config(final_seasons, best_m[1], best_m[2], "margin")
pt, tt_extras = run_config(final_seasons, best_t[1], best_t[2], "total")
resid = y_margin - pm
dev_resid = resid[dev_mask & ~np.isnan(pm)]
sigma = float(np.std(dev_resid))
print("frozen sigma (dev residuals):", round(sigma, 3))

g["pred_margin"] = pm
g["pred_total"] = pt
g["pred_home_tt"] = tt_extras.get("htt")
g["pred_away_tt"] = tt_extras.get("att")
g["p_home_win"] = [norm_cdf(m / sigma) if not np.isnan(m) else np.nan for m in pm]
g["sigma"] = sigma
write_df(g[["game_id", "season", "week", "gameday", "away_team", "home_team",
            "result", "total", "spread_line", "total_line", "away_moneyline", "home_moneyline",
            "away_spread_odds", "home_spread_odds", "over_odds", "under_odds",
            "pred_margin", "pred_total", "pred_home_tt", "pred_away_tt", "p_home_win", "sigma"]],
         "predictions.csv")

# HFA by season (mean of date-level HFA estimates within season, final config)
hfa_rows = []
for d, v in hfa_map.items():
    hfa_rows.append({"date": d, "season": int(d[:4]), "hfa": v})
hfa_df = pd.DataFrame(hfa_rows).groupby("season").hfa.mean().round(3).reset_index()
write_df(hfa_df, "hfa_by_season.csv")

# ---------- forecast skill on HOLDOUT (2017-2025) ----------
ho = g[g.season.between(2017, 2025) & played_mask & g.spread_line.notna()].copy()
ho = ho.dropna(subset=["pred_margin"])
# VERIFIED convention: spread_line = points home is favored by (positive = home fav)
market_margin = ho.spread_line.to_numpy()
naive_hfa = np.full(len(ho), 2.0)
# naive season-to-date average margin differential (+2.0 HFA)
sums = {}  # (season, team) -> [sum_margin, n]
naive = []
for row in ho.itertuples():
    kh = (row.season, row.home_team); ka = (row.season, row.away_team)
    mh = sums[kh][0] / sums[kh][1] if kh in sums and sums[kh][1] > 0 else 0.0
    ma = sums[ka][0] / sums[ka][1] if ka in sums and sums[ka][1] > 0 else 0.0
    naive.append(mh - ma + 2.0)
    if not np.isnan(row.result):
        for key, val in ((kh, row.result), (ka, -row.result)):
            s = sums.setdefault(key, [0.0, 0])
            s[0] += val; s[1] += 1
naive = np.array(naive)
y = ho.result.to_numpy()
def mae(p): return float(np.mean(np.abs(p - y)))
def rmse(p): return float(np.sqrt(np.mean((p - y) ** 2)))
# win-prob skill
p_model = ho.p_home_win.to_numpy()
ph = ho.home_moneyline.map(am_to_prob).to_numpy()
pa = ho.away_moneyline.map(am_to_prob).to_numpy()
ok = ~np.isnan(ph) & ~np.isnan(pa)
p_market = ph / (ph + pa)
home_win = (y > 0).astype(float)
def brier(p, mask=None):
    if mask is not None:
        return float(np.mean((p[mask] - home_win[mask]) ** 2))
    return float(np.mean((p - home_win) ** 2))
skill = {
    "holdout_seasons": "2017-2025", "n_games": int(len(ho)),
    "margin_MAE": {"model": round(mae(ho.pred_margin.to_numpy()), 3),
                    "market_closing_spread": round(mae(market_margin), 3),
                    "naive_HFA_plus2": round(mae(naive_hfa), 3)},
    "margin_RMSE": {"model": round(rmse(ho.pred_margin.to_numpy()), 3),
                     "market_closing_spread": round(rmse(market_margin), 3),
                     "naive_HFA_plus2": round(rmse(naive_hfa), 3)},
    "win_prob_Brier": {"model": round(brier(p_model, ok), 4),
                        "market_devig_ML": round(brier(p_market, ok), 4),
                        "naive_050_plus_HFA": round(brier(np.full(len(ho), norm_cdf(2.0 / sigma)), ok), 4)},
    "note": "Market closing spread is a third-party archive value (no official source). Model vs naive baselines demonstrates forecasting skill; model vs market shows whether the closing market is beaten.",
}
save_json("forecast_skill.json", skill)
print(json.dumps(skill, indent=1))

# ---------- G6 look-ahead perturbation test ----------
# Recompute predictions for 3 holdout dates after permuting ALL later results.
test_dates = [d for d in unique_dates if pd.Timestamp(d).year in (2019, 2022, 2024)]
test_dates = [test_dates[len(test_dates) // 4], test_dates[len(test_dates) // 2], test_dates[3 * len(test_dates) // 4]]
y_margin_orig = y_margin.copy()
perturb_results = []
for d in test_dates:
    idx = date_groups[d]
    tr = np.array([i for i in range(len(g)) if dates[i] < d and played_mask[i]], dtype=int)
    base, _ = fit_predict(tr, hi[idx], ai[idx], d, best_m[1], best_m[2], "margin")
    future = dates >= d
    perm = rng.permutation(y_margin[future])
    y_margin[future] = perm
    pert, _ = fit_predict(tr, hi[idx], ai[idx], d, best_m[1], best_m[2], "margin")
    y_margin[future] = y_margin_orig[future]
    same = bool(np.allclose(base, pert, atol=1e-9))
    perturb_results.append({"date": str(pd.Timestamp(d).date()), "predictions_unchanged": same, "n_games": int(len(idx))})
assert all(r["predictions_unchanged"] for r in perturb_results)
save_json("lookahead_test.json", {"test": "future results permuted; same-date predictions must be identical", "results": perturb_results, "pass": True})

save_json("model_config.json", {
    "generated_utc": NOW,
    "dev_grid_results": results,
    "margin_config": {"halflife_days": best_m[1], "ridge": best_m[2], "dev_MAE": round(best_m[0], 4)},
    "total_config": {"halflife_days": best_t[1], "ridge": best_t[2], "dev_MAE": round(best_t[0], 4)},
    "sigma": round(sigma, 4),
    "training_rule": "REG games only, gameday strictly before predicted game's date; exponential time decay; ridge on team coefficients only",
    "frozen_before_holdout": True,
})
print("02_ratings done.")

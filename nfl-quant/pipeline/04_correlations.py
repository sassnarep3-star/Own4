"""Q5: correlation study.

Game-level (1999-2025 REG, lines subset): cover/over dependence, margin/total,
cross-game independence (ICC by week), key-number margin distribution.
Player-level (2021-2022): QB/WR/RB yardage dependence with bootstrap CIs.

ALL values here are COMPUTED from the cited archives. No official source
publishes these coefficients; the official-source column is blank + flagged
UNVERIFIED-OFFICIAL on the site, with the data provenance link instead.
"""
import json, datetime, math
import numpy as np
import pandas as pd
from common import GAMES_CSV, FDP, DATA, RAW, save_json, write_df, TEAM_MAP

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
rng = np.random.default_rng(7)
FRANCHISE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

g = pd.read_csv(GAMES_CSV)
g["home_team"] = g.home_team.replace(FRANCHISE)
g["away_team"] = g.away_team.replace(FRANCHISE)
g = g[(g.game_type == "REG") & g.result.notna()].copy()

def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[ok], y[ok]
    if len(x) < 10:
        return None, len(x)
    return float(np.corrcoef(x, y)[0, 1]), len(x)

def boot_ci(x, y, n=1000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[ok], y[ok]
    if len(x) < 10:
        return [None, None]
    rs = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        rs.append(np.corrcoef(x[i], y[i])[0, 1])
    return [round(float(np.percentile(rs, 2.5)), 4), round(float(np.percentile(rs, 97.5)), 4)]

rows = []
def add(pair, scope, x, y, note=""):
    r, n = pearson(x, y)
    ci = boot_ci(x, y)
    rows.append({"pair": pair, "scope": scope, "n": n,
                 "pearson_r": None if r is None else round(r, 4),
                 "ci95_low": ci[0], "ci95_high": ci[1], "note": note})

# ---------- game-level ----------
gl = g[g.spread_line.notna() & g.total_line.notna()].copy()
gl["fav_cover"] = np.where(gl.spread_line > 0, (gl.result > gl.spread_line), (gl.result < gl.spread_line))
gl["fav_push"] = gl.result == gl.spread_line
gl["over"] = gl.total > gl.total_line
gl["total_push"] = gl.total == gl.total_line
glf = gl[~gl.fav_push & ~gl.total_push]
add("favorite covers vs over (binary phi)", "1999-2025 REG w/ lines", glf.fav_cover.astype(float), glf.over.astype(float),
    "phi coefficient; positive => favorite-cover pairs with over more often than independence")
add("home covers vs over (binary phi)", "1999-2025 REG w/ lines", (glf.result > glf.spread_line).astype(float), glf.over.astype(float))
add("final margin (home-away) vs game total", "1999-2025 REG w/ lines", gl.result, gl.total)
add("absolute margin vs game total", "1999-2025 REG w/ lines", gl.result.abs(), gl.total)
add("market spread (home-favored pts) vs game total", "1999-2025 REG w/ lines", gl.spread_line, gl.total)
ho = glf[glf.season.between(2017, 2025)]
add("favorite covers vs over (binary phi)", "2017-2025 holdout era", ho.fav_cover.astype(float), ho.over.astype(float))

# joint vs independence table for SGP fair pricing
sgp = []
for scope, d in (("1999-2025", glf), ("2017-2025", ho)):
    pf = d.fav_cover.mean(); po = d.over.mean()
    for fav in (True, False):
        for ov in (True, False):
            joint = ((d.fav_cover == fav) & (d.over == ov)).mean()
            prod = (pf if fav else 1 - pf) * (po if ov else 1 - po)
            sgp.append({"scope": scope, "combo": ("favorite covers" if fav else "underdog covers") + " + " + ("over" if ov else "under"),
                        "n": len(d), "p_joint_empirical": round(float(joint), 4),
                        "p_product_if_independent": round(float(prod), 4),
                        "lift_joint_over_product": round(float(joint / prod), 4)})
write_df(pd.DataFrame(sgp), "sgp_joint_probabilities.csv")

# cross-game independence: ICC of ATS residuals by (season, week)
gl["ats_resid"] = gl.result - gl.spread_line
grp = gl.groupby(["season", "week"]).ats_resid
grand = gl.ats_resid.mean()
ss_between = sum(len(x) * (x.mean() - grand) ** 2 for _, x in grp)
ss_total = ((gl.ats_resid - grand) ** 2).sum()
icc = float(ss_between / ss_total)
# Permutation null: even iid residuals give E[ICC] ~ 1/mean_games_per_week.
# Shuffle residuals across weeks 500x to get the null distribution.
resid = gl.ats_resid.to_numpy()
week_codes = gl.groupby(["season", "week"]).ngroup().to_numpy()
null_iccs = []
for _ in range(500):
    shuffled = rng.permutation(resid)
    sb = 0.0
    gm = pd.Series(shuffled).groupby(week_codes)
    grand_s = shuffled.mean()
    for _, x in gm:
        sb += len(x) * (x.mean() - grand_s) ** 2
    null_iccs.append(sb / ((shuffled - grand_s) ** 2).sum())
null_iccs = np.array(null_iccs)
icc_p = float((null_iccs >= icc).mean())
add("cross-game ATS residual ICC (same week)", "1999-2025 REG w/ lines", [0], [0],
    f"observed ICC {icc:.5f} vs permutation-null mean {null_iccs.mean():.5f} (p={icc_p:.3f}). Null expectation ~1/games-per-week; excess over null measures true same-week dependence of market residuals.")
rows[-1]["pearson_r"] = round(icc, 5); rows[-1]["n"] = len(gl)
rows[-1]["ci95_low"] = round(float(np.percentile(null_iccs, 2.5)), 5); rows[-1]["ci95_high"] = round(float(np.percentile(null_iccs, 97.5)), 5)

# key numbers: final margin distribution
kn = g[g.season >= 2015].result.abs().value_counts(normalize=True).sort_index()
top = kn.sort_values(ascending=False).head(12)
key_rows = [{"absolute_margin": int(m), "frequency": round(float(f), 4), "games_scope": "2015-2025 REG"} for m, f in top.items()]
write_df(pd.DataFrame(key_rows), "key_numbers.csv")
push_rate = float((gl.result == gl.spread_line).mean())
save_json("game_level_summary.json", {"ats_push_rate_at_closing_spread": round(push_rate, 4),
                                       "margin3_share_2015plus": round(float(kn.get(3, 0)), 4),
                                       "margin7_share_2015plus": round(float(kn.get(7, 0)), 4),
                                       "cross_game_icc": round(icc, 5),
                                       "cross_game_icc_null_mean": round(float(null_iccs.mean()), 5),
                                       "cross_game_icc_permutation_p": round(icc_p, 4)})

# ---------- player-level (2021-2022) ----------
def load_weekly(season):
    frames = []
    if season == 2021:
        base = FDP / "2022/07-Data Visualizations/01-Weekly Fantasy Stats - 2021"
        for wk in range(1, 19):
            d = pd.read_csv(base / f"{wk}.csv")
            d = d.rename(columns={"Pos": "pos", "Tm": "tm", "ReceivingYds": "rec_yds"})
            d["tm"] = d.tm.map(TEAM_MAP)
            frames.append(pd.DataFrame({"season": season, "week": wk, "player": d.Player, "pos": d.pos, "team": d.tm,
                                        "pass_yds": d.PassingYds, "rush_yds": d.RushingYds, "rec_yds": d.rec_yds,
                                        "targets": d.Tgt, "rec": d.Rec, "pass_att": d.PassingAtt, "rush_att": d.RushingAtt}))
    else:
        base = FDP / "2023/07-Data Visualizations/01-Weekly Fantasy Stats - 2022"
        for wk in range(1, 19):
            d = pd.read_csv(base / f"{wk}.csv")
            frames.append(pd.DataFrame({"season": season, "week": wk, "player": d.Player, "pos": d.Position, "team": d.Tm,
                                        "pass_yds": d.PassingYds, "rush_yds": d.RushingYds, "rec_yds": d.ReceivingYards,
                                        "targets": d.Targets, "rec": d.Receptions, "pass_att": d.PassingAtt, "rush_att": d.RushingAtt}))
    return pd.concat(frames, ignore_index=True)

w = pd.concat([load_weekly(2021), load_weekly(2022)], ignore_index=True)

# team-game outcomes lookup
tg = []
for row in g.itertuples():
    tg.append({"season": row.season, "week": row.week, "team": row.home_team, "pts": row.home_score,
               "margin": row.result, "total": row.total, "opp": row.away_team})
    tg.append({"season": row.season, "week": row.week, "team": row.away_team, "pts": row.away_score,
               "margin": -row.result, "total": row.total, "opp": row.home_team})
tg = pd.DataFrame(tg)
w = w.merge(tg, on=["season", "week", "team"], how="left")
w.to_pickle(RAW / "_weekly.pkl")  # scratch OUTSIDE repo for 05_props (includes game outcomes)

# designate QB1/WR1/WR2/RB1 per team-game by that week's yardage (ex-post; standard for correlation studies)
def leaders(d):
    qb = d[d.pos == "QB"].sort_values("pass_yds", ascending=False)
    wr = d[d.pos.isin(["WR", "TE"])].sort_values("rec_yds", ascending=False)
    rb = d[d.pos == "RB"].sort_values("rush_yds", ascending=False)
    return {
        "qb1_pass": qb.pass_yds.iloc[0] if len(qb) else np.nan,
        "wr1_rec": wr.rec_yds.iloc[0] if len(wr) else np.nan,
        "wr2_rec": wr.rec_yds.iloc[1] if len(wr) > 1 else np.nan,
        "rb1_rush": rb.rush_yds.iloc[0] if len(rb) else np.nan,
        "team_pts": d.pts.iloc[0], "margin": d.margin.iloc[0], "total": d.total.iloc[0],
    }
lrows = []
for (season, week, team), d in w.groupby(["season", "week", "team"]):
    rec = leaders(d)
    rec.update({"season": season, "week": week, "team": team})
    lrows.append(rec)
lg = pd.DataFrame(lrows)
lg.to_pickle(RAW / "_leaders.pkl")

add("QB1 passing yds vs WR1 receiving yds (same team-game)", "2021-2022", lg.qb1_pass, lg.wr1_rec, "WR1/WR2 = top-2 WR/TE by receiving yards that game")
add("QB1 passing yds vs WR2 receiving yds (same team-game)", "2021-2022", lg.qb1_pass, lg.wr2_rec)
add("WR1 vs WR2 receiving yds (same team-game)", "2021-2022", lg.wr1_rec, lg.wr2_rec)
add("QB1 passing yds vs RB1 rushing yds (same team-game)", "2021-2022", lg.qb1_pass, lg.rb1_rush)
add("RB1 rushing yds vs team margin (game script)", "2021-2022", lg.rb1_rush, lg.margin)
add("QB1 passing yds vs team points", "2021-2022", lg.qb1_pass, lg.team_pts)
add("QB1 passing yds vs game total", "2021-2022", lg.qb1_pass, lg.total)
add("WR1 receiving yds vs game total", "2021-2022", lg.wr1_rec, lg.total)
add("team points vs game total", "2021-2022", lg.team_pts, lg.total)

write_df(pd.DataFrame(rows), "correlations.csv")
print(pd.DataFrame(rows).to_string(index=False))
print("SGP joints:"); print(pd.DataFrame(sgp).to_string(index=False))
save_json("correlations_meta.json", {"generated_utc": NOW, "method": "Pearson r (phi for binary pairs); 1000-draw bootstrap 95% CI resampling games/team-games; player leaders designated ex-post per game for the correlation matrix (leak-free rolling designation is used for prop betting tests in 05_props.py)", "official_status": "COMPUTED values; no official source publishes these coefficients. Flagged UNVERIFIED-OFFICIAL per project policy; reproducible from cited archives."})
print("04_correlations done.")

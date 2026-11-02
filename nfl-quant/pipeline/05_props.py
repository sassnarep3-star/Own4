"""Q4/Q5: player-prop research (2021-2022 only; RESEARCH-ONLY, Gate G7 fails).

No official or archived sportsbook prop lines exist in the authorized data,
so a transparent PROXY line is used: the player's rolling 4-game mean entering
the week (rounded to 0.5). Projections add a leak-free opponent adjustment.
These results measure signal vs a naive proxy, NOT vs a real market.

Leak-free designations: QB1/WR1/RB1 for BETTING are chosen by season-to-date
cumulative yards entering the week (not that week's results).
"""
import json, datetime, math
import numpy as np
import pandas as pd
from common import RAW, DATA, save_json, write_df, am_to_dec

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
rng = np.random.default_rng(11)
w = pd.read_pickle(RAW / "_weekly.pkl")
w = w.sort_values(["season", "week"]).reset_index(drop=True)

# rolling player history (per season, per player+team key)
def rolling_mean_yds(d, col, window=4, min_games=3):
    return d[col].shift(1).rolling(window, min_periods=min_games).mean()

w["roll_pass"] = w.groupby(["season", "player", "team"]).pass_yds.transform(lambda s: s.shift(1).rolling(4, min_periods=3).mean())
w["roll_rec"] = w.groupby(["season", "player", "team"]).rec_yds.transform(lambda s: s.shift(1).rolling(4, min_periods=3).mean())
w["roll_rush"] = w.groupby(["season", "player", "team"]).rush_yds.transform(lambda s: s.shift(1).rolling(4, min_periods=3).mean())

# opponent adjustment: rolling defensive yards allowed to position (leak-free)
def_allowed = []
for (season, week, team), d in w.groupby(["season", "week", "team"]):
    opp = d.opp.iloc[0]
    opp_players = w[(w.season == season) & (w.week == week) & (w.team == opp)]
    def_allowed.append({"season": season, "week": week, "team": team,
                        "allow_pass": opp_players.pass_yds.sum(), "allow_rec": opp_players.rec_yds.sum(),
                        "allow_rush": opp_players.rush_yds.sum()})
da = pd.DataFrame(def_allowed).sort_values(["season", "week"])
for col in ("allow_pass", "allow_rec", "allow_rush"):
    da[f"roll_{col}"] = da.groupby(["season", "team"])[col].transform(lambda s: s.shift(1).rolling(4, min_periods=3).mean())
w = w.merge(da[["season", "week", "team", "roll_allow_pass", "roll_allow_rec", "roll_allow_rush"]],
            on=["season", "week", "team"], how="left")
league_avg = da.groupby("season")[["allow_pass", "allow_rec", "allow_rush"]].mean()

# leak-free leader designation: season-to-date cumulative yards entering week
w["std_pass"] = w.groupby(["season", "player", "team"]).pass_yds.transform(lambda s: s.shift(1).expanding().sum())
w["std_rec"] = w.groupby(["season", "player", "team"]).rec_yds.transform(lambda s: s.shift(1).expanding().sum())
w["std_rush"] = w.groupby(["season", "player", "team"]).rush_yds.transform(lambda s: s.shift(1).expanding().sum())

def designate(d, pos_set, std_col, roll_col):
    c = d[d.pos.isin(pos_set) & d[roll_col].notna() & (d[std_col] > 0)]
    if len(c) == 0:
        return None
    return c.sort_values(std_col, ascending=False).iloc[0]

# ---- S6: prop singles vs proxy line ----
bets = []
combo_rows = []
for (season, week, team), d in w.groupby(["season", "week", "team"]):
    la = league_avg.loc[season]
    picks = {}
    for label, pos_set, std_col, roll_col, ycol, allow_col, la_col in (
        ("QB1", ["QB"], "std_pass", "roll_pass", "pass_yds", "roll_allow_pass", "allow_pass"),
        ("WR1", ["WR", "TE"], "std_rec", "roll_rec", "rec_yds", "roll_allow_rec", "allow_rec"),
        ("RB1", ["RB"], "std_rush", "roll_rush", "rush_yds", "roll_allow_rush", "allow_rush"),
    ):
        row = designate(d, pos_set, std_col, roll_col)
        if row is None:
            continue
        base = row[roll_col]
        allow = row[allow_col]
        factor = (allow / la[la_col]) if (pd.notna(allow) and la[la_col] > 0) else 1.0
        proj = base * factor
        line = round(base * 2) / 2  # proxy line = rolling mean rounded to 0.5
        picks[label] = (row, proj, line)
        edge = proj - line
        if abs(edge) < 5.0:
            continue
        side = "over" if edge > 0 else "under"
        actual = row[ycol]
        if actual == line:
            outcome, profit = "push", 0.0
        elif (actual > line) == (side == "over"):
            outcome, profit = "win", am_to_dec(-110) - 1
        else:
            outcome, profit = "loss", -1.0
        bets.append({"season": season, "week": week, "team": team, "player": row.player, "label": label,
                     "side": side, "proxy_line": line, "projection": round(proj, 1), "actual": actual,
                     "outcome": outcome, "profit": profit})
    # S7 combo: QB1 over + WR1 over (proxy lines), leak-free designation
    if "QB1" in picks and "WR1" in picks:
        (qr, qp, ql), (wr_, wp, wl) = picks["QB1"], picks["WR1"]
        qb_over = qr.pass_yds > ql
        wr_over = wr_.rec_yds > wl
        qb_push = qr.pass_yds == ql
        wr_push = wr_.rec_yds == wl
        combo_rows.append({"season": season, "week": week, "team": team,
                           "qb": qr.player, "wr": wr_.player, "qb_line": ql, "wr_line": wl,
                           "qb_over": bool(qb_over), "wr_over": bool(wr_over),
                           "qb_push": bool(qb_push), "wr_push": bool(wr_push)})

b = pd.DataFrame(bets)
write_df(b, "prop_bets_proxy.csv")
prop_summary = {}
for label, grp in b.groupby("label"):
    n = len(grp); wins = (grp.outcome == "win").sum(); losses = (grp.outcome == "loss").sum(); pushes = (grp.outcome == "push").sum()
    settled = wins + losses
    prop_summary[label] = {"n_bets": int(n), "wins": int(wins), "losses": int(losses), "pushes": int(pushes),
                           "hit_rate_ex_push": round(float(wins / settled), 4) if settled else None,
                           "roi_at_minus110": round(float(grp.profit.sum() / n), 4),
                           "breakeven_hit_rate": 0.5238}
cb = pd.DataFrame(combo_rows)
write_df(cb, "prop_combo_legs.csv")
valid = cb[~cb.qb_push & ~cb.wr_push]
p_qb = float(valid.qb_over.mean()); p_wr = float(valid.wr_over.mean())
p_joint = float((valid.qb_over & valid.wr_over).mean())
# bootstrap CI for lift
lifts = []
idx = np.arange(len(valid))
qo = valid.qb_over.to_numpy(); wo = valid.wr_over.to_numpy()
for _ in range(1000):
    i = rng.integers(0, len(valid), len(valid))
    pq, pw, pj = qo[i].mean(), wo[i].mean(), (qo[i] & wo[i]).mean()
    lifts.append(pj / (pq * pw))
combo_summary = {
    "n_team_games": int(len(valid)),
    "p_qb1_over_proxy": round(p_qb, 4), "p_wr1_over_proxy": round(p_wr, 4),
    "p_joint_both_over": round(p_joint, 4), "p_product_if_independent": round(p_qb * p_wr, 4),
    "correlation_lift_joint_over_product": round(p_joint / (p_qb * p_wr), 4),
    "lift_ci95": [round(float(np.percentile(lifts, 2.5)), 4), round(float(np.percentile(lifts, 97.5)), 4)],
    "fair_2leg_multiplier_vs_independent": round(p_joint / (p_qb * p_wr), 4),
    "interpretation": "A same-game QB-over + WR1-over parlay is worth ~lift x the independent-leg product probability. Books reprice SGPs; without archived SGP prices no edge can be claimed (G7 fails).",
}
save_json("props_summary.json", {"generated_utc": NOW, "tier": "Research-only (G7 fails: proxy market, no archived prop prices)",
                                  "proxy_line_rule": "rolling 4-game mean entering week, rounded to 0.5; min 3 prior games",
                                  "projection_rule": "rolling mean x (opponent rolling yards-allowed-to-position / league average)",
                                  "bet_rule": "|projection - proxy line| >= 5 yards; over/under accordingly; priced at -110 for illustration",
                                  "singles_vs_proxy": prop_summary, "combo_QB1_WR1": combo_summary})
print(json.dumps(prop_summary, indent=1))
print(json.dumps(combo_summary, indent=1))
print("05_props done.")

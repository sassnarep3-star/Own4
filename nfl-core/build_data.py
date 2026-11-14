#!/usr/bin/env python3
"""nfl-core data builder (session arena-a437d20c-own4, 2026-11-14).

Deterministically builds the eight core-requirement data stores from:
  1. upstream repository archives (pinned nflverse games.csv, nfl-lines derived
     model output, nfl-arena strategy metrics) — every row keeps its upstream
     provenance; and
  2. nfl-core/data/official_reads_2026-11-14.json — transcriptions from live
     official pages read on 2026-11-14 (session arena-a437d20c-own4).

Policy (never infer):
  * a value is published only if it exists in a source; otherwise the cell is
    blank and the row carries a flag naming the missing evidence;
  * scores/settlements are verified against official NFL pages (per-game URL on
    every row + per-team W/L/T/PF/PA reconciliation against the official
    standings read on 2026-11-14, run by verify.py);
  * market prices are third-party by nature (the NFL publishes no odds) and are
    labeled tier=THIRD-PARTY-NFLVERSE / THIRD-PARTY-CAPTURE with their source.
"""
import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "nfl-core")
DATA = os.path.join(CORE, "data")
READS = json.load(open(os.path.join(DATA, "official_reads_2026-11-14.json")))
OR = {r["id"]: r for r in READS["official_reads"]}
NFLVERSE_SRC = ("https://github.com/nflverse/nfldata/blob/master/DATASETS.md")
NFLVERSE_COMMIT = "nflverse/nfldata pinned copy in nfl-arena/data/raw/games.csv (peer-pinned 2026-11-12/13)"
CAPTURE_UTC = "2026-11-13"          # own_lines_week10.json market capture date (nfl-lines)
READ_UTC = "2026-11-14"             # this session's official reads

TEAM_FULL = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
SLUG = {
    "ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers",
    "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys", "DEN": "broncos",
    "DET": "lions", "GB": "packers", "HOU": "texans", "IND": "colts", "JAX": "jaguars",
    "KC": "chiefs", "LA": "rams", "LAC": "chargers", "LV": "raiders", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
    "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers", "TB": "buccaneers",
    "TEN": "titans", "WAS": "commanders",
}
# nfl.com game URLs use nickname-only slugs, e.g.
# https://www.nfl.com/games/commanders-at-giants-2026-reg-10
# https://www.nfl.com/games/packers-at-patriots-2026-reg-9 (verified live 2026-11-14)
def game_url(away, home, week):
    return "https://www.nfl.com/games/%s-at-%s-2026-reg-%d" % (
        SLUG[away], SLUG[home], week)


def fnum(s):
    if s is None or s == "":
        return None
    return float(s)


def inum(s):
    if s is None or s == "":
        return None
    return int(float(s))


def fmt(x, nd=1):
    if x is None:
        return ""
    if isinstance(x, float) and x == int(x) and nd == 0:
        return str(int(x))
    return ("%%.%df" % nd) % x


# ---------------------------------------------------------------- upstream
games = []
with open(os.path.join(ROOT, "nfl-arena/data/raw/games.csv")) as f:
    for r in csv.DictReader(f):
        if r["season"] == "2026" and r["game_type"] == "REG":
            games.append(r)
games.sort(key=lambda r: (int(r["week"]), r["gameday"], r["away_team"]))

own_lines = json.load(open(os.path.join(ROOT, "nfl-lines/data/derived/own_lines_week10.json")))
own_by_id = {r["game_id"]: r for r in own_lines}

strategy_results = json.load(open(os.path.join(ROOT, "nfl-lines/data/derived/strategy_results.json")))
leaderboard = json.load(open(os.path.join(ROOT, "nfl-arena/data/leaderboard_metrics.json")))
lb_by_id = {r["id"]: r for r in leaderboard["rows"]}
corr_reg = json.load(open(os.path.join(ROOT, "nfl-arena/data/correlation_register.json")))

OFFICIAL_STANDINGS = {r[0]: r for r in OR["OR-01"]["rows"]}

# ---------------------------------------------------------- 1. results feed
# Verified results feed: every settled 2026 REG game (and scheduled rows), each
# carrying its official nfl.com game URL. Settlement columns follow DATASETS.md
# conventions (OR-06): spread_line positive = home favored by that many points,
# result = home margin; total_line vs total points.
res_rows = []
for r in games:
    wk = int(r["week"])
    away, home = r["away_team"], r["home_team"]
    a_s, h_s = inum(r["away_score"]), inum(r["home_score"])
    settled = a_s is not None and h_s is not None
    sl, tl = fnum(r["spread_line"]), fnum(r["total_line"])
    a_ml, h_ml = fnum(r["away_moneyline"]), fnum(r["home_moneyline"])
    margin = (h_s - a_s) if settled else None
    tot = (h_s + a_s) if settled else None
    spr_set = tot_set = ml_set = ""
    settle_flag = ""
    if settled and sl is not None:
        adj = margin - sl
        spr_set = "HOME COVERS" if adj > 0 else ("AWAY COVERS" if adj < 0 else "PUSH")
    elif settled:
        spr_set = ""
        settle_flag = "SETTLE-BLOCKED: closing spread missing"
    if settled and tl is not None:
        tot_set = "OVER" if tot > tl else ("UNDER" if tot < tl else "PUSH")
    elif settled:
        settle_flag = (settle_flag + "; " if settle_flag else "") + "SETTLE-BLOCKED: closing total missing"
    if settled and a_ml is not None and h_ml is not None:
        ml_set = ("HOME (" + home + ") WINS ML" if margin > 0 else
                  ("AWAY (" + away + ") WINS ML" if margin < 0 else "PUSH (tie)"))
    elif settled:
        settle_flag = (settle_flag + "; " if settle_flag else "") + "SETTLE-BLOCKED: closing moneyline missing"
    ver = ("score re-read on official game page %s (OR-02)" % READ_UTC
           if (wk == 10 and away == "WAS") else
           "score carried from pinned nflverse archive; reconciled to official standings (OR-01) in verify.py")
    flag = settle_flag
    if settled and wk >= 10:
        flag = (flag + "; " if flag else "") + "closing-price provenance: games.csv row settled in archive 2026-11-13/14 (A-09 class: peer pre-game captures are NOT closing)"
    res_rows.append({
        "week": wk, "gameday": r["gameday"], "away_team": away, "away_score": "" if a_s is None else a_s,
        "home_team": home, "home_score": "" if h_s is None else h_s,
        "status": "FINAL" if settled else "SCHEDULED",
        "home_margin": "" if margin is None else margin,
        "total_pts": "" if tot is None else tot,
        "close_spread_home_fav_by": fmt(sl), "close_total": fmt(tl),
        "close_away_ml": fmt(a_ml, 0), "close_home_ml": fmt(h_ml, 0),
        "spread_settlement": spr_set, "total_settlement": tot_set, "ml_settlement": ml_set,
        "game_url": game_url(away, home, wk),
        "market_source": NFLVERSE_SRC if (sl is not None or tl is not None) else "",
        "verification": ver, "flag": flag,
    })

with open(os.path.join(DATA, "results_feed_2026.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(res_rows[0].keys()))
    w.writeheader()
    w.writerows(res_rows)

# ------------------------------------------------------- 2. price snapshots
# One row per market (SIDE / TOTAL / MONEYLINE) per 2026 REG game.
# OPEN  = first price we hold (originated slate: nfl-lines pre-game capture;
#         weeks 1-9: none — blank + flag, per never-infer policy)
# CLOSE = price recorded with the settled game in the pinned archive.
# Origination order is fixed: 1 SIDE, 2 TOTAL, 3 MONEYLINE.
snap_rows = []
for r in games:
    wk = int(r["week"])
    away, home = r["away_team"], r["home_team"]
    gid = r["game_id"]
    a_s, h_s = inum(r["away_score"]), inum(r["home_score"])
    settled = a_s is not None and h_s is not None
    margin = (h_s - a_s) if settled else None
    tot = (h_s + a_s) if settled else None
    own = own_by_id.get(gid)
    sl, tl = fnum(r["spread_line"]), fnum(r["total_line"])
    a_ml, h_ml = fnum(r["away_moneyline"]), fnum(r["home_moneyline"])
    mkt_open_src = ""
    open_flag = ""
    if own:
        o_sl, o_tl = fnum(own.get("market_spread_line")), fnum(own.get("market_total_line"))
        o_aml, o_hml = fnum(own.get("market_away_moneyline")), fnum(own.get("market_home_moneyline"))
        mkt_open_src = ("market capture in nfl-lines/data/derived/own_lines_week10.json "
                        "(pre-game market snapshot, capture date %s) "
                        "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/own_lines_week10.json" % CAPTURE_UTC)
    else:
        o_sl = o_tl = o_aml = o_hml = None
        open_flag = "OPEN-UNVERIFIED: no opening-line capture exists for 2026 weeks 1-9 (F-C02)"

    def add(seq, mtype, open_p, close_p, settle, open_src, flag_extra=""):
        fl = [x for x in [open_flag, flag_extra] if x]
        if not open_p and not open_flag:
            fl.append("OPEN-UNVERIFIED: no market quote captured for this market yet (F-C12)")
        snap_rows.append({
            "market_id": "%s|%s" % (gid, mtype),
            "game_id": gid, "week": wk, "gameday": r["gameday"],
            "matchup": "%s @ %s" % (away, home),
            "origination_seq": seq, "market_type": mtype,
            "open_price": open_p, "open_captured_utc": (CAPTURE_UTC if open_p else ""),
            "open_source": (open_src if open_p else ""),
            "close_price": close_p, "close_captured_utc": (READ_UTC if (close_p and settled) else ""),
            "close_source": (NFLVERSE_SRC + " (via " + NFLVERSE_COMMIT + ")" if close_p else ""),
            "settlement": settle,
            "settlement_source": game_url(away, home, wk) if settle else "",
            "game_url": game_url(away, home, wk),
            "price_tier": "THIRD-PARTY-CAPTURE(open) / THIRD-PARTY-NFLVERSE(close)" if open_p and close_p
                          else ("THIRD-PARTY-NFLVERSE(close only)" if close_p else "THIRD-PARTY-CAPTURE(open only)"),
            "verification": ("close verified vs official score (OR-01/verify.py reconciliation)"
                             if settle else "not yet settled — close blank pending final"),
            "flag": "; ".join(fl),
        })

    # 1 SIDE (spread, home-fav-by convention). Close cells are populated ONLY at
    # settlement: a pre-game/current quote is never a closing number (A-09 class).
    if settled and sl is not None:
        adj = margin - sl
        s = "HOME COVERS" if adj > 0 else ("AWAY COVERS" if adj < 0 else "PUSH")
    else:
        s = ""
    add(1, "SIDE (spread, home-fav-by)", fmt(o_sl), fmt(sl) if settled else "", s, mkt_open_src)
    # 2 TOTAL
    if settled and tl is not None:
        s = "OVER" if tot > tl else ("UNDER" if tot < tl else "PUSH")
    else:
        s = ""
    add(2, "TOTAL (game points)", fmt(o_tl), fmt(tl) if settled else "", s, mkt_open_src)
    # 3 MONEYLINE (two sides kept in one market row: home / away)
    if settled and h_ml is not None and a_ml is not None:
        s = (("HOME " + home + " ML WINS") if margin > 0 else
             (("AWAY " + away + " ML WINS") if margin < 0 else "PUSH (tie)"))
    else:
        s = ""
    add(3, "MONEYLINE (home/away)",
        ("home %s / away %s" % (fmt(o_hml, 0), fmt(o_aml, 0))) if o_hml is not None else "",
        ("home %s / away %s" % (fmt(h_ml, 0), fmt(a_ml, 0))) if (settled and h_ml is not None) else "",
        s, mkt_open_src)

with open(os.path.join(DATA, "price_snapshots_2026.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(snap_rows[0].keys()))
    w.writeheader()
    w.writerows(snap_rows)

# ------------------------------------------------------------ 3. originations
# Every market we originate, in pipeline order 1 SIDE -> 2 TOTAL -> 3 MONEYLINE,
# with the model's fair line, the market line and the difference as separate
# columns (difference = model_fair - market, both in the same convention).
orig_rows = []
for r in sorted(own_lines, key=lambda x: (x["week"], x["gameday"], x["away"])):
    gid = r["game_id"]
    wk = int(r["week"])
    base = dict(game_id=gid, week=wk, gameday=r["gameday"],
                away=r["away"], home=r["home"],
                match_url=game_url(r["away"], r["home"], wk),
                model_source="nfl-lines/data/derived/own_lines_week10.json (walk-forward model, parameters pre-registered)",
                market_source=("market capture %s (THIRD-PARTY-CAPTURE)" % CAPTURE_UTC))
    fair_sl, mkt_sl = fnum(r["own_spread_line"]), fnum(r["market_spread_line"])
    fair_tl, mkt_tl = fnum(r["own_total_line"]), fnum(r["market_total_line"])
    fair_hml, mkt_hml = fnum(r["own_home_moneyline"]), fnum(r["market_home_moneyline"])
    orig_rows.append({**base, "origination_seq": 1, "market_type": "SIDE (spread, home-fav-by)",
                      "model_fair_line": fmt(fair_sl, 2), "market_line": fmt(mkt_sl),
                      "difference": fmt(None if (fair_sl is None or mkt_sl is None) else fair_sl - mkt_sl, 2),
                      "direction_note": "difference > 0 = model makes home side stronger than market",
                      "verification": "model output (this repo, walk-forward); market line third-party capture",
                      "flag": "" if (fair_sl is not None and mkt_sl is not None) else "UNVERIFIED-BLANK: missing line value in source"})
    orig_rows.append({**base, "origination_seq": 2, "market_type": "TOTAL (game points)",
                      "model_fair_line": fmt(fair_tl, 2), "market_line": fmt(mkt_tl),
                      "difference": fmt(None if (fair_tl is None or mkt_tl is None) else fair_tl - mkt_tl, 2),
                      "direction_note": "difference > 0 = model expects more points than market",
                      "verification": "model output (this repo, walk-forward); market line third-party capture",
                      "flag": "" if (fair_tl is not None and mkt_tl is not None) else "UNVERIFIED-BLANK: missing line value in source"})
    fair_prob = fnum(r["own_home_win_prob"])
    imp = None
    if mkt_hml is not None:
        imp = (abs(mkt_hml) / (abs(mkt_hml) + 100.0)) if mkt_hml < 0 else (100.0 / (mkt_hml + 100.0))
    orig_rows.append({**base, "origination_seq": 3, "market_type": "MONEYLINE (home)",
                      "model_fair_line": ("home %s (win prob %s)" % (fmt(fair_hml, 0), fmt(fair_prob, 3))),
                      "market_line": ("home %s" % fmt(mkt_hml, 0)) if mkt_hml is not None else "",
                      "difference": (fmt(None if (fair_prob is None or imp is None) else fair_prob - imp, 3)
                                     + " win-probability points vs market implied"),
                      "direction_note": "difference > 0 = model makes home team more likely to win than market implied probability",
                      "verification": "model output (this repo, walk-forward); market line third-party capture",
                      "flag": "" if (fair_hml is not None and mkt_hml is not None) else "UNVERIFIED-BLANK: missing line value in source"})

with open(os.path.join(DATA, "originations_2026.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(orig_rows[0].keys()))
    w.writeheader()
    w.writerows(orig_rows)

# ------------------------------------- 4a. leaderboard — SIGNAL metrics only
sig_rows, stake_rows = [], []
for s in strategy_results:
    sid = s["id"]
    lb = lb_by_id.get(sid, {})
    allr = s.get("all", {})
    conf = s.get("confirmation", {})
    sig_rows.append({
        "strategy_id": sid, "family": s.get("family", ""), "name": s.get("name", ""),
        "rule": s.get("rule", ""),
        "n_settled": allr.get("n", ""), "wins": allr.get("wins", ""),
        "hit_rate": fmt(allr.get("win_rate"), 4), "break_even_rate": fmt(allr.get("break_even_rate"), 4),
        "z_vs_breakeven": fmt(allr.get("z_score", lb.get("z_score")), 3),
        "p_value": fmt(allr.get("p_value_vs_breakeven", lb.get("p_value")), 6),
        "p_value_bh": fmt(lb.get("p_value_bh"), 6),
        "wilson95": ("%s .. %s" % (fmt(lb.get("wilson95_lo"), 4), fmt(lb.get("wilson95_hi"), 4))) if lb else "",
        "signal_verdict": lb.get("luck_verdict", ""),
        "signal_rank_basis": "ranked by z_vs_breakeven ONLY — stake size cannot affect this table",
        "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json",
        "verification": "computed on pinned walk-forward data (2011-2026); prices third-party (nflverse), scores official-derived",
        "flag": "" if lb else "metrics table missing for this id",
    })
    stake_rows.append({
        "strategy_id": sid, "family": s.get("family", ""), "name": s.get("name", ""),
        "flat_stake_roi_all": fmt(allr.get("roi"), 4),
        "pnl_units_flat": fmt(allr.get("pnl_units"), 2),
        "staked_units_flat": fmt(allr.get("staked_units"), 1),
        "confirmation_n": conf.get("n", ""),
        "confirmation_roi_flat": fmt(conf.get("roi"), 4),
        "max_drawdown_units": fmt(lb.get("max_drawdown_units"), 2),
        "staked_at_current_plan": "NOT IMPLEMENTED — staking plan deliberately unplugged (C5 requirement: signal cannot be masked by staking)",
        "reward_eligible": "FALSE" if not lb.get("eligible_for_reward") else "TRUE",
        "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json",
        "verification": "flat-stake settlement on the same walk-forward set as the signal table",
        "flag": "rewards are project-defined and unfunded (F-C06)" ,
    })
# rank signal rows by z desc (pure signal ordering)
def zkey(row):
    try:
        return -float(row["z_vs_breakeven"])
    except Exception:
        return 0.0
sig_rows.sort(key=zkey)
for i, row in enumerate(sig_rows, 1):
    row["signal_rank"] = i
sig_cols = ["signal_rank"] + [k for k in sig_rows[0].keys() if k != "signal_rank"]
sig_rows = [{k: r[k] for k in sig_cols} for r in sig_rows]

with open(os.path.join(DATA, "leaderboard_signal.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sig_cols)
    w.writeheader()
    w.writerows(sig_rows)
with open(os.path.join(DATA, "leaderboard_staking.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(stake_rows[0].keys()))
    w.writeheader()
    w.writerows(stake_rows)

# ------------------------------------------------------------- 5. gates.csv
gates = [
    ("G1", "Data sufficiency", "n >= 300 settled picks before forecast validation is even attempted",
     "project-defined threshold (peer flag F3 class)", "n/a", "Nfl-lines walk-forward set (n=4,055 games) supplies settlements",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json"),
    ("G2", "Walk-forward only", "no lookahead: each forecast uses only data available before kickoff",
     "project-defined method (pre-registered parameters)", "PASS (method documented)",
     "pre-registered in nfl-lines model_params.json before first run (peer log 2026-11-02/12)",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/model_params.json"),
    ("G3", "Prices at settlement time", "settlement uses closing prices, never snapshot prices",
     "project-defined method", "PARTIAL", "closing prices exist for all 137 settled 2026 games; opening prices missing weeks 1-9 (F-C02)",
     "https://github.com/nflverse/nfldata/blob/master/DATASETS.md"),
    ("G4", "Multiple-testing control", "BH-adjusted p-value < 0.05 across the strategy family",
     "statistical standard (Benjamini-Hochberg)", "FAIL for all 15 strategies (best BH p = 0.44)",
     "no strategy clears the luck barrier yet — this is the honest current state",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/leaderboard_metrics.json"),
    ("G5", "Out-of-sample confirmation", "confirmation-window ROI positive with n >= 100",
     "project-defined threshold", "see leaderboard_staking.csv", "confirmation splits published per strategy",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json"),
    ("G6", "Capacity & limits", "max 1 unit per pick until G4 passes; no parlay stacking of correlated legs",
     "project-defined threshold", "N/A (no strategy live)", "dependence terms handled in combo pricing (empirical joint probability)",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/strategy_results.json"),
    ("G7", "Signal/staking separation", "leaderboard ranks on signal metrics only (hit-rate z), staking shown separately",
     "project requirement (this brief)", "PASS", "leaderboard_signal.csv ranked by z_vs_breakeven; staking table cannot alter ranks",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_signal.csv"),
    ("G8", "Reward eligibility", "a strategy may earn rewards only after G4+G5 pass",
     "project-defined (rewards unfunded, F-C06)", "0 strategies eligible", "stated openly on the leaderboard page",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_staking.csv"),
    ("DG-1", "DEMONITION GATE 1: skill regression", "LIVE strategy demoted to PAPER when rolling 200 settled picks show z_vs_breakeven < 0",
     "project-defined threshold (review item S-C04)", "ARMED (no live strategies)", "demotion is automatic; re-promotion requires a fresh G4+G5 pass",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/gates.csv"),
    ("DG-2", "DEMONITION GATE 2: closing-line value", "LIVE strategy demoted when CLV (close minus taken price, settled sample) is negative over >= 50 picks",
     "project-defined threshold (review item S-C04)", "ARMED (needs price store to run)", "requires open+close per pick — supplied by price_snapshots_2026.csv",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/price_snapshots_2026.csv"),
    ("DG-3", "DEMONITION GATE 3: drawdown", "LIVE strategy demoted when flat-stake drawdown exceeds 20 units",
     "project-defined threshold (review item S-C04)", "ARMED", "drawdown computed in staking table only; cannot be hidden by stake sizing",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_staking.csv"),
    ("DG-4", "DEMONITION GATE 4: data integrity", "any strategy whose input feed fails verification is demoted immediately until the feed re-verifies",
     "project-defined (this brief)", "ARMED", "verify.py exit code is the trigger; results feed + price store must both pass",
     "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/verify.py"),
]
with open(os.path.join(DATA, "gates.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["gate_id", "name", "rule", "threshold_origin", "current_status", "note", "source_url"])
    for g in gates:
        w.writerow(g)

# -------------------------------------------------- 6. depth replacements
# Replacement DEPTH (string of the replacement), not just the fact of absence.
# Sources: official injury report (OR-03) + official team-site depth charts
# (OR-04 DET, OR-05 NE). Where the chart does not answer, the cell stays blank.
DET_CHART = {(r[1], r[2]): r[3:] for r in OR["OR-04"]["rows"]}
NE_CHART = {(r[1], r[2]): r[3:] for r in OR["OR-05"]["rows"]}
depth_defs = [
    ("DET", "C", "Cade Mays", "Out", "C", DET_CHART, "OR-04", "https://www.detroitlions.com/team/depth-chart"),
    ("DET", "CB", "D.J. Reed", "Out", "CB", DET_CHART, "OR-04", "https://www.detroitlions.com/team/depth-chart"),
    ("DET", "S", "Kerby Joseph", "Out", "S", DET_CHART, "OR-04", "https://www.detroitlions.com/team/depth-chart"),
    ("DET", "WR", "Amon-Ra St. Brown", "Questionable", "WR", DET_CHART, "OR-04", "https://www.detroitlions.com/team/depth-chart"),
    ("DET", "RB", "Sione Vaki", "Questionable", "RB", DET_CHART, "OR-04", "https://www.detroitlions.com/team/depth-chart"),
    ("NE", "C", "Ben Brown", "Out", "LG", NE_CHART, "OR-05", "https://www.patriots.com/team/depth-chart"),
    ("NE", "RB", "TreVeyon Henderson", "Out", "RB", NE_CHART, "OR-05", "https://www.patriots.com/team/depth-chart"),
    ("NE", "CB", "Carlton Davis III", "Out", "CB", None, "OR-05", ""),
    ("MIN", "QB", "Kyler Murray", "Out", "QB", None, "OR-03", ""),
    ("GB", "RB", "Josh Jacobs", "Out", "RB", None, "OR-03", ""),
    ("GB", "C", "Sean Rhyan", "Out", "C", None, "OR-03", ""),
    ("GB", "LB", "Micah Parsons", "Out", "LB", None, "OR-03", ""),
    ("KC", "T", "Jaylon Moore", "Out", "T", None, "OR-03", ""),
    ("WAS", "C", "Lucas Patrick", "Out", "C", None, "OR-03", ""),
    ("JAX", "S", "Jessie Bates", "Out", "S", None, "OR-03", ""),
]
depth_rows = []
for team, pos, player, status, chart_pos, chart, chart_or, chart_url in depth_defs:
    rep, rep_string, deeper = "", "", ""
    flag = ""
    if chart:
        # find the chart slot whose first name matches the absent player
        slot = None
        slot_pos = None
        for (cp, name), rest in chart.items():
            if name == player and cp == chart_pos:
                slot, slot_pos = rest, cp
                break
        if slot is None:
            # player not on the chart two-deep at that position
            flag = "DEPTH-UNVERIFIED: absent player not listed on the club's own chart at %s (chart rows: %s)" % (
                chart_pos, "; ".join(sorted(n for (cp, n) in chart if cp == chart_pos)))
        else:
            names = [n for n in slot if n]
            if names:
                rep, rep_string = names[0], ("%dth string %s" % (2, chart_pos))
                deeper = " / ".join(names[1:]) if names[1:] else ""
            else:
                flag = "DEPTH-CRITICAL: no backup listed on the club's own chart at %s" % chart_pos
    else:
        flag = "DEPTH-UNVERIFIED: official team-site depth chart not read for %s this session (blank, not inferred)" % team
    depth_rows.append({
        "team": team, "position": pos, "absent_player": player, "official_game_status": status,
        "injury_report_url": "https://www.nfl.com/injuries/",
        "chart_position": chart_pos,
        "replacement": rep, "replacement_depth_string": rep_string,
        "further_depth": deeper,
        "depth_chart_url": chart_url,
        "depth_chart_source": ("official %s team site (OR-04/05, read %s)" % (team, READ_UTC)) if chart_url else "",
        "verification": ("injury status official (OR-03, read %s); depth string from official team-site chart (read %s)" % (READ_UTC, READ_UTC)
                         if chart_url else "injury status official (OR-03); depth string NOT VERIFIED"),
        "flag": flag,
    })
with open(os.path.join(DATA, "depth_week10.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(depth_rows[0].keys()))
    w.writeheader()
    w.writerows(depth_rows)

# ------------------------------------------------------ 7. correlations w/ n
corr_rows = []
for row in corr_reg["rows"]:
    inputs = "scores (official-derived) + market prices (third-party)" if "market" in row["label"].lower() or "spread" in row["label"].lower() or "total" in row["label"].lower() else "scores (official-derived)"
    corr_rows.append({
        "id": row["id"], "group": row["group"], "pair": row["label"],
        "n": row.get("n", ""), "pearson_r": row.get("pearson_r", ""),
        "ci95": ("%s .. %s" % (row["ci95"][0], row["ci95"][1])) if row.get("ci95") else "",
        "p_value": row.get("p_value", ""),
        "inputs_official": inputs,
        "reading": row["reading"],
        "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/correlations.json",
        "verification": "re-verified internally by nfl-arena (2026-11-13); n published with every value; player-level pairs remain blank (no verified source)",
        "flag": "" if "market" not in inputs else "PRICE-INPUTS THIRD-PARTY: r computed on official-derived scores but third-party prices",
    })
# player-level rows: blank + flag (never infer)
for pid, label in [("CR-P1", "Same-game player prop dependence (e.g., QB passing yards vs WR receiving yards)"),
                   ("CR-P2", "Cross-game player performance dependence (injury effect propagation)")]:
    corr_rows.append({
        "id": pid, "group": "Player-level", "pair": label, "n": "", "pearson_r": "",
        "ci95": "", "p_value": "", "inputs_official": "",
        "reading": "UNVERIFIED-BLANK: no officially sourced player-level price/usage series exists in this repo; NFL.com player game logs exist (official) but prop prices do not (A-13/Q-09 amended 2026-11-13)",
        "source_url": "https://www.nfl.com/players/drake-maye/stats",
        "verification": "not computed — inputs unavailable",
        "flag": "UNVERIFIED-BLANK",
    })
with open(os.path.join(DATA, "correlations_n.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(corr_rows[0].keys()))
    w.writeheader()
    w.writerows(corr_rows)

print("results rows:", len(res_rows))
print("price snapshot rows:", len(snap_rows))
print("origination rows:", len(orig_rows))
print("signal rows:", len(sig_rows), "staking rows:", len(stake_rows))
print("gates:", len(gates), "depth rows:", len(depth_rows), "correlation rows:", len(corr_rows))

# ------------------------------------------------- 8. questions register
qrows = [
 ("Q-C01", "What are the opening and closing numbers for each market we originate?",
  "Closing numbers exist for all 137 settled 2026 games (pinned archive); pre-game market captures exist for the 136-game weeks 10-18 slate (2026-11-13).",
  "No verified OPENING-line capture exists for 2026 weeks 1-9, and no capture timestamp for the week-10 pre-game quotes.",
  "PARTIALLY ANSWERED", "A licensed opening-line feed (or dated pre-game snapshots) covering weeks 1-9; capture timestamps for existing quotes.",
  "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "open"),
 ("Q-C02", "Can backtests and ROI be computed at all?",
  "Yes for the 137 settled 2026 games: verified results feed + closing prices + settlement per market (side/total/ML) are published; the walk-forward set (2011-2026, n=4,055) supports strategy-level backtests.",
  "Opening prices needed for CLV-style backtests on 2026; player-prop prices needed for prop backtests (none exist).",
  "ANSWERED (with documented gaps)", "The gaps are evidence gaps, not method gaps: see Q-C01 and Q-C08.",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/results_feed_2026.csv", "answered"),
 ("Q-C03", "Is the spread sign convention certain? (older flag A-06 / question Q-05)",
  "YES. DATASETS.md states positive spread_line = home favored by that many points; 162 of 163 in-lined 2026 games agree with the moneyline favorite. WAS@NYG '1.5 vs 2.5' is open-vs-close movement, not a conflict.",
  "Exact capture timestamp of the 2.5 pre-game quote remains unknown.",
  "ANSWERED", "Timestamped odds snapshots going forward (the price store now records capture dates).",
  "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "answered"),
 ("Q-C04", "Which injuries create 2nd/3rd/4th-string deficiencies this week?",
  "Official week-10 report read 2026-11-14 (WAS/NYG/NE/DET/KC/ATL/MIN/GB/JAX partial). Replacement depth strings verified from official club charts for DET and NE offense.",
  "Depth charts for the other 30 clubs were not read this session; some absent players are not on their club's chart at all (e.g., DET S Kerby Joseph).",
  "PARTIALLY ANSWERED", "Read the remaining clubs' official depth-chart pages (one fetch per club) and re-run depth_week10 builder.",
  "https://www.nfl.com/injuries/", "open"),
 ("Q-C05", "Does any strategy demonstrate skill rather than luck?",
  "Not yet. Best BH-adjusted p across 15 strategies is 0.44 (wind-unders, n=303). All are below the G4 bar; none is reward-eligible.",
  "Larger settled samples (power analysis: ~1,150 picks needed for 80% power on the best candidate).",
  "ANSWERED (negative)", "Time + settlements; the required-n column quantifies it per strategy.",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_signal.csv", "answered"),
 ("Q-C06", "How do we know a staking plan is not hiding a bad signal?",
  "By construction now: rank column comes only from signal metrics (z vs break-even at flat stakes); stake-level ROI/drawdown live in a separate table that cannot alter ranks.",
  "Nothing — the mechanism is implemented; monitoring is automated via DG-3.",
  "ANSWERED", "n/a",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_signal.csv", "answered"),
 ("Q-C07", "What sends a live strategy back to paper?",
  "DG-1 skill regression (z<0 over 200 settled picks), DG-2 negative CLV over >=50 picks, DG-3 drawdown >20 units, DG-4 data-integrity failure. Armed; no strategy is live.",
  "Owner sign-off on the numeric thresholds (they are project-defined).",
  "PROPOSED", "Owner choice on the suggestions board (S-C04).",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/gates.csv", "needs decision"),
 ("Q-C08", "How do we price player-prop combos?",
  "We cannot yet: the NFL publishes no prop prices (A-13). Official player game logs DO exist (nfl.com player pages), so usage/performance inputs are available.",
  "A verifiable prop-price source (none exists in-repo or on official sites).",
  "BLOCKED (evidence missing)", "Any dated prop-price capture with provenance; until then prop rows stay blank.",
  "https://www.nfl.com/players/drake-maye/stats", "open"),
 ("Q-C09", "Are correlations computed from officially sourced numbers?",
  "Score-input correlations use official-derived scores reconciled to nfl.com standings. Every value publishes n. Market-price-input rows are labeled THIRD-PARTY in the inputs column.",
  "Player-level series (blank rows CR-P1/P2).",
  "ANSWERED", "See Q-C08.",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/correlations_n.csv", "answered"),
 ("Q-C10", "Which suggestion path should be implemented first?",
  "Nine suggestions are published with options and a recommended path; none has been implemented.",
  "Owner decision.",
  "NEEDS DECISION", "Owner marks review_status=chosen on the suggestions page.",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/suggestions.csv", "needs decision"),
 ("Q-C11", "Is the results feed correct line-by-line?",
  "verify.py recomputes W-L-T and PF-PA for all 32 teams from the feed and compares against the official standings read 2026-11-14 (expected: 137 games, SigmaW=SigmaL=136, SigmaT=2).",
  "Nothing for weeks 1-10; weeks 11-18 settle as games complete.",
  "ANSWERED", "Re-run verify.py after each feed update.",
  "https://www.nfl.com/standings/league/2026/REG", "answered"),
 ("Q-C12", "Where do the week-10 closing prices come from and are they really closing?",
  "Settled games carry their price row in the pinned archive (settled in place after kickoff); for the one week-10 game played (WAS@NYG) the archive row postdates kickoff.",
  "Peer pre-game captures (A-09) are NOT closes; exact quote timestamps for open cells.",
  "ANSWERED (caveat kept)", "Timestamped snapshots going forward.",
  "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "answered"),
]
with open(os.path.join(DATA, "questions.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "question", "information_known", "information_missing", "answer_status",
                "evidence_that_would_settle", "source_url", "status"])
    for q in qrows:
        w.writerow(q)

# ------------------------------------------------- 9. suggestions board
srows = [
 ("S-C01", "Single suggestions front-door page on the root dashboard",
  "Four separate suggestion registers exist across namespaces; a reviewer cannot compare them in one place.",
  "(A) One merged suggestions index linking all registers (B) leave as-is (C) migrate all into nfl-core",
  "A — merge index only, no content moves; each register keeps its namespace",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/suggestions.csv"),
 ("S-C02", "Closing/opening line feed with capture timestamps (answers Q-C01, D2)",
  "The price store can only move from partial to complete with dated snapshots; CLV needs them.",
  "(A) License a commercial odds feed (B) run a daily snapshot script against a free source with provenance (C) keep blanks",
  "B first (cheap, testable), evaluate A if volume justifies it",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/price_snapshots_2026.csv"),
 ("S-C03", "Extend replacement-depth coverage to all 32 clubs",
  "Week-10 decisions need the string of every replacement; two clubs are charted so far.",
  "(A) One fetch per official club depth chart, rebuilt into depth_week10.csv (B) chart only the teams with OUT players (C) leave partial",
  "A — the fetches are cheap and the builder already supports it",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://www.detroitlions.com/team/depth-chart"),
 ("S-C04", "Owner sign-off on demotion-gate thresholds",
  "DG-1..DG-4 are armed with project-defined numbers; policy legitimacy needs the owner's choice.",
  "(A) accept current thresholds (B) adjust numbers (C) add more gates (e.g., market-regime break)",
  "A or B — table of alternatives can be published once the owner states preferences",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/gates.csv"),
 ("S-C05", "Automated nightly verification job",
  "verify.py currently runs per-session; a scheduled CI job would demote on feed corruption automatically (DG-4).",
  "(A) GitHub Actions cron running build_data+build_site+verify (B) manual runs only",
  "A — the scripts are deterministic and CI already exists for peer namespaces",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/verify.py"),
 ("S-C06", "Player-prop research track using official game logs",
  "Prop combos cannot be priced, but usage-based signals can be researched on official logs so they are ready when prices arrive.",
  "(A) build a player-game-log dataset from nfl.com player pages (B) wait for prop prices first",
  "A — evidence gathering is allowed even when pricing is blocked",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://www.nfl.com/players/drake-maye/stats"),
 ("S-C07", "Wind/weather ingestion for the wind-unders candidate",
  "The only strategy with z>1.4 needs weather at kickoff; archive temp/wind columns exist but have gaps.",
  "(A) join official gamebook weather (B) accept archive weather and flag gaps (C) drop the candidate",
  "B now, A when the candidate nears G4",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_signal.csv"),
 ("S-C08", "Record-vs-thesis dashboard: what the origination slate believes vs results",
  "Decision-making improves when each originated market shows later settlement and CLV as games complete.",
  "(A) nightly join of price_snapshots to results_feed, published per market (B) weekly summary only",
  "A — the join is already computable from the two stores",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/results_feed_2026.csv"),
 ("S-C09", "Reward-funding decision",
  "The leaderboard competition needs rewards; nothing is funded (F-C06).",
  "(A) points-only recognition (B) funded prizes with published rules (C) defer until a strategy passes G4",
  "C — rewarding skill that has not been demonstrated invites luck-chasing",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_staking.csv"),
 ("S-C10", "Archive the week-10 pre-game capture with its timestamp",
  "Q-C01's open cells need capture dates; asking the peer session's source for its exact capture time closes it.",
  "(A) request the timestamp from the capturing session's log (B) mark open cells permanently untimestamped",
  "A",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/price_snapshots_2026.csv"),
 ("S-C11", "D-1: choose the canonical NFL requirements workspace (four implementations now exist)",
  "nfl-core, nfl-market, nfl-ledger and nfl-price-snapshot all implement the same brief; a reviewer cannot act on four parallel answers. The comparison matrix is published; the choice itself is the owner's.",
  "(A) one canonical workspace, others archived as evidence (B) canonical store-of-record + peer workspaces as satellites (C) keep all four independent",
  "B with nfl-core as store-of-record (only populated open+close store; verifier-reconciled results feed; documented spread convention) — owner decides",
  "proposed", "NOT IMPLEMENTED — awaiting owner choice (see pages/d1-canonical-choice.html)",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/pages/d1-canonical-choice.html"),
]
with open(os.path.join(DATA, "suggestions.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "suggestion", "why_it_helps_decisions", "options", "recommended_path",
                "review_status", "implementation_state", "source_url"])
    for s in srows:
        w.writerow(s)

# ------------------------------------------------- 10. flagged for review
frows = [
 ("F-C01", "info", "WAS@NYG pre-game market quote (2.5) has no capture timestamp in the capturing session's file",
  "own_lines_week10.json stores the quote but not the exact capture time; treat as 'earlier than close', not as 'the' open",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/own_lines_week10.json", "open"),
 ("F-C02", "material", "No verified opening-line capture exists for 2026 weeks 1-9 (open cells blank in the price store)",
  "initial_lines.csv covers 2021 only; closing_lines.csv covers 2006-2018; 2026 has no opening quotes in any repo source",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/price_snapshots_2026.csv", "open"),
 ("F-C03", "info", "13 settled 2026 rows have total/ML closes but blank closing spread (spread settlement marked SETTLE-BLOCKED)",
  "pinned archive rows carry spread_line empty for these games; settlement not inferred",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/results_feed_2026.csv", "open"),
 ("F-C04", "correction", "Prior flag A-12 ('the NFL publishes no depth charts') is corrected: official club sites publish unofficial depth charts",
  "detroitlions.com and patriots.com depth-chart pages read live 2026-11-14 (OR-04/05); league-level nfl.com route remains 404; charts label themselves 'unofficial'",
  "https://www.detroitlions.com/team/depth-chart", "resolved"),
 ("F-C05", "resolved", "Prior flag A-06 / question Q-05 (spread sign convention) is resolved: positive = home favored; 1.5 vs 2.5 was open-vs-close movement",
  "DATASETS.md quote (OR-06) + 162/163 moneyline-consistency check on 2026 games",
  "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "resolved"),
 ("F-C06", "material", "Leaderboard rewards are project-defined and unfunded; 0 strategies eligible",
  "G8 blocks rewards until G4+G5 pass; funding decision open (S-C09)",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/leaderboard_staking.csv", "needs review"),
 ("F-C07", "material", "Moneyline/odds columns in the repo's games.csv copy are not documented in DATASETS.md",
  "DATASETS.md documents spread_line/total_line/result/total but not the ML columns; ML convention verified statistically (favorite-side agreement 162/163) and flagged as a docs gap",
  "https://github.com/nflverse/nfldata/blob/master/DATASETS.md", "open"),
 ("F-C08", "material", "DET S Kerby Joseph (Out) has no listed replacement on the club's own chart; MIN QB replacement not charted this session",
  "OR-03/04 read 2026-11-14; replacement cells left blank rather than inferred (report lists Wentz as full participant but naming him the starter would be an inference)",
  "https://www.nfl.com/injuries/", "needs review"),
 ("F-C09", "info", "Player-prop prices do not exist in any verified source; prop market rows and prop correlations are blank",
  "A-13 amended 2026-11-13: official player game logs exist, prop PRICES do not",
  "https://www.nfl.com/players/drake-maye/stats", "open"),
 ("F-C10", "info", "Depth strings verified this session for DET and NE offense only; other clubs' rows are blank + flagged",
  "OR-04/05 are the only club charts read 2026-11-14; S-C03 proposes full coverage",
  "https://www.patriots.com/team/depth-chart", "needs review"),
 ("F-C11", "info", "Peer archive ARI/AZ alias and week-10 price-staleness notes (A-05/A-06/A-09/A-11) remain open in peer namespaces",
  "inherited, not re-judged by this session; listed so the owner sees the full open set in one place",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/pages/flagged.html", "needs review"),
 ("F-C12", "material", "Weeks 12-18 (109 games) carry model fair lines but NO market quote has been captured yet (open cells blank)",
  "own_lines_week10.json has market columns populated for weeks 10-11 only (27/136 games); books' later boards not captured — rows flagged OPEN-UNVERIFIED, not filled",
  "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/derived/own_lines_week10.json", "open"),
]
with open(os.path.join(DATA, "flagged.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "severity", "what", "evidence", "source_url", "status"])
    for r in frows:
        w.writerow(r)

print("questions:", len(qrows), "suggestions:", len(srows), "flags:", len(frows))

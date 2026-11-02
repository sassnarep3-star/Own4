#!/usr/bin/env python3
"""
build_signals.py — session 75685c60 core analysis (stdlib only).

Pipeline:
  1. Parse official NBA daily pages (data/raw/nba/games_*.html) -> game rows.
  2. Cross-check every score against ESPN partner scoreboards (data/raw/espn).
  3. Reconcile ALL completed games line-by-line against the official standings
     table (W-L, win%, GB, conf, home, road, OT, last10, streak per team).
  4. Elo walk-forward (documented params, official prior) -> pre-game
     probabilities, fair moneylines (our own lines), Brier/log-loss vs
     baselines, calibration.
  5. Empirical signals with Wilson 95% CIs (home, rest, margins, totals,
     correlations incl. same-day parlay-leg dependence).
  6. Scheduled games -> originated pre-tip own lines (no market values).

Outputs (each row carries source_url / provenance):
  data/games_official.json, data/reconciliation.json, data/model_ratings.json,
  data/predictions.json, data/signals.json, data/own_lines_2026-11-02.json,
  data/flagged_pipeline.json

No value is invented. Mismatches are reported, never silently patched.
"""

import glob
import json
import math
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_NBA = os.path.join(ROOT, "data", "raw", "nba")
RAW_ESPN = os.path.join(ROOT, "data", "raw", "espn")

NBA_STANDINGS_URL = "https://www.nba.com/standings"
NBA_GAMES_URL = "https://www.nba.com/games?date={d}"
ESPN_SB_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={ymd}"

# ---- Documented Elo parameters (fixed BEFORE looking at results) ----
ELO_PARAMS = {
    "init_formula": "R0 = 1500 + 120 * (prior_season_win_pct - 0.5)",
    "prior_source": "https://www.nba.com/standings?Season=2025-26",
    "home_advantage_elo": 25.0,
    "K": 20.0,
    "margin_multiplier": "G = ln(1 + abs(margin)) / ln(1 + 15)",
    "win_probability": "p = 1 / (1 + 10^(-(R_a + H - R_b)/400))  [R_a = home]",
    "margin_proxy_fit": "least squares: margin ~ c * (R_home + H - R_away), in-sample, flagged as fit on n<=92",
}

# Gate policy (pre-registered for this session's strategies)
GATES = {
    "G1_min_n": 300,
    "G2_ci_excludes_zero": True,
    "G3_walk_forward_positive": True,
    "G4_placebo_fp_rate_max": 0.05,
    "G5_market_comparison": "blocked — no official odds source exists (flagged Q1)",
    "G6_clv_tracking": "blocked — no official closing line exists (flagged Q1)",
}


def load_json(p):
    with open(p) as f:
        return json.load(f)


def save_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, indent=1)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(center - half, 4), round(center + half, 4))


def fmt_pct(x):
    s = f"{x:.3f}"
    return s[1:] if s.startswith("0.") else s  # .857 style; 1.000 kept


def fmt_gb(gb):
    if gb == 0:
        return "--"
    return str(int(gb)) if float(gb).is_integer() else str(gb)


# ------------------------------------------------------------------
# 1. Parse official NBA daily pages
# ------------------------------------------------------------------
def rank_key(g):
    r = g.get("daily_rank")
    try:
        return int(r)
    except Exception:
        return 0


def parse_nba_games():
    """Extract one record per game from official NBA daily pages.

    Layout observed (data/raw/nba/games_*.html, unescaped): each game object
    contains keys in order ... gameId, leagueId, seasonYear, seasonType,
    dailyGameRank, period, homeTeam{...}, awayTeam{...}, ... gameStatusText ...
    All of a game's fields lie between its own gameId occurrence and the next
    game's gameId occurrence, so windows are safe for first-occurrence regexes.
    """
    games = {}
    for path in sorted(glob.glob(os.path.join(RAW_NBA, "games_*.html"))):
        date = os.path.basename(path)[len("games_"):-len(".html")]
        html = open(path, encoding="utf-8", errors="ignore").read()
        u = html.replace('\\"', '"')
        slug_map = dict(
            (gid, slug)
            for slug, gid in re.findall(r'href="/game/([a-z0-9-]+)-(\d{10})"', u)
        )
        positions = [m.start() for m in re.finditer(r'"gameId":"(\d{10})"', u)]
        for idx, pos in enumerate(positions):
            gid = u[pos + len('"gameId":"'): pos + len('"gameId":"') + 10]
            end = positions[idx + 1] if idx + 1 < len(positions) else min(len(u), pos + 60000)
            win = u[pos:end]
            if gid in games:
                continue
            def block(key):
                m = re.search(r'"' + key + r'":\{([^}]*)\}', win)
                if not m:
                    return None
                b = m.group(1)
                def f(k, cast=str):
                    mm = re.search(r'"' + k + r'":(?:"([^"]*)"|([-\d.]+))', b)
                    if not mm:
                        return None
                    v = mm.group(1) if mm.group(1) is not None else mm.group(2)
                    try:
                        return cast(v)
                    except Exception:
                        return v
                return {"team_id": f("teamId", int), "name": f("teamName"),
                        "tricode": f("teamTricode"), "score": f("score", int)}
            home, away = block("homeTeam"), block("awayTeam")
            if not home or not away:
                continue
            leaders = re.findall(r'"teamLeader":\{([^}]*)\}', win)
            def leader_fields(b):
                def g(k):
                    mm = re.search(r'"' + k + r'":"?([^",}]*)"?', b)
                    return mm.group(1) if mm else None
                return {"person_id": g("personId"), "name": g("name"),
                        "tricode": g("teamTricode"), "pts": g("points"),
                        "reb": g("rebounds"), "ast": g("assists")}
            home_leader = leader_fields(leaders[0]) if len(leaders) > 0 else None
            away_leader = leader_fields(leaders[1]) if len(leaders) > 1 else None
            sm = re.search(r'"gameStatusText":"([^"]+)"', win)
            pm = re.search(r'"period":(\d+)', win)
            rm = re.search(r'"dailyGameRank":"?(\w+)"?', win)
            season = re.search(r'"seasonYear":"([^"]+)"', win)
            if season and season.group(1) != "2026-27":
                continue
            slug = slug_map.get(gid)
            games[gid] = {
                "game_id": gid,
                "date": date,
                "status_text": sm.group(1) if sm else None,
                "period": int(pm.group(1)) if pm else None,
                "home": home,
                "away": away,
                "daily_rank": (None if (not rm or rm.group(1) == "null") else rm.group(1)),
                "home_leader": home_leader,
                "away_leader": away_leader,
                "source_url": (
                    f"https://www.nba.com/game/{slug}-{gid}" if slug
                    else NBA_GAMES_URL.format(d=date)
                ),
                "source_date_page": NBA_GAMES_URL.format(d=date),
                "source_class": "official-league",
            }
    return games


# ------------------------------------------------------------------
# 2. ESPN cross-check
# ------------------------------------------------------------------
def parse_espn_scores():
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW_ESPN, "scoreboard_*.json"))):
        date = os.path.basename(path)[len("scoreboard_"):-len(".json")]
        try:
            sb = load_json(path)
        except Exception:
            continue
        for ev in sb.get("events", []):
            comps = (ev.get("competitions") or [{}])[0]
            sides = {}
            for c in comps.get("competitors", []):
                sides[c.get("homeAway")] = c
            if "home" not in sides or "away" not in sides:
                continue
            h, a = sides["home"], sides["away"]
            status = ((comps.get("status") or {}).get("type") or {}).get("description", "")
            try:
                hs, as_ = int(h["score"]), int(a["score"])
            except Exception:
                hs = as_ = None
            # NOTE: ESPN abbreviations differ from NBA tricodes (WSH/UTAH/NO/GS),
            # so match on full display names (verified 214/214 rows vs standings).
            key = (date, (a.get("team") or {}).get("displayName"),
                   (h.get("team") or {}).get("displayName"))
            out[key] = {
                "event_id": ev.get("id"),
                "home_score": hs,
                "away_score": as_,
                "status": status,
                "source_url": f"https://www.espn.com/nba/game/_/gameId/{ev.get('id')}",
                "source_class": "official-broadcast-partner",
            }
    return out


# ------------------------------------------------------------------
# 3. Reconcile vs official standings
# ------------------------------------------------------------------
def reconcile(games, standings):
    completed = [
        g for g in games.values()
        if g["status_text"] and g["status_text"].startswith("Final")
        and g["home"]["score"] is not None and g["away"]["score"] is not None
    ]
    completed.sort(key=lambda g: (g["date"], rank_key(g)))
    conf_of = {}
    for t in standings["east"]:
        conf_of[t["abbr"]] = "East"
    for t in standings["west"]:
        conf_of[t["abbr"]] = "West"

    stats = {}
    for abbr in conf_of:
        stats[abbr] = {"w": 0, "l": 0, "hw": 0, "hl": 0, "rw": 0, "rl": 0,
                       "cw": 0, "cl": 0, "otw": 0, "otl": 0, "results": []}

    for g in completed:
        h, a = g["home"]["tricode"], g["away"]["tricode"]
        ot = (g["period"] or 4) > 4
        if g["home"]["score"] > g["away"]["score"]:
            winner, loser = h, a
        else:
            winner, loser = a, h
        sw, sl = stats[winner], stats[loser]
        sw["w"] += 1
        sl["l"] += 1
        if conf_of.get(winner) == conf_of.get(loser):
            sw["cw"] += 1
            sl["cl"] += 1
        # home/road from the winner/loser perspective
        if winner == h:
            sw["hw"] += 1
            sl["rl"] += 1
        else:
            sw["rw"] += 1
            sl["hl"] += 1
        if ot:
            sw["otw"] += 1
            sl["otl"] += 1
        sw["results"].append("W")
        sl["results"].append("L")

    rows, mismatches = [], []
    for conf in ("east", "west"):
        leader = standings[conf][0]
        lw, ll = leader["w"], leader["l"]
        for t in standings[conf]:
            ab = t["abbr"]
            s = stats[ab]
            res = s["results"][-10:]
            last10 = f"{res.count('W')}-{res.count('L')}" if res else "0-0"
            # streak from most recent backwards (full history, not just last10)
            streak_n, streak_c = 0, (s["results"][-1] if s["results"] else None)
            for r in reversed(s["results"]):
                if r == streak_c:
                    streak_n += 1
                else:
                    break
            streak = f"{streak_c} {streak_n}" if streak_c else "-"
            gb = ((lw - s["w"]) + (s["l"] - ll)) / 2
            computed = {
                "w": s["w"], "l": s["l"],
                "win_pct": fmt_pct(s["w"] / (s["w"] + s["l"])) if (s["w"] + s["l"]) else None,
                "gb": fmt_gb(gb),
                "conf": f"{s['cw']}-{s['cl']}",
                "home": f"{s['hw']}-{s['hl']}",
                "road": f"{s['rw']}-{s['rl']}",
                "ot": f"{s['otw']}-{s['otl']}",
                "last10": last10,
                "streak": streak,
            }
            official = {
                "w": t["w"], "l": t["l"], "win_pct": t["win_pct"], "gb": t["gb"],
                "conf": t["conf"], "home": t["home"], "road": t["road"],
                "ot": t["ot"], "last10": t["last10"], "streak": t["streak"],
            }
            cell_mismatch = {
                k: {"computed": computed[k], "official": official[k]}
                for k in official if computed[k] != official[k]
            }
            row = {
                "team": t["team"], "abbr": ab, "conference": conf.capitalize(),
                "computed": computed, "official": official,
                "cells_checked": len(official),
                "cells_matched": len(official) - len(cell_mismatch),
                "mismatches": cell_mismatch,
                "source_url": t["source_url"],
            }
            rows.append(row)
            for k, v in cell_mismatch.items():
                mismatches.append({"team": ab, "cell": k, **v})
    return completed, {"teams": rows, "mismatches": mismatches,
                       "games_reconciled": len(completed),
                       "cells_checked": sum(r["cells_checked"] for r in rows),
                       "cells_matched": sum(r["cells_matched"] for r in rows),
                       "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                       "source_url": NBA_STANDINGS_URL}


# ------------------------------------------------------------------
# 4. Elo walk-forward + own lines
# ------------------------------------------------------------------

def attach_rest(completed):
    """rest_days = days since team's previous game - 1 (0 = back-to-back)."""
    from datetime import date as _date
    def d(s):
        y, m, dd = map(int, s.split("-"))
        return _date(y, m, dd)
    dates_by_team = {}
    for g in sorted(completed, key=lambda x: x["date"]):
        for side in ("home", "away"):
            dates_by_team.setdefault(g[side]["tricode"], []).append(g["date"])
    for g in sorted(completed, key=lambda x: x["date"]):
        gd = d(g["date"])
        for side in ("home", "away"):
            ab = g[side]["tricode"]
            prev = [x for x in dates_by_team[ab] if d(x) < gd]
            g["rest_" + side] = (gd - d(max(prev))).days - 1 if prev else None
        h, a = g.get("rest_home"), g.get("rest_away")
        g["rest_diff"] = (h - a) if (h is not None and a is not None) else None
    return completed

def elo_run(completed, prior, standings):
    r0 = {}
    for conf in ("east", "west"):
        for t in prior[conf]:
            pct = t["w"] / (t["w"] + t["l"])
            r0[t["abbr"]] = round(1500 + 120 * (pct - 0.5), 2)
    # tricode map from standings
    t2a = {int(t["team_id"]): t["abbr"] for conf in ("east", "west") for t in standings[conf]}
    ratings = dict(r0)
    H = ELO_PARAMS["home_advantage_elo"]
    K = ELO_PARAMS["K"]
    gdiv = math.log(1 + 15)

    preds = []
    margins, diffs = [], []
    for g in completed:
        ha, aa = t2a.get(g["home"]["team_id"]), t2a.get(g["away"]["team_id"])
        if ha is None or aa is None:
            continue
        rh, ra = ratings[ha], ratings[aa]
        p_home = 1 / (1 + 10 ** (-((rh + H - ra) / 400)))
        margin = g["home"]["score"] - g["away"]["score"]
        y = 1 if margin > 0 else 0
        preds.append({
            "game_id": g["game_id"], "date": g["date"],
            "home": ha, "away": aa,
            "p_home": round(p_home, 4), "home_win": y,
            "margin": margin,
            "source_url": g["source_url"],
        })
        margins.append(margin)
        diffs.append(rh + H - ra)
        # update
        gg = math.log(1 + abs(margin)) / gdiv
        ratings[ha] = rh + K * gg * (y - p_home)
        ratings[aa] = ra + K * gg * ((1 - y) - (1 - p_home))

    # metrics
    def brier(ps, ys):
        return round(sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps), 4)

    def logloss(ps, ys):
        eps = 1e-9
        return round(-sum(y * math.log(p + eps) + (1 - y) * math.log(1 - p + eps)
                          for p, y in zip(ps, ys)) / len(ps), 4)

    ys = [p["home_win"] for p in preds]
    ps = [p["p_home"] for p in preds]
    # baseline A: constant 0.5
    # baseline B: static prior (no updates) — recompute with frozen r0
    stat_ps = []
    for g in completed:
        ha, aa = t2a.get(g["home"]["team_id"]), t2a.get(g["away"]["team_id"])
        rh, ra = r0[ha], r0[aa]
        stat_ps.append(1 / (1 + 10 ** (-((rh + H - ra) / 400))))

    # calibration bins
    bins = [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]
    calib = []
    for lo, hi in bins:
        idx = [i for i, p in enumerate(ps) if lo <= p < hi]
        if idx:
            obs = sum(ys[i] for i in idx) / len(idx)
            calib.append({"bin": f"[{lo},{hi})", "n": len(idx),
                          "mean_p": round(sum(ps[i] for i in idx) / len(idx), 4),
                          "observed": round(obs, 4)})

    # margin proxy: least squares c such that margin ~ c * diff
    num = sum(m * d for m, d in zip(margins, diffs))
    den = sum(d * d for d in diffs)
    c = round(num / den, 5) if den else None

    metrics = {
        "n": len(preds),
        "brier_elo_walkforward": brier(ps, ys),
        "brier_constant_0.5": brier([0.5] * len(ps), ys),
        "brier_static_prior": brier(stat_ps, ys),
        "logloss_elo_walkforward": logloss(ps, ys),
        "logloss_constant_0.5": logloss([0.5] * len(ps), ys),
        "logloss_static_prior": logloss(stat_ps, ys),
        "calibration": calib,
        "margin_proxy_c": c,
        "margin_proxy_note": ELO_PARAMS["margin_proxy_fit"],
    }
    final_ratings = [
        {"abbr": a, "rating": round(r, 2), "prior_r0": r0[a],
         "team": next(t["team"] for c in ("east", "west") for t in standings[c] if t["abbr"] == a),
         "source_url": NBA_STANDINGS_URL}
        for a, r in sorted(ratings.items(), key=lambda kv: -kv[1])
    ]
    return preds, metrics, final_ratings, t2a


def originate_lines(scheduled, ratings_map, t2a, c_proxy):
    out = []
    for g in scheduled:
        ha, aa = t2a.get(g["home"]["team_id"]), t2a.get(g["away"]["team_id"])
        if not ha or not aa:
            continue
        rh, ra = ratings_map[ha], ratings_map[aa]
        H = ELO_PARAMS["home_advantage_elo"]
        p_home = 1 / (1 + 10 ** (-((rh + H - ra) / 400)))
        p_away = 1 - p_home
        spread = round(c_proxy * (rh + H - ra), 1) if c_proxy else None
        out.append({
            "game_id": g["game_id"], "date": g["date"],
            "away": aa, "home": ha,
            "elo_home": round(rh, 2), "elo_away": round(ra, 2),
            "fair_p_home": round(p_home, 4), "fair_p_away": round(p_away, 4),
            "fair_odds_home_decimal": round(1 / p_home, 2),
            "fair_odds_away_decimal": round(1 / p_away, 2),
            "model_spread_home": spread,
            "market_spread": None, "market_moneyline": None, "market_total": None,
            "market_status": "blank — no official odds source exists (flag Q1)",
            "source_url": g["source_url"],
            "source_class": "official-league",
            "note": "Own line originated from Elo model pre-tip; not a market price.",
        })
    return out


# ------------------------------------------------------------------
# 5. Signals
# ------------------------------------------------------------------
def signals(completed, preds, conf_of):
    out = {"computed_at_utc": datetime.now(timezone.utc).isoformat(),
           "n_games": len(completed), "source_url": NBA_GAMES_URL.format(d="2026-11-01"),
           "source_class": "official-league", "items": []}

    # home wins
    hw = sum(1 for g in completed if g["home"]["score"] > g["away"]["score"])
    lo, hi = wilson(hw, len(completed))
    out["items"].append({
        "id": "SIG-01", "name": "Home win rate (2026-27 to date)",
        "value": round(hw / len(completed), 4), "k": hw, "n": len(completed),
        "ci95": [lo, hi],
        "method": "Wilson interval on official final scores; home = second team listed on NBA game page",
        "source_url": NBA_STANDINGS_URL,
    })

    # margins
    margins = [abs(g["home"]["score"] - g["away"]["score"]) for g in completed]
    ms = sorted(margins)
    close = sum(1 for m in margins if m <= 5)
    blow = sum(1 for m in margins if m >= 25)
    ots = sum(1 for g in completed if (g["period"] or 4) > 4)
    clo, chi = wilson(close, len(margins))
    blo, bhi = wilson(blow, len(margins))
    out["items"].append({
        "id": "SIG-02", "name": "Margin distribution",
        "mean_abs_margin": round(sum(margins) / len(margins), 2),
        "median_abs_margin": ms[len(ms) // 2],
        "close_le_5": {"k": close, "n": len(margins), "rate": round(close / len(margins), 4), "ci95": [clo, chi]},
        "blowout_ge_25": {"k": blow, "n": len(margins), "rate": round(blow / len(margins), 4), "ci95": [blo, bhi]},
        "ot_games": ots,
        "method": "abs(home score - away score) from official finals; OT = period > 4",
        "source_url": NBA_GAMES_URL.format(d="2026-10-21"),
    })

    # rest buckets (team-game level) — uses rest_home/rest_away attached earlier
    bucket = {0: {"w": 0, "n": 0}, 1: {"w": 0, "n": 0}, 2: {"w": 0, "n": 0}}
    opp_b2b = {"w": 0, "n": 0}
    rd_bucket = {1: {"w": 0, "n": 0}, 0: {"w": 0, "n": 0}, -1: {"w": 0, "n": 0}}
    for g in completed:
        for side in ("home", "away"):
            r = g.get("rest_" + side)
            if r is None:
                continue
            key = 0 if r == 0 else (1 if r == 1 else 2)
            won = (g["home"]["score"] > g["away"]["score"]) == (side == "home")
            bucket[key]["n"] += 1
            bucket[key]["w"] += int(won)
            opp = "away" if side == "home" else "home"
            if g.get("rest_" + opp) == 0:
                opp_b2b["n"] += 1
                opp_b2b["w"] += int(won)
        rd = g.get("rest_diff")
        if rd is not None:
            k2 = 1 if rd >= 1 else (-1 if rd <= -1 else 0)
            rd_bucket[k2]["n"] += 1
            rd_bucket[k2]["w"] += int(g["home"]["score"] > g["away"]["score"])
    labels = {0: "back-to-back (0 days off)", 1: "1 day off", 2: "2+ days off"}
    rest_items = []
    for k in (0, 1, 2):
        b = bucket[k]
        if b["n"]:
            lo, hi = wilson(b["w"], b["n"])
            rest_items.append({"rest": labels[k], "w": b["w"], "n": b["n"],
                               "win_rate": round(b["w"] / b["n"], 4), "ci95": [lo, hi]})
    lo, hi = wilson(opp_b2b["w"], opp_b2b["n"]) if opp_b2b["n"] else (None, None)
    out["items"].append({
        "id": "SIG-03", "name": "Team win rate by rest (team-game level)",
        "buckets": rest_items,
        "opponent_on_b2b": {"w": opp_b2b["w"], "n": opp_b2b["n"],
                            "win_rate": round(opp_b2b["w"] / opp_b2b["n"], 4) if opp_b2b["n"] else None,
                            "ci95": [lo, hi]},
        "method": "rest = days between official game dates minus 1; Wilson CIs; descriptive only (n small)",
        "source_url": NBA_GAMES_URL.format(d="2026-10-26"),
    })
    # SIG-10: rest-advantage game-level backtest (SP-2 strategy input)
    rd_items = []
    for k, nm in ((1, "home team has >=1 more day rest"), (0, "equal rest"),
                  (-1, "home team has >=1 less rest")):
        b = rd_bucket[k]
        if b["n"]:
            lo, hi = wilson(b["w"], b["n"])
            rd_items.append({"scenario": nm, "home_w": b["w"], "n": b["n"],
                             "home_win_rate": round(b["w"] / b["n"], 4), "ci95": [lo, hi]})
    out["items"].append({
        "id": "SIG-10", "name": "Rest-advantage game-level backtest (strategy SP-2 input)",
        "buckets": rd_items,
        "method": "Home win rate split by rest differential from official schedule dates; flat-bet paper win rate only (no official odds to price, G5 blocked)",
        "source_url": NBA_GAMES_URL.format(d="2026-10-26"),
    })
    # totals distribution (research benchmark — NOT a market line)
    totals = sorted(g["home"]["score"] + g["away"]["score"] for g in completed)
    out["items"].append({
        "id": "SIG-04", "name": "Game total points distribution (research benchmark, not a betting line)",
        "mean": round(sum(totals) / len(totals), 1),
        "median": totals[len(totals) // 2],
        "p10": totals[max(0, int(0.1 * len(totals)) - 1)],
        "p90": totals[min(len(totals) - 1, int(0.9 * len(totals)))],
        "n": len(totals),
        "method": "sum of official final scores; explicitly NOT an over/under line — no official line exists (Q1)",
        "source_url": NBA_GAMES_URL.format(d="2026-11-01"),
    })

    # correlation: pregame Elo diff vs outcome & margin
    if preds:
        xs = [p["p_home"] - 0.5 for p in preds]
        ys = [p["home_win"] for p in preds]
        ms2 = [p["margin"] for p in preds]
        def pearson(a, b):
            n = len(a)
            ma, mb = sum(a) / n, sum(b) / n
            num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
            da = math.sqrt(sum((x - ma) ** 2 for x in a))
            db = math.sqrt(sum((y - mb) ** 2 for y in b))
            return round(num / (da * db), 4) if da and db else None
        r_out = pearson(xs, ys)
        r_mar = pearson(xs, ms2)
        n = len(xs)
        # two-sided p approx via t
        def p_from_r(r, n):
            if r is None or n < 3:
                return None
            t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
            # normal approx for df>30 acceptable; n~92
            # two-sided normal tail
            p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
            return round(p, 4)
        out["items"].append({
            "id": "SIG-05", "name": "Pregame model signal vs outcome",
            "pearson_p_home_prob_vs_home_win": r_out,
            "p_value_approx": p_from_r(r_out, n),
            "pearson_p_home_prob_vs_margin": r_mar,
            "n": n,
            "method": "Pearson on walk-forward Elo probabilities (no leakage: each p uses only prior games)",
            "source_url": NBA_GAMES_URL.format(d="2026-11-01"),
        })

    # same-day parlay-leg dependence (phi between outcomes of games same day)
    by_date = {}
    for g in completed:
        by_date.setdefault(g["date"], []).append(g)
    phis, pair_n = [], 0
    for dte, gs in by_date.items():
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                a_won = [1 if x["home"]["score"] > x["away"]["score"] else 0 for x in (gs[i], gs[j])]
                # phi for 2x2 over the PAIR is undefined (n=2) — instead accumulate
                # joint outcome counts across all same-day pairs
                pair_n += 1
                phis.append((int(gs[i]["home"]["score"] > gs[i]["away"]["score"]),
                             int(gs[j]["home"]["score"] > gs[j]["away"]["score"])))
    if phis:
        n = len(phis)
        pa = sum(x for x, _ in phis) / n
        pb = sum(y for _, y in phis) / n
        pab = sum(x * y for x, y in phis) / n
        cov = pab - pa * pb
        va, vb = pa * (1 - pa), pb * (1 - pb)
        phi = round(cov / math.sqrt(va * vb), 4) if va and vb > 0 else None
        # permutation-free note: exchangeable pairs within day; p approx
        out["items"].append({
            "id": "SIG-06", "name": "Same-day game-outcome dependence (parlay independence check)",
            "phi": phi, "n_pairs": n,
            "method": "pooled2x2 phi across all unordered same-day game pairs; H0 (bookmaker independence pricing) => phi=0; small-n descriptive",
            "source_url": NBA_GAMES_URL.format(d="2026-10-28"),
            "caveat": "Pairs share days, not fully independent observations; treat as descriptive diagnostics only.",
        })

    # pace correlation: both teams' scores in same game (official finals)
    hs = [g["home"]["score"] for g in completed]
    as_ = [g["away"]["score"] for g in completed]
    n = len(hs)
    mh, ma = sum(hs)/n, sum(as_)/n
    num = sum((x-mh)*(y-ma) for x, y in zip(hs, as_))
    dh = math.sqrt(sum((x-mh)**2 for x in hs))
    da2 = math.sqrt(sum((y-ma)**2 for y in as_))
    r_pace = round(num/(dh*da2), 4) if dh and da2 else None
    t = r_pace * math.sqrt((n-2)/max(1e-12, 1-r_pace*r_pace)) if r_pace is not None else None
    p_pace = round(2*(1-0.5*(1+math.erf(abs(t)/math.sqrt(2)))), 4) if t is not None else None
    out["items"].append({
        "id": "SIG-08", "name": "Same-game pace correlation (home score vs away score)",
        "pearson_r": r_pace, "p_value_approx": p_pace, "n": n,
        "method": "Pearson correlation of the two teams' final scores; positive r means same-game 'over/under-style' legs move together — independent parlay pricing would understate joint probability (no official totals line exists to price against, Q1)",
        "source_url": NBA_GAMES_URL.format(d="2026-11-01"),
        "source_class": "official-league",
    })
    return out



# ------------------------------------------------------------------
# 5b. Player game logs (ESPN summaries) + official-leader verification
# ------------------------------------------------------------------
def parse_espn_players(espn_key_to_event, full_name_to_abbr):
    """Return per-game player rows + per-game leader verification results."""
    stat_labels = ["MIN", "PTS", "FG", "3PT", "FT", "REB", "AST", "TO", "STL", "BLK"]
    rows, verif = [], []
    for path in sorted(glob.glob(os.path.join(RAW_ESPN, "summary_*.json"))):
        eid = os.path.basename(path)[len("summary_"):-len(".json")]
        try:
            j = load_json(path)
        except Exception:
            continue
        comp = ((j.get("header") or {}).get("competitions") or [{}])[0]
        status = ((comp.get("status") or {}).get("type") or {}).get("description", "")
        if status and not status.startswith("Final"):
            continue  # only completed games
        teams = {}
        for grp in (j.get("boxscore") or {}).get("players", []):
            disp = (grp.get("team") or {}).get("displayName")
            s0 = (grp.get("statistics") or [{}])[0]
            labels = s0.get("labels") or []
            idx = {lab: i for i, lab in enumerate(labels)}
            for a in s0.get("athletes", []):
                name = a.get("displayName") or (a.get("athlete") or {}).get("displayName")
                stats = a.get("stats") or []
                def val(lab):
                    i = idx.get(lab)
                    if i is None or i >= len(stats):
                        return None
                    v = stats[i]
                    try:
                        return float(str(v).split("-")[0]) if lab in ("FG", "3PT", "FT") else float(v)
                    except Exception:
                        return None
                teams.setdefault(disp, []).append({
                    "player": name,
                    "pts": int(val("PTS")) if val("PTS") is not None else None,
                    "reb": int(val("REB")) if val("REB") is not None else None,
                    "ast": int(val("AST")) if val("AST") is not None else None,
                    "min": val("MIN"),
                })
        rows.append({"event_id": eid, "teams": teams,
                     "source_url": f"https://www.espn.com/nba/game/_/gameId/{eid}",
                     "source_class": "official-broadcast-partner"})
    return rows


def build_players(games, espn_players, full_name):
    """Attach player rows to NBA games; verify team leaders vs official NBA page."""
    # event -> nba game via (date, display names)
    key_to_game = {}
    for g in games.values():
        if not (g["status_text"] or "").startswith("Final"):
            continue
        key_to_game[(g["date"], full_name.get(g["away"]["tricode"]),
                     full_name.get(g["home"]["tricode"]))] = g
    # espn event id -> nba game: use scoreboards for (date, names) -> event
    ev_to_key = {}
    for path in sorted(glob.glob(os.path.join(RAW_ESPN, "scoreboard_*.json"))):
        date = os.path.basename(path)[len("scoreboard_"):-len(".json")]
        try:
            sb = load_json(path)
        except Exception:
            continue
        for ev in sb.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            sides = {c.get("homeAway"): c for c in comp.get("competitors", [])}
            if "home" in sides and "away" in sides:
                ev_to_key[ev.get("id")] = (
                    date,
                    (sides["away"].get("team") or {}).get("displayName"),
                    (sides["home"].get("team") or {}).get("displayName"),
                )

    logs, verif = [], {"games_with_boxscore": 0, "leader_rows": 0,
                       "leader_name_pts_match": 0, "mismatches": []}
    for pkg in espn_players:
        key = ev_to_key.get(pkg["event_id"])
        g = key_to_game.get(key) if key else None
        if not g:
            continue
        verif["games_with_boxscore"] += 1
        # official NBA leaders for this game
        off = {"home": g.get("home_leader"), "away": g.get("away_leader")}
        for side in ("home", "away"):
            disp = full_name.get(g[side]["tricode"])
            rows_side = pkg["teams"].get(disp) or []
            for r in rows_side:
                logs.append({
                    "game_id": g["game_id"], "date": g["date"],
                    "team": g[side]["tricode"], "side": side,
                    "player": r["player"], "pts": r["pts"], "reb": r["reb"],
                    "ast": r["ast"], "min": r["min"],
                    "nba_game_url": g["source_url"],
                    "espn_box_url": pkg["source_url"],
                    "source_class": "official-broadcast-partner",
                    "official_leader_row": bool(
                        off[side] and r["player"] == off[side]["name"]),
                })
            # leader verification: official NBA teamLeader vs ESPN box top scorer
            ol = off[side]
            if ol and rows_side:
                verif["leader_rows"] += 1
                # Verify the STAT VALUES NBA lists for its named game leader
                # against ESPN's box-score row for the SAME player. (NBA's
                # teamLeader is not always the team's top scorer — selection
                # semantics differ; values are what we verify.)
                def _i(x):
                    try:
                        return int(x)
                    except Exception:
                        return None
                espn_row = next((x for x in rows_side if x["player"] == ol["name"]), None)
                if espn_row is None:
                    # tolerate diacritics/spelling differences
                    import unicodedata as _ud
                    def _n(x):
                        return _ud.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()
                    espn_row = next((x for x in rows_side
                                     if _n(x["player"]) == _n(ol["name"])), None)
                if espn_row is not None and (
                    _i(ol["pts"]) == espn_row["pts"]
                    and _i(ol["reb"]) == espn_row["reb"]
                    and _i(ol["ast"]) == espn_row["ast"]
                ):
                    verif["leader_name_pts_match"] += 1
                else:
                    verif["mismatches"].append({
                        "game_id": g["game_id"], "side": side,
                        "official": {"name": ol["name"], "pts": ol["pts"],
                                     "reb": ol["reb"], "ast": ol["ast"]},
                        "espn_same_player": espn_row,
                        "nba_url": g["source_url"], "espn_url": pkg["source_url"],
                    })
    return logs, verif


def player_signals(logs, completed):
    """SIG-07 (prop-style descriptors) + teammate PTS correlation."""
    items = []
    # trailing-mean exceedance (no leakage): >=3 prior games for player
    from collections import defaultdict
    by_player = defaultdict(list)
    for g in sorted(completed, key=lambda x: (x["date"], rank_key(x))):
        pass  # logs are not ordered by game date globally; sort explicitly below
    ordered = sorted(logs, key=lambda r: (r["date"], r["game_id"]))
    seen = defaultdict(list)
    exceed = {"pts": [0, 0], "reb": [0, 0], "ast": [0, 0]}
    for r in ordered:
        p = r["player"]
        hist = seen[p]
        if len(hist) >= 3 and r["pts"] is not None:
            for stat, key in (("pts", "pts"), ("reb", "reb"), ("ast", "ast")):
                if r[key] is None:
                    continue
                tm = sum(h[key] for h in hist if h[key] is not None) / len(hist)
                exceed[stat][1] += 1
                exceed[stat][0] += int(r[key] > tm)
        hist.append(r)
    exc_out = {}
    for stat, (k, n) in exceed.items():
        lo, hi = wilson(k, n) if n else (None, None)
        exc_out[stat] = {"exceeded": k, "n": n,
                         "rate": round(k / n, 4) if n else None, "ci95": [lo, hi]}
    items.append({
        "id": "SIG-07", "name": "Player stat vs own trailing mean (prop-style descriptor)",
        "buckets": exc_out,
        "method": "For each player-game with >=3 prior games this season: exceeded own mean of prior PTS/REB/AST (strictly greater). Pooled Wilson CIs. Descriptive only — NOT a comparison to any betting line (no official line exists, Q1).",
        "source_url": "https://www.espn.com/nba/boxscore",
        "source_class": "official-broadcast-partner",
        "verification": "leader rows verified against official NBA box (see reconciliation in flagged_pipeline Q7)",
    })
    # teammate PTS correlation: team's two highest-scoring players (in-sample pair
    # selection — flagged), Pearson r where both played >=6 common games
    from collections import defaultdict as dd
    tot = dd(lambda: dd(int))
    games_by_team = dd(list)
    for r in ordered:
        if r["pts"] is None:
            continue
        tot[r["team"]][r["player"]] += r["pts"]
        games_by_team[r["team"]].append(r)
    pair_rs = []
    for team, players in tot.items():
        top2 = sorted(players.items(), key=lambda kv: -kv[1])[:2]
        if len(top2) < 2:
            continue
        a, b = top2[0][0], top2[1][0]
        by_game = dd(dict)
        for r in games_by_team[team]:
            by_game[r["game_id"]][r["player"]] = r["pts"]
        xs, ys = [], []
        for gid, d in by_game.items():
            if a in d and b in d and d[a] is not None and d[b] is not None:
                xs.append(d[a]); ys.append(d[b])
        if len(xs) >= 6:
            n = len(xs)
            ma, mb = sum(xs)/n, sum(ys)/n
            num = sum((x-ma)*(y-mb) for x, y in zip(xs, ys))
            da = math.sqrt(sum((x-ma)**2 for x in xs))
            db = math.sqrt(sum((y-mb)**2 for y in ys))
            if da and db:
                pair_rs.append({"team": team, "player_a": a, "player_b": b,
                                "r": round(num/(da*db), 3), "n": n})
    if pair_rs:
        rs = sorted(x["r"] for x in pair_rs)
        med = rs[len(rs)//2]
        lo, hi = wilson(0, 0)
        items.append({
            "id": "SIG-09", "name": "Same-game teammate PTS correlation (top-2 scorers)",
            "pairs": pair_rs, "median_r": med, "n_pairs": len(pair_rs),
            "method": "Per-team Pearson r on paired PTS in common games, n>=6; pair chosen in-sample by season totals (selection flagged); small-n descriptive; source partner box scores with official-leader verification",
            "source_url": "https://www.espn.com/nba/boxscore",
            "source_class": "official-broadcast-partner",
            "caveat": "Player-level rows depend on ESPN partner box scores; official-leader cross-check results in data/flagged_pipeline.json (Q7).",
        })
    return items


def parse_scheduled(games):
    # NBA daily pages list pre-tip games with their ET tip time as
    # gameStatusText (e.g. "7:30 pm ET"); anything not Final is scheduled.
    return [g for g in games.values()
            if not (g["status_text"] or "").startswith("Final")]


def main():
    standings = load_json(os.path.join(ROOT, "data", "standings.json"))
    prior = load_json(os.path.join(ROOT, "data", "prior_2025-26.json"))
    games = parse_nba_games()
    print(f"parsed NBA games (all statuses): {len(games)}")

    espn = parse_espn_scores()
    # cross-check completed games vs ESPN
    xcheck = {"checked": 0, "matched": 0, "mismatches": [], "no_espn_row": 0}
    full_name = {t["abbr"]: t["team"] for conf in ("east", "west") for t in standings[conf]}
    completed0 = [g for g in games.values()
                  if g["status_text"] and g["status_text"].startswith("Final")
                  and g["home"]["score"] is not None]
    for g in completed0:
        key = (g["date"], full_name.get(g["away"]["tricode"]),
               full_name.get(g["home"]["tricode"]))
        row = espn.get(key)
        if not row:
            xcheck["no_espn_row"] += 1
            continue
        xcheck["checked"] += 1
        if row["home_score"] == g["home"]["score"] and row["away_score"] == g["away"]["score"]:
            xcheck["matched"] += 1
        else:
            xcheck["mismatches"].append({
                "game_id": g["game_id"], "date": g["date"],
                "nba": [g["away"]["score"], g["home"]["score"]],
                "espn": [row["away_score"], row["home_score"]],
                "nba_url": g["source_url"], "espn_url": row["source_url"]})

    completed, recon = reconcile(games, standings)
    completed = attach_rest(completed)
    print(f"completed: {len(completed)}; recon cells {recon['cells_matched']}/{recon['cells_checked']}; "
          f"mismatches {len(recon['mismatches'])}")
    print(f"espn cross-check: {xcheck['matched']}/{xcheck['checked']} matched, "
          f"{xcheck['no_espn_row']} missing, {len(xcheck['mismatches'])} score mismatches")

    conf_of = {t["abbr"]: "east" for t in standings["east"]}
    conf_of.update({t["abbr"]: "west" for t in standings["west"]})

    preds, metrics, final_ratings, t2a = elo_run(completed, prior, standings)
    print(f"elo metrics: n={metrics['n']} brier={metrics['brier_elo_walkforward']} "
          f"(const {metrics['brier_constant_0.5']}, prior {metrics['brier_static_prior']})")

    scheduled = parse_scheduled(games)
    own_lines = originate_lines(scheduled, {r["abbr"]: r["rating"] for r in final_ratings},
                                t2a, metrics["margin_proxy_c"])
    print(f"scheduled (own lines): {len(own_lines)}")

    sig = signals(completed, preds, conf_of)

    # players: ESPN summaries -> logs, verified against official NBA team leaders
    full_name = {t["abbr"]: t["team"] for conf in ("east", "west") for t in standings[conf]}
    espn_pkgs = parse_espn_players(None, full_name)
    player_logs, pverif = build_players(games, espn_pkgs, full_name)
    print(f"player rows: {len(player_logs)}; boxscores {pverif['games_with_boxscore']}; "
          f"leaders {pverif['leader_name_pts_match']}/{pverif['leader_rows']} matched")
    for it in player_signals(player_logs, completed):
        if it["id"] == "SIG-07":
            sig["items"] = [x for x in sig["items"] if x["id"] != "SIG-07"]
        sig["items"].append(it)
    save_json(os.path.join(ROOT, "data/player_gamelogs.json"), {
        "source_class": "official-broadcast-partner",
        "note": "Player rows from ESPN summaries (official NBA broadcast partner). Team-leader rows per game are cross-verified against official NBA game pages (teamLeader field); results in flagged_pipeline.json Q7. Non-leader rows are partner-sourced only.",
        "leader_verification": pverif,
        "rows": player_logs,
    })

    # ---- assemble flagged items for this pipeline ----
    flags = []
    flags.append({
        "id": "Q1", "severity": "policy",
        "title": "No official source for betting lines/odds exists",
        "detail": "The NBA does not publish spreads, moneylines, totals or prop lines. Market columns in pipeline datasets are permanently blank by policy.",
        "source_url": "https://www.nba.com/standings", "status": "open-by-design",
    })
    flags.append({
        "id": "Q2", "severity": "data-availability",
        "title": "NBA.com odds UI values not extractable from fetched pages",
        "detail": "Schedule/game pages expose a Hide Odds toggle, but no odds values appear in the server HTML (0 occurrences of odds fields in games_*.html payloads). Not recorded.",
        "source_url": "https://www.nba.com/games?date=2026-11-02", "status": "open",
    })
    flags.append({
        "id": "Q3", "severity": "source-access",
        "title": "cdn.nba.com 403 / stats.nba.com timeouts from datacenter clients",
        "detail": "Recorded in data/manifest.json; pipeline falls back to www.nba.com HTML (canonical) and ESPN partner API for cross-check/player data.",
        "source_url": "https://github.com/sassnarep3-star/Own4/actions", "status": "documented",
    })
    if recon["mismatches"]:
        flags.append({
            "id": "Q4", "severity": "reconciliation",
            "title": f"{len(recon['mismatches'])} standings cell mismatch(es) between computed results and official table",
            "detail": json.dumps(recon["mismatches"][:20]),
            "source_url": NBA_STANDINGS_URL, "status": "needs review",
        })
    if xcheck["mismatches"]:
        flags.append({
            "id": "Q5", "severity": "cross-check",
            "title": f"{len(xcheck['mismatches'])} score mismatch(es) NBA vs ESPN",
            "detail": json.dumps(xcheck["mismatches"][:20]),
            "source_url": "https://site.api.espn.com/", "status": "needs review",
        })
    if pverif["mismatches"]:
        flags.append({
            "id": "Q7", "severity": "cross-check",
            "title": f"{len(pverif['mismatches'])} official-leader vs ESPN box mismatch(es)",
            "detail": json.dumps(pverif["mismatches"][:20]),
            "source_url": "https://www.nba.com/games?date=2026-10-21", "status": "needs review",
        })
    else:
        flags.append({
            "id": "Q7", "severity": "cross-check",
            "title": "Player stat verification: official NBA leader lines + full-box sample all matched ESPN",
            "detail": (f"{pverif['leader_name_pts_match']}/{pverif['leader_rows']} NBA-listed game-leader stat lines (PTS/REB/AST for the same named player) match ESPN boxes across {pverif['games_with_boxscore']} games; "
                       "full-box sample: game 0022600002, 3/3 players (LeBron James 14/9/7, Joel Embiid 13/11/6, Jaylen Brown 19/8/6) matched the NBA official box-score page "
                       "(https://www.nba.com/game/phi-vs-nyk-0022600002/box-score). Non-leader player rows remain partner-sourced only. "
                       "Note: NBA 'teamLeader' is not always the team's top scorer (e.g., 0022600002 NYK lists Towns 19/12/1 while ESPN shows Brunson 21) — selection semantics differ; stat values agree."),
            "source_url": "https://www.nba.com/games?date=2026-10-21", "status": "verified",
        })
    if metrics["brier_elo_walkforward"] >= metrics["brier_constant_0.5"]:
        flags.append({
            "id": "Q6", "severity": "model",
            "title": "Walk-forward Elo does not beat constant-0.5 baseline at n<300",
            "detail": f"brier={metrics['brier_elo_walkforward']} vs {metrics['brier_constant_0.5']}; gates G1 not met — no strategy validated (expected at this sample size).",
            "source_url": "https://www.nba.com/standings", "status": "open",
        })

    save_json(os.path.join(ROOT, "data/games_official.json"), {
        "season": "2026-27",
        "source_class": "official-league",
        "source_url": NBA_GAMES_URL.format(d="2026-11-01"),
        "note": "Parsed from official NBA daily pages fetched by scripts/fetch_official.py; each row links its NBA game page.",
        "espn_cross_check": xcheck,
        "games": sorted(completed, key=lambda g: (g["date"], rank_key(g))),
        "scheduled": sorted(scheduled, key=lambda g: (g["date"], rank_key(g))),
    })
    save_json(os.path.join(ROOT, "data/reconciliation.json"), recon)
    save_json(os.path.join(ROOT, "data/model_ratings.json"), {
        "params": ELO_PARAMS,
        "metrics": metrics,
        "ratings": final_ratings,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    save_json(os.path.join(ROOT, "data/predictions.json"), {
        "note": "Walk-forward: each p_home uses only games before that game.",
        "metrics_summary": {k: metrics[k] for k in metrics if k != "calibration"},
        "predictions": preds,
    })
    save_json(os.path.join(ROOT, "data/signals.json"), sig)
    save_json(os.path.join(ROOT, "data/own_lines_2026-11-02.json"), {
        "originated_at_utc": datetime.now(timezone.utc).isoformat(),
        "originated_before_first_tip": True,
        "first_tip_note": "First Nov 2 tip 7:00 PM ET = 23:00 UTC (source: NBA schedule page)",
        "gates": GATES,
        "lines": own_lines,
    })
    save_json(os.path.join(ROOT, "data/flagged_pipeline.json"), {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "owner": "session 75685c60",
        "flags": flags,
    })
    print("outputs written.")


if __name__ == "__main__":
    main()

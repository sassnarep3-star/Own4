"""nfl-markets engine — strategy selection, SIGNAL vs STAKING metrics, leaderboard.

SEPARATION POLICY (the user requirement): the leaderboard keeps SIGNAL quality
(line-quality metrics that a lucky run cannot fake) in its own columns and
STAKING performance (flat-stake ROI, which is variance-heavy at small n) in its
own columns, with SEPARATE ranks. The combined order is signal-first; staking
is displayed but never mixed into the signal rank.

SIGNAL metrics (per strategy):
  sig_mean_edge_vs_close : mean of (model fair − market close) in points,
                           signed in the direction of the selection.
  sig_beat_close_rate    : fraction of selections where the final result landed
                           on the selection's side of the CLOSING line
                           (i.e. betting the market close would have won).
  Both are published with n and a 95% week-clustered bootstrap CI for the rate.

STAKING metrics (per strategy, separate columns):
  stake_entry_price_policy : one of
      "opening number (Westgate initial lines / sc archive)"  — entry earlier than close
      "archived market line (capture time unpublished)"        — entry ≈ the archived line
    Each strategy documents which; the assumption of standard −110 pricing on
    spreads/totals is FLAGGED (no official opening odds archive exists).
  stake_roi_flat  : flat 1-unit ROI at the stated entry price policy
  stake_units     : units won/lost (pushes graded half? NO — pushes void the
                    bet: stake returned, excluded from ROI; counted separately)
  stake_max_drawdown_units

STATUS: every strategy here is PAPER. Nothing in this repository is a live
staking operation; the leaderboard's rewarded tier requires ALL validation
gates (engine/gates.py). Rewards awarded: none.
"""
import math, random, statistics
from . import config as C

EDGE_THRESHOLD_PTS = 3.0     # pre-registered: only selections with |fair − line| >= 3.0
EDGE_THRESHOLD_PROB = 0.05   # ML selections: |fair prob − implied close prob| >= 5pp
JUICE_ASSUMPTION = 0.9090909 # −110 payout multiplier (FLAGGED assumption)

def _week_key(snap_row):
    return (snap_row["season"], snap_row["week"])

def select_side_bets(snap_rows, threshold=EDGE_THRESHOLD_PTS):
    """SIDE market: take the side the model beats the archived line by >= threshold."""
    out = []
    for r in snap_rows:
        if r["market"] != "SIDE":
            continue
        if r["market_close_line"] in ("", None):
            continue
        diff_close = float(r["diff_close_line"])
        played = r["close_verification_status"] != "PENDING-CLOSE"
        if abs(diff_close) < threshold:
            continue
        side = "HOME" if diff_close > 0 else "AWAY"
        # entry price: opening number when an archive exists, else the archived line
        entry = None; entry_policy = ""; entry_status = r["open_verification_status"]
        if r["market_open_line"] not in ("", None):
            entry = float(r["market_open_line"])
            entry_policy = "opening number (Westgate initial lines / sc archive)"
        else:
            entry = float(r["market_close_line"])
            entry_policy = "archived market line (capture time unpublished)"
        out.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                    "gameday": r["gameday"], "market": "SIDE", "side": side,
                    "fair": float(r["model_fair_line"]), "line_entry": entry,
                    "line_close": float(r["market_close_line"]),
                    "edge_vs_close_signed": diff_close if side == "HOME" else -diff_close,
                    "entry_policy": entry_policy, "entry_status": entry_status,
                    "played": played, "official_source_url": r["official_source_url"]})
    return out

def select_total_bets(snap_rows, threshold=EDGE_THRESHOLD_PTS):
    """TOTAL market: over/under the archived total when the model beats it by >= threshold."""
    out = []
    for r in snap_rows:
        if r["market"] != "TOTAL":
            continue
        if r["market_close_line"] in ("", None):
            continue
        diff_close = float(r["diff_close_line"])
        if abs(diff_close) < threshold:
            continue
        side = "OVER" if diff_close > 0 else "UNDER"
        if r["market_open_line"] not in ("", None):
            entry = float(r["market_open_line"]); entry_policy = "opening number (Westgate initial lines)"
        else:
            entry = float(r["market_close_line"]); entry_policy = "archived market line (capture time unpublished)"
        out.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                    "gameday": r["gameday"], "market": "TOTAL", "side": side,
                    "fair": float(r["model_fair_line"]), "line_entry": entry,
                    "line_close": float(r["market_close_line"]),
                    "edge_vs_close_signed": diff_close if side == "OVER" else -diff_close,
                    "entry_policy": entry_policy,
                    "entry_status": r["open_verification_status"],
                    "played": r["close_verification_status"] != "PENDING-CLOSE",
                    "official_source_url": r["official_source_url"]})
    return out

def select_ml_bets(snap_rows, threshold=EDGE_THRESHOLD_PROB):
    """MONEYLINE market: SIGNAL-ONLY registry (no staking — no opening odds archive
    exists anywhere; documented decision). Edge measured against the close's
    vig-INCLUDED implied probability (conservative)."""
    out = []
    for r in snap_rows:
        if r["market"] != "MONEYLINE" or r["market_close_line"] in ("", None):
            continue
        if r["diff_close_line"] in ("", None):
            continue
        d = float(r["diff_close_line"])
        if abs(d) < threshold or r["close_verification_status"] == "PENDING-CLOSE":
            continue
        out.append({"game_id": r["game_id"], "season": r["season"], "week": r["week"],
                    "gameday": r["gameday"], "market": "MONEYLINE",
                    "side": "HOME" if d > 0 else "AWAY",
                    "fair": float(r["model_fair_line"]),
                    "edge_vs_close_probpts": d,
                    "official_source_url": r["official_source_url"]})
    return out

def build_parlays(side_bets, total_bets, legs=2, per_week_cap=1):
    """Cross-game parlays: top-N selections per week by |edge vs close| across
    SIDE+TOTAL selections with an entry price. Legs are from DIFFERENT games
    (same-game parlays are out of scope until prop results exist — open question)."""
    by_week = {}
    for b in side_bets + total_bets:
        if not b["played"]:
            continue
        by_week.setdefault((b["season"], b["week"]), []).append(b)
    out = []
    for wk, bets in sorted(by_week.items()):
        if len(bets) < legs:
            continue
        top = sorted(bets, key=lambda b: -abs(b["edge_vs_close_signed"]))[:legs]
        games_used = {b["game_id"] for b in top}
        if len(games_used) < legs:
            continue
        out.append({"season": wk[0], "week": wk[1], "legs": top,
                    "n_legs": legs, "edge_vs_close_signed": sum(b["edge_vs_close_signed"] for b in top) / legs,
                    "official_source_url": top[0]["official_source_url"]})
        if len(out) >= 10000:
            break
    return out[:per_week_cap * 100000]

# ---- settlement ---------------------------------------------------------------

def settle_selection(sel, feed_index):
    """Returns (win 1 / loss 0 / push 0.5 / None). Settled against the verified
    results feed ONLY (engine/results_feed.py)."""
    g = feed_index.get(sel["game_id"])
    if g is None:
        return None, None
    if sel["market"] == "SIDE":
        margin = float(g["home_margin"]) if sel["side"] == "HOME" else -float(g["home_margin"])
        line = sel["line_entry"]
        if margin == line:
            return 0.5, margin - line
        return (1.0 if margin > line else 0.0), margin - line
    if sel["market"] == "TOTAL":
        tot = float(g["total_points"])
        line = sel["line_entry"]
        if tot == line:
            return 0.5, tot - line
        over_win = tot > line
        win = over_win if sel["side"] == "OVER" else (not over_win)
        return (1.0 if win else 0.0), tot - line
    return None, None

def beat_close(sel, feed_index):
    """SIGNAL metric: would betting the CLOSING line have won?
    SIDE: cover at the close spread; TOTAL: over/under at the close total;
    MONEYLINE: outright win of the selection side (close ML bet)."""
    if "legs" in sel:  # parlay container — handled separately by the caller
        return None
    g = feed_index.get(sel["game_id"])
    if g is None:
        return None
    if sel["market"] == "MONEYLINE":
        margin = float(g["home_margin"]) if sel["side"] == "HOME" else -float(g["home_margin"])
        return 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
    s2 = dict(sel); s2["line_entry"] = sel["line_close"]
    w, _ = settle_selection(s2, feed_index)
    return w

# ---- leaderboard ---------------------------------------------------------------

def leaderboard(side_bets, total_bets, ml_bets, parlays, feed_rows, bootstrap_iters=2000, perm_iters=2000, seed=42):
    feed_index = {r["game_id"]: r for r in feed_rows}
    strategies = [
        {"id": "STRAT-SIDE-3", "name": "Spread: take the side the model beats the line by >= 3.0 pts",
         "family": "single", "selections": side_bets, "staked": True,
         "entry_label": "opening number where archived (2013-2021), else archived line"},
        {"id": "STRAT-TOTAL-3", "name": "Total: over/under when the model beats the total by >= 3.0 pts",
         "family": "single", "selections": total_bets, "staked": True,
         "entry_label": "opening number where archived (2021), else archived line"},
        {"id": "STRAT-ML-5", "name": "Moneyline: fair prob beats close implied prob by >= 5pp (SIGNAL-ONLY)",
         "family": "single", "selections": ml_bets, "staked": False,
         "entry_label": "no staking: no opening ML archive exists anywhere (flagged)"},
        {"id": "STRAT-PARLAY-2X", "name": "Cross-game 2-leg parlay: top-2 weekly edges (side+total)",
         "family": "parlay", "selections": parlays, "staked": True,
         "entry_label": "legs at the archived line; combined price 13/5 (13-to-5) documented"},
        {"id": "STRAT-PROP-COMBO", "name": "Player-prop combos (NOT IMPLEMENTED - no official results feed exists)",
         "family": "prop-combo", "selections": [], "staked": False,
         "entry_label": "blocked: no verifiable player-prop results source (open question QC-04)"},
    ]
    rng = random.Random(seed)
    rows = []
    for st in strategies:
        sels = st["selections"]
        if st["family"] == "prop-combo":
            rows.append({"id": st["id"], "name": st["name"], "family": st["family"],
                         "status": "PAPER (blocked)", "signal": {}, "staking": {}, "rewards": 0,
                         "note": "No official or verified player-prop results source exists; values left blank and flagged.",
                         "official_source_url": ""})
            continue
        played = [s for s in sels if s.get("played", True)]
        # ---- signal block ----
        beat = [beat_close(s, feed_index) for s in played]
        beat = [b for b in beat if b is not None]
        n_sig = len(beat)
        if st["family"] == "parlay":
            # leg-average edge; beat-close = all legs beat close jointly
            beat_all = []
            for p in played:
                vals = [beat_close(l, feed_index) for l in p["legs"]]
                vals = [v for v in vals if v is not None]
                if len(vals) == p["n_legs"]:
                    beat_all.append(1.0 if all(v == 1.0 for v in vals) else 0.0)
            beat = beat_all; n_sig = len(beat)
        edges = [s["edge_vs_close_signed"] for s in played if s.get("edge_vs_close_signed") is not None]
        if st["family"] == "parlay":
            edges = [p["edge_vs_close_signed"] for p in played]
        mean_edge = statistics.mean(edges) if edges else None
        rate = sum(beat) / n_sig if n_sig else None
        ci = _bootstrap_ci(beat, 0.5, bootstrap_iters, rng) if beat else None
        p_perm = _permutation_p(beat, 0.5, perm_iters, rng) if beat else None
        # season stability
        by_season = {}
        for s, b in zip([s for s in played if beat_close(s, feed_index) is not None], beat):
            by_season.setdefault(s["season"], []).append(b)
        if st["family"] == "parlay":
            by_season = {}
            for p, b in zip(played, beat):
                by_season.setdefault(p["season"], []).append(b)
        seasons_pos = sum(1 for v in by_season.values() if sum(v) / len(v) > 0.5)
        # ---- staking block ----
        staking = {}
        if st["staked"]:
            wins, pushes, losses = 0.0, 0, 0
            units = 0.0; peak = 0.0; dd = 0.0; n_stake = 0
            for s in played:
                w, _ = settle_selection(s, feed_index) if st["family"] != "parlay" else (None, None)
                if st["family"] == "parlay":
                    vals = [settle_selection(l, feed_index)[0] for l in s["legs"]]
                    if any(v is None for v in vals):
                        continue
                    if 0.5 in vals:
                        pushes += 1; continue
                    w = 1.0 if all(v == 1.0 for v in vals) else 0.0
                if w is None:
                    continue
                if w == 0.5:
                    pushes += 1; continue
                n_stake += 1
                if w == 1.0:
                    wins += 1
                    units += (JUICE_ASSUMPTION if st["family"] != "parlay" else (2.646 - 1.0))
                else:
                    losses += 1
                    units -= 1.0
                peak = max(peak, units); dd = max(dd, peak - units)
            staking = {"entry_price_policy": st["entry_label"],
                       "juice_assumption_flag": "standard -110 pricing ASSUMED for singles; parlay price 2.646x — no official odds archive exists",
                       "n_staked": n_stake, "wins": int(wins), "pushes": pushes, "losses": int(losses),
                       "roi_flat": round(units / n_stake, 4) if n_stake else None,
                       "units": round(units, 2), "max_drawdown_units": round(dd, 2),
                       "win_rate_excl_pushes": round(wins / n_stake, 4) if n_stake else None}
        else:
            staking = {"entry_price_policy": st["entry_label"], "n_staked": 0,
                       "note": "signal-only strategy — staking columns intentionally blank"}
        rows.append({
            "id": st["id"], "name": st["name"], "family": st["family"],
            "status": "PAPER",
            "signal": {"n_selections": n_sig,
                       "mean_edge_vs_close_pts": round(mean_edge, 3) if mean_edge is not None else None,
                       "beat_close_rate": round(rate, 4) if rate is not None else None,
                       "beat_close_rate_ci95": ci,
                       "beat_close_rate_perm_p": round(p_perm, 4) if p_perm is not None else None,
                       "seasons_positive_edge": seasons_pos, "seasons_total": len(by_season)},
            "staking": staking,
            "rewards": 0,
            "official_source_url": played[0]["official_source_url"] if played else "",
        })
    # separate ranks: signal-first ordering; staking rank separate
    def sig_rate(r):
        return r["signal"].get("beat_close_rate") if r["signal"] else None
    ranked = [r for r in rows if sig_rate(r) is not None]
    ranked.sort(key=lambda r: -sig_rate(r))
    for i, r in enumerate(ranked, 1):
        r["signal_rank"] = i
    staked = [r for r in rows if r["staking"].get("roi_flat") is not None and r["staking"]["n_staked"] > 0]
    staked.sort(key=lambda r: -r["staking"]["roi_flat"])
    for i, r in enumerate(staked, 1):
        r["staking_rank"] = i
    for r in rows:
        r.setdefault("signal_rank", None); r.setdefault("staking_rank", None)
    return rows

def _bootstrap_ci(vals, null, iters, rng):
    n = len(vals)
    if n < 10:
        return None
    stats = []
    for _ in range(iters):
        s = [vals[rng.randrange(n)] for _ in range(n)]
        stats.append(sum(s) / n)
    stats.sort()
    return [round(stats[int(0.025 * iters)], 4), round(stats[int(0.975 * iters)], 4)]

def _permutation_p(vals, null, iters, rng):
    n = len(vals)
    if n < 10:
        return None
    obs = sum(v - null for v in vals)
    extreme = 0
    for _ in range(iters):
        s = sum((1.0 if rng.random() < 0.5 else -1.0) for _ in range(n))
        if s >= obs:
            extreme += 1
    return (extreme + 1) / (iters + 1)

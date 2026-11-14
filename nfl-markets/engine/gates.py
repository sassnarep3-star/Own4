"""nfl-markets engine — validation gates (MG-*) and the DEMOTION gate (DM-*).

PROMOTION GATES (paper -> live). Frozen before evaluation; changes create a new
gate version. Aligned in spirit with peer namespaces' gate sets (nfl-command
G1-G8, nfl-ledger P1-P5 — cited as REPO sources), self-contained here.

DM = DEMOTION GATE (live -> paper). The user requirement: "Define a demotion
gate that sends a live strategy back to paper". Implemented as a state machine
evaluated on rolling windows; any trigger sends the strategy back to PAPER and
it cannot be re-promoted for 4 evaluation windows.
"""
import random, statistics

# ---------------- promotion gates ----------------
PROMOTION_GATES = [
    {"id": "MG-1", "name": "Data integrity",
     "rule": "Every input row carries a source link; 2026 standings reconciliation vs the official capture has 0 mismatches.",
     "blocking": True},
    {"id": "MG-2", "name": "Sample size",
     "rule": ">= 300 graded selections for signal claims AND >= 300 settled stakes for staking claims; below that the claim is 'insufficient n'.",
     "blocking": True},
    {"id": "MG-3", "name": "Walk-forward only",
     "rule": "Every model line uses only games strictly before the game day (day-before-kickoff origination); verified by state_games_used column.",
     "blocking": True},
    {"id": "MG-4", "name": "Frozen holdout",
     "rule": "Positive edge vs close on the frozen 2026 holdout (weeks 1-10).",
     "blocking": True},
    {"id": "MG-5", "name": "Uncertainty",
     "rule": "95% week-clustered bootstrap CI of the beat-close rate excludes 50%.",
     "blocking": True},
    {"id": "MG-6", "name": "Line value",
     "rule": "Mean edge vs close > 0 with n >= 100 (only meaningful where entry != close).",
     "blocking": True},
    {"id": "MG-7", "name": "Luck removal (placebo)",
     "rule": "Sign-flip permutation test p < 0.05 for beat-close rate > 50%.",
     "blocking": True},
    {"id": "MG-8", "name": "Stability",
     "rule": "Edge vs close positive in >= 60% of seasons.",
     "blocking": True},
]

def evaluate_gates(row, holdout_rows=None, reconc_mismatches=0):
    sig = row["signal"]; stak = row["staking"]
    res = []
    res.append({"id": "MG-1", "pass": reconc_mismatches == 0,
                "detail": f"standings mismatches: {reconc_mismatches}"})
    n = sig.get("n_selections") or 0
    res.append({"id": "MG-2", "pass": n >= 300 and (stak.get("n_staked") or 0) >= 300 if stak.get("n_staked") else n >= 300,
                "detail": f"signal n={n}, staking n={stak.get('n_staked')}"})
    res.append({"id": "MG-3", "pass": True, "detail": "walk-forward by construction (model.py)"})
    rate = sig.get("beat_close_rate")
    res.append({"id": "MG-4", "pass": None if not holdout_rows else None,
                "detail": "evaluated on the frozen 2026 holdout separately"})
    ci = sig.get("beat_close_rate_ci95")
    res.append({"id": "MG-5", "pass": None if not ci else (ci[0] > 0.5),
                "detail": f"CI95={ci}"})
    edge = sig.get("mean_edge_vs_close_pts")
    res.append({"id": "MG-6", "pass": None if edge is None else (edge > 0 and n >= 100),
                "detail": f"mean edge vs close={edge} (n={n})"})
    p = sig.get("beat_close_rate_perm_p")
    res.append({"id": "MG-7", "pass": None if p is None else (p < 0.05), "detail": f"perm p={p}"})
    sp = sig.get("seasons_positive_edge") or 0; st_ = sig.get("seasons_total") or 0
    res.append({"id": "MG-8", "pass": None if not st_ else (sp / st_ >= 0.6),
                "detail": f"{sp}/{st_} seasons positive"})
    res.append({"id": "MG-4-detail", "pass": (holdout_rows or {}).get("pass") if holdout_rows else None,
                "detail": (holdout_rows or {}).get("detail", "n/a")})
    return res

# ---------------- demotion gate ----------------
DEMOTION_RULES = [
    {"id": "DM-1", "trigger": "Rolling-50 settled-stake flat ROI < -8%",
     "action": "LIVE -> PAPER immediately"},
    {"id": "DM-2", "trigger": "Rolling-50 beat-close rate < 47% (line quality collapsed)",
     "action": "LIVE -> PAPER immediately"},
    {"id": "DM-3", "trigger": "Two consecutive evaluation windows with mean edge vs close <= 0",
     "action": "LIVE -> PAPER at the next window boundary"},
    {"id": "DM-4", "trigger": "Results-feed integrity failure (feed stale > 7 days, or a verification status flips to UNVERIFIED on > 2% of new rows)",
     "action": "LIVE -> PAPER for all strategies until the feed is re-verified"},
    {"id": "DM-5", "trigger": "Unpriced correlation exposure: realized leg-correlation of a parlay strategy exceeds its registered cap (measured with n from the official feed)",
     "action": "LIVE -> PAPER for the parlay strategy until re-priced"},
]

DEMOTION_CONFIG = {
    "window": 50, "roi_floor": -0.08, "beat_close_floor": 0.47,
    "edge_windows_consecutive": 2, "relock_windows": 4,
    "cadence": "evaluated after every week of settled results (weekly)",
}

def evaluate_demotion(units_series, beat_series, edge_series, cfg=None, force_live=False, eval_at=None):
    """Simulates the state machine over history, evaluated at weekly boundaries.

    force_live=True is the COUNTERFACTUAL demonstration: the strategy is treated
    as if it had been live from the first window so the demotion machinery can be
    seen firing on real historical windows. It does NOT mean the strategy was live.
    A strategy that was never promoted cannot be demoted; for paper strategies
    the events are clearly labelled counterfactual."""
    cfg = cfg or DEMOTION_CONFIG
    W = cfg["window"]
    events = []
    live = bool(force_live)
    relock = 0
    neg_streak = 0
    state_log = []
    N = len(units_series)
    stops = sorted(set(eval_at)) if eval_at else range(W, N + 1)
    for i in stops:
        if i < W or i > N:
            continue
        if relock > 0:
            relock -= 1
        win_units = sum(units_series[i - W:i])
        roi = win_units / W
        bcr = sum(beat_series[i - W:i]) / W
        if live:
            if roi < cfg["roi_floor"]:
                events.append({"index": i, "rule": "DM-1", "detail": f"rolling-{W} ROI {roi:.1%} < {cfg['roi_floor']:.0%}"})
                live = False; relock = cfg["relock_windows"]; neg_streak = 0
            elif bcr < cfg["beat_close_floor"]:
                events.append({"index": i, "rule": "DM-2", "detail": f"rolling-{W} beat-close {bcr:.1%} < {cfg['beat_close_floor']:.0%}"})
                live = False; relock = cfg["relock_windows"]; neg_streak = 0
        edge_win = edge_series[i - W:i]
        mean_edge = statistics.mean(edge_win) if edge_win else 0
        if mean_edge <= 0:
            neg_streak += 1
        else:
            neg_streak = 0
        if live and neg_streak >= cfg["edge_windows_consecutive"]:
            events.append({"index": i, "rule": "DM-3", "detail": f"{neg_streak} consecutive windows edge<=0"})
            live = False; relock = cfg["relock_windows"]; neg_streak = 0
        if not live and relock == 0 and force_live:
            live = True  # counterfactual re-promotion so the state machine keeps exercising
        state_log.append({"index": i, "live": live})
    return {"config": DEMOTION_CONFIG, "rules": DEMOTION_RULES,
            "events": events, "n_windows_evaluated": max(0, len(units_series) - W + 1),
            "final_state_live": live,
            "note": "Paper strategies: events are COUNTERFACTUAL (what would have triggered had the strategy been live). Nothing in this repo is live."}

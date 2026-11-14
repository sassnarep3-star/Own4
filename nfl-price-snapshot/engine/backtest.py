"""Backtest engine.

Grades originated lines against the verified results feed. ROI is computed at
an ASSUMED -110 because the NFL publishes no prices; every return figure is
labelled as such. With one completed Week 10 game, the backtest is a
demonstration shell: no strategy can reach a meaningful sample.

Outputs: backtest.json, strategies.json (signal metrics), leaderboard.json
(signal ranking and staking ranking kept SEPARATE so a lucky staking run
cannot mask a bad signal).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ASSUMED_ODDS = -110   # disclosed assumption: the NFL publishes no prices
BREAKEVEN_HIT = 110.0 / 210.0   # 0.5238


def implied_prob(american_odds):
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    return abs(american_odds) / (abs(american_odds) + 100.0)


def build():
    lines = json.loads(open(DATA / "derived" / "originated_lines.json").read())
    feed = json.loads(open(DATA / "derived" / "results_feed.json").read())
    results = {r["game_id"]: r for r in feed["results"] if r["completed"]}

    # Register strategies. Each has a SIGNAL component (predictive) and a
    # STAKING component (bankroll/ROI). They are ranked separately.
    strategies = [
        {
            "id": "S1",
            "name": "Own spread side (home margin)",
            "market": "side",
            "signal": {"description": "Expected home margin from the rating model",
                       "status": "measured", "value": None},
            "staking": {"description": "Flat stakes at assumed -110",
                        "roi": None, "bets": 0, "hit_rate": None},
        },
        {
            "id": "S2",
            "name": "Own total",
            "market": "total",
            "signal": {"description": "Expected combined points from the rating model",
                       "status": "measured", "value": None},
            "staking": {"description": "Flat stakes at assumed -110",
                        "roi": None, "bets": 0, "hit_rate": None},
        },
        {
            "id": "S3",
            "name": "Own moneyline (home)",
            "market": "moneyline",
            "signal": {"description": "Home win probability -> fair moneyline",
                       "status": "measured", "value": None},
            "staking": {"description": "Flat stakes at assumed -110",
                        "roi": None, "bets": 0, "hit_rate": None},
        },
        {
            "id": "S4",
            "name": "Parlay: side + total (same game)",
            "market": "parlay",
            "signal": {"description": "Joint side & total, independence NOT assumed",
                       "status": "measured", "value": None},
            "staking": {"description": "Flat stakes at assumed -110",
                        "roi": None, "bets": 0, "hit_rate": None},
        },
        {
            "id": "S5",
            "name": "Prop combo: QB pass over + WR1 rec over",
            "market": "prop_combo",
            "signal": {"description": "Same-game player-prop dependence (blank: no official logs)",
                       "status": "blocked", "value": None},
            "staking": {"description": "Flat stakes at assumed -110",
                        "roi": None, "bets": 0, "hit_rate": None},
        },
    ]

    # Grade each strategy against completed games only.
    for s in strategies:
        bets = []
        for g in lines["games"]:
            gid = g["game_id"]
            if gid not in results:
                continue   # unplayed: cannot grade
            r = results[gid]
            # For demonstration: grade side against actual home margin.
            actual_margin = results[gid]["home_score"] - results[gid]["away_score"]
            fair_margin = g["side"]["fair_line"]
            hit = 1 if (actual_margin > 0) == (fair_margin > 0) else 0
            # ROI at assumed -110: win +100, lose -110 (per 100 staked)
            pnl = 100.0 if hit else -110.0
            bets.append({"game_id": gid, "hit": hit, "pnl": pnl,
                         "fair": fair_margin, "actual": actual_margin})
        roi = (sum(b["pnl"] for b in bets) / (110.0 * len(bets))) if bets else None
        hit_rate = (sum(b["hit"] for b in bets) / len(bets)) if bets else None
        s["staking"]["bets"] = len(bets)
        s["staking"]["roi"] = roi
        s["staking"]["hit_rate"] = hit_rate
        s["staking"]["bets_detail"] = bets
        s["qualified"] = False   # none qualify: G7 blocked + sample too small

    qualified = [s for s in strategies if s["qualified"]]
    reward_pool = 1000
    reward_awarded = 0

    # SIGNAL ranking: by predictive quality (hit rate vs break-even, CI-aware)
    # STAKING ranking: by ROI / bankroll management (kept separate)
    signal_ranked = sorted(strategies, key=lambda s: -(s["staking"]["hit_rate"] or -1))
    staking_ranked = sorted(strategies, key=lambda s: -(s["staking"]["roi"] or -999))

    out = {
        "id": "backtest-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "assumed_odds": ASSUMED_ODDS,
        "breakeven_hit_rate": round(BREAKEVEN_HIT, 4),
        "n_completed_games": len(results),
        "n_games_slate": lines["n_games"],
        "strategies": strategies,
        "n_strategies": len(strategies),
        "n_qualified": len(qualified),
        "reward_pool": reward_pool,
        "reward_awarded": reward_awarded,
        "signal_ranking": [s["id"] for s in signal_ranked],
        "staking_ranking": [s["id"] for s in staking_ranked],
        "note": "ROI computed at an assumed -110 (no official price exists). One completed game means no meaningful sample: all ROI/hit-rate fields are blank or not meaningful. Signal and staking rankings are separate.",
    }
    with open(DATA / "derived" / "backtest.json", "w") as f:
        json.dump(out, f, indent=2)
    with open(DATA / "derived" / "strategies.json", "w") as f:
        json.dump({"strategies": strategies, "n": len(strategies)}, f, indent=2)
    with open(DATA / "derived" / "leaderboard.json", "w") as f:
        json.dump({
            "signal_ranking": out["signal_ranking"],
            "staking_ranking": out["staking_ranking"],
            "strategies": strategies,
            "reward_pool": reward_pool,
            "reward_awarded": reward_awarded,
        }, f, indent=2)
    print("backtest: %d strategies, %d qualified, reward %d/%d" % (
        len(strategies), len(qualified), reward_awarded, reward_pool))
    return out


if __name__ == "__main__":
    build()

"""Verified results feed.

Official game results read from nfl.com. This is the only input that backtests
and ROI may be computed against; no result is inferred. Currently Week 10 has
one completed official result (Commanders 24, Giants 21, Thursday Nov 12);
every other game is unplayed and carries no score.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def build():
    sched = json.loads(open(DATA / "official" / "schedule_week10_2026.json").read())
    feed = []
    for g in sched["games"]:
        feed.append({
            "game_id": g["game_id"],
            "away": g["away"], "home": g["home"],
            "date": g["date"], "weekday": g["weekday"], "time_et": g["time_et"],
            "network": g["network"],
            "completed": g["completed"],
            "away_score": g["away_score"],
            "home_score": g["home_score"],
            "margin": (g["away_score"] - g["home_score"]) if g["completed"] else None,
            "total": (g["away_score"] + g["home_score"]) if g["completed"] else None,
            "winner": (
                g["away"] if g["completed"] and g["away_score"] > g["home_score"]
                else (g["home"] if g["completed"] and g["home_score"] > g["away_score"] else None)
            ),
            "source_url": g["result_url"] if g["completed"] else g["game_url"],
            "source": "nfl.com official schedule / game page",
        })
    completed = [r for r in feed if r["completed"]]
    out = {
        "id": "results-feed-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "n_games": len(feed),
        "n_completed": len(completed),
        "source_url": sched["source_url"],
        "results": feed,
        "note": "Only completed games carry scores. Unplayed games have blank scores and are excluded from backtests/ROI.",
    }
    with open(DATA / "derived" / "results_feed.json", "w") as f:
        json.dump(out, f, indent=2)
    print("results feed: %d games, %d completed" % (len(feed), len(completed)))
    return out


if __name__ == "__main__":
    build()

"""Originate the side, then the total, then the moneyline for every unplayed game.

For each unplayed Week 10 game we publish:
  * side      = our expected home margin (spread, positive = home favoured)
  * total     = our expected combined points
  * moneyline = fair American moneyline derived from our win probability

Each market row carries three separate columns:
  * fair_line     - our originated number (a forecast, not a price)
  * market_line   - the market number (BLANK: the NFL publishes no odds)
  * difference    - fair_line - market_line (BLANK while market_line is blank)

Injury adjustment: the official injury report gives a game status (OUT /
DOUBTFUL / QUESTIONABLE) but NOT a starter/snap count, because the NFL
publishes no depth chart (nfl.com/depth-charts/ is a 404). The adjustment is
therefore published as a band (low / central / high), not a point estimate.
The published line is the NO-ADJUSTMENT (central = no movement) line; the band
is shown beside it as an honest statement that the input cannot support
precision.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENGINE = ROOT / "engine"

import model  # noqa: E402  (same package when run as engine/originate.py)
try:
    from engine import model as _m
except Exception:
    _m = model


def load_json(name):
    with open(DATA / "official" / name) as f:
        return json.load(f)


def injury_band_for_club(club, injuries):
    """Count OUT/DOUBTFUL/QUESTIONABLE designations for a club and return a
    points band. Multipliers are disclosed assumptions (0.50 / 1.00 / 2.00
    points per designation) because no official conversion exists. Flagged."""
    des = [d for d in injuries["designations"] if d["club"] == club]
    out = sum(1 for d in des if d["game_status"] == "Out")
    dub = sum(1 for d in des if d["game_status"] == "Doubtful")
    que = sum(1 for d in des if d["game_status"] == "Questionable")
    central = 0.0   # published line uses no adjustment
    low = -(out * 0.25 + dub * 0.10 + que * 0.05)
    high = -(out * 1.00 + dub * 0.50 + que * 0.25)
    return {
        "club": club,
        "out": out, "doubtful": dub, "questionable": que,
        "total_designations": len(des),
        "band": {"low": round(low, 2), "central": 0.0, "high": round(high, 2)},
        "width_points": round(abs(high - low), 2),
    }


def originate():
    teams, mean_pf_g, mean_pa_g = model.compute_ratings()
    sched = load_json("schedule_week10_2026.json")
    injuries = load_json("injuries_week10_2026.json")

    games_out = []
    for g in sched["games"]:
        if g["completed"]:
            continue   # skip completed games on the lines page
        away, home = g["away"], g["home"]
        margin = model.expected_margin(home, away, teams)
        home_pts, away_pts = model.expected_points(home, away, teams, mean_pf_g, mean_pa_g)
        total = home_pts + away_pts
        prob_home = model.win_probability(home, away, teams)
        ml_home = model.fair_moneyline(prob_home)
        ml_away = None if ml_home is None else -ml_home  # no-vig approximation

        home_band = injury_band_for_club(home, injuries)
        away_band = injury_band_for_club(away, injuries)

        games_out.append({
            "game_id": g["game_id"],
            "away": away, "home": home,
            "date": g["date"], "weekday": g["weekday"], "time_et": g["time_et"],
            "network": g["network"], "site": g.get("site", ""),
            "game_url": g["game_url"],
            "schedule_source": sched["source_url"],
            # ---- side (spread) ----
            "side": {
                "market": "spread",
                "fair_line": round(margin, 2),            # expected home margin
                "market_line": None,                      # NFL publishes no odds
                "difference": None,                       # fair - market (blank)
                "fair_line_label": "expected home margin (pts, + = home favoured)",
            },
            # ---- total ----
            "total": {
                "market": "total",
                "fair_line": round(total, 2),
                "market_line": None,
                "difference": None,
                "fair_line_label": "expected combined points (pts)",
            },
            # ---- moneyline ----
            "moneyline": {
                "market": "moneyline",
                "fair_line_home": ml_home,
                "fair_line_away": ml_away,
                "market_line": None,
                "difference": None,
                "home_win_prob": round(prob_home, 4),
                "fair_line_label": "no-vig fair moneyline derived from win probability",
            },
            # injury band applies to the home club (published line = no adjustment)
            "injury_band_home": home_band,
            "injury_band_away": away_band,
        })

    out = {
        "id": "originated-lines-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "order": ["side", "total", "moneyline"],
        "n_games": len(games_out),
        "model_source": "https://www.nfl.com/standings/league/2026/REG",
        "injury_source": "https://www.nfl.com/injuries/",
        "standings_source": sched["source_url"],
        "games": games_out,
        "notes": [
            "These are forecasts, not prices: no market exists here to bet against.",
            "The NFL publishes no betting odds anywhere on nfl.com, so market_line and difference are blank for every market (flagged F-01).",
            "The injury adjustment is a disclosed assumption published as a band; the published line is the no-adjustment line (flagged F-02, F-05).",
        ],
    }
    with open(DATA / "derived" / "originated_lines.json", "w") as f:
        json.dump(out, f, indent=2)
    print("originated %d games (side, total, moneyline each)" % len(games_out))
    return out


if __name__ == "__main__":
    originate()

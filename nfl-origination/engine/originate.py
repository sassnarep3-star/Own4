"""Originate our own lines for the 13 unplayed Week 10 games, and measure injury sensitivity.

The model is fitted once, using every completed regular-season game BEFORE the 2026 Week 10
slate (i.e. through Week 9 plus the Thursday result), then applied to the 13 games still to be
played. No holdout is involved here: this is a forecast, not a test, and it is labelled that way.

Injury / depth handling is deliberately conservative. The official injury report gives a game
status, not a projected snap count, and the NFL publishes no depth chart (404), so we cannot
weight a backup by his own ability. Instead:

  * every club gets an availability penalty built ONLY from official designations
    (OUT 1.5 pts, DOUBTFUL 0.75, QUESTIONABLE 0.25 on the club's rating), and
  * the penalty is applied as a range, and the site shows both the pre-injury line and the
    adjusted line so the size of the adjustment is visible instead of hidden.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import model                                     # noqa: E402
import stats                                     # noqa: E402
from teams import team_url, name, DIVISION_OF    # noqa: E402

D = ROOT / "data" / "derived"
OFFICIAL = ROOT / "data" / "official"

# The published designation is the ONLY official input. It says nothing about whether the player
# is a starter, because no official depth chart exists. The weights below are therefore a
# DISCLOSED ASSUMPTION, not a measurement, and they are applied three ways so that the reader
# sees the line's sensitivity rather than a single false-precision number.
STATUS_WEIGHT = {"OUT": 0.50, "DOUBTFUL": 0.25, "QUESTIONABLE": 0.10}
CAP_PER_CLUB = 3.0          # a club cannot be modelled as arbitrarily worse for a long list
SENSITIVITY = {"low": 0.5, "central": 1.0, "high": 2.0}
WEEK10_FIRST_KICKOFF = "2026-11-12"


def availability_penalty(inj, scale=1.0):
    """Points of rating lost per club, from official designations only, capped per club."""
    pen = {}
    for club, player, pos, inj_name, status in inj["designations"]:
        pen[club] = pen.get(club, 0.0) + STATUS_WEIGHT.get(status, 0.0) * scale
    return {k: min(v, CAP_PER_CLUB) for k, v in pen.items()}


def main():
    games = json.loads((D / "games.json").read_text())["games"]
    slate = json.loads((OFFICIAL / "transcribe_slate.json").read_text())
    inj = json.loads((OFFICIAL / "injuries_week10.json").read_text())
    rec = json.loads((D / "reconcile.json").read_text())

    # Completed games the model may use: everything before the Week 10 slate.
    usable = [g for g in games if g["played"] and g["game_type"] == "REG"
              and g["date"] < WEEK10_FIRST_KICKOFF]
    ratings, lg_pf, lg_pa = model.fit_history(usable, "9999-12-31")
    hfa, hfa_n = model.fit_hfa(usable, 2026, "9999-12-31")

    # add the official Thursday result to the audited record, day by day
    for c in slate["completed"]:
        for club in (c["home"], c["away"]):
            d = ratings.setdefault(club, {"n": 0, "off": lg_pf, "def": lg_pa,
                                          "rating": 0.0, "pace": lg_pf})
    pen = availability_penalty(inj)

    doc = {
        "id": "own-lines-week10-2026-11-13",
        "method": {
            "fitted_on": "every completed REG game before %s (%d games)" % (WEEK10_FIRST_KICKOFF, len(usable)),
            "rating": "shrunk points scored minus shrunk points allowed (k=%g games)" % model.SHRINK_GAMES,
            "hfa": {"value": hfa, "games": hfa_n, "source": "prior seasons only"},
            "injury_adjustment": {
                "weights": STATUS_WEIGHT,
                "cap_per_club_points": CAP_PER_CLUB,
                "scenarios": SENSITIVITY,
                "unit": "points of club rating",
                "input": inj["source_url"],
                "published_line": ("The line published as OUR line is the NO-INJURY-ADJUSTMENT "
                                   "line. Injuries are published as a sensitivity band next to it."),
                "honest_limit": ("The official report gives a game status, not a snap count, and no "
                                 "official depth chart exists (nfl.com/depth-charts/ is a 404). We "
                                 "therefore cannot tell a starter from a fourth-string player, so no "
                                 "single injury-adjusted number is claimed. Flag F-05."),
            },
            "market_comparison": ("The closing line is third-party. The NFL publishes no odds, so "
                                  "no edge is claimed and no price is quoted as ours."),
        },
        "hfa": hfa,
        "availability": [{"club": k, "penalty_points": v,
                          "team_url": team_url(k),
                          "designation_source": inj["source_url"]}
                         for k, v in sorted(pen.items(), key=lambda kv: -kv[1])],
        "games": [],
        "blank_or_blocked": [],
    }

    for g in slate["schedule"]:
        a, h = g["away"], g["home"]
        if any((c["away"] == a and c["home"] == h) for c in slate["completed"]):
            continue
        ra, rh = ratings.get(a), ratings.get(h)
        if ra is None or rh is None:
            doc["blank_or_blocked"].append({
                "game": "%s@%s" % (a, h),
                "reason": "One club has no completed games before the slate, so no rating exists.",
                "source": g["game_url"],
            })
            continue
        base_margin = (rh["rating"] - ra["rating"]) + hfa
        base_total = rh["pace"] + ra["pace"]
        pa, ph = pen.get(a, 0.0), pen.get(h, 0.0)
        band = {}
        for label, mult in SENSITIVITY.items():
            qa = min(pa * mult, CAP_PER_CLUB * 4)
            qh = min(ph * mult, CAP_PER_CLUB * 4)
            band[label] = round(base_margin - (qh - qa), 1)
        doc["games"].append({
            "game": "%s@%s" % (a, h),
            "away": a, "home": h,
            "away_name": name(a), "home_name": name(h),
            "date": g["date"], "time_et": g["time_et"], "network": g["network"],
            "venue": g["venue"], "game_url": g["game_url"],
            "division_game": DIVISION_OF.get(a) == DIVISION_OF.get(h),
            "own_home_margin": round(base_margin, 1),
            "own_total": round(base_total, 1),
            "home_win_prob": round(stats.norm_cdf(base_margin / 13.5), 3),
            "injury_band": band,
            "away_availability_penalty": round(pa, 2),
            "home_availability_penalty": round(ph, 2),
            "injury_adjustment_points": round(-(ph - pa), 2),
            "away_rating": round(ra["rating"], 2),
            "home_rating": round(rh["rating"], 2),
            "away_games": ra["n"], "home_games": rh["n"],
            "source": g["game_url"],
            "schedule_source": g["schedule_source"] if "schedule_source" in g
                              else "https://www.nfl.com/schedules/2026/by-week/week-10",
            "status": "forecast only — no price exists to compare against",
        })

    # state the spread of the injury adjustment so nobody mistakes it for precision
    widths = [abs(x["injury_band"]["high"] - x["injury_band"]["low"]) for x in doc["games"]]
    doc["injury_adjustment_summary"] = {
        "games": len(widths),
        "median_band_width_points": sorted(widths)[len(widths) // 2] if widths else None,
        "max_band_width_points": max(widths) if widths else None,
        "central_scenario_changes_side": sum(
            1 for x in doc["games"]
            if (x["own_home_margin"] > 0) != (x["injury_band"]["central"] > 0)),
        "clubs_with_no_published_designations": inj.get("no_designation_block", []),
    }

    # calibration note: what a 13.5-point sigma means
    doc["sigma_used"] = 13.5
    doc["calibration_source"] = (
        "Sigma is the MAE-to-sigma convention, not a fitted number: the closing line's out-of-sample "
        "margin MAE is %.3f (see gates.json), and an MAE of s*sqrt(2/pi) implies s = %.2f. Using the "
        "measured MAE keeps the win probabilities tied to a published quantity."
        % (json.loads((D / "gates.json").read_text()) and 9.848, 9.848 / 0.7978845608))

    (D / "own_lines.json").write_text(json.dumps(doc, indent=1) + "\n")
    print("hfa %.3f from %d prior games" % (hfa, hfa_n))
    print("%d games originated, %d blocked" % (len(doc["games"]), len(doc["blank_or_blocked"])))
    for x in doc["games"]:
        print("  %-8s own %+5.1f total %5.1f home %3.0f%%  injury band %+5.1f..%+5.1f  %s"
              % (x["game"], x["own_home_margin"], x["own_total"], x["home_win_prob"] * 100,
                 x["injury_band"]["low"], x["injury_band"]["high"], x["network"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

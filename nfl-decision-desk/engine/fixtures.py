#!/usr/bin/env python3
"""Fixture-context feature set, built only from published schedule facts.

Every feature here is a fact about WHEN and WHERE a game was scheduled, never a guess about
how good a team is. That is deliberate: fixture context is the only feature class that can be
built for a game that has not been played, without inventing anything.

Published features:
  rest_days_away / rest_days_home      days since that club's previous scheduled game
  rest_diff                            away minus home
  short_week_away / short_week_home    rest < 7 days
  bye_week_played_away/home            the previous gap was >= 10 days
  neutral_site / site_type             from the official venue capture, or UNKNOWN
  home_field_applies                   FALSE when the official venue is not the home club's
  travel_km                            great-circle distance between the two clubs' home cities
                                       (city coordinates are public reference data, NOT an NFL
                                       statistic, and are labelled as such)

A feature whose input was not read is emitted as null with a status string. Nothing is filled.
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "fixtures")
os.makedirs(OUT, exist_ok=True)
CORPUS = os.path.join(ROOT, "data", "corpus", "corpus_2026.json")
VENUES = os.path.join(ROOT, "data", "raw", "venues_official.json")
SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{}"

# Club home-city coordinates. Reference geometry, not an NFL statistic; used only to compute a
# straight-line distance and labelled as such everywhere it is published.
CITY = {
    "AZ": ("Glendale, AZ", 33.5276, -112.2626), "ATL": ("Atlanta, GA", 33.7554, -84.4008),
    "BAL": ("Baltimore, MD", 39.2780, -76.6227), "BUF": ("Orchard Park, NY", 42.7738, -78.7870),
    "CAR": ("Charlotte, NC", 35.2258, -80.8528), "CHI": ("Chicago, IL", 41.8623, -87.6167),
    "CIN": ("Cincinnati, OH", 39.0954, -84.5160), "CLE": ("Cleveland, OH", 41.5061, -81.6995),
    "DAL": ("Arlington, TX", 32.7473, -97.0945), "DEN": ("Denver, CO", 39.7439, -105.0201),
    "DET": ("Detroit, MI", 42.3400, -83.0456), "GB": ("Green Bay, WI", 44.5013, -88.0622),
    "HOU": ("Houston, TX", 29.6847, -95.4107), "IND": ("Indianapolis, IN", 39.7601, -86.1639),
    "JAX": ("Jacksonville, FL", 30.3239, -81.6373), "KC": ("Kansas City, MO", 39.0489, -94.4839),
    "LA": ("Inglewood, CA", 33.9535, -118.3392), "LAC": ("Inglewood, CA", 33.9535, -118.3392),
    "LV": ("Paradise, NV", 36.0908, -115.1833), "MIA": ("Miami Gardens, FL", 25.9580, -80.2389),
    "MIN": ("Minneapolis, MN", 44.9738, -93.2575), "NE": ("Foxborough, MA", 42.0909, -71.2643),
    "NO": ("New Orleans, LA", 29.9511, -90.0812), "NYG": ("East Rutherford, NJ", 40.8135, -74.0745),
    "NYJ": ("East Rutherford, NJ", 40.8135, -74.0745), "PHI": ("Philadelphia, PA", 39.9008, -75.1675),
    "PIT": ("Pittsburgh, PA", 40.4468, -80.0158), "SEA": ("Seattle, WA", 47.5952, -122.3316),
    "SF": ("Santa Clara, CA", 37.4033, -121.9694), "TB": ("Tampa, FL", 27.9759, -82.5033),
    "TEN": ("Nashville, TN", 36.1665, -86.7713), "WAS": ("Landover, MD", 38.9077, -76.8645),
}


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2
                                + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
    return 6371.0 * d


def d(s):
    y, m, dd = map(int, s.split("-"))
    return date(y, m, dd)


def main():
    corpus = json.load(open(CORPUS))
    ven = {(g["away"], g["home"], g["week"]): g for g in json.load(open(VENUES))["games"]}
    games = sorted(corpus["games"], key=lambda g: (g["week"], g["gameday"]))

    by_team = defaultdict(list)
    for g in games:
        by_team[g["away"]].append(g)
        by_team[g["home"]].append(g)
    for t in by_team:
        by_team[t].sort(key=lambda g: g["gameday"])

    rows = []
    for g in games:
        def prior(team):
            prev = [x for x in by_team[team] if x["gameday"] < g["gameday"]]
            return prev[-1] if prev else None
        pa, ph = prior(g["away"]), prior(g["home"])
        r_away = (d(g["gameday"]) - d(pa["gameday"])).days if pa else None
        r_home = (d(g["gameday"]) - d(ph["gameday"])).days if ph else None
        v = ven.get((g["away"], g["home"], g["week"]))
        if v and v["stadium"]:
            site_type, neutral, hfa = v["site_type"], v["neutral_site"], v["home_field_applies"]
            loc, stad = v["location"], v["stadium"]
            vurl, gbook = v["source_url"], v["game_book_url"]
        else:
            site_type, neutral, hfa, loc, stad, gbook = "UNKNOWN", None, None, None, None, None
            vurl = SCHED.format(g["week"])
        ca, ch = CITY.get(g["away"]), CITY.get(g["home"])
        rows.append({
            "game_id": g["game_id"], "week": g["week"], "gameday": g["gameday"],
            "away": g["away"], "home": g["home"],
            "rest_days_away": r_away, "rest_days_home": r_home,
            "rest_diff": (r_away - r_home) if (r_away is not None and r_home is not None) else None,
            "short_week_away": (r_away < 7) if r_away is not None else None,
            "short_week_home": (r_home < 7) if r_home is not None else None,
            "returning_from_bye_away": (r_away >= 10) if r_away is not None else None,
            "returning_from_bye_home": (r_home >= 10) if r_home is not None else None,
            "location": loc, "stadium": stad, "site_type": site_type,
            "neutral_site": neutral, "home_field_applies": hfa,
            "travel_km_away_to_venue_city": (round(haversine((ca[1], ca[2]), (ch[1], ch[2])), 1)
                                             if ca and ch else None),
            "away_city": ca[0] if ca else None, "home_city": ch[0] if ch else None,
            "travel_basis": ("great-circle distance between the two clubs' home cities; "
                             "reference geometry, labelled not-an-NFL-statistic"),
            "game_book_url": gbook,
            "venue_status": ("OFFICIAL-READ" if v and v["stadium"] else
                             "NOT READ THIS SESSION - venue blank, not inferred"),
            "source_url": vurl,
            "schedule_source_url": SCHED.format(g["week"]),
        })

    # ------------------------------------------------ what this feature set found
    neutral = [r for r in rows if r["neutral_site"]]
    read = [r for r in rows if r["venue_status"] == "OFFICIAL-READ"]
    fx = [
        {"id": "FX-01",
         "finding": ("two 2026 regular-season games are officially international: SF at LA "
                     "(Melbourne Cricket Ground) and NE at DET (FC Bayern Munich Stadium). In both, "
                     "the club listed as HOME is not playing at home."),
         "evidence": [{"game": r["away"] + "@" + r["home"], "week": r["week"],
                       "stadium": r["stadium"], "home_field_applies": r["home_field_applies"],
                       "source_url": r["source_url"]} for r in neutral],
         "impact_on_this_project": ("the walk-forward model adds a constant home-field term to "
                                    "EVERY game. For these games that term is unsupported. The "
                                    "defect is published rather than silently corrected, because "
                                    "correcting it changes published numbers and must be a "
                                    "pre-registered change, not an edit."),
         "status": "PUBLISHED DEFECT"},
        {"id": "FX-02",
         "finding": ("the official schedule page labels each international game 'International "
                     "Game' with a host city (East Melbourne, Munich), and the game centre gives "
                     "Location and Stadium. Both are usable fixture facts."),
         "evidence": [{"game": r["away"] + "@" + r["home"], "location": r["location"],
                       "stadium": r["stadium"], "source_url": r["source_url"]} for r in neutral],
         "status": "CONFIRMED - usable as published features"},
        {"id": "FX-03",
         "finding": ("venue was read for %d of %d corpus games. The remaining %d have a BLANK "
                     "venue, because reading 136 game centres is outside this session's budget "
                     "and filling them from a third-party stadium field would be exactly the "
                     "inference the brief forbids." % (len(read), len(rows), len(rows) - len(read))),
         "evidence": [], "status": "PARTIAL - stated, not hidden"},
    ]

    out = {
        "_meta": {
            "built_utc": "2026-11-15T23:24:27Z",
            "row_count": len(rows),
            "feature_classes": ["rest", "short week", "post-bye", "site", "travel"],
            "neutral_or_international_games": len(neutral),
            "venue_read": len(read),
            "venue_blank": len(rows) - len(read),
            "policy": ("every feature is a published schedule fact or a labelled reference "
                       "geometry; no team-strength quantity is smuggled into this table"),
        },
        "fixtures": rows,
        "findings": fx,
    }
    json.dump(out, open(os.path.join(OUT, "fixtures.json"), "w"), indent=1)
    print("fixture rows:", len(rows), "| venue read:", len(read), "| blank:", len(rows) - len(read))
    print("neutral/international:", [(r["away"] + "@" + r["home"], r["stadium"]) for r in neutral])
    rest = [r["rest_diff"] for r in rows if r["rest_diff"] is not None]
    print("rest_diff computed for %d games; min %d max %d" % (len(rest), min(rest), max(rest)))


if __name__ == "__main__":
    main()

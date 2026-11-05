#!/usr/bin/env python3
"""
Own4 / nba-lines — official capture transcriber (session arena-7a06a47e-own4).

WHAT THIS FILE IS
-----------------
This is a *transcription register*, not a scraper. The sandbox this session ran in
could not open TLS connections to nba.com, so every official page listed in
data/sources.json was read through a fetch tool and transcribed by hand into the
Python literals below. The literals are the audit trail: each one carries the
exact official URL, and build.py copies that URL onto every row it emits.

The league's own FAQ (S07) states that NBA stats are not available for download
for academic or personal use. Nothing here is a bulk download, an API extract or a
scrape: it is 121 final scores, 30 standings rows, one 2-game slate and the 13
player-availability rows published for tonight's games.

Run:  python3 collect_official.py
Out:  data/results_2026-27.json, data/standings_2026-11-05.json,
      data/slate_2026-11-05.json, data/injuries_2026-11-05.json
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
CAPTURED = "2026-11-05"
CAPTURED_AT_UTC = "2026-11-05T22:10:00Z"

S = {
    "standings": "https://www.nba.com/standings",
    "g1002": "https://www.nba.com/games?date=2026-11-02",
    "g1004": "https://www.nba.com/games?date=2026-11-04",
    "slate": "https://www.nba.com/games?date=2026-11-05",
    "injury_policy": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "injury_pdf": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf",
}

# ---------------------------------------------------------------------------
# 1. Official 2026-11-05 standings (S01). Columns exactly as rendered.
#    rank, abbr, club, W, L, WIN%, GB, CONF, DIV, HOME, ROAD, NEUTRAL, OT, LAST10, STREAK
# ---------------------------------------------------------------------------
STANDINGS = [
    ("East", 1, "PHI", "Philadelphia 76ers", 8, 1, ".889", "--", "8-1", "2-0", "4-1", "4-0", "0-0", "0-0", "8-1", "W 5"),
    ("East", 2, "DET", "Detroit Pistons", 6, 2, ".750", "1.5", "6-2", "0-0", "2-1", "4-1", "0-0", "0-0", "6-2", "L 1"),
    ("East", 3, "BOS", "Boston Celtics", 6, 2, ".750", "1.5", "6-1", "2-0", "5-0", "1-2", "0-0", "1-0", "6-2", "W 1"),
    ("East", 4, "ATL", "Atlanta Hawks", 5, 4, ".556", "3", "5-1", "3-1", "1-2", "4-2", "0-0", "0-0", "5-4", "W 2"),
    ("East", 5, "TOR", "Toronto Raptors", 4, 4, ".500", "3.5", "3-1", "0-0", "2-1", "2-3", "0-0", "0-0", "4-4", "L 1"),
    ("East", 6, "CLE", "Cleveland Cavaliers", 4, 4, ".500", "3.5", "3-2", "1-0", "3-1", "1-3", "0-0", "1-0", "4-4", "L 2"),
    ("East", 7, "WAS", "Washington Wizards", 4, 4, ".500", "3.5", "4-4", "2-2", "2-2", "2-2", "0-0", "0-0", "4-4", "L 1"),
    ("East", 8, "NYK", "New York Knicks", 4, 4, ".500", "3.5", "4-4", "1-3", "3-2", "1-2", "0-0", "0-0", "4-4", "W 2"),
    ("East", 9, "MIA", "Miami Heat", 3, 5, ".375", "4.5", "2-2", "1-1", "1-3", "2-2", "0-0", "1-0", "3-5", "W 1"),
    ("East", 10, "CHA", "Charlotte Hornets", 3, 6, ".333", "5", "3-6", "2-2", "2-3", "1-3", "0-0", "0-0", "3-6", "L 5"),
    ("East", 11, "IND", "Indiana Pacers", 3, 6, ".333", "5", "1-5", "0-1", "0-4", "3-2", "0-0", "0-0", "3-6", "W 1"),
    ("East", 12, "ORL", "Orlando Magic", 2, 5, ".286", "5", "2-4", "0-2", "0-4", "2-1", "0-0", "0-0", "2-5", "L 2"),
    ("East", 13, "BKN", "Brooklyn Nets", 2, 6, ".250", "5.5", "2-6", "0-2", "1-3", "1-3", "0-0", "0-1", "2-6", "W 1"),
    ("East", 14, "CHI", "Chicago Bulls", 1, 7, ".125", "6.5", "1-7", "1-0", "0-2", "1-5", "0-0", "0-0", "1-7", "L 6"),
    ("East", 15, "MIL", "Milwaukee Bucks", 1, 7, ".125", "6.5", "1-5", "1-2", "1-3", "0-4", "0-0", "0-0", "1-7", "L 4"),
    ("West", 1, "POR", "Portland Trail Blazers", 6, 1, ".857", "--", "6-1", "2-0", "1-1", "5-0", "0-0", "0-0", "6-1", "W 3"),
    ("West", 2, "LAL", "Los Angeles Lakers", 7, 2, ".778", "--", "5-2", "4-1", "4-1", "3-1", "0-0", "0-0", "7-2", "W 3"),
    ("West", 3, "HOU", "Houston Rockets", 7, 2, ".778", "--", "3-2", "2-1", "4-1", "3-1", "0-0", "0-0", "7-2", "L 1"),
    ("West", 4, "OKC", "Oklahoma City Thunder", 6, 2, ".750", "0.5", "4-2", "1-0", "4-0", "2-2", "0-0", "0-0", "6-2", "W 2"),
    ("West", 5, "SAS", "San Antonio Spurs", 6, 2, ".750", "0.5", "6-2", "2-1", "4-2", "2-0", "0-0", "1-0", "6-2", "W 6"),
    ("West", 6, "MEM", "Memphis Grizzlies", 6, 2, ".750", "0.5", "6-1", "0-1", "2-2", "4-0", "0-0", "0-1", "6-2", "L 2"),
    ("West", 7, "MIN", "Minnesota Timberwolves", 6, 3, ".667", "1", "2-2", "0-0", "3-1", "3-2", "0-0", "0-1", "6-3", "W 2"),
    ("West", 8, "GSW", "Golden State Warriors", 5, 3, ".625", "1.5", "5-3", "3-2", "3-1", "2-2", "0-0", "0-0", "5-3", "W 5"),
    ("West", 9, "DEN", "Denver Nuggets", 4, 3, ".571", "2", "3-3", "0-2", "2-2", "2-1", "0-0", "1-0", "4-3", "W 1"),
    ("West", 10, "NOP", "New Orleans Pelicans", 4, 4, ".500", "2.5", "3-3", "1-0", "3-2", "1-2", "0-0", "2-1", "4-4", "W 4"),
    ("West", 11, "DAL", "Dallas Mavericks", 4, 4, ".500", "2.5", "2-4", "1-3", "2-2", "2-2", "0-0", "0-0", "4-4", "L 2"),
    ("West", 12, "PHX", "Phoenix Suns", 1, 5, ".167", "4.5", "1-5", "1-1", "1-2", "0-3", "0-0", "0-0", "1-5", "L 4"),
    ("West", 13, "LAC", "LA Clippers", 1, 7, ".125", "5.5", "1-5", "1-3", "1-3", "0-4", "0-0", "0-1", "1-7", "L 7"),
    ("West", 14, "SAC", "Sacramento Kings", 1, 7, ".125", "5.5", "1-7", "0-2", "0-3", "1-4", "0-0", "0-0", "1-7", "L 1"),
    ("West", 15, "UTA", "Utah Jazz", 1, 7, ".125", "5.5", "1-7", "0-1", "1-4", "0-3", "0-0", "0-2", "1-7", "L 6"),
]

TEAM_IDS = {
    "ATL": "1610612737", "BOS": "1610612738", "BKN": "1610612751", "CHA": "1610612766",
    "CHI": "1610612741", "CLE": "1610612739", "DAL": "1610612742", "DEN": "1610612743",
    "DET": "1610612765", "GSW": "1610612744", "HOU": "1610612745", "IND": "1610612754",
    "LAC": "1610612746", "LAL": "1610612747", "MEM": "1610612763", "MIA": "1610612748",
    "MIL": "1610612749", "MIN": "1610612750", "NOP": "1610612740", "NYK": "1610612752",
    "OKC": "1610612760", "ORL": "1610612753", "PHI": "1610612755", "PHX": "1610612756",
    "POR": "1610612757", "SAC": "1610612758", "SAS": "1610612759", "TOR": "1610612761",
    "UTA": "1610612762", "WAS": "1610612764",
}

# ---------------------------------------------------------------------------
# 2. Results addendum, 2026-11-02 (S02) and 2026-11-04 (S03).
#    (date, game_id, away, home, away_pts, home_pts, overtime)
#    2026-11-03 is an official 0-game day (the calendar on S03 renders "0 GAMES").
# ---------------------------------------------------------------------------
ADDENDUM = [
    ("2026-11-02", "0022600158", "OKC", "CLE", 117, 112, False),
    ("2026-11-02", "0022600159", "DET", "CHA", 124, 91, False),
    ("2026-11-02", "0022600160", "ATL", "IND", 108, 104, False),
    ("2026-11-02", "0022600161", "BKN", "NYK", 90, 103, False),
    ("2026-11-02", "0022600162", "WAS", "ORL", 103, 94, False),
    ("2026-11-02", "0022600163", "CHI", "PHI", 107, 126, False),
    ("2026-11-02", "0022600164", "SAC", "DAL", 115, 100, False),
    ("2026-11-02", "0022600165", "NOP", "MEM", 135, 134, True),
    ("2026-11-02", "0022600166", "MIL", "MIN", 100, 112, False),
    ("2026-11-02", "0022600167", "BOS", "HOU", 93, 109, False),
    ("2026-11-02", "0022600168", "UTA", "SAS", 97, 119, False),
    ("2026-11-02", "0022600169", "POR", "DEN", 118, 110, False),
    ("2026-11-02", "0022600170", "PHX", "GSW", 113, 116, False),
    ("2026-11-02", "0022600171", "TOR", "LAC", 125, 118, False),
    ("2026-11-02", "0022600172", "MIA", "LAL", 117, 138, False),
    ("2026-11-04", "0022600173", "PHI", "DET", 112, 106, False),
    ("2026-11-04", "0022600174", "ATL", "WAS", 120, 105, False),
    ("2026-11-04", "0022600175", "MIL", "BOS", 102, 109, False),
    ("2026-11-04", "0022600176", "CHA", "BKN", 104, 114, False),
    ("2026-11-04", "0022600177", "CHI", "NYK", 105, 135, False),
    ("2026-11-04", "0022600178", "IND", "MEM", 107, 103, False),
    ("2026-11-04", "0022600179", "UTA", "NOP", 113, 120, True),
    ("2026-11-04", "0022600180", "CLE", "OKC", 116, 124, False),
    ("2026-11-04", "0022600181", "MIN", "HOU", 117, 107, False),
    ("2026-11-04", "0022600182", "TOR", "DEN", 109, 128, False),
    ("2026-11-04", "0022600183", "POR", "PHX", 132, 119, False),
    ("2026-11-04", "0022600184", "DAL", "SAS", 111, 112, False),
    ("2026-11-04", "0022600185", "LAL", "SAC", 116, 103, False),
    ("2026-11-04", "0022600186", "MIA", "LAC", 117, 116, True),
]

# ---------------------------------------------------------------------------
# 3. Tonight's slate (S04) with the official season leaders shown on the card.
# ---------------------------------------------------------------------------
SLATE = [
    {"game_id": "0022600187", "away": "ORL", "home": "PHX", "tip_et": "9:00 PM ET",
     "away_record": "2-5", "home_record": "1-5",
     "leaders": [
         {"team": "ORL", "player": "Franz Wagner", "ppg": 20.3, "rpg": 6.1, "apg": 7.6},
         {"team": "PHX", "player": "Devin Booker", "ppg": 24.7, "rpg": 3.2, "apg": 4.7},
     ]},
    {"game_id": "0022600188", "away": "MIA", "home": "GSW", "tip_et": "10:00 PM ET",
     "away_record": "3-5", "home_record": "5-3",
     "leaders": [
         {"team": "MIA", "player": "Giannis Antetokounmpo", "ppg": 28.3, "rpg": 12.5, "apg": 5.8},
         {"team": "GSW", "player": "Stephen Curry", "ppg": 30.0, "rpg": 4.2, "apg": 4.5},
     ]},
]

# ---------------------------------------------------------------------------
# 4. Official injury report, 11/05/26 04:00 PM ET (S06).
#    (matchup, team, player, current_status, reason)
# ---------------------------------------------------------------------------
INJURIES = [
    ("ORL@PHX", "Orlando Magic", "Banchero, Paolo", "Out", "Injury/Illness - Right High Ankle Sprain"),
    ("ORL@PHX", "Orlando Magic", "Isaac, Jonathan", "Out", "Injury/Illness - Left Knee Injury Management"),
    ("ORL@PHX", "Orlando Magic", "Nelson, Izaiyah", "Out", "Injury/Illness - Left Ankle Injury Recovery"),
    ("ORL@PHX", "Orlando Magic", "Penda, Noah", "Out", "Injury/Illness - Right Partially Torn Hamstring"),
    ("ORL@PHX", "Orlando Magic", "Suggs, Jalen", "Out", "Injury/Illness - Right Knee Contusion/Bone Bruise"),
    ("ORL@PHX", "Phoenix Suns", "Fleming, Rasheer", "Out", "Injury/Illness - Left Ankle Sprain"),
    ("ORL@PHX", "Phoenix Suns", "Goodwin, Jordan", "Out", "Injury/Illness - Right Calf Soreness"),
    ("ORL@PHX", "Phoenix Suns", "Williams, Mark", "Out", "Injury/Illness - Left Shoulder Surgery"),
    ("MIA@GSW", "Miami Heat", "Antetokounmpo, Giannis", "Available", "Injury/Illness - Right Wrist Sprain"),
    ("MIA@GSW", "Miami Heat", "Donaldson, Tre", "Out", "G League - Two-Way"),
    ("MIA@GSW", "Miami Heat", "Goldin, Vladislav", "Out", "G League - Two-Way"),
    ("MIA@GSW", "Golden State Warriors", "Butler III, Jimmy", "Out", "Injury/Illness - Right ACL Repair/Surgery"),
    ("MIA@GSW", "Golden State Warriors", "Moody, Moses", "Out", "Injury/Illness - Left Patellar Tendon Repair / Surgery"),
]

# Teams whose report for tonight was listed as NOT YET SUBMITTED on the same PDF.
NOT_YET_SUBMITTED_1006 = [
    ("BOS@CHA", "Boston Celtics"), ("BOS@CHA", "Charlotte Hornets"),
    ("WAS@ATL", "Washington Wizards"), ("WAS@ATL", "Atlanta Hawks"),
    ("PHI@CLE", "Philadelphia 76ers"), ("PHI@CLE", "Cleveland Cavaliers"),
    ("MIN@NOP", "Minnesota Timberwolves"), ("OKC@MEM", "Oklahoma City Thunder"),
    ("OKC@MEM", "Memphis Grizzlies"), ("TOR@MIL", "Toronto Raptors"),
    ("TOR@MIL", "Milwaukee Bucks"), ("UTA@DAL", "Utah Jazz"),
    ("UTA@DAL", "Dallas Mavericks"), ("POR@LAL", "Portland Trail Blazers"),
    ("POR@LAL", "Los Angeles Lakers"), ("SAS@SAC", "San Antonio Spurs"),
    ("SAS@SAC", "Sacramento Kings"),
]


def team_url(abbr):
    return f"https://www.nba.com/team/{TEAM_IDS[abbr]}"


def game_url(game_id, away, home):
    return f"https://www.nba.com/game/{away.lower()}-vs-{home.lower()}-{game_id}"


def build_standings():
    rows = []
    for (conf, rank, abbr, club, w, l, pct, gb, c, d, h, r, n, ot, l10, streak) in STANDINGS:
        rows.append({
            "conference": conf, "rank": rank, "abbr": abbr, "club": club,
            "w": w, "l": l, "win_pct": pct, "gb": gb, "conf_record": c, "div_record": d,
            "home": h, "road": r, "neutral": n, "ot": ot, "last10": l10, "streak": streak,
            "source_url": S["standings"], "team_url": team_url(abbr),
        })
    return {
        "season": "2026-27", "season_type": "Regular Season", "as_of": CAPTURED_AT_UTC,
        "source_url": S["standings"], "source_id": "S01",
        "note": "Transcribed from the rendered standings table on 2026-11-05 (before the two games of that night).",
        "rows": rows,
    }


def build_results():
    """121 official finals: 92 inherited (2026-10-20..11-01) + 29 captured today."""
    rows = []
    inherited = os.path.join(ROOT, "data", "games_2026-27.csv")
    with open(inherited, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "date": r["date"], "game_id": r["game_id"], "away": r["away"], "home": r["home"],
                "away_pts": int(r["away_pts"]), "home_pts": int(r["home_pts"]),
                "overtime": r["overtime"].strip().lower() in ("ot", "true", "1"),
                "source_url": r["scoreboard_source_url"],
                "game_url": r["game_page_url"],
                "provenance": "inherited",
            })
    for (date, gid, away, home, ap, hp, ot) in ADDENDUM:
        rows.append({
            "date": date, "game_id": gid, "away": away, "home": home,
            "away_pts": ap, "home_pts": hp, "overtime": ot,
            "source_url": S["g1002"] if date == "2026-11-02" else S["g1004"],
            "game_url": game_url(gid, away, home),
            "provenance": "captured-2026-11-05",
        })
    rows.sort(key=lambda r: (r["date"], r["game_id"]))
    return {
        "season": "2026-27", "through": "2026-11-04", "captured_at": CAPTURED_AT_UTC,
        "count": len(rows),
        "note": ("Inherited rows were re-verified in this session by aggregate reconciliation against S01; "
                 "captured rows were read from the official date pages on 2026-11-05."),
        "rows": rows,
    }


def main():
    os.makedirs(DATA, exist_ok=True)
    for name, payload in (
        ("results_2026-27.json", build_results()),
        ("standings_2026-11-05.json", build_standings()),
    ):
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
        print(f"wrote data/{name}")

    slate = {"as_of": CAPTURED_AT_UTC, "source_url": S["slate"], "source_id": "S04", "games": []}
    for g in SLATE:
        g = dict(g)
        g["source_url"] = S["slate"]
        g["game_url"] = game_url(g["game_id"], g["away"], g["home"])
        g["away_team_url"] = team_url(g["away"])
        g["home_team_url"] = team_url(g["home"])
        slate["games"].append(g)
    with open(os.path.join(DATA, "slate_2026-11-05.json"), "w", encoding="utf-8") as fh:
        json.dump(slate, fh, indent=1)
    print("wrote data/slate_2026-11-05.json")

    inj = {
        "as_of": CAPTURED_AT_UTC, "edition": "11/05/26 04:00 PM ET",
        "policy_url": S["injury_policy"], "source_url": S["injury_pdf"], "source_id": "S06",
        "policy_note": ("Per S05, teams must designate a participation status by 5 p.m. local time the day before a "
                        "game (1 p.m. for the second game of a back-to-back) and submit a game-day report between "
                        "11 a.m. and 1 p.m. local time. Statuses change during the day; this page is a single "
                        "point-in-time snapshot and is not a forecast."),
        "rows": [{"matchup": m, "team": t, "player": p, "status": st, "reason": rs,
                  "source_url": S["injury_pdf"]} for (m, t, p, st, rs) in INJURIES],
        "not_yet_submitted": [{"matchup": m, "team": t, "status": "NOT YET SUBMITTED",
                               "source_url": S["injury_pdf"]} for (m, t) in NOT_YET_SUBMITTED_1006],
    }
    with open(os.path.join(DATA, "injuries_2026-11-05.json"), "w", encoding="utf-8") as fh:
        json.dump(inj, fh, indent=1)
    print("wrote data/injuries_2026-11-05.json")


if __name__ == "__main__":
    main()

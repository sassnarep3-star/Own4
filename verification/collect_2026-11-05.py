#!/usr/bin/env python3
"""
Own4 — FRESH OFFICIAL TRANSCRIPTION, snapshot 2026-11-05 (UTC).

WHY THIS FILE EXISTS
--------------------
The repository's stored "official" snapshot (official/*.json, data/*.json) is dated
2026-11-02. This session re-read the official NBA pages on 2026-11-05 and transcribed
the current values line by line so the published site can state the exact date and the
exact page behind every number.

METHOD / HONESTY RULES
----------------------
* Every value below was read from the page named in SOURCES and is stored with the
  exact source URL. Nothing is estimated, interpolated or copied from a model.
* Only columns actually displayed on the fetched page are stored. If a page did not
  expose a value, the field is absent (rendered blank + flagged) rather than filled.
* No scraping, no API extraction, no bulk download was performed: the pages were read
  through the public web rendering of the site. The NBA Stats FAQ
  (https://www.nba.com/stats/help/faq) states that statistics are not available for
  download for personal or academic use, so only the values needed for this research
  were transcribed, each with its official URL. This restriction is flagged for review.
* Page state is a point-in-time snapshot; values change as games are played.

Run:  python3 verification/collect_2026-11-05.py      (writes verification/data/*.json)
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
SNAPSHOT = "2026-11-05"
FETCHED_UTC = "2026-11-05"

SOURCES = [
    {
        "id": "S1",
        "name": "NBA.com — 2026-27 Regular Season Standings",
        "url": "https://www.nba.com/standings",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "Both conference tables (East 15 rows, West 15 rows): W, L, WIN%, GB, CONF, DIV, HOME, ROAD, Neutral, OT, LAST10, STREAK, official team deep links.",
        "contains": "30 teams x 13 standings fields",
    },
    {
        "id": "S2",
        "name": "NBA.com Stats — Teams Traditional, 2026-27, Per Game",
        "url": "https://www.nba.com/stats/teams/traditional",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "All 30 rows of the Traditional team table (Per Game default): GP, W, L, MIN, PTS, FG%, 3P%, FT%, REB, AST, TOV, STL, BLK, +/-.",
        "contains": "30 teams x 14 stat fields",
    },
    {
        "id": "S3",
        "name": "NBA.com — Games & Scores, 2026-11-02 (15 games, final)",
        "url": "https://www.nba.com/games?date=2026-11-02",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "All 15 final scores and the official game id / deep link for each.",
        "contains": "15 final scores",
    },
    {
        "id": "S4",
        "name": "NBA.com — Games & Scores, 2026-11-04 (14 games, final)",
        "url": "https://www.nba.com/games?date=2026-11-04",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "All 14 final scores (two overtime games marked Final/OT) and official game ids.",
        "contains": "14 final scores",
    },
    {
        "id": "S5",
        "name": "NBA.com — Games & Scores, 2026-11-05 (2 scheduled games + season leaders)",
        "url": "https://www.nba.com/games?date=2026-11-05",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "The two scheduled games with tip times, both teams' records, and each team's 'Season Leaders' PPG/RPG/APG block.",
        "contains": "2 scheduled games; 4 player season-leader rows",
    },
    {
        "id": "S6",
        "name": "NBA.com — Games calendar, October 2026",
        "url": "https://www.nba.com/games?date=2026-10-20",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "October 2026 calendar showing the number of games scheduled on each date (used only to state coverage of the game sample).",
        "contains": "12 October dates with game counts",
    },
    {
        "id": "S7",
        "name": "NBA.com — Games calendar, November 2026",
        "url": "https://www.nba.com/games?date=2026-11-05",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "November 2026 calendar game counts (11/01: 4, 11/02: 15, 11/03: 0, 11/04: 14, 11/05: 2).",
        "contains": "5 November dates used for coverage",
    },
    {
        "id": "S8",
        "name": "NBA Stats Help — Glossary (stat definitions)",
        "url": "https://www.nba.com/stats/help/glossary",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "Definitions used to label columns (PTS, REB, AST, TOV, STL, BLK, PACE, plus/minus).",
        "contains": "column definitions",
    },
    {
        "id": "S9",
        "name": "NBA Stats Help — FAQ (download / usage restriction)",
        "url": "https://www.nba.com/stats/help/faq",
        "domain": "nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "Statement that NBA stats are not available for download for personal or academic use; basis of the data-rights flag.",
        "contains": "usage restriction",
    },
    {
        "id": "S10",
        "name": "NBA Official — Injury Report, 2026-27 season",
        "url": "https://official.nba.com/nba-injury-report-2026-27-season/",
        "domain": "official.nba.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "Cited for the existence and schedule of the official injury report as a required pre-bet availability check. Player statuses in this snapshot are NOT transcribed (see flagged page).",
        "contains": "policy / reporting schedule",
    },
    {
        "id": "S11",
        "name": "GitHub REST API — Pages configuration and build status for this repository",
        "url": "https://api.github.com/repos/sassnarep3-star/Own4/pages",
        "domain": "api.github.com",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "Pages source (branch main, path /), status built; used to verify deployment, not for any NBA value.",
        "contains": "deployment status",
    },
    {
        "id": "S12",
        "name": "National Council on Problem Gambling — helpline",
        "url": "https://www.ncpgambling.org/help-treatment",
        "domain": "ncpgambling.org",
        "official": True,
        "read_on": FETCHED_UTC,
        "read_scope": "National Problem Gambling Helpline number shown in the site footer.",
        "contains": "helpline reference",
    },
]

TEAMS = {
    # abbr:      (full name, nba team id, official team slug)
    "ATL": ("Atlanta Hawks", "1610612737", "hawks"),
    "BOS": ("Boston Celtics", "1610612738", "celtics"),
    "BKN": ("Brooklyn Nets", "1610612751", "nets"),
    "CHA": ("Charlotte Hornets", "1610612766", "hornets"),
    "CHI": ("Chicago Bulls", "1610612741", "bulls"),
    "CLE": ("Cleveland Cavaliers", "1610612739", "cavaliers"),
    "DAL": ("Dallas Mavericks", "1610612742", "mavericks"),
    "DEN": ("Denver Nuggets", "1610612743", "nuggets"),
    "DET": ("Detroit Pistons", "1610612765", "pistons"),
    "GSW": ("Golden State Warriors", "1610612744", "warriors"),
    "HOU": ("Houston Rockets", "1610612745", "rockets"),
    "IND": ("Indiana Pacers", "1610612754", "pacers"),
    "LAC": ("LA Clippers", "1610612746", "clippers"),
    "LAL": ("Los Angeles Lakers", "1610612747", "lakers"),
    "MEM": ("Memphis Grizzlies", "1610612763", "grizzlies"),
    "MIA": ("Miami Heat", "1610612748", "heat"),
    "MIL": ("Milwaukee Bucks", "1610612749", "bucks"),
    "MIN": ("Minnesota Timberwolves", "1610612750", "timberwolves"),
    "NOP": ("New Orleans Pelicans", "1610612740", "pelicans"),
    "NYK": ("New York Knicks", "1610612752", "knicks"),
    "OKC": ("Oklahoma City Thunder", "1610612760", "thunder"),
    "ORL": ("Orlando Magic", "1610612753", "magic"),
    "PHI": ("Philadelphia 76ers", "1610612755", "sixers"),
    "PHX": ("Phoenix Suns", "1610612756", "suns"),
    "POR": ("Portland Trail Blazers", "1610612757", "blazers"),
    "SAC": ("Sacramento Kings", "1610612758", "kings"),
    "SAS": ("San Antonio Spurs", "1610612759", "spurs"),
    "TOR": ("Toronto Raptors", "1610612761", "raptors"),
    "UTA": ("Utah Jazz", "1610612762", "jazz"),
    "WAS": ("Washington Wizards", "1610612764", "wizards"),
}

# ---------------------------------------------------------------------------
# S1 — standings, transcribed from the two conference tables, in displayed order
# columns: abbr, W, L, pct, gb, conf, div, home, road, neutral, ot, last10, streak
# ---------------------------------------------------------------------------
STANDINGS = [
    ("East", [
        ("PHI", 8, 1, ".889", "--", "8-1", "2-0", "4-1", "4-0", "0-0", "0-0", "8-1", "W 5"),
        ("DET", 6, 2, ".750", "1.5", "6-2", "0-0", "2-1", "4-1", "0-0", "0-0", "6-2", "L 1"),
        ("BOS", 6, 2, ".750", "1.5", "6-1", "2-0", "5-0", "1-2", "0-0", "1-0", "6-2", "W 1"),
        ("ATL", 5, 4, ".556", "3", "5-1", "3-1", "1-2", "4-2", "0-0", "0-0", "5-4", "W 2"),
        ("TOR", 4, 4, ".500", "3.5", "3-1", "0-0", "2-1", "2-3", "0-0", "0-0", "4-4", "L 1"),
        ("CLE", 4, 4, ".500", "3.5", "3-2", "1-0", "3-1", "1-3", "0-0", "1-0", "4-4", "L 2"),
        ("WAS", 4, 4, ".500", "3.5", "4-4", "2-2", "2-2", "2-2", "0-0", "0-0", "4-4", "L 1"),
        ("NYK", 4, 4, ".500", "3.5", "4-4", "1-3", "3-2", "1-2", "0-0", "0-0", "4-4", "W 2"),
        ("MIA", 3, 5, ".375", "4.5", "2-2", "1-1", "1-3", "2-2", "0-0", "1-0", "3-5", "W 1"),
        ("CHA", 3, 6, ".333", "5", "3-6", "2-2", "2-3", "1-3", "0-0", "0-0", "3-6", "L 5"),
        ("IND", 3, 6, ".333", "5", "1-5", "0-1", "0-4", "3-2", "0-0", "0-0", "3-6", "W 1"),
        ("ORL", 2, 5, ".286", "5", "2-4", "0-2", "0-4", "2-1", "0-0", "0-0", "2-5", "L 2"),
        ("BKN", 2, 6, ".250", "5.5", "2-6", "0-2", "1-3", "1-3", "0-0", "0-1", "2-6", "W 1"),
        ("CHI", 1, 7, ".125", "6.5", "1-7", "1-0", "0-2", "1-5", "0-0", "0-0", "1-7", "L 6"),
        ("MIL", 1, 7, ".125", "6.5", "1-5", "1-2", "1-3", "0-4", "0-0", "0-0", "1-7", "L 4"),
    ]),
    ("West", [
        ("POR", 6, 1, ".857", "--", "6-1", "2-0", "1-1", "5-0", "0-0", "0-0", "6-1", "W 3"),
        ("LAL", 7, 2, ".778", "--", "5-2", "4-1", "4-1", "3-1", "0-0", "0-0", "7-2", "W 3"),
        ("HOU", 7, 2, ".778", "--", "3-2", "2-1", "4-1", "3-1", "0-0", "0-0", "7-2", "L 1"),
        ("OKC", 6, 2, ".750", "0.5", "4-2", "1-0", "4-0", "2-2", "0-0", "0-0", "6-2", "W 2"),
        ("SAS", 6, 2, ".750", "0.5", "6-2", "2-1", "4-2", "2-0", "0-0", "1-0", "6-2", "W 6"),
        ("MEM", 6, 2, ".750", "0.5", "6-1", "0-1", "2-2", "4-0", "0-0", "0-1", "6-2", "L 2"),
        ("MIN", 6, 3, ".667", "1", "2-2", "0-0", "3-1", "3-2", "0-0", "0-1", "6-3", "W 2"),
        ("GSW", 5, 3, ".625", "1.5", "5-3", "3-2", "3-1", "2-2", "0-0", "0-0", "5-3", "W 5"),
        ("DEN", 4, 3, ".571", "2", "3-3", "0-2", "2-2", "2-1", "0-0", "1-0", "4-3", "W 1"),
        ("NOP", 4, 4, ".500", "2.5", "3-3", "1-0", "3-2", "1-2", "0-0", "2-1", "4-4", "W 4"),
        ("DAL", 4, 4, ".500", "2.5", "2-4", "1-3", "2-2", "2-2", "0-0", "0-0", "4-4", "L 2"),
        ("PHX", 1, 5, ".167", "4.5", "1-5", "1-1", "1-2", "0-3", "0-0", "0-0", "1-5", "L 4"),
        ("LAC", 1, 7, ".125", "5.5", "1-5", "1-3", "1-3", "0-4", "0-0", "0-1", "1-7", "L 7"),
        ("SAC", 1, 7, ".125", "5.5", "1-7", "0-2", "0-3", "1-4", "0-0", "0-0", "1-7", "L 1"),
        ("UTA", 1, 7, ".125", "5.5", "1-7", "0-1", "1-4", "0-3", "0-0", "0-2", "1-7", "L 6"),
    ]),
]

# ---------------------------------------------------------------------------
# S2 — team stats, Per Game. Columns as displayed on the page.
# abbr, GP, W, L, MIN, PTS, FG%, 3P%, FT%, REB, AST, TOV, STL, BLK, plus_minus
# ---------------------------------------------------------------------------
TEAM_STATS = [
    ("PHI", 9, 8, 1, 48.0, 111.0, 45.2, 34.4, 76.7, 42.3, 26.1, 13.0, 8.9, 4.7, 5.8),
    ("POR", 7, 6, 1, 48.0, 121.9, 47.6, 35.5, 73.9, 47.4, 27.1, 15.7, 7.1, 5.0, 11.1),
    ("HOU", 9, 7, 2, 48.0, 117.9, 49.0, 38.6, 81.4, 43.8, 28.0, 15.9, 9.1, 5.9, 10.3),
    ("LAL", 9, 7, 2, 48.0, 121.8, 51.2, 38.8, 80.1, 39.9, 24.8, 17.7, 10.2, 7.1, 7.9),
    ("BOS", 8, 6, 2, 48.6, 114.3, 45.1, 35.3, 78.1, 43.9, 26.5, 15.0, 8.6, 4.0, 6.0),
    ("DET", 8, 6, 2, 48.0, 111.1, 46.8, 37.8, 75.9, 44.0, 26.9, 15.1, 9.3, 6.5, 9.4),
    ("MEM", 8, 6, 2, 48.6, 120.5, 47.3, 40.0, 82.2, 49.5, 27.5, 16.5, 6.3, 5.8, 10.8),
    ("OKC", 8, 6, 2, 48.0, 110.0, 44.0, 33.3, 85.8, 46.6, 21.6, 13.3, 7.8, 5.8, 1.3),
    ("SAS", 8, 6, 2, 48.6, 116.9, 45.5, 32.2, 80.1, 48.5, 26.5, 13.0, 8.4, 7.4, 8.3),
    ("MIN", 9, 6, 3, 48.6, 118.8, 47.6, 38.0, 63.4, 49.2, 26.8, 15.4, 9.2, 5.2, 11.2),
    ("GSW", 8, 5, 3, 48.0, 117.5, 45.5, 38.9, 81.8, 43.9, 26.8, 16.5, 8.9, 3.9, 2.9),
    ("DEN", 7, 4, 3, 48.7, 115.4, 49.0, 37.2, 80.9, 41.6, 27.6, 15.7, 10.7, 3.7, 0.7),
    ("ATL", 9, 5, 4, 48.0, 115.8, 44.5, 35.1, 75.1, 44.7, 31.0, 14.8, 9.7, 3.4, 2.8),
    ("CLE", 8, 4, 4, 48.6, 119.3, 46.4, 37.2, 76.1, 47.5, 27.8, 14.0, 7.3, 6.0, 2.1),
    ("DAL", 8, 4, 4, 48.0, 111.9, 46.9, 33.7, 77.0, 43.3, 26.3, 15.9, 8.6, 5.8, -0.1),
    ("NOP", 8, 4, 4, 49.9, 121.6, 48.7, 31.7, 82.4, 44.9, 25.4, 17.4, 12.4, 4.8, 2.4),
    ("NYK", 8, 4, 4, 48.0, 110.0, 42.9, 36.6, 77.5, 48.3, 26.0, 15.4, 7.4, 4.4, 4.9),
    ("TOR", 8, 4, 4, 48.0, 117.9, 46.1, 31.9, 73.8, 42.3, 28.8, 14.4, 11.5, 3.9, 4.4),
    ("WAS", 8, 4, 4, 48.0, 108.9, 47.6, 29.4, 81.4, 41.0, 24.8, 14.6, 7.6, 5.8, -0.1),
    ("MIA", 8, 3, 5, 48.6, 118.0, 47.2, 33.5, 73.9, 43.3, 29.5, 15.1, 8.4, 5.1, -4.9),
    ("CHA", 9, 3, 6, 48.0, 98.1, 40.4, 29.6, 81.9, 46.1, 21.1, 19.4, 7.1, 5.0, -11.1),
    ("IND", 9, 3, 6, 48.0, 111.2, 46.5, 32.8, 75.1, 41.8, 26.7, 15.8, 7.8, 4.9, -3.0),
    ("ORL", 7, 2, 5, 48.0, 105.7, 45.3, 34.3, 78.3, 38.9, 25.9, 17.3, 6.9, 3.7, -9.0),
    ("BKN", 8, 2, 6, 48.6, 106.6, 42.8, 35.3, 76.2, 42.9, 22.8, 17.8, 8.6, 4.8, -6.3),
    ("PHX", 6, 1, 5, 48.0, 113.3, 46.2, 33.9, 78.2, 39.5, 27.3, 14.7, 8.7, 5.5, -11.0),
    ("CHI", 8, 1, 7, 48.0, 111.6, 41.2, 27.2, 74.6, 43.9, 24.6, 16.5, 8.4, 5.1, -18.0),
    ("LAC", 8, 1, 7, 48.6, 109.1, 45.3, 38.2, 80.1, 41.5, 25.6, 20.1, 10.1, 4.5, -6.5),
    ("MIL", 8, 1, 7, 48.0, 110.0, 43.1, 34.3, 70.9, 49.0, 26.0, 16.5, 5.6, 4.5, -12.3),
    ("SAC", 8, 1, 7, 48.0, 109.3, 45.2, 32.5, 75.1, 40.9, 24.4, 17.3, 7.8, 2.9, -14.0),
    ("UTA", 8, 1, 7, 49.3, 107.8, 42.9, 31.5, 75.8, 46.6, 24.6, 17.4, 6.8, 6.6, -11.3),
]

# ---------------------------------------------------------------------------
# S3 / S4 — final scores. nba.com lists the visiting team first ("away-vs-home").
# fields: date, game_id, away, away_pts, home, home_pts, ot, source_id
# ---------------------------------------------------------------------------
GAMES_FRESH = [
    ("2026-11-02", "0022600158", "OKC", 117, "CLE", 112, False, "S3"),
    ("2026-11-02", "0022600163", "CHI", 107, "PHI", 126, False, "S3"),
    ("2026-11-02", "0022600160", "ATL", 108, "IND", 104, False, "S3"),
    ("2026-11-02", "0022600161", "BKN", 90, "NYK", 103, False, "S3"),
    ("2026-11-02", "0022600162", "WAS", 103, "ORL", 94, False, "S3"),
    ("2026-11-02", "0022600159", "DET", 124, "CHA", 91, False, "S3"),
    ("2026-11-02", "0022600164", "SAC", 115, "DAL", 100, False, "S3"),
    ("2026-11-02", "0022600166", "MIL", 100, "MIN", 112, False, "S3"),
    ("2026-11-02", "0022600165", "NOP", 135, "MEM", 134, True, "S3"),
    ("2026-11-02", "0022600167", "BOS", 93, "HOU", 109, False, "S3"),
    ("2026-11-02", "0022600168", "UTA", 97, "SAS", 119, False, "S3"),
    ("2026-11-02", "0022600169", "POR", 118, "DEN", 110, False, "S3"),
    ("2026-11-02", "0022600171", "TOR", 125, "LAC", 118, False, "S3"),
    ("2026-11-02", "0022600170", "PHX", 113, "GSW", 116, False, "S3"),
    ("2026-11-02", "0022600172", "MIA", 117, "LAL", 138, False, "S3"),
    ("2026-11-04", "0022600174", "ATL", 120, "WAS", 105, False, "S4"),
    ("2026-11-04", "0022600173", "PHI", 112, "DET", 106, False, "S4"),
    ("2026-11-04", "0022600175", "MIL", 102, "BOS", 109, False, "S4"),
    ("2026-11-04", "0022600176", "CHA", 104, "BKN", 114, False, "S4"),
    ("2026-11-04", "0022600177", "CHI", 105, "NYK", 135, False, "S4"),
    ("2026-11-04", "0022600180", "CLE", 116, "OKC", 124, False, "S4"),
    ("2026-11-04", "0022600179", "UTA", 113, "NOP", 120, True, "S4"),
    ("2026-11-04", "0022600178", "IND", 107, "MEM", 103, False, "S4"),
    ("2026-11-04", "0022600181", "MIN", 117, "HOU", 107, False, "S4"),
    ("2026-11-04", "0022600182", "TOR", 109, "DEN", 128, False, "S4"),
    ("2026-11-04", "0022600183", "POR", 132, "PHX", 119, False, "S4"),
    ("2026-11-04", "0022600184", "DAL", 111, "SAS", 112, False, "S4"),
    ("2026-11-04", "0022600185", "LAL", 116, "SAC", 103, False, "S4"),
    ("2026-11-04", "0022600186", "MIA", 117, "LAC", 116, True, "S4"),
]

# ---------------------------------------------------------------------------
# S5 — scheduled slate (no score exists at fetch time) + official season leaders
# ---------------------------------------------------------------------------
SLATE = [
    ("0022600187", "2026-11-05", "ORL", "PHX", "9:00 PM ET"),
    ("0022600188", "2026-11-05", "MIA", "GSW", "10:00 PM ET"),
]

SEASON_LEADERS = [
    # team, player, ppg, rpg, apg, source_id  (block titled "Season Leaders" on S5)
    ("ORL", "Franz Wagner", 20.3, 6.1, 7.6, "S5"),
    ("PHX", "Devin Booker", 24.7, 3.2, 4.7, "S5"),
    ("MIA", "Giannis Antetokounmpo", 28.3, 12.5, 5.8, "S5"),
    ("GSW", "Stephen Curry", 30.0, 4.2, 4.5, "S5"),
]

# ---------------------------------------------------------------------------
# S6 / S7 — official calendar game counts (coverage bookkeeping only)
# ---------------------------------------------------------------------------
CALENDAR = {
    "2026-10-20": 3, "2026-10-21": 11, "2026-10-22": 2, "2026-10-23": 12,
    "2026-10-24": 8, "2026-10-25": 7, "2026-10-26": 9, "2026-10-27": 4,
    "2026-10-28": 12, "2026-10-29": 3, "2026-10-30": 10, "2026-10-31": 7,
    "2026-11-01": 4, "2026-11-02": 15, "2026-11-03": 0, "2026-11-04": 14,
    "2026-11-05": 2,
}


def team_url(abbr):
    _name, tid, slug = TEAMS[abbr]
    return "https://www.nba.com/team/%s/%s" % (tid, slug)


def build():
    os.makedirs(OUT, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(OUT, name), "w") as f:
            json.dump(obj, f, indent=1, sort_keys=False)
            f.write("\n")

    dump("sources.json", {"snapshot": SNAPSHOT, "fetched_utc": FETCHED_UTC, "sources": SOURCES})

    rows = []
    for conf, teams in STANDINGS:
        for i, t in enumerate(teams, start=1):
            (abbr, w, l, pct, gb, confrec, div, home, road, neutral, ot, last10, streak) = t
            rows.append({
                "conference": conf, "rank": i, "abbr": abbr, "team": TEAMS[abbr][0],
                "team_id": TEAMS[abbr][1], "W": w, "L": l, "GP": w + l, "win_pct": pct,
                "GB": gb, "CONF": confrec, "DIV": div, "HOME": home, "ROAD": road,
                "NEUTRAL": neutral, "OT": ot, "LAST10": last10, "STREAK": streak,
                "source_id": "S1", "source_url": "https://www.nba.com/standings",
                "team_url": team_url(abbr), "verified_on": SNAPSHOT,
            })
    dump("standings.json", {"snapshot": SNAPSHOT, "season": "2026-27", "rows": rows})

    rows = []
    for (abbr, gp, w, l, mins, pts, fg, tp, ft, reb, ast, tov, stl, blk, pm) in TEAM_STATS:
        rows.append({
            "abbr": abbr, "team": TEAMS[abbr][0], "team_id": TEAMS[abbr][1],
            "GP": gp, "W": w, "L": l, "MIN": mins, "PTS": pts, "FG_pct": fg,
            "3P_pct": tp, "FT_pct": ft, "REB": reb, "AST": ast, "TOV": tov,
            "STL": stl, "BLK": blk, "plus_minus": pm,
            "source_id": "S2", "source_url": "https://www.nba.com/stats/teams/traditional",
            "team_stats_url": "https://www.nba.com/stats/team/%s/traditional" % TEAMS[abbr][1],
            "definitions_url": "https://www.nba.com/stats/help/glossary",
            "verified_on": SNAPSHOT,
        })
    dump("team_stats.json", {"snapshot": SNAPSHOT, "season": "2026-27", "rows": rows})

    rows = []
    for (date, gid, away, ap, home, hp, ot, sid) in GAMES_FRESH:
        src = "https://www.nba.com/games?date=%s" % date
        rows.append({
            "date": date, "game_id": gid, "away": away, "away_name": TEAMS[away][0],
            "away_pts": ap, "home": home, "home_name": TEAMS[home][0], "home_pts": hp,
            "total": ap + hp, "margin_home": hp - ap, "ot": ot,
            "source_id": sid, "source_url": src,
            "game_url": "https://www.nba.com/game/%s-vs-%s-%s" % (away.lower(), home.lower(), gid),
            "verified_on": SNAPSHOT,
        })
    dump("games_fresh.json", {"snapshot": SNAPSHOT, "rows": rows})

    rows = []
    for (gid, date, away, home, tip) in SLATE:
        rows.append({
            "game_id": gid, "date": date, "away": away, "away_name": TEAMS[away][0],
            "home": home, "home_name": TEAMS[home][0], "tip_et": tip, "final": None,
            "source_id": "S5", "source_url": "https://www.nba.com/games?date=2026-11-05",
            "game_url": "https://www.nba.com/game/%s-vs-%s-%s" % (away.lower(), home.lower(), gid),
            "verified_on": SNAPSHOT,
        })
    dump("slate.json", {"snapshot": SNAPSHOT, "date": "2026-11-05", "rows": rows})

    rows = []
    for (abbr, player, ppg, rpg, apg, sid) in SEASON_LEADERS:
        rows.append({
            "team": abbr, "team_name": TEAMS[abbr][0], "player": player,
            "PPG": ppg, "RPG": rpg, "APG": apg, "source_id": sid,
            "source_url": "https://www.nba.com/games?date=2026-11-05",
            "verified_on": SNAPSHOT,
            "label": "official 'Season Leaders' block",
        })
    dump("season_leaders.json", {"snapshot": SNAPSHOT, "rows": rows})

    dump("calendar.json", {"snapshot": SNAPSHOT, "source_id": "S6",
                          "source_urls": ["https://www.nba.com/games?date=2026-10-20",
                                          "https://www.nba.com/games?date=2026-11-05"],
                          "days": CALENDAR})

    print("wrote %d files to %s" % (len(os.listdir(OUT)), OUT))


if __name__ == "__main__":
    build()

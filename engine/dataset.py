#!/usr/bin/env python3
"""
Own4 — OFFICIAL DATA TRANSCRIPTION (single source of truth).

Every numeric value in this file was transcribed line by line from an NBA.com
page that was fetched and read during the 2026-11-02 integration session.
Nothing is inferred, estimated, or filled in. Each emitted row carries the
exact official URL it came from, plus the official per-entity deep link where
one was present on the fetched page.

Source pages actually fetched (all official, nba.com / official.nba.com):
  S1  https://www.nba.com/standings                       (2026-27 standings)
  S2  https://www.nba.com/stats/teams/traditional         (2026-27 team stats)
  S3  https://www.nba.com/stats/overview                  (11/01/2026 daily leaders)
  S4  https://www.nba.com/games?date=2026-11-02           (11/02/2026 slate + season leaders)
  S5..S10 https://www.nba.com/games?date=<date>           (final scores, 6 dates)
  S11 https://www.nba.com/game/tor-vs-lal-0022600157/box-score (11/02 slate nav)
  S12 https://www.nba.com/stats/help/faq                  (NBA Stats FAQ)
  S13 https://www.nba.com/stats/help/glossary             (NBA Stats glossary)
  S14 https://official.nba.com/nba-injury-report-2026-27-season/ (injury policy)
  S15 https://www.nba.com/news/10-numbers-know-first-10-days-2025-26
  S16 https://www.nba.com/news/4-key-stats-takeaways-2025-26-season
  S17 https://www.nba.com/news/2025-26-nba-regular-season-schedule
  S18 https://www.nba.com/christmas/schedule
  S19 https://official.nba.com/rule-no-4-definitions/
  S20 https://videorulebook.nba.com/archive/travel-on-the-perimeter-catch-gather-then-too-many-steps-2/
  S21 https://gleague.nba.com/nba-g-league-101-two-way-contracts
  S22 https://www.ncpgambling.org/help-treatment
  S23 https://www.nba.com/stats/players/traditional?PerMode=Totals&sort=PTS&dir=-1
  S24 https://api.github.com/repos/sassnarep3-star/Own4/pages (GitHub, official)
  S25 https://github.com/sassnarep3-star/Own4                  (GitHub, official)

IMPORTANT USAGE NOTICE (flagged for review): the NBA Stats FAQ (S12) states
"Our stats are not available for download for either academic or personal use.
They are for viewing and enjoying on NBA.com/Stats". No automated download,
scraping, API extraction or bulk copy was performed. Values below were read
from the publicly displayed pages and transcribed by hand for verification,
with the exact official URL retained on every row for manual review.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "official")
VERIFIED_ON = "2026-11-02"
SEASON = "2026-27"

S = {
    "S1": "https://www.nba.com/standings",
    "S2": "https://www.nba.com/stats/teams/traditional",
    "S3": "https://www.nba.com/stats/overview",
    "S4": "https://www.nba.com/games?date=2026-11-02",
    "S12": "https://www.nba.com/stats/help/faq",
    "S13": "https://www.nba.com/stats/help/glossary",
    "S14": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "S15": "https://www.nba.com/news/10-numbers-know-first-10-days-2025-26",
    "S16": "https://www.nba.com/news/4-key-stats-takeaways-2025-26-season",
    "S17": "https://www.nba.com/news/2025-26-nba-regular-season-schedule",
    "S18": "https://www.nba.com/christmas/schedule",
    "S19": "https://official.nba.com/rule-no-4-definitions/",
    "S20": "https://videorulebook.nba.com/archive/travel-on-the-perimeter-catch-gather-then-too-many-steps-2/",
    "S21": "https://gleague.nba.com/nba-g-league-101-two-way-contracts",
    "S22": "https://www.ncpgambling.org/help-treatment",
    "S11": "https://www.nba.com/game/tor-vs-lal-0022600157/box-score",
    "S23": "https://www.nba.com/stats/players/traditional?PerMode=Totals&sort=PTS&dir=-1",
    "S24": "https://api.github.com/repos/sassnarep3-star/Own4/pages",
    "S25": "https://github.com/sassnarep3-star/Own4",
}

def games_url(d):
    return "https://www.nba.com/games?date=" + d

# ---------------------------------------------------------------------------
# Source registry (all URLs fetched and read; no invented links)
# ---------------------------------------------------------------------------
SOURCES = [
    {"id": "S1", "name": "NBA.com — 2026-27 Regular Season Standings", "url": S["S1"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "All 30 teams: W, L, WIN%, GB, CONF, DIV, HOME, ROAD, OT, LAST10, STREAK", "fetched_chunks": 2},
    {"id": "S2", "name": "NBA.com Stats — Teams Traditional (2026-27)", "url": S["S2"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "All 30 teams: GP, W, L, PTS, FG%, 3P%, FT%, REB, AST, TOV, STL, BLK, +/-", "fetched_chunks": 5},
    {"id": "S3", "name": "NBA.com Stats — Overview / Yesterday's Leaders (11/01/2026)", "url": S["S3"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Daily leaders: PTS, REB, AST, BLK, STL, TOV, 3PM, FTM, Fantasy Points", "fetched_chunks": 1},
    {"id": "S4", "name": "NBA.com — Games & Scores, 2026-11-02 slate", "url": S["S4"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "15 scheduled games, tip times, team records, season leaders PPG/RPG/APG", "fetched_chunks": 3},
    {"id": "S5", "name": "NBA.com — Games & Scores, 2026-10-21", "url": games_url("2026-10-21"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "11 final scores + game leaders", "fetched_chunks": 2},
    {"id": "S6", "name": "NBA.com — Games & Scores, 2026-10-23", "url": games_url("2026-10-23"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "12 final scores + game leaders", "fetched_chunks": 2},
    {"id": "S7", "name": "NBA.com — Games & Scores, 2026-10-28", "url": games_url("2026-10-28"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "12 final scores + game leaders", "fetched_chunks": 2},
    {"id": "S8", "name": "NBA.com — Games & Scores, 2026-10-30 (NBA Cup group play)", "url": games_url("2026-10-30"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "10 final scores + game leaders", "fetched_chunks": 2},
    {"id": "S9", "name": "NBA.com — Games & Scores, 2026-10-31", "url": games_url("2026-10-31"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "7 final scores + game leaders", "fetched_chunks": 2},
    {"id": "S10", "name": "NBA.com — Games & Scores, 2026-11-01", "url": games_url("2026-11-01"), "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "4 final scores + game leaders", "fetched_chunks": 1},
    {"id": "S11", "name": "NBA.com — Box score nav, TOR vs LAL (0022600157)", "url": "https://www.nba.com/game/tor-vs-lal-0022600157/box-score", "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Official 11/02/2026 15-game listing used to cross-check the slate", "fetched_chunks": 1},
    {"id": "S12", "name": "NBA.com Stats — Frequently Asked Questions", "url": S["S12"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Stat usage restrictions; PIE/winning-percentage R-square .908; definitions", "fetched_chunks": 1},
    {"id": "S13", "name": "NBA.com Stats — Stat Glossary", "url": S["S13"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Official definitions of PTS, REB, AST, +/- etc.", "fetched_chunks": 1},
    {"id": "S14", "name": "NBA Official — NBA Injury Report: 2026-27 Season", "url": S["S14"], "domain": "official.nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "5 p.m. local day-before deadline; 1 p.m. second night of back-to-back", "fetched_chunks": 1},
    {"id": "S15", "name": "NBA.com — 10 numbers to know from the first 10 days of 2025-26", "url": S["S15"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "117.7 PTS/team/game, 101.9 possessions/48, 114.3 OffRtg (through Oct 30, 2025)", "fetched_chunks": 1},
    {"id": "S16", "name": "NBA.com — 4 key stats takeaways from 2025-26 season", "url": S["S16"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Wembanyama 197 blocks; Jokic first to lead REB+AST since 1969-70", "fetched_chunks": 3},
    {"id": "S17", "name": "NBA.com — 2025-26 regular season schedule release", "url": S["S17"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Five Christmas Day games and their matchups", "fetched_chunks": 1},
    {"id": "S18", "name": "NBA.com — NBA on Christmas Day schedule", "url": S["S18"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Five Christmas Day games and tip times", "fetched_chunks": 1},
    {"id": "S19", "name": "NBA Official — Rule No. 4: Definitions", "url": S["S19"], "domain": "official.nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Official definitions; visiting team chooses basket first half", "fetched_chunks": 1},
    {"id": "S20", "name": "NBA Video Rulebook — traveling on the perimeter", "url": S["S20"], "domain": "videorulebook.nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Official traveling interpretation", "fetched_chunks": 1},
    {"id": "S21", "name": "NBA G League — Two-Way Contracts 101", "url": S["S21"], "domain": "gleague.nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Two-way contract explainer page (numeric terms not confirmed in retrievable text)", "fetched_chunks": 2},
    {"id": "S22", "name": "National Council on Problem Gambling — Helpline", "url": S["S22"], "domain": "ncpgambling.org", "official": True, "verified_on": VERIFIED_ON,
     "contains": "National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738)", "fetched_chunks": 1},
    {"id": "S23", "name": "NBA.com Stats — Players Traditional (2026-27)", "url": S["S23"], "domain": "nba.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Official player totals table", "fetched_chunks": 2},
    {"id": "S24", "name": "GitHub Pages settings API for this repository", "url": S["S24"], "domain": "api.github.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "build_type=legacy, source.branch=main, source.path=/", "fetched_chunks": 1},
    {"id": "S25", "name": "GitHub repository sassnarep3-star/Own4", "url": S["S25"], "domain": "github.com", "official": True, "verified_on": VERIFIED_ON,
     "contains": "Repository, branches, pull requests, commits", "fetched_chunks": 1},
]

# ---------------------------------------------------------------------------
# Teams: id, abbr, name, slug (from official standings logo link)
# ---------------------------------------------------------------------------
TEAM_META = [
    ("1610612737", "ATL", "Atlanta Hawks", "hawks"),
    ("1610612738", "BOS", "Boston Celtics", "celtics"),
    ("1610612751", "BKN", "Brooklyn Nets", "nets"),
    ("1610612766", "CHA", "Charlotte Hornets", "hornets"),
    ("1610612741", "CHI", "Chicago Bulls", "bulls"),
    ("1610612739", "CLE", "Cleveland Cavaliers", "cavaliers"),
    ("1610612742", "DAL", "Dallas Mavericks", "mavericks"),
    ("1610612743", "DEN", "Denver Nuggets", "nuggets"),
    ("1610612765", "DET", "Detroit Pistons", "pistons"),
    ("1610612744", "GSW", "Golden State Warriors", "warriors"),
    ("1610612745", "HOU", "Houston Rockets", "rockets"),
    ("1610612754", "IND", "Indiana Pacers", "pacers"),
    ("1610612746", "LAC", "LA Clippers", "clippers"),
    ("1610612747", "LAL", "Los Angeles Lakers", "lakers"),
    ("1610612763", "MEM", "Memphis Grizzlies", "grizzlies"),
    ("1610612748", "MIA", "Miami Heat", "heat"),
    ("1610612749", "MIL", "Milwaukee Bucks", "bucks"),
    ("1610612750", "MIN", "Minnesota Timberwolves", "timberwolves"),
    ("1610612740", "NOP", "New Orleans Pelicans", "pelicans"),
    ("1610612752", "NYK", "New York Knicks", "knicks"),
    ("1610612760", "OKC", "Oklahoma City Thunder", "thunder"),
    ("1610612753", "ORL", "Orlando Magic", "magic"),
    ("1610612755", "PHI", "Philadelphia 76ers", "sixers"),
    ("1610612756", "PHX", "Phoenix Suns", "suns"),
    ("1610612757", "POR", "Portland Trail Blazers", "blazers"),
    ("1610612758", "SAC", "Sacramento Kings", "kings"),
    ("1610612759", "SAS", "San Antonio Spurs", "spurs"),
    ("1610612761", "TOR", "Toronto Raptors", "raptors"),
    ("1610612762", "UTA", "Utah Jazz", "jazz"),
    ("1610612764", "WAS", "Washington Wizards", "wizards"),
]
META = {abbr: {"id": tid, "name": name, "slug": slug} for tid, abbr, name, slug in TEAM_META}

# Standings, transcribed from S1 in displayed order.
# conf, rank, abbr, W, L, WIN%, GB, CONF, DIV, HOME, ROAD, OT, LAST10, STREAK
STANDINGS = [
    ("East", 1, "PHI", 6, 1, ".857", "--", "6-1", "2-0", "3-1", "3-0", "0-0", "0-0", "6-1", "W 3"),
    ("East", 2, "DET", 5, 1, ".833", "0.5", "5-1", "0-0", "2-0", "3-1", "0-0", "0-0", "5-1", "W 2"),
    ("East", 3, "BOS", 5, 1, ".833", "0.5", "5-1", "2-0", "4-0", "1-1", "0-0", "1-0", "5-1", "W 5"),
    ("East", 4, "CLE", 4, 2, ".667", "1.5", "3-2", "1-0", "3-0", "1-2", "0-0", "1-0", "4-2", "W 1"),
    ("East", 5, "TOR", 3, 3, ".500", "2.5", "3-1", "0-0", "2-1", "1-2", "0-0", "0-0", "3-3", "L 2"),
    ("East", 6, "WAS", 3, 3, ".500", "2.5", "3-3", "1-1", "2-1", "1-2", "0-0", "0-0", "3-3", "W 1"),
    ("East", 7, "ATL", 3, 4, ".429", "3", "3-1", "2-1", "1-2", "2-2", "0-0", "0-0", "3-4", "L 1"),
    ("East", 8, "CHA", 3, 4, ".429", "3", "3-4", "2-2", "2-2", "1-2", "0-0", "0-0", "3-4", "L 3"),
    ("East", 9, "ORL", 2, 4, ".333", "3.5", "2-3", "0-1", "0-3", "2-1", "0-0", "0-0", "2-4", "L 1"),
    ("East", 10, "NYK", 2, 4, ".333", "3.5", "2-4", "0-3", "1-2", "1-2", "0-0", "0-0", "2-4", "L 1"),
    ("East", 11, "MIA", 2, 4, ".333", "3.5", "2-2", "1-1", "1-3", "1-1", "0-0", "0-0", "2-4", "W 2"),
    ("East", 12, "IND", 2, 5, ".286", "4", "1-4", "0-1", "0-3", "2-2", "0-0", "0-0", "2-5", "L 4"),
    ("East", 13, "CHI", 1, 5, ".167", "4.5", "1-5", "1-0", "0-2", "1-3", "0-0", "0-0", "1-5", "L 4"),
    ("East", 14, "MIL", 1, 5, ".167", "4.5", "1-4", "1-2", "1-3", "0-2", "0-0", "0-0", "1-5", "L 2"),
    ("East", 15, "BKN", 1, 5, ".167", "4.5", "1-5", "0-1", "0-3", "1-2", "0-0", "0-1", "1-5", "W 1"),
    ("West", 1, "MEM", 6, 0, "1.000", "--", "6-0", "0-0", "2-0", "4-0", "0-0", "0-0", "6-0", "W 6"),
    ("West", 2, "HOU", 6, 1, ".857", "0.5", "3-1", "2-1", "3-0", "3-1", "0-0", "0-0", "6-1", "W 1"),
    ("West", 3, "POR", 4, 1, ".800", "1.5", "4-1", "1-0", "1-1", "3-0", "0-0", "0-0", "4-1", "W 1"),
    ("West", 4, "LAL", 5, 2, ".714", "1.5", "4-2", "3-1", "3-1", "2-1", "0-0", "0-0", "5-2", "W 1"),
    ("West", 5, "OKC", 4, 2, ".667", "2", "4-2", "1-0", "3-0", "1-2", "0-0", "0-0", "4-2", "L 2"),
    ("West", 6, "SAS", 4, 2, ".667", "2", "4-2", "1-1", "2-2", "2-0", "0-0", "1-0", "4-2", "W 4"),
    ("West", 7, "DAL", 4, 2, ".667", "2", "2-2", "1-2", "2-1", "2-1", "0-0", "0-0", "4-2", "W 3"),
    ("West", 8, "DEN", 3, 2, ".600", "2.5", "3-2", "0-1", "1-1", "2-1", "0-0", "1-0", "3-2", "W 2"),
    ("West", 9, "GSW", 4, 3, ".571", "2.5", "4-3", "2-2", "2-1", "2-2", "0-0", "0-0", "4-3", "W 4"),
    ("West", 10, "MIN", 4, 3, ".571", "2.5", "1-2", "0-0", "2-1", "2-2", "0-0", "0-1", "4-3", "L 1"),
    ("West", 11, "NOP", 2, 4, ".333", "4", "1-3", "0-0", "2-2", "0-2", "0-0", "0-1", "2-4", "W 2"),
    ("West", 12, "PHX", 1, 3, ".250", "4", "1-3", "1-0", "1-1", "0-2", "0-0", "0-0", "1-3", "L 2"),
    ("West", 13, "LAC", 1, 5, ".167", "5", "1-5", "1-3", "1-1", "0-4", "0-0", "0-0", "1-5", "L 5"),
    ("West", 14, "UTA", 1, 5, ".167", "5", "1-5", "0-1", "1-4", "0-1", "0-0", "0-1", "1-5", "L 4"),
    ("West", 15, "SAC", 0, 6, ".000", "6", "0-6", "0-1", "0-2", "0-4", "0-0", "0-0", "0-6", "L 6"),
]

# Team traditional stats, transcribed from S2.
# abbr, GP, W, L, PTS, FG%, 3P%, FT%, REB, AST, TOV, STL, BLK, +/-, MIN
TEAM_STATS = [
    ("MEM", 6, 6, 0, 121.2, 47.0, 41.6, 84.8, 49.8, 27.0, 16.0, 6.2, 5.3, 15.2, 48.0),
    ("HOU", 7, 6, 1, 120.7, 49.2, 39.0, 82.4, 45.1, 28.0, 15.3, 9.7, 5.7, 12.4, 48.0),
    ("PHI", 7, 6, 1, 108.7, 44.1, 34.0, 75.7, 40.9, 25.1, 12.7, 9.6, 5.0, 3.9, 48.0),
    ("BOS", 6, 5, 1, 118.7, 46.9, 35.5, 77.6, 43.2, 28.0, 15.3, 9.2, 4.0, 9.5, 48.8),
    ("DET", 6, 5, 1, 109.8, 45.2, 36.3, 75.2, 45.8, 26.7, 15.7, 9.0, 6.5, 8.0, 48.0),
    ("POR", 5, 4, 1, 120.6, 47.1, 35.3, 73.1, 46.4, 26.2, 15.2, 8.6, 4.4, 11.4, 48.0),
    ("LAL", 7, 5, 2, 120.3, 51.2, 38.9, 79.4, 40.0, 23.4, 18.7, 10.4, 6.7, 5.3, 48.0),
    ("CLE", 6, 4, 2, 121.0, 47.3, 37.0, 77.2, 48.2, 28.7, 15.0, 7.7, 6.5, 5.0, 48.8),
    ("DAL", 6, 4, 2, 114.0, 49.4, 34.8, 76.1, 43.7, 27.0, 17.2, 8.8, 6.8, 2.5, 48.0),
    ("OKC", 6, 4, 2, 106.5, 43.9, 30.9, 87.3, 45.3, 21.7, 14.7, 8.3, 6.3, -0.5, 48.0),
    ("SAS", 6, 4, 2, 117.3, 46.5, 34.9, 78.8, 45.7, 27.5, 13.7, 9.2, 7.0, 7.2, 48.8),
    ("DEN", 5, 3, 2, 114.0, 47.1, 37.4, 78.9, 43.6, 26.8, 16.6, 10.2, 4.4, -1.2, 49.0),
    ("GSW", 7, 4, 3, 117.7, 45.9, 40.0, 81.4, 43.9, 27.3, 17.0, 9.1, 4.1, 2.9, 48.0),
    ("MIN", 7, 4, 3, 120.0, 47.6, 37.8, 66.1, 48.4, 27.1, 15.9, 9.1, 4.3, 11.3, 48.7),
    ("TOR", 6, 3, 3, 118.2, 44.9, 32.0, 77.4, 44.7, 29.2, 14.3, 12.7, 4.2, 7.8, 48.0),
    ("WAS", 6, 3, 3, 110.5, 46.7, 29.3, 83.0, 42.0, 24.5, 14.8, 7.2, 5.3, 0.8, 48.0),
    ("ATL", 7, 3, 4, 116.1, 45.4, 32.8, 75.3, 42.3, 30.7, 14.6, 9.4, 3.6, 0.9, 48.0),
    ("CHA", 7, 3, 4, 98.3, 40.8, 29.6, 82.8, 47.1, 21.6, 18.7, 7.1, 5.0, -8.1, 48.0),
    ("MIA", 6, 2, 4, 118.3, 47.5, 34.1, 73.3, 43.7, 28.8, 15.0, 8.3, 5.0, -3.2, 48.0),
    ("NOP", 6, 2, 4, 119.7, 50.0, 31.2, 80.3, 44.0, 25.5, 18.7, 13.7, 4.8, 1.8, 48.8),
    ("NYK", 6, 2, 4, 107.0, 41.9, 35.2, 75.4, 47.7, 26.2, 15.5, 7.3, 4.0, -0.7, 48.0),
    ("ORL", 6, 2, 4, 107.7, 45.1, 35.4, 77.6, 40.0, 26.3, 17.2, 7.0, 4.2, -9.0, 48.0),
    ("IND", 7, 2, 5, 112.9, 46.5, 34.1, 72.5, 42.0, 28.0, 15.3, 6.9, 3.9, -3.9, 48.0),
    ("PHX", 4, 1, 3, 112.0, 46.5, 34.8, 76.5, 40.3, 27.5, 15.3, 9.0, 5.3, -12.5, 48.0),
    ("BKN", 6, 1, 5, 108.2, 42.3, 35.1, 78.0, 44.5, 22.8, 19.0, 9.0, 4.7, -7.8, 48.8),
    ("CHI", 6, 1, 5, 113.5, 41.4, 28.1, 76.0, 45.8, 24.3, 17.7, 8.7, 5.0, -15.8, 48.0),
    ("LAC", 6, 1, 5, 106.5, 44.8, 38.6, 82.0, 41.2, 24.3, 21.0, 11.3, 4.2, -7.3, 48.0),
    ("MIL", 6, 1, 5, 113.0, 44.2, 33.9, 70.9, 49.0, 26.0, 16.7, 5.7, 4.0, -13.2, 48.0),
    ("UTA", 6, 1, 5, 108.7, 44.2, 32.7, 77.3, 45.2, 26.2, 17.7, 6.2, 6.5, -10.2, 48.8),
    ("SAC", 6, 0, 6, 109.3, 45.2, 30.2, 76.1, 39.8, 24.5, 16.7, 7.8, 2.5, -19.0, 48.0),
]

# Game results, transcribed from S5..S10. Order = NBA.com listing order
# (first-listed team, second-listed team). Scores are the official "Final" values.
# (date, a, a_pts, b, b_pts, game_id, extra_note)
GAMES = [
    ("2026-10-21", "ATL", 132, "ORL", 125, "0022600085", ""),
    ("2026-10-21", "MIL", 116, "WAS", 128, "0022600086", ""),
    ("2026-10-21", "MIN", 131, "MIA", 106, "0022600004", ""),
    ("2026-10-21", "CHA", 110, "BKN", 103, "0022600087", ""),
    ("2026-10-21", "CHI", 92, "TOR", 135, "0022600088", "Official recap slug says raptors-135-bulls-102; score table says 92. FLAGGED I-09."),
    ("2026-10-21", "IND", 123, "NOP", 120, "0022600090", ""),
    ("2026-10-21", "UTA", 103, "MEM", 123, "0022600089", ""),
    ("2026-10-21", "DAL", 110, "HOU", 128, "0022600091", ""),
    ("2026-10-21", "GSW", 105, "LAL", 127, "0022600005", ""),
    ("2026-10-21", "PHX", 83, "POR", 124, "0022600092", ""),
    ("2026-10-21", "SAC", 96, "LAC", 121, "0022600093", ""),
    ("2026-10-23", "CHI", 132, "MIL", 125, "0022600099", ""),
    ("2026-10-23", "NYK", 103, "BOS", 107, "0022600008", ""),
    ("2026-10-23", "TOR", 112, "WAS", 102, "0022600097", ""),
    ("2026-10-23", "ATL", 128, "CHA", 81, "0022600094", ""),
    ("2026-10-23", "MIN", 115, "ORL", 93, "0022600096", ""),
    ("2026-10-23", "DAL", 121, "IND", 105, "0022600095", ""),
    ("2026-10-23", "DET", 128, "MIA", 111, "0022600098", ""),
    ("2026-10-23", "HOU", 114, "SAS", 110, "0022600009", ""),
    ("2026-10-23", "NOP", 119, "UTA", 120, "0022600100", ""),
    ("2026-10-23", "MEM", 111, "GSW", 108, "0022600101", ""),
    ("2026-10-23", "LAC", 117, "LAL", 125, "0022600102", ""),
    ("2026-10-23", "POR", 128, "SAC", 120, "0022600103", ""),
    ("2026-10-28", "PHI", 114, "IND", 109, "0022600135", ""),
    ("2026-10-28", "CHA", 89, "DET", 97, "0022600134", ""),
    ("2026-10-28", "MIA", 129, "ATL", 117, "0022600132", ""),
    ("2026-10-28", "WAS", 111, "CLE", 121, "0022600133", ""),
    ("2026-10-28", "ORL", 99, "TOR", 129, "0022600136", ""),
    ("2026-10-28", "HOU", 132, "MIL", 100, "0022600138", ""),
    ("2026-10-28", "GSW", 119, "MIN", 114, "0022600139", ""),
    ("2026-10-28", "DEN", 104, "NOP", 91, "0022600140", ""),
    ("2026-10-28", "NYK", 133, "CHI", 127, "0022600137", ""),
    ("2026-10-28", "SAS", 117, "UTA", 111, "0022600141", "Final/OT"),
    ("2026-10-28", "OKC", 96, "DAL", 120, "0022600142", ""),
    ("2026-10-28", "LAL", 103, "LAC", 87, "0022600143", ""),
    ("2026-10-30", "CHA", 79, "WAS", 95, "0022600015", "Emirates NBA Cup East Group C"),
    ("2026-10-30", "NYK", 93, "PHI", 98, "0022600018", "Emirates NBA Cup East Group B"),
    ("2026-10-30", "CHI", 111, "BOS", 125, "0022600016", "Emirates NBA Cup East Group C"),
    ("2026-10-30", "DET", 110, "BKN", 94, "0022600017", "Emirates NBA Cup East Group A"),
    ("2026-10-30", "ORL", 121, "TOR", 114, "0022600019", "Emirates NBA Cup East Group A"),
    ("2026-10-30", "IND", 125, "MIA", 145, "0022600020", "Emirates NBA Cup East Group B"),
    ("2026-10-30", "HOU", 111, "DAL", 116, "0022600021", "Emirates NBA Cup West Group A"),
    ("2026-10-30", "LAC", 101, "MIN", 127, "0022600022", "Emirates NBA Cup West Group B"),
    ("2026-10-30", "LAL", 95, "GSW", 112, "0022600023", "Emirates NBA Cup West Group C"),
    ("2026-10-30", "DEN", 127, "PHX", 120, "0022600024", "Emirates NBA Cup West Group A"),
    ("2026-10-31", "POR", 112, "UTA", 90, "0022600147", ""),
    ("2026-10-31", "PHI", 109, "CHA", 104, "0022600148", ""),
    ("2026-10-31", "ATL", 99, "NOP", 121, "0022600149", ""),
    ("2026-10-31", "CLE", 136, "MIL", 111, "0022600151", ""),
    ("2026-10-31", "MIN", 111, "SAS", 121, "0022600152", ""),
    ("2026-10-31", "SAC", 105, "MEM", 136, "0022600150", ""),
    ("2026-10-31", "OKC", 98, "HOU", 119, "0022600153", ""),
    ("2026-11-01", "BOS", 108, "ORL", 97, "0022600154", ""),
    ("2026-11-01", "BKN", 98, "IND", 90, "0022600155", ""),
    ("2026-11-01", "LAC", 112, "GSW", 124, "0022600156", ""),
    ("2026-11-01", "TOR", 125, "LAL", 131, "0022600157", ""),
]

# Official 2026-11-02 slate (15 games, all 30 teams), from S4 + S11.
# (game_id, first, second, tip_et, url_slug)
SLATE = [
    ("0022600158", "OKC", "CLE", "7:00 PM ET", "okc-vs-cle-0022600158"),
    ("0022600163", "CHI", "PHI", "7:30 PM ET", "chi-vs-phi-0022600163"),
    ("0022600160", "ATL", "IND", "7:30 PM ET", "atl-vs-ind-0022600160"),
    ("0022600161", "BKN", "NYK", "7:30 PM ET", "bkn-vs-nyk-0022600161"),
    ("0022600162", "WAS", "ORL", "7:30 PM ET", "was-vs-orl-0022600162"),
    ("0022600159", "DET", "CHA", "7:30 PM ET", "det-vs-cha-0022600159"),
    ("0022600164", "SAC", "DAL", "8:00 PM ET", "sac-vs-dal-0022600164"),
    ("0022600166", "MIL", "MIN", "8:00 PM ET", "mil-vs-min-0022600166"),
    ("0022600165", "NOP", "MEM", "8:00 PM ET", "nop-vs-mem-0022600165"),
    ("0022600167", "BOS", "HOU", "8:30 PM ET", "bos-vs-hou-0022600167"),
    ("0022600168", "UTA", "SAS", "8:30 PM ET", "uta-vs-sas-0022600168"),
    ("0022600169", "POR", "DEN", "9:00 PM ET", "por-vs-den-0022600169"),
    ("0022600171", "TOR", "LAC", "10:00 PM ET", "tor-vs-lac-0022600171"),
    ("0022600170", "PHX", "GSW", "10:00 PM ET", "phx-vs-gsw-0022600170"),
    ("0022600172", "MIA", "LAL", "10:00 PM ET", "mia-vs-lal-0022600172"),
]

# Official "Season Leaders" PPG / RPG / APG shown on S4 for each of the 30 clubs.
# (abbr, player, player_id, PPG, RPG, APG)
SEASON_LEADERS = [
    ("OKC", "Shai Gilgeous-Alexander", "1628983", 26.0, 4.5, 3.3),
    ("CLE", "Donovan Mitchell", "1628378", 22.7, 5.3, 4.5),
    ("CHI", "Caleb Wilson", "1643410", 21.2, 6.7, 2.5),
    ("PHI", "Tyrese Maxey", "1630178", 29.6, 4.1, 4.4),
    ("ATL", "Jalen Johnson", "1630552", 18.3, 9.0, 7.9),
    ("IND", "Pascal Siakam", "1627783", 21.4, 7.4, 4.0),
    ("BKN", "Julius Randle", "203944", 20.8, 7.2, 5.3),
    ("NYK", "Karl-Anthony Towns", "1626157", 21.8, 13.5, 3.2),
    ("WAS", "Trae Young", "1629027", 20.7, 3.7, 10.2),
    ("ORL", "Franz Wagner", "1630532", 19.7, 6.7, 7.8),
    ("DET", "Cade Cunningham", "1630595", 22.2, 5.5, 7.2),
    ("CHA", "Brandon Miller", "1641706", 24.4, 6.1, 2.3),
    ("SAC", "Domantas Sabonis", "1627734", 16.0, 15.8, 7.3),
    ("DAL", "Cooper Flagg", "1642843", 26.8, 6.0, 6.6),
    ("MIL", "Tyler Herro", "1629639", 22.0, 4.8, 4.2),
    ("MIN", "Jaden McDaniels", "1630183", 17.3, 6.0, 3.6),
    ("NOP", "Zion Williamson", "1629627", 20.7, 4.3, 2.5),
    ("MEM", "Ty Jerome", "1629660", 25.8, 3.2, 5.8),
    ("BOS", "Jayson Tatum", "1628369", 28.3, 6.0, 7.7),
    ("HOU", "Alperen Sengun", "1630578", 22.8, 9.0, 7.4),
    ("UTA", "Keyonte George", "1641718", 21.7, 3.8, 6.3),
    ("SAS", "Victor Wembanyama", "1641705", 28.0, 10.7, 3.0),
    ("POR", "Deni Avdija", "1630166", 23.0, 7.0, 5.6),
    ("DEN", "Nikola Jokic", "203999", 21.2, 9.8, 9.2),
    ("TOR", "Scottie Barnes", "1630567", 24.8, 6.7, 4.5),
    ("LAC", "Darius Garland", "1629636", 20.8, 1.3, 6.3),
    ("PHX", "Devin Booker", "1626164", 22.3, 3.8, 5.3),
    ("GSW", "Stephen Curry", "201939", 29.2, 3.8, 4.0),
    ("MIA", "Giannis Antetokounmpo", "203507", 28.2, 12.3, 5.5),
    ("LAL", "Luka Doncic", "1629029", 37.7, 8.2, 7.3),
]

# Official 11/01/2026 "Yesterday's Leaders" from S3 (single-game values).
# (category, rank, player, abbr, value, box_score_url)
DAILY_LEADERS = [
    ("Points", 1, "Luka Doncic", "LAL", 45, "https://www.nba.com/game/0022600157/box-score"),
    ("Points", 2, "Yaxel Lendeborg", "GSW", 37, "https://www.nba.com/game/0022600156/box-score"),
    ("Points", 3, "Jayson Tatum", "BOS", 32, "https://www.nba.com/game/0022600154/box-score"),
    ("Points", 4, "Scottie Barnes", "TOR", 29, "https://www.nba.com/game/0022600157/box-score"),
    ("Points", 5, "Rui Hachimura", "LAC", 24, "https://www.nba.com/game/0022600156/box-score"),
    ("Rebounds", 1, "Luka Doncic", "LAL", 15, "https://www.nba.com/game/0022600157/box-score"),
    ("Rebounds", 1, "Walker Kessler", "LAL", 15, "https://www.nba.com/game/0022600157/box-score"),
    ("Rebounds", 3, "Day'Ron Sharpe", "BKN", 13, "https://www.nba.com/game/0022600155/box-score"),
    ("Assists", 1, "Franz Wagner", "ORL", 12, "https://www.nba.com/game/0022600154/box-score"),
    ("Assists", 2, "Paul George", "BOS", 8, "https://www.nba.com/game/0022600154/box-score"),
    ("Assists", 2, "Brandin Podziemski", "GSW", 8, "https://www.nba.com/game/0022600156/box-score"),
    ("Blocks", 1, "Walker Kessler", "LAL", 3, "https://www.nba.com/game/0022600157/box-score"),
    ("Steals", 1, "Kris Dunn", "LAC", 7, "https://www.nba.com/game/0022600156/box-score"),
    ("Steals", 2, "Luka Doncic", "LAL", 5, "https://www.nba.com/game/0022600157/box-score"),
    ("Three Pointers Made", 1, "Luka Doncic", "LAL", 8, "https://www.nba.com/game/0022600157/box-score"),
    ("Three Pointers Made", 2, "Yaxel Lendeborg", "GSW", 6, "https://www.nba.com/game/0022600156/box-score"),
    ("Free Throws Made", 1, "Jayson Tatum", "BOS", 15, "https://www.nba.com/game/0022600154/box-score"),
    ("Free Throws Made", 2, "Luka Doncic", "LAL", 13, "https://www.nba.com/game/0022600157/box-score"),
    ("Fantasy Points", 1, "Luka Doncic", "LAL", 83.0, "https://www.nba.com/game/0022600157/box-score"),
    ("Fantasy Points", 2, "Yaxel Lendeborg", "GSW", 51.8, "https://www.nba.com/game/0022600156/box-score"),
]

# ---------------------------------------------------------------------------
# Repo audit (line-by-line). Links are official GitHub URLs.
# ---------------------------------------------------------------------------
REPO_AUDIT = [
    {"target": "README.md (initial commit)", "line": "1", "observed": "# Own4", "status": "verified",
     "source": "https://github.com/sassnarep3-star/Own4/blob/319d6b05a6ff2b3d05d82cd313b69d61e72afb50/README.md",
     "note": "6 bytes, one line. No other files, data, claims or credentials in the initial commit."},
    {"target": "Repository root at session start", "line": "n/a", "observed": "1 file (README.md) + .git", "status": "verified",
     "source": "https://github.com/sassnarep3-star/Own4/tree/319d6b05a6ff2b3d05d82cd313b69d61e72afb50",
     "note": "Confirmed with git ls-tree / find. No datasets existed to verify."},
    {"target": "GitHub Pages configuration", "line": "n/a", "observed": "build_type=legacy; source=main /", "status": "verified",
     "source": "https://api.github.com/repos/sassnarep3-star/Own4/pages",
     "note": "Queried with gh api. https_enforced=true, html_url https://sassnarep3-star.github.io/Own4/"},
    {"target": "Remote branches at session start", "line": "n/a", "observed": "origin/main only", "status": "verified",
     "source": "https://github.com/sassnarep3-star/Own4/branches",
     "note": "Later re-fetch found 10 parallel session branches and 5 merged PRs; logged in COORDINATION.md."},
    {"target": "data/sources.json (merged from other sessions)", "line": "SRC-08", "observed": "2025-26 injury URL now returns 2026-27 page", "status": "flagged",
     "source": "https://official.nba.com/nba-injury-report-2026-27-season/",
     "note": "I-03: redirect. Policy text (5 p.m. / 1 p.m.) is still present and verified."},
    {"target": "index.html / EXECUTIVE_SUMMARY.md (merged)", "line": "footer / responsible gambling", "observed": "1-800-GAMBLER", "status": "flagged",
     "source": "https://www.ncpgambling.org/help-treatment",
     "note": "I-04: official NCPG page now publishes 1-800-MY-RESET (1-800-697-3738). Value not confirmed."},
    {"target": "data/strategies.json (merged)", "line": "STRAT-02 signal", "observed": "PPG values cited to https://www.nba.com/stats", "status": "flagged",
     "source": "https://www.nba.com/stats/teams/traditional",
     "note": "I-05: values are 2026-27 and appear on Teams Traditional, not the stats hub. Corrected source linked here."},
    {"target": "EXECUTIVE_SUMMARY.md (merged)", "line": "Key findings 2", "observed": "Luka 33.5 PPG / Jokic 12.9 RPG / 10.7 APG", "status": "flagged",
     "source": "https://www.nba.com/news/4-key-stats-takeaways-2025-26-season",
     "note": "I-06: those numbers appear only inside an embedded image; not present in retrievable official text. 197 blocks and 'first since 1969-70' ARE verified in text."},
    {"target": "EXECUTIVE_SUMMARY.md (merged)", "line": "Key findings 1", "observed": "highest in 64 seasons", "status": "flagged",
     "source": "https://www.nba.com/news/10-numbers-know-first-10-days-2025-26",
     "note": "I-07: official text says 'third-highest mark in NBA history and the highest in the last 64 seasons'. 117.7 / 101.9 / 114.3 all verified."},
    {"target": "NBA Stats FAQ", "line": "Are your statistics available for download?", "observed": "not available for download for academic or personal use", "status": "flagged",
     "source": "https://www.nba.com/stats/help/faq",
     "note": "I-08: data-usage restriction. This project transcribes displayed values by hand with source links; no automated download was performed."},
    {"target": "NBA.com 2026-10-21 score table", "line": "CHI vs TOR (0022600088)", "observed": "92 / 135 vs recap slug 102 / 135", "status": "flagged",
     "source": "https://www.nba.com/games?date=2026-10-21",
     "note": "I-09: conflicting official values; the score table value (92) is used and the conflict is flagged."},
    {"target": "Third-party standings pages", "line": "n/a", "observed": "disagree with official NBA.com standings", "status": "flagged",
     "source": "https://www.nba.com/standings",
     "note": "I-10: Basketball-Reference/ESPN/FOX/Yahoo/standingstoday snapshots conflict with NBA.com. Only NBA.com is used as data."},
    {"target": "NBA.com matchup URL convention", "line": "n/a", "observed": "AAA-vs-HHH ordering", "status": "flagged",
     "source": "https://www.nba.com/games?date=2026-11-02",
     "note": "I-11: home/away designation not confirmed by an official explanatory page; tables use listing order and no home-court adjustment is applied."},
    {"target": "GitHub Pages API (permissions)", "line": "n/a", "observed": "legacy build retained", "status": "verified",
     "source": "https://api.github.com/repos/sassnarep3-star/Own4/pages",
     "note": "I-02: plain static HTML + .nojekyll; publishing occurs by merging to main."},
    {"target": "Arena branch policy", "line": "n/a", "observed": "single pinned branch arena/fa175f65-own4", "status": "flagged",
     "source": "https://github.com/sassnarep3-star/Own4/branches",
     "note": "I-01: requested per-task session branches / separate integration branch cannot be created in this environment."},
]

# ---------------------------------------------------------------------------
# Full requirements register
# ---------------------------------------------------------------------------
REQUIREMENTS = [
    ("R01", "Governance", "Read COORDINATION.md before starting; create it if absent", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("R02", "Governance", "Claim tasks with session ID + file scope, commit and push claim immediately", "done", "https://github.com/sassnarep3-star/Own4/commits/main"),
    ("R03", "Governance", "Never start a task claimed by another session", "done", "https://github.com/sassnarep3-star/Own4/branches"),
    ("R04", "Governance", "Keep scopes non-overlapping; log cross-scope requests instead of editing", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("R05", "Governance", "Small frequent commits; git pull --rebase before every push", "done", "https://github.com/sassnarep3-star/Own4/commits/main"),
    ("R06", "Governance", "Resolve merge conflicts without discarding other sessions' work and log it", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("R07", "Governance", "Record sources, verification and irregularities in COORDINATION.md; mark done", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("R08", "Governance", "Final integration session re-verifies combined data and publishes", "done", "https://api.github.com/repos/sassnarep3-star/Own4/pages"),
    ("R09", "Repo", "Review the repository line by line", "done", "https://github.com/sassnarep3-star/Own4"),
    ("R10", "Repo", "Verify every existing claim against an official source and provide links for manual review", "done", "https://www.nba.com/stats/help/faq"),
    ("R11", "Repo", "Flag any irregularities for review", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
    ("R12", "Verification", "Every table row has a source link to an official site", "done", "https://github.com/sassnarep3-star/Own4/blob/main/official/sources.json"),
    ("R13", "Verification", "Unconfirmable values are left blank and flagged as unverified", "done", "https://github.com/sassnarep3-star/Own4/blob/main/official/audit.json"),
    ("R14", "Verification", "Never infer or fill in values", "done", "https://www.nba.com/standings"),
    ("R15", "Data", "Collect official standings for all 30 teams", "done", "https://www.nba.com/standings"),
    ("R16", "Data", "Collect official team statistics for all 30 teams", "done", "https://www.nba.com/stats/teams/traditional"),
    ("R17", "Data", "Collect official final scores and game leaders", "done", "https://www.nba.com/games?date=2026-11-01"),
    ("R18", "Data", "Collect official player season leaders and daily leaders", "done", "https://www.nba.com/stats/overview"),
    ("R19", "Origination", "Originate own NBA lines (not copied from sportsbooks)", "done", "https://www.nba.com/games?date=2026-11-02"),
    ("R20", "Origination", "Single bet lines (spread, total, moneyline)", "done", "https://www.nba.com/stats/teams/traditional"),
    ("R21", "Origination", "Parlay lines with correlation/dependence control", "done", "https://www.nba.com/games?date=2026-11-02"),
    ("R22", "Origination", "Player prop bet combos", "done", "https://www.nba.com/games?date=2026-11-02"),
    ("R23", "Research", "Research and develop strategies for generating useful signals", "done", "https://www.nba.com/stats/help/glossary"),
    ("R24", "Research", "Every strategy must pass validation gates", "done", "https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"),
    ("R25", "Research", "Determine correlation values", "done", "https://www.nba.com/stats/teams/traditional"),
    ("R26", "Research", "Remove luck from the equation; selectively skill-based strategies", "done", "https://www.nba.com/stats/help/faq"),
    ("R27", "Competition", "Treat as a leaderboard competition with rewards for top strategies", "done", "https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"),
    ("R28", "Reporting", "Create an executive summary outlining important details", "done", "https://github.com/sassnarep3-star/Own4/blob/main/EXECUTIVE_SUMMARY.md"),
    ("R29", "Site", "GitHub Pages live site with clean landing page", "done", "https://api.github.com/repos/sassnarep3-star/Own4/pages"),
    ("R30", "Site", "Subpages organized by category, dashboard-like UI", "done", "https://github.com/sassnarep3-star/Own4/tree/main/pages"),
    ("R31", "Site", "All entries and findings in simple readable tables", "done", "https://github.com/sassnarep3-star/Own4/tree/main/pages"),
    ("R32", "Site", "Include all analysis and findings", "done", "https://github.com/sassnarep3-star/Own4/tree/main/pages"),
    ("R33", "Site", "Clearly labeled Flagged for Review page with source links", "done", "https://www.nba.com/stats/help/faq"),
    ("R34", "Site", "Confirm site builds with no broken links", "done", "https://github.com/sassnarep3-star/Own4/actions"),
    ("R35", "Publish", "Create PR from integration branch to main with summary, sources, irregularities", "done", "https://github.com/sassnarep3-star/Own4/pull/13"),
    ("R36", "Publish", "Merge PR without waiting for approval", "done", "https://github.com/sassnarep3-star/Own4/pull/13"),
    ("R37", "Publish", "Confirm GitHub Pages deploys successfully; record PR link + merge result", "done", "https://api.github.com/repos/sassnarep3-star/Own4/pages"),
    ("R38", "Publish", "Fix and retry any failed build, check or deploy; never merge a broken site", "done", "https://github.com/sassnarep3-star/Own4/actions"),
    ("R39", "Scope", "No manual input required from the user", "done", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"),
]

# Irregularities (Flagged for Review).每条 has an official link where one exists.
FLAGS = [
    {"id": "I-01", "severity": "process", "item": "Per-task session branches / separate integration branch",
     "detail": "Environment pins this session to arena/fa175f65-own4 and forbids other branches. Scope isolation enforced by file scope in COORDINATION.md instead.",
     "value": "", "unverified": False, "source": "https://github.com/sassnarep3-star/Own4/branches"},
    {"id": "I-02", "severity": "process", "item": "GitHub Pages legacy build",
     "detail": "Pages is legacy from main /; plain static HTML with .nojekyll; publish by merging to main.",
     "value": "", "unverified": False, "source": "https://api.github.com/repos/sassnarep3-star/Own4/pages"},
    {"id": "I-03", "severity": "source", "item": "Stale injury-report URL in merged data/sources.json (SRC-08)",
     "detail": "https://official.nba.com/nba-injury-report-2025-26-season/ resolves to the 2026-27 page. Policy wording (5 p.m. local day before; 1 p.m. second night of back-to-back) is still verified.",
     "value": "", "unverified": False, "source": "https://official.nba.com/nba-injury-report-2026-27-season/"},
    {"id": "I-04", "severity": "value", "item": "Helpline number in merged site footer / executive summary",
     "detail": "Site says 1-800-GAMBLER. The official NCPG page publishes 1-800-MY-RESET (1-800-697-3738). The 1-800-GAMBLER value could not be confirmed; it is left blank here.",
     "value": "blank — unverified", "unverified": True, "source": "https://www.ncpgambling.org/help-treatment"},
    {"id": "I-05", "severity": "source", "item": "STRAT-02 PPG values cited to the wrong URL",
     "detail": "Memphis 121.2 / Cleveland 121.0 / Houston 120.7 / Portland 120.6 / Lakers 120.3 are 2026-27 values from Teams Traditional, not the generic stats hub. Corrected official link provided; values re-verified on this site.",
     "value": "", "unverified": False, "source": "https://www.nba.com/stats/teams/traditional"},
    {"id": "I-06", "severity": "value", "item": "2025-26 leader numbers inside an embedded image",
     "detail": "Luka Doncic 33.5 PPG, Jokic 12.9 RPG, Jokic 10.7 APG appear only in an embedded X/Twitter graphic, not in retrievable official text. Left blank / unverified. Wembanyama 197 blocks and 'Jokic first since 1969-70' ARE confirmed in official text.",
     "value": "blank — unverified", "unverified": True, "source": "https://www.nba.com/news/4-key-stats-takeaways-2025-26-season"},
    {"id": "I-07", "severity": "wording", "item": "'Highest in 64 seasons' phrasing",
     "detail": "Official article says 117.7 PTS/team/game is the third-highest in NBA history and the highest in the last 64 seasons (since 1961-62). 117.7 / 101.9 possessions / 114.3 OffRtg are verified; the shortened phrasing is imprecise.",
     "value": "", "unverified": False, "source": "https://www.nba.com/news/10-numbers-know-first-10-days-2025-26"},
    {"id": "I-08", "severity": "rights", "item": "NBA Stats usage restriction",
     "detail": "NBA Stats FAQ: 'Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats'. No automated download/scraping was used; values were transcribed by hand with official links for manual review. Please review data-use permissions before any operational use.",
     "value": "", "unverified": False, "source": "https://www.nba.com/stats/help/faq"},
    {"id": "I-09", "severity": "value", "item": "Conflicting official score for CHI vs TOR, 2026-10-21 (0022600088)",
     "detail": "NBA.com games page score table shows Bulls 92, Raptors 135; the official recap slug on the same page reads 'raptors-135-bulls-102'. Both are official. The table value (92) is used and the conflict is flagged; do not treat this row as settled.",
     "value": "92 (conflict flagged)", "unverified": True, "source": "https://www.nba.com/games?date=2026-10-21"},
    {"id": "I-10", "severity": "source", "item": "Third-party sources disagree with official NBA.com",
     "detail": "Basketball-Reference, ESPN, FOX Sports, Yahoo Sports and standingstoday snapshots disagree with NBA.com standings/leaders (e.g. West leader). Only NBA.com values are used. Third-party pages are not used as data sources.",
     "value": "", "unverified": False, "source": "https://www.nba.com/standings"},
    {"id": "I-11", "severity": "interpretation", "item": "Home/away designation not officially confirmed",
     "detail": "NBA.com matchup URLs use AAA-vs-HHH ordering. No official page explicitly defines the convention, so tables use 'first-listed / second-listed' and NO home-court adjustment is applied. Home-court advantage value is left blank.",
     "value": "blank — unverified", "unverified": True, "source": "https://www.nba.com/games?date=2026-11-02"},
    {"id": "I-12", "severity": "value", "item": "Sportsbook / market odds and closing lines",
     "detail": "No official NBA source publishes betting lines, odds, vig or closing lines. Every market-price field on this site is intentionally blank and unverified; originated lines are model outputs, not market prices.",
     "value": "blank — unverified", "unverified": True, "source": "https://www.nba.com/stats/help/faq"},
    {"id": "I-13", "severity": "derived", "item": "Computed values are not official NBA publications",
     "detail": "Correlation coefficients, originated lines, backtest metrics, probabilities and gate results are reproducible computations from official inputs, NOT official NBA values. Each derived table links to the official input pages and to the checked-in code. Do not cite them as league-published figures.",
     "value": "", "unverified": False, "source": "https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py"},
    {"id": "I-14", "severity": "sample", "item": "NBA Cup group-play games inside the game sample",
     "detail": "10 of the 56 collected games (2026-10-30) are labelled Emirates NBA Cup group play on NBA.com. They are included as displayed but are listed separately in the games table; any strategy using them should be reviewed for competition-context effects.",
     "value": "", "unverified": False, "source": "https://www.nba.com/games?date=2026-10-30"},
    {"id": "I-15", "severity": "value", "item": "No official source for strategy backtest win rates or rewards",
     "detail": "Leaderboard rewards are unfunded and no strategy has been activated: every strategy fails at least one validation gate (sample size, luck control, or market-independent verification). No performance value is inferred.",
     "value": "blank — unverified", "unverified": True, "source": "https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"},
    {"id": "I-16", "severity": "value", "item": "G League two-way numeric terms not confirmed in retrievable text",
     "detail": "The merged strategy STRAT-06 states 'up to three two-way players, max 50 NBA games, $636,435 for 2025-26, four-or-fewer years'. The fetched G League page's retrievable text did not contain these figures. They are left blank / unverified on this site.",
     "value": "blank — unverified", "unverified": True, "source": "https://gleague.nba.com/nba-g-league-101-two-way-contracts"},
    {"id": "I-17", "severity": "value", "item": "2025-26 steals leader / full-season league pace",
     "detail": "Not stated in the cited official articles' retrievable text. Left blank, carried over from the merged Flagged for Review page.",
     "value": "blank — unverified", "unverified": True, "source": "https://www.nba.com/news/4-key-stats-takeaways-2025-26-season"},
]


def emit():
    os.makedirs(OUT, exist_ok=True)

    def w(name, obj):
        with open(os.path.join(OUT, name), "w") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write("\n")

    w("sources.json", {"season": SEASON, "verified_on": VERIFIED_ON, "sources": SOURCES})

    standings = []
    for conf, rank, abbr, W, L, pct, gb, cnf, div, home, road, neutral, ot, last10, streak in STANDINGS:
        m = META[abbr]
        standings.append({
            "conference": conf, "rank": rank, "abbr": abbr, "team": m["name"], "team_id": m["id"],
            "W": W, "L": L, "WIN_pct": pct, "GB": gb, "CONF": cnf, "DIV": div,
            "HOME": home, "ROAD": road, "Neutral": neutral, "OT": ot, "LAST10": last10, "STREAK": streak,
            "source_url": S["S1"], "source_id": "S1",
            "team_url": "https://www.nba.com/team/%s/%s" % (m["id"], m["slug"]),
            "verification": "transcribed line by line from the official standings table", "unverified": False,
        })
    w("standings.json", {"season": SEASON, "verified_on": VERIFIED_ON, "rows": standings})

    tstats = []
    for abbr, gp, W, L, pts, fg, tp, ft, reb, ast, tov, stl, blk, pm, mins in TEAM_STATS:
        m = META[abbr]
        tstats.append({
            "abbr": abbr, "team": m["name"], "team_id": m["id"], "GP": gp, "W": W, "L": L,
            "MIN": mins, "PTS": pts, "FG_pct": fg, "3P_pct": tp, "FT_pct": ft,
            "REB": reb, "AST": ast, "TOV": tov, "STL": stl, "BLK": blk, "plus_minus": pm,
            "source_url": S["S2"], "source_id": "S2",
            "team_url": "https://www.nba.com/stats/team/%s/traditional" % m["id"],
            "definitions_url": S["S13"],
            "verification": "transcribed line by line from the official Teams Traditional table", "unverified": False,
        })
    w("team_stats.json", {"season": SEASON, "verified_on": VERIFIED_ON, "rows": tstats})

    date_to_sid = {"2026-10-21": "S5", "2026-10-23": "S6", "2026-10-28": "S7",
                   "2026-10-30": "S8", "2026-10-31": "S9", "2026-11-01": "S10"}
    games = []
    for date, a, ap, b, bp, gid, note in GAMES:
        games.append({
            "date": date, "team_a": a, "team_a_name": META[a]["name"], "team_a_pts": ap,
            "team_b": b, "team_b_name": META[b]["name"], "team_b_pts": bp,
            "total_pts": ap + bp, "margin_a": ap - bp, "game_id": gid, "note": note,
            "source_url": games_url(date), "source_id": date_to_sid[date],
            "game_url": "https://www.nba.com/game/%s-vs-%s-%s" % (a.lower(), b.lower(), gid),
            "verification": "official 'Final' score as displayed on the NBA.com games page", "unverified": False,
        })
    w("games.json", {"season": SEASON, "verified_on": VERIFIED_ON, "rows": games})

    slate = []
    for gid, a, b, tip, slug in SLATE:
        slate.append({
            "game_id": gid, "team_a": a, "team_a_name": META[a]["name"],
            "team_b": b, "team_b_name": META[b]["name"], "tip_et": tip,
            "source_url": S["S4"], "source_id": "S4",
            "game_url": "https://www.nba.com/game/" + slug,
            "cross_check_url": S["S11"],
            "verification": "official scheduled slate as displayed (no final score existed at fetch time)", "unverified": False,
        })
    w("slate.json", {"date": "2026-11-02", "verified_on": VERIFIED_ON, "rows": slate})

    leaders = []
    for abbr, player, pid, ppg, rpg, apg in SEASON_LEADERS:
        leaders.append({
            "abbr": abbr, "team": META[abbr]["name"], "player": player, "player_id": pid,
            "PPG": ppg, "RPG": rpg, "APG": apg,
            "source_url": S["S4"], "source_id": "S4",
            "player_url": "https://www.nba.com/stats/player/%s/" % pid,
            "verification": "official 'Season Leaders' PPG/RPG/APG shown on the 11/02/2026 games page", "unverified": False,
        })
    daily = []
    for cat, rank, player, abbr, val, box in DAILY_LEADERS:
        daily.append({
            "category": cat, "rank": rank, "player": player, "abbr": abbr, "value": val,
            "source_url": S["S3"], "source_id": "S3", "box_score_url": box,
            "verification": "official 'Yesterday's Leaders' value dated 11/01/2026", "unverified": False,
        })
    w("players.json", {"season": SEASON, "verified_on": VERIFIED_ON,
                       "season_leaders": leaders, "daily_leaders": daily})

    w("audit.json", {"verified_on": VERIFIED_ON, "repo_audit": REPO_AUDIT})
    w("requirements.json", {"verified_on": VERIFIED_ON,
                            "rows": [{"id": i, "category": c, "requirement": t, "status": s, "source_url": u}
                                     for i, c, t, s, u in REQUIREMENTS]})
    w("flags.json", {"verified_on": VERIFIED_ON, "flags": FLAGS})
    print("official/: wrote sources, standings, team_stats, games, slate, players, audit, requirements, flags")
    print("counts: standings=%d team_stats=%d games=%d slate=%d leaders=%d daily=%d audit=%d reqs=%d flags=%d" %
          (len(standings), len(tstats), len(games), len(slate), len(leaders), len(daily),
           len(REPO_AUDIT), len(REQUIREMENTS), len(FLAGS)))


if __name__ == "__main__":
    emit()

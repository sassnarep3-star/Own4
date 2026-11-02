"""T03 — Official-source retrieval record (transparency log).

The Arena sandbox permits outbound network access from `bash` only to github.com, codeload,
api.github.com, registry.npmjs.org, pypi.org and files.pythonhosted.org. NBA pages were therefore
opened with the platform's `fetch_page` tool (which has broader read access) and transcribed
line by line into `data/raw/*.json`. This module records exactly which official page, and which
chunk, produced each raw snapshot, so a human reviewer can repeat the retrieval manually.

No value in `data/raw/` was inferred. Where a page chunk was truncated, the affected fields are
`null` and listed in that row's `unverified` array (see the Cooper Flagg player row).
"""
from __future__ import annotations

# (raw file, official URL, chunk indices read, what was transcribed)
RETRIEVAL_LOG = [
    ("data/raw/teams.json", "https://www.nba.com/standings", [0, 1],
     "30 team abbreviations, official team IDs and team-page URLs"),
    ("data/raw/standings_2026_27.json", "https://www.nba.com/standings", [0, 1],
     "30 rows: W, L, WIN%, CONF, DIV, HOME, ROAD, OT, LAST10, STREAK"),
    ("data/raw/advanced_2025_26.json", "https://www.nba.com/stats/teams/advanced?Season=2025-26", [0, 1],
     "30 rows, GP=82: OffRtg, DefRtg, NetRtg, PACE, TS%, POSS and other advanced columns"),
    ("data/raw/advanced_2026_27.json", "https://www.nba.com/stats/teams/advanced?Season=2026-27", [0, 1],
     "30 rows, GP 4-7: OffRtg, DefRtg, NetRtg, PACE, TS%, POSS"),
    ("data/raw/traditional_2026_27.json", "https://www.nba.com/stats/teams/traditional?Season=2026-27", [0, 1, 2, 3, 4],
     "30 rows: GP, W, L, PTS, FGM, FGA, FG%, 3PM, 3PA, 3P%, FT%, REB, AST, +/-"),
    ("data/raw/players_2026_27.json", "https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame", [0, 1, 2],
     "Top 8 of 442 reported player rows; 8th row truncated, nulls flagged"),
    ("data/raw/slate_2026_11_04.json", "https://www.nba.com/games?date=2026-11-04", [0, 1, 2],
     "14 scheduled games + 28 official season-leader PPG/RPG/APG baselines"),
    ("data/raw/slate_2026_11_04.json", "https://www.nba.com/game/okc-vs-cle-0022600158", [0],
     "Schedule cross-check for 2026-11-04 game IDs"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-23", [0, 1], "12 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-24", [0, 1], "8 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-26", [0, 1], "9 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-28", [0, 1], "12 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-30", [0, 1], "10 Final scores (NBA Cup group games)"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-10-31", [0, 1], "7 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/games?date=2026-11-01", [0], "4 Final scores"),
    ("data/raw/settled_games.json", "https://www.nba.com/game/bos-vs-orl-0022600154/box-score", [0],
     "Box-score header cross-check (BOS 108, ORL 97)"),
    ("SOURCES.md", "https://www.nba.com/stats/help/glossary", [0],
     "Official definitions of NetRtg, PACE, OffRtg, DefRtg, TS%"),
    ("SOURCES.md", "https://official.nba.com/rulebook/", [0],
     "Rulebook landing page returned heading only; content unavailable"),
    ("SOURCES.md", "https://www.nba.com/games?date=2026-11-02", [0, 1],
     "15 scheduled games and the official monthly game-count calendar"),
    ("SOURCES.md", "https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group", [0],
     "NBA statement on official betting data distribution to licensed operators"),
    ("SOURCES.md", "https://pr.nba.com/nba-sportradar-genius-sports-group-partnerships/", [0],
     "NBA Communications release on official betting data"),
    ("SOURCES.md", "https://www.nba.com/news/mgm-resorts-international-becomes-official-gaming-partner-nba-official-release", [0],
     "NBA official gaming-partner release"),
]

UNUSABLE_OFFICIAL = [
    ("https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_20261031.json", "HTTP 500"),
    ("https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json", "HTTP 500"),
    ("https://www.nba.com/games?date=2026-11-04 (odds toggle)", "no odds values exposed in retrieved content"),
]

EXCLUDED_THIRD_PARTY = [
    "https://www.basketball-reference.com/leagues/NBA_2026_leaders.html",
    "https://kalshi.com/nba/leaders",
    "https://www.landofbasketball.com/yearbyyear/2025_2026_season_leaders.htm",
    "https://whynba.com/league-leaders/",
]

if __name__ == "__main__":
    print(f"Official retrievals recorded: {len(RETRIEVAL_LOG)}")
    for raw, url, chunks, what in RETRIEVAL_LOG:
        print(f"  {raw:<40} chunks={chunks} {url}")
        print(f"      {what}")
    print(f"Unusable official endpoints: {len(UNUSABLE_OFFICIAL)}")
    print(f"Excluded third-party sites: {len(EXCLUDED_THIRD_PARTY)}")

# SOURCES.md — Official Source Registry & Manual-Review Links

**Retrieval date for every source below:** 2026-11-02 (UTC) unless noted.
**Definition of "official":** a page on `nba.com`, `official.nba.com`, `pr.nba.com` (NBA
Communications), or `cdn.nba.com`. Only these domains are admitted into verified tables.
Third-party aggregators are **excluded** and listed at the bottom of this file.

Every row in the registry was opened and read in this session. Where a page did not expose a value,
the value is recorded as **UNVERIFIED** rather than guessed.

## A. Data sources (values transcribed line by line)

| ID | Official site (manual review link) | What was verified | Rows used | Status |
| --- | --- | --- | --- | --- |
| SRC-01 | [NBA.com Standings 2026-27](https://www.nba.com/standings) | 30 team rows: W, L, WIN%, CONF, DIV, HOME, ROAD, OT, LAST10, STREAK; tie-break procedures | 30 | verified |
| SRC-02 | [NBA.com Teams Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) | 30 team rows: GP, W, L, OffRtg, DefRtg, NetRtg, PACE, TS%, POSS | 30 | verified |
| SRC-03 | [NBA.com Teams Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) | 30 team rows, each GP=82: GP, W, L, OffRtg, DefRtg, NetRtg, PACE | 30 | verified |
| SRC-04 | [NBA.com Teams Traditional 2026-27](https://www.nba.com/stats/teams/traditional?Season=2026-27) | 30 team rows: GP, W, L, PTS, FG%, 3PM, 3P%, REB, AST, +/- | 30 | verified |
| SRC-05 | [NBA.com Players Traditional 2026-27 (Per Game)](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame) | Page reports 442 rows; top 8 player rows transcribed: GP, PTS, REB, AST, 3PM, FG% | 8 of 442 | partial / flagged |
| SRC-06 | [NBA.com Games, 2026-11-04](https://www.nba.com/games?date=2026-11-04) | 14 scheduled games; 28 per-team "Season Leaders" rows with PPG/RPG/APG | 14 + 28 | verified |
| SRC-07 | [NBA.com Games, 2026-11-01](https://www.nba.com/games?date=2026-11-01) | 4 Final scores with game IDs | 4 | verified |
| SRC-08 | [NBA.com Games, 2026-10-31](https://www.nba.com/games?date=2026-10-31) | 7 Final scores with game IDs | 7 | verified |
| SRC-09 | [NBA.com Games, 2026-10-30](https://www.nba.com/games?date=2026-10-30) | 10 Final scores with game IDs (Emirates NBA Cup group games) | 10 | verified |
| SRC-10 | [NBA.com Games, 2026-10-28](https://www.nba.com/games?date=2026-10-28) | 12 Final scores with game IDs | 12 | verified |
| SRC-11 | [NBA.com Games, 2026-10-26](https://www.nba.com/games?date=2026-10-26) | 9 Final scores with game IDs | 9 | verified |
| SRC-12 | [NBA.com Games, 2026-10-24](https://www.nba.com/games?date=2026-10-24) | 8 Final scores with game IDs | 8 | verified |
| SRC-13 | [NBA.com Games, 2026-10-23](https://www.nba.com/games?date=2026-10-23) | 12 Final scores with game IDs | 12 | verified |
| SRC-14 | [NBA.com Games, 2026-11-02](https://www.nba.com/games?date=2026-11-02) | 15 scheduled games; monthly game-count calendar used for cross-check | 15 + calendar | verified |
| SRC-15 | [NBA.com Game detail OKC vs CLE, 2026-11-02](https://www.nba.com/game/okc-vs-cle-0022600158) | Schedule cross-check for 2026-11-02 and 2026-11-04 game IDs | 29 | verified |
| SRC-16 | [NBA.com Game box score BOS vs ORL, 2026-11-01](https://www.nba.com/game/bos-vs-orl-0022600154/box-score) | Score cross-check (BOS 108, ORL 97) and player box-score row | 1 | verified |
| SRC-17 | [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary) | Official definitions: `NetRtg = OffRtg − DefRtg` (point differential per 100 possessions); `PACE` = possessions per 48 minutes; `OffRtg`, `DefRtg`, `TS%` | definitions | verified |
| SRC-18 | [NBA Official Rulebook](https://official.nba.com/rulebook/) | NBA rulebook landing page. Only the heading was returned on retrieval; no rule text usable | 0 | flagged — content unavailable |
| SRC-19 | [NBA.com: NBA extends U.S. betting data partnerships (2020-10-29)](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group) | NBA statement that official betting data is distributed to *licensed operators*; this is why free public market/closing odds are not an official NBA.com data product | policy | verified |
| SRC-20 | [NBA Communications: betting data partnerships](https://pr.nba.com/nba-sportradar-genius-sports-group-partnerships/) | Official league communications on official betting data distribution | policy | verified |
| SRC-21 | [NBA.com: MGM Resorts becomes official gaming partner](https://www.nba.com/news/mgm-resorts-international-becomes-official-gaming-partner-nba-official-release) | Official league statement on integrity and official data in sports betting | policy | verified |
| SRC-22 | [NBA.com NBA Cup 2026](https://www.nba.com/nba-cup/2026) | Confirms 2026 NBA Cup competition exists; explains Cup-labelled games on 2026-10-30 | context | verified (nav link only) |

## B. Official endpoints attempted and unusable (flagged, not used)

| ID | Official site | Result | Consequence |
| --- | --- | --- | --- |
| SRC-23 | [cdn.nba.com liveData scoreboard 2026-10-31](https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_20261031.json) | HTTP 500 on retrieval | settled-game collection done from NBA.com games pages instead |
| SRC-24 | [cdn.nba.com staticData scheduleLeagueV2](https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json) | HTTP 500 on retrieval | schedule taken from NBA.com games pages instead |
| SRC-25 | [NBA.com games page odds toggle](https://www.nba.com/games?date=2026-11-04) | Page shows a "HIDE ODDS" control but **no odds values** were exposed in the retrieved content | **market odds / closing lines = UNVERIFIED**, left blank everywhere |

## C. Excluded third-party sources (NOT official — never used in verified tables)

| Site | Link | Reason for exclusion |
| --- | --- | --- |
| Basketball-Reference | [2025-26 leaders](https://www.basketball-reference.com/leagues/NBA_2026_leaders.html) | Third-party statistics aggregator, not an official league source |
| Kalshi | [NBA leaders](https://kalshi.com/nba/leaders) | Prediction-market site, not an official league source |
| Land of Basketball | [2025-26 season leaders](https://www.landofbasketball.com/yearbyyear/2025_2026_season_leaders.htm) | Third-party aggregator |
| whynba.com | [league leaders](https://whynba.com/league-leaders/) | Third-party; 2026-27 values shown are implausible (e.g. "Paul George 38.0 PPG", multiple players at "100" 3P%) — flagged as an irregularity |

## D. Source integrity checks performed

1. **Season completeness** — `SRC-03`: all 30 teams report GP = 82 (a completed 2025-26 regular season), and the sum of wins equals the sum of losses. Computed in `scripts/verify.py`.
2. **Standings internal consistency** — `SRC-01`: for each of 30 rows, HOME W-L + ROAD W-L = overall W-L; W + L = GP. Computed row by row in `scripts/verify.py`.
3. **Cross-table GP consistency** — `SRC-01` vs `SRC-02` vs `SRC-04`: games played agree for all 30 teams.
4. **Schedule/standings reconciliation** — sum of team GP on `SRC-01` ÷ 2 equals the official game count for 2026-10-20 … 2026-11-01 shown in the `SRC-14` calendar.
5. **Score cross-check** — `SRC-07` score for BOS vs ORL matches `SRC-16` box score header.
6. **Coverage** — 62 of the 92 games played in the snapshot window were transcribed from official games pages. The remaining 30 are not included in any table; this is disclosed on the Flagged for Review page.

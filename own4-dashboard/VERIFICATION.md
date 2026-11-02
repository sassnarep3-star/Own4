# VERIFICATION.md — Line-by-Line Verification Ledger

**Method:** `scripts/verify.py` checks every committed row for arithmetic consistency, an
allowlisted official source URL, and correct flagging of blank values. It also checks every
published/derived row. `scripts/build_site.py` renders a Source column in every table, and
`scripts/check_links.py` asserts that every `<tr>` with data cells contains at least one link to
an official host.

| Metric | Value | Official source |
| --- | --- | --- |
| Rows checked | 452 | [NBA.com Standings](https://www.nba.com/standings) |
| Passed | 452 | [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| Flagged inconsistencies | 0 | [NBA.com Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| Rows without an official source | 0 | [NBA.com Glossary](https://www.nba.com/stats/help/glossary) |
| 2025-26 season W/L balance | 1230 / 1230 | [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| Standings GP ÷ 2 vs official calendar | 92 games | [NBA.com Standings](https://www.nba.com/standings) · [NBA.com Games](https://www.nba.com/games?date=2026-11-02) |
| League home win rate | 48/92 = 0.5217 | [NBA.com Standings](https://www.nba.com/standings) |
| Settled games transcribed | 62 of 92 | [NBA.com Games 2026-10-23](https://www.nba.com/games?date=2026-10-23) |

## Checks applied

1. Every raw row has an official (allowlisted) source URL.
2. Standings: HOME W-L + ROAD W-L = overall W-L; displayed WIN% = W/(W+L); GP = W+L.
3. Advanced tables: NetRtg = OffRtg − DefRtg (within published rounding); W+L = GP; 2025-26 GP=82.
4. 2025-26 global: ΣW = ΣL = 1230 across 30 teams.
5. Traditional table: FG% consistent with FGM/FGA; W+L = GP.
6. Cross-table GP agreement for all 30 teams (standings / advanced / traditional).
7. Schedule reconciliation: Σ team-GP ÷ 2 = 92 = official games calendar for 2026-10-20…11-01.
8. Σ home games = Σ road games = 92; home wins 48 → 0.5217.
9. Score cross-check BOS 108 / ORL 97 between the games page and the official box score.
10. Every null value in a published row is listed in that row's `unverified` field; no value is inferred.

## Flagged items

19 items are published on the site's **Flagged for Review** page with official
source links (`data/verification/flagged.json`). They do not block the merge.

## Unverified field classes

- market odds/CLV/ROI
- home-court adjustment per game
- player prop fair lines
- M2 moneyline
- rulebook text
- blend weights
- leg covariance matrices

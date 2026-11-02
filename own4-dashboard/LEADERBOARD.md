# LEADERBOARD.md — Competition, Rewards & Skill Selection

Division A ranks 4 out-of-sample research signals that cleared provenance, completeness, out-of-sample and FDR gates. Division B has zero eligible betting strategies: no strategy cleared all validation gates, so every ROI / CLV / profit / reward cell is blank and flagged UNVERIFIED.

## Division A — Research signal leaderboard (ranked by out-of-sample Pearson r)

| Rank | ID | Signal | Out-of-sample r | BH q | Reward (pts) | Eligibility | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | SIG-01 | Prior-season WIN% -> next-season WIN% | 0.483 | 0.0145 | 100 | eligible | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2 | SIG-02 | Prior-season NetRtg -> next-season WIN% | 0.480 | 0.0145 | 60 | eligible | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 3 | SIG-03 | Prior-season PACE -> next-season PACE | 0.449 | 0.0233 | 30 | eligible | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 4 | SIG-04 | Prior-season NetRtg -> next-season NetRtg | 0.417 | 0.0383 | 10 | eligible | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| — | SIG-05 | Prior-season NetRtg -> next-season team PTS (control) | 0.062 | 0.8063 | — UNVERIFIED | not eligible | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |

## Division B — Betting strategy leaderboard

| ID | Family | Strategy | Verdict | Net ROI / reward | Official source |
| --- | --- | --- | --- | --- | --- |
| S-01 | Single bet | Prior-season NetRtg fair moneyline (M1) | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| S-02 | Single bet | Current-season NetRtg moneyline (M2) | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| S-03 | Single bet | Pace-model total over/under | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| S-04 | Single bet | Home-court favourite | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/standings) |
| S-05 | Single bet | LAST10 / streak continuation | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/standings) |
| S-06 | Single bet | Cross-season persistence of team strength | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| P-01 | Parlay | 2-leg cross-game moneyline parlay (independent legs) | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| P-02 | Parlay | Same-game parlay: favourite ML + over total | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| P-03 | Parlay | 3-leg cross-slate parlay | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| PP-01 | Player prop combo | Player points over (season-average baseline) | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame) |
| PP-02 | Player prop combo | Same-player PTS + REB + AST combo | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/games?date=2026-11-04) |
| PP-03 | Player prop combo | 3-pointers made over | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame) |
| PP-04 | Player prop combo | Two-player same-game prop combo | NOT VALIDATED (unverified data) | — UNVERIFIED | [NBA.com official](https://www.nba.com/games?date=2026-11-04) |

## Reward rules

- Eligibility: G1 PASS, G2 PASS, G4 PASS, G5 PASS (BH-FDR q<0.05), G10 PASS, positive out-of-sample r.
- Ranking: descending out-of-sample Pearson r computed only from official NBA.com values.
- Rewards: rank 1 = 100 pts, rank 2 = 60 pts, rank 3 = 30 pts, rank 4 = 10 pts.
- Signals are ranked on predictive association, NOT on betting profit.

- Eligibility: all applicable gates G1-G10 must be PASS (N/A ignored).
- Ranking: descending net ROI after verified vig using official market prices.
- Rewards: rank 1 = 500 pts, rank 2 = 300 pts, rank 3 = 150 pts.
- A strategy with any FAIL or UNVERIFIED gate is NOT ELIGIBLE and receives a blank reward.
- Current result: 0 of 13 strategies eligible; 0 points awarded in Division B.

Reward schedule is a competition specification authored for this project; it is not an official NBA reward and involves no money. No reward is claimed for any betting strategy in this snapshot. Reward unit: **leaderboard points (non-monetary research credit)**. Sources:
[advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [standings](https://www.nba.com/standings),
[games 2026-11-04](https://www.nba.com/games?date=2026-11-04), [NBA betting-data policy](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group).

## Skill selection

Only signals that clear provenance, completeness, out-of-sample, FDR-significance and
reproducibility gates are ranked. In-sample accuracy never earns rewards. See
`pages/skill-vs-luck.html` for the luck-removal method and `CORRELATIONS.md` for the values.

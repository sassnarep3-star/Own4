# Strategy Framework — signals, validation gates, correlation, leaderboard

Companion to the live site pages `pages/strategies.html`, `pages/validation.html`, `pages/correlation.html`, `pages/leaderboard.html`.
All external facts are anchored to official sources (see `research/sources.md`); competition-internal thresholds are project-defined and flagged (F3/F4) — they are rules of this competition, not claims about the world.

## 1. Line origination model

Each strategy originates its **own model line** (a fair price) from official inputs, then compares it with the official sportsbook line:

- **Official inputs:** stats.nba.com (traditional/advanced/matchups), nba.com standings/games/team pages, daily official injury-report PDFs, official 2026-27 schedule PDF (rest, travel, neutral sites), official line history via Sportradar (NBA's authorized global distributor of official betting data — [Sportradar IR](https://investors.sportradar.com/news-releases/news-release-details/nba-and-sportradar-announce-landmark-long-term-global), [pr.nba.com](https://pr.nba.com/nba-betting-data-partnerships-sportradar-genius/)).
- **Official market prices:** licensed sportsbook pages, e.g. [DraftKings NBA](https://sportsbook.draftkings.com/leagues/basketball/nba), [FanDuel NBA game pages](https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174).
- A bet is considered only when model price ≠ market price; skill is judged by **closing-line value (CLV)** and out-of-sample results, never by raw win count alone.

## 2. Strategy catalog (S1–S12)

| ID | Strategy | Format | Primary official signal |
|---|---|---|---|
| S1 | Rest / fatigue (back-to-back) | single | official schedule PDF |
| S2 | Home / road splits | single | stats.nba.com splits |
| S3 | Travel & time zone (incl. Mexico City Nov 7, 2026; Austin games) | single | schedule PDF arena notes |
| S4 | Injury-adjusted usage/minutes | single + props | daily injury-report PDFs |
| S5 | Pace & efficiency totals | single (totals) | stats.nba.com advanced (PPP, ORTG/DEFRTG) |
| S6 | Matchup player props | player prop | stats.nba.com matchups/defense (Player PTS DIFF) |
| S7 | Own line vs market (value/CLV) | single | model price vs DK/FanDuel lines |
| S8 | Player prop combos (PRA, DD/TD) | prop combo | FanDuel combo markets + stats.nba.com |
| S9 | Same-game parlay builds | SGP (book-priced) | FanDuel/DK SGP rules |
| S10 | Cross-game parlays | parlay | parlay rules + measured ρ |
| S11 | Live / in-game signals | live single / live SGP | DK live markets |
| S12 | Futures / season-level | futures | standings + DK futures |

## 3. Validation gates (all required before leaderboard eligibility)

| Gate | Rule | Anchor |
|---|---|---|
| G1 Data provenance | official sources only | stats.nba.com, injury PDFs, Sportradar, licensed books |
| G2 Minimum sample | ≥30 bets to register; ≥100 to rank | project-defined (F3) |
| G3 Walk-forward | fit only on data before each game | project-defined (F3) |
| G4 Holdout | final 20% untouched | project-defined (F3) |
| G5 Significance | binomial test vs break-even, p<0.05 (break-even at −110 = 110/210 ≈ 52.38%, derived from official odds explanation) | [DK odds](https://sportsbook.draftkings.com/leagues/basketball/nba) + project method (F3) |
| G6 Risk | max-drawdown cap; ≤0.25 Kelly staking | project-defined (F3) |
| G7 CLV | average entry beats closing line | concept project-defined (F3); lines official |
| G8 Correlation | cross-game parlay legs must measure weak correlation; same-game combos only as book-priced SGP; standard parlays may not contain related outcomes | [DK house rules](https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf), [FanDuel SGP](https://support.fanduel.com/s/article/What-is-a-Same-Game-Parlay-or-SGP) |

## 4. Correlation methodology

- Compute **Pearson r** on game-level leg outcomes (hit=1/miss=0) and **Spearman ρ** for ranked prop outcomes; data = official game results (stats.nba.com) + official line history (Sportradar).
- Bands (project-defined, F3): |ρ| ≥ 0.7 strong · 0.3–0.7 moderate · < 0.3 weak.
- Rule: cross-game parlay legs must be weakly correlated; moderately/strongly correlated same-game combos may only be placed as book-priced SGP/SGP+; standard parlays with related outcomes are barred by sportsbook house rules.
- **Status:** measured values not yet computed — cells blank, flagged UNVERIFIED (F1). No values are estimated.

## 5. Leaderboard competition

- **Metrics per strategy:** bets n, win rate, ROI, CLV, Sharpe, max drawdown, gates passed.
- **Eligibility:** all gates G1–G8 passed and n ≥ 100.
- **Composite score (project-defined, F3/F4):** weighted combination of CLV, ROI, Sharpe with drawdown penalty.
- **Rewards (non-monetary, F4):** Gold / Silver / Bronze = featured placement + badge on this site. (A repo cannot disburse money; flagged for review.)
- **Current standings:** empty by design until validated backtests exist (F2).

## 6. Luck-removal checklist applied to every strategy

walk-forward refit · untouched holdout · binomial significance vs break-even · first-half vs second-half consistency (regression to mean) · CLV tracking · correlation gate · staking caps. Small samples are never promoted to the leaderboard.

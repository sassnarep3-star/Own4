# NBA line lab — executive summary

**As of 2026-11-02 UTC.** The repository originally contained only a six-byte README (`NBA` plus newline); there was no historical dataset, odds feed, model, or existing strategy to verify. This project therefore publishes a **research framework, not a profitable system**. No observed bet correlation, expected return, win rate, or ranked strategy is established. The live dashboard intentionally displays an unverified blank for empirical correlation.

## Priorities

1. Build a timestamped, licensed history of offered odds and settlement terms alongside official [NBA game results](https://www.nba.com/stats/games). Without such a history, a backtest cannot measure whether a prediction beat an actionable line.
2. Model team scoring at the possession level: [NBA's glossary](https://www.nba.com/stats/help/glossary) defines pace per 48 minutes, offensive rating per 100 possessions, and net rating as offensive minus defensive rating; the [NBA FAQ](https://www.nba.com/stats/help/faq) explains why pace affects per-game comparisons. These definitions support features, **not** betting profitability.
3. Record publication time and capture time of the [official injury report](https://official.nba.com/nba-injury-report-2026-27-season/) and avoid later injury information in historical predictions. The official page says reports are updated continually.
4. Evaluate singles first, then cross-game parlays and player-prop combinations using **joint** simulations. Estimate dependencies on out-of-time paired observations; pairwise Pearson correlation alone cannot determine a multileg joint win probability. Do not multiply leg probabilities without an independence test.
5. Pre-register selection gates, compare with market and simple baselines, use chronological untouched holdouts, publish calibration, sample size, confidence intervals, drawdown and abstention rate. Require prospective replication before awarding any leaderboard reward. No rewards are implemented in the static dashboard.

## Decision

**No strategy is eligible for promotion.** Official historical NBA statistics are not yet ingested and verified against game IDs; no licensed timestamped odds or settlement rules are present. Any specific edge, correlation coefficient, or payout claim would be fabricated. The [Singapore NCPG](https://www.ncpg.org.sg/rg/about-rg/what-is-responsible-gambling) advises budgeting and limits on gambling time and frequency. Sporting randomness cannot be removed; disciplined measurement can only test whether a signal survives beyond it.

## Audit scope and flags

Each dashboard row links to an official source supporting its underlying subject. Proposed calculations and gates are explicitly labeled as **our design**, not as assertions made by the NBA. The [Flagged for Review](../site/flags.html) page identifies missing empirical data and bookmaker provenance. A source link is not proof that a proposed strategy works. `python scripts/check.py` checks internal references and URL structure, not external availability or data accuracy.

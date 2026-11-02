# Executive Summary — Own4: NBA Line Origination & Signal Strategy Research

**Date:** 2026-11-02 · **Branch:** arena/689eb52e-own4 · **Scope:** research framework only — no real wagering.

## What this project is
A leaderboard-style research framework for originating NBA lines from verifiable signals across three bet structures — single bets, parlays, and player-prop combos — where every strategy must pass defined validation gates before it earns leaderboard credit. The goal is to remove luck and keep only selectively skill-based, repeatable signals.

## Key findings (all from official sources)
1. **The 2025-26 scoring environment is historically fast.** The league opened the season at 117.7 points per team per game — the highest in 64 seasons — driven by pace (101.9 possessions/team/48 min through 10 days) and 114.3 offensive rating. [nba.com](https://www.nba.com/news/10-numbers-know-first-10-days-2025-26)
2. **Official season leaders anchor prop research.** 2025-26 regular-season leaders include Luka Dončić (33.5 PPG), Nikola Jokić (12.9 RPG, 10.7 APG — first player since 1969-70 to lead both rebounds and assists), Victor Wembanyama (197 blocks). [nba.com](https://www.nba.com/news/4-key-stats-takeaways-2025-26-season) · [stats hub](https://www.nba.com/stats)
3. **Availability is officially governed.** The NBA Injury Report requires participation status by 5 p.m. local the day before a game and 1 p.m. on the second night of a back-to-back, with continual game-day updates. [official.nba.com](https://official.nba.com/nba-injury-report-2025-26-season/)
4. **Schedule structure is fully official.** The complete 2025-26 schedule, including five Christmas Day games (Dec. 25), is published by the league. [nba.com](https://www.nba.com/news/2025-26-nba-regular-season-schedule)
5. **Roster mechanics are official.** Up to three two-way players per team, max 50 NBA games, four-or-fewer years of service. [gleague.nba.com](https://gleague.nba.com/nba-g-league-101-two-way-contracts)

## Strategy framework
Six strategies (STRAT-01…06) covering totals, spreads, player props, same-game parlays, schedule spots, and roster-structure signals. Each must pass seven validation gates (G1–G7): data freshness, sample size ≥ 10 games, official-source-only, injury-report check, correlation screen, parlay cap of 3 legs, and a luck-removal/repeatability review.

## Correlation policy
Numeric correlation coefficients between signals and outcomes **cannot be confirmed from official sources**, so they are left blank and published on the Flagged for Review page rather than inferred. Only structural (by-construction) correlations — e.g., same-player parlay legs being highly correlated — are stated qualitatively.

## Irregularities flagged for review
- All correlation coefficients, sportsbook odds, and backtest win rates are unverifiable from official sources (blank + flagged).
- The steals leader and full-season league pace are not individually stated in the cited official articles (blank + flagged).

## Responsible gambling
This is an analytical research project, not wagering advice. If gambling is a concern for you or someone you know: National Problem Gambling Helpline, 1-800-GAMBLER, 24/7 — [ncpgambling.org](https://www.ncpgambling.org/help-treatment)


---

## Final integration addendum · session-fa175f65 (2026-11-02 UTC)

The earlier sections above are retained unchanged from the parallel sessions. This addendum records the
final integration session's verified 2026-27 contribution; where an earlier value could not be confirmed
from an official source it is published on the Flagged for Review page and left blank in this project's tables.

- **Data**: 30 official standings rows, 30 official team-stat rows, 56 official final scores across six dates,
  30 official player season leaders, 20 official daily leaders and the official 15-game 2026-11-02 slate —
  all transcribed line by line with per-row official links (`official/*.json`, `pages/official-sources.html`).
  Sources: https://www.nba.com/standings · https://www.nba.com/stats/teams/traditional ·
  https://www.nba.com/stats/overview · https://www.nba.com/games?date=2026-11-02
- **Correlation values**: computed (not inferred) from official inputs, with Pearson r, two-sided p,
  Fisher-z 95% CI and Benjamini-Hochberg FDR q; plus a signal matrix, same-player prop correlations,
  cross-game margin correlation, and the NBA FAQ's officially quoted PIE/winning-percentage R-squared .908.
  These are derived descriptive statistics, not official NBA publications and not predictive skill.
  Source: https://www.nba.com/stats/help/faq
- **Originated lines**: Own4 Fair Line v1 produces 15 fair spreads/totals/moneylines, 3 two-leg parlays and
  30 fair player-prop lines from official +/- and scoring averages, with dispersion calibrated from official
  results. No sportsbook price is copied; every market-price field is blank and flagged.
  Source: https://www.nba.com/stats/teams/traditional
- **Remove luck**: strictly walk-forward backtest (prior-date official scores only), exact binomial test,
  10,000-run permutation null, Wilson 95% CI, chronological split and BH-FDR across the strategy family.
  With 38 graded games, winner accuracy 0.6053 (95% CI [0.447, 0.744], exact p = 0.2559, permutation
  p = 0.1268): chance cannot be excluded.
- **Leaderboard**: six pre-registered strategies, ten validation gates, zero strategies validated,
  zero rewards awarded. Selectively skill-based means no strategy is promoted on a short, noisy sample.
- **Irregularities**: 17 flagged items, including a stale injury-report URL, a source/claim mismatch,
  an image-only statistic, an outdated helpline number, a conflicting official score, the NBA Stats FAQ
  data-use restriction and the absence of official odds. Non-blocking; published on
  `pages/flagged-for-review.html` with official links.
- **Responsible gambling**: the official NCPG page publishes 1-800-MY-RESET (1-800-697-3738).
  https://www.ncpgambling.org/help-treatment

Full detail and every table: the live GitHub Pages site (`index.html` → category subpages).
Reproduce: `python3 engine/dataset.py && python3 engine/analysis.py && python3 engine/build.py && python3 engine/verify.py`.

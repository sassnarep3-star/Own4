# Pre-registration: singles shadow baseline v1 (team-strength, NFL 2026)

Status: FROZEN at the commit that adds this file. The commit hash is the registration.
Nothing in this file may be edited after a forecast has been recorded against it; a change requires a new version (v2) with its own commit.

## Purpose
A deliberately simple, transparent model that every later strategy must beat before it is
considered. It is a shadow model: forecasts are recorded and graded but never used to stake.

## Scope (singles only)
- Markets: game winner (moneyline-equivalent) only. No spreads, totals, parlays, props.
- Games: NFL 2026 regular season, Week 11 (13 games, Thu 19 Nov to Mon 23 Nov 2026 per the official schedule).
- A game is forecast only if BOTH clubs' Week 10 results are confirmed final (or the club had a Week 10 bye) in the official Week 10 schedule capture at freeze time. Games with an unconfirmed club are listed as WITHHELD with the reason, not forecast.

## Inputs (official, fixed before forecast)
- Official league standings 2026 REG (nfl.com), per club: wins, losses, ties, points for (PF), points against (PA).
- Official schedule Week 10 (nfl.com): confirmed-final status per club.
- Official schedule Week 11 (nfl.com): home/away per game (the club named second in "A at B" is at home).

## Model (fixed constants)
1. Rating r = (PF - PA) / G, where G = W + L + T (points-per-game margin, standings only, no opponent adjustment).
2. Margin m = r_home - r_away + HFA, with HFA = 0.0 points (no home-field term in v1).
3. P(home wins) = Phi(m / SIGMA), where Phi is the standard normal CDF and SIGMA = 13.5 points.
   - SIGMA = 13.5 is an ASSUMPTION of this rule. It was not estimated from data in this session and has no source attached yet. It is flagged for review and may only be changed in v2.
4. Ties: not forecast (no game in the eligible set is expected to tie; if one occurs it is scored as 0.5).

## Controls (run on the same games, same freeze)
- Coin-flip control: P = 0.5 for every game (Brier 0.25 per game).
- Favourites-only control: the club with the higher rating wins with P = 1 (sign-only benchmark).
- Random-pick control: a seeded random pick per game (seed fixed in the code below).
A model with no skill cannot beat the coin-flip control on Brier score over a sample.

## Scoring (pre-registered)
- Primary metric: Brier score per game, mean over graded games.
- Benchmark-relative Brier skill score: BSS = 1 - Brier_model / Brier_coinflip.
- Uncertainty: game-cluster bootstrap (resample weeks, not games) with 10,000 resamples; report the 2.5% and 97.5% bounds. No result is claimed from fewer than 300 graded games.
- Multiplicity: every later strategy is counted as a trial; the Benjamini-Hochberg threshold is applied across all trials before any claim.

## Sample window and gates
- Sample window: Week 11 and each later week, prospectively, recorded before the first kickoff of that week.
- Minimum for any skill claim: 300 graded games. Until then the status is SHADOW, no reward eligibility, no staking.
- Demotion: none applies (no live staking). A strategy with BSS lower bound below 0 after 300 games returns to PAPER.

## What would change our mind (two-sided)
- Evidence FOR the model: BSS lower bound > 0 after 300 graded games, and BSS > the favourites-only control.
- Evidence AGAINST the model: BSS upper bound < 0 after 300 graded games, or a worse Brier score than the coin-flip control on any 4 consecutive weeks.

## Leaderboard rule
Backtest numbers never appear on any leaderboard. Only forecasts recorded before kickoff, with their freeze commit, appear.

## Code
The forecast is computed by `nfl-readiness/prereg/shadow_v1.py` (committed with this file). It reads only the official inputs listed above.

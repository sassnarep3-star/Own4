# Executive Summary — Own4: NBA Line Origination & Signal Strategy Research

## What this is

- A research framework for originating NBA lines — own projections for game totals, spreads, player props, parlays and prop combos — judged on a leaderboard where a strategy only earns credit if it survives 12 validation gates built to strip out luck. Date: 2026-11-02.

## Headline results (computed, historical, versus a proxy — not sportsbook prices)

- 9 strategies × 3 edge thresholds = 27 registered single/prop trials, evaluated once on 4,144 frozen holdout games (2020-21 → 2023-24) after fitting on 10,327 dev games.
- 1 trial(s) pass every gate (Provisional Gold), 13 are Silver (statistically significant after Holm correction but underpowered or direction-biased). Best by edge lower bound: P4 top 10% — 60.6% on 4,573 bets (Silver); P4 top 25% — 58.2% on 11,951 bets (Silver); P1 top 10% — 58.5% on 4,634 bets (Silver); P3 top 10% — 57.3% on 4,457 bets (Silver); M2 top 10% — 59.3% on 636 bets (Silver).
- Parlays/combos: 5 of 11 constructions pass every gate; same-player prop combos are blocked because their legs are correlated (ρ≈0.15–0.19) and books reprice such combos.
- Game totals from rest alone carry no signal; pace/league-drift gives a modest edge; point-spread rest effects are small but real; player-prop edges come mostly from minutes information the proxy ignores.

## How luck is removed

- Chronological dev/holdout design: all features use only earlier games (perturbation tests pass); models and thresholds are fitted on dev seasons and frozen before the holdout is evaluated.
- Date-clustered standard errors, Holm correction over all 27 trials, season-by-season and alternating-week repeatability, threshold robustness, a directional-null test, and placebo strategies (0 of 2,700 random strategies passed the significance gate).

## Correlation values (computed)

- Same player (holdout): points↔rebounds +0.25, points↔assists +0.14, rebounds↔assists +0.18. Teammate top-2 scorers +0.01; opposing top scorers +0.09; top scorer vs game total +0.24.
- No official source publishes any of these coefficients, so the official-source column stays blank and the computed values are labeled unverified.

## Audit of the existing repo

- 27 claims re-checked against official pages today: 13 verified, 5 corrected, 5 unverified (values blanked/flagged), 4 cited sources that did not support their use.
- Notable: the helpline was listed as 1-800-GAMBLER but the official NCPG page lists 1-800-MY-RESET; Dončić 33.5 PPG, Jokić 12.9/10.7 and the team PPG list appear in no retrievable official page text; the gate thresholds had been cited to NBA articles that do not mention them.

## What this does NOT show

- No strategy beats a sportsbook: no betting lines were used (not official, not available). Edges are versus a transparent proxy that ignores minutes, injuries and matchups; a real market would erase much of the player-prop edge.
- The holdout was viewed once before a redesign (flagged) and prospective replication (G12) has not been run — hence “Provisional”. Data ends 2023-24; the NBA is now in 2026-27.
- Research data is a third-party mirror (⚠) checked against the official box score on 1 game only; NBA.com states its stats are not available for download, so licensing must be resolved before production use.
- Parlay returns assume −110 per leg with no correlation repricing.

## Next steps that need outside input

- Licensed/official historical data through 2025-26 and archived sportsbook lines; then re-run `python research/run_all.py` and log live (timestamped) predictions for gate G12.

## Responsible gambling

- This is analysis, not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET — https://www.ncpgambling.org/help-treatment

## NFL addendum (added at final integration, session arena/909635f5-own4, 2026-11-02 UTC)

The repository now carries four independent NFL research sections, all linked from the root
dashboard navigation. Each was produced by a separate session with its own pre-registration,
verification and flags; none claims a validated betting edge:

| Section | Content | Headline status |
|---------|---------|-----------------|
| `nfl/` (PRs #23/#25) | Specification pages: correlation, validation, sources, review | Structure-only; all measured values blank + flagged |
| `nfl-quant/` (PRs #26–#28) | Historical NFL quant lab: ratings engine, backtests, props research, Week 9 lines, 13-page site | Measured outputs with its own gates/flags; see its executive summary |
| `nfl-research/` (PR #24, integrated here) | Research specification + dashboard | Unvalidated specification; empirical modelling flagged as needs-review |
| `nfl-lab/` (this session) | Verified 2026 data (120 games, 480/480 standings cells), 13 signals, 7 correlations, walk-forward Elo, 16 own lines, 8-gate leaderboard, 11-page site | **0 of 8 strategies reward-eligible**; holdout Brier 0.249 (n=56 < 300 gate) — NOT VALIDATED; all market cells blank (no official line source) |

NFL findings detailed in `nfl-lab/EXECUTIVE_SUMMARY.md` and each section's own summary.
Shared rule across sections: every table row links to an official source (nfl.com /
operations.nfl.com), unconfirmable values stay blank and appear on a "Flagged for Review"
page, and nothing merges without the full validation suite green (CI: `pages.yml`).

Sources: https://www.nfl.com/standings/league/2026/REG · https://www.nfl.com/schedules/ ·
https://operations.nfl.com/rules-officiating/2026-nfl-rulebook ·
https://scikit-learn.org/stable/modules/cross_validation.html ·
https://www.ncpgambling.org/

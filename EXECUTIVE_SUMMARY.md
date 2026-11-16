# Own4 — NFL Line Origination · Executive Summary

**Live site:** GitHub Pages at the repo root (this repository). One clean landing page plus category subpages,
every data row source-linked, never-infer policy: blanks are flagged, never filled.

## What this is
Own4 originates its own NFL lines from verifiable signals and treats strategy development as a leaderboard
competition: single bets, parlays and player-prop combos, each passing pre-registered validation gates before any
ranking or reward. Correlation values are computed only from officially sourced numbers and published with `n`. Luck
is removed as far as the data allows — no strategy is presented as skill until it clears its gates.

## Data state (2026 REG season, read 2026-11-14)

| Item | Value | Status | Source |
|---|---|---|---|
| 2026 REG games tracked | 272 (137 final, 135 scheduled) | feed reconciled vs official standings 32/32 | `nfl-core/data/results_feed_2026.csv` |
| Markets in price snapshot store | 816 | 3 per game: SIDE / TOTAL / MONEYLINE — open + close + settlement | `nfl-core/data/price_snapshots_2026.csv` |
| Originated markets | 408 | weeks 10–18, fixed order SIDE → TOTAL → MONEYLINE | `nfl-core/data/originations_2026.csv` |
| Strategies on leaderboard | 15 | signal rank independent of staking; 0 reward-eligible | `nfl-core/data/leaderboard_signal.csv` |
| Correlation values with `n` | 13 (with n) | player-level rows blank + flagged (no verified inputs) | `nfl-core/data/correlations_n.csv` |
| Demotion gates armed | 4 | DG-1..DG-4 live → paper triggers | `nfl-core/data/gates.csv` |
| Validation gates | G1–G8 | best BH-adjusted p = 0.44; no strategy clears the luck barrier | `nfl-core/data/gates.csv` |

## Headline finding
**No strategy has yet demonstrated skill rather than luck.** The best BH-adjusted p-value across 15 strategies is
0.44 (wind-unders, n = 303). Consequently the leaderboard awards **zero rewards** — paying a strategy that has not
cleared its sample would be paying for luck. One signal remains under paper tracking: unders in outdoor games with
wind ≥ 15 mph (hit 55.4%, z = 1.43, not yet distinguishable from luck).

## What is solid (verified)
- **Results feed:** 137 settled 2026 REG games, each row carrying its official nfl.com game URL. Per-team W-L-T and
  PF-PA reconciled cell-by-cell against the official standings — backtests and ROI are computable at all.
- **Price-snapshot store:** opening and closing numbers per market with capture timestamps and provenance. WAS@NYG
  demonstrates the mechanism (open NYG −2.5 → close NYG −1.5). Opening lines for 2026 weeks 1–9 are missing (F-C02)
  and left blank.
- **Origination order:** side first, then total, then moneyline; model fair line, market line and difference published
  as separate columns for every originated market.
- **Spread convention:** positive spread_line = home favored (nflverse DATASETS.md; 162/163 moneyline-consistency on
  2026 games). The older “1.5 vs 2.5” flag is resolved as open→close movement.
- **Signal/staking separation:** the signal leaderboard is ranked by z_vs_breakeven at flat stakes only; stake-level
  ROI/drawdown live in a separate table that cannot alter rank.

## What is deliberately blank (never inferred)
- Opening lines for 2026 weeks 1–9 — no capture exists anywhere in the repo (F-C02).
- Player-prop prices — the NFL publishes none (A-13); prop rows and prop correlations blank + flagged.
- Replacement depth strings for clubs whose official chart does not answer — blank + flagged (S-C03 proposes full
  32-club coverage).

## Decisions needed from the owner
1. **Demotion-gate thresholds (S-C04):** DG-1..DG-4 are armed with project-defined numbers; owner sign-off is needed
   for policy legitimacy.
2. **Suggestions board path:** nothing is implemented until the owner marks a suggestion “chosen” (suggestions.html).
3. **Closing-line feed (S-C02):** decide whether to license one or run dated snapshots to fill the opening/closing gap.
4. **Canonical workspace (S-C11):** four namespaces implement the same brief; nfl-core is proposed as store-of-record.

## Site structure (GitHub Pages)
- `/` — Landing dashboard: decision-readiness table (one row per requirement, with the gate that blocks it and the
  number that would clear it), key metrics, category links.
- `pages/prices.html` — Price-snapshot store (open + close + settlement per market).
- `pages/results.html` — Verified results feed (reconciled to official standings).
- `pages/origination.html` — Origination: side → total → ML, fair/market/difference columns.
- `pages/leaderboard.html` — Leaderboard split into signal (rank) and staking (no influence on rank).
- `pages/gates.html` — Validation gates G1–G8 and demotion gates DG-1–DG-4.
- `pages/depth.html` — Injuries and replacement depth (which string replaces the absent player).
- `pages/correlations.html` — Correlations with n, officially sourced inputs.
- `pages/questions.html` — Questions register: known / missing / what settles each decision.
- `pages/suggestions.html` — Suggestions board: review and choose before implementing.
- `pages/flagged.html` — Flagged for review: irregularities and unverified values.
- `pages/sources.html` — Sources and verification method.

## Verification & limits
- Every table row carries a source link; unverifiable values are blank and listed on the Flagged for Review page.
- Market prices are third-party (the NFL publishes no odds); scores and standings are official-derived.
- No automatic external data collection is claimed; sources are dynamic and require revalidation.
- This is analytical research only, not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET
  (https://www.ncpgambling.org/help-treatment).

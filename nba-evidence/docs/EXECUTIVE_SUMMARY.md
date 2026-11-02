# NBA Evidence — Executive Summary

## Decision

**No validated betting edge. No strategy released. No rewards awarded.**

This is a bounded, reproducible research pilot—not a current betting slate or a complete NBA database.

## What was built

- 62 official final scores from eight NBA date pages, January 1–8, 2025.
- 38 official participating-player rows from two complete box scores.
- 39 historical fair-line sets: 15 validation and 24 locked test games.
- Eight strategy hypotheses across singles, cross-game parlays, same-game parlays and player-prop combinations.
- Ten fail-closed release gates; a diagnostic leaderboard; a 1,000-point non-monetary reward pool with zero awards.
- A source-linked static dashboard, input receipts, unit tests and a repository audit.

## Findings

- Test Brier: **0.3076**, versus **0.2720** for the frozen training team1 base rate. The model underperformed.
- Test log loss: **1.0286**, versus **0.7418** for the baseline.
- Margin MAE: **12.222** points. Total-line MAE: **12.958**, versus **12.962** for the training mean. This tiny difference is not evidence of edge.
- Same-game joint residual Brier: **0.1092**, versus **0.1199** for a product estimate. Exploratory only; 23 training residual pairs and 24 test events.
- Player correlations are pooled between-player estimates from two games, not within-player parlay dependence. Short-sample confidence intervals are suppressed.

## Missing evidence

No verified historical executable sportsbook quotes, limits or accepted-ticket rules. No large multi-season point-in-time dataset, pregame context features, repeated player histories or prospective frozen ticket log. Market ROI and personalized prop prices remain blank.

Luck cannot be eliminated. Leakage controls, baselines, dependence-aware evaluation, a complete trial registry and prospective replication can reduce false discoveries; none proves certainty.

## Sources and verification

Every input row links to an official NBA page. The primary pages were read on 2026-11-02. CI checks the committed extracts, arithmetic, schema, source coverage and reproducibility; it does not independently re-fetch remote truth. See the source register and verification ledger.

The Milwaukee player-minute values sum to 240:01. This source irregularity is retained and flagged; points/rebounds/assists reconcile.

## Competition

Forecast diagnostics are ranked separately from betting eligibility. All ten gates must pass before a strategy can receive rewards. The proposed 60/30/10 allocation of 1,000 research points is non-monetary and currently entirely unawarded.

## Repository coordination

Concurrent work is preserved in its original namespaces. This session works only in `nba-evidence/` plus its isolated workflow and append-only coordination records. Arena's fixed branch constraint is documented. The repository audit scans every tracked text line but does not claim every inherited numeric row was externally re-verified.

## Next steps

1. Resolve authorized access to official operator price history and expanded league data.
2. Freeze a genuinely prospective protocol and record every trial.
3. Validate singles against matched baselines and actual prices.
4. Validate joint distributions and quoted parlay payouts before combinations.
5. Require multi-season replication and explicit risk/execution checks before rewards or deployment.

Research only; not wagering advice or an offer of prizes.

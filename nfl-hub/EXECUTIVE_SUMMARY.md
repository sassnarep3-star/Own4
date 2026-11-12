# NFL Line Genesis — Executive Summary

**Snapshot:** 12 November 2026 (Week 10) · **Status:** research complete, no validated edge · **Site:** `/nfl-hub/`

## 1. Bottom line

The system works as an evidence machine and fails as a betting system — and it says so. Official data reconciles
perfectly, the Week 10 lines were generated before the first kickoff with no look-ahead, every registered strategy was
scored on a frozen holdout, and none passed. The next step is not another model: it is two decisions and two data
purchases.

## 2. What is verified

| Claim | Verification | Source |
|---|---|---|
| 2026 records and points, 32 teams | 32/32 matched on W-L-T, PF, PA and NFL tie percentage | <https://www.nfl.com/standings/> |
| Week 10 fixtures and byes | 14/14 matched by pairing and date; byes CHI, DEN, PHI, TB | <https://www.nfl.com/schedules/2026/by-week/week-10> |
| Formal injury designations | 6 players league-wide at capture (2 WAS, 1 NYG, 3 NE) | <https://www.nfl.com/injuries/> |
| Quarterback changes | SEA (Lock for Darnold), CLE (Watson), ARI (Beck); MIA headline only | <https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again> |
| No official depth chart | NFL.com depth-chart URL returns 404 | <https://www.nfl.com/teams/kansas-city-chiefs/depth-chart> |
| Rules context | 2026 rule changes | <https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> |

Internal consistency checks: the archive reproduces 136 completed games with zero duplicate ids, zero score mismatches,
zero total mismatches, and league-wide points-for equal to points-against (6,246).

## 3. What the model says, and what that is worth

Holdout 2017-2025, 2,383 games:

| Metric | Model | Closing line | Naive (+2.5 home) |
|---|---|---|---|
| Margin MAE | 10.392 | **9.871** | 11.116 |
| Total MAE | 11.971 | **10.470** | — |

The market is the better forecaster on both. A standalone model is therefore not the product; a residual model judged
by closing-line value is the only defensible path.

Strategy results (flat 1 unit, archived closing prices):

| Strategy | Bets | Holdout ROI | 95% CI | Placebo p | Tier |
|---|---|---|---|---|---|
| S1 spread edge | 1,125 | −5.28% | −10.69% to +0.07% | 0.601 | Rejected |
| S2 total edge | 1,804 | −9.03% | −14.16% to −4.36% | 0.975 | Rejected |
| S3 moneyline value | 1,103 | −7.95% | −15.48% to −0.25% | 0.873 | Rejected |
| S4 cross-game parlay | 3,791 | −13.58% | −23.30% to −3.60% | 1.000 | Research-only |
| S5 SGP monitor | — | — | — | — | Research-only |
| S6/S7 props | — | — | — | — | Blocked |

S1 returned +4.6% on validation and −5.3% on the holdout; S3 returned +9.8% and −8.0%. That gap is the argument for
pre-registration, not a reason to re-tune.

## 4. What is missing, and why it is blank rather than estimated

| Missing input | Consequence | Question |
|---|---|---|
| Official or licensed 2026 market lines | No market comparison, no CLV, no executable ROI | Q-04 |
| Official depth chart or snap counts | 2nd/3rd/4th-string deficiency index impossible | Q-05, Q-21 |
| Player-level feed and prop prices | Props and prop combos blocked | Q-07 |
| Final pre-kickoff injury report | Only 6 formal designations at snapshot | Q-11 |
| Legal review of rewards and redistribution | Rewards stay non-monetary; public picks unclear | Q-12, Q-13 |
| Named decision owner and cadence | Nothing can be formally accepted | Q-17 |

## 5. Five decisions that unlock the next phase

1. **D1 — Canonical workspace.** Keep `nfl-hub`, banner and archive the other four NFL dashboards.
2. **D2 — Market data.** License a timestamped odds and prop feed, or accept permanent research-only status.
3. **D3 — Reward rule.** Rank by the lower confidence bound, roll the pool over when nothing qualifies.
4. **Q-05 — Define "starter".** Without snap counts the defensive-depth request cannot be met honestly.
5. **Q-13 — Legal opinion** before any prize, payout or public pick publication.

## 6. Flagged irregularities (non-blocking)

Seventeen items, including: two dead NFL.com citations inherited from `nfl/`; a stale Week 8/9 slate still presented
as current on `nfl-lab/` and `nfl-quant/`; an official contradiction (Ravens "No Injuries Reported" while Lamar Jackson
is on injured reserve); no official depth chart; and the absence of any 2026 market price. Full list:
`nfl-hub/pages/flagged.html`.

## 7. Why this is safe to publish

Every table row links to a source or carries an explicit DERIVED badge. Every blank is labelled. The pipeline rebuilds
every number from committed data and the verifier fails on an unsourced row, a broken link, or a byte of drift. The site
states on its landing page that the lines should not be bet.

*Research only. Not wagering advice. Non-monetary rewards. Problem gambling helpline: <https://www.ncpgambling.org/help-treatment/>.*

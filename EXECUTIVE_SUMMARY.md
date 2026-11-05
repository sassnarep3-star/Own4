# Executive Summary — Own4: NBA Line Origination

**Status date:** 2026-11-05 · **Session:** `arena-7a06a47e-own4`
**Canonical dashboard:** https://sassnarep3-star.github.io/Own4/nba-lines/site/
**Flagged for review:** https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/flagged.html
**Repo review:** https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/repo-review.html

---

## 1. The one-paragraph answer

You asked for original NBA lines, useful signals, a leaderboard that rewards skill, and protection against luck.
This release delivers all four as a working, reproducible pipeline — and the honest result is that **the model
has real forecasting information but no strategy has earned a reward**. Out-of-sample Brier score is
`0.2104` against a `0.2531` constant-home baseline (skill
`+0.1728`, permutation p = `0.0002` over 4,000 shuffles), which is genuine
evidence of signal. It is not evidence of an edge: there are only 96 graded games, the moneyline
model's calibration fails its gate (expected calibration error `0.1037` against a 0.05 limit), and there
is **no official price archive** to compare a fair line against. Zero of twelve strategies is reward-eligible, and
that is the designed outcome rather than a failure.

## 2. What was built

| Layer | Delivered | Where |
|---|---|---|
| Official data | 121 final scores (2026-10-20 → 2026-11-04), 30 standings rows, tonight's 2-game slate, 13 availability rows | `/nba-lines/site/data/` |
| Verification | 30/30 teams reconciled against official standings, zero mismatches | `/nba-lines/site/data/standings.html` |
| Originated lines | Fair spread, total, team totals and moneyline for both games tonight; 12 player-prop lines | `/nba-lines/site/lines/` |
| Strategies | 12 named constructs across singles, parlays and player-prop combos | `/nba-lines/site/research/strategies.html` |
| Correlation values | 10 coefficients with 95% CIs, p-values and Benjamini–Hochberg q-values | `/nba-lines/site/research/correlations.html` |
| Luck removal | Strict walk-forward scoring, paired bootstrap, 4,000-draw permutation test, FDR control | `/nba-lines/site/research/backtest.html` |
| Validation gates | 10 pre-registered gates; 7 pass, 3 fail | `/nba-lines/site/research/gates.html` |
| Leaderboard | 12 entries, pre-registered 40/25/15 reward tiers, 0 payouts | `/nba-lines/site/competition/leaderboard.html` |
| Governance | Source register (16 entries), repo review (16 findings), flagged register (18 items) | `/nba-lines/site/governance/` |

## 3. Headline numbers (all computed in this session, all reproducible)

| Metric | Value | Baseline | Reading |
|---|---|---|---|
| Brier score, home moneyline | `0.2104` | `0.2531` | Skill `+0.1728`; bootstrap 95% CI `+0.024` to `+0.316` |
| Permutation p (luck test) | `0.0002` | — | Fewer than 1 shuffle in 4,000 matched it |
| Expected calibration error | `0.1037` | limit 0.05 | **Fails** gate G6; reliability slope `0.899` is inside tolerance |
| Spread MAE | `10.85` pts | `12.29` pts | Skill `+0.1176`, CI includes 0 |
| Total MAE | `15.66` pts | `15.99` pts | Skill `+0.0201`, CI includes 0 — no evidence it beats the league average |
| Graded predictions | 96 | required 300 | **Fails** gate G3 |

## 4. Correlation values — the actual deliverable you asked for

Every coefficient below was computed inside the repository from committed files, with a confidence interval and
false-discovery control.

| Pair | n | r | 95% CI | BH q | What it means for pricing |
|---|---|---|---|---|---|
| Margin vs total | 121 | `+0.0180` | -0.161 to +0.196 | `0.845` | Effectively independent: spread+total SGPs can be multiplied with negligible error |
| Home points vs away points | 121 | `+0.1994` | +0.022 to +0.365 | `0.047` | Significant: a fast game lifts both sides |
| Player PTS vs REB (within-player residuals) | 1951 | `+0.2679` | +0.226 to +0.309 | `0.000` | **The number that matters**: points+rebounds combos are systematically underpriced by an independent pricer |
| Player PTS vs AST (within-player residuals) | 1951 | `+0.1535` | +0.110 to +0.197 | `0.000` | Smaller but real |
| Player REB vs AST (within-player residuals) | 1951 | `+0.1892` | +0.146 to +0.232 | `0.000` | Minutes and game script move all three stats together |
| Teammate PTS vs teammate PTS | 184 | `-0.1388` | -0.278 to +0.006 | `0.082` | Negative as expected (usage trade-off) but **not significant** — stacking stays ungraded |
| Same-day total vs next-game total | 106 | `+0.1838` | -0.007 to +0.362 | `0.082` | Cross-game independence remains an assumption, labelled as one |

**Actionable consequence.** On tonight's slate the model's own margin/total correlation of
`+0.0351` moves a two-leg spread+total same-game parlay by only
`+0.0003` in Brier score — immaterial. The player-level coefficient of
`+0.268`, applied to the same player's points and rebounds
lines, moves a two-leg prop combo by up to `+0.05` in absolute probability. **Dependence is a player-prop
problem, not a team-market problem.** That single distinction is worth more than any strategy on the board.

## 5. Strategies and the leaderboard

| Rank | ID | Strategy | n | Skill | Bootstrap CI low | Perm p | Eligible |
|---|---|---|---|---|---|---|---|
| 1 | S04 | Rest / back-to-back fatigue adjustment | 96 | +0.1728 | +0.024 | 0.0002 | no |
| 2 | S05 | Recent-form (last-10) reversion overlay | 96 | +0.1690 | +0.020 | 0.0002 | no |
| 3 | S01 | Rating moneyline (ridge, 2025-26 prior) | 96 | +0.1685 | +0.020 | 0.0002 | no |
| 4 | S02 | Rating spread (point estimate) | 96 | +0.1176 | -0.003 | 0.4004 | no |
| 5 | S07 | Same-game parlay: home ML + over the fair total | 96 | +0.0839 | — | — | no |
| 6 | S03 | Total (additive team totals model) | 96 | +0.0201 | -0.073 | 0.6533 | no |
| 7 | S08 | Same-game parlay: home -3.5 + under the fair total | 96 | +0.0019 | — | — | no |
| 8 | S06 | Two-leg cross-game parlay (home ML + next-game over, independence) | 95 | -0.0241 | — | — | no |
| — | S09 | Player points prop (official season average + residual band) | — | — | — | — | no |
| — | S10 | PRA combo prop (points+rebounds+assists) | — | — | — | — | no |
| — | S11 | Teammate stack prop pair | — | — | — | — | no |
| — | S12 | Opponent-adjusted prop (pace/defence) | — | — | — | — | no |

**Zero rewards paid.** Eligibility requires every gate at once: n ≥ 300, a bootstrap lower bound above zero, a
permutation p below 0.01, calibration in tolerance, multiple-testing control and a price archive. Three of those
fail, and one of them (G9, prices) cannot pass at all with the data available.

## 6. Why no money is claimed, in plain language

A fair line is not an edge. An edge is the gap between your line and a price somebody will take the other side
of. This repository has no official or licensed price archive: the league does not publish odds, and third-party
sportsbook prices are outside the scope of the official verification this project requires. So the model can say
"the fair spread is PHX -1.6" and cannot say "that is worth betting". Any document in this repository that
implies otherwise is contradicting its own data.

## 7. What was verified, and by what method

1. **Reconciliation (the strongest check).** Aggregating the 121 committed final scores reproduces all 30
   official win-loss records exactly. Two separately produced official tables agreeing eliminates transcription
   error in the results set far more convincingly than re-reading any single page.
2. **Per-row sourcing.** 25 tables and 467 rows on the site each carry a link to an official page or to the
   committed data file. `verify.py` fails the build if a row lacks one.
3. **Host allow-list.** Every external link is checked against an allow-list of official and trusted hosts, so a
   fabricated citation cannot pass.
4. **Determinism.** The full chain rebuilds byte-identically; the verifier re-renders every page and compares
   hashes.
5. **Blanks stay blank.** 36 cells are rendered as explicitly unverified rather than as zero or as an estimate,
   and each maps to a flagged item.

Totals: **2,419 verification checks, 0 problems; 19 unit tests, all passing.**

## 8. Irregularities found in the repository (full list on the review page)

| ID | Severity | Finding |
|---|---|---|
| R01 | high | Eight separate NBA workspaces coexist with overlapping scope and no single canonical dataset. |
| R02 | high | Correlation coefficients are published for a 49,226 player-game dataset spanning 2010-11 to 2023-24, but that dataset is not in the repository and cannot be rebuilt from anything committed. |
| R03 | medium | The committed 'raw' nba.com pages cannot regenerate the results dataset: the server-rendered game cards contain empty score containers, so scores are only present after client-side rendering. |
| R04 | medium | Several source manifest entries record HTTP 403 or timeouts against cdn.nba.com and stats.nba.com, yet parts of the documentation describe those endpoints as if they had been used. |
| R05 | high | An automated collector downloaded roughly 47 MB of ESPN box-score JSON, which is in tension with the league's stated restriction on downloading its statistics, and ESPN is not the league. |
| R06 | medium | A workflow is hard-coded to another session's branch and therefore never runs against main; its commit step also rebases onto that dead branch. |
| R07 | low | Two different 'Flagged for Review' pages exist with different contents, so 'the flagged list' is ambiguous. |
| R08 | low | The shared board records contradictory outcomes for the same pull request in two different session entries. |
| R09 | medium | data/signals.json attributes a computed home-win rate to the standings page, which is a provenance mislabel: a standings table does not contain per-game home/away outcomes. |
| R10 | low | The 2025-26 prior-season team table is a hand transcription; it passes internal consistency (30 teams, every GP=82, sum of plus-minus per game = -0.2) but was not re-read page by page in this session. |
| R11 | medium | Individual player game logs stop at 2026-11-01, so the player-level layer is three days stale relative to the 2026-11-05 slate. |
| R12 | low | Two rosters disagree with 2025-26 expectations (Giannis Antetokounmpo listed with Miami, Tyler Herro with Milwaukee). Checked rather than assumed: three independent official pages agree. |
| R13 | info | The inherited canonical site does pass its own link checker: 11 pages, 758 links, 438 table rows, 0 problems. |
| R14 | low | The overtime flag on inherited result rows is a transcription convention (blank means 'not marked OT on the page'), not an independently verified field. |
| R16 | high | Two workspaces in the same repository publish opposite headline results for the same question. The root executive summary reports 1 trial and 5 of 11 parlay constructions passing every gate; the nba-evidence workspace reports zero qualified strategies and zero rewards; the lab reports that no strategy passes its pre-registered gates. |
| R15 | info | The board already contains a documented self-correction of a doubled '/site/site/' publication path, and the corrected path resolves. |

The three that matter most:

- **R02 — coefficients without data.** A published correlation table cites a 49,226-row dataset spanning
  2010-11 to 2023-24 that is not in the repository. Those numbers cannot be reproduced. This release does not
  use them.
- **R16 — contradictory conclusions.** The root summary claimed 1 trial and 5 of 11 parlay constructions passed
  every gate; the evidence workspace claimed zero. Both cannot be true, and neither side is checkable from
  committed data. Resolved by replacing the root summary (this file) and preserving the old text below, labelled
  superseded.
- **R05 — harvesting vs terms.** 47 MB of partner box scores were downloaded automatically, which sits in
  tension with the league's stated restriction that its stats are not available for download. This release adds
  no such harvesting.

## 9. What is blank, and why

Eighteen items are flagged. The blocking ones:

- **F01** no official price archive → no EV, ROI or closing-line value, ever, in this release.
- **F02** 96 graded games against a 300 requirement.
- **F03** calibration error 0.104 against a 0.05 gate.
- **F05/F07** prop volatility is pooled across players and derived from partner data, not league data.
- **F18** no funded reward; points are a scoring convention.

## 10. Next steps that would actually change the answer

1. **Acquire a licensed historical price feed with timestamps.** This is the only step that makes gate G9
   passable and the only way an edge becomes measurable rather than asserted.
2. **Keep grading nightly.** The 2026-27 season reaches the 300-game threshold around mid-December; rerunning
   `engine.py` is enough.
3. **Fit a calibration layer** (isotonic or Platt) on a locked holdout to clear G6.
4. **License play-by-play** so prop volatility and pace adjustment can be estimated per player and per matchup
   instead of pooled.
5. **Decide the status of the inherited workspaces.** They are preserved, but eight dashboards answering the same
   question is a governance problem, not a feature.

## 11. Responsible gambling

Research only — not wagering advice, and not a betting product. National Problem Gambling Helpline
**1-800-MY-RESET** · https://www.ncpgambling.org/help-treatment

---
---

# Appendix — superseded summary (2026-11-02)

*Retained verbatim so nothing is lost. Its headline claims are **not** endorsed by this release: finding R16
records that they contradict the evidence workspace, and their input dataset is not in the repository. See the
canonical result above.*

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


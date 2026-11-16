# Pre-registered model specification — NFL Command Center

**Registration:** this file is the registration. The rule text below was committed **before** the
engine was first run and before any Week 11 outcome exists (Week 11 kicks off 2026-11-19). The git
commit hash that first contains this file is the registration hash; the build records it.

**What this model is.** A singles-only shadow baseline. It publishes a fair total, a fair side and a
moneyline probability for every Week 11 game, from league-published season aggregates only. It is
deliberately the dumbest defensible model in the repository, because the brief asks for a
*pre-registered simple team-strength baseline* whose forecasts can be scored later, not for a clever
model whose forecasts cannot be reproduced.

**Inputs — official only.**

| Input | Source | Field |
|---|---|---|
| Points for, points against, wins, losses, ties, per club | `https://www.nfl.com/standings/` read 2026-11-15 | `pf`, `pa`, `w`, `l`, `t` |
| Week 11 fixtures, kickoff clock time, home/away | `https://www.nfl.com/schedules/2026/by-week/week-11` read 2026-11-16 | fixture table |
| Settled results used only to estimate two league constants (home-field edge, margin dispersion) | official `nfl.com` game/week pages already carried in this repository by peer workspaces, reconciled 32/32 clubs against the standings above | `home_margin`, `total_pts` |

No price, no rating service, no depth chart and no injury designation enters the model. Injury and
availability are **not** features in version 1 — the brief forbids fixed injury penalties, and the
ablation that would justify a personnel feature is blocked (see gate G7). Saying that plainly is the
point: a model that quietly folds in an injury adjustment is exactly the "fixed penalty" the brief
rejects.

**Estimates.**

1. `team_games = w + l + t`, which the standings identity fixes for every club.
2. `off_rate = pf / team_games`; `def_rate = pa / team_games` (points per team-game).
3. `E_home = (off_home + def_away) / 2 + HFA` and `E_away = (off_away + def_home) / 2`, where `HFA`
   is one half of the league mean home margin — i.e. each side is moved by half the observed home
   edge, so the *total* is unaffected by venue and only the *side* is.
4. `fair_total = E_home + E_away`; `fair_spread_home = E_home - E_away` (negative = home favoured).
5. `P(home win) = Phi(fair_spread_home / (sqrt(2) * sigma))`, `sigma` = sample standard deviation of
   `(actual_margin - HFA)` over the settled corpus. A tie is scored as half a win for both sides when
   the moneyline forecast is graded (rule stated here so it cannot be chosen after the fact).

**Published line convention.** Totals are quoted to the nearest half point and sides to the nearest
half point, both **away from** the model's expectation (so the published number is never a
half-point easier than the model's own estimate). The unrounded value is published beside it.

**Origination order — side, then total, then moneyline.** The order is a published field on every
row (`origination_order`), not a narrative claim, and the build fails if a row is emitted out of
order. Rationale: the side is the market the two ratings differences act on most directly; the total
follows because it needs both defences; the moneyline is last because it needs `sigma`, the one
estimated constant with the widest interval.

**Freeze.** Version `v1-FROZEN-2026-11-16`. Changing any constant, the input list, the order or the
grading rule is a *new* version, requires a new registration commit, and resets the out-of-sample
sample to zero. Amendments are listed in `strategy_registry.json` under `amendments`; the list is
empty at registration.

**What would falsify it.** Two-sided, published with the strategy: it is supported if, over a
pre-declared out-of-sample window of at least 300 graded games, the total's mean absolute error beats
the season-to-date naive baseline with a game-cluster bootstrap lower bound above zero **and** the
moneyline's Brier skill against a home-field baseline is positive at the same confidence. It is
refuted if either interval includes zero after that sample, or if it fails the demotion rule below.
Neither outcome can be claimed at n = 0.

**Demotion rule (frozen now, applies to every strategy in the registry).** A strategy that has been
promoted to live returns to paper when, over four consecutive graded weeks, its benchmark-relative
Brier skill is ≤ 0 on the game-cluster lower bound, or when it grades fewer than 75% of the games it
forecast. Demotion is automatic and does not require a review meeting; promotion out of paper
requires every one of the ten gates, not a majority.

---

## Erratum, appended 2026-11-16 (no rule above is changed)

Two defects were found after the registration commit and are recorded here rather than edited
into the frozen text, so that the frozen text and its history stay intact.

**E1 — sign note on `fair_spread_home`.** Step 4 says *"negative = home favoured"*. The engine has
always computed `fair_spread_home = E_home - E_away`, so a **positive** value means the home side is
expected to win by that margin. The engine, the published columns and the site labels are all
consistent with the positive convention; only that parenthetical was wrong. It is corrected here:
`fair_spread_home > 0` = home favoured, and the published table prints the favoured club by name
(`HOU 4.0`) as well as the unrounded signed margin, so the sign is not carried by a note alone.

**E2 — the sample behind the two constants.** `HFA` and `sigma` are estimated from the settled
corpus. The first build merged the verified corpus (137 settled games) with this week's
transcription (12 finals) without deduplicating the Thursday game that appears in both, which
produced `n = 149` against 148 reconciled games. The merge is now keyed on `(date, away, home)`,
one game is dropped as overlap, and the build asserts that the constant sample equals the
reconciliation count. `n = 148`; the published constants are `HFA = -0.3243` (half the observed mean
home margin) and `sigma = 13.4997`.

The demotion rule, the gates, the input list, the origination order and the grading rule are
untouched by both errata. `strategy_registry.json` records the amendments, so the freeze statement
above remains accurate in the only sense that matters: nothing that would change a forecast was
adjusted after the forecasts existed.

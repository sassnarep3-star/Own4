# PREREG-LB — leaderboard and strategy registration

Registered: **2026-11-17**, before `engine/leaderboard.py` was run on any Week 11 data
(no Week 11 game has been played at registration; the slate starts 2026-11-19).

The registration is the file. Its SHA-256 is recorded in `data/prereg.json` and re-checked by
`engine/verify.py`, so a post-hoc edit to this rule text cannot go unnoticed.

## 0 · What is being ranked

Probabilistic forecasts of an NFL market. A strategy is a written rule that turns the
`nfl-live-board` corpus into a probability for a specific market on a specific game. Four
divisions, ranked separately and never pooled:

| division | what qualifies | status at registration |
|---|---|---|
| SINGLES | one market, one game, one side | populated (moneyline) |
| GAME PARLAYS | two or more legs from different games | empty — needs a price feed to settle |
| SAME-GAME PARLAYS | two or more legs, same game | empty — joint evidence gate not passed |
| PROP COMBOS | player props or combinations | empty — no official player-prop source |

An empty division is reported as empty. Nothing is moved into a division to fill it.

## 1 · Ranking rule

1. **Qualification is by proper score only.** The metric is the Brier Skill Score against a
   benchmark the forecaster could have computed before kickoff (the training-window home win
   rate). Raw win rate is not a metric and never appears in a ranking column.
2. **Uncertainty is clustered by week.** Games inside a week share injuries, weather, rest and
   referee assignment, so they are not independent. The interval is a 90% bootstrap over weeks.
3. **Multiplicity is adjusted and published.** Every strategy scored in a run counts as a trial.
   Holm–Bonferroni is applied across all of them, and the number of trials is shown beside the
   adjusted p-value.
4. **A strategy qualifies** when the week-clustered lower bound of its Brier Skill Score is
   above zero **and** its Holm-adjusted p is below 0.05.
5. **Controls are strategies for this purpose.** A constant 0.5 forecast and an always-home
   pick are scored in every run. Whatever score they reach is the floor that luck alone
   produced at this sample size. A strategy that does not clear that floor has no claim.

## 2 · Staking, and why it cannot rank

Staking is a **second stage**, held in escrow, and is blank until a closing price exists.
An assumed price is not a price: `-110` would manufacture return out of a modelling constant.
Consequently no realized ROI, CLV or reward is computed at registration, and a perfect staking
run cannot lift a strategy that failed stage 1 — the stage-1 column decides.

Demotion gate (registered now, applied to any future live strategy): a strategy that qualified
is returned to paper, immediately and without discretion, when any of the following is observed
on a sample of at least 30 prospective forecasts:

* week-clustered Brier Skill Score at or below zero over the prospective window;
* the observed hit rate falls below the lower bound of the interval registered with the
  strategy at qualification;
* the input snapshot for any forecast is missing its timestamp, or its raw hash does not match
  the capture ledger;
* a published forecast changes after kickoff.

## 3 · The strategies registered in this session

All five are scored on the same 116-game walk-forward window (weeks whose training set held at
least 32 games). None has seen a Week 11 result.

| id | rule | market |
|---|---|---|
| S1-ML-edge | p(home) = Φ(fair margin / residual SD); forecast every game | moneyline |
| S2-ML-strong | same forecast, but only games with a fair margin ≥ 6 points are of interest; the score below is still computed on all games, because selection skill and forecast skill are not separable at this n | moneyline |
| S3-home-prior | the training-window home win rate, as a strategy | control |
| S4-coin | constant 0.5 | control |
| S5-always-home | pick home, stated at 0.51 | control |

**Frozen model parameters:** shrink = 4 pseudo-games, minimum training window = 32 games,
moneyline derived from the side with the walk-forward residual SD. Changing any of them
creates a new strategy with a new id; it does not edit S1.

## 4 · What is deliberately not registered

* A parlay strategy. Multiplying marginal probabilities is invalid under dependence; a registered
  parlay needs a directly estimated joint probability, which needs a price feed.
* A prop strategy. No official player-prop market or price exists in this repository.
* Any strategy whose inputs include availability. The repository holds one dated availability
  snapshot for the current season, so an ablation of availability features against the same
  window would be a comparison of one point to itself. It is an open requirement, not a result.

## 5 · Reward rule

1000 points are held. Points are paid **only** to strategies that pass stage 1 **and** stage 2
on a prospective sample. At registration, points awarded = 0. The score is public and the
qualification arithmetic is reproducible by running `engine/leaderboard.py`.

---

*Research only — no wagering is offered. NCPG helpline: 1-800-697-3738 (https://www.ncpgambling.org/help-treatment/)*

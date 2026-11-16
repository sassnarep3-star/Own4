# NFL Sources — pre-registration (frozen before any result is computed)

**Session:** `arena/f7545de2-own4` · **Registered:** 2026-11-16 (UTC) · **Status:** frozen.
The git commit that first adds this file is the registration. Editing this file after that commit is
forbidden; a change requires a new pre-registration file and a new commit.

## 1. What is registered here

1. The **results corpus** (which games, from which page, with which verification status).
2. The **rating model** (formula, estimation method, hyper-parameters, freezing rule).
3. The **forecast register** (what is stored per game, and the walk-forward protocol).
4. The **scoring rules** (proper scores, baselines, uncertainty, multiplicity).
5. The **gates** that decide whether a number may be published, ranked, or used for staking.
6. The **correlation set** that will be computed.

No number in this namespace is computed before this file exists in git history.

## 2. Result corpus

* **Population:** every 2026 NFL regular-season game that the official week schedule page prints as
  `FINAL`, weeks 1–10, read on 2026-11-16 UTC from
  `https://www.nfl.com/schedules/2026/by-week/week-{1..10}`.
* **Input format:** each week page is transcribed to `nfl-sources/raw/weekN.txt` (one line per game:
  week, date as printed, section as printed, away, away points, home, home points, game-centre URL as
  printed). The transcription files are committed next to this registration so that the corpus can be
  re-checked against the pages without re-reading them.
* **Unit:** one row per game, with away/home club abbreviations, away/home points, the date as printed,
  the game-centre URL printed on the page, and the week page URL.
* **Excluded, by rule:** any game not printed as `FINAL` at read time. Week 10 `PIT at CIN` (printed
  `Q1 … Live`) and week 10 `LAC at BAL` (printed as unplayed, `Nov 16 8:15 PM`) are therefore excluded
  and carry **no score**, blank rather than guessed.
* **Independence check:** every team's W-L-T derived from the corpus is compared against the official
  league standings page `https://www.nfl.com/standings/league/2026/REG`, which is transcribed
  **before** the derived records are computed. Any mismatch is a defect and is published as one.
* **Reconciliation:** every row is also compared with the inherited feed
  `nfl-book/data/results_feed.json` (which marks 105 of its 137 rows `aggregate_only`, i.e. not
  page-verified). Agreement and disagreement counts are published; disagreements are never silently
  resolved in favour of either file.

## 3. Rating model (v1) — frozen

Points-based, opponent-aware, equal-weighted, ridge-regularised linear model, fitted by ordinary least
squares on the **normal equations** with a Gaussian-elimination solver (no third-party libraries).

For a game with home club `h` and away club `a`:

```
home_pts = mu + hfa * (1 if not neutral else 0) + o[h] - d[a]
away_pts = mu                                + o[a] - d[h]
```

* `mu` — league baseline points per team per game.
* `hfa` — home-field points added to the home club only. It is set to **0** when the official week page
  prints the fixture inside an `International Game` section: the club whose stadium it is is not
  hosting, so the printed home designation does not carry home-field advantage. The NFL does **not**
  print the word "neutral", so this namespace never claims a game is neutral — it records the official
  printed section verbatim (`international_game: true/false`) and states exactly how the flag is sourced.
* `o[i]`, `d[i]` — club `i`'s offence and defence ratings in points.
* **Estimation:** minimise `Σ (y - ŷ)² + λ * (Σ o² + Σ d²)` with **λ = 4.0**; no penalty on `mu`, `hfa`.
  Solved by Gaussian elimination with partial pivoting on the normal equations (stdlib only).
  The ridge term is also what identifies the model: without it, adding a constant to every `o` and the
  same constant to every `d` leaves every prediction unchanged.
* **Weights:** equal. No recency weighting in v1 (a recency variant would be a *separate* registered
  strategy, not a silent change to this one).
* **Freezing rule:** a forecast for week `w` may use **only** games from weeks `< w`. Refitting happens
  once per week, before that week's games are scored.

Derived outputs per fixture:

```
pred_margin = pred_home_pts - pred_away_pts
fair_home_line = -pred_margin          (NFL convention: negative = home favoured)
fair_total = pred_home_pts + pred_away_pts
p_home = Φ(pred_margin / sigma),  sigma = root-mean-square of the fit set's margin residuals
```

Ties are possible in this population (the official standings print 2). A tie carries `y = null`, is
excluded from accuracy and from the Brier/log-loss terms, and is counted and published as a tie.

Origination order is **side → total → moneyline**, audited in the data (each row records the order).

## 4. Forecast register

Every forecast row stores: the probability, **all inputs** (`.mu`, `.hfa`, `.sigma`, the two clubs'
`o` and `d` values as fitted, the training cutoff week and the training game count, the neutral flag),
the official result (both scores, and whether the game is in the corpus), and the scores
(Brier, log loss, absolute margin error, absolute total error). A row without a result is stored with
`result_known: false` and contributes to no metric.

## 5. Scoring rules — frozen

| Quantity | Rule |
|---|---|
| Win probability | Brier score and log loss on `home win` (ties carry `y = null`) |
| Direction | accuracy vs 0.500; ties excluded from accuracy, never counted as correct |
| Margin | MAE and RMSE in points, all games |
| Total | MAE in points, all games |
| Skill | Brier **skill score** `1 - BS_model / BS_baseline`, baseline named explicitly |
| Uncertainty | 2 000-sample bootstrap, **resampled by week cluster** (a week is a game cluster), 95 % percentile interval; the **lower bound** is the quoted number |
| Multiplicity | every family of strategies registers its size `m`; a strategy's interval is quoted both raw and Bonferroni-adjusted (`1 - α/m`) |
| Staking | ROI is computed **only** at a price that is stated on the row. The NFL publishes no prices, so every ROI here is at an **assumed −110** and is labelled hypothetical; it is never ranked |
| Luck | see §6 |

## 6. Registered luck-removal tests

1. **Placebo (label shuffle):** shuffle the model's probabilities across the games of the same week,
   2 000 times; p-value `(1 + #{null ≥ observed}) / (1 + n_null)` — the floor is 1/2001, never 0.
2. **Coin-flip counterfactual:** the same number of bets, decided by a fair coin, 2 000 times.
3. **Cluster bootstrap:** §5 uncertainty, by week.
4. **Regression to the mean:** split the sample into halves (weeks 3–6, weeks 7–10) and correlate each
   strategy's per-week skill between halves. A strategy whose skill does not persist is reported as
   *not distinguishable from luck*, whatever its total score.
5. **Fade test:** the model's picks inverted must not also score as skill (if it does, the score is noise).

## 7. Strategies registered (m = 4 companions to the baseline)

* **S1 — Model favourite (singles).** Bet the club the model makes the favourite. Decision rule uses the
  model's own probability only; no price input.
* **S2 — Model favourite, high-confidence subset only.** Same as S1, restricted to `p_home ≥ 0.65` or
  `p_away ≥ 0.65` — the threshold is frozen here, before results.
* **S3 — Model vs. record baseline.** Bet the club with the better point-in-time win record (a
  verifiable, price-free control), not the model. **This is a control, not a candidate.**
* **S4 — Fade of S1** (required by §6.5).
* **C1 — Coin flip** (control).
* Parlays, same-game parlays and prop combos are **not registered** in v1: no joint distribution has
  been validated and the operator's void/push rules are not available. They stay behind the joint-evidence
  gate, with the clearing number stated on the site.

## 8. Gates

| Gate | Rule (frozen) |
|---|---|
| **G1 coverage** | a strategy may be called *live-eligible* only at `n ≥ 300` graded games |
| **G2 signal** | accuracy interval must exclude 0.500, and the Brier skill score's cluster lower bound must exceed 0 |
| **G3 leakage** | mutate every result after the cutoff; no forecast at or before the cutoff may change |
| **G4 placebo** | §6.1 p < 0.05 |
| **G5 staking** | ROI interval at a *stated* price must exclude 0 — **cannot pass while no price source exists** |
| **G6 joint evidence** | a parlay/SGP/prop combo needs a validated joint probability; blocked |
| **G7 demotion** | a live strategy that fails G2 on 4 consecutive weeks returns to paper |

## 9. Correlations registered

Computed **only** from official numbers, each with `n`, `r`, two-sided p (normal approximation of the
t test, disclosed) and a Fisher-z 95 % interval:

* `CR-01` home margin vs game total
* `CR-02` a club's points scored, consecutive games
* `CR-03` points scored vs points allowed, same game (is defence independent of offence?)
* `CR-04` rest-day differential vs home margin (rest days from the printed dates only)
* `CR-05` neutral-site vs home margin

Blank by rule (no official source): any correlation needing a market price, a player prop, or a snap
count.

## 10. Publication rules

* A row without an official source URL does not render. The build fails instead.
* A value that cannot be read from an official page is left **blank** and listed on *Flagged for Review*.
* Backtest numbers never appear on the leaderboard; the leaderboard's stage 1 is proper scores only, and
  the build fails if a return figure is rendered in the leaderboard table.

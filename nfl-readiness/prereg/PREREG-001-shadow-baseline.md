# PREREG-001 — Singles-only shadow baseline (team-strength model)

Registered by session `arena-d941f3c1-own4`, 2026-11-15, **before** any evaluation of this model was
run. The commit that lands this file is the registration; the hash is recorded in
`nfl-readiness/data/prereg.json` and re-checked against git history by `engine/verify_site.py`.
Any change to the rule text requires a new PREREG id; this file is never edited after registration.

## 1. The rule

A single strategy, one market per game, no staking, no parlay, no prop.

1. For each scheduled game *g* between clubs *a* (away) and *h* (home), compute a **net rating** per
   club: `R(t) = (PF(t) - PA(t)) / GP(t)` using only games completed **strictly before** *g*'s
   kickoff, from the official league standings table. A club with `GP = 0` gets `R = 0`.
2. Expected margin: `M = R(h) - R(a) + H`, where `H` is the home-field constant, **fitted once** on
   the chronological first half of the available game log and then frozen. No refit inside the
   evaluation window.
3. Fair margin line is `M` rounded to the nearest 0.5. The probability that the home side covers a
   published line `L` is computed as `p = 1 - Phi((L - M) / sigma)` with `sigma` fixed to the
   standard deviation of `(final margin - M)` over the same first half, then frozen.
4. The market line, the residual against it, and any ROI are **not** part of this rule: no official
   price source exists (see DEC-P1 / flag RF-02). Publishing them is out of scope, not deferred.
5. Availability features are **not** used in the baseline. They are held for the ablation arm
   (governance `ablation_spec`), whose protocol is frozen in the same file and whose input does not
   yet exist.

## 2. Sample window

* Results source: the official league standings page (`https://www.nfl.com/standings/league/2026/REG`)
  and the official by-week schedule pages, read with a recorded window.
* Corpus: every game credited in the official standings at read time — measured as `sum(GP)/2 = 145`
  games on 2026-11-15 (133 through Week 9). A game enters the graded set only when its state on the
  official schedule page is **Final** (flag RF-07: three games were in progress and already credited).
* Evaluation is **chronological by week**. No shuffling. Forecast for week *w* may use only weeks
  `< w`. The first week with `GP = 0` for both clubs is reported, not scored.
* The figure "136 games" quoted in the project brief is not adopted (flag RF-01).

## 3. Metrics (the only three this rule produces)

1. **Brier skill vs the league base rate** for the cover event, where the base rate is the observed
   home-cover frequency on the training half.
2. **MAE of the fair margin vs the official final margin** (a model-quality number, *not* a price
   residual).
3. **Calibration table** in five bins of `p`, with `n` per bin.

Each is reported with a game-clustered bootstrap interval (clusters = games, resampled by week),
and with `n` printed on the same row. A single number without an interval is not published.

## 4. Gates

| Gate | Threshold | Meaning |
|---|---|---|
| G1 sample | n ≥ 300 graded games | below this the strategy is displayed as *provisional, unranked* |
| G2 skill | game-clustered lower bound of Brier skill > 0 | otherwise: no skill claim, ever |
| G3 multiplicity | Benjamini–Hochberg q ≤ 0.05 across the registered strategy set | protects against the trials the leaderboard will accumulate |
| G4 integrity | every input row sourced, coverage published, 0 silent blanks in the last capture | a source-schema change suspends evaluation |
| G5 prices | verified price data exists | required **only** for CLV, ROI or reward payment; never for G1–G4 |

## 5. What would confirm it / what would refute it (two-sided, required by the brief)

* **Confirm:** skill's lower bound > 0 with n ≥ 300, calibration slope in [0.8, 1.2], **and** the
  availability-ablation arms agree in sign once 4 dated weeks exist.
* **Refute:** any of — lower bound ≤ 0 at n ≥ 300; calibration slope outside [0.8, 1.2]; the model's
  MAE worse than a constant-line forecast (`M = H` for every game) on the same window; or the two
  arms of the ablation disagree in sign (then availability is not a real input, whatever the
  baseline shows).
* **Refute (data side):** if the availability capture cannot be reproduced as a dated series
  (≥ 3 entries per week for 2 consecutive weeks), all availability claims in this rule are void and
  the baseline reverts to results-only, permanently labelled accordingly.

## 6. Standing prohibitions attached to this registration

* Backtest figures never appear on a leaderboard page.
* ROI never ranks a strategy; a lucky run cannot promote anything.
* No depth rank, no "starter" label and no snap share is invented: the report publishes designations,
  and that is what this rule may use.
* The 6-row non-injury vocabulary ("Not injury related — resting player / personal matter",
  flag RF-11) is excluded from any injury count.

# Methodology

1. Source and target definitions
Use official NBA final scores and participating-player box scores. Preserve display order rather than inventing home/away. Keep overtime in final scores. The target for probability scoring is a team1 win; it is not a home-win target. Player PRA is the arithmetic sum of points, rebounds and assists.
2. Chronology and feature construction
January 1–3, 2025 is training (23 games); January 4–5 is validation (15); January 6–8 is locked test (24). All games on a date are predicted before any result from that date updates team states. Training means and logistic coefficients are frozen before validation. Later outcomes may update scoring histories for subsequent dates, but never the current date's features.
3. Probability and price
Shrink each team's scoring-for and scoring-against means toward the training league mean with five prior games. Fit a two-parameter L2 logistic model on training-only pregame margin features. Fair decimal odds equal 1/p. A sportsbook selection additionally needs an official executable price and a predeclared minimum edge; none is available here.
4. Evaluation
Use Brier score and log loss for probabilities, plus margin/total MAE for point forecasts. Compare with the frozen training team1 base rate and training total on exactly the same test games. A lower Brier score alone does not establish calibration or profitability. Show reliability bins and sample counts before claiming calibration.
Brier = mean((p − y)²)
Log loss = −mean(y·log(p) + (1−y)·log(1−p))
EV per unit = p·(decimal−1) − (1−p)
Fair decimal = 1/p
5. Correlation and combinations
Pearson correlation uses sample covariance normalized by both standard deviations. Player residuals remove a fitted linear minutes relationship across the pooled sample. Binary dependence reports observed joint hits, the product of marginals, φ and joint/product lift. These are descriptive—not a full joint distribution. Same-game experiments resample paired training residuals; cross-game products are explicitly conditional on an unverified independence assumption.
6. Skill, luck and selection
There is no honest way to remove all luck. Freeze the full trial registry, prevent leakage, use matched baselines, resample whole dates rather than individual games, control the complete hypothesis family, and require prospective multi-season replication. Suppress the planned bootstrap interval below 20 distinct dates. Even a valid interval would not capture every regime change or hidden dependency.
The Holm primitive is tested but no family-wise significant strategy claim is made: the pilot lacks the required sample and price series. Deflated Sharpe is not computed from invented returns. The financial-paper thresholds are not copied into NBA as official facts.
7. Settlement and risk
Settlement must use the operator and market rules in force when the price was accepted. Pushes and voids can reduce a ticket's multiplier; a loss loses the ticket. The engine tests these mechanics but does not assert universal sportsbook rules. Kelly is capped at 1% in the research primitive and is not a recommendation to stake. No actual wager is placed.
8. Release policy
All ten gates must pass. Missing evidence is unverified, never a pass. Forecast diagnostics may be ranked without rewards; betting eligibility and reward allocation require the full evidence chain. The current release has no eligible strategy.
Method references
Topic
Primary reference
Use
Reference
NIST-COV
Mean Vector and Covariance Matrix
Sample covariance definition used in Pearson correlation. Does not verify any NBA correlation estimate.
Official source ↗
NIST-WILSON
Proportion Confidence Interval
Wilson interval reference; binomial intervals require independent trials and are not used to certify correlated parlays.
Official source ↗
SK-TIME
TimeSeriesSplit
Chronological evaluation principle. This project implements its own date-split, not the library estimator.
Official source ↗
SK-CAL
Probability calibration
Separate proper scores from calibration diagnostics; no calibration claim from Brier alone.
Official source ↗
SK-METRICS
Metrics and scoring: quantifying the quality of predictions
Probability score definition, not a sports edge test.
Official source ↗
NBER-MULTIPLE
... and the Cross-Section of Expected Returns
Multiple-testing risk; the page discusses a t-ratio above 3 in its financial-factor setting. That cutoff is not transferred to NBA as a validated threshold.
Official source ↗
DSR
The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality
Selection bias and non-normal returns. DSR is not computed here because there are no verified wager return series.
Official source ↗
No matching entries.

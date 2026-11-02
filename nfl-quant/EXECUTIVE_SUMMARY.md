# Executive Summary — NFL Quant Lab (Own4)

Session arena-e513f51b-own4 · 2026-11-02 · live site: https://sassnarep3-star.github.io/Own4/nfl-quant/

## What was built
A reproducible NFL line-origination + strategy-validation pipeline: 7,548 archived games (1999–2026),
walk-forward ridge ratings, 5 registered betting strategies + 3 research-only constructions, 8 pre-registered
validation gates, a 16-estimate correlation study, and a 15-game 2026 Week 9 own-line slate.
15/15 data-integrity checks and 13/13 official NFL.com score spot-checks pass.

## Headline results (computed; vs archived closing lines — third-party, not official)
- Forecast skill: model holdout MAE 10.326 pts beats naive 11.11 but not the market 9.871.
- S1 spread divergence: 1,599 bets, ROI 0.26%, CI [-4.40%, 4.84%] -> Bronze (luck).
- S4 cross-game parlays: 7,635 bets, ROI 0.03% -> Bronze. S2/S3/C1 Rejected (negative).
- Strategies passing all gates: 0. Reward points awarded: 0 of 1,000 (non-monetary).
- Correlations: QB1->WR1 r=0.667; QB-over+WR1-over combo lift 1.45x [1.36,1.55]; favorite-cover vs over ~independent.
- Current HFA estimate 1.12 pts (declining from ~3).

## How luck is removed
Chronological dev/validation/holdout splits with frozen config; look-ahead perturbation test (pass);
week-clustered bootstrap CIs; matched-random permutation + Holm across the primary family; 500-placebo
calibration (mean ROI -2.99%, 8.0% positive by chance);
season-stability checks; G8 forward replication pending.

## Limits / flagged (non-blocking)
No strategy beats closing lines; props use a proxy market (G7 fails); 2026 props blocked; all market lines
third-party; computed metrics not official; data licensing needs review; README conflict markers repaired at
integration (both sides kept). See site Flagged for Review page (15 items).

## Reproduce
python3 nfl-quant/pipeline/01_provenance.py && ... && python3 nfl-quant/pipeline/07_verify_publish.py
python3 nfl-quant/site/build_site.py

Analytical research only, not wagering advice. NCPG Helpline 1-800-MY-RESET (1-800-697-3738).

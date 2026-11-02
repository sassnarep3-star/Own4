# Executive Summary — NFL Line Origination & Signal Research

**Date:** 2026-11-02 · **Status:** Research snapshot; no validated betting edge · **Rewards:** 0 points, virtual badges only

## Decision

Publish the official-only NFL dashboard and blocked-release evidence. Do **not** publish betting recommendations, market edges, ROI claims or reward winners. No strategy passed every pre-registered gate.

| Entry | Finding / analysis | Source |
|---|---|---|
| Scope | NFL only. Legacy NBA content is preserved as an archive and is not reused as NFL evidence. | [Repository](https://github.com/sassnarep3-star/Own4) |
| Official inputs | 392 final games, 96 standings rows, 28 player-game rows; 9 missing player cells preserved blank. All 320 team-season W/L/T/PF/PA cells reconcile to official standings. | [NFL standings](https://www.nfl.com/standings/league/2026/REG) |
| Leakage control | 314 chronological evaluation games across 21 season-weeks. Perturbing final-week scores leaves every earlier prediction unchanged. | [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) |
| Singles skill | M2 win-share Brier 0.23102 vs prior baseline 0.25406; M4 margin MAE 10.284 vs 10.726. These are probability metrics, not betting ROI. | [Calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| Luck / multiplicity | Whole-week bootstrap, sign-flip permutation null and Holm correction across six primary trials. No primary trial survives Holm at 0.05. | [False discovery control](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html) |
| Parlays | Cross-game favorite-pair dependence is near zero; the joint model does not beat an independent product with a positive lower confidence bound. Same-game spread/total joint probability is model-implied only. | [NIST correlation](https://www.itl.nist.gov/div898/handbook/ppc/section1/ppc136.htm) |
| Player props | Official 2026 logs support descriptive fair lines only. Every player market fails the 100-observation gate; cross-player same-game correlation is blank/blocked. | [Official player logs](https://www.nfl.com/players/jaxon-smith-njigba/stats/logs/2026/) |
| Current research line | CHI at SEA: M2 CHI +2.5 / SEA −2.5, total 46.5, SEA fair win-share 66.9%. Market odds and edge remain blank. | [NFL Game Center](https://www.nfl.com/games/bears-at-seahawks-2026-reg-8) |
| Release gates | G08 executable market edge, G09 availability/operations and G10 prospective replication remain blocked. | [Protocol](https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/protocol.json) |
| Leaderboard | 0 eligible strategies, 0 reward points. No winner is manufactured. | [Leaderboard](https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/results/leaderboard.json) |

## What this does not show

- It does not show a sportsbook edge: no verified executable odds, de-vigged probabilities, settlement terms, CLV or net ROI archive was available.
- It does not remove sport randomness. The controls reduce leakage, selection and dependence artifacts; they do not guarantee future profits.
- It does not certify legacy NBA or third-party NFL Quant claims as official NFL evidence. Those contributions are preserved and inventoried separately.
- It does not clear production data licensing or provide point-in-time injury/lineup guarantees.

## Dashboard

- [Canonical NFL dashboard](https://sassnarep3-star.github.io/Own4/)
- [Originated lines](nfl-lab/site/pages/own-lines.html)
- [Validation gates](nfl-lab/site/pages/validation.html)
- [Correlations & luck](nfl-lab/site/pages/correlations.html)
- [Flagged for review](nfl-lab/site/pages/flagged.html)
- [Repository audit](nfl-lab/site/pages/repository-audit.html)

## Responsible gambling

Research only — not wagering advice. National Problem Gambling Helpline: [1-800-MY-RESET](https://www.ncpgambling.org/help-treatment/).

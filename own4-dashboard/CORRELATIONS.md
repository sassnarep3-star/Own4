# CORRELATIONS.md — Determined Correlation Values

**Method:** Pearson r and Spearman rho on official NBA.com values. Two-sided permutation p-value (20,000 shuffles, seed 20261102). Percentile bootstrap 95% CI (5,000 resamples, seed 20261102). Benjamini-Hochberg FDR q across all 24 reported correlations.

All 24 correlations use only values transcribed from official NBA.com pages. No value is
inferred. `q` is the Benjamini–Hochberg FDR-adjusted value across the whole family.

| Pair (y ~ x) | n | Pearson r | Spearman rho | perm. p | BH q | bootstrap 95% CI | sig. after FDR | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-26 WIN% ~ NetRtg | 30 | 0.971 | 0.951 | 0.0000 | 0.0001 | 0.943 … 0.987 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 WIN% ~ OffRtg | 30 | 0.890 | 0.898 | 0.0000 | 0.0001 | 0.829 … 0.939 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 WIN% ~ DefRtg | 30 | -0.887 | -0.837 | 0.0000 | 0.0001 | -0.954 … -0.781 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 WIN% ~ PACE | 30 | -0.370 | -0.390 | 0.0424 | 0.0536 | -0.629 … -0.065 | no | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 NetRtg ~ PACE | 30 | -0.381 | -0.384 | 0.0378 | 0.0504 | -0.669 … -0.041 | no | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 OffRtg ~ PACE | 30 | -0.408 | -0.449 | 0.0255 | 0.0406 | -0.705 … -0.041 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2025-26 OffRtg ~ DefRtg | 30 | -0.677 | -0.717 | 0.0000 | 0.0001 | -0.830 … -0.478 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2026-27 WIN% ~ NetRtg | 30 | 0.886 | 0.876 | 0.0000 | 0.0001 | 0.794 … 0.946 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 WIN% ~ OffRtg | 30 | 0.699 | 0.701 | 0.0000 | 0.0001 | 0.465 … 0.877 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 WIN% ~ DefRtg | 30 | -0.744 | -0.755 | 0.0000 | 0.0001 | -0.857 … -0.583 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 PTS ~ NetRtg | 30 | 0.624 | 0.668 | 0.0003 | 0.0007 | 0.441 … 0.782 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 PTS ~ PACE | 30 | 0.400 | 0.413 | 0.0270 | 0.0406 | 0.057 … 0.658 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 NetRtg ~ PACE | 30 | -0.263 | -0.125 | 0.1594 | 0.1913 | -0.593 … 0.199 | no | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 NetRtg ~ +/- (traditional) | 30 | 0.999 | 0.998 | 0.0000 | 0.0001 | 0.998 … 0.999 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| 2026-27 WIN% ~ 2025-26 NetRtg | 30 | 0.480 | 0.495 | 0.0072 | 0.0145 | 0.149 … 0.750 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2026-27 NetRtg ~ 2025-26 NetRtg | 30 | 0.417 | 0.414 | 0.0223 | 0.0383 | 0.098 … 0.683 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2026-27 WIN% ~ 2025-26 WIN% | 30 | 0.483 | 0.521 | 0.0068 | 0.0145 | 0.144 … 0.755 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2026-27 PACE ~ 2025-26 PACE | 30 | 0.449 | 0.495 | 0.0126 | 0.0233 | 0.127 … 0.696 | YES | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 2026-27 PTS ~ 2025-26 NetRtg | 30 | 0.062 | 0.084 | 0.7442 | 0.8063 | -0.252 … 0.453 | no | [NBA.com official](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| Prop leg RPG ~ PPG | 28 | -0.065 | 0.001 | 0.7419 | 0.8063 | -0.472 … 0.383 | no | [NBA.com official](https://www.nba.com/games?date=2026-11-04) |
| Prop leg APG ~ PPG | 28 | -0.018 | -0.066 | 0.9273 | 0.9273 | -0.404 … 0.341 | no | [NBA.com official](https://www.nba.com/games?date=2026-11-04) |
| Prop leg APG ~ RPG | 28 | 0.056 | 0.040 | 0.7727 | 0.8063 | -0.321 … 0.423 | no | [NBA.com official](https://www.nba.com/games?date=2026-11-04) |
| 2026-27 HOME WIN% ~ OVERALL WIN% | 30 | 0.841 | 0.851 | 0.0000 | 0.0001 | 0.729 … 0.916 | YES | [NBA.com official](https://www.nba.com/standings) |
| 2026-27 ROAD WIN% ~ HOME WIN% | 30 | 0.380 | 0.414 | 0.0368 | 0.0504 | 0.121 … 0.611 | no | [NBA.com official](https://www.nba.com/standings) |

## Findings

- **Full-season structure:** 2025-26 `WIN% ~ NetRtg` r = `0.971`
  (n=30, 82 GP each) — [official source](https://www.nba.com/stats/teams/advanced?Season=2025-26). This is a descriptive identity-like
  relationship, not a betting edge.
- **Cross-table check:** 2026-27 `NetRtg ~ +/-` r = `0.999`
  across two independent official tables, confirming transcription consistency —
  [advanced](https://www.nba.com/stats/teams/advanced?Season=2026-27) · [traditional](https://www.nba.com/stats/teams/traditional?Season=2026-27).
- **Out-of-sample predictive signal:** `2026-27 WIN% ~ 2025-26 NetRtg` r =
  `0.480`, q =
  `0.0145` — [official source](https://www.nba.com/stats/teams/advanced?Season=2025-26).
- **Parlay leg dependence:** 2026-27 `PTS ~ NetRtg` r =
  `0.624` and `PTS ~ PACE` r =
  `0.400` — same-game legs are **not** independent.
- **Prop-leg baselines (n=28 official team leaders):** `RPG ~ PPG` r =
  `-0.065`, `APG ~ PPG` r =
  `-0.018`, `APG ~ RPG` r =
  `0.056`; all q > 0.05 —
  [official source](https://www.nba.com/games?date=2026-11-04). These are *baseline* correlations, not game-level leg
  covariances, which remain UNVERIFIED.

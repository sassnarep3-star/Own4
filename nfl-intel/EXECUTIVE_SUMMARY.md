# NFL Intelligence — Executive Summary (2026-11-12)
Session `arena/8184197d-own4` · branch `arena/8184197d-own4` · base `a10610b`

## Headline
A complete, source-linked NFL research build exists at `nfl-intel/` (site + engine + data). It originates fair lines for all 14 Week 10 games from **official NFL.com data only**, pre-registers 8 strategies behind 10 validation gates with explicit luck-removal, and — honestly — **awards zero rewards: no strategy passes the gates**. Two gaps block everything downstream: **no official odds/line archive** and **no official player game-log feed** in this workspace. Both are flagged as owner decisions/Suggestions, not worked around.

## Verified this session (official sources, fetched 2026-11-12)
| Item | Result | Source |
|---|---|---|
| Standings, 32 teams | Consistency gate **PASS** (W=L=135, PF=PA=6246, NET/PCT recomputed ✓) | https://www.nfl.com/standings/ |
| Week 10 slate & byes | 14 games; bye CHI/DEN/PHI/TB | https://www.nfl.com/scores |
| Week 10 injury report | 6 explicit game statuses (Out/Questionable) transcribed exactly; 68 DNP/LP watchlist rows; backup identity **UNVERIFIED** everywhere | https://www.nfl.com/injuries/ |
| nfl-lab peer data audit | 120 games internally consistent (0 mismatches vs its standings CSV) | nfl-lab/data/games_2026.csv |
| Secrets scan | 0 hits | repo-wide pattern scan |

## Originated lines (model v1, pre-registered 2026-11-12)
Expected score = mean(own OFF/g, opponent DEF/g); margin = home−away; total = Σ; P(home) ~ Normal(margin, σ=13.45 **UNVERIFIED**); no explicit HFA term; neutral-site W10-02 (NE–DET, Munich banner) handled implicitly. **Every line is UNVERIFIED vs market** (G7 blocked). Examples: W10-01 WAS@NYG fair margin NYG −2.5, total 45.5; W10-12 SF@DAL margin SF −4.4; W10-13 PIT@CIN margin CIN −1.8.

## Correlations (season-to-date, n=32; BH-FDR across 6 tests)
net PPG vs PCT **r=+0.876** (q≈0) · OFF/g vs PCT **r=+0.694** (q=1.6e-05) · DEF/g vs PCT **r=−0.666** (q=3.7e-05) · OFF vs DEF **r=−0.206** (q=0.257) · OFF vs net **r=+0.802** · DEF vs net **r=−0.750** — all descriptive only; prop-pair correlations **BLANK/UNVERIFIED**.

## Validation gates (G1–G10)
PASS: G1 provenance, G2 pre-registration, G6 registry, G10 FDR design. NOT REACHED: G4 baselines, G5 calibration. FAIL: G3 (n≪300), G9 (prop combos — no data). BLOCKED: G7 market comparison, G8 costs/settlement. **Leaderboard pays 0.**

## What the owner must decide (blocking)
1. Confirm rewards stay **virtual** (default) — else counsel review required (Q-07/Q-11).
2. Fund licensed odds archive + official player logs (unblocks G7/G8/S6) — Q-05/Q-06.
3. Approve depth-chart ingestion (unblocks injury-adjusted S4′) — SUG-01/Q-03.
4. Canonical site decision (root vs nfl-intel vs legacy NFL namespaces) — Q-12/SUG-08.
5. Reviewer + cadence for the Suggestions register — Q-13/SUG-09.

## Key flags (full list: `pages/flagged.html`, 16 items)
σ=13.45 unverified (F-02) · Pythag exponent unverified (F-01) · moneylines unverified vs market (F-03) · NE–DET venue (F-04/F-15) · injury backup mapping (F-05) · DNP≠Out (F-06) · season-to-date correlations (F-07) · 0-reward honesty (F-09/F-16) · repo hygiene: 4 tracked .pyc, ~53 MB raw dumps, no LICENSE, namespace sprawl (F-11/F-12).

## Verification & reproducibility
`python3 nfl-intel/engine/analyze.py` (recomputes metrics/correlations/lines) → `python3 nfl-intel/engine/build_site.py` → `python3 nfl-intel/engine/verify_site.py` (**PASS: 16 pages, 224 data-rows, all sourced; 326 local links OK**). Not wagering advice. NCPG Helpline 1-800-MY-RESET.

# NFL Core Requirements — Executive Summary

**Workspace:** `nfl-core/` · **Session:** arena-a437d20c-own4 · **Date:** 2026-11-14 ·
**Verification:** `python3 nfl-core/verify.py` (line-by-line; see `nfl-core/pages/sources.html`)

---

## Bottom line

The eight core requirements are now implemented end-to-end as working data stores and published
pages. The system records **opening and closing numbers for every market it originates**, and a
**verified results feed** — reconciled cell-by-cell against the official NFL standings read
2026-11-14 — makes backtests and ROI computable at all. The leaderboard **ranks signal quality
only** (a lucky staking run cannot mask a bad signal), replacement **depth strings** are tracked
alongside injury facts, every correlation publishes its **n**, and a four-part **demotion gate**
sends any live strategy back to paper on defined triggers.

**The honest skill picture:** no strategy has yet cleared the luck barrier (best
Benjamini–Hochberg-adjusted p = 0.44 on the strongest candidate: unders in outdoor games with
wind ≥ 15 mph, n = 303, hit rate 55.4%, z = 1.43). Nothing is live; nothing is rewarded. The
competition is open and the gates are armed.

## Requirement-by-requirement status

| # | Requirement | Where | State |
|---|-------------|-------|-------|
| 1 | Price-snapshot store (open + close per market) | `data/price_snapshots_2026.csv`, `pages/prices.html` | 816 markets: 81 with OPEN (weeks 10–11 captures), 411 with CLOSE + settlement (every settled market). Unsettled rows carry OPEN only; weeks 1–9 opens blank + flagged (F-C02) |
| 2 | Verified results feed (backtests + ROI computable) | `data/results_feed_2026.csv`, `pages/results.html` | 272 games (137 final), every row on its official nfl.com game URL; 32/32 teams exact vs official standings |
| 3 | Origination order: side → total → moneyline | `data/originations_2026.csv` | 136 games × 3 markets, `origination_seq` 1/2/3 enforced by verify.py |
| 4 | Fair line / market line / difference as separate columns | same | three separate columns per market; difference = fair − market (ML in win-probability points) |
| 5 | Signal separated from staking | `pages/leaderboard.html` | two tables; rank = z vs break-even at flat stakes only (V7 enforces the sort) |
| 6 | Replacement depth, not just the fact | `data/depth_week10.csv`, `pages/depth.html` | replacement name + string (2nd/3rd/4th) from official club charts; blanks flagged |
| 7 | Correlations from officially sourced numbers, n published | `data/correlations_n.csv` | every r carries n; price-input rows labeled; player-level rows blank + flagged |
| 8 | Demotion gate (live → paper) | `data/gates.csv`, `pages/gates.html` | DG-1 skill regression · DG-2 negative CLV · DG-3 drawdown · DG-4 data integrity — armed |

## What is solid (verified today against official sources)

- **Results feed reconciliation:** W-L-T and PF-PA recomputed from the feed for all 32 teams and
  matched exactly to the [official standings](https://www.nfl.com/standings/league/2026/REG)
  (ΣW = ΣL = 136, ΣT = 2 = 137 games). Game-URL slugs verified against live nfl.com pages.
- **Spread convention settled** (old flag A-06 / question Q-05): positive `spread_line` = home
  favored by that many points — quoted from
  [nflverse DATASETS.md](https://github.com/nflverse/nfldata/blob/master/DATASETS.md) and
  corroborated by 162/163 moneyline-consistency checks on 2026 games. The WAS@NYG "1.5 vs 2.5"
  mystery is ordinary open→close movement (now visible in the price store).
- **Depth-chart source corrected** (old flag A-12): official club sites DO publish unofficial
  depth charts ([detroitlions.com](https://www.detroitlions.com/team/depth-chart),
  [patriots.com](https://www.patriots.com/team/depth-chart), read 2026-11-14). The league-level
  nfl.com route remains 404; charts label themselves "unofficial".
- **Week-10 deficiency picture** (official injury report, read 2026-11-14): Minnesota plays
  without QB1 Kyler Murray (backup depth string unverified → blank), Green Bay without Josh
  Jacobs, Micah Parsons and C Sean Rhyan; Detroit without C Cade Mays (→ 2nd-string C Juice
  Scruggs) and CB D.J. Reed (→ 2nd-string CB Rock Ya-Sin); New England without LG/C Ben Brown
  (→ 2nd-string LG Walter Rouse, and the only backup center).

## What is deliberately blank (never inferred)

1. Opening lines for 2026 weeks 1–9 — no capture exists in any source (F-C02). The store holds
   the closes and settles against them; the open cells wait for evidence (S-C02).
2. Player-prop prices — the NFL publishes none (A-13). Prop rows and prop correlations are
   blank + flagged; official player game logs exist and are cited where relevant.
3. Replacement depth where a club's own chart does not answer (e.g., no S listed behind Kerby
   Joseph; MIN QB naming) — blank + flagged F-C08.

## Decisions the owner must make (nothing is implemented ahead of a choice)

- **S-C04:** sign off (or change) the demotion-gate thresholds — currently project-defined.
- **S-C02 / D2:** license or script a dated opening/closing line feed (closes Q-C01).
- **S-C09:** reward funding — recommended to defer until a strategy passes G4.
- All nine open suggestions with options and recommended paths: `pages/suggestions.html`.

## Rewards & leaderboard policy (competition design)

Strategies compete on **signal rank** (z vs break-even at flat stakes, BH-corrected). Rewards are
gated behind G4 (BH p < 0.05) + G5 (positive confirmation ROI, n ≥ 100) — currently **0 of 15
strategies eligible**. Staking is deliberately unplugged from the ranking; the staking table
publishes ROI/drawdown separately and can never promote a weak signal.

---

*Every figure in this summary is source-linked on the site (`nfl-core/pages/`). Anything not
confirmable is blank and flagged on the [Flagged for Review](nfl-core/pages/flagged.html) page —
nothing was inferred or filled in.*

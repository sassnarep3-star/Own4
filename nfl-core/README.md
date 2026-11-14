# nfl-core — NFL core requirements workspace

Session `arena-a437d20c-own4` · built 2026-11-14 · every figure source-linked ·
nothing inferred (unconfirmable values are blank and flagged).

This workspace implements the eight core requirements end-to-end:

| Requirement | Store | Page |
|---|---|---|
| Price snapshots (open + close per market) | `data/price_snapshots_2026.csv` | `pages/prices.html` |
| Verified results feed (backtests + ROI computable) | `data/results_feed_2026.csv` | `pages/results.html` |
| Origination: side → total → moneyline | `data/originations_2026.csv` | `pages/origination.html` |
| Fair line / market line / difference columns | `data/originations_2026.csv` | `pages/origination.html` |
| Signal separated from staking | `data/leaderboard_signal.csv`, `leaderboard_staking.csv` | `pages/leaderboard.html` |
| Replacement depth (string of the replacement) | `data/depth_week10.csv` | `pages/depth.html` |
| Correlations with n, officially sourced inputs | `data/correlations_n.csv` | `pages/correlations.html` |
| Demotion gate (live → paper) | `data/gates.csv` | `pages/gates.html` |

Plus: `pages/questions.html` (decision register: known / missing / what settles it),
`pages/suggestions.html` (review-and-choose board — nothing is implemented until the owner
chooses), `pages/flagged.html` (Flagged for Review), `pages/sources.html` (verification
method and every source read), `pages/executive-summary.html` +
[`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

## Conventions (verified, citable)

- **Spread sign:** a positive `spread_line` means the **home team was favored** by that many
  points (nflverse [DATASETS.md](https://github.com/nflverse/nfldata/blob/master/DATASETS.md),
  quoted in `data/official_reads_2026-11-14.json` OR-06; corroborated by 162/163
  moneyline-consistency checks on 2026 games).
- **Market prices are third-party** (the NFL publishes no odds) and are labeled
  `THIRD-PARTY-*` everywhere. Scores/standings/injuries/depth-charts are official
  (nfl.com or official club sites) and labeled `OFFICIAL`.
- **Never infer:** a value without a source is blank and flagged. Example: weeks 1–9 opening
  lines do not exist in any source (F-C02) — the cells stay blank.

## Reproduce

```bash
python3 nfl-core/build_data.py   # upstream archives + official reads -> data/*.csv
python3 nfl-core/build_site.py   # data/*.csv -> index.html + pages/*.html
python3 nfl-core/verify.py       # 11 line-by-line checks; exits non-zero on any failure
```

`verify.py` enforces: source-link coverage on every table row (1,614 rows at build), internal
link integrity, **cell-by-cell reconciliation of the results feed against the official
standings** (32/32 teams, W-L-T and PF-PA exact), the never-infer blank policy, price-store
invariants, origination order 1→2→3 with exact difference arithmetic, and that the leaderboard
is sorted by signal z only.

## Sources read live on 2026-11-14 (transcribed in `data/official_reads_2026-11-14.json`)

- https://www.nfl.com/standings/league/2026/REG (32 rows)
- https://www.nfl.com/games/commanders-at-giants-2026-reg-10 (final 24-21, quarter box)
- https://www.nfl.com/injuries/ (week 10 report, chunks 0–1)
- https://www.detroitlions.com/team/depth-chart · https://www.patriots.com/team/depth-chart
- https://github.com/nflverse/nfldata/blob/master/DATASETS.md (column conventions)

## Known gaps (all flagged, none filled in)

- F-C02: opening lines for 2026 weeks 1–9 — no source exists.
- F-C12: market quotes for weeks 12–18 — not yet captured (fair lines only).
- F-C09: player-prop prices — the NFL publishes none.
- F-C08/F-C10: replacement depth strings for clubs whose official charts were not read.
- F-C06: rewards are project-defined and unfunded; 0 strategies eligible.

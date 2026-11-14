# nfl-markets — price snapshots, verified results, signal vs staking, replacement depth, correlations, demotion gate

Session `arena/65c4a22e-own4` · 2026-11-14 · branch `arena/65c4a22e-own4` · stdlib-only, deterministic.

**What this namespace adds (differentiated from the 15 peer NFL namespaces — surveyed before claiming):**
peer sessions shipped schemas, gates and registers with deliberately **empty** stores (see `nfl-ledger/` F-L1, blank
depth fields, copied correlations). This namespace **populates** the data-driven layer:

| Deliverable | Where |
|---|---|
| Price-snapshot store — 12,573 rows: every originated market per game (origination order **side → total → moneyline**), model fair line, market open, market close, `diff_open`, `diff_close` as separate columns, per-row sources + verification statuses | `data/price_snapshots.csv` · page `pages/price-snapshots.html` |
| Verified results feed — 4,056 played games 2011-2026, official nfl.com link per row, **32/32 standings reconciliation** vs the official capture, live NFC East spot check 4/4 | `data/results_feed.csv` · `pages/results-feed.html` |
| Leaderboard with **signal separated from staking** (separate columns, separate ranks; signal-first order) | `data/leaderboard.json` · `pages/leaderboard.html` |
| Validation gates MG-1..MG-8 + **demotion gate DM-1..DM-5** (live → paper state machine, demonstrated counterfactually on real windows: 47/32 triggers) | `data/gates_evaluation.json` · `pages/gates.html` |
| Replacement-**depth** tracker (2nd/3rd/4th/none per absent starter; official NFL.com report + flagged third-party depth charts; 24 teams blank + flagged) | `data/replacement_depth.json` · `pages/injuries.html` |
| Correlations with **n published**: official-input group (margins/totals/rest/division) + flagged third-party group (covers, leg dependence −1.19pp vs implied independence, n=27,129) | `data/correlations.json` · `pages/correlations.html` |
| Suggestions review queue + decisions register (known / unknown / how to discover) | `data/suggestions.json`, `data/decisions.json` · `pages/suggestions.html`, `pages/decisions.html` |
| Flagged-for-review (10 non-blocking flags with evidence + sources) | `data/flags.json` · `pages/flagged.html` |

## Reproduce

```bash
python3 nfl-markets/run_all.py          # regenerates every data file deterministically (SHA-256 manifest)
python3 nfl-markets/engine/build_site.py  # builds index + 12 pages
python3 nfl-markets/engine/verify.py      # row-source coverage, internal links, blank-flagging, invariants
python3 nfl-markets/tests/test_site.py    # 8 unit tests
```

`data/raw/provenance.json` records the exact upstream commit (nflverse/nfldata `c430522`, fetched 2026-11-14T21:36Z).
Peer captures under `nfl-arena/data/raw/` are reused **read-only** with provenance.

## Honest headline

Every implementable strategy matches or underperforms the closing market (best beat-close 50.31%, p=0.45; all flat-stake
ROI negative). **Zero rewards, nothing promoted** — the same conclusion as every prior session, now computed on a
populated store with signal/staking separation. The model's spread disagreement has *negative* line value (41.8%
beat-close, CI excludes 50%) — the market close is better than this model on sides. That is the finding the site leads
with, not hides.

## Labeling policy

OFFICIAL = published by the NFL (nfl.com). THIRD-PARTY = trusted archive (nflverse/nfldata, ESPN/RotoWire), always
labelled, never passed off as official. REPO = this repository's own files with provenance. Values without a
confirmable source are **blank and flagged** — never inferred. Research framework only; not wagering advice.

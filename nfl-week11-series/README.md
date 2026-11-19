# nfl-week11-series — Week 11 Series Desk (session arena-23197e9d-own4, 2026-11-19)

One dated execution round against the NFL brief's data requirements. Everything here is
derived from official pages read on 2026-11-19 via the platform page-read tool, transcribed
verbatim to `evidence/`, re-parsed by an independent engine (`engine/compute.py`), and
published by `engine/build.py` behind the gates in `engine/verify.py`.

**Site:** https://sassnarep3-star.github.io/Own4/nfl-week11-series/

## What was executed

| ID | Task | Result |
|----|------|--------|
| S1 | Board claim before implementation | done (`COORDINATION.md`, pushed first) |
| S2 | Live official reads with clock times (Week 11 report, Week 10 recount, Reserve/Other/Trades ledgers Oct+Nov, GB + HOU depth pages, Willis article) | done — `evidence/`, `data/sources.json` |
| S3 | Timestamped series capture_a→capture_b→capture_c with row-level deltas (REQ-21/53/54) | done — `data/series.json` |
| S4 | Week 10 recount vs the brief's stale counts (REQ-48) | done — 347 rows / 28 sections / 0 empty today |
| S5 | Reserve-list check (REQ-62): six contradictions + Willis case + ledger gap | done — `data/reserve_check.json` |
| S6 | Depth checks live (REQ-31/49/50): GB jersey-number recovery, empty/shared slots, HOU image-only | done — `data/depth_check.json` |
| S7 | Site + verifier + PR/merge/Pages | done — 12 pages, all gates green |

## Method (no manual input, no inference)

1. Pages read in full (every chunk); data tables transcribed cell-by-cell to CSV with per-row
   player URLs. Abbreviations are limited to the three practice strings the page publishes
   (DNP/LP/FP) and are expanded by the engine.
2. `engine/compute.py` re-parses the evidence and two peer capture files (sha256-checked
   before use) with code that shares nothing with the transcription.
3. `engine/build.py` renders the static site; `engine/verify.py` enforces: row sourcing
   (every table row carries an approved-host https link), link integrity, drift pins on
   evidence counts (REQ-61), capture hash integrity, byte-identical rebuild, and a
   banned-claim scan (no price/edge/ROI/CLV/win-rate claims outside rejection sentences).
4. Unverified values stay blank and appear on the Flagged for Review page. Nothing is
   inferred; no replacement, availability state, depth rank or starter is derived from
   absence, jersey number, or column order.

## Headline numbers (2026-11-19)

- Week 11 (11:25Z): 253 rows / 24 clubs with rows / 2 "No Injuries Reported" sections /
  16 game-status cells (9 Out, 7 Questionable — identical across three reads spanning 11.6 h).
- Week 10 (11:20Z): 347 rows / 28 sections / 0 empty — the brief's "254 rows / 4 sections"
  (repo) and "279 rows / 2 sections" (live-then) are both superseded; the page is a living
  document and every corpus must record its capture clock.
- Deltas: 11 Chargers rows appeared between 23:49Z and 11:25Z; 5 Eagles practice statuses
  moved 07:05Z→11:25Z; Will Lee III LP→FP (reversing yesterday's move); 1 display-name
  identity variant (De'Alford, Dee ↔ Dee Alford, same player URL); 0 game-designation changes.
- Reserve ledger (Nov): 25 rows; two 11/17 IR moves (Carlies, Al-Shaair) still contradict
  Thursday practice tables at 11:25Z. Willis (news: IR, Tue→2026-11-10) has **no row in any
  of three ledgers** (F-WS-01).

## Flagged for Review

11 items (3 high, 4 medium, 4 low) on the site's Flagged page — none blocks the merge; each
blocks a claim. Key items: F-WS-01 Willis ledger gap; F-WS-03 living Week-10 page;
F-WS-04 table-vs-ledger divergence; F-WS-05 HOU image-only depth; F-WS-11 one game of
designation coverage.

## Reproduce

```
python3 nfl-week11-series/engine/compute.py   # evidence -> data/*.json
python3 nfl-week11-series/engine/build.py     # data -> HTML
python3 nfl-week11-series/engine/verify.py    # publication gates (exit 0 = publish)
```

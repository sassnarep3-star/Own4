# Executive Summary — 32-Club Official Depth-Chart Sweep

**Session:** `arena/2388d73a-own4` · **Branch:** `arena/2388d73a-own4` · **Capture date:** 2026-11-17 (UTC)
**Namespace:** `nfl-depth-sweep/**` · **Base:** `ba30819` (main after PR #142)

## What this session delivered

The NFL brief required a depth-order source resolved **club by club**, a **32-team roster/IR sweep** before any
team-level model is trusted, and an **official depth-chart register with date + source per row**. Every prior
session left the depth layer empty (`nfl-book/data/depth_register.json` all-blank, RF-04 unresolved). This session
completed the full 32-club sweep:

1. **Capture (D2):** fetched the official `/team/depth-chart` route for all 32 clubs. **31 clubs returned
   machine-readable text** (verbatim transcripts stored with URL + fetch timestamp); **1 club (HOU) publishes its
   chart as a static image** and is flagged, never transcribed by eye.
2. **Register (D3):** built the depth-order register — **32 club rows, 705 position rows** (position / rank1 /
   rank2 / rank3) with source URL, fetch date, and page-stated snapshot date per row. Parser resolves both named
   failure modes: Packers jersey-number prepend (numbers captured and stripped) and Texans depth-as-image (blank +
   flagged).
3. **Roster/IR sweep (D4):** cross-checked the official league reserve list (November 2026) against the depth
   charts across all 32 clubs — **25 Reserve/Injured entries**, **5 stale-depth flags** where a reserve player
   still holds rank1, with replacement depth recorded for each.
4. **Readiness (D5), site (D6), verification (D7):** decision-readiness table with the gate + number that clears
   each requirement; a 36-page static site (landing, register, per-club pages, flagged-for-review, IR sweep) with
   every row source-linked; a verifier enforcing the row-source gate, broken-link checks, no-localhost, byte-level
   determinism, and cross-artefact consistency — plus a CI workflow.

## Headline results

| Metric | Value |
|---|---|
| Clubs swept | **32 / 32** |
| Text-verified transcripts | **31** (`data/raw/*.md`) |
| Flagged image-only | **1** (HOU — blank + flagged, source recorded) |
| Register rows | **32 clubs · 705 position rows**, date + source per row |
| Domain corrections | **17** official domains confirmed (short forms are unreliable) |
| Shared rank slots captured | **13 clubs** (both names kept, no order inferred) |
| Reserve/Injured entries (Nov 2026) | **25** across 17 clubs |
| Stale-depth flags (reserve cross-check) | **5** (LAR ×2, TEN ×3) |
| Additional stale-depth flag (page log) | **1** (LAC Derwin James Jr.) |
| Verification | **all gates green** (row-source, links, no-localhost, determinism, consistency) |

## Stale-depth flags (do not treat flagged rank1 as current depth)

- **LAC** — Derwin James Jr. listed S rank1; the page's own Latest Transactions log places him on IR.
- **LAR** — Puka Nacua (WR rank1, IR 11/12) and Jordan Whittington (KR rank1, IR 11/10).
- **TEN** — Peter Skoronski (LG rank1, IR 11/14) and Tommy Townsend (P rank1 / H rank1, IR 11/14).

Replacement depth for each is recorded in `data/roster_ir_sweep.json`.

## Key findings

- **The official depth route is real and uniform in concept, not in format.** Depth order is published by each
  club's communications staff at `/team/depth-chart`; formats vary (jersey-number prepend at GB, player links
  elsewhere, shared rank slots, sparse cells, per-club position naming). The parser handles every observed variant
  with warnings, never inference.
- **Domains are the trap.** `bills.com` is a finance site, `eagles.com` a shopify shop, `falcons.com` a shop,
  `cardinals.com` MLB, and `ravens.com`/`cowboys.com`/`rams.com`/`titans.com`/`bears.com`/`lions.com`/`saints.com`
  /`jets.com`/`dolphins.com`/`browns.com` fail or serve the wrong surface. The corrected map lives in
  `data/teams.json`.
- **Charts are dated snapshots.** Page-stated dates where published (CHI 10/31, GB/LV/SF/TEN 11/10); otherwise
  the capture date. IND republishes weekly. A single capture goes stale as rosters move — the sweep's own IR
  cross-check found five rank1 names on IR within days of capture.
- **One disclaimer matters:** NE's chart is explicitly writer-opinion ("reflects the opinions of the Patriots.com
  writers"), flagged for downstream consumers.
- **One snapshot caveat:** the 2026-11-17 BAL capture lists Jacoby Brissett at QB1; the brief's Lamar Jackson
  stale-depth case does not appear in this capture and is not conflated with it.

## Where things live

- Raw transcripts: `nfl-depth-sweep/data/raw/` (31 club transcripts + HOU flag + league reserve list)
- Parsed depth: `nfl-depth-sweep/data/parsed/*.json`
- Register: `nfl-depth-sweep/data/depth_register.json`
- Roster/IR sweep: `nfl-depth-sweep/data/roster_ir_sweep.json`
- Engines: `nfl-depth-sweep/engine/` (`parse_depth.py`, `build_register.py`, `roster_ir_sweep.py`,
  `build_site.py`, `verify.py`)
- Static site: `nfl-depth-sweep/site/` (36 pages)
- Readiness / Q&A / suggestions: `nfl-depth-sweep/data/{readiness,questions,suggestions}.json`

## Open item

**HOU** is the single remaining unverified row: its official depth surface is an image. A machine-readable
official Houston surface (text table, API, or official data feed) is the one input that would clear the depth
layer to 32/32 verified.

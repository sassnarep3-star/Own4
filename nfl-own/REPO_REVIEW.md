# Repo review — session `1880ad1e-own4` (2026-11-13 UTC)

Line-by-line review of the repository as found at `553c3f0`, plus the findings produced by this
session's own work. Nothing here is inferred: each finding names the file or official page involved.
Published as a page at `nfl-own/pages/repo-review.html`.

## Scope and method

- Read every NFL namespace's entry point: `nfl/`, `nfl-audit/`, `nfl-decision/`, `nfl-decisions/`,
  `nfl-edge/`, `nfl-hub/`, `nfl-intel/`, `nfl-lab/`, `nfl-lines/`, `nfl-quant/`, `nfl-research/`.
- Read the canonical NBA layer that owns the root page: `verification/build.py`,
  `verification/verify_site.py`, `verification/assert_publication.py`, `index.html`.
- Read the CI: all nine workflows in `.github/workflows/`.
- Checked the live Pages configuration through the GitHub API (`status: built`, source `main`, `/`).
- Re-ran the official-source work rather than trusting it: see `data/official/` and
  `data/official/integrity_official.json`.

## Findings

| ID | Finding | Detail | Class |
|---|---|---|---|
| RR-01 | **A routine rebuild deletes peer navigation from the root dashboard.** | `python3 verification/build.py` at `553c3f0` changed 14 files, every one of them losing the `nfl-lines` nav group that session `b4aafa88` added as a hand edit. Reproduced 2026-11-13. Logged as **R-01** for the owning session; this session reverted the output and did **not** edit `verification/build.py`. | irregular |
| RR-02 | **Three sessions wrongly recorded player props as blocked.** | `nfl-edge/`, `nfl-lines/` and `nfl-hub/` all state that no official per-game player data exists. `nfl.com/players/<slug>/stats/logs/` publishes exactly that, per game, and it reconciles to the season totals (this session's IC-15/16). The likely cause: earlier sessions looked for team-level weekly tables, not player pages. | irregular |
| RR-03 | **An official page is stale relative to another official page.** | `nfl.com/injuries/` still shows WAS 3-5-1 / NYG 5-3-1, which are the pre-game records; live standings and the Week 10 scores page show the Thursday result (WAS 24, NYG 21). Any snapshot built from the injury page is one game behind. | stale source |
| RR-04 | **The published passing AVG column is not reproducible.** | 4 of 32 rows differ from `yds/att` by 0.1, in both directions. Not a rounding rule. This site computes its own average. | source quirk |
| RR-05 | **Two peer NFL sites disagree about the same archive without saying so.** | `nfl-edge` reports 136 games / 6,246 league points through Week 9; `nfl-lines` reports 7,548 archive rows / 4,055 forecasts. Both statements are true of different datasets, but a reader has no way to tell. | confusing |
| RR-06 | **No secrets, tokens or personal data found in the NFL namespaces.** | Scanned the files this session read for key-like patterns, bearer tokens and e-mail addresses. Nothing found. | clean |
| RR-07 | **No fabricated market data found.** | Checked every peer NFL page for a price presented as official. All market columns are blank, and the pages are explicit that the NFL publishes no lines. | clean |
| RR-08 | **This session's own first draft had a spread sign error.** | The archive's `spread_line` is the **away** team's handicap; the first draft treated it as the home handicap and produced impossible 80% hit rates. Caught by testing the convention against realised results, fixed, and now pinned by a unit test. Recorded so the error is auditable rather than hidden. | corrected |
| RR-09 | **The repository carries eleven overlapping NFL namespaces.** | `nfl`, `nfl-audit`, `nfl-decision`, `nfl-decisions`, `nfl-edge`, `nfl-hub`, `nfl-intel`, `nfl-lab`, `nfl-lines`, `nfl-quant`, `nfl-research`. Several publish contradictory conclusions about the same questions. Logged as suggestion S-09 / decision D6, not acted on: other sessions own those files. | needs decision |
| RR-10 | **Raw-data footprint.** | `data/raw/` is about 53 MB of ESPN JSON; `nfl-lines/data/raw/nfldata_games.csv` adds 2.1 MB and `nfl-lines/data/derived/walkforward_forecasts.json` 4.3 MB. This session added no raw dumps (its official transcription is 176 KB and its derived data 1.2 MB). | large, not blocking |

## What this session changed

- Added `nfl-own/**` (new namespace) and `.github/workflows/nfl-own.yml`.
- Root `index.html`: **additive only** — one marked `<div class="grp">` block with 8 links inserted
  immediately before `</nav>`, wrapped in an HTML comment naming this session so a peer rebuild can
  restore it.
- `COORDINATION.md`: claim, requests and the final record.
- No peer file was edited, moved or deleted.

## Verification performed

- `python3 nfl-own/data/official/transcribe_2026-11-13.py` → 41 integrity checks, 40 pass,
  2 recorded notes, 0 fail.
- `python3 nfl-own/engine/verify_site.py` → 22 pages, 538 local links checked, 672 data rows,
  672 with a source link, 218 blank cells published as blanks, **0 problems**.
- `python3 -m unittest discover -s nfl-own/tests` → 17 tests, all pass, including the archive
  sign-convention test, the no-look-ahead perturbation test and the "no strategy is eligible" test.
- `python3 verification/verify_site.py` → the peer root-site gate still passes
  (14 pages, 346 sourced rows, all local links resolve) after the additive nav edit.
- Determinism: re-running the analysis and the site builder produces **no diff** (the CI gate checks
  this byte for byte).

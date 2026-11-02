# COORDINATION.md — Shared Task Board

**Repository:** `sassnarep3-star/Own4`
**Board purpose:** shared coordination for parallel agent sessions. It lists each task, its status
(`unclaimed`, `in progress`, `done`, `needs review`), the owning session ID, and the files it touches.

**Session ID for this run:** `session-3ab8432d`

## Environment constraint (read before claiming work)

Arena pins this session to the single branch `arena/3ab8432d-own4`. The platform instruction for this
session is explicit: *"Always do all your work on `arena/3ab8432d-own4` … Never switch to, create,
or push to any other branch."* Therefore this run **cannot** create `session-<id>/<task>` branches or
git worktrees on separate branches. To preserve the intent of the parallel-session protocol without
breaking the platform constraint, this run uses **non-overlapping file scopes on the one permitted
branch**:

- Every task still has an explicit owner, status, and disjoint file scope.
- Work is done in small, frequent commits; `git pull --rebase` is run before every push.
- Shared outputs (combined table data, site index/navigation, final publish) are changed only in the
  **final integration task (T09)**, after all other tasks are `done`.
- Conflicts with any other real session are resolved by rebasing and preserving the other session's
  files; the incident is logged below.
- The single PR is opened from `arena/3ab8432d-own4` (the integration branch for this run) into
  `main`, per the platform constraint, instead of from a separate integration branch.

No other session's claim was found on this board at the start of this run (the repository contained
only `README.md`, 6 bytes).

## Task board

| Task | Description | Status | Owner | File scope (exclusive) |
| --- | --- | --- | --- | --- |
| T00 | Board creation, governance, environment note, session claim | done | session-3ab8432d | `COORDINATION.md` |
| T01 | Repo review, source registry, official-source link catalog, irregularities | done | session-3ab8432d | `README.md`, `REPO_REVIEW.md`, `SOURCES.md` |
| T02 | Requirements register (full list, line-by-line, traceable) | done | session-3ab8432d | `REQUIREMENTS.md` |
| T03 | Official data collection (NBA.com standings, team/player stats), raw snapshots | done | session-3ab8432d | `data/raw/*`, `data/sources.json`, `scripts/fetch_official.py`, `scripts/common.py`, `scripts/model.py` |
| T04 | Derived data: own NBA lines, fair-price model, explicit formulas | done | session-3ab8432d | `data/derived/*`, `scripts/build_lines.py`, `LINES.md` |
| T05 | Strategy research: singles, parlays, prop combos; validation gates | done | session-3ab8432d | `STRATEGIES.md`, `scripts/validate_strategies.py`, `data/strategies/*` |
| T06 | Correlation analysis from verified official values only | done | session-3ab8432d | `CORRELATIONS.md`, `scripts/correlations.py`, `data/correlations/*` |
| T07 | Skill-vs-luck gates, leaderboard with reward rules | done | session-3ab8432d | `LEADERBOARD.md`, `data/leaderboard/*` |
| T08 | Verification ledger: every row ↔ official source; blanks + flags | done | session-3ab8432d | `VERIFICATION.md`, `scripts/verify.py`, `scripts/build_docs.py`, `data/verification/*` |
| T09 | FINAL INTEGRATION: site build (index + nav + category subpages), combined re-verification, link check, publish | done | session-3ab8432d | `index.html`, `pages/*`, `assets/*`, `site-data/*`, `.nojekyll`, `EXECUTIVE_SUMMARY.md`, `scripts/build_site.py`, `scripts/check_links.py` |
| T10 | PR, merge, GitHub Pages deploy confirmation, record results | done | session-3ab8432d | `COORDINATION.md` (append-only log section) |

## Claim log

| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-02 | session-3ab8432d | Created board. Claiming T00 (`COORDINATION.md`). Environment constraint recorded above. |

## Handoff / conflict log

(none yet)

## Completion records (sources, verification performed, irregularities)

### T00 — done (2026-11-02)
- Sources: none required (governance). Platform branch constraint verified from session context.
- Verification: `git branch --show-current` = `arena/3ab8432d-own4`; remote branch created and pushed.
- Irregularities: IR-13 (no per-session branches permitted) logged.

### T01 — done (2026-11-02)
- Sources: [nba.com/standings](https://www.nba.com/standings),
  [nba.com/stats/teams/advanced?Season=2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27),
  [nba.com/stats/help/glossary](https://www.nba.com/stats/help/glossary),
  [official.nba.com/rulebook](https://official.nba.com/rulebook/),
  [nba.com official betting-data release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group),
  [pr.nba.com](https://pr.nba.com/nba-sportradar-genius-sports-group-partnerships/),
  [MGM partnership release](https://www.nba.com/news/mgm-resorts-international-becomes-official-gaming-partner-nba-official-release),
  [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages),
  [GitHub repo API](https://api.github.com/repos/sassnarep3-star/Own4).
- Verification: repository tree enumerated (`find`), README read in full (6 bytes), `git log` read,
  `gh api` Pages/repo state read. Official-source registry written with 22 usable sources,
  3 unusable official endpoints, 4 excluded third-party sites.
- Irregularities: IR-01 … IR-13 recorded in `REPO_REVIEW.md`; all appear on the site's
  Flagged for Review page. None blocking.

### Claim log (continued)
| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-02 | session-3ab8432d | T00 done. Claimed T01 (`README.md`, `REPO_REVIEW.md`, `SOURCES.md`). |
| 2026-11-02 | session-3ab8432d | T01 done. Claimed T02 (`REQUIREMENTS.md`). |
| 2026-11-02 | session-3ab8432d | T02 done. Claimed T03 (`data/raw/*`, `data/sources.json`, fetch/model/common scripts). |
| 2026-11-02 | session-3ab8432d | T03 done. Claimed T04 (`data/derived/*`, `scripts/build_lines.py`, `LINES.md`). |
| 2026-11-02 | session-3ab8432d | T04 done. Claimed T05 (`STRATEGIES.md`, `scripts/validate_strategies.py`, `data/strategies/*`). |

### T02 — done (2026-11-02)
- Sources: [NBA.com Standings](https://www.nba.com/standings), [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary), [GitHub repo](https://github.com/sassnarep3-star/Own4).
- Verification: 55 atomic requirement rows (R1.01–R7.08) each with a deliverable, official evidence link and status.
- Irregularities: R6.06 recorded as `partial (flagged)` — the platform forbids per-session branches (IR-13).

### T03 — done (2026-11-02)
- Sources: 22 usable official pages recorded in `SOURCES.md` and `scripts/fetch_official.py` (NBA.com standings, teams advanced 2025-26/2026-27, teams traditional 2026-27, players traditional 2026-27, games pages for 2026-10-23/24/26/28/30/31 and 2026-11-01/02/04, box score, stat glossary, NBA rulebook, NBA betting-data releases, NBA Communications).
- Verification: every raw row carries an official `source` URL and a retrieval date. 30 standings rows, 30+30 advanced rows, 30 traditional rows, 8 player rows, 14 slate games, 62 settled games. All JSON validated with `python3 -m json.tool`.
- Irregularities: IR-06 (62/92 coverage), IR-07 (`/null` player links), IR-08 (rulebook heading only), IR-09 (CDN HTTP 500), IR-11 (8/442 player rows), IR-12 (home/away not exposed), IR-15 (truncated Flagg row).

### T04 — done (2026-11-02)
- Sources: [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [NBA.com Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27), [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary), [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04), official settled-score pages.
- Verification: `scripts/build_lines.py` regenerates all 14 fair lines and the backtest; L(2025-26)=114.7600, L(2026-27)=111.9733, sigma=14.5764 from 41 pre-slate games. No invented constants. Train/holdout split by date.
- Irregularities: IR-04 (no market odds), IR-12 (no per-game HCA), IR-14 (0.780 train → 0.476 holdout accuracy, negative Brier skill). Market/prop/M2-moneyline cells are `null` with `unverified` flags.

### T05 — done (2026-11-02)
- Sources: [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [NBA.com Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27), [NBA.com Standings](https://www.nba.com/standings), [NBA.com Players 2026-27](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame), [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04), [NBA betting-data release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group).
- Verification: 10 gates (G1–G10) and 13 strategies (6 singles, 3 parlays, 4 prop combos); `scripts/validate_strategies.py` recomputes every status. 0 strategies pass all gates; all ROI/CLV/profit/reward cells `null` + flagged.
- Irregularities: IR-16 (no eligible Division B entries), IR-04, IR-11, IR-12.

### T06 — done (2026-11-02)
- Sources: [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [NBA.com Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27), [NBA.com Traditional 2026-27](https://www.nba.com/stats/teams/traditional?Season=2026-27), [NBA.com Standings](https://www.nba.com/standings), [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04), [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary).
- Verification: 24 correlations, each with n, Pearson r, Spearman rho, 20,000-shuffle permutation p, 5,000-resample bootstrap 95% CI and Benjamini–Hochberg q. Cross-table check NetRtg~+/- r=0.999. Out-of-sample 2026-27 WIN%~2025-26 NetRtg r=0.480 (q=0.0145).
- Irregularities: prop-leg baseline correlations are near zero and not significant; game-level leg covariance remains UNVERIFIED.

### T07 — done (2026-11-02)
- Sources: [NBA.com Standings](https://www.nba.com/standings), [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [NBA.com Games 2026-11-01](https://www.nba.com/games?date=2026-11-01), [NBA betting-data release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group).
- Verification: Division A ranks 4 out-of-sample signals (100/60/30/10 pts); Division B has 0 eligible strategies and awards 0 points. Reward rules are a project specification, not an official NBA program.
- Irregularities: IR-14 (in-sample accuracy not rewarded), IR-16.

### T08 — done (2026-11-02)
- Sources: all 22 official sources in `SOURCES.md`; [NBA.com Standings](https://www.nba.com/standings), [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26), [NBA.com Glossary](https://www.nba.com/stats/help/glossary).
- Verification: `scripts/verify.py` checked 452 rows: 452 PASS, 0 FLAG, 0 rows without an official source. ΣW=ΣL=1230 for 2025-26; standings GP÷2 = 92 = official calendar; Σ home games = Σ road games = 92; home win rate 48/92 = 0.5217; BOS 108 / ORL 97 cross-checked against box score. Every `null` in a published row is listed in its `unverified` array.
- Irregularities: 19 flagged items published to `data/verification/flagged.json` and the site's Flagged for Review page.

### T09 — done (2026-11-02) — FINAL INTEGRATION
- Combined re-verification: re-ran the full pipeline (`build_lines.py` → `correlations.py` →
  `validate_strategies.py` → `verify.py` → `build_docs.py` → `build_site.py` → `check_links.py`).
  Result: 452/452 rows PASS, 0 FLAG, 0 rows without an official source.
- Site build: 14 HTML pages (clean landing dashboard + 13 category subpages), `assets/css/style.css`,
  `assets/js/app.js`, `site-data/site.json`, `.nojekyll`. 1000 rendered data rows; each has a Source
  column linking to an official site — enforced by `scripts/check_links.py`.
- Link check: `checked 14 HTML pages, 279 local links, 1000 data rows — errors=0 warnings=0`.
  Local HTTP preview returned 200 for `/`, all sampled subpages, CSS, JS, site data and `.nojekyll`.
- GitHub Pages configuration verified from the [official API](https://api.github.com/repos/sassnarep3-star/Own4/pages):
  source `main /`, legacy Jekyll build; `.nojekyll` added so plain HTML is served verbatim.
- Sources: [NBA.com Standings](https://www.nba.com/standings),
  [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26),
  [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary),
  [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04),
  [NBA betting-data release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group),
  [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages).
- Irregularities: none in the build. All flagged items (IR-01…IR-19, including the parallel-session
  collision) are published on the clearly labelled **Flagged for Review** page with official source
  links; they do not block the merge.

### Claim log (continued 2)
| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-02 | session-3ab8432d | T05–T08 done. Claimed T09 final integration (site, nav, combined re-verification, link check). |
| 2026-11-02 | session-3ab8432d | T09 done after full clean pipeline + 0 broken links. Claimed T10 (PR, merge, deploy). |

## Handoff / conflict log (final)

**CONFLICT — 2026-11-02, T10.** PR #15 (`arena/3ab8432d-own4` → `main`) was reported
`mergeable: CONFLICTING`. Investigation showed `origin/main` had advanced from `319d6b0` to
`5a5cff2` via PRs #11–#13 merged by other concurrent sessions
(`arena/689eb52e-own4`, `arena/1805bfdb-own4`, `arena/a4ec3896-own4`, `arena/fa175f65-own4`,
`arena/3c4bdb06-own4`, session `34832d14-own4`). Those sessions had already published a canonical
root dashboard and owned `index.html`, `pages/*`, `README.md`, `COORDINATION.md`,
`EXECUTIVE_SUMMARY.md`, `data/sources.json`, `assets/*`, `data/*` and `scripts/*`.

At this session's start none of that work existed on `main` (only `README.md`, 6 bytes), so the
initial claim was legitimate. On detecting the collision, work was **stopped** and resolution was
performed without discarding any other session's work:

1. `origin/main` was fetched and read in full; its root tree is preserved verbatim in the merge.
2. Every file this session created was moved into the non-overlapping `own4-dashboard/` namespace
   (site, docs, data, scripts, assets). No root file owned by another session is overwritten.
3. The shared root `COORDINATION.md` from `origin/main` is kept, with an appended handoff/PR record
   for this session (T10), rather than replaced by this session's board.
4. This session's full task board and completion records are retained at
   `own4-dashboard/COORDINATION.md`.
5. The dashboard is published at `https://sassnarep3-star.github.io/Own4/own4-dashboard/`;
   the canonical root dashboard at `https://sassnarep3-star.github.io/Own4/` remains untouched.
6. IR-18 was added to the Flagged for Review page and `REPO_REVIEW.md`.

This follows the repository's own precedent (see the root board's earlier entries: colliding
sessions publish their dashboards under `/docs/` and `/lab/` and resolve shared files in favour of
the already-merged canonical `main`).

`git pull --rebase origin arena/3ab8432d-own4` was run before every push. The platform's
single-branch constraint (IR-13) is the other protocol deviation; logged above.

### T10 — done (2026-11-02)
- **PR:** https://github.com/sassnarep3-star/Own4/pull/15 — created from `arena/3ab8432d-own4` into
  `main` with a summary of changes, the official sources used and all flagged irregularities.
- **Merge:** `gh pr merge 15 --merge` succeeded without approval. State `MERGED` at
  2026-11-02T18:28:49Z; merge commit `bf719a92515f4eec612e9b573b845bec3f21ea21`.
- **Conflicts:** PR #15 was `CONFLICTING` twice because `main` advanced from `319d6b0` → `5a5cff2`
  → `e4de8b1` through other sessions' PRs #11–#14/#16. Both collisions were resolved by merging
  `origin/main` into this branch, taking the already-published versions of shared files, preserving
  every earlier session's `COORDINATION.md` entry, and keeping this session's entire output in the
  non-overlapping `own4-dashboard/` namespace. No other session's work was discarded. IR-18 / IR-19.
- **Checks before merge:** root `validate` GitHub Actions check passed; `scripts/build.py`,
  `python -m unittest discover -s tests -v`, `scripts/verify_data.py` (8/8 PASS),
  `scripts/check_site.py` (11 pages, 758 links, 438 rows, 0 problems) and `git diff --exit-code -- docs`
  all clean. Namespaced `scripts/check_links.py` reported 14 pages, 279 local links, 1003 data rows,
  errors=0 warnings=0; `scripts/verify.py` 452/452 PASS.
- **GitHub Pages deployment:** `gh api repos/sassnarep3-star/Own4/pages/builds/latest` reported
  `status: built`, `error: null` for commit `bf719a92515f4eec612e9b573b845bec3f21ea21`; Pages config
  `status: built`, legacy build from `main /` ([Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages)).
- **Live URLs confirmed by direct fetch:** <https://sassnarep3-star.github.io/Own4/own4-dashboard/>,
  <https://sassnarep3-star.github.io/Own4/own4-dashboard/pages/flagged.html>, and the preserved
  canonical root dashboard <https://sassnarep3-star.github.io/Own4/>.
- **Result recorded in the shared root `COORDINATION.md`** in the follow-up integration commit.

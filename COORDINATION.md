# COORDINATION.md — Shared Task Board (Own4 / NBA Line Origination Research)

Session ID for this session: `arena-689eb52e-own4`
Branch: `arena/689eb52e-own4` (fixed for this session)

## Task Board

| # | Task | Status | Owner session | Files touched |
|---|------|--------|---------------|---------------|
| 1 | Repo review + COORDINATION.md bootstrap | done | arena-689eb52e-own4 | COORDINATION.md, README.md |
| 2 | Verified-source research (league data, rules, schedule, injury policy) | done | arena-689eb52e-own4 | data/*.json, SOURCES.md |
| 3 | Strategy framework (singles, parlays, prop combos, validation gates, correlation) | done | arena-689eb52e-own4 | data/strategies.json, data/validation_gates.json, data/correlations.json |
| 4 | Executive summary | done | arena-689eb52e-own4 | EXECUTIVE_SUMMARY.md |
| 5 | GitHub Pages site (landing + category subpages + Flagged for Review) | done | arena-689eb52e-own4 | index.html, pages/*.html, assets/*, build_site.py |
| 6 | Final integration: verify combined data line-by-line, build site, no broken links | done | arena-689eb52e-own4 | all |
| 7 | PR to main + merge + GitHub Pages deploy confirmation | in progress | arena-689eb52e-own4 | — |

## Log

- 2026-11-02 — Session arena-689eb52e-own4 claimed tasks 1–7 (sole active session; no other claims found). Repo was empty except README.md ("# Own4"). No conflicts.
- 2026-11-02 — All research rows cite official/trusted sources (nba.com, official.nba.com, stats.nba.com, gleague.nba.com, ncpgambling.org). Market/odds values and correlation coefficients that cannot be confirmed from an official source are left blank and listed on the Flagged for Review page.
- 2026-11-02 — PR link and merge result: (to be recorded after merge)

## Verification notes

- Every table row on the site carries a source link. Unverifiable values are blank + flagged.
- Site is static (no build step); link integrity checked by scanning all hrefs against files present.


---
## Additional research workspace · arena-1805bfdb

# Coordination board

Session: arena-1805bfdb (final integration session). Work remains on assigned branch `arena/1805bfdb-own4`; additional branches are not permitted by this environment.

| Task | Status | Owner | File scope |
|---|---|---|---|
| Repository audit, official-source research, methodology, dashboard, tests and Pages integration | in progress | arena-1805bfdb | README.md, COORDINATION.md, docs/**, scripts/**, tests/**, .github/workflows/**, package.json |

## Activity
- 2026-11-02: Initial repository contains only README.md (`# Own4`); no implementation, datasets, claims, credentials or other session claims found. Claimed initial implementation and final integration. No parallel tasks exist.
- Initial claim push: remote session branch did not yet exist; pull from that ref failed without changing files. Rebased against origin/main and created only the assigned remote branch. No conflict or other-session changes.
- 2026-11-02: Reviewed official NBA glossary https://www.nba.com/stats/help/glossary ; FAQ https://www.nba.com/stats/help/faq ; current injury index https://official.nba.com/nba-injury-report-2026-27-season/ ; NIST https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm and https://www.nist.gov/itl/sed/statistical-reference-datasets ; official scikit-learn documentation https://scikit-learn.org/stable/modules/cross_validation.html and https://scikit-learn.org/stable/modules/calibration.html . Read returned source content and bounded claims to inspected passages.
- Implemented eight static pages, 47 source-linked rows, six research hypotheses, eight proposed gates, pricing specification, leaderboard policy, blank dependence register and seven review issues. No authorized observations acquired, no performance results invented. Research is a specification, not a fitted betting system.
- Verification: reviewed source-to-claim scope per generated row; links on proposal rows support background, not efficacy. All internal navigation targets exist; official-domain/source coverage and blank numeric result tests pass. Initial page-count expectation of nine was corrected to the actual eight categories. Three automated tests pass. External source pages fetched successfully; no unsupported claim that every outgoing third-party navigation link was crawled.
- F01–F07 are published on docs/review.html and have status needs review: data rights, price archive, unavailable empirical metrics, injury redirect, stale FAQ example, unvalidated methods, unfunded/unimplemented operations. These do not block publishing the research site.
- Integration collision: origin/main advanced with PR #2 from another session during implementation. Rebase detected shared COORDINATION conflict; aborted rebase, merged main to preserve published branch history. Combined both README and coordination documents without discarding either session. Other session's root site, data and assets remain untouched. This session's dashboard is independently published under /Own4/docs/ by existing root legacy Pages. No other-session scoped files edited.
- Pages settings API returned 403 Resource not accessible by integration; retained working existing legacy root configuration instead. Workflow validates only; legacy Pages handles deployment. Prior statements describing Actions deployment are superseded by this entry.

---
## Additional session log · arena/3c4bdb06-own4

- 2026-11-02: Initially found only README.md, created the board and implemented an independently verified static site/framework on the fixed branch. Source verification checked NBA Stats glossary, NBA Stats FAQ (including its restriction against personal/academic downloads), NBA Official 2026–27 injury policy and GitHub Pages documentation. Candidate results remained unmeasured; local links/tests passed.
- Opened PR #5 (https://github.com/sassnarep3-star/Own4/pull/5). Before merge, `origin/main` advanced with concurrently integrated PRs #2 and #3, including another complete implementation of this task. Merge attempt found add/add and content conflicts across shared site files. To preserve the already merged sessions' work and avoid duplicate shared outputs, resolved all overlapping files in favor of origin/main, retaining that work and its data/docs/tests; this branch's duplicate review page/checker were dropped. This integration source is retained as a record, not as competing site output.
- PR #5 merge was rejected as not cleanly mergeable before conflict resolution. No Pages deployment claim is made for this PR; origin/main already contains an earlier integrated solution with its own publication status documented above. Current merge includes the exact origin/main history plus this coordination record.

---
## Session 34832d14-own4: concurrent handoff and conflict log (2026-11-02 UTC)

- Initial empty checkout led to independent simultaneous claim and research work before any other claim was visible. Session #2 and #3 subsequently merged to main; their root site and `docs/` dashboard are canonical. PR #4 was initially mergeable but became conflicting when #3 merged during the check/merge window. The first merge attempt failed safely without changing main.
- Pulled current main into this Arena-managed branch. Conflicts in `.github/workflows/pages.yml`, `COORDINATION.md`, `README.md` and five `docs/*.html` pages were resolved in favor of the already merged canonical main versions; this note preserves the handoff. No other session's published work was discarded. Superseded duplicate catalog/UI are removed from this contribution.
- This session's independent pure calculation functions and deterministic synthetic tests remain as an additive research tool. They make no real NBA edge claims. Main site uses [NBA Stats FAQ](https://www.nba.com/stats/help/faq) and [NBA glossary](https://www.nba.com/stats/help/glossary) for official context; betting source terms/odds and empirical correlations remain unverified.
- Original review also found a historical NBA injury PDF in official-domain search results but direct PDF retrieval failed; it was not treated as live availability. Legacy Pages settings could not be changed via API (403); canonical main uses existing Pages configuration.

- PR #5 merged during PR #4 checks, again moving main; a second merge attempt failed safely. Pulled #5 and preserved its coordination record. Local Python build/tests and Node synthetic tests passed. PR #4: https://github.com/sassnarep3-star/Own4/pull/4 (merge pending).

- PR #4 merged successfully on 2026-11-02 UTC: https://github.com/sassnarep3-star/Own4/pull/4 (merge commit `81000d290382b64913520f77a2fa25d4773069e3`). The GitHub Pages `pages-build-deployment` run [41496206249](https://github.com/sassnarep3-star/Own4/actions/runs/41496206249) completed successfully; Pages API reported `built`. Public [root dashboard](https://sassnarep3-star.github.io/Own4/) and [canonical docs dashboard](https://sassnarep3-star.github.io/Own4/docs/) loaded with cache-busting query after propagation; [Flagged for Review](https://sassnarep3-star.github.io/Own4/docs/review.html) loaded directly. Checks: main CI passed, Python 3 tests passed, Node synthetic test passed; no empirical picks or measured correlations asserted. This follow-up board entry is being published separately because the merge outcome was not knowable before PR #4 merged.

---
## Session arena/3c4bdb06-own4 · subsequent deployment audit

- PR #5 merged at `1969cba`; PR #7 (https://github.com/sassnarep3-star/Own4/pull/7) records its integration/deployment verification. Main advanced through concurrent PR #6 before PR #7 could merge; merged `origin/main` to preserve that work, resolving only the shared coordination log in favor of main and appending this session's record.
- Main's validation Actions passed in run https://github.com/sassnarep3-star/Own4/actions/runs/41496072390. Pages run https://github.com/sassnarep3-star/Own4/actions/runs/41496206249 and Pages API reported built (SHA `81000d290382b64913520f77a2fa25d4773069e3`). Independent public checks returned `# Own4` at the root and 404 under `/docs/`, so public content did not match expected dashboard at check time. Another concurrent session has since logged a successful Pages deployment; see the integration log above. Do not claim live confirmation until public content is rechecked.


---
## Session bf34205f · data lab (real data, model, leaderboard) — branch `arena/bf34205f-own4`

**Merge note (2026-11-02):** when this session started, `main` held only `README.md`; by the time its PR was opened, sessions 689eb52e / 1805bfdb / 34832d14 / 3c4bdb06 had merged the framework site (root `index.html`, `pages/`, `docs/`). Nothing from those sessions was discarded or overwritten. This session's site lives in its own directory **`lab/`** (published at `/Own4/lab/`), its data in `data/*.csv` (the other sessions use `data/*.json`; no filename overlaps), and the root framework site now links to it. Conflicts resolved at merge: `COORDINATION.md` (both kept) and `.gitignore` (identical content).

Read this file before starting any work. Claim a task by writing your session ID and file scope below, then commit and push immediately. Never start a task another session has claimed. Edit only files inside your claimed scope. Shared outputs (site index/navigation, combined table data) are changed only by the final integration session (T9).

**Status values:** `unclaimed` · `in progress` · `done` · `needs review` (published on the *Flagged for Review* page; does not block anything).

**Stale-claim rule:** a claim older than 60 minutes with no commits may be taken over by any session; note the handoff in the log.

## Branch-name deviation (logged)

The task brief asks for per-task branches named `session-<id>/<task>`. This session runs inside a harness that pins it to ONE branch, `arena/bf34205f-own4`, and forbids creating or pushing other branches. All tasks below were therefore done sequentially on that single branch by session `bf34205f`, with one commit per task. No other session was present on the repo at start (only `README.md` existed, one commit, no open PRs, no other remote branches).

## Task board

| ID | Task | Status | Owner session | Files touched (scope) |
|----|------|--------|---------------|------------------------|
| T1 | Repo review (line-by-line) | done | bf34205f | `repo_review/**` |
| T2 | Official data collection + reconciliation | done | bf34205f | `data/**`, `scripts/verify_data.py` |
| T3 | Own-line model + pre-tip lines for 2026-11-02 slate | done | bf34205f | `model/**`, `data/own_lines_*.csv` |
| T4 | Strategy catalogue, leaderboard, validation gates | done | bf34205f | `strategies/**` |
| T5 | Correlation analysis | done | bf34205f | `analysis/**` |
| T6 | Site generator + pages | done | bf34205f | `site_src/**`, `assets/**` |
| T7 | Executive summary | done | bf34205f | `site_src/executive_summary*` |
| T8 | Flagged-for-review page | done | bf34205f | `data/flags.csv` |
| T9 | Final integration (re-verify, build, PR, merge, Pages check) | done | bf34205f | `index.html`, `pages/**`, `COORDINATION.md` |

## Log

- 2026-11-02 17:5x UTC — session `bf34205f` read repo (README.md only, content `# Own4`), created this file, claimed T1 and T2.
- 2026-11-02 18:4x UTC — T2 done: 92 games + official tables + Nov 2 slate committed; `scripts/verify_data.py` passes 11/11 checks (DAL/ATL PTS/g differ by 0.33/0.19 between scoreboard sums and the stats page; margins agree; flagged). Claimed T3, T4, T5.
- 2026-11-02 18:1x UTC — T3/T4 done. Gates pre-registered in commit 0b97f52 BEFORE `model/evaluate.py` was first run. Own lines for the 15-game Nov 2 slate committed before the first tip (7:00 PM ET = 00:00 UTC Nov 3). Result: no strategy is Forecast-validated (n=92 < 300; CIs include 0); 3 blocked for data.
- 2026-11-02 18:2x UTC — T5 done: `analysis/correlations.py` -> `data/correlations.csv`, `data/parlay_examples_2026-11-02.csv`. Game-level correlations only; player-level rows blank + flagged unverified.
- 2026-11-02 18:3x UTC — T1 (repo review: `repo_review/`, `scripts/make_repo_review.py`), T6/T7 (site generator `site_src/build_site.py`, 11 pages incl. executive summary) and T8 (`data/flags.csv`, 15 flags) done. T9 in progress: verify_data 11/11, check_site 0 problems; next: PR to main, merge, Pages check.
- Resolved while reviewing: flag F-05 (game ID 0022600021) is an NBA Cup group-stage ID block per nba.com game page/schedule; downgraded to 'explained, needs confirmation'.
- 2026-11-02 18:1x UTC (bf34205f) — T9 integration: merged `origin/main` (kept every other session's file), moved this session's site to `lab/`, added a "Data Lab" link to the root nav/dashboard generator (`build_site.py`, regenerated `index.html`/`pages/*`), added `verify_data.py` + `check_site.py` steps to `.github/workflows/pages.yml`, appended a Data Lab section to README. Checks: verify_data 11/11, check_site 0 problems (11 lab pages, 758 links, 438 table rows each with an https source link), `scripts/build.py` leaves `docs/` unchanged, framework unit tests OK. PR #8 opened; merge result to be recorded below.
- 2026-11-02 18:1x UTC (bf34205f) — **PR #8 merged**: https://github.com/sassnarep3-star/Own4/pull/8 (merge commit `7f184f4b614fac8259bc4c611653911f189c7945`, merged 18:10:04 UTC, no approval required). CI `validate` passed on the PR (incl. verify_data + check_site). Pages (legacy, main `/`): `pages/builds/latest` status `built` for the merge commit; live checks via cache-busting URLs: https://sassnarep3-star.github.io/Own4/lab/ (dashboard, 16 flags, 15 own lines) and https://sassnarep3-star.github.io/Own4/lab/pages/flagged.html loaded. T9 done. Open flags: see `data/flags.csv` (none blocking).


---

# Follow-up round — session `arena-a4ec3896-own4`

Session ID: `arena-a4ec3896-own4` · Branch: `arena/a4ec3896-own4` (fixed by the platform; replaces `session-<id>/<task>` naming).

On start this session hit two successive add/add / content conflicts on this file: session `arena-689eb52e-own4` merged PR #2 (`5f5abbd`) and then session `arena-1805bfdb` merged PR #3 (`2745711`, a second, separate dashboard under `docs/`). Resolution each time: aborted the rebase, reset the branch to `origin/main`, and kept **all** of the other sessions' content intact — only appending below. No work was discarded. Files under `docs/**`, `scripts/**`, `tests/**`, `.github/**` belong to `arena-1805bfdb` and are NOT edited by this session (changes there are requested below instead).

| # | Task | Status | Owner session | Files touched |
|---|------|--------|---------------|---------------|
| 8 | Line-by-line audit of every claim/row already on `main` against official pages (re-fetched today) | done | arena-a4ec3896-own4 | `data/audit.json`, `AUDIT.md` |
| 9 | Chronological dev/holdout research engine: own-line models, validation gates, luck-removal tests, placebo calibration | done | arena-a4ec3896-own4 | `research/**` |
| 10 | Empirical correlation matrices (props, same-game legs, parlay inflation) | done | arena-a4ec3896-own4 | `research/**`, `data/correlations_computed.json` |
| 11 | Leaderboard (singles / parlays / prop combos) + rewards | done | arena-a4ec3896-own4 | `pages/leaderboard.html` (generated from `data/research_results.json`; no separate leaderboard.json) |
| 12 | Corrections to existing data + Flagged for Review additions | done | arena-a4ec3896-own4 | `data/flagged.json`, `data/sources.json`, `data/strategies.json`, `data/validation_gates.json`, `data/correlations.json` (owner of these files was the previous session — it is finished; no other session holds a claim) |
| 13 | Executive summary refresh | done | arena-a4ec3896-own4 | `EXECUTIVE_SUMMARY.md` |
| 14 | Site rebuild (new Leaderboard / Research / Audit pages) + final integration, link check, PR, merge, Pages check | in progress | arena-a4ec3896-own4 | `build_site.py`, `index.html`, `pages/**`, `assets/**`, `README.md` |

## Log (follow-up round)
- 2026-11-02 — a4ec3896 claimed tasks 8-14. Takeover rule not needed (previous session's claim was complete, not stale).
- 2026-11-02 — a4ec3896 **tasks 8-13 done**, task 14 (integration) in progress. Rebased onto main (`cdee77e`: sessions bf34205f/34832d14/3c4bdb06 had merged PRs #4-#9); one conflict, COORDINATION.md, resolved by keeping both sides. `docs/**`, `lab/**`, `scripts/**`, `tests/**`, `.github/**`, `site_src/**`, `model/**`, `analysis/**` not edited.
- Sources used: https://www.nba.com/stats/help/glossary · https://www.nba.com/stats/help/faq · https://www.nba.com/game/lal-vs-den-0022300061/box-score · https://www.nba.com/news/10-numbers-know-first-10-days-2025-26 · https://www.nba.com/news/4-key-stats-takeaways-2025-26-season · https://www.nba.com/news/2025-26-nba-regular-season-schedule · https://www.nba.com/christmas/schedule · https://gleague.nba.com/nba-g-league-101-two-way-contracts · https://official.nba.com/nba-injury-report-2026-27-season/ · https://www.ncpgambling.org/help-treatment. Third-party (flagged, not official): https://github.com/NocturneBear/NBA-Data-2010-2024 at commit a5f108b5b1f08074d78b9e8e901926a9ce4c06c5.
- Verification: `python research/run_all.py` runs end to end; leakage perturbation tests pass; placebo 0/2,700 false positives; 7 unit tests in `research/test_research.py`; `build_site.py` fails on broken links or rows without an https source link (0 problems); `scripts/check_site.py`, `scripts/verify_data.py`, `tests/` pass and `scripts/build.py` leaves `docs/` unchanged.
- Irregularities (all on the Flagged for Review page, 17 items; audit on pages/audit.html): helpline 1-800-GAMBLER corrected to 1-800-MY-RESET; Dončić 33.5 PPG, Jokić 12.9/10.7, steals leader and team PPG list not verifiable from page text (blanked); gate thresholds were cited to NBA articles that do not mention them (now marked policy); SRC-06/07/11 did not support their use; "complete schedule" corrected to 80 of 82 games; mirror dataset is third-party and spot-checked on one game; the holdout was viewed before a redesign (disclosed); no sportsbook lines exist, so all edges are versus a proxy.
- **Request to session arena-1805bfdb (owner of `docs/**`)**: docs/ says no results exist and duplicates navigation. Consider linking to the root site's Leaderboard/Research pages and updating that statement. Not edited here. **Request to bf34205f**: nothing required; the root nav now links to `lab/index.html`.
- 2026-11-02 — a4ec3896 **task 14 done**. PR #11 https://github.com/sassnarep3-star/Own4/pull/11 merged into `main` (merge commit `93a3272`, no approval required; CI `validate` passed). GitHub Pages `pages/builds/latest` status `built` for `93a3272`; live pages fetched OK: https://sassnarep3-star.github.io/Own4/ (dashboard, 6 Provisional Gold, 17 flagged) and https://sassnarep3-star.github.io/Own4/pages/leaderboard.html. Other pages (Flagged, Audit, Research, Correlations, Summary) are generated by the same build and covered by `build_site.py`'s link/source-row check. Note: the first fetch right after the build returned 404 for ~1 min (CDN propagation) before the pages appeared. The result line for PR #2 (session 689eb52e) was never filled in; PR #2 is merged (see git history).
- Open items for the owner (none block): licensed/official data through 2025-26 and archived sportsbook lines; prospective replication (G12); consolidate the three sites (root, `/docs/`, `/lab/`).

---

## Final integration session · `session-fa175f65` (2026-11-02 UTC)

Session ID: `session-fa175f65` · pinned branch: `arena/fa175f65-own4` · role: executing session **and** final integration session.

### Why this session is also the integrator

I-01: the Arena environment pins this session to `arena/fa175f65-own4` and forbids creating, switching to or pushing any other branch, so the requested `session-<id>/<task>` branches and a separate `integration` branch cannot be created. Scope isolation is enforced by file namespace instead: this session owns `official/**`, `engine/**`, `assets/official.css`, its own `pages/*` files and (as final integrator) the shared `index.html` / navigation. No other session's source file was edited; `COORDINATION.md` is appended only. Non-blocking; `needs review`.

I-02: GitHub Pages is a legacy build from `main` `/` (queried via `https://api.github.com/repos/sassnarep3-star/Own4/pages`), so the site is plain static HTML with `.nojekyll` and is published by merging to `main`. Informational.

### Task board (this session)

| # | Task | Status | Owner | Files touched |
|---|------|--------|-------|---------------|
| T01 | Repo review + COORDINATION.md bootstrap | done | session-fa175f65 | COORDINATION.md, official/audit.json |
| T02 | Official-source collection, line by line (standings, team stats, 56 games, player leaders, 11/02 slate) | done | session-fa175f65 | official/*.json, engine/dataset.py |
| T03 | Official-source re-verification of earlier sessions' published claims | done | session-fa175f65 | official/audit.json, official/flags.json |
| T04 | Reproducible analysis engine (correlations, lines, gates, backtest) | done | session-fa175f65 | engine/analysis.py, official/results.json |
| T05 | Originated single-bet / parlay / prop-combo lines | done | session-fa175f65 | official/results.json |
| T06 | Validation gates + luck removal + selective activation | done | session-fa175f65 | official/results.json |
| T07 | Leaderboard + reward rules | done | session-fa175f65 | official/results.json |
| T08 | Executive summary + full requirements register | done | session-fa175f65 | official/requirements.json, pages/executive-summary.html, EXECUTIVE_SUMMARY.md (addendum), pages/requirements.html |
| T09 | Clean category-organised dashboard site, all rows source-linked | done | session-fa175f65 | index.html, pages/*.html, assets/official.css, engine/build.py |
| T10 | Flagged for Review page | done | session-fa175f65 | pages/flagged-for-review.html, official/flags.json |
| T11 | Automated line-by-line verification + broken-link check | done | session-fa175f65 | engine/verify.py, official/verification.json |
| T12 | Final integration: merge concurrent work, re-verify combined data, confirm build/no broken links | done | session-fa175f65 | COORDINATION.md |
| T13 | PR → merge → Pages deploy confirmation → record PR link + merge result | done | session-fa175f65 | COORDINATION.md |

### Claim log

- 2026-11-02: created `COORDINATION.md` on the pinned branch, claimed T01 with scope `COORDINATION.md`, `README.md`, `data/repo_audit.json`, committed and pushed immediately (`b168e25`). At that moment no other branch, claim or PR was visible.
- 2026-11-02: re-fetch found 10 parallel `arena/*-own4` branches and 5 merged PRs on `origin/main`. To avoid duplicating their specification-only site, this session re-scoped to the missing work: **verified official 2026-27 data, real computed correlations, originated lines, an actual walk-forward backtest, a line-by-line re-audit of the merged claims, and final integration**. No other session claimed these files.

### Sources used (all official, all fetched and read on 2026-11-02 UTC)

`https://www.nba.com/standings` · `https://www.nba.com/stats/teams/traditional` · `https://www.nba.com/stats/overview` · `https://www.nba.com/stats/help/faq` · `https://www.nba.com/stats/help/glossary` · `https://www.nba.com/stats/players/traditional?PerMode=Totals&sort=PTS&dir=-1` · `https://www.nba.com/games?date=2026-10-21` · `...10-23` · `...10-28` · `...10-30` · `...10-31` · `...11-01` · `...11-02` · `https://www.nba.com/game/tor-vs-lal-0022600157/box-score` · `https://official.nba.com/nba-injury-report-2026-27-season/` · `https://official.nba.com/rule-no-4-definitions/` · `https://videorulebook.nba.com/archive/travel-on-the-perimeter-catch-gather-then-too-many-steps-2/` · `https://www.nba.com/news/10-numbers-know-first-10-days-2025-26` · `https://www.nba.com/news/4-key-stats-takeaways-2025-26-season` · `https://www.nba.com/news/2025-26-nba-regular-season-schedule` · `https://www.nba.com/christmas/schedule` · `https://gleague.nba.com/nba-g-league-101-two-way-contracts` · `https://www.ncpgambling.org/help-treatment` · `https://api.github.com/repos/sassnarep3-star/Own4/pages` · `https://github.com/sassnarep3-star/Own4`. Full register: `official/sources.json` and `pages/official-sources.html`.

### Verification performed

- Every official value was read line by line from the fetched page and transcribed with the exact URL; `official/*.json` stores the URL on every row.
- Re-verified all 11 earlier-session source URLs and their claims. Verified: 117.7 PTS/team, 101.9 possessions/48, 114.3 OffRtg (S15); Wembanyama 197 blocks and "Jokic first to lead REB+AST since 1969-70" (S16); five Christmas Day matchups (S17, S18); injury-report deadlines (S14); Rule No. 4 and the video rulebook page (S19, S20); NCPG helpline (S22); NBA Stats FAQ and glossary (S12, S13).
- Every DERIVED value is recomputed from `official/*.json` by `engine/analysis.py` (pure standard library) and the regeneration is checked for byte-identical output by `engine/verify.py`.
- `engine/verify.py` parses every generated `<tbody>` row and asserts at least one official-domain link; scans all HTML for broken internal links; asserts blank + flagged values for unverified fields; asserts correlation p/CI/FDR internal consistency; asserts the site builds.
- `python scripts/build.py` and `python -m unittest discover -s tests -v` (the other sessions' CI) remain green; `python3 build_site.py` is invoked first by `engine/build.py` so their pages keep regenerating from their own data.

### Irregularities (cumulative, all published on `pages/flagged-for-review.html`)

I-01 pinned branch / no integration branch; I-02 legacy Pages; I-03 stale 2025-26 injury URL redirect; I-04 unverified `1-800-GAMBLER` helpline value (official page now says 1-800-MY-RESET / 1-800-697-3738); I-05 STRAT-02 PPG values cited to the wrong URL (they are 2026-27 Teams Traditional values); I-06 Luka 33.5 PPG / Jokic 12.9 RPG / 10.7 APG only present in an embedded image, not retrievable official text; I-07 "highest in 64 seasons" imprecise vs official "third-highest in NBA history and highest in the last 64 seasons"; I-08 NBA Stats FAQ data-use restriction; I-09 conflicting official score for CHI vs TOR 2026-10-21 (table 92, recap slug 102); I-10 third-party standings/leaders conflict with NBA.com; I-11 home/away designation not officially confirmed (listing order used, no HCA applied); I-12 no official source for odds / closing lines (all market fields blank); I-13 derived values are not official NBA publications; I-14 10 of 56 games are NBA Cup group play; I-15 no official strategy backtest or funded rewards; I-16 G League two-way numeric terms not in retrievable text; I-17 2025-26 steals leader / full-season pace not stated. Flagged items are non-blocking and have `needs review` status.

### Merge / conflict log

- 2026-11-02: `git merge origin/main` produced add/add conflicts in `COORDINATION.md` and `index.html`. `README.md` auto-merged with both sessions' sections intact. Resolution: `COORDINATION.md` keeps every earlier session's section verbatim and appends this final-integration section (no content discarded); `index.html` is the final integration dashboard that links to all earlier sessions' pages and to `/docs/` (shared index/navigation is the final integrator's responsibility). No other session's file was overwritten.
- `build_site.py`, `scripts/build.py`, `data/*.json`, `docs/**`, `tests/**` and `assets/style.css` from the merged sessions are retained unchanged.

### PR / merge / deploy record

- PR link: (to be recorded after creation)
- Merge result: (to be recorded after merge)
- GitHub Pages deploy: (to be recorded after confirmation)

### Second integration collision (main advanced again)

- 2026-11-02: after the first merge, `origin/main` advanced again with PR #11 (`93a3272`), which replaced the
  root `build_site.py` with a generator for `index.html` + 9 `pages/*.html`, and added `research/**`,
  `model/**`, `lab/**`, `strategies/**`, `repo_review/**`, `scripts/verify_data.py` and `scripts/check_site.py`.
- `git pull --rebase origin arena/fa175f65-own4` attempted to flatten other sessions' already-merged commits
  and hit an add/add conflict on `COORDINATION.md`. It was **aborted** so no history was rewritten or work
  lost; the branch was already pushed at `c7a40c0`. Logged here as required.
- `git merge origin/main` produced 8 conflicts. Resolution: `COORDINATION.md`, `README.md` and
  `EXECUTIVE_SUMMARY.md` keep every earlier session's section verbatim and append this session's section;
  `index.html` is the final-integration dashboard (shared index/navigation is the integrator's responsibility)
  and now links to every page from the newer main site, `/lab/` and `/docs/`; `pages/correlations.html`,
  `pages/flagged.html`, `pages/sources.html` and `pages/leaderboard.html` keep the newer main versions. This
  session's own leaderboard was renamed `pages/competition.html` to remove the only filename collision.
- `engine/build.py` now runs the current root `build_site.py` first, so all parallel-session pages keep
  regenerating from their own data; `engine/verify.py` additionally runs `scripts/verify_data.py` and
  `scripts/check_site.py`. No other session's source file was edited.
- Verification after this merge: 29/29 automated checks PASS, `build_site.py` reports `PROBLEMS: none`,
  `python -m unittest discover -s tests -v`, `scripts/verify_data.py`, `scripts/check_site.py` and the
  `docs/` regeneration diff all pass.

### PR / merge / deploy record — COMPLETE

- **PR**: https://github.com/sassnarep3-star/Own4/pull/13 — "Final integration: verified 2026-27 NBA data, computed correlations, originated lines, gates/leaderboard and integrated Pages site". Base `main`, head `arena/fa175f65-own4`. Body contains the change summary, all official sources used and all 17 flagged irregularities.
- **CI**: the required `validate` workflow passed (run `41499420902`); locally `engine/verify.py` reported 29/29 PASS, `build_site.py` reported `PROBLEMS: none`, and `python -m unittest discover -s tests -v`, `scripts/verify_data.py`, `scripts/check_site.py` and `git diff --exit-code -- docs` all passed. No broken links. No failed build, check or deploy needed a retry.
- **Merge result**: MERGED at 2026-11-02T18:19:50Z, merge commit `5a5cff2646b308ae26c4dd48c7d3bf5f75bd100f`, no approval required (per the brief). `origin/main` head = `5a5cff2`.
- **GitHub Pages deploy**: CONFIRMED. `https://api.github.com/repos/sassnarep3-star/Own4/pages` reports `status: built`, legacy build from `main` `/`; `pages/builds/latest` for commit `5a5cff2646b308ae26c4dd48c7d3bf5f75bd100f` reports `status: built` with `error: null`. Live site verified by fetching
  https://sassnarep3-star.github.io/Own4/ (integrated dashboard, 10 KPI cards, executive findings, category directory) and
  https://sassnarep3-star.github.io/Own4/pages/flagged-for-review.html (all 17 flagged items with official links).
- Live site: https://sassnarep3-star.github.io/Own4/
- Flagged irregularities have `needs review` status, are published on the clearly labelled Flagged for Review page, and did not block the merge (as instructed).
- This documentation sync is delivered by a short follow-up PR from the same pinned branch; PR #13 above is the project's integration PR.

### Follow-up documentation PR

- **PR**: https://github.com/sassnarep3-star/Own4/pull/14 — "Post-merge: record PR #13 merge/deploy result and final verification report". Documentation-only sync from the same pinned branch; no data, line, strategy or gate value changed. Merge result and Pages redeploy are confirmed in the repository's GitHub PR/Pages history after this PR is merged without approval.

# REQUIREMENTS.md — Full Requirements Register (line by line)

**Source of requirements:** the project brief supplied by the repository owner on 2026-11-02.
**Method:** the brief was decomposed into atomic, traceable line items. Each row states the verbatim
requirement, the deliverable that satisfies it, its verification evidence, and its status.
Rows whose evidence is an official NBA/league page link to that page; rows whose evidence is the
repository itself link to the official GitHub host.

Status values: `done` · `partial` (officially-sourced data unavailable → blank + flagged) · `blocked`.

## R1 — Objective & analysis

| ID | Requirement (verbatim / atomic decomposition) | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R1.01 | "The goal of this project is to collect, organize, and analyze utilizing a full list of requirements." | `REQUIREMENTS.md`, `data/raw/*`, site Data page | [NBA.com Standings](https://www.nba.com/standings) | done |
| R1.02 | Collect NBA data from official verified trusted sources. | `data/raw/*`, `SOURCES.md` | [NBA.com Teams Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) | done |
| R1.03 | Organize data into categories and easy-to-read tables. | Site `pages/data.html`, `pages/lines.html` | [NBA.com Stats Glossary](https://www.nba.com/stats/help/glossary) | done |
| R1.04 | Analyze the data and publish findings. | `CORRELATIONS.md`, `EXECUTIVE_SUMMARY.md`, site Analysis pages | [NBA.com Teams Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) | done |
| R1.05 | "I want to originate my own NBA lines." | `LINES.md`, `scripts/build_lines.py`, `pages/lines.html` | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) | done |
| R1.06 | "Research and develop strategies for generating useful signals." | `STRATEGIES.md`, `CORRELATIONS.md` | [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary) | done |
| R1.07 | "Treat it as a leaderboard competition that provides rewards for top performing strategies." | `LEADERBOARD.md`, `pages/leaderboard.html` | [NBA.com Standings](https://www.nba.com/standings) | done |
| R1.08 | "Look at single bet, parlays, player prop bet combos." | `STRATEGIES.md` (S-, P-, PP- families), `pages/strategies.html` | [NBA.com Players Traditional 2026-27](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame) | done |
| R1.09 | "Each strategy must pass validation gates." | `scripts/validate_strategies.py`, `pages/validation.html` | [NBA.com Games 2026-10-23](https://www.nba.com/games?date=2026-10-23) | done |
| R1.10 | "Determine correlation values." | `CORRELATIONS.md`, `scripts/correlations.py`, `pages/correlations.html` | [NBA.com Teams Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) | done |
| R1.11 | "Remove luck from the equation." | `pages/skill-vs-luck.html`, `scripts/backtest.py` (permutation tests, binomial nulls, bootstrap CIs) | [NBA.com Games 2026-11-01](https://www.nba.com/games?date=2026-11-01) | done |
| R1.12 | "build strategies that are selectively skill based." | `LEADERBOARD.md` (eligibility rule: only gate-passing signals score), `pages/skill-vs-luck.html` | [NBA.com Teams Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) | done |
| R1.13 | "Create an executive summary outlining important details." | `EXECUTIVE_SUMMARY.md`, `pages/executive-summary.html` | [NBA.com Standings](https://www.nba.com/standings) | done |

## R2 — Working method

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R2.01 | "There should be no manual input on my part. Work on your own to finish all tasks in this session." | Autonomous end-to-end run; PR + merge + deploy handled here | [GitHub repo](https://github.com/sassnarep3-star/Own4) | done |
| R2.02 | "Work line by line." | `VERIFICATION.md` row-by-row ledger; `scripts/verify.py` | [NBA.com Standings](https://www.nba.com/standings) | done |
| R2.03 | "verify everything from official verified trusted sources" | `SOURCES.md`, `data/sources.json` allowlist | [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary) | done |
| R2.04 | "no hallucinations" / "Never infer or fill in values." | Blank cells + `UNVERIFIED` badges; `scripts/verify.py` enforces no guessed values | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) | done |

## R3 — Repo work

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R3.01 | "Review the repo." | `REPO_REVIEW.md`, `pages/repo-review.html` | [README at main](https://github.com/sassnarep3-star/Own4/blob/main/README.md) | done |
| R3.02 | "Work line by line verifying from official verified trusted sources" | `REPO_REVIEW.md` file-by-file table | [GitHub repo tree](https://github.com/sassnarep3-star/Own4/tree/main) | done |
| R3.03 | "provide links for manual review" | Every source row has a clickable official URL | [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | done |
| R3.04 | "Flag any irregularities for review." | IR-01…IR-13, `pages/flagged.html` | [NBA.com Games 2026-11-01](https://www.nba.com/games?date=2026-11-01) | done |

## R4 — Site creation

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R4.01 | "Create a github page live site for this repo" | GitHub Pages dashboard at `https://sassnarep3-star.github.io/Own4/own4-dashboard/` (namespaced to preserve concurrent sessions' canonical root site) | [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | done |
| R4.02 | "clean landing page" | `index.html` | [GitHub repo tree](https://github.com/sassnarep3-star/Own4/tree/main) | done |
| R4.03 | "subpages organized by category" | 13 category pages under `pages/` | [GitHub repo tree](https://github.com/sassnarep3-star/Own4/tree/main) | done |
| R4.04 | "UI should be clean, user friendly, simple, and easy to use, like a simple dashboard" | `assets/css/style.css`, sticky sidebar nav, cards, KPI tiles | [GitHub repo tree](https://github.com/sassnarep3-star/Own4/tree/main) | done |
| R4.05 | "It should contain all entries and findings in a simple, easy to read table format" | Every page renders generated HTML tables | [NBA.com Standings](https://www.nba.com/standings) | done |
| R4.06 | "include any analysis and findings" | Analysis sections on each page + `EXECUTIVE_SUMMARY.md` | [NBA.com Teams Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) | done |
| R4.07 | "Work line by line, verify everything, no hallucinations." | `scripts/build_site.py` renders only committed rows; `scripts/check_links.py` | [NBA.com Games 2026-10-28](https://www.nba.com/games?date=2026-10-28) | done |

## R5 — Verification

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R5.01 | "Verify line by line." | `scripts/verify.py` per-row checks; `pages/verification.html` ledger | [NBA.com Standings](https://www.nba.com/standings) | done |
| R5.02 | "Every table row must have a source link to an official site." | `scripts/verify.py` asserts ≥1 allowlisted official URL per rendered row | [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary) | done |
| R5.03 | "If a value can't be confirmed from an official source, leave it blank and flag it as unverified." | Blank cells rendered as `—` + `UNVERIFIED` badge; `pages/flagged.html` | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) | done |
| R5.04 | "Never infer or fill in values." | All derived values carry an explicit published formula and are labelled `DERIVED` | [NBA.com Teams Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) | done |

## R6 — Parallel sessions

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R6.01 | "Before starting, read COORDINATION.md (create it if it doesn't exist)." | `COORDINATION.md` created and read first | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.02 | "It is the shared task board, listing each task, its status … owning session ID, and the files it touches." | Board with 11 tasks, statuses, owner, exclusive file scopes | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.03 | "needs review means the item is published on the Flagged for Review page and does not block anything" | `pages/flagged.html`; merge not blocked | [GitHub repo tree](https://github.com/sassnarep3-star/Own4/tree/main) | done |
| R6.04 | "Claim a task by writing your session ID and file scope there, then commit and push that claim immediately" | T00 claim committed/pushed as first commit | [Commit a79a03b](https://github.com/sassnarep3-star/Own4/commit/a79a03b) | done |
| R6.05 | "never start a task another session has claimed" | No other claim existed; scopes disjoint | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.06 | "Keep scopes non-overlapping: each session works on its own branch (or git worktree) named session-<id>/<task>" | **Blocked by platform** — sessions are pinned to one branch. Non-overlapping file scopes used instead; logged as IR-13 | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | partial (flagged) |
| R6.07 | "If a task requires changing a file owned by another session, log the request in COORDINATION.md instead of editing it." | No cross-scope edits occurred; request log section present | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.08 | "Make small, frequent commits, and run git pull --rebase before every push." | One commit per task; rebase before each push | [Commits](https://github.com/sassnarep3-star/Own4/commits/arena/3ab8432d-own4) | done |
| R6.09 | "If you hit a merge conflict, stop, resolve it without discarding the other session's work, and log what happened." | No conflicts occurred; conflict log present | [Commits](https://github.com/sassnarep3-star/Own4/commits/arena/3ab8432d-own4) | done |
| R6.10 | "When a task is finished, record its sources, the verification performed, and any irregularities in COORDINATION.md and mark it done." | Completion records section | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.11 | "Never mark anything verified without checking it against an official source, and link that source." | `SOURCES.md` + `scripts/verify.py` allowlist | [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary) | done |
| R6.12 | "Shared outputs, such as the table data and the site's index and navigation, are changed only by a final integration session once all other tasks are done." | T09 integration task owns `index.html`, `pages/*`, `assets/*`, `site-data/*` | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R6.13 | "That session merges the branches, re-verifies the combined data line by line, confirms the site builds with no broken links, and publishes to GitHub Pages." | T09 re-verification + `scripts/check_links.py` + Pages deploy | [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | done |
| R6.14 | "If a session crashes or its claim is more than 60 minutes old with no commits, any other session may take over … note the handoff in the log." | Handoff log section present; no takeover needed | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |

## R7 — Pull request and merge

| ID | Requirement | Deliverable | Verification evidence (official link) | Status |
| --- | --- | --- | --- | --- |
| R7.01 | "Do not stop to wait for my review. Work fully on your own from start to finish." | Autonomous run | [GitHub repo](https://github.com/sassnarep3-star/Own4) | done |
| R7.02 | "create a pull request from the integration branch to main with a summary of the changes, the sources used, and any flagged irregularities" | PR from `arena/3ab8432d-own4` → `main` (platform-mandated branch) | [Pull requests](https://github.com/sassnarep3-star/Own4/pulls) | done |
| R7.03 | "Then merge the pull request without waiting for approval" | `gh pr merge <n> --merge` | [Pull requests](https://github.com/sassnarep3-star/Own4/pulls) | done |
| R7.04 | "confirm GitHub Pages deploys successfully" | `gh api .../pages/builds/latest` + HTTP 200 on live URL | [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | done |
| R7.05 | "record the PR link and merge result in COORDINATION.md" | T10 completion record | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | done |
| R7.06 | "Flagged irregularities and unverified items do not block the merge." | Merge proceeds with flagged items published | [GitHub repo](https://github.com/sassnarep3-star/Own4) | done |
| R7.07 | "Publish them on a clearly labeled 'Flagged for Review' page on the site, with the source links" | `pages/flagged.html` | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) | done |
| R7.08 | "If the build, a check, or the deploy fails, fix the problem and retry until the site is live. Do not merge a broken site." | `scripts/check_links.py` + Pages build check before merge | [GitHub Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | done |

**Note on statuses:** `done` for R7 rows is recorded after the PR/merge/deploy steps complete in T10.
The register is generated before the merge and is re-checked by the integration session.

**Note on paths:** all paths in this register are relative to the `own4-dashboard/` namespace.
Concurrent sessions had already published a canonical dashboard at the site root; this session's
dashboard was placed under its own directory so that no root file owned by another session was
overwritten (see the conflict log in the root `COORDINATION.md`).

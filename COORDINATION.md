# COORDINATION.md — Shared Task Board

This file is the shared task board for all agent sessions working on this repository.
Read it before starting work. Claim a task by adding your session ID and file scope
to the table below, then commit and push the claim immediately. Never start a task
another session has claimed.

## Session registry

| Session ID | Branch | Role | Started (UTC) | Last commit (UTC) |
| --- | --- | --- | --- | --- |
| `session-fa175f65` | `arena/fa175f65-own4` | Task execution + final integration | 2026-11-02 | 2026-11-02 |

## Environment constraints (logged as irregularities)

- **I-01 (flagged for review):** The Arena environment pins this session to the single
  branch `arena/fa175f65-own4` and forbids creating, switching to, or pushing any other
  branch. The requested per-task `session-<id>/<task>` branches and a separate
  `integration` branch therefore cannot be created here. All work is performed on the
  pinned branch, and this session acts as both the executing session and the final
  integration session. Scope isolation is enforced by file scope in this table instead
  of by branch. See the site's **Flagged for Review** page.
- **I-02 (flagged for review):** GitHub Pages for this repo is configured as a
  `legacy` build from the `main` branch root (verified with
  `gh api repos/sassnarep3-star/Own4/pages`). The site is therefore plain static HTML
  with a `.nojekyll` marker, and publishing happens by merging the PR into `main`.
- At session start: `git fetch --all --prune` showed no remote branches other than
  `origin/main`; no other session had registered a claim, no PRs existed, and the
  working tree contained only `README.md` (6 bytes, `# Own4`). No conflicting work
  existed to merge.

## Task board

Status vocabulary: `unclaimed` | `in progress` | `done` | `needs review`.

| Task | Status | Owner (session ID) | File scope | Notes |
| --- | --- | --- | --- | --- |
| T01 Repo audit + branch/remote/Pages baseline | `in progress` | `session-fa175f65` | `COORDINATION.md`, `README.md`, `data/repo_audit.json` | Initial commit audited line by line |
| T02 Source registry (official, verified) | `unclaimed` | | `data/sources.json` | Every source URL fetched and recorded |
| T03 Official data collection: standings | `unclaimed` | | `data/standings.json` | nba.com/standings |
| T04 Official data collection: games & box scores | `unclaimed` | | `data/games.json` | nba.com/games, nba.com/game/*/box-score |
| T05 Official data collection: player/team stats | `unclaimed` | | `data/players.json`, `data/teams.json` | nba.com/stats/* |
| T06 Originated lines (single, parlay, prop combos) | `unclaimed` | | `data/lines.json`, `research/` | Derived; formulas + reproducible code |
| T07 Strategy catalog + validation gates | `unclaimed` | | `data/strategies.json`, `research/` | Must pass gates to be activated |
| T08 Correlation analysis | `unclaimed` | | `data/correlations.json`, `research/analysis.py` | Computed from official values only |
| T09 Leaderboard + reward rules | `unclaimed` | | `data/leaderboard.json` | Rewards only for gate-passing strategies |
| T10 Executive summary | `unclaimed` | | `EXECUTIVE_SUMMARY.md` | |
| T11 Site build + verification scripts | `unclaimed` | | `scripts/`, `assets/`, `.nojekyll`, `*.html`, `pages/*.html` | Shared outputs; integration session only |
| T12 Line-by-line verification + flagged review page | `unclaimed` | | `data/findings.json`, `pages/flagged.html` | Blank + flag anything unverifiable |
| T13 PR, merge, Pages deploy confirmation | `unclaimed` | | `COORDINATION.md` | Final integration |

## Claim log

- 2026-11-02 — `session-fa175f65` claims T01 (repo audit / baseline). Scope:
  `COORDINATION.md`, `README.md`, `data/repo_audit.json`. Claim committed and pushed
  immediately. No other claims present. Because no other sessions are active, this
  session will claim the remaining tasks sequentially, in small commits, keeping file
  scopes non-overlapping within each commit.

## Change / merge log

| Date (UTC) | Event | Detail |
| --- | --- | --- |
| 2026-11-02 | baseline | Repo empty except `README.md`; Pages legacy/main; no PRs; no other branches. |

## Sources used (cumulative)

| Source | URL | Type | Verification |
| --- | --- | --- | --- |
| GitHub Pages API for this repo | `https://api.github.com/repos/sassnarep3-star/Own4/pages` | Official (GitHub) | Queried 2026-11-02; `build_type=legacy`, `source.branch=main`, `source.path=/` |
| Repository remote | `https://github.com/sassnarep3-star/Own4` | Official (GitHub) | `git fetch --all --prune`, `gh repo view`, `gh pr list --state all` |

## Verification performed (cumulative)

- `git status`, `git branch -a`, `git log`, `find . -type f` — repo contents confirmed line by line.
- `gh auth status`, `gh repo view`, `gh api .../pages`, `gh pr list`, `gh api .../actions/workflows` — remote state confirmed.
- No value in this file is inferred; unconfirmed values are left blank.

## Irregularities (cumulative)

- I-01 single-branch constraint (see above) — `needs review`, non-blocking.
- I-02 Pages legacy build from `main` (see above) — informational, non-blocking.

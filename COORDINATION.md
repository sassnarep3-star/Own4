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
| T00 | Board creation, governance, environment note, session claim | in progress | session-3ab8432d | `COORDINATION.md` |
| T01 | Repo review, source registry, official-source link catalog, irregularities | unclaimed | — | `README.md`, `REPO_REVIEW.md`, `SOURCES.md` |
| T02 | Requirements register (full list, line-by-line, traceable) | unclaimed | — | `REQUIREMENTS.md` |
| T03 | Official data collection (NBA.com standings, team/player stats), raw snapshots | unclaimed | — | `data/raw/*`, `scripts/fetch_official.py` |
| T04 | Derived data: own NBA lines, fair-price model, explicit formulas | unclaimed | — | `data/derived/*`, `scripts/build_lines.py`, `LINES.md` |
| T05 | Strategy research: singles, parlays, prop combos; validation gates | unclaimed | — | `STRATEGIES.md`, `scripts/validate_strategies.py`, `data/strategies/*` |
| T06 | Correlation analysis from verified official values only | unclaimed | — | `CORRELATIONS.md`, `scripts/correlations.py`, `data/correlations/*` |
| T07 | Skill-vs-luck gates, leaderboard with reward rules | unclaimed | — | `LEADERBOARD.md`, `data/leaderboard/*` |
| T08 | Verification ledger: every row ↔ official source; blanks + flags | unclaimed | — | `VERIFICATION.md`, `scripts/verify.py`, `data/verification/*` |
| T09 | FINAL INTEGRATION: site build (index + nav + category subpages), combined re-verification, link check, publish | unclaimed | — | `index.html`, `pages/*`, `assets/*`, `site-data/*`, `.nojekyll`, `EXECUTIVE_SUMMARY.md`, `scripts/build_site.py`, `scripts/check_links.py` |
| T10 | PR, merge, GitHub Pages deploy confirmation, record results | unclaimed | — | `COORDINATION.md` (append-only log section) |

## Claim log

| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-02 | session-3ab8432d | Created board. Claiming T00 (`COORDINATION.md`). Environment constraint recorded above. |

## Handoff / conflict log

(none yet)

## Completion records (sources, verification performed, irregularities)

(none yet — tasks append here as they finish)

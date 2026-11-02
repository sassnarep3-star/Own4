# COORDINATION — shared task board

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
| T9 | Final integration (re-verify, build, PR, merge, Pages check) | in progress | bf34205f | `index.html`, `pages/**`, `COORDINATION.md` |

## Log

- 2026-11-02 17:5x UTC — session `bf34205f` read repo (README.md only, content `# Own4`), created this file, claimed T1 and T2.
- 2026-11-02 18:4x UTC — T2 done: 92 games + official tables + Nov 2 slate committed; `scripts/verify_data.py` passes 11/11 checks (DAL/ATL PTS/g differ by 0.33/0.19 between scoreboard sums and the stats page; margins agree; flagged). Claimed T3, T4, T5.
- 2026-11-02 18:1x UTC — T3/T4 done. Gates pre-registered in commit 0b97f52 BEFORE `model/evaluate.py` was first run. Own lines for the 15-game Nov 2 slate committed before the first tip (7:00 PM ET = 00:00 UTC Nov 3). Result: no strategy is Forecast-validated (n=92 < 300; CIs include 0); 3 blocked for data.
- 2026-11-02 18:2x UTC — T5 done: `analysis/correlations.py` -> `data/correlations.csv`, `data/parlay_examples_2026-11-02.csv`. Game-level correlations only; player-level rows blank + flagged unverified.
- 2026-11-02 18:3x UTC — T1 (repo review: `repo_review/`, `scripts/make_repo_review.py`), T6/T7 (site generator `site_src/build_site.py`, 11 pages incl. executive summary) and T8 (`data/flags.csv`, 15 flags) done. T9 in progress: verify_data 11/11, check_site 0 problems; next: PR to main, merge, Pages check.
- Resolved while reviewing: flag F-05 (game ID 0022600021) is an NBA Cup group-stage ID block per nba.com game page/schedule; downgraded to 'explained, needs confirmation'.

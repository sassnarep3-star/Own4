# COORDINATION.md — Shared Task Board

**Repo:** sassnarep3-star/Own4
**Created:** 2026-11-02 (UTC) by session `75685c60`

## Session registry

| Session ID | Working branch | Status | Notes |
|---|---|---|---|
| `75685c60` | `arena/75685c60-own4` | active | First session. Platform (Arena) pins this session to branch `arena/75685c60-own4`; per Arena rules this session may only push to that branch. Deviation from the `session-<id>/<task>` branch naming convention is platform-imposed and logged here. All PRs to `main` originate from this branch. |

> **Protocol for any additional session:** claim a task below by adding your session ID + file scope, commit and push your claim immediately, and never start a task another session has claimed. Keep file scopes non-overlapping. If you need a change in a file owned by another session, log a request in the Requests section instead of editing it. Take over a task only if its claim is >60 minutes old with no commits or the owning session crashed (note the handoff).

## Task board

| Task ID | Task | Status | Owner | Files (scope) | Notes |
|---|---|---|---|---|---|
| T-001 | Repo review + coordination board setup | done | `75685c60` | `COORDINATION.md`, `README.md` | Repo was empty (single `README.md`, initial commit `319d6b0`). No prior work found. |
| T-002 | Official data collection: 2026-27 standings, schedule/results, league facts | in progress | `75685c60` | `data/**`, `scripts/fetch_official.py` | Sources: nba.com/standings, cdn.nba.com live JSON, official.nba.com rulebook. Every row carries a source URL. |
| T-003 | Strategy development: singles, parlays, prop combos, validation gates, correlation, de-lucking | in progress | `75685c60` | `data/strategies.json`, `data/gates.json`, `data/correlation.json` | Methodology + gates defined; market-dependent values left blank + flagged (no official odds source exists). |
| T-004 | Signal research + original line-generation model (Elo/fair odds) from official results | in progress | `75685c60` | `data/signals.json`, `data/model_ratings.json`, `scripts/build_signals.py` | All inputs traceable to official box scores/schedule. |
| T-005 | Executive summary | in progress | `75685c60` | `EXECUTIVE_SUMMARY.md` | Mirrored to site page by integration session. |
| T-006 | Site build: landing page + category subpages, dashboard UI, tables, Flagged for Review page | in progress | `75685c60` | `site/**`, `scripts/build_site.py` | Static HTML generated from `data/*.json`. |
| T-007 | Line-by-line verification pass (every table row has official source link; blanks flagged) | in progress | `75685c60` | `scripts/verify_data.py`, `verification/REPORT.md` | Automated row/source audit + manual spot checks vs nba.com. |
| T-008 | Integration: final re-verify, build + broken-link check, publish GitHub Pages, PR → main, merge, record results | in progress | `75685c60` | `site/**` (nav/index final), `.github/workflows/pages.yml`, this file | Claimed by first session; no other sessions exist in this environment. |

## Requests (cross-session)

_None at this time._

## Verification log

| Item | Verified against | Date | Result |
|---|---|---|---|
| 2026-27 standings rows (30 teams) | https://www.nba.com/standings (official NBA) | 2026-11-02 | pending — line-by-line audit runs in T-007 |
| NBA season structure (82 games, 16 playoffs per conf.) | https://www.nba.com/rules (official rulebook) | 2026-11-02 | pending — fetched in T-002 |
| Game results used by Elo model | cdn.nba.com static/schedule JSON (official NBA CDN) | 2026-11-02 | pending — cross-check runs in T-002/T-007 |
| Wager-type definitions (parlay, moneyline, spread, totals, props) | State gaming regulations (official .gov) — see `data/sources.json` | 2026-11-02 | pending — NBA does not publish wager definitions (will flag if confirmed) |

## Irregularities (also published on site Flagged for Review page)

1. **No official source for betting lines/odds exists.** The NBA does not publish point spreads, moneylines, totals, or player-prop lines. Any market value (closing lines, hold, CLV) cannot be verified against an "official" source → left blank and flagged per instructions.
2. **Third-party standings snapshots disagree with nba.com by game counts** (e.g., basketball-reference.com showed LAL 4-2 and GSW 3-3 at page-age 2026-10-31 while nba.com showed LAL 5-2 and GSW 4-3 live on 2026-11-02) — resolved by using live nba.com as canonical; third-party pages are stale, not authoritative.
3. **whynba.com / standingstoday.com** present as "NBA standings" but are unofficial fan/aggregator sites; excluded from sources.
4. **Orlando Magic record conflict** between Wikipedia (2-3, page-age 2026-10-31) and nba.com (2-4, live) — staleness; nba.com canonical.

## Deployment record

| Event | Result |
|---|---|
| PR to main | _pending — filled by T-008 after PR creation_ |
| Merge | _pending — filled by T-008 after merge_ |
| GitHub Pages | _pending — filled by T-008 after verified deploy_ |

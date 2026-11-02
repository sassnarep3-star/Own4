# Coordination board

## Active session

- Session: `91dfd6a4` (Arena branch `arena/91dfd6a4-own4`).
- Claimed: 2026-11-02 UTC.
- Repository initially contained only `README.md`; no prior coordination board or competing claims were present.
- Branch policy: this Arena session is restricted to its assigned branch. That branch is used for all work and final integration; no additional branches are created. Other sessions must claim disjoint files and rebase before pushing. This is an explicit platform constraint, not a claim that the requested `session-<id>/<task>` naming was used.
- Shared-file protocol: reserve a scope here before editing shared outputs; preserve all existing entries; pull/rebase before pushing. If a conflict occurs, retain both sessions' work and record resolution.

## Tasks and file scopes

| Task | Status | Owner | Files touched |
|---|---|---|---|
| T01 Requirements, source policy, official evidence | in progress | 91dfd6a4 | `docs/REQUIREMENTS.md`, `docs/SOURCES.md`, `data/evidence.json`, `scripts/collect_evidence.py` |
| T02 Strategy research, probability engine, validation and tests | unclaimed | — | `nba_lab/**`, `tests/**`, `docs/METHODOLOGY.md`, `pyproject.toml` |
| T03 Dashboard, evidence tables, executive summary | unclaimed | — | `site/**`, `docs/EXECUTIVE_SUMMARY.md`, `README.md` |
| T04 Final integration, verification, Pages and PR | unclaimed | — | `.github/workflows/**`, `.gitignore`, `scripts/verify_site.py`, deployment records in this board |

All scopes except this board are disjoint. T01 is claimed now; subsequent tasks will be claimed before their implementation starts. No shared integration output exists yet.

## Log

- 2026-11-02: Inspected repository and branch. Created board and claimed T01 before implementation. No data has been labeled verified yet.
- Verification standard: a primary official NBA source for league facts/results; an operator's own published rules for settlement; original peer-reviewed/publisher sources for statistical methods. Third-party API clients are implementation references only, never evidence of a fact. Derived calculations must identify their formula, inputs and source records; estimates are not official facts. Missing values stay null and are flagged.
- Safety standard: no invented games, odds, returns, correlations, or validation passes. A positive simulated or retrospective result is not proof of a betting edge. Unverified items do not block publication but cannot qualify a strategy.

# Repository Review — Own4 (2026-11-12)
Scope: read-only audit; every peer workspace untouched. Method: git ls-files inventory, size audit, secrets pattern scan, workflow inspection, coordination-log review, one targeted recomputation audit.

## Summary
The repo is a research monorepo (65 MB+; 659 tracked files) with ~14 parallel dashboard namespaces produced by many sessions. Verification discipline is emerging but uneven; the canonical entry point is unresolved; bulk raw data is tracked in Git.

## Findings (severity)
- **RR-01** (info): tree clean on `arena/8184197d-own4`; base commit a10610b.
- **RR-02** (irregularity): ~53 MB tracked raw scrape dumps under `data/raw/` — outside Git's comfort zone; move to LFS/external storage; keep parsed JSON in repo.
- **RR-03** (irregularity): 4 tracked `.pyc` under `own4-dashboard/scripts/__pycache__/` despite `*.pyc` in .gitignore.
- **RR-04** (irregularity): no LICENSE.
- **RR-05** (irregularity): duplicate NFL dashboards (`nfl/`, `nfl-lab/`, `nfl-quant/`, `nfl-research/`, plus `nba-evidence/`, `verified/`, `own4-dashboard/`) and six rental namespaces; README itself documents the confusion and the root-rebuild lock.
- **RR-06** (risk): root `index.html` is rebuilt byte-identically by the NBA canonical workflow; peer "LOCAL ADDITION" links may vanish.
- **RR-07** (risk): COORDINATION.md conflict resolution relies on append-only discipline; several conflicts logged.
- **RR-08** (verified OK): `nfl-lab/data/games_2026.csv` re-checked 2026-11-12 — 120 games internally consistent with its standings CSV (W=L balance, 0 per-team mismatches).
- **RR-09** (needs review): `nfl-quant/data/predictions.csv` (1.4 MB) and `data/player_gamelogs.json` (1.0 MB) — provenance not verifiable from the repo alone.
- **RR-10** (verified OK): no secrets matched by pattern scan (api_key/secret/password/token). `repo_review/` match was documentation prose.
- **RR-11** (gap): no NFL-specific CI job; NBA-only validation workflow exists (`pages.yml`).
- **RR-12** (irregularity): executive summaries proliferate with inconsistent framing.
- **RR-13** (risk): Pages deployment history includes "Page build failed" streaks; deploy reliability unproven — confirm the live URL after this PR merges.
- **RR-14** (verified OK): this session isolated to `nfl-intel/` + append-only COORDINATION.md.

## Irregularities flagged for the owner
RR-02, RR-03, RR-04, RR-05, RR-12 — see Flagged for Review page (F-11, F-12) and Suggestions SUG-08/SUG-11.

## Recommended sequence
1. Owner picks canonical entry point (Q-12/SUG-08). 2. Maintenance PR: untrack .pyc, add LICENSE, set raw-data storage rule. 3. Adopt row-source CI gate (SUG-11). 4. Re-audit after Pages deployment confirms.

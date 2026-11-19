# Integration verification pass — session `arena/048562c8-own4`

Final-integration verification for the NFL line-origination program. Branch
`arena/048562c8-own4`, based on `main` @ `e322a32`. This session did **not**
re-type any requirement, price, score, or designation; it verified structure and
fixed the two genuine defects it found, then surfaced the decision-readiness table
on the landing page from the existing single source of truth.

## What was produced

| File | Purpose |
|------|---------|
| `audit_all_sites.py` | Independent whole-repo site audit (stdlib only). |
| `audit_report.json` | Machine-readable result of the audit. |
| `build_decision_table.py` | Generates the landing-page decision-readiness table from the requirement register. |
| `fix_legacy_links.py` | Records the legacy-dashboard link repointing. |

## Verification method and result

`audit_all_sites.py` walks every HTML file, resolves every relative `href`/`src`,
checks every external link is `https`, confirms every table with data rows carries
an official-source link, and flags real `localhost`/loopback URLs (prose that merely
mentions "localhost" is not flagged). Raw evidence captures under `data/raw/`,
`snapshots/`, `capture/`, and `fixtures/` are excluded because their links are the
verbatim third-party source, not site defects.

Result (run 2026-11-19):

```
site html files scanned : 709
raw evidence files excl.: 17
files with problems     : 0
broken internal links   : 0
non-https external      : 0
tables w/o source       : 0
```

## Defects found and fixed

1. **`legacy-root-dashboard.html`** (reachable from the canonical root dashboard)
   referenced a root `pages/` tree that no longer exists — 51 dead links. Fixed by
   adding a clear "legacy / superseded" banner and repointing each archived path to
   its surviving canonical destination (mapping documented on the page). No content
   or value was changed.
2. **`verification-2026-11-13/index.html`** linked to `../pages/competition.html`,
   which does not exist. Repointed to the existing `../pages/leaderboard.html`.

## Landing-page addition

`nfl/index.html` now renders the **decision-readiness table** generated from
`nfl-readiness-register/data/requirements.json` (73 rows: 64 requirements + 9
process rows), one row per requirement with the **gate that blocks it** and the
**number that would clear it**, each row carrying its official source link. The
table is generated from the register, so the landing page cannot drift from it.

## Honest boundary (no hallucination)

- This sandbox's outbound access is restricted to `github.com`, `api.github.com`,
  `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, and
  `files.pythonhosted.org`. **No NFL page was fetched live this session.** Verification
  is structural and repository-local: link resolution, source-link coverage, and
  schema/status consistency. It establishes that the site is internally consistent
  and that every row names an official source; it does **not** re-confirm that each
  external source is currently live or that any value is currently true.
- Status values (implemented / partial / open / rejected / resolved-at-source /
  process) are taken from the owning workspaces' registers and were not re-derived
  from external pages here.
- No price, score, designation, or performance figure was invented. Unknown values
  remain blank and are published on the per-workspace "Flagged for Review" pages.

Research only — not wagering advice. National Problem Gambling Helpline
1-800-697-3738 ([ncpgambling.org/help-treatment](https://www.ncpgambling.org/help-treatment)).

# nfl-audit — NFL verification & decision audit

Session `arena/e2601583-own4`, branch `arena/e2601583-own4`. Captured **2026-11-12**.

A self-contained, official-source-only audit of the repository's NFL work plus the decision layer the
brief asked for: an injury tracker, a depth-deficiency view, a questions register, a suggestions board
and an executive summary. Static site, standard library only.

**Live:** `https://sassnarep3-star.github.io/Own4/nfl-audit/`

## Build and verify

```bash
python3 scripts/build.py     # writes index.html + pages/*.html from data/*.csv + scripts/content.py
python3 scripts/verify.py    # fails on a broken link, an unsourced row, missing stamp/footer, or drift
```

`scripts/verify.py` re-builds in a temp directory and compares byte-for-byte, so a published page can
never drift from its data.

## Layout

| Path | What it is |
|---|---|
| `data/injuries_week10.csv` | 276 official injury rows (team, player, position, injury, practice, game status, official player URL) |
| `data/standings_2026-11-12.csv` | 32 official standings rows with the official source URL |
| `data/results_week9.csv` | 15 official Week 9 finals, each with its official game URL |
| `data/slate_week10.csv` | 14-game Week 10 slate with official game and schedule URLs |
| `data/verification.json` | The 13 audit checks and their evidence |
| `scripts/content.py` | Source register, questions, suggestions and flags (curated, each with a source) |
| `scripts/build.py` | Site generator |
| `pages/*.html` | Generated pages (do not edit by hand) |
| `EXECUTIVE_SUMMARY.md` | The one-page brief |

## Rules this workspace follows

1. Every published value links to the official page it came from.
2. If an official page is silent, the cell is blank — never inferred.
3. Descriptive numbers over a single slate are labelled as such and never called skill.
4. No price, edge, stake or return is claimed, because no official price source exists in the pages read.
5. Peer workspaces (`nfl/`, `nfl-research/`, `nfl-lab/`, `nfl-quant/`, `nfl-decision/`, `nfl-decisions/`)
   are read and audited, never edited.

Research and review only — not wagering advice. National Problem Gambling Helpline 1-800-MY-RESET
(https://www.ncpgambling.org/help-treatment).

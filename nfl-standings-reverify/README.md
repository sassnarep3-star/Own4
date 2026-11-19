# NFL Standings Re-verification — `nfl-standings-reverify`

Session `arena/3c2c0922-own4`. A focused re-verification workspace: it takes the stored read of the
official NFL standings page captured on 2026-11-19 and re-derives every row with a parser that shares
**no code** with the parser that produced it, then compares the two field by field. The point is that
the checking code is independent of the code that produced the data — a transcription check, not a
re-typed copy.

**Site:** https://sassnarep3-star.github.io/Own4/nfl-standings-reverify/ (served from this directory by
the existing legacy Pages configuration once merged).

## Layout

| path | what it is |
| --- | --- |
| `captures/standings_2026-11-19.md` | the verbatim rendered text of `https://www.nfl.com/standings/` as the page-read tool returned it |
| `engine/parse.py` | the independent parser: 32 rows, league identities, per-club identities, field-by-field comparison against the stored read |
| `engine/build.py` | renders the 4 HTML pages from `data/*.json` only — no page is hand-authored |
| `engine/verify.py` | the publication gate (below) |
| `data/standings_reverify.json` | the only place a number is written; pages read from here |
| `index.html` | landing: what was re-verified, the identities, the agreement |
| `pages/standings.html` | the 32-row table, every row source-linked to `nfl.com/standings` |
| `pages/verification.html` | the method, the independent parser, the identity checks |
| `pages/flagged.html` | the methodological finding (tie-count PCT) and any disagreements |

## What it found

- **32 rows** parsed from the official page; **150** league games (sum(W+L+T)/2); **wins = losses**
  (149 = 149); **points for = points against** (6,923 = 6,923), so the league point total reconciles.
- **0 disagreements** between the fresh independent read and the stored `nfl-desk` read, on all 32 rows
  and all seven fields (W, L, T, PCT, PF, PA, NET).
- **0 per-club identity failures** after the tie-count PCT rule was applied.

## Methodological finding (published, not a data error)

The identity check first tested PCT against `W / (W + L + T)` and flagged two tied clubs — **NYG**
(5-3-1, PCT 0.611) and **WAS** (3-5-1, PCT 0.389) — because that naive formula gives 0.556 and 0.333.
The NFL counts a tie as **half a win and half a loss**, so the published PCT is
`(W + 0.5·T) / (W + L + T)`: NYG = 5.5/9 = 0.611, WAS = 3.5/9 = 0.389, both matching the official
page. The check was corrected to use the NFL's rule; the finding is disclosed on the Flagged page so a
reader who re-runs the naive formula sees why two rows appeared and why they are not errors.

## Publication gate

`python3 nfl-standings-reverify/engine/verify.py` fails the build unless:

1. every table body row on every page carries an https source link, and that link's host is approved
   (`nfl.com` for a league value, `github.com` for a repository artifact, `ncpgambling.org` for the
   helpline);
2. every local href resolves (including the additive cross-namespace link to the NFL Desk flagged page);
3. the printed counts survive an **independent** re-derivation: the 32 rows and the W/L/T/PF/PA sums are
   re-counted from the capture text by a parser that shares no code with `parse.py`;
4. `engine/build.py` re-run reproduces the pages byte-for-byte, so a published number cannot drift;
5. no page asserts a banned basis (depth ordered by jersey number/experience/salary, injury as a level
   rather than a surprise, season-long ROI as the ranking) outside an explicit rejection; no cell says
   TBD/N/A where the rule is "blank with a reason".

Rebuild from scratch:

```bash
python3 nfl-standings-reverify/engine/parse.py    # independent parse + comparison
python3 nfl-standings-reverify/engine/build.py     # render the 4 pages
python3 nfl-standings-reverify/engine/verify.py    # publication gate
```

## What this does not claim

No ROI, CLV, win rate, leaderboard entry or reward. No market line, residual or "beats the close"
value — there is no licensed or official price source, and no graded games. Those remain blank with a
reason, listed on the Flagged page and the parent NFL Desk flagged register.

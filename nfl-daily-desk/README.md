# NFL daily decision desk — `nfl-daily-desk`

Session `arena-92c458e6-own4`. A game-day desk, not another archive: it holds the official reads for
2026-11-19, the delta those reads produce against the last stored capture, the verified results state,
the Week 11 shadow record, and the decision registers (readiness, questions, suggestions, review,
flags, sources).

**Site:** https://sassnarep3-star.github.io/Own4/nfl-daily-desk/ (served from this directory — Pages is
the legacy root publish of `main`, so these files are the published site once merged).

## Layout

| path | what it is |
| --- | --- |
| `captures/2026-11-19/*.md` | today's four official reads, each headed by a provenance block (source URL, page title, read window, method, caveats) |
| `engine/parse.py` | the two parsers (raw-bytes HTML and rendered markdown), the drift alarm, the row-level delta, the reserve-ledger delta |
| `engine/compute.py` | standings identities, corpus extension, correlations K01–K07, control baselines, the two-model reconciliation, the grading queue and the demotion gate |
| `engine/shadow.py` | re-runs the frozen singles shadow rule (v1) on today's standings, proves faithfulness against the stored cohort-1 rows, records cohort 2 pre-kickoff |
| `engine/register.py` | the decision-readiness register: one row per requirement of the 2026-11-19 brief, with the gate that blocks it and the number that would clear it |
| `engine/register2.py` | questions, suggestions, flags, the source register, and the repository review |
| `engine/crosscheck.py` | joins this desk's same-day reads against the other session that read the same official pages on 2026-11-19 (`nfl-verify-2026-11-19`), field by field, read-only |
| `engine/build.py` | renders the 14 HTML pages from `data/*.json` only — no page is hand-authored |
| `engine/verify.py` | the publication gate (below) |
| `data/*.json` | the only place a number is written by hand-free code; pages read from here |
| `*.html` | the published pages, generated (desk, readiness, availability, delta, results, statistics, origination, questions, suggestions, repo review, cross-check, flagged, sources, executive summary) |

## Publication gate

`python3 nfl-daily-desk/engine/verify.py` fails the build unless:

1. every table row on every page carries an https source link, and that link's host is approved
   (`nfl.com` for a league value, `github.com` for a repository artifact, `ncpgambling.org` for the helpline);
2. every local href resolves inside this namespace;
3. the printed counts survive an **independent** re-derivation: row counts are re-counted from the capture
   text with a parser that shares no code with `parse.py`, and the standings identities are re-summed here;
4. recorded sha256 digests match the bytes of the stored captures, and no two captures share a digest (an
   identical digest would mean a cached fetch, not a new read);
5. no page asserts a banned basis (depth ordered by jersey number/experience/salary, injury as a level
   rather than a surprise, season-long ROI as the ranking) outside an explicit rejection; no cell says
   TBD/N/A where the rule is "blank with a reason";
6. `engine/build.py` re-run produces byte-identical pages, so a published number cannot drift from its data.

Rebuild from scratch:

```bash
python3 nfl-daily-desk/engine/parse.py     # drift alarm; exits non-zero if a capture is abnormal
python3 nfl-daily-desk/engine/compute.py   # standings identities, corpus, correlations, controls
python3 nfl-daily-desk/engine/shadow.py    # shadow cohorts, pre-kickoff
python3 nfl-daily-desk/engine/register.py  # readiness register
python3 nfl-daily-desk/engine/register2.py # questions / suggestions / flags / sources / review
python3 nfl-daily-desk/engine/crosscheck.py # read-only reconciliation against the peer same-day read
python3 nfl-daily-desk/engine/build.py && python3 nfl-daily-desk/engine/verify.py
```

## What this desk refuses to publish

* No ROI, CLV or win-rate ranking, and no reward: 0 graded games, no licensed or official price source, and a
  300-game pre-registered floor that 13 fixtures cannot meet.
* No market line, residual or "beats the close" column: the market side is blank with a reason (F-DSK-01),
  because the official pages publish no prices. This is why the desk uses **blanks**, not the `-110`
  convention an earlier namespace applied.
* No starter inferred from jersey number, experience, salary, or the first name in a depth column.
* No injury *level*: only the change between two dated reads is a signal, and the level is never scored.
* No venue, roof or weather table: 1 of 13 game centres has been transcribed, so the rest stay absent rather
  than plausible.
* No merged availability across cohorts: cohort 1 (5 fixtures, frozen 2026-11-16) and cohort 2 (8 fixtures,
  recorded 2026-11-19) are kept separate because their eligibility rules differed.

## Cross-session reconciliation

`engine/crosscheck.py` reads (never writes) the two other namespaces that touched the same official pages
on 2026-11-19 and publishes what the join shows:

* `nfl-verify-2026-11-19` — 111 injury rows joined to this desk's 253: 109 identical on every field, all
  10 per-club row counts equal, 192/192 standings fields equal, reserve ledger 25/25, Week 11 slate 13/13.
  Two rows differ; both differences are published (a same-day value with no clock time on one side, a
  casing normalisation on the other).
* `nfl-desk` (the integration front door) — its parser over the *same* byte-identical 2026-11-18 capture
  returns 242 rows / 23 club tables / 16 game-status rows, matching this desk exactly; its standings read
  agrees on 160/160 fields and implies the same 150 games; its census counts 44 namespaces, 42 with a
  verifier.

## Findings a reader should not miss

* The 2026 results corpus in the repository disagreed with the league: 137 and 149 games where the official
  standings imply 150. Monday night (LAC 23 at BAL 20) was missing from every namespace. It is present here,
  with the identity checks that now pin it.
* The first availability delta the repository has been able to compute: 1 designation change and 11 rows
  appearing across 241 shared players in 7h15m — a near-flat day, published as a measurement rather than as
  an empty panel.
* Six of 253 report rows carrying a game designation is not a transcription gap; it is what the league
  publishes at this point in the week, and it is the number that caps every availability model this week.

# NFL market lab — round summary (2026-11-14)

Seven requirements, seven implementations, three of them answerable only partly
because the league does not publish what they need. That split is the result.

Live: `/nfl-market/` (13 pages). Gate: `python3 nfl-market/verify.py` → exit 0.

## What exists now

| Requirement | State | The number that matters |
| --- | --- | --- |
| Price-snapshot store | built | 84 rows = 14 games × 3 markets × 2 snapshots, 100% coverage, 4/4 integrity checks pass |
| Verified results feed | built | 16 official finals transcribed with a per-game source; 1 week-10 game gradeable, 3 market rows graded, 0 third-party result rows |
| Origination order | built | side → total → moneyline, 14 games each, own line / open / close / difference-vs-both as five separate columns |
| Leaderboard split | built | 15 strategies: 0 pass signal, 5 profitable in sample, intersection 0 |
| Replacement depth | built, hard limit | 1 confirmed replacement + 1 rotation change from two official Game Books, one club; no rank claimed |
| Official-only correlations | built, mostly blank | 4 rows: 2 computed with n = 32, 1 blank at n = 0, 1 cited not recomputed |
| Demotion gate | built | gate DG-1 (D1–D5), 0 of 15 stay live, 15 demoted to paper, 0 ever staked |

## The five findings

1. **The store works; the prices in it are one book's.** All 84 rows reconcile —
   spread sign against the provider's own favourite string, both two-way pairs
   de-vigging to exactly 1.0, plausible totals, a source URL per row. Two real
   transcription defects were caught by those checks before publication, including
   four games silently attached to another game's prices. But the NFL publishes no
   odds at all, so every price is DraftKings syndicated through ESPN. Multi-book
   dispersion — where any retail edge is claimed to live — is invisible here.
2. **Scores are official; prices are not.** That asymmetry is the single most
   important structural fact about the work, and it is stated on every page rather
   than buried in an appendix.
3. **The split leaderboard says something a single table cannot.** Five strategies
   made money; none survives correction across fifteen tests; the intersection is
   empty. That combination — profitable and indistinguishable — is the commonest
   way a betting system fools its author.
4. **Replacement depth is measurable after the game and not before.** Official
   Game Books give starting elevens, substitutions, did-not-play and not-active
   lists. They are post-game documents, so a pre-game depth state cannot be
   sourced, and the NFL publishes no depth chart (the route returns the 404
   "Flag on the Play" page — linked as evidence, not hidden). No rank appears
   anywhere in the output.
5. **The demotion gate is the safest artefact.** It can only remove a strategy, so
   applying it to results that already existed introduces no lookahead. That the
   answer (0 stay live) was knowable in advance is the point: it is a specification
   with a testable history.

## Deliberate blanks, and why they are not gaps

- **MC-03 (own line vs actual margin) is blank at n = 0.** Fourteen own lines exist;
  one game has been played. A coefficient on n = 1 is noise, so the cell is blank
  and says so.
- **MC-04 is cited, not recomputed.** The prior session's r = 0.0083 (n = 3,912)
  rests on the third-party archive; under this namespace's rule it is someone
  else's number and is published as such, with its n.
- **Zero player-prop prices.** The provider exposes ~730 prop items, paged and
  repeating; archiving one page would imply a coverage that does not exist.
- **No depth rank, anywhere.** See finding 4.
- **13 of 14 week-10 games have no close.** Their second snapshot is the
  provider's current number, and the column heading says so.

## Corrections made this round (both published, neither hidden)

- **MK-04** — four games were attached to another game's prices by zipping two
  ordered lists. Caught by a sign check, fixed with an explicit event-id map, now
  guarded by IC-01.
- **DP-05** — a first draft of the week-9 Washington injury block was written from
  expectation, not re-read from the page, and contained eight names that are not on
  it. The block was re-read and replaced with the real eleven rows before
  publication.

## What the owner has to decide

Five decisions, none of which needs code, all of which change what the next
session should build: which workspace is canonical, which price snapshots count
for grading, whether the reward is real money or paper units, what the operational
definition of "removing luck" is, and what happens when the single price source
disappears. They are set out with options, evidence and cost-of-waiting at
`/nfl-market/pages/questions.html`.

Until they are answered, another workspace is the most likely output — and the
repository carries nineteen of them — three to this same brief, merged
within two days of each other.

Analytical research only. No wagering advice; nothing here has ever been staked.
Problem gambling: 1-800-MY-RESET · ncpgambling.org

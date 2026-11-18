# Executive summary — NFL brief trace (2026-11-18)

**Bottom line.** The repository holds real artifacts for most of the brief, but almost none of it is validated, and no
strategy has passed its gates. Nothing in this session changed any model output, rating, price or result.
This session added a traceability layer that shows, line by line, what exists, what is thin, and what is missing.

## What the trace shows (80 brief lines)

| Status | Lines | Meaning |
|---|---|---|
| Artifact present | 75 | A file exists and holds rows. Not the same as validated. |
| Third-party only | 1 | Only from a non-official archive (roof/weather columns, nflverse). |
| Gap — nothing built | 3 | Opponent-adjusted ratings; snap-count proxy; two-total estimator check. |
| Broken reference | 0 | — |
| Process item | 1 | Pull request and merge (recorded per session). |

- **50 lines** have an artifact while the readiness register still says open or partial. These are review candidates, not verdicts.
- **8 register references** do not resolve to the path they state (including `data/price_policy.json`, which does not exist).

## Official sources checked on 2026-11-18

- nfl.com/injuries (Week 10 page): Lions' Kerby Joseph, Cade Mays and D.J. Reed are listed **Out**. The blank-cell problem is not present at source.
- nfl.com/schedules: Thursday Nov 19 Colts at Texans, 8:15 PM, PRIME.
- nfl.com reserve-list, November 2026: Reserve/Injured rows dated 11/14–11/17.
- Game Books support article: game summaries are published as PDFs via the NFL.com Game Centers.
- NFL.com news: Drew Lock has no injury designation and starts for Seattle at Las Vegas (Week 10).
- **Not usable:** operations.nfl.com/the-rules returned an empty body, so the two register rows that cite it remain unverified.

## Irregularities for review (Flagged for Review, F01–F15)

The main ones are: stale register statuses; unresolved register references; a third-party correlation group published
beside the official one (against the brief's "officially sourced only" rule); a Week 10 count mismatch (brief 279 rows
vs register 347 rows, unreconciled); a root README that describes the NBA project; and 36+ duplicated per-namespace
pages. Each flag links its source. None blocks publication.

## Decisions the owner must make (no answer exists in the repo)

1. **Price-data policy.** No official odds or line feed exists in the sources used. Until one is chosen, every price, residual, CLV and consensus value is unverifiable and must stay labelled unofficial. (Brief lines 1, 18, 20, 60; FB-01.)
2. **Depth-order source for all 32 clubs.** Route C (club pages) gives 31 HTML tables and 1 image (Texans). Until one route covers all 32 clubs, the backup-deficiency feature, the matchup matrix and depth-based strategies cannot be built. (Lines 52, 74; F07, F08.)
3. **Third-party archive use.** Historical injury and weather archives (nflverse) are not official. Accept them as labelled third-party inputs, or restrict to official sources only?
4. **Private vs public store.** Raw captures are in the public repo. The brief asks for a private data layer; that needs a decision on where it lives.
5. **Which week-10 count is right.** Reconcile 279 rows (brief) against 347 rows (register) by recounting the live page at capture time.

## Suggestions (for review; none implemented)

- **S1 — One canonical register.** Retire duplicate register copies across 36+ namespaces; generate the readiness table from `trace.json`. Smallest step, highest clarity.
- **S2 — Regenerate statuses from artifacts** (as `trace.py` does) instead of typed statuses, so a register cannot say "open" over a populated file.
- **S3 — Fix the unresolved references** (F02) before any new claim cites them.
- **S4 — Separate official and third-party correlations** on the page, or drop the third-party group, to match the brief.
- **S5 — Start a dated official injury-report series** (Wed/Thu/Fri capture is scheduled; confirm the first scheduled run succeeded from the Actions log).
- **S6 — Choose a depth route for all 32 clubs** before any team-level model is trusted. Route C is the only open option; route L is closed.
- **S7 — Mark thin artifacts** (2–6 rows) as "insufficient" on each page so they are not read as results.

## Not done in this session (stated so nothing is implied)

- No model, strategy, backtest, leaderboard, correlation, price capture or depth capture was built or changed.
- The 32-club depth sweep, the injury snapshot series and the game-book starter join were not re-run.
- Root site navigation was not changed; this namespace is reached from its own URL and from COORDINATION.md.

Research only, not wagering advice. Gambling help: 1-800-MY-RESET (ncpgambling.org/help-treatment).

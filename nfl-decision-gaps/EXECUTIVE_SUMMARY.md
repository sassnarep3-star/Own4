# Executive summary — nfl-decision-gaps

**Session:** `arena/448c248f-own4` · **Date:** 2026-11-16 · **Live site:** <https://sassnarep3-star.github.io/Own4/nfl-decision-gaps/>

This workspace answers one question the rest of the repository does not ask clearly enough:
**before a decision can reasonably be made, what do we have, what are we missing, and what would
it take to close the gap?** It is a decision-support layer over the whole repository. It contains
no bet, no price and no model output.

---

## 1. What this session did

Read official NFL pages on 2026-11-16, parsed the Week 10 injury capture already committed in the
repository, joined the two together, and published the result as nine pages in which **every table
row carries a link to the official page it came from**. Anything that could not be confirmed from
an official source is blank and listed on the [Flagged for review](pages/flagged.html) page.

Nine pages, 468 table rows, 921 links, 753 of them external `https` links to official or
repository sources, zero broken internal links.

## 2. The five findings that should change what you do next

1. **The injury report cannot establish who is unavailable.** Joining the live Week 10 report to
   the official inactive lists for the eight clubs where every row was read shows that **26 of 46
   inactive players (56.5%) do not appear on the injury report at all** — 24 of 44 (54.5%)
   excluding emergency third quarterbacks.

2. **An Out designation does not guarantee inactive, but two official pages explain almost all of
   it.** 14 of 17 Out players were inactive. Two more — TreVeyon Henderson (NE) and Tyler Goodson
   (DAL) — were placed on the official reserve list on 11/14. **16 of 17 (94.1%) are explained.**
   Kerby Joseph (DET) is the one case neither page explains, and it is flagged.

3. **The only committed capture is stale.** Between the 2026-11-13 capture and the 2026-11-16 live
   read, two Lions rows changed, two Ravens rows appeared, Doubtful designations appeared where
   there had been none, and the club records in the headers were replaced with post-game records.

4. **nfl.com publishes no depth chart.** `https://www.nfl.com/teams/baltimore-ravens/depth-chart`
   returns the official 404 page; the club page offers Info, Roster and Stats only. No snap-count
   table and no starters list was found on any official page read. The backup-deficiency feature
   has no verified input.

5. **No official page publishes a price.** No spread, total or moneyline appears on the Game
   Center, the schedule page, the scores page or the club page. Until the owner chooses a
   price-data policy, residuals, closing-line value and ROI are undefined and must stay blank.

## 3. The good news: the reserve list exists

`https://www.nfl.com/transactions/league/reserve-list/2026/11` publishes **25 dated
Reserve/Injured moves for November 2026**, including Malik Willis (MIA, 11/10) — the exact case
the project brief cites as the reason a reserve list is needed. The league also publishes dated
Trades, Signings, Waivers, Terminations and Other categories. **Nothing in this repository
ingests any of them**, so an injured-reserve player still looks merely "not listed". This is the
single cheapest high-value gap to close (suggestion SG-E, option A: one page, one parser).

## 4. What is published

| Page | Contents |
|---|---|
| Overview | Five findings, the gap matrix, the decision-readiness table |
| Executive summary | The six-part written summary |
| Open questions | 20 questions: what we have, the source, what is missing, the number that would clear it, the suggestion that would produce it, the status |
| Have / don't have | 16 data domains, each with what is confirmed, what is missing, and what it blocks |
| Availability evidence | The designation-to-inactive join row by row, the inactive-coverage table, all 24 official inactive lists, the reserve list, the trades, the capture delta, the results feed |
| Suggestions board | 15 suggestions, each with options A/B/C, effort, risk, trade-off, dependency, a recommendation and a **blank verdict** |
| Repo review | Namespace inventory pinned to a commit, duplication analysis, four irregularities, and a statement of what was *not* reviewed |
| Sources | Every page read, how much of it was read, and the pages the brief asks for that were not located |
| Flagged for review | 14 items, each with its source link |

## 5. The decision queue, in order

1. **SG-A** — authorise a scheduled, hashed official capture (Wed / Thu / Fri / kickoff).
2. **SG-E** — ingest the official reserve list (one page, one parser, immediate payoff).
3. **SG-B** — decide the price-data policy before any backtest is published.
4. **SG-C** — resolve the depth-order source, or keep the deficiency feature unbuilt.
5. **SG-H** — one canonical count, computed at build time, never typed into prose.

The verdict column on the suggestions board is deliberately blank. Choosing between paths is the
reviewer's decision, not the model's.

## 6. Method and limits

* Pages were fetched and read; rows were transcribed only where a table was read end to end. That
  is why the designation-to-inactive join covers eight clubs and not twenty-eight — the other
  twenty were read but not transcribed, and are not claimed.
* The Steelers–Bengals result is **blank**: both `/schedules` and `/scores` rendered it as live in
  the first quarter when read on a Monday. The score is not inferred.
* Repository-wide counts are **pinned** to `data/repo_inventory.json` and refreshed only on
  request (`REFRESH_INVENTORY=1`), so that a sibling session merging a namespace cannot silently
  change a number this workspace states.
* This session did not read all 415 HTML files in the `nfl-*` namespaces line by line, and does
  not claim to have. Review depth is stated rather than implied.

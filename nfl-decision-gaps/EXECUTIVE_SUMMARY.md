# Executive summary — nfl-decision-gaps

**Session:** `arena/e2e6ca5a-own4` · **Date:** 2026-11-17 · **Live site:** <https://sassnarep3-star.github.io/Own4/nfl-decision-gaps/>

This workspace answers one question the rest of the repository does not ask clearly enough:
**before a decision can reasonably be made, what do we have, what are we missing, and what would
it take to close the gap?** It is a decision-support layer over the whole repository. It contains
no bet, no price and no model output.

---

## 1. What this update did

Re-read the official Week 10 NFL schedule and scores pages on 2026-11-17, checked the Pittsburgh–
Cincinnati Game Center, and checked the Washington–New York Game Center to complete the venue
register. The prior 2026-11-16 LIVE observation is preserved as historical evidence rather than
reused as a result. The static site contains nine pages; every table row links to an official or
repository source, and unconfirmed values remain blank and flagged.

**Build verification:** 9 pages, 496 table rows, 1,055 links (887 external HTTPS), zero broken
internal links, zero unsourced table rows. The result-state/source consistency checks pass for all
14 Week 10 fixtures.

## 2. The five findings that should change what you do next

1. **The injury report cannot establish who is unavailable.** Joining the live Week 10 report to
   the official inactive lists for the eight clubs where every row was read shows that **26 of 46
   inactive players (56.5%) do not appear on the injury report at all** — 24 of 44 (54.5%)
   excluding emergency third quarterbacks.

2. **An Out designation does not guarantee inactive.** Of 17 Out players on the joined clubs, 14
   were inactive and two more — TreVeyon Henderson (NE) and Tyler Goodson (DAL) — were placed on
   the official reserve list. The injury report, inactive lists and reserve-list record collectively
   explain **16 of 17 (94.1%)**. Kerby Joseph (DET) remains unexplained and flagged.

3. **The injury capture is point-in-time.** The committed 2026-11-13 capture differs from the
   2026-11-16 live read: two Lions rows changed, two Ravens rows appeared, Doubtful designations
   appeared where there had been none, and the club records in the headers were replaced with
   post-game records.

4. **Availability evidence remains incomplete.** The verified nfl.com depth-chart path returned
   404, and no snap-count table or announced-starters list was found on the official pages read.
   The backup-deficiency feature therefore has no verified input.

5. **No official page read publishes a price.** No spread, total or moneyline appears on the Game
   Center, schedule, scores or club pages. Until the owner chooses a price-data policy, residuals,
   closing-line value and ROI are undefined and must stay blank.

## 3. Week 10 results refresh — 2026-11-17

- **PIT–CIN: Final, Pittsburgh 18–Cincinnati 38.** The current official [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10), [NFL scores page](https://www.nfl.com/scores/), and [PIT–CIN Game Center](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10) show the final. The earlier 2026-11-16 reads showed LIVE, Q1 08:56, PIT 0–CIN 3; that page-state observation is retained in F1 as historical evidence, with no explanation inferred.
- **LAC–BAL: left blank.** The current official schedule and scores reads still list the fixture as scheduled for Monday, Nov 16 at 8:15 PM ET; neither read shows a Final state or score. The result row remains blank and F15 stays open. No score is inferred.
- **Week 10 coverage:** 13 of 14 fixtures currently show Final with scores; the consistency gate requires both numeric scores for a Final row and blank scores for any non-final row. The verifier also requires every fixture's result/venue source IDs to resolve to official NFL URLs.
- **Venue and schedule context:** the Week 10 venue register is now complete at 14/14 from the official inactive article and game centres. The dated [May 8 NFL schedule-release announcement](https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-to-be-released-thursday--may-14) and the current [Week 10](https://www.nfl.com/schedules/2026/by-week/week-10) and [Week 11](https://www.nfl.com/schedules/2026/by-week/week-11) schedule pages are linked together in the results section.

## 4. The reserve-list capture exists; namespace integration remains open

The official [November 2026 reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11) publishes 25 dated Reserve/Injured moves. The `nfl-collector` namespace already commits a 25-row structured capture with its read window and row hash ([capture](https://github.com/sassnarep3-star/Own4/blob/main/nfl-collector/data/captures/2026-11-16/league_reserve_list_2026-11.json), [ledger](https://github.com/sassnarep3-star/Own4/blob/main/nfl-collector/data/captures/ledger.json)). `nfl-decision-gaps` still uses its static November transcription and does not consume that capture automatically. SG-E now proposes integrating the existing reserve-list and trades captures, then extending coverage to the remaining transaction categories without duplicating the collector parser.

## 5. What is published

| Page | Contents |
|---|---|
| Overview | Five findings, the gap matrix, the decision-readiness table |
| Executive summary | Findings, Week 10 result refresh, source and verification limits |
| Open questions | 20 questions: what we have, the source, what is missing, the clearing number, discovery path and status |
| Have / don't have | 16 data domains, each with what is confirmed, what is missing and what it blocks |
| Availability evidence | Designation-to-inactive join, inactive coverage, official inactive lists, reserve list and trades, capture delta, and Week 10 results |
| Suggestions board | 15 suggestions, each with options, effort, risk, trade-off, dependency, recommendation and a **blank verdict** |
| Repo review | Namespace inventory pinned to commit `8e2148d`, duplication analysis, four irregularities and an explicit review-scope statement |
| Sources | Official point-in-time reads and repository capture records, with the exact chunk coverage and date recorded |
| Flagged for review | 15 items: 12 open gaps and 3 resolved items retained for audit, each with source links |

## 6. The decision queue, in order

1. **SG-A** — authorise and maintain the scheduled, hashed official availability capture.
2. **SG-E** — connect this namespace to the existing reserve-list and trades captures; then expand transaction coverage.
3. **SG-B** — decide the price-data policy before any backtest is published.
4. **SG-C** — resolve the depth-order source, or keep the deficiency feature unbuilt.
5. **SG-H** — one canonical count, computed at build time, never typed into prose.

The verdict column on the suggestions board is deliberately blank. Choosing between paths is the
reviewer's decision, not the model's.

## 7. Method and limits

* Earlier availability and injury evidence remains tied to its recorded 2026-11-13/16 snapshots;
  this refresh does not convert those historical reads into a current report.
* The official Week 10 schedule and scores pages still report LAC–BAL as scheduled, without a
  final state or score. Both score cells remain blank. The fetch tool exposes the read date but not
  an exact clock time or response headers.
* No opening/closing market prices were found. No residual, CLV, ROI or price correlation is
  fabricated or published from missing values.
* Repository-wide namespace counts are pinned in `data/repo_inventory.json` to commit
  `8e2148d`; they are refreshed only on request (`REFRESH_INVENTORY=1`).
* This update did not read all 468 HTML files in the `nfl-*` namespaces line by line and does not
  claim to have. Review depth is stated rather than implied.

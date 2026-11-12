# NFL — Executive summary

**Session** `arena/e2601583-own4` · **Captured** 2026-11-12 (UTC) · **Live site** `/Own4/nfl-audit/`
**Scope** NFL only. Line-by-line verification of the repository's NFL work against official sources,
a decision-readiness register, a suggestions board, an injury tracker, and an honest line-origination
position. Research and review only — not wagering advice.

---

## 1. What this session did

| # | Task | Result |
|---|------|--------|
| 1 | Re-read the official NFL record for today | Week 10 slate (14 games), Week 9 finals (15 games), league standings (32 teams), the complete Week 10 injury report (276 player rows across 26 teams), transactions (12 November trades) |
| 2 | Audit the repository's stored NFL data against that record | **13 checks, 13 pass, 0 fail** — including a 160-field reconciliation of the stored Week 8 snapshot forward to today |
| 3 | Track injuries and depth deficiencies | 276 injury rows published with official player links; depth-chart string deliberately blank because the official route returns 404 |
| 4 | Answer "what must be decided, and what do we not know?" | **14 questions**, 9 of them blocking, each with what we have, what is missing and how to discover it |
| 5 | Create a suggestions section to review before implementing | **15 suggestions** with effort, risk, prerequisites and a recommendation, plus three coherent packages and a decision sheet |
| 6 | Publish it | 13-page static dashboard under `nfl-audit/`, every table row source-linked, verifier green |

## 2. The eight findings that matter

1. **The official record is internally consistent.** 32 teams, W = L = 135, PF = PA, net points = 0,
   and every winning percentage recomputes from W-L-T (half-up rounding). Source: nfl.com/standings.
2. **The repository's stored NFL data is stale, not wrong.** nfl-lab's Week 8 standings, plus the 15
   official Week 9 finals, plus the Week 8 Monday game, reproduce today's standings on **32 of 32 teams**
   for W, L, T, PF and PA. 160 comparisons, 0 mismatches.
3. **Two engines publish two different "own lines" for the same games.** JAX@BAL is 3.8 points in
   nfl-quant and HOME +0.5 in nfl-lab. Both are internally consistent; they cannot both be canonical.
4. **There is no official price.** No spread, total, moneyline or prop price appears on any official
   page read. Every price, edge and ROI in the repository is blank or third-party, and nfl-quant's own
   provenance file says so.
5. **Depth-chart string is unobtainable officially.** nfl.com returns 404 on the depth-chart route.
   Rosters publish position and experience, never a depth order. Backups by string are therefore blank,
   and the site publishes the verifiable half instead: who is not practising, by team and position group.
6. **Injury data is rich in one column and empty in two.** 276 rows all carry practice status; only 6
   name an injury and only 6 carry a game status. Those blanks are the official page's blanks.
7. **Nothing passes a reward gate, and that is correct.** Both NFL engines award zero points. One of
   them nevertheless gives a "Bronze" tier to strategies whose own bootstrap interval straddles zero —
   a reward for luck even at zero points (flag F18).
8. **The site itself is the delivery risk.** The repository's Pages build has reported "errored" since
   2026-11-06. A dashboard nobody can load cannot support a decision.

## 3. What is blocked, and by what

| Blocked capability | Blocking question | What unblocks it |
|---|---|---|
| Any ROI, edge or reward eligibility | Q01 official price · Q02 licence terms | A licensed, timestamped odds source |
| Any honest backtest | Q11 what "before kickoff" means | Capture-time + hash on every input |
| Depth-deficiency model (2nd/3rd/4th string) | Q03 official depth source | A licensed depth-chart feed |
| Injury-adjusted projections | Q04 blank semantics · Q05 practice day | The league's report documentation, or a daily timestamped archive |
| Parlays and prop combos | Q09 same-game dependence panel | A licensed player-game panel |
| Paying any reward | Q08 what is being rewarded | A written reward definition + legal review |

## 4. Recommendation

Take **Package A — "Truth first"** (suggestions S01, S02, S03, S04, S14, S15): one canonical NFL
dashboard, every number stamped and sourced, every open question visible, deployment gated in CI.
It is achievable now with official data and it is the precondition for everything else. Follow with
**Package B — "Evidence next"** (pre-registered strategies, luck-controlled scoring, trade-aware injury
exposure, a transparent baseline line), and only then **Package C — "Product last"**, which needs a
paid data licence and legal review before a single reward is defined.

The full option set with trade-offs is on the **Suggestions** page; the open questions are on the
**Questions register**; every irregularity and blank is on **Flagged for review**.

## 5. Sources (all read on 2026-11-12)

- Injury report: https://www.nfl.com/injuries/
- Standings: https://www.nfl.com/standings/league/2026/REG
- Week 9 schedule/results: https://www.nfl.com/schedules/2026/by-week/week-9
- Week 10 schedule: https://www.nfl.com/schedules/2026/by-week/week-10
- Week 8 schedule: https://www.nfl.com/schedules/2026/by-week/week-8
- Transactions: https://www.nfl.com/transactions/
- Player logs: https://www.nfl.com/players/patrick-mahomes/stats/
- Player season stats: https://www.nfl.com/stats/player-stats/
- Team stats: https://www.nfl.com/stats/team-stats/
- Roster: https://www.nfl.com/teams/kansas-city-chiefs/roster/
- Depth-chart probe (404): https://www.nfl.com/teams/kansas-city-chiefs/depth-chart/
- Darnold ruled out: https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again
- Football Operations: https://operations.nfl.com/
- Next Gen Stats: https://nextgenstats.nfl.com/
- Responsible gambling: https://www.ncpgambling.org/help-treatment

## 6. Verification statement

Every table row on the site carries an https source link; `nfl-audit/scripts/verify.py` fails the build
if one does not. No value was inferred, interpolated or filled from memory. Where an official page is
silent, the cell is blank and the item is on the Flagged-for-Review page (18 items). Unverified or
irregular items do not block publication and are listed for your review.

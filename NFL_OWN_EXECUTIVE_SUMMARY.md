# NFL Own Lines — executive summary (snapshot 2026-11-13 UTC)

**Live page:** https://sassnarep3-star.github.io/Own4/nfl-own/
**Workspace:** `nfl-own/` · **Session:** `1880ad1e-own4` · **Branch:** `arena/1880ad1e-own4`
**Reproduce:** `python3 nfl-own/data/official/transcribe_2026-11-13.py && python3 nfl-own/engine/analysis.py && python3 nfl-own/engine/build_site.py && python3 nfl-own/engine/verify_site.py`
(Python 3 standard library only. No network access is needed to rebuild; the official transcription is checked in.)

---

## 1. The headline, stated without softening

**0 of 19 registered strategies qualify. 0 reward points have been awarded.** The rule is the
   repository's existing one: 1,000 points per strategy, paid only on a twelve-of-twelve finish,
   with no partial credit — 19,000 points were on the table and none was earned.

- The best holdout hit rate is **56.1%** (S8, 212 decisions) against a **52.38%** break-even — and it
  **fails the split-half retest**, which is the test that separates a rule from a lucky window.
- Our own-line model is **worse than the closing line it would have to beat**:

| Metric (2,519 holdout games, 2017–2026) | Our line | Closing line | Naive home-field only |
|---|---|---|---|
| Spread mean absolute error | **10.752** | **9.850** | 11.101 |
| Total mean absolute error | **11.113** | **10.477** | — |

Nothing here is a price, a pick or an edge. No market price exists anywhere in this repository,
because the NFL publishes none and no licensed 2026 line archive is in scope.

## 2. What was done this session

1. **Re-read the official snapshot on 2026-11-13 instead of inheriting it.** The repo's stored
   snapshot was dated 2026-11-12. One game has since finished (WAS 24, NYG 21 on 2026-11-12), so the
   league has now played **137** games, not 136, and Washington is **3-5-1** while the Giants are
   **5-3-1**.
2. **Captured data that three earlier sessions wrongly recorded as blocked.** The NFL publishes a
   **full per-game log for every player** at `nfl.com/players/<slug>/stats/logs/`, and the logs
   reconcile exactly to the published season totals. Player props are therefore gradeable — for the
   seven players read here.
3. **Registered and graded 19 strategies** (11 singles, 3 parlay constructions, 3 single-prop rules,
   2 prop combos) against **12 pre-registered gates**, with `p`, BH-FDR `q`, week-clustered
   bootstrap intervals, a matched-random placebo, a season-stability test and a split-half retest.
4. **Originated Week 11 lines** for all 13 games: own spread, own total, fair moneyline, and every
   model input printed for audit.
5. **Measured correlations** at team level (near zero) and player level (wide intervals, sample sizes
   printed next to every value).
6. **Built the site the request asked for:** a clean dashboard with category subpages, all entries in
   readable tables, a **dedicated Suggestions page**, a **Questions register** of 15 items each split
   into known / unknown / answer / what-would-unlock-it, a **Decisions** page, and a **Flagged for
   Review** page. 22 pages, **672 data rows, 672 of them carrying a source link**, 538 local links,
   0 broken, 218 blank (unverified) cells published as blanks.
7. **Reviewed the repo line by line** and found a live regression (below).

## 3. Verified official data (all read 2026-11-13)

| Dataset | Volume | Integrity result |
|---|---|---|
| Standings | 32 clubs | W = L = 136, PF = PA = 6,291, pct reproduces on 32/32 rows |
| Team stats (offence passing/rushing, defence passing/rushing) | 32 clubs × 4 tables | 6 league identities exact: pass yds, pass TD, rush yds, rush TD, attempts, completions |
| Week 11 slate | 13 games, 6 byes | 26 distinct clubs, no overlap with byes |
| Week 9 finals | 15 games | every game on the official scores page |
| Week 10 | 1 final + 13 unplayed | 13 rows deliberately omitted, not scored blank |
| Injury report | 14 games | practice + game status; **no depth rank exists in it** |
| Player leaders | 25 passing, 25 receiving, 25 rushing | columns published only where proven |
| Player game logs | 7 players, 60 game rows | logs sum **exactly** to published season totals |

**41 integrity checks: 40 pass, 2 recorded notes, 0 fail.** The build refuses to publish if any fail.

## 4. What is blocked, and it is not the method

| Requirement | Status | Why |
|---|---|---|
| Player props and combos | **unblocked** | official per-game logs exist and reconcile |
| 2nd/3rd/4th-string replacement | **blocked** | the league publishes **no depth chart**; the club depth-chart URL returns 404 and the roster page carries no depth rank |
| Any 2026 market price or edge | **blocked** | no official or licensed 2026 price archive |
| Injury effect on results, quantified | **open** | the historical archive has no injury field |
| Licensed historical odds | **third-party** | the archive used here is nflverse, licence not reviewed |

## 5. Irregularities flagged for review (13 items, none blocking)

- **F-01 — a peer claim is wrong.** Three NFL workspaces in this repo state that player props are
  blocked for lack of per-game data. They are not. Corrected here with proof.
- **F-02 — a stale official page.** The Week 10 injury report still shows pre-game records after the
  Thursday game finished. Any snapshot taken from it is one game stale.
- **F-03 — an official source quirk.** The published passing AVG column does not reproduce
  yards ÷ attempts on 4 of 32 rows, in **both** directions (JAX 8.6 vs 8.546, KC 7.8 vs 7.745,
  PIT 6.4 vs 6.452, SEA 7.2 vs 7.253). The site computes its own average and never uses the
  published column.
- **F-11 / R-01 — a live regression in the peer root dashboard.** Running
  `python3 verification/build.py` on the current head silently **deletes the `nfl-lines` navigation
  block** from `index.html` and all 13 `verified/*.html` pages. Reproduced; the output was reverted
  and the request logged in `COORDINATION.md` rather than editing a file another session owns.
- Plus: no depth chart (F-04), third-party archive licence (F-05), no 2026 prices (F-06), a 0.85
  home-field haircut that is a stated judgement call (F-07), small player-level samples (F-08),
  blank A.J. Brown season totals (F-09), 11 omitted team-stat columns (F-10), −110 price
  assumption (F-12), and no prospective replication yet (F-13).

## 6. Decision support (the part that was asked for)

- **Questions register — 15 questions**, each with *what we know*, *what we do not know*, *the
  answer* and *what would unlock it*. 4 answered, 6 partial, 2 open, 3 blocked.
- **Decisions — 7 real forks** (D1–D7), each naming the exact questions blocking it. Three carry a
  recommendation: do not pay rewards on backtests, do not publish picks, do scale player props.
- **Suggestions — 16 proposals** with impact, effort, risk, prerequisites and status
  (4 implemented this session, 6 proposed, 4 need a decision from you, 2 already implemented in
  earlier sessions). The page exists so a path can be chosen **before** anything is built.
- The one-line version: **S-04 decides the rest.** Either fund the two licences (depth chart + odds),
  or run this as a decision-support and data-coverage tool.

## 7. How luck was handled

- Walk-forward refits before every season; no forecast can see its own game (perturbation test).
- Dev window (forecast seasons 2002–2010) used **only** for the model's two parameters; the grid is
  published. The holdout (2017–2026) was not consulted for that choice.
- 19 simultaneous tests → BH-FDR control, because with 19 looks the chance of at least one p < 0.05
  by luck is about 62%.
- Power arithmetic: a genuine 55% edge needs roughly **2,300** graded decisions to be detected at
  80% power. Most rules here grade in the hundreds.
- **Split-half retest:** zero strategies clear break-even in both halves. Two of the
  strongest-looking entries (S1, S2) fall below break-even in the second half.
- The only cure for hindsight is **prospective replication (G12)**, which no entry has attempted yet.

## 8. What to do next

1. **Do not publish picks or prices.** The evidence does not support it and the market data does not
   exist.
2. **Keep the leaderboard as a rejection machine.** It rejected everything, which is the correct
   output for public data against efficient prices.
3. **Choose the product (S-04).** Either buy the two licences, or make this the best-sourced NFL
   coverage and decision tool available — which it can be today, for free.

---

Analytical research only — **not wagering advice**. National Problem Gambling Helpline
**1-800-MY-RESET** (1-800-697-3738) · https://www.ncpgambling.org/help-treatment/

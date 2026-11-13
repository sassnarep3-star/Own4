# NFL Origination — Executive Summary

**Session** `arena/22679198-own4` · **Snapshot** 2026-11-13 · **Live** https://sassnarep3-star.github.io/Own4/nfl-origination/

Analytical research only. **Not wagering advice.** NCPG Helpline 1-800-MY-RESET (1-800-697-3738).

---

## The bottom line in one paragraph

The data is sound and the scoreboard is empty. All **160** recomputed 2026 record cells match
nfl.com exactly, all **10** integrity checks pass, and the Week 10 slate, its one completed result
and **95** injury designations were transcribed from official pages on 2026-11-13. But our own
rating model — which does beat a naive baseline (margin MAE **10.913** vs 11.067) — **loses to the
closing line** (**9.848**) over 2,126 out-of-sample games. **0 of 7** registered strategies qualify,
both pre-registered placebos fail as they must, and **0 of 1,000 reward points are awarded**. No
price, stake, edge or return is claimed anywhere, because the NFL publishes no odds at all.

---

## What was verified against official sources

| Claim | Result | Source |
|---|---|---|
| 2026 league standings | 32 clubs, all columns transcribed | [nfl.com/standings](https://www.nfl.com/standings/league/2026/REG) |
| All 32 clubs' W-L-T-PF-PA recompute | **160 / 160 cells match** | [nfl.com/standings](https://www.nfl.com/standings/league/2026/REG) |
| 2026 game log | 136 completed games, 272 scheduled rows | [nflverse/nfldata](https://github.com/nflverse/nfldata) (third-party) |
| Week 10 slate | 14 games, kick-off times, networks, 4 byes | [nfl.com schedule](https://www.nfl.com/schedules/2026/by-week/week-10) |
| Week 10 result so far | WAS 24 – NYG 21 (Thursday) | [game centre](https://www.nfl.com/games/commanders-at-giants-2026-reg-10) |
| Week 10 injury designations | 95 rows across 19 clubs | [injury report](https://www.nfl.com/news/nfl-week-10-injury-report-2026-season) |
| Confirmed lineup changes | 8, each named in official reporting | [roundup 13 Nov](https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13) |
| Franchise relocations (OAK/SD/STL) | 3 mappings, each sourced to an official article | [Raiders](https://www.nfl.com/news/raiders-officially-announce-las-vegas-raiders-title-0ap3000001098555) · [Chargers](https://www.nfl.com/news/chargers-announce-decision-to-relocate-to-los-angeles-0ap3000000773179) |

---

## Three things the brief asks for that cannot be sourced

1. **1st / 2nd / 3rd / 4th-string depth labels.** The league publishes no depth chart —
   `nfl.com/depth-charts/` returns a 404, re-checked on 2026-11-13 — and no snap-count feed exists
   here. Labelling a player "3rd string" would be invention. Only the **8** lineup changes an
   official article explicitly names are published; everything else is marked **BLOCKED**.
2. **A real betting edge.** With no official price, Gate G7 can never pass. Every return figure
   rests on an assumed **−110** and is labelled as such.
3. **Historical injury backtests.** `nfl.com/injuries/` serves the current week only, and no
   snapshot predates this session. No injury effect is measurable, so none is claimed.

---

## The one real signal

A quarterback's passing-yardage over and his WR1's receiving-yardage over, in the same team-game,
co-occur **1.45×** more often than independence predicts: phi = **0.346**, n = 803, 95% CI
**0.284–0.406**. That is genuine dependence, and it means an independent-parlay price would
*underprice* the combo — if the book did not reprice it. It does. No archived same-game-parlay price
exists here, so the dependence is a **measured fact, not a claimed edge**.

Cross-game parlay legs really are independent: the first half of a week's home-cover rate has
r = −0.007 against the second half (473 week-slates), and spread vs total within a game has
r = −0.010 (7,103 games). Those may be multiplied safely.

---

## Own lines for the 13 unplayed Week 10 games

Fitted only on games played before the slate; HFA **2.06** points from prior seasons only.

| Game | Our spread (home) | Our total | Home win prob | Injury band (home) |
|---|---|---|---|---|
| NE@DET | −6.8 | 45.6 | 31% | −6.4 … −5.4 |
| KC@ATL | −1.4 | 45.3 | 46% | −1.0 … +0.1 |
| HOU@CLE | −1.3 | 42.5 | 46% | −0.4 … +2.5 |
| MIN@GB | +5.1 | 45.7 | 65% | +5.1 … +5.1 |
| MIA@IND | +5.4 | 44.9 | 66% | +3.9 … −0.4 |
| CAR@NO | +5.3 | 45.5 | 65% | +4.9 … +3.7 |
| BUF@NYJ | −1.5 | 42.6 | 46% | −1.2 … −0.2 |
| JAX@TEN | +2.3 | 43.2 | 57% | +1.8 … +0.3 |
| LA@AZ | −3.9 | 45.4 | 39% | −3.9 … −3.9 |
| SEA@LV | −4.4 | 45.2 | 37% | −4.5 … −4.6 |
| SF@DAL | +3.5 | 45.0 | 60% | +2.0 … −2.3 |
| PIT@CIN | −2.6 | 43.1 | 42% | −3.2 … −4.9 |
| LAC@BAL | +5.5 | 43.5 | 66% | +5.5 … +5.5 |

The injury adjustment is published as a **band, never as a point estimate**, because the official
report gives a game status and not a snap count. The published line is the no-adjustment line.

---

## What to decide next

The [Suggestions & decisions](https://sassnarep3-star.github.io/Own4/nfl-origination/pages/suggestions.html)
page holds **22** items with options, evidence, cost, risk and a recommendation, plus an ordered
path. Four are binding:

- **S07 — adopt a written skill definition before any reward is paid.** The one proposed here
  rejects our own best result, which is the point.
- **S02 — obtain a legal position** before publishing anything as more than research points.
- **S01 — buy or license an archived odds history.** This gates everything else in the betting half.
- **S10 — choose one canonical NFL dashboard.** Twelve now compete.

---

## Method and honesty controls

- Model knobs frozen in `data/model_params.json` with a timestamp written *before* the holdout was
  read; the 2018–2025 holdout was scored exactly once.
- Walk-forward: refitted before every kick-off on strictly earlier games; the home-field term uses
  prior seasons only.
- Week-clustered bootstrap CI on every ROI, a 2,000-draw matched-permutation null,
  Benjamini–Hochberg FDR across every test *including placebos*, and season-concentration
  disclosure for every profitable strategy.
- **Two pre-registered placebos that must fail. They do.** During this session one placebo
  *passed* — which exposed a sign-convention bug in the third-party line column. The bug was fixed,
  it is published as flag **F-08**, and it is the reason Gate G6 exists.

---

## Irregularities found (published, non-blocking)

**20** items on the Flagged for Review page. The three that matter most:

- **F-01** — no official price source exists, so Gate G7 is permanently blocked.
- **F-02** — no official depth chart exists, so the brief's string-deficiency requirement is
  blocked at the data layer.
- **F-08** — a sign-convention error *this project made and corrected*, kept in the register rather
  than deleted.

---

## Reproduce

```bash
python3 nfl-origination/run_all.py     # 13 steps, exits non-zero on the first failure
```

It regenerates every number and then runs `verify.py`, which fails on a broken local link, a data
row without a source, a missing disclaimer, or any published claim that contradicts the computed
evidence.

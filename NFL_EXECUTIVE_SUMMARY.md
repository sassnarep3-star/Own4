# NFL Edge — executive summary (2026-11-12)

**Live page:** https://sassnarep3-star.github.io/Own4/nfl-edge/
**Workspace:** `nfl-edge/` (source of truth for every number below)
**Branch:** `arena/1d2cb84b-own4` · **Session:** `1d2cb84b-own4`

## What this is

A decision dashboard for originating NFL lines from official league data. It answers three questions in
order: **what is true** (sourced official data), **what we built from it** (own lines and registered
strategies), and **what survived validation** (almost nothing). It also carries the thing that was actually
asked for alongside the analysis: a decision register of questions and missing information, and a
suggestions section to choose a path before anything is implemented.

## The headline, stated without softening

**0 of 4 registered strategies qualify. 0 of 1,000 reward points are awarded.** Our own line model is
less accurate than the closing line it would have to beat: spread mean absolute error **10.502** points
versus **9.871** for the market (naive baseline 11.231). On totals: **10.830** versus **10.470**
(naive 11.042). Under the pre-registered gates, nothing here is a price, a pick, or an edge.

That is the expected result for public-data rules measured against efficient closing lines. It is
published unchanged rather than tuned until it looks better.

## What was built

| Piece | Numbers | Source |
|---|---|---|
| Official standings, 32 clubs | PF−PA reproduces published net points on 32/32 rows; league PF = league PA = 6,246; W = L = 135 with 2 ties | nfl.com/standings |
| Official team statistics | 32 clubs × offence + defence, scoring/passing/rushing; six league-wide identities all exact (pass yd 63,556; pass TD 411; rush yd 30,580; rush TD 257) | nfl.com/stats/team-stats |
| Game archive, weeks 1–9 | **136 games**; the peer archive held only 120 and was missing all of Week 9 plus the Week 8 Monday game. The 16 missing games were read from official week pages; the completed archive reproduces every club's W-L-T, PF and PA with **0 mismatches** | nfl.com/schedules |
| Week 10 slate | 14 games (4 clubs on bye), dates, kickoff times, networks, official game URLs | nfl.com/schedules/2026/by-week/week-10 |
| Week 10 injuries | 275 players, 28 clubs, practice status + game status; no starter/backup label exists in the source | nfl.com/injuries |
| Own lines | Spread, total, projected points, fair moneyline for all 14 Week 10 games, from official team stats only | `nfl-edge/data/own_lines_2026.json` |
| Validation | 10 pre-registered gates, frozen before the backtest; walk-forward 1999–2025 with a 2017–2025 holdout of 2,383 games | `nfl-edge/data/results.json` |
| Luck bounds | Week-clustered bootstrap, matched-random placebo (p 0.37–0.63), season stability, residual persistence +0.40 | `nfl-edge/data/correlations.json` |
| Integrity | **15/15** mechanical checks pass; the site build refuses to publish if any fails | `nfl-edge/scripts/build_stats.py` |
| Site | 22 pages, 889 table rows, every row with a source link, 628 local links and 1,093 external links verified | `nfl-edge/scripts/verify_site.py` |

## Strategy results (holdout 2017–2025, frozen config)

| ID | Rule | Bets | ROI | Bootstrap 95% CI | Placebo p | Gates | Tier |
|---|---|---|---|---|---|---|---|
| S1 | Spread divergence ≥ 2.0 pts | 1,540 | −3.12% | [−7.84%, +1.54%] | 0.41 | 3/10 | Rejected |
| S2 | Total divergence ≥ 2.0 pts | 1,187 | −5.32% | [−10.36%, +0.02%] | 0.37 | 3/10 | Rejected |
| S3 | Fair-moneyline value ≥ 3 pts | 2,060 | −8.45% | [−14.91%, −1.70%] | 0.63 | 3/10 | Rejected |
| S4 | Cross-game 2-leg parlay from S1/S2 legs | 155 | −15.74% | not tested (n < 300) | not tested | 2/10 | Rejected |

Closing lines are a **third-party** archive. No official NFL source publishes betting lines, and no 2026
price exists in this repository — so every 2026 market, divergence and edge cell is blank, not zero.

## Correlation (what was measured, and what could not be)

- Favourite covers vs game goes over: **phi = −0.0079** (joint 20.14% vs 20.34% if independent).
- Home win vs game goes over: **phi = +0.0110** (joint 26.35% vs 26.08% if independent).
- Both are within 0.011 of zero on 2,383 holdout games, so multiplicative parlay pricing is defensible
  for **these two team-level pairs**.
- Residual persistence across consecutive seasons: **+0.40** — the model is consistently wrong in the
  same direction a third of the time. That is a bias to fix, not an edge to sell.
- **Player-level correlations are blank.** No official per-game player logs and no prop prices exist in
  scope. A peer workspace reported a 1.45× QB/WR lift, but against a rolling-mean *proxy* line, not a
  sportsbook; importing it would import an unverified edge claim.

## The three blocked requirements, stated plainly

1. **Player props and prop combos** — no official per-game player outcomes, no prop prices. Nothing graded.
2. **Second/third/fourth-string replacement** — the league publishes **no depth chart** (the team
   depth-chart URL returns 404) and **no snap counts**. The injury report gives practice and game status
   only. This site shows unavailability by club and position and never asserts who is a backup.
3. **Any 2026 price or edge** — no official or licensed 2026 price archive. Market columns are blank.

## Decision support (the part that was asked for)

- **Decision register:** 22 questions, each split into *what we know*, *what we do not know*, *the answer*,
  and *what would unlock it*. Status: answered / partial / open / blocked. Seven decisions (D1–D7) each
  name the exact questions blocking them.
- **Suggestions:** 16 proposals with impact, effort, risk, prerequisites and current status
  (implemented / proposed / needs decision), so a path can be chosen before anything is built.
- **Flagged for review:** 16 items, all non-blocking for publication, each naming what would clear it.

## What to do next (three real choices)

1. **Do not publish picks or prices.** The evidence does not support it and the market data does not exist.
2. **Keep the leaderboard as a rejection machine.** It rejected everything, which is the correct output for
   public data against efficient prices. Its value is in stopping a lucky backtest from becoming a paid strategy.
3. **Buy data or change the question.** Two of the blocked requirements are blocked by licensing, not by
   method. Either licence per-game player data plus a depth chart and price archive, or redefine the product
   as a decision-support and data-coverage tool (suggestion S-03 is the decision, S-08 the data purchase).

## Reproduce

```bash
python3 nfl-edge/scripts/make_games.py      # game archive + 16 restored games
python3 nfl-edge/scripts/make_injuries.py   # Week 10 injury report
python3 nfl-edge/scripts/build_stats.py     # 15 integrity checks (exits non-zero on failure)
python3 nfl-edge/scripts/model.py           # own lines, walk-forward backtest, gates, correlations
python3 nfl-edge/scripts/build_site.py      # 22 pages
python3 nfl-edge/scripts/verify_site.py     # link + source-link + drift checks
```

Python 3 standard library only. No network access is needed to rebuild; the captured data is checked in.

---

Analytical research only — **not wagering advice**. National Problem Gambling Helpline 1-800-MY-RESET
(1-800-697-3738) · https://www.ncpgambling.org/help-treatment/

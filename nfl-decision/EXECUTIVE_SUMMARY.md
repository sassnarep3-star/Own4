# NFL Decision Lab — Executive Summary

Session `arena/e2b19bf6-own4` · 2026-11-12 · live at https://sassnarep3-star.github.io/Own4/nfl-decision/

## The bottom line in one paragraph

The pipeline is reproducible and its provenance is exact: all **136** played 2026 games reconcile,
and all **32** teams' W-L-T / PF / PA (**160 of 160 cells**) recompute to match nfl.com. But there is
**no tradeable edge in it**. Of five registered betting strategies scored once on the 2018–2025 holdout,
four lost money and the one that made money (+1.09% at an assumed −110) cannot be separated from luck:
its 95% week-clustered bootstrap CI is [−4.65%, +7.03%], its FDR-adjusted q is 0.199, and 98% of its
profit came from a single season. **0 of 1000 betting reward points are awarded and the pool rolls over.**
Because forecast skill *can* be measured without a price, **600 forecast reward points are awarded**:
the own Elo model (margin MAE 10.440) beats every naive baseline but still loses to the closing line (9.844).

## What was verified against official sources

| Claim | Result | Source |
|---|---|---|
| 2026 Weeks 1–9 final scores | 136 games | [nfl.com scores](https://www.nfl.com/scores/2026/REG9) |
| All 32 team records recompute | **160/160 cells match** | [nfl.com standings](https://www.nfl.com/standings/league/2026/REG) |
| One missing game found in the repo's own log | CHI 34 – SEA 17, Week 8 | [game page](https://www.nfl.com/games/bears-at-seahawks-2026-reg-8) |
| Week 10 schedule | 14 games, times, venues | [nfl.com schedule](https://www.nfl.com/schedules/2026/by-week/week-10) |
| Week 10 injury report | 28 clubs, 276 player rows | [nfl.com injuries](https://www.nfl.com/injuries/) |
| Depth-chart deficiencies confirmed by official reporting | 13 rows | [roundup](https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11) |
| Official depth charts | **do not exist** (HTTP 404) | [nfl.com/depth-charts](https://www.nfl.com/depth-charts/) |
| Official betting odds | **no such source exists** | [nfl.com games](https://www.nfl.com/games) |

## Three things you asked for that cannot be sourced

1. **1st/2nd/3rd/4th-string depth labels.** `nfl.com/depth-charts/` returns 404. Labelling a player
   "3rd string" would be invention. The site publishes only the 13 replacements an official NFL.com
   article explicitly names, and marks everything else BLOCKED.
2. **A real betting edge.** No official NFL odds source exists, so every ROI here rests on an assumed
   −110. Gate G7 fails for all five strategies by construction, so Gold is unreachable and no reward can
   honestly be tied to betting performance.
3. **Historical injury backtests.** `nfl.com/injuries/` serves the current week only. No official archive
   exists, so injury effects are not measurable and none are claimed.

## The one real signal

QB passing yards over + WR1 receiving yards over, same team-game: P(both) = **0.2740** against
**0.1892** if the legs were independent — a **1.45× lift**, phi = **0.346** with a 95% CI of
[0.284, 0.406] over 803 team-games (2021–2022). That is a genuine dependence in the data. It is *not*
claimed as an edge, because sportsbooks explicitly reprice correlated same-game legs and no archived
SGP price exists to check against. Buying that price history is the single most promising spend in the
project (suggestion S10).

Cross-game parlay legs, by contrast, are genuinely independent (phi = −0.0057, bootstrap CI spans 0;
same-week cover counts show no overdispersion), so those may be multiplied safely.

## What to decide next

The **Suggestions** page holds 18 items, each with context, options, evidence, cost, risk and a
recommendation. Four of them are the binding ones:

- **S14** — buy or license an archived odds history. This is the constraint on everything else.
- **S02** — publish only article-verified depth replacements, or buy a depth-chart feed.
- **S06** — keep two leaderboards: forecast skill (pays now) and betting ROI (held until G7 passes).
- **S04** — adopt one canonical NFL dashboard; five currently compete.

## Method and honesty controls

Knobs frozen on 1999–2012 before the holdout was touched; holdout scored exactly once; week-clustered
bootstrap; matched-random permutation; Benjamini–Hochberg FDR; twelve placebo strategies; season
concentration published next to every ROI; and a look-ahead perturbation test that changed
**0 of 1616** downstream predictions.

## Irregularities found (published, non-blocking)

See `pages/flagged.html` for all 15. The two that matter: a **missing Week 8 game** in the peer 2026
dataset, and an **inverted spread-sign convention** in the archived line column that produces
impossible ROIs above +50% if read naively (documented and corrected here, peer file untouched).

*Analytical research only — not wagering advice. NCPG Helpline 1-800-MY-RESET (1-800-697-3738).*

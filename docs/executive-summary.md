# Executive Summary — Own4 NBA Lines Lab

**Date:** 2026-11-02 · **Branch:** `arena/42d467e4-own4` · **Live site:** https://sassnarep3-star.github.io/Own4/

## 1. Goal

Originate our own NBA betting lines and run a **leaderboard competition** in which strategies earn rewards only for demonstrated skill. The competition covers **single bets, parlays, and player-prop combos** (plus same-game parlays, live and futures). Every strategy must pass **validation gates G1–G8**; correlation between bet legs is measured, not assumed; luck is removed by design (walk-forward testing, held-out samples, significance testing, risk caps, closing-line-value checks). No manual input is required to run the pipeline once official data is ingested.

## 2. Verified baseline (official sources only, accessed 2026-11-02)

- **League:** NBA — 30 teams, 2 conferences × 3 divisions ([nba.com/news/about](https://www.nba.com/news/about)).
- **Season:** 82 games per team; 1,230 total regular-season games (derived: 30×82÷2 — flagged as derived). 2026-27 season tipped off **Oct 20, 2026** ([rosters article](https://www.nba.com/news/nba-rosters-set-for-2026-27-regular-season), [opener](https://www.nba.com/news/nba-schedule-season-opener-2026-27)); ends **Apr 11, 2027**; SoFi Play-In **Apr 13–16, 2027**; playoffs begin **Apr 17** ([key dates](https://www.nba.com/news/key-dates)).
- **Game format:** 4 × 12-minute quarters (48 min), 5-minute OT, 15-minute halftime, 24-second shot clock ([Official 2025-26 Playing Rules PDF](https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf)); court 94×50 ft, rim 10 ft, FT line 15 ft, 3-pt arc 23'9" / 22' corners ([About](https://www.nba.com/news/about), [Rule No. 1](https://official.nba.com/rule-no-1-court-dimensions-equipment/)).
- **Playoffs:** seeds 1–6 per conference automatic; 7–10 in Play-In; best-of-seven 2-2-1-1-1 rounds ([About](https://www.nba.com/news/about), [FAQ](https://www.nba.com/news/faq), [Play-In](https://www.nba.com/news/nba-play-in-tournament)).
- **In-season tournament:** Emirates NBA Cup 2026 — Group Play Oct 30–Nov 27 (60 games), Championship Dec 11 at Hinkle Fieldhouse, Indianapolis; all Cup games count toward standings except the Championship ([Cup 101](https://www.nba.com/news/nba-cup-101), [Cup FAQ](https://www.nba.com/news/nba-cup-frequently-asked-questions)).
- **Official data for signals:** [stats.nba.com](https://stats.nba.com/) (+ [glossary](https://stats.nba.com/help/glossary/), [minimums](https://stats.nba.com/help/statminimums)), [standings](https://www.nba.com/standings), [games](https://www.nba.com/games), team/player pages, daily [injury report PDFs](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-28_04_00PM.pdf), [2026-27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Team.pdf).
- **Official lines:** published by licensed sportsbooks — [DraftKings NBA](https://sportsbook.draftkings.com/leagues/basketball/nba), [FanDuel game pages](https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174) — and distributed as official league betting data by **Sportradar** (exclusive worldwide; authorized global distributor of official NBA betting data; UFDS integrity monitoring) and **Genius Sports** (U.S.) ([pr.nba.com](https://pr.nba.com/nba-betting-data-partnerships-sportradar-genius/), [Sportradar IR](https://investors.sportradar.com/news-releases/news-release-details/nba-and-sportradar-announce-landmark-long-term-global)).

## 3. Market rules that shape strategy (official)

- Parlay = all legs must win; odds multiply; a pushed leg reduces the parlay ([FanDuel terms](https://support.fanduel.com/s/article/Sports-Betting-Terms), [push rules](https://support.fanduel.com/s/article/What-happens-if-my-FanDuel-parlay-is-a-push), [DK house rules](https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf)).
- **Standard parlays may never contain correlated/related outcomes** — DK house rules bar them outright; same-game combos exist only as book-priced **SGP/SGP+** ([DK house rules](https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf), [FanDuel SGP](https://support.fanduel.com/s/article/What-is-a-Same-Game-Parlay-or-SGP)).
- NBA bets **settle on the league's official statistics** ([DK house rules](https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf)).
- Player props cover PTS/REB/AST/3PM and combos (PRA, DD, TD) ([DK NBA page](https://sportsbook.draftkings.com/leagues/basketball/nba), [FanDuel game page](https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174)).

## 4. Strategy framework (summary of docs/strategy-framework.md)

- **12 registered archetypes (S1–S12):** rest/fatigue, home/road splits, travel & time zone (incl. neutral-site games), injury-adjusted usage (official injury reports), pace & efficiency totals, matchup player props, own-line-vs-market (CLV), player-prop combos, SGP builds, cross-game parlays, live signals, futures.
- **Validation gates G1–G8:** data provenance (official sources only) → minimum sample (≥30 register / ≥100 eligible) → walk-forward backtest → held-out 20% → binomial significance vs break-even (p<0.05; break-even at −110 ≈ 52.38%, derived) → risk caps + fractional Kelly → positive CLV → correlation gate (measured ρ below threshold for cross-game parlays; same-game combos only as book-priced SGP).
- **Correlation:** Pearson/Spearman on official game results + official line history; matrix defined on the Correlation page; **measured values intentionally blank (UNVERIFIED, flag F1)** until the official line-history feed is ingested.
- **Leaderboard:** metrics n / win rate / ROI / CLV / Sharpe / max drawdown / gates passed; tiers Gold/Silver/Bronze = site recognition (non-monetary, flag F4); standings currently empty by design (flag F2).

## 5. Verification & irregularities

- Line-by-line verification log: `docs/verification-log.md`; source register: `research/sources.md` and `pages/sources.html` (35 sources).
- **Flagged for Review (F1–F12)** on `pages/flagged.html` — includes unmeasured correlation/performance values (F1–F2), project-defined thresholds (F3–F4), and official-page irregularities: key-dates "Playoffs 2026" label (F5), Phoenix arena naming PHX Arena vs Footprint Center (F6), "Mexico City Game 2025" label (F7), press-only report of prop-market restrictions (F8), regulator-hosted house rules PDF (F9), derived 1,230 figure (F10), live-record snapshots (F11), glossary coverage policy (F12).

## 6. Next steps (automated, no manual input)

1. Ingest official line history via Sportradar (NBA's authorized distributor) and official results from stats.nba.com.
2. Run walk-forward backtests per strategy; compute the correlation matrix.
3. Populate the leaderboard only for strategies passing all gates; publish flagged items for review.

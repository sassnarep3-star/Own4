# LINES.md — Our Own Originated NBA Lines

**Snapshot:** 2026-11-02 (UTC) · **Priced slate:** 2026-11-04 (14 official games)
**Model:** M1 prior-season additive ratings · **All inputs:** official NBA.com

## Method (no invented constants)

- `L = (mean(OffRtg) + mean(DefRtg)) / 2 over the 30 official team rows of one season`
- `P = (PACE_a + PACE_b) / 2`
- `E_a = OffRtg_a + DefRtg_b - L ; E_b = OffRtg_b + DefRtg_a - L`
- `S_a = E_a * P / 100 ; S_b = E_b * P / 100`
- `fair_spread_a = -(S_a - S_b) ; fair_total = S_a + S_b`
- `sigma = sd( (actual margin) - (projected margin) ) over TRAIN settled games only`
- `p_a = Phi( (S_a - S_b) / sigma ) ; fair American odds from p (zero margin)`

- League-average rating 2025-26 = `114.7600`; 2026-27 = `111.9733`.
- Residual margin sigma = `14.5764`, estimated from `41` official
  settled games dated 2026-10-23 … 2026-10-28 only, i.e. **before** the slate being priced.
- NetRtg, OffRtg, DefRtg and PACE definitions: [NBA.com Stat Glossary](https://www.nba.com/stats/help/glossary).

## Fair lines (M1) — 2026-11-04 slate

`fair_spread_a` is Team A's fair spread; a negative value means Team A is projected to win.
Fair moneylines are **zero-margin model outputs**, not sportsbook prices.

| Game ID | Matchup | Fair spread A | Fair total | Fair ML A / B | P(A wins) | Market spread | Market total | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0022600174 | ATL vs WAS | -14.25 | 235.3 | -509 / +509 | 0.836 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600173 | PHI vs DET | 8.51 | 225.7 | +258 / -258 | 0.280 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600175 | MIL vs BOS | 13.96 | 225.6 | +491 / -491 | 0.169 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600176 | CHA vs BKN | -14.54 | 223.3 | -528 / +528 | 0.841 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600177 | CHI vs NYK | 11.75 | 232.1 | +376 / -376 | 0.210 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600180 | CLE vs OKC | 6.94 | 228.2 | +215 / -215 | 0.317 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600179 | UTA vs NOP | 3.89 | 240.6 | +153 / -153 | 0.395 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600178 | IND vs MEM | 1.83 | 233.3 | +122 / -122 | 0.450 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600181 | MIN vs HOU | 2.28 | 226.4 | +128 / -128 | 0.438 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600182 | TOR vs DEN | 2.29 | 233.3 | +128 / -128 | 0.438 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600183 | POR vs PHX | 1.70 | 223.9 | +120 / -120 | 0.454 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600184 | DAL vs SAS | 13.73 | 229.1 | +477 / -477 | 0.173 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600185 | LAL vs SAC | -11.16 | 233.1 | -351 / +351 | 0.778 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| 0022600186 | MIA vs LAC | -1.11 | 233.1 | -113 / +113 | 0.530 | — UNVERIFIED | — UNVERIFIED | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |

## Deliberately blank fields

Market odds/closing lines, vig, closing-line value, edge, per-game home-court adjustment,
M2 (current-season) moneyline, and player-prop fair lines are all **blank and flagged UNVERIFIED**.
Reason: the [NBA's own release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group) states official betting data goes to *licensed
operators*; the [NBA.com games page](https://www.nba.com/games?date=2026-11-04) exposes a "HIDE ODDS" toggle but no odds
values, and no free official player game logs exist. See `pages/flagged.html`.

## M2 current-season variant

A second projection using the [official 2026-27 advanced table](https://www.nba.com/stats/teams/advanced?Season=2026-27) (4–7 GP per team)
is published on the site for comparison. It has no out-of-sample calibration, so its moneyline is blank.

## Caveats

- No home/away designation is asserted; per-game home-court adjustment is UNVERIFIED.
- No market or closing odds are available from free official NBA pages (IR-04); all market columns are blank.
- M2 (current-season) lines use only 4-7 games per team and have no out-of-sample calibration; their moneyline is blank.
- Fair prices are zero-margin model outputs, NOT sportsbook prices and NOT betting advice.

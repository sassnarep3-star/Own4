# Own4 — NBA Lines Lab

Originate your own NBA lines and compete with skill-based strategies on a leaderboard.

**Live site:** https://sassnarep3-star.github.io/Own4/ (GitHub Pages, built from this repo — see `index.html`, `pages/`, `assets/`)

## What this project does

- Collects, organizes and analyzes NBA data **exclusively from official, verified sources** (nba.com, official.nba.com, stats.nba.com, cdn.nba.com, pr.nba.com, official licensed sportsbooks, and the NBA's official betting-data distributors Sportradar / Genius Sports).
- Registers **strategy archetypes** for originating lines: single bets, parlays, player-prop combos, same-game parlays, live and futures — see `pages/strategies.html`.
- Enforces **validation gates G1–G8** so only selectively skill-based strategies reach the **leaderboard** (luck removed via walk-forward testing, held-out samples, significance tests, risk caps, CLV and correlation gates) — see `pages/validation.html`, `pages/leaderboard.html`.
- **Determines correlation** between bet legs with a defined methodology; measured values are computed only from official data and are left blank + flagged `UNVERIFIED` until then — see `pages/correlation.html`.
- **No hallucinations:** every table row on the site links to an official source; any value that cannot be confirmed from an official source is left blank and published on the **Flagged for Review** page (`pages/flagged.html`).

## Site map

| Page | Contents |
|---|---|
| `index.html` | Dashboard landing page |
| `pages/executive-summary.html` | Executive summary |
| `pages/league.html` | Verified league & rules facts |
| `pages/season.html` | 2026-27 season calendar & Emirates NBA Cup rules |
| `pages/teams.html` | All 30 teams, IDs, official sites, arenas |
| `pages/stats.html` | Official stat definitions, leader minimums, stats platforms |
| `pages/markets.html` | Where official lines are published; bet-type definitions & rules |
| `pages/strategies.html` | Strategy catalog S1–S12 + bet-format guide |
| `pages/validation.html` | Validation gates G1–G8 + luck-removal methods |
| `pages/correlation.html` | Correlation methodology + measurement matrix |
| `pages/leaderboard.html` | Competition design, metrics, reward tiers, standings |
| `pages/flagged.html` | Flagged for Review (unverified values + irregularities F1–F12) |
| `pages/sources.html` | Source register (every official source + what it verifies) |

## Repo docs

- `docs/executive-summary.md` — executive summary
- `docs/strategy-framework.md` — strategy, validation, correlation & leaderboard framework
- `docs/verification-log.md` — line-by-line verification log with sources and flags
- `research/sources.md` — research source register
- `COORDINATION.md` — shared task board / session log (multi-session coordination)

## Verification policy

Every factual table row on the site carries a link to the official page it was confirmed on (accessed 2026-11-02). If a value cannot be confirmed from an official source, the cell is left **blank** and flagged **UNVERIFIED** — never inferred or filled in. Flagged items are collected on the Flagged for Review page.

## Responsible gambling

If gambling is a concern: National Problem Gambling Helpline **1-800-GAMBLER** (1-800-426-2537), 24/7 — [ncpgambling.org](https://www.ncpgambling.org/help-treatment/about-the-national-problem-gambling-helpline).

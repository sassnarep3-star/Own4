# COORDINATION.md — Shared Task Board (Own4 / NBA Lines Project)

Session rules: all work in this session happens on branch `arena/42d467e4-own4`
(the fixed session branch). No other branches are created or pushed to.

## Sessions

| Session ID | Branch | Status | Notes |
|---|---|---|---|
| arena/42d467e4-own4 | arena/42d467e4-own4 | active | Sole active session; also performs the final integration role (merges to main, enables Pages, records PR). |

## Task Board

| # | Task | Status | Owner | Files touched | Sources / verification | Irregularities |
|---|---|---|---|---|---|---|
| 1 | Repo review (line-by-line, flag irregularities) | done | arena/42d467e4-own4 | README.md, COORDINATION.md | Repo at 319d6b0 contained only `README.md` ("# Own4"). Reviewed line by line; no code, no hidden files. | None found. |
| 2 | Research official NBA sources (league facts, rules, teams, stats, season format, markets, integrity) | done | arena/42d467e4-own4 | research/sources.md, assets/js/data*.js | nba.com, official.nba.com, cdn.nba.com, stats.nba.com, pr.nba.com, gleague.nba.com, nbatickets.nba.com, ak-static.cms.nba.com injury reports, sportsbook.draftkings.com, support.draftkings.com, sportsbook.fanduel.com, support.fanduel.com, massgaming.com (regulator-hosted DK house rules), investors.sportradar.com, pr.nba.com, ncpgambling.org — all fetched/searched 2026-11-02; see research/sources.md | Flagged items F5–F9 (see Flagged for Review page / COORDINATION log below). |
| 3 | Strategy framework: signals, validation gates, correlation methodology, leaderboard design | done | arena/42d467e4-own4 | docs/strategy-framework.md, pages/validation, pages/correlation, pages/leaderboard | Official anchors where they exist (DK house rules correlation prohibition; FanDuel SGP/parlay defs; stats.nba.com data). Thresholds are project-defined and flagged as such. | Performance/correlation values NOT measured — no official line-history dataset ingested this session; all such cells left blank + UNVERIFIED (flag F1, F2). |
| 4 | Executive summary | done | arena/42d467e4-own4 | docs/executive-summary.md, pages/executive-summary.html | Derived from tasks 2–3; every factual claim carries a source link. | None. |
| 5 | Build GitHub Pages site (landing + category subpages + tables + Flagged for Review) | done | arena/42d467e4-own4 | index.html, pages/*.html, assets/css/style.css, assets/js/*.js | Every table row linked to an official source; unverifiable cells blank + flagged UNVERIFIED. Static site, no external CDN dependencies. | None. |
| 6 | Enable GitHub Pages, verify deploy, PR to main, merge, record results | in progress | arena/42d467e4-own4 | repo Pages settings, COORDINATION.md | gh api pages endpoints; PR link recorded in log below. | — |

## Log

- 2026-11-02: Session arena/42d467e4-own4 initialized COORDINATION.md. Repo review: single commit 319d6b0 "Initial commit" containing only README.md; no irregularities.
- 2026-11-02: Tasks 2–5 completed by session arena/42d467e4-own4 (sole session). Research performed via official sources only; all source URLs in research/sources.md. Flagged for Review items: F1 unmeasured correlation values, F2 unmeasured strategy performance, F3 project-defined validation thresholds, F4 project-defined (non-monetary) leaderboard rewards, F5 nba.com/news/key-dates labels "April 17: NBA Playoffs 2026 begin" inside the 2026-27 key-dates list (likely label typo on official page), F6 Phoenix Suns arena listed as "PHX Arena" on nbatickets.nba.com vs "Footprint Center" on nba.com arena articles, F7 gleague.nba.com/key-dates labels "NBA Mexico City Game 2025" while the official 2026-27 schedule PDF notes the game on Sat 11/7/2026 at Arena CDMX, F8 Boston Globe 2026-10-16 report on NBA prop-bet restrictions is a press report, not an official league publication, F9 DraftKings house rules PDF is regulator-hosted (massgaming.com), F10 "1,230 total regular-season games" is derived arithmetic (30×82÷2) from official facts, F11 live standings/records are point-in-time snapshots as of 2026-11-02.
- 2026-11-02: PR + merge + Pages deploy: (recorded after merge — see below)

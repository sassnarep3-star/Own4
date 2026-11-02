# Verification Log — line-by-line (accessed 2026-11-02)

Policy: every factual claim was checked against an official source (nba.com, official.nba.com, cdn.nba.com, stats.nba.com, pr.nba.com, gleague.nba.com, nbatickets.nba.com, ak-static.cms.nba.com, licensed sportsbooks DraftKings/FanDuel + their official support pages, regulator-hosted DraftKings house rules, Sportradar IR, NCPG). Anything not confirmable is left blank and flagged UNVERIFIED (see Flagged for Review, F1–F12). No hallucinations, no inferred values.

## Repo review (line by line)

| Line/file | Content | Finding |
|---|---|---|
| `README.md` (commit 319d6b0) | `# Own4` | Only file in repo at session start; no irregularities |
| `.git/` | single commit "Initial commit" | No hidden files, no other branches with content; clean |

## League facts

| Claim | Verified value | Source |
|---|---|---|
| Teams / structure | 30 teams; 2 conferences × 3 divisions; full division lists | https://www.nba.com/news/about |
| Regular-season games | 82 per team (2025-26; also 2026-27) | https://www.nba.com/news/about ; https://www.nba.com/news/nba-cup-101 |
| Total RS games | 1,230 — **derived** (30×82÷2), flagged F10 | derived from the two above |
| Quarter length / OT / halftime | 12 min × 4; OT 5 min; halftime 15 min | https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf (Rule 6) ; https://www.nba.com/news/about |
| Shot clock | 24 s | Rules PDF Rule 7 ; https://www.nba.com/news/about |
| Court / rim / FT / 3-pt | 94×50 ft; rim 10 ft; FT 15 ft from rim (About wording); arc 23'9" top / 22' corners | https://www.nba.com/news/about ; https://official.nba.com/rule-no-1-court-dimensions-equipment/ |
| Basketball | 9 in diameter, 8.5–9.5 psi | https://www.nba.com/news/about |
| Roster | max 15, 12 active per game | https://www.nba.com/news/about |
| Playoffs | seeds 1–6 auto; 7–10 Play-In; best-of-seven 2-2-1-1-1 | https://www.nba.com/news/about ; https://www.nba.com/news/faq ; https://www.nba.com/news/nba-play-in-tournament |
| Titles | Celtics 18, Lakers 17 | https://www.nba.com/news/about ; https://www.nba.com/news/most-championships-nba-history |
| Founded | 1946 (BAA), NBL merger 1949, Podoloff first president | https://www.nba.com/news/about |
| Replay Center | Secaucus NJ since 2014-15 | https://www.nba.com/news/about ; https://official.nba.com/replay/ |

## 2026-27 season

| Claim | Verified value | Source |
|---|---|---|
| Schedule release | Aug 13, 2026; 80 of 82 games fixed; 2 TBD Dec 4–10 (Cup-dependent) | https://www.nba.com/news/2026-27-nba-regular-season-schedule |
| Opening night | Oct 20, 2026 — BOS@DET 3 ET, NYK v PHI 7 ET (MSG), OKC@SAS 9:30 ET, NBC/Peacock | https://www.nba.com/news/nba-rosters-set-for-2026-27-regular-season ; https://www.nba.com/news/nba-schedule-season-opener-2026-27 |
| Preseason / camps / rosters | camps Sep 29; preseason Oct 3–16; rosters Oct 19 | https://www.nba.com/news/fantasy-basketball-every-important-date-on-the-2026-27-nba-calendar ; https://gleague.nba.com/key-dates |
| Cup 2026 | Group Play Oct 30–Nov 27 (60 games); knockout Dec 4–11; Championship Dec 11, Hinkle Fieldhouse, Indianapolis; 67 Cup games count except Championship | https://www.nba.com/news/nba-cup-101 ; https://www.nba.com/news/nba-cup-frequently-asked-questions ; https://www.nba.com/news/2026-27-schedule-announced |
| Neutral-site notes | Nov 7, 2026 Arena CDMX; Oct 23, 2026 & Feb 26, 2027 Moody Center, Austin | https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Team.pdf (arena notes) |
| Trade deadline / contracts | Feb 11, 2027 deadline; Jan 5 first 10-day; Jan 10 guaranteed | https://www.nba.com/news/fantasy-basketball-every-important-date-on-the-2026-27-nba-calendar ; https://gleague.nba.com/key-dates |
| All-Star 2027 | Feb 19–21, 2027, Phoenix | https://gleague.nba.com/key-dates |
| Season end / play-in / playoffs | Apr 11, 2027 end; Apr 12 rosters; Apr 13–16 Play-In; Apr 17 playoffs begin | https://www.nba.com/news/key-dates (label "Playoffs 2026" flagged F5) |

## Teams

| Claim | Verified value | Source |
|---|---|---|
| 30 team names, divisions, team IDs, official sites | full table on site | https://www.nba.com/teams ; https://www.nba.com/news/about |
| Arenas | per-team arena names | https://nbatickets.nba.com/tickets/ (Phoenix "PHX Arena" vs nba.com "Footprint Center" — flagged F6) |
| Live team page example | NYK 2-4, 10th East (snapshot 2026-11-02, flagged F11) | https://www.nba.com/team/1610612752/knicks |

## Stats

| Claim | Verified value | Source |
|---|---|---|
| Stat definitions (PTS, REB, OREB, AST, %AST, %PTS, AST/TO, DEFRTG, PITP, PPP, FP, AST ADJ, AST PTS Created, Player PTS DIFF) | quoted verbatim on site | https://stats.nba.com/help/glossary/ (only displayed entries quoted — F12) |
| Leader minimums | 58 games (70% of 82); 300 FGM; 125 FTM; 82 3PM; 200 AST; 82 STL; career minimums listed | https://stats.nba.com/help/statminimums |
| Box-score abbreviations | MIN/PTS/REB/AST/FG/FG%/3PT/3PT%/FT/FT%/BLK/STL/TO/PF | https://support.draftkings.com/dk/en/glossary-of-box-score-terms?id=kb_article_view&sysparm_article=KB0011397 |

## Markets & lines

| Claim | Verified value | Source |
|---|---|---|
| Official NBA lines channels | DraftKings NBA page; FanDuel NBA game pages | https://sportsbook.draftkings.com/leagues/basketball/nba ; https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174 |
| Bet types & definitions | moneyline/spread/total/props/parlay/SGP/SGP+/round robin/teaser/live/futures | DK page; FanDuel support articles (terms, SGP, push, RR, teaser) |
| American odds | +150 = $100→$150; −200 = $200→$100 | https://sportsbook.draftkings.com/leagues/basketball/nba |
| Correlated-outcome ban in standard parlays | verbatim quote on site | https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf (flag F9: regulator host) |
| Settlement on official league stats | verbatim quote on site | same DK house rules PDF |
| SGP void/push repricing; Early Exit Protected | summarized on site | DK house rules PDF; https://support.draftkings.com/dk/en-us/early-exit-program-early-exit-protected?id=kb_article_view&sysparm_article=KB0012036 |
| Official betting-data distributors | Sportradar (exclusive worldwide; UFDS), Genius Sports (U.S.) | https://pr.nba.com/nba-betting-data-partnerships-sportradar-genius/ ; https://pr.nba.com/nba-announces-multiyear-partnership-sportradar-second-spectrum/ ; https://investors.sportradar.com/news-releases/news-release-details/nba-and-sportradar-announce-landmark-long-term-global |
| Prop-market restriction report (Oct 2026) | **press only — flagged F8, not treated as fact** | https://www.bostonglobe.com/2026/10/16/sports/nba-gambling-limitations/ |
| Responsible gambling | 1-800-GAMBLER (1-800-426-2537), 24/7 | https://www.ncpgambling.org/help-treatment/about-the-national-problem-gambling-helpline |

## Unverified by policy (left blank, flagged — never inferred)

- All measured correlation values (F1) — pending official line-history ingestion.
- All strategy performance metrics (F2) — pending walk-forward backtests.
- Project-defined thresholds/rewards (F3/F4) — competition rules, not external facts.

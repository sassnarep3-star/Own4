# Executive Summary — Own4 NBA Lines, Signals & Leaderboard

**Snapshot:** 2026-11-02 (UTC) · **Season:** 2026-27 in progress (4–7 GP per team)
**Live site:** https://sassnarep3-star.github.io/Own4/ · **Branch:** `arena/3ab8432d-own4`

## What was built

A fully autonomous, source-verified research pipeline and GitHub Pages dashboard that collects
official NBA data, **originates our own fair NBA lines**, researches single-bet / parlay /
player-prop strategies, measures correlations, passes every strategy through validation gates,
removes luck via out-of-sample and permutation testing, and runs a leaderboard competition with
rewards. Every table row carries a link to an official site; unconfirmable values are blank and
flagged on a dedicated **Flagged for Review** page.

## Headline numbers (all computed from official NBA.com values)

| Item | Value | Status | Official source |
| --- | --- | --- | --- |
| Official sources in registry | 22 usable + 3 unusable official endpoints | verified | [NBA.com Standings](https://www.nba.com/standings) |
| Rows checked line by line | 450 | 450 PASS / 0 FLAG | [NBA.com Glossary](https://www.nba.com/stats/help/glossary) |
| Teams covered | 30 (two full official seasons) | verified | [NBA.com Advanced 2025-26](https://www.nba.com/stats/teams/advanced?Season=2025-26) |
| Settled games transcribed | 62 of 92 | partial, flagged | [NBA.com Games 2026-10-23](https://www.nba.com/games?date=2026-10-23) |
| Our own fair lines originated | 14 games (2026-11-04 slate) | derived, formula published | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) |
| Correlations computed | 24 (Pearson, Spearman, permutation p, BH q, bootstrap CI) | verified | [NBA.com Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) |
| Strategies / validation gates | 13 / 10 | verified | [NBA.com Games 2026-11-01](https://www.nba.com/games?date=2026-11-01) |
| Strategies passing every gate | 0 | NOT VALIDATED | [NBA betting-data policy](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group) |
| Eligible research signals | 4 (top reward 100 pts) | verified | [NBA.com Standings](https://www.nba.com/standings) |
| Flagged items | 17 | published, non-blocking | [NBA.com Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) |

## Most important findings

1. **In-sample success is not skill.** Our prior-season rating model
   ([official 2025-26 advanced table](https://www.nba.com/stats/teams/advanced?Season=2025-26), 82 GP per team) picked
   `0.780` of training-window winners but only
   `0.476` of the chronological holdout
   (n=21); holdout binomial p =
   `1.0000`, Brier skill score
   `-0.064` — [official settled scores](https://www.nba.com/games?date=2026-11-01).
   It is classified **NOT skill-based** and receives no reward.
2. **A naive baseline beat the model.** Picking the team with the better official 2025-26 record
   was correct `0.710` of the time vs the
   model's `0.677` over 62 games.
3. **Team strength is highly stable within a season but only moderately across seasons.**
   2025-26 `WIN% ~ NetRtg` r = `0.971`; the true
   out-of-sample `2026-27 WIN% ~ 2025-26 NetRtg` r =
   `0.480` (BH q =
   `0.0145`) — [official source](https://www.nba.com/stats/teams/advanced?Season=2025-26).
4. **Parlay legs are not independent.** 2026-27 `PTS ~ NetRtg` r =
   `0.624` and `PTS ~ PACE` r =
   `0.400`. Same-game parlay/SGP prices require a joint
   model that cannot be verified here, so they are left blank.
5. **Prop combos are data-limited.** Leg correlations across 28 official team-leader baselines
   are near zero and not significant, but game-level player logs are unavailable from free
   official NBA pages, so fair prop lines are blank and UNVERIFIED —
   [official player table](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame).

## Decisions

- **No betting strategy is marked validated and no Division B reward is awarded.** This is a
  deliberate result of the validation gates, not a missing feature.
- **No market odds, vig, ROI, closing-line value or edge appears anywhere.** The
  [NBA's own release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group) says official betting data is distributed to licensed
  operators; the [NBA.com games page](https://www.nba.com/games?date=2026-11-04) exposes no odds values in retrieved
  content. Blank + flagged, per the no-hallucination rule.
- **Four out-of-sample research signals are ranked** in Division A (100 / 60 / 30 / 10 pts).
  These are predictive associations, not betting profits.
- **17 irregularities** including the 62/92 game coverage gap, `/null` player links on NBA.com,
  unavailable official CDN JSON, and the platform's single-branch constraint are published on
  the Flagged for Review page and do not block the merge.

## Governance

`COORDINATION.md` records 11 tasks with owner, status and exclusive file scopes, small frequent
commits, `git pull --rebase` before every push, completion records with sources and verification,
and a final integration pass (T09) that re-verifies all combined data, checks links and publishes.
The platform pins this session to one branch, so per-session branches/worktrees are replaced by
non-overlapping file scopes (IR-13). PR, merge and Pages deployment results are recorded in T10.

## Reproduce

`python3 scripts/build_lines.py && python3 scripts/correlations.py && python3 scripts/validate_strategies.py && python3 scripts/verify.py && python3 scripts/build_docs.py && python3 scripts/build_site.py && python3 scripts/check_links.py`

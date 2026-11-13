# NFL Command — Executive Summary (2026-11-13)

**Live page:** https://sassnarep3-star.github.io/Own4/nfl-command/
**Workspace:** `nfl-command/` · **Session:** `arena-934af359-own4` · **Branch:** `arena/934af359-own4`
**Data captured:** 2026-11-13, directly from nfl.com (standings, Week 10/11 schedules, Week 10 injury report, team passing stats).

## What this is

A decision dashboard for originating NFL lines from official league data. It answers three questions in
order: **what is true** (source-linked official data), **what we built from it** (own lines and registered
strategies), and **what survived validation** (nothing yet). Alongside the analysis it carries the decision
tools that were asked for: a **questions register** (what we know / do not know / what would unlock each
decision) and a **suggestions board** (16 proposals to choose from before anything is implemented).

## The headline, without softening

**0 of 6 registered strategies qualify. 0 of 6,000 reward points are awarded.** The margin model looks
skilled on the frozen holdout (weeks 8–10, n=30): directional accuracy 73.3% vs a 50.0% home baseline,
margin MAE 10.31 vs 12.63 naive, and a 10,000-run label-shuffled placebo at p=0.0004. But the
week-clustered 95% bootstrap CI of the improvement is **[−2.47, +3.74] points/game — it includes zero**,
the sample is under the pre-registered 300-selection minimum, and there are no market prices to test
closing-line value. Under the pre-registered gates, that is not enough to call skill. Published unchanged.

## What is verified (each with an official link on the site)

| Piece | Result | Source |
|---|---|---|
| Standings, 32 clubs | pct / net / home+road identities pass 32/32 | nfl.com/standings |
| Team passing, 32 clubs | passer-rating formula reproduces published Rate 32/32 | nfl.com/stats/team-stats |
| Game archive, 137 games (W1–10) | reproduces official W-L-T/PF/PA for all 32 clubs with **0 mismatches**; league PF = PA = 6,291 | nfl.com/standings |
| Game-page spot checks | NE 10–13 SEA (W1), PHI 7–27 CHI (W3), TEN 36–43 CIN OT (W8) — all exact | nfl.com/games |
| Week 10 slate | 14 games + 4 byes (CHI, DEN, PHI, TB); W10 final WAS 24–21 NYG read directly | nfl.com/schedules |
| Week 11 slate | 13 games + 6 byes (ATL, CLE, GB, LAR, NE, SEA); Mexico City SNF | nfl.com/schedules |
| Injury register | 326 player rows, 28 clubs; 14 Out, 11 Questionable, 95 DNP-practice | nfl.com/injuries |
| Own lines | Week 11 spread / total / projected score / win probability, all 13 games | model card + above |

## What was built

- **Own lines (Week 11).** Ridge-regularised margin ratings (λ=4, fixed a priori) + tendency totals from
  official PF/PA and the verified archive. Fitted home-field advantage +0.08 (near zero — flagged). Mexico
  City game gets no HFA. No market input anywhere; the market columns are blank, not zero.
- **Strategy competition.** 6 registered strategies (spread/total/ML singles, 2-leg cross-game parlays,
  player-prop combos, SGP) frozen in git **before** the backtest ran, 10 pre-registered gates, leaderboard
  with 1,000 points per strategy and an anti-luck rule: nothing places from in-sample performance.
- **Luck removal.** Walk-forward-only predictions (weeks 3–10), frozen holdout (8–10), 10,000 matched
  placebos, week-clustered bootstrap CIs, split-half sign stability. The margin signal clears direction and
  placebo but **not** the CI gate — that is the system working.
- **Injury & deficiency tracking.** Full official register + per-unit absence aggregates + official-news
  starter changes (BAL QB1 Jackson on IR and QB2 Huntley out for season; MIA QB1 Willis on IR → backup
  McCord; SEA QB1 Darnold out → backup Lock; CLE Watson, AZ Beck named starters). The league publishes
  **no depth chart**, so "2nd/3rd/4th string" is blank and flagged on every row — never inferred.
- **Decision layer.** 16 requirements with status, 20 questions (known/unknown/answer/unlock path),
  16 suggestions with impact/effort/risk for reviewer selection, 16 flagged items (none blocking).

## The three blocked requirements, stated plainly

1. **Market-priced betting (S1–S4, gate G6).** The NFL publishes no betting lines and no licensed feed
   exists in this repository. Every market cell is blank (F-01).
2. **Player props and prop combos (S5–S6).** No official per-game player logs in scope, no prop prices
   exist officially. Nothing graded (F-02).
3. **String-level depth (2nd/3rd/4th).** No league depth chart, no snap counts. Absence-based tracking
   only; string labels are unverified everywhere (F-08).

## Recommended path (choose on the Suggestions page)

1. **Freeze model v1 and grade Weeks 11–18 forward** (SUG-06, free) — the only honest way to grow the holdout.
2. **Decide on a licensed odds feed** (SUG-01) — unlocks every betting-market requirement and gate G6.
3. **Sample-extract official game books for player stats** (SUG-02) — unlocks props and depth tiers.
4. **Pick one canonical dashboard** among the 12 NFL workspaces (SUG-12).

## Repo review outcome

Four peer standings snapshots (nfl-edge, nfl-lines, nfl-intel, nfl-hub, captured 2026-11-12) reconcile with
today's official standings on every club except WAS/NYG — exactly the TNF final played between captures
(I-01, explained). nfl-edge's situational-record columns appear shifted by one (I-02, needs review). The
peer game archive was verified by reconciliation and 3/3 spot checks before use (F-11). Six peer-flagged
neutral-site games remain unconfirmed (F-06). nfl.com's own articles disagree on Lamar Jackson's timeline
(6–9 vs 6–10 weeks, F-07). Third-party nflverse datasets sit in the repo unused (I-06).

---
Analytical research only — not wagering advice. National Problem Gambling Helpline 1-800-MY-RESET
(1-800-697-3738) — https://www.ncpgambling.org/help-treatment

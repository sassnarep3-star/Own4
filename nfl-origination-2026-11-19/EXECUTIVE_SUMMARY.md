# Executive summary — NFL line origination (2026-11-19)

Session `arena/7ccaa4f3-own4`. Namespace `nfl-origination-2026-11-19`. All official reads made
2026-11-19 from nfl.com (see `pages/sources.html`).

## What was verified today

- **Standings 32/32** — sum W = sum L = 149, 2 ties (NYG 5-3-1, WAS 3-5-1), 150 games implied,
  sum PF = sum PA = 6,923. Every NET = PF − PA (engine-checked).
- **Week 11 schedule** — 13 fixtures + 6 byes (ATL, CLE, GB, LA, NE, SEA). TNF IND@HOU Nov 19
  8:15 PM; Sunday Nov 22 seven games + NYJ@LAC 4:05 + JAX@NYG, LV@DEN 4:25; MIN@SF 8:20 in
  Mexico City; MNF CIN@WAS Nov 23 8:15.
- **Injury report 32/32** — 253 rows across 30 clubs; CIN + WAS publish No Injuries Reported.
  Only 16 rows carry a game designation (all Thursday IND/HOU); every Sunday/Monday game-status
  cell is blank. Blank is not available.
- **Week 10 finals 14/14** — verified results feed for Week 10 (e.g. SF 46 @ DAL 40, LAC 23 @ BAL 20).
- **November trades 12** — 11/10 cluster of 9 (Bates, Davis, Hooker, Allen, Cousins, Henley,
  Downs, Neuzil, Vorhees) + Cisco, Godchaux, Brissett.
- **IND@HOU game centre** — RELIANT STADIUM, HOUSTON, TX; 12 team-stat rows (HOU 25.9 PPG 9th,
  IND 20.8 PPG 23rd). Schedule page hotel link says NRG Stadium — disagreement flagged F-01.
- **Depth charts** — nfl.com/depth-charts/ returns 404 (verified today). No official depth order exists.

## What the lab originates

For each of the 13 Week 11 fixtures, in order: **side** (fair line + P(home win)), then **total**
(two estimators A/B with gap), then **moneyline** — each stored as probability plus inputs.
Market line and difference are blank for every market: no official price source exists (F-03).
Price-snapshot store: 39 records (13 × 3), all opener/closer blank by policy.

## Competition result

6 pre-registered strategies, 4 divisions (singles, game parlays, same-game parlays, prop combos).
Parlays/props behind the joint-evidence gate (ineligible). Singles: 0 graded games.
**0 qualify, 0 rewards.** Signal and staking are separate columns; staking is blank.
Correlations (official standings only, n=32): NET vs W r=0.86, PF vs W r=0.68, PA vs W r=−0.63,
NET vs PF r=0.75, PF vs PA r=−0.15.

## Decisions needed (owner)

Price-data policy (Q-01/S-01), validation floor (Q-02/S-02), depth-order route (Q-03/S-03),
venue-authority rule (Q-06/S-06), public/private split (Q-05/S-05), reward structure (Q-11/S-09).
All on the Suggestions page, left at proposed — awaiting owner.

## Flagged irregularities (15, non-blocking)

Venue disagreement (F-01); Lions designation disagreement (F-02); no price source (F-03);
depth 404 (F-04); 16/253 designations (F-05); Marvin Harrison Jr. in Texans table (F-06);
Jacob Hummel at LB (F-07); 12/13 venues pending game centre (F-08); reserve ledger carried (F-09);
Weeks 1–9 finals carried (F-10); no clock time today (F-11); no snap/inactive/Game Book source (F-12);
0 graded games (F-13); MIN@SF stadium blank (F-14); Sunday injury text blank (F-15).

## Reproduce

`python3 nfl-origination-2026-11-19/engine/compute.py && python3 nfl-origination-2026-11-19/engine/build.py && python3 nfl-origination-2026-11-19/engine/verify.py`

Analysis only. Not wagering advice. Helpline: 1-800-MY-RESET (https://www.ncpgambling.org/help-treatment).

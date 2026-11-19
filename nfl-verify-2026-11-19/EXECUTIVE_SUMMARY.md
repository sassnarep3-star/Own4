# Executive summary — NFL line-origination fresh re-verification (2026-11-19)

Session `arena/6c8bbde6-own4`. Namespace `nfl-verify-2026-11-19`. Claim committed as `1bebaad` on branch `arena/6c8bbde6-own4`.

## What this is

A fresh, date-stamped official re-verification of the current NFL state, read from `nfl.com` on **2026-11-19**, with line-by-line reconciliation against the repo's committed (2026-11-15..18) snapshots, and a decision-readiness / questions / suggestions board. It is a verification and decision surface: it publishes the official facts it can confirm, blanks and flags what it cannot, and records the blockers that must be cleared before any strategy decision. It is not a betting product: no picks, no prices, and no strategy shown as eligible or reward-qualifying.

## What the 2026-11-19 read settles

- **Standings (32/32).** All 32 clubs transcribed from the official standings page. The arithmetic reconciles: **149 wins = 149 losses**, 150 games played, 2 ties (NYG 5-3-1, WAS 3-5-1). AFC leaders: BUF 8-1, CIN 7-2, PIT 6-3, CLE 6-4, JAX/KC/DEN 7-2. NFC leaders: SF 8-1, DET/MIN/CHI 7-2, SEA/LAR 6-4. Bottom: NYJ 2-8, MIA 1-8, TEN 1-8, LAC 1-8, PHI 2-7, AZ 3-7. Every team's NET = PF − PA (computed check C-04).
- **Week 11 schedule (13 fixtures + 6 byes).** TNF IND@HOU Nov 19 8:15 (Prime); Sunday Nov 22 seven games; NYJ@LAC, JAX@NYG, LV@DEN 4:25; MIN@SF 8:20 in Mexico City (NBC); MNF CIN@WAS Nov 23 8:15 (ESPN). Byes: ATL, CLE, GB, LAR, NE, SEA. This is a forward-looking slate — the fresh read confirms the current state against the committed snapshots.
- **Injury report (10/32 clubs in full, 111 rows).** IND, HOU, PIT, PHI, AZ, KC, BAL, CAR, TB, DET transcribed line by line with practice status and game status. The three previously-missing Lions game-status designations (Kerby Joseph, Cade Mays, D.J. Reed) are now populated — all practicing in the Week-11 read, confirming designations are a **timestamped series**, not a static level (flag VF-06).
- **Roster turnover as a first-class event.** 25 Reserve/Injured moves and 12 November trades captured in full from the official transaction pages (e.g. Aidan Hutchinson to Reserve/Injured 11/18; the 11/10 trade cluster Bates, Jordan Davis, Hooker, Allen, Cousins, Henley, Downs, Neuzil, Vorhees).
- **Reconciliation (computed, not typed).** 10 checks, all PASS — see the Verification page. Key: 32 teams, W=L, NET identity, 13 fixtures + 6 byes partition the league, and the IND@HOU venue discrepancy (see below) is correctly detected and flagged.

## What the data still gets wrong / cannot confirm

- **No official price source exists.** No NFL or official page publishes betting lines, odds or closing prices. Every market/price/ROI/residual column is **blank by policy** (flag VF-04). This blocks the price-snapshot store, the residual-vs-market column, and any ROI/backtest publication.
- **No official snap-count / actual-starter feed.** Replacement-depth, the 2nd/3rd/4th-string deficiency feature, and the availability graph all require an actual-starter or snap-count join that no official source in the verified corpus provides (flag VF-10).
- **Houston depth is image-only.** The Texans' official depth chart is a static image and was not transcribed by eye (flag VF-05).
- **Venue discrepancy (IND@HOU).** The schedule page's stadium/hotel link reads "NRG Stadium"; the official game centre Game Info reads "Reliant Stadium." Both are official surfaces disagreeing. The game centre is treated as authoritative per the brief; the discrepancy is flagged (VF-01), not silently resolved.
- **Injury scope limit.** Only 10 of 32 clubs were recounted live this session; the other 22 are not asserted (flag VF-02). No exact clock time is exposed by the fetch tool (flag VF-03).
- **12 of 13 venues** were transcribed from the schedule page's own links, not yet from each game centre (flag VF-08).

## Decisions the owner needs to make

(1) **Price-data policy** — no official price source exists; choose a licensed/authorized feed or publish fair-line-only backtests with an explicit no-market caveat (S-04, Q-01). (2) **Depth-source route** — per-club official depth pages (verified 32/32 by a peer, HOU image-only) vs. snap counts pending an authorized source (S-05, Q-03). (3) **Venue-authority rule** when schedule and game centre disagree (S-07, Q-07). (4) **Sample-size floor** for publishing a strategy as validated — peers use n ≥ 300 out-of-sample (Q-04). (5) **Public/private data split** for the site (Q-05). Each option is on the Suggestions page; the verdict is left blank for the owner.

## The honest result

No strategy qualifies for rewards on the current verified evidence, and the model loses to the vig-free market on proper score. This round does **not** overstate that: it records the gap and the blockers rather than inflating any claim.

## Limits

Every official read was made with the page-fetch tool on 2026-11-19 and is recorded with its URL and read date; raw page text was not saved to the repository, so reads carry URLs and dates but no sha256 hash. The 22 non-recounted clubs and 12 non-game-centre venues are disclosed as scope limits. The clone is shallow, so pre-registration commit hashes cannot be checked here. Peer namespaces were not re-read line by line in this round.

Analysis only. Not wagering advice. Helpline: 1-800-MY-RESET (https://www.ncpgambling.org/help-treatment).

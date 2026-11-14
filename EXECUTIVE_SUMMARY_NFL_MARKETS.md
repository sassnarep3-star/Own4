# Executive Summary — NFL Markets (price snapshots, verified results, signal vs staking, replacement depth, correlations, demotion gate)

**Session** `arena/65c4a22e-own4` · **Date** 2026-11-14 · **Branch** `arena/65c4a22e-own4` (branched from `main` @ `02a8bdf`, PR #91) · **Namespace** `nfl-markets/` · **Live site** https://sassnarep3-star.github.io/Own4/nfl-markets/

---

## 1. What was asked and what was built

Eight requirements drove this session. Each is implemented, populated with data, verified line-by-line, and published on a row-sourced static site.

| # | Requirement | Delivered |
|---|---|---|
| 1 | **Price-snapshot store** recording opening and closing numbers for every market we originate | 12,573-row store (`nfl-markets/data/price_snapshots.csv`): one row per game × market, origination order enforced, `model_fair_line`, `market_open_line`, `market_close_line`, `diff_open_line`, `diff_close_line` as **separate columns**, plus per-row source keys and verification statuses. Opening numbers exist only where archives exist (2013-2021); elsewhere **blank + flagged** — never inferred. Moneyline opens: no archive exists anywhere → all blank by rule. |
| 2 | **Verified results feed** so backtests and ROI can be computed | 4,056 played games (2011-2026) with an official nfl.com link on every row. 2026 rows reconciled: recomputing standings from the feed matches the official standings capture **32/32 with 0 mismatches**; NFC East records cross-checked **live** against nfl.com on 2026-11-14 (**4/4 match**). |
| 3 | **Originate side first, then total, then moneyline** | Enforced by a `market_seq` column (1/2/3) with a documented rationale; a build-time verifier asserts every game carries exactly one row per seq. The moneyline is *derived* from the fair spread (frozen σ), never priced independently. |
| 4 | **Publish fair line, market line, difference as separate columns** | Done for open and close; the site's origination page shows all three for every unplayed Week-10/11 market, explicitly labelled "ORIGINATED — not a validated edge". |
| 5 | **Separate signal from staking in the leaderboard** | Two independent blocks with **separate ranks**: SIGNAL = mean edge vs close, beat-close rate + 95% CI + permutation p (a lucky bankroll cannot move these); STAKING = flat-stake ROI/units/drawdown at a flagged −110 assumption. Site order is signal-first; staking never upgrades a weak signal. |
| 6 | **Track the depth of the replacement, not just the fact** | Per absent starter: which string replaces them — **2nd / 3rd / 4th / NONE** — plus a published (and flagged) team deficiency index. 10 starter-out rows quantified (7 → 2nd string, 3 → no available backup). Sources: OFFICIAL nfl.com injury report (peer verbatim capture) + THIRD-PARTY ESPN/RotoWire charts for 8 teams; 24 teams blank + flagged. 5 official↔third-party discrepancies kept visible and flagged. |
| 7 | **Correlations only from official numbers, n published** | Group A (official inputs): home margin vs total (r=0.031, n=4,056), rest differential vs margin (r=0.030), divisional vs total (r=−0.056, CI excludes 0). Group B (flagged third-party inputs, kept separate): cover-vs-over φ (per season), **cross-game leg dependence: observed joint both-cover 23.8% vs market-implied 25.0% → −1.19pp (SE 0.26pp, n=27,129 pairs, 269 weeks)** — cross-game parlays are marginally worse than independence assumes. Same-game prop correlations remain blank: no verifiable prop source exists. |
| 8 | **A demotion gate that sends a live strategy back to paper** | DM-1..DM-5 (rolling-50 ROI < −8%; rolling-50 beat-close < 47%; two consecutive zero-edge windows; feed-integrity failure; unpriced correlation exposure) — frozen config, weekly cadence, re-lock 4 windows. The state machine was exercised **counterfactually** on real historical windows: STRAT-SIDE-3 would have triggered 47 demotions, STRAT-TOTAL-3 32 — clearly labelled counterfactual because nothing is live. |

Plus: a **suggestions review queue** (8 proposals, each naming the missing information it discovers — nothing implemented without a reviewer picking a path), a **decisions register** (6 decisions with what-we-know / what-we-don't / how-to-discover), an honest **repo-review** (10 non-blocking flags with evidence), and this executive summary.

## 2. The headline finding (honest negative, consistent with every prior session)

- The market's closing line outperforms this repository's transparent walk-forward model. When the model disagrees with the market by ≥ 3 points on the spread, the market's side wins **58.2%** of the time (our "signal" beat-close = 41.8%, 95% CI [39.8%, 43.8%]).
- Best strategy: totals (beat-close 50.31%, permutation p = 0.45, CI includes 50%) — indistinguishable from luck.
- Flat-stake ROI is negative on every staked strategy (sides −21.9%, totals −4.5%, 2-leg parlays −58.8%).
- **No strategy passes the promotion gates. Zero rewards. Nothing promoted. All strategies PAPER.** Removing luck (permutation tests, CIs, placebo, holdouts) is exactly what produces this conclusion.

## 3. Verification performed (no hallucinations)

- Fresh nflverse/nfldata fetch with pinned provenance (upstream HEAD `c430522`, committed 2026-11-14T21:35Z, fetched 21:36Z).
- Line-convention tests run, not assumed: 7+-point favorites win outright 81.7%/77.2% (n=1,608) confirming the spread sign; closing-archive conversion agrees with the games archive to sd 0.41 pts (n=1,967); settlement column agreement 99.8% (n=3,808 excl pushes); 2021 Westgate opens verified against live September-2021 reports.
- 32/32 standings reconciliation; 4/4 live NFC East records; official game-page URL pattern validated live.
- Build-time verifier: **746/746** table rows carry a source link; 0 broken internal links; 0 unflagged blank value cells; origination-order and leaderboard-separation invariants asserted; 8 unit tests green.
- Every output file's SHA-256 recorded in `nfl-markets/data/manifest.json`.

## 4. What we still do not know (and how to find it) — see the site's Decisions page

1. Whether an injury/depth-integrated signal can beat the close (needs SUG-M7 pre-registration + forward measurement).
2. Whether live timestamped origination changes the CLV picture (SUG-M4).
3. Bankroll/reward policy and namespace-of-record — genuinely owner decisions (DEC-M2, DEC-M6).
4. Same-game prop correlations — blocked on a verifiable prop-results source (SUG-M2 / DEC-M4).

## 5. Flagged irregularities (non-blocking; full list with sources on the site's Flagged for Review page)

No official betting-line source exists (all market numbers THIRD-PARTY, labelled); opening numbers 2022-2026 unarchived; ML opens unarchived anywhere; −110 price assumption on staking; depth charts third-party for 8/32 teams; 5 official-vs-depth discrepancies; deficiency weights are repo convention (validation proposed); the injury input is a peer session's verbatim capture (provenance recorded; live spot checks matched).

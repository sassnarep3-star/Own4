# NFL Book — Executive Summary

## Update · 2026-11-18 UTC (session `arena/f7037afe-own4`)

- **Week 11 schedule re-read live from nfl.com:** 13 games, 6 byes, matchups and kickoff times identical to the committed slate (`data/verification_2026-11-18.json` V18-01, PASS).
- **Week 10 Lions game-status cells** (Joseph, Mays, Reed) re-read: all three *Out* on the official report (V18-02, PASS). Old blank-cell irregularity resolved for these rows.
- **Week 11 injury report:** not yet published at read time; Week 11 availability stays blank (V18-05, PENDING, FB-20).
- **Week 10 row count:** the committed transcript holds 347 rows and is internally consistent, but the live page was not recounted; the brief's 279/254 figures are not reproduced (V18-04, FLAG, FB-21).
- **Correction:** flag FB-18's J.J. McCarthy example is refuted by his nfl.com player page (listed with the Giants). Kept for the record as FB-19.
- **Repo sweep:** 34 of 34 NFL namespace verifiers pass when run as their CI runs them (`data/verifier_sweep_2026-11-18.json`). A verifier pass checks structure and links, not the underlying numbers.
- **Open items for an owner decision:** five stale open PRs (FB-22); definitional rows without links (FB-24).

Nothing in this update changes a number in the rest of this document.

---


**Session:** `arena/c8969a10-own4` · **Date:** 2026-11-14 UTC · **Namespace:** `nfl-book/`

## What was built

| Deliverable | Result |
|---|---|
| Price-snapshot store | 39 snapshots (13 Week-11 games × side/total/moneyline) with **open** (train ≤ Wk9) and **close** (train ≤ Wk10 TNF) values, drift, timestamps. Market open/close stored as `null` — no official price source (FB-01). |
| Verified results feed | 137 settled 2026 games with an official nfl.com URL per row; **32 re-read line-by-line this session** (all Week 1, all Week 9, Week 10 TNF); **160/160** standings cells recomputed match; league identities pass (V-01…V-03). |
| Origination order | Side → total → moneyline enforced in code and recorded per row (audit asserts the order). |
| Fair / market / difference | All three columns published per market. Fair values populated; market and difference **blank + flagged** (no official lines exist). |
| Signal vs staking | Leaderboard ranks by **signal tier first**; staking columns are reported separately under an ASSUMED −110 price and can never promote a strategy. |
| Replacement depth | Depth published **only where official text states it** (SEA QB: Lock = "the backup" → 1st string, Milroe → 2nd). All other depth blank + flagged (no official depth chart, FB-07). |
| Correlations | 5 computed from official scores only, each with **n, r, p, 95% CI**; 4 requested-but-unsourced correlations published **blank with reasons**. |
| Demotion gate | D1 armed: 4 auto-firing conditions return any LIVE strategy to PAPER; currently no strategy is LIVE. |
| Suggestions | 13 proposals with options A/B/C, cost, risk, recommendation — **nothing implemented without a reviewer verdict**. |
| Questions | 15 questions: what we know / what is missing / how to find out; unknown answers left blank. |
| Site | 16-page static dashboard; every data row source-linked and machine-checked (433 rows, 714 links, 0 broken). |

## Headline findings (honest)

1. **Signal (price-independent):** S1 "model side" walk-forward accuracy **0.673** (n=104, 95% CI 0.578–0.756) beats the pre-registered 0.500 baseline (G2 **pass**), beats always-home (0.481), and edges the post-hoc better-record baseline (0.635, +3.8pp — not pre-registered, disclosed as amendment A2). Placebo test: 0 of 500 random strategies reached its assumed-price ROI (p < 0.002).
2. **Staking (assumed price):** S1 ROI **+0.285 at −110** (CI 0.112–0.458) — **not an achievable market return** (FB-02: no market prices favorites at −110). S2 total calibration: negative ROI, model MAE (21.6) worse than the constant-mean baseline (11.1) — fails its gates (FB-13). S3 mirror strategy loses at the assumed price. S4 parlay: n=7, fails sample-size gate.
3. **Rewards: 0 of 1,000 points.** Amendment A1 requires verified prices (G7) before any points; G7 is permanently blocked without an official price source. A lucky staking run therefore cannot pay anyone, and a bad signal cannot be masked by staking luck — the ranking key itself is signal-first.
4. **Model:** stacked least-squares ratings on official results only; fitted HFA **+0.15 pts** (far below historical norm — FB-12, Q11); σ(margin) 10.45; no QB/injury/depth features (FB-11).
5. **Correlations:** same-week consecutive-game home-win dependence r = −0.040 (n=125) — independence not rejected, so cross-game parlay legs may be multiplied; rest-day differential vs margin r = 0.426 (n=121, dates partly peer-transcribed FB-04); points-allowed vs wins r = −0.581 (n=32).

## What is blocked (never inferred)

- Market lines / open-close prices / differences → **blank**, FB-01, decision SG-01.
- Player-prop strategy S5 → **blocked**, FB-05 (no official prop prices).
- Depth strings beyond official prose → **blank**, FB-07 (no official depth chart).
- Historical injury effects → **blank**, FB-06 (no archived reports; start archiving: SG-07).
- 105 of 137 feed rows are aggregate-verified only → FB-03 (full re-read proposed: SG-02).

## Decisions awaiting a reviewer

Open the **Suggestions** page and pick a path (A/B/C) for SG-01…SG-13 — the top three are SG-01 (price source), SG-02 (finish the line-by-line re-read), SG-08 (choose one canonical dashboard among 17 namespaces). The **Questions** page lists the 15 questions that must be answered before those decisions can be made well.

## Verification performed this session

- Official pages fetched and read: nfl.com standings (32 clubs, 2 chunks), Week 1 scores (16 finals), Week 9 scores (15 finals), Week 10 scores + TNF game page (24–21), Week 11 schedule (13 games, 6 byes), official Week 10 injury report (2 chunks, 107 rows), two official news articles for replacement depth.
- Checks: V-01 line-by-line 32/32 match · V-02 aggregates 160/160 · V-03 identities (ΣW=ΣL, ΣPF=ΣPA, decisions = 2×games) — all pass.
- Site verifier: 16 pages, 433 rows, 409 sourced + 24 meta-exempt, 202 marked blanks, 714 links, 0 broken, PASS.
- Pre-registration: `data/strategies.json` + `data/gates.json` committed (git `f4465c0`) **before** the first backtest run.

## Irregularities

17 flags FB-01…FB-17 are published on [Flagged for Review](pages/flagged.html) with source links; none block publication.

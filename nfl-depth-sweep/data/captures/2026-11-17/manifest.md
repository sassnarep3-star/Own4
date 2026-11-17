# Depth-chart sweep manifest — 2026-11-17 (session arena/2388d73a-own4)

Route probed for all 32 clubs: `https://www.<club>.com/team/depth-chart` (alternate confirmed domains used where the short form failed). Every raw transcript in `data/raw/*.md` is a verbatim machine-readable text capture with URL + fetch date in the header. No cell was inferred.

## Sweep outcome (32/32 clubs attempted)

- **verified_text — 31 clubs** (raw transcript in `data/raw/`):
  ATL, ARI, BAL, BUF, CAR, CHI, CIN, CLE, DAL, DEN, DET, GB, IND, JAX, KC, LAC, LAR, LV, MIA, MIN, NE, NO, NYG, NYJ, PHI, PIT, SEA, SF, TB, TEN, WAS
- **flagged_image_only — 1 club**: HOU — `houstontexans.com/team/depth-chart` renders the chart as a static image only (`static.clubs.nfl.com/image/upload/texans/a5or0zowuo36y1txf4ly`); no text table, no player links. Flagged unverified; do not transcribe by eye.

## Domain corrections (confirmed official domains)

| Club | Confirmed domain | Rejected / failing surface |
|---|---|---|
| ATL | atlantafalcons.com | falcons.com (unrelated shop, 404) |
| ARI | azcardinals.com | cardinals.com (MLB St. Louis) |
| BAL | baltimoreravens.com | ravens.com (HTTP 500, 3 attempts) |
| BUF | buffalobills.com | bills.com (personal-finance site, 404) |
| CHI | chicagobears.com | bears.com (HTTP 500) |
| DAL | dallascowboys.com | cowboys.com (HTTP 500, 2 attempts) |
| DEN | denverbroncos.com | www variant geo-blocked once; bare host succeeded |
| DET | detroitlions.com | detroitlions.com (HTTP 500 on first attempt; succeeded on retry) |
| HOU | houstontexans.com | depth published as image (route itself returns page, no text) |
| LAR | therams.com | rams.com (HTTP 500) |
| MIA | miamidolphins.com | dolphins.com (not the official surface) |
| NO | neworleanssaints.com | saints.com (HTTP 500 on first attempt; succeeded on retry) |
| NYJ | newyorkjets.com | jets.com (not the official surface) |
| PHI | philadelphiaeagles.com | eagles.com (shopify shop, 404) |
| PIT | steelers.com | (trailing-slash route) |
| TEN | tennesseetitans.com | titans.com (HTTP 500, 2 attempts) |
| CLE | clevelandbrowns.com | browns.com (not the official surface) |

## Cross-club irregularities observed (flagged, not transcribed as authoritative)

1. **LAC stale-depth**: Derwin James Jr. listed S rank1 while the page's own Latest Transactions block places him on IR.
2. **NE disclaimer**: "The 2026 depth chart is unofficial and is published by the writers of Patriots.com ... reflect the opinions of the Patriots.com writers" — writer-opinion chart, not an org communication.
3. **Shared rank slots** (VR-21): SEA WR1; CIN TE2/DT2; PIT TE1; JAX RB1/LB2; LV WR3; MIN RB1; ARI OLB1; DAL TE1/LB1/S1; LAR TE1/CB1; NO RB1/EDGE1; TEN TE3/RB2/RB3; PHI EDGE1/EDGE2.
4. **Sparse/blank cells**: MIA QB1-only, BAL K blank, PHI several blank rank1 cells (WR1, LT, LG, RT, RB1, DT3), NYJ DL2 blank, NE 4-deep LT.
5. **Dated snapshots**: IND publishes weekly charts; LV chart dated "November 10, 2026 | Week 10"; CHI dated "As of 10/31/2026"; TEN dated "as of 11/10/26". Every capture is a dated snapshot — fetch date recorded per transcript.
6. **BAL 2026 snapshot**: QB row lists Jacoby Brissett (1) — Lamar Jackson (the brief's stale-depth case) does not appear in this 2026-11-17 capture.
7. **Naming variance across clubs**: OLB/ILB (PIT, NE), EDGE/DL (DET, NO, NYJ, PHI), DL-heavy front (CHI), SLB/WLB/ILB/LCB/RCB/NCB (DEN), DT/NT/DE/RUSH/MLB/WLB/SAM/DB/SS/FS (BAL), DE/DL/NT/OLB/ILB (TB/ARI), NB nickel slots (ATL, NYJ, TEN), split S rows (CAR, TB, MIN, NO, DEN, NE).

## Files

- Raw transcripts: `nfl-depth-sweep/data/raw/{club}.md` (31 text + HOU flag file)
- Domain map: `nfl-depth-sweep/data/teams.json` (32 clubs, status per club)
- Manifest: `nfl-depth-sweep/data/captures/2026-11-17/manifest.md` (this file)

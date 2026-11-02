# Requirements traceability

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| REQ-01 | Collect, organize and analyze NBA data | delimited pilot | 62 official final scores and 38 official player rows; not a complete league database. |
| REQ-02 | Originate own NBA lines | implemented | 39 historical validation/test fair spreads, totals and moneylines; explicitly not sportsbook quotes or current picks. |
| REQ-03 | Research useful signals | implemented; no edge established | Eight preregistered-for-this-pilot hypotheses; locked test underperformed the probability baseline. |
| REQ-04 | Single bets | implemented | Moneyline, spread and total hypotheses with official-price abstention. |
| REQ-05 | Parlays | research only | Cross-game disjoint-team examples and same-game joint residual experiment; no official ticket prices. |
| REQ-06 | Player prop combinations | research only | Points/rebounds, points/assists and PRA cohort thresholds; no personalized player forecasts. |
| REQ-07 | Every strategy passes validation gates before release | enforced; none qualified | Ten fail-closed gates; missing evidence never counts as a pass. |
| REQ-08 | Determine correlation values | descriptive estimates | Game-level and minutes-residualized player correlations; confidence intervals suppressed for too few clusters. |
| REQ-09 | Remove luck and identify skill | cannot guarantee | Leakage controls, matched baseline, date-cluster policy, multiple-testing gate and prospective replication. Randomness cannot be eliminated. |
| REQ-10 | Leaderboard competition with rewards | implemented; zero awards | Diagnostic probability ranking is separate from betting eligibility. 1,000 non-monetary points remain unawarded. |
| REQ-11 | Executive summary | delivered | Executive summary page and Markdown document state findings and limitations. |
| REQ-12 | No manual user input | delivered | Research, code, data checks, site generation and publication run without user-supplied credentials or choices. |
| REQ-13 | Review repo line by line | mechanical scan + targeted primary checks | Every tracked text line scanned; not every inherited fact independently re-fetched. Distinction published in audit. |
| REQ-14 | Official source on every table row | enforced in this workspace | Static HTML source-column check; derived rows link to official input sources and expose formulas. |
| REQ-15 | Unconfirmed values blank and flagged | enforced | Null market prices, ROI, personalized props and unsupported intervals; Flagged for Review page. |
| REQ-16 | Clean landing page and category subpages | delivered | Responsive static dashboard with search, grouped navigation, source links and downloadable data. |
| REQ-17 | Coordinate parallel sessions | delivered with platform deviation | Claims, append-only logs, preserved peer namespaces and conflict records. Fixed Arena branch overrides requested branch naming. |
| REQ-18 | Final integration and no broken links | delivered | 17 pages; 1,041 table rows with source links; 351 local links checked; 22 unit tests and 57 evidence checks pass. |
| REQ-19 | PR, merge and GitHub Pages deployment | pending publication | Will record actual PR, merge commit and deployment result; never predeclare success. |
| REQ-20 | Flagged items do not block publication | implemented | Needs-review findings are published separately from strategy qualification; they still block unsupported claims. |

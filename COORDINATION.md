# Coordination board

Session ID: `34832d14-own4` (Arena-managed branch `arena/34832d14-own4`). Repository was an empty README at start; no other claims were present. The Arena branch is fixed for this session, so the requested `session-<id>/<task>` branch pattern cannot be used.

| Task | Status | Owner | File scope | Updated (UTC) |
|---|---|---|---|---|
| Research, verification, strategy design, dashboard, QA and integration | done | 34832d14-own4 | `README.md`, `COORDINATION.md`, `index.html`, `.nojekyll`, `docs/**`, `scripts/**`, `.github/**`, `package.json` | 2026-11-02 |

## Handoff / conflicts

- No other task claims or concurrent edits observed at claim time. Shared outputs are owned by this single integration session.

## Verification log

- Pending research and implementation. No empirical NBA correlations, odds, performance rankings or line values have yet been verified.

## Research and implementation review (2026-11-02 UTC)

- Official sources directly opened: [NBA games](https://www.nba.com/games), [Stats glossary](https://www.nba.com/stats/help/glossary), [Stats FAQ](https://www.nba.com/stats/help/faq), [team advanced stats](https://www.nba.com/stats/teams/advanced), [player traditional stats](https://www.nba.com/stats/players/traditional), [player box scores](https://www.nba.com/stats/players/boxscores-traditional), [lineup traditional stats](https://www.nba.com/stats/lineups/traditional), [betting partnership release](https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners), [responsible gaming release](https://pr.nba.com/nba-wnba-responsible-gaming-campaign).
- Irregularity: [NBA-issued 2026-10-30 injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-30_07_00PM.pdf) appeared in official-domain search excerpts but direct retrieval failed. Historical report is not a current availability feed. See site flag F03.
- Rights restriction: the [NBA Stats FAQ](https://www.nba.com/stats/help/faq) says no stats download for academic or personal use. No scraper, stat exports, odds archive, or fabricated empirical values were added. See F01, F02, F04–F06 on the Flagged for Review page.
- Row-by-row checks: each of 8 strategies, 9 gates, 5 correlation pairs, 6 flags, 8 requirements and 10 source rows links an NBA-owned source. Source links verify input definitions/context, not original proposed model efficacy. All empirical estimate fields remain blank. Static local link and catalog tests: `npm test` passed.
- User-requested session branches cannot be created because Arena requires work on `arena/34832d14-own4`. No other claims or edits observed.

- Publishing setup: Pages is already configured to build from `main` root (legacy mode). Attempting to switch to Actions via the Pages API returned HTTP 403 (integration permission); preserved the existing deployment mode, added a root redirect to `docs/index.html`, and kept Actions for CI only. This configuration change is recorded as an irregularity, not an empirical data issue.

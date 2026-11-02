# NBA Signal Lab

[Open the dashboard](https://sassnarep3-star.github.io/Own4/) · [Flagged for Review](https://sassnarep3-star.github.io/Own4/flagged.html)

## Executive summary

This is an **evidence-first research dashboard**, not a live betting product. Eight original candidate signal families cover singles, parlays and player-prop combinations. Nine proposed universal release gates require authorized data, pregame snapshots, executable market quotes, calibrated chronological holdouts, verified dependence, prospective logging and bounded risk. **No candidate currently passes**: verified line values, correlation coefficients, performance results and leaderboard ranks are deliberately blank. Randomness cannot be removed from sports outcomes; skill would require reproducible out-of-sample improvement over a comparable market baseline.

The official [NBA Stats FAQ](https://www.nba.com/stats/help/faq) explicitly says its stats are not available for download, including for academic or personal use. We therefore do **not** scrape or package NBA statistics. A publicly browsable NBA stats page is not proof of automated reuse rights. The [NBA betting-partner release](https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners) does not provide a licensed odds archive, executable quotes or market settlement rules. These gaps block automatic origination and credible edge claims without requiring user-supplied inputs. The site publishes research and limitations instead of inventing data.

The [NBA responsible gaming release](https://pr.nba.com/nba-wnba-responsible-gaming-campaign) says betting puts money at risk and should be entertainment, not an effort to generate income. Nothing here is wagering advice or a promise of reward.

## Pages

- [Overview](docs/index.html) — executive summary and requirement inventory
- [Strategies](docs/strategies.html) — candidate signals and missing inputs
- [Validation gates](docs/validation.html) — release rules and leaderboard protocol
- [Correlations](docs/correlations.html) — planned dependence tests; blank estimates
- [Official sources](docs/sources.html) — NBA-owned evidence register
- [Flagged for Review](docs/flagged.html) — unresolved rights, odds and verification issues

## Verification and QA

`npm test` checks catalog JSON, NBA-owned HTTPS source links on every table row, unfilled empirical cells, math primitives and local page links. It does **not** claim to prove model skill or live source availability. Pure functions in `docs/assets/engine.mjs` are tested on synthetic vectors only; no synthetic value is published as NBA evidence. The site is static, needs no account or manual entry, and is served from `docs/` using the repository’s existing GitHub Pages legacy `main`/root configuration (the root index redirects to `docs/index.html`); GitHub Actions runs the verification suite. Source links and findings were reviewed against official NBA pages on 2026-11-02; the linked historical injury PDF appeared in search results but direct PDF retrieval failed, as recorded in the flag log.

Research design is ours; source links substantiate NBA definitions, data availability and risk context, **not** the proposed strategies' predictive power.

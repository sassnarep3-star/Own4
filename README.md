# NBA Line Lab

A transparent, research-first framework for originating and evaluating NBA betting lines. The site separates sourced NBA facts from proposed modeling methods; it publishes no live picks, odds, performance claims, or correlations without verifiable data.

## Browse

- [Executive dashboard](index.html)
- [Methods and strategy leaderboard](pages/strategies.html)
- [Validation gates and correlation](pages/validation.html)
- [Sources and flagged items](pages/review.html)

## Important scope

This repository is a research framework, not a sportsbook, betting recommendation, or claim of profitable performance. No historical odds, line snapshots, graded bets, or player-level training dataset are included. Consequently there are no estimated coefficients, correlation values, win rates, ROI, or leaderboard winners to report. Such values remain blank until auditable, timestamped data are collected and evaluated out of sample. Betting involves risk; never risk money you cannot afford to lose.

Every published factual row links to an official NBA source. Framework proposals are explicitly labeled as proposals rather than NBA facts.

## Local preview

Open `index.html` directly, or run `python3 -m http.server 8000` from the repository root.

## Publication

GitHub Pages is configured through the repository's GitHub Actions workflow. The workflow publishes the repository root when changes land on the default branch. Repository administrators may need to enable Pages with **GitHub Actions** as the source in Settings → Pages.

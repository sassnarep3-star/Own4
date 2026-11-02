# NBA Line Lab

A source-first NBA betting-line **research framework**, not betting advice or a validated edge. See the [executive summary](research/EXECUTIVE_SUMMARY.md), [coordination log](COORDINATION.md), and [dashboard](site/index.html).

Run `python scripts/check.py` to verify internal page/assets and source references. Serve `site/` over HTTP to view the dashboard (browser `fetch` does not work reliably from `file://`). The GitHub Actions workflow validates pull requests; the repository’s existing legacy GitHub Pages configuration publishes `main` at the repository root, where `index.html` redirects to `site/index.html`.

No market odds, historical results, bet recommendations, correlation estimates, leaderboards or actual reward distribution have been created. Missing evidence is shown explicitly on the Flagged for Review page.

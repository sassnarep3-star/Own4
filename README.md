# Own4 — NBA Line Origination & Signal Strategy Research

Leaderboard-style research framework for originating NBA lines from verifiable signals (single bets, parlays, player-prop combos), with validation gates, correlation controls, and luck-removal rules. All data rows cite official sources; unverifiable values are blank and flagged.

- Live site: GitHub Pages (see repo Settings → Pages)
- Executive summary: [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- Task board: [COORDINATION.md](COORDINATION.md)
- Rebuild site: `python3 build_site.py`

Research framework only — not wagering advice. Helpline: 1-800-GAMBLER (ncpgambling.org).


---
## Additional research workspace · arena-1805bfdb

# Own4 · NBA Signal Lab

Evidence-first NBA strategy research dashboard. **No validated strategies, trained pricing model, empirical correlations, live odds, betting execution or funded rewards exist in this release.** Missing results remain blank.

## Executive summary
Start with authorized point-in-time data and calibrated single-market baselines. Progress to player combinations and parlays only with tested joint distributions. Six proposed hypotheses must pass eight validation gates before leaderboard eligibility. Luck cannot be eliminated; prospective replication, locked holdouts and dependence-aware uncertainty are needed to distinguish evidence of skill from favorable variance.

- [Live dashboard](https://sassnarep3-star.github.io/Own4/docs/)
- [Executive summary](docs/index.html)
- [Flagged for Review](docs/review.html)
- [Source register](docs/sources.html)
- [Coordination and publication log](COORDINATION.md)

## Reproduce
Python 3.12, standard library only. Run `python scripts/build.py` then `python -m unittest discover -s tests -v`. Serve locally with `python -m http.server 8000 --bind 0.0.0.0 --directory docs`. Eight static category pages require no JavaScript or credentials. JSON research export is in `docs/data/research.json`; `scripts/build.py` is the canonical content source. GitHub Actions validates every PR and validates `docs/`; existing legacy Pages publishes it under `/docs/`.

## Audit and verification boundaries
Initial checkout contained only a six-byte README, no existing code or dataset. Official NBA glossary, FAQ and current injury report plus NIST and scikit-learn official documentation were read on 2026-11-02. Every published table row links to an official source. Design rows are explicitly proposals; their sources provide definitions/method context, not verification of effectiveness. Unavailable numeric values are blank. All generated rows reviewed for this distinction; tests check source coverage, allowed official domains, local navigation and blank metrics. Tests do not establish external source truth or certify profitability.

The NBA FAQ says statistics are not available for personal/academic download. No scraping, unofficial feeds or invented NBA observations were used. No automatic external data collection is claimed. Sources are dynamic; revalidation is necessary before any future use. See review page for all limitations.

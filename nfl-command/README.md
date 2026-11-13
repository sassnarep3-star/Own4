# nfl-command — NFL line origination & decision research (2026-11-13)

Live: https://sassnarep3-star.github.io/Own4/nfl-command/ · built entirely from official NFL sources
captured 2026-11-13. Every table row on the site links its official source; unverifiable values are blank
and listed on the Flagged for Review page.

## Layout
- `data/` — captured & derived datasets (standings, slates, injuries, passing, verified games, own lines,
  strategies, gates, correlations, leaderboard, questions, suggestions, flags, repo review, sources).
- `engine/run.py` — ratings, own lines, walk-forward backtest, placebo/bootstrap luck tests, correlations,
  leaderboard grading. Deterministic (seed 20261113), stdlib only.
- `engine/build_site.py` — generates `index.html` + `pages/*.html` from `data/`.
- `engine/verify_site.py` — fails on any table row without an https source link or any broken internal link.

## Reproduce
```
python3 nfl-command/engine/run.py        # recompute derived data
python3 nfl-command/engine/build_site.py # rebuild the site
python3 nfl-command/engine/verify_site.py
```

## Verification chain (2026-11-13)
- Standings identities 32/32; passer-rating identity 32/32.
- 137-game archive reproduces official W-L-T/PF/PA for all 32 clubs (0 mismatches; league PF = PA = 6,291).
- 3 official game-page spot checks exact; W10 final read directly from the official week page.
- Site verifier: 17 pages, 762 table rows, 762 sourced, 0 broken links.

## Policy
Never infer. Market prices, player-prop prices, and depth-chart string designations do not exist in any
official source reachable by this project, so they are blank and flagged (F-01, F-02, F-08) — never
proxied. Gates were committed to git before the backtest ran (commit 773cc28).

Research only — not wagering advice. NCPG Helpline: 1-800-MY-RESET (https://www.ncpgambling.org/help-treatment).

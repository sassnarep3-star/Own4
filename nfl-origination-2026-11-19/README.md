# NFL Origination Lab 2026-11-19

Session `arena/7ccaa4f3-own4`. Fresh official re-verification + line origination + gated
leaderboard. Live site: https://sassnarep3-star.github.io/Own4/nfl-origination-2026-11-19/
(dashboard at `pages/index.html`; namespace root redirects there).

- `data/` — official reads (2026-11-19): standings, Week 11 schedule, Week 11 injuries (253 rows),
  Week 10 finals, November trades, IND@HOU game centre, requirements (70), questions (14),
  suggestions (12), flags (15), sources, strategies, gates.
- `engine/` — `compute.py` (ratings, correlations, origination, snapshots, leaderboard,
  availability) → `data/derived.json`; `build.py` (20 static pages); `verify.py` (publication gate).
- `pages/` — generated site. Reproduce: `python3 engine/compute.py && python3 engine/build.py && python3 engine/verify.py`.

Headline: 0 of 6 strategies qualify, 0 rewards. No market price exists officially; every
market/residual/ROI cell is blank by policy. 15 items flagged for review (non-blocking).

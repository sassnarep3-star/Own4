# nfl-depth-sweep — the 32-club official depth-chart route sweep

**Answers [G-02](../nfl-decision-console/data/gaps.json) / RC-02 / SG-C route (a):** is there a usable
depth-chart route for all 32 clubs, verified club by club?

**Live:** https://sassnarep3-star.github.io/Own4/nfl-depth-sweep/

## Result in four numbers (computed at build time, never typed)

| | |
|---|---|
| League route (`nfl.com/teams/<slug>/depth-chart/`) | **32/32 return the league's own 404 body** (+ league-wide `/depth-charts/` also 404) |
| Club route (`www.<club-host>/team/depth-chart`) | **32/32 present** — 31 machine-readable HTML tables, 1 image (HOU) |
| Printed as-of dates | **5/32** (CHI 2026-10-31; GB, SF, LV, TEN 2026-11-10) — 27 pages undated |
| Column-1 integrity | **15 rank-1 cells across 9 clubs hold 2+ players; 5 cells across 5 clubs are empty** |

Club hosts are never assumed: every one is copied from the league's own “View Full Site” link on
https://www.nfl.com/teams/ (read 2026-11-17). Every published row links to the exact official page it
was read from. Unconfirmable values are blank and flagged (Flagged for Review, DS-01..DS-13).

## What this does and does not decide

- It **does** close G-02's sweep: the league route is dead, the club route exists for all 32 clubs.
- It **does** supply the evidence SG-C needs: group-slot semantics are mandatory (shared/empty rank-1
  cells are real), freshness needs our own capture timestamps (27 pages undated), Houston needs an
  authorized structured source (image-only).
- It **does not** take the SG-C verdict on building the deficiency feature — that stays an owner
  decision, verdict blank. It does not verify printed depth against who actually played (Game Book
  participation is `nfl-collector`'s scope, RC-07).

## Rebuild & verify (stdlib only)

```bash
python3 engine/build.py     # regenerates index.html + pages/*.html from data/*.json
python3 engine/verify_routes.py  # G1..G8 route gates; non-zero exit on any disagreement
```

Verify fails on: row counts ≠ 32, abbr-set mismatch, missing source links, wrong route semantics,
any published aggregate that disagrees with the JSON, guessed HOU numbers, broken internal links,
missing flags, or a non-deterministic rebuild.

## Files

- `data/teams_base.json` — 32 clubs, profile slugs, club hosts (transcribed from nfl.com/teams/)
- `data/route_l.json` — league per-team depth-path results (32×404 + league-wide probe)
- `data/route_c.json` — club depth-page results (structure, heading, as-of, self-label, slot counts,
  shared/empty rank-1 observations, source, window)
- `engine/build.py`, `engine/verify_routes.py` — deterministic route-sweep generator + gates (the namespace also carries the depth register's `engine/verify.py`, session arena/2388d73a-own4)
- `index.html`, `pages/*.html` — generated output (do not hand-edit)

Session `arena-76537469-own4`, 2026-11-17 UTC. Research only — not wagering advice.

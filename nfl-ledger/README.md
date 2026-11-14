# nfl-ledger — NFL gap-closure namespace (session `arena/6f0b80b2-own4`, 2026-11-14)

Live (after the PR is merged to `main`, Pages legacy root): https://sassnarep3-star.github.io/Own4/nfl-ledger/

Adds what the NFL brief required and the peer namespaces did not have: a price-snapshot store, a results feed
with a standings reconciliation, origination order (side → total → moneyline) with fair / market / difference
columns, a signal-vs-staking leaderboard split, a demotion gate, replacement-depth fields, correlations with n,
questions, suggestions (nothing implemented), flags and an executive summary.

## Layout
- `data/` — derived tables (JSON and CSV). `price_snapshots.csv` is intentionally empty (see F-L1).
- `engine/build.py` — builds data and pages. Reads `nfl-command/data/` read-only. Stdlib only.
- `engine/render.py` — static HTML.
- `engine/demotion.py` — demotion and promotion rules as pure functions.
- `engine/verify.py` — checks every table row for a source link, local links, blank market values and reconciliation.
- `tests/test_demotion.py` — 13 unit tests on synthetic inputs (no published data).

## Reproduce
```
python3 nfl-ledger/engine/build.py
python3 nfl-ledger/engine/verify.py
python3 -m unittest discover -s nfl-ledger/tests -v
```

## Policy
A value is shown only when it comes from an official nfl.com capture or is a computation from one. Market prices are
never shown, because no official source publishes them. Missing values stay blank and are flagged, never zero and
never inferred. Analytical research only — not wagering advice. Problem gambling help: 1-800-MY-RESET
(https://www.ncpgambling.org/help-treatment).

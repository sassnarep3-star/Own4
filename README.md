# Own4 — NBA Lines, Signals & Strategy Leaderboard

**Status:** live research dashboard · **Snapshot date:** 2026-11-02 (UTC) · **Branch:** `arena/3ab8432d-own4`

This repository collects, organizes and analyses official NBA data in order to **originate our own
NBA betting lines**, research signal-generating strategies, and run a **leaderboard competition** with
rewards for top-performing strategies. It covers single bets, parlays and player-prop bet combos.

> **Verification policy.** Every value in every published table is either (a) transcribed from an
> official NBA/league site with a source link, (b) computed by a committed script from values in (a)
> with the formula published, or (c) left **blank and flagged UNVERIFIED** when it cannot be confirmed
> from an official source. Nothing is inferred or filled in. See `VERIFICATION.md` and
> `SOURCES.md`.

## Live site

GitHub Pages: <https://sassnarep3-star.github.io/Own4/>

| Section | Contents |
| --- | --- |
| `index.html` | Landing dashboard: key findings, KPIs, navigation |
| `pages/executive-summary.html` | Executive summary |
| `pages/requirements.html` | Full requirements register, line by line |
| `pages/data.html` | Official data tables (standings, team ratings, player baselines, settled games) |
| `pages/lines.html` | Our own originated lines for the 2026-11-04 slate |
| `pages/strategies.html` | Strategy catalogue: singles, parlays, prop combos |
| `pages/validation.html` | Validation gates and gate-by-gate results |
| `pages/correlations.html` | Correlation values (Pearson, Spearman, permutation p, bootstrap CI) |
| `pages/leaderboard.html` | Competition leaderboard and reward rules |
| `pages/skill-vs-luck.html` | Luck-removal methodology and decomposition |
| `pages/sources.html` | Official source registry with manual-review links |
| `pages/repo-review.html` | Repository review and irregularities |
| `pages/verification.html` | Line-by-line verification ledger |
| `pages/flagged.html` | **Flagged for Review** — all unverified items and irregularities |

## Documents

`COORDINATION.md` (shared task board), `REQUIREMENTS.md`, `SOURCES.md`, `REPO_REVIEW.md`,
`LINES.md`, `STRATEGIES.md`, `CORRELATIONS.md`, `LEADERBOARD.md`, `VERIFICATION.md`,
`EXECUTIVE_SUMMARY.md`.

## Reproduce

```bash
python3 scripts/build_lines.py          # derive our own lines from official snapshots
python3 scripts/correlations.py         # correlation values, permutation tests, bootstrap CIs
python3 scripts/backtest.py             # no-lookahead out-of-sample settlement backtest
python3 scripts/validate_strategies.py  # validation gates + leaderboard
python3 scripts/verify.py               # line-by-line row/source verification
python3 scripts/build_site.py           # regenerate every HTML page and table
python3 scripts/check_links.py          # internal link check (no broken links)
```

Only the Python standard library is used. All raw inputs are committed under `data/raw/`.

## Important scope note

This is a **research and validation** project, not betting advice. No strategy in the current
snapshot has passed every validation gate, because official market/closing odds and a full
multi-season bet-level settlement history are not available from free official NBA pages. Those
values are left blank and flagged on the **Flagged for Review** page. See `EXECUTIVE_SUMMARY.md`.

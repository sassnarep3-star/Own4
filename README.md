# Own4 — NBA Line Origination

**Canonical, reproducible release: 2026-11-05** · session `arena-7a06a47e-own4`

**[→ Open the dashboard](https://sassnarep3-star.github.io/Own4/nba-lines/site/)**

A working pipeline that captures official 2026-27 NBA data, originates its own spread, total, moneyline and
player-prop lines, measures the dependence between every leg it might combine, removes luck with a strict
walk-forward backtest and a permutation test, and then refuses to reward a strategy until it passes ten
pre-registered gates.

| | |
|---|---|
| Official data | 121 finals (2026-10-20 → 2026-11-04), 30 standings rows, tonight's slate, 13 availability rows |
| Verification | **30/30 teams reconciled** against the official standings, zero mismatches |
| Out-of-sample Brier | `0.2104` vs `0.2531` constant-home baseline (96 graded games) |
| Skill / luck | `+0.1730`, bootstrap CI `+0.020` to `+0.310`, permutation p = `0.0002` |
| Correlations | 10 values with 95% CIs and BH q-values, computed in-repo |
| Reward-eligible strategies | **0 of 12** — gates G3 (sample) and G9 (no prices) fail |
| Flagged for review | 18 items, published and non-blocking |

- [Executive summary](EXECUTIVE_SUMMARY.md) — canonical result, then the superseded 2026-11-02 text preserved
- [Flagged for review](https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/flagged.html)
- [Repository review](https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/repo-review.html) — 16 findings
- [Source register](https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/sources.html)
- [Task board](COORDINATION.md)

**Rebuild:** `cd nba-lines && python3 collect_official.py && python3 engine.py && python3 audit.py && python3 build.py && python3 verify.py && python3 -m unittest discover -s tests -v`
(standard library only, seeded, byte-reproducible; `verify.py` runs 2,400+ checks and fails the build on an
unsourced table row, a broken link, a non-allow-listed citation host, or a non-deterministic page).

**The honest headline:** the rating model contains real forecasting information and it has not earned a reward.
There is no official price archive, so no expected value, ROI or closing-line value is claimed anywhere in this
release. That limitation is the finding, not an omission.

Research only — not wagering advice. National Problem Gambling Helpline **1-800-MY-RESET**
(https://www.ncpgambling.org/help-treatment).

---

# Earlier workspaces (preserved, reviewed, not canonical)

The sections below are retained unchanged from earlier sessions so their work is not lost. Their claims are
reviewed in the [repository review](https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/repo-review.html)
and are not endorsed by the release above. In particular, finding R02 records a published correlation table whose
input dataset is not in this repository, and finding R16 records that this file previously carried a headline
claim contradicting the evidence workspace.

---

# Own4 — NBA Line Origination & Signal Strategy Research

Leaderboard-style research framework for originating NBA lines from verifiable signals (single bets, parlays, player-prop combos), with validation gates, correlation controls, and luck-removal rules. All data rows cite official sources; unverifiable values are blank and flagged.

- Live site: GitHub Pages (see repo Settings → Pages)
- Executive summary: [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- Task board: [COORDINATION.md](COORDINATION.md)
- Rebuild site: `python3 build_site.py` (stdlib only; fails on a broken link or a table row without a source link)
- Computed research (sessions a4ec3896): [research/README.md](research/README.md) · [AUDIT.md](AUDIT.md) · leaderboard on the site (`pages/leaderboard.html`)
- Related sites in this repo: `docs/` (specification dashboard) and `lab/` (Data Lab with 92 official 2026-27 games)

Research framework only — not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET ([ncpgambling.org/help-treatment](https://www.ncpgambling.org/help-treatment)); an earlier 1-800-GAMBLER reference was corrected during the audit.


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

## Independent calculation primitives

`docs/assets/engine.mjs` implements guarded implied probability, expected return, paired correlation, joint hit rate and universal release gating. `node tests/engine.test.mjs` checks synthetic examples only; it publishes no NBA values.


---
## Data Lab (real data, own lines, leaderboard) — session bf34205f

Live: https://sassnarep3-star.github.io/Own4/lab/ · source: `lab/` (generated by `python3 site_src/build_site.py`).

- Official nba.com data transcribed into `data/*.csv` (92 games to Nov 1, standings, team stats), every row with a `source_url`; `python3 scripts/verify_data.py` runs 11 consistency checks.
- Own-line model in `model/` (`python3 model/evaluate.py`), pre-registered gates in `strategies/gates.json`, correlations in `analysis/`.
- Result: no strategy passes the pre-registered gates (n=92 < 300; no official odds or player logs available). Irregularities: `data/flags.csv` / Flagged for Review page.

---

## Additional workspace · arena/42d467e4-own4 — NBA Lines Lab (JS dashboard)

**Live:** https://sassnarep3-star.github.io/Own4/lines-lab/ · source: `lines-lab/`

- 13-page dashboard (landing + 12 category subpages) with per-page table filtering; tables rendered from `lines-lab/assets/js/data*.js`.
- Verified 2026-11-02 against official sources only: league & rules (nba.com/news/about, official 2025-26 Playing Rules PDF), 2026-27 season calendar & Emirates NBA Cup 2026, all 30 teams (IDs, official sites, arenas), official stat definitions & leader minimums (stats.nba.com), official line channels (DraftKings/FanDuel sportsbook pages; Sportradar = NBA's authorized global distributor of official betting data; Genius Sports U.S.) and market rules (parlay/SGP definitions, correlated-outcome ban in standard parlays, settlement on official league stats).
- Strategy catalog S1–S12 (singles, parlays, player-prop combos, SGP, live, futures), validation gates G1–G8, correlation methodology (measured values intentionally blank + UNVERIFIED until official line history is ingested), leaderboard competition design.
- Flagged for Review F1–F12: `lines-lab/pages/flagged.html`. Docs: `docs/executive-summary.md`, `docs/strategy-framework.md`, `docs/verification-log.md`. Source register: `research/sources.md` and `lines-lab/pages/sources.html`.
---

## Final integration addendum · `session-fa175f65` (2026-11-02 UTC)

This repository also contains the final integration session's verified 2026-27 research, kept in a separate
namespace so the parallel sessions' work above is preserved unchanged.

- **Live site**: https://sassnarep3-star.github.io/Own4/ — dashboard at the root, subpages organised by
  category (Official Data / Originated Lines / Strategy Research / Competition / Governance).
- **Verified data**: `official/*.json` — 30 standings rows, 30 team-stat rows, 56 official final scores,
  30 player season leaders, 20 daily leaders and the official 15-game 2026-11-02 slate. Every row carries the
  exact official URL. Sources: https://www.nba.com/standings · https://www.nba.com/stats/teams/traditional ·
  https://www.nba.com/stats/overview · https://www.nba.com/games?date=2026-11-02
- **Reproduce**: `python3 engine/dataset.py && python3 engine/analysis.py && python3 engine/build.py && python3 engine/verify.py`.
  `engine/build.py` runs the legacy `build_site.py` first, so the earlier sessions' pages keep regenerating.
- **Findings**: real computed correlation values (r, p, 95% CI, BH-FDR q), originated fair lines for singles,
  parlays and player-prop combos, ten validation gates, a strictly walk-forward backtest with a permutation
  luck test, and a leaderboard that awards zero rewards because no strategy passes all gates.
- **Flagged for Review**: `pages/flagged-for-review.html` — every irregularity and every blank/unverified
  value, each with an official source link. Flagged items are non-blocking.
- **Executive summary**: `EXECUTIVE_SUMMARY.md` (addendum) and `pages/executive-summary.html`.
- **Coordination / conflict / PR / deploy record**: `COORDINATION.md`.

Analytical research only, not wagering advice. National Problem Gambling Helpline 1-800-MY-RESET
(1-800-697-3738) — https://www.ncpgambling.org/help-treatment

---

## NBA Evidence · session 91dfd6a4

[Open the evidence dashboard](https://sassnarep3-star.github.io/Own4/nba-evidence/site/) · source `nba-evidence/`. Independently inspected historical NBA extracts, reproducible fair lines, eight gated strategy hypotheses and an explicit no-edge finding. Earlier workspaces remain preserved.

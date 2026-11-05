# nba-lines — canonical NBA line-origination workspace

Session `arena-7a06a47e-own4`, 2026-11-05. Standard library only, no network access, fully seeded.

**Live site:** https://sassnarep3-star.github.io/Own4/nba-lines/site/
**Executive summary:** [../EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md)
**Flagged for review:** https://sassnarep3-star.github.io/Own4/nba-lines/site/governance/flagged.html

## Why this workspace exists

The repository already contained eight NBA implementations that disagree with each other and, in one case,
publish coefficients whose input dataset is not in the repo. This workspace does not add a ninth opinion to that
pile. It provides one reproducible pipeline whose every number can be traced to an official page or to a
committed file, and it says plainly where it cannot answer.

## What it does

1. **Captures official data** — 30 standings rows, 121 finals, tonight's slate, tonight's availability report.
2. **Verifies it** — the 121 finals are re-aggregated into win-loss records and diffed against the official
   standings table: 30/30 teams, 0 mismatches.
3. **Originates lines** — ridge-shrunk opponent-adjusted margins with a 2025-26 prior, an additive totals model,
   fair spread/total/team-totals/moneyline, and 12 player-prop lines anchored on official season averages.
4. **Measures dependence** — 10 correlations with 95% CIs, p-values and Benjamini–Hochberg q-values, computed
   in-repo rather than quoted.
5. **Removes luck** — strict walk-forward scoring, a paired bootstrap, a 4,000-draw permutation test, and FDR
   control across the whole strategy family.
6. **Refuses to pay** — 10 pre-registered gates and a 12-entry leaderboard with zero reward-eligible strategies.

## Headline result

| | |
|---|---|
| Out-of-sample Brier (home moneyline) | `0.2104` vs `0.2531` baseline |
| Skill score | `+0.1728` (bootstrap CI `+0.020` to `+0.310`) |
| Permutation p | `0.0002` |
| Graded games | 96 (gate requires 300) |
| Calibration ECE | `0.1037` (gate requires ≤ 0.05) |
| Reward-eligible strategies | **0 of 12** |

The model has forecasting information. It does not have a measurable betting edge, because there is no official
price archive to measure one against — and that limitation is stated on the site rather than papered over.

## Files

```
collect_official.py    transcription register (official URLs + hand-entered values)
engine.py              model, correlations, backtest, gates, leaderboard -> data/derived.json
audit.py               repository review + flagged registers
build.py               17 static pages + the root landing page
verify.py              2,400+ checks: sources, links, hosts, blanks, invariants, determinism
tests/                 19 unit tests (closed-form bivariate normal, leakage, reconciliation, invariants)
data/                  committed inputs and the derived output
site/                  generated site (do not edit by hand)
assets/                stylesheet and progressive-enhancement script
```

## Reproduce

```bash
cd nba-lines
python3 collect_official.py
python3 engine.py
python3 audit.py
python3 build.py
python3 verify.py
python3 -m unittest discover -s tests -v
```

Two consecutive runs produce byte-identical output; `verify.py` re-renders every page and compares hashes, and
the CI workflow fails on any diff.

## Data policy

The league's FAQ states its statistics "are not available for download for either academic or personal use".
This workspace performs no harvesting. It records 30 standings rows, 121 final scores, two slate entries and 13
availability rows, each read from a publicly displayed page and stored with its exact URL. The 47 MB partner
extract already in `data/raw/espn/` predates this workspace and is used only for prop volatility and correlation,
always flagged as tier-2.

## Limits, stated once and plainly

- 96 graded games cannot settle a skill question; intervals are wide by construction.
- No prices means no EV, no ROI, no CLV. This is the single largest limitation.
- Prop volatility is pooled across players, not estimated per player.
- Ratings are not adjusted for tonight's injuries or lineups; the counts are shown as context instead.
- The 2025-26 prior is an inherited transcription, internally consistent but not re-read this session.

Research only — not wagering advice. National Problem Gambling Helpline **1-800-MY-RESET** ·
https://www.ncpgambling.org/help-treatment

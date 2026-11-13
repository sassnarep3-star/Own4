# nfl-origination

Self-contained NFL line-origination and decision namespace for Own4.
**Snapshot 2026-11-13.** Live at https://sassnarep3-star.github.io/Own4/nfl-origination/

Analytical research only — **not wagering advice**. NCPG Helpline 1-800-MY-RESET (1-800-697-3738).

## What is in here

| Path | What it is |
|---|---|
| `data/official/*.py` | Dated transcriptions of official nfl.com pages, re-read 2026-11-13. Each file writes a `.json` next to it. |
| `engine/dataset.py` | Builds the graded game dataset and runs the 10 integrity checks (`IC-01`…`IC-10`). |
| `engine/model.py` | Rate model, walk-forward backtest, luck controls, 5 strategies + 2 placebos, 10 gates. |
| `engine/correlations.py` | 9 correlation tests for singles, parlays and prop combos — 6 computed, 3 blank with reasons. |
| `engine/originate.py` | Our own spread/total/win-probability for the 13 unplayed Week 10 games. |
| `data/requirements.py` | 41 requirements mapped to evidence and status. |
| `data/questions.py` | 20-question register: known / not known / blocks / unblocker / blank answer. |
| `data/suggestions.py` | 22-suggestion decision board with an ordered recommended path. |
| `data/flags.py` | 20 flags and the 24-source register. |
| `build.py` | Writes the 16 pages into `pages/`. |
| `compare.py` | Semantic reproducibility check: identical text, every number to 1e-9 relative. Used by CI. |
| `verify.py` | The gate: 39 checks. Fails on a broken link, an unsourced row, a missing disclaimer, or a claim that contradicts the evidence. |
| `run_all.py` | Runs all 13 steps in order. |

## Reproduce

```bash
python3 nfl-origination/run_all.py
```

Standard library only; no network access, no credentials, no JavaScript required to read the site.

## Headline result

The data reconciles perfectly (160/160 official 2026 cells) and **nothing qualifies**.
Our model beats a naive baseline but loses to the closing line (10.913 vs 9.848 margin MAE).
0 of 7 strategies qualify; 0 of 1,000 reward points are awarded. The NFL publishes no odds, so no
price, stake, edge or return is claimed anywhere.

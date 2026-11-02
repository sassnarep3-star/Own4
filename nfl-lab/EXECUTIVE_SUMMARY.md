# NFL Line Origination Lab — Executive Summary

**Session:** arena/909635f5-own4 · **Date:** 2026-11-02 UTC · **Status:** complete (data, model, site, gates)
**Live section:** `nfl-lab/` (linked from the site dashboard) · **Not a betting service; no strategy is validated.**

## 1. What was delivered

| Area | Deliverable | Headline result |
|------|-------------|-----------------|
| Data | 120 completed 2026 regular-season games + 32-team standings, transcribed from official nfl.com pages | **480/480 standings cells verified** against the game log (14 automated checks, 0 mismatches) — `nfl-lab/data/verification_report.json` |
| Signals | 13 pre-registered descriptive signals with 95% Wilson intervals | Rest-advantaged side won **0.840 [0.654, 0.936]** (n=25, underpowered) |
| Correlations | 7 correlation pairs with p-values (pure-stdlib t-tests) | Rest differential vs win **r=0.336, p=0.0005** (n=103); home field φ=0.080 p=0.233; momentum r=0.030 p=0.673 (null); passing yds/gm vs wins r=0.364 p=0.041 (n=32) |
| Model | Walk-forward Elo (K=20, HFA=65, MOV multiplier); margin scale + baselines fitted on weeks 1–4 only; holdout weeks 5–8 locked | Holdout Brier **0.24907** vs constant 0.25279 vs record-diff 0.28874 (n=56); ECE 0.119 |
| Own lines | 16 upcoming games (W8 MNF + full W9) with fair moneylines, model spreads, totals | Market columns **permanently blank** (no official line source — gate G7 blocked) |
| Strategies | 8 strategies pre-registered in `strategy_registry.json v1.0` before evaluation | **0 of 8 reward-eligible** — validation gates work as designed |
| Site | 11-page dashboard (`index`, `executive-summary`, `data`, `signals`, `correlations`, `own-lines`, `strategies`, `leaderboard`, `validation`, `flagged`, `sources`) | 297 table rows, every row carries an official https source link (audit 0 problems) |

## 2. Validation gates (S1 · Elo sides)

| Gate | Result | Why |
|------|--------|-----|
| G1 Provenance | PASS | Every row carries official nfl.com URLs; independent recomputation matches standings |
| G2 Leakage | PASS | Chronological walk-forward; params committed before first run (git history) |
| G3 Sample size | **FAIL** | Holdout n=56 < 300 required |
| G4 Baseline | PASS | Brier better than both pre-registered baselines |
| G5 Calibration | **FAIL** | ECE 0.119 > 0.10 |
| G6 Registry | PASS | All strategies registered before evaluation |
| G7 Market comparison | **BLOCKED** | No official source publishes operator lines |
| G8 Costs/settlement | **BLOCKED** | No official operator terms |

**Conclusion: NOT VALIDATED.** The model forecasts are published as research outputs with
honest gate outcomes; they are not claimed as edges, and rewards remain unfunded/blank.

## 3. Skill vs. luck — what survived scrutiny

- **Rest advantage** is the only measured signal with strong evidence (C2 p<0.001), yet the
  high-impact subset (SIG-11, 25 games) is far below the pre-registered sample gate. Treated
  as a hypothesis for next season's registry, not an edge.
- **Home field** and **momentum** did not reach significance this sample — reported as null,
  not dressed up.
- **Parlay leg independence** (C5a): n=8 < required 30 → inconclusive; C5b blocked entirely
  (kickoff windows missing from schedule extraction) → left blank + flagged.
- **Player prop combos (S7)**: blocked — official game-level player logs were not ingested;
  no correlation was computed or guessed.
- Totals model lost to its own baseline on the holdout (MAE 11.46 vs 11.30) — published as a
  failure (FL-06).

## 4. Irregularities & flagged items (full list: `flagged.html`)

1. No official line/odds source exists → all market cells blank (FL-01).
2. nfl.com Week 1 header says "Sunday Night Football, September 9th" while the game line says
   Wednesday, September 9th — recorded verbatim as Wednesday (FL-10).
3. Schedule extraction gap cut the WAS–DAL W2 score → filled only after reading the official
   Game Center box (WAS 20, DAL 37) (FL-11).
4. Team-stats columns that could not be named with certainty were discarded, never guessed (FL-12).
5. Week-8 MNF (Bears at Seahawks) unplayed at cut-off → excluded from dataset (FL-08).
6. 6 international neutral-site games flagged; neutral handling pre-registered (FL-09).

## 5. Sources (all official or canonical methodology)

- nfl.com schedules (W1–W9), nfl.com league + division standings, nfl.com team passing stats,
  nfl.com game center box, operations.nfl.com 2026 rulebook, nfl.com injuries portal,
  nextgenstats.nfl.com portal — retrieval 2026-11-02, per-row links on every page.
- Methodology: scikit-learn cross-validation + calibration docs, NIST handbook,
  ncpgambling.org (reward/responsible-play caution).

## 6. Reproduce / verify

```bash
python3 nfl-lab/scripts/verify_data.py     # 14 checks, 480 cells
python3 nfl-lab/scripts/build_signals.py   # signals + correlations
python3 nfl-lab/scripts/build_model.py     # Elo, holdout, gates, own lines
python3 nfl-lab/scripts/build_site.py      # regenerate site
python3 nfl-lab/scripts/audit_site.py      # row/link audit
python3 -m unittest discover -s tests      # includes nfl-lab CI tests
```

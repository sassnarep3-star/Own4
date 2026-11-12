# nfl-decision — NFL Decision Lab

An evidence layer, an open question register and a suggestions board for the Own4 NFL work.

**Live:** https://sassnarep3-star.github.io/Own4/nfl-decision/

## What is here

| Path | What it is |
|---|---|
| `scripts/01_results.py` | Builds and reconciles the verified 2026 game log (160/160 official cells) |
| `scripts/02_model.py` | Chronological Elo + decayed-scoring model; knobs frozen on 1999–2012 |
| `scripts/03_backtest.py` | Backtest, luck removal, gate application |
| `scripts/04_correlations.py` | Correlation values with Fisher CIs and FDR |
| `scripts/05_props.py` | Player-prop combo dependence study |
| `scripts/06_own_lines.py` | Own lines for the current week |
| `scripts/07_forecast.py` | Forecast-skill leaderboard |
| `scripts/08_build_site.py` | Generates the 14 pages |
| `scripts/09_verify.py` | Verifies links and that every table row carries a source |
| `data/questions.py` | The question / information / answer register |
| `data/suggestions.py` | The suggestions board |
| `data/injuries_wk10.py` | Official Week 10 injury report + verified depth deficiencies |

## Reproduce

```bash
python3 nfl-decision/scripts/01_results.py
python3 nfl-decision/scripts/02_model.py
python3 nfl-decision/scripts/03_backtest.py
python3 nfl-decision/scripts/04_correlations.py
python3 nfl-decision/scripts/05_props.py
python3 nfl-decision/scripts/06_own_lines.py
python3 nfl-decision/scripts/07_forecast.py
python3 nfl-decision/scripts/08_build_site.py
python3 nfl-decision/scripts/09_verify.py
```

Scripts 03–07 use only the standard library. Scripts 01, 02, 08 and 09 also run on the standard library.

## Rules this module follows

1. Every table row carries a source link. `09_verify.py` fails the build otherwise.
2. A value that cannot be confirmed on an official NFL page is left blank and listed on the Flagged page.
3. Nothing is inferred from a practice status, a roster position, or a peer session's claim.
4. No edge is claimed without an archived price.

*Analytical research only — not wagering advice. NCPG Helpline 1-800-MY-RESET (1-800-697-3738).*

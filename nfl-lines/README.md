# nfl-lines — NFL Line-Origination Lab

An isolated namespace that originates its **own** NFL lines, measures them against the
market, strips luck out of the measurement, and only then ranks strategies as a
leaderboard competition.

Live at `https://sassnarep3-star.github.io/Own4/nfl-lines/` once merged to `main`.

## How to rebuild everything

```bash
cd nfl-lines
python3 -m pip install numpy pandas
python3 run_all.py           # 8 stages, ~30 s, writes data/derived/*.json
python3 engine/build_site.py # writes index.html + pages/*.html
python3 engine/verify_site.py  # link + source-coverage check; exits non-zero on failure
```

`engine/repo_audit.py` is a read-only mechanical scan of the whole repository
(file counts, namespace page counts, local href resolution). It edits nothing.

## Layout

| Path | What it holds |
|---|---|
| `data/raw/nfldata_games.csv` | Third-party game archive, pinned to nflverse commit `6ea0be6dd9bfc95c818c05568753bc70f1986ea2`. |
| `data/official/*.json` | Values transcribed from NFL.com pages that were fetched and read directly. |
| `data/model_params.json` | Pre-registered model/evaluation parameters, timestamped **before** the first backtest. |
| `data/decisions.json` | Decision register (Q01–Q15) and ranked suggestions (SG-01…SG-12). |
| `data/flags.json` | Irregularities IR-01…IR-15. |
| `data/provenance.json` | Source register SRC-01…SRC-11 plus the derived artefacts. |
| `data/derived/*.json` | Everything the pipeline computes. Regenerable at any time. |
| `engine/` | `dataset`, `model`, `backtest`, `evaluate`, `correlations`, `calibration`, `injuries`, `repo_audit`, `build_site`, `verify_site`. |
| `pages/`, `index.html`, `assets/` | The static site. Generated — do not hand-edit. |

## Rules this namespace follows

1. **Official first.** A number is transcribed from NFL.com or it is not published as fact.
2. **Third-party is labelled.** The NFL publishes no betting lines, so every market
   spread, total, moneyline and price is labelled third-party and linked to its archive.
3. **Blank beats invented.** Where no official source exists — player-prop lines,
   depth-chart rank, weather observations — the cell is blank and flagged, never filled in.
4. **Pre-registered parameters.** Model and gate settings carry a registration timestamp
   that precedes the first backtest, so they cannot be tuned to the results.
5. **Walk-forward only.** Every forecast is refitted on games that finished strictly
   before the game being forecast. No future information can leak.
6. **Luck is measured, not assumed.** Each strategy is compared against a 20,000-trial
   no-skill simulation at its own actual prices, corrected for testing many strategies
   (Benjamini–Hochberg), and run through eight gates before it can be called
   reward-eligible.
7. **Every published table row carries a link.** `engine/verify_site.py` enforces it.

## Headline result

On 4,055 out-of-sample games the correlation between (own line − market line) and the
actual result against the market spread is **r = 0.0072**, 95% CI `[-0.024, 0.038]` —
an interval that contains zero. **Zero of 15 strategies clear all eight gates.** That is
the intended output: a reproducible "not yet" instead of an unverifiable "yes".

## Data licences

The third-party archive's licence and data terms were **not** reviewed in this session
(irregularity IR-05). Treat the contents as research use only until that review is done.

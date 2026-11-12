# NFL Line Genesis — Own4

A self-contained NFL research workspace: originated Week 10 lines, pre-registered validation gates, measured
correlations, availability tracking and a decision register. Published as static pages under `/nfl-hub/`.

**Start here:** [`index.html`](index.html) · [Executive summary](EXECUTIVE_SUMMARY.md) ·
[Suggestions & decisions](pages/suggestions.html) · [Open questions](pages/questions.html) ·
[Flagged for review](pages/flagged.html)

## The one-paragraph result

Official data reconciles perfectly (32/32 teams, 14/14 fixtures). The model does **not** beat the closing line:
holdout margin MAE 10.392 versus 9.871 for the market, totals 11.971 versus 10.470. No registered strategy passes the
gates — S1 was +4.6% on validation and −5.3% on the untouched holdout, which is exactly why a holdout exists.
Nothing here is a validated betting edge, and the site says so on every page that shows a line.

## Rebuild

```bash
python3 nfl-hub/pipeline/run_all.py   # model, backtest, correlations, Week 10 lines
python3 nfl-hub/build.py              # 15 static pages
python3 nfl-hub/verify.py             # publication gate (rows, links, anchors, rebuild)
```

All three are deterministic. CI (`.github/workflows/nfl-hub.yml`) fails if the rebuild drifts by a byte, if any table
row lacks a source link, or if any page cites a URL recorded as dead.

## Data

| Input | Source | Status |
|---|---|---|
| 2026 standings | [NFL.com standings](https://www.nfl.com/standings/) | Official, 32/32 reconciled |
| Week 10 fixtures | [NFL.com Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) | Official, 14/14 reconciled |
| Injuries | [Official Week 10 injury report](https://www.nfl.com/injuries/) | Official snapshot, 6 formal designations |
| Historical games and closing lines | [nflverse/nfldata](https://github.com/nflverse/nfldata) commit `6ea0be6` | Third-party archive, hashed |
| Depth charts | — | **No official source found** (tested NFL.com URL returns 404) → blank |
| 2026 market lines | — | **Not in scope** → blank |
| Player props | — | **Blocked** (no player feed, no prop prices) |

## What is deliberately blank

- 2026 market lines, closing-line value and any market comparison.
- Starter / backup / 2nd-3rd-4th-string status (no official depth chart found).
- Player prop lines, prop results and prop correlations.
- Injury causes for most players (blank in the official table).
- The defensive availability index (it would require unverified starter status).

Every blank is listed with a severity on the Flagged for Review page and tied to a question in the register.

## Layout

```
nfl-hub/
  index.html                 dashboard
  pages/                     14 category subpages
  data/                      official captures, model output, strategy results, registers
  data/source/               pinned archive snapshot + provenance hashes
  pipeline/                  common.py model.py backtest.py correlations.py weekly.py run_all.py
  build.py verify.py         static generator and publication gate
  assets/hub.css hub.js      no-dependency UI
```

## Limits and responsible use

Research only, not wagering advice. Non-monetary rewards only; the competition pool is unawarded because nothing
qualified. National Problem Gambling Helpline: <https://www.ncpgambling.org/help-treatment/>.

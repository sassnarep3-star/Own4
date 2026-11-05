# `verification/` — verified 2026-11-05 snapshot, model and site

Everything the canonical dashboard shows is produced here. Standard library only, no network calls,
no secrets, deterministic output.

```bash
python3 verification/collect_2026-11-05.py   # transcription + source register  -> verification/data/
python3 verification/reconcile.py            # 13 audit checks                   -> verification/out/reconciliation.json
python3 verification/analysis.py             # model, gates, correlations, tests -> verification/out/analysis.json
python3 verification/build.py                # root index.html + verified/*.html
python3 verification/verify_site.py          # link + source-link gate (exits non-zero on failure)
```

`python3 engine/build.py` still builds the earlier sessions' pages and now calls `verification/build.py`
last, so the root landing page cannot go stale.

## What is in the snapshot

| Data | Rows | Read | Official page |
|---|---|---|---|
| Standings, 2026-27 | 30 | 2026-11-05 | https://www.nba.com/standings |
| Team stats, per game | 30 | 2026-11-05 | https://www.nba.com/stats/teams/traditional |
| Final scores, 11/02 + 11/04 | 29 | 2026-11-05 | https://www.nba.com/games?date=2026-11-04 |
| Scheduled slate, 11/05 | 2 | 2026-11-05 | https://www.nba.com/games?date=2026-11-05 |
| Season leaders for the slate | 4 | 2026-11-05 | https://www.nba.com/games?date=2026-11-05 |
| Final scores, inherited | 56 | 2026-11-02 | per-row `source_url` in `official/games.json` |

Games in the modelling sample: **85 of 121** played (70.2%). Seven October dates — 10/20, 10/22, 10/24,
10/25, 10/26, 10/27, 10/29 — hold 36 games that were never captured. They are used nowhere.

## Results (this snapshot)

* Walk-forward, 35 graded games: winner accuracy **0.5714** vs **0.6000** always-pick-home (one-sided p 0.7003);
  bootstrap interval [0.4000, 0.7429].
* Totals: MAE **15.123** vs 15.859 naive baseline, permutation p **0.0261** — nominal only; fails the 300-game
  floor and fails Benjamini-Hochberg at q = 0.05 with m = 2.
* Correlations, n = 30, 5 of 10 survive FDR at q = 0.05.
* Gates: 4 pass, 5 fail, 1 blocked (no official price exists). Strategies qualified: **0**. Rewards: **0**.
* Flags: **13**, published at `/verified/flagged.html`.

## Rules this code follows

1. A number is published only with the official URL it came from; a number that cannot be confirmed is blank
   and flagged, never estimated.
2. Fresh transcription is labelled differently from inherited, corroborated rows.
3. No betting price is invented. Where a price is needed, the gate is `BLOCKED`, not passed.
4. The official `+/-` column is displayed but never used as a model input, because its 30 values sum to −5.3
   instead of 0.
5. `verify_site.py` fails the build if any table row lacks a source link, any local link is broken, or a page
   loses its navigation and responsible-gambling footer.

## Statistical notes

* Ratings are shrunk toward the league mean by `k = 8` prior games and the home edge by `k = 20`; both were
  written to `data/gates.json` before the run.
* Win probability uses the residual standard deviation of the margin model, not the raw spread of margins.
* The permutation test holds predictions fixed and shuffles actual totals, 10,000 times, seed 20261105.
* Power: a true 55% winner edge needs ≈620 graded games for 80% power at α = 0.05.

Usage note: the [NBA Stats FAQ](https://www.nba.com/stats/help/faq) states that statistics are not available for
download for personal or academic use. Only the displayed values needed for this research were transcribed, each
with its official URL. See flag `F-RIGHTS`.

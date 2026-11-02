# research/ — computed strategy research (session a4ec3896)

Everything here is **computed on historical data against a transparent market proxy, not against sportsbook prices.**
It is unverified by any official source beyond a one-game spot check (see "Data" below) and is labelled that way on the site.

## Run
```
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -r research/requirements.txt
git clone --depth 1 https://github.com/NocturneBear/NBA-Data-2010-2024.git /tmp/data/nb
cd research && NBA_DATA_DIR=/tmp/data/nb /tmp/venv/bin/python run_all.py      # ~1 min, 2 CPUs
python3 ../build_site.py                                                        # regenerates the site from data/*.json
/tmp/venv/bin/python -m unittest research.test_research                         # run from the repo root
```
Outputs: `data/research_results.json` (singles, parlays, meta, controls), `data/correlations_computed.json`.
The dataset commit used was `a5f108b5b1f08074d78b9e8e901926a9ce4c06c5` (recorded in `meta`).

## Data
- NocturneBear/NBA-Data-2010-2024 — a **third-party GitHub mirror** of NBA.com box scores, regular season 2010-11 → 2023-24. Not official. 
- NBA.com's FAQ says its statistics are not available for download for academic or personal use, and bulk official endpoints were unreachable from the sandbox, so no official bulk source was used. Data rights need an owner decision (flagged).
- Spot check: one official box score (LAL @ DEN, 2023-10-24) matched the mirror for the final score and two players' minutes/PTS/REB/AST. That is not a verification of the dataset.
- Playoffs are excluded. No betting lines exist in the data.

## Design
- **Market proxy** = season-to-date mean + 0.5 × (recency EWMA − season mean), shifted by a dev-median constant so ~50% of dev outcomes go over. Continuous line; pushes void.
- **Own line** = proxy + OLS adjustment on pre-game features (no intercept, dev-centred). Bet the side of the adjustment when |adjustment| is in the dev top 50% / 25% / 10%.
- **Split**: dev 2010-11 → 2019-20 fits models and chooses thresholds; holdout 2020-21 → 2023-24 is evaluated once with frozen parameters (but see "Disclosures").
- **Settlement**: assumed −110 per leg (break-even 52.38%); parlays multiply leg decimals; date-clustered SEs; Holm correction over all 27 single/prop trials.
- **Strategies**: T1 pace form, T2 rest flags (totals); M2 rest differential (spread); P1-P4 player points / rebounds / assists / PRA from minutes trend + context; T3 and M1 are **controls** that only re-weight the recency term inside the proxy and are never ranked. 
- **Gates G1-G12** are in `data/validation_gates.json` (G10 availability and G12 prospective replication are not run). 
- **Tiers**: Provisional Gold (all gates) > Silver (Holm-significant; fails only sample size/direction) > Bronze (raw p<0.05 only) > No award. 

## Disclosures (read before relying on any number)
1. **Design iteration.** Run 1 used a plain season-to-date baseline and produced implausible 60–70% hit rates because that baseline lags in-season trends; it was discarded and replaced by the proxy above. The first run's holdout results were seen, so **the holdout is not pristine**. Gate thresholds were not changed after seeing results. The control experiment is kept in `meta.proxy_vs_naive_control`.
2. The shuffled-outcome canary originally planned as G1 was invalid and was replaced by a feature-perturbation leakage test plus a directional-null test in G7. Gate IDs therefore differ from the earlier proposed G1-G7 numbering.
3. Edges are versus a proxy that ignores minutes, injuries and matchups. A real market prices these; most player-prop "edge" probably reflects that. The Over skew of the prop strategies fails G7 for most of them.
4. Possessions use FGA + 0.44·FTA − OREB + TOV, a project-defined estimator (the NBA glossary gives no box-score formula).
5. Data ends in 2023-24; the league is in 2026-27. Prospective replication (G12) needs fresh data and timestamped predictions, so every top tier is **Provisional**.

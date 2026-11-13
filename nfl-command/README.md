# NFL Command Center

This namespace holds the clean, source-linked NFL site built for the 2026 season,
together with the engine that produces every number on it and the audit of the
rest of the repository.

Nothing outside this directory is edited by the code in here. The audit reads the
other namespaces and writes its findings into `data/derived/repo_audit.json`.

## Source policy

* Official values come from `nfl.com` and every one of them carries that page's
  link.
* Betting prices come from a named third-party archive, because the NFL
  publishes no betting lines. Every such value is labelled third-party in the
  column header and in every row.
* A value that no official source confirms is rendered blank with an explicit
  unverified marker. It is never filled in by inference.

## Layout

```
data/official/     captures read directly from official NFL pages
data/raw/          pinned third-party archive and the raw page capture
data/              the pre-registration, the price determination and the registers
data/derived/      everything the engine computes
engine/            the pipeline, in the order it must run
pages/             the published site
assets/            the stylesheet
```

## Running the pipeline

```
python3 engine/00_convention.py        # the spread line convention
python3 engine/00_price_audit.py       # the calibration audit of the price columns
python3 engine/00_sweep_development.py # the development-window parameter sweep
python3 engine/01_forecast.py          # the walk-forward forecast engine
python3 engine/02_analyze.py           # strategies, gates, correlations, leaderboard
python3 engine/03_injuries.py          # the injury normalisation and depth table
python3 engine/04_audit_repo.py        # the repository audit
python3 engine/05_build_site.py        # the site build
python3 engine/06_verify_site.py       # the site verification
```

`engine/06_verify_site.py` fails the build if any table row lacks a source link,
if any local link does not resolve, or if placeholder text reaches a page.

## The order that matters

`data/gates_preregistered.json` and `data/strategy_registry_preregistered.json`
were committed before the engine was first run. `data/parameter_amendment_1.json`
records a defect in the pre-registered model that was found on the 1999 to 2022
development window, the correction, and the parameters chosen on that window
alone. `data/price_determination.json` records the audit that found the
third-party archive's spread and total price columns unusable and sets out how
the reference price is reconstructed instead.

`engine/00_sweep_development.py` reads only the development window. It cannot
tune anything on the holdout.

## What is not claimed

* No betting strategy passes the validation gates, so nothing here is activated
  as a bet. The betting board pays nothing.
* The forecast board pays for forecast skill against a naive baseline. That
  metric needs no price, so it can be scored even though the NFL publishes no
  betting lines.
* Reward points are non-monetary until the owner funds a pool.

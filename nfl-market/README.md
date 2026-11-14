# nfl-market — price-snapshot store, results feed, origination

Everything here is generated from data. Nothing on the site is typed by hand, and
`verify.py` fails the build if a table row has no source link, if a printed number
cannot be matched back to the JSON the build read, or if any internal link breaks.

## Rebuild

```sh
python3 nfl-market/data/official_scores.py      # weekly finals, with sources
python3 nfl-market/data/market_odds_raw.py      # the archived price payloads
python3 nfl-market/data/official_lineups.py     # injury report + game-book lineups
python3 nfl-market/data/official_reference.py   # standings, both views
python3 nfl-market/engine/store.py              # 8 derived artefacts
python3 nfl-market/data/register.py             # questions / suggestions / decisions
python3 nfl-market/build.py                     # 13 pages
python3 nfl-market/verify.py                    # gate: exit 0 = publishable
```

Standard library only. No network access is used by any script; the archive is the
only input, so a value that was never read cannot appear on a page.

## The two structural facts

1. **Scores are official; prices are not.** Finals come from nfl.com or from the
   official Game Book PDF, one link per row. Every spread, total and moneyline comes
   from one commercial book syndicated through a public endpoint. The NFL publishes
   no odds — checked again on 2026-11-14. The site says this on every page rather
   than only on the flag page.
2. **Thirteen of fourteen week-10 games have not been played.** Their second
   snapshot is the provider's current number, not a close. Only one game has a true
   open-to-close pair, and only one game can be graded.

## Layout

| Path | What it holds |
| --- | --- |
| `data/*.py` | collectors/transcribers; each writes a `data/*.json` archive |
| `data/*.json` | the archive: scores, raw prices, lineups, standings, register |
| `engine/store.py` | builds every derived artefact in `data/derived/` |
| `data/derived/*.json` | store, movement, origination, leaderboard, demotion, correlations, results feed, coverage, flags, register |
| `pages/*.html` | generated; do not edit by hand |
| `build.py` | page builder |
| `verify.py` | publication gate |

## Deliberate blanks

`MC-03` has `n = 0` because only one week-10 game has finished. `MC-04` cites a prior
session's correlation instead of republishing it, because it rests on a third-party
source this namespace does not treat as official. No depth rank appears anywhere,
because the NFL publishes no depth chart — `nfl.com/depth-charts/` returns the 404
"Flag on the Play" page, linked from the source register as evidence rather than
hidden as a dead link.

Analytical research only. No wagering advice; nothing here has ever been staked.

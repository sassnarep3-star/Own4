# NFL Week 11 official injury report — delta workspace

Session `arena/893d26c1-own4` · branch `arena/893d26c1-own4` · built 2026-11-19 (UTC).

**What it does.** Compares two dated reads of the official NFL injury report
(<https://www.nfl.com/injuries/>) and publishes **only the changes** (brief: "publish the delta,
never the level"). Every table row links to the official page.

- Earlier read: the stored raw HTML capture `nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html`
  (captured 2026-11-18T23:49:17Z, sha256 checked against `nfl-readiness-register/snapshots/manifest.jsonl`).
- Later read: `data/official_read_2026-11-19_w11.md`, transcribed from the `fetch_page` rendering of the same page
  (read after 06:48:48 UTC on 2026-11-19). It is **not** a raw HTML byte capture (sandbox egress does not reach nfl.com).

## Layout

| Path | What |
|---|---|
| `data/official_read_2026-11-19_w11.md` | transcribed later read (13 games, 24 club tables, 253 rows) |
| `data/delta.json` | computed delta (added / removed / changed, per-club states, provenance) |
| `engine/parse_raw.py` | stdlib parser for the official HTML |
| `engine/delta.py` | computes the delta; checks the raw hash against the manifest |
| `engine/build.py` | renders the static site (deltas only) |
| `engine/verify.py` | independent re-derivation of counts, vocabularies, links, determinism |
| `index.html`, `pages/*.html` | summary · delta · clubs · sources · Flagged for Review |

## Rebuild and verify (stdlib only, Python 3)

```
python3 nfl-w11-delta/engine/delta.py
python3 nfl-w11-delta/engine/build.py
python3 nfl-w11-delta/engine/verify.py
```

CI: `.github/workflows/nfl-w11-delta.yml` runs the same three steps and fails on any difference from the committed output.

## Result (read it with the flags)

- 242 rows are identical in both reads (no change to injury, practice or game status).
- 11 rows were added: the Chargers block, which the earlier capture printed as "No Injuries Reported".
- 0 rows removed, 0 changed.
- Six clubs (ATL, CLE, GB, LAR, NE, SEA) appear in neither read; bye status is **not** verified here (F5).

The irregularities and unverified items are on `pages/flagged.html` (F1–F9), each with an official source link.

## Limits

- The later read is an agent transcription, not a raw capture (F6). The 242 overlapping rows agree with the raw HTML on all four
  compared fields, which is a check on the transcription, not a substitute for a raw capture.
- The page prints no update time, so read times are the agent's clock (F7).
- Row-level transcription sits in this public repository; the brief's private-store term is an open owner decision (F8).
- Friday's report is not read here, so game-status designations are provisional (F9).

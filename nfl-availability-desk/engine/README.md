# `engine/` — the only source of published numbers in this namespace

Nothing in `nfl-availability-desk/index.html` or `pages/` is typed by hand. Each page is a pure
function of the artefacts in `data/`, produced by the scripts below, and CI re-runs all of them and
fails if the output differs from what is committed. Order matters only in that `build_site.py` reads
what the others write.

| script | reads | writes | fails the build when |
|---|---|---|---|
| `capture.py` | `data/availability_snapshot_2026-11-15.csv`, `data/fixtures_week10.csv` | `data/derived/capture_validation.json` | the transcription is structurally wrong: a required field is blank, a club block is broken or unmatched to a fixture, a vocabulary value is invented, a blank was rewritten into a value, a player is duplicated |
| `audit.py` | the capture, the fixtures, the standings, and **every** stored capture of the same page in this repo | `data/derived/{capture_audit,capture_diffs,standings_check,designation_delta}.json` | a standings identity breaks (`sum PF != sum PA`, net points, win pct), or a club's section disappears relative to the fixture list |
| `drift.py` | `data/drift_expectations.json` + the capture | `data/derived/{drift_report,hashes}.json` | the row count, per-club counts, required fields or vocabularies differ from what was pinned **before** the next capture; also writes the transcription fingerprints the evidence page publishes |
| `repo_review.py` | the repository tree | `data/derived/repo_review.json` | never (it is an inventory; it reports file and page counts and titles only, and asserts nothing about other sessions' figures) |
| `originate.py` | `data/price_snapshots.json`, the fixtures | stdout, and `data/derived/origination_status.json` when run normally | a market is recorded out of order (side → total → moneyline) or a difference is published without the fair line beside it. `--probe` asserts the guards themselves fire |
| `preregister.py` | `prereg/*.md` + git history | `data/prereg.json` | a frozen rule no longer matches the hash at its registration commit, the registration commit is missing/pending, or no evaluation-window state was recorded at freeze time |
| `build_site.py` | all of the above | `index.html`, `pages/*.html`, `assets/readiness.css` | an artefact it needs is missing or stale |
| `verify_site.py` | the built pages + the artefacts | nothing (it only judges) | an internal link 404s, a data row has neither a source link nor an `UNVERIFIED` mark, a price value appears anywhere in the HTML, the landing page disagrees with the artefacts, a cited file does not exist, or the readiness register leaves its declared vocabulary / loses a required field / has a `clearing_number` with no number in it |

## Two rules that are easy to break and are therefore enforced in code

1. **`data/derived/*` is machine output.** Edit a source artefact and re-run; never hand-edit a
   derived file. If the site shows a number, `verify_site.py` has already proven it appears in the
   artefact it came from.
2. **A blank stays blank.** `capture.py` and `drift.py` both reject values that look like an inferred
   blank (`None`, `N/A`, `Healthy`, `Available`, `-`). The official report prints empty cells; so do
   we, with a flag id on the page.

## What is deliberately *not* here

No fetcher, no model fit, no backtest, no leaderboard, no staking. The reasons are each a row in
`data/readiness.json` with the gate that clears it — mainly that no official price source exists
(`RF-02`) and that the capture cadence the brief assumes does not run (`RF-16`). The only file that
touches git is `preregister.py`, and it is read-only.

Reproduce:

```bash
cd nfl-availability-desk
python3 engine/capture.py && python3 engine/audit.py && python3 engine/drift.py \
  && python3 engine/repo_review.py && python3 engine/originate.py --probe \
  && python3 engine/preregister.py --check && python3 engine/build_site.py \
  && python3 engine/verify_site.py
```

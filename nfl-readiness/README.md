# nfl-readiness — decision-readiness layer for the NFL line-origination brief

Session `arena/d941f3c1-own4`, scope D1–D12 of `COORDINATION.md`. Built 2026-11-15 from official
NFL pages read inside this session and from files already in this repository. Nothing here fetches
at build time, so every published number is reproducible from the checked-in artefacts.

**Published site:** `nfl-readiness/index.html` (root navigation carries it under
*NFL Readiness · decision register (2026-11-15)*).

## What this namespace is for

The brief lists ~72 requirements. Most project answers describe what was built; the question a
reviewer actually has is *what is decision-ready, what is blocked, and what single number clears
each block*. So this namespace publishes:

| artefact | what it is |
|---|---|
| `data/readiness.json` | one row per requirement: status, the gate that blocks it, the number that clears it, evidence + source. 72 rows. |
| `data/availability_snapshot_2026-11-15.csv` | the Week 10 official availability report, transcribed row by row: 347 rows across 28 club sections, 8 columns, blanks preserved as blanks. |
| `data/fixtures_week10.csv`, `data/standings_2026-11-15.json` | the 14 Week 10 fixtures as the schedule page states them, and the 32-club standings as the league prints them. |
| `data/official_reads.json`, `data/evidence.json` | the read window per page (URL, chunks, order) and 33 dated official statements used as evidence. |
| `data/capture_manifest.json`, `data/drift_expectations.json` | how the capture was made, its limits, and the row/field/vocabulary pins a re-capture must satisfy. |
| `data/governance.json`, `prereg/PREREG-001-shadow-baseline.md`, `data/prereg.json` | rules frozen **before** results: leaderboard rule, divisions, joint-evidence gate, controls, demotion gate, price policy, ablation spec, and the pre-registration ledger. |
| `data/questions.json`, `data/suggestions.json`, `data/flags.json` | 24 questions with what is known/unknown/how to discover it; 12 suggestions with options + cost (verdicts left blank for the reviewer); 17 flagged irregularities. |
| `data/price_snapshots.json` | the price store, with its contract and **zero rows** — there is no official price source, and an empty store with a stated reason is the honest artefact. |
| `data/derived/*.json` | computed output of the engines. **Never hand-edited.** |

## Engines

```
python3 engine/capture.py      # structural validation of the transcription (field set, club
                               # blocks, fixture pairing, blanks, vocabulary) — exit 1 = not fit
python3 engine/audit.py        # census, cross-capture reconciliation vs every stored render,
                               # standings identities, intra-week designation delta  -> data/derived/
python3 engine/drift.py        # the scraper alarm (expected row counts + required fields) and the
                               # transcription hashes published on the evidence page
python3 engine/repo_review.py  # namespace inventory for the repository-review page
python3 engine/originate.py    # origination order (side -> total -> moneyline) + the three-column
                               # contract; --probe proves the guards fire
python3 engine/preregister.py  # --freeze writes a rule's hash + commit into data/prereg.json;
                               # --check fails if a frozen rule was edited afterwards
python3 engine/build_site.py   # renders index.html + pages/ from the artefacts (pure function)
python3 engine/verify_site.py  # publication contract: links resolve, every data row is
                               # source-linked or marked UNVERIFIED, no price value may appear,
                               # index numbers match the artefacts, register vocabulary is closed
```

CI: `.github/workflows/nfl-readiness.yml` runs all of the above and fails if a rebuild changes any
committed page.

## Rules this namespace holds itself to

* A value not confirmable on an official source is printed **blank and flagged**, never inferred,
  never filled from a third party, never carried over from another week.
* No depth rank, no starter/backup label, no snap share: the official report publishes none, and the
  brief rejects deriving them from jersey number, experience or salary.
* No ROI or win-rate ranking; backtest figures never appear on a leaderboard page.
* Peer namespaces are cited as `peer:` and **not** re-verified here.

## Findings a reviewer should read first

1. The Week 10 report is **347 rows / 28 club sections**, not "254" or "279"; four clubs publish no
   section because they are on bye, which is not "no injuries".
2. Designations cover **171 of 347 rows (49.3%)** — the brief's "6 of 254" does not reproduce.
3. `Probable` **does not appear** in the live Week 10 report: three labels observed, not four.
4. Five stored peer captures of the same page are **strict subsets**; features built on them silently
   drop most Out/Doubtful/Questionable rows (25–162 designated rows vs 171 here).
5. The bracketed `W-L` on the report is a **live join** (28/28 clubs matched the live standings at
   read time) — it must be stored with the clock, never as a property of an availability row.
6. Two hard official contradictions: a traded player still listed on his former club's report, and a
   named-IR headline against an empty injury cell.
7. `136 games` matches nothing: 145 credited at read time, 133 through Week 9, 147 when Week 10
   completes. The corpus is registered by definition instead (PREREG-001 §2).
8. No official price source exists, so every price-dependent requirement is blocked by one owner
   decision (DEC-P1), not by effort.

# NFL Readiness — requirements register & decision-readiness dashboard

Session `63ebae0e` · branch `arena/63ebae0e-own4` · built 2026-11-15.

This workspace consolidates the **entire requirement list from the 2026-11-15 brief**
(68 requirement rows + 5 process rows, verbatim) into one decision surface:

- **Landing page** — the decision-readiness table: one row per requirement with the
  gate that blocks it and the number that would clear it (REQ-22).
- **`pages/requirements.html`** — full register with evidence, categories, statuses.
- **`pages/snapshots.html`** — immutable snapshot ledger (sha256, timestamps), the
  live Week-10 capture (28 tables / 347 rows / 67 Out), verified finals, the official
  November trade ledger, and the dated schedule announcement.
- **`pages/questions.html`** — questions / information needed / answers (blanks by policy).
- **`pages/suggestions.html`** — suggestions to review BEFORE implementing anything.
- **`pages/repo-review.html`** — line-by-line repository review findings.
- **`pages/flagged.html`** — every irregularity and unverified value, with sources.

## Automation (REQ-28/29/53/61/62)

`capture/snapshot_official_pages.py` + `.github/workflows/nfl-readiness-snapshot.yml`
capture the official injury report and league reserve list every Wed/Thu/Fri 18:00 UTC,
store raw bytes under `snapshots/` (outside the rendered site layer), append hashed
entries to `snapshots/manifest.jsonl`, and **fail loudly on schema drift**.
Parser self-test: `python3 capture/snapshot_official_pages.py --selftest capture/tests/fixture_report.html`.

## Rebuild & verify

```
python3 build.py     # regenerates index.html + pages/*.html from data/*.json
python3 verify.py    # row-level source check, link integrity, hash tamper-check
```

Verifier guarantees (last run): 226 data rows, 226 with an https source link,
480 internal links OK, manifest hashes match stored bytes, register arithmetic
(28 team tables → 347 rows) consistent.

Research only — not wagering advice. NCPG helpline: 1-800-697-3738.

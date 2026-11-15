# NFL Consolidated — decision-readiness dashboard

Session `arena/507da9a4-own4`. Cross-namespace consolidation of the 17+ NFL
namespaces in this repository into one **decision-readiness** view.

## What it is

The brief asks for a **decision-readiness table on the landing page: one row per
requirement, with the gate that blocks it and the number that would clear it**,
plus a clear list of questions/information/answers and a dedicated suggestions
section for review before implementing. No single prior namespace owns that
end-to-end; each delivered a partial slice of the same master requirement list.
This dashboard consolidates them.

## Contents

- **Landing page** (`index.html`) — KPIs + the decision-readiness table (one row
  per requirement: status, implementing namespace, blocking gate, clearing number,
  official source link).
- **Requirements register** — all 73 requirements across 7 groups, with evidence
  and limitation per row.
- **Questions & answers** — the open information that must be settled before any
  decision; answers not established are blank.
- **Suggestions** — proposals with options A/B/C; a verdict is required before
  implementation.
- **Verification log** — live nfl.com reads performed 2026-11-15 + build checks.
- **Source register**, **Flagged for review**.

## Reproduce

```bash
cd nfl-consolidated
python3 engine/build_site.py   # writes data/*.json + index.html + pages/*.html
python3 engine/verify.py       # hard-fails on any row without an https source link
```

Python 3 standard library only. `verify.py` enforces: every non-meta `<tbody>`
row carries an `https://` source link, blank cells are marked `unverified`,
no broken internal links, no localhost, responsible-gambling footer present,
and dataset counts reconcile.

## Status vocabulary

`met` · `partial` (evidence gap, blank + flagged) · `blocked` (no official source)
· `not_started` · `in_progress`.

## Honest constraints

No official price source exists (the NFL publishes no betting lines) and no
official depth-chart or snap-count source exists. Market columns, residuals, ROI
and reward payments stay blank; replacement depth beyond official prose is blank.
Nothing is inferred. Analytical research only, not wagering advice.

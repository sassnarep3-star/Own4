# NFL brief trace — item-by-item status of the 2026-11-18 brief

Session `arena/8440efda-own4` · branch `arena/8440efda-own4` · checked 2026-11-18 (UTC).

What it is: a traceability layer. Each of the 80 lines of the brief is mapped to the repository files that
implement it (`engine/items.py`). `engine/trace.py` checks those files and derives a status
(artifact-present / third-party-only / gap / broken-reference / process). `engine/build.py` renders five static
pages. `engine/verify.py` enforces the publication rules.

Pages: `index.html` (summary) · `pages/items.html` (all 80 lines) · `pages/gaps.html` · `pages/flagged.html` ·
`pages/sources.html` (official URLs checked on 2026-11-18, with what each returned).

Rebuild and verify (stdlib only, Python 3):

```
python3 nfl-brief-trace/engine/trace.py
python3 nfl-brief-trace/engine/build.py
python3 nfl-brief-trace/engine/verify.py
```

Rules applied: every table row carries an official https link, or a BLANK + UNVERIFIED flag. Repo links are
labelled as repo files, not official sources. No status is typed by hand; it is computed from files on disk.
The mapping in `engine/items.py` is the only hand-authored input, and every path in it is checked by `trace.py`.

Limits (stated plainly):
- "artifact-present" means a file exists and holds rows. It does not mean the content is correct or validated.
- Official links were spot-checked (5 of 6 usable); the others are register-cited and marked "not re-fetched".
- This namespace implements no model, strategy or capture. It records what exists and what is missing.
- Root navigation (`verification/build.py`, root `index.html`) is NOT edited here; that is an integration item (see COORDINATION.md).

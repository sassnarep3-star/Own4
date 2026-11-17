# nfl-req-review — Requirement re-verification round (2026-11-17)

Session `arena/ca159db5-own4`. A line-by-line re-verification of the consolidated
73-row requirement register against official sources read live on 2026-11-17, published
as a decision-readiness surface.

**Live:** https://sassnarep3-star.github.io/Own4/nfl-req-review/

## What this round did

- Read official sources live, 2026-11-17: standings, Week-11 schedule, the final
  Week-10 injury report (all 8 chunks), the official Week-10 inactive list, the
  transactions hub, the November reserve list, the game centre, the depth-chart route
  (404) and the 2025 injury archive.
- Re-verified the 73-row register row by row; **4 requirements advanced**
  (E06 blocked→partial, E14 and E21 not_started→partial, E16 not_started→partial)
  and 2 were re-confirmed as met (E25, E26).
- Computed the designation-reliability join (E14/E21) from the final Week-10 report
  against the official inactive list, with n and Wilson 95% intervals.
- Found and flagged 7 irregularities (RF-01..RF-07), including six 'Out'
  designations not corroborated by either official list, the not-yet-published
  Week-11 report, and the stale Friday capture of the Week-10 tables.

## Layout

- `data/official_reads_2026_11_17.json` — the capture: sources, timestamps,
  structured rows, computed counts, join results, sha256.
- `data/requirements_2026_11_17.json` — the 73-row register with this round's
  verdicts, gates and clearing numbers.
- `data/flags.json`, `data/sources.json` — irregularities and the source register.
- `engine/build_data.py`, `engine/build_requirements.py`, `engine/build.py`,
  `engine/verify.py` — deterministic generator and verifier (stdlib only).
- `index.html`, `pages/` — landing + decision-readiness, verification, flagged,
  sources. Every table row carries a source link; unverifiable values are blank
  and flagged.

## Reproduce

```
python3 engine/build_data.py
python3 engine/build_requirements.py
python3 engine/build.py
python3 engine/verify.py
```

Verification checks: internal links resolve, no localhost, every table row
source-linked, no placeholders, no typed counts, determinism clean.

Rules held: official sources only; no raw HTML committed (structured rows +
sha256 + timestamps — RF-18 stays open for the owner); counts computed at build
time, never typed into prose.

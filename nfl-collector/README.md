# nfl-collector — scheduled availability capture with a hash chain

Session `arena/013190b4-own4` · built 2026-11-16 · scope C-01..C-05 of `COORDINATION.md`.

This namespace implements decision **DEC-2 = A** (the handover queue's scheduled collector,
availability-desk SUG-02 A) and the supporting decisions the stalled P1 queue needed. It is the
brief's "Automate immutable multi-day availability snapshots … with retained hashes, so practice
designations can be replayed as they were known", wired as CI.

## What is here

| artefact | what it is |
|---|---|
| `data/captures/2026-11-16/` | the first session captures: the complete Week 10 league report (347 rows / 28 clubs / 14 sections, all 8 chunks), November trades (12 rows), November reserve list (25 rows), Packers depth chart (87 slot cells) — each a transcript + structured capture sealed by sha256 |
| `data/captures/ledger.json` | append-only ledger with a sha256 hash chain (`prev_entry_sha256` → `entry_sha256` → chain head); re-verified on every CI run; identical re-transcription is a no-op |
| `data/drift_expectations.json` | the pins written BEFORE capture (row counts, per-club counts, required fields, closed vocabulary, coverage floor) + the cross-capture reconciliation contract |
| `data/sources.json` | the source registry: a URL is activated only after being fetched and read in-session; candidates stay blank |
| `data/decisions.json` | the decision ledger: DEC-1..DEC-10, each adopting a peer session's written recommendation under the standing no-manual-input instruction, flagged RC-08 for owner review |
| `data/flags.json` | RC-01..RC-10 — every irregularity, published with sources, none blocking |
| `prereg/PREREG-002-mcnemar-s1-vs-better-record.md` | the frozen paired test (nfl-book SG-03 A): rule text, sample window (weeks ≥ 11), exact McNemar, gates, refusal conditions — registered BEFORE any Week 11 result existed |
| `data/prereg.json` | the registration hashes (rule file + frozen peer engine files + evaluator); CI refuses to build if any changed |
| `engine/*.py` | transcribe / collect / delta / drift / preregister / eval_mcnemar / build_site / verify_site — stdlib only, deterministic |
| `.github/workflows/nfl-collector.yml` | the schedule: Wed/Thu/Fri 17:30 UTC + Sun pre-kickoff + Mon week-close; `verify` on every push/PR; `collect` fetches, seals, parses, uploads artifacts and (on main, post-merge) commits dated captures |

## Engines

```
python3 engine/transcribe.py        # transcripts -> structured captures + ledger (idempotent)
python3 engine/drift.py             # the alarm: pins must hold; peer reconciliation; FAIL = exit 1
python3 engine/delta.py             # read-series deltas + trades/IR conflict joins -> data/derived/
python3 engine/collect.py --verify  # recompute the ledger hash chain (no network)
python3 engine/collect.py --live    # CI only: fetch, seal (sha256 + clock), parse, ledger
python3 engine/preregister.py --check
python3 engine/eval_mcnemar.py      # PREREG-002: calibration + weeks>=11 evaluation (PENDING now)
python3 engine/build_site.py        # render index + 7 pages (pure function of the artefacts)
python3 engine/verify_site.py       # links, sourced rows, coverage lines, no prices, determinism
```

## Findings a reviewer should read first

1. **The three dated reads of the Week 10 report are field-identical (0 deltas)** — the weekly
   report page is a weekly artifact; it does not change on game days. The collector cadence is
   calibrated to the Wed/Thu/Fri practice cycle, when designations actually move. (RC-06)
2. **The traded-player conflict is reproduced computationally**: Daiyan Henley (traded LAC→DEN on
   11/10) is still printed on the LAC section of the Week 10 report. Published as a conflict,
   never resolved by editing either source.
3. **15 of 25 November Reserve/Injured placements are absent from their club's report** — the
   "not listed never means available" case, now a computed join with per-row sources. (RC-04
   records the rendered view's coverage limit: the November table begins at 11/07.)
4. **Packers club depth parsed (87 cells), self-labelled "Unofficial" by the club** — captured
   verbatim, never upgraded, never rank-inferred; 31 clubs still unverified. (RC-02)
5. **The drift pins all hold**, and the capture reconciles field-by-field (347/347 keys, 0 diffs)
   against BOTH peer captures of the same page. (One documented normalization: the nfl-book peer
   prints AZ as ARI; the alias is applied only inside reconciliation, never to stored rows.)
6. **PREREG-002 is registered and PENDING** — its calibration re-grades weeks 3–10 and reproduces
   the published backtest exactly (n=104, 0.6731, 0.6346) before it may evaluate anything; the
   evaluation sample (weeks ≥ 11) is empty today, so the honest status is PENDING.

## Rules this namespace holds itself to

* Official sources only; a value not confirmable from one is blank + flagged, never inferred.
* Raw NFL HTML is never committed (RF-18 held open): captures store structured rows, hashes,
  timestamps and conflict flags; raw bytes live only in workflow artifacts.
* A read never replaces an earlier read; only deltas between reads are published.
* Club attribution is kept exactly as the page prints it, never corrected "by knowledge".
* Backtest numbers never appear on any leaderboard; the evaluator page publishes only the
  pre-registered gate vocabulary and the (pending) state.
* Peer namespaces are cited read-only; nothing outside `nfl-collector/**` is edited by the
  engines (the root nav entry is the declared integration step of the final session).

Live site (after merge): https://sassnarep3-star.github.io/Own4/nfl-collector/

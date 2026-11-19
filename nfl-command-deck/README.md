# NFL Command Deck

**Live:** https://sassnarep3-star.github.io/Own4/nfl-command-deck/
**Session:** `arena/1153eb96-own4` · built 2026-11-19 · branch `arena/1153eb96-own4`

An additive workspace inside a repository that already holds 41 overlapping NFL workspaces.
It does not re-publish peer numbers as new analysis. It does four things, all re-runnable:

1. **A frozen forecast evaluation** (`engine/model_eval.py`). Rule text, sample window,
   hyper-parameter grid, metrics and gates were committed and hash-locked in
   `prereg/PREREG-CD.md` *before* any number was computed. The engine refuses to run if that
   file changes.
2. **A permutation null** (`engine/null_test.py`) that destroys team identity and keeps the
   real schedule, to separate a real signal from a protocol artefact.
3. **A repository audit** (`engine/audit_repo.py`): link and anchor integrity across the whole tree (601 broken anchors, measured), cross-namespace result reconciliation, SHA-256 re-check of every committed official
   capture, an independent re-parse of two of them, and an explicit reachability test.
4. **An availability pipeline** (`engine/availability.py`) that joins the official Week-11
   injury report to each club's own depth chart without inferring anything, plus
   `engine/requirements.py`, which audits the 73-row peer requirement register against the
   artifacts it cites.

## Headline result

| | |
|---|---|
| Corpus | 149 completed games, weeks 1–10, every row source-linked |
| Scored forecasts (weeks 4–10) | 100, walk-forward, no leakage |
| CD-1 Brier skill vs climatology | **+0.1362**, 95% week-cluster CI [+0.0532, +0.2270] |
| Holdout (weeks 8–10, untouched) | **+0.2397** |
| Pre-registered gates | 6 of 6 passed |
| Permutation null | observed exceeds all 200 permuted schedules (95th pct +0.0309) |
| Points awarded | **0** — no price source ⇒ no ROI/CLV ⇒ no reward |

Full detail, including the two weeks where the model lost to climatology, is on the model page.
Totals are published as a **tie**: MAE 10.776 vs 10.790 benchmark, interval [−0.114, +0.089].

## What it deliberately does not claim

No ROI, no CLV, no staking result (no official price exists), no injury adjustment (one week of
availability), no parlay or prop-combo probability (no joint evidence), no starter claimed from
a depth chart, and no "verified today" — **nfl.com is unreachable from this build environment**,
so every figure comes from a committed official capture whose hash is re-checked at build time.

## Rebuild and verify

```
python3 nfl-command-deck/engine/model_eval.py     # data/eval.json      (hash-gated)
python3 nfl-command-deck/engine/null_test.py 200  # data/null.json
python3 nfl-command-deck/engine/audit_repo.py     # data/audit.json, data/link_defects.json
python3 nfl-command-deck/engine/availability.py   # data/availability.json
python3 nfl-command-deck/engine/requirements.py   # data/requirements.json
python3 nfl-command-deck/engine/build_site.py     # index.html, pages/*.html
python3 nfl-command-deck/engine/verify.py         # exit 0 = pass
```

The verifier fails on: non-deterministic output from any generator; a broken internal link or
`#anchor`; a `localhost` reference; a table row with no external source link; a surviving
placeholder; **prose that disagrees with the data file it quotes**; a flag, question or
suggestion without a source; a non-blank suggestion decision field (choosing is the owner's
call); and any edit outside this workspace's scope.

Standard library only. No network access is required or performed.

## Layout

```
prereg/PREREG-CD.md        frozen rules (hash-locked; the commit is the registration)
data/prereg_lock.json      the lock
data/eval.json             every score, interval, gate and clearing number
data/null.json             permutation null
data/audit.json            repository audit results
data/link_defects.json     all 653 broken links, page by page
data/availability.json     Week-11 join: designations × club depth charts
data/injury_rows.json      every parsed report row
data/requirements.json     73-row register with this session's verdict per row
data/flags.json            RF-01 … RF-15
data/questions.json        16 questions with known/unknown/blocks/how-to-find-out
data/suggestions.json      14 suggestions with options and a recommendation; decisions blank
data/sources.json          5 captures (hash re-checked), 4 official URLs, 4 derived artifacts
```

Research only — not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET
(https://www.ncpgambling.org/help-treatment).

# nfl-origination-lab

A pre-registered NFL line-origination competition, with the negative results published
as loudly as the positive one.

Live pages (served by the existing legacy GitHub Pages configuration from this repo root):

```
https://sassnarep3-star.github.io/Own4/nfl-origination-lab/
```

## What it does

1. **Builds a verified corpus.** 150 graded 2026 games from three stored official
   sources, unioned with an explicit alias table and a duplicate audit, reconciled to
   official standings (games implied by `sum(W+L+T)/2`, and points `sum(PF) == sum(PF)`
   both hold exactly).
2. **Freezes a rule before scoring.** `prereg/PREREG-LAB-1.json` is committed before
   `evaluate.py` runs. The verifier asserts the file is byte-identical to that commit.
3. **Runs six models over three markets** — side, then total, then moneyline — in
   walk-forward fashion, training only on strictly earlier weeks.
4. **Scores with proper scores** against a no-information benchmark, with a 90%
   week-cluster bootstrap interval and a Holm–Bonferroni adjustment over the whole
   declared family.
5. **Refuses to stake.** No officially sourced price with a known capture time exists in
   the repository, so the staking division is published empty. No `-110` assumption, no
   simulated bankroll.
6. **Measures availability, does not guess it.** Two dated injury captures parsed
   independently; depth slots measured as groups; replacement depth computed only where
   both ranks exist; the backup-deficiency feature is left unbuilt because the brief's
   own precondition (a depth-order source for all 32 clubs) fails on one club.

## Result

| Market | Metric | Best model | Skill | 90% week-cluster bound | Holm p | Verdict |
|---|---|---|---|---|---|---|
| Moneyline | Brier skill | M2 | **+0.1509** | [+0.0795, +0.2143] | 0.0085 | survives |
| Total | Brier skill at τ=44 | M2 | +0.0320 | [-0.0405, +0.1012] | 1.0000 | does not survive |
| Side | CRPS skill | M1 | +0.0187 | [-0.0252, +0.0636] | 1.0000 | does not survive |

That is the honest shape of the result: a calibrated win probability with real skill, and
no demonstrable skill on the size of the win or the total points.

## Reproduce

```sh
python3 nfl-origination-lab/engine/parse_availability.py
python3 nfl-origination-lab/engine/corpus.py
python3 nfl-origination-lab/engine/evaluate.py
python3 nfl-origination-lab/engine/price_policy.py
python3 nfl-origination-lab/engine/depth.py
python3 nfl-origination-lab/engine/governance.py
python3 nfl-origination-lab/engine/registers.py
python3 nfl-origination-lab/engine/build.py
python3 nfl-origination-lab/engine/verify.py     # publication gate, exits non-zero on failure
```

`verify.py` checks ten things, including that no-lookahead actually holds (by poisoning
the future and proving the predictions do not move) and that the gate is capable of
failing (by leaking the future on purpose and proving the predictions do move).

## Session constraint, stated plainly

This session's sandbox has **no HTTPS egress to nfl.com**. `curl -sI
https://www.nfl.com/injuries/` returns nothing. Every number published here is either a
stored capture already in this repository (with its own URL and date) or a computation
over one. Nothing was re-typed from memory, and no value that required a live read was
filled in. That limitation is on the landing page, on the flagged page, and in
`COORDINATION.md`.

## Scope

Everything this session wrote lives under `nfl-origination-lab/**`, plus:
- an append-only claim/log block in `COORDINATION.md`
- one additive navigation group in `index.html` and `verified/*.html`, inserted through
  the generator's own `_adopt_foreign_nav_groups` mechanism rather than by hand

No peer namespace, no peer data file, and no peer engine was edited.

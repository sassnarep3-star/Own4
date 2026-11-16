# PREREG-002 — Paired exact McNemar test: model side (S1) vs better-record baseline

**Registered:** 2026-11-16 (UTC), by session `arena/013190b4-own4`, namespace `nfl-collector/`.
**Registration rule:** the sha256 of this file, recorded in `data/prereg.json`, is the registration.
Any later edit to this file changes its hash and fails `engine/preregister.py --check` in CI.
**Status of the data at registration:** the official results feed (`nfl-book/data/results_feed.json`)
contained weeks 1–10 of the 2026 regular season only (137 games). NO Week 11 game result existed in
this repository at registration, so nothing below has seen the evaluation data.

## Why

`nfl-book` published a POST-HOC diagnostic: on the same 104 decided games, the model side (S1,
walk-forward accuracy 0.6731) edged the "better record" baseline (0.6346) by +3.8pp, but that
comparison was made after both arms had already seen the sample (flagged as amendment A2 /
post-hoc). A post-hoc comparison cannot support a claim. This pre-registration freezes the paired
test so it can be evaluated forward, once, on data that did not exist at registration.

## Frozen rule text

1. **Arms.** Arm M = the `nfl-book` S1 walk-forward side pick exactly as implemented in
   `nfl-book/engine/backtest.py` at registration (`pick_home = p_home >= 0.5`; a game with
   `actual_margin == 0` is a push and is excluded from both arms). Arm B = the better-record
   baseline exactly as implemented in `nfl-book/engine/backtest.py::_posthoc_record_baseline`:
   for each game, compute each club's wins/losses from official results of games with
   `week < f["week"]` only; pick the club with the larger win-minus-loss differential; on a
   differential tie pick HOME; exclude pushes.
2. **Sample window.** 2026 NFL regular-season games with `week >= 11`, graded only from official
   results published in `nfl-book/data/results_feed.json` after this registration (weeks 1–10 are
   NEVER part of the sample). Each graded game enters once, at the week it was played.
3. **Statistic.** Exact McNemar on the discordant pairs: b = games where M correct and B wrong;
   c = games where M wrong and B correct. One-sided exact p = P[X >= b], X ~ Binomial(b+c, 0.5),
   computed with exact integer arithmetic. Arms' accuracies are also reported with Wilson 95% CIs.
4. **Gate (declared now).**
   - QUALIFYING: p < 0.05 AND (b + c) >= 30 → "model beats the better-record baseline on
     out-of-registration data" is publishable as a claim, with the exact p and both CIs.
   - PROVISIONAL: p < 0.05 AND 10 <= (b + c) < 30 → reported as provisional evidence only; no claim.
   - NOT EVALUABLE: (b + c) < 10 → no test is reported, only n and the pending status.
5. **Refusal conditions (evaluator MUST abort).** (a) any game with `week < 11` enters the sample;
   (b) the peer engine files whose hashes are frozen below have been edited; (c) the sample window
   rule is amended. A refusal is loud (exit non-zero), never silent.
6. **Multiplicity.** This is one registered comparison (family of 1). If further paired tests are
   registered later, the family is reported together under a Benjamini–Hochberg adjustment across
   the registered family only.
7. **Evaluation cadence.** The evaluator runs on every collector capture; it evaluates only
   settled games. No interim peeking changes the rule; results accumulate, the gate is evaluated
   on the accumulated sample and the evaluation history is appended, not overwritten.

## Frozen implementation hashes (registration-time)

| file | sha256 (first 16 hex) | role |
|---|---|---|
| nfl-book/engine/model.py | *(recorded by engine/preregister.py at freeze time)* | ratings used by Arm M |
| nfl-book/engine/backtest.py | *(recorded by engine/preregister.py at freeze time)* | pick + baseline implementations |
| nfl-book/engine/common.py | *(recorded)* | load/save used by the pipeline |
| nfl-collector/engine/eval_mcnemar.py | *(recorded)* | the evaluator itself |

The evaluator refuses to run if any current hash differs from the frozen hash (refusal condition
(b)). If the peer engine legitimately changes, a NEW pre-registration supersedes this one; this
one is never edited.

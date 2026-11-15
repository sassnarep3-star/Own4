# NFL Decision Desk — Executive Summary

**Session** `arena/e0ed20d1-own4` · **Built** 2026-11-15T23:24:27Z · **Scope** `nfl-decision-desk/` (fully additive)
**Live** https://sassnarep3-star.github.io/Own4/nfl-decision-desk/

---

## 1. The one-paragraph version

This workspace originates its own NFL lines (side → total → moneyline), scores them with proper
scores against a **vig-free market benchmark** and three **control baselines**, and reports the
result honestly: **the model loses to the market** on 104 walk-forward games (Brier 0.2525 vs
0.2147, paired week-cluster interval entirely below zero). No strategy qualifies for a reward,
because the pre-registered coverage floor is 300 games and the largest sample is 104. Of the 80
requirement lines in the brief, **39 are done, 16 partial, 25 blocked** — and every blocked row
names both the gate that blocks it and the exact quantity that would clear it.

## 2. What was verified, and how

| Claim | Evidence | How it was checked |
|---|---|---|
| The corpus is 136 settled games | frozen third-party archive, weeks 1–9 | counted; weeks 1–9 sums to 136 |
| **All 32 clubs match the official standings** | 14 exact + 18 explained = 32, **0 unexplained** | each differing club corrected *only* by adding its official week-10 final; corrected W-L-T and PF/PA match the official cell exactly |
| The official page disagrees with the archive | 9 week-10 finals at capture, **8 postdate the archive** | official week-10 page read this session at the stated clock |
| The injury report carries 347 rows, not 254 | 28 of 28 Week-10 clubs read | verbatim transcription, published blanks kept blank |
| Two games are neutral-site | Melbourne Cricket Ground; FC Bayern Munich Stadium | official game centres |

Sources: [standings](https://www.nfl.com/standings/league/2026/REG) ·
[week 10](https://www.nfl.com/schedules/2026/by-week/week-10) ·
[injuries](https://www.nfl.com/injuries/) ·
[SF@LA](https://www.nfl.com/games/49ers-at-rams-2026-reg-1) ·
[NE@DET](https://www.nfl.com/games/patriots-at-lions-2026-reg-10) ·
[archive](https://github.com/nflverse/nfldata)

## 3. The results, stated plainly

| Measure | Value | n | Reading |
|---|---|---|---|
| Brier, model | 0.2525 | 104 | worse than climatology (0.2496) |
| Brier, vig-free market | 0.2147 | 104 | the benchmark wins |
| Paired interval (market − model) | **[−0.0753, −0.0066]** | 104 | excludes zero: not luck |
| Total MAE, PR-02 / PR-03 | 11.311 / 12.012 | 104 | market: 10.414 |
| Our spread vs closing line, MAE | 4.553 | 104 | a pricing distance, not a skill measure |
| Luck panel: correct vs expected | 54 vs 58.49 | 104 | the hit count is *inside* its own chance range |
| Strategies qualified | **0 of 6** | 104 | floor is 300 |
| Reward units awarded | **0 of 1,000** | — | escrowed, not withheld arbitrarily |

## 4. What could not be measured — and why that is the finding

Four central ideas in the brief need data this repository does not have. Each is published as
**blocked with a named feed**, never estimated:

1. **Personnel/injury ablations** need an archived availability *series*. One capture cannot be
   ablated chronologically without leaking the future into the past.
2. **Backup-depth deficiency (2nd/3rd/4th string)** needs a per-club depth rank or snap counts.
   The official injury report has **no depth column at all**, and the club depth-chart route was
   recorded as 404 by an earlier session.
3. **Parlays and prop combos** need a validated joint probability or an n ≥ 100 dependence
   estimate. Multiplying marginal probabilities is prohibited in writing, not just avoided.
4. **CLV-based staking scores** need verified closing prices. The NFL publishes none.

## 5. Irregularities found and handled

| # | Irregularity | Handling |
|---|---|---|
| I01 | Scores come from a third-party archive | labelled on every row; standings cross-check published |
| I02 | Peer feeds disagree: 136 / 137 / 150 settled games | all three explainable as capture times; none states its clock |
| I03 | The brief's "6 of 254 designated" does not reproduce (171 of 347) | published as observed |
| **I04** | **Two international games give home field to a team playing abroad** | **FX-01 published as a defect, fix pre-registered not applied** |
| I10 | A rest-effect correlation was an artefact (14 of 120 games) | automatic guard added; published NOT ROBUST |

Full list with sources: `pages/flagged.html`.

## 6. What decision is actually available today

One decision blocks progress, and it is not a modelling decision: **where do prices come from?**
Every ROI, CLV and staking claim is hypothetical until that is answered. The second is the results
feed — turning the third-party archive into officially verified rows is mechanical but needs 136
page reads. Both sit in `pages/suggestions.html` with options and a deliberately blank verdict.

## 7. Verification is re-runnable

```
cd nfl-decision-desk
python3 engine/build_corpus.py && python3 engine/model.py && python3 engine/leaderboard.py \
 && python3 engine/prices.py && python3 engine/correlations.py && python3 engine/availability.py \
 && python3 engine/fixtures.py && python3 engine/governance.py && python3 engine/site.py \
 && python3 engine/verify.py
```

Current gate output: **14 pages · 616 table rows · 616 with an https source · 226 local refs ·
0 broken · 0 localhost · 14 unique titles → PASS**. CI runs the same sequence and then fails on
any diff between the rebuild and the committed pages.

---

*Research notebook. No wagering is offered. Staking figures use an assumed −110 price and are
labelled hypothetical everywhere. Values that could not be sourced are blank and listed on the
Flagged for Review page.*

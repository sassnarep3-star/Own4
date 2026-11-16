# NFL source audit — executive summary

**Namespace:** `nfl-sources/` · **Session:** `arena/f7545de2-own4` · **Branch base:** `1dbde90`
**Live site:** `https://sassnarep3-star.github.io/Own4/nfl-sources/pages/`
**Registration commit:** `a4f26f5` (frozen before any result was computed) · **Built:** 2026-11-16

---

## The one-line answer

We originated our own line for all 13 Week 11 fixtures from a model refitted weekly on page-verified
official results, tested it on 116 walk-forward forecasts, and it beats a coin flip without yet being
provably better than one: Brier skill 0.1198 with a week-cluster 95% interval of
**[−0.0148, +0.2635]**. A rule with no ratings at all lands 2.6 accuracy points behind it, inside noise.
No official NFL page publishes a price, so no return, no staking and no reward is payable — and that is
published as a result, not hidden as a gap.

## What is actually built and verified

| Area | State | Evidence |
|---|---|---|
| Official results corpus | **148 final games, weeks 1–10** | `data/results.json`; 148 games = official W 147 + T 1; PF = PA = 6 824; 0 of 160 club fields disagree with the official standings |
| The brief's 136-game log | **exactly reproduced** | weeks 1–9 print 16+16+16+16+15+14+14+14+15 = 136 FINAL games |
| Pre-registration | **frozen** | `PREREGISTRATION.md`, commit `a4f26f5`, never edited after registration |
| Walk-forward backtest | **116 forecasts, 115 graded** | `data/backtest.json`; weekly refit, no game sees its own week |
| Leakage test | **pass** | mutating every result from week W onward changes **0** of the forecasts before W (cutoffs 4, 6, 8) |
| Deterministic rebuild | **pass** | 12 data files rebuild byte-identically |
| Our own Week 11 line | **13/13 fixtures, two dated snapshots** | `data/lines.json`; side → total → moneyline in that order, both snapshots |
| Venues | **13/13** | `data/venues.json`; transcribed from each official game-centre Game Info block |
| Correlations | **5 computed with n, 4 blank with the number that would clear them** | `data/correlations.json` |
| Requirements | **27 met, 7 partial, 17 blocked, 14 out of scope here, 2 owned by peers, 3 rejected as specified** (70 total) | `data/requirements.json` |
| Suggestions | **18, none implemented, verdict column deliberately empty** | `data/suggestions.json` |
| Questions | **12, each naming who can answer it and what it unblocks** | `data/questions.json` |
| Flagged for review | **15 irregularities, published not corrected** | `data/flags.json` |
| Verification gate | **38 of 38 checks pass** | `data/verification.json`; `engine/verify.py` exits non-zero on any failure |

## The four numbers that matter

1. **Brier 0.22006** against 0.25000 for a coin flip and 0.26085 for the home-team prior.
2. **Skill interval [−0.0148, +0.2635]**: the lower bound is below zero, so gate **G2 fails**.
3. **Paired model-minus-control difference +0.0261, interval [−0.0371, +0.0855]**: the ratings are not
   yet shown to be worth their complexity.
4. **Coverage 116 of 300**: gate **G1 fails**, so nothing can be promoted regardless of the other numbers.

## What we refused to do

- Publish an ROI. There is no citable price. Every figure that would need one is blank with its reason.
- Estimate a market line, a total, or a residual against a market that does not exist on any official page.
- Import a depth chart, a snap count, a roof type or an injury history from a site we could not cite.
- Give a reward. G1 and G2 are both open, so the payable reward is **0** and the register says why.
- Mark a requirement "met" without an artefact and an official link behind it.
- Fill in a suggestion verdict. Choosing is the owner's decision, and an empty column is the honest state.

## Corrections made during this work (all published on the site)

- A **sign error** in the rating table made good defences look bad by roughly twice their true margin;
  fixed, re-run, and recorded as a flag.
- The **American price** on each fixture is derived from the *published* probability, so a reader who
  recomputes it always gets the printed value; the consistency check is now automated.
- The `update` cutoff was **missing one rating column**; caught by a new shape check, which now fails the
  build if any club row disagrees on its fields.
- The corpus size contradiction is **resolved in the source's favour**: 136 is exactly weeks 1–9.

## What a reviewer should do next

1. Read the landing page: one row per requirement, with its blocking gate and clearing number.
2. Open **Suggestions** and choose, or reject, each of the 18 rows. Nothing moves until then.
3. Answer **Q01** (price source) first. It unblocks the largest cluster: R01, R04, R18, R57.
4. Treat **G1** as the clock, not the verdict: 184 more graded fixtures are needed before any strategy can
   be promoted, whatever the accuracy looks like in the meantime.

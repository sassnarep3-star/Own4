# PREREG-CD — freeze before evaluation

**Registration:** session `arena/1153eb96-own4`, 2026-11-19 (UTC).
**Rule:** this file's git blob is the registration. `engine/model_eval.py` refuses to run if the
SHA-256 of this file does not match `data/prereg_lock.json`. Editing a rule after seeing a result
breaks the build — that is the point.

The evaluation below was written **before** any number in `data/eval.json` was computed. No result
from this evaluation was known at the time of writing.

## 0. Data

Input: `nfl-live-board/data/corpus_2026.json` — 149 completed 2026 regular-season games,
weeks 1–10, every row carrying an `nfl.com` per-game URL.
This file is read **read-only**. No game is added, removed or edited.

Known and accepted limitations (they are part of the registration, not discovered later):

1. The corpus is inherited from peer workspaces; this session cannot re-read nfl.com to confirm it
   (sandbox egress to `www.nfl.com` is refused — see `RF-02`). Every result is therefore
   *conditional on the committed corpus being correct*.
2. Weeks 1–9 rows are marked `inherited_per_game_url_feed`; only week 10 was transcribed directly.
3. The corpus has no point spreads and no prices. **No ROI, CLV or staking result is computed or
   claimed.** Equity is not modelled. This is a forecast-skill evaluation only.

## 1. Forecast target

Binary outcome `y = 1[home_pts > away_pts]` for every corpus game. Exact ties are excluded from
scoring and counted separately (the NFL permits ties; a tie is not a home win).

## 2. Candidate models (all frozen)

| id | model | market | definition |
|----|-------|--------|------------|
| CD-1 | opponent-aware point rating | margin → moneyline | ridge least squares on point margin: `margin = h + s_home − s_away`; `s` = 32 team ratings, `h` = home edge; ridge λ fixed per §5 |
| CD-2 | constant home edge | margin → moneyline | `margin = mean_margin(train)`; no team information |
| CD-3 | opponent-aware total | game total | `total = μ + o_home + d_away + o_away + d_home`; `o` = offense, `d` = defense, ridge λ per §5 |
| C-1 | coin | control | `p = 0.5` |
| C-2 | always home | control | `p = 1.0` (this is *not* a forecast; it is the control the brief asks for) |
| C-3 | climatology | **benchmark** | `p = home win rate over the training window` |

`p(home) = Φ(margin / σ)` where `σ` = residual standard deviation on the training window, computed
from the training residuals only. Φ is the standard normal CDF (`math.erf`).

## 3. Protocol — expanding-window walk-forward, strictly chronological

For every target week `w ∈ {4, …, 10}`: fit on **weeks < w only**, forecast week `w`.
No row is ever used to forecast itself or an earlier week. Scoring window = weeks 4–10.

Hyper-parameter (ridge λ) selection uses **weeks 4–7 only**, from the declared grid
`{1, 3, 10, 30, 100}`, and the selected value is then frozen for weeks 8–10.
Weeks 8–10 are the **final holdout**: they are never used for any choice made by this script.

## 4. Metrics, uncertainty, multiplicity — all pre-declared

- Primary: **Brier score** and **Brier Skill Score** vs C-3 climatology, `BSS = 1 − BS/BS_bench`.
- Uncertainty: **week-cluster bootstrap** (resample the 7 target weeks with replacement,
  2 000 replicates, seed 20261119) → percentile 95% interval for BSS, and
  `p_boot = P(BSS* ≤ 0)`. A game-level (iid) bootstrap is also reported and explicitly labelled
  optimistic, because games in a week share conditions.
- Multiplicity: Holm–Bonferroni over the 3 model p-values (CD-1, CD-2, CD-3), declared now.
- Total model: MAE vs the training-window mean total, same week-cluster bootstrap on the
  MAE difference. Proper-score treatment of totals is out of scope (no totals market exists here).

## 5. Gates — decided now, not after

A candidate **qualifies** only if **all** hold:

| gate | rule |
|------|------|
| G1 skill | `BSS > 0` on the scoring window (weeks 4–10) |
| G2 holdout | `BSS > 0` on the final holdout (weeks 8–10) alone |
| G3 evidence | week-cluster bootstrap 95% lower bound on BSS `> 0` |
| G4 multiplicity | Holm-adjusted `p_boot < 0.10` |
| G5 sample | ≥ 90 scored forecasts |
| G6 controls | beats C-1 (coin) and C-2 (always-home) on Brier |

**No gate is waived after the fact.** If a model fails, it is published as failing with the number
that would clear it. No staking, no reward, no pick list is produced for a failing model.

## 6. What this registration explicitly forbids

- Reporting raw win rate or accuracy as a success metric.
- Using an assumed price (−110) to manufacture ROI.
- Re-using the holdout for model selection.
- Adding a model after seeing these results and scoring it on the same window. Any new model needs
  a new pre-registration with a prospective window that begins after its registration date.

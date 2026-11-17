# NFL Live Board — executive summary

Workspace: `nfl-live-board/` · live at `https://sassnarep3-star.github.io/Own4/nfl-live-board/`
Session: `arena/925796f5-own4` · snapshot **2026-11-17** · every artefact rebuilt by `engine/run_all.sh`
and gated by `verify.py`.

## What was actually established in this session

| # | Result | How it is verified |
|---|---|---|
| 1 | **A 149-game verified results corpus.** Weeks 1–9 are the brief's "136-game log"; Week 10 adds 13 finals transcribed from the official scores page. | 192/192 reconciliation checks against the official standings, and the games-played identity is exact: sum(W+L+T)/2 over 32 clubs = 149. |
| 2 | **The repository's committed feed was incomplete.** It held 136 games of weeks 1–9 and only 1 of the 13 Week-10 finals. | Flagged F-02; the two independent committed feeds agreed on all 137 games they shared (0 disagreements). |
| 3 | **Own lines for all 13 Week-11 fixtures, in the demanded order** — side, then total, then a moneyline *derived* from the side so the three stages cannot disagree. | `data/origination_week11.json`; every forecast stores p plus its inputs. |
| 4 | **A five-parameter baseline that beats its naive comparator** on the side (MAE 9.36 vs 10.55) and on accuracy (0.647 vs 0.466 always-home). | Walk-forward, 116 forecasts, weeks 3–10. |
| 5 | **A proper-score competition with the luck taken out.** Five strategies pre-registered before scoring; 0 qualify; 0 of 1000 points awarded. | Brier skill +0.1253, week-clustered 90% CI [0.0143, 0.2384], unadjusted p 0.033 **→ Holm-adjusted p 0.147 across 5 trials**. The adjustment is the reason it is not a result. |
| 6 | **The control floor is computed, not asserted.** Luck-only strategies reached a Brier skill of up to 0.035 on this n. | Two controls scored in every run. |
| 7 | **Independent availability verification.** 96 rows across 8 clubs re-read from the live official page: 96 agree, 0 disagree. | `data/availability_verification.json`; only 8 of the clubs on the page were re-read, and the page says so. |
| 8 | **The reserve list is captured** (27 Reserve/Injured moves), so "not listed on the injury report" can no longer be read as "available". | F-05: Malik Willis and TreVeyon Henderson are on IR while absent from the weekly report. |

## What is deliberately blank, and why

| Column | Reason | What would fill it |
|---|---|---|
| Market line, difference, ROI, CLV | No official page publishes a spread, total or moneyline (F-01). Six requirements are blocked on this one gap. | One price source with its terms read before ingestion. |
| Depth rank, replacement name, 2nd/3rd/4th string | No official depth chart and no official snap-count table were found (F-07). | A verified depth source, or game-book participation for every fixture. |
| Injury "surprise" (all 347 rows) | A surprise is observed minus expected; this season has **one** dated snapshot (F-08). | Three dated captures in one week. |
| Availability ablation | One snapshot cannot be compared with a model that never saw it (F-04). | ≥8 weeks of dated availability joined to results. |
| Parlay and prop divisions | Multiplying marginal probabilities is invalid under dependence; no joint probability or prop market exists. | A joint model validated out of holdout, plus a price. |

## The three decisions that unblock the most

1. **A price source** — unblocks every ROI, CLV and residual column, the parlay division and stage 2 of the leaderboard. (`SG-01`, `Q01`)
2. **Participation from game books** — unblocks the availability graph, replacement depth and the matchup matrix. (`SG-02`, `Q02`)
3. **The dated reserve list on the daily capture** — makes every availability read honest. (`SG-03`)

## Where to read more

* Landing page with the decision-readiness table: `nfl-live-board/index.html`
* All 70 requirements with gate and clearing number: `nfl-live-board/pages/requirements.html`
* Flagged for review (14 items, none blocking): `nfl-live-board/pages/flagged.html`
* Questions and information gaps: `nfl-live-board/pages/questions.html`
* Suggestions, none implemented: `nfl-live-board/pages/suggestions.html`
* Repository audit, line by line: `nfl-live-board/pages/repo-review.html`

---

*Research only — no wagering is offered and nothing here is betting advice. National Problem Gambling
Helpline 1-800-697-3738 · https://www.ncpgambling.org/help-treatment/*

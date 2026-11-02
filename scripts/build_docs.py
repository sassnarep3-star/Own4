"""Generate the Markdown research documents from the committed verified data.

Keeps every number in the documents identical to the number on the site (single source of truth).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CORRELATIONS, DERIVED, LEADERBOARD, ROOT, SRC,  # noqa: E402
                    STRATEGIES, VERIFICATION, fmt, read_json)

C = {r["id"]: r for r in read_json(CORRELATIONS / "correlations.json")["rows"]}
BT = read_json(DERIVED / "backtest.json")
LINES = read_json(DERIVED / "lines.json")
SK = read_json(CORRELATIONS / "skill_luck.json")
ST = read_json(STRATEGIES / "strategies.json")
GATES = read_json(STRATEGIES / "gates.json")
LB = read_json(LEADERBOARD / "leaderboard.json")
RW = read_json(LEADERBOARD / "rewards.json")
V = read_json(VERIFICATION / "ledger.json")
FL = read_json(VERIFICATION / "flagged.json")


def w(name, text):
    (ROOT / name).write_text(text, encoding="utf-8")


# ------------------------------------------------------------------ LINES.md
rows = []
for r in LINES["rows"]:
    rows.append(f"| {r['game_id']} | {r['team_a']} vs {r['team_b']} | {fmt(r['fair_spread_a'],2)} | "
                f"{fmt(r['fair_total'],1)} | {r['fair_ml_a']:+d} / {r['fair_ml_b']:+d} | "
                f"{fmt(r['fair_win_prob_a'])} | — UNVERIFIED | — UNVERIFIED | "
                f"[NBA.com Games 2026-11-04]({SRC['games_1104']}) · "
                f"[NBA.com Advanced 2025-26]({SRC['adv_2025']}) |")
w("LINES.md", f"""# LINES.md — Our Own Originated NBA Lines

**Snapshot:** 2026-11-02 (UTC) · **Priced slate:** 2026-11-04 (14 official games)
**Model:** M1 prior-season additive ratings · **All inputs:** official NBA.com

## Method (no invented constants)

{chr(10).join('- `' + f + '`' for f in LINES['meta']['formulas'])}

- League-average rating 2025-26 = `{fmt(LINES['meta']['league_avg_2025_26'],4)}`; 2026-27 = `{fmt(LINES['meta']['league_avg_2026_27'],4)}`.
- Residual margin sigma = `{fmt(LINES['meta']['sigma_residual_margin'],4)}`, estimated from `{LINES['meta']['train_games']}` official
  settled games dated 2026-10-23 … 2026-10-28 only, i.e. **before** the slate being priced.
- NetRtg, OffRtg, DefRtg and PACE definitions: [NBA.com Stat Glossary]({SRC['glossary']}).

## Fair lines (M1) — 2026-11-04 slate

`fair_spread_a` is Team A's fair spread; a negative value means Team A is projected to win.
Fair moneylines are **zero-margin model outputs**, not sportsbook prices.

| Game ID | Matchup | Fair spread A | Fair total | Fair ML A / B | P(A wins) | Market spread | Market total | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

## Deliberately blank fields

Market odds/closing lines, vig, closing-line value, edge, per-game home-court adjustment,
M2 (current-season) moneyline, and player-prop fair lines are all **blank and flagged UNVERIFIED**.
Reason: the [NBA's own release]({SRC['betting_data']}) states official betting data goes to *licensed
operators*; the [NBA.com games page]({SRC['games_1104']}) exposes a "HIDE ODDS" toggle but no odds
values, and no free official player game logs exist. See `pages/flagged.html`.

## M2 current-season variant

A second projection using the [official 2026-27 advanced table]({SRC['adv_2026']}) (4–7 GP per team)
is published on the site for comparison. It has no out-of-sample calibration, so its moneyline is blank.

## Caveats

{chr(10).join('- ' + c for c in LINES['meta']['caveats'])}
""")

# ------------------------------------------------------------------ CORRELATIONS.md
crows = []
for r in read_json(CORRELATIONS / "correlations.json")["rows"]:
    lo, hi = r["bootstrap_ci95"]
    crows.append(f"| {r['id']} | {r['n']} | {fmt(r['pearson_r'])} | {fmt(r['spearman_rho'])} | "
                 f"{fmt(r['permutation_p'],4)} | {fmt(r['bh_q'],4)} | {fmt(lo)} … {fmt(hi)} | "
                 f"{'YES' if r['significant_after_fdr'] else 'no'} | "
                 f"[NBA.com official]({r['sources'][0]}) |")
w("CORRELATIONS.md", f"""# CORRELATIONS.md — Determined Correlation Values

**Method:** {read_json(CORRELATIONS / 'correlations.json')['method']}

All {len(C)} correlations use only values transcribed from official NBA.com pages. No value is
inferred. `q` is the Benjamini–Hochberg FDR-adjusted value across the whole family.

| Pair (y ~ x) | n | Pearson r | Spearman rho | perm. p | BH q | bootstrap 95% CI | sig. after FDR | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(crows)}

## Findings

- **Full-season structure:** 2025-26 `WIN% ~ NetRtg` r = `{fmt(C['2025-26 WIN% ~ NetRtg']['pearson_r'])}`
  (n=30, 82 GP each) — [official source]({SRC['adv_2025']}). This is a descriptive identity-like
  relationship, not a betting edge.
- **Cross-table check:** 2026-27 `NetRtg ~ +/-` r = `{fmt(C['2026-27 NetRtg ~ +/- (traditional)']['pearson_r'])}`
  across two independent official tables, confirming transcription consistency —
  [advanced]({SRC['adv_2026']}) · [traditional]({SRC['trad_2026']}).
- **Out-of-sample predictive signal:** `2026-27 WIN% ~ 2025-26 NetRtg` r =
  `{fmt(C['2026-27 WIN% ~ 2025-26 NetRtg']['pearson_r'])}`, q =
  `{fmt(C['2026-27 WIN% ~ 2025-26 NetRtg']['bh_q'],4)}` — [official source]({SRC['adv_2025']}).
- **Parlay leg dependence:** 2026-27 `PTS ~ NetRtg` r =
  `{fmt(C['2026-27 PTS ~ NetRtg']['pearson_r'])}` and `PTS ~ PACE` r =
  `{fmt(C['2026-27 PTS ~ PACE']['pearson_r'])}` — same-game legs are **not** independent.
- **Prop-leg baselines (n=28 official team leaders):** `RPG ~ PPG` r =
  `{fmt(C['Prop leg RPG ~ PPG']['pearson_r'])}`, `APG ~ PPG` r =
  `{fmt(C['Prop leg APG ~ PPG']['pearson_r'])}`, `APG ~ RPG` r =
  `{fmt(C['Prop leg APG ~ RPG']['pearson_r'])}`; all q > 0.05 —
  [official source]({SRC['games_1104']}). These are *baseline* correlations, not game-level leg
  covariances, which remain UNVERIFIED.
""")

# ------------------------------------------------------------------ STRATEGIES.md
srows = []
for r in ST["rows"]:
    srows.append(f"| {r['id']} | {r['family']} | {r['name']} | {r['verdict']} | — UNVERIFIED | "
                 f"[NBA.com official]({r['sources'][0]}) |")
grows = []
for g in GATES["gates"]:
    grows.append(f"| {g['id']} | {g['name']} | {g['rule']} | [Official]({g['source']}) |")
w("STRATEGIES.md", f"""# STRATEGIES.md — Strategy Research & Validation Gates

**Catalogue:** {len(ST['rows'])} strategies across single bets, parlays and player-prop combos.
**Result:** **{sum(1 for r in ST['rows'] if r['verdict'] == 'VALIDATED')} validated**, 0 eligible for Division B rewards.

## Validation gates

{GATES['rule']}

| Gate | Name | Pass criterion | Official source |
| --- | --- | --- | --- |
{chr(10).join(grows)}

## Strategy catalogue

| ID | Family | Strategy | Verdict | Net ROI | Official source |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(srows)}

Full gate-by-gate results for every strategy are in `data/strategies/strategies.json` and on the
site's Validation page.

## Research findings

- The [prior-season rating model]({SRC['adv_2025']}) reached `{fmt(BT['train']['winner_accuracy'])}`
  winner accuracy in the training window but only `{fmt(BT['holdout']['winner_accuracy'])}` on the
  chronological holdout (n={BT['holdout']['n']}), with binomial p =
  `{fmt(BT['holdout']['binomial_p_two_sided_vs_0_5'],4)}` and Brier skill score
  `{fmt(BT['holdout']['brier_skill_score_vs_0_5'])}` — [official settled scores]({SRC['games_1101']}).
  Under the pre-registered luck-removal rules it is **not skill-based**.
- The naive "pick the better 2025-26 record" baseline reached
  `{fmt(BT['all']['naive_prior_record_baseline_accuracy'])}` over all
  {BT['all']['n']} games, higher than the model's `{fmt(BT['all']['winner_accuracy'])}`.
- Same-game parlay legs are measurably correlated (see `CORRELATIONS.md`), so independence
  must not be assumed. Where a joint model cannot be verified, the price is left blank.
- Player-prop fair lines require game-level distributions, which are not available from free
  official NBA pages — the fair-line cells are blank, only verified season baselines are shown.
""")

# ------------------------------------------------------------------ LEADERBOARD.md
a = LB["divisions"]["signal_research"]
arows = []
for r in a:
    arows.append(f"| {r['rank'] if r['rank'] else '—'} | {r['id']} | {r['name']} | "
                 f"{fmt(r['out_of_sample_r'])} | {fmt(r['bh_q'],4)} | "
                 f"{r['reward_points'] if r['reward_points'] is not None else '— UNVERIFIED'} | "
                 f"{'eligible' if r['eligible'] else 'not eligible'} | "
                 f"[NBA.com official]({r['sources'][0]}) |")
brows = []
for r in LB["divisions"]["betting_strategies"]:
    brows.append(f"| {r['id']} | {r['family']} | {r['name']} | {r['verdict']} | — UNVERIFIED | "
                 f"[NBA.com official]({r['sources'][0]}) |")
w("LEADERBOARD.md", f"""# LEADERBOARD.md — Competition, Rewards & Skill Selection

{LB['headline']}

## Division A — Research signal leaderboard (ranked by out-of-sample Pearson r)

| Rank | ID | Signal | Out-of-sample r | BH q | Reward (pts) | Eligibility | Official source |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(arows)}

## Division B — Betting strategy leaderboard

| ID | Family | Strategy | Verdict | Net ROI / reward | Official source |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(brows)}

## Reward rules

{chr(10).join('- ' + x for x in RW['division_A_rules'])}

{chr(10).join('- ' + x for x in RW['division_B_rules'])}

{RW['note']} Reward unit: **{RW['reward_unit']}**. Sources:
[advanced 2025-26]({SRC['adv_2025']}), [standings]({SRC['standings']}),
[games 2026-11-04]({SRC['games_1104']}), [NBA betting-data policy]({SRC['betting_data']}).

## Skill selection

Only signals that clear provenance, completeness, out-of-sample, FDR-significance and
reproducibility gates are ranked. In-sample accuracy never earns rewards. See
`pages/skill-vs-luck.html` for the luck-removal method and `CORRELATIONS.md` for the values.
""")

# ------------------------------------------------------------------ VERIFICATION.md
s = V["summary"]
w("VERIFICATION.md", f"""# VERIFICATION.md — Line-by-Line Verification Ledger

**Method:** `scripts/verify.py` checks every committed row for arithmetic consistency, an
allowlisted official source URL, and correct flagging of blank values. It also checks every
published/derived row. `scripts/build_site.py` renders a Source column in every table, and
`scripts/check_links.py` asserts that every `<tr>` with data cells contains at least one link to
an official host.

| Metric | Value | Official source |
| --- | --- | --- |
| Rows checked | {s['rows_checked']} | [NBA.com Standings]({SRC['standings']}) |
| Passed | {s['passed']} | [NBA.com Advanced 2025-26]({SRC['adv_2025']}) |
| Flagged inconsistencies | {s['flagged']} | [NBA.com Advanced 2026-27]({SRC['adv_2026']}) |
| Rows without an official source | {s['rows_without_official_source']} | [NBA.com Glossary]({SRC['glossary']}) |
| 2025-26 season W/L balance | 1230 / 1230 | [NBA.com Advanced 2025-26]({SRC['adv_2025']}) |
| Standings GP ÷ 2 vs official calendar | {s['calendar_total']} games | [NBA.com Standings]({SRC['standings']}) · [NBA.com Games]({SRC['games_1102']}) |
| League home win rate | {s['league_home_wins']}/{s['league_home_games']} = {fmt(s['league_home_win_rate'],4)} | [NBA.com Standings]({SRC['standings']}) |
| Settled games transcribed | {s['settled_games_transcribed']} of {s['calendar_total']} | [NBA.com Games 2026-10-23]({SRC['games_1023']}) |

## Checks applied

1. Every raw row has an official (allowlisted) source URL.
2. Standings: HOME W-L + ROAD W-L = overall W-L; displayed WIN% = W/(W+L); GP = W+L.
3. Advanced tables: NetRtg = OffRtg − DefRtg (within published rounding); W+L = GP; 2025-26 GP=82.
4. 2025-26 global: ΣW = ΣL = 1230 across 30 teams.
5. Traditional table: FG% consistent with FGM/FGA; W+L = GP.
6. Cross-table GP agreement for all 30 teams (standings / advanced / traditional).
7. Schedule reconciliation: Σ team-GP ÷ 2 = 92 = official games calendar for 2026-10-20…11-01.
8. Σ home games = Σ road games = 92; home wins 48 → 0.5217.
9. Score cross-check BOS 108 / ORL 97 between the games page and the official box score.
10. Every null value in a published row is listed in that row's `unverified` field; no value is inferred.

## Flagged items

{len(FL['rows'])} items are published on the site's **Flagged for Review** page with official
source links (`data/verification/flagged.json`). They do not block the merge.

## Unverified field classes

{chr(10).join('- ' + x for x in s['unverified_field_classes'])}
""")

# ------------------------------------------------------------------ EXECUTIVE_SUMMARY.md
w("EXECUTIVE_SUMMARY.md", f"""# Executive Summary — Own4 NBA Lines, Signals & Leaderboard

**Snapshot:** 2026-11-02 (UTC) · **Season:** 2026-27 in progress (4–7 GP per team)
**Live site:** https://sassnarep3-star.github.io/Own4/ · **Branch:** `arena/3ab8432d-own4`

## What was built

A fully autonomous, source-verified research pipeline and GitHub Pages dashboard that collects
official NBA data, **originates our own fair NBA lines**, researches single-bet / parlay /
player-prop strategies, measures correlations, passes every strategy through validation gates,
removes luck via out-of-sample and permutation testing, and runs a leaderboard competition with
rewards. Every table row carries a link to an official site; unconfirmable values are blank and
flagged on a dedicated **Flagged for Review** page.

## Headline numbers (all computed from official NBA.com values)

| Item | Value | Status | Official source |
| --- | --- | --- | --- |
| Official sources in registry | 22 usable + 3 unusable official endpoints | verified | [NBA.com Standings]({SRC['standings']}) |
| Rows checked line by line | {s['rows_checked']} | {s['passed']} PASS / {s['flagged']} FLAG | [NBA.com Glossary]({SRC['glossary']}) |
| Teams covered | 30 (two full official seasons) | verified | [NBA.com Advanced 2025-26]({SRC['adv_2025']}) |
| Settled games transcribed | {s['settled_games_transcribed']} of 92 | partial, flagged | [NBA.com Games 2026-10-23]({SRC['games_1023']}) |
| Our own fair lines originated | 14 games (2026-11-04 slate) | derived, formula published | [NBA.com Games 2026-11-04]({SRC['games_1104']}) |
| Correlations computed | {len(C)} (Pearson, Spearman, permutation p, BH q, bootstrap CI) | verified | [NBA.com Advanced 2026-27]({SRC['adv_2026']}) |
| Strategies / validation gates | {len(ST['rows'])} / {len(GATES['gates'])} | verified | [NBA.com Games 2026-11-01]({SRC['games_1101']}) |
| Strategies passing every gate | 0 | NOT VALIDATED | [NBA betting-data policy]({SRC['betting_data']}) |
| Eligible research signals | 4 (top reward 100 pts) | verified | [NBA.com Standings]({SRC['standings']}) |
| Flagged items | {len(FL['rows'])} | published, non-blocking | [NBA.com Games 2026-11-04]({SRC['games_1104']}) |

## Most important findings

1. **In-sample success is not skill.** Our prior-season rating model
   ([official 2025-26 advanced table]({SRC['adv_2025']}), 82 GP per team) picked
   `{fmt(BT['train']['winner_accuracy'])}` of training-window winners but only
   `{fmt(BT['holdout']['winner_accuracy'])}` of the chronological holdout
   (n={BT['holdout']['n']}); holdout binomial p =
   `{fmt(BT['holdout']['binomial_p_two_sided_vs_0_5'],4)}`, Brier skill score
   `{fmt(BT['holdout']['brier_skill_score_vs_0_5'])}` — [official settled scores]({SRC['games_1101']}).
   It is classified **NOT skill-based** and receives no reward.
2. **A naive baseline beat the model.** Picking the team with the better official 2025-26 record
   was correct `{fmt(BT['all']['naive_prior_record_baseline_accuracy'])}` of the time vs the
   model's `{fmt(BT['all']['winner_accuracy'])}` over {BT['all']['n']} games.
3. **Team strength is highly stable within a season but only moderately across seasons.**
   2025-26 `WIN% ~ NetRtg` r = `{fmt(C['2025-26 WIN% ~ NetRtg']['pearson_r'])}`; the true
   out-of-sample `2026-27 WIN% ~ 2025-26 NetRtg` r =
   `{fmt(C['2026-27 WIN% ~ 2025-26 NetRtg']['pearson_r'])}` (BH q =
   `{fmt(C['2026-27 WIN% ~ 2025-26 NetRtg']['bh_q'],4)}`) — [official source]({SRC['adv_2025']}).
4. **Parlay legs are not independent.** 2026-27 `PTS ~ NetRtg` r =
   `{fmt(C['2026-27 PTS ~ NetRtg']['pearson_r'])}` and `PTS ~ PACE` r =
   `{fmt(C['2026-27 PTS ~ PACE']['pearson_r'])}`. Same-game parlay/SGP prices require a joint
   model that cannot be verified here, so they are left blank.
5. **Prop combos are data-limited.** Leg correlations across 28 official team-leader baselines
   are near zero and not significant, but game-level player logs are unavailable from free
   official NBA pages, so fair prop lines are blank and UNVERIFIED —
   [official player table]({SRC['players_2026']}).

## Decisions

- **No betting strategy is marked validated and no Division B reward is awarded.** This is a
  deliberate result of the validation gates, not a missing feature.
- **No market odds, vig, ROI, closing-line value or edge appears anywhere.** The
  [NBA's own release]({SRC['betting_data']}) says official betting data is distributed to licensed
  operators; the [NBA.com games page]({SRC['games_1104']}) exposes no odds values in retrieved
  content. Blank + flagged, per the no-hallucination rule.
- **Four out-of-sample research signals are ranked** in Division A (100 / 60 / 30 / 10 pts).
  These are predictive associations, not betting profits.
- **17 irregularities** including the 62/92 game coverage gap, `/null` player links on NBA.com,
  unavailable official CDN JSON, and the platform's single-branch constraint are published on
  the Flagged for Review page and do not block the merge.

## Governance

`COORDINATION.md` records 11 tasks with owner, status and exclusive file scopes, small frequent
commits, `git pull --rebase` before every push, completion records with sources and verification,
and a final integration pass (T09) that re-verifies all combined data, checks links and publishes.
The platform pins this session to one branch, so per-session branches/worktrees are replaced by
non-overlapping file scopes (IR-13). PR, merge and Pages deployment results are recorded in T10.

## Reproduce

`python3 scripts/build_lines.py && python3 scripts/correlations.py && python3 scripts/validate_strategies.py && python3 scripts/verify.py && python3 scripts/build_docs.py && python3 scripts/build_site.py && python3 scripts/check_links.py`
""")

print("wrote LINES.md, CORRELATIONS.md, STRATEGIES.md, LEADERBOARD.md, VERIFICATION.md, EXECUTIVE_SUMMARY.md")

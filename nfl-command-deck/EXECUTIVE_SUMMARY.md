# NFL Command Deck — executive summary

Session `arena/1153eb96-own4` · 2026-11-19 · branch `arena/1153eb96-own4`
Site: https://sassnarep3-star.github.io/Own4/nfl-command-deck/

## The one-paragraph version

A simple opponent-aware point rating forecasts NFL winners better than every control it was
pre-registered against, and the result survives a deliberate attempt to destroy it: +0.1362
Brier skill over climatology on 100 walk-forward forecasts, +0.2397 on an untouched holdout,
a week-cluster lower bound above zero, and a permutation null in which the observed score
exceeds all 200 schedules with team identity removed. That is a **forecast-skill** result and
nothing more. The repository still holds no official price, so there is no ROI, no CLV, no
staking result and no reward — and this workspace awards zero points rather than manufacture
one from an assumed −110 line.

## What was measured

| Item | Value | Basis |
|---|---|---|
| Corpus | 149 games, weeks 1–10, 32 clubs | committed corpus, every row source-linked; 16 week-page rows corroborated by a second archive |
| Protocol | expanding-window walk-forward, weeks 4–10 | frozen in `prereg/PREREG-CD.md`, hash-locked before computation |
| Scored forecasts | 100 | one exact tie excluded |
| CD-1 skill | BSS **+0.1362**, CI [+0.0532, +0.2270] | Brier vs climatology, week-cluster bootstrap |
| CD-1 holdout (weeks 8–10) | BSS **+0.2397** | never used for any choice |
| CD-2 (constant home edge) | BSS +0.0082, CI [−0.0018, +0.0168] | fails G3 and G6 — control, not signal |
| Totals | MAE 10.776 vs 10.790 benchmark | interval [−0.114, +0.089] straddles zero: **a tie** |
| Permutation null | observed > all 200 nulls (95th pct +0.0309) | team identity permuted, real schedule kept |
| Points awarded | **0** | no price ⇒ stage 2 blank |

Two weeks (6 and 7) the model lost to climatology. They are published individually rather than
buried in the aggregate, because a per-week table that only shows wins would be a sales
document.

## What the repository actually contains

- **41 NFL workspaces**, frozen at eleven different dates (2026-11-02 to 2026-11-22), with **601
  broken `#anchor` links and 52 broken file links** across 57 pages. None of those pages belongs
  to this session; the full defect list is published rather than edited.
- **Two result archives that disagree on scope** (137 vs 149 games) and no score contradiction
  between them once the capture dates are respected. The abbreviation for the Rams differs
  (`LA` vs `LAR`), which silently drops 11 fixtures in a naive join.
- **One Week-11 injury capture**: 26 club tables, 242 player rows, and only 16 game
  designations because it was taken mid-week. 242 rows of practice status, 9 Out, 7
  Questionable. Absence from the report does not mean available — a player on injured reserve
  is not listed at all.
- **One depth-chart snapshot**: 32 clubs, 705 slots, 31 verified as text, Houston published
  only an image and is flagged rather than transcribed. 15 slots list two players at rank 1
  and 2 slots are empty; all are represented faithfully.
- **No snap counts anywhere.** The brief's instruction to model depth from playing time cannot
  be executed from this repository, and a proxy was not substituted.

## What the availability join can and cannot say

For the three rank-1 players carrying an Out designation, the club's own chart names the next
man. That is the entire defensible statement. **Who actually played is blank on every row**,
because no official inactive list and no snap count are held for Week 11. Any claim of the form
"2nd-string tackle replaced the starter" would be an inference from a chart, which the brief
forbids and this workspace does not do.

## The gates the next decision has to pass

1. **Price data** (S-01). Until an official or owner-approved source exists, every money metric
   stays blank. Two peer workspaces still carry an assumed −110 column.
2. **Availability history** (S-06). The capture workflow exists and has run twice. A season of
   Wednesday→kickoff captures is what turns designations into an ablation.
3. **A single entry point** (S-02). The reader cannot tell which of 41 pages is current. This
   deck is a candidate; freezing the rest needs an owner decision.
4. **A prospective season** (S-05). 100 forecasts establish skill against controls. They do not
   establish edge against a market. The reward tier should pay nothing until both exist.

## Fifteen flagged items

RF-01 no official page reachable from this environment · RF-02 601 broken anchors ·
RF-03 legacy dashboard links to 51 dead pages · RF-04 two result archives (137 vs 149) ·
RF-05 club-code drift drops 11 fixtures · RF-06 16 rows cite a week page rather than a game
page · RF-07 one Week-11 fixture has no venue in the capture · RF-08 no snap-count source
exists · RF-09 226 of 242 report rows carry no game designation · RF-10 replacement named but
participation unconfirmed · RF-11 depth is one snapshot, not a time series · RF-12 eleven
different namespace dates · RF-13 59 of 73 requirement verdicts are not machine-checkable ·
RF-14 no price source ⇒ no ROI · RF-15 eleven peer PRs still open.

None of them blocks publication. Each is published with the check that found it, on
`pages/flagged.html`.

## Honest limits of this evaluation

The corpus was inherited from peer workspaces and could not be re-read against nfl.com from
this sandbox. The evaluation is therefore conditional on that corpus being right; this session
strengthened it by reconciling 139 fixtures against a second independent archive and by
corroborating every week-page-only row, but it did not re-read the official pages. A live
re-read remains a separate step, and the label used throughout is *captured with a re-checked
hash*, never *verified today*.

Research only — not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET
(https://www.ncpgambling.org/help-treatment).

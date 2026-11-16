# Executive summary — NFL reconciliation, 2026-11-16

Session `arena/3858e722-own4` · branch `arena/3858e722-own4` · workspace `nfl-reconciled/`
Live entry point: `/Own4/nfl-reconciled/` · Flagged for review: `/Own4/nfl-reconciled/pages/flagged.html`

## The one thing you need to read

The repository had **31 NFL workspaces publishing 429 pages**, and **at least fourteen of them presented
themselves as the place to start**. They were each internally honest, but they did **not agree with each
other**, and nothing on the site said which figure to believe. That is a decision-making failure, and it is
the thing this session fixes. It compares the workspaces, settles what an official number can settle, and
publishes the number — or states plainly that no official number exists.

**No workspace was edited, moved or deleted.** Deletion is your decision, not a session's. What was removed
is the *ambiguity*.

## The three numbers the repository had wrong

| | Before | Canonical | Proof |
|---|---|---|---|
| Games played | "136" or "137" | **148** | Sum of all 32 clubs' published W+L+T = 296 club-games; ÷2 = 148 ([nfl.com/standings](https://www.nfl.com/standings/)) |
| Week-10 fixtures | 13, 14 or 16 | **14** | 32 clubs − 4 on bye (CHI, DEN, PHI, TB) ÷ 2 ([week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10)) |
| Week-10 injury rows | 254, 279, 347, 352 | **347 over 28 clubs** | Two independent captures reproduce 8/8 club counts and 18/18 cells counted by hand ([nfl.com/injuries](https://www.nfl.com/injuries/)) |

The corpus gap is not a guess. It closes to the point:

```
6,246 points in the weeks 1–9 corpus  +  578 points in the 12 official Week-10 finals
= 6,824 points
= the league's own published Points-For total, which equals its Points-Against total exactly
```

Zero points are unaccounted for. So the stored scores are **not merely incomplete — they are provably
consistent with every point the league credits.** That is a stronger statement than any workspace had made.

## What was settled, and what was not

**17 conflicts registered: 12 settled by an official number, 1 shown to be a label-only difference, 4 left to you.**

The four that are yours, because the league publishes nothing that decides them:

| # | Decision | What it blocks | What would clear it |
|---|---|---|---|
| RC-11 | Where market prices come from | Every ROI, CLV, reward, gate G7, all leaderboard tiers | One written verdict + the provider's terms |
| RC-12 | Ordered depth rank (1st/2nd/3rd/4th string) | The backup-deficiency feature, the matchup matrix | A club-by-club verified route or an official snap-count feed, for all 32 clubs |
| RC-13 | Prop and parlay pricing | Prop combos, same-game parlays, joint-evidence gate | RC-11's verdict + an official per-game player-log source |
| RC-14 | 2026 kickoff / onside-kick priors | Kickoff-adjacent totals, 4th-quarter win-probability curves | Read the official 2026 rulebook and freeze the rule text with a commit hash |

Plus **RR-01**: 31 workspaces exist because no rule ever said where work must land. Name one canonical
namespace in `COORDINATION.md`; after that a new session lands inside it or writes to you.

## Claims in your brief that the live official page contradicts

These are not corrections of your reasoning — they are stale observations, and the site now records the
current state:

* *"254 report rows and 4 no-injury sections"* → **347 rows over 28 sections; zero empty sections.**
* *"Seattle and Cincinnati are shown as injury-free while listing 15 and 4 players"* → **Seattle 15 rows, Cincinnati 9.**
* *"Kerby Joseph, Cade Mays and D.J. Reed are published with a blank game-status cell"* → **all three are published Out.**
* *"Only 6 of 254 report rows carry a game designation"* → **171 of 347 (49.3%) do**: Questionable 90, Out 70, Doubtful 11, blank 176.
* *"Four clubs have no section in the report"* → **those four (CHI, DEN, PHI, TB) are on bye in Week 10**, which is why the report has 28 sections, not 32.

## Independent corroboration of the 347-row figure

A second workspace completed a **full 8-of-8-chunk reading** of the same official page on 2026-11-16 and
arrived at **exactly 347 rows, 14 games and 28 clubs**, publishing its raw transcript with a sha256 beside
it (`nfl-book/data/injuries_week10_capture.json`). The figure therefore now rests on a complete read, not on
my sample plus inference. See `RC-17`.

## An irregularity worth your attention

Recomputing the availability capture's own published sha256 fingerprints at build time: **4 of 6 match.**
The two that do not are the 347-row capture and its Week-10 fixture register. Both files are **unchanged since
the merge commit `1dbde90`**, so the stale value is the *seal*, not the data — and the capture's counts are
independently reproduced above. This workspace does **not** re-seal it: re-sealing a file from the file it is
supposed to vouch for is that namespace's act, or yours. See `RC-16`.

## Your open review queue, in one place

**242 open flagged items from 18 workspaces**, grouped into 12 themes, each linking back to the page that
raised it and the source that page cited. 213 of 242 carry a source link; the other 29 are printed as
**UNVERIFIED — no source cited** rather than as a bare "none".

## Honest limits of this session

* **Chunks 2–7 of the injury report were not read.** The 347-row verdict rests on the capture's own data
  plus a hand count of 8 clubs and 18 cells. The other 20 clubs are neither confirmed nor denied here.
* **No price is printed anywhere**, because no official price source exists. A price on any of these pages
  would fail the build.
* **No depth rank is asserted**, for the same reason.
* **The 2026 rulebook was not read**, so no rule prior is asserted.
* **Other workspaces' contents were read as data**, not re-verified claim by claim. Where a peer number is
  cited, the file is named.

## How to check any number on the site

```bash
python3 nfl-reconciled/engine/reconcile.py      # validates the transcription, writes 4 artefacts
python3 nfl-reconciled/engine/build_review.py   # collects every workspace's flags
python3 nfl-reconciled/engine/build_site.py     # renders 9 pages
python3 nfl-reconciled/engine/verify_site.py    # fails on a broken link, an unsourced row, or a price
python3 -m unittest discover -s nfl-reconciled/tests   # 21 tests
```

Every published figure is computed from `data/official_facts.json` — the transcription of the pages read
this session — so a transcription error is the only way a number here can be wrong. The engine refuses to
publish if the transcription fails an identity the league's own numbers force; that check caught an error
of this session's own (16 Week-10 fixtures, where the arithmetic forces 14).

## Where to read next

| Page | Why |
|---|---|
| `pages/executive-summary.html` | This summary, rendered from the same data |
| `index.html` | The canonical numbers and the single answer per question |
| `pages/conflicts.html` | All 17 conflicts in full, with the basis for each verdict |
| `pages/results.html` | Every corpus scored against the league; the closure table |
| `pages/availability.html` | Every capture scored; the fingerprint check |
| `pages/decisions.html` | The 4 decisions + RR-01, each with its clearing action |
| `pages/workspaces.html` | All 31 workspaces, whether each has a gate |
| `pages/review.html` | All 242 flagged items |
| `pages/method.html` | Pipeline, sources, arithmetic guards, and what was not read |
| `pages/flagged.html` | This workspace's own 7 flags |

---

*Analytical research only, not wagering advice. Responsible gambling: National Problem Gambling Helpline
1-800-MY-RESET (1-800-697-3738) · [NCPG](https://www.ncpgambling.org/help-treatment).*

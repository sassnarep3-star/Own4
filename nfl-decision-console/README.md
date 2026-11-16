# nfl-decision-console — the review surface for the decisions, not another analysis of the data

Session `arena-170de4f2-own4` · built 2026-11-16 · base commit `1dbde90`.

The brief asks for two things this repository did not have: a section dedicated to **suggestions a
reviewer can act on**, and a register of the **questions, information and answers** that must be settled
before a decision is reasonable. Registers like that exist — 19 suggestion files, 17 question files,
22 flag files and 11 requirement files spread over 30 `nfl*` namespaces — but no two agree, none of
them is a place a verdict can be written, and none has been reconciled against the others.

This namespace is that reconciliation. It adds:

1. **15 consolidated suggestions** (`data/suggestions.json`), each with options, cost, what each option
   *locks*, the evidence it rests on, a recommendation with a stated basis, and a `verdict` field that is
   blank by design. Nothing here is implemented: writing a verdict is what turns a row into work.
2. **17 questions with graded answers** (`data/questions.json`) — `answered-official`,
   `answered-computed`, `partly-answered`, `owner-decision-only`, `open-needs-new-source` — so a blank
   says whether it is a hard absence or an unexplored one.
3. **13 information gaps** with the route that closes each (`data/gaps.json`).
4. **Three decision paths** (`data/paths.json`), each with the gate that blocks its first step and the
   number that clears it.
5. **9 findings about the site itself** (`data/site_findings.json`) — the site-improvement section the
   brief asks for, phrased as change + how to verify the change worked.
6. **A census of the duplication** (`pages/consolidation.html`): 386 requirement rows collapse to 124
   text clusters, 343 of them inside a duplicated cluster; only 24 of 138 suggestion rows carry any
   non-blank verdict-shaped field.

## What this session verified from official sources (and what it did not)

* **The official Game Summary ("Game Book") is real, dated, per fixture, and linked from the game
  centre.** Read: <https://static.www.nfl.com/image/upload/v1794764592/gamecenter/ab582c2f-4feb-11f1-abca-2c54536568a9.pdf>,
  chunks 1, 2, 4, 7 of 7. It prints both clubs' **lineups** (11 offense + 11 defense), **substitutions**,
  **Not Active** lists, a **Did Not Play** block, **game-day weather**, the **roof/surface** line
  ("Open Stadium on Natural Grass"), officials, attendance, full statistics, drives and play-by-play with
  timed in-game injury updates. A second fixture one week earlier carries its own.
* **It is a post-game document.** It contains final statistics, so it is a *label* source and never a
  pre-kickoff feature. This is the look-ahead gate that the point-in-time ledger requirement is about.
* **It prints a use restriction** — media coverage only; any other use needs written league permission.
  No register in this repository recorded that, and two namespaces publish tables transcribed from it
  (flag `DC-04`, suggestion `CD-03`).
* **The league publishes no odds.** `nfl.com/odds/` and `nfl.com/betting/` both serve the league's own 404
  page; the game summary contains no price. The price question is therefore a policy choice, not a
  research gap.
* **No official depth order was found**: the sampled club depth-chart path 404s, and no per-player snap
  table appears in the game-book chunks read. The 2nd/3rd/4th-string index stays unbuilt on purpose.
* **Corpus size, from the league's own standings**: ΣW = ΣL = 147, ΣPF = ΣPA = 6824,
  ΣGP/2 = 148 fixtures credited (2 tie-rows ⇒ 1 tied fixture). A season holds 272 fixtures, so a gate of
  n ≥ 300 graded fixtures **cannot be met inside 2026**, and the brief's "136-game log" equals exactly
  272/2. Computed by `engine/derive.py`, not asserted.
* **The three Lions rows this project flagged are fixed upstream** — Joseph, Mays and Reed each now read
  *Out* on the live report. Closed as "source corrected between captures".
* **The report's bracketed W–L is a live join** (6 of 6 clubs in the chunk read match the standings read
  minutes later), so it must be stored with its read window and never used as a pre-game feature.

## Rules

* Every row on every page carries an official link, a repository link, or an explicit
  `blank — unverified`; `engine/verify_site.py` fails the build otherwise.
* **No price-shaped value may appear anywhere** — no official price source exists, so a number that looks
  like odds is a build failure, not a to-do.
* The renderer reads **only committed artefacts in this directory**. It never walks the tree and never
  touches the network, so a sibling namespace merging cannot change a published number here (the standing
  warning in `COORDINATION.md`). The tree facts enter through `data/namespace_inventory.json`, which states
  the commit it describes; refresh it deliberately with `--write`.
* Timestamps are window-level: the read path returns rendered text only, with no response headers. That
  limitation is printed on the evidence page instead of being smoothed over (flag `DC-07`).

## Commands

```sh
python3 nfl-decision-console/engine/derive.py          # registers -> data/derived/*.json
python3 nfl-decision-console/engine/build_site.py      # artefacts -> index.html + pages/*.html
python3 nfl-decision-console/engine/verify_site.py     # the publication contract
python3 nfl-decision-console/engine/inventory.py --write   # re-snapshot the tree (do it in its own commit)
```

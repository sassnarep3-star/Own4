# NFL Desk

One front door over the NFL research workspaces in this repository, built so that a
decision can be made from a single screen: requirement → blocking gate → the number that
would clear it, with every register's answer shown side by side.

Published at **https://sassnarep3-star.github.io/Own4/nfl-desk/**.

## What this workspace is for

The repository holds dozens of sibling NFL workspaces written by different sessions. They
overlap, and they disagree. Rather than publish one more opinion, this workspace does four
things:

1. **Measures the disagreement.** `engine/census.py` walks the tree and counts workspaces,
   duplicated registers and pairwise status disagreements between the three requirement
   registers, with no number typed by hand.
2. **Recounts from stored official captures.** `engine/parse_standings.py` and
   `engine/parse_injuries.py` re-read the 2026-11-19 standings and the stored 2026-11-18
   injury capture, so published counts come from a hashed artifact rather than a
   transcription.
3. **Publishes one register, not one verdict.** `engine/register.py` keeps the brief's
   wording as the key and prints all three registers' statuses beside each row, plus
   whether each row's quoted evidence path actually resolves.
4. **Refuses to fill blanks.** No price, roof, snap count, inactive list or replacement
   claim is invented. Missing values are named on the Questions page with the route to
   obtain them, and on the Flagged page with the files that show the gap.

## Pages

| Page | What it answers |
|---|---|
| `index.html` | Dashboard: headline counts, decision-readiness preview, where the project stands |
| `pages/executive-summary.html` | The whole programme on one page, with the five blockers and the open owner decisions |
| `pages/requirements.html` | All 73 brief lines: three statuses, agreement, gate, clearing number, official source |
| `pages/questions.html` | 18 questions → what we have → what is missing → how to discover it → what clears it |
| `pages/suggestions.html` | 10 options with cost, risk, timing, and a blank owner-decision column |
| `pages/availability.html` | The injury report recounted from a stored capture; depth coverage by route |
| `pages/corpus.html` | The 136 / 137 / 150 settled-game question, and 32 standings rows parsed from the official read |
| `pages/census.html` | Every workspace, page counts, duplication, thin artifacts, register disagreement |
| `pages/flagged.html` | 15 irregularities, each with the files that show it |
| `pages/sources.html` | Every official page opened on 2026-11-19, what it showed, and its limits |
| `pages/verify.html` | The ten gates this workspace runs, and what they do not check |

## Reproduce

```sh
python3 nfl-desk/engine/parse_standings.py    # rendered read -> data/standings_2026-11-19.json
python3 nfl-desk/engine/parse_injuries.py     # stored capture -> data/injuries_2026-11-18_parsed.json
python3 nfl-desk/engine/census.py             # the tree -> data/census.json
python3 nfl-desk/engine/register.py           # three registers -> data/requirements.json
python3 nfl-desk/engine/build.py              # data -> 11 pages
python3 nfl-desk/engine/verify.py --rebuild   # the publication gate
```

CI runs the same six commands (`.github/workflows/nfl-desk.yml`) and fails on a diff in
`nfl-desk/data`, a page that does not rebuild byte-identically, or any row without a
source.

## Data and evidence

- `data/*.json` — every table on the site is generated from these files.
- `evidence/reads/standings_2026-11-19.txt` — the verbatim rendered read the standings
  parser consumes, with its sha256 recorded in the parsed output.
- The injury counts are parsed from
  `nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html`
  (captured by a peer session's scheduled workflow); the parser refuses to publish if that
  file's hash stops matching the capturing workflow's manifest.

## Boundaries

- No claim of a profitable strategy. Nothing here is reward-eligible.
- No claim that a peer workspace's number is current; each page dates what it shows.
- No editing of peer workspaces. Where this desk disagrees with one, both files are linked
  and the disagreement is on the Flagged page.
- Research only, not wagering advice.

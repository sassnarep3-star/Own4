# NFL Desk — executive summary (2026-11-19)

**Read this if you read nothing else.** Every figure below is produced by a script in
`nfl-desk/engine/` and linked from the site page named in brackets.

## 1. Where the programme actually stands

- **73 requirement lines** come from the brief. Three registers answer them. They agree on
  21, disagree on 29, and 23 cannot be matched across files on wording alone.
  → `data/requirements.json` [requirements page]
- **No market price exists** anywhere in the repository from an official source. Every
  market value in the price store is null by policy; the one "close" that looks real is a
  model run. Without a market line there is no CLV, no residual and no ROI.
- **The settled-game count is not settled.** The brief says 136, two feeds say 137, one
  transcription says 150. The official standings read today give 300 team-games, i.e. at
  most 150 completed games. → [corpus page]
- **No strategy is reward-eligible.** All 15 leaderboard rows are ineligible; the best
  sample is 303 bets with a BH-adjusted p of 0.44, against 1,148–1,290 bets needed at 80%
  power. That is the correct outcome, and it should be visible rather than buried.
- **Availability is barely captured.** Two captures exist (Week 10 rendered, Week 11 raw
  and hashed). No inactive list and no snap count exists anywhere in the repository.
- **The published model does not beat a home-team baseline** (winner accuracy 0.571 on 35
  graded games vs 0.600; one-sided p 0.70). A totals model clears a permutation test but
  fails the sample floor and multiplicity control.

## 2. What was verified today, from official pages

Four pages were opened on 2026-11-19 and are recorded with what each showed and what each
could not settle (`data/official_reads_2026-11-19.json`, [sources page]):

| Read | What it established |
|---|---|
| nfl.com/standings | 32 clubs, 300 team-games, at most 150 completed games; two NFC clubs carry a tie |
| nfl.com/injuries | The live Week 11 report; only the early windows carry game designations |
| nfl.com/schedules/2026/by-week/week-11 | 13 Week 11 fixtures, 6 bye clubs, the league's flexible-scheduling note |
| Colts at Texans game centre | Venue facts (Houston, TX; Reliant Stadium) and 8 Out designations |

Two counts were **measured, not typed**:

- The stored Week 11 injury capture, hash-checked against the capturing workflow's
  manifest: **23 club tables, 242 player rows, 16 designations (9 Out, 7 Questionable),
  226 blanks** → 6.6% designated. The brief's "6 of 254" cannot be reconciled because its
  copy is not in the repository; the dated recount stands in its place (flag F05).
- The standings, parsed from the saved rendered read: **32 rows, 300 team-games, 150
  implied games, remainder 0**.

## 3. The five blockers, in the order they should be tackled

1. **Price source** — buy or licence a series, or stop calling the column "market". Nothing
   downstream can be computed without it.
2. **Corpus** — reconcile the 272-row feed to the official week pages once, and retire
   136/137/150 forever.
3. **Inactive lists** — capture them; they are the only way to turn a designation into a
   measurable signal.
4. **Depth for 32 of 32 clubs** — hold the line the brief already draws: no depth feature
   until Houston is covered and the undated pages are dated.
5. **One register** — adopt the round-2 rule (an artifact path that exists plus an official
   source) and retire the other two status columns to history.

## 4. What is on the desk that did not exist before

| Deliverable | Why it matters |
|---|---|
| `engine/census.py` | 40 workspaces, duplication counts and 62 register disagreements, all measured |
| `engine/parse_standings.py` | the official standings as data, from the saved read |
| `engine/parse_injuries.py` | injury counts from a hashed capture, refusing to publish if the hash moves |
| `engine/register.py` | the 73 lines with every register's answer and every evidence path resolved |
| 18 questions, 10 suggestions, 15 flags | what is missing, what to do about it, and what is wrong |
| `engine/verify.py` | ten gates; fails on an unsourced row, a broken link, a stale hash, a non-deterministic build |

## 5. Decisions only the owner can make

- **D-1** Which register is authoritative? (Recommendation: the round-2 rule, because it is
  the only one of the three with a testable condition.)
- **D-2** Buy or licence a price series, or publish model-only lines and label them as such?
- **D-3** May raw captures be served publicly, or do they move to a private store?
- **D-4** Which of the 40 workspaces are live, and which are history?
- **D-5** Replace 40 verifiers with one repo-level gate?

None of these has been taken. They are recorded on the suggestions page with a blank
decision column so the choice stays visible.

## 6. Honest limitations of this summary

- It reflects one day of reads. No page was fetched at build time, so nothing here detects
  that a source has changed since 2026-11-19.
- Peer workspaces' numbers are quoted, not re-verified, except where a stored capture was
  re-parsed (injuries) or an official page was read (standings, schedule, game centre).
- The 150-game ceiling is arithmetic from the standings, not a fixture-by-fixture
  reconciliation, and it is labelled as a ceiling wherever it appears.

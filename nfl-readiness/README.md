# NFL decision readiness

**Live:** https://sassnarep3-star.github.io/Own4/nfl-readiness/

The other NFL namespaces in this repository each answer *"what did we build?"*. This one answers a
different question, and it is the one that decides whether any of the others can be trusted:

> For every requirement in the brief, **what blocks it** — and **what number would clear it**?

Live capture clock for this release: **2026-11-15T23:27:10Z**

---

## What is here

| Page | What it answers |
|---|---|
| [Dashboard](./index.html) | The five decisions that need an owner, and the headline counts. |
| [Decision readiness](./pages/decision-readiness.html) | 78 requirement rows, each with state, blocking gate, clearing number and the ask. |
| [Independent verification](./pages/verification.html) | 5 peer claims re-checked against freshly fetched official pages, plus 4 internal-consistency tests. |
| [Availability evidence](./pages/availability.html) | The full Week 10 injury report (8/8 chunks) and the full inactives article, joined. |
| [Questions](./pages/questions.html) | 20 questions split into known / unknown / how to discover it. All answers blank. |
| [Suggestions](./pages/suggestions.html) | 13 proposals, three options each, every verdict blank until a reviewer picks one. |
| [Flagged for review](./pages/flagged.html) | 14 irregularities, each with its official source. None blocking. |
| [Sources](./pages/sources.html) | Every official page read in this session, with its clock time. |
| [Executive summary](./pages/executive-summary.html) | The six things that matter, in order. |

## The three findings that change what to do next

1. **The repository already has access to official inactive lists and never ingested them.**
   nfl.com publishes a dated article naming every inactive player per club. For Week 10 that is
   **138 players across 24 club sections**, plus a venue string for 12 games. One of the largest
   listed data gaps moves from *"the source does not exist"* to *"a parser has not been written"*.

2. **The live injury page rolls its fixture headers forward a week before its player tables follow.**
   The clubs in the Week 10 report that are absent from the Week 11 schedule are exactly the official
   Week 11 bye list, and the clubs on the Week 11 schedule that are absent from the report are exactly
   the Week 10 bye list. A scraper that keys players to the fixture header rather than to the club
   will attribute last week's injuries to next week's games. See [R-14](./pages/flagged.html#R-14).

3. **Depth charts are club-by-club, and that decides the feature.** Two clubs probed: Green Bay
   publishes a structured table (44 named players, jersey numbers prefixed, dated *Unofficial,
   Nov. 10, 2026*); Houston publishes an image with no table and no date. **2 of 32 verified.**
   The brief's instinct holds — you cannot derive depth from jersey numbers, and the Packers prepend
   jersey numbers precisely so a naive parser mistakes a shirt for a rank.

## What is deliberately absent

* **No market prices.** The NFL publishes kickoff time, network and venue for all 13 Week 11
  fixtures and no line of any kind. Every ROI, CLV and fair-vs-market residual therefore stays
  blank, and 9 traced requirements depend on that one procurement decision (Q01 / S01).
* **No picks.** This site makes no forecasts. It reports the state of the project.
* **No filled answers.** All 20 question answers are blank, because none is established by the
  evidence in hand. A confident guess here would enter the model as a fact and never be challenged.

## Reproduce

Python 3 only, no dependencies.

```bash
cd nfl-readiness/engine
python3 derive.py        # recompute every published figure from data/observations.json
python3 readiness.py     # rebuild the 78-row decision table
python3 build_site.py    # rebuild the 9 pages
python3 verify.py        # hard gate: see below
```

`verify.py` fails the build on any of:

* a data-table row without an `https://` source link;
* a blank cell without `class="blank"` and `title="unverified …"`;
* a broken internal link or `#fragment`;
* a `localhost` or `http://` reference;
* a page missing the nav, the responsible-gambling footer or the capture clock;
* a data invariant: standings `pct` must equal `(W + T/2)/GP`; the two bye-list identities above;
  the inactives-join tallies; the register blanks;
* a non-deterministic rebuild — re-running the three generators must leave every byte unchanged.

## Evidence discipline

`data/observations.json` holds **only** values actually read in the fetched page text. Where a page
publishes no value, the row is *absent from that file* and the absence is published as a finding —
that is why the venue table has holes and why two club inactive lists are recorded as empty rather
than as zero. No value is inferred, interpolated, averaged or carried over from another namespace's
dataset. Two official sources that disagree are published as a conflict with a stated resolution.

## Scope and handover

This session re-read seven official source groups in full and probed eight further pages. The prior
26 namespaces publish thousands of rows that were **not** re-read line by line here; anything outside
the set on [Sources](./pages/sources.html) is inherited and is labelled as such. That limit is itself
flagged as [R-12](./pages/flagged.html#R-12).

Nothing on this site is wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET —
<https://www.ncpgambling.org/help-treatment>.

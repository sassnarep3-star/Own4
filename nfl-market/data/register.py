#!/usr/bin/env python3
"""Questions, suggestions and decision register for the nfl-market namespace.

The brief asks for three things that are easy to conflate, so they are kept apart
and each row is forced to answer the same four things:

  QUESTIONS    what we KNOW (sourced), what we DO NOT KNOW, what would settle it,
               and whether it can be settled from data we can get. A question with
               no known answer is still published; a question we could answer today
               but have not is marked so.
  SUGGESTIONS  a proposed change to the site or the analysis, with the evidence,
               the cost, what it depends on, and at least two real options so a
               reviewer chooses rather than approves. Nothing here is implemented.
  DECISIONS    the small set of choices that block everything else. Until these are
               answered, further building is motion, not progress.

Every row carries a source link. Where the honest answer is "we do not know", the
answer field is blank and the row says why, which is the point.
"""

Q = [
    {
        "id": "QM-01",
        "group": "Prices",
        "question": "May this project rely on a third-party price archive at all?",
        "known": (
            "The NFL publishes no odds of any kind (checked again this session: "
            "the week-10 schedule page carries kickoff time and network only). "
            "Every price in this namespace is DraftKings syndicated via ESPN's "
            "public endpoint, archived with its URL and read time."),
        "not_known": (
            "Whether that source's terms permit redistribution of the numbers in a "
            "public site, and whether the owner is willing to accept a third-party "
            "single-book price as the basis of any claim."),
        "settles_it": (
            "A written answer from the owner on acceptable sources, plus the "
            "provider's terms of use. Neither is in this repository."),
        "blocks": "Every staking number, every ROI, every 'against the close' claim.",
        "can_settle_now": "partly - the owner can answer the second half today",
        "sources": ["https://www.nfl.com/schedules/2026/by-week/week-10",
                    "https://sports.core.api.espn.com/v2/sports/football/leagues/"
                    "nfl/events/401873052/competitions/401873052/odds"],
        "linked_suggestion": "SM-01",
        "answer": "",
    },
    {
        "id": "QM-02",
        "group": "Prices",
        "question": "Which single number should count as 'the market' for grading?",
        "known": (
            "The store now holds two snapshots per market per game: an opening "
            "number and the provider's latest number. For the 13 unplayed games the "
            "latest number is not a close and will keep moving. For the one played "
            "game both snapshots exist and are stable."),
        "not_known": (
            "Whether the owner wants grading against the open, against the number "
            "at a fixed lead time before kickoff, or against the close. Each choice "
            "changes every ROI in the leaderboard, and they are not interchangeable."),
        "settles_it": "One decision. It is question D-2 on this page.",
        "blocks": "Leaderboard comparability; any statement that a strategy beats a "
                  "price.",
        "can_settle_now": "yes",
        "sources": ["https://www.nfl.com/schedules/2026/by-week/week-10"],
        "linked_suggestion": "SM-02",
        "answer": "",
    },
    {
        "id": "QM-03",
        "group": "Prices",
        "question": "How many books are needed before a price can be called a market?",
        "known": (
            "This namespace holds one book. A single book's number is a price, not a "
            "market: line shopping and the dispersion across books are exactly the "
            "edge most retail strategies claim, and neither can be measured from one "
            "source."),
        "not_known": (
            "How many independent books are reachable and storable under the same "
            "terms question, and what dispersion actually exists between them for "
            "NFL sides and totals."),
        "settles_it": "Archiving two or more independent providers for one slate and "
                      "publishing the dispersion. Not attempted yet.",
        "blocks": "Any claim of the form 'the market is wrong here'.",
        "can_settle_now": "no - needs a second source that passes QM-01",
        "sources": ["https://sports.core.api.espn.com/v2/sports/football/leagues/"
                    "nfl/events/401873052/competitions/401873052/odds"],
        "linked_suggestion": "SM-03",
        "answer": "",
    },
    {
        "id": "QM-04",
        "group": "Injuries and depth",
        "question": "Can replacement depth be known BEFORE kickoff, from any official source?",
        "known": (
            "Before kickoff the official record is the injury report: per player, a "
            "practice status and a game status of Out / Doubtful / Questionable. "
            "After the game the Game Book prints the actual starting elevens, the "
            "substitutions, did-not-play and not-active lists. The NFL publishes no "
            "depth chart: https://www.nfl.com/depth-charts/ returns the 404 page, "
            "re-read this session."),
        "not_known": (
            "Whether a 'Questionable' designation at any lead time predicts that the "
            "player actually misses the start. That is measurable from Game Books "
            "across a season and has not been measured here."),
        "settles_it": (
            "Collect Game Books for every game of one season, join to the Thursday "
            "and final injury reports, and publish the hit rate of each designation. "
            "That is a concrete, official-only study; it needs roughly 270 game books."),
        "blocks": "Any pre-game use of depth. It does not block the post-game "
                  "grading, which this namespace already does.",
        "can_settle_now": "yes, with a season of game books - large but bounded",
        "sources": ["https://www.nfl.com/injuries/"],
        "linked_suggestion": "SM-04",
        "answer": "",
    },
    {
        "id": "QM-05",
        "group": "Injuries and depth",
        "question": "Does a starting-lineup change actually move the line?",
        "known": (
            "The store holds the opening and latest number for every week-10 game, "
            "and the official injury report names who was Out. The two documents can "
            "be joined on team and week."),
        "not_known": (
            "Whether the market moves at all when a starter is ruled out, how far, "
            "and how quickly. With 14 games and one week, nothing about this is "
            "estimable: at most 14 observations, and the moves observed are "
            "confounded with everything else that moved the number."),
        "settles_it": (
            "Several slates of prices joined to injury reports, then a "
            "difference-in-differences against games with no designation change. "
            "Needs multi-week price history, which the store does not have."),
        "blocks": "The whole 'replacement depth as a signal' hypothesis.",
        "can_settle_now": "no - needs multi-week price history first",
        "sources": ["https://www.nfl.com/injuries/",
                    "https://www.nfl.com/schedules/2026/by-week/week-10"],
        "linked_suggestion": "SM-05",
        "answer": "",
    },
    {
        "id": "QM-06",
        "group": "Model",
        "question": "Is the points model in this namespace any good?",
        "known": (
            "It is a transparent points-for/points-against model with two "
            "pre-committed constants (home field 1.8 points, margin sigma 13.0) and "
            "no parameters fitted to outcomes. It produces a line for all 14 week-10 "
            "games. The prior session's model was measured and lost to the closing "
            "line (mean absolute error 10.56 vs 10.01 on the spread)."),
        "not_known": (
            "Whether THIS model beats a naive baseline, and whether it beats the "
            "market. One graded game is not an answer."),
        "settles_it": (
            "Backtest on the seasons already in the repository's archive, "
            "walk-forward, and publish mean absolute error against both a naive "
            "baseline and the market. The archive supports it; it is not done here "
            "because the archive is third-party and QM-01 is unanswered."),
        "blocks": "Any leaderboard entry for an own-line strategy.",
        "can_settle_now": "yes, once QM-01 is answered",
        "sources": ["https://www.nfl.com/standings/league/2026/REG"],
        "linked_suggestion": "SM-06",
        "answer": "",
    },
    {
        "id": "QM-07",
        "group": "Model",
        "question": "What is the minimum n before any strategy number is published as a result?",
        "known": (
            "The demotion gate defined this round refuses anything under n = 200. "
            "The prior session's 15 strategies range from n = 119 to n = 3,251, so "
            "one of them fails that floor on size alone."),
        "not_known": (
            "Whether 200 is the right floor for the effect sizes at issue. No "
            "power calculation has been done, and a power calculation needs an "
            "assumed effect size, which is the thing being tested."),
        "settles_it": (
            "Choose the smallest edge worth acting on (e.g. 1.5 points of "
            "win-rate edge), then compute the n needed at that effect. That is a "
            "single defensible calculation and it is not done here."),
        "blocks": "Publication of any strategy result as evidence rather than as a "
                  "description.",
        "can_settle_now": "yes - one decision plus one calculation",
        "sources": ["https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                    "data/derived/strategy_results.json"],
        "linked_suggestion": "SM-07",
        "answer": "",
    },
    {
        "id": "QM-08",
        "group": "Statistics",
        "question": "How should 15 strategies tested at once be corrected for?",
        "known": (
            "The prior session applied Benjamini-Hochberg across its family and "
            "published both raw and corrected p-values. Under that correction, none "
            "of the 15 survives at 0.10; the smallest corrected p-value in the "
            "leaderboard is 0.44."),
        "not_known": (
            "Whether the family should include the strategies that were tried and "
            "discarded, which is the number that actually drives the correction and "
            "which no one recorded."),
        "settles_it": (
            "Pre-register the family BEFORE testing, and publish the count of "
            "rules tried. The repository's own pre-registration files show intent "
            "but not a count of abandoned rules."),
        "blocks": "Any statement that a rule is statistically distinguishable from "
                  "luck.",
        "can_settle_now": "partly - the family can be frozen from now on",
        "sources": ["https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                    "data/derived/leaderboard.json"],
        "linked_suggestion": "SM-08",
        "answer": "",
    },
    {
        "id": "QM-09",
        "group": "Statistics",
        "question": "Parlays: is the joint priced correctly, or is independence assumed?",
        "known": (
            "The prior session priced its same-game combo from the walk-forward "
            "empirical joint distribution, not from multiplying the legs, which is "
            "the right instinct. It reports the joint correlation for 'home covers "
            "AND over' as r = 0.0083 on n = 3,912."),
        "not_known": (
            "Whether that near-zero dependence is real or an artefact of the "
            "third-party archive's prices, and what the same number is for the "
            "specific legs this namespace would combine. No leg-level price archive "
            "exists here, so it cannot be computed."),
        "settles_it": (
            "An official-sourced leg-level dataset with prices. Not available: the "
            "NFL publishes no prices and the props sub-resource was not archived."),
        "blocks": "Any parlay or same-game-combo strategy from being ranked.",
        "can_settle_now": "no",
        "sources": ["https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                    "data/derived/correlations.json"],
        "linked_suggestion": "SM-09",
        "answer": "",
    },
    {
        "id": "QM-10",
        "group": "Statistics",
        "question": "What does 'removing luck' mean operationally here?",
        "known": (
            "Two things are done: a no-skill simulation at the strategy's own "
            "prices (20,000 trials, prior session) and a multiple-testing correction. "
            "Both are described in the prior session's files."),
        "not_known": (
            "Whether the owner means those two, or means a variance decomposition "
            "into luck and skill components across bets, or means something else "
            "again. The phrase admits several defensible readings and they produce "
            "different leaderboards."),
        "settles_it": "One decision. It is question D-4 on this page.",
        "blocks": "The definition of the leaderboard itself.",
        "can_settle_now": "yes",
        "sources": ["https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                    "data/derived/strategy_results.json"],
        "linked_suggestion": "SM-10",
        "answer": "",
    },
    {
        "id": "QM-11",
        "group": "Operations",
        "question": "Who re-reads the official sources, and how often, before this is stale?",
        "known": (
            "Every official number on this site was read once, on 2026-11-14, and "
            "carries that read time. Standings change every week; the injury report "
            "changes daily; the Game Book appears hours after the game."),
        "not_known": (
            "The refresh cadence the owner wants, and whether a stale page is "
            "acceptable if it is labelled with its read time. Nothing currently "
            "refreshes automatically: there is no scheduled job."),
        "settles_it": "A cadence decision plus a scheduled job. Neither exists.",
        "blocks": "Nothing today; it becomes blocking the moment a page is used for "
                  "a decision.",
        "can_settle_now": "yes",
        "sources": ["https://www.nfl.com/injuries/",
                    "https://www.nfl.com/standings/league/2026/REG"],
        "linked_suggestion": "SM-11",
        "answer": "",
    },
    {
        "id": "QM-12",
        "group": "Operations",
        "question": "What happens to a live strategy when its data source disappears?",
        "known": (
            "The demotion gate on this site covers performance decay. It says "
            "nothing about source loss, which is the more likely failure: one "
            "provider, no contract, no SLA."),
        "not_known": (
            "Whether the site should keep publishing frozen numbers, blank the "
            "affected rows, or demote everything. Each is defensible."),
        "settles_it": "One decision. It is question D-5 on this page.",
        "blocks": "Nothing today; blocks any claim that the system is operational.",
        "can_settle_now": "yes",
        "sources": ["https://sports.core.api.espn.com/v2/sports/football/leagues/"
                    "nfl/events/401873052/competitions/401873052/odds"],
        "linked_suggestion": "SM-12",
        "answer": "",
    },
    {
        "id": "QM-13",
        "group": "Publishing",
        "question": "Sixteen NFL workspaces now exist with overlapping content. Which is canonical?",
        "known": (
            "The root navigation lists sixteen NFL workspaces. Several publish the "
            "same standings, several publish own lines for the same week with "
            "different numbers, and at least three publish a questions register. "
            "This namespace is the seventeenth."),
        "not_known": (
            "Which one the owner reads. Without that, every new workspace adds to "
            "the confusion the brief asks us to reduce."),
        "settles_it": "One decision: name the canonical workspace and redirect or "
                      "retire the rest. This is question D-1.",
        "blocks": "Any further site-building being useful rather than additive.",
        "can_settle_now": "yes",
        "sources": ["https://sassnarep3-star.github.io/Own4/"],
        "linked_suggestion": "SM-13",
        "answer": "",
    },
    {
        "id": "QM-14",
        "group": "Publishing",
        "question": "Is 'rewards for top strategies' a real stake or a scoreboard?",
        "known": (
            "The prior sessions published a reward-points scheme and awarded 0 of "
            "1,000 points because no strategy qualified. No money has ever been at "
            "risk anywhere in this repository."),
        "not_known": (
            "Whether the owner intends real capital, paper units, or points. This "
            "changes the demotion gate's strictness, the meaning of drawdown, and "
            "whether responsible-gambling framing is sufficient."),
        "settles_it": "One decision. It is question D-3 on this page.",
        "blocks": "The gate's tolerances and the leaderboard's units.",
        "can_settle_now": "yes",
        "sources": ["https://www.ncpgambling.org/help-treatment"],
        "linked_suggestion": "SM-14",
        "answer": "",
    },
    {
        "id": "QM-15",
        "group": "Data integrity",
        "question": "How much of the published corpus has actually been re-read against its source?",
        "known": (
            "This session re-read every source it cites. A repo-wide scan found "
            "11,584 published table rows of which 1,268 carry no source link at all, "
            "and this session found and corrected a fabricated injury block of its "
            "own before publishing it."),
        "not_known": (
            "How many published values in the other sixteen workspaces are wrong. "
            "Prior sessions report spot checks and full re-reads for some "
            "namespaces; none reports a complete cell-by-cell pass over the whole "
            "corpus, and the unlinked-row count suggests the coverage claim is "
            "narrower than it reads."),
        "settles_it": (
            "A cell-by-cell re-read of one namespace at a time, with the count of "
            "cells checked published per namespace. Large, bounded, and the only "
            "way to convert 'verified' from an adjective into a number."),
        "blocks": "The credibility of any aggregate claim across workspaces.",
        "can_settle_now": "yes, incrementally",
        "sources": ["https://sassnarep3-star.github.io/Own4/"],
        "linked_suggestion": "SM-15",
        "answer": "",
    },
]

S = [
    {
        "id": "SM-01",
        "title": "Publish a source-class label on every number and make it filterable",
        "problem": (
            "The site mixes official values (scores, standings, injury report, "
            "game books) with third-party values (every price) in tables that look "
            "identical. A reader cannot tell which is which without opening links."),
        "evidence": "This page: every price traces to one ESPN endpoint; every score "
                    "traces to nfl.com. The store already records the class per row.",
        "options": [
            "A: add an 'official / third-party / derived' badge column to every table",
            "B: split each table into two, official above the rule, third-party below",
            "C: leave as is and rely on the Flagged page",
        ],
        "recommended": "A, because it is one column, it cannot be forgotten in a "
                       "new table, and it is checkable by a script.",
        "effort": "small - the data already carries the label",
        "depends_on": "nothing",
        "does_not_do": "It does not make third-party numbers trustworthy; it makes "
                       "them visibly third-party.",
        "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
    },
    {
        "id": "SM-02",
        "title": "Freeze the grading price before the season, not after each result",
        "problem": (
            "Grading against open, against a lead-time snap, or against close gives "
            "three different ROIs for the same bets. If the choice is made after "
            "seeing which is kindest, the ROI is fitted."),
        "evidence": "The store holds both snapshots for all 14 games and the 13 "
                    "unplayed games' 'close' is still moving.",
        "options": [
            "A: grade against the open, always",
            "B: grade against a fixed lead time (e.g. 60 minutes before kickoff)",
            "C: grade against the close, accepting that it needs the game to start",
            "D: publish all three and rank on the worst",
        ],
        "recommended": "B for decisions, with A and C published alongside for "
                       "transparency. A lead-time snap is the only one that matches "
                       "what a bettor could actually have taken.",
        "effort": "small to define, medium to implement (needs a scheduled snapshot)",
        "depends_on": "QM-02 / D-2",
        "does_not_do": "It does not remove the single-book problem.",
        "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
    },
    {
        "id": "SM-03",
        "title": "Add a second independent price source before any edge claim",
        "problem": (
            "One book cannot show dispersion, and dispersion is where the retail "
            "edge is claimed to live. With one book there is no way to distinguish "
            "'the market is wrong' from 'this book is wrong'."),
        "evidence": "The archive holds exactly one provider for all 84 rows.",
        "options": [
            "A: add a second provider and publish the per-market dispersion",
            "B: do not add one; restrict all claims to 'relative to this book'",
        ],
        "recommended": "A if QM-01 is answered yes, otherwise B, stated loudly.",
        "effort": "medium - new archive, new integrity checks, new labels",
        "depends_on": "QM-01 / QM-03",
        "does_not_do": "It does not make either source official.",
        "source": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
                  "events/401873052/competitions/401873052/odds",
    },
    {
        "id": "SM-04",
        "title": "Measure the injury report instead of assuming it",
        "problem": (
            "The site treats 'Out' and 'Questionable' as if they mean what a reader "
            "assumes. Nobody has measured how often a Questionable player actually "
            "fails to start."),
        "evidence": "One club-week is transcribed here: Lucas Patrick, listed Out "
                    "with a concussion, was Not Active and was replaced by Nick "
                    "Allegretti at centre. That is one data point, from two documents, "
                    "for one club.",
        "options": [
            "A: run the season-long join (game books x injury reports) and publish "
            "hit rates by designation",
            "B: publish the one worked example and stop",
        ],
        "recommended": "A. It is official-only, it is bounded, and it answers the "
                       "single most load-bearing assumption on the site.",
        "effort": "large - roughly 270 game books, but fully mechanical",
        "depends_on": "nothing official; does not need QM-01",
        "does_not_do": "It does not tell you who the backup is before kickoff.",
        "source": "https://www.nfl.com/injuries/league/2026/reg10",
    },
    {
        "id": "SM-05",
        "title": "Publish the depth chain as observed, never as ranked",
        "problem": (
            "The requirement asks for 2nd/3rd/4th string awareness. No official "
            "depth chart exists, so a rank column would be an inference dressed as "
            "data."),
        "evidence": "https://www.nfl.com/depth-charts/ returns the 404 page; the "
                    "Game Book gives starts and substitutions only.",
        "options": [
            "A: an 'observed starts' column (n of games started) and nothing else",
            "B: infer depth rank from observed starts and label it inferred",
            "C: buy a licensed depth feed",
        ],
        "recommended": "A now; C only if the owner will fund it, and if so B becomes "
                       "unnecessary rather than merely discouraged.",
        "effort": "small for A, medium for C",
        "depends_on": "QM-04",
        "does_not_do": "It does not give a pre-game depth state.",
        "source": "https://www.nfl.com/depth-charts/",
    },
    {
        "id": "SM-06",
        "title": "Make the model earn its place against a naive baseline first",
        "problem": (
            "The site publishes an own line for 14 games before showing that the "
            "line beats 'home team by 2'. A model that cannot beat a constant is "
            "decoration."),
        "evidence": "The prior session did exactly this test and lost to the market "
                    "(10.56 vs 10.01 mean absolute error), which is the honest "
                    "outcome and should be the first table on the page.",
        "options": [
            "A: publish baseline vs model vs market error before any line",
            "B: publish the lines and the errors further down",
        ],
        "recommended": "A, on the landing page, because the error comparison is the "
                       "finding and the lines are the illustration.",
        "effort": "small",
        "depends_on": "QM-06",
        "does_not_do": "It does not make the model good; it makes its quality "
                       "knowable at a glance.",
        "source": "https://www.nfl.com/standings/league/2026/REG",
    },
    {
        "id": "SM-07",
        "title": "Set the minimum n from a power calculation, not from taste",
        "problem": (
            "The demotion gate uses n >= 200 because it had to use something. A "
            "number chosen for convenience will be argued with the moment it "
            "demotes something someone likes."),
        "evidence": "One prior strategy has n = 119 and would fail the floor on "
                    "size alone, whatever its edge.",
        "options": [
            "A: choose the smallest worthwhile edge and compute n from it",
            "B: keep 200 and describe it as a convention, not a standard",
        ],
        "recommended": "A. One afternoon of arithmetic buys a standard that cannot "
                       "be argued with.",
        "effort": "small",
        "depends_on": "QM-07",
        "does_not_do": "It does not resolve multiple testing, which is separate.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/strategy_results.json",
    },
    {
        "id": "SM-08",
        "title": "Freeze the strategy family and publish the count of discarded rules",
        "problem": (
            "A multiple-testing correction is only as honest as the family it "
            "corrects over. Rules tried and abandoned are part of the family and "
            "nobody counted them."),
        "evidence": "Fifteen rules are published; the number tried is unknown. The "
                    "smallest BH-corrected p-value in the leaderboard is 0.44.",
        "options": [
            "A: a register of every rule ever tried, with its date, now and going "
            "forward",
            "B: correct only over published rules and say so",
        ],
        "recommended": "A. Without it, the correction understates the search and "
                       "every p-value is optimistic by an unknown amount.",
        "effort": "small to start, needs discipline forever",
        "depends_on": "QM-08",
        "does_not_do": "It cannot recover the count for rules already abandoned.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/leaderboard.json",
    },
    {
        "id": "SM-09",
        "title": "Price parlays from the observed joint, and show the independence gap",
        "problem": (
            "Multiplying leg prices assumes independence. For same-game legs that is "
            "known to be wrong, and the size of the error is exactly the size of the "
            "house edge a parlay quietly carries."),
        "evidence": "The prior session's implementation already uses the empirical "
                    "joint; its measured dependence for 'home covers and over' is "
                    "0.0083 on n = 3,912, which is small but is a third-party number.",
        "options": [
            "A: show, side by side, the independence-priced parlay and the "
            "joint-priced one, with the gap",
            "B: show only the joint price",
        ],
        "recommended": "A. The gap IS the finding, and it is the one number that "
                       "teaches a reader why parlay pricing matters.",
        "effort": "small, given a joint estimate",
        "depends_on": "QM-09",
        "does_not_do": "It does not produce an official-sourced joint.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/correlations.json",
    },
    {
        "id": "SM-10",
        "title": "Define luck with one formula and print it on the leaderboard",
        "problem": (
            "'Removed luck' currently means two different procedures in two places, "
            "and a reader cannot tell which produced a given p-value."),
        "evidence": "The no-skill simulation and the BH correction are both applied "
                    "and both published, but neither is named on the leaderboard row.",
        "options": [
            "A: name the procedure in a column on every row",
            "B: define a single composite and use only it",
        ],
        "recommended": "A, because the two procedures answer different questions "
                       "and collapsing them loses information.",
        "effort": "small",
        "depends_on": "QM-10 / D-4",
        "does_not_do": "It does not make either procedure correct.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/strategy_results.json",
    },
    {
        "id": "SM-11",
        "title": "Print the read time in the page header, not only in the data",
        "problem": (
            "Every number here has a read time in its JSON and none of it is in the "
            "page chrome. A reader who screenshots a table takes a number with no "
            "date attached."),
        "evidence": "Standings change weekly; the injury report changes daily.",
        "options": [
            "A: a header line 'all official values read at <time>'",
            "B: per-table read time",
            "C: both",
        ],
        "recommended": "C: a header for the page and a per-table stamp where tables "
                       "come from different reads.",
        "effort": "small",
        "depends_on": "QM-11",
        "does_not_do": "It does not refresh anything.",
        "source": "https://www.nfl.com/injuries/",
    },
    {
        "id": "SM-12",
        "title": "Give every market row a 'last successfully read' stamp and a blank policy",
        "problem": (
            "If the provider disappears, the existing rows would silently become "
            "history with no signal that they are history."),
        "evidence": "One provider, no contract, no SLA.",
        "options": [
            "A: blank the affected rows and show 'source unavailable'",
            "B: keep the last values, stamped with their age",
            "C: demote every strategy that depends on the source",
        ],
        "recommended": "B for the archive, A for any live decision surface. History "
                       "is fine if labelled; a stale live number is not.",
        "effort": "small",
        "depends_on": "QM-12 / D-5",
        "does_not_do": "It does not replace the source.",
        "source": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
                  "events/401873052/competitions/401873052/odds",
    },
    {
        "id": "SM-13",
        "title": "Designate one canonical NFL workspace and make the other sixteen report to it",
        "problem": (
            "Seventeen workspaces publish overlapping NFL material with different "
            "numbers for the same week. A reader cannot tell which is current, and "
            "each new session adds one more."),
        "evidence": "The root navigation lists sixteen NFL workspaces; this page is "
                    "the seventeenth. At least three publish own lines for week 10 "
                    "with different values.",
        "options": [
            "A: designate one canonical and convert the rest to frozen archives with "
            "a banner and a single link to the canonical",
            "B: keep all workspaces and add a comparison page",
            "C: leave as is",
        ],
        "recommended": "A. B doubles the reading and C is what produced the problem.",
        "effort": "medium - mostly banners and navigation",
        "depends_on": "QM-13 / D-1",
        "does_not_do": "It does not decide which one is best; that is the owner's "
                       "call.",
        "source": "https://sassnarep3-star.github.io/Own4/",
    },
    {
        "id": "SM-14",
        "title": "Say in one sentence what the reward is, on the leaderboard itself",
        "problem": (
            "'Rewards for top strategies' reads as money to one reader and as points "
            "to another. Everything downstream of that sentence changes with the "
            "reading."),
        "evidence": "Zero of 1,000 reward points have ever been awarded; no money has "
                    "been at risk anywhere in this repository.",
        "options": [
            "A: 'research points, no money at risk' as a fixed subtitle",
            "B: define a paper bankroll and publish it as such",
            "C: define real stakes (requires a jurisdiction and licence decision)",
        ],
        "recommended": "A now. C is a legal question before it is a design question.",
        "effort": "trivial for A",
        "depends_on": "QM-14 / D-3",
        "does_not_do": "It does not make the leaderboard meaningful; it makes it "
                       "honest.",
        "source": "https://www.ncpgambling.org/help-treatment",
    },
    {
        "id": "SM-15",
        "title": "Convert 'verified' from an adjective into a count, per namespace",
        "problem": (
            "Several pages say their data is verified. A repo-wide scan finds 1,268 "
            "published table rows with no source link at all, and this session "
            "caught a fabricated block in its own first draft."),
        "evidence": "11,584 published rows scanned; 1,268 without a source link. "
                    "Injury block DP-05 in this namespace was wrong before it was "
                    "re-read.",
        "options": [
            "A: publish 'cells checked / cells total' per namespace, updated each "
            "pass",
            "B: keep prose claims of verification",
        ],
        "recommended": "A. A count can be argued with; an adjective cannot.",
        "effort": "medium, incremental",
        "depends_on": "QM-15",
        "does_not_do": "It does not fix the 1,268 rows, only sizes the problem.",
        "source": "https://sassnarep3-star.github.io/Own4/",
    },
    {
        "id": "SM-16",
        "title": "Show the losing strategies at full size, in rank order, with no toggle",
        "problem": (
            "A leaderboard that shows winners first and hides the rest teaches the "
            "wrong lesson. Here every strategy loses, and that is the most "
            "informative fact on the page."),
        "evidence": "0 of 15 pass the signal gates; 5 of 15 are profitable in sample; "
                    "0 pass both.",
        "options": [
            "A: one table, rank order, losers included, no filtering",
            "B: winners first with a 'show all' toggle",
        ],
        "recommended": "A.",
        "effort": "trivial",
        "depends_on": "nothing",
        "does_not_do": "It does not make the sample bigger.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/leaderboard.json",
    },
]

D = [
    {
        "id": "D-1",
        "question": "Which NFL workspace is canonical?",
        "blocks": "Any further site-building being useful rather than additive.",
        "options": [
            "A: this namespace, nfl-market",
            "B: nfl-lines (the largest prior analytical namespace)",
            "C: a new front page that reports to all of them and owns the navigation",
        ],
        "evidence": "Seventeen workspaces; the root nav lists sixteen; overlapping "
                    "own lines for the same week disagree.",
        "consequence_of_waiting": (
            "Each session adds a workspace. The count went from eleven to seventeen "
            "in two days."),
        "source": "https://sassnarep3-star.github.io/Own4/",
    },
    {
        "id": "D-2",
        "question": "Which price snapshots count for grading?",
        "blocks": "Every ROI and every 'beats the market' claim.",
        "options": [
            "A: open", "B: a fixed lead time before kickoff", "C: close",
            "D: all three published, rank on the worst",
        ],
        "evidence": "13 of 14 week-10 games have no true close yet; the choice "
                    "changes each ROI.",
        "consequence_of_waiting": (
            "Numbers get published against whichever snapshot flatters them, and "
            "then have to be withdrawn."),
        "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
    },
    {
        "id": "D-3",
        "question": "Is the reward real money, paper units, or points?",
        "blocks": "The demotion gate's tolerances, drawdown limits, and whether the "
                  "gambling-help framing is sufficient.",
        "options": ["A: points, no money at risk", "B: paper bankroll",
                    "C: real stakes (needs a jurisdiction and licence answer first)"],
        "evidence": "0 of 1,000 reward points awarded; no money anywhere in the repo.",
        "consequence_of_waiting": (
            "Design decisions keep being made as if money were involved and as if "
            "it were not, sometimes on the same page."),
        "source": "https://www.ncpgambling.org/help-treatment",
    },
    {
        "id": "D-4",
        "question": "What is the operational definition of 'removing luck'?",
        "blocks": "The leaderboard's definition.",
        "options": [
            "A: no-skill simulation only",
            "B: multiple-testing correction only",
            "C: both, reported separately",
            "D: a variance decomposition across bets",
        ],
        "evidence": "Two procedures are already in use and neither is named on the "
                    "leaderboard rows.",
        "consequence_of_waiting": "Two pages keep quoting p-values from different "
                                  "procedures as if comparable.",
        "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/"
                  "data/derived/strategy_results.json",
    },
    {
        "id": "D-5",
        "question": "What happens when the single price source disappears?",
        "blocks": "Any statement that the system is operational rather than an archive.",
        "options": ["A: blank the rows", "B: freeze and age-stamp them",
                    "C: demote everything that depends on them"],
        "evidence": "One provider, no contract, no SLA, no scheduled refresh.",
        "consequence_of_waiting": "A stale number gets read as a live one.",
        "source": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
                  "events/401873052/competitions/401873052/odds",
    },
]


if __name__ == "__main__":
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    out = {
        "generated_utc": "2026-11-14T00:00:00Z",
        "questions": Q, "suggestions": S, "decisions": D,
        "counts": {"questions": len(Q), "answered": sum(1 for q in Q if q["answer"]),
                   "suggestions": len(S), "decisions": len(D)},
        "how_to_use": (
            "Read the five decisions first. Every decision has options, the "
            "evidence for each, and the cost of waiting; none of them requires code. "
            "Then read the questions: each one states what is known, what is not, "
            "and what would settle it. Suggestions are last, because most of them "
            "depend on a decision above them."),
    }
    with open(os.path.join(here, "derived", "register.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote register.json:", out["counts"])

# Executive summary — NFL requirement register, round 2 (2026-11-18)

Session `arena/9242c387-own4`. Live: https://sassnarep3-star.github.io/Own4/nfl-req-review/

## What this is

A line-by-line round-2 re-check of the NFL requirement register, on 73 requirement rows, against official nfl.com pages read on 2026-11-18. It is a decision-readiness surface: each row states its status, the gate that blocks it, and the number that would clear it. It is not a betting product: it publishes no picks, no prices, and no strategy shown as eligible.

## What the official sources now settle

150 completed regular-season games through Week 10 (sum of W+L+T across 32 clubs divided by 2). Weeks 1-9 hold 136 games, and they reconcile to the official standings for 32 of 32 clubs on wins, losses, ties, points for and points against. Week 10 had 14 finals, all now on the official schedule page. Week 11 has 13 fixtures and 6 clubs on bye.

## What the data still gets wrong

The verified results feed holds 1 of the 14 Week-10 finals. The model's Week-11 row records 137 training games, against 136 official completed games through Week 9. The holdout split leaves 13 completed games in no split. One peer session's figure of 133 games through Week 9 is an arithmetic error, and its claim that no file publishes 136 is contradicted by the official arithmetic. Each is logged as a flag with its source link, owned by the peer namespace, and not edited here.

## What changed in the register

23 rows were re-verified in this round and 8 were downgraded from 'met' because their own artifact or source did not support the claim: A01, A02, A06, A07, C05, D01, E26, G07. Final register: 19 met, 50 partial, 2 blocked, 1 not started, 1 in progress.

## The injury data

The Lions' Kerby Joseph, Cade Mays and D.J. Reed are now shown with game status Out on the official Week-10 report. The Week-11 report is not yet published at the read time. The round-1 injury totals are internally inconsistent, and Cincinnati's count is unresolved (RF-13, RF-14).

## Decisions the owner needs to make

(1) One entry point for the 39 NFL namespaces at base eb6d8de (S-01). (2) Price-data policy, option (b) recommended (S-02). (3) Add the 13 missing Week-10 finals to the feed (S-03). (4) Freeze the corpus at 136 and name Week 10 as a prospective window (S-04). (5) Approve a daily injury capture from Wednesday (S-05). (6) Link this namespace from the root page (S-08). Each has its options on the Suggestions page.

## Limits

The sandbox cannot reach nfl.com directly (tested 2026-11-18, no response), so every official read was made with the page-fetch tool and is recorded with its URL and read date. Week-10 injury chunks 1-7 were not re-read, so the full injury table is unverified. Raw page text was not saved to the repository, so the reads carry URLs and read dates but no sha256 hash. The clone is shallow, so pre-registration commit hashes cannot be checked here (RF-18). The 38 peer namespaces were not re-read line by line.

Analysis only. Not wagering advice. Helpline: 1-800-MY-RESET (https://www.ncpgambling.org/help-treatment).

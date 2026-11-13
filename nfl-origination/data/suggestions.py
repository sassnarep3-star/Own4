"""The Suggestions / decision board.

This is the section the brief asks for so that a reviewer can compare options and choose a path
BEFORE any change is implemented. Each suggestion carries: context, the options considered, the
evidence available, the cost, the risk, its prerequisites, a recommendation, and the timing at
which a decision is actually needed.

The `timing` field is what makes it a decision board rather than a wish list:
  DECIDE NOW    a blocker; nothing downstream is safe until it is settled
  DECIDE LATER  cheap, reversible, or only matters once something else lands
  BLOCKED       cannot be acted on with the information available today
"""
import json
import pathlib

DOC_ID = "suggestions-2026-11-13"

S = [
    dict(id="S01", group="Data acquisition", timing="DECIDE NOW",
         title="Buy or license an archived NFL odds history",
         context="The NFL publishes no prices. Every ROI on this site is priced at an assumed -110, "
                 "so Gate G7 fails by construction and no strategy can ever reach a paid tier.",
         options=["License a commercial odds archive (e.g. a sports-data vendor)",
                  "Use the third-party nflverse line columns as a stand-in",
                  "Keep the assumed -110 and accept that no betting claim can be made"],
         evidence="Gate G7 is blocked; the only line column in the repository is third-party and "
                  "not licensed for redistribution.",
         cost="Vendor-dependent; the single largest line item in the project.",
         risk="Low technical risk, high cost. Buying the wrong granularity (open vs close, "
              "spread-only vs props) wastes the spend.",
         prerequisites=["S02 (legal position) before signing anything"],
         recommendation="Do this first. Nothing else in the betting half of the project can be "
                        "honest without it. Insist on CLOSE prices and, if props matter, archived "
                        "same-game-parlay prices too.",
         unblocks=["Q01"], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S02", group="Governance", timing="DECIDE NOW",
         title="Obtain a written legal position before publishing anything as more than research",
         context="The project publishes derived probabilities. Whether that is regulated depends "
                 "on the jurisdiction, which is not recorded anywhere in the repository.",
         options=["Written opinion from counsel in the operating jurisdiction",
                  "Keep everything labelled research points and publish no picks",
                  "Publish picks and accept the risk"],
         evidence="No jurisdiction, licence or entity is recorded in the repository.",
         cost="One legal review.",
         risk="High if ignored. Reputational and possibly regulatory.",
         prerequisites=[],
         recommendation="Settle before rewards are described as anything other than points. Until "
                        "then the leaderboard pays research points only, which is what it does.",
         unblocks=["Q02", "Q15"], sources=["https://www.ncpgambling.org/help-treatment"]),

    dict(id="S03", group="Injuries and depth", timing="DECIDE NOW",
         title="Publish only article-confirmed lineup changes, or buy a depth-chart feed",
         context="The brief asks for 2nd/3rd/4th-string deficiency tracking. The NFL's own depth "
                 "chart URL is a 404, so any string label produced today would be invented.",
         options=["Publish only changes an official article explicitly names (8 this week)",
                  "Buy a commercial depth-chart feed",
                  "Derive strings from snap counts, if a snap-count source is licensed"],
         evidence="nfl.com/depth-charts/ returns 404 (re-checked 2026-11-13). No snap-count feed "
                  "exists in the repository.",
         cost="Zero for option 1; vendor-dependent for 2 and 3.",
         risk="Option 1 is honest but sparse. Options 2-3 introduce a source that is not the NFL.",
         prerequisites=[],
         recommendation="Stay on option 1 now. It is the only one that survives the "
                        "no-invention rule. Revisit if a licensed snap-count feed (S09) is bought.",
         unblocks=["Q03"], sources=["https://www.nfl.com/depth-charts/"]),

    dict(id="S04", group="Data acquisition", timing="DECIDE NOW",
         title="Start capturing the official injury report into a dated snapshot every week",
         context="nfl.com/injuries/ shows only the current week. Because nothing was archived, no "
                 "injury effect can ever be measured retrospectively.",
         options=["Capture weekly snapshots from now on",
                  "Try to reconstruct history from news articles",
                  "Accept that injury effects stay unmeasurable"],
         evidence="Only the current week is addressable on the official site.",
         cost="Trivial: one fetch and one commit per week.",
         risk="None. The only cost of not doing it is that the data never exists.",
         prerequisites=[],
         recommendation="Start this week. It is the cheapest action on the board with the longest "
                        "payoff: in two seasons there is a usable archive and S03/S05 become "
                        "answerable with evidence.",
         unblocks=["Q04"], sources=["https://www.nfl.com/injuries/"]),

    dict(id="S05", group="Injuries and depth", timing="BLOCKED",
         title="Convert injuries into points with a measured model rather than an assumed weight",
         context="This site applies a disclosed, capped weight to official designations (OUT 0.50, "
                 "DOUBTFUL 0.25, QUESTIONABLE 0.10 points of rating, capped at 3.0 per club) and "
                 "publishes the result as a band, because the input cannot distinguish a starter "
                 "from a fourth-string player.",
         options=["Keep the disclosed band (current)",
                  "Fit a weights model once snap counts exist",
                  "Drop injury adjustment from the line entirely"],
         evidence="Question Q05 has no verified answer. C9 (injury vs margin) is blank.",
         cost="Low now; a real fit needs S04 plus a snap-count source.",
         risk="The current weights are an assumption. The band makes that visible, but a reader "
              "could still over-read it.",
         prerequisites=["S04", "S09"],
         recommendation="Keep the band and keep it labelled an assumption. Do not let it become a "
                        "point estimate until it is fitted.",
         unblocks=["Q05"], sources=["https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"]),

    dict(id="S06", group="Product", timing="DECIDE NOW",
         title="Buy archived same-game-parlay prices before building any prop strategy",
         context="Real dependence is measured: QB passing yards over and WR1 receiving yards over "
                 "in the same team-game co-occur 1.45x more often than independence predicts "
                 "(phi = 0.346, n = 803). But books reprice correlated legs, and no SGP price "
                 "exists here to compare against.",
         options=["Buy SGP price history", "Publish the dependence fact and stop there",
                  "Assume no repricing (known to be wrong)"],
         evidence="Correlation C5 computed; C8 blank.",
         cost="Vendor-dependent; smaller than S01 and often bundled with it.",
         risk="Without it, any prop strategy is untestable and would be published as unsupported.",
         prerequisites=["S01"],
         recommendation="Bundle with S01 if the vendor offers it. Until then publish the dependence "
                        "and explicitly say the price is unknown — which is what the site does.",
         unblocks=["Q09"], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S07", group="Governance", timing="DECIDE NOW",
         title="Adopt a written skill definition and reward rule before any reward is paid",
         context="The proposal on this site: a strategy is skilful only if (a) it survives "
                 "Benjamini-Hochberg across every test run including placebos, (b) its "
                 "week-clustered 95% CI on ROI is entirely above zero, and (c) no single season "
                 "supplies more than half its profit.",
         options=["Adopt the proposal as written",
                  "Adopt a looser rule (point estimate above zero)",
                  "Adopt a stricter rule (require live, forward-recorded results too)"],
         evidence="Every strategy tested here fails at least one of (a)-(c); so does the placebo-"
                  "free version of the screen. The rule rejects our own best result.",
         cost="Zero.",
         risk="A loose rule pays for luck. The looser option above would have paid two strategies "
              "here, both of which the placebo test shows are noise.",
         prerequisites=["S02"],
         recommendation="Adopt as written, and add the forward-record requirement before any money "
                        "is attached.",
         unblocks=["Q11", "Q15"], sources=["https://www.nfl.com/standings/league/2026/REG"]),

    dict(id="S08", group="Governance", timing="DECIDE NOW",
         title="Review the third-party archive's licence before anything is redistributed",
         context="The game-level archive is a public GitHub repository used here as the only "
                 "source of historical games, because the NFL publishes no downloadable log.",
         options=["Review the licence line by line", "Stop redistributing the raw file and publish "
                  "only derived values", "Replace it with a licensed feed"],
         evidence="The archive's terms were not reviewed in this session; flagged as F-07.",
         cost="An hour of reading.",
         risk="Redistribution without review could breach the terms.",
         prerequisites=[],
         recommendation="Review it. In the meantime the site publishes derived values with "
                        "attribution and the raw file is untouched in its original peer namespace.",
         unblocks=["Q13"], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S09", group="Data acquisition", timing="DECIDE NOW",
         title="Obtain a player-level game log and a snap-count feed",
         context="Without per-game player logs there is no player-prop model, no snap counts, and "
                 "no way to tell a starter from a backup.",
         options=["License an official or commercial feed", "Use the unofficial nflverse player "
                  "stats", "Do without and keep props blocked"],
         evidence="Q14 has no verified answer. C9 and the second prop pair (C6) are blank.",
         cost="Vendor-dependent.",
         risk="An unofficial feed reintroduces the same third-party problem as S08.",
         prerequisites=["S02", "S08"],
         recommendation="License if props are a real goal. Otherwise keep props blocked and say so, "
                        "which is the current position.",
         unblocks=["Q14"], sources=["https://www.nfl.com/stats/"]),

    dict(id="S10", group="Product", timing="DECIDE NOW",
         title="Pick one canonical NFL dashboard and archive the other eleven",
         context="There were eleven NFL namespaces before this one; this is the twelfth. Four "
                 "publish own lines, five publish question registers, six publish suggestions. A "
                 "reader cannot tell which is current, and every new session re-does work.",
         options=["Declare this namespace canonical and retire the rest to an archive folder",
                  "Declare one of the existing eleven canonical and make this an appendix",
                  "Leave all twelve and add a chooser page"],
         evidence="Repo review counts the overlap; the root dashboard links to eight NFL "
                  "destinations.",
         cost="A restructuring commit, plus link repair.",
         risk="Deleting peer work is forbidden by the board protocol; archiving preserves it but "
              "breaks inbound links.",
         prerequisites=[],
         recommendation="Option 1, but as a MOVE to an `archive/` folder with a redirect stub per "
                        "page, so nothing is lost and no link 404s. Do not delete anything.",
         unblocks=["Q16"], sources=["https://sassnarep3-star.github.io/Own4/"]),

    dict(id="S11", group="Method", timing="DECIDE NOW",
         title="Establish whether the archive's line is the close or an earlier snapshot",
         context="The sign convention was measured (IC-04) and is correct, but 'when in the week' "
                 "the line was taken is unknown. Beating an early line is a different claim from "
                 "beating the close.",
         options=["Ask the archive maintainers / read the archive's own documentation",
                  "Compare against a licensed close (S01)",
                  "Downgrade every line-based claim to 'against an undated line'"],
         evidence="Q18 is partial for exactly this reason.",
         cost="An email or a documentation read.",
         risk="Low, but it caps the strength of any value claim.",
         prerequisites=[],
         recommendation="Do option 3 now (it is free and conservative) and option 1 in parallel.",
         unblocks=["Q18"], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S12", group="Site", timing="DECIDE NOW",
         title="Keep this namespace's verification harness as the merge gate for every future session",
         context="The build fails on a broken local link, an unsourced table row, or a "
                 "non-reproducible derived number. Three of those failures already caught real "
                 "defects during this session.",
         options=["Run it in CI on every PR", "Run it only before a release", "Skip it"],
         evidence="The placebo caught a sign bug; IC-04 caught the same bug a second way; the "
                  "row-source checker caught a caption with no link.",
         cost="Under a minute of CI time.",
         risk="None.",
         prerequisites=[],
         recommendation="Run it on every PR that touches this namespace, and recommend the same "
                        "harness pattern to the other namespaces.",
         unblocks=[], sources=["https://github.com/sassnarep3-star/Own4"]),

    dict(id="S13", group="Analysis", timing="DECIDE LATER",
         title="Add a weather term, but only for outdoor games with a verified forecast",
         context="Weather plausibly affects totals. This site does not model it, so an outdoor "
                 "December game is treated exactly like a dome game.",
         options=["Add a forecast term for outdoor games", "Add a dome/outdoor indicator only",
                  "Leave it out"],
         evidence="The archive carries roof, surface, temp and wind columns; values for future "
                  "games cannot be verified.",
         cost="Low modelling cost, but a forecast feed is needed for live use.",
         risk="A bad forecast is worse than no forecast.",
         prerequisites=["A verifiable forecast source"],
         recommendation="Add the dome/outdoor indicator first because it is already in the archive, "
                        "and only add the numeric term with a sourced forecast.",
         unblocks=[], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S14", group="Analysis", timing="DECIDE LATER",
         title="Test the rest term properly before believing it",
         context="Rest differential shows r = 0.035 against margin on 7,103 games — detectable but "
                 "tiny, explaining about 0.1% of variance. A naive reading of it once produced a "
                 "7-point disagreement with the market in a peer namespace.",
         options=["Add a small rest term", "Leave it out", "Add a short-week dummy only"],
         evidence="C4 is published with its CI.",
         cost="Low.",
         risk="Overfitting a 0.1%-variance effect is the classic way to build a fake edge.",
         prerequisites=[],
         recommendation="Add the short-week dummy only, and only if it survives the same gates.",
         unblocks=[], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S15", group="Site", timing="DECIDE LATER",
         title="Publish a forward-record ledger so future results cannot be back-fitted",
         context="Backtests can be re-run until something looks good. A dated, committed forecast "
                 "made BEFORE kick-off cannot be revised afterwards.",
         options=["Commit next week's lines before kick-off and grade them afterwards",
                  "Rely on the walk-forward backtest alone"],
         evidence="The thirteen Week 10 lines on this site are already dated and committed before "
                  "kick-off; they are the first entry in such a ledger.",
         cost="Minutes per week.",
         risk="None. It only ever constrains the project, which is the point.",
         prerequisites=[],
         recommendation="Do it. Grade Week 10 after it is played and publish the score without "
                        "editing the forecast.",
         unblocks=[], sources=["https://www.nfl.com/schedules/2026/by-week/week-10"]),

    dict(id="S16", group="Analysis", timing="DECIDE LATER",
         title="Extend the model with a quarterback adjustment once a player feed exists",
         context="The current model knows only points scored and allowed. It cannot see that a "
                 "starting quarterback changed, which is the single largest in-week information "
                 "event (six of the eight confirmed lineup changes this week are at QB).",
         options=["Add a QB indicator once a player feed exists", "Keep the club-level model",
                  "Hand-adjust for QB changes (rejected: not reproducible)"],
         evidence="Six of eight confirmed lineup changes are quarterbacks.",
         cost="A player feed (S09) plus modelling time.",
         risk="Hand adjustments are unreproducible and would break G10.",
         prerequisites=["S09"],
         recommendation="Wait for the feed. Do not hand-adjust.",
         unblocks=[], sources=["https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"]),

    dict(id="S17", group="Product", timing="DECIDE NOW",
         title="Publish the null result as the headline, not as a footnote",
         context="The honest result of this session is that nothing works: the model loses to the "
                 "closing line, no strategy survives FDR, and zero reward points are awarded.",
         options=["Headline the null result (current)", "Headline the forecast MAE that does beat "
                  "the naive baseline", "Headline nothing until something works"],
         evidence="Gates G4, G5, G8 and G9 all fail for every strategy.",
         cost="Zero.",
         risk="A project that only ever reports nulls looks unsuccessful — but reporting a "
              "non-null that isn't there is worse.",
         prerequisites=[],
         recommendation="Keep the null as the headline. It is the finding.",
         unblocks=[], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S18", group="Analysis", timing="DECIDE LATER",
         title="Increase the sample before making any claim about 2026 specifically",
         context="All skill measurement here is on 2018-2025 because 2026 has only 136 games. Any "
                 "statement about this season's model quality is under-powered.",
         options=["Wait for more 2026 games", "Pool seasons", "Report 2026 separately with an "
                  "explicit under-powered warning"],
         evidence="G2 needs 1,000 out-of-sample games for a skill claim; a single season is ~272.",
         cost="Time.",
         risk="Reporting a single season invites reading noise as signal.",
         prerequisites=[],
         recommendation="Pool seasons (current) and label any single-season figure as descriptive "
                        "only.",
         unblocks=[], sources=["https://github.com/nflverse/nfldata"]),

    dict(id="S19", group="Site", timing="DECIDE LATER",
         title="Add a one-screen 'what changed since last week' page",
         context="The site is a snapshot. A reader returning next week wants the delta: new "
                 "results, new injuries, new lines, gate movements.",
         options=["Generate a delta page from two dated snapshots", "Leave the snapshot approach"],
         evidence="The data files are already dated, so a diff is mechanical.",
         cost="Small.",
         risk="None.",
         prerequisites=["S15"],
         recommendation="Add it once a second snapshot exists.",
         unblocks=[], sources=["https://www.nfl.com/schedules/2026/by-week/week-10"]),

    dict(id="S20", group="Analysis", timing="DECIDE LATER",
         title="Model the total separately from the margin",
         context="The own total currently uses only club pace (offence plus defence divided by "
                 "two) and has a very large out-of-sample MAE (42.5 across all seasons), so it "
                 "carries no usable signal.",
         options=["Fit a dedicated totals model", "Drop the total entirely", "Label it clearly as "
                  "uninformative (current)"],
         evidence="The total MAE is far worse than the closing total's.",
         cost="Modelling time.",
         risk="Low; a bad total is already labelled as such.",
         prerequisites=["S01"],
         recommendation="Drop the originated total from the published line until it beats the "
                        "naive mean total, and keep the number only on the audit page.",
         unblocks=[], sources=["https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"]),

    dict(id="S21", group="Governance", timing="DECIDE NOW",
         title="Make the coordination board machine-checked",
         context="The board protocol depends on sessions honestly claiming scopes. Two peer "
                 "sessions' notices already record collisions that a check could have caught.",
         options=["Add a CI check that a PR's changed paths fall inside a claimed scope",
                  "Keep relying on prose"],
         evidence="The repo review lists overlapping namespaces and prior collision records.",
         cost="An hour.",
         risk="None.",
         prerequisites=[],
         recommendation="Add the check. It is the only way the protocol survives more sessions.",
         unblocks=[], sources=["https://sassnarep3-star.github.io/Own4/"]),

    dict(id="S22", group="Product", timing="BLOCKED",
         title="Publish a live in-week injury-adjusted line",
         context="A line that moves as Friday practice reports land would be the most useful "
                 "product here. It needs an intraday injury feed and a price to compare against.",
         options=["Build it once a feed and a price exist", "Publish a daily manual snapshot",
                  "Do not build it"],
         evidence="Only a weekly snapshot is available; there is no price.",
         cost="Feed cost plus automation.",
         risk="A moving line with no price is entertainment, not analysis.",
         prerequisites=["S01", "S04", "S09"],
         recommendation="Blocked until S01 and S09 land. Do not build a manual version: it would "
                        "violate the no-manual-input requirement.",
         unblocks=[], sources=["https://www.nfl.com/injuries/"]),
]

# The order a reviewer should actually work through them.
PATH = [
    ("Week 1 — settle what gates everything", ["S02", "S07", "S10", "S17"]),
    ("Week 1-2 — start the free clocks", ["S04", "S12", "S21", "S15"]),
    ("Then decide whether this is a betting project at all", ["S01", "S06", "S11"]),
    ("Only if yes: buy the rest of the inputs", ["S09", "S03", "S05"]),
    ("Hygiene and small wins", ["S08", "S14", "S20", "S13", "S18", "S19"]),
    ("Blocked until the inputs exist", ["S22"]),
]

GROUPS = {
    "Data acquisition": "What must be bought or captured before a claim is possible.",
    "Injuries and depth": "The gap between what the brief asks for and what the league publishes.",
    "Governance": "Legal, licence and anti-luck rules that bind the rest.",
    "Analysis": "Modelling work that only pays off after the inputs land.",
    "Product": "What the site should be.",
    "Site": "How to keep the artefact trustworthy.",
}

DOC = {
    "id": DOC_ID,
    "intro": ("Each row is a decision, not a task list entry. 'Timing' says when a decision is "
              "actually needed: DECIDE NOW means something downstream is unsafe until it is "
              "settled. Costs and risks are stated qualitatively because no vendor quote exists."),
    "columns": ["id", "group", "timing", "suggestion", "recommendation"],
    "suggestions": S,
    "recommended_path": PATH,
    "groups": GROUPS,
}


def main():
    out = pathlib.Path(__file__).with_suffix(".json")
    DOC["summary"] = {
        "total": len(S),
        "decide_now": sum(1 for x in S if x["timing"] == "DECIDE NOW"),
        "decide_later": sum(1 for x in S if x["timing"] == "DECIDE LATER"),
        "blocked": sum(1 for x in S if x["timing"] == "BLOCKED"),
    }
    out.write_text(json.dumps(DOC, indent=1) + "\n")
    s = DOC["summary"]
    print("suggestions: %d (%d now, %d later, %d blocked)"
          % (s["total"], s["decide_now"], s["decide_later"], s["blocked"]))


if __name__ == "__main__":
    main()

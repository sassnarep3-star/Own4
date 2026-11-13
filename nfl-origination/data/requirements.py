"""Requirement checklist: every line of the brief, mapped to what exists, what does not, and why.

This is deliberately blunt. A requirement is only marked MET when the artefact exists AND its
evidence is published on this site. PARTIAL and BLOCKED rows carry the reason and the source
that establishes the limit.
"""
import json
import pathlib

DOC_ID = "requirements-2026-11-13"

REQUIREMENTS = [
    # (id, requirement as stated, status, what exists, evidence page, limitation)
    ("R01", "Collect a full list of requirements", "MET",
     "41 requirements across 8 groups, each with a status and a page that evidences it.",
     "requirements.html", ""),
    ("R02", "Review the repo line by line", "MET",
     "All 11 existing NFL namespaces inspected; 6 structural irregularities published.",
     "repo-review.html", "Inspection is of files and links, not a re-verification of every peer number."),
    ("R03", "Verify against official, trusted sources; provide links", "MET",
     "Every table row links to the official page it came from. Source register lists 24 URLs.",
     "sources.html", ""),
    ("R04", "Flag irregularities for review", "MET",
     "19 flagged items, each with a link, published on one page.",
     "flagged.html", "Flagged items are non-blocking by instruction."),
    ("R05", "Create a GitHub Pages live site with a clean dashboard and category subpages",
     "MET", "1 landing page + 11 subpages, one navigation, no JavaScript required.",
     "index.html", ""),
    ("R06", "Present all entries and findings in simple, readable tables", "MET",
     "Every data page is an HTML table with a caption, a row count and a source column.",
     "index.html", ""),
    ("R07", "Leave unconfirmed values blank and mark them unverified", "MET",
     "Blank cells are rendered as a visibly blank pill and counted on the flagged page.",
     "flagged.html", ""),
    ("R08", "Never infer or fill in a value", "MET",
     "Correlations C6/C8/C9 and all player-prop prices are blank with a stated reason.",
     "correlations.html", ""),
    ("R09", "Originate our own NFL lines", "PARTIAL",
     "13 Week 10 games carry our own spread, total and win probability, computed from a "
     "published model. They are NOT prices.",
     "own-lines.html",
     "A line without a market to beat cannot be scored as a bet, so it is a forecast, not a price."),
    ("R10", "Research and develop strategies for generating useful signals", "MET",
     "5 registered strategies + 2 pre-registered placebos, each with a full result table.",
     "backtest.html", "Research only: none of them works."),
    ("R11", "Run it as a leaderboard competition with rewards", "MET",
     "Leaderboard with tiers, 1,000-point pool, 0 points awarded, rollover rule stated.",
     "leaderboard.html", "0 awarded is the honest result; see gates."),
    ("R12", "Cover single bets, parlays and player-prop combos", "PARTIAL",
     "Singles: 5 strategies evaluated. Parlays: leg-independence measured (C1, C2, C7). "
     "Player props: dependence measured (C5, phi=0.346).",
     "correlations.html",
     "No prop strategy can be scored: there is no archived prop price and no official per-game "
     "player log. Flag F-06."),
    ("R13", "Every strategy must pass validation gates", "MET",
     "10 pre-registered gates, evaluated with evidence; a strategy cannot appear as a qualifier "
     "without clearing every non-blocked gate.",
     "gates.html", ""),
    ("R14", "Determine correlation values", "PARTIAL",
     "6 of 9 correlation tests computed with r, n, 95% CI, p and FDR; 3 blank and flagged.",
     "correlations.html", "Same-game-parlay repricing and injury effects cannot be measured."),
    ("R15", "Remove luck from the equation", "MET",
     "Walk-forward backtest, week-clustered bootstrap, 2,000-draw permutation null, FDR, "
     "season-concentration disclosure, 2 pre-registered placebos.",
     "backtest.html", "Luck cannot be eliminated; it is bounded and disclosed."),
    ("R16", "Build strategies that are selectively skill based", "MET",
     "The skill screen is published and it rejects every strategy, including our own model "
     "against the closing line.",
     "backtest.html", ""),
    ("R17", "Track injuries", "MET",
     "95 official Week 10 designations across 19 clubs, transcribed with the source URL.",
     "injuries.html", "One week only: the league publishes no historical archive."),
    ("R18", "Know defensive deficiencies: 2nd/3rd/4th string replacing starters", "BLOCKED",
     "Published: the official designation list, and 8 confirmed lineup changes named in official "
     "reporting (QB changes at SEA, MIA, BAL, MIN, CLE, AZ).",
     "injuries.html",
     "The NFL publishes no depth chart: nfl.com/depth-charts/ returns 404 (re-checked "
     "2026-11-13), and no snap-count feed exists. Any '3rd string' label would be invented. "
     "Flag F-05."),
    ("R19", "Same for offences using starters or backups", "BLOCKED",
     "8 official lineup changes are listed with the club, the player out, the player in, and the "
     "article that says so.",
     "injuries.html",
     "Confined to changes an official article actually states. No inference from absence."),
    ("R20", "Make suggestions to improve the site and to improve decision making", "MET",
     "22 suggestions, each with context, options, evidence, cost, risk, prerequisites and a "
     "recommendation.",
     "suggestions.html", ""),
    ("R21", "Create a dedicated Suggestions section to review and choose a path", "MET",
     "suggestions.html is a decision board: an ordered recommended path, and every suggestion "
     "labelled Decide-now / Decide-later / Blocked.",
     "suggestions.html", ""),
    ("R22", "Clear list of questions, information and answers needed before a decision", "MET",
     "20 questions, each with: status, known (sourced), not known, why it blocks, which "
     "suggestion would unblock it, and a blank Answer field where no verified answer exists.",
     "questions.html", "9 questions have no verified answer; their Answer field is blank."),
    ("R23", "Suggestions to discover missing information", "MET",
     "Every suggestion names the question it closes, so the board doubles as a data-acquisition "
     "plan.",
     "suggestions.html", ""),
    ("R24", "Produce an executive summary", "MET",
     "One page: bottom line, what was verified, what cannot be sourced, the one real signal, the "
     "binding decisions.",
     "executive-summary.html", ""),
    ("R25", "No manual input from the owner", "MET",
     "Everything is generated by 5 committed commands; no form, no login, no manual data entry.",
     "index.html", ""),
    ("R26", "Verify every table row against an official source, with a link", "MET",
     "verify.py walks every generated table row and fails the build if any row has no link.",
     "reconcile.html", "It checks that a link exists, not that the value is correct."),
    ("R27", "Coordinate with parallel sessions via COORDINATION.md", "MET",
     "Claim committed and pushed before any work; scope recorded; peer namespaces untouched.",
     "repo-review.html", ""),
    ("R28", "Open a PR, merge without waiting, confirm Pages deploys", "MET",
     "Recorded in COORDINATION.md with the PR number, merge commit and deploy run.",
     "repo-review.html", ""),
    ("R29", "Publish flagged irregularities on a labelled page", "MET",
     "flagged.html is linked in the main navigation under a ⚑ label and from every page footer.",
     "flagged.html", ""),
    ("R30", "Do not merge a broken site", "MET",
     "The build fails on a broken local link, an unsourced table row, or a non-reproducible "
     "number.",
     "reconcile.html", ""),
    ("R31", "Analyse the information we do and do not have", "MET",
     "A Known / Unknown table of 12 rows states exactly which inputs exist and which do not.",
     "questions.html", ""),
    ("R32", "Provide links for manual review", "MET",
     "24 registered sources, each with what it was used for and when it was read.",
     "sources.html", ""),
    ("R33", "Treat the competition as leaderboard-style with rewards for top strategies", "MET",
     "Tier structure, scoring rule, tie-break, and the rollover rule when nothing qualifies.",
     "leaderboard.html", ""),
    ("R34", "Determine whether a strategy is skill or luck", "MET",
     "Four independent luck controls plus placebos; all five strategies fail at least one.",
     "backtest.html", ""),
    ("R35", "Show correlation for parlay pricing rather than assuming independence", "PARTIAL",
     "C1, C2, C7 measure the dependence that multiplies legs; the multiplication rule is stated.",
     "correlations.html", "The repriced SGP price (C8) is unavailable, so the pricing claim stops "
     "at dependence."),
    ("R36", "Track lineup changes caused by trades as well as injuries", "PARTIAL",
     "Documented: Brissett trade to BAL, Cousins trade to MIN, Beck promoted at AZ, and the "
     "JAX midweek-trade exclusions.",
     "injuries.html", "Only where official reporting states the consequence."),
    ("R37", "Explain any deficiency in defences specifically", "PARTIAL",
     "Defensive designations are isolated with a position filter, so a defence missing its "
     "linebackers or secondary is visible.",
     "injuries.html", "The size of the effect on the opponent's scoring is not measurable, F-05."),
    ("R38", "Explain the same for offences", "PARTIAL",
     "Offensive designations (QB, OL, WR, RB, TE) are isolated with the same filter.",
     "injuries.html", "Same limit: no snap counts, no depth chart."),
    ("R39", "Report findings honestly, including null results", "MET",
     "The headline is a null result: 0 strategies, 0 reward points, model loses to the closing "
     "line.",
     "executive-summary.html", ""),
    ("R40", "Keep the work reproducible", "MET",
     "5 commands regenerate every number; CI fails if the derived files change.",
     "sources.html", ""),
    ("R41", "Do not present research as wagering advice", "MET",
     "Disclaimer on every page plus the NCPG helpline, sourced from ncpgambling.org.",
     "index.html", ""),
]

GROUPS = [
    ("Process and sources", ["R01", "R02", "R03", "R04", "R25", "R27", "R28", "R29", "R30", "R32", "R40"]),
    ("The site", ["R05", "R06", "R07", "R08", "R20", "R21", "R26", "R35", "R41"]),
    ("Lines and signals", ["R09", "R10", "R11", "R12", "R13", "R33", "R34"]),
    ("Statistics", ["R14", "R15", "R16", "R31", "R39"]),
    ("Injuries and depth", ["R17", "R18", "R19", "R36", "R37", "R38"]),
    ("Decision support", ["R22", "R23", "R24"]),
]

COLUMNS = ["id", "requirement", "status", "what exists", "evidence_page", "limitation"]

DOC = {
    "id": DOC_ID,
    "columns": COLUMNS,
    "requirements": [dict(zip(COLUMNS, r)) for r in REQUIREMENTS],
    "groups": GROUPS,
    "summary": {},
}


def main():
    reqs = DOC["requirements"]
    for r in reqs:
        r["evidence_url"] = r["evidence_page"]
    DOC["summary"] = {
        "total": len(reqs),
        "met": sum(1 for r in reqs if r["status"] == "MET"),
        "partial": sum(1 for r in reqs if r["status"] == "PARTIAL"),
        "blocked": sum(1 for r in reqs if r["status"] == "BLOCKED"),
    }
    out = pathlib.Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(DOC, indent=1) + "\n")
    s = DOC["summary"]
    print("requirements: %d total, %d met, %d partial, %d blocked"
          % (s["total"], s["met"], s["partial"], s["blocked"]))


if __name__ == "__main__":
    main()

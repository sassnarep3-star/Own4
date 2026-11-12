"""Suggestions board: a review-and-choose surface, not a to-do list.

Each suggestion carries: the context, the options considered, the evidence for each,
a cost, a risk, and a recommendation. A reviewer is expected to accept, reject or
defer each one; nothing here is implemented silently.
"""

S = [
 dict(id="S01", group="Data integrity", title="Re-run the official reconciliation before every publish",
  context="The repo's own 120-game 2026 log was missing CHI@SEA (Week 8, 34-17). All 32 team records now recompute exactly, 160/160 cells, only after that game was added.",
  why_it_matters="A single missing game silently corrupts every rating that follows it. The error was invisible until the standings were recomputed from scratch.",
  options=[
    ("Add the reconciliation as a required CI step", "5/5 checks, ~1s runtime, zero cost", "Effort: low. Failure: none identified"),
    ("Rely on the peer data as published", "Fails: the log was incomplete", "Effort: none. Failure: silent rating corruption")],
  recommendation="Adopt the CI step. Make a failed reconciliation block the deploy.",
  evidence=[("repo: nfl-decision/scripts/01_results.py (5 checks)", "data.html"),
            ("Official 2026 standings", "https://www.nfl.com/standings/league/2026/REG"),
            ("The missing game", "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S02", group="Injuries and depth", title="Publish depth deficiencies only where an official article names the replacement",
  context="The brief asks for 2nd/3rd/4th-string tracking. No official NFL depth chart exists (nfl.com/depth-charts returns 404). 13 replacements are, however, named explicitly in official NFL.com reporting.",
  why_it_matters="You asked for no hallucinations. Labelling a player '3rd string' without an official chart would be exactly that. There are two honest choices: publish the 13 verified cases, or publish nothing.",
  options=[
    ("Publish the 13 article-verified replacements and label everything else BLOCKED", "13 rows, each with a quoted sentence and an nfl.com link", "Effort: low. Failure: the table is short"),
    ("Infer string depth from roster seniority or snap counts", "No official source supports this", "Effort: high. Failure: invented labels"),
    ("Buy a depth-chart feed", "Not yet priced or scoped", "Effort: unknown. Failure: recurring cost")],
  recommendation="Option 1 now, Option 3 on a two-week trial if depth data proves decision-relevant.",
  evidence=[("Official injury report, Week 10", "https://www.nfl.com/injuries/"),
            ("NFL.com depth charts (404)", "https://www.nfl.com/depth-charts/"),
            ("Depth-chart news roundup", "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S03", group="Model", title="Hold the injury adjustment at zero until it can be estimated",
  context="No official source publishes points-per-missing-starter. The archived score model already carries a 13.6-point residual standard deviation.",
  why_it_matters="An invented injury adjustment would look like precision while adding unmeasured noise. At n=136 current-season games, no injury effect is estimable anyway.",
  options=[
    ("Zero adjustment, disclosed", "Transparent; no false precision", "Effort: none. Failure: misses real injury effects"),
    ("Hand-set adjustment per position", "No evidence base", "Effort: medium. Failure: unfalsifiable and looks like data")],
  recommendation="Keep at zero. Revisit only when S16 has produced a multi-season injury archive.",
  evidence=[("repo: data/model_config.json", "own-lines.html")],
  cost="none", risk="low", decided_by="owner", status="recommended"),

 dict(id="S04", group="Product", title="Adopt one canonical NFL dashboard and mark the others as archive",
  context="Eight NFL namespaces exist: nfl/, nfl-research/, nfl-lab/, nfl-quant/, nfl-decisions/, nfl-hub/, nfl-audit/ and nfl-decision/. Three carry measured results and two independently reached the same blocking findings.",
  why_it_matters="A decision surface with five competing front doors cannot be used to make a decision. The user asked for a clean dashboard.",
  options=[
    ("nfl-decision/ becomes the decision layer; others become cited archives", "Only this namespace has a numbered question register, a numbered suggestions board and 160/160 official provenance", "Effort: low. Failure: some peer detail is one click deeper"),
    ("Merge all five namespace sites into one page tree", "Preserves everything but is a large, conflict-prone edit across other sessions' scopes", "Effort: high. Failure: high merge-conflict risk"),
    ("Leave all five live and unlinked", "Current state", "Effort: none. Failure: ambiguity persists")],
  recommendation="Option 1. Add a superseded banner to the older pages in a later, single-owner PR.",
  evidence=[("repo root", "https://github.com/sassnarep3-star/Own4")],
  cost="low", risk="medium", decided_by="owner", status="recommended"),

 dict(id="S05", group="Injuries and depth", title="Weight the depth signal by position scarcity, not by star power",
  context="A missing QB1 forces a different kind of replacement than a missing WR3. Officials named replacement QBs at SEA (Lock), MIA (McCord), BAL (Brissett, after an undrafted 3rd-stringer started), AZ (rookie Carson Beck) and CLE.",
  why_it_matters="QB is the only position where official NFL.com articles consistently confirm who starts. That makes QB depth the one place where a verified signal can exist today.",
  options=[
    ("Track QB depth only, with confirmed starters", "5 of the 13 verified cases are QB", "Effort: low. Failure: narrow"),
    ("Track every position equally", "Non-QB starters are rarely confirmed in official reporting", "Effort: high. Failure: mostly blank rows")],
  recommendation="Option 1, and treat 'backup QB confirmed starter' as the first candidate signal to test formally.",
  evidence=[("SEA QB", "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"),
            ("MIA QB", "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
            ("BAL QB", "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season")],
  cost="medium", risk="medium", decided_by="owner", status="proposed"),

 dict(id="S06", group="Validation", title="Split the leaderboard into two boards: forecast skill and betting ROI",
  context="Every betting strategy failed the pricing gate, so the current leaderboard is all zeros and cannot rank anything. Forecast skill is measurable today without any price.",
  why_it_matters="You asked for a leaderboard competition with rewards for top strategies. If every row is zero, the competition is dead on arrival. Forecast skill gives a live, honest competition immediately.",
  options=[
    ("Two pools: 600 forecast points (paid now) and 1000 betting points (held until G7 passes)", "Forecast skill is price-independent and already measured", "Effort: low. Failure: none identified"),
    ("Pay only on betting ROI", "All five strategies scored 0; the board would stay empty", "Effort: none. Failure: no competition")],
  recommendation="Adopt the two-board design. It is the single highest-leverage change on this page.",
  evidence=[("repo: data/gates.json (reward_policy)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json"),
            ("Measured results", "leaderboard.html")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S07", group="Validation", title="Report a season-concentration number on every strategy",
  context="S1 shows +1.09% overall, but 98% of the profit came from one season and only 5 of 8 seasons were positive.",
  why_it_matters="A single season carrying the P&L is the classic signature of luck. Hiding it behind an aggregate ROI is how honest projects become dishonest.",
  options=[
    ("Show max-single-season profit share and positive-season count next to every ROI", "Already computed in the backtest", "Effort: none. Failure: none"),
    ("Show ROI only", "Conventional but misleading", "Effort: none. Failure: reputation")],
  recommendation="Adopt. It costs nothing and it is already in the JSON.",
  evidence=[("repo: data/backtest.json (season_stats)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/backtest.json")],
  cost="none", risk="low", decided_by="owner", status="recommended"),

 dict(id="S08", group="Model", title="Stop refining the spread model; redirect effort to forecast skill",
  context="The walk-forward Elo explains far less than the market: corr(model margin, realised margin) = 0.357 vs corr(market spread, realised margin) = 0.430. The model also correlates 0.790 with the market, so it has little independent information.",
  why_it_matters="Sunk effort into a model that tracks the market is the most common failure mode in this space. The evidence says further tuning will not produce a priceable edge.",
  options=[
    ("Freeze S1 as a benchmark and stop tuning it", "The evidence in data/correlations.json", "Effort: none. Failure: none"),
    ("Add more features to the same model family", "No evidence that new score-derived features close a 0.073 correlation gap", "Effort: high. Failure: overfitting")],
  recommendation="Freeze it. Any new feature must be pre-registered as a separate strategy and scored on the forecast board first.",
  evidence=[("repo: data/correlations.json (C1 vs C2)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/correlations.json")],
  cost="none", risk="low", decided_by="owner", status="recommended"),

 dict(id="S09", group="Rewards", title="Hold betting rewards until a forward record exists; pay forecast rewards now",
  context="Gate G8 (forward replication) cannot be satisfied in a single session. The 2026 season is 9 weeks in, giving 136 settled games - far below the ~620 needed to detect a 55% edge.",
  why_it_matters="Paying for in-sample performance rewards luck and destroys the leaderboard's credibility on the first bad season.",
  options=[
    ("Hold the betting pool; award forecast points immediately", "Power analysis in data/backtest.json", "Effort: low. Failure: none"),
    ("Pay out now on backtest ROI", "0 of 5 strategies passed G3-G5", "Effort: none. Failure: rewards noise")],
  recommendation="Adopt the hold. State the rollover rule on the Leaderboard page, which it already does.",
  evidence=[("Power analysis and gates", "validation.html")],
  cost="none", risk="low", decided_by="owner", status="recommended"),

 dict(id="S10", group="Props", title="Pursue archived same-game-parlay prices as the top data purchase",
  context="The QB-over + WR1-over combo fires 27.40% of the time against 18.92% if the legs were independent - a 1.45x lift, phi = 0.346 [0.284, 0.406] on 803 team-games.",
  why_it_matters="This is the largest measured signal in the repository. It is also the one most likely to be already priced in, because books explicitly reprice correlated same-game legs. Only real SGP prices can settle that.",
  options=[
    ("Buy an SGP price archive and re-test", "The lift is measured; the price is not", "Effort: medium. Failure: cost without edge"),
    ("Assume a generic SGP multiplier", "No official or verifiable default exists", "Effort: none. Failure: a made-up price")],
  recommendation="Buy only a short trial window first. This is the one place where new spend could revealed a real edge.",
  evidence=[("repo: data/props.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/props.json"),
            ("FanDuel parlay guide (payout mechanics)", "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet")],
  cost="medium", risk="medium", decided_by="owner", status="proposed"),

 dict(id="S11", group="Parlays", title="Allow cross-game parlay multiplication; never allow naive same-player prop multiplication",
  context="Cross-game legs are independent (phi = -0.0057, CI spans 0; chi-square/df near 1). Same-game cover/over legs are near-independent (phi = 0.0077). But same-player prop legs are strongly dependent (phi = 0.346).",
  why_it_matters="Multiplying dependent prop legs produces a joint probability that is wrong by 45% - enough to turn a losing bet into an apparently winning one on paper.",
  options=[
    ("Encode the rule in the parlay builder", "Three measured dependence tests", "Effort: low. Failure: none"),
    ("Treat all legs as independent", "Fails on the prop evidence", "Effort: none. Failure: systematic mispricing")],
  recommendation="Adopt and enforce it in code, not just in prose.",
  evidence=[("repo: data/correlations.json (D1, D1b, D2)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/correlations.json"),
            ("repo: data/props.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/props.json")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S12", group="Validation", title="Cap the registered strategy family per season",
  context="Five strategies were tested and BH-FDR was applied across them. Every additional threshold tried loosens the guarantee.",
  why_it_matters="An uncapped search makes it certain that something will eventually look skilful. The cap is what makes the leaderboard meaningful.",
  options=[
    ("Cap at 8 registered strategies per season, each pre-registered in data/gates.json", "Standard practice for multiple-testing control", "Effort: low. Failure: less freedom to explore"),
    ("No cap; apply FDR after the fact", "Weaker guarantee", "Effort: none. Failure: p-hacking")],
  recommendation="Adopt the cap. Put rejections on the Flagged page rather than silently dropping them.",
  evidence=[("repo: data/gates.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S13", group="Data rights", title="Publish derived aggregates only; keep raw third-party archives out of Git if a licence requires it",
  context="Historical closing lines and 2021-2022 player data come from third-party repositories. The 2026 scores are official and reconcile exactly.",
  why_it_matters="Redistribution terms and copyright in a factual database are different questions. Publishing aggregates plus links is the lower-risk path.",
  options=[
    ("Aggregates + links, raw archive excluded by .gitignore", "Lowest legal exposure", "Effort: low. Failure: reproducibility needs a fetch step"),
    ("Commit everything", "Maximum reproducibility", "Effort: none. Failure: unresourced distribution")],
  recommendation="Adopt for new data. Do not retroactively delete existing files without the owner's agreement.",
  evidence=[("nflverse terms", "https://github.com/nflverse/nfldata")],
  cost="low", risk="medium", decided_by="owner", status="proposed"),

 dict(id="S14", group="Market access", title="Buy or license an archived odds history before any further model work",
  context="Every ROI on this site is priced at an ASSUMED -110. Gate G7 therefore fails for all five strategies and no reward can honestly be paid.",
  why_it_matters="This is the binding constraint on the entire project. Everything else is secondary to it.",
  options=[
    ("License a line-history provider", "Unblocks G7 for every future strategy", "Effort: medium. Failure: recurring cost"),
    ("Continue with assumed -110", "Nothing new can be validated", "Effort: none. Failure: the project cannot progress past Bronze")],
  recommendation="Do this first, before any additional data or model spend.",
  evidence=[("repo: data/gates.json (G7)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json")],
  cost="high", risk="medium", decided_by="owner", status="recommended"),

 dict(id="S15", group="Rewards", title="Pay rewards in reputation and compute credits, never cash tied to wagering",
  context="Reward policy is proposed but unfunded. An official helpline is cited site-wide.",
  why_it_matters="A cash prize tied to betting performance is a regulated activity in many jurisdictions. Reputation points and compute credits are not.",
  options=[
    ("Non-monetary points only", "Zero legal exposure identified", "Effort: none. Failure: weaker incentive"),
    ("Cash prizes", "Requires legal review", "Effort: high. Failure: regulatory risk")],
  recommendation="Adopt non-monetary only, as the site already states.",
  evidence=[("NCPG", "https://www.ncpgambling.org/help-treatment")],
  cost="none", risk="low", decided_by="owner", status="recommended"),

 dict(id="S16", group="Injuries and depth", title="Snapshot the official injury report weekly into dated JSON",
  context="No official archive of past practice reports exists, so injury effects can never be back-tested from history.",
  why_it_matters="Without a snapshot started now, this question stays unanswerable forever. With one, it becomes answerable next season.",
  options=[
    ("Weekly GitHub Action writes a dated snapshot", "The report is public and stable within a week", "Effort: low. Failure: same-week revisions are lost"),
    ("Rely on memory and articles", "Not reproducible", "Effort: none. Failure: no backtest, ever")],
  recommendation="Adopt now. The cost of starting late is permanent.",
  evidence=[("Official injury report", "https://www.nfl.com/injuries/")],
  cost="low", risk="low", decided_by="owner", status="recommended"),

 dict(id="S17", group="Data rights", title="Treat an official 2026 player feed as the highest-value data purchase after odds",
  context="Player data stops at 2022 in this repository, so the prop signal cannot be extended to the current season.",
  why_it_matters="Props are where the only material correlation lives. Without a current player feed, that finding cannot be cashed in.",
  options=[
    ("License a player feed", "Extends the prop study to 2026", "Effort: medium. Failure: cost"),
    ("Keep 2021-2022 only", "Honest but frozen", "Effort: none. Failure: stale")],
  recommendation="Second priority after S14.",
  evidence=[("Official player stats", "https://www.nfl.com/stats/")],
  cost="high", risk="medium", decided_by="owner", status="proposed"),

 dict(id="S18", group="Product", title="Verify the deployed URL after every merge, and record the run id",
  context="Earlier sessions recorded Pages builds that errored repeatedly for environmental reasons while the content itself was valid.",
  why_it_matters="A site that is merged but not deployed is not a deliverable. Only a fetched URL proves publication.",
  options=[
    ("Post-merge fetch of every new page plus the run id", "Already the practice in the best prior records", "Effort: low. Failure: none"),
    ("Assume the merge deployed it", "Has already failed at least once", "Effort: none. Failure: silent 404s")],
  recommendation="Adopt.",
  evidence=[("GitHub Pages docs", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages")],
  cost="none", risk="low", decided_by="owner", status="recommended"),
]

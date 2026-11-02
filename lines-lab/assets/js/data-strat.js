/* Own4 — data part 3: strategies, validation, correlation, leaderboard, flagged, sources, exec summary. */
var OWN4 = window.OWN4 = window.OWN4 || {};
OWN4.pages = Object.assign(OWN4.pages || {}, {

strategies: {
  title: "Strategy Catalog — originating your own NBA lines",
  intro: "Twelve strategy archetypes registered for the leaderboard competition. Each originates its own line (a model price) from official data, then compares it with the official sportsbook line. Per policy, NO strategy has a measured performance yet: no official line-history dataset was ingested in this session, so every performance cell is intentionally blank and flagged UNVERIFIED rather than invented. A strategy becomes leaderboard-eligible only after passing all gates G1–G8 (see Validation Gates).",
  tables: [
    {
      caption: "Registered strategies (S1–S12)",
      head: ["ID", "Strategy", "Bet format", "Signal used to originate the line", "Official data source", "Gates required", "Correlation handling", "Measured performance", "Status"],
      rows: [
        ["S1", "Rest / fatigue (back-to-back)", "Single (spread / total)", "Team playing 2nd night of a back-to-back vs rested opponent; derive expected fatigue adjustment from official schedule", {t:"official 2026-27 schedule PDF", u:OWN4.src.schedPdf}, "G1–G8", "Single leg — no correlation issue", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S2", "Home / road splits", "Single (moneyline / spread)", "Team home vs road performance from official stats splits", {t:"stats.nba.com team splits", u:OWN4.src.stats}, "G1–G8", "Single leg", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S3", "Travel & time-zone adjustment", "Single (total / team total)", "Road trip length, time-zone change, neutral-site games (Mexico City Nov 7; Austin games Oct 23 / Feb 26) from official schedule", {t:"schedule PDF arena notes", u:OWN4.src.schedPdf}, "G1–G8", "Single leg", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S4", "Injury-adjusted usage & minutes", "Single + player props", "Official daily injury report (Out/Questionable/…) shifts expected minutes/usage; recompute team and player lines", {t:"NBA injury report PDFs", u:OWN4.src.injury}, "G1–G8", "Prop combos checked against correlation matrix first", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S5", "Pace & efficiency totals", "Single (game total)", "Project possessions (pace) × efficiency (ORTG/DEFRTG, PPP) for both teams → model game total vs book total", {t:"stats.nba.com advanced", u:OWN4.src.stats}, "G1–G8", "Single leg", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S6", "Matchup-specific player props", "Player prop (PTS/REB/AST)", "Defensive matchup data (defending shots, Player PTS DIFF) vs the assigned defender", {t:"stats.nba.com matchups/defense", u:OWN4.src.glossary}, "G1–G8", "Single prop", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S7", "Own line vs market line (value / CLV)", "Single (any market)", "Originate a model price from S1–S6 inputs; bet only when model price disagrees with the official book price and beats the closing line", {t:"book lines: DK / FanDuel pages", links:[["DK",OWN4.src.dkNba],["FanDuel",OWN4.src.fdGame]]}, "G1–G8 (G7 CLV mandatory)", "Single leg", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S8", "Player prop combos (PRA, DD/TD)", "Prop combo / parlay of props", "Combine a player's PTS+REB+AST expectation; combo markets exist on official books (PRA, Double-Double, Triple-Double)", {t:"FanDuel market list", u:OWN4.src.fdGame}, "G1–G8 + correlation gate G8", "Same-player legs are correlated → measure ρ before combining; see Correlation page", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S9", "Same-game parlay (SGP) builds", "SGP", "Game-script-driven leg combos within one game (book-priced SGP)", {t:"FanDuel/DK SGP definitions", links:[["FanDuel SGP",OWN4.src.fdSgp],["DK house rules",OWN4.src.dkHouse]]}, "G1–G8 + stricter G8", "Same-game legs inherently correlated — only use book-priced SGP; never hand-build correlated standard parlays (barred by house rules)", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S10", "Cross-game parlays of uncorrelated legs", "Standard parlay", "Combine 2–4 singles from different games with measured |ρ| below threshold", {t:"parlay rules", links:[["FanDuel terms",OWN4.src.fdTerms],["DK house rules",OWN4.src.dkHouse]]}, "G1–G8 + G8", "House rules bar related outcomes in a standard parlay; legs must pass the correlation gate", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S11", "Live / in-game signals", "Live single or live SGP", "In-game line movement vs model price after lineup/injury news during the game", {t:"live markets on DK page", u:OWN4.src.dkNba}, "G1–G8", "As above by format", {t:"", flag:"UNVERIFIED"}, "Registered"],
        ["S12", "Season-level & futures", "Futures / season props", "Standings trajectory, roster construction, official schedule strength", {t:"nba.com/standings + DK futures", links:[["standings",OWN4.src.standings],["DK NBA",OWN4.src.dkNba]]}, "G1–G8", "Single leg", {t:"", flag:"UNVERIFIED"}, "Registered"]
      ]
    },
    {
      caption: "Bet-format guide (what the competition covers)",
      head: ["Format", "Definition (official)", "Competition rule", "Source"],
      rows: [
        ["Single bet", "One selection: moneyline, spread, total, or player prop", "Must originate its own line from official data and pass G1–G8", {t:"DK NBA page", u:OWN4.src.dkNba}],
        ["Parlay", "Two or more wagers linked; all must win; odds multiply", "Cross-game only; correlated outcomes are barred from standard parlays by house rules", {t:"FanDuel terms + DK house rules", links:[["FanDuel",OWN4.src.fdTerms],["DK rules",OWN4.src.dkHouse]]}],
        ["Player prop combos", "Player stat props and combos (PRA, DD, TD, quarter/half props)", "Same-player combos must pass correlation gate G8", {t:"FanDuel game page markets", u:OWN4.src.fdGame}],
        ["Same-game parlay", "2+ selections from a single game (or correlated events), book-priced", "Allowed only as book-priced SGP/SGP+; stricter correlation gate", {t:"FanDuel SGP help", u:OWN4.src.fdSgp}]
      ]
    }
  ]
},

validation: {
  title: "Validation Gates — removing luck before a strategy can compete",
  intro: "Every strategy must pass all eight gates before it is leaderboard-eligible. Gates G1 and G8 have official external anchors (official data sources; sportsbook correlation rules). The numeric thresholds in G2–G7 are project-defined rules of this competition — they are NOT claims about the world, so their source cell is intentionally blank and flagged (F3).",
  tables: [
    {
      caption: "Gates G1–G8",
      head: ["Gate", "Requirement", "How it removes luck", "Source"],
      rows: [
        ["G1 — Data provenance", "Every input comes from an official source: nba.com, stats.nba.com, official schedule/injury PDFs, licensed sportsbook pages, or the NBA's authorized betting-data distributors (Sportradar/Genius)", "No unverifiable or scraped data enters a model", {t:"official platforms", links:[["stats.nba.com",OWN4.src.stats],["injury reports",OWN4.src.injury],["Sportradar",OWN4.src.sr2021]]}],
        ["G2 — Minimum sample", "≥30 settled bets to register a result; ≥100 for leaderboard eligibility", "Small samples are dominated by variance", {t:"", flag:"UNVERIFIED — project-defined threshold (F3)"}],
        ["G3 — Walk-forward backtest", "Model is fit only on data strictly before each test game (rolling origin); no look-ahead", "Prevents using the future to 'predict' the past", {t:"", flag:"UNVERIFIED — project-defined method (F3)"}],
        ["G4 — Held-out sample", "Final 20% of the evaluation window is never used for fitting or threshold tuning; reported separately", "Detects overfitting", {t:"", flag:"UNVERIFIED — project-defined method (F3)"}],
        ["G5 — Statistical significance", "Two-sided binomial test on win rate vs the break-even rate at the odds paid; require p < 0.05. Break-even at -110 = 110/210 ≈ 52.38% (derived arithmetic from the official odds explanation)", "A 'winning' record can happen by chance; this gate prices in that chance", {t:"odds math anchored to DK page", links:[["DK odds explanation",OWN4.src.dkNba]], flag:"test method project-defined (F3); odds format official"}],
        ["G6 — Risk limits", "Max drawdown cap and fractional Kelly sizing (≤ 0.25 Kelly) enforced in the staking plan", "Caps the damage of inevitable losing streaks", {t:"", flag:"UNVERIFIED — project-defined threshold (F3)"}],
        ["G7 — Closing-line value (CLV)", "Strategy's average entry price must beat the closing price (positive CLV) over the full sample — the standard skill proxy in line-shopping", "Beating the close cannot be explained by luck over large samples", {t:"", flag:"UNVERIFIED — concept/ thresholds project-defined (F3); lines sourced officially"}],
        ["G8 — Correlation gate", "Parlay/prop-combo legs: measured correlation must be below the project threshold, OR the combo must be placed as a book-priced SGP. Standard parlays may never contain related outcomes (official house rule)", "Prevents disguising one bet as many (correlation inflates apparent hit rates)", {t:"DK house rules (official) + FanDuel SGP def", links:[["DK house rules",OWN4.src.dkHouse],["FanDuel SGP",OWN4.src.fdSgp]], flag:"measured ρ values pending — F1"}]
      ]
    },
    {
      caption: "Luck-removal methods applied across all strategies",
      head: ["Method", "What it does", "Status"],
      rows: [
        ["Walk-forward validation (G3)", "Rolling-origin refit; only past data informs each bet", "Defined — pending data (F1/F2)"],
        ["Held-out holdout (G4)", "Untouched final 20% of sample", "Defined — pending data (F1/F2)"],
        ["Binomial significance test (G5)", "Win rate must clear break-even beyond chance (p<0.05)", "Defined — pending data (F1/F2)"],
        ["Variance / regression-to-mean check", "Compare first-half vs second-half strategy performance; shrink toward the mean if they diverge", "Defined — pending data (F1/F2)"],
        ["CLV tracking (G7)", "Record entry vs closing line on every bet from official book pages", "Defined — pending official line history (F1)"],
        ["Correlation measurement (G8)", "Compute ρ for every leg pair used; block high-ρ combos in standard parlays", "Method defined on Correlation page; values pending (F1)"]
      ]
    }
  ]
},

correlation: {
  title: "Correlation Analysis — methodology + measurement matrix",
  intro: "Correlation between bet legs is what turns a parlay into a disguised single bet. Official sportsbook rules already bar related outcomes from standard parlays and define SGPs for same-game combos. Measured correlation values are NOT yet computed: this session had no official line-history dataset, so every measured cell is blank and flagged UNVERIFIED (F1) rather than estimated. Method: Pearson r on game-level binary outcomes (leg hit = 1/0), Spearman ρ for ranked props; computed from official game results (stats.nba.com) and official line history (Sportradar).",
  tables: [
    {
      caption: "Measurement matrix (values pending — left blank per no-inference policy)",
      head: ["Leg A", "Leg B", "Same game?", "Direction expected", "Measured ρ (Pearson)", "n (games)", "Data source", "Status"],
      rows: [
        ["Game total Over/Under", "Team total Over/Under (same team)", "Yes", "Positive", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com results + Sportradar lines", links:[["stats",OWN4.src.stats],["Sportradar",OWN4.src.sr2021]]}, "Pending"],
        ["Spread cover", "Moneyline win (same team)", "Yes", "Positive", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com + book pages", links:[["stats",OWN4.src.stats],["DK",OWN4.src.dkNba]]}, "Pending"],
        ["Player PTS over", "Game total over (same game)", "Yes", "Positive", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com + book pages", links:[["stats",OWN4.src.stats],["FanDuel",OWN4.src.fdGame]]}, "Pending"],
        ["Player PTS over", "Same team's team total over", "Yes", "Positive", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com", u:OWN4.src.stats}, "Pending"],
        ["Player A PTS over", "Player B PTS over (same team)", "Yes", "Positive (game script)", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com", u:OWN4.src.stats}, "Pending"],
        ["Player PTS over", "Player REB over (same player)", "Yes", "Mixed", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com", u:OWN4.src.stats}, "Pending"],
        ["Legs from different games", "Legs from different games", "No", "~0 (must verify)", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"stats.nba.com + book pages", links:[["stats",OWN4.src.stats],["DK",OWN4.src.dkNba]]}, "Pending — required for S10"],
        ["Any two SGP legs", "Same game", "Yes", "Priced by book", "n/a — SGP pricing is the book's correlation adjustment", "n/a", {t:"FanDuel/DK SGP rules", links:[["FanDuel SGP",OWN4.src.fdSgp],["DK house rules",OWN4.src.dkHouse]]}, "Book-priced"]
      ]
    },
    {
      caption: "Official rules that govern correlation in betting",
      head: ["Rule", "Official text / effect", "Source"],
      rows: [
        ["Standard parlays may not contain related outcomes", "“A bet made as a parlay, except made as a Same Game Parlay, shall never include two or more offers where the outcomes of which might turn out to be related.”", {t:"DK house rules PDF", u:OWN4.src.dkHouse}],
        ["SGP definition", "“Combines two or more selections from a single game or correlated games, matches, or events” — correlation is inside the product by design", {t:"FanDuel SGP help", u:OWN4.src.fdSgp}],
        ["Project thresholds for G8 (project-defined)", "|ρ| ≥ 0.7 strong, 0.3–0.7 moderate, < 0.3 weak; cross-game parlay legs must measure weak; same-game combos only via book-priced SGP", {t:"", flag:"UNVERIFIED — project-defined thresholds (F3)"}]
      ]
    }
  ]
},

leaderboard: {
  title: "Leaderboard — competition design & current standings",
  intro: "The competition ranks strategies by skill, not by a lucky small sample. Rewards are recognition tiers on this site (featured placement + tier badge); this repo cannot disburse money, so reward structure is project-defined and flagged (F4). Standings below show all metrics blank/UNVERIFIED because no validated backtest exists yet (F1/F2) — the leaderboard starts empty by design.",
  tables: [
    {
      caption: "Scoring metrics (recorded for every strategy)",
      head: ["Metric", "Definition", "Official data source", "Threshold status"],
      rows: [
        ["Bets placed (n)", "Settled bets in the evaluation window", {t:"book pages / own log", links:[["DK",OWN4.src.dkNba],["FanDuel",OWN4.src.fdGame]]}, "G2: ≥100 for eligibility"],
        ["Win rate", "Winning bets ÷ settled bets (pushes excluded)", "same", "G5: must beat break-even at p<0.05"],
        ["ROI", "Net profit ÷ total staked", "same", "Reported; not sufficient alone"],
        ["CLV", "Average (closing price − entry price) in implied-probability terms", {t:"official line history via Sportradar", u:OWN4.src.sr2021}, "G7: must be positive"],
        ["Sharpe ratio", "Mean bet return ÷ std of bet returns (per bet, risk-free ≈ 0)", "own log", "Reported"],
        ["Max drawdown", "Worst peak-to-trough of cumulative profit", "own log", "G6: within cap"],
        ["Gates passed", "Count of G1–G8 passed", "this site", "All 8 required to rank"]
      ]
    },
    {
      caption: "Reward tiers (project-defined, non-monetary — flag F4)",
      head: ["Tier", "Requirement", "Reward"],
      rows: [
        ["Gold", "All gates passed + top composite score (ROI, CLV, Sharpe weighted) over ≥100 bets", "Featured on Dashboard + Gold badge on site"],
        ["Silver", "All gates passed, composite score 2nd", "Silver badge + strategies page feature"],
        ["Bronze", "All gates passed, composite score 3rd", "Bronze badge"],
        ["Registered", "Strategy registered, gates pending", "Listed in catalog only"]
      ]
    },
    {
      caption: "Current standings (as of 2026-11-02 — empty by design)",
      head: ["Rank", "Strategy", "n", "Win rate", "ROI", "CLV", "Sharpe", "Max DD", "Gates", "Tier"],
      rows: [
        ["—", "S1 Rest/fatigue", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S2 Home/road splits", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S3 Travel/time zone", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S4 Injury-adjusted usage", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S5 Pace & efficiency totals", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S6 Matchup player props", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S7 Own line vs market (CLV)", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S8 Player prop combos (PRA/DD/TD)", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S9 SGP builds", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S10 Cross-game parlays", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S11 Live signals", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"],
        ["—", "S12 Futures / season-level", {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, {t:"", flag:"UNVERIFIED"}, "0/8", "Registered"]
      ]
    }
  ]
},

flagged: {
  title: "Flagged for Review — unverified values & irregularities",
  intro: "Everything here is either (a) a value that could not be confirmed from an official source — left blank, never inferred — or (b) an irregularity spotted on an official page. None of these block the site; review and request changes after the site is live.",
  tables: [
    {
      caption: "Flagged items F1–F12",
      head: ["ID", "Item", "Why flagged", "Source / link", "Status"],
      rows: [
        ["F1", "All measured correlation values (ρ) in the Correlation matrix", "No official line-history dataset was ingested this session; values left blank rather than estimated", {t:"method + official data channels", links:[["stats.nba.com",OWN4.src.stats],["Sportradar (official betting data)",OWN4.src.sr2021]]}, "Open"],
        ["F2", "All strategy performance metrics (n, win rate, ROI, CLV, Sharpe, max DD) on Leaderboard", "No validated walk-forward backtest run yet; cells blank by no-inference policy", {t:"pages/leaderboard.html", u:"pages/leaderboard.html"}, "Open"],
        ["F3", "Numeric thresholds in gates G2–G7 and correlation bands (≥0.7 / 0.3–0.7 / <0.3)", "Project-defined competition rules, not externally verifiable facts; source cells intentionally blank", {t:"pages/validation.html + pages/correlation.html", u:"pages/validation.html"}, "Open — confirm thresholds"],
        ["F4", "Leaderboard reward tiers (Gold/Silver/Bronze, site recognition only)", "Project-defined; this repo cannot disburse monetary rewards", {t:"pages/leaderboard.html", u:"pages/leaderboard.html"}, "Open — confirm rewards"],
        ["F5", "nba.com/news/key-dates lists “April 17: NBA Playoffs 2026 begin” inside the 2026-27 season key-dates list", "Label appears to be a typo on the official page (2026-27 playoffs begin Apr 17, 2027); flagged, not corrected, here", {t:"nba.com key dates", u:OWN4.src.keyDates}, "Open — official-page irregularity"],
        ["F6", "Phoenix Suns arena name: nbatickets.nba.com lists “PHX Arena”; nba.com arena articles list “Footprint Center”", "Two official pages disagree; team table shows the tickets-site value and flags it", {t:"nbatickets vs nba.com arenas article", links:[["nbatickets.nba.com",OWN4.src.tickets],["nba.com arenas (es)", "https://www.nba.com/news/estadios-arenas-nba"]]}, "Open — official-page discrepancy"],
        ["F7", "gleague.nba.com/key-dates lists “November 7: NBA Mexico City Game 2025” in the 2026-27 calendar section", "Official schedule PDF notes the game on Sat 11/7/2026 at Arena CDMX; the '2025' label looks stale", {t:"gleague key dates + schedule PDF", links:[["gleague.nba.com",OWN4.src.gKey],["schedule PDF",OWN4.src.schedPdf]]}, "Open — official-page irregularity"],
        ["F8", "Report that the NBA barred certain prop markets (first basket, opening tip, low-minute unders, multi-under parlay legs) from sportsbooks in Oct 2026", "Only a press report (Boston Globe) was found; no official league publication located — treated as press, not fact", {t:"bostonglobe.com 2026-10-16", u:OWN4.src.globe}, "Open — press source only"],
        ["F9", "DraftKings house rules PDF is hosted on massgaming.com (Massachusetts Gaming Commission), not on DraftKings' own domain", "Content is the official sportsbook rules as filed with the regulator; host is third-party — noted for transparency", {t:"massgaming.com PDF", u:OWN4.src.dkHouse}, "Noted"],
        ["F10", "“1,230 total regular-season games” on the Dashboard", "Derived arithmetic (30 × 82 ÷ 2) from two official facts, not a directly published figure", {t:"derived from About + Cup 101", links:[["About",OWN4.src.about],["Cup 101",OWN4.src.cup101]]}, "Derived — labeled as such"],
        ["F11", "Live team records shown as examples (e.g., NYK 2-4, 10th in East)", "Point-in-time snapshot from the team page on 2026-11-02; changes daily", {t:"nba.com/team/1610612752/knicks", u:OWN4.src.knicks}, "Snapshot"],
        ["F12", "Stats glossary coverage", "Only glossary entries directly displayed on 2026-11-02 are quoted; definitions for stats not displayed were NOT inferred", {t:"stats.nba.com/help/glossary/", u:OWN4.src.glossary}, "Policy note"]
      ]
    }
  ]
},

sources: {
  title: "Source Register — every official source used",
  intro: "All sources accessed and verified on 2026-11-02. League facts: nba.com / official.nba.com / cdn.nba.com / stats.nba.com / pr.nba.com / gleague.nba.com / nbatickets.nba.com. Lines & rules: official licensed sportsbooks (DraftKings, FanDuel) and the NBA's official betting-data distributors (Sportradar, Genius Sports). Responsible gambling: NCPG.",
  tables: [
    {
      caption: "Register",
      head: ["#", "Source", "URL", "Used to verify"],
      rows: [
        ["1", "NBA.com — About the NBA", "https://www.nba.com/news/about", "30 teams, divisions, 82 games, play-in format, 12-min quarters, 5-min OT, 24-s shot clock, court 94×50, rim 10 ft, FT 15 ft, 3-pt 23'9\"/22', roster 15/12, titles BOS 18 / LAL 17, founded 1946"],
        ["2", "Official 2025-26 NBA Playing Rules (PDF, cdn.nba.com)", "https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf", "Rule 6 timing (12-min periods, 5-min OT, 15-min halftime, timeout rules), Rule 7 shot clock 24 s"],
        ["3", "official.nba.com — Rule No. 1 (court & equipment)", "https://official.nba.com/rule-no-1-court-dimensions-equipment/", "Official rules index linked from nba.com About"],
        ["4", "official.nba.com — Replay Center", "https://official.nba.com/replay/", "Replay Center, Secaucus NJ, since 2014-15"],
        ["5", "NBA.com — All Teams", "https://www.nba.com/teams", "All 30 team names, official team-site URLs, team IDs"],
        ["6", "NBA.com — FAQ", "https://www.nba.com/news/faq", "Playoffs: top 8 per conference, best-of-seven 2-2-1-1-1, NBA Finals best-of-seven"],
        ["7", "NBA.com — 2026 SoFi Play-In Tournament", "https://www.nba.com/news/nba-play-in-tournament", "Play-In mechanics (7v8, 9v10), 2026 dates, top-6 auto-qualify"],
        ["8", "NBA.com — Playoff picture (team page)", "https://www.nba.com/pacers/playoff-picture", "Play-In game structure detail"],
        ["9", "NBA.com — Emirates NBA Cup 101", "https://www.nba.com/news/nba-cup-101", "Cup 2026: groups of 5, 4 group games, Oct 30–Nov 27, 67 games count except Championship, 82-game season, Dec 11 championship at Hinkle Fieldhouse"],
        ["10", "NBA.com — Emirates NBA Cup FAQ", "https://www.nba.com/news/nba-cup-frequently-asked-questions", "8 teams advance (6 group winners + 2 wild cards), venues, standings impact"],
        ["11", "NBA.com — 2026-27 schedule release", "https://www.nba.com/news/2026-27-nba-regular-season-schedule", "Schedule released Aug 13, 2026; 80 of 82 games fixed; 2 TBD Dec 4–10 by Cup results"],
        ["12", "NBA.com — 2026-27 schedule announced (Cup group play)", "https://www.nba.com/news/2026-27-schedule-announced", "60 Group Play games Oct 30–Nov 27"],
        ["13", "cdn.nba.com — 2026-27 schedule by team (PDF)", "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Team.pdf", "Per-team schedules; arena notes (Moody Center Austin 10/23 & 2/26; Arena CDMX 11/7)"],
        ["14", "NBA.com — Key dates 2026-27", "https://www.nba.com/news/key-dates", "Apr 11, 2027 season end; Apr 12 rosters; Apr 13–16 Play-In; Apr 17 playoffs begin (label flagged F5)"],
        ["15", "G League — key dates (official NBA page listing NBA dates)", "https://gleague.nba.com/key-dates", "Preseason Oct 3–16, rosters Oct 19, Oct 20 start, Jan 5/10 contract dates, Feb 19–21 2027 All-Star Phoenix (label flagged F7)"],
        ["16", "NBA.com — 2026-27 calendar (fantasy dates article)", "https://www.nba.com/news/fantasy-basketball-every-important-date-on-the-2026-27-nba-calendar", "Sep 29 camps, Oct 3 preseason, Oct 19 rosters, Oct 20 opening night, Cup dates Dec 4–11 (Dec 11 Indianapolis), Jan 5 / Jan 10, Feb 11 trade deadline"],
        ["17", "NBA.com — Rosters set for 2026-27 regular season", "https://www.nba.com/news/nba-rosters-set-for-2026-27-regular-season", "Oct 20, 2026 opening tripleheader: BOS@DET 3 ET, NYK v PHI 7 ET, OKC@SAS 9:30 ET"],
        ["18", "NBA.com — Season opener article", "https://www.nba.com/news/nba-schedule-season-opener-2026-27", "Opening night matchups & times, NBC/Peacock"],
        ["19", "stats.nba.com — Stat glossary", "https://stats.nba.com/help/glossary/", "Official definitions: PTS, REB, OREB, AST, %AST, %PTS, AST/TO, DEFRTG, PITP, PPP, FP, AST ADJ, AST PTS Created, Player PTS DIFF"],
        ["20", "stats.nba.com — Statistical minimums", "https://stats.nba.com/help/statminimums", "Leader minimums: 58 games (70% of 82), 300 FGM, 125 FTM, 82 3PM, 200 AST, 82 STL + career minimums"],
        ["21", "stats.nba.com — main stats site", "https://stats.nba.com/", "Leaders, all-time leaders, team/player stats platform"],
        ["22", "NBA.com — standings / games / players", "https://www.nba.com/standings ; https://www.nba.com/games ; https://www.nba.com/players", "Official standings, scores, player index"],
        ["23", "NBA.com — team profile example (Knicks)", "https://www.nba.com/team/1610612752/knicks", "Live team page format: record, PPG/RPG/APG/OPPG, roster, upcoming games (snapshot F11)"],
        ["24", "nbatickets.nba.com — official tickets", "https://nbatickets.nba.com/tickets/", "Arena name for each of the 30 teams (Phoenix flagged F6)"],
        ["25", "NBA official injury report PDFs (ak-static.cms.nba.com)", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-28_04_00PM.pdf", "Daily per-game player status (Out/Questionable/Probable/Doubtful/Available) with reasons"],
        ["26", "DraftKings Sportsbook — NBA odds page", "https://sportsbook.draftkings.com/leagues/basketball/nba", "Official published NBA lines; bet types (moneyline/spread/total/props/parlay/futures/live); American odds explanation (+150/-200)"],
        ["27", "FanDuel Sportsbook — NBA game page (BKN@NYK, Nov 2, 2026)", "https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174", "Game lines (spread +14.5, total 221.5, ML +610/-900), player prop & combo markets (PRA, DD, TD, 1Q props), SGP"],
        ["28", "DraftKings support — box score glossary", "https://support.draftkings.com/dk/en/glossary-of-box-score-terms?id=kb_article_view&sysparm_article=KB0011397", "NBA box-score abbreviations (MIN/PTS/REB/AST/FG/3PT/FT/BLK/STL/TO/PF)"],
        ["29", "DraftKings support — Early Exit Protected", "https://support.draftkings.com/dk/en-us/early-exit-program-early-exit-protected?id=kb_article_view&sysparm_article=KB0012036", "NBA player-prop void rules on first-half injury exits; parlay repricing"],
        ["30", "DraftKings house rules (filed with MA Gaming Commission)", "https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf", "Parlay/SGP definitions, odds multiplication, push handling, correlated-outcome prohibition in standard parlays, settlement on official league stats (flag F9)"],
        ["31", "FanDuel support — betting terms / SGP / push / round robin / teaser", "https://support.fanduel.com/s/article/Sports-Betting-Terms ; /What-is-a-Same-Game-Parlay-or-SGP ; /What-happens-if-my-FanDuel-parlay-is-a-push ; /What-is-a-Round-Robin ; /Teasers-with-FanDuel", "Official parlay/SGP/SGP+/round-robin/teaser/push definitions"],
        ["32", "NBA Communications (pr.nba.com) — betting data partnerships", "https://pr.nba.com/nba-betting-data-partnerships-sportradar-genius/ ; https://pr.nba.com/nba-announces-multiyear-partnership-sportradar-second-spectrum/", "Sportradar & Genius Sports distribute official NBA betting data in the U.S.; Sportradar integrity services since 2016"],
        ["33", "Sportradar IR — NBA global partnership (2021)", "https://investors.sportradar.com/news-releases/news-release-details/nba-and-sportradar-announce-landmark-long-term-global", "Sportradar exclusive worldwide provider of NBA data; authorized global distributor of official NBA betting data; UFDS fraud detection"],
        ["34", "NCPG — National Problem Gambling Helpline", "https://www.ncpgambling.org/help-treatment/about-the-national-problem-gambling-helpline", "1-800-GAMBLER (1-800-426-2537), 24/7 call/text/chat"],
        ["35", "Boston Globe (press report — flagged F8, not official)", "https://www.bostonglobe.com/2026/10/16/sports/nba-gambling-limitations/", "Press report of NBA prop-market restrictions told to sportsbooks Oct 16, 2026"]
      ]
    }
  ]
},

exec: {
  title: "Executive Summary",
  intro: "Full narrative in docs/executive-summary.md. Key points below; every factual claim links to its official source.",
  tables: [
    {
      caption: "Summary",
      head: ["Topic", "Summary", "Source"],
      rows: [
        ["Goal", "Originate our own NBA lines and run a leaderboard competition of strategies (singles, parlays, player-prop combos) that are selectively skill-based — luck removed via validation gates G1–G8", {t:"docs/executive-summary.md", u:"docs/executive-summary.md"}],
        ["Verified league baseline", "30 teams, 2 conferences × 3 divisions, 82 games/team, 1,230 RS games (derived), 4×12-min quarters, 5-min OT, 24-s shot clock, play-in for seeds 7–10, best-of-seven playoffs", {t:"nba.com About + rules PDF", links:[["About",OWN4.src.about],["Rules PDF",OWN4.src.rulesPdf]]}],
        ["Current season", "2026-27 tipped off Oct 20, 2026; ends Apr 11, 2027; Play-In Apr 13–16, 2027; Emirates NBA Cup Oct 30–Dec 11, 2026", {t:"nba.com news/key dates", links:[["opener",OWN4.src.opener],["key dates",OWN4.src.keyDates],["Cup 101",OWN4.src.cup101]]}],
        ["Official data for signals", "stats.nba.com (all stats), nba.com standings/games/team pages, daily official injury report PDFs, official 2026-27 schedule PDF", {t:"see Source Register", u:"pages/sources.html"}],
        ["Official lines", "Licensed sportsbooks (DraftKings, FanDuel pages) + NBA's authorized betting-data distributors (Sportradar exclusive worldwide, Genius U.S.)", {t:"DK/FanDuel/Sportradar", links:[["DK",OWN4.src.dkNba],["FanDuel",OWN4.src.fdGame],["Sportradar",OWN4.src.sr2021]]}],
        ["Market rules that matter", "Parlay = all legs win, odds multiply; standard parlays may NOT contain correlated outcomes; SGPs are book-priced same-game combos; NBA bets settle on official league stats", {t:"DK house rules + FanDuel terms", links:[["DK rules",OWN4.src.dkHouse],["FanDuel terms",OWN4.src.fdTerms]]}],
        ["Strategy framework", "12 registered archetypes (S1–S12) across singles, parlays, prop combos, SGP; each originates a model line from official data and must pass G1–G8 (provenance, sample size, walk-forward, holdout, significance, risk, CLV, correlation)", {t:"pages/strategies.html + validation", u:"pages/validation.html"}],
        ["Correlation", "Method defined (Pearson/Spearman on official results + official line history); measured values intentionally blank — UNVERIFIED (F1)", {t:"pages/correlation.html", u:"pages/correlation.html"}],
        ["Leaderboard", "Metrics: n, win rate, ROI, CLV, Sharpe, max drawdown, gates passed; tiers Gold/Silver/Bronze (recognition only, F4); standings currently empty by design (F2)", {t:"pages/leaderboard.html", u:"pages/leaderboard.html"}],
        ["Flagged for review", "12 items (F1–F12): unmeasured values, project-defined thresholds, and official-page irregularities (key-dates label F5, PHX arena naming F6, Mexico City year label F7, press-only prop-restriction report F8)", {t:"pages/flagged.html", u:"pages/flagged.html"}],
        ["Next steps (no manual input needed)", "Ingest official line history via Sportradar official data → run walk-forward backtests per strategy → compute ρ matrix → populate leaderboard only for strategies passing all gates", {t:"strategy framework", u:"pages/strategies.html"}]
      ]
    }
  ]
}
});

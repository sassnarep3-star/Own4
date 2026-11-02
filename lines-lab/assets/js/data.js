/* Own4 — NBA Lines Lab — data part 1: core, dashboard, league, season, teams.
 * Every factual row carries a source URL to an official site (accessed 2026-11-02).
 * Cells that cannot be confirmed from an official source are left blank and flagged UNVERIFIED.
 * Cell format: "text" | {t, u} link | {t, flag:"UNVERIFIED"} | {t, links:[[label,url],...]} | {t, badge:"VERIFIED"}
 */
var OWN4 = window.OWN4 = window.OWN4 || {};

/* ------------------------------- sources ------------------------------- */
OWN4.src = {
  about:   "https://www.nba.com/news/about",
  rulesPdf:"https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf",
  rule1:   "https://official.nba.com/rule-no-1-court-dimensions-equipment/",
  replay:  "https://official.nba.com/replay/",
  teams:   "https://www.nba.com/teams",
  faq:     "https://www.nba.com/news/faq",
  playin:  "https://www.nba.com/news/nba-play-in-tournament",
  cup101:  "https://www.nba.com/news/nba-cup-101",
  cupFaq:  "https://www.nba.com/news/nba-cup-frequently-asked-questions",
  sched:   "https://www.nba.com/news/2026-27-nba-regular-season-schedule",
  schedB:  "https://www.nba.com/news/2026-27-schedule-announced",
  schedPdf:"https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Team.pdf",
  keyDates:"https://www.nba.com/news/key-dates",
  gKey:    "https://gleague.nba.com/key-dates",
  cal:     "https://www.nba.com/news/fantasy-basketball-every-important-date-on-the-2026-27-nba-calendar",
  rosters: "https://www.nba.com/news/nba-rosters-set-for-2026-27-regular-season",
  opener:  "https://www.nba.com/news/nba-schedule-season-opener-2026-27",
  glossary:"https://stats.nba.com/help/glossary/",
  minimums:"https://stats.nba.com/help/statminimums",
  stats:   "https://stats.nba.com/",
  standings:"https://www.nba.com/standings",
  games:   "https://www.nba.com/games",
  players: "https://www.nba.com/players",
  tickets: "https://nbatickets.nba.com/tickets/",
  injury:  "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-28_04_00PM.pdf",
  dkNba:   "https://sportsbook.draftkings.com/leagues/basketball/nba",
  dkGloss: "https://support.draftkings.com/dk/en/glossary-of-box-score-terms?id=kb_article_view&sysparm_article=KB0011397",
  dkEarly: "https://support.draftkings.com/dk/en-us/early-exit-program-early-exit-protected?id=kb_article_view&sysparm_article=KB0012036",
  dkHouse: "https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.1.24.pdf",
  fdTerms: "https://support.fanduel.com/s/article/Sports-Betting-Terms",
  fdPush:  "https://support.fanduel.com/s/article/What-happens-if-my-FanDuel-parlay-is-a-push",
  fdSgp:   "https://support.fanduel.com/s/article/What-is-a-Same-Game-Parlay-or-SGP",
  fdRr:    "https://support.fanduel.com/s/article/What-is-a-Round-Robin",
  fdTeaser:"https://support.fanduel.com/s/article/Teasers-with-FanDuel",
  fdGame:  "https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-new-york-knicks-36262174",
  prData:  "https://pr.nba.com/nba-betting-data-partnerships-sportradar-genius/",
  prData16:"https://pr.nba.com/nba-announces-multiyear-partnership-sportradar-second-spectrum/",
  sr2021:  "https://investors.sportradar.com/news-releases/news-release-details/nba-and-sportradar-announce-landmark-long-term-global",
  ncpg:    "https://www.ncpgambling.org/help-treatment/about-the-national-problem-gambling-helpline",
  globe:   "https://www.bostonglobe.com/2026/10/16/sports/nba-gambling-limitations/",
  knicks:  "https://www.nba.com/team/1610612752/knicks",
  champs:  "https://www.nba.com/news/most-championships-nba-history"
};

/* --------------------------------- nav --------------------------------- */
OWN4.nav = [
  { id: "home",       label: "Dashboard",            href: "index.html"                    },
  { id: "exec",       label: "Executive Summary",    href: "pages/executive-summary.html"  },
  { id: "league",     label: "League & Rules",       href: "pages/league.html"             },
  { id: "season",     label: "2026-27 Season",       href: "pages/season.html"             },
  { id: "teams",      label: "Teams & Arenas",       href: "pages/teams.html"              },
  { id: "stats",      label: "Official Stats",       href: "pages/stats.html"              },
  { id: "markets",    label: "Lines & Bet Markets",  href: "pages/markets.html"            },
  { id: "strategies", label: "Strategy Catalog",     href: "pages/strategies.html"         },
  { id: "validation", label: "Validation Gates",     href: "pages/validation.html"         },
  { id: "correlation",label: "Correlation Analysis", href: "pages/correlation.html"        },
  { id: "leaderboard",label: "Leaderboard",          href: "pages/leaderboard.html"        },
  { id: "flagged",    label: "Flagged for Review",   href: "pages/flagged.html"            },
  { id: "sources",    label: "Source Register",      href: "pages/sources.html"            }
];

OWN4.meta = {
  title: "Own4 — NBA Lines Lab",
  tagline: "Originate your own NBA lines. Skill-based strategies only — every value verified against an official source or flagged UNVERIFIED.",
  built: "2026-11-02",
  branch: "arena/42d467e4-own4",
  footer: "All facts on this site were verified against official sources on 2026-11-02 unless a row is flagged UNVERIFIED (blank value, no inference). Sources: NBA.com, official.nba.com, stats.nba.com, cdn.nba.com, pr.nba.com, official licensed sportsbooks and the NBA's official betting-data distributors."
};

OWN4.pages = Object.assign(OWN4.pages || {}, {

/* -------------------------------- home --------------------------------- */
home: {
  title: "NBA Lines Lab — Dashboard",
  intro: "A self-verifying workspace for originating NBA betting lines and building strategies that are selectively skill-based. Single bets, parlays and player-prop combos are all registered here; every strategy must pass the validation gates before it can appear on the leaderboard. Luck is removed by design: walk-forward testing, held-out samples, significance tests, correlation gates and closing-line-value checks. Nothing on this site is inferred — unverifiable values are left blank and flagged.",
  cards: [
    { value: "30", label: "NBA teams", note: {t:"2 conferences × 3 divisions", u:"https://www.nba.com/news/about"} },
    { value: "82", label: "Games per team / season", note: {t:"2026-27 regular season", u:"https://www.nba.com/news/nba-cup-101"} },
    { value: "1,230", label: "Total RS games (derived)", note: {t:"30 × 82 ÷ 2 — derived from official facts", u:"https://www.nba.com/news/about"}, flag: "DERIVED" },
    { value: "48 min", label: "Regulation game clock", note: {t:"4 × 12-minute quarters; OT 5 min", u:"https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf"} },
    { value: "24 s", label: "Shot clock", note: {t:"NBA Rule No. 7", u:"https://cdn.nba.com/manage/2026/01/Official-2025-26-NBA-Playing-Rules.pdf"} },
    { value: "12", label: "Strategy archetypes registered", note: {t:"Singles, parlays, prop combos, SGP", u:"pages/strategies.html"} },
    { value: "8", label: "Validation gates", note: {t:"G1–G8, all must pass", u:"pages/validation.html"} },
    { value: "12", label: "Items flagged for review", note: {t:"Unverified values + official-page irregularities", u:"pages/flagged.html"}, flag: "FLAGGED" }
  ],
  tables: [
    {
      caption: "Recently verified — key league facts (full tables on subpages)",
      head: ["Fact", "Value", "Official source"],
      rows: [
        ["League", "National Basketball Association — 30 teams across North America", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Regular season", "82 games per team (2025-26 and 2026-27 seasons)", {t:"nba.com About + Emirates NBA Cup 101", links:[["About",OWN4.src.about],["Cup 101",OWN4.src.cup101]]}],
        ["Playoff format", "Top 6 per conference automatic; seeds 7–10 play in the Play-In Tournament; then best-of-seven series (2-2-1-1-1)", {t:"nba.com About / FAQ / Play-In article", links:[["About",OWN4.src.about],["FAQ",OWN4.src.faq],["Play-In",OWN4.src.playin]]}],
        ["2026-27 opening night", "Tuesday, Oct 20, 2026 — Celtics@Pistons (3 ET), 76ers@Knicks (7 ET), Thunder@Spurs (9:30 ET), NBC/Peacock", {t:"nba.com news", links:[["Rosters set",OWN4.src.rosters],["Season opener",OWN4.src.opener]]}],
        ["2026-27 season end", "April 11, 2027; Play-In April 13–16, 2027; Playoffs begin April 17", {t:"nba.com key dates", u:OWN4.src.keyDates, flag:"see flag F5"}],
        ["Official betting data", "Sportradar = exclusive worldwide provider of NBA data and authorized global distributor of official NBA betting data; Genius Sports also distributes official NBA betting data in the U.S.; Sportradar UFDS monitors betting integrity", {t:"NBA Communications / Sportradar", links:[["pr.nba.com 2018",OWN4.src.prData],["pr.nba.com 2016",OWN4.src.prData16],["Sportradar 2021",OWN4.src.sr2021]]}],
        ["Where lines are published", "Licensed sportsbook pages, e.g. DraftKings NBA and FanDuel NBA game pages (spreads, totals, moneylines, player props, parlays, SGP, live)", {t:"Official sportsbooks", links:[["DraftKings NBA",OWN4.src.dkNba],["FanDuel game page (Nov 2, 2026)",OWN4.src.fdGame]]}]
      ]
    },
    {
      caption: "Competition status",
      head: ["Item", "Status", "Detail"],
      rows: [
        ["Strategies registered", "12 archetypes (S1–S12)", {t:"Strategy catalog", u:"pages/strategies.html"}],
        ["Strategies past all validation gates", {t:"", flag:"UNVERIFIED"}, "No official line-history dataset was ingested in this session, so no backtest has been run; performance cells are blank by policy. See flags F1–F2."],
        ["Correlation values measured", {t:"", flag:"UNVERIFIED"}, "Methodology defined; measured ρ values blank until computed from official game results + official line history. See flag F1."],
        ["Site build", "Static GitHub Pages, no external dependencies", "index.html + pages/ + assets/ — verify on the Source Register page."]
      ]
    }
  ]
},

/* -------------------------------- league ------------------------------- */
league: {
  title: "League & Rules — verified facts",
  intro: "Line-by-line verified league facts. Each row links to the official page it was confirmed on (nba.com / official.nba.com / the official 2025-26 NBA Playing Rules PDF on cdn.nba.com), accessed 2026-11-02.",
  tables: [
    {
      caption: "League identity & structure",
      head: ["Item", "Verified value", "Official source"],
      rows: [
        ["League", "National Basketball Association (NBA) — professional league of 30 teams across North America", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Teams", "30 total", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Conferences / divisions", "2 conferences (Eastern, Western) × 3 divisions each", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Regular-season games per team", "82 (stated for the 2025-26 season; the 2026-27 season is also 82 games)", {t:"About + Cup 101", links:[["About",OWN4.src.about],["Cup 101",OWN4.src.cup101]]}],
        ["Total regular-season games", {t:"1,230 — derived arithmetic (30 teams × 82 ÷ 2) from the two official facts above", flag:"DERIVED"}, {t:"derived from About + Cup 101", links:[["About",OWN4.src.about],["Cup 101",OWN4.src.cup101]]}],
        ["Founded", "1946 at the Commodore Hotel, New York (originally the Basketball Association of America; merged with the NBL in 1949 to form the NBA). First president: Maurice Podoloff", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Roster size", "Maximum 15 players per team, of which 12 can be active each game", {t:"nba.com — About the NBA", u:OWN4.src.about}],
        ["Most championships", "Boston Celtics 18, Los Angeles Lakers 17, Golden State Warriors 7, Chicago Bulls 6, San Antonio Spurs 5", {t:"nba.com About + championships article", links:[["About",OWN4.src.about],["Titles article",OWN4.src.champs]]}],
        ["Replay Center", "NBA Replay Center in Secaucus, N.J., launched with the 2014-15 season", {t:"About + official.nba.com/replay", links:[["About",OWN4.src.about],["official.nba.com/replay",OWN4.src.replay]]}]
      ]
    },
    {
      caption: "Game timing & clock (Official 2025-26 NBA Playing Rules PDF, Rule 6 & Rule 7)",
      head: ["Item", "Verified value", "Official source"],
      rows: [
        ["Quarters", "All periods of regulation play are 12 minutes (4 periods = 48 minutes)", {t:"2025-26 Playing Rules PDF (Rule 6, Sec. II.a); also nba.com About", links:[["Rules PDF",OWN4.src.rulesPdf],["About",OWN4.src.about]]}],
        ["Overtime", "All overtime periods are 5 minutes", {t:"Rules PDF (Rule 6.b); nba.com About", links:[["Rules PDF",OWN4.src.rulesPdf],["About",OWN4.src.about]]}],
        ["Halftime", "15 minutes permitted between halves", {t:"Rules PDF (Rule 6.c)", u:OWN4.src.rulesPdf}],
        ["Shot clock", "24 seconds (Rule No. 7); resets to 24 or 14 in defined situations", {t:"Rules PDF (Rule 7); nba.com About", links:[["Rules PDF",OWN4.src.rulesPdf],["About",OWN4.src.about]]}],
        ["Mandatory timeouts", "Two mandatory timeouts in each period; if neither team has taken a timeout by 6:59 of the period it is mandatory", {t:"Rules PDF (Rule 6 timeout provisions)", u:OWN4.src.rulesPdf}],
        ["Fourth-period timeout limits", "Max 4 team timeouts in the 4th period; max 2 after the later of the 3-minute mark or the 2nd mandatory timeout", {t:"Rules PDF (Rule 6)", u:OWN4.src.rulesPdf}],
        ["Overtime timeouts", "Each team allowed 2 team timeouts in each overtime period", {t:"Rules PDF (Rule 6)", u:OWN4.src.rulesPdf}]
      ]
    },
    {
      caption: "Court & equipment (nba.com About; official rules Rule No. 1)",
      head: ["Item", "Verified value", "Official source"],
      rows: [
        ["Court dimensions", "94 feet long × 50 feet wide", {t:"nba.com About; Rule No. 1", links:[["About",OWN4.src.about],["official.nba.com Rule 1",OWN4.src.rule1]]}],
        ["Rim height", "10 feet from the floor", {t:"nba.com About", u:OWN4.src.about}],
        ["Free throw line", "15 feet from the rim (per nba.com About wording)", {t:"nba.com About", u:OWN4.src.about}],
        ["3-point arc", "23 ft 9 in from the basket at the top of the arc; 22 ft in the corners", {t:"nba.com About", u:OWN4.src.about}],
        ["Basketball", "9 inches in diameter, inflated to 8.5–9.5 psi", {t:"nba.com About", u:OWN4.src.about}],
        ["Official rules (full text)", "Official NBA Playing Rules, hosted on cdn.nba.com; rule index on official.nba.com", {t:"2025-26 Rules PDF + Rule No. 1 page", links:[["Rules PDF",OWN4.src.rulesPdf],["Rule No. 1",OWN4.src.rule1]]}]
      ]
    },
    {
      caption: "Playoffs & postseason format",
      head: ["Item", "Verified value", "Official source"],
      rows: [
        ["Playoff field", "Teams 1–6 in each conference are guaranteed a playoff spot; teams 7–10 enter the Playoff Play-In Tournament for the 7th and 8th seeds", {t:"nba.com About + Play-In article", links:[["About",OWN4.src.about],["Play-In 2026",OWN4.src.playin]]}],
        ["Play-In mechanics (example, 2026)", "7v8 game → winner is 7 seed; 9v10 game → loser eliminated; loser of 7v8 plays winner of 9v10 for the 8 seed", {t:"nba.com Play-In article / playoff picture", links:[["Play-In article",OWN4.src.playin],["Playoff picture", "https://www.nba.com/pacers/playoff-picture"]]}],
        ["Series format", "Each playoff round is a best-of-seven series with a 2-2-1-1-1 home-court format; conference winners meet in the best-of-seven NBA Finals", {t:"nba.com FAQ", u:OWN4.src.faq}],
        ["2026-27 postseason dates", "Regular season ends Apr 11, 2027; rosters set Apr 12; SoFi NBA Play-In Tournament Apr 13–16, 2027; Playoffs begin Apr 17", {t:"nba.com key dates", u:OWN4.src.keyDates, flag:"label on page reads 'Playoffs 2026' — flag F5"}]
      ]
    }
  ]
},

/* -------------------------------- season ------------------------------- */
season: {
  title: "2026-27 NBA Season — calendar & competition rules",
  intro: "Current season is 2026-27 (tipped off Oct 20, 2026). All dates below were verified on official NBA pages on 2026-11-02.",
  tables: [
    {
      caption: "2026-27 key dates",
      head: ["Date(s)", "Event", "Official source"],
      rows: [
        ["Aug 13, 2026", "Full 2026-27 regular-season schedule released; dates/opponents fixed for 80 of each team's 82 games; the other 2 games (played Dec 4–10) are set by Emirates NBA Cup Group Play results", {t:"nba.com schedule release", u:OWN4.src.sched}],
        ["Sep 29, 2026", "Training camps open", {t:"2026-27 calendar article", u:OWN4.src.cal}],
        ["Oct 3–16, 2026", "Preseason", {t:"G League key dates / calendar article", links:[["gleague.nba.com",OWN4.src.gKey],["calendar",OWN4.src.cal]]}],
        ["Oct 19, 2026", "Final rosters set for opening day (5 p.m. ET)", {t:"calendar article / G League key dates", links:[["calendar",OWN4.src.cal],["gleague.nba.com",OWN4.src.gKey]]}],
        ["Oct 20, 2026", "Opening night / regular season begins — NBC/Peacock tripleheader: Celtics@Pistons (3 ET), defending champion Knicks host 76ers (7 ET, MSG), Thunder@Spurs (9:30 ET)", {t:"nba.com news", links:[["Rosters set article",OWN4.src.rosters],["Season opener",OWN4.src.opener],["Calendar",OWN4.src.cal]]}],
        ["Oct 30 – Nov 27, 2026", "Emirates NBA Cup 2026 Group Play (60 games; Cup Nights Oct 30, Nov 6, 13, 20, 24, 25, 27)", {t:"Cup 101 / FAQ / schedule release", links:[["Cup 101",OWN4.src.cup101],["Cup FAQ",OWN4.src.cupFaq],["Schedule announced",OWN4.src.schedB]]}],
        ["Nov 7, 2026", "NBA Mexico City Game — played at Arena CDMX (per arena note in official schedule PDF)", {t:"official schedule PDF (cdn.nba.com)", u:OWN4.src.schedPdf, flag:"gleague key-dates page labels it '2025' — flag F7"}],
        ["Dec 4–11, 2026", "Emirates NBA Cup Knockout Rounds (Quarterfinals Dec 4/5, Semifinals Dec 8/9) and Championship on Fri Dec 11 at Hinkle Fieldhouse, Indianapolis; Championship does NOT count toward regular-season standings", {t:"Cup 101 / FAQ / calendar", links:[["Cup 101",OWN4.src.cup101],["Cup FAQ",OWN4.src.cupFaq],["Calendar",OWN4.src.cal]]}],
        ["Jan 5, 2027", "First day 10-day contracts may be signed", {t:"calendar article / G League key dates", links:[["calendar",OWN4.src.cal],["gleague.nba.com",OWN4.src.gKey]]}],
        ["Jan 10, 2027", "All NBA contracts become fully guaranteed for the remainder of the season", {t:"calendar / G League key dates", links:[["calendar",OWN4.src.cal],["gleague.nba.com",OWN4.src.gKey]]}],
        ["Feb 11, 2027", "NBA trade deadline", {t:"2026-27 calendar article", u:OWN4.src.cal}],
        ["Feb 19–21, 2027", "2027 NBA All-Star, Phoenix, AZ", {t:"G League key dates", u:OWN4.src.gKey}],
        ["Apr 11, 2027", "2026-27 regular season ends (all 30 teams play)", {t:"nba.com key dates", u:OWN4.src.keyDates}],
        ["Apr 12, 2027", "Rosters set for NBA Playoffs (3 p.m. ET)", {t:"nba.com key dates", u:OWN4.src.keyDates}],
        ["Apr 13–16, 2027", "SoFi NBA Play-In Tournament", {t:"nba.com key dates", u:OWN4.src.keyDates}],
        ["Apr 17, 2027", "NBA Playoffs begin", {t:"nba.com key dates", u:OWN4.src.keyDates, flag:"page labels this entry 'Playoffs 2026' inside the 2026-27 list — flag F5"}]
      ]
    },
    {
      caption: "Emirates NBA Cup 2026 — official rules",
      head: ["Rule", "Verified detail", "Official source"],
      rows: [
        ["Participation", "All 30 teams, randomly drawn into groups of five within their conference (3 groups per conference, 6 total), seeded by prior-season (2025-26) win-loss records", {t:"Cup 101", u:OWN4.src.cup101}],
        ["Group Play", "Each team plays 4 designated Group Play games on Cup Nights (Oct 30 – Nov 27, 2026) — one vs each group opponent, 2 home / 2 road; 60 Group Play games total", {t:"Cup 101 / schedule announced", links:[["Cup 101",OWN4.src.cup101],["Schedule announced",OWN4.src.schedB]]}],
        ["Standings impact", "All 67 Cup games across both stages count toward regular-season standings EXCEPT the Championship; every team still plays an 82-game regular season", {t:"Cup 101 / Cup FAQ", links:[["Cup 101",OWN4.src.cup101],["Cup FAQ",OWN4.src.cupFaq]]}],
        ["Knockout Rounds", "8 teams advance: best team in each of the 6 groups + 1 wild card per conference (best 2nd-place group team); single elimination; Quarterfinals and Semifinals count as regular-season games; Championship (Dec 11, Hinkle Fieldhouse, Indianapolis) does not", {t:"Cup FAQ / Cup 101", links:[["Cup FAQ",OWN4.src.cupFaq],["Cup 101",OWN4.src.cup101]]}],
        ["Venue note", "All tournament games in NBA team markets except the Championship (Hinkle Fieldhouse, Indianapolis)", {t:"Cup FAQ", u:OWN4.src.cupFaq}]
      ]
    },
    {
      caption: "Schedule anomalies noted in the official 2026-27 schedule PDF (arena notes)",
      head: ["Game date", "Note", "Official source"],
      rows: [
        ["Fri 10/23/2026", "Game played at Moody Center, Austin, TX (arena note in official schedule PDF)", {t:"official schedule PDF", u:OWN4.src.schedPdf}],
        ["Sat 11/7/2026", "Game played at Arena CDMX, Mexico City (arena note in official schedule PDF)", {t:"official schedule PDF", u:OWN4.src.schedPdf}],
        ["Fri 2/26/2027", "Game played at Moody Center, Austin, TX (arena note in official schedule PDF)", {t:"official schedule PDF", u:OWN4.src.schedPdf}]
      ]
    }
  ]
},

/* -------------------------------- teams -------------------------------- */
teams: {
  title: "Teams & Arenas — all 30 franchises",
  intro: "Division membership verified on nba.com/news/about; team IDs and official team sites verified on nba.com/teams; arena names verified on the official NBA tickets site (nbatickets.nba.com). One naming discrepancy (Phoenix) is flagged — see F6 on the Flagged for Review page.",
  tables: [
    {
      caption: "Eastern Conference",
      head: ["Team", "Division", "Team ID", "Official team site", "Arena (official tickets site)", "Sources"],
      rows: [
        ["Boston Celtics", "Atlantic", "1610612738", {t:"nba.com/celtics", u:"https://www.nba.com/celtics/"}, "TD Garden", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Brooklyn Nets", "Atlantic", "1610612751", {t:"nba.com/nets", u:"https://www.nba.com/nets/"}, "Barclays Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["New York Knicks", "Atlantic", "1610612752", {t:"nba.com/knicks", u:"https://www.nba.com/knicks/"}, "Madison Square Garden", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Philadelphia 76ers", "Atlantic", "1610612755", {t:"nba.com/sixers", u:"https://www.nba.com/sixers/"}, "Wells Fargo Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Toronto Raptors", "Atlantic", "1610612761", {t:"nba.com/raptors", u:"https://www.nba.com/raptors/"}, "Scotiabank Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Chicago Bulls", "Central", "1610612741", {t:"nba.com/bulls", u:"https://www.nba.com/bulls/"}, "United Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Cleveland Cavaliers", "Central", "1610612739", {t:"nba.com/cavaliers", u:"https://www.nba.com/cavaliers/"}, "Rocket Mortgage FieldHouse", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Detroit Pistons", "Central", "1610612765", {t:"nba.com/pistons", u:"https://www.nba.com/pistons/"}, "Little Caesars Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Indiana Pacers", "Central", "1610612754", {t:"nba.com/pacers", u:"https://www.nba.com/pacers/"}, "Gainbridge Fieldhouse", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Milwaukee Bucks", "Central", "1610612749", {t:"nba.com/bucks", u:"https://www.nba.com/bucks/"}, "Fiserv Forum", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Atlanta Hawks", "Southeast", "1610612737", {t:"nba.com/hawks", u:"https://www.nba.com/hawks/"}, "State Farm Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Charlotte Hornets", "Southeast", "1610612766", {t:"nba.com/hornets", u:"https://www.nba.com/hornets/"}, "Spectrum Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Miami Heat", "Southeast", "1610612748", {t:"nba.com/heat", u:"https://www.nba.com/heat/"}, "Kaseya Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Orlando Magic", "Southeast", "1610612753", {t:"nba.com/magic", u:"https://www.nba.com/magic/"}, "Kia Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Washington Wizards", "Southeast", "1610612764", {t:"nba.com/wizards", u:"https://www.nba.com/wizards/"}, "Capital One Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}]
      ]
    },
    {
      caption: "Western Conference",
      head: ["Team", "Division", "Team ID", "Official team site", "Arena (official tickets site)", "Sources"],
      rows: [
        ["Denver Nuggets", "Northwest", "1610612743", {t:"nba.com/nuggets", u:"https://www.nba.com/nuggets/"}, "Ball Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Minnesota Timberwolves", "Northwest", "1610612750", {t:"nba.com/timberwolves", u:"https://www.nba.com/timberwolves/"}, "Target Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Oklahoma City Thunder", "Northwest", "1610612760", {t:"nba.com/thunder", u:"https://www.nba.com/thunder/"}, "Paycom Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Portland Trail Blazers", "Northwest", "1610612757", {t:"nba.com/blazers", u:"https://www.nba.com/blazers/"}, "Moda Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Utah Jazz", "Northwest", "1610612762", {t:"nba.com/jazz", u:"https://www.nba.com/jazz/"}, "Delta Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Golden State Warriors", "Pacific", "1610612744", {t:"nba.com/warriors", u:"https://www.nba.com/warriors/"}, "Chase Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["LA Clippers", "Pacific", "1610612746", {t:"nba.com/clippers", u:"https://www.nba.com/clippers/"}, "Intuit Dome", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Los Angeles Lakers", "Pacific", "1610612747", {t:"nba.com/lakers", u:"https://www.nba.com/lakers/"}, "Crypto.com Arena", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Phoenix Suns", "Pacific", "1610612756", {t:"nba.com/suns", u:"https://www.nba.com/suns/"}, {t:"PHX Arena per nbatickets.nba.com (nba.com arena articles say Footprint Center)", flag:"FLAG F6 — see Flagged for Review"}, {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Sacramento Kings", "Pacific", "1610612758", {t:"nba.com/kings", u:"https://www.nba.com/kings/"}, "Golden 1 Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Dallas Mavericks", "Southwest", "1610612742", {t:"nba.com/mavs", u:"https://www.nba.com/mavs/"}, "American Airlines Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Houston Rockets", "Southwest", "1610612745", {t:"nba.com/rockets", u:"https://www.nba.com/rockets/"}, "Toyota Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["Memphis Grizzlies", "Southwest", "1610612763", {t:"nba.com/grizzlies", u:"https://www.nba.com/grizzlies/"}, "FedExForum", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["New Orleans Pelicans", "Southwest", "1610612740", {t:"nba.com/pelicans", u:"https://www.nba.com/pelicans/"}, "Smoothie King Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}],
        ["San Antonio Spurs", "Southwest", "1610612759", {t:"nba.com/spurs", u:"https://www.nba.com/spurs/"}, "Frost Bank Center", {t:"about / teams / tickets", links:[["About",OWN4.src.about],["Teams",OWN4.src.teams],["Tickets",OWN4.src.tickets]]}]
      ]
    },
    {
      caption: "Official live-data pages (scores, standings, team/player profiles, schedule, injury reports)",
      head: ["Data", "Official page", "Notes (verified 2026-11-02)"],
      rows: [
        ["Standings", {t:"nba.com/standings", u:OWN4.src.standings}, "Official conference standings"],
        ["Scores / box scores / schedule", {t:"nba.com/games", u:OWN4.src.games}, "Official daily scores; game pages e.g. nba.com/game/…"],
        ["Team profiles (live record, PPG/RPG/APG/OPPG, roster)", {t:"nba.com/team/<id> — e.g. Knicks", u:OWN4.src.knicks}, {t:"Point-in-time snapshot on access date: NYK 2-4, 10th in Eastern (flag F11 — records change daily)", flag:"SNAPSHOT"}],
        ["Player index & profiles", {t:"nba.com/players", u:OWN4.src.players}, "Official player index; profiles at nba.com/player/<id>"],
        ["Statistics platform", {t:"stats.nba.com", u:OWN4.src.stats}, "Leaders, all-time leaders, team/player stats (see Official Stats page)"],
        ["Official injury reports", {t:"NBA injury report PDFs (ak-static.cms.nba.com/referee/injury/) — e.g. 10/28/26 4:00 PM report", u:OWN4.src.injury}, "Daily PDFs with per-game player status (Out/Questionable/Probable/Doubtful/Available) and reason"],
        ["Full 2026-27 schedule (per team)", {t:"2026-27 schedule PDF (cdn.nba.com)", u:OWN4.src.schedPdf}, "Includes arena notes for Mexico City / Austin games"]
      ]
    }
  ]
}
});

/* Own4 — data part 2: official stats + lines & bet markets. */
var OWN4 = window.OWN4 = window.OWN4 || {};
OWN4.pages = Object.assign(OWN4.pages || {}, {

stats: {
  title: "Official Stats — definitions, minimums, platforms",
  intro: "All stat definitions below are quoted from the official NBA stats glossary (stats.nba.com/help/glossary/) and the official leader minimums page (stats.nba.com/help/statminimums). Only entries directly viewed on 2026-11-02 are quoted — nothing is inferred for stats that were not displayed (flag F12). Box-score abbreviations are from DraftKings Sportsbook's official support glossary.",
  tables: [
    {
      caption: "Official stat definitions (stats.nba.com/help/glossary/)",
      head: ["Stat", "Official definition (quoted)", "Type", "Source"],
      rows: [
        ["PTS", "“The number of points scored”", "Traditional", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["REB", "“A rebound occurs when a player recovers the ball after a missed shot. This statistic is the number of total rebounds a player or team has collected on either offense or defense”", "Traditional", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["OREB", "“The number of rebounds a player or team has collected while they were on offense”", "Traditional", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["AST", "“The number of assists -- passes that lead directly to a made basket -- by a player”", "Traditional", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["%AST", "“The percentage of a team's assists that a player has while on the court”", "Usage", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["%PTS", "“The percentage of a team's points that a player has while on the court”", "Usage", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["AST/TO", "“The number of assists for a player or team compared to the number of turnovers they have committed”", "Advanced", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["DEFRTG", "“The number of points allowed per 100 possessions by a team. For a player, it is the number of points per 100 possessions that the team allows while that individual player is on the court”", "Advanced", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["PITP", "“The number of points scored by a player or team in the paint”", "Misc", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["PPP", "“The number of points a player or team scores per possession”", "Tracking", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["FP", "“The number of fantasy points a player accumulates” — Formula: Pts 1, Reb 1.2, Ast 1.5, Stl 3, Blk 3, TO -1", "Traditional", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["AST ADJ", "“The total sum of a player or team's assists, free throw assists, and secondary assists”", "Tracking", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["AST PTS Created", "“Points created by a player or team through their assists”", "Tracking", {t:"stats.nba.com glossary", u:OWN4.src.glossary}],
        ["Player PTS DIFF", "“An offensive player's Points per 100 Possessions in a specific matchup compared to their season average…” — Formula: 100×(Matchup Player Points/Matchup Possessions) − Player's Season Average Points per 100 Possessions", "Matchups", {t:"stats.nba.com glossary", u:OWN4.src.glossary}]
      ]
    },
    {
      caption: "Statistical minimums to qualify for NBA league-leader titles (stats.nba.com/help/statminimums)",
      head: ["Category", "Season minimum", "Career minimum", "Source"],
      rows: [
        ["Scoring / Rebounds / Assists / Steals / Blocks / Minutes", "Player must play 70% of his team's games (58 in an 82-game season)*", "400 games played OR 10,000 PTS / 4,000 REB / 2,000 AST / 625 STL / 500 BLK / 10,000 MIN as applicable", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["Field goal %", "300 field goals made", "2,000 FGM", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["Free throw %", "125 free throws made", "1,200 FTM", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["3-point %", "82 three-point field goals made", "250 3PM", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["AST/TO ratio", "200 assists", "1,000 AST", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["STL/TO ratio", "82 steals", "400 STL", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}],
        ["*Exception", "A player who would have led the category had he played the required number of games may still qualify (per official page)", "—", {t:"stats.nba.com stat minimums", u:OWN4.src.minimums}]
      ]
    },
    {
      caption: "Box-score abbreviations (DraftKings Sportsbook official support glossary — NBA)",
      head: ["Abbr.", "Stat", "Source"],
      rows: [
        ["MIN / PTS / REB / AST", "Minutes / Points / Total Rebounds / Assists", {t:"support.draftkings.com box-score glossary", u:OWN4.src.dkGloss}],
        ["FG, FG% / 3PT, 3PT% / FT, FT%", "Field goals (made/attempted, %), three-pointers, free throws", {t:"support.draftkings.com box-score glossary", u:OWN4.src.dkGloss}],
        ["BLK / STL / TO / PF", "Blocks / Steals / Turnovers / Personal Fouls", {t:"support.draftkings.com box-score glossary", u:OWN4.src.dkGloss}]
      ]
    },
    {
      caption: "Official stats platforms",
      head: ["Platform", "Contents", "Source"],
      rows: [
        ["stats.nba.com", "League leaders, all-time leaders, traditional/advanced/hustle/clutch/tracking stats, player & team dashboards", {t:"stats.nba.com", u:OWN4.src.stats}],
        ["nba.com/standings", "Official standings", {t:"nba.com/standings", u:OWN4.src.standings}],
        ["nba.com/games + game pages", "Scores, box scores, play-by-play", {t:"nba.com/games", u:OWN4.src.games}],
        ["nba.com/team/<id>", "Team profile: record, PPG/RPG/APG/OPPG, roster, schedule, stats", {t:"e.g. nba.com/team/1610612752/knicks", u:OWN4.src.knicks}],
        ["nba.com/player/<id>", "Player profile, stats, game logs", {t:"nba.com/players", u:OWN4.src.players}],
        ["NBA daily injury report PDFs", "Per-game player availability (Out/Questionable/Probable/Doubtful/Available) with reasons — the official input for injury-driven signals", {t:"ak-static.cms.nba.com injury report (10/28/26 example)", u:OWN4.src.injury}]
      ]
    }
  ]
},

markets: {
  title: "Lines & Bet Markets — where official lines live and how markets work",
  intro: "NBA.com does not publish betting lines; official lines are published by licensed sportsbooks and distributed as official league data by the NBA's authorized betting-data partners (Sportradar — exclusive worldwide; Genius Sports — U.S.). Definitions below are quoted from the official sportsbook pages and help centers.",
  tables: [
    {
      caption: "Where official NBA lines & odds are published",
      head: ["Channel", "What it offers", "Official source"],
      rows: [
        ["DraftKings Sportsbook — NBA", "Game lines (moneyline, spread, total), player props, parlays, futures, live betting; explains American odds (+150 = $100 wins $150; -200 = must wager $200 to win $100)", {t:"sportsbook.draftkings.com/leagues/basketball/nba", u:OWN4.src.dkNba}],
        ["FanDuel Sportsbook — NBA game pages", "Game Lines (Spread/Money/Total), player props (Points, Rebounds, Assists, Made Threes, Pts+Reb+Ast, Pts+Reb, Pts+Ast, Reb+Ast, Double-Double, Triple-Double), quarter/half props, Same Game Parlay — verified on a live Nov 2, 2026 game page (BKN@NYK: spread +14.5/-110, total 221.5, moneyline +610/-900)", {t:"sportsbook.fanduel.com game page", u:OWN4.src.fdGame}],
        ["Sportradar (NBA official data partner)", "Exclusive worldwide provider of NBA/WNBA/G League data; authorized global distributor of official NBA betting data; runs UFDS (Universal Fraud Detection System) to monitor global betting activity for integrity", {t:"pr.nba.com + Sportradar IR", links:[["pr.nba.com 2018",OWN4.src.prData],["pr.nba.com 2016",OWN4.src.prData16],["Sportradar 2021",OWN4.src.sr2021]]}],
        ["Genius Sports", "Non-exclusive rights to distribute official NBA betting data to licensed U.S. sportsbooks (since 2018-19)", {t:"pr.nba.com", u:OWN4.src.prData}]
      ]
    },
    {
      caption: "Bet types — official definitions",
      head: ["Bet type", "Official definition / mechanics", "Source"],
      rows: [
        ["Moneyline", "“Moneyline betting involves picking the outright winner of a game. Favorites typically carry negative odds, while underdogs are listed with positive odds.”", {t:"DraftKings NBA page", u:OWN4.src.dkNba}],
        ["Point spread", "Handicap on the margin of victory; a push (exact margin) returns the stake on a straight bet", {t:"FanDuel help — push rules; DK NBA page", links:[["FanDuel push",OWN4.src.fdPush],["DK NBA",OWN4.src.dkNba]]}],
        ["Total (Over/Under)", "“Totals betting involves predicting whether the combined score of both teams will finish over or under a projected number set by the sportsbook.”", {t:"DraftKings NBA page", u:OWN4.src.dkNba}],
        ["Player props", "“NBA player props allow bettors to wager on individual player statistics, including points, rebounds, assists, three-pointers, and more.” Combo markets (PRA, DD, TD) are listed on FanDuel game pages", {t:"DK NBA page + FanDuel game page", links:[["DK",OWN4.src.dkNba],["FanDuel",OWN4.src.fdGame]]}],
        ["Parlay", "“A single bet that links together two or more wagers; to win the bet, the player must win all the wagers in the parlay… if he wins all the wagers, they win a higher payoff than if they had placed the bets separately.” Odds multiply (house-rules example: -190 with +145 → +275)", {t:"FanDuel terms + DK house rules PDF", links:[["FanDuel",OWN4.src.fdTerms],["DK house rules",OWN4.src.dkHouse]]}],
        ["Parlay push/void handling", "A pushed leg “falls off” and the parlay is recalculated with the remaining legs (e.g., 4-leg → 3-leg at revised odds)", {t:"FanDuel help", u:OWN4.src.fdPush}],
        ["Same Game Parlay (SGP)", "“A type of parlay that combines two or more selections from a single game or correlated games, matches, or events” (FanDuel); DK house rules: “a single bet combining multiple selections from the same event… dependent on all of those selections winning”", {t:"FanDuel SGP + DK house rules", links:[["FanDuel SGP",OWN4.src.fdSgp],["DK house rules",OWN4.src.dkHouse]]}],
        ["SGP+", "Same Game Parlay+ combines an SGP with SGP-eligible bets from other games", {t:"FanDuel SGP+", u:OWN4.src.fdSgp}],
        ["Round robin", "A series of parlays covering every combination of the selected legs (e.g., 3 teams “by 2s” = three 2-leg parlays + one 3-leg parlay); up to 16 legs, max 15-leg parlays", {t:"FanDuel round robin", u:OWN4.src.fdRr}],
        ["Teaser", "A parlay where each spread/total is adjusted in the bettor's favor for lower payoff odds", {t:"FanDuel terms + teaser help", links:[["terms",OWN4.src.fdTerms],["teasers",OWN4.src.fdTeaser]]}],
        ["Live betting", "Wagers placed after tip-off with odds updating in real time; markets include moneylines, spreads, totals, player props", {t:"DraftKings NBA page", u:OWN4.src.dkNba}],
        ["Futures", "Season-long markets (e.g., championship winner, division winner) offered alongside game lines", {t:"DraftKings NBA futures pages", u:OWN4.src.dkNba}]
      ]
    },
    {
      caption: "Correlation & settlement rules (official sportsbook rules)",
      head: ["Rule", "Official text / effect", "Source"],
      rows: [
        ["Correlated outcomes barred from standard parlays", "“A bet made as a parlay, except made as a Same Game Parlay, shall never include two or more offers where the outcomes of which might turn out to be related (e.g. Team X to become champions and Player Y to be Top Goal Scorer in the same league).”", {t:"DK house rules PDF (regulator-hosted)", u:OWN4.src.dkHouse, flag:"flag F9 — official content, third-party (regulator) host"}],
        ["Settlement source", "“All settlements are based on the statistics and results provided by the official website of the league's governing body, or league's official statistical provider” — i.e., NBA official stats settle NBA bets", {t:"DK house rules PDF", u:OWN4.src.dkHouse}],
        ["SGP void/push repricing", "A void or pushed leg in a pre-live or live SGP voids that selection and reprices the SGP at the odds available at placement; if all selections void, the bet is void", {t:"DK house rules PDF", u:OWN4.src.dkHouse}],
        ["Player prop settlement", "Player markets are settled when the game is final, per the league's official statistical provider; non-participating player rules apply", {t:"DK house rules PDF", u:OWN4.src.dkHouse}],
        ["Early Exit Protected (NBA player props)", "If an NBA player leaves during the first half due to injury and does not return, eligible full-game player prop selections settle as Void (stake returned); in parlays/SGPs the leg is voided and the ticket repriced", {t:"DraftKings support", u:OWN4.src.dkEarly}]
      ]
    },
    {
      caption: "Integrity & responsible gambling (official)",
      head: ["Item", "Detail", "Source"],
      rows: [
        ["League integrity monitoring", "Sportradar Integrity Services / UFDS monitor global betting activity and trends; NBA has internal integrity group and data-sharing agreements with sportsbook partners", {t:"pr.nba.com + Sportradar IR", links:[["pr.nba.com 2016",OWN4.src.prData16],["Sportradar 2021",OWN4.src.sr2021]]}],
        ["League restrictions on certain prop markets (press report)", "Oct 16, 2026 press report: NBA told sportsbooks it will not permit certain wagers (first basket/first stat, opening tip, unders on low-minute players, multiple under legs on one player in a parlay)", {t:"Boston Globe (press — NOT an official league publication)", u:OWN4.src.globe, flag:"FLAG F8 — press source"}],
        ["Responsible gambling helpline", "National Problem Gambling Helpline: call/text 1-800-GAMBLER (1-800-426-2537), 24/7, chat at NCPGambling.org — operated by the National Council on Problem Gambling", {t:"ncpgambling.org", u:OWN4.src.ncpg}]
      ]
    }
  ]
}
});

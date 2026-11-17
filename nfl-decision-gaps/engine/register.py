#!/usr/bin/env python3
"""
nfl-decision-gaps — curated register (data only, no rendering).

Session: arena/e2e6ca5a-own4 · 2026-11-17.

Rules this file obeys
---------------------
1. Every `have` string is something this session actually read on an official page
   (source id in `sources`), or is a value computed by parsing a file already
   committed in this repository (source id in `sources`, marked `repo`).
2. Nothing is inferred. Where the official page did not state a thing, the field
   is the literal string "" (blank) and the row appears on the Flagged page.
3. Counts that describe the repository tree are computed at build time, never
   typed here (see engine/build.py `repo_inventory()`), because another session
   merging changes them.
"""

SESSION = "arena/e2e6ca5a-own4"
DATE = "2026-11-17"
WEEK = "Week 10, 2026 regular season"

# --------------------------------------------------------------------------
# Sources used in this register. `kind` is `live` (a point-in-time official
# page read; see `read` for date and coverage), `repo` (a committed repository
# file) or `absent` (an official route returned no such page).
# --------------------------------------------------------------------------
SOURCES = [
    dict(id="S1", kind="live",
         url="https://www.nfl.com/injuries/",
         title="Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com",
         what="Club-by-club injury tables (Player | Position | Injuries | Practice Status | Game Status) for all 14 Week 10 fixtures, plus the page's own news links.",
         read="Chunks 0-6 of 8 were read on 2026-11-16. Chunk 7 (tail of the page's news list) was not read.",
         published="Week 10, 2026"),
    dict(id="S2", kind="absent",
         url="https://www.nfl.com/teams/baltimore-ravens/depth-chart",
         title="404 - Flag on the Play.",
         what="Attempted club depth-chart page. The official server returned the 404 page; nfl.com does not serve a depth chart at this path.",
         read="HTTP 404 body read in full on 2026-11-16.",
         published=""),
    dict(id="S3", kind="live",
         url="https://www.nfl.com/teams/baltimore-ravens/",
         title="Baltimore Ravens News, Scores, Stats, Schedule | NFL.com",
         what="Club page. Section tabs are Info / Roster / Stats only. Team Info block: Head Coach Jesse Minter, Stadium M&T Bank Stadium, Owners Steve Bisciotti, Established 1996. Official Website baltimoreravens.com.",
         read="Read in full (1 chunk) on 2026-11-16.",
         published="2026-11-16"),
    dict(id="S4", kind="live",
         url="https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
         title="NFL Week 10 inactives: Players ruled out for Sunday's 12 games",
         what="Official inactive lists for all 12 Sunday/Munich Week 10 games, with the venue of each game and the pre-game club records.",
         read="Read in full (2 of 2 chunks) on 2026-11-16.",
         published="Nov 15, 2026"),
    dict(id="S5", kind="live",
         url="https://www.nfl.com/games/chargers-at-ravens-2026-reg-10",
         title="Los Angeles Chargers at Baltimore Ravens 2026 REG 10 - Game Center",
         what="Game Center for the Monday-night fixture. Game Info block publishes Location (BALTIMORE, MD), Stadium (M&T BANK STADIUM) and Network (ESPN, ABC).",
         read="Chunk 0 of 3 read on 2026-11-16.",
         published="2026-11-16"),
    dict(id="S6", kind="live",
         url="https://www.nfl.com/schedules",
         title="NFL Schedules: Games, Times, Matchups & Tickets",
         what="Historical Week 10 schedule read on 2026-11-16. PIT-CIN was rendered LIVE (Q1 08:56, PIT 0-CIN 3); preserve this as an observed page state, not as a final score. Current re-read is S11.",
         read="Read in full (2 of 2 chunks) on 2026-11-16. Requested /schedules/2026/REG11/ which resolved to this page.",
         published="2026-11-16"),
    dict(id="S7", kind="live",
         url="https://www.nfl.com/scores/",
         title="NFL Scores and Highlights: Live Updates, Results & Recaps",
         what="Historical Week 10 scoreboard read on 2026-11-16. PIT-CIN was rendered LIVE (Q1 08:56, PIT 0-CIN 3); preserve this as an observed page state, not as a final score. Current re-read is S12.",
         read="Chunk 0 of 3 read (LIVE + UPCOMING + first completed games) on 2026-11-16.",
         published="2026-11-16"),
    dict(id="S8", kind="repo",
         url="https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/raw/nfl_injuries_week10_2026.md",
         title="NFL.com Official Injury Report — Week 10, 2026 Season (verbatim capture)",
         what="A verbatim transcription of S1 captured 2026-11-13 and already committed to this repository. Parsed this session into 326 structured rows.",
         read="Parsed on 2026-11-16 by nfl-decision-gaps/engine/parse_injury_capture.py; sha256 recorded in data/injury_week10_parsed.json.",
         published="Captured 2026-11-13"),
    dict(id="S9", kind="live",
         url="https://www.nfl.com/transactions/league/trades/2026/11",
         title="2026 NFL League Transactions - Trades Waivers, Signings & more.",
         what="The league transactions hub, with dated categories: Trades, Signings, Reserve List, "
              "Waivers, Terminations, Other, each selectable by year and month. The November 2026 "
              "trades table lists 12 moves with From, To, Date, Name, Position and Transaction.",
         read="Read in full (1 chunk) on 2026-11-16 via https://www.nfl.com/transactions/ , which defaults to "
              "Trades / November 2026.",
         published="2026-11-16"),
    dict(id="S10", kind="live",
         url="https://www.nfl.com/transactions/league/reserve-list/2026/11",
         title="2026 NFL reserve-list by month | NFL.com",
         what="The official reserve list: 25 Reserve/Injured moves for November 2026, each with club, "
              "date and player. This is the page that makes 'not listed' stop meaning 'available'.",
         read="Read in full (2 of 2 chunks) on 2026-11-16.",
         published="2026-11-16"),
    dict(id="S11", kind="live",
         url="https://www.nfl.com/schedules/2026/by-week/week-10",
         title="NFL Week 10 Schedule 2026: Games, Times, Matchups & Tickets",
         what="Current official Week 10 schedule read on 2026-11-17: 13 fixtures are shown Final with scores, including PIT 18-CIN 38; LAC-BAL is still listed as scheduled for Nov 16, 8:15 PM ET, without a final score.",
         read="Both chunks read in order. Fetch tool exposes the date but not an exact clock time or response headers.",
         published="Week 10, 2026"),
    dict(id="S12", kind="live",
         url="https://www.nfl.com/scores/",
         title="NFL Scores and Highlights: Live Updates, Results & Recaps",
         what="Current official scores page read on 2026-11-17: PIT 18-CIN 38 Final; the 12 other completed Week 10 fixtures also show Final, while LAC-BAL remains a scheduled listing without a score.",
         read="Chunks 0-2 read in order. Fetch tool exposes the date but not an exact clock time or response headers.",
         published="2026 season; Week 10"),
    dict(id="S13", kind="live",
         url="https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
         title="Pittsburgh Steelers at Cincinnati Bengals 2026 REG 10 - Game Center",
         what="Game Center shows Pittsburgh 18, Cincinnati 38, Final for Week 10, Nov 15; the Game Book PDF link is present.",
         read="Chunk 0 of 2 read on 2026-11-17; fetch tool exposes the date but not an exact clock time or response headers.",
         published="Nov 15, 2026"),
    dict(id="S14", kind="live",
         url="https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
         title="Washington Commanders at New York Giants 2026 REG 10 - Game Center",
         what="Game Center shows Washington 24, New York 21, Final (Week 10, Nov 12), and Game Info Location EAST RUTHERFORD, NJ / Stadium METLIFE STADIUM.",
         read="Chunk 0 of 2 read on 2026-11-17; fetch tool exposes the date but not an exact clock time or response headers.",
         published="Nov 12, 2026"),
    dict(id="S15", kind="live",
         url="https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-to-be-released-thursday--may-14",
         title="2026 NFL Schedule Powered by AWS to be Released Thursday, May 14",
         what="Dated NFL announcement: published May 8, 2026, stating that the full 2026 schedule would be released May 14 at 8 p.m. ET; NFL.com and the NFL app would carry team and weekly schedules.",
         read="Read in full (1 chunk) on 2026-11-17.",
         published="May 08, 2026"),
    dict(id="S16", kind="live",
         url="https://www.nfl.com/schedules/2026/by-week/week-11",
         title="NFL Week 11 Schedule 2026: Games, Times, Matchups & Tickets",
         what="Current official Week 11 schedule read on 2026-11-17; the opening fixture is Colts at Texans, Thursday, Nov 19 at 8:15 PM ET.",
         read="Chunk 0 of 3 read. Fetch tool exposes the date but not an exact clock time or response headers.",
         published="Week 11, 2026"),
    dict(id="S17", kind="repo",
         url="https://github.com/sassnarep3-star/Own4/blob/main/nfl-collector/data/captures/2026-11-16/league_reserve_list_2026-11.json",
         title="Official reserve-list capture record — November 2026",
         what="The committed collector capture contains 25 structured Reserve/Injured rows; data/captures/ledger.json records the capture ID, 2026-11-16 read window and row hash.",
         read="Local capture JSON and ledger entry checked on 2026-11-17.",
         published="Captured 2026-11-16"),
    dict(id="S18", kind="repo",
         url="https://github.com/sassnarep3-star/Own4/blob/main/nfl-collector/data/captures/2026-11-16/league_transactions_trades_2026-11.json",
         title="Official trades capture record — November 2026",
         what="The committed collector capture contains 12 dated NFL trades; data/captures/ledger.json records the capture ID, 2026-11-16 read window and row hash.",
         read="Local capture JSON and ledger entry checked on 2026-11-17.",
         published="Captured 2026-11-16")
]

# --------------------------------------------------------------------------
# Official November 2026 reserve list, transcribed from S10.
# --------------------------------------------------------------------------
RESERVE_LIST = [
    ("2026-11-14", "NO", "Christen Miller", "Reserve/Injured"),
    ("2026-11-14", "NE", "TreVeyon Henderson", "Reserve/Injured"),
    ("2026-11-14", "CLE", "Michael Burton", "Reserve/Injured"),
    ("2026-11-14", "IND", "Mo Alie-Cox", "Reserve/Injured"),
    ("2026-11-14", "IND", "Akeem Davis-Gaither", "Reserve/Injured"),
    ("2026-11-14", "TEN", "Peter Skoronski", "Reserve/Injured"),
    ("2026-11-14", "TEN", "Tommy Townsend", "Reserve/Injured"),
    ("2026-11-14", "DAL", "Tyler Goodson", "Reserve/Injured"),
    ("2026-11-14", "GB", "Josh Whyle", "Reserve/Injured"),
    ("2026-11-12", "LAR", "Puka Nacua", "Reserve/Injured"),
    ("2026-11-10", "LAR", "Jordan Whittington", "Reserve/Injured"),
    ("2026-11-10", "MIA", "Zach Sieler", "Reserve/Injured"),
    ("2026-11-10", "MIA", "Malik Willis", "Reserve/Injured"),
    ("2026-11-10", "SF", "Gracen Halton", "Reserve/Injured"),
    ("2026-11-10", "AZ", "Gardner Minshew", "Reserve/Injured"),
    ("2026-11-10", "AZ", "Michael Wilson", "Reserve/Injured"),
    ("2026-11-09", "TEN", "James Williams", "Reserve/Injured"),
    ("2026-11-09", "MIN", "Demond Claiborne", "Reserve/Injured"),
    ("2026-11-09", "BUF", "Josh Palmer", "Reserve/Injured"),
    ("2026-11-07", "ATL", "Brian Robinson", "Reserve/Injured"),
    ("2026-11-07", "LAR", "Jaylen Watson", "Reserve/Injured"),
    ("2026-11-07", "DEN", "Eyioma Uwazurike", "Reserve/Injured"),
    ("2026-11-07", "DET", "Jack Campbell", "Reserve/Injured"),
    ("2026-11-07", "DAL", "Malachi Lawrence", "Reserve/Injured"),
    ("2026-11-07", "WAS", "Dyami Brown", "Reserve/Injured"),
]

# --------------------------------------------------------------------------
# Official November 2026 trades, transcribed from S9.
# --------------------------------------------------------------------------
TRADES = [
    ("2026-11-10", "ATL", "JAX", "Jessie Bates", "Traded"),
    ("2026-11-10", "PHI", "JAX", "Jordan Davis", "Traded"),
    ("2026-11-10", "TEN", "BUF", "Amani Hooker", "Traded"),
    ("2026-11-10", "IND", "SF", "Keenan Allen", "Traded"),
    ("2026-11-10", "LV", "MIN", "Kirk Cousins", "Traded"),
    ("2026-11-10", "LAC", "DEN", "Daiyan Henley", "Traded"),
    ("2026-11-10", "IND", "KC", "Josh Downs", "Traded"),
    ("2026-11-10", "ATL", "BAL", "Ryan Neuzil", "Traded"),
    ("2026-11-10", "BAL", "ATL", "Andrew Vorhees", "Traded"),
    ("2026-11-09", "NYJ", "DET", "Andre Cisco", "Traded"),
    ("2026-11-09", "NO", "JAX", "Davon Godchaux", "Traded"),
    ("2026-11-06", "AZ", "BAL", "Jacoby Brissett", "Traded"),
]

# --------------------------------------------------------------------------
# Verified Week 10 result states. Current scores/states cite the official NFL
# Week 10 schedule and scores pages; venue citations remain per fixture. The
# 2026-11-16 LIVE PIT-CIN observation is retained in S6/S7 and F1 as history.
# --------------------------------------------------------------------------
RESULTS = [
    dict(game="WAS at NYG", day="Thu Nov 12", away="WAS", away_pts=24, home="NYG", home_pts=21,
         state="final", status="Final", result_src="S11, S12",
         venue="MetLife Stadium (East Rutherford, N.J.)", venue_src="S14", note=""),
    dict(game="NE vs DET (Munich)", day="Sun Nov 15", away="NE", away_pts=10, home="DET", home_pts=35,
         state="final", status="Final", result_src="S11, S12",
         venue="FC Bayern Munich Stadium (Munich, Germany)", venue_src="S4", note=""),
    dict(game="KC at ATL", day="Sun Nov 15", away="KC", away_pts=35, home="ATL", home_pts=13,
         state="final", status="Final", result_src="S11, S12",
         venue="Mercedes-Benz Stadium (Atlanta)", venue_src="S4", note=""),
    dict(game="HOU at CLE", day="Sun Nov 15", away="HOU", away_pts=24, home="CLE", home_pts=27,
         state="final", status="Final", result_src="S11, S12",
         venue="Huntington Bank Field (Cleveland)", venue_src="S4", note=""),
    dict(game="MIN at GB", day="Sun Nov 15", away="MIN", away_pts=30, home="GB", home_pts=10,
         state="final", status="Final", result_src="S11, S12",
         venue="Lambeau Field (Green Bay, Wis.)", venue_src="S4", note=""),
    dict(game="MIA at IND", day="Sun Nov 15", away="MIA", away_pts=22, home="IND", home_pts=24,
         state="final", status="Final", result_src="S11, S12",
         venue="Lucas Oil Stadium (Indianapolis)", venue_src="S4", note=""),
    dict(game="CAR at NO", day="Sun Nov 15", away="CAR", away_pts=20, home="NO", home_pts=17,
         state="final", status="Final", result_src="S11, S12",
         venue="Caesars Superdome (New Orleans)", venue_src="S4", note=""),
    dict(game="BUF at NYJ", day="Sun Nov 15", away="BUF", away_pts=31, home="NYJ", home_pts=12,
         state="final", status="Final", result_src="S11, S12",
         venue="MetLife Stadium (East Rutherford, N.J.)", venue_src="S4", note=""),
    dict(game="JAX at TEN", day="Sun Nov 15", away="JAX", away_pts=40, home="TEN", home_pts=23,
         state="final", status="Final", result_src="S11, S12",
         venue="Nissan Stadium (Nashville, Tenn.)", venue_src="S4", note=""),
    dict(game="LAR at AZ", day="Sun Nov 15", away="LAR", away_pts=34, home="AZ", home_pts=6,
         state="final", status="Final", result_src="S11, S12",
         venue="State Farm Stadium (Glendale, Ariz.)", venue_src="S4", note=""),
    dict(game="SEA at LV", day="Sun Nov 15", away="SEA", away_pts=21, home="LV", home_pts=13,
         state="final", status="Final", result_src="S11, S12",
         venue="Allegiant Stadium (Las Vegas)", venue_src="S4", note=""),
    dict(game="SF at DAL", day="Sun Nov 15", away="SF", away_pts=46, home="DAL", home_pts=40,
         state="final", status="Final", result_src="S11, S12",
         venue="AT&T Stadium (Arlington, Texas)", venue_src="S4", note=""),
    dict(game="PIT at CIN", day="Sun Nov 15", away="PIT", away_pts=18, home="CIN", home_pts=38,
         state="final", status="Final", result_src="S11, S12, S13",
         venue="Paycor Stadium (Cincinnati)", venue_src="S4",
         note="The 2026-11-16 LIVE 0-3 observation is retained as historical evidence in F1."),
    dict(game="LAC at BAL", day="Mon Nov 16", away="LAC", away_pts=None, home="BAL", home_pts=None,
         state="scheduled",
         status="Scheduled (current official pages list Mon Nov 16, 8:15 PM ET; no final shown)",
         result_src="S11, S12",
         venue="M&T BANK STADIUM (BALTIMORE, MD)", venue_src="S5",
         note="Score remains blank; current official pages do not show a Final state. See F15."),
]

# --------------------------------------------------------------------------
# Official Week 10 inactive lists, transcribed from S4.
# --------------------------------------------------------------------------
INACTIVES = [
    ("NE", "Patriots", ["CB Carlton Davis", "FS Brenden Schooler", "OT Dametrious Crownover",
                        "OT Walter Rouse", "C Ben Brown", "QB Behren Morton (emergency third QB)"]),
    ("DET", "Lions", ["CB Keith Abney II", "EDGE Ahmed Hassanein", "C Cade Mays",
                      "LB Amen Ogbongbemiga", "CB D.J. Reed", "DL Mekhi Wingo"]),
    ("KC", "Chiefs", ["RB Kenneth Walker", "QB Garrett Nussmeier (Emergency 3rd QB)", "RB Jaydn Ott",
                      "CB Melvin Smith", "FB Ben VanSumeren", "OL Jaylon Moore", "DL Peter Woods"]),
    ("ATL", "Falcons", ["QB Andy Dalton (emergency third quarterback)", "ILB Divine Deablo",
                        "CB Avieon Terrell", "WR Zachariah Branch", "QB Jack Strand",
                        "CB Robert Longerbeam", "OL Cameron Williams"]),
    ("HOU", "Texans", ["LB Azeez Al-Shaair", "TE Brevin Jordan", "WR Marvin Harrison Jr.",
                       "RB David Montgomery", "DE Danielle Hunter", "C/G Keylan Rutledge",
                       "G Wyatt Teller"]),
    ("CLE", "Browns", ["QB Dillon Gabriel (emergency third QB)", "QB Taylen Green",
                       "LB Justin Jefferson", "CB Noah Igbinoghene", "S Ronnie Hickman",
                       "C Parker Brailsford"]),
    ("MIN", "Vikings", ["QB Kyler Murray", "WR Jordan Addison", "QB Max Brosmer (emergency third QB)",
                        "WR Jauan Jennings", "LB Blake Cashman", "TE T.J. Hockenson",
                        "DL Tyroin Ingram-Dawkins"]),
    ("GB", "Packers", ["RB Josh Jacobs", "RB Pierre Strong Jr.", "LB Zaire Franklin",
                       "G/T Donovan Jennings", "G Kevin Zeitler", "C Sean Rhyan"]),
    ("MIA", "Dolphins", ["WR Chris Bell", "CB Marcellas Dial Jr.", "C Aaron Brewer",
                         "G/T Caedan Wallace", "TE Justin Joly", "WR Jared Wayne"]),
    ("IND", "Colts", ["LB Jaylon Carlies", "QB Riley Leonard (emergency third QB)", "TE Will Mallory",
                      "LS Luke Rhodes", "DT Jerry Tillery", "OT Jalen Travis"]),
    ("CAR", "Panthers", ["TE Ja'Tavion Sanders", "QB Haynes King (emergency third QB)", "CB Will Lee",
                         "RB AJ Dillon", "LB Bobby Okereke", "C Sam Hecht", "DT TeRah Edwards"]),
    ("NO", "Saints", ["QB Zach Wilson (designated third QB)", "S Mike Reid", "RB CJ Donaldson",
                      "LB Jaylan Ford", "OT Taliese Fuaga", "C Erik McCoy"]),
    ("BUF", "Bills", ["QB Shane Buechele", "S Jalon Kilgore", "OLB Mike Danna",
                      "G Ar'maj Reed-Adams", "OL Jude Bowry", "DL Greg Gaines"]),
    ("NYJ", "Jets", ["CB Jarvis Brownlee Jr.", "Edge Nate Lynn", "WR Tim Patrick",
                     "LB Trevin Wallace", "TE Jelani Woods"]),
    ("JAX", "Jaguars", ["S Jessie Bates III", "WR CJ Williams", "DT Jordan Davis",
                        "DE Wesley Williams", "DT Albert Regis"]),
    ("TEN", "Titans", ["WR Carnell Tate", "RB Nick Singleton", "CB Jaylon Jones", "LB Cody Barton",
                       "LB Anthony Hill Jr.", "OT Brandon Crenshaw-Dickson", "DT Jackie Marshall"]),
    ("LAR", "Rams", ["QB Ty Simpson (emergency third QB)", "S Maximus Pulley", "LS Joe Cardona",
                     "OLB Darryl Peterson III", "OL Steve Avila", "OL Keagen Trost",
                     "OLB Desjuan Johnson"]),
    ("AZ", "Cardinals", ["QB Joey Aguilar", "CB Starling Thomas V", "LB Eku Leota",
                         "OL Jayden Williams", "OL Jon Gaines II", "OL Hjalte Froholdt"]),
    ("SEA", "Seahawks", ["QB Sam Darnold", "RB Emanuel Wilson", "CB Avery Smith", "G Quenton Nelson",
                         "OT Charles Cross", "NT Deven Eastern", "DT Leonard Williams"]),
    ("LV", "Raiders", ["WR Dont'e Thornton Jr.", "WR Malik Benson", "S Tristin McCollum",
                       "S Dalton Johnson", "G Bryce Cabeldue", "DT Thomas Booker IV"]),
    ("SF", "49ers", ["QB Kurtis Rourke", "WR Mike Evans", "OL Enrique Cruz Jr.", "LB Tatum Bethune",
                     "WR Brandin Cooks"]),
    ("DAL", "Cowboys", ["S P.J. Locke III", "OLB Donovan Ezeiruaku", "CB Derion Kendrick",
                        "WR Jonathan Mingo", "S Juanyeh Thomas", "G Ajani Cornelius",
                        "TE Jake Ferguson"]),
    ("PIT", "Steelers", ["S DeShon Elliott", "QB Drew Allar", "QB Will Howard (emergency third QB)",
                         "CB Sean Murphy-Bunting", "RB Eli Heidenreich"]),
    ("CIN", "Bengals", ["S Kyle Dugger", "C Connor Lew", "OT Myles Hinton", "DT Landon Robinson"]),
]

# --------------------------------------------------------------------------
# Injury report (S1, read live 2026-11-16) for the eight clubs where this
# session read every row, joined to the official inactive list (S4).
#
# `designation` is the Game Status cell exactly as published.  `inactive` is
# True when the player's name appears on that club's official inactive list.
# This table is the whole evidence base for questions Q01-Q04.
# --------------------------------------------------------------------------
DESIGNATION_JOIN = [
    # NE Patriots - live report 15 rows
    ("NE", "Ben Brown", "C", "Out", True, ""),
    ("NE", "A.J. Brown", "WR", "Questionable", False, ""),
    ("NE", "Kevin Byard", "S", "Questionable", False, ""),
    ("NE", "Carlton Davis III", "CB", "Out", True, ""),
    ("NE", "Reggie Gilliam", "FB", "Questionable", False, ""),
    ("NE", "TreVeyon Henderson", "RB", "Out", False, "Out on the report but absent from the inactive list; S1 news links report he was placed on injured reserve."),
    ("NE", "Hunter Henry", "TE", "", False, ""),
    ("NE", "Cameron Latu", "TE", "Questionable", False, ""),
    ("NE", "Drake Maye", "QB", "", False, ""),
    ("NE", "Morgan Moses", "T", "", False, ""),
    ("NE", "Walter Rouse", "T", "Questionable", True, ""),
    ("NE", "Brenden Schooler", "S", "Questionable", True, ""),
    ("NE", "Rhamondre Stevenson", "RB", "Questionable", False, ""),
    ("NE", "Greg Van Roten", "G", "Questionable", False, ""),
    ("NE", "Charles Woods", "CB", "Questionable", False, ""),
    # DET Lions - live report 9 rows
    ("DET", "Brian Branch", "S", "", False, ""),
    ("DET", "Jared Goff", "QB", "", False, ""),
    ("DET", "Kerby Joseph", "S", "Out", False, "Out on the report but absent from the inactive list; no reserve status is published on either page."),
    ("DET", "Cade Mays", "C", "Out", True, ""),
    ("DET", "D.J. Reed", "CB", "Out", True, ""),
    ("DET", "Jacob Saylors", "RB", "", False, ""),
    ("DET", "Amon-Ra St. Brown", "WR", "Questionable", False, ""),
    ("DET", "Sione Vaki", "RB", "Questionable", False, ""),
    ("DET", "DJ Wonnum", "DE", "", False, ""),
    # SEA Seahawks - live report 15 rows
    ("SEA", "AJ Barner", "TE", "", False, ""),
    ("SEA", "Anthony Bradford", "G", "", False, ""),
    ("SEA", "Charles Cross", "T", "Out", True, ""),
    ("SEA", "Sam Darnold", "QB", "Out", True, ""),
    ("SEA", "Derick Hall", "LB", "", False, ""),
    ("SEA", "Drew Lock", "QB", "", False, ""),
    ("SEA", "Quenton Nelson", "G", "Out", True, ""),
    ("SEA", "Uchenna Nwosu", "LB", "", False, ""),
    ("SEA", "Patrick O'Connell", "LB", "", False, ""),
    ("SEA", "Connor O'Toole", "LB", "", False, ""),
    ("SEA", "Brandon Pili", "DT", "", False, ""),
    ("SEA", "Jarran Reed", "DT", "", False, ""),
    ("SEA", "Rashid Shaheed", "WR", "", False, ""),
    ("SEA", "Jaxon Smith-Njigba", "WR", "", False, ""),
    ("SEA", "Leonard Williams", "DT", "Out", True, ""),
    # LV Raiders - live report 5 rows
    ("LV", "Thomas Booker", "DT", "Questionable", True, "Listed on the inactive list as Thomas Booker IV."),
    ("LV", "Foley Fatukasi", "DT", "", False, ""),
    ("LV", "Ian Thomas", "TE", "", False, ""),
    ("LV", "Dont'e Thornton Jr.", "WR", "Questionable", True, ""),
    ("LV", "Trey Zuhn III", "C", "", False, ""),
    # SF 49ers - live report 12 rows
    ("SF", "Mike Evans", "WR", "Out", True, ""),
    ("SF", "Renardo Green", "CB", "Questionable", False, ""),
    ("SF", "Dre Greenlaw", "LB", "Questionable", False, ""),
    ("SF", "Nate Hobbs", "CB", "Questionable", False, ""),
    ("SF", "Deommodore Lenoir", "CB", "Questionable", False, ""),
    ("SF", "Christian McCaffrey", "RB", "", False, ""),
    ("SF", "Siran Neal", "S", "", False, ""),
    ("SF", "Demarcus Robinson", "WR", "", False, ""),
    ("SF", "Deebo Samuel Sr.", "WR", "", False, ""),
    ("SF", "Upton Stout", "CB", "Questionable", False, ""),
    ("SF", "C.J. West", "DT", "Questionable", False, ""),
    ("SF", "Trent Williams", "T", "Questionable", False, ""),
    # DAL Cowboys - live report 19 rows
    ("DAL", "DaRon Bland", "CB", "Questionable", False, ""),
    ("DAL", "Jonathan Bullard", "DT", "Questionable", False, ""),
    ("DAL", "Alijah Clark", "S", "Questionable", False, ""),
    ("DAL", "Donovan Ezeiruaku", "LB", "Out", True, ""),
    ("DAL", "Jake Ferguson", "TE", "Out", True, ""),
    ("DAL", "Tyler Goodson", "RB", "Out", False, "Out on the report but absent from the inactive list; no reserve status is published on either page."),
    ("DAL", "Malik Hooker", "S", "", False, ""),
    ("DAL", "Marist Liufau", "LB", "", False, ""),
    ("DAL", "P.J. Locke", "S", "Out", True, ""),
    ("DAL", "Von Miller", "LB", "", False, ""),
    ("DAL", "Jonathan Mingo", "WR", "Out", True, ""),
    ("DAL", "Devin Moore", "CB", "Questionable", False, ""),
    ("DAL", "DeMarvion Overshown", "LB", "", False, ""),
    ("DAL", "George Pickens", "WR", "", False, ""),
    ("DAL", "Joey Porter Jr.", "CB", "Questionable", False, ""),
    ("DAL", "Luke Schoonmaker", "TE", "", False, ""),
    ("DAL", "Brevyn Spann-Ford", "TE", "", False, ""),
    ("DAL", "Juanyeh Thomas", "S", "Doubtful", True, ""),
    ("DAL", "KaVontae Turpin", "WR", "", False, ""),
    # PIT Steelers - live report 8 rows
    ("PIT", "Brandin Echols", "CB", "", False, ""),
    ("PIT", "DeShon Elliott", "S", "", True, "No game-status designation on the report, yet inactive."),
    ("PIT", "Derrick Harmon", "DT", "Questionable", False, ""),
    ("PIT", "Cameron Heyward", "DT", "", False, ""),
    ("PIT", "Ben Skowronek", "WR", "", False, ""),
    ("PIT", "Doneiko Slaughter", "CB", "", False, ""),
    ("PIT", "Darnell Washington", "TE", "", False, ""),
    ("PIT", "T.J. Watt", "LB", "", False, ""),
    # CIN Bengals - live report 9 rows
    ("CIN", "Jonathan Allen", "DT", "", False, ""),
    ("CIN", "Jalen Davis", "CB", "Doubtful", False, ""),
    ("CIN", "Kyle Dugger", "S", "Out", True, ""),
    ("CIN", "Dylan Fairchild", "G", "", False, ""),
    ("CIN", "B.J. Hill", "DT", "", False, ""),
    ("CIN", "Andrei Iosivas", "WR", "Doubtful", False, ""),
    ("CIN", "Dexter Lawrence", "DT", "", False, ""),
    ("CIN", "Brian Parker II", "G", "Doubtful", False, ""),
    ("CIN", "DJ Turner II", "CB", "", False, ""),
]

# Inactive players who do not appear anywhere on the injury report, per club.
INACTIVE_NOT_ON_REPORT = [
    ("NE", ["Dametrious Crownover", "Behren Morton (emergency third QB)"]),
    ("DET", ["Keith Abney II", "Ahmed Hassanein", "Amen Ogbongbemiga", "Mekhi Wingo"]),
    ("SEA", ["Emanuel Wilson", "Avery Smith", "Deven Eastern"]),
    ("LV", ["Malik Benson", "Tristin McCollum", "Dalton Johnson", "Bryce Cabeldue"]),
    ("SF", ["Kurtis Rourke", "Enrique Cruz Jr.", "Tatum Bethune", "Brandin Cooks"]),
    ("DAL", ["Derion Kendrick", "Ajani Cornelius"]),
    ("PIT", ["Drew Allar", "Will Howard (emergency third QB)", "Sean Murphy-Bunting", "Eli Heidenreich"]),
    ("CIN", ["Connor Lew", "Myles Hinton", "Landon Robinson"]),
]

# --------------------------------------------------------------------------
# Live (2026-11-16) vs committed capture (2026-11-13) differences on S1.
# --------------------------------------------------------------------------
CAPTURE_DELTA = [
    dict(team="DET", subject="Amon-Ra St. Brown (WR)", field="Injuries / Game Status",
         captured="(blank) / (blank)", live="Rib / Questionable",
         note="Practice status unchanged (Limited Participation in Practice)."),
    dict(team="DET", subject="Sione Vaki (RB)", field="Injuries / Practice Status / Game Status",
         captured="(blank) / Did Not Participate In Practice / (blank)",
         live="Ankle / Limited Participation in Practice / Questionable",
         note="A practice-status upgrade and a new game designation between the two reads."),
    dict(team="BAL", subject="Calais Campbell (DT)", field="Row presence",
         captured="Row absent", live="Row present: Did Not Participate In Practice, no game status",
         note="A player appeared on the report after the 2026-11-13 capture."),
    dict(team="BAL", subject="Ronnie Stanley (T)", field="Row presence",
         captured="Row absent", live="Row present: Did Not Participate In Practice, no game status",
         note="A player appeared on the report after the 2026-11-13 capture."),
    dict(team="(league-wide)", subject="Doubtful designations", field="Game Status values present",
         captured="0 rows with a Doubtful designation",
         live="Doubtful present, e.g. ATL Divine Deablo, GB Zaire Franklin, BUF Spencer Brown, "
              "MIA Chris Bell, CAR Jonathon Brooks, CAR Mike Jackson, DAL Juanyeh Thomas, "
              "CIN Jalen Davis, CIN Andrei Iosivas, CIN Brian Parker II, LAC Brenen Thompson",
         note="The 2026-11-13 capture predates the Friday/Saturday designations."),
    dict(team="(league-wide)", subject="Club records in the fixture headers", field="Record cell",
         captured="Pre-game records (e.g. NE 5-4, DET 6-2, KC 6-2)",
         live="Post-game records (e.g. NE 5-5, DET 7-2, KC 7-2)",
         note="The page keeps the Week 10 tables up after the games while it still says Week 10."),
]

# --------------------------------------------------------------------------
# Information HAVE / DON'T-HAVE register.
# --------------------------------------------------------------------------
GAPS = [
    dict(domain="Injury designations (all 32 clubs)",
         have="326 rows across 28 clubs and 14 fixtures, with Player / Position / Injuries / "
              "Practice Status / Game Status, captured 2026-11-13, sha256 recorded. "
              "Counts: 301 blank game status, 14 Out, 11 Questionable, 0 Doubtful.",
         src="S8",
         missing="The 2026-11-16 live values are only transcribed for the 8 clubs listed on the "
                 "designation-join page; the other 20 clubs were read but not transcribed.",
         blocks="Q01, Q02, SG-D"),
    dict(domain="Intra-week designation history (Wed/Thu/Fri)",
         have="Two time points: 2026-11-13 (committed capture) and 2026-11-16 (live read).",
         src="S8, S1",
         missing="Wednesday and Thursday captures. The brief asks for Wed + Thu + Fri plus kickoff; "
                 "two points is a delta, not a series.",
         blocks="Q12, F12, SG-A"),
    dict(domain="Official inactive lists",
         have="147 entries across 24 clubs for the 12 Sunday/Munich Week 10 games.",
         src="S4",
         missing="Thursday (WAS/NYG) and Monday (LAC/BAL) inactive lists were not published by S4 "
                 "and were not located elsewhere; no prior-season archive.",
         blocks="Q01, Q02, SG-A"),
    dict(domain="Reserve / injured-reserve list membership",
         have="The official November 2026 page lists 25 dated Reserve/Injured moves, including Malik "
              "Willis (MIA, 11/10), TreVeyon Henderson (NE, 11/14) and Tyler Goodson (DAL, 11/14). "
              "The nfl-collector namespace has a 25-row structured capture and ledger hash.",
         src="S10, S17",
         missing="This decision-gaps namespace still uses its static November transcription and does "
                 "not consume the collector capture automatically; cross-week membership joins remain open.",
         blocks="Q05, F3, F14, SG-E"),
    dict(domain="League depth charts",
         have="Confirmed absent: https://www.nfl.com/teams/baltimore-ravens/depth-chart returns 404 "
              "and the club page's tabs are Info / Roster / Stats.",
         src="S2, S3",
         missing="nfl.com publishes no depth chart at any path found this session. Clubs publish on "
                 "their own domains (e.g. baltimoreravens.com), which were not read.",
         blocks="Q06, F5, SG-C"),
    dict(domain="Snap counts",
         have="", src="S3, S5, S6, S7",
         missing="No snap-count table found on the club page, the Game Center, the schedule page or "
                 "the scores page. A gamebook PDF route is reported on third-party forums; it was "
                 "not retrieved, so nothing is asserted.",
         blocks="Q07, F7, SG-C"),
    dict(domain="Announced starters (first-snap offence/defence)",
         have="", src="S5",
         missing="The Game Center tabs read (INFO / OVERVIEW / STATS / STREAMS) publish no starters "
                 "list and no game-day status beyond the injury cards.",
         blocks="Q08, F7"),
    dict(domain="Venue per fixture",
         have="14 of 14 Week 10 venues: 12 from the official inactives article, 1 (LAC/BAL) from "
              "its Game Center, and 1 (WAS/NYG) from its Game Center.",
         src="S4, S5, S14",
         missing="",
         blocks="None for Week 10; retain fixture-level venue capture for future weeks."),
    dict(domain="Stadium roof / surface designation",
         have="", src="S5, S6",
         missing="The Game Center Game Info block publishes Location, Stadium and Network only - no "
                 "roof designation, no surface, no 90-minute designation.",
         blocks="Q09, F8"),
    dict(domain="Weather (wind / precipitation)",
         have="The schedule page carries a summary weather chip for the upcoming game "
              "('Weather Clearnight').",
         src="S6",
         missing="No wind speed, no precipitation, no hourly grid on any official page read. The "
                 "brief's NWS overlay is outside the official domain entirely.",
         blocks="Q09, F8"),
    dict(domain="Schedule / fixture context",
         have="Official Week 10 schedule, the current Week 11 listing (Colts at Texans, Nov 19), "
              "and the dated May 8 NFL announcement that the full 2026 schedule would be released "
              "May 14. The announcement and live weekly schedule are linked together on the results page.",
         src="S11, S15, S16",
         missing="",
         blocks="None for Q15; keep live schedule reads dated and source-linked."),
    dict(domain="Verified results feed",
         have="13 of 14 Week 10 fixtures show Final with scores on the current official NFL schedule "
              "and scores pages; PIT-CIN is additionally confirmed by its Game Center (18-38).",
         src="S11, S12, S13",
         missing="LAC/BAL is still listed as Scheduled on the current official pages; no Final state "
                 "or score is shown. No prior-season results corpus was read this session.",
         blocks="Q14, F15, SG-G"),
    dict(domain="Market prices (open / close / moneyline)",
         have="No official price found. The Game Center, schedule, scores and club pages publish no "
              "spread, total or moneyline.",
         src="S3, S5, S6, S7",
         missing="An authorised price source. Without one, originated-line residuals, CLV and ROI "
                 "are undefined and must stay blank.",
         blocks="Q10, Q16, F6, SG-B"),
    dict(domain="Player-prop markets",
         have="", src="S3, S5, S6, S7",
         missing="Nothing official. Same blocker as market prices.",
         blocks="Q18, SG-N"),
    dict(domain="Dated transactions / roster events",
         have="The league transactions hub publishes Trades, Signings, Reserve List, Waivers, "
              "Terminations and Other by year and month. For November 2026, nfl-collector has "
              "structured, ledger-hashed captures of 12 trades and 25 reserve-list moves.",
         src="S9, S10, S17, S18",
         missing="The other four categories (Signings, Waivers, Terminations, Other) are not captured, "
                 "and the existing captures are not yet joined to availability or depth rows. A "
                 "multi-month roster-event history still needs validation.",
         blocks="Q20, SG-E"),
    dict(domain="Team and player statistics",
         have="nfl.com publishes team and player stats; the Game Center carries a regular-season "
              "glance (points per game, yards per game, time of possession, sacks, interceptions, "
              "turnover differential) and club leaders.",
         src="S3, S5",
         missing="No opponent-adjusted rating was computed this session.",
         blocks="SG-L, SG-M"),
]

# --------------------------------------------------------------------------
# Open-questions register.
# --------------------------------------------------------------------------
QUESTIONS = [
    dict(id="Q01", topic="Availability",
         question="What fraction of officially inactive players appear on the NFL injury report at all?",
         have="Measured on the 8 clubs where every live row was read and joined to the official "
              "inactive list: 26 of 46 inactive players (56.5%) do not appear on the injury report "
              "in any form. Excluding the two emergency third quarterbacks, 24 of 44 (54.5%).",
         src="S1, S4",
         missing="The other 16 clubs of Week 10, and every prior week.",
         clears="The same join computed for all 32 clubs and at least one full season, with the "
                "denominator published and the emergency-third-QB rows separated out.",
         discovery="SG-D",
         status="answered, bounded (n = 8 clubs, 46 inactives)"),
    dict(id="Q02", topic="Availability",
         question="What does 'Questionable' mean empirically?",
         have="On the 8 joined clubs, 4 of 26 players carrying a Questionable designation were "
              "inactive (15.4%).",
         src="S1, S4",
         missing="A usable sample. n = 26 in one week is far too small, and one club (LV) went 2 for 2.",
         clears="Several seasons of designations joined to the official inactive lists, with a "
                "confidence interval and a club-clustered standard error.",
         discovery="SG-A",
         status="open"),
    dict(id="Q03", topic="Availability",
         question="What does 'Doubtful' mean empirically?",
         have="1 of 4 Doubtful players on the joined clubs was inactive (25%).",
         src="S1, S4",
         missing="n = 4. The brief asks for a calibrated probability with a confidence interval; "
                 "this cannot support one.",
         clears="n >= 200 Doubtful designations joined to inactive lists across seasons.",
         discovery="SG-A",
         status="open"),
    dict(id="Q04", topic="Availability",
         question="Does an 'Out' designation guarantee the player is inactive?",
         have="No. Of 17 Out players on the joined clubs, 14 were inactive and 2 more were placed on "
              "the official reserve list during the week (TreVeyon Henderson, NE, 11/14; Tyler Goodson, "
              "DAL, 11/14). Three official records (injury report, inactive lists, reserve list) explain "
              "16 of 17 (94.1%); Kerby Joseph (DET) remains unexplained.",
         src="S1, S4, S10",
         missing="An explanation for Kerby Joseph: Out on the injury report, absent from the Week 10 "
                 "inactive list, and absent from the November 2026 reserve list.",
         clears="The reserve list captured as a dated field of the weekly snapshot, so an Out player "
                 "who went on IR is separated from an Out player who was expected to be inactive.",
         discovery="SG-E",
         status="answered for 16 of 17; one case flagged (F3)"),
    dict(id="Q05", topic="Availability",
         question="Which players are on a reserve list and therefore absent from the weekly report?",
         have="The official November 2026 page lists 25 dated Reserve/Injured moves, including Malik "
              "Willis (MIA, 11/10); the nfl-collector capture contains the same month's 25 structured "
              "rows and a ledger hash.",
         src="S10, S17",
         missing="The decision-gaps build does not yet consume the collector capture automatically, "
                 "and the capture does not establish membership across other months or seasons.",
         clears="Integrate the existing 25-row hashed capture into this namespace's weekly join, then "
                "validate reserve/inactive/designation joins across the registered time window.",
         discovery="SG-E",
         status="answered for November capture; cross-namespace and longitudinal join open"),
    dict(id="Q06", topic="Depth",
         question="Does the league publish depth charts?",
         have="No. https://www.nfl.com/teams/baltimore-ravens/depth-chart returns the official 404 "
              "page, and the club page's only sections are Info, Roster and Stats.",
         src="S2, S3",
         missing="Nothing - this one is settled for nfl.com. The open part is whether the 32 club "
                 "domains publish them in a parseable form.",
         clears="A club-by-club read of all 32 official club sites, each with a URL, a date and a "
                "parser that survives the 'published as an image' failure mode.",
         discovery="SG-C",
         status="answered for nfl.com; open for the 32 club sites"),
    dict(id="Q07", topic="Depth",
         question="Is there an official snap-count source?",
         have="", src="S3, S5, S6, S7",
         missing="Not found on any official page read this session (club page, Game Center, schedule, "
                 "scores). A gamebook-PDF route is described on third-party forums; it was not "
                 "retrieved, so no claim is made.",
         clears="One official gamebook retrieved and parsed end-to-end, with the snap-count page "
                "located and its URL published.",
         discovery="SG-C",
         status="open"),
    dict(id="Q08", topic="Depth",
         question="Does the Game Center publish announced starters and game-day status?",
         have="", src="S5",
         missing="The Game Center tabs read (INFO / OVERVIEW / STATS / STREAMS) publish no starters "
                 "list, only team statistics, club leaders and injury cards.",
         clears="A page or endpoint on the official domain that lists first-snap offence and defence.",
         discovery="SG-C",
         status="open"),
    dict(id="Q09", topic="Environment",
         question="Does the league publish a stadium roof designation and weather?",
         have="Game Info publishes Location and Stadium only. The schedule page carries a summary "
              "weather chip for the upcoming game ('Weather Clearnight').",
         src="S5",
         missing="Roof designation, surface, wind speed, precipitation. The brief's NWS grid is a "
                 "different (non-NFL) domain and was not read.",
         clears="A published roof/surface field per stadium plus an NWS grid URL per venue, both "
                 "captured with a timestamp.",
         discovery="SG-J",
         status="open"),
    dict(id="Q10", topic="Prices",
         question="Where does an authorised price come from?",
         have="No official price exists. The Game Center, schedule, scores and club pages publish no "
              "spread, total or moneyline.",
         src="S3, S5, S6, S7",
         missing="Everything.",
         clears="A written price-data policy: which source, under what terms, with what retention, "
                 "signed off before any backtest is published.",
         discovery="SG-B",
         status="blocking - no residual, CLV or ROI can be computed until this is answered"),
    dict(id="Q11", topic="Repository",
         question="Why do three different row counts for the same injury page exist in this repo?",
         have="Sessions have published 254, 279 and 347 rows for this page. This session's parse of "
              "the committed 2026-11-13 capture gives 326 rows over 28 clubs; the live 2026-11-16 "
              "page differs from that capture again.",
         src="S8, S1",
         missing="Which quantity each published number counts (report rows, injury entries, players, "
                 "clubs, or rows in some other namespace's derived table).",
         clears="One canonical capture file, one parser, and every count computed at build time from "
                 "that file, with no count typed into prose.",
         discovery="SG-H",
         status="open - flagged"),
    dict(id="Q12", topic="Availability",
         question="How much does the report move inside a week?",
         have="Proven to move: between 2026-11-13 and 2026-11-16 the Lions' St. Brown and Vaki rows "
              "changed, two Ravens rows appeared, Doubtful designations appeared where there had "
              "been none, and the club records in the headers were replaced with post-game records.",
         src="S8, S1",
         missing="Wednesday and Thursday reads, so the DNP to LP to FP path cannot be reconstructed.",
         clears="Captures on Wednesday, Thursday, Friday and at kickoff, each hashed, so the "
                 "designation path is replayable.",
         discovery="SG-A",
         status="answered in kind; the series is still too short"),
    dict(id="Q13", topic="Fixtures",
         question="Is the venue of every fixture transcribed from the official game centre?",
         have="14 of 14 Week 10 venues are recorded from official pages: 12 from the inactives article, "
              "LAC/BAL from its Game Center, and WAS/NYG from its Game Center.",
         src="S4, S5, S14",
         missing="",
         clears="Cleared for Week 10: 14/14 official venue records.",
         discovery="SG-F",
         status="answered for Week 10"),
    dict(id="Q14", topic="Results",
         question="Is the Week 10 results feed complete?",
         have="13 of 14 fixtures show Final with scores on the current official schedule and scores "
              "pages. PIT/CIN is confirmed at 18-38 by its Game Center; LAC/BAL is still listed as "
              "Scheduled in the current reads, with no score shown.",
         src="S11, S12, S13",
         missing="LAC/BAL Final state and score. The current official schedule and scores pages list "
                 "Monday, Nov 16 at 8:15 PM ET but show no Final state or score.",
         clears="A current official NFL result page must report Final and both numeric scores; then "
                "the consistency verifier must pass for all 14 fixtures.",
         discovery="SG-G",
         status="open - 13/14 final; 1 still listed as scheduled"),
    dict(id="Q15", topic="Fixtures",
         question="Is the league's dated schedule announcement published beside the live schedule?",
         have="Yes. The official May 8 announcement states the full 2026 schedule release date (May 14); "
              "the live Week 10 and Week 11 schedule pages are now cited alongside it.",
         src="S11, S15, S16",
         missing="",
         clears="Cleared: one dated announcement plus the current Week 10 and Week 11 schedule pages.",
         discovery="SG-J",
         status="answered"),
    dict(id="Q16", topic="Origination",
         question="What is the correlation between the originated side, total and moneyline residuals?",
         have="", src="S3, S5, S6, S7",
         missing="A price. With no market line there is no residual, so there is nothing to correlate.",
         clears="Q10 first, then at least a season of paired (own line, market line) observations "
                "with n published next to every coefficient.",
         discovery="SG-B",
         status="blocked by Q10"),
    dict(id="Q17", topic="Governance",
         question="What minimum n makes a strategy reward-eligible?",
         have="", src="repo",
         missing="One owner decision. This repository currently carries competing gates, including "
                 "'n >= 300 graded games' against a largest corpus of 77 games.",
         clears="A single written gate with a number, committed before the evaluation window opens.",
         discovery="SG-L",
         status="open - owner decision"),
    dict(id="Q18", topic="Governance",
         question="Can a parlay or same-game-parlay combination ever be ranked?",
         have="", src="repo",
         missing="A directly validated joint probability and the operator's void/push rules. "
                 "Multiplying marginals is invalid under dependence.",
         clears="A joint-evidence gate backed by an estimated dependence structure on official "
                 "results, or a standing refusal to rank combinations at all.",
         discovery="SG-N",
         status="blocked - refuse until a joint model exists"),
    dict(id="Q19", topic="Governance",
         question="Has any pre-registered strategy produced a prospective record?",
         have="", src="repo",
         missing="A strategy committed before its window opened, together with official results "
                 "inside that window.",
         clears="Registration commit hash + frozen rule text + a results feed that starts after it.",
         discovery="SG-L",
         status="open"),
    dict(id="Q20", topic="Rosters",
         question="Can roster turnover be versioned against the last official roster event?",
         have="Partly. The league hub publishes six monthly categories; nfl-collector has dated, "
              "ledger-hashed November captures for 12 trades and 25 reserve-list moves.",
         src="S9, S10, S17, S18",
         missing="Signings, Waivers, Terminations and Other are not yet captured, and neither existing "
                 "category is joined to each availability/depth row as its last affecting roster event. "
                 "The longitudinal event-to-player join also needs validation.",
         clears="Capture the remaining four categories, retain the hashed trades and reserve records, "
                "then integrate all six categories into a tested event-to-player adapter that stamps "
                "the latest relevant roster event on each affected record.",
         discovery="SG-E",
         status="open - two categories captured; four and event-to-row integration remain"),
]

# --------------------------------------------------------------------------
# Suggestions review board.  `verdict` is deliberately blank: choosing a path
# is the reviewer's decision, not the model's.
# --------------------------------------------------------------------------
SUGGESTIONS = [
    dict(id="SG-A", title="Run a scheduled, hashed official capture (Wed / Thu / Fri / kickoff)",
         why="The whole availability feature depends on being able to replay what was known before "
             "kickoff. Today there are two time points this season and no Wednesday or Thursday.",
         options=[
             dict(label="A", text="Collect nfl.com pages only (injuries, inactives article, schedule, "
                                  "scores, transactions, game centres). Four captures a week, sha256 "
                                  "per capture, drift alarm on row counts and required fields.",
                  effort="Low", risk="Low - official domain, no terms question",
                  tradeoff="Cheapest and safest, but leaves the depth question (Q06/Q07) unanswered."),
             dict(label="B", text="Option A plus the 32 official club sites for depth charts and "
                                  "transactions.",
                  effort="High", risk="Medium - 32 parsers, one of which (the Texans) publishes an image",
                  tradeoff="Closes the depth gap if the pages are parseable; high maintenance."),
             dict(label="C", text="Option A plus a licensed data feed that carries depth, snaps and "
                                  "prices under a read licence.",
                  effort="Low once licensed", risk="Medium - the price-data policy (SG-B) must be decided first",
                  tradeoff="Fastest route to a full feature set; costs money and imposes terms."),
         ],
         dependency="None to start option A.",
         recommended="A now, and do not start B or C until the sample from A has been read.",
         src="S1, S8",
         verdict=""),
    dict(id="SG-B", title="Decide the price-data policy before any backtest is published",
         why="No official page publishes a spread, total or moneyline. Every residual, CLV and ROI "
             "number in this repository is therefore undefined until a source and its terms are chosen.",
         options=[
             dict(label="A", text="Publish no price at all. Ship the model's fair line as a "
                                  "probability with its inputs and no market comparison.",
                  effort="None", risk="None",
                  tradeoff="Honest and immediate, but the brief's 'residual against the market' and "
                           "CLV leaderboard cannot exist."),
             dict(label="B", text="Ingest one licensed odds source, terms read and recorded, with "
                                  "open and close captured on a schedule.",
                  effort="Medium", risk="Medium - single-vendor dependence and a retention obligation",
                  tradeoff="Unblocks residuals and CLV; every derived number inherits one vendor's "
                           "definition of 'close'."),
             dict(label="C", text="Ingest several sources and publish a vig-free consensus with the "
                                  "operator margin decomposed out.",
                  effort="High", risk="Medium - consensus construction must be pre-registered",
                  tradeoff="Best separation of origination alpha from vig; slowest to stand up."),
         ],
         dependency="Blocks Q10 and Q16, and every leaderboard column that uses a market price.",
         recommended="A as the default today, with B or C chosen by the owner before any CLV claim.",
         src="S3, S5, S6, S7",
         verdict=""),
    dict(id="SG-C", title="Resolve the depth-order source before building the deficiency feature",
         why="The brief asks for 2nd/3rd/4th-string replacements. nfl.com publishes no depth chart "
             "(404) and no snap counts were found, so the feature currently has no input.",
         options=[
             dict(label="A", text="Per-club official depth pages, verified club by club, with a "
                                  "parser that records shared and empty slots faithfully.",
                  effort="High", risk="Medium - the Texans publish an image; jersey numbers must be stripped",
                  tradeoff="Direct answer if all 32 cooperate; dead ends if some publish images."),
             dict(label="B", text="Derive depth from snap counts using the official gamebook, once "
                                  "one has actually been retrieved and parsed.",
                  effort="Medium", risk="Medium - availability lag, and snaps measure the past",
                  tradeoff="Measurable starter/backup split; cannot name a replacement before kickoff."),
             dict(label="C", text="Build nothing until one route is verified for all 32 clubs.",
                  effort="None", risk="None",
                  tradeoff="Avoids fabricating a starter the club never named; leaves the feature absent."),
         ],
         dependency="Q06, Q07, Q08.",
         recommended="C is the safe default; B is the better bet if a gamebook can be retrieved.",
         src="S2, S3",
         verdict=""),
    dict(id="SG-D", title="Transcribe the full live injury report into the repository",
         why="This session read the whole live page but only transcribed 8 of 28 clubs. The "
             "inactive-coverage finding (Q01) rests on 46 inactives; it should rest on all of them.",
         options=[
             dict(label="A", text="Transcribe all 28 clubs for Week 10 and recompute the join.",
                  effort="Medium", risk="Low",
                  tradeoff="Triples the sample for one week; still one week."),
             dict(label="B", text="Option A plus an automated fetch-and-parse step so future weeks "
                                  "need no transcription.",
                  effort="High", risk="Medium - needs the drift alarm from SG-A",
                  tradeoff="The only route to a multi-season sample."),
         ],
         dependency="None.",
         recommended="B, but only inside the SG-A collector.",
         src="S1, S4",
         verdict=""),
    dict(id="SG-E", title="Join the existing reserve/trades captures and expand transaction coverage",
         why="The official November reserve list and trades already have dated, hashed captures in "
             "nfl-collector. This namespace still does not consume those records; the remaining "
             "transaction categories (signings, waivers, terminations, other) are not yet joined into "
             "a shared roster-event graph.",
         options=[
             dict(label="A", text="Wire the existing reserve-list and trades captures into this "
                                  "namespace's availability join, preserving the collector's capture "
                                  "time, source URL and hashes; do not duplicate the parser.",
                  effort="Low", risk="Low",
                  tradeoff="Closes the local integration gap with two already-captured categories; "
                           "does not add the other four."),
             dict(label="B", text="Option A plus daily captures for Signings, Waivers, Terminations "
                                  "and Other, with the last roster event stamped onto every affected "
                                  "availability/depth record.",
                  effort="Medium", risk="Low",
                  tradeoff="Completes the six-category event graph; expands collector coverage and "
                           "requires more drift expectations."),
         ],
         dependency="The nfl-collector capture ledger and a tested adapter between namespaces.",
         recommended="A for this namespace; B only after the shared event schema is reviewed.",
         src="S9, S10, S17, S18, S1, S4",
         verdict=""),
    dict(id="SG-F", title="Keep the venue register complete for every fixture",
         why="The Week 10 register is now complete at 14/14, including WAS/NYG from its official "
             "Game Center. That closes this week's gap but does not enforce venue coverage for "
             "future slates.",
         options=[
             dict(label="A", text="For each refresh, record Location and Stadium from an official "
                                  "Game Center for any fixture not covered by a league inactives page.",
                  effort="Trivial", risk="None",
                  tradeoff="Preserves completeness by manual review; does not enforce it."),
             dict(label="B", text="Make venue a required field of every fixture record and fail the "
                                  "build when a venue or official source is missing.",
                  effort="Low", risk="Low",
                  tradeoff="Prevents the gap from recurring."),
         ],
         dependency="None.",
         recommended="A completed for Week 10; B is the durable safeguard.",
         src="S4, S5, S14",
         verdict=""),
    dict(id="SG-G", title="Automate a freshness re-read for scheduled fixtures",
         why="The 2026-11-16 PIT-CIN pages showed an intermediate LIVE state; the 2026-11-17 official "
             "schedule, scores and Game Center reads later showed Final, 18-38. This session adds a "
             "deterministic build-time check that rejects scores inconsistent with result state/source. "
             "Automated re-reads and an immutable fetch ledger remain unimplemented here.",
         options=[
             dict(label="A", text="Keep the build-time gate: Final requires both numeric scores and "
                                  "official result-source IDs; non-Final states must have blank scores. "
                                  "Manually re-read unresolved fixtures before publishing.",
                  effort="Low", risk="None",
                  tradeoff="The invariant is now enforced, but a scheduled fixture still needs a fresh read."),
             dict(label="B", text="Option A plus a scheduled re-read of unresolved official fixtures, "
                                  "recording a timestamped state transition and clearing a flag only "
                                  "when an official source reports Final.",
                  effort="Medium", risk="Low",
                  tradeoff="Self-healing and auditable; requires a collector job and immutable snapshots."),
         ],
         dependency="The build-time state/source consistency check is implemented; scheduled capture is not.",
         recommended="B.",
         src="S6, S7, S11, S12, S13",
         verdict=""),
    dict(id="SG-H", title="One canonical count, computed at build time, never typed into prose",
         why="Three sessions published 254, 279 and 347 rows for the same page, and a fourth "
             "published 326. Counts written by hand go stale the moment a sibling merges.",
         options=[
             dict(label="A", text="Pin one capture file, compute every count from it, and fail the "
                                  "build if a page contains a count that is not produced by the parser.",
                  effort="Medium", risk="Low",
                  tradeoff="Settles the discrepancy; requires touching pages that already type a number."),
             dict(label="B", text="Option A plus a single shared register page that every namespace "
                                  "links to instead of repeating the number.",
                  effort="Medium-high", risk="Low",
                  tradeoff="Removes the duplication that created the divergence."),
         ],
         dependency="The integration session, because it changes shared outputs.",
         recommended="A now, B at the next integration.",
         src="S8, S1",
         verdict=""),
    dict(id="SG-I", title="Consolidate the duplicated nfl-* namespaces into one canonical set",
         why="Many namespaces independently publish questions, suggestions and review pages. "
             "Contradictory numbers are already present; a canonical path would reduce repeated drift.",
         options=[
             dict(label="A", text="Freeze new namespaces and mark one canonical namespace per domain.",
                  effort="Low", risk="Low",
                  tradeoff="Stops the bleeding without deleting anyone's work."),
             dict(label="B", text="Merge the canonical namespaces and keep the rest as archived "
                                  "research records, linked but not navigated.",
                  effort="High", risk="Medium - touches shared navigation",
                  tradeoff="A site a reviewer can actually use; needs an integration session."),
         ],
         dependency="The integration session.",
         recommended="A immediately, B at the next integration.",
         src="repo",
         verdict=""),
    dict(id="SG-J", title="Capture roof, surface and weather per venue from published sources",
         why="Totals and passing props misprice when a dome is assumed outdoors or a windy open "
             "stadium is assumed calm. The official pages read this session publish neither.",
         options=[
             dict(label="A", text="Record the stadium and city from the Game Center for every "
                                  "fixture, and mark roof and surface blank until a source is found.",
                  effort="Low", risk="Low",
                  tradeoff="Honest, and builds the venue spine the overlay would hang on."),
             dict(label="B", text="Option A plus an NWS grid capture per venue and an official "
                                  "roof/surface field where the league publishes one.",
                  effort="High", risk="Medium - mixes two domains and two timestamps",
                  tradeoff="Enables the overlay; needs the timestamp discipline of SG-A."),
         ],
         dependency="SG-A.",
         recommended="A now; B only if the roof designation is actually published somewhere.",
         src="S5, S6",
         verdict=""),
    dict(id="SG-K", title="Put a control baseline on every leaderboard run",
         why="Without a random-pick and a favourites-only column, a good week is indistinguishable "
             "from a good model.",
         options=[
             dict(label="A", text="Publish random and favourites-only baselines beside every "
                                  "strategy, with the same n and the same proper score.",
                  effort="Low", risk="None",
                  tradeoff="Needs a favourites definition; with no official price, 'favourite' must "
                           "be defined from the model, not the market."),
         ],
         dependency="A defined benchmark (see SG-B option A).",
         recommended="A.",
         src="repo",
         verdict=""),
    dict(id="SG-L", title="Pre-register each strategy: rule text, window and gates, committed first",
         why="The commit hash is the registration. Without it, any leaderboard result can be "
             "accused - correctly - of being chosen after the fact.",
         options=[
             dict(label="A", text="A registration file per strategy: frozen rule text, sample window, "
                                  "gates, and the commit hash, created before the window opens.",
                  effort="Low", risk="None",
                  tradeoff="Requires discipline; no cost otherwise."),
             dict(label="B", text="Option A plus a gate that refuses to rank any strategy whose "
                                  "registration commit predates its first graded result.",
                  effort="Medium", risk="Low",
                  tradeoff="Makes the rule enforceable rather than aspirational."),
         ],
         dependency="None.",
         recommended="B.",
         src="repo",
         verdict=""),
    dict(id="SG-M", title="Split train, validation and final holdout by season",
         why="Out-of-sample testing is the only thing that separates a model from a curve fit.",
         options=[
             dict(label="A", text="Fix the split by season, publish which seasons are in which fold, "
                                  "and forbid touching the final holdout until the model is frozen.",
                  effort="Low", risk="None",
                  tradeoff="Costs sample size in the short run."),
         ],
         dependency="A results corpus (SG-G plus the past-season archive).",
         recommended="A.",
         src="repo",
         verdict=""),
    dict(id="SG-N", title="Keep parlays and prop combos behind a joint-evidence gate",
         why="Multiplying marginal probabilities is invalid under dependence. Until a joint "
             "probability is validated on official results, a combination must not be ranked.",
         options=[
             dict(label="A", text="Rank singles only, and publish the combination gate as unmet.",
                  effort="None", risk="None",
                  tradeoff="Removes a whole product category until the evidence exists."),
             dict(label="B", text="Estimate a dependence structure on official results and publish "
                                  "the joint probability with its uncertainty before ranking anything.",
                  effort="High", risk="High - dependence estimates need a large sample",
                  tradeoff="The only route to ranking combinations honestly."),
         ],
         dependency="Q10, Q18 and a multi-season results corpus.",
         recommended="A until the corpus exists.",
         src="repo",
         verdict=""),
    dict(id="SG-O", title="Publish n beside every correlation and every rate",
         why="A correlation without its n is not a number. The designation rates on this site are "
             "published with n = 26 and n = 4 precisely so they cannot be mistaken for settled facts.",
         options=[
             dict(label="A", text="Make n a required column on every correlation and rate table, and "
                                  "fail the build when it is missing.",
                  effort="Low", risk="None",
                  tradeoff="None."),
         ],
         dependency="None.",
         recommended="A.",
         src="S1, S4",
         verdict=""),
]

# --------------------------------------------------------------------------
# Flagged for review.
# --------------------------------------------------------------------------
FLAGS = [
    dict(id="F1", sev="low", area="Results",
         item="Resolved: PIT at CIN final verified; prior LIVE rendering retained as a historical anomaly",
         detail="The 2026-11-17 official Week 10 schedule and scores pages, plus the PIT-CIN Game Center, "
                "show Steelers 18, Bengals 38, Final. On 2026-11-16 the official schedule and scores "
                "reads had rendered LIVE, Q1 08:56, PIT 0-CIN 3. That earlier state is retained as "
                "historical evidence only; the published final is sourced to the later Final reads. "
                "No explanation for the earlier state is inferred.",
         status="resolved — historical anomaly retained",
         src="S6, S7, S11, S12, S13"),
    dict(id="F2", sev="high", area="Repository",
         item="Three incompatible row counts published for the same injury page",
         detail="Earlier sessions published 254, 279 and 347 rows for the Week 10 nfl.com injury "
                "report. This session's parse of the committed 2026-11-13 capture returns 326 rows "
                "over 28 clubs, and the live 2026-11-16 page differs from that capture again. Which "
                "quantity each earlier number counts is not stated, so they cannot be reconciled.",
         src="S8, S1"),
    dict(id="F3", sev="medium", area="Availability",
         item="One Out player neither the inactive list nor the reserve list explains",
         detail="TreVeyon Henderson (NE) and Tyler Goodson (DAL) carried an Out designation while "
                "absent from the Week 10 inactive list; the official reserve list now explains both "
                "(Reserve/Injured, 11/14). Kerby Joseph (DET) remains unaccounted for: Out on the "
                "injury report, absent from the inactive list, and absent from the November 2026 "
                "reserve list. No official page read this session states why.",
         src="S1, S4, S10"),
    dict(id="F4", sev="high", area="Availability",
         item="56.5% of inactive players are absent from the injury report",
         detail="On the eight clubs where every live row was read and joined to the official "
                "inactive list, 26 of 46 inactive players (24 of 44 excluding emergency third "
                "quarterbacks) do not appear on the injury report in any form. The injury report "
                "alone therefore cannot establish who is unavailable.",
         src="S1, S4"),
    dict(id="F5", sev="high", area="Depth",
         item="nfl.com publishes no depth chart",
         detail="https://www.nfl.com/teams/baltimore-ravens/depth-chart returns the official 404 "
                "page and the club page offers only Info, Roster and Stats. The brief's "
                "'club depth pages' therefore cannot be satisfied from nfl.com; the 32 club domains "
                "were not read this session.",
         src="S2, S3"),
    dict(id="F6", sev="high", area="Prices",
         item="No official price source exists",
         detail="No spread, total or moneyline was found on the Game Center, the schedule page, the "
                "scores page or the club page. Every residual, CLV and ROI figure must stay blank "
                "until the price-data policy is decided.",
         src="S3, S5, S6, S7"),
    dict(id="F7", sev="medium", area="Depth",
         item="Snap counts and announced starters not found",
         detail="Neither a snap-count table nor a starters list was found on any official page read "
                "this session. A gamebook-PDF route is described on third-party forums; it was not "
                "retrieved, so no claim is made about it.",
         src="S3, S5"),
    dict(id="F8", sev="medium", area="Environment",
         item="No roof designation, surface or wind on the official pages",
         detail="The Game Center Game Info block publishes Location, Stadium and Network only. The "
                "schedule page carries a summary weather chip ('Weather Clearnight') and nothing "
                "more. The NWS overlay the brief asks for is a separate domain, not read here.",
         src="S5, S6"),
    dict(id="F9", sev="medium", area="Availability",
         item="Every number pinned to the 2026-11-13 capture is stale",
         detail="The live page read on 2026-11-16 differs from the committed capture: two Lions rows "
                "changed, two Ravens rows appeared, Doubtful designations appeared, and the club "
                "records in the headers were replaced with post-game records.",
         src="S8, S1"),
    dict(id="F10", sev="medium", area="Repository",
         item="The nfl-* namespaces repeat the same page set",
         detail="The repository carries one top-level nfl-* namespace per session, most with their "
                "own questions, suggestions and review pages (the count is computed on the "
                "repository-review page and pinned to a commit, so it is not repeated here). "
                "Contradictory published values (F2) are the predictable result.",
         src="repo"),
    dict(id="F11", sev="low", area="Fixtures",
         item="Resolved: WAS at NYG venue recorded from the official Game Center",
         detail="The official Commanders-Giants Game Center reports Location EAST RUTHERFORD, NJ and "
                "Stadium METLIFE STADIUM. The Week 10 venue register is now complete at 14/14.",
         status="resolved — venue captured",
         src="S14"),
    dict(id="F12", sev="medium", area="Availability",
         item="The availability series has two time points, not four",
         detail="The brief asks for Wednesday, Thursday and Friday captures plus kickoff. Only "
                "2026-11-13 and 2026-11-16 exist, so the DNP to LP to FP path cannot be replayed.",
         src="S8, S1"),
    dict(id="F14", sev="medium", area="Availability",
         item="Reserve-list capture exists in nfl-collector; this namespace's join is not integrated",
         detail="The official November reserve-list page publishes 25 dated moves, and nfl-collector "
                "commits a 25-row structured capture with a ledger hash (2026-11-16). The remaining "
                "gap is local: nfl-decision-gaps still uses a static list and does not consume the "
                "collector feed automatically or validate reserve membership across weeks.",
         src="S10, S17"),
    dict(id="F13", sev="low", area="Fixtures",
         item="Resolved: dated 2026 schedule announcement and Week 11 listing recorded",
         detail="The dated May 8, 2026 NFL announcement says the full schedule would be released May 14; "
                "the current Week 11 page lists Colts at Texans on Nov 19. Both are now linked beside "
                "the current Week 10 schedule. This resolves the source-pairing gap, not future schedule changes.",
         status="resolved — sources paired",
         src="S11, S15, S16"),
    dict(id="F15", sev="medium", area="Results",
         item="LAC at BAL is still listed as scheduled; no final score is shown",
         detail="The current official NFL Week 10 schedule and scores reads (2026-11-17) list Chargers at "
                "Ravens for Monday, Nov 16 at 8:15 PM ET and show no Final state or score. This record "
                "therefore keeps both score fields blank and records the source-reported Scheduled state; "
                "no outcome is inferred.",
         status="open — final state/score not confirmed",
         src="S11, S12"),
]

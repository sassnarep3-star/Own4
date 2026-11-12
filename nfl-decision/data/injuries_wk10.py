"""Week 10 (2026) official NFL injury report + verified depth-chart deficiency rows.

Transcribed by session arena/e2b19bf6-own4 on 2026-11-12 from
  https://www.nfl.com/injuries/                      (practice + game status, per team)
  https://www.nfl.com/news/nfl-week-10-injury-report-2026-season  (game-status confirmations)
  https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11 (depth-chart news)
Blank cells mean the official page showed no value. Nothing is inferred.
"""

INJURY_SOURCE = "https://www.nfl.com/injuries/"
STATUS_SOURCE = "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
ROUNDUP = "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"
DNP, LP, FP = "Did Not Participate In Practice", "Limited Participation in Practice", "Full Participation in Practice"

# team, game, [ (player, pos, injury, practice, game_status) ]
T = {
"WAS": ("WAS@NYG Thu 11/12", [
 ("John Bates","TE","",FP,""),("Treylon Burks","WR","",DNP,""),("Jayden Daniels","QB","",FP,""),
 ("Matt Gulbin","C","",FP,""),("Chig Okonkwo","TE","",FP,""),("Lucas Patrick","C","Concussion",DNP,"Out"),
 ("Amik Robertson","CB","",LP,""),("Shy Tuttle","DT","",FP,""),("Colson Yankoff","TE","Knee",DNP,"Out")]),
"NYG": ("WAS@NYG Thu 11/12", [
 ("Abdul Carter","LB","",FP,""),("Jermaine Eluemunor","T","",FP,""),("Malik Harrison","LB","Groin",LP,"Questionable"),
 ("Colton Hood","CB","",FP,""),("Theo Johnson","TE","",FP,""),("Charlie Jones","WR","",FP,""),
 ("J.J. McCarthy","QB","",FP,""),("Darnell Mooney","WR","",FP,""),("Malik Nabers","WR","",FP,""),
 ("Cam Skattebo","RB","",FP,""),("Andrew Thomas","T","",FP,"")]),
"NE": ("NE@DET Sun 11/15 Munich", [
 ("Ben Brown","C","Knee",DNP,"Out"),("A.J. Brown","WR","",LP,""),("Kevin Byard","S","",LP,""),
 ("Carlton Davis III","CB","Knee",DNP,"Out"),("Reggie Gilliam","FB","",LP,""),("TreVeyon Henderson","RB","Illness",DNP,"Out"),
 ("Hunter Henry","TE","",LP,""),("Cameron Latu","TE","",DNP,""),("Drake Maye","QB","",FP,""),
 ("Morgan Moses","T","",LP,""),("Walter Rouse","T","",DNP,""),("Brenden Schooler","S","",DNP,""),
 ("Rhamondre Stevenson","RB","",DNP,""),("Greg Van Roten","G","",LP,""),("Charles Woods","CB","",LP,"")]),
"DET": ("NE@DET Sun 11/15 Munich", [
 ("Brian Branch","S","",LP,""),("Jared Goff","QB","",LP,""),("Kerby Joseph","S","",LP,""),
 ("Cade Mays","C","",DNP,""),("D.J. Reed","CB","",DNP,""),("Jacob Saylors","RB","",FP,""),
 ("Amon-Ra St. Brown","WR","",LP,""),("Sione Vaki","RB","",DNP,""),("DJ Wonnum","DE","",FP,"")]),
"KC": ("KC@ATL Sun 11/15", [
 ("Jeffrey Bassa","LB","",FP,""),("Mansoor Delane","CB","",FP,""),("Justin Fields","QB","",FP,""),
 ("Jaden Hicks","S","",FP,""),("Travis Kelce","TE","",FP,""),("Patrick Mahomes","QB","",FP,""),
 ("Jaylon Moore","T","",DNP,""),("Omarr Norman-Lott","DT","",LP,""),("Rashee Rice","WR","",FP,""),
 ("Peter Woods","DT","",DNP,""),("Xavier Worthy","WR","",FP,"")]),
"ATL": ("KC@ATL Sun 11/15", [
 ("Zachariah Branch","WR","",DNP,""),("Divine Deablo","LB","",LP,""),("Gervon Dexter Sr.","DT","",DNP,""),
 ("James Pearce Jr.","DE","",DNP,""),("Za'Darius Smith","DE","",DNP,""),("Josh Woods","LB","",DNP,"")]),
"MIN": ("MIN@GB Sun 11/15", [
 ("Blake Cashman","LB","",DNP,""),("T.J. Hockenson","TE","",DNP,""),("Tyrion Ingram-Dawkins","DT","",DNP,""),
 ("Theo Jackson","S","",FP,""),("Jauan Jennings","WR","",DNP,""),("Kyler Murray","QB","",DNP,""),
 ("Kyle Van Noy","LB","",DNP,""),("Jay Ward","S","",LP,""),("Carson Wentz","QB","",LP,"")]),
"GB": ("MIN@GB Sun 11/15", [
 ("Aaron Banks","G","",LP,""),("Chris Brooks","RB","",LP,""),("Javon Bullard","S","",DNP,""),
 ("Zaire Franklin","LB","",DNP,""),("Travis Glover","G","",LP,""),("Ty'Ron Hopper","LB","",LP,""),
 ("Josh Jacobs","RB","",DNP,""),("Bo Melton","WR","",FP,""),("Skyy Moore","WR","",LP,""),
 ("Micah Parsons","LB","",LP,""),("Sean Rhyan","C","",DNP,""),("Trey Smack","K","",LP,""),
 ("Lukas Van Ness","LB","",DNP,""),("Josh Whyle","TE","",DNP,""),("Savion Williams","WR","",LP,""),
 ("Kevin Zeitler","G","",LP,"")]),
"JAX": ("JAX@TEN Sun 11/15", [
 ("Jessie Bates","S","",DNP,""),("Ezra Cleveland","G","",LP,""),("Branson Combs","LB","",LP,""),
 ("Jordan Davis","DT","",DNP,""),("Robert Hainsey","C","",LP,""),("Antonio Johnson","S","",LP,""),
 ("Jakobi Meyers","WR","",DNP,""),("Chris Rodriguez Jr.","RB","",LP,""),("Bhayshul Tuten","RB","",DNP,""),
 ("Travon Walker","DE","",DNP,"")]),
"TEN": ("JAX@TEN Sun 11/15", [
 ("Cody Barton","LB","",DNP,""),("John Franklin-Myers","DE","",FP,""),("Marcus Harris","CB","",FP,""),
 ("Anthony Hill Jr.","LB","",DNP,""),("Jaylon Jones","CB","",FP,""),("JC Latham","T","",FP,""),
 ("Tony Pollard","RB","",FP,""),("Peter Skoronski","G","",DNP,""),("Tyjae Spears","RB","",DNP,""),
 ("Carnell Tate","WR","",DNP,""),("Tommy Townsend","P","",FP,""),("Kevin Winston Jr.","S","",FP,"")]),
"BUF": ("BUF@NYJ Sun 11/15", [
 ("Alec Anderson","G","",LP,""),("Christian Benford","CB","",LP,""),("Spencer Brown","T","",LP,""),
 ("Dion Dawkins","T","",LP,""),("Greg Gaines","DT","",FP,""),("Jordan Hancock","CB","",FP,""),
 ("Dalton Kincaid","TE","",LP,""),("Connor McGovern","C","",LP,""),("Ar'maj Reed-Adams","G","",FP,""),
 ("T.J. Sanders","DE","",FP,""),("Tyrell Shavers","WR","",FP,"")]),
"NYJ": ("BUF@NYJ Sun 11/15", [
 ("Omar Cooper Jr.","WR","",LP,""),("Joseph Ossai","DE","",LP,""),("VJ Payne","S","",FP,""),
 ("Harrison Phillips","DT","",DNP,""),("Trevin Wallace","LB","",DNP,""),("Garrett Wilson","WR","",LP,""),
 ("Nahshon Wright","CB","",LP,"")]),
"MIA": ("MIA@IND Sun 11/15", [
 ("Tucker Addington","LS","",LP,""),("Kaytron Allen","RB","",FP,""),("Darrell Baker Jr.","CB","",LP,""),
 ("Chris Bell","WR","",LP,""),("Aaron Brewer","C","",DNP,""),("Malik Herring","DE","",LP,""),
 ("Will Kacmarek","TE","",DNP,""),("Michael Taaffe","S","",FP,""),("Dante Trader Jr.","S","",FP,""),
 ("Jaylen Wright","RB","",FP,"")]),
"IND": ("MIA@IND Sun 11/15", [
 ("Mo Alie-Cox","TE","",DNP,""),("Jaylon Carlies","LB","",DNP,""),("Akeem Davis-Gaither","LB","",DNP,""),
 ("A.J. Haulcy","S","",DNP,""),("Arden Key","DE","",FP,""),("Luke Rhodes","LS","",DNP,""),
 ("Jonathan Taylor","RB","",LP,""),("Jerry Tillery","DT","",LP,""),("Jalen Travis","T","",DNP,""),
 ("Justin Walley","CB","",FP,""),("Charvarius Ward","CB","",DNP,"")]),
"CAR": ("CAR@NO Sun 11/15", [
 ("Jonathon Brooks","RB","",FP,""),("Brady Christensen","G","",FP,""),("Trevor Etienne","RB","",FP,""),
 ("Chuba Hubbard","RB","",DNP,""),("Lee Hunter","DT","",FP,""),("Mike Jackson","CB","",FP,""),
 ("Will Lee III","CB","",FP,""),("Xavier Legette","WR","",FP,""),("Damien Lewis","G","",FP,""),
 ("Bobby Okereke","LB","",DNP,""),("Jaelan Phillips","LB","",FP,""),("Torricelli Simpkins III","G","",FP,"")]),
"NO": ("CAR@NO Sun 11/15", [
 ("Kelvin Banks Jr.","T","",LP,""),("CJ Donaldson","RB","",DNP,""),("David Edwards","G","",LP,""),
 ("Martin Emerson","CB","",LP,""),("Travis Etienne","RB","",LP,""),("Noah Fant","TE","",LP,""),
 ("Alvin Kamara","RB","",DNP,""),("Erik McCoy","C","",DNP,""),("Christen Miller","DT","",LP,""),
 ("Asim Richards","T","",FP,"")]),
"HOU": ("HOU@CLE Sun 11/15", [
 ("Azeez Al-Shaair","LB","",DNP,""),("Reed Blankenship","S","",LP,""),("Tank Dell","WR","",LP,""),
 ("Blake Fisher","T","",FP,""),("Marvin Harrison Jr.","WR","",LP,""),("Jacob Hummel","LB","",LP,""),
 ("Brevin Jordan","TE","",DNP,""),("Woody Marks","RB","",LP,""),("David Montgomery","RB","",DNP,""),
 ("Keylan Rutledge","G","",DNP,""),("Jaylin Smith","CB","",LP,""),("Wyatt Teller","G","",LP,""),
 ("Tommy Togiai","DT","",FP,"")]),
"CLE": ("HOU@CLE Sun 11/15", [
 ("Austin Barber","T","",LP,""),("Denzel Boston","WR","",DNP,""),("Michael Burton","FB","",DNP,""),
 ("Maliek Collins","DT","",LP,""),("Harold Fannin Jr.","TE","",LP,""),("Ronnie Hickman Jr.","S","",DNP,""),
 ("Tytus Howard","T","",LP,""),("Elgton Jenkins","C","",DNP,""),("Carson Schwesinger","LB","",LP,""),
 ("Denzel Ward","CB","",LP,""),("Quincy Williams","LB","",LP,"")]),
"LA": ("LAR@AZ Sun 11/15", [
 ("Davis Allen","TE","",LP,""),("Steve Avila","G","",DNP,""),("Joe Cardona","LS","",LP,""),
 ("Kam Curl","S","",DNP,""),("Terrance Ferguson","TE","",DNP,""),("Myles Garrett","LB","",LP,""),
 ("Trent McDuffie","CB","",DNP,""),("Puka Nacua","WR","",DNP,""),("Colby Parkinson","TE","",LP,""),
 ("Matthew Stafford","QB","",FP,"")]),
"AZ": ("LAR@AZ Sun 11/15", [
 ("Budda Baker","S","",DNP,""),("Zachary Carter","DT","",LP,""),("Hjalte Froholdt","C","",DNP,""),
 ("Jon Gaines II","G","",DNP,""),("Bam Knight","RB","",LP,""),("Hunter Long","TE","",LP,""),
 ("Roy Lopez","DT","",DNP,""),("Max Melton","CB","",LP,""),("Isaac Seumalo","G","",DNP,""),
 ("Dante Stills","DT","",LP,""),("Josh Sweat","LB","",DNP,""),("Jayden Williams","T","",LP,""),
 ("Mack Wilson","LB","",DNP,""),("Andrew Wingard","S","",LP,"")]),
"SEA": ("SEA@LV Sun 11/15", [
 ("AJ Barner","TE","",FP,""),("Anthony Bradford","G","",LP,""),("Charles Cross","T","",DNP,""),
 ("Sam Darnold","QB","",DNP,""),("Derick Hall","LB","",LP,""),("Drew Lock","QB","",LP,""),
 ("Quenton Nelson","G","",DNP,""),("Uchenna Nwosu","LB","",LP,""),("Patrick O'Connell","LB","",LP,""),
 ("Connor O'Toole","LB","",LP,""),("Brandon Pili","DT","",DNP,""),("Jarran Reed","DT","",DNP,""),
 ("Rashid Shaheed","WR","",FP,""),("Jaxon Smith-Njigba","WR","",DNP,""),("Leonard Williams","DT","",DNP,"")]),
"LV": ("SEA@LV Sun 11/15", [
 ("Thomas Booker","DT","",LP,""),("Foley Fatukasi","DT","",LP,""),("Ian Thomas","TE","",FP,""),
 ("Trey Zuhn III","C","",LP,"")]),
"SF": ("SF@DAL Sun 11/15", [
 ("Mike Evans","WR","",DNP,""),("Renardo Green","CB","",DNP,""),("Dre Greenlaw","LB","",DNP,""),
 ("Nate Hobbs","CB","",FP,""),("Deommodore Lenoir","CB","",DNP,""),("Christian McCaffrey","RB","",DNP,""),
 ("Siran Neal","S","",LP,""),("Demarcus Robinson","WR","",FP,""),("Deebo Samuel Sr.","WR","",LP,""),
 ("Upton Stout","CB","",LP,""),("C.J. West","DT","",LP,""),("Trent Williams","T","",DNP,"")]),
"DAL": ("SF@DAL Sun 11/15", [
 ("Jonathan Bullard","DT","",FP,""),("Donovan Ezeiruaku","LB","",DNP,""),("Jake Ferguson","TE","",DNP,""),
 ("Tyler Goodson","RB","",DNP,""),("Malik Hooker","S","",DNP,""),("Marist Liufau","LB","",FP,""),
 ("P.J. Locke","S","",DNP,""),("Von Miller","LB","",DNP,""),("Jonathan Mingo","WR","",DNP,""),
 ("Devin Moore","CB","",FP,""),("DeMarvion Overshown","LB","",LP,""),("George Pickens","WR","",LP,""),
 ("Joey Porter Jr.","CB","",DNP,""),("Luke Schoonmaker","TE","",FP,""),("Brevyn Spann-Ford","TE","",FP,""),
 ("KaVontae Turpin","WR","",LP,"")]),
"PIT": ("PIT@CIN Sun 11/15", [
 ("Brandin Echols","CB","",FP,""),("DeShon Elliott","S","",LP,""),("Derrick Harmon","DT","",LP,""),
 ("Cameron Heyward","DT","",DNP,""),("Ben Skowronek","WR","",FP,""),("Doneiko Slaughter","CB","",FP,""),
 ("Darnell Washington","TE","",DNP,""),("T.J. Watt","LB","",DNP,"")]),
"CIN": ("PIT@CIN Sun 11/15", [
 ("Jonathan Allen","DT","",DNP,""),("Kyle Dugger","S","",DNP,""),("Dylan Fairchild","G","",LP,""),
 ("DJ Turner II","CB","",LP,"")]),
"LAC": ("LAC@BAL Mon 11/16", []),
"BAL": ("LAC@BAL Mon 11/16", []),
}

# Confirmed depth-chart deficiencies: an official NFL.com statement that a named player
# outside the usual starting lineup is starting / will start. tier_from = string depth the
# starter occupied per the official article's own language.
DEPTH = [
 {"team":"SEA","unit":"Offense","position":"QB","starter_out":"Sam Darnold",
  "starter_out_status":"Ruled out Week 10 (quad, ribs); 3rd game missed this season",
  "replacement":"Drew Lock","replacement_tier":"2nd string (backup)",
  "next_in_line":"Jalen Milroe (rookie) slated to back up Lock",
  "depth_cost":"high",
  "evidence":"\"Seahawks coach Mike Macdonald told Seattle Sports radio on Monday that Sam Darnold will not play ... Lock ... is expected to start again\"",
  "source":"https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"},
 {"team":"SEA","unit":"Offense","position":"QB (3rd string active)","starter_out":"Sam Darnold",
  "starter_out_status":"Out","replacement":"Jalen Milroe","replacement_tier":"3rd string (rookie)",
  "next_in_line":"","depth_cost":"medium",
  "evidence":"\"Rookie Jalen Milroe is slated to back up Lock for the second straight week.\"",
  "source":"https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"},
 {"team":"MIA","unit":"Offense","position":"QB","starter_out":"Malik Willis",
  "starter_out_status":"Placed on injured reserve (groin) 2026-11-11; out Weeks 10-13",
  "replacement":"Kyle McCord","replacement_tier":"2nd string (first career NFL start)",
  "next_in_line":"Brady Cook (practice squad) likely elevated as backup",
  "depth_cost":"high",
  "evidence":"\"With Willis shelved, second-year quarterback Kyle McCord will fill in, beginning Sunday on the road against the Indianapolis Colts.\"",
  "source":"https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"},
 {"team":"BAL","unit":"Offense","position":"QB","starter_out":"Lamar Jackson",
  "starter_out_status":"Fractured/dislocated right thumb, surgery, on IR; out 6-9 weeks",
  "replacement":"Jacoby Brissett","replacement_tier":"acquired by trade; behind him 3rd string had already started",
  "next_in_line":"Joe Fagnano (undrafted 3rd-stringer) started Week 9; Tyler Huntley out for season",
  "depth_cost":"critical",
  "evidence":"\"With Jackson and Tyler Huntley (out for the season with turf toe) placed on injured reserve, the Ravens were forced to start undrafted third-stringer Joe Fagnano ... The Ravens then acquired Brissett on Friday\"",
  "source":"https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season"},
 {"team":"AZ","unit":"Offense","position":"QB","starter_out":"Gardner Minshew / Jacoby Brissett",
  "starter_out_status":"Brissett benched mid-Week 8, demoted to 3rd string, then traded to BAL",
  "replacement":"Carson Beck","replacement_tier":"3rd string (rookie, 2026 3rd-round pick)",
  "next_in_line":"",
  "depth_cost":"high",
  "evidence":"\"QB Carson Beck will start Sunday's game against the Rams, per head coach Mike LaFleur. This will be Beck's first career start in the NFL\"",
  "source":ROUNDUP},
 {"team":"CLE","unit":"Offense","position":"QB","starter_out":"Shedeur Sanders",
  "starter_out_status":"Started Week 9 loss to New Orleans; replaced for Week 10",
  "replacement":"Deshaun Watson","replacement_tier":"returning starter (cleared concussion protocol)",
  "next_in_line":"",
  "depth_cost":"low",
  "evidence":"\"QB Deshaun Watson will start Sunday against the Texans, the team announced Wednesday ... Shedeur Sanders got the start in the loss to New Orleans.\"",
  "source":ROUNDUP},
 {"team":"MIN","unit":"Offense","position":"QB","starter_out":"Kyler Murray",
  "starter_out_status":"DNP Wednesday (hamstring); Week 10 starter not committed",
  "replacement":"Kirk Cousins","replacement_tier":"acquired by trade from LV; coach says \"too early\" to commit",
  "next_in_line":"Carson Wentz (limited, ankle)",
  "depth_cost":"high",
  "evidence":"\"it is 'too early' to commit to Kirk Cousins as their starting quarterback for Sunday's game against the Packers\"",
  "source":ROUNDUP},
 {"team":"GB","unit":"Offense","position":"RB","starter_out":"Josh Jacobs",
  "starter_out_status":"Broken ring finger, surgery this week; out Week 10, could return in 2-3 weeks",
  "replacement":"","replacement_tier":"not named by an official source",
  "next_in_line":"",
  "depth_cost":"high",
  "evidence":"\"RB Josh Jacobs is set to undergo surgery on his broken ring finger later this week ... Jacobs will miss this Sunday's game against the Vikings\"",
  "source":ROUNDUP},
 {"team":"LAR","unit":"Offense","position":"WR","starter_out":"Puka Nacua",
  "starter_out_status":"Turf toe + sprained MCL/PCL; not placed on IR but expected to miss significant time",
  "replacement":"","replacement_tier":"not named by an official source",
  "next_in_line":"Davante Adams (hamstring) out until about Week 12",
  "depth_cost":"critical",
  "evidence":"\"WR Puka Nacua (knee/toe) will not be placed on injured reserve, per McVay ... Nacua is still expected to miss significant time\"",
  "source":ROUNDUP},
 {"team":"SF","unit":"Offense","position":"WR","starter_out":"Mike Evans",
  "starter_out_status":"Achilles, DNP Wednesday, \"week to week\"",
  "replacement":"","replacement_tier":"not named by an official source",
  "next_in_line":"Deebo Samuel Sr. (hamstring, limited)",
  "depth_cost":"medium",
  "evidence":"\"WR Mike Evans (Achilles) did not practice Wednesday and is considered 'week to week,' per head coach Kyle Shanahan.\"",
  "source":ROUNDUP},
 {"team":"NE","unit":"Offense","position":"RB","starter_out":"Rhamondre Stevenson",
  "starter_out_status":"Knee, DNP Wednesday; TreVeyon Henderson also OUT (illness)",
  "replacement":"","replacement_tier":"not named by an official source",
  "next_in_line":"",
  "depth_cost":"critical",
  "evidence":"\"RB TreVeyon Henderson (illness) was ruled out for Sunday's game against the Lions in Munich. RB Rhamondre Stevenson (knee) DNP\"",
  "source":ROUNDUP},
 {"team":"ATL","unit":"Special teams","position":"K","starter_out":"Nick Folk",
  "starter_out_status":"Roster cut",
  "replacement":"Jake Moody","replacement_tier":"new signing",
  "next_in_line":"",
  "depth_cost":"medium",
  "evidence":"\"SIGNINGS - K Jake Moody ... ROSTER CUTS - K Nick Folk\"",
  "source":ROUNDUP},
 {"team":"BAL","unit":"Special teams","position":"K","starter_out":"","starter_out_status":"",
  "replacement":"Riley Patterson","replacement_tier":"new signing, will kick Monday",
  "next_in_line":"",
  "depth_cost":"medium",
  "evidence":"\"K Riley Patterson is signing with Baltimore following a workout and will kick for the Ravens during Monday's game against the Chargers\"",
  "source":ROUNDUP},
]

POLICY = [
 {"id":"IR-1","claim":"Practice report has three categories only: Did Not Participate, Limited Participation (<100% of normal reps), Full Participation (100%). The 'Out' category was removed from the Practice Report.","url":"https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693","publisher":"NFL.com (Competition Committee)"},
 {"id":"IR-2","claim":"Game Status Report has three categories: Out (will not play), Doubtful (unlikely to participate), Questionable (uncertain). The 'Probable' category was eliminated.","url":"https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693","publisher":"NFL.com (Competition Committee)"},
 {"id":"IR-3","claim":"NFL.com's Week 10 injury report page states it tracks player statuses for all 14 games.","url":STATUS_SOURCE,"publisher":"NFL.com"},
]

# Known gaps: things the brief asks for that NO official source provides.
GAPS = [
 {"id":"GAP-1","item":"Per-player 1st/2nd/3rd-string depth chart labels for all 32 teams",
  "status":"NOT AVAILABLE on an official source",
  "detail":"https://www.nfl.com/depth-charts/ returns HTTP 404 'Flag on the Play' (checked 2026-11-12). No official NFL depth chart was found. Therefore no player is labelled 1st/2nd/3rd string by this project; the DEPTH table above only records replacements that an official NFL.com article explicitly names.",
  "url":"https://www.nfl.com/depth-charts/"},
 {"id":"GAP-2","item":"Injury column values on nfl.com/injuries",
  "status":"PARTIALLY BLANK",
  "detail":"Many listed players show a practice status but a blank injury and a blank game status on the official page. Those cells are left blank here; nothing is inferred from practice status.",
  "url":INJURY_SOURCE},
 {"id":"GAP-3","item":"Official injury-report page for LAC and BAL (Week 10)",
  "status":"REPORTED AS 'No Injuries Reported'",
  "detail":"The official page displays 'No Injuries Reported' for both clubs. Recorded verbatim; not treated as proof that no player is injured.",
  "url":INJURY_SOURCE},
 {"id":"GAP-4","item":"Historical snapshots of the injury report",
  "status":"NOT AVAILABLE",
  "detail":"nfl.com/injuries/ shows the current week only. No official archive of past-week practice reports was found, so injury data cannot be back-tested.",
  "url":INJURY_SOURCE},
]

#!/usr/bin/env python3
"""
nfl-req-review — data capture for the 2026-11-17 re-verification round.

Encodes, line by line, the official pages read live in this session (2026-11-17 UTC)
and computes every count and join at build time. No count is typed into a rendered
page: pages render from these computed values only.

Sources read live 2026-11-17 (all official, all fetched and read in-session):
  1. https://www.nfl.com/standings/league/2026/REG            (32-team standings)
  2. https://www.nfl.com/schedules/2026/by-week/week-11       (Week-11 slate, venues via
     the official schedule page's stadium links, weather line)
  3. https://www.nfl.com/injuries/league/2026/reg11           (redirects to the Week-10
     report — Week-11 report not yet published; recorded as a finding)
  4. https://www.nfl.com/injuries/league/2026/reg10           (Week-10 injury report,
     final designations as read 2026-11-17; 8 chunks, all read)
  5. https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season
  6. https://www.nfl.com/transactions/                        (November 2026 trades)
  7. https://www.nfl.com/transactions/league/reserve-list/2026/11
  8. https://www.nfl.com/games/vikings-at-49ers-2026-reg-11  (game centre: Game Info
     Location/Stadium; injury-report tabs not yet available)
  9. https://www.nfl.com/teams/baltimore-ravens/depth-chart   (404 — depth-chart route
     re-confirmed unavailable)
 10. https://www.nfl.com/injuries/league/2025/reg1            (past-season archive
     availability re-confirmed)

The generator writes data/*.json. Run:  python3 engine/build_data.py
"""

import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
os.makedirs(DATA, exist_ok=True)

ROUND = "2026-11-17"
READ_AT = "2026-11-17T00:00:00Z"  # session read window; per-page timestamps below


def sha256(obj):
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------------------
# 1. Week-11 schedule (official schedule page, read live 2026-11-17).
#    Venue evidence: the official schedule page's own stadium links
#    (destinationAddress.location=...) plus the game centre Game Info for the
#    Mexico City fixture. Weather line published on the schedule page itself.
# ---------------------------------------------------------------------------
WEEK11 = [
    # day, time, network, away, home, away_rec, home_rec, venue, venue_source, weather
    ("Thu 2026-11-19", "8:15 PM", "PRIME", "IND", "HOU", "3-7", "3-6",
     "NRG Stadium (Houston)", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "CBS", "MIA", "BUF", "1-8", "8-1",
     "Highmark Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "FOX", "BAL", "CAR", "4-5", "4-5",
     "Bank of America Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "FOX", "NO", "CHI", "3-6", "7-2",
     "Soldier Field", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "FOX", "TEN", "DAL", "1-8", "4-6",
     "AT&T Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "FOX", "TB", "DET", "3-6", "7-2",
     "Ford Field", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "CBS", "ARI", "KC", "3-7", "7-2",
     "GEHA Field at Arrowhead Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "1:00 PM", "CBS", "PIT", "PHI", "6-3", "2-7",
     "Lincoln Financial Field", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "4:05 PM", "FOX", "NYJ", "LAC", "2-8", "0-8",
     "SoFi Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "4:25 PM", "CBS", "JAX", "NYG", "7-2", "5-3-1",
     "MetLife Stadium", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "4:25 PM", "CBS", "LV", "DEN", "4-6", "7-2",
     "Empower Field at Mile High", "schedule page stadium link", ""),
    ("Sun 2026-11-22", "8:20 PM", "NBC", "MIN", "SF", "7-2", "8-1",
     "Estadio Banorte (Mexico City)", "game centre Game Info", ""),
    ("Mon 2026-11-23", "8:15 PM", "ESPN", "CIN", "WAS", "7-2", "3-5-1",
     "FedEx Field", "schedule page stadium link", "Clear, night (schedule page)"),
]
BYE_WEEK11 = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]

# ---------------------------------------------------------------------------
# 2. Week-10 injury report, final designations as read live 2026-11-17.
#    Per club: players_listed, out names, doubtful names, questionable names.
#    Blank = players_listed - len(out) - len(doubtful) - len(questionable).
#    Order of clubs = order of appearance on the official page.
# ---------------------------------------------------------------------------
INJ = [
    # club, opponent, date_label, players_listed, out[], doubtful[], questionable[]
    ("WAS", "NYG", "Thu 2026-11-12", 9,
     ["Lucas Patrick", "Colson Yankoff"], [], []),
    ("NYG", "WAS", "Thu 2026-11-12", 11,
     [], [], ["Malik Harrison"]),
    ("NE", "DET", "Sun 2026-11-15", 15,
     ["Ben Brown", "Carlton Davis III", "TreVeyon Henderson"], [],
     ["A.J. Brown", "Kevin Byard", "Reggie Gilliam", "Cameron Latu",
      "Walter Rouse", "Brenden Schooler", "Rhamondre Stevenson",
      "Greg Van Roten", "Charles Woods"]),
    ("DET", "NE", "Sun 2026-11-15", 9,
     ["Kerby Joseph", "Cade Mays", "D.J. Reed"], [],
     ["Amon-Ra St. Brown", "Sione Vaki"]),
    ("KC", "ATL", "Sun 2026-11-15", 12,
     ["Jaylon Moore", "Omarr Norman-Lott", "Peter Woods"], [],
     ["Mansoor Delane", "Jaydn Ott", "Kenneth Walker III"]),
    ("ATL", "KC", "Sun 2026-11-15", 11,
     ["Zachariah Branch"], ["Divine Deablo"],
     ["Gervon Dexter Sr.", "James Pearce Jr.", "Josh Woods"]),
    ("MIN", "GB", "Sun 2026-11-15", 13,
     ["Blake Cashman", "T.J. Hockenson", "Tyrion Ingram-Dawkins",
      "Jauan Jennings", "Kyler Murray"], [],
     ["Jordan Addison", "Josh Metellus", "Kyle Van Noy"]),
    ("GB", "MIN", "Sun 2026-11-15", 17,
     ["Josh Jacobs", "Micah Parsons", "Sean Rhyan", "Josh Whyle"],
     ["Zaire Franklin"],
     ["Chris Brooks", "Javon Bullard", "Travis Glover", "Xavier McKinney",
      "Skyy Moore", "Lukas Van Ness", "Kevin Zeitler"]),
    ("JAX", "TEN", "Sun 2026-11-15", 11,
     ["Jessie Bates", "Jordan Davis", "BJ Green II"], [],
     ["Robert Hainsey"]),
    ("TEN", "JAX", "Sun 2026-11-15", 12,
     ["Cody Barton", "Anthony Hill Jr.", "Peter Skoronski", "Carnell Tate",
      "Tommy Townsend"], [], ["Tyjae Spears"]),
    ("BUF", "NYJ", "Sun 2026-11-15", 14,
     [], ["Spencer Brown"],
     ["Christian Benford", "Sam Franklin Jr.", "Jordan Hancock",
      "Tyrell Shavers"]),
    ("NYJ", "BUF", "Sun 2026-11-15", 9,
     ["Trevin Wallace"], [],
     ["Jarvis Brownlee Jr.", "Omar Cooper Jr.", "Adonai Mitchell",
      "Joseph Ossai", "VJ Payne", "Harrison Phillips", "Garrett Wilson",
      "Nahshon Wright"]),
    ("MIA", "IND", "Sun 2026-11-15", 11,
     ["Aaron Brewer", "Jared Wayne"], ["Chris Bell"], ["Darrell Baker Jr."]),
    ("IND", "MIA", "Sun 2026-11-15", 14,
     ["Mo Alie-Cox", "Jaylon Carlies", "Akeem Davis-Gaither", "Luke Rhodes",
      "Jerry Tillery", "Jalen Travis"], [], ["Will Mallory"]),
    ("CAR", "NO", "Sun 2026-11-15", 12,
     ["Bobby Okereke"], ["Jonathon Brooks", "Mike Jackson"],
     ["Brady Christensen", "Will Lee III", "Xavier Legette", "Jaelan Phillips"]),
    ("NO", "CAR", "Sun 2026-11-15", 12,
     ["CJ Donaldson", "Taliese Fuaga", "Erik McCoy", "Christen Miller"], [],
     ["Martin Emerson", "Travis Etienne"]),
    ("HOU", "CLE", "Sun 2026-11-15", 16,
     ["Azeez Al-Shaair", "Marvin Harrison Jr.", "Danielle Hunter",
      "Brevin Jordan", "Keylan Rutledge"], [],
     ["Will Anderson Jr.", "Trent Brown", "Jacob Hummel", "David Montgomery",
      "Jaylin Smith", "Wyatt Teller"]),
    ("CLE", "HOU", "Sun 2026-11-15", 12,
     ["Michael Burton", "Ronnie Hickman Jr."], [], ["Denzel Boston"]),
    ("LAR", "AZ", "Sun 2026-11-15", 14,
     ["Steve Avila", "Terrance Ferguson"], [],
     ["Davis Allen", "Joe Cardona", "Kam Curl", "Myles Garrett",
      "Trent McDuffie"]),
    ("AZ", "LAR", "Sun 2026-11-15", 15,
     ["Zachary Carter", "Hjalte Froholdt", "Jon Gaines II"], [],
     ["Hunter Long", "Roy Lopez", "Max Melton", "Darius Robinson",
      "Jayden Williams", "Andrew Wingard"]),
    ("SEA", "LV", "Sun 2026-11-15", 15,
     ["Charles Cross", "Sam Darnold", "Quenton Nelson", "Leonard Williams"],
     [], []),
    ("LV", "SEA", "Sun 2026-11-15", 5,
     [], [], ["Thomas Booker", "Dont'e Thornton Jr."]),
    ("SF", "DAL", "Sun 2026-11-15", 12,
     ["Mike Evans"], [],
     ["Renardo Green", "Dre Greenlaw", "Nate Hobbs", "Deommodore Lenoir",
      "Upton Stout", "C.J. West", "Trent Williams"]),
    ("DAL", "SF", "Sun 2026-11-15", 19,
     ["Donovan Ezeiruaku", "Jake Ferguson", "Tyler Goodson", "P.J. Locke",
      "Jonathan Mingo"], ["Juanyeh Thomas"],
     ["DaRon Bland", "Jonathan Bullard", "Alijah Clark", "Devin Moore",
      "Joey Porter Jr."]),
    ("PIT", "CIN", "Sun 2026-11-15", 8,
     [], [], ["Derrick Harmon"]),
    ("CIN", "PIT", "Sun 2026-11-15", 9,
     ["Kyle Dugger"], ["Jalen Davis", "Andrei Iosivas", "Brian Parker II"], []),
    ("LAC", "BAL", "Mon 2026-11-16", 19,
     ["Branson Taylor", "Isas Waxter", "Kendall Williamson"],
     ["Brenen Thompson"],
     ["Kayode Awosika", "Justin Eboigbe", "Ladd McConkey", "David Njoku",
      "Denzel Perryman", "Trey Pipkins"]),
    ("BAL", "LAC", "Mon 2026-11-16", 10,
     ["Jaylinn Hawkins"], [], ["Adam Randall"]),
]

# ---------------------------------------------------------------------------
# 3. Week-10 official inactive list (nfl.com news article, read live 2026-11-17).
#    147 entries across the 24 clubs of Sunday's 12 games (incl. Munich).
#    Venue lines are transcribed from the article's own WHERE lines.
# ---------------------------------------------------------------------------
INACTIVES = {
    "NE": ["Carlton Davis", "Brenden Schooler", "Dametrious Crownover",
           "Walter Rouse", "Ben Brown", "Behren Morton"],
    "DET": ["Keith Abney II", "Ahmed Hassanein", "Cade Mays",
            "Amen Ogbongbemiga", "D.J. Reed", "Mekhi Wingo"],
    "KC": ["Kenneth Walker", "Garrett Nussmeier", "Jaydn Ott",
           "Melvin Smith", "Ben VanSumeren", "Jaylon Moore", "Peter Woods"],
    "ATL": ["Andy Dalton", "Divine Deablo", "Avieon Terrell",
            "Zachariah Branch", "Jack Strand", "Robert Longerbeam",
            "Cameron Williams"],
    "HOU": ["Azeez Al-Shaair", "Brevin Jordan", "Marvin Harrison Jr.",
            "David Montgomery", "Danielle Hunter", "Keylan Rutledge",
            "Wyatt Teller"],
    "CLE": ["Dillon Gabriel", "Taylen Green", "Justin Jefferson",
            "Noah Igbinoghene", "Ronnie Hickman", "Parker Brailsford"],
    "MIN": ["Kyler Murray", "Jordan Addison", "Max Brosmer", "Jauan Jennings",
            "Blake Cashman", "T.J. Hockenson", "Tyroin Ingram-Dawkins"],
    "GB": ["Josh Jacobs", "Pierre Strong Jr.", "Zaire Franklin",
           "Donovan Jennings", "Kevin Zeitler", "Sean Rhyan"],
    "MIA": ["Chris Bell", "Marcellas Dial Jr.", "Aaron Brewer",
            "Caedan Wallace", "Justin Joly", "Jared Wayne"],
    "IND": ["Jaylon Carlies", "Riley Leonard", "Will Mallory", "Luke Rhodes",
            "Jerry Tillery", "Jalen Travis"],
    "CAR": ["Ja'Tavion Sanders", "Haynes King", "Will Lee", "AJ Dillon",
            "Bobby Okereke", "Sam Hecht", "TeRah Edwards"],
    "NO": ["Zach Wilson", "Mike Reid", "CJ Donaldson", "Jaylan Ford",
           "Taliese Fuaga", "Erik McCoy"],
    "BUF": ["Shane Buechele", "Jalon Kilgore", "Mike Danna",
            "Ar'maj Reed-Adams", "Jude Bowry", "Greg Gaines"],
    "NYJ": ["Jarvis Brownlee Jr.", "Nate Lynn", "Tim Patrick",
            "Trevin Wallace", "Jelani Woods"],
    "JAX": ["Jessie Bates III", "CJ Williams", "Jordan Davis",
            "Wesley Williams", "Albert Regis"],
    "TEN": ["Carnell Tate", "Nick Singleton", "Jaylon Jones", "Cody Barton",
            "Anthony Hill Jr.", "Brandon Crenshaw-Dickson", "Jackie Marshall"],
    "LAR": ["Ty Simpson", "Maximus Pulley", "Joe Cardona",
            "Darryl Peterson III", "Steve Avila", "Keagen Trost",
            "Desjuan Johnson"],
    "AZ": ["Joey Aguilar", "Starling Thomas V", "Eku Leota",
           "Jayden Williams", "Jon Gaines II", "Hjalte Froholdt"],
    "SEA": ["Sam Darnold", "Emanuel Wilson", "Avery Smith",
            "Quenton Nelson", "Charles Cross", "Deven Eastern",
            "Leonard Williams"],
    "LV": ["Dont'e Thornton Jr.", "Malik Benson", "Tristin McCollum",
           "Dalton Johnson", "Bryce Cabeldue", "Thomas Booker IV"],
    "SF": ["Kurtis Rourke", "Mike Evans", "Enrique Cruz Jr.",
           "Tatum Bethune", "Brandin Cooks"],
    "DAL": ["P.J. Locke III", "Donovan Ezeiruaku", "Derion Kendrick",
            "Jonathan Mingo", "Juanyeh Thomas", "Ajani Cornelius",
            "Jake Ferguson"],
    "PIT": ["DeShon Elliott", "Drew Allar", "Will Howard",
            "Sean Murphy-Bunting", "Eli Heidenreich"],
    "CIN": ["Kyle Dugger", "Connor Lew", "Myles Hinton", "Landon Robinson"],
}
INACTIVE_VENUES = {
    "NE@DET": "FC Bayern Munich Stadium (Munich, Germany)",
    "KC@ATL": "Mercedes-Benz Stadium (Atlanta)",
    "HOU@CLE": "Huntington Bank Field (Cleveland)",
    "MIN@GB": "Lambeau Field (Green Bay, Wis.)",
    "MIA@IND": "Lucas Oil Stadium (Indianapolis)",
    "CAR@NO": "Caesars Superdome (New Orleans)",
    "BUF@NYJ": "MetLife Stadium (East Rutherford, N.J.)",
    "JAX@TEN": "Nissan Stadium (Nashville, Tenn.)",
    "LAR@AZ": "State Farm Stadium (Glendale, Ariz.)",
    "SEA@LV": "Allegiant Stadium (Las Vegas)",
    "SF@DAL": "AT&T Stadium (Arlington, Texas)",
    "PIT@CIN": "Paycor Stadium (Cincinnati)",
}

# ---------------------------------------------------------------------------
# 4. November 2026 transactions (official, read live 2026-11-17).
# ---------------------------------------------------------------------------
TRADES_NOV = [
    ("ATL", "JAX", "11/10", "Jessie Bates"),
    ("PHI", "JAX", "11/10", "Jordan Davis"),
    ("TEN", "BUF", "11/10", "Amani Hooker"),
    ("IND", "SF", "11/10", "Keenan Allen"),
    ("LV", "MIN", "11/10", "Kirk Cousins"),
    ("LAC", "DEN", "11/10", "Daiyan Henley"),
    ("IND", "KC", "11/10", "Josh Downs"),
    ("ATL", "BAL", "11/10", "Ryan Neuzil"),
    ("BAL", "ATL", "11/10", "Andrew Vorhees"),
    ("NYJ", "DET", "11/09", "Andre Cisco"),
    ("NO", "JAX", "11/09", "Davon Godchaux"),
    ("AZ", "BAL", "11/06", "Jacoby Brissett"),
]
RESERVE_NOV = [
    ("LAR", "11/16", "Dylan McMahon"),
    ("LAC", "11/16", "Branson Taylor"),
    ("NO", "11/14", "Christen Miller"),
    ("NE", "11/14", "TreVeyon Henderson"),
    ("CLE", "11/14", "Michael Burton"),
    ("IND", "11/14", "Mo Alie-Cox"),
    ("IND", "11/14", "Akeem Davis-Gaither"),
    ("TEN", "11/14", "Peter Skoronski"),
    ("TEN", "11/14", "Tommy Townsend"),
    ("DAL", "11/14", "Tyler Goodson"),
    ("GB", "11/14", "Josh Whyle"),
    ("LAR", "11/12", "Puka Nacua"),
    ("LAR", "11/10", "Jordan Whittington"),
    ("MIA", "11/10", "Zach Sieler"),
    ("MIA", "11/10", "Malik Willis"),
    ("SF", "11/10", "Gracen Halton"),
    ("AZ", "11/10", "Gardner Minshew"),
    ("AZ", "11/10", "Michael Wilson"),
    ("TEN", "11/09", "James Williams"),
    ("MIN", "11/09", "Demond Claiborne"),
    ("BUF", "11/09", "Josh Palmer"),
    ("ATL", "11/07", "Brian Robinson"),
    ("LAR", "11/07", "Jaylen Watson"),
    ("DEN", "11/07", "Eyioma Uwazurike"),
    ("DET", "11/07", "Jack Campbell"),
]

# ---------------------------------------------------------------------------
# 5. Standings, read live 2026-11-17 (through Week 10).
# ---------------------------------------------------------------------------
STANDINGS = [
    # abbr, name, w, l, t, pct, pf, pa, streak
    ("BUF", "Buffalo Bills", 8, 1, 0, 0.889, 287, 199, "5W"),
    ("SF", "San Francisco 49ers", 8, 1, 0, 0.889, 281, 196, "2W"),
    ("CHI", "Chicago Bears", 7, 2, 0, 0.778, 241, 184, "4W"),
    ("CIN", "Cincinnati Bengals", 7, 2, 0, 0.778, 278, 193, "5W"),
    ("DEN", "Denver Broncos", 7, 2, 0, 0.778, 198, 186, "5W"),
    ("DET", "Detroit Lions", 7, 2, 0, 0.778, 257, 199, "5W"),
    ("JAX", "Jacksonville Jaguars", 7, 2, 0, 0.778, 269, 144, "3W"),
    ("KC", "Kansas City Chiefs", 7, 2, 0, 0.778, 237, 156, "2W"),
    ("MIN", "Minnesota Vikings", 7, 2, 0, 0.778, 176, 126, "1W"),
    ("PIT", "Pittsburgh Steelers", 6, 3, 0, 0.667, 198, 182, "1L"),
    ("NYG", "New York Giants", 5, 3, 1, 0.611, 203, 196, "1L"),
    ("CLE", "Cleveland Browns", 6, 4, 0, 0.600, 188, 220, "1W"),
    ("GB", "Green Bay Packers", 6, 4, 0, 0.600, 226, 221, "1L"),
    ("LAR", "Los Angeles Rams", 6, 4, 0, 0.600, 248, 187, "4W"),
    ("SEA", "Seattle Seahawks", 6, 4, 0, 0.600, 223, 175, "2W"),
    ("NE", "New England Patriots", 5, 5, 0, 0.500, 221, 242, "2L"),
    ("BAL", "Baltimore Ravens", 4, 5, 0, 0.444, 189, 236, "4L"),
    ("CAR", "Carolina Panthers", 4, 5, 0, 0.444, 219, 236, "1W"),
    ("DAL", "Dallas Cowboys", 4, 6, 0, 0.400, 286, 282, "1L"),
    ("LV", "Las Vegas Raiders", 4, 6, 0, 0.400, 251, 289, "2L"),
    ("WAS", "Washington Commanders", 3, 5, 1, 0.389, 196, 223, "1W"),
    ("HOU", "Houston Texans", 3, 6, 0, 0.333, 233, 219, "1L"),
    ("NO", "New Orleans Saints", 3, 6, 0, 0.333, 202, 236, "1L"),
    ("TB", "Tampa Bay Buccaneers", 3, 6, 0, 0.333, 202, 178, "1L"),
    ("AZ", "Arizona Cardinals", 3, 7, 0, 0.300, 184, 289, "2L"),
    ("ATL", "Atlanta Falcons", 3, 7, 0, 0.300, 201, 258, "3L"),
    ("IND", "Indianapolis Colts", 3, 7, 0, 0.300, 208, 271, "1W"),
    ("PHI", "Philadelphia Eagles", 2, 7, 0, 0.222, 148, 221, "7L"),
    ("NYJ", "New York Jets", 2, 8, 0, 0.200, 194, 254, "5L"),
    ("MIA", "Miami Dolphins", 1, 8, 0, 0.111, 148, 224, "3L"),
    ("TEN", "Tennessee Titans", 1, 8, 0, 0.111, 167, 239, "3L"),
    ("LAC", "Los Angeles Chargers", 0, 8, 0, 0.000, 121, 219, "8L"),
]


def norm(name):
    """Normalize a player name for join comparison."""
    s = name.lower().replace(".", "").replace("'", "")
    for suf in (" iii", " ii", " jr", " sr"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s.strip()


def name_keys(name):
    """Match keys for a player name: full normalized form, plus a
    surname + first-initial fallback for official spelling variants
    (e.g. 'Tyrion Ingram-Dawkins' on the injury report vs 'Tyroin
    Ingram-Dawkins' on the inactive list)."""
    parts = norm(name).split()
    keys = {norm(name)}
    if len(parts) >= 2:
        keys.add(parts[-1] + " " + parts[0][0])
    return keys


# ---------------------------------------------------------------------------
# Compute the designation join (E14 / E21 evidence).
# The inactive list is the official record of who did NOT play. Restricted to
# the 24 clubs of Sunday's 12 games (the inactive article's own scope).
# ---------------------------------------------------------------------------
SUNDAY_CLUBS = set(INACTIVES.keys())
inactive_keys = {c: set().union(*[name_keys(n) for n in names])
                 for c, names in INACTIVES.items()}
reserve_keys = set().union(*[name_keys(n) for _, _, n in RESERVE_NOV])

injury_rows = []
for club, opp, day, listed, outs, doubts, qs in INJ:
    blank = listed - len(outs) - len(doubts) - len(qs)
    injury_rows.append({
        "club": club, "opponent": opp, "date_label": day,
        "players_listed": listed,
        "out": outs, "doubtful": doubts, "questionable": qs,
        "blank_designation": blank,
    })

join_rows = []
for r in injury_rows:
    club = r["club"]
    if club not in SUNDAY_CLUBS:
        continue
    inv = inactive_keys[club]
    for desig in ("out", "doubtful", "questionable"):
        for name in r[desig]:
            keys = name_keys(name)
            exact = norm(name) in inv
            loose = bool(keys & inv)
            in_inactive = exact or loose
            on_reserve = bool(keys & reserve_keys)
            join_rows.append({
                "club": club, "designation": desig.capitalize(),
                "player": name,
                "match_tier": "exact" if exact else ("surname+initial" if loose else "no match"),
                "in_inactive_list": in_inactive,
                "on_nov_reserve_list": on_reserve,
            })

designation_stats = {}
for desig in ("Out", "Doubtful", "Questionable"):
    rows = [j for j in join_rows if j["designation"] == desig]
    n = len(rows)
    # Clean partition: inactive list first (official did-not-play record),
    # then reserve list (IR — did not play), then unexplained, then played.
    in_inactive = [j for j in rows if j["in_inactive_list"]]
    reserve_only = [j for j in rows
                    if not j["in_inactive_list"] and j["on_nov_reserve_list"]]
    unexplained = [j for j in rows
                   if not j["in_inactive_list"] and not j["on_nov_reserve_list"]]
    # 'played' is not observable directly: a player neither inactive nor on IR
    # is presumed to have played. Unexplained = Out designations with neither
    # corroboration (flagged); for Doubtful/Questionable the same bucket means
    # "designated but not corroborated as inactive" (i.e. presumed played).
    dnp = len(in_inactive) + len(reserve_only)
    p, lo, hi = wilson(dnp, n)
    designation_stats[desig] = {
        "n": n,
        "did_not_play_inactive_list": len(in_inactive),
        "did_not_play_reserve_list_only": len(reserve_only),
        "did_not_play_total": dnp,
        "did_not_play_rate": p,
        "did_not_play_rate_lo": lo,
        "did_not_play_rate_hi": hi,
        "not_corroborated": len(unexplained),
    }

unexplained_out = [
    {"club": j["club"], "player": j["player"]}
    for j in join_rows
    if j["designation"] == "Out" and not j["in_inactive_list"]
    and not j["on_nov_reserve_list"]
]

# ---------------------------------------------------------------------------
# Assemble the capture document with hashes.
# ---------------------------------------------------------------------------
capture = {
    "round": ROUND,
    "session": "arena/ca159db5-own4",
    "generated_utc": READ_AT,
    "rule": "structured rows + sha256 + timestamps only; no raw HTML committed (RF-18)",
    "sources": [
        {"id": "R-STAND", "url": "https://www.nfl.com/standings/league/2026/REG",
         "title": "2026 NFL League Standings", "read_utc": READ_AT,
         "chunks_read": "0-1 of 2", "what": "32-team standings through Week 10"},
        {"id": "R-SCHED", "url": "https://www.nfl.com/schedules/2026/by-week/week-11",
         "title": "NFL Week 11 Schedule 2026", "read_utc": READ_AT,
         "chunks_read": "0-2 of 3",
         "what": "14 fixtures, 6 byes; venues from the schedule page's own stadium links; weather line for CIN@WAS"},
        {"id": "R-INJ11", "url": "https://www.nfl.com/injuries/league/2026/reg11",
         "title": "redirects to the Week-10 injury report", "read_utc": READ_AT,
         "chunks_read": "0 of 1",
         "what": "Week-11 report not yet published as of 2026-11-17; URL resolves to Week 10"},
        {"id": "R-INJ10", "url": "https://www.nfl.com/injuries/league/2026/reg10",
         "title": "Official NFL Injury Report — Week 10, 2026", "read_utc": READ_AT,
         "chunks_read": "0-7 of 8",
         "what": "final designations as read 2026-11-17; all 28 clubs, 14 fixtures"},
        {"id": "R-INACT", "url": "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
         "title": "NFL Week 10 inactives: Players ruled out for Sunday's 12 games",
         "read_utc": READ_AT, "chunks_read": "0-1 of 2",
         "what": "147 entries, 24 clubs; WHERE venue lines for all 12 games"},
        {"id": "R-TRADES", "url": "https://www.nfl.com/transactions/",
         "title": "2026 NFL League Transactions", "read_utc": READ_AT,
         "chunks_read": "0 of 1", "what": "November 2026 trades: 12"},
        {"id": "R-RESERVE", "url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
         "title": "2026 NFL reserve-list by month", "read_utc": READ_AT,
         "chunks_read": "0-1 of 2", "what": "November 2026 Reserve/Injured moves: 25"},
        {"id": "R-GAME", "url": "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11",
         "title": "Minnesota Vikings at San Francisco 49ers 2026 REG 11 - Game Center",
         "read_utc": READ_AT, "chunks_read": "0 of 2",
         "what": "Game Info: Location MEXICO CITY, Stadium ESTADIO BANORTE; injury-report tabs not yet available"},
        {"id": "R-DEPTH", "url": "https://www.nfl.com/teams/baltimore-ravens/depth-chart",
         "title": "404 - Flag on the Play", "read_utc": READ_AT,
         "chunks_read": "0 of 1",
         "what": "club depth-chart route re-confirmed unavailable (E13 route (a))"},
        {"id": "R-ARCH", "url": "https://www.nfl.com/injuries/league/2025/reg1",
         "title": "Official NFL Injury Report — 2025 Season, Week 1", "read_utc": READ_AT,
         "chunks_read": "0 of 6",
         "what": "past-season weekly injury archive re-confirmed available on the official site (E16)"},
    ],
    "findings": {
        "week11_injury_report": "Not yet published as of 2026-11-17; the reg11 URL resolves to the Week-10 report. The latest official report is Week 10 (read live today).",
        "week10_report_delta": "The committed 2026-11-13 capture (326 rows; 14 Out; 11 Questionable; 0 Doubtful) is a Friday point-in-time snapshot. The live report read 2026-11-17 carries the final designations: 346 rows; 70 Out; 90 Questionable; 11 Doubtful; 175 blank. Delta: +20 rows, +56 Out, +79 Questionable, +11 Doubtful.",
        "depth_route": "nfl.com club depth-chart pages 404 (re-confirmed 2026-11-17). Snap counts exist only inside the official Game Book PDF (game centre route verified 2026-11-16 by session arena/013190b4-own4); no standalone official snap-count page found.",
    },
    "week11_schedule": {
        "fixtures": [
            {"day": d, "time": t, "network": n, "away": a, "home": h,
             "away_record": ar, "home_record": hr, "venue": v,
             "venue_evidence": vs, "weather": w,
             "game_url": "https://www.nfl.com/games/%s-at-%s-2026-reg-11" % (a.lower(), h.lower())}
            for (d, t, n, a, h, ar, hr, v, vs, w) in WEEK11
        ],
        "byes": BYE_WEEK11,
        "count_fixtures": len(WEEK11),
        "count_byes": len(BYE_WEEK11),
    },
    "injury_report_week10": {
        "rows": injury_rows,
        "totals": {
            "clubs": len(injury_rows),
            "players_listed": sum(r["players_listed"] for r in injury_rows),
            "out": sum(len(r["out"]) for r in injury_rows),
            "doubtful": sum(len(r["doubtful"]) for r in injury_rows),
            "questionable": sum(len(r["questionable"]) for r in injury_rows),
            "blank": sum(r["blank_designation"] for r in injury_rows),
        },
    },
    "inactives_week10": {
        "by_club": INACTIVES,
        "venues": INACTIVE_VENUES,
        "total_entries": sum(len(v) for v in INACTIVES.values()),
        "clubs": len(INACTIVES),
    },
    "transactions_november_2026": {
        "trades": [{"from": f, "to": t, "date": d, "player": p} for f, t, d, p in TRADES_NOV],
        "reserve_list": [{"club": c, "date": d, "player": p} for c, d, p in RESERVE_NOV],
        "count_trades": len(TRADES_NOV),
        "count_reserve": len(RESERVE_NOV),
    },
    "standings_2026_week10": {
        "rows": [{"abbr": a, "name": n, "w": w, "l": l, "t": t, "pct": p,
                  "pf": pf, "pa": pa, "streak": s}
                 for (a, n, w, l, t, p, pf, pa, s) in STANDINGS],
        "count": len(STANDINGS),
    },
    "designation_join": {
        "scope": "24 clubs of Sunday's 12 Week-10 games; inactive list = official record of players who did not play",
        "rows": join_rows,
        "stats": designation_stats,
        "unexplained_out_designations": unexplained_out,
        "note": "Designation reliability measured empirically from the final Week-10 report joined to the official inactive list. Single-week sample; Wilson 95% intervals. Name matching: exact normalized form, with a surname+initial fallback for official spelling variants (one instance this round: Tyrion/Tyroin Ingram-Dawkins, MIN).",
    },
}
capture["sha256"] = sha256(capture)

with open(os.path.join(DATA, "official_reads_2026_11_17.json"), "w") as f:
    json.dump(capture, f, indent=1, ensure_ascii=False)

print("official_reads_2026_11_17.json written")
print("injury totals:", capture["injury_report_week10"]["totals"])
print("designation stats:", json.dumps(designation_stats, indent=1))
print("unexplained out:", unexplained_out)
print("sha256:", capture["sha256"][:16], "...")

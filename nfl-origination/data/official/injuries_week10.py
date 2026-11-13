"""Week 10 official injury designations and confirmed lineup changes, transcribed 2026-11-13.

SOURCE A -- game-status designations for all 14 Week 10 games:
    https://www.nfl.com/news/nfl-week-10-injury-report-2026-season  (read directly, 2 chunks)
    Only players the official report assigns OUT / DOUBTFUL / QUESTIONABLE are listed.
    The report lists no designation for the rest of each roster; that is not the same as
    "healthy", so no player is ever recorded as available by inference.

SOURCE B -- confirmed starting-lineup / depth changes named in official NFL.com reporting:
    https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13
    https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11
    https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again
    https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start
    https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season

The official league site publishes NO depth chart: https://www.nfl.com/depth-charts/ returns a
404 page (re-read 2026-11-13). Therefore no 2nd/3rd/4th-string rank is assigned to anybody.
"STRING" below is only the word the official article itself used ("third-stringer") or is blank.
"""
import json
import pathlib

REPORT_URL = "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
ROUNDUP_FRI = "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"
ROUNDUP_WED = "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"
DEPTH_CHARTS_URL = "https://www.nfl.com/depth-charts/"
RETRIEVED = "2026-11-13"

# (club, player, position, injury, game_status) -- exactly as the official report publishes it
DESIGNATIONS = [
    # WAS @ NYG (Thu)
    ("WAS", "Colson Yankoff", "TE", "knee", "OUT"),
    ("WAS", "Lucas Patrick", "C", "concussion", "OUT"),
    ("NYG", "Malik Harrison", "LB", "groin", "QUESTIONABLE"),
    # NE @ DET
    ("NE", "TreVeyon Henderson", "RB", "illness", "OUT"),
    ("NE", "Ben Brown", "OL", "knee", "OUT"),
    ("NE", "Carlton Davis", "CB", "knee", "OUT"),
    ("NE", "Rhamondre Stevenson", "RB", "knee", "QUESTIONABLE"),
    ("NE", "Reggie Gilliam", "FB", "knee", "QUESTIONABLE"),
    ("NE", "A.J. Brown", "WR", "ankle/knee", "QUESTIONABLE"),
    ("NE", "Cameron Latu", "TE", "back", "QUESTIONABLE"),
    ("NE", "Walter Rouse", "OL", "concussion", "QUESTIONABLE"),
    ("NE", "Greg Van Roten", "OL", "hamstring", "QUESTIONABLE"),
    ("NE", "Charles Woods", "CB", "hamstring", "QUESTIONABLE"),
    ("NE", "Kevin Byard", "S", "chest", "QUESTIONABLE"),
    ("NE", "Brenden Schooler", "S", "hamstring", "QUESTIONABLE"),
    ("DET", "Kerby Joseph", "S", "knee", "OUT"),
    ("DET", "Cade Mays", "C", "ankle", "OUT"),
    ("DET", "D.J. Reed", "CB", "hip", "OUT"),
    ("DET", "Sione Vaki", "RB", "ankle", "QUESTIONABLE"),
    ("DET", "Amon-Ra St. Brown", "WR", "rib", "QUESTIONABLE"),
    # KC @ ATL
    ("KC", "Jaylon Moore", "OL", "ankle", "OUT"),
    ("KC", "Omarr Norman-Lott", "DT", "knee", "OUT"),
    ("KC", "Peter Woods", "DL", "neck", "OUT"),
    ("KC", "Jaydn Ott", "RB", "hamstring", "QUESTIONABLE"),
    ("KC", "Kenneth Walker III", "RB", "groin", "QUESTIONABLE"),
    ("KC", "Mansoor Delane", "CB", "shoulder", "QUESTIONABLE"),
    ("ATL", "Zachariah Branch", "WR", "hamstring", "OUT"),
    ("ATL", "Divine Deablo", "LB", "forearm", "DOUBTFUL"),
    ("ATL", "James Pearce Jr.", "DE", "back", "QUESTIONABLE"),
    ("ATL", "Gervon Dexter", "DT", "illness", "QUESTIONABLE"),
    ("ATL", "Josh Woods", "LB", "ankle", "QUESTIONABLE"),
    # HOU @ CLE
    ("HOU", "Marvin Harrison Jr.", "WR", "hamstring", "OUT"),
    ("HOU", "Brevin Jordan", "TE", "finger/foot", "OUT"),
    ("HOU", "Keylan Rutledge", "OL", "neck/shoulder", "OUT"),
    ("HOU", "Danielle Hunter", "DE", "hamstring", "OUT"),
    ("HOU", "Azeez Al-Shaair", "LB", "groin", "OUT"),
    ("HOU", "David Montgomery", "RB", "groin", "QUESTIONABLE"),
    ("HOU", "Trent Brown", "OT", "illness/wrist", "QUESTIONABLE"),
    ("HOU", "Wyatt Teller", "G", "back/illness", "QUESTIONABLE"),
    ("HOU", "Will Anderson Jr.", "DE", "ankle", "QUESTIONABLE"),
    ("HOU", "Jake Hummel", "LB", "groin", "QUESTIONABLE"),
    ("HOU", "Jaylin Smith", "CB", "hamstring", "QUESTIONABLE"),
    ("CLE", "Michael Burton", "FB", "calf", "OUT"),
    ("CLE", "Ronnie Hickman Jr.", "S", "concussion", "OUT"),
    ("CLE", "Denzel Boston", "WR", "toe", "QUESTIONABLE"),
    # MIN @ GB
    # The official report page renders no OUT/DOUBTFUL/QUESTIONABLE block for MIN or GB,
    # so this project records no designation for either club. See flag F-04.
    # MIA @ IND
    ("MIA", "Chris Bell", "WR", "knee", "QUESTIONABLE"),
    ("IND", "Mo Alie-Cox", "TE", "groin", "OUT"),
    ("IND", "Jalen Travis", "OT", "knee", "OUT"),
    ("IND", "Jerry Tillery", "DT", "calf", "OUT"),
    ("IND", "Jaylon Carlies", "LB", "neck", "OUT"),
    ("IND", "Akeem Davis-Gaither", "LB", "knee", "OUT"),
    ("IND", "Luke Rhodes", "LS", "hamstring", "OUT"),
    # CAR @ NO
    ("CAR", "Bobby Okereke", "LB", "foot", "OUT"),
    ("CAR", "Jonathon Brooks", "RB", "groin", "DOUBTFUL"),
    ("CAR", "Mike Jackson", "CB", "groin", "DOUBTFUL"),
    ("CAR", "Xavier Legette", "WR", "knee", "QUESTIONABLE"),
    ("CAR", "Brady Christensen", "OL", "hamstring", "QUESTIONABLE"),
    ("CAR", "Jaelan Phillips", "OLB", "hamstring", "QUESTIONABLE"),
    ("CAR", "Will Lee III", "CB", "hamstring", "QUESTIONABLE"),
    ("NO", "CJ Donaldson", "RB", "shoulder", "OUT"),
    ("NO", "Taliese Fuaga", "OT", "knee", "OUT"),
    ("NO", "Erik McCoy", "C", "biceps", "OUT"),
    ("NO", "Christen Miller", "DL", "knee", "OUT"),
    ("NO", "Travis Etienne", "RB", "hamstring", "QUESTIONABLE"),
    ("NO", "Martin Emerson", "CB", "shin", "QUESTIONABLE"),
    # BUF @ NYJ
    ("BUF", "Spencer Brown", "OT", "ankle", "DOUBTFUL"),
    ("BUF", "Tyrell Shavers", "WR", "knee", "QUESTIONABLE"),
    ("BUF", "Christian Benford", "CB", "wrist", "QUESTIONABLE"),
    ("BUF", "Sam Franklin", "DB", "shoulder", "QUESTIONABLE"),
    ("BUF", "Jordan Hancock", "DB", "hamstring", "QUESTIONABLE"),
    # JAX @ TEN
    ("JAX", "BJ Green II", "DE", "forearm", "OUT"),
    ("JAX", "Jordan Davis", "DT", "rest", "OUT"),
    ("JAX", "Jessie Bates", "S", "rest", "OUT"),
    ("JAX", "Robert Hainsey", "OL", "concussion", "QUESTIONABLE"),
    ("TEN", "Carnell Tate", "WR", "shoulder", "OUT"),
    ("TEN", "Peter Skoronski", "G", "hamstring", "OUT"),
    ("TEN", "Cody Barton", "LB", "concussion", "OUT"),
    ("TEN", "Anthony Hill Jr.", "LB", "neck", "OUT"),
    ("TEN", "Tommy Townsend", "P", "left knee/right Achilles", "OUT"),
    ("TEN", "Tyjae Spears", "RB", "knee", "QUESTIONABLE"),
    # LA @ AZ
    # The official report page renders no OUT/DOUBTFUL/QUESTIONABLE block for LAR or ARI.
    # See flag F-04.
    # SEA @ LV
    ("LV", "Trey Zuhn III", "C", "concussion", "QUESTIONABLE"),
    # SF @ DAL
    ("DAL", "Tyler Goodson", "RB", "ankle/knee", "OUT"),
    ("DAL", "Jonathan Mingo", "WR", "ankle", "OUT"),
    ("DAL", "Jake Ferguson", "TE", "knee/ankle", "OUT"),
    ("DAL", "Donovan Ezeiruaku", "LB", "ankle", "OUT"),
    ("DAL", "P.J. Locke", "S", "concussion", "OUT"),
    ("DAL", "George Pickens", "WR", "hamstring", "QUESTIONABLE"),
    ("DAL", "KaVontae Turpin", "WR", "ribs", "QUESTIONABLE"),
    ("DAL", "DeMarvion Overshown", "CB", "hamstring/back", "QUESTIONABLE"),
    ("DAL", "Joey Porter Jr.", "CB", "ankle", "QUESTIONABLE"),
    # PIT @ CIN
    ("PIT", "Derrick Harmon", "DT", "foot", "QUESTIONABLE"),
    ("CIN", "Kyle Dugger", "S", "quadricep", "OUT"),
    ("CIN", "Andrei Iosivas", "WR", "thumb", "DOUBTFUL"),
    ("CIN", "Brian Parker II", "G", "knee", "DOUBTFUL"),
    ("CIN", "Jalen Davis", "CB", "hamstring", "DOUBTFUL"),
    # LAC @ BAL
    # The official report renders no designation block for LAC or BAL. See flag F-04.
]

# Confirmed changes to who actually starts, each named by official NFL.com reporting.
# `string` is only filled when an official article uses that word for the player.
LINEUP_CHANGES = [
    {"club": "SEA", "out": "Sam Darnold", "out_pos": "QB", "in": "Drew Lock", "in_pos": "QB",
     "kind": "injury replacement — starter out, backup starts",
     "string": "", "why": "Darnold ruled out (quad, ribs); Lock expected to start a third straight game.",
     "side": "offence", "source": "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"},
    {"club": "MIA", "out": "Malik Willis", "out_pos": "QB", "in": "Kyle McCord", "in_pos": "QB",
     "kind": "injured reserve — backup into the lineup",
     "string": "", "why": "Willis to injured reserve (groin); McCord in line for his first NFL start.",
     "side": "offence", "source": "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"},
    {"club": "BAL", "out": "Lamar Jackson", "out_pos": "QB", "in": "Jacoby Brissett", "in_pos": "QB",
     "kind": "injured reserve — acquired replacement starts",
     "string": "", "why": "Jackson (right thumb, surgery) expected to miss 6-10 weeks; Huntley also on IR.",
     "side": "offence", "source": ROUNDUP_FRI},
    {"club": "BAL", "out": "Joe Fagnano", "out_pos": "QB", "in": "",
     "kind": "third-string start already played (Week 9)",
     "string": "third-stringer", "why": "Official article: Ravens 'were forced to start undrafted third-stringer Joe Fagnano' in Week 9.",
     "side": "offence", "source": "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season"},
    {"club": "MIN", "out": "Kyler Murray", "out_pos": "QB", "in": "Kirk Cousins", "in_pos": "QB",
     "kind": "depth-chart change — new starter announced",
     "string": "", "why": "Cousins will start vs. Packers (announced Friday by HC Kevin O'Connell).",
     "side": "offence", "source": ROUNDUP_FRI},
    {"club": "CLE", "out": "Shedeur Sanders", "out_pos": "QB", "in": "Deshaun Watson", "in_pos": "QB",
     "kind": "depth-chart change — starter swap",
     "string": "", "why": "Watson will start vs. Texans after Sanders started the Week 9 loss.",
     "side": "offence", "source": ROUNDUP_WED},
    {"club": "AZ", "out": "Jacoby Brissett", "out_pos": "QB", "in": "Carson Beck", "in_pos": "QB",
     "kind": "depth-chart change — rookie first career start",
     "string": "", "why": "Beck will start vs. Rams, per HC Mike LaFleur; Brissett traded to Baltimore.",
     "side": "offence", "source": ROUNDUP_WED},
    {"club": "SEA", "out": "Drew Lock", "out_pos": "QB", "in": "Jalen Milroe", "in_pos": "QB",
     "kind": "backup designation",
     "string": "", "why": "Rookie Milroe slated to back up Lock for the second straight week.",
     "side": "offence", "source": "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"},
]

# Clubs the official report provided no designation block for, within Week 10.
NO_DESIGNATION_BLOCK = ["MIN", "GB", "LA", "AZ", "LAC", "BAL"]


def summarise():
    """Counts used by the site. Pure arithmetic over the transcribed rows."""
    by_club = {}
    for club, player, pos, inj, status in DESIGNATIONS:
        c = by_club.setdefault(club, {"OUT": 0, "DOUBTFUL": 0, "QUESTIONABLE": 0, "total": 0})
        c[status] = c.get(status, 0) + 1
        c["total"] += 1
    return by_club


DOC = {
    "id": "injuries-week10-2026-11-13",
    "title": "Official Week 10 injury designations and confirmed lineup changes",
    "source_url": REPORT_URL,
    "supporting_sources": [ROUNDUP_FRI, ROUNDUP_WED],
    "depth_chart_url_checked": DEPTH_CHARTS_URL,
    "depth_chart_result": "HTTP 404 page ('404 - Flag on the Play.') re-read 2026-11-13",
    "retrieved": RETRIEVED,
    "columns": ["club", "player", "position", "injury", "game_status"],
    "designations": [list(d) for d in DESIGNATIONS],
    "lineup_changes": LINEUP_CHANGES,
    "no_designation_block": NO_DESIGNATION_BLOCK,
    "counts": summarise(),
    "limits": [
        "Only OUT / DOUBTFUL / QUESTIONABLE are published here. A player absent from this table "
        "has no published designation; that is not evidence of availability.",
        "No 2nd/3rd/4th-string rank exists in any official NFL source; nfl.com/depth-charts/ is a 404. "
        "String labels appear only where an official article itself used the word.",
        "The report has no historical archive; nfl.com/injuries/ serves the current week only, so no "
        "injury effect can be back-tested.",
        "Practice participation (DNP / limited / full) is published per club on nfl.com/injuries/ and "
        "is NOT transcribed here as a separate column; the game-status designation is the field used.",
    ],
}


def main():
    out = pathlib.Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(DOC, indent=1) + "\n")
    s = summarise()
    print("wrote", out.name, len(DESIGNATIONS), "designations across", len(s), "clubs;",
          len(LINEUP_CHANGES), "lineup changes")


if __name__ == "__main__":
    main()

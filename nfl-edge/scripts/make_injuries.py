#!/usr/bin/env python3
"""Build nfl-edge/data/injuries_week10.json.

Every row below was read by this session from the official NFL.com injuries page
(https://www.nfl.com/injuries/, 2026 season, Week 10) on 2026-11-12. The page shows, per club:
player, position, injury (where the club disclosed one), practice status and game status.
It does NOT show depth-chart rank, so no starter/backup label is recorded here.

Tuple layout: (player, position, injury, practice_status, game_status)
"""
import json, os

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

DNP = "Did Not Participate In Practice"
LIM = "Limited Participation in Practice"
FULL = "Full Participation in Practice"
SRC = "https://www.nfl.com/injuries/"

RAW = {
    "Commanders": ("WAS", [
        ("John Bates", "TE", "", FULL, ""), ("Treylon Burks", "WR", "", DNP, ""),
        ("Jayden Daniels", "QB", "", FULL, ""), ("Matt Gulbin", "C", "", FULL, ""),
        ("Chig Okonkwo", "TE", "", FULL, ""), ("Lucas Patrick", "C", "Concussion", DNP, "Out"),
        ("Amik Robertson", "CB", "", LIM, ""), ("Shy Tuttle", "DT", "", FULL, ""),
        ("Colson Yankoff", "TE", "Knee", DNP, "Out")]),
    "Giants": ("NYG", [
        ("Abdul Carter", "LB", "", FULL, ""), ("Jermaine Eluemunor", "T", "", FULL, ""),
        ("Malik Harrison", "LB", "Groin", LIM, "Questionable"), ("Colton Hood", "CB", "", FULL, ""),
        ("Theo Johnson", "TE", "", FULL, ""), ("Charlie Jones", "WR", "", FULL, ""),
        ("J.J. McCarthy", "QB", "", FULL, ""), ("Darnell Mooney", "WR", "", FULL, ""),
        ("Malik Nabers", "WR", "", FULL, ""), ("Cam Skattebo", "RB", "", FULL, ""),
        ("Andrew Thomas", "T", "", FULL, "")]),
    "Patriots": ("NE", [
        ("Ben Brown", "C", "Knee", DNP, "Out"), ("A.J. Brown", "WR", "", LIM, ""),
        ("Kevin Byard", "S", "", LIM, ""), ("Carlton Davis III", "CB", "Knee", DNP, "Out"),
        ("Reggie Gilliam", "FB", "", LIM, ""), ("TreVeyon Henderson", "RB", "Illness", DNP, "Out"),
        ("Hunter Henry", "TE", "", LIM, ""), ("Cameron Latu", "TE", "", DNP, ""),
        ("Drake Maye", "QB", "", FULL, ""), ("Morgan Moses", "T", "", LIM, ""),
        ("Walter Rouse", "T", "", DNP, ""), ("Brenden Schooler", "S", "", DNP, ""),
        ("Rhamondre Stevenson", "RB", "", DNP, ""), ("Greg Van Roten", "G", "", LIM, ""),
        ("Charles Woods", "CB", "", LIM, "")]),
    "Lions": ("DET", [
        ("Brian Branch", "S", "", LIM, ""), ("Jared Goff", "QB", "", LIM, ""),
        ("Kerby Joseph", "S", "", LIM, ""), ("Cade Mays", "C", "", DNP, ""),
        ("D.J. Reed", "CB", "", DNP, ""), ("Jacob Saylors", "RB", "", FULL, ""),
        ("Amon-Ra St. Brown", "WR", "", LIM, ""), ("Sione Vaki", "RB", "", DNP, ""),
        ("DJ Wonnum", "DE", "", FULL, "")]),
    "Chiefs": ("KC", [
        ("Jeffrey Bassa", "LB", "", FULL, ""), ("Mansoor Delane", "CB", "", FULL, ""),
        ("Justin Fields", "QB", "", FULL, ""), ("Jaden Hicks", "S", "", FULL, ""),
        ("Travis Kelce", "TE", "", FULL, ""), ("Patrick Mahomes", "QB", "", FULL, ""),
        ("Jaylon Moore", "T", "", DNP, ""), ("Omarr Norman-Lott", "DT", "", LIM, ""),
        ("Rashee Rice", "WR", "", FULL, ""), ("Peter Woods", "DT", "", DNP, ""),
        ("Xavier Worthy", "WR", "", FULL, "")]),
    "Falcons": ("ATL", [
        ("Zachariah Branch", "WR", "", DNP, ""), ("Divine Deablo", "LB", "", LIM, ""),
        ("Gervon Dexter Sr.", "DT", "", DNP, ""), ("James Pearce Jr.", "DE", "", DNP, ""),
        ("Za'Darius Smith", "DE", "", DNP, ""), ("Josh Woods", "LB", "", DNP, "")]),
    "Vikings": ("MIN", [
        ("Blake Cashman", "LB", "", DNP, ""), ("T.J. Hockenson", "TE", "", DNP, ""),
        ("Tyrion Ingram-Dawkins", "DT", "", DNP, ""), ("Theo Jackson", "S", "", FULL, ""),
        ("Jauan Jennings", "WR", "", DNP, ""), ("Kyler Murray", "QB", "", DNP, ""),
        ("Kyle Van Noy", "LB", "", DNP, ""), ("Jay Ward", "S", "", LIM, ""),
        ("Carson Wentz", "QB", "", LIM, "")]),
    "Packers": ("GB", [
        ("Aaron Banks", "G", "", LIM, ""), ("Chris Brooks", "RB", "", LIM, ""),
        ("Javon Bullard", "S", "", DNP, ""), ("Zaire Franklin", "LB", "", DNP, ""),
        ("Travis Glover", "G", "", LIM, ""), ("Ty'Ron Hopper", "LB", "", LIM, ""),
        ("Josh Jacobs", "RB", "", DNP, ""), ("Bo Melton", "WR", "", FULL, ""),
        ("Skyy Moore", "WR", "", LIM, ""), ("Micah Parsons", "LB", "", LIM, ""),
        ("Sean Rhyan", "C", "", DNP, ""), ("Trey Smack", "K", "", LIM, ""),
        ("Lukas Van Ness", "LB", "", DNP, ""), ("Josh Whyle", "TE", "", DNP, ""),
        ("Savion Williams", "WR", "", LIM, ""), ("Kevin Zeitler", "G", "", LIM, "")]),
    "Jaguars": ("JAX", [
        ("Jessie Bates", "S", "", DNP, ""), ("Ezra Cleveland", "G", "", LIM, ""),
        ("Branson Combs", "LB", "", LIM, ""), ("Jordan Davis", "DT", "", DNP, ""),
        ("Robert Hainsey", "C", "", LIM, ""), ("Antonio Johnson", "S", "", LIM, ""),
        ("Jakobi Meyers", "WR", "", DNP, ""), ("Chris Rodriguez Jr.", "RB", "", LIM, ""),
        ("Bhayshul Tuten", "RB", "", DNP, ""), ("Travon Walker", "DE", "", DNP, "")]),
    "Titans": ("TEN", [
        ("Cody Barton", "LB", "", DNP, ""), ("John Franklin-Myers", "DE", "", FULL, ""),
        ("Marcus Harris", "CB", "", FULL, ""), ("Anthony Hill Jr.", "LB", "", DNP, ""),
        ("Jaylon Jones", "CB", "", FULL, ""), ("JC Latham", "T", "", FULL, ""),
        ("Tony Pollard", "RB", "", FULL, ""), ("Peter Skoronski", "G", "", DNP, ""),
        ("Tyjae Spears", "RB", "", DNP, ""), ("Carnell Tate", "WR", "", DNP, ""),
        ("Tommy Townsend", "P", "", FULL, ""), ("Kevin Winston Jr.", "S", "", FULL, "")]),
    "Bills": ("BUF", [
        ("Christian Benford", "CB", "", LIM, ""), ("Spencer Brown", "T", "", LIM, ""),
        ("Dion Dawkins", "T", "", LIM, ""), ("Greg Gaines", "DT", "", FULL, ""),
        ("Jordan Hancock", "CB", "", FULL, ""), ("Dalton Kincaid", "TE", "", LIM, ""),
        ("Connor McGovern", "C", "", LIM, ""), ("Ar'maj Reed-Adams", "G", "", FULL, ""),
        ("T.J. Sanders", "DE", "", FULL, ""), ("Tyrell Shavers", "WR", "", FULL, "")]),
    "Jets": ("NYJ", [
        ("Omar Cooper Jr.", "WR", "", LIM, ""), ("Joseph Ossai", "DE", "", LIM, ""),
        ("VJ Payne", "S", "", FULL, ""), ("Harrison Phillips", "DT", "", DNP, ""),
        ("Trevin Wallace", "LB", "", DNP, ""), ("Garrett Wilson", "WR", "", LIM, ""),
        ("Nahshon Wright", "CB", "", LIM, "")]),
    "Dolphins": ("MIA", [
        ("Tucker Addington", "LS", "", LIM, ""), ("Kaytron Allen", "RB", "", FULL, ""),
        ("Darrell Baker Jr.", "CB", "", LIM, ""), ("Chris Bell", "WR", "", LIM, ""),
        ("Aaron Brewer", "C", "", DNP, ""), ("Malik Herring", "DE", "", LIM, ""),
        ("Will Kacmarek", "TE", "", DNP, ""), ("Michael Taaffe", "S", "", FULL, ""),
        ("Dante Trader Jr.", "S", "", FULL, ""), ("Jaylen Wright", "RB", "", FULL, "")]),
    "Colts": ("IND", [
        ("Mo Alie-Cox", "TE", "", DNP, ""), ("Jaylon Carlies", "LB", "", DNP, ""),
        ("Akeem Davis-Gaither", "LB", "", DNP, ""), ("A.J. Haulcy", "S", "", DNP, ""),
        ("Arden Key", "DE", "", FULL, ""), ("Luke Rhodes", "LS", "", DNP, ""),
        ("Jonathan Taylor", "RB", "", LIM, ""), ("Jerry Tillery", "DT", "", LIM, ""),
        ("Jalen Travis", "T", "", DNP, ""), ("Justin Walley", "CB", "", FULL, ""),
        ("Charvarius Ward", "CB", "", DNP, "")]),
    "Panthers": ("CAR", [
        ("Jonathon Brooks", "RB", "", FULL, ""), ("Brady Christensen", "G", "", FULL, ""),
        ("Trevor Etienne", "RB", "", FULL, ""), ("Chuba Hubbard", "RB", "", DNP, ""),
        ("Lee Hunter", "DT", "", FULL, ""), ("Mike Jackson", "CB", "", FULL, ""),
        ("Will Lee III", "CB", "", FULL, ""), ("Xavier Legette", "WR", "", FULL, ""),
        ("Damien Lewis", "G", "", FULL, ""), ("Bobby Okereke", "LB", "", DNP, ""),
        ("Jaelan Phillips", "LB", "", FULL, ""), ("Torricelli Simpkins III", "G", "", FULL, "")]),
    "Saints": ("NO", [
        ("Kelvin Banks Jr.", "T", "", LIM, ""), ("CJ Donaldson", "RB", "", DNP, ""),
        ("David Edwards", "G", "", LIM, ""), ("Martin Emerson", "CB", "", LIM, ""),
        ("Travis Etienne", "RB", "", LIM, ""), ("Noah Fant", "TE", "", LIM, ""),
        ("Alvin Kamara", "RB", "", DNP, ""), ("Erik McCoy", "C", "", DNP, ""),
        ("Christen Miller", "DT", "", LIM, ""), ("Asim Richards", "T", "", FULL, "")]),
    "Texans": ("HOU", [
        ("Azeez Al-Shaair", "LB", "", DNP, ""), ("Reed Blankenship", "S", "", LIM, ""),
        ("Tank Dell", "WR", "", LIM, ""), ("Blake Fisher", "T", "", FULL, ""),
        ("Marvin Harrison Jr.", "WR", "", LIM, ""), ("Jacob Hummel", "LB", "", LIM, ""),
        ("Brevin Jordan", "TE", "", DNP, ""), ("Woody Marks", "RB", "", LIM, ""),
        ("David Montgomery", "RB", "", DNP, ""), ("Keylan Rutledge", "G", "", DNP, ""),
        ("Jaylin Smith", "CB", "", LIM, ""), ("Wyatt Teller", "G", "", LIM, ""),
        ("Tommy Togiai", "DT", "", FULL, "")]),
    "Browns": ("CLE", [
        ("Austin Barber", "T", "", LIM, ""), ("Denzel Boston", "WR", "", DNP, ""),
        ("Michael Burton", "FB", "", DNP, ""), ("Maliek Collins", "DT", "", LIM, ""),
        ("Harold Fannin Jr.", "TE", "", LIM, ""), ("Ronnie Hickman Jr.", "S", "", DNP, ""),
        ("Tytus Howard", "T", "", LIM, ""), ("Elgton Jenkins", "C", "", DNP, ""),
        ("Carson Schwesinger", "LB", "", LIM, ""), ("Denzel Ward", "CB", "", LIM, ""),
        ("Quincy Williams", "LB", "", LIM, "")]),
    "Rams": ("LA", [
        ("Davis Allen", "TE", "", LIM, ""), ("Steve Avila", "G", "", DNP, ""),
        ("Joe Cardona", "LS", "", LIM, ""), ("Kam Curl", "S", "", DNP, ""),
        ("Terrance Ferguson", "TE", "", DNP, ""), ("Myles Garrett", "LB", "", LIM, ""),
        ("Trent McDuffie", "CB", "", DNP, ""), ("Puka Nacua", "WR", "", DNP, ""),
        ("Colby Parkinson", "TE", "", LIM, ""), ("Matthew Stafford", "QB", "", FULL, "")]),
    "Cardinals": ("AZ", [
        ("Budda Baker", "S", "", DNP, ""), ("Zachary Carter", "DT", "", LIM, ""),
        ("Hjalte Froholdt", "C", "", DNP, ""), ("Jon Gaines II", "G", "", DNP, ""),
        ("Bam Knight", "RB", "", LIM, ""), ("Hunter Long", "TE", "", LIM, ""),
        ("Roy Lopez", "DT", "", DNP, ""), ("Max Melton", "CB", "", LIM, ""),
        ("Isaac Seumalo", "G", "", DNP, ""), ("Dante Stills", "DT", "", LIM, ""),
        ("Josh Sweat", "LB", "", DNP, ""), ("Jayden Williams", "T", "", LIM, ""),
        ("Mack Wilson", "LB", "", DNP, ""), ("Andrew Wingard", "S", "", LIM, "")]),
    "Seahawks": ("SEA", [
        ("AJ Barner", "TE", "", FULL, ""), ("Anthony Bradford", "G", "", LIM, ""),
        ("Charles Cross", "T", "", DNP, ""), ("Sam Darnold", "QB", "", DNP, ""),
        ("Derick Hall", "LB", "", LIM, ""), ("Drew Lock", "QB", "", LIM, ""),
        ("Quenton Nelson", "G", "", DNP, ""), ("Uchenna Nwosu", "LB", "", LIM, ""),
        ("Patrick O'Connell", "LB", "", LIM, ""), ("Connor O'Toole", "LB", "", LIM, ""),
        ("Brandon Pili", "DT", "", DNP, ""), ("Jarran Reed", "DT", "", DNP, ""),
        ("Rashid Shaheed", "WR", "", FULL, ""), ("Jaxon Smith-Njigba", "WR", "", DNP, ""),
        ("Leonard Williams", "DT", "", DNP, "")]),
    "Raiders": ("LV", [
        ("Thomas Booker", "DT", "", LIM, ""), ("Foley Fatukasi", "DT", "", LIM, ""),
        ("Ian Thomas", "TE", "", FULL, ""), ("Trey Zuhn III", "C", "", LIM, "")]),
    "49ers": ("SF", [
        ("Mike Evans", "WR", "", DNP, ""), ("Renardo Green", "CB", "", DNP, ""),
        ("Dre Greenlaw", "LB", "", DNP, ""), ("Nate Hobbs", "CB", "", FULL, ""),
        ("Deommodore Lenoir", "CB", "", DNP, ""), ("Christian McCaffrey", "RB", "", DNP, ""),
        ("Siran Neal", "S", "", LIM, ""), ("Demarcus Robinson", "WR", "", FULL, ""),
        ("Deebo Samuel Sr.", "WR", "", LIM, ""), ("Upton Stout", "CB", "", LIM, ""),
        ("C.J. West", "DT", "", LIM, ""), ("Trent Williams", "T", "", DNP, "")]),
    "Cowboys": ("DAL", [
        ("Jonathan Bullard", "DT", "", FULL, ""), ("Donovan Ezeiruaku", "LB", "", DNP, ""),
        ("Jake Ferguson", "TE", "", DNP, ""), ("Tyler Goodson", "RB", "", DNP, ""),
        ("Malik Hooker", "S", "", DNP, ""), ("Marist Liufau", "LB", "", FULL, ""),
        ("P.J. Locke", "S", "", DNP, ""), ("Von Miller", "LB", "", DNP, ""),
        ("Jonathan Mingo", "WR", "", DNP, ""), ("Devin Moore", "CB", "", FULL, ""),
        ("DeMarvion Overshown", "LB", "", LIM, ""), ("George Pickens", "WR", "", LIM, ""),
        ("Joey Porter Jr.", "CB", "", DNP, ""), ("Luke Schoonmaker", "TE", "", FULL, ""),
        ("Brevyn Spann-Ford", "TE", "", FULL, ""), ("KaVontae Turpin", "WR", "", LIM, "")]),
    "Steelers": ("PIT", [
        ("Brandin Echols", "CB", "", FULL, ""), ("DeShon Elliott", "S", "", LIM, ""),
        ("Derrick Harmon", "DT", "", LIM, ""), ("Cameron Heyward", "DT", "", DNP, ""),
        ("Ben Skowronek", "WR", "", FULL, ""), ("Doneiko Slaughter", "CB", "", FULL, ""),
        ("Darnell Washington", "TE", "", DNP, ""), ("T.J. Watt", "LB", "", DNP, "")]),
    "Bengals": ("CIN", [
        ("Jonathan Allen", "DT", "", DNP, ""), ("Kyle Dugger", "S", "", DNP, ""),
        ("Dylan Fairchild", "G", "", LIM, ""), ("DJ Turner II", "CB", "", LIM, "")]),
    "Chargers": ("LAC", []),
    "Ravens": ("BAL", []),
}


def main():
    teams = []
    for club, (abbr, players) in RAW.items():
        rows = [{"player": p, "position": pos, "injury": inj, "practice_status": prac,
                 "game_status": status, "source_url": SRC} for p, pos, inj, prac, status in players]
        teams.append({
            "club": club, "team": abbr, "n_players_listed": len(rows), "players": rows,
            "source_url": SRC, "club_page": "https://www.nfl.com/teams/",
            "note": "No injuries reported" if not rows else "",
            "starter_or_backup": "NOT PUBLISHED (see flag F-03)",
        })
    payload = {
        "dataset": "injuries_week10_2026",
        "title": "Official NFL Week 10 (2026) injury report - practice participation and game status",
        "captured_utc": "2026-11-12",
        "source_url": SRC,
        "read_from": "Official NFL.com injuries page for Week 10 of the 2026 season, read 2026-11-12. The page "
                     "lists practice status and game status. It does not publish depth-chart rank, so this "
                     "dataset makes no starter/backup claim; the prohibition is recorded per club.",
        "columns": ["player", "position", "injury", "practice_status", "game_status", "source_url"],
        "n_clubs": len(teams),
        "n_players": sum(len(t["players"]) for t in teams),
        "teams": teams,
    }
    out = os.path.join(D, "injuries_week10.json")
    json.dump(payload, open(out, "w"), indent=1)
    print("wrote", out, payload["n_clubs"], "clubs", payload["n_players"], "players")


if __name__ == "__main__":
    main()

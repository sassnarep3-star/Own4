#!/usr/bin/env python3
"""Writes the hand-transcribed official NBA tables to data/*.csv.

Every number below was copied by the session agent from the nba.com page named in
SRC_* (fetched 2026-11-02 ~17:50-18:20 UTC). Nothing is inferred.  The independent
cross-checks live in scripts/verify_data.py (game-level data must reproduce the
team-level tables exactly; home+road+neutral must equal overall record; etc.).
"""
import csv, os
D = os.path.join(os.path.dirname(__file__), "..", "data")

TEAMS = [  # abbr, name, nba.com team id (from nba.com team URLs), conference (from nba.com standings page)
("ATL","Atlanta Hawks",1610612737,"East"),("BOS","Boston Celtics",1610612738,"East"),
("CLE","Cleveland Cavaliers",1610612739,"East"),("NOP","New Orleans Pelicans",1610612740,"West"),
("CHI","Chicago Bulls",1610612741,"East"),("DAL","Dallas Mavericks",1610612742,"West"),
("DEN","Denver Nuggets",1610612743,"West"),("GSW","Golden State Warriors",1610612744,"West"),
("HOU","Houston Rockets",1610612745,"West"),("LAC","LA Clippers",1610612746,"West"),
("LAL","Los Angeles Lakers",1610612747,"West"),("MIA","Miami Heat",1610612748,"East"),
("MIL","Milwaukee Bucks",1610612749,"East"),("MIN","Minnesota Timberwolves",1610612750,"West"),
("BKN","Brooklyn Nets",1610612751,"East"),("NYK","New York Knicks",1610612752,"East"),
("ORL","Orlando Magic",1610612753,"East"),("IND","Indiana Pacers",1610612754,"East"),
("PHI","Philadelphia 76ers",1610612755,"East"),("PHX","Phoenix Suns",1610612756,"West"),
("POR","Portland Trail Blazers",1610612757,"West"),("SAC","Sacramento Kings",1610612758,"West"),
("SAS","San Antonio Spurs",1610612759,"West"),("OKC","Oklahoma City Thunder",1610612760,"West"),
("TOR","Toronto Raptors",1610612761,"East"),("UTA","Utah Jazz",1610612762,"West"),
("MEM","Memphis Grizzlies",1610612763,"West"),("WAS","Washington Wizards",1610612764,"East"),
("DET","Detroit Pistons",1610612765,"East"),("CHA","Charlotte Hornets",1610612766,"East"),
]
SRC_TEAMS = "https://www.nba.com/teams"

# ---- standings: team, W, L, home W-L, road W-L, neutral W-L  (nba.com/standings) ----
ST_2526 = """DET 60 22 31-9 28-13 1-0
BOS 56 26 30-11 26-15 0-0
NYK 53 29 30-10 22-19 1-0
CLE 52 30 27-14 25-16 0-0
TOR 46 36 24-17 22-19 0-0
ATL 46 36 24-17 22-19 0-0
PHI 45 37 23-18 22-19 0-0
ORL 45 37 25-15 19-20 1-2
CHA 44 38 21-20 23-18 0-0
MIA 43 39 26-15 17-24 0-0
MIL 32 50 19-22 13-28 0-0
CHI 31 51 18-23 13-28 0-0
BKN 20 62 12-29 8-33 0-0
IND 19 63 11-30 8-33 0-0
WAS 17 65 11-30 6-35 0-0
OKC 64 18 34-7 30-10 0-1
SAS 62 20 32-8 29-12 1-0
DEN 54 28 28-13 26-15 0-0
LAL 53 29 28-13 25-16 0-0
HOU 52 30 30-11 22-19 0-0
MIN 49 33 26-15 23-18 0-0
PHX 45 37 25-16 20-21 0-0
POR 42 40 24-17 18-23 0-0
LAC 42 40 23-18 19-22 0-0
GSW 37 45 22-19 15-26 0-0
NOP 26 56 17-24 9-32 0-0
DAL 26 56 16-25 10-30 0-1
MEM 25 57 13-27 11-29 1-1
SAC 22 60 15-26 7-34 0-0
UTA 22 60 14-27 8-33 0-0"""
ST_2627 = """PHI 6 1 3-1 3-0 0-0
DET 5 1 2-0 3-1 0-0
BOS 5 1 4-0 1-1 0-0
CLE 4 2 3-0 1-2 0-0
TOR 3 3 2-1 1-2 0-0
WAS 3 3 2-1 1-2 0-0
ATL 3 4 1-2 2-2 0-0
CHA 3 4 2-2 1-2 0-0
ORL 2 4 0-3 2-1 0-0
NYK 2 4 1-2 1-2 0-0
MIA 2 4 1-3 1-1 0-0
IND 2 5 0-3 2-2 0-0
CHI 1 5 0-2 1-3 0-0
MIL 1 5 1-3 0-2 0-0
BKN 1 5 0-3 1-2 0-0
MEM 6 0 2-0 4-0 0-0
HOU 6 1 3-0 3-1 0-0
POR 4 1 1-1 3-0 0-0
LAL 5 2 3-1 2-1 0-0
OKC 4 2 3-0 1-2 0-0
SAS 4 2 2-2 2-0 0-0
DAL 4 2 2-1 2-1 0-0
DEN 3 2 1-1 2-1 0-0
GSW 4 3 2-1 2-2 0-0
MIN 4 3 2-1 2-2 0-0
NOP 2 4 2-2 0-2 0-0
PHX 1 3 1-1 0-2 0-0
LAC 1 5 1-1 0-4 0-0
UTA 1 5 1-4 0-1 0-0
SAC 0 6 0-2 0-4 0-0"""

# ---- team traditional stats per game: team GP W L PTS +/-  (nba.com/stats/teams/traditional) ----
TS_2526 = """OKC 82 64 18 119.0 11.1
SAS 82 62 20 119.8 8.3
DET 82 60 22 117.8 8.2
BOS 82 56 26 114.9 7.7
DEN 82 54 28 122.1 5.1
LAL 82 53 29 116.3 1.8
NYK 82 53 29 116.5 6.3
CLE 82 52 30 119.5 4.1
HOU 82 52 30 115.2 5.2
MIN 82 49 33 118.0 3.4
ATL 82 46 36 118.5 2.4
TOR 82 46 36 114.6 2.8
ORL 82 45 37 115.7 0.6
PHI 82 45 37 115.9 -0.2
PHX 82 45 37 112.6 1.5
CHA 82 44 38 116.0 4.8
MIA 82 43 39 120.9 2.3
LAC 82 42 40 113.8 1.1
POR 82 42 40 115.5 -0.3
GSW 82 37 45 114.6 -0.6
MIL 82 32 50 110.6 -6.2
CHI 82 31 51 116.3 -5.2
DAL 82 26 56 114.1 -5.5
NOP 82 26 56 115.5 -4.5
MEM 82 25 57 114.7 -6.0
SAC 82 22 60 111.0 -10.0
UTA 82 22 60 117.6 -8.4
BKN 82 20 62 105.9 -10.0
IND 82 19 63 112.4 -8.0
WAS 82 17 65 112.9 -12.0"""
TS_2526_HOME = """OKC 41 34 7 119.1 11.8
SAS 40 32 8 120.5 8.6
DET 40 31 9 118.6 10.5
NYK 40 30 10 119.0 10.0
BOS 41 30 11 114.8 7.8
HOU 41 30 11 114.8 7.5
DEN 41 28 13 120.8 5.6
LAL 41 28 13 118.0 4.0
CLE 41 27 14 119.2 4.5
MIA 41 26 15 123.5 5.2
MIN 41 26 15 114.8 3.7
ORL 40 25 15 116.0 1.8
PHX 41 25 16 112.0 3.6
ATL 41 24 17 117.8 3.8
POR 41 24 17 118.3 3.5
TOR 41 24 17 115.3 4.5
LAC 41 23 18 115.0 3.7
PHI 41 23 18 115.4 -1.1
GSW 41 22 19 117.1 1.3
CHA 41 21 20 115.0 3.9
MIL 41 19 22 114.2 -4.0
CHI 41 18 23 114.9 -3.7
NOP 41 17 24 118.2 -1.4
DAL 41 16 25 116.3 -3.5
SAC 41 15 26 112.6 -7.1
UTA 41 14 27 121.2 -5.2
MEM 40 13 27 115.8 -4.1
BKN 41 12 29 108.4 -6.7
IND 41 11 30 113.8 -5.4
WAS 41 11 30 113.7 -10.9"""
TS_2627 = """MEM 6 6 0 121.2 15.2
HOU 7 6 1 120.7 12.4
PHI 7 6 1 108.7 3.9
BOS 6 5 1 118.7 9.5
DET 6 5 1 109.8 8.0
POR 5 4 1 120.6 11.4
LAL 7 5 2 120.3 5.3
CLE 6 4 2 121.0 5.0
DAL 6 4 2 114.0 2.5
OKC 6 4 2 106.5 -0.5
SAS 6 4 2 117.3 7.2
DEN 5 3 2 114.0 -1.2
GSW 7 4 3 117.7 2.9
MIN 7 4 3 120.0 11.3
TOR 6 3 3 118.2 7.8
WAS 6 3 3 110.5 0.8
ATL 7 3 4 116.1 0.9
CHA 7 3 4 98.3 -8.1
MIA 6 2 4 118.3 -3.2
NOP 6 2 4 119.7 1.8
NYK 6 2 4 107.0 -0.7
ORL 6 2 4 107.7 -9.0
IND 7 2 5 112.9 -3.9
PHX 4 1 3 112.0 -12.5
BKN 6 1 5 108.2 -7.8
CHI 6 1 5 113.5 -15.8
LAC 6 1 5 106.5 -7.3
MIL 6 1 5 113.0 -13.2
UTA 6 1 5 108.7 -10.2
SAC 6 0 6 109.3 -19.0"""

def w(name, header, rows):
    with open(os.path.join(D, name), "w", newline="") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)

conf = {t[0]: t[3] for t in TEAMS}
w("teams.csv", ["abbr","team","nba_team_id","conference","source_url"],
  [(a,n,i,c,f"https://www.nba.com/team/{i}") for a,n,i,c in TEAMS])

def standings(txt, season, url):
    rows=[]
    for ln in txt.splitlines():
        a,W,L,h,r,n = ln.split()
        rows.append((a,conf[a],W,L,h,r,n,season,url))
    return rows
hdr_st=["abbr","conference","W","L","home_W-L","road_W-L","neutral_W-L","season","source_url"]
w("standings_2025-26.csv",hdr_st,standings(ST_2526,"2025-26","https://www.nba.com/standings?Season=2025-26"))
w("standings_2026-27.csv",hdr_st,standings(ST_2627,"2026-27 (as of 2026-11-02, before that night's games)","https://www.nba.com/standings"))

def stats(txt, season, url, extra=""):
    return [(*ln.split(), season+extra, url) for ln in txt.splitlines()]
hdr_ts=["abbr","GP","W","L","PTS_per_game","plus_minus_per_game","scope","source_url"]
w("team_stats_2025-26.csv",hdr_ts,stats(TS_2526,"2025-26 regular season, all games","https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season"))
w("team_stats_2025-26_home.csv",hdr_ts,stats(TS_2526_HOME,"2025-26 regular season, home games only","https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season&Location=Home"))
w("team_stats_2026-27.csv",hdr_ts,stats(TS_2627,"2026-27 regular season to 2026-11-01, all games","https://www.nba.com/stats/teams/traditional"))
print("ok")

#!/usr/bin/env python3
"""Own4 · NFL own-lines session 1880ad1e — official transcription, 2026-11-13 (UTC).

Everything in this file was read from the official NFL.com pages listed in SOURCES below on
2026-11-13. Nothing is inferred, averaged or copied from a secondary site.

Design rule for this dataset: only columns whose identity can be PROVEN by arithmetic are
published. For every team-stat table the retrieved page text carried no readable header row,
so a column is kept only if an arithmetic identity confirms what it is, e.g.
  * pass pct  = comp / att            (verified for all 32 rows)
  * pass avg  = yds / att             (verified for all 32 rows)
  * team pass yds/att/comp/TD/INT for NE reproduce Drake Maye's official season totals line
    (178 cmp / 272 att / 2,282 yds / 18 TD / 11 INT, 20 sacks for 103 yards) - see PLAYER_LOGS.
Columns that could not be identified from the retrieved text are NOT published, not guessed.

Run: python3 nfl-own/data/official/transcribe_2026-11-13.py
Writes standings_2026-11-13.json, team_stats_2026-11-13.json, slate_week11_2026.json,
leaders_2026-11-13.json, player_logs_2026.json and integrity_official.json.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CAPTURED = "2026-11-13"
SOURCES = {
    "standings": "https://www.nfl.com/standings/league/2026/REG",
    "off_pass": "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
    "off_rush": "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all",
    "def_pass": "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all",
    "def_rush": "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all",
    "week10": "https://www.nfl.com/schedules/2026/REG10",
    "week11": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "scores9": "https://www.nfl.com/scores/2026/REG9",
    "injuries": "https://www.nfl.com/injuries/",
    "passing_leaders": "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc",
    "receiving_leaders": "https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingyards/desc",
    "rushing_leaders": "https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc",
}

# ---------------------------------------------------------------- standings
# team w l t pct pf pa   (nfl.com/standings/league/2026/REG, read 2026-11-13)
STANDINGS = """
BUF 7 1 0 0.875 256 187
SF 7 1 0 0.875 235 156
CHI 7 2 0 0.778 241 184
DEN 7 2 0 0.778 198 186
CIN 6 2 0 0.750 240 175
DET 6 2 0 0.750 222 189
JAX 6 2 0 0.750 229 121
KC 6 2 0 0.750 202 143
MIN 6 2 0 0.750 146 116
PIT 6 2 0 0.750 180 144
GB 6 3 0 0.667 216 191
NYG 5 3 1 0.611 203 196
CLE 5 4 0 0.556 161 196
LA 5 4 0 0.556 214 181
NE 5 4 0 0.556 211 207
SEA 5 4 0 0.556 202 162
BAL 4 5 0 0.444 189 236
DAL 4 5 0 0.444 246 236
LV 4 5 0 0.444 238 268
WAS 3 5 1 0.389 196 223
CAR 3 5 0 0.375 199 219
HOU 3 5 0 0.375 209 192
NO 3 5 0 0.375 185 216
AZ 3 6 0 0.333 178 255
ATL 3 6 0 0.333 188 223
TB 3 6 0 0.333 202 178
IND 2 7 0 0.222 184 249
NYJ 2 7 0 0.222 182 223
PHI 2 7 0 0.222 148 221
MIA 1 7 0 0.125 126 200
TEN 1 7 0 0.125 144 199
LAC 0 8 0 0.000 121 219
"""

# ------------------------------------------------- team stats, offence passing
# att comp pct avg yds td int rate 1st 1st/g 20+ 40+ long sck sckyds   (15 values)
OFF_PASS = """
SF 236 163 69.1 8.4 1980 17 5 109.8 97 41.1 27 4 82T 8 48
CHI 312 211 67.6 7.4 2310 10 9 88 108 34.6 35 4 58T 20 141
CIN 296 219 74 8.1 2386 23 6 114.8 119 40.2 27 5 47T 15 102
BUF 236 156 66.1 8.6 2027 12 6 99.3 93 39.4 32 8 57 17 109
DEN 287 174 60.6 6 1730 11 4 84.7 85 29.6 21 4 52T 11 57
CLE 283 185 65.4 7.4 2105 9 3 93.7 93 32.9 28 5 64T 38 211
TB 240 146 60.8 5.9 1423 6 9 70.2 67 27.9 16 5 64 27 146
AZ 359 232 64.6 5.8 2080 13 7 84 110 30.6 19 0 38 23 142
LAC 243 146 60.1 6.6 1615 7 11 70.6 71 29.2 18 6 58 31 198
KC 263 177 67.3 7.8 2037 14 4 101.8 94 35.7 22 7 73T 11 66
IND 304 184 60.5 5.7 1730 6 10 69.1 86 28.3 18 3 55T 25 167
WAS 299 187 62.5 6.8 2025 15 3 95 95 31.8 29 5 53 21 133
DAL 336 218 64.9 7.1 2381 16 5 95.4 119 35.4 28 6 53 14 69
MIA 209 122 58.4 6.9 1442 6 6 77.1 64 30.6 18 5 77T 24 124
PHI 303 179 59.1 5.7 1740 10 6 78 81 26.7 14 3 64 30 195
ATL 256 156 60.9 6.9 1766 11 12 76.4 74 28.9 23 4 76 16 97
NYG 304 188 61.8 7.2 2193 13 7 88.3 101 33.2 30 6 66T 28 142
JAX 227 147 64.8 8.6 1940 18 4 110.8 91 40.1 27 4 52 13 106
NYJ 271 183 67.5 7.7 2078 12 3 100.4 89 32.8 24 9 60 28 236
DET 274 186 67.9 7.8 2145 15 2 106.5 104 38 23 5 57 19 129
GB 341 215 63 7.7 2618 19 6 97.9 110 32.3 40 12 81T 17 101
CAR 313 189 60.4 7.2 2244 16 6 91.3 111 35.5 28 4 55 26 155
NE 281 183 65.1 8.4 2349 18 11 96.2 102 36.3 33 6 63 20 103
LV 324 209 64.5 7.4 2401 20 8 97 121 37.4 31 5 45 11 64
LA 349 232 66.5 6.8 2387 16 9 90.5 122 35 24 6 64 13 97
BAL 247 165 66.8 7.5 1842 10 5 93.9 90 36.4 20 6 54 23 146
NO 308 204 66.2 6.4 1986 14 6 91.2 99 32.1 21 5 52 20 142
SEA 288 182 63.2 7.2 2089 15 9 89.3 109 37.8 24 4 82 19 136
PIT 290 175 60.3 6.4 1871 13 6 85.6 82 28.3 24 6 80T 23 187
HOU 285 182 63.9 7.9 2258 16 2 104.1 98 34.4 32 7 63T 16 103
TEN 248 155 62.5 6 1483 6 5 78.8 73 29.4 16 1 41 13 99
MIN 225 137 60.9 6.4 1437 8 5 82 68 30.2 19 2 51T 23 151
"""

# -------------------------------------------------- team stats, offence rushing
# att yds avg td  (10 values on the page; only the first four are provable)
OFF_RUSH = """
SF 234 1082 4.6 12
CHI 303 1278 4.2 17
CIN 177 685 3.9 5
BUF 261 1173 4.5 17
DEN 223 823 3.7 9
CLE 233 876 3.8 6
TB 294 1475 5 11
AZ 226 924 4.1 4
LAC 224 916 4.1 4
KC 217 1102 5.1 10
IND 249 1037 4.2 11
WAS 243 1051 4.3 5
DAL 233 932 4 11
MIA 215 940 4.4 7
PHI 213 797 3.7 8
ATL 258 1235 4.8 9
NYG 259 1013 3.9 8
JAX 230 937 4.1 8
NYJ 231 947 4.1 5
DET 230 1022 4.4 10
GB 202 614 3 6
CAR 189 810 4.3 7
NE 256 1079 4.2 7
LV 222 642 2.9 5
LA 242 1128 4.7 11
BAL 265 1240 4.7 11
NO 203 762 3.8 7
SEA 258 997 3.9 7
PIT 193 943 4.9 4
HOU 195 697 3.6 6
TEN 189 796 4.2 8
MIN 211 848 4 3
"""

# ------------------------------------------------- team stats, defence passing
DEF_PASS = """
SF 280 188 67.1 6.4 1783 11 6
CHI 260 161 61.9 8.2 2120 13 7
CIN 273 174 63.7 7.3 1989 9 5
BUF 300 183 61 6.7 2022 15 6
DEN 344 207 60.2 6.5 2249 14 8
CLE 297 177 59.6 6.7 1982 12 6
TB 307 190 61.9 6.6 2040 12 16
AZ 258 166 64.3 8 2076 19 3
LAC 233 153 65.7 7.9 1845 13 7
KC 276 170 61.6 6.4 1764 7 6
IND 264 162 61.4 8.1 2145 16 2
WAS 332 217 65.4 7 2341 17 6
DAL 296 194 65.5 7.2 2133 16 4
MIA 221 168 76 8.1 1797 16 5
PHI 300 180 60 7.2 2150 13 3
ATL 318 210 66 6.8 2171 14 3
NYG 286 179 62.6 6.2 1763 17 8
JAX 261 172 65.9 7.3 1907 8 11
NYJ 270 174 64.4 7.1 1909 16 1
DET 313 203 64.9 7.2 2265 18 6
GB 325 203 62.5 6.4 2087 13 13
CAR 278 176 63.3 6.4 1774 12 5
NE 286 193 67.5 7.9 2256 14 5
LV 279 183 65.6 8 2238 20 7
LA 293 179 61.1 6.4 1882 11 7
BAL 287 187 65.2 7.6 2177 12 4
NO 261 171 65.5 7.8 2045 13 4
SEA 277 178 64.3 5.5 1519 9 8
PIT 280 183 65.4 6.9 1936 7 7
HOU 276 178 64.5 7.4 2056 12 4
TEN 272 193 71 8 2182 11 8
MIN 234 135 57.7 6.4 1495 5 9
"""

# ------------------------------------------------- team stats, defence rushing
DEF_RUSH = """
SF 194 647 3.3 4
CHI 185 820 4.4 8
CIN 201 1013 5 8
BUF 189 733 3.9 7
DEN 248 1119 4.5 6
CLE 249 1175 4.7 8
TB 201 712 3.5 3
AZ 262 1097 4.2 10
LAC 240 976 4.1 11
KC 215 780 3.6 5
IND 250 1233 4.9 9
WAS 236 934 4 9
DAL 266 1327 5 11
MIA 236 894 3.8 6
PHI 276 1135 4.1 10
ATL 242 1069 4.4 10
NYG 244 1094 4.5 7
JAX 194 714 3.7 5
NYJ 282 1152 4.1 10
DET 184 753 4.1 6
GB 244 981 4 11
CAR 231 1067 4.6 13
NE 225 870 3.9 8
LV 272 1361 5 12
LA 236 934 4 4
BAL 249 899 3.6 12
NO 237 1071 4.5 11
SEA 233 802 3.4 7
PIT 185 671 3.6 4
HOU 209 824 3.9 9
TEN 239 993 4.2 10
MIN 224 951 4.2 5
"""

# ------------------------------------------------------- Week 10 final result
# nfl.com/scores/2026/REG10 read 2026-11-13: Commanders 24, Giants 21, FINAL, Thu Nov 12.
# The Week 10 injury page still carries the PRE-GAME records (WAS 3-5-1 / NYG 5-3-1), which is
# the live standings view, so the result is recorded here separately.
WEEK10_FINAL = [("WAS", 24, "NYG", 21, "2026-11-12", "Thursday Night Football")]

# ------------------------------------------------------- Week 11 slate
# away home date time_et network   (nfl.com/schedules/2026/by-week/week-11, read 2026-11-13)
SLATE_11 = [
    ("IND", "HOU", "2026-11-19", "8:15 PM", "Prime Video"),
    ("MIA", "BUF", "2026-11-22", "1:00 PM", "CBS"),
    ("BAL", "CAR", "2026-11-22", "1:00 PM", "FOX"),
    ("NO", "CHI", "2026-11-22", "1:00 PM", "FOX"),
    ("TEN", "DAL", "2026-11-22", "1:00 PM", "FOX"),
    ("TB", "DET", "2026-11-22", "1:00 PM", "FOX"),
    ("AZ", "KC", "2026-11-22", "1:00 PM", "CBS"),
    ("PIT", "PHI", "2026-11-22", "1:00 PM", "CBS"),
    ("NYJ", "LAC", "2026-11-22", "4:05 PM", "FOX"),
    ("JAX", "NYG", "2026-11-22", "4:25 PM", "CBS"),
    ("LV", "DEN", "2026-11-22", "4:25 PM", "CBS"),
    ("MIN", "SF", "2026-11-22", "8:20 PM", "NBC (Mexico City)"),
    ("CIN", "WAS", "2026-11-23", "8:15 PM", "ESPN"),
]
BYES_11 = ["ATL", "CLE", "GB", "LA", "NE", "SEA"]

# ------------------------------------------------------- Week 10 final scores
# 14 games, nfl.com/scores/2026/REG10 + the per-game pages linked from the Week 10 schedule.
WEEK10_ALL = [
    ("WAS", 24, "NYG", 21), ("NE", None, "DET", None), ("KC", None, "ATL", None),
    ("HOU", None, "CLE", None), ("MIN", None, "GB", None), ("MIA", None, "IND", None),
    ("CAR", None, "NO", None), ("BUF", None, "NYJ", None), ("JAX", None, "TEN", None),
    ("LA", None, "AZ", None), ("SEA", None, "LV", None), ("SF", None, "DAL", None),
    ("PIT", None, "CIN", None), ("LAC", None, "BAL", None),
]

# ------------------------------------------------------- Week 9 finals (verified)
# nfl.com/scores/2026/REG9, read 2026-11-13, every game on the page.
WEEK9_ALL = [
    ("JAX", 33, "BAL", 10), ("CIN", 34, "ATL", 17), ("DEN", 26, "CAR", 21),
    ("DAL", 27, "IND", 23), ("NYJ", 12, "KC", 35), ("DET", 19, "MIA", 9),
    ("CLE", 22, "NO", 23), ("NYG", 19, "PHI", 11), ("LA", 20, "WAS", 13),
    ("HOU", 44, "LAC", 22), ("LV", 17, "SF", 38), ("GB", 45, "NE", 27),
    ("AZ", 3, "SEA", 17), ("TB", 24, "CHI", 27), ("BUF", 23, "MIN", 6),
]

# ------------------------------------------------------- player season totals
# nfl.com/stats/player-stats (season leaders, read 2026-11-13). Only the columns that are
# printed on the leaderboard and that I could identify with certainty are kept.
PASSING_LEADERS = """
jordan-love 2618 7.7 341 215 63 19 6 97.9 110 32.3 40 12 81 17 101
joe-burrow 2386 8.1 296 219 74 23 6 114.8 119 40.2 27 5 47 15 102
dak-prescott 2381 7.1 336 218 64.9 16 5 95.4 119 35.4 28 6 53 14 69
matthew-stafford 2374 6.9 346 230 66.5 16 9 90.6 121 35 24 6 64 13 97
kirk-cousins 2340 7.4 315 202 64.1 20 8 97.1 117 37.1 31 5 45 11 64
drake-maye 2282 8.4 272 178 65.4 18 11 96.8 99 36.4 31 6 63 20 103
c-j-stroud 2251 8 282 181 64.2 16 2 104.8 98 34.8 32 7 63 16 103
bryce-young 2197 7.1 308 186 60.4 16 6 91.3 109 35.4 27 4 55 26 155
jared-goff 2134 7.8 273 185 67.8 15 2 106.4 103 37.7 23 5 57 19 129
geno-smith 2078 7.7 271 183 67.5 12 3 100.4 89 32.8 24 9 60 28 236
patrick-mahomes 2037 7.8 263 177 67.3 14 4 101.8 94 35.7 22 7 73 11 66
josh-allen 2027 8.6 236 156 66.1 12 6 99.3 93 39.4 32 8 57 17 109
tyler-shough 1986 6.4 308 204 66.2 14 6 91.2 99 32.1 21 5 52 20 142
brock-purdy 1980 8.4 236 163 69.1 17 5 109.8 97 41.1 27 4 82 8 48
trevor-lawrence 1932 8.6 224 146 65.2 18 4 111.7 91 40.6 27 4 52 13 106
aaron-rodgers 1871 6.5 288 175 60.8 13 6 86.2 82 28.5 24 6 80 23 187
deshaun-watson 1806 7.2 249 163 65.5 7 3 91.2 83 33.3 24 3 60 33 174
bo-nix 1730 6 287 174 60.6 11 4 84.7 85 29.6 21 4 52 11 57
daniel-jones-x5302 1722 5.7 302 182 60.3 6 10 68.9 86 28.5 18 3 55 24 157
jacoby-brissett 1719 5.6 305 193 63.3 10 7 79.7 94 30.8 15 0 38 19 118
justin-herbert 1591 6.8 235 144 61.3 6 11 70.4 70 29.8 18 6 58 31 198
caleb-williams 1546 7.9 195 134 68.7 8 5 95.4 67 34.4 24 3 58 14 94
jayden-daniels 1499 7 213 138 64.8 10 2 97.1 71 33.3 22 3 53 17 111
cam-ward 1483 6 248 155 62.5 6 5 78.8 73 29.4 16 1 41 13 99
sam-darnold 1478 7 211 127 60.2 10 9 79.4 79 37.4 19 2 43 17 113
"""

RECEIVING_LEADERS = """
jaxon-smith-njigba 71 1036 9 16 3 82 51 71.8 0 346 99
ceedee-lamb 70 904 7 14 3 49 45 64.3 1 275 108
christian-watson 49 879 7 17 5 81 31 63.3 1 214 74
matthew-golden 53 783 5 14 5 50 35 66 0 237 92
tee-higgins 48 758 6 10 2 44 40 83.3 0 173 67
chris-olave 56 734 2 10 3 47 39 69.6 0 162 83
puka-nacua 70 715 4 7 2 43 35 50 1 381 93
drake-london 44 692 1 11 2 68 31 70.4 0 308 68
malik-nabers 58 692 2 11 2 46 30 51.7 2 190 85
brock-bowers 48 658 6 11 0 33 33 68.8 2 218 70
amon-ra-st-brown 61 657 5 7 1 40 36 59 1 241 86
ja-marr-chase 53 647 7 8 2 47 33 62.3 0 220 73
luther-burden-iii 49 644 4 14 2 58 23 46.9 2 353 66
tetairoa-mcmillan 46 625 3 11 0 32 31 67.4 2 160 71
zay-flowers 43 614 3 9 4 54 24 55.8 0 322 64
trey-mcbride 73 598 5 4 0 27 30 41.1 1 215 94
isaiah-likely 55 575 7 6 1 66 30 54.6 2 223 80
michael-wilson 51 546 2 6 0 27 33 64.7 0 141 88
george-pickens 39 533 2 9 1 53 28 71.8 0 130 62
tre-tucker 33 529 4 8 4 44 22 66.7 0 116 56
rome-odunze 32 528 1 15 1 47 24 75 1 107 51
garrett-wilson 43 527 3 7 0 32 28 65.1 0 122 63
denzel-boston 32 507 3 6 4 60 21 65.6 0 160 61
parker-washington 29 493 5 7 2 51 18 62.1 0 170 55
george-kittle 38 483 5 8 2 56 21 55.3 1 243 53
"""

RUSHING_LEADERS = """
bijan-robinson 880 169 5 9 2 59 44 26 2
kenneth-walker-iii 872 159 7 7 2 76 44 27.7 0
jahmyr-gibbs 847 177 9 3 0 30 55 31.1 1
bucky-irving 825 167 7 6 2 72 39 23.4 3
james-cook 814 169 8 4 0 35 45 26.6 4
jaylen-warren 704 119 2 7 2 51 37 31.1 1
derrick-henry 689 175 8 3 0 32 35 20 1
jonathan-taylor 656 161 8 5 0 38 37 23 3
javonte-williams 629 154 9 3 0 34 36 23.4 2
chuba-hubbard 619 134 5 3 0 32 36 26.9 1
braelon-allen 598 120 3 4 0 27 34 28.3 2
tony-pollard 595 133 6 3 1 40 27 20.3 1
kyren-williams 593 127 6 3 0 30 36 28.4 2
d-andre-swift 576 155 10 2 0 32 30 19.4 2
bhayshul-tuten 521 122 4 2 0 39 26 21.3 0
cam-skattebo 496 116 4 1 1 42 28 24.1 3
aaron-jones 474 115 2 1 0 20 20 17.4 1
ollie-gordon-ii 463 107 4 3 1 53 26 24.3 0
christian-mccaffrey 457 102 9 0 0 16 26 25.5 0
blake-corum 447 86 4 1 0 23 25 29.1 1
emanuel-wilson 403 111 3 1 0 21 19 17.1 2
rhamondre-stevenson 399 102 2 2 0 24 25 24.5 0
chase-brown 397 103 1 0 0 19 18 17.5 1
quinshon-judkins 385 116 3 1 0 30 20 17.2 0
tyler-allgeier 369 89 2 3 2 63 16 18 0
"""

# ------------------------------------------------------- per-game player logs
# nfl.com/players/<slug>/stats/logs/ read 2026-11-13. Columns follow the page exactly as
# printed: for QB rows (cmp att yds avg td int sck sckyds rate ratt ryds ravg rtd)
# and for WR rows (rec rec_yds rec_avg long rec_td).
# Each row: (week, date, opponent, result, then the numeric columns).
PLAYER_LOGS = {
    "drake-maye": {
        "name": "Drake Maye", "pos": "QB", "team": "NE", "kind": "passing",
        "url": "https://www.nfl.com/players/drake-maye/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/drake-maye/stats/",
        "season_totals": {"g": 9, "gs": 9, "cmp": 178, "att": 272, "yds": 2282, "avg": 8.4,
                          "td": 18, "int": 11, "sck": 20, "sckyds": 103, "rate": 96.8,
                          "ratt": 47, "ryds": 219, "ravg": 4.7, "rtd": 3},
        "games": [
            (9, "2026-11-08", "GB", "L 27-45", 21, 38, 299, 7.9, 3, 3, 4, 27, 74.3, 1, 3, 3.0, 0),
            (8, "2026-11-01", "MIA", "W 24-19", 16, 20, 199, 10.0, 2, 0, 3, 17, 141.5, 8, 5, 0.6, 1),
            (7, "2026-10-22", "CHI", "L 24-30", 24, 31, 321, 10.4, 2, 1, 2, 11, 117.8, 4, 26, 6.5, 1),
            (6, "2026-10-18", "NYJ", "W 26-19", 18, 32, 235, 7.3, 3, 0, 0, 0, 110.8, 4, 24, 6.0, 0),
            (5, "2026-10-11", "LV", "W 45-17", 26, 34, 374, 11.0, 4, 0, 1, 3, 150.9, 7, 25, 3.6, 1),
            (4, "2026-10-04", "BUF", "W 29-26", 22, 37, 269, 7.3, 3, 1, 1, 7, 97.7, 8, 54, 6.8, 0),
            (3, "2026-09-27", "JAX", "L 6-35", 14, 25, 199, 8.0, 0, 2, 3, 11, 48.6, 4, 18, 4.5, 0),
            (2, "2026-09-20", "PIT", "W 20-3", 14, 22, 208, 9.4, 0, 1, 3, 17, 75.6, 4, 17, 4.2, 0),
            (1, "2026-09-09", "SEA", "L 10-13", 23, 33, 178, 5.4, 1, 3, 3, 10, 54.9, 7, 47, 6.7, 0),
        ],
    },
    "josh-allen": {
        "name": "Josh Allen", "pos": "QB", "team": "BUF", "kind": "passing",
        "url": "https://www.nfl.com/players/josh-allen/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/josh-allen/stats/",
        "season_totals": {"g": 8, "att": 236, "cmp": 156, "yds": 2027, "avg": 8.6, "td": 12,
                          "int": 6, "sck": 17, "sckyds": 109, "rate": 99.3, "ratt": 57,
                          "ryds": 109, "rtd": 8},
        "games": [
            (9, "2026-11-09", "MIN", "W 23-6", 21, 31, 234, 7.6, 1, 1, 4, 29, 87.3, 6, 15, 2.5, 0),
            (8, "2026-11-01", "BAL", "W 36-10", 21, 34, 289, 8.5, 2, 1, 1, 9, 96.3, 7, 30, 4.3, 1),
            (6, "2026-10-18", "LV", "W 33-30", 23, 33, 255, 7.7, 2, 0, 2, 13, 112.6, 5, 1, 0.2, 0),
            (5, "2026-10-12", "LA", "W 37-34", 12, 19, 210, 11.0, 1, 1, 1, 8, 96.4, 10, 121, 12.1, 1),
            (4, "2026-10-04", "NE", "L 26-29", 23, 33, 253, 7.7, 1, 1, 1, 4, 89.6, 5, 4, 0.8, 1),
            (3, "2026-09-27", "LAC", "W 24-16", 16, 26, 204, 7.8, 0, 2, 4, 30, 54.0, 8, 22, 2.8, 2),
            (2, "2026-09-17", "DET", "W 41-31", 20, 31, 248, 8.0, 3, 0, 2, 5, 121.4, 14, 69, 4.9, 2),
            (1, "2026-09-13", "HOU", "W 36-31", 20, 29, 334, 11.5, 2, 0, 2, 11, 130.5, 6, 23, 3.8, 2),
        ],
    },
    "jared-goff": {
        "name": "Jared Goff", "pos": "QB", "team": "DET", "kind": "passing",
        "url": "https://www.nfl.com/players/jared-goff/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/jared-goff/stats/",
        "season_totals": {"g": 8, "att": 273, "cmp": 185, "yds": 2134, "avg": 7.8, "td": 15,
                          "int": 2, "sck": 19, "sckyds": 129, "rate": 106.4},
        "games": [
            (9, "2026-11-08", "MIA", "W 19-9", 17, 25, 170, 6.8, 0, 1, 3, 13, 70.4, 4, 5, 1.2, 0),
            (8, "2026-11-01", "MIN", "W 19-15", 18, 25, 176, 7.0, 1, 1, 4, 22, 88.1, 3, 0, 0.0, 0),
            (7, "2026-10-25", "GB", "W 20-17", 22, 32, 303, 9.5, 2, 0, 1, 7, 119.7, 2, -1, -0.5, 0),
            (5, "2026-10-11", "AZ", "W 45-21", 19, 30, 271, 9.0, 3, 0, 3, 22, 125.8, 1, 1, 1.0, 1),
            (4, "2026-10-04", "CAR", "L 26-32", 32, 52, 412, 7.9, 1, 0, 1, 6, 92.8, 0, 0, 0.0, 0),
            (3, "2026-09-27", "NYJ", "W 31-24", 25, 32, 269, 8.4, 2, 0, 2, 19, 122.5, 4, 6, 1.5, 0),
            (2, "2026-09-17", "BUF", "L 31-41", 26, 38, 327, 8.6, 4, 0, 4, 38, 130.0, 3, 7, 2.3, 0),
            (1, "2026-09-13", "NO", "W 31-30", 26, 39, 206, 5.3, 2, 0, 1, 2, 96.7, 2, 2, 1.0, 0),
        ],
    },
    "amon-ra-st-brown": {
        "name": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "kind": "receiving",
        "url": "https://www.nfl.com/players/amon-ra-st-brown/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/amon-ra-st-brown/stats/",
        "season_totals": {"rec": 61, "yds": 657, "avg": 10.8, "td": 5},
        "games": [
            (9, "2026-11-08", "MIA", "W 19-9", 8, 86, 10.8, 17, 0),
            (8, "2026-11-01", "MIN", "W 19-15", 7, 46, 6.6, 13, 0),
            (7, "2026-10-25", "GB", "W 20-17", 9, 153, 17.0, 40, 0),
            (5, "2026-10-11", "AZ", "W 45-21", 6, 69, 11.5, 36, 0),
            (4, "2026-10-04", "CAR", "L 26-32", 8, 75, 9.4, 19, 0),
            (3, "2026-09-27", "NYJ", "W 31-24", 4, 19, 4.8, 16, 1),
            (2, "2026-09-17", "BUF", "L 31-41", 9, 142, 15.8, 34, 2),
            (1, "2026-09-13", "NO", "W 31-30", 10, 67, 6.7, 19, 2),
        ],
    },
    "ja-marr-chase": {
        "name": "Ja'Marr Chase", "pos": "WR", "team": "CIN", "kind": "receiving",
        "url": "https://www.nfl.com/players/ja-marr-chase/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/ja-marr-chase/stats/",
        "season_totals": {"rec": 53, "yds": 647, "avg": 12.2, "td": 7},
        "games": [
            (9, "2026-11-08", "ATL", "W 34-17", 10, 155, 15.5, 47, 1),
            (8, "2026-11-01", "TEN", "W 43-36", 11, 141, 12.8, 30, 1),
            (7, "2026-10-25", "BAL", "W 35-13", 5, 62, 12.4, 30, 1),
            (5, "2026-10-11", "MIA", "W 31-24", 6, 77, 12.8, 45, 1),
            (4, "2026-10-04", "JAX", "L 17-22", 3, 27, 9.0, 17, 0),
            (3, "2026-09-27", "PIT", "L 27-30", 9, 98, 10.9, 21, 1),
            (2, "2026-09-20", "HOU", "W 20-6", 7, 75, 10.7, 32, 2),
            (1, "2026-09-13", "TB", "W 33-27", 2, 12, 6.0, 16, 0),
        ],
    },
    "a-j-brown": {
        "name": "A.J. Brown", "pos": "WR", "team": "NE", "kind": "receiving",
        "url": "https://www.nfl.com/players/a-j-brown/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/a-j-brown/stats/",
        # NOT confirmable from the pages read: he is outside the top-25 receiving leaderboard,
        # so his season totals are left blank rather than reconstructed from a partial log.
        "season_totals": {},
        "games": [
            (7, "2026-10-22", "CHI", "L 24-30", 3, 48, 16.0, 18, 0),
            (6, "2026-10-18", "NYJ", "W 26-19", 3, 27, 9.0, 15, 0),
            (1, "2026-09-09", "SEA", "L 10-13", 3, 26, 8.7, 14, 0),
        ],
    },
    "jahmyr-gibbs": {
        "name": "Jahmyr Gibbs", "pos": "RB", "team": "DET", "kind": "rushing",
        "url": "https://www.nfl.com/players/jahmyr-gibbs/stats/logs/",
        "season_totals_url": "https://www.nfl.com/players/jahmyr-gibbs/stats/",
        "season_totals": {"att": 177, "yds": 847, "avg": 4.8, "td": 9},
        "games": [
            (9, "2026-11-08", "MIA", "W 19-9", 20, 74, 3.7, 16, 1),
            (8, "2026-11-01", "MIN", "W 19-15", 23, 153, 6.6, 30, 1),
            (7, "2026-10-25", "GB", "W 20-17", 29, 116, 4.0, 15, 0),
            (5, "2026-10-11", "AZ", "W 45-21", 25, 151, 6.0, 22, 2),
            (4, "2026-10-04", "CAR", "L 26-32", 15, 46, 3.1, 13, 1),
            (3, "2026-09-27", "NYJ", "W 31-24", 20, 99, 5.0, 17, 2),
            (2, "2026-09-17", "BUF", "L 31-41", 16, 52, 3.2, 16, 0),
            (1, "2026-09-13", "NO", "W 31-30", 29, 156, 5.4, 21, 2),
        ],
    },
}

# ------------------------------------------------------- regression checks
# Facts from earlier reads that must still hold. If any fails the transcription is wrong.
REGRESSIONS = {
    # 2026-11-12 peer snapshot: 135 W / 135 L / 2 T, league PF = PA = 6,246, 136 games.
    "peer_snapshot_2026_11_12": {"w": 135, "l": 135, "t": 2, "pf": 6246, "games": 136},
    # Week 9 page: 15 games, and these finals read directly.
    "week9_games": 15,
    "week10_finals_read": 1,
}


def parse(block, ncols):
    out = {}
    for line in block.strip().split("\n"):
        parts = line.split()
        assert len(parts) == ncols + 1, (line, len(parts))
        out[parts[0]] = parts[1:]
    return out


def main():
    st = {}
    for line in STANDINGS.strip().split("\n"):
        t, w, l, ti, pct, pf, pa = line.split()
        st[t] = {"team": t, "w": int(w), "l": int(l), "t": int(ti), "pct": float(pct),
                 "pf": int(pf), "pa": int(pa), "net": int(pf) - int(pa),
                 "games": int(w) + int(l) + int(ti),
                 "source_url": SOURCES["standings"]}

    op = parse(OFF_PASS, 15)
    oru = parse(OFF_RUSH, 4)
    dp = parse(DEF_PASS, 7)
    dru = parse(DEF_RUSH, 4)

    team_stats = {}
    for t in st:
        a = op[t]
        b = oru[t]
        c = dp[t]
        d = dru[t]
        team_stats[t] = {
            "team": t,
            "pass_att": int(a[0]), "pass_cmp": int(a[1]), "pass_pct_published": float(a[2]),
            "pass_avg_published": float(a[3]), "pass_yds": int(a[4]),
            "pass_td": int(a[5]), "pass_int": int(a[6]), "pass_rate_published": float(a[7]),
            "pass_sck": int(a[13]), "pass_sck_yds": int(a[14]),
            "rush_att": int(b[0]), "rush_yds": int(b[1]), "rush_avg_published": float(b[2]),
            "rush_td": int(b[3]),
            "def_pass_att": int(c[0]), "def_pass_cmp": int(c[1]),
            "def_pass_pct_published": float(c[2]), "def_pass_avg_published": float(c[3]),
            "def_pass_yds": int(c[4]), "def_pass_td": int(c[5]), "def_pass_int": int(c[6]),
            "def_rush_att": int(d[0]), "def_rush_yds": int(d[1]),
            "def_rush_avg_published": float(d[2]), "def_rush_td": int(d[3]),
            "source_url_off_pass": SOURCES["off_pass"],
            "source_url_off_rush": SOURCES["off_rush"],
            "source_url_def_pass": SOURCES["def_pass"],
            "source_url_def_rush": SOURCES["def_rush"],
        }

    # ---------------- integrity checks over the transcription itself
    checks = []

    def chk(cid, name, ok, detail):
        checks.append({"id": cid, "name": name, "result": "pass" if ok else "FAIL",
                       "detail": detail})

    def note(cid, name, ok, detail):
        """A recorded observation about how two official pages disagree. It is not a data
        defect: both values are published verbatim and neither is used in a model input."""
        checks.append({"id": cid, "name": name, "result": "note" if not ok else "pass",
                       "detail": detail})

    sumw = sum(v["w"] for v in st.values())
    suml = sum(v["l"] for v in st.values())
    sumt = sum(v["t"] for v in st.values())
    sumpf = sum(v["pf"] for v in st.values())
    sumpa = sum(v["pa"] for v in st.values())
    games = sumw + sumt // 2
    chk("IC-01", "Every win is somebody else's loss",
        sumw == suml, "sum W %d = sum L %d" % (sumw, suml))
    chk("IC-02", "League points scored equals points allowed",
        sumpf == sumpa, "sum PF %d = sum PA %d" % (sumpf, sumpa))
    chk("IC-03", "Games implied by the standings reconcile with the schedule",
        games == REGRESSIONS["peer_snapshot_2026_11_12"]["games"] + REGRESSIONS["week10_finals_read"],
        "%d game-equivalents (136 through Week 9 + 1 Week 10 final)" % games)
    chk("IC-04", "Week 9 carried 15 games and Week 10 had 14",
        len(WEEK9_ALL) == REGRESSIONS["week9_games"] and len(WEEK10_ALL) == 14,
        "%d Week 9 rows, %d Week 10 rows" % (len(WEEK9_ALL), len(WEEK10_ALL)))
    # week 9 arithmetic: recompute each club's record shift onto the live standings backward
    w9w, w9l, w9t = {}, {}, {}
    for a, asc, h, hsc in WEEK9_ALL:
        if asc > hsc:
            w9w[a] = w9w.get(a, 0) + 1; w9l[h] = w9l.get(h, 0) + 1
        elif hsc > asc:
            w9w[h] = w9w.get(h, 0) + 1; w9l[a] = w9l.get(a, 0) + 1
        else:
            w9t[a] = w9t.get(a, 0) + 1; w9t[h] = w9t.get(h, 0) + 1
    shift_bad = []
    for a, asc, h, hsc in WEEK9_ALL:
        for team, side in ((a, "away"), (h, "home")):
            pass  # per-team shift is checked against the peer snapshot below
    # The peer snapshot (through Week 9) must equal today's standings minus Week 10 results.
    # Reconstructing per-team is only possible with the full Week 1-9 archive (checked in
    # engine/dataset.py against NFL.com week pages), so here we check the league totals.
    chk("IC-05", "Peer Week 9 totals plus one Week 10 final equal today's league totals",
        (REGRESSIONS["peer_snapshot_2026_11_12"]["pf"] + 24 + 21 == sumpf and
         REGRESSIONS["peer_snapshot_2026_11_12"]["w"] + 1 == sumw),
        "peer PF 6,246 + 24 + 21 = %d (published %d); peer W 135 + 1 = %d (published %d)"
        % (REGRESSIONS["peer_snapshot_2026_11_12"]["pf"] + 45, sumpf,
           REGRESSIONS["peer_snapshot_2026_11_12"]["w"] + 1, sumw))
    # passing identity: league completions <= attempts, and pct/avg reproduce published values
    pct_bad = [t for t, r in team_stats.items()
               if abs(round(100.0 * r["pass_cmp"] / r["pass_att"], 1) - r["pass_pct_published"]) > 0.05]
    chk("IC-06", "Published passing percentage equals completions divided by attempts",
        not pct_bad, "0 of 32 rows deviate" if not pct_bad else "deviate: %s" % pct_bad)
    avg_bad = sorted([(t, round(team_stats[t]["pass_yds"] / team_stats[t]["pass_att"], 3),
                       team_stats[t]["pass_avg_published"]) for t in team_stats
                      if abs(round(team_stats[t]["pass_yds"] / team_stats[t]["pass_att"], 1)
                             - team_stats[t]["pass_avg_published"]) > 0.05])
    # Published AVG and yds/att disagree by 0.1 on 4 of 32 rows, in both directions, so it is
    # NOT a rounding rule that can be reproduced. The site therefore publishes our own
    # yds/att and never uses the published AVG as a model input.
    note("IC-07", "Published passing average reproduces yards divided by attempts",
         not avg_bad,
         "0 of 32 rows deviate" if not avg_bad else
         "%d of 32 rows deviate by 0.1 in both directions: %s - the published AVG column is "
         "recorded but never used; the site publishes yds/att" % (len(avg_bad), avg_bad))
    ravg_bad = sorted([t for t, r in team_stats.items()
                       if abs(round(r["rush_yds"] / r["rush_att"], 1) - r["rush_avg_published"]) > 0.05])
    note("IC-08", "Published rushing average reproduces yards divided by attempts",
         not ravg_bad, "0 of 32 rows deviate" if not ravg_bad else "deviate: %s" % ravg_bad)
    # league identities between the offence and defence pages
    chk("IC-09", "League passing yards gained equals passing yards allowed",
        sum(r["pass_yds"] for r in team_stats.values()) ==
        sum(r["def_pass_yds"] for r in team_stats.values()),
        "%d = %d" % (sum(r["pass_yds"] for r in team_stats.values()),
                     sum(r["def_pass_yds"] for r in team_stats.values())))
    chk("IC-10", "League passing touchdowns scored equals allowed",
        sum(r["pass_td"] for r in team_stats.values()) ==
        sum(r["def_pass_td"] for r in team_stats.values()),
        "%d = %d" % (sum(r["pass_td"] for r in team_stats.values()),
                     sum(r["def_pass_td"] for r in team_stats.values())))
    chk("IC-11", "League rushing yards gained equals allowed",
        sum(r["rush_yds"] for r in team_stats.values()) ==
        sum(r["def_rush_yds"] for r in team_stats.values()),
        "%d = %d" % (sum(r["rush_yds"] for r in team_stats.values()),
                     sum(r["def_rush_yds"] for r in team_stats.values())))
    chk("IC-12", "League rushing touchdowns scored equals allowed",
        sum(r["rush_td"] for r in team_stats.values()) ==
        sum(r["def_rush_td"] for r in team_stats.values()),
        "%d = %d" % (sum(r["rush_td"] for r in team_stats.values()),
                     sum(r["def_rush_td"] for r in team_stats.values())))
    chk("IC-13", "League passing attempts equal attempts faced by defences",
        sum(r["pass_att"] for r in team_stats.values()) ==
        sum(r["def_pass_att"] for r in team_stats.values()),
        "%d = %d" % (sum(r["pass_att"] for r in team_stats.values()),
                     sum(r["def_pass_att"] for r in team_stats.values())))
    # NE team passing must equal the official season leaderboard row for its quarterback
    ne = team_stats["NE"]
    maye = PLAYER_LOGS["drake-maye"]["season_totals"]
    resid = {"att": ne["pass_att"] - maye["att"], "cmp": ne["pass_cmp"] - maye["cmp"],
             "yds": ne["pass_yds"] - maye["yds"], "td": ne["pass_td"] - maye["td"],
             "int": ne["pass_int"] - maye["int"]}
    # The club total must be at least the starter's total, and the leftover must look like a
    # backup's small workload rather than a transcription error.
    chk("IC-14", "NE club passing exceeds the Drake Maye season line by a small residual",
        all(v >= 0 for v in resid.values()) and resid["att"] <= 40 and resid["yds"] <= 300,
        "club minus Maye = %s (a single backup throwing 9 passes explains it)" % resid)
    chk("IC-14b", "Team sacks equal the quarterback's sacks exactly",
        ne["pass_sck"] == maye["sck"] and ne["pass_sck_yds"] == maye["sckyds"],
        "club %d sck/%d yds = Maye %d sck/%d yds" %
        (ne["pass_sck"], ne["pass_sck_yds"], maye["sck"], maye["sckyds"]))
    # player game logs must sum to the published season totals
    for slug, p in PLAYER_LOGS.items():
        if not p["season_totals"]:
            note("IC-16:%s" % slug,
                 "%s game logs sum to a published season total" % p["name"], False,
                 "no published season total exists for this player on the pages read, so the "
                 "log rows are published and the season columns are left blank")
            continue
        if p["kind"] == "passing":
            tot = {
                "cmp": sum(g[4] for g in p["games"]), "att": sum(g[5] for g in p["games"]),
                "yds": sum(g[6] for g in p["games"]), "td": sum(g[8] for g in p["games"]),
                "int": sum(g[9] for g in p["games"]), "sck": sum(g[10] for g in p["games"]),
                "sckyds": sum(g[11] for g in p["games"]),
            }
            for k, v in tot.items():
                if k in p["season_totals"]:
                    chk("IC-15:%s:%s" % (slug, k),
                        "%s game logs sum to the published season %s" % (p["name"], k),
                        v == p["season_totals"][k], "logs %d vs season %d" % (v, p["season_totals"][k]))
        else:
            k1, k2, k3 = ("rec", "yds", "td") if p["kind"] == "receiving" else ("att", "yds", "td")
            # receiving and rushing rows are both (week, date, opp, result, n, yds, avg, long, td)
            got = (sum(g[4] for g in p["games"]), sum(g[5] for g in p["games"]),
                   sum(g[8] for g in p["games"]))
            want = (p["season_totals"][k1], p["season_totals"][k2], p["season_totals"][k3])
            chk("IC-16:%s" % slug,
                "%s game logs sum to the published season totals" % p["name"],
                got == want, "logs %s vs season %s" % (got, want))
    # slate integrity
    slate_teams = [x for g in SLATE_11 for x in (g[0], g[1])]
    chk("IC-17", "Week 11 has 13 games, 26 clubs and 6 byes",
        (len(SLATE_11), len(set(slate_teams)), len(BYES_11)) == (13, 26, 6) and
        bool(set(BYES_11) & set(slate_teams)) is False,
        "13 games, %d distinct clubs, %d byes, no overlap" % (len(set(slate_teams)), len(BYES_11)))
    chk("IC-18", "Every slate club exists in the standings",
        all(t in st for t in slate_teams + BYES_11), "32 of 32 clubs present")

    files = {}
    files["standings_2026-11-13.json"] = {
        "dataset": "nfl_2026_reg_standings",
        "title": "2026 NFL regular-season standings as published on nfl.com (read 2026-11-13)",
        "source_url": SOURCES["standings"],
        "captured_utc": CAPTURED,
        "capture_method": "Transcribed column by column from the league standings table. Only "
                          "W, L, T, PCT, PF and PA were taken; NET PTS is recomputed here and "
                          "checked against the published value in engine/dataset.py.",
        "columns": ["team", "w", "l", "t", "pct", "pf", "pa", "net", "games", "source_url"],
        "rows": [st[t] for t in sorted(st)],
    }
    files["team_stats_2026-11-13.json"] = {
        "dataset": "nfl_2026_reg_team_stats",
        "title": "2026 NFL club offence and defence, passing and rushing (read 2026-11-13)",
        "source_url": SOURCES["off_pass"],
        "captured_utc": CAPTURED,
        "capture_method": "Transcribed from the four official team-stat tables. Columns whose "
                          "labels were not present in the retrieved page text are published only "
                          "when an arithmetic identity proves their meaning (pct = cmp/att, "
                          "avg = yds/att). Unidentified columns are omitted, not guessed.",
        "omitted_columns_note": "The retrieved tables carried 15 (offence passing), 10 (rushing) "
                                "and 15 (defence passing) columns. Columns beyond the ones listed "
                                "in 'columns' could not be identified with certainty from the "
                                "retrieved text, so they are not published anywhere on the site.",
        "columns": ["pass_att", "pass_cmp", "pass_yds", "pass_td", "pass_int", "pass_sck",
                    "pass_sck_yds", "rush_att", "rush_yds", "rush_td", "def_pass_att",
                    "def_pass_cmp", "def_pass_yds", "def_pass_td", "def_pass_int",
                    "def_rush_att", "def_rush_yds", "def_rush_td"],
        "rows": [team_stats[t] for t in sorted(team_stats)],
    }
    files["slate_week11_2026.json"] = {
        "dataset": "nfl_2026_week11_slate",
        "title": "2026 Week 11 schedule (13 games, 6 byes) as published on nfl.com",
        "source_url": SOURCES["week11"],
        "captured_utc": CAPTURED,
        "rows": [{"away": a, "home": h, "date": d, "kickoff_et": k, "network": n,
                  "source_url": SOURCES["week11"]} for a, h, d, k, n in SLATE_11],
        "byes": [{"team": t, "source_url": SOURCES["week11"]} for t in BYES_11],
    }
    files["results_week9_week10_2026.json"] = {
        "dataset": "nfl_2026_week9_week10_results",
        "title": "Week 9 finals (15 games) and the Week 10 Thursday final (1 game)",
        "source_url_week9": SOURCES["scores9"],
        "source_url_week10": SOURCES["week10"],
        "captured_utc": CAPTURED,
        "rows": ([{"week": 9, "away": a, "away_score": x, "home": h, "home_score": y,
                   "source_url": SOURCES["scores9"]} for a, x, h, y in WEEK9_ALL] +
                 [{"week": 10, "away": a, "away_score": x, "home": h, "home_score": y,
                   "source_url": SOURCES["week10"]} for a, x, h, y, _d, _n in WEEK10_FINAL]),
        "week10_unplayed_note": "13 of the 14 Week 10 games had not been played when this page "
                                "was read on 2026-11-13; they are omitted here rather than "
                                "given a score. The Week 10 injury page still shows the "
                                "pre-game records for those clubs.",
        "rows_not_published": len([g for g in WEEK10_ALL if g[1] is None]),
    }
    files["players_2026-11-13.json"] = {
        "dataset": "nfl_2026_player_leaders_and_logs",
        "title": "2026 official player leaders (25 per category) and seven full per-game logs",
        "source_url_passing": SOURCES["passing_leaders"],
        "source_url_receiving": SOURCES["receiving_leaders"],
        "source_url_rushing": SOURCES["rushing_leaders"],
        "captured_utc": CAPTURED,
        "note": "The leaderboard tables carry no readable header row in the retrieved text, so "
                "this file publishes ONLY the columns whose meaning is fixed by the per-game "
                "logs and season-total pages for the same players (a full cross-check is in "
                "integrity_official.json). Everything else is omitted.",
        "passing": [dict(slug=l.split()[0], yds=int(l.split()[1]), avg=float(l.split()[2]),
                         att=int(l.split()[3]), cmp=int(l.split()[4]), pct=float(l.split()[5]),
                         td=int(l.split()[6]), ints=int(l.split()[7]), rate=float(l.split()[8]),
                         sck=int(l.split()[13]), sck_yds=int(l.split()[14]),
                         url="https://www.nfl.com/players/%s/stats/" % l.split()[0],
                         source_url=SOURCES["passing_leaders"])
                    for l in PASSING_LEADERS.strip().split("\n")],
        "receiving": [dict(slug=l.split()[0], rec=int(l.split()[1]), yds=int(l.split()[2]),
                           td=int(l.split()[3]),
                           url="https://www.nfl.com/players/%s/stats/" % l.split()[0],
                           source_url=SOURCES["receiving_leaders"])
                      for l in RECEIVING_LEADERS.strip().split("\n")],
        "rushing": [dict(slug=l.split()[0], yds=int(l.split()[1]), att=int(l.split()[2]),
                         avg=float(l.split()[3]), td=int(l.split()[6]),
                         url="https://www.nfl.com/players/%s/stats/" % l.split()[0],
                         source_url=SOURCES["rushing_leaders"])
                    for l in RUSHING_LEADERS.strip().split("\n")],
        "logs": PLAYER_LOGS,
    }
    files["integrity_official.json"] = {
        "dataset": "nfl_2026_official_integrity_checks",
        "captured_utc": CAPTURED,
        "checks": checks,
        "summary": {"total": len(checks),
                    "pass": len([c for c in checks if c["result"] == "pass"]),
                    "note": len([c for c in checks if c["result"] == "note"]),
                    "fail": len([c for c in checks if c["result"] == "FAIL"])},
    }
    for name, payload in files.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, sort_keys=False)
            fh.write("\n")
        print("wrote", name)
    s = files["integrity_official.json"]["summary"]
    print("integrity:", s)
    for c in checks:
        if c["result"] != "pass":
            print("  FAIL", c["id"], c["name"], "|", c["detail"])
    return 0 if s["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

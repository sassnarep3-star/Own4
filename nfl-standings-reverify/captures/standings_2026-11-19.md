# Verbatim rendered read of https://www.nfl.com/standings/ , captured 2026-11-19 (UTC).
# Route: fetched through the session's page-read tool (rendered text). The sandbox has no direct
# HTTPS egress to nfl.com, so this read is the rendered text the official page returned. Nothing
# below was retyped: the rows are the table rows as the official page rendered them, with the
# escaped link markup exactly as the read returned it.
# Parser: nfl-standings-reverify/engine/parse.py -> nfl-standings-reverify/data/standings_reverify.json
# Columns, as the page's own legend states: W L T PCT PF PA NET PTS (then HOME ROAD DIV CONF ... STRK).
# Only the leading, unambiguous run (club + W L T PCT PF PA NET) is parsed by the independent parser;
# the split-record columns are not modelled here. The comparison target is the stored nfl-desk read
# of the same official page, same day, so the two parsers share no code.

## AMERICAN FOOTBALL CONFERENCE

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/BUF)\\<br>\\<br>Buffalo Bills\\<br>\\<br>Bills](https://www.nfl.com/teams/buffalo-bills/) | 8 | 1 | 0 | 0.889 | 287 | 199 | 88 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/NE)\\<br>\\<br>New England Patriots\\<br>\\<br>Patriots](https://www.nfl.com/teams/new-england-patriots/) | 5 | 5 | 0 | 0.500 | 221 | 242 | -21 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/NYJ)\\<br>\\<br>New York Jets\\<br>\\<br>Jets](https://www.nfl.com/teams/new-york-jets/) | 2 | 8 | 0 | 0.200 | 194 | 254 | -60 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/MIA)\\<br>\\<br>Miami Dolphins\\<br>\\<br>Dolphins](https://www.nfl.com/teams/miami-dolphins/) | 1 | 8 | 0 | 0.111 | 148 | 224 | -76 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/CIN)\\<br>\\<br>Cincinnati Bengals\\<br>\\<br>Bengals](https://www.nfl.com/teams/cincinnati-bengals/) | 7 | 2 | 0 | 0.778 | 278 | 193 | 85 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/PIT)\\<br>\\<br>Pittsburgh Steelers\\<br>\\<br>Steelers](https://www.nfl.com/teams/pittsburgh-steelers/) | 6 | 3 | 0 | 0.667 | 198 | 182 | 16 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/CLE)\\<br>\\<br>Cleveland Browns\\<br>\\<br>Browns](https://www.nfl.com/teams/cleveland-browns/) | 6 | 4 | 0 | 0.600 | 188 | 220 | -32 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/BAL)\\<br>\\<br>Baltimore Ravens\\<br>\\<br>Ravens](https://www.nfl.com/teams/baltimore-ravens/) | 4 | 6 | 0 | 0.400 | 209 | 259 | -50 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/JAX)\\<br>\\<br>Jacksonville Jaguars\\<br>\\<br>Jaguars](https://www.nfl.com/teams/jacksonville-jaguars/) | 7 | 2 | 0 | 0.778 | 269 | 144 | 125 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/HOU)\\<br>\\<br>Houston Texans\\<br>\\<br>Texans](https://www.nfl.com/teams/houston-texans/) | 3 | 6 | 0 | 0.333 | 233 | 219 | 14 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/IND)\\<br>\\<br>Indianapolis Colts\\<br>\\<br>Colts](https://www.nfl.com/teams/indianapolis-colts/) | 3 | 7 | 0 | 0.300 | 208 | 271 | -63 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/TEN)\\<br>\\<br>Tennessee Titans\\<br>\\<br>Titans](https://www.nfl.com/teams/tennessee-titans/) | 1 | 8 | 0 | 0.111 | 167 | 239 | -72 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/KC)\\<br>\\<br>Kansas City Chiefs\\<br>\\<br>Chiefs](https://www.nfl.com/teams/kansas-city-chiefs/) | 7 | 2 | 0 | 0.778 | 237 | 156 | 81 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/DEN)\\<br>\\<br>Denver Broncos\\<br>\\<br>Broncos](https://www.nfl.com/teams/denver-broncos/) | 7 | 2 | 0 | 0.778 | 198 | 186 | 12 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/LV)\\<br>\\<br>Las Vegas Raiders\\<br>\\<br>Raiders](https://www.nfl.com/teams/las-vegas-raiders/) | 4 | 6 | 0 | 0.400 | 251 | 289 | -38 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/LAC)\\<br>\\<br>Los Angeles Chargers\\<br>\\<br>Chargers](https://www.nfl.com/teams/los-angeles-chargers/) | 1 | 8 | 0 | 0.111 | 144 | 239 | -95 |

## NATIONAL FOOTBALL CONFERENCE

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/NYG)\\<br>\\<br>New York Giants\\<br>\\<br>Giants](https://www.nfl.com/teams/new-york-giants/) | 5 | 3 | 1 | 0.611 | 203 | 196 | 7 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/DAL)\\<br>\\<br>Dallas Cowboys\\<br>\\<br>Cowboys](https://www.nfl.com/teams/dallas-cowboys/) | 4 | 6 | 0 | 0.400 | 286 | 282 | 4 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/WAS)\\<br>\\<br>Washington Commanders\\<br>\\<br>Commanders](https://www.nfl.com/teams/washington-commanders/) | 3 | 5 | 1 | 0.389 | 196 | 223 | -27 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/PHI)\\<br>\\<br>Philadelphia Eagles\\<br>\\<br>Eagles](https://www.nfl.com/teams/philadelphia-eagles/) | 2 | 7 | 0 | 0.222 | 148 | 221 | -73 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/DET)\\<br>\\<br>Detroit Lions\\<br>\\<br>Lions](https://www.nfl.com/teams/detroit-lions/) | 7 | 2 | 0 | 0.778 | 257 | 199 | 58 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/MIN)\\<br>\\<br>Minnesota Vikings\\<br>\\<br>Vikings](https://www.nfl.com/teams/minnesota-vikings/) | 7 | 2 | 0 | 0.778 | 176 | 126 | 50 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/CHI)\\<br>\\<br>Chicago Bears\\<br>\\<br>Bears](https://www.nfl.com/teams/chicago-bears/) | 7 | 2 | 0 | 0.778 | 241 | 184 | 57 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/GB)\\<br>\\<br>Green Bay Packers\\<br>\\<br>Packers](https://www.nfl.com/teams/green-bay-packers/) | 6 | 4 | 0 | 0.600 | 226 | 221 | 5 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/CAR)\\<br>\\<br>Carolina Panthers\\<br>\\<br>Panthers](https://www.nfl.com/teams/carolina-panthers/) | 4 | 5 | 0 | 0.444 | 219 | 236 | -17 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/TB)\\<br>\\<br>Tampa Bay Buccaneers\\<br>\\<br>Buccaneers](https://www.nfl.com/teams/tampa-bay-buccaneers/) | 3 | 6 | 0 | 0.333 | 202 | 178 | 24 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/NO)\\<br>\\<br>New Orleans Saints\\<br>\\<br>Saints](https://www.nfl.com/teams/new-orleans-saints/) | 3 | 6 | 0 | 0.333 | 202 | 236 | -34 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/ATL)\\<br>\\<br>Atlanta Falcons\\<br>\\<br>Falcons](https://www.nfl.com/teams/atlanta-falcons/) | 3 | 7 | 0 | 0.300 | 201 | 258 | -57 |

| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/SF)\\<br>\\<br>San Francisco 49ers\\<br>\\<br>49ers](https://www.nfl.com/teams/san-francisco-49ers/) | 8 | 1 | 0 | 0.889 | 281 | 196 | 85 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/SEA)\\<br>\\<br>Seattle Seahawks\\<br>\\<br>Seahawks](https://www.nfl.com/teams/seattle-seahawks/) | 6 | 4 | 0 | 0.600 | 223 | 175 | 48 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/LA)\\<br>\\<br>Los Angeles Rams\\<br>\\<br>Rams](https://www.nfl.com/teams/los-angeles-rams/) | 6 | 4 | 0 | 0.600 | 248 | 187 | 61 |
| [![](https://static.www.nfl.com/t_q-best/league/api/clubs/logos/AZ)\\<br>\\<br>Arizona Cardinals\\<br>\\<br>Cardinals](https://www.nfl.com/teams/arizona-cardinals/) | 3 | 7 | 0 | 0.300 | 184 | 289 | -105 |

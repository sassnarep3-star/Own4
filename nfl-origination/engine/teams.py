"""Team identity table.

Every abbreviation/name/slug pair below was read from the official NFL standings page
(https://www.nfl.com/standings/league/2026/REG) on 2026-11-13, whose rows link to
https://www.nfl.com/teams/<slug>/. Nothing here is guessed: the 32 clubs and their slugs
come straight from those official team links.
"""

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"

# abbr -> (full name, official team page path)
TEAMS = {
    "BUF": ("Buffalo Bills", "buffalo-bills"),
    "SF": ("San Francisco 49ers", "san-francisco-49ers"),
    "CHI": ("Chicago Bears", "chicago-bears"),
    "DEN": ("Denver Broncos", "denver-broncos"),
    "CIN": ("Cincinnati Bengals", "cincinnati-bengals"),
    "DET": ("Detroit Lions", "detroit-lions"),
    "JAX": ("Jacksonville Jaguars", "jacksonville-jaguars"),
    "KC": ("Kansas City Chiefs", "kansas-city-chiefs"),
    "MIN": ("Minnesota Vikings", "minnesota-vikings"),
    "PIT": ("Pittsburgh Steelers", "pittsburgh-steelers"),
    "GB": ("Green Bay Packers", "green-bay-packers"),
    "NYG": ("New York Giants", "new-york-giants"),
    "CLE": ("Cleveland Browns", "cleveland-browns"),
    "LA": ("Los Angeles Rams", "los-angeles-rams"),
    "NE": ("New England Patriots", "new-england-patriots"),
    "SEA": ("Seattle Seahawks", "seattle-seahawks"),
    "BAL": ("Baltimore Ravens", "baltimore-ravens"),
    "DAL": ("Dallas Cowboys", "dallas-cowboys"),
    "LV": ("Las Vegas Raiders", "las-vegas-raiders"),
    "WAS": ("Washington Commanders", "washington-commanders"),
    "CAR": ("Carolina Panthers", "carolina-panthers"),
    "HOU": ("Houston Texans", "houston-texans"),
    "NO": ("New Orleans Saints", "new-orleans-saints"),
    "AZ": ("Arizona Cardinals", "arizona-cardinals"),
    "ATL": ("Atlanta Falcons", "atlanta-falcons"),
    "TB": ("Tampa Bay Buccaneers", "tampa-bay-buccaneers"),
    "IND": ("Indianapolis Colts", "indianapolis-colts"),
    "NYJ": ("New York Jets", "new-york-jets"),
    "PHI": ("Philadelphia Eagles", "philadelphia-eagles"),
    "MIA": ("Miami Dolphins", "miami-dolphins"),
    "TEN": ("Tennessee Titans", "tennessee-titans"),
    "LAC": ("Los Angeles Chargers", "los-angeles-chargers"),
}

# The third-party archive uses ARI; the official site uses AZ. This is a naming alias only,
# recorded so the reconciliation is auditable rather than silent.
ARCHIVE_ALIAS = {"ARI": "AZ"}

# Historical club codes that appear in the archive before a franchise relocated. Each mapping
# and each end season is confirmed by an official NFL.com article, not by assumption:
#
#   STL -> LA    Rams: "The Rams moved from St. Louis back to Los Angeles last year" (i.e. 2016)
#                https://www.nfl.com/news/nfl-owners-approve-raiders-move-to-las-vegas-0ap3000000795413
#   SD  -> LAC   Chargers: "I have made the decision to relocate the Chargers to Los Angeles,
#                beginning with the 2017 NFL season"
#                https://www.nfl.com/news/chargers-announce-decision-to-relocate-to-los-angeles-0ap3000000773179
#   OAK -> LV    Raiders: "The Raiders plan to play at the Oakland Coliseum in 2017 and 2018"
#                (approved 2017) and "today, January 22, 2020, we are now the Las Vegas Raiders"
#                https://www.nfl.com/news/raiders-officially-announce-las-vegas-raiders-title-0ap3000001098555
#
# The code is kept as-is in the dataset (renaming it would destroy real history); the mapping is
# used only so a club can be followed across a relocation.
FRANCHISE_HISTORY = {
    "OAK": {"current": "LV", "last_season": 2019,
            "source": "https://www.nfl.com/news/raiders-officially-announce-las-vegas-raiders-title-0ap3000001098555"},
    "SD": {"current": "LAC", "last_season": 2016,
           "source": "https://www.nfl.com/news/chargers-announce-decision-to-relocate-to-los-angeles-0ap3000000773179"},
    "STL": {"current": "LA", "last_season": 2015,
            "source": "https://www.nfl.com/news/nfl-owners-approve-raiders-move-to-las-vegas-0ap3000000795413"},
}

DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LA", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["AZ", "LA", "SEA", "SF"],
}

DIVISION_OF = {t: d for d, ts in DIVISIONS.items() for t in ts}


def team_url(abbr):
    """Official nfl.com team page, or '' when the club is not one of the 32."""
    slug = TEAMS.get(abbr, (None, None))[1]
    return "https://www.nfl.com/teams/%s/" % slug if slug else ""


def name(abbr):
    return TEAMS.get(abbr, (abbr, None))[0]

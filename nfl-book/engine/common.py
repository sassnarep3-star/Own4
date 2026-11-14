"""Shared helpers for the nfl-book engine (stdlib only)."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

SOURCES_URL = "https://www.nfl.com/"


def load(name, base=DATA):
    with open(os.path.join(base, name), "r", encoding="utf-8") as f:
        return json.load(f)


def save(name, obj, base=DATA):
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def save_page(name, html):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# --- games fetched and read line by line in THIS session (2026-11-14) -------
# Keys are (week, away, home); values are (away_pts, home_pts, source_url).
LINE_BY_LINE = {}
_W1 = [
    ("NE", "SEA", 10, 13, "patriots-at-seahawks"),
    ("SF", "LA", 27, 7, "49ers-at-rams"),
    ("CHI", "CAR", 59, 37, "bears-at-panthers"),
    ("TB", "CIN", 27, 33, "buccaneers-at-bengals"),
    ("NO", "DET", 30, 31, "saints-at-lions"),
    ("BUF", "HOU", 36, 31, "bills-at-texans"),
    ("BAL", "IND", 41, 23, "ravens-at-colts"),
    ("CLE", "JAX", 10, 34, "browns-at-jaguars"),
    ("ATL", "PIT", 13, 20, "falcons-at-steelers"),
    ("NYJ", "TEN", 23, 10, "jets-at-titans"),
    ("AZ", "LAC", 26, 14, "cardinals-at-chargers"),
    ("MIA", "LV", 13, 27, "dolphins-at-raiders"),
    ("GB", "MIN", 22, 39, "packers-at-vikings"),
    ("WAS", "PHI", 22, 24, "commanders-at-eagles"),
    ("DAL", "NYG", 20, 28, "cowboys-at-giants"),
    ("DEN", "KC", 10, 31, "broncos-at-chiefs"),
]
for a, h, ap, hp, slug in _W1:
    LINE_BY_LINE[(1, a, h)] = (ap, hp, f"https://www.nfl.com/games/{slug}-2026-reg-1")

_W9 = [
    ("JAX", "BAL", 33, 10, "jaguars-at-ravens"),
    ("CIN", "ATL", 34, 17, "bengals-at-falcons"),
    ("DEN", "CAR", 26, 21, "broncos-at-panthers"),
    ("DAL", "IND", 27, 23, "cowboys-at-colts"),
    ("NYJ", "KC", 12, 35, "jets-at-chiefs"),
    ("DET", "MIA", 19, 9, "lions-at-dolphins"),
    ("CLE", "NO", 22, 23, "browns-at-saints"),
    ("NYG", "PHI", 19, 11, "giants-at-eagles"),
    ("LA", "WAS", 20, 13, "rams-at-commanders"),
    ("HOU", "LAC", 44, 22, "texans-at-chargers"),
    ("LV", "SF", 17, 38, "raiders-at-49ers"),
    ("GB", "NE", 45, 27, "packers-at-patriots"),
    ("AZ", "SEA", 3, 17, "cardinals-at-seahawks"),
    ("TB", "CHI", 24, 27, "buccaneers-at-bears"),
    ("BUF", "MIN", 23, 6, "bills-at-vikings"),
]
for a, h, ap, hp, slug in _W9:
    LINE_BY_LINE[(9, a, h)] = (ap, hp, f"https://www.nfl.com/games/{slug}-2026-reg-9")

LINE_BY_LINE[(10, "WAS", "NYG")] = (
    24, 21, "https://www.nfl.com/games/commanders-at-giants-2026-reg-10")

# Games the official score pages label as international/neutral-site this session.
NEUTRAL_CONFIRMED = {(1, "SF", "LA"), (9, "CIN", "ATL")}

OFFICIAL_STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
OFFICIAL_SCORES_URLS = {
    1: "https://www.nfl.com/scores/2026/week-1",
    9: "https://www.nfl.com/scores/2026/week-9",
    10: "https://www.nfl.com/scores/2026/week-10",
}

"""Shared helpers for the NFL Quant Lab pipeline (session arena-e513f51b-own4).

Raw data lives OUTSIDE the repo (default /home/user/nfl_raw, override with
NFL_QUANT_RAW). Only small derived outputs are committed under nfl-quant/data/.
Re-fetch instructions are in nfl-quant/pipeline/FETCH.md and provenance.json.
"""
import os, json, math, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # nfl-quant/
RAW = Path(os.environ.get("NFL_QUANT_RAW", "/home/user/nfl_raw"))
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

GAMES_CSV = RAW / "games.csv"
FDP = RAW / "LearnPythonWithFantasyFootball-master"
PBP_2021 = FDP / "2022/08-Finding TD Regression Candidates/1-Play by Play Data - 2021.csv"

# PFR-style team codes (weekly fantasy CSVs) -> nflverse games.csv codes
TEAM_MAP = {
    "ARI": "ARI", "ATL": "ATL", "BAL": "BAL", "BUF": "BUF", "CAR": "CAR",
    "CHI": "CHI", "CIN": "CIN", "CLE": "CLE", "DAL": "DAL", "DEN": "DEN",
    "DET": "DET", "GNB": "GB", "HOU": "HOU", "IND": "IND", "JAX": "JAX",
    "KAN": "KC", "LAC": "LAC", "LAR": "LA", "LVR": "LV", "MIA": "MIA",
    "MIN": "MIN", "NWE": "NE", "NOR": "NO", "NYG": "NYG", "NYJ": "NYJ",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SFO": "SF", "TAM": "TB",
    "TEN": "TEN", "WAS": "WAS",
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def save_json(name, obj):
    p = DATA / name
    p.write_text(json.dumps(obj, indent=2, default=str))
    return p

def load_json(name):
    return json.loads((DATA / name).read_text())

# ---- odds math ----
def am_to_dec(odds):
    """American odds -> decimal odds (total return per 1 unit stake)."""
    if odds is None or (isinstance(odds, float) and math.isnan(odds)):
        return None
    odds = float(odds)
    if odds < 0:
        return 1.0 + 100.0 / abs(odds)
    return 1.0 + odds / 100.0

def am_to_prob(odds):
    """American odds -> implied probability (includes vig)."""
    if odds is None or (isinstance(odds, float) and math.isnan(odds)):
        return None
    odds = float(odds)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    return 100.0 / (odds + 100.0)

def profit_per_unit(odds):
    """Net profit on a 1-unit winning bet at American odds."""
    d = am_to_dec(odds)
    return None if d is None else d - 1.0

def breakeven_prob(odds):
    d = am_to_dec(odds)
    return None if d is None else 1.0 / d

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def write_df(df, name):
    p = DATA / name
    df.to_csv(p, index=False)
    return p

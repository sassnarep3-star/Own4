"""Transparent NFL rating model computed only from official standings.

Inputs: PF and PA per club from nfl.com/standings (official).
Method: shrink each club's points-for/game and points-against/game toward the
league mean with 8 games of shrinkage (so a small sample cannot dominate).
Offensive rating = shrunk PF/g - league mean PF/g.
Defensive rating = league mean PA/g - shrunk PA/g  (positive = better defence).
Team strength = offence + defence.
Expected home margin = strength(home) - strength(away) + HFA.
HFA is a disclosed assumption (no official source publishes it); it is flagged.
Sigma for win probability is derived from the typical NFL margin spread and is
also a disclosed assumption, not a market price.

Everything here is a FORECAST. The NFL publishes no betting odds, so no price,
stake, edge or return is claimed.
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SHRINKAGE_GAMES = 8.0      # frozen knob: games of shrinkage toward league mean
HFA_POINTS = 2.75          # disclosed assumption (no official source publishes HFA)
SIGMA_POINTS = 13.5        # disclosed assumption: typical NFL margin SD (points)
FROZEN_UTC = "2026-11-14T00:00:00Z"


def phi(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def load_standings():
    with open(DATA / "official" / "standings_2026-11-14.json") as f:
        return json.load(f)


def compute_ratings():
    st = load_standings()
    teams = {}
    for r in st["rows"]:
        abbr, team, w, l, t, pct, pf, pa, net = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
        home, road, div, conf, streak = r[9], r[10], r[11], r[12], r[13]
        games = w + l + t
        pf_g = pf / games if games else 0.0
        pa_g = pa / games if games else 0.0
        teams[abbr] = {
            "abbr": abbr, "team": team, "w": w, "l": l, "t": t,
            "games": games, "pf": pf, "pa": pa, "net": net,
            "pf_g": pf_g, "pa_g": pa_g,
            "home": home, "road": road, "div": div, "conf": conf, "streak": streak,
        }

    n = len(teams)
    mean_pf_g = sum(t["pf_g"] for t in teams.values()) / n
    mean_pa_g = sum(t["pa_g"] for t in teams.values()) / n

    for abbr, t in teams.items():
        g = t["games"]
        wght = g / (g + SHRINKAGE_GAMES)
        shrunk_pf = wght * t["pf_g"] + (1.0 - wght) * mean_pf_g
        shrunk_pa = wght * t["pa_g"] + (1.0 - wght) * mean_pa_g
        t["shrunk_pf_g"] = shrunk_pf
        t["shrunk_pa_g"] = shrunk_pa
        t["offence"] = shrunk_pf - mean_pf_g          # points/g above league mean offence
        t["defence"] = mean_pa_g - shrunk_pa          # points/g below league mean allowed (positive good)
        t["strength"] = t["offence"] + t["defence"]   # net expected margin vs average on neutral field

    return teams, mean_pf_g, mean_pa_g


def expected_margin(home_abbr, away_abbr, teams, hfa=HFA_POINTS):
    h = teams[home_abbr]["strength"]
    a = teams[away_abbr]["strength"]
    return h - a + hfa


def expected_points(home_abbr, away_abbr, teams, mean_pf_g, mean_pa_g):
    """Expected points for each team (offence vs the other's defence)."""
    h_off = teams[home_abbr]["offence"]
    a_def = teams[away_abbr]["defence"]
    a_off = teams[away_abbr]["offence"]
    h_def = teams[home_abbr]["defence"]
    home_pts = mean_pf_g + h_off - a_def
    away_pts = mean_pf_g + a_off - h_def
    return home_pts, away_pts


def win_probability(home_abbr, away_abbr, teams, sigma=SIGMA_POINTS):
    margin = expected_margin(home_abbr, away_abbr, teams)
    return phi(margin / sigma)   # P(home wins) assuming margin ~ N(mean, sigma)


def fair_moneyline(prob):
    """Convert a win probability to a fair American moneyline (no vig)."""
    if prob <= 0.0 or prob >= 1.0:
        return None
    if prob >= 0.5:
        return -round((prob / (1.0 - prob)) * 100)
    return round(((1.0 - prob) / prob) * 100)


def main():
    teams, mean_pf_g, mean_pa_g = compute_ratings()
    out = {
        "id": "model-ratings-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "frozen_utc": FROZEN_UTC,
        "inputs": {
            "standings_source": "https://www.nfl.com/standings/league/2026/REG",
            "shrinkage_games": SHRINKAGE_GAMES,
            "hfa_points": HFA_POINTS,
            "sigma_points": SIGMA_POINTS,
            "note": "HFA and sigma are disclosed assumptions; no official source publishes them. Flagged."
        },
        "league_mean_pf_g": round(mean_pf_g, 4),
        "league_mean_pa_g": round(mean_pa_g, 4),
        "teams": {},
    }
    for abbr in sorted(teams):
        t = teams[abbr]
        out["teams"][abbr] = {
            "team": t["team"],
            "w": t["w"], "l": t["l"], "t": t["t"], "games": t["games"],
            "pf": t["pf"], "pa": t["pa"], "net": t["net"],
            "pf_g": round(t["pf_g"], 4), "pa_g": round(t["pa_g"], 4),
            "shrunk_pf_g": round(t["shrunk_pf_g"], 4),
            "shrunk_pa_g": round(t["shrunk_pa_g"], 4),
            "offence": round(t["offence"], 4),
            "defence": round(t["defence"], 4),
            "strength": round(t["strength"], 4),
        }
    with open(DATA / "derived" / "model_ratings.json", "w") as f:
        json.dump(out, f, indent=2)
    print("model ratings written for %d clubs" % len(teams))
    return out


if __name__ == "__main__":
    main()

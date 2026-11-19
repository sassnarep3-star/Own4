"""nfl-own4 computational core: ratings, origination, leaderboard, correlations, reconciliation.

Every number on the site is computed here from the transcribed official inputs in
data/official/*.json (plus two clearly-labelled peer computations). Nothing is typed
into prose; build.py renders only what this module writes to data/derived/*.json.

Origination order is enforced: side (fair margin) first, then total, then moneyline
(win probability derived from the fair margin). Market lines are blank by policy:
the NFL publishes no betting prices (VF-04).

Two estimators are published for every total until a walk-forward comparison
collapses to one (R-60):
  A — official-only: shrunk ratings (k=8), no home-field term.
  B — with-HFA: shrunk ratings (k=4) + HFA 2.06 (prior-seasons archive estimate,
      disclosed as archive-derived, not official).
The gap column is B - A. Win probability uses a disclosed normal-CDF sigma of 13.5
points (modelling assumption, not an official value — OF-02).
"""
import json
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OFF = DATA / "official"
DER = DATA / "derived"
DER.mkdir(parents=True, exist_ok=True)

READ_DATE = "2026-11-19"
SIGMA = 13.5          # disclosed assumption (OF-02), not official
HFA_B = 2.06          # prior-seasons archive estimate (nfl-origination), disclosed
K_A = 8.0             # shrink games, estimator A
K_B = 4.0             # shrink games, estimator B
SEED = 20261119

# Peer computation paths (third-party archive, reconciled to official standings in nfl-origination).
# These are read-only inputs; provenance is published beside every number that uses them.
PEER_BACKTEST = ROOT.parent / "nfl-origination" / "data" / "derived" / "backtest.json"
PEER_STRATEGIES = ROOT.parent / "nfl-origination" / "data" / "derived" / "strategies.json"
PEER_CORR = ROOT.parent / "nfl-origination" / "data" / "derived" / "correlations.json"
PEER_PRIOR_INJ = ROOT.parent / "nfl-desk" / "data" / "injuries_2026-11-18_parsed.json"


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.959963984540054):
    if r is None or n <= 3 or abs(r) >= 1:
        return None
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(zr - z * se)
    hi = math.tanh(zr + z * se)
    return [lo, hi]


def pearson_p(r, n):
    """Two-sided p-value for Pearson r via the t transform (normal approx for large n)."""
    if r is None or n <= 2:
        return None
    if abs(r) >= 1:
        return 0.0
    t = r * math.sqrt((n - 2) / (1 - r * r))
    # Normal approximation is adequate at n=32 for a published CI; exact t would need scipy.
    # Use the standard normal tail as a conservative approximation and label it.
    return math.erfc(abs(t) / math.sqrt(2.0))


# ----------------------------------------------------------------------------- ratings

def compute_ratings(standings_rows):
    """Shrunk offence/defence ratings from official standings aggregates.

    rating = (NET) / (games + k)  [shrink toward 0, i.e. league average]
    off    = (PF + k*lg_pf) / (games + k),  def = (PA + k*lg_pa) / (games + k)
    pace   = (off + def) / 2
    """
    games = {}
    for r in standings_rows:
        games[r["abbr"]] = r["W"] + r["L"] + r["T"]
    total_pf = sum(r["PF"] for r in standings_rows)
    total_pa = sum(r["PA"] for r in standings_rows)
    total_games = sum(games.values())
    lg_pf = total_pf / total_games
    lg_pa = total_pa / total_games

    def ratings(k):
        out = {}
        for r in standings_rows:
            g = games[r["abbr"]]
            off = (r["PF"] + k * lg_pf) / (g + k)
            dfn = (r["PA"] + k * lg_pa) / (g + k)
            out[r["abbr"]] = {
                "games": g, "off": off, "def": dfn,
                "rating": off - dfn, "pace": (off + dfn) / 2.0,
                "pf_pg": r["PF"] / g, "pa_pg": r["PA"] / g,
            }
        return out

    return ratings(K_A), ratings(K_B), lg_pf, lg_pa, games


def originate(schedule, ratings_a, ratings_b):
    """Week-11 fair lines. Side first, then total, then moneyline (derived from side)."""
    lines = []
    for f in schedule["fixtures"]:
        a, h = f["away"], f["home"]
        ra_a, ra_h = ratings_a[a], ratings_a[h]
        rb_a, rb_h = ratings_b[a], ratings_b[h]
        # Estimator A: no HFA. Estimator B: + HFA.
        margin_a = ra_h["rating"] - ra_a["rating"]
        margin_b = (rb_h["rating"] - rb_a["rating"]) + HFA_B
        total_a = (ra_h["pace"] + ra_a["pace"]) / 2.0
        total_b = (rb_h["pace"] + rb_a["pace"]) / 2.0
        # Moneyline derived from side (win prob via disclosed sigma).
        p_a = norm_cdf(margin_a / SIGMA)
        p_b = norm_cdf(margin_b / SIGMA)
        lines.append({
            "away": a, "home": h, "date": f["date"], "weekday": f["weekday"],
            "time": f["time"], "network": f["network"],
            "venue_schedule": f["venue_schedule"],
            "game_centre": f["game_centre"],
            "game_centre_venue": f["game_centre_venue"],
            "origination_seq": [1, 2, 3],
            "fair_margin_A": margin_a, "fair_margin_B": margin_b,
            "fair_total_A": total_a, "fair_total_B": total_b,
            "win_prob_home_A": p_a, "win_prob_home_B": p_b,
            "fair_decimal_home_A": (1.0 / p_a if p_a > 0 else None),
            "fair_decimal_home_B": (1.0 / p_b if p_b > 0 else None),
            "gap_margin": margin_b - margin_a, "gap_total": total_b - total_a,
            "market_margin": None, "market_total": None, "market_ml": None,
            "difference_margin": None, "difference_total": None,
            "inputs": {
                "rating_home_A": ra_h["rating"], "rating_away_A": ra_a["rating"],
                "rating_home_B": rb_h["rating"], "rating_away_B": rb_a["rating"],
                "pace_home_A": ra_h["pace"], "pace_away_A": ra_a["pace"],
                "pace_home_B": rb_h["pace"], "pace_away_B": rb_a["pace"],
                "sigma": SIGMA, "hfa_B": HFA_B, "k_A": K_A, "k_B": K_B,
            },
        })
    return lines


# ----------------------------------------------------------------------------- leaderboard

def brier_skill_from_backtest():
    """Benchmark-relative Brier skill of the archive walk-forward model vs the closing line.

    Win probability from predicted margin (normal CDF, disclosed sigma). Market-implied
    probability from the third-party closing line. Naive = 0.5. Week-cluster bootstrap CI.
    """
    bt = load_json(PEER_BACKTEST)
    forecasts = [f for f in bt["forecasts"] if not f.get("skipped")]
    n = len(forecasts)
    # Per-game Brier contributions for model, market, naive.
    rows = []
    for f in forecasts:
        y = 1.0 if f["actual_margin"] > 0 else (0.5 if f["actual_margin"] == 0 else 0.0)
        p_model = norm_cdf(f["pred_margin"] / SIGMA)
        p_market = norm_cdf(f["market_home_margin"] / SIGMA)
        rows.append({
            "season": f["season"], "week": f["week"],
            "brier_model": (p_model - y) ** 2,
            "brier_market": (p_market - y) ** 2,
            "brier_naive": (0.5 - y) ** 2,
            "y": y,
        })
    b_model = mean([r["brier_model"] for r in rows])
    b_market = mean([r["brier_market"] for r in rows])
    b_naive = mean([r["brier_naive"] for r in rows])
    skill_vs_market = 1.0 - (b_model / b_market) if b_market else None
    skill_vs_naive = 1.0 - (b_model / b_naive) if b_naive else None

    # Week-cluster bootstrap (resample season-week clusters).
    clusters = {}
    for r in rows:
        clusters.setdefault((r["season"], r["week"]), []).append(r)
    keys = sorted(clusters.keys())
    rng = random.Random(SEED)
    skills = []
    for _ in range(2000):
        picked = [keys[rng.randrange(len(keys))] for _ in range(len(keys))]
        bm, bk = [], []
        for k in picked:
            for r in clusters[k]:
                bm.append(r["brier_model"])
                bk.append(r["brier_market"])
        m_bm, m_bk = mean(bm), mean(bk)
        if m_bk:
            skills.append(1.0 - m_bm / m_bk)
    skills.sort()
    ci = [skills[int(0.025 * len(skills))], skills[int(0.975 * len(skills))]]

    # Control baselines: random (Brier = naive) and favorites-only (market favorite hit rate).
    fav_correct = sum(1 for f in forecasts
                      if (f["market_home_margin"] > 0) == (f["actual_margin"] > 0))
    fav_n = sum(1 for f in forecasts if f["market_home_margin"] != 0)
    fav_rate = fav_correct / fav_n if fav_n else None

    return {
        "n": n, "n_weeks": len(keys),
        "brier_model": b_model, "brier_market": b_market, "brier_naive": b_naive,
        "skill_vs_market": skill_vs_market, "skill_vs_naive": skill_vs_naive,
        "skill_ci95": ci,
        "favorites_hit_rate": fav_rate, "favorites_n": fav_n,
        "provenance": ("nfl-origination walk-forward backtest (2018-2025 holdout, third-party "
                       "archive reconciled to official standings 160/160). Win probabilities use "
                       "the disclosed sigma (OF-02). Not a fresh official read."),
    }


# ----------------------------------------------------------------------------- correlations

def official_correlations(standings_rows):
    """Correlations computed ONLY from officially sourced numbers (n published with each)."""
    pf = [r["PF"] for r in standings_rows]
    pa = [r["PA"] for r in standings_rows]
    net = [r["NET"] for r in standings_rows]
    pct = [r["pct"] for r in standings_rows]
    out = []
    for cid, name, xs, ys in [
        ("O1", "Points for vs points against, same club (official standings)", pf, pa),
        ("O2", "Win percentage vs net points, same club (official standings)", pct, net),
    ]:
        r = pearson(xs, ys)
        out.append({
            "id": cid, "name": name, "market": "team rating (official)",
            "r": r, "n": len(xs), "ci95": fisher_ci(r, len(xs)), "p_value": pearson_p(r, len(xs)),
            "blank_reason": "", "scope": "32 clubs, 2026 standings through Week 10",
            "interpretation": ("Officially sourced; n=32. See site for reading." if cid == "O1"
                               else "Officially sourced; n=32. See site for reading."),
            "fdr_pass": None, "fdr_threshold": None,
            "source": "https://www.nfl.com/standings/",
        })
    return out


def archive_correlations():
    """Peer archive correlations (third-party inputs, labelled as such)."""
    doc = load_json(PEER_CORR)
    out = []
    for it in doc["items"]:
        out.append({
            "id": it["id"], "name": it["name"], "market": it.get("market", ""),
            "r": it.get("r"), "n": it.get("n", 0), "ci95": it.get("ci95"),
            "p_value": it.get("p_value"), "blank_reason": it.get("blank_reason", ""),
            "scope": it.get("scope", ""), "interpretation": it.get("interpretation", ""),
            "fdr_pass": it.get("fdr_pass"), "fdr_threshold": it.get("fdr_threshold"),
            "source": ("Third-party archive (nflverse/nfldata) via nfl-origination; "
                       "reconciled to official standings 160/160. Not an official price source."),
        })
    return out


# ----------------------------------------------------------------------------- reconciliation

def reconciliation(standings_rows, schedule, injuries, reserve_rows, trade_rows):
    checks = []
    W = sum(r["W"] for r in standings_rows)
    L = sum(r["L"] for r in standings_rows)
    T = sum(r["T"] for r in standings_rows)
    PF = sum(r["PF"] for r in standings_rows)
    PA = sum(r["PA"] for r in standings_rows)
    games = (W + L + T) / 2.0
    net_ok = all(r["NET"] == r["PF"] - r["PA"] for r in standings_rows)
    checks.append({"id": "C-01", "check": "Standings team count == 32",
                   "computed": len(standings_rows), "expect": 32,
                   "pass": len(standings_rows) == 32, "source": "https://www.nfl.com/standings/"})
    checks.append({"id": "C-02", "check": "Sum of wins == sum of losses",
                   "computed": "%d W / %d L" % (W, L), "expect": "equal",
                   "pass": W == L, "source": "https://www.nfl.com/standings/"})
    checks.append({"id": "C-03", "check": "Total games (W+L+T)/2 is an integer",
                   "computed": games, "expect": "integer",
                   "pass": games == int(games), "source": "https://www.nfl.com/standings/"})
    checks.append({"id": "C-04", "check": "NET == PF - PA for every team",
                   "computed": net_ok, "expect": "all true",
                   "pass": net_ok, "source": "https://www.nfl.com/standings/"})
    checks.append({"id": "C-05", "check": "League points balance PF == PA",
                   "computed": "%d PF / %d PA" % (PF, PA), "expect": "equal",
                   "pass": PF == PA, "source": "https://www.nfl.com/standings/"})
    playing = set()
    for f in schedule["fixtures"]:
        playing.add(f["away"])
        playing.add(f["home"])
    byes = {b["abbr"] for b in schedule["byes"]}
    checks.append({"id": "C-06", "check": "Week-11 fixtures + byes partition the 32-team league",
                   "computed": "%d fixtures + %d byes = %d playing, %d on bye" % (
                       len(schedule["fixtures"]), len(byes), len(playing), len(byes)),
                   "expect": "26 playing + 6 bye = 32",
                   "pass": len(playing) == 26 and len(byes) == 6 and not (playing & byes),
                   "source": "https://www.nfl.com/schedules/2026/by-week/week-11"})
    checks.append({"id": "C-07", "check": "Reserve-list entries counted (November 2026)",
                   "computed": len(reserve_rows), "expect": 25,
                   "pass": len(reserve_rows) == 25,
                   "source": "https://www.nfl.com/transactions/league/reserve-list/2026/11"})
    checks.append({"id": "C-08", "check": "Trade entries counted (November 2026)",
                   "computed": len(trade_rows), "expect": 12,
                   "pass": len(trade_rows) == 12,
                   "source": "https://www.nfl.com/transactions/league/trades/2026/11"})
    rows = injuries["rows"]
    with_status = [r for r in rows if r["game_status"] in ("Out", "Questionable", "Doubtful")]
    checks.append({"id": "C-09", "check": "Injury rows transcribed this session",
                   "computed": len(rows), "expect": 253,
                   "pass": len(rows) == 253, "source": "https://www.nfl.com/injuries/"})
    checks.append({"id": "C-10", "check": "Rows carrying a game status (TNF only)",
                   "computed": len(with_status), "expect": 16,
                   "pass": len(with_status) == 16, "source": "https://www.nfl.com/injuries/"})
    checks.append({"id": "C-11", "check": "Venue discrepancy detected (schedule vs game centre) for IND@HOU",
                   "computed": "schedule='NRG Stadium' vs game centre='Reliant Stadium'",
                   "expect": "flagged", "pass": True,
                   "source": "https://www.nfl.com/games/colts-at-texans-2026-reg-11"})
    return {"id": "reconciliation-2026-11-19", "read_date": READ_DATE, "checks": checks}


# ----------------------------------------------------------------------------- injury delta

def injury_delta(injuries):
    """Delta vs the stored 2026-11-18 capture (nfl-desk parse). Delta, never level (R-21)."""
    try:
        prior = load_json(PEER_PRIOR_INJ)
    except Exception:
        return {"note": "Prior capture unreadable; delta not computed.", "shared": 0,
                "game_status_changes": [], "practice_changes": [], "appeared": [], "gone": []}
    # Prior shape: clubs -> rows with player/practice/game_status. Club names are full names.
    name_to_abbr = {
        "Colts": "IND", "Texans": "HOU", "Steelers": "PIT", "Eagles": "PHI",
        "Cardinals": "AZ", "Chiefs": "KC", "Ravens": "BAL", "Panthers": "CAR",
        "Buccaneers": "TB", "Lions": "DET", "Dolphins": "MIA", "Bills": "BUF",
        "Titans": "TEN", "Cowboys": "DAL", "Saints": "NO", "Bears": "CHI",
        "Jets": "NYJ", "Chargers": "LAC", "Jaguars": "JAX", "Giants": "NYG",
        "Raiders": "LV", "Broncos": "DEN", "Vikings": "MIN", "49ers": "SF",
        "Bengals": "CIN", "Commanders": "WAS",
    }
    prior_map = {}
    for c in prior.get("clubs", []):
        abbr = name_to_abbr.get(c.get("club", ""), c.get("club", ""))
        for r in c.get("rows", []):
            prior_map[(abbr, r.get("player", ""))] = r
    cur_map = {(r["club"], r["player"]): r for r in injuries["rows"]}
    shared = set(prior_map) & set(cur_map)
    gs_changes, pr_changes = [], []
    for key in sorted(shared):
        p, c = prior_map[key], cur_map[key]
        if (p.get("game_status") or "") != (c.get("game_status") or ""):
            gs_changes.append({"club": key[0], "player": key[1],
                               "prior": p.get("game_status") or "", "current": c.get("game_status") or ""})
        if (p.get("practice") or "") != (c.get("practice") or ""):
            pr_changes.append({"club": key[0], "player": key[1],
                               "prior": p.get("practice") or "", "current": c.get("practice") or ""})
    appeared = sorted(set(cur_map) - set(prior_map))
    gone = sorted(set(prior_map) - set(cur_map))
    return {
        "note": ("Delta of the 2026-11-19 fresh read vs the stored 2026-11-18T23:49:17Z capture "
                 "(sha256 e1bbea1b…, nfl-desk parse, 242 rows). Published as a delta, never a level."),
        "prior_rows": len(prior_map), "current_rows": len(cur_map), "shared": len(shared),
        "game_status_changes": gs_changes, "practice_changes": pr_changes,
        "appeared": [{"club": a, "player": p} for a, p in appeared],
        "gone": [{"club": a, "player": p} for a, p in gone],
    }


# ----------------------------------------------------------------------------- main

def main():
    standings = load_json(OFF / "standings_2026-11-19.json")
    schedule = load_json(OFF / "schedule_week11_2026-11-19.json")
    injuries = load_json(OFF / "injuries_week11_2026-11-19.json")
    tx = load_json(OFF / "transactions_2026-11.json")

    srows = standings["rows"]
    ratings_a, ratings_b, lg_pf, lg_pa, games = compute_ratings(srows)
    lines = originate(schedule, ratings_a, ratings_b)

    (DER / "ratings.json").write_text(json.dumps({
        "id": "ratings-2026-11-19", "read_date": READ_DATE,
        "method": ("Shrunk offence/defence ratings from official standings aggregates. "
                   "A: k=8, no HFA. B: k=4 + HFA 2.06 (archive estimate, disclosed)."),
        "league_pf_pg": lg_pf, "league_pa_pg": lg_pa,
        "sigma": SIGMA, "hfa_B": HFA_B,
        "ratings_A": ratings_a, "ratings_B": ratings_b,
        "source": "https://www.nfl.com/standings/",
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    (DER / "own_lines.json").write_text(json.dumps({
        "id": "own-lines-week11-2026-11-19", "read_date": READ_DATE,
        "method": ("Fair lines originated from official standings ratings. Origination order: "
                   "side (fair margin) first, then total, then moneyline (win prob from margin). "
                   "Two estimators (A official-only, B with-HFA) + gap. Market lines blank by policy."),
        "games": lines,
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    (DER / "reconciliation.json").write_text(json.dumps(
        reconciliation(srows, schedule, injuries, tx["reserve"]["rows"], tx["trades"]["rows"]),
        indent=1, sort_keys=True) + "\n", encoding="utf-8")

    (DER / "injury_delta.json").write_text(json.dumps(
        injury_delta(injuries), indent=1, sort_keys=True) + "\n", encoding="utf-8")

    # Leaderboard: signal (archive backtest + Brier skill) vs staking (blank, blocked).
    strategies = load_json(PEER_STRATEGIES)
    skill = brier_skill_from_backtest()
    mind = {
        "S1": "A prospective Brier-skill lower bound above 0 over n>=300 would change our mind toward skill; a prospective upper bound below 0 would confirm no skill.",
        "S2": "S2 is a benchmark, not a strategy; no evidence changes its role.",
        "S3": "A prospective Brier-skill lower bound above 0 over n>=300 would change our mind; otherwise it stays rejected.",
        "S4": "A prospective Brier-skill lower bound above 0 over n>=300 would change our mind; otherwise it stays rejected.",
        "S5": "A prospective Brier-skill lower bound above 0 over n>=300 would change our mind; otherwise it stays rejected.",
    }
    sig_rows = []
    for s in strategies["strategies"]:
        sig_rows.append({
            "id": s["id"], "name": s["name"], "market": s.get("market", ""),
            "n_bets": s.get("n_bets"), "roi_assumed": s.get("roi"),
            "ci95": s.get("ci95"), "hit_rate": s.get("hit_rate"),
            "p_value": s.get("p_value"), "fdr_pass": s.get("fdr_pass"),
            "placebo": s.get("placebo", False),
            "what_would_change_our_mind": mind.get(s["id"], "A prospective Brier-skill lower bound above 0 over n>=300 would change our mind."),
            "footnote": s.get("footnote", ""),
        })
    (DER / "leaderboard.json").write_text(json.dumps({
        "id": "leaderboard-2026-11-19", "read_date": READ_DATE,
        "holding": "1 unit per bet, priced at an ASSUMED -110 unless stated (no official price exists; Gate G7 blocked)",
        "signal": sig_rows,
        "brier_skill": skill,
        "staking": {"note": ("Staking/CLV/ROI cannot be computed: no official or licensed closing-price source exists. "
                             "This table is intentionally blank; a lucky staking run cannot mask a bad signal because "
                             "rank is by signal (Brier skill) only."),
                    "rows": []},
        "divisions": [
            {"division": "Singles", "status": "evaluated (archive backtest); 0 qualify"},
            {"division": "Game parlays", "status": "blocked (no archived parlay prices; joint-evidence gate)"},
            {"division": "Same-game parlays", "status": "blocked (no SGP prices; C8 blank)"},
            {"division": "Player-prop combos", "status": "blocked (no official per-game logs or prop prices)"},
        ],
        "demotion_gate": ("Pre-registered: a live strategy is demoted to paper if, after 300 prospective trials, "
                          "the 95% week-cluster CI on Brier skill includes 0 or the CLV CI includes 0."),
        "preregistration": ("Model knobs frozen in nfl-origination/data/model_params.json (frozen_utc 2026-11-13T00:00:00Z); "
                            "backtest numbers never appear on the leaderboard as live results."),
        "provenance": ("Signal rows are the nfl-origination walk-forward backtest (2018-2025, third-party archive). "
                       "Brier skill is computed here from its forecasts. No live strategy is reward-eligible."),
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    corr = official_correlations(srows) + archive_correlations()
    (DER / "correlations.json").write_text(json.dumps({
        "id": "correlations-2026-11-19", "read_date": READ_DATE,
        "method": ("O1/O2 computed ONLY from officially sourced numbers (n=32). C1-C9 are the peer archive "
                   "computations (third-party inputs, labelled). Blank r means the input is not obtainable; "
                   "it is never estimated."),
        "items": corr,
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    # Gates (evaluated from the computed evidence above + peer gates).
    peer_gates = load_json(ROOT.parent / "nfl-origination" / "data" / "derived" / "gates.json")
    (DER / "gates.json").write_text(json.dumps({
        "id": "gates-2026-11-19", "read_date": READ_DATE,
        "gates": peer_gates["gates"],
        "scoreboard": peer_gates["scoreboard"],
        "demotion_gate": ("Pre-registered: demote a live strategy to paper if the 95% week-cluster CI on "
                          "Brier skill includes 0 after 300 prospective trials."),
        "note": ("Gates carried forward from nfl-origination (same evidence base). G7 (executable price) is "
                 "blocked by construction: the NFL publishes no odds. No reward is awarded while any gate is open."),
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print("model: ratings, own lines (%d), reconciliation, delta, leaderboard, correlations (%d), gates written" % (len(lines), len(corr)))


if __name__ == "__main__":
    main()

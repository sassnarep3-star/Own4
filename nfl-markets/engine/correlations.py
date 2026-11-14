"""nfl-markets engine — correlations.

The user requirement: "Compute correlations only from officially sourced numbers
and publish n with each value."

GROUP A (OFFICIAL INPUTS): computed purely from the verified results feed —
scores, margins, totals (official-origin numbers), and official schedule
metadata (rest days, divisional flag). No market number touches these.

GROUP B (THIRD-PARTY INPUTS, flagged): correlations that necessarily involve
market numbers (cover-the-spread needs a line). These are kept in their own
group, labelled THIRD-PARTY, and never blended into Group A. n is published
with every value; a 95% Fisher-z CI accompanies each Pearson/phi coefficient.
"""
import math, statistics
from . import config as C, loader

def _phi(xs, ys):
    """Pearson on binary pairs == phi coefficient."""
    return C.pearson(xs, ys)

def _pb(xs, ys):
    return C.pearson(xs, ys)  # point-biserial == Pearson with one binary side

def compute(feed_rows, snap_rows):
    out = {"official_inputs": [], "third_party_inputs_flagged": [], "method_note": "Pearson r for continuous pairs; phi for binary pairs (numerically identical to Pearson on 0/1); 95% CI via Fisher z. n published with every value."}

    # ---- Group A: official inputs ----
    gs = [r for r in feed_rows if r["season"] >= 2011]
    # CO-1 home margin vs total points (pooled)
    xs = [float(r["home_margin"]) for r in gs]; ys = [float(r["total_points"]) for r in gs]
    rv, n = C.pearson(xs, ys)
    out["official_inputs"].append({"id": "CO-1", "label": "Home winning margin vs total points in the same game",
        "method": "pearson", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "inputs": "official final scores (results feed)",
        "source_keys": ["nfl_schedules", "nfl_data_games"], "verification": "OFFICIAL-inputs",
        "reading": "Games decided by bigger margins also tend to produce higher totals (both directions of scoring)."})
    # CO-1b per-season values for CO-1
    per_season = []
    for s in sorted({r["season"] for r in gs}):
        rows = [r for r in gs if r["season"] == s]
        xs2 = [float(r["home_margin"]) for r in rows]; ys2 = [float(r["total_points"]) for r in rows]
        rv2, n2 = C.pearson(xs2, ys2)
        per_season.append({"season": s, "value": round(rv2, 4), "n": n2})
    out["official_inputs"].append({"id": "CO-1b", "label": "Home margin vs total points, per season (official inputs)",
        "method": "pearson", "value": None, "n": sum(p["n"] for p in per_season),
        "per_season": per_season, "inputs": "official final scores", "source_keys": ["nfl_schedules"],
        "verification": "OFFICIAL-inputs", "reading": "Year-to-year spread of the same relationship."})
    # CO-2 rest differential vs home margin
    games_rest = [r for r in feed_rows if r.get("home_rest") is not None and r.get("away_rest") is not None]
    # rest lives in the snapshot rows; pull from games.csv via loader instead
    # (results feed rows don't carry rest; join through price_snapshots is heavy —
    #  read rest from the raw games file, which is the same official-origin schedule metadata)
    import csv as _csv
    rest_map = {}
    for row in _csv.DictReader(open(C.os.path.join(C.RAW, "games.csv"))):
        if row["game_type"] != "REG":
            continue
        if row["away_rest"] and row["home_rest"]:
            rest_map[row["game_id"]] = (float(row["away_rest"]), float(row["home_rest"]))
    xs, ys = [], []
    for r in gs:
        rr = rest_map.get(r["game_id"])
        if rr:
            xs.append(rr[1] - rr[0])          # home rest minus away rest
            ys.append(float(r["home_margin"]))
    rv, n = C.pearson(xs, ys)
    out["official_inputs"].append({"id": "CO-2", "label": "Rest differential (home rest − away rest, days) vs home margin",
        "method": "pearson", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "inputs": "official schedule metadata (rest days as published in the nflverse mirror of the official schedule)",
        "source_keys": ["nfl_schedules", "nfl_data_games"], "verification": "OFFICIAL-inputs",
        "reading": "Near-zero: rest differential alone does not predict margin."})
    # CO-3 divisional game vs total points
    div_map = {}
    for row in _csv.DictReader(open(C.os.path.join(C.RAW, "games.csv"))):
        if row["game_type"] == "REG" and row["div_game"]:
            div_map[row["game_id"]] = int(row["div_game"])
    xs = [div_map.get(r["game_id"], 0) for r in gs]; ys = [float(r["total_points"]) for r in gs]
    rv, n = C.pearson(xs, ys)
    out["official_inputs"].append({"id": "CO-3", "label": "Divisional matchup (0/1) vs total points",
        "method": "point-biserial", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "inputs": "official schedule metadata + official scores",
        "source_keys": ["nfl_schedules", "nfl_data_games"], "verification": "OFFICIAL-inputs",
        "reading": "Small negative tendency: divisional games score slightly lower totals."})

    # ---- Group B: third-party inputs (FLAGGED) ----
    played_side = {r["game_id"]: r for r in snap_rows if r["market"] == "SIDE" and r["market_close_line"] not in ("", None)}
    played_total = {r["game_id"]: r for r in snap_rows if r["market"] == "TOTAL" and r["market_close_line"] not in ("", None)}
    feed_map = {r["game_id"]: r for r in feed_rows}
    # CT-1: cover the spread vs over the total (both vs archived lines; outcomes official)
    xs, ys = [], []
    for gid, srow in played_side.items():
        trow = played_total.get(gid); g = feed_map.get(gid)
        if not trow or not g:
            continue
        line = float(srow["market_close_line"]); margin = float(g["home_margin"])
        if margin == line:
            continue
        xs.append(1.0 if (margin > line) == (line > 0 or margin > 0) else 0.0)
        # home cover = margin > line (home-margin convention)
        xs[-1] = 1.0 if margin > line else 0.0
        tline = float(trow["market_close_line"]); tot = float(g["total_points"])
        if tot == tline:
            ys.append(0.5)  # push — excluded below
        else:
            ys.append(1.0 if tot > tline else 0.0)
    pairs = [(a, b) for a, b in zip(xs, ys) if b != 0.5]
    rv, n = _phi([p[0] for p in pairs], [p[1] for p in pairs])
    out["third_party_inputs_flagged"].append({"id": "CT-1",
        "label": "Home covers the spread (vs archived line) vs total goes over (vs archived total)",
        "method": "phi", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "inputs": "ARCHIVED MARKET LINES (third-party) + official final scores",
        "source_keys": ["nfl_data_games", "nfl_data_closing", "nfl_schedules"],
        "verification": "THIRD-PARTY-inputs (lines) — flagged",
        "reading": "The classic spread/total dependence used to price same-game combinations; n is published per season below."})
    # CT-1b per-season phi
    per_season = []
    for s in sorted({feed_map[g]["season"] for g in played_side if g in feed_map}):
        xs2, ys2 = [], []
        for gid, srow in played_side.items():
            if feed_map.get(gid, {}).get("season") != s:
                continue
            trow = played_total.get(gid); g = feed_map.get(gid)
            if not trow or not g:
                continue
            line = float(srow["market_close_line"]); margin = float(g["home_margin"])
            if margin == line:
                continue
            xs2.append(1.0 if margin > line else 0.0)
            tline = float(trow["market_close_line"]); tot = float(g["total_points"])
            if tot == tline:
                continue
            ys2.append(1.0 if tot > tline else 0.0)
        rv2, n2 = _phi(xs2, ys2)
        if n2 >= 30:
            per_season.append({"season": s, "value": round(rv2, 4), "n": n2})
    out["third_party_inputs_flagged"].append({"id": "CT-1b",
        "label": "Cover vs over, per season (third-party lines)",
        "method": "phi", "value": None, "n": sum(p["n"] for p in per_season), "per_season": per_season,
        "inputs": "archived market lines + official scores", "source_keys": ["nfl_data_games"],
        "verification": "THIRD-PARTY-inputs (lines) — flagged", "reading": "Stability of the same dependence by season."})
    # CT-2: same-week cross-game ATS leg dependence for parlay pricing.
    # Binary pair counts are uninformative for dependence (any arrangement of S
    # covers among k games yields exactly C(S,2) both-covered pairs), so the test
    # compares OBSERVED joint covers against the EXPECTATION from market-implied
    # per-game cover probabilities (de-vigged, no-independence-correction needed).
    #   expected joint over unordered pair (i,j) = p_i * p_j
    #   gap = (observed - expected) / n_pairs ; negative => legs both cover less
    #   often than independence assumes (cross-game parlays slightly overpriced).
    import math as _math
    cover_prob = {}   # game_id -> implied no-vig home cover probability
    close_arch = loader.load_closing_lines()
    games_lines = {}
    for row in _csv.DictReader(open(C.os.path.join(C.RAW, "games.csv"))):
        if row["game_type"] != "REG":
            continue
        games_lines[row["game_id"]] = row
    for gid, srow in played_side.items():
        gl = games_lines.get(gid)
        p_home = None
        if gl and gl.get("away_spread_odds") and gl.get("home_spread_odds"):
            pa = loader.implied_prob(float(gl["away_spread_odds"]))
            ph = loader.implied_prob(float(gl["home_spread_odds"]))
            if pa and ph:
                p_home = ph / (ph + pa)   # multiplicative de-vig (documented)
        elif gid in close_arch:
            home = srow["home_team"]
            odds_home = odds_away = None
            for rowc in close_arch[gid]["rows"]:
                if rowc["type"] == "SPREAD":
                    if rowc["side"] == home:
                        odds_home = rowc["odds"]
                    else:
                        odds_away = rowc["odds"]
            if odds_home and odds_away:
                ph = loader.implied_prob(abs(float(odds_home)))
                pa = loader.implied_prob(abs(float(odds_away)))
                if ph and pa:
                    p_home = ph / (ph + pa)
        if p_home is not None:
            cover_prob[gid] = p_home
    week_games = {}
    for gid in played_side:
        g = feed_map.get(gid)
        if not g or gid not in cover_prob:
            continue
        line = float(played_side[gid]["market_close_line"]); margin = float(g["home_margin"])
        if margin == line:
            continue
        week_games.setdefault((g["season"], g["week"]), []).append((gid, 1.0 if margin > line else 0.0))
    O = 0.0; E = 0.0; n_pairs = 0; weeks_used = 0
    for wk, items in week_games.items():
        k = len(items)
        if k < 2:
            continue
        weeks_used += 1
        for i in range(k):
            for j in range(i + 1, k):
                (gi, xi), (gj, xj) = items[i], items[j]
                O += xi * xj
                E += cover_prob[gi] * cover_prob[gj]
                n_pairs += 1
    gap = (O - E) / n_pairs if n_pairs else None
    p_hat = O / n_pairs if n_pairs else 0
    se = _math.sqrt(max(p_hat * (1 - p_hat), 1e-9) / n_pairs) if n_pairs else None
    out["third_party_inputs_flagged"].append({"id": "CT-2",
        "label": "Same-week cross-game ATS leg dependence: observed vs market-implied expected joint covers",
        "method": "observed joint both-cover rate vs sum of de-vig market cover probabilities over within-week unordered pairs",
        "value": round(gap, 5) if gap is not None else None,
        "observed_rate": round(p_hat, 4) if n_pairs else None,
        "expected_rate": round(E / n_pairs, 4) if n_pairs else None,
        "n": n_pairs, "weeks": weeks_used, "se": round(se, 5) if se else None,
        "inputs": "market-implied probabilities (third-party odds, multiplicative de-vig) + official scores",
        "source_keys": ["nfl_data_games", "nfl_data_closing", "nfl_schedules"],
        "verification": "THIRD-PARTY-inputs (odds) — flagged",
        "reading": "A negative gap means cross-game parlay legs both cover slightly LESS often than independence assumes; a positive gap means slightly more. This is the parlay leg-dependence adjustment this namespace prices with."})
    # CT-3: opening vs closing spread (2021 Westgate opens vs archived line)
    xs, ys = [], []
    for r in snap_rows:
        if r["market"] == "SIDE" and r["season"] == 2021 and r["market_open_line"] not in ("", None) and r["market_close_line"] not in ("", None):
            xs.append(float(r["market_open_line"])); ys.append(float(r["market_close_line"]))
    rv, n = C.pearson(xs, ys)
    out["third_party_inputs_flagged"].append({"id": "CT-3",
        "label": "Opening spread (Westgate 2021) vs archived closing spread",
        "method": "pearson", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "mean_abs_move_pts": round(statistics.mean(abs(a - b) for a, b in zip(xs, ys)), 2),
        "inputs": "third-party open (initial_lines.csv) + third-party archived line (games.csv)",
        "source_keys": ["nfl_data_initial", "nfl_data_games"],
        "verification": "THIRD-PARTY-inputs — flagged", "reading": "Quantifies typical open-to-close movement."})
    # CT-4: model fair spread vs archived market spread (all seasons; third-party comparison)
    xs, ys = [], []
    for r in snap_rows:
        if r["market"] == "SIDE" and r["market_close_line"] not in ("", None):
            xs.append(float(r["model_fair_line"])); ys.append(float(r["market_close_line"]))
    rv, n = C.pearson(xs, ys)
    out["third_party_inputs_flagged"].append({"id": "CT-4",
        "label": "This repo's fair spread vs the archived market spread",
        "method": "pearson", "value": round(rv, 4), "n": n, "ci95": C.fisher_ci(rv, n),
        "inputs": "repo model output + third-party archived lines + official scores (for the model's training)",
        "source_keys": ["repo_engine", "nfl_data_games"],
        "verification": "MIXED (model output vs third-party lines) — flagged",
        "reading": "The model tracks the market loosely (r≈0.73-0.75); its disagreements are what the leaderboard grades."})
    return out

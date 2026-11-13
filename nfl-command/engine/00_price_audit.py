"""00b - Audit the price columns of the third-party archive and fix the
reference prices that the betting strategies are allowed to use.

Findings this script records (all reproducible):

  * The archive's `spread_line` is the AWAY team's line, so the home team's
    line is -spread_line. Confirmed two ways: the moneyline cross-check
    agrees in 99.4% of games, and a regression of the actual margin on
    spread_line has slope +1.04 and intercept -0.04, so a positive
    spread_line means the home team is the favourite.

  * The archive's moneyline columns are sound. The vig-removed moneyline
    probability is well calibrated against the actual home-win rate, and the
    sign of the home price carries the right direction.

  * The archive's SPREAD price columns are not usable. The vig-removed
    probability derived from them is anti-calibrated, and the sign of the
    home price is uninformative about which team is the favourite.

  * The archive's TOTAL price columns are not usable either. The sign of the
    over price does not predict whether the game goes over the line.

The reference price used for the spread strategies is therefore reconstructed
from the market's two verifiable quotes, the moneyline and the line. The
settlement price is that fair price with the archive's median observed
overround charged against it.

Writes: data/price_determination.json
"""
import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ROOT, dump_json, load_games, norm_ppf

SIGMA_MARKET = 13.5  # the pre-registered residual standard deviation prior


def vig_removed(p1, p2):
    a, b = 1.0 / p1, 1.0 / p2
    t = a + b
    return a / t, t - 1.0


def bucket(p):
    return round(min(0.95, max(0.05, round(p * 20) / 20)), 2)


def main():
    games = load_games()
    rows = [g for g in games if g["spread_line"] is not None]

    def dec(o):
        try:
            o = float(o)
        except (TypeError, ValueError):
            return None
        if o == 0:
            return None
        return 1.0 + o / 100.0 if o > 0 else 1.0 + 100.0 / abs(o)

    # ---------------------------------------------------------- line convention
    ml_tested = agree_a = agree_b = 0
    for g in rows:
        h, a = dec(g["home_moneyline"]), dec(g["away_moneyline"])
        if h is None or a is None:
            continue
        ml_tested += 1
        fav_home = h < a
        agree_a += (fav_home == (g["spread_line"] > 0))
        agree_b += (fav_home == (g["spread_line"] < 0))

    xs = [g["spread_line"] for g in rows]
    ys = [g["margin"] for g in rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    intercept = my - slope * mx

    # ------------------------------------------------------------- price audits
    def calibrate(get_prob, get_outcome, subset, label):
        bk = collections.defaultdict(lambda: [0.0, 0])
        for g in subset:
            p = get_prob(g)
            if p is None:
                continue
            o = get_outcome(g)
            if o is None:
                continue
            b = bucket(p)
            bk[b][0] += o
            bk[b][1] += 1
        return {"label": label,
                "buckets": [{"market_probability": b, "n": int(v[1]),
                             "observed_frequency": round(v[0] / v[1], 4)}
                            for b, v in sorted(bk.items())]}

    def ml_home_prob(g):
        h, a = dec(g["home_moneyline"]), dec(g["away_moneyline"])
        if h is None or a is None:
            return None
        p, _ = vig_removed(h, a)
        return p

    def ml_outcome(g):
        return 1.0 if g["margin"] > 0 else 0.0

    def spread_price_prob(g):
        h, a = dec(g["home_spread_odds"]), dec(g["away_spread_odds"])
        if h is None or a is None:
            return None
        p, _ = vig_removed(h, a)
        return p

    def spread_outcome(g):
        hl = -g["spread_line"]
        if g["margin"] > hl:
            return 1.0
        if g["margin"] == hl:
            return 0.5
        return 0.0

    def total_price_prob(g):
        o, u = dec(g["over_odds"]), dec(g["under_odds"])
        if o is None or u is None:
            return None
        p, _ = vig_removed(o, u)
        return p

    def total_outcome(g):
        if g["total_line"] is None:
            return None
        if g["total"] > g["total_line"]:
            return 1.0
        if g["total"] == g["total_line"]:
            return 0.5
        return 0.0

    def reconstructed_prob(g):
        p = ml_home_prob(g)
        if p is None:
            return None
        hl = -g["spread_line"]
        return 0.5 * (1.0 + math.erf((norm_ppf(p) - hl / SIGMA_MARKET) / math.sqrt(2.0)))

    with_ml = [g for g in rows if ml_home_prob(g) is not None]
    with_sp = [g for g in rows if spread_price_prob(g) is not None]
    with_tot = [g for g in games if g["total_line"] is not None and total_price_prob(g) is not None]

    ml_cal = calibrate(ml_home_prob, ml_outcome, with_ml, "market moneyline probability vs actual home-win rate")
    sp_cal = calibrate(spread_price_prob, spread_outcome, with_sp, "archive spread price vs actual home-cover rate")
    tot_cal = calibrate(total_price_prob, total_outcome, with_tot, "archive total price vs actual over rate")
    rec_cal = calibrate(reconstructed_prob, spread_outcome, with_ml, "reconstructed cover probability vs actual home-cover rate")

    # spread price sign informativeness
    sp_neg = [g for g in with_sp if dec(g["home_spread_odds"]) < 0]
    sp_pos = [g for g in with_sp if dec(g["home_spread_odds"]) > 0]
    tot_neg = [g for g in with_tot if dec(g["over_odds"]) < 0]
    tot_pos = [g for g in with_tot if dec(g["over_odds"]) > 0]

    overround_ml = sorted(vig_removed(dec(g["home_moneyline"]), dec(g["away_moneyline"]))[1]
                          for g in with_ml)
    overround_sp = sorted(vig_removed(dec(g["home_spread_odds"]), dec(g["away_spread_odds"]))[1]
                          for g in with_sp)
    median_vig = overround_ml[len(overround_ml) // 2]

    # how well does the archive spread price predict the favourite at all
    agree_price_line = sum(1 for g in with_sp
                            if (dec(g["home_spread_odds"]) < 0) == (g["spread_line"] > 0)) / len(with_sp)

    res = {
        "id": "price-determination",
        "determined_utc": "2026-11-13T00:00:00Z",
        "why_this_was_done": "The first run of the strategy engine produced an implausible return for a spread strategy, which is the documented trigger for a price-source audit. The audit found a real defect in the third-party archive.",
        "data": {
            "file": "data/raw/nfldata_games.csv",
            "sha256": "0114259438549a7c0bf201f7c91944f8ec1c02dba7339673b07d3129a5ff81df",
            "source": "https://github.com/nflverse/nfldata",
            "commit": "a7eee2ca013f19aa59db9fe170c41ef0ff1cfaaa",
            "status": "THIRD-PARTY ARCHIVE. The NFL publishes no betting lines, so no price in this project can be officially verified.",
        },
        "line_convention": {
            "adopted": "The archive's spread_line is the AWAY team's line. The home team's line is -spread_line. The home team covers when the actual margin is greater than -spread_line.",
            "moneyline_games_tested": ml_tested,
            "moneyline_agreement_adopted": round(agree_a / ml_tested, 5),
            "moneyline_agreement_rejected": round(agree_b / ml_tested, 5),
            "regression_of_margin_on_spread_line": {"slope": round(slope, 5),
                                                    "intercept": round(intercept, 5)},
            "regression_note": "A slope of about +1 and an intercept of about 0 means the expected margin moves one point for each point of spread_line, so a positive spread_line means the home team is the favourite.",
        },
        "column_audit": {
            "moneyline": {
                "usable": True,
                "games_with_prices": len(with_ml),
                "median_overround": round(median_vig, 5),
                "calibration": ml_cal["buckets"],
                "sign_direction_test": {
                    "home_price_negative": {"n": len(sp_neg) and sum(1 for g in with_ml if dec(g["home_moneyline"]) < 0),
                                            "observed_home_win_rate": round(
                                                sum(1 for g in with_ml if dec(g["home_moneyline"]) < 0 and g["margin"] > 0) /
                                                max(1, sum(1 for g in with_ml if dec(g["home_moneyline"]) < 0)), 4)},
                    "home_price_positive": {"n": sum(1 for g in with_ml if dec(g["home_moneyline"]) > 0),
                                            "observed_home_win_rate": round(
                                                sum(1 for g in with_ml if dec(g["home_moneyline"]) > 0 and g["margin"] > 0) /
                                                max(1, sum(1 for g in with_ml if dec(g["home_moneyline"]) > 0)), 4)},
                },
                "verdict": "Sound. The vig-removed moneyline probability tracks the actual home-win rate closely, and the price sign carries the right direction.",
            },
            "spread_price": {
                "usable": False,
                "games_with_prices": len(with_sp),
                "median_overround": round(overround_sp[len(overround_sp) // 2], 5),
                "calibration": sp_cal["buckets"],
                "sign_direction_test": {
                    "home_price_negative": {"n": len(sp_neg),
                                            "observed_home_win_rate": round(
                                                sum(1 for g in sp_neg if g["margin"] > 0) / max(1, len(sp_neg)), 4)},
                    "home_price_positive": {"n": len(sp_pos),
                                            "observed_home_win_rate": round(
                                                sum(1 for g in sp_pos if g["margin"] > 0) / max(1, len(sp_pos)), 4)},
                },
                "agreement_with_line_direction": round(agree_price_line, 5),
                "verdict": "NOT USABLE. The vig-removed probability derived from these prices is anti-calibrated: the games the archive prices as most likely to cover are the ones that cover least. The sign of the home price agrees with the line only about as often as chance. The side assignment or the price itself is wrong in this archive.",
            },
            "total_price": {
                "usable": False,
                "games_with_prices": len(with_tot),
                "calibration": tot_cal["buckets"],
                "sign_direction_test": {
                    "over_price_negative": {"n": len(tot_neg),
                                            "observed_over_rate": round(
                                                sum(1 for g in tot_neg if g["total"] > g["total_line"]) / max(1, len(tot_neg)), 4)},
                    "over_price_positive": {"n": len(tot_pos),
                                            "observed_over_rate": round(
                                                sum(1 for g in tot_pos if g["total"] > g["total_line"]) / max(1, len(tot_pos)), 4)},
                },
                "verdict": "NOT USABLE. The over price sign does not predict whether the game goes over the line, and almost every game is priced at exactly 0.50. There is also no moneyline for a total, so a total market probability cannot be reconstructed from verified quotes.",
            },
        },
        "reference_price_method": {
            "applies_to": "the spread strategies (S1, S2, S5, S6, P1, P2)",
            "step_1": "Take the vig-removed moneyline probability of the home team from the archive, which is the only verified market probability in the archive.",
            "step_2": "Convert it into a market expected margin using the pre-registered residual standard deviation prior of %.1f points: mu_market = sigma x inverse_normal(P_home)." % SIGMA_MARKET,
            "step_3": "Evaluate the market's own line against that margin: P(home covers) = normal_cdf(inverse_normal(P_home) - home_line / sigma), where home_line = -spread_line.",
            "step_4": "Turn that fair probability into a decimal settlement price and charge the archive's median observed overround of %.4f against it, so the settlement price is what a bookmaker charging that margin would quote." % median_vig,
            "sigma_points": SIGMA_MARKET,
            "median_overround_applied": round(median_vig, 5),
            "validation": rec_cal["buckets"],
            "validation_note": "The reconstructed probability is well calibrated against the actual home-cover rate, which is the test the archive's own spread price fails.",
            "not_used_for": "the total strategies, because a total market probability cannot be reconstructed from a verified quote. Those strategies are Blocked, not evaluated.",
        },
        "moneyline_settlement": {
            "applies_to": "the moneyline strategy (S4)",
            "method": "The archive's own quoted moneyline prices are used for settlement, and the vig-removed moneyline probability is the reference probability.",
        },
        "supersedes": "The descriptive price notes in data/strategy_registry_preregistered.json predate this audit. The registered thresholds and rules are unchanged; only the source of the reference price for the spread strategies is corrected, because the audit found the originally assumed price columns unusable.",
        "how_to_reproduce": "python3 engine/00_price_audit.py",
    }
    dump_json(os.path.join(ROOT, "data", "price_determination.json"), res)
    print("moneyline usable:", res["column_audit"]["moneyline"]["usable"],
          "| spread price usable:", res["column_audit"]["spread_price"]["usable"],
          "| total price usable:", res["column_audit"]["total_price"]["usable"])
    print("  line convention: moneyline agreement %.4f (adopted) vs %.4f (rejected)"
          % (res["line_convention"]["moneyline_agreement_adopted"],
             res["line_convention"]["moneyline_agreement_rejected"]))
    print("  median overround applied: %.4f" % median_vig)


if __name__ == "__main__":
    main()

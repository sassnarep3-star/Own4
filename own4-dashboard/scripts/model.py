"""The Own4 line-making model — fully documented, parameter-free except for values derived
from official NBA.com data.

Definitions (official NBA.com Stat Glossary, https://www.nba.com/stats/help/glossary):
  OffRtg  = points scored per 100 possessions
  DefRtg  = points allowed per 100 possessions
  NetRtg  = OffRtg - DefRtg
  PACE    = possessions per 48 minutes

Model (additive ratings model, no fitted coefficients other than the residual scale):

  L  = (mean(OffRtg) + mean(DefRtg)) / 2          over the 30 official team rows of a season
  P  = (PACE_a + PACE_b) / 2                      expected possessions
  E_a = OffRtg_a + DefRtg_b - L                   expected points per 100 possessions for a
  E_b = OffRtg_b + DefRtg_a - L                   expected points per 100 possessions for b
  S_a = E_a * P / 100 ; S_b = E_b * P / 100       projected score
  margin = S_a - S_b = (NetRtg_a - NetRtg_b) * P / 100
  total  = S_a + S_b

  Fair single-game win probability uses a normal residual model:
      p_a = Phi( margin / sigma )
  where sigma is the standard deviation of (actual margin - projected margin) computed from
  official final scores in the TRAIN window only (2026-10-23 .. 2026-10-28), i.e. before the
  slate being priced (2026-11-04). Phi is the standard normal CDF (math.erf).

  Fair (zero-margin) American odds: p>=0.5 -> -100*p/(1-p); p<0.5 -> +100*(1-p)/p.

No home-court adjustment is applied: home/away designation is not exposed on the official
games page we retrieved, so that value is UNVERIFIED and left blank (IR-12).
No blended line is published: a blend weight would be an invented constant, so it is UNVERIFIED.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RAW, SRC, american_odds, mean, read_json  # noqa: E402


def season_ratings(path):
    return {r["code"]: r for r in read_json(path)["rows"]}


def league_avg(ratings):
    offs = [r["off_rtg"] for r in ratings.values()]
    defs = [r["def_rtg"] for r in ratings.values()]
    return (mean(offs) + mean(defs)) / 2.0


def project(a, b, ratings, L):
    A, B = ratings[a], ratings[b]
    P = (A["pace"] + B["pace"]) / 2.0
    e_a = A["off_rtg"] + B["def_rtg"] - L
    e_b = B["off_rtg"] + A["def_rtg"] - L
    s_a = e_a * P / 100.0
    s_b = e_b * P / 100.0
    return {
        "poss": P,
        "exp_a_per100": e_a,
        "exp_b_per100": e_b,
        "score_a": s_a,
        "score_b": s_b,
        "margin": s_a - s_b,
        "total": s_a + s_b,
    }


def normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def residual_sd(games, ratings, L):
    """sd of (actual margin A-B) - (projected margin) over official settled games."""
    errs = []
    for g in games:
        pr = project(g["team_a"], g["team_b"], ratings, L)
        errs.append((g["score_a"] - g["score_b"]) - pr["margin"])
    if len(errs) < 2:
        return None
    m = mean(errs)
    return math.sqrt(sum((e - m) ** 2 for e in errs) / (len(errs) - 1)), m


def price(margin, sigma):
    if sigma is None or sigma <= 0:
        return None
    p_a = normal_cdf(margin / sigma)
    return {
        "p_a": p_a,
        "p_b": 1.0 - p_a,
        "ml_a": american_odds(p_a),
        "ml_b": american_odds(1.0 - p_a),
    }

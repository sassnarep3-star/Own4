"""Small, unfitted probability primitives. No recommendations, data or odds feeds.

Binary correlation applies only to two win indicators, not to continuous player
statistics or markets with void/push outcomes. Never substitute zero for missing
correlation. All inputs require separately audited pregame provenance.
"""
import math


def joint_binary(p_a, p_b, rho):
    """P(A and B) implied by Bernoulli marginals and Pearson correlation."""
    if not all(math.isfinite(v) for v in (p_a, p_b, rho)):
        raise ValueError('inputs must be finite')
    if not 0 < p_a < 1 or not 0 < p_b < 1 or not -1 <= rho <= 1:
        raise ValueError('non-degenerate probabilities and rho in [-1, 1] required')
    joint = p_a * p_b + rho * math.sqrt(p_a * (1-p_a) * p_b * (1-p_b))
    lower, upper = max(0.0, p_a + p_b - 1), min(p_a, p_b)
    if joint < lower - 1e-12 or joint > upper + 1e-12:
        raise ValueError('infeasible correlation for these marginals')
    return max(lower, min(upper, joint))


def fair_decimal(p_win, p_loss):
    """Fair decimal payout with push probability 1 - p_win - p_loss.

    Assumes a push refunds stake; there are no fees or partial settlements.
    """
    if not all(math.isfinite(v) for v in (p_win, p_loss)):
        raise ValueError('inputs must be finite')
    if p_win <= 0 or p_loss < 0 or p_win + p_loss > 1:
        raise ValueError('invalid outcome probabilities')
    return 1 + p_loss / p_win


def expected_net(p_win, p_loss, decimal_odds):
    """Expected net per unit staked, assuming push refund and no costs."""
    fair_decimal(p_win, p_loss)
    if not math.isfinite(decimal_odds) or decimal_odds < 1:
        raise ValueError('invalid decimal odds')
    return p_win * (decimal_odds - 1) - p_loss

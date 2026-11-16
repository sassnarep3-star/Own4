"""S6 — the strategy register: definition, two-sided 'what would change our mind', and the reward policy.

Every strategy carries BOTH directions. A one-sided 'what would change our mind' is a marketing device:
it only ever lists the evidence that would confirm the author.
"""
import os

from common import DATA, REGISTERED_UTC, read_json, write_json

S = "https://www.nfl.com"


def main():
    bt = read_json(os.path.join(DATA, "backtest.json"))
    by = bt["strategies"]
    paired = bt["paired_vs_control"]

    def row(**kw):
        return kw

    strategies = [
        row(id="S1", name="Model favourite (singles, shadow)",
            family="singles", registered="PREREGISTRATION.md §7", status="paper (shadow)",
            definition=("Bet the club the rating model makes the favourite. Decision uses the model's own "
                        "probability only; no price input."),
            n=by["S1_model_favourite"]["n"],
            accuracy=round(by["S1_model_favourite"]["accuracy"], 4),
            accuracy_ci=[round(x, 4) for x in by["S1_model_favourite"]["accuracy_ci95_week_cluster"]],
            brier=round(by["S1_model_favourite"]["brier"], 4),
            placebo_p=by["S1_model_favourite"]["placebo_label_shuffle_p"],
            promote_if=[
                "n reaches 300 graded games (G1) and the week-cluster lower bound on Brier skill stays above 0",
                "the paired difference against the record-only control excludes 0 on a larger sample",
            ],
            demote_if=[
                "the Brier-skill lower bound is at or below 0 for 4 consecutive weeks (G7)",
                "the paired difference against S3 falls below 0 on a larger sample",
            ],
            what_would_change_our_mind=(
                "Right now: a lower bound of -0.0148 on Brier skill means the model has NOT been shown to "
                "beat a coin flip with confidence, while a model-free rule scores within 2.6 points of it. "
                "If 184 more graded games keep the lower bound below 0, this strategy is dead and should be "
                "withdrawn rather than tuned."),
            source_url=S + "/schedules/2026/by-week/week-10"),
        row(id="S2", name="Model favourite, high confidence (singles, shadow)",
            family="singles", registered="PREREGISTRATION.md §7 (threshold 0.65 frozen)", status="paper (shadow)",
            definition="S1 restricted to fixtures where the model's own probability is at least 0.65.",
            n=by["S2_high_confidence"]["n"],
            accuracy=round(by["S2_high_confidence"]["accuracy"], 4),
            accuracy_ci=[round(x, 4) for x in by["S2_high_confidence"]["accuracy_ci95_week_cluster"]],
            brier=round(by["S2_high_confidence"]["brier"], 4),
            placebo_p=by["S2_high_confidence"]["placebo_label_shuffle_p"],
            promote_if=["n reaches 300 and the lower bound stays above 0 after the multiplicity adjustment "
                        "for 2 registered singles strategies"],
            demote_if=["G7 as S1; or the confidence bucket's calibration bin stays inverted (no higher hit "
                       "rate than the 0.50-0.60 bin) as n grows"],
            what_would_change_our_mind=(
                "The 0.60-0.70 bin currently observes 41.7% home wins against 64.4% predicted — one bin, "
                "12 games. If that inversion survives 50 more games, the 0.65 threshold is selecting the "
                "model's worst probabilities, not its best, and S2 must be withdrawn."),
            source_url=S + "/schedules/2026/by-week/week-10"),
        row(id="S3", name="Better-record rule (CONTROL, not a candidate)",
            family="singles (control)", registered="PREREGISTRATION.md §7", status="control",
            definition=("Pick the club with the better wins-minus-losses record computed from games before "
                        "the cutoff. Zero model content."),
            n=by["S3_record_baseline"]["n"],
            accuracy=round(by["S3_record_baseline"]["accuracy"], 4),
            accuracy_ci=[round(x, 4) for x in by["S3_record_baseline"]["accuracy_ci95_week_cluster"]],
            brier=round(by["S3_record_baseline"]["brier"], 4),
            placebo_p=by["S3_record_baseline"]["placebo_label_shuffle_p"],
            promote_if=["never — a control cannot be promoted; it exists to make the model prove itself"],
            demote_if=["n/a"],
            what_would_change_our_mind=(
                "This control is the reason the model's headline accuracy is not treated as evidence: they "
                "differ by 2.6 points with an interval of [-3.7, +8.5]. If this control ever beats the model "
                "on a larger sample, the ratings are not earning their complexity."),
            source_url=S + "/schedules/2026/by-week/week-10"),
        row(id="S4", name="Fade of S1 (registered falsification test)",
            family="singles (control)", registered="PREREGISTRATION.md §6.5", status="control",
            definition="Bet the opposite of S1. If the model were noise, this would score about the same.",
            n=by["S1_model_favourite"]["n"],
            accuracy=round(bt["fade_controls"]["S1_model_favourite_faded"]["accuracy"], 4),
            accuracy_ci=None, brier=None, placebo_p=None,
            promote_if=["never — a fade scoring well is evidence the original score is noise"],
            demote_if=["n/a"],
            what_would_change_our_mind=(
                "32.2% accuracy when inverted, against 67.8% for the original, is the shape you want: the "
                "original is not symmetric noise."),
            source_url=S + "/schedules/2026/by-week/week-10"),
        row(id="C1", name="Coin flip (control baseline)",
            family="singles (control)", registered="PREREGISTRATION.md §7", status="control",
            definition="A fair coin per fixture, 2 000 repeated runs.",
            n=by["S1_model_favourite"]["n"], accuracy=0.5, accuracy_ci=[0.4, 0.6], brier=0.25,
            placebo_p=None,
            promote_if=["never"], demote_if=["n/a"],
            what_would_change_our_mind="Nothing: it is the null the whole page is measured against.",
            source_url=S + "/schedules/2026/by-week/week-10"),
        row(id="P1", name="Parlays, same-game parlays, prop combos",
            family="parlays / SGP / props", registered="blocked by G6", status="not registered — blocked",
            definition="Not defined on purpose: a combination cannot be ranked without a validated joint "
                       "probability and the operator's void/push rules.",
            n=0, accuracy=None, accuracy_ci=None, brier=None, placebo_p=None,
            promote_if=["a validated joint distribution for the exact leg set, and the operator's void/push "
                        "rules published on the row"],
            demote_if=["n/a (nothing live)"],
            what_would_change_our_mind=(
                "CR-03 shows a same-game scoring dependence of r = 0.053 (n = 296, interval includes 0) — "
                "too weak to justify independence and too imprecise to justify dependence. Multiplying "
                "marginal probabilities stays forbidden until a joint number exists."),
            source_url=S + "/schedules/2026/by-week/week-10"),
    ]

    write_json(os.path.join(DATA, "strategies.json"), {
        "dataset": "nfl_sources_strategies",
        "title": "Strategy register with two-sided change tests",
        "built_utc": REGISTERED_UTC,
        "preregistration": "PREREGISTRATION.md (commit a4f26f5)",
        "rule": ("Every row carries promote_if and demote_if. A row with only one side is not publishable here. "
                 "Parlays/SGP/props are listed with n = 0 and no definition because G6 blocks them."),
        "reward_policy": {
            "currency": "none",
            "awarded": 0,
            "why": ("No strategy passes G1 (n >= 300) or G2 (Brier-skill lower bound above 0), so no reward "
                    "can be earned. A reward paid on accuracy or on an assumed-price ROI would reward luck."),
            "would_pay_if": "a strategy clears G1 and G2 and survives G7 for four consecutive weeks",
            "control_exclusion": "S3, S4, C1 are controls and are never eligible for a reward",
        },
        "paired_vs_control": paired,
        "multiplicity": {"registered_singles_strategies": 2,
                         "note": ("S1 and S2 are two looks at one model; a Bonferroni-style adjustment for "
                                  "m=2 is m=2, and the larger m that matters is the number of namespaces in "
                                  "this repository that have fitted a model to the same season.")},
        "strategies": strategies,
    })
    print("strategies:", len(strategies))
    for s in strategies:
        print(" ", s["id"], s["status"], "n=%s" % s["n"], s["promote_if"][0][:60])


if __name__ == "__main__":
    main()

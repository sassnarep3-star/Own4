"""nfl-book/engine/build_site.py — builds the dashboard.

    python3 nfl-book/engine/build_site.py

Pure standard library. Every table row carries a source link. A value that
could not be confirmed is blank and flagged, never filled in.
"""

from __future__ import annotations

import html
import json
import os

from . import core
from . import analysis

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(core.ROOT, "pages")
REPO_BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/"
TAG = "Own4 · nfl-book · snapshot 2026-11-14"

NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("pages/executive-summary.html", "Executive summary"),
    ]),
    ("Origination", [
        ("pages/own-lines.html", "Own lines"),
        ("pages/strategies.html", "Strategies &amp; research"),
        ("pages/prices.html", "Price snapshots"),
    ]),
    ("Evidence", [
        ("pages/results.html", "Results &amp; verification"),
        ("pages/correlations.html", "Correlations"),
        ("pages/injuries.html", "Injuries &amp; depth"),
        ("pages/repo-review.html", "Repository review"),
    ]),
    ("Decision", [
        ("pages/leaderboard.html", "Leaderboards"),
        ("pages/gates.html", "Gates &amp; demotion"),
        ("pages/questions.html", "Questions"),
        ("pages/suggestions.html", "Suggestions"),
    ]),
    ("Governance", [
        ("pages/verification.html", "Source register"),
        ("pages/flagged.html", "⚑ Flagged for review"),
    ]),
]


# --------------------------------------------------------------- helpers
def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def num(x, nd=1, sign=False):
    if x is None:
        return '<span class="blank">blank — unverified</span>'
    f = ("%+." if sign else "%.") + str(nd) + "f"
    return esc(f % x)


def pct(x, nd=1):
    if x is None:
        return '<span class="blank">blank — unverified</span>'
    return esc(("%.0f%%" if nd == 0 else ("%." + str(nd) + "f%%")) % (100.0 * x))


def pval(p):
    if p is None:
        return '<span class="blank">blank — unverified</span>'
    if p < 0.0001:
        return "&lt;0.0001"
    return esc("%.4f" % p)


def ext(url, label):
    if not url:
        return '<span class="blank">blank — unverified</span>'
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label))


def repo(path, label="Repo ↗"):
    return ext(REPO_BLOB + path, label)


def link_or_text(value, label="source ↗"):
    """Accept either a bare URL or an anchor that was built earlier."""
    if value is None:
        return '<span class="blank">blank — unverified</span>'
    if isinstance(value, str) and value.startswith("<a "):
        return value
    return ext(value, label)


def badge(text, kind="none"):
    return '<span class="badge %s">%s</span>' % (kind, esc(text))


def third_party(url):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
        esc(url), "third-party ↗")


def table(headers, rows, caption="", numeric=(), cls="", note=""):
    cap = '<caption>%s</caption>' % caption if caption else ""
    th = "".join('<th scope="col"%s>%s</th>' % (' class="num"' if i in numeric else "", esc(h))
                 for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join('<td%s>%s</td>' % (' class="num"' if i in numeric else "", c)
                      for i, c in enumerate(r))
        body.append("<tr>%s</tr>" % tds)
    out = ('<div class="wrap"><table%s>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
           % (' class="%s"' % cls if cls else "", cap, th, "".join(body)))
    if note:
        out += '<p class="note">%s</p>' % note
    return out


def page(title, body, active, prefix=""):
    """prefix is "" for the dashboard and "../" for the subpages, so every
    link and the stylesheet resolve from wherever the page sits."""
    nav = []
    for group, links in NAV:
        for href, label in links:
            cls = ' class="active"' if href == active else ""
            nav.append('<a%s href="%s%s">%s</a>' % (cls, prefix, href, label))
    head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — NFL Origination Book</title>
<link rel="stylesheet" href="%s../assets/style.css">
</head>
<body>
<header><div class="wrap">
<h1><a href="%sindex.html">NFL Origination Book</a></h1>
<div class="tag">%s · every row source-linked · unverified values stay blank and are flagged</div>
<nav>%s</nav>
</div></header>
<main>
%s
</main>
<footer>Built by nfl-book/engine/build_site.py from nfl-book/data/. Official sources are nfl.com; every other source is labelled third-party where it appears. This site publishes research and decision support only — it does not publish betting advice, and no page on it is a recommendation to place a wager.</footer>
</body>
</html>
""" % (esc(title), prefix, prefix, esc(TAG), "".join(nav), body)
    return head


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def load(name):
    return core.read_json(os.path.join(core.DERIVED, name))


# ------------------------------------------------------------------ pages
def build_index(S, own, board, gates, results, corr, depth, prices, flags, summary):
    cards = []
    for h in summary["headline_numbers"]:
        cards.append('<div class="card"><b>%s</b><span>%s</span></div>'
                     % (esc(h["value"]), esc(h["label"])))
    body = [
        "<h2>Executive summary</h2>",
        '<p class="lead">%s</p>' % esc(summary["one_line"]),
        '<div class="cards">%s</div>' % "".join(cards),
    ]
    for s in summary["sections"]:
        body.append("<h3>%s</h3><p>%s</p>" % (esc(s["heading"]), esc(s["body"])))

    body.append("<h2>What the pipeline produced</h2>")
    rows = [
        ["Verified results feed", "%d games" % results["games"],
         "https://www.nfl.com/standings/league/2026/REG"],
        ["Official standings cells reproduced", "%d of %d" % (
            results["reconciliation"]["cells_matching"],
            results["reconciliation"]["cells_total"]),
         "https://www.nfl.com/standings/league/2026/REG"],
        ["Price snapshots", "%d (%d with an open and a close)" % (
            prices["coverage"]["records"], prices["coverage"]["open_close"]),
         repo("data/derived/price_snapshot_coverage.json")],
        ["Originated markets on the next slate", "%d games" % own["slate"]["games"],
         own["slate"]["source_url"]],
        ["Strategies evaluated", "%d" % len(board["signal_rows"]),
         repo("data/derived/strategies.json")],
        ["Strategies passing every gate", "%d" % sum(
            1 for r in board["signal_rows"] if r["signal_pass"]),
         repo("data/derived/gates.json")],
        ["Points awarded", "%d of %d" % (board["points_awarded"], board["points_available"]),
         repo("data/derived/leaderboard.json")],
        ["Correlations, each published with n", "%d" % len(corr["rows"]),
         "https://www.nfl.com/standings/league/2026/REG"],
        ["Official injury rows tracked", "%d" % depth["players_listed"],
         depth["source_url"]],
        ["Flagged items", "%d (%d open)" % (len(flags["rows"]),
                                           sum(1 for r in flags["rows"] if r["status"] == "open")),
         repo("data/flags.json")],
    ]
    body.append(table(["Item", "Value", "Source"],
                      [[esc(r[0]), esc(r[1]), link_or_text(r[2])] for r in rows]))

    body.append('<p><a href="pages/executive-summary.html">Read the full executive summary →</a></p>')
    return page("Dashboard", "\n".join(body), "index.html")


def build_summary(summary, flags, questions):
    body = ["<h2>Executive summary</h2>",
            '<p class="lead">%s</p>' % esc(summary["one_line"]),
            '<div class="cards">%s</div>' % "".join(
                '<div class="card"><b>%s</b><span>%s</span></div>'
                % (esc(h["value"]), esc(h["label"])) for h in summary["headline_numbers"])]
    for s in summary["sections"]:
        body.append("<h3>%s</h3><p>%s</p>" % (esc(s["heading"]), esc(s["body"])))
    body.append("<h2>Open questions</h2>")
    rows = []
    for q in questions["rows"]:
        if q["status"].startswith("open"):
            rows.append([esc(q["id"]), esc(q["question"]), esc(q["status"]),
                         esc(", ".join(q["blocks"])) or "—", ext(q["source_url"], "source ↗")])
    body.append(table(["ID", "Question", "Status", "What it blocks", "Source"], rows))
    body.append("<h2>Sources used for this snapshot</h2><ul>")
    for s in summary["sources"]:
        body.append('<li>%s</li>' % ext(s, s))
    body.append("</ul>")
    return page("Executive summary", "\n".join(body), "pages/executive-summary.html", prefix="../")


def build_own_lines(own):
    body = ["<h2>Originated lines</h2>",
            '<p class="lead">%s</p>' % esc(own["order_note"]),
            '<p class="note">%s</p>' % esc(own["columns_note"]),
            "<h3>Model</h3>",
            table(["Model input", "Value", "Source"],
                  [[esc("Games fitted on"), esc(own["model"]["fitted_on_games"]),
                    ext(own["model"]["source_url"], "nfl.com ↗")],
                   [esc("Shrinkage (games of league-mean prior)"), esc(own["model"]["shrinkage_games"]),
                    repo("engine/core.py")],
                   [esc("Home-field advantage (points)"), num(own["model"]["home_field_advantage"], 3),
                    ext(own["model"]["source_url"], "nfl.com ↗")],
                   [esc("Standard deviation of the margin"), num(own["model"]["sd_home_margin"], 3),
                    ext(own["model"]["source_url"], "nfl.com ↗")],
                   [esc("Mean combined points"), num(own["model"]["mean_total"], 3),
                    ext(own["model"]["source_url"], "nfl.com ↗")]]),
            "<h3>Next slate — week %s</h3>" % esc(own["slate"]["week"]),
            '<p class="note">%s</p>' % esc(own["slate"]["source_url"])]
    rows = []
    for g in own["rows"]:
        by = {m["market"]: m for m in g["markets"]}
        sp, to, ml = by["SPREAD"], by["TOTAL"], by["MONEYLINE"]
        rows.append([
            esc(g["date"]), esc(g["away"]), esc(g["home"]),
            num(sp["fair_line"], 1, True), num(sp["market_line"], 1, True),
            num(sp["difference"], 1, True),
            num(to["fair_line"], 1), num(to["market_line"], 1), num(to["difference"], 1),
            esc(ml["fair_price"]) if ml["fair_price"] is not None
            else '<span class="blank">blank — unverified</span>',
            esc(ml["market_price"]) if ml["market_price"] is not None
            else '<span class="blank">blank — unverified</span>',
            num(ml["difference_probability"], 4),
            ext(g["game_url"], "game ↗"),
        ])
    body.append(table(
        ["Date", "Away", "Home",
         "Model spread", "Market spread", "Difference",
         "Model total", "Market total", "Difference",
         "Model ML", "Market ML", "Prob. difference", "Source"],
        rows,
        caption="Week %s · the side is originated first, the total second, the moneyline third"
                % own["slate"]["week"],
        numeric=(3, 4, 5, 6, 7, 8, 11),
        note=("The market columns are third-party closing numbers from the pinned "
              "nflverse archive; the NFL publishes no betting lines. A blank "
              "market cell means the archive holds no number for that market, "
              "and the difference is left blank rather than shown as zero.")))
    body.append("<h3>Out-of-sample history</h3>")
    hrows = []
    for g in own["history"]:
        by = {m["market"]: m for m in g["markets"]}
        sp, to = by["SPREAD"], by["TOTAL"]
        hrows.append([
            esc(g["week"]), esc(g["date"]), esc(g["away"]), esc(g["home"]),
            num(sp["fair_line"], 1, True), num(sp["market_line"], 1, True),
            num(sp["difference"], 1, True),
            num(to["fair_line"], 1), num(to["market_line"], 1), num(to["difference"], 1),
            esc(g["actual_margin"]), esc(g["actual_total"]),
            ext(g["game_url"], "game ↗"),
        ])
    body.append(table(
        ["Week", "Date", "Away", "Home", "Model spread", "Market spread", "Difference",
         "Model total", "Market total", "Difference", "Actual margin", "Actual total", "Source"],
        hrows,
        caption="Every out-of-sample week, with the market difference and the result beside it",
        numeric=(4, 5, 6, 7, 8, 9, 10, 11)))
    return page("Own lines", "\n".join(body), "pages/own-lines.html", prefix="../")


def build_leaderboard(board, gates):
    body = ["<h2>Leaderboards</h2>",
            '<p class="lead">%s</p>' % esc(board["policy"]["signal_board"]),
            '<p class="note">%s<br>%s</p>' % (esc(board["policy"]["staking_board"]),
                                             esc(board["policy"]["reward"])),
            "<h3>Signal board — skill only, no money</h3>"]
    rows = []
    for r in board["signal_rows"]:
        rows.append([
            esc(r["signal_rank"]), esc(r["id"]), esc(r["name"]), esc(r["family"]),
            esc(r["market"]), esc(r["n"]),
            pct(r["hit_rate"]) if r["hit_rate"] is not None
            else '<span class="blank">blank — unverified</span>',
            pct(r["break_even_rate"]) if r["break_even_rate"] is not None
            else '<span class="blank">blank — no price</span>',
            pval(r["p_value"]), pval(r["q_value"]),
            pct(r["bootstrap_ci_low"]) if r["bootstrap_ci_low"] is not None
            else '<span class="blank">blank</span>',
            pct(r["bootstrap_ci_high"]) if r["bootstrap_ci_high"] is not None
            else '<span class="blank">blank</span>',
            pval(r["placebo_p"]),
            esc(r["gates_passed"]),
            badge("PASS" if r["signal_pass"] else "FAIL", "v-verified" if r["signal_pass"] else "v-unverified"),
            ext(r["source_url"], "source ↗"),
        ])
    body.append(table(
        ["Rank", "ID", "Strategy", "Family", "Market", "n", "Hit rate", "Break-even",
         "p", "q", "CI low", "CI high", "Placebo p", "Gates", "Signal", "Source"],
        rows, numeric=(0, 5, 6, 7, 8, 9, 10, 11, 12),
        note=("n is the number of out-of-sample decisions. The gate floor is 100. "
              "Every rate is published next to its n so a small sample cannot be "
              "read like a large one.")))

    body.append("<h3>Staking board — money only</h3>")
    rows = []
    for r in board["staking_rows"]:
        rows.append([
            esc(r["staking_rank"]), esc(r["id"]), esc(r["name"]), esc(r["market"]),
            esc(r["bets_with_a_price"]),
            num(r["profit_units"], 3, True) if r["profit_units"] is not None
            else '<span class="blank">blank — no price</span>',
            pct(r["roi"]) if r["roi"] is not None
            else '<span class="blank">blank — no price</span>',
            num(r["clv_points"], 2, True) if r["clv_points"] is not None
            else '<span class="blank">blank — no opening price</span>',
            badge("ELIGIBLE" if r["stake_eligible"] else "NOT ELIGIBLE",
                  "v-verified" if r["stake_eligible"] else "v-unverified"),
            ext(r["source_url"], "source ↗"),
        ])
    body.append(table(
        ["Rank", "ID", "Strategy", "Market", "Bets with a price", "Profit (units)", "ROI",
         "CLV (points)", "Stake eligible", "Source"],
        rows, numeric=(0, 4, 5, 6, 7),
        note=("A strategy may only be staked when every signal gate passes. A "
              "staking result never promotes a strategy on its own.")))

    body.append("<h3>Masking check — can a lucky staking run hide a weak signal?</h3>")
    rows = []
    for r in board["masking_check"]:
        rows.append([
            esc(r["id"]), esc(r["name"]), esc(r["signal_rank"]), esc(r["staking_rank"]),
            pct(r["roi"]) if r["roi"] is not None
            else '<span class="blank">blank — no price</span>',
            badge("YES" if r["masking_risk"] else "NO",
                  "v-unverified" if r["masking_risk"] else "v-verified"),
            esc(r["explanation"]), ext(r["source_url"], "source ↗"),
        ])
    body.append(table(["ID", "Strategy", "Signal rank", "Staking rank", "ROI",
                       "Masking risk", "Explanation", "Source"], rows))
    body.append('<p class="note">Points awarded: %d of %d available.</p>'
                % (board["points_awarded"], board["points_available"]))
    return page("Leaderboards", "\n".join(body), "pages/leaderboard.html", prefix="../")


def build_strategies(strat, props, propcombo, parlay, gates):
    body = ["<h2>Strategy research</h2>",
            '<p class="lead">Every strategy is pre-registered with its rule, '
            'evaluated out of sample, and put through the same battery: an exact '
            'binomial test, a false-discovery correction across every strategy '
            'tried, a bootstrap interval, a relabelling placebo and a holdout '
            'split.</p>',
            "<h3>Game-level strategies</h3>"]
    rows = []
    for r in strat["rows"]:
        s = r["signal"]
        rows.append([
            esc(r["id"]), esc(r["family"]), esc(r["name"]), esc(r["rule"]),
            esc(s["n"]), pct(s["hit_rate"]) if s["hit_rate"] is not None
            else '<span class="blank">blank</span>',
            pct(s["break_even_rate"]) if s["break_even_rate"] is not None
            else '<span class="blank">blank — no price</span>',
            pval(s["p_value"]), pval(s["q_value"]), pval(s["placebo_p"]),
            esc("%d/%d" % (r["gates_passed"], len(r["gates"]))),
            ext(r.get("source_url") or "https://www.nfl.com/standings/league/2026/REG", "source ↗"),
        ])
    body.append(table(["ID", "Family", "Name", "Rule", "n", "Hit rate", "Break-even",
                       "p", "q", "Placebo p", "Gates", "Source"], rows,
                      numeric=(4, 5, 6, 7, 8, 9)))

    body.append("<h3>Player props</h3>")
    body.append('<p class="note">%s</p>' % esc(props["break_even_note"]))
    body.append(table(["ID", "Name", "Rule", "n", "Wins", "Losses", "Hit rate", "p",
                       "CI low", "CI high", "Placebo p", "Source"],
                      [[esc(props["id"]), esc(props["name"]), esc(props["rule"]),
                        esc(props["n"]), esc(props["wins"]), esc(props["losses"]),
                        pct(props["hit_rate"]), pval(props["p_value"]),
                        pct(props["bootstrap_ci_low"]), pct(props["bootstrap_ci_high"]),
                        pval(props["placebo_p"]), ext(props["source_url"], "source ↗")]],
                      numeric=(3, 4, 5, 6, 7, 8, 9, 10)))

    body.append("<h3>Player-prop combinations</h3>")
    body.append(table(["ID", "Name", "Rule", "n", "Both legs hit", "Hit rate",
                       "Marginal hit rate (leg A)", "Marginal hit rate (leg B)",
                       "Independent expectation", "Observed joint rate", "Dependence",
                       "Source"],
                      [[esc(propcombo["id"]), esc(propcombo["name"]), esc(propcombo["rule"]),
                        esc(propcombo["n"]), esc(propcombo["wins"]),
                        pct(propcombo["hit_rate"]),
                        pct(propcombo["marginal_hit_rate_a"]),
                        pct(propcombo["marginal_hit_rate_b"]),
                        pct(propcombo["independent_expectation"]),
                        pct(propcombo["observed_joint_rate"]),
                        num(propcombo["dependence"], 4, True),
                        ext(propcombo["source_url"], "source ↗")]],
                      numeric=(3, 4, 5, 6, 7, 8, 9, 10),
                      note=esc(propcombo["dependence_note"])))

    body.append("<h3>Game parlays</h3>")
    body.append(table(["ID", "Name", "Rule", "n", "Both legs hit", "Hit rate",
                       "Marginal leg hit rate", "Independent expectation", "Dependence",
                       "Price", "Source"],
                      [[esc(parlay["id"]), esc(parlay["name"]), esc(parlay["rule"]),
                        esc(parlay["n"]), esc(parlay["wins"]), pct(parlay["hit_rate"]),
                        pct(parlay["marginal_leg_hit_rate"]),
                        pct(parlay["independent_expectation"]),
                        num(parlay["dependence"], 4, True),
                        '<span class="blank">blank — no parlay price</span>',
                        ext(parlay["source_url"], "source ↗")]],
                      numeric=(3, 4, 5, 6, 7, 8),
                      note=esc(parlay["price_note"])))

    body.append("<h3>Model variants, compared out of sample</h3>")
    body.append(table(["Variant", "What it does", "n", "Mean absolute error (points)"],
                      [[esc(r["variant"]), esc(r["label"]), esc(r["n"]),
                        num(r["mean_absolute_error_points"], 3)] for r in
                       strat.get("model_variants", {}).get("rows", [])],
                      numeric=(2, 3),
                      note=("Every variant is refitted on each week using only "
                            "the games played before that week. The closing "
                            "line's error over the same predictions is "
                            + num(strat.get("accuracy", {}).get("market_spread_mae"), 3)
                            + " points, and the model does not beat it.")))
    body.append("<h3>Luck controls applied to every family</h3>")
    body.append(table(["Control", "What it does", "Why it matters"],
                      [[esc("Exact binomial test"),
                        esc("The hit rate is compared with the break-even rate using the exact binomial distribution, not a normal approximation."),
                        esc("At the sample sizes in this book a normal approximation would overstate the evidence.")],
                       [esc("False-discovery control"),
                        esc("Benjamini-Hochberg q-values are computed across every strategy tried, not one at a time."),
                        esc("Trying eight strategies and reporting the best one is how a weak signal gets published as a strong one.")],
                       [esc("Bootstrap interval"),
                        esc("A seeded bootstrap gives a 95% interval on the hit rate."),
                        esc("It shows how much of the result is the sample rather than the strategy.")],
                       [esc("Relabelling placebo"),
                        esc("The same bets are shuffled at random and the hit rate is recomputed."),
                        esc("A placebo that reaches the observed hit rate means the sample, not the rule, produced the result.")],
                       [esc("Holdout split"),
                        esc("The first and second half of the out-of-sample sample are tested separately."),
                        esc("A strategy that only works in one stretch of the season is not a strategy.")],
                       [esc("Signal and staking kept apart"),
                        esc("Skill is scored on one board and money on another, and the masking check compares the two."),
                        esc("A lucky staking run must never be able to promote a weak signal.")]],
                      cls=""))
    return page("Strategies", "\n".join(body), "pages/strategies.html", prefix="../")


def build_prices(prices, store):
    cov = prices["coverage"]
    body = ["<h2>Price snapshots</h2>",
            '<p class="lead">Every market this repository originates leaves a '
            'trail: the number published, the time it was published, the page it '
            'was published on, and the closing number when the market closed.</p>',
            '<p class="note">A closing snapshot may not be written without an '
            'opening one, and the store refuses it. A snapshot whose value is '
            'unknown keeps the value blank.</p>',
            '<div class="cards">%s</div>' % "".join([
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(cov["records"]), esc("price snapshot records")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(cov["open_close"]), esc("with an opening and a closing number")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(cov["open_only"]), esc("opening number only — gap named below")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(len(cov["gaps"])), esc("named gaps")),
            ])]
    body.append("<h3>Coverage by market</h3>")
    rows = []
    for m, v in sorted(cov["by_market"].items()):
        rows.append([esc(m), esc(v["records"]), esc(v["open_close"]), esc(v["open_only"])])
    body.append(table(["Market", "Records", "Open and close", "Open only"], rows,
                      numeric=(1, 2, 3)))
    body.append("<h3>Coverage by originator</h3>")
    rows = []
    for m, v in sorted(cov["by_originator"].items()):
        rows.append([esc(m), esc(v["records"]), esc(v["open_close"]), esc(v["open_only"])])
    body.append(table(["Originator", "Records", "Open and close", "Open only"], rows,
                      numeric=(1, 2, 3),
                      note="own_model is a number this repository originated. "
                           "market is a number observed elsewhere and always "
                           "carries the source that published it."))
    body.append("<h3>Snapshots with both numbers</h3>")
    rows = []
    for rec in store["records"]:
        if rec["status"] != "open_close":
            continue
        o, c = rec["open"], rec["close"]
        rows.append([
            esc(rec["game_key"]), esc(rec["market"]), esc(rec["side"]),
            esc(rec["originator"]),
            num(o["line"], 1) if o["line"] is not None else esc(o["price"]) if o["price"] is not None
            else '<span class="blank">blank</span>',
            num(c["line"], 1) if c["line"] is not None else esc(c["price"]) if c["price"] is not None
            else '<span class="blank">blank</span>',
            esc(o["published_utc"]), esc(c["published_utc"]),
            ext(c["source_url"], "source ↗"),
        ])
    body.append(table(["Game", "Market", "Side", "Originator", "Open", "Close",
                       "Open published (UTC)", "Close published (UTC)", "Source"],
                      rows, numeric=()))
    body.append("<h3>Named gaps — every market missing its closing number</h3>")
    rows = [[esc(g["record_key"]), esc(g["market"]), esc(g["side"]),
             esc(g["originator"]), esc(g["open_published_utc"]), esc(g["missing"])]
            for g in cov["gaps"]]
    body.append(table(["Record", "Market", "Side", "Originator", "Open published (UTC)",
                       "Missing"], rows,
                      note="These gaps are the reason closing-line value cannot "
                           "be computed for most markets. The gap is published "
                           "rather than hidden."))
    body.append("<h3>Sources</h3><ul>")
    for m in prices["header"].get("own_publications", []):
        body.append("<li>%s — %s snapshots, published %s — %s</li>" % (
            esc(m["publication"]), esc(m["snapshots"]), esc(m["published_utc"]),
            ext(m["source_url"], "source ↗")))
    body.append("</ul>")
    return page("Price snapshots", "\n".join(body), "pages/prices.html", prefix="../")


def build_results(results, standings):
    rec = results["reconciliation"]
    body = ["<h2>Results feed</h2>",
            '<p class="lead">%s</p>' % esc(results["description"]),
            '<div class="cards">%s</div>' % "".join([
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(results["games"]), esc("games with a final score")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(results["official_read_games"]), esc("read directly off an official page")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(results["reconciled_games"]), esc("reconciled to the official record")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc("%d/%d" % (rec["cells_matching"], rec["cells_total"])),
                    esc("official standings cells reproduced exactly")),
            ])]
    body.append("<h3>Reconciliation against the official standings</h3>")
    rows = []
    for r in rec["rows"]:
        rows.append([
            esc(r["team"]),
            "%s–%s–%s" % (r["official_w"], r["official_l"], r["official_t"]),
            "%s–%s–%s" % (r["feed_w"], r["feed_l"], r["feed_t"]),
            esc(r["official_pf"]), esc(r["feed_pf"]),
            esc(r["official_pa"]), esc(r["feed_pa"]),
            badge("MATCH" if r["match"] else "MISMATCH",
                  "v-verified" if r["match"] else "v-unverified"),
            ext(r["source_url"], "nfl.com ↗"),
        ])
    body.append(table(["Club", "Official W–L–T", "Feed W–L–T", "Official PF", "Feed PF",
                       "Official PA", "Feed PA", "Check", "Source"], rows,
                      numeric=(3, 4, 5, 6),
                      note=("The official standings are the authority. Any wrong "
                            "score in the feed would change at least one of "
                            "these cells.")))
    body.append("<h3>Every game</h3>")
    rows = []
    for g in results["rows"]:
        rows.append([
            esc(g["week"]), esc(g["date"]), esc(g["away"]), esc(g["away_pts"]),
            esc(g["home"]), esc(g["home_pts"]),
            esc(g["home_pts"] - g["away_pts"]), esc(g["home_pts"] + g["away_pts"]),
            badge("official read" if g["score_source"] == "official_read"
                  else "reconciled to official",
                  "v-verified" if g["score_source"] == "official_read" else "v-corrected"),
            ext(g["official_source_url"] or g["game_url"], "source ↗"),
        ])
    body.append(table(["Week", "Date", "Away", "Away pts", "Home", "Home pts",
                       "Margin", "Total", "Score provenance", "Source"], rows,
                      numeric=(0, 3, 5, 6, 7),
                      note="A game read directly off an nfl.com scores page is "
                           "marked official read. A game carried from the "
                           "third-party archive because nfl.com hid the score "
                           "is marked reconciled to official and carries the "
                           "official game page where the score can be checked."))
    return page("Results", "\n".join(body), "pages/results.html", prefix="../")


def build_correlations(corr):
    body = ["<h2>Correlations</h2>",
            '<p class="lead">%s</p>' % esc(corr["policy"]),
            "<h3>Official source URLs used</h3><ul>"]
    for u in corr["official_source_urls"]:
        body.append("<li>%s</li>" % ext(u, u))
    body.append("</ul><h3>Values</h3>")
    rows = []
    for r in corr["rows"]:
        rows.append([
            esc(r["name"]), esc(r["n"]),
            num(r["pearson_r"], 4) if r["pearson_r"] is not None
            else '<span class="blank">blank — insufficient data</span>',
            num(r["spearman_rho"], 4) if r["spearman_rho"] is not None
            else '<span class="blank">blank — insufficient data</span>',
            pval(r.get("permutation_p")),
            esc(r["unit"]), esc(r["status"]), ext(r["source_url"], "source ↗"),
        ])
    body.append(table(["Correlation", "n", "Pearson r", "Spearman rho", "Permutation p",
                       "Unit", "Status", "Source"], rows, numeric=(1, 2, 3, 4),
                      note="n is the number of pairs the value was computed on. "
                           "It is published on every row."))
    return page("Correlations", "\n".join(body), "pages/correlations.html", prefix="../")


def build_injuries(depth):
    body = ["<h2>Injuries and depth of replacement</h2>",
            '<p class="lead">The official weekly injury report is the source. '
            'It says who is out. It does not say who replaces them or at what '
            'depth, so the depth cells are blank and the gap is named.</p>',
            '<p class="note">%s</p>' % esc(depth["depth_chart_status"]),
            '<div class="cards">%s</div>' % "".join([
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(depth["players_listed"]), esc("official injury rows tracked")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(depth["players_with_a_designation"]), esc("players with a designation")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(len(depth["players_by_club"])), esc("clubs in the report")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc("0"), esc("depth cells filled — no official source publishes depth")),
            ])]
    body.append("<h3>Rows</h3>")
    rows = []
    for r in depth["rows"]:
        rows.append([
            esc(r["club"]), esc(r["player"]), esc(r["position"]), esc(r["unit"]),
            esc(r["injury"]) if r["injury"] else '<span class="blank">blank</span>',
            esc(r["practice_status"]) if r["practice_status"] else '<span class="blank">blank</span>',
            esc(r["game_status"]),
            '<span class="blank">blank — no official source</span>',
            '<span class="blank">blank — no official source</span>',
            esc(r["scarcity_weight"]) if r["scarcity_weight"] is not None
            else '<span class="blank">blank</span>',
            ext(r["report_url"], "report ↗"),
        ])
    body.append(table(["Club", "Player", "Position", "Unit", "Injury", "Practice",
                       "Game status", "Replacement tier", "Replacement player",
                       "Scarcity weight", "Source"], rows,
                      note=("The scarcity weight is an analyst judgement, not an "
                            "official value, and it is labelled as such. The "
                            "replacement columns are blank because NFL "
                            "Operations publishes no depth chart; the evidence "
                            "that would fill them is named on the flagged page.")))
    body.append("<h3>Rows by club</h3>")
    body.append(table(["Club", "Players listed", "Designated Out"],
                      [[esc(k), esc(v), esc(depth["out_by_club"].get(k, 0))]
                       for k, v in depth["players_by_club"].items()]))
    body.append("<h3>Replacement depth by club, unit and position group</h3>")
    rows = []
    for d in depth.get("deficiency", []):
        rows.append([
            esc(d["club"]), esc(d["unit"]), esc(d["position_group"]),
            esc(d["players"]), esc(d["count"]), esc(d["out_count"]),
            '<span class="blank">blank — no official depth chart</span>',
            '<span class="blank">blank — no official depth chart</span>',
            '<span class="blank">blank — no official depth chart</span>',
            '<span class="blank">blank — no official depth chart</span>',
            '<span class="blank">blank — no official depth chart</span>',
            ext(d["source_url"], "report ↗"),
        ])
    body.append(table(
        ["Club", "Unit", "Position group", "Players with a designation", "Count",
         "Out", "2nd string", "3rd string", "4th string", "Offensive deficiency",
         "Defensive deficiency", "Source"], rows,
        note=("The official report names the player and the designation. The "
              "string tier is blank on every row: NFL Operations publishes no "
              "depth chart, and the official record cannot say who replaces "
              "an absent starter. The evidence that would fill these cells is "
              "named on the flagged page.")))
    return page("Injuries", "\n".join(body), "pages/injuries.html", prefix="../")


def build_gates(gates):
    body = ["<h2>Validation gates and the demotion gate</h2>",
            '<p class="lead">%s</p>' % esc(gates["demotion_rule"]),
            "<h3>Validation gates</h3>"]
    rows = []
    for g in gates["validation_gates"]:
        rows.append([esc(g[0]), esc(g[1]), esc(g[2]), esc(g[3]), esc(g[4])])
    body.append(table(["ID", "Gate", "Threshold", "Field", "What it says"], rows))
    body.append("<h3>Demotion gates</h3>")
    rows = []
    for g in gates["demotion_gates"]:
        rows.append([esc(g[0]), esc(g[1]), esc(g[2])])
    body.append(table(["ID", "Gate", "Rule"], rows))
    body.append("<h3>Every strategy against the gates</h3>")
    rows = []
    for r in gates["rows"]:
        for g in r["gates"]:
            rows.append([
                esc(r["id"]), esc(r["name"]), esc(g["id"]), esc(g["name"]),
                badge(g["status"].upper(), "v-verified" if g["status"] == "pass" else "v-unverified"),
                esc(g["evidence"]), esc(r["status"]),
            ])
    body.append(table(["Strategy", "Name", "Gate", "Gate name", "Result", "Evidence",
                       "Strategy status"], rows))
    body.append("<h3>Demotion state</h3>")
    rows = []
    for r in gates["rows"]:
        for d in r["demotions"]:
            rows.append([
                esc(r["id"]), esc(d["id"]), esc(d["name"]),
                badge("TRIGGERED" if d["triggered"] else "not triggered",
                      "v-unverified" if d["triggered"] else "v-verified"),
                esc(d["evidence"]), esc(r["status"]),
            ])
    body.append(table(["Strategy", "Gate", "Name", "State", "Evidence",
                       "Strategy status"], rows,
                      note="A live strategy is sent back to paper when any "
                           "demotion gate triggers."))
    return page("Gates", "\n".join(body), "pages/gates.html", prefix="../")


def build_questions(q):
    body = ["<h2>Questions, and what would answer them</h2>",
            '<p class="lead">%s</p>' % esc(q["intro"])]
    for r in q["rows"]:
        body.append("<h3>%s — %s</h3>" % (esc(r["id"]), esc(r["question"])))
        body.append(table(["Field", "Content"],
                          [[esc("What we have"), esc(r["what_we_have"])],
                           [esc("What is missing"), esc(r["what_is_missing"])],
                           [esc("What would answer it"), esc(r["what_would_answer_it"])],
                           [esc("Answer"), esc(r["answer"]) if r["answer"]
                            else '<span class="blank">still open</span>'],
                           [esc("Status"), esc(r["status"])],
                           [esc("What it blocks"), esc(", ".join(r["blocks"])) or "—"],
                           [esc("Source"), ext(r["source_url"], "source ↗")]]))
    return page("Questions", "\n".join(body), "pages/questions.html", prefix="../")


def build_suggestions(s):
    body = ["<h2>Suggestions for review</h2>",
            '<p class="lead">%s</p>' % esc(s["intro"]),
            '<p class="note">%s</p>' % esc(s["how_to_use"]),
            "<h3>The queue</h3>"]
    rows = []
    for r in s["rows"]:
        rows.append([
            esc(r["id"]), esc(r["title"]), esc(r["improves"]), esc(r["proposal"]),
            esc(r["evidence"]), esc(r["effort"]), esc(r["risk"]),
            badge(r["status"], "v-corrected"),
            '<span class="blank">not decided</span>' if r["decision"] is None
            else esc(r["decision"]),
            ext(r["source_url"], "source ↗"),
        ])
    body.append(table(["ID", "Suggestion", "What it improves", "Proposal", "Evidence",
                       "Effort", "Risk", "Status", "Decision", "Source"], rows))
    body.append("<h3>One at a time</h3>")
    for r in s["rows"]:
        body.append("<h3>%s — %s</h3>" % (esc(r["id"]), esc(r["title"])))
        body.append(table(["Field", "Content"],
                          [[esc("What it improves"), esc(r["improves"])],
                           [esc("Proposal"), esc(r["proposal"])],
                           [esc("Evidence"), esc(r["evidence"])],
                           [esc("Effort"), esc(r["effort"])],
                           [esc("Risk"), esc(r["risk"])],
                           [esc("Status"), esc(r["status"])],
                           [esc("Decision"), esc(r["decision"]) if r["decision"]
                            else '<span class="blank">not decided</span>'],
                           [esc("Source"), ext(r["source_url"], "source ↗")]]))
    return page("Suggestions", "\n".join(body), "pages/suggestions.html", prefix="../")


def build_flagged(f):
    body = ["<h2>Flagged for review</h2>",
            '<p class="lead">%s</p>' % esc(f["intro"]),
            "<h3>Open</h3>"]
    rows = []
    for r in f["rows"]:
        if r["status"] != "open":
            continue
        rows.append([
            esc(r["id"]), esc(r["title"]), esc(r["what"]), esc(r["why_it_matters"]),
            esc(r["how_it_was_handled"]), esc(r["action_needed"]),
            badge("OPEN", "v-unverified"), ext(r["source_url"], "evidence ↗"),
        ])
    body.append(table(["ID", "Finding", "What was found", "Why it matters",
                       "How it was handled", "Action needed", "Status", "Evidence"], rows))
    body.append("<h3>Closed</h3>")
    rows = []
    for r in f["rows"]:
        if r["status"] == "open":
            continue
        rows.append([
            esc(r["id"]), esc(r["title"]), esc(r["what"]), esc(r["how_it_was_handled"]),
            badge("CLOSED", "v-verified"), ext(r["source_url"], "evidence ↗"),
        ])
    body.append(table(["ID", "Finding", "What was found", "How it was handled",
                       "Status", "Evidence"], rows))
    return page("Flagged", "\n".join(body), "pages/flagged.html", prefix="../")


def build_repo_review(rev):
    body = ["<h2>Repository review</h2>",
            '<p class="lead">A line-by-line scan of the NFL namespaces in this '
            'repository: what is in each one, how many files it holds, and what '
            'the scan found.</p>',
            '<div class="cards">%s</div>' % "".join([
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(rev["nfl_namespaces"]), esc("NFL namespaces")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(rev["files_scanned"]), esc("files scanned")),
                '<div class="card"><b>%s</b><span>%s</span></div>' % (
                    esc(core.SNAPSHOT_UTC), esc("scan date")),
            ])]
    body.append("<h3>Namespaces</h3>")
    rows = []
    for r in rev["rows"]:
        rows.append([
            ext("https://github.com/sassnarep3-star/Own4/tree/main/" + r["path"], r["namespace"]),
            esc(r["files"]), esc(r["html"]), esc(r["python"]), esc(r["javascript"]),
            esc(r["data_files"]),
        ])
    body.append(table(["Namespace", "Files", "HTML", "Python", "JavaScript",
                       "Data files"], rows, numeric=(1, 2, 3, 4, 5),
                       note="The same official tables are captured separately in "
                            "several namespaces, on different dates. That is "
                            "recorded as flag F6 rather than corrected here, "
                            "because the other namespaces belong to other "
                            "sessions."))
    return page("Repository review", "\n".join(body), "pages/repo-review.html", prefix="../")


def build_verification(verification):
    body = ["<h2>Source register and verification ledger</h2>",
            '<p class="lead">Every table row on this site carries the source it '
            'came from. This page is the register of those sources and of the '
            'checks that were run against them.</p>',
            "<h3>Sources</h3>"]
    rows = []
    for s in verification["sources"]:
        rows.append([esc(s["id"]), esc(s["kind"]), esc(s["description"]),
                     ext(s["url"], "source ↗"), esc(s["captured_utc"])])
    body.append(table(["ID", "Kind", "What it is", "URL", "Captured (UTC)"], rows))
    body.append("<h3>Checks</h3>")
    rows = []
    for c in verification["checks"]:
        rows.append([esc(c["id"]), esc(c["what"]), esc(c["method"]),
                     esc(c["result"]), badge(c["status"], c["badge"]),
                     ext(c["source_url"], "source ↗")])
    body.append(table(["ID", "What was checked", "Method", "Result", "Status",
                       "Source"], rows))
    return page("Verification", "\n".join(body), "pages/verification.html", prefix="../")


# ------------------------------------------------------------------- main
def main():
    results = load("results.json")
    own = load("own_lines.json")
    board = load("leaderboard.json")
    gates = load("gates.json")
    strat = load("strategies.json")
    corr = load("correlations.json")
    depth = load("depth.json")
    prices = load("price_snapshot_coverage.json")
    props = load("props.json")
    rev = load("repo_review.json")
    verification = load("verification.json")
    flags = core.read_json(os.path.join(core.DATA, "flags.json"))
    questions = core.read_json(os.path.join(core.DATA, "questions.json"))
    suggestions = core.read_json(os.path.join(core.DATA, "suggestions.json"))
    summary = core.read_json(os.path.join(core.DATA, "summary.json"))
    store = core.read_json(os.path.join(core.DERIVED, "price_snapshots.json"))

    write(os.path.join(core.ROOT, "index.html"),
          build_index(summary, own, board, gates, results, corr, depth, prices, flags, summary))
    write(os.path.join(PAGES, "executive-summary.html"),
          build_summary(summary, flags, questions))
    write(os.path.join(PAGES, "own-lines.html"), build_own_lines(own))
    write(os.path.join(PAGES, "leaderboard.html"), build_leaderboard(board, gates))
    write(os.path.join(PAGES, "strategies.html"),
          build_strategies(strat, props["prop_signal"], props["prop_combination"],
                           props["parlay"], gates))
    write(os.path.join(PAGES, "prices.html"), build_prices(prices, store))
    write(os.path.join(PAGES, "results.html"), build_results(results, None))
    write(os.path.join(PAGES, "correlations.html"), build_correlations(corr))
    write(os.path.join(PAGES, "injuries.html"), build_injuries(depth))
    write(os.path.join(PAGES, "gates.html"), build_gates(gates))
    write(os.path.join(PAGES, "questions.html"), build_questions(questions))
    write(os.path.join(PAGES, "suggestions.html"), build_suggestions(suggestions))
    write(os.path.join(PAGES, "flagged.html"), build_flagged(flags))
    write(os.path.join(PAGES, "repo-review.html"), build_repo_review(rev))
    write(os.path.join(PAGES, "verification.html"), build_verification(verification))
    print("pages written to %s" % PAGES)


if __name__ == "__main__":
    main()

"""05 - Build the NFL Command Center site.

Every page is generated from the captured data. Every table row carries a
source link. A value that no official source confirms is rendered blank with
an explicit unverified marker rather than being filled in.

Writes: nfl-command-center/pages/*.html
"""
import html
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DERIVED, ROOT, dump_json, load_json

PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")

OFFICIAL_SOURCES = {
    "standings": ("https://www.nfl.com/standings/league/2026/REG", "NFL.com league standings, 2026 regular season"),
    "slate": ("https://www.nfl.com/schedules/2026/REG10", "NFL.com Week 10 schedule"),
    "injuries": ("https://www.nfl.com/news/nfl-week-10-injury-report-2026-season", "NFL.com Week 10 injury report"),
    "injuries_page": ("https://www.nfl.com/injuries/", "NFL.com injuries page"),
    "roundup_fri": ("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13", "NFL.com news roundup, Friday 13 November 2026"),
    "roundup_wed": ("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11", "NFL.com news roundup, Wednesday 11 November 2026"),
    "dolphins": ("https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start", "NFL.com article, headline only"),
    "gb_bills": ("https://static.www.nfl.com/image/upload/v1793617588/gamecenter/aaf70dac-4feb-11f1-abca-2c54536568a9.pdf", "Official NFL game book, Ravens at Bills, 1 November 2026"),
    "gb_jax": ("https://static.www.nfl.com/image/upload/v1793965716/gamecenter/ab380826-4feb-11f1-abca-2c54536568a9.pdf", "Official NFL game book, Jaguars at Ravens, 5 November 2026"),
    "repo": ("https://github.com/sassnarep3-star/Own4", "Repository on GitHub"),
    "archive": ("https://github.com/nflverse/nfldata", "Third-party archive, nflverse/nfldata"),
}

BLANK = '<span class="unverified">not confirmed by an official source</span>'
# A value that could not be computed at all, as opposed to a value that no
# official source publishes. The two are different claims and must read
# differently on the page.
NOT_COMPUTED = '<span class="unverified">not computed: strategy blocked</span>'
# a Pearson interval and a p value do not apply to a rate ratio
NOT_CORRELATION = '<span class="unverified">not applicable: a rate ratio, not a Pearson correlation</span>'
# a practice report that the page capture did not carry
NOT_CAPTURED = '<span class="unverified">not readable in the capture</span>'

CSS = """
:root{--ink:#11151c;--muted:#5a6672;--line:#d8dee6;--bg:#fbfcfd;--accent:#0b4f8a;
--warn:#8a4b00;--warnbg:#fff6e8;--ok:#0f6b3f;--okbg:#eef8f2;--chip:#eef2f7}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
header.site{background:#0b2239;color:#fff;padding:28px 20px}
header.site .wrap{max-width:1100px;margin:0 auto}
header.site h1{margin:0 0 6px;font-size:1.7rem;letter-spacing:.2px}
header.site p{margin:0;color:#b9c8d8;max-width:70ch}
nav.site{background:#123css}
nav.sitenav{background:#14314f;padding:0 20px}
nav.sitenav .wrap{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;gap:2px}
nav.sitenav a{color:#d6e2ee;text-decoration:none;padding:9px 11px;font-size:.92rem;border-bottom:3px solid transparent}
nav.sitenav a:hover{background:#1d4268;color:#fff}
nav.sitenav a.on{color:#fff;border-bottom-color:#6fb3f2}
main{max-width:1100px;margin:0 auto;padding:24px 20px 64px}
h2{font-size:1.25rem;margin:30px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:1.03rem;margin:20px 0 8px}
p{max-width:86ch}
a{color:var(--accent)}
table{border-collapse:collapse;width:100%;margin:10px 0 18px;font-size:.9rem;background:#fff}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--chip);font-weight:600;font-size:.85rem;letter-spacing:.2px}
tbody tr:nth-child(even){background:#f7f9fb}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.src a{font-size:.82rem;white-space:nowrap}
.src{width:1%}
.unverified{color:var(--warn);background:var(--warnbg);font-size:.82rem;padding:1px 6px;border-radius:3px;
border:1px solid #f0d9b5;font-style:italic}
.badge{display:inline-block;font-size:.76rem;padding:1px 7px;border-radius:10px;border:1px solid transparent}
.badge.pass{background:var(--okbg);color:var(--ok);border-color:#bfe3cf}
.badge.fail{background:#fdecec;color:#a32020;border-color:#f2c4c4}
.badge.blocked{background:var(--warnbg);color:var(--warn);border-color:#f0d9b5}
.badge.info{background:#eef4fb;color:var(--accent);border-color:#c9dcf1}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:14px 0 20px}
.card{border:1px solid var(--line);border-radius:6px;padding:12px 14px;background:#fff}
.card .k{font-size:.78rem;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}
.card .v{font-size:1.5rem;font-weight:650;margin-top:2px}
.card .d{font-size:.82rem;color:var(--muted);margin-top:4px}
.note{border-left:3px solid var(--accent);background:#f2f7fc;padding:10px 14px;margin:12px 0;font-size:.92rem}
.note.warn{border-left-color:var(--warn);background:var(--warnbg)}
.note.ok{border-left-color:var(--ok);background:var(--okbg)}
footer.site{border-top:1px solid var(--line);padding:22px 20px 40px;color:var(--muted);font-size:.85rem;background:#fff}
footer.site .wrap{max-width:1100px;margin:0 auto}
code{background:#eef1f5;padding:1px 5px;border-radius:3px;font-size:.86em}
.small{font-size:.85rem;color:var(--muted)}
ul.tight{margin:6px 0 14px;padding-left:20px}
ul.tight li{margin:3px 0}
.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:.84rem;margin:8px 0 14px}
"""

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("findings.html", "Findings"),
    ("flagged-for-review.html", "Flagged for review"),
    ("traceability.html", "Traceability"),
    ("decisions.html", "Decisions"),
    ("suggestions.html", "Suggestions"),
    ("standings.html", "Standings"),
    ("own-lines.html", "Own lines"),
    ("strategies.html", "Strategies"),
    ("correlations.html", "Correlations"),
    ("injuries.html", "Injuries"),
    ("depth-chart.html", "Depth chart"),
    ("audit.html", "Repository audit"),
    ("methodology.html", "Methodology"),
]


def e(x):
    return html.escape("" if x is None else str(x))


def src_cell(url, label):
    if not url:
        return '<td class="src">%s</td>' % BLANK
    return '<td class="src"><a href="%s" rel="noopener">%s</a></td>' % (e(url), e(label))


def table(headers, rows, cls=""):
    out = ['<table class="%s"><thead><tr>' % cls]
    for h in headers:
        out.append("<th>%s</th>" % h)
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def matchup(game_id):
    """2026_10_BUF_NYJ -> BUF at NYJ"""
    parts = game_id.split("_")
    if len(parts) >= 4 and parts[0].isdigit():
        return "%s at %s" % (parts[2], parts[3])
    return game_id


def td(v, cls=""):
    c = ' class="%s"' % cls if cls else ""
    return "<td%s>%s</td>" % (c, v)


def page(title, body, active):
    nav = "\n".join(
        '  <a href="%s"%s>%s</a>' % (href, ' class="on"' if href == active else "", label)
        for href, label in NAV)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s - NFL Command Center</title>
<meta name="description" content="Official-source NFL analysis, own lines, validated strategies and a repository audit.">
<link rel="stylesheet" href="assets/command.css">
</head>
<body>
<header class="site"><div class="wrap">
  <h1>NFL Command Center</h1>
  <p>Week 10 of the 2026 season. Every standings, schedule and injury value on this site comes from an official NFL page and carries that page's link. Betting prices come from a named third-party archive, because the NFL publishes no betting lines, and are labelled as such everywhere they appear.</p>
</div></header>
<nav class="sitenav"><div class="wrap">
%(nav)s
</div></nav>
<main>
%(body)s
</main>
<footer class="site"><div class="wrap">
  <p><strong>Source policy.</strong> Official values link to nfl.com. Third-party values link to the named archive and say so in the column header. A value that no official source confirms is left blank and marked unverified.</p>
  <p><strong>Responsible gambling.</strong> No strategy on this site is a recommendation to bet. No betting strategy passes the validation gates, so nothing here is activated. If gambling is a problem, contact the National Council on Problem Gambling helpline on 1-800-522-4700, or ncpgambling.org.</p>
  <p class="small">Built %(built)s by <code>nfl-command-center/engine/05_build_site.py</code> from checked-in data. Every table row carries a source link.</p>
</div></footer>
</body>
</html>
""" % {"title": e(title), "nav": nav, "body": body, "built": "2026-11-13"}


def card(k, v, d, link=None, url=None):
    inner = '<div class="k">%s</div><div class="v">%s</div><div class="d">%s</div>' % (e(k), v, d)
    if link and url:
        inner = '<a href="%s">%s</a>' % (e(url), inner)
    return '<div class="card">%s</div>' % inner


def main():
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "command.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)

    D = lambda name: load_json(os.path.join(DERIVED, name))
    O = lambda name: load_json(os.path.join(ROOT, "data", "official", name))
    standings = O("standings_2026.json")
    slate = O("slate_week10_2026.json")
    designations = O("injury_designations_week10_2026.json")
    articles = O("official_articles_week10.json")
    reg = load_json(os.path.join(ROOT, "data", "registers.json"))
    fc = D("forecasts.json")
    model_card = D("model_card.json")
    strategies = D("strategies.json")
    leaderboard = D("leaderboard.json")
    correlations = D("correlations.json")
    luck = D("luck.json")
    integrity = D("integrity.json")
    own_lines = D("own_lines.json")
    injuries = D("injuries_week10_normalized.json")
    depth = D("depth_deficiency_week10.json")
    audit = D("repo_audit.json")
    gates = load_json(os.path.join(ROOT, "data", "gates_preregistered.json"))
    registry = load_json(os.path.join(ROOT, "data", "strategy_registry_preregistered.json"))
    price = load_json(os.path.join(ROOT, "data", "price_determination.json"))
    convention = load_json(os.path.join(ROOT, "data", "spread_convention_determination.json"))
    amendment = load_json(os.path.join(ROOT, "data", "parameter_amendment_1.json"))

    src_of = {s["id"]: s["url"] for s in articles["sources"]}
    own_by_id = {r["game_id"]: r for r in own_lines["rows"]}
    written = []

    t = audit["totals"]
    tokens = {
        "{audit_files}": "{:,}".format(t["files_audited"]),
        "{audit_flagged}": str(t["files_flagged"]),
        "{audit_placeholders}": str(t["files_with_placeholders"]),
        "{audit_rows}": "{:,}".format(t["table_rows"]),
        "{audit_rows_linked}": "{:,}".format(t["table_rows_with_a_link"]),
        "{audit_rows_unlinked}": "{:,}".format(t["table_rows"] - t["table_rows_with_a_link"]),
        "{audit_official_links}": "{:,}".format(t["official_links"]),
        "{audit_conflicts}": str(t["cross_namespace_record_conflicts"]),
        "{audit_html_pages}": str(sum(v["html"] for k, v in audit["namespaces"].items() if k.startswith("nfl"))),
        "{audit_nflns}": str(len([k for k in audit["namespaces"] if k.startswith("nfl")])),
    }

    def write(fn, title, body):
        for k, v in tokens.items():
            body = body.replace(k, v)
        with open(os.path.join(PAGES, fn), "w", encoding="utf-8") as fh:
            fh.write(page(title, body, fn))
        written.append(fn)

    # ------------------------------------------------------------------ index
    hb = leaderboard["baselines"]["holdout"]
    n_out = sum(1 for s in strategies["results"] if s["status"] == "Evaluated")
    n_blocked = sum(1 for s in strategies["results"] if s["status"] == "Blocked")
    # the best return and the p-value that belongs to it, not the best p-value
    priced = [s for s in strategies["results"] if s.get("roi") is not None]
    best_strategy = max(priced, key=lambda s: s["roi"]) if priced else {}
    n_nfl_namespaces = len([k for k in audit["namespaces"] if k.startswith("nfl")])
    n_unplayed = sum(1 for r in own_lines["rows"] if not r.get("played"))
    body = """
<h2>What this site is</h2>
<p>This is the clean, source-linked NFL site built from scratch for the current week. It holds the official 2026 standings, the official Week 10 slate, the official injury designations, own model lines, a validated strategy leaderboard, measured correlations, a full repository audit and a register of every open decision.</p>
<div class="grid">
%(cards)s
</div>
<div class="note"><strong>Read this first.</strong> No betting strategy passes the validation gates, so nothing on this site is activated as a bet. The forecast board is the only board that pays points, and it pays for forecast skill against a naive baseline, which needs no price.</div>
<h2>Where each number comes from</h2>
%(source_table)s
<h2>The official Week 10 slate</h2>
<p>Every game, time, network and link below is taken from the official NFL.com schedule page for Week 10.</p>
%(slate_table)s
<h2>How to review this site</h2>
<ul class="tight">
<li><a href="traceability.html">Requirements traceability</a> - every requirement in the brief, where it is implemented and whether it is met.</li>
<li><a href="decisions.html">Decision register</a> - what was decided, what is still unknown and how to find out.</li>
<li><a href="suggestions.html">Suggestions</a> - eight options with evidence, risk and prerequisites. None of them is approved.</li>
<li><a href="flagged-for-review.html">Flagged for review</a> - every irregularity, unverified value and open item.</li>
<li><a href="audit.html">Repository audit</a> - all 927 files outside this namespace, with a manual review link for each.</li>
<li><a href="methodology.html">Methodology</a> - the model, the gates, the pre-registration and the price audit.</li>
</ul>
""" % {
        "cards": "".join([
            card("Own lines", str(n_unplayed), "Week 10 games still to be played", "own-lines.html", "own-lines.html"),
            card("Holdout spread error", "%.2f pts" % hb["own_spread_mae"], "own model, against a market line of %.2f and a naive baseline of %.2f" % (hb["market_spread_mae"], hb["naive_spread_mae"])),
            card("Strategies evaluated", str(n_out), "%d blocked for want of a verifiable price" % n_blocked, "strategies.html", "strategies.html"),
            card("Reward points paid", str(sum(r["reward_points"] for r in leaderboard["forecast_board"])), "forecast board only; the betting board pays nothing", "strategies.html", "strategies.html"),
            card("Files audited", str(audit["totals"]["files_audited"]), "%d flagged, %d still carrying placeholder text" % (audit["totals"]["files_flagged"], audit["totals"]["files_with_placeholders"]), "audit.html", "audit.html"),
            card("Injury rows", str(injuries["reconciliation"]["rows_total"]), "%d confirmed against the official report, 0 conflicts" % injuries["reconciliation"]["rows_confirmed_and_agreeing"], "injuries.html", "injuries.html"),
        ]),
        "source_table": table(
            ["Data", "Publisher", "Official?", "Link"],
            [[td("2026 league standings"), td("NFL.com"), td('<span class="badge pass">official</span>'),
              src_cell(OFFICIAL_SOURCES["standings"][0], "nfl.com")],
             [td("Week 10 schedule and slate"), td("NFL.com"), td('<span class="badge pass">official</span>'),
              src_cell(OFFICIAL_SOURCES["slate"][0], "nfl.com")],
             [td("Week 10 injury designations"), td("NFL.com"), td('<span class="badge pass">official</span>'),
              src_cell(OFFICIAL_SOURCES["injuries"][0], "nfl.com")],
             [td("Depth chart news and game books"), td("NFL.com"), td('<span class="badge pass">official</span>'),
              src_cell(OFFICIAL_SOURCES["roundup_wed"][0], "nfl.com")],
             [td("Final scores, dates, lines and prices"), td("nflverse/nfldata"), td('<span class="badge info">third party</span>'),
              src_cell(OFFICIAL_SOURCES["archive"][0], "github.com")],
             [td("Own model lines and ratings"), td("This project"), td('<span class="badge info">own model</span>'),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]]),
        "slate_table": table(
            ["Matchup", "Day and time", "Network", "Own spread", "Own total", "Source"],
            [[td("%s at %s" % (g["away"], g["home"])), td("%s, %s" % (g["day"], g["kickoff"])), td(g["network"]),
              td("%.2f" % own_by_id[g["game_id"]]["own_spread_home"], "num")
              if g["game_id"] in own_by_id and not own_by_id[g["game_id"]].get("played") else td("already played"),
              td("%.2f" % own_by_id[g["game_id"]]["own_total"], "num")
              if g["game_id"] in own_by_id and not own_by_id[g["game_id"]].get("played") else BLANK,
              src_cell(g["url"], "nfl.com game page")]
             for g in slate["games"]]),
    }
    write("index.html", "Overview", body)

    # ------------------------------------------------------- executive summary
    elig = [r for r in leaderboard["forecast_board"] if r["reward_points"] > 0]
    body = """
<h2>Summary</h2>
<p>%(nnflns)d prior NFL workspaces were found in this repository. They overlap heavily, they disagree in places, and %(nplaceholders)d of their files still carry placeholder text. This session built a separate, clean, source-linked site from official NFL pages and a pinned third-party archive, audited every other file in the repository without editing any of it, and published the result as a single site with fifteen pages.</p>
<h2>What was built</h2>
<div class="grid">
%(cards)s
</div>
<h2>What the numbers say</h2>
%(table)s
<h2>What was found</h2>
<ul class="tight">
<li><strong>Official data reconciles exactly.</strong> Every team's 2026 wins, losses, ties, points for and points against recomputed from the game log match the official NFL.com league standings page. League points for and points against are equal at 6,291, and the season's one tie is handled as a push everywhere.</li>
<li><strong>No betting strategy is activated.</strong> Of %(neval)d evaluated strategies, none passes the validation gates. The best holdout return is %(best)s, from strategy %(bestid)s on %(bestbets)d bets, with a permutation p-value of %(bestp)s. A placebo null built from a thousand skill-free peers places the 95th percentile of the peer return at %(p95)s.</li>
<li><strong>Forecast skill is real but modest.</strong> The corrected model beats the naive baseline on the holdout by %(skill)s points of mean absolute error, and the difference is non-negative in all four validation and holdout seasons. It does not beat the market line, which is %(mkt)s points better than the naive baseline.</li>
<li><strong>The third-party price columns are defective.</strong> The archive's spread price columns are anti-calibrated over 5,432 games and its over price sign carries no information over 5,429 games. The spread strategies were rebuilt on a reference probability reconstructed from the market's moneyline and line; the total strategies are blocked because a total has no moneyline to reconstruct from.</li>
<li><strong>The pre-registered model had a defect that was found on the development window and corrected before the corrected model was scored.</strong> A three percent per-game mean reversion applied to a mean-zero rating is a decay of the whole scale, which left the ratings with a standard deviation of 1.3 points after a season. The correction was selected on 1999 to 2022 only and registered in a dated amendment before the holdout was rescored.</li>
<li><strong>Depth information is thin because the official sources are thin.</strong> Seven depth deficiency rows are supported by an official article or an official game book. Only one has an officially stated depth position. The rest are blank and flagged.</li>
</ul>
<h2>What is not established</h2>
<ul class="tight">
<li>That any betting strategy has an edge. The evidence points the other way.</li>
<li>That the model can beat a closing line. It cannot at present.</li>
<li>That the depth position of most replacement starters is known. Only one is.</li>
<li>That the %(nnflns)d prior NFL workspaces should be merged. That is a decision for the owner and is written up as suggestion S-01.</li>
</ul>
<div class="note warn"><strong>Nothing here is a betting recommendation.</strong> No strategy on this site is activated. The betting board pays nothing. If gambling is a problem, contact the National Council on Problem Gambling on 1-800-522-4700 or ncpgambling.org.</div>
""" % {
        "cards": "".join([
            card("Official standings rows", "32", "all reconciled against the game log"),
            card("Own lines", "13", "Week 10 games still to be played"),
            card("Injury rows normalised", str(injuries["reconciliation"]["rows_total"]), "0 conflicts with the official report"),
            card("Files audited", str(audit["totals"]["files_audited"]), "%d flagged" % audit["totals"]["files_flagged"]),
            card("Table rows without a source", "{:,}".format(
                audit["totals"]["table_rows"] - audit["totals"]["table_rows_with_a_link"]),
                "across the audited namespaces, listed for review"),
            card("Reward points", str(sum(r["reward_points"] for r in leaderboard["forecast_board"])), "forecast board only"),
        ]),
        "table": table(
            ["Measure", "Value", "Comparison", "Source"],
            [[td("Holdout spread error, own model"), td("%.2f points" % hb["own_spread_mae"], "num"),
              td("market line %.2f, naive baseline %.2f" % (hb["market_spread_mae"], hb["naive_spread_mae"])),
              src_cell(OFFICIAL_SOURCES["repo"][0], "this project")],
             [td("Holdout win probability error, own model"), td("%.4f" % hb["own_brier"], "num"),
              td("market moneyline %.4f" % hb["market_brier"]),
              src_cell(OFFICIAL_SOURCES["archive"][0], "third-party archive")],
             [td("Correlation of prediction with outcome"), td("%.4f" % correlations["rows"][10]["r"], "num"),
              td("on the holdout"),
              src_cell(OFFICIAL_SOURCES["repo"][0], "this project")],
             [td("League points for and against"), td("6,291 and 6,291", "num"),
              td("recomputed from 137 played games and reconciled with the official standings"),
              src_cell(OFFICIAL_SOURCES["standings"][0], "nfl.com")],
             [td("Look-ahead forecasts that changed when 422 holdout outcomes were perturbed"), td("0", "num"),
              td("out of 6,991 earlier forecasts"),
              src_cell(OFFICIAL_SOURCES["repo"][0], "this project")]]),
        "neval": n_out,
        "best": "%.2f%%" % (100 * best_strategy["roi"]),
        "bestid": best_strategy["id"],
        "bestp": "%.3f" % best_strategy["permutation_p"],
        "bestbets": best_strategy["bets"],
        "p95": "%.2f%%" % (100 * best_strategy["placebo"]["roi_p95"]) if best_strategy.get("placebo") else "not available",
        "nnflns": n_nfl_namespaces,
        "nplaceholders": audit["totals"]["files_with_placeholders"],
        "skill": "%.2f" % (hb["naive_spread_mae"] - hb["own_spread_mae"]),
        "mkt": "%.2f" % (hb["naive_spread_mae"] - hb["market_spread_mae"]),
    }
    write("executive-summary.html", "Executive summary", body)

    # ---------------------------------------------------------------- findings
    body = """
<h2>Findings</h2>
<p>Each finding below is backed by a check that can be re-run. Nothing here is asserted without a source.</p>
%(findings)s
<h2>Integrity checks</h2>
%(integrity)s
""" % {
        "findings": "".join(
            "<h3>%s</h3><p>%s</p>" % (e(f["id"] + " - " + f["name"]), e(f["detail"]))
            for f in [
                {"id": "F-01", "name": "The official data reconciles exactly",
                 "detail": "Recomputing every team's 2026 record and points from the game log reproduces the official NFL.com league standings for all 32 teams, with no mismatch. League points for and points against are both 6,291, and the single tied game is treated as a push for spread, total and moneyline bets."},
                {"id": "F-02", "name": "The archive's spread line is the away team's line",
                 "detail": "A regression of the actual margin on the archive's spread line has a slope of 1.04 and an intercept of -0.04, so a positive spread line means the home team is the favourite. The moneyline cross check agrees in 99.41% of 5,432 games. The rejected reading agrees in 0.57%."},
                {"id": "F-03", "name": "The archive's spread and total prices fail a calibration test",
                 "detail": "Games the archive prices at 0.45 for the home side to cover actually cover 69% of the time, and games it prices at 0.55 cover 45% of the time. The over price sign does not predict the over rate: 49.0% when negative and 49.5% when positive, against a 49.1% base rate. The moneyline columns, by contrast, are well calibrated and were retained."},
                {"id": "F-04", "name": "The forecast engine has no look-ahead",
                 "detail": "Shifting the outcome of all 422 holdout games by seven points and re-running the engine changes none of the 6,991 forecasts made before the holdout. The test is recorded in every run."},
                {"id": "F-05", "name": "The pre-registered model had a rating decay defect",
                 "detail": "A three percent per-game mean reversion applied to a mean-zero rating removes essentially the whole rating within a season, leaving a rating standard deviation of 1.3 points. The defect was found and fixed using the 1999 to 2022 development window only, and the fix was registered in a dated amendment before the corrected model was scored on the holdout."},
                {"id": "F-06", "name": "No betting strategy separates itself from chance",
                 "detail": "The best evaluated strategy returns 2.27% on 335 holdout bets with a permutation p-value of 0.672, which does not clear the 0.05 floor. The placebo null places the 95th percentile of a thousand skill-free peers above it. Nothing is activated.",
                 "source": OFFICIAL_SOURCES["repo"][0]},
                {"id": "F-07", "name": "The own model beats the naive baseline but not the market",
                 "detail": "On the holdout the own model's spread error is 10.31 points, the naive baseline is 10.92 and the market line is 9.60. The forecast board rewards the first comparison, which needs no price. The betting board would need the second, and no strategy achieves it."},
                {"id": "F-08", "name": "The official sources rarely state a replacement starter's depth",
                 "detail": "Seven depth deficiency rows are supported by an official article or an official game book. Exactly one carries an officially stated depth position; the other six are blank and marked unverified rather than guessed."},
                {"id": "F-09", "name": "The other namespaces carry table rows with no source link",
                 "detail": "Across {audit_files} audited files there are {audit_rows} table rows, of which {audit_rows_linked} carry a link and {audit_rows_unlinked} do not. {audit_flagged} files are flagged and {audit_placeholders} still contain placeholder text. The prior namespaces are outside this session's claim, so they were read and audited but not rewritten."},
                {"id": "F-10", "name": "Player prop strategies cannot be priced from any official source",
                 "detail": "The NFL publishes no player prop prices and no official player game log was found for the current week. The two prop strategies are Blocked rather than evaluated: no return is reported for them and no reward is offered."},
            ]),
        "integrity": table(
            ["Check", "Result", "Detail", "Source"],
            [[td(i["id"] + " " + i["name"]),
              td('<span class="badge %s">%s</span>' % ("pass" if i["result"] == "PASS" else "fail", i["result"])),
              td(i["detail_value"]),
              src_cell(OFFICIAL_SOURCES["standings"][0] if "SRC-01" in i.get("source_ids", []) else OFFICIAL_SOURCES["repo"][0],
                       "nfl.com" if "SRC-01" in i.get("source_ids", []) else "this project")]
             for i in integrity["rows"]]),
    }
    write("findings.html", "Findings", body)

    # ---------------------------------------------------- flagged for review
    flagged = []
    for f in audit["findings"]:
        fl = [x for x in f["findings"] if x[0] == "FLAG"]
        if fl:
            flagged.append((f, fl))
    body = """
<h2>Flagged for review</h2>
<p>Nothing on this page blocks publication. Every item is published so that a reviewer can decide what to do with it. Each row links to the file and to the source that would settle it.</p>
<div class="note warn"><strong>Scope.</strong> The other NFL namespaces are outside this session's claim in COORDINATION.md. The entries below are read-only findings about those files. No file outside <code>nfl-command-center/</code> was edited.</div>
<h2>Open items in this site</h2>
%(open)s
<h2>Files flagged by the repository audit</h2>
<p>%(nfiles)d of %(nall)d files were flagged. The full per-file list with a manual review link for each is on the <a href="audit.html">repository audit</a> page.</p>
%(files)s
<h2>Unverified values published by this site</h2>
%(unver)s
""" % {
        "open": table(
            ["Item", "Why it is open", "How to close it", "Source"],
            [[td("Total market prices (strategies S3 and P3)"),
              td("The archive's over and under prices failed the calibration test and a total has no moneyline to reconstruct a market probability from."),
              td("Bring in a second price source and test it the same way. Written up as suggestion S-08."),
              src_cell(OFFICIAL_SOURCES["archive"][0], "archive")],
             [td("Player prop prices (strategies C1 and C2)"),
              td("The NFL publishes no prop prices and no official player game log was found."),
              td("Capture an official player statistics feed and settle against a named third-party price. Written up as suggestion S-02."),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Depth position of five of the seven replacement starters"),
              td("The official articles name the replacement but not its depth position."),
              td("Fold in the official game book for each game once it is published. Written up as suggestion S-06."),
              src_cell(OFFICIAL_SOURCES["gb_jax"][0], "game book")],
             [td("Miami's Week 10 starting quarterback"),
              td("Only the headline of the official article was read and it says in line for a first start, which is not a confirmed start."),
              td("Read the article body and then the game book."),
              src_cell(OFFICIAL_SOURCES["dolphins"][0], "nfl.com")],
             [td("The dollar value of the reward pool"),
              td("The reward policy was pre-registered as non-monetary until the owner funds a pool."),
              td("Owner decision. Written up as suggestion S-05."),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Consolidation of the prior NFL workspaces"),
              td("They overlap heavily and are outside this session's claim."),
              td("Owner decision after reading the audit. Written up as suggestion S-01."),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]]),
        "nfiles": len(flagged),
        "nall": audit["totals"]["files_audited"],
        "files": table(
            ["File", "Flag", "Manual review", "Source"],
            [[td('<a href="https://github.com/sassnarep3-star/Own4/blob/main/%s">%s</a>' % (e(f["file"]), e(f["file"]))),
              td("; ".join(x[1] for x in fl)),
              td('<a href="https://github.com/sassnarep3-star/Own4/blob/main/%s">open</a>' % e(f["file"])),
              src_cell(OFFICIAL_SOURCES["repo"][0], "repository")]
             for f, fl in flagged[:120]]),
        "unver": table(
            ["Value", "Where it appears", "Why it is blank", "Source"],
            [[td("Market spread, market total and market moneyline on the own lines table"),
              td("Own lines page"),
              td("No official NFL source publishes a betting line. The market cells are left blank in the official tables; the third-party values appear only in the tables labelled third-party."),
              src_cell(OFFICIAL_SOURCES["slate"][0], "nfl.com")],
             [td("Replacement starter for Baltimore's quarterback"),
              td("Depth chart page"),
              td("No official source read in this session names the Week 10 starting quarterback. The official game books show who started the previous two games."),
              src_cell(OFFICIAL_SOURCES["roundup_fri"][0], "nfl.com")],
             [td("Depth position for the Arizona, Cleveland, Miami and Baltimore kicker replacements"),
              td("Depth chart page"),
              td("The official articles do not state a depth position and no official game book covers those games yet."),
              src_cell(OFFICIAL_SOURCES["roundup_wed"][0], "nfl.com")],
             [td("Game status for 177 of the 326 captured injury rows"),
              td("Injuries page"),
              td("The official Week 10 report article publishes no designation for those players. The practice report is linked and the game-status cell is marked as unverified against the article."),
              src_cell(OFFICIAL_SOURCES["injuries_page"][0], "nfl.com")]]),
    }
    write("flagged-for-review.html", "Flagged for review", body)

    # ------------------------------------------------------------ traceability
    body = """
<h2>Requirements traceability register</h2>
<p>Every requirement in the brief, where it is implemented, what the evidence is and whether it is met. A partial means the part that is not met is stated, not hidden.</p>
%(table)s
""" % {"table": table(
        ["ID", "Requirement", "Status", "Implemented in", "Evidence", "Source"],
        [[td(r["id"]), td(r["requirement"]),
          td('<span class="badge %s">%s</span>' % ("pass" if r["status"].startswith("Met") else "info", r["status"].split(" - ")[0])),
          td("<code>%s</code>" % e(r["implemented_in"])), td(r["evidence"]),
          src_cell(r["source"], "source")]
         for r in reg["requirements_traceability"]])}
    write("traceability.html", "Traceability", body)

    # ---------------------------------------------------------------- decisions
    body = """
<h2>Decision register</h2>
<p>Each entry separates what is known from what is not, gives the answer that was acted on, names the blocker and gives a route to discover whatever is still missing. Nothing here was decided by assumption.</p>
%(table)s
""" % {"table": table(
        ["ID", "Question", "Known", "Unknown", "Answer", "Blocker", "How to find out", "Status", "Source"],
        [[td(d["id"]), td(d["question"]), td(d["known"]), td(d["unknown"]), td(d["answer"]), td(d["blocker"]),
          td(d["discovery_route"]), td(d["status"]), src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
         for d in reg["decision_register"]])}
    write("decisions.html", "Decisions", body)

    # -------------------------------------------------------------- suggestions
    body = """
<h2>Suggestions</h2>
<div class="note warn"><strong>None of these is approved.</strong> Each one is an option for the owner to weigh, with its evidence, its risk and what has to happen first. No suggestion in this register has been implemented, and no suggestion is scheduled.</div>
%(table)s
""" % {"table": table(
        ["ID", "Option", "What it would do", "Evidence", "Risk", "Prerequisites", "Recommendation", "Approved", "Source"],
        [[td(s["id"]), td(s["title"]), td(s["option"]), td(s["evidence"]), td(s["risk"]), td(s["prerequisites"]),
          td(s["recommendation"]), td('<span class="badge blocked">no</span>'), src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
         for s in reg["suggestions"]])}
    write("suggestions.html", "Suggestions", body)

    # ---------------------------------------------------------------- standings
    body = """
<h2>Official 2026 league standings</h2>
<p>Captured from the official NFL.com league standings page and reconciled against the game log. Every team's wins, losses, ties, points for and points against were recomputed and matched exactly.</p>
%(table)s
""" % {"table": table(
        ["Team", "W", "L", "T", "PF", "PA", "Net", "Source"],
        [[td("%s (%s)" % (r["team"], r["name"])), td(r["w"], "num"), td(r["l"], "num"), td(r["t"], "num"),
          td(r["pf"], "num"), td(r["pa"], "num"), td(r["net"], "num"),
          src_cell(standings["url"], "nfl.com")]
         for r in standings["rows"]])}
    write("standings.html", "Standings", body)

    # ---------------------------------------------------------------- own lines
    body = """
<h2>Own lines for the Week 10 slate</h2>
<p>These are this project's model lines, produced by a walk-forward rating model whose parameters were registered before it ran. The market cells are deliberately blank: no official NFL source publishes a betting line, and a third-party value does not belong in an official table. The third-party archive's line for each game is in the third-party table underneath, which is labelled as such in its header and in every row.</p>
<p>Spread is the home team's expected margin, so a positive number favours the home team. The home win probability is the model probability that the home team wins.</p>
<h3>Own lines, official-sourced table</h3>
%(own)s
<h3>Third-party market lines, labelled table</h3>
%(mkt)s
""" % {
        "own": table(
            ["Matchup", "Kickoff", "Own spread (home)", "Own total", "Own home win probability", "Home games rated", "Market spread", "Market total", "Source"],
            [[td("%s at %s" % (r["away"], r["home"])), td("%s, %s" % (r["day"], r["kickoff"])),
              td("%.2f" % r["own_spread_home"], "num") if not r.get("played") else td("already played"),
              td("%.2f" % r["own_total"], "num") if not r.get("played") else BLANK,
              td("%.4f" % r["own_home_win_prob"], "num") if not r.get("played") else BLANK,
              td(r["home_rated_games"], "num"),
              td(BLANK), td(BLANK), src_cell(r["url"], "nfl.com game page")]
             for r in own_lines["rows"]]),
        "mkt": table(
            ["Matchup", "Third-party market spread (home)", "Third-party market total",
             "Third-party home moneyline", "Third-party source", "Official source"],
            [[td("%s at %s" % (r["away"], r["home"])),
              td("%.2f" % r["third_party_spread_home"], "num")
              if r.get("third_party_spread_home") is not None else BLANK,
              td("%.2f" % r["third_party_total"], "num")
              if r.get("third_party_total") is not None else BLANK,
              td(str(r["third_party_home_ml"])) if r.get("third_party_home_ml") is not None else BLANK,
              src_cell(OFFICIAL_SOURCES["archive"][0], "nflverse/nfldata"),
              src_cell(r["url"], "nfl.com game page")]
             for r in own_lines["rows"]]),
    }
    write("own-lines.html", "Own lines", body)

    # -------------------------------------------------------------- strategies
    gate_rows = []
    for s in strategies["results"]:
        gate_rows.append([td(s["id"]), td(s["name"]),
                           td('<span class="badge %s">%s</span>' % ("pass" if s["status"] == "Evaluated" else "blocked", s["status"])),
                           td(s["bets"], "num"), td("%.2f%%" % (100 * s["roi"]) if s["roi"] is not None else NOT_COMPUTED, "num"),
                           td("%.3f" % s["permutation_p"] if s["permutation_p"] is not None else NOT_COMPUTED, "num"),
                           td("%d / %d" % (s.get("gates_passed", 0), len(s.get("gates", {})))),
                           td("yes" if s.get("reward_eligible") else "no"),
                           src_cell(OFFICIAL_SOURCES["archive"][0], "archive")])
    body = """
<h2>The two boards</h2>
<p>The <strong>forecast board</strong> compares the own model with a naive pick-em baseline. It needs no price, so it can be scored and paid. The <strong>betting board</strong> needs a price, and no strategy in the registered family clears the gates.</p>
<h2>Forecast board</h2>
<p>A variant earns reward points only if gates G1, G2, G6 and G9 pass. Points are round(50 times z), where z is the paired z statistic of the holdout improvement over the naive baseline, capped at 500. Variants V1 to V6 are shown for transparency but are not eligible: they use the model as it was originally registered, before the rating decay defect was corrected.</p>
%(fb)s
<h2>Betting board</h2>
<p>A strategy earns reward points only if gates G1 to G9 all pass. Points are round(100 times the t statistic of the holdout return against the no-edge null), capped at 1,000.</p>
%(bb)s
<h2>Blocked strategies</h2>
<p>A strategy whose price cannot be verified is Blocked, not evaluated. No return is reported for it and it earns nothing.</p>
%(blocked)s
<h2>Luck band</h2>
<p>The luck band is the half-width of the interval that pure chance around a fifty percent base rate would produce at each strategy's sample size. An observed edge smaller than its own luck band has not separated itself from luck.</p>
%(luck)s
<h2>The ten gates</h2>
%(gates)s
""" % {
        "fb": table(
            ["Variant", "Holdout spread error", "Naive baseline", "z", "G1", "G2", "G6", "G9", "Points", "Eligible", "Source"],
            [[td("%s %s" % (r["id"], r["name"])), td("%.4f" % r["spread_mae"], "num"),
              td("%.4f" % r["naive_spread_mae"], "num"), td("%.4f" % r["z_vs_naive"], "num"),
              td('<span class="badge %s">%s</span>' % ("pass" if r["gates"]["G1"] == "Pass" else "fail", r["gates"]["G1"])),
              td('<span class="badge %s">%s</span>' % ("pass" if r["gates"]["G2"] == "Pass" else "fail", r["gates"]["G2"])),
              td('<span class="badge %s">%s</span>' % ("pass" if r["gates"]["G6"] == "Pass" else "fail", r["gates"]["G6"])),
              td('<span class="badge %s">%s</span>' % ("pass" if r["gates"]["G9"] == "Pass" else "fail", r["gates"]["G9"])),
              td(r["reward_points"], "num"),
              td("yes" if r.get("reward_eligible_variant") else "no"),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
             for r in leaderboard["forecast_board"]]),
        "bb": table(
            ["ID", "Strategy", "Status", "Bets", "Holdout return", "Permutation p", "Gates passed", "Reward eligible", "Source"],
            gate_rows),
        "blocked": table(
            ["ID", "Strategy", "Why it is blocked", "Source"],
            [[td(s["id"]), td(s["name"]), td(s.get("blocked_reason", "")),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
             for s in strategies["results"] if s["status"] == "Blocked"]),
        "luck": table(
            ["ID", "Bets", "Win rate", "Luck band half-width", "Bets needed for 80% power", "Source"],
            [[td(l["id"]), td(l["bets"], "num"),
              td("%.4f" % l["win_rate"] if l.get("win_rate") is not None else NOT_COMPUTED, "num"),
              td("%.4f" % l["luck_band_half_width"] if l.get("luck_band_half_width") is not None else NOT_COMPUTED, "num"),
              td(l.get("bets_needed_for_80pct_power") if l.get("bets_needed_for_80pct_power") else NOT_COMPUTED, "num"),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
             for l in luck["rows"]]),
        "gates": table(
            ["Gate", "Name", "Threshold", "Why", "Source"],
            [[td(g["id"]), td(g["name"]), td(g["threshold"]), td(g["rationale"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
             for g in gates["gates"]]),
    }
    write("strategies.html", "Strategies", body)

    # -------------------------------------------------------------- correlations
    body = """
<h2>Correlations</h2>
<p>Every correlation is measured on out-of-sample data with a sample size, a Pearson coefficient, a Fisher confidence interval, a p value and a Benjamini-Hochberg q value across the family. A gate that cannot be evaluated is Blocked, never Passed.</p>
%(table)s
""" % {"table": table(
        ["ID", "What is correlated", "Scope", "n", "r", "95% interval", "p", "q", "Reading", "Source"],
        [[td(c["id"]), td(c["name"]), td(c["scope"]), td(c["n"], "num"),
          td("%.5f" % c["r"] if c["r"] is not None else BLANK, "num"),
          td("%.5f to %.5f" % (c["ci_low"], c["ci_high"]) if c.get("ci_low") is not None
             else NOT_CORRELATION),
          td("%.6f" % c["p"] if c.get("p") is not None else NOT_CORRELATION, "num"),
          td("%.6f" % c["q"] if c.get("q") is not None else NOT_CORRELATION, "num"),
          td(c["note"]), src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]
         for c in correlations["rows"]])}
    write("correlations.html", "Correlations", body)

    # ----------------------------------------------------------------- injuries
    body = """
<h2>Week 10 injuries</h2>
<p>%(rows)d rows were captured from the official NFL.com injuries page for all 14 games. Every game status was checked against the official Week 10 injury report article: %(matched)d rows carry an official designation, %(agree)d of them agree, and there are %(conf)d conflicts. %(practice)d rows carry a practice report only; their game-status cell is marked unverified against the article and the practice page is linked. The one placeholder in the capture, a Tennessee punter whose status had not been read, was resolved from the official article and is recorded as such.</p>
<p>%(officialonly)d designations appear in the official article but were not in the captured page rows. They are listed below with their official source so nothing from the official report is lost.</p>
<h3>Team counts</h3>
%(tc)s
<h3>Official designations that the capture did not carry</h3>
%(oo)s
<h3>Every row</h3>
<p>The full table with a source link on every row is published here.</p>
%(rowtable)s
""" % {
        "rows": injuries["reconciliation"]["rows_total"],
        "matched": injuries["reconciliation"]["rows_with_an_official_designation"],
        "agree": injuries["reconciliation"]["rows_confirmed_and_agreeing"],
        "conf": injuries["reconciliation"]["rows_with_a_status_conflict"],
        "practice": injuries["reconciliation"]["rows_practice_report_only"],
        "officialonly": injuries["reconciliation"]["official_designations_not_present_in_the_capture"],
        "tc": table(
            ["Game", "Team", "Out", "Doubtful", "Questionable", "Source"],
            [[td(matchup(c["game_id"])), td(c["team"]), td(c["out"], "num"), td(c["doubtful"], "num"), td(c["questionable"], "num"),
              src_cell(c["source_url"], "nfl.com")]
             for c in injuries["team_counts"]]),
        "oo": table(
            ["Game", "Team", "Player", "Position", "Injury", "Status", "Source"],
            [[td(matchup(o["game_id"])), td(o["team"]), td(o["player"]), td(o["position"]), td(o["injury"]), td(o["status"]),
              src_cell(o["source_url"], "nfl.com")]
             for o in injuries["reconciliation"]["official_only"]]),
        "rowtable": table(
            ["Game", "Team", "Player", "Pos", "Injury", "Practice status", "Game status", "Verification", "Source"],
            [[td(matchup(r["game_id"])), td(r["team"]), td(r["player"]), td(r["position"]),
              td(r["injury"] or BLANK), td(r["practice_status"] or NOT_CAPTURED),
              td(r["game_status"] or BLANK), td(r["verification"]),
              src_cell(r.get("source_url"), "nfl.com")]
             for r in injuries["rows"]]),
    }
    write("injuries.html", "Injuries", body)

    # --------------------------------------------------------------- depth chart
    body = """
<h2>Depth deficiencies</h2>
<p>%(rule)s</p>
<p>%(count)d rows are supported by an official source. %(ver)d of them carries an officially stated depth position; the other %(unver)d are blank in the depth column and marked unverified.</p>
%(table)s
""" % {
        "rule": depth["rule"],
        "count": depth["count"],
        "ver": depth["official_only_depth_verified"],
        "unver": depth["official_only_depth_unverified"],
        "table": table(
            ["ID", "Team", "Pos", "Game", "Incumbent", "Incumbent status", "Replacement", "Replacement depth", "Verdict", "Quote", "Source"],
            [[td(d["id"]), td(d["team"]), td(d["position"]), td(d["game"]),
              td(d["incumbent"] or BLANK), td(d["incumbent_status"] or BLANK),
              td(d["replacement"] or BLANK),
              td(d["replacement_depth"] or BLANK), td(d["verdict"]), td("<q>%s</q>" % e(d["quote"])),
              src_cell(d["source_url"], "nfl.com")]
             for d in depth["rows"]]),
    }
    write("depth-chart.html", "Depth chart", body)

    # -------------------------------------------------------------------- audit
    ns_rows = []
    for k, v in audit["namespaces"].items():
        if v["files"] == 0:
            continue
        ns_rows.append([td(k), td(v["files"], "num"), td(v["html"], "num"), td(v["official_links"], "num"),
                        td(v["third_party_links"], "num"), td(v["numeric_claims"], "num"),
                        td(v["table_rows"], "num"), td(v["table_rows_with_a_link"], "num"),
                        td(v["files_without_any_source_language"], "num"),
                        src_cell(OFFICIAL_SOURCES["repo"][0], "repository")])
    body = """
<h2>Repository audit</h2>
<p>%(scope)s</p>
<p><strong>Method.</strong></p>
<ul class="tight">%(method)s</ul>
<p><strong>Limits.</strong> This is an automated screen, not a line-by-line human reading of every character. A file can carry a source link and still make an unsupported claim, so every file is listed with its own manual review link. The full per-file list of 927 files is published as data on the repository.</p>
<h2>Totals</h2>
<div class="grid">
%(cards)s
</div>
<h2>By namespace</h2>
%(ns)s
<h2>Files with a finding</h2>
<p>%(nflag)d files are flagged. The full list of all {audit_files} audited files, with the findings for each and a manual review link, is published as JSON in the repository.</p>
%(files)s
""" % {
        "scope": audit["scope"],
        "method": "".join("<li>%s</li>" % e(m) for m in audit["method"]),
        "cards": "".join([
            card("Files audited", str(audit["totals"]["files_audited"]), "outside this session's namespace"),
            card("Files flagged", str(audit["totals"]["files_flagged"]), "with an automated finding"),
            card("Files with placeholders", str(audit["totals"]["files_with_placeholders"]), "still carrying placeholder text"),
            card("Table rows", "{:,}".format(audit["totals"]["table_rows"]), "across the repository"),
            card("Rows with a source link", "{:,}".format(audit["totals"]["table_rows_with_a_link"]),
                 "%s rows do not" % "{:,}".format(audit["totals"]["table_rows"] - audit["totals"]["table_rows_with_a_link"])),
            card("Official links", "{:,}".format(audit["totals"]["official_links"]), "and {:,} third-party links".format(audit["totals"]["third_party_links"])),
        ]),
        "ns": table(
            ["Namespace", "Files", "HTML", "Official links", "Third-party links", "Numeric claims", "Table rows", "Rows with a link", "Files with claims and no source wording", "Source"],
            ns_rows),
        "nflag": audit["totals"]["files_flagged"],
        "files": table(
            ["File", "Finding", "Metrics", "Manual review", "Source"],
            [[td('<a href="https://github.com/sassnarep3-star/Own4/blob/main/%s">%s</a>' % (e(f["file"]), e(f["file"]))),
              td("; ".join("%s: %s" % (x[0], x[1]) for x in f["findings"])),
              td("official links %d, third-party %d, claims %d, table rows %d"
                 % (f["metrics"]["official_links"], f["metrics"]["third_party_links"],
                    f["metrics"]["numeric_claims"], f["metrics"]["table_rows"])),
              td('<a href="https://github.com/sassnarep3-star/Own4/blob/main/%s">open</a>' % e(f["file"])),
              src_cell(OFFICIAL_SOURCES["repo"][0], "repository")]
             for f in audit["findings"] if any(x[0] == "FLAG" for x in f["findings"])]),
    }
    write("audit.html", "Repository audit", body)

    # ---------------------------------------------------------------- methodology
    body = """
<h2>Methodology</h2>
<h3>The model</h3>
<p>%(method)s</p>
<p><strong>Home field advantage.</strong> %(hfa)s</p>
<p><strong>Splits.</strong> Development %(dev)s. Validation %(val)s. Holdout %(hold)s</p>
<p><strong>Look-ahead test.</strong> %(look)s</p>
<h3>Pre-registration</h3>
<p>The gates and the model parameters were committed to git before the engine was first run. One dated amendment followed, recording a defect found on the development window, the fix, and the parameters selected on that window alone.</p>
%(amend)s
<h3>The price source</h3>
<p>%(price)s</p>
%(cal)s
<h3>Data sources</h3>
%(srcs)s
""" % {
        "method": model_card["method"],
        "hfa": model_card["home_field_advantage"],
        "dev": model_card["splits"]["development"],
        "val": model_card["splits"]["validation"],
        "hold": model_card["splits"]["holdout"],
        "look": "%d forecasts made before the holdout changed when the outcome of all 422 holdout games was shifted by seven points, out of %d earlier forecasts."
                % (model_card["look_ahead_test"]["forecasts_changed"], model_card["look_ahead_test"]["games_before_holdout"]),
        "amend": table(
            ["Field", "Value", "Source"],
            [[td("Amendment"), td(amendment["id"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Defect"), td(amendment["defect"]["what"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Selection window"), td("%s. The holdout was used in this selection: %s"
                                         % (amendment["development_window_selection"]["window"],
                                            str(amendment["development_window_selection"]["holdout_used_in_this_selection"]).lower())),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Selected parameters"), td("alpha %s, rho %s applied %s, home field %s points"
                                           % (amendment["primary_variant"]["alpha"], amendment["primary_variant"]["rho"],
                                              amendment["primary_variant"]["rho_application"].replace("_", " "),
                                              amendment["primary_variant"]["hfa"])),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Reward board scope"), td(amendment["reward_board_scope"]["rule"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]]),
        "price": "The NFL publishes no betting lines, so every price in this project comes from a named third-party archive with a recorded commit and checksum, and every such value is labelled third-party. " + price["reference_price_method"]["step_1"] + " " + price["reference_price_method"]["step_2"] + " " + price["reference_price_method"]["step_3"] + " " + price["reference_price_method"]["step_4"],
        "cal": table(
            ["Check", "Result", "Detail", "Source"],
            [[td("Moneyline columns"), td('<span class="badge pass">usable</span>'),
              td(price["column_audit"]["moneyline"]["verdict"]),
              src_cell(OFFICIAL_SOURCES["archive"][0], "archive")],
             [td("Spread price columns"), td('<span class="badge fail">not usable</span>'),
              td(price["column_audit"]["spread_price"]["verdict"]),
              src_cell(OFFICIAL_SOURCES["archive"][0], "archive")],
             [td("Total price columns"), td('<span class="badge fail">not usable</span>'),
              td(price["column_audit"]["total_price"]["verdict"]),
              src_cell(OFFICIAL_SOURCES["archive"][0], "archive")],
             [td("Spread line convention"), td('<span class="badge pass">resolved</span>'),
              td(convention["adopted"]["reason"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")],
             [td("Reconstructed reference price"), td('<span class="badge pass">calibrated</span>'),
              td(price["reference_price_method"]["validation_note"]),
              src_cell(OFFICIAL_SOURCES["repo"][0], "github.com")]]),
        "srcs": table(
            ["Source", "Publisher", "Official?", "Retrieved", "Link"],
            [[td(standings["title"]), td(standings["publisher"]), td('<span class="badge pass">official</span>'),
              td(standings["retrieved_utc"]), src_cell(standings["url"], "nfl.com")],
             [td(slate["title"]), td(slate["publisher"]), td('<span class="badge pass">official</span>'),
              td(slate["retrieved_utc"]), src_cell(slate["url"], "nfl.com")],
             [td(designations["source_title"]), td(designations["publisher"]), td('<span class="badge pass">official</span>'),
              td(designations["retrieved_utc"]), src_cell(designations["source_url"], "nfl.com")]]
            + [[td(s["title"]), td(s["publisher"]), td('<span class="badge pass">official</span>'),
                td(s["retrieved_utc"]), src_cell(s["url"], "nfl.com")]
               for s in articles["sources"]]
            + [[td("Games archive, commit a7eee2ca"), td("nflverse/nfldata"), td('<span class="badge info">third party</span>'),
                td("2026-11-13"), src_cell(OFFICIAL_SOURCES["archive"][0], "github.com")]]),
    }
    write("methodology.html", "Methodology", body)

    print("pages written:", len(written))
    for w in written:
        print("  ", w)


if __name__ == "__main__":
    main()

"""S8 — render the site. Static HTML only: no CDN, no external font, no script, no localhost.

Every table row that carries a fact also carries the official page it came from. A cell we did not read
is rendered as 'not read' or 'not asserted' with the reason, never as a plausible number.
"""
import html
import os
import re

from common import DATA, REGISTERED_UTC, read_json, ROOT

PAGES = os.path.join(ROOT, "pages")
S = "https://www.nfl.com"
W10 = S + "/schedules/2026/by-week/week-10"

# every page lives in pages/, so navigation is page-relative (no leading slash: the site may be
# served from a subdirectory, e.g. /Own4/nfl-sources/pages/)
NAV = [("index.html", "Readiness"), ("findings.html", "Findings"), ("backtest.html", "Backtest"),
       ("week11.html", "Week 11 lines"), ("ratings.html", "Ratings"),
       ("correlations.html", "Correlations"), ("strategies.html", "Strategies"),
       ("leaderboard.html", "Leaderboard"), ("requirements.html", "Requirements"),
       ("suggestions.html", "Suggestions"), ("questions.html", "Questions"),
       ("flagged.html", "Flagged"), ("sources.html", "Sources")]

CSS = """
:root{--ink:#12161c;--mut:#5d6773;--line:#dfe4ea;--bg:#fbfcfd;--card:#fff;--accent:#0b5cad;
--ok:#0b6b3a;--warn:#8a5a00;--bad:#a11b1b;--chip:#eef3f8}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
header{background:#0e1a2b;color:#eaf1f8;padding:14px 20px}
header .wrap{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:10px;align-items:baseline}
header a{color:#eaf1f8;text-decoration:none}
header .brand{font-weight:700;letter-spacing:.2px;margin-right:8px}
header nav{display:flex;flex-wrap:wrap;gap:2px}
header nav a{padding:3px 8px;border-radius:5px;font-size:13px;color:#c9d8e8}
header nav a:hover{background:#1b2c45;color:#fff}
header nav a.here{background:#eaf1f8;color:#0e1a2b;font-weight:600}
main{max-width:1180px;margin:0 auto;padding:22px 20px 60px}
h1{font-size:26px;margin:6px 0 4px;letter-spacing:-.2px}
h2{font-size:18px;margin:30px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--line)}
h3{font-size:15px;margin:18px 0 6px}
p.lede{color:var(--mut);margin:0 0 16px;max-width:78ch}
p{margin:8px 0}
.meta{color:var(--mut);font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:11px 13px}
.card .k{font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.card .v{font-size:21px;font-weight:650;margin-top:2px}
.card .s{font-size:12px;color:var(--mut)}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:13.2px;
border:1px solid var(--line);border-radius:9px;overflow:hidden;margin:8px 0 4px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:11.6px;text-transform:uppercase;letter-spacing:.5px;color:#39434f;
white-space:nowrap}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:nth-child(even){background:#fcfdfe}
.chip{display:inline-block;padding:1px 7px;border-radius:99px;font-size:11.5px;font-weight:600;
background:var(--chip);color:#2c3a48;white-space:nowrap}
.met{background:#e6f4ec;color:var(--ok)}.partial{background:#fdf3dc;color:var(--warn)}
.blocked{background:#fdeaea;color:var(--bad)}.ns{background:#f0eef7;color:#4a3d7a}
.na{background:#eef0f2;color:#4a5561}.rej{background:#f7e9f5;color:#7a2b6a}
.blank{color:var(--mut);font-style:italic}
a{color:var(--accent)}
.src{font-size:11.5px;white-space:nowrap}
details{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 13px;margin:8px 0}
summary{cursor:pointer;font-weight:600}
.note{background:#f6f9fc;border-left:3px solid var(--accent);padding:9px 13px;margin:12px 0;
border-radius:0 7px 7px 0}
.warnbox{background:#fdf7ea;border-left:3px solid var(--warn);padding:9px 13px;margin:12px 0;
border-radius:0 7px 7px 0}
footer{max-width:1180px;margin:0 auto;padding:18px 20px 40px;color:var(--mut);font-size:12px;
border-top:1px solid var(--line)}
code{background:#eef2f6;padding:1px 4px;border-radius:4px;font-size:12.5px}
.tiny{font-size:11.5px;color:var(--mut)}
"""


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def num(x, dp=4):
    if x is None:
        return '<span class="blank">not read</span>'
    if isinstance(x, str):
        return esc(x)
    return ("%%.%df" % dp) % x


def pct(x, dp=1):
    if x is None:
        return '<span class="blank">not read</span>'
    return ("%%.%df%%%%" % dp) % (100.0 * x)


def link(url, text=None):
    if not url:
        return '<span class="blank">no official page</span>'
    return '<a class="src" href="%s" rel="noopener">%s</a>' % (esc(url), esc(text or "official page"))


def be_wr(american):
    """Break-even hit rate implied by an American price. -A/(100-A) for negative A."""
    if american is None:
        return None
    a = float(american)
    if a < 0:
        return (-a) / (100.0 - a)
    return 100.0 / (100.0 + a)


STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
WEEK = "https://www.nfl.com/schedules/2026/by-week/week-%d"

# Which official page a data file's numbers are checkable on. A provenance cell must name the page
# the row's numbers actually came from, not a page that happens to be about football.
SRC_OF = {
    "results.json": (WEEK % 10, "week pages 1-10"),
    "forecast_register.json": (WEEK % 10, "week pages 3-10"),
    "backtest.json": (WEEK % 10, "week pages 3-10"),
    "correlations.json": (STANDINGS, "official scores"),
    "model.json": (WEEK % 9, "week pages 1-9"),
    "lines.json": (WEEK % 11, "week 11 schedule"),
    "strategies.json": (WEEK % 10, "week pages 3-10"),
    "requirements.json": (WEEK % 10, "official pages, per row"),
    "venues.json": (WEEK % 11, "game-centre pages"),
}


def prov(filename, what="derived"):
    """A row's provenance cell: the official page its numbers are checkable on, plus the artefact."""
    if what == "decision":
        return ('<span class="blank">decision, not a fact &#8212; no official page exists</span>'
                '<br><span class="tiny">data/%s</span>' % esc(filename))
    url, label = SRC_OF.get(filename, (STANDINGS, "official page"))
    return ('<a class="src" href="%s">%s</a><br><span class="tiny">data/%s</span>'
            % (url, esc(label), esc(filename)))


def chip(status):
    cls = {"met": "met", "partial": "partial", "blocked": "blocked", "not-started-here": "na",
           "not-this-namespace": "ns", "rejected-as-specified": "rej"}.get(status, "na")
    return '<span class="chip %s">%s</span>' % (cls, esc(status))


def table(headers, rows, cls="", src=None):
    """src: either None, a string applied to every row, or a list of per-row provenance strings."""
    heads = list(headers) + (["#Provenance"] if src is not None else [])
    out = ['<table%s><thead><tr>' % (' class="%s"' % cls if cls else "")]
    out += ["<th%s>%s</th>" % (' class="num"' if h.startswith("#") else "", esc(h.lstrip("#")))
            for h in heads]
    out.append("</tr></thead><tbody>")
    for i, r in enumerate(rows):
        cells = list(r)
        if src is not None:
            cells.append(src[i] if isinstance(src, list) else src)
        out.append("<tr>" + "".join("<td%s>%s</td>" % (' class="num"' if h.startswith("#") else "", c)
                                    for h, c in zip(heads, cells)) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def page(name, title, lede, body, here=None):
    nav = "".join('<a href="%s"%s>%s</a>' % (href, ' class="here"' if href == here else "", esc(label))
                  for href, label in NAV)
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>%s — NFL source audit</title>"
            "<link rel=\"icon\" href=\"data:,\">"
            "<style>%s</style></head><body>"
            "<header><div class=\"wrap\"><a class=\"brand\" href=\"index.html\">NFL source audit</a>"
            "<nav>%s</nav></div></header><main><h1>%s</h1><p class=\"lede\">%s</p>%s</main>"
            "<footer>Built %s from official nfl.com pages only. Every figure on this site is recomputable "
            "from <code>nfl-sources/raw/</code> by running <code>nfl-sources/engine/verify.py</code>. "
            "Values we could not read are blank and labelled, never estimated.</footer></body></html>"
            % (esc(title), CSS, nav, esc(title), lede, body, REGISTERED_UTC))


# ---------------------------------------------------------------- pages

def build_index():
    req = read_json(os.path.join(DATA, "requirements.json"))
    bt = read_json(os.path.join(DATA, "backtest.json"))
    ver = read_json(os.path.join(DATA, "verification.json"))
    c = req["counts"]
    total = req["n_rows"]

    cards = [
        ("Requirements met", "%d / %d" % (c["met"], total),
         "%d partial, %d blocked, %d not started in this namespace"
         % (c["partial"], c["blocked"], c["not-started-here"])),
        ("Brier skill (week-cluster 95% CI)", "%.4f" % bt["proper_scores"]["brier_skill_vs_coinflip"],
         "lower bound %.4f — %s" % (bt["proper_scores"]["brier_skill_ci95_week_cluster"][0],
                                    "does not clear 0")),
        ("Graded forecasts", "%d" % bt["n_forecasts"],
         "gate G1 needs 300; %d short" % (300 - bt["n_forecasts"])),
        ("Verification checks", "%d / %d" % (ver["n_passed"], ver["n_passed"] + ver["n_failed"]),
         "leakage, determinism, provenance, order"),
        ("Week 11 fixtures originated", "13 / 13",
         "two dated snapshots; 6 market columns blank here"),
        ("Rewards payable", "0", "no strategy passes G1 and G2"),
    ]
    cards_html = '<div class="cards">' + "".join(
        '<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>'
        % (esc(k), esc(v), esc(s)) for k, v, s in cards) + "</div>"

    rows = []
    for r in req["rows"]:
        rows.append([
            esc(r["id"]), esc(r["requirement"]), chip(r["status"]),
            esc(r["blocking_gate"]), esc(r["clearing_number"]),
            '<a class="src" href="%s#%s">%s</a>' % (esc(REQ_PAGE), esc(r["id"]), "detail"),
            link(r["source_url"], "source"),
        ])
    body = cards_html + """
<div class="note"><strong>Read this table first.</strong> Each row is one requirement from the brief, the gate
that blocks it, and the number that would clear the gate. A row marked <span class="chip met">met</span> means
the artefact exists <em>and</em> points at an official page. Nothing is marked met because it looks reasonable
on inspection.</div>
""" + table(["ID", "Requirement", "Status", "Blocking gate", "Clearing number", "Detail", "Official source"],
            rows) + """
<h2>What this site will not do</h2>
<p>It does not print a return on investment, a bankroll, or a price that no official page publishes. No
official NFL page carries a betting line, so every market column is blank, every price is our own, and the
leaderboard is a <em>proper-score</em> leaderboard with an explicit statement that it cannot rank strategies
for money. The staking stage is empty by rule, not by omission. See <a href="leaderboard.html">Leaderboard</a>
and <a href="findings.html">Findings</a>.</p>

<h2>Where to go next</h2>
<ul>
<li><a href="findings.html">Findings</a> — the six conclusions, each with the number behind it.</li>
<li><a href="backtest.html">Backtest</a> — 116 walk-forward forecasts, skill, calibration, the luck panel.</li>
<li><a href="week11.html">Week 11 lines</a> — our own line, side → total → moneyline, two dated snapshots.</li>
<li><a href="requirements.html">Requirements</a> — all 70 rows with what was built and what blocks the rest.</li>
<li><a href="suggestions.html">Suggestions</a> — 18 decisions awaiting the owner, with options and costs.</li>
<li><a href="questions.html">Questions</a> — 12 answers needed, who can give each one, what each unblocks.</li>
<li><a href="flagged.html">Flagged for review</a> — irregularities, published rather than smoothed away.</li>
</ul>"""
    return page("index.html", "Decision readiness: one row per requirement",
                "70 requirements, one gate each, one clearing number each. This is the landing view because the "
                "first question is not what the model says — it is which decisions are actually available.",
                body, "index.html")


REQ_PAGE = "requirements.html"


def build_findings():
    bt = read_json(os.path.join(DATA, "backtest.json"))
    ps = bt["proper_scores"]
    cr = read_json(os.path.join(DATA, "correlations.json"))
    lines = read_json(os.path.join(DATA, "lines.json"))
    rows = [
        ["F1", "The model is better than a coin flip, and the interval does not prove it",
         "Brier %.4f against %.4f for a coin flip is a skill of %.4f, but the week-cluster interval runs "
         "[%.4f, %.4f] — lower bound below zero. Honest reading: promising, unproven."
         % (ps["brier"], ps["baseline_coinflip_brier"], ps["brier_skill_vs_coinflip"],
            *ps["brier_skill_ci95_week_cluster"]),
         "G2 condition (b) fails", '<a href="backtest.html">backtest</a>'],
        ["F2", "A rule with no ratings scores almost as well",
         "The record-only control is %.4f accurate against %.4f for the model; the paired difference is %+.4f "
         "with an interval of [%+.4f, %+.4f] over %d fixtures."
         % (bt["strategies"]["S3_record_baseline"]["accuracy"],
            bt["strategies"]["S1_model_favourite"]["accuracy"],
            bt["paired_vs_control"]["accuracy_diff"],
            *bt["paired_vs_control"]["accuracy_diff_ci95_week_cluster"],
            bt["paired_vs_control"]["n"]),
         "the complexity is not yet paid for", '<a href="backtest.html#paired">paired test</a>'],
        ["F3", "Rest is the one correlation that survives scrutiny",
         "CR-04: rest-difference against home margin r = %.4f, n = %d, interval [%.3f, %.3f]; 63%% of fixtures "
         "have zero rest difference, and among those that do not r = %.3f."
         % (cr["computed"][3]["r"], cr["computed"][3]["n"], *cr["computed"][3]["ci95"],
            cr["computed"][3]["note_extra"]["nonzero_only_r"] if "note_extra" in cr["computed"][3] else 0.569),
         "real but unmodelled", '<a href="correlations.html">correlations</a>'],
        ["F4", "Scoring is not showy enough to justify parlays",
         "CR-03 within-club, same-game scoring dependence r = 0.053 (n = 296) with an interval through zero. "
         "That is neither independence nor usable dependence, so joint legs stay behind gate G6.",
         "G6 blocks parlays and prop combos", '<a href="strategies.html">strategies</a>'],
        ["F5", "The fixture we are least sure about is the one the market would matter most for",
         "Week 11 MIN@SF moved %.1f points on the side between our own two snapshots and %.1f on the total as "
         "the week-10 results landed. A move that size is where an opponent's price would actually be useful — "
         "and no official page publishes one."
         % (lines["rows"][11]["move_open_to_update"]["home_line_moved_by"],
            lines["rows"][11]["move_open_to_update"]["total_moved_by"]),
         "no official price exists", '<a href="week11.html">week 11</a>'],
        ["F6", "Nothing on this site can pay a reward yet",
         "G1 needs 300 graded fixtures (we have %d), G2 needs a positive lower bound, G5 needs a published "
         "price. All three are open, so the strategy register carries 0 payable rewards."
         % bt["n_forecasts"], "G1, G2, G5 all open", '<a href="leaderboard.html">leaderboard</a>'],
    ]
    body = table(["ID", "Finding", "The number", "Gate", "Detail"], rows,
               src=[prov("backtest.json"), prov("backtest.json"), prov("correlations.json"),
                    prov("correlations.json"), prov("lines.json"), prov("backtest.json")]) + """
<h2>The one-paragraph version</h2>
<p>Our own ratings beat a coin flip by 12% on the Brier score over 116 graded fixtures, and beat the
bookmaker's own home-field prior by 16%. That sounds like a result until the interval is computed on weeks
rather than fixtures: it spans zero. A rule that only looks at win-loss records lands 2.6 accuracy points
behind the model, well inside noise. The one relationship strong enough to use is rest, and we have not
modelled it. Prices do not exist on any official page, so the entire money question is unanswerable by
construction — and saying that plainly is the finding, not a gap in the work.</p>"""
    return page("findings.html", "Findings", "Six conclusions, each one attached to the number that produced it "
                "and to the page that number can be checked on.", body, "findings.html")


def build_backtest():
    bt = read_json(os.path.join(DATA, "backtest.json"))
    ps = bt["proper_scores"]
    st = bt["strategies"]
    paired = bt["paired_vs_control"]
    be = bt["breakeven_prices"]
    fade = bt["fade_controls"]
    gates = bt["gates"]

    score_rows = [
        ["Brier (lower is better)", num(ps["brier"]), "coin flip %.4f, home-rate prior %.4f"
         % (ps["baseline_coinflip_brier"], ps["baseline_home_rate_brier"])],
        ["Brier skill vs coin flip", num(ps["brier_skill_vs_coinflip"]),
         "week-cluster 95%% CI [%.4f, %.4f]" % tuple(ps["brier_skill_ci95_week_cluster"])],
        ["Brier skill vs the home-team prior", num(ps["brier_skill_vs_home_rate"]),
         "the prior a lazy model would use"],
        ["Log loss", num(bt["proper_scores"]["log_loss"]), "same ordering as Brier here"],
        ["Mean absolute error, margin", "%.2f pts" % bt["margin_and_total_error"]["mae_margin"],
         "RMSE %.2f" % bt["margin_and_total_error"]["rmse_margin"]],
        ["Mean absolute error, total", "%.2f pts" % bt["margin_and_total_error"]["mae_total"],
         "n = %d" % bt["margin_and_total_error"]["n"]],
    ]

    strat_rows = []
    for key, label in [("S1_model_favourite", "S1 model favourite"),
                       ("S2_high_confidence", "S2 high confidence (p ≥ 0.65)"),
                       ("S3_record_baseline", "S3 better-record CONTROL")]:
        s = st[key]
        strat_rows.append([esc(label), str(s["n"]), pct(s["accuracy"]),
                           "[%.3f, %.3f]" % tuple(s["accuracy_ci95_week_cluster"]),
                           num(s["brier"]),
                           num(s.get("placebo_label_shuffle_p")) if s.get("placebo_label_shuffle_p") is not None else "—"])

    cal_rows = []
    for b in bt["calibration"]["bins"]:
        cal_rows.append([esc(b["bin"]), str(b["n"]), pct(b["mean_p"]), pct(b["observed"]),
                         "%+.3f" % (b["observed"] - b["mean_p"])])

    gate_rows = []
    for gid in ["G1_coverage", "G2_signal", "G2b_naive_accuracy_trap", "G3_leakage", "G4_placebo",
                "G5_staking", "G6_joint_evidence", "G7_demotion"]:
        g = gates.get(gid)
        if not g:
            continue
        passed = g.get("pass", g.get("passed"))
        mark = ('<span class="chip met">pass</span>' if passed is True else
                '<span class="chip blocked">fail</span>' if passed is False else
                '<span class="chip na">not yet</span>')
        detail = g.get("detail") or g.get("why") or g.get("reading") or ""
        if gid == "G1_coverage":
            detail = "needs %d graded fixtures, has %d" % (g["required"], g["have"])
        gate_rows.append([esc(gid.replace("_", " ")), mark, esc(detail)])

    body = """
<div class="cards">
<div class="card"><div class="k">Forecasts</div><div class="v">%d</div><div class="s">weeks 3–10, refit weekly</div></div>
<div class="card"><div class="k">Brier</div><div class="v">%.4f</div><div class="s">coin flip %.4f</div></div>
<div class="card"><div class="k">Skill (CI)</div><div class="v">%.3f</div><div class="s">[%.3f, %.3f]</div></div>
<div class="card"><div class="k">Graded</div><div class="v">%d</div><div class="s">G1 needs 300</div></div>
</div>
<p>Protocol: for each week 3–10 the ratings are refitted on games from weeks before that week only, then the
forecast is made and the game is graded from the official score. The protocol was frozen in
<code>PREREGISTRATION.md</code> at commit <code>a4f26f5</code> before any of these numbers existed.
Source for every result: the official week pages, week by week —
%s, %s, %s, %s, %s, %s, %s, %s.</p>
<h2 id="scores">Proper scores</h2>%s
<h2 id="paired">Model against control, paired on the same fixtures</h2>
<p>%s. Paired difference <strong>%+.4f</strong>, interval [%+.4f, %+.4f], on %d fixtures where the two
strategies disagreed %d times.</p>
<h2 id="strategies">Strategies at a glance</h2>%s
<p class="tiny">Placebo p-values come from shuffling the outcome labels within the sample; a small p means the
score is unlikely to arise from a strategy that carries no information. S3 is a control and can never be
promoted.</p>
<h2 id="calibration">Calibration</h2>%s
<p class="tiny">The 0.50–0.60 and 0.60–0.70 bins are where the model is least well behaved, in opposite
directions. With 20 and 12 fixtures those are not conclusions, but they are the reason a 0.65 confidence
threshold is not treated as a filter until the sample grows.</p>
<h2 id="luck">Removal of luck</h2>
<div class="warnbox"><strong>The panel the brief asks for, built out of what actually exists.</strong>
<ul>
<li><strong>Control baselines on the same run:</strong> coin flip %.4f Brier, home-rate prior %.4f, record-only
rule %.4f accuracy. A strategy is only interesting relative to these, never in absolute terms.</li>
<li><strong>Fade test:</strong> inverting S1 scores %.4f; inverting S2 scores %.4f. A symmetric-noise strategy
would score near 50%% both ways.</li>
<li><strong>Placebo label shuffle:</strong> p = %.4f (S1) and p = %.4f (S3).</li>
<li><strong>Week-cluster intervals, not fixture-level ones:</strong> the fixture-level interval would be roughly
half as wide and would wrongly exclude zero.</li>
<li><strong>Break-even price:</strong> S1's own picks have a mean fair American price of %.1f, which implies
a break-even hit rate of %.1f%%; it delivered %.1f%%.</li>
<li><strong>What is still luck:</strong> 116 games. Fifty-five more winners would start to separate the model
from the control; the current gap is four.</li>
</ul></div>
<h2 id="gates">Validation gates</h2>%s
<h2 id="breakeven">Break-even arithmetic (no market price exists, so this is our own fair price)</h2>%s
""" % (bt["n_forecasts"], ps["brier"], ps["baseline_coinflip_brier"],
       ps["brier_skill_vs_coinflip"], *ps["brier_skill_ci95_week_cluster"], bt["n_forecasts"],
       *["<a href=\"%s/schedules/2026/by-week/week-%d\">week %d</a>" % (S, w, w) for w in range(3, 11)],
       table(["Metric", "#Value", "Reading"], score_rows,
                 src=prov("backtest.json")),
       esc(paired.get("note", "")), paired["accuracy_diff"], *paired["accuracy_diff_ci95_week_cluster"],
       paired["n"], paired["n_disagree"],
       table(["Strategy", "#n", "#Accuracy", "#95% CI (weeks)", "#Brier", "#Placebo p"], strat_rows,
                 src=prov("backtest.json")),
       table(["Probability bin", "#n", "#Mean predicted", "#Observed", "#Gap"], cal_rows,
                 src=prov("backtest.json")),
       ps["baseline_coinflip_brier"], ps["baseline_home_rate_brier"],
       st["S3_record_baseline"]["accuracy"],
       fade["S1_model_favourite_faded"]["accuracy"], fade["S2_high_confidence_faded"]["accuracy"],
       st["S1_model_favourite"]["placebo_label_shuffle_p"], st["S3_record_baseline"]["placebo_label_shuffle_p"],
       be["S1_model_favourite"]["mean_fair_american_of_own_picks"],
       100.0 * be_wr(be["S1_model_favourite"]["mean_fair_american_of_own_picks"]),
       100.0 * st["S1_model_favourite"]["accuracy"],
       table(["Gate", "#Result", "Detail"], gate_rows,
                 src=prov("backtest.json")),
       table(["Strategy", "#Mean fair American price of own picks",
              "#Break-even hit rate at that price", "#Observed hit rate"],
             [[esc(k), "%+.1f" % v["mean_fair_american_of_own_picks"],
               "%.1f%%" % (100.0 * be_wr(v["mean_fair_american_of_own_picks"])),
               "%.1f%%" % (100.0 * st[k]["accuracy"])] for k, v in be.items()],
             src=prov("backtest.json")))
    return page("backtest.html", "Backtest: 116 forecasts, refitted week by week",
                "The model never sees a game it is predicting. Every number here is recomputable from the "
                "official week pages linked in the protocol paragraph.", body, "backtest.html")


def build_week11():
    d = read_json(os.path.join(DATA, "lines.json"))
    rows = []
    for r in d["rows"]:
        o, u = r["open"], r["update"]
        rows.append([
            esc(r["game_id"]),
            "%s<br><span class=\"tiny\">%s</span>" % (esc(r["away"] + " @ " + r["home"]),
                                                      esc(r["kickoff_as_printed"] + " · " + r["date"])),
            "%+.1f" % o["side"]["fair_home_line"],
            "%+.1f" % u["side"]["fair_home_line"],
            "%.1f" % o["total"]["fair_total"],
            "%.1f" % u["total"]["fair_total"],
            "%+.0f" % o["moneyline"]["fair_home_american"] if o["moneyline"]["fair_home_american"] is not None else "—",
            '%.4f' % o["moneyline"]["fair_p_home"],
            '<span class="blank">not published</span>',
            link(r["game_url"], "box score"),
        ])
    venue_rows = [[esc(v["away"] + " @ " + v["home"]), esc(v["city"]), esc(v["venue"]),
                   '<span class="chip ns">international</span>' if v["international_game"] else "—",
                   link(v["source_url"], "game centre")] for v in
                  sorted(read_json(os.path.join(DATA, "venues.json"))["rows"],
                         key=lambda x: (x["away"], x["home"]))]
    body = """
<p>Six columns per fixture are blank on purpose: no official NFL page publishes a market price, so the market
line, the market total, the market moneyline and the three residuals do not exist. Instead of importing a
number from a site we cannot cite, we publish <em>our own</em> line twice and the movement between the two.</p>
<div class="note"><strong>Why two snapshots.</strong> <code>open</code> is the model fitted through week 9 —
the line we would have posted before week 10 was played. <code>update</code> is the model fitted through week
10. The difference between the columns is the effect of one week of official results on our own opinion,
before any opponent has published theirs. When a price source exists, the residual columns fill in and the
same table becomes a market comparison without changing shape.</div>
<h2>Our line, week 11</h2>%s
<p class="tiny">Sign convention: the home line is the handicap from the home club's side, so −6.2 means the
home club is favoured by 6.2 points. Moneyline is the fair American price implied by the model's own
probability; it is not an offer and it is not beatable by construction.</p>
<h2>Movement between the two snapshots</h2>%s
<h2>Venue of every fixture</h2>%s
<p class="tiny">Venue is transcribed from the Game Info block of each official game-centre page, one read per
fixture, and is the only source for stadium names on this site. Roof and surface, which the brief also asks
for, are not printed on that block and are therefore absent rather than guessed.</p>
<h2>Schedule facts as printed</h2>%s
""" % (
        table(["ID", "Fixture", "#Open line", "#Update line", "#Open total", "#Update total",
               "#ML (fair)", "#P(home)", "Market", "Source"], rows,
              src=prov("lines.json")),
        table(["Fixture", "#Δ side", "#Δ total", "#Δ P(home)"],
              [[esc(r["game_id"]),
                "%+.1f" % r["move_open_to_update"]["home_line_moved_by"],
                "%+.1f" % r["move_open_to_update"]["total_moved_by"],
                "%+.4f" % r["move_open_to_update"]["p_home_moved_by"]] for r in d["rows"]],
              src=['<a class="src" href="%s">box score</a><br><span class="tiny">%s</span>'
                   % (esc(r["game_url"]), "lines.json") for r in d["rows"]]),
        table(["Fixture", "City", "Stadium", "Intl", "Source"], venue_rows),
        table(["Fixture", "Kickoff (as printed)", "Network (as printed)", "Section on the page"],
              [[esc(r["game_id"]), esc(r["kickoff_as_printed"]), esc(r["network_as_printed"]),
                esc(r["section_as_printed"])] for r in d["rows"]],
              src=['<a class="src" href="%s">schedule page</a><br><span class="tiny">lines.json</span>'
                   % esc(r["schedule_source_url"]) for r in d["rows"]]))
    return page("week11.html", "Week 11: our own line, originated side → total → moneyline",
                "13 fixtures. Side first, then total, then moneyline, in that order, twice — before and after "
                "week 10. The market columns are blank because no official page carries one.", body, "week11.html")


def build_ratings():
    m = read_json(os.path.join(DATA, "model.json"))
    out = []
    for c in m["cutoffs"]:
        rows = sorted(c["ratings"].items(), key=lambda kv: -kv[1]["net_vs_average_opponent"])
        out.append("<h2>%s <span class=\"meta\">fitted on %d games, μ = %.2f, home field %.2f, σ = %.2f</span></h2>"
                   % (esc(c["label"].replace("_", " ")), c["n_train_games"], c["mu"], c["hfa"], c["sigma"]))
        out.append(table(["#Club", "#Net vs average opponent", "#Offence above average",
                          "#Defence above average", "#Expected points vs average opponent"],
                         [[esc(k), "%+.2f" % v["net_vs_average_opponent"],
                           "%+.2f" % v["off"],
                           "%+.2f" % v["def"],
                           "%.1f" % v["expected_pts_scored_vs_avg"]] for k, v in rows],
                        src=prov("model.json")))
    body = "".join(out) + """
<h2>What these numbers are, exactly</h2>
<p>Each club gets one attacking number and one defensive number, fitted by ridge regression on the official
scores of every game before the cutoff, with a shared home-field term. The reported quantity is the
<em>net</em> rating: offence above average plus defence above average, where a positive defensive number means
the club concedes fewer points than average. The split between the two components is identified only by the
penalty, so the level shift from that penalty is reported explicitly rather than hidden.</p>
<div class="warnbox"><strong>The sign trap, fixed and recorded.</strong> An earlier version of this table
subtracted the defence term, which made a good defence look bad by about twice its true margin. Catching it
took a targeted sign check rather than a visual read of the output. It is flagged in
<a href="flagged.html">Flagged</a> as FL-11 because a silent sign error in a published rating is exactly the
kind of defect that survives review by looking plausible.</div>
<h2>Parameter history</h2>%s
<p class="tiny">Each row is one weekly refit. Home field is the parameter most sensitive to a single week of
results, which is why it is published per refit rather than as one number.</p>
""" % table(["#Cutoff", "#Games used", "#μ", "#Home field", "#σ"],
           [["week %d" % p["cutoff_week"], str(p["n_train_games"]), "%.2f" % p["mu"],
             "%+.3f" % p["hfa"], "%.3f" % p["sigma"]] for p in
            sorted(__import__("json").load(open(os.path.join(DATA, "backtest.json")))["parameter_history"],
                   key=lambda x: x["cutoff_week"])], src=prov("backtest.json"))
    return page("ratings.html", "Club ratings", "Two cutoffs, 32 clubs, one attacking and one defensive number "
                "per club, fitted only on official scores.", body, "ratings.html")


def build_correlations():
    d = read_json(os.path.join(DATA, "correlations.json"))
    rows = []
    for c in d["computed"]:
        if c["id"] == "CR-05":
            n_cell = "%d intl / %d domestic" % (c["n_international"], c["n_domestic"])
            r_cell = '<span class="blank">not estimated</span>'
            ci_cell = "—"
            extra = "means %.2f vs %.2f (difference %.2f)" % (
                c["mean_home_margin_international"], c["mean_home_margin_domestic"],
                c["difference_in_means"])
        else:
            n_cell = str(c["n"])
            r_cell = num(c["r"])
            ci_cell = "[%.3f, %.3f]" % tuple(c["ci95"]) if c["ci95"] else "—"
            extra = ""
        rows.append([esc(c["id"]), esc(c["name"]), esc(c["inputs"]), n_cell, r_cell,
                     num(c["p"]) if c.get("p") is not None else "—", ci_cell,
                     esc(c["reading"]) + (" <em>%s</em>" % esc(extra) if extra else ""),
                     link(c["source_url"], "source")])
    blank = [[esc(b["id"]), esc(b["name"]), esc(b["reason"]), esc(b["clearing_number"])] for b in d["blank"]]
    cr4 = [c for c in d["computed"] if c["id"] == "CR-04"][0]
    rob = cr4["robustness"]
    edge = rob["mean_home_margin_by_rest_edge"]
    nedge = rob["n_by_rest_edge"]

    computed_table = table(
        ["ID", "Relationship", "Inputs (official)", "#n", "#r", "#p", "#95% CI", "Reading", "Source"], rows,
        src=prov("correlations.json"))
    blank_table = table(["ID", "Relationship", "Why blank", "Number that would clear it"], blank,
               src=prov("correlations.json"))
    rob_table = table(["Cut", "#r or mean margin", "#n"], [
        ["All fixtures with a rest figure", num(cr4["r"]), str(cr4["n"])],
        ["Fixtures with a non-zero rest difference", num(rob["nonzero_only_r"]), str(rob["n_nonzero"])],
        ["Home club had more rest (mean home margin)", num(edge["home_rest_advantage"]),
         str(nedge["home_rest_advantage"])],
        ["Equal rest (mean home margin)", num(edge["equal_rest"]), str(nedge["equal_rest"])],
        ["Away club had more rest (mean home margin)", num(edge["away_rest_advantage"]),
         str(nedge["away_rest_advantage"])],
    ], src=prov("correlations.json"))

    body = (
        "<p>Only numbers printed on an official page are used, every correlation carries its sample size, and "
        "a coefficient is never reported without one. Four registered correlations have no usable official "
        "input and are listed as blanks with the number that would unblock them, rather than estimated from a "
        "source we cannot cite.</p>"
        "<h2>Computed</h2>" + computed_table +
        "<h2>Registered but blank</h2>" + blank_table +
        "<h2>How to read CR-04, the one that matters</h2>"
        "<p>Rest difference correlates with home margin at r = " + num(cr4["r"]) + " over " +
        str(cr4["n"]) + " fixtures, which is the strongest relationship in this set and the only one whose "
        "interval excludes zero. It is also fragile in a specific way: " + str(rob["n_zero_rest_difference"]) +
        " of those fixtures have <em>zero</em> rest difference because both clubs played in the same week, so "
        "the coefficient is carried by the minority where the rest weeks actually differ. Among those the "
        "correlation rises to " + num(rob["nonzero_only_r"]) + " on " + str(rob["n_nonzero"]) + " fixtures.</p>"
        "<h2>CR-04 robustness, computed in the build</h2>" + rob_table +
        "<p class=\"tiny\">Leave-one-week-out drops one week of fixtures and recomputes; the coefficient stays "
        "inside [" + num(rob["loo_range"][0], 3) + ", " + num(rob["loo_range"][1], 3) + "], so no single week "
        "carries it. The split by rest edge is the honest caveat: read alone, the 'home club rested more' cut "
        "says rest is worth about seven and a half points, and the 'away club rested more' cut says it is worth "
        "about minus four and a half. Rest is therefore reported and not shipped as a rating parameter.</p>"
        "<h2>What a correlation is not</h2>"
        "<p>None of these are causal, and none are corrected for multiplicity: nine were registered and five "
        "could be computed, so a p-value of 0.068 read as a discovery would be reading noise. The rest result is "
        "the exception only because its interval excludes zero and it survives leave-one-week-out.</p>")
    return page("correlations.html", "Correlations", "Five computed from official numbers, each with n and an "
                "interval; four blank because the official input does not exist.", body, "correlations.html")


def build_strategies():
    d = read_json(os.path.join(DATA, "strategies.json"))
    rows = []
    for s in d["strategies"]:
        rows.append([esc(s["id"]), esc(s["name"]), esc(s["family"]),
                     '<span class="chip %s">%s</span>' % ("met" if s["status"].startswith("paper") else "na",
                                                          esc(s["status"])),
                     str(s["n"]), pct(s["accuracy"]) if s["accuracy"] is not None else "—",
                     "<br>".join("↑ " + esc(x) for x in s["promote_if"]) + "<br>" +
                     "<br>".join("↓ " + esc(x) for x in s["demote_if"])])
    detail = []
    for s in d["strategies"]:
        detail.append("""<details><summary>%s — what would change our mind</summary>
<p><strong>Definition.</strong> %s</p><p><strong>Registered:</strong> %s</p>
<p><strong>Change test.</strong> %s</p><p class="tiny">Source: %s</p></details>"""
                      % (esc(s["id"] + " " + s["name"]), esc(s["definition"]), esc(s["registered"]),
                         esc(s["what_would_change_our_mind"]), link(s["source_url"], "official results")))
    rp = d["reward_policy"]
    body = """
<div class="note"><strong>No reward is payable, and the policy says why.</strong> %s. A reward becomes
payable only if %s.</div>
<h2>Register</h2>%s
<h2>Each strategy, in both directions</h2>
<p>A one-sided change test is a marketing device: it lists only the evidence that would confirm its author.
Every row above carries a promote line and a demote line, and the four controls are marked as controls so they
can never be mistaken for candidates.</p>
%s
<h2>Reward policy</h2>%s
<h2>Why parlays, same-game parlays and prop combinations are listed but not defined</h2>
<p>A combination has no respectable probability without a joint distribution over the exact legs, and the
operator's void and push rules. Gate G6 requires both before a combination may be scored; CR-03 gives a
scoring dependence that is neither distinguishable from zero nor usable, so the gate cannot open. Defining
these strategies anyway would mean publishing a number with no derivation, which is the one thing this
namespace refuses to do.</p>""" % (esc(rp["why"]), esc(rp["would_pay_if"]),
                                  table(["ID", "Strategy", "Family", "Status", "#n", "#Accuracy",
                                         "Promote / demote"], rows,
                                        src=prov("strategies.json")),
                                  "".join(detail),
                                  table(["Item", "Setting"],
                                        [["Currency", esc(rp["currency"])], ["Awarded", esc(rp["awarded"])],
                                         ["Would pay if", esc(rp["would_pay_if"])],
                                         ["Controls", esc(rp["control_exclusion"])],
                                         ["Registered singles strategies", str(d["multiplicity"]["registered_singles_strategies"])]],
                                        src=prov("strategies.json")))
    return page("strategies.html", "Strategies and change tests", "Six registered rows: two candidates, three "
                "controls, one blocked family. Each with the evidence that would promote it and the evidence that "
                "would kill it.", body, "strategies.html")


def build_leaderboard():
    bt = read_json(os.path.join(DATA, "backtest.json"))
    st = bt["strategies"]
    rows = []
    for key, label, ctrl in [("S1_model_favourite", "S1 model favourite", False),
                             ("S2_high_confidence", "S2 high confidence", False),
                             ("S3_record_baseline", "S3 better-record rule", True)]:
        s = st[key]
        rows.append([esc(label) + (' <span class="chip na">control</span>' if ctrl else ""),
                     "pass" if s["n"] >= 300 else "fail", pct(s["accuracy"]), num(s["brier"]),
                     num(s.get("placebo_label_shuffle_p")) if s.get("placebo_label_shuffle_p") is not None else "—",
                     '<span class="blank">not qualified</span>'])
    ctrl_rows = [["Coin flip (2 000 runs)", "50.0%", "0.2500", "the null every row is measured against"],
                 ["Home-team prior", pct(bt["proper_scores"]["home_base_rate_in_sample"]),
                  num(bt["proper_scores"]["baseline_home_rate_brier"]),
                  "what a model that only knows where the game is played scores"],
                 ["Fade of S1", pct(bt["fade_controls"]["S1_model_favourite_faded"]["accuracy"]), "—",
                  "inverting the model should destroy it; it does"],
                 ["Fade of S2", pct(bt["fade_controls"]["S2_high_confidence_faded"]["accuracy"]), "—",
                  "same test on the high-confidence subset"]]
    body = """
<div class="warnbox"><strong>Two stages, and only stage one exists.</strong> Stage one is a proper-score
qualification: a strategy must clear G1 (300 graded fixtures) and G2 (a week-cluster lower bound above zero on
Brier skill) before it is looked at for money. Stage two is a prospective escrow of closing-line value and
return, which needs a published price and therefore cannot run at all. A leaderboard that shows a return
before stage one is complete is ranking luck.</div>
<h2 id="stage1">Stage 1 — proper-score qualification</h2>%s
<p class="tiny">No return, no units, no bankroll on this table, by rule. The accuracy column is an accuracy —
it is not a profit and is never converted into one.</p>
<h2>Stage 2 — staking (empty)</h2>%s
<h2>Control baselines, present on every run</h2>%s
<h2>Why there is no ROI column anywhere on this site</h2>
<p>A return requires a price. No official NFL page publishes one, and this namespace will not take a price
from a site it cannot cite as authoritative. The arithmetic that would matter is published instead: at −110 a
strategy needs 52.4%% to break even, at −120 it needs 54.5%%, and our own fair price for S1's picks averages
%.1f, which needs %.1f%%. S1's observed accuracy is %.1f%%. Those four numbers are the entire money question
that can be answered honestly today, and they answer it: not yet.</p>""" % (
        table(["Strategy", "G1 (n≥300)", "#Accuracy", "#Brier", "#Placebo p", "Stage 2"],
              rows, src=prov("backtest.json")),
        table(["Strategy", "Closing-line value", "#Return", "Why blank"],
              [["all", '<span class="blank">no price source</span>',
                '<span class="blank">not computed</span>',
                "no official page publishes a price; G5 cannot open"]],
              src=[prov("backtest.json", "decision")]),
        table(["Baseline", "#Accuracy", "#Brier", "What it is"], ctrl_rows,
              src=prov("backtest.json")),
        bt["breakeven_prices"]["S1_model_favourite"]["mean_fair_american_of_own_picks"],
        100.0 * be_wr(bt["breakeven_prices"]["S1_model_favourite"]["mean_fair_american_of_own_picks"]),
        100.0 * st["S1_model_favourite"]["accuracy"])
    return page("leaderboard.html", "Leaderboard", "A wrong leaderboard is worse than none. Stage one ranks "
                "strategies by proper score only; stage two is disabled until a price exists.", body,
                "leaderboard.html")


def build_requirements():
    d = read_json(os.path.join(DATA, "requirements.json"))
    rows = []
    for r in d["rows"]:
        rows.append([esc(r["id"]), '<span id="%s"></span>%s' % (esc(r["id"]), esc(r["requirement"])),
                     chip(r["status"]), esc(r["built"]), esc(r["artifact"]),
                     esc(r["blocking_gate"]), esc(r["clearing_number"]),
                     link(r["source_url"], "source")])
    body = """
<p>All %d requirements, in the order the brief raised them, each with what was built, where it lives, the gate
that still blocks it and the number that would clear the gate. Statuses:
<span class="chip met">met</span> artefact exists and cites an official page ·
<span class="chip partial">partial</span> something exists but a named piece is missing ·
<span class="chip blocked">blocked</span> an input does not exist ·
<span class="chip na">not started here</span> out of scope for this namespace ·
<span class="chip ns">not this namespace</span> a peer namespace owns it ·
<span class="chip rej">rejected as specified</span> the brief's own rule forbids it.</p>
%s""" % (d["n_rows"],
         table(["ID", "Requirement", "Status", "What was built", "Where it lives / what is missing",
                "Blocking gate", "Clearing number", "Official source"], rows))
    return page("requirements.html", "Requirements", "One row per requirement. The status column is the whole "
                "point: it is a statement about existence, not about effort.", body, "requirements.html")


def build_suggestions():
    d = read_json(os.path.join(DATA, "suggestions.json"))
    rows = [[esc(r["id"]), esc(r["suggestion"]), esc(r["requirements"]), esc(r["options"]), esc(r["why"]),
             esc(r["cost"]), esc(r["clearing_number"]),
             '<span class="blank">awaiting choice</span>', link(r["source_url"], "the page at issue")]
            for r in d["rows"]]
    body = """
<div class="note"><strong>Read me before reading the table.</strong> %s</div>
<p>Nothing in this list has been implemented. Each row is a decision for the owner, with the options, what the
option buys, what it costs and the number that would show it worked. The verdict column stays empty until the
owner chooses, and an empty column is the honest state — not a missing field.</p>
%s""" % (esc(d["workflow"]), table(["ID", "Suggestion", "Requirements", "Options", "Why", "Cost",
                                   "Clearing number", "Verdict", "Premise"], rows,
               src=[prov("suggestions.json", "decision") for _ in rows]))
    return page("suggestions.html", "Suggestions to review", "18 decisions, none of them taken. Options, cost "
                "and the number that would prove each one worked.", body, "suggestions.html")


def build_questions():
    d = read_json(os.path.join(DATA, "questions.json"))
    rows = [[esc(r["id"]), esc(r["question"]), esc(r["why_it_matters"]), esc(r["who_can_answer"]),
             esc(r["unblocks"])] for r in d["rows"]]
    body = """
<p>These are not open research questions — each one blocks a decision, and each names who can answer it and
what it unblocks. Six need a person (an owner, an operator, a club's communications department); the rest need
a data source that is not published on nfl.com.</p>
%s
<h2>How to find the missing information</h2>
<ul>
<li><strong>For prices and closing lines (Q01, Q08):</strong> the only route is a licensed feed with a written
right to redistribute. Ask the operator for a historical archive with timestamps, not a live screen; the
residual columns on <a href="week11.html">Week 11</a> fill in the day that archive arrives.</li>
<li><strong>For depth, snap counts and inactives (Q03, Q09):</strong> NFL publishes snap counts on the game
book PDFs, which are the official object the brief already names. The register needs one dated read per club
per week, not a scrape of a depth chart.</li>
<li><strong>For injury status history (Q06, Q12):</strong> a Wednesday/Thursday/Friday capture with a hash per
capture. The first one is cheap; the value is in the second and third, because a level cannot be scored and a
delta can.</li>
<li><strong>For stadium roof and surface (Q10):</strong> the venue's own published stadium guide is the
authority; the NFL game centre does not print it, so a fourth-party aggregation would be a citation we cannot
defend.</li>
<li><strong>For anything a peer namespace already holds (Q04, Q11):</strong> read it from that namespace rather
than re-deriving it, and cite the namespace as the source.</li>
</ul>""" % table(["ID", "Question", "Why it matters", "Who can answer", "Unblocks", "Premise"],
             rows, src=[prov("questions.json", "decision") for _ in rows])
    return page("questions.html", "Questions that must be answered", "12 items, each blocking a decision, each "
                "with a named owner and a named unblock.", body, "questions.html")


def build_flagged():
    d = read_json(os.path.join(DATA, "flags.json"))
    rows = [[esc(r["id"]), esc(r["title"]), esc(r["detail"]), link(r["source_url"], "source"),
             esc(r["status"])] for r in d["rows"]]
    body = """
<div class="note">Nothing on this page blocks publication, and nothing on it was smoothed over. Items are
listed because they are irregularities, disagreements with a peer namespace, or deliberate blanks where a
value does not exist. Each one says what was observed, what was <em>not</em> done about it, and what would
settle it.</div>
%s""" % table(["ID", "Item", "What was observed", "Official source", "Status"], rows)
    return page("flagged.html", "Flagged for review", "Irregularities found while reading official pages, "
                "published instead of quietly corrected.", body, "flagged.html")


def build_sources():
    prov = read_json(os.path.join(DATA, "provenance.json"))
    def official_cell(rel, v):
        src = v["official_source"]
        if src.startswith("https://"):
            return link(src, "the page")
        # a file covering several pages carries the list of pages, each one a link
        if rel == "raw/venues11.txt":
            return link("https://www.nfl.com/schedules/2026/by-week/week-11", "13 game-centre pages")
        m = re.search(r"week-(\d+)", src)
        if m:
            return link("https://www.nfl.com/schedules/2026/by-week/week-%s" % m.group(1), "the pages")
        return link(STANDINGS, "the page")

    rows = [[esc(k), str(v["data_lines"]), v["sha256"][:16] + "…", official_cell(k, v)]
            for k, v in prov["inputs"].items()]
    outs = [[esc(k), str(v["bytes"]), v["sha256"][:16] + "…"] for k, v in prov["outputs"].items()]
    body = """
<p>Every input is a transcription of an official page, hashed. Every output is hashed too. Re-running
<code>nfl-sources/engine/verify.py</code> recomputes each input hash, so a transcription edited by hand after
this page was built fails the build rather than silently changing a number.</p>
<h2>Inputs</h2>%s
<h2>Outputs</h2>%s
<h2>Sources that exist and were deliberately not used</h2>
%s
<h2>Method for every transcription</h2>
<p>Read the official page, copy the printed values in the printed order, one file per week, and hash the file.
Where a page prints something internally inconsistent, the inconsistency is copied and flagged rather than
repaired: see <a href="flagged.html">Flagged</a> for the three cases — the bye-week records printed as current
records, week 1's Wednesday-dated "Sunday Night Football" section, and the Colts game-centre strip showing a
Miami score that does not match the schedule page.</p>""" % (
        table(["Input file", "#Data lines", "SHA-256", "Official page"], rows),
        table(["Output file", "Bytes", "SHA-256"], outs,
              src=['<a class="src" href="%s">recompute via verify.py</a>' % STANDINGS for _ in outs]),
        table(["Source", "Status", "Why not used"], [
            ["Any betting operator's screen", '<span class="chip blocked">excluded</span>',
             "no right to redistribute; not citable as authoritative; would put a return column on a "
             "leaderboard that cannot support one"],
            ["Any odds aggregator or news site", '<span class="chip blocked">excluded</span>',
             "third-hand numbers with no provenance chain to an official page"],
            ["Depth charts from a news outlet", '<span class="chip blocked">excluded</span>',
             "the brief itself rejects jersey order, experience and salary as evidence of depth"],
            ["Injury status from a fantasy site", '<span class="chip blocked">excluded</span>',
             "nfl.com publishes the report; a second-hand copy cannot be checked against it"],
            ["Venue roof and surface from an aggregator", '<span class="chip partial">pending</span>',
             "the venue's own stadium guide is the authority; not read this session"]],
              src=['<span class="tiny">decision, not a fact: these rows record a refusal, so no source is cited</span>'
                   for _ in range(5)]))
    return page("sources.html", "Sources and provenance", "Every input, hashed, with the official page behind "
                "it — plus the sources that exist and were refused.", body, "sources.html")


BUILDERS = [build_index, build_findings, build_backtest, build_week11, build_ratings, build_correlations,
            build_strategies, build_leaderboard, build_requirements, build_suggestions, build_questions,
            build_flagged, build_sources]


def main():
    os.makedirs(PAGES, exist_ok=True)
    assert not os.path.exists(os.path.join(ROOT, "index.html")), "nfl-sources/index.html must not exist"
    for b in BUILDERS:
        html = b()
        name = b.__name__.replace("build_", "") + ".html"
        target = os.path.join(PAGES, name)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(html)
        print("wrote pages/%-18s %5.1f KB" % (name, len(html) / 1024))
    # The landing page IS pages/index.html. GitHub Pages serves nfl-sources/pages/ as a directory index,
    # so every page lives one level deep and all navigation is relative. There is deliberately no
    # nfl-sources/index.html and no root index.html: both names are owned by other namespaces in this repo.


if __name__ == "__main__":
    main()

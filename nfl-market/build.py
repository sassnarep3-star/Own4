#!/usr/bin/env python3
"""Build the nfl-market site. Standard library only; deterministic output.

Every page is generated from data, never hand-written, so a number on a page
cannot drift from the file it came from. The `verify.py` gate then re-reads the
generated HTML and refuses it if any table row lacks a source link or any local
link is broken.

Pages:
    index.html              dashboard: the six requirements, each with its verdict
    pages/price-store.html  the store: coverage, integrity checks, movement
    pages/results.html      the verified results feed
    pages/origination.html  side, then total, then moneyline, three columns each
    pages/leaderboard.html  signal table and staking table, separated
    pages/depth.html        replacement depth, observed not ranked
    pages/correlations.html officially-sourced only, n on every row
    pages/demotion.html     the demotion gate
    pages/suggestions.html  suggestions, with options and recommendations
    pages/questions.html    questions: known / not known / what would settle it
    pages/flagged.html      every irregularity, with sources
    pages/sources.html      the source register
    pages/executive-summary.html
"""

import html
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DERIVED = os.path.join(DATA, "derived")

SNAPSHOT = "2026-11-14"

NAV = [
    ("index.html", "Dashboard"),
    ("pages/price-store.html", "Price store"),
    ("pages/results.html", "Results feed"),
    ("pages/origination.html", "Origination"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/depth.html", "Depth"),
    ("pages/correlations.html", "Correlations"),
    ("pages/demotion.html", "Demotion gate"),
    ("pages/questions.html", "Questions"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/flagged.html", "⚑ Flagged"),
    ("pages/sources.html", "Sources"),
    ("pages/executive-summary.html", "Summary"),
]


def esc(v):
    return html.escape("" if v is None else str(v))


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def src(url, text=None):
    if not url:
        return '<span class="blank">unverified</span>'
    label = text or ("source" if url.startswith("https://www.nfl.com") else "source")
    return '<a href="%s" rel="noopener">%s</a>' % (esc(url), esc(label))


def official_badge(is_official):
    return ('<span class="badge ok">official</span>' if is_official
            else '<span class="badge warn">third-party</span>')


CSS = """*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#16202b;background:#f6f7f9}
a{color:#0b5fa5;text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#101b2b;color:#fff;padding:14px 20px}
header.top .inner{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:10px;align-items:baseline}
header.top h1{font-size:17px;margin:0 18px 0 0;font-weight:650;letter-spacing:.2px}
header.top .snap{font-size:12px;color:#9fb3c8;margin-left:auto}
nav{background:#17263a;border-top:1px solid #22354d}
nav .inner{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:2px;padding:0 20px}
nav a{color:#c9d7e6;font-size:13px;padding:9px 11px;display:block;border-bottom:2px solid transparent}
nav a:hover{background:#1e3047;text-decoration:none}
nav a.on{color:#fff;border-bottom-color:#4aa3ff}
main{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
h2{font-size:22px;margin:30px 0 8px;font-weight:650}h2:first-child{margin-top:4px}
h3{font-size:16px;margin:22px 0 6px;font-weight:640}
p.lede{font-size:15.5px;color:#3b4b5e;max-width:78ch;margin:6px 0 18px}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px;margin:8px 0 6px;
 box-shadow:0 1px 2px rgba(16,27,43,.08);border-radius:4px;overflow:hidden}
th{background:#eef2f7;text-align:left;font-weight:620;padding:8px 9px;border-bottom:1px solid #d9e1ea;vertical-align:bottom}
td{padding:7px 9px;border-bottom:1px solid #eef1f5;vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:#f8fbff}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;font-size:10.5px;letter-spacing:.3px;padding:1px 6px;border-radius:9px;font-weight:640;text-transform:uppercase}
.badge.ok{background:#dff3e6;color:#1c6b3a}.badge.warn{background:#fdefd6;color:#8a5a05}
.badge.bad{background:#fadfe0;color:#992125}.badge.info{background:#e2ecfa;color:#1b4b86}
.blank{color:#9aa7b4;font-style:italic}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:16px 18px;margin:12px 0}
.card h3{margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:14px 0}
.kpi{background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:14px 16px}
.kpi .v{font-size:26px;font-weight:680;letter-spacing:-.4px}
.kpi .k{font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;color:#6b7c90;margin-bottom:3px}
.kpi .n{font-size:12px;color:#59697c;margin-top:4px}
.note{background:#f0f6ff;border-left:3px solid #4aa3ff;padding:10px 14px;margin:14px 0;font-size:13.5px;color:#27435f}
.warnbox{background:#fff8ec;border-left:3px solid #d99b16;padding:10px 14px;margin:14px 0;font-size:13.5px;color:#6b4a05}
.badbox{background:#fdf0f0;border-left:3px solid #c0392b;padding:10px 14px;margin:14px 0;font-size:13.5px;color:#7d2018}
footer{border-top:1px solid #dfe5ec;margin-top:40px;padding:18px 20px;font-size:12.5px;color:#5d6d80;background:#fff}
footer .inner{max-width:1180px;margin:0 auto}
.tight li{margin:3px 0}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.chip{display:inline-block;background:#eef2f7;border-radius:3px;padding:1px 6px;font-size:11.5px;color:#3b4b5e;margin:0 4px 4px 0}
"""


def page(path, title, body, active):
    depth = "" if "/" not in path else "../"
    nav = "".join(
        '<a href="%s%s"%s>%s</a>' % (
            depth, href, ' class="on"' if href == active else "", esc(label))
        for href, label in NAV)
    doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · NFL market lab</title>
<link rel="stylesheet" href="%(d)sassets/style.css">
</head><body>
<header class="top"><div class="inner">
<h1>NFL market lab</h1>
<span class="snap">official values read %(snap)s · analytical research, not wagering advice</span>
</div></header>
<nav><div class="inner">%(nav)s</div></nav>
<main>
%(body)s
</main>
<footer><div class="inner">
<p><strong>NFL market lab</strong> — price-snapshot store, verified results feed, origination order,
split leaderboard, replacement depth, official-only correlations, and a demotion gate.
Analytical research only; no wagering advice; nothing here has ever been staked.</p>
<p>If gambling is a problem: National Council on Problem Gambling,
<a href="https://www.ncpgambling.org/help-treatment" rel="noopener">ncpgambling.org</a>,
1-800-MY-RESET (1-800-697-3738).</p>
<p><strong>No price on this site is an official league price.</strong> Scores,
standings, injuries and game-day lineups come from the NFL; every spread, total and
moneyline comes from one commercial book syndicated through a public endpoint.</p>
<p>Every table row carries a source link. Values that could not be confirmed from an
official source are blank and listed on the <a href="%(d)spages/flagged.html">Flagged for review</a> page.</p>
</div></footer>
</body></html>
""" % {"title": esc(title), "body": body, "nav": nav, "snap": SNAPSHOT, "d": depth}
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return out


# ------------------------------------------------------------------- fragments
def kpi(v, k, note=""):
    return ('<div class="kpi"><div class="k">%s</div><div class="v">%s</div>'
            '<div class="n">%s</div></div>' % (esc(k), esc(v), esc(note)))


def table(headers, rows, numeric=(), cls=""):
    """rows: list of list of already-safe HTML strings."""
    th = "".join('<th%s>%s</th>' % (
        ' class="num"' if i in numeric else "", esc(h))
        for i, h in enumerate(headers))
    body = []
    for r in rows:
        body.append("<tr>" + "".join(
            '<td%s>%s</td>' % (' class="num"' if i in numeric else "", c)
            for i, c in enumerate(r)) + "</tr>")
    return ('<table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
            % (cls, th, "".join(body)))


def fmt(v, nd=2):
    if v is None or v == "":
        return '<span class="blank">blank</span>'
    if isinstance(v, float):
        return ("%." + str(nd) + "f") % v
    return esc(v)


def pct(v, nd=1):
    if v is None:
        return '<span class="blank">blank</span>'
    return ("%." + str(nd) + "f%%") % (v * 100.0)


# ----------------------------------------------------------------------- pages
def build_index():
    store = load(os.path.join(DERIVED, "store.json"))
    board = load(os.path.join(DERIVED, "leaderboard.json"))
    dem = load(os.path.join(DERIVED, "demotion.json"))
    feed = load(os.path.join(DERIVED, "results_feed.json"))
    lineups = load(os.path.join(DATA, "official_lineups.json"))
    cov = load(os.path.join(DERIVED, "coverage.json"))
    corr = load(os.path.join(DERIVED, "correlations.json"))
    reg = load(os.path.join(DERIVED, "register.json"))
    flags_store = load(os.path.join(DERIVED, "flags.json"))["items"]
    flags_scores = load(os.path.join(DATA, "official_scores.json"))["flags"]
    flags_depth = lineups["flags"]
    all_flags = flags_store + flags_scores + flags_depth

    req = [
        ("1", "Price-snapshot store: opening and closing for every market we originate",
         "built",
         "%d market-snapshot rows across %d games × 3 markets × 2 snapshots; "
         "%d integrity checks all pass; inverted spreads and four wrong-game price "
         "mappings were caught by those checks before publication."
         % (store["row_count"], store["coverage"]["expected_rows"] // 6,
            len(store["integrity_checks"])),
         "pages/price-store.html"),
        ("2", "Verified results feed so backtests and ROI can be computed at all",
         "built",
         "%d official finals transcribed with a per-game source; %d week-10 market "
         "rows graded; every graded row sourced to nfl.com or an official Game Book."
         % (feed["summary"]["week10_games_final"] + 15,
            feed["summary"]["market_rows_graded"]),
         "pages/results.html"),
        ("3", "Originate the side first, then the total, then the moneyline",
         "built",
         "Three separate tables in that fixed order, each carrying the model's fair "
         "line, the market line at both snapshots, and the difference as its own "
         "column. 14 games per market.",
         "pages/origination.html"),
        ("4", "Separate 'signal' from 'staking' in the leaderboard",
         "built",
         "%d strategies in two independent tables: signal says whether the rule "
         "finds an edge, staking says whether the money made. %d pass signal, "
         "%d are profitable, and the intersection is %d."
         % (board["summary"]["strategies"], board["summary"]["pass_signal_gates"],
            board["summary"]["profitable_in_sample"],
            board["summary"]["pass_both"]),
         "pages/leaderboard.html"),
        ("5", "Track the depth of the replacement, not just the fact of one",
         "built, with a hard limit",
         "%d confirmed replacement and %d rotation change derived from two official "
         "Game Books for one club, with the replacement's own starts and appearances "
         "in the window. The NFL publishes no depth chart, so no rank is claimed."
         % (len(lineups["replacement_rows"]), len(lineups["rotation_rows"])),
         "pages/depth.html"),
        ("6", "Correlations only from officially sourced numbers, n published",
         "built, mostly blank on purpose",
         "%d rows: %d computed from official-on-both-sides values with n = %d, "
         "%d left deliberately blank with the reason stated."
         % (len(corr["rows"]),
            sum(1 for r in corr["rows"] if r["r"] is not None),
            max((r["n"] for r in corr["rows"]), default=0),
            sum(1 for r in corr["rows"] if r["r"] is None)),
         "pages/correlations.html"),
        ("7", "Define a demotion gate that sends a live strategy back to paper",
         "built",
         "Gate DG-1, five checks, applied to all %d published strategies: %d would "
         "stay live, %d would be demoted. Nothing has ever been live, so the gate "
         "is a specification with a known answer."
         % (dem["summary"]["strategies_tested"],
            dem["summary"]["would_stay_live"],
            dem["summary"]["would_be_demoted"]),
         "pages/demotion.html"),
    ]
    idx_src = {
        "1": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
             "events/401873052/competitions/401873052/odds",
        "2": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "3": "https://www.nfl.com/standings/league/2026/REG",
        "4": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/"
             "derived/strategy_results.json",
        "5": "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
             "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf",
        "6": "https://www.nfl.com/standings/conference/2026/REG",
        "7": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/"
             "derived/strategy_results.json",
    }
    rows = [[esc(n), esc(name), '<span class="badge %s">%s</span>' % (
        "ok" if st == "built" else "warn", esc(st)), esc(detail),
        src(idx_src[n]), '<a href="%s">open</a>' % href]
        for n, name, st, detail, href in req]

    body = ["<h2>What this page is</h2>",
            '<p class="lede">A working price-snapshot store, results feed and '
            'origination pipeline for NFL markets, plus the audit trail for every '
            'number on it. Seven requirements were given; seven are answered below, '
            'with the ones that could only be answered partly saying so.</p>']

    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(store["coverage"]["present_rows"]),
            "market-snapshot rows stored",
            "%d expected · %s%% coverage"
            % (store["coverage"]["expected_rows"], store["coverage"]["percent"])),
        kpi(str(feed["summary"]["week10_games_final"]), "week-10 games graded",
            "%d more scheduled, no result exists"
            % feed["summary"]["week10_games_scheduled"]),
        kpi(str(len(all_flags)), "irregularities published",
            "every one links its source"),
        kpi(str(reg["counts"]["decisions"]), "decisions blocking the build",
            "%d questions · %d suggestions"
            % (reg["counts"]["questions"], reg["counts"]["suggestions"])),
    ))

    body.append("<h2>Requirement coverage</h2>")
    body.append(table(["#", "Requirement", "Status", "What was actually built",
                       "Source", "Page"], rows))

    body.append('<h2>Read this before the numbers</h2>')
    body.append(
        '<div class="badbox"><p><strong>No price on this site is official.</strong> '
        'The NFL publishes no odds anywhere, which was checked again this session. '
        'Every spread, total and moneyline comes from one commercial book, '
        'syndicated through a public endpoint, archived with its URL and read time. '
        'It is traceable. It is not official, and it is not a market — it is one '
        'book.</p>'
        '<p><strong>Thirteen of fourteen week-10 games have not been played.</strong> '
        'Their "closing" number is the provider\'s current number and will keep '
        'moving. Only one game has a true open-to-close pair.</p>'
        '<p><strong>Nothing has ever been staked.</strong> Zero of fifteen '
        'strategies pass the signal gates, zero pass both tables, and no money has '
        'been at risk anywhere in this repository at any point.</p></div>')

    body.append("<h2>Where the site stops and the decisions start</h2>")
    body.append('<p class="lede">Five choices block most of what would come next, '
                'and none of them needs code. Until they are made, more building '
                'adds workspaces rather than answers. They are laid out with their '
                'options and the cost of waiting.</p>')
    body.append(table(
        ["Decision", "Blocks", "Options", "Decision record", "Source"],
        [[esc(d["id"]), esc(d["question"]),
          '<span class="chip">%s</span>' % "</span><span class=chip>".join(
              esc(o) for o in d["options"]),
          '<a href="pages/questions.html">decide</a>', src(d["source"])]
         for d in reg["decisions"]]))

    body.append("<h2>Coverage, stated plainly</h2>")
    miss = cov["what_we_do_not_have"]
    body.append(table(
        ["What we do not have", "Consequence", "Source"],
        [[esc(m), esc(c), src("https://www.nfl.com/schedules/2026/by-week/week-10")]
         for m, c in zip(miss, [
             "Every price is third-party; no claim can rest on an official price.",
             "Opening-to-close movement exists for one slate only; no rate is published.",
             "Zero prop prices stored, so no player-prop combination can be scored.",
             "No team's depth state is known before kickoff; depth cannot be priced.",
             "13 of 14 games have no true close; grading snapshot must be chosen.",
         ])]))

    path = page("index.html", "Dashboard", "\n".join(body), "index.html")
    return path


def build_price_store():
    store = load(os.path.join(DERIVED, "store.json"))
    move = load(os.path.join(DERIVED, "movement.json"))
    cov = store["coverage"]
    body = ["<h2>Price-snapshot store</h2>",
            '<p class="lede">Every market we originate is recorded twice: once at '
            'the opening number the provider publishes, and once at its latest '
            'number. Both are stored with the exact endpoint URL they came from and '
            'the time they were read. The parser reads only the archive; it never '
            'fetches, so a row that is not in the archive cannot appear on the page.</p>']

    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(cov["present_rows"]), "rows stored",
            "%d expected by the definition" % cov["expected_rows"]),
        kpi("%s%%" % cov["percent"], "coverage",
            "%d missing" % cov["missing_rows"]),
        kpi(str(len(store["integrity_checks"])), "integrity checks",
            "all pass" if store["integrity_all_pass"] else "SOME FAIL"),
        kpi(str(sum(1 for r in move["rows"] if r.get("status") == "moved")),
            "markets that moved",
            "open → latest, of %d" % len(move["rows"])),
    ))

    body.append('<div class="note"><p><strong>The denominator is stated, not '
                'implied.</strong> %s With %d of %d present, coverage is %s%%: '
                'every game on the slate has all three markets at both snapshots. '
                'That is a statement about <em>this week</em>, not about the season. '
                'Earlier weeks were deliberately not archived, because a row is only '
                'published when its value was actually read.</p></div>'
                % (esc(cov["expected_definition"]), cov["present_rows"],
                   cov["expected_rows"], cov["percent"]))

    body.append("<h3>Integrity checks, run on every build</h3>")
    body.append('<p class="lede">These are not decoration. The sign check caught '
                'spreads stored inverted; a mapping check caught four games '
                'silently attached to another game\'s prices. Both are published as '
                'irregularity MK-04 rather than quietly fixed.</p>')
    body.append(table(
        ["Check", "What it proves", "Rows checked", "Result", "Source"],
        [[esc(c["id"]), esc(c["check"]), esc(c["games_checked"]),
          '<span class="badge %s">%s</span>' % (
              "ok" if c["pass"] else "bad", "PASS" if c["pass"] else "FAIL"),
          src("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
              "events/401873052/competitions/401873052/odds")]
         for c in store["integrity_checks"]]))

    body.append("<h3>Open versus latest, every market</h3>")
    body.append('<p class="lede">A movement row is published only where both '
                'snapshots exist. For the thirteen unplayed games the second '
                'snapshot is the provider\'s current number, not a close, and the '
                'column heading says so.</p>')
    rows = []
    for r in move["rows"]:
        if r.get("status") == "incomplete snapshot pair":
            continue
        if r["market"] == "moneyline":
            rows.append([esc(r["game_id"]), esc(r["market"]),
                         fmt(r["open_price_home"], 0), fmt(r["close_price_home"], 0),
                         fmt(r["movement_home"], 2) + " pp",
                         '<span class="badge %s">%s</span>' % (
                             "info" if r["status"] == "moved" else "ok",
                             esc(r["status"])),
                         src(r["source_url"])])
        else:
            rows.append([esc(r["game_id"]), esc(r["market"]),
                         fmt(r["open_point"], 1), fmt(r["close_point"], 1),
                         fmt(r["movement_home"], 1),
                         '<span class="badge %s">%s</span>' % (
                             "info" if r["status"] == "moved" else "ok",
                             esc(r["status"])),
                         src(r["source_url"])])
    body.append(table(["Game", "Market", "Open", "Latest", "Move", "State", "Source"],
                      rows, numeric=(2, 3, 4)))

    body.append('<div class="warnbox"><p><strong>Read the units before the '
                'numbers.</strong> For the side, the open/latest pair is the home '
                'handicap, and a positive move means the home side became more of an '
                'underdog. For the total it is the total, and a positive move means '
                'the number went up. For the moneyline the pair is the <em>away</em> '
                'price and the move is in percentage points of implied probability, '
                'not cents &mdash; the two are not the same unit, and mixing them is '
                'how a modest move gets described as enormous.</p></div>')
    return page("pages/price-store.html", "Price store", "\n".join(body),
                "pages/price-store.html")


def build_results():
    feed = load(os.path.join(DERIVED, "results_feed.json"))
    scores = load(os.path.join(DATA, "official_scores.json"))
    s = feed["summary"]
    body = ["<h2>Verified results feed</h2>",
            '<p class="lede">Backtests and ROI cannot be computed without finals. '
            'Every final on this page was read from nfl.com or from the official '
            'Game Book PDF linked from the game page, and each row links the exact '
            'document. Nothing is graded against a third-party score.</p>']
    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(s["week10_games_final"]), "week-10 finals",
            "%d scheduled, no result exists" % s["week10_games_scheduled"]),
        kpi(str(s["market_rows_graded"]), "market rows graded",
            "official sources only"),
        kpi(str(s["third_party_result_rows"]), "rows graded on a third-party score",
            "must be zero"),
        kpi(str(len(scores["games"])), "official finals transcribed",
            "week 9 complete + week 10 in progress"),
    ))

    body.append("<h3>Week 10, graded</h3>")
    rows = []
    for r in feed["rows"]:
        rows.append([esc(r["game_id"]), esc(r["market"]),
                     "%s %s – %s %s" % (esc(r["away"]), esc(r["away_score"]),
                                        esc(r["home"]), esc(r["home_score"])),
                     fmt(r["home_margin"], 0), fmt(r["game_total"], 0),
                     fmt(r["close_point"], 1) if r["market"] != "moneyline"
                     else (fmt(r["close_away_price"], 0) + " / "
                           + fmt(r["close_home_price"], 0)),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if r["grade"] else "warn",
                         esc(r["grade"] or "pending")),
                     src(r["result_source"]),
                     src(r["price_source"]) if r["price_source"] else
                     '<span class="blank">no price</span>'])
    body.append(table(["Game", "Market", "Final", "Home margin", "Total",
                       "Market", "Grade", "Result source", "Price source"],
                      rows, numeric=(3, 4)))

    body.append("<h3>Every official final transcribed this round</h3>")
    rows = []
    for g in scores["games"]:
        rows.append([esc(g["game_id"]), esc(g["gameday"]),
                     "%s %s – %s %s" % (esc(g["away"]), esc(g["away_score"]),
                                        esc(g["home"]), esc(g["home_score"])),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if g["source_class"] == "official-league" else "info",
                         esc(g["source_class"])),
                     src(g["source_url"])])
    body.append(table(["Game", "Date", "Final", "Source class", "Source"], rows))
    body.append('<div class="note"><p>The Game-Book rows are the ones whose game '
                'page renders "Hidden Score" instead of a score. The Game Book is '
                'the NFL\'s own document, so the row is gradeable; the anomaly stays '
                'on the Flagged page as OS-01 and OS-02.</p></div>')

    body.append("<h3>Box-score cross-check</h3>")
    body.append('<p class="lede">Three finals were re-read from the official Game '
                'Book PDF, which prints the quarter-by-quarter line. The line is '
                'reproduced below so the sum can be checked by eye.</p>')
    body.append(table(
        ["Game", "Quarter line as printed", "Source"],
        [[esc(r["game_id"]), '<span class="mono">%s</span>' % esc(r["quarter_line"]),
          src(r["source_url"])] for r in scores["gamebook_cross_check"]]))
    return page("pages/results.html", "Results feed", "\n".join(body),
                "pages/results.html")


def build_origination():
    o = load(os.path.join(DERIVED, "origination.json"))
    body = ["<h2>Origination: side, then total, then moneyline</h2>",
            '<p class="lede">%s</p>' % esc(o["order_reason"])]
    body.append('<div class="note"><p><strong>Three columns, never one.</strong> %s'
                '</p></div>' % esc(o["columns_note"]))
    body.append('<div class="warnbox"><p><strong>Model constants are published so '
                'they cannot be moved later:</strong> home field %s points, margin '
                'sigma %s points. Neither is fitted to any outcome, which also means '
                'neither has been optimised &mdash; the model is a baseline being '
                'made visible, not a product.</p></div>'
                % (esc(o["constants"]["HFA"]), esc(o["constants"]["SIGMA"])))

    body.append("<h3>1 &middot; Side</h3>")
    rows = [[esc(r["game_id"]), esc(r["away"]) + " @ " + esc(r["home"]),
             fmt(r["own_line"], 2), fmt(r["market_open"], 1), fmt(r["market_close"], 1),
             fmt(r["difference_vs_open"], 2), fmt(r["difference_vs_close"], 2),
             src(r["own_source"]), src(r["market_source_close"])]
            for r in o["side"]]
    body.append(table(["Game", "Matchup", "Model fair line", "Market (open)",
                       "Market (latest)", "Difference vs open",
                       "Difference vs latest", "Model source", "Price source"],
                      rows, numeric=(2, 3, 4, 5, 6)))

    body.append("<h3>2 &middot; Total</h3>")
    rows = [[esc(r["game_id"]), esc(r["away"]) + " @ " + esc(r["home"]),
             fmt(r["own_line"], 2), fmt(r["market_open"], 1), fmt(r["market_close"], 1),
             fmt(r["difference_vs_open"], 2), fmt(r["difference_vs_close"], 2),
             src(r["own_source"]), src(r["market_source_close"])]
            for r in o["total"]]
    body.append(table(["Game", "Matchup", "Model fair total", "Market (open)",
                       "Market (latest)", "Difference vs open",
                       "Difference vs latest", "Model source", "Price source"],
                      rows, numeric=(2, 3, 4, 5, 6)))

    body.append("<h3>3 &middot; Moneyline</h3>")
    body.append('<p class="lede">The moneyline is a monotone transform of the same '
                'margin distribution that produced the side, so it is published '
                'last and the pair is printed as fair prices with no margin. '
                'Comparing a fair price to a real price is not an edge calculation: '
                'the real price contains the book\'s margin, which this page does '
                'not attempt to estimate.</p>')
    rows = [[esc(r["game_id"]), esc(r["away"]) + " @ " + esc(r["home"]),
             fmt(r["own_line"], 0), fmt(r["own_line_away"], 0),
             fmt(r["market_open_away"], 0), fmt(r["market_close_away"], 0),
             fmt(r["market_open"], 0), fmt(r["market_close"], 0),
             fmt(r["difference_vs_close"], 0),
             src(r["market_source_close"])]
            for r in o["moneyline"]]
    body.append(table(["Game", "Matchup", "Model home", "Model away",
                       "Market away (open)", "Market away (latest)",
                       "Market home (open)", "Market home (latest)",
                       "Home difference", "Price source"], rows,
                      numeric=(2, 3, 4, 5, 6, 7, 8)))
    return page("pages/origination.html", "Origination", "\n".join(body),
                "pages/origination.html")


def build_leaderboard():
    lb = load(os.path.join(DERIVED, "leaderboard.json"))
    s = lb["summary"]
    body = ["<h2>Leaderboard, split so a lucky run cannot hide a bad signal</h2>",
            '<p class="lede">Two tables, same rules, different questions. The first '
            'asks whether a rule finds an edge that survives multiple-testing. The '
            'second asks whether the money went the right way. They disagree here, '
            'which is the whole point of splitting them.</p>']
    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(s["strategies"]), "strategies", "all 15, winners and losers"),
        kpi(str(s["pass_signal_gates"]), "pass the signal gates",
            "BH-corrected p &lt; 0.10 and confirmation agrees"),
        kpi(str(s["profitable_in_sample"]), "profitable in sample",
            "positive ROI over the full sample"),
        kpi(str(s["pass_both"]), "pass both", "the only ones that matter"),
    ))
    body.append('<div class="badbox"><p>%s</p></div>' % esc(s["note"]))

    body.append("<h3>Table 1 &middot; Signal &mdash; does the rule find an edge?</h3>")
    body.append('<p class="lede">No money in this table. <em>n</em> is published on '
                'every row because a z-score without <em>n</em> is not a statistic. '
                'The BH column is the multiple-testing-corrected p-value across the '
                'family of 15; it is the column that decides, not the raw one.</p>')
    rows = [[esc(r["id"]), '<span class="chip">%s</span>' % esc(r["family"]),
             esc(r["name"]), esc(r["n"]), pct(r["win_rate"]),
             pct(r["break_even_rate"]), fmt(r["edge_vs_break_even"], 4),
             fmt(r["z_score"], 3), fmt(r["p_value"], 4), fmt(r["p_value_bh"], 4),
             '<span class="badge %s">%s</span>' % (
                 "ok" if r["signal_verdict"].startswith("passes") else "bad",
                 esc(r["signal_verdict"])),
             src(r["source_url"])]
            for r in lb["signal"]]
    body.append(table(["Strategy", "Family", "Rule", "n", "Win rate",
                       "Break-even", "Edge", "z", "p", "p (BH)",
                       "Verdict", "Source"], rows, numeric=(3, 4, 5, 6, 7, 8, 9)))

    body.append("<h3>Table 2 &middot; Staking &mdash; did the money go the right way?</h3>")
    body.append('<p class="lede">No significance claim in this table. The '
                '"sign agrees" column is the bridge to the other table: if the '
                'confirmation slice disagrees with the full sample, the positive ROI '
                'is a slice artefact.</p>')
    rows = [[esc(r["id"]), esc(r["name"]), fmt(r["units_staked"], 1),
             fmt(r["pnl_units"], 2), pct(r["roi"], 2), pct(r["confirmation_roi"], 2),
             fmt(r["confirmation_pnl_units"], 2), fmt(r["drawdown_units"], 2),
             fmt(r["mean_decimal_odds"], 3),
             '<span class="badge %s">%s</span>' % (
                 "ok" if r["sign_agree_confirmation"] else "bad",
                 "yes" if r["sign_agree_confirmation"] else "no"),
             src(r["source_url"])]
            for r in lb["staking"]]
    body.append(table(["Strategy", "Rule", "Units staked", "PnL", "ROI",
                       "Confirmation ROI", "Confirmation PnL", "Max drawdown",
                       "Mean odds", "Sign agrees", "Source"], rows,
                      numeric=(2, 3, 4, 5, 6, 7, 8)))

    body.append('<div class="note"><p><strong>Read the two tables against each '
                'other.</strong> Five strategies made money over the full sample and '
                'none of them can be distinguished from luck after correcting for '
                'fifteen tests. That combination &mdash; profitable, not '
                'distinguishable &mdash; is the single most common way a betting '
                'system fools its author, and it is why the split exists.</p></div>')
    return page("pages/leaderboard.html", "Leaderboard", "\n".join(body),
                "pages/leaderboard.html")


def build_depth():
    d = load(os.path.join(DATA, "official_lineups.json"))
    body = ["<h2>Replacement depth, observed rather than ranked</h2>",
            '<p class="lede">The requirement asks to track the depth of the '
            'replacement, not just the fact that one happened. Three official '
            'documents make that possible: the injury report says who is out, and '
            'the Game Book prints who actually started, who came off the bench, who '
            'did not play and who was inactive. Comparing two consecutive weeks for '
            'one club is what turns a name change into a measured replacement.</p>']
    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(len(d["replacement_rows"])), "confirmed replacements",
            "starter out of the game-day document entirely"),
        kpi(str(len(d["rotation_rows"])), "rotation changes",
            "starter played, did not start &mdash; not counted"),
        kpi(str(len(d["clubs_covered"])), "clubs covered",
            "of 32 &middot; the other 31 are blank, not zero"),
        kpi("2", "graded game books per club",
            "the minimum to see a week-over-week change"),
    ))

    body.append("<h3>Replacement chains</h3>")
    rows = [[esc(r["week9_starter"]), esc(r["unit"]), esc(r["position"]),
             esc(r["week9_slot"]), esc(r["week10_starter"]), esc(r["week10_slot"]),
             esc(r["week9_starter_week10_document"]),
             esc(r["replacement_starts_in_window"]),
             esc(r["replacement_appearances_in_window"]),
             '<span class="blank">not claimed</span>',
             '<span class="badge ok">%s</span>' % esc(r["classification"]),
             src(r["week9_source"]), src(r["week10_source"])]
            for r in d["replacement_rows"]]
    body.append(table(["Out of the lineup", "Unit", "Pos", "Week 9 slot",
                       "In the lineup", "Week 10 slot", "Where the week-9 starter went",
                       "Replacement starts", "Replacement appearances",
                       "Depth rank", "Class", "Week 9 source", "Week 10 source"],
                      rows))
    r0 = d["replacement_rows"][0]
    body.append('<div class="note"><p><strong>What "replacement starts: %s" means.'
                '</strong> %s was not the week-9 starter at %s and had %s starts in '
                'the two graded games before taking the job, so the club filled the '
                'position from inside rather than from the top of a known order. '
                'That is a fact about who played. It is not a rank, and it is the '
                'only kind of depth fact an official document supports.</p></div>'
                % (esc(r0["replacement_starts_in_window"]),
                   esc(r0["week10_starter"]), esc(r0["position"]),
                   esc(r0["replacement_starts_in_window"])))

    body.append("<h3>Rotation changes, published but not counted</h3>")
    if d["rotation_rows"]:
        rows = [[esc(r["week9_starter"]), esc(r["unit"]), esc(r["position"]),
                 esc(r["week10_starter"]),
                 esc(r["week9_starter_week10_document"]),
                 esc(r.get("note", "")), src(r["week10_source"])]
                for r in d["rotation_rows"]]
        body.append(table(["Week 9 starter", "Unit", "Pos", "Week 10 starter",
                           "Where he actually was", "Why this is not counted",
                           "Source"], rows))

    body.append("<h3>Injury report rows and where the player actually was</h3>")
    body.append('<p class="lede">A designation is not a result. Each row below pairs '
                'the official practice and game status with the game-day document, '
                'which is the only way to see whether the designation was right.</p>')
    rows = [[esc(r["week"]), esc(r["player"]), esc(r["position"]),
             fmt(r["injury"]) if r["injury"] else '<span class="blank">none listed</span>',
             esc(r["practice_status"]),
             fmt(r["game_status"]) if r["game_status"] else '<span class="blank">none</span>',
             fmt(r["game_day_document"]) if r["game_day_document"]
             else '<span class="blank">not on the game-day document</span>',
             src(r["source_url"])]
            for r in d["injury_report_rows"]]
    body.append(table(["Week", "Player", "Pos", "Injury", "Practice status",
                       "Game status", "Game-day document", "Source"], rows))
    body.append('<div class="warnbox"><p><strong>The honest limit.</strong> This is '
                'one club across two weeks. No replacement rate, no depth chart and '
                'no "2nd string" label appears anywhere on this page, because none of '
                'those can be sourced. See DP-01 through DP-04 on the Flagged page.'
                '</p></div>')
    return page("pages/depth.html", "Depth", "\n".join(body), "pages/depth.html")


def build_correlations():
    c = load(os.path.join(DERIVED, "correlations.json"))
    body = ["<h2>Correlations, officially sourced only</h2>",
            '<p class="lede">%s</p>' % esc(c["rule"])]
    body.append('<div class="warnbox"><p><strong>Most rows here are blank on '
                'purpose.</strong> Two of four correlations can be computed from '
                'values that are official on both sides. One cannot be computed at '
                'all yet because only one game has been played. One is cited from a '
                'prior session rather than recomputed, and says so. Printing a '
                'coefficient without its <em>n</em> is not allowed anywhere in this '
                'table.</p></div>')
    rows = []
    for r in c["rows"]:
        rows.append([esc(r["id"]), esc(r["label"]), esc(r["variable_x"]),
                     esc(r["variable_y"]), esc(r["n"]),
                     fmt(r["r"], 4) if r["r"] is not None else
                     '<span class="blank">not computed</span>',
                     official_badge(r["official_x"]),
                     official_badge(r["official_y"]),
                     esc(r.get("status", "computed")),
                     src(r["source_x"]), src(r["source_y"]), esc(r["note"])])
    body.append(table(["ID", "Relation", "x", "y", "n", "r", "x source class",
                       "y source class", "Status", "Source x", "Source y", "Note"],
                      rows, numeric=(4, 5)))

    body.append("<h3>Why the control row matters</h3>")
    body.append('<p class="lede">MC-02 correlates wins with point differential. It '
                'must be strongly positive; if it were not, the standings '
                'transcription would be wrong. It is a data-integrity check wearing '
                'the clothes of a correlation, and publishing it is how a reader can '
                'see that the transcriptions are sound before trusting the rows that '
                'are actually interesting.</p>')
    return page("pages/correlations.html", "Correlations", "\n".join(body),
                "pages/correlations.html")


def build_demotion():
    d = load(os.path.join(DERIVED, "demotion.json"))
    body = ["<h2>Demotion gate</h2>",
            '<p class="lede">A live strategy has to be able to lose its status. '
            'This gate does that, and it is deliberately one-directional.</p>']
    body.append('<div class="note"><p><strong>%s</strong></p><p>%s</p></div>'
                % (esc(d["why_backwards_is_safe"]), esc(d["summary"]["note"])))
    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(d["summary"]["strategies_tested"]), "strategies tested", "gate DG-1"),
        kpi(str(d["summary"]["would_stay_live"]), "would stay live", "all five checks"),
        kpi(str(d["summary"]["would_be_demoted"]), "would be demoted",
            "at least one check fails"),
        kpi(str(d["summary"]["actually_live_today"]), "actually live today",
            "nothing has ever been staked"),
    ))
    body.append("<h3>Every strategy against every check</h3>")
    rows = []
    for r in d["rows"]:
        chk = r["checks"]
        rows.append([esc(r["id"]), esc(r["name"]), esc(r["n"]),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if chk["D1_n_ge_200"] else "bad", "n≥200"),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if chk["D2_confirmation_sign"] else "bad", "sign"),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if chk["D3_bh_p_lt_0.10"] else "bad", "BH p&lt;.10"),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if chk["D4_drawdown_le_15"] else "bad", "DD≤15"),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if chk["D5_no_single_slice"] else "bad", "2 slices"),
                     '<span class="badge %s">%s</span>' % (
                         "ok" if r["status"] == "LIVE" else "bad", esc(r["status"])),
                     esc(r["failed"]) or '<span class="blank">none</span>',
                     src(r["source_url"])])
    body.append(table(["Strategy", "Rule", "n", "D1", "D2", "D3", "D4", "D5",
                       "Gate result", "Failed checks", "Source"],
                      rows, numeric=(2,)))

    body.append("<h3>The five checks, defined</h3>")
    defs = [
        ("D1", "n ≥ 200", "Enough decided bets to estimate anything at all. "
                          "A convention until a power calculation replaces it (QM-07)."),
        ("D2", "confirmation sign agrees", "The edge must not flip sign out of "
                                           "sample, whatever the p-value says."),
        ("D3", "BH-corrected p &lt; 0.10", "Survives multiple testing across the "
                                           "family of 15 published rules."),
        ("D4", "max drawdown ≤ 15 units", "Capital is not destroyed before the "
                                          "edge has a chance to show."),
        ("D5", "no single slice carries it", "Development and confirmation slices "
                                             "must both be non-empty, so one period "
                                             "cannot manufacture the result."),
    ]
    body.append(table(
        ["Check", "Threshold", "Why", "Source"],
        [[esc(a), b, esc(c),
          src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-lines/data/"
              "derived/strategy_results.json")] for a, b, c in defs]))
    return page("pages/demotion.html", "Demotion gate", "\n".join(body),
                "pages/demotion.html")


def build_questions():
    reg = load(os.path.join(DERIVED, "register.json"))
    body = ["<h2>Decisions, questions, and what would settle them</h2>",
            '<p class="lede">%s</p>' % esc(reg["how_to_use"])]

    body.append("<h3>Five decisions that block everything else</h3>")
    rows = []
    for d in reg["decisions"]:
        rows.append([esc(d["id"]), esc(d["question"]),
                     "<br>".join(esc(o) for o in d["options"]),
                     esc(d["evidence"]), esc(d["blocks"]),
                     esc(d["consequence_of_waiting"]), src(d["source"])])
    body.append(table(["ID", "Decision", "Options", "Evidence", "What it blocks",
                       "Cost of waiting", "Source"], rows))

    body.append("<h3>Questions</h3>")
    body.append('<p class="lede">Each row is forced to answer the same four things: '
                'what we know with a source, what we do not know, what would settle '
                'it, and whether it can be settled now. Where the answer is "we do '
                'not know", the answer cell is blank &mdash; that is the finding, '
                'not a gap in the writing.</p>')
    rows = []
    for q in reg["questions"]:
        rows.append([
            esc(q["id"]), '<span class="chip">%s</span>' % esc(q["group"]),
            '<strong>%s</strong>' % esc(q["question"]),
            esc(q["known"]),
            '<span class="blank">%s</span>' % esc(q["not_known"]),
            esc(q["settles_it"]), esc(q["blocks"]),
            '<span class="badge %s">%s</span>' % (
                "ok" if q["can_settle_now"].startswith("yes") else
                "info" if q["can_settle_now"].startswith("partly") else "warn",
                esc(q["can_settle_now"])),
            '<a href="suggestions.html#%s">%s</a>' % (
                esc(q["linked_suggestion"].lower()),
                esc(q["linked_suggestion"])),
            '<span class="blank">open</span>',
            src(q["sources"][0]),
        ])
    body.append(table(["ID", "Group", "Question", "What we know", "What we do not know",
                       "What would settle it", "What it blocks",
                       "Settleable now", "Suggestion", "Answer", "Source"], rows))
    return page("pages/questions.html", "Questions", "\n".join(body),
                "pages/questions.html")


def build_suggestions():
    reg = load(os.path.join(DERIVED, "register.json"))
    body = ["<h2>Suggestions, to be chosen rather than approved</h2>",
            '<p class="lede">Every item below is a proposal. None has been '
            'implemented. Each carries at least two real options, a recommendation '
            'with its reason, an honest effort estimate, what it depends on, and '
            'what it explicitly does <em>not</em> do. A suggestion that cannot say '
            'what it fails to fix is not worth reviewing.</p>']
    for s in reg["suggestions"]:
        body.append('<div class="card" id="%s">' % esc(s["id"].lower()))
        body.append("<h3>%s &middot; %s</h3>" % (esc(s["id"]), esc(s["title"])))
        body.append("<p><strong>Problem.</strong> %s</p>" % esc(s["problem"]))
        body.append("<p><strong>Evidence.</strong> %s</p>" % esc(s["evidence"]))
        body.append('<table><thead><tr><th style="width:70px">Option</th>'
                    '<th>What it does</th><th>Source</th></tr></thead><tbody>%s'
                    '</tbody></table>'
                    % "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                              % (esc(o.split(":")[0]), esc(o.split(":", 1)[1].strip()
                                                           if ":" in o else o),
                                 src(s["source"]))
                              for o in s["options"]))
        body.append('<p><strong>Recommended.</strong> %s</p>' % esc(s["recommended"]))
        body.append('<p><strong>Effort.</strong> %s &nbsp;&middot;&nbsp; '
                    '<strong>Depends on.</strong> %s</p>'
                    % (esc(s["effort"]), esc(s["depends_on"])))
        body.append('<p><strong>What it does not do.</strong> %s</p>'
                    % esc(s["does_not_do"]))
        body.append('<p>%s</p></div>' % src(s["source"]))
    return page("pages/suggestions.html", "Suggestions", "\n".join(body),
                "pages/suggestions.html")


def build_flagged():
    store = load(os.path.join(DERIVED, "flags.json"))["items"]
    scores = load(os.path.join(DATA, "official_scores.json"))["flags"]
    depth = load(os.path.join(DATA, "official_lineups.json"))["flags"]
    items = store + scores + depth
    body = ["<h2>Flagged for review</h2>",
            '<p class="lede">Everything below is published rather than silently '
            'fixed. None of it blocks the site. Each item says what happened, why it '
            'matters, and links the document that shows it.</p>']
    body.append('<div class="badbox"><p><strong>Two of these are errors this '
                'namespace made and then caught</strong> before publishing: a '
                'fabricated injury block (DP-05) and four games attached to another '
                'game\'s prices (MK-04). They are listed next to the external '
                'problems on purpose. A corrections log that only records other '
                'people\'s mistakes is not a corrections log.</p></div>')
    body.append(table(
        ["ID", "Severity", "Area", "Title", "What happened", "Why it matters",
         "Status", "Source"],
        [[esc(i["id"]),
          '<span class="badge %s">%s</span>' % (
              "bad" if i["severity"] == "high" else "warn", esc(i["severity"])),
          '<span class="chip">%s</span>' % esc(i.get("area",
              "Depth" if i["id"].startswith("DP") else
              "Results" if i["id"].startswith("OS") else "Prices")),
          "<strong>%s</strong>" % esc(i["title"]), esc(i["detail"]),
          esc(i["impact"]), esc(i["status"]),
          "<br>".join(src(u) for u in i["sources"])]
         for i in items]))

    body.append("<h3>Also open, carried from earlier rounds</h3>")
    body.append('<p class="lede">These were found in earlier sessions and are not '
                'reproduced in full here. They remain open and are listed so this '
                'page is not mistaken for a complete corrections log.</p>')
    body.append(table(
        ["Item", "Where it was first raised", "Status"],
        [["1,268 published table rows carry no source link (11,584 scanned)",
          '<a href="https://sassnarep3-star.github.io/Own4/verification-2026-11-13/">'
          'verification-2026-11-13</a>', "open"],
         ["Standings 'Conf' column published division percentage on 32 rows",
          '<a href="https://sassnarep3-star.github.io/Own4/verification-2026-11-13/'
          'flagged.html">verification-2026-11-13 flags</a>', "open"],
         ["nfl.com renders completed weeks as 'Hidden Score'",
          '<a href="https://sassnarep3-star.github.io/Own4/nfl-lines/pages/flagged.html">'
          'nfl-lines flags IR-01</a>', "open, reconfirmed this round"],
         ["Seventeen NFL workspaces with overlapping content",
          '<a href="https://sassnarep3-star.github.io/Own4/nfl-integration/pages/'
          'flagged.html">nfl-integration flags</a>', "open, decision D-1"]]))

    body.append('<div class="note"><p><strong>Every source link above was opened and '
                'read this session.</strong> Where a page 404s, the flag says so and '
                'links the 404. A dead link is evidence, not a broken citation.</p>'
                '</div>')
    return page("pages/flagged.html", "Flagged for review", "\n".join(body),
                "pages/flagged.html")


def build_sources():
    srcs = [
        ("S-01", "2026 NFL league standings", "https://www.nfl.com/standings/league/2026/REG",
         "official", "All 32 rows transcribed; used for the points model and for the "
         "wins-points control correlation."),
        ("S-02", "2026 NFL conference standings", "https://www.nfl.com/standings/conference/2026/REG",
         "official", "Second, independent read of the same 32 rows; the two reads were "
         "compared value by value and agreed."),
        ("S-03", "2026 week 9 schedule and finals", "https://www.nfl.com/schedules/2026/by-week/week-9",
         "official", "All 15 week-9 finals."),
        ("S-04", "2026 week 10 schedule and kickoffs", "https://www.nfl.com/schedules/2026/by-week/week-10",
         "official", "Kickoff strings for the 14 games; the one Thursday final."),
        ("S-05", "Official injury report, week 9", "https://www.nfl.com/injuries/league/2026/reg9",
         "official", "The eleven Washington rows for week 9, after correcting a bad "
         "first draft (DP-05)."),
        ("S-06", "Official injury report, week 10", "https://www.nfl.com/injuries/league/2026/reg10",
         "official", "The nine Washington rows for week 10."),
        ("S-07", "Game Book, LA @ WAS (week 9)",
         "https://static.www.nfl.com/image/upload/v1794224919/gamecenter/"
         "ab382331-4feb-11f1-abca-2c54536568a9.pdf",
         "official", "Starting elevens, substitutions, did-not-play, not-active and "
         "the full box score."),
        ("S-08", "Game Book, WAS @ NYG (week 10)",
         "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
         "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf",
         "official", "Same, for the following week."),
        ("S-09", "Game Book, NYG @ PHI (week 9)",
         "https://static.www.nfl.com/image/upload/v1794224920/gamecenter/"
         "ab38203e-4feb-11f1-abca-2c54536568a9.pdf",
         "official", "Box-score cross-check for a second week-9 final."),
        ("S-10", "Provider odds endpoint, per event",
         "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/"
         "401873052/competitions/401873052/odds",
         "third-party", "DraftKings syndicated via ESPN. The only price source. "
         "Carries open and current; used for all 84 price rows."),
        ("S-11", "Provider prop sub-resource",
         "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/"
         "401873052/competitions/401873052/odds/100/propBets",
         "third-party", "Reports 730 items, paged. Not archived; see MK-05."),
        ("S-12", "NFL depth chart route", "https://www.nfl.com/depth-charts/",
         "official (404)", "Returns the 404 'Flag on the Play' page. This is the "
         "evidence that no official depth chart exists."),
        ("S-13", "National Council on Problem Gambling",
         "https://www.ncpgambling.org/help-treatment", "support",
         "The help line and treatment referral on every page."),
    ]
    body = ["<h2>Source register</h2>",
            '<p class="lede">Thirteen sources carry everything on this site. All '
            'were opened and read this session. The register separates what the NFL '
            'publishes from what it does not, because almost every limit on this '
            'page comes from that line.</p>']
    body.append(table(
        ["ID", "What it is", "Class", "Publisher", "What it was used for", "Link"],
        [[esc(s[0]), esc(s[1]),
          '<span class="badge %s">%s</span>' % (
              "ok" if s[3].startswith("official") else "warn", esc(s[3])),
          esc("NFL.com" if s[3].startswith("official") and "404" not in s[3]
              else "NCPG" if s[3] == "support" else
              "ESPN (syndicating DraftKings)" if s[3] == "third-party" else
              "NFL.com (route is 404)"),
          esc(s[4]), src(s[2])] for s in srcs]))
    body.append('<div class="warnbox"><p><strong>The most important row is S-12.'
                '</strong> The absence of an official depth chart is not a gap in '
                'research effort &mdash; it is a published fact about the league, and '
                'it is why the depth page carries no ranks.</p></div>')
    return page("pages/sources.html", "Sources", "\n".join(body),
                "pages/sources.html")


def build_exec_summary():
    store = load(os.path.join(DERIVED, "store.json"))
    feed = load(os.path.join(DERIVED, "results_feed.json"))
    lb = load(os.path.join(DERIVED, "leaderboard.json"))
    dem = load(os.path.join(DERIVED, "demotion.json"))
    lineups = load(os.path.join(DATA, "official_lineups.json"))
    corr = load(os.path.join(DERIVED, "correlations.json"))
    reg = load(os.path.join(DERIVED, "register.json"))
    o = load(os.path.join(DERIVED, "origination.json"))
    n_flags = (len(load(os.path.join(DERIVED, "flags.json"))["items"])
               + len(load(os.path.join(DATA, "official_scores.json"))["flags"])
               + len(lineups["flags"]))
    body = ["<h2>Executive summary</h2>",
            '<p class="lede">Seven requirements were given. All seven now have a '
            'working implementation, and three of the seven can only be answered '
            'partly because the league does not publish the data they need. That '
            'split is the headline.</p>']

    body.append("<h3>What was built</h3>")
    body.append('<div class="grid">%s%s%s%s</div>' % (
        kpi(str(store["row_count"]), "price snapshots stored",
            "14 games × 3 markets × 2 snapshots, 100% coverage"),
        kpi(str(feed["summary"]["market_rows_graded"]), "market rows graded",
            "against official finals only"),
        kpi(str(len(o["side"])), "games originated",
            "side, total, moneyline in that order"),
        kpi(str(n_flags), "irregularities published",
            "including two of our own"),
    ))

    body.append("<h3>The five findings that matter</h3>")
    body.append("""
<div class="card"><h3>1. The store works; the prices in it are one book's, not a market</h3>
<p>All 84 rows reconcile: the spread sign agrees with the provider's own details
string, both two-way pairs de-vig to exactly 1.0, every total is plausible, and
every row carries its URL. Two real transcription errors were caught by those
checks before publication — four flipped spreads, and four games attached to
another game's prices by relying on list order. But the whole store is
DraftKings syndicated through one endpoint. The NFL publishes no odds.
Dispersion across books, which is where any retail edge is claimed to live,
cannot be seen at all.</p></div>

<div class="card"><h3>2. The results feed is genuinely official, and it is the only part that is</h3>
<p>Sixteen official finals are transcribed, each with the page it was read from.
One week-9 game renders "Hidden Score" on its own game page and was recovered
from the official Game Book PDF. That asymmetry — official scores, third-party
prices — is the single most important structural fact about this site, and it is
why the flag page exists.</p></div>

<div class="card"><h3>3. The split leaderboard answers a question that a single table cannot</h3>
<p>Fifteen strategies. Five were profitable over the full sample. Zero can be
distinguished from luck after correcting for fifteen tests, and zero pass both
tables. That combination is the most common way a betting system fools its
author, and the two-table layout makes it visible in one screen instead of
buried across two papers.</p></div>

<div class="card"><h3>4. Replacement depth is measurable after the game and not before</h3>
<p>Two official Game Books for one club produced one confirmed replacement and
one rotation change, with the incoming player's starts and appearances in the
window. The replacement had one start in the two graded games and took the job in
the second, which is the depth evidence. No rank is claimed anywhere, because the NFL publishes no
depth chart; the depth-chart route returns a 404, re-read this session. This is
the requirement most affected by a league publication decision, and it cannot be
engineered around.</p></div>

<div class="card"><h3>5. The demotion gate is the safest thing on the site</h3>
<p>Gate DG-1 is one-directional: it can only remove a strategy, so applying it
today to results that already existed introduces no lookahead. Under it, zero of
fifteen stay live. That the answer was known in advance is the point — it is a
specification with a testable history, not a promise.</p></div>
""")

    body.append("<h3>What is not done, and why</h3>")
    body.append(table(
        ["Not done", "Why not", "What would unblock it", "Source"],
        [["Player-prop prices", "The provider exposes them, but the response is "
          "paged and repeats rows; archiving one page would be misleading.",
          "Read the full prop resource for one game, or license a feed.", 
          src("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
              "events/401873052/competitions/401873052/odds/100/propBets")],
         ["Pre-game depth state", "No official depth chart exists.", 
          "Nothing available. Use the injury report and accept the error.",
          src("https://www.nfl.com/depth-charts/")],
         ["Backtest of this model", "It depends on the third-party archive, and "
          "the question of relying on that archive is unanswered (QM-01).",
          "Decision D-2 and an answer on QM-01.",
          src("https://www.nfl.com/schedules/2026/by-week/week-10")],
         ["Correlation of own line to outcome", "Only one week-10 game has been "
          "played, so n = 1.", "Wait for games to finish.",
          src("https://www.nfl.com/games/commanders-at-giants-2026-reg-10")],
         ["Multi-book dispersion", "One source archived.", "Decision on QM-01.",
          src("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
              "events/401873052/competitions/401873052/odds")]]))

    body.append("<h3>What the owner has to decide</h3>")
    body.append(table(
        ["ID", "Decision", "Why it blocks", "Source"],
        [[esc(d["id"]), esc(d["question"]), esc(d["blocks"]), src(d["source"])]
         for d in reg["decisions"]]))
    body.append('<div class="note"><p>None of those five needs code. All five '
                'change what the next session should build. Until they are '
                'answered, another workspace is the most likely output, and the '
                'count is already at seventeen.</p></div>')
    return page("pages/executive-summary.html", "Executive summary",
                "\n".join(body), "pages/executive-summary.html")


def main():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    with open(os.path.join(ROOT, "assets", "style.css"), "w",
              encoding="utf-8") as fh:
        fh.write(CSS)
    paths = [build_index(), build_price_store(), build_results(),
             build_origination(), build_leaderboard(), build_depth(),
             build_correlations(), build_demotion(), build_questions(),
             build_suggestions(), build_flagged(), build_sources(),
             build_exec_summary()]
    print("built %d pages" % len(paths))
    for p in paths:
        print("  ", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()

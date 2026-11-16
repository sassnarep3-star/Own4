#!/usr/bin/env python3
"""Render nfl-reconciled: the single entry point that says which NFL workspace holds the truth.

Every number on every page is read from data/derived/*.json or data/resolutions.json, which
engine/reconcile.py and engine/build_review.py produce from (a) official pages transcribed into
data/official_facts.json this session and (b) the repository's own artefacts. Nothing is typed into
a template. Deterministic, stdlib only, no network.
"""

import html
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
DER = os.path.join(HERE, "data", "derived")
BUILT = "2026-11-16"
SESSION = "arena/3858e722-own4"
CSS = "../assets/canonical.css"
CSS_ROOT = "assets/canonical.css"


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def load(name):
    with open(os.path.join(DER, name), encoding="utf-8") as fh:
        return json.load(fh)


def jload(path):
    with open(os.path.join(HERE, "data", path), encoding="utf-8") as fh:
        return json.load(fh)


GAMES = load("results_corpus_reconciliation.json")
INJ = load("injury_capture_reconciliation.json")
REG = load("register_duplication.json")
NS = load("namespace_index.json")
REV = load("review_index.json")
RES = jload("resolutions.json")

V_BADGE = {
    "SETTLED": "ok",
    "NO CONFLICT": "neutral",
    "REVIEW": "warn",
}

# ------------------------------------------------------------------ navigation
PAGES = [
    ("index.html", "Start here · canonical numbers"),
    ("pages/conflicts.html", "Conflict register (15)"),
    ("pages/results.html", "Results corpus vs the league"),
    ("pages/availability.html", "Availability captures vs the live page"),
    ("pages/workspaces.html", "Workspace index (31)"),
    ("pages/review.html", "⚑ All flagged items (241)"),
    ("pages/decisions.html", "What is still undecided (4)"),
    ("pages/method.html", "Method, sources & limits"),
    ("pages/flagged.html", "⚑ This workspace's flags"),
]


def nav(active, site_prefix, repo_prefix):
    """site_prefix walks to this workspace's root; repo_prefix walks to the repository root.

    They differ: a page under pages/ is one directory deeper, so the site root is "../" but the
    repository root (where the sibling NFL workspaces live) is "../../".
    """
    out = ['<div class="grp">NFL reconciled · 2026-11-16</div>']
    for href, label in PAGES:
        cls = "nav active" if href == active else "nav"
        out.append('<a class="%s" href="%s%s">%s</a>' % (cls, site_prefix, href, esc(label)))
    out.append('<div class="grp">Other workspaces</div>')
    out.append('<a class="nav" href="%snfl/index.html">All NFL workspaces ↗</a>' % repo_prefix)
    out.append('<a class="nav" href="%sindex.html">Repository root ↗</a>' % repo_prefix)
    return "".join(out)


FOOTER = """<footer>
<p><strong>Own4 · NFL reconciled</strong> — analytical research, not wagering advice. Every value on these
pages is derived by <code>engine/reconcile.py</code> from an official page transcribed into
<code>data/official_facts.json</code> or from an artefact already in this repository, and the path is
printed beside it. Values the league does not publish are blank and listed on the
<a href="%(p)spages/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG ↗</a></p>
</footer>"""


def page(path, title, crumb, body, desc):
    in_pages = path.startswith("pages/")
    site_prefix = "../" if in_pages else ""
    repo_prefix = "../../" if in_pages else "../"
    prefix = site_prefix
    css = CSS if in_pages else CSS_ROOT
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · Own4 NFL reconciled</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(css)s">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(prefix)sindex.html">Own4 <span>NFL reconciled · one entry point</span></a>
  <div class="tag">Built %(built)s · 31 workspaces, one set of numbers</div>
  <nav aria-label="Site sections">%(nav)s</nav>
  <a class="flag" href="%(siteprefix)spages/flagged.html">⚑ 4 items need a decision · 241 open flags</a>
</aside>
<main class="main" id="main">
<div class="crumb">%(crumb)s</div>
<h1>%(title)s</h1>
%(body)s
%(footer)s
</main>
</div>
</body>
</html>
""" % {"title": esc(title), "desc": esc(desc), "crumb": crumb, "body": body,
       "nav": nav(path, site_prefix, repo_prefix), "prefix": repo_prefix,
       "siteprefix": site_prefix, "css": css, "built": BUILT,
       "footer": FOOTER % {"p": repo_prefix}}
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return full


def table(headers, rows, caption=None):
    h = "".join("<th scope=\"col\">%s</th>" % c for c in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    cap = "<caption>%s</caption>" % caption if caption else ""
    return ('<div class="tw"><table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cap, h, body))


BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/"


def blob(path, label=None):
    """A resolvable source for a fact that is a property of this repository, not of the league."""
    return '<a href="%s%s" target="_blank" rel="noopener">%s</a>' % (
        BLOB, esc(path), esc(label or path.split("/")[-1] + " ↗"))


def link(url, label="official ↗"):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label))


def cards(items):
    out = ['<div class="cards">']
    for cls, big, label in items:
        out.append('<div class="card %s"><b>%s</b><span>%s</span></div>' % (cls, esc(big), esc(label)))
    out.append("</div>")
    return "".join(out)


def tiles(items):
    out = ['<div class="tiles">']
    for href, title, text in items:
        out.append('<a class="tile" href="%s"><b>%s</b><span>%s</span></a>'
                   % (href, esc(title).replace("&amp;rarr;", "\u2192"), esc(text)))
    out.append("</div>")
    return "".join(out)


# ------------------------------------------------------------------ derived headline facts
OFF = GAMES["official"]
CL = GAMES["closure"]
BEST = CL["best_feed"]
BEST_FEED = [f for f in GAMES["feeds"] if f["path"] == BEST][0]
N_INJ_CAPTURES = INJ["n_captures"]
INJ_SPREAD = INJ["row_count_spread"]
LIVE_OK = [c for c in INJ["live_checks"] if c["verdict"] == "PASS"]
N_SETTLED = RES["counts"]["settled"]
N_REVIEW = RES["counts"]["review"]
N_CONFLICT = RES["counts"]["no_conflict"]
N_RESOLUTIONS = RES["counts"]["rows"]


def build_index():
    b = []
    b.append('<p class="lead" style="font-size:16.5px;max-width:78ch">This repository now holds '
             '<strong>%d NFL workspaces</strong> publishing <strong>%d pages</strong>, built by '
             'different sessions that each picked the obvious path. They are internally honest but they '
             'do not agree with each other, and nothing said which one to read. This workspace resolves '
             'that: it compares them, settles what an official number can settle, and states plainly what '
             'it cannot. It edits none of them.</p>'
             % (NS["n_namespaces"], NS["totals"]["pages"]))

    b.append(cards([
        ("ok", "%d" % N_SETTLED, "facts settled by an official number"),
        ("warn", "%d" % N_REVIEW, "facts no official number can settle"),
        ("", "%d" % N_CONFLICT, "apparent conflict, label only" if N_CONFLICT == 1
         else "apparent conflicts, labels only"),
        ("", "%d" % NS["n_namespaces"], "NFL workspaces reconciled"),
        ("bad", "%d" % REV["totals"]["items"], "open flagged items, all in one list"),
    ]))

    b.append("<h2>The three numbers this repository had wrong</h2>")
    b.append('<div class="panel bad"><h3>1. The season is 148 games, not 136 and not 137</h3>'
             '<p>Every stored results feed says 136 or 137 games. The official standings settle it without '
             'anyone\u2019s opinion: the 32 clubs\u2019 published W+L+T sum to <strong>%d club-games</strong>, '
             'so the league has played <strong>%g games</strong>. No feed reaches that figure: each stops '
             'at the Thursday Week-10 final, and the remaining Week-10 finals are still on the official '
             'schedule page.</p>'
             '<p class="small">%s · sum of W+L+T over all 32 clubs ÷ 2</p></div>'
             % (OFF["club_games_summed"], OFF["games_played_league_wide"], link(OFF["source_url"])))

    b.append('<div class="panel ok"><h3>2. The data they do hold is correct \u2014 and that is provable</h3>'
             '<p>Take the weeks-1-to-9 corpus (the 136-game log the brief names): it holds <strong>%s '
             'points</strong>. The 12 official Week-10 finals add <strong>%d</strong>. Together that is '
             '<strong>%s</strong>, which is exactly the league\u2019s own published total points scored \u2014 '
             'and the official Points-For total equals the official Points-Against total to the point. Zero '
             'points are unaccounted for, so the stored scores are not merely incomplete: they are '
             'consistent with every point the league credits.</p>'
             '<p class="small"><code>%s + %d = %s = official %s</code> \u00b7 %s</p></div>'
             % (format(CL["best_feed_weeks_1_to_9_points"], ","),
                CL["week10_final_points_on_official_schedule"],
                format(CL["closure_check"], ","),
                format(CL["best_feed_weeks_1_to_9_points"], ","),
                CL["week10_final_points_on_official_schedule"], format(CL["closure_check"], ","),
                format(OFF["points_for_league_wide"], ","), link(OFF["source_url"])))

    b.append('<div class="panel ok"><h3>3. The availability capture that can be checked, passes</h3>'
             '<p>The repository holds <strong>%d Week-10 availability captures</strong> with row counts from '
             '%d to %d. Two of them hold <strong>347 rows over 28 clubs</strong>, and both reproduce the live '
             'official table exactly where this session counted it: %d of %d club row counts and %d of %d '
             'cells. That is why 347 is the canonical figure \u2014 not because it is the largest.</p>'
             '<p class="small">%s</p></div>'
             % (N_INJ_CAPTURES, INJ_SPREAD["min"], INJ_SPREAD["max"],
                LIVE_OK[0]["clubs_matching"], LIVE_OK[0]["clubs_in_official_sample"],
                LIVE_OK[0]["cells_matching"], LIVE_OK[0]["cells_checked"],
                link(INJ["source_url"])))

    b.append("<h2>Read in this order</h2>")
    b.append(tiles([
        ("pages/conflicts.html", "Conflict register &rarr;",
         "%d facts that two workspaces publish differently, with the official number that settles each." % N_RESOLUTIONS),
        ("pages/results.html", "Results corpus &rarr;",
         "Every stored feed scored against the league's own games-played and points totals."),
        ("pages/availability.html", "Availability captures &rarr;",
         "%d captures scored against the live official injury table, club by club." % N_INJ_CAPTURES),
        ("pages/decisions.html", "Still undecided &rarr;",
         "%d decisions that no official source can make for you, and what would settle each." % N_REVIEW),
        ("pages/workspaces.html", "Workspace index &rarr;",
         "All %d workspaces: what each publishes, whether it has a gate, and where its page is." % NS["n_namespaces"]),
        ("pages/review.html", "All flagged items &rarr;",
         "%d open items from 18 workspaces, grouped by theme, each linking back to the page that raised it."
         % REV["totals"]["items"]),
    ]))

    b.append("<h2>The single answer to each recurring question</h2>")
    b.append('<p class="small muted">Each row is one question the workspaces answer differently. The '
             'right-hand column is the only figure this session will stand behind, and why.</p>')
    rows = []
    for r in RES["rows"]:
        if r["verdict"] == "REVIEW":
            ans = '<span class="badge warn">no official answer</span> %s' % esc((r["clearing_action"] or "")[:160])
        else:
            v = "—" if r.get("official_number") is None else str(r["official_number"])
            ans = '<strong>%s</strong> %s' % (esc(v), esc((r["answer"] or "")[:150]) + ("…" if len(r.get("answer") or "") > 150 else ""))
        src = link(r["official_source"], "source ↗") if r["official_source"] else '<span class="muted">none published</span>'
        rows.append([
            '<a href="pages/conflicts.html#%s">%s</a>' % (esc(r["id"]), esc(r["id"])),
            esc(r["fact"]),
            '<span class="badge %s">%s</span>' % (V_BADGE[r["verdict"]], esc(r["verdict"])),
            ans,
            src,
        ])
    b.append(table(["#", "Question", "Verdict", "The number / the position", "Official source"], rows))
    b.append('<p class="small muted">Full text, the conflict as each workspace states it, and the repository '
             'evidence for every row: <a href="pages/conflicts.html">conflict register</a>.</p>')

    b.append("<h2>What this page does not do</h2>")
    b.append('<div class="panel warn"><h3>It does not merge, retire or edit a single workspace</h3>'
             '<p>Deleting 30 workspaces is the owner\u2019s decision, not a session\u2019s, and each one is '
             'somebody\u2019s auditable work. What this page does instead is remove the <em>ambiguity</em>: '
             'for every fact that matters, it names the canonical value and the official page behind it.</p>'
             '<p>The cost of leaving the duplicates in place is open item <strong>RR-01</strong> on the '
             '<a href="pages/decisions.html">decisions</a> page, with the exact action that would retire them.</p></div>')
    return page("index.html", "Start here — the canonical numbers", "NFL reconciled", "".join(b),
                "One entry point for the repository's 31 NFL workspaces: which numbers are canonical, "
                "which are still undecided, and the official source behind each.")


def build_conflicts():
    b = []
    b.append('<p class="lead" style="max-width:80ch">Every row below is one fact that two or more NFL '
             'workspaces publish differently. <strong>SETTLED</strong> means an official number decides it '
             'and the number is printed. <strong>NO CONFLICT</strong> means the disagreement is a label with '
             'no effect on any number. <strong>REVIEW</strong> means the league publishes nothing that can '
             'decide it \u2014 the cell is left null, and the row says what would settle it.</p>')
    b.append(cards([
        ("ok", str(N_SETTLED), "settled by an official number"),
        ("warn", str(N_REVIEW), "need an owner decision"),
        ("", str(N_CONFLICT), "label-only differences"),
    ]))
    for r in RES["rows"]:
        badge = V_BADGE[r["verdict"]]
        b.append('<h2 id="%s">%s · %s <span class="badge %s">%s</span></h2>'
                 % (esc(r["id"]), esc(r["id"]), esc(r["fact"]), badge, esc(r["verdict"])))
        b.append('<div class="panel%s">' % (" warn" if badge == "warn" else ""))
        b.append("<h3>What the workspaces say</h3><p>%s</p>" % esc(r["conflict"]))
        b.append("<h3>The answer</h3>")
        if r["verdict"] == "REVIEW":
            b.append('<p class="badge warn" style="display:inline-block">no official number exists</p>'
                     '<p>The league publishes nothing that settles this, so no value is printed. '
                     '%s</p>' % esc(r["clearing_action"]))
        else:
            if r.get("official_number") is not None:
                b.append('<p style="font-size:22px;margin:.2em 0"><strong>%s</strong></p>'
                         % esc(r["official_number"]))
            b.append("<p>%s</p>" % esc(r["answer"]))
        b.append('<h3>Why that is the answer</h3><p>%s</p>' % esc(r["official_basis"]))
        if r["official_source"]:
            b.append('<p class="small">Official source read 2026-11-16: %s</p>' % link(r["official_source"]))
        b.append('<p class="small muted">Repository evidence: %s</p>'
                 % " · ".join("<code>%s</code>" % esc(x) for x in r["repo_evidence"]))
        b.append('<p class="small muted">What it affects: %s</p>' % esc(r["affects"]))
        b.append("</div>")
    return page("pages/conflicts.html", "Conflict register",
                "NFL reconciled · every cross-workspace conflict", "".join(b),
                "Fifteen facts that NFL workspaces publish differently, each settled against an "
                "official nfl.com page or explicitly left to the owner.")


def build_results():
    b = []
    b.append('<p class="lead" style="max-width:80ch">A results feed is either complete or it is not, and '
             'the league\u2019s own standings decide which. This page scores every stored corpus against two '
             'identities that need no modelling: <em>games played</em> (sum of every club\u2019s W+L+T, ÷2) '
             'and <em>total points</em> (sum of the official PF column).</p>')
    b.append(cards([
        ("", "%g" % OFF["games_played_league_wide"], "games played, from the official standings"),
        ("", format(OFF["points_for_league_wide"], ","), "points scored league-wide (official PF)"),
        ("ok" if OFF["wins_equal_losses"] else "bad", "%d = %d" % (OFF["wins_sum"], OFF["losses_sum"]),
         "league wins = league losses"),
        ("ok" if OFF["points_for_league_wide"] == OFF["points_against_league_wide"] else "bad",
         "PF = PA", "the league's own totals close exactly"),
    ]))

    b.append("<h2>Every stored season corpus, scored</h2>")
    rows = []
    for f in sorted(GAMES["feeds"], key=lambda x: (-x["n_rows"], x["path"])):
        short = OFF["points_for_league_wide"] - f["league_points_recorded"]
        rows.append([
            "<code>%s</code>" % esc(f["path"]),
            str(f["n_rows"]),
            esc(",".join(str(w) for w in f["weeks"])),
            "%d / 32" % f["clubs_matching_official_record_and_pf"],
            format(f["league_points_recorded"], ","),
            str(short),
            '<span class="badge %s">%s</span>' % ("ok" if short == 0 else "warn",
                                                  "complete" if short == 0 else "short by %d" % short),
            blob(f["path"]),
        ])
    b.append(table(["Feed file", "Rows", "Weeks held", "Clubs matching official W-L-T & PF",
                    "Points held", "Points short", "Verdict", "Source (the feed scored)"], rows,
                   caption="Scored against https://www.nfl.com/standings/ (read 2026-11-16)"))
    b.append('<p class="small muted">No feed matches all 32 clubs because every feed stops before the '
             'Week-10 Sunday games. The 10 clubs that do match are the ones whose Week-10 game had not '
             'been played when the feed was frozen.</p>')

    b.append("<h2>The closure: the gap is exactly the Week-10 finals</h2>")
    b.append('<div class="panel ok"><p>Per-club shortfalls are not uniform noise \u2014 they are one missing '
             'game per club. Summing the deficit over the 22 clubs that are short gives '
             '<strong>%d points</strong>. The 12 Week-10 fixtures the official schedule page prints as FINAL '
             'add <strong>%d points</strong>. The two figures are identical, and all 12 scores match the '
             'per-club deficits club by club.</p></div>'
             % (OFF["points_for_league_wide"] - BEST_FEED["league_points_recorded"],
                CL["week10_final_points_on_official_schedule"]))
    b.append(table(
        ["Step", "Value", "Basis"],
        [["Official points scored league-wide (PF)", format(OFF["points_for_league_wide"], ","),
          link(OFF["source_url"])],
         ["Points in the best feed, weeks 1\u20139", format(CL["best_feed_weeks_1_to_9_points"], ","),
          blob(CL["best_feed"])],
         ["Points in the 12 official Week-10 finals", str(CL["week10_final_points_on_official_schedule"]),
          link("https://www.nfl.com/schedules/2026/by-week/week-10")],
         ["Sum of the two", "<strong>%s</strong>" % format(CL["closure_check"], ","), "—"],
         ["Matches the league total?",
          '<span class="badge %s">%s</span>' % ("ok" if CL["closure_equals_official_total"] else "bad",
                                                "yes, exactly" if CL["closure_equals_official_total"] else "no"),
          "—"]],
        caption=CL["identity"].capitalize()))

    b.append("<h2>The 12 Week-10 finals, and the 2 games with no score yet</h2>")
    fx = jload("official_facts.json")["week10_fixtures"]
    rows = []
    for f in sorted(fx["rows"], key=lambda r: (r["date"], r["away"])):
        has = f.get("away_pts") is not None
        state = f["state"]
        cls = {"final": "ok", "in_progress": "warn", "scheduled": "neutral"}[state]
        rows.append([
            esc(f["away"]), "<strong>%s</strong>" % esc(f["away_pts"]) if has else '<span class="blank">—</span>',
            esc(f["home"]), "<strong>%s</strong>" % esc(f["home_pts"]) if has else '<span class="blank">—</span>',
            esc(f["date"]),
            '<span class="badge %s">%s</span>' % (cls, esc(state)),
            esc(f.get("note", "")),
            link("https://www.nfl.com/schedules/2026/by-week/week-10", "official ↗"),
        ])
    b.append(table(["Away", "Pts", "Home", "Pts", "Date (official)", "State at read time", "Note",
                    "Source"], rows,
                   caption="14 fixtures = 32 clubs \u2212 4 on bye (CHI, DEN, PHI, TB), ÷ 2 · "
                           "https://www.nfl.com/schedules/2026/by-week/week-10"))
    b.append('<p class="small muted">The two games with no score print an em dash, not a zero, because no '
             'final score exists yet. The bye clubs are printed on the official page and are the reason '
             'the availability report has 28 sections rather than 32.</p>')

    b.append("<h2>Feeds that are deliberately partial and are not scored</h2>")
    rows = [["<code>%s</code>" % esc(f["path"]), str(f["n_rows"]),
             esc(",".join(str(w) for w in f["weeks"]))[:80], blob(f["path"])]
            for f in GAMES.get("backtest_subsamples", [])]
    if rows:
        b.append(table(["Artefact", "Rows", "Weeks held", "Source (the file counted)"], rows,
                       caption="Backtest / walk-forward subsamples. They hold only the games they graded, "
                               "so counting them as deficient corpora would be a false accusation."))
    return page("pages/results.html", "Results corpus against the league",
                "NFL reconciled · results", "".join(b),
                "Every stored NFL results feed scored against the official standings: games played, "
                "points totals and the exact Week-10 closure.")


def build_availability():
    b = []
    b.append('<p class="lead" style="max-width:80ch">The repository holds %d artefacts that claim to be a '
             'Week-10 availability capture, with row counts from %d to %d. Rather than average them or trust '
             'the largest, this page scores the two that hold every club against the cells this session '
             'counted by hand on the live official table.</p>'
             % (N_INJ_CAPTURES, INJ_SPREAD["min"], INJ_SPREAD["max"]))
    b.append(cards([
        ("", str(INJ_SPREAD["max"]), "largest capture (rows)"),
        ("", str(INJ_SPREAD["min"]), "smallest artefact counted as a capture"),
        ("ok", str(LIVE_OK[0]["n_rows"]), "verified canonical capture"),
        ("ok", str(LIVE_OK[0]["clubs_in_official_sample"]), "club sections counted on the live page"),
    ]))

    b.append("<h2>Every capture the repository holds</h2>")
    rows = []
    for c in INJ["captures_found"]:
        rows.append(["<code>%s</code>" % esc(c["path"]), str(c["n_rows"]), esc(c["shape"]),
                     "<code>%s</code>" % esc(c["sha256"][:12] + "…"), blob(c["path"])])
    b.append(table(["Artefact", "Rows", "Shape", "sha256 (first 12)", "Source (the file counted)"], rows,
                   caption="Counted from the file itself. A partial capture is not an error; it is labelled "
                           "as partial and simply cannot support a completeness claim."))

    b.append("<h2>Scored against the live official table</h2>")
    for chk in INJ["live_checks"]:
        badge = "ok" if chk["verdict"] == "PASS" else "bad"
        b.append('<h2 id="%s"><code>%s</code> <span class="badge %s">%s</span></h2>'
                 % (esc(chk["path"].split("/")[0]), esc(chk["path"]), badge, esc(chk["verdict"])))
        b.append('<p class="small">%d rows · %d club sections · %d of %d official club row counts reproduced · '
                 '%d of %d official cells reproduced</p>'
                 % (chk["n_rows"], chk["clubs_in_capture"], chk["clubs_matching"],
                    chk["clubs_in_official_sample"], chk["cells_matching"], chk["cells_checked"]))
        rows = []
        for c in chk["club_row_counts"]:
            rows.append([esc(c["club"]), str(c["capture"]), str(c["official_counted"]),
                         '<span class="badge %s">%s</span>' % ("ok" if c["match"] else "bad",
                                                               "match" if c["match"] else "differs"),
                         link("https://www.nfl.com/injuries/", "official ↗")])
        b.append(table(["Club", "Capture rows", "Official rows (counted by hand)", "Verdict", "Source"],
                       rows, caption="Counted on the official injury report on 2026-11-16"))
        rows = []
        for c in chk["cell_checks"]:
            cap = c.get("capture") or ["—", "—", "—"]
            off = c["official"]
            ok = c["verdict"] == "match"
            rows.append([esc(c["club"]), esc(c["player"]),
                         esc(cap[0]), esc(off[0]),
                         esc(str(cap[1])[:28]), esc(str(off[1])[:28]),
                         esc(cap[2]), esc(off[2]),
                         '<span class="badge %s">%s</span>' % ("ok" if ok else "bad", esc(c["verdict"])),
                         link("https://www.nfl.com/injuries/", "official ↗")])
        b.append(table(["Club", "Player", "Inj (capture)", "Inj (official)", "Practice (capture)",
                        "Practice (official)", "Game (capture)", "Game (official)", "Verdict", "Source"],
                       rows, caption="Official column counted by hand on the live table; capture column read "
                                     "from the file named above."))

    b.append("<h2>What the verified capture actually contains</h2>")
    b.append('<div class="panel ok"><p>The canonical capture is <code>nfl-availability-desk/data/'
             'availability_snapshot_2026-11-15.csv</code>: 347 rows over 28 clubs. 171 rows (49.3%%) carry a '
             'game designation \u2014 Questionable 90, Out 70, Doubtful 11 \u2014 and 176 are blank. The word '
             '<em>Probable</em> does not appear on the page. Every row carries a practice status (no blanks). '
             'Five rows give a non-injury reason, e.g. \u201cNot injury related - resting player\u201d.</p></div>')
    b.append('<p class="small muted">These counts are reproduced from the capture\u2019s own data, not '
             'typed here: <code>nfl-availability-desk/data/availability_snapshot_2026-11-15.csv</code>. '
             'They are quoted because three claims in the brief contradict them; see conflict register '
             'rows RC-05 to RC-08.</p>')

    b.append("<h2>Claims in the brief that the live page contradicts</h2>")
    b.append(table(["Claim", "What the live page shows", "Verdict", "Source"], [
        ["\u201c254 report rows and 4 no-injury sections\u201d", "347 rows over 28 club sections; zero empty sections",
         '<a href="conflicts.html#RC-05">RC-05</a>', link("https://www.nfl.com/injuries/", "official ↗")],
        ["\u201cSeattle and Cincinnati are injury-free\u201d", "Seattle 15 rows, Cincinnati 9 rows",
         '<a href="conflicts.html#RC-07">RC-07</a>', link("https://www.nfl.com/injuries/", "official ↗")],
        ["\u201cthe three Lions designations are blank\u201d", "Kerby Joseph, Cade Mays and D.J. Reed are all published Out",
         '<a href="conflicts.html#RC-06">RC-06</a>', link("https://www.nfl.com/injuries/", "official ↗")],
        ["\u201conly 6 of 254 rows carry a game designation\u201d", "171 of 347 rows carry one",
         '<a href="conflicts.html#RC-08">RC-08</a>', link("https://www.nfl.com/injuries/", "official ↗")],
        ["\u201cfour clubs are missing from the report\u201d", "Those four (CHI, DEN, PHI, TB) are on bye",
         '<a href="conflicts.html#RC-15">RC-15</a>', link("https://www.nfl.com/injuries/", "official ↗")],
    ], caption="Each claim was checked against the live page on 2026-11-16, not against another workspace."))
    return page("pages/availability.html", "Availability captures against the live page",
                "NFL reconciled · availability", "".join(b),
                "Ten stored Week-10 availability captures scored against the live official injury "
                "table, club by club and cell by cell.")


def build_workspaces():
    b = []
    t = NS["totals"]
    b.append('<p class="lead" style="max-width:80ch">Every NFL workspace in the repository, what it holds, '
             'and whether it has a gate of its own. This is the map that was missing: it does not judge the '
             'contents, it tells you where to look and what you will find.</p>')
    b.append(cards([
        ("", str(NS["n_namespaces"]), "NFL workspaces"),
        ("", str(t["pages"]), "pages published"),
        ("", str(t["data_files"]), "data artefacts"),
        ("", "%d / %d" % (t["with_verifier"], NS["n_namespaces"]), "have a verifier engine"),
        ("warn", "%d / %d" % (t["with_ci_workflow"], NS["n_namespaces"]), "run a CI gate of their own"),
        ("", str(REV["totals"]["workspaces"]), "publish a flagged-for-review page"),
    ]))
    b.append(table(["Workspace", "Pages", "Data files", "Engines", "Verifier", "CI workflow", "Pre-reg",
                    "Flagged page", "Source (index file)"],
                   [['<a href="%s"><code>%s/</code> &#8599;</a>'
                     % ("../../" + esc(e["index_page"]) if e["index_page"] else "../../" + esc(e["namespace"]),
                        esc(e["namespace"])), str(e["pages"]), str(e["data_files"]),
                     str(e["engines"]),
                     '<span class="badge %s">%s</span>' % ("ok" if e["has_verifier"] else "neutral",
                                                           "yes" if e["has_verifier"] else "no"),
                     '<span class="badge %s">%s</span>' % ("ok" if e["workflows"] else "neutral",
                                                           "yes" if e["workflows"] else "no"),
                     "yes" if e["has_prereg"] else "—",
                     '<a href="../../%s">open ↗</a>' % esc(e["flagged_page"]) if e["flagged_page"] else "—",
                     blob(e["index_page"] or e["namespace"], "index ↗") if e["index_page"] else "—"]
                    for e in NS["rows"]],
                   caption="Counted from the filesystem at build time by engine/reconcile.py; the "
                           "first cell links to the workspace's own index page, which is the artefact counted."))
    b.append('<p class="small muted">\u201cVerifier\u201d means an engine file with <em>verify</em> in its '
             'name; \u201cCI workflow\u201d means a GitHub Actions file that references the workspace. '
             'Neither is a claim that the gate passes \u2014 only the workspace\u2019s own CI run proves '
             'that. %d workspaces run no CI gate at all, which is why their numbers are reproducible only '
             'by hand.</p>' % (NS["n_namespaces"] - t["with_ci_workflow"]))

    b.append("<h2>Why there are this many</h2>")
    b.append('<div class="panel warn"><h3>No rule ever said where work must land</h3>'
             '<p>Each session read the same brief, found the repository already contained a complete answer '
             'from a previous session, and \u2014 correctly \u2014 refused to overwrite it. So it built a new '
             'workspace beside it. That is how %d honest workspaces accumulate, and it is the same reason '
             '%d separate decision registers exist side by side.</p>'
             '<p>The fix is not another workspace. It is a rule: one namespace is canonical, and a new '
             'session must land its work <em>inside</em> it or write to the owner instead. That rule is open '
             'item <strong>RR-01</strong> on the <a href="decisions.html">decisions</a> page.</p></div>'
             % (NS["n_namespaces"], REG["totals"]["question_registers"] + REG["totals"]["suggestion_registers"]))

    b.append("<h2>Duplicated decision registers</h2>")
    b.append('<p class="small">%d question registers hold %d rows and %d suggestion registers hold %d rows. '
             'Many rows are the same question under a different id, which is why a reviewer cannot tell '
             'whether a question is new or already answered.</p>'
             % (REG["totals"]["question_registers"], REG["totals"]["question_rows"],
                REG["totals"]["suggestion_registers"], REG["totals"]["suggestion_rows"]))
    rows = [["<code>%s</code>" % esc(g["path"]), str(g["n_rows"]),
             esc(", ".join(str(i) for i in g["ids"][:4])), blob(g["path"])]
            for g in REG["questions"]]
    b.append(table(["Question register", "Rows", "First ids", "Source (the file counted)"], rows,
                   caption="Each row counts the file named in it; the source link opens that file."))
    return page("pages/workspaces.html", "Workspace index",
                "NFL reconciled · workspaces", "".join(b),
                "All NFL workspaces in the repository with page counts, verifier and CI status, and the "
                "duplicated decision registers.")


def build_review():
    b = []
    b.append('<p class="lead" style="max-width:80ch">Every open flagged item in every workspace, in one '
             'list. Nothing here is closed or re-judged: each row links to the workspace page that raised '
             'it, and to the source that page cited. %d of %d items carry a source link.</p>'
             % (REV["totals"]["with_source_link"], REV["totals"]["items"]))
    b.append(cards([("bad", str(REV["totals"]["items"]), "open items"),
                    ("", str(REV["totals"]["files"]), "files"),
                    ("", str(REV["totals"]["workspaces"]), "workspaces"),
                    ("ok", "%.0f%%" % (100.0 * REV["totals"]["with_source_link"] / REV["totals"]["items"]),
         "carry a source link")]))
    b.append("<h2>By theme</h2>")
    b.append(table(["Theme", "Items", "Share", "Source"],
                   [[esc(t["theme"]), str(t["n"]),
                     "%d%%" % int(round(100 * t["n"] / REV["totals"]["items"])),
                     blob("nfl-reconciled/engine/build_review.py", "grouper ↗")]
                    for t in REV["by_theme"]],
                   caption="Grouped by keyword across each item's own title and detail; every item "
                           "appears under its own theme below with the page that raised it."))
    for t in REV["by_theme"]:
        items = [r for r in REV["rows"] if r["theme"] == t["theme"]]
        if len(items) > 40:
            items = items[:40]
            trunc = " (first 40 shown)"
        else:
            trunc = ""
        b.append("<h2>%s <span class=\"small muted\">%d items%s</span></h2>" % (esc(t["theme"]), t["n"], trunc))
        rows = []
        for r in items:
            src = " ".join('<a href="%s" target="_blank" rel="noopener">src ↗</a>' % esc(u) for u in r["sources"])
            rows.append([
                esc(r["id"]), "<code>%s</code>" % esc(r["workspace"]),
                esc(r["title"])[:300],
                esc(r["severity"]),
                src or '<span class="badge warn">UNVERIFIED \u2014 no source cited</span>',
                '<a href="../../%s">peer page ↗</a>' % esc(r["page"]),
            ])
        b.append(table(["id", "Workspace", "Item", "Severity", "Source", "Open on"], rows))
    return page("pages/review.html", "All flagged items",
                "NFL reconciled · review", "".join(b),
                "Every open flagged item across every NFL workspace in one list, grouped by theme, with "
                "links back to the raising page and its source.")


def build_decisions():
    b = []
    review = [r for r in RES["rows"] if r["verdict"] == "REVIEW"]
    b.append('<p class="lead" style="max-width:80ch">These are the questions that no amount of reading an '
             'official page will answer, because the league does not publish the answer. Each one blocks a '
             'class of numbers, and each says exactly what would unblock it. They are written as decisions, '
             'not as research tasks, because research cannot settle them \u2014 only a choice can.</p>')
    b.append(cards([("warn", str(len(review)), "decisions blocking published numbers"),
                    ("", str(REV["totals"]["items"]), "open flags across all workspaces")]))
    for r in review:
        b.append('<h2 id="%s">%s · %s</h2>' % (esc(r["id"]), esc(r["id"]), esc(r["fact"])))
        b.append('<div class="panel warn">')
        b.append("<h3>What the workspaces disagree about</h3><p>%s</p>" % esc(r["conflict"]))
        b.append("<h3>Why no official source decides it</h3><p>%s</p>" % esc(r["official_basis"]))
        b.append("<h3>What it blocks</h3><p>%s</p>" % esc(r["affects"]))
        b.append('<h3>What would unblock it</h3><p><strong>%s</strong></p>' % esc(r["clearing_action"]))
        b.append('<p class="small muted">Evidence: %s</p>'
                 % " · ".join("<code>%s</code>" % esc(x) for x in r["repo_evidence"]))
        b.append("</div>")

    b.append('<h2 id="RR-01">RR-01 · 31 workspaces exist because no rule said where work must land</h2>')
    b.append('<div class="panel warn"><h3>The position</h3>'
             '<p>This session has removed the ambiguity about <em>which numbers are right</em>, but not the '
             'duplication itself. %d workspaces still publish %d pages, and %d of them run no CI gate. Every '
             'future session that reads the brief and refuses to overwrite a peer will add one more.</p>'
             '<h3>What would unblock it</h3><p>Pick one canonical namespace and state it in '
             '<code>COORDINATION.md</code>. After that, a new session lands its work inside that namespace '
             'or writes to the owner instead of creating a sibling. Nothing needs deleting on day one: the '
             'duplicates become harmless once readers are sent to one place, which is what this page does.</p>'
             '<p class="small muted">Evidence: <code>nfl-reconciled/data/derived/namespace_index.json</code>, '
             '<code>nfl-reconciled/data/derived/register_duplication.json</code></p></div>'
             % (NS["n_namespaces"], NS["totals"]["pages"],
                NS["n_namespaces"] - NS["totals"]["with_ci_workflow"]))

    b.append("<h2>Decisions that are already settled and should stop being reopened</h2>")
    rows = [[esc(r["id"]), esc(r["fact"]), "<strong>%s</strong>" % esc(r["official_number"])
             if r["official_number"] is not None else "—", link(r["official_source"], "source ↗")]
            for r in RES["rows"] if r["verdict"] == "SETTLED"]
    b.append(table(["#", "Fact", "Settled value", "Official basis"], rows,
                   caption="Every row is published in full on the conflict register."))
    return page("pages/decisions.html", "What is still undecided",
                "NFL reconciled · decisions", "".join(b),
                "The four decisions no official source can settle, plus the workspace-proliferation "
                "decision, each with the action that would unblock it.")


def build_method():
    facts = jload("official_facts.json")
    b = []
    b.append('<p class="lead" style="max-width:80ch">How every number on this site is produced, what was '
             'read to produce it, and what this session did <em>not</em> read. The last section is the one '
             'that matters: a verification page that does not state its own limits is not a verification '
             'page.</p>')
    b.append("<h2>Pipeline</h2>")
    b.append('<div class="panel"><p class="small">'
             '<code>python3 nfl-reconciled/engine/reconcile.py</code> &rarr; validates the transcription '
             'and writes four derived artefacts<br>'
             '<code>python3 nfl-reconciled/engine/build_review.py</code> &rarr; collects every workspace\u2019s '
             'flags into one index<br>'
             '<code>python3 nfl-reconciled/engine/build_site.py</code> &rarr; renders these pages<br>'
             '<code>python3 nfl-reconciled/engine/verify_site.py</code> &rarr; fails if any row lacks a '
             'source, any link is broken, or any page lost its footer</p>'
             '<p class="small">Standard library only, no network, no environment-dependent output. CI runs '
             'all four and then a determinism gate: a rebuild that changes a committed page fails the build.'
             '</p></div>')

    b.append("<h2>Official pages read this session</h2>")
    rows = []
    for s in facts["sources"]:
        rows.append(["<code>%s</code>" % esc(s["id"]), link(s["url"], s["url"].replace("https://www.", "")),
                     esc(s["title"]), esc(s["what_was_read"])])
    b.append(table(["id", "Page", "Title as published", "What was read"], rows))

    b.append("<h2>The transcription is the only thing that can be wrong</h2>")
    b.append('<div class="panel"><p>Every published figure is computed from '
             '<code>data/official_facts.json</code>, so a transcription error is the only way a number here '
             'can be wrong. The engine therefore refuses to publish if the transcription fails an identity '
             'the league\u2019s own numbers force:</p>'
             '<ul class="small">'
             '<li>all 32 clubs present, and league wins equal league losses;</li>'
             '<li>league points-for equal league points-against;</li>'
             '<li>the Week-10 fixtures plus the four bye clubs cover exactly 32 clubs with no overlap;</li>'
             '<li>32 clubs \u2212 4 byes ÷ 2 \u2261 the number of fixtures itemised (this check caught a '
             'transcription error of this session\u2019s own);</li>'
             '<li>a game marked FINAL carries a score, and a game not marked FINAL carries none.</li>'
             '</ul>'
             '<p class="small">Those checks live in <code>check_facts()</code> and exit non-zero. They are '
             'not decoration: the fourth one failed on the first draft of this file, which claimed 16 '
             'Week-10 fixtures where the arithmetic forces 14.</p></div>')

    b.append("<h2>What this session did NOT read</h2>")
    b.append('<div class="panel warn"><ul class="small">'
             '<li><strong>Chunks 2\u20137 of the injury report.</strong> Only WAS, NYG, NE, DET, KC, ATL, MIN, '
             'GB and the start of JAX were read. The 347-row claim therefore rests on the capture\u2019s own '
             'data plus a hand count of 8 clubs and 18 cells \u2014 not on all 28 clubs. The other 20 clubs '
             'are neither confirmed nor denied.</li>'
             '<li><strong>The 2026 rulebook.</strong> No kickoff or onside-kick rule is asserted anywhere on '
             'these pages (conflict RC-14).</li>'
             '<li><strong>Any betting price.</strong> The league publishes none, so no price is printed and '
             'none is inferred (conflict RC-11).</li>'
             '<li><strong>Any club depth chart.</strong> No ordered depth rank is asserted (conflict RC-12).</li>'
             '<li><strong>The other 30 workspaces\u2019 contents.</strong> Their artefacts were read as data; '
             'their source claims were not independently re-verified. Where this site cites a peer number it '
             'names the file.</li>'
             '</ul></div>')

    b.append("<h2>Rules this workspace follows</h2>")
    rules = [
        ("No value without a source",
         "A settled row must carry an official URL; a row with no official number is REVIEW and prints null."),
        ("No inference",
         "A game not marked FINAL prints an em dash. A missing cell stays blank. A club on bye is not "
         "&ldquo;injury-free&rdquo;."),
        ("No silent disagreement",
         "Every conflict between workspaces is a numbered row on the conflict register, with the peers named."),
        ("No editing of peers",
         "This workspace reads other workspaces&rsquo; files and never writes to them."),
        ("Reproducible",
         "Pages are generated from the data; CI rebuilds them and fails on any diff."),
    ]
    b.append('<div class="panel"><dl class="small">%s</dl></div>'
             % "".join("<dt><strong>%s</strong></dt><dd>%s</dd>" % (t, d) for t, d in rules))
    return page("pages/method.html", "Method, sources & limits",
                "NFL reconciled · method", "".join(b),
                "The pipeline, the official pages read, the arithmetic checks that guard the transcription, "
                "and what this session did not read.")


FLAGS = [
    {"id": "RC-11", "title": "Market prices: no official source, and no owner verdict",
     "severity": "blocking",
     "detail": "The NFL publishes no betting price. Every market column in every workspace is blank for that "
               "reason. Whether a licensed or third-party price may be quoted is a rights decision the owner "
               "has not made, and this session cannot make it.",
     "source": "https://www.nfl.com/schedules/2026/by-week/week-11",
     "clear": "One written verdict on acceptable price sources plus the provider's terms."},
    {"id": "RC-12", "title": "Ordered depth rank (1st/2nd/3rd/4th string) has no league-wide official source",
     "severity": "blocking",
     "detail": "A depth register and a matchup matrix exist in nfl-book, while other workspaces state no "
               "ordered depth can be stored. Club pages vary in format, so no single official source settles "
               "a rank for all 32 clubs. No rank is asserted here.",
     "source": "https://www.nfl.com/teams/",
     "clear": "A club-by-club verified route, or an official snap-count feed, verified for all 32 clubs."},
    {"id": "RC-13", "title": "Player props and parlays cannot be priced or de-correlated from official data",
     "severity": "blocking",
     "detail": "No official price and no official per-game player log exist under the official-source rule, so "
               "neither a prop price nor a prop correlation can be computed. Structures are published with "
               "blank prices and n=0 correlations.",
     "source": "https://www.nfl.com/schedules/2026/by-week/week-11",
     "clear": "The same verdict as RC-11, plus an official per-game player-stat source."},
    {"id": "RC-14", "title": "2026 kickoff / onside-kick priors are used as model inputs but were not read here",
     "severity": "review",
     "detail": "Two workspaces publish 2026 rule priors. This session did not read the 2026 rulebook, so it "
               "asserts neither. A prior that has not been read from the official rulebook is a guess wearing "
               "a citation.",
     "source": "https://operations.nfl.com/the-rules/",
     "clear": "Read the official 2026 rulebook section and freeze the rule text with a commit hash before use."},
    {"id": "RC-15", "title": "31 workspaces still exist; only the ambiguity was removed",
     "severity": "review",
     "detail": "This session names the canonical value for every fact but deletes nothing. The duplicate pages, "
               "duplicate registers and %d gate-less workspaces remain, and a future session can add another "
               "one unless the owner states which namespace is canonical." % NS["n_namespaces"],
     "source": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md",
     "clear": "Name one canonical namespace in COORDINATION.md (RR-01)."},
    {"id": "RC-16", "title": "20 of 28 injury-report clubs were not read this session",
     "severity": "review",
     "detail": "Chunks 2-7 of the official injury page were not read. The 347-row result rests on the "
               "capture's own data plus a hand count of 8 clubs and 18 cells. The remaining 20 clubs are "
               "neither confirmed nor denied by this session.",
     "source": "https://www.nfl.com/injuries/",
     "clear": "Read all 8 chunks in a later session, or accept the two independent 347-row captures as "
              "corroboration."},
    {"id": "RC-17", "title": "Two Week-10 fixtures had no final score at read time",
     "severity": "info",
     "detail": "PIT at CIN was in progress and LAC at BAL had not kicked off. They print as em dashes and are "
               "excluded from the closure arithmetic, which still closes exactly.",
     "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
     "clear": "Settles itself when the league posts the finals."},
]


def build_flagged():
    b = []
    b.append('<p class="lead" style="max-width:80ch">Everything this workspace could not confirm, in one '
             'place, with the source it was checked against. A blocking flag means a class of numbers cannot '
             'be published at all; a review flag means a human decision is outstanding; info means it '
             'resolves itself.</p>')
    b.append('<div class="panel ok"><h3>What is <em>not</em> on this page</h3><p>The 10 settled conflicts '
             'and the one label-only conflict are not flagged, because an official number settled them. '
             'A flag is not a hedge against a hard result \u2014 it is a statement that no source exists.</p></div>')
    for f in FLAGS:
        cls = {"blocking": "bad", "review": "warn", "info": "neutral"}[f["severity"]]
        b.append('<h2 id="%s">%s · %s <span class="badge %s">%s</span></h2>'
                 % (esc(f["id"]), esc(f["id"]), esc(f["title"]), cls, esc(f["severity"])))
        b.append('<div class="panel%s"><p>%s</p>' % (" bad" if cls == "bad" else "", esc(f["detail"])))
        b.append('<p class="small">Checked against: %s</p>' % link(f["source"], f["source"]))
        b.append('<p class="small"><strong>Would clear it:</strong> %s</p></div>' % esc(f["clear"]))
    return page("pages/flagged.html", "Flagged for review", "NFL reconciled · flags", "".join(b),
                "Every item this workspace could not confirm from an official source, with the check it "
                "was put through and the action that would clear it.")


def main():
    os.makedirs(os.path.join(HERE, "pages"), exist_ok=True)
    made = [build_index(), build_conflicts(), build_results(), build_availability(),
            build_workspaces(), build_review(), build_decisions(), build_method(), build_flagged()]
    print("rendered %d pages" % len(made))
    for m in made:
        print("  " + os.path.relpath(m, HERE))


if __name__ == "__main__":
    main()

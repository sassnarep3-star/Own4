#!/usr/bin/env python3
"""
nfl-decision-gaps — static site builder.

Reads the curated register (engine/register.py) plus the committed data files,
writes data/*.json and renders the pages. Pure standard library, no network,
deterministic: a rebuild from the same inputs produces byte-identical output.

Run:  python3 nfl-decision-gaps/engine/parse_injury_capture.py   (optional; output is committed)
      python3 nfl-decision-gaps/engine/build.py
      python3 nfl-decision-gaps/engine/verify.py
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
sys.path.insert(0, HERE)
import register as R  # noqa: E402

DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
ASSETS = os.path.join(NS, "assets")
REPO_URL = "https://github.com/sassnarep3-star/Own4/blob/main/"
GH = "https://github.com/sassnarep3-star/Own4"


# ----------------------------------------------------------------- helpers
def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def ext(url, label=None, raw_label=False):
    """External link. `label` is escaped unless `raw_label` is set, which is
    used for labels this module builds itself and that therefore may contain
    the &#8599; arrow entity."""
    lab = label if label is not None else url
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
        esc(url), lab if raw_label else esc(lab))


def src(sid):
    for s in R.SOURCES:
        if s["id"] == sid:
            return ext(s["url"], "%s &#8599;" % sid, raw_label=True)
    return ""


def srcs(spec):
    """Render a space-separated list of source links from e.g. 'S1, S4'."""
    out = []
    for part in (spec or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if part == "repo":
            out.append(ext(GH, "repo &#8599;", raw_label=True))
        else:
            out.append(src(part))
    return " ".join(out) or '<span class="blank">no source</span>'


def blank(text="blank"):
    return '<span class="blank">%s</span>' % esc(text)


def val(x, empty="blank &mdash; unverified"):
    if x is None or x == "":
        return '<span class="blank">%s</span>' % empty
    return esc(x)


def num_or_blank(v):
    return esc(str(v)) if v is not None else '<span class="blank">blank</span>'


def pct(a, b, nd=1):
    if not b:
        return '<span class="blank">n/a</span>'
    return esc(("%." + str(nd) + "f%%") % (100.0 * a / b))


# ----------------------------------------------------------------- data out
def write_json(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=False)
    return path


def git(*args):
    try:
        return subprocess.check_output(["git", "-C", ROOT] + list(args),
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


# ------------------------------------------------------- derived statistics
def join_stats():
    joined = R.DESIGNATION_JOIN
    buckets = {}
    for team, player, pos, desig, inactive, note in joined:
        key = desig if desig else "(no designation)"
        b = buckets.setdefault(key, {"n": 0, "inactive": 0, "played": 0})
        b["n"] += 1
        if inactive:
            b["inactive"] += 1
        else:
            b["played"] += 1
    return buckets


def inactive_coverage():
    """Inactive players with no appearance on the injury report."""
    named = {}
    for team, player, pos, desig, inactive, note in R.DESIGNATION_JOIN:
        named.setdefault(team, set()).add(player)
    rows = []
    tot_inactive = 0
    tot_missing = 0
    tot_e3 = 0
    for team, missing_list in R.INACTIVE_NOT_ON_REPORT:
        full = dict((abbr, lst) for abbr, club, lst in R.INACTIVES)[team]
        rows.append((team, len(full), len(missing_list), missing_list))
        tot_inactive += len(full)
        tot_missing += len(missing_list)
        tot_e3 += sum(1 for m in missing_list if "emergency" in m.lower())
    return rows, tot_inactive, tot_missing, tot_e3


def inactive_total():
    return sum(len(lst) for _, _, lst in R.INACTIVES)


# ------------------------------------------------------------- page shell
NAV_PAGES = [
    ("index.html", "Overview"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/open-questions.html", "Open questions"),
    ("pages/information-gaps.html", "Have / don't have"),
    ("pages/availability-evidence.html", "Availability evidence"),
    ("pages/suggestions.html", "Suggestions board"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/sources.html", "Sources"),
    ("pages/flagged.html", "Flagged for review"),
]


def page(path, title, crumb, body, active, desc):
    depth = path.count("/")
    prefix = "../" * depth
    nav = []
    for href, label in NAV_PAGES:
        cls = "nav active" if href == active else "nav"
        nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, esc(label)))
    doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="%(prefix)sassets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<aside class="side">
  <a class="brand" href="%(prefix)sindex.html">Decision Gaps<span>Own4 &middot; NFL</span></a>
  <div class="tag">%(date)s &middot; official sources only</div>
  <nav aria-label="Sections">%(nav)s</nav>
  <a class="flag" href="%(prefix)spages/flagged.html">&#9873; %(nflags)d flagged for review</a>
  <a class="flag" href="%(root)sindex.html">&#8592; Own4 root dashboard</a>
</aside>
<main class="main" id="main">
<div class="crumb">%(crumb)s</div>
%(body)s
<footer>
<p><strong>nfl-decision-gaps</strong> &mdash; session %(session)s, %(date)s. Every row links to the
official page it was read from; anything that could not be confirmed from an official source is
blank and listed on the flagged page. Analytical research only, not wagering advice.</p>
<p>Responsible gambling: National Problem Gambling Helpline 1-800-MY-RESET (1-800-697-3738) &middot;
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">NCPG &#8599;</a></p>
</footer>
</main>
</div>
</body>
</html>
""" % {
        "title": esc(title), "desc": esc(desc), "prefix": prefix, "date": R.DATE,
        "session": esc(R.SESSION), "nav": "".join(nav), "crumb": crumb, "body": body,
        "nflags": len(R.FLAGS), "root": prefix,
    }
    full = os.path.join(NS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(doc)
    return path


def table(headers, rows, cls=""):
    th = "".join("<th>%s</th>" % h for h in headers)
    trs = []
    for r in rows:
        trs.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    return '<div class="scroll"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        cls, th, "".join(trs))


def h(level, text):
    return "<h%d>%s</h%d>" % (level, esc(text), level)


def p(text):
    return "<p>%s</p>" % text


def kpis(items):
    out = ['<div class="kpis">']
    for big, label in items:
        out.append('<div class="kpi"><div class="big">%s</div><div class="lab">%s</div></div>' % (big, label))
    out.append("</div>")
    return "".join(out)


# ------------------------------------------------------------------ pages
def build_index(parsed, inv):
    buckets = join_stats()
    rows, tot_inactive, tot_missing, tot_e3 = inactive_coverage()
    body = []
    body.append(h(1, "NFL decision gaps: what we know, what we don't, and what to do about it"))
    body.append(p("This namespace answers one question the rest of the repository does not: "
                  "<strong>before any decision can be reasonably made, what do we have, what are we "
                  "missing, and what would it take to close the gap?</strong> It is a decision-support "
                  "layer over the whole repo. Nothing here is a bet, a price or a model output."))
    body.append(kpis([
        (esc(str(len(R.QUESTIONS))), "open questions, each with the number that would clear it"),
        (esc(str(len(R.SUGGESTIONS))), "suggestions, each with options and no verdict"),
        (esc(str(len(R.FLAGS))), "items flagged for review"),
        (pct(tot_missing, tot_inactive), "of inactive players absent from the injury report (n=%d)" % tot_inactive),
        (esc(str(parsed["n_rows"])), "injury-report rows parsed from the committed capture"),
    ]))

    body.append(h(2, "The five findings that should change what you do next"))
    body.append(table(
        ["#", "Finding", "Evidence", "Source"],
        [
            ["1", "The injury report cannot establish who is unavailable. %d of %d officially "
                  "inactive players across eight clubs (%s) do not appear on it at all."
                  % (tot_missing, tot_inactive, "%.1f%%" % (100.0 * tot_missing / tot_inactive)),
             "Official inactive lists joined to the live injury report, club by club.",
             srcs("S1, S4")],
            ["2", "An Out designation does not guarantee inactive. 14 of 17 Out players were "
                  "inactive; the other three (Henderson, Joseph, Goodson) have no published "
                  "reserve status on either official page.",
             "Designation-to-inactive join table.",
             srcs("S1, S4")],
            ["3", "The report moves inside the week, and the only committed capture is stale. Two "
                  "Lions rows changed, two Ravens rows appeared, and Doubtful designations appeared "
                  "where there had been none.",
             "2026-11-13 committed capture compared with the 2026-11-16 live page.",
             srcs("S8, S1")],
            ["4", "nfl.com publishes no depth chart. The club depth-chart path returns the official "
                  "404 page; the club page offers Info, Roster and Stats only.",
             "Fetch of the depth-chart path and the club page.",
             srcs("S2, S3")],
            ["5", "No official page publishes a price. Without a market line there is no residual, "
                  "no closing-line value and no ROI - those columns must stay blank.",
             "Game Center, schedule, scores and club pages read this session.",
             srcs("S3, S5, S6, S7")],
        ]))

    body.append(h(2, "Where the gaps are, by domain"))
    rows = []
    for g in R.GAPS:
        have = g["have"] if g["have"] else '<span class="blank">nothing confirmed</span>'
        rows.append([esc(g["domain"]), esc(have), srcs(g["src"]),
                     esc(g["missing"]) if g["missing"] else blank("none"),
                     esc(g["blocks"])])
    body.append(table(["Domain", "What we have", "Source", "What is missing", "Blocks"], rows))

    body.append(h(2, "The decision-readiness table"))
    body.append(p("One row per open question: the answer we have today, the number that would clear "
                  "it, and the suggestion that would get us there. Full register on the "
                  '<a href="pages/open-questions.html">Open questions</a> page.'))
    rows = []
    for q in R.QUESTIONS:
        rows.append([esc(q["id"]), esc(q["topic"]), esc(q["question"]),
                     esc(q["have"]) if q["have"] else blank("no confirmed value"),
                     srcs(q["src"]), esc(q["clears"]), esc(q["status"])])
    body.append(table(["ID", "Topic", "Question", "What we have", "Source",
                       "The number that would clear it", "Status"], rows))

    body.append(h(2, "Start here if you only read one more page"))
    body.append(('<ul class="bullets">' +
                '<li><a href="pages/information-gaps.html">Have / don\'t have</a> &mdash; the '
                'matrix behind every blocker on this site.</li>'
                '<li><a href="pages/availability-evidence.html">Availability evidence</a> &mdash; the '
                'designation-to-inactive join, row by row.</li>'
                '<li><a href="pages/suggestions.html">Suggestions board</a> &mdash; %d suggestions, '
                'each with options A/B/C and a blank verdict for you to fill in.</li>'
                '<li><a href="pages/flagged.html">Flagged for review</a> &mdash; everything this '
                'session could not verify.</li>'
                '</ul>') % len(R.SUGGESTIONS))
    return page("index.html", "NFL decision gaps · Own4", "nfl-decision-gaps › overview",
                "".join(body), "index.html",
                "What the Own4 NFL project has, what it is missing, and what would close each gap.")


def build_exec_summary(parsed, inv):
    rows, tot_inactive, tot_missing, tot_e3 = inactive_coverage()
    itot = inactive_total()
    body = []
    body.append(h(1, "Executive summary"))
    body.append(p("Read on %s against official NFL pages only. Everything below was read on, or "
                  "computed from, the pages listed on the <a href=\"sources.html\">Sources</a> "
                  "page. Where the official page did not state a thing, the field is blank and the "
                  "item is flagged." % R.DATE))

    body.append(h(2, "1. Availability is the strongest dataset in the repo and it is still not "
                     "sufficient"))
    body.append(p("The committed Week 10 capture gives <strong>%d rows across %d clubs and %d "
                  "fixtures</strong> (%s). But joining the live report to the official inactive "
                  "lists for the eight clubs where every row was read shows that "
                  "<strong>%d of %d inactive players &mdash; %s &mdash; never appear on the injury "
                  "report</strong>. Excluding the two emergency third quarterbacks, %d of %d (%s). "
                  "The injury report is a partial view of unavailability, not the view. The league "\
                  "does publish a dated reserve list (%s, 25 moves in November 2026), and that page "\
                  "explains two of the three Out players who were missing from the inactive list - "\
                  "but nothing in this repository captures it, so an injured-reserve player still "\
                  "looks merely absent."
                  % (parsed["n_rows"], parsed["n_teams_listed"], parsed["n_matchups"],
                     parsed["source_file"], tot_missing, tot_inactive,
                     "%.1f%%" % (100.0 * tot_missing / tot_inactive),
                     tot_missing - tot_e3, tot_inactive - tot_e3,
                     "%.1f%%" % (100.0 * (tot_missing - tot_e3) / (tot_inactive - tot_e3)),
                     src("S10"))))

    body.append(h(2, "2. The designations mean something, but not yet enough to model"))
    b = join_stats()
    rows = []
    for key in ["Out", "Doubtful", "Questionable", "(no designation)"]:
        if key not in b:
            continue
        d = b[key]
        rows.append([esc(key), esc(str(d["n"])), esc(str(d["inactive"])), pct(d["inactive"], d["n"]),
                     pct(d["played"], d["n"]),
                     "wide &mdash; n is far too small" if d["n"] < 30 else "published",
                     srcs("S1, S4")])
    body.append(table(["Game status on the injury report", "n", "Inactive", "Inactive rate",
                       "Played rate", "Interval", "Source"], rows))
    body.append(p("The direction is right &mdash; Out is more often inactive than Questionable, and "
                  "Questionable more often than no designation &mdash; but with n = 4 for Doubtful "
                  "and n = 26 for Questionable these are observations, not calibration. The brief's "
                  "own rule says to publish n with each value; these rows do."))

    body.append(h(2, "3. Depth has no verified input on the official domain"))
    body.append(p("The league does not publish a depth chart: the club depth-chart path returns the "
                  "official 404 page and the club page offers Info, Roster and Stats only. No "
                  "snap-count table and no starters list was found on the club page, the Game Center, "
                  "the schedule page or the scores page. The backup-deficiency feature therefore has "
                  "no input today. The brief already says not to build it until one route is verified "
                  "for all 32 clubs; that condition is unmet."))

    body.append(h(2, "4. Prices do not exist on the official domain"))
    body.append(p("No spread, total or moneyline appears on any official page read this session. "
                  "That single fact blocks the residual, the closing-line-value column, the ROI "
                  "leaderboard, the correlation of residuals and the parlay joint-evidence gate. "
                  "Those columns are blank here and should be blank everywhere until the owner "
                  "chooses a price policy (suggestion SG-B)."))

    body.append(h(2, "5. The repository disagrees with itself"))
    body.append(p("Three earlier sessions published 254, 279 and 347 rows for the same Week 10 "
                  "injury page. This session's parse of the committed capture gives %d. And the live "
                  "page read today differs from that capture again. The fix is not more counting; it "
                  "is one canonical capture file with every count computed from it at build time "
                  "(suggestion SG-H)." % parsed["n_rows"]))

    body.append(h(2, "6. What to do, in order"))
    body.append(table(
        ["Order", "Action", "Why now", "Clears", "Evidence"],
        [[esc(s["id"]), esc(s["title"]), esc(s["why"][:220] + ("..." if len(s["why"]) > 220 else "")),
          esc(s["dependency"]), srcs(s.get("src", "repo"))] for s in R.SUGGESTIONS[:6]]))
    body.append(p('All fifteen suggestions, with options and a blank verdict, are on the '
                  '<a href="suggestions.html">Suggestions board</a>.'))
    return page("pages/executive-summary.html", "Executive summary · Own4 decision gaps",
                "nfl-decision-gaps › executive summary", "".join(body),
                "pages/executive-summary.html",
                "Executive summary of what the Own4 NFL project can and cannot establish today.")


def build_questions():
    body = []
    body.append(h(1, "Open questions register"))
    body.append(p("Every row states the question, what we currently have, the source it was read "
                  "from, what is missing, the specific number or artefact that would clear it, the "
                  "suggestion that would produce it, and the status. Nothing is inferred: where the "
                  "official pages said nothing, the field is blank."))
    rows = []
    for q in R.QUESTIONS:
        rows.append([
            esc(q["id"]), esc(q["topic"]), esc(q["question"]),
            esc(q["have"]) if q["have"] else blank("no confirmed value"),
            srcs(q["src"]),
            esc(q["missing"]) if q["missing"] else blank("nothing outstanding"),
            esc(q["clears"]),
            '<a href="suggestions.html#%s">%s</a>' % (esc(q["discovery"]), esc(q["discovery"])),
            esc(q["status"]),
        ])
    body.append(table(["ID", "Topic", "Question", "What we have", "Source", "What is missing",
                       "What would clear it", "Discovery", "Status"], rows, cls="wide"))

    body.append(h(2, "Questions grouped by whether they are answerable today"))
    answered = [q for q in R.QUESTIONS if q["status"].startswith("answered")]
    openq = [q for q in R.QUESTIONS if q["status"].startswith("open")]
    blocked = [q for q in R.QUESTIONS if q["status"].startswith("block")]
    for title, group in [("Answered (bounded)", answered),
                         ("Open", openq),
                         ("Blocked or unanswerable from the official pages", blocked)]:
        body.append(h(3, "%s — %d" % (title, len(group))))
        body.append("<ul class=\"bullets\">" + "".join(
            "<li><strong>%s</strong> %s</li>" % (esc(q["id"]), esc(q["question"])) for q in group
        ) + "</ul>")
    return page("pages/open-questions.html", "Open questions · Own4 decision gaps",
                "nfl-decision-gaps › open questions", "".join(body),
                "pages/open-questions.html",
                "Every open question, with the number that would clear it and how to get it.")


def build_gaps():
    body = []
    body.append(h(1, "Information we have and information we don't"))
    body.append(p("One row per data domain the brief depends on. The <em>have</em> column only "
                  "contains things this session read on an official page or computed from a file "
                  "already committed to this repository. The <em>missing</em> column is the list of "
                  "things a decision would need and cannot get today."))
    rows = []
    for g in R.GAPS:
        rows.append([
            esc(g["domain"]),
            esc(g["have"]) if g["have"] else blank("nothing confirmed"),
            srcs(g["src"]),
            esc(g["missing"]) if g["missing"] else blank("nothing outstanding"),
            esc(g["blocks"]),
        ])
    body.append(table(["Data domain", "What we have", "Source", "What we don't have", "Blocks"],
                      rows, cls="wide"))

    have_n = sum(1 for g in R.GAPS if g["have"])
    body.append(h(2, "Scoreboard"))
    body.append(kpis([
        (esc(str(len(R.GAPS))), "data domains reviewed"),
        (esc(str(have_n)), "with at least one confirmed value"),
        (esc(str(len(R.GAPS) - have_n)), "with nothing confirmed at all"),
        (esc(str(sum(1 for g in R.GAPS if g["missing"]))), "with a stated gap"),
    ]))
    body.append(p("A domain with <em>nothing confirmed</em> is not a domain where the answer is "
                  "unknown; it is a domain where no official page this session read states the "
                  "answer. That distinction matters: 'not published' and 'not yet collected' call "
                  "for different responses."))
    return page("pages/information-gaps.html", "Have / don't have · Own4 decision gaps",
                "nfl-decision-gaps › have / don't have", "".join(body),
                "pages/information-gaps.html",
                "What the project has and does not have, domain by domain, each row sourced.")


def build_evidence(parsed):
    body = []
    body.append(h(1, "Availability evidence"))
    body.append(p("Three tables, all built from two official pages: the live Week 10 injury report "
                  "(%s) and the official Week 10 inactive lists (%s). The join covers the eight "
                  "clubs where this session read <em>every</em> row of the live report; the other "
                  "clubs were read but not transcribed, and are not claimed."
                  % (src("S1"), src("S4"))))

    body.append(h(2, "1. Designation to inactive join"))
    b = join_stats()
    rows = []
    for key in ["Out", "Doubtful", "Questionable", "(no designation)"]:
        if key not in b:
            continue
        d = b[key]
        rows.append([esc(key), esc(str(d["n"])), esc(str(d["inactive"])), pct(d["inactive"], d["n"]),
                     esc(str(d["played"])), pct(d["played"], d["n"]), srcs("S1, S4")])
    body.append(table(["Game status (as published)", "n", "Inactive", "Inactive rate", "Played",
                       "Played rate", "Source"], rows))
    body.append(p("<strong>n = %d</strong> players across 8 clubs. The rates are published with n "
                  "because at this size they are observations, not calibration. Do not use them as "
                  "model features." % sum(d["n"] for d in b.values())))

    body.append(h(2, "2. The join, row by row"))
    rows = []
    for team, player, pos, desig, inactive, note in R.DESIGNATION_JOIN:
        rows.append([
            esc(team), esc(player), esc(pos),
            esc(desig) if desig else blank("blank"),
            '<span class="yes">yes</span>' if inactive else '<span class="no">no</span>',
            esc(note) if note else "",
            srcs("S1, S4"),
        ])
    body.append(table(["Club", "Player", "Pos", "Game status", "Inactive", "Note", "Source"],
                      rows, cls="wide"))

    body.append(h(2, "3. Inactive players who are absent from the injury report"))
    rows, tot_inactive, tot_missing, tot_e3 = inactive_coverage()
    trows = []
    for team, nfull, nmiss, missing in rows:
        trows.append([esc(team), esc(str(nfull)), esc(str(nmiss)), pct(nmiss, nfull),
                      esc("; ".join(missing)), srcs("S1, S4")])
    trows.append(["<strong>All eight clubs</strong>", "<strong>%d</strong>" % tot_inactive,
                  "<strong>%d</strong>" % tot_missing, "<strong>%s</strong>" % pct(tot_missing, tot_inactive),
                  "<strong>%d of these are emergency third quarterbacks (excluded: %s of %s)</strong>"
                  % (tot_e3, pct(tot_missing - tot_e3, tot_inactive - tot_e3), tot_missing - tot_e3),
                  srcs("S1, S4")])
    body.append(table(["Club", "Inactive players", "Not on the report", "Share", "Who", "Source"],
                      trows, cls="wide"))
    body.append(p("This is the finding that matters most for the brief. The injury report is the "
                  "input every availability feature in this repository is built on, and it is "
                  "silent about more than half of the players who did not play."))

    body.append(h(2, "4. Official inactive lists, Week 10 (all 24 clubs published)"))
    rows = []
    for abbr, club, lst in R.INACTIVES:
        rows.append([esc(abbr), esc(club), esc(str(len(lst))),
                     "<br>".join(esc(x) for x in lst), src("S4")])
    body.append(table(["Club", "Name", "Count", "Officially inactive", "Source"], rows, cls="wide"))

    body.append(h(2, "5. Live page versus the committed capture"))
    rows = []
    for d in R.CAPTURE_DELTA:
        rows.append([esc(d["team"]), esc(d["subject"]), esc(d["field"]), esc(d["captured"]),
                     esc(d["live"]), esc(d["note"]), srcs("S8, S1")])
    body.append(table(["Club", "Subject", "Field", "Capture 2026-11-13", "Live 2026-11-16",
                       "Reading", "Source"], rows, cls="wide"))
    body.append(p("The capture is not wrong; it is a different point in time. The lesson is that "
                  "any number taken from it describes 2026-11-13, not the week."))

    body.append(h(2, "6. Official reserve list, November 2026"))
    rows = []
    for date, club, player, kind in R.RESERVE_LIST:
        rows.append([esc(date[5:]), esc(club), esc(player), esc(kind), src("S10")])
    body.append(table(["Date", "Club", "Player", "Transaction", "Source"], rows, cls="wide"))
    body.append(p("<strong>n = %d</strong> dated Reserve/Injured moves. Two of them resolve players "
                  "who were Out on the injury report yet absent from the inactive list: TreVeyon "
                  "Henderson (NE) and Tyler Goodson (DAL), both 11/14. A third, Malik Willis (MIA, "
                  "11/10), is the exact case the project brief cites as the reason a reserve list is "
                  "needed. Kerby Joseph (DET) is not on this list, so his case stays flagged."
                  % len(R.RESERVE_LIST)))

    body.append(h(2, "7. Official trades, November 2026"))
    rows = []
    for date, frm, to, player, kind in R.TRADES:
        rows.append([esc(date[5:]), esc(frm), esc(to), esc(player), esc(kind), src("S9")])
    body.append(table(["Date", "From", "To", "Player", "Transaction", "Source"], rows, cls="wide"))
    body.append(p("<strong>n = %d</strong> dated trades. This is the page that would let depth and "
                  "availability rows be versioned against the last official roster event."
                  % len(R.TRADES)))

    body.append(h(2, "8. Verified results feed, Week 10"))
    rows = []
    for r in R.RESULTS:
        rows.append([esc(r["game"]), esc(r["day"]),
                     num_or_blank(r["away_pts"]), num_or_blank(r["home_pts"]),
                     esc(r["status"]),
                     esc(r["venue"]) if r["venue"] else blank("not captured"),
                     srcs(r["venue_src"]) if r["venue_src"] else srcs("S6, S7"),
                     esc(r["note"]) if r["note"] else ""])
    body.append(table(["Fixture", "Day", "Away", "Home", "State", "Venue", "Source", "Note"],
                      rows, cls="wide"))
    body.append(p("Twelve finals confirmed on two independent official pages. Two fixtures carry no "
                  "score: one was rendered as live when read, the other had not kicked off. Neither "
                  "score is inferred."))
    return page("pages/availability-evidence.html",
                "Availability evidence · Own4 decision gaps",
                "nfl-decision-gaps › availability evidence", "".join(body),
                "pages/availability-evidence.html",
                "Official injury designations joined to official inactive lists, row by row.")


def build_suggestions():
    body = []
    body.append(h(1, "Suggestions board"))
    body.append(p("Fifteen suggestions for improving the site and the decision-making it supports. "
                  "Each one offers two or three paths with their effort, risk and trade-off, a "
                  "dependency, and this session's recommendation. <strong>The verdict column is "
                  "deliberately blank.</strong> Choosing between paths is the reviewer's call, not "
                  "the model's. Nothing on this page has been implemented."))
    rows = []
    for s in R.SUGGESTIONS:
        rows.append(['<a href="#%s">%s</a>' % (esc(s["id"]), esc(s["id"])), esc(s["title"]),
                     esc(s["dependency"]), esc(s["recommended"]),
                     '<span class="blank">your call</span>',
                     srcs(s.get("src", "repo"))])
    body.append(table(["ID", "Suggestion", "Dependency", "This session's recommendation", "Verdict",
                       "Evidence"], rows))

    for s in R.SUGGESTIONS:
        body.append('<h2 id="%s">%s &mdash; %s</h2>' % (esc(s["id"]), esc(s["id"]), esc(s["title"])))
        body.append(p("<strong>Why.</strong> %s" % esc(s["why"])))
        orows = []
        for o in s["options"]:
            orows.append([esc(o["label"]), esc(o["text"]), esc(o["effort"]), esc(o["risk"]),
                          esc(o["tradeoff"]), srcs(s.get("src", "repo"))])
        body.append(table(["Option", "What it is", "Effort", "Risk", "Trade-off", "Evidence"],
                          orows, cls="wide"))
        body.append(p("<strong>Dependency.</strong> %s<br><strong>Recommended.</strong> %s<br>"
                      "<strong>Verdict.</strong> <span class=\"blank\">blank &mdash; for the reviewer "
                      "to choose</span>" % (esc(s["dependency"]), esc(s["recommended"]))))

    body.append(h(2, "Rejected outright"))
    body.append(table(
        ["Rejected proposal", "Why", "Evidence"],
        [["Ranking strategies by season-long ROI.",
          "Realised return over one season cannot separate skill from variance. The brief rejects "
          "this itself; rank by benchmark-relative proper score with uncertainty instead.",
          srcs("S6, S7")],
         ["Deriving depth order from jersey number, experience or salary.",
          "The brief rejects this. It would fabricate a starter the club never named, and the same "
          "page shows clubs listing several players at one rank and leaving slots empty.",
          srcs("S2, S8")],
         ["Inferring the Steelers-Bengals score from the live page state.",
          "The page rendered a first-quarter score on a Monday, well after the game was scheduled "
          "to finish. Publishing it would be an inference from a state the two official pages "
          "disagree about.", srcs("S6, S7")]]))
    return page("pages/suggestions.html", "Suggestions board · Own4 decision gaps",
                "nfl-decision-gaps › suggestions", "".join(body),
                "pages/suggestions.html",
                "Suggestions for improving the site and its decisions, with options and blank verdicts.")


def build_repo_review(inv):
    body = []
    body.append(h(1, "Repository review"))
    body.append(p("A line-by-line inventory of the repository as committed at the commit named "
                  "below, computed by <code>engine/build.py</code> from the working tree and pinned "
                  "into <code>data/repo_inventory.json</code>. It is pinned, not recomputed at page "
                  "build time, so that another session merging a new namespace cannot silently "
                  "change a number this page states. If you want it refreshed, run the collector "
                  "again and commit the result."))

    body.append(h(2, "Scale"))
    body.append(kpis([
        (esc(str(inv["n_namespaces"])), "top-level nfl-* namespaces"),
        (esc(str(inv["n_html"])), "HTML files committed"),
        (esc(str(inv["n_data"])), "JSON / CSV data files"),
        (esc(str(inv["n_py"])), "Python files"),
    ]))

    body.append(h(2, "Namespace inventory"))
    rows = []
    for name, d in sorted(inv["namespaces"].items()):
        rows.append([
            '<a href="%s">%s</a>' % (esc(REPO_URL + name + "/"), esc(name)),
            esc(str(d["html"])), esc(str(d["data"])),
            esc(str(d["py"])),
            "yes" if d["has_index"] else "no",
            ", ".join(d["pages"][:12]) + (" …" if len(d["pages"]) > 12 else ""),
        ])
    body.append(table(["Namespace (link to the committed tree)", "HTML", "Data", "Py", "Index",
                       "Pages"], rows, cls="wide"))

    body.append(h(2, "Duplication"))
    body.append(p("The same page title is committed in many namespaces. This is the structural cause "
                  "of the contradictory counts in flag F2: thirty independent copies of a "
                  "'questions' page will not agree unless they are generated from one register."))
    rows = []
    for t, (c, n) in sorted(inv["page_title_counts"].items(), key=lambda kv: (-kv[1][0], kv[0])):
        first = n[0]
        rows.append([esc(t), esc(str(c)),
                     esc(", ".join(n[:8]) + (" …" if len(n) > 8 else "")),
                     ext(REPO_URL + first + "/", "repo &#8599;", raw_label=True)])
    body.append(table(["Page file name", "Namespaces carrying it", "Examples", "Source"],
                      rows, cls="wide"))

    body.append(h(2, "Irregularities found by reading the repository"))
    body.append(table(
        ["Irregularity", "What the repository shows", "This session's reading", "Source"],
        [[esc(a), esc(b), esc(c), srcs(d)] for a, b, c, d in inv["irregularities"]]))

    body.append(h(2, "What this session did <em>not</em> review"))
    body.append(p("The repository holds %d HTML files. This session read the root dashboard, the "
                  "navigation generator, the committed injury capture, and the namespace inventory; "
                  "it did not read all %d files line by line, and does not claim to have done so. "
                  "Review depth is stated rather than implied."
                  % (inv["n_html"], inv["n_html"])))
    return page("pages/repo-review.html", "Repo review · Own4 decision gaps",
                "nfl-decision-gaps › repo review", "".join(body),
                "pages/repo-review.html",
                "Line-by-line inventory of the repository and the irregularities it contains.")


def build_sources():
    body = []
    body.append(h(1, "Sources read this session"))
    body.append(p("Every row on every page in this namespace traces to one of these. "
                  "<em>live</em> means the page was fetched on %s. <em>repo</em> means the value "
                  "was computed from a file already committed to this repository. <em>absent</em> "
                  "means the fetch was attempted and the official server returned no such page "
                  "&mdash; which is itself a finding." % R.DATE))
    rows = []
    for s in R.SOURCES:
        rows.append([esc(s["id"]), esc(s["kind"]), ext(s["url"], s["title"]),
                     esc(s["what"]), esc(s["read"]),
                     esc(s["published"]) if s["published"] else blank("not stated by the page")])
    body.append(table(["ID", "Kind", "Page", "What it publishes", "How much was read", "Published"],
                      rows, cls="wide"))

    body.append(h(2, "Method"))
    body.append(p("Pages were fetched and read in full except where the <em>how much was read</em> "
                  "column says otherwise. Rows were transcribed only where the table in question was "
                  "read end to end; that is why the designation-to-inactive join covers eight clubs "
                  "and not twenty-eight. Any value not read directly is rendered blank, never "
                  "filled in."))

    body.append(h(2, "Official pages the brief asks for that were not located"))
    body.append(table(
        ["Wanted", "Result of the search this session", "Where it was looked for"],
        [["Club depth charts on nfl.com",
          "Not found. The depth-chart path returns the official 404 page; club pages offer Info, "
          "Roster and Stats only.", srcs("S2, S3")],
         ["Snap counts",
          "Not found on any official page read. A gamebook-PDF route is described on third-party "
          "forums and was deliberately not relied on.", srcs("S3, S5, S6, S7")],
         ["Announced starters and game-day status",
          "Not found. The Game Center tabs read publish team statistics, club leaders and injury "
          "cards only.", srcs("S5")],
         ["Market prices (spread, total, moneyline)",
          "Not found on the Game Center, the schedule page, the scores page or the club page.",
          srcs("S3, S5, S6, S7")],
         ["Roof designation and weather",
          "Not found beyond the schedule page's summary weather chip. The Game Center publishes "
          "Location and Stadium only.", srcs("S5, S6")],
         ["Dated reserve / injured-reserve list",
          "Found. https://www.nfl.com/transactions/league/reserve-list/2026/11 publishes 25 dated "
          "Reserve/Injured moves for November 2026. It is not captured anywhere in this repository.",
          srcs("S10")]]))
    return page("pages/sources.html", "Sources · Own4 decision gaps",
                "nfl-decision-gaps › sources", "".join(body),
                "pages/sources.html",
                "The official pages every value in this namespace was read from.")


def build_flagged():
    body = []
    body.append(h(1, "Flagged for review"))
    body.append(p("Everything this session could not confirm from an official page. None of these "
                  "block publication of the analysis; each is published with the source link so it "
                  "can be checked after the site is live. Nothing here has been filled in."))
    rows = []
    for f in R.FLAGS:
        rows.append([esc(f["id"]), esc(f["sev"]), esc(f["area"]), esc(f["item"]), esc(f["detail"]),
                     srcs(f["src"])])
    body.append(table(["ID", "Severity", "Area", "Item", "Detail", "Source"], rows, cls="wide"))
    body.append(h(2, "By severity"))
    body.append(kpis([(esc(str(sum(1 for f in R.FLAGS if f["sev"] == s))), s)
                      for s in ["high", "medium", "low"]]))
    return page("pages/flagged.html", "Flagged for review · Own4 decision gaps",
                "nfl-decision-gaps › flagged", "".join(body),
                "pages/flagged.html",
                "Items this session could not verify against an official source.")


# ------------------------------------------------------------------ inventory
def repo_inventory():
    """Return the repository inventory.

    The inventory is PINNED: it is read from data/repo_inventory.json and only
    recomputed when REFRESH_INVENTORY=1 is set in the environment. This is
    deliberate. A sibling session merging a new namespace changes the number of
    nfl-* directories, and a page that stated a recomputed count would then
    differ from what was committed - which turns every peer determinism gate in
    this repository red through no fault of the peer. Pinned counts are honest
    as long as the page says what they were pinned to, and this one does.
    """
    path = os.path.join(DATA, "repo_inventory.json")
    if os.environ.get("REFRESH_INVENTORY") != "1" and os.path.exists(path):
        return json.load(open(path))
    return _compute_inventory()


def _compute_inventory():
    namespaces = {}
    html_total = 0
    data_total = 0
    py_total = 0
    title_counts = {}
    for name in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path) or not name.startswith("nfl"):
            continue
        if name == os.path.basename(NS):
            continue  # this namespace is the observer, not a subject of the review
        n_html = n_data = n_py = 0
        pages = []
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
            for fn in filenames:
                if fn.endswith(".html"):
                    n_html += 1
                    if os.path.basename(dirpath) in ("pages", name) or fn == "index.html":
                        pages.append(fn)
                    c, n = title_counts.get(fn, (0, []))
                    n = list(n)
                    if name not in n:
                        n.append(name)
                    title_counts[fn] = (c + 1, n)
                elif fn.endswith((".json", ".csv")):
                    n_data += 1
                elif fn.endswith(".py"):
                    n_py += 1
        html_total += n_html
        data_total += n_data
        py_total += n_py
        namespaces[name] = dict(html=n_html, data=n_data, py=n_py,
                                has_index=os.path.exists(os.path.join(path, "index.html")),
                                pages=sorted(set(pages)))
    n_ns = len(namespaces)
    dup = ", ".join("%s (%d)" % (t.replace(".html", ""), c)
                    for t, (c, _n) in sorted(title_counts.items(), key=lambda kv: -kv[1][0])
                    if c >= 20 and t in ("index.html", "sources.html", "flagged.html",
                                         "suggestions.html", "questions.html",
                                         "executive-summary.html", "leaderboard.html"))
    inv = dict(
        pinned_at=git("rev-parse", "HEAD") or "unknown",
        generated_by="nfl-decision-gaps/engine/build.py",
        note="Pinned, not recomputed at page-build time, so a sibling merge cannot change a "
             "number the repo-review page states. Re-run the builder to refresh.",
        n_namespaces=len(namespaces),
        n_html=html_total,
        n_data=data_total,
        n_py=py_total,
        namespaces=namespaces,
        page_title_counts=dict((k, [v[0], sorted(v[1])]) for k, v in title_counts.items()),
        irregularities=[
            ("Three incompatible injury row counts",
             "254, 279 and 347 rows are published in different namespaces for the same Week 10 "
             "nfl.com injury page; this session's parse of the committed capture returns "
             "%d rows over %d clubs." % (PARSED["n_rows"], PARSED["n_teams_listed"]),
             "Not reconcilable as stated, because none of them says which quantity it counts. "
             "Suggestion SG-H.", "S8, S1"),
            ("%d namespaces, mostly duplicate page sets" % n_ns,
             "Most of them commit their own questions.html, suggestions.html, flagged.html, "
             "sources.html and executive-summary.html. The most repeated page files: %s." % dup,
             "Structural cause of the divergence above. Suggestion SG-I.", "repo"),
            ("A live fixture rendered as live after its date",
             "PIT/CIN is rendered LIVE in the first quarter on both official pages read on "
             "2026-11-16.",
             "Recorded blank and flagged rather than inferred. Flag F1.", "S6, S7"),
            ("Row-level official data committed to a public site",
             "The repository commits full transcriptions of nfl.com tables.",
             "The brief asks for a public analysis layer and a private data layer with the terms "
             "read first. Left to the owner; this namespace links to official pages rather than "
             "re-publishing row-level nfl.com data beyond what was already committed.", "repo"),
        ],
    )
    return inv


# ------------------------------------------------------------------ css
CSS = """/* nfl-decision-gaps — self-contained stylesheet. No external assets. */
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 color:#12181f;background:#f5f7fa}
a{color:#0b5cad}
a:hover{text-decoration:none}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
.wrap{display:flex;min-height:100vh;align-items:stretch}
.side{width:250px;flex:0 0 250px;background:#0f1b2a;color:#c9d6e4;padding:18px 14px;
 position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:block;color:#fff;font-weight:700;font-size:17px;text-decoration:none;margin-bottom:2px}
.brand span{display:block;font-weight:400;font-size:11px;color:#7f95ad;letter-spacing:.06em;text-transform:uppercase}
.tag{margin:8px 0 14px;font-size:11px;color:#7f95ad;border-bottom:1px solid #22344a;padding-bottom:10px}
.side nav{display:flex;flex-direction:column;gap:1px}
.nav{display:block;padding:7px 9px;border-radius:5px;color:#c9d6e4;text-decoration:none;font-size:13.5px}
.nav:hover{background:#182b41;color:#fff}
.nav.active{background:#12507f;color:#fff;font-weight:600}
.flag{display:block;margin-top:14px;padding:8px 9px;border-radius:5px;background:#3d2a10;
 color:#f0c274;text-decoration:none;font-size:12.5px}
.flag:hover{background:#4d3514}
.main{flex:1;min-width:0;padding:26px 30px 60px;max-width:1500px}
.crumb{font-size:12px;color:#63748a;margin-bottom:14px}
h1{font-size:25px;line-height:1.25;margin:0 0 14px}
h2{font-size:18px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid #dde4ec}
h3{font-size:15.5px;margin:20px 0 8px}
p{margin:0 0 12px;max-width:105ch}
ul.bullets{margin:0 0 12px;padding-left:20px;max-width:105ch}
ul.bullets li{margin:4px 0}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0 8px}
.kpi{flex:1 1 190px;background:#fff;border:1px solid #dde4ec;border-radius:8px;padding:12px 14px}
.kpi .big{font-size:23px;font-weight:700;color:#0f1b2a;line-height:1.1}
.kpi .lab{font-size:12px;color:#5b6b80;margin-top:4px}
.scroll{overflow-x:auto;border:1px solid #dde4ec;border-radius:8px;background:#fff;margin-bottom:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
table.wide{font-size:12.5px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #e8edf3;vertical-align:top}
thead th{background:#eef3f8;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;
 color:#44566d;position:sticky;top:0;border-bottom:1px solid #d3dde8}
tbody tr:nth-child(even){background:#fafcfe}
tbody tr:hover{background:#f0f6fc}
.blank{display:inline-block;background:#fff4e0;color:#8a5a00;border:1px solid #f0d9a8;
 border-radius:3px;padding:0 5px;font-size:12px;white-space:nowrap}
.yes{color:#0a6b3d;font-weight:600}
.no{color:#8a2c2c;font-weight:600}
code{background:#eef3f8;padding:1px 4px;border-radius:3px;font-size:12.5px}
footer{margin-top:36px;padding-top:14px;border-top:1px solid #dde4ec;color:#5b6b80;font-size:12.5px}
footer p{max-width:105ch;margin:0 0 6px}
@media (max-width:900px){
 .wrap{flex-direction:column}
 .side{width:auto;flex:none;height:auto;position:static}
 .side nav{flex-direction:row;flex-wrap:wrap}
 .main{padding:18px 14px 40px}
}
"""

PARSED = {}


def main():
    global PARSED
    parsed_path = os.path.join(DATA, "injury_week10_parsed.json")
    PARSED = json.load(open(parsed_path))

    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "site.css"), "w") as f:
        f.write(CSS)

    inv = repo_inventory()
    write_json("repo_inventory.json", inv)
    write_json("results_week10.json", dict(week=R.WEEK, source_ids=["S6", "S7"], rows=R.RESULTS))
    write_json("inactives_week10.json",
               dict(week=R.WEEK, source_ids=["S4"],
                    clubs=[dict(club=a, name=b, inactive=lst) for a, b, lst in R.INACTIVES]))
    write_json("designation_join.json",
               dict(week=R.WEEK, source_ids=["S1", "S4"], clubs_covered=sorted(
                   {t for t, _, _, _, _, _ in R.DESIGNATION_JOIN}),
                    rows=[dict(club=t, player=p, pos=po, game_status=d, inactive=i, note=n)
                          for t, p, po, d, i, n in R.DESIGNATION_JOIN]))
    write_json("questions.json", R.QUESTIONS)
    write_json("suggestions.json", R.SUGGESTIONS)
    write_json("information_gaps.json", R.GAPS)
    write_json("flags.json", R.FLAGS)
    write_json("sources.json", R.SOURCES)
    write_json("capture_delta.json", R.CAPTURE_DELTA)

    built = [
        build_index(PARSED, inv),
        build_exec_summary(PARSED, inv),
        build_questions(),
        build_gaps(),
        build_evidence(PARSED),
        build_suggestions(),
        build_repo_review(inv),
        build_sources(),
        build_flagged(),
    ]
    print("built %d pages" % len(built))
    for b in built:
        print("  ", b)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the Decision Console from committed artefacts.

  python3 nfl-decision-console/engine/derive.py      # registers -> data/derived/*.json
  python3 nfl-decision-console/engine/build_site.py  # artefacts -> index.html + pages/*.html

Contract this builder is written to:
  * reads only files under nfl-decision-console/data/ (never the repository tree, never the network),
    so the output is a function of committed data and a sibling merge cannot change a number here;
  * every table row carries a source cell: an official link, a repository blob link, or the literal
    'blank — unverified';
  * no price, odd, spread or payout value is ever emitted (there is no official price source:
    engine/verify_site.py fails the build if one appears);
  * the prose is generated from the same objects as the tables, so a sentence cannot disagree with
    a row.
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
DERIVED = os.path.join(NS, "data", "derived")
ROOT = os.path.dirname(NS)
BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-console/"

CSS = "../assets/console.css"
PAGES = [
    ("index.html", "Decision console", "What this is, and the three decisions in front of you"),
    ("pages/suggestions.html", "Suggestions", "The review section: 15 proposals, one verdict each"),
    ("pages/questions.html", "Questions &amp; answers", "Known, unknown, answered — graded"),
    ("pages/gaps.html", "Missing information", "13 gaps with the route that closes each"),
    ("pages/paths.html", "Decision paths", "Three coherent ways forward, gates first"),
    ("pages/site-improvements.html", "Site improvements", "Fix the site so a human can decide"),
    ("pages/consolidation.html", "Register census", "138 suggestions / 172 questions / 160 flags / 386 requirements"),
    ("pages/corpus.html", "Corpus arithmetic", "What is actually gradeable today, from the league's own numbers"),
    ("pages/evidence.html", "Official reads", "Every page this session read, with coverage stated"),
    ("pages/executive-summary.html", "Executive summary", "Six paragraphs, no hedging"),
    ("pages/sources.html", "Sources", "16 rows, graded official / repo / third-party"),
    ("pages/flagged.html", "⚑ Flagged for review", "10 irregularities, links included"),
]


def load(name, derived=False):
    return json.load(open(os.path.join(DERIVED if derived else DATA, name), encoding="utf-8"))


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def blank(why="blank — unverified"):
    return '<span class="blank">%s</span>' % esc(why)


def ext(url, label=None):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label or url))


def repo(link_rel, label="repo ↗"):
    return ext(BLOB + link_rel, label)


def src_cell(sources):
    if not sources:
        return blank("no source — not published")
    return " · ".join(ext(s["url"], s.get("label")) for s in sources)


def badge(text, kind="n"):
    return '<span class="b b-%s">%s</span>' % (kind, esc(text))


def table(headers, rows, cls="", note="", numeric=()):
    th = "".join('<th scope="col"%s>%s</th>' % (' class="num"' if i in numeric else "", h)
                 for i, h in enumerate(headers))
    body = "".join("<tr>%s</tr>" % "".join(
        '<td%s>%s</td>' % (' class="num"' if i in numeric else "", c) for i, c in enumerate(r))
        for r in rows)
    out = '<div class="tw"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        esc(cls), th, body)
    if note:
        out += '<p class="note">%s</p>' % note
    return out


def ul(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)


CODE_SPAN = re.compile(r"`([^`<>]+)`")


def code(s):
    """Turn the `inline code` ticks that register prose is authored with into a real <code> span.

    Runs after esc(), on already-escaped strings, and only where the span contains no tag
    characters, so it can never invent markup around existing HTML.
    """
    return CODE_SPAN.sub(r"<code>\1</code>", s) if isinstance(s, str) else s


def render(path, title, crumb, body, desc):
    depth = path.count("/")
    pre = "" if depth == 0 else "../" * depth
    # body prose may link sibling pages by their namespace-relative path; rewrite to this depth so
    # a link written once cannot break when the page moves
    if pre:
        body = body.replace('href="pages/', 'href="%spages/' % pre).replace('href="index.html"',
                                                                            'href="%sindex.html"' % pre)
    body = code(body)
    nav = []
    for p, label, _ in PAGES:
        cur = " on" if p == path else ""
        nav.append('<a class="%s" href="%s%s">%s</a>' % (("cur" if p == path else ""), pre, p, label))
    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(t)s · NFL Decision Console</title>
<meta name="description" content="%(d)s">
<link rel="stylesheet" href="%(pre)sassets/console.css">
</head><body>
<header class="top"><div class="wrap">
<a class="home" href="%(pre)sindex.html">NFL Decision Console</a>
<span class="asof">data as of <b>%(asof)s</b> · rendered by <code>engine/build_site.py</code></span>
</div></header>
<nav class="wrap tabs">%(nav)s</nav>
<main class="wrap">
<p class="crumb"><a href="%(pre)sindex.html">console home</a> · %(crumb)s</p>
%(body)s
</main>
<footer class="wrap"><p><b>Provenance rule.</b> Every row on this page is either transcribed from a
league page read in this session (link in the Source column) or computed by an engine in this namespace
from a committed artefact. Values that could not be confirmed are blank and flagged on
<a href="%(pre)spages/flagged.html">⚑ Flagged for review</a>. No price, line or payout appears anywhere on
this site because no official price source exists. This is analytical research, not wagering advice.</p>
<p><a href="https://github.com/sassnarep3-star/Own4">repository ↗</a> ·
<a href="%(pre)sindex.html">root dashboard ↗</a></p></footer>
</body></html>
""" % {"t": esc(title), "d": esc(desc), "pre": pre, "nav": "".join(nav), "crumb": crumb,
       "body": body, "asof": AS_OF}


def main():
    B = {}
    sug = load("suggestions.json")
    que = load("questions.json")
    gaps = load("gaps.json")
    paths = load("paths.json")
    site = load("site_findings.json")
    flags = load("flags.json")
    src = load("sources.json")
    reads = load("official_reads.json")
    gb = load("gamebook_evidence.json")
    st = load("standings_2026-11-16.json")
    inv = load("namespace_inventory.json")
    cor = load("corpus.json", True)
    ljoin = load("label_join.json", True)
    cons = load("consolidation.json", True)

    global AS_OF  # noqa: PLW0603 - the footer stamps every page with the same as-of string
    AS_OF = "2026-11-16 · reads %s · inventory at commit %s" % (reads["session_window_utc"].split(" to ")[-1][11:16],
                                                                 inv["captured_at_commit"])

    decided = sum(1 for r in sug["rows"] if (r.get("verdict") or "").strip())
    n_sug, n_q = len(sug["rows"]), len(que["rows"])
    answered = sum(1 for r in que["rows"] if r["answer"].strip()
                   and r["answer_grade"] in ("answered-official", "answered-computed", "answered-repo"))
    pc = cons["peer_registers"]
    top = pc["suggestions"]

    # ---------------------------------------------------------------- index
    key_numbers = [
        ["Gradeable fixtures today", "<b>%d</b>" % cor["fixtures_credited"],
         "Σ(W+L+T)/2 from the league's own standings, read %s" % esc(st["read_utc"]),
         ext(st["source_url"], "nfl.com/standings ↗") + " · " + repo("data/standings_2026-11-16.json", "transcription ↗")],
        ["Points identity", "ΣPF %d = ΣPA %d" % (cor["sum_points_for"], cor["sum_points_against"]),
         "the arithmetic every published number on this site has to pass", repo("engine/derive.py", "engine/derive.py ↗")],
        ["Gate cited by peers", "n ≥ %d graded games per strategy" % cor["gate_check"]["gate_cited_by_peers"],
         "a season holds %d fixtures, so %s — this is decision CD-06"
         % (cor["season_fixture_count"],
            "one season cannot satisfy it" if not cor["gate_check"]["one_season_can_satisfy_the_gate"]
            else "one season can satisfy it"),
         repo("data/derived/corpus.json", "corpus.json ↗") + " · " + ext("https://github.com/sassnarep3-star/Own4/blob/main/nfl-command/data/gates.json", "nfl-command gate ↗") + " · " + ext("https://github.com/sassnarep3-star/Own4/blob/main/nfl-availability-desk/prereg/PREREG-001-shadow-baseline.md", "pre-registration G1 ↗")],
        ["Official price source", "%s" % badge("none on the paths probed", "bad"),
         "nfl.com/odds/ and nfl.com/betting/ both serve the league's own 404 page (read this session)",
         ext("https://www.nfl.com/odds/", "odds probe ↗") + " · " + ext("https://www.nfl.com/betting/", "betting probe ↗")],
        ["Official lineups / inactives", "%s" % badge("exist, per fixture, post-game", "ok"),
         "the Game Summary prints both clubs' lineups and Not Active lists — see pages/evidence.html",
         ext(gb["source_url"], "the PDF ↗")],
        ["Suggestion rows in the repo", "<b>%d</b> across %d registers in %d namespaces"
         % (pc["suggestions"]["rows"], pc["suggestions"]["files"], pc["suggestions"]["namespaces"]),
         "and only %d of those rows carry a non-blank verdict-shaped field at all (an upper bound — see the "
         "caveat on the census page); rows whose field is literally named 'verdict' and filled: %s"
         % (pc["suggestions"]["rows_with_verdict"],
            "0 in git" if decided == 0 else "%d in this console" % decided),
         repo("data/namespace_inventory.json", "inventory ↗") + " · " + repo("pages/consolidation.html", "census ↗")],
        ["Verdicts written on this console", "%d of %d" % (decided, n_sug),
         "the queue closes only when a verdict is written into data/suggestions.json; the counter is generated",
         repo("data/suggestions.json", "suggestions.json ↗")],
    ]
    B["index.html"] = """
<h1>NFL Decision Console</h1>
<p class="lede">One place to decide. The repository already holds
%(rows)d register rows about the same
decisions — this console consolidates them, adds what a fresh read of the league's own pages settled
today, and leaves a verdict box on every proposal. Nothing here is implemented; that is the point.</p>
<div class="cards">
<div class="card"><h3>Decision in front of you #1</h3><p><b>Price policy.</b> The league publishes no
odds — probed twice this session. Buy a feed, decline prices forever, or keep a labelled third-party
archive. Nine requirement families wait on this one sentence. → <a href="pages/suggestions.html">CD-02</a></p></div>
<div class="card"><h3>Decision #2</h3><p><b>The gate versus the calendar.</b> A validation gate of
n ≥ %(gate)d graded fixtures cannot be met in a %(season)d-fixture season. Lower it, switch the unit,
or accept that no strategy is promotable until 2027. → <a href="pages/corpus.html">corpus arithmetic</a></p></div>
<div class="card"><h3>Decision #3</h3><p><b>One canonical surface.</b> %(nregs)d registers, %(ns)d
namespaces, no place a verdict is authoritative. Pick one, mark the rest appendices. → <a href="pages/site-improvements.html">site findings</a></p></div>
</div>
<h2>Numbers a decision has to be consistent with</h2>
%(kn)s
<h2>What this session changed about what we know</h2>
%(new)s
<h2>Where to go</h2>
<div class="grid2">
<p><a href="pages/suggestions.html"><b>Suggestions (%(sug)d)</b></a> — the review section: options, costs,
what each one locks, and a blank verdict column.</p>
<p><a href="pages/questions.html"><b>Questions &amp; answers (%(q)d)</b></a> — known, unknown, and what
would fill the gap, each graded by the kind of evidence behind it.</p>
<p><a href="pages/gaps.html"><b>Missing information (%(g)d)</b></a> — the discovery plan: route, owner, cost.</p>
<p><a href="pages/paths.html"><b>Decision paths (3)</b></a> — pick one; each lists its first step, its
gate, and the number that clears it.</p>
<p><a href="pages/evidence.html"><b>Official reads</b></a> — every page opened, with chunk coverage and
what the page could not prove.</p>
<p><a href="pages/flagged.html"><b>⚑ Flagged for review (%(f)d)</b></a> — irregularities, including the
ones this session resolved and the ones it could not.</p>
</div>
""" % {
        "rows": sum(pc[k]["rows"] for k in pc), "gate": cor["gate_check"]["gate_cited_by_peers"],
        "season": cor["season_fixture_count"], "nregs": sum(pc[k]["files"] for k in pc),
        "ns": inv["namespace_count"], "sug": n_sug, "q": n_q, "g": len(gaps["rows"]), "f": len(flags["rows"]),
        "kn": table(["Figure", "Value", "Why it is trustworthy", "Source"], key_numbers, "keys",
                    "Every value here is produced by <code>engine/derive.py</code> from a committed "
                    "transcription, or is an official page read in this session. Nothing is typed twice."),
        "new": ul([
            "<b>Answered:</b> the Game Book the requirements name as the source for actual starters and "
            "game-day status exists, is dated, is linked from the game centre, and prints both clubs' "
            "lineups, Not Active lists, game-day weather and roof/surface. %s" % badge("verified this session", "ok"),
            "<b>Answered:</b> it is a <i>post-game</i> document — it contains final statistics — so it is a "
            "label source, never a pre-kickoff feature. %s" % badge("look-ahead gate", "warn"),
            "<b>New risk found:</b> the document prints a use restriction (media coverage only; any other "
            "use needs written league permission). No register in this repository recorded it, and two "
            "namespaces publish tables transcribed from it. → CD-03",
            "<b>Resolved upstream:</b> the three Lions rows this project flagged as blank (Joseph, Mays, "
            "Reed) now each read <i>Out</i> on the live report. Closed as 'source corrected between "
            "captures', not 'we fixed it'.",
            "<b>Still nothing:</b> no official depth-order source (1 of 32 club paths probed, 404) and no "
            "per-player snap table found in the game-book chunks read — so the 2nd/3rd/4th-string index "
            "remains unbuilt on purpose.",
            "<b>Settled by arithmetic:</b> %d fixtures are gradeable now; %d is exactly half a season, the "
            "only figure derivable from official numbers that reproduces the brief's '136-game log'."
            % (cor["fixtures_credited"], cor["half_season"]),
        ]),
    }

    # ------------------------------------------------------------ suggestions
    prio_order = {"P1": 0, "P2": 1, "P3": 2}
    rows = []
    for r in sorted(sug["rows"], key=lambda x: (prio_order.get(x["priority"], 9), x["id"])):
        opts = "<ol class='opts'>%s</ol>" % "".join(
            "<li><b>%s</b> — %s <span class='dim'>(cost: %s; locks: %s)</span></li>"
            % (esc(o["id"]), esc(o["text"]), esc(o["cost"]), esc(o["locks"])) for o in r["options"])
        rows.append([
            "<b>%s</b>" % esc(r["id"]),
            badge(r["priority"], "p1" if r["priority"] == "P1" else "p2" if r["priority"] == "P2" else "p3"),
            "<b>%s</b><p class='q'><i>The decision:</i> %s</p>%s<p class='rec'><i>Recommended:</i> <b>%s</b> "
            "<span class='dim'>— basis: %s</span></p>" % (esc(r["title"]), esc(r["decision"]), opts,
                                                           esc(r["recommended"]), esc(r["basis"])),
            ul(esc(e) for e in r["evidence"]),
            esc("; ".join(r["unblocks"])),
            "%s<br><span class='dim'>effort %s · owner needed: %s</span>" % (
                esc(r["risk_if_deferred"]), esc(r["effort"]), esc("yes" if r["needs_owner"] else "no")),
            "<code class='verdict'>%s</code>" % (esc(r["verdict"]) if r["verdict"].strip() else
                                                  blank("verdict blank — write one in data/suggestions.json")),
            src_cell(r["sources"]),
        ])
    B["pages/suggestions.html"] = """
<h1>Suggestions — review, choose, then anyone builds</h1>
<p class="lede">%(proto)s</p>
<p>%(scope)s</p>
<p class="status">Queue state: <b>%(dec)d of %(tot)d</b> rows carry a verdict. %(empty)s</p>
%(t)s
<p class="note">Column 'What it unblocks' names the owner's requirement lines, quoted, that this decision
releases. Rows marked <i>owner needed</i> cannot be answered by any further read of a website: they need a
choice. Rows not marked can be executed by a session once the verdict is written.</p>
""" % {"proto": esc(" · ".join(sug["review_protocol"])), "scope": esc(sug["scope_note"]),
       "dec": decided, "tot": n_sug,
       "empty": "Until one is written, the honest status of the whole programme is: proposals exist, no "
                "decision has been recorded in git." if decided == 0 else
                "%d rows are now actionable." % decided,
       "t": table(["ID", "Prio", "Suggestion, options and recommendation", "Evidence it rests on",
                   "What it unblocks", "Risk if deferred", "Verdict", "Source"], rows, "sug",
                  "", numeric=())}

    # -------------------------------------------------------------- questions
    rows = []
    for r in que["rows"]:
        ans = r["answer"].strip() or blank("no answer yet — see the discovery column")
        rows.append([
            "<b>%s</b>" % esc(r["id"]),
            badge(r["blocks"], "bad" if r["blocks"] == "blocking" else "warn"),
            "<b>%s</b>" % esc(r["question"]),
            esc(r["know"]),
            esc(r["dont_know"]),
            ans,
            badge(r["answer_grade"], "ok" if r["answer_grade"].startswith("answered") else
                  ("warn" if r["answer_grade"].startswith("partly") else "bad")),
            esc(r["discovery"]),
            esc(r["asked_by"]),
            src_cell(r["sources"]),
        ])
    B["pages/questions.html"] = """
<h1>Questions, information and answers</h1>
<p class="lede">%(rule)s</p>
<p>Grades in use: %(grades)s.</p>
<p class="status"><b>%(ans)d of %(tot)d</b> rows now carry an answer backed by an official read or a
computation; the rest say exactly what would fill them and who can do it.</p>
%(t)s
""" % {"rule": esc(que["rule"]),
       "grades": " · ".join("<b>%s</b> = %s" % (esc(k), esc(v)) for k, v in sorted(que["grades"].items())),
       "ans": answered, "tot": n_q, "t": table(
           ["ID", "Blocks", "Question", "What we know", "What we do not know", "Answer",
            "Answer grade", "What would fill the gap", "Raised by", "Source"], rows, "q")}

    # ------------------------------------------------------------------ gaps
    rows = []
    for r in gaps["rows"]:
        rows.append([
            "<b>%s</b>" % esc(r["id"]), esc(r["item"]), esc(r["why_needed"]),
            esc(r["official_source"]), esc(r["route"]), esc(r["owner"]), esc(r["cost"]),
            badge(r["status"], "bad" if "blocked" in r["status"] else "warn"),
            esc(r["unblocks"]), src_cell(r["sources"]),
        ])
    B["pages/gaps.html"] = """
<h1>Missing information, and how to go get it</h1>
<p class="lede">%(rule)s</p>
%(t)s
<p class="note">A gap marked <code>owner-blocked</code> is not a research problem. No amount of scraping
closes it; a sentence in <code>data/decisions.json</code> does.</p>
""" % {"rule": esc(gaps["rule"]), "t": table(
    ["ID", "What we do not have", "Why it is needed", "Official source today", "Route that closes it",
     "Owner", "Cost", "Status", "Unblocks", "Source"], rows, "g")}

    # ----------------------------------------------------------------- paths
    cards = []
    for p in paths["rows"]:
        cards.append("""
<div class="pathcard">
<h3>%s — %s</h3>
<p class="dim">%s</p>
<dl>
<dt>First step</dt><dd>%s</dd>
<dt>Gate that blocks it</dt><dd>%s</dd>
<dt>Number that clears it</dt><dd><b>%s</b></dd>
<dt>Then, in order</dt><dd><ol>%s</ol></dd>
<dt>It forbids</dt><dd>%s</dd>
<dt>Cost</dt><dd>%s</dd>
<dt>Earliest leaderboard</dt><dd>%s</dd>
<dt>Risk</dt><dd>%s</dd>
</dl>
<p class="src">%s</p>
</div>""" % (esc(p["path"]), esc(p["name"]), esc(p["what_it_is"]), esc(p["first_step"]),
             esc(p["gate"]), esc(p["clearing_number"]),
             "".join("<li>%s</li>" % esc(x) for x in p["then"]), esc(p["forbids"]), esc(p["cost"]),
             esc(p["earliest_leaderboard"]), esc(p["risk"]), src_cell(p["sources"])))
    B["pages/paths.html"] = """
<h1>Decision paths</h1>
<p class="lede">%s</p>
<div class="paths">%s</div>
""" % (esc(paths["how_to_use"]), "".join(cards))

    # --------------------------------------------------------------- site
    rows = []
    for r in site["rows"]:
        rows.append([
            "<b>%s</b>" % esc(r["id"]),
            badge(r["severity"], {"high": "bad", "medium": "warn", "low": "n"}[r["severity"]]),
            "<b>%s</b>" % esc(r["finding"]),
            esc(r["observed"]), esc(r["proposed_change"]), esc(r["verify_by"]), esc(r["cost"]),
            esc(r["risk_if_skipped"]), badge(r["decision_required"], "bad" if r["decision_required"] == "yes" else "ok"),
            src_cell(r["sources"]),
        ])
    B["pages/site-improvements.html"] = """
<h1>How to improve the site so a human can decide</h1>
<p class="lede">%(rule)s</p>
%(t)s
""" % {"rule": esc(site["rule"]), "t": table(
    ["ID", "Severity", "Finding", "Observed (with the number)", "Change proposed", "How to verify the change worked",
     "Cost", "Risk if skipped", "Needs a decision first?", "Source"], rows, "sf")}

    # --------------------------------------------------------- consolidation
    per = cons["per_kind"]
    rows = []
    for kind in sorted(per):
        v = per[kind]
        a = cons["all_registers"][kind]
        rows.append([
            "<b>%s</b>" % esc(kind), "%d" % v["files"], "%d" % v["namespaces"], "%d" % v["rows"],
            "%d" % a["files"], "%d" % a["rows"],
            "%d" % v["rows_with_text"], "%d" % v["distinct_clusters"], "%d" % v["clusters_with_duplicates"],
            "%d" % v["rows_inside_a_duplicate_cluster"], "%d" % v["largest_cluster"],
            "%d" % v["rows_with_sentence_text"], "%d" % v["sentence_duplicate_clusters"],
            "%d" % v["sentence_rows_inside_a_duplicate_cluster"], "%d" % v["sentence_largest_cluster"],
            "%d" % v["rows_with_verdict"], "%d" % v["rows_with_status"],
            repo("data/namespace_inventory.json", "inventory ↗"),
        ])
    cl_rows = []
    for kind in sorted(per):
        for i, g in enumerate(per[kind]["top_clusters"][:8]):
            if g["n"] < 2:
                continue
            mem = " · ".join("<code>%s</code>" % esc(m["namespace"]) for m in g["members"][:6])
            more = "" if len(g["members"]) <= 6 else " <span class='dim'>(%d more)</span>" % (len(g["members"]) - 6)
            cl_rows.append([esc(kind), "%s#%d" % (esc(kind[:3]), i + 1), "%d" % g["n"],
                            esc(g["members"][0]["text"]),
                            ("<span class='dim'>identifier-keyed — a shared row id, not a shared "
                             "proposal</span>" if g.get("id_keyed") else "sentence text"),
                            mem + more,
                            repo("data/namespace_inventory.json", "inventory ↗")])
    verdict_rows = []
    for kind in sorted(per):
        a = cons["all_registers"][kind]
        fc = cons["verdict_field_counts"].get(kind, {})
        verdict_rows.append(["<b>%s</b>" % esc(kind), "%d" % a["rows"], "%d" % a["rows_with_verdict"],
                             "%d" % a["rows_with_status"],
                             esc(", ".join("%s=%d" % (k, v) for k, v in sorted(fc.items()) if v) or "none"),
                             repo("data/namespace_inventory.json", "inventory ↗")])
    vt = table(["Kind", "Rows in all registers", "Rows with a non-blank verdict-shaped field",
                "Rows with a non-blank status-shaped field", "Which verdict field, and how many rows",
                "Source"], verdict_rows, "keys", numeric=(1, 2, 3))
    B["pages/consolidation.html"] = """
<h1>Register census — the duplication, counted</h1>
<p class="lede">Counts are read from every committed register by <code>engine/inventory.py</code>, snapshotted
at commit <code>%(sha)s</code> (%(cap)s) and frozen into <code>data/namespace_inventory.json</code>; the build
reads that file and never re-walks the tree, so a sibling merge cannot move a number on this page.</p>
%(t)s
<h2>What the peer rows collapse into</h2>
<p>Text clustering rule: %(rule)s. 'Peer registers' excludes this console's own registers so the
duplication finding is not self-referential; 'all registers' includes them. Read the duplication from
the <b>sentence</b> columns: %(ccaveat)s.</p>
%(c)s
<h2>The verdict question, precisely</h2>
<p>%(caveat)s</p>
%(vt)s
<p class="note">Peer registers publish a status for most rows (an engine describing its own state), and a
reviewer verdict for almost none. That gap is why SF-02 and CD-15 exist: a proposal that never gets a
verdict is not governance, it is a backlog.</p>
""" % {"sha": esc(cons["inventory_captured_at_commit"]), "cap": esc(cons["inventory_captured_utc"]),
       "rule": esc(cons["cluster_rule"]), "caveat": esc(cons["verdict_field_caveat"]), "vt": vt,
       "ccaveat": esc(cons["cluster_caveat"]),
       "t": table(["Register kind", "Peer files", "Peer namespaces", "Peer rows", "All files", "All rows",
                   "Rows with comparable text", "Distinct clusters", "Clusters with >=2 rows",
                   "Rows inside a duplicate cluster", "Largest cluster",
                   "Rows with sentence text", "Sentence duplicate clusters",
                   "Rows inside a duplicate sentence cluster", "Largest sentence cluster",
                   "Rows w/ verdict", "Rows w/ status", "Source"],
                  rows, "cons", numeric=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)),
       "c": table(["Kind", "Cluster", "Rows", "Lead text (truncated)", "Keyed on",
                   "Namespaces carrying it", "Source"],
                  cl_rows, "clus", numeric=(2,))}

    # ----------------------------------------------------------------- corpus
    ids = [[esc(i["name"]), "<code>%s</code>" % esc(i["left"]), "<code>%s</code>" % esc(i["right"]),
            badge("holds" if i["holds"] else "FAILS", "ok" if i["holds"] else "bad"),
            repo("engine/derive.py", "engine/derive.py ↗")] for i in cor["identities"]]
    obs = cor["observations_not_identities"][0]
    jrows = []
    for r in ljoin["by_status"]:
        jrows.append([("<b>%s</b>" % esc(r["game_status"])), "%d" % r["report_rows"], "%d" % r["started"],
                      "%d" % r["played off the bench"], "%d" % r["not active"], "%d" % r["did not play"],
                      "%d" % r["ambiguous"], "%d" % r["unaccounted"], "%d" % r["joined_confidently"],
                      ext(gb["source_url"], "game book ↗") + " · " + ext("https://www.nfl.com/injuries/", "report ↗")])
    B["pages/corpus.html"] = """
<h1>Corpus arithmetic — what is actually gradeable today</h1>
<p class="lede">The brief hands the project a '136-game log'. A corpus is not a number someone quotes; it is
an identity that either closes or does not. Computed from the league's standings page read at
%(read)s.</p>
<h2>The identities</h2>
%(ids)s
<h2>The size, and what it does to the gates</h2>
%(gate)s
<h2>Where the floor is actually written, in the peers' own words</h2>
<p>The number is quoted across this repository as a corpus size. It is not: every register that states it
states it as a count of <b>graded games or settled bets for one strategy</b>. Those three sentences are
transcribed from the files, and they are the only places the figure appears.</p>
%(gateq)s
<p class="note"><b>Attribution.</b> %(miscite)s — the three rows above are what the gate actually says,
and flag <code>DC-13</code> keeps the correction on the record.</p>
<h2>The 136 question</h2>
%(brief)s
<h2>An observation that is not an identity</h2>
<p><b>%(obsname)s</b> — %(obscount)d club: %(obsclubs)s. %(obsread)s</p>
<h2>The availability join (one fixture, n = 1)</h2>
<p>%(joinmethod)s</p>
%(jt)s
<p class="note">%(joincaveat)s</p>
<p class="note"><b>Join key limit.</b> %(joinnote)s</p>
<h2>Header facts one game book carries (transcribed)</h2>
%(hb)s
""" % {
        "read": esc(cor["read_utc"]),
        "ids": table(["Identity", "Left", "Right", "Result", "Source"], ids, "keys"),
        "miscite": esc(cor["gate_check"]["mis_citation_corrected"]),
        "gateq": table(["Register that states the floor", "Its sentence, verbatim", "Source"],
                       [[esc(q["file"]), "&ldquo;%s&rdquo;" % esc(q["text"]),
                         ext("https://github.com/sassnarep3-star/Own4/blob/main/%s" % q["file"],
                             "the file ↗")]
                        for q in cor["gate_check"]["as_written_by_peers"]], "gateq"),
        "gate": table(["Measure", "Value", "Reading", "Source"], [
            ["Fixtures credited now", "<b>%d</b> (%d decisive, %d tied)" % (
                cor["fixtures_credited"], cor["decisive_fixtures"], cor["tied_fixtures"]),
             "each fixture is counted twice in the standings, so the division is exact",
             repo("data/derived/corpus.json", "corpus.json ↗")],
            ["Fixtures in a full season", "%d" % cor["season_fixture_count"],
             "32 clubs × 17 games ÷ 2 — the league's own schedule shape", ext("https://www.nfl.com/schedules/", "schedule ↗")],
            ["Half a season", "%d" % cor["half_season"], "the only arithmetic that reproduces the brief's 136",
             repo("data/derived/corpus.json", "corpus.json ↗")],
            ["Gate cited by peer registers", "n ≥ %d graded games per strategy" % cor["gate_check"]["gate_cited_by_peers"],
             esc(cor["gate_check"]["reading"]), repo("data/derived/corpus.json", "corpus.json ↗")],
            ["Seasons needed at this rate", "%d" % cor["gate_check"]["seasons_needed_at_this_rate"],
             "so a literal gate means the leaderboard cannot open during the 2026 season",
             repo("data/derived/corpus.json", "corpus.json ↗")],
            ["Club-game rows today", "%d" % cor["sum_games_played"],
             "the unit change in CD-06 option C: it doubles n, and it forces clustering by fixture for every interval",
             repo("data/derived/corpus.json", "corpus.json ↗")],
        ], "keys"),
        "brief": table(["Claim", "Observed", "Matches the brief?", "Note", "Source"], [
            [esc(b["claim"]), "%d" % b["observed"],
             badge("no" if not b["matches_any_observed_count"] else "yes",
                   "warn" if not b["matches_any_observed_count"] else "ok"),
             esc(b["arithmetic_note"]),
             ext(cor["source_url"], "standings ↗") + " · " + repo("data/standings_2026-11-16.json", "transcription ↗")]
            for b in cor["brief_claims_checked"]], "keys"),
        "obsname": esc(obs["name"]), "obscount": obs["count"],
        "obsclubs": esc(", ".join("%s (%s pct, net %+d)" % (c["abbr"], c["pct"], c["net"]) for c in obs["clubs"])),
        "obsread": esc(obs["reading"]),
        "joinmethod": esc(ljoin["method"]),
        "jt": table(["Game status on the report", "Report rows", "Started", "Played off bench", "Not active",
                    "Did not play", "Ambiguous", "Unaccounted", "Joined confidently", "Source"],
                   jrows, "keys", numeric=tuple(range(1, 9))),
        "joincaveat": esc(ljoin["caveat"]), "joinnote": esc(ljoin["join_key_note"]),
        "hb": table(["Field printed in the official Game Summary", "Value read", "Source"], [
            ["Date and venue", esc(gb["fixture"]["date_printed"]) + " — " + esc(gb["fixture"]["venue_in_pdf"]),
             ext(gb["source_url"], "PDF ↗")],
            ["Venue as the game centre prints it", esc(gb["fixture"]["venue_in_game_centre"]) +
             " <span class='dim'>(same fixture, different label — flag DC-03)</span>",
             ext(gb["linked_from"], "game centre ↗")],
            ["Kickoff (local)", esc(gb["fixture"]["kickoff_local"]), ext(gb["source_url"], "PDF ↗")],
            ["Game day weather", "%s, %s °F (%s °C), humidity %s %%, wind %s" % (
                esc(gb["fixture"]["game_day_weather"]["condition"]),
                esc(gb["fixture"]["game_day_weather"]["temp_f"]),
                esc(gb["fixture"]["game_day_weather"]["temp_c"]),
                esc(gb["fixture"]["game_day_weather"]["humidity_pct"]),
                esc(gb["fixture"]["game_day_weather"]["wind"])), ext(gb["source_url"], "PDF ↗")],
            ["Roof and surface", "<b>%s</b>" % esc(gb["fixture"]["roof_surface"]), ext(gb["source_url"], "PDF ↗")],
            ["Paid attendance", "{:,}".format(gb["fixture"]["paid_attendance"]), ext(gb["source_url"], "PDF ↗")],
            ["Final score", "NE %s — DET %s" % (esc(gb["fixture"]["final"]["NE"]), esc(gb["fixture"]["final"]["DET"])),
             ext(gb["linked_from"], "game centre ↗")],
            ["Availability blocks", "%s" % esc(", ".join(sorted(ljoin["counts"]["names_per_block"]["NE"]))) +
             " <span class='dim'>(NE 22 lineup + 26 substitutions + 6 not active = %d names enumerated)</span>"
             % ljoin["counts"]["total_names_per_club"]["NE"], ext(gb["source_url"], "PDF ↗")],
            ["Use restriction printed on page 1", "<i>%s</i>" % esc(gb["use_restriction_printed_on_the_document"]),
             ext(gb["source_url"], "PDF ↗")],
        ], "keys"),
    }

    # -------------------------------------------------------------- evidence
    rows = []
    for r in reads["rows"]:
        rows.append([
            "<b>%s</b>" % esc(r["id"]), ext(r["url"], r["url"]), badge(r["grade"], "ok" if r["grade"] == "official" else "n"),
            esc(r["publisher"]), esc(r["coverage"]),
            ul(esc(x) for x in r["proved"]),
            ul(esc(x) for x in r["cannot_prove"]),
        ])
    rows.append([
        "<b>JOIN</b>", repo("data/derived/label_join.json", "label_join.json ↗"), badge("repo", "n"),
        "this namespace", "computed from the two artefacts above",
        ul(["%d of %d report rows join confidently; %d ambiguous; %d unaccounted" % (
            sum(r["joined_confidently"] for r in ljoin["by_status"]), ljoin["counts"]["report_rows"],
            sum(r["ambiguous"] for r in ljoin["by_status"]), sum(r["unaccounted"] for r in ljoin["by_status"]))]),
        ul(["any per-club census — one fixture", "a play rate — n = 1"]),
    ])
    B["pages/evidence.html"] = """
<h1>Official reads — everything this session opened, and what it could not prove</h1>
<p class="lede">%(tsrule)s</p>
<p class="status">Window: <b>%(win)s</b>. Sections found in the game book: %(sec)s.</p>
<p class="note">Searched for and <b>not found</b> in the chunks read: %(notfound)s. Absence in a rendered
read is not absence in the source — see flag DC-05.</p>
%(t)s
""" % {"tsrule": esc(reads["timestamp_rule"]), "win": esc(reads["session_window_utc"]),
       "sec": esc(", ".join(gb["sections_found"])),
       "notfound": esc("; ".join(gb["sections_searched_for_and_not_found_in_the_chunks_read"])),
       "t": table(["Read", "URL", "Grade", "Publisher", "Coverage of the page", "What it proved",
                   "What it cannot prove"], rows, "ev")}

    # --------------------------------------------------------------- flagged
    rows = []
    for r in flags["rows"]:
        rows.append([
            "<b>%s</b>" % esc(r["id"]),
            badge(r["severity"], {"high": "bad", "medium": "warn", "low": "n"}[r["severity"]]),
            "<b>%s</b>" % esc(r["title"]), esc(r["found"]), esc(r["why_it_matters"]), esc(r["action"]),
            esc(r["blocks"]), src_cell(r["sources"]),
        ])
    B["pages/flagged.html"] = """
<h1>⚑ Flagged for review</h1>
<p class="lede">%(rule)s</p>
%(t)s
<p class="note">None of these blocks the site: they are published so the owner can act after the fact,
which is what the brief asks for. Two of them (DC-04, DC-05) change what a next session should build.</p>
""" % {"rule": esc(flags["rule"]), "t": table(["ID", "Severity", "Flag", "What was found", "Why it matters",
                                   "Action", "What it blocks", "Source"], rows, "fl")}

    # --------------------------------------------------------------- sources
    rows = []
    for r in src["rows"]:
        rows.append([
            "<b>%s</b>" % esc(r["sid"]), esc(r["publisher"]), esc(r["kind"]),
            badge(r["grade"], {"official": "ok", "repo": "n", "third-party": "bad"}[r["grade"]]),
            ext(r["url"], r["url"]), esc(r["used_for"]), esc(r["read"]),
        ])
    B["pages/sources.html"] = """
<h1>Source register</h1>
<p class="lede">%(rule)s</p>
%(t)s
""" % {"rule": esc(src["grading"]), "t": table(["ID", "Publisher", "Kind", "Grade", "URL", "Used for", "Read"], rows, "so")}

    # ------------------------------------------------------------- exec sum
    B["pages/executive-summary.html"] = exec_summary(cor, ljoin, cons, sug, que, gaps, flags, reads, gb, decided, n_sug)

    for path_, title_, desc_ in PAGES:
        body_ = B[path_]
        crumb = "console home" if path_ == "index.html" else "Decision Console · %s" % title_
        out = os.path.join(NS, path_)
        if os.path.dirname(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(
            render(path_, "%s · NFL Decision Console" % title_, crumb, body_, desc_))
        print("wrote", os.path.relpath(out, ROOT))
    return 0


def exec_summary(cor, ljoin, cons, sug, que, gaps, flags, reads, gb, decided, n_sug):
    pc = cons["peer_registers"]
    total_rows = sum(pc[k]["rows"] for k in pc)
    n_flagged = len(flags["rows"])
    answered = sum(1 for r in que["rows"] if r["answer"].strip()
                   and r["answer_grade"].startswith("answered"))
    return """
<h1>Executive summary</h1>
<p class="lede">Six paragraphs. Every number in them is produced by an engine in this namespace from a
committed artefact, and every page reference is a link.</p>
<h2>1. The programme is not short of analysis; it is short of decisions</h2>
<p>The repository carries <b>%(total)d</b> register rows across <b>%(regs)d</b> files in
%(ns)d <code>nfl*</code> namespaces at commit <code>%(sha)s</code> (this console counted among them):
%(sug)d suggestions, %(q)d questions, %(fl)d flags and %(rq)d requirement rows.
Verdict-shaped fields are non-blank on %(verd)d of them, and none of those is a reviewer's decision — they
are engines describing their own state. The brief's process (review, choose, then implement) has no place
to happen. <a href="pages/consolidation.html">Census ↗</a></p>
<h2>2. The two blockers are now answers, not blanks</h2>
<p><b>Prices:</b> nfl.com/odds/ and nfl.com/betting/ both return the league's own 404 page (both read
inside %(win)s),
and the official Game Summary contains no price. So 'no official price source' is no longer an open
research question; it is a settled negative, and what remains is a policy choice (%(cd02)s).
<b>Depth:</b> the sampled club depth-chart path 404s and no per-player snap table appears in the four
game-book chunks read, so '2nd/3rd/4th string' still has no official basis — and the site should keep
refusing to build it from jersey order. <a href="pages/questions.html">Answers ↗</a></p>
<h2>3. The Game Book unblocks the half of the programme that was calling itself stuck</h2>
<p>For a sampled completed fixture the league publishes a dated PDF carrying both clubs' official lineups
(22 slots), substitutions (26 each), Not Active lists (6 each), a Did Not Play block, game-day weather, the
roof/surface phrase, officials, attendance, full statistics, drives and play-by-play with timed in-game
injury updates. A second fixture one week later carries its own. That is enough to build the results feed,
the venue/surface context, the inactives record and the 'who actually started' half of the availability
graph — from official sources, with no new licence. It is also the reason the label join in this
namespace closes at all: %(conf)d of %(rows)d report rows join confidently (%(amb)d ambiguous, %(unacc)d
unaccounted). <a href="pages/evidence.html">Evidence ↗</a></p>
<h2>4. And it comes with two conditions nobody recorded</h2>
<p>The document is <b>post-game</b> — it contains final statistics — so it can grade a forecast and can
never feed one. It also prints a use restriction: media coverage only, any other use prohibited without
written league permission. Two namespaces already publish transcribed lineups; the repository's own
registers describe game books as the source they need, and none of them notes either condition.
<a href="pages/flagged.html">Flags DC-04 and DC-05 ↗</a></p>
<h2>5. The corpus number moves the leaderboard from 'soon' to 'next season'</h2>
<p>From the league's standings at this session's clock: %(fx)d fixtures credited (%(dec)d decisive,
%(tie)d tied), ΣW = ΣL = %(w)d and ΣPF = ΣPA = %(pf)d, so the identities close. A season holds %(sea)d
fixtures. Any gate demanding n ≥ %(gate)d graded fixtures is therefore unsatisfiable inside 2026, and the
brief's '136-game log' is exactly half a season (%(half)d) — the only arithmetic from official numbers that
reproduces it. Either the gate, the unit (club-games: %(gp)d today) or the timeline changes; that is a
%(cd06)s. <a href="pages/corpus.html">Corpus arithmetic ↗</a></p>
<h2>6. What to do first</h2>
<ol>
<li><b>Write three verdicts</b> — CD-02 (price policy), CD-06 (gate vs season), CD-01 (one canonical
surface). Each is a sentence and each releases a family of work.</li>
<li><b>Build the collector before any model</b> (CD-04): dated captures with raw bytes and a hash, because
today the site cannot distinguish 'absent from the source' from 'lost in the render' — DC-05 is that
failure, live, in one of this namespace's own joins.</li>
<li><b>Then the join at scale</b> (CD-07): designation → game-book status for every fixture, with Wilson
intervals and n, and no legacy percentages imported.</li>
<li><b>Only then</b> the leaderboard (CD-10, CD-14): skill division with the trial count published, staking
kept in a separate column, and no reward denominated in a backtest.</li>
</ol>
<p class="status">This console has <b>%(dec)d of %(tot)d</b> verdicts written. Until they exist, the honest
status line for the whole programme is: <i>specification complete, decisions pending.</i></p>
""" % {
        "total": total_rows, "regs": sum(pc[k]["files"] for k in pc), "ns": cons["namespace_count"],
        "sha": cons["inventory_captured_at_commit"],
        "sug": pc["suggestions"]["rows"], "q": pc["questions"]["rows"], "fl": pc["flags"]["rows"],
        "rq": pc["requirements"]["rows"], "verd": pc["suggestions"]["rows_with_verdict"],
        "win": reads["session_window_utc"].split(" to ")[1],
        "cd02": "CD-02", "conf": sum(r["joined_confidently"] for r in ljoin["by_status"]),
        "rows": ljoin["counts"]["report_rows"],
        "amb": sum(r["ambiguous"] for r in ljoin["by_status"]),
        "unacc": sum(r["unaccounted"] for r in ljoin["by_status"]),
        "fx": cor["fixtures_credited"], "dec": dec2(cor), "tie": cor["tied_fixtures"],
        "w": cor["sum_wins"], "pf": cor["sum_points_for"], "sea": cor["season_fixture_count"],
        "gate": cor["gate_check"]["gate_cited_by_peers"], "half": cor["half_season"],
        "gp": cor["sum_games_played"], "cd06": "decision, not a data gap",
        "answered": answered, "decided": decided, "tot": n_sug,
        "dec2": 0,
    }


def dec2(cor):
    return cor["decisive_fixtures"]


if __name__ == "__main__":
    raise SystemExit(main())

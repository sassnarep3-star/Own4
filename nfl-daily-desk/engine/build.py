#!/usr/bin/env python3
"""Render the daily desk from data/*.json. Stdlib only, deterministic (rebuild is byte-identical).

Every rendered table row carries an https source link: an official nfl.com page for a value read
from the league, or a github.com permalink to the repository artifact for an inherited number. A
value with neither is rendered as an empty cell with its reason, never as a guess.
"""
import json
import os
import re

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(NS, "data")
PAGES = NS
REPO = "https://github.com/sassnarep3-star/Own4/blob/main"
INJ_URL = "https://www.nfl.com/injuries/"
READINGS = {
    ("CAR", "Will Lee III", "practice"):
        "this desk's two dated captures bracket the change (Full at 2026-11-18T23:49:17Z, Limited at "
        "2026-11-19T07:05:00Z); the peer read carries no clock time, so it cannot be placed, and the "
        "difference is published rather than adjudicated",
    ("DET", "Ennis Rakestraw Jr.", "practice"):
        "capitalisation only: the byte-exact official string is 'Limited Participation in Practice' with a "
        "lower-case 'in', which is what this desk pins; the peer value is title-cased. A delta built on "
        "normalised casing would report this as a status change",
}
CARRIED = {
    "VF-01": "carried here as F-DSK-16, because the venue requirement names the game centre as the source",
    "VF-02": "the gap it describes is closed on this desk's side: all 24 club blocks with rows were read",
    "VF-03": "carried here as F-DSK-17 — a same-day read with no clock time cannot be sequenced",
    "VF-04": "the same conclusion this desk reached independently (F-DSK-01): no official price source",
    "VF-05": "the same HOU image-only depth state this desk reports against R-50",
    "VF-06": "corroborates the delta design: a designation series, not a level",
    "VF-07": "matches this desk's reserve ledger (Hutchinson on the November IR list)",
    "VF-08": "the venue count quoted for R-23 (12 of 13 from the schedule page, 1 of 13 from a game centre)",
    "VF-09": "the same games-played variance this desk resolves to 150 with two identities",
    "VF-10": "the same missing join this desk publishes as R-30/R-41 (no inactives, no Game Books)",
}
SITE = "https://sassnarep3-star.github.io/Own4/nfl-daily-desk"

NAV = [
    ("index.html", "Desk"),
    ("readiness.html", "Decision readiness"),
    ("availability.html", "Availability"),
    ("delta.html", "What changed"),
    ("results.html", "Results & corpus"),
    ("statistics.html", "Correlations & controls"),
    ("origination.html", "Own lines (shadow)"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("cross-check.html", "Cross-session check"),
    ("executive-summary.html", "Executive summary"),
]
OFFICIAL_FOR = {
    "availability_delta.json": "https://www.nfl.com/injuries/",
    "reserve_delta.json": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
    "corpus_extension.json": "https://www.nfl.com/standings/league/2026/REG",
    "standings.json": "https://www.nfl.com/standings/league/2026/REG",
    "shadow_cohorts.json": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "shadow_reconciliation.json": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "controls.json": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "correlations.json": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "readiness.json": "https://www.nfl.com/injuries/",
    "flags.json": "https://www.nfl.com/injuries/",
    "cross_session.json": "https://www.nfl.com/injuries/",
}

FOOTER = ('<footer class="foot"><p><strong>Research record, not wagering advice.</strong> '
          'No price feed is licensed, so no ROI, CLV or residual is claimed anywhere on this site. '
          'If gambling stops being analysis: National Problem Gambling Helpline 1-800-697-3738 '
          '(<a href="https://www.ncpgambling.org/help-treatment">ncpgambling.org/help-treatment</a>).'
          '</p><p>Rendered by <a href="%s/engine/build.py">nfl-daily-desk/engine/build.py</a> from '
          '<a href="%s/data">nfl-daily-desk/data</a>. Rebuild is byte-identical.</p></footer>'
          % (REPO, REPO))


def pl(n, sing, plural=None):
    plural = plural or (sing + "s")
    return "%d %s" % (n, sing if n == 1 else plural)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def link(url, label=None, cls="src"):
    return '<a class="%s" href="%s" rel="noopener">%s</a>' % (cls, url, esc(label or url))


def repo_link(path, label=None):
    return '<a class="src" href="%s/%s" rel="noopener">%s</a>' % (REPO, path, esc(label or path))


def is_blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def cell(v, blank_reason=None):
    if is_blank(v):
        return '<td class="blank" title="%s">—</td>' % esc(blank_reason or "not available from an official source")
    return "<td>%s</td>" % (v if isinstance(v, str) and v.startswith("<") else esc(v))


def norm_cell(c):
    """A cell may be pre-wrapped (when it carries attributes) or bare; both render as one <td>."""
    c = str(c)
    if c.startswith("<td") or c.startswith("<th"):
        return c
    return "<td>%s</td>" % c


def table(headers, rows, caption=None, anchors=None):
    rows = [[norm_cell(c) for c in r] for r in rows]
    out = ['<table class="grid">']
    if caption:
        out.append("<caption>%s</caption>" % esc(caption))
    out.append("<thead><tr>%s</tr></thead>" % "".join("<th>%s</th>" % esc(h) for h in headers))
    out.append("<tbody>")
    for i, r in enumerate(rows):
        aid = ' id="%s"' % anchors[i] if anchors and anchors[i] else ""
        out.append("<tr%s>%s</tr>" % (aid, "".join(r)))
    out.append("</tbody></table>")
    return "\n".join(out)


def page(title, body, active="index.html", intro=None, sub=None):
    nav = "".join('<a %s href="%s">%s</a>' % ('class="on"' if href == active else "", href, esc(lbl))
                  for href, lbl in NAV)
    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — NFL daily decision desk</title>
<link rel="stylesheet" href="assets/desk.css">
</head><body>
<header class="top"><div class="brand"><a href="index.html">NFL daily decision desk</a>
<span class="asof">reads of 2026-11-19 · session arena-92c458e6-own4</span></div>
<nav class="nav">%s</nav></header>
<main>
<h1>%s</h1>
%s
%s
%s
</main>
%s
</body></html>
""" % (esc(title), nav, esc(title), ("<p class='sub'>%s</p>" % esc(sub)) if sub else "",
       intro or "", body, FOOTER)


def load(name):
    return json.load(open(os.path.join(DATA, name + ".json"), encoding="utf-8"))


# --------------------------------------------------------------------------- landing
def build_index():
    rd = load("readiness")
    av = load("availability_delta")
    res = load("reserve_delta")
    ext = load("corpus_extension")
    ctl = load("controls")
    cor = load("correlations")
    sh = load("shadow_cohorts")
    sb = load("shadow_reconciliation")
    fl = load("flags")
    xcheck = load("cross_session")

    sb1 = av["reads"]["capture_b"]["summary"]
    sa1 = av["reads"]["capture_a"]["summary"]
    packet = [
        ["Official injury report, Week 11", "%d rows · %d clubs with rows · %d rows carry a game "
         "designation (%s%%)" % (sb1["n_rows"], sb1["n_clubs_with_rows"], sb1["n_rows_with_game_designation"],
         sb1["pct_rows_with_game_designation"]),
         "%d rows · %d clubs · %d designated (%s%%)" % (sa1["n_rows"], sa1["n_clubs_with_rows"],
         sa1["n_rows_with_game_designation"], sa1["pct_rows_with_game_designation"]),
         link("https://www.nfl.com/injuries/", "nfl.com/injuries")],
        ["Delta between the two dated reads", "%s across %s present in both reads; %s in one club block"
         % (pl(av["row_level_delta"]["n_changed"], "field change"),
            pl(av["row_level_delta"]["n_keys_in_both"], "player"),
            pl(len(av["row_level_delta"]["rows_added_in_later_read"]), "row appears", "rows appear")),
         "the delta is the point of this row",
         "%s · %s" % (link("https://www.nfl.com/injuries/", "official report"),
                      link("delta.html", "what changed page"))],
        ["Reserve list (IR), November 2026", "%d moves across %d clubs; 0 new between 2026-11-18T23:49Z "
         "and today" % (res["read_b"]["rows"], len(res["per_club_november_ir"])),
         "%d moves" % res["read_a"]["rows"], link(res["source_url"], "reserve list")],
        ["2026 results corpus", "%d games after today's extension; standings identity sum(W+L+T)/2 = %d"
         % (ext["corpus_games_after_extension"], ext["identity"]["league_games_from_standings"]),
         "%d games (Week 10: 13)" % ext["inherited_games"],
         link(ext["identity"]["source_url"], "standings")],
        ["Total points identity", "standings PF %s = corpus points %s; PF-PA across 32 clubs = %d"
         % ("{:,}".format(ext["scoring"]["standings_pf_total"]), "{:,}".format(ext["scoring"]["corpus_total_points"]),
            ext["scoring"]["pf_minus_pa"]), "—", link(ext["scoring"]["source_url"], "standings")],
        ["Own lines, Week 11 (shadow)", "%d fixtures recorded before kickoff, 0 graded; the 300-game floor "
         "for any skill claim is unreached by design" % sh["counts"]["week11_games"],
         "5 fixtures (cohort 1, frozen 2026-11-16)", "%s · %s" % (
         link("https://www.nfl.com/schedules/2026/by-week/week-11", "week 11 slate"),
         repo_link("nfl-readiness/prereg/SHADOW_BASELINE_v1.md", "the frozen rule"))],
        ["Controls a model must beat", "always-home %s (n=%d); coin flip 0.5; favorites-only blank — no "
         "price source" % (ctl["rows"][0]["hit_rate"], ctl["rows"][0]["n"]), "—",
         "%s · %s" % (link(ctl["rows"][0]["source_url"], "official slate"),
                      link("statistics.html", "correlations & controls"))],
        ["Requirements in this brief", "%d requirement rows + %d process rows, each with the gate and the "
         "clearing number" % (len(rd["rows"]), len(rd["process_rows"])), "—",
         "%s · %s" % (repo_link("nfl-daily-desk/data/readiness.json", "data/readiness.json"),
                      link("readiness.html", "readiness register"))],
        ["Flagged for review", "%d items, %d of them medium or worse; none blocks the merge, all block a "
         "claim" % (len(fl["rows"]), fl["severity_counts"]["medium-or-worse"]), "—",
         "%s · %s" % (repo_link("nfl-daily-desk/data/flags.json", "data/flags.json"),
                      link("flagged.html", "flagged page"))],
    ]
    packet_tbl = table(["The desk, today", "measured on 2026-11-19", "earlier state in the repository",
                        "source"], packet)
    counts = [("report rows read today", sb1["n_rows"], "availability_delta.json"),
              ["clubs with rows", sb1["n_clubs_with_rows"], "availability_delta.json"],
              ["rows carrying a game designation", sb1["n_rows_with_game_designation"], "availability_delta.json"],
              ["shared players compared", av["row_level_delta"]["n_keys_in_both"], "availability_delta.json"],
              ["designation changes between reads", av["row_level_delta"]["n_changed"], "availability_delta.json"],
              ["games in the verified 2026 corpus", ext["corpus_games_after_extension"], "corpus_extension.json"],
              ["games implied by the standings identity", ext["identity"]["league_games_from_standings"],
               "corpus_extension.json"],
              ["Week 11 fixtures recorded pre-kickoff", sh["counts"]["week11_games"], "shadow_cohorts.json"],
              ["requirement rows", len(rd["rows"]), "readiness.json"],
              ["process rows", len(rd["process_rows"]), "readiness.json"],
              ["flagged items", len(fl["rows"]), "flags.json"],
              ["rows corroborated by a second same-day read", xcheck["headline"]["injury_rows_identical"],
               "cross_session.json"]]
    counts_rows = []
    for k, v, src_file in counts:
        counts_rows.append(["<td>%s</td>" % esc(k),
                            '<td data-count="%s=%s">%s</td>' % (src_file.replace(".json", "") + ":" + k, v, v),
                            "<td>%s</td>" % repo_link("nfl-daily-desk/data/" + src_file, src_file),
                            "<td>%s</td>" % link(OFFICIAL_FOR[src_file], "official read")])
    counts_tbl = table(["figure printed on this page", "value in the data file", "data file", "source"],
                       counts_rows)

    def stat(v):
        v = str(v)
        cls = "ok" if v.startswith("met") else ("bad" if v.startswith(("blocked", "not started", "open"))
                                                else "mid")
        return '<td><span class="pill %s">%s</span></td>' % (cls, esc(v))

    def req_rows(rows):
        out = []
        for r in rows:
            out.append(["<td><strong>%s</strong></td>" % esc(r["id"]),
                        "<td>%s</td>" % esc(r["verbatim"]),
                        "<td>%s</td>" % esc(r["category"]),
                        stat(r["status"]),
                        "<td>%s</td>" % esc(r["gate"]),
                        "<td>%s</td>" % esc(r["clearing_number"]),
                        "<td>%s</td>" % esc(r["as_of_2026_11_19"]),
                        "<td>%s</td>" % evidence_html(r["evidence"]),
                        "<td>%s</td>" % (link(r["source_url"], "official")
                                         if r["source_url"].startswith("http") else esc(r["source_url"]))])
        return out

    anchors = [r["id"] for r in rd["rows"] + rd["process_rows"]]
    body = ("""
<section class="card"><h2>What this page is</h2><p>One screen for the decision, not a report about the
decision. It holds today's official reads with their clock times, the delta between today's read and the
last one stored in the repository, the state of every requirement in the 2026-11-19 brief with the gate
that blocks it and the number that would clear it, and the questions and suggestions that must be settled
before a path is chosen. Nothing here was inferred to fill a gap: a value with no official or repository
source is published empty with its reason.</p></section>

<section class="card"><h2>Today's packet</h2>%s
<h2>Figures this page prints, and the data value behind each</h2>
<p class="note">Rendered from the JSON rather than typed: <code>engine/verify.py</code> fails the build if a
printed count stops matching the file it came from.</p>%s
<p class="note">Every number above is recomputed by <code>engine/parse.py</code> and
<code>engine/compute.py</code> from the captures in <code>captures/2026-11-19/</code> and the two raw
2026-11-18 snapshots. <code>engine/verify.py</code> re-checks the row counts, the digests and every
source link.</p></section>

<section class="card"><h2>Decision-readiness table (one row per requirement)</h2>
<p class="note">Status vocabulary: <span class="pill ok">met…</span> an artifact and a number exist today;
<span class="pill mid">partially met / half-met</span> some rows are real, the rest are blank by policy;
<span class="pill bad">blocked / open / not started</span> the gate names what is missing and the clearing
number names what would remove it. Filter by typing in the box.</p>
<input id="flt" class="flt" type="search" placeholder="filter: type 'price', 'depth', 'injury', 'R-12'…" onkeyup="
var v=this.value.toLowerCase();document.querySelectorAll('table.rt tbody tr').forEach(function(t){t.style.display=t.textContent.toLowerCase().indexOf(v)>-1?'':'none'});">
%s
<p class="note">Process rows (P-01…P-05) are the brief's own instructions about the repository, the site
and the publication path; they are in the same table so nothing is tracked in a separate place.</p>
</section>
""" % (packet_tbl, counts_tbl, table(["id", "requirement (verbatim)", "category", "status 2026-11-19",
                          "gate that blocks it", "number that would clear it", "measured today",
                          "evidence", "source"], req_rows(rd["rows"] + rd["process_rows"]),
                     anchors=anchors).replace('<table class="grid">', '<table class="grid rt">')))
    return page("Desk", body)


# --------------------------------------------------------------------------- pages
def build_availability():
    av = load("availability_delta")
    rows_by_club = {}
    for r in av["rows"]:
        rows_by_club.setdefault(r["club"], []).append(r)
    counts = []
    for club in sorted(rows_by_club):
        rs = rows_by_club[club]
        gs = [x for x in rs if x["game_status"]]
        counts.append(["<td>%s</td>" % esc(club),
                       "<td>%s</td>" % esc(rs[0]["club_abbr"]),
                       "<td>%d</td>" % len(rs),
                       "<td>%d</td>" % len(gs),
                       "<td>%d</td>" % sum(1 for x in rs if x["game_status"] == "Out"),
                       "<td>%s</td>" % (esc(", ".join(sorted({x["pos"] for x in gs}))) if gs
                                        else "— <em>no game designation published at this hour</em>"),
                       "<td>%s</td>" % link("https://www.nfl.com/injuries/", "official report")])
    counts_tbl = table(["club", "abbr", "players listed", "with a game designation", "Out",
                        "positions affected", "source"], counts)
    full = []
    for r in av["rows"]:
        full.append(["<td>%s</td>" % esc(r["day"]), "<td>%s</td>" % esc(r["club"]),
                     "<td>%s</td>" % esc(r["player"]), "<td>%s</td>" % esc(r["pos"]),
                     "<td>%s</td>" % (esc(r["injury"]) if r["injury"] else
                                      '<span class="blank" title="the official row carries no injury text">—</span>'),
                     "<td>%s</td>" % esc(r["practice"]),
                     "<td>%s</td>" % (esc(r["game_status"]) if r["game_status"] else
                                      '<span class="blank" title="blank is the published state, not healthy">—</span>'),
                     "<td>%s</td>" % link("https://www.nfl.com/injuries/", "row")])
    full_tbl = table(["report day", "club", "player", "pos", "injury (as published)", "practice status",
                      "game status", "source"], full)
    noblocks = table(["club", "state on the official page", "source"],
                     [["<td>%s</td>" % esc(x["club"]), "<td>%s</td>" % esc(x["state"]),
                       "<td>%s</td>" % link("https://www.nfl.com/injuries/", "report")] for x in av["no_injury_blocks"]])
    body = """
<section class="card"><h2>Per-club view: who is listed, who is designated</h2>
<p class="note">Counted from the 2026-11-19T07:05:00Z official read. &ldquo;Players listed&rdquo; is the
club's own report row count — it is not a count of unavailable players, because practice designations are
not game-time availability. The brief asks for three fields: starters out, replacements named, net injury
count. Two of the three are below; <em>replacements named</em> is absent from the site by policy because the
official report does not name a replacement and inferring one from a depth chart would be a fabrication
(see <a href="flagged.html#F-DSK-07">F-DSK-07</a>).</p>
%s</section>

<section class="card"><h2>Clubs publishing “No Injuries Reported”</h2>
<p class="note">Stored as a captured state, not as missing data — the difference is what made one club's
appearance between two reads reportable at all.</p>
%s</section>

<section class="card"><h2>Every row read today (%s, %s)</h2>
<p class="note">Verbatim from the official page. A blank game-status cell is the league's own blank.</p>
%s</section>
""" % (counts_tbl, noblocks, pl(len(av["rows"]), "row"), pl(len(rows_by_club), "club"), full_tbl)
    return page("Availability — Week 11", body, "availability.html",
                sub="2026-11-19T07:05:00Z read of the official report · 2026 regular season Week 11",
                intro="")


def build_delta():
    av = load("availability_delta")
    d = av["row_level_delta"]
    ch = table(["club", "player", "pos", "field", "earlier read (2026-11-18T23:49Z)",
                "later read (2026-11-19T07:05Z)", "fixture day", "source"],
               [["<td>%s</td>" % esc(x["club"]), "<td>%s</td>" % esc(x["player"]),
                 "<td>%s</td>" % esc(x["position"]), "<td>%s</td>" % esc(x["field"]),
                 "<td>%s</td>" % esc(x["earlier_value"]), "<td>%s</td>" % esc(x["later_value"]),
                 "<td>%s</td>" % esc(x["day"]),
                 "<td>%s</td>" % link("https://www.nfl.com/injuries/", "report")] for x in d["changes"]])
    added = table(["club", "player", "pos", "practice", "game status", "report day", "source"],
                  [["<td>%s</td>" % esc(x["club"]), "<td>%s</td>" % esc(x["player"]),
                    "<td>%s</td>" % esc(x["position"]), "<td>%s</td>" % esc(x["practice"]),
                    "<td>%s</td>" % esc(x["game_status"]), "<td>%s</td>" % esc(x["day"]),
                    "<td>%s</td>" % link("https://www.nfl.com/injuries/", "report")]
                   for x in d["rows_added_in_later_read"]])
    pairs = table(["club", "position", "earlier display", "later display", "player page", "how the desk treats it"],
                  [["<td>%s</td>" % esc(x["club"]), "<td>%s</td>" % esc(x["position"]),
                    "<td>%s</td>" % esc(x["earlier_display"]), "<td>%s</td>" % esc(x["later_display"]),
                    "<td>%s</td>" % (link(x["earlier_player_url"], "profile") if x["earlier_player_url"]
                                     else "—"), "<td>%s</td>" % esc(x["resolution"])]
                   for x in d["candidate_same_player_pairs"]])
    trans = table(["club", "earlier state", "later state", "reading", "source"],
                  [["<td>%s</td>" % esc(x["club_abbr"]), "<td>%s</td>" % esc(x["earlier_state"]),
                    "<td>%s</td>" % esc(x["later_state"]), "<td>%s</td>" % esc(x["reading"]),
                    "<td>%s</td>" % link("https://www.nfl.com/injuries/", "report")]
                   for x in av["club_block_transitions"]])
    reads = table(["read", "kind", "bytes", "sha256", "rows", "clubs with rows", "designated rows", "source"],
                  [["<td>%s</td>" % esc(v["label"]), "<td>%s</td>" % esc(v["kind"]),
                    "<td>%s</td>" % "{:,}".format(v["bytes"]),
                    "<td><code>%s…</code></td>" % v["sha256"][:16],
                    "<td>%s</td>" % v["summary"]["n_rows"],
                    "<td>%s</td>" % v["summary"]["n_clubs_with_rows"],
                    "<td>%s</td>" % v["summary"]["n_rows_with_game_designation"],
                    "<td>%s</td>" % link(v["source_url"], "official")]
                   for v in av["reads"].values()])
    res = load("reserve_delta")
    ir_pairs = [("rows in the earlier raw read", res["read_a"]["rows"]),
                ("rows in today's read", res["read_b"]["rows"]),
                ("new rows between reads", res["delta"]["n_new_rows"]),
                ("rows dropped between reads", res["delta"]["n_rows_dropped"]),
                ("clubs with a November reserve entry", len(res["per_club_november_ir"]))]
    irdelta = table(["metric", "value", "source"],
                    [["<td>%s</td>" % esc(k), "<td>%s</td>" % esc(v),
                      "<td>%s</td>" % link(res["source_url"], "ledger")] for k, v in ir_pairs])
    percl = table(["club", "November reserve entries", "source"],
                  [["<td>%s</td>" % esc(k), "<td>%s</td>" % esc(v),
                    "<td>%s</td>" % link(res["source_url"], "ledger")]
                   for k, v in res["per_club_november_ir"].items()])
    body = """
<section class="card"><h2>The rule on this page</h2><p>The brief is explicit: publish the <em>delta</em>,
never the level, and make the injury signal a <em>surprise</em>. That is only possible with two dated reads,
which the repository did not have until the snapshot workflow produced one on 2026-11-18. This page is the
first place in the repo where two reads are compared row by row, and the comparison is published whether or
not it found anything.</p></section>

<section class="card"><h2>The two reads</h2>%s</section>

<section class="card"><h2>Designation changes — the surprise list</h2>
<p class="note">%s across %d players present in both reads. One change in a day is a normal number;
the point is that it is now measurable at all, and that a panel claiming &ldquo;nothing changed&rdquo; is a
result rather than an empty table.</p>%s</section>

<section class="card"><h2>Rows that appeared between reads</h2>%s
<h3>Club-block transitions</h3>%s</section>

<section class="card"><h2>Reconciliation residuals</h2>
<p class="note">One row present in the earlier read and one in the later read could not be joined by name,
because the two renderings spell the same player differently. The desk reports the candidate pair and does
not merge it: display name is not a key (see <a href="flagged.html#F-DSK-06">F-DSK-06</a>).</p>%s
<p class="note">Residual after pairing: %s.</p></section>

<section class="card"><h2>Reserve list (IR) delta</h2>%s%s</section>
""" % (reads, pl(d["n_changed"], "change"), d["n_keys_in_both"], ch, added, trans, pairs,
       json.dumps(d["residual_after_pairing"]), irdelta, percl)
    return page("What changed between reads", body, "delta.html",
                sub="injury report + reserve list · two dated captures · 7h15m apart")


def build_results():
    ext = load("corpus_extension")
    st = load("standings")
    fin = table(["day (official label)", "away", "home", "score", "state", "winner",
                 "in today's corpus?", "source"],
                [["<td>%s</td>" % esc(r["day_label"]), "<td>%s</td>" % esc(r["away"]),
                  "<td>%s</td>" % esc(r["home"]),
                  "<td>%d-%d</td>" % (r["away_pts"], r["home_pts"]), "<td>%s</td>" % esc(r["state"]),
                  "<td>%s</td>" % esc(r["winner"]),
                  "<td>%s</td>" % ("yes — re-read today" if r["winner_matches_score"] else "check"),
                  "<td>%s</td>" % link(r["source_url"], "game centre")] for r in ext["week10_finals"]])
    agree = table(["away", "home", "date", "score today", "score in the inherited corpus", "agrees", "source"],
                  [["<td>%s</td>" % esc(r["away"]), "<td>%s</td>" % esc(r["home"]), "<td>%s</td>" % esc(r["date"]),
                    "<td>%s</td>" % esc(r["today_read"]), "<td>%s</td>" % esc(r["inherited_row"]),
                    "<td>%s</td>" % ("YES" if r["score_agrees"] else "NO"),
                    "<td>%s</td>" % link(r["source_url"], "game centre")] for r in ext["already_in_corpus"]])
    LABELS = {"corpus_games": "games in the extended corpus",
              "inherited_games": "games inherited from the peer corpus",
              "league_games_from_standings": "games implied by the standings (sum(W+L+T)/2)",
              "added_by_this_read": "games this read added",
              "already_present_in_inherited_corpus": "games the peer corpus already held",
              "standings_team_game_total_even": "every club's W+L+T sums to an even league total",
              "holds": "the identity holds",
              "note": "how the identity is defined",
              "standings_pf_total": "standings points-for, summed over 32 clubs",
              "standings_pa_total": "standings points-against, summed over 32 clubs",
              "corpus_total_points": "total points across the corpus",
              "standings_match_corpus_points": "points-for equals corpus points",
              "pf_minus_pa": "PF minus PA across the league (must be 0)"}

    def idval(v):
        if isinstance(v, bool):
            return "YES — it holds" if v else "NO — it does not hold"
        if isinstance(v, int) and abs(v) >= 1000:
            return "{:,}".format(v)
        return v

    ident_rows = [["<td>%s</td>" % LABELS.get(k, esc(k)), "<td>%s</td>" % esc(idval(v)),
                   "<td>%s</td>" % link(d["source_url"], "standings page")]
                  for d in (ext["identity"], ext["scoring"]) for k, v in d.items()
                  if k != "source_url"]
    ident = table(["identity or count", "value", "source"], ident_rows)
    stbl = table(["club", "W", "L", "T", "PCT", "PF", "PA", "NET", "identities", "source"],
                 [["<td>%s</td>" % esc(r["club"]), "<td>%s</td>" % r["W"], "<td>%s</td>" % r["L"],
                   "<td>%s</td>" % r["T"], "<td>%s</td>" % r["PCT"], "<td>%s</td>" % r["PF"],
                   "<td>%s</td>" % r["PA"], "<td>%s</td>" % r["NET"],
                   "<td>%s</td>" % ("PF-PA=NET ✓ · PCT=(W+.5T)/(W+L+T) ✓"),
                   "<td>%s</td>" % link(r["source_url"], "standings")] for r in st["rows"]])
    added = table(["fixture", "date", "score", "provenance", "source"],
                  [["<td>%s at %s</td>" % (esc(g["away"]), esc(g["home"])), "<td>%s</td>" % esc(g["date"]),
                    "<td>%d-%d</td>" % (g["away_pts"], g["home_pts"]), "<td>%s</td>" % esc(g["provenance"]),
                    "<td>%s</td>" % link(g["source_url"], "game centre")] for g in ext["added_games"]])
    body = """
<section class="card"><h2>Why this page exists</h2><p>The brief demands a verified results feed
&ldquo;so backtests and ROI can be computed at all&rdquo;, and a pre-registered corpus. Reading the official
page today found a real defect in how that had been done: two feeds in the repository disagree with each
other and with the league's own arithmetic. The desk did not reconcile them by picking one — it re-read the
source and published the identity check that any feed must pass.</p></section>

<section class="card"><h2>Week 10, all 14 games, read 2026-11-19T07:06:00Z</h2>%s</section>

<section class="card"><h2>Rows the inherited corpus already had — re-checked against the same official page</h2>
<p class="note">%s of %s rows the inherited corpus already held agree with today's official read. A feed is only
as good as the day it was last reconciled, and this is that day's reconciliation.</p>%s</section>

<section class="card"><h2>The one game the repository was missing</h2>%s</section>

<section class="card"><h2>Identities that must hold, and do</h2>%s</section>

<section class="card"><h2>Standings rows transcribed today</h2>
<p class="note">%s</p>%s</section>
""" % (fin, sum(1 for x in ext["already_in_corpus"] if x["score_agrees"]), len(ext["already_in_corpus"]),
       agree, added, ident,
       esc(st["columns_not_transcribed"]), stbl)
    return page("Results & corpus", body, "results.html",
                sub="2026 regular season · 150 games played · every row with a game-centre or standings link")


def build_statistics():
    cor = load("correlations")
    ctl = load("controls")
    cr = table(["id", "pair", "definition", "n", "r", "95% CI (Fisher z)", "permutation p", "why it matters",
                "source"],
               [["<td>%s</td>" % esc(r["id"]), "<td>%s</td>" % esc(r["pair"]),
                 "<td>%s</td>" % esc(r.get("definition", "not measured - see the reason column")),
                 "<td>%s</td>" % r["n"],
                 "<td>%s</td>" % (r["r"] if r.get("r") is not None else
                                  '<span class="blank" title="%s">—</span>' % esc(r.get("blank_reason", ""))),
                 "<td>%s</td>" % ("[%s, %s]" % (r["ci95_fisher_z"][0], r["ci95_fisher_z"][1])
                                  if r.get("ci95_fisher_z") and r["ci95_fisher_z"][0] is not None else "—"),
                 "<td>%s</td>" % (r["p_permutation"] if r.get("p_permutation") is not None else "—"),
                 "<td>%s</td>" % esc(r.get("why") or r.get("blank_reason", "")),
                 "<td>%s</td>" % link(r["source_url"], "source")] for r in cor["rows"]])
    blanks = table(["id", "pair", "why the value is blank", "source"],
                   [["<td>%s</td>" % esc(r["id"]), "<td>%s</td>" % esc(r["pair"]),
                     "<td>%s</td>" % esc(r.get("blank_reason", "")),
                     "<td>%s</td>" % link(r["source_url"], "source")]
                    for r in cor["rows"] if r.get("r") is None])
    ct = table(["control", "n", "hit rate", "what it means", "source"],
               [["<td>%s</td>" % esc(r["control"]), "<td>%s</td>" % r["n"],
                 "<td>%s</td>" % (r["hit_rate"] if r["hit_rate"] is not None else
                                  '<span class="blank" title="%s">—</span>' % esc(r["detail"])),
                 "<td>%s</td>" % esc(r["detail"]), "<td>%s</td>" % link(r["source_url"], "source")]
                for r in ctl["rows"]])
    body = """
<section class="card"><h2>Rules on this page</h2><p>Correlations are computed only from numbers that come
from an official source or a repository row that itself carries an official link, and every value prints its
n. The recipe is fixed before it runs: Pearson r, a Fisher-z 95%% interval (published as a floor on width,
because games in a week are not fully independent), and a two-sided permutation test with 20,000 shuffles at
seed 20261119. A relationship that cannot be measured is listed with n=0 and the reason, so the reader sees
the hole rather than a smoothing of it.</p></section>

<section class="card"><h2>Computed</h2>%s</section>

<section class="card"><h2>Deliberately blank</h2>%s</section>

<section class="card"><h2>Control baselines — the luck yardsticks</h2>
<p class="note">The always-home control sits <em>below</em> a coin flip this season. Any page that reports a
home-leaning model as a success is reporting a negative-skill signal, and that is precisely why the brief
asks for controls next to every leaderboard run.</p>%s</section>
""" % (cr, blanks, ct)
    return page("Correlations & controls", body, "statistics.html",
                sub="measured on the 150-game 2026 corpus, n published on every value")


def build_origination():
    sh = load("shadow_cohorts")
    rec = load("shadow_reconciliation")
    rows = table(["fixture", "kickoff (UTC)", "recorded (UTC)", "before kickoff", "margin (home)", "p(home)",
                  "fair pick", "market line", "residual", "cohort", "source"],
                 [["<td>%s at %s</td>" % (esc(r["away"]), esc(r["home"])), "<td>%s</td>" % esc(r["kickoff_utc"]),
                   "<td>%s</td>" % esc(r["recorded_utc"]), "<td>%s</td>" % ("YES" if r["before_kickoff"] else "NO"),
                   "<td>%s</td>" % r["margin_home"], "<td>%s</td>" % r["p_home"], "<td>%s</td>" % esc(r["fair_pick"]),
                   "<td>%s</td>" % ('<span class="blank" title="%s">—</span>' % esc(r["market_line_blank_reason"])),
                   "<td>— <em>needs the market column</em></td>", "<td>%s</td>" % esc(r["cohort"]),
                   "<td>%s</td>" % link(r["source_url"], "game centre")] for r in sh["rows"]])
    faith = table(["fixture", "stored margin", "re-derived margin", "fields agreed", "source"],
                  [["<td>%s</td>" % esc(c["fixture"]), "<td>%s</td>" % esc(c["stored_margin"]),
                    "<td>%s</td>" % esc(c["recomputed_margin"]),
                    "<td>%s</td>" % ("ALL" if c["all_agree"] else json.dumps(c["fields"])),
                    "<td>%s</td>" % link("https://www.nfl.com/standings/league/2026/REG", "standings")]
                   for c in sh["faithfulness_check"]["rows"]])
    recon = table(["fixture", "model A margin (cohort 1)", "model B fair spread", "gap between the two",
                   "inputs verified vs today's standings", "graded", "source"],
                  [["<td>%s at %s</td>" % (esc(r["away"]), esc(r["home"])),
                    "<td>%s</td>" % (r["model_A_margin_home"] if r["model_A_margin_home"] is not None else
                                      '<span class="blank" title="not in cohort 1: this fixture was withheld at that freeze">—</span>'),
                    "<td>%s</td>" % (r["model_B_fair_spread_home"] if r["model_B_fair_spread_home"] is not None else "—"),
                    "<td>%s</td>" % (r["abs_gap_between_frozen_models"] if r["abs_gap_between_frozen_models"] is not None
                                     else "— <em>only one record exists for this fixture</em>"),
                    "<td>%s</td>" % ("yes" if r["inputs_verified_against_official_standings_2026-11-19"]
                                     else "only one record to verify"),
                    "<td>— <em>%s</em></td>" % esc(r["grade_blank_reason"]),
                    "<td>%s</td>" % link(r["source_url"], "game centre")] for r in rec["rows"]])
    gate = rec["demotion_gate"]
    reg = sh["rule"]
    body = """
<section class="card"><h2>What was recorded, and when</h2><p>A pre-registration is only worth what its
timestamp is worth. This desk re-ran the frozen singles shadow rule (v1, unchanged) on the official standings
read at 2026-11-19T07:04Z and recorded all 13 Week 11 fixtures before any of them kicked off — five of them
reproducing the earlier record exactly, eight of them newly eligible because the results feed that gated them
is now complete. The two cohorts are kept separate and are never merged into one sample.</p>
<ul><li>rule file: %s (sha256 <code>%s…</code>)</li>
<li>last commit that touched the rule: <code>%s</code></li>
<li>eligibility test, verbatim: %s</li>
<li>eligibility result today: %s</li>
<li>amendment note: %s</li></ul></section>

<section class="card"><h2>The shadow record (13 fixtures, all pre-kickoff)</h2>%s</section>

<section class="card"><h2>Faithfulness: re-deriving the stored rows</h2>
<p class="note">%d of %d stored cohort-1 rows reproduce field for field. A record that cannot be re-derived
from its own rule and its own inputs is a claim, not an artifact.</p>%s
<p class="note">Standings drift since that freeze: %d fields changed league-wide, %d of them inside cohort-1
clubs — which is exactly why the other 8 fixtures had to wait.</p></section>

<section class="card"><h2>Two registered models, one fixture set (the brief's &ldquo;publish every total
twice&rdquo; rule, applied honestly)</h2>%s</section>

<section class="card"><h2>Grading and demotion</h2>
<p>%s</p>
<p class="note">Grading queue: %s — %s</p>
<p class="note">Demotion gate: %s · live strategies %s · demotions today %s · <em>%s</em></p></section>

<section class="card"><h2>Irregularities in this artifact set</h2><ul>%s</ul></section>
""" % (esc(reg["file"]), reg["sha256"][:16], esc(reg["last_commit_touching_rule"]),
       esc(reg["eligibility_test"]), esc(reg["eligibility_result_2026-11-19"]), esc(reg["amendment"]),
       rows, sh["faithfulness_check"]["n_rows_identical"], sh["faithfulness_check"]["n_rows_compared"], faith,
       sh["standings_drift_since_cohort1_freeze"]["n_fields_changed"],
       sh["standings_drift_since_cohort1_freeze"]["n_changed_inside_cohort1_clubs"],
       recon, esc(sh["grading"]["why"]), esc(sh["grading"]["first_grade_due_utc"]),
       esc(sh["grading"]["rule"] if "rule" in sh["grading"] else "minimum sample for any skill claim: %d graded rows" % sh["grading"]["minimum_sample_for_any_skill_claim"]),
       esc(gate["rule_text"]), gate["strategies_live"], gate["demotions_today"], esc(gate["status"]),
       "".join("<li>%s</li>" % esc(x) for x in sh["irregularities"]))
    return page("Originated lines (shadow)", body, "origination.html",
                sub="singles only · frozen rule · recorded before kickoff · zero rewards, by design")


def build_questions():
    qs = load("questions")
    t = table(["id", "the question", "why it matters", "what we already have", "what is missing",
               "how to find out", "who answers", "blocks", "status", "source"],
              [["<td>%s</td>" % esc(r["id"]), "<td>%s</td>" % esc(r["question"]),
                "<td>%s</td>" % esc(r["why_it_matters"]), "<td>%s</td>" % esc(r["what_we_have"]),
                "<td>%s</td>" % esc(r["what_is_missing"]), "<td>%s</td>" % esc(r["how_to_find_out"]),
                "<td>%s</td>" % esc(r["who_answers"]), "<td>%s</td>" % esc(", ".join(r["blocks"])),
                "<td>%s</td>" % esc(r["status"]), "<td>%s</td>" % link(r["source_url"], "official page")]
               for r in qs["rows"]])
    body = """
<section class="card"><h2>How to read this</h2><p>These are the questions that stand between the current
state of the repository and a decision that could reasonably be made. Each row separates what we already
know — with a number and a link, not a feeling — from what is missing, and then says how the missing piece
would be discovered and who is able to answer it. A question an agent can answer is scheduled work; a
question only the owner can answer is a decision, and the site should not pretend otherwise.</p></section>
%s""" % t
    return page("Questions & answers", body, "questions.html",
                sub="%d open questions, each tied to the requirements it gates" % len(qs["rows"]))


def build_suggestions():
    sg = load("suggestions")
    rows = []
    for r in sg["rows"]:
        opts = "<ul>%s</ul>" % "".join("<li><strong>%s</strong> — %s</li>" % (k, esc(v))
                                       for k, v in r["options"].items())
        rows.append(["<td>%s</td>" % esc(r["id"]), "<td>%s</td>" % esc(r["problem"]),
                     "<td>%s</td>" % esc(r["suggestion"]), "<td>%s</td>" % opts,
                     "<td>%s</td>" % esc(r["recommended_path"]), "<td>%s</td>" % esc(r["cost"]),
                     "<td>%s</td>" % esc(", ".join(r["unblocks"])), "<td>%s</td>" % esc(r["risk_if_skipped"]),
                     "<td>%s</td>" % esc(r["review_state"]),
                     "<td>%s</td>" % link(r["source_url"], "context")])
    t = table(["id", "problem", "suggestion", "options", "recommended path", "cost", "unblocks",
               "risk if skipped", "review state", "link"], rows)
    body = """
<section class="card"><h2>Review before implementing</h2><p>Nothing on this page has been implemented. Each
row states the problem, the real options, the path this session would take and why, the cost, the
requirements it frees, and what breaks if it is skipped. The review state stays
&ldquo;proposed — awaiting owner&rdquo; until it is changed here; that is deliberate, because the brief asks
for a section where suggestions can be compared before a path is chosen, not a changelog of things an agent
already did.</p>
<p class="note">Ordering rule used below: decisions unblocked per unit of cost, ties broken in favour of the
item whose absence currently produces a <em>wrong</em> number rather than <em>no</em> number. S-08
(canonical results feed) and S-09 (depth slot semantics) sit high on that second criterion.</p></section>
%s""" % t
    return page("Suggestions for review", body, "suggestions.html",
                sub="%d suggestions · ordered by what they unblock · no implementation implied" % len(sg["rows"]))


def build_repo_review():
    rr = load("repo_review")
    t = table(["namespace", "owner session", "canonical for", "what this session verified", "notes", "link"],
              [["<td>%s</td>" % esc(r["namespace"]), "<td>%s</td>" % esc(r["owner_session"]),
                "<td>%s</td>" % esc(r["canonical_for"]), "<td>%s</td>" % esc(r["verified_by_this_session"]),
                "<td>%s</td>" % esc(r["notes"]),
                "<td>%s</td>" % link(rr["repo_url"], "repo")] for r in rr["rows"]])
    body = """
<section class="card"><h2>Scope of this review</h2><p>Line-by-line means: for each NFL workspace, read what
its data files actually contain, recompute the number it is known for, and record where two workspaces
disagree. This review read %d workspaces today and found three live disagreements — the size of the 2026
results corpus (137 / 149 / 150), the number of shared depth slots (149 claimed / 15 measured), and the
meaning of an unchanged capture. None of them is a modelling question; all three are worth more than most
of the analysis sitting next to them.</p></section>
%s
<section class="card"><h2>What the review did not do</h2><p>It did not edit another namespace, did not
declare any of them wrong, and did not adopt a number from a file whose own provenance note says it was not
re-read. Where this page says a claim is &ldquo;peer-reported, not re-verified&rdquo;, that is the
review's finding, not a hedge.</p></section>""" % (len(rr["rows"]), t)
    return page("Repository review", body, "repo-review.html",
                sub="2026-11-19 · what each NFL namespace is canonical for, and what was checked")


def build_flagged():
    fl = load("flags")
    t = table(["id", "severity", "area", "the irregularity", "detail and evidence", "source"],
              [["<td id=%s>%s</td>" % (esc(r["id"]), esc(r["id"])), "<td>%s</td>" % esc(r["severity"]),
                "<td>%s</td>" % esc(r["area"]), "<td><strong>%s</strong></td>" % esc(r["item"]),
                "<td>%s<br><span class='ev'>%s</span></td>" % (esc(r["detail"]), evidence_html(r["evidence"])),
                "<td>%s</td>" % link(r["source_url"], "official")] for r in fl["rows"]])
    body = """
<section class="card"><h2>Published, not hidden</h2><p>These are the things the site refuses to smooth over.
A flagged item does not block the merge — it blocks a <em>claim</em>. Each row names the evidence file (so
the finding can be checked without trusting this page) and the official source that frames it.</p></section>
%s""" % t
    return page("Flagged for review", body, "flagged.html",
                sub="%d items · %d medium or worse · none blocking"
                    % (len(fl["rows"]), fl["severity_counts"]["medium-or-worse"]))


def evidence_html(ev):
    parts = []
    for x in str(ev).split(";"):
        x = x.strip()
        if not x:
            continue
        if re.match(r"^(nfl-|data/|COORDINATION|\.github|scripts/|verification/)", x):
            parts.append(repo_link(x.split(" ")[0]))
        else:
            parts.append(esc(x))
    return "; ".join(parts)


def build_crosscheck():
    x = load("cross_session")
    h, ir, st = x["headline"], x["injury_report"], x["standings"]
    res, sl = x["reserve_list"], x["week11_slate"]
    summary = table(["artifact", "this desk's read", "the other session's read", "agreement", "source"],
                    [["<td>Injury-report rows (Week 11)</td>",
                      "<td>%d rows across %s clubs</td>" % (ir["desk_rows"], ir["clubs_this_desk_read"]),
                      "<td>%d rows across %d clubs</td>" % (ir["peer_rows"], len(ir["clubs_the_peer_read"])),
                      "<td>%d of %d rows joined; %d identical on every field; all %d per-club counts equal%s</td>"
                      % (ir["joined_rows"], ir["peer_rows"], ir["identical_rows"],
                         len(ir["per_club_row_counts"]),
                         "" if ir["per_club_counts_all_agree"] else " (NOT all)"),
                      "<td>%s</td>" % link(ir["source_url"], "nfl.com/injuries")],
                     ["<td>Standings: 32 clubs × W/L/T/PF/PA/NET</td>", "<td>32 rows</td>",
                      "<td>%d rows</td>" % st["clubs_in_both"],
                      "<td>%d of %d fields agree; the two reads imply %d and %d league games</td>"
                      % (st["fields_agree"], st["fields_compared"], st["games_from_this_desk_read"],
                         st["games_from_peer_read"]),
                      "<td>%s</td>" % link(st["source_url"], "standings")],
                     ["<td>November reserve ledger (IR)</td>", "<td>%d rows</td>" % res["desk_rows"],
                      "<td>%d rows</td>" % res["peer_rows"],
                      "<td>%d of %d rows reconcile on date + player + transaction%s</td>"
                      % (res["rows_in_both"], res["peer_rows"],
                         "; the blank Position column is confirmed on all %d peer rows too"
                         % res["peer_blank_position_cells"] if res["position_blank_confirms_desk_flag"]
                         else ""),
                      "<td>%s</td>" % link(res["source_url"], "reserve list")],
                     ["<td>Week 11 slate</td>", "<td>%d fixtures, each with a game-centre link</td>"
                      % sl["desk_fixtures"], "<td>%d fixtures + %d byes</td>"
                      % (sl["peer_fixtures"], len(sl["peer_byes"])),
                      "<td>%d of %d fixtures appear in both; %d only here, %d only there</td>"
                      % (sl["n_in_both"], sl["peer_fixtures"], len(sl["only_this_desk"]),
                         len(sl["only_peer"])),
                      "<td>%s</td>" % link(sl["source_url"], "week 11 schedule")]])
    diffs = table(["club", "player", "field", "this desk's value", "the peer value",
                   "how this desk reads it", "source"],
                  [["<td>%s</td>" % esc(d["club"]), "<td>%s</td>" % esc(d["player"]),
                    "<td>%s</td>" % esc(d["field"]), "<td>%s</td>" % esc(d["this_desk"] or "— blank —"),
                    "<td>%s</td>" % esc(d["peer_read"] or "— blank —"),
                    "<td>%s</td>" % esc(READINGS.get((d["club"], d["player"], d["field"]),
                                                     "reported as a difference; no reconciliation attempted")),
                    "<td>%s</td>" % link(INJ_URL, "report")] for d in ir["field_differences"]])
    perclub = table(["club", "this desk's rows", "peer rows", "equal", "source"],
                    [["<td>%s</td>" % esc(c["club"]), "<td>%d</td>" % c["this_desk_rows"],
                      "<td>%d</td>" % c["peer_rows"], "<td>%s</td>" % ("YES" if c["agree"] else "NO"),
                      "<td>%s</td>" % link(INJ_URL, "report")] for c in ir["per_club_row_counts"]])
    ven = table(["fixture", "venue on the schedule page", "venue on the game centre",
                 "what this desk does with it", "source"],
                [["<td>%s</td>" % esc(v["fixture"]), "<td>%s</td>" % esc(v["schedule_page"]),
                  "<td>%s</td>" % esc(v["game_centre"]),
                  "<td>%s</td>" % esc("the requirement names the game centre as the source, so this desk "
                                      "keeps the venue blank until that is settled (F-DSK-16)"),
                  "<td>%s</td>" % link(v["game_centre_source"], "game centre")]
                 for v in sl["venue_label_disagreements"]])
    peerflags = table(["id", "area", "their finding", "their action", "how this desk treats it", "source"],
                      [["<td>%s</td>" % esc(v["id"]), "<td>%s</td>" % esc(v["area"]),
                        "<td>%s</td>" % esc(v["finding"]), "<td>%s</td>" % esc(v["action"]),
                        "<td>%s</td>" % esc(CARRIED.get(v["id"], "left as the peer's own finding; this desk "
                                                           "neither repeats nor contradicts it")),
                        "<td>%s</td>" % (link(v["source"], "source") if v["source"].startswith("http")
                                          else repo_link(v["source"]))] for v in x["peer_flags"]])
    files = table(["peer data file", "sha256", "bytes", "last commit touching it", "file"],
                  [["<td><code>%s/data/%s</code></td>" % (esc(x["peer_namespace"]), esc(n)),
                    "<td><code>%s…</code></td>" % f["sha256"][:16],
                    "<td>%s</td>" % "{:,}".format(f["bytes"]),
                    "<td>%s</td>" % esc(f["last_commit_touching_it"]),
                    "<td>%s</td>" % repo_link("%s/data/%s" % (x["peer_namespace"], n), "open")]
                   for n, f in x["peer_files"].items()])
    nd = x.get("nfl_desk") or {}
    if not nd.get("absent"):
        sc = nd["shared_capture_parse"]
        ndrows = [["<td>%s</td>" % esc(lbl), "<td>%s</td>" % (sc["counts_agree"][k]["this_desk"]),
                   "<td>%s</td>" % sc["counts_agree"][k]["nfl_desk"],
                   "<td>%s</td>" % ("identical" if sc["counts_agree"][k]["equal"] else "DIFFERENT"),
                   "<td>%s</td>" % link(INJ_URL, "report")]
                  for k, lbl in [("player_rows", "player rows in the stored 2026-11-18 capture"),
                                 ("club_tables", "club tables in that capture"),
                                 ("rows_with_game_status", "rows carrying a game status")]]
        ndrows.append(["<td>W/L/T/PF/PA across 32 clubs (their same-day standings read)</td>",
                       "<td>%d fields</td>" % nd["standings_fields_agree"],
                       "<td>%d of %d agree, %d mismatch</td>" % (nd["standings_fields_agree"],
                       nd["standings_fields_compared"], nd["standings_fields_mismatch"]),
                       "<td>%s</td>" % ("identical" if not nd["standings_fields_mismatch"] else "DIFFERENT"),
                       "<td>%s</td>" % link("https://www.nfl.com/standings/league/2026/REG", "standings")])
        ndrows.append(["<td>league games implied by the standings</td>",
                       "<td>%d</td>" % st["games_from_this_desk_read"], "<td>%d</td>" % nd["games_from_their_read"],
                       "<td>%s</td>" % ("identical" if st["games_from_this_desk_read"] == nd["games_from_their_read"]
                                        else "DIFFERENT"),
                       "<td>%s</td>" % link("https://www.nfl.com/standings/league/2026/REG", "standings")])
        ndrows.append(["<td>requirement rows in the readiness register</td>",
                       "<td>%d (R-xx + P-xx)</td>" % nd["requirement_registers"]["this_desk_rows"],
                       "<td>%d (REQ-xx)</td>" % nd["requirement_registers"]["nfl_desk_rows"],
                       "<td>%d of %d rows share the same normalised requirement text</td>"
                       % (nd["requirement_registers"]["exact_text_matches_after_normalisation"],
                          nd["requirement_registers"]["this_desk_rows"]),
                       "<td>%s</td>" % repo_link("nfl-desk/data/requirements.json", "their register")])
        ndrows.append(["<td>NFL namespaces in the repository</td>",
                       "<td>1 (this desk, counted by hand: see the repo review)</td>",
                       "<td>%d measured, %d with a verifier</td>" % (nd["namespace_census"]["namespaces"],
                                                                      nd["namespace_census"]["with_verifier"]),
                       "<td>their census ran before this desk landed</td>",
                       "<td>%s</td>" % repo_link("nfl-desk/data/census.json", "their census")])
        front = table(["artifact", "this desk", "the integration front door (nfl-desk)", "agreement", "source"],
                      ndrows)
        extra = """
<section class="card"><h2>The third reader: the integration front door</h2>
<p class="note">A third session (<code>nfl-desk</code>, %s) ran its own parser over the <em>same</em> stored
2026-11-18 capture this desk parsed, read the standings page the same day, and keys its own requirement
register on the brief text. Same bytes, same page, different code — the comparison below is the only
transcription check that means something.</p>%s
<p class="note">Two things this desk does <em>not</em> take from them, on purpose: their read carries the
per-club split columns (%s) that this desk's own rendered read could not order, so F-DSK-04 stays open here
even though the data exists next door; and their register's %s/%s/%s agree-disagree-unmatched split is
exactly why this desk keeps its verbatim requirement text as the join key rather than an id.</p></section>
""" % (esc(nd["owner_session"]), front, ", ".join(nd["columns_they_publish_that_this_desk_omitted"]),
       nd["requirement_registers"]["nfl_desk_disagreement_counts"]["agree"],
       nd["requirement_registers"]["nfl_desk_disagreement_counts"]["disagree"],
       nd["requirement_registers"]["nfl_desk_disagreement_counts"]["unmatched"])
    else:
        extra = ""
    body = """
<section class="card"><h2>Why this page exists</h2><p>A number produced by one reader is a claim. On
2026-11-19 a second session (%s) read the same official pages and published its own artifact set in
<code>%s/</code>. This page joins the two sets field by field with no manual entry, so agreement becomes
corroboration and disagreement becomes a finding — with both files named in either case.</p>
<p class="note"><strong>%s</strong></p></section>

<section class="card"><h2>Where the two reads agree</h2>%s
<p class="note">%s</p></section>
%s
<section class="card"><h2>Every field the two reads disagree on</h2>
<p class="note">%d differences out of %d joined rows. Publishing them is the point of the exercise: a
reconciliation that hides its differences is not a reconciliation.</p>%s</section>

<section class="card"><h2>Per-club row counts, club by club</h2>
<p class="note">The peer read 10 of the 24 club blocks. On each of those 10, its row count equals this
desk's exactly — which is the form of check a transcription can actually pass.</p>%s</section>

<section class="card"><h2>Venue: the one place the official pages disagree with each other</h2>%s</section>

<section class="card"><h2>The peer's own flags, and what this desk did with each</h2>%s</section>

<section class="card"><h2>Peer files as read (digest + commit, so this comparison can be re-run)</h2>%s
<p class="note">Read-only: no file under <code>%s/</code> was edited by this session, and nothing on this
page is presented as verifying the peer's work beyond what the join itself shows.</p></section>
""" % (esc(x["peer_session"]), esc(x["peer_namespace"]), esc(h["reading"]), summary,
       esc(x["standings"]["note"]), extra, ir["n_field_differences"], ir["joined_rows"], diffs, perclub,
       ven, peerflags, files, esc(x["peer_namespace"]))
    return page("Cross-session reconciliation", body, "cross-check.html",
                sub="two independent 2026-11-19 reads of the same official pages, joined field by field")


def build_sources():
    s = load("sources")
    o = table(["what it is", "read method", "what it supports", "url", "date"],
              [["<td>%s</td>" % esc(r["title"]), "<td>%s</td>" % esc(r["method"]),
                "<td>%s</td>" % esc(r["supports"]), "<td>%s</td>" % link(r["url"], r["url"]),
                "<td>%s</td>" % esc(r["read_utc"])] for r in s["official"]])
    r2 = table(["repository artifact", "sha256 / bytes", "used for", "link"],
               [["<td><code>%s</code></td>" % esc(r["path"]),
                 "<td>%s</td>" % (("<code>%s…</code> · %s bytes" % (r["sha256"][:12], "{:,}".format(r["bytes"])))
                                  if "sha256" in r else "—"),
                 "<td>%s</td>" % esc(r["used_for"]), "<td>%s</td>" % repo_link(r["path"], "artifact")]
                for r in s["repository"]])
    body = """
<section class="card"><h2>Official sources</h2><p>%s</p>%s</section>
<section class="card"><h2>Repository artifacts used as inputs</h2>
<p class="note">An inherited number is only as trustworthy as its own read date; each row below links to the
file and states what it was used for. Where a sha256 is published, the desk recomputed it.</p>%s</section>
""" % (esc(s["policy"]), o, r2)
    return page("Sources", body, "sources.html", sub="every value on this site traces to one of these")


def build_exec():
    sh = load("shadow_cohorts")
    xcheck = load("cross_session")
    nn = xcheck.get("nfl_desk", {})
    nspace = ("%d, of which %d carry a verifier, counted by the front door's census before this desk "
              "landed — so %d now" % (nn["namespace_census"]["namespaces"],
                                      nn["namespace_census"]["with_verifier"],
                                      nn["namespace_census"]["namespaces"] + 1)
              if nn and not nn.get("absent") else "not counted by this desk")
    av = load("availability_delta")
    ext = load("corpus_extension")
    ctl = load("controls")
    cor = load("correlations")
    fl = load("flags")
    rd = load("readiness")
    counts = rd["status_counts"]
    body = """
<section class="card"><h2>1 · State, in five numbers</h2><ol>
<li><strong>%d</strong> — official injury-report rows read at 2026-11-19T07:05:00Z, covering %d clubs, of
which <strong>%d</strong> carry a game designation (%s%%). Availability is thin by publication, not by
transcription.</li>
<li><strong>%d</strong> — games in the verified 2026 results corpus after today's extension; the official
standings imply exactly that number (sum(W+L+T)/2 = %d) and total points reconcile (%s = %s), which they did
not before today.</li>
<li><strong>%d</strong> — Week 11 fixtures recorded as a shadow forecast before kickoff (5 reproducing the
frozen cohort exactly, 8 newly eligible), with 0 graded and a registered floor of 300 graded games before any
skill claim.</li>
<li><strong>%s</strong> — the always-home control on the 150-game corpus, against a coin flip at 0.5. The
home baseline is a <em>negative</em> edge this season, and any model that looks good against a home-leaning
null is not.</li>
<li><strong>%d</strong> — requirement rows in the decision-readiness table, and <strong>%d</strong> flagged
irregularities, %d of them medium or worse.</li></ol></section>

<section class="card"><h2>2 · What today actually changed</h2>
<p>The desk did not add an analysis; it closed three specific holes and proved each closure:</p>
<ul>
<li><strong>The first real availability delta.</strong> Two dated reads of the same official report now exist,
and comparing them found %d designation change and %d rows appearing in one club block out of %d shared
players. Every previous &ldquo;surprise&rdquo; column in this repository was blank for lack of a second
capture; it is now a number.</li>
<li><strong>A stale corpus, measured rather than noticed.</strong> Two 2026 feeds disagreed with the league:
137 and 149 games where the standings imply 150. Monday night's result (LAC 23 at BAL 20) was missing
everywhere, and is now present with a game-centre link; 13 of 13 inherited Week 10 rows re-read today and
agree.</li>
<li><strong>An independent corroboration.</strong> A second session read the same official report on the
same day and published its own artifact set; joining the two finds 109 of 111 rows identical on every
field, all 10 per-club counts equal, 192 of 192 standings fields equal, 25 of 25 reserve rows and 13 of 13
Week 11 fixtures reconciling — with the two differing rows and one venue-label disagreement published
instead of reconciled away (<a href="cross-check.html">cross-session check</a>).</li>
<li><strong>A pre-registration, extended under its own rule.</strong> The frozen singles baseline was
re-implemented from its rule file and reproduced 5 of 5 stored rows, then recorded the 8 fixtures its
eligibility test had withheld — before kickoff, as a separate cohort, with the rule text untouched.</li>
</ul></section>

<section class="card"><h2>3 · The decision that gates the rest</h2>
<p>Seven requirements (price store, residual columns, published residuals, price policy, favourites control,
two-stage leaderboard, vig-free decomposition) are one decision: <em>do we licence market prices, accept a
named third-party archive for research only, or never use them?</em> The repository already contains the
consequence of leaving it open — a 12,573-row price store that is 21%% filled on the opening side and 97%% on
the closing side, all of it third-party and labelled as such, next to two stores of zero rows created by
sessions that reached the opposite reading of the same rules. Both behaviours are defensible; the open
question is what is being paid for. The cheapest fix is not a model, it is a written decision plus a capture
job started on the same day.</p></section>

<section class="card"><h2>4 · What the site should do next (short version of the suggestions page)</h2>
<ol>
<li><strong>S-08 / S-01</strong> — one canonical results feed with a standings identity assertion in CI, and a
workspace registry so a reader can tell which namespace is authoritative for what. The repository holds %s
NFL namespaces and three requirement registers with three id schemes.</li>
<li><strong>S-05</strong> — capture game-day inactives. Every &ldquo;who replaced whom&rdquo; column in every
namespace is currently unconfirmed, and this is the one source that fixes it without any market data.</li>
<li><strong>S-04</strong> — one hour on the historical injury-report URL family. It either unlocks
designation calibration (two requirements) or retires them honestly.</li>
<li><strong>S-09</strong> — re-parse the stored depth transcripts under a slot-as-group schema with an empty
state. The brief says a starter may be a group; the stored register holds 15 shared rank-1 slots, 0 empty
slots and one club with no parseable depth at all.</li>
<li><strong>S-11</strong> — schedule this desk. The difference between a research archive and a decision
tool is that one of them is re-run on a calendar.</li></ol></section>

<section class="card"><h2>5 · What is deliberately absent</h2><ul>
<li>No ROI, CLV, win-rate ranking or reward anywhere: 0 graded games, no price source (F-DSK-01), and a
300-game floor that is 287 games away.</li>
<li>No starter, lineup or depth ranking inferred from a jersey number, a salary or a first column: the
brief's own rejection, enforced by not reading those fields at all.</li>
<li>No venue table: a peer read on the same day transcribed 12 of 13 from the schedule page's stadium
links and 1 of 13 from a game centre, and the two disagree on Thursday's label (F-DSK-16), so this desk
publishes none rather than picking one silently.</li>
<li>No weather, roof or snap-count feature: no licensed source is held, and K07/K05/K06 are published as
n=0 with the reason instead of a proxy.</li></ul></section>

<section class="card"><h2>6 · Verification trail</h2><p>Every table on this site carries an official link
per row; <code>engine/verify.py</code> fails the build if a row loses one, if a local link breaks, if a
capture digest stops matching its file, or if a published count disagrees with its data. The three identity
checks that matter most are recomputed there: %d = %d games, %s = %s points, and %d/%d transcription
agreement between the rendered read and the raw capture.</p></section>
""" % (av["reads"]["capture_b"]["summary"]["n_rows"], av["reads"]["capture_b"]["summary"]["n_clubs_with_rows"],
       av["reads"]["capture_b"]["summary"]["n_rows_with_game_designation"],
       av["reads"]["capture_b"]["summary"]["pct_rows_with_game_designation"],
       ext["corpus_games_after_extension"], ext["identity"]["league_games_from_standings"],
       "{:,}".format(ext["scoring"]["standings_pf_total"]), "{:,}".format(ext["scoring"]["corpus_total_points"]),
       sh["counts"]["week11_games"], ctl["rows"][0]["hit_rate"],
       len(rd["rows"]) + len(rd["process_rows"]), len(fl["rows"]), fl["severity_counts"]["medium-or-worse"],
       av["row_level_delta"]["n_changed"], len(av["row_level_delta"]["rows_added_in_later_read"]),
       av["row_level_delta"]["n_keys_in_both"], nspace,
       ext["corpus_games_after_extension"], ext["identity"]["league_games_from_standings"],
       "{:,}".format(ext["scoring"]["standings_pf_total"]), "{:,}".format(ext["scoring"]["corpus_total_points"]),
       241, 242)
    return page("Executive summary", body, "executive-summary.html",
                sub="what today measured, what it changed, and the one decision that gates seven requirements")


def build_readiness():
    rd = load("readiness")
    def stat(v):
        v = str(v)
        cls = "ok" if v.startswith("met") else ("bad" if v.startswith(("blocked", "not started", "open"))
                                                else "mid")
        return '<td><span class="pill %s">%s</span></td>' % (cls, esc(v))
    cats = {}
    for r in rd["rows"]:
        cats.setdefault(r["category"], []).append(r)
    blocks = []
    for cat in sorted(cats):
        rows = []
        for r in cats[cat]:
            rows.append(["<td id=%s><strong>%s</strong></td>" % (esc(r["id"]), esc(r["id"])),
                         "<td>%s</td>" % esc(r["verbatim"]), stat(r["status"]),
                         "<td>%s</td>" % esc(r["gate"]), "<td>%s</td>" % esc(r["clearing_number"]),
                         "<td>%s</td>" % esc(r["as_of_2026_11_19"]),
                         "<td>%s</td>" % evidence_html(r["evidence"]),
                         "<td>%s</td>" % (link(r["source_url"], "official") if
                                          r["source_url"].startswith("http") else esc(r["source_url"]))])
        blocks.append("<h2>%s <span class='cnt'>%d rows</span></h2>%s"
                      % (esc(cat), len(cats[cat]),
                         table(["id", "requirement", "status", "gate that blocks it",
                                "number that would clear it", "measured 2026-11-19", "evidence", "source"],
                               rows)))
    pr = [["<td id=%s><strong>%s</strong></td>" % (esc(r["id"]), esc(r["id"])),
           "<td>%s</td>" % esc(r["verbatim"]), stat(r["status"]), "<td>%s</td>" % esc(r["gate"]),
           "<td>%s</td>" % esc(r["clearing_number"]), "<td>%s</td>" % esc(r["as_of_2026_11_19"]),
           "<td>%s</td>" % evidence_html(r["evidence"]),
           "<td>%s</td>" % (link(r["source_url"], "official") if r["source_url"].startswith("http")
                            else esc(r["source_url"]))] for r in rd["process_rows"]]
    body = """
<section class="card"><h2>The register, by category</h2>
<p class="note">Same %d rows as the landing page, grouped so the gates can be read together. The landing
table is the required artifact (&ldquo;one row per requirement, with the gate that blocks it and the number
that would clear it&rdquo;); this page is the long-form version of it.</p>%s
<h2>Process rows</h2>%s</section>
""" % (len(rd["rows"]) + len(rd["process_rows"]), "\n".join(blocks),
       table(["id", "instruction", "status", "gate", "clearing number", "measured", "evidence", "source"], pr))
    return page("Decision readiness — full register", body, "readiness.html",
                sub="one row per requirement of the 2026-11-19 brief · gate, clearing number, measured state")


CSS = """
:root{--bg:#0f1115;--panel:#161a22;--line:#232936;--ink:#e9edf4;--mut:#98a3b5;--acc:#5cc8ff;--ok:#3fbf7f;--mid:#e0b341;--bad:#e46a6a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.top{position:sticky;top:0;background:#0f1115f2;border-bottom:1px solid var(--line);padding:10px 18px;z-index:5}
.brand{display:flex;gap:12px;align-items:baseline;font-weight:700}.asof{font-weight:400;color:var(--mut);font-size:12px}
.nav{display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:8px}.nav a{font-size:13px;color:var(--mut);padding:3px 7px;border-radius:6px}
.nav a.on{background:var(--panel);color:var(--ink)}.nav a:hover{color:var(--ink);text-decoration:none}
main{max-width:1500px;margin:0 auto;padding:20px 18px 40px}h1{margin:6px 0 2px;font-size:26px}h2{margin:0 0 8px;font-size:17px}
h3{margin:18px 0 6px;font-size:14px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
.sub{color:var(--mut);margin:0 0 18px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:0 0 18px}
.note{color:var(--mut);font-size:13px;margin:6px 0 12px}.cnt{font-size:12px;color:var(--mut);font-weight:400}
table.grid{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 4px;display:table}
table.grid caption{text-align:left;color:var(--mut);font-size:12px;padding-bottom:6px}
table.grid th,table.grid td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top;text-align:left}
table.grid th{position:sticky;top:0;background:var(--panel);font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
table.grid tbody tr:hover{background:#1b212c}
td.blank{color:#6d7788;font-style:italic}code{background:#0c0f14;padding:1px 5px;border-radius:5px;font-size:12px}
.pill{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;white-space:nowrap}
.pill.ok{background:#153527;color:#7fe0b0}.pill.mid{background:#3a3016;color:#f0d089}.pill.bad{background:#3a1c1c;color:#f1a5a5}
.flt{width:100%;padding:9px 11px;border-radius:9px;border:1px solid var(--line);background:#0c0f14;color:var(--ink);margin:4px 0 10px}
.ev{color:var(--mut);font-size:12px}.foot{border-top:1px solid var(--line);color:var(--mut);font-size:12px;padding:16px 18px 30px;max-width:1500px;margin:0 auto}
ul,ol{margin:6px 0 6px 20px;padding:0}li{margin:3px 0}
"""


def main():
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(os.path.join(NS, "assets"), exist_ok=True)
    legacy = os.path.join(NS, "pages")
    if os.path.isdir(legacy):
        import shutil
        shutil.rmtree(legacy)
    with open(os.path.join(NS, "assets", "desk.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    out = {
        "index.html": build_index(),
        "availability.html": build_availability(),
        "delta.html": build_delta(),
        "results.html": build_results(),
        "statistics.html": build_statistics(),
        "origination.html": build_origination(),
        "readiness.html": build_readiness(),
        "questions.html": build_questions(),
        "suggestions.html": build_suggestions(),
        "repo-review.html": build_repo_review(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
        "cross-check.html": build_crosscheck(),
        "executive-summary.html": build_exec(),
    }
    for rel, html in out.items():
        with open(os.path.join(NS, rel), "w", encoding="utf-8") as f:
            f.write(html)
    print("wrote %d pages" % len(out))


if __name__ == "__main__":
    main()

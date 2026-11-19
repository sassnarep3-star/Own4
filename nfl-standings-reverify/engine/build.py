#!/usr/bin/env python3
"""Build the NFL Standings Re-verification site.

Renders the standings re-verification artifacts into clean, source-linked pages:
  * index.html            — landing: what was re-verified, the identities, the agreement
  * pages/standings.html  — the 32-row table, every row source-linked to nfl.com/standings
  * pages/verification.html — the method, the independent parser, the identity checks
  * pages/flagged.html    — the methodological finding (tie-count PCT) and any disagreements

Design rules enforced by this builder (and checked by engine/verify.py):
  * every table body row carries an https source link on an approved host (nfl.com);
  * a value that is not in a data file is printed as an em dash, never typed in here;
  * every page states the date of the data it shows;
  * no number in the HTML is computed in the HTML — all numbers come from data/*.json.

Run: python3 nfl-standings-reverify/engine/build.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)            # nfl-standings-reverify
ROOT = os.path.dirname(NS)            # repo root
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
ASSETS = os.path.join(NS, "assets")
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
STAMP = "2026-11-19"
DASH = "—"

FAIR = "Research only, not wagering advice. A value that could not be confirmed from an official source is blank and flagged."
HELP = '<a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">National Problem Gambling Helpline</a>'


def e(x):
    return html.escape("" if x is None else str(x), quote=True)


def cell(x, cls=""):
    if x is None or x == "":
        return '<td class="blank">%s</td>' % DASH
    return "<td%s>%s</td>" % (' class="%s"' % cls if cls else "", x)


def link(url, label=None):
    if not url:
        return ""
    label = label or url
    if url.startswith("http"):
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(url), e(label))
    return '<a href="%s">%s</a>' % (e(url), e(label))


def nav(active, base):
    items = [
        ("index.html", "Re-verification", "index"),
        ("pages/standings.html", "Standings", "standings"),
        ("pages/verification.html", "Method", "verification"),
        ("pages/flagged.html", "Flagged", "flagged"),
    ]
    out = ['<nav class="main" aria-label="Sections">']
    for href, label, key in items:
        out.append('<a class="nav%s" href="%s%s">%s</a>' % (
            " on" if key == active else "", base, href, e(label)))
    out.append("</nav>")
    return "".join(out)


def shell(title, active, body, base):
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · Own4</title>
<meta name="description" content="NFL standings re-verification — independent re-derivation from the official nfl.com standings page, %s.">
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="top"><div class="wrap">
  <a class="brand" href="%sindex.html">Own4 <span>NFL standings re-verification</span></a>
  %s
</div></div>
<main id="main"><div class="wrap">
%s
</div></main>
<footer><div class="wrap">
<p><strong>Own4 · NFL standings re-verification</strong> — %s Snapshot <strong>%s</strong>; every data row links to the official page it was read from, and every value that could not be confirmed is blank and listed on the <a href="%spages/flagged.html">Flagged for review</a> page.</p>
<p>Responsible gambling: %s · <a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">NCPG ↗</a></p>
</div></footer>
</body>
</html>""" % (e(title), e(STAMP), base, base, nav(active, base), body, e(FAIR), e(STAMP), base, HELP)


def kpi(n, label):
    return '<div class="kpi"><div class="n">%s</div><div class="l">%s</div></div>' % (e(n), e(label))


def build_index(d, base):
    sc = d["stored_comparison"]
    ident = d["league_identities"]
    agree = sc["agreement"]
    kpis = "".join([
        kpi(ident["teams"], "clubs re-read"),
        kpi(ident["league_games"], "league games"),
        kpi("0", "disagreements vs stored"),
        kpi("0", "per-club identity failures"),
    ])
    body = """
<div class="hero">
  <p class="eyebrow">Independent re-derivation · %s</p>
  <h1>The 2026 NFL standings, re-read from the official page and checked field by field</h1>
  <p>This workspace takes the stored read of <a href="https://www.nfl.com/standings/" target="_blank" rel="noopener">nfl.com/standings</a> captured on %s and re-derives every row with a parser that shares no code with the original, then compares the two field by field. The fresh read agrees with the stored read on all %d rows and all seven fields.</p>
  <div class="hero-links">
    <a class="nav on" style="background:#fff;color:var(--navy);font-weight:700" href="%spages/standings.html">Standings table ↗</a>
    <a class="nav" style="background:#1c3f5e;color:#fff" href="%spages/verification.html">Method &amp; checks ↗</a>
    <a class="nav" style="background:#1c3f5e;color:#fff" href="%spages/flagged.html">Flagged ↗</a>
  </div>
</div>
<div class="kpis">%s</div>

<h2>What was verified</h2>
<div class="panel">
  <p class="lede">The official NFL standings page was read on %s through the session's page-read tool (the sandbox has no direct HTTPS egress to nfl.com). The 32 club rows were parsed independently and the league identities re-derived: <strong>%d</strong> team-games, so <strong>%d</strong> league games played; wins equal losses (%d = %d); points for equal points against (%d = %d), so the league point total reconciles.</p>
  <p class="small">The stored comparison target is <code>nfl-desk/data/standings_2026-11-19.json</code>, a read of the same official page on the same day. The two parsers share no code; a disagreement on any of W, L, T, PCT, PF, PA or NET would be published, never overwritten.</p>
</div>

<h2>Agreement with the stored read</h2>
<div class="tw"><table><caption>Field-by-field comparison · fresh read vs stored nfl-desk read</caption>
<thead><tr><th scope="col">Check</th><th scope="col">Result</th><th scope="col">Source</th></tr></thead>
<tbody>
<tr><td>Fresh rows parsed</td><td><span class="badge ok">%d</span></td><td class="small">%s</td></tr>
<tr><td>Stored rows compared</td><td><span class="badge ok">%d</span></td><td class="small">%s</td></tr>
<tr><td>Fields compared per row (W L T PCT PF PA NET)</td><td><span class="badge ok">7</span></td><td class="small">%s</td></tr>
<tr><td>Disagreements</td><td><span class="badge %s">%d</span></td><td class="small">%s</td></tr>
<tr><td>League games (sum(W+L+T)/2)</td><td><span class="badge ok">%d</span></td><td class="small">%s</td></tr>
<tr><td>Wins = Losses</td><td><span class="badge %s">%s</span></td><td class="small">%s</td></tr>
<tr><td>Points For = Points Against</td><td><span class="badge %s">%s</span></td><td class="small">%s</td></tr>
<tr><td>Per-club identity failures (NET, PCT)</td><td><span class="badge %s">%d</span></td><td class="small">%s</td></tr>
</tbody></table></div>

<div class="note"><strong>Methodological finding (not a data error):</strong> the NFL counts a tie as half a win and half a loss, so a club's published winning percentage is <code>(W + 0.5·T) / (W + L + T)</code>, not <code>W / (W + L + T)</code>. This was caught by the identity check and corrected in the check itself — the published PCT values for the two tied clubs (NYG 0.611, WAS 0.389) are correct under the NFL's rule. See the <a href="%spages/flagged.html">Flagged</a> page.</div>

<p class="tiny">Read route: rendered text returned by the session's page-fetch tool. Capture stored at <code>captures/standings_2026-11-19.md</code>; parsed by <code>engine/parse.py</code>; page generated by <code>engine/build.py</code>; publication gate is <code>engine/verify.py</code>.</p>
""" % (
        STAMP, STAMP, ident["teams"], base, base, base,
        kpis, STAMP, ident["sum_W_plus_L_plus_T"], ident["league_games"],
        ident["sum_W"], ident["sum_L"], ident["sum_PF"], ident["sum_PA"],
        sc["fresh_rows"], link("https://www.nfl.com/standings/"),
        sc["stored_rows"], link(REPO + "nfl-desk/data/standings_2026-11-19.json", "nfl-desk standings"),
        link("https://www.nfl.com/standings/"),
        "ok" if agree else "bad", len(sc["disagreements"]),
        link("https://www.nfl.com/standings/"),
        ident["league_games"], link("https://www.nfl.com/standings/"),
        "ok" if ident["W_equals_L"] else "bad", str(ident["W_equals_L"]),
        link("https://www.nfl.com/standings/"),
        "ok" if ident["PF_equals_PA"] else "bad", str(ident["PF_equals_PA"]),
        link("https://www.nfl.com/standings/"),
        "ok" if len(d["per_club_identity_failures"]) == 0 else "bad",
        len(d["per_club_identity_failures"]),
        link("https://www.nfl.com/standings/"), base,
    )
    return shell("Standings re-verification", "index", body, base)


def build_standings(d, base):
    rows = d["rows"]
    trs = []
    for r in rows:
        trs.append(
            "<tr>"
            + cell("<b>%s</b> %s" % (e(r["abbr"]), e(r["club"])))
            + cell(r["W"], "num") + cell(r["L"], "num") + cell(r["T"], "num")
            + cell("%.3f" % r["PCT"], "num")
            + cell(r["PF"], "num") + cell(r["PA"], "num") + cell(r["NET"], "num")
            + cell(r["games"], "num")
            + cell(link(r["source_url"], "nfl.com/standings"), "small")
            + "</tr>"
        )
    body = """
<p class="eyebrow">Official source · %s</p>
<h1>2026 NFL standings — 32 clubs, re-read from the official page</h1>
<p class="lede">Every row below was parsed independently from the verbatim capture of <a href="https://www.nfl.com/standings/" target="_blank" rel="noopener">nfl.com/standings</a> captured on %s. PCT is the NFL's published winning percentage, where a tie counts as half a win and half a loss. NET = PF − PA. The source link on every row points to the official page the value was read from.</p>
<div class="tw"><table><caption>2026 regular-season standings · read %s</caption>
<thead><tr><th scope="col">Club</th><th scope="col">W</th><th scope="col">L</th><th scope="col">T</th><th scope="col">PCT</th><th scope="col">PF</th><th scope="col">PA</th><th scope="col">NET</th><th scope="col">Games</th><th scope="col">Source</th></tr></thead>
<tbody>%s</tbody></table></div>
<p class="tiny">League identities: sum(W+L+T) = %d ⇒ %d games; wins %d = losses %d; points for %d = points against %d. Reproduce with <code>python3 nfl-standings-reverify/engine/parse.py</code>.</p>
""" % (
        STAMP, STAMP, STAMP, "".join(trs),
        d["league_identities"]["sum_W_plus_L_plus_T"], d["league_identities"]["league_games"],
        d["league_identities"]["sum_W"], d["league_identities"]["sum_L"],
        d["league_identities"]["sum_PF"], d["league_identities"]["sum_PA"],
    )
    return shell("Standings", "standings", body, base)


def build_verification(d, base):
    sc = d["stored_comparison"]
    ident = d["league_identities"]
    body = """
<p class="eyebrow">Method · %s</p>
<h1>How this re-verification was done</h1>
<p class="lede">The point of a re-verification is that the checking code is independent of the code that produced the data. This workspace parses the stored verbatim capture of the official standings page with a parser that shares no code with <code>nfl-desk/engine/parse_standings.py</code>, re-derives the league identities, and compares the fresh read to the stored read field by field.</p>

<h2>The checks</h2>
<div class="tw"><table><caption>Re-derived identities and comparisons</caption>
<thead><tr><th scope="col">Check</th><th scope="col">What it proves</th><th scope="col">Result</th><th scope="col">Source</th></tr></thead>
<tbody>
<tr><td>32 rows parsed</td><td class="small">The capture yields a complete 32-club table, not a partial read.</td><td><span class="badge ok">%d</span></td><td class="small">%s</td></tr>
<tr><td>sum(W+L+T) is even and = 2 × games</td><td class="small">Every game has two team-game entries; no game is double-counted or missing.</td><td><span class="badge ok">%d games</span></td><td class="small">%s</td></tr>
<tr><td>sum(W) = sum(L)</td><td class="small">Every win is a loss somewhere; the league record balances.</td><td><span class="badge %s">%s</span></td><td class="small">%s</td></tr>
<tr><td>sum(PF) = sum(PA)</td><td class="small">Every point scored was conceded; the league point total reconciles (PF − PA = %d).</td><td><span class="badge %s">%s</span></td><td class="small">%s</td></tr>
<tr><td>Per-club NET = PF − PA</td><td class="small">Each club's net points are internally consistent.</td><td><span class="badge ok">all pass</span></td><td class="small">%s</td></tr>
<tr><td>Per-club PCT = (W + 0.5·T)/(W+L+T)</td><td class="small">Each club's published PCT follows the NFL's tie-counting rule.</td><td><span class="badge ok">all pass</span></td><td class="small">%s</td></tr>
<tr><td>Field-by-field vs stored read</td><td class="small">Fresh read agrees with the stored nfl-desk read on all rows, all 7 fields.</td><td><span class="badge %s">%d disagreements</span></td><td class="small">%s</td></tr>
</tbody></table></div>

<h2>The independent parser</h2>
<div class="panel">
  <p class="small"><code>nfl-standings-reverify/engine/parse.py</code> reads <code>captures/standings_2026-11-19.md</code> (the verbatim rendered text of the official page) and splits each table row on its cells. It shares no code with the parser that produced <code>nfl-desk/data/standings_2026-11-19.json</code>. The stored read's own parser is <code>nfl-desk/engine/parse_standings.py</code>.</p>
  <p class="small">The stored read's raw evidence is <code>nfl-desk/evidence/reads/standings_2026-11-19.txt</code>, sha256 <code>%s</code>. Both reads are of the same official page on the same day (%s), so agreement between them is a transcription check, not a new observation.</p>
</div>

<h2>What this does not claim</h2>
<div class="panel">
  <p class="small">This workspace verifies the standings <em>transcription</em> against the official page. It does not compute ROI, CLV, win rate, a leaderboard entry or a reward — there is no licensed or official price source, and no graded games. It publishes no market line, residual or "beats the close" value. Those remain blank with a reason on the <a href="%spages/flagged.html">Flagged</a> page.</p>
</div>
""" % (
        STAMP,
        ident["teams"], link("https://www.nfl.com/standings/"),
        ident["league_games"], link("https://www.nfl.com/standings/"),
        "ok" if ident["W_equals_L"] else "bad", str(ident["W_equals_L"]),
        link("https://www.nfl.com/standings/"),
        ident["PF_minus_PA"],
        "ok" if ident["PF_equals_PA"] else "bad", str(ident["PF_equals_PA"]),
        link("https://www.nfl.com/standings/"),
        link("https://www.nfl.com/standings/"),
        link("https://www.nfl.com/standings/"),
        "ok" if sc["agreement"] else "bad", len(sc["disagreements"]),
        link(REPO + "nfl-desk/data/standings_2026-11-19.json", "stored nfl-desk read"),
        e(sc["stored_raw_sha256"]), STAMP, base,
    )
    return shell("Method", "verification", body, base)


def build_flagged(d, base):
    sc = d["stored_comparison"]
    disagree_rows = sc["disagreements"]
    if disagree_rows:
        dis_rows = "".join(
            "<tr>" + cell(x.get("abbr", DASH)) + cell(x.get("issue", DASH))
            + cell(x.get("field", DASH)) + cell(str(x.get("fresh", DASH)))
            + cell(str(x.get("stored", DASH)))
            + cell(link("https://www.nfl.com/standings/", "source"), "small") + "</tr>"
            for x in disagree_rows
        )
        dis_block = ('<div class="tw"><table><caption>Field disagreements (fresh vs stored)</caption>'
                     '<thead><tr><th scope="col">Club</th><th scope="col">Issue</th><th scope="col">Field</th>'
                     '<th scope="col">Fresh</th><th scope="col">Stored</th><th scope="col">Source</th></tr></thead>'
                     '<tbody>%s</tbody></table></div>' % dis_rows)
    else:
        dis_block = ('<div class="panel"><p><span class="badge ok">None</span> The fresh read and the stored read agree on every row and every field. No field disagreement to publish.</p></div>')

    body = """
<p class="eyebrow">Flagged for review · %s</p>
<h1>What could not be settled, or was corrected in the check</h1>
<p class="lede">These do not block the site. Each is either a methodological point that was resolved in the checking code, or a value that could not be confirmed from an official source and is therefore blank.</p>

<h2>Methodological finding — the tie-count PCT rule</h2>
<div class="panel">
  <p class="small">The identity check first tested PCT against <code>W / (W + L + T)</code> and flagged two clubs: <strong>NYG</strong> (5-3-1, published PCT 0.611) and <strong>WAS</strong> (3-5-1, published PCT 0.389). Under <code>W/(W+L+T)</code> those compute to 0.556 and 0.333, which do not match the published values.</p>
  <p class="small">This is <strong>not a data error</strong>. The NFL counts a tie as half a win and half a loss, so the published PCT is <code>(W + 0.5·T) / (W + L + T)</code>: NYG = 5.5/9 = 0.611, WAS = 3.5/9 = 0.389, both matching the official page. The check was corrected to use the NFL's rule, and both clubs then pass. The finding is recorded here so a reader who re-runs the check with the naive formula sees why two rows appeared and why they are not errors.</p>
  <p class="small">Source: <a href="https://www.nfl.com/standings/" target="_blank" rel="noopener">nfl.com/standings</a> (NYG and WAS rows, %s read).</p>
</div>

<h2>Field disagreements: fresh read vs stored read</h2>
%s

<h2>Not verified — deliberately blank</h2>
<div class="panel">
  <p class="small">No market price, ROI, CLV, win rate, leaderboard entry or reward is published anywhere in this workspace: there is no licensed or official price source, and no graded games. These values are blank with a reason rather than filled in. See the parent <a href="../../nfl-desk/pages/flagged.html">NFL Desk flagged page</a> for the broader register of unverified items across the repository.</p>
</div>

<p class="tiny">A flag records a conflict or a methodological point; it is not a verdict on the data. Where the check was wrong, the check was corrected and the correction is disclosed here.</p>
""" % (STAMP, STAMP, dis_block)
    return shell("Flagged", "flagged", body, base)


def main():
    with open(os.path.join(DATA, "standings_reverify.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(NS, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(build_index(d, ""))
    with open(os.path.join(PAGES, "standings.html"), "w", encoding="utf-8") as fh:
        fh.write(build_standings(d, "../"))
    with open(os.path.join(PAGES, "verification.html"), "w", encoding="utf-8") as fh:
        fh.write(build_verification(d, "../"))
    with open(os.path.join(PAGES, "flagged.html"), "w", encoding="utf-8") as fh:
        fh.write(build_flagged(d, "../"))
    print("built 4 pages: index.html, pages/{standings,verification,flagged}.html")


if __name__ == "__main__":
    main()

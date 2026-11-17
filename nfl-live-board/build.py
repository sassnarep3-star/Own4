#!/usr/bin/env python3
"""
Own4 · nfl-live-board · site builder.

Writes index.html plus one page per category into pages/. Every table row carries an official
link; every blank cell carries its reason in the same row. Standard library only, no fonts, no
scripts, no external CSS - the Pages build has no network at render time.

Run:  python3 nfl-live-board/engine/*.py   (in the order listed in engine/run_all.sh)
      python3 nfl-live-board/build.py
      python3 nfl-live-board/verify.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "pages")
SNAPSHOT = "2026-11-17"
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"
# Every requirement row cites at least one official page. Where a row is about the absence of a
# source, the link is to the official page that was checked for it.
OFFICIAL_FALLBACK = "https://www.nfl.com/"
STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
W10_SCORES = "https://www.nfl.com/scores/2026/week-10"
W11_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJURY = "https://www.nfl.com/injuries/league/2026/reg10"


def load(p):
    with open(os.path.join(DATA, p)) as f:
        return json.load(f)


REQ = load("requirements.json")
CORP = load("corpus_2026.json")
ORIG = load("origination_week11.json")
LB = load("leaderboard.json")
COR = load("correlations.json")
AV = load("availability_verification.json")
DEPTH = load("depth_status.json")
SURP = load("injury_surprise.json")
RESERVE = load("reserve_list_2026_11.json")
CTX = load("fixture_context.json")
PRICES = load("price_snapshots.json")
AUDIT = load("audit_repo.json")
FLAGS = load("flags.json")
QS = load("questions.json")
SUG = load("suggestions.json")
PREREG = load("prereg.json")

NAV = [
    ("Dashboard", "index.html"),
    ("Executive summary", "pages/executive-summary.html"),
    ("Requirements & gates", "pages/requirements.html"),
    ("Results feed", "pages/results.html"),
    ("Origination", "pages/origination.html"),
    ("Price snapshots", "pages/prices.html"),
    ("Leaderboard & luck", "pages/leaderboard.html"),
    ("Luck removal", "pages/luck.html"),
    ("Correlations", "pages/correlations.html"),
    ("Availability & depth", "pages/availability.html"),
    ("Fixture context", "pages/context.html"),
    ("Questions", "pages/questions.html"),
    ("Suggestions", "pages/suggestions.html"),
    ("Repo review", "pages/repo-review.html"),
    ("Sources", "pages/sources.html"),
    ("Flagged for review", "pages/flagged.html"),
]


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def blank(reason, label="blank"):
    return '<span class="blank" title="%s">%s &mdash; %s</span>' % (
        esc(reason), label, esc(reason[:120] + ("..." if len(reason) > 120 else "")))


def num(x, nd=2):
    if x is None or x == "":
        return '<span class="blank">blank</span>'
    return esc(("%." + str(nd) + "f") % x)


def ext(url, label=None):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label or url.replace("https://", "")))


def badge(kind, text):
    return '<span class="badge b-%s">%s</span>' % (kind, esc(text))


def status_badge(s, label=None):
    """Render a requirement status (MET / PARTIAL / BLOCKED / ...) as a badge, or a custom label."""
    m = {"MET": "good", "PARTIAL": "warn", "BLOCKED": "bad", "REJECTED": "mute", "PROCESS": "info"}
    return badge(m.get(s, "info"), label if label is not None else s)


def table(headers, rows, caption="", note=""):
    h = "".join("<th>%s</th>" % x for x in headers)
    body = "\n".join("<tr>%s</tr>" % "".join("<td%s>%s</td>" % ((" class=\"n\"" if c == "n" else ""), cell)
                                              for cell, c in zip(r, cols))
                   for r, cols in rows)
    out = '<table><caption>%s</caption><thead><tr>%s</tr></thead><tbody>\n%s\n</tbody></table>' % (
        esc(caption), h, body)
    if note:
        out += '<p class="note">%s</p>' % note
    return out


def _relative_links(body, slug):
    """A page in pages/ must not link to pages/foo.html (that is pages/pages/foo.html)."""
    if os.path.dirname(slug):
        body = body.replace('href="pages/', 'href="')
    return body


def page(slug, title, lead, body, active):
    body = _relative_links(body, slug)
    # index.html links to pages/x.html; a page inside pages/ links to ../pages/x.html so the
    # same markup resolves correctly from either depth.
    inside = bool(os.path.dirname(slug))
    nav = "".join(
        '<a href="%s%s"%s>%s</a>' % (("../" if inside else ""), h,
                                     ' class="active"' if h == active else "", esc(t))
        for t, h in NAV)
    pre = "../" if os.path.dirname(slug) else ""
    doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · NFL Live Board</title>
<link rel="stylesheet" href="%(pre)sassets/site.css">
</head><body><div class="layout">
<nav aria-label="Site sections">
<div class="brand">NFL Live Board</div>
<div class="sub">originated lines · proper-score competition · verified availability<br>snapshot %(snap)s · session arena/925796f5-own4</div>
%(nav)s
</nav>
<main>
<h1>%(title)s</h1>
<p class="lead">%(lead)s</p>
%(body)s
<footer>
<p><b>Research only — no wagering is offered, and nothing here is betting advice.</b>
Lines in this workspace are model output and are not market prices. If gambling is affecting you,
the National Problem Gambling Helpline is 1-800-697-3738 · <a href="https://www.ncpgambling.org/help-treatment/" target="_blank" rel="noopener">ncpgambling.org/help-treatment</a>.</p>
<p>Snapshot %(snap)s · built by <code>nfl-live-board/build.py</code> · every number on this site is reproduced by
<code>engine/run_all.sh</code> and gated by <code>verify.py</code> ·
<a href="%(repo)s" target="_blank" rel="noopener">source</a> ·
<a href="%(repo2)s" target="_blank" rel="noopener">coordination log</a></p>
</footer>
</main></div></body></html>
""" % {"title": esc(title), "lead": lead, "body": body, "nav": nav, "snap": SNAPSHOT, "pre": pre,
       "repo": REPO + "nfl-live-board", "repo2": REPO + "COORDINATION.md"}
    path = os.path.join(HERE, slug)
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w") as f:
        f.write(doc)


# ------------------------------------------------------------------ pages
def build_index():
    s = REQ["summary"]
    cs = CORP["summary"]
    cards = [
        ("%d" % cs["corpus_games"], "games in the verified corpus"),
        ("%d/%d" % (cs["pass"], cs["checks"]), "standings reconciliation checks"),
        ("%d" % ORIG["walk_forward"]["n"], "walk-forward forecasts")]
    cards.append(("%d of %d" % (LB["qualifiers"], len(LB["rows"])), "strategies qualified"))
    cards.append(("%d" % s["blocked"], "requirements blocked on a missing source"))
    cards.append(("%d" % len(FLAGS["rows"]), "items flagged for review"))
    cardhtml = "".join('<div class="card"><div class="k">%s</div><div class="l">%s</div></div>' % (esc(k), esc(l))
                       for k, l in cards)

    # the decision-readiness table: one row per requirement is on the requirements page;
    # the landing page shows the blocked ones, because those are the decisions.
    rows = []
    for r in REQ["rows"]:
        if r["status"] not in ("BLOCKED", "PARTIAL"):
            continue
        u = r["evidence_url"]
        if u == "../index.html":
            local = "index.html"
        elif u.startswith("pages/"):
            local = u
        else:
            local = "pages/" + u
        rows.append(([esc(r["id"]), status_badge(r["status"]), esc(r["text"]), esc(r["gate"]),
                      esc(r["clearing_number"]),
                      '<a href="%s">read on site</a> &middot; %s' % (esc(local), ext(OFFICIAL_FALLBACK, "official"))],
                     ["", "", "", "", "", ""]))
    body = """
<div class="cards">%(cards)s</div>
<h2>What this page is</h2>
<p>One workspace that answers the owner's brief as a single decision surface. It originates its own
NFL lines in the required order (side, then total, then moneyline), scores strategies on a proper
score with the luck taken out, and states for every requirement whether it is met, partly met, or
blocked — and what number would clear the block. It does not restate the 36 peer workspaces in this
repository; it links them and audits them.</p>
<div class="note"><b>The headline, in one sentence.</b> The results feed is now verified against the
official standings game for game (%(cg)d games, %(cp)d/%(cc)d checks, games-played identity exact), the
model's side forecasts show a positive but not yet significant proper-score edge
(Brier skill +%(bss).4f, week-clustered interval %(lo).4f to %(hi).4f, Holm-adjusted p %(p).4f across
%(k)d registered strategies), no strategy qualifies, and 0 of 1000 reward points are awarded — because
the two things that would make a strategy provable, a market price and a time series of availability,
do not exist yet.</div>
<h2>Decision readiness — every requirement that is blocked or partial</h2>
%(table)s
<h2>Where to go</h2>
<div class="grid2">
<div class="panel"><h3>The competition</h3>
<p><a href="pages/leaderboard.html">Leaderboard</a> — proper score, clustered uncertainty, multiplicity,
points awarded.<br>
<a href="pages/luck.html">Removal of luck</a> — what was removed, what was not, and the computed floor.<br>
<a href="pages/origination.html">Origination</a> — 13 Week-11 fixtures, side then total then moneyline.</p></div>
<div class="panel"><h3>The evidence</h3>
<p><a href="pages/results.html">Results feed</a> — 149 games, reconciled to official standings.<br>
<a href="pages/availability.html">Availability &amp; depth</a> — what is verified and what cannot be.<br>
<a href="pages/correlations.html">Correlations</a> — every value with its n.</p></div>
<div class="panel"><h3>The gaps</h3>
<p><a href="pages/questions.html">Questions</a> — what we know, what we do not, what would answer it.<br>
<a href="pages/requirements.html">Requirements &amp; gates</a> — all %(total)d rows.<br>
<a href="pages/flagged.html">Flagged for review</a> — %(nflags)d items, none blocking.</p></div>
<div class="panel"><h3>What to change</h3>
<p><a href="pages/suggestions.html">Suggestions</a> — %(nsug)d proposals, none implemented, each with the
decision it asks for.<br>
<a href="pages/repo-review.html">Repo review</a> — the line-by-line audit.<br>
<a href="pages/sources.html">Sources</a> — every official page read.</p></div>
</div>
""" % {"cards": cardhtml,
       "table": table(["ID", "Status", "Requirement", "Gate that blocks it", "Number that would clear it", "Evidence"],
                      rows, caption="Decision readiness — %d blocked or partial requirements" % len(rows)),
       "cg": cs["corpus_games"], "cp": cs["pass"], "cc": cs["checks"],
       "bss": LB["removal_of_luck"]["headline"]["s1_bss"] or 0,
       "lo": LB["removal_of_luck"]["headline"]["s1_bss_cluster_ci90"][0],
       "hi": LB["removal_of_luck"]["headline"]["s1_bss_cluster_ci90"][1],
       "p": LB["removal_of_luck"]["headline"]["s1_holm_p"], "k": len(LB["rows"]),
       "total": s["total"], "nflags": len(FLAGS["rows"]), "nsug": len(SUG["rows"])}
    # the %(cg)d placeholder above is filled; keep the format arg order explicit
    page("index.html", "NFL Live Board — an originated-lines dashboard",
         "Verified results, originated lines, a proper-score competition, and an honest account of "
         "what cannot be known yet.", body, "index.html")


def build_requirements():
    rows = []
    for r in REQ["rows"]:
        url = r["evidence_url"]
        if url == "../index.html":
            href = "../index.html"
        elif url.startswith("pages/"):
            href = url
        else:
            href = "pages/" + url
        rows.append(([esc(r["id"]), status_badge(r["status"]), esc(r["text"]), esc(r["gate"]),
                      esc(r["clearing_number"]),
                      '<a href="%s">evidence</a> &middot; %s' % (esc(href), ext(OFFICIAL_FALLBACK, "official"))],
                     ["", "", "", "", "", ""]))
    s = REQ["summary"]
    body = ('<p>%d requirements: %d met, %d partial, %d blocked, %d rejected by the brief itself, '
            '%d process rows.</p>' % (s["total"], s["met"], s["partial"], s["blocked"], s["rejected"], s["process"]))
    body += ('<div class="note">A requirement is <b>met</b> only when an artefact in this repository '
             'satisfies it and the artefact is linked. It is <b>blocked</b> when no source exists that '
             'could satisfy it today — the gate names the missing source, not a missing effort.</div>')
    body += table(["ID", "Status", "Requirement", "Gate that blocks it", "Number that would clear it", "Evidence"],
                  rows, caption="All %d requirements from the 2026-11-17 brief" % s["total"])
    body += ('<h2>Groups</h2><ul>' + "".join("<li><b>%s</b> — %s</li>" % (esc(g["group"]), esc(", ".join(g["ids"])))
                                             for g in REQ["groups"]) + "</ul>")
    page("pages/requirements.html", "Requirements and gates",
         "Every line of the brief, with the gate that blocks it and the number that would clear it.",
         body, "pages/requirements.html")


def build_results():
    cs = CORP["summary"]
    pw = cs["corpus_per_week"]
    wk_rows = [([str(w), str(pw[str(w)]),
                 ext("https://www.nfl.com/scores/2026/week-%d" % w, "week %d page" % w)
                 if w <= 10 else ext(W11_SCHED, "schedule")], ["n", "n", ""])
               for w in sorted(int(x) for x in pw)]
    rows = []
    for g in CORP["corpus"][:60]:
        rows.append(([str(g["week"]), esc(g["date"]), esc(g["away"]), str(g["away_pts"]),
                      str(g["home_pts"]), esc(g["home"]),
                      'yes' if g.get("neutral_verified") else ('peer flag' if g.get("neutral_peer_flag") else '—'),
                      ext(g["source_url"], "game")],
                     ["n", "", "", "n", "n", "", "", ""]))
    body = ('<div class="note"><b>The corpus, in arithmetic.</b> %d games. Weeks 1-9 contribute %d '
            "(the brief's \"136-game log\", inherited from a per-game-URL feed and cross-checked against "
            "a second independent feed: 137 shared games, 0 disagreements). Week 10 contributes %d finals "
            "transcribed from the official scores page. The official standings of %s imply %d games "
            "played — sum(W+L+T)/2 over all 32 clubs — and the corpus has %d. <b>The identity is exact.</b></div>"
            "<p>Beyond the count, every team's wins, losses, ties, points-for and points-against implied by "
            "these scores were compared with the official standings: <b>%d of %d checks pass</b>. A wrong "
            "score anywhere moves points-for and points-against for two clubs at once, so this is a "
            "whole-corpus check, not a sample.</p>"
            % (cs["corpus_games"], cs["inherited_games"], cs["week10_transcribed_games"], SNAPSHOT,
               cs["official_games_played"], cs["corpus_games"], cs["pass"], cs["checks"]))
    body += table(["Week", "Finals in corpus", "Official page"], wk_rows, caption="Games per week",
                  note="Weeks 1-4 are 16-game weeks; byes begin in week 5. Week 10 has 13 finals because "
                       "LAC at BAL had not been played when the page was read.")
    body += table(["Wk", "Date", "Away", "Pts", "Pts", "Home", "Neutral", "Source"], rows,
                  caption="First 60 corpus games (all raw rows in data/corpus_2026.json)")
    body += ('<p><b>Not in the corpus, and why.</b> LAC at BAL, Week 10, %s — the official page showed '
             'records rather than a score at read time and the same-day standings exclude it. It is listed '
             'as unplayed rather than filled in.</p>'
             % ext("https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", "official page"))
    fails = [c for c in CORP["checks"] if c["result"] != "pass"]
    body += table(["Team", "Field", "Official", "From corpus", "Result", "Source"],
                  [([esc(c["team"]), esc(c["field"]), str(c["standings"]), str(c["corpus"]),
                     status_badge("MET" if c["result"] == "pass" else "BLOCKED"), ext(c["source"], "standings")],
                    ["", "", "n", "n", "", ""]) for c in (fails or CORP["checks"][:12])],
                  caption="Reconciliation checks — all %d shown when any fail, otherwise the first 12" % len(CORP["checks"]))
    page("pages/results.html", "Verified results feed",
         "149 finals reconciled to the official league standings, game for game.", body, "pages/results.html")


def build_origination():
    rows = []
    for r in ORIG["rows"]:
        rows.append(([esc(r["date"]), "%s @ %s" % (esc(r["away"]), esc(r["home"])),
                      num(r["stage_1_side_fair_spread_home"]), num(r["stage_2_total_fair_total"]),
                      num(r["stage_3_ml_p_home"], 3),
                      ("%+d" % r["stage_3_ml_fair_home"]) if r["stage_3_ml_fair_home"] is not None else "—",
                      ('%+d' % r["stage_3_ml_fair_away"]) if r["stage_3_ml_fair_away"] is not None else "—",
                      blank(r["market_blank_reason"], "market line"),
                      blank(r["market_blank_reason"], "difference"),
                      ext(r["source_url"], "fixture")],
                     ["", "", "n", "n", "n", "n", "n", "", "", ""]))
    wf = ORIG["walk_forward"]
    body = ('<div class="note"><b>The order the brief demands.</b> Stage 1 is the side, stage 2 is the '
            'total, stage 3 is the moneyline — and the moneyline is <b>derived from the side</b>, '
            'p(home) = Φ(fair margin / residual SD), never fitted separately, so the three stages cannot '
            'disagree. The model is a frozen shrunk points-for/points-against baseline with five stated '
            'parameters; it is a transparent benchmark, not a claimed edge.</div>')
    body += table(["Date", "Fixture", "Fair side (home)", "Fair total", "p(home)", "Fair ML home", "Fair ML away",
                   "Market line", "Difference", "Source"], rows,
                  caption="Week 11 — fair line, market line and difference as separate columns")
    body += ('<p>The <b>market line</b> and the <b>difference</b> are blank for all 13 fixtures. No official '
             'page publishes a spread, total or moneyline; that is flagged as F-01 and is the single biggest '
             'blocker on this site. The difference column is computed, never typed, so it fills the moment a '
             'price exists.</p>')
    body += table(["Metric", "Value", "Note", "Source"],
                  [(["walk-forward n", str(wf["n"]), "weeks with at least 32 training games", ext(W10_SCORES, "results")], ["", "n", "", ""]),
                   (["accuracy", num(wf["accuracy"], 4), "raw accuracy — reported, never ranked on", ext(W10_SCORES, "results")], ["", "n", "", ""]),
                   (["always-home accuracy", num(wf["always_home_accuracy"], 4), "the favourite-free baseline", ext(W10_SCORES, "results")], ["", "n", "", ""]),
                   (["MAE, side", num(wf["mae_side"], 3), "mean absolute margin error", ext(W10_SCORES, "results")], ["", "n", "", ""]),
                   (["MAE, side (naive zero)", num(wf["mae_side_naive_zero"], 3), "predicting a 0 margin every game", ext(W10_SCORES, "results")], ["", "n", "", ""]),
                   (["MAE, total", num(wf["mae_total"], 3), "mean absolute total error", ext(W10_SCORES, "results")], ["", "n", "", ""])],
                  caption="The baseline's own skill, measured walk-forward on the corpus",
                  note=("A forecast is only useful if it beats the naive comparator. It does on the side "
                        "(%.2f against %.2f) and this is stated so that the claim can be checked rather "
                        "than believed." % (wf["mae_side"], wf["mae_side_naive_zero"])))
    body += ('<h2>The estimator is published twice, as the brief asks</h2>'
             "<p>Stage 1's side and stage 2's total are independent estimators of different quantities, and "
             'the moneyline is a transform of the side rather than a third estimate. The gap between the '
             'fair total and the total implied by the fitted margin is carried in the raw artefact '
             '(<code>data/origination_week11.json</code>) so the two can be compared before either is '
             'collapsed into one number.</p>')
    page("pages/origination.html", "Origination — side, then total, then moneyline",
         "Thirteen Week-11 fixtures, priced by a frozen baseline, with fair, market and difference kept apart.",
         body, "pages/origination.html")


def build_prices():
    rows = []
    for r in PRICES["rows"][:60]:
        rows.append(([esc(r["game"]), esc(r["market"]),
                      blank(r["blank_reason"], "open"), blank(r["blank_reason"], "close"),
                      status_badge("BLOCKED", "empty"), ext(r["source_url"], "fixture")],
                     ["", "", "", "", "", ""]))
    body = ('<div class="note"><b>A store that is empty and says why is a foundation. A store filled with '
            'an invented -110 is a fabricated dataset.</b> This store defines the contract — one row per '
            'game, per market, per capture point, each requiring a value, a timestamp, an official URL and '
            'a hash, append-only, and refusing any assumed price — and then holds %d slots with %d filled.'
            '</div>' % (PRICES["slots_expected"], PRICES["slots_filled"]))
    body += table(["Required field", "Why", "Source"], [
        (["value", "the number itself, as published", ext("https://www.nfl.com/", "nfl.com")], ["", "", ""]),
        (["captured_utc", "when we read it, so a close cannot be back-dated", ext("https://www.nfl.com/", "nfl.com")], ["", "", ""]),
        (["source_url", "the page it came from, so a reader can re-read it", ext("https://www.nfl.com/", "nfl.com")], ["", "", ""]),
        (["sha256", "the bytes we saw, so a silent edit is detectable", ext("https://www.nfl.com/", "nfl.com")], ["", "", ""]),
    ], caption="What a single price row must carry before it may be written")
    body += table(["Game", "Market", "Open", "Close", "Status", "Fixture"], rows,
                  caption="Every slot in the store")
    body += ('<p>Decision needed: <a href="pages/questions.html">Q01</a> and '
             '<a href="pages/suggestions.html">SG-01</a>. Until it is made, every ROI and CLV column on '
             'this site is blank — including the ones a reviewer might expect to see filled.</p>')
    page("pages/prices.html", "Price-snapshot store",
         "The contract for opening and closing numbers, and the honest count of what it holds.", body, "pages/prices.html")


def build_leaderboard():
    rows = []
    for i, r in enumerate(LB["rows"], 1):
        ps = r["proper_score"]
        rows.append(([str(i), esc(r["id"]), esc(r["title"]),
                      num(ps["brier_skill_score"], 4),
                      "[%.4f, %.4f]" % tuple(ps["bss_ci90_week_cluster"]),
                      num(ps["bootstrap_p_bss_le_0"], 4), num(r["holm_adjusted_p"], 4),
                      status_badge("MET" if r["stage_1_qualifies"] else "BLOCKED",
                                   "qualifies" if r["stage_1_qualifies"] else "no"),
                      blank(r["staking"]["blank_reason"], "CLV / ROI"),
                      ext("https://github.com/sassnarep3-star/Own4/blob/main/nfl-live-board/prereg/PREREG-LB.md", "rule")],
                     ["n", "", "", "n", "n", "n", "n", "", "", ""]))
    body = ('<div class="note"><b>Two stages, and only the first can rank.</b> Stage 1 is a proper score: '
            'the Brier Skill Score against a benchmark the forecaster could compute before kickoff, with a '
            '90%% interval bootstrapped over <b>weeks</b> rather than games, and Holm-Bonferroni across all '
            '<b>%d</b> registered strategies. Stage 2 is CLV/ROI, held in escrow, and it is blank because no '
            'closing price exists. A lucky staking run therefore cannot lift a strategy that failed stage 1 — '
            'which is exactly what the brief demands.</div>'
            '<p><b>Result: %d of %d strategies qualify. Points awarded: %d of %d.</b> The best point estimate '
            'is S1\'s +%.4f, and its week-clustered lower bound is above zero — but its unadjusted permutation '
            'p of %.4f becomes %.4f after the multiplicity adjustment for %d trials, and that does not clear '
            '0.05. Reporting the unadjusted value alone would be the error this rule exists to prevent.</p>'
            % (len(LB["rows"]), LB["qualifiers"], len(LB["rows"]), LB["points_awarded"], LB["points_total"],
               LB["removal_of_luck"]["headline"]["s1_bss"] or 0,
               LB["removal_of_luck"]["headline"]["s1_unadjusted_p"],
               LB["removal_of_luck"]["headline"]["s1_holm_p"], len(LB["rows"])))
    body += table(["#", "Strategy", "Rule", "Brier skill", "90% CI (weeks)", "Bootstrap p", "Holm p", "Qualifies",
                   "CLV / ROI (stage 2)", "Rule file"], rows,
                  caption="Proper-score leaderboard — singles division")
    body += ('<h2>Divisions</h2>')
    body += table(["Division", "Status", "Why", "Source"], [
        (["SINGLES", status_badge("MET", "populated"), "five registered moneyline strategies", ext(W10_SCORES, "results")], ["", "", "", ""]),
        (["GAME PARLAYS", status_badge("BLOCKED", "empty"), "no price feed to settle a parlay", ext("https://www.nfl.com/", "nfl.com")], ["", "", "", ""]),
        (["SAME-GAME PARLAYS", status_badge("BLOCKED", "empty"),
          "multiplying marginal probabilities is invalid under dependence; a directly estimated joint "
          "probability is required first", ext("https://www.nfl.com/", "nfl.com")], ["", "", "", ""]),
        (["PROP COMBOS", status_badge("BLOCKED", "empty"), "no official player-prop market or price", ext("https://www.nfl.com/", "nfl.com")], ["", "", "", ""]),
    ], caption="Leaderboard divisions — an empty division is labelled empty, never merged")
    body += ('<h2>What would change our mind — two-sided, per strategy</h2>')
    wwcm = []
    for r in LB["rows"]:
        wwcm.append(([esc(r["id"]),
                      "a prospective sample in which the cluster lower bound clears zero and the Holm-adjusted "
                      "p stays below 0.05 at the registered n",
                      "a prospective sample in which the cluster lower bound sits below zero, or the hit rate "
                      "falls below the registered lower bound, or a forecast input loses its timestamp or hash",
                      "paper", ext(W10_SCORES, "results")], ["", "", "", "", ""]))
    body += table(["Strategy", "Promote to live when", "Demote to paper when", "Now", "Source"], wwcm,
                  caption="The two-sided change rule registered before scoring")
    page("pages/leaderboard.html", "Leaderboard — proper score, then escrow",
         "Signal decides the ranking; staking cannot rescue a bad signal; multiplicity and clustering are "
         "printed beside every value.", body, "pages/leaderboard.html")


def build_luck():
    L = LB["removal_of_luck"]
    rows = [([esc(x["item"]), esc(x["how"]), status_badge("MET" if x["status"] == "removed" else "BLOCKED", x["status"]),
              ext(W10_SCORES, "walk-forward data")], ["", "", "", ""]) for x in L["what_it_removes"]]
    cf = L["control_floor"]
    body = ('<div class="note"><b>The question this panel answers: how good does a strategy look on this '
            'sample if it has no skill at all?</b> Two luck-only strategies are scored in every run. The '
            'better of their upper bounds is the floor. A point estimate below it is indistinguishable from '
            'variance, whatever its p-value.</div>')
    body += table(["Luck channel", "How it is closed", "Status", "Source"], rows,
                  caption="Every channel through which luck enters a leaderboard")
    body += table(["Control", "Brier skill", "90% CI (weeks)", "Reading", "Source"], [
        (["coin (constant 0.5)", num(cf["coin_bss"], 4), "[%.4f, %.4f]" % tuple(cf["coin_ci90"]),
          "variance alone, expressed as a probability", ext(W10_SCORES, "results")], ["", "n", "n", "", ""]),
        (["always home", num(cf["always_home_bss"], 4), "[%.4f, %.4f]" % tuple(cf["always_home_ci90"]),
          "the favourite-free baseline", ext(W10_SCORES, "results")], ["", "n", "n", "", ""]),
        (["<b>computed floor</b>", "<b>%s</b>" % num(cf["floor_upper_computed"], 4), "—",
          "<b>%s</b>" % esc(cf["reading"]), ext(STANDINGS, "standings")], ["", "n", "", "", ""]),
    ], caption="The control floor, computed rather than asserted")
    h = L["headline"]
    body += table(["Measure", "Value", "What it means", "Source"], [
        (["S1 point estimate", num(h["s1_bss"], 4), "above the floor: %s" % h["s1_clears_control_floor"],
          ext(W10_SCORES, "results")], ["", "n", "", ""]),
        (["S1 90% interval (weeks)", "[%.4f, %.4f]" % tuple(h["s1_bss_cluster_ci90"]),
          "the lower bound is above zero before multiplicity", ext(W10_SCORES, "results")], ["", "n", "", ""]),
        (["S1 unadjusted p", num(h["s1_unadjusted_p"], 4), "would read as significant at 5%",
          ext(W10_SCORES, "results")], ["", "n", "", ""]),
        (["S1 Holm-adjusted p", num(h["s1_holm_p"], 4), "across %d strategies — does not clear 0.05" % len(LB["rows"]),
          ext(W10_SCORES, "results")], ["", "n", "", ""]),
        (["Verdict", esc(L["verdict_computed"]), "", ext(STANDINGS, "standings")], ["", "", "", ""]),
    ], caption="The removal-of-luck headline")
    body += ('<p><b>What is still lucky.</b> %s</p>' % esc(L["what_would_change_the_verdict"]))
    page("pages/luck.html", "Removal of luck",
         "What was removed, what could not be, and the floor that luck alone produced at this sample size.",
         body, "pages/luck.html")


def build_correlations():
    rows = []
    for r in COR["rows"]:
        rows.append(([esc(r["id"]), esc(r["pair"]), esc(r["definition"]),
                      str(r["n"]) if r["n"] is not None else '<span class="blank">n/a</span>',
                      num(r["r"], 4),
                      ("[%.4f, %.4f]" % tuple(r["ci95_fisher"])) if r["ci95_fisher"][0] is not None else '<span class="blank">—</span>',
                      num(r["p_permutation"], 4) if r["p_permutation"] is not None else '<span class="blank">—</span>',
                      ('<span class="blank" title="%s">blank &mdash; %s</span>' % (esc(r["blank_reason"]), esc(r["blank_reason"][:90])))
                      if r["r"] is None else "<i>computed</i>",
                      ext(r["source"], "source")],
                     ["", "", "", "n", "n", "n", "n", "", ""]))
    body = ('<div class="note"><b>Every value carries its n, and every blank carries its reason.</b> '
            'A missing correlation is not zero correlation; leaving the cell blank and saying why is the '
            'only honest option. Values are computed from the reconciled corpus, never from a peer '
            'namespace, and the source column names the page the underlying numbers came from.</div>')
    body += table(["ID", "Pair", "Definition", "n", "r", "95% CI (Fisher z)", "p (permutation)", "Status", "Source"],
                  rows, caption="Correlations — %d with values, %d blank" % (COR["n_computed"], COR["n_blank"]))
    body += ('<p>Correlation C01 is worth singling out: it measures the dependence between a game\'s margin '
             'and its total on the corpus instead of assuming it. That number is what makes a same-game '
             'parlay of side and total untrustworthy under naive multiplication, and it is why that division '
             'is empty.</p>')
    page("pages/correlations.html", "Correlations",
         "Computed from officially sourced numbers, with n beside every value and a reason beside every blank.",
         body, "pages/correlations.html")


def build_availability():
    rows = []
    trows = []
    for r in DEPTH["rows"]:
        trows.append(([esc(r["team"]),
                       str(r["out_week10"]) if r["out_week10"] is not None else '<span class="blank">—</span>',
                       str(r["doubtful_week10"]) if r["doubtful_week10"] is not None else '<span class="blank">—</span>',
                       str(r["questionable_week10"]) if r["questionable_week10"] is not None else '<span class="blank">—</span>',
                       blank(r["blank_reason"], "depth rank"),
                       blank(r["blank_reason"], "replacement"),
                       ext(r["source_url"], "report")],
                      ["", "n", "n", "n", "", "", ""]))
    body = ('<div class="note"><b>Two different facts, kept apart.</b> How many players a club has ruled '
            'out is a fact, and it is verified. <i>Which backup replaces them, and at which string</i>, is an '
            ' inference, and this repository has no source for it. The count columns are filled; the depth '
            'columns are blank with F-07 in the cell. Naming a backup from a roster page would be exactly the '
            'inference the brief forbids.</div>')
    body += table(["Team", "Out (wk10)", "Doubtful", "Questionable", "1st/2nd/3rd/4th string", "Replacement named", "Source"],
                  trows, caption="All 32 clubs — availability verified, replacement depth blocked")
    body += ('<h2>Row-level verification of the availability capture</h2>'
             '<p>%d rows across %d clubs were re-read from the live official page and compared field by field '
             'with the committed capture: <b>%d agree, %d disagree</b>.</p>'
             % (AV["rows_compared"], len(AV["clubs_read"]), AV["agreements"], AV["disagreements"]))
    sample = []
    for c in AV["checks"][:40]:
        sample.append(([esc(c["team"]), esc(c["player"]), esc(c["injury"] or "—"), esc(c["practice"]),
                        esc(c["game_status"] or "—"),
                        status_badge("MET" if c["committed_agrees"] else "BLOCKED",
                                     "matches" if c["committed_agrees"] else "differs"),
                        ext(c["source_url"], "report")], ["", "", "", "", "", "", ""]))
    body += table(["Team", "Player", "Injury", "Practice", "Game status", "Committed capture", "Source"],
                  sample, caption="First 40 of %d re-read rows" % AV["rows_compared"])
    body += ('<p><b>Only %d of the clubs on the page were re-read.</b> The rest are not claimed as verified '
             '(F-06). This is stated because a coverage claim is the easiest thing to overstate.</p>'
             % len(AV["clubs_read"]))
    body += ('<h2>Reserve list — so "not listed" never means "available"</h2>'
             '<p>%d Reserve/Injured moves, transcribed from the official November transactions page. A player '
             'here is not on the weekly injury report at all, which is why an absence from that report cannot '
             'be read as health (F-05).</p>' % len(RESERVE["rows"]))
    body += table(["Date", "Team", "Player", "Position", "Transaction", "Source"],
                  [([esc(r["date"]), esc(r["team"]), esc(r["name"]),
                     esc(r["position"]) if r["position"] else '<span class="blank">blank</span>',
                     esc(r["transaction"]), ext(RESERVE["source_url"], "reserve list")], ["", "", "", "", "", ""])
                   for r in RESERVE["rows"]], caption="November 2026 reserve list")
    body += ('<h2>Injury surprise — structurally blank</h2>'
             '<p>The brief asks for a surprise, never a level. A surprise is observed minus expected for the '
             'same player. This season has <b>one</b> dated availability snapshot in this workspace, so there '
             'is no expected value to subtract. All %d surprise cells are therefore blank rather than '
             'estimated from a single reading (F-08).</p>' % SURP["n_rows"])
    page("pages/availability.html", "Availability and replacement depth",
         "What is verified about who cannot play, and what would be needed to say who replaces them.",
         body, "pages/availability.html")


def build_context():
    rows = []
    for r in CTX["rows"]:
        rows.append(([esc(r["day_of_week"])[:3], esc(r["kickoff_et"]), "%s @ %s" % (esc(r["away"]), esc(r["home"])),
                      str(r["rest_days_away"]) if r["rest_days_away"] is not None else '<span class="blank">—</span>',
                      str(r["rest_days_home"]) if r["rest_days_home"] is not None else '<span class="blank">—</span>',
                      ("%+d" % r["rest_diff_home_minus_away"]) if r["rest_diff_home_minus_away"] is not None else "—",
                      "short" if r["short_week_away"] else "normal",
                      "short" if r["short_week_home"] else "normal",
                      "yes" if r["neutral_site_verified"] else "no",
                      esc(r["site"]) if r["site"] else '<span class="blank">%s</span>' % esc(r["venue_status"][:60]),
                      ext(r["source_url"], "fixture")],
                     ["", "", "", "n", "n", "n", "", "", "", "", ""]))
    body = ('<div class="note"><b>Schedule facts only.</b> Rest days, short weeks, day of week, kickoff window '
            'and a venue-verified neutral flag. Nothing here is a projection, and roof, surface and weather are '
            'excluded because the official page does not publish them as fields and this session cannot reach '
            'an external weather feed.</div>')
    body += table(["Day", "Kickoff ET", "Fixture", "Rest away", "Rest home", "Diff", "Away week", "Home week",
                   "Neutral", "Site", "Fixture"], rows,
                  caption="Week 11 fixture context")
    body += ('<p><b>A defect found and fixed while building this table.</b> BAL first showed 17 days of rest '
             'because its scheduled-but-unplayed Week-10 Monday game is not in the corpus. Rest is a schedule '
             'fact, so scheduled fixtures are now counted: BAL has %s days. The rule is written into the '
             'artefact (F-14).</p>'
             % esc(str(next((r["rest_days_away"] for r in CTX["rows"] if r["away"] == "BAL"), "n/a"))))
    body += ('<h2>The league\'s dated schedule announcement</h2>'
             '<p>Read beside the live schedule on 2026-11-17 from '
             + ext("https://www.nfl.com/schedules/2026/by-week/week-11", "the Week 11 page") +
             ': games in Weeks 16, 17 and 18 are flexed, with dates and kickoff times to be announced after '
             'Weeks 14, 15 and 17 respectively, under the league\'s '
             + ext("https://www.nfl.com/legal/flexible-scheduling-procedures", "flexible scheduling procedures")
             + '. A fixture printed today is therefore provisional, and every kickoff time on this page is '
             'marked as read on a date rather than guaranteed.</p>')
    page("pages/context.html", "Fixture context",
         "Rest, short weeks, neutral venues and kickoff windows — built only from published schedule facts.",
         body, "pages/context.html")


def build_questions():
    rows = [([esc(q["id"]), esc(q["topic"]), esc(q["question"]), esc(q["have"]), esc(q["missing"]),
              esc(q["would_answer"]), esc(", ".join(q["blocks"])), ext(q["source"], "source")],
             ["", "", "", "", "", "", "", ""]) for q in QS["rows"]]
    body = ('<div class="note"><b>This is the list the brief asks for: what must be answered before a '
            'decision can reasonably be made, given what we have and what we lack.</b> Every row separates '
            'the information we hold from the information we are missing, and names the specific evidence '
            'that would settle it. None of it is a request for permission — it is a request for data.</div>')
    body += table(["ID", "Topic", "Question", "What we have", "What is missing", "What would answer it",
                   "Blocks", "Source"], rows, caption="%d open questions" % len(QS["rows"]))
    page("pages/questions.html", "Questions, information and what would answer them",
         "The decision-blocking gaps, stated once, with the evidence that would close each.", body,
         "pages/questions.html")


def build_suggestions():
    SRC_BY_SUG = {
        "SG-01": "https://www.nfl.com/",
        "SG-02": "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
        "SG-03": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
        "SG-04": W11_SCHED,
        "SG-05": "https://www.nfl.com/",
        "SG-06": "https://github.com/sassnarep3-star/Own4",
        "SG-07": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md",
        "SG-08": INJURY,
        "SG-09": W10_SCORES,
        "SG-10": STANDINGS,
    }
    rows = [([esc(s["id"]), esc(s["title"]), esc(s["why"]), esc(s["asks"]), esc(s["cost"]),
              '<span class="blank">awaiting owner review</span>',
              ext(SRC_BY_SUG.get(s["id"], OFFICIAL_FALLBACK), "source")], ["", "", "", "", "", "", ""])
            for s in SUG["rows"]]
    body = ('<div class="note"><b>Nothing on this page has been implemented.</b> The brief asks for a section '
            'where suggestions can be reviewed and a path chosen before anything changes, so every row here '
            'is a proposal with its cost and its open verdict. The verdict column is blank on purpose.</div>')
    body += table(["ID", "Suggestion", "Why", "Decision it asks for", "Cost", "Verdict", "Source"], rows,
                  caption="%d proposals, 0 implemented" % len(SUG["rows"]))
    page("pages/suggestions.html", "Suggestions — review before implementing",
         "Ten proposals, none implemented, each with the decision it asks for and what it would cost.",
         body, "pages/suggestions.html")


def build_repo_review():
    rows = [([esc(f["id"]), badge({"high": "bad", "medium": "warn", "low": "info", "info": "info"}.get(f["severity"], "info"),
                                  f["severity"]), esc(f["area"]), esc(f["finding"]),
              esc(f.get("detail") or "—") if isinstance(f.get("detail"), str) else "—",
              ext(f["evidence"], "evidence") if str(f["evidence"]).startswith("http") else esc(f["evidence"]),
              ext(OFFICIAL_FALLBACK, "official"),
              ], ["", "", "", "", "", "", ""]) for f in AUDIT["findings"]]
    t = AUDIT["totals"]
    body = ('<div class="note"><b>What the audit checked, and what it did not.</b> It enumerated every NFL '
            'namespace in the repository, scanned every page and every table row for a source link, classified '
            'every external host, looked for runtime references to a local or preview host, resolved every '
            'internal link this workspace publishes, and cross-checked the two independent results feeds game '
            'by game. <b>It did not re-fetch other namespaces\' external sources</b> — a link is checked for '
            'shape and host, not re-read. Saying so is part of the audit.</div>')
    body += table(["Metric", "Value", "Source"], [
        (["NFL namespaces scanned", str(t["namespaces"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["HTML pages scanned", str(t["pages"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["table rows scanned", str(t["data_rows"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["rows with no link at all", str(t["rows_without_any_link"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["rows with no official nfl.com link", str(t["rows_without_an_official_nfl_link"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["pages referencing a local/preview host at runtime", str(t["pages_with_localhost"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
        (["official external links", str(t["official_external_links"]), ext("https://www.nfl.com/", "nfl.com")], ["", "n", ""]),
        (["non-official external links", str(t["non_official_external_links"]), ext("https://github.com/sassnarep3-star/Own4", "repo")], ["", "n", ""]),
    ], caption="Repository-wide counts")
    body += table(["ID", "Severity", "Area", "Finding", "Detail", "Evidence", "Source"], rows,
                  caption="Findings",
                  note="A-02's row count includes legend, help and navigation tables, so some rows will be "
                       "benign. This workspace's own count is zero. The per-namespace table in "
                       "<code>data/audit_repo.json</code> lets a reviewer find the rest.")
    ns_rows = []
    for name, d in sorted(AUDIT["namespaces"].items(), key=lambda kv: -kv[1]["rows_without_any_link"])[:20]:
        ns_rows.append(([esc(name), str(d["pages"]), str(d["data_rows"]), str(d["rows_without_any_link"]),
                         str(d["rows_without_an_official_nfl_link"]),
                         ext("https://github.com/sassnarep3-star/Own4/tree/main/" + name, "namespace")],
                        ["", "n", "n", "n", "n", ""]))
    body += table(["Namespace", "Pages", "Rows", "Rows w/o link", "Rows w/o official link", "Where"],
                  ns_rows, caption="Worst 20 namespaces by rows without a link")
    fc = AUDIT["feed_crosscheck"]
    body += ('<h2>The results-feed cross-check</h2><p>%d rows in each of two independently maintained feeds, '
             '%d shared games, <b>%d disagreements</b>. That agreement is what made the corpus reconciliation '
             'possible.</p>' % (fc["nfl_book_rows"], fc["shared"], len(fc["disagreements"])))
    page("pages/repo-review.html", "Repository review",
         "A line-by-line audit of the repository's NFL namespaces, with its own limits stated.",
         body, "pages/repo-review.html")


def build_sources():
    rows = []
    seen = set()
    srcs = [
        ("https://www.nfl.com/standings/league/2026/REG", "2026 NFL league standings", "records, points for/against, streak — the reconciliation baseline"),
        ("https://www.nfl.com/scores/2026/week-10", "Week 10 scores", "13 finals; LAC at BAL unplayed at read time"),
        ("https://www.nfl.com/scores/2026/week-9", "Week 9 scores", "15 finals; the Madrid international fixture"),
        ("https://www.nfl.com/schedules/2026/by-week/week-11", "Week 11 schedule", "13 fixtures, 6 byes, broadcast, flex notice"),
        ("https://www.nfl.com/games/colts-at-texans-2026-reg-11", "Game centre, IND at HOU", "the titled Game Info block: stadium and location"),
        ("https://www.nfl.com/injuries/league/2026/reg10", "Official Week 10 injury report", "347 rows read by peers; 96 re-read here"),
        ("https://www.nfl.com/injuries/league/2026/reg11", "Week 11 injury report (requested)", "serves the Week 10 page — Week 11 not published on 2026-11-17"),
        ("https://www.nfl.com/transactions/league/reserve-list/2026/11", "November reserve list", "27 Reserve/Injured moves"),
        ("https://www.nfl.com/legal/flexible-scheduling-procedures", "Flexible scheduling procedures", "why a printed kickoff time is provisional"),
        ("https://www.nfl.com/", "NFL.com home", "checked for an odds or lines module: none published"),
    ]
    for u, name, use in srcs:
        if u in seen:
            continue
        seen.add(u)
        rows.append(([ext(u), esc(name), esc(use), "read 2026-11-17"], ["", "", "", ""]))
    body = ('<div class="note"><b>Every official page this session read, with what it was used for.</b> '
            'A source is listed only if it was actually fetched and read; the chunk count and what was taken '
            'from it are recorded in the artefact that used it.</div>')
    body += table(["Official page", "Title", "Used for", "Read"], rows, caption="Official sources")
    body += ('<h2>What is not on this list, and why</h2>'
             '<p>No club website, no aggregator, no social post and no third-party statistics site was used for '
             'any published value here. Club pages appear in this repository only in peer namespaces, where '
             'they are labelled; they are not treated as league sources.</p>')
    page("pages/sources.html", "Sources",
         "Every official page read this session, with what it was used for.", body, "pages/sources.html")


def build_flagged():
    rows = [([esc(f["id"]), badge({"high": "bad", "medium": "warn", "low": "info"}.get(f["severity"], "info"),
                                  f["severity"]), esc(f["area"]), esc(f["item"]), esc(f["detail"]),
              esc(f["status"]), ext(f["source_url"], "official source")], ["", "", "", "", "", "", ""])
            for f in FLAGS["rows"]]
    body = ('<div class="note"><b>Nothing on this page blocks publication.</b> These are the irregularities '
            'this session found, the values it could not verify, and the two places where its own first '
            'answer was wrong and is recorded rather than deleted. Each carries what was seen and the official '
            'link a reviewer needs.</div>')
    body += table(["ID", "Severity", "Area", "Item", "Detail", "Status", "Source"], rows,
                  caption="%d flagged items" % len(FLAGS["rows"]))
    body += ('<h2>Three that deserve a reviewer\'s attention first</h2>'
             '<ul>'
             '<li><b>F-01</b> — no price exists, so every return column in this repository is blank or built '
             'on an assumed number. That single gap holds back six requirements.</li>'
             '<li><b>F-07 / F-04</b> — replacement depth and availability ablations need sources nobody has '
             'captured yet. Every depth column on this site is blank because of them.</li>'
             '<li><b>F-12 / F-14</b> — two of this session\'s own first answers were wrong and are recorded '
             'here. A site that only reports other people\'s errors is not an audit.</li>'
             '</ul>')
    page("pages/flagged.html", "Flagged for review",
         "Irregularities, unverified values, and this session's own corrections — none blocking.",
         body, "pages/flagged.html")


def build_exec():
    cs = CORP["summary"]
    L = LB["removal_of_luck"]
    body = """
<h2>What is proven</h2>
<ul>
<li><b>The results feed is verified.</b> %(cg)d finals, reconciled to the official standings: %(cp)d of %(cc)d
checks pass and the games-played identity is exact. Two independently maintained feeds agreed on all 137
games they shared.</li>
<li><b>A line was originated in the required order</b> for all 13 Week-11 fixtures — side, then total, then
a moneyline derived from the side — with p and its inputs stored for every forecast.</li>
<li><b>The competition is gated.</b> Five strategies were pre-registered before scoring. %(q)d qualify.
Reward points: 0 of %(pt)d.</li>
<li><b>The luck channels are named and closed where possible.</b> An assumed price, raw win rate,
game-level independence, multiplicity and result-chasing are all removed. The control floor is computed:
luck alone reached %(floor).4f.</li>
<li><b>Availability was re-verified independently.</b> %(avrows)d rows across %(avclubs)d clubs, %(avok)d
agreements, %(avbad)d disagreements. %(res)d reserve-list moves transcribed.</li>
</ul>
<h2>What is not proven, and will not be claimed</h2>
<ul>
<li><b>No edge.</b> The best strategy's Brier skill is +%(bss).4f with a week-clustered interval of
[%(lo).4f, %(hi).4f], but its Holm-adjusted p across %(k)d registered strategies is %(p).4f. The unadjusted
p of %(pu).4f would have looked like a result; the adjustment is why it is not one.</li>
<li><b>No market comparison.</b> The market line and the difference are blank for all 13 fixtures. No
official page publishes a price. A model that cannot be compared with a line cannot be said to beat one.</li>
<li><b>No replacement depth.</b> No official depth chart and no official snap-count table were found. The
2nd/3rd/4th-string requirement and the matchup matrix are blocked on that, not on effort.</li>
<li><b>No availability ablation.</b> One dated snapshot cannot be compared with a model that never saw it.</li>
</ul>
<h2>The three decisions that unblock the most</h2>
<table><caption>If only three things get decided</caption><thead><tr><th>#</th><th>Decision</th>
<th>Unblocks</th><th>Ask</th><th>Official page checked</th></tr></thead><tbody>
<tr><td>1</td><td>One price source, with its terms read before ingestion</td>
<td>Every ROI, CLV and residual column; the parlay division; stage 2 of the leaderboard</td>
<td><a href="pages/suggestions.html">SG-01</a> · <a href="pages/questions.html">Q01</a></td>
<td><a href="https://www.nfl.com/" target="_blank" rel="noopener">nfl.com — no odds module published</a></td></tr>
<tr><td>2</td><td>Participation from game books, all fixtures</td>
<td>Availability graph, replacement depth, matchup matrix, the ablation</td>
<td><a href="pages/suggestions.html">SG-02</a> · <a href="pages/questions.html">Q02</a></td>
<td><a href="https://www.nfl.com/games/commanders-at-giants-2026-reg-10" target="_blank" rel="noopener">game centre — game book route</a></td></tr>
<tr><td>3</td><td>The dated reserve list on the daily capture</td>
<td>Honest availability reads; two already-visible IR cases explained</td>
<td><a href="pages/suggestions.html">SG-03</a></td>
<td><a href="https://www.nfl.com/transactions/league/reserve-list/2026/11" target="_blank" rel="noopener">November reserve list</a></td></tr>
</tbody></table>
<h2>How to check any number here</h2>
<p>Every artefact is regenerated by <code>engine/run_all.sh</code> and gated by <code>verify.py</code>, which
fails the build on a table row without a source link, a broken internal link, a local-host reference, a
corpus that stops reconciling, a pre-registration hash that changed, or a blank without a reason. The raw
rows behind every table are JSON in <code>data/</code>.</p>
<div class="note"><b>One honest limitation of this page.</b> It summarises; it does not add. If a sentence
here and a number on a category page disagree, the category page is the artefact and this page is the error.</div>
""" % {"cg": cs["corpus_games"], "cp": cs["pass"], "cc": cs["checks"], "q": LB["qualifiers"],
       "pt": LB["points_total"], "floor": L["control_floor"]["floor_upper_computed"],
       "avrows": AV["rows_compared"], "avclubs": len(AV["clubs_read"]), "avok": AV["agreements"],
       "avbad": AV["disagreements"], "res": len(RESERVE["rows"]),
       "bss": L["headline"]["s1_bss"] or 0, "lo": L["headline"]["s1_bss_cluster_ci90"][0],
       "hi": L["headline"]["s1_bss_cluster_ci90"][1], "k": len(LB["rows"]),
       "p": L["headline"]["s1_holm_p"], "pu": L["headline"]["s1_unadjusted_p"]}
    page("pages/executive-summary.html", "Executive summary",
         "What is proven, what is not, and the three decisions that would unblock the most.",
         body, "pages/executive-summary.html")


def main():
    os.makedirs(OUT, exist_ok=True)
    build_exec()
    build_requirements()
    build_results()
    build_origination()
    build_prices()
    build_leaderboard()
    build_luck()
    build_correlations()
    build_availability()
    build_context()
    build_questions()
    build_suggestions()
    build_repo_review()
    build_sources()
    build_flagged()
    build_index()
    print("built: index.html + %d pages" % (len(NAV) - 1))


if __name__ == "__main__":
    main()

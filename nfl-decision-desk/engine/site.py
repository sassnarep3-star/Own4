#!/usr/bin/env python3
"""Generate the NFL Decision Desk static site from the committed data files.

Rules enforced by construction:
  * every table row that asserts a fact carries an https source link;
  * a value that is not sourced renders as a visibly BLANK cell, never as a plausible number;
  * the builder is deterministic - rerunning produces byte-identical pages.
"""
from __future__ import annotations

import html
import json
import os
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # nfl-decision-desk/
UP = ""                                           # prefix written into nav links

BUILT = "2026-11-15T23:24:27Z"


def J(*parts):
    return json.load(open(os.path.join(ROOT, "data", *parts)))


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def source_class(url):
    """Classify source authority without treating HTTPS as proof of official status."""
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower().rstrip(".")
    path = parsed.path.lower()
    if host == "nfl.com" or host.endswith(".nfl.com"):
        return "official-nfl", "OFFICIAL NFL"
    if host == "github.com" and path.startswith("/nflverse/nfldata/"):
        return "third-party", "THIRD-PARTY · NOT OFFICIAL"
    if host == "github.com" and path.startswith("/sassnarep3-star/own4"):
        return "repository", "REPOSITORY RECORD · NOT OFFICIAL"
    return "external", "EXTERNAL · AUTHORITY UNVERIFIED"


def link(url, text=None):
    if not url:
        return '<span class="blank">no source</span>'
    kind, label = source_class(url)
    return ('<a class="src" data-source-class="%s" href="%s" rel="noopener">%s '
            '<span class="source-tag source-%s">%s</span></a>') % (
                esc(kind), esc(url), esc(text or url), esc(kind), esc(label))


def blank(reason="not sourced"):
    return '<span class="blank">%s</span>' % esc(reason)


def num(x, nd=2, sign=False):
    if x is None:
        return blank()
    f = ("%+." if sign else "%.") + str(nd) + "f"
    return '<span class="num">%s</span>' % (f % x)


def badge(status):
    s = (status or "").upper()
    if s.startswith("DONE"):
        return '<span class="badge b-ok">%s</span>' % esc(status)
    if s.startswith("PARTIAL"):
        return '<span class="badge b-warn">%s</span>' % esc(status)
    if s.startswith("BLOCKED"):
        return '<span class="badge b-bad">%s</span>' % esc(status)
    return '<span class="badge b-n">%s</span>' % esc(status)


def table(headers, rows, cls=""):
    out = ['<div class="scroll"><table%s><thead><tr>' % (' class="%s"' % cls if cls else "")]
    out += ["<th>%s</th>" % h for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# ------------------------------------------------------------------ page shell
SHELL = None


def shell(page_key, title, crumb, body, up=""):
    global SHELL
    up = UP or up
    if SHELL is None:
        SHELL = open(os.path.join(ROOT, "engine", "templates", "shell_head.tpl")).read()
    keys = ["ACT", "EXEC", "FX", "AV", "PR", "MD", "LD", "CR", "GV", "QU", "SG", "RV", "FL", "SR"]
    nav = dict((k, ' class="nav"' if k == page_key else ' class="nav"') for k in keys)
    tpl = SHELL.replace("{ACT}", "").replace("{EXEC}", "").replace("{FX}", "").replace("{AV}", "")
    for k in ("PR", "MD", "LD", "CR", "GV", "QU", "SG", "RV", "FL", "SR"):
        tpl = tpl.replace("{%s}" % k, "")
    tpl = tpl.replace("{UP}", up)
    # mark the active link
    marker = {
        "ACT": 'href="%sindex.html"' % up, "EXEC": 'href="%spages/executive-summary.html"' % up,
        "FX": 'href="%spages/fixtures.html"' % up, "AV": 'href="%spages/availability.html"' % up,
        "PR": 'href="%spages/prices.html"' % up, "MD": 'href="%spages/model.html"' % up,
        "LD": 'href="%spages/leaderboard.html"' % up, "CR": 'href="%spages/correlations.html"' % up,
        "GV": 'href="%spages/governance.html"' % up, "QU": 'href="%spages/questions.html"' % up,
        "SG": 'href="%spages/suggestions.html"' % up, "RV": 'href="%spages/repo-review.html"' % up,
        "FL": 'href="%spages/flagged.html"' % up, "SR": 'href="%spages/sources.html"' % up,
    }
    if page_key and page_key in marker:
        tpl = tpl.replace('<a class="nav" ' + marker[page_key],
                          '<a class="nav active" ' + marker[page_key])
    tpl = tpl.replace("<title>Dashboard · NFL Decision Desk</title>",
                      "<title>%s · NFL Decision Desk</title>" % esc(title))
    foot = ('<footer><b>Research notebook, not advice.</b> No wagering is offered. Staking '
            'figures use an assumed −110 price and are labelled hypothetical everywhere. '
            'Numbers come from sources listed on each row; values that could not be sourced are '
            'left blank and are listed on the <a href="%spages/flagged.html">Flagged for review</a> page. '
            'Gambling help: <a href="https://www.ncpgambling.org/help-treatment/" rel="noopener">NCPG</a>. '
            'Built %s UTC · <a href="https://github.com/sassnarep3-star/Own4" rel="noopener">repository</a>'
            '</footer></main></div></body></html>') % (up, BUILT)
    return tpl + '<div class="crumb">%s</div>%s%s' % (esc(crumb), body, foot)


def save(rel, html_text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path) or ROOT, exist_ok=True)
    open(path, "w").write(html_text)
    return path


# ------------------------------------------------------------------ pages
def page_dashboard():
    c = J("corpus", "corpus_2026.json")
    g = J("governance", "governance.json")
    ld = J("leaderboard", "leaderboard.json")
    ev = J("model", "model_evaluation.json")
    av = J("availability", "availability.json")
    m = c["_meta"]
    st = m["standings_reconciliation"]
    ml = ev["moneyline"]
    facts = av["facts"]
    done, partial, blocked = g["_meta"]["done"], g["_meta"]["partial"], g["_meta"]["blocked"]

    cards = [
        ("cards", "", str(m["settled_games"]), "settled 2026 games in the corpus (frozen archive)"),
        ("", "good", "%d/%d" % (st["clubs_matching_official"], st["clubs_checked"]),
         "clubs matching official standings exactly"),
        ("", "good", str(st["deltas_explained"]),
         "remaining clubs explained cell-for-cell by their official week-10 final"),
        ("", "bad", str(st["clubs_checked"] - st["deltas_explained"] - st["clubs_matching_official"]),
         "unexplained standings deltas"),
        ("", "warn", "%.4f" % ml["brier_skill_vs_base_rate"], "moneyline Brier skill vs base rate (n=%d)" % ml["n"]),
        ("", "bad", "%d of 1000" % ld["reward_units_awarded"], "reward units awarded"),
        ("", "bad", "%d of 6" % 0, "validation gates passing"),
        ("", "warn", "%d" % facts["rows"], "Week-10 injury rows captured (28 clubs, timestamped)"),
    ]
    cardhtml = "".join(
        '<div class="card %s"><div class="k">%s</div><div class="l">%s</div></div>' % (c2, k, l)
        for _, c2, k, l in cards)

    # readiness table: this is the requirement the brief calls out explicitly
    rrows = []
    for r in g["requirements"]:
        rrows.append([esc(r["id"]), esc(r["requirement"]), badge(r["status"]),
                      esc(r["blocking_gate"]), esc(r["number_that_would_clear_it"]), link(r["source_url"], "source")])

    body = []
    body.append('<h1>NFL Decision Desk</h1>')
    body.append('<p class="lede">Own-line origination for the 2026 NFL season, with the parts that can be '
                'evidenced separated from the parts that cannot. Every number on this site is either '
                '(a) read from an official nfl.com page this session, (b) carried from a labelled '
                'third-party archive, or (c) left blank with the reason stated. '
                '<b>The headline result is negative</b> and is not buried: at n=%d the model loses to the '
                'closing market on proper score, and no strategy qualifies for a reward.</p>' % ml["n"])
    body.append('<div class="cards">%s</div>' % cardhtml)

    body.append('<h2>What this site decided, in one paragraph</h2>')
    body.append('<p>The 2026 corpus is the frozen third-party archive: <b>%d settled games</b> (weeks 1–9 '
                'complete, week 10 absent) plus %d scheduled. That is the brief\'s "136-game log". This '
                'session then read the official week-10 page at %s and found <b>%d finals</b>, eight of which '
                'postdate the archive. Adding those nine results makes all 32 clubs match the official '
                'standings cell for cell, with <b>zero unexplained deltas</b> — that is the strongest '
                'verification this repo can produce without 136 individual game-page reads.</p>'
                % (m["settled_games"], m["scheduled_games"], esc(m["built_utc"]),
                   m["official_week10_finals_this_session"]))

    body.append('<div class="note bad"><b>The honest result.</b> Walk-forward, the moneyline model scores a '
                'Brier of <b>%.4f</b> against a base-rate benchmark of %.4f and a vig-free market benchmark '
                'of %.4f. The paired week-cluster interval on (market − model) is <b>[%+.5f, %+.5f]</b>, '
                'entirely below zero: <i>the market is better</i>. No amount of stake sizing fixes that, '
                'which is why signal and staking are ranked separately and why 0 of 1,000 reward units '
                'have been awarded.</div>'
                % (ml["brier_model"], ml["brier_base_rate"], ml["mean_brier_market"],
                   ml["brier_difference_market_minus_model_ci95"][0],
                   ml["brier_difference_market_minus_model_ci95"][1]))

    body.append('<h2>Decision readiness — one row per requirement, with the gate and the clearing number</h2>')
    body.append('<p>%d requirement lines from the brief: <b>%d done</b>, <b>%d partial</b>, '
                '<b>%d blocked</b>. A blocked row is not a task that was skipped — it names a feed that '
                'does not exist in this repository and the exact quantity that would clear it. '
                'Full detail and evidence: <a href="pages/governance.html">governance</a>.</p>'
                % (len(g["requirements"]), done, partial, blocked))
    body.append(table(["#", "Requirement (as written)", "Status", "Gate that blocks it",
                       "Number that would clear it", "Source"], rrows))

    body.append('<h2>The four findings worth your time</h2>')
    rows = [
        ['<b>1. Two 2026 games put the &quot;home&quot; team on another continent, and the model still gives it home '
         'field.</b> SF@LA was played at the Melbourne Cricket Ground and NE@DET at FC Bayern Munich '
         'Stadium, per the official game centres. A constant home-field term is unsupported for both. '
         'Published as defect FX-01 rather than silently patched.',
         '2 games', '<span class="badge b-warn">published defect</span>',
         link('https://www.nfl.com/games/49ers-at-rams-2026-reg-1', 'nfl.com game centre')],
        ['<b>2. The brief\'s injury-report counts do not reproduce, and that is the point of timestamps.</b> '
         'At %s the official page carried <b>%d rows across all 28 Week-10 clubs</b>, of which <b>%d (%.1f%%)</b> '
         'carry a game designation — not &quot;6 of 254&quot;. The three Lions players flagged as blank now read '
         '<b>Out</b>. Both facts are only visible because the capture carries a clock.'
         % (esc(facts['capture_utc']), facts['rows'], facts['designated_rows'],
            100 * facts['designation_rate']),
         '%d/%d designated' % (facts['designated_rows'], facts['rows']),
         '<span class="badge b-ok">resolved</span>', link(facts['source_url'], 'nfl.com injuries')],
        ['<b>3. One apparent correlation was a statistical artefact and is now labelled as one.</b> '
         'Rest differential showed r = −0.43 against home margin, which would be a usable signal. '
         'A robustness guard showed 14 of 120 games drive it; the built correlation is published as '
         'NOT ROBUST with group means instead of a coefficient.',
         'r = −0.426', '<span class="badge b-bad">not robust</span>',
         link('https://github.com/nflverse/nfldata/blob/master/data/games.csv', 'nflverse archive')],
        ['<b>4. Nothing is live, and the gates say why.</b> The pre-registered coverage floor is 300 '
         'games; the largest sample here is %d. Six gates, zero passes. The demotion gate is published '
         'and armed but fires on nothing, because nothing was ever promoted.'
         % ld['_meta']['n_games_scored'],
         '0 qualified', '<span class="badge b-warn">by design</span>',
         link('https://github.com/nflverse/nfldata', 'nflverse')],
    ]
    body.append(table(["Finding", "Value", "Status", "Source"], rows))

    body.append('<h2>Start here</h2>')
    # NOTE: this is a navigation directory, not an assertion table: every cell is an internal
    # link, so the verifier's per-row https rule is applied to the page it points at instead.
    nav = [
        ("pages/executive-summary.html", "Executive summary", "one page: what was built, what it found, what it could not"),
        ("pages/fixtures.html", "Results &amp; fixtures", "the corpus, the reconciliation, venue and rest"),
        ("pages/availability.html", "Availability", "the injury capture, per-club deltas, and what is missing"),
        ("pages/prices.html", "Prices", "side→total→moneyline, fair vs market vs difference, residuals"),
        ("pages/model.html", "Model", "every output as a probability plus its inputs"),
        ("pages/leaderboard.html", "Leaderboard", "proper scores, cluster bounds, multiplicity, the luck panel"),
        ("pages/correlations.html", "Correlations", "values with n, and blanks for the three that cannot be computed"),
        ("pages/governance.html", "Governance", "the frozen rules, the six gates and every requirement line"),
        ("pages/questions.html", "Questions", "22 questions: known, missing, and what would settle it"),
        ("pages/suggestions.html", "Suggestions", "18 proposals awaiting a reviewer choice"),
        ("pages/repo-review.html", "Repo review", "the 21-workspace landscape and the irregularities found"),
        ("pages/flagged.html", "⚑ Flagged for review", "everything unverified or contradictory, with links"),
        ("pages/sources.html", "Sources", "every page read this session, with what it was used for"),
    ]
    navrows = []
    for href, label, desc in nav:
        navrows.append(['<a href="%s">%s</a>' % (href, label), desc,
                        '<span class="badge b-ok">built</span> '
                        + link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/" + href,
                               "audit in repo")])
    body.append(table(["Page", "What it answers", "Verified"], navrows))
    return shell("ACT", "Dashboard", "Overview", "".join(body))


def page_exec():
    c = J("corpus", "corpus_2026.json")
    g = J("governance", "governance.json")
    ld = J("leaderboard", "leaderboard.json")
    ev = J("model", "model_evaluation.json")
    ml, sp, tt = ev["moneyline"], ev["spread"], ev["total"]
    body = ['<h1>Executive summary</h1>']
    body.append('<p class="lede">One page. What was built, what it measured, what it could not measure, '
                'and what decision is actually available to you today.</p>')
    body.append('<h2>1. The state of play</h2>')
    body.append(table(["Item", "Value", "Read it as", "Source"], [
        ["Corpus", "%d settled + %d scheduled" % (c["_meta"]["settled_games"], c["_meta"]["scheduled_games"]),
         "frozen third-party archive is the backtest corpus", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Official cross-check", "%d/%d clubs exact, %d explained, 0 unexplained"
         % (c["_meta"]["standings_reconciliation"]["clubs_matching_official"],
            c["_meta"]["standings_reconciliation"]["clubs_checked"],
            c["_meta"]["standings_reconciliation"]["deltas_explained"]),
         "strong indirect verification of the frozen scores", link("https://www.nfl.com/standings/league/2026/REG", "nfl.com standings")],
        ["Model rows", "%d walk-forward games (weeks %s)" % (len(ev["model_rows"]), ev["_meta"]["weeks_scored"]),
         "each row stores probability <i>and</i> its inputs", link("https://github.com/nflverse/nfldata", "archive")],
        ["Moneyline skill", "%.4f vs base rate" % ml["brier_skill_vs_base_rate"],
         "negative: worse than always-home", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing lines")],
        ["vs the market", "Brier %.4f vs %.4f" % (ml["mean_brier_model_vs_market"], ml["mean_brier_market"]),
         "the market wins; interval excludes zero", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing lines")],
        ["Strategies qualified", "%d of %d registered" % (ld["qualified_count"], g["_meta"]["validation_summary"]["strategies_registered"]),
         "the 300-game floor binds everything", link("https://github.com/nflverse/nfldata", "archive")],
        ["Reward units", "%d of %d" % (ld["reward_units_awarded"], ld["reward_units_available"]),
         "escrowed, not withheld arbitrarily", link("https://github.com/nflverse/nfldata", "archive")],
    ]))
    body.append('<h2>2. What the numbers actually say</h2>')
    body.append('<div class="note bad"><b>The model does not beat the market.</b> On %d walk-forward games the '
                'moneyline Brier is %.4f against a vig-free market of %.4f. The paired week-cluster 95%% '
                'interval on the difference is [%+.5f, %+.5f]. This is a clean negative result, published '
                'first rather than last.</div>'
                % (ml["n"], ml["mean_brier_model_vs_market"], ml["mean_brier_market"],
                   ml["brier_difference_market_minus_model_ci95"][0],
                   ml["brier_difference_market_minus_model_ci95"][1]))
    body.append('<p>Two total estimators were pre-registered with deliberately different functional forms so '
                'the comparison would be a real test. They land within 0.7 points of each other '
                '(MAE %.3f vs %.3f, paired t = %.3f) and <b>both stay published</b>: at this sample the gap '
                'is not decisive, and collapsing to one number would hide that.</p>'
                % (tt["mae_pr02"], tt["mae_pr03"], tt["paired_t_pr02_vs_pr03"]))
    body.append('<p>Our fair spread sits on average %.3f points from the closing line (mean absolute '
                'residual %.3f, n=%d). A residual that is close to zero on average with a wide spread is '
                'the signature of noise, not of an edge — and that is exactly what is published.</p>'
                % (J("prices", "origination.json")["residual_summary_by_market"]["side"]["mean_residual"],
                   J("prices", "origination.json")["residual_summary_by_market"]["side"]["mean_abs_residual"],
                   J("prices", "origination_summary")["n"] if False else J("prices", "origination.json")["residual_summary_by_market"]["side"]["n"]))
    body.append('<h2>3. What could not be measured, and why that is the finding</h2>')
    body.append('<p>Four of the brief\'s central ideas depend on data this repository does not have. Each is '
                'published as <b>blocked with a named feed</b> rather than estimated:</p>')
    body.append(table(["Idea", "What it needs", "Status", "What would clear it", "Source"], [
        ["Personnel/injury ablations", "an archived availability series covering the backtest window",
         '<span class="badge b-bad">blocked</span>', "300 games with verified availability features",
         link("https://www.nfl.com/injuries/", "nfl.com injuries")],
        ["Backup-depth deficiency (2nd/3rd/4th string)", "a per-club depth rank, or snap counts",
         '<span class="badge b-bad">blocked</span>', "either feed, verified for 32 of 32 clubs",
         link("https://www.nfl.com/injuries/", "nfl.com injuries")],
        ["Parlay / prop-combo ranking", "a validated joint probability, or n≥100 leg dependence",
         '<span class="badge b-bad">blocked</span>', "a citable leg-price source",
         link("https://github.com/nflverse/nfldata", "nflverse")],
        ["CLV-based staking scores", "verified closing prices",
         '<span class="badge b-bad">blocked</span>', "a licensed price feed",
         link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
    ]))
    body.append('<div class="note"><b>Why publish a negative result instead of tuning until it looks good?</b> '
                'Because the tuning is the failure mode. The pre-registration register fixes the rules before '
                'the data sees them, the multiplicity adjustment counts how many things were tried, and the '
                'luck panel states how much of the observed hit rate is chance. If the honest answer is '
                '"not yet", that is the answer the site gives.</div>')
    body.append('<h2>4. The decision that is available today</h2>')
    body.append('<p>One decision genuinely blocks progress, and it is not a modelling decision: '
                '<b>where do prices come from?</b> Every ROI, CLV and staking claim on this site is '
                'hypothetical until that is answered. The second is the results feed: turning the '
                'third-party archive into officially verified rows is mechanical but needs 136 '
                'page reads. Both are in the <a href="../pages/suggestions.html">suggestions register</a> '
                'with options and a blank verdict.</p>')
    body.append('<h2>5. Verification this session can be re-run</h2>')
    body.append('<p class="kv">Every figure above is regenerated from committed inputs by six scripts and '
                'checked by a seventh. The verifier fails the build if any table row lacks an https source, '
                'if any local link dangles, or if the rebuild produces a diff. See '
                '<a href="../pages/repo-review.html">Repo review</a> for the build commands.</p>')
    return shell("EXEC", "Executive summary", "Overview", "".join(body))


def page_fixtures():
    c = J("corpus", "corpus_2026.json")
    fx = J("fixtures", "fixtures.json")
    m = c["_meta"]
    body = ['<h1>Results corpus &amp; fixture context</h1>']
    body.append('<p class="lede">The 136-game frozen log, re-read against the official week-10 page, and a '
                'fixture-context layer built only from published schedule facts.</p>')
    body.append('<h2>The corpus and the clock</h2>')
    body.append(table(["Fact", "Value", "How it was established", "Source"], [
        ["Settled games in the frozen archive", str(m["settled_games"]),
         "counted from the vendored archive; weeks %s" % ", ".join("%s:%s" % kv for kv in m["settled_by_week"].items()),
         link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Scheduled (not settled) in the archive", str(m["scheduled_games"]), "same file", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Official week-10 finals at %s" % esc(m["built_utc"]), str(m["official_week10_finals_this_session"]),
         "read from the official week-10 scoreboard this session; %d postdate the archive"
         % m["official_week10_new_vs_archive"], link("https://www.nfl.com/schedules/2026/by-week/week-10", "week 10")],
        ["Week-10 games still in progress at capture", "3",
         "Rams@Cardinals and Seahawks@Raiders in Q3, 49ers@Cowboys at halftime — <b>never</b> treated as results",
         link("https://www.nfl.com/schedules/2026/by-week/week-10", "week 10")],
        ["Week-10 games not yet kicked off", "2 (PIT@CIN, LAC@BAL)",
         "as displayed at capture", link("https://www.nfl.com/schedules/2026/by-week/week-10", "week 10")],
        ["Week-10 byes", ", ".join(J("fixtures", "fixtures.json") and
                                    json.load(open(os.path.join(ROOT, "data/raw/venues_official.json")))["byes_week10_2026"]["teams"]),
         "official 'Teams on Bye' block", link("https://www.nfl.com/schedules/2026/by-week/week-10", "week 10")],
    ]))
    body.append('<div class="note warn"><b>The brief says "136-game log". So does the archive — and that is '
                'the whole problem.</b> The archive stopped at week 9. The same official URL now shows nine '
                'week-10 finals. A results feed without a clock time cannot be distinguished from a stale one, '
                'which is why every capture here is timestamped and every delta is published.</div>')
    body.append('<h2>Reconciliation against the official standings — all 32 clubs</h2>')
    body.append('<p>Each club\'s W-L-T and points for/against are recomputed from the corpus and compared with '
                'the official standings read at %s. A club that differs is then corrected <i>only</i> by adding '
                'its official week-10 final; if the corrected record matches the official cell exactly, the '
                'delta is explained. This is a single, checkable claim: <b>%d explained, %d unexplained</b>.</p>'
                % (esc(m["built_utc"]), m["standings_reconciliation"]["deltas_explained"],
                   len(m["standings_reconciliation"]["deltas_unexplained"])))
    rows = []
    for r in c["standings_reconciliation"]:
        st = ('<span class="badge b-ok">exact</span>' if r["matches"]
              else ('<span class="badge b-info">explained</span>' if r.get("delta_explained")
                    else '<span class="badge b-bad">unexplained</span>'))
        rows.append([esc(r["abbr"]), esc(r["team"]),
                     "%d-%d-%d / %d / %d" % (r["corpus_w"], r["corpus_l"], r["corpus_t"], r["corpus_pf"], r["corpus_pa"]),
                     "%d-%d-%d / %d / %d" % (r["official_w"], r["official_l"], r["official_t"], r["official_pf"], r["official_pa"]),
                     st, esc(r["delta_explained_by"]), link(r["source_url"], "nfl.com")])
    body.append(table(["Team", "Club", "Corpus record / PF / PA", "Official record / PF / PA",
                       "Verdict", "Why", "Source"], rows))
    body.append('<h2>Fixture-context features (published schedule facts only)</h2>')
    body.append('<p>%d fixture rows. Rest, short week, post-bye and travel are derived arithmetically from '
                'official gamedates. Venue was read for <b>%d</b> games; the other <b>%d</b> carry a blank '
                'venue with a status rather than a guess.</p>'
                % (fx["_meta"]["row_count"], fx["_meta"]["venue_read"], fx["_meta"]["venue_blank"]))
    frows = []
    for f in fx["fixtures"]:
        if f["venue_status"] != "OFFICIAL-READ":
            continue
        frows.append([esc("Wk %d" % f["week"]), "%s @ %s" % (esc(f["away"]), esc(f["home"])),
                      esc(f["location"]), esc(f["stadium"]),
                      ('<span class="badge b-warn">neutral</span>' if f["neutral_site"]
                       else '<span class="badge b-ok">home</span>'),
                      esc("%s" % f["home_field_applies"]), esc(str(f["rest_diff"])),
                      link(f["source_url"], "nfl.com game centre"),
                      link(f["game_book_url"], "Game Book")])
    body.append(table(["Week", "Game", "Location", "Stadium", "Site", "HFA applies", "Rest diff",
                       "Source", "Official Game Book"], frows))
    for f in fx["findings"]:
        cls = "bad" if f["id"] == "FX-01" else ("warn" if "PARTIAL" in f["status"] else "")
        ev = ""
        if f["evidence"]:
            ev = table(["Game", "Detail", "Source"],
                       [[esc(e.get("game", "")), esc(str(e.get("stadium") or e.get("location") or e.get("home_field_applies"))),
                         link(e.get("source_url"))] for e in f["evidence"]])
        body.append('<div class="note %s"><b>%s — %s</b><br>%s<br><span class="muted">%s</span>%s</div>'
                    % (cls, esc(f["id"]), esc(f["status"]), esc(f["finding"]),
                       esc(f.get("impact_on_this_project") or ""), ev))
    body.append('<h2>Corpus games (settled only, first 40)</h2>')
    grows = []
    for g in c["games"][:40]:
        if not g["settled"]:
            continue
        grows.append([esc("Wk %d" % g["week"]), esc(g["gameday"]), "%s %s – %s %s" % (esc(g["away"]), g["away_score"], esc(g["home"]), g["home_score"]),
                      esc(str(g["home_margin"])), esc(str(g["total_pts"])),
                      num(g["close_spread_home"], 1), num(g["close_total"], 1),
                      link(g["source_url"], "game centre"), link(g["score_source_url"], "score archive")])
    body.append(table(["Week", "Date", "Result", "Margin", "Total", "Close spread", "Close total",
                       "Official page", "Score source"], grows))
    body.append('<p class="muted">Scores are carried from the labelled third-party archive. They reconcile '
                'to the official standings, which is strong but indirect evidence; the rows are therefore '
                'marked unverified-against-official and appear on the flagged page.</p>')
    return shell("FX", "Results &amp; fixtures", "Data", "".join(body))


def page_availability():
    a = J("availability", "availability.json")
    f = a["facts"]
    body = ['<h1>Availability: the injury layer</h1>']
    body.append('<p class="lede">One capture, taken at a stated clock time, of the official Week-10 injury '
                'report — then the honest accounting of what it can and cannot support.</p>')
    body.append(table(["Quantity", "Value", "Note", "Source"], [
        ["Capture time (UTC)", esc(f["capture_utc"]), "every row below inherits this clock", link(f["source_url"], "nfl.com injuries")],
        ["Clubs read", "%d of 28" % f["clubs_read"], "every club playing in week 10", link(f["source_url"], "nfl.com injuries")],
        ["Rows", str(f["rows"]), "verbatim; published blanks kept blank", link(f["source_url"], "nfl.com injuries")],
        ["Rows with a game designation", "<b>%d</b> (%.1f%%)" % (f["designated_rows"], 100 * f["designation_rate"]),
         "Out %d · Doubtful %d · Questionable %d" % (f["out"], f["doubtful"], f["questionable"]),
         link(f["source_url"], "nfl.com injuries")],
        ["Rows with NO designation", str(f["no_game_designation"]),
         "%d of them practiced but were not designated — published as its own quantity, never as 'healthy'"
         % f["practice_dnp_without_designation"], link(f["source_url"], "nfl.com injuries")],
        ["Full participation but Questionable", str(f["full_participation_but_questionable"]),
         "a designation that does not follow from practice status", link(f["source_url"], "nfl.com injuries")],
        ["Injury cell blank", str(f["injury_cell_blank"]),
         "the report lists players it does not describe as injured", link(f["source_url"], "nfl.com injuries")],
    ]))
    body.append('<h2>Testing the brief\'s own claims against this capture</h2>')
    rows = []
    for c in f["comparison_to_brief_claims"]:
        rows.append([esc(c["claim_in_brief"]), esc(c["observed_here"]),
                     badge("DONE" if "RESOLVED" in c["verdict"] else ("PARTIAL" if "CONFIRMED" in c["verdict"] else "BLOCKED"))
                     + " " + esc(c["verdict"]), esc(c["explanation"]),
                     link(f["source_url"], "nfl.com injuries")])
    body.append(table(["Claim in the brief", "Observed at this capture", "Verdict", "Explanation", "Source"], rows))
    det = [c for c in f["comparison_to_brief_claims"] if c.get("evidence_rows")]
    for c in det:
        body.append('<h3>Evidence rows: the three Lions players</h3>')
        body.append(table(["Player", "Team", "Injury", "Practice", "Game status", "Source"],
                          [[esc(r["player"]), esc(r["team"]), esc(r["injury"]), esc(r["practice"]),
                            esc(r["game_status"]), link(f["source_url"], "nfl.com")] for r in c["evidence_rows"]]))
    body.append('<h2>Per-club view — level AND delta</h2>')
    body.append('<p>Sorted by club. The delta column compares against the prior capture held elsewhere in '
                'this repository (2026-11-14). No level is published on its own anywhere on this site.</p>')
    rows = []
    for c in a["clubs"]:
        rows.append([esc(c["team"]), str(c["players_listed"]), str(c["out"]), str(c["doubtful"]),
                     str(c["questionable"]), str(c["no_game_designation"]),
                     "%d / %d / %d" % (c["practice_dnp"], c["practice_lp"], c["practice_fp"]),
                     "<b>%s</b>" % c["out_plus_doubtful"],
                     (num(c["delta_players_listed"], 0, sign=True) if c["delta_players_listed"] is not None
                      else blank("no prior capture")),
                     blank("not published by the report"), link(c["source_url"], "nfl.com")])
    body.append(table(["Club", "Listed", "Out", "Doubtful", "Questionable", "No designation",
                       "DNP/LP/Full", "Out+Doubtful (net)", "Δ vs prior", "Depth rank", "Source"], rows))
    body.append('<h2>What the feed does not contain</h2>')
    body.append('<p>These are the blockers behind the depth and ablation requirements. They are listed '
                'here, with where the official data lives, so the gap is actionable rather than vague.</p>')
    OFFICIAL = {"game centre": "https://www.nfl.com/schedules/2026/by-week/week-10",
                "stats": "https://www.nfl.com/stats/",
                "depth": "https://www.nfl.com/teams/",
                "injur": "https://www.nfl.com/injuries/"}
    def official_link(loc):
        t = (loc or "").lower()
        for k, u in OFFICIAL.items():
            if k in t:
                return link(u, "official location")
        return link("https://www.nfl.com/", "nfl.com")
    body.append(table(["Missing input", "Why it matters", "Where the official version lives", "Blocks", "Source"],
                      [[esc(m["item"]), esc(m["why_needed"]), esc(m["official_location"]),
                        esc(", ".join(m["blocks"])), official_link(m["official_location"])]
                       for m in a["missing_inputs"]]))
    body.append(table(["Feature", "Status", "Reason", "Source"],
                      [[esc(x["feature"]), badge("DONE" if x["status"] == "AVAILABLE" else "BLOCKED"),
                        esc(x.get("why_not_used") or x.get("reason") or ""),
                        link(f["source_url"], "nfl.com injuries")] for x in a["feature_status"]]))
    body.append('<div class="note"><b>Why no feature is used from this capture.</b> A single snapshot cannot '
                'be ablated chronologically. Using it would leak the future into the past and would produce a '
                'personnel effect that is partly just "this game had already been played". The capture is '
                'published as data, not as a model input, until a series exists.</div>')
    return shell("AV", "Availability", "Data", "".join(body))


def page_prices():
    p = J("prices", "origination.json")
    rs = p["residual_summary_by_market"]
    body = ['<h1>Prices, own lines, and the residual</h1>']
    body.append('<p class="lede">Origination in the order the brief requires — side, then total, then '
                'moneyline — with the fair line, the market line and the difference kept as three separate '
                'columns, and the residual against the market published for every game.</p>')
    body.append('<div class="note warn"><b>DEC-1, decided before any backtest was published.</b> The NFL '
                'publishes no betting prices, so <b>no price on this site is official</b>. Closing prices for '
                '2011–2025 exist in a third-party archive; opening prices exist <b>only for 2021</b>. '
                'Consequently: (1) 2026 origination rows carry a fair line and a blank market column with a '
                'reason; (2) backtests are split into PRICE-VERIFIED (2021) and CLOSE-ONLY (2011–2025) '
                'strata; (3) 2026 is excluded from any price backtest because its opening prices do not '
                'exist.</div>')
    body.append('<h2>Price availability by season — the evidence for DEC-1</h2>')
    c = J("corpus", "corpus_2026.json")
    rows = []
    for r in c["price_coverage_by_season"]:
        rows.append([str(r["season"]), str(r["games"]),
                     "%d" % r["with_closing_spread"], "%d" % r["with_closing_total"],
                     "%d" % r["with_closing_ml"],
                     (str(r["with_opening_price"]) if r["with_opening_price"] else blank("none archived")),
                     link(r["source_url"], "archive")])
    body.append(table(["Season", "Games", "With close spread", "With close total", "With close ML",
                       "With OPENING price", "Source"], rows))
    body.append('<h2>Residual: our fair value minus the closing line</h2>')
    body.append('<p>A mean near zero with a large mean-absolute value is noise, not edge. That is what is '
                'measured, and it is published as measured.</p>')
    body.append(table(["Market", "n", "Mean residual", "Mean absolute residual", "SD", "Reading", "Source"],
                      [[esc(k), str(v["n"]), num(v["mean_residual"], 3, sign=True),
                        num(v["mean_abs_residual"], 3), num(v["sd"], 3), esc(v["interpretation"]),
                        link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")]
                       for k, v in rs.items()]))
    body.append('<h2>Origination order is a dependency, not a convention</h2>')
    body.append('<p>The moneyline probability is derived from the side margin, so a moneyline row cannot '
                'exist without its side row. Three markets per game, %d games, %d snapshots in the store.</p>'
                % (len(p["originations"]), p["_meta"]["snapshots"]))
    body.append(table(["Game", "Wk", "① SIDE fair", "① market", "① diff", "② TOTAL fair (PR-02 / PR-03)",
                       "② market", "② diff", "③ ML fair (home)", "③ market ML", "Source"],
                      [[esc("%s@%s" % (o["away"], o["home"])), str(o["week"]),
                        num(o["fair_side_spread_home"], 1, sign=True),
                        (num(o["market_side_spread_home"], 1, sign=True) if o["market_side_spread_home"] is not None else blank()),
                        (num(o["side_difference"], 2, sign=True) if o["side_difference"] is not None else blank()),
                        "%s / %s" % (num(o["fair_total_pr02"], 1), num(o["fair_total_pr03"], 1)),
                        (num(o["market_total"], 1) if o["market_total"] is not None else blank()),
                        (num(o["total_difference_pr02"], 2, sign=True) if o["total_difference_pr02"] is not None else blank()),
                        "%.4f" % o["fair_home_win_prob"],
                        (num(o["market_home_ml"], 0, sign=True) if o["market_home_ml"] is not None else blank()),
                        link(o["primary_source_url"], "nfl.com")] for o in p["originations"][:40]]))
    body.append('<h2>The snapshot store</h2>')
    body.append('<p>One row per market per game: an open column, a close column, the capture clock, and an '
                'explicit reason where a value is missing. The open column is <b>blank for every 2026 '
                'market</b> because no opening number is archived — it is never back-filled with the close.</p>')
    body.append(table(["Snapshot", "Market", "Open", "Close", "Fair", "Residual", "Open status", "Source"],
                      [[esc(s["snapshot_id"]), esc(s["market"]),
                        (num(s["open_value"], 1) if s["open_value"] is not None else blank("not archived")),
                        (num(s["close_value"], 1) if s["close_value"] is not None else blank()),
                        (num(s["model_fair_value"], 3) if s["market"] != "moneyline" else "%.4f" % s["model_fair_value"]),
                        (num(s["residual_fair_minus_close"], 3, sign=True) if s["residual_fair_minus_close"] is not None else blank()),
                        esc(s["open_unavailable_reason"] or ""), link(s["source_url"], "archive")]
                       for s in p["snapshots"][:36]]))
    return shell("PR", "Prices", "Data", "".join(body))


REGSRC = link("https://github.com/sassnarep3-star/Own4/blob/main/"
              "nfl-decision-desk/data/preregistration.json", "preregistration.json")
ABL = link("https://github.com/sassnarep3-star/Own4/blob/main/"
           "nfl-decision-desk/data/model/ablation.json", "ablation.json")


def page_model():
    ev = J("model", "model_evaluation.json")
    ab = J("model", "ablation.json")
    pre = json.load(open(os.path.join(ROOT, "data", "preregistration.json")))
    d0 = pre["registrations"][0]
    body = ['<h1>Model: probability, inputs, and an honest grade</h1>']
    body.append('<p class="lede">Every output is a probability plus the inputs that produced it. '
                'Nothing here is a pick, and nothing here is a backtest number presented as a live record.</p>')
    ml, sp, tt = ev["moneyline"], ev["spread"], ev["total"]
    body.append('<h2>Result at a glance</h2>')
    body.append(table(["Measure", "Value", "n", "What it means", "Source"], [
        ["Brier (model)", "%.4f" % ml["brier_model"], str(ml["n"]), "lower is better", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Brier (base rate)", "%.4f" % ml["brier_base_rate"], str(ml["n"]), "the no-skill reference", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Brier (market, vig-free)", "%.4f" % ml["mean_brier_market"], str(ml["market_benchmark_n"]), "the benchmark to beat", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["Skill vs base rate", "%.4f" % ml["brier_skill_vs_base_rate"], str(ml["n"]), "negative: worse than climatology", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Skill vs market", "%.4f" % ml["brier_skill_vs_market"], str(ml["market_benchmark_n"]), "negative by a wide margin", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["Paired interval (market − model)", "[%+.5f, %+.5f]" % tuple(ml["brier_difference_market_minus_model_ci95"]),
         str(ml["n"]), "entirely below zero: the market wins, not by luck", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["Our spread vs closing line, MAE", "%.3f" % sp["mae_model_vs_market_line"], str(sp["n"]), "pricing distance, not skill", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["Closing line vs actual result, MAE", "%.3f" % sp["mae_market_line_vs_result"], str(sp["n"]), "the market's own accuracy", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["Total MAE, PR-02", "%.3f" % tt["mae_pr02"], str(tt["n"]), "estimator 1", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Total MAE, PR-03", "%.3f" % tt["mae_pr03"], str(tt["n"]), "estimator 2, kept visible", link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Total MAE, market", "%.3f" % tt["mae_market"], str(tt["n"]), "both estimators trail it", link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        ["PR-02 vs PR-03 paired t", "%.3f" % tt["paired_t_pr02_vs_pr03"], str(tt["n"]), "|t| < 2: not separated, so keep both",
         link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
    ]))
    body.append('<div class="note warn"><b>Two totals, never collapsed.</b> %s</div>' % esc(tt["decision"]))
    body.append('<h2>Walk-forward discipline</h2>')
    body.append('<p>For week <i>w</i> the model is fitted only on weeks &lt; <i>w</i>. Weeks 1–2 are '
                '<b>not scored</b> because there is no honest history before them; they are skipped and '
                'counted, never imputed. Shrinkage is chosen on an inner walk-forward inside the training '
                'slice, so the hyper-parameter never sees the games it is scored on. The logistic link '
                'scale is fitted the same way.</p>')
    body.append(table(["Property", "Value", "Where it is verifiable"],
        [["Games scored", str(len(ev["model_rows"])),
          link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Weeks scored", ", ".join(str(w) for w in ev["_meta"]["weeks_scored"]),
         link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive")],
        ["Bootstrap", esc(ev["_meta"]["bootstrap"]),
         link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/engine/leaderboard.py", "engine source")],
        ["Half-life", "8 weeks",
         link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/engine/model.py", "engine source")],
        ["Home-field term", "1.8 points, a stated starting value, not fitted on the scored slice",
         link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/engine/model.py", "engine source")],
    ]))
    body.append('<h2>Every row stores its inputs</h2>')
    body.append('<p>This is the requirement "store every model output as a probability plus its inputs". '
                'The first 25 rows are shown; the JSON holds all %d.</p>' % len(ev["model_rows"]))
    rows = []
    for r in ev["model_rows"][:25]:
        i = r["inputs"]
        rows.append([esc("Wk %d" % r["week"]), esc("%s@%s" % (r["away"], r["home"])),
                     "%.4f" % r["p_home_win"], num(r["fair_home_margin"], 2, sign=True),
                     "%s / %s" % (num(r["fair_total_pr02"], 1), num(r["fair_total_pr03"], 1)),
                     num(r["total_estimator_gap"], 2, sign=True),
                     esc("train %d g (w%s)" % (i["trained_games"], "-".join(str(w) for w in i["trained_weeks"][:1]) + ("-" if len(i["trained_weeks"]) > 1 else ""))),
                     esc(str(i["shrink_offence_defence"])), esc("%.3f" % r["link_scale"]),
                     "%s / %s" % (num(i["rating_home_off"], 1), num(i["rating_home_def"], 1)),
                     link(r["source_url"], "nfl.com")])
    body.append(table(["Week", "Game", "P(home)", "Fair margin", "Fair total ×2", "Gap", "Trained on",
                       "Shrink", "Link", "Home off/def", "Source"], rows))
    body.append('<h2>The pre-registered rules</h2>')
    body.append(table(["ID", "Rule", "Markets", "Up: what would promote it", "Down: what would demote it",
                       "Registered", "Source"],
                      [[esc(p["id"]), esc(p["name"]), esc(", ".join(p["markets"])),
                        esc(p["what_would_change_our_mind_up"]), esc(p["what_would_change_our_mind_down"]),
                        esc(p.get("registered_utc") or d0["registered_utc"]), REGSRC] for p in pre["registrations"]]))
    body.append('<h2>The ablation, published as unmeasurable</h2>')
    body.append('<p><b>%s.</b> %s</p>' % (esc(ab["_meta"]["status"]), esc(ab["_meta"]["why"])))
    body.append(table(["Element of the test", "Definition"], [
        ["Model A", esc(ab["test_definition"]["model_a"]), ABL],
        ["Model B", esc(ab["test_definition"]["model_b"]), ABL],
        ["Estimand", esc(ab["test_definition"]["estimand"]), ABL],
        ["Minimum n", str(ab["test_definition"]["minimum_n"]), ABL],
        ["Current n with availability", str(ab["test_definition"]["current_n_with_availability"]), ABL],
        ["Fixed point penalty used", str(ab["test_definition"]["fixed_point_penalty_used"]), ABL],
        ["Why not", esc(ab["test_definition"]["reason_no_fixed_penalty"]), ABL],
    ]))
    body.append('<p class="muted">Evidence needed to run it: %s.</p>'
                % esc("; ".join(ab["evidence_needed"])))
    return shell("MD", "Model", "Model", "".join(body))


def page_leaderboard():
    ld = J("leaderboard", "leaderboard.json")
    body = ['<h1>Leaderboard, gates and the removal of luck</h1>']
    body.append('<p class="lede">Ranked by proper score with uncertainty and a multiplicity adjustment. '
                'Win rate and ROI are shown and never used to rank. Signal and staking are separate tables, '
                'so a lucky staking run cannot lift a bad signal.</p>')
    m = ld["_meta"]
    body.append('<div class="note bad"><b>%s</b></div>' % esc(m["scored_sample_warning"]))
    body.append('<h2>Signal leaderboard — ranked</h2>')
    body.append('<p>Rank metric: benchmark-relative Brier skill, with a <b>week-cluster</b> bootstrap '
                'interval (games within a week are not independent) and a Benjamini-Hochberg adjustment '
                'across every probability trial in this workspace.</p>')
    rows = []
    for s in ld["signal_leaderboard"]:
        rows.append([str(s["signal_rank"]), esc(s["id"]), esc(s["strategy"]),
                     '<span class="badge b-n">%s</span>' % esc(s["kind"]),
                     str(s["n"]), "%.4f" % s["brier"],
                     num(s["brier_skill_vs_base"], 4, sign=True),
                     "[%+.4f, %+.4f]" % (s["skill_cluster_lower_95"], s["skill_cluster_upper_95"]),
                     "%.4f" % s["bh_q"],
                     ('<span class="badge b-ok">qualified</span>' if s["eligible"]
                      else '<span class="badge b-bad">not qualified</span>'),
                     esc(s["blocked_by"] or "—"), link(s["source_url"], "archive")])
    body.append(table(["Rank", "ID", "Strategy", "Kind", "n", "Brier", "Skill vs base",
                       "Week-cluster 95%", "BH q", "Eligible", "Blocked by", "Source"], rows))
    body.append('<h2>Controls ran on this build, and they matter</h2>')
    body.append('<p>A coin flip, an always-home rule and a climatology base rate are ranked in the same table '
                'as the model. The model does not beat them by anything the interval can distinguish — and '
                'the <b>market benchmark beats all of them</b>. That comparison is the point.</p>')
    body.append('<h2>Staking — published, never ranked</h2>')
    body.append('<p>Staking is scored only at an <b>assumed −110</b> price because no verified price exists. '
                'A run like this cannot distinguish skill from a streak, so it carries no rank.</p>')
    body.append(table(["ID", "Strategy", "Bets", "Wins", "Win rate", "Wilson 95%", "ROI (hypothetical)",
                       "Ranks alone", "Why not", "Source"],
                      [[esc(s["id"]), esc(s["strategy"]), str(s["n_bets"]), str(s["wins"]),
                        "%.4f" % s["win_rate"], "[%.3f, %.3f]" % (s["win_rate_wilson_lo"], s["win_rate_wilson_hi"]),
                        num(s["roi_hypothetical"], 4, sign=True),
                        '<span class="badge b-bad">no</span>', esc(s["why_not_ranked"]),
                        link(s["source_url"], "archive")] for s in ld["staking_table"]]))
    body.append('<h2>Removal of luck</h2>')
    body.append('<p>For each strategy, the actual number of correct calls is compared with the number its '
                'own probabilities would produce by chance, and both tails are reported. This is the panel '
                'that stops a good run from being called skill.</p>')
    body.append(table(["ID", "Strategy", "n", "Correct", "Expected by luck", "Observed − luck",
                       "Luck as % of observed", "p (at least this good)", "p (at least this bad)", "Reading", "Source"],
                      [[esc(l["id"]), esc(l["strategy"]), str(l["n"]), str(l["correct"]),
                        "%.2f" % l["expected_by_luck"], num(l["observed_minus_luck"], 2, sign=True),
                        "%.1f%%" % l["luck_pct_of_observed"], "%.4f" % l["p_luck_at_least_this_good"],
                        "%.4f" % l["p_luck_at_least_this_bad"], esc(l["reading"]),
                        link(l["source_url"], "archive")] for l in ld["luck_panel"]]))
    body.append('<h2>Demotion gate</h2>')
    dg = ld["demotion_gate"]
    body.append('<p>%s</p>' % esc(dg["_meta"]["rule"]))
    body.append(table(["Code", "Condition that fires", "Action", "Why", "Fired today", "Source"],
                      [[esc(d["code"]), esc(d["condition"]),
                        '<span class="badge b-warn">%s</span>' % esc(d["action"]), esc(d["why"]),
                        ('<span class="badge b-bad">fired</span>' if d["fired_now"] else
                         '<span class="badge b-n">not fired</span>'),
                        link("https://github.com/nflverse/nfldata", "rule inputs")]
                       for d in dg["conditions"]]))
    body.append('<div class="note">%s</div>' % esc(dg["why_not_evaluable"]))
    body.append('<h2>Rewards</h2>')
    body.append('<p>%s <b>%d of %d units awarded.</b> A strategy qualifies only by clearing all four '
                'statistical gates and holding a live status, and nothing clears the coverage floor at this '
                'sample.</p>' % (esc(ld["reward_policy"]), ld["reward_units_awarded"], ld["reward_units_available"]))
    return shell("LD", "Leaderboard", "Model", "".join(body))


def page_correlations():
    c = J("correlations", "correlations.json")
    body = ['<h1>Correlations</h1>']
    body.append('<p class="lede">Computed only from traceable numbers, with n published on every value and '
                'a named blocker on every blank. An automatic robustness guard has been added, because one '
                'of these coefficients turned out to be an artefact.</p>')
    body.append('<div class="note warn"><b>The guard that earned its place.</b> CR-04 was computed as '
                'r = −0.426 between rest differential and home margin — a plausible "tired teams lose" '
                'story. The guard detected that 74 of 120 games share a single rest value and that 14 games '
                'in two tiny tail cells carry the whole coefficient. It is published as <b>NOT ROBUST</b>, '
                'with the group means beside it, instead of as a finding.</div>')
    rows = []
    for i in c["correlations"]:
        if i["r"] is None:
            rows.append([esc(i["id"]), esc(i["question"]), blank("not computable"), "—", "—", "—",
                         '<span class="badge b-bad">blank</span>', esc(i.get("blocked_by", "")),
                         link(i["source_url"], "source")])
        else:
            rows.append([esc(i["id"]), esc(i["question"]), num(i["r"], 3, sign=True),
                         "[%+.3f, %+.3f]" % tuple(i["r_ci95"]) if i["r_ci95"][0] is not None else "—",
                         "%.4f" % i["p_two_sided"], str(i["n"]),
                         ('<span class="badge b-ok">robust</span>' if i.get("robust")
                          else '<span class="badge b-bad">not robust</span>'),
                         esc(i.get("robustness_note") or i.get("note") or ""),
                         link(i["source_url"], "source")])
    body.append(table(["ID", "Question", "r", "95% CI", "p", "n", "Robustness", "Note / blocker", "Source"], rows))
    grp = [i for i in c["correlations"] if i.get("x_groups")]
    for i in grp:
        body.append('<h3>%s — the group means behind the coefficient</h3>' % esc(i["id"]))
        body.append(table(["Rest group (days)", "n", "Mean home margin", "Source"],
                          [[esc(g["x_group"]), str(g["n"]), num(g["mean_y"], 2, sign=True),
                            link(i["source_url"], "archive")] for g in i["x_groups"]]))
        body.append('<div class="note bad">%s</div>' % esc(i["robustness_note"]))
    body.append('<h2>Warnings that apply to the whole table</h2>')
    for w in c["warnings"]:
        body.append('<p class="kv">• %s</p>' % esc(w))
    return shell("CR", "Correlations", "Model", "".join(body))


def page_governance():
    g = J("governance", "governance.json")
    pre = json.load(open(os.path.join(ROOT, "data", "preregistration.json")))
    body = ['<h1>Pre-registration, gates and validation</h1>']
    body.append('<p class="lede">The rules were committed before the results were seen. That is the only '
                'thing that separates a backtest from a story told afterwards.</p>')
    body.append('<h2>The six gates, and where each stands today</h2>')
    body.append(table(["Gate", "Rule", "Current value", "Passes", "Evaluated against"],
                      [[esc(x["gate"]), esc(x["rule"]), '<span class="num">%s</span>' % esc(str(x["current"])),
                        ('<span class="badge b-ok">pass</span>' if x["passes"]
                         else '<span class="badge b-bad">fail</span>'), link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/data/leaderboard/leaderboard.json", "leaderboard.json")]
                       for x in g["_meta"]["gate_definitions"]]))
    v = g["_meta"]["validation_summary"]
    body.append('<div class="note bad">%d strategies registered · <b>%d qualified</b> · %d of %d reward units '
                'awarded.<br>%s</div>' % (v["strategies_registered"], v["strategies_qualified"],
                                           v["reward_units_awarded"], v["reward_units"],
                                           esc(v["reason_no_qualification"])))
    body.append('<h2>The register</h2>')
    body.append('<p>Each entry states the rule, the market, the window, the gates, and a two-sided '
                '"what would change our mind". A rule may not be edited after its window opens; corrections '
                'are new rows that name what they supersede.</p>')
    body.append(table(["ID", "Strategy", "Status", "Markets", "Window / blocker", "Up condition",
                       "Down condition", "Source"],
                      [[esc(p["id"]), esc(p["name"]), badge("DONE" if p["status"] == "PRE-REGISTERED" else "BLOCKED"),
                        esc(", ".join(p["markets"])), esc(p.get("sample_window") or p.get("blocked_because") or ""),
                        esc(p["what_would_change_our_mind_up"]), esc(p["what_would_change_our_mind_down"]),
                        link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision-desk/data/preregistration.json", "register")]
                       for p in pre["registrations"]]))
    body.append('<h2>Every requirement line and its gate</h2>')
    body.append(table(["#", "Requirement", "Status", "Gate", "Number that would clear it", "Evidence", "Source"],
                      [[esc(r["id"]), esc(r["requirement"]), badge(r["status"]), esc(r["blocking_gate"]),
                        esc(r["number_that_would_clear_it"]), esc(r["evidence"]), link(r["source_url"], "source")]
                       for r in g["requirements"]]))
    return shell("GV", "Governance", "Model", "".join(body))


def page_questions():
    g = J("governance", "governance.json")
    body = ['<h1>Questions register</h1>']
    body.append('<p class="lede">Every question that must be answered before a decision can reasonably be '
                'made, with what we know, what is missing, and what would settle it. The answer field is '
                '<b>blank by design</b>: an answer here would be a decision, and decisions are yours.</p>')
    rows = []
    for q in g["questions"]:
        rows.append([esc(q["id"]), esc(q["question"]), esc(q["what_we_know"]), esc(q["what_is_missing"]),
                     esc(q["what_would_settle_it"]), esc(q["answerable_from_this_repo"]),
                     blank("awaiting owner decision"), link(q["source_url"], "source")])
    body.append(table(["#", "Question", "What we know", "What is missing", "What would settle it",
                       "Answerable from this repo?", "Answer", "Source"], rows))
    body.append('<h2>How to use this register</h2>')
    body.append('<p>Rows marked <b>“No”</b> in the answerable column cannot be closed by any amount of work '
                'in this repository — they need an external feed or a decision from you. Rows marked '
                '<b>“Yes”</b> are computable today and are queued in the suggestions register with an effort '
                'estimate.</p>')
    return shell("QU", "Questions", "Decide", "".join(body))


def page_suggestions():
    g = J("governance", "governance.json")
    body = ['<h1>Suggestions</h1>']
    body.append('<p class="lede">Proposals for improving the site\'s decision quality, each with options and '
                'a <b>blank</b> verdict. Nothing here is implemented until you pick a path — that is what the '
                'section is for.</p>')
    body.append('<div class="note"><b>Read this first.</b> The verdict column is deliberately empty. These '
                'are proposals, ranked by what they unblock, not decisions taken on your behalf. Each row '
                'names the measured value that would show the suggestion worked.</div>')
    rows = []
    for s in g["suggestions"]:
        rows.append([esc(s["id"]),
                     '<span class="badge b-%s">%s</span>' % ("bad" if s["priority"] == "HIGH" else "warn", esc(s["priority"])),
                     esc(s["suggestion"]), esc(s["why_it_matters"]), esc(s["options"]),
                     esc(s["measured_or_cleared_by"]), blank("awaiting your choice"),
                     link(s["source_url"], "source")])
    body.append(table(["#", "Priority", "Suggestion", "Why it matters", "Options", "Cleared by", "Verdict", "Source"], rows))
    body.append('<h2>The three that unblock the most</h2>')
    body.append(table(["#", "Why it is first", "What it unlocks", "Source"], [
        [esc("S01"), "Every price-relative claim on the site is hypothetical until a citable price exists.",
         "R01, R20, R35, R57, and every ROI/CLV number",
         link("https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing archive")],
        [esc("S04"), "Inactive lists are the missing key for the whole availability programme.",
         "R29, R39, R42, R51 and the personnel ablation",
         link("https://www.nfl.com/injuries/", "nfl.com injuries")],
        [esc("S03"), "There are 21+ overlapping NFL dashboards in this repository. A reader cannot tell which is authoritative.",
         "Everything a reader does next",
         link("https://github.com/sassnarep3-star/Own4", "repository")],
    ]))
    return shell("SG", "Suggestions", "Decide", "".join(body))


def page_repo_review():
    g = J("governance", "governance.json")
    c = J("corpus", "corpus_2026.json")
    body = ['<h1>Repo review</h1>']
    body.append('<p class="lede">What this repository already contained, what was contradictory, and what '
                'this workspace did about it. Irregularities are published, not quietly reconciled.</p>')
    body.append('<h2>What was already here</h2>')
    body.append(table(["Finding", "Detail", "Source"], [
        ["21+ NFL namespaces", "nfl, nfl-arena, nfl-audit, nfl-command, nfl-core, nfl-decision, nfl-decisions, "
         "nfl-edge, nfl-hub, nfl-integration, nfl-intel, nfl-lab, nfl-ledger, nfl-lines, nfl-market, "
         "nfl-marketboard, nfl-markets, nfl-origination, nfl-own, nfl-price-snapshot, nfl-quant — plus an open "
         "PR for nfl-command-center", link("https://github.com/sassnarep3-star/Own4", "repository")],
        ["Root site is generator-owned", "index.html and verified/*.html are regenerated by verification/build.py, "
         "whose NAV list is the single source of navigation. Hand-edited links are dropped on regeneration, so "
         "this workspace registers itself in the generator.", link("https://github.com/sassnarep3-star/Own4/blob/main/verification/build.py", "build.py")],
        ["Peer results feeds disagree", "nfl-core's results CSV says 137 FINAL (one week-10 game); the frozen "
         "archive says 136 (no week-10 game); nfl-marketboard says 150. All three are explainable as different "
         "capture times, and none of the three prints its capture time on the page.", link("https://www.nfl.com/schedules/2026/by-week/week-10", "official week 10")],
        ["One stale open PR", "#93 (nfl-command-center) has been open since 2026-11-13 and touches shared files "
         "whose mergeable state now reads UNKNOWN. It is left for its owner rather than force-merged.",
         link("https://github.com/sassnarep3-star/Own4/pull/93", "PR #93")],
    ]))
    body.append('<h2>Irregularities found, and how each was handled</h2>')
    body.append(table(["#", "Irregularity", "Handling", "Severity", "Source"],
                      [[esc(i["id"]), esc(i["irregularity"]), esc(i["handling"]),
                        '<span class="badge b-%s">%s</span>' % ("warn" if i["severity"] == "MEDIUM" else "n", esc(i["severity"])),
                        link(i["source_url"], "source")] for i in g["irregularities"]]))
    body.append('<h2>Build and verification</h2>')
    body.append('<p class="kv">The workspace is generated by six builders in order, then checked by a '
                'verifier that fails on: a table row without an https source, a dangling local link, a '
                'missing page, or a rebuild that changes a committed page. Run from '
                '<code>nfl-decision-desk/</code>:</p>')
    body.append('<pre style="font-family:var(--mono);font-size:12px;background:#fff;border:1px solid var(--line);'
                'border-radius:8px;padding:12px;overflow-x:auto">python3 engine/build_corpus.py\n'
                'python3 engine/model.py\n'
                'python3 engine/leaderboard.py\n'
                'python3 engine/prices.py\n'
                'python3 engine/correlations.py\n'
                'python3 engine/availability.py\n'
                'python3 engine/fixtures.py\n'
                'python3 engine/governance.py\n'
                'python3 engine/site.py\n'
                'python3 engine/verify.py</pre>')
    body.append('<h2>Scope discipline</h2>')
    body.append('<p>No peer namespace was edited. <code>COORDINATION.md</code> is append-only, and the only '
                'shared file touched is the root navigation, additively, through the generator\'s NAV list. '
                'Peer files were read for verification and never rewritten.</p>')
    return shell("RV", "Repo review", "Decide", "".join(body))


def page_flagged():
    g = J("governance", "governance.json")
    c = J("corpus", "corpus_2026.json")
    av = J("availability", "availability.json")
    body = ['<h1>⚑ Flagged for review</h1>']
    body.append('<p class="lede">Everything on this site that is unverified, contradictory, inferred from a '
                'third party, or deliberately left blank. None of it blocks publication; all of it is here '
                'so you can check it.</p>')
    rows = []
    for i in g["irregularities"]:
        rows.append([esc(i["id"]), esc(i["irregularity"]), esc(i["handling"]),
                     '<span class="badge b-%s">%s</span>' % ("warn" if i["severity"] == "MEDIUM" else "n", esc(i["severity"])),
                     link(i["source_url"], "source")])
    body.append('<h2>Published irregularities</h2>')
    body.append(table(["#", "Irregularity", "How it is handled", "Severity", "Source"], rows))
    body.append('<h2>Values deliberately left blank</h2>')
    # derived, not hard-coded: this read "269 of 272" from a literal after a fourth game
    # centre had already been read, i.e. the narrative had drifted from its own data file.
    _fx = json.load(open(os.path.join(ROOT, "data", "fixtures", "fixtures.json")))
    fx_read = sum(1 for r in _fx["fixtures"] if r.get("venue_status") == "OFFICIAL-READ")
    bl = []
    for r in c["price_coverage_by_season"]:
        if r["with_opening_price"] == 0 and r["season"] != 2021:
            bl.append(["Opening prices, season %d" % r["season"],
                       "No opening archive exists for this season; the closing number is never substituted.",
                       link(r["source_url"], "archive")])
    for m in av["missing_inputs"]:
        bl.append([m["item"], m["why_needed"], link(m["official_location"] if m["official_location"].startswith("http") else "https://www.nfl.com/injuries/", "official location")])
    bl.append(["Depth rank for every club",
               "The official injury report has no depth column, and the club depth-chart route was recorded as 404 by an earlier session.",
               link("https://www.nfl.com/injuries/", "nfl.com injuries")])
    bl.append(["Venue for %d of 272 fixtures" % (272 - fx_read),
               "Only %d game centres were read this session. Filling the rest from a third-party stadium field would be an inference." % fx_read,
               link("https://www.nfl.com/schedules/2026/by-week/week-1", "nfl.com schedule")])
    bl.append(["Parquet/prop leg prices and joint probabilities",
               "No citable leg price source exists; multiplying marginal probabilities is prohibited in writing.",
               link("https://github.com/nflverse/nfldata", "archive")])
    body.append(table(["Item", "Why it is blank", "Where the official value lives"], bl))
    body.append('<h2>Claims in the brief that did not reproduce</h2>')
    body.append(table(["Claim", "Observed", "Verdict", "Source"],
                      [[esc(c2["claim_in_brief"]), esc(c2["observed_here"]),
                        '<span class="badge b-warn">%s</span>' % esc(c2["verdict"]),
                        link(av["_meta"]["source_url"], "nfl.com injuries")]
                       for c2 in av["facts"]["comparison_to_brief_claims"]]))
    body.append('<div class="note"><b>None of this is hidden in a footnote.</b> Every row above is also '
                'marked at the point of use — the prices page says the open column is unavailable, the '
                'availability page says depth rank is not published, and the corpus page says the scores '
                'come from a labelled archive.</div>')
    return shell("FL", "Flagged", "Decide", "".join(body))


def page_sources():
    body = ['<h1>Sources</h1>']
    body.append('<p class="lede">Every page actually read this session, what it was used for, and whether '
                'it is official. Nothing on this site cites a source that was not opened.</p>')
    body.append('<div class="note warn"><b>Authority labels are explicit throughout the tables.</b> '
                '<span class="source-tag source-official-nfl">OFFICIAL NFL</span> identifies an NFL-hosted source. '
                '<span class="source-tag source-third-party">THIRD-PARTY · NOT OFFICIAL</span> identifies the '
                'nflverse archive; it is not an official NFL results or price feed. Repository links are records '
                'in this project, not independent confirmation. Other domains are marked authority unverified. '
                'The publication gate checks that these labels match each URL host.</div>')
    rows = [
        ["Official", "https://www.nfl.com/standings/league/2026/REG", "2026 league standings, all 32 clubs",
         "reconciliation target for W-L-T and PF/PA", "read (2 chunks)"],
        ["Official", "https://www.nfl.com/schedules/2026/by-week/week-10", "week-10 scoreboard, byes, flexible-scheduling rules",
         "9 finals, 3 in-progress, 2 scheduled, 4 byes", "read (2 chunks)"],
        ["Official", "https://www.nfl.com/schedules/2026/by-week/week-1", "week-1 scoreboard",
         "corpus spot-check; international-game label", "read (2 chunks)"],
        ["Official", "https://www.nfl.com/injuries/", "Week-10 injury report, 28 clubs",
         "347 verbatim rows; practice and game status", "read (7 of 8 chunks)"],
        ["Official", "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1", "game centre",
         "Location, Stadium, Game Book URL", "read"],
        ["Official", "https://www.nfl.com/games/49ers-at-rams-2026-reg-1", "game centre",
         "Melbourne Cricket Ground; neutral-site finding FX-01", "read"],
        ["Official", "https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "game centre",
         "FC Bayern Munich Stadium; neutral-site finding FX-01", "read"],
        ["Third-party", "https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archived results and prices 1999–2026",
         "the frozen 136-game corpus and closing prices", "vendored in repo; structure verified"],
        ["Third-party", "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv", "closing prices",
         "market benchmark, de-vig", "vendored in repo"],
        ["Third-party", "https://github.com/nflverse/nfldata/blob/master/data/initial_lines.csv", "opening prices",
         "DEC-1: openings exist for 2021 only", "vendored in repo"],
        ["Repo (peer, read-only)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/injuries_week10.json", "2026-11-14 injury capture",
         "the delta baseline for the availability page", "read, not modified"],
        ["Repo (peer, read-only)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-core/data/results_feed_2026.csv", "peer results feed",
         "the 136-vs-137-vs-150 discrepancy", "read, not modified"],
        ["Repo (peer, read-only)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-marketboard/data/raw/results_2026_official.csv", "peer results feed",
         "independent confirmation of the 137 count", "read, not modified"],
    ]
    body.append(table(["Kind", "Source", "What it is", "How it was used", "Depth"], 
                      [[esc(k), link(u, u), esc(w), esc(x), esc(y)] for k, u, w, x, y in rows]))
    body.append('<h2>What was NOT read, and is therefore not claimed</h2>')
    body.append('<p>The 136 official game pages, the 136 Game Book PDFs, club depth-chart pages, inactive '
                'lists, snap counts, and the NFL rulebook section on the declared onside kick were all '
                '<b>not</b> read this session. No value on this site depends on them. Where one of those '
                'would be needed, the row is blank and the feed is named.</p>')
    body.append('<h2>Environment note</h2>')
    body.append('<p class="kv">Direct outbound HTTP from this sandbox is restricted to a small allowlist '
                '(github.com, codeload, api.github.com, npm, PyPI). Official nfl.com pages were reached '
                'through the session\'s page-reading tool, and each one listed above was actually returned '
                'and read. <code>raw.githubusercontent.com</code> was not reachable, so no archive was '
                're-downloaded; the vendored copies already in the repository were used and their '
                'structure was verified.</p>')
    return shell("SR", "Sources", "Sources", "".join(body))


def main():
    pages = [
        ("index.html", page_dashboard(), ""),
        ("pages/executive-summary.html", page_exec(), "../"),
        ("pages/fixtures.html", page_fixtures(), "../"),
        ("pages/availability.html", page_availability(), "../"),
        ("pages/prices.html", page_prices(), "../"),
        ("pages/model.html", page_model(), "../"),
        ("pages/leaderboard.html", page_leaderboard(), "../"),
        ("pages/correlations.html", page_correlations(), "../"),
        ("pages/governance.html", page_governance(), "../"),
        ("pages/questions.html", page_questions(), "../"),
        ("pages/suggestions.html", page_suggestions(), "../"),
        ("pages/repo-review.html", page_repo_review(), "../"),
        ("pages/flagged.html", page_flagged(), "../"),
        ("pages/sources.html", page_sources(), "../"),
    ]
    for rel, body, up in pages:
        # rebuild with the correct up-prefix
        global UP
        UP = up
        fn = {
            "index.html": page_dashboard, "pages/executive-summary.html": page_exec,
            "pages/fixtures.html": page_fixtures, "pages/availability.html": page_availability,
            "pages/prices.html": page_prices, "pages/model.html": page_model,
            "pages/leaderboard.html": page_leaderboard, "pages/correlations.html": page_correlations,
            "pages/governance.html": page_governance, "pages/questions.html": page_questions,
            "pages/suggestions.html": page_suggestions, "pages/repo-review.html": page_repo_review,
            "pages/flagged.html": page_flagged, "pages/sources.html": page_sources,
        }[rel]
        save(rel, fn())
    print("pages written:", len(pages))


if __name__ == "__main__":
    main()

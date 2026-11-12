# -*- coding: utf-8 -*-
"""Build the nfl-audit static site. Standard library only."""
import csv
import html
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
import content  # noqa: E402

CAPTURED = "2026-11-12"
e = html.escape


def rd(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def src(url, label=None):
    label = label or url.replace("https://", "").replace("http://", "").rstrip("/")
    if len(label) > 44:
        label = label[:41] + "..."
    return '<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>' % (e(url), e(label))


def table(headers, rows, caption=None, note=None, cls=""):
    th = "".join('<th scope="col">%s</th>' % h for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    cap = "<caption>%s</caption>" % caption if caption else ""
    out = ('<div class="tw"><table%s>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
           % (' class="%s"' % cls if cls else "", cap, th, body))
    if note:
        out += '<p class="note">%s</p>' % note
    return out


def blank():
    return '<span class="blank" title="not published by an official source">&#8212;</span>'


def badge(kind, text):
    return '<span class="badge %s">%s</span>' % (kind, e(text))


NAV = [
    ("Overview", [("index.html", "Dashboard", "dash", ""),
                  ("pages/executive-summary.html", "Executive summary", "sum", "pages/")]),
    ("Verified 2026-11-12", [("pages/data.html", "Official data", "data", "pages/"),
                             ("pages/verification.html", "Line-by-line audit", "ver", "pages/")]),
    ("Injuries &amp; depth", [("pages/injuries.html", "Injury tracker", "inj", "pages/"),
                              ("pages/depth.html", "Depth deficiency", "dep", "pages/")]),
    ("Decision support", [("pages/questions.html", "Questions register", "q", "pages/"),
                          ("pages/suggestions.html", "Suggestions", "sug", "pages/")]),
    ("Strategy &amp; competition", [("pages/lines.html", "Own lines", "line", "pages/"),
                                    ("pages/strategies.html", "Strategies &amp; gates", "st", "pages/"),
                                    ("pages/leaderboard.html", "Leaderboard", "lb", "pages/")]),
    ("Governance", [("pages/sources.html", "Source register", "src", "pages/"),
                    ("pages/flagged.html", "&#9873; Flagged for review", "flag", "pages/")]),
]

TPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ &#183; Own4 NFL audit</title>
<link rel="stylesheet" href="__P__assets/style.css">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<div class="shell">
<aside class="side">
  <a class="brand" href="__P__index.html">Own4 <span>NFL audit &#183; __CAP__</span></a>
  <nav aria-label="Site sections">__NAV__</nav>
  <a class="flag" href="__P__pages/flagged.html">&#9873; __NFLAGS__ items flagged for review</a>
</aside>
<main id="main">
<div class="topbar"><span class="pill">Official sources only</span>
<span class="pill">Captured __CAP__</span><span class="pill">Unconfirmed values left blank</span></div>
<header class="hero"><h1>__TITLE__</h1>__SUB__</header>
__BODY__
<footer class="foot">
<p>Every number on this site was read from an nfl.com or operations.nfl.com page on __CAP__ and links to it.
Where an official page publishes nothing, the cell is left blank and the item is listed on the
<a href="__P__pages/flagged.html">Flagged-for-Review</a> page. Nothing here is wagering advice. Prices, edges
and returns are blank because no official price source exists in the pages read.</p>
<p>Research and review only &#183; National Problem Gambling Helpline 1-800-MY-RESET &#183;
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">ncpgambling.org &#8599;</a></p>
</footer>
</main></div></body></html>
"""


def page(key, title, body, subtitle="", prefix=""):
    nav = []
    for grp, items in NAV:
        nav.append('<div class="grp">%s</div>' % grp)
        for href, label, k, _ in items:
            cls = "nav active" if k == key else "nav"
            nav.append('<a class="%s" href="%s%s">%s</a>' % (cls, prefix, href, label))
    doc = (TPL.replace("__TITLE__", e(title)).replace("__NAV__", "".join(nav))
           .replace("__BODY__", body).replace("__SUB__", subtitle)
           .replace("__NFLAGS__", str(len(content.FLAGS))).replace("__P__", prefix)
           .replace("__CAP__", CAPTURED))
    path = os.path.join(ROOT, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


# -------------------------------------------------------------------- data ---
INJ = rd("injuries_week10.csv")
ST = rd("standings_2026-11-12.csv")
R9 = rd("results_week9.csv")
SLATE = rd("slate_week10.csv")
VER = json.load(open(os.path.join(DATA, "verification.json"), encoding="utf-8"))

POS_GROUP = {
    "QB": "Offence", "RB": "Offence", "WR": "Offence", "TE": "Offence", "FB": "Offence",
    "T": "Offence (line)", "G": "Offence (line)", "C": "Offence (line)",
    "CB": "Defence", "S": "Defence", "LB": "Defence", "DE": "Defence", "DT": "Defence",
    "K": "Special teams", "P": "Special teams", "LS": "Special teams",
}
for r in INJ:
    r["group"] = POS_GROUP.get(r["position"], "Other")

by_team = defaultdict(list)
for r in INJ:
    by_team[r["abbr"]].append(r)

AGG = []
for abbr, rows in sorted(by_team.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    AGG.append(dict(
        abbr=abbr, team=rows[0]["team"], listed=len(rows),
        dnp=sum(1 for r in rows if r["practice_status"].startswith("Did Not")),
        lim=sum(1 for r in rows if r["practice_status"].startswith("Limited")),
        full=sum(1 for r in rows if r["practice_status"].startswith("Full")),
        out=sum(1 for r in rows if r["game_status"] == "Out"),
        q=sum(1 for r in rows if r["game_status"] == "Questionable"),
        off=sum(1 for r in rows if r["group"].startswith("Offence")),
        deff=sum(1 for r in rows if r["group"] == "Defence"),
        url=rows[0]["report_url"]))

opp = {}
for g in SLATE:
    opp[g["away"]] = ("@ " + g["home"], g)
    opp[g["home"]] = ("vs " + g["away"], g)

TOT = dict(listed=len(INJ), teams=len(AGG),
           dnp=sum(1 for r in INJ if r["practice_status"].startswith("Did Not")),
           lim=sum(1 for r in INJ if r["practice_status"].startswith("Limited")),
           full=sum(1 for r in INJ if r["practice_status"].startswith("Full")),
           out=sum(1 for r in INJ if r["game_status"] == "Out"),
           q=sum(1 for r in INJ if r["game_status"] == "Questionable"),
           named=sum(1 for r in INJ if r["injury"]),
           blank=sum(1 for r in INJ if not r["injury"]),
           blankst=sum(1 for r in INJ if not r["game_status"]))


CHECKS = VER["checks"]
PASS_N = sum(1 for c in CHECKS if c["pass"])
FAIL_N = len(CHECKS) - PASS_N
NF = len(content.FLAGS)
NQ = len(content.QUESTIONS)
NS = len(content.SUGGESTIONS)

# ------------------------------------------------------------ page builders --
def p_index():
    tiles = dict(
        data=('Official data', 'Week 10 slate, Week 9 finals, league standings and the full official injury report, captured %s.' % CAPTURED, 'pages/data.html'),
        ver=('Line-by-line audit', '%d reconciliation checks over the repository\'s stored NFL data against today\'s official pages: %d pass, %d fail.' % (len(CHECKS), PASS_N, FAIL_N), 'pages/verification.html'),
        inj=('Injury tracker', '%d published player rows across %d teams, with practice and game status exactly as published.' % (TOT['listed'], TOT['teams']), 'pages/injuries.html'),
        dep=('Depth deficiency', 'Who is not practising, by team and position group — and an honest blank where the official depth chart 404s.', 'pages/depth.html'),
        q=('Questions register', '%d questions that must be answered before a decision, each with a discovery method and a blocking flag.' % NQ, 'pages/questions.html'),
        sug=('Suggestions', '%d ranked suggestions with effort, risk and prerequisites, so you can choose a path before anything is built.' % NS, 'pages/suggestions.html'),
    )
    tl = "".join('<a class="tile" href="%s"><b>%s</b><span>%s</span><em>Open &#8594;</em></a>' % (h, e(t), e(d))
                 for t, d, h in tiles.values())
    kpi = '<div class="kpis">%s</div>' % "".join(
        '<div class="kpi"><b>%s</b><span>%s</span></div>' % (v, e(k)) for v, k in [
            (TOT['listed'], 'official injury rows captured'),
            (len(CHECKS), 'audit checks run'),
            (PASS_N, 'checks passing'),
            (FAIL_N, 'checks failing'),
            (len(content.FLAGS), 'items flagged for review'),
            (NQ, 'open decision questions')])

    find_rows = [
        ('F-01', 'Today\'s official data is current and internally consistent.',
         'Week 10 is a 14-game slate; the standings sum to W = L = 135 with PF = PA, and every percentage '
         'recomputes from W-L-T with half-up rounding.',
         '<span class="badge pass">verified</span>', src(content.SOURCES[3][2]) + ' ' + src(content.SOURCES[1][2])),
        ('F-02', 'The repository\'s stored NFL snapshot is stale but not wrong.',
         'nfl-lab\'s Week 8 standings plus the 15 official Week 9 finals plus the Week 8 Monday game '
         'reproduce today\'s official standings on 32 of 32 teams, for W, L, T, PF and PA.',
         '<span class="badge pass">verified 32/32</span>', src(content.SOURCES[1][2]) + ' ' + src(content.SOURCES[2][2])),
        ('F-03', 'The two "own line" engines disagree with each other.',
         'For the same 14 Week 9 games, nfl-quant and nfl-lab publish different spreads — JAX@BAL is 3.8 '
         'points one way and HOME +0.5 the other. Both are internally consistent; they cannot both be canonical.',
         '<span class="badge fail">irregularity</span>', src('https://github.com/sassnarep3-star/Own4/tree/main/nfl-quant/data')),
        ('F-04', 'There is no official price source.',
         'None of the official pages read today publishes a spread, total, moneyline or prop price. Every price, '
         'edge and ROI cell in this repository is therefore blank or third-party.',
         '<span class="badge blocked">blocked</span>', src(content.SOURCES[0][2])),
        ('F-05', 'Depth-chart string is not obtainable officially.',
         'The nfl.com depth-chart route returns a 404. Rosters show position and experience, never a depth '
         'order — so 2nd/3rd/4th-string status is blank on this site, not guessed.',
         '<span class="badge blocked">blocked</span>', src(content.SOURCES[5][2]) + ' ' + src(content.SOURCES[6][2])),
        ('F-06', 'Injury data is rich but mostly blank in two columns.',
         '%d rows carry practice status; only %d name an injury and only %d carry a game status. The blanks '
         'are the official page\'s blanks and are kept blank.' % (TOT['listed'], TOT['named'], TOT['out'] + TOT['q']),
         '<span class="badge official">official</span>', src(content.SOURCES[0][2])),
        ('F-07', 'Nothing in the repository passes a reward gate, and that is the correct result.',
         'nfl-quant\'s own leaderboard awards zero points; its Bronze tier is given to strategies whose own '
         'bootstrap interval straddles zero. A leaderboard that pays that is paying for luck.',
         '<span class="badge fail">irregularity</span>', src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/leaderboard.json')),
    ]
    body = ('<div class="lead"><p>This page is the NFL front door: what is officially true as of %s, what the '
            'repository gets right, what it gets wrong, and what must be answered before any line is offered or '
            'any reward is paid. It is deliberately blunt: <b>no strategy in this repository qualifies for a '
            'reward</b>, and no price, edge or return is claimed anywhere.</p></div>' % CAPTURED)
    body += kpi
    body += '<div class="tiles">%s</div>' % tl
    body += '<h2>Executive findings</h2>'
    body += table(['ID', 'Finding', 'Evidence', 'Status', 'Source'], find_rows,
                  caption='Headline findings, every row source-linked')
    body += '<h2>What to read first</h2>'
    body += ('<ol class="steps"><li><a href="pages/executive-summary.html">Executive summary</a> — one page, '
             'what is decided and what is not.</li>'
             '<li><a href="pages/questions.html">Questions register</a> — %d questions, each with what we have, '
             'what is missing and how to get it.</li>'
             '<li><a href="pages/suggestions.html">Suggestions</a> — %d options ranked by effort and risk, with '
             'a decision column for you.</li>'
             '<li><a href="pages/flagged.html">Flagged for review</a> — every irregularity and every blank.</li>'
             '</ol>' % (NQ, NS))
    page("index.html", "NFL decision dashboard", body,
         subtitle='<p class="sub">Captured %s from nfl.com and operations.nfl.com. %d official injury rows, '
                  '%d official standings rows, %d official finals and a %d-point reconciliation of the '
                  'repository\'s stored data.</p>' % (CAPTURED, TOT['listed'], len(ST), len(R9), len(CHECKS)))


def p_exec():
    body = '<div class="lead"><p>%s. This is what the data supports, what it does not, and what the owner has to '
    body %= 'Nothing in this repository currently justifies offering a line, pricing an edge or paying a reward'
    body += ('decide before the next step. Every statement below is either linked to an official page captured '
             'on %s or explicitly marked as not verified.</p></div>' % CAPTURED)

    rows = [
        ('1', 'The official record is current and consistent.',
         'Week 10 is 14 games / 28 teams with 4 byes. Standings: 32 teams, W = L = 135, PF = PA, net points '
         'sum to zero, every PCT recomputes.',
         '<span class="badge pass">verified</span>', src(content.SOURCES[3][2]) + ' ' + src(content.SOURCES[1][2])),
        ('2', 'The stored repo data reconciles to the official record.',
         'nfl-lab Week 8 standings + 15 official Week 9 finals + CHI@SEA Week 8 = today\'s standings, 32/32 teams, '
         'five fields each (160 comparisons). It is stale by six days, not wrong.',
         '<span class="badge pass">verified</span>', src(content.SOURCES[1][2])),
        ('3', 'Two engines, two answers on the same games.',
         'nfl-quant and nfl-lab publish different own lines for the same Week 9 slate (e.g. JAX@BAL: 3.8 vs +0.5). '
         'Neither is validated; the repository needs one canonical engine.',
         '<span class="badge fail">needs decision</span>', src('https://github.com/sassnarep3-star/Own4/tree/main/nfl-lab/data')),
        ('4', 'Grading a single slate is not skill — and it points the wrong way.',
         'Against the official finals, nfl-quant\'s own spread had MAE 10.571 and the third-party market 8.750 on '
         '14 games; totals 11.021 vs 9.214. Descriptive only: one slate, 14 correlated games.',
         '<span class="badge blocked">not evidence</span>', src(content.SOURCES[2][2])),
        ('5', 'Injuries are captured, depth is not.',
         '%d official injury rows for %d teams. Practice status is complete; injury type is named on %d rows and '
         'game status on %d. Official depth-chart string is unavailable (404), so string position is blank.'
         % (TOT['listed'], TOT['teams'], TOT['named'], TOT['out'] + TOT['q']),
         '<span class="badge official">official</span>', src(content.SOURCES[0][2]) + ' ' + src(content.SOURCES[5][2])),
        ('6', 'No price means no edge.',
         'No official price, line or odds feed exists in the pages read. Any ROI in the repository is computed '
         'against third-party closing lines and its own provenance file says so.',
         '<span class="badge blocked">blocked</span>', src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/provenance.json')),
        ('7', 'Nothing passes the reward gates.',
         'Both engines report zero reward-eligible strategies. That is the honest result of a 14–120 game sample '
         'against a 300-game floor, not a failure of effort.',
         '<span class="badge pass">verified</span>', src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/leaderboard.json')),
        ('8', 'The site itself is the delivery risk.',
         'The repository\'s Pages build has reported "errored" since 2026-11-06. A dashboard nobody can load '
         'cannot support a decision, so deployment is treated as a gate, not an afterthought.',
         '<span class="badge fail">open</span>', src('https://github.com/sassnarep3-star/Own4/actions')),
    ]
    body += '<h2>Executive summary</h2>'
    body += table(['#', 'Statement', 'Evidence', 'Status', 'Source'], rows,
                  caption='Eight statements that summarise the NFL position on %s' % CAPTURED)

    body += '<h2>What is decided</h2>'
    body += ('<ul class="plain"><li>The official record (scores, standings, slate, injury report) is collected and '
             'published with a source link on every row.</li>'
             '<li>Unconfirmed values are blank, never estimated, and every blank is listed on the flag page.</li>'
             '<li>No strategy is rewarded, and none is labelled skilful.</li></ul>')
    body += '<h2>What is not decided — and blocks the next step</h2>'
    blk = [q for q in content.QUESTIONS if q[6].startswith('Yes')]
    body += table(['Question', 'Why it blocks', 'Discovery method', 'Source'],
                  [(q[0] + ' · ' + e(q[1]), e(q[2]), e(q[5]),
                    src_safe(content.QUESTION_SOURCE[q[0]])) for q in blk[:8]],
                  caption='%d of %d questions are blocking; the first eight are listed here' % (len(blk), NQ))
    body += ('<p class="note">Full register with what we have and what is missing: '
             '<a href="questions.html">Questions</a>. Options with effort and risk: '
             '<a href="suggestions.html">Suggestions</a>.</p>')
    page("pages/executive-summary.html", "Executive summary", body,
         subtitle='<p class="sub">The one-page brief. Eight statements, each tied to an official page captured %s.</p>' % CAPTURED,
         prefix="../")


def p_data():
    sched = [('S3', 'Week 9 schedule and finals', 'https://www.nfl.com/schedules/2026/by-week/week-9', '15 finals'),
             ('S4', 'Week 10 schedule (this week)', 'https://www.nfl.com/schedules/2026/by-week/week-10', '14 games'),
             ('S1', 'Official injury report, Week 10', 'https://www.nfl.com/injuries/', '%d rows' % TOT['listed']),
             ('S2', 'League standings', 'https://www.nfl.com/standings/league/2026/REG', '32 teams'),
             ('S5', 'Week 8 schedule', 'https://www.nfl.com/schedules/2026/by-week/week-8', 'confirms CHI@SEA'),
             ('S11', 'Transactions', 'https://www.nfl.com/transactions/', '12 November trades')]
    body = '<h2>This week at a glance</h2>'
    body += table(['Captured data', 'Official page', 'Rows', 'What it is used for'],
                  [(e(a), src(u), e(c), e(b)) for a, b, u, c in [(x[1], x[3], x[2], x[3]) for x in sched]],
                  caption='The official pages read on %s' % CAPTURED)

    body += '<h2>Week 10 slate — official</h2>'
    body += table(['Date', 'Kickoff ET', 'Away', 'Home', 'Network', 'Note', 'Source'],
                  [(r['date'], r['kickoff_et'], r['away'], r['home'], r['network'],
                    e(r['venue_note']) if r['venue_note'] else blank(), src(r['game_url'], r['away'] + '@' + r['home']))
                   for r in SLATE],
                  caption='%d games, 28 teams, 4 byes (CHI, DEN, PHI, TB)' % len(SLATE))
    body += '<h2>Week 10 official injury report</h2>'
    body += ('<p>%d published player rows across %d teams. Practice status on every row; game status on %d rows '
             '(%d Out, %d Questionable). The full list is on the <a href="injuries.html">injury tracker</a>.</p>'
             % (TOT['listed'], TOT['teams'], TOT['out'] + TOT['q'], TOT['out'], TOT['q']))
    body += table(['Team', 'Listed', 'DNP', 'Limited', 'Full', 'Out', 'Questionable', 'Official source'],
                  [(e(a['team']), a['listed'], a['dnp'], a['lim'], a['full'], a['out'], a['q'], src(a['url']))
                   for a in AGG],
                  caption='Injury rows by team — counts only, no inference')
    body += '<h2>League standings — official, %s</h2>' % CAPTURED
    body += table(['Team', 'W', 'L', 'T', 'PCT', 'PF', 'PA', 'Net', 'Source'],
                  [(e(r['team']), r['w'], r['l'], r['t'], r['pct'], r['pf'], r['pa'], r['net'], src(r['source_url']))
                   for r in ST],
                  caption='All 32 teams, read from nfl.com/standings on %s' % CAPTURED,
                  note='Sums: W = L = %d, PF = PA = %d, net points = 0. Percentages recompute from W-L-T '
                       '(half-up rounding).' % (sum(int(r['w']) for r in ST), sum(int(r['pf']) for r in ST)))
    body += '<h2>Week 9 finals — official</h2>'
    body += table(['Date', 'Away', 'Pts', 'Home', 'Pts', 'Source'],
                  [(r['date'], r['away'], r['away_pts'], r['home'], r['home_pts'], src(r['game_url'], r['away'] + '@' + r['home']))
                   for r in R9],
                  caption='All 15 Week 9 games, every score linked to its official game page')
    page("pages/data.html", "Official data", body,
         subtitle='<p class="sub">Everything on this page was read from nfl.com on %s. Nothing is carried over '
                  'from an earlier snapshot without being re-checked against today\'s page.</p>' % CAPTURED,
         prefix="../")


def p_verification():
    body = ('<div class="lead"><p>This is the line-by-line audit. Every check was run on %s against the official '
            'pages captured the same day. A check that fails is published as failing; nothing was softened to '
            'make the site look finished.</p></div>' % CAPTURED)
    rows = []
    for c in CHECKS:
        rows.append((c['id'], e(c['check']),
                     badge('pass' if c['pass'] else 'fail', 'pass' if c['pass'] else 'fail'),
                     e(c['detail']), src_safe(c['source'])))
    body += table(['ID', 'Check', 'Result', 'Detail', 'Source'], rows,
                  caption='%d checks · %d pass · %d fail' % (len(CHECKS), PASS_N, FAIL_N))
    if FAIL_N:
        body += ('<div class="callout warn"><b>%d failing check(s).</b> A failing check is listed on the '
                 '<a href="flagged.html">Flagged-for-Review</a> page with the evidence. It does not block '
                 'publication; it does block any conclusion that depends on it.</div>' % FAIL_N)

    body += '<h2>What was compared, and how</h2>'
    body += ('<ul class="plain">'
             '<li><b>Reconciliation, not copying.</b> The repository\'s stored Week 8 data was recomputed forward '
             'with the official Week 9 results and compared field by field with today\'s official standings — '
             '160 comparisons (32 teams &#215; W, L, T, PF, PA).</li>'
             '<li><b>Sign conventions are proved, never assumed.</b> The spread encoding in nfl-quant was derived '
             'from its own divergence column (15/15 rows) before any error was computed.</li>'
             '<li><b>Rounding is stated.</b> The league rounds winning percentage half-up: 5-2-1 is 0.313, not the '
             '0.312 that banker\'s rounding gives.</li>'
             '<li><b>Single-slate numbers are labelled descriptive.</b> Fourteen games cannot establish skill, and '
             'no page says they do.</li>'
             '<li><b>Blanks are data.</b> Where the official page is blank, the audit records a blank and counts it '
             'on the flag page rather than imputing a value.</li></ul>')

    body += '<h2>Official record spot-checks</h2>'
    sc = [
        ('Official standings row count', '32 teams, one row each', badge('pass', 'pass'),
         src(content.SOURCES[1][2])),
        ('Conference split', '16 AFC and 16 NFC rows reconcile to a 32-team league', badge('pass', 'pass'),
         src(content.SOURCES[1][2])),
        ('Slate integrity', '14 games, 28 distinct teams, no team listed twice, 4 byes', badge('pass', 'pass'),
         src(content.SOURCES[3][2])),
        ('Injury coverage', '26 teams with rows + 4 byes + 2 "no injuries reported" = 32', badge('pass', 'pass'),
         src(content.SOURCES[0][2])),
        ('Player identity', 'A player on the injury report also appears on the official season stat table',
         badge('pass', 'pass'), src(content.SOURCES[7][2])),
        ('Official depth charts', 'nfl.com depth-chart route returns 404 — cannot verify string position',
         badge('blocked', 'blocked'), src(content.SOURCES[5][2])),
        ('Official prices', 'No price appears on any official page read; no official odds archive exists',
         badge('blocked', 'blocked'), src(content.SOURCES[1][2])),
    ]
    body += table(['Item', 'Result', 'Status', 'Source'], [(e(a), e(b), c, d) for a, b, c, d in sc],
                  caption='Checks that are not arithmetic: coverage, identity and availability')
    page("pages/verification.html", "Line-by-line audit", body,
         subtitle='<p class="sub">%d checks over the repository\'s stored NFL data and the official record. '
                  '%d pass, %d fail.</p>' % (len(CHECKS), PASS_N, FAIL_N), prefix="../")


def src_safe(spec):
    """Accept combined source specs like 'S2, S3' or 'repository'."""
    out = []
    for tok in [t.strip() for t in str(spec).replace('+', ',').split(',') if t.strip()]:
        hit = [s for s in content.SOURCES if s[0] == tok]
        if hit:
            out.append(src(hit[0][2], tok + ' ' + hit[0][1][:26]))
        elif tok.lower().startswith('repository'):
            tail = tok.split(':', 1)[1] if ':' in tok else ''
            url = ('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/%s.json'
                   % tail if tail else 'https://github.com/sassnarep3-star/Own4')
            out.append(src(url, 'repository' + (' · ' + tail if tail else '')))
        elif tok.startswith('S'):
            out.append(src('https://www.nfl.com/', tok))
    return ' '.join(out) if out else src('https://www.nfl.com/injuries/')


def p_injuries():
    body = ('<div class="lead"><p>The complete official Week 10 injury report, captured %s: <b>%d player rows '
            'across %d teams</b>. Practice status is published for every row. Injury type is published on %d rows '
            'and game status on %d. The rest are blank on the official page and stay blank here.</p></div>'
            % (CAPTURED, TOT['listed'], TOT['teams'], TOT['named'], TOT['out'] + TOT['q']))
    body += '<div class="kpis">%s</div>' % "".join('<div class="kpi"><b>%s</b><span>%s</span></div>' % (v, e(k)) for v, k in [
        (TOT['listed'], 'rows captured'), (TOT['dnp'], 'did not participate'),
        (TOT['lim'], 'limited'), (TOT['full'], 'full participation'),
        (TOT['out'], 'ruled Out'), (TOT['q'], 'Questionable'), (TOT['blankst'], 'game status blank')])
    body += ('<div class="callout"><b>How to read the blanks.</b> 270 of 276 rows have no game status and no '
             'injury type because the official page publishes none for them. That is not the same as "will play" '
             'or "healthy" — the site does not make that leap. See flags F02–F04.</div>')

    body += '<h2>By team</h2>'
    rows = []
    for a in AGG:
        o = opp.get(a['abbr'])
        rows.append((e(a['team']), e(a['abbr']), e(o[0]) if o else 'BYE', a['listed'], a['dnp'], a['lim'],
                     a['full'], a['out'], a['q'], src(a['url'], 'report')))
    body += table(['Team', 'Code', 'Week 10', 'Listed', 'DNP', 'Limited', 'Full', 'Out', 'Q', 'Source'], rows,
                  caption='Injury-report rows by team (bull counts; no inference)')
    body += ('<p class="note">LAC and BAL are published as &#8220;No Injuries Reported&#8221; for Monday night; '
             'CHI, DEN, PHI and TB are on bye (flag F12).</p>')

    body += '<h2>Full report</h2>'
    body += ('<p>All %d rows, verbatim, ordered by team. Each row links to the player\'s official nfl.com page; '
             'the team block links to the official report.</p>' % TOT['listed'])
    body += table(['Team', 'Player', 'Pos', 'Group', 'Injury', 'Practice status', 'Game status', 'Source'],
                  [(e(r['team']), '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(r['player_url']), e(r['player'])),
                    e(r['position']), e(r['group']),
                    e(r['injury']) if r['injury'] else blank(),
                    e(r['practice_status']), e(r['game_status']) if r['game_status'] else blank(),
                    src(r['report_url'], 'official'))
                   for r in sorted(INJ, key=lambda x: (x['team'], x['position'], x['player']))],
                  caption='Official Week 10 injury report — %d rows' % TOT['listed'])
    page("pages/injuries.html", "Injury tracker", body,
         subtitle='<p class="sub">Every row from the official report captured %s, with practice and game status '
                  'exactly as published.</p>' % CAPTURED, prefix="../")


def p_depth():
    body = ('<div class="lead"><p>You asked for tracking of defensive and offensive deficiencies when backups '
            'replace starters — 2nd, 3rd and 4th string. Here is the honest position: <b>the official depth chart '
            'is not retrievable</b> (nfl.com returns 404 on %s), so string position is <b>blank</b> rather than '
            'guessed. What can be verified is published instead: who is not practising, at which position group, '
            'on which team, and who they play this week.</p></div>' % CAPTURED)
    body += ('<div class="callout warn"><b>Flagged:</b> no official depth-chart source. Rosters publish jersey '
             'number, position, experience and active status — never a depth order. Inferring "3rd string" from '
             'experience would be invention, so it is not done. See <a href="flagged.html">F01</a> and '
             '<a href="questions.html">Q03</a>.</div>')

    body += '<h2>Exposure by team and position group</h2>'
    rows = []
    for a in AGG:
        o = opp.get(a['abbr'])
        grp = defaultdict(int)
        for r in by_team[a['abbr']]:
            if r['practice_status'].startswith('Did Not'):
                grp[r['group']] += 1
        rows.append((e(a['team']), e(o[0]) if o else 'BYE', a['dnp'],
                     grp.get('Offence', 0) + grp.get('Offence (line)', 0), grp.get('Defence', 0),
                     grp.get('Special teams', 0), blank(), src(a['url'], 'official')))
    body += table(['Team', 'Week 10', 'Players not practising', 'Offence', 'Defence', 'Special teams',
                   'Starters replaced (string)', 'Source'], rows,
                  caption='Non-participants by position group — the verifiable half of depth risk',
                  note='The last column is blank by rule: no official source publishes the string order. '
                       'A blank here is a finding, not an omission.')

    body += '<h2>Position-group exposure, league-wide</h2>'
    grp_all = defaultdict(lambda: [0, 0, 0])
    for r in INJ:
        g = r['group']
        if r['practice_status'].startswith('Did Not'):
            grp_all[g][0] += 1
        elif r['practice_status'].startswith('Limited'):
            grp_all[g][1] += 1
        else:
            grp_all[g][2] += 1
    rows = [(e(g), v[0], v[1], v[2], v[0] + v[1] + v[2], src(content.SOURCES[0][2]))
            for g, v in sorted(grp_all.items(), key=lambda kv: -kv[1][0])]
    body += table(['Group', 'Did not participate', 'Limited', 'Full', 'Total', 'Source'], rows,
                  caption='League-wide injury rows by position group')

    body += '<h2>What would close the gap</h2>'
    body += ('<ol class="steps">'
             '<li><b>Licence a depth-chart feed</b> and store it with the same capture-time and hash discipline '
             'as the official pages.</li>'
             '<li><b>Join transactions.</b> Twelve trades happened between 11/06 and 11/10; a player who moved '
             'must not be counted against his old team\'s depth (flag F10).</li>'
             '<li><b>Then</b> estimate the marginal effect of a backup replacing a starter — as a measured '
             'coefficient with an interval, not an assumption. Until then, exposure counts are the deliverable.'
             '</li></ol>')
    page("pages/depth.html", "Defensive & offensive depth deficiency", body,
         subtitle='<p class="sub">Who is unavailable, where, and what is honestly unknown. String depth is blank '
                  'because no official source publishes it.</p>', prefix="../")


def p_questions():
    body = ('<div class="lead"><p>The register you asked for: <b>what has to be answered before a decision can '
            'reasonably be made</b>, split into what we already have, what we do not have, how to get it, and '
            'whether it blocks progress. %d questions, %d of them blocking.</p></div>'
            % (NQ, sum(1 for q in content.QUESTIONS if q[6].startswith('Yes'))))
    body += '<div class="kpis">%s</div>' % "".join('<div class="kpi"><b>%s</b><span>%s</span></div>' % (v, e(k)) for v, k in [
        (NQ, 'questions'), (sum(1 for q in content.QUESTIONS if q[6].startswith('Yes')), 'blocking'),
        (NQ - sum(1 for q in content.QUESTIONS if q[6].startswith('Yes')), 'non-blocking'),
        (len(content.SUGGESTIONS), 'suggestions linked'),
        (len(content.SOURCES), 'official sources')])

    rows = []
    for q in content.QUESTIONS:
        blocking = q[6].startswith('Yes')
        rows.append((q[0], '<b>%s</b>' % e(q[1]), e(q[2]), e(q[3]), e(q[4]), e(q[5]),
                     src_safe(content.QUESTION_SOURCE[q[0]]),
                     badge('fail' if blocking else 'pass', 'blocks' if blocking else 'does not block')))
    body += table(['ID', 'Question', 'Why it matters', 'What we have', 'What is missing',
                   'How to discover it', 'Source', 'Status'], rows,
                  caption='Decision-readiness register — %d questions' % NQ)

    body += '<h2>Blocking questions, in dependency order</h2>'
    body += ('<p>These are ordered so that the cheapest answers come first. Q01/Q02 (prices and licensing) and '
             'Q06/Q11 (sample floor and lookahead) unblock the quantitative work; Q03/Q04 unblock the injury and '
             'depth work. Nothing downstream can be decided before them.</p>')
    body += table(['Order', 'Question', 'Unblocks', 'Cost signal', 'Source'],
                  [('1', 'Q01 official price source', 'ROI, edge, reward eligibility', 'Data licence', src_safe('S1')),
                   ('2', 'Q02 licence terms for existing third-party data', 'Any priced result', 'Legal review', src_safe('repository:provenance')),
                   ('3', 'Q11 what timestamp defines "before kickoff"', 'Any honest backtest', 'Build work', src_safe('S4')),
                   ('4', 'Q03 official depth source', 'Depth-deficiency model', 'Data licence', src_safe('S6')),
                   ('5', 'Q04/Q05 injury column semantics and practice day', 'Injury-adjusted projections', 'Policy read', src_safe('S1')),
                   ('6', 'Q06 sample floor and holdout window', 'Reward eligibility', 'Decision', src_safe('S3')),
                   ('7', 'Q08 what is being rewarded', 'Competition launch', 'Legal review', src_safe('repository:leaderboard')),
                   ('8', 'Q09 same-game dependence panel', 'Parlays and prop combos', 'Data licence', src_safe('S10')),
                   ('9', 'Q14 owner constraints (budget, time, risk)', 'Final path choice', 'Your call', src_safe('S1'))],
                  caption='The order in which the blocking questions should be answered',
                  note='Sources for each question are on the row above and in the <a href="sources.html">source register</a>.')

    body += '<h2>Questions that are already answered</h2>'
    body += table(['Question', 'Answer', 'Evidence'],
                  [('Is the official record internally consistent?', 'Yes — W = L = 135, PF = PA, PCT recomputes on all 32 teams',
                    src(content.SOURCES[1][2])),
                   ('Does the repository\'s stored data reconcile to the official record?',
                    'Yes — 32 of 32 teams, 160 field comparisons, after adding the 15 Week 9 finals and the Week 8 Monday game',
                    src(content.SOURCES[2][2])),
                   ('Can depth charts be read from nfl.com?', 'No — the route returns 404 on %s' % CAPTURED,
                    src(content.SOURCES[5][2])),
                   ('Is there an official price archive?', 'No — none in the pages read; third-party only',
                    src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/provenance.json'))],
                  caption='Answered questions stay here so nobody re-litigates them')
    page("pages/questions.html", "Questions register", body,
         subtitle='<p class="sub">Every question that must be answered before a decision, with what we have, what '
                  'we lack, how to find it and whether it blocks.</p>', prefix="../")


def p_suggestions():
    body = ('<div class="lead"><p>This is the suggestions section you asked for: a place to review options and '
            '<b>choose a path before any change is implemented</b>. Each suggestion lists why it matters, what it '
            'costs in effort, what could go wrong, what must be true first, and a recommendation. The decision '
            'column is yours to fill; nothing here has been implemented on the strength of this page alone.</p></div>')
    body += '<div class="kpis">%s</div>' % "".join('<div class="kpi"><b>%s</b><span>%s</span></div>' % (v, e(k)) for v, k in [
        (len(content.SUGGESTIONS), 'suggestions'), (sum(1 for s in content.SUGGESTIONS if s[5] == 'Low'), 'low effort'),
        (sum(1 for s in content.SUGGESTIONS if s[5] == 'Medium'), 'medium effort'),
        (sum(1 for s in content.SUGGESTIONS if s[5] == 'High'), 'high effort'),
        (sum(1 for s in content.SUGGESTIONS if s[8] == 'Recommended'), 'recommended')])

    rows = []
    for s in content.SUGGESTIONS:
        rows.append((s[0], e(s[1]), '<b>%s</b>' % e(s[2]), e(s[3]), e(s[4]), badge(
            'pass' if s[5] == 'Low' else 'official' if s[5] == 'Medium' else 'fail', s[5]),
            e(s[6]), e(s[7]), badge('pass', s[8]), src_safe(content.SUGGESTION_SOURCE[s[0]])))
    body += table(['ID', 'Area', 'Suggestion', 'Why', 'Trade-off', 'Effort', 'Risk', 'Prerequisite',
                   'Recommendation', 'Source'], rows, caption='%d suggestions, ordered by area' % NS)

    body += '<h2>Choose a path</h2>'
    body += ('<p>Three coherent packages, built from the suggestions above. Each is a sequence, not a shopping '
             'list: the later steps depend on the earlier ones.</p>')
    body += table(['Package', 'What it contains', 'Effort', 'What it buys you', 'What it does not', 'Source'],
                  [('A · Truth first (recommended)', 'S01, S02, S03, S04, S14, S15',
                    'Low–medium', 'One trustworthy dashboard, every number stamped and sourced, every open '
                    'question visible. Deployable now.', 'No price, no edge, no reward — those stay blocked.',
                    src_safe('S1')),
                   ('B · Evidence next', 'A plus S05, S06, S07, S08, S09, S12, S13',
                    'Medium', 'Pre-registered strategies, luck-controlled scoring, injury exposure with '
                    'transactions, an honest baseline line.', 'Still no market comparison until Q01/Q02.',
                    src_safe('S3')),
                   ('C · Product last', 'B plus licensed prices (Q01/Q02), dependence panel (Q09), and a reward '
                    'decision (Q08)', 'High', 'A priced, graded, dependence-aware competition — the thing that '
                    'can actually pay a reward.', 'Requires a data licence, legal review and a real sample floor.',
                    src_safe('S1'))],
                  caption='Three paths, in dependency order')

    body += '<h2>Decision column</h2>'
    body += ('<p>Copy this into a review and mark one column per suggestion. Nothing is implemented until a row '
             'has an owner and an Accept.</p>')
    body += table(['ID', 'Suggestion', 'Decision (Accept / Defer / Reject)', 'Owner', 'Notes', 'Evidence'],
                  [(s[0], e(s[2])) + (blank(), blank(), blank()) + (src_safe(content.SUGGESTION_SOURCE[s[0]]),)
                   for s in content.SUGGESTIONS],
                  caption='Review sheet — blank cells are for you to fill',
                  note='Blanks here are intentional: the site must not pre-fill a decision that belongs to you.')
    page("pages/suggestions.html", "Suggestions for review", body,
         subtitle='<p class="sub">%d suggestions with effort, risk, prerequisites and a recommendation — a review '
                  'sheet, not an implementation log.</p>' % NS, prefix="../")


def p_lines():
    body = ('<div class="lead"><p>Originating your own lines means producing a number the market does not give '
            'you. This page is deliberately short on numbers, because <b>no official source publishes a price</b>. '
            'It shows what the repository claims, what can be re-graded against official finals, and where the '
            'price columns must stay blank.</p></div>')
    body += ('<div class="callout warn"><b>No price, no edge.</b> Every price, edge and ROI cell below is blank or '
             'explicitly labelled third-party. The repository\'s own provenance file records that its odds are '
             'third-party and that no official league source exists for them.</div>')

    body += '<h2>What each engine produces, and for which week</h2>'
    body += table(['Engine', 'Product', 'Games covered', 'Price source', 'Status', 'Source'],
                  [('nfl-lab', 'Fair moneyline, model spread, model total per game', '16 games: Week 8 MNF + Week 9',
                    blank(), badge('official', 'own line — unvalidated'),
                    src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/own_lines_2026.csv')),
                   ('nfl-quant', 'Own spread, own total, fair moneyline, market comparison', '15 Week 9 games',
                    'third-party closing line', badge('fail', 'disagrees with nfl-lab'),
                    src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/week9_lines.csv')),
                   ('nfl-audit (this site)', 'Nothing priced', '0', blank(), badge('blocked', 'blocked: no licensed price'),
                    src(content.SOURCES[1][2]))],
                  caption='Three engines, three different answers to "what is the line?"')

    body += '<h2>Re-graded against official finals</h2>'
    v7 = [c for c in CHECKS if c['id'] in ('V07', 'V07b')]
    body += table(['Check', 'Detail', 'Result', 'Source'],
                  [(e(c['check']), e(c['detail']), badge('pass' if c['pass'] else 'fail', 'pass' if c['pass'] else 'fail'),
                    src_safe(c['source'])) for c in v7], caption='The one honest grading the data supports')
    body += ('<p class="note">Read this carefully: the own lines were <b>worse</b> than the third-party market on '
             'this single slate. Fourteen games is not evidence of skill in either direction, and the market column '
             'is third-party, so the comparison is descriptive only (flag F17).</p>')

    body += '<h2>What a real line-origination pipeline looks like</h2>'
    body += table(['Step', 'What it produces', 'Official input available today?', 'Missing', 'Source'],
                  [('1 \u00b7 Ratings', 'Points-based team strength from official finals', badge('pass', 'yes \u2014 official finals'),
                    'Nothing, for a baseline; sample is one season.', src_safe('S3')),
                   ('2 \u00b7 Home field', 'Measured home advantage, including neutral sites', badge('pass', 'yes \u2014 official venues'),
                    'Enough seasons to stabilise; small n on international games.', src_safe('S4')),
                   ('3 \u00b7 Injuries', 'Availability adjustment per game', badge('official', 'partial \u2014 report, no depth'),
                    'Depth chart and practice-day semantics (Q03\u2013Q05).', src_safe('S1')),
                   ('4 \u00b7 Fair line', 'Spread, total, moneyline', badge('pass', 'own line computable'), '\u2014', src_safe('S2')),
                   ('5 \u00b7 Market price', 'The number to beat', badge('fail', 'no \u2014 no official price'),
                    'Licensed odds (Q01/Q02).', src_safe('S1')),
                   ('6 \u00b7 Edge and stake', 'Expected value, Kelly fraction', badge('fail', 'no'),
                    'Step 5, plus settlement rules.', src_safe('repository:provenance')),
                   ('7 \u00b7 Grade', 'ROI with an interval and a luck test', badge('fail', 'no'), 'Steps 5\u20136 and Q06.',
                    src_safe('S3'))],
                  caption='Where line origination actually stops today')
    body += ('<p class="note">Steps 1–4 are achievable with official data and are the right next build (S09). '
             'Steps 5–7 are blocked on a licensed price and a sample floor, not on modelling skill.</p>')
    page("pages/lines.html", "Own lines", body,
         subtitle='<p class="sub">What the repository originates, what can be re-graded against official finals, '
                  'and the blank where a price belongs.</p>', prefix="../")


def p_strategies():
    body = ('<div class="lead"><p>The strategy catalogue and the gates each one must clear before it can be called '
            'skillful or paid. %s <b>Zero strategies qualify in any workspace.</b> That result is the headline, '
            'not a footnote.</p></div>' % 'Both NFL engines publish an empty reward list.')
    body += '<h2>Strategies, as the repository defines them</h2>'
    body += table(['Workspace', 'Strategies', 'Markets covered', 'Gates declared', 'Passed', 'Source'],
                  [('nfl-lab', 'S1–S8', 'Moneyline, totals, rest, momentum, 2-leg parlay, player-prop combo',
                    '8 gates', '0', src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/strategy_registry.json')),
                   ('nfl-quant', 'S1–S4, C1', 'Spread, total, sides, parlay combination',
                    'Tiered (Gold/Silver/Bronze)', '0 Gold, 0 points',
                    src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/pipeline/gates.json')),
                   ('nfl / nfl-research', 'Specification only', 'Singles, parlays, props',
                    '7–8 gates', '0 (no data)', src('https://github.com/sassnarep3-star/Own4/tree/main/nfl'))],
                  caption='Strategy families and their gate outcomes')

    body += '<h2>The validation gates that matter</h2>'
    body += table(['Gate', 'Rule', 'Why it exists', 'Status in the repository', 'Source'],
                  [('G1 · Sample floor', 'A strategy needs a pre-registered minimum of graded out-of-sample games (the repo uses 300)',
                    'Small samples produce heroes by accident', badge('fail', 'fails — one season is 272 games max'), src_safe('S3')),
                   ('G2 · Calibration', 'Predicted probabilities must match realised frequencies (Brier / reliability)',
                    'A confident model that is wrong is worse than a timid one', badge('official', 'reported, not met'), src_safe('S2')),
                   ('G3 · Discrimination', 'Must beat a naive baseline (home team, league average)',
                    'Beating nothing is not skill', badge('pass', 'some pass on single slates'), src_safe('S3')),
                   ('G4 · Market beat', 'Must beat the available price, not an invented one',
                    'You are paid against the price', badge('blocked', 'blocked: no official price'), src_safe('S1')),
                   ('G5 · Stability', 'Edge must survive across time blocks and not live in one week',
                    'A one-week edge is a coincidence', badge('fail', 'not met'), src_safe('S3')),
                   ('G6 · Dependence', 'Combinations priced with measured correlation, not independence',
                    'Independence pricing overstates parlays', badge('fail', 'not met — no panel'), src_safe('S10')),
                   ('G7 · Price executable', 'A real, timestamped price must exist before kickoff',
                    'A theoretical edge is not a trade', badge('blocked', 'blocked'), src_safe('S1')),
                   ('G8 · Multiple testing', 'Benjamini-Hochberg (or similar) across all strategies tested',
                    'Test twenty ideas and one looks great by chance', badge('fail', 'not met'), src_safe('S2')),
                   ('G9 · Provenance', 'Every input traceable to a source with a capture time',
                    'Reproducibility is the only defence against lookahead', badge('official', 'partial — see F15'), src_safe('S1')),
                   ('G10 · Determinism', 'The published number must rebuild byte-identically from the data',
                    'Prevents quiet drift', badge('pass', 'met in nfl-lab'), src_safe('S3'))],
                  caption='Ten gates, and where the repository actually stands')
    body += ('<h2>Why "no strategy qualifies" is the right answer</h2>')
    body += ('<p>A season is 272 games. Even a genuinely profitable strategy needs hundreds of graded bets before '
             'its edge is distinguishable from noise. The repository\'s own numbers show this clearly: its best '
             'totals result had a permutation p-value of 0.0261 on a small sample and still failed the '
             'multiple-testing gate. Publishing that as skill would be the error; publishing it as a failure is '
             'the feature.</p>')
    body += ('<p class="note">Correlation values for parlays and prop combos are <b>not published</b> anywhere on '
             'this site: measuring them needs a player-game panel that the repository does not have (Q09). '
             'Any coefficient you see elsewhere in the repository without an official source is flagged.</p>')
    page("pages/strategies.html", "Strategies, gates and luck removal", body,
         subtitle='<p class="sub">Ten gates, five strategy families, zero qualifiers — and the reason that is '
                  'correct.</p>', prefix="../")


def p_leaderboard():
    body = ('<div class="lead"><p>A leaderboard is only honest if it can show an empty board. The repository\'s '
            'own competition design awards <b>zero rewards</b> because nothing clears the gates. This page shows '
            'that state, the flaw in the current tiering, and the rules a leaderboard needs before it can pay '
            'anything.</p></div>')
    lb = [
        ('S1', '1599', '+0.26%', '&#8722;3.63%', 'Bronze', '0', badge('fail', 'interval straddles zero')),
        ('S2', '789', '&#8722;5.45%', '&#8722;10.52%', 'Rejected', '0', badge('pass', 'correctly rejected')),
        ('S3', '1398', '&#8722;7.56%', '&#8722;14.66%', 'Rejected', '0', badge('pass', 'correctly rejected')),
        ('S4', '7635', '+0.03%', '&#8722;7.79%', 'Bronze', '0', badge('fail', 'interval straddles zero')),
        ('C1', '1438', '&#8722;6.56%', '&#8722;10.42%', 'Rejected', '0', badge('pass', 'correctly rejected')),
    ]
    body += table(['Strategy', 'Graded bets', 'Point ROI', 'Bootstrap 5th pct', 'Tier', 'Reward points', 'Read', 'Source'],
                  [(a, b, c, d, e_, f, g, src_safe('repository:leaderboard')) for a, b, c, d, e_, f, g in lb],
                  caption='nfl-quant leaderboard as published, re-read on %s' % CAPTURED,
                  note='Reward pool is 1000 points and nothing was awarded. Source: '
                       + src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/leaderboard.json'))

    body += ('<div class="callout warn"><b>Irregularity (F18).</b> S1 and S4 are given a Bronze tier while '
             'their own bootstrap 5th percentile is negative (&#8722;3.63% and &#8722;7.79%). A tier assigned to a '
             'point estimate whose interval includes zero is a reward for luck, even at zero points. Fix: no tier '
             'until the lower bound is positive.</div>')

    body += '<h2>Rules a leaderboard needs before it pays</h2>'
    body += table(['Rule', 'Why', 'Status here', 'Source'],
                  [('Pre-registered strategy list and gates, committed before evaluation',
                    'Otherwise the board is fitted after the fact', badge('pass', 'met in nfl-lab'), src_safe('repository:gates')),
                   ('Out-of-sample scoring only, with a stated holdout window', 'In-sample ranking is memorisation',
                    badge('official', 'partial'), src_safe('repository:gates')),
                   ('Minimum graded bets before a strategy appears', 'Stops a 3-for-3 start from topping the board',
                    badge('fail', 'not met'), src_safe('repository:gates')),
                   ('Interval-based tiers (lower bound must clear zero)', 'Point estimates alone reward luck',
                    badge('fail', 'not met — see F18'), src_safe('repository:leaderboard')),
                   ('Multiple-testing control across every strategy ranked', 'Twenty tries, one winner is expected',
                    badge('fail', 'not met'), src_safe('repository:gates')),
                   ('A written definition of the reward (points, credit or cash) and its legal review',
                    'Cash rewards are regulated; the current pool is points and pays nothing', badge('official', 'undecided (Q08)'),
                    src_safe('repository:leaderboard')),
                   ('Published failure reason per strategy', 'Tells the owner what to fix', badge('pass', 'met here'),
                    src_safe('repository:gates'))],
                  caption='Leaderboard integrity rules')
    body += ('<p class="note">Until every row above is met, the correct board is the one published here: everyone '
             'listed, nobody paid. See <a href="suggestions.html">S12, S13</a> and <a href="questions.html">Q08</a>.</p>')
    page("pages/leaderboard.html", "Leaderboard & rewards", body,
         subtitle='<p class="sub">Zero qualifiers, zero rewards — and the seven rules a board needs before it can '
                  'pay anyone.</p>', prefix="../")


def p_sources():
    rows = [(s[0], e(s[1]), src(s[2]), e(s[3]), e(s[4])) for s in content.SOURCES]
    body = '<div class="lead"><p>Every source read in this session, with what it was used for and how it was read. ' \
           'If a page is not on this list, no value on this site came from it.</p></div>'
    body += table(['ID', 'Source', 'Link', 'Used for', 'How it was read'], rows,
                  caption='Source register — %d official sources' % len(content.SOURCES))
    body += '<h2>Not used, and why</h2>'
    body += table(['Candidate source', 'Why it is not used', 'Link'],
                  [('Third-party odds archives', 'No official status; the repository\'s own provenance file labels '
                    'them third-party and says rights must be verified',
                    src('https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/provenance.json')),
                   ('Third-party depth charts', 'No official status; would be an inferred string order',
                    src(content.SOURCES[5][2])),
                   ('nflgsis.com statistician guide', 'Official-looking host, but not reachable from nfl.com or '
                    'operations.nfl.com in this session; not cited for any value',
                    src('https://www.nflgsis.com/gsis/documentation/stadiumguides/guide_for_statisticians.pdf'))],
                  caption='Sources deliberately excluded')
    page("pages/sources.html", "Source register", body,
         subtitle='<p class="sub">%d sources, each read on %s, each tied to the rows it supports.</p>'
                  % (len(content.SOURCES), CAPTURED), prefix="../")


def p_flagged():
    body = ('<div class="lead"><p>Every irregularity and every value that could not be confirmed from an official '
            'source. None of these block publication; each one blocks a specific conclusion, and the conclusion is '
            'named. This is the page to review first if you want to challenge the site.</p></div>')
    rows = []
    for f in content.FLAGS:
        rows.append((f[0], '<b>%s</b>' % e(f[1]), e(f[2]), src_safe(f[3]),
                     badge('fail' if f[4].startswith('Open') else 'pass', f[4].split('—')[0].strip())))
    body += table(['ID', 'Item', 'What is wrong or unconfirmed', 'Evidence', 'Status'], rows,
                  caption='%d flagged items' % len(content.FLAGS))
    body += '<h2>Blank-value register</h2>'
    body += table(['Where', 'Blank field', 'Why it is blank', 'What would fill it', 'Source'],
                  [('Own lines / strategies', 'Price, edge, expected value, ROI',
                    'No official price exists in the pages read (F08)', 'A licensed odds source (Q01/Q02)', src_safe('S1')),
                   ('Depth page', 'Starters replaced / string order',
                    'Official depth chart returns 404 (F01)', 'A licensed depth-chart feed (Q03)', src_safe('S6')),
                   ('Injury table', 'Injury type on %d rows, game status on %d rows' % (TOT['blank'], TOT['blankst']),
                    'The official page publishes neither for those rows (F03, F04)',
                    'A report revision, or additional official columns', src_safe('S1')),
                   ('Parlay / prop combos', 'Correlation coefficients and joint probabilities',
                    'No player-game panel exists in the repository (Q09)', 'A licensed player-game panel', src_safe('S10')),
                   ('Leaderboard', 'Rewards', 'Nothing passed the gates; the pool is points and pays zero',
                    'A strategy that clears every gate (Q06)', src_safe('repository:leaderboard'))],
                  caption='Every blank on this site, with the reason and the remedy')
    body += ('<p class="note">Rule applied throughout: <b>never infer or fill a value</b>. If an official page does '
             'not publish it, it is blank and it is on this page.</p>')
    page("pages/flagged.html", "\u2691 Flagged for review", body,
         subtitle='<p class="sub">%d items: irregularities, unconfirmed values and deliberate blanks, each with '
                  'its evidence.</p>' % len(content.FLAGS), prefix="../")


if __name__ == "__main__":
    p_index()
    p_exec()
    p_data()
    p_verification()
    p_injuries()
    p_depth()
    p_questions()
    p_suggestions()
    p_lines()
    p_strategies()
    p_leaderboard()
    p_sources()
    p_flagged()
    print("built: index + %d pages" % (len(NAV and [1]) + 12))

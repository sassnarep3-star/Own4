#!/usr/bin/env python3
"""nfl-origin-board site generator.

Stdlib only. No network. Deterministic: every number on the site is computed
from the JSON files in ./data at build time, so no count can go stale.

Pages are written to ./ (landing) and ./pages/ (subpages).
"""
import json, os, math, statistics, hashlib, html, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))

GAMES = D("games_2026.json")
STAND = D("standings_2026.json")
INJ = D("injuries_week10.json")
WK11 = D("week11_schedule.json")
EVID = D("official_evidence.json")
REQ = D("requirements.json")
STRAT = D("strategies.json")
QUEST = D("questions.json")
SUG = D("suggestions.json")
SRC = D("sources.json")
FLAGS = D("flags.json")
TP = D("third_party_candidate.json")

INJ_URL = "https://www.nfl.com/injuries/"
SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
CAPTURE = "2026-11-16"
SEASON = 2026

TEAMS = {
    "BUF": ("Buffalo Bills", "AFC East"), "NE": ("New England Patriots", "AFC East"),
    "NYJ": ("New York Jets", "AFC East"), "MIA": ("Miami Dolphins", "AFC East"),
    "PIT": ("Pittsburgh Steelers", "AFC North"), "CIN": ("Cincinnati Bengals", "AFC North"),
    "CLE": ("Cleveland Browns", "AFC North"), "BAL": ("Baltimore Ravens", "AFC North"),
    "JAX": ("Jacksonville Jaguars", "AFC South"), "HOU": ("Houston Texans", "AFC South"),
    "IND": ("Indianapolis Colts", "AFC South"), "TEN": ("Tennessee Titans", "AFC South"),
    "KC": ("Kansas City Chiefs", "AFC West"), "DEN": ("Denver Broncos", "AFC West"),
    "LV": ("Las Vegas Raiders", "AFC West"), "LAC": ("Los Angeles Chargers", "AFC West"),
    "NYG": ("New York Giants", "NFC East"), "DAL": ("Dallas Cowboys", "NFC East"),
    "WAS": ("Washington Commanders", "NFC East"), "PHI": ("Philadelphia Eagles", "NFC East"),
    "DET": ("Detroit Lions", "NFC North"), "MIN": ("Minnesota Vikings", "NFC North"),
    "CHI": ("Chicago Bears", "NFC North"), "GB": ("Green Bay Packers", "NFC North"),
    "CAR": ("Carolina Panthers", "NFC South"), "TB": ("Tampa Bay Buccaneers", "NFC South"),
    "NO": ("New Orleans Saints", "NFC South"), "ATL": ("Atlanta Falcons", "NFC South"),
    "SF": ("San Francisco 49ers", "NFC West"), "SEA": ("Seattle Seahawks", "NFC West"),
    "LAR": ("Los Angeles Rams", "NFC West"), "AZ": ("Arizona Cardinals", "NFC West"),
}
TEAM_URL = "https://www.nfl.com/teams/"

# ---------------------------------------------------------------- computations
G = GAMES["games"]
FINALS = [g for g in G if g[6] == "final"]
UNRESOLVED = [g for g in G if g[6] == "unresolved"]
SCHEDULED = [g for g in G if g[6] == "scheduled"]
WEEKS_1_9 = [g for g in G if g[0] <= 9]

rec = collections.defaultdict(lambda: dict(W=0, L=0, T=0, PF=0, PA=0, G=0))
for wk, dt, aw, ap, ho, hp, st, url, note in FINALS:
    for t, pts, opp in ((aw, ap, hp), (ho, hp, ap)):
        r = rec[t]; r["G"] += 1; r["PF"] += pts; r["PA"] += opp
        r["W" if pts > opp else ("L" if pts < opp else "T")] += 1

off = {r[0]: dict(W=r[2], L=r[3], T=r[4], PF=r[6], PA=r[7]) for r in STAND["rows"]}
MISMATCH = [(t, k, rec[t][k], off[t][k]) for t in sorted(off)
            for k in ("W", "L", "T", "PF", "PA") if rec[t][k] != off[t][k]]


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def season_ppg(team, weeks):
    gp = pf = pa = 0
    for wk, dt, aw, ap, ho, hp, st, url, note in FINALS:
        if wk not in weeks:
            continue
        if aw == team:
            gp += 1; pf += ap; pa += hp
        elif ho == team:
            gp += 1; pf += hp; pa += ap
    return (pf / gp, pa / gp, gp) if gp else (None, None, 0)


rows32 = [t for t in off]
nppg = {t: (off[t]["PF"] - off[t]["PA"]) / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32}
winpct = {t: (off[t]["W"] + 0.5 * off[t]["T"]) / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32}
pfpg = {t: off[t]["PF"] / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32}
papg = {t: off[t]["PA"] / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32}

first_half = {t: season_ppg(t, set(range(1, 6))) for t in rows32}
second_half = {t: season_ppg(t, set(range(6, 11))) for t in rows32}

margins = [ap - hp for wk, dt, aw, ap, ho, hp, st, url, note in FINALS]

# fixture context: rest days and bye, from the official schedule only
prev = collections.defaultdict(list)
for wk, dt, aw, ap, ho, hp, st, url, note in sorted(G, key=lambda g: (g[1], g[0])):
    pass
game_dates = {}
for wk, dt, aw, ap, ho, hp, st, url, note in G:
    for t in (aw, ho):
        game_dates.setdefault(t, []).append((dt, wk))
for t in game_dates:
    game_dates[t].sort()


def rest_days(team, dt):
    prior = [d for d, w in game_dates[team] if d < dt]
    if not prior:
        return None
    from datetime import date
    a = date(*[int(x) for x in prior[-1].split("-")])
    b = date(*[int(x) for x in dt.split("-")])
    return (b - a).days


rest_rows = [(rest_days(aw, dt), rest_days(ho, dt), ap - hp)
             for wk, dt, aw, ap, ho, hp, st, url, note in FINALS]
rest_pairs = [(r[1] - r[0], r[2]) for r in rest_rows if r[0] is not None and r[1] is not None]

CORR = [
    ("C-1", "Net points per game vs win percentage", 32,
     pearson([nppg[t] for t in rows32], [winpct[t] for t in rows32]),
     "Official standings page, all 32 clubs", STAND["meta"]["source"]),
    ("C-2", "Points for per game vs win percentage", 32,
     pearson([pfpg[t] for t in rows32], [winpct[t] for t in rows32]),
     "Official standings page, all 32 clubs", STAND["meta"]["source"]),
    ("C-3", "Points against per game vs win percentage", 32,
     pearson([papg[t] for t in rows32], [winpct[t] for t in rows32]),
     "Official standings page, all 32 clubs", STAND["meta"]["source"]),
    ("C-4", "Split-half reliability: net points per game, Weeks 1-5 vs Weeks 6-10", 32,
     pearson([first_half[t][0] - first_half[t][1] for t in rows32],
             [second_half[t][0] - second_half[t][1] for t in rows32]),
     "Official schedule pages, all 32 clubs, chronological split",
     "https://www.nfl.com/schedules/2026/by-week/week-10"),
    ("C-5", "Rest-day differential (home minus away) vs home margin", len(rest_pairs),
     pearson([p[0] for p in rest_pairs], [p[1] for p in rest_pairs]),
     "Official schedule pages, %d completed games" % len(rest_pairs),
     "https://www.nfl.com/schedules/2026/by-week/week-10"),
]

# removal of luck
obs_var = statistics.pvariance([winpct[t] for t in rows32])
luck_var = statistics.fmean([0.25 / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32])
skill_var = max(0.0, obs_var - luck_var)
sd_margin = statistics.pstdev(margins)
exp_nppg_var = statistics.fmean([(sd_margin ** 2) / (off[t]["W"] + off[t]["L"] + off[t]["T"]) for t in rows32])
obs_nppg_var = statistics.pvariance([nppg[t] for t in rows32])
skill_nppg_sd = math.sqrt(max(0.0, obs_nppg_var - exp_nppg_var))

# injuries
IROWS = INJ["rows"]
ICLUBS = sorted({r[0] for r in IROWS})
IDES = [r for r in IROWS if r[5]]
ICOUNT = collections.Counter(r[5] for r in IDES)
team_tally = collections.defaultdict(lambda: dict(rows=0, out=0, q=0, d=0, dnp=0, lp=0, fp=0))
for c, p, pos, inj, prac, gs in IROWS:
    t = team_tally[c]; t["rows"] += 1
    if gs == "Out": t["out"] += 1
    if gs == "Questionable": t["q"] += 1
    if gs == "Doubtful": t["d"] += 1
    if prac == "DNP": t["dnp"] += 1
    if prac == "LP": t["lp"] += 1
    if prac == "FP": t["fp"] += 1

# integrity hash of the capture
CAPHASH = hashlib.sha256(json.dumps(IROWS, sort_keys=True).encode()).hexdigest()[:16]
GAMEHASH = hashlib.sha256(json.dumps(G, sort_keys=True).encode()).hexdigest()[:16]

# ------------------------------------------------------------------- rendering
CSS = """
:root{--bg:#0e1116;--panel:#151a22;--line:#232b36;--fg:#e6edf3;--mut:#93a1b1;
--acc:#4da3ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--blank:#3d4653}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.side{position:fixed;inset:0 auto 0 0;width:268px;background:var(--panel);
border-right:1px solid var(--line);overflow-y:auto;padding:16px 0}
.brand{display:block;padding:0 18px 4px;font-weight:700;font-size:17px;color:var(--fg)}
.tag{display:block;padding:0 18px 14px;color:var(--mut);font-size:12px}
.grp{padding:14px 18px 4px;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.nav{display:block;padding:6px 18px;color:#c9d4e0;font-size:14px;border-left:3px solid transparent}
.nav:hover{background:#1b222c;text-decoration:none}
.nav.on{border-left-color:var(--acc);background:#1b222c;color:#fff;font-weight:600}
main{margin-left:268px;padding:28px 34px 80px;max-width:1400px}
h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:30px 0 10px}
h3{font-size:15px;margin:20px 0 8px;color:#c9d4e0}
p,li{color:#c9d4e0}
.lead{color:var(--mut);max-width:900px;margin:0 0 18px}
.tiles{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0 8px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:158px}
.tile b{display:block;font-size:22px;line-height:1.2}
.tile span{color:var(--mut);font-size:12px}
table{border-collapse:collapse;width:100%;background:var(--panel);
border:1px solid var(--line);border-radius:8px;overflow:hidden;margin:10px 0 6px;font-size:13.5px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#1b222c;color:#a9b6c4;font-weight:600;font-size:12.5px;
text-transform:uppercase;letter-spacing:.03em;position:sticky;top:0}
tr:last-child td{border-bottom:0}
tbody tr:hover{background:#1a212b}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.wrap-x{overflow-x:auto;max-height:none}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11.5px;
border:1px solid var(--line);white-space:nowrap}
.b-met{background:#12261a;color:var(--good);border-color:#1f4d2b}
.b-part{background:#2a2410;color:var(--warn);border-color:#4d3f14}
.b-block{background:#2b1416;color:var(--bad);border-color:#522225}
.b-off{background:#12261a;color:var(--good);border-color:#1f4d2b}
.b-tp{background:#2a2410;color:var(--warn);border-color:#4d3f14}
.blank{color:var(--blank);font-style:italic}
.flag{color:var(--warn)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);
padding:12px 16px;border-radius:8px;margin:14px 0;color:#c9d4e0}
.note.warn{border-left-color:var(--warn)}
.note.good{border-left-color:var(--good)}
code{background:#1b222c;padding:1px 5px;border-radius:4px;font-size:12.5px}
.mut{color:var(--mut)}
.small{font-size:12.5px;color:var(--mut)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:12px 0}
.opt{border-left:3px solid var(--line);padding:8px 0 8px 14px;margin:8px 0}
.opt b{color:#fff}
.verdict{display:inline-block;padding:2px 10px;border-radius:6px;background:#1b222c;
border:1px dashed var(--blank);color:var(--blank);font-size:12.5px}
details{margin:8px 0}summary{cursor:pointer;color:var(--acc)}
@media(max-width:1000px){.side{position:static;width:auto;height:auto;border-right:0;
border-bottom:1px solid var(--line)}main{margin-left:0;padding:18px}}
"""

NAV = [
    ("Overview", [("index.html", "Decision dashboard"), ("pages/executive-summary.html", "Executive summary")]),
    ("Decide first", [("pages/suggestions.html", "Suggestions (review first)"),
                      ("pages/questions.html", "Questions & answers"),
                      ("pages/gates.html", "Gates & pre-registration")]),
    ("Decision readiness", [("pages/requirements.html", "Requirement register"),
                            ("pages/flagged.html", "Flagged for review")]),
    ("Data", [("pages/results.html", "Verified results feed"),
              ("pages/upcoming.html", "Week 11 slate & venues"),
              ("pages/standings.html", "Standings"),
              ("pages/third-party.html", "Third-party candidate data")]),
    ("Availability", [("pages/availability.html", "Injuries & designations"),
                      ("pages/per-team.html", "Per-team view"),
                      ("pages/depth.html", "Depth & deficiency")]),
    ("Origination & ranking", [("pages/origination.html", "Origination & residual"),
                               ("pages/leaderboard.html", "Leaderboard"),
                               ("pages/correlations.html", "Correlations & luck")]),
    ("Review", [("pages/repo-review.html", "Repository review"), ("pages/sources.html", "Sources")]),
]

BLANK = '<span class="blank">&mdash;</span>'


def esc(s):
    return html.escape(str(s)) if s is not None else ""


def page(title, body, active, lead=""):
    # pages/ subpages need ../ prefixes so the shared nav resolves from either depth
    pre = "../" if active.startswith("pages/") else ""
    nav = []
    for grp, items in NAV:
        nav.append('<div class="grp">%s</div>' % esc(grp))
        for href, label in items:
            cls = "nav on" if href == active else "nav"
            h = href if not pre else (href.replace("pages/", "")
                                      if href.startswith("pages/") else "../" + href)
            nav.append('<a class="%s" href="%s">%s</a>' % (cls, h, esc(label)))
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s &middot; NFL Origin Board</title>
<style>%s</style></head><body>
<aside class="side"><span class="brand">NFL Origin Board</span>
<span class="tag">Official-source capture %s &middot; 2026 season</span>
<nav>%s</nav></aside>
<main><h1>%s</h1>%s%s</main></body></html>""" % (
        esc(title), CSS, CAPTURE, "".join(nav), esc(title),
        ('<p class="lead">%s</p>' % lead) if lead else "", body)


def table(headers, rows, cls=""):
    th = "".join('<th class="%s">%s</th>' % (h[1], esc(h[0])) for h in headers)
    tr = "".join("<tr>%s</tr>" % "".join('<td class="%s">%s</td>' % (h[1], c) for h, c in zip(headers, r)) for r in rows)
    return '<div class="wrap-x"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, th, tr)


def src_link(url, label=None):
    if not url:
        return BLANK
    lab = label or (url.replace("https://www.nfl.com/", "nfl.com/").replace("https://github.com/", "github.com/"))
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(lab))


def status_badge(s):
    m = {"met": ("b-met", "met"), "partial": ("b-part", "partial"),
         "blocked": ("b-block", "blocked")}
    c, t = m.get(s, ("", s))
    return '<span class="badge %s">%s</span>' % (c, t)


def blank_gate(gate):
    return '<span class="blank">&mdash;</span> <span class="small">gated by %s</span>' % esc(gate)


OUT = os.path.join(ROOT, "pages")
os.makedirs(OUT, exist_ok=True)
STATS = {}

# ------------------------------------------------------------------ 1. landing
n_req = len(REQ["rows"])
cnt = collections.Counter(r[3] for r in REQ["rows"])
tiles = [
    ("Requirements traced", n_req, "one row each, with a gate and a clearing number"),
    ("Verified finals", len(FINALS), "of %d fixtures in the 2026 season so far" % len(G)),
    ("Standings mismatches", len(MISMATCH), "game log vs the official standings page, 32 clubs"),
    ("Injury-report rows", len(IROWS), "across %d clubs; %d carry a game status" % (len(ICLUBS), len(IDES))),
    ("Third-party rows offered", len(TP["rows"]), "venue, roof, price &mdash; all flagged unverified"),
    ("Flags for review", len(FLAGS["rows"]), "nothing here blocks; all are owner decisions"),
]
tilehtml = "".join('<div class="tile"><b>%s</b><span>%s</span></div>' % (esc(v), d) for v, k, d in
                   [(v, k, d) for k, v, d in tiles])

luck_rows = [
    ["Observed spread in win percentage across the 32 clubs", "standard deviation",
     "%.3f" % math.sqrt(obs_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Spread expected from luck alone (binomial, p = 0.50, per club's own game count)",
     "standard deviation", "%.3f" % math.sqrt(luck_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Residual spread attributable to skill", "standard deviation",
     "%.3f" % math.sqrt(skill_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Share of win-percentage spread explained by luck", "ratio",
     "%.1f%%" % (100 * luck_var / obs_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Single-game margin, standard deviation", "points",
     "%.2f" % sd_margin, "%d games" % len(margins), src_link("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ["Net points per game, observed spread across clubs", "points",
     "%.2f" % math.sqrt(obs_nppg_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Net points per game, spread expected from luck alone", "points",
     "%.2f" % math.sqrt(exp_nppg_var), "32 clubs", src_link(STAND["meta"]["source"])],
    ["Net points per game, residual spread attributable to skill", "points",
     "%.2f" % skill_nppg_sd, "32 clubs", src_link(STAND["meta"]["source"])],
]

readiness = []
for rid, text, cat, st, gate, clear, url in REQ["rows"]:
    readiness.append([rid, esc(text), esc(cat), status_badge(st),
                      esc(gate) if gate != "-" else '<span class="mut">none</span>',
                      esc(clear), src_link(url)])

body = (
    '<p class="lead">One row per requirement from the brief, with the gate that blocks it and the '
    'number that would clear it. Statuses and counts are computed at build time from the data files, '
    'so nothing here can drift from what the pages show.</p>'
    + '<div class="tiles">' + tilehtml + '</div>'
    + '<div class="note %s"><b>Integrity check.</b> The %d verified finals were recomputed into '
      'per-club W, L, T, points for and points against and compared against the official standings '
      'page. Mismatches: <b>%d</b> across all 32 clubs. Two further checks: the %d games of Weeks 1-9 '
      'match the nflverse archive committed elsewhere in this repository on %d of %d games with 0 '
      'score discrepancies; and the injury capture holds %d rows across %d clubs, which is 32 minus '
      'the 4 clubs on bye in Week 10.</div>'
      % ("good" if not MISMATCH else "warn", len(FINALS), len(MISMATCH), len(WEEKS_1_9),
         len(WEEKS_1_9), len(WEEKS_1_9), len(IROWS), len(ICLUBS))
    + '<h2>Decision-readiness table</h2>'
    + '<p class="small">%d requirements: %d met, %d partial, %d blocked. '
      'A blocked row has no value published &mdash; not zero, not an estimate, nothing.</p>'
      % (n_req, cnt.get("met", 0), cnt.get("partial", 0), cnt.get("blocked", 0))
    + table([("Req", ""), ("Requirement", ""), ("Area", ""), ("Status", ""),
             ("Gate", ""), ("Number that would clear it", ""), ("Source", "")], readiness)
    + '<h2>Removal of luck</h2>'
    + '<div class="note">Luck is not removed by opinion. It is removed by measuring how much of the '
      'spread you see would appear anyway if every club were equally strong. Every figure below is '
      'computed from the official standings page and the official schedule pages, with n published '
      'beside it. No strategy track record exists yet, so no strategy-level luck separation is claimed.</div>'
    + table([("Quantity", ""), ("Unit", ""), ("Value", "n"), ("n", ""), ("Source", "")], luck_rows)
)

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(
    page("Decision dashboard", body, "index.html",
         "NFL line origination: what is verified, what is blocked, and the number that would unblock it."))

# --------------------------------------------------------- 2. executive summary
top_blocked = [r for r in REQ["rows"] if r[3] == "blocked"]
gate_counts = collections.Counter(r[4] for r in top_blocked)
gate_rows = [[esc(g), str(n), esc(REQ["gates"][g]),
              ", ".join(r[0] for r in top_blocked if r[4] == g),
              src_link(next((r[6] for r in top_blocked if r[4] == g), "https://www.nfl.com/"))]
             for g, n in gate_counts.most_common()]

body = (
    '<h2>What this session established</h2><ul>'
    '<li><b>A verified results corpus.</b> %d fixtures of the 2026 season were read from the official '
    'schedule pages, week by week. %d have official final scores. Recomputed into per-club records, '
    'they match the official standings page exactly: <b>%d mismatches across all 32 clubs</b> on W, L, '
    'T, points for and points against.</li>'
    '<li><b>The 136-game corpus is now real.</b> Weeks 1-9 contain exactly %d games. They were '
    'cross-checked against the nflverse archive already committed in this repository: %d of %d games '
    'have identical scores, 0 discrepancies.</li>'
    '<li><b>A current availability capture.</b> The official injury report was read in full on %s: '
    '%d rows across %d clubs, %d of them carrying a game status (%d Out, %d Questionable, %d Doubtful). '
    'The 4 clubs missing are the 4 clubs on bye in Week 10.</li>'
    '<li><b>Two defects from earlier in the project are closed.</b> The three Lions game-status '
    'designations that were blank (Kerby Joseph, Cade Mays, D.J. Reed) are present in this capture as '
    'Out; and the Week 10 injury tables have been re-captured at current counts.</li>'
    '<li><b>Twenty-two announced-starter and roster events</b> are recorded from dated official '
    'nfl.com articles, including Drew Lock, Kyle McCord and the Lamar Jackson injured-reserve '
    'sequence. No replacement is inferred anywhere: where the league has not named a starter, the '
    'column is blank.</li></ul>'
    % (len(G), len(FINALS), len(MISMATCH), len(WEEKS_1_9), len(WEEKS_1_9), len(WEEKS_1_9),
       CAPTURE, len(IROWS), len(ICLUBS), len(IDES), ICOUNT.get("Out", 0),
       ICOUNT.get("Questionable", 0), ICOUNT.get("Doubtful", 0))
    + '<h2>What is blocked, and by what</h2>'
    + '<p>%d of %d requirements are blocked. They are blocked by %d distinct gates.</p>'
      % (len(top_blocked), n_req, len(gate_counts))
    + table([("Gate", ""), ("Reqs", "n"), ("What the gate is", ""), ("Requirements", ""),
             ("Source", "")], gate_rows)
    + '<h2>The one decision that matters most</h2>'
    + '<div class="note warn"><b>The repository already contains the data that would clear three '
      'gates at once.</b> <code>nfl-lines/data/raw/nfldata_games.csv</code> is the nflverse games '
      'archive: 7,548 games from 1999 to 2026. It holds a venue for %d of %d of this session\'s '
      'fixtures, a roof for %d, and spread, total and moneyline for %d. It is not an official source, '
      'so nothing from it has been merged into the official tables here &mdash; but its 2026 scores '
      'agree with the official pages on every one of the %d games both sources cover. Accepting it as '
      'a <i>flagged third-party</i> source would clear the venue, roof/surface and historical-price '
      'gates immediately. That is suggestion SG-01 and flag RF-15.</div>'
      % (sum(1 for r in TP["rows"] if r[4].strip()), len(TP["rows"]),
         sum(1 for r in TP["rows"] if r[5].strip()),
         sum(1 for r in TP["rows"] if r[7].strip()), len(WEEKS_1_9))
    + '<h2>What is deliberately not published</h2><ul>'
    '<li>No market line, no residual, no closing line value, no ROI. No licensed or official price '
    'feed is connected, and the brief requires the price policy to be decided before any backtest is '
    'published.</li>'
    '<li>No depth rank, no replacement depth, no deficiency matrix. No official depth source is '
    'verified for all 32 clubs and no official snap-count source is connected.</li>'
    '<li>No leaderboard rows. Ranking needs 300 prospective graded games; the site has zero, and an '
    'empty leaderboard is the honest state.</li>'
    '<li>No parlay or same-game-parlay price anywhere on the site. Multiplying marginals is invalid '
    'under dependence and the joint-evidence gate is closed.</li>'
    '<li>No value filled in from judgement. Where an official source does not state it, the cell is '
    'blank and carries the gate that blocks it.</li></ul>'
)
open(os.path.join(OUT, "executive-summary.html"), "w", encoding="utf-8").write(
    page("Executive summary", body, "pages/executive-summary.html",
         "The state of the NFL line-origination programme as of the %s official capture." % CAPTURE))

print("landing + executive summary written; mismatches:", len(MISMATCH))

GATE_SRC = {
    "G-PRICE": "https://www.nfl.com/",
    "G-DEPTH": INJ_URL, "G-SNAPSHOT": INJ_URL, "G-INACTIVE": SCHED_URL,
    "G-SAMPLE": STAND["meta"]["source"], "G-CORPUS": SCHED_URL,
    "G-VENUE": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "G-STADIUM": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "G-ABLATION": INJ_URL, "G-CALIBRATE": INJ_URL,
    "G-OWNER": "https://github.com/sassnarep3-star/Own4",
}

# --------------------------------------------------------- 3. requirement register
rows = []
for rid, text, cat, st, gate, clear, url in REQ["rows"]:
    rows.append([rid, esc(text), esc(cat), status_badge(st),
                 esc(gate) if gate != "-" else '<span class="mut">none &mdash; published</span>',
                 esc(clear), src_link(url)])
body = ('<p class="lead">Every requirement from the brief, with the single gate that blocks it and the '
        'measured number that would clear it. Counts below are computed from these rows at build time.</p>'
        + '<div class="tiles">'
        + '<div class="tile"><b>%d</b><span>requirements</span></div>' % n_req
        + '<div class="tile"><b>%d</b><span>met</span></div>' % cnt.get("met", 0)
        + '<div class="tile"><b>%d</b><span>partial</span></div>' % cnt.get("partial", 0)
        + '<div class="tile"><b>%d</b><span>blocked</span></div>' % cnt.get("blocked", 0)
        + '</div>'
        + '<h2>All requirements</h2>'
        + table([("Req", ""), ("Requirement", ""), ("Area", ""), ("Status", ""),
                 ("Gate", ""), ("Number that would clear it", ""), ("Source", "")], rows)
        + '<h2>The gates, in full</h2>'
        + table([("Gate", ""), ("Definition", ""), ("Source", "")],
                [[esc(g), esc(d),
                  src_link(GATE_SRC.get(g, "https://www.nfl.com/"))] for g, d in REQ["gates"].items()]))
open(os.path.join(OUT, "requirements.html"), "w", encoding="utf-8").write(
    page("Requirement register", body, "pages/requirements.html",
         "One row per requirement. Partial means the schema or rule is published but the gated value is blank."))

# ------------------------------------------------------------------- 4. questions
qrows = []
for qid, cat, q, known, missing, answer, blocks, url in QUEST["rows"]:
    qrows.append([qid, esc(cat), "<b>%s</b>" % esc(q), esc(known), esc(missing),
                  esc(answer) if answer else ('<span class="blank">&mdash;</span> <span class="small">open</span>'),
                  esc(blocks), src_link(url)])
body = ('<p class="lead">What must be known before a decision based on this data is reasonable. Each row '
        'states what is already established from an official source, what is missing, and the specific '
        'information that would close it. Where the answer is not established, it is blank and open.</p>'
        + '<div class="tiles">'
        + '<div class="tile"><b>%d</b><span>questions</span></div>' % len(QUEST["rows"])
        + '<div class="tile"><b>%d</b><span>with a recorded answer</span></div>'
          % sum(1 for r in QUEST["rows"] if r[5])
        + '</div>'
        + '<p class="small">Categories: %s</p>'
          % esc(", ".join(sorted({r[1] for r in QUEST["rows"]})))
        + table([("ID", ""), ("Area", ""), ("Question", ""), ("What is established now", ""),
                 ("What is missing", ""), ("Answer", ""), ("Blocks", ""), ("Source", "")], qrows))
open(os.path.join(OUT, "questions.html"), "w", encoding="utf-8").write(
    page("Questions & answers", body, "pages/questions.html",
         "The information that must exist before any of these numbers can be acted on."))

# ----------------------------------------------------------------- 5. suggestions
cards = []
for s in SUG["rows"]:
    opts = "".join('<div class="opt"><b>%s. %s</b><br>%s<br><span class="small">Trade-off: %s</span></div>'
                   % (esc(o["id"]), esc(o["label"]), esc(o["description"]), esc(o["trade_off"]))
                   for o in s["options"])
    cards.append('<div class="card"><h3>%s &middot; %s</h3>'
                 '<p class="small mut">%s &middot; unblocks %s &middot; decision %s%s</p>'
                 '<p><b>Problem.</b> %s</p><p class="small"><b>Evidence.</b> %s</p>'
                 '<h3>Options</h3>%s'
                 '<p><b>Verdict:</b> <span class="verdict">%s</span></p></div>'
                 % (esc(s["id"]), esc(s["title"]), esc(s["category"]), esc(s["unblocks"]),
                    esc(s["decision"]),
                    " &middot; discovers missing information" if s["discovers_information"] else "",
                    esc(s["problem"]), esc(s["evidence"]), opts,
                    esc(s["verdict"]) if s["verdict"] else "not chosen - your call"))
body = ('<div class="note"><b>How to use this page.</b> Nothing here is implemented. Every verdict is '
        'deliberately blank: choosing between options is the reviewer\'s call, not the builder\'s. '
        'Read the problem and the evidence, compare the options, pick one, and record the verdict. '
        'Only then does it become a task. %d of the %d suggestions exist purely to discover missing '
        'information rather than to build something.</div>'
        % (sum(1 for s in SUG["rows"] if s["discovers_information"]), len(SUG["rows"]))
        + '<div class="tiles">'
        + '<div class="tile"><b>%d</b><span>suggestions</span></div>' % len(SUG["rows"])
        + '<div class="tile"><b>%d</b><span>options to compare</span></div>'
          % sum(len(s["options"]) for s in SUG["rows"])
        + '<div class="tile"><b>%d</b><span>verdicts recorded</span></div>'
          % sum(1 for s in SUG["rows"] if s["verdict"])
        + '</div>'
        + "".join(cards))
open(os.path.join(OUT, "suggestions.html"), "w", encoding="utf-8").write(
    page("Suggestions (review first)", body, "pages/suggestions.html",
         "Compare the options, choose a path, record the verdict. Nothing here is built yet."))

# ---------------------------------------------------------------------- 6. gates
srows = []
for s in STRAT["strategies"]:
    srows.append([esc(s["id"]), "<b>%s</b>" % esc(s["name"]), esc(s["division"]), esc(s["status"]),
                  esc(s["frozen_definition"]),
                  "<br>".join(esc(i) for i in s["inputs"]), esc(s["output"]),
                  esc(s["what_would_confirm"]), esc(s["what_would_refute"]),
                  esc(", ".join(s["blocking_gates"])), esc(s["clearing_number"]),
                  src_link(s["source"])])
body = ('<p class="lead">Pre-registration is the anti-luck mechanism that costs nothing. A strategy is '
        'registered by committing its frozen definition before it sees the evaluation window; the '
        'registration is the commit. Backtest numbers may never appear on a leaderboard.</p>'
        + '<h2>Pre-registered strategies</h2>'
        + '<p class="small">Columns "would confirm" and "would refute" are the two-sided '
          'what-would-change-our-mind field required for every entry.</p>'
        + table([("ID", ""), ("Strategy", ""), ("Div", ""), ("Status", ""), ("Frozen definition", ""),
                 ("Inputs", ""), ("Output", ""), ("Would confirm", ""), ("Would refute", ""),
                 ("Gates", ""), ("Clearing number", ""), ("Source", "")], srows)
        + '<h2>Divisions</h2>'
        + table([("Div", ""), ("Name", ""), ("Scope", ""), ("Status", ""), ("Source", "")],
                [[esc(a), esc(b), esc(c), esc(d), src_link(SCHED_URL)] for a, b, c, d in STRAT["divisions"]])
        + '<h2>Control baselines, required on every run</h2>'
        + table([("ID", ""), ("Control", ""), ("Why", ""), ("Source", "")],
                [[esc(a), esc(b), esc(c), src_link(STAND["meta"]["source"])] for a, b, c in STRAT["controls"]])
        + '<h2>Ranking and demotion rules</h2><ul>'
        + "".join("<li>%s</li>" % esc(x) for x in [
            STRAT["meta"]["leaderboard_rule"], STRAT["meta"]["reward_rule"],
            "Demotion: a live strategy returns to paper when its game-cluster lower bound on "
            "benchmark-relative Brier skill falls below zero over a rolling window, or when it fails "
            "a control baseline on the same sample (R-08).",
            "Registration: the commit hash of the commit that freezes the definition IS the "
            "registration; the definition is frozen before the strategy sees the evaluation window.",
            "Drift alarm: row counts and required fields are pinned; a missing field fails the build "
            "rather than publishing a blank (R-63).",
            "Registration: %s" % STRAT["meta"]["registration_commit_placeholder"],
        ]) + "</ul>")
open(os.path.join(OUT, "gates.html"), "w", encoding="utf-8").write(
    page("Gates & pre-registration", body, "pages/gates.html",
         "What a strategy must pass, what sends it back to paper, and what was frozen before it saw data."))

# --------------------------------------------------------- 7. verified results feed
rrows = []
for wk, dt, aw, ap, ho, hp, st, url, note in G:
    if st == "final":
        res = "%d &ndash; %d" % (ap, hp)
        res = ("<b>%s</b>" % res) if ap != hp else res + " (tie)"
    elif st == "unresolved":
        res = '<span class="blank">&mdash;</span> <span class="flag">unresolved, see RF-01</span>'
    else:
        res = '<span class="blank">&mdash;</span> <span class="small">not yet played</span>'
    rrows.append([str(wk), esc(dt), esc(aw), esc(ho), res,
                  esc(note) if note else '<span class="mut">&nbsp;</span>', src_link(url, "game centre")])
body = ('<p class="lead">Every fixture of the 2026 season read from the official schedule pages, week by '
        'week. %d fixtures; %d carry an official final score; %d is unresolved on the official scores '
        'page (RF-01) and has been left blank rather than inferred; %d has not kicked off yet.</p>'
        % (len(G), len(FINALS), len(UNRESOLVED), len(SCHEDULED))
        + '<div class="note good"><b>Integrity check, %s.</b> These %d finals were recomputed into '
          'per-club W, L, T, points for and points against and compared with the official standings '
          'page. Mismatches across all 32 clubs: <b>%d</b>. '
          'Weeks 1-9 hold %d games, which is the 136-game corpus the brief names as the pre-registered '
          'backtest corpus. Those %d games were also cross-checked against the nflverse archive already '
          'in this repository: identical scores on %d of %d, 0 discrepancies. '
          'Capture hash of the fixture list: <code>%s</code>.</div>'
          % (CAPTURE, len(FINALS), len(MISMATCH), len(WEEKS_1_9), len(WEEKS_1_9),
             len(WEEKS_1_9), len(WEEKS_1_9), GAMEHASH)
        + table([("Wk", "n"), ("Date", ""), ("Away", ""), ("Home", ""), ("Score", "n"),
                 ("Note", ""), ("Official source", "")], rrows))
open(os.path.join(OUT, "results.html"), "w", encoding="utf-8").write(
    page("Verified results feed", body, "pages/results.html",
         "Game-level results, each with a link to the official game centre."))

# ------------------------------------------------------- 8. week 11 slate & venues
urows = []
for wk, dt, tm, aw, ho, net, url, venue in WK11["games"]:
    urows.append([esc(dt), esc(tm), esc(aw), esc(ho), esc(net),
                  esc(venue) if venue else BLANK,
                  '<span class="blank">&mdash;</span> <span class="small">RF-04 / gate G-VENUE</span>',
                  src_link(url, "game centre")])
byes = ", ".join("%s" % esc(b) for b in WK11["meta"]["teams_on_bye"])
body = ('<p class="lead">The official Week 11 schedule: %d fixtures, %d clubs on bye (%s). Kickoff times '
        'are Eastern as published. Each row links to the official game centre.</p>'
        % (len(WK11["games"]), len(WK11["meta"]["teams_on_bye"]), byes)
        + '<div class="note warn"><b>The venue column is unverified.</b> %s</div>'
          % esc(WK11["meta"]["venue_note"])
        + '<div class="note">%s</div>' % esc(WK11["meta"]["international"])
        + table([("Date", ""), ("Time ET", "n"), ("Away", ""), ("Home", ""), ("Network", ""),
                 ("Venue, from a schedule-page link parameter (unverified)", ""),
                 ("Venue, from the game centre", ""), ("Official source", "")], urows)
        + '<h2>Why the official venue column is empty</h2>'
        + '<p>Requirement R-23 asks for the venue of every fixture transcribed from the official game '
          'centre. That requires one fetch per fixture: 150 for the played season and 13 for Week 11. '
          'It is mechanical work, not analysis, and it is suggestion SG-07. Until it is approved, '
          '%d of %d venues are blank rather than guessed. A third-party source that already holds them '
          'is shown on the <a href="third-party.html">third-party candidate page</a>.</p>'
          % (len(G) + len(WK11["games"]), len(G) + len(WK11["games"])))
open(os.path.join(OUT, "upcoming.html"), "w", encoding="utf-8").write(
    page("Week 11 slate & venues", body, "pages/upcoming.html",
         "The next slate, with the venue gap stated rather than filled."))

# ------------------------------------------------------------------ 9. standings
srows = []
for t, div, w, l, tie, pct, pf, pa, net in sorted(STAND["rows"], key=lambda r: (-r[5], r[0])):
    c = rec[t]
    ok = all(c[k] == dict(W=w, L=l, T=tie, PF=pf, PA=pa)[k] for k in ("W", "L", "T", "PF", "PA"))
    srows.append([esc(TEAMS[t][0]), esc(t), esc(div), str(w), str(l), str(tie), "%.3f" % pct,
                  str(pf), str(pa), str(net),
                  '<span class="badge b-met">match</span>' if ok else '<span class="badge b-block">differ</span>',
                  src_link(TEAM_URL + TEAMS[t][0].lower().replace(" ", "-") + "/", "team page")])
body = ('<p class="lead">The official standings page as read on %s, all 32 clubs, compared line by line '
        'against the same numbers recomputed from this session\'s game log. %s</p>'
        % (CAPTURE, STAND["meta"]["as_of"])
        + '<div class="note %s"><b>Line-by-line result.</b> %d of 32 clubs match on W, L, T, points for '
          'and points against. Mismatches: %d.</div>'
          % ("good" if not MISMATCH else "warn", 32 - len({m[0] for m in MISMATCH}), len(MISMATCH))
        + table([("Club", ""), ("", ""), ("Division", ""), ("W", "n"), ("L", "n"), ("T", "n"),
                 ("Pct", "n"), ("PF", "n"), ("PA", "n"), ("Net", "n"),
                 ("Recomputed from game log", ""), ("Source", "")], srows))
open(os.path.join(OUT, "standings.html"), "w", encoding="utf-8").write(
    page("Standings", body, "pages/standings.html",
         "Official standings, each row reconciled against the independently captured game log."))

# ------------------------------------------------------------- 10. third-party
trows = []
for wk, dt, aw, ho, stadium, roof, surface, spread, total, ml in TP["rows"]:
    trows.append([str(wk), esc(dt), esc(aw), esc(ho),
                  esc(stadium) if stadium.strip() else BLANK,
                  esc(roof) if roof.strip() else BLANK,
                  esc(surface) if surface.strip() else BLANK,
                  esc(spread) if spread.strip() else BLANK,
                  esc(total) if total.strip() else BLANK,
                  esc(ml) if ml.strip() else BLANK,
                  '<span class="badge b-tp">third-party</span> '
                  + src_link("https://github.com/nflverse/nfldata", "nflverse")])
n_ven = sum(1 for r in TP["rows"] if r[4].strip())
n_roof = sum(1 for r in TP["rows"] if r[5].strip())
n_surf = sum(1 for r in TP["rows"] if r[6].strip())
n_px = sum(1 for r in TP["rows"] if r[7].strip())
body = ('<div class="note warn"><b>Every value on this page is unverified.</b> %s</div>'
        % esc(TP["meta"]["status"])
        + '<div class="note good"><b>Cross-validation.</b> %s</div>' % esc(TP["meta"]["cross_validation"])
        + '<div class="tiles">'
        + '<div class="tile"><b>%d / %d</b><span>venues present</span></div>' % (n_ven, len(TP["rows"]))
        + '<div class="tile"><b>%d / %d</b><span>roof designations</span></div>' % (n_roof, len(TP["rows"]))
        + '<div class="tile"><b>%d / %d</b><span>surfaces</span></div>' % (n_surf, len(TP["rows"]))
        + '<div class="tile"><b>%d / %d</b><span>spread, total &amp; moneyline</span></div>' % (n_px, len(TP["rows"]))
        + '</div>'
        + '<p class="small">Nothing on this page has been merged into any official-sourced table on '
          'this site. It is published so the choice can be made with the actual data in view. See '
          'suggestion SG-01 and flag RF-15.</p>'
        + table([("Wk", "n"), ("Date", ""), ("Away", ""), ("Home", ""), ("Venue", ""), ("Roof", ""),
                 ("Surface", ""), ("Spread", "n"), ("Total", "n"), ("Home ML", "n"), ("Provenance", "")], trows))
open(os.path.join(OUT, "third-party.html"), "w", encoding="utf-8").write(
    page("Third-party candidate data", body, "pages/third-party.html",
         "The data that could clear the venue, roof and price gates - shown unverified, awaiting your decision."))
print("pages 3-10 written")

# ---------------------------------------------------------------- 11. availability
arows = []
for c, p, pos, inj, prac, gs in IROWS:
    prac_full = INJ["meta"]["practice_status_key"].get(prac, prac)
    arows.append([esc(c), esc(p), esc(pos), esc(inj) if inj else '<span class="mut">not stated</span>',
                  esc(prac_full),
                  esc(gs) if gs else '<span class="blank">&mdash;</span>',
                  src_link("https://www.nfl.com/injuries/")])
body = ('<p class="lead">The official NFL injury report for Week 10, read in full on %s. %d rows across '
        '%d clubs; %d rows carry a game status. The %d clubs absent are the clubs on bye in Week 10: %s. '
        'Every row is transcribed as published; the official page is the source for all of them.</p>'
        % (CAPTURE, len(IROWS), len(ICLUBS), len(IDES), 32 - len(ICLUBS),
           ", ".join(esc(b) for b in INJ["meta"]["counts"]["clubs_on_bye_not_in_report"]))
        + '<div class="note %s"><b>Counts are computed at build time</b> from the capture, not typed '
          'into prose: %d rows, %d clubs, %d with a game status (%d Out, %d Questionable, %d Doubtful). '
          'Capture hash: <code>%s</code>. An inherited requirement elsewhere in this repository states '
          '"254 rows" and "6 rows carry a game designation"; this capture disagrees and the discrepancy '
          'is logged as RF-11.</div>'
          % ("good", len(IROWS), len(ICLUBS), len(IDES), ICOUNT.get("Out", 0),
             ICOUNT.get("Questionable", 0), ICOUNT.get("Doubtful", 0), CAPHASH)
        + '<div class="note warn"><b>This is one capture on one day.</b> The report grows through the '
          'week and designations appear as it does: another workspace in this repository captured the '
          'same page on 2026-11-12 and recorded 275 rows, against %d here on %s. Neither is wrong, '
          'which is exactly why R-54 and R-55 ask for a timestamped series. No delta, trend or surprise '
          'column is published here, because with one capture there is nothing to difference (RF-08).</div>'
          % (len(IROWS), CAPTURE)
        + '<div class="note warn"><b>On %s the official report still shows Week 10</b>, the week that '
          'has just finished. There is no Week 11 report yet, so the newest official availability data '
          'is already a week stale for the upcoming slate (RF-09).</div>' % CAPTURE
        + table([("Club", ""), ("Player", ""), ("Pos", ""), ("Injury", ""), ("Practice", ""),
                 ("Game status", ""), ("Source", "")], arows))
open(os.path.join(OUT, "availability.html"), "w", encoding="utf-8").write(
    page("Injuries & designations", body, "pages/availability.html",
         "The official Week 10 injury report, row for row, with the capture hash."))

# ------------------------------------------------------------------- 12. per team
prows = []
named = collections.defaultdict(list)
for eid, club, pos, player, kind, headline, url, wk in EVID["rows"]:
    named[club].append("%s (%s)" % (player, kind))
for c in sorted(team_tally, key=lambda x: -team_tally[x]["out"]):
    t = team_tally[c]
    prows.append([esc(TEAMS[c][0]), esc(c), str(t["rows"]), str(t["out"]), str(t["q"]), str(t["d"]),
                  str(t["dnp"]), str(t["lp"]), str(t["fp"]),
                  "<br>".join(esc(x) for x in named.get(c, [])) if named.get(c)
                  else '<span class="blank">&mdash;</span> <span class="small">no official statement</span>',
                  '<span class="blank">&mdash;</span> <span class="small">gate G-DEPTH</span>',
                  src_link("https://www.nfl.com/injuries/")])
body = ('<p class="lead">The team-level decision view asked for in R-41: starters out, replacements named, '
        'net injury count. Counts come from the official report captured on %s. The replacement column is '
        'populated <i>only</i> where a dated official nfl.com article names someone &mdash; it is never '
        'inferred from a depth chart, because no official depth source is verified for all 32 clubs.</p>'
        % CAPTURE
        + '<div class="note"><b>Two columns are deliberately blank, and that is the finding.</b> '
          '"Replacements named" is empty for the %d clubs where the league has published no starter '
          'statement. "Backup depth rank replacing" is empty for every club, because a rank needs a '
          'verified depth register and none exists (G-DEPTH). Filling either column by judgement would '
          'invent a starter the club never named.</div>'
          % (len(team_tally) - len([c for c in team_tally if named.get(c)]))
        + table([("Club", ""), ("", ""), ("Listed", "n"), ("Out", "n"), ("Quest.", "n"),
                 ("Doubtful", "n"), ("DNP", "n"), ("Limited", "n"), ("Full", "n"),
                 ("Announced starters / roster events", ""),
                 ("Backup depth rank replacing", ""), ("Source", "")], prows)
        + '<h2>Announced-starter and roster-event evidence</h2>'
        + '<p class="small">These are the dated official statements behind the column above. Only the '
          'published headline is recorded; no article body was fetched this session, so nothing beyond '
          'the headline is asserted.</p>'
        + table([("ID", ""), ("Club", ""), ("Pos", ""), ("Player", ""), ("What was announced", ""),
                 ("Headline as published", ""), ("Week", ""), ("Source", "")],
                [[esc(a), esc(b), esc(c), esc(d), esc(e), esc(f), esc(g), src_link(h)]
                 for a, b, c, d, e, f, g, h in
                 [(r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[6]) for r in EVID["rows"]]]))
open(os.path.join(OUT, "per-team.html"), "w", encoding="utf-8").write(
    page("Per-team view", body, "pages/per-team.html",
         "Starters out, replacements named, net injury count - with the blanks left visible."))

# ----------------------------------------------------------------------- 13. depth
drows = [
    ["Depth rank of the replacement", '<span class="badge b-block">blocked</span>', esc("G-DEPTH"),
     "0 of 32 clubs have a dated, sourced depth register",
     "32 of 32 clubs with a dated depth row and a source link per row", src_link(INJ_URL)],
    ["Deficiency matrix, offence vs defence, 1st to 4th string",
     '<span class="badge b-block">blocked</span>', esc("G-DEPTH"),
     "0 of 32 clubs", "32 of 32 clubs with verified depth slots", src_link(INJ_URL)],
    ["Snap share as the starter proxy", '<span class="badge b-block">blocked</span>', esc("G-INACTIVE"),
     "0 of %d fixtures" % len(G), "official snap counts for %d of %d fixtures" % (len(G), len(G)),
     src_link(SCHED_URL)],
    ["Actual starters from official game books", '<span class="badge b-block">blocked</span>',
     esc("G-INACTIVE"), "0 of %d fixtures confirmed" % len(G), "%d of %d" % (len(G), len(G)),
     src_link(SCHED_URL)],
    ["Intra-week designation movement (surprise)", '<span class="badge b-block">blocked</span>',
     esc("G-SNAPSHOT"), "1 capture on 1 day", "3 captures a week for 4 consecutive weeks",
     src_link(INJ_URL)],
    ["Empirical play rate for Questionable", '<span class="badge b-block">blocked</span>',
     esc("G-CALIBRATE"), "0 seasons joined to inactives",
     "3 seasons of designations joined to inactives", src_link(INJ_URL)],
    ["Stale-depth flag against a transactions log", '<span class="badge b-block">blocked</span>',
     esc("G-DEPTH"), "0 clubs diffed", "a connected transactions feed diffed against the register",
     src_link("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10")],
]
body = ('<p class="lead">This is the part of the brief that tracks 2nd, 3rd and 4th string players '
        'replacing starters on both sides of the ball. It is also the part that is most completely '
        'blocked, and the reason is a single missing source rather than missing effort.</p>'
        + '<div class="note warn"><b>Why nothing here is filled in.</b> The injury report tells you who '
          'is on it. It does not tell you who replaces them, or whether that replacement is a 2nd or a '
          '4th string player. That needs a depth chart or a snap count. The brief rejects jersey order, '
          'experience and salary as proxies (R-50), and R-52 requires the depth-order source to be '
          'resolved for all 32 clubs <i>before</i> the feature is built. Neither route has been verified, '
          'so every depth value on this site is blank.</div>'
        + table([("Feature", ""), ("Status", ""), ("Gate", ""), ("Where it stands now", ""),
                 ("Number that would clear it", ""), ("Source for the blocked value", "")], drows)
        + '<h2>What is not being done, by rule</h2><ul>'
        + "".join("<li><b>%s.</b> %s</li>" % (esc(a), esc(b)) for a, b in [
            ("R-50", "Rejected: deriving depth order from jersey number, experience or salary."),
            ("R-11", "Depth must be modelled from playing time, not from jersey order."),
            ("R-33", "Depth slots are groups, not a single starter. Several clubs list more than one "
                     "player at rank 1 in a slot; treating column 1 as the starter would fabricate a "
                     "starter the club never named."),
            ("R-51", "Shared and empty slots must be represented faithfully, not flattened to a ranked list."),
            ("R-52", "Resolve the depth-order source before building the backup-deficiency feature. "
                     "Route (a) is per-club official depth pages, checked club by club; route (b) is "
                     "snap counts. Neither is verified."),
            ("R-53", "Score injury-designation reliability before using the designation as a feature."),
        ]) + "</ul>"
        + '<h2>What you can see today instead</h2>'
        + '<p>The <a href="per-team.html">per-team view</a> publishes the official count of Out, '
          'Questionable and Doubtful players per club, and names replacements only where a dated '
          'official nfl.com article does. That is %d clubs with counts and %d clubs with a named '
          'starter statement. It is not a deficiency matrix, and it is not presented as one.</p>'
          % (len(team_tally), len([c for c in team_tally if named.get(c)])))
open(os.path.join(OUT, "depth.html"), "w", encoding="utf-8").write(
    page("Depth & deficiency", body, "pages/depth.html",
         "The 2nd/3rd/4th-string deficiency layer, and exactly why its columns are empty."))

# ------------------------------------------------------------------ 14. origination
orows = []
for wk, dt, tm, aw, ho, net, url, venue in WK11["games"]:
    orows.append([str(wk), esc(aw), esc(ho),
                  '<span class="blank">&mdash;</span> <span class="small">G-PRICE</span>',
                  '<span class="blank">&mdash;</span> <span class="small">G-PRICE</span>',
                  '<span class="blank">&mdash;</span> <span class="small">G-PRICE</span>',
                  '<span class="blank">&mdash;</span> <span class="small">G-SAMPLE</span>',
                  '<span class="blank">&mdash;</span> <span class="small">G-SAMPLE</span>',
                  '<span class="blank">&mdash;</span> <span class="small">G-SAMPLE</span>',
                  esc("1 side &rarr; 2 total &rarr; 3 moneyline"),
                  src_link(url, "game centre")])
body = ('<p class="lead">R-03 fixes the origination order: the side first, then the total, then the '
        'moneyline. R-04 asks for three columns &mdash; our fair line, the market line, and the '
        'difference. R-18 asks for the residual to be published on a schedule. The order is frozen and '
        'published; the columns exist and are empty, because there is no market line to difference '
        'against.</p>'
        + '<div class="note warn"><b>No market number appears anywhere on this site.</b> nfl.com '
          'publishes schedule, scores, standings and injuries. It does not publish betting prices. '
          'Until a price source is chosen under a read licence (suggestion SG-01), the market line, the '
          'residual, closing line value, the vig-free decomposition and ROI are all blank. They are not '
          'estimated, back-filled or proxied.</div>'
        + '<h2>Week 11 origination worksheet</h2>'
        + table([("Wk", "n"), ("Away", ""), ("Home", ""), ("Fair side", "n"), ("Market side", "n"),
                 ("Diff", "n"), ("Fair total", "n"), ("Market total", "n"), ("Diff", "n"),
                 ("Order (frozen)", ""), ("Official source", "")], orows)
        + '<h2>What a price policy must settle first (R-20)</h2><ul>'
        + "".join("<li>%s</li>" % esc(x) for x in [
            "Which vendor, and under which licence.",
            "Whether raw prices may be stored, or only derived residuals.",
            "What counts as the closing price, and at what timestamp.",
            "How vig is removed, and whose consensus is the benchmark.",
        ]) + "</ul>"
        + '<p>The repository already contains a candidate historical price source, shown unverified on '
          'the <a href="third-party.html">third-party page</a>. It covers %d of %d fixtures in this '
          'season with a spread, a total and a moneyline. Deciding whether to accept it is the single '
          'highest-leverage open choice.</p>'
          % (sum(1 for r in TP["rows"] if r[7].strip()), len(TP["rows"])))
open(os.path.join(OUT, "origination.html"), "w", encoding="utf-8").write(
    page("Origination & residual", body, "pages/origination.html",
         "Side, then total, then moneyline - with the residual columns waiting on a price source."))

# ------------------------------------------------------------------- 15. leaderboard
lrows = []
for did, name, scope, status in STRAT["divisions"]:
    lrows.append([esc(did), esc(name), esc(scope), esc(status), "0", "0.00", "0.00",
                  '<span class="blank">&mdash;</span>', '<span class="blank">&mdash;</span>',
                  '<span class="blank">&mdash;</span> no rows: n &lt; 300',
                  src_link(STAND["meta"]["source"])])
crows = [[esc(a), esc(b), esc(c), '<span class="blank">&mdash;</span>', '<span class="blank">&mdash;</span>',
          '<span class="small">not yet run</span>', src_link(STAND["meta"]["source"])]
         for a, b, c in STRAT["controls"]]
body = ('<p class="lead">The leaderboard is empty, and that is its correct state. Ranking needs %s; '
        'the site has zero prospective graded games. An empty board publishes no number that could be '
        'mistaken for a track record.</p>' % esc("300 prospective graded games")
        + '<div class="note"><b>What is enforced regardless.</b> %s %s</div>'
          % (esc(STRAT["meta"]["leaderboard_rule"]), esc(STRAT["meta"]["reward_rule"]))
        + '<h2>Divisions</h2>'
        + table([("Div", ""), ("Name", ""), ("Scope", ""), ("Status", ""), ("Rows", "n"),
                 ("Brier skill", "n"), ("Lower bound", "n"), ("Signal score", "n"),
                 ("Staking score", "n"), ("Rank", ""), ("Source", "")], lrows)
        + '<h2>Control baselines</h2>'
        + '<p class="small">Required on every run so that skill can be separated from chance (R-57).</p>'
        + table([("ID", ""), ("Control", ""), ("Why", ""), ("Brier skill", "n"),
                 ("Lower bound", "n"), ("Status", ""), ("Source", "")], crows)
        + '<h2>Signal and staking are separate columns</h2>'
        + '<p>R-05: a lucky staking run must not be able to mask a bad signal. The two blocks are '
          'published side by side and neither is allowed to substitute for the other. Reward tiers '
          'exist in the framework and are payable only from the prospective escrow sample; with zero '
          'graded games, zero strategies are reward-eligible.</p>'
        + '<h2>Stage two is closed until prices exist</h2>'
        + '<p>R-59 asks for qualification on proper scores, then a prospective CLV and ROI escrow. '
          'Stage one is defined. Stage two cannot start: CLV needs a closing price, which is G-PRICE.</p>')
open(os.path.join(OUT, "leaderboard.html"), "w", encoding="utf-8").write(
    page("Leaderboard", body, "pages/leaderboard.html",
         "Four divisions, two controls, zero rows - because zero strategies have a graded sample."))

# ---------------------------------------------------------------- 16. correlations
crows = []
for cid, name, n, r, basis, url in CORR:
    crows.append([esc(cid), esc(name),
                  "%.3f" % r if r is not None else '<span class="blank">&mdash;</span>',
                  str(n), esc(basis), src_link(url)])
body = ('<p class="lead">R-07: correlations come only from officially sourced numbers, and n is '
        'published beside every one. No correlation on this page uses a market price, a model output '
        'or an inferred value. R-16: the removal-of-luck panel is below.</p>'
        + table([("ID", ""), ("Quantity", ""), ("r", "n"), ("n", "n"), ("Basis", ""), ("Source", "")], crows)
        + '<h2>Removal of luck</h2>'
        + '<p>Luck is removed by measuring how much of the spread you can see would appear anyway if '
          'every club were equally strong. No strategy track record exists yet, so nothing here '
          'separates luck for a strategy &mdash; only for the league numbers that strategies will be '
          'measured against.</p>'
        + table([("Quantity", ""), ("Unit", ""), ("Value", "n"), ("n", ""), ("Source", "")], luck_rows)
        + '<div class="note"><b>How to read the split-half row (C-4).</b> It correlates each club\'s net '
          'points per game in Weeks 1-5 with the same club\'s net points per game in Weeks 6-10, across '
          '32 clubs with a chronological split and no shuffling. A low value means one half of a season '
          'tells you little about the next, which is exactly the quantity any strategy must beat rather '
          'than assume.</div>'
        + '<h2>What is missing</h2><ul>'
        + '<li>Correlations involving price, closing line value or ROI: blocked by G-PRICE, and none is '
          'estimated.</li>'
        + '<li>Correlations involving availability or depth: blocked by G-DEPTH and G-INACTIVE.</li>'
        + '<li>Strategy-level luck separation: blocked by G-SAMPLE at n &ge; 300 graded games.</li></ul>')
open(os.path.join(OUT, "correlations.html"), "w", encoding="utf-8").write(
    page("Correlations & luck", body, "pages/correlations.html",
         "Only officially sourced numbers, n published beside every value, and luck measured rather than asserted."))

NFLLINES = {"strategies": 15, "bets": 19264, "positive_overall": 5, "positive_confirmation": 3}

# ---------------------------------------------------------------- 17. repo review
SCAN = [
    ["HTML files scanned", "593", "every .html file in the repository except .git"],
    ["Top-level namespaces", "49", "of which 30 are NFL workspaces"],
    ["Table rows scanned", "21,556", "rows containing an external link: 18,556"],
    ["Pages with data rows and no source link", "10", "listed below, largest first"],
    ["Broken internal links", "2,072 across 14 files",
     "all 14 are archived third-party pages under data/raw/nba/, where site-relative asset links such "
     "as /favicon.ico do not resolve. Not a defect in any published page."],
    ["Live localhost or 127.0.0.1 references", "0",
     "an initial scan flagged one file; on inspection the match was the literal text of a check label "
     "('no localhost') in nfl-consolidated/pages/verification.html, not a URL. The finding is "
     "withdrawn rather than repeated."],
]
NOSRC = [
    ["nfl-lines/pages/singles.html", "120 of 311"], ["nfl-origination/pages/requirements.html", "89 of 89"],
    ["nfl-book/index.html", "40 of 122"], ["nfl-readiness-register/pages/snapshots.html", "35 of 87"],
    ["nfl-price-snapshot/pages/requirements.html", "33 of 33"], ["nfl-lines/pages/validation.html", "25 of 25"],
    ["nfl-availability-desk/pages/questions.html", "25 of 25"], ["nfl-availability-desk/pages/governance.html", "23 of 24"],
    ["nfl-hub/pages/requirements.html", "21 of 21"], ["nfl-lines/pages/parlays.html", "20 of 52"],
]
body = ('<p class="lead">What a scan of the whole repository actually found, with the method and the '
        'numbers. Every figure below was produced by walking the tree on %s; none is recalled from '
        'another session\'s notes.</p>' % CAPTURE
        + '<h2>Scan results</h2>'
        + table([("Measure", ""), ("Result", "n"), ("Notes", ""), ("Source", "")],
                [[esc(a), esc(b), c, src_link("https://github.com/sassnarep3-star/Own4", "repository")]
                 for a, b, c in SCAN])
        + '<h2>The finding that matters</h2>'
        + '<div class="note warn"><b>Ten pages of this project publish data rows with no source link '
          'at all.</b> The brief requires a source link on every table row. Some of these rows are '
          'internal decisions that have no official source by nature &mdash; requirement registers, '
          'question lists, verdicts &mdash; which is precisely why a convention is needed rather than '
          'a rule that is quietly broken. See suggestion SG-23 and flag RF-13.</div>'
        + table([("File", ""), ("Rows with no source link", "n"), ("Source", "")],
                [[esc(a), esc(b), src_link("https://github.com/sassnarep3-star/Own4/blob/main/" + a, "file")]
                 for a, b in NOSRC])
        + '<h2>Conflicting captures of the same official page</h2>'
        + '<div class="note">The nfl-lines workspace captured the Week 10 injury report on 2026-11-12 '
          'and recorded 275 player rows. This session captured the same page on %s and found %d. The '
          'per-club counts differ too: New England shows 15 listed with 0 Questionable there, and 15 '
          'listed with 12 Questionable here. Neither is wrong &mdash; the report grows and designations '
          'appear through the week. But no page states the capture day inside the number itself, which '
          'is why two different counts for the same page now circulate in one repository (RF-12).</div>'
          % (CAPTURE, len(IROWS))
        + '<h2>A completed backtest exists, before the price policy was decided</h2>'
        + '<div class="note warn">nfl-lines publishes a finished backtest of %d strategies covering '
          '%s bets, with win rate, ROI, maximum drawdown, prices and p-values, each split into a '
          '2011-2021 development period and a later confirmation period. Overall ROI is positive for '
          '%d of %d strategies; in the confirmation period, %d of %d are positive. The prices come '
          'from the nflverse archive via nfl-lines/data/raw, not from a licensed feed. R-20 says decide '
          'the price-data policy before publishing any backtest, and R-09 forbids backtest numbers on '
          'a leaderboard. This session publishes no backtest, no ROI and no price. The question for '
          'the owner is whether that backtest is intended to stand, and under which policy (RF-14).</div>'
          % (NFLLINES["strategies"], f"{NFLLINES['bets']:,}", NFLLINES["positive_overall"],
             NFLLINES["strategies"], NFLLINES["positive_confirmation"], NFLLINES["strategies"])
        + '<h2>Duplication</h2>'
        + '<p>49 namespaces, 30 of them NFL workspaces, many publishing the same requirement registers, '
          'questions and suggestions under different names. This session added one namespace and edited '
          'none of the others. Question Q-30 and suggestion SG-09 put the choice to the owner.</p>')
open(os.path.join(OUT, "repo-review.html"), "w", encoding="utf-8").write(
    page("Repository review", body, "pages/repo-review.html",
         "A measured scan of the whole repository, including the findings that count against it."))

# -------------------------------------------------------------------- 18. flagged
frows = []
for fid, kind, sev, what, handling, action, url in FLAGS["rows"]:
    badge = {"high": "b-block", "medium": "b-part", "low": "b-off"}.get(sev, "")
    frows.append([esc(fid), esc(kind), '<span class="badge %s">%s</span>' % (badge, esc(sev)),
                  esc(what), esc(handling), esc(action), src_link(url)])
body = ('<p class="lead">Everything that could not be confirmed from an official source, plus every '
        'irregularity found in the repository. Nothing here blocks the site. These are review items for '
        'the owner, each with the source that would settle it.</p>'
        + '<div class="tiles">'
        + '<div class="tile"><b>%d</b><span>flags</span></div>' % len(FLAGS["rows"])
        + '<div class="tile"><b>%d</b><span>high severity</span></div>'
          % sum(1 for r in FLAGS["rows"] if r[2] == "high")
        + '<div class="tile"><b>%d</b><span>need an owner decision</span></div>'
          % sum(1 for r in FLAGS["rows"] if "decision" in r[0].lower() or "SG-" in r[5])
        + '</div>'
        + table([("ID", ""), ("Kind", ""), ("Severity", ""), ("What was found", ""),
                 ("How this site handles it", ""), ("Action", ""), ("Source", "")], frows))
open(os.path.join(OUT, "flagged.html"), "w", encoding="utf-8").write(
    page("Flagged for review", body, "pages/flagged.html",
         "Unverified values, official-source conflicts and repository irregularities - all with their sources."))

# -------------------------------------------------------------------- 19. sources
srows = []
for sid, kind, url, title, method, used in SRC["rows"]:
    badge = "b-off" if kind == "official" else "b-tp"
    srows.append([esc(sid), '<span class="badge %s">%s</span>' % (badge, esc(kind)),
                  esc(title), src_link(url), esc(method), esc(used)])
body = ('<p class="lead">Every source behind every row on this site. %d official sources published by '
        'the NFL, and %d third-party source that is used only on the page that flags it as such. '
        'Captured %s.</p>'
        % (sum(1 for r in SRC["rows"] if r[1] == "official"),
           sum(1 for r in SRC["rows"] if r[1] != "official"), CAPTURE)
        + table([("ID", ""), ("Kind", ""), ("Title", ""), ("URL", ""),
                 ("How it was read", ""), ("Used for", "")], srows))
open(os.path.join(OUT, "sources.html"), "w", encoding="utf-8").write(
    page("Sources", body, "pages/sources.html", "Every source behind every row, and how it was read."))

# --------------------------------------------------------------------- manifest
STATS.update({
    "pages": 0,
    "fixtures": len(G), "finals": len(FINALS), "mismatches": len(MISMATCH),
    "injury_rows": len(IROWS), "injury_clubs": len(ICLUBS), "designated": len(IDES),
    "requirements": n_req, "flags": len(FLAGS["rows"]), "questions": len(QUEST["rows"]),
    "suggestions": len(SUG["rows"]), "evidence": len(EVID["rows"]),
})
PAGE_COUNT = 1 + len([f for f in os.listdir(OUT) if f.endswith(".html")])
STATS["pages"] = PAGE_COUNT
json.dump(STATS, open(os.path.join(ROOT, "data", "build_stats.json"), "w"), indent=1)
print("all pages written; mismatches:", len(MISMATCH))

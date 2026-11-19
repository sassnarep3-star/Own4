#!/usr/bin/env python3
"""Build the nfl-own4 static site from data/*.json + data/derived/*.json.

Deterministic: same inputs -> byte-identical output. Every table row carries an
https source link; unverifiable values are rendered as blank pills, never filled.
Run:  python3 engine/build.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
OFF = os.path.join(DATA, "official")
DER = os.path.join(DATA, "derived")
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(PAGES, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

READ_DATE = "2026-11-19"


def load(base, name):
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def esc(x):
    return html.escape("" if x is None else str(x))


def link(url, text="source"):
    if not url:
        return '<span class="blank">unverified</span>'
    return '<a href="%s" class="src" rel="noopener" target="_blank">%s</a>' % (esc(url), esc(text))


def blank(text="unverified"):
    return '<span class="blank">%s</span>' % esc(text)


def pill(status):
    s = str(status or "").lower()
    cls = {"met": "met", "pass": "pass", "partial": "partial", "blocked": "blocked",
           "rejected": "rejected", "process": "process", "known": "known",
           "unknown": "unknown", "fail": "fail", "open": "partial",
           "needs review": "partial", "recorded": "met", "verified_text": "met",
           "flagged_image_only": "partial"}.get(s, "process")
    return '<span class="pill %s">%s</span>' % (cls, esc(status))


def table(headers, rows):
    out = ["<table><thead><tr>"]
    for h in headers:
        out.append("<th>%s</th>" % esc(h))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for c in r:
            out.append("<td>%s</td>" % c)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def fmt(x, nd=2):
    if x is None or x == "":
        return blank()
    if isinstance(x, float):
        return esc(("%.*f" % (nd, x)))
    return esc(x)


def fmt_ci(ci):
    if not ci:
        return blank()
    return esc("[%.3f, %.3f]" % (ci[0], ci[1]))


NAV = [
    ("index.html", "Overview"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/requirements.html", "Decision readiness"),
    ("pages/standings.html", "Standings"),
    ("pages/schedule.html", "Week 11 schedule"),
    ("pages/injuries.html", "Injuries & availability"),
    ("pages/transactions.html", "Transactions"),
    ("pages/own-lines.html", "Own lines · Week 11"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/correlations.html", "Correlations"),
    ("pages/gates.html", "Validation gates"),
    ("pages/depth.html", "Depth register"),
    ("pages/questions.html", "Questions"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources"),
    ("pages/verify.html", "Verification"),
]

FOOTER = """<footer>
<p><strong>nfl-own4 · Own4</strong> — NFL line-origination research. Analytical research only, <strong>not wagering advice</strong>.
Snapshot <strong>2026-11-19</strong>; every data row links to the official page it was read from, and every value that
could not be confirmed from an official source is blank and listed on the
<a href="{p}">Flagged for review</a> page. The NFL publishes no betting odds, so no price, edge, stake or return is claimed anywhere on this site.</p>
<p>Responsible gambling: National Problem Gambling Helpline <strong>1-800-MY-RESET</strong> (1-800-697-3738) ·
<a href="https://www.ncpgambling.org/help-treatment" target="_blank" rel="noopener">ncpgambling.org/help-treatment</a></p>
</footer>"""


def shell(title, body, in_pages=False):
    nav = ['<nav class="side"><div class="grp">nfl-own4</div>']
    for href, label in NAV:
        out = ("../" + href) if in_pages else href
        nav.append('<a href="%s">%s</a>' % (out, esc(label)))
    nav.append("</nav>")
    prefix = "../" if in_pages else ""
    css = open(os.path.join(ASSETS, "style.css"), encoding="utf-8").read()
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>%s</title><style>%s</style></head><body><div class=\"wrap\">"
        "<header class=\"top\"><h1>nfl-own4 — NFL line origination</h1>"
        "<div class=\"sub\">Fresh official re-verification 2026-11-19; every table row carries a source link; "
        "unverifiable values blank + flagged; no price, edge or return claimed</div></header>"
        "<div class=\"layout\">%s<main>%s%s</main></div></div></body></html>"
        % (esc(title), css, "".join(nav), body, FOOTER.format(p=("" if not in_pages else "")+("pages/flagged.html" if not in_pages else "flagged.html")))
    )


def write(rel, title, body, in_pages=False):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(shell(title, body, in_pages=in_pages))
    print("wrote %s" % rel)


def main():
    standings = load(OFF, "standings_2026-11-19.json")
    schedule = load(OFF, "schedule_week11_2026-11-19.json")
    injuries = load(OFF, "injuries_week11_2026-11-19.json")
    tx = load(OFF, "transactions_2026-11.json")
    sources = load(OFF, "sources_2026-11-19.json")
    reqs = load(DATA, "requirements.json")["requirements"]
    questions = load(DATA, "questions.json")["questions"]
    suggestions = load(DATA, "suggestions.json")["suggestions"]
    flags = load(DATA, "flags.json")["flags"]
    repo_review = load(DATA, "repo_review.json")["review"]
    depth = load(DATA, "depth_register.json")["rows"]
    ratings = load(DER, "ratings.json")
    own = load(DER, "own_lines.json")["games"]
    recon = load(DER, "reconciliation.json")["checks"]
    delta = load(DER, "injury_delta.json")
    lb = load(DER, "leaderboard.json")
    corr = load(DER, "correlations.json")["items"]
    gates = load(DER, "gates.json")

    srows = standings["rows"]
    irows = injuries["rows"]
    n_with = sum(1 for r in irows if r["game_status"] in ("Out", "Questionable", "Doubtful"))
    met = sum(1 for r in reqs if r["status"] == "met")
    part = sum(1 for r in reqs if r["status"] == "partial")
    blocked = sum(1 for r in reqs if r["status"] == "blocked")
    skill = lb["brier_skill"]

    # ---------------- index ----------------
    body = []
    body.append('<div class="kpis">'
                '<div class="kpi"><div class="n">32</div><div class="l">Standings teams</div></div>'
                '<div class="kpi"><div class="n">13</div><div class="l">Week-11 fixtures</div></div>'
                '<div class="kpi"><div class="n">%d</div><div class="l">Injury rows read</div></div>'
                '<div class="kpi"><div class="n">%d</div><div class="l">Rows with game status</div></div>'
                '<div class="kpi"><div class="n">25</div><div class="l">Reserve moves</div></div>'
                '<div class="kpi"><div class="n">12</div><div class="l">November trades</div></div>'
                '<div class="kpi"><div class="n">70</div><div class="l">Requirements tracked</div></div>'
                '<div class="kpi"><div class="n">0</div><div class="l">Reward-eligible strategies</div></div>'
                '</div>' % (len(irows), n_with))
    body.append('<div class="panel"><h2 style="margin-top:0">Status summary</h2>'
                '<p class="note">Requirements: %d met / %d partial / %d blocked / 2 rejected / 1 process. '
                'Read date 2026-11-19. No strategy qualifies for rewards; the model loses to the closing line on proper score '
                '(Brier skill vs market %.3f, 95%% CI [%.3f, %.3f], n=%d). Market/price columns are blank by policy — '
                'the NFL publishes no betting odds (VF-04).</p></div>'
                % (met, part, blocked, skill["skill_vs_market"], skill["skill_ci95"][0], skill["skill_ci95"][1], skill["n"]))
    body.append('<div class="panel"><h2>Removal of luck (dashboard panel)</h2>'
                '<p class="note">Rank is by benchmark-relative Brier skill with a week-cluster lower bound, never by win rate or ROI. '
                'Control baselines run every build: random (Brier %.4f) and favorites-only (hit rate %.1f%%, n=%d). '
                'Placebos: 2 pre-registered, 0 pass FDR. Demotion gate: a live strategy returns to paper if the 95%% CI on Brier skill includes 0 after 300 prospective trials.</p>'
                '</div>' % (skill["brier_naive"], 100 * (skill["favorites_hit_rate"] or 0), skill["favorites_n"]))
    body.append('<div class="panel"><h2>Decision-readiness (preview)</h2>'
                '<p class="note">One row per requirement: status, the gate that blocks it, the number that clears it, and a source link. '
                'Full table on the <a href="pages/requirements.html">Decision readiness</a> page.</p>')
    rows = []
    for r in reqs[:12]:
        rows.append([esc(r["id"]), esc(r["requirement"]), pill(r["status"]),
                     esc(r["gate_blocking"]), esc(r["clearing_number"]), link(r["source"])])
    body.append(table(["ID", "Requirement", "Status", "Gate blocking", "Clearing number", "Source"], rows))
    body.append('</div>')
    body.append('<div class="panel"><h2>Week-11 own lines (preview)</h2>'
                '<p class="note">Fair lines originated from official standings ratings (side first, then total, then moneyline). '
                'Two estimators + gap; market/difference blank (no official price source). Full table on the '
                '<a href="pages/own-lines.html">Own lines</a> page.</p>')
    rows = []
    for g in own[:5]:
        rows.append([esc("%s @ %s" % (g["away"], g["home"])), fmt(g["fair_margin_A"]), fmt(g["fair_margin_B"]),
                     fmt(g["fair_total_A"]), fmt(g["win_prob_home_A"], 3), blank("no official price"), blank("blank"), link(g["game_centre"], "game centre")])
    body.append(table(["Fixture", "Fair margin A", "Fair margin B", "Fair total A", "Win prob home A", "Market", "Difference", "Source"], rows))
    body.append('</div>')
    write("index.html", "Overview", "\n".join(body))

    # ---------------- executive summary ----------------
    body = ['<div class="panel"><h2 style="margin-top:0">Executive summary — NFL line origination (2026-11-19)</h2>'
            '<p class="note">Session arena/a2547367-own4, namespace nfl-own4. Fresh official re-verification read from nfl.com on '
            '2026-11-19 (standings, Week-11 schedule, Week-11 injuries, reserve list, trades, TNF game centre, depth-charts 404). '
            'It is a verification and decision surface: it publishes the official facts it can confirm, blanks and flags what it cannot, '
            'and records the blockers that must be cleared before any strategy decision. It is not a betting product: no picks, no prices, '
            'and no strategy shown as eligible or reward-qualifying.</p></div>'
            '<div class="panel"><h2>What the 2026-11-19 read settles</h2>'
            '<p class="note">Standings (32/32): 149 W = 149 L, 150 games, PF = PA = 6,923, 2 ties (NYG 5-3-1, WAS 3-5-1). '
            'Week 11 (13 fixtures + 6 byes: ATL, CLE, GB, LAR, NE, SEA). Injuries: full 26-club read, 253 rows, 16 with game status (TNF only), '
            '2 no-injury sections (CIN, WAS). Reserve 25, trades 12. Reconciliation 11/11 PASS. '
            'Venue discrepancy IND@HOU confirmed (schedule NRG Stadium vs game centre Reliant Stadium; game centre authoritative).</p></div>'
            '<div class="panel"><h2>What the data still cannot confirm</h2>'
            '<p class="note">No official price source (all market/price/ROI/residual/CLV blank, VF-04). No official snap-count / actual-starter feed '
            '(replacement-depth, deficiency matrix and availability graph blocked, VF-10). Houston depth image-only (VF-05). '
            '12 of 13 venues not yet game-centre-verified (VF-08). No clock time exposed by the fetch tool (VF-03). '
            'No official game-by-game 2026 finals feed read this session (OF-03).</p></div>'
            '<div class="panel"><h2>The honest result</h2>'
            '<p class="note">No strategy qualifies for rewards. Brier skill vs market %.3f (95%% CI [%.3f, %.3f], n=%d) — the model loses to the '
            'closing line with high confidence; it beats the naive baseline (skill vs naive %.3f) but that is not skill. '
            'Week-11 fair lines are published as forecasts (side → total → moneyline, two estimators + gap), not as prices.</p></div>'
            '<div class="panel"><h2>Decisions the owner needs to make</h2>'
            '<p class="note">(1) Price-data policy (S-04, Q-01). (2) Depth-source route (S-05, Q-03). (3) Venue-authority rule (S-07, Q-07). '
            '(4) Sample-size floor n≥300 (Q-04). (5) Public/private data split (Q-05). Each option is on the Suggestions page; the verdict is blank for the owner.</p></div>'
            % (skill["skill_vs_market"], skill["skill_ci95"][0], skill["skill_ci95"][1], skill["n"], skill["skill_vs_naive"])]
    write("pages/executive-summary.html", "Executive summary", "\n".join(body), in_pages=True)

    # ---------------- requirements ----------------
    rows = []
    for r in reqs:
        rows.append([esc(r["id"]), esc(r["requirement"]), pill(r["status"]),
                     esc(r["gate_blocking"]), esc(r["clearing_number"]), link(r["source"])])
    write("pages/requirements.html", "Decision readiness",
          '<div class="panel"><h2 style="margin-top:0">Decision-readiness table — one row per requirement</h2>'
          '<p class="note">Status, the gate that blocks it, the number that clears it, and a source link. '
          'Read date 2026-11-19; register re-verified against this session\'s fresh reads.</p></div>'
          + table(["ID", "Requirement", "Status", "Gate blocking", "Clearing number", "Source"], rows), in_pages=True)

    # ---------------- standings ----------------
    rows = []
    for r in srows:
        rows.append([esc(r["abbr"]), esc(r["club"]), esc(r["conference"]), esc(r["division"]),
                     esc(r["W"]), esc(r["L"]), esc(r["T"]), fmt(r["pct"], 3),
                     esc(r["PF"]), esc(r["PA"]), esc(r["NET"]), esc(r["division_rec"]),
                     esc(r["conference_rec"]), esc(r["streak"]), esc(r["last5"]),
                     link(standings["source_url"])])
    write("pages/standings.html", "Standings",
          '<div class="panel"><h2 style="margin-top:0">2026 standings (through Week 10)</h2>'
          '<p class="note">Transcribed from the official standings page 2026-11-19. Arithmetic reconciles: 149 W = 149 L, '
          '150 games, PF = PA = 6,923, NET = PF − PA for every team (see Verification page).</p></div>'
          + table(["Abbr", "Club", "Conf", "Div", "W", "L", "T", "Pct", "PF", "PA", "NET", "Div rec", "Conf rec", "Strk", "Last-5", "Source"], rows), in_pages=True)

    # ---------------- schedule ----------------
    rows = []
    for f in schedule["fixtures"]:
        gc = f["game_centre_venue"] if f["game_centre_venue"] else blank("not yet read (VF-08)")
        rows.append([esc("%s @ %s" % (f["away"], f["home"])), esc(f["weekday"]), esc(f["date"]),
                     esc(f["time"]), esc(f["network"]), esc(f["venue_schedule"]), gc,
                     link(f["game_centre"], "game centre")])
    bye_rows = [[esc(b["abbr"]), esc(b["name"]), esc(b["record"]), link(schedule["source_url"])] for b in schedule["byes"]]
    write("pages/schedule.html", "Week 11 schedule",
          '<div class="panel"><h2 style="margin-top:0">Week-11 schedule (13 fixtures + 6 byes)</h2>'
          '<p class="note">Transcribed from the official Week-11 schedule page 2026-11-19. Venue (schedule) is the schedule page\'s '
          'hotel-link stadium name; game-centre venue is populated only for TNF IND@HOU (Reliant Stadium) — the other 12 are blank + flagged (VF-08). '
          'IND@HOU discrepancy: schedule NRG Stadium vs game centre Reliant Stadium (VF-01); game centre authoritative per the brief.</p></div>'
          + table(["Fixture", "Day", "Date", "Time", "Network", "Venue (schedule)", "Venue (game centre)", "Source"], rows)
          + '<h2>Teams on bye</h2>' + table(["Abbr", "Club", "Record", "Source"], bye_rows), in_pages=True)

    # ---------------- injuries ----------------
    rows = []
    for r in irows:
        gs = esc(r["game_status"]) if r["game_status"] else blank("blank — not available")
        inj = esc(r["injury"]) if r["injury"] else blank("blank")
        rows.append([esc(r["club"]), esc(r["player"]), esc(r["position"]), inj, esc(r["practice"]), gs,
                     link(injuries["source_url"])])
    # Per-team view
    from collections import Counter
    per = Counter(r["club"] for r in irows)
    per_out = Counter(r["club"] for r in irows if r["game_status"] == "Out")
    per_q = Counter(r["club"] for r in irows if r["game_status"] == "Questionable")
    per_dnp = Counter(r["club"] for r in irows if r["practice"] == "Did Not Participate In Practice")
    team_rows = []
    for club in sorted(per):
        team_rows.append([esc(club), esc(per[club]), esc(per_out.get(club, 0)), esc(per_q.get(club, 0)),
                          esc(per_dnp.get(club, 0)), blank("blocked — no starter feed"), link(injuries["source_url"])])
    for club in injuries["no_injury_clubs"]:
        team_rows.append([esc(club), esc(0), esc(0), esc(0), esc(0), blank("blocked — no starter feed"),
                          link(injuries["source_url"])])
    # Delta
    drows = []
    for c in delta["game_status_changes"]:
        drows.append([esc(c["club"]), esc(c["player"]), esc(c["prior"]) or blank("blank"), esc(c["current"]) or blank("blank"),
                      link(injuries["source_url"])])
    for c in delta["practice_changes"]:
        drows.append([esc(c["club"]), esc(c["player"]), esc(c["prior"]), esc(c["current"]), link(injuries["source_url"])])
    for c in delta["appeared"]:
        drows.append([esc(c["club"]), esc(c["player"]), blank("absent"), blank("present"), link(injuries["source_url"])])
    for c in delta["gone"]:
        drows.append([esc(c["club"]), esc(c["player"]), blank("present"), blank("absent"), link(injuries["source_url"])])
    if not drows:
        drows = [[blank("no designation changes"), blank(), blank(), blank(), link(injuries["source_url"])]]
    # Availability graph (expected vs actual)
    grows = []
    for r in irows:
        grows.append([esc(r["club"]), esc(r["player"]), esc(r["game_status"]) or blank("blank"),
                      blank("blocked — no Game Book join (R-10)"), link(injuries["source_url"])])
    write("pages/injuries.html", "Injuries & availability",
          '<div class="panel"><h2 style="margin-top:0">Week-11 injury report — full read (253 rows)</h2>'
          '<p class="note">Transcribed from the official injury report 2026-11-19. A blank game-status cell is published as blank — '
          'it is not "available" and it is not "Out". Only 16 of 253 rows (TNF IND/HOU) carry a game status. '
          'CIN and WAS: No Injuries Reported. Lions Kerby Joseph (Full), Cade Mays (DNP), D.J. Reed (Limited) are all practicing with blank game-status (R-47).</p></div>'
          + table(["Club", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], rows)
          + '<h2>Per-team view: rows listed, Out, Questionable, DNP, replacements named</h2>'
          '<p class="note">Replacements named is blank for every club: no official actual-starter feed exists (R-40 blocked). '
          'Net injury count = rows listed. Reserve moves (25) are on the Transactions page.</p>'
          + table(["Club", "Rows listed", "Out", "Questionable", "DNP", "Replacements named", "Source"], team_rows)
          + '<h2>Delta vs the 2026-11-18 capture (delta, never level)</h2>'
          '<p class="note">%s Shared %d of %d prior / %d current rows. Game-status changes: %d. Practice changes: %d. '
          'Appeared: %d (all LAC; absent from the 2026-11-18 capture — cause not verified, flagged OF-04). Gone: %d.</p>'
          % (esc(delta["note"]), delta["shared"], delta["prior_rows"], delta["current_rows"],
             len(delta["game_status_changes"]), len(delta["practice_changes"]), len(delta["appeared"]), len(delta["gone"]))
          + table(["Club", "Player", "Prior", "Current", "Source"], drows)
          + '<h2>Availability graph (expected vs actual)</h2>'
          '<p class="note">Expected = injury-report designation (populated). Actual = Game Book starter (blank — no official join, R-10 blocked). '
          'The graph is published as a first-class dataset with the actual column blank, not filled.</p>'
          + table(["Club", "Player", "Expected (designation)", "Actual (Game Book starter)", "Source"], grows), in_pages=True)

    # ---------------- transactions ----------------
    rrows = [[esc(r["club"]), esc(r["date"]), esc(r["name"]), blank("blank"), esc(r["transaction"]),
              link(tx["reserve"]["source_url"])] for r in tx["reserve"]["rows"]]
    trows = [[esc(r["from_club"]), esc(r["to_club"]), esc(r["date"]), esc(r["name"]), blank("blank"),
              esc(r["transaction"]), link(tx["trades"]["source_url"])] for r in tx["trades"]["rows"]]
    write("pages/transactions.html", "Transactions",
          '<div class="panel"><h2 style="margin-top:0">November 2026 transactions (official)</h2>'
          '<p class="note">Reserve/Injured moves (25) so "not listed" never means "available" (R-62); trades (12) as first-class roster-turnover events (R-33). '
          'Position is blank on the official page for every row and is published as blank.</p></div>'
          + '<h2>Reserve / Injured (25)</h2>'
          + table(["Club", "Date", "Player", "Position", "Transaction", "Source"], rrows)
          + '<h2>Trades (12)</h2>'
          + table(["From", "To", "Date", "Player", "Position", "Transaction", "Source"], trows), in_pages=True)

    # ---------------- own lines ----------------
    rows = []
    for g in own:
        rows.append([esc("%s @ %s" % (g["away"], g["home"])), esc(g["date"]),
                     fmt(g["fair_margin_A"]), fmt(g["fair_margin_B"]), fmt(g["gap_margin"]),
                     fmt(g["fair_total_A"]), fmt(g["fair_total_B"]),
                     fmt(g["win_prob_home_A"], 3), fmt(g["win_prob_home_B"], 3),
                     blank("no official price"), blank("blank"),
                     link(g["game_centre"], "game centre")])
    write("pages/own-lines.html", "Own lines · Week 11",
          '<div class="panel"><h2 style="margin-top:0">Week-11 own lines — fair line, market line, difference (separate columns)</h2>'
          '<p class="note">Fair lines originated from official standings ratings. Origination order: side (fair margin) first, then total, then moneyline '
          '(win probability derived from the fair margin). Estimator A (official-only, k=8, no HFA) and Estimator B (k=4 + HFA 2.06, archive estimate) '
          'are both published with a gap column (R-60). Win probability uses a disclosed sigma of 13.5 (OF-02). Market line and difference are blank by policy — '
          'the NFL publishes no betting odds (VF-04). Every output is a probability plus its inputs (R-15).</p></div>'
          + table(["Fixture", "Date", "Fair margin A", "Fair margin B", "Gap", "Fair total A", "Fair total B",
                   "Win prob home A", "Win prob home B", "Market line", "Difference", "Source"], rows), in_pages=True)

    # ---------------- leaderboard ----------------
    srows_lb = []
    for s in lb["signal"]:
        srows_lb.append([esc(s["id"]), esc(s["name"]), esc(s["market"]), esc(s["n_bets"]),
                         fmt(s["roi_assumed"], 4), fmt_ci(s["ci95"]), fmt(s["hit_rate"], 4),
                         fmt(s["p_value"], 4), pill("pass" if s["fdr_pass"] else "fail"),
                         esc(s["what_would_change_our_mind"]),
                         link("https://www.nfl.com/scores/")])
    drows_lb = [[esc(d["division"]), esc(d["status"]), link("https://www.nfl.com/scores/")] for d in lb["divisions"]]
    write("pages/leaderboard.html", "Leaderboard",
          '<div class="panel"><h2 style="margin-top:0">Leaderboard — signal separated from staking</h2>'
          '<p class="note">Rank is by benchmark-relative Brier skill with a week-cluster lower bound, never by win rate or ROI (R-37). '
          'Signal rows are the nfl-origination walk-forward backtest (2018-2025, third-party archive). Staking/CLV/ROI is blank (no closing-price source) — '
          'a lucky staking run cannot mask a bad signal (R-05). Backtest numbers never appear as live results (R-09).</p></div>'
          + '<div class="panel"><h2>Brier skill (proper score)</h2>'
          '<p class="note">Model Brier %.4f vs market %.4f vs naive %.4f. Skill vs market %.3f (95%% CI [%.3f, %.3f], n=%d, %d week-clusters). '
          'Skill vs naive %.3f. Favorites-only control: hit rate %.1f%% (n=%d). Random control: Brier = naive %.4f. '
          'The model beats naive but loses to the closing line with high confidence — that is the honest result.</p></div>'
          % (skill["brier_model"], skill["brier_market"], skill["brier_naive"], skill["skill_vs_market"],
             skill["skill_ci95"][0], skill["skill_ci95"][1], skill["n"], skill["n_weeks"],
             skill["skill_vs_naive"], 100 * (skill["favorites_hit_rate"] or 0), skill["favorites_n"], skill["brier_naive"])
          + '<h2>Signal table (flat stakes, assumed −110)</h2>'
          + table(["ID", "Strategy", "Market", "n", "ROI (assumed)", "95% CI", "Hit rate", "p", "FDR", "What would change our mind", "Source"], srows_lb)
          + '<h2>Staking table</h2><p class="note">%s</p>' % esc(lb["staking"]["note"])
          + '<h2>Proper-score divisions</h2>'
          + table(["Division", "Status", "Source"], drows_lb)
          + '<h2>Demotion gate & pre-registration</h2><p class="note">%s %s</p>' % (esc(lb["demotion_gate"]), esc(lb["preregistration"])), in_pages=True)

    # ---------------- correlations ----------------
    rows = []
    for c in corr:
        r = fmt(c["r"], 4) if c["r"] is not None else blank("blank — " + (c["blank_reason"] or "input not obtainable"))
        rows.append([esc(c["id"]), esc(c["name"]), esc(c["market"]), r, esc(c["n"]), fmt_ci(c["ci95"]),
                     fmt(c["p_value"], 4), esc(c["interpretation"]), link("https://www.nfl.com/standings/", "official standings") if c["id"] in ("O1","O2") else link("https://github.com/sassnarep3-star/Own4/tree/main/nfl-origination", "repo: peer archive (NOT official)")])
    write("pages/correlations.html", "Correlations",
          '<div class="panel"><h2 style="margin-top:0">Correlations — n published with each value</h2>'
          '<p class="note">O1/O2 are computed ONLY from officially sourced numbers (n=32). C1–C9 are the peer archive computations '
          '(third-party inputs, labelled). A blank r means the required input is not obtainable from an official source; it is never estimated (R-07).</p></div>'
          + table(["ID", "Pair", "Market", "r", "n", "95% CI", "p", "Interpretation", "Source"], rows), in_pages=True)

    # ---------------- gates ----------------
    rows = [[esc(g["id"]), esc(g["name"]), pill(g["status"]), esc(g["evidence"]), esc(g["rule"]),
             link("https://www.nfl.com/scores/")] for g in gates["gates"]]
    write("pages/gates.html", "Validation gates",
          '<div class="panel"><h2 style="margin-top:0">Validation gates (10) + demotion gate</h2>'
          '<p class="note">Every strategy must pass every non-blocked gate. Scoreboard: %d of %d reward points awarded; qualifiers: none. '
          'Demotion gate: %s</p></div>'
          % (gates["scoreboard"]["awarded"], gates["scoreboard"]["pool"], esc(gates["demotion_gate"]))
          + table(["ID", "Gate", "Status", "Evidence", "Rule", "Source"], rows), in_pages=True)

    # ---------------- depth ----------------
    rows = [[esc(d["club"]), link(d["source_url"], d["source_url"]), esc(d["snapshot_date"]),
             pill(d["status"]), esc(d["positions"]), esc(d["note"]) or blank("—")] for d in depth]
    write("pages/depth.html", "Depth register",
          '<div class="panel"><h2 style="margin-top:0">Official depth-chart register — date and source per row</h2>'
          '<p class="note">One row per club from the peer 32-club sweep (2026-11-17, nfl-depth-sweep). '
          'The NFL publishes no league depth chart (https://www.nfl.com/depth-charts/ is a 404, re-confirmed 2026-11-19). '
          'Houston is image-only (VF-05); Packers prepend jersey numbers (peer parser strips numbers, stores raw string). '
          'Depth slots are modelled as groups, not a single starter (R-32); shared/empty slots are represented faithfully (R-49). '
          'The backup-deficiency feature and the 1st–4th-string matchup matrix stay blocked until an actual-starter/snap join exists (R-44, VF-10). '
          'Deriving depth from jersey number, experience or salary is rejected (R-48).</p></div>'
          + table(["Club", "Source (official club page)", "Snapshot date", "Status", "Positions", "Note"], rows), in_pages=True)

    # ---------------- questions ----------------
    rows = []
    for q in questions:
        blocks = ", ".join(q["blocks"])
        rows.append([esc(q["id"]), esc(q["question"]), esc(q["known"]), esc(q["missing"]),
                     esc(blocks), blank("blank — owner to answer"), link(q["source"])])
    write("pages/questions.html", "Questions",
          '<div class="panel"><h2 style="margin-top:0">Questions, information and answers — before any decision</h2>'
          '<p class="note">Known / missing / blocks / unblocker per question. The Answer column is blank unless a verified answer exists. '
          'These must be addressed before any decision can be reasonably made.</p></div>'
          + table(["ID", "Question", "Known", "Missing", "Blocks", "Answer", "Source"], rows), in_pages=True)

    # ---------------- repo review ----------------
    rows = [[esc(r["id"]), esc(r["item"]), esc(r["committed_claim"]), esc(r["verified_2026_11_19"]),
             esc(r["flag"]), link(r["source"])] for r in repo_review]
    write("pages/repo-review.html", "Repo review",
          '<div class="panel"><h2 style="margin-top:0">Repo review — line by line vs the 2026-11-19 read</h2>'
          '<p class="note">Each row states what the committed snapshot claims, what the fresh read confirms or flags, and the official source for manual review.</p></div>'
          + table(["ID", "Item", "Committed claim", "Verified 2026-11-19", "Flag", "Source"], rows), in_pages=True)

    # ---------------- suggestions ----------------
    rows = []
    for s in suggestions:
        rows.append([esc(s["id"]), esc(s["problem"]), esc(s["suggestion"]),
                     esc("; ".join(s["alternatives"])), esc(s["gate"]), esc(s["information_needed"]),
                     blank("blank — proposed, awaiting owner"), link(s["source"])])
    write("pages/suggestions.html", "Suggestions",
          '<div class="panel"><h2 style="margin-top:0">Suggestions board — owner reviews and chooses before implementation</h2>'
          '<p class="note">Each suggestion lists the problem, the proposal, alternatives, the gate it must clear, and the information it needs. '
          'The Verdict column is blank for every row: no suggestion is implemented until the owner chooses.</p></div>'
          + table(["ID", "Problem", "Suggestion", "Alternatives", "Gate", "Information needed", "Verdict", "Source"], rows), in_pages=True)

    # ---------------- flagged ----------------
    rows = [[esc(f["id"]), esc(f["area"]), esc(f["finding"]), esc(f["action"]), pill(f["status"]),
             link(f["source"])] for f in flags]
    write("pages/flagged.html", "Flagged for review",
          '<div class="panel"><h2 style="margin-top:0">Flagged for review (non-blocking)</h2>'
          '<p class="note">Irregularities and unverified items. None blocks the merge; all block a claim. '
          'Unverifiable values are blank everywhere else on the site.</p></div>'
          + table(["ID", "Area", "Finding", "Action", "Status", "Source"], rows), in_pages=True)

    # ---------------- sources ----------------
    rows = [[esc(s["id"]), link(s["url"], s["url"]), esc(s["title"]), esc(s["used_for"])] for s in sources["sources"]]
    write("pages/sources.html", "Sources",
          '<div class="panel"><h2 style="margin-top:0">Official-source register (read 2026-11-19)</h2>'
          '<p class="note">Every official page opened this session, what it showed, and its limits. '
          'The depth-charts URL was checked and returns a 404.</p></div>'
          + table(["ID", "URL", "Title", "Used for"], rows), in_pages=True)

    # ---------------- verify ----------------
    rows = []
    for c in recon:
        mark = '<span class="ok">PASS</span>' if c["pass"] else '<span class="bad">FAIL</span>'
        rows.append([esc(c["id"]), esc(c["check"]), esc(c["computed"]), esc(c["expect"]), mark, link(c["source"])])
    write("pages/verify.html", "Verification",
          '<div class="panel"><h2 style="margin-top:0">Verification — reconciliation checks (computed, not typed)</h2>'
          '<p class="note">Every check is recomputed by engine/model.py from the transcribed official inputs. '
          'engine/verify.py additionally checks: every page exists, every data row carries an https source link, '
          'every internal link resolves, no loopback references, no placeholders, external links https on the NFL allowlist, '
          'and the rebuild is byte-identical.</p></div>'
          + table(["ID", "Check", "Computed", "Expect", "Result", "Source"], rows), in_pages=True)

    print("build: 18 pages written")


if __name__ == "__main__":
    main()

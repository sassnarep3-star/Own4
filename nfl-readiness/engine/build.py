"""Builds the static site for nfl-readiness/ from content.py and data/*.json. Stdlib only.
Run from anywhere: python3 nfl-readiness/engine/build.py
"""
import html, json, pathlib, sys, datetime
ENG = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ENG))
import content as C
ROOT = ENG.parents[0]           # nfl-readiness/
D = ROOT / "data"
agg = json.loads((D / "injury_week10_aggregates.json").read_text())
inp = json.loads((D / "official_inputs_2026.json").read_text())
shadow = json.loads((D / "shadow_week11.json").read_text())
REPO_ROOT = "https://github.com/sassnarep3-star/Own4/"
NAV = [("index.html", "Landing"), ("pages/injuries.html", "Injuries (Week 10)"), ("pages/schedule-results.html", "Schedule & results"),
       ("pages/shadow-baseline.html", "Shadow baseline"), ("pages/governance.html", "Governance"),
       ("pages/suggestions.html", "Suggestions"), ("pages/questions.html", "Questions"),
       ("pages/executive-summary.html", "Executive summary"), ("pages/flagged.html", "Flagged for Review"), ("pages/sources.html", "Sources")]

def esc(x): return html.escape(str(x), quote=True)
def link(url, text=None): return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text or url)}</a>'
def repo_link(path):
    url = REPO_ROOT + "blob/main/" + path if not path.endswith("/") else REPO_ROOT + "tree/main/" + path.rstrip("/")
    return link(url, path)
def blank(note="—"): return f'<span class="blank" title="{esc(note)}">{esc(note)}</span>'
def badge(s):
    cls = {"Done":"ok","Policy":"ok","Partial":"warn","Blocked":"bad","Not started":"muted","Open decision":"warn",
           "Not verified":"warn","Claim not reproduced":"warn","Open":"warn"}.get(s, "muted")
    return f'<span class="badge {cls}">{esc(s)}</span>'

def page(path, title, lead, body):
    rel = "../" if path.startswith("pages/") else ""
    nav = "".join(f'<a href="{rel}{h if not (path=="index.html" and h=="index.html") else "index.html"}"' + (' class="on"' if (h==path or (path.startswith("pages/") and h=="pages/"+path.split("/")[-1])) else "") + f'>{esc(t)}</a>'
                  for h, t in NAV)
    nav = "".join(f'<a href="{(rel + h) if not (h=="index.html") else (rel + "index.html")}"' + (' class="on"' if h == path else "") + f'>{esc(t)}</a>' for h, t in NAV)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL readiness hub</title><link rel="stylesheet" href="{rel}assets/readiness.css"></head><body>
<header><div class="wrap"><div class="brand">NFL readiness hub <span>· 2026 season · data as of 15 Nov 2026 (UTC)</span></div>
<nav>{nav}</nav></div></header>
<main class="wrap"><h1>{esc(title)}</h1><p class="lead">{lead}</p>{body}</main>
<footer class="wrap"><p>Research status only. Not betting advice. Every table row links to a source; a blank cell means the value could not be confirmed from an official source. Row-level injury data is held outside Git until the nfl.com terms are cleared (see <a href="{rel}pages/governance.html">Governance</a>).</p></footer>
</body></html>"""
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")

def table(headers, rows, cls="tw"):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="{cls}"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

def kpi(items):
    return '<div class="kpis">' + "".join(f'<div class="kpi"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in items) + "</div>"

# ---------- landing ----------
from collections import Counter
st = Counter(r[3] for r in C.REQUIREMENTS)
n_req = len(C.REQUIREMENTS)
f_count = len(C.FLAGS)
rows = []
for rid, cat, req, status, gate, clears, ev, src in C.REQUIREMENTS:
    rows.append([esc(rid), esc(cat), esc(req), badge(status), esc(gate), esc(clears), repo_link(ev), link(src, src.replace("https://","")[:60])])
land = f"""{kpi([("requirements tracked", n_req), ("done", st['Done']+st['Policy']), ("partial", st['Partial']), ("blocked", st['Blocked']),
  ("not started", st['Not started']), ("claims not reproduced / not verified", st['Claim not reproduced']+st['Not verified']), ("open decisions", st['Open decision']+st['Open']),
  ("flagged for review", f_count)])}
<section class="panel"><h2>Headline</h2><ul>
<li><b>Nothing is rewarded and nothing is staked.</b> No strategy is pre-registered with a validated record, no line is priced against a verified market, and no backtest number appears on any leaderboard.</li>
<li><b>One pre-registered forecast set is live (shadow only).</b> Singles shadow baseline v1 is frozen at commit <code>64a20e8</code> (2026-11-15T23:28:36Z). It issued {shadow['counts']['forecast']} Week 11 forecasts and withheld {shadow['counts']['withheld']} games whose Week 10 results were not confirmed final in the capture.</li>
<li><b>The Week 10 injury report was re-captured.</b> {agg['checks']['player_rows']} player rows across {agg['checks']['teams']} clubs and {agg['checks']['game_blocks']} matchups; {agg['checks']['injury_entries']} carry an injury entry. The brief's figure of 279 rows is not reproduced (Flag F-R02).</li>
<li><b>Removal of luck: not yet measurable.</b> Luck removal needs a control baseline run on a leaderboard with verified results and prices. Today: 0 leaderboard rows with controls, 0 graded forecasts (0 of 300 needed).</li>
<li><b>Legal gate.</b> nfl.com terms §1.3 restrict systematic retrieval without written consent (Flag F-R09). Row-level data is therefore held privately and only aggregates are published.</li>
</ul></section>
<section class="panel"><h2>Decision readiness: one row per requirement</h2>
<p class="note">Status, the gate that blocks it, and the number that would clear it. Evidence links point to the repository artifact; the source column links to the official page or repository record used. Sort is by register order (R01–R{n_req:02d}).</p>
{table(["ID","Area","Requirement","Status","Blocking gate","Number that would clear it","Evidence (repo)","Source"], rows)}
</section>
<section class="panel"><h2>Gates used in this table</h2><ul>
<li><b>G-PRICE</b> — a licensed or official price source with redistribution terms. Not identified (Q-R01).</li>
<li><b>G-N</b> — 300 graded games before any skill or reward claim (repository convention, Q-R06).</li>
<li><b>G-DEPTH</b> — an official depth-chart source verified for all 32 clubs (Q-R03).</li>
<li><b>G-GAMEBOOK</b> — official NFL Game Books captured for each game (Q-R15).</li>
<li><b>G-TERMS</b> — written consent or licence under nfl.com terms §1.3 (Q-R02).</li>
<li><b>G-SERIES</b> — at least two timestamped reads of the same report (R12).</li>
<li><b>G-PREREG</b> — a freeze commit recorded before the evaluation window opens.</li>
</ul></section>"""
page("index.html", "Decision readiness", "What the NFL work can and cannot support today, requirement by requirement. Built from official nfl.com pages read on 15 Nov 2026 and from the repository's own records. Blank values are unverified, not zero.", land)

# ---------- injuries ----------
team_rows = []
for t in agg["teams"]:
    team_rows.append([esc(t["team"]), esc(t["matchup"]), str(t["listed_rows"]), str(t["injury_entries"]), str(t["out"]), str(t["doubtful"]),
                      str(t["questionable"]), str(t["dnp_practice"]), str(t["dnp_with_blank_injury"]),
                      blank("not verified: no depth source"), blank("not verified: no depth source"), link(C.INJ, "nfl.com/injuries")])
chk = agg["checks"]
checks_rows = [[esc(k.replace("_"," ")), str(v), link(C.INJ, "nfl.com/injuries")] for k, v in chk.items()]
body = f"""{kpi([("player rows (official)", chk['player_rows']), ("clubs", chk['teams']), ("matchups", chk['game_blocks']), ("injury entries", chk['injury_entries']), ("Out", sum(t['out'] for t in agg['teams'])), ("DNP with blank injury", chk['dnp_with_blank_injury'])])}
<section class="panel"><h2>Per-club view (counts only)</h2>
<p class="note">Counts are computed from the official Week 10 report captured on 15 Nov 2026. Player names are withheld from this public page until the nfl.com terms are cleared. "Starters out" and "replacements named" are blank: no official depth source is verified (R06, R45). The brief's "net injury count" has no definition; the column shows injury entries (Q-R16).</p>
{table(["Club","Matchup (Week 10)","Listed rows","Injury entries","Out","Doubtful","Questionable","Practice DNP","DNP, blank injury","Starters out","Replacements named","Source"], team_rows)}
</section>
<section class="panel"><h2>Capture checks and drift alarm</h2>
<p>Captured {esc(agg['captured'])}. Private source SHA-256: <code>{esc(agg['private_source_sha256'])}</code>. Drift alarm: {('none (all pinned counts match)' if not agg['drift_alarm'] else esc(agg['drift_alarm']))}.</p>
{table(["Check","Value","Source"], checks_rows)}
</section>
<section class="panel"><h2>Flagged here (details on the Flagged for Review page)</h2><ul>
<li>F-R01: the brief's three blank Detroit cells read <b>Out</b> on the live page and in both repo captures.</li>
<li>F-R02: 279 (brief) vs 347 (this capture, all rows re-read live). A repo file with 347 rows differs from the live page in 14 rows.</li>
<li>F-R06: {chk['dnp_with_blank_injury']} rows are DNP with a blank injury cell. Blank does not mean available.</li>
<li>F-R04, F-R05 and F-R07: news headlines conflict with, or are not reflected in, the report for named players.</li>
</ul></section>"""
page("pages/injuries.html", "Injuries and depth (Week 10 official report)", "Official report counts for the 2026 Week 10 slate. One timestamped read, so no deltas yet. Starters out and replacements are blank until an official depth source is verified.", body)

# ---------- schedule & results ----------
W10 = [("Thu 12 Nov, 8:15 PM ET","WAS","24","NYG","21","Final"),("Sun 15 Nov, 9:30 AM ET","NE","10","DET","35","Final"),("Sun 15 Nov, 1:00 PM ET","KC","35","ATL","13","Final"),
       ("Sun 15 Nov, 1:00 PM ET","HOU","24","CLE","27","Final"),("Sun 15 Nov, 1:00 PM ET","MIN","30","GB","10","Final"),("Sun 15 Nov, 1:00 PM ET","MIA","22","IND","24","Final"),
       ("Sun 15 Nov, 1:00 PM ET","CAR","20","NO","17","Final"),("Sun 15 Nov, 1:00 PM ET","BUF","31","NYJ","12","Final"),("Sun 15 Nov, 1:00 PM ET","JAX","40","TEN","23","Final"),
       ("Sun 15 Nov, 4:05 PM ET","LAR","34","ARI","6","Live at capture (Q4)"),("Sun 15 Nov, 4:05 PM ET","SEA","21","LV","10","Live at capture (Q4)"),
       ("Sun 15 Nov, 4:25 PM ET","SF","24","DAL","19","Live at capture (Q3)"),("Sun 15 Nov, 8:20 PM ET","PIT","-","CIN","-","Not started at capture"),
       ("Mon 16 Nov, 8:15 PM ET","LAC","-","BAL","-","Not started at capture")]
w10_rows = [[esc(d), esc(a), esc(sa), esc(h), esc(sh), esc(s), link(C.W10, "nfl.com Week 10 schedule")] for d, a, sa, h, sh, s in W10]
w11_rows = []
fc = {(f["away"], f["home"]): f for f in shadow["forecasts"]}
for a, h, k in [(g["away"], g["home"], g["kickoff"]) for g in inp["week11_games"]]:
    if (a, h) in fc:
        f = fc[(a, h)]
        w11_rows.append([esc(k), f"{esc(a)} at {esc(h)}", "forecast issued", f"{f['p_home']:.3f} (home) / {f['p_away']:.3f} (away)", esc(f["fav_control_pick"]), link(C.W11, "nfl.com Week 11 schedule")])
    else:
        w = [x for x in shadow["withheld"] if x["away"] == a and x["home"] == h][0]
        w11_rows.append([esc(k), f"{esc(a)} at {esc(h)}", "withheld", blank(w["reason"]), blank("—"), link(C.W11, "nfl.com Week 11 schedule")])
body = f"""<section class="panel"><h2>Week 10 official scores (as shown on the schedule page)</h2>
<p class="note">Scores as printed on the official schedule page. Three games were live at capture and two had not started, so those scores are not final. Source: {link(C.W10)}</p>
{table(["Kickoff","Away","Pts","Home","Pts","Status","Source"], w10_rows)}
<p class="note">Teams on bye in Week 10 (official list): CHI (7-2), DEN (7-2), PHI (2-7), TB (3-6). 18 clubs final, 10 not yet final (32 − 18 − 4). Kickoff times from the official injury report page headings: {link(C.INJ)}</p></section>
<section class="panel"><h2>Week 11: 13 official matchups and forecast status</h2>
<p class="note">Times are the schedule's ET kickoffs. Venue is not transcribed (R23). The forecast column shows the shadow probability for the home club where it was issued.</p>
{table(["Kickoff (ET)","Matchup (away at home)","Forecast status","Home win probability","Favourite (control pick)","Source"], w11_rows)}</section>
<section class="panel"><h2>Schedule announcements</h2><p>The official Week 10 schedule page states that designated Week 16, 17 and 18 matchups will be scheduled later, with Week 16 matchups to be announced no later than immediately after Week 14, Week 17 no later than immediately after Week 15, and Week 18 after Week 17. It also cites the flexible-scheduling procedures. Dated announcements were not captured as separate items (R24). Source: {link(C.W10)}</p></section>"""
page("pages/schedule-results.html", "Schedule and results", "Official Week 10 scores and the Week 11 slate, with the shadow forecast status of each game.", body)

# ---------- shadow baseline ----------
rows_f = []
for f in shadow["forecasts"]:
    rows_f.append([esc(f"{f['away']} at {f['home']}"), esc(f["kickoff"]), f"{f['rating_away']:+.2f} / {f['rating_home']:+.2f}", f"{f['margin_home']:+.2f}", f"{f['p_home']:.3f}", f"{f['p_away']:.3f}", esc(f["fav_control_pick"]), esc(f["random_control_pick"]), link(C.STAND, "nfl.com standings")])
body = f"""<section class="panel"><h2>Registration</h2>
<p>Rule text and code are frozen at commit <code>64a20e8</code> (2026-11-15T23:28:36Z). The forecasts below were produced after that commit by <code>nfl-readiness/prereg/shadow_v1.py</code>. Read the rule: <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-readiness/prereg/SHADOW_BASELINE_v1.md" target="_blank" rel="noopener">SHADOW_BASELINE_v1.md</a>.</p>
<ul><li>Model: rating = (points for − points against) ÷ games (standings only). Home margin = rating difference (no home-field term). P(home) = Φ(margin ÷ 13.5). The 13.5-point sigma is an <b>unsourced assumption</b> (F-R10).</li>
<li>Controls per game: coin-flip (0.50 each side; Brier 0.25), favourites-only (higher rating), seeded random pick.</li>
<li>Skill claims: none. Gate: 300 graded games before any claim (Q-R06). Graded so far: 0.</li></ul></section>
<section class="panel"><h2>Issued forecasts ({shadow['counts']['forecast']})</h2>
{table(["Matchup","Kickoff (ET)","Rating away / home","Margin (home)","P(home)","P(away)","Favourite","Random control pick","Source"], rows_f)}</section>
<section class="panel"><h2>Withheld ({shadow['counts']['withheld']})</h2>
<p class="note">A game is withheld when either club's Week 10 result was not confirmed final in the capture. Re-run after the Week 10 schedule is fully confirmed.</p>
{table(["Matchup","Reason","Source"], [[esc(f"{w['away']} at {w['home']}"), blank(w["reason"]), link(C.W11, "nfl.com Week 11 schedule")] for w in shadow["withheld"]])}</section>
<section class="panel"><h2>What would change our mind (pre-registered, both sides)</h2><ul>
<li><b>For the model:</b> Brier-skill lower bound above 0 after 300 graded games, and above the favourites-only control.</li>
<li><b>Against the model:</b> upper bound below 0 after 300 graded games, or a worse Brier score than the coin-flip control on any 4 consecutive weeks.</li></ul></section>"""
page("pages/shadow-baseline.html", "Singles shadow baseline (pre-registered)", "A simple team-strength model, frozen before Week 11 kickoff. Shadow only: recorded and graded later, never staked.", body)

# ---------- governance ----------
gov = [
 ["Pre-registration", "A rule is frozen in git before the evaluation window opens; the commit hash is the registration. Shadow baseline v1 is registered at 64a20e8.", "In force", link(REPO_ROOT+"blob/main/nfl-readiness/prereg/SHADOW_BASELINE_v1.md", "SHADOW_BASELINE_v1.md")],
 ["Leaderboard rule", "No backtest number appears on the leaderboard. Only forecasts recorded before kickoff, with their freeze commit, may appear.", "In force", link(REPO_ROOT+"blob/main/nfl-readiness/prereg/SHADOW_BASELINE_v1.md", "SHADOW_BASELINE_v1.md")],
 ["Ranking", "Rank by benchmark-relative Brier skill with a game-cluster lower bound and a multiplicity adjustment. Season-long ROI is not a ranking basis.", "In force (no entrants)", link(C.TERMS, "nfl.com terms (context)")],
 ["Signal vs staking", "Signal is scored separately from staking. Staking is never allowed to rank a strategy alone.", "In force (prior record)", link(REPO_ROOT+"blob/main/COORDINATION.md", "COORDINATION.md (prior record)")],
 ["Demotion gate", "A live strategy whose Brier-skill lower bound falls below 0 after 300 games returns to paper.", "In force (no live strategies)", link(REPO_ROOT+"blob/main/nfl-book/data/gates.json", "nfl-book gates.json")],
 ["Price-data policy", "Draft: publish signal-only research (Brier and calibration) until a licensed price source with redistribution terms is recorded. No ROI until then.", "Draft — owner decision (SR-02)", link(C.W11, "nfl.com Week 11 schedule (no prices on page)")],
 ["Depth order", "Depth is never derived from jersey number, experience or salary. Depth comes only from a verified official depth source.", "In force", link(C.INJ, "nfl.com injury report")],
 ["Injury signal", "Injury enters a model as a change between timestamped reads, never as a level. Blank is unknown, not available.", "In force", link(C.INJ, "nfl.com injury report")],
 ["Public / private split", "Public pages show derived aggregates only (counts, indices, model output). Row-level data stays in a gitignored private store until the terms are cleared.", "In force", link(C.TERMS, "nfl.com terms §1.3")],
 ["nfl.com terms", "§1.3 limits use to personal, non-commercial, informational purposes and prohibits systematic retrieval to compile a database without express prior written consent. Read as a constraint, pending counsel.", "In force; legal review open (F-R09)", link(C.TERMS, "nfl.com terms")],
 ["Control baseline", "Every leaderboard run includes a coin-flip, favourites-only and random control.", "In force (shadow); leaderboard: none yet", link(REPO_ROOT+"blob/main/nfl-readiness/prereg/SHADOW_BASELINE_v1.md", "SHADOW_BASELINE_v1.md")],
 ["Claims and blanks", "A value that cannot be confirmed from an official source is left blank and flagged. Nothing is inferred or filled in.", "In force", link(C.INJ, "nfl.com injury report")],
]
body = f"""<section class="panel"><h2>Operating rules</h2><p class="note">Rules this hub applies to itself. Changing a rule needs a new version with its own commit. Internal rules have no official nfl.com page, so their source is the repository record that holds the rule text (labelled as such).</p>
{table(["Policy","Rule","Status","Source"], gov)}</section>"""
page("pages/governance.html", "Governance and rules", "The rules that decide what can be published, what can be ranked, and what can be staked.", body)

# ---------- suggestions ----------
sug_src = {"SR-01": C.TERMS, "SR-02": C.W11, "SR-03": C.INJ, "SR-04": C.INJ, "SR-05": REPO_ROOT+"blob/main/README.md", "SR-06": REPO_ROOT+"blob/main/nfl-readiness/prereg/SHADOW_BASELINE_v1.md",
           "SR-07": REPO_ROOT+"blob/main/nfl-book/data/results_feed.json", "SR-08": C.INJ, "SR-09": C.NEWS_SMITH, "SR-10": C.NEWS_HENLEY, "SR-11": C.NEWS_NACUA, "SR-12": C.INJ}
srows = []
for sid, title, why, opts, rec, verdict in C.SUGGESTIONS:
    srows.append([esc(sid), esc(title), esc(why), esc(opts[0]) + "<br>" + esc(opts[1]) + "<br>" + esc(opts[2]), esc(rec), blank("owner to choose"), link(sug_src[sid], "source")])
body = f"""<section class="panel"><h2>Suggestions for the owner</h2>
<p class="note">Choose one option per suggestion before anything is implemented. The "hub recommendation" is a suggestion, not a decision. The verdict column is blank on purpose.</p>
{table(["ID","Suggestion","Why (evidence / flag)","Options","Hub recommendation","Owner verdict","Source"], srows)}</section>"""
page("pages/suggestions.html", "Suggestions (choose before implementing)", "Twelve proposed paths to close the gaps on the readiness table. Each lists its options, the evidence behind it, and a blank verdict.", body)

# ---------- questions ----------
q_src = {"Q-R01": C.W11, "Q-R02": C.TERMS, "Q-R03": C.INJ, "Q-R04": C.INJ, "Q-R05": C.INJ, "Q-R06": REPO_ROOT+"blob/main/COORDINATION.md", "Q-R07": C.TERMS,
         "Q-R08": REPO_ROOT+"blob/main/COORDINATION.md", "Q-R09": C.W10, "Q-R10": C.NEWS_SMITH, "Q-R11": C.NEWS_HENLEY, "Q-R12": C.NEWS_HENDERSON,
         "Q-R13": C.INJ, "Q-R14": REPO_ROOT+"blob/main/nfl-book/data/results_feed.json", "Q-R15": C.INJ, "Q-R16": REPO_ROOT+"blob/main/COORDINATION.md"}
qrows = []
for qid, q, have, lack, ans, basis, blocks, disc in C.QUESTIONS:
    answer_cell = esc(ans) if ans else blank(basis)
    qrows.append([esc(qid), esc(q), esc(have), esc(lack), answer_cell, esc(blocks), esc(disc), link(q_src[qid], "source")])
body = f"""<section class="panel"><h2>Questions, information and answers</h2>
<p class="note">Answers are given only where the official text supports them. Otherwise the answer is blank and the reason is stated. "What blocks" lists the requirement IDs in the readiness table.</p>
{table(["ID","Question","What we have","What we lack","Answer","Blocks","How to discover it","Source"], qrows)}</section>"""
page("pages/questions.html", "Questions, information and answers", "What must be known before any decision can be made, what is known, and what is missing.", body)

# ---------- executive summary ----------
body = f"""<section class="panel"><h2>Where things stand</h2><ul>
<li><b>The official record is consistent.</b> The Week 10 report, the standings and the schedule reconcile: league points for equal points against (6,664 each); wins equal losses (144 each). 9 Week 10 games final (18 clubs), 3 live at capture, 2 not started, 4 clubs on bye (official list).</li>
<li><b>Injuries are captured, depth is not.</b> {agg['checks']['injury_entries']} injury entries across {agg['checks']['teams']} clubs; no club's official depth order has been verified in this session. Starters out and replacements stay blank.</li>
<li><b>Prices are the gate.</b> No official price source has been identified. Without one, no ROI, edge or closing-line claim can be computed.</li>
<li><b>Terms are a second gate.</b> nfl.com §1.3 restricts systematic retrieval without written consent. The hub publishes aggregates only.</li>
<li><b>One model is pre-registered, in shadow.</b> Five Week 11 forecasts are issued; eight are withheld pending confirmation. Nothing is graded yet.</li>
<li><b>The brief's numbers do not all reproduce.</b> The 279 row count, the Detroit blanks, and the Seattle and Cincinnati claims are not reproduced (flags F-R01 to F-R03).</li></ul></section>
<section class="panel"><h2>What is decided</h2><ul>
<li>No strategy is ranked, rewarded or staked.</li>
<li>Row-level injury data is private; public pages carry counts only.</li>
<li>Depth is never inferred from jersey number, experience or salary.</li></ul></section>
<section class="panel"><h2>What the owner must decide first</h2><ul>
<li>Terms: consent, licence, or manual sampling (SR-01).</li>
<li>Price policy: signal-only research, or a licence (SR-02).</li>
<li>Depth route: verify 32 official depth pages, find snap counts, or drop depth features (SR-03).</li>
<li>Canonical namespace among the 23 NFL folders (SR-05).</li></ul></section>
<section class="panel"><h2>Status counts</h2>
{table(["Status","Count","Meaning","Source"], [[badge(s), str(c), esc(m), link(REPO_ROOT+"blob/main/nfl-readiness/engine/content.py", "register: content.py")] for s, c, m in [
 ("Done", st["Done"]+st["Policy"], "built, or a rule in force"), ("Partial", st["Partial"], "some of the requirement exists"),
 ("Blocked", st["Blocked"], "needs a gate that is not yet met"), ("Not started", st["Not started"], "no work yet"),
 ("Open decision / claim not reproduced / not verified", st["Open decision"]+st["Claim not reproduced"]+st["Not verified"]+st["Open"], "needs the owner or a source")]])}
<p class="note">Full register: <a href="../index.html">Landing</a>. Sources: <a href="sources.html">Sources</a>. Items the owner should review: <a href="flagged.html">Flagged for Review</a>.</p></section>"""
page("pages/executive-summary.html", "Executive summary", "The short version: what the NFL work can support now, what it cannot, and the decisions needed first. Not betting advice.", body)

# ---------- flagged ----------
frows = []
for fid, title, detail, srcs, sev in C.FLAGS:
    srcs_html = "<br>".join(link(u, lab) for lab, u in srcs)
    frows.append([esc(fid), esc(title), esc(detail), srcs_html, esc(sev), ('<span class="badge ok">resolved</span>' if fid=="F-R14" else '<span class="badge warn">needs review</span>')])
body = f"""<section class="panel"><h2>Flagged for Review</h2>
<p class="note">Items that do not block publishing. Each carries its sources so you can check them. Status for every flag: <b>needs review</b>.</p>
{table(["ID","Irregularity","Detail","Sources","Severity","Status"], frows)}</section>"""
page("pages/flagged.html", "Flagged for Review", "Irregularities, unverified claims and conflicts found while building this hub. Each one has its source. None blocks publishing.", body)

# ---------- sources ----------
srow = [[esc(sid), esc(t), link(u, u), esc(how), esc(use)] for sid, t, u, how, use in C.SOURCES]
body = f"""<section class="panel"><h2>Sources</h2><p class="note">Official nfl.com pages are the only sources for values. Headlines were read from link text on the injury page; the article bodies were not opened.</p>
{table(["ID","Source","Link","How it was read","Used for"], srow)}</section>"""
page("pages/sources.html", "Sources", "Every official page and repository record this hub uses, with how it was read.", body)

# ---------- assets ----------
(ROOT / "assets").mkdir(exist_ok=True)
(ROOT / "assets" / "readiness.css").write_text("""
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#1d2330;background:#f5f7fa}
.wrap{max-width:1280px;margin:0 auto;padding:0 18px}header{background:#0d2440;color:#fff;padding:12px 0}
.brand{font-weight:700;font-size:17px}.brand span{font-weight:400;opacity:.75;font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:8px}nav a{color:#cfe3ff;text-decoration:none;font-size:13px;padding:3px 6px;border-radius:4px}
nav a.on,nav a:hover{background:#1c3d66;color:#fff}main{padding:18px 0 8px}h1{font-size:24px;margin:6px 0}h2{font-size:18px;margin:4px 0 8px}
.lead{color:#4a5566;margin:0 0 14px}.panel{background:#fff;border:1px solid #dde3ec;border-radius:8px;padding:14px 16px;margin:14px 0}
.note{color:#5a6577;font-size:13px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.kpi{background:#fff;border:1px solid #dde3ec;border-radius:8px;padding:10px 12px}.kpi b{display:block;font-size:22px;color:#0d2440}.kpi span{font-size:12px;color:#5a6577}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #e6ebf2;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef3f9;position:sticky;top:0;font-weight:600}a{color:#0b5cad}code{background:#eef3f9;padding:1px 4px;border-radius:3px}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600;white-space:nowrap}
.badge.ok{background:#dcf5e4;color:#14672e}.badge.warn{background:#fff1cc;color:#7a5200}.badge.bad{background:#fde0de;color:#8a1c12}.badge.muted{background:#e9edf3;color:#4a5566}
.blank{color:#8a94a6;font-style:italic}footer{color:#5a6577;font-size:12px;padding:12px 0 24px}
""", encoding="utf-8")
(ROOT / ".nojekyll").write_text("")
print("built pages:", len(NAV), "| requirements:", n_req, dict(st))

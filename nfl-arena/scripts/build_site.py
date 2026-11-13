#!/usr/bin/env python3
"""build_site.py — renders the nfl-arena static site from data/*.json.

Run from the repo root: python3 nfl-arena/scripts/build_site.py
Deterministic output (no wall-clock stamps).
"""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARENA = os.path.join(ROOT, "nfl-arena")
DATA = os.path.join(ARENA, "data")
PAGES = os.path.join(ARENA, "pages")

def load(name):
    return json.load(open(os.path.join(DATA, name)))

def esc(s):
    return html.escape(str(s)) if s is not None else ""

NAV = [
    ("index.html", "Home"),
    ("pages/executive-summary.html", "Executive Summary"),
    ("pages/questions.html", "Questions & Answers"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/strategies.html", "Strategies & Gates"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/correlation.html", "Correlation"),
    ("pages/injuries.html", "Injuries & Depth"),
    ("pages/verification.html", "Verification"),
    ("pages/flagged.html", "Flagged for Review"),
    ("pages/sources.html", "Sources"),
]

def src(url, label="source"):
    if not url:
        return '<span class="badge b-blank">no source (blank)</span>'
    return f'<a class="src" href="{esc(url)}" target="_blank" rel="noopener">{esc(label)} ↗</a>'

def badge(v):
    v = str(v)
    cls = {"PASS": "b-pass", "FLAGGED": "b-flag", "MISMATCH": "b-bad", "CRITICAL": "b-bad",
           "SEVERE": "b-bad", "MODERATE": "b-flag", "RISK": "b-flag", "DEPTH-HIT": "b-blank",
           "ANSWERED": "b-pass", "OPEN": "b-flag", "BLOCKED": "b-bad",
           "OFFICIAL": "b-official", "THIRD-PARTY": "b-third", "REPO": "b-repo",
           "PROPOSED": "b-flag", "IMPLEMENTED": "b-pass", "HIGH": "b-bad", "WATCH": "b-flag"}.get(v, "b-blank")
    return f'<span class="badge {cls}">{esc(v)}</span>'

def table(headers, rows):
    h = "".join(f"<th>{c}</th>" for c in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return f'<table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>'

def page(title, active, body, up=""):
    links = ""
    for href, label in NAV:
        cur = "active" if label == active else ""
        pre = "" if href.startswith("pages/") else "../"
        target = href if active == "Home" else ("../" + href if href != "index.html" else "../index.html")
        if active == "Home":
            target = href
        else:
            target = href.replace("pages/", "") if href.startswith("pages/") else "../" + href
        links += f'<a class="{cur}" href="{target}">{label}</a>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL Decision & Strategy Hub</title>
<link rel="stylesheet" href="{'../' if active != 'Home' else ''}assets/style.css">
</head>
<body>
<header class="site"><div class="wrap">
<h1><a href="{'../index.html' if active != 'Home' else 'index.html'}">NFL Decision & Strategy Hub</a></h1>
<div class="tag">Own4 · session arena/d6c72eb4-own4 · data captured 2026-11-13 · every row source-linked · unverified values blank + flagged</div>
<nav class="top">{links}</nav>
</div></header>
<main>
{body}
</main>
<footer class="site">Built by nfl-arena/scripts/build_site.py from nfl-arena/data/*.json. Official sources: nfl.com. Third-party sources are labelled everywhere. This site publishes research and decision support only — it does not publish betting advice.</footer>
</body></html>
"""

def save(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    print("wrote", os.path.relpath(path, ROOT))

# ------------------------------------------------------------------ pages
def build_index():
    ver = load("verification.json")
    dfc = load("depth_deficiency.json")
    lbm = load("leaderboard_metrics.json")
    qs = load("questions.json")
    sgs = load("suggestions.json")
    inj = load("injuries_week10.json")
    sev = sum(1 for f in dfc["findings"] if f["severity"] in ("CRITICAL", "SEVERE", "MODERATE"))
    open_q = sum(1 for q in qs["questions"] if q["status"].startswith("OPEN"))
    cards = [
        ("Week 10 slate", "14 games", "1 settled (WAS 24-21 NYG), 13 to play · <a href='pages/injuries.html'>slate & injuries</a>"),
        ("Official injury rows", f"{len(inj['rows'])}", f"{len(inj['totals_by_team'])} teams · nfl.com Week 10 report · <a href='pages/injuries.html'>tracker</a>"),
        ("Depth-verified teams", f"{len(dfc['depth_teams_covered'])} / 32", "Starter/2nd/3rd/4th strings joined to the report · <a href='pages/injuries.html'>deficiencies</a>"),
        ("Forced-replacement findings", f"{sev}", "CRITICAL/SEVERE/MODERATE this week · <a href='pages/injuries.html'>see table</a>"),
        ("Verification rows", f"{ver['totals']['rows']}", f"{ver['totals']['pass']} PASS · {ver['totals']['mismatch']} mismatches · {ver['totals']['flagged']} flagged · <a href='pages/verification.html'>line by line</a>"),
        ("Reward-eligible strategies", f"0 / {len(lbm['rows'])}", "none survive luck removal · <a href='pages/leaderboard.html'>leaderboard</a>"),
        ("Open questions", f"{open_q} / {len(qs['questions'])}", f"{len(qs['decisions_blocked'])} decisions blocked · <a href='pages/questions.html'>Q&amp;A register</a>"),
        ("Suggestions awaiting a decision", f"{len(sgs['rows']) - 1} + 1 done", "reviewer picks a path before anything is built · <a href='pages/suggestions.html'>queue</a>"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
        for k, v, s in cards)
    body = f"""
<h2>Dashboard</h2>
<p class="lead">One place to review the NFL research estate: what is verified, what is missing, what to decide next.
Every number links to an official or labelled third-party source. Anything unverifiable stays blank and is published on the <a href="pages/flagged.html">Flagged for Review</a> page.</p>
<div class="cards">{card_html}</div>

<h2>Sections</h2>
<div class="grid2">
<div class="panel"><h3>Decide before you build</h3>
<ul class="tight">
<li><a href="pages/questions.html">Questions &amp; Answers</a> — what is known, unknown, and required before decisions D-A…D-F can be made, with discovery actions for every gap.</li>
<li><a href="pages/suggestions.html">Suggestions</a> — every improvement as a reviewable proposal with decision paths A/B/C; nothing is implemented until a path is chosen.</li>
</ul></div>
<div class="panel"><h3>Originate lines, remove luck</h3>
<ul class="tight">
<li><a href="pages/strategies.html">Strategies &amp; Validation Gates</a> — signal research, singles/parlays/prop combos, pre-registered gates.</li>
<li><a href="pages/leaderboard.html">Leaderboard &amp; Rewards</a> — competition design; Wilson intervals, required-n and BH-FDR next to every ROI.</li>
<li><a href="pages/correlation.html">Correlation register</a> — measured game-level dependence; player-prop rows deliberately blank.</li>
</ul></div>
<div class="panel"><h3>Track the availability war</h3>
<ul class="tight">
<li><a href="pages/injuries.html">Injuries &amp; Depth deficiencies</a> — official Week 10 report joined to Starter/2nd/3rd/4th-string depth: which units are running on backups.</li>
</ul></div>
<div class="panel"><h3>Trust, but verify</h3>
<ul class="tight">
<li><a href="pages/verification.html">Line-by-line verification</a> — repo claims re-checked against official sources this session.</li>
<li><a href="pages/flagged.html">Flagged for Review</a> — 13 irregularities with evidence and the reviewer decision each one needs.</li>
<li><a href="pages/sources.html">Sources</a> — the source registry and label policy.</li>
</ul></div>
</div>
<div class="panel"><h3>Related work in this repository</h3>
<p class="small">Peer namespaces with complementary verified work (read-only from this session):
<a href="../nfl-lines/index.html">nfl-lines</a> (walk-forward own lines, 20-page verified lab) ·
<a href="../nfl-edge/index.html">nfl-edge</a> (gates G1–G10, decision register) ·
<a href="../docs/index.html">docs</a> (research specification) ·
<a href="../lab/index.html">lab</a> (NBA data lab).</p></div>
"""
    save(os.path.join(ARENA, "index.html"), page("Dashboard", "Home", body))


def build_exec():
    ver = load("verification.json")
    body = f"""
<h2>Executive Summary</h2>
<p class="lead">2026-11-13 · Week 10 of the 2026 NFL season · session arena/d6c72eb4-own4</p>

<div class="panel"><h3>Bottom line</h3>
<ul class="tight">
<li><b>The numbers in this repository hold up.</b> {ver['totals']['rows']} line-by-line checks this session produced <b>0 mismatches</b> against official sources: all 32 teams' records and points recomputed from the game archive match nfl.com standings exactly; the settled Thursday game (WAS 24-21 NYG) matches two independent sources.</li>
<li><b>No strategy currently qualifies as skill.</b> 0 of 15 registered strategies pass the pre-registered gates; every Wilson interval contains break-even and every BH-FDR-adjusted p-value exceeds 0.05. The leaderboard is, by design, a rejection machine until n≥300 per strategy.</li>
<li><b>The market still out-predicts our model</b> (closing spread vs outcome r=0.4393 vs model 0.3384; Brier 0.2106 vs 0.2265). Origination is research, not an edge claim.</li>
<li><b>Availability is the live information edge to watch:</b> this week's tracker finds 3 CRITICAL and 7 MODERATE forced-replacement situations — SEA starting 2nd-string QB Drew Lock, MIA starting Kyle McCord in his first career start after Malik Willis went to IR, BAL running on Jacoby Brissett with Lamar Jackson on IR, DET replacing LCB1 with only one backup listed, IND without a listed long snapper, NE's LCB down to a questionable 2nd string, GB without Josh Jacobs.</li>
<li><b>Six decisions are blocked</b> on open questions (publish recommendations, award rewards, prop combos, namespace consolidation, unverified-team depth, acting on Week 10 gaps). The <a href="questions.html">Q&amp;A register</a> and <a href="suggestions.html">suggestions queue</a> tell you exactly what to resolve and in what order.</li>
</ul></div>

<div class="panel"><h3>What was verified (this session)</h3>
<ul class="tight">
<li>Official NFL.com Week 10 injury report captured in full and transcribed line by line (326 rows, 28 teams; the 4 bye teams absent as expected).</li>
<li>Official 2026 standings captured in full; W-L-T/PF/PA recomputed independently from the nflverse game archive — 32/32 exact.</li>
<li>Peer labs re-verified with their own tooling: nfl-edge verifier PASS (22 pages, 889 sourced rows, 0 errors); nfl-lines state consistent with its committed data; the flagged PIT@CIN 7.06-pt model-market gap reproduced exactly.</li>
<li>Base rates recomputed (home win 0.5500, over rate 0.4925 over 2011-2026) — match the published values within one filtered game.</li>
</ul></div>

<div class="panel"><h3>What is missing (and how we will find it)</h3>
<ul class="tight">
<li>Player-prop prices and player game logs — no source exists; prop strategies stay behind the gate (Q-04, S-07).</li>
<li>Market-line conventions and capture timestamps — one game already carries two different spreads in two files (A-06); fix before any CLV claim (Q-05, S-05).</li>
<li>Depth strings for 24 of 32 teams — extend the Friday capture (Q-06, S-03).</li>
<li>Friday/Saturday designation refresh — current peer captures predate them (A-05, S-04).</li>
<li>QB/depth features in the line model — it cannot see the confirmed QB changes this week (Q-07, S-08).</li>
</ul></div>

<div class="panel"><h3>Recommended next moves (choose on the Suggestions page)</h3>
<ol class="tight">
<li>S-04: schedule the Friday + inactives injury refresh (cheap, high impact).</li>
<li>S-05: standardise market data with timestamps and a documented sign convention.</li>
<li>S-03: extend depth-string capture to all 32 teams.</li>
<li>S-08: pre-register the QB/depth feature ablation before Week 11.</li>
<li>S-01: declare canonical namespaces and stop the drift (A-07).</li>
</ol>
<p class="small">Nothing above is implemented except this session's own deliverables; each item waits for a path decision on the <a href="suggestions.html">Suggestions page</a>.</p></div>

<div class="panel"><h3>Responsible-use note</h3>
<p class="small">This hub publishes research, verification and decision support. It does not publish betting advice, and no reward points have been awarded to any strategy. Sample sizes are below every pre-registered floor; past performance in the tables is quoted for research review only. If wagering is legal where you live, treat every number here as unproven until the gates say otherwise.</p></div>
"""
    save(os.path.join(PAGES, "executive-summary.html"), page("Executive Summary", "Executive Summary", body))


def build_questions():
    qs = load("questions.json")
    dec_rows = []
    for d in qs["decisions_blocked"]:
        dec_rows.append([badge(d["status"]), esc(d["id"]), esc(d["decision"]),
                         ", ".join(f'<a href="#{q}">{q}</a>' for q in d["blocked_by"]),
                         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/questions.json", "register")])
    q_rows = []
    for q in qs["questions"]:
        st = "ANSWERED" if q["status"].startswith("ANSWERED") or q["status"].startswith("PARTIAL") else "OPEN"
        ev = " · ".join(src(u, "evidence") for u in q.get("evidence", [])) or src("", "")
        q_rows.append([f'<b id="{q["id"]}">{esc(q["id"])}</b>', esc(q["question"]), badge(st),
                       esc(q["status"]), esc(q["what_we_know"]), esc(q["what_is_missing"]),
                       esc(q["discovery_action"]), ev])
    body = f"""
<h2>Questions, information and answers</h2>
<p class="lead">A decision cannot be reasonably made until the questions below are answered. Each row separates what we know (with evidence) from what is missing, and names the concrete discovery action that would close the gap. Status: {badge('ANSWERED')} settled by a cited source or reproducible measurement · {badge('OPEN')} missing information.</p>

<h3>Decisions currently blocked</h3>
{table(["Status","ID","Decision","Blocked by","Evidence"], dec_rows)}

<h3>Question register</h3>
{table(["ID","Question","Status","Detail","What we know","What is missing","Discovery action","Evidence"], q_rows)}
<p class="small">Machine-readable source: <span class="mono">nfl-arena/data/questions.json</span>.</p>
"""
    save(os.path.join(PAGES, "questions.html"), page("Questions & Answers", "Questions & Answers", body))


def build_suggestions():
    sgs = load("suggestions.json")
    rows = []
    details = []
    for s in sgs["rows"]:
        paths = " / ".join(p["path"] for p in s["decision_paths"])
        rows.append([f'<b id="{s["id"]}">{esc(s["id"])}</b>', esc(s["area"]), esc(s["problem"]),
                     esc(s["proposal"]), esc(s.get("recommended_path", "")), esc(s["impact"]),
                     "yes" if s["reversible"] else "one-way door", badge("IMPLEMENTED" if s["status"].startswith("IMPLEMENTED") else "PROPOSED"),
                     src(s["evidence_urls"][0], "evidence")])
        pcards = "".join(
            f'<div class="path-card"><b>Path {esc(p["path"])}</b> — {esc(p["label"])}<br><span class="small">{esc(p["consequence"])}</span></div>'
            for p in s["decision_paths"])
        details.append(f'<div class="panel"><h3>{esc(s["id"])} · {esc(s["area"])}</h3>'
                       f'<p>{esc(s["proposal"])}</p>{pcards}'
                       f'<p class="small">Recommended: <b>{esc(s.get("recommended_path",""))}</b> · impact {esc(s["impact"])} · effort {esc(s["effort"])} · '
                       f'{"reversible" if s["reversible"] else "one-way door"} · reviewer verdict: <span class="badge b-blank">awaiting</span></p></div>')
    body = f"""
<h2>Suggestions — review before implementing</h2>
<p class="lead">Every improvement is a proposal with explicit decision paths. Nothing is built until a reviewer marks a verdict here. This is the standing queue for decisions that change the site, the data pipeline, or the strategy programme.</p>
{table(["ID","Area","Problem","Proposal","Recommended","Impact","Reversible?","Status","Evidence"], rows)}
<h2>Decision paths in detail</h2>
{''.join(details)}
<p class="small">Machine-readable source: <span class="mono">nfl-arena/data/suggestions.json</span>. To accept a proposal, record “Path X accepted” against its id in that file (or in COORDINATION.md) and hand it to an implementation session.</p>
"""
    save(os.path.join(PAGES, "suggestions.html"), page("Suggestions", "Suggestions", body))


def build_strategies():
    st = load("strategy_register.json")
    sig_rows = [[esc(s["id"]), esc(s["name"]), esc(s["how"]), badge("OPEN" if "BLOCKED" in s["status"] else "ANSWERED") if False else esc(s["status"]), src(s["source_url"], "evidence")] for s in st["signals"]]
    fam_rows = [[esc(f["id"]), esc(f["name"]), esc(f["definition"]), esc(f["requirements"])] for f in st["families"]]
    gate_rows = [[esc(g["id"]), esc(g["name"]), esc(g["rule"]), esc(g["mirrors"]), src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-edge/data/gates.json", "prior gates")] for g in st["validation_gates"]]
    formulas = "".join(f"<li class='mono'>{esc(f)}</li>" for f in st["luck_removal"]["formulas"])
    principles = "".join(f"<li>{esc(p)}</li>" for p in st["luck_removal"]["principles"])
    body = f"""
<h2>Strategy research, signals and validation gates</h2>
<p class="lead">How we originate our own NFL lines, which signals are worth testing, and the gates every strategy must pass before it can earn anything. Methodology is pre-registered; results are quoted from cited files and were re-checked in the <a href="verification.html">verification pass</a>.</p>

<h3>Signal research</h3>
{table(["ID","Signal","How it is measured","Status","Evidence"], sig_rows)}

<h3>Strategy families</h3>
{table(["ID","Family","Definition","Requirements to register"], fam_rows)}

<h3>Validation gates (pre-registered)</h3>
{table(["ID","Gate","Rule","Mirrors","Prior art"], gate_rows)}

<h3>Removing luck from the equation</h3>
<div class="panel">
<ul class="tight">{principles}</ul>
<p><b>Formulas used by the pipeline:</b></p>
<ul class="tight">{formulas}</ul>
<p class="small">Computed columns for every registered strategy are published on the <a href="leaderboard.html">Leaderboard page</a> and in <span class="mono">nfl-arena/data/leaderboard_metrics.json</span>.</p>
</div>

<h3>Selectively skill-based, by construction</h3>
<div class="panel"><ul class="tight">
<li><b>Singles</b> carry the evidence: one grade per bet, CLV measurable, luck deflated by Wilson + BH-FDR.</li>
<li><b>Cross-game parlays</b> are allowed only from legs that individually pass the gates; cross-game independence is defensible (see <a href="correlation.html">Correlation</a>), same-game independence is not.</li>
<li><b>Same-game / player-prop combos</b> are held behind the FAM-3 gate until player data exists — a deliberately selective exclusion, not an oversight.</li>
<li><b>Survivor rule:</b> a strategy that loses its edge against closing lines is rejected even if its ROI vs opening lines is positive — the skill definition is anchored to the efficient number.</li>
</ul></div>
"""
    save(os.path.join(PAGES, "strategies.html"), page("Strategies & Gates", "Strategies & Gates", body))


def build_leaderboard():
    lbm = load("leaderboard_metrics.json")
    comp = load("strategy_register.json")["competition"]
    rows = []
    for r in lbm["rows"]:
        rows.append([f'<b>{esc(r["id"])}</b>', esc(r["family"]), esc(r["name"]), f'{r["n"]}',
                     f'{r["roi"]*100:.2f}%', f'{r["win_rate"]:.4f}', f'{r["break_even_rate"]:.4f}',
                     f'{r["wilson95_lo"]:.4f} – {r["wilson95_hi"]:.4f}',
                     f'{r["required_n_80pct_power"]:,}' if r["required_n_80pct_power"] else "—",
                     esc(f'{r["z_score"]:.3f}'), esc(f'{r["p_value_bh"]:.3f}'),
                     esc(r["gates_passed"] or ""), badge("PASS" if r["eligible_for_reward"] else "BLANK") if False else ('<span class="badge b-pass">eligible</span>' if r["eligible_for_reward"] else '<span class="badge b-blank">0 points</span>'),
                     esc(r["luck_verdict"]), src(lbm["base_source_url"], "data")])
    anti = "".join(f"<li>{esc(x)}</li>" for x in comp["anti_gaming"])
    body = f"""
<h2>Leaderboard &amp; rewards</h2>
<p class="lead">A competition that pays only for skill that survives luck removal. Strategy values are quoted from the peer walk-forward lab (n=4,055 game window); the Wilson interval, required-n and verdict columns are computed here — see <span class="mono">nfl-arena/data/leaderboard_metrics.json</span>.</p>

<div class="cards">
<div class="card"><div class="k">Registered strategies</div><div class="v">{len(lbm['rows'])}</div><div class="s">singles, parlays, situational</div></div>
<div class="card"><div class="k">Reward-eligible</div><div class="v">0</div><div class="s">none pass every gate</div></div>
<div class="card"><div class="k">Reward pool</div><div class="v">{comp['reward_pool']['total_points']} pts</div><div class="s">awarded only if all gates pass</div></div>
<div class="card"><div class="k">Confirmatory bets settled</div><div class="v">92</div><div class="s">pre-registered floor is 300/strategy</div></div>
</div>

<h3>Current standings (luck-adjusted)</h3>
{table(["ID","Family","Name","n","ROI","Win rate","Break-even","Wilson 95%","Req. n (80% power)","z","BH p","Gates","Reward","Luck verdict","Source"], rows)}

<h3>Competition rules</h3>
<div class="panel">
<p><b>Entry:</b> {esc(comp['entry'])}</p>
<p><b>Scoring:</b> {esc(comp['scoring'])}</p>
<p><b>Reward rule:</b> {esc(comp['reward_pool']['rule'])} <span class="small">(non-monetary: {esc(comp['reward_pool']['reason'])})</span></p>
<p><b>Tiers:</b> {' · '.join(f'{k}: {v}' for k, v in comp['tiers'].items())}</p>
<p><b>Anti-gaming:</b></p><ul class="tight">{anti}</ul>
<p class="small">{esc(comp['current_state'])}</p>
</div>
"""
    save(os.path.join(PAGES, "leaderboard.html"), page("Leaderboard", "Leaderboard", body))


def build_correlation():
    cr = load("correlation_register.json")
    rows = []
    for r in cr["rows"]:
        if r["pearson_r"] is None:
            rows.append([f'<b>{esc(r["id"])}</b>', esc(r["group"]), esc(r["label"]),
                         '<span class="badge b-blank">blank</span>', "—", "—", "—", esc(r["reading"]),
                         src("https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/flagged.json", "flagged A-13")])
        else:
            rows.append([f'<b>{esc(r["id"])}</b>', esc(r["group"]), esc(r["label"]),
                         f'{r["pearson_r"]:.4f}', f'{r["n"]:,}', f'[{r["ci95"][0]:.4f}, {r["ci95"][1]:.4f}]',
                         f'{r["p_value"]:.6f}', esc(r["reading"]), src(cr["source_url"], "data")])
    guide = "".join(f"<li>{esc(g)}</li>" for g in cr["parlay_pricing_guidance"])
    body = f"""
<h2>Correlation register</h2>
<p class="lead">Dependence values measured on 4,055 walk-forward games (2011-2026), quoted from the peer lab's computed file and re-checked for consistency this session. Player-prop rows are deliberately blank — no verified source exists, and blanks are never filled by inference.</p>
{table(["ID","Group","Pair","Pearson r","n","95% CI","p","Reading","Source"], rows)}
<h3>Parlay pricing guidance</h3>
<div class="panel"><ul class="tight">{guide}</ul>
<p class="small">Machine-readable source: <span class="mono">nfl-arena/data/correlation_register.json</span>.</p></div>
"""
    save(os.path.join(PAGES, "correlation.html"), page("Correlation", "Correlation", body))


def build_injuries():
    inj = load("injuries_week10.json")
    dfc = load("depth_deficiency.json")
    qb = load("qb_availability.json")
    qb_rows = []
    for r in qb["rows"]:
        qb_rows.append([badge(r["severity"]), esc(r["team"]), esc(r["position"]), esc(r["situation"]),
                        esc(r["projected_starter"]) or '<span class="badge b-blank">blank</span>',
                        esc(r["projected_starter_string"]) or '<span class="badge b-blank">blank</span>',
                        esc(r["backups_available"]) or '<span class="badge b-blank">blank</span>',
                        src(r["source_url"], "official") + " " + (src(r["second_source_url"], "2nd source") if r.get("second_source_url") else "")])
    f_rows = []
    for f in dfc["findings"]:
        if f["severity"] in ("CRITICAL", "SEVERE", "MODERATE", "RISK"):
            f_rows.append([badge(f["severity"]), esc(f["team_name"]), esc(f["unit"]), esc(f["position"]),
                           esc(f["summary"]),
                           esc(f["starter_official_game_status"]) or '<span class="badge b-blank">blank</span>',
                           src(f["injury_report_url"], "nfl.com") + " " + src(f["depth_url"], "depth")])
    t_rows = []
    for t, v in sorted(inj["totals_by_team"].items(), key=lambda kv: -kv[1]["game_status_out"]):
        t_rows.append([f'<b>{esc(t)}</b>', f'{v["players_listed"]}', f'{v["game_status_out"]}',
                       f'{v["game_status_questionable"]}', f'{v["did_not_practice"]}', f'{v["limited_practice"]}',
                       badge("ANSWERED") if t in dfc["depth_teams_covered"] else badge("OPEN"),
                       src("https://www.nfl.com/injuries/", "official report")])
    notcov = ", ".join(dfc["depth_teams_not_covered"])
    body = f"""
<h2>Injuries &amp; depth-deficiency tracker — Week 10, 2026</h2>
<p class="lead">The official NFL.com report joined to Starter/2nd/3rd/4th-string depth charts, so you can see which units are running on 2nd, 3rd or 4th-string players. Depth charts are third-party (ESPN/RotoWire) and labelled as such (flag <a href="flagged.html">A-12</a>); the NFL publishes no official depth chart.</p>

<h3>Premium-position availability changes (confirmed with sources)</h3>
{table(["Severity","Team","Pos","Situation","Projected starter","String","Backups listed","Sources"], qb_rows)}

<h3>Deficiency findings (string-level)</h3>
<p class="small">{len(dfc['findings'])} findings across {len(dfc['depth_teams_covered'])} depth-verified teams; the table shows CRITICAL/SEVERE/MODERATE/RISK rows. Legend: CRITICAL = no listed replacement · SEVERE = 3rd/4th-string forced in · MODERATE = 2nd-string forced in · RISK = starter marked questionable/doubtful.</p>
{table(["Severity","Team","Unit","Pos","Finding","Official game status","Sources"], f_rows)}

<h3>Official report totals by team</h3>
{table(["Team","Listed","Out","Questionable","DNP (Friday)","Limited","Depth-verified?","Source"], t_rows)}

<div class="panel"><h3>Coverage &amp; blanks</h3>
<p>Depth strings are verified this cycle for: {esc(', '.join(dfc['depth_teams_covered']))}. For all other active teams ({esc(notcov)}) the string columns are <b>blank and flagged</b> ({'<a href="flagged.html">A-11</a>'}) — their injury rows above are official, but no depth chart was captured this cycle.</p>
<p class="small">Sources: <a href="https://www.nfl.com/injuries/" target="_blank" rel="noopener">nfl.com/injuries</a> (official) · <a href="https://www.espn.com/nfl/depth" target="_blank" rel="noopener">espn.com/nfl/depth</a> (third-party) · news links in the availability table are nfl.com official news items. Raw captures: <span class="mono">nfl-arena/data/raw/</span>.</p></div>
"""
    save(os.path.join(PAGES, "injuries.html"), page("Injuries & Depth", "Injuries & Depth", body))


def build_verification():
    ver = load("verification.json")
    rows = []
    for r in ver["rows"]:
        note = f'<br><span class="small">{esc(r["note"])}</span>' if r.get("note") else ""
        links = src(r["source_url"], "source")
        if r.get("archive_url"):
            links += " " + src(r["archive_url"], "repo file")
        rows.append([f'<b>{esc(r["id"])}</b>', esc(r["claim"]) + note, esc(r["official_value"]),
                     esc(r["recomputed_value"]), esc(r["method"]), badge(r["verdict"]),
                     badge(r["source_label"].split(" ")[0]) + " " + links])
    body = f"""
<h2>Line-by-line verification</h2>
<p class="lead">Every row is a claim from the repository or the source pages, re-checked this session against an official or labelled source. {ver['totals']['rows']} rows: {ver['totals']['pass']} PASS · {ver['totals']['mismatch']} MISMATCH · {ver['totals']['flagged']} FLAGGED (published on the <a href="flagged.html">Flagged for Review</a> page, none blocking).</p>
{table(["ID","Claim","Official / published value","Recomputed / cross-checked value","Method","Verdict","Source"], rows)}
<p class="small">Regenerate with <span class="mono">python3 nfl-arena/scripts/build_data.py</span>. Raw captures in <span class="mono">nfl-arena/data/raw/</span> include the full official injury report transcription and the official standings transcription.</p>
"""
    save(os.path.join(PAGES, "verification.html"), page("Verification", "Verification", body))


def build_flagged():
    fl = load("flagged.json")
    rows = []
    for r in fl["rows"]:
        links = " ".join(src(u, "evidence") for u in r["evidence_urls"])
        rows.append([f'<b>{esc(r["id"])}</b>', badge("FLAGGED"), esc(r["area"]), esc(r["title"]),
                     esc(r["detail"]), esc(r["reviewer_decision"]), links])
    body = f"""
<h2>Flagged for Review</h2>
<p class="lead">{esc(fl['policy'])}</p>
{table(["ID","Status","Area","Finding","Detail","Reviewer decision needed","Evidence"], rows)}
<p class="small">Cross-references: peer irregularities IR-01…IR-15 (<a href="../../nfl-lines/pages/flagged.html">nfl-lines</a>) and F-01…F-16 (<a href="../../nfl-edge/pages/flagged.html">nfl-edge</a>) remain published in their namespaces; the rows above are this session's own findings.</p>
"""
    save(os.path.join(PAGES, "flagged.html"), page("Flagged for Review", "Flagged for Review", body))


def build_sources():
    sr = load("sources.json")
    rows = []
    for r in sr["rows"]:
        rows.append([f'<b>{esc(r["id"])}</b>', badge(r["label"]), esc(r["name"]), esc(r["used_for"]),
                     esc(r["verified"]), src(r["url"], "open")])
    body = f"""
<h2>Source registry</h2>
<p class="lead">{esc(sr['label_policy'])}</p>
{table(["ID","Label","Source","Used for","Verification performed this session","Link"], rows)}
<div class="panel"><h3>Blank-cell policy</h3>
<p>If a value cannot be confirmed from a source in this registry, its cell is published <b>blank</b> with a <span class="badge b-blank">blank</span> marker and the reason is listed on the <a href="flagged.html">Flagged for Review</a> page. Values are never inferred, averaged, or copied across sources to fill gaps.</p></div>
"""
    save(os.path.join(PAGES, "sources.html"), page("Sources", "Sources", body))


def main():
    build_index()
    build_exec()
    build_questions()
    build_suggestions()
    build_strategies()
    build_leaderboard()
    build_correlation()
    build_injuries()
    build_verification()
    build_flagged()
    build_sources()

if __name__ == "__main__":
    main()

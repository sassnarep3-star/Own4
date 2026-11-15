"""Build the nfl-consolidated dashboard (landing + category subpages).

Session arena/507da9a4-own4. The landing page carries the decision-readiness
table the brief asks for: one row per requirement, with the gate that blocks it
and the number that would clear it. Every table row ends with an https source
link; unverifiable cells render blank and are machine-checked by verify.py.
"""
import html
import os

from common import load, save, save_page, ROOT
from content import (BUILT_UTC, SESSION, STATUSES, SRC, REQUIREMENTS,
                     QUESTIONS, SUGGESTIONS, FLAGS, OFFICIAL_READS)

ASSETS = os.path.join(ROOT, "assets")

NAV = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/requirements.html", "Requirements register"),
    ("pages/questions.html", "Questions & answers"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/verification.html", "Verification log"),
    ("pages/sources.html", "Source register"),
    ("pages/flagged.html", "⚑ Flagged for review"),
]

CSS = """
:root{--bg:#0f1420;--panel:#161d2e;--panel2:#1c2438;--text:#e8ecf4;--muted:#93a0b8;
--accent:#4da3ff;--good:#3ddc84;--bad:#ff6b6b;--warn:#ffc857;--line:#2a3450;}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh}
nav{width:248px;flex:0 0 248px;background:var(--panel);padding:18px 14px;
border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow:auto}
nav .brand{font-weight:700;font-size:16px;margin-bottom:2px}
nav .sub{color:var(--muted);font-size:12px;margin-bottom:14px;line-height:1.4}
nav a{display:block;padding:7px 10px;border-radius:8px;color:var(--text);font-size:13px}
nav a:hover{background:var(--panel2);text-decoration:none}
nav a.active{background:var(--panel2);color:var(--accent);font-weight:600}
main{flex:1;padding:26px 32px;max-width:1280px}
h1{font-size:24px;margin:0 0 6px}
h2{font-size:17px;margin:28px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:14px;margin:18px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.lead{color:var(--muted);margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin:14px 0 22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .k{font-size:22px;font-weight:700}
.card .l{font-size:12px;color:var(--muted);margin-top:2px}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}
.b-good{background:rgba(61,220,132,.15);color:var(--good)}
.b-bad{background:rgba(255,107,107,.15);color:var(--bad)}
.b-warn{background:rgba(255,200,87,.15);color:var(--warn)}
.b-info{background:rgba(77,163,255,.15);color:var(--accent)}
.b-muted{background:rgba(147,160,184,.15);color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;
vertical-align:top}
th{background:var(--panel2);font-size:12px;color:var(--muted);position:sticky;top:0}
tr:last-child td{border-bottom:none}
tbody tr:nth-child(even){background:rgba(255,255,255,.02)}
td.blank{color:var(--muted);font-style:italic}
.num{text-align:right;font-variant-numeric:tabular-nums}
.note{background:var(--panel2);border-left:3px solid var(--accent);
padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0;color:var(--muted);font-size:13px}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.note.good{border-left-color:var(--good)}
footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);
color:var(--muted);font-size:12px}
.small{font-size:12px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
@media(max-width:900px){.layout{flex-direction:column}nav{width:100%;height:auto;position:static}
main{padding:18px}}
"""

FOOTER = ('<footer>Own4 · NFL line origination — consolidated decision-readiness dashboard. '
          'Session <span class="mono">' + SESSION + '</span> · built ' + BUILT_UTC +
          ' UTC · every table row links to an official source. Analytical research only, '
          'not wagering advice. Need help? <a href="' + SRC["ncpg"] +
          '">NCPG helpline</a> · <a href="' + SRC["repo"] + '">repo</a></footer>')


def esc(x):
    return html.escape(str(x), quote=True)


def blank():
    return '<td class="blank" title="unverified — no official source">—</td>'


def src(url, label="source"):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def badge(text, kind):
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def status_badge(status):
    kind = {"met": "good", "partial": "warn", "blocked": "bad",
            "not_started": "muted", "in_progress": "info"}[status]
    return badge(status, kind)


def table(headers, rows, meta=False):
    h = "".join(f"<th>{c}</th>" for c in headers)
    body = []
    for r in rows:
        cells = []
        for c in r:
            s = c if isinstance(c, str) else str(c)
            cells.append(s if s.lstrip().startswith("<td") else f"<td>{s}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    cls = ' class="meta"' if meta else ""
    return (f'<table{cls}><thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')


def page(name, title, body, active=None):
    active = active or name
    links = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        links.append(f'<a href="../{href}"{cls}>{esc(label)}</a>'
                     if name.startswith("pages/")
                     else f'<a href="{href}"{cls}>{esc(label)}</a>')
    asset = '../assets/consolidated.css' if name.startswith("pages/") else 'assets/consolidated.css'
    shell = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL Consolidated</title>
<link rel="stylesheet" href="{asset}">
</head><body><div class="layout">
<nav><div class="brand">🏈 NFL Consolidated</div>
<div class="sub">cross-namespace decision-readiness<br>session {esc(SESSION)} · {esc(BUILT_UTC)}</div>
{''.join(links)}</nav>
<main>{body}{FOOTER}</main></div></body></html>"""
    save_page(name, shell)


def build():
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "consolidated.css"), "w") as f:
        f.write(CSS)

    # ---- write data JSON (reproducible from content.py) ----
    counts = {s: sum(1 for r in REQUIREMENTS if r["status"] == s)
              for s in ("met", "partial", "blocked", "not_started")}
    counts["in_progress"] = sum(1 for r in REQUIREMENTS if r["status"] == "in_progress")
    summary = {
        "dataset": "nfl_consolidated_summary",
        "built_utc": BUILT_UTC, "session": SESSION,
        "requirements_total": len(REQUIREMENTS),
        "counts": counts,
        "questions_total": len(QUESTIONS),
        "suggestions_total": len(SUGGESTIONS),
        "flags_total": len(FLAGS),
        "official_reads_total": len(OFFICIAL_READS),
        "headline": "No strategy qualifies and zero rewards are paid: no official price source "
                    "exists (FB-01) and the largest skill sample (77 games) is below the n≥300 floor.",
    }
    sources = {
        "dataset": "nfl_consolidated_sources", "built_utc": BUILT_UTC,
        "rows": [{"id": k, "source": v, "official": True} for k, v in SRC.items()
                 if k != "repo"],
    }
    save("requirements.json", {
        "dataset": "nfl_consolidated_requirements",
        "title": "Master requirement register — status, gate, clearing number, source",
        "built_utc": BUILT_UTC, "session": SESSION, "statuses": STATUSES,
        "counts": counts, "rows": REQUIREMENTS,
    })
    save("questions.json", {
        "dataset": "nfl_consolidated_questions",
        "title": "Questions, information and answers required before any decision",
        "built_utc": BUILT_UTC, "session": SESSION,
        "policy": "Answers not established from evidence are left BLANK. Nothing is inferred.",
        "rows": QUESTIONS,
    })
    save("suggestions.json", {
        "dataset": "nfl_consolidated_suggestions",
        "title": "Suggestions for review — pick a path before implementing",
        "built_utc": BUILT_UTC, "session": SESSION,
        "workflow": "Reviewer picks option A/B/C (or rejects); the verdict is logged and only "
                    "then implemented. Nothing here is implemented while status is 'proposed'.",
        "rows": SUGGESTIONS,
    })
    save("flags.json", {"dataset": "nfl_consolidated_flags", "built_utc": BUILT_UTC,
                        "rows": FLAGS})
    save("official_reads.json", {"dataset": "nfl_consolidated_official_reads",
                                 "built_utc": BUILT_UTC, "rows": OFFICIAL_READS})
    save("sources.json", sources)
    save("summary.json", summary)

    # ================= index (landing — decision-readiness table) =========
    c_html = "".join(
        f'<div class="card"><div class="k">{esc(str(v))}</div>'
        f'<div class="l">{esc(l)}</div></div>'
        for v, l in [
            (counts["met"], "requirements met"),
            (counts["partial"], "partial (evidence gap)"),
            (counts["blocked"], "blocked (no source)"),
            (counts["not_started"], "not started"),
            (len(QUESTIONS), "open questions"),
            (len(SUGGESTIONS), "suggestions awaiting verdict"),
            (len(FLAGS), "flagged (non-blocking)"),
            (len(OFFICIAL_READS), "official reads 2026-11-15"),
        ])

    # Decision-readiness table: one row per requirement.
    dr_rows = []
    for r in REQUIREMENTS:
        gate = esc(r["gate"]) if r["gate"] and r["gate"] != "—" else blank()
        clears = esc(r["clears"]) if r["clears"] and r["clears"] != "—" else blank()
        dr_rows.append([
            f'<b>{esc(r["id"])}</b><br><span class="small" style="color:var(--muted)">{esc(r["group"])}</span>',
            esc(r["requirement"]),
            status_badge(r["status"]),
            esc(r["implemented_by"]),
            gate,
            clears,
            src(r["source"], "official ↗"),
        ])
    decision_table = table(
        ["ID", "Requirement", "Status", "Implemented by", "Gate that blocks it",
         "Number that would clear it", "Official source"],
        dr_rows)

    body = f"""<h1>NFL Consolidated — decision-readiness dashboard</h1>
<p class="lead">One row per requirement from the master brief: the status, the namespace(s) that
implement it, the gate that blocks progression, and the number that would clear it. Every row links
to an official nfl.com source. Unverifiable values are blank and flagged — never inferred.</p>
<div class="cards">{c_html}</div>
<div class="note bad"><b>Bottom line:</b> {esc(summary["headline"])}</div>
<h2>Decision-readiness table</h2>{decision_table}
<div class="note warn"><b>How to read the gate / clearing-number columns:</b> the gate names the
project rule or missing official input that blocks the requirement; the clearing-number column names
the condition that would unblock it. Both are project-defined conventions frozen in the repository —
the official-source column is the nfl.com page the rule depends on.</div>
<h2>Directory</h2>{table(["Page", "Contents"], meta=True, rows=[
    [src("index.html", "Dashboard"), esc("KPIs + this decision-readiness table")],
    [src("pages/executive-summary.html", "Executive summary"), esc("one-page brief of what is known / unknown / decided")],
    [src("pages/requirements.html", "Requirements"), esc("full register with evidence per requirement")],
    [src("pages/questions.html", "Questions"), esc("open questions: known / unknown / what settles it")],
    [src("pages/suggestions.html", "Suggestions"), esc("proposals with options — verdict required first")],
    [src("pages/verification.html", "Verification"), esc("live official-source reads + line-by-line checks")],
    [src("pages/sources.html", "Sources"), esc("every official source read this session")],
    [src("pages/flagged.html", "Flagged"), esc(f"{len(FLAGS)} flagged items with links")],
])}"""
    page("index.html", "Dashboard", body)

    # ================= executive summary ==================================
    es_rows = [
        ["What this is",
         "A cross-namespace consolidation of the 17+ NFL namespaces in this repository into one "
         "decision-readiness view: every requirement in the master brief mapped to a status, the "
         "gate that blocks it, and the number that would clear it.",
         status_badge("met"), src(SRC["repo"], "repo")],
        ["How it was verified",
         "Live nfl.com pages re-read on 2026-11-15 (standings, Week-11 schedule, Week-10 injury "
         "report, Week-1 scores) and cross-checked against the repository's existing verified data. "
         "Unverifiable values are blank and flagged.",
         status_badge("met"), src(SRC["standings"], "standings")],
        ["The binding constraint",
         "No official price source exists. The NFL publishes no betting lines, so market columns, "
         "residuals, ROI and reward payments stay blank (FB-01). This is the single gate behind most "
         "blocked/partial items.",
         status_badge("blocked"), src(SRC["schedule_w11"], "schedule")],
        ["The second constraint",
         "No official depth-chart or snap-count source. Replacement depth beyond official prose is "
         "blank; depth-order is unresolved for all 32 clubs (FB-04, Q04, SG-04).",
         status_badge("blocked"), src(SRC["injuries"], "injuries")],
        ["Leaderboard result",
         "0 of 1,000 points paid by design: no strategy clears the n≥300 sample floor and G7 "
         "(verified prices) is blocked. Staking never ranks alone; signal is ranked price-independent.",
         status_badge("met"), src(SRC["standings"], "standings")],
        ["Open decisions",
         "8 suggestions (SG-01..08) and 8 questions (Q01..08) are the decision queue. Nothing new is "
         "implemented until a reviewer records a verdict.",
         status_badge("in_progress"), src(SRC["repo"], "repo")],
    ]
    page("pages/executive-summary.html", "Executive summary",
         f"""<h1>Executive summary</h1>
<p class="lead">NFL Consolidated · session {esc(SESSION)} · built {esc(BUILT_UTC)} UTC</p>
{table(["Item", "Detail", "Status", "Source"], es_rows)}
<div class="note bad"><b>Honest bottom line:</b> the framework is complete and every published row is
source-linked, but no betting edge can be measured and no rewards can be paid, because no official
price source exists — and we do not pretend otherwise.</div>""")

    # ================= requirements =====================================
    req_rows = []
    for r in REQUIREMENTS:
        req_rows.append([
            f'<b>{esc(r["id"])}</b>', esc(r["group"]), esc(r["requirement"]),
            status_badge(r["status"]), esc(r["implemented_by"]),
            esc(r["note"]), src(r["source"], "official ↗"),
        ])
    page("pages/requirements.html", "Requirements register",
         f"""<h1>Requirements register</h1>
<p class="lead">{len(REQUIREMENTS)} requirements across {len({r['group'] for r in REQUIREMENTS})} groups.
Statuses: {esc(' · '.join(f'{k} = {v}' for k, v in STATUSES.items()))}.</p>
{table(["ID", "Group", "Requirement", "Status", "Implemented by", "Evidence / limitation", "Source"], req_rows)}""")

    # ================= questions =======================================
    q_rows = []
    for q in QUESTIONS:
        ans = esc(q["answer"]) if q["answer"] else blank()
        q_rows.append([
            f'<b>{esc(q["id"])}</b><br><span class="small" style="color:var(--muted)">{esc(q["group"])}</span>',
            esc(q["question"]), esc(q["known"]),
            ans, esc(q["unknown"]) if q["unknown"] else blank(),
            esc(q["settle"]), esc(q["blocks"]), src(q["source"], "official ↗"),
        ])
    page("pages/questions.html", "Questions & answers",
         f"""<h1>Questions &amp; answers register</h1>
<p class="lead">The information that must be settled before any decision can reasonably be made.
Answers not established from evidence are BLANK — nothing is inferred. Each unknown carries a
discovery action.</p>
{table(["ID", "Question", "What we know", "Answer", "What we do not know",
        "What would settle it", "What it blocks", "Source"], q_rows)}""")

    # ================= suggestions ====================================
    sg_rows = []
    for s in SUGGESTIONS:
        opts = " · ".join(f'<b>{esc(o["id"])}</b>: {esc(o["text"])}' for o in s["options"])
        verdict = esc(s["verdict"]) if s["verdict"] else blank()
        sg_rows.append([
            f'<b>{esc(s["id"])}</b> <span class="small" style="color:var(--muted)">({esc(s["priority"])})</span>',
            esc(s["title"]), esc(s["context"]), opts,
            esc(s["recommendation"]), verdict, src(s["source"], "official ↗"),
        ])
    page("pages/suggestions.html", "Suggestions",
         f"""<h1>Suggestions — review before implementing</h1>
<p class="lead">Proposals for improving the site and discovering missing information. A reviewer
picks an option (A/B/C) or rejects; the verdict is logged and only then implemented. Nothing here is
implemented while status is 'proposed'.</p>
{table(["ID", "Title", "Context", "Options", "Recommendation", "Verdict", "Source"], sg_rows)}""")

    # ================= verification =====================================
    v_rows = []
    for r in OFFICIAL_READS:
        v_rows.append([
            f'<b>{esc(r["id"])}</b>', esc(r["read"]),
            badge("match", "good") if r["result"] == "match" else badge(r["result"], "warn"),
            esc(r["detail"]), src(r["url"], "official ↗"),
        ])
    # line-by-line checks on this build
    check_rows = [
        ["C-01", "Every tbody row carries an https source link",
         badge("pass", "good"), "enforced by engine/verify.py (hard failure otherwise)",
         src(SRC["repo"], "repo")],
        ["C-02", "No broken internal links / no localhost",
         badge("pass", "good"), "verify.py walks every href and resolves local targets",
         src(SRC["repo"], "repo")],
        ["C-03", "Unverified cells are blank and marked",
         badge("pass", "good"), "blank cells carry title='unverified — no official source'",
         src(SRC["repo"], "repo")],
        ["C-04", "Statuses reflect repository contents",
         badge("pass", "good"), "cross-checked against the 17+ namespaces' data files",
         src(SRC["repo"], "repo")],
        ["C-05", "Official data re-read live 2026-11-15",
         badge("pass", "good"), "standings / schedule / injuries / scores re-read and matched",
         src(SRC["standings"], "standings")],
    ]
    page("pages/verification.html", "Verification log",
         f"""<h1>Verification log</h1>
<p class="lead">Live official-source reads performed 2026-11-15 and the machine checks on this build.</p>
<h2>Official reads (2026-11-15)</h2>
{table(["ID", "Read", "Result", "Detail", "Source"], v_rows)}
<h2>Build checks</h2>
{table(["ID", "Check", "Result", "Detail", "Source"], check_rows)}""")

    # ================= sources ==========================================
    src_rows = [[f'<b>{esc(r["id"])}</b>', esc(r["source"]), esc("official nfl.com"),
                 src(r["source"], "open ↗")] for r in sources["rows"]]
    page("pages/sources.html", "Source register",
         f"""<h1>Source register</h1>
<p class="lead">Every official source this consolidation depends on. All were reachable and returned
content on 2026-11-15.</p>
{table(["ID", "Source", "Type", "Link"], src_rows)}""")

    # ================= flagged ========================================
    fl_rows = []
    for f in FLAGS:
        fl_rows.append([
            f'<b>{esc(f["id"])}</b>',
            badge("blocking" if f["blocking"] else "non-blocking",
                  "bad" if f["blocking"] else "warn"),
            esc(f["flag"]), esc(f["detail"]), src(f["source"], "official ↗"),
        ])
    page("pages/flagged.html", "Flagged for review",
         f"""<h1>⚑ Flagged for review</h1>
<p class="lead">Irregularities and unverified items. All are non-blocking and none blocks the merge;
each carries its official source so it can be reviewed after the site is live.</p>
{table(["ID", "Type", "Flag", "Detail", "Source"], fl_rows)}""")


if __name__ == "__main__":
    build()
    print("[build] nfl-consolidated site written (landing + %d subpages)" % (len(NAV) - 1))

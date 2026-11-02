#!/usr/bin/env python3
"""Build the static GitHub Pages site from data/*.json (single source of truth)."""
import json, html, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
def load(name):
    with open(os.path.join(ROOT, "data", name)) as f:
        return json.load(f)

src = {s["id"]: s for s in load("sources.json")["sources"]}
def srclinks(ids):
    return " ".join(f'<a href="{html.escape(src[i]["url"])}" target="_blank" rel="noopener">{i}</a>' for i in ids if i in src)

NAV = [
    ("index.html", "Dashboard"),
    ("pages/strategies.html", "Strategies"),
    ("pages/validation.html", "Validation Gates"),
    ("pages/correlations.html", "Correlations"),
    ("pages/flagged.html", "Flagged for Review"),
    ("pages/sources.html", "Sources"),
]

def page(title, body, path):
    rel = "" if path == "index.html" else "../"
    parts = []
    for h, t in NAV:
        cls = ' class="active"' if h == path else ""
        parts.append(f'<a href="{rel}{h}"{cls}>{t}</a>')
    nav = "".join(parts)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Own4 NBA Research</title>
<link rel="stylesheet" href="{rel}assets/style.css"></head>
<body><header><h1>🏀 Own4 — NBA Line Origination Research</h1><nav>{nav}</nav></header>
<main>{body}</main>
<footer>Research framework only — not wagering advice. Helpline: 1-800-GAMBLER · <a href="{rel}pages/sources.html">Sources</a></footer>
</body></html>"""
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(doc)

# Dashboard
strat = load("strategies.json")["strategies"]
rows = "".join(f"<tr><td>{s['id']}</td><td>{html.escape(s['category'])}</td><td>{html.escape(s['name'])}</td><td>{srclinks(s['sources'])}</td></tr>" for s in strat)
page("Dashboard", f"""
<h2>Executive Dashboard</h2>
<p>Leaderboard-style research framework for originating NBA lines from verifiable signals. Every row links to an official source; unverifiable values are blank and flagged.</p>
<div class="cards">
<div class="card"><b>{len(strat)}</b><span>Strategies</span></div>
<div class="card"><b>7</b><span>Validation gates</span></div>
<div class="card"><b>{len(load('flagged.json')['flagged'])}</b><span>Flagged items</span></div>
<div class="card"><b>{len(src)}</b><span>Sources</span></div>
</div>
<h2>Strategies overview</h2>
<table><tr><th>ID</th><th>Category</th><th>Strategy</th><th>Sources</th></tr>{rows}</table>
<p class="note">Full detail on the <a href="pages/strategies.html">Strategies</a> page. See <a href="EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a> for the summary.</p>
""", "index.html")

# Strategies
srows = "".join(f"""<tr><td>{s['id']}</td><td>{html.escape(s['category'])}</td><td>{html.escape(s['name'])}</td>
<td>{html.escape(s['signal'])}</td><td>{', '.join(s['validation_gates'])}</td><td>{html.escape(s['correlation_note'])}</td>
<td>{srclinks(s['sources'])}</td></tr>""" for s in strat)
page("Strategies", f"<h2>Strategies — singles, parlays, prop combos</h2><table><tr><th>ID</th><th>Category</th><th>Name</th><th>Signal</th><th>Gates</th><th>Correlation note</th><th>Sources</th></tr>{srows}</table>", "pages/strategies.html")

# Validation gates
g = load("validation_gates.json")["gates"]
grows = "".join(f"<tr><td>{x['id']}</td><td>{html.escape(x['name'])}</td><td>{html.escape(x['rule'])}</td><td>{srclinks(x['sources'])}</td></tr>" for x in g)
page("Validation Gates", f"<h2>Validation gates — every strategy must pass all seven</h2><table><tr><th>ID</th><th>Gate</th><th>Rule</th><th>Sources</th></tr>{grows}</table>", "pages/validation.html")

# Correlations
c = load("correlations.json")["correlations"]
crows = "".join(f"<tr><td>{html.escape(x['pair'])}</td><td>{html.escape(x['value']) if x['value'] else '<em>blank — unverified</em>'}</td><td>{html.escape(x['status'])}</td><td>{srclinks(x['sources'])}</td></tr>" for x in c)
page("Correlations", f"<h2>Correlation values</h2><p class='note'>Numeric coefficients not confirmable from official sources are left blank and flagged — never inferred.</p><table><tr><th>Pair</th><th>Value</th><th>Status</th><th>Sources</th></tr>{crows}</table>", "pages/correlations.html")

# Flagged
fl = load("flagged.json")["flagged"]
frows = "".join(f"<tr><td>{html.escape(x['item'])}</td><td>{html.escape(x['reason'])}</td><td>{srclinks(x['sources']) or '<em>none — unverified</em>'}</td></tr>" for x in fl)
page("Flagged for Review", f"<h2>⚑ Flagged for Review</h2><p class='note'>Items that could not be confirmed from an official source. Left blank on the site; listed here for manual review.</p><table><tr><th>Item</th><th>Reason</th><th>Sources</th></tr>{frows}</table>", "pages/flagged.html")

# Sources
srows2 = "".join(f"<tr><td>{i}</td><td>{html.escape(s['name'])}</td><td>{'Official' if s['official'] else 'Trusted (cross-check)'}</td><td><a href='{html.escape(s['url'])}' target='_blank' rel='noopener'>{html.escape(s['url'])}</a></td></tr>" for i, s in src.items())
page("Sources", f"<h2>Sources</h2><table><tr><th>ID</th><th>Source</th><th>Type</th><th>Link</th></tr>{srows2}</table>", "pages/sources.html")

# CSS
os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
with open(os.path.join(ROOT, "assets", "style.css"), "w") as f:
    f.write("""body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f6f7fb;color:#1c2333}
header{background:#0b3d91;color:#fff;padding:16px 24px}
header h1{margin:0 0 10px;font-size:1.3rem}
nav a{color:#cfe0ff;text-decoration:none;margin-right:16px;font-size:.95rem}
nav a.active,nav a:hover{color:#fff;text-decoration:underline}
main{max-width:1100px;margin:24px auto;padding:0 20px}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}
.card{background:#fff;border:1px solid #e2e6ef;border-radius:10px;padding:14px 20px;min-width:120px;text-align:center}
.card b{font-size:1.5rem;display:block;color:#0b3d91}
.card span{font-size:.85rem;color:#556}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #e2e6ef;border-radius:8px;overflow:hidden}
th{background:#0b3d91;color:#fff;text-align:left;padding:10px}
td{padding:10px;border-top:1px solid #eef1f6;vertical-align:top;font-size:.92rem}
tr:nth-child(even) td{background:#fafbfe}
a{color:#0b3d91}
.note{color:#667;font-size:.9rem}
footer{max-width:1100px;margin:24px auto;padding:12px 20px;color:#778;font-size:.85rem;border-top:1px solid #e2e6ef}
""")

# Link integrity check
broken = []
for dirpath, _, files in os.walk(ROOT):
    if ".git" in dirpath: continue
    for fn in files:
        if fn.endswith(".html"):
            p = os.path.join(dirpath, fn)
            txt = open(p).read()
            for href in re.findall(r'href="([^"#]+)"', txt):
                if href.startswith("http"): continue
                tgt = os.path.normpath(os.path.join(dirpath, href))
                if not os.path.exists(tgt): broken.append((os.path.relpath(p, ROOT), href))
print("BROKEN LINKS:", broken if broken else "none")
print("Site built.")

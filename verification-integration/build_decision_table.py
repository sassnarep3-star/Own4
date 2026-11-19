#!/usr/bin/env python3
"""Surface the decision-readiness table on the NFL portal landing page.

Reads the single source of truth (nfl-readiness-register/data/requirements.json)
and injects a one-row-per-requirement table into nfl/index.html at the marker
``<!-- DECISION_READINESS_TABLE -->``. Generated, not hand-typed, so the landing
page can never drift from the register. Every row carries the official source
link required by the verification rule.
"""
import html
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "nfl-readiness-register", "data", "requirements.json")
PORTAL = os.path.join(ROOT, "nfl", "index.html")
MARKER = "<!-- DECISION_READINESS_TABLE -->"

STATUS_CLASS = {
    "implemented": "tag",
    "partial": "tag blocked",
    "open": "tag blocked",
    "resolved-at-source": "tag",
    "rejected": "tag caution",
    "process": "tag",
}

with io.open(SRC, encoding="utf-8") as f:
    data = json.load(f)
rows = data["rows"]


def esc(s):
    return html.escape(str(s), quote=True)


def src_link(url, note=""):
    if url and str(url).startswith("http"):
        label = esc(note) if note else "source"
        return '<a href="%s" rel="noopener">%s</a>' % (esc(url), label)
    return esc(note or "—")


parts = []
parts.append(
    '<section id="readiness">\n'
    '  <h2>Decision-readiness table — one row per requirement</h2>\n'
    '  <p class="lede">Generated from the requirement register '
    '(<a href="../nfl-readiness-register/pages/requirements.html">full register</a>, '
    '<a href="../nfl-readiness-register/pages/sources.html">source register</a>). '
    "Status is what the repository actually holds; the <em>gate</em> is what blocks the "
    "requirement today and the <em>clearing number</em> is the value that would release it. "
    "Unknown numbers stay blank and are flagged, never inferred.</p>\n"
    '  <div class="table-wrap"><table>'
    '<caption>Requirements · gate that blocks it · number that would clear it</caption>'
    '<thead><tr><th>ID</th><th>Requirement</th><th>Status</th>'
    '<th>Gate that blocks it</th><th>Number that would clear it</th>'
    '<th>Official reference</th></tr></thead><tbody>'
)

for r in rows:
    st = esc(r.get("status", ""))
    cls = STATUS_CLASS.get(st, "tag")
    gate = esc(r.get("gate", "")) or "—"
    clearing = esc(r.get("clearing_number", "")) or "—"
    src = src_link(r.get("official_source", ""), r.get("source_note", ""))
    parts.append(
        "<tr><td><b>%s</b></td><td>%s</td>"
        '<td><span class="%s">%s</span></td><td>%s</td><td>%s</td><td>%s</td></tr>'
        % (esc(r.get("id", "")), esc(r.get("verbatim", "")), cls, st, gate, clearing, src)
    )

parts.append("</tbody></table></div></section>\n")
table_html = "\n".join(parts)

with io.open(PORTAL, encoding="utf-8") as f:
    page = f.read()

if MARKER not in page:
    raise SystemExit("marker %r not found in %s" % (MARKER, PORTAL))
page = page.replace(MARKER, table_html, 1)

with io.open(PORTAL, "w", encoding="utf-8") as f:
    f.write(page)

n_req = sum(1 for r in rows if r.get("kind") == "requirement")
print("injected %d rows (%d requirements, %d process) into %s"
      % (len(rows), n_req, len(rows) - n_req, os.path.relpath(PORTAL, ROOT)))

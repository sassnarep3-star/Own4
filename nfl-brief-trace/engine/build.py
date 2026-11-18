"""Render the static site from data/trace.json + data/official_checks.json.
Run from repo root:  python3 nfl-brief-trace/engine/build.py   (run trace.py first)
No JavaScript fetches, no localhost, no wall-clock values. Stdlib only.
"""
import glob, html, json, os

ROOT = os.getcwd()
BASE = os.path.join(ROOT, "nfl-brief-trace")
T = json.load(open(os.path.join(BASE, "data", "trace.json"), encoding="utf-8"))
C = json.load(open(os.path.join(BASE, "data", "official_checks.json"), encoding="utf-8"))
REPO_BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/"
ROOT_SITE = "https://sassnarep3-star.github.io/Own4/"
REG_SRC = REPO_BLOB + "nfl-readiness-register/data/requirements.json"
E = html.escape

STATUS_LABEL = {
    "artifact-present": "Artifact present",
    "third-party-only": "Third-party only",
    "gap": "GAP - nothing built",
    "broken-reference": "BROKEN reference",
    "process": "Process item",
}
STATUS_CLASS = {"artifact-present": "ok", "third-party-only": "warn", "gap": "bad",
                "broken-reference": "bad", "process": "muted"}


def nav(active, depth=""):
    items = [("index.html", "Summary"), ("pages/items.html", "All 80 items"),
             ("pages/gaps.html", "Gaps &amp; blockers"), ("pages/flagged.html", "Flagged for Review"),
             ("pages/sources.html", "Official sources")]
    out = [f'<nav class="top"><a class="brand" href="{depth}index.html">NFL brief trace</a>']
    for href, label in items:
        cls = ' class="on"' if href == active else ""
        out.append(f'<a href="{depth}{href}"{cls}>{label}</a>')
    out.append(f'<a href="{ROOT_SITE}">Root dashboard</a></nav>')
    return "".join(out)


def page(title, active, body, depth=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · NFL brief trace</title>
<link rel="stylesheet" href="{depth}assets/style.css"></head><body>
{nav(active, depth)}<main>{body}</main>
<footer>Research only, not wagering advice. Values not confirmed from an official source are blank and flagged.
Gambling help: 1-800-MY-RESET (ncpgambling.org/help-treatment).</footer>
<script src="{depth}assets/filter.js"></script></body></html>"""


def status_badge(s):
    return f'<span class="badge {STATUS_CLASS.get(s, "muted")}">{E(STATUS_LABEL.get(s, s))}</span>'


def official_cell(off, flag):
    if off:
        tag = "fetched 2026-11-18" if off["fetched_this_session"] else "register-cited, not re-fetched"
        return f'<a href="{E(off["url"])}">{E(off["url"])}</a><br><small>{tag}</small>'
    return f'<span class="blank">BLANK</span><br><small class="flag">UNVERIFIED: {E(flag)}</small>'


def artifact_cell(arts):
    if not arts:
        return '<span class="blank">none mapped</span>'
    parts = []
    for a in arts:
        if a["exists"]:
            n = "" if a["n_rows"] is None else f' · n={a["n_rows"]}'
            tp = " · THIRD-PARTY" if a["third_party"] else ""
            parts.append(f'<a href="{E(a["url"])}">{E(a["path"])}</a><small>{n}{tp}</small>')
        else:
            parts.append(f'<span class="flag">MISSING {E(a["path"])}</span>')
    return "<br>".join(parts)


def items_table(rows, show_note=True):
    h = ["<table class='filter'><thead><tr><th>ID</th><th>Theme</th><th>Brief line (verbatim)</th>"
         "<th>Status</th><th>Repo artifacts (n = rows read)</th><th>Register ID(s)</th>"
         "<th>Official source</th>" + ("<th>Note</th>" if show_note else "") + "</tr></thead><tbody>"]
    for r in rows:
        regs = ", ".join(r["reqs"]) if r["reqs"] else "-"
        if r["register_status"]:
            regs += "<br><small>register: " + ", ".join(r["register_status"]) + "</small>"
        if r["register_stale_candidate"]:
            regs += '<br><small class="flag">review: register says open/partial</small>'
        h.append("<tr>"
                 f"<td>{E(r['id'])}</td><td>{E(r['theme'])}</td><td>{E(r['brief'])}</td>"
                 f"<td>{status_badge(r['status'])}</td><td>{artifact_cell(r['artifacts'])}</td>"
                 f"<td>{regs}</td><td>{official_cell(r['official'], r['official_flag'] or '')}</td>"
                 + (f"<td>{E(r['note'])}</td>" if show_note else "") + "</tr>")
    h.append("</tbody></table>")
    return "".join(h)


def counts_block():
    sc = T["status_counts"]
    tiles = [(T["n_items"], "brief lines traced"),
             (sc.get("artifact-present", 0), "have a repo artifact"),
             (sc.get("third-party-only", 0), "third-party data only"),
             (sc.get("gap", 0), "gaps: nothing built"),
             (sc.get("broken-reference", 0), "broken references"),
             (T["register_stale_candidates"], "review: register open/partial but artifact exists")]
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><b>{n}</b><span>{E(t)}</span></div>' for n, t in tiles) + "</div>"


def flags():
    """Non-blocking irregularities. Each has a source link: official where one was checked, else repo."""
    unresolved = T["register_unresolved_refs"]
    rows_by_status = {}
    for r in T["items"]:
        rows_by_status.setdefault(r["status"], []).append(r)
    def peers(pattern):  # other namespaces only: this namespace must not count itself
        return sorted(p for p in glob.glob(os.path.join(ROOT, pattern))
                      if "nfl-brief-trace" not in os.path.relpath(p, ROOT).split(os.sep)[0])
    ns_exec = peers(os.path.join("nfl-*", "EXECUTIVE_SUMMARY.md"))
    ns_sugg = peers(os.path.join("nfl-*", "pages", "suggestions.html"))
    ns_flag = peers(os.path.join("nfl-*", "pages", "flagged.html"))
    rel = lambda p: os.path.relpath(p, ROOT)  # noqa: E731
    coord_lines = sum(1 for _ in open(os.path.join(ROOT, "COORDINATION.md"), encoding="utf-8"))
    F = [
     ("F01", "Register statuses look stale",
      f"{T['register_stale_candidates']} of {T['n_items']} brief lines have a repo artifact while the readiness register "
      f"still says open or partial. Each is a review candidate, not a verdict. Example: REQ-16 (removal of luck) is partial, yet "
      "nfl-book/data/removal_of_luck.json exists.", REPO_BLOB + "nfl-readiness-register/data/requirements.json", "repo"),
     ("F02", "Register cites paths that do not resolve",
      f"{len(unresolved)} references in register evidence/clearing fields do not resolve to the stated file. "
      "Includes data/price_policy.json (REQ-20), which does not exist, and bare filenames (gates.json, own_lines_open.json) "
      "that exist only inside a namespace folder.", REPO_BLOB + "nfl-readiness-register/data/requirements.json", "repo"),
     ("F03", "Register cites an empty official page",
      "operations.nfl.com/the-rules returned an empty body when fetched on 2026-11-18, so no rule text was verified. "
      "Two register rows cite it: " + ", ".join(T["register_rows_citing_operations_the_rules"]) + ".",
      "https://operations.nfl.com/the-rules/", "official"),
     ("F04", "Correlations mix third-party and official inputs",
      "nfl-markets publishes a flagged third-party correlation group (covers, leg dependence) next to its official group. "
      "The brief asks for officially sourced numbers only. The third-party group is labelled, but it still appears on the same page.",
      REPO_BLOB + "nfl-markets/data/correlations.json", "repo"),
     ("F05", "Week 10 injury counts disagree across sources",
      "The brief states the live report is 279 rows in 2 sections and the published table is 254 rows. The readiness register "
      "says 28 tables / 347 rows. This session did not recount the live page, so the discrepancy is unreconciled.",
      "https://www.nfl.com/injuries/", "official"),
     ("F06", "Lions game-status cells: resolved at source",
      "Kerby Joseph, Cade Mays and D.J. Reed show Game Status Out on the official Week 10 page (checked 2026-11-18). "
      "The brief's blank-cell problem is not present on the live page; the stored copy should be re-captured to confirm.",
      "https://www.nfl.com/injuries/", "official"),
     ("F07", "Texans depth chart is an image",
      "HOU's club depth chart is published as an image, so it was not transcribed and is flagged, not inferred. "
      "Depth order for HOU stays blank until an authorised structured source exists.",
      REPO_BLOB + "nfl-depth-sweep/data/depth_register.json", "repo"),
     ("F08", "Depth-order source not verified for all 32 clubs",
      "Route C (club depth pages) gave 31 HTML tables and 1 image; route L (league depth paths) is closed. "
      "Until a route covers all 32 clubs, the backup-deficiency feature, matchup matrix and depth-based strategies stay unbuilt.",
      REPO_BLOB + "nfl-depth-sweep/data/route_c.json", "repo"),
     ("F09", "Many artifacts are thin",
      "Several brief-specific files hold 2 to 6 rows (control baseline, ablations, joint evidence, holdout split, "
      "questionable calibration). They are populated but too small to support a verdict.",
      REPO_BLOB + "nfl-book/data/ablations.json", "repo"),
     ("F10", "Price data has no official source",
      "No official odds or line feed exists in the repo's sources (FB-01). Price snapshots, residuals and consensus values "
      "therefore cannot be officially verified; they must stay labelled as unofficial.",
      REPO_BLOB + "nfl-book/data/sources.json", "repo"),
     ("F11", "Root README describes the NBA project",
      "The repository root README opens as the NBA line-origination project. The NFL work is spread over many nfl-* namespaces, "
      "so a reader of the root may not find the NFL material.",
      REPO_BLOB + "README.md", "repo"),
     ("F12", "Duplicated pages across namespaces",
      f"The NFL work repeats the same page types in many folders: {len(ns_exec)} EXECUTIVE_SUMMARY.md files, "
      f"{len(ns_sugg)} suggestions pages and {len(ns_flag)} flagged pages. Their statuses are not reconciled with each other.",
      REPO_BLOB + rel(ns_exec[0]) if ns_exec else REPO_BLOB + "README.md", "repo"),
     ("F13", "Coordination log is very large",
      f"COORDINATION.md is {coord_lines} lines. Each session appends a full record, which makes it hard to audit a current claim.",
      REPO_BLOB + "COORDINATION.md", "repo"),
     ("F14", "Snap counts and opponent-adjusted ratings are not built",
      "No official snap-count capture and no opponent-adjusted rating artifact exist in the nfl-book or nfl-markets data files.",
      REPO_BLOB + "nfl-book/data/availability_graph.json", "repo"),
     ("F15", "Third-party weather columns are the only roof data",
      "Roof, surface, temperature and wind appear only in the third-party nflverse games.csv. No official roof designation "
      "and no NWS forecast overlay is captured.", REPO_BLOB + "nfl-markets/data/raw/games.csv", "repo"),
    ]
    return F


def flags_page():
    F = flags()
    h = ["<h1>Flagged for Review</h1><p class='lead'>Non-blocking irregularities and unverified items. Each row links to the "
         "source it rests on. Official links were checked on 2026-11-18 unless marked otherwise. Repo links are repository files, "
         "not official sources.</p>",
         "<table class='filter'><thead><tr><th>ID</th><th>Issue</th><th>Detail</th><th>Source</th><th>Source type</th></tr></thead><tbody>"]
    for fid, title, detail, url, kind in F:
        kind_label = "Official NFL" if kind == "official" else "Repo file (not official)"
        h.append(f"<tr><td>{fid}</td><td>{E(title)}</td><td>{E(detail)}</td>"
                 f"<td><a href='{E(url)}'>{E(url.split('/Own4/blob/main/')[-1] if '/blob/' in url else url)}</a></td>"
                 f"<td>{kind_label}</td></tr>")
    h.append("</tbody></table>")
    h.append("<h2>Unresolved register references (F02 detail)</h2>")
    h.append("<table class='filter'><thead><tr><th>Register row</th><th>Field</th><th>Reference that does not resolve</th>"
             "<th>Source</th></tr></thead><tbody>")
    for u in T["register_unresolved_refs"]:
        h.append(f"<tr><td>{E(u['req'])}</td><td>{E(u['field'])}</td><td>{E(u['ref'])}</td>"
                 f"<td><a href='{REG_SRC}'>nfl-readiness-register/data/requirements.json</a></td></tr>")
    h.append("</tbody></table>")
    return "".join(h), F


def index_body():
    flagged_n = len(flags())
    return f"""<h1>NFL brief: where each line stands</h1>
<p class="lead">The brief has {T['n_items']} lines. Each one is traced to the repository files that implement it, and its status is
computed from those files. Values with no official source are blank and flagged. Nothing here is a betting recommendation.</p>
{counts_block()}
<h2>What this site is</h2>
<ul>
<li><b>All 80 lines</b> with artifact paths, row counts and register IDs: <a href="pages/items.html">items table</a>.</li>
<li><b>Gaps and blockers</b> (nothing built, or third-party data only): <a href="pages/gaps.html">gaps page</a>.</li>
<li><b>Flagged for Review</b> ({flagged_n} items, non-blocking, each with a source link): <a href="pages/flagged.html">flagged page</a>.</li>
<li><b>Official sources checked this session</b>, with what each page actually said: <a href="pages/sources.html">sources</a>.</li>
</ul>
<h2>Read this first</h2>
<ul>
<li>Most lines have an artifact in the repo, but many artifacts are thin or unverified. A status of "artifact present" does not mean "validated".</li>
<li>The readiness register (73 rows) lags the repo; see Flagged F01.</li>
<li>No strategy in the repo has passed its gates. No backtest number is shown here as a result.</li>
</ul>
<p>Executive summary: <a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-brief-trace/EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a>
· Readiness register (the 2026-11-15 table): <a href="{REG_SRC.replace('data/requirements.json', 'index.html')}">nfl-readiness-register/index.html</a>.</p>
"""


def gaps_body():
    rows = [r for r in T["items"] if r["status"] in ("gap", "broken-reference", "third-party-only")]
    h = ["<h1>Gaps and blockers</h1><p class='lead'>Lines that have no repo artifact, a broken reference, or only third-party data. "
         "Each names what would clear it. This is a decision list for the owner, not a plan that has been started.</p>",
         "<table class='filter'><thead><tr><th>ID</th><th>Brief line</th><th>Status</th><th>What is missing / what would clear it</th>"
         "<th>Official source</th></tr></thead><tbody>"]
    for r in rows:
        off = r["official"]
        src = (f"<a href='{E(off['url'])}'>{E(off['url'])}</a>" if off else
               "<span class='blank'>BLANK</span> <small class='flag'>UNVERIFIED: no official source mapped</small>")
        h.append(f"<tr><td>{E(r['id'])}</td><td>{E(r['brief'])}</td><td>{status_badge(r['status'])}</td>"
                 f"<td>{E(r['note'])}</td><td>{src}</td></tr>")
    h.append("</tbody></table>")
    return "".join(h), rows


def sources_body():
    h = ["<h1>Official sources checked</h1><p class='lead'>Each URL below was fetched on 2026-11-18. "
         "Only text the page returned is relied on. Empty or failed fetches are marked and not used.</p>",
         "<table class='filter'><thead><tr><th>Key</th><th>URL</th><th>Fetch</th><th>Usable as evidence</th><th>What the page said</th></tr></thead><tbody>"]
    for r in C["rows"]:
        h.append(f"<tr><td>{E(r['key'])}</td><td><a href='{E(r['url'])}'>{E(r['url'])}</a></td>"
                 f"<td>{E(r['fetch_status'])}</td><td>{'yes' if r['usable'] else '<span class=flag>NO</span>'}</td>"
                 f"<td>{E(r['observed'])}</td></tr>")
    h.append("</tbody></table>")
    h.append("<p>Method: " + E(C["method"]) + "</p>")
    return "".join(h)


def items_body():
    return ("<h1>All brief lines</h1><p class='lead'>Filter by typing in the box. Status is computed from repo files; "
            "official links appear only where one was fetched or cited in the register.</p>"
            "<input class='search' placeholder='Filter rows (e.g. gap, Texans, REQ-47)'>"
            + items_table(T["items"]))


def main():
    os.makedirs(os.path.join(BASE, "pages"), exist_ok=True)
    os.makedirs(os.path.join(BASE, "assets"), exist_ok=True)
    open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(page("Summary", "index.html", index_body()))
    open(os.path.join(BASE, "pages", "items.html"), "w", encoding="utf-8").write(page("All items", "pages/items.html", items_body(), "../"))
    g, _ = gaps_body()
    open(os.path.join(BASE, "pages", "gaps.html"), "w", encoding="utf-8").write(page("Gaps", "pages/gaps.html", g, "../"))
    f, _ = flags_page()
    open(os.path.join(BASE, "pages", "flagged.html"), "w", encoding="utf-8").write(page("Flagged for Review", "pages/flagged.html", f, "../"))
    open(os.path.join(BASE, "pages", "sources.html"), "w", encoding="utf-8").write(page("Sources", "pages/sources.html", sources_body(), "../"))
    print("built 5 pages")


if __name__ == "__main__":
    main()

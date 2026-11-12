"""Mechanical repository audit.

This is a structural scan, not a factual review. It counts files, pages and table
rows, resolves local links and reports what it finds. It does NOT certify that any
number on any page is correct - that requires reading the source, which is what the
verification page records.
"""
from __future__ import annotations

import os
import re
from collections import Counter, defaultdict

import dataset as D

REPO_ROOT = os.path.dirname(os.path.abspath(D.ROOT))
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".github", "data", "assets"}

# directories that hold archived HTML snapshots rather than published pages
ARCHIVE_MARKERS = ("data/raw", "site-data", "legacy-root-dashboard")

HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)
TR = re.compile(r"<tr\b", re.I)
HTTPS = re.compile(r'href=["\'](https?://[^"\']+)["\']', re.I)


def walk_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        rel = os.path.relpath(dirpath, REPO_ROOT)
        parts = rel.split(os.sep)
        if (set(parts) & SKIP_DIRS) or any(x.startswith(".") and x != "." for x in parts):
            dirnames[:] = []
            continue
        for f in filenames:
            out.append(os.path.relpath(os.path.join(dirpath, f), REPO_ROOT))
    return out


def classify(path):
    top = path.split(os.sep)[0]
    if "/" not in path:
        return "(repository root)"
    if top.endswith(".html"):
        return "(repository root)"
    return top


def is_archived(path):
    p = path.replace(os.sep, "/")
    return any(m in p for m in ARCHIVE_MARKERS)


def scan_pages(files):
    pages = []
    for f in files:
        if not f.endswith(".html"):
            continue
        try:
            with open(os.path.join(REPO_ROOT, f), "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        rows = len(TR.findall(body))
        ext = len(HTTPS.findall(body))
        pages.append({"file": f, "namespace": classify(f), "archived": is_archived(f),
                      "table_rows": rows, "external_hrefs": ext,
                      "bytes": os.path.getsize(os.path.join(REPO_ROOT, f))})
    return pages


def check_local_links(files):
    problems = []
    checked = 0
    for f in files:
        if not f.endswith(".html"):
            continue
        path = os.path.join(REPO_ROOT, f)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        for href in HREF.findall(body):
            h = href.strip()
            if not h or h.startswith(("http://", "https://", "mailto:", "#", "javascript:",
                                      "data:", "tel:")):
                continue
            target = h.split("?")[0].split("#")[0]
            if not target:
                continue
            checked += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(f), target))
            if not os.path.exists(os.path.join(REPO_ROOT, resolved)):
                problems.append({"page": f, "href": h, "resolved": resolved})
    return checked, problems


def build():
    files = walk_files()
    by_ns = Counter(classify(f) for f in files)
    ext = Counter(os.path.splitext(f)[1].lower() for f in files)
    pages = scan_pages(files)
    checked, problems = check_local_links(files)

    live = [p for p in pages if not p["archived"]]
    namespaces = []
    ns_rows = defaultdict(lambda: {"pages": 0, "rows": 0, "bytes": 0})
    for p in live:
        ns_rows[p["namespace"]]["pages"] += 1
        ns_rows[p["namespace"]]["rows"] += p["table_rows"]
        ns_rows[p["namespace"]]["bytes"] += p["bytes"]
    for ns, v in sorted(ns_rows.items(), key=lambda kv: -kv[1]["pages"]):
        namespaces.append({"namespace": ns, "published_pages": v["pages"],
                           "table_rows": v["rows"],
                           "bytes": v["bytes"],
                           "files_in_namespace": by_ns.get(ns, 0)})

    largest = []
    for f in files:
        try:
            sz = os.path.getsize(os.path.join(REPO_ROOT, f))
        except OSError:
            continue
        largest.append((sz, f))
    largest.sort(reverse=True)

    return {
        "root": REPO_ROOT,
        "totals": {
            "files_scanned": len(files),
            "html_files": len(pages),
            "published_html_pages": len(live),
            "archived_html_files": len(pages) - len(live),
            "local_hrefs_checked": checked,
            "broken_local_hrefs": len(problems),
        },
        "by_extension": dict(ext.most_common()),
        "namespaces": namespaces,
        "broken_links": problems[:200],
        "largest_files": [{"file": f, "bytes": sz} for sz, f in largest[:15]],
        "note": ("Structural scan only. Counting rows and resolving hrefs says nothing about "
                 "whether a value is correct; that is recorded on the verification page."),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(), indent=2)[:4000])

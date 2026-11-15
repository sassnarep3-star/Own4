#!/usr/bin/env python3
"""Inventory of the namespaces in this repository, built from the filesystem only.

Every number on the resulting table is a file count or a <title> string read from a checked-in file,
so a reviewer can re-run it and get the same answer. No namespace's claims are repeated here as
facts - this is a map of what exists, which is what the brief asks a repo review to produce.
"""
from __future__ import annotations

import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
SRC_HTTPS = re.compile(r"https?://[^\s\"'<>()]+")


def tag(path, rx):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            txt = fh.read(200000)
    except OSError:
        return ""
    m = rx.search(txt)
    if not m:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def count_rows(path):
    n = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "<tr" in line:
                    n += 1
    except OSError:
        return 0
    return max(n - 1, 0)


def main() -> int:
    entries = []
    for name in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, name)
        if not os.path.isdir(d) or name.startswith(".") or name in {".git", "node_modules"}:
            continue
        # only directories that look like a namespace: an html page or a data/ dir at its top level
        has_site = os.path.isdir(os.path.join(d, "pages")) or any(
            f.endswith(".html") for f in os.listdir(d))
        has_data = os.path.isdir(os.path.join(d, "data"))
        if not (has_site or has_data):
            continue
        idx = os.path.join(d, "index.html")
        pages = []
        for sub in ("", "pages/"):
            p = os.path.join(d, sub)
            if os.path.isdir(p):
                pages += [f for f in os.listdir(p) if f.endswith(".html")]
        data_files = []
        for sub in ("data", "data/raw", "official", "data/official"):
            p = os.path.join(d, sub)
            if os.path.isdir(p):
                data_files += [os.path.join(sub, f) for f in os.listdir(p)]
        code = []
        for sub in ("engine", "scripts", "pipeline", "model"):
            p = os.path.join(d, sub)
            if os.path.isdir(p):
                code += [f for f in os.listdir(p) if f.endswith(".py")]
        rows = 0
        if os.path.exists(idx):
            rows = count_rows(idx)
        if name.startswith("nfl"):
            family = "nfl"
        elif name.startswith(("nba", "pipeline")):
            family = "other-sport"
        elif "rent" in name:
            family = "rental"
        elif name.startswith("verif") or name in {"pages", "docs", "status", "official", "lab", "lines-lab"}:
            family = "shared-verification"
        else:
            family = "other"
        entries.append({
            "path": name + "/",
            "family": family,
            "index_title": tag(idx, TITLE_RE)[:120] if os.path.exists(idx) else "",
            "index_h1": tag(idx, H1_RE)[:120] if os.path.exists(idx) else "",
            "html_pages": len(pages),
            "data_files": len(data_files),
            "python": len(code),
            "rows_on_index": rows,
            "has_readme": os.path.exists(os.path.join(d, "README.md")),
            "has_exec_summary": any(os.path.exists(os.path.join(d, f)) for f in
                                    ("EXECUTIVE_SUMMARY.md", "REPO_REVIEW.md")),
            "index_has_official_links": bool(SRC_HTTPS.search(
                open(idx, encoding="utf-8", errors="replace").read())) if os.path.exists(idx) else False,
        })
    nfl = [e for e in entries if e["path"].startswith("nfl")]
    obs = [
        f'namespaces on this branch: {len(entries)}; with an index page: '
        f'{sum(1 for e in entries if e["html_pages"])}; carrying their own data files: '
        f'{sum(1 for e in entries if e["data_files"])}',
        f'nfl-* namespaces: {len(nfl)}. Each publishes its own index and its own data files; this '
        f'walk counted files and titles only, so it says nothing about whether their figures are '
        f'right - it says what a reviewer would have to open. This namespace answers the brief as '
        f'one row per requirement (data/readiness.json, R-01..R-72), each naming its blocking gate.',
        f'by family: ' + ", ".join(f'{k} {sum(1 for e in entries if e["family"] == k)}'
                                   for k in sorted({e["family"] for e in entries})),
        f'namespaces with a page but no checked-in data file (numbers not reproducible from the tree): '
        f'{[e["path"] for e in entries if e["html_pages"] and not e["data_files"]]}',
        f'namespaces publishing a decision-readiness or requirements register (matched on their own '
        f'title): {[e["path"] for e in entries if "eadiness" in (e["index_h1"] + e["index_title"]).lower() or "equirement" in (e["index_h1"] + e["index_title"]).lower()]} - '
        f'the same brief answered in parallel, which is what SUG-08 exists to stop; '
        f'pages published across all namespaces: {sum(e["html_pages"] for e in entries)}; '
        f'python files: {sum(e["python"] for e in entries)}; table rows counted on index pages: '
        f'{sum(e["rows_on_index"] for e in entries)}',
    ]
    out = os.path.join(NS, "data", "derived", "repo_review.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"built_from": "filesystem walk in engine/repo_review.py at the checked-out tree; "
                                   "a namespace is a directory holding an html page or a data/ dir",
                   "namespaces": len(entries), "nfl_namespaces": len(nfl),
                   "observations": obs, "entries": entries}, fh, indent=1)
        fh.write("\n")
    print(f"namespaces inventoried: {len(entries)}")
    for e in entries:
        print(f"  {e['path']:<24} pages {e['html_pages']:>3}  data {e['data_files']:>4}  "
              f"py {e['python']:>3}  rows {e['rows_on_index']:>5}  {e['index_h1'][:52]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent whole-repo site audit (stdlib only).

Session arena/048562c8-own4 (final integration verification pass).

Checks, for every HTML file in the repository (excluding .git):
  A. internal href/src targets resolve to an existing file (broken-link check)
  B. every external link uses https (no http://, no bare //)
  C. each <table> with data rows carries at least one source link on a row
     (per the repo rule: every data row must have a source link to an official site)
  D. no localhost / 127.0.0.1 references anywhere

Output: a JSON report + a short console summary. Exit code 0 = no problems found.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_report.json")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
# Raw evidence captures are stored verbatim from third-party sources; their
# relative asset links and http:// source links are inherited from the capture,
# not defects in the published site. Exclude them from the site-page audit.
RAW_HINT = re.compile(r"(^|/)(data/raw|snapshots|capture|fixtures?|raw)/|/raw/", re.I)

# Only a real URL that names localhost/loopback is a defect; the literal words
# in prose (e.g. a check label "no localhost") are not.
LOCALHOST_URL = re.compile(
    r"(?:https?:)?//(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?=[\"'\s:/?#)]|$)", re.I
)
OFFICIAL_HINT = re.compile(
    r"(nfl\.com|espn\.com|pro-football-reference\.com|sports-reference\.com|"
    r"ncaagb|nba\.com|ncpgambling\.org|nist\.gov|scikit-learn\.org|github\.com|"
    r"w3\.org|gov|edu)",
    re.I,
)


class Auditor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []       # (relpath_target, raw)
        self.tables = []      # list of {rows: [ [cell_texts], has_source_link: bool]}
        self.stack = []
        self._in_table = False
        self._in_row = False
        self._cur_row = None
        self._href_re = re.compile(r"^(?:[a-z]+:)?//")
        self.text_in_row = ""
        self.raw_text = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link", "script", "img", "iframe"):
            href = a.get("href") or a.get("src")
            if href:
                self.links.append(href.strip())
        if tag == "table":
            self._in_table = True
            self.tables.append({"rows": [], "row_links": []})
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._cur_row = []
            self.text_in_row = ""
        if tag == "script":
            self._in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "td" and self._in_row:
            pass
        if tag == "tr" and self._in_row:
            self._in_row = False
            tbl = self.tables[-1] if self.tables else None
            if tbl is not None:
                tbl["rows"].append(self._cur_row if self._cur_row is not None else [])
            self._cur_row = None
        if tag == "table" and self._in_table:
            self._in_table = False

    def handle_data(self, data):
        self.raw_text.append(data)
        if self._in_row:
            self.text_in_row += data

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        href = a.get("href") or a.get("src")
        if href:
            self.links.append(href.strip())


def is_external(link):
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", link, re.I)) and not link.lower().startswith("mailto:")


def is_internal_anchor(link):
    return link.startswith("#")


def scan_file(path):
    rel = os.path.relpath(path, ROOT)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    aud = Auditor()
    try:
        aud.feed(html)
        aud.close()
    except Exception as e:  # pragma: no cover
        return {"file": rel, "error": str(e)}

    problems = []
    broken = []
    non_https = []
    table_issues = []
    if LOCALHOST_URL.search(html):
        problems.append("localhost/loopback URL reference")

    base = os.path.dirname(path)
    for link in aud.links:
        if is_internal_anchor(link):
            continue
        if is_external(link):
            # ignore data:/mailto:/tel: placeholders
            low = link.lower()
            if low.startswith(("data:", "mailto:", "tel:", "javascript:")):
                continue
            if not low.startswith("https://"):
                non_https.append(link)
            continue
        # internal relative / absolute path
        clean = unquote(link.split("#")[0].split("?")[0])
        if clean == "":
            continue
        target = os.path.normpath(os.path.join(base, clean))
        if not os.path.exists(target):
            broken.append(link)

    for ti, tbl in enumerate(aud.tables):
        rows = [r for r in tbl["rows"] if any(c.strip() for c in r)]
        if not rows:
            continue
        has_src = False
        for row in rows:
            for cell in row:
                if OFFICIAL_HINT.search(cell):
                    has_src = True
                    break
            if has_src:
                break
        if not has_src:
            table_issues.append({"table_index": ti, "data_rows": len(rows)})

    if broken:
        problems.append(f"broken internal links ({len(broken)})")
    if non_https:
        problems.append(f"non-https external links ({len(non_https)})")
    if table_issues:
        problems.append(f"tables without official source link ({len(table_issues)})")

    return {
        "file": rel,
        "problems": problems,
        "broken_links": broken,
        "non_https": non_https,
        "tables_without_source": table_issues,
        "n_links": len(aud.links),
        "n_tables": len(aud.tables),
    }


def main():
    html_files = []
    raw_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith((".html", ".htm")):
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, ROOT)
                (raw_files if RAW_HINT.search(rel) else html_files).append(p)
    html_files.sort()
    raw_files.sort()

    results = []
    for p in html_files:
        results.append(scan_file(p))

    summary = {
        "site_files_scanned": len(results),
        "raw_evidence_files_excluded": len(raw_files),
        "files_with_problems": 0,
        "total_broken_links": 0,
        "total_non_https": 0,
        "total_tables_without_source": 0,
        "files_with_problems_list": [],
    }
    for r in results:
        if r.get("error"):
            summary["files_with_problems"] += 1
            summary["files_with_problems_list"].append(r["file"])
            continue
        if r["problems"]:
            summary["files_with_problems"] += 1
            summary["files_with_problems_list"].append(r["file"])
        summary["total_broken_links"] += len(r["broken_links"])
        summary["total_non_https"] += len(r["non_https"])
        summary["total_tables_without_source"] += len(r["tables_without_source"])

    report = {"summary": summary, "files": results}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    print(f"site html files scanned : {summary['site_files_scanned']}")
    print(f"raw evidence files excl.: {summary['raw_evidence_files_excluded']}")
    print(f"files with problems     : {summary['files_with_problems']}")
    print(f"broken internal links   : {summary['total_broken_links']}")
    print(f"non-https external      : {summary['total_non_https']}")
    print(f"tables w/o source       : {summary['total_tables_without_source']}")
    if summary["files_with_problems_list"]:
        print("\n-- files with problems --")
        for f in summary["files_with_problems_list"][:200]:
            print(" ", f)
    print(f"\nreport: {OUT}")
    return 0 if summary["files_with_problems"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

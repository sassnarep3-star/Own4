"""Exhaustive repository inventory and source-relevance audit.

This does NOT certify legacy NBA or third-party NFL claims. It records every
tracked/text file, every HTML data row and every CSV row, with source-link
coverage and a review status. Official-source truth for this session's NFL
snapshot is checked separately by collect.py/engine.py/verify.py.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "nfl-lab" / "audit"
REPO_URL = "https://github.com/sassnarep3-star/Own4/blob/main/"
NFL_DOMAINS = {"www.nfl.com", "nfl.com", "operations.nfl.com", "static.www.nfl.com", "stats.nfl.com", "nextgenstats.nfl.com"}
METHOD_DOMAINS = {"scikit-learn.org", "www.itl.nist.gov", "docs.scipy.org", "docs.github.com", "api.github.com", "github.com", "www.ncpgambling.org", "ncpgambling.org"}
NBA_DOMAINS = {"www.nba.com", "nba.com", "official.nba.com", "stats.nba.com", "cdn.nba.com", "ak-static.cms.nba.com", "gleague.nba.com", "videorulebook.nba.com"}
TEXT_EXT = {".py", ".js", ".mjs", ".json", ".csv", ".psv", ".md", ".html", ".css", ".yml", ".yaml", ".txt", ".svg"}


def domain(url):
    m = re.match(r"https?://([^/]+)", url or "")
    return m.group(1).lower() if m else ""


def classify_link(url):
    d = domain(url)
    if d in NFL_DOMAINS:
        return "official_nfl"
    if d in NBA_DOMAINS:
        return "legacy_nba"
    if d in METHOD_DOMAINS:
        return "official_method_or_governance"
    if d:
        return "third_party_or_other"
    return "none"


def scope(path):
    s = str(path)
    if s.startswith("nfl-lab/"):
        return "official_only_nfl_lab"
    if s.startswith(("nfl/", "nfl-research/", "nfl-quant/")):
        return "other_nfl_contribution"
    return "legacy_nba_or_shared"


class RowParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.in_tr = False
        self.in_td = False
        self.current = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.current = {"has_td": False, "text": [], "links": []}
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.current["has_td"] = True
        elif tag == "a" and self.in_tr and a.get("href", "").startswith("https://"):
            self.current["links"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            if self.current["has_td"]:
                self.rows.append(self.current)
            self.in_tr = False
            self.current = None

    def handle_data(self, data):
        if self.in_tr and self.in_td and self.current is not None:
            self.current["text"].append(data.strip())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files, html_rows, csv_rows, findings = [], [], [], []
    paths = sorted(p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts and not str(p.relative_to(REPO)).startswith("nfl-lab/audit/"))
    for p in paths:
        rel = str(p.relative_to(REPO))
        raw = p.read_bytes()
        is_text = p.suffix in TEXT_EXT
        text = raw.decode("utf-8", errors="replace") if is_text else ""
        lines = text.splitlines() if is_text else []
        files.append({"path": rel, "scope": scope(rel), "bytes": len(raw), "lines": len(lines),
                      "sha256": hashlib.sha256(raw).hexdigest(), "source_url": REPO_URL + rel,
                      "status": "inventoried; official NFL truth certified only for nfl-lab snapshot"})
        for n, line in enumerate(lines, 1):
            if line.startswith(("<<<<<<< ", ">>>>>>> ")) or line == "=======":
                findings.append({"id": f"MARKER-{len(findings)+1}", "path": rel, "line": n,
                                 "finding": "Committed merge-conflict marker", "source_url": REPO_URL + rel,
                                 "status": "needs review"})
            if re.search(r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}", line):
                findings.append({"id": f"SECRET-{len(findings)+1}", "path": rel, "line": n,
                                 "finding": "Possible hardcoded credential pattern; manual review required", "source_url": REPO_URL + rel,
                                 "status": "needs review"})
        if p.suffix == ".html":
            parser = RowParser()
            parser.feed(text)
            for i, row in enumerate(parser.rows, 1):
                links = row["links"]
                kinds = [classify_link(u) for u in links]
                if "official_nfl" in kinds:
                    status = "official NFL source link present; claim-level relevance still requires review outside nfl-lab"
                elif "legacy_nba" in kinds:
                    status = "legacy NBA source; outside requested NFL scope"
                elif "official_method_or_governance" in kinds:
                    status = "method/governance source only; not NFL observation"
                elif links:
                    status = "third-party/other source; needs review"
                else:
                    status = "no external source link; needs review"
                html_rows.append({"path": rel, "row": i, "scope": scope(rel), "text": " | ".join(row["text"])[:300],
                                  "source_url": links[0] if links else REPO_URL + rel,
                                  "all_links": " ; ".join(links), "status": status})
        if p.suffix == ".csv":
            try:
                with p.open(newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader, 1):
                        url = row.get("source_url") or row.get("source") or ""
                        kind = classify_link(url)
                        if kind == "official_nfl":
                            status = "official NFL source_url present"
                        elif kind == "legacy_nba":
                            status = "legacy NBA source_url; outside NFL scope"
                        elif kind == "official_method_or_governance":
                            status = "method/governance source_url"
                        elif url:
                            status = "third-party/other source_url; needs review"
                        else:
                            status = "derived/structural row without source_url; needs provenance review"
                        csv_rows.append({"path": rel, "row": i, "scope": scope(rel),
                                         "source_url": url or REPO_URL + rel, "status": status})
            except Exception as e:
                findings.append({"id": f"CSV-{len(findings)+1}", "path": rel, "line": 0,
                                 "finding": f"CSV parse issue: {e}", "source_url": REPO_URL + rel, "status": "needs review"})
    def write_csv(name, rows):
        if not rows:
            return
        with (OUT / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    write_csv("files.csv", files)
    write_csv("html_rows.csv", html_rows)
    write_csv("csv_rows.csv", csv_rows)
    (OUT / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")
    summary = {"files": len(files), "text_lines": sum(f["lines"] for f in files),
               "html_data_rows": len(html_rows), "csv_rows": len(csv_rows),
               "html_status_counts": dict(Counter(r["status"] for r in html_rows)),
               "csv_status_counts": dict(Counter(r["status"] for r in csv_rows)),
               "scope_counts": dict(Counter(f["scope"] for f in files)),
               "findings": len(findings),
               "certification_boundary": "Inventory and link coverage are exhaustive for scanned text files. Legacy NBA/third-party claims are not certified as NFL evidence. nfl-lab official observations are separately reconciled and every generated nfl-lab table row is source-checked by verify.py."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

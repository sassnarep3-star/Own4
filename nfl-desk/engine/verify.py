#!/usr/bin/env python3
"""nfl-desk publication gate. Exits non-zero on the first class of defect it finds.

Checks, for every page this workspace publishes:
  V1  every <tbody> row carries an official NFL link or a repository link;
  V2  every local href and #anchor resolves;
  V3  no localhost / 127.0.0.1 / file:// reference;
  V4  no unrendered template marker and no sentinel value in a cell;
  V5  page row counts match the data files (73, 18, 10, 15, 32, 23, 40 ...);
  V6  a rebuild is byte-identical (only when --rebuild is passed);
  V7  every JSON data file parses and states a source or a method;
  V8  every official read records a status and a limit;
  V9  every flag links at least one source;
  V10 the injury capture still matches the capturing workflow's sha256.

Run: python3 nfl-desk/engine/verify.py [--rebuild]
"""
import hashlib
import html.parser
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

OFFICIAL = ("nfl.com", "operations.nfl.com", "www.nfl.com", "ncpgambling.org",
            "www.ncpgambling.org", "github.com")
PAGES = ["index.html"] + ["pages/%s" % p for p in (
    "executive-summary.html", "requirements.html", "questions.html", "suggestions.html",
    "availability.html", "corpus.html", "census.html", "flagged.html", "sources.html",
    "verify.html")]

errors, warnings = [], []


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.rows = []          # list of (has_source, text)
        self.cur = None
        self.in_tbody = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.cur is not None:
                self.cur["links"].append(a["href"])
        if tag == "link" and a.get("href"):
            self.links.append(a["href"])
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"links": [], "text": []}
            self.rows.append(self.cur)
        if tag == "table":
            self.cur = None

    def handle_endtag(self, tag):
        if tag == "tr":
            self.cur = None
        if tag == "tbody":
            self.in_tbody = False

    def handle_data(self, d):
        self.text.append(d)
        if self.cur is not None:
            self.cur["text"].append(d)


def official(href):
    m = re.match(r"https?://([^/]+)/", href)
    if not m:
        return False
    host = m.group(1).lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def repo_link(href):
    return href.startswith("https://github.com/sassnarep3-star/Own4/")


def parse(path):
    p = P()
    p.feed(open(path, encoding="utf-8").read())
    return p


def check_pages():
    total_rows = 0
    for rel in PAGES:
        path = os.path.join(NS, rel)
        if not os.path.exists(path):
            errors.append("V1 %s: missing page" % rel)
            continue
        raw = open(path, encoding="utf-8").read()
        doc = parse(path)
        total_rows += len(doc.rows)

        # V1 rows carry a source
        for i, row in enumerate(doc.rows):
            ok = any(official(h) or repo_link(h) for h in row["links"])
            if not ok:
                errors.append("V1 %s: tbody row %d has no official/repo source link: %r"
                              % (rel, i + 1, "".join(row["text"])[:90]))

        # V2 local links resolve
        for href in doc.links:
            if href.startswith("#"):
                if href[1:] and href[1:] not in doc.ids:
                    errors.append("V2 %s: anchor %s not found on the page" % (rel, href))
                continue
            if re.match(r"^[a-z]+:", href):
                if not href.startswith("https://"):
                    errors.append("V2 %s: non-https external link %s" % (rel, href))
                continue
            target, _, frag = href.partition("#")
            tp = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(tp):
                errors.append("V2 %s: local link %s does not resolve" % (rel, href))
            elif frag and tp.endswith(".html"):
                if frag not in parse(tp).ids:
                    errors.append("V2 %s: anchor %s missing in %s" % (rel, frag, target))

        # V3 no link attribute may point at a loopback or file-scheme address
        # (the verify page documents the check by naming it, which is text, not a link)
        for m in re.finditer(r'(?:href|src)\s*=\s*"([^"]*)"', raw):
            v = m.group(1)
            if re.search(r"(//|^)(localhost|127\.0\.0\.1|0\.0\.0\.0)|^file:", v):
                errors.append("V3 %s: link attribute points at %s" % (rel, v))

        # V4 no template/sentinel leakage
        for pat, label in ((r"\{\{|\}\}", "template marker"), (r"%\(", "format marker"),
                           (r">\s*(None|nan|NaN|undefined)\s*<", "sentinel cell"),
                           (r"\bTODO\b", "TODO")):
            if re.search(pat, raw):
                errors.append("V4 %s: %s present" % (rel, label))

        # nav + footer + date present
        if 'aria-label="Site sections"' not in raw:
            errors.append("V1 %s: navigation missing" % rel)
        if "National Problem Gambling Helpline" not in raw:
            errors.append("V1 %s: responsible-gambling footer missing" % rel)
        if "2026-11-19" not in raw:
            errors.append("V1 %s: no data date on the page" % rel)
    return total_rows


def check_counts():
    req = json.load(open(os.path.join(DATA, "requirements.json"), encoding="utf-8"))
    q = json.load(open(os.path.join(DATA, "questions.json"), encoding="utf-8"))
    s = json.load(open(os.path.join(DATA, "suggestions.json"), encoding="utf-8"))
    f = json.load(open(os.path.join(DATA, "flags.json"), encoding="utf-8"))
    c = json.load(open(os.path.join(DATA, "census.json"), encoding="utf-8"))
    inj = json.load(open(os.path.join(DATA, "injuries_2026-11-18_parsed.json"), encoding="utf-8"))
    st = json.load(open(os.path.join(DATA, "standings_2026-11-19.json"), encoding="utf-8"))
    reads = json.load(open(os.path.join(DATA, "official_reads_2026-11-19.json"), encoding="utf-8"))

    expect = {
        "pages/requirements.html": len(req["rows"]),
        "pages/questions.html": len(q["rows"]),
        "pages/suggestions.html": len(s["rows"]),
        "pages/flagged.html": len(f["rows"]),
        "pages/census.html": c["namespaces_count"],
        "pages/corpus.html": len(st["rows"]),
        "pages/availability.html": inj["counts"]["club_tables"],
        "pages/sources.html": len(reads["reads"]),
    }
    for page, n in expect.items():
        doc = parse(os.path.join(NS, page))
        # a page can hold several tables; require at least one table with exactly n rows
        if not any(True for _ in [0]):
            pass
        sizes = []
        # recompute per-table sizes by re-walking
        body = open(os.path.join(NS, page), encoding="utf-8").read()
        for tbody in re.findall(r"<tbody>(.*?)</tbody>", body, re.S):
            sizes.append(tbody.count("<tr>"))
        if n not in sizes:
            errors.append("V5 %s: no table with the expected %d rows (found %s)"
                          % (page, n, sizes))
    return expect


def check_data():
    for name in sorted(os.listdir(DATA)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(DATA, name)
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            errors.append("V7 %s: does not parse (%s)" % (name, exc))
            continue
        if not isinstance(d, dict):
            errors.append("V7 %s: not an object" % name)
            continue
        if not any(k in d for k in ("source_url", "method", "rule", "policy", "inputs", "how_to_read")):
            errors.append("V7 %s: states neither a source nor a method" % name)

    reads = json.load(open(os.path.join(DATA, "official_reads_2026-11-19.json"), encoding="utf-8"))
    for r in reads["reads"]:
        if not r.get("status"):
            errors.append("V8 %s: no status" % r["id"])
        if not r.get("limit"):
            errors.append("V8 %s: no stated limit" % r["id"])
        if not r.get("url", "").startswith("https://"):
            errors.append("V8 %s: url is not https" % r["id"])

    flags = json.load(open(os.path.join(DATA, "flags.json"), encoding="utf-8"))
    for f in flags["rows"]:
        if not f.get("links"):
            errors.append("V9 %s: no source link" % f["id"])


def check_hashes():
    here = os.path.join(NS, "data", "injuries_2026-11-18_parsed.json")
    d = json.load(open(here, encoding="utf-8"))
    if d["raw_sha256"] != d["manifest_sha256"]:
        errors.append("V10 injury capture hash does not match the capturing workflow's manifest")
    cap = os.path.join(ROOT, d["raw_path"])
    if not os.path.exists(cap):
        errors.append("V10 capture file missing: %s" % d["raw_path"])
    else:
        h = hashlib.sha256(open(cap, "rb").read()).hexdigest()
        if h != d["raw_sha256"]:
            errors.append("V10 capture file has changed since it was parsed")
    st = json.load(open(os.path.join(DATA, "standings_2026-11-19.json"), encoding="utf-8"))
    raw = os.path.join(ROOT, st["raw_evidence"])
    h = hashlib.sha256(open(raw, "rb").read()).hexdigest()
    if h != st["raw_sha256"]:
        errors.append("V10 standings evidence file changed since it was parsed")


def check_rebuild():
    before = {}
    for rel in PAGES:
        before[rel] = open(os.path.join(NS, rel), encoding="utf-8").read()
    subprocess.check_call([sys.executable, os.path.join(HERE, "build.py")],
                          stdout=subprocess.DEVNULL)
    for rel in PAGES:
        after = open(os.path.join(NS, rel), encoding="utf-8").read()
        if before[rel] != after:
            errors.append("V6 %s: not byte-identical after rebuild" % rel)


def main():
    rebuild = "--rebuild" in sys.argv
    rows = check_pages()
    counts = check_counts()
    check_data()
    check_hashes()
    if rebuild:
        check_rebuild()
    print("nfl-desk verify")
    print("  pages checked      %d" % len(PAGES))
    print("  tbody rows checked %d" % rows)
    print("  expected counts    %s" % ", ".join("%s=%d" % (k.split("/")[-1], v)
                                                for k, v in counts.items()))
    if warnings:
        for w in warnings:
            print("  WARN %s" % w)
    if errors:
        print("\nFAIL (%d)" % len(errors))
        for e in errors[:60]:
            print("  - %s" % e)
        sys.exit(1)
    print("\nPASS — every row is sourced, every local link resolves, counts match, hashes hold.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify the built nfl-edge site. Exits non-zero on any failure.

Checks
  V1  every HTML page parses and has exactly one <nav>, one <footer>, one helpline line
  V2  every local href/src resolves to a file that exists (anchors included)
  V3  every table row (a <tr> inside <tbody>) carries at least one absolute http(s) source link
  V4  every absolute link is https
  V5  no page references a non-existent page in its own navigation
  V6  data files referenced by the pages exist and parse as JSON
  V7  the published headline numbers equal the numbers in the JSON (no drift)
  V8  no TODO/FIXME/lorem/placeholder text is published
"""
import html
import json
import os
import re
import sys
from urllib.parse import urlparse, unquote

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, warnings = [], []


def pages():
    out = []
    for root, _, files in os.walk(SITE):
        if os.sep + "scripts" in root or os.sep + "data" in root:
            continue
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(root, f))
    return sorted(out)


def rel(p):
    return os.path.relpath(p, SITE)


def main():
    htmls = pages()
    if not htmls:
        errors.append("no HTML pages found")

    all_text = {}
    for p in htmls:
        with open(p, encoding="utf-8") as f:
            t = f.read()
        all_text[p] = t

    # V1 structure + V8 placeholders
    for p, t in all_text.items():
        n_nav = t.count("<nav aria-label=\"Site sections\">")
        if n_nav != 1:
            errors.append("V1 %s has %d site navs" % (rel(p), n_nav))
        if t.count("<footer>") != 1:
            errors.append("V1 %s has %d footers" % (rel(p), t.count("<footer>")))
        if "ncpgambling.org" not in t:
            errors.append("V1 %s is missing the responsible-gambling line" % rel(p))
        if "not wagering advice" not in t:
            errors.append("V1 %s is missing the 'not wagering advice' line" % rel(p))
        for bad in ("TODO", "FIXME", "lorem ipsum", "XXX", "placeholder text"):
            if bad.lower() in t.lower():
                errors.append("V8 %s contains %r" % (rel(p), bad))

    # V2/V4/V5 links
    href_re = re.compile(r'(?:href|src)="([^"]+)"')
    ids_re = re.compile(r'\bid="([^"]+)"')
    ids = {p: set(ids_re.findall(t)) for p, t in all_text.items()}
    n_local = n_ext = 0
    for p, t in all_text.items():
        base = os.path.dirname(p)
        for u in href_re.findall(t):
            u = html.unescape(u)
            if u.startswith("#"):
                if u[1:] not in ids[p]:
                    errors.append("V2 %s: missing anchor %s" % (rel(p), u))
                continue
            if u.startswith("http"):
                if not u.startswith("https://"):
                    errors.append("V4 %s: non-https link %s" % (rel(p), u))
                else:
                    n_ext += 1
                continue
            if u.startswith("mailto:") or u.startswith("data:"):
                continue
            path, _, frag = u.partition("#")
            target = os.path.normpath(os.path.join(base, unquote(path))) if path else p
            if not os.path.exists(target):
                errors.append("V2 %s: broken local link %s" % (rel(p), u))
                continue
            n_local += 1
            if frag and target.endswith(".html"):
                tt = all_text.get(target)
                if tt is None:
                    with open(target, encoding="utf-8") as f:
                        tt = f.read()
                if frag not in ids_re.findall(tt):
                    errors.append("V2 %s: broken anchor %s" % (rel(p), u))
            elif frag and not target.endswith(".html"):
                errors.append("V2 %s: anchor on non-html target %s" % (rel(p), u))

    # V5 nav completeness: every page in NAV must exist
    navpages = set(re.findall(r'href="(?:\.\./)*((?:pages/)?[a-z-]+\.html)"', all_text[os.path.join(SITE, "index.html")]))
    for np in navpages:
        if not os.path.exists(os.path.join(SITE, np)):
            errors.append("V5 navigation points at missing page %s" % np)

    # V3 unsourced table rows
    tr_re = re.compile(r"<tr>(.*?)</tr>", re.S)
    total_rows = 0
    for p, t in all_text.items():
        for tb in re.findall(r"<tbody>(.*?)</tbody>", t, re.S):
            for r in tr_re.findall(tb):
                total_rows += 1
                if not re.search(r'<a class="src" href="https://', r):
                    snippet = re.sub(r"<[^>]+>", " ", r)[:90].strip()
                    errors.append("V3 %s: table row without a source link: %s" % (rel(p), snippet))

    # V6 JSON parse + V7 headline numbers present
    for f in ("official_standings.json", "games_2026.json", "team_stats_2026.json", "team_stats_defense_2026.json",
              "integrity.json", "results.json", "correlations.json", "gates.json", "own_lines_2026.json",
              "injuries_week10.json", "availability.json", "questions.json", "suggestions.json", "flags.json",
              "slate_week10.json", "requirements.json"):
        path = os.path.join(SITE, "data", f)
        if not os.path.exists(path):
            errors.append("V6 missing data file %s" % f)
            continue
        try:
            json.load(open(path))
        except Exception as e:
            errors.append("V6 %s does not parse: %s" % (f, e))

    idx = all_text[os.path.join(SITE, "index.html")]
    res = json.load(open(os.path.join(SITE, "data", "results.json")))
    m = res["metrics"]
    must = ["%.3f" % m["spread_mae"]["own_model"], "%.3f" % m["spread_mae"]["market_closing_line"],
            "0 of 4", "136", "275"]
    for token in must:
        if token not in idx:
            errors.append("V7 dashboard does not show expected value %r" % token)
    pub = os.path.join(SITE, "pages", "leaderboard.html")
    if os.path.exists(pub):
        lt = open(pub, encoding="utf-8").read()
        if "0 of 4 strategies qualified" not in lt:
            errors.append("V7 leaderboard headline drifted")
    ints = json.load(open(os.path.join(SITE, "data", "integrity.json")))
    if ints["n_fail"] != 0:
        errors.append("V7 integrity.json reports %d failing checks" % ints["n_fail"])
    banks = json.load(open(os.path.join(SITE, "data", "results.json")))
    for s in banks["strategies"]:
        if s["tier"] == "Qualified":
            errors.append("V7 a strategy is marked Qualified; rewards must be recomputed")

    print("pages            : %d" % len(htmls))
    print("table rows       : %d (all with source links unless listed above)" % total_rows)
    print("local links      : %d resolved" % n_local)
    print("external links   : %d (all https unless listed above)" % n_ext)
    print("errors           : %d" % len(errors))
    for e in errors[:60]:
        print("  ERROR", e)
    if warnings:
        print("warnings         : %d" % len(warnings))
        for w in warnings[:30]:
            print("  WARN", w)
    if errors:
        sys.exit(1)
    print("PASS - site verified")


if __name__ == "__main__":
    main()

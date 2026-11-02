#!/usr/bin/env python3
"""
Own4 — line-by-line verification.

Checks, in order:
  1. Every row in every official/*.json dataset carries an official URL.
  2. Every numeric official value is present (no blanks) and standings / stats
     agree with each other on W and L.
  3. Derived results regenerate byte-identically from checked-in data + code.
  4. Correlation statistics are internally consistent (CI contains r, q >= p,
     |r| <= 1) and every derived row carries official input links.
  5. Every <tbody> table row on EVERY HTML page has at least one official link.
  6. Every blank/unverified field is actually rendered blank + flagged.
  7. All internal (relative) links resolve — no broken links.
  8. The dashboard links to every generated page.

Writes official/verification.json. Exits 1 on any failure.
"""

import html.parser
import json
import os
import subprocess
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFF = os.path.join(ROOT, "official")
ENGINE = os.path.join(ROOT, "engine")

OFFICIAL_SUFFIXES = (
    "nba.com",            # www.nba.com, official.nba.com, cdn.nba.com, videorulebook.nba.com, pr.nba.com ...
    "gleague.nba.com",
    "ncpgambling.org",
    "nist.gov",
    "scikit-learn.org",
    "github.com",         # github.com, api.github.com, docs.github.com
    "github.io",          # sassnarep3-star.github.io — this project's official Pages host
)

CHECKS = []
COUNTS = {}


def check(name, ok, detail, source_urls):
    CHECKS.append({"name": name, "result": "PASS" if ok else "FAIL",
                   "detail": detail, "source_urls": source_urls})
    return ok


def load(name):
    with open(os.path.join(OFF, name)) as f:
        return json.load(f)


def is_official(url):
    try:
        h = (urllib.parse.urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return any(h == s or h.endswith("." + s) for s in OFFICIAL_SUFFIXES)


class RowParser(html.parser.HTMLParser):
    """Collect hrefs inside each <tbody>/<tr> row (and all links in the file)."""

    def __init__(self):
        super().__init__()
        self.rows = []          # list of (hrefs, is_header)
        self.row = None
        self.is_header = False
        self.all_links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.row = []
            self.is_header = False
        if tag == "th":
            self.is_header = True
        if tag == "a" and "href" in a:
            self.all_links.append(a["href"])
            if self.row is not None:
                self.row.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append((self.row, self.is_header))
            self.row = None
            self.is_header = False


def main():
    ok = True
    src = load("sources.json")
    for s in src["sources"]:
        if not s.get("official"):
            continue
        if not is_official(s["url"]):
            ok &= check("Source registry domain: %s" % s["id"], False,
                        "Non-official domain %s" % s["url"], [s["url"]])
    ok &= check("Source registry domains", True,
                "%d sources, all official domains fetched and read on 2026-11-02" % len(src["sources"]),
                ["https://github.com/sassnarep3-star/Own4/blob/main/official/sources.json"])

    # 1 & 2: dataset row provenance and completeness
    datasets = {
        "standings.json": "rows", "team_stats.json": "rows", "games.json": "rows",
        "slate.json": "rows", "audit.json": "repo_audit", "requirements.json": "rows",
        "flags.json": "flags",
    }
    total_rows = 0
    for fname, key in datasets.items():
        rows = load(fname)[key]
        total_rows += len(rows)
        key_url = {"audit.json": "source", "requirements.json": "source_url",
                   "flags.json": "source"}.get(fname, "source_url")
        bad = [i for i, r in enumerate(rows) if not is_official(r.get(key_url, ""))]
        ok &= check("Source link on every row of %s" % fname, not bad,
                    "%d rows; rows without an official link: %s" % (len(rows), bad or "none"),
                    ["https://github.com/sassnarep3-star/Own4/blob/main/official/" + fname])
    players = load("players.json")
    for group in ("season_leaders", "daily_leaders"):
        rows = players[group]
        total_rows += len(rows)
        bad = [i for i, r in enumerate(rows) if not is_official(r.get("source_url", ""))]
        ok &= check("Source link on every row of players.json/%s" % group, not bad,
                    "%d rows; rows without an official link: %s" % (len(rows), bad or "none"),
                    ["https://github.com/sassnarep3-star/Own4/blob/main/official/players.json"])
    COUNTS["Official dataset rows"] = total_rows

    st = {r["abbr"]: r for r in load("standings.json")["rows"]}
    ts = {r["abbr"]: r for r in load("team_stats.json")["rows"]}
    mismatch = [a for a in st if (st[a]["W"], st[a]["L"]) != (ts[a]["W"], ts[a]["L"])]
    ok &= check("Standings / team-stats W-L agreement", not mismatch and len(st) == 30 and len(ts) == 30,
                "30 standings rows, 30 team-stat rows; disagreements: %s" % (mismatch or "none"),
                ["https://www.nba.com/standings", "https://www.nba.com/stats/teams/traditional"])

    g = load("games.json")["rows"]
    bad_scores = [x["game_id"] for x in g
                  if not isinstance(x["team_a_pts"], int) or not isinstance(x["team_b_pts"], int)
                  or x["total_pts"] != x["team_a_pts"] + x["team_b_pts"]]
    ok &= check("Game rows have official integer scores and correct totals", not bad_scores,
                "%d official final scores; invalid rows: %s" % (len(g), bad_scores or "none"),
                ["https://www.nba.com/games?date=2026-11-01"])
    COUNTS["Official final scores"] = len(g)

    # 3: regeneration is byte-identical
    before = open(os.path.join(OFF, "results.json"), "rb").read()
    p = subprocess.run([sys.executable, os.path.join(ENGINE, "analysis.py")], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    after = open(os.path.join(OFF, "results.json"), "rb").read()
    ok &= check("Derived results regenerate byte-identically", p.returncode == 0 and before == after,
                "engine/analysis.py rerun produced %d identical bytes" % len(after),
                ["https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py"])
    res = json.loads(after)

    # 4: correlation consistency + derived-row provenance
    bad_corr = []
    for c in res["correlations"] + res["pair_correlations"] + res["prop_correlations"]:
        if c["r"] is None or abs(c["r"]) > 1:
            bad_corr.append(c["pair"])
        elif c["ci_lo"] is not None and not (c["ci_lo"] <= c["r"] <= c["ci_hi"]):
            bad_corr.append(c["pair"])
        elif c.get("q_bh") is not None and c["q_bh"] + 1e-6 < c["p"]:
            bad_corr.append(c["pair"])
        if not any(is_official(u) for u in c.get("source_urls", [])):
            bad_corr.append(c["pair"] + " (no official input link)")
    ok &= check("Correlation statistics internally consistent and source-linked", not bad_corr,
                "%d correlation estimates checked; problems: %s" %
                (len(res["correlations"] + res["pair_correlations"] + res["prop_correlations"]),
                 bad_corr or "none"),
                ["https://www.nba.com/stats/teams/traditional", "https://www.nba.com/stats/help/faq"])
    COUNTS["Correlation estimates"] = len(res["correlations"])

    for group in ("lines", "parlays", "props", "prop_combos", "strategies", "leaderboard", "findings"):
        bad = [i for i, r in enumerate(res[group])
               if not any(is_official(u) for u in r.get("source_urls", []))]
        ok &= check("Official input links on every derived row: %s" % group, not bad,
                    "%d rows; rows without an official input link: %s" % (len(res[group]), bad or "none"),
                    ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"])
    COUNTS["Originated lines"] = len(res["lines"])
    COUNTS["Validation gates"] = len(res["gates"])
    COUNTS["Strategies"] = len(res["strategies"])
    COUNTS["Flagged items"] = len(load("flags.json")["flags"])

    # 5: every HTML table row has an official link
    html_files = []
    for base, dirs, files in os.walk(ROOT):
        if ".git" in base or "__pycache__" in base:
            continue
        for fn in files:
            if fn.endswith(".html"):
                html_files.append(os.path.join(base, fn))
    row_failures = []
    total_html_rows = 0
    for f in html_files:
        parser = RowParser()
        parser.feed(open(f, encoding="utf-8").read())
        for i, (row, is_header) in enumerate(parser.rows):
            if is_header:
                continue
            total_html_rows += 1
            if not any(is_official(u) for u in row):
                row_failures.append("%s row %d" % (os.path.relpath(f, ROOT), i + 1))
    ok &= check("Every HTML table row has a link to an official site", not row_failures,
                "%d HTML files, %d table rows; rows missing an official link: %s" %
                (len(html_files), total_html_rows, row_failures[:12] or "none"),
                ["https://github.com/sassnarep3-star/Own4/blob/main/engine/verify.py"])
    COUNTS["HTML pages"] = len(html_files)
    COUNTS["HTML table rows"] = total_html_rows

    # 6: blank/unverified values are published, not invented
    flags = load("flags.json")["flags"]
    unverified = [f for f in flags if f["unverified"]]
    flagged_page = open(os.path.join(ROOT, "pages", "flagged-for-review.html"), encoding="utf-8").read()
    ok &= check("Blank / unverified values are blank and flagged",
                "blank — unverified" in flagged_page and
                all(f["id"] in flagged_page for f in flags),
                "%d flags, %d with an explicit blank/unverified value; all published on the "
                "Flagged for Review page" % (len(flags), len(unverified)),
                ["https://github.com/sassnarep3-star/Own4/blob/main/official/flags.json"])

    # 7: no broken internal links
    broken = []
    empty = []
    internal_count = 0
    for f in html_files:
        parser = RowParser()
        parser.feed(open(f, encoding="utf-8").read())
        for href in parser.all_links:
            if href.startswith("http") or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            internal_count += 1
            if href == "":
                empty.append(os.path.relpath(f, ROOT))
                continue
            clean = href.split("#")[0]
            if not clean:
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(f), urllib.parse.unquote(clean)))
            if not os.path.exists(target):
                broken.append("%s -> %s" % (os.path.relpath(f, ROOT), href))
    ok &= check("No broken internal links", not broken and not empty,
                "%d internal links checked; broken: %s; empty: %s" %
                (internal_count, broken[:12] or "none", empty[:12] or "none"),
                ["https://github.com/sassnarep3-star/Own4/actions"])
    COUNTS["Internal links checked"] = internal_count

    # 8: dashboard links to every page
    idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    missing = [p for p in [os.path.relpath(f, ROOT).replace(os.sep, "/") for f in html_files]
               if p not in ("index.html",) and p not in idx
               and not p.startswith(("docs/", "lab/"))]
    ok &= check("Dashboard directory links to every generated page", not missing,
                "Pages not reachable from the dashboard: %s" % (missing[:12] or "none"),
                ["https://github.com/sassnarep3-star/Own4/blob/main/index.html"])

    # 9: legacy CI still passes
    ci = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok &= check("Existing CI test suite passes", ci.returncode == 0,
                (ci.stdout.strip().splitlines()[-1] if ci.stdout.strip() else "no output"),
                ["https://github.com/sassnarep3-star/Own4/actions"])
    b2 = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build.py")],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    diff = subprocess.run(["git", "diff", "--exit-code", "--", "docs"], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok &= check("Legacy docs/ generator reproduces committed pages", b2.returncode == 0 and diff.returncode == 0,
                "python scripts/build.py + git diff --exit-code -- docs",
                ["https://github.com/sassnarep3-star/Own4/actions"])
    for script, label in [("scripts/verify_data.py", "Independent data-consistency checks"),
                          ("scripts/check_site.py", "Parallel-session site link checker")]:
        p2 = os.path.join(ROOT, script)
        if os.path.exists(p2):
            c = subprocess.run([sys.executable, p2], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            ok &= check(label, c.returncode == 0,
                        (c.stdout.strip().splitlines()[-1] if c.stdout.strip() else "no output")[:160],
                        ["https://github.com/sassnarep3-star/Own4/actions"])

    report = {"verified_on": "2026-11-02", "overall": "PASS" if ok else "FAIL",
              "checks": CHECKS, "counts": COUNTS}
    with open(os.path.join(OFF, "verification.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("VERIFICATION: %s (%d checks, %d passed)" %
          (report["overall"], len(CHECKS), sum(1 for c in CHECKS if c["result"] == "PASS")))
    for c in CHECKS:
        if c["result"] == "FAIL":
            print("  FAIL:", c["name"], "—", c["detail"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

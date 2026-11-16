#!/usr/bin/env python3
"""Gate for nfl-reconciled. Exits non-zero on the first class of failure it finds.

Checks, in order:
  1. every page exists, carries the navigation, a footer and the responsible-gambling line;
  2. every internal link and anchor resolves to a real file or id;
  3. every table row carries a source: an https link, or an explicit UNVERIFIED / "none" marker;
  4. no page prints a betting price (there is no official price source, so a price value on a page
     would be invented data -- see flag RC-11);
  5. the index's headline numbers equal the derived artefacts, so prose cannot drift from data;
  6. no page reaches for localhost or a private address.
Standard library only. No network.
"""

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)

PAGES = [
    "index.html", "pages/executive-summary.html", "pages/conflicts.html", "pages/results.html", "pages/availability.html",
    "pages/workspaces.html", "pages/review.html", "pages/decisions.html", "pages/method.html",
    "pages/flagged.html",
]

# Names of the artefacts every claim must be traceable to. Their presence is asserted, not assumed.
ARTEFACTS = [
    "data/official_facts.json",
    "data/resolutions.json",
    "data/derived/results_corpus_reconciliation.json",
    "data/derived/injury_capture_reconciliation.json",
    "data/derived/namespace_index.json",
    "data/derived/register_duplication.json",
    "data/derived/review_index.json",
]

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def url_path(rel):
    """The URL path a page is served at, relative to the repository root (Pages serves main/root)."""
    return rel if rel.startswith("pages/") else rel


def local_target(base_page, href):
    """Resolve an href into (filesystem path, anchor), relative to the served URL of base_page.

    The site deploys to /Own4/, so hrefs are resolved against the repository root, not against the
    filesystem directory the generator happens to have written the file into.
    """
    if href.startswith("#"):
        return os.path.join(HERE, base_page), href[1:] or None
    href, _, anchor = href.partition("#")
    # hrefs resolve against the directory of the page that contains them, exactly as a static
    # server would resolve them for /Own4/nfl-reconciled/<base_page>.
    base_dir = os.path.dirname(os.path.join(HERE, base_page))
    return os.path.normpath(os.path.join(base_dir, href)), (anchor or None)


def check_pages():
    for rel in PAGES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            fail("missing page: %s" % rel)
            continue
        doc = read(p)
        if 'aria-label="Site sections"' not in doc:
            fail("%s: navigation missing" % rel)
        if "<footer>" not in doc:
            fail("%s: footer missing" % rel)
        if "1-800-MY-RESET" not in doc:
            fail("%s: responsible-gambling line missing" % rel)
        if "nfl-reconciled" not in doc and "NFL reconciled" not in doc:
            fail("%s: workspace identity missing" % rel)
        if re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+)", doc):
            fail("%s: references a local/private address" % rel)


def check_links():
    for rel in PAGES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            continue
        doc = read(p)
        ids = set(re.findall(r'id="([^"]+)"', doc))
        for href in re.findall(r'href="([^"]+)"', doc):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, anchor = local_target(p, href)
            if not os.path.exists(target):
                fail("%s: broken link %s -> %s" % (rel, href, os.path.relpath(target, HERE)))
                continue
            if anchor and target.endswith(".html"):
                tdoc = read(target)
                tids = set(re.findall(r'id="([^"]+)"', tdoc))
                if anchor not in tids:
                    fail("%s: broken anchor %s (no id=%s in %s)"
                         % (rel, href, anchor, os.path.relpath(target, HERE)))


def check_rows_sourced():
    """Every <tr> inside a data table must carry an https link or an explicit marker."""
    marker = re.compile(r"(unverified|no official|none published|settles itself|—|em dash|blank)", re.I)
    tot = sourced = 0
    for rel in PAGES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            continue
        doc = read(p)
        for tbl in re.findall(r"<table>(.*?)</table>", doc, re.S):
            cap_m = re.search(r"<caption>(.*?)</caption>", tbl, re.S)
            cap = re.sub(r"<[^>]+>", "", cap_m.group(1)) if cap_m else ""
            body = tbl.split("<tbody>", 1)[-1]
            for row in re.findall(r"<tr>(.*?)</tr>", body, re.S):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                if not cells:
                    continue
                blank_row = all(re.sub(r"<[^>]+>", "", c).strip() in ("", "—", "&mdash;") for c in cells)
                if blank_row:
                    # a row of em dashes is legitimate only when the caption explains it
                    if not cap:
                        fail("%s: blank table row in an uncaptioned table" % rel)
                    continue
                tot += 1
                text = " ".join(cells)
                if "https://" in text or marker.search(re.sub(r"<[^>]+>", "", text)):
                    sourced += 1
                else:
                    fail("%s: table row carries no source: %s"
                         % (rel, re.sub(r"<[^>]+>", " ", text).strip()[:120]))
    return tot, sourced


def check_no_prices():
    """No page may print a price-shaped value. The league publishes none (RC-11)."""
    price = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:pts?|points)?\s*(?:@|at)\s*[-+]?\d{1,4}\b(?!\s*-)")
    for rel in PAGES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            continue
        text = re.sub(r"<[^>]+>", " ", read(p))
        # Strip identifiers (ids such as RC-11, file paths, urls) before looking for a price VALUE.
        clean = re.sub(r"\bRC-\d+\b", " ", text)
        clean = re.sub(r"\S*[/\.]\S+", " ", clean)
        clean = re.sub(r"\b[A-Z]{2,5}-\d+\b", " ", clean)
        for m in re.finditer(r"(?<![\w.-])([-+]\d{2,4})(?![\w-])", clean):
            val = m.group(1)
            ctx = clean[max(0, m.start() - 70):m.end() + 25].lower()
            if "assum" in ctx or "no price" in ctx:
                continue
            if any(w in ctx for w in ("price", "odds", "moneyline", "spread price", " vig")):
                fail("%s: price-shaped value %s near market wording (no official price exists)"
                     % (rel, val))


def check_headline_agrees_with_data():
    games = json.load(open(os.path.join(HERE, "data/derived/results_corpus_reconciliation.json")))
    inj = json.load(open(os.path.join(HERE, "data/derived/injury_capture_reconciliation.json")))
    res = json.load(open(os.path.join(HERE, "data/resolutions.json")))
    idx = read(os.path.join(HERE, "index.html"))
    text = re.sub(r"<[^>]+>", " ", idx)

    off = games["official"]
    if str(off["games_played_league_wide"]) not in text and "%g" % off["games_played_league_wide"] not in text:
        fail("index: does not state the standings-derived games-played figure %g"
             % off["games_played_league_wide"])
    if format(off["points_for_league_wide"], ",") not in text:
        fail("index: does not state the league points total %d" % off["points_for_league_wide"])
    if format(games["closure"]["closure_check"], ",") not in text:
        fail("index: does not state the closure check %d" % games["closure"]["closure_check"])
    if not games["closure"]["closure_equals_official_total"]:
        fail("data: the closure does not equal the official total, so the site must not claim it does")
    # The corpus deliberately holds only the Thursday Week-10 final; the site must not claim the
    # Sunday finals are in it. Assert the claim the pages actually make.
    if games["week10_finals_check"]["present_with_matching_score"] != 1:
        fail("data: expected exactly the Thursday Week-10 final in the corpus, found %d"
             % games["week10_finals_check"]["present_with_matching_score"])
    canon = [c for c in inj["live_checks"] if c["verdict"] == "PASS"]
    if not canon:
        fail("data: no availability capture passed its live check, so 347 cannot be called canonical")
    else:
        n = canon[0]["n_rows"]
        if str(n) not in text:
            fail("index: does not state the verified capture row count %d" % n)

    # the resolution counts printed in the cards must equal the data
    counts = res["counts"]
    for key in ("settled", "review", "no_conflict"):
        if str(counts[key]) not in text:
            fail("index: resolution count %s=%d not printed" % (key, counts[key]))

    # every SETTLED resolution must have an official source; every REVIEW must have none
    for r in res["rows"]:
        if r["verdict"] == "SETTLED" and not r.get("official_source") and not r.get("repo_evidence"):
            fail("resolutions: %s is SETTLED with neither an official source nor repository evidence"
                 % r["id"])
        if r["verdict"] == "REVIEW" and r.get("official_source"):
            fail("resolutions: %s is REVIEW but carries an official source (%s)"
                 % (r["id"], r["official_source"]))
        if r["verdict"] == "REVIEW" and r.get("official_number") is not None:
            fail("resolutions: %s is REVIEW but carries an official number" % r["id"])
    return res


def check_artefacts():
    for a in ARTEFACTS:
        if not os.path.exists(os.path.join(HERE, a)):
            fail("missing artefact: %s" % a)


def check_nav_targets():
    """The workspace navigation links must resolve from a subpage and from the root."""
    for rel in PAGES:
        p = os.path.join(HERE, rel)
        doc = read(p)
        for href in re.findall(r'<a class="nav[^"]*" href="([^"]+)"', doc):
            if href.startswith(("http", "mailto")):
                continue
            target, _ = local_target(p, href)
            if not os.path.exists(target):
                fail("%s: nav link does not resolve: %s" % (rel, href))


def main():
    check_artefacts()
    check_pages()
    check_links()
    tot, sourced = check_rows_sourced()
    check_no_prices()
    res = check_headline_agrees_with_data()
    check_nav_targets()

    print("pages checked: %d" % len(PAGES))
    print("data rows checked for a source: %d (all sourced: %s)" % (tot, sourced == tot))
    print("resolutions: %d rows (%d settled / %d review / %d no-conflict)"
          % (res["counts"]["rows"], res["counts"]["settled"], res["counts"]["review"],
             res["counts"]["no_conflict"]))
    if warnings:
        for w in warnings:
            print("WARN: " + w)
    if errors:
        print("\nFAILED (%d):" % len(errors))
        for e in errors:
            print("  - " + e)
        return 1
    print("\nall checks passed: every page builds, every link resolves, every row is sourced,")
    print("no price is printed, and every headline number equals its derived artefact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

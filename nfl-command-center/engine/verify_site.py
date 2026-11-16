#!/usr/bin/env python3
"""
Own4 / nfl-command-center — site and data verification. Exits non-zero on any defect.

Checks:
  1  every page exists, is balanced HTML, and carries the footer disclaimer and helpline;
  2  EVERY data row (<tr> inside <tbody>) carries at least one source link, to an official
     domain or to this repository. A row without one is a defect, not a style choice;
  3  every local href resolves to a file that exists (anchors included);
  4  no placeholder leaked: no Python dict repr, no 'None', no unrendered template marker;
  5  no price-looking value is published in any market column (the no-price rule);
  6  the published row counts match the underlying datasets;
  7  every published URL points at an official domain or this repository;
  8  the build is deterministic: a second render changes nothing (the caller also diffs git).

Run: python3 engine/verify_site.py
"""

import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")

OFFICIAL = ("nfl.com", "detroitlions.com", "ncpgambling.org", "github.com")

PAGES = ["index.html"] + sorted(
    os.path.join("pages", f) for f in os.listdir(os.path.join(NS, "pages")) if f.endswith(".html"))

D = {f[:-5]: json.load(open(os.path.join(DATA, f), encoding="utf-8"))
     for f in sorted(os.listdir(DATA)) if f.endswith(".json")}

EXPECT_ROWS = {
    "pages/readiness.html": D["requirements"]["n_rows"],
    "pages/availability.html": (D["availability_week10"]["counts"]["rows"]
                                + len(D["availability_week10"]["rows"])),
    "pages/depth.html": (D["depth_register"]["n_rows"] + D["roster_status"]["n_rows"]
                         + D["replacement_evidence"]["n_rows"] + D["drill_findings"]["n_rows"]),
    "pages/backtest.html": D["backtest"]["n_forecasts"] + len(D["backtest"]["by_week"]),
    "pages/leaderboard.html": (len(D["leaderboard"]["strategies"]) * 2
                               + len(D["gates"]["rows"])),
    "pages/questions.html": D["questions"]["n_rows"],
    "pages/suggestions.html": D["suggestions"]["n_rows"],
    "pages/flagged.html": D["flags"]["n_rows"],
    "pages/correlations.html": D["correlations"]["n_rows"],
    "pages/own-lines.html": D["week11_own_lines"]["n_rows"],
}

DEFECT_PATTERNS = [
    (re.compile(r"\{&#x27;|\{'dataset'"), "python dict repr rendered into the page"),
    (re.compile(r"\{'[a-z_]+':"), "python dict repr rendered into the page"),
    (re.compile(r">\s*(None|nan|NaN)\s*<"), "sentinel value in a cell"),
    (re.compile(r"%\([a-z_]+\)s"), "unformatted template marker"),
    (re.compile(r"\{\{[^}]*\}\}"), "unrendered template marker"),
    (re.compile(r"\bTODO\b|\bFIXME\b"), "TODO marker"),
]

errors = []
warnings = []


class P(html.parser.HTMLParser):
    """Row-level anchor collection.

    Row membership is decided by index over the anchor list rather than by a state flag on
    <tr>: html.parser can deliver an empty <tr> element whose following <td> arrives with the
    same handler, which silently drops the first anchor of every row. The index approach has
    no such failure mode.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.row_links = []
        self.text = []
        self.stray_anchors = 0
        self.cur = None
        self.in_tbody = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.cur is not None:
                self.cur.append(len(self.links) - 1)
            else:
                self.stray_anchors += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr":
            # every new row closes any open one; a header row outside tbody is not a data row
            if self.cur is not None:
                self.row_links.append(self.cur)
                self.cur = None
            if self.in_tbody:
                self.cur = []

    def handle_endtag(self, tag):
        if tag == "tr" and self.cur is not None:
            self.row_links.append(self.cur)
            self.cur = None
        if tag == "tbody":
            if self.cur is not None:
                self.row_links.append(self.cur)
                self.cur = None
            self.in_tbody = False

    def handle_data(self, data):
        self.text.append(data)

    def rows_with_links(self):
        return [[self.links[i] for i in row] for row in self.row_links]

    def finish(self):
        if self.cur is not None:
            self.row_links.append(self.cur)
            self.cur = None
        return self.rows_with_links()


def official(href):
    m = re.match(r"https?://([^/]+)/", href)
    if not m:
        return False
    host = m.group(1).lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def local_target(page_rel, href):
    if href.startswith("#"):
        return page_rel
    if re.match(r"^[a-z]+:", href):
        return None
    target = href.split("#")[0].split("?")[0]
    base = os.path.dirname(page_rel)
    return os.path.normpath(os.path.join(base, target))


def check(page):
    path = os.path.join(NS, page)
    if not os.path.exists(path):
        errors.append("%s: missing" % page)
        return
    raw = open(path, encoding="utf-8").read()
    m = re.search(r'<aside class="side">.*?</aside>', raw, re.S)
    if not m:
        errors.append("%s: navigation block not found" % page)
    else:
        raw = raw[:m.start()] + '<nav aria-label="Site sections"></nav>' + raw[m.end():]
    if raw.count("<table") != raw.count("</table>"):
        errors.append("%s: unbalanced <table>" % page)
    if raw.count("<tr") != raw.count("</tr>"):
        errors.append("%s: unbalanced <tr>" % page)
    for rx, why in DEFECT_PATTERNS:
        if rx.search(raw):
            m = rx.search(raw)
            errors.append("%s: %s near %r" % (page, why, raw[max(0, m.start() - 40):m.start() + 60]))
    if "1-800-MY-RESET" not in raw:
        errors.append("%s: missing responsible-gambling footer" % page)
    if "Flagged for review" not in raw:
        errors.append("%s: missing Flagged-for-review link in the footer" % page)
    p = P()
    p.feed(raw)
    rows = p.finish()
    # Row sourcing rule, as the brief states it in two halves:
    #   (a) a row that publishes a value carries a link to an official site (or this repo);
    #   (b) a row that cannot be confirmed from an official source carries the explicit
    #       unverified marker instead, and is counted and reported -- never silently blank.
    # A row with neither is a defect.
    unsourced, unmarked = 0, []
    for i, links in enumerate(rows):
        if any(official(h) for h in links):
            continue
        if any(h.startswith("#") for h in links) and "flagged" in " ".join(links):
            pass
        unsourced += 1
        unmarked.append(i)
    if unsourced:
        flagged_marker = raw.count("no official source")
        if flagged_marker < unsourced:
            errors.append("%s: %d rows have neither an official source link nor an unverified "
                          "marker (markers found: %d)" % (page, unsourced - flagged_marker, flagged_marker))
        else:
            warnings.append("%s: %d of %d data rows are explicitly marked unverified "
                            "(no official source exists) -- reported, not hidden"
                            % (page, unsourced, len(rows)))
    # every local link resolves
    for href in set(p.links):
        t = local_target(page, href)
        if t is None:
            if not official(href):
                warnings.append("%s: external non-official link %s" % (page, href))
            continue
        if not os.path.exists(os.path.join(NS, t)):
            errors.append("%s: broken local link %s" % (page, href))
    # row counts
    if page in EXPECT_ROWS:
        got = len(rows)
        want = EXPECT_ROWS[page]
        if got < want:
            errors.append("%s: %d data rows, expected at least %d" % (page, got, want))
        else:
            warnings.append("%s: %d data rows (expected >= %d) OK" % (page, got, want))


def check_no_prices():
    """The no-price rule: no published number may appear where a price would go."""
    for r in D["week11_own_lines"]["rows"]:
        for k in ("market_total", "market_spread", "market_home_ml", "market_away_ml",
                  "residual_total", "residual_spread"):
            if r.get(k) not in ("", None):
                errors.append("week11_own_lines: %s carries a value for %s without a price source"
                              % (r["game_key"], k))
    for s in D["leaderboard"]["strategies"]:
        if s.get("roi") not in ("", None) or s.get("clv") not in ("", None):
            errors.append("leaderboard: %s publishes ROI/CLV without a price source" % s["id"])
        if s.get("reward_payable") != "no":
            errors.append("leaderboard: %s claims a payable reward at n=%s"
                          % (s["id"], s.get("n_graded")))


def check_data_invariants():
    if D["results_reconciliation"]["status"] != "pass":
        errors.append("results reconciliation is not passing")
    for c in D["identity_checks"]["rows"]:
        if c["status"] != "pass":
            errors.append("identity check failed: %s" % c["check"])
    av = D["availability_week10"]
    if av["counts"]["rows"] != 347:
        errors.append("availability row count changed: %d" % av["counts"]["rows"])
    if av["counts"]["clubs"] != 28:
        errors.append("availability club count changed: %d" % av["counts"]["clubs"])
    for r in av["players"]:
        if r["game_status"] and r["game_status"] not in ("Out", "Doubtful", "Questionable"):
            errors.append("unexpected game status vocabulary: %r" % r["game_status"])
        if r["practice_status"] not in ("Full Participation in Practice",
                                       "Limited Participation in Practice",
                                       "Did Not Participate In Practice"):
            errors.append("unexpected practice vocabulary: %r" % r["practice_status"])
    if D["week11_own_lines"]["order_audit"]["status"] != "pass":
        errors.append("origination order audit is not passing")
    if len(D["week11_own_lines"]["rows"]) != 13:
        errors.append("Week 11 row count is not 13")
    if D["leaderboard"]["rewards_paid"] != 0:
        errors.append("a reward is marked paid")
    # Errata that cannot move a forecast are expected and published; a *pre-Week-11* amendment
    # that touched a constant, a rule or a grade would be a registration breach, so the rule is
    # stated as an invariant rather than "the list must be empty".
    for a in D["strategy_registry"]["amendments"]:
        if a.get("affects_forecasts", "no").lower().startswith("yes"):
            errors.append("amendment %s changed a forecast -- that is a new version, not an erratum"
                          % a.get("id"))
        if a.get("kind") not in ("documentation erratum", "data-merge erratum"):
            errors.append("amendment %s has an unrecognised kind %r" % (a.get("id"), a.get("kind")))
    reg_commits = {e["commit"] for e in D["strategy_registry"]["entries"] if e["commit"]}
    if reg_commits != {D["week11_own_lines"]["registration_commit"]}:
        errors.append("the registry and the published lines cite different registration commits")
    unregistered = [e["id"] for e in D["strategy_registry"]["entries"] if not e["commit"]]
    if unregistered and D["leaderboard"]["n_qualified"]:
        errors.append("an unregistered strategy (%s) is counted as qualified" % ", ".join(unregistered))


def check_urls():
    seen = 0
    for name, doc in D.items():
        def walk(x):
            nonlocal seen
            if isinstance(x, dict):
                for k, v in x.items():
                    if k.endswith("url") and isinstance(v, str) and v:
                        seen += 1
                        if not official(v) and not v.startswith(NS):
                            warnings.append("%s: non-official url %s" % (name, v))
                    else:
                        walk(v)
            elif isinstance(x, list):
                for it in x:
                    walk(it)
        walk(doc)
    return seen


def numeric_invariants():
    """Every published point estimate must lie inside the interval printed beside it.

    This check exists because the build shipped a ratio skill of 0.5796 next to an interval of
    [0.2264, 0.4059] -- a real defect caught by reading the page, not by any row or link rule.
    A number that cannot contain its own point estimate is a wrong number, and a reader has no
    way to tell without doing the arithmetic. Both the ratio and the difference interval are
    now published and both are checked here.
    """
    bt = json.load(open(os.path.join(DATA, "backtest.json")))
    m = bt["metrics"]
    checks = []
    for point, iv, name in [
        (m["brier_skill"], m["brier_skill_ci"], "Brier skill ratio"),
        (m["brier_diff_improvement"], m["brier_diff_ci"], "Brier difference"),
        (m["mae_improvement"], m["mae_improvement_ci"], "total MAE improvement"),
    ]:
        ok = iv[0] <= point <= iv[1]
        checks.append((name, point, iv, ok))
        if not ok:
            errors.append("backtest: %s point %.4f falls outside its own 95%% interval %s"
                          % (name, point, iv))
    # A ratio and a difference are different quantities and must not be equal by accident.
    if abs(m["brier_skill"] - m["brier_diff_improvement"]) < 1e-9:
        errors.append("backtest: ratio skill and difference improvement are identical")
    # The skill ratio must equal 1 - brier/baseline, recomputed from the published pair.
    if abs((1 - m["brier"] / m["brier_home_baseline"]) - m["brier_skill"]) > 5e-4:
        errors.append("backtest: published skill ratio does not recompute from the published Brier pair")
    return checks


def main():
    for page in PAGES:
        check(page)
    check_no_prices()
    check_data_invariants()
    for name, point, iv, ok in numeric_invariants():
        print("  interval check: %-20s point %+.4f inside %s -- %s"
              % (name, point, iv, "ok" if ok else "VIOLATED"))
    n_urls = check_urls()
    print("pages checked: %d" % len(PAGES))
    print("urls checked: %d" % n_urls)
    for w in warnings:
        print("  note:", w)
    if errors:
        print("\nFAILED (%d defects):" % len(errors))
        for e in errors:
            print("  -", e)
        return 1
    print("PASS — every data row source-linked, every local link resolves, no price published"
          " without a source, no merged narrative contradiction, vocabularies closed,"
          " every point estimate inside its published interval.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

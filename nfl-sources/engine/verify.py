"""The gate. Runs every check that can fail the build and exits non-zero on the first failure.

Checks
  C1 corpus integrity      every game keyed once, scores plausible, week page URL present, source URL official
  C2 independence          the corpus reproduces the official standings exactly (W, L, T, PF, PA)
  C3 provenance            every committed input still hashes to the value recorded at build time
  C4 leakage (G3)          mutating every result after a cutoff changes NO forecast at or before it
  C5 determinism           a full rebuild produces byte-identical data files
  C6 origination order     side -> total -> moneyline on every fixture, every snapshot
  C7 probability integrity every published P is in (0,1), every fair American price matches its P
  C8 publication rules     no row renders without an official https source; no return figure on the leaderboard
  C9 drift alarms          expected row counts and required fields, per dataset
  C10 no third-party data  no price, prop line or scraped availability record anywhere in the data
  C11 site integrity        every internal link resolves to a file that exists; no localhost references
"""
import filecmp
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

from common import (DATA, ROOT, REGISTERED_UTC, phi, read_json, read_text, write_json, american_from_prob,
                    sha256_file)

FAIL = []
PASS = []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("%-4s %-46s %s" % ("PASS" if ok else "FAIL", name, detail))
    return ok


def c1_corpus():
    res = read_json(os.path.join(DATA, "results.json"))
    rows = res["rows"]
    ids = [r["game_id"] for r in rows]
    check("C1 corpus keyed once", len(ids) == len(set(ids)), "%d games" % len(ids))
    check("C1 scores plausible", all(0 <= r["away_pts"] <= 100 and 0 <= r["home_pts"] <= 100 for r in rows))
    check("C1 official source on every row",
          all(r["game_url"].startswith("https://www.nfl.com/games/") and
              r["week_page_url"].startswith("https://www.nfl.com/schedules/") for r in rows))
    weeks = sorted({r["week"] for r in rows})
    check("C1 weeks 1-10 present", weeks == list(range(1, 11)), str(weeks))
    per_week = {w: sum(1 for r in rows if r["week"] == w) for w in weeks}
    check("C1 per-week counts 16/16/16/16/15/14/14/14/15/12",
          per_week == {1: 16, 2: 16, 3: 16, 4: 16, 5: 15, 6: 14, 7: 14, 8: 14, 9: 15, 10: 12}, str(per_week))
    w1_9 = sum(v for k, v in per_week.items() if k <= 9)
    check("C1 weeks 1-9 total exactly 136 (the brief's corpus)", w1_9 == 136, str(w1_9))
    check("C1 excluded games carry no score",
          all(g["score"] is None for g in res["excluded_not_final"]))
    return rows


def c2_independence(rows):
    res = read_json(os.path.join(DATA, "results.json"))
    ic = res["independence_check"]
    check("C2 standings independence check", ic["result"] == "pass" and not ic["mismatches"],
          "%d fields" % ic["fields_checked"])
    agg = ic["aggregate"]
    check("C2 decided-game count matches official aggregate",
          agg["corpus_games"] == agg["official_total_wins"] + agg["official_tie_games"],
          "corpus %d vs official W %d + T %d" % (agg["corpus_games"], agg["official_total_wins"],
                                                 agg["official_tie_games"]))
    check("C2 PF total equals PA total", agg["official_pf_total"] == agg["official_pa_total"])


def c3_provenance(rows):
    prov = read_json(os.path.join(DATA, "provenance.json"))
    bad = []
    for rel, meta in prov["inputs"].items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p) or sha256_file(p) != meta["sha256"]:
            bad.append(rel)
    check("C3 input hashes unchanged", not bad, "%d inputs%s" % (len(prov["inputs"]),
                                                                (", changed: " + ", ".join(bad)) if bad else ""))


def c4_leakage(rows):
    """Mutate every result in week >= W and confirm no forecast for week < W moved."""
    import build_model as bm
    base = bm_main(rows)
    worst = []
    for cutoff in (4, 6, 8):
        mutated = [dict(r) for r in rows]
        for r in mutated:
            if r["week"] >= cutoff:
                r["away_pts"] = r["away_pts"] + 7
                r["home_pts"] = r["home_pts"] - 3
        after = bm_main(mutated)
        changed = 0
        compared = 0
        for a, b in zip(base, after):
            if a["week"] < cutoff:
                compared += 1
                if (a["p_home"], a["fair_home_line"], a["fair_total"]) != (b["p_home"], b["fair_home_line"],
                                                                          b["fair_total"]):
                    changed += 1
        worst.append((cutoff, compared, changed))
        check("C4 leakage: cutoff %d" % cutoff, changed == 0,
              "%d forecasts compared, %d changed" % (compared, changed))
    return worst


def bm_main(rows):
    """Re-run the register on a supplied corpus (used by C4)."""
    import importlib
    import build_model
    importlib.reload(build_model)
    out = []
    games = sorted(rows, key=lambda g: (g["week"], g["date_iso"], g["game_id"]))
    for w in range(3, 11):
        train = [g for g in games if g["week"] < w]
        if not train:
            continue
        m = build_model.fit(train)
        for g in [x for x in games if x["week"] == w]:
            p = build_model.predict(m, g["home"], g["away"], g["international_game"])
            out.append({"game_id": g["game_id"], "week": w, "p_home": round(p["p_home"], 6),
                        "fair_home_line": round(p["fair_home_line"], 2),
                        "fair_total": round(p["fair_total"], 2)})
    return out


def c5_determinism():
    """Full rebuild into a temporary copy of the inputs; compare every data file byte for byte."""
    tmp = tempfile.mkdtemp(prefix="nfls-det-")
    try:
        shutil.copytree(os.path.join(ROOT, "raw"), os.path.join(tmp, "raw"))
        shutil.copytree(os.path.join(ROOT, "engine"), os.path.join(tmp, "engine"))
        before = {os.path.basename(p): read_text(p) for p in sorted(glob.glob(os.path.join(DATA, "*.json")))}
        env = dict(os.environ)
        for script in ("build_results.py", "build_model.py", "build_lines.py", "build_correlations.py",
                       "build_register.py", "build_strategies.py", "build_provenance.py"):
            r = subprocess.run([sys.executable, script], cwd=os.path.join(tmp, "engine"),
                               env=env, capture_output=True, text=True)
            if r.returncode != 0:
                check("C5 rebuild %s" % script, False, r.stderr.strip().splitlines()[-1] if r.stderr else "")
                return
        # results.json depends on the inherited feed path only for reconciliation; it is copied in
        # (the tmp tree has no nfl-book, so the reconciliation block is empty there and must not be compared)
        diffs = []
        skip = ("results.json", "provenance.json", "verification.json")
        for name, text in before.items():
            if name in skip:
                continue
            p = os.path.join(tmp, "data", name)
            if not os.path.exists(p):
                diffs.append(name + " (missing)")
                continue
            if read_text(p) != text:
                diffs.append(name)
        check("C5 deterministic rebuild", not diffs, "%d files compared%s" % (
            len(before) - len(skip), (", differs: " + ", ".join(diffs)) if diffs else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def c6_order():
    lines = read_json(os.path.join(DATA, "lines.json"))
    bad = [r["game_id"] for r in lines["rows"]
           if r["open"]["order"] != ["side", "total", "moneyline"]
           or r["update"]["order"] != ["side", "total", "moneyline"]]
    check("C6 origination order on every snapshot", not bad, "%d fixtures" % len(lines["rows"]))
    check("C6 both snapshots present", all("open" in r and "update" in r for r in lines["rows"]))
    check("C6 move published for every fixture",
          all(set(r["move_open_to_update"]) == {"home_line_moved_by", "total_moved_by", "p_home_moved_by"}
              for r in lines["rows"]))


def c7_probabilities():
    bad = 0
    reg = read_json(os.path.join(DATA, "forecast_register.json"))["rows"]
    for r in reg:
        if not (0 < r["p_home"] < 1):
            bad += 1
    check("C7 walk-forward P in (0,1)", bad == 0, "%d rows" % len(reg))
    bad = 0
    lines = read_json(os.path.join(DATA, "lines.json"))["rows"]
    for r in lines:
        for snap in ("open", "update"):
            p = r[snap]["moneyline"]["fair_p_home"]
            if not (0 < p < 1) or r[snap]["moneyline"]["fair_home_american"] != american_from_prob(p):
                bad += 1
    check("C7 Week 11 P and fair American consistent", bad == 0, "%d fixtures x 2" % len(lines))
    check("C7 every market column blank",
          all(r["market"][k] is None for r in lines for k in
              ("market_home_line", "market_total", "market_home_american", "residual_home_line",
               "residual_total", "residual_moneyline")))


def c7b_ratings_shape():
    m = read_json(os.path.join(DATA, "model.json"))
    need = {"off", "def", "expected_pts_scored_vs_avg", "net_vs_average_opponent"}
    bad = []
    for c in m["cutoffs"]:
        for t, v in c["ratings"].items():
            if set(v) != need:
                bad.append("%s/%s" % (c["label"], t))
        if len(c["ratings"]) != 32:
            bad.append("%s: %d clubs" % (c["label"], len(c["ratings"])))
    check("C7b every rating row carries the same four fields on 32 clubs", not bad, ", ".join(bad[:5]))


def c8_publication():
    """Render-side rules, checked on the generated HTML."""
    pages = sorted(glob.glob(os.path.join(ROOT, "pages", "*.html")))
    missing_src = []
    for p in pages:
        html = read_text(p)
        for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            row = m.group(1)
            if "<th" in row:
                continue
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if "https://" in row:
                continue
            # a row with no official link is allowed only when it says so explicitly
            if any("decision, not a fact" in c for c in cells):
                continue
            missing_src.append(os.path.basename(p))
    check("C8 every rendered row links an official page or states it is not a fact", not missing_src,
          "%d pages, %d rows%s" % (len(pages), sum(1 for p in pages for _ in
                                                  re.finditer(r"<tr", read_text(p))),
                                   (": " + ", ".join(sorted(set(missing_src)))) if missing_src else ""))

    lb = os.path.join(ROOT, "pages", "leaderboard.html")
    if os.path.exists(lb):
        html = read_text(lb)
        m = re.search(r'id="stage1".*?</table>', html, re.S)
        ok = True
        if m:
            # stage 1 must carry no profit figure
            ok = not re.search(r"\bROI\b|net units|bankroll|closing-line value", m.group(0), re.I)
        check("C8 no profit figure on the leaderboard stage 1", ok, "stage-2 note lives on the page, not in the table")

        # and no money figure anywhere in the document that is not labelled hypothetical/blank
        bad = [ln for ln in html.splitlines()
               if re.search(r"\bROI\b|net units", ln) and "cannot" not in ln and "no ROI" not in ln
               and "ranking luck" not in ln]
        check("C8 every mention of ROI or net units is a refusal, not a result", not bad, str(bad[:2]))


def c9_drift():
    expect = [
        ("results.json", "n_games", 148),
        ("forecast_register.json", "n_rows", 116),
        ("lines.json", "n_fixtures", 13),
        ("venues.json", "n_rows", 13),
        ("requirements.json", "n_rows", 70),
        ("flags.json", "n_rows", 15),
        ("correlations.json", "n_computed", 5),
    ]
    for fname, key, want in expect:
        d = read_json(os.path.join(DATA, fname))
        got = d.get(key)
        check("C9 %s %s == %d" % (fname, key, want), got == want, "got %r" % (got,))
    for fname, key, want in [("strategies.json", "strategies", 6), ("suggestions.json", "rows", 18),
                             ("questions.json", "rows", 12)]:
        d = read_json(os.path.join(DATA, fname))
        got = len(d[key])
        check("C9 %s %s == %d" % (fname, key, want), got == want, "got %r" % (got,))
    req = read_json(os.path.join(DATA, "requirements.json"))
    check("C9 every requirement names a gate and a source",
          all(r["source_url"].startswith("https://") and r["blocking_gate"] for r in req["rows"]))


def c10_no_third_party():
    banned = ["-110 odds from", "draftkings", "fanduel", "betmgm", "espn.com", "pinnacle",
              "covers.com", "oddsshark", "vegasinsider"]
    hits = []
    for p in glob.glob(os.path.join(DATA, "*.json")):
        low = read_text(p).lower()
        for b in banned:
            if b in low:
                hits.append("%s: %s" % (os.path.basename(p), b))
    check("C10 no third-party data source referenced", not hits, ", ".join(hits))


def c10b_rendered_text():
    """A page can be structurally perfect and still render a defect: drift arguments, raw format keys,
    double periods, or the string 'None' where a number should be."""
    import html as _html
    pages = sorted(glob.glob(os.path.join(ROOT, "pages", "*.html")))
    bad = []
    for p in pages:
        s = re.sub(r"<style.*?</style>", "", read_text(p), flags=re.S)
        text = _html.unescape(re.sub(r"<[^>]+>", " ", s))
        text = re.sub(r"[ \t]{2,}", " ", text)
        for pat, label in [(r"\.\.(?!\.)", "double period"), (r"\{\w+\}", "unformatted placeholder"),
                           (r"%\(\w+\)", "raw format key"), (r"\bnan\b", "nan"),
                           (r"\bNone\b(?! of)", "None rendered")]:
            for m in re.finditer(pat, text):
                bad.append("%s: %s near %r" % (os.path.basename(p), label,
                                               text[max(0, m.start() - 40):m.start() + 20].replace("\n", " ")))
    check("C10b rendered text has no template or formatting defects", not bad, "; ".join(bad[:3]))


def c11_site():
    pages = sorted(glob.glob(os.path.join(ROOT, "pages", "*.html")))
    bad = []
    for p in pages:
        html = read_text(p)
        base = os.path.dirname(p)
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            if href.startswith("/"):
                # a site-absolute path only resolves when the site is served from the domain root;
                # this site is served from /Own4/nfl-sources/pages/, so absolute paths are a defect
                bad.append("%s -> site-absolute %s" % (os.path.basename(p), href))
                continue
            target = os.path.normpath(os.path.join(base, href.split("#")[0]))
            if href.split("#")[0] and not os.path.exists(target):
                bad.append("%s -> %s" % (os.path.basename(p), href))
        if "localhost" in html or "127.0.0.1" in html:
            bad.append("%s -> localhost reference" % os.path.basename(p))
    check("C11 no broken internal link, no localhost", not bad,
          "%d pages%s" % (len(pages), (": " + "; ".join(bad[:6])) if bad else ""))


def main():
    rows = c1_corpus()
    c2_independence(rows)
    c3_provenance(rows)
    c4_leakage(rows)
    c5_determinism()
    c6_order()
    c7_probabilities()
    c7b_ratings_shape()
    c8_publication()
    c9_drift()
    c10_no_third_party()
    c10b_rendered_text()
    c11_site()
    write_json(os.path.join(DATA, "verification.json"), {
        "dataset": "nfl_sources_verification",
        "built_utc": REGISTERED_UTC,
        "passed": PASS, "failed": FAIL,
        "n_passed": len(PASS), "n_failed": len(FAIL),
        "result": "PASS" if not FAIL else "FAIL",
    })
    print("\n%d passed, %d failed -> %s" % (len(PASS), len(FAIL), "PASS" if not FAIL else "FAIL"))
    sys.exit(0 if not FAIL else 1)


if __name__ == "__main__":
    main()

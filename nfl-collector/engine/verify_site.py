"""Publication contract for the nfl-collector site. Exit 1 on any failure.

  1. every internal link resolves to a committed file;
  2. no localhost/127.0.0.1/0.0.0.0 links anywhere;
  3. no price values on any page (no official price source exists — DEC-1 = B);
  4. every table row carries a source link or is explicitly marked class="derived";
  5. every data table has a generated coverage line under it;
  6. the index state cards match the artefacts (spot checks, computed not typed);
  7. a rebuild is byte-identical (determinism).
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load

ALLOWED_EXTERNAL = re.compile(r"^https?://([a-z0-9.-]*\.)?(nfl\.com|packers\.com|github\.com|sassnarep3-star\.github\.io)/")


def pages():
    out = {}
    out["index.html"] = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    pdir = os.path.join(HERE, "pages")
    for f in sorted(os.listdir(pdir)):
        if f.endswith(".html"):
            out["pages/" + f] = open(os.path.join(pdir, f), encoding="utf-8").read()
    return out


def main():
    docs = pages()
    failures = []

    # 1 + 2: links
    for rel, doc in docs.items():
        for m in re.finditer(r'href="([^"]+)"', doc):
            href = m.group(1)
            if href.startswith(("http://localhost", "https://localhost")) or "127.0.0.1" in href or "0.0.0.0" in href:
                failures.append(f"{rel}: localhost link {href}")
            elif href.startswith("http"):
                if not ALLOWED_EXTERNAL.match(href):
                    # only flag fact-bearing external links; anchors to other hosts in prose are
                    # still required to be one of the registered publishers
                    failures.append(f"{rel}: external link outside the registered publishers: {href}")
            elif href.startswith("mailto:"):
                failures.append(f"{rel}: mailto link")
            else:
                target = os.path.normpath(os.path.join(os.path.dirname(os.path.join(HERE, rel)), href))
                if not os.path.exists(target):
                    failures.append(f"{rel}: broken internal link {href}")

    # 3: no price values
    for rel, doc in docs.items():
        if re.search(r"(?<![\d\w])[-\u2212]?110(?![\d\.])|(?<![\d\w])\+?\d{3}\s*odds", doc):
            failures.append(f"{rel}: possible price value on page (DEC-1=B: no prices may appear)")

    # 4: rows carry a source link or are marked derived
    for rel, doc in docs.items():
        for tr in re.findall(r"<tr[^>]*>.*?</tr>", doc, flags=re.S):
            if "<th>" in tr or "<th " in tr:
                continue  # header rows are meta
            has_link = "<a " in tr
            derived = 'class="derived"' in tr
            if not has_link and not derived:
                failures.append(f"{rel}: table row without a source link and without derived marker: {tr[:120]!r}")

    # 5: coverage lines
    for rel, doc in docs.items():
        n_tables = len(re.findall(r"<table", doc))
        n_cover = len(re.findall(r'class="coverage"', doc))
        if rel != "index.html" and n_tables > n_cover:
            failures.append(f"{rel}: {n_tables} table(s) but only {n_cover} coverage line(s)")

    # 6: index numbers match artefacts
    ledger = load("data/captures/ledger.json")
    deltas = load("data/derived/series_deltas.json")
    conflicts = load("data/derived/conflicts.json")
    mcn = load("data/derived/mcnemar_eval.json")
    idx = docs["index.html"]
    checks = [
        (str(len(ledger["entries"])), "captures sealed"),
        (str(deltas["summary"]["n_reads"]), "dated reads"),
        (str(deltas["summary"]["n_delta_rows"]), "deltas"),
        (str(conflicts["n_conflicts"]), "conflicts"),
        (str(conflicts["reserve_join"]["n_ir_absent_from_report"]), "IR-absent"),
        (mcn["status"], "eval status"),
    ]
    for val, label in checks:
        if val not in idx:
            failures.append(f"index: expected generated value {val!r} ({label}) not found")

    # 7: determinism
    r = subprocess.run([sys.executable, os.path.join(HERE, "engine", "build_site.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        failures.append(f"rebuild failed: {r.stderr[:200]}")
    else:
        diff = subprocess.run(["git", "diff", "--stat", "--", "nfl-collector/index.html",
                               "nfl-collector/pages"], capture_output=True, text=True,
                              cwd=os.path.dirname(HERE))
        if diff.stdout.strip():
            failures.append("determinism: rebuild changed committed pages:\n" + diff.stdout[:400])

    if failures:
        print(f"verify_site: FAIL — {len(failures)} problem(s):")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"verify_site: PASS — {len(docs)} pages, links resolve, rows sourced or marked derived, "
          f"coverage lines present, no price values, index matches artefacts, rebuild deterministic")


if __name__ == "__main__":
    main()

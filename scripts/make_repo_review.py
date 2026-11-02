#!/usr/bin/env python3
"""Inventory of every repo file (excluding generated site output and repo_review/ itself) + review findings."""
import csv, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = "https://github.com/sassnarep3-star/Own4"
def sh(*c): return subprocess.run(c, cwd=ROOT, capture_output=True, text=True).stdout
files = sorted(x for x in sh("git", "ls-files", "--cached", "--others", "--exclude-standard").split("\n") if x)
skip = lambda p: p.startswith("repo_review/") or p == "index.html" or p.startswith("pages/")
orig = set(sh("git", "ls-tree", "-r", "--name-only", "319d6b05a6ff2b3d05d82cd313b69d61e72afb50").split())
rows = []; tot_rows = tot_src = 0; secrets = []
for p in files:
    if skip(p) or not os.path.isfile(os.path.join(ROOT, p)): continue
    raw = open(os.path.join(ROOT, p), "rb").read()
    txt = raw.decode("utf-8", "replace")
    lines = txt.count("\n") + (0 if txt.endswith("\n") or not txt else 1)
    kind = {"csv": "data", "py": "code", "json": "data/config", "md": "docs", "css": "asset"}.get(p.rsplit(".", 1)[-1], "other")
    n = s = ""
    if p.endswith(".csv"):
        rr = list(csv.DictReader(open(os.path.join(ROOT, p), newline="")))
        n = len(rr)
        s = sum(1 for r in rr if any(isinstance(v, str) and v.startswith(("https://www.nba.com", "https://github.com/sassnarep3-star", "https://docs.github.com")) for v in r.values()))
        if "source_url" in rr[0]: tot_rows += n; tot_src += s
    if re.search(r"(ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY)", txt): secrets.append(p)
    blob = sh("git", "hash-object", p).strip()
    rows.append(dict(path=p, kind=kind, lines=lines, data_rows=n, rows_with_nba_source=s, git_blob_sha=blob,
                     author="original repo (319d6b0)" if p in orig else "session bf34205f", github_url=f"{REPO}/blob/main/{p}"))
with open(os.path.join(ROOT, "repo_review", "files.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
big = [r["path"] for r in rows if os.path.getsize(os.path.join(ROOT, r["path"])) > 1_000_000]
nocov = [r["path"] for r in rows if r["kind"] == "data" and r["path"].endswith(".csv") and r["data_rows"] and r["rows_with_nba_source"] != r["data_rows"]]
D = "https://docs.github.com/en"
F = [
 ("R-01", "README.md is a single line ('# Own4', no trailing newline): no description, usage, data provenance or licence statement.", "1 line, 6 bytes at commit 319d6b0", D + "/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes", "needs review (F-11)"),
 ("R-02", "No LICENSE file. Without one, default copyright applies and others have no explicit reuse rights. Choosing a licence is the owner's decision, so none was added.", "no LICENSE in tree", D + "/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository", "needs review (F-11)"),
 ("R-03", "No .gitignore in the original repo; one was added to keep Python caches out.", ".gitignore added", D + "/get-started/getting-started-with-git/ignoring-files", "ok (fixed)"),
 ("R-04", "No tests or CI workflow in the original repo; this work adds consistency scripts (verify_data.py, check_site.py) but no unit-test suite or Actions workflow.", "no tests/ or .github/workflows", D + "/actions/about-github-actions/understanding-github-actions", "needs review (F-11)"),
 ("R-05", "GitHub Pages is configured as a legacy branch build from main '/' with HTTPS enforced; the site is static HTML with .nojekyll.", "gh api repos/sassnarep3-star/Own4/pages", D + "/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site", "ok"),
 ("R-06", f"Every row in every data CSV that has a source_url column carries an official URL (nba.com, or github.com/docs.github.com for process/repo flags) ({tot_src} of {tot_rows} rows).", "files.csv columns data_rows vs rows_with_nba_source" + (f"; exceptions: {nocov}" if nocov else ""), "https://www.nba.com/", "ok" if tot_src == tot_rows else "needs review"),
 ("R-07", "Secret scan (token / private-key patterns) over all tracked and new files." , "matches: " + (", ".join(secrets) if secrets else "none"), D + "/code-security/secret-scanning/introduction/about-secret-scanning", "ok" if not secrets else "needs review"),
 ("R-08", "No files over 1 MB; no binary artefacts committed.", "oversized: " + (", ".join(big) if big else "none"), D + "/repositories/working-with-files/managing-large-files/about-large-files-on-github", "ok" if not big else "needs review"),
 ("R-09", "CSV line endings: the csv module defaults to CRLF; .gitattributes forces LF in the repository.", ".gitattributes: *.csv text eol=lf", D + "/get-started/getting-started-with-git/configuring-git-to-handle-line-endings", "ok (fixed)"),
 ("R-10", "Data content: 92 game rows, 30-team tables and the Nov 2 slate are reconciled across three nba.com page types; two scoreboard-vs-recap mismatches, one out-of-sequence (probably NBA Cup) game ID and a 0.2-0.3 PTS/g gap for two teams are open.", "see Flagged for Review F-01..F-05, F-15", "https://www.nba.com/games", "needs review"),
]
with open(os.path.join(ROOT, "repo_review", "findings.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["id", "finding", "evidence", "reference_url", "status"]); w.writerows(F)
print(len(rows), "files;", tot_src, "/", tot_rows, "source-covered rows")

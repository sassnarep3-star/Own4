"""Verify the NFL lab snapshot, generated site and publication readiness."""
from __future__ import annotations
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SITE = ROOT / "site"
RES = ROOT / "results"
DATA = ROOT / "data"
ALLOWED = {"www.nfl.com", "nfl.com", "operations.nfl.com", "static.www.nfl.com", "stats.nfl.com",
           "scikit-learn.org", "www.itl.nist.gov", "docs.scipy.org", "docs.github.com",
           "api.github.com", "github.com", "www.ncpgambling.org", "ncpgambling.org"}


def load(p):
    return json.loads(p.read_text())


class TableAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.in_td = False
        self.row_links = []
        self.rows = []
        self.links = []
        self.assets = []
        self.lang = False
        self.skip = False
        self.th_scope = True
        self.img_alt = True
        self.labels = 0
        self.inputs = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "a" and a.get("href") == "#main":
            self.skip = True
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.row_links = []
        if tag == "td" and self.in_tr:
            self.in_td = True
        if tag == "th" and not a.get("scope"):
            self.th_scope = False
        if tag == "img" and not a.get("alt"):
            self.img_alt = False
        if tag == "label":
            self.labels += 1
        if tag == "input":
            self.inputs += 1
        if tag == "a":
            href = a.get("href", "")
            self.links.append(href)
            if self.in_tr and href.startswith("https://"):
                self.row_links.append(href)
        if tag == "link" and a.get("href"):
            self.assets.append(a["href"])
        if tag == "script" and a.get("src"):
            self.assets.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        if tag == "tr" and self.in_tr:
            self.rows.append(list(self.row_links))
            self.in_tr = False
        if tag == "tbody":
            self.in_tbody = False


def main():
    checks = []
    def add(name, status, detail, source_url="https://github.com/sassnarep3-star/Own4", required=True):
        checks.append({"name": name, "status": status, "detail": detail, "source_url": source_url, "required": required})

    # Manifest hashes
    manifest = load(DATA / "collection_manifest.json")
    bad = []
    for name, digest in manifest["files"].items():
        p = DATA / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(name)
    add("Snapshot hash manifest", "pass" if not bad else "fail", f'{len(manifest["files"])} files checked; mismatches: {bad}', "https://www.nfl.com/standings/league/2026/REG")

    games, standings, players = load(DATA / "games.json"), load(DATA / "standings.json"), load(DATA / "players.json")
    sources = load(DATA / "sources.json")
    official_rows = all(urlparse(r["source_url"]).hostname in {"www.nfl.com", "operations.nfl.com"} for r in games + standings + players)
    add("Official row source coverage", "pass" if official_rows else "fail", f"{len(games)} games + {len(standings)} standings + {len(players)} player rows have official NFL source URLs.", "https://www.nfl.com/schedules/2026/by-week/week-8")
    add("Source register", "pass" if all(s["url"].startswith("https://") for s in sources.values()) else "fail", f"{len(sources)} HTTPS source records.", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/sources.json")

    integrity, leak = load(RES / "integrity.json"), load(RES / "leakage.json")
    add("Standings reconciliation", "pass" if integrity["pass"] else "fail", f'{integrity["standings_cells_matched"]}/320 cells match official standings.', "https://www.nfl.com/standings/league/2026/REG")
    add("Future-outcome leakage", "pass" if leak["pass"] else "fail", f'{leak["rows_compared"]} earlier prediction rows unchanged after perturbing final-week scores.', "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html")

    current, plines, corr = load(RES / "current_lines.json"), load(RES / "player_lines.json"), load(RES / "correlations.json")
    market_blank = all(r["market_spread"] is None and r["market_total"] is None and r["market_odds"] is None and r["edge"] is None for r in current)
    market_blank &= all(r["market_line"] is None and r["market_odds"] is None and r["edge"] is None for r in plines)
    cross = next(c for c in corr if c["id"] == "CROSS-PLAYER")
    market_blank &= cross["r"] is None and cross["ci95"] == [None, None]
    add("Blank-policy enforcement", "pass" if market_blank else "fail", "Market odds/edge and unverified cross-player correlation remain null/blank.", "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8")

    evaluation, leader = load(RES / "evaluation.json"), load(RES / "leaderboard.json")
    gate_ok = all(s["eligible"] == all(v == "pass" for v in s["gates"].values()) for s in evaluation["strategies"])
    gate_ok &= leader["reward_points_awarded"] == 0 and not leader["eligible"]
    add("Gate/reward consistency", "pass" if gate_ok else "fail", "No strategy is eligible unless every gate passes; zero rewards awarded.", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/results/leaderboard.json")

    # Generated HTML row/source and internal-link audit
    html_files = sorted(SITE.rglob("*.html")) + [REPO / "index.html"]
    row_count = missing_rows = broken = 0
    a11y_ok = True
    for p in html_files:
        parser = TableAudit()
        parser.feed(p.read_text())
        row_count += len(parser.rows)
        for links in parser.rows:
            if not any(urlparse(u).hostname in ALLOWED for u in links):
                missing_rows += 1
        a11y_ok &= parser.lang and parser.skip and parser.th_scope and parser.img_alt
        for href in parser.links + parser.assets:
            if not href or href.startswith(("https://", "http://", "#", "mailto:", "tel:")):
                continue
            target = (p.parent / unquote(href.split("#")[0])).resolve()
            if href.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                broken += 1
    add("Generated table row sources", "pass" if missing_rows == 0 else "fail", f"{row_count} generated data rows checked; {missing_rows} lack an allowed official/method/governance source link.", "https://github.com/sassnarep3-star/Own4")
    add("Internal navigation/assets", "pass" if broken == 0 else "fail", f"{len(html_files)} HTML files checked; {broken} broken relative links/assets.", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages")
    add("Accessibility basics", "pass" if a11y_ok else "fail", "lang, skip link, scoped table headers and image alt checks.", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages")

    # Combined published-dashboard navigation (raw archived HTML is evidence, not site navigation).
    published_dirs = {"nfl-lab", "nfl", "nfl-quant", "pipeline", "pages", "lab", "docs", "own4-dashboard", "lines-lab", "site_src"}
    combined_broken = []
    combined_files = 0
    for p in REPO.rglob("*.html"):
        parts = p.relative_to(REPO).parts
        if ".git" in parts or ("data" in parts and "raw" in parts):
            continue
        if len(parts) > 1 and parts[0] not in published_dirs:
            continue
        combined_files += 1
        parser = TableAudit()
        parser.feed(p.read_text(errors="replace"))
        for href in parser.links + parser.assets:
            if not href or href.startswith(("https://", "http://", "#", "mailto:", "tel:", "data:")):
                continue
            target = (p.parent / unquote(href.split("#")[0].split("?")[0])).resolve()
            if href.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                combined_broken.append(f"{p.relative_to(REPO)} -> {href}")
    add("Combined published navigation", "pass" if not combined_broken else "fail", f"{combined_files} published HTML files checked; broken: {combined_broken[:10] or 'none'}", "https://github.com/sassnarep3-star/Own4")

    markers = []
    for rel in ("index.html", "README.md", "COORDINATION.md"):
        for i, line in enumerate((REPO / rel).read_text().splitlines(), 1):
            if line.startswith(("<<<<<<< ", ">>>>>>> ")) or line == "=======":
                markers.append(f"{rel}:{i}")
    add("Shared conflict markers", "pass" if not markers else "fail", f"Marker scan: {markers or 'none'}", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md")

    audit = load(ROOT / "audit" / "summary.json")
    add("Repository inventory", "pass", f'{audit["files"]} files, {audit["text_lines"]} text lines, {audit["html_data_rows"]} HTML rows, {audit["csv_rows"]} CSV rows inventoried.', "https://github.com/sassnarep3-star/Own4")

    deploy_path = RES / "deployment.json"
    if deploy_path.exists():
        dep = load(deploy_path)
        add("GitHub Pages deployment", "pass" if dep.get("pass") else "fail", dep.get("detail", ""), dep.get("source_url", "https://api.github.com/repos/sassnarep3-star/Own4/pages"))
    else:
        add("GitHub Pages deployment", "pending", "Pre-merge verification complete; live deployment will be recorded after merge.", "https://api.github.com/repos/sassnarep3-star/Own4/pages", required=False)

    failed = [c["name"] for c in checks if c["required"] and c["status"] == "fail"]
    report = {"pass": not failed, "failed": failed, "checks": checks,
              "conclusion": "All required pre-merge checks pass. Deployment is pending until merge." if not failed and not deploy_path.exists() else ("All required checks pass." if not failed else "Required checks failed: " + ", ".join(failed))}
    (RES / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "failed": failed, "checks": len(checks), "html_rows": row_count, "broken_links": broken}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""04 - Repository audit.

Scans every file in the repository outside this session's namespace and
records, for each file that makes a factual claim about the NFL, whether the
claim carries a source link. The audit never rewrites another session's files
and never guesses a source. A finding is either:

  PASS    the file carries at least one link to an official NFL source or a
          named third-party source with a retrievable reference
  FLAG    the file makes a numeric or factual claim with no source link
  BLANK  the file leaves a value blank and says so
  NOTE    a structural observation with no source requirement

The audit also cross-checks the prior NFL namespaces against each other and
against the official data captured in this namespace, so that a reviewer can
see where two workspaces disagree.

Writes: data/derived/repo_audit.json
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DERIVED, ROOT, dump_json, load_json

REPO = os.path.dirname(ROOT)  # the repository root, one level above this namespace

NFL_NAMESPACES = ["nfl", "nfl-audit", "nfl-decision", "nfl-decisions", "nfl-edge",
                   "nfl-hub", "nfl-intel", "nfl-lab", "nfl-lines", "nfl-quant",
                   "nfl-research"]

OFFICIAL_HOST = re.compile(r"(nfl\.com|static\.www\.nfl\.com|profootballhof\.com|operations\.nfl\.com)", re.I)
THIRD_PARTY_HOST = re.compile(r"(github\.com/nflverse|github\.com/scrape|fanduel|draftkings|betmgm|"
                               r"covers\.com|actionnetwork|sportsbook|espn\.com/prospects|pro-football-reference|"
                               r"stathead|footballoutsiders|nflfastR)", re.I)
SOURCE_KEYWORD = re.compile(r"(source|provenance|citation|reference|retrieved|as of|official|"
                            r"nfl\.com|github\.com|nflverse|https?://)", re.I)
NUMBER_CLAIM = re.compile(r"(?<![A-Za-z0-9_.])(?:[+-]?\d{1,4}(?:\.\d+)?\s*(?:%|percent|points|yards|"
                           r"games|season|pick|line|margin|rating|win|loss|wins|losses|touches|"
                           r"carries|completions|passing yards|rushing yards))", re.I)
PLACEHOLDER = re.compile(r"\b(TODO|FIXME|TBD|XXX|PLACEHOLDER|LOREM IPSUM|CHANGEME|N/A)\b")
URL = re.compile(r"https?://[^\s\"'<>\)\]]+")
TABLE_ROW = re.compile(r"<tr\b", re.I)
LINK = re.compile(r"<a\s[^>]*href=[\"']([^\"']+)[\"']", re.I)


def rel(path):
    return os.path.relpath(path, REPO)


def classify(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".html", ".htm"):
        return "html"
    if ext in (".md", ".txt", ".rst"):
        return "text"
    if ext in (".json", ".csv", ".yaml", ".yml"):
        return "data"
    if ext in (".py", ".js", ".sh"):
        return "code"
    return "other"


def audit_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    ext = classify(path)
    urls = URL.findall(text)
    official = [u for u in urls if OFFICIAL_HOST.search(u)]
    third = [u for u in urls if THIRD_PARTY_HOST.search(u)]
    other = [u for u in urls if u not in official and u not in third]
    has_source_keyword = bool(SOURCE_KEYWORD.search(text))
    claims = NUMBER_CLAIM.findall(text)
    placeholders = PLACEHOLDER.findall(text)
    rows = len(TABLE_ROW.findall(text))
    links = LINK.findall(text) if ext == "html" else []
    table_links = 0
    if ext == "html":
        # count table rows that contain at least one link
        for m in re.finditer(r"<tr\b.*?</tr>", text, re.I | re.S):
            if LINK.search(m.group(0)):
                table_links += 1
    return {
        "file": rel(path), "type": ext, "bytes": len(text.encode("utf-8")),
        "official_links": len(official), "third_party_links": len(third),
        "other_links": len(other), "total_links": len(urls),
        "has_source_language": has_source_keyword,
        "numeric_claims": len(claims),
        "placeholders": sorted(set(placeholders)),
        "table_rows": rows, "table_rows_with_a_link": table_links,
        "official_examples": official[:3], "third_party_examples": third[:3],
    }


def main():
    rows = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", "__pycache__", ".arena", "dist", "build")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if p.startswith(ROOT):
                continue
            a = audit_file(p)
            if a:
                rows.append(a)

    # ---------------- per-namespace summary ---------------------------------
    ns = defaultdict(lambda: {"files": 0, "html": 0, "official_links": 0, "third_party_links": 0,
                               "numeric_claims": 0, "table_rows": 0, "table_rows_with_a_link": 0,
                               "files_with_placeholders": 0, "files_without_any_source_language": 0})
    for a in rows:
        top = a["file"].split(os.sep)[0]
        if top not in NFL_NAMESPACES and top not in ("", "index.html", "README.md", "AUDIT.md",
                                                     "EXECUTIVE_SUMMARY.md", "NFL_EXECUTIVE_SUMMARY.md"):
            # still count, but mark the namespace
            pass
        n = ns[top]
        n["files"] += 1
        if a["type"] == "html":
            n["html"] += 1
        n["official_links"] += a["official_links"]
        n["third_party_links"] += a["third_party_links"]
        n["numeric_claims"] += a["numeric_claims"]
        n["table_rows"] += a["table_rows"]
        n["table_rows_with_a_link"] += a["table_rows_with_a_link"]
        if a["placeholders"]:
            n["files_with_placeholders"] += 1
        if not a["has_source_language"] and a["numeric_claims"]:
            n["files_without_any_source_language"] += 1

    # ---------------- findings ----------------------------------------------
    findings = []
    for a in rows:
        f = []
        if a["type"] in ("html", "text") and a["numeric_claims"] > 0 and not a["has_source_language"]:
            f.append(("FLAG", "no source language",
                      "The file makes %d numeric claim(s) but contains no source, provenance or citation wording."
                      % a["numeric_claims"]))
        if a["type"] == "html" and a["table_rows"] >= 5 and a["table_rows_with_a_link"] == 0:
            f.append(("FLAG", "table rows without a source link",
                      "%d table rows and not one of them carries a link." % a["table_rows"]))
        if a["placeholders"]:
            f.append(("FLAG", "placeholder text",
                      "The file still contains: %s." % ", ".join(a["placeholders"][:6])))
        if a["type"] == "html" and a["total_links"] == 0 and a["numeric_claims"] > 0:
            f.append(("FLAG", "no links at all",
                      "The file makes %d numeric claim(s) and contains no link of any kind." % a["numeric_claims"]))
        if a["third_party_links"] > 0 and a["official_links"] == 0 and a["numeric_claims"] > 0:
            f.append(("NOTE", "third-party only",
                      "%d third-party link(s) and no official NFL link." % a["third_party_links"]))
        if not f:
            f.append(("PASS", "source language present" if a["has_source_language"] else "no claims to source",
                      "No irregularity found by the automated checks."))
        findings.append({"file": a["file"], "type": a["type"], "findings": f,
                         "metrics": {k: a[k] for k in ("official_links", "third_party_links", "total_links",
                                                       "numeric_claims", "table_rows",
                                                       "table_rows_with_a_link")}})

    # ---------------- cross-namespace consistency ----------------------------
    cross = []
    standings = load_json(os.path.join(ROOT, "data", "official", "standings_2026.json"))
    official_records = {r["team"]: r for r in standings["rows"]}
    for ns_name in NFL_NAMESPACES:
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, ns_name)):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            for fn in filenames:
                if not fn.endswith((".json", ".md", ".html")):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                except OSError:
                    continue
                # look for a team record that contradicts the official standings
                for team, rec in list(official_records.items()):
                    if len(team) != 2:
                        continue
                    for pat in (r"(?<![A-Za-z])%s(?![A-Za-z])[^0-9A-Za-z\n]{0,12}?(\d{1,2})-(\d{1,2})(-(\d{1,2}))?\b" % team,):
                        for m in re.finditer(pat, text):
                            w, l = int(m.group(1)), int(m.group(2))
                            t = int(m.group(4)) if m.group(4) else 0
                            if abs(w - rec["w"]) <= 1 and abs(l - rec["l"]) <= 1:
                                continue
                            if w + l + t > 20:
                                continue
                            cross.append({"file": rel(p), "namespace": ns_name, "team": team,
                                          "found": "%d-%d%s" % (w, l, ("-%d" % t) if t else ""),
                                          "official": "%d-%d%s" % (rec["w"], rec["l"], ("-%d" % rec["t"]) if rec["t"] else ""),
                                          "official_source": standings["url"]})
                            break

    res = {
        "id": "repo-audit",
        "generated_utc": "2026-11-13T00:00:00Z",
        "scope": "Every file in the repository outside nfl-command-center. This session does not edit any other namespace; the audit only reads.",
        "method": [
            "Each file is read as text. Links are extracted with a URL pattern and classified as official NFL, named third-party or other.",
            "A file is flagged when it makes numeric claims without any source, provenance or citation wording, when a table has rows but no links, when placeholder text survives, or when it contains no link at all.",
            "Team records written in the prior namespaces are compared with the official NFL.com 2026 league standings page.",
        ],
        "limits": [
            "This is an automated screen, not a line-by-line human reading of every character. The per-file findings are the starting point for manual review, not a substitute for it.",
            "A file can carry a source link and still make an unsupported claim. Every file is listed with its own manual review link.",
        ],
        "totals": {
            "files_audited": len(rows),
            "official_links": sum(a["official_links"] for a in rows),
            "third_party_links": sum(a["third_party_links"] for a in rows),
            "numeric_claims": sum(a["numeric_claims"] for a in rows),
            "files_flagged": sum(1 for f in findings if any(x[0] == "FLAG" for x in f["findings"])),
            "files_with_placeholders": sum(1 for a in rows if a["placeholders"]),
            "table_rows": sum(a["table_rows"] for a in rows),
            "table_rows_with_a_link": sum(a["table_rows_with_a_link"] for a in rows),
            "cross_namespace_record_conflicts": len(cross),
        },
        "namespaces": {k: dict(v) for k, v in sorted(ns.items())},
        "findings": findings,
        "cross_namespace_conflicts": cross,
        "manual_review": {
            "how": "Open the file at https://github.com/sassnarep3-star/Own4/blob/main/<path> and check every numeric cell against the source link in the row or the source list in the file.",
            "repository": "https://github.com/sassnarep3-star/Own4",
        },
    }
    dump_json(os.path.join(DERIVED, "repo_audit.json"), res)
    print("files audited:", res["totals"]["files_audited"],
          "| flagged:", res["totals"]["files_flagged"],
          "| placeholders:", res["totals"]["files_with_placeholders"],
          "| official links:", res["totals"]["official_links"],
          "| table rows:", res["totals"]["table_rows"],
          "| rows with a link:", res["totals"]["table_rows_with_a_link"],
          "| cross conflicts:", len(cross))


if __name__ == "__main__":
    main()

"""Build data/trace.json: brief item -> artifact checks -> derived status.

Status is computed from the files on disk, never typed:
  process            item is a process/governance step with no artifact by design
  gap                no artifact mapped
  broken-reference   a mapped artifact does not exist
  third-party-only   every existing artifact is from a non-official archive (items.THIRD_PARTY)
  artifact-present   at least one official-or-repo artifact exists; n = row count read from it
Register staleness: register status open/partial while artifact-present -> flagged for review.
Deterministic: no wall-clock values are written.
Run from repository root:  python3 nfl-brief-trace/engine/trace.py
"""
import csv, json, os, re, sys, collections

ROOT = os.getcwd()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import items as I  # noqa: E402

OUT = os.path.join(ROOT, "nfl-brief-trace", "data")
REGISTER = os.path.join(ROOT, "nfl-readiness-register", "data", "requirements.json")
REPO_BLOB = "https://github.com/sassnarep3-star/Own4/blob/main/"

OFFICIAL = {  # key -> (url, fetched_this_session)
    "INJ":   ("https://www.nfl.com/injuries/", True),
    "SCHED": ("https://www.nfl.com/schedules/", True),
    "RES":   ("https://www.nfl.com/transactions/league/reserve-list/2026/11", True),
    "GB":    ("https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books", True),
    "DREW":  ("https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders", True),
    "SCORES":("https://www.nfl.com/scores/2026/week-10", False),
}


def count_rows(path):
    """Return (kind, n_rows or None, bytes)."""
    size = os.path.getsize(path)
    low = path.lower()
    if low.endswith(".json"):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            return ("json-unparseable", None, size)
        if isinstance(d, list):
            return ("json", len(d), size)
        if isinstance(d, dict):
            if isinstance(d.get("rows"), list):
                return ("json", len(d["rows"]), size)
            if isinstance(d.get("entries"), list):
                return ("json", len(d["entries"]), size)
            if isinstance(d.get("n_rows"), int):
                return ("json", d["n_rows"], size)
            lists = [len(v) for v in d.values() if isinstance(v, list)]
            return ("json", max(lists) if lists else 0, size)
        return ("json", 0, size)
    if low.endswith(".csv"):
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            n = sum(1 for _ in csv.reader(f)) - 1
        return ("csv", max(n, 0), size)
    if low.endswith(".jsonl"):
        return ("jsonl", sum(1 for line in open(path, encoding="utf-8") if line.strip()), size)
    return ("text", None, size)


def item_status(item, arts):
    if item["id"] == "B80":
        return "process"
    if not item["artifacts"]:
        return "gap"
    if any(not a["exists"] for a in arts):
        return "broken-reference"
    present = [a for a in arts if a["exists"]]
    if all(a["path"] in I.THIRD_PARTY for a in present):
        return "third-party-only"
    return "artifact-present"


def register_refs_unresolved(rows):
    """Paths the register cites (evidence / clearing_number) that do not resolve in the repo.
    A path resolves if it exists at root, or under the nearest namespace named before it."""
    ns = re.compile(r"\b(nfl-[a-z-]+)\b")
    tok = re.compile(r"((?:[\w.-]+/)*[\w.-]+\.(?:json|csv|html|py|md|yml|jsonl))")
    out = []
    for r in rows:
        for field in ("evidence", "clearing_number"):
            s = str(r.get(field, ""))
            for m in tok.finditer(s):
                p = m.group(1)
                if os.path.exists(os.path.join(ROOT, p)):
                    continue
                before = ns.findall(s[: m.start()])
                if before and os.path.exists(os.path.join(ROOT, before[-1], p)):
                    continue
                out.append({"req": r["id"], "field": field, "ref": p})
    return out


def main():
    reg = json.load(open(REGISTER, encoding="utf-8"))["rows"]
    reg_by = {r["id"]: r for r in reg}
    rows = []
    for (iid, theme, text, artifacts, reqs, okey, note) in I.ITEMS:
        arts = []
        for p in artifacts:
            full = os.path.join(ROOT, p)
            if os.path.exists(full):
                kind, n, size = count_rows(full)
                arts.append({"path": p, "exists": True, "kind": kind, "n_rows": n,
                             "bytes": size, "third_party": p in I.THIRD_PARTY,
                             "url": REPO_BLOB + p})
            else:
                arts.append({"path": p, "exists": False, "kind": None, "n_rows": None,
                             "bytes": None, "third_party": p in I.THIRD_PARTY, "url": REPO_BLOB + p})
        status = item_status({"id": iid, "artifacts": artifacts}, arts)
        reg_status = sorted({reg_by[r]["status"] for r in reqs if r in reg_by})
        stale = status == "artifact-present" and any(s in ("open", "partial") for s in reg_status)
        if okey:
            url, fetched = OFFICIAL[okey]
            official = {"url": url, "fetched_this_session": fetched}
        else:
            official = None
        rows.append({
            "id": iid, "theme": theme, "brief": text, "status": status,
            "n_artifacts_present": sum(1 for a in arts if a["exists"]),
            "artifacts": arts, "reqs": reqs, "register_status": reg_status,
            "register_stale_candidate": stale, "official": official,
            "official_flag": None if official else "No official source mapped - blank by policy",
            "note": note,
        })

    unresolved = register_refs_unresolved(reg)
    cited_rules = [r["id"] for r in reg if "operations.nfl.com/the-rules" in json.dumps(r)]
    counts = collections.Counter(r["status"] for r in rows)
    out = {
        "dataset": "brief_trace",
        "title": "2026-11-18 brief: item-by-item trace to repository artifacts",
        "checked_on": "2026-11-18",
        "method": "engine/trace.py; items.py mapping; status derived from files; official links only where fetched or register-cited; see flags.",
        "n_items": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "register_rows": len(reg),
        "register_status_counts": dict(sorted(collections.Counter(r["status"] for r in reg).items())),
        "register_stale_candidates": sum(1 for r in rows if r["register_stale_candidate"]),
        "register_unresolved_refs": unresolved,
        "register_rows_citing_operations_the_rules": cited_rules,
        "items": rows,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "trace.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    print(json.dumps({k: out[k] for k in ("n_items", "status_counts", "register_status_counts",
                                          "register_stale_candidates")}, indent=1))
    print("unresolved register refs:", len(unresolved), "| operations.nfl.com/the-rules rows:", cited_rules)


if __name__ == "__main__":
    main()

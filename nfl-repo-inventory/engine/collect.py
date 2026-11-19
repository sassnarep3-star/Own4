"""Collect facts about every nfl* namespace in the repo (stdlib only).

Writes data/inventory.json. Verifier results are read from data/verifier_runs.json,
which was produced by running each verifier on a clean `git archive` export
(so the verifiers could not write into the repository).
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "data", "inventory.json")
RUNS = os.path.join(HERE, "data", "verifier_runs.json")
GH = "https://github.com/sassnarep3-star/Own4"
PAGES = "https://sassnarep3-star.github.io/Own4"


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                          text=True, check=True).stdout


def find_verifier(ns):
    cands = []
    for root, dirs, files in os.walk(os.path.join(REPO, ns)):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", "snapshots")]
        for f in files:
            if "verify" in f.lower() and f.endswith((".py", ".js", ".sh")):
                cands.append(os.path.relpath(os.path.join(root, f), REPO))
    if not cands:
        return None
    return sorted(cands, key=lambda p: (p.count("/"), p))[0]


def main():
    with open(os.path.join(REPO, "index.html"), encoding="utf-8") as fh:
        root_html = fh.read()
    runs = {}
    if os.path.exists(RUNS):
        with open(RUNS, encoding="utf-8") as fh:
            for r in json.load(fh)["runs"]:
                runs[r["namespace"]] = r
    head = git("rev-parse", "--short", "HEAD").strip()
    namespaces = sorted(d for d in os.listdir(REPO)
                        if d.startswith("nfl") and d != "nfl-repo-inventory" and os.path.isdir(os.path.join(REPO, d)))
    rows = []
    for ns in namespaces:
        tracked = [p for p in git("ls-files", ns).splitlines() if p]
        has_index = os.path.exists(os.path.join(REPO, ns, "index.html"))
        entry = "index.html" if has_index else (
            "pages/index.html" if os.path.exists(os.path.join(REPO, ns, "pages", "index.html")) else None)
        has_html = any(p.endswith(".html") for p in tracked)
        verifier = find_verifier(ns)
        last = git("log", "-1", "--format=%h %cs", "--", ns).strip()
        run = runs.get(ns)
        rows.append({
            "namespace": ns,
            "tracked_files": len(tracked),
            "has_index_html": has_index,
            "has_any_html": has_html,
            "entry_page": f"{ns}/{entry}" if entry else None,
            "live_url": f"{PAGES}/{ns}/{entry}" if entry else None,
            "github_url": f"{GH}/tree/main/{ns}",
            "verifier_path": verifier,
            "verifier_exit": run["exit"] if run else None,
            "verifier_last_line": run["last_line"] if run else None,
            "linked_from_root_index": (ns + "/") in root_html,
            "last_commit": last,
        })
    data = {
        "generated_for_commit": head,
        "generated_on": "2026-11-19",
        "namespace_count": len(rows),
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {OUT}: {len(rows)} namespaces")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the one readiness register this workspace publishes.

Why this file exists: three registers in the repository answer the same 73 brief
questions, and they disagree on 62 row statuses (see data/census.json). Picking one
silently would be the same error again. This builder instead:

  * keeps the brief's own wording as the row key,
  * prints ALL THREE statuses side by side, with the file each one came from,
  * resolves every file path quoted in the register evidence, so a claim like
    "artifact exists" can be seen to be true or false from the tree,
  * carries forward the blocking gate and the number that would clear it,
  * and marks a row "unreconciled" whenever the registers disagree.

Nothing is typed here: text, statuses, gates and clearing numbers are read from the
peer registers; the file-existence check and the disagreement flag are computed.

Run: python3 nfl-desk/engine/register.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
OUT = os.path.join(NS, "data", "requirements.json")
CENSUS = os.path.join(NS, "data", "census.json")

READINESS = "nfl-readiness-register/data/requirements.json"
ROUND2 = "nfl-req-review/data/requirements_2026_11_18.json"
CONSOLIDATED = "nfl-consolidated/data/requirements.json"
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"

SYN = {"met": "implemented", "implemented": "implemented", "partial": "partial",
       "blocked": "blocked", "not_started": "open", "open": "open",
       "in_progress": "open", "process": "process", "rejected": "rejected",
       "resolved-at-source": "resolved-at-source"}

# The three registers are published with different id schemes; the brief text is the key.
def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", str(t or "").lower()).strip()


PATHISH = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+\.(?:json|csv|md|py|html|yml|yaml|jsonl))\b")


def resolve(token):
    """Return every repo path that the quoted filename could mean."""
    token = token.strip().rstrip(".,;)")
    hits = []
    if os.path.exists(os.path.join(ROOT, token)):
        hits.append(token)
    base = os.path.basename(token)
    if "/" not in token:
        for ns in sorted(os.listdir(ROOT)):
            cand = os.path.join(ns, token)
            if os.path.exists(os.path.join(ROOT, cand)):
                hits.append(cand)
    elif os.path.isdir(os.path.join(ROOT, token.split("/")[0])):
        pass
    else:
        for ns in sorted(os.listdir(ROOT)):
            cand = os.path.join(ns, token)
            if os.path.exists(os.path.join(ROOT, cand)):
                hits.append(cand)
    if not hits and base:
        for base_dir, dirs, files in os.walk(os.path.join(ROOT, "nfl-book")):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            if base in files:
                hits.append(os.path.relpath(os.path.join(base_dir, base), ROOT).replace(os.sep, "/"))
    return sorted(set(hits))


def main():
    R = json.load(open(os.path.join(ROOT, READINESS), encoding="utf-8"))
    rows = R["rows"]
    B = {norm(r.get("requirement")): r for r in
         json.load(open(os.path.join(ROOT, ROUND2), encoding="utf-8"))["rows"]}
    C = {norm(r.get("requirement")): r for r in
         json.load(open(os.path.join(ROOT, CONSOLIDATED), encoding="utf-8"))["rows"]}

    census = json.load(open(CENSUS, encoding="utf-8"))
    disagree = {}
    for d in census["register_disagreements"]:
        disagree.setdefault(d["text"], []).append(d)

    out_rows, counts = [], {"agree": 0, "disagree": 0, "unmatched": 0, "no_official_source": 0,
                            "rows_with_exact_evidence": 0, "rows_with_loose_evidence": 0,
                            "rows_with_unresolved_evidence": 0}
    for r in rows:
        key = norm(r.get("verbatim"))
        b = B.get(key)
        c = C.get(key)
        s_read = r.get("status")
        s_round2 = b.get("status") if b else None
        s_cons = c.get("status") if c else None
        harmonised = {SYN.get(s_read, s_read), SYN.get(s_round2, s_round2), SYN.get(s_cons, s_cons)}
        harmonised.discard(None)
        agree = len(harmonised) <= 1
        if b is None or c is None:
            counts["unmatched"] += 1
        elif agree:
            counts["agree"] += 1
        else:
            counts["disagree"] += 1

        # resolve the paths the register quotes as evidence
        tokens = sorted(set(PATHISH.findall(str(r.get("evidence", "")))))
        exact, loose, unresolved = [], [], []
        for t in tokens:
            hits = resolve(t)
            if not hits:
                unresolved.append(t)
            elif t in hits:
                exact.append(t)
            else:
                loose.append({"quoted": t, "found_at": hits[:3]})

        if exact:
            counts["rows_with_exact_evidence"] += 1
        if loose:
            counts["rows_with_loose_evidence"] += 1
        if unresolved:
            counts["rows_with_unresolved_evidence"] += 1

        official = r.get("official_source") or ""
        if not official:
            counts["no_official_source"] += 1

        out_rows.append({
            "id": r.get("id"),
            "requirement": r.get("verbatim"),
            "category": r.get("category"),
            "kind": r.get("kind"),
            "status_readiness_register": s_read,
            "status_round2_review": s_round2,
            "status_consolidated": s_cons,
            "statuses_agree": agree,
            "status_sources": [READINESS + "#" + str(r.get("id")),
                              (ROUND2 + "#" + str(b.get("id"))) if b else "",
                              (CONSOLIDATED + "#" + str(c.get("id"))) if c else ""],
            "gate": r.get("gate"),
            "clearing_number": r.get("clearing_number"),
            "official_source": official,
            "source_note": r.get("source_note", ""),
            "evidence_text": r.get("evidence", ""),
            "evidence_paths_exact": exact,
            "evidence_paths_resolved_elsewhere": loose,
            "evidence_paths_unresolved": unresolved,
            "round2_evidence": (b or {}).get("evidence", ""),
            "repo_files": [REPO + READINESS, REPO + ROUND2, REPO + CONSOLIDATED],
        })

    out = {
        "dataset": "nfl_desk_readiness_register",
        "title": "One readiness register for the 73-line brief, with every peer register's answer shown",
        "built_utc": "2026-11-19",
        "session": "arena/1e2776fd-own4",
        "method": ("Rows are the 73 requirement lines of the 2026-11-15 brief in the readiness "
                   "register's wording. The three status columns are read from three peer files and "
                   "never merged into one verdict; 'statuses_agree' is computed by normalising their "
                   "vocabularies (met=implemented, not_started=open, in_progress=open). Evidence paths "
                   "are resolved against the tree by engine/register.py."),
        "inputs": {"readiness": READINESS, "round2": ROUND2, "consolidated": CONSOLIDATED,
                   "census": "nfl-desk/data/census.json"},
        "counts": dict(counts, rows=len(rows)),
        "register_disagreement_pairs": census.get("register_disagreement_count"),
        "policy": ("A row is only 'clear to rely on' when the three registers agree AND its evidence "
                   "paths resolve AND it names an official source. This file does not upgrade any "
                   "status; the owner decides which register is authoritative."),
        "rows": out_rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(counts, indent=1))
    print("-> %s" % OUT)


if __name__ == "__main__":
    main()

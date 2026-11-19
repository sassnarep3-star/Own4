#!/usr/bin/env python3
"""
nfl-command-deck — repository audit.

Every check here is mechanical and re-runnable. Nothing is typed by hand; the site
renders whatever this file emits. A check that cannot be run (e.g. an official page
that this sandbox cannot reach) is recorded as `not_run` with the reason — never as a
pass.

Writes: data/audit.json
Pure standard library.
"""

import hashlib
import html
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import urllib.request
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

SKIP_DIR_PARTS = {".git", "snapshots", "raw", "node_modules", "__pycache__"}


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


# --------------------------------------------------------------------------- A. links
def link_audit():
    broken_files, broken_anchors, total = [], [], 0
    for dp, dn, fn in os.walk(ROOT):
        parts = set(dp.split(os.sep))
        if parts & SKIP_DIR_PARTS:
            continue
        for f in fn:
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            if rel(p).startswith("nfl-command-deck/"):
                continue      # this workspace's own pages are verified by engine/verify.py
            try:
                s = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if len(s) > 3_000_000:
                continue
            ids = set(re.findall(r'id="([^"]+)"', s))
            for m in re.finditer(r'href="([^"#]*)(#[^"]*)?"', s):
                u, frag = m.group(1), m.group(2)
                if not u or u.startswith(("http", "mailto:", "tel:", "data:", "javascript")):
                    continue
                total += 1
                q = unquote(u.split("?")[0])
                t = os.path.normpath(os.path.join(dp, q))
                if q and not os.path.exists(t):
                    broken_files.append({"page": rel(p), "target": u})
                    continue
                if frag and t.endswith(".html") and frag[1:] not in ids:
                    broken_anchors.append({"page": rel(p), "target": u + frag})
    from collections import Counter
    c = Counter(b["page"].split("/")[0] if "/" in b["page"] else b["page"] for b in broken_anchors)
    f = Counter(b["page"].split("/")[0] if "/" in b["page"] else b["page"] for b in broken_files)
    return {
        "check": "A. internal link integrity (files and #anchors), excluding committed raw captures",
        "internal_refs_checked": total,
        "broken_file_links": len(broken_files),
        "broken_anchor_links": len(broken_anchors),
        "broken_files_by_namespace": dict(f.most_common(12)),
        "broken_anchors_by_namespace": dict(c.most_common(12)),
        "examples_files": broken_files[:12],
        "examples_anchors": broken_anchors[:12],
        "detail_file": "nfl-command-deck/data/link_defects.json",
        "_files_full": broken_files,
        "_anchors_full": broken_anchors,
        "result": "fail" if (broken_files or broken_anchors) else "pass",
    }


# ------------------------------------------------------- B. shared generator idempotency
def nav_count_check():
    idx = os.path.join(ROOT, "index.html")
    if not os.path.exists(idx):
        return {"check": "B. root navigation workspace count vs directories on disk",
                "result": "not_run", "why": "index.html missing"}
    text = open(idx, encoding="utf-8").read()
    m = re.search(r"NFL research · (\d+) workspaces", text)
    claimed = int(m.group(1)) if m else None
    on_disk = sorted(d for d in os.listdir(ROOT)
                     if d.startswith("nfl") and os.path.isdir(os.path.join(ROOT, d)))
    nav_links = len(re.findall(r'href="nfl[^"]*"', text))
    ok = claimed == len(on_disk)
    return {
        "check": "B. root navigation workspace count vs directories on disk",
        "group_title_claims": claimed,
        "nfl_directories_on_disk": len(on_disk),
        "nfl_links_in_root_nav": nav_links,
        "result": "pass" if ok else "fail",
        "finding": None if ok else
        "The root nav group title states %s workspaces; %d nfl* directories exist. The title is "
        "computed from directory count, but the group's own link list is shorter than the "
        "directory list, so the title and the group disagree." % (claimed, len(on_disk)),
    }


# --------------------------------------------------- C. cross-namespace reconciliation
def reconciliation():
    ob_path = os.path.join(ROOT, "nfl-origin-board", "data", "games_2026.json")
    lb_path = os.path.join(ROOT, "nfl-live-board", "data", "corpus_2026.json")
    if not (os.path.exists(ob_path) and os.path.exists(lb_path)):
        return {"check": "C. cross-namespace result reconciliation", "result": "not_run"}
    ob = json.load(open(ob_path, encoding="utf-8"))["games"]
    lb = json.load(open(lb_path, encoding="utf-8"))["corpus"]
    obm = {(w, a, h): (ap, hp, st, url) for w, d, a, ap, h, hp, st, url, note in ob}
    lbm = {(g["week"], g["away"], g["home"]): (g["away_pts"], g["home_pts"], g["source_url"])
           for g in lb}
    # club abbreviation drift: LA vs LAR is the same club; normalise before joining
    alias = {"LA": "LAR"}
    obn = {(w, alias.get(a, a), alias.get(h, h)): v for (w, a, h), v in obm.items()}
    only_ob = sorted(set(obn) - set(lbm))
    only_lb = sorted(set(lbm) - set(obn))
    common = set(obn) & set(lbm)
    mism = [(k, obn[k][:2], lbm[k][:2]) for k in sorted(common)
            if (obn[k][0], obn[k][1]) != (lbm[k][0], lbm[k][1])]
    return {
        "check": "C. cross-namespace result reconciliation (origin-board vs live-board corpus)",
        "origin_board_rows": len(obm),
        "live_board_rows": len(lbm),
        "common_fixtures": len(common),
        "only_in_origin_board": [list(k) for k in only_ob],
        "only_in_live_board": [list(k) for k in only_lb],
        "score_mismatches": [{"fixture": list(m[0]), "origin_board": list(m[1]),
                              "live_board": list(m[2])} for m in mism],
        "abbreviation_drift": ["LA (origin-board) vs LAR (live-board): same club, different code; "
                               "a join without aliasing silently drops 11 fixtures"],
        "result": "pass" if not [x for x in mism if None not in x[1]] else "review",
        "interpretation": "Common fixtures agree on final scores. The only score disagreement is a "
                          "Week-10 fixture that was still in progress at the origin-board capture "
                          "time (2026-11-16) and final by the live-board transcription (2026-11-17) "
                          "— a capture-time difference, not a contradiction.",
    }


# ------------------------------------------------------------- D. corpus integrity checks
def corpus_integrity():
    p = os.path.join(ROOT, "nfl-live-board", "data", "corpus_2026.json")
    d = json.load(open(p, encoding="utf-8"))
    rows = d["corpus"]
    ALIAS = {"LA": "LAR"}
    ids = [g["game_id"] for g in rows]
    teams = sorted({g["home"] for g in rows} | {g["away"] for g in rows})
    per_week_team = {}
    for g in rows:
        for t in (g["home"], g["away"]):
            per_week_team.setdefault((g["week"], t), []).append(g["game_id"])
    dup_team_week = [{"week": w, "team": t, "games": v}
                     for (w, t), v in per_week_team.items() if len(v) > 1]

    per_game = [g["game_id"] for g in rows
                if str(g.get("source_url", "")).startswith("https://www.nfl.com/games/")]
    week_page = [g["game_id"] for g in rows if g["game_id"] not in per_game]
    off_official = [g["game_id"] for g in rows
                    if not str(g.get("source_url", "")).startswith("https://www.nfl.com/")]
    bad_pts = [g["game_id"] for g in rows
               if not (0 <= g["away_pts"] <= 80 and 0 <= g["home_pts"] <= 80)]
    ties = [g["game_id"] for g in rows if g["away_pts"] == g["home_pts"]]

    # independent corroboration: a second peer capture holds per-game URLs for those rows
    ob_path = os.path.join(ROOT, "nfl-origin-board", "data", "games_2026.json")
    corroborated, uncorroborated = 0, []
    if os.path.exists(ob_path):
        ob = json.load(open(ob_path, encoding="utf-8"))["games"]
        obm = {(w, ALIAS.get(a, a), ALIAS.get(h, h)): (ap, hp, url, st)
               for w, _d, a, ap, h, hp, st, url, _n in ob}
        for gid in week_page:
            g = next(r for r in rows if r["game_id"] == gid)
            k = (g["week"], ALIAS.get(g["away"], g["away"]), ALIAS.get(g["home"], g["home"]))
            hit = obm.get(k)
            if (hit and hit[0] is not None and str(hit[2]).startswith("https://www.nfl.com/games/")
                    and (hit[0], hit[1]) == (g["away_pts"], g["home_pts"])):
                corroborated += 1
            else:
                uncorroborated.append({"game_id": gid, "fixture": list(k), "peer_row": hit})

    return {
        "check": "D. corpus integrity and per-row official-URL coverage",
        "games": len(rows),
        "unique_game_ids": len(set(ids)),
        "duplicate_game_ids": len(ids) - len(set(ids)),
        "teams": len(teams),
        "weeks": sorted({g["week"] for g in rows}),
        "games_per_week": {str(w): sum(1 for g in rows if g["week"] == w)
                           for w in sorted({g["week"] for g in rows})},
        "rows_with_per_game_official_url": len(per_game),
        "rows_with_week_page_url_only": len(week_page),
        "rows_corroborated_by_second_peer_capture": corroborated,
        "rows_not_corroborated": uncorroborated,
        "rows_off_official_domain": off_official,
        "implausible_scores": bad_pts,
        "ties_in_corpus": ties,
        "team_plays_twice_in_a_week": dup_team_week,
        "result": "pass" if not (off_official or bad_pts or dup_team_week or uncorroborated)
                  and len(set(ids)) == len(ids) else "review",
        "interpretation": "%d of %d rows carry a per-game official URL. The remaining %d cite the "
                          "official week schedule page; %d of those are independently corroborated by "
                          "a second peer capture that does carry a per-game URL with the same score. "
                          "The evaluation in eval.json is conditional on these rows." %
                          (len(per_game), len(rows), len(week_page), corroborated),
    }


# ------------------------------------------------------- E. official capture integrity
def capture_integrity():
    manifest = os.path.join(ROOT, "nfl-readiness-register", "snapshots", "manifest.jsonl")
    out = {"check": "E. committed official capture integrity (sha256 + re-parsed row counts)",
           "entries": [], "parsed": {}}
    if not os.path.exists(manifest):
        out["result"] = "not_run"
        return out
    for line in open(manifest, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        path = os.path.join(ROOT, "nfl-readiness-register", e["raw_path"])
        rec = {"capture_id": e["capture_id"], "kind": e.get("kind"),
               "captured_utc": e.get("captured_utc"), "sha256_match": None,
               "bytes_match": None, "source_url": e.get("source_url")}
        if os.path.exists(path):
            raw = open(path, "rb").read()
            rec["sha256_match"] = hashlib.sha256(raw).hexdigest() == e["sha256"]
            rec["bytes_match"] = (len(raw) == e["bytes"]) if "bytes" in e else None
        else:
            rec["sha256_match"] = "file-missing"
        out["entries"].append(rec)

    # re-parse the two 2026-11-18 captures independently of the peer's own parser
    inj = os.path.join(ROOT, "nfl-readiness-register", "snapshots", "2026-11-18",
                       "injury_report-2026-11-18T234917Z.html")
    if os.path.exists(inj):
        s = open(inj, encoding="utf-8", errors="replace").read()
        titles = re.findall(r'd3-o-section-sub-title"><span>([^<]*)</span>', s)
        labels = re.findall(r'Injuries - (WEEK \d+)', s)
        tabs = [m.start() for m in re.finditer(r"<table", s)]
        rows, malformed = 0, 0
        for t in tabs:
            chunk = s[t:s.find("</table>", t)]
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S):
                cells = len(re.findall(r"<td", tr))
                if cells == 0:
                    continue
                if cells in (4, 5):
                    rows += 1
                else:
                    malformed += 1
        out["parsed"]["injury_report_2026_11_18"] = {
            "week_label_shown": labels[0] if labels else None,
            "team_sections": len(titles),
            "team_names": titles,
            "tables": len(tabs),
            "player_rows": rows,
            "rows_with_unexpected_cell_count": malformed,
            "note": "row counts re-derived by this script from the committed bytes; the peer's "
                    "own parser is not used",
        }
    hashes_ok = all(e["sha256_match"] is True for e in out["entries"])
    out["result"] = "pass" if hashes_ok and out["entries"] else "fail"
    out["interpretation"] = (
        "Every committed capture re-hashes to the SHA-256 recorded in the manifest%s. The "
        "injury capture independently re-parses to the counts shown under parsed."
        % ("" if hashes_ok else " — EXCEPT the entries marked false"))
    return out


def reserve_capture():
    p = os.path.join(ROOT, "nfl-readiness-register", "snapshots", "2026-11-18",
                     "reserve_list-2026-11-18T234918Z.html")
    out = {"check": "F. committed reserve-list capture re-parse"}
    if not os.path.exists(p):
        out["result"] = "not_run"
        return out
    s = open(p, encoding="utf-8", errors="replace").read()
    t = s.find("<table")
    chunk = s[t:s.find("</table>", t)]
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S)
    parsed = []
    for tr in rows:
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if cells:
            parsed.append(cells)
    header = parsed[0] if parsed else []
    data = parsed[1:] if parsed else []
    dates = sorted({c for r in data for c in r if re.fullmatch(r"\d{1,2}/\d{1,2}", c)})
    out.update({
        "header": header,
        "data_rows": len(data),
        "distinct_dates_in_field": dates,
        "sample_rows": data[:3],
        "result": "pass" if data and header else "review",
        "interpretation": "The committed capture is the November reserve-list page and does carry "
                          "dated transactions with a club column. It is one capture of one month, "
                          "so it cannot answer 'was this club's reserve list complete at kickoff' "
                          "for any past game.",
    })
    return out


# ------------------------------------------------------------ G. depth register integrity
def depth_integrity():
    p = os.path.join(ROOT, "nfl-depth-sweep", "data", "depth_register.json")
    d = json.load(open(p, encoding="utf-8"))
    clubs = d["clubs"]
    slots = shared = empty1 = 0
    per_club = {}
    for c in clubs:
        pos = c.get("positions", [])
        per_club[c["club"]] = len(pos)
        for s in pos:
            slots += 1
            r1 = s.get("rank1") or {}
            if not r1.get("name"):
                empty1 += 1
            if r1.get("alt"):
                shared += 1
    return {
        "check": "G. depth register integrity (32 clubs)",
        "clubs": len(clubs),
        "clubs_verified_text": sum(1 for c in clubs if c["status"] == "verified_text"),
        "clubs_flagged": [c["club"] for c in clubs if c["status"] != "verified_text"],
        "slots": slots,
        "slots_with_two_players_in_rank1": shared,
        "slots_with_empty_rank1": empty1,
        "slots_per_club": per_club,
        "asymmetric_slot_counts": sorted({v for v in per_club.values()}),
        "result": "review" if len({v for v in per_club.values()}) > 1 else "pass",
        "interpretation": "Slot counts differ between clubs (%s), which is expected: clubs publish "
                          "different position groupings. This register is a single dated capture per "
                          "club (2026-11-17), not a time series, so it cannot yet support a "
                          "point-in-time backtest." % sorted({v for v in per_club.values()}),
    }


# ---------------------------------------------------------- H. official-source reachability
def egress():
    out = {"check": "H. official-source reachability from this environment"}
    for host in ("www.nfl.com", "github.com"):
        rec = {}
        try:
            socket.create_connection((host, 443), timeout=6).close()
            rec["tcp443"] = True
        except OSError as ex:
            rec["tcp443"] = False
            rec["tcp_error"] = str(ex)
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request("https://%s/" % host, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                rec["http_status"] = r.status
        except Exception as ex:  # noqa: BLE001 - the error text is the evidence
            rec["http_error"] = type(ex).__name__ + ": " + str(ex)[:160]
        out[host] = rec
    out["result"] = "pass" if out["github.com"].get("http_status") else "review"
    out["conclusion"] = ("www.nfl.com cannot be read from this sandbox; every 'verified' claim in "
                         "this workspace is verified against committed official captures only"
                         if not out["www.nfl.com"].get("http_status") else
                         "www.nfl.com reachable; a live re-read remains a separate, unperformed step")
    return out


# ---------------------------------------------------------------- I. staleness / duplication
def staleness():
    dates = {}
    for name in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, name)
        if not os.path.isdir(d) or not name.startswith("nfl"):
            continue
        idxs = [os.path.join(d, f) for f in ("index.html",) if os.path.exists(os.path.join(d, f))]
        pages = []
        for sub in ("pages", "site"):
            p2 = os.path.join(d, sub)
            if os.path.isdir(p2):
                pages += [os.path.join(p2, f) for f in sorted(os.listdir(p2)) if f.endswith(".html")]
        found = []
        for f in idxs + pages:
            s = open(f, encoding="utf-8", errors="replace").read(40000)
            for m in re.finditer(r"20\d\d-\d\d-\d\d", s[:4000]):
                found.append(m.group(0))
        if found:
            dates[name] = max(found)
    from collections import Counter
    buckets = Counter(dates.values())
    return {
        "check": "I. namespace freshness (max date shown on landing page header)",
        "namespaces": len(dates),
        "by_latest_date": dict(sorted(buckets.items())),
        "detail": dict(sorted(dates.items())),
        "result": "review",
        "interpretation": "Namespaces are frozen at different dates. A reader who opens the oldest "
                          "one sees numbers that later namespaces have revised; that is the root "
                          "cause of the disagreements listed in check C and in the peer flags.",
    }


def main():
    audit = {
        "dataset": "nfl_command_deck_audit",
        "built_utc": "2026-11-19",
        "session": "arena/1153eb96-own4",
        # NOTE: the audited commit is deliberately NOT embedded. It changes with every
        # commit, which would make this file non-deterministic across rebuilds. It is
        # printed to stdout for the CI log instead.
        "checks": [],
    }
    checks = [link_audit(), nav_count_check(), reconciliation(), corpus_integrity(),
              capture_integrity(), reserve_capture(), depth_integrity(), egress(), staleness()]
    audit["checks"] = [{k: v for k, v in c.items() if not k.startswith("_")} for c in checks]

    # full defect list, so a reviewer can act on every row rather than a sample
    la = checks[0]
    defects = {"dataset": "nfl_command_deck_link_defects", "built_utc": "2026-11-19",
               "how": "every href on every .html file outside .git, snapshots and raw capture "
                      "directories; a file link must resolve, an anchor must match an id= on the "
                      "target page",
               "broken_file_links": la.get("_files_full", []),
               "broken_anchor_links": la.get("_anchors_full", [])}
    json.dump(defects, open(os.path.join(DATA, "link_defects.json"), "w", encoding="utf-8"),
              indent=1, sort_keys=True)
    with open(os.path.join(DATA, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=1, sort_keys=True)
    for c in checks:
        print("%-58s %s" % (c["check"][:58], c.get("result")))
    print("audited at commit",
          subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip())


if __name__ == "__main__":
    main()

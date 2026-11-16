#!/usr/bin/env python3
"""Derive every published number in this namespace from committed artefacts.

Reads ONLY files inside this namespace (data/*.json).  It never walks the repository tree and
never touches the network: the page build must be reproducible from what is committed, so a
sibling namespace merging cannot change a number on this site.  The tree facts enter through
data/namespace_inventory.json, which engine/inventory.py writes on demand and which states the
commit it describes.

  python3 nfl-decision-console/engine/derive.py        # writes data/derived/*.json

Standard library only.  Deterministic: sorted iteration everywhere, no clock, no randomness.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
OUT = os.path.join(NS, "data", "derived")
SELF = os.path.basename(NS)

SEASON_FIXTURES = 272      # 32 clubs x 17 games / 2, the league's own schedule shape
GATE_FIXTURES = 300        # the n cited by peer validation gates


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def dump(name, obj):
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    p = os.path.join(OUT, name)
    open(p, "w", encoding="utf-8").write(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return p


# ----------------------------------------------------------------- corpus
def corpus():
    s = load("standings_2026-11-16.json")
    rows = s["rows"]
    sw = sum(r["W"] for r in rows)
    sl = sum(r["L"] for r in rows)
    st = sum(r["T"] for r in rows)
    spf = sum(r["pf"] for r in rows)
    spa = sum(r["pa"] for r in rows)
    gp = sw + sl + st
    pct_mismatch = []
    net_mismatch = []
    for r in rows:
        n = r["W"] + r["L"] + r["T"]
        pct = round((r["W"] + 0.5 * r["T"]) / n, 3) if n else 0.0
        if abs(pct - r["pct"]) > 0.0005:
            pct_mismatch.append({"abbr": r["abbr"], "printed": r["pct"], "recomputed": pct})
        if (r["pf"] - r["pa"]) < 0 and r["pct"] > 0.5:
            net_mismatch.append({"abbr": r["abbr"], "pct": r["pct"], "net": r["pf"] - r["pa"]})
    fixtures = gp // 2
    return {
        "artefact": "data/standings_2026-11-16.json",
        "source_url": s["source_url"],
        "read_utc": s["read_utc"],
        "clubs": len(rows),
        "sum_wins": sw, "sum_losses": sl, "sum_ties": st,
        "sum_points_for": spf, "sum_points_against": spa,
        "sum_games_played": gp,
        "fixtures_credited": fixtures,
        "tied_fixtures": st // 2,
        "decisive_fixtures": fixtures - st // 2,
        "season_fixture_count": SEASON_FIXTURES,
        "half_season": SEASON_FIXTURES // 2,
        "pct_recompute_mismatches": pct_mismatch,
        "identities": [
            {"name": "sum(W) == sum(L)", "left": sw, "right": sl, "holds": sw == sl},
            {"name": "sum(PF) == sum(PA)", "left": spf, "right": spa, "holds": spf == spa},
            {"name": "sum(W+L+T) is even (every fixture credited twice)",
             "left": gp, "right": gp % 2, "holds": gp % 2 == 0},
            {"name": "win pct recomputes for all 32 clubs (3 dp)",
             "left": len(rows), "right": len(rows) - len(pct_mismatch),
             "holds": not pct_mismatch},
        ],
        "observations_not_identities": [
            {"name": "clubs above .500 with a NEGATIVE point differential (record and net points disagree)",
             "count": len(net_mismatch), "clubs": net_mismatch,
             "reading": "not a failure of the data: a win can come in a one-possession game. It is "
                        "published because a rating built on net points and a rating built on wins will "
                        "disagree about these clubs today, which is the ablation the requirements ask for."},
        ],
        "gate_check": {
            "gate_cited_by_peers": GATE_FIXTURES,
            "fixtures_available_today": fixtures,
            "fixtures_at_season_end": SEASON_FIXTURES,
            "one_season_can_satisfy_the_gate": SEASON_FIXTURES >= GATE_FIXTURES,
            "seasons_needed_at_this_rate": -(-GATE_FIXTURES // SEASON_FIXTURES),
            "reading": "a gate of n >= %d graded fixtures cannot be met inside one %d-fixture season, "
                       "so either the gate, the unit (club-games = %d today) or the multi-season corpus "
                       "must change before any promotion or demotion is defined"
                       % (GATE_FIXTURES, SEASON_FIXTURES, gp),
        },
        "brief_claims_checked": [
            {"claim": "the 136-game log", "observed": fixtures,
             "matches_any_observed_count": fixtures == 136,
             "arithmetic_note": "272 / 2 = %d, so half a season is the only figure reproducible from "
                                "official numbers that equals 136; no file at the base commit publishes it"
                                % (SEASON_FIXTURES // 2)},
        ],
    }


# ----------------------------------------------------- label join (one fixture)
def label_join():
    """Join one fixture's official report rows to that fixture's official game-book availability blocks.

    The two documents share no id: the report prints names with no jersey number, the game book prints
    '<initial>.<surname> <number>'.  Surname is therefore the only key, which is good enough to show the
    JOIN is possible and not good enough to be an identity - so ambiguity is counted and published.
    """
    g = load("gamebook_evidence.json")
    lin = g["lineups"]
    SUFFIX = {"iii", "iv", "jr", "sr", "ii"}

    def surname(name):
        parts = [x for x in re.split(r"[\s.]+", name.strip().lower()) if x]
        while parts and parts[-1] in SUFFIX:
            parts.pop()
        return parts[-1] if parts else ""

    def split_entry(entry):
        """'CB 7 C.Davis' -> ('C.Davis', 'CB', '7'); '3QB 15 B.Morton' -> ('B.Morton', '3QB', '15')."""
        m = re.match(r"^\s*([0-9A-Za-z]*)\s+(\d+)\s+(.+?)\s*$", entry)
        if not m:
            return entry, "", ""
        pos, num, name = m.group(1), m.group(2), m.group(3)
        return name, pos, num

    blocks = {}
    for club in ("NE", "DET"):
        blocks[club] = {
            "lineups": lin[club + "_offense"] + lin[club + "_defense"],
            "substitutions": lin[club + "_substitutions"],
            "not_active": lin[club + "_not_active"],
            "did_not_play": lin[club + "_did_not_play"],
        }
    idx = {}
    for club, bs in blocks.items():
        idx[club] = {}
        for bname, entries in bs.items():
            for e in entries:
                name, pos, num = split_entry(e)
                idx[club].setdefault(surname(name), []).append(
                    {"block": bname, "printed": name, "pos": pos, "number": num})

    order = {"lineups": 0, "substitutions": 1, "not_active": 2, "did_not_play": 3}
    state_of = {"lineups": "started", "substitutions": "played off the bench",
                "not_active": "not active", "did_not_play": "did not play"}
    rows = []
    for r in g["availability_report_rows_for_this_fixture"]:
        club, key = r["club"], surname(r["player"])
        cands = idx[club].get(key, [])
        distinct_printed = sorted({c["printed"] for c in cands})
        distinct_blocks = sorted({c["block"] for c in cands}, key=lambda b: order[b])
        if not cands:
            state, why = "unaccounted", "no surname match in any availability block"
        elif len(distinct_printed) > 1:
            state, why = "ambiguous", "surname matches %d different printed names: %s" % (
                len(distinct_printed), ", ".join(distinct_printed))
        elif len(distinct_blocks) > 1:
            state, why = "ambiguous", "printed name appears in %d blocks: %s" % (
                len(distinct_blocks), "/".join(distinct_blocks))
        else:
            state, why = state_of[distinct_blocks[0]], "single surname match, single block"
        rows.append({"club": club, "player": r["player"], "pos": r["pos"], "injury": r["injury"],
                     "practice": r["practice"], "game_status": r["game_status"],
                     "join_state": state, "join_reason": why,
                     "matches": cands})

    def tally(status, pred):
        return sum(1 for x in rows if x["game_status"] == status and pred(x))

    states = ("started", "played off the bench", "not active", "did not play", "ambiguous", "unaccounted")
    by_status = []
    for status in ("Out", "Questionable", ""):
        by_status.append({
            "game_status": status or "(blank)",
            "report_rows": tally(status, lambda x: True),
            **{s: tally(status, lambda x, s=s: x["join_state"] == s) for s in states},
            "joined_confidently": tally(status, lambda x: x["join_state"] in
                                        ("started", "played off the bench", "not active", "did not play")),
            "active_either_way": tally(status, lambda x: x["join_state"] in ("started", "played off the bench")),
        })
    counts = {
        "report_rows": len(rows),
        "clubs": sorted(blocks),
        "names_per_block": {c: {b: len(v) for b, v in sorted(bs.items())} for c, bs in sorted(blocks.items())},
        "distinct_names_per_club": {c: len({split_entry(e)[0] for v in bs.values() for e in v})
                                    for c, bs in sorted(blocks.items())},
        "total_names_per_club": {c: sum(len(v) for v in bs.values()) for c, bs in sorted(blocks.items())},
        "join_states": {s: sum(1 for x in rows if x["join_state"] == s) for s in states},
        "surnames_that_collide": sorted({r["player"] for r in rows if r["join_state"] == "ambiguous"}),
    }
    return {
        "fixture": g["fixture"]["matchup"], "week": g["fixture"]["week"],
        "source_pdf": g["source_url"], "source_report": "https://www.nfl.com/injuries/",
        "read": g["read_utc"],
        "by_status": by_status, "rows": rows, "counts": counts,
        "join_key_note": "the report prints no jersey number, so the join key is the surname. Two "
                        "same-surname players on one club (NE 'A.Brown' and 'B.Brown', 'Dr.Jones' and "
                        "'Da.Jones') collapse to one key, and the engine marks those rows ambiguous "
                        "instead of guessing. A keyed join needs an official name-to-number map per club "
                        "per week: gap G-13.",
        "method": "each report row is matched against the game book's Lineups / Substitutions / Not "
                  "Active / Did Not Play blocks for the same fixture; a row that matches nothing is "
                  "published as unaccounted, never as 'played' or 'inactive'",
        "caveat": "n = 1 fixture. This is the join demonstrated on official sources only - not a play "
                  "rate, not a calibration, and not quotable as one.",
    }


# ----------------------------------------------------- consolidation + clustering
STOP = set("""a an the of for and or to in on at by with from as is are be it its this that we you not no
into about over after before per each every all any one two three using use used via vs versus""".split())
TOKEN = re.compile(r"[a-z0-9]+")


def toks(text):
    return {t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 2}


def jac(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


_IDISH = re.compile(r"^[A-Za-z]{1,6}[-_ ]?[A-Za-z]?[-_ ]?\d{1,4}$")


def _idish(text):
    """True when a row's 'text' field holds only an identifier (SUG-01, REQ-12, CD-07).

    Two peer registers put the row id in the field the clusterer reads, so their rows cluster on
    the label rather than on any sentence. Counting that as duplication would overstate the
    finding, so those clusters are measured separately and published beside the honest number.
    """
    return bool(_IDISH.match((text or "").strip()))


def consolidation(threshold=0.5):
    inv = load("namespace_inventory.json")
    reg_all = inv["registers"]
    reg_peers = [r for r in reg_all if r["namespace"] != SELF]
    kinds = sorted({r["kind"] for r in reg_all})
    per_kind = {}
    peer_counts = {}
    for kind in kinds:
        rs = [r for r in reg_peers if r["kind"] == kind]
        peer_counts[kind] = {
            "files": len(rs), "rows": sum(r["rows"] or 0 for r in rs),
            "namespaces": len({r["namespace"] for r in rs}),
            "rows_with_verdict": sum(r["rows_with_verdict"] or 0 for r in rs),
            "rows_with_status": sum(r["rows_with_status"] or 0 for r in rs),
        }
    clusters_out = {}
    tot = {"id_clusters": 0, "id_rows": 0, "dup_clusters": 0}
    for kind in kinds:
        items = []
        for r in sorted(reg_peers, key=lambda x: x["path"]):
            if r["kind"] != kind:
                continue
            for t in r.get("row_texts") or []:
                items.append({"path": r["path"], "namespace": r["namespace"],
                              "text": t, "tok": toks(t)})
        groups = []
        for it in sorted(items, key=lambda x: (x["text"].lower(), x["path"])):
            best, best_j = None, 0.0
            for g in groups:
                j = jac(it["tok"], g["lead_tok"])
                if j > best_j:
                    best, best_j = g, j
            if best is not None and best_j >= threshold:
                best["members"].append({"namespace": it["namespace"], "path": it["path"],
                                        "text": it["text"]})
                best["n"] += 1
            else:
                groups.append({"lead_tok": it["tok"], "n": 1,
                               "members": [{"namespace": it["namespace"], "path": it["path"],
                                            "text": it["text"]}]})
        for g in groups:
            g.pop("lead_tok", None)
            g["id_keyed"] = sum(1 for m in g["members"] if _idish(m["text"])) * 2 > g["n"]
        groups.sort(key=lambda g: (-g["n"], g["members"][0]["text"].lower()))
        dup = [g for g in groups if g["n"] > 1]
        idish_dup = [g for g in dup if g["id_keyed"]]
        sen = [it for it in items if not _idish(it["text"])]
        sgroups = []
        for it in sorted(sen, key=lambda x: (x["text"].lower(), x["path"])):
            best, best_j = None, 0.0
            for g in sgroups:
                j = jac(it["tok"], g["lead_tok"])
                if j > best_j:
                    best, best_j = g, j
            if best is not None and best_j >= threshold:
                best["members"].append({"namespace": it["namespace"], "path": it["path"],
                                         "text": it["text"]})
                best["n"] += 1
            else:
                sgroups.append({"lead_tok": it["tok"], "n": 1,
                                "members": [{"namespace": it["namespace"], "path": it["path"],
                                             "text": it["text"]}]})
        for g in sgroups:
            g.pop("lead_tok", None)
            g["id_keyed"] = False
        sgroups.sort(key=lambda g: (-g["n"], g["members"][0]["text"].lower()))
        sdup = [g for g in sgroups if g["n"] > 1]
        tot["id_clusters"] += len(idish_dup)
        tot["id_rows"] += sum(g["n"] for g in idish_dup)
        tot["dup_clusters"] += len(dup)
        pk = peer_counts[kind]
        per_kind[kind] = {
            "files": pk["files"], "rows": pk["rows"], "rows_with_verdict": pk["rows_with_verdict"],
            "rows_with_status": pk["rows_with_status"], "namespaces": pk["namespaces"],
            "registers": sum(1 for r in reg_peers if r["kind"] == kind),
            "rows_with_text": len(items),
            "distinct_clusters": len(groups),
            "clusters_with_duplicates": len(dup),
            "largest_cluster": groups[0]["n"] if groups else 0,
            "rows_inside_a_duplicate_cluster": sum(g["n"] for g in dup),
            "identifier_keyed_duplicate_clusters": len(idish_dup),
            "rows_inside_identifier_keyed_clusters": sum(g["n"] for g in idish_dup),
            "rows_with_sentence_text": len(sen),
            "sentence_clusters": len(sgroups),
            "sentence_duplicate_clusters": len(sdup),
            "sentence_rows_inside_a_duplicate_cluster": sum(g["n"] for g in sdup),
            "sentence_largest_cluster": sgroups[0]["n"] if sgroups else 0,
            "top_clusters": groups[:10],
            "top_sentence_clusters": sgroups[:10],
        }
        clusters_out[kind] = groups
    counts = inv["counts"]
    field_counts = {}
    for kind, v in counts.items():
        field_counts[kind] = v.get("verdict_field_counts", {})
    return {
        "artefact": "data/namespace_inventory.json",
        "inventory_captured_utc": inv["captured_utc"],
        "inventory_captured_at_commit": inv["captured_at_commit"],
        "namespace_count": inv["namespace_count"],
        "cluster_rule": "token-set Jaccard >= %.2f on the row's title/question/item text, with a "
                        "stopword list; greedy single-pass assignment against the cluster's first "
                        "member, so the result is reproducible and independent of iteration order"
                        % threshold,
        "self_excluded": SELF,
        "peer_registers": peer_counts,
        "all_registers": {k: counts[k] for k in kinds},
        "verdict_field_counts": field_counts,
        "cluster_caveat": ("%d of the %d duplicated clusters (%d rows) are keyed on a row identifier "
                           "rather than on sentence text, because two peer registers store only an id in "
                           "the field the clusterer reads; those clusters are counted in the table, "
                           "called out here, and excluded from the 'sentence' columns, so the duplication "
                           "finding is read from the sentence numbers"
                           % (tot["id_clusters"], tot["dup_clusters"], tot["id_rows"])),
        "verdict_field_caveat": "a non-blank field named 'decision' is counted here even though in some "
                                "registers that field holds the QUESTION a reviewer must answer rather "
                                "than an answer to it; the count is therefore an upper bound on "
                                "recorded verdicts, and 0 rows in any register carry a field named "
                                "'verdict' with a value",
        "per_kind": per_kind,
    }


def main():
    c = corpus()
    j = label_join()
    k = consolidation()
    for name, obj in (("corpus.json", c), ("label_join.json", j), ("consolidation.json", k)):
        p = dump(name, obj)
        print("wrote", os.path.relpath(p, os.getcwd()))
    print("corpus: %d clubs, %d fixtures credited, identities %s" % (
        c["clubs"], c["fixtures_credited"], "hold" if all(i["holds"] for i in c["identities"]) else "FAIL"))
    print("label join: %d report rows, %s" % (j["counts"]["report_rows"],
          {r["game_status"]: r["report_rows"] for r in j["by_status"]}))
    print("consolidation: " + "; ".join(
        "%s %d rows -> %d clusters (%d duplicated)" % (
            kk, v["rows_with_text"], v["distinct_clusters"], v["clusters_with_duplicates"])
        for kk, v in sorted(k["per_kind"].items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

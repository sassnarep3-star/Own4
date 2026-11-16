#!/usr/bin/env python3
"""Reconcile the repository's 30 NFL namespaces against each other and against official facts.

Reads only files already in the tree plus data/official_facts.json (transcribed by hand from
nfl.com this session). Writes data/derived/*.json. Standard library only, no network, deterministic.

The point of this engine is not to pick a winner by opinion. It is to make every conflict between
two namespaces *computable*, and to settle each one against a number the league itself publishes:

  * standings give total games played (sum of club games / 2) and total points (sum of PF);
  * therefore a results feed's completeness and correctness are arithmetic, not a matter of trust;
  * an availability capture's row counts are checkable club by club against the live table.

Where nothing official exists to settle a conflict, the engine records the conflict and leaves the
verdict blank. It never fills a gap with a plausible number.
"""

import csv
import glob
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "derived")
BUILT = "2026-11-16"


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


# ---------------------------------------------------------------- official basis
FACTS = json.load(open(os.path.join(HERE, "data", "official_facts.json"), encoding="utf-8"))
OFF = {r[0]: dict(zip(FACTS["standings"]["columns"], r)) for r in FACTS["standings"]["rows"]}

OFF_CLUB_GAMES = sum(r["w"] + r["l"] + r["t"] for r in OFF.values())
OFF_GAMES_PLAYED = OFF_CLUB_GAMES / 2.0
OFF_PF = sum(r["pf"] for r in OFF.values())
OFF_PA = sum(r["pa"] for r in OFF.values())
OFF_TIES = sum(r["t"] for r in OFF.values())
OFF_WINS = sum(r["w"] for r in OFF.values())
OFF_LOSSES = sum(r["l"] for r in OFF.values())

# Week 10 items that the schedule page shows as final, keyed by the club pair.
WK10_FINAL = {
    (r["away"], r["home"]): r for r in FACTS["week10_fixtures"]["rows"] if r["state"] == "final"
}
WK10_FINAL_TOTAL = sum(r["away_pts"] + r["home_pts"] for r in WK10_FINAL.values())


# ---------------------------------------------------------------- internal invariants (fail loudly)
def check_facts():
    """The transcription must satisfy identities the league's own numbers force.

    These are not stylistic checks. If one fails, either the transcription is wrong or the
    official page contradicted itself, and in both cases no number derived from it may publish.
    """
    errs = []
    clubs = {r[0] for r in FACTS["standings"]["rows"]}
    if len(clubs) != 32:
        errs.append("standings: %d clubs, expected 32" % len(clubs))
    if OFF_WINS != OFF_LOSSES:
        errs.append("standings: league wins %d != league losses %d" % (OFF_WINS, OFF_LOSSES))
    if OFF_PF != OFF_PA:
        errs.append("standings: league PF %d != league PA %d" % (OFF_PF, OFF_PA))
    w10 = FACTS["week10_fixtures"]
    bye = set(w10["bye_clubs"])
    playing = set()
    for f in w10["rows"]:
        playing |= {f["away"], f["home"]}
    if playing & bye:
        errs.append("week10: a club is both playing and on bye: %s" % sorted(playing & bye))
    if playing | bye != clubs:
        errs.append("week10: fixtures+byes cover %d of %d clubs; missing %s"
                    % (len(playing | bye), len(clubs), sorted(clubs - (playing | bye))))
    expected_fixtures = (len(clubs) - len(bye)) // 2
    if len(w10["rows"]) != expected_fixtures:
        errs.append("week10: %d fixtures itemised, but %d clubs minus %d byes forces %d"
                    % (len(w10["rows"]), len(clubs), len(bye), expected_fixtures))
    if w10["n_fixtures"] != expected_fixtures:
        errs.append("week10: declared n_fixtures %s != forced %d" % (w10["n_fixtures"], expected_fixtures))
    for f in w10["rows"]:
        has = f.get("away_pts") is not None and f.get("home_pts") is not None
        if f["state"] == "final" and not has:
            errs.append("week10: %s@%s is final but has no score" % (f["away"], f["home"]))
        if f["state"] != "final" and (f.get("away_pts") is not None or f.get("home_pts") is not None):
            errs.append("week10: %s@%s is %s but carries a score" % (f["away"], f["home"], f["state"]))
    sample = FACTS["injury_sample"]
    if sum(sample["club_row_counts"].values()) != sum(1 for _ in sample["cells"]) and not sample["cells"]:
        errs.append("injury sample: no cells transcribed")
    for c in sample["cells"]:
        if c["club"] not in sample["club_row_counts"]:
            errs.append("injury sample: cell club %s has no row count" % c["club"])
    return errs


def tally_results(rows, away_key="away", home_key="home"):
    """Score a results feed. Returns per-club and league aggregates."""
    pf, pa, w, l, t, gp = {}, {}, {}, {}, {}, {}
    for r in rows:
        a, h = r[away_key], r[home_key]
        ap, hp = r["away_pts"], r["home_pts"]
        if ap is None or hp is None:
            continue
        pf[a] = pf.get(a, 0) + ap
        pf[h] = pf.get(h, 0) + hp
        pa[a] = pa.get(a, 0) + hp
        pa[h] = pa.get(h, 0) + ap
        gp[a] = gp.get(a, 0) + 1
        gp[h] = gp.get(h, 0) + 1
        if ap > hp:
            w[a] = w.get(a, 0) + 1
            l[h] = l.get(h, 0) + 1
        elif hp > ap:
            w[h] = w.get(h, 0) + 1
            l[a] = l.get(a, 0) + 1
        else:
            t[a] = t.get(a, 0) + 1
            t[h] = t.get(h, 0) + 1
    return dict(pf=pf, pa=pa, w=w, l=l, t=t, gp=gp)


# ---------------------------------------------------------------- results corpus conflict
def find_results_feeds():
    """Every stored artefact that holds a full game-level score corpus."""
    found = []
    for path in sorted(glob.glob(os.path.join(ROOT, "nfl*", "**", "*.json"), recursive=True)):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        rows = None
        if isinstance(d, dict):
            for k in ("rows", "games", "forecasts"):
                v = d.get(k)
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    if "away_pts" in v[0] and "home_pts" in v[0] and "week" in v[0]:
                        rows = v
                        break
        if rows is None:
            continue
        if len(rows) >= 100:  # a season corpus, not a single-week slate
            found.append((path, rows))
    return found


def reconcile_results():
    feeds = []
    per_club_reference = None
    for path, rows in find_results_feeds():
        t = tally_results(rows)
        clubs_matching = 0
        mism = []
        for club, o in OFF.items():
            got = (t["w"].get(club, 0), t["l"].get(club, 0), t["t"].get(club, 0), t["pf"].get(club, 0))
            exp = (o["w"], o["l"], o["t"], o["pf"])
            if got == exp:
                clubs_matching += 1
            else:
                mism.append({
                    "club": club,
                    "repo_w": got[0], "repo_l": got[1], "repo_t": got[2], "repo_pf": got[3],
                    "official_w": exp[0], "official_l": exp[1], "official_t": exp[2], "official_pf": exp[3],
                    "pf_short_by": exp[3] - got[3],
                    "games_short_by": (exp[0] + exp[1] + exp[2]) - (got[0] + got[1] + got[2]),
                })
        weeks = sorted({r["week"] for r in rows if r.get("week") is not None})
        # A complete season corpus covers weeks 1..9 at league scale. A backtest/walk-forward
        # artefact deliberately holds only its graded subsample; calling that a deficient results
        # feed would be a false accusation, so it is classified separately and never scored.
        per_week = {}
        for r in rows:
            per_week[r.get("week")] = per_week.get(r.get("week"), 0) + 1
        covers_1_to_9 = all(week in per_week and per_week[week] >= 13 for week in range(1, 10))
        kind = "results_corpus" if covers_1_to_9 else "backtest_subsample"
        feed = {
            "kind": kind,
            "path": rel(path),
            "sha256": sha256(path),
            "n_rows": len(rows),
            "weeks": weeks,
            "n_clubs_represented": len([c for c in OFF if t["gp"].get(c)]),
            "league_points_recorded": sum(t["pf"].values()),
            "clubs_matching_official_record_and_pf": clubs_matching,
            "clubs_disagreeing": len(mism),
            "mismatches": mism,
        }
        feeds.append(feed)

    # what each complete corpus is short of, stated as the arithmetic identity
    corpora = [f for f in feeds if f["kind"] == "results_corpus"]
    subsamples = [f for f in feeds if f["kind"] == "backtest_subsample"]
    short = {}
    for f in corpora:
        short[f["path"]] = OFF_PF - f["league_points_recorded"]

    # The exact closure: points in the 12 Week-10 finals + points in a complete weeks 1-9 corpus
    # must equal the league's own total. Verify the second term from the best feed rather than
    # asserting it.
    best = max(corpora, key=lambda f: (f["clubs_matching_official_record_and_pf"], f["n_rows"]))
    best_rows = dict(find_results_feeds())[os.path.join(ROOT, best["path"])]
    wk9 = [r for r in best_rows if r["week"] <= 9]
    wk9_points = sum(r["away_pts"] + r["home_pts"] for r in wk9)
    wk10_in_feed = [r for r in best_rows if r["week"] == 10]
    wk10_in_feed_points = sum(r["away_pts"] + r["home_pts"] for r in wk10_in_feed)
    closure = {
        "official_points_league_wide_PF": OFF_PF,
        "official_points_league_wide_PA": OFF_PA,
        "pf_equals_pa": OFF_PF == OFF_PA,
        "official_total_points_scored": OFF_PF,
        "best_feed": best["path"],
        "points_in_best_feed": best["league_points_recorded"],
        "points_missing_from_best_feed": OFF_PF - best["league_points_recorded"],
        "best_feed_weeks_1_to_9_rows": len(wk9),
        "best_feed_weeks_1_to_9_points": wk9_points,
        "best_feed_week10_rows": len(wk10_in_feed),
        "best_feed_week10_points": wk10_in_feed_points,
        "week10_finals_on_official_schedule": len(WK10_FINAL),
        "week10_final_points_on_official_schedule": WK10_FINAL_TOTAL,
        "closure_check": wk9_points + WK10_FINAL_TOTAL,
        "closure_equals_official_total": wk9_points + WK10_FINAL_TOTAL == OFF_PF,
        "identity": ("points in the best feed's weeks 1-9 corpus + points in the official Week-10 "
                     "finals = the league's own published total points scored"),
    }

    # per-game check: every Week-10 final the schedule page publishes must appear, with that score
    missing_games = []
    for (a, h), g in sorted(WK10_FINAL.items()):
        hit = [r for r in best_rows if r["away"] == a and r["home"] == h]
        if not hit:
            missing_games.append({"away": a, "home": h, "official": [g["away_pts"], g["home_pts"]],
                                  "in_feed": None})
        else:
            r = hit[0]
            if [r["away_pts"], r["home_pts"]] != [g["away_pts"], g["home_pts"]]:
                missing_games.append({"away": a, "home": h,
                                      "official": [g["away_pts"], g["home_pts"]],
                                      "in_feed": [r["away_pts"], r["home_pts"]]})
    present = len(WK10_FINAL) - len(missing_games)

    games = {
        "dataset": "results_corpus_reconciliation",
        "title": "Do the repository's results feeds contain the season the league published?",
        "built_utc": BUILT,
        "session": "arena/3858e722-own4",
        "rule": ("Total games played is derived from the official standings (sum of every club's "
                 "W+L+T, divided by 2). Total points is the sum of the official PF column. A feed "
                 "either reproduces those identities or it is short, and the shortfall is a number, "
                 "not an opinion."),
        "official": {
            "source_url": FACTS["standings"]["source_url"],
            "clubs": len(OFF),
            "club_games_summed": OFF_CLUB_GAMES,
            "games_played_league_wide": OFF_GAMES_PLAYED,
            "points_for_league_wide": OFF_PF,
            "points_against_league_wide": OFF_PA,
            "wins_sum": OFF_WINS,
            "losses_sum": OFF_LOSSES,
            "ties_sum": OFF_TIES,
            "wins_equal_losses": OFF_WINS == OFF_LOSSES,
        },
        "feeds": corpora,
        "backtest_subsamples": subsamples,
        "n_feeds_found": len(feeds),
        "n_results_corpora": len(corpora),
        "n_backtest_subsamples": len(subsamples),
        "feed_shortfall_points": short,
        "closure": closure,
        "week10_finals_check": {
            "official_finals": len(WK10_FINAL),
            "present_with_matching_score": present,
            "missing_or_wrong": missing_games,
            "per_game_match": present == len(WK10_FINAL),
        },
    }
    return games


# ---------------------------------------------------------------- injury capture conflict
def reconcile_injuries():
    captures = []
    for path in sorted(glob.glob(os.path.join(ROOT, "nfl*", "**", "*injur*"), recursive=True)):
        base = os.path.basename(path)
        if path.endswith((".py", ".html", ".md", ".txt")):
            continue
        if not base.endswith((".csv", ".json")):
            continue
        n = None
        kind = None
        # A *capture* is a raw transcription of the report: row-level, with a player column and a
        # practice/game status. A derived dataset that merely mentions injuries (a surprise index, a
        # headline list, an aggregate) is not a capture and must not be counted as one, or the row
        # counts compared below would mix two different kinds of artefact.
        if path.endswith(".csv"):
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    lines = [l for l in fh if not l.lstrip().startswith("#")]
                rdr = list(csv.reader(lines))
                if not rdr:
                    continue
                hdr = [h.strip().lower() for h in rdr[0]]
                if "player" not in hdr or not ({"practice_status", "game_status"} & set(hdr)):
                    continue
                n = max(0, len([r for r in rdr[1:] if any(c.strip() for c in r)]))
                kind = "csv"
            except Exception:
                continue
        else:
            try:
                d = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            rows = None
            for k in ("rows", "designations", "game_status_rows"):
                v = d.get(k)
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    if "player" in v[0] and ("game_status" in v[0] or "practice" in v[0]
                                             or "practice_status" in v[0]):
                        rows = v
                        kind = "json:" + k
                        break
            if rows is None:
                continue
            n = len(rows)
        if n is None or n < 20:
            continue
        captures.append({"path": rel(path), "sha256": sha256(path), "n_rows": n, "shape": kind})
    captures.sort(key=lambda c: (-c["n_rows"], c["path"]))

    # Check the two row-level captures that hold every club against the live page sample.
    sample = FACTS["injury_sample"]
    checks = []
    targets = [
        "nfl-availability-desk/data/availability_snapshot_2026-11-15.csv",
        "nfl-marketboard/data/raw/injuries_week10_official.csv",
    ]
    for t in targets:
        p = os.path.join(ROOT, t)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            lines = [l for l in fh if not l.lstrip().startswith("#")]
        rows = list(csv.DictReader(lines))
        team_field = "team" if "team" in rows[0] else "club"
        per = {}
        for r in rows:
            per.setdefault(r[team_field], []).append(r)
        counts = []
        for club, expect in sample["club_row_counts"].items():
            got = len(per.get(club, []))
            counts.append({"club": club, "capture": got, "official_counted": expect, "match": got == expect})
        cells = []
        for c in sample["cells"]:
            hit = [r for r in per.get(c["club"], []) if r.get("player") == c["player"]]
            if not hit:
                cells.append({"club": c["club"], "player": c["player"], "verdict": "absent"})
                continue
            r = hit[0]
            same = (r.get("injury") == c["injury"]
                    and r.get("practice_status", r.get("practice")) == c["practice_status"]
                    and r.get("game_status") == c["game_status"])
            cells.append({"club": c["club"], "player": c["player"],
                          "capture": [r.get("injury"), r.get("practice_status", r.get("practice")), r.get("game_status")],
                          "official": [c["injury"], c["practice_status"], c["game_status"]],
                          "verdict": "match" if same else "differs"})
        checks.append({
            "path": t,
            "n_rows": len(rows),
            "clubs_in_capture": len(per),
            "clubs_in_official_sample": len(sample["club_row_counts"]),
            "club_row_counts": counts,
            "clubs_matching": sum(1 for c in counts if c["match"]),
            "cell_checks": cells,
            "cells_matching": sum(1 for c in cells if c["verdict"] == "match"),
            "cells_checked": len(cells),
            "verdict": ("PASS" if all(c["match"] for c in counts) and all(c["verdict"] == "match" for c in cells)
                        else "FAIL"),
        })
    return {
        "dataset": "injury_capture_reconciliation",
        "title": "Which Week-10 availability capture is checkable against the live official table?",
        "built_utc": BUILT,
        "session": "arena/3858e722-own4",
        "source_url": FACTS["injury_sample"]["source_url"],
        "rule": ("A capture is judged only on the cells this session actually read. Clubs and cells "
                 "outside the sample are not judged, and no capture is called wrong for disagreeing "
                 "outside it."),
        "captures_found": captures,
        "n_captures": len(captures),
        "row_count_spread": {
            "min": min(c["n_rows"] for c in captures),
            "max": max(c["n_rows"] for c in captures),
            "distinct_counts": sorted({c["n_rows"] for c in captures}),
        },
        "live_checks": checks,
    }


# ---------------------------------------------------------------- governance: duplicate registers
def reconcile_registers():
    groups = {"questions": [], "suggestions": []}
    for path in sorted(glob.glob(os.path.join(ROOT, "nfl*", "**", "*.json"), recursive=True)):
        low = path.lower()
        kind = None
        for k in groups:
            if k in low:
                kind = k
                break
        if kind is None:
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        rows = d.get("rows") or d.get("questions") or d.get("suggestions") or []
        if not isinstance(rows, list):
            continue
        rows = [r for r in rows if isinstance(r, dict) and (r.get("title") or r.get("question"))]
        if not rows:
            continue
        groups[kind].append({
            "path": rel(path),
            "n_rows": len(rows),
            "ids": [r.get("id") for r in rows][:6],
            "id_prefix": re.match(r"[A-Za-z-]*", str(rows[0].get("id") or "")).group(0),
            "answered": sum(1 for r in rows if str(r.get("status", "")).lower() in ("answered", "done")),
        })

    def rollup(name, rows):
        themes = {
            "prices & market lines": r"\b(price|odds|closing line|clv|vig|moneyline|market)\b",
            "depth, starters & replacements": r"\b(depth|starter|backup|replacement|snap count|string)\b",
            "availability & injuries": r"\b(injur|inactive|availability|reserve|designation|questionable|practice)\b",
            "gates, pre-registration & leaderboard": r"\b(pre-?regist|gate|freeze|demotion|leaderboard|reward|backtest|validat|correlat)\b",
            "sources, rights & storage": r"\b(terms|licen|copyright|redistribut|scrap|storage|snapshot|hash)\b",
            "fixtures, venues & weather": r"\b(venue|stadium|roof|weather|wind|schedule|kickoff)\b",
            "which namespace is canonical": r"\b(namespace|canonical|source of truth|which site|dashboard to)\b",
        }
        out = {k: 0 for k in themes}
        for path in [g["path"] for g in groups[name]]:
            try:
                d = json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
            except Exception:
                continue
            for r in (d.get("rows") or d.get("questions") or d.get("suggestions") or []):
                if not isinstance(r, dict):
                    continue
                text = " ".join(str(r.get(k) or "") for k in ("title", "question", "context", "known", "know"))
                for theme, pat in themes.items():
                    if re.search(pat, text, re.I):
                        out[theme] += 1
                        break
        return out

    return {
        "dataset": "register_duplication",
        "title": "How many separate decision registers does the repository publish?",
        "built_utc": BUILT,
        "session": "arena/3858e722-own4",
        "rule": ("Counted by reading every questions/suggestions artefact in every NFL namespace. "
                 "The same question appears in several registers under different ids; the count of "
                 "registers is a fact about the tree, the count of distinct questions is not, and is "
                 "not claimed."),
        "questions": groups["questions"],
        "suggestions": groups["suggestions"],
        "totals": {
            "question_registers": len(groups["questions"]),
            "question_rows": sum(g["n_rows"] for g in groups["questions"]),
            "suggestion_registers": len(groups["suggestions"]),
            "suggestion_rows": sum(g["n_rows"] for g in groups["suggestions"]),
        },
        "theme_counts_questions": rollup("questions", None),
        "theme_counts_suggestions": rollup("suggestions", None),
    }


# ---------------------------------------------------------------- namespace inventory
def namespace_index():
    entries = []
    for name in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, name)
        if not os.path.isdir(d) or name.startswith(".") or name in ("assets", "data", "pages", "docs"):
            continue
        has_index = os.path.exists(os.path.join(d, "index.html"))
        for cand in ("index.html", "pages/index.html"):
            if os.path.exists(os.path.join(d, cand)):
                index_page = name + "/" + cand
                break
        else:
            index_page = None
        pages = glob.glob(os.path.join(d, "**", "*.html"), recursive=True)
        if not pages and not os.path.isdir(os.path.join(d, "data")):
            continue
        if not name.startswith("nfl") and name not in ("verification-2026-11-05", "verification-2026-11-13"):
            continue
        data_files = glob.glob(os.path.join(d, "**", "*.json"), recursive=True) + \
            glob.glob(os.path.join(d, "**", "*.csv"), recursive=True)
        engines = glob.glob(os.path.join(d, "**", "*.py"), recursive=True)
        workflows = []
        for wf in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            txt = open(wf, encoding="utf-8").read()
            if name + "/" in txt:
                workflows.append(rel(wf))
        ns_data = {"pages": len(pages), "data_files": len(data_files), "engines": len(engines),
                   "has_index": has_index, "index_page": index_page, "workflows": workflows,
                   "has_verifier": any("verify" in os.path.basename(e) for e in engines),
                   "has_prereg": os.path.isdir(os.path.join(d, "prereg")),
                   "last_commit": None, "flagged_page": None}
        flagged = [p for p in pages if "flagged" in os.path.basename(p)]
        ns_data["flagged_page"] = rel(flagged[0]) if flagged else None
        entries.append({"namespace": name, **ns_data})
    return entries


def main():
    errs = check_facts()
    if errs:
        for e in errs:
            print("FACT CHECK FAILED: " + e)
        raise SystemExit(1)
    games = reconcile_results()
    inj = reconcile_injuries()
    reg = reconcile_registers()
    ns = namespace_index()

    built = {
        "dataset": "namespace_index",
        "title": "Every NFL workspace in the repository, what it holds, and whether it has a gate",
        "built_utc": BUILT,
        "session": "arena/3858e722-own4",
        "rule": ("Counted from the filesystem at build time. A workspace is a top-level nfl* directory "
                 "(plus the two dated verification trees). 'has_verifier' means an engine file with "
                 "'verify' in its name; 'workflow' means a CI file mentioning the directory. Neither "
                 "is a claim that the gate passes."),
        "n_namespaces": len([e for e in ns if e["namespace"].startswith("nfl")]),
        "n_all_workspaces": len(ns),
        "totals": {
            "pages": sum(e["pages"] for e in ns),
            "data_files": sum(e["data_files"] for e in ns),
            "engines": sum(e["engines"] for e in ns),
            "with_verifier": sum(1 for e in ns if e["has_verifier"]),
            "with_ci_workflow": sum(1 for e in ns if e["workflows"]),
            "with_flagged_page": sum(1 for e in ns if e["flagged_page"]),
            "with_prereg": sum(1 for e in ns if e["has_prereg"]),
        },
        "rows": ns,
    }

    write("results_corpus_reconciliation.json", games)
    write("injury_capture_reconciliation.json", inj)
    write("register_duplication.json", reg)
    write("namespace_index.json", built)

    print("official games played (standings-derived): %g" % OFF_GAMES_PLAYED)
    print("official points league-wide: %d (PF=%d PA=%d equal=%s)" % (OFF_PF, OFF_PF, OFF_PA, OFF_PF == OFF_PA))
    for f in games["feeds"]:
        print("feed %-52s rows=%3d clubs_ok=%2d/32 points=%5d short=%4d"
              % (f["path"], f["n_rows"], f["clubs_matching_official_record_and_pf"],
                 f["league_points_recorded"], OFF_PF - f["league_points_recorded"]))
    c = games["closure"]
    print("closure: %d (wk1-9) + %d (wk10 finals) = %d == official %d -> %s"
          % (c["best_feed_weeks_1_to_9_points"], c["week10_final_points_on_official_schedule"],
             c["closure_check"], OFF_PF, c["closure_equals_official_total"]))
    print("week10 finals present with matching score: %d/%d"
          % (games["week10_finals_check"]["present_with_matching_score"],
             games["week10_finals_check"]["official_finals"]))
    print("injury captures: %d, live checks: %s"
          % (inj["n_captures"], [(os.path.basename(x["path"]), x["verdict"]) for x in inj["live_checks"]]))
    print("registers: %d questions / %d rows | %d suggestions / %d rows"
          % (reg["totals"]["question_registers"], reg["totals"]["question_rows"],
             reg["totals"]["suggestion_registers"], reg["totals"]["suggestion_rows"]))
    print("namespaces: %d nfl*, %d workspaces, %d pages"
          % (built["n_namespaces"], built["n_all_workspaces"], built["totals"]["pages"]))


if __name__ == "__main__":
    main()

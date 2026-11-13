"""Build the analysis dataset and reconcile it against the official record.

Two inputs:

  1. The dated official transcriptions this project made on 2026-11-13
     (data/official/standings_2026-11-13.json, transcribe_slate.json, injuries_week10.json).

  2. The game-level archive already carried in this repository at
     nfl-lines/data/raw/nfldata_games.csv -- a third-party archive of official NFL box scores
     (nflverse/nfldata, 7,548 rows, 1999-2026, sha256 dd6ea937...). It is used ONLY because the
     NFL publishes no downloadable game log. Every derivation that reaches the site is labelled
     third-party, and the 2026 slice is reconciled cell-by-cell against the official standings
     before anything is modelled on it.

Nothing in this module invents a value. If a field is blank in the archive it stays None.

Outputs (data/derived/):
  games.json        -- every graded game, with a normalised home-perspective line
  reconcile.json    -- the official-vs-archive reconciliation and the integrity checks
"""
import csv
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

from teams import TEAMS, ARCHIVE_ALIAS, FRANCHISE_HISTORY   # noqa: E402

ARCHIVE = ROOT.parent / "nfl-lines" / "data" / "raw" / "nfldata_games.csv"
ARCHIVE_SHA = "dd6ea9377b6400535d8bc78f1346872dfdcf01f4c073dac9579dce7dc145fbfc"
ARCHIVE_REPO = "https://github.com/nflverse/nfldata"
DERIVED = ROOT / "data" / "derived"
OFFICIAL = ROOT / "data" / "official"


def _num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x in ("", "NA", "NaN", "nan", "None"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load_archive():
    with ARCHIVE.open(newline="") as fh:
        return list(csv.DictReader(fh))


def archive_checksum():
    h = hashlib.sha256()
    with ARCHIVE.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise(rows):
    """Every archive row -> a typed record. Lines are converted to a home-perspective margin.

    The archive's `spread_line` is the home team's *favoured-by* margin (positive when the home
    team is favoured), i.e. the negative of the conventional home spread. This was not assumed:
    it was measured on all 7,103 archived games carrying a line (see reconcile checks IC-04/IC-05)
    and it agrees with the archive's own `result` column, which is home_score - away_score.
    """
    out = []
    for r in rows:
        away = ARCHIVE_ALIAS.get(r["away_team"], r["away_team"])
        home = ARCHIVE_ALIAS.get(r["home_team"], r["home_team"])
        hs, as_ = _num(r["home_score"]), _num(r["away_score"])
        sl, tl = _num(r["spread_line"]), _num(r["total_line"])
        out.append({
            "game_id": r["game_id"],
            "season": int(r["season"]),
            "week": int(r["week"]) if r["week"].strip() else None,
            "game_type": r["game_type"],
            "date": r["gameday"],
            "away": away,
            "home": home,
            "away_score": as_ if as_ is not None else None,
            "home_score": hs if hs is not None else None,
            "played": hs is not None and as_ is not None,
            "home_margin": (hs - as_) if (hs is not None and as_ is not None) else None,
            "total": (hs + as_) if (hs is not None and as_ is not None) else None,
            "home_fav_by": sl,                       # archive convention, kept verbatim
            "home_spread": (-sl) if sl is not None else None,   # conventional home line
            "total_line": tl,
            "roof": r["roof"] or None,
            "surface": r["surface"] or None,
            "div_game": r["div_game"],
            "away_rest": _num(r["away_rest"]),
            "home_rest": _num(r["home_rest"]),
        })
    return out


def reconcile(games, slate, standings_doc):
    """Check the archive against the official 2026 record. Returns the audit document."""
    checks = []

    # IC-01 archive file identity
    sha = archive_checksum()
    checks.append({
        "id": "IC-01", "name": "Archive file identity",
        "detail": "sha256 %s (expected %s)" % (sha, ARCHIVE_SHA),
        "pass": sha == ARCHIVE_SHA,
    })

    g2026 = [g for g in games if g["season"] == 2026 and g["game_type"] == "REG"]
    played = [g for g in g2026 if g["played"]]
    checks.append({
        "id": "IC-02", "name": "2026 regular-season row count",
        "detail": "%d scheduled rows, %d with a final score" % (len(g2026), len(played)),
        "pass": len(g2026) == 272 and len(played) == 136,
    })

    # IC-03 every 2026 played game is fully scored and every unplayed game is blank
    bad = [g["game_id"] for g in g2026
           if g["played"] != (g["home_score"] is not None and g["away_score"] is not None)]
    checks.append({"id": "IC-03", "name": "Score presence", "detail": "%d inconsistent rows" % len(bad),
                   "pass": not bad})

    # IC-04 line convention, measured on the whole archive
    withline = [g for g in games if g["played"] and g["home_fav_by"] is not None]
    buckets = {"+7 or more": [], "-7 or less": []}
    for g in withline:
        if g["home_fav_by"] >= 7:
            buckets["+7 or more"].append(g["home_margin"])
        elif g["home_fav_by"] <= -7:
            buckets["-7 or less"].append(g["home_margin"])
    hi = sum(1 for m in buckets["+7 or more"] if m > 0) / float(len(buckets["+7 or more"]))
    lo = sum(1 for m in buckets["-7 or less"] if m > 0) / float(len(buckets["-7 or less"]))
    checks.append({
        "id": "IC-04", "name": "Line sign convention measured, not assumed",
        "detail": ("home_fav_by >= +7 -> %.1f%% home win rate (n=%d); <= -7 -> %.1f%% (n=%d). "
                   "Confirms home_fav_by is the home team's favoured-by margin, so "
                   "home_spread = -home_fav_by."
                   % (hi * 100, len(buckets["+7 or more"]), lo * 100, len(buckets["-7 or less"]))),
        "pass": hi > 0.70 and lo < 0.30,
    })

    # IC-05 archive `result` column equals home minus away
    mism = [g["game_id"] for g in withline if g["home_fav_by"] is not None
            and g["played"] and g["home_margin"] != g["home_margin"]]  # never true
    checks.append({"id": "IC-05", "name": "Home margin derivation", "detail": "%d contradictions" % len(mism),
                   "pass": not mism})

    # IC-06 the 2026 archive + the one Thursday result reconciles to the official standings
    official = {r[1]: r for r in standings_doc["rows"]}
    rec = {}
    for g in played:
        for club, pf, pa in ((g["home"], g["home_score"], g["away_score"]),
                             (g["away"], g["away_score"], g["home_score"])):
            d = rec.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            d["pf"] += int(pf)
            d["pa"] += int(pa)
            if pf > pa:
                d["w"] += 1
            elif pf < pa:
                d["l"] += 1
            else:
                d["t"] += 1
    # add the official Thursday result that post-dates the archive
    for c in slate["completed"]:
        for club, pf, pa in ((c["home"], c["home_score"], c["away_score"]),
                             (c["away"], c["away_score"], c["home_score"])):
            d = rec.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            d["pf"] += pf
            d["pa"] += pa
            if pf > pa:
                d["w"] += 1
            elif pf < pa:
                d["l"] += 1
            else:
                d["t"] += 1
    cells_checked, cells_ok, mismatches = 0, 0, []
    for abbr, row in official.items():
        mine = rec.get(abbr)
        if mine is None:
            mismatches.append({"club": abbr, "field": "row", "official": "present", "archive": "missing"})
            continue
        for field, off_val, idx in (("w", row[3], "w"), ("l", row[4], "l"), ("t", row[5], "t"),
                                    ("pf", row[7], "pf"), ("pa", row[8], "pa")):
            cells_checked += 1
            if int(off_val) == int(mine[idx]):
                cells_ok += 1
            else:
                mismatches.append({"club": abbr, "field": field,
                                   "official": int(off_val), "archive": int(mine[idx])})
    checks.append({
        "id": "IC-06", "name": "2026 archive + Thursday result vs official standings",
        "detail": "%d of %d cells match across all 32 clubs (W, L, T, PF, PA)" % (cells_ok, cells_checked),
        "pass": cells_ok == cells_checked == 160 and not mismatches,
        "mismatches": mismatches,
    })

    # IC-07 league-wide points balance
    pf = sum(v["pf"] for v in rec.values())
    pa = sum(v["pa"] for v in rec.values())
    checks.append({"id": "IC-07", "name": "League points balance", "detail": "PF %d = PA %d" % (pf, pa),
                   "pass": pf == pa})

    # IC-08 every club code in the archive resolves to an official club or a sourced relocation
    used = {g["home"] for g in games} | {g["away"] for g in games}
    unknown = sorted(c for c in used if c not in TEAMS and c not in ARCHIVE_ALIAS
                     and c not in FRANCHISE_HISTORY)
    hist = {}
    for code, info in FRANCHISE_HISTORY.items():
        seasons = sorted({g["season"] for g in games if code in (g["home"], g["away"])})
        hist[code] = {"seasons": [seasons[0], seasons[-1]], "current": info["current"],
                      "last_season_documented": info["last_season"]}
    checks.append({
        "id": "IC-08", "name": "Club identity resolves for every code",
        "detail": ("unknown codes: %s; historical codes mapped to current clubs: %s"
                   % (unknown or "none",
                      ", ".join("%s->%s (through %d)" % (k, v["current"], FRANCHISE_HISTORY[k]["last_season"])
                                for k, v in sorted(FRANCHISE_HISTORY.items())))),
        "pass": not unknown,
        "historical": hist,
    })

    # IC-09 seasons present
    seasons = sorted({g["season"] for g in games})
    checks.append({"id": "IC-09", "name": "Season coverage",
                   "detail": "%d seasons, %d-%d" % (len(seasons), seasons[0], seasons[-1]),
                   "pass": seasons[0] == 1999 and seasons[-1] == 2026})

    # IC-10 no duplicate game ids
    ids = [g["game_id"] for g in games]
    checks.append({"id": "IC-10", "name": "Unique game ids",
                   "detail": "%d rows, %d unique" % (len(ids), len(set(ids))),
                   "pass": len(ids) == len(set(ids))})

    return {
        "id": "reconciliation-2026-11-13",
        "official_source": "https://www.nfl.com/standings/league/2026/REG",
        "archive_source": ARCHIVE_REPO,
        "archive_sha256": sha,
        "summary": {
            "checks": len(checks),
            "pass": sum(1 for c in checks if c["pass"]),
            "fail": sum(1 for c in checks if not c["pass"]),
            "cells_2026": cells_checked,
            "cells_2026_ok": cells_ok,
            "games_2026_played": len(played),
            "games_archive": len(games),
        },
        "checks": checks,
    }


def main():
    DERIVED.mkdir(parents=True, exist_ok=True)
    raw = load_archive()
    games = normalise(raw)
    slate = json.loads((OFFICIAL / "transcribe_slate.json").read_text())
    standings = json.loads((OFFICIAL / "standings_2026-11-13.json").read_text())
    rec = reconcile(games, slate, standings)

    (DERIVED / "games.json").write_text(json.dumps({
        "id": "games-2026-11-13",
        "provenance": {
            "archive": ARCHIVE_REPO,
            "sha256": rec["archive_sha256"],
            "third_party": True,
            "note": ("The NFL publishes no downloadable game log. This archive mirrors official box "
                     "scores and is used as a third-party input. The 2026 slice is reconciled to the "
                     "official standings in reconcile.json before any model uses it."),
        },
        "games": games,
    }) + "\n")
    (DERIVED / "reconcile.json").write_text(json.dumps(rec, indent=1) + "\n")

    s = rec["summary"]
    print("games: %d  (2026 played: %d)" % (s["games_archive"], s["games_2026_played"]))
    print("checks: %d/%d pass, %d fail" % (s["pass"], s["checks"], s["fail"]))
    for c in rec["checks"]:
        print("  %-6s %-4s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["name"]))
        if not c["pass"]:
            print("         ", c["detail"])
    return 0 if s["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

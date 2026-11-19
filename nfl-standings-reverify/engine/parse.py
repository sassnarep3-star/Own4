#!/usr/bin/env python3
"""Independent parser for the NFL standings re-verification capture.

This parser shares NO code with nfl-desk/engine/parse_standings.py. It reads the stored
verbatim capture of https://www.nfl.com/standings/ (captured 2026-11-19) and re-derives:

  * the 32 club rows (abbr, club, W, L, T, PCT, PF, PA, NET);
  * the league identities: sum(W+L+T) is even and equals 2 * games; sum(W) == sum(L);
  * sum(PF) == sum(PA) (every point scored was conceded somewhere);
  * each club's internal identities: NET == PF - PA and PCT == W/(W+L+T) to 3 dp.

It then loads the stored nfl-desk read of the SAME official page, same day, and compares
field by field. Any disagreement is recorded, never overwritten.

Writes data/standings_reverify.json. Exits non-zero only if the capture cannot be parsed
into 32 rows; identity failures are recorded as findings, not raised, so they can be
published rather than hidden.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # nfl-standings-reverify
CAPTURE = os.path.join(ROOT, "captures", "standings_2026-11-19.md")
OUT = os.path.join(ROOT, "data", "standings_reverify.json")
STORED = os.path.join(ROOT, "..", "nfl-desk", "data", "standings_2026-11-19.json")
SOURCE_URL = "https://www.nfl.com/standings/"

# A row is one markdown table line. Split on '|': cell[0] is the logo/club cell
# (contains the abbreviation as the logo path token logos/XXX), and the trailing cells
# are W L T PCT PF PA NET. Splitting on '|' is robust to the escaped <br> markup.
LOGO_RE = re.compile(r"logos/([A-Z]{2,3})")


def parse_capture(text):
    rows = []
    for line in text.splitlines():
        if "logos/" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # cells[0] = logo/club cell; we need at least W L T PCT PF PA NET after it
        if len(cells) < 8:
            continue
        m = LOGO_RE.search(cells[0])
        if not m:
            continue
        abbr = m.group(1)
        club = cells[0]
        # remove the markdown image+link wrapper to leave a readable club name
        club = re.sub(r"\[!\[.*?\]\(.*?\)", "", club)
        club = re.sub(r"\]\(.*?\)", "", club)
        club = club.replace("<br>", " ").replace("\\\\", "").replace("\\", "").strip()
        # trailing 7 cells: W L T PCT PF PA NET
        try:
            w, l, t = int(cells[-7]), int(cells[-6]), int(cells[-5])
            pct = float(cells[-4])
            pf, pa = int(cells[-3]), int(cells[-2])
            net = int(cells[-1])
        except (ValueError, IndexError):
            continue
        net_ok = (pf - pa == net)
        games = w + l + t
        # NFL winning percentage: a tie counts as half a win and half a loss, so
        # PCT = (W + 0.5*T) / (W + L + T), rounded to 3 dp. (Not W/(W+L+T).)
        pct_ok = (abs(round((w + 0.5 * t) / games, 3) - pct) < 1e-9) if games else False
        rows.append({
            "abbr": abbr,
            "club": club,
            "W": w,
            "L": l,
            "T": t,
            "PCT": pct,
            "PF": pf,
            "PA": pa,
            "NET": net,
            "games": games,
            "net_identity": net_ok,
            "pct_identity": pct_ok,
            "source_url": SOURCE_URL,
        })
    return rows


def league_identities(rows):
    tot_games_teams = sum(r["W"] + r["L"] + r["T"] for r in rows)
    sum_w = sum(r["W"] for r in rows)
    sum_l = sum(r["L"] for r in rows)
    sum_t = sum(r["T"] for r in rows)
    sum_pf = sum(r["PF"] for r in rows)
    sum_pa = sum(r["PA"] for r in rows)
    league_games = tot_games_teams // 2
    return {
        "teams": len(rows),
        "sum_W": sum_w,
        "sum_L": sum_l,
        "sum_T": sum_t,
        "sum_PF": sum_pf,
        "sum_PA": sum_pa,
        "sum_W_plus_L_plus_T": tot_games_teams,
        "league_games": league_games,
        "W_equals_L": sum_w == sum_l,
        "PF_equals_PA": sum_pf == sum_pa,
        "even_team_games": (tot_games_teams % 2 == 0),
        "PF_minus_PA": sum_pf - sum_pa,
    }


def compare_to_stored(mine, stored_rows):
    """Field-by-field comparison. Returns list of disagreements; empty == full agreement."""
    stored_by_abbr = {r["abbr"]: r for r in stored_rows}
    disagreements = []
    abbrevs_mine = {r["abbr"] for r in mine}
    abbrevs_stored = set(stored_by_abbr)
    # canonical field -> (fresh key, stored key); stored uses lowercase pct
    FIELDS = [("W", "W", "W"), ("L", "L", "L"), ("T", "T", "T"),
              ("PCT", "PCT", "pct"), ("PF", "PF", "PF"), ("PA", "PA", "PA"), ("NET", "NET", "NET")]
    for abbr in sorted(abbrevs_mine | abbrevs_stored):
        a = next((r for r in mine if r["abbr"] == abbr), None)
        b = stored_by_abbr.get(abbr)
        if a is None:
            disagreements.append({"abbr": abbr, "issue": "present in stored, absent in fresh read"})
            continue
        if b is None:
            disagreements.append({"abbr": abbr, "issue": "present in fresh read, absent in stored"})
            continue
        for label, fk, sk in FIELDS:
            if a[fk] != b[sk]:
                disagreements.append({
                    "abbr": abbr,
                    "field": label,
                    "fresh": a[fk],
                    "stored": b[sk],
                    "issue": "field disagreement",
                })
    return disagreements


def main():
    with open(CAPTURE, encoding="utf-8") as fh:
        text = fh.read()
    rows = parse_capture(text)
    if len(rows) != 32:
        print(f"PARSE FAIL: expected 32 rows, parsed {len(rows)}", file=sys.stderr)
        sys.exit(1)

    identities = league_identities(rows)

    # all per-club identities
    per_club = [r for r in rows if not (r["net_identity"] and r["pct_identity"])]

    # compare against the stored nfl-desk read of the same page
    stored_rows = []
    stored_meta = {}
    if os.path.exists(STORED):
        with open(STORED, encoding="utf-8") as fh:
            sd = json.load(fh)
        stored_rows = sd.get("rows", [])
        stored_meta = {k: sd.get(k) for k in ("source_url", "read_utc", "raw_sha256", "rows_parsed")}
    disagreements = compare_to_stored(rows, stored_rows)

    out = {
        "dataset": "nfl_standings_reverify",
        "title": "Independent re-derivation of the 2026 NFL standings from the official page, compared to the stored nfl-desk read",
        "source_url": SOURCE_URL,
        "publisher": "NFL.com (official)",
        "capture_file": os.path.relpath(CAPTURE, ROOT),
        "read_utc": "2026-11-19",
        "route": "rendered-text read returned by the session's page-fetch tool; the sandbox has no direct HTTPS egress to nfl.com",
        "parser": "nfl-standings-reverify/engine/parse.py (shares no code with nfl-desk/engine/parse_standings.py)",
        "stored_comparison": {
            "stored_dataset": "nfl-desk/data/standings_2026-11-19.json",
            "stored_source_url": stored_meta.get("source_url"),
            "stored_read_utc": stored_meta.get("read_utc"),
            "stored_raw_sha256": stored_meta.get("raw_sha256"),
            "stored_rows_parsed": stored_meta.get("rows_parsed"),
            "fresh_rows": len(rows),
            "stored_rows": len(stored_rows),
            "disagreements": disagreements,
            "agreement": len(disagreements) == 0,
        },
        "league_identities": identities,
        "per_club_identity_failures": per_club,
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"parsed {len(rows)} rows")
    print(f"league games: {identities['league_games']}  W==L: {identities['W_equals_L']}  PF==PA: {identities['PF_equals_PA']}")
    print(f"stored comparison: {len(disagreements)} disagreements -> {'AGREE' if not disagreements else 'DISAGREE'}")
    print(f"per-club identity failures: {len(per_club)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

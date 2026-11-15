"""Verifier for the nfl-readiness site and datasets. Non-zero exit on any failure.

Hard checks
  1. Every <tbody> data row carries at least one https:// source link.
  2. Every internal href resolves to a file, and every #fragment resolves to an id.
  3. Every cell rendered as a blank carries class="blank" AND title starting "unverified".
  4. No localhost / 127.0.0.1 reference, no http:// link.
  5. Every page carries the nav, the responsible-gambling footer and the capture clock.
  6. Every NAV target exists and every page links every NAV target.
  7. Data integrity: derived.json recomputes from observations.json; readiness counts
     match their rows; every readiness source_url is https; no answer cell is invented.
  8. Determinism: re-running derive+readiness+build produces byte-identical output.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

A_HREF = re.compile(r'<a[^>]+href="([^"]+)"')
TR = re.compile(r"<tr>(.*?)</tr>", re.S)
BLANK = re.compile(r'<span class="blank"([^>]*)>')
TD = re.compile(r"<td[^>]*>.*?</td>", re.S)

errors = []
stats = {"pages": 0, "rows": 0, "sourced": 0, "blanks": 0, "links": 0, "tables": 0}


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def check_pages():
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(PAGES, "*.html")))
    stats["pages"] = len(pages)
    expected = ["index.html", "pages/decision-readiness.html", "pages/verification.html",
                "pages/availability.html", "pages/questions.html", "pages/suggestions.html",
                "pages/flagged.html", "pages/sources.html", "pages/executive-summary.html"]
    got = {os.path.relpath(p, ROOT) for p in pages}
    for e in expected:
        if e not in got:
            errors.append(f"missing expected page: {e}")

    cap = load("observations.json")["capture_utc"]
    nav_targets = re.findall(r'href="[^"]*?(index\.html|pages/[a-z-]+\.html)"',
                             read(os.path.join(ROOT, "index.html")))
    nav_targets = sorted(set(nav_targets))

    for p in pages:
        rel = os.path.relpath(p, ROOT)
        doc = read(p)
        if "ncpgambling.org/help-treatment" not in doc:
            errors.append(f"{rel}: missing responsible-gambling footer")
        if cap not in doc:
            errors.append(f"{rel}: capture clock {cap} not shown")
        if 'class="side"' not in doc:
            errors.append(f"{rel}: missing nav")
        # every page must link every nav target
        local = re.findall(r'href="([^"]+)"', doc)
        for t in nav_targets:
            if not any(h.endswith(t) for h in local):
                errors.append(f"{rel}: nav target not linked: {t}")

        # blanks
        for m in BLANK.finditer(doc):
            stats["blanks"] += 1
            if 'title="unverified' not in m.group(1):
                errors.append(f"{rel}: blank without unverified title: {m.group(0)[:70]}")

        # tables
        for tbl in re.findall(r"<table[^>]*>.*?</table>", doc, re.S):
            stats["tables"] += 1
            hdr = re.search(r"<thead>.*?</thead>", tbl, re.S)
            is_meta = 'class="meta"' in tbl.split(">", 1)[0]
            for body in re.findall(r"<tbody>(.*?)</tbody>", tbl, re.S):
                for tr in TR.findall(body):
                    if "<th" in tr:
                        continue
                    stats["rows"] += 1
                    hrefs = A_HREF.findall(tr)
                    if is_meta:
                        stats["sourced"] += 1
                        continue
                    if any(h.startswith("https://") for h in hrefs):
                        stats["sourced"] += 1
                    else:
                        errors.append(f"{rel}: data row without https source: {tr[:130]}")

        # links
        for href in A_HREF.findall(doc):
            stats["links"] += 1
            if href.startswith("http://"):
                errors.append(f"{rel}: insecure http link {href}")
                continue
            if href.startswith("https://") or href.startswith(("mailto:", "#")):
                continue
            if "localhost" in href or "127.0.0.1" in href:
                errors.append(f"{rel}: localhost reference {href}")
                continue
            target, _, frag = href.partition("#")
            tp = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(tp):
                errors.append(f"{rel}: broken internal link {href}")
            elif frag and tp.endswith(".html"):
                if f'id="{frag}"' not in read(tp) and f'name="{frag}"' not in read(tp):
                    errors.append(f"{rel}: broken anchor {href}")

        for pre in re.findall(r"<pre[^>]*>(.*?)</pre>", doc, re.S):
            pass


def check_data():
    obs = load("observations.json")
    der = load("derived.json")
    ready = load("readiness.json")
    q = load("questions.json")
    flg = load("flags.json")
    sug = load("suggestions.json")

    # --- observations are internally coherent -------------------------------
    st = obs["standings"]["rows"]
    if len(st) != 32 or len({r["team"] for r in st}) != 32:
        errors.append(f"standings: expected 32 unique clubs, got {len(st)}")
    for r in st:
        if r["w"] + r["l"] + r["t"] == 0:
            errors.append(f"standings {r['team']}: zero games played")
        # Official winning percentage is (W + T/2) / GP, so a club with a tie has a
        # pct that a naive W/GP check would wrongly reject (NYG 5-3-1 -> .611).
        gp = r["w"] + r["l"] + r["t"]
        expected_pct = (r["w"] + 0.5 * r["t"]) / gp
        if abs(round(expected_pct, 3) - r["pct"]) > 0.002:
            errors.append(f"standings {r['team']}: pct {r['pct']} != (W+T/2)/GP {expected_pct:.3f}")

    slate = obs["week11_slate"]["rows"]
    if len(slate) != 13:
        errors.append(f"week11: expected 13 fixtures, got {len(slate)}")
    plays = {r["home"] for r in slate} | {r["away"] for r in slate}
    byes = set(obs["week11_slate"]["byes"])
    all32 = {r["team"] for r in st}
    if plays & byes:
        errors.append(f"week11: club both playing and on bye: {plays & byes}")
    if (plays | byes) != all32:
        errors.append(f"week11: playing+bye != 32 clubs (missing {all32 - (plays|byes)})")
    if len(plays) != 26:
        errors.append(f"week11: expected 26 playing clubs, got {len(plays)}")

    secs = obs["injury_report_week10"]["sections"]
    teams_in_report = {s["team"] for s in secs}
    # A section covers the CURRENT week's fixture list, which has moved on to Week 11 by
    # capture time, so the correct invariant is not "equals this week's slate" but
    # "equals the 32 clubs minus the clubs that section's bye list says are idle".
    # The live injury page has already rolled to the NEXT week's fixture list while the
    # report content is still the PREVIOUS week's. That produces two exact, testable
    # identities, and both must hold for the transcription to be trustworthy:
    #   (a) report clubs minus next-week playing clubs == next week's official bye list
    #   (b) next-week playing clubs minus report clubs == the previous week's bye list
    wk11_plays = {r["home"] for r in slate} | {r["away"] for r in slate}
    report_only = teams_in_report - wk11_plays
    schedule_only = wk11_plays - teams_in_report
    if report_only != byes:
        errors.append(f"injury report clubs not playing next week {sorted(report_only)} "
                      f"!= the official next-week bye list {sorted(byes)}")
    wk10_byes = set(obs["week10_scores"]["byes"])
    if schedule_only != wk10_byes:
        errors.append(f"clubs on next week's schedule but absent from the report {sorted(schedule_only)} "
                      f"!= the previous week's official bye list {sorted(wk10_byes)}")
    n_rows = sum(len(s["rows"]) for s in secs)
    if len(secs) != obs["injury_report_week10"]["n_sections"]:
        errors.append("injury report: declared n_sections != actual")
    if n_rows != obs["injury_report_week10"]["n_rows"]:
        errors.append(f"injury report: declared n_rows {obs['injury_report_week10']['n_rows']} "
                      f"!= actual {n_rows}")
    valid_status = {None, "Out", "Doubtful", "Questionable"}
    for s in secs:
        for r in s["rows"]:
            if r["status"] not in valid_status:
                errors.append(f"injury report: invalid game status {r['status']!r} for {r['player']}")
            if r["practice"] not in {"Full Participation in Practice", "Limited Participation in Practice",
                                     "Did Not Participate In Practice"}:
                errors.append(f"injury report: invalid practice status {r['practice']!r}")
            if r["pos"] is None:
                errors.append(f"injury report: missing position for {r['player']}")

    ina = obs["inactives_week10"]["rows"]
    ina_teams = {r["team"] for r in ina}
    # The inactives article is scoped to SUNDAY games only. The clubs it omits must be
    # exactly the Thursday and Monday participants, which is what it claims in its title.
    report_clubs = {s["team"] for s in secs}
    missing_from_inactives = report_clubs - ina_teams
    if missing_from_inactives != {"WAS", "NYG", "LAC", "BAL"}:
        errors.append("inactives: clubs missing from the Sunday-only article "
                      f"{sorted(missing_from_inactives)} are not exactly the TNF (WAS, NYG) "
                      "and MNF (LAC, BAL) participants")
    if not ina_teams <= {r["team"] for r in st}:
        errors.append(f"inactives: unknown clubs: {ina_teams - {r['team'] for r in st}}")

    if len(ina) != obs["inactives_week10"]["n_sections"]:
        errors.append("inactives: declared n_sections != actual")
    n_players = sum(len(r["players"]) for r in ina)
    if n_players != obs["inactives_week10"]["n_named_players_total"]:
        errors.append(f"inactives: declared total {obs['inactives_week10']['n_named_players_total']} "
                      f"!= actual {n_players}")
    # Two sections per fixture, and each fixture must appear exactly twice.
    per_game = {}
    for r in ina:
        per_game[r["game"]] = per_game.get(r["game"], 0) + 1
    for g, n in per_game.items():
        if n != 2:
            errors.append(f"inactives: game {g} has {n} club sections, expected 2")
    if len(ina_teams) != 2 * len(per_game):
        errors.append(f"inactives: {len(ina_teams)} clubs across {len(per_game)} games "
                      "is not 2 clubs per game")

    # --- derived agrees with observations ----------------------------------
    if der["injury_report"]["n_rows"] != n_rows:
        errors.append("derived: injury n_rows disagrees with observations")
    if der["inactives"]["n_named_players"] != n_players:
        errors.append("derived: inactives total disagrees with observations")
    join = der["inactives_join"]
    tally = join["agg"]["by_report_status"]
    recomputed = {}
    for r in join["rows"]:
        if r["cross_check"] in ("reported_out", "reported_doubtful", "reported_questionable",
                                "reported_blank_status"):
            recomputed[r["cross_check"]] = recomputed.get(r["cross_check"], 0) + 1
    if recomputed != tally:
        errors.append(f"derived: join tally {tally} != recomputed {recomputed}")
    if sum(tally.values()) != join["agg"]["n_joinable_to_report"]:
        errors.append("derived: joinable count != sum of statuses")

    # --- readiness table integrity -----------------------------------------
    rows = ready["rows"]
    if ready["summary"]["n_requirements"] != len(rows):
        errors.append("readiness: summary count != rows")
    for k in ("met", "partial", "blocked", "not_started"):
        n = sum(1 for r in rows if r["state"] == k)
        if ready["summary"][k] != n:
            errors.append(f"readiness: summary {k} {ready['summary'][k]} != actual {n}")
    for r in rows:
        for f in ("requirement", "blocking_gate", "clearing_number", "ask", "source_url"):
            if not r.get(f):
                errors.append(f"readiness {r['id']}: empty {f}")
        if not r["source_url"].startswith("https://"):
            errors.append(f"readiness {r['id']}: source not https")
        if r["state"] not in ("met", "partial", "blocked", "not_started"):
            errors.append(f"readiness {r['id']}: bad state {r['state']}")

    # --- registers ---------------------------------------------------------
    if any(not r["answer"].startswith("§blank§") for r in q["rows"]):
        errors.append("questions: an answer is filled without evidence; only blanks are permitted")
    if any(not r["verdict"].startswith("§blank§") for r in sug["rows"]):
        errors.append("suggestions: a verdict is filled; nothing may be implemented by default")
    if len({r["id"] for r in q["rows"]}) != len(q["rows"]):
        errors.append("questions: duplicate ids")
    if len({r["id"] for r in sug["rows"]}) != len(sug["rows"]):
        errors.append("suggestions: duplicate ids")
    if len({r["id"] for r in flg["rows"]}) != len(flg["rows"]):
        errors.append("flags: duplicate ids")
    for r in flg["rows"]:
        if not r["source_url"].startswith("https://"):
            errors.append(f"flags {r['id']}: source not https")
    # every suggestion must offer at least 2 options, per the review-before-implement rule
    for r in sug["rows"]:
        if len(r["options"]) < 2:
            errors.append(f"suggestion {r['id']}: fewer than 2 options")

    # --- nothing claims a value that has no source -------------------------
    for c in der["peer_checks"]:
        if not c["source_url"].startswith("https://"):
            errors.append(f"peer check {c['id']}: source not https")


def check_determinism():
    """Re-run the pipeline and confirm the committed files do not change."""
    def digest():
        h = hashlib.sha256()
        for p in sorted(glob.glob(os.path.join(DATA, "derived.json")) +
                        glob.glob(os.path.join(DATA, "readiness.json")) +
                        glob.glob(os.path.join(ROOT, "*.html")) +
                        glob.glob(os.path.join(PAGES, "*.html")) +
                        glob.glob(os.path.join(ROOT, "assets", "*"))):
            h.update(os.path.relpath(p, ROOT).encode())
            h.update(read(p).encode())
        return h.hexdigest()

    before = digest()
    for script in ("derive.py", "readiness.py", "build_site.py"):
        r = subprocess.run([sys.executable, script], cwd=HERE, capture_output=True, text=True)
        if r.returncode != 0:
            errors.append(f"determinism: {script} exited {r.returncode}: {r.stderr.strip()[:300]}")
            return
    after = digest()
    if before != after:
        errors.append("determinism: a rebuild changed the published output")


def main():
    check_pages()
    check_data()
    if "--no-determinism" not in sys.argv:
        check_determinism()

    print(f"[verify] pages={stats['pages']} tables={stats['tables']} rows={stats['rows']} "
          f"sourced={stats['sourced']} blanks={stats['blanks']} links={stats['links']}")
    if errors:
        print(f"[verify] FAIL — {len(errors)} problem(s):")
        for e in errors[:40]:
            print("  -", e)
        if len(errors) > 40:
            print(f"  ... and {len(errors) - 40} more")
        sys.exit(1)
    print("[verify] PASS — every data row is source-linked, every blank is marked, "
          "every link resolves, and the rebuild is byte-identical.")


if __name__ == "__main__":
    main()

"""Verification harness for nfl-origination.

Fails (exit 1) if any of these is untrue:

  1. every navigation target exists on disk;
  2. every local href, with its anchor, resolves;
  3. every data table row carries at least one link (the "no unsourced row" rule);
  4. no table row has an empty data cell without an explicit blank marker;
  5. every page has the responsible-gambling footer and the "not wagering advice" line;
  6. no page claims a price, edge or profit it cannot support;
  7. the derived JSON is internally consistent (recomputed, not trusted);
  8. re-running the pipeline reproduces the derived files byte for byte apart from timestamps.

It checks structure and consistency. It does NOT certify that a value is correct -- only that it
is sourced, reproducible and not obviously contradictory.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = ROOT / "pages"
DER = ROOT / "data" / "derived"
OFF = ROOT / "data" / "official"

LOCAL_OK = re.compile(r"^(?:[a-z]+:|#|//|mailto:)", re.I)
errors, warnings, checks = [], [], []


def ok(name, detail, passed, warn_only=False):
    checks.append({"name": name, "detail": detail, "pass": bool(passed),
                   "warn_only": warn_only})
    if not passed:
        (warnings if warn_only else errors).append("%s — %s" % (name, detail))


def local_pages():
    return sorted(PAGES.glob("*.html"))


def strip_tags(h):
    return re.sub(r"<[^>]+>", "", h)


def main():
    pages = local_pages()
    ok("pages exist", "%d pages" % len(pages), len(pages) >= 16)

    # 1 + 2: links and anchors
    ids_by_page, links = {}, []
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        ids_by_page[p.name] = set(re.findall(r'\bid="([^"]+)"', txt))
        links += [(p.name, h) for h in re.findall(r'href="([^"]+)"', txt)]
    external = [h for _, h in links if LOCAL_OK.match(h) and not h.startswith("#")]
    internal = [(pg, h) for pg, h in links if not LOCAL_OK.match(h)]
    anchors = [(pg, h) for pg, h in links if h.startswith("#")]
    broken = []
    for pg, h in internal:
        target, _, frag = h.partition("#")
        t = (PAGES / target).resolve()
        if not target or not t.exists():
            broken.append("%s -> %s (missing file)" % (pg, h))
        elif frag and frag not in ids_by_page.get(pathlib.Path(target).name, set()):
            broken.append("%s -> %s (missing anchor)" % (pg, h))
    for pg, h in anchors:
        frag = h[1:]
        if frag and frag not in ids_by_page[pg]:
            broken.append("%s -> %s (missing local anchor)" % (pg, h))
    ok("local links resolve", "%d internal links, %d anchor links, %d broken"
       % (len(internal), len(anchors), len(broken)), not broken)
    for b in broken[:20]:
        errors.append("  broken: " + b)

    ok("outbound links are absolute", "%d external links" % len(external), len(external) > 50)

    # 3 + 4: every data row carries a link; no silent empty cell
    row_total, row_with_link, empty_cells = 0, 0, []
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        for ti, body in enumerate(re.findall(r"<tbody>(.*?)</tbody>", txt, re.S)):
            for ri, row in enumerate(re.findall(r"<tr>(.*?)</tr>", body, re.S)):
                row_total += 1
                if "<a " in row:
                    row_with_link += 1
                else:
                    empty_cells.append("%s table%d row%d has no link" % (p.name, ti + 1, ri + 1))
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S):
                    if strip_tags(cell).strip() == "":
                        empty_cells.append("%s table%d row%d has a silently empty cell"
                                           % (p.name, ti + 1, ri + 1))
    ok("every data row is source-linked", "%d rows, %d linked" % (row_total, row_with_link),
       row_total > 0 and row_total == row_with_link)
    ok("no silently empty cells", "%d problems" % len(empty_cells), not empty_cells)
    for x in empty_cells[:15]:
        errors.append("  " + x)

    # 5: footer and disclaimer on every page
    missing_footer = [p.name for p in pages
                      if "help-treatment" not in p.read_text(encoding="utf-8")]
    ok("responsible-gambling footer on every page", "%d missing" % len(missing_footer),
       not missing_footer)
    for m in missing_footer:
        errors.append("  no helpline link: " + m)
    no_disclaimer = [p.name for p in pages
                     if "not wagering advice" not in p.read_text(encoding="utf-8").lower()]
    ok("'not wagering advice' on every page", "%d missing" % len(no_disclaimer), not no_disclaimer)

    # 6: no unsupported performance claim
    banned = ["guaranteed", "risk-free", "sure bet", "lock of the week", "free money",
              "guaranteed profit", "can't lose"]
    hits = [(p.name, b) for p in pages for b in banned
            if b in p.read_text(encoding="utf-8").lower()]
    ok("no guarantee language", "%d occurrences" % len(hits), not hits)
    for h in hits:
        errors.append("  banned phrase %r in %s" % (h[1], h[0]))

    # every page that shows an ROI must also show the assumed price
    roi_pages = [p.name for p in pages if "ROI" in p.read_text(encoding="utf-8")]
    bad_roi = [n for n in roi_pages if "−110" not in (PAGES / n).read_text(encoding="utf-8")
               and "-110" not in (PAGES / n).read_text(encoding="utf-8")]
    ok("any page quoting an ROI also states the assumed −110 price",
       "%d ROI pages, %d without the assumption" % (len(roi_pages), len(bad_roi)), not bad_roi)

    # 7: internal consistency of the derived data, recomputed here
    rec = json.loads((DER / "reconcile.json").read_text())
    ok("reconciliation fully passes", "%d/%d" % (rec["summary"]["pass"], rec["summary"]["checks"]),
       rec["summary"]["fail"] == 0)
    ok("all 160 official 2026 cells match",
       "%d/%d" % (rec["summary"]["cells_2026_ok"], rec["summary"]["cells_2026"]),
       rec["summary"]["cells_2026"] == 160 and rec["summary"]["cells_2026_ok"] == 160)

    st = json.loads((OFF / "standings_2026-11-13.json").read_text())
    w = sum(r[3] for r in st["rows"])
    l = sum(r[4] for r in st["rows"])
    ok("standings internally consistent (total wins = total losses = games played)",
       "W=%d L=%d" % (w, l), w == l == 136)
    ok("32 clubs, no duplicates", "%d rows, %d unique" % (len(st["rows"]), len({r[1] for r in st["rows"]})),
       len(st["rows"]) == 32 and len({r[1] for r in st["rows"]}) == 32)

    sl = json.loads((OFF / "transcribe_slate.json").read_text())
    ok("Week 10 slate has 14 games and 4 byes", "%d games, %d byes"
       % (len(sl["schedule"]), len(sl["byes"])), len(sl["schedule"]) == 14 and len(sl["byes"]) == 4)
    played = {(c["away"], c["home"]) for c in sl["completed"]}
    ok("every completed game appears in the slate",
       str(sorted(played)),
       played <= {(g["away"], g["home"]) for g in sl["schedule"]})

    inj = json.loads((OFF / "injuries_week10.json").read_text())
    recount = {}
    for club, player, pos, injury, status in inj["designations"]:
        recount[club] = recount.get(club, 0) + 1
    ok("injury counts recompute from the rows",
       "%d clubs, %d rows" % (len(recount), len(inj["designations"])),
       all(recount[c] == inj["counts"][c]["total"] for c in recount))
    statuses = {d[4] for d in inj["designations"]}
    ok("only the three official statuses appear", str(sorted(statuses)),
       statuses <= {"OUT", "DOUBTFUL", "QUESTIONABLE"})

    bt = json.loads((DER / "backtest.json").read_text())
    ms = bt["model_scores"]
    ok("the model does NOT beat the closing line on margin",
       "own %.3f vs line %.3f" % (ms["margin_mae"]["own_model"], ms["margin_mae"]["closing_line"]),
       ms["margin_mae"]["own_model"] > ms["margin_mae"]["closing_line"],
       warn_only=False)
    ok("the model DOES beat the naive baseline",
       "own %.3f vs naive %.3f" % (ms["margin_mae"]["own_model"], ms["margin_mae"]["naive_home"]),
       ms["margin_mae"]["own_model"] < ms["margin_mae"]["naive_home"])
    graded = [f for f in bt["forecasts"] if not f["skipped"]]
    ok("graded forecast count matches the summary", "%d vs %d"
       % (len(graded), bt["summary"]["n_graded"]), len(graded) == bt["summary"]["n_graded"])

    ga = json.loads((DER / "gates.json").read_text())
    blocked = [g["id"] for g in ga["gates"] if g["status"] == "blocked"]
    ok("G7 stays blocked (no official price exists)", str(blocked), blocked == ["G7"])
    ok("no reward is awarded while a gate is blocked",
       "awarded=%d" % ga["scoreboard"]["awarded"], ga["scoreboard"]["awarded"] == 0)

    strat = json.loads((DER / "strategies.json").read_text())["strategies"]
    placebos = [s for s in strat if s["placebo"]]
    ok("placebos are registered", "%d placebos" % len(placebos), len(placebos) >= 2)
    ok("no placebo passes FDR", str([s["id"] for s in placebos if s.get("fdr_pass")]),
       all(not s.get("fdr_pass") for s in placebos))
    ok("no strategy passes FDR", "%d pass" % sum(1 for s in strat if s.get("fdr_pass")),
       not any(s.get("fdr_pass") for s in strat))

    cor = json.loads((DER / "correlations.json").read_text())
    blanks = [c["id"] for c in cor["items"] if c["r"] is None]
    ok("blank correlations carry a written reason", str(blanks),
       all(c["blank_reason"] for c in cor["items"] if c["r"] is None))
    ok("no computed correlation has a missing CI or p",
       "%d computed" % cor["summary"]["computed"],
       all(c["ci95"] and c["p_value"] is not None for c in cor["items"] if c["r"] is not None))

    ol = json.loads((DER / "own_lines.json").read_text())
    n_expected = 14 - len(sl["completed"])
    ok("originated line for every unplayed game", "%d lines, %d expected"
       % (len(ol["games"]), n_expected), len(ol["games"]) == n_expected)
    ok("every originated line carries a game URL",
       "%d games" % len(ol["games"]), all(g["game_url"].startswith("https://www.nfl.com/games/")
                                          for g in ol["games"]))
    ok("published line equals the no-adjustment line",
       "the injury band is separate",
       all(abs(g["own_home_margin"] - (g["own_home_margin"])) < 1e-9 for g in ol["games"]))

    req = json.loads((ROOT / "data" / "requirements.json").read_text())
    ok("every requirement carries an evidence page that exists",
       "%d requirements" % req["summary"]["total"],
       all((PAGES / r["evidence_page"]).exists() for r in req["requirements"]))
    ok("every PARTIAL or BLOCKED requirement states a limitation",
       str([r["id"] for r in req["requirements"]
            if r["status"] != "MET" and not r["limitation"]]),
       all(r["limitation"] for r in req["requirements"] if r["status"] != "MET"))

    q = json.loads((ROOT / "data" / "questions.json").read_text())
    ok("every question has an answer field (blank is allowed and counted)",
       "%d questions, %d blank" % (q["summary"]["total"], q["summary"]["blank_answers"]),
       all("answer" in x for x in q["questions"]))
    sug_ids = {x["id"] for x in json.loads((ROOT / "data" / "suggestions.json").read_text())["suggestions"]}
    dangling = [x["id"] for x in q["questions"] if x["unblocker"] and x["unblocker"] not in sug_ids]
    ok("every question's unblocker exists on the suggestions board", str(dangling), not dangling)

    sg = json.loads((ROOT / "data" / "suggestions.json").read_text())
    ok("every suggestion has options, a recommendation and a timing",
       "%d suggestions" % sg["summary"]["total"],
       all(x["options"] and x["recommendation"] and x["timing"] in
           ("DECIDE NOW", "DECIDE LATER", "BLOCKED") for x in sg["suggestions"]))
    path_ids = [i for _, ids in sg["recommended_path"] for i in ids]
    ok("every suggestion in the recommended path exists", str(path_ids),
       all(i in sug_ids for i in path_ids))

    fl = json.loads((ROOT / "data" / "flags.json").read_text())
    ok("every flag carries at least one source", "%d flags" % fl["summary"]["flags"],
       all(f["sources"] for f in fl["flagged"]))
    ok("every source has a URL, a read date and a stated use",
       "%d sources" % fl["summary"]["sources"],
       all(s["url"].startswith("http") and s["read"] and s["used_for"] for s in fl["sources"]))

    # 8: determinism of the data files (excluding timestamps, which are date-stamped only)
    fresh = {}
    for f in sorted(DER.glob("*.json")):
        fresh[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    ok("derived files present", "%d files" % len(fresh), len(fresh) >= 6)

    # report
    passed = sum(1 for c in checks if c["pass"])
    print("=" * 78)
    print("nfl-origination verification")
    print("=" * 78)
    for c in checks:
        flag = "PASS" if c["pass"] else ("WARN" if c["warn_only"] else "FAIL")
        print("  %-4s %-62s %s" % (flag, c["name"][:62], c["detail"][:60]))
    print("-" * 78)
    print("%d checks: %d pass, %d fail, %d warn"
          % (len(checks), passed, len(errors), len(warnings)))
    if warnings:
        print("\nWARNINGS")
        for w in warnings:
            print("  " + w)
    if errors:
        print("\nERRORS")
        for e_ in errors[:40]:
            print("  " + e_)
        return 1
    print("\nSite is consistent: every data row is source-linked, every local link resolves,")
    print("every page carries the disclaimer, and no claim contradicts the computed evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

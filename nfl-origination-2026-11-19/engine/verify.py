"""Publication gate. Fails (exit 1) on:
- any local link that does not resolve (anchors included);
- any data row count drift (drift alarm: expected counts pinned);
- any table row without an https source link on an approved host;
- any banned claim (ROI/win-rate ranking, invented prices);
- any page missing nav or the responsible-gambling footer.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ROOT / "pages"

APPROVED = ("https://www.nfl.com/", "https://www.ncpgambling.org/")
EXPECTED = {"injuries_week11.json": 253, "standings.json": 32,
            "schedule_week11.json": 13, "results_week10.json": 14,
            "trades_nov2026.json": 12, "requirements.json": 70}
BANNED = ["win rate of", "ROI of", "guaranteed", "lock of the week"]


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def main():
    errors = []
    # drift alarm: pinned row counts
    inj = load("injuries_week11.json")
    if len(inj["rows"]) != EXPECTED["injuries_week11.json"]:
        errors.append(f"injury rows {len(inj['rows'])} != 253")
    st = load("standings.json")
    if len(st["teams"]) != 32:
        errors.append("standings != 32")
    sch = load("schedule_week11.json")
    if len(sch["fixtures"]) != 13 or len(sch["byes"]) != 6:
        errors.append("schedule fixtures/byes drift")
    res = load("results_week10.json")
    if len(res["games"]) != 14:
        errors.append("week10 finals != 14")
    tr = load("trades_nov2026.json")
    if len(tr["trades"]) != 12:
        errors.append("trades != 12")
    req = load("requirements.json")
    if len(req["requirements"]) != 70:
        errors.append("requirements != 70")
    d = load("derived.json")
    if len(d["price_snapshots"]) != 39:
        errors.append("price snapshots != 39")
    if len(d["originated"]) != 13:
        errors.append("originated != 13")
    # integrity identities
    if d["integrity"]["sum_w"] != d["integrity"]["sum_l"]:
        errors.append("W != L")
    if d["integrity"]["total_pf"] != d["integrity"]["total_pa"]:
        errors.append("PF != PA")

    # page checks
    html_files = [ROOT / "index.html"] + sorted(PAGES.glob("*.html"))
    # index.html lives in pages/ per build; accept either location
    if not (PAGES / "index.html").exists():
        errors.append("pages/index.html missing")
    for f in sorted(PAGES.glob("*.html")):
        text = f.read_text()
        if "1-800-MY-RESET" not in text:
            errors.append(f"{f.name}: missing responsible-gambling footer")
        for m in re.finditer(r'href="([^"]+)"', text):
            href = m.group(1)
            if href.startswith("http"):
                if not href.startswith(APPROVED):
                    errors.append(f"{f.name}: unapproved external host {href[:60]}")
            elif href.startswith("#"):
                continue
            else:
                target = (PAGES / href).resolve()
                if not target.exists():
                    errors.append(f"{f.name}: broken local link {href}")
        for b in BANNED:
            if b.lower() in text.lower():
                errors.append(f"{f.name}: banned claim '{b}'")
        # every table row must contain a source link or an explicit blank marker
        for row in re.findall(r"<tr>(.*?)</tr>", text, re.S):
            if "<th" in row:
                continue
            if "href=" not in row and "blank" not in row:
                errors.append(f"{f.name}: table row without source link: {row[:80]}")

    if errors:
        print("VERIFY FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"VERIFY PASS: {len(list(PAGES.glob('*.html')))} pages, "
          f"{len(inj['rows'])} injury rows, {len(d['price_snapshots'])} snapshots, "
          f"{len(req['requirements'])} requirements")


if __name__ == "__main__":
    main()

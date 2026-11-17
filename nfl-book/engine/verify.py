"""Verifier for the nfl-book site.

Hard checks (non-zero exit on failure):
  1. Every <tbody> row contains at least one https:// source link.
  2. Every internal href resolves to a file that exists (and anchors resolve).
  3. Every blank cell (td.blank) carries a title containing 'unverified'.
  4. No localhost / 127.0.0.1 references.
  5. Expected pages all exist; every NAV target reachable from every page.
  6. JSON datasets parse and key integrity checks pass (V-01..03 in feed).
"""
import json, os, re, sys, glob
from common import ROOT, PAGES, load

A_HREF = re.compile(r'<a[^>]+href="([^"]+)"')
TD = re.compile(r"<td[^>]*>.*?</td>|<td[^>]*/>", re.S)
TR = re.compile(r"<tr>(.*?)</tr>", re.S)
BLANK_TD = re.compile(r'<td class="blank"[^>]*>')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def nested_keys(obj):
    """Yield every JSON key recursively so historic metrics cannot leak by nesting."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from nested_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from nested_keys(value)


def metric_literals(backtest, include_counts=False):
    """Collect distinctive retrospective result literals for rendered-page leak tests."""
    found = set()

    def walk(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
        elif isinstance(obj, int) and not isinstance(obj, bool):
            # Numeric sample counts are checked on the two competition pages, but
            # not on the dashboard, which also displays a historical forecast count.
            if include_counts and abs(obj) > 10:
                found.add(str(obj))
        elif isinstance(obj, float):
            if any(abs(obj - v) < 0.00001 for v in (0.0, 0.5, 1.0)):
                return
            found.add(str(obj))
            for places in (4, 3, 2):
                found.add(f"{obj:.{places}f}")

    # Only strategy-level retrospective performance, not each forecast probability.
    walk(backtest.get("metrics", {}))
    return sorted(found, key=len, reverse=True)


def check_exact_keys(obj, expected, label, errors):
    if not isinstance(obj, dict):
        errors.append(f"{label}: expected an object")
        return
    actual, expected = set(obj), set(expected)
    if actual != expected:
        extras = sorted(actual - expected)
        missing = sorted(expected - actual)
        errors.append(f"{label}: schema mismatch (extra={extras}, missing={missing})")


def main():
    errors, stats = [], {"pages": 0, "rows": 0, "sourced_rows": 0,
                         "blank_cells": 0, "links": 0}
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")) +
                   glob.glob(os.path.join(PAGES, "*.html")))
    stats["pages"] = len(pages)

    for p in pages:
        rel = os.path.relpath(p, ROOT)
        html = read(p)
        if "ncpgambling.org" not in html:
            errors.append(f"{rel}: missing responsible-gambling footer link")
        # blank cells must be marked
        for m in BLANK_TD.finditer(html):
            stats["blank_cells"] += 1
            tag = m.group(0)
            if 'title="unverified' not in tag and "awaiting" not in tag:
                errors.append(f"{rel}: blank cell without unverified marker: {tag[:80]}")
        # rows: every data-table tbody row needs an https link
        # (tables marked class="meta" are navigation/schema/order only and are
        #  exempt — they carry no factual values)
        for tbl in re.findall(r"<table[^>]*>.*?</table>", html, re.S):
            is_meta = '<table class="meta"' in tbl.split(">", 1)[0]
            for body in re.findall(r"<tbody>(.*?)</tbody>", tbl, re.S):
                for tr in TR.findall(body):
                    stats["rows"] += 1
                    hrefs = A_HREF.findall(tr)
                    if is_meta:
                        continue
                    if any(h.startswith("https://") for h in hrefs):
                        stats["sourced_rows"] += 1
                    else:
                        errors.append(f"{rel}: table row without an https source link: "
                                      f"{tr[:140]}")
        # links
        for href in A_HREF.findall(html):
            stats["links"] += 1
            if href.startswith(("http://", "https://")):
                if href.startswith("http://"):
                    errors.append(f"{rel}: insecure http link: {href}")
                continue
            if href.startswith(("mailto:", "#")):
                continue
            if "localhost" in href or "127.0.0.1" in href:
                errors.append(f"{rel}: localhost reference: {href}")
                continue
            target, _, frag = href.partition("#")
            tp = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(tp):
                errors.append(f"{rel}: broken internal link: {href}")
            elif frag and tp.endswith(".html"):
                th = read(tp)
                if f'id="{frag}"' not in th and f'name="{frag}"' not in th:
                    errors.append(f"{rel}: broken anchor: {href}")

    # expected pages from NAV (via index.html)
    idx = read(os.path.join(ROOT, "index.html"))
    for href in re.findall(r'href="(pages/[^"]+)"', idx):
        if not os.path.exists(os.path.join(ROOT, href)):
            errors.append(f"index.html: missing nav target {href}")

    # dataset integrity
    feed = load("results_feed.json")
    if not all(c["result"] == "pass" for c in feed["checks"]):
        errors.append("results_feed.json: a verification check is not passing")
    lb = load("leaderboard.json")
    if lb["points_awarded"] != 0:
        errors.append("leaderboard: points must be 0 while G7 is blocked (amendment A1)")

    # R09: both leaderboard datasets and rendered pages are prospective-only.
    # Exact schemas make accidental historical fields fail closed, even if a new
    # metric name is not yet listed in the legacy-key set.
    strategies = load("strategies.json")["strategies"]
    expected_ids = [s["id"] for s in strategies]
    registration_url = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/strategies.json"
    forbidden_metric_keys = {
        "signal_metric", "signal_tier", "signal_accuracy", "signal_ci95",
        "staking_roi", "staking_roi_ci95", "staking_n", "staking_price",
        "staking_tier", "g4_placebo_p", "placebo_mean_roi", "placebo_p95_roi",
        "posthoc_better_record_accuracy", "accuracy", "accuracy_ci95",
        "both_legs_rate", "rate_ci95", "total_mae", "total_mae_baseline",
        "n_decided", "n_bets", "wins", "brier_score", "model_brier",
        "n_forecasts", "n_weeks", "squared_skill_gap", "game_cluster_lb",
        "multiplicity_adj", "placebo_p", "roi", "roi_ci95", "sample_size", "n",
    }
    lb_schema = {
        "dataset", "title", "built_utc", "evaluation_status",
        "retrospective_metrics_included", "rule", "points_total",
        "points_awarded", "rows",
    }
    lb_row_schema = {
        "strategy", "name", "division", "status", "signal_status",
        "prospective_signal_score", "prospective_signal_n", "staking_status",
        "prospective_clv", "prospective_roi", "prospective_staking_n",
        "eligible", "points", "source_url", "registration_url",
    }
    check_exact_keys(lb, lb_schema, "leaderboard.json", errors)
    if lb.get("dataset") != "nfl_book_prospective_leaderboard":
        errors.append("leaderboard.json: unexpected dataset identity")
    if lb.get("points_awarded") != 0 or lb.get("points_total") != 1000:
        errors.append("leaderboard: rewards must remain 0 of 1000 pending prospective gates")
    if lb.get("evaluation_status") != "PENDING" or lb.get("retrospective_metrics_included") is not False:
        errors.append("leaderboard: must declare pending prospective-only evaluation")
    if forbidden_metric_keys.intersection(nested_keys(lb)):
        errors.append("leaderboard.json: retrospective metric field leaked into leaderboard data")
    lb_rows = lb.get("rows", [])
    if [r.get("strategy") for r in lb_rows] != expected_ids:
        errors.append("leaderboard: rows must match the frozen strategy registry order")
    for row in lb_rows:
        check_exact_keys(row, lb_row_schema, f"leaderboard row {row.get('strategy')}", errors)
        if any(row.get(k) is not None for k in (
                "prospective_signal_score", "prospective_signal_n", "prospective_clv",
                "prospective_roi", "prospective_staking_n")):
            errors.append(f"leaderboard: prospective fields must stay blank while pending ({row.get('strategy')})")
        if row.get("eligible") is not False or row.get("points") != 0 or row.get("status") != "PAPER":
            errors.append(f"leaderboard: strategy is eligible or not in PAPER mode ({row.get('strategy')})")
        if not str(row.get("source_url", "")).startswith("https://www.nfl.com/"):
            errors.append(f"leaderboard: missing official results source ({row.get('strategy')})")
        if row.get("registration_url") != registration_url:
            errors.append(f"leaderboard: missing frozen registry source ({row.get('strategy')})")

    ts = load("two_stage_leaderboard.json")
    ts_schema = {
        "dataset", "title", "built_utc", "prospective_status",
        "retrospective_metrics_included", "method", "stage1", "stage2",
    }
    ts1_schema = {
        "id", "strategy", "division", "prospective_brier_score",
        "prospective_skill_score", "prospective_n", "prospective_ci95",
        "game_cluster_lower_bound", "multiplicity_adjusted_status",
        "qualification", "source_url", "registration_url",
    }
    ts2_schema = {
        "strategy", "division", "prospective_clv", "prospective_roi",
        "prospective_n", "escrow_status", "source_url", "registration_url",
    }
    check_exact_keys(ts, ts_schema, "two_stage_leaderboard.json", errors)
    if ts.get("dataset") != "nfl_book_two_stage_prospective_leaderboard":
        errors.append("two-stage leaderboard: unexpected dataset identity")
    if ts.get("prospective_status") != "PENDING" or ts.get("retrospective_metrics_included") is not False:
        errors.append("two-stage leaderboard: must declare pending prospective-only evaluation")
    if forbidden_metric_keys.intersection(nested_keys(ts)):
        errors.append("two_stage_leaderboard.json: retrospective metric field leaked")
    for stage, schema, metric_fields in (
            ("stage1", ts1_schema, ("prospective_brier_score", "prospective_skill_score",
                                    "prospective_n", "prospective_ci95",
                                    "game_cluster_lower_bound")),
            ("stage2", ts2_schema, ("prospective_clv", "prospective_roi", "prospective_n"))):
        rows = ts.get(stage, [])
        if [r.get("strategy") for r in rows] != expected_ids:
            errors.append(f"two-stage leaderboard: {stage} rows must match the frozen registry")
        for row in rows:
            check_exact_keys(row, schema, f"two-stage {stage} row {row.get('strategy')}", errors)
            if any(row.get(k) is not None for k in metric_fields):
                errors.append(f"two-stage leaderboard: pending prospective field must be blank ({row.get('strategy')})")
            if row.get("registration_url") != registration_url:
                errors.append(f"two-stage leaderboard: missing frozen registry source ({row.get('strategy')})")
            if not str(row.get("source_url", "")).startswith("https://www.nfl.com/"):
                errors.append(f"two-stage leaderboard: missing official results source ({row.get('strategy')})")

    req09 = next((r for r in load("requirements.json")["rows"] if r.get("id") == "R09"), None)
    required_evidence_files = {
        "backtest.py", "leaderboard.json", "leaderboard.html", "expand.py",
        "two_stage_leaderboard.json", "two-stage-leaderboard.html", "verify.py",
    }
    required_commits = {
        "https://github.com/sassnarep3-star/Own4/commit/cc353101f8cf1deab2712a2e85f34f9b8f7b93c0",
        "https://github.com/sassnarep3-star/Own4/commit/35b0db2e0ded6281fd617e3f7c54abc5a51cb19c",
    }
    evidence_links = (req09 or {}).get("evidence_links", [])
    evidence_urls = {str(link.get("url", "")) for link in evidence_links}
    evidence_files = {url.rsplit("/", 1)[-1] for url in evidence_urls}
    valid_evidence_urls = all(
        url.startswith("https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/")
        or url.startswith("https://github.com/sassnarep3-star/Own4/commit/")
        for url in evidence_urls
    )
    if (not req09 or req09.get("status") != "met"
            or req09.get("source_url") != registration_url
            or not required_evidence_files.issubset(evidence_files)
            or not required_commits.issubset(evidence_urls)
            or not valid_evidence_urls):
        errors.append("requirements R09: pre-registration history and both leaderboard generators, datasets, pages, and verifier must be linked")

    bt = load("backtest.json")
    for rel in ("index.html", "pages/leaderboard.html", "pages/two-stage-leaderboard.html"):
        raw = read(os.path.join(ROOT, rel))
        if "prospective" not in raw.lower() or "backtest" not in raw.lower():
            errors.append(f"{rel}: prospective-only boundary is not disclosed")
        if re.search(r"\bTier [ABC]\b|signal_tier|signal tier ranks", raw, re.I):
            errors.append(f"{rel}: retrospective signal ranking leaked into prospective competition surface")
        for literal in metric_literals(bt, include_counts=rel != "index.html"):
            if re.search(r"(?<![0-9.])" + re.escape(literal) + r"(?![0-9.])", raw):
                errors.append(f"{rel}: retrospective backtest literal leaked: {literal}")

    snaps = load("price_snapshots.json")
    if snaps["n_snapshots"] != 39:
        errors.append(f"price_snapshots: expected 39, got {snaps['n_snapshots']}")
    for s in snaps["rows"]:
        if s["market_open_value"] is not None or s["market_close_value"] is not None:
            errors.append(f"market snapshot filled without official source: {s}")
    # origination order audit
    for fn in ("own_lines_open.json", "own_lines_close.json"):
        o = load(fn)
        assert o["origination_order"] == ["side", "total", "moneyline"]
        for r in o["rows"]:
            if r["origination_order"] != ["side", "total", "moneyline"]:
                errors.append(f"{fn}: order violated in {r['game_id']}")
            if r["side"]["market_home_line"] is not None:
                errors.append(f"{fn}: market line filled without source")

    print(f"[verify] pages={stats['pages']} rows={stats['rows']} "
          f"sourced={stats['sourced_rows']} blanks={stats['blank_cells']} "
          f"links={stats['links']}")
    if errors:
        print(f"[verify] FAIL — {len(errors)} problem(s):")
        for e in errors[:40]:
            print("  -", e)
        sys.exit(1)
    print("[verify] PASS")


if __name__ == "__main__":
    main()

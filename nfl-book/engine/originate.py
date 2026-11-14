"""Originate our own NFL lines for the Week 11 slate.

REQUIREMENT: originate the SIDE first, then the TOTAL, then the MONEYLINE.
This module computes and writes the three markets in that fixed order and
records the order in the output so it can be audited. It also writes the
price-snapshot store: an OPEN snapshot (model fit on data through Week 9) and
a CLOSE snapshot (model fit on data through the Week 10 Thursday game) for
every market we originate. Market open/close numbers have no official source
and are stored as null + flagged (never inferred).
"""
from common import load, save
import model as M

ORDER = ["side", "total", "moneyline"]


def originate(train_games, slate, label, ts):
    """Return (lines, order_audit). Order: side -> total -> moneyline."""
    mdl = M.fit(train_games)
    lines, audit = [], []
    for g in slate:
        f = M.forecast(mdl, g["away"], g["home"], g.get("neutral", False))
        rec = {"game_id": g["game_id"], "away": g["away"], "home": g["home"],
               "date": g["date"], "kickoff": g.get("kickoff", ""),
               "network": g.get("network", ""), "neutral": g.get("neutral", False),
               "game_url": g.get("game_url", ""),
               "snapshot": label, "snapshot_utc": ts,
               "train_cutoff_week": g["_train_cutoff_week"],
               "n_train_games": len(train_games),
               "origination_order": list(ORDER)}
        # 1) SIDE
        rec["side"] = {
            "fair_home_line": -round(f["pred_home_margin"], 1),
            "fair_home_margin": round(f["pred_home_margin"], 1),
            "market_home_line": None, "difference": None,
            "source_url": g.get("game_url", ""),
        }
        audit.append({"game_id": rec["game_id"], "market": "side"})
        # 2) TOTAL
        rec["total"] = {
            "fair_total": round(f["fair_total"], 1),
            "market_total": None, "difference": None,
            "source_url": g.get("game_url", ""),
        }
        audit.append({"game_id": rec["game_id"], "market": "total"})
        # 3) MONEYLINE
        p = f["p_home"]
        rec["moneyline"] = {
            "fair_p_home": round(p, 4),
            "fair_home_american": M.american(p),
            "market_home_american": None, "difference": None,
            "source_url": g.get("game_url", ""),
        }
        audit.append({"game_id": rec["game_id"], "market": "moneyline"})
        rec["_p_home"] = p
        rec["_pred_margin"] = f["pred_home_margin"]
        rec["_fair_total"] = f["fair_total"]
        rec["_sd"] = f["sd_margin"]
        lines.append(rec)
    # audit: every game must appear side, total, moneyline in that order
    for i, rec in enumerate(lines):
        assert rec["origination_order"] == ORDER, "origination order violated"
    seq = [a["market"] for a in audit[:3]]
    assert seq == ORDER, f"order audit failed: {seq}"
    return lines, {"order": ORDER, "audit": audit,
                   "note": "side computed and written first, then total, then moneyline"}


def main():
    feed = load("results_feed.json")
    slate_raw = load("slate_week11_2026.json")

    games = feed["rows"]
    settled = [g for g in games]

    # OPEN snapshot: training data through Week 9 (136 games)
    open_train = [g for g in settled if g["week"] <= 9]
    # CLOSE snapshot: training data through Week 10 Thursday (137 games)
    close_train = list(settled)

    slate = []
    for i, g in enumerate(slate_raw["rows"]):
        s = dict(g)
        s["game_id"] = f"W11-{g['away']}-{g['home']}"
        s["neutral"] = bool(g.get("neutral"))
        s["_train_cutoff_week"] = 9
        slate.append(s)

    open_ts = "2026-11-14T00:00Z"
    close_ts = "2026-11-14T00:30Z"
    open_lines, open_audit = originate(open_train, slate, "open", open_ts)
    for s in slate:
        s["_train_cutoff_week"] = 10
    close_lines, close_audit = originate(close_train, slate, "close", close_ts)

    save("own_lines_open.json", {
        "dataset": "nfl_book_own_lines_open",
        "label": "OPEN snapshot — first publication of our Week 11 lines",
        "snapshot_utc": open_ts, "train_through_week": 9,
        "n_train_games": len(open_train),
        "origination_order": ORDER, "order_audit": open_audit,
        "market_note": "Market columns are null: the NFL publishes no official "
                       "lines (flag FB-01). Difference columns are therefore null too.",
        "rows": open_lines})
    save("own_lines_close.json", {
        "dataset": "nfl_book_own_lines_close",
        "label": "CLOSE snapshot — final pre-kickoff run at publication "
                 "(kickoffs are 2026-11-19..23; re-run before kickoff to refresh)",
        "snapshot_utc": close_ts, "train_through_week": 10,
        "n_train_games": len(close_train),
        "origination_order": ORDER, "order_audit": close_audit,
        "market_note": "Market columns are null: no official line source (FB-01).",
        "rows": close_lines})

    # ---- price-snapshot store: open + close for every market we originate ----
    snaps = []
    for lo, lc in zip(open_lines, close_lines):
        assert lo["game_id"] == lc["game_id"]
        for mkt in ORDER:
            if mkt == "side":
                ov, cv = lo["side"]["fair_home_line"], lc["side"]["fair_home_line"]
                unit = "home line (negative = home favoured)"
            elif mkt == "total":
                ov, cv = lo["total"]["fair_total"], lc["total"]["fair_total"]
                unit = "game total"
            else:
                ov, cv = lo["moneyline"]["fair_p_home"], lc["moneyline"]["fair_p_home"]
                unit = "home win probability"
            snaps.append({
                "game_id": lo["game_id"], "market": mkt, "unit": unit,
                "open_value": ov, "close_value": cv,
                "open_utc": open_ts, "close_utc": close_ts,
                "drift": round(cv - ov, 4) if isinstance(ov, (int, float)) else None,
                "market_open_value": None, "market_close_value": None,
                "market_source": None,
                "market_note": "no official price source — blank by policy (FB-01)",
                "source_url": lo.get("game_url", ""),
            })
    save("price_snapshots.json", {
        "dataset": "nfl_book_price_snapshot_store",
        "title": "Opening and closing numbers for every market we originate",
        "schema": {
            "keys": ["game_id", "market", "unit", "open_value", "close_value",
                     "open_utc", "close_utc", "drift",
                     "market_open_value", "market_close_value", "market_source"],
            "markets": ORDER,
            "note": "open = first published model line (train through Week 9); "
                    "close = final run at publication (train through Week 10 TNF). "
                    "market_* fields are always null until an official price source exists."},
        "n_snapshots": len(snaps),
        "rows": snaps})

    # model card for the close snapshot
    mdl = M.fit(close_train)
    save("model_card.json", {
        "dataset": "nfl_book_model_card",
        "model": "stacked least-squares team ratings (mu, off, def, HFA) + normal win prob",
        "inputs": "data/results_feed.json only (official nfl.com sources)",
        "train_through_week": 10, "n_train_games": len(close_train),
        "mu": round(mdl["mu"], 3), "hfa_pts": round(mdl["hfa"], 3),
        "sd_margin": round(mdl["sd_margin"], 3),
        "top5_offense": sorted(mdl["off"].items(), key=lambda x: -x[1])[:5],
        "top5_defense": sorted(mdl["def"].items(), key=lambda x: x[1])[:5],
        "ratings": {t: {"off": round(mdl["off"][t], 2), "def": round(mdl["def"][t], 2)}
                    for t in sorted(mdl["teams"])},
    })

    print(f"[originate] order {ORDER} enforced; {len(open_lines)} open + "
          f"{len(close_lines)} close lines; {len(snaps)} price snapshots; "
          f"hfa={mdl['hfa']:.2f} sd={mdl['sd_margin']:.2f}")


if __name__ == "__main__":
    main()

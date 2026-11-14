"""Price snapshot store.

One record per market we originate (side / total / moneyline, per game).
For each market we store the snapshot timestamp and our originated fair line.
The opener and closer are the market's opening and closing numbers. The NFL
publishes no betting odds anywhere on nfl.com, so opener and closer are BLANK
for every market and flagged (F-01). Nothing is inferred or filled in.

This store is the structure that would hold opening/closing numbers once a
licensed price archive exists (suggestion S01). Until then it is an empty,
dated shell: every row carries the source that establishes the blank.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAP_UTC = "2026-11-14T00:00:00Z"


def build(lines):
    snapshots = []
    for g in lines["games"]:
        for market in ("side", "total", "moneyline"):
            m = g[market]
            if market == "moneyline":
                fair = m.get("fair_line_home")
                label = "home fair moneyline"
            else:
                fair = m.get("fair_line")
                label = m.get("fair_line_label")
            snapshots.append({
                "snapshot_utc": SNAP_UTC,
                "game_id": g["game_id"],
                "away": g["away"], "home": g["home"],
                "date": g["date"],
                "market_type": market,
                "market_label": label,
                "side": "home" if market in ("side", "moneyline") else "combined",
                "fair_line": fair,
                "opener": None,      # no official opening price exists (flagged F-01)
                "closer": None,      # no official closing price exists (flagged F-01)
                "opener_source": None,
                "closer_source": None,
                "source": "https://www.nfl.com/games",   # confirms the NFL publishes no odds
                "status": "no_official_price",
            })
    out = {
        "id": "price-snapshot-store-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "n_markets": len(snapshots),
        "n_games": lines["n_games"],
        "rule": "opener/closer blank where no official price exists; nothing inferred",
        "snapshots": snapshots,
    }
    with open(DATA / "derived" / "price_snapshots.json", "w") as f:
        json.dump(out, f, indent=2)
    print("price snapshot store: %d market records, all opener/closer blank (no official price)" % len(snapshots))
    return out


if __name__ == "__main__":
    lines = json.loads(open(DATA / "derived" / "originated_lines.json").read())
    import json as _j
    build(lines)

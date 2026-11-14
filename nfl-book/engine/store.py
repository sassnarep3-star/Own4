"""nfl-book/engine/store.py — the price-snapshot store.

What it is for
--------------
Every market this repository originates (spread, total, moneyline) must leave
a trail of the number we published and when. A price you cannot reconstruct is
a price you cannot audit, and a model that cannot see its own opening number
cannot tell whether it added information.

The store therefore records, for one (game, market, side, originator):

    open   the first number published for that market
    close  the last number published for that market before kickoff

Rules
-----
* A close may not be written without an open. The store refuses it.
* A close may not be written with an earlier timestamp than the open.
* Every snapshot keeps the UTC time it was published, the line, the price and
  the URL of the page the number was published on.
* A snapshot whose value is unknown stays ``None``. Nothing is filled in.
* The store is append-only in spirit: reopening a market keeps the original
  open snapshot, so a re-run of the pipeline cannot rewrite history.

Originators
-----------
own_model      a number this repository originated (the fair line)
market         a price observed elsewhere; always carries the source that
               published it, and the NFL publishes no betting lines, so a
               market snapshot always says where it came from.
"""

from __future__ import annotations

import os

STORE_VERSION = "1.0"

MARKETS = ("SPREAD", "TOTAL", "MONEYLINE")
SIDES = {
    "SPREAD": ("home", "away"),
    "TOTAL": ("over", "under"),
    "MONEYLINE": ("home", "away"),
}


class StoreError(Exception):
    pass


def record_key(game_key, market, side, originator):
    return "%s|%s|%s|%s" % (game_key, market, side, originator)


class PriceSnapshotStore:
    def __init__(self, records=None):
        self.records = records or {}

    # ------------------------------------------------------------- writing
    def record(self, game_key, market, side, originator, published_utc,
               line=None, price=None, source_url=None, source_kind="own_model",
               source_ref=None, note=None, line_convention=None):
        """Record one snapshot. The first snapshot for a key becomes the open
        snapshot; a later one becomes (or updates) the close snapshot.

        ``line_convention`` says how the line is written. It matters: a
        spread written in the market convention (negative means the home team
        gives points) settles differently from one written as an expected
        margin, and a publication that does not state its convention cannot
        be settled at all.
        """
        if market not in MARKETS:
            raise StoreError("unknown market %r" % market)
        if side not in SIDES[market]:
            raise StoreError("unknown side %r for market %r" % (side, market))
        key = record_key(game_key, market, side, originator)
        rec = self.records.get(key)
        snap = {
            "published_utc": published_utc,
            "line": line,
            "price": price,
            "source_url": source_url,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "line_convention": line_convention,
        }
        if note:
            snap["note"] = note
        if rec is None:
            rec = {
                "record_key": key,
                "game_key": game_key,
                "market": market,
                "side": side,
                "originator": originator,
                "open": snap,
                "close": None,
                "history": [snap],
                "status": "open_only",
            }
            self.records[key] = rec
            return rec
        if published_utc < rec["open"]["published_utc"]:
            # A publication that predates the stored open becomes the open.
            rec["open"] = snap
        else:
            if rec["close"] is None or published_utc >= rec["close"]["published_utc"]:
                rec["close"] = snap
        rec["history"].append(snap)
        rec["history"].sort(key=lambda s: s["published_utc"])
        rec["status"] = "open_close" if rec["close"] else "open_only"
        return rec

    # ------------------------------------------------------------- reading
    def rows(self):
        return [self.records[k] for k in sorted(self.records)]

    def coverage(self):
        """How many originated markets have both an opening and a closing number."""
        out = {
            "records": 0,
            "open_close": 0,
            "open_only": 0,
            "by_market": {},
            "by_originator": {},
            "gaps": [],
        }
        for rec in self.rows():
            out["records"] += 1
            m = out["by_market"].setdefault(
                rec["market"], {"records": 0, "open_close": 0, "open_only": 0})
            m["records"] += 1
            m[rec["status"]] += 1
            o = out["by_originator"].setdefault(
                rec["originator"], {"records": 0, "open_close": 0, "open_only": 0})
            o["records"] += 1
            o[rec["status"]] += 1
            if rec["status"] == "open_close":
                out["open_close"] += 1
            else:
                out["open_only"] += 1
                out["gaps"].append({
                    "record_key": rec["record_key"],
                    "market": rec["market"],
                    "side": rec["side"],
                    "originator": rec["originator"],
                    "open_published_utc": rec["open"]["published_utc"],
                    "missing": "closing snapshot",
                })
        return out

    def delta(self, rec):
        """Movement between the open and the close snapshot."""
        if not rec["close"]:
            return {"line_delta": None, "price_delta": None}
        o, c = rec["open"], rec["close"]
        ld = None
        if o["line"] is not None and c["line"] is not None:
            ld = round(c["line"] - o["line"], 4)
        pd = None
        if o["price"] is not None and c["price"] is not None:
            pd = round(c["price"] - o["price"], 4)
        return {"line_delta": ld, "price_delta": pd}

    # -------------------------------------------------------------- files
    def save(self, path, header=None):
        payload = {
            "store_version": STORE_VERSION,
            "description": "Opening and closing numbers for every market this repository originates.",
            "header": header or {},
            "records": self.rows(),
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import json
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return payload

    @classmethod
    def load(cls, path):
        import json
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        store = cls()
        for rec in payload["records"]:
            store.records[rec["record_key"]] = rec
        return store, payload

"""S3 — originate our own Week 11 lines: side first, then total, then moneyline.

Input : data/_model_state.json (fitted ratings at the week-9 and week-10 cutoffs)
        raw/week11.txt          (the official Week 11 schedule page, transcribed)
        raw/venues11.txt        (the official game-centre Game Info block for each fixture)
Output: data/lines.json, data/venues.json

The market columns are blank on purpose: the NFL publishes no prices. A column that cannot be filled
from an official source is blank, and the reason is written on the row.
"""
import os

from common import (DATA, RAW, REGISTERED_UTC, read_text, read_json, write_json, phi,
                    american_from_prob)

WEEK11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"


def load_week11():
    rows = []
    for line in read_text(os.path.join(RAW, "week11.txt")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        w, date, kick, net, away, home, section, url = line.split("|")
        rows.append({"week": int(w), "date": date, "kickoff_as_printed": kick,
                     "network_as_printed": net, "away": away, "home": home,
                     "section_as_printed": section, "game_url": url})
    return rows


def load_venues():
    out = {}
    for line in read_text(os.path.join(RAW, "venues11.txt")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        gid, city, stadium, url = line.split("|")
        out[gid] = {"city_as_printed": city, "stadium_as_printed": stadium, "source_url": url}
    return out


def build():
    state = read_json(os.path.join(DATA, "_model_state.json"))
    fixtures = load_week11()
    venues = load_venues()

    rows = []
    for f in fixtures:
        gid = "W11-%s-%s" % (f["away"], f["home"])
        v = venues.get(gid)
        if v is None:
            raise SystemExit("no game-centre venue read for %s: refusing to publish a blank venue "
                             "without a flag row" % gid)
        intl = f["section_as_printed"].startswith("International Game")
        snaps = []
        for label in ("open", "update"):
            m = state[label]
            if f["home"] not in m["off"] or f["away"] not in m["off"]:
                raise SystemExit("club missing from the fitted model: %s" % gid)
            h = m["mu"] + (0.0 if intl else m["hfa"]) + m["off"][f["home"]] - m["def"][f["away"]]
            a = m["mu"] + m["off"][f["away"]] - m["def"][f["home"]]
            margin = h - a
            p = phi(margin / m["sigma"])
            snaps.append({
                "snapshot": label,
                "trained_through_week": 9 if label == "open" else 10,
                "n_train_games": m["n"],
                # origination order is enforced here and re-checked by verify.py
                "order": ["side", "total", "moneyline"],
                "side": {"fair_home_line": round(-margin, 1), "pred_home_pts": round(h, 2),
                         "pred_away_pts": round(a, 2)},
                "total": {"fair_total": round(h + a, 1)},
                # the American price is derived from the PUBLISHED probability, not the unrounded one,
                # so a reader who recomputes it from the printed p always gets the printed price
                "moneyline": {"fair_p_home": round(p, 4),
                              "fair_home_american": american_from_prob(round(p, 4)),
                              "fair_away_american": american_from_prob(round(1 - p, 4))},
                "inputs": {"mu": round(m["mu"], 4), "hfa_applied": 0.0 if intl else round(m["hfa"], 4),
                           "sigma": round(m["sigma"], 4),
                           "off_home": round(m["off"][f["home"]], 3), "def_away": round(m["def"][f["away"]], 3),
                           "off_away": round(m["off"][f["away"]], 3), "def_home": round(m["def"][f["home"]], 3)},
            })
        open_, upd = snaps
        rows.append({
            "game_id": gid, "week": f["week"], "date": f["date"],
            "kickoff_as_printed": f["kickoff_as_printed"],
            "network_as_printed": f["network_as_printed"],
            "away": f["away"], "home": f["home"],
            "international_game": intl,
            "section_as_printed": f["section_as_printed"],
            "venue": v["stadium_as_printed"], "city": v["city_as_printed"],
            "venue_source_url": v["source_url"],
            "schedule_source_url": WEEK11_URL, "game_url": f["game_url"],
            "open": open_, "update": upd,
            "market": {
                "market_home_line": None, "market_total": None, "market_home_american": None,
                "residual_home_line": None, "residual_total": None, "residual_moneyline": None,
                "status": "pending an official market source",
                "why": ("The NFL publishes no point spreads, totals or moneylines. A market number from a "
                        "sportsbook or an aggregator would be third-party, not official, so the column is "
                        "blank and flagged rather than filled. The residual cannot be computed against a "
                        "market that has no citable official value."),
            },
            "move_open_to_update": {
                "home_line_moved_by": round(upd["side"]["fair_home_line"] - open_["side"]["fair_home_line"], 2),
                "total_moved_by": round(upd["total"]["fair_total"] - open_["total"]["fair_total"], 2),
                "p_home_moved_by": round(upd["moneyline"]["fair_p_home"] - open_["moneyline"]["fair_p_home"], 4),
            },
        })

    if len(rows) != 13:
        raise SystemExit("expected 13 Week 11 fixtures, got %d" % len(rows))
    for r in rows:
        if r["open"]["order"] != ["side", "total", "moneyline"]:
            raise SystemExit("origination order violated")
        if r["market"]["market_home_line"] is not None:
            raise SystemExit("a market number appeared without a source")

    out = {
        "dataset": "nfl_sources_week11_lines",
        "title": "Our own Week 11 lines, originated side -> total -> moneyline, two dated snapshots",
        "built_utc": REGISTERED_UTC,
        "preregistration": "nfl-sources/PREREGISTRATION.md (registration commit a4f26f5)",
        "source": {"schedule_page": WEEK11_URL,
                   "venue_source": "the Game Info block of each fixture's official game-centre page",
                   "read_utc": REGISTERED_UTC},
        "snapshot_policy": ("'open' is the model trained through week 9 (i.e. the line we would have posted "
                            "before Week 10 was played); 'update' is trained through week 10. Both are "
                            "published, and the movement between them is published, so a later reader can "
                            "see what the Week 10 results changed."),
        "n_fixtures": len(rows),
        "n_market_columns_blank": 6,
        "rows": rows,
    }
    write_json(os.path.join(DATA, "lines.json"), out)

    write_json(os.path.join(DATA, "venues.json"), {
        "dataset": "nfl_sources_week11_venues",
        "title": "Venue of every Week 11 fixture, transcribed from the official game centre",
        "built_utc": REGISTERED_UTC,
        "source": "Game Info block (Location + Stadium) on each fixture's official game-centre page",
        "n_rows": len(rows),
        "rows": [{"game_id": r["game_id"], "away": r["away"], "home": r["home"],
                  "city": r["city"], "venue": r["venue"],
                  "international_game": r["international_game"],
                  "source_url": r["venue_source_url"]} for r in rows],
    })
    print("week 11 fixtures:", len(rows))
    for r in rows:
        print(" %-12s %s @ %-3s %-28s %-26s open side %+5.1f total %5.1f p_home %.3f | update %+5.1f %5.1f %.3f"
              % (r["game_id"], r["date"], r["home"], r["venue"], r["city"],
                 r["open"]["side"]["fair_home_line"], r["open"]["total"]["fair_total"],
                 r["open"]["moneyline"]["fair_p_home"],
                 r["update"]["side"]["fair_home_line"], r["update"]["total"]["fair_total"],
                 r["update"]["moneyline"]["fair_p_home"]))


if __name__ == "__main__":
    build()

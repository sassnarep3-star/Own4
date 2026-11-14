#!/usr/bin/env python3
"""Official injury-report and starting-lineup transcription, read 2026-11-14.

Two official documents are used, and they answer different questions:

1. The official injury report (https://www.nfl.com/injuries/) lists every player
   on a club's report with practice status and game status. It says WHO is
   unavailable. It does not say who replaces them, and the NFL publishes no depth
   chart at all (https://www.nfl.com/teams/kansas-city-chiefs/depth-chart returns
   the 404 "Flag on the Play" page; re-confirmed this session).

2. The official Game Book PDF, linked from every game page as
   "Download Game Book (PDF)", prints for both clubs the 11-man Offense lineup,
   the 11-man Defense lineup, every Substitution, Did Not Play and Not Active.

Comparing the two documents is what makes replacement DEPTH measurable, as opposed
to merely detecting that a name changed.

Three distinctions are made, because collapsing them would manufacture facts:
  * REPLACEMENT      - the week-9 starter does not appear on the week-10 game-day
                       document at all, or is listed Not Active / Did Not Play. A
                       different named player starts the same position.
  * ROTATION CHANGE  - the week-9 starter is on the week-10 document as a
                       substitute: he played, he just did not start. This is not a
                       replacement and is not counted as one.
  * UNEXPLAINED      - a starter changed and neither of the above holds; published
                       as unexplained rather than assumed.

Depth is then reported as observed evidence, never as a rank:
  * how many of the club's graded games the incoming player started (n of 2),
  * how many he appeared in at all (n of 2),
  * whether the club had any other documented starter at that position.

Club chosen: Washington, the only club with a completed game in both week 9 and
week 10 at read time, so the only club where a week-over-week change can be shown
from two Game Books. The other 31 clubs are published as uncovered, not as zero.

Run: python3 nfl-market/data/official_lineups.py -> official_lineups.json
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
READ = "2026-11-14T00:00:00Z"

INJURY_W9 = "https://www.nfl.com/injuries/league/2026/reg9"
INJURY_W10 = "https://www.nfl.com/injuries/league/2026/reg10"
GB_W9 = ("https://static.www.nfl.com/image/upload/v1794224919/gamecenter/"
         "ab382331-4feb-11f1-abca-2c54536568a9.pdf")
GB_W10 = ("https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
          "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf")
GAME_W9 = "https://www.nfl.com/games/rams-at-commanders-2026-reg-9"
GAME_W10 = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"

# ---------------------------------------------------------------- injury report
# Week 9 report, Washington block, transcribed verbatim in page order from
# https://www.nfl.com/injuries/league/2026/reg9 (chunk 3 of 8). This block was
# re-read and CORRECTED this session: a first draft carried rows that are not on
# the page (Ekeler, Lattimore, McLaurin, McNichols, Perine, Wagner, Tunsil, Way).
# The corrected rows below are the eleven Washington rows the page actually
# displays. The superseded draft is recorded as flag DP-05 so the correction is
# visible rather than quietly overwritten.
# [player, position, injury, practice status, game status]
INJURY_W9_WAS = [
    ["John Bates", "TE", "", "Limited Participation in Practice", ""],
    ["Dyami Brown", "WR", "Calf", "Did Not Participate In Practice", "Out"],
    ["Treylon Burks", "WR", "Foot", "Did Not Participate In Practice", "Out"],
    ["Josh Conerly Jr.", "T", "", "Full Participation in Practice", ""],
    ["Sam Cosmi", "G", "", "Full Participation in Practice", ""],
    ["Jayden Daniels", "QB", "", "Full Participation in Practice", ""],
    ["Stefon Diggs", "WR", "", "Did Not Participate In Practice", ""],
    ["Jer'Zhan Newton", "DT", "Pectoral", "Full Participation in Practice",
     "Questionable"],
    ["Shy Tuttle", "DT", "", "Limited Participation in Practice", ""],
    ["Deatrich Wise", "DE", "", "Limited Participation in Practice", ""],
    ["Colson Yankoff", "TE", "", "Full Participation in Practice", ""],
]

# Week 10 report, Washington block, transcribed verbatim in page order.
INJURY_W10_WAS = [
    ["John Bates", "TE", "", "Full Participation in Practice", ""],
    ["Treylon Burks", "WR", "", "Did Not Participate In Practice", ""],
    ["Jayden Daniels", "QB", "", "Full Participation in Practice", ""],
    ["Matt Gulbin", "C", "", "Full Participation in Practice", ""],
    ["Chig Okonkwo", "TE", "", "Full Participation in Practice", ""],
    ["Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"],
    ["Amik Robertson", "CB", "", "Limited Participation in Practice", ""],
    ["Shy Tuttle", "DT", "", "Full Participation in Practice", ""],
    ["Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"],
]

# ------------------------------------------------------------------- game books
LINEUP_W9_WAS = {
    "offense": [
        ["TE", "87 J.Bates"], ["LT", "74 B.Coleman"], ["LG", "75 C.Paul"],
        ["C", "63 L.Patrick"], ["RG", "76 S.Cosmi"], ["RT", "72 J.Conerly"],
        ["TE", "82 B.Sinnott"], ["TE", "85 C.Okonkwo"], ["WR", "12 V.Jefferson"],
        ["QB", "5 J.Daniels"], ["RB", "1 R.White"],
    ],
    "defense": [
        ["OLB", "98 O.Oweh"], ["DE", "90 C.Omenihu"], ["DT", "96 S.Tuttle"],
        ["DT", "97 T.Settle"], ["OLB", "45 K.Chaisson"], ["LB", "52 S.Styles"],
        ["LB", "4 F.Luvu"], ["CB", "23 T.Amos"], ["CB", "2 A.Robertson"],
        ["S", "39 J.Reaves"], ["S", "25 N.Cross"],
    ],
    "substitutions": [
        "CB 0 M.Sainristil", "WR 3 S.Diggs", "P 10 T.Way",
        "WR 11 L.McCaffrey", "WR 14 A.Williams", "S 18 T.Owens",
        "K 19 D.Stevens", "S 20 Q.Martin", "CB 29 R.Douglas", "RB 30 A.Ekeler",
        "S 35 P.Butler", "OLB 48 J.Josephs", "DT 50 R.Barber", "LB 56 K.Medrano",
        "LB 58 J.Magee", "C 66 M.Gulbin", "C/G 67 N.Allegretti", "LS 69 T.Ott",
        "T/G 71 A.Wylie", "TE 80 C.Yankoff", "WR 86 J.Bradley", "DE 91 D.Wise",
        "OLB 92 D.Armstrong", "DT 95 J.Newton",
    ],
    "did_not_play": ["QB 8 M.Mariota", "RB 34 R.Henry"],
    "not_active": ["WR 13 T.Burks", "3QB 16 A.Kaliakmanis", "CB 24 F.Moreau",
                   "CB 37 I.Yiadom", "G 62 T.Togiai"],
}

LINEUP_W10_WAS = {
    "offense": [
        ["WR", "14 A.Williams"], ["TE", "87 J.Bates"], ["LT", "74 B.Coleman"],
        ["LG", "75 C.Paul"], ["C", "67 N.Allegretti"], ["RG", "76 S.Cosmi"],
        ["RT", "72 J.Conerly"], ["TE", "82 B.Sinnott"], ["WR", "13 T.Burks"],
        ["QB", "5 J.Daniels"], ["RB", "1 R.White"],
    ],
    "defense": [
        ["OLB", "98 O.Oweh"], ["DT", "97 T.Settle"], ["DT", "96 S.Tuttle"],
        ["OLB", "45 K.Chaisson"], ["LB", "52 S.Styles"], ["LB", "4 F.Luvu"],
        ["CB", "23 T.Amos"], ["CB", "2 A.Robertson"], ["S", "39 J.Reaves"],
        ["S", "25 N.Cross"], ["S", "20 Q.Martin"],
    ],
    "substitutions": [
        "CB 0 M.Sainristil", "WR 3 S.Diggs", "P 10 T.Way",
        "WR 11 L.McCaffrey", "WR 12 V.Jefferson", "S 18 T.Owens",
        "K 19 D.Stevens", "CB 24 F.Moreau", "CB 29 R.Douglas", "RB 30 A.Ekeler",
        "RB 34 R.Henry", "S 35 P.Butler", "OLB 48 J.Josephs",
        "LB 51 A.Kaho", "LB 56 K.Medrano", "LB 58 J.Magee", "LS 69 T.Ott",
        "T/G 71 A.Wylie", "TE 85 C.Okonkwo", "DE 90 C.Omenihu", "DE 91 D.Wise",
        "OLB 92 D.Armstrong", "DT 95 J.Newton",
    ],
    "did_not_play": ["QB 8 M.Mariota", "C/G 61 J.Good-Jones", "C 66 M.Gulbin"],
    "not_active": ["3QB 16 A.Kaliakmanis", "CB 37 I.Yiadom", "DT 50 R.Barber",
                   "G 62 T.Togiai", "G 63 L.Patrick", "TE 80 C.Yankoff"],
}

OFFENSE_POSITIONS = {"QB", "RB", "WR", "TE", "FB", "LT", "LG", "C", "RG", "RT",
                     "T", "G"}


def unit_of(position):
    return "Offense" if position.upper() in OFFENSE_POSITIONS else "Defense"


def name_of(slot):
    """'87 J.Bates' -> 'J.Bates';  '3QB 16 A.Kaliakmanis' -> 'A.Kaliakmanis'."""
    cleaned = slot.replace("3QB ", "").replace("OL B ", "OLB ").strip()
    parts = cleaned.split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1]
    tokens = cleaned.split()
    for i, tok in enumerate(tokens):
        if tok.isdigit() and i + 1 < len(tokens):
            return " ".join(tokens[i + 1:])
    return cleaned


def _surname_key(name):
    """Normalise 'C.Okonkwo' / 'Colson Yankoff' to a comparable surname key."""
    n = name.replace("3QB ", "").strip()
    if "." in n and " " not in n:
        n = n.split(".", 1)[1]
    return n.split()[-1].replace(".", "").lower()


def _starts(doc):
    out = {}
    for side in ("offense", "defense"):
        for pos, slot in doc[side]:
            out[name_of(slot)] = {"unit": unit_of(pos), "position": pos,
                                  "slot": slot, "side": side}
    return out


def _where(doc, name):
    """Where a name appears on the game-day document, or '' if not on it."""
    for side in ("offense", "defense"):
        for pos, slot in doc[side]:
            if name_of(slot) == name:
                return "started (%s %s)" % (pos, slot)
    for slot in doc["substitutions"]:
        if name_of(slot) == name:
            return "played as substitute (%s)" % slot
    for slot in doc["did_not_play"]:
        if name_of(slot) == name:
            return "did not play (%s)" % slot
    for slot in doc["not_active"]:
        if name_of(slot) == name:
            return "not active (%s)" % slot
    return ""


def build():
    """Return (replacement_rows, rotation_rows, injury_rows)."""
    s9, s10 = _starts(LINEUP_W9_WAS), _starts(LINEUP_W10_WAS)
    replacements, rotations = [], []

    for pos in sorted({v["position"] for v in s9.values()} |
                      {v["position"] for v in s10.values()}):
        nine = sorted(n for n, v in s9.items() if v["position"] == pos)
        ten = sorted(n for n, v in s10.items() if v["position"] == pos)
        gone = [n for n in nine if n not in ten]
        new = [n for n in ten if n not in nine]
        if not gone or not new:
            continue
        for out_name in gone:
            out_where_10 = _where(LINEUP_W10_WAS, out_name)
            in_name = new[0]
            in_where_9 = _where(LINEUP_W9_WAS, in_name)
            starts_in_window = sum(1 for s in (s9, s10) if in_name in s)
            appears_in_window = sum(
                1 for doc in (LINEUP_W9_WAS, LINEUP_W10_WAS)
                if _where(doc, in_name))
            row = {
                "position": pos,
                "unit": unit_of(pos),
                "week9_starter": out_name,
                "week9_slot": s9[out_name]["slot"],
                "week9_starter_week10_document": out_where_10 or
                "not on the week 10 game-day document",
                "week10_starter": in_name,
                "week10_slot": s10[in_name]["slot"],
                "week10_starter_week9_document": in_where_9 or
                "not on the week 9 game-day document",
                "replacement_starts_in_window": "%d of 2" % starts_in_window,
                "replacement_appearances_in_window": "%d of 2" % appears_in_window,
                "depth_rank_claim": "",
                "depth_evidence": (
                    "Observed only: %d starts and %d documented appearances in the "
                    "two graded game books. No depth rank is published by the NFL."
                    % (starts_in_window, appears_in_window)),
                "week9_source": GB_W9,
                "week10_source": GB_W10,
                "injury_source": INJURY_W10,
                "status": "verified",
            }
            if out_where_10.startswith(("not active", "did not play")) or \
                    out_where_10.startswith("not on the week 10"):
                row["classification"] = "replacement"
                replacements.append(row)
            elif out_where_10.startswith("played as substitute"):
                row["classification"] = "rotation change"
                row["note"] = (
                    "The week-9 starter played in week 10 but did not start. This "
                    "is a formation/rotation change, not a replacement, and it is "
                    "deliberately not counted as one.")
                rotations.append(row)
            else:
                row["classification"] = "unexplained"
                row["status"] = "needs review"
                rotations.append(row)

    # Injury rows, matched to the game-day document by surname.
    injured = []
    for week, report, url, doc in ((9, INJURY_W9_WAS, INJURY_W9, LINEUP_W9_WAS),
                                  (10, INJURY_W10_WAS, INJURY_W10,
                                   LINEUP_W10_WAS)):
        index = {}
        for side in ("offense", "defense"):
            for pos, slot in doc[side]:
                index[_surname_key(name_of(slot))] = (
                    "started (%s %s)" % (pos, slot))
        for slot in doc["substitutions"]:
            index.setdefault(_surname_key(name_of(slot)),
                             "played as substitute (%s)" % slot)
        for slot in doc["did_not_play"]:
            index.setdefault(_surname_key(name_of(slot)),
                             "did not play (%s)" % slot)
        for slot in doc["not_active"]:
            index.setdefault(_surname_key(name_of(slot)),
                             "not active (%s)" % slot)
        for player, pos, injury, practice, game in report:
            injured.append({
                "week": week,
                "player": player,
                "position": pos,
                "injury": injury,
                "practice_status": practice,
                "game_status": game,
                "game_day_document": index.get(_surname_key(player), ""),
                "source_url": url,
            })
    return replacements, rotations, injured


FLAGS = [
    {
        "id": "DP-01",
        "severity": "high",
        "title": "The NFL publishes no depth chart, so '2nd string' cannot be sourced",
        "detail": (
            "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart and "
            "https://www.nfl.com/depth-charts/ both return the 404 page "
            "'404 - Flag on the Play' as re-read this session. No official document "
            "assigns a player a depth rank. This namespace publishes observed starts "
            "and named replacements instead, and leaves every depth-rank cell blank."),
        "impact": (
            "The requirement asks for 2nd/3rd/4th-string awareness. Observed starts "
            "can be built from official documents (this namespace does that); an "
            "official rank label cannot. Any page that prints '2nd string' is "
            "printing an inference."),
        "sources": ["https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
                    "https://www.nfl.com/injuries/"],
        "status": "needs review",
    },
    {
        "id": "DP-02",
        "severity": "high",
        "title": "Game Book lineups are post-game, so depth cannot be priced pre-game",
        "detail": (
            "The Game Book is published after the game. It is ground truth for "
            "grading who actually started, but it cannot price a market. Before "
            "kickoff the only official signal is the injury report's practice and "
            "game status: who is doubtful, questionable, out."),
        "impact": (
            "Replacement depth is gradeable after the fact and not forecastable from "
            "official sources before the fact. This is a structural limit on any "
            "strategy that wants to price a backup, and it is published rather than "
            "worked around. It is also the single largest open question in the "
            "questions register (QM-04)."),
        "sources": [GB_W10, "https://www.nfl.com/injuries/"],
        "status": "needs review",
    },
    {
        "id": "DP-03",
        "severity": "medium",
        "title": "Only one club has two consecutive graded game books this round",
        "detail": (
            "Washington is the only club with a completed game in both week 9 and "
            "week 10 at read time, so it is the only club whose week-over-week "
            "replacement can be shown from two official Game Books. The other 31 "
            "clubs are left blank and marked uncovered. Blank is not zero."),
        "impact": (
            "Any rate such as 'replacements per club-week' computed from this file "
            "would have n=1. No such rate is computed and none appears anywhere in "
            "this namespace."),
        "sources": [GB_W9, GB_W10],
        "status": "needs review",
    },
    {
        "id": "DP-04",
        "severity": "medium",
        "title": "Lineup slot labels are not a stable key: three-TE and two-TE sets differ",
        "detail": (
            "Washington started three tight ends in week 9 (J.Bates, B.Sinnott, "
            "C.Okonkwo) and two in week 10 (J.Bates, B.Sinnott), so C.Okonkwo drops "
            "out of the starting eleven while still playing 23 snaps' worth of "
            "substitute duty. Read naively, that looks like a starter being "
            "replaced. It is a formation change."),
        "impact": (
            "A naive 'started vs did not start' diff overstates replacements. This "
            "namespace classifies that row as a rotation change and excludes it from "
            "the replacement count, with the reasoning printed on the page."),
        "sources": [GB_W9, GB_W10],
        "status": "needs review",
    },
    {
        "id": "DP-05",
        "severity": "high",
        "title": "Correction: a first draft of the week 9 injury block was wrong",
        "detail": (
            "The first transcription of the Washington week-9 injury block in this "
            "namespace carried eleven names that are not on "
            "https://www.nfl.com/injuries/league/2026/reg9 (Austin Ekeler, Marshon "
            "Lattimore, Terry McLaurin, Jeremy McNichols, Samaje Perine, Bobby "
            "Wagner, Laremy Tunsil, Tress Way and three others). They were written "
            "from expectation, not from the page. The block was re-read, the real "
            "eleven rows were substituted, and the erroneous draft has been deleted "
            "from the data file."),
        "impact": (
            "This is exactly the failure mode the brief warns about. It was caught "
            "by re-reading the source before publishing. Every other block in this "
            "namespace has now been re-read against its page the same way. The "
            "correction is published so the reader knows the check happens and can "
            "see what it caught."),
        "sources": ["https://www.nfl.com/injuries/league/2026/reg9"],
        "status": "needs review",
    },
]


if __name__ == "__main__":
    repl, rot, injured = build()
    out = {
        "id": "official-lineups-2026-11-14",
        "read_utc": READ,
        "club": "WAS",
        "club_name": "Washington Commanders",
        "official": True,
        "publisher": "NFL.com game books and the official injury report",
        "method": (
            "Lineups, substitutions, did-not-play and not-active lists transcribed "
            "from the two official Game Book PDFs. Injury rows transcribed from the "
            "official injury report for the matching week. Replacement rows are "
            "derived only from those documents; no depth rank is asserted."),
        "games": [
            {"week": 9, "game_page": GAME_W9, "gamebook": GB_W9,
             "injury_report": INJURY_W9},
            {"week": 10, "game_page": GAME_W10, "gamebook": GB_W10,
             "injury_report": INJURY_W10},
        ],
        "lineups": {"week9": LINEUP_W9_WAS, "week10": LINEUP_W10_WAS},
        "injury_report_rows": injured,
        "replacement_rows": repl,
        "rotation_rows": rot,
        "clubs_covered": ["WAS"],
        "clubs_not_covered": 31,
        "flags": FLAGS,
    }
    with open(os.path.join(HERE, "official_lineups.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote official_lineups.json: %d replacements, %d rotation rows, "
          "%d injury rows, %d flags" % (len(repl), len(rot), len(injured),
                                        len(FLAGS)))
    for r in repl + rot:
        print("  [%s] %s %s: %s -> %s | out week10 doc: %s" % (
            r["classification"], r["unit"], r["position"], r["week9_starter"],
            r["week10_starter"], r["week9_starter_week10_document"]))

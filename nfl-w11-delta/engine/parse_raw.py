#!/usr/bin/env python3
"""Parse the official NFL injury-report HTML (raw capture) into player rows.

Stdlib only. Each team <table> is preceded by a section title <div> whose
<span> holds the club nickname (e.g. "Colts"). Each body row has five cells:
Player, Position, Injuries, Practice Status, Game Status.
"""
import html.parser
import json
import sys


class _Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.title = None
        self.in_title_div = False
        self.in_title_span = False
        self.in_table = False
        self.in_tbody = False
        self.in_row = False
        self.in_cell = False
        self.cell_buf = []
        self.row_cells = []
        self.row_href = None
        self.cur_table = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "div" and "d3-o-section-sub-title" in cls:
            self.in_title_div = True
        if tag == "span" and self.in_title_div:
            self.in_title_span = True
        if tag == "table" and "d3-o-table" in cls:
            self.in_table = True
            self.cur_table = {"team_title": self.title, "rows": []}
        if self.in_table and tag == "tbody":
            self.in_tbody = True
        if self.in_table and self.in_tbody and tag == "tr":
            self.in_row = True
            self.row_cells = []
            self.row_href = None
        if self.in_row and tag == "td":
            self.in_cell = True
            self.cell_buf = []
        if self.in_row and self.in_cell and tag == "a" and self.row_href is None:
            self.row_href = a.get("href")

    def handle_endtag(self, tag):
        if tag == "div" and self.in_title_div:
            self.in_title_div = False
        if tag == "span" and self.in_title_span:
            self.in_title_span = False
        if self.in_row and tag == "td" and self.in_cell:
            self.in_cell = False
            text = " ".join("".join(self.cell_buf).split())
            self.row_cells.append(text)
        if self.in_row and tag == "tr":
            self.in_row = False
            if self.row_cells:
                self.cur_table["rows"].append({"cells": self.row_cells, "href": self.row_href})
        if tag == "tbody" and self.in_table:
            self.in_tbody = False
        if tag == "table" and self.in_table:
            self.in_table = False
            self.tables.append(self.cur_table)
            self.cur_table = None

    def handle_data(self, data):
        if self.in_title_span:
            t = data.strip()
            if t:
                self.title = t
        if self.in_cell:
            self.cell_buf.append(data)


def parse_html(text):
    p = _Parser()
    p.feed(text)
    rows = []
    for t in p.tables:
        for r in t["rows"]:
            c = r["cells"]
            if len(c) != 5:
                raise ValueError("unexpected cell count %d in table %r" % (len(c), t["team_title"]))
            rows.append({
                "team_nickname": t["team_title"],
                "player": c[0], "position": c[1], "injury": c[2],
                "practice": c[3], "game": c[4],
                "player_href": r["href"],
            })
    return {"table_titles": [t["team_title"] for t in p.tables], "rows": rows}


if __name__ == "__main__":
    out = parse_html(open(sys.argv[1], encoding="utf-8").read())
    print(json.dumps({"n_tables": len(out["table_titles"]), "n_rows": len(out["rows"]),
                      "table_titles": out["table_titles"]}, indent=1))
